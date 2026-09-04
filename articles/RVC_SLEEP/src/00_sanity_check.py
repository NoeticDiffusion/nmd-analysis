"""
00_sanity_check.py — QC audit for the RVC_SLEEP analysis-repo side, before any
Pass A/B/C modelling.

This re-verifies (on the analysis side) what Gate #2 QC already established on
the NMD ingest side (see handover_From_nmd.md §4), so that a stale copy, wrong
run folder, or partial `data/raw/` transfer is caught immediately rather than
silently propagating into the passes.

Reports:
  A. Run-manifest identity check (config_hash, dataset_id) for all 4 frozen roots
  B. Subject/session counts vs. handover_From_nmd.md expectations
  C. Event-locked row counts, condition/bin_label coverage, per dataset
  D. Anchor-column (HRV / respiratory) NaN rates on the primary surface
  E. coords_9d_finite / n2 coverage (the Pass A base filter)
  F. Summary tables written to results/

Run: python src/00_sanity_check.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from rvc_sleep_support import (
    ANCHOR_COLS_BY_DATASET,
    BIN_LABEL_ORDER,
    CONFIG_HASH,
    CONDITION_CONTROL,
    CONDITION_EVENT,
    DATASETS,
    EXPECTED_N_SUBJECTS,
    PRIMARY_ANCHOR_COL,
    RUN_ROOTS,
    SURFACES,
    load_all_primary,
    make_results_subdir,
)

OUT = make_results_subdir("00_sanity_check")

# ──────────────────────────────────────────────────────────────────────────────
# A + B. Run-manifest identity and subject-count check
# ──────────────────────────────────────────────────────────────────────────────
print("=== A. Run-manifest identity check ===")
manifest_rows = []
for (dataset, surface), root in RUN_ROOTS.items():
    manifest_path = root / "run_manifest.json"
    row = {
        "dataset": dataset,
        "surface": surface,
        "run_dir": root.name,
        "manifest_exists": manifest_path.exists(),
        "digest_ok": False,
        "n_subjects": np.nan,
        "n_subjects_ok": False,
    }
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        digest = manifest.get("config", {}).get("digest_sha256", "")
        expected = CONFIG_HASH.get((dataset, surface), "")
        row["digest_ok"] = digest.startswith(expected) if expected else False
        n_subj = manifest.get("subjects_index", {}).get("subjects", {}).get("count", np.nan)
        row["n_subjects"] = n_subj
        row["n_subjects_ok"] = n_subj == EXPECTED_N_SUBJECTS.get(dataset)
    manifest_rows.append(row)

manifest_df = pd.DataFrame(manifest_rows)
print(manifest_df.to_string(index=False))
manifest_df.to_csv(OUT / "run_manifest_check.csv", index=False)

if not manifest_df["manifest_exists"].all():
    print("\n  WARNING: one or more run_manifest.json files are missing under data/raw/.")
if not manifest_df["digest_ok"].all():
    print("\n  WARNING: one or more config_hash values do not match handover_From_nmd.md.")
if not manifest_df["n_subjects_ok"].all():
    print("\n  WARNING: one or more subject counts do not match the expected 27 (ANPHY) / 128 (BOAS).")

# ──────────────────────────────────────────────────────────────────────────────
# C. Event-locked row counts and condition/bin_label coverage (primary surface)
# ──────────────────────────────────────────────────────────────────────────────
print("\n=== B. Loading primary event-locked parquets ===")
primary = load_all_primary()
print(f"  Total rows: {len(primary):,}")
print(f"  Datasets:   {primary['dataset_id'].value_counts().to_dict()}")
print(f"  Subjects:   {primary.groupby('dataset_id')['subject_id'].nunique().to_dict()}")

print("\n--- C. Condition x bin_label coverage ---")
coverage = (
    primary.groupby(["dataset_id", "condition", "bin_label"])
    .size()
    .reset_index(name="n_rows")
)
print(coverage.to_string(index=False))
coverage.to_csv(OUT / "event_locked_coverage.csv", index=False)

n_events = primary[primary["condition"] == CONDITION_EVENT].groupby("dataset_id").size()
n_controls = primary[primary["condition"] == CONDITION_CONTROL].groupby("dataset_id").size()
print(f"\n  spindle_event rows per dataset:  {n_events.to_dict()}")
print(f"  matched_control rows per dataset: {n_controls.to_dict()}")

missing_bins = set(BIN_LABEL_ORDER) - set(
    primary.loc[primary["condition"] == CONDITION_EVENT, "bin_label"].unique()
)
if missing_bins:
    print(f"  WARNING: missing spindle_event bin_label(s): {missing_bins}")
else:
    print("  All 5 spindle peri-event bins present.")

# ──────────────────────────────────────────────────────────────────────────────
# D. Anchor-column NaN rates (primary surface, per dataset)
# ──────────────────────────────────────────────────────────────────────────────
print("\n=== D. Anchor-column NaN rates (primary surface) ===")
anchor_rows = []
for dataset in DATASETS:
    sub = primary[primary["dataset_id"] == dataset]
    for col in ANCHOR_COLS_BY_DATASET.get(dataset, []):
        if col not in sub.columns:
            anchor_rows.append({"dataset": dataset, "column": col, "present": False,
                                 "nan_rate": np.nan, "n_subjects_valid_pre_far": np.nan})
            continue
        nan_rate = sub[col].isna().mean()
        pre_far = sub[(sub["condition"] == CONDITION_EVENT) & (sub["bin_label"] == "pre_far")]
        n_valid_subj = pre_far.loc[pre_far[col].notna(), "subject_id"].nunique()
        anchor_rows.append({
            "dataset": dataset, "column": col, "present": True,
            "nan_rate": round(float(nan_rate), 4),
            "n_subjects_valid_pre_far": n_valid_subj,
        })
anchor_df = pd.DataFrame(anchor_rows)
print(anchor_df.to_string(index=False))
anchor_df.to_csv(OUT / "anchor_nan_rates.csv", index=False)

primary_anchor_summary = {ds: PRIMARY_ANCHOR_COL[ds] for ds in DATASETS}
print(f"\n  Pass C primary anchors: {primary_anchor_summary}")

# ──────────────────────────────────────────────────────────────────────────────
# E. Pass A base filter coverage (coords_9d_finite, n2)
# ──────────────────────────────────────────────────────────────────────────────
print("\n=== E. Pass A base filter coverage ===")
filter_rows = []
for dataset in DATASETS:
    sub = primary[primary["dataset_id"] == dataset]
    row = {"dataset": dataset, "n_rows": len(sub)}
    if "coords_9d_finite" in sub.columns:
        row["frac_coords_9d_finite"] = round(float((sub["coords_9d_finite"] == 1).mean()), 4)
    if "n2" in sub.columns:
        row["frac_n2"] = round(float((sub["n2"] == 1).mean()), 4)
    filter_rows.append(row)
filter_df = pd.DataFrame(filter_rows)
print(filter_df.to_string(index=False))
filter_df.to_csv(OUT / "pass_a_filter_coverage.csv", index=False)

print("\n=== Sanity check complete ===")
print(f"All outputs in: {OUT}")
