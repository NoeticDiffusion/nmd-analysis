"""Compute Stratified Family Temporal Coupling (SFTC) per APPLESEED session.

Test run: exploratory, not yet part of any manuscript claim. See
`articles/aaa_ideas/ideas_trajectory_repertoire_status_and_infant_eeg.md`.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from family_coupling_support import (
    DEFAULT_DATA_ROOT,
    COORDINATE_CONTRACT,
    LAGS,
    MIN_VALID_PAIRS,
    ORDERED_PAIRS,
    compute_family_coupling,
    contiguous_segments,
    h5_paths,
    read_subject_h5,
    rows_to_wide,
    wide_columns,
)

ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "appleseed_sftc_20260807" / "01_family_coupling"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--limit-sessions", type=int, default=None)
    return parser.parse_args()


def process_one(path: Path) -> tuple[list[dict], dict, dict]:
    subject = read_subject_h5(path)
    if subject is None:
        return [], {}, {"source_h5_path": str(path), "status": "missing_9d_coords"}
    segments = contiguous_segments(subject["time"])
    long_rows = compute_family_coupling(subject["families"], segments)
    meta = {
        "subject_id": subject["subject_id"],
        "session": subject["session"],
        "age_stratum": subject["age_stratum"],
        "age_days_nominal": subject["age_days_nominal"],
        "sex": subject["sex"],
        "source_group": subject["source_group"],
        "source_h5_path": subject["source_h5_path"],
        "n_timepoints": subject["n_timepoints"],
        "n_contiguous_segments": len(segments),
    }
    for row in long_rows:
        row.update(meta)
    wide_row = {**meta, **rows_to_wide(long_rows)}
    qc_row = {
        **meta,
        "status": "ok",
        "min_n_pairs_any_cell": min((row["n_pairs"] for row in long_rows), default=0),
        "n_cells_below_min_valid_pairs": sum(1 for row in long_rows if row["n_pairs"] < MIN_VALID_PAIRS),
        "n_cells_total": len(long_rows),
    }
    return long_rows, wide_row, qc_row


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    paths = h5_paths(args.data_root)
    if args.limit_sessions:
        paths = paths[: args.limit_sessions]

    all_long: list[dict] = []
    all_wide: list[dict] = []
    all_qc: list[dict] = []
    for path in paths:
        long_rows, wide_row, qc_row = process_one(path)
        all_long.extend(long_rows)
        if wide_row:
            all_wide.append(wide_row)
        all_qc.append(qc_row)

    long_df = pd.DataFrame(all_long).sort_values(["subject_id", "session", "receiver_family", "driver_family", "lag_epochs"])
    wide_df = pd.DataFrame(all_wide).sort_values(["subject_id", "session"])
    qc_df = pd.DataFrame(all_qc).sort_values(["subject_id", "session"])

    long_df.to_csv(args.output_dir / "family_coupling_long.csv", index=False)
    wide_df.to_csv(args.output_dir / "family_coupling_wide.csv", index=False)
    qc_df.to_csv(args.output_dir / "family_coupling_qc.csv", index=False)

    manifest = {
        "data_root": str(args.data_root),
        "coordinate_contract": COORDINATE_CONTRACT,
        "n_h5": len(paths),
        "n_sessions_ok": int(len(wide_df)),
        "n_subjects_ok": int(wide_df["subject_id"].nunique()) if not wide_df.empty else 0,
        "families": ["m", "d", "e"],
        "ordered_pairs": [f"{a}_recv_{b}_drive" for a, b in ORDERED_PAIRS],
        "lags_epochs": list(LAGS),
        "min_valid_pairs": MIN_VALID_PAIRS,
        "wide_endpoint_columns": wide_columns(),
        "n_sessions_below_min_valid_pairs_any_cell": int((qc_df["n_cells_below_min_valid_pairs"] > 0).sum())
        if "n_cells_below_min_valid_pairs" in qc_df
        else None,
        "n_missing_9d": int((qc_df["status"] == "missing_9d_coords").sum()) if "status" in qc_df else 0,
    }
    (args.output_dir / "export_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
