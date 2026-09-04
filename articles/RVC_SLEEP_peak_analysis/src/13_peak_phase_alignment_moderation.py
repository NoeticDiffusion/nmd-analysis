"""
13_peak_phase_alignment_moderation.py -- Does spindle-peak respiratory-phase
*alignment* moderate the spindle-locked geometry response? (new analysis,
2026-07-10; RVC_SLEEP_peak_analysis follow-up article, Phase 2 of
.cursor/plans/rvc_sleep_peak_analysis_article_c1413bc0.plan.md).

Context: 11_richsleep_maalb_corrected.py + 12_richsleep_maalb_peak_phase_
deepdive.py established (diary 241/242) that spindle *peak* (not onset)
respiratory phase is a robust, subject-consistent, population-level
phase-locked quantity (duration-tercile-stable, split-half-replicated,
LOSO-robust across all 24 subjects) -- a *timing* result. Per
02_response.md's timing-vs-efficacy distinction (also flagged in
01_eap_wake_vs_sleep_and_rvc_formalization.md), timing alone does not
establish that the phase carries any functional/consequential role for the
denoising process EAP proposes. This script asks the natural next question:
does how close a given spindle's peak lands to the *population-preferred*
respiratory phase relate at all to the size of its geometry response?

Design (avoiding circularity):
  1. Estimate the population-preferred peak phase `mu_resp_peak` from the
     full ~23k-event raw catalog, EXCLUDING the 190 geometry-valid events
     used in the regression below (held out; the 190 are <1% of the
     catalog, so this costs almost no power on the phase-locking side).
     `mu_resp_peak` is the (subject-balanced) second-order circular mean:
     each of the 24 subjects' own held-out mean direction is computed
     first, then averaged on the circle -- consistent with this article's
     subject-fairness convention elsewhere (A1r, WLS-cluster weighting).
  2. For each of the 190 geometry-valid events, compute
     `resp_peak_alignment = cos(phi_resp_peak - mu_resp_peak)`: +1 when
     that event's peak lands exactly at the population-preferred phase,
     -1 when diametrically opposite.
  3. Primary family: WLS-cluster (Mal-C machinery, `fit_wls_cluster`) fit
     of `delta ~ resp_peak_alignment + covariates` per geometry endpoint (9)
     x delta mode (event_control, event_prefar) = 18 tests, BH-FDR jointly
     -- identical family size/design to the original Mal C, for direct
     comparability. Cardiac-peak is deliberately NOT included (already
     downgraded to fragile in diary 242); only the validated resp channel
     is tested here.
  4. Secondary/exploratory (reported, NOT folded into the primary FDR
     family): a free circular-regression sensitivity check,
     `delta ~ cos(phi_resp_peak) + sin(phi_resp_peak) + covariates`, whose
     implied "geometry-optimal" phase direction (atan2 of the two
     coefficients) is compared, honestly, against `mu_resp_peak` -- do the
     timing-preferred and (if any) geometry-preferred directions coincide,
     or are they decoupled?

This is exploratory, phase-2 work. No .typ file is touched by this script.

Run: python src/13_peak_phase_alignment_moderation.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from rvc_sleep_support import (
    ARTICLE_DIR,
    GEOMETRY_COLS,
    RESULTS_DIR,
    available_covariates,
    bh_fdr,
    circular_mean_resultant,
    fit_wls_cluster,
    make_results_subdir,
    sign_flip_permutation_test,
    subject_level_sensitivity,
    subject_level_slopes,
)

OUT = make_results_subdir("13_peak_phase_alignment_moderation")
PHASE_V2_DIR = ARTICLE_DIR / "RichSleep_resolved" / "phase_resolved_v2"

NUISANCE_COVARIATES = [
    "event_duration_sec", "window_center_sec",
    "ocular_stability_index", "sympathetic_index", "vagal_index",
    "eog_quality_quality", "ecg_quality_quality", "resp_quality_quality",
    "cardioresp_quality_quality", "anchor_support_fraction_quality",
]
DELTA_MODES = ["event_control", "event_prefar"]

# ─────────────────────────────────────────────────────────────────────────
# Load full raw catalog + the 190-event geometry-valid merged table
# ─────────────────────────────────────────────────────────────────────────
print("=== Loading full raw event_phase_v2 catalog (held-out mu_resp_peak estimation) ===")
phase_files = sorted(PHASE_V2_DIR.glob("*_event_phase_v2.parquet"))
if len(phase_files) != 24:
    raise RuntimeError(f"Expected 24 event_phase_v2 files, found {len(phase_files)} in {PHASE_V2_DIR}")

frames = []
for p in phase_files:
    d = pd.read_parquet(p)
    d["subject_id"] = f"sub-{p.stem.replace('_event_phase_v2', '')}"
    frames.append(d)
full_df = pd.concat(frames, ignore_index=True)
print(f"  full catalog: n_subjects={full_df['subject_id'].nunique()}, n_events={len(full_df)}")

merged_190_path = sorted(
    RESULTS_DIR.glob("rvc_sleep_*/10_richsleep_phase_resolved_eap/richsleep_event_phase_merged.parquet")
)
if not merged_190_path:
    raise RuntimeError(
        "richsleep_event_phase_merged.parquet not found - run 10_richsleep_phase_resolved_eap.py first."
    )
merged = pd.read_parquet(merged_190_path[-1])
print(f"  geometry-valid, N2-staged subsample: n_subjects={merged['subject_id'].nunique()}, n_events={len(merged)}")

# ─────────────────────────────────────────────────────────────────────────
# Held-out mu_resp_peak: exclude the 190 events by (subject_id, onset_sec)
# ─────────────────────────────────────────────────────────────────────────
used_keys = merged[["subject_id", "onset_sec"]].drop_duplicates()
anti_join = full_df.merge(used_keys, on=["subject_id", "onset_sec"], how="left", indicator=True)
held_out = anti_join[anti_join["_merge"] == "left_only"].drop(columns=["_merge"])
print(f"  held-out set (full catalog minus the 190 geometry-valid events): n_events={len(held_out)} "
      f"(dropped {len(full_df) - len(held_out)}, expected {len(used_keys)})")
if len(full_df) - len(held_out) != len(used_keys):
    raise RuntimeError(
        f"Anti-join dropped {len(full_df) - len(held_out)} rows, expected exactly {len(used_keys)} "
        "(one per geometry-valid event) -- (subject_id, onset_sec) may not be a unique key; investigate "
        "before trusting mu_resp_peak as truly held-out."
    )

subject_mean_angles = {}
for subj, sub in held_out.groupby("subject_id"):
    angle, r, n = circular_mean_resultant(sub["phi_resp_peak"].to_numpy())
    if np.isfinite(angle):
        subject_mean_angles[subj] = angle
mu_resp_peak, mu_R, mu_n_subjects = circular_mean_resultant(np.array(list(subject_mean_angles.values())))
print(f"\n=== Held-out population-preferred peak phase (subject-balanced, second-order mean) ===")
print(f"  mu_resp_peak = {mu_resp_peak:.4f} rad ({np.degrees(mu_resp_peak):.1f} deg), "
      f"R={mu_R:.4f} (n_subjects={mu_n_subjects}), from {len(held_out)} held-out events")
pd.DataFrame([{
    "mu_resp_peak_rad": mu_resp_peak, "mu_resp_peak_deg": float(np.degrees(mu_resp_peak)),
    "R_second_order": mu_R, "n_subjects": mu_n_subjects, "n_held_out_events": len(held_out),
    "n_excluded_geometry_valid_events": len(used_keys),
}]).to_csv(OUT / "held_out_mu_resp_peak.csv", index=False)

# ─────────────────────────────────────────────────────────────────────────
# resp_peak_alignment for the 190 geometry-valid events
# ─────────────────────────────────────────────────────────────────────────
merged = merged.copy()
merged["resp_peak_alignment"] = np.cos(merged["phi_resp_peak"] - mu_resp_peak)
print(f"\nresp_peak_alignment summary: mean={merged['resp_peak_alignment'].mean():.3f}, "
      f"std={merged['resp_peak_alignment'].std():.3f}, "
      f"range=[{merged['resp_peak_alignment'].min():.3f}, {merged['resp_peak_alignment'].max():.3f}]")

covariates = available_covariates(merged, NUISANCE_COVARIATES)
predictor = "resp_peak_alignment"

# ─────────────────────────────────────────────────────────────────────────
# Primary family: 9 endpoints x 2 delta modes = 18 tests, BH-FDR jointly
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Primary family: resp_peak_alignment moderation of the geometry delta ===")
rows = []
slope_rows = []
for delta_mode in DELTA_MODES:
    for endpoint in GEOMETRY_COLS:
        ctrl_col = f"{endpoint}_control_median"
        far_col = f"{endpoint}_far"
        baseline_col = ctrl_col if delta_mode == "event_control" else far_col
        if endpoint not in merged.columns or baseline_col not in merged.columns:
            continue
        needed = [endpoint, baseline_col, predictor, "subject_id", *covariates]
        sub = merged.dropna(subset=[c for c in needed if c in merged.columns]).copy()
        row = {"delta_mode": delta_mode, "predictor": predictor, "endpoint": endpoint,
               "n_events": len(sub), "n_subjects": sub["subject_id"].nunique() if len(sub) else 0}
        if len(sub) < 10 or row["n_subjects"] < 5:
            row["note"] = "insufficient N"
            rows.append(row)
            continue
        sub["delta"] = sub[endpoint] - sub[baseline_col]

        centered_terms = []
        for c in covariates:
            cname = f"{c}_c"
            sub[cname] = sub[c] - sub[c].mean()
            centered_terms.append(cname)

        n_events_by_subj = sub.groupby("subject_id")["subject_id"].transform("size")
        sub["_weight"] = 1.0 / n_events_by_subj

        formula = f"delta ~ {predictor}" + "".join(f" + {c}" for c in centered_terms)
        fit = fit_wls_cluster(formula, sub, weights_col="_weight", groups_col="subject_id")
        if fit is not None:
            row["alignment_coef"] = float(fit.params.get(predictor, np.nan))
            row["alignment_se"] = float(fit.bse.get(predictor, np.nan))
            row["alignment_p"] = float(fit.pvalues.get(predictor, np.nan))
        else:
            row["alignment_coef"] = row["alignment_se"] = row["alignment_p"] = np.nan

        slopes = subject_level_slopes(
            sub[predictor].to_numpy(), sub["delta"].to_numpy(), sub["subject_id"].to_numpy(), min_events=3,
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
                slope_rows.append({"delta_mode": delta_mode, "predictor": predictor,
                                    "endpoint": endpoint, "subject_id": subj, "slope": b})
        else:
            row["slope_mean"] = row["slope_ttest_p"] = row["slope_wilcoxon_p"] = row["slope_perm_p"] = np.nan

        rows.append(row)

primary_df = pd.DataFrame(rows)
if "alignment_p" in primary_df.columns:
    primary_df["alignment_p_fdr"] = bh_fdr(primary_df["alignment_p"].to_numpy())
print(primary_df.to_string(index=False))
primary_df.to_csv(OUT / "resp_peak_alignment_moderation.csv", index=False)
pd.DataFrame(slope_rows).to_csv(OUT / "resp_peak_alignment_moderation_subject_slopes.csv", index=False)

n_fdr_sig = int((primary_df.get("alignment_p_fdr", pd.Series(dtype=float)) < 0.05).sum())
print(f"\nPrimary family result: {n_fdr_sig}/18 tests BH-FDR-significant at alignment_p_fdr<0.05")

# ─────────────────────────────────────────────────────────────────────────
# Secondary/exploratory: free circular-regression sensitivity check
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Secondary/exploratory: free circular-regression check (delta ~ cos+sin(phi_resp_peak)) ===")
circ_rows = []
for delta_mode in DELTA_MODES:
    for endpoint in GEOMETRY_COLS:
        ctrl_col = f"{endpoint}_control_median"
        far_col = f"{endpoint}_far"
        baseline_col = ctrl_col if delta_mode == "event_control" else far_col
        if endpoint not in merged.columns or baseline_col not in merged.columns:
            continue
        needed = [endpoint, baseline_col, "phi_resp_peak", "subject_id", *covariates]
        sub = merged.dropna(subset=[c for c in needed if c in merged.columns]).copy()
        row = {"delta_mode": delta_mode, "endpoint": endpoint, "n_events": len(sub),
               "n_subjects": sub["subject_id"].nunique() if len(sub) else 0}
        if len(sub) < 10 or row["n_subjects"] < 5:
            row["note"] = "insufficient N"
            circ_rows.append(row)
            continue
        sub["delta"] = sub[endpoint] - sub[baseline_col]
        sub["cos_phi"] = np.cos(sub["phi_resp_peak"])
        sub["sin_phi"] = np.sin(sub["phi_resp_peak"])

        centered_terms = []
        for c in covariates:
            cname = f"{c}_c"
            sub[cname] = sub[c] - sub[c].mean()
            centered_terms.append(cname)

        n_events_by_subj = sub.groupby("subject_id")["subject_id"].transform("size")
        sub["_weight"] = 1.0 / n_events_by_subj

        formula = "delta ~ cos_phi + sin_phi" + "".join(f" + {c}" for c in centered_terms)
        fit = fit_wls_cluster(formula, sub, weights_col="_weight", groups_col="subject_id")
        if fit is None:
            row["cos_coef"] = row["sin_coef"] = row["joint_wald_p"] = np.nan
            row["geometry_optimal_phase_rad"] = row["geometry_optimal_phase_deg"] = np.nan
            row["angular_distance_to_mu_deg"] = np.nan
            circ_rows.append(row)
            continue

        cos_coef = float(fit.params.get("cos_phi", np.nan))
        sin_coef = float(fit.params.get("sin_phi", np.nan))
        row["cos_coef"] = cos_coef
        row["sin_coef"] = sin_coef
        row["cos_p"] = float(fit.pvalues.get("cos_phi", np.nan))
        row["sin_p"] = float(fit.pvalues.get("sin_phi", np.nan))
        try:
            wald = fit.wald_test("cos_phi = 0, sin_phi = 0", scalar=True)
            row["joint_wald_p"] = float(wald.pvalue)
        except Exception:
            row["joint_wald_p"] = np.nan

        if np.isfinite(cos_coef) and np.isfinite(sin_coef):
            geom_phase = float(np.arctan2(sin_coef, cos_coef))
            row["geometry_optimal_phase_rad"] = geom_phase
            row["geometry_optimal_phase_deg"] = float(np.degrees(geom_phase))
            ang_dist = float(np.degrees(np.abs(np.arctan2(
                np.sin(geom_phase - mu_resp_peak), np.cos(geom_phase - mu_resp_peak)
            ))))
            row["angular_distance_to_mu_deg"] = ang_dist
        else:
            row["geometry_optimal_phase_rad"] = row["geometry_optimal_phase_deg"] = np.nan
            row["angular_distance_to_mu_deg"] = np.nan

        circ_rows.append(row)

circ_df = pd.DataFrame(circ_rows)
print(circ_df.to_string(index=False))
circ_df.to_csv(OUT / "resp_peak_circular_regression_secondary.csv", index=False)

print("\n=== Peak-phase alignment moderation analysis complete ===")
print(f"All outputs in: {OUT}")
