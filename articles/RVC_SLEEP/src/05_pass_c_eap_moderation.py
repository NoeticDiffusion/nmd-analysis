"""
05_pass_c_eap_moderation.py — Pass C: EAP x RVC moderation.

Uses primary EEG-only geometry only. Tests whether the pre-event anchor state
(HRV for ANPHY, respiratory regularity for BOAS) moderates spindle-locked
geometry change.

Protocol amendment (sciencelead/001.md, 002.md, 2026-07-03): Pass C inherits
the A1r subject-weighted estimand rather than the A1-original pooled
event-weighted one — a handful of high-event-count subjects should not be
allowed to dominate the pooled moderation slope, especially in BOAS (median 5
events/subject, range 1-18). Per sciencelead/002.md, Pass C is run TWICE, on
both delta definitions, since the A1/A2 decomposition (02d) showed they ask
different questions:

    event_control_delta = event_bin - matched_control_median   ("A1-style":
                            does anchor state predict spindle-specific
                            geometry relative to matched N2?)
    event_prefar_delta   = event_bin - mean(pre_far bins, same event)  ("A2-style":
                            does anchor state predict the within-spindle
                            denoising/rise step?)

Model (per dataset/anchor/delta-mode):
    PRIMARY:      delta ~ anchor_pre_far + <covariates, mean-centered>
                  weighted by 1/n_events_subject, cluster-robust SE by subject_id
    SENSITIVITY:  per-subject OLS slope(delta ~ anchor_pre_far), tested across
                  subjects (immune to event-count imbalance by construction)

Nuisance-control guardrail (sciencelead/002.md #2): because A1r is
significant across almost every endpoint, reviewers will ask whether this is
a broad amplitude/arousal shift rather than an endpoint-specific effect.
Covariates now include, wherever coverage allows (available_covariates(),
min 50% non-NaN): event_duration_sec, window_center_sec (time-of-night
proxy — no true clock time in the schema), ocular_stability_index,
sympathetic_index (EMG/arousal proxy — no true EMG channel in the schema),
eog_quality_quality, anchor_support_fraction_quality, ecg_quality_quality,
vagal_index. `frequency_hz` is requested by the science lead but is NOT
present in the NMD event-locked schema at all (checked directly against
event_level_primary.parquet columns, 2026-07-03) — listed defensively in case
a future NMD export adds it, but currently always dropped by
available_covariates(). Sigma-power residualization is NOT available in this
schema and is NOT approximated by duration/frequency here — it is planned as
a follow-up detector-strength robustness analysis, not silently substituted.

2026-07-03 bugfix (see 01_build_event_level_tables.py): `pass_c_anchor_contexts.parquet`
used to key only on (dataset_id, event_id), but `event_id` is a per-subject-local
counter, not globally unique — the old merge was many-to-many and attached
essentially-random subjects' anchor values to most events. Fixed upstream in
01; this script now merges on (dataset_id, subject_id, event_id).

ANPHY:  anchor_pre_far = ecg_hrv_rmssd_ms_pre_far        (Pass C primary anchor)
BOAS:   anchor_pre_far = resp_regular_index_pre_far      (respiratory-available
                          subset only — report N explicitly, NOT full N=128;
                          see handover_From_nmd.md §6 known limitation #1)
        sensitivity rerun with anchor_index_v02_pre_far   (available in ~127/128)

Run: python src/05_pass_c_eap_moderation.py
Requires: 01_build_event_level_tables.py to have been run first (with the
          subject_id-keyed anchor-context fix).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from rvc_sleep_support import (
    DATASET_ANPHY,
    DATASET_BOAS,
    GEOMETRY_COLS,
    RESULTS_DIR,
    available_covariates,
    bh_fdr,
    fit_wls_cluster,
    make_results_subdir,
    sign_flip_permutation_test,
    subject_level_sensitivity,
    subject_level_slopes,
)

OUT = make_results_subdir("05_pass_c_eap_moderation")

NUISANCE_COVARIATES = [
    "event_duration_sec", "frequency_hz", "window_center_sec",
    "ocular_stability_index", "sympathetic_index", "vagal_index",
    "eog_quality_quality", "ecg_quality_quality", "anchor_support_fraction_quality",
    "anchor_quality",
]

# (dataset, anchor_column, label) — BOAS run twice: primary + sensitivity anchor
PASS_C_MODELS = [
    (DATASET_ANPHY, "ecg_hrv_rmssd_ms_pre_far", "primary"),
    (DATASET_BOAS, "resp_regular_index_pre_far", "primary"),
    (DATASET_BOAS, "anchor_index_v02_pre_far", "sensitivity"),
]

DELTA_MODES = ["event_control", "event_prefar"]


def find_latest(pattern: str) -> Path:
    candidates = sorted(RESULTS_DIR.glob(f"rvc_sleep_*/01_build_event_level_tables/{pattern}"))
    if not candidates:
        raise FileNotFoundError(f"No {pattern} found. Run 01_build_event_level_tables.py first.")
    return candidates[-1]


print(f"Loading {find_latest('event_level_primary.parquet')} ...")
event_level = pd.read_parquet(find_latest("event_level_primary.parquet"))
print(f"Loading {find_latest('pass_c_anchor_contexts.parquet')} ...")
anchor_contexts = pd.read_parquet(find_latest("pass_c_anchor_contexts.parquet"))
if "subject_id" not in anchor_contexts.columns:
    raise RuntimeError(
        "pass_c_anchor_contexts.parquet has no subject_id column — rerun "
        "01_build_event_level_tables.py with the 2026-07-03 subject-keying fix "
        "before running Pass C."
    )

event_bins = event_level[event_level["bin_label"] == "event"].copy()
event_bins = event_bins.merge(anchor_contexts, on=["dataset_id", "subject_id", "event_id"], how="left")

# For the event_prefar delta mode, aggregate each event's own pre_far bin(s)
# per endpoint (same construction as 03b_pass_a2r_subject_balanced_profile.py).
far_geom_by_dataset = {}
for endpoint in GEOMETRY_COLS:
    if endpoint not in event_level.columns:
        continue
    far = (
        event_level[event_level["bin_label"] == "pre_far"]
        .groupby(["dataset_id", "subject_id", "event_id"])[endpoint].mean()
        .rename(f"{endpoint}_far")
    )
    far_geom_by_dataset[endpoint] = far
if far_geom_by_dataset:
    far_frame = pd.concat(far_geom_by_dataset.values(), axis=1).reset_index()
    event_bins = event_bins.merge(far_frame, on=["dataset_id", "subject_id", "event_id"], how="left")

results_rows = []
slope_rows = []
for delta_mode in DELTA_MODES:
    for dataset, anchor_col, model_label in PASS_C_MODELS:
        sub_ds = event_bins[event_bins["dataset_id"] == dataset]
        if anchor_col not in sub_ds.columns:
            results_rows.append({
                "delta_mode": delta_mode, "dataset": dataset, "anchor_col": anchor_col, "model": model_label,
                "note": "anchor column not found in pass_c_anchor_contexts.parquet",
            })
            continue

        covariates = available_covariates(sub_ds, NUISANCE_COVARIATES)
        print(f"  [{delta_mode}/{dataset}/{model_label}] available covariates: {covariates}")

        for endpoint in GEOMETRY_COLS:
            ctrl_col = f"{endpoint}_control_median"
            far_col = f"{endpoint}_far"
            baseline_col = ctrl_col if delta_mode == "event_control" else far_col
            if endpoint not in sub_ds.columns or baseline_col not in sub_ds.columns:
                continue
            sub = sub_ds.dropna(subset=[endpoint, baseline_col, anchor_col, "subject_id", *covariates]).copy()
            if len(sub) < 10 or sub["subject_id"].nunique() < 5:
                results_rows.append({
                    "delta_mode": delta_mode, "dataset": dataset, "anchor_col": anchor_col, "model": model_label,
                    "endpoint": endpoint, "n_events": len(sub), "note": "insufficient N",
                })
                continue
            sub["delta"] = sub[endpoint] - sub[baseline_col]

            centered_terms = []
            for c in covariates:
                cname = f"{c}_c"
                sub[cname] = sub[c] - sub[c].mean()
                centered_terms.append(cname)

            n_events_by_subj = sub.groupby("subject_id")["subject_id"].transform("size")
            sub["_weight"] = 1.0 / n_events_by_subj

            row = {
                "delta_mode": delta_mode, "dataset": dataset, "anchor_col": anchor_col, "model": model_label,
                "endpoint": endpoint, "n_events": len(sub), "n_subjects": sub["subject_id"].nunique(),
            }

            formula = f"delta ~ {anchor_col}" + "".join(f" + {c}" for c in centered_terms)
            fit = fit_wls_cluster(formula, sub, weights_col="_weight", groups_col="subject_id")
            if fit is not None:
                row["anchor_coef"] = float(fit.params.get(anchor_col, np.nan))
                row["anchor_se"] = float(fit.bse.get(anchor_col, np.nan))
                row["anchor_p"] = float(fit.pvalues.get(anchor_col, np.nan))
            else:
                row["anchor_coef"] = row["anchor_se"] = row["anchor_p"] = np.nan

            slopes = subject_level_slopes(
                sub[anchor_col].to_numpy(), sub["delta"].to_numpy(), sub["subject_id"].to_numpy(), min_events=3,
            )
            row["n_subjects_with_slope"] = len(slopes)
            if len(slopes) >= 5:
                sens = subject_level_sensitivity(slopes.values, slopes.index.to_numpy())
                row["slope_mean"] = sens["subject_mean_delta"]
                row["slope_ttest_p"] = sens["ttest_p"]
                row["slope_wilcoxon_p"] = sens["wilcoxon_p"]
                _, perm_p = sign_flip_permutation_test(slopes.values, slopes.index.to_numpy(), n_perm=2000)
                row["slope_perm_p"] = perm_p
                for subj, b in slopes.items():
                    slope_rows.append({
                        "delta_mode": delta_mode, "dataset": dataset, "anchor_col": anchor_col,
                        "model": model_label, "endpoint": endpoint, "subject_id": subj, "slope": b,
                    })
            else:
                row["slope_mean"] = row["slope_ttest_p"] = row["slope_wilcoxon_p"] = row["slope_perm_p"] = np.nan

            results_rows.append(row)

results_df = pd.DataFrame(results_rows)
if "anchor_p" in results_df.columns:
    results_df["anchor_p_fdr"] = np.nan
    for (delta_mode, dataset, model_label), idx in results_df.groupby(["delta_mode", "dataset", "model"]).groups.items():
        mask = results_df.index.isin(idx)
        results_df.loc[mask, "anchor_p_fdr"] = bh_fdr(results_df.loc[mask, "anchor_p"].values)

print(results_df.to_string(index=False))
results_df.to_csv(OUT / "pass_c_eap_moderation.csv", index=False)
pd.DataFrame(slope_rows).to_csv(OUT / "pass_c_subject_slopes.csv", index=False)

print("\n=== Pass C complete (both delta modes) ===")
print(f"All outputs in: {OUT}")

# TODO: report the BOAS primary-anchor restricted-sample N explicitly in the
# manuscript (expected ~54/128; see handover_From_nmd.md §6 known limitation #1),
# and compare direction/magnitude between the resp_regular_index and
# anchor_index_v02 sensitivity models before drawing conclusions.
# TODO: sigma-power residualization is planned as a follow-up detector-strength
# robustness analysis; duration/window_center_sec covariates here do not
# substitute for it (sciencelead/002.md guardrail #2).
