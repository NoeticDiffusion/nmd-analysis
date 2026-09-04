"""
10_richsleep_phase_resolved_eap.py — Phase-resolved EAP fairness test on
RichSleep (diary 233/234/235; "Test 1", Mål B + Mål C).

Context: the long-window Pass C / R6 EAP-moderation test (09_richsleep_
verification.py) tests whether a *tonic* pre-event physiological state
(a ~2-4 min pre_far average) predicts the size of the spindle-locked
geometry response. That is a coarse proxy for the actual mechanism NDT's
Embodied Anchoring Principle (EAP, @eq:rvc in NoeticDiffusionTheory.typ)
proposes: phase-resolved cardiorespiratory entrainment of the denoising
process, not a slow tonic-state moderation. This script runs two more
direct, phase-resolved tests instead, using NMD's `event_phase_v2` export
(24/24 subjects, onset-catalog-verified against the corrected
`neuralmanifolddynamics_RichSleep_20260708_135627` event-locked run - see
diary 235 for the full verification):

  Mål B — Spindle-onset phase-locking ("self-prior / boundary condition"):
    do spindle onsets preferentially occur at a particular phase of the
    cardiac and/or respiratory cycle, rather than being phase-uniform?
    Rayleigh test per subject (within-subject entrainment), plus a
    second-order Rayleigh test on the 24 subject-level mean directions
    (population-level common preferred phase).

  Mål C — HEP-amplitude moderation: does pre-event heartbeat-evoked-
    potential (HEP) amplitude - a more direct interoceptive-precision
    proxy than the tonic `cardioresp_anchor_index` composite - moderate
    the spindle-locked geometry response? Same Pass-C-style WLS-cluster +
    subject-level-slope-permutation machinery as 09_richsleep_verification.py,
    with `hep_amplitude_pre_far` as the sole anchor.

Mål A (phase-resolved manifold variance) is infeasible on this export
(coords_9d resolution = 1 value / 30 s epoch; confirmed in
phase_resolved_v1/run_meta.json, diary 233) and is not attempted here.
Mål D (ANPHY/BOAS partial replication) was not requested for this pass -
RichSleep is the only dataset with a phase-resolved export.

This is exploratory, phase-2 work, NOT yet part of the manuscript's frozen
claims (R1-R6). Results are reported here for review before any manuscript
integration decision.

Run: python src/10_richsleep_phase_resolved_eap.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from rvc_sleep_support import (
    ARTICLE_DIR,
    DATASET_RICHSLEEP,
    GEOMETRY_COLS,
    RESULTS_DIR,
    SURFACE_PRIMARY,
    available_covariates,
    bh_fdr,
    circular_mean_resultant,
    fit_wls_cluster,
    make_results_subdir,
    rayleigh_test,
    sign_flip_permutation_test,
    subject_level_sensitivity,
    subject_level_slopes,
)

OUT = make_results_subdir("10_richsleep_phase_resolved_eap")
PHASE_V2_DIR = ARTICLE_DIR / "RichSleep_resolved" / "phase_resolved_v2"

NUISANCE_COVARIATES = [
    "event_duration_sec", "window_center_sec",
    "ocular_stability_index", "sympathetic_index", "vagal_index",
    "eog_quality_quality", "ecg_quality_quality", "resp_quality_quality",
    "cardioresp_quality_quality", "anchor_support_fraction_quality",
]

# ─────────────────────────────────────────────────────────────────────────
# Load and verify event_phase_v2, join against the corrected event-locked
# geometry table (built by 09_richsleep_verification.py - must be run first)
# ─────────────────────────────────────────────────────────────────────────
print("=== Loading event_phase_v2 (24 subjects) ===")
phase_files = sorted(PHASE_V2_DIR.glob("*_event_phase_v2.parquet"))
if len(phase_files) != 24:
    raise RuntimeError(f"Expected 24 event_phase_v2 files, found {len(phase_files)} in {PHASE_V2_DIR}")

phase_frames = []
for p in phase_files:
    df = pd.read_parquet(p)
    subj_short = p.stem.replace("_event_phase_v2", "")
    df["subject_id"] = f"sub-{subj_short}"
    phase_frames.append(df)
phase_df = pd.concat(phase_frames, ignore_index=True)
print(f"  n_subjects: {phase_df['subject_id'].nunique()}, n_events: {len(phase_df)}")

event_level_path = latest = sorted(
    RESULTS_DIR.glob("rvc_sleep_*/09_richsleep_verification/event_level_richsleep.parquet")
)
if not event_level_path:
    raise RuntimeError(
        "event_level_richsleep.parquet not found - run 09_richsleep_verification.py first "
        "(against the corrected neuralmanifolddynamics_RichSleep_20260708_135627 ingest)."
    )
event_level_path = event_level_path[-1]
print(f"  event_level source: {event_level_path}")
event_level = pd.read_parquet(event_level_path)
event_rows = event_level[event_level["bin_label"] == "event"].copy()

# pre_far endpoint means, needed for the event_prefar delta mode (mirrors
# 09_richsleep_verification.py's far_geom_frame construction) - event_level
# already carries all bin_labels, not just "event".
far_geom = {}
for endpoint in GEOMETRY_COLS:
    if endpoint not in event_level.columns:
        continue
    far_geom[endpoint] = (
        event_level[event_level["bin_label"] == "pre_far"]
        .groupby(["dataset_id", "subject_id", "event_id"])[endpoint].mean()
        .rename(f"{endpoint}_far")
    )
far_geom_frame = pd.concat(far_geom.values(), axis=1).reset_index() if far_geom else pd.DataFrame()
if not far_geom_frame.empty:
    event_rows = event_rows.merge(far_geom_frame, on=["dataset_id", "subject_id", "event_id"], how="left")

# Onset-catalog verification (must be exact - re-checks diary 235's 24/24 result
# inline so this script fails loudly if it is ever re-run against stale data)
merge_check = event_rows.merge(
    phase_df[["subject_id", "onset_sec"]],
    left_on=["subject_id", "event_onset_sec"], right_on=["subject_id", "onset_sec"],
    how="left", indicator=True,
)
match_rate = (merge_check["_merge"] == "both").mean()
print(f"  onset-catalog match rate (event_level vs event_phase_v2): {match_rate:.4f}")
if match_rate < 0.99:
    raise RuntimeError(
        f"event_level and event_phase_v2 onset catalogs do not match (match_rate={match_rate:.4f}). "
        "Do not proceed - re-verify run roots before trusting any join (see diary 233/234)."
    )

merged = event_rows.merge(
    phase_df, left_on=["subject_id", "event_onset_sec"], right_on=["subject_id", "onset_sec"],
    how="inner", suffixes=("", "_phase"),
)
print(f"  merged event-level x phase-resolved table: {merged.shape}")
merged.to_parquet(OUT / "richsleep_event_phase_merged.parquet", index=False)

# ─────────────────────────────────────────────────────────────────────────
# Mål B — spindle-onset phase-locking (self-prior / boundary condition)
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Mal B: spindle-onset cardiac/respiratory phase-locking ===")
b_rows = []
subject_means = {"phi_cardiac_onset": {}, "phi_resp_onset": {}}
for channel in ["phi_cardiac_onset", "phi_resp_onset"]:
    for subj, sub in merged.groupby("subject_id"):
        phases = sub[channel].dropna().to_numpy()
        r, p, n = rayleigh_test(phases)
        angle, _, _ = circular_mean_resultant(phases)
        b_rows.append({
            "channel": channel, "subject_id": subj, "n_events": n,
            "mean_angle_rad": angle, "R": r, "rayleigh_p": p,
        })
        if np.isfinite(angle):
            subject_means[channel][subj] = angle

b_df = pd.DataFrame(b_rows)
b_df["rayleigh_p_fdr"] = np.nan
for channel, idx in b_df.groupby("channel").groups.items():
    mask = b_df.index.isin(idx)
    b_df.loc[mask, "rayleigh_p_fdr"] = bh_fdr(b_df.loc[mask, "rayleigh_p"].values)
b_df.to_csv(OUT / "molB_within_subject_phase_locking.csv", index=False)

print("Within-subject Rayleigh test summary (n subjects with FDR-significant "
      "onset-phase concentration, out of 24):")
for channel in ["phi_cardiac_onset", "phi_resp_onset"]:
    sub = b_df[b_df["channel"] == channel]
    n_sig = int((sub["rayleigh_p_fdr"] < 0.05).sum())
    print(f"  {channel}: {n_sig}/24 subjects FDR-significant (median R={sub['R'].median():.3f})")

print("\nSecond-order (population-level) Rayleigh test on subject mean-direction angles:")
b2_rows = []
for channel, means in subject_means.items():
    angles = np.array(list(means.values()))
    r, p, n = rayleigh_test(angles)
    mean_angle, _, _ = circular_mean_resultant(angles)
    b2_rows.append({
        "channel": channel, "n_subjects": n, "mean_of_subject_means_rad": mean_angle,
        "R_second_order": r, "rayleigh_p_second_order": p,
    })
    print(f"  {channel}: n_subjects={n}, R={r:.3f}, p={p:.4f}, "
          f"common mean angle={mean_angle:.3f} rad")
b2_df = pd.DataFrame(b2_rows)
b2_df["rayleigh_p_second_order_fdr"] = bh_fdr(b2_df["rayleigh_p_second_order"].values)
b2_df.to_csv(OUT / "molB_second_order_population_phase.csv", index=False)

# ─────────────────────────────────────────────────────────────────────────
# Mål C — HEP-amplitude moderation of the spindle-locked geometry response
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Mal C: HEP-amplitude moderation ===")
covariates = available_covariates(merged, NUISANCE_COVARIATES)
anchor_col = "hep_amplitude_pre_far"

c_rows = []
slope_rows = []
DELTA_MODES = ["event_control", "event_prefar"]
for delta_mode in DELTA_MODES:
    for endpoint in GEOMETRY_COLS:
        ctrl_col = f"{endpoint}_control_median"
        far_col = f"{endpoint}_far"
        baseline_col = ctrl_col if delta_mode == "event_control" else far_col
        if endpoint not in merged.columns or baseline_col not in merged.columns or anchor_col not in merged.columns:
            continue
        needed = [endpoint, baseline_col, anchor_col, "subject_id", *covariates]
        sub = merged.dropna(subset=[c for c in needed if c in merged.columns]).copy()
        row = {"delta_mode": delta_mode, "anchor_col": anchor_col, "endpoint": endpoint,
               "n_events": len(sub), "n_subjects": sub["subject_id"].nunique() if len(sub) else 0}
        if len(sub) < 10 or row["n_subjects"] < 5:
            row["note"] = "insufficient N"
            c_rows.append(row)
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
                                    "endpoint": endpoint, "subject_id": subj, "slope": b})
        else:
            row["slope_mean"] = row["slope_ttest_p"] = row["slope_wilcoxon_p"] = row["slope_perm_p"] = np.nan

        c_rows.append(row)

c_df = pd.DataFrame(c_rows)
if "anchor_p" in c_df.columns:
    c_df["anchor_p_fdr"] = np.nan
    for delta_mode, idx in c_df.groupby("delta_mode").groups.items():
        mask = c_df.index.isin(idx)
        c_df.loc[mask, "anchor_p_fdr"] = bh_fdr(c_df.loc[mask, "anchor_p"].values)
print(c_df.to_string(index=False))
c_df.to_csv(OUT / "molC_hep_moderation.csv", index=False)
pd.DataFrame(slope_rows).to_csv(OUT / "molC_hep_moderation_subject_slopes.csv", index=False)

print("\n=== Phase-resolved EAP test (Mal B + Mal C) complete ===")
print(f"All outputs in: {OUT}")
