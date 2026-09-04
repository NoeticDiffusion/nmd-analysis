"""
02c_pass_a1r_subject_weighted_specificity.py — Pass A1r: corrected primary,
subject-weighted RVC specificity.

Protocol amendment (sciencelead/001.md, 2026-07-03): the BOAS A1 heterogeneity
audit (02b_pass_a1_heterogeneity_audit.py, diary 227) showed that
02_pass_a1_rvc_specificity.py's event-weighted cluster-robust OLS
overrepresents high-event-count subjects in BOAS (median 5 events/subject,
range 1-18) specifically for `d_n`, `d_s`, `e_s` — subject-equal weighting
recovers a robust, same-direction-as-ANPHY effect for those endpoints via
event-balanced resampling, top-subject exclusion, and cluster bootstrap.

The science lead's decision: adopt an EQUAL-SUBJECT-WEIGHT estimand as the
corrected PRIMARY for Pass A1, applied identically to ANPHY and BOAS (not a
BOAS-only rescue). This script implements that corrected primary as its own
result layer ("A1r"), WITHOUT touching or overwriting the original
event-weighted table (which remains a "pre-amendment sensitivity analysis" —
see sciencelead/001.md).

Estimator (per dataset, per frozen endpoint):
    event_control_delta = event_bin_geometry - median(matched_control_geometry)   [unchanged from A1-original]
    subject_mean_delta  = mean(event_control_delta within subject)

Primary test:  subject_mean_delta ~ 1, via subject-level SIGN-FLIP PERMUTATION
               (chosen as the single formal primary p-value: robust,
               non-parametric, matches the within-subject direction question).
Sensitivity:   one-sample t-test + Wilcoxon signed-rank (reported, not primary).
Also reported: mean subject delta + 95% CI (analytic, t-based).

BH-FDR applied fresh across the frozen 18-test family (9 endpoints x 2
datasets) on the permutation p-values — a different estimand from
A1-original, so it gets its own multiplicity correction rather than reusing
A1-original's q-values.

Implementation note: this reuses subject_level_sensitivity() and
sign_flip_permutation_test() from rvc_sleep_support.py unchanged. Those
helpers already aggregate event-level values to one row per subject before
testing, so feeding them event-level event_control_delta values (as here) is
mathematically identical to first collapsing to subject_mean_delta and then
testing — no new statistics were written for A1r, only a new primary-status
result table and FDR layer.

Run: python src/02c_pass_a1r_subject_weighted_specificity.py
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

OUT = make_results_subdir("02c_pass_a1r_subject_weighted_specificity")


def find_latest_event_level_primary() -> Path:
    candidates = sorted(RESULTS_DIR.glob("rvc_sleep_*/01_build_event_level_tables/event_level_primary.parquet"))
    if not candidates:
        raise FileNotFoundError("No event_level_primary.parquet found. Run 01_build_event_level_tables.py first.")
    return candidates[-1]


print(f"Loading {find_latest_event_level_primary()} ...")
event_level = pd.read_parquet(find_latest_event_level_primary())
event_rows = event_level[event_level["bin_label"] == "event"].copy()
print(f"  {len(event_rows)} spindle 'event'-bin rows across {event_rows['dataset_id'].nunique()} dataset(s)")

results_rows = []
for dataset in DATASETS:
    sub_ds = event_rows[event_rows["dataset_id"] == dataset]
    for endpoint in GEOMETRY_COLS:
        ctrl_col = f"{endpoint}_control_median"
        if endpoint not in sub_ds.columns or ctrl_col not in sub_ds.columns:
            continue
        sub = sub_ds.dropna(subset=[endpoint, ctrl_col, "subject_id"]).copy()
        row = {
            "dataset": dataset, "endpoint": endpoint,
            "n_events": len(sub), "n_subjects": sub["subject_id"].nunique() if len(sub) else 0,
        }
        if len(sub) < 10 or row["n_subjects"] < 5:
            row["note"] = "insufficient N"
            results_rows.append(row)
            continue
        sub["event_control_delta"] = sub[endpoint] - sub[ctrl_col]

        # Subject-level collapse, done explicitly here (not just implicitly
        # inside the helpers) so mean/CI are reported on the actual estimand.
        subj_means = sub.groupby("subject_id")["event_control_delta"].mean()
        mean_delta, ci_lo, ci_hi = one_sample_ci(subj_means.values)
        row["subject_mean_delta"] = mean_delta
        row["ci95_lo"] = ci_lo
        row["ci95_hi"] = ci_hi

        # Primary: subject-level sign-flip permutation.
        perm_obs, perm_p = sign_flip_permutation_test(
            sub["event_control_delta"].values, sub["subject_id"].values, n_perm=2000
        )
        row["perm_observed_stat"] = perm_obs
        row["perm_p"] = perm_p

        # Sensitivity: one-sample t-test + Wilcoxon on the same subject means.
        sens = subject_level_sensitivity(sub["event_control_delta"].values, sub["subject_id"].values)
        row.update({f"sens_{k}": v for k, v in sens.items() if k != "n_subjects"})

        results_rows.append(row)

results_df = pd.DataFrame(results_rows)

# Frozen FDR family (9 endpoints x 2 datasets = 18 tests), applied fresh to
# the A1r primary (permutation) p-values.
if "perm_p" in results_df.columns:
    results_df["perm_p_fdr"] = bh_fdr(results_df["perm_p"].values)

print(results_df.to_string(index=False))
results_df.to_csv(OUT / "pass_a1r_subject_weighted_specificity.csv", index=False)

print("\n--- A1r vs A1-original direction check ---")
orig_candidates = sorted(RESULTS_DIR.glob("rvc_sleep_*/02_pass_a1_rvc_specificity/pass_a1_rvc_specificity.csv"))
if orig_candidates:
    orig = pd.read_csv(orig_candidates[-1])
    merged = results_df.merge(
        orig[["dataset", "endpoint", "ols_intercept_coef", "ols_intercept_p_fdr"]],
        on=["dataset", "endpoint"], how="left",
    )
    merged["sign_agree"] = np.sign(merged["subject_mean_delta"]) == np.sign(merged["ols_intercept_coef"])
    print(merged[["dataset", "endpoint", "subject_mean_delta", "perm_p_fdr",
                   "ols_intercept_coef", "ols_intercept_p_fdr", "sign_agree"]].to_string(index=False))
    merged.to_csv(OUT / "a1r_vs_a1original_comparison.csv", index=False)
else:
    print("  [skip] A1-original table not found for comparison")

print("\n=== Pass A1r complete (corrected primary; A1-original table untouched) ===")
print(f"All outputs in: {OUT}")
