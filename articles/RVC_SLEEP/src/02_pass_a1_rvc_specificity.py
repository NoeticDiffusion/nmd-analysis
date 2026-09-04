"""
02_pass_a1_rvc_specificity.py — Pass A1: primary RVC specificity.

Corrected Pass A structure (plan2.md "Key analysis correction"): because
matched_control rows only carry a single `control` bin (no peri-event
timecourse), the primary specificity test is a per-event delta against the
aggregated matched-control baseline, NOT a symmetric
`geometry ~ condition * bin_label` model.

For each spindle event (bin_label == "event"):
    y_event_control = geometry_event_bin - control_median   (control_median
                      from event_level_primary.parquet, built in script 01)

2026-07-02 correction: the original MixedLM(y ~ 1 + covariates, groups=subject)
degenerated for several endpoints on this one-row-per-event table (singular
random-effects covariance, coefficients collapsing to ~1e-17 with p=1.0) —
too little within-subject replication for a random intercept to be
identified. Replaced with an explicit, preregistered fallback hierarchy that
does not require estimating a subject-level variance component:

  A1-primary:     OLS  y ~ 1 + <available covariates>, cluster-robust SE by subject_id
  A1-sensitivity1: subject-level mean delta -> one-sample t-test + Wilcoxon signed-rank vs 0
  A1-sensitivity2: within-subject sign-flip permutation test (non-parametric)

BH-FDR is applied only to the A1-primary (OLS) p-values, across the frozen
9-endpoint x 2-dataset family (<=18 tests) — the sensitivity analyses are
reported raw as convergence/robustness checks on the primary result, not as
separate hypothesis tests.

Run: python src/02_pass_a1_rvc_specificity.py
Requires: 01_build_event_level_tables.py to have been run first (reads its
          most recent output from results/rvc_sleep_<date>/01_build_event_level_tables/).
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
    available_covariates,
    bh_fdr,
    fit_ols_cluster,
    make_results_subdir,
    sign_flip_permutation_test,
    subject_level_sensitivity,
)

OUT = make_results_subdir("02_pass_a1_rvc_specificity")

CANDIDATE_COVARIATES = [
    "event_duration_sec", "frequency_hz", "window_center_sec",
    "match_distance", "anchor_quality",
]


def find_latest_event_level_primary() -> Path:
    """Locate the most recently written event_level_primary.parquet under results/."""
    candidates = sorted(RESULTS_DIR.glob("rvc_sleep_*/01_build_event_level_tables/event_level_primary.parquet"))
    if not candidates:
        raise FileNotFoundError(
            "No event_level_primary.parquet found. Run 01_build_event_level_tables.py first."
        )
    return candidates[-1]


print(f"Loading {find_latest_event_level_primary()} ...")
event_level = pd.read_parquet(find_latest_event_level_primary())
event_rows = event_level[event_level["bin_label"] == "event"].copy()
print(f"  {len(event_rows)} spindle 'event'-bin rows across {event_rows['dataset_id'].nunique()} dataset(s)")

results_rows = []
for dataset in DATASETS:
    sub_ds = event_rows[event_rows["dataset_id"] == dataset]
    # Covariate availability (presence AND >=50% non-NaN coverage) is checked
    # per dataset: e.g. match_distance may be fully populated in one dataset
    # and entirely absent/NaN in another.
    covariates = available_covariates(sub_ds, CANDIDATE_COVARIATES)
    print(f"  [{dataset}] available covariates: {covariates}")

    for endpoint in GEOMETRY_COLS:
        ctrl_col = f"{endpoint}_control_median"
        if endpoint not in sub_ds.columns or ctrl_col not in sub_ds.columns:
            continue
        sub = sub_ds.dropna(subset=[endpoint, ctrl_col, "subject_id", *covariates]).copy()
        row = {
            "dataset": dataset, "endpoint": endpoint,
            "n_events": len(sub), "n_subjects": sub["subject_id"].nunique() if len(sub) else 0,
        }
        if len(sub) < 10:
            row["note"] = "insufficient N"
            results_rows.append(row)
            continue
        sub["y_event_control"] = sub[endpoint] - sub[ctrl_col]

        row["mean_y_event_control"] = float(sub["y_event_control"].mean())
        row["median_y_event_control"] = float(sub["y_event_control"].median())

        # A1-primary: OLS, cluster-robust SE by subject
        formula = "y_event_control ~ 1" + "".join(f" + {c}" for c in covariates)
        fit = fit_ols_cluster(formula, sub, groups_col="subject_id")
        if fit is not None:
            row["ols_intercept_coef"] = float(fit.params.get("Intercept", np.nan))
            row["ols_intercept_se"] = float(fit.bse.get("Intercept", np.nan))
            row["ols_intercept_p"] = float(fit.pvalues.get("Intercept", np.nan))
        else:
            row["ols_intercept_coef"] = np.nan
            row["ols_intercept_se"] = np.nan
            row["ols_intercept_p"] = np.nan

        # A1-sensitivity 1: subject-level mean delta, t-test + Wilcoxon vs 0
        sens1 = subject_level_sensitivity(sub["y_event_control"].values, sub["subject_id"].values)
        row.update({f"subj_{k}": v for k, v in sens1.items()})

        # A1-sensitivity 2: within-subject sign-flip permutation
        perm_obs, perm_p = sign_flip_permutation_test(
            sub["y_event_control"].values, sub["subject_id"].values, n_perm=2000
        )
        row["perm_observed_stat"] = perm_obs
        row["perm_p"] = perm_p

        results_rows.append(row)

results_df = pd.DataFrame(results_rows)

# Frozen FDR family: all 9 endpoints x 2 datasets tested here (<=18 tests),
# per plan2.md "freeze a small endpoint family first". Applied once, across
# the whole family, to the A1-primary (OLS) p-values only — sensitivity
# analyses 1 and 2 are robustness checks on the same test, not additional
# hypotheses, and are reported raw.
if "ols_intercept_p" in results_df.columns:
    results_df["ols_intercept_p_fdr"] = bh_fdr(results_df["ols_intercept_p"].values)

print(results_df.to_string(index=False))
results_df.to_csv(OUT / "pass_a1_rvc_specificity.csv", index=False)

# Convergence/agreement summary: how often do the three methods agree on sign?
print("\n--- Cross-method sign agreement (informal convergence check) ---")
usable = results_df.dropna(subset=["ols_intercept_coef", "subj_subject_mean_delta"])
if len(usable):
    agree = (
        (np.sign(usable["ols_intercept_coef"]) == np.sign(usable["subj_subject_mean_delta"]))
        & (np.sign(usable["subj_subject_mean_delta"]) == np.sign(usable["perm_observed_stat"]))
    )
    print(f"  All three methods agree on sign: {agree.sum()}/{len(usable)} endpoint x dataset rows")

print("\n=== Pass A1 complete ===")
print(f"All outputs in: {OUT}")
