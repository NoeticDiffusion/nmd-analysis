"""
09_richsleep_verification.py — RichSleep as a THIRD, independent verification
dataset for RVC_SLEEP.

Context (diary 231, 2026-07-04): Pass A/B/C on ANPHY + BOAS are frozen
(sciencelead/004.md). RichSleep was ingested afterwards as a fully separate
NMD run (primary_eeg_only surface, same coordinate contract
`rvc_v1_eeg_only_e_m` and same 9D subcoord weights as ANPHY/BOAS primary) and
is used here ONLY to:

  (a) Sanity-check the run (subject count, config_hash, event/control
      coverage, anchor coverage) — mirrors 00_sanity_check.py.
  (b) Replicate the frozen A1r (event vs. matched-control) and A2r
      (event vs. pre_far, within-spindle) subject-weighted estimands
      out-of-sample, using the exact same statistics helpers as
      02c/03b, and report sign-agreement against the frozen ANPHY/BOAS
      A1r/A2r tables.
  (c) Run a "proper" EAP moderation test (Pass-C-style) using RichSleep's
      composite `cardioresp_anchor_index` as the primary anchor. Unlike
      ANPHY (cardiac-only) and BOAS (resp-only, ~66/128 missing),
      RichSleep has simultaneous near-complete ECG+resp+EOG+EMG coverage,
      so this is the first EAP-moderation test in this article without a
      single-channel-missingness caveat. Sensitivity anchors
      (sympathetic_index, resp_anchor_index, ocular_stability_index,
      anchor_index_v02) are also run.

This script does NOT modify ANPHY/BOAS data, DATASETS, or any frozen
Pass A/B/C script/result. RichSleep results live in their own
`09_richsleep_verification/` results subfolder.

RichSleep has no `n2`/`n3`/`rem`/`wake` indicator columns — `n2` is derived
from the numeric `stage` codebook via `ensure_n2_column()` before
`pass_a_filter()` is applied (RichSleep stage 2 == N2).

Run: python src/09_richsleep_verification.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from rvc_sleep_support import (
    ANCHOR_COLS_BY_DATASET,
    CONDITION_EVENT,
    CONFIG_HASH,
    DATASET_RICHSLEEP,
    EXPECTED_N_SUBJECTS,
    GEOMETRY_COLS,
    PRIMARY_ANCHOR_COL,
    RESULTS_DIR,
    SURFACE_PRIMARY,
    aggregate_controls_per_event,
    available_covariates,
    bh_fdr,
    ensure_n2_column,
    fit_wls_cluster,
    load_event_locked,
    make_results_subdir,
    one_sample_ci,
    pass_a_filter,
    run_root,
    sign_flip_permutation_test,
    subject_level_sensitivity,
    subject_level_slopes,
)

OUT = make_results_subdir("09_richsleep_verification")

NUISANCE_COVARIATES = [
    "event_duration_sec", "window_center_sec",
    "ocular_stability_index", "sympathetic_index", "vagal_index",
    "eog_quality_quality", "ecg_quality_quality", "resp_quality_quality",
    "cardioresp_quality_quality", "anchor_support_fraction_quality",
]

RICHSLEEP_SENSITIVITY_ANCHORS = [
    a for a in ANCHOR_COLS_BY_DATASET[DATASET_RICHSLEEP]
    if a != PRIMARY_ANCHOR_COL[DATASET_RICHSLEEP]
]

# ─────────────────────────────────────────────────────────────────────────
# (a) Sanity check
# ─────────────────────────────────────────────────────────────────────────
print("=== (a) RichSleep sanity check ===")
root = run_root(DATASET_RICHSLEEP, SURFACE_PRIMARY)
import json

manifest = json.loads((root / "run_manifest.json").read_text())
digest = manifest.get("config", {}).get("digest_sha256", "")[:16]
expected_digest = CONFIG_HASH[(DATASET_RICHSLEEP, SURFACE_PRIMARY)]
print(f"  run_dir: {root}")
print(f"  config_hash: {digest} (expected {expected_digest}) -> {'OK' if digest == expected_digest else 'MISMATCH'}")

raw = load_event_locked(DATASET_RICHSLEEP, SURFACE_PRIMARY)
raw = ensure_n2_column(raw)
n_subjects = raw["subject_id"].nunique()
print(f"  n_subjects: {n_subjects} (expected {EXPECTED_N_SUBJECTS[DATASET_RICHSLEEP]}) -> "
      f"{'OK' if n_subjects == EXPECTED_N_SUBJECTS[DATASET_RICHSLEEP] else 'MISMATCH'}")

sanity_rows = [{
    "check": "config_hash", "observed": digest, "expected": expected_digest,
    "pass": digest == expected_digest,
}, {
    "check": "n_subjects", "observed": n_subjects, "expected": EXPECTED_N_SUBJECTS[DATASET_RICHSLEEP],
    "pass": n_subjects == EXPECTED_N_SUBJECTS[DATASET_RICHSLEEP],
}]

filtered = pass_a_filter(raw)
sanity_rows.append({
    "check": "pass_a_filter_coverage", "observed": len(filtered), "expected": f"of {len(raw)} raw rows",
    "pass": len(filtered) > 0,
})
print(f"  pass_a_filter: {len(filtered)}/{len(raw)} rows retained (N2 + coords_9d_finite)")

for col in [PRIMARY_ANCHOR_COL[DATASET_RICHSLEEP], *RICHSLEEP_SENSITIVITY_ANCHORS]:
    if col in filtered.columns:
        coverage = filtered[col].notna().mean()
        sanity_rows.append({"check": f"anchor_coverage[{col}]", "observed": round(float(coverage), 4),
                             "expected": ">=0.9 (verification target)", "pass": coverage >= 0.9})
        print(f"  anchor coverage [{col}]: {coverage:.4f}")

pd.DataFrame(sanity_rows).to_csv(OUT / "sanity_check.csv", index=False)

# ─────────────────────────────────────────────────────────────────────────
# Build event-level table (mirrors 01_build_event_level_tables.py, RichSleep only)
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Building RichSleep event-level table ===")
anchor_cols = [c for c in ANCHOR_COLS_BY_DATASET[DATASET_RICHSLEEP] if c in filtered.columns]
value_cols = sorted(set([c for c in GEOMETRY_COLS if c in filtered.columns] + anchor_cols))

control_agg = aggregate_controls_per_event(filtered, value_cols)
event_rows = filtered[filtered["condition"] == CONDITION_EVENT].copy()
event_level = event_rows.merge(
    control_agg, left_on=["dataset_id", "event_id"], right_on=["dataset_id", "matched_event_id"],
    how="left", suffixes=("", "_ctrl_join"),
)
print(f"  event_level: {event_level.shape}")
event_level.to_parquet(OUT / "event_level_richsleep.parquet", index=False)

# pre_far anchor context, one row per (subject_id, event_id)
far_anchor = (
    filtered[filtered["bin_label"] == "pre_far"]
    .groupby(["dataset_id", "subject_id", "event_id"])[anchor_cols].mean()
    .rename(columns={c: f"{c}_pre_far" for c in anchor_cols})
    .reset_index()
)
far_geom = {}
for endpoint in GEOMETRY_COLS:
    if endpoint not in filtered.columns:
        continue
    far_geom[endpoint] = (
        filtered[filtered["bin_label"] == "pre_far"]
        .groupby(["dataset_id", "subject_id", "event_id"])[endpoint].mean()
        .rename(f"{endpoint}_far")
    )
far_geom_frame = pd.concat(far_geom.values(), axis=1).reset_index() if far_geom else pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────
# (b) A1r replication: event vs matched-control, subject-weighted
# ─────────────────────────────────────────────────────────────────────────
print("\n=== (b1) A1r-style replication: event vs matched-control ===")
a1r_rows = []
for endpoint in GEOMETRY_COLS:
    ctrl_col = f"{endpoint}_control_median"
    if endpoint not in event_level.columns or ctrl_col not in event_level.columns:
        continue
    sub = event_level.dropna(subset=[endpoint, ctrl_col, "subject_id"]).copy()
    row = {"endpoint": endpoint, "n_events": len(sub), "n_subjects": sub["subject_id"].nunique() if len(sub) else 0}
    if len(sub) < 10 or row["n_subjects"] < 5:
        row["note"] = "insufficient N"
        a1r_rows.append(row)
        continue
    sub["event_control_delta"] = sub[endpoint] - sub[ctrl_col]
    subj_means = sub.groupby("subject_id")["event_control_delta"].mean()
    mean_delta, ci_lo, ci_hi = one_sample_ci(subj_means.values)
    row["subject_mean_delta"] = mean_delta
    row["ci95_lo"] = ci_lo
    row["ci95_hi"] = ci_hi
    perm_obs, perm_p = sign_flip_permutation_test(
        sub["event_control_delta"].values, sub["subject_id"].values, n_perm=2000
    )
    row["perm_observed_stat"] = perm_obs
    row["perm_p"] = perm_p
    sens = subject_level_sensitivity(sub["event_control_delta"].values, sub["subject_id"].values)
    row.update({f"sens_{k}": v for k, v in sens.items() if k != "n_subjects"})
    a1r_rows.append(row)

a1r_df = pd.DataFrame(a1r_rows)
if "perm_p" in a1r_df.columns:
    a1r_df["perm_p_fdr"] = bh_fdr(a1r_df["perm_p"].values)
print(a1r_df.to_string(index=False))
a1r_df.to_csv(OUT / "richsleep_a1r_specificity.csv", index=False)

# ─────────────────────────────────────────────────────────────────────────
# (b2) A2r replication: event vs pre_far, within-spindle
# ─────────────────────────────────────────────────────────────────────────
print("\n=== (b2) A2r-style replication: event vs pre_far ===")
a2r_rows = []
for endpoint in GEOMETRY_COLS:
    if endpoint not in filtered.columns:
        continue
    ev_vals = (
        filtered[filtered["bin_label"] == "event"]
        .groupby(["subject_id", "event_id"])[endpoint].mean().rename("event_val")
    )
    far_vals = (
        filtered[filtered["bin_label"] == "pre_far"]
        .groupby(["subject_id", "event_id"])[endpoint].mean().rename("far_val")
    )
    paired = pd.concat([ev_vals, far_vals], axis=1).dropna()
    row = {"endpoint": endpoint, "n_events_paired": len(paired),
           "n_subjects": paired.index.get_level_values("subject_id").nunique() if len(paired) else 0}
    if len(paired) < 10 or row["n_subjects"] < 5:
        row["note"] = "insufficient N"
        a2r_rows.append(row)
        continue
    paired["within_spindle_delta"] = paired["event_val"] - paired["far_val"]
    deltas = paired["within_spindle_delta"].reset_index()
    subj_means = deltas.groupby("subject_id")["within_spindle_delta"].mean()
    mean_delta, ci_lo, ci_hi = one_sample_ci(subj_means.values)
    row["subject_mean_delta"] = mean_delta
    row["ci95_lo"] = ci_lo
    row["ci95_hi"] = ci_hi
    perm_obs, perm_p = sign_flip_permutation_test(
        deltas["within_spindle_delta"].values, deltas["subject_id"].values, n_perm=2000
    )
    row["perm_observed_stat"] = perm_obs
    row["perm_p"] = perm_p
    sens = subject_level_sensitivity(deltas["within_spindle_delta"].values, deltas["subject_id"].values)
    row.update({f"sens_{k}": v for k, v in sens.items() if k != "n_subjects"})
    a2r_rows.append(row)

a2r_df = pd.DataFrame(a2r_rows)
if "perm_p" in a2r_df.columns:
    a2r_df["perm_p_fdr"] = bh_fdr(a2r_df["perm_p"].values)
print(a2r_df.to_string(index=False))
a2r_df.to_csv(OUT / "richsleep_a2r_profile.csv", index=False)

# Cross-dataset sign-agreement check against frozen ANPHY/BOAS A1r/A2r tables
print("\n--- Sign agreement vs frozen ANPHY/BOAS A1r/A2r ---")


def latest(pattern: str):
    cands = sorted(RESULTS_DIR.glob(pattern))
    return cands[-1] if cands else None


a1r_frozen_path = latest("rvc_sleep_*/02c_pass_a1r_subject_weighted_specificity/pass_a1r_subject_weighted_specificity.csv")
a2r_frozen_path = latest("rvc_sleep_*/03b_pass_a2r_subject_balanced_profile/pass_a2r_subject_balanced_profile.csv")

if a1r_frozen_path is not None:
    frozen = pd.read_csv(a1r_frozen_path)
    frozen_dir = frozen.groupby("endpoint")["subject_mean_delta"].mean().apply(np.sign)
    a1r_df["frozen_sign_anphy_boas"] = a1r_df["endpoint"].map(frozen_dir)
    a1r_df["sign_agree_with_frozen"] = np.sign(a1r_df["subject_mean_delta"]) == a1r_df["frozen_sign_anphy_boas"]
    print("A1r sign agreement:")
    print(a1r_df[["endpoint", "subject_mean_delta", "perm_p_fdr", "sign_agree_with_frozen"]].to_string(index=False))
    a1r_df.to_csv(OUT / "richsleep_a1r_specificity.csv", index=False)
else:
    print("  [skip] frozen A1r table not found")

if a2r_frozen_path is not None:
    frozen2 = pd.read_csv(a2r_frozen_path)
    frozen2_dir = frozen2.groupby("endpoint")["subject_mean_delta"].mean().apply(np.sign)
    a2r_df["frozen_sign_anphy_boas"] = a2r_df["endpoint"].map(frozen2_dir)
    a2r_df["sign_agree_with_frozen"] = np.sign(a2r_df["subject_mean_delta"]) == a2r_df["frozen_sign_anphy_boas"]
    print("A2r sign agreement:")
    print(a2r_df[["endpoint", "subject_mean_delta", "perm_p_fdr", "sign_agree_with_frozen"]].to_string(index=False))
    a2r_df.to_csv(OUT / "richsleep_a2r_profile.csv", index=False)
else:
    print("  [skip] frozen A2r table not found")

# ─────────────────────────────────────────────────────────────────────────
# (c) "Proper EAP" moderation (Pass-C-style), primary + sensitivity anchors
# ─────────────────────────────────────────────────────────────────────────
print("\n=== (c) Proper EAP moderation (cardioresp_anchor_index + sensitivity anchors) ===")
event_bins = event_level.merge(far_anchor, on=["dataset_id", "subject_id", "event_id"], how="left")
if not far_geom_frame.empty:
    event_bins = event_bins.merge(far_geom_frame, on=["dataset_id", "subject_id", "event_id"], how="left")

anchor_models = [(PRIMARY_ANCHOR_COL[DATASET_RICHSLEEP], "primary")] + [
    (a, "sensitivity") for a in RICHSLEEP_SENSITIVITY_ANCHORS
]
DELTA_MODES = ["event_control", "event_prefar"]

eap_rows = []
slope_rows = []
for delta_mode in DELTA_MODES:
    for anchor_base, model_label in anchor_models:
        anchor_col = f"{anchor_base}_pre_far"
        if anchor_col not in event_bins.columns:
            continue
        covariates = available_covariates(event_bins, NUISANCE_COVARIATES)
        for endpoint in GEOMETRY_COLS:
            ctrl_col = f"{endpoint}_control_median"
            far_col = f"{endpoint}_far"
            baseline_col = ctrl_col if delta_mode == "event_control" else far_col
            if endpoint not in event_bins.columns or baseline_col not in event_bins.columns:
                continue
            sub = event_bins.dropna(subset=[endpoint, baseline_col, anchor_col, "subject_id", *covariates]).copy()
            row = {"delta_mode": delta_mode, "anchor_col": anchor_col, "model": model_label,
                   "endpoint": endpoint, "n_events": len(sub),
                   "n_subjects": sub["subject_id"].nunique() if len(sub) else 0}
            if len(sub) < 10 or row["n_subjects"] < 5:
                row["note"] = "insufficient N"
                eap_rows.append(row)
                continue
            sub["delta"] = sub[endpoint] - sub[baseline_col]

            centered_terms = []
            for c in covariates:
                cname = f"{c}_c"
                sub[cname] = sub[c] - sub[c].mean()
                centered_terms.append(cname)

            n_events_by_subj = sub.groupby("subject_id")["subject_id"].transform("size")
            sub["_weight"] = 1.0 / n_events_by_subj

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
                    slope_rows.append({"delta_mode": delta_mode, "anchor_col": anchor_col,
                                        "model": model_label, "endpoint": endpoint, "subject_id": subj, "slope": b})
            else:
                row["slope_mean"] = row["slope_ttest_p"] = row["slope_wilcoxon_p"] = row["slope_perm_p"] = np.nan

            eap_rows.append(row)

eap_df = pd.DataFrame(eap_rows)
if "anchor_p" in eap_df.columns:
    eap_df["anchor_p_fdr"] = np.nan
    for (delta_mode, model_label), idx in eap_df.groupby(["delta_mode", "model"]).groups.items():
        mask = eap_df.index.isin(idx)
        eap_df.loc[mask, "anchor_p_fdr"] = bh_fdr(eap_df.loc[mask, "anchor_p"].values)

print(eap_df.to_string(index=False))
eap_df.to_csv(OUT / "richsleep_eap_moderation.csv", index=False)
pd.DataFrame(slope_rows).to_csv(OUT / "richsleep_eap_subject_slopes.csv", index=False)

print("\n=== RichSleep verification complete ===")
print(f"All outputs in: {OUT}")
