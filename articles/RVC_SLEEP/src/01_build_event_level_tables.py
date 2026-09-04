"""
01_build_event_level_tables.py — Build the frozen, analysis-ready tables that
every subsequent Pass A/B/C script reads from. This is the most important
script in the pipeline (plan1.md §"Recommended analysis repo first scripts").

Outputs (results/rvc_sleep_<date>/01_build_event_level_tables/):
  event_level_primary.parquet    — spindle_event rows (all 5 peri-event bins),
                                    primary EEG-only surface, both datasets,
                                    with matched-control medians joined on
                                    (dataset_id, event_id)
  event_level_anchor_aug.parquet — same row structure, anchor-augmented surface
  pass_c_anchor_contexts.parquet — per-event pre_far anchor values, ready to be
                                    merged onto all bins of that event for Pass C
  dataset_qc_summary.csv         — row/subject counts per dataset x surface

Run: python src/01_build_event_level_tables.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from rvc_sleep_support import (
    ANCHOR_COLS_BY_DATASET,
    CONDITION_EVENT,
    DATASETS,
    GEOMETRY_COLS,
    MNJ_COLS,
    PRIMARY_ANCHOR_COL,
    REACH_COLS,
    aggregate_controls_per_event,
    load_all_anchor_aug,
    load_all_primary,
    make_results_subdir,
    pass_a_filter,
)

OUT = make_results_subdir("01_build_event_level_tables")


def build_event_level(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to the Pass A base sample, then join matched-control medians
    onto each spindle_event row via (dataset_id, event_id) <-> (dataset_id,
    matched_event_id)."""
    df = pass_a_filter(df)

    value_cols = [c for c in (*GEOMETRY_COLS, *MNJ_COLS, *REACH_COLS) if c in df.columns]
    for ds in DATASETS:
        value_cols += [c for c in ANCHOR_COLS_BY_DATASET.get(ds, []) if c in df.columns]
    value_cols = sorted(set(value_cols))

    control_agg = aggregate_controls_per_event(df, value_cols)

    event_rows = df[df["condition"] == CONDITION_EVENT].copy()
    event_level = event_rows.merge(
        control_agg,
        left_on=["dataset_id", "event_id"],
        right_on=["dataset_id", "matched_event_id"],
        how="left",
        suffixes=("", "_ctrl_join"),
    )
    return event_level


def build_pass_c_anchor_contexts(event_level_primary: pd.DataFrame) -> pd.DataFrame:
    """One row per (dataset_id, subject_id, event_id) with the pre_far anchor
    value(s), ready to be merged onto all bins of that event for Pass C
    moderation models (handover_From_nmd.md §5, Pass C).

    2026-07-03 bugfix: `event_id` is a per-subject-local counter (NOT globally
    unique within a dataset — e.g. `event_id=639` recurs across dozens of
    different subjects in both ANPHY and BOAS; see diary 228/229). The
    original version of this function keyed only on (dataset_id, event_id),
    so 05_pass_c_eap_moderation.py's merge on that same key was a many-to-many
    join that silently duplicated rows and attached the WRONG subject's
    anchor value to most events. Fixed by keying on
    (dataset_id, subject_id, event_id), which is a unique key. A pre_far bin
    can still repeat >1x per event (multiple far-offset windows), so we mean
    -aggregate to one row per event first.
    """
    rows = []
    for ds in DATASETS:
        anchor_cols = [c for c in ANCHOR_COLS_BY_DATASET.get(ds, []) if c in event_level_primary.columns]
        if not anchor_cols:
            continue
        sub = event_level_primary[
            (event_level_primary["dataset_id"] == ds) & (event_level_primary["bin_label"] == "pre_far")
        ]
        keep = (
            sub.groupby(["dataset_id", "subject_id", "event_id"])[anchor_cols]
            .mean()
            .reset_index()
        )
        rename = {c: f"{c}_pre_far" for c in anchor_cols}
        keep = keep.rename(columns=rename)
        rows.append(keep)
    if not rows:
        return pd.DataFrame(columns=["dataset_id", "subject_id", "event_id"])
    return pd.concat(rows, ignore_index=True)


print("Loading primary surface (both datasets) ...")
primary_raw = load_all_primary()
event_level_primary = build_event_level(primary_raw)
event_level_primary.to_parquet(OUT / "event_level_primary.parquet", index=False)
print(f"  event_level_primary: {event_level_primary.shape} -> {OUT / 'event_level_primary.parquet'}")

print("\nLoading anchor-augmented surface (both datasets) ...")
aug_raw = load_all_anchor_aug()
event_level_aug = build_event_level(aug_raw)
event_level_aug.to_parquet(OUT / "event_level_anchor_aug.parquet", index=False)
print(f"  event_level_anchor_aug: {event_level_aug.shape} -> {OUT / 'event_level_anchor_aug.parquet'}")

print("\nBuilding Pass C anchor contexts (pre_far anchors per event) ...")
pass_c_contexts = build_pass_c_anchor_contexts(event_level_primary)
pass_c_contexts.to_parquet(OUT / "pass_c_anchor_contexts.parquet", index=False)
print(f"  pass_c_anchor_contexts: {pass_c_contexts.shape} -> {OUT / 'pass_c_anchor_contexts.parquet'}")

print("\nBuilding dataset QC summary ...")
qc_rows = []
for label, df in [("primary", event_level_primary), ("anchor_aug", event_level_aug)]:
    for ds in DATASETS:
        sub = df[df["dataset_id"] == ds]
        primary_anchor = PRIMARY_ANCHOR_COL.get(ds)
        n_anchor_valid = (
            int(sub[primary_anchor].notna().sum())
            if primary_anchor and primary_anchor in sub.columns
            else None
        )
        qc_rows.append({
            "surface": label,
            "dataset": ds,
            "n_event_rows": len(sub),
            "n_events": sub["event_id"].nunique() if "event_id" in sub.columns else None,
            "n_subjects": sub["subject_id"].nunique() if "subject_id" in sub.columns else None,
            "primary_anchor_col": primary_anchor,
            "n_rows_primary_anchor_valid": n_anchor_valid,
        })
qc_df = pd.DataFrame(qc_rows)
print(qc_df.to_string(index=False))
qc_df.to_csv(OUT / "dataset_qc_summary.csv", index=False)

print("\n=== Event-level table build complete ===")
print(f"All outputs in: {OUT}")

# TODO: once Pass A1/A2 scripts are implemented, confirm event_level_primary
# contains exactly 5 bin_label rows per event_id (pre_far/pre_near/event/
# post_near/post_far) with no duplicate (dataset_id, event_id, bin_label) keys.
