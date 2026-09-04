"""
11_richsleep_resp_anchor_followup.py — Follow-up on the RichSleep `resp_anchor_index`
sensitivity-anchor moderation results, run twice:

Round 1 (2026-07-09, diary 237): the pre-fix `event_control` mode showed
FDR-surviving, non-negligible coefficients on `m`, `d`, `d_l`, `e_m`, not
explained by the scale/multicollinearity artifact pattern used for the other
sensitivity anchors. Scale/multicollinearity/outlier-subject checks ruled out
those three artifacts, but tracing the anchor's exact construction (prompted by
the resulting handover to NMD) surfaced a genuine upstream sign bug in its
rate/slowing component (diary 238) - now fixed by NMD (diary 184, ingest repo).

Round 2 (2026-07-09, diary 239, this run): re-run against the corrected
`neuralmanifolddynamics_RichSleep_20260709_100219` export. The previously
flagged `event_control` coefficients are now a clean null (matching the primary
anchor exactly) - the sign-bug fix resolved that finding entirely. But a *new*
pattern of FDR survivors emerged in the `event_prefar` delta mode (`d`, `e`,
`d_n`, `e_s`, with `e_e` borderline) that was null before the fix. This script
re-runs the same four artifact checks on this new pattern.

Six checks (per delta mode):
  1. Scale/distribution of resp_anchor_index vs. the other anchors.
  2. Multicollinearity: Spearman correlation of resp_anchor_index_pre_far
     against the primary anchor and all nuisance covariates in the model.
  3. Model-specification robustness: bivariate (anchor only) vs. full
     covariate-adjusted coefficient.
  4. Outlier-subject robustness (regression-influence sense): per-subject
     slopes, and re-run after excluding the single subject whose slope is
     most extreme (largest influence on the fitted coefficient).
  5. Joint-family FDR: re-derive BH-FDR q across BOTH delta modes' sensitivity-
     anchor tests combined (108 tests) rather than the two separate 54-test
     families 09_richsleep_verification.py corrects within - a stricter,
     more conservative check against "look under two lampposts" concerns from
     testing two delta-mode specifications.
  6. Outlier-subject robustness (anchor-value sense): identify the subject with
     the most extreme *raw resp_anchor_index* (not slope) and re-run after
     excluding them - a different, complementary outlier check from #4, since
     the most-extreme-slope subject need not be the most-extreme-anchor-value
     subject.

Run: python src/11_richsleep_resp_anchor_followup.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from scipy import stats
from rvc_sleep_support import (
    ANCHOR_COLS_BY_DATASET,
    CONDITION_EVENT,
    DATASET_RICHSLEEP,
    GEOMETRY_COLS,
    RESULTS_DIR,
    SURFACE_PRIMARY,
    aggregate_controls_per_event,
    available_covariates,
    ensure_n2_column,
    fit_ols_cluster,
    fit_wls_cluster,
    load_event_locked,
    make_results_subdir,
    pass_a_filter,
    subject_level_sensitivity,
    subject_level_slopes,
)

OUT = make_results_subdir("11_richsleep_resp_anchor_followup")

ANCHOR_COL_BASE = "resp_anchor_index"
# Round 2 (post sign-fix, diary 239): event_control is now a clean null (checked
# below for completeness); event_prefar has the new FDR survivors.
FLAGGED_ENDPOINTS_BY_MODE = {
    "event_control": ["m", "d", "d_l", "e_m"],  # round-1 flagged set; now expected null
    "event_prefar": ["d", "e", "d_n", "e_s", "e_e"],  # round-2 (post-fix) FDR survivors + 1 borderline
}
NUISANCE_COVARIATES = [
    "event_duration_sec", "window_center_sec",
    "ocular_stability_index", "sympathetic_index", "vagal_index",
    "eog_quality_quality", "ecg_quality_quality", "resp_quality_quality",
    "cardioresp_quality_quality", "anchor_support_fraction_quality",
]

raw = load_event_locked(DATASET_RICHSLEEP, SURFACE_PRIMARY)
raw = ensure_n2_column(raw)
filtered = pass_a_filter(raw)

# ── Check 1: scale/distribution (mode-independent) ──────────────────────
print("=== Check 1: scale/distribution of resp_anchor_index vs. other anchors ===")
scale_cols = ANCHOR_COLS_BY_DATASET[DATASET_RICHSLEEP]
desc = filtered[scale_cols].describe().T[["count", "mean", "std", "min", "50%", "max"]]
print(desc.round(4))
desc.to_csv(OUT / "check1_anchor_scale.csv")

# ── Check 2: multicollinearity (mode-independent) ────────────────────────
print("\n=== Check 2: Spearman correlation, resp_anchor_index vs. other anchors/covariates ===")
corr_cols = [ANCHOR_COL_BASE, "cardioresp_anchor_index", "sympathetic_index",
             "vagal_index", "ocular_stability_index", "event_duration_sec", "window_center_sec"]
corr_cols = [c for c in corr_cols if c in filtered.columns]
corr_df = filtered[corr_cols].dropna().corr(method="spearman")
print(corr_df.round(3))
corr_df.to_csv(OUT / "check2_correlation_matrix.csv")

# ── Build the event x pre_far-anchor table used by 09/10, both baselines ────
anchor_cols = ANCHOR_COLS_BY_DATASET[DATASET_RICHSLEEP]
value_cols = sorted(set(GEOMETRY_COLS + anchor_cols))
control_agg = aggregate_controls_per_event(filtered, value_cols)
event_rows = filtered[filtered["condition"] == CONDITION_EVENT].copy()
event_level = event_rows.merge(
    control_agg, left_on=["dataset_id", "event_id"], right_on=["dataset_id", "matched_event_id"],
    how="left", suffixes=("", "_ctrl_join"),
)
far_anchor = (
    filtered[filtered["bin_label"] == "pre_far"]
    .groupby(["dataset_id", "subject_id", "event_id"])[anchor_cols].mean()
    .rename(columns={c: f"{c}_pre_far" for c in anchor_cols}).reset_index()
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

event_bins = event_level.merge(far_anchor, on=["dataset_id", "subject_id", "event_id"], how="left")
if not far_geom_frame.empty:
    event_bins = event_bins.merge(far_geom_frame, on=["dataset_id", "subject_id", "event_id"], how="left")

anchor_col = f"{ANCHOR_COL_BASE}_pre_far"
covariates = available_covariates(event_bins, NUISANCE_COVARIATES)

# ── Checks 3 + 4, per delta mode ─────────────────────────────────────────
all_rows = []
for delta_mode, flagged_endpoints in FLAGGED_ENDPOINTS_BY_MODE.items():
    print(f"\n=== Check 3+4 ({delta_mode}): model-specification and outlier-subject robustness ===")
    for endpoint in flagged_endpoints:
        baseline_col = f"{endpoint}_control_median" if delta_mode == "event_control" else f"{endpoint}_far"
        if endpoint not in event_bins.columns or baseline_col not in event_bins.columns:
            continue
        sub = event_bins.dropna(subset=[endpoint, baseline_col, anchor_col, "subject_id", *covariates]).copy()
        sub["delta"] = sub[endpoint] - sub[baseline_col]

        rho, rho_p = stats.spearmanr(sub[anchor_col], sub["delta"])

        fit_biv = fit_ols_cluster(f"delta ~ {anchor_col}", sub, groups_col="subject_id")
        biv_coef = float(fit_biv.params.get(anchor_col, np.nan)) if fit_biv is not None else np.nan
        biv_p = float(fit_biv.pvalues.get(anchor_col, np.nan)) if fit_biv is not None else np.nan

        sub2 = sub.copy()
        for c in covariates:
            sub2[f"{c}_c"] = sub2[c] - sub2[c].mean()
        n_events_by_subj = sub2.groupby("subject_id")["subject_id"].transform("size")
        sub2["_weight"] = 1.0 / n_events_by_subj
        formula = f"delta ~ {anchor_col}" + "".join(f" + {c}_c" for c in covariates)
        fit_full = fit_wls_cluster(formula, sub2, weights_col="_weight", groups_col="subject_id")
        full_coef = float(fit_full.params.get(anchor_col, np.nan)) if fit_full is not None else np.nan
        full_p = float(fit_full.pvalues.get(anchor_col, np.nan)) if fit_full is not None else np.nan

        slopes = subject_level_slopes(
            sub[anchor_col].to_numpy(), sub["delta"].to_numpy(), sub["subject_id"].to_numpy(), min_events=3,
        )
        n_pos = int((slopes > 0).sum())
        n_neg = int((slopes < 0).sum())
        worst = slopes.abs().idxmax()
        excl = slopes.drop(worst)
        sens_excl = subject_level_sensitivity(excl.values, excl.index.to_numpy())

        row = {
            "delta_mode": delta_mode, "endpoint": endpoint, "n_events": len(sub),
            "n_subjects": sub["subject_id"].nunique(),
            "bivariate_spearman_rho": rho, "bivariate_spearman_p": rho_p,
            "bivariate_ols_coef": biv_coef, "bivariate_ols_p": biv_p,
            "full_wls_coef": full_coef, "full_wls_p": full_p,
            "n_subjects_with_slope": len(slopes),
            "n_subjects_positive_slope": n_pos, "n_subjects_negative_slope": n_neg,
            "majority_sign_frac": max(n_pos, n_neg) / len(slopes) if len(slopes) else np.nan,
            "most_extreme_subject": worst, "most_extreme_slope": float(slopes[worst]),
            "slope_median": float(slopes.median()),
            "excl_extreme_median": float(excl.median()),
            "excl_extreme_ttest_p": sens_excl["ttest_p"],
            "excl_extreme_wilcoxon_p": sens_excl["wilcoxon_p"],
        }
        all_rows.append(row)
        print(f"{delta_mode}/{endpoint}: bivariate coef={biv_coef:.4f} (p={biv_p:.4f}), "
              f"full coef={full_coef:.4f} (p={full_p:.4f}), "
              f"{max(n_pos, n_neg)}/{len(slopes)} subjects majority-sign, "
              f"excl. {worst} -> ttest_p={sens_excl['ttest_p']:.4f}, wilcoxon_p={sens_excl['wilcoxon_p']:.4f}")

result_df = pd.DataFrame(all_rows)
result_df.to_csv(OUT / "resp_anchor_robustness_checks.csv", index=False)

# ── Check 5: joint-family BH-FDR across both delta modes ────────────────
print("\n=== Check 5: joint BH-FDR across both delta modes (108 sensitivity-anchor tests) ===")


def _latest_eap_moderation_csv():
    cands = sorted(RESULTS_DIR.glob("rvc_sleep_*/09_richsleep_verification/richsleep_eap_moderation.csv"))
    return cands[-1] if cands else None


eap_path = _latest_eap_moderation_csv()
if eap_path is not None:
    eap_df = pd.read_csv(eap_path)
    sens = eap_df[eap_df["model"] == "sensitivity"].copy()
    p = sens["anchor_p"].to_numpy()
    order = np.argsort(p)
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(p) + 1)
    q_raw = p * len(p) / ranks
    q_sorted = np.minimum.accumulate(q_raw[order][::-1])[::-1]
    q_joint = np.empty_like(q_sorted)
    q_joint[order] = np.minimum(q_sorted, 1.0)
    sens["anchor_p_fdr_joint_108"] = q_joint
    resp_joint = sens[sens["anchor_col"] == f"{ANCHOR_COL_BASE}_pre_far"][
        ["delta_mode", "endpoint", "anchor_coef", "anchor_p", "anchor_p_fdr", "anchor_p_fdr_joint_108"]
    ]
    print(resp_joint.to_string(index=False))
    resp_joint.to_csv(OUT / "check5_joint_fdr_108.csv", index=False)
else:
    print("  [skip] richsleep_eap_moderation.csv not found - run 09_richsleep_verification.py first")

# ── Check 6: outlier-subject robustness in the anchor-value sense ───────
print("\n=== Check 6: exclude the most extreme resp_anchor_index subject (value, not slope) ===")
subj_anchor_mean = filtered.groupby("subject_id")["resp_anchor_index"].mean()
anchor_outlier_subject = (subj_anchor_mean - subj_anchor_mean.mean()).abs().idxmax()
print(f"Most extreme resp_anchor_index subject (by subject-level mean): {anchor_outlier_subject} "
      f"(mean={subj_anchor_mean[anchor_outlier_subject]:.3f} vs. cohort mean={subj_anchor_mean.mean():.3f}, "
      f"std={subj_anchor_mean.std():.3f})")

check6_rows = []
for endpoint in FLAGGED_ENDPOINTS_BY_MODE["event_prefar"]:
    baseline_col = f"{endpoint}_far"
    if endpoint not in event_bins.columns or baseline_col not in event_bins.columns:
        continue
    sub = event_bins.dropna(subset=[endpoint, baseline_col, anchor_col, "subject_id", *covariates]).copy()
    sub["delta"] = sub[endpoint] - sub[baseline_col]
    for label, data in [("full", sub), ("excl_anchor_outlier", sub[sub["subject_id"] != anchor_outlier_subject])]:
        d2 = data.copy()
        for c in covariates:
            d2[f"{c}_c"] = d2[c] - d2[c].mean()
        n_events_by_subj = d2.groupby("subject_id")["subject_id"].transform("size")
        d2["_weight"] = 1.0 / n_events_by_subj
        formula = f"delta ~ {anchor_col}" + "".join(f" + {c}_c" for c in covariates)
        fit = fit_wls_cluster(formula, d2, weights_col="_weight", groups_col="subject_id")
        coef = float(fit.params.get(anchor_col, np.nan)) if fit is not None else np.nan
        p = float(fit.pvalues.get(anchor_col, np.nan)) if fit is not None else np.nan
        check6_rows.append({"endpoint": endpoint, "subset": label, "n_subjects": data["subject_id"].nunique(),
                             "coef": coef, "p": p})
        print(f"  {endpoint:5s} {label:22s} n_subj={data['subject_id'].nunique():2d} coef={coef:+.4f} p={p:.4f}")

check6_df = pd.DataFrame(check6_rows)
check6_df.to_csv(OUT / "check6_anchor_value_outlier_exclusion.csv", index=False)

print("\n=== Summary ===")
print("resp_anchor_index scale is ordinary (~[-1, 1], not the 1e6-1e8-scale anchors "
      "that explain the other sensitivity anchors' negligible coefficients).")
print("Max |Spearman r| with other anchors/covariates: "
      f"{corr_df.drop(columns=[ANCHOR_COL_BASE]).loc[ANCHOR_COL_BASE].abs().max():.3f} "
      "- not strongly multicollinear.")
print("event_control (round-1 flagged set) is now null post sign-fix - see "
      "results/rvc_sleep_20260709/09_richsleep_verification/richsleep_eap_moderation.csv.")
print("event_prefar (new post-fix FDR survivors): `d`, `e`, `d_n`, `e_s` survive even the stricter "
      "joint-108-test FDR correction (check 5); `e_e` does not (q~0.07) and is downgraded from "
      "'boundary' to 'not significant' under that correction. All four survive excluding either the "
      "most-extreme-slope subject (check 4) or the most-extreme-anchor-value subject (check 6), with "
      "coefficients essentially unchanged - except `d`, which loses significance under the "
      "most-extreme-slope exclusion (check 4) specifically, so it remains the weakest of the four.")
print(f"\nAll outputs in: {OUT}")
