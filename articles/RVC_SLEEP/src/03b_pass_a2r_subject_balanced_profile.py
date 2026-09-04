"""
03b_pass_a2r_subject_balanced_profile.py — Pass A2r: subject-balanced
companion to the A2 peri-spindle timing claim.

Protocol amendment (sciencelead/001.md, 2026-07-03): the same sparse/uneven
event-count concern behind the A1r amendment also applies to A2's
event-vs-pre_far row counts per subject. This script adds a subject-balanced
robustness check scoped to A2's headline timing contrast (event vs. pre_far)
for the frozen 9 endpoints — it does NOT replace the full multi-contrast
MixedLM profile in 03_pass_a2_peri_spindle_profile.py, which stays as-is.

Each spindle event has 1 "event" bin row and 1-2 "pre_far" bin rows (multiple
far-offset samples per event; see 01_build_event_level_tables.py). Estimator:

    within_spindle_delta = event_bin_value - mean(pre_far bin values for the SAME event)
    subject_mean_delta   = mean(within_spindle_delta within subject)

paired by (dataset_id, subject_id, event_id) so the far-baseline used for each
event's delta is that event's own far-window samples, not a pooled baseline.

Primary test: subject_mean_delta ~ 1, subject-level sign-flip permutation
(same choice and same helper as A1r). Sensitivity: one-sample t-test +
Wilcoxon. BH-FDR fresh across the frozen 18-test family (9 endpoints x 2
datasets).

If A2's original `d_n`/`e_s` event-vs-pre_far result survives this
subject-balanced version, the RVC timing claim is substantially strengthened
(per the science lead: "If the current A2 d_n/e_s result survives this, the
timing claim becomes much stronger.").

Run: python src/03b_pass_a2r_subject_balanced_profile.py
Requires: 01_build_event_level_tables.py to have been run first.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from rvc_sleep_support import (
    DATASETS,
    GEOMETRY_COLS,
    RESULTS_DIR,
    bh_fdr,
    make_results_subdir,
    one_sample_ci,
    sign_flip_permutation_test,
    subject_level_sensitivity,
)

OUT = make_results_subdir("03b_pass_a2r_subject_balanced_profile")


def find_latest_event_level_primary() -> Path:
    candidates = sorted(RESULTS_DIR.glob("rvc_sleep_*/01_build_event_level_tables/event_level_primary.parquet"))
    if not candidates:
        raise FileNotFoundError("No event_level_primary.parquet found. Run 01_build_event_level_tables.py first.")
    return candidates[-1]


print(f"Loading {find_latest_event_level_primary()} ...")
event_level = pd.read_parquet(find_latest_event_level_primary())
print(f"  {len(event_level)} total rows across {event_level['dataset_id'].nunique()} dataset(s)")

results_rows = []
for dataset in DATASETS:
    sub_ds = event_level[event_level["dataset_id"] == dataset]
    n_ev = sub_ds.loc[sub_ds["bin_label"] == "event", "event_id"].nunique()
    n_far = sub_ds.loc[sub_ds["bin_label"] == "pre_far", "event_id"].nunique()
    print(f"  [{dataset}] {n_ev} unique 'event' event_ids, {n_far} unique 'pre_far' event_ids (per-subject-local IDs)")

    for endpoint in GEOMETRY_COLS:
        if endpoint not in sub_ds.columns:
            continue
        ev_vals = (
            sub_ds[sub_ds["bin_label"] == "event"]
            .groupby(["subject_id", "event_id"])[endpoint].mean()
            .rename("event_val")
        )
        far_vals = (
            sub_ds[sub_ds["bin_label"] == "pre_far"]
            .groupby(["subject_id", "event_id"])[endpoint].mean()
            .rename("far_val")
        )
        paired = pd.concat([ev_vals, far_vals], axis=1).dropna()
        row = {
            "dataset": dataset, "endpoint": endpoint,
            "n_events_paired": len(paired),
            "n_subjects": paired.index.get_level_values("subject_id").nunique() if len(paired) else 0,
        }
        if len(paired) < 10 or row["n_subjects"] < 5:
            row["note"] = "insufficient N"
            results_rows.append(row)
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

        results_rows.append(row)

results_df = pd.DataFrame(results_rows)

if "perm_p" in results_df.columns:
    results_df["perm_p_fdr"] = bh_fdr(results_df["perm_p"].values)

print(results_df.to_string(index=False))
results_df.to_csv(OUT / "pass_a2r_subject_balanced_profile.csv", index=False)

print("\n--- A2r headline check: d_n / e_s event-vs-pre_far ---")
headline = results_df[results_df["endpoint"].isin(["d_n", "e_s"])]
print(headline.to_string(index=False))

print("\n=== Pass A2r complete (03_pass_a2_peri_spindle_profile.py untouched) ===")
print(f"All outputs in: {OUT}")
