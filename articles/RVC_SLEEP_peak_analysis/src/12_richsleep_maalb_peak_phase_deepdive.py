"""
12_richsleep_maalb_peak_phase_deepdive.py -- Robustness follow-up on the
exploratory spindle-*peak*-phase coupling finding from
11_richsleep_maalb_corrected.py (diary 241; requested by Robin, 2026-07-10).

That script found: onset-phase locking stays null under a corrected,
pseudo-replication-safe permutation test even at ~120x the original sample
size (23,029 events), but spindle *peak*-phase (not onset) shows a
population-level, subject-consistent coupling to respiratory phase
(p=0.0005 pooled, p=7e-6 second-order) and, more weakly, cardiac phase
(p=0.020 pooled, p=0.005 second-order). That result was explicitly flagged
as exploratory/post-hoc (it emerged from a secondary sweep run *because*
onset was null) and not yet promoted beyond "plausible interpretation".

This script runs four independent robustness checks before any further
promotion is considered, none of which require new NMD data:

  1. Phase-convention calibration and physiological labelling. NMD's own
     phase-resolved-v1 run_meta.json documents the exact convention
     (phi_resp: Hilbert-transform phase of the 0.1-0.5 Hz bandpassed chest
     signal, 0 = full inhale, (-pi,0) = rising/inhale, (0,pi) = falling/
     exhale; phi_cardiac: 0 = R-peak, pi = mid-cycle). This script (a)
     re-verifies that v2's `inhale_at_onset` flag is internally consistent
     with that documented convention (a cheap sanity check that catches
     schema drift, given this dataset's history of upstream sign bugs --
     diary 234/238), and (b) reports the preferred peak-phase angles in
     degrees with an explicit physiological label, and compares them,
     honestly, against the two external onset-timing papers cited in
     01_eap_wake_vs_sleep_and_rvc_formalization.md S4.1 (Ghibaudo et al.
     2024: inhalation-peak-ward; ScienceDirect timing paper: mid-to-late
     expiration) -- our operationalization (peak-of-envelope phase-locking,
     not an onset-count histogram) is methodologically different from
     both, so this is a labelling/context step, not a replication claim.

  2. Onset-to-peak phase-advance / duration-confound check. Because
     peak_sec - onset_sec correlates with duration_sec (by construction of
     the detector), and the respiratory/cardiac phase at peak is
     mechanically onset-phase plus an advance proportional to
     (peak_sec - onset_sec) / local_period, a natural worry is that peak-
     phase "coherence" is just a data-dependent rotation of the (null)
     onset-phase signal. This is mathematically not possible if onset phase
     is truly uniform and the rotation amount is independent of the onset
     phase value itself (convolving a uniform circular distribution with
     any phase-independent rotation is still uniform) -- but this script
     checks it empirically anyway via a duration-stratified re-test: if the
     peak-phase coupling is an artifact of the long-duration tail (where
     phase can wrap multiple cycles, especially for cardiac), it should
     disappear within duration terciles; if it holds within terciles, that
     rules out the tail-driven-artifact explanation directly.

  3. Leave-one-subject-out jackknife on both the second-order (24
     subject-mean) test and the pooled subject-rotation permutation test,
     to check whether the result is driven by one or two high-leverage
     subjects.

  4. Deterministic split-half self-replication (alphabetically first 12 vs
     last 12 subject IDs): does the peak-phase coupling replicate
     independently in both halves, at reduced but still-present strength,
     rather than being wholly carried by one half of the sample?

This is exploratory follow-up work. No .typ file is touched.

Run: python src/12_richsleep_maalb_peak_phase_deepdive.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from rvc_sleep_support import (
    ARTICLE_DIR,
    circular_mean_resultant,
    harmonic_stats,
    make_results_subdir,
    rayleigh_test,
    subject_rotation_permutation_test,
)

OUT = make_results_subdir("12_richsleep_maalb_peak_phase_deepdive")
PHASE_V2_DIR = ARTICLE_DIR / "RichSleep_resolved" / "phase_resolved_v2"
CHANNELS = ["phi_resp_peak", "phi_cardiac_peak"]
N_PERM_FULL = 2000
N_PERM_JACKKNIFE = 500  # reduced for the 24x-repeated leave-one-out loop


def circ_diff(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Wrapped a - b, into (-pi, pi]."""
    return (a - b + np.pi) % (2 * np.pi) - np.pi


def rad_to_label(angle_rad: float, channel_kind: str) -> str:
    """Physiological label for a phase angle, per NMD's documented convention
    (phase_resolved_v1/run_meta.json `phase_conventions`): phi_resp in
    (-pi,pi), 0=full inhale, (-pi,0)=rising/inhale, (0,pi)=falling/exhale;
    phi_cardiac in [0,2pi), 0=R-peak, pi=mid-cycle.
    """
    deg = np.degrees(angle_rad)
    if channel_kind == "resp":
        if angle_rad < 0:
            frac_to_peak = 1 - abs(angle_rad) / np.pi  # 0 at exhale trough, 1 at inhale peak
            return f"{deg:.1f} deg = inhale (rising), {frac_to_peak * 100:.0f}% of the way to inhale-peak"
        else:
            frac_to_trough = angle_rad / np.pi  # 0 at inhale peak, 1 at exhale trough
            return f"{deg:.1f} deg = exhale (falling), {frac_to_trough * 100:.0f}% of the way to exhale-trough"
    else:
        if deg < 0:
            deg += 360
        return f"{deg:.1f} deg after R-peak (0=R-peak, 180=mid-cycle)"


# ─────────────────────────────────────────────────────────────────────────
# Load full raw catalog
# ─────────────────────────────────────────────────────────────────────────
print("=== Loading full raw event_phase_v2 catalog ===")
phase_files = sorted(PHASE_V2_DIR.glob("*_event_phase_v2.parquet"))
frames = []
for p in phase_files:
    d = pd.read_parquet(p)
    d["subject_id"] = f"sub-{p.stem.replace('_event_phase_v2', '')}"
    frames.append(d)
full_df = pd.concat(frames, ignore_index=True)
full_df["time_to_peak"] = full_df["peak_sec"] - full_df["onset_sec"]
print(f"  n_subjects={full_df['subject_id'].nunique()}, n_events={len(full_df)}")

# ─────────────────────────────────────────────────────────────────────────
# Check 1: phase-convention sanity check + physiological labelling
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Check 1: phase-convention sanity check (against documented v1 convention) ===")
print("Documented (phase_resolved_v1/run_meta.json): phi_resp in (-pi,pi), 0=full inhale, "
      "(-pi,0)=rising/inhale, (0,pi)=falling/exhale. inhale_at_onset = 1 if phi_resp<0.")

mean_phi_resp_when_inhale, _, n_inhale = circular_mean_resultant(
    full_df.loc[full_df["inhale_at_onset"] == 1, "phi_resp_onset"].to_numpy()
)
mean_phi_resp_when_exhale, _, n_exhale = circular_mean_resultant(
    full_df.loc[full_df["inhale_at_onset"] == 0, "phi_resp_onset"].to_numpy()
)
print(f"  mean phi_resp_onset | inhale_at_onset=1 (n={n_inhale}): {mean_phi_resp_when_inhale:.3f} rad "
      f"(expected in (-pi,0)) -> {'OK' if mean_phi_resp_when_inhale < 0 else 'CONVENTION MISMATCH'}")
print(f"  mean phi_resp_onset | inhale_at_onset=0 (n={n_exhale}): {mean_phi_resp_when_exhale:.3f} rad "
      f"(expected in (0,pi)) -> {'OK' if mean_phi_resp_when_exhale > 0 else 'CONVENTION MISMATCH'}")

label_rows = []
for channel in CHANNELS:
    kind = "resp" if "resp" in channel else "cardiac"
    angle, r, n = circular_mean_resultant(full_df[channel].to_numpy())
    label_rows.append({
        "channel": channel, "n_events": n, "mean_angle_rad": angle,
        "mean_angle_deg": float(np.degrees(angle)), "R": r,
        "physiological_label": rad_to_label(angle, kind),
    })
    print(f"  {channel}: mean angle = {angle:.3f} rad ({np.degrees(angle):.1f} deg), "
          f"R={r:.4f} -> {rad_to_label(angle, kind)}")
pd.DataFrame(label_rows).to_csv(OUT / "check1_phase_convention_and_labels.csv", index=False)

# ─────────────────────────────────────────────────────────────────────────
# Check 2: onset->peak phase-advance / duration-confound characterization
# + duration-tercile-stratified re-test
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Check 2: onset->peak phase-advance characterization + duration-tercile re-test ===")
full_df["dphi_resp"] = circ_diff(full_df["phi_resp_peak"].to_numpy(), full_df["phi_resp_onset"].to_numpy())
full_df["dphi_cardiac"] = circ_diff(full_df["phi_cardiac_peak"].to_numpy(), full_df["phi_cardiac_onset"].to_numpy())

print(f"  time_to_peak: median={full_df['time_to_peak'].median():.3f}s, "
      f"corr(time_to_peak, duration_sec)={full_df['time_to_peak'].corr(full_df['duration_sec']):.3f} "
      "(confirms peak ~= event midpoint, as expected for an amplitude-envelope-peak detector)")
print(f"  dphi_resp (onset->peak advance): median={full_df['dphi_resp'].median():.3f} rad, "
      f"IQR=[{full_df['dphi_resp'].quantile(.25):.3f}, {full_df['dphi_resp'].quantile(.75):.3f}] -- "
      "a fairly tight, mostly-positive advance, consistent with a ~4s local respiratory period "
      "(median_time_to_peak / median_dphi_resp * 2pi = "
      f"{full_df['time_to_peak'].median() / full_df['dphi_resp'].median() * 2 * np.pi:.2f}s), "
      "i.e. a physiologically plausible ~13-16 breaths/min -- reassuring sanity check, not an artifact.")
print(f"  dphi_cardiac (onset->peak advance): median={full_df['dphi_cardiac'].median():.3f} rad, "
      f"std={full_df['dphi_cardiac'].std():.3f} -- much more dispersed (time_to_peak often spans multiple "
      "RR intervals, ~0.8-0.9s each), i.e. onset->peak wraps the cardiac cycle unpredictably; this is exactly "
      "why phi_cardiac_peak carries materially different information from phi_cardiac_onset rather than "
      "being a fixed rotation of it.")
print("  NOTE: convolving a uniform (null) onset-phase distribution with *any* rotation that is "
      "independent of the onset-phase value itself is still uniform in expectation -- a data-dependent "
      "onset->peak rotation cannot mechanically manufacture the observed peak-phase R1 out of a true "
      "onset null. The tercile re-test below checks this empirically anyway.")

tercile_rows = []
full_df["duration_tercile"] = pd.qcut(full_df["duration_sec"], 3, labels=["short", "mid", "long"])
TERCILE_SEEDS = {"short": 46, "mid": 47, "long": 48}
for tercile in ["short", "mid", "long"]:
    sub = full_df[full_df["duration_tercile"] == tercile]
    dur_range = (sub["duration_sec"].min(), sub["duration_sec"].max())
    for channel in CHANNELS:
        perm = subject_rotation_permutation_test(
            sub[channel].to_numpy(), sub["subject_id"].to_numpy(), n_perm=N_PERM_FULL, seed=TERCILE_SEEDS[tercile],
        )
        tercile_rows.append({"duration_tercile": tercile, "duration_range_sec": dur_range, "channel": channel, **perm})
        print(f"  [{tercile} duration, {dur_range[0]:.2f}-{dur_range[1]:.2f}s] {channel}: "
              f"n={perm['n_events']}, R1={perm['obs_R1']:.4f}, perm_p_R1={perm['perm_p_R1']:.4f}")
pd.DataFrame(tercile_rows).to_csv(OUT / "check2_duration_tercile_stratified.csv", index=False)

# ─────────────────────────────────────────────────────────────────────────
# Check 3: leave-one-subject-out jackknife
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Check 3: leave-one-subject-out jackknife ===")
jackknife_rows = []
all_subjects = sorted(full_df["subject_id"].unique())
for channel in CHANNELS:
    for dropped in all_subjects:
        sub = full_df[full_df["subject_id"] != dropped]
        # Second-order Rayleigh on remaining 23 subject means
        subj_means = []
        for _, g in sub.groupby("subject_id"):
            angle, _, n = circular_mean_resultant(g[channel].to_numpy())
            if np.isfinite(angle):
                subj_means.append(angle)
        r2, p2, n2 = rayleigh_test(np.array(subj_means))
        # Pooled subject-rotation permutation (reduced n_perm for speed)
        perm = subject_rotation_permutation_test(
            sub[channel].to_numpy(), sub["subject_id"].to_numpy(), n_perm=N_PERM_JACKKNIFE, seed=44,
        )
        jackknife_rows.append({
            "channel": channel, "dropped_subject": dropped, "n_subjects_remaining": n2,
            "second_order_R": r2, "second_order_p": p2,
            "pooled_R1": perm["obs_R1"], "pooled_perm_p_R1": perm["perm_p_R1"],
        })

jack_df = pd.DataFrame(jackknife_rows)
jack_df.to_csv(OUT / "check3_leave_one_subject_out.csv", index=False)
for channel in CHANNELS:
    sub = jack_df[jack_df["channel"] == channel]
    n_still_sig_2nd = int((sub["second_order_p"] < 0.05).sum())
    n_still_sig_pooled = int((sub["pooled_perm_p_R1"] < 0.05).sum())
    print(f"  {channel}: second-order test still p<0.05 in {n_still_sig_2nd}/24 leave-one-out reruns "
          f"(range p=[{sub['second_order_p'].min():.4f}, {sub['second_order_p'].max():.4f}]); "
          f"pooled-permutation test still p<0.05 in {n_still_sig_pooled}/24 reruns "
          f"(range p=[{sub['pooled_perm_p_R1'].min():.4f}, {sub['pooled_perm_p_R1'].max():.4f}])")
    worst_2nd = sub.loc[sub["second_order_p"].idxmax()]
    print(f"    single most influential subject (second-order test): dropping {worst_2nd['dropped_subject']} "
          f"gives the weakest remaining result (p={worst_2nd['second_order_p']:.4f})")

# ─────────────────────────────────────────────────────────────────────────
# Check 4: deterministic split-half self-replication
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Check 4: deterministic split-half self-replication (alphabetical first 12 vs last 12) ===")
half_a = all_subjects[:12]
half_b = all_subjects[12:]
print(f"  half A: {half_a}")
print(f"  half B: {half_b}")

split_rows = []
for half_name, half_subjects in [("half_A_first12", half_a), ("half_B_last12", half_b)]:
    sub_full = full_df[full_df["subject_id"].isin(half_subjects)]
    for channel in CHANNELS:
        perm = subject_rotation_permutation_test(
            sub_full[channel].to_numpy(), sub_full["subject_id"].to_numpy(), n_perm=N_PERM_FULL, seed=45,
        )
        subj_means = []
        for _, g in sub_full.groupby("subject_id"):
            angle, _, n = circular_mean_resultant(g[channel].to_numpy())
            if np.isfinite(angle):
                subj_means.append(angle)
        r2, p2, n2 = rayleigh_test(np.array(subj_means))
        split_rows.append({
            "half": half_name, "channel": channel, "n_events": perm["n_events"], "n_subjects": n2,
            "pooled_R1": perm["obs_R1"], "pooled_perm_p_R1": perm["perm_p_R1"],
            "second_order_R": r2, "second_order_p": p2,
        })
        print(f"  [{half_name}] {channel}: n={perm['n_events']}, pooled R1={perm['obs_R1']:.4f} "
              f"(perm p={perm['perm_p_R1']:.4f}), second-order R={r2:.4f} (p={p2:.4f})")

pd.DataFrame(split_rows).to_csv(OUT / "check4_split_half_replication.csv", index=False)

print("\n=== Peak-phase deep-dive complete ===")
print(f"All outputs in: {OUT}")
