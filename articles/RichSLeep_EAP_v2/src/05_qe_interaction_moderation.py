"""
05_qe_interaction_moderation.py -- Does intrinsic spindle strength (qe)
moderate the resp-peak-alignment -> geometry-delta relationship? (Phase 3,
task 8 of .cursor/plans/richsleep_eap_v2_article_aa3119f9.plan.md;
manuscript Part 2, the N2 efficacy test).

Context: RVC_SLEEP_peak_analysis's 13_peak_phase_alignment_moderation.py
(diary 243) found 2/18 FDR-significant *main-effect* alignment->delta tests
on the 190 geometry-valid N2 spindles, using `resp_peak_alignment = cos(
phi_resp_peak - mu_resp_peak)` (mu_resp_peak = held-out, subject-balanced
population-preferred peak phase). `phase_resolved_v3` newly adds per-event
intrinsic strength (`sigma_power_z_n2`, `amplitude`, `frequency_hz`) and
SO-spindle coupling (`so_spindle_coupling_score`, `so_amplitude`) -- this
script asks whether a *stronger* spindle shows a *larger* alignment effect
(an interaction, i.e. a step toward "efficacy" rather than mere "timing").

Design (mirrors 13_peak_phase_alignment_moderation.py's held-out mu_resp_peak
construction exactly, recomputed here from this article's own phase_resolved_v3
catalog for self-containment):

  Primary family (N=190, well-powered): `delta ~ resp_peak_alignment * qe +
  covariates` via `fit_wls_cluster`, qe = log1p(sigma_power_z_n2) (robustified;
  raw sigma_power_z_n2 is heavily right-skewed, skew~2.75). Tests the
  INTERACTION term across 9 geometry endpoints x 2 delta modes = 18 tests,
  BH-FDR; main effects (alignment, qe) reported alongside, not FDR-corrected
  (not the primary question here).

  Robustness: repeat with qe = amplitude (log1p) and qe = raw
  sigma_power_z_n2 (untransformed) -- reported, not re-FDR-corrected (same
  18-test family structure, different qe operationalization).

  Secondary/exploratory (N=25 events / 15 subjects, the true SO-coupled
  subset): descriptive delta vs. so_spindle_coupling_score/so_amplitude,
  explicitly labeled non-confirmatory -- too few degrees of freedom for an
  interaction model or a BH-FDR family.

Run: python src/05_qe_interaction_moderation.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from rvc_sleep_support import (
    GEOMETRY_COLS,
    RESULTS_DIR,
    available_covariates,
    bh_fdr,
    circular_mean_resultant,
    fit_wls_cluster,
    load_phase_v3,
    make_results_subdir,
)

OUT = make_results_subdir("05_qe_interaction_moderation")

NUISANCE_COVARIATES = [
    "event_duration_sec", "window_center_sec",
    "ocular_stability_index", "sympathetic_index", "vagal_index",
    "eog_quality_quality", "ecg_quality_quality", "resp_quality_quality",
    "cardioresp_quality_quality", "anchor_support_fraction_quality",
]
DELTA_MODES = ["event_control", "event_prefar"]

# ─────────────────────────────────────────────────────────────────────────
# Load the 190-event merged table + full catalog for held-out mu_resp_peak
# ─────────────────────────────────────────────────────────────────────────
merged_path = sorted(RESULTS_DIR.glob("rvc_sleep_v2_*/02_build_merged_table/richsleep_event_phase_v3_merged.parquet"))
if not merged_path:
    raise RuntimeError("richsleep_event_phase_v3_merged.parquet not found -- run 02_build_merged_table.py first.")
merged = pd.read_parquet(merged_path[-1]).copy()
print(f"Loaded {len(merged)} geometry-valid events, {merged['subject_id'].nunique()} subjects "
      f"from {merged_path[-1]}")

full_df = load_phase_v3()
used_keys = merged[["subject_id", "onset_sec"]].drop_duplicates()
anti_join = full_df.merge(used_keys, on=["subject_id", "onset_sec"], how="left", indicator=True)
held_out = anti_join[anti_join["_merge"] == "left_only"].drop(columns=["_merge"])
if len(full_df) - len(held_out) != len(used_keys):
    raise RuntimeError(
        f"Anti-join dropped {len(full_df) - len(held_out)} rows, expected exactly {len(used_keys)} -- "
        "(subject_id, onset_sec) may not be a unique key; investigate before trusting mu_resp_peak."
    )

subject_mean_angles = {}
for subj, sub in held_out.groupby("subject_id"):
    angle, r, n = circular_mean_resultant(sub["phi_resp_peak"].to_numpy())
    if np.isfinite(angle):
        subject_mean_angles[subj] = angle
mu_resp_peak, mu_R, mu_n_subjects = circular_mean_resultant(np.array(list(subject_mean_angles.values())))
print(f"Held-out mu_resp_peak = {mu_resp_peak:.4f} rad ({np.degrees(mu_resp_peak):.1f} deg), "
      f"R={mu_R:.4f} (n_subjects={mu_n_subjects}, from {len(held_out)} held-out events) "
      f"-- regression check vs. diary 243's 13_peak_phase_alignment_moderation.py")

merged["resp_peak_alignment"] = np.cos(merged["phi_resp_peak"] - mu_resp_peak)

# ─────────────────────────────────────────────────────────────────────────
# qe operationalizations
# ─────────────────────────────────────────────────────────────────────────
merged["qe_sigma_log"] = np.log1p(merged["sigma_power_z_n2"])
merged["qe_amplitude_log"] = np.log1p(merged["amplitude"])
merged["qe_sigma_raw"] = merged["sigma_power_z_n2"]
for c in ["qe_sigma_log", "qe_amplitude_log", "qe_sigma_raw"]:
    merged[f"{c}_z"] = (merged[c] - merged[c].mean()) / merged[c].std()

print("\nqe transform summary:")
for c in ["sigma_power_z_n2", "qe_sigma_log", "amplitude", "qe_amplitude_log"]:
    print(f"  {c}: mean={merged[c].mean():.3f}, skew={merged[c].skew():.3f}")

covariates = available_covariates(merged, NUISANCE_COVARIATES)


def run_interaction_family(qe_col: str, family_name: str) -> pd.DataFrame:
    rows = []
    for delta_mode in DELTA_MODES:
        for endpoint in GEOMETRY_COLS:
            ctrl_col = f"{endpoint}_control_median"
            far_col = f"{endpoint}_far"
            baseline_col = ctrl_col if delta_mode == "event_control" else far_col
            if endpoint not in merged.columns or baseline_col not in merged.columns:
                continue
            needed = [endpoint, baseline_col, "resp_peak_alignment", qe_col, "subject_id", *covariates]
            sub = merged.dropna(subset=[c for c in needed if c in merged.columns]).copy()
            row = {"family": family_name, "delta_mode": delta_mode, "endpoint": endpoint,
                   "n_events": len(sub), "n_subjects": sub["subject_id"].nunique() if len(sub) else 0}
            if len(sub) < 10 or row["n_subjects"] < 5:
                row["note"] = "insufficient N"
                rows.append(row)
                continue
            sub["delta"] = sub[endpoint] - sub[baseline_col]
            sub["_qe_c"] = sub[qe_col] - sub[qe_col].mean()
            sub["_align_c"] = sub["resp_peak_alignment"] - sub["resp_peak_alignment"].mean()
            sub["_interaction"] = sub["_align_c"] * sub["_qe_c"]

            centered_terms = []
            for c in covariates:
                cname = f"{c}_c"
                sub[cname] = sub[c] - sub[c].mean()
                centered_terms.append(cname)

            n_events_by_subj = sub.groupby("subject_id")["subject_id"].transform("size")
            sub["_weight"] = 1.0 / n_events_by_subj

            formula = ("delta ~ _align_c + _qe_c + _interaction"
                       + "".join(f" + {c}" for c in centered_terms))
            fit = fit_wls_cluster(formula, sub, weights_col="_weight", groups_col="subject_id")
            if fit is not None:
                row["align_main_coef"] = float(fit.params.get("_align_c", np.nan))
                row["align_main_p"] = float(fit.pvalues.get("_align_c", np.nan))
                row["qe_main_coef"] = float(fit.params.get("_qe_c", np.nan))
                row["qe_main_p"] = float(fit.pvalues.get("_qe_c", np.nan))
                row["interaction_coef"] = float(fit.params.get("_interaction", np.nan))
                row["interaction_se"] = float(fit.bse.get("_interaction", np.nan))
                row["interaction_p"] = float(fit.pvalues.get("_interaction", np.nan))
            else:
                row["align_main_coef"] = row["align_main_p"] = np.nan
                row["qe_main_coef"] = row["qe_main_p"] = np.nan
                row["interaction_coef"] = row["interaction_se"] = row["interaction_p"] = np.nan
            rows.append(row)
    df = pd.DataFrame(rows)
    if "interaction_p" in df.columns:
        df["interaction_p_fdr"] = bh_fdr(df["interaction_p"].fillna(1.0).to_numpy())
    return df


# ─────────────────────────────────────────────────────────────────────────
# Primary family: qe = log1p(sigma_power_z_n2)
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Primary family: delta ~ resp_peak_alignment * log1p(sigma_power_z_n2) + covariates ===")
primary_df = run_interaction_family("qe_sigma_log", "primary_sigma_log")
print(primary_df.to_string(index=False))
primary_df.to_csv(OUT / "qe_interaction_primary_sigma_log.csv", index=False)
n_sig = int((primary_df.get("interaction_p_fdr", pd.Series(dtype=float)) < 0.05).sum())
print(f"\nPrimary family result: {n_sig}/18 interaction tests BH-FDR-significant at interaction_p_fdr<0.05")

# ─────────────────────────────────────────────────────────────────────────
# Robustness: qe = amplitude (log1p), qe = raw sigma_power_z_n2
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Robustness: qe = log1p(amplitude) ===")
robust_amp_df = run_interaction_family("qe_amplitude_log", "robust_amplitude_log")
print(robust_amp_df[["delta_mode", "endpoint", "n_events", "interaction_coef", "interaction_p", "interaction_p_fdr"]]
      .to_string(index=False))
robust_amp_df.to_csv(OUT / "qe_interaction_robust_amplitude_log.csv", index=False)

print("\n=== Robustness: qe = raw (untransformed) sigma_power_z_n2 ===")
robust_raw_df = run_interaction_family("qe_sigma_raw", "robust_sigma_raw")
print(robust_raw_df[["delta_mode", "endpoint", "n_events", "interaction_coef", "interaction_p", "interaction_p_fdr"]]
      .to_string(index=False))
robust_raw_df.to_csv(OUT / "qe_interaction_robust_sigma_raw.csv", index=False)

# Cross-transform agreement check on which (delta_mode, endpoint) pairs are
# FDR-significant under each qe operationalization.
sig_primary = set(primary_df.loc[primary_df["interaction_p_fdr"] < 0.05, ["delta_mode", "endpoint"]].apply(tuple, axis=1))
sig_amp = set(robust_amp_df.loc[robust_amp_df["interaction_p_fdr"] < 0.05, ["delta_mode", "endpoint"]].apply(tuple, axis=1))
sig_raw = set(robust_raw_df.loc[robust_raw_df["interaction_p_fdr"] < 0.05, ["delta_mode", "endpoint"]].apply(tuple, axis=1))
print(f"\nFDR-significant (delta_mode, endpoint) pairs -- primary (sigma_log): {sorted(sig_primary)}")
print(f"FDR-significant (delta_mode, endpoint) pairs -- robust (amplitude_log): {sorted(sig_amp)}")
print(f"FDR-significant (delta_mode, endpoint) pairs -- robust (sigma_raw): {sorted(sig_raw)}")

# ─────────────────────────────────────────────────────────────────────────
# Secondary/exploratory: SO-coupled subset (N=25/15 subjects) -- descriptive
# only, explicitly non-confirmatory (no interaction model, no FDR family).
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Secondary/exploratory: SO-coupled subset (N=25 events / 15 subjects) -- descriptive only ===")
so_coupled = merged[merged["so_partner_missing"] == 0].copy()
print(f"  SO-coupled events: {len(so_coupled)}, subjects: {so_coupled['subject_id'].nunique()}")

descriptive_rows = []
for delta_mode in DELTA_MODES:
    for endpoint in GEOMETRY_COLS:
        ctrl_col = f"{endpoint}_control_median"
        far_col = f"{endpoint}_far"
        baseline_col = ctrl_col if delta_mode == "event_control" else far_col
        if endpoint not in so_coupled.columns or baseline_col not in so_coupled.columns:
            continue
        sub = so_coupled.dropna(subset=[endpoint, baseline_col, "so_spindle_coupling_score", "so_amplitude"]).copy()
        if len(sub) < 8:
            continue
        sub["delta"] = sub[endpoint] - sub[baseline_col]
        r_coupling = sub["delta"].corr(sub["so_spindle_coupling_score"])
        r_amplitude = sub["delta"].corr(sub["so_amplitude"])
        descriptive_rows.append({
            "delta_mode": delta_mode, "endpoint": endpoint, "n_events": len(sub),
            "n_subjects": sub["subject_id"].nunique(),
            "pearson_r_delta_vs_coupling_score": r_coupling,
            "pearson_r_delta_vs_so_amplitude": r_amplitude,
        })
descriptive_df = pd.DataFrame(descriptive_rows)
print(descriptive_df.to_string(index=False))
descriptive_df.to_csv(OUT / "so_coupled_descriptive_exploratory.csv", index=False)
print("\n  NOTE: descriptive correlations only, N=25/15 subjects -- not a confirmatory test, no FDR "
      "family, not part of the manuscript's primary claims. Reported for completeness/future hypothesis "
      "generation only (per the plan's explicit power caveat).")

print(f"\nOutputs in: {OUT}")
