"""
11_richsleep_maalb_corrected.py -- Corrected population-level Mal B
reanalysis (follow-up, 2026-07-10; see
articles/Rythmic_Variance_Control_in_Sleep_theory/plan/02_response.md, S7).

Context: 10_richsleep_phase_resolved_eap.py's Mal B tested (a) per-subject
Rayleigh (within-subject entrainment) and (b) a second-order Rayleigh on the
24 subject-level mean directions -- both null, on N=190 events (the
geometry-valid, N2-staged subsample that Mal C's HEP-moderation test also
needs). An external LLM reviewer (02_response.md, S7) correctly flagged that
the *proposed* next step in 01_eap_wake_vs_sleep_and_rvc_formalization.md
(S7, item 1) -- pooling all events and permuting *subject labels* -- does
not construct a valid null: shuffling which subject a fixed set of pooled
angles is attributed to leaves the pooled angle multiset, and hence any
pooled circular-uniformity statistic, exactly invariant. That proposed
correction was itself wrong and is retracted here in favour of the
alternatives 02_response.md actually proposes.

This script:
  1. Uses NMD's *full* raw event_phase_v2 catalog (23,029 spindle-onset
     events across the same 24 RichSleep subjects), not just the 190-event
     geometry-valid subsample -- Mal B (pure phase-locking) does not need
     the geometry join at all, so restricting it to the geometry-valid
     subsample was an unforced, avoidable power loss.
  2. Replaces the flawed subject-label-shuffle null with a subject-specific
     random-phase-rotation surrogate (02_response.md S7, option 3): each
     permutation draws one iid Uniform(0, 2*pi) rotation per subject and
     adds it to *all* of that subject's phases. This destroys any common
     population-level preferred phase / axial alignment while exactly
     preserving each subject's event count, within-subject clustering, and
     the observed unequal per-subject sampling -- giving a pseudo-
     replication-safe Monte Carlo p-value with no asymptotic-formula
     dependence.
  3. Adds a subject-cluster bootstrap (02_response.md S7, option 2) to
     characterise estimation stability (a CI), kept conceptually separate
     from the hypothesis test itself.
  4. Adds a simple first+second-harmonic omnibus statistic T2 = R1^2 + R2^2
     (R2 = |mean(exp(2i*phase))|) as an honestly-labelled analogue of
     Hermans-Rasson's robustness-to-multimodality/axial-alternative
     motivation -- NOT a re-implementation of the literature Hermans-Rasson
     statistic itself (to avoid risking a subtly wrong formula). Because
     every p-value here is a Monte Carlo permutation p-value rather than an
     asymptotic one, any well-defined statistic is valid; T2 is chosen for
     transparency and ease of independent verification.

Primary family (BH-FDR applied jointly across these 4 tests):
    {phi_cardiac_onset, phi_resp_onset} x {full catalog, quality-filtered
    (cardiac_phase_quality >= 0.7) subset}.

Secondary / exploratory (reported, NOT in the FDR family):
  - the same machinery on phi_*_peak (spindle peak, not onset) -- checks
    02_response.md's point that coupling need not be strongest at a
    zero-lag onset reference;
  - the same machinery re-applied to the original 190-event geometry-valid,
    N2-staged subsample, for direct comparability with the R6b numbers
    already reported in the manuscript and in 01_eap_wake_vs_sleep_and_rvc_
    formalization.md's side-by-side table;
  - a categorical cross-check: subject-level proportion of onsets during
    inspiration (inhale_at_onset) vs. the 0.5 null, aggregated at the
    subject level first (pseudo-replication-safe by construction);
  - retained for context: per-subject Rayleigh + BH-FDR across subjects,
    and the second-order Rayleigh on the 24 subject-level mean directions
    (both already pseudo-replication-safe by construction; unaffected by
    the critique above).

This is exploratory follow-up work, NOT part of the manuscript's frozen
claims (R1-R6/R6b). No .typ file is touched by this script.

Run: python src/11_richsleep_maalb_corrected.py
"""
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from rvc_sleep_support import (
    ARTICLE_DIR,
    RESULTS_DIR,
    bh_fdr,
    binary_subject_level_test,
    circular_mean_resultant,
    harmonic_stats,
    make_results_subdir,
    rayleigh_test,
    subject_cluster_bootstrap_ci,
    subject_rotation_permutation_test,
)

OUT = make_results_subdir("11_richsleep_maalb_corrected")
PHASE_V2_DIR = ARTICLE_DIR / "RichSleep_resolved" / "phase_resolved_v2"
QUALITY_THRESHOLD = 0.7
N_PERM = 2000
N_BOOT = 2000

PHASE_CHANNELS_PRIMARY = ["phi_cardiac_onset", "phi_resp_onset"]
PHASE_CHANNELS_SECONDARY = ["phi_cardiac_peak", "phi_resp_peak"]


def run_channel(sample_name: str, channel: str, df: pd.DataFrame) -> Dict[str, object]:
    phases = df[channel].to_numpy()
    subjects = df["subject_id"].to_numpy()
    row: Dict[str, object] = {"sample": sample_name, "channel": channel}

    naive_r1, naive_r2, naive_t2 = harmonic_stats(phases)
    row["naive_pooled_R1"], row["naive_pooled_R2"], row["naive_pooled_T2"] = naive_r1, naive_r2, naive_t2

    perm = subject_rotation_permutation_test(phases, subjects)
    for k, v in perm.items():
        row[f"perm_{k}"] = v

    boot = subject_cluster_bootstrap_ci(phases, subjects)
    row.update(boot)

    return row


def per_subject_and_second_order(sample_name: str, channel: str, df: pd.DataFrame,
                                  subj_rows: list, second_order_rows: list) -> None:
    subject_means = {}
    for subj, sub in df.groupby("subject_id"):
        phases = sub[channel].dropna().to_numpy()
        r, p, n = rayleigh_test(phases)
        angle, _, _ = circular_mean_resultant(phases)
        subj_rows.append({
            "sample": sample_name, "channel": channel, "subject_id": subj,
            "n_events": n, "mean_angle_rad": angle, "R": r, "rayleigh_p": p,
        })
        if np.isfinite(angle):
            subject_means[subj] = angle

    angles = np.array(list(subject_means.values()))
    r, p, n = rayleigh_test(angles)
    mean_angle, _, _ = circular_mean_resultant(angles)
    second_order_rows.append({
        "sample": sample_name, "channel": channel, "n_subjects": n,
        "mean_of_subject_means_rad": mean_angle, "R_second_order": r,
        "rayleigh_p_second_order": p,
    })


# ─────────────────────────────────────────────────────────────────────────
# Load full raw event_phase_v2 catalog (24 subjects, no geometry join)
# ─────────────────────────────────────────────────────────────────────────
print("=== Loading full raw event_phase_v2 catalog (24 subjects, no geometry join) ===")
phase_files = sorted(PHASE_V2_DIR.glob("*_event_phase_v2.parquet"))
if len(phase_files) != 24:
    raise RuntimeError(f"Expected 24 event_phase_v2 files, found {len(phase_files)} in {PHASE_V2_DIR}")

frames = []
for p in phase_files:
    d = pd.read_parquet(p)
    subj_short = p.stem.replace("_event_phase_v2", "")
    d["subject_id"] = f"sub-{subj_short}"
    frames.append(d)
full_df = pd.concat(frames, ignore_index=True)
print(f"  full catalog: n_subjects={full_df['subject_id'].nunique()}, n_events={len(full_df)}")

quality_df = full_df[
    (full_df["cardiac_phase_quality"] >= QUALITY_THRESHOLD) & (full_df["resp_phase_quality"] >= 1.0)
].copy()
print(f"  quality-filtered (cardiac_phase_quality>={QUALITY_THRESHOLD}): "
      f"n_subjects={quality_df['subject_id'].nunique()}, n_events={len(quality_df)}")

merged_190_path = sorted(
    RESULTS_DIR.glob("rvc_sleep_*/10_richsleep_phase_resolved_eap/richsleep_event_phase_merged.parquet")
)
if not merged_190_path:
    raise RuntimeError(
        "richsleep_event_phase_merged.parquet not found - run 10_richsleep_phase_resolved_eap.py first."
    )
merged_190 = pd.read_parquet(merged_190_path[-1])
print(f"  original 190-event geometry-valid, N2-staged subsample (for comparability): "
      f"n_subjects={merged_190['subject_id'].nunique()}, n_events={len(merged_190)}")

SAMPLES = {
    "full_catalog": full_df,
    "quality_filtered": quality_df,
    "geometry_valid_190": merged_190,
}

# ─────────────────────────────────────────────────────────────────────────
# Primary family: {cardiac_onset, resp_onset} x {full_catalog, quality_filtered}
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Primary family: corrected subject-rotation permutation test ===")
primary_rows = []
for sample_name in ["full_catalog", "quality_filtered"]:
    for channel in PHASE_CHANNELS_PRIMARY:
        row = run_channel(sample_name, channel, SAMPLES[sample_name])
        primary_rows.append(row)
        print(f"  [{sample_name}] {channel}: n={row['perm_n_events']}, "
              f"naive_pooled_R1={row['naive_pooled_R1']:.4f}, "
              f"perm_p_R1={row['perm_perm_p_R1']:.4f}, perm_p_T2={row['perm_perm_p_T2']:.4f}, "
              f"boot_R1_CI=[{row['boot_R1_ci_lo']:.4f}, {row['boot_R1_ci_hi']:.4f}]")

primary_df = pd.DataFrame(primary_rows)
primary_df["perm_p_R1_fdr"] = bh_fdr(primary_df["perm_perm_p_R1"].to_numpy())
primary_df["perm_p_T2_fdr"] = bh_fdr(primary_df["perm_perm_p_T2"].to_numpy())
primary_df.to_csv(OUT / "molB_primary_corrected_permutation.csv", index=False)

print("\nPrimary family BH-FDR summary:")
print(primary_df[["sample", "channel", "perm_n_events", "naive_pooled_R1",
                   "perm_perm_p_R1", "perm_p_R1_fdr", "perm_perm_p_T2", "perm_p_T2_fdr"]]
      .to_string(index=False))

# ─────────────────────────────────────────────────────────────────────────
# Secondary / exploratory: peak-phase + 190-subsample re-analysis
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Secondary/exploratory: peak-phase channels + 190-event subsample ===")
secondary_rows = []
for sample_name, channels in [
    ("full_catalog", PHASE_CHANNELS_SECONDARY),
    ("quality_filtered", PHASE_CHANNELS_SECONDARY),
    ("geometry_valid_190", PHASE_CHANNELS_PRIMARY + PHASE_CHANNELS_SECONDARY),
]:
    for channel in channels:
        if channel not in SAMPLES[sample_name].columns:
            continue
        row = run_channel(sample_name, channel, SAMPLES[sample_name])
        secondary_rows.append(row)
        print(f"  [{sample_name}] {channel}: n={row['perm_n_events']}, "
              f"naive_pooled_R1={row['naive_pooled_R1']:.4f}, perm_p_R1={row['perm_perm_p_R1']:.4f}")

secondary_df = pd.DataFrame(secondary_rows)
secondary_df["perm_p_R1_fdr_within_block"] = np.nan
secondary_df.to_csv(OUT / "molB_secondary_exploratory_permutation.csv", index=False)

# ─────────────────────────────────────────────────────────────────────────
# Retained for context: per-subject Rayleigh + second-order Rayleigh
# (already pseudo-replication-safe; unaffected by the S7 critique)
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Context (unaffected by the correction): per-subject + second-order Rayleigh ===")
subj_rows: list = []
second_order_rows: list = []
for sample_name, channels in [
    ("full_catalog", PHASE_CHANNELS_PRIMARY + PHASE_CHANNELS_SECONDARY),
    ("geometry_valid_190", PHASE_CHANNELS_PRIMARY + PHASE_CHANNELS_SECONDARY),
]:
    for channel in channels:
        if channel not in SAMPLES[sample_name].columns:
            continue
        per_subject_and_second_order(sample_name, channel, SAMPLES[sample_name], subj_rows, second_order_rows)

subj_df = pd.DataFrame(subj_rows)
subj_df["rayleigh_p_fdr"] = np.nan
for (sample_name, channel), idx in subj_df.groupby(["sample", "channel"]).groups.items():
    mask = subj_df.index.isin(idx)
    subj_df.loc[mask, "rayleigh_p_fdr"] = bh_fdr(subj_df.loc[mask, "rayleigh_p"].to_numpy())
subj_df.to_csv(OUT / "molB_per_subject_rayleigh.csv", index=False)

second_order_df = pd.DataFrame(second_order_rows)
second_order_df["rayleigh_p_second_order_fdr"] = bh_fdr(second_order_df["rayleigh_p_second_order"].to_numpy())
second_order_df.to_csv(OUT / "molB_second_order_rayleigh.csv", index=False)

print("\nPer-subject Rayleigh (n FDR-significant / n subjects), by sample x channel:")
for (sample_name, channel), sub in subj_df.groupby(["sample", "channel"]):
    n_sig = int((sub["rayleigh_p_fdr"] < 0.05).sum())
    print(f"  [{sample_name}] {channel}: {n_sig}/{len(sub)} subjects FDR-significant "
          f"(median R={sub['R'].median():.3f}, median n_events={sub['n_events'].median():.0f})")

print("\nSecond-order (population-level) Rayleigh on subject mean directions:")
print(second_order_df.to_string(index=False))

# ─────────────────────────────────────────────────────────────────────────
# Exploratory categorical cross-check: inhale_at_onset vs. 0.5
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Exploratory: inhale_at_onset categorical cross-check (full catalog) ===")
inhale_result = binary_subject_level_test(
    full_df["inhale_at_onset"].to_numpy(), full_df["subject_id"].to_numpy()
)
print(inhale_result)
pd.DataFrame([inhale_result]).to_csv(OUT / "molB_inhale_categorical_crosscheck.csv", index=False)

print("\n=== Corrected Mal B reanalysis complete ===")
print(f"All outputs in: {OUT}")
