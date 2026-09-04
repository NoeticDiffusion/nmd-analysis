"""
02_build_merged_table.py -- Build the 190-event geometry x phase_resolved_v3
master table (Phase 2, task 5 of
.cursor/plans/richsleep_eap_v2_article_aa3119f9.plan.md).

Reuses the already-verified RichSleep event-locked geometry table from the
companion article (RVC_SLEEP_peak_analysis's 09_richsleep_verification.py
output, `event_level_richsleep.parquet`) as a lineage copy -- geometry
(coords_9d and its deltas) is unchanged by the new NMD delivery (confirmed
by 01_validate_v3_delivery.py's v2-vs-v3 bit-identity check), so there is no
reason to recompute it. This script only adds the new qe (spindle-strength/
SO-coupling) columns from `phase_resolved_v3` via the same onset-catalog
exact-match merge used by RVC_SLEEP_peak_analysis's
10_richsleep_phase_resolved_eap.py (diary 235's >99% match-rate gate).

Run: python src/02_build_merged_table.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from rvc_sleep_support import (
    GEOMETRY_COLS,
    PEAK_ANALYSIS_DIR,
    load_phase_v3,
    make_results_subdir,
)

OUT = make_results_subdir("02_build_merged_table")

# ─────────────────────────────────────────────────────────────────────────
# Load the companion article's already-verified event-level geometry table
# (lineage copy, not recomputed -- see module docstring).
# ─────────────────────────────────────────────────────────────────────────
event_level_candidates = sorted(
    (PEAK_ANALYSIS_DIR / "results").glob("rvc_sleep_*/09_richsleep_verification/event_level_richsleep.parquet")
)
if not event_level_candidates:
    raise RuntimeError(
        f"No event_level_richsleep.parquet found under {PEAK_ANALYSIS_DIR / 'results'} -- "
        "run RVC_SLEEP_peak_analysis's 09_richsleep_verification.py first."
    )
event_level_path = event_level_candidates[-1]
print(f"Lineage source: {event_level_path}")
event_level = pd.read_parquet(event_level_path)
event_rows = event_level[event_level["bin_label"] == "event"].copy()
print(f"  event_level rows (all bin_labels): {len(event_level)}; geometry-valid event rows: {len(event_rows)}")

# pre_far endpoint means (needed for the event_prefar delta mode downstream,
# mirrors 09_richsleep_verification.py's far_geom_frame construction).
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
print(f"  event_rows after pre_far merge: {event_rows.shape}")

# ─────────────────────────────────────────────────────────────────────────
# Load phase_resolved_v3 and re-verify the onset-catalog match rate inline
# (fails loudly if this is ever re-run against stale/mismatched data, same
# discipline as the original 10_richsleep_phase_resolved_eap.py).
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Loading phase_resolved_v3 (24 subjects) ===")
phase_df = load_phase_v3()
print(f"  n_subjects: {phase_df['subject_id'].nunique()}, n_events: {len(phase_df)}")

merge_check = event_rows.merge(
    phase_df[["subject_id", "onset_sec"]],
    left_on=["subject_id", "event_onset_sec"], right_on=["subject_id", "onset_sec"],
    how="left", indicator=True,
)
match_rate = (merge_check["_merge"] == "both").mean()
print(f"  onset-catalog match rate (event_level vs phase_resolved_v3): {match_rate:.4f}")
if match_rate < 0.99:
    raise RuntimeError(
        f"event_level and phase_resolved_v3 onset catalogs do not match (match_rate={match_rate:.4f}). "
        "Do not proceed -- re-verify run roots before trusting any join."
    )

merged = event_rows.merge(
    phase_df, left_on=["subject_id", "event_onset_sec"], right_on=["subject_id", "onset_sec"],
    how="inner", suffixes=("", "_phase"),
)
print(f"  merged event-level x phase_resolved_v3 table: {merged.shape}")
assert len(merged) == 190, f"Expected 190 geometry-valid events, got {len(merged)}"

# ─────────────────────────────────────────────────────────────────────────
# Quick qe-column summary for downstream scripts (transform choice etc.)
# ─────────────────────────────────────────────────────────────────────────
print("\n=== qe column summary (190 geometry-valid events) ===")
for col in ["sigma_power_z_n2", "amplitude", "frequency_hz", "so_spindle_coupling_score"]:
    if col in merged.columns:
        n_valid = merged[col].notna().sum()
        print(f"  {col}: n_valid={n_valid}, mean={merged[col].mean():.3f}, "
              f"median={merged[col].median():.3f}, skew={merged[col].skew():.3f}")
n_so_coupled = int((merged["so_partner_missing"] == 0).sum())
n_so_coupled_subj = merged.loc[merged["so_partner_missing"] == 0, "subject_id"].nunique()
print(f"  SO-coupled subset: {n_so_coupled} events / {n_so_coupled_subj} subjects "
      f"(exploratory-only, per plan's power caveat)")

merged.to_parquet(OUT / "richsleep_event_phase_v3_merged.parquet", index=False)
print(f"\nWrote: {OUT / 'richsleep_event_phase_v3_merged.parquet'}")
