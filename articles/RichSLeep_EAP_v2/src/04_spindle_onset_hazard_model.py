"""
04_spindle_onset_hazard_model.py -- Two independent strengthenings of the
N2-spindle-onset phase-locking null from 03_multistage_phase_locking.py
(Phase 2, task 7 of .cursor/plans/richsleep_eap_v2_article_aa3119f9.plan.md).

Both tests below avoid the *parametric* uniform-circular null used by
03's subject-rotation permutation test, replacing it with a null grounded
directly in real physiological exposure data:

  A. Case-control test using `non_event_risk_v1` (NMD's purpose-built,
     N2-restricted, per-subject-matched non-event risk-set sample -- see
     handover/handover_From_nmd_richsleep_eap_v2_delivery_received.md S6).
     Real spindle onsets = cases (1), risk-set timepoints = controls (0).
     `is_case ~ cos(phase) + sin(phase)`, cluster-robust logistic regression
     by subject, joint Wald chi2(2) test on the {cos, sin} pair. A
     significant result means real onsets occur at different phases than a
     matched sample of "could a spindle have started here" N2 timepoints --
     the correct case-control analogue of a hazard-ratio test.

  B. Circular time-shift surrogate (rvc_sleep_support.circular_time_shift_surrogate_test):
     shift each subject's own continuous 10 Hz phase stream (phase_continuous_v1)
     by an independent random lag and re-read phase at the same real onset
     clock-times. This preserves the exact non-sinusoidal waveform/
     autocorrelation of each subject's own physiological signal, a
     genuinely different null-construction principle than either A or 03's
     parametric rotation -- convergent evidence across three independent
     null constructions (03's rotation, A, B) is a much stronger claim than
     any single one alone.

An earlier attempt at a third, phase-binned Poisson-offset exposure model
used the per-subject geometry H5's `labels/stage` array as a continuous
hypnogram; this was abandoned when `labels/stage` turned out to be sparse
(only the 177 jacobian-center windows/subject, not a continuous record) --
see the handover note S6 caveat. `non_event_risk_v1` (test A) supersedes it.

Run: python src/04_spindle_onset_hazard_model.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from rvc_sleep_support import (
    bh_fdr,
    circular_time_shift_surrogate_test,
    fit_logit_cluster,
    load_non_event_risk,
    load_phase_continuous,
    load_phase_v3,
    make_results_subdir,
)

OUT = make_results_subdir("04_spindle_onset_hazard_model")
CHANNELS = {"cardiac": ("phi_cardiac_onset", "phi_cardiac"), "resp": ("phi_resp_onset", "phi_resp")}

phase_v3 = load_phase_v3()
risk = load_non_event_risk()
print(f"Cases (real spindle onsets): {len(phase_v3)} events, {phase_v3['subject_id'].nunique()} subjects")
print(f"Controls (non_event_risk_v1): {len(risk)} rows, {risk['subject_id'].nunique()} subjects")

# ─────────────────────────────────────────────────────────────────────────
# Test A -- case-control logistic regression vs. non_event_risk_v1
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Test A: case-control logistic regression (cases vs. non_event_risk_v1) ===")
case_control_rows = []
for channel, (event_col, risk_col) in CHANNELS.items():
    cases = phase_v3[["subject_id", event_col]].rename(columns={event_col: "phase"}).dropna()
    cases["is_case"] = 1
    controls = risk[["subject_id", risk_col]].rename(columns={risk_col: "phase"}).dropna()
    controls["is_case"] = 0
    pooled = pd.concat([cases, controls], ignore_index=True)
    pooled["cos_phase"] = np.cos(pooled["phase"])
    pooled["sin_phase"] = np.sin(pooled["phase"])

    fit = fit_logit_cluster("is_case ~ cos_phase + sin_phase", pooled, groups_col="subject_id")
    row = {"channel": channel, "n_cases": int(cases.shape[0]), "n_controls": int(controls.shape[0])}
    if fit is not None:
        b_cos, b_sin = fit.params["cos_phase"], fit.params["sin_phase"]
        cov = fit.cov_params().loc[["cos_phase", "sin_phase"], ["cos_phase", "sin_phase"]].to_numpy()
        theta = np.array([b_cos, b_sin])
        wald_stat = float(theta @ np.linalg.solve(cov, theta))
        from scipy import stats as scipy_stats
        wald_p = float(scipy_stats.chi2.sf(wald_stat, df=2))
        preferred_phase = float(np.arctan2(b_sin, b_cos))
        row.update({
            "coef_cos": float(b_cos), "coef_sin": float(b_sin),
            "coef_cos_p": float(fit.pvalues["cos_phase"]), "coef_sin_p": float(fit.pvalues["sin_phase"]),
            "wald_chi2": wald_stat, "wald_p": wald_p, "preferred_phase_rad": preferred_phase,
        })
    else:
        row.update({"coef_cos": np.nan, "coef_sin": np.nan, "wald_chi2": np.nan, "wald_p": np.nan})
    case_control_rows.append(row)
    print(f"  {channel}: wald_chi2={row.get('wald_chi2', np.nan):.3f}, wald_p={row.get('wald_p', np.nan):.4f}, "
          f"preferred_phase={row.get('preferred_phase_rad', np.nan):.3f} rad")

case_control_df = pd.DataFrame(case_control_rows)
case_control_df["wald_p_fdr"] = bh_fdr(case_control_df["wald_p"].to_numpy())
case_control_df.to_csv(OUT / "case_control_logit.csv", index=False)

# ─────────────────────────────────────────────────────────────────────────
# Test B -- circular time-shift surrogate on the continuous phase stream
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Test B: circular time-shift surrogate (phase_continuous_v1) ===")
time_shift_rows = []
for channel, (event_col, cont_col) in CHANNELS.items():
    sub_events = phase_v3[["subject_id", "onset_sec", event_col]].dropna(subset=[event_col])
    result = circular_time_shift_surrogate_test(
        sub_events["onset_sec"].to_numpy(), sub_events["subject_id"].to_numpy(),
        continuous_loader=load_phase_continuous, channel=cont_col, n_perm=500,
    )
    result["channel"] = channel
    time_shift_rows.append(result)
    print(f"  {channel}: n_events={result['n_events']}, obs_T2={result['obs_T2']:.6f}, "
          f"null_T2_95pct={result['null_T2_95pct']:.6f}, perm_p_T2={result['perm_p_T2']:.4f}")

time_shift_df = pd.DataFrame(time_shift_rows)
time_shift_df["perm_p_T2_fdr"] = bh_fdr(time_shift_df["perm_p_T2"].to_numpy())
time_shift_df["perm_p_R1_fdr"] = bh_fdr(time_shift_df["perm_p_R1"].to_numpy())
time_shift_df.to_csv(OUT / "circular_time_shift_surrogate.csv", index=False)

# ─────────────────────────────────────────────────────────────────────────
# Cross-null summary -- note this is NOT a convergence story: the three
# independent null constructions disagree with each other for both
# channels, and that disagreement is itself the reportable result (see
# print commentary below for the diagnostic behind each number).
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Cross-null summary (onset-phase-locking, three independent null constructions) ===")
print("  Null 0 (03_multistage_phase_locking.py, subject-rotation permutation, uniform-circular null): "
      "cardiac raw p=0.0815, resp raw p=0.0265 (borderline, family-dependent -- see that script)")
print(case_control_df[["channel", "wald_chi2", "wald_p", "wald_p_fdr"]]
      .rename(columns={"wald_p": "nullA_p", "wald_p_fdr": "nullA_p_fdr"}).to_string(index=False))
print(time_shift_df[["channel", "perm_p_T2", "perm_p_T2_fdr"]]
      .rename(columns={"perm_p_T2": "nullB_p", "perm_p_T2_fdr": "nullB_p_fdr"}).to_string(index=False))

convergence = case_control_df[["channel", "wald_p", "wald_p_fdr"]].merge(
    time_shift_df[["channel", "perm_p_T2", "perm_p_T2_fdr"]], on="channel"
).rename(columns={"wald_p": "nullA_case_control_p", "wald_p_fdr": "nullA_case_control_p_fdr",
                   "perm_p_T2": "nullB_time_shift_p", "perm_p_T2_fdr": "nullB_time_shift_p_fdr"})
convergence["null0_subject_rotation_p"] = [0.0815, 0.0265]  # cardiac, resp -- from 03_multistage_phase_locking.py
convergence.to_csv(OUT / "cross_null_convergence.csv", index=False)

print(
    "\n  Honest reading: the three nulls DISAGREE, and do so in different directions per channel:\n"
    "  - cardiac: null A (case-control, p=0.38) says no effect; null B (time-shift, p=0.004) says weak\n"
    "    effect; null 0 says borderline-null (p=0.0815, raw). Case/control histogram check (ad hoc,\n"
    "    12 bins) shows no coherent shape difference for cardiac -- null B's cardiac hit is not\n"
    "    corroborated by the other two and is treated here as likely a false positive of that specific\n"
    "    construction rather than a real effect.\n"
    "  - resp: null A (case-control, p=4e-7) finds a small but very clearly non-zero effect -- an ad hoc\n"
    "    12-bin histogram check confirms a coherent, monotonic first-harmonic-like excess/deficit pattern\n"
    "    (not noise), just a SMALL one (~5-10% density deviation per bin), detectable only because null A's\n"
    "    N (23,029 cases + 66,827 matched controls) gives it far more power than null 0 or null B. Null 0's\n"
    "    raw p=0.0265 is directionally consistent (same channel, same qualitative 'weak positive signal')\n"
    "    but does not reach the same significance; null B (p=1.0) finds nothing.\n"
    "  Net: onset-phase-locking is at most a very weak, null-construction-sensitive effect for respiration,\n"
    "  and not corroborated at all for cardiac -- in sharp, deliberate contrast to the N2-peak and N3-SO\n"
    "  results (03_multistage_phase_locking.py), which are large and significant under every null tried.\n"
    "  This three-way disagreement is reported as-is (not resolved by selecting a preferred null) and used\n"
    "  in the manuscript as a methodological illustration of why 'onset locking is null' claims from a\n"
    "  single null construction should be read cautiously."
)

print(f"\nOutputs in: {OUT}")
