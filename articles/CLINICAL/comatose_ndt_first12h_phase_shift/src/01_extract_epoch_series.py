"""Extract per-epoch 9D+composite chart series for the first N hours post-arrest.

Reuses H5 discovery, run-identity parsing, and anchor-relative timing from
``comatose_ndt/src/icare_patient_timeline_analysis.py`` (via ``summarize_run``
for per-run metadata) so this pipeline inherits the same QC/inclusion
conventions as the published article, instead of re-deriving them.

See ``coma_phase_shift_support.py`` for the d_n naming caveat: this script
does not treat d_n specially, it just resolves whatever coordinates the H5
9D chart contract exposes.

Output: one consolidated parquet of epoch-level rows
(subject, run, acq, epoch_idx, t_hours_from_anchor, <12 coordinate columns>)
clipped to [0, max_hours), plus a per-run extraction QC CSV.
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from itertools import repeat
from pathlib import Path
from typing import Any, Dict, List, Optional

import h5py
import numpy as np
import pandas as pd

import coma_phase_shift_support as support

from icare_patient_timeline_analysis import (  # noqa: E402
    DEFAULT_RAW_ROOT,
    iter_h5_paths,
    parse_run_identity,
    resolve_default_processed_root,
    summarize_run,
)
from ndt_analysis.h5_contract import resolve_coords_9d  # noqa: E402


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "epoch_series"
DEFAULT_MAX_HOURS = 12.0
# The generic ndt_analysis default is "cohort_anchored", but the I-CARE coma
# pipeline always runs with "subject_anchored" (see
# comatose_ndt/config/icare_ndt_analysis.yaml: coordinate_contract). I-CARE
# H5 exports only populate the subject_anchored coordinate groups, so using
# the generic default here silently drops every run (resolve_coords_9d
# returns None -> status "missing_coords_9d").
DEFAULT_ICARE_COORDINATE_CONTRACT = "subject_anchored"


@dataclass(frozen=True)
class ExtractConfig:
    processed_root: Path
    raw_root: Path
    output_dir: Path
    coordinate_contract: str
    max_hours: float
    cohort_tag: str
    limit_h5: Optional[int]
    workers: int


def parse_args() -> ExtractConfig:
    parser = argparse.ArgumentParser(
        description="Extract per-epoch 9D+composite MNPS chart series for the first N hours post-arrest."
    )
    parser.add_argument("--processed-root", type=Path, default=resolve_default_processed_root())
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--coordinate-contract",
        type=str,
        default=DEFAULT_ICARE_COORDINATE_CONTRACT,
        choices=["cohort_anchored", "subject_anchored", "legacy"],
    )
    parser.add_argument(
        "--max-hours",
        type=float,
        default=DEFAULT_MAX_HOURS,
        help="Upper bound (exclusive) on anchor-relative hours to retain per epoch.",
    )
    parser.add_argument(
        "--cohort-tag",
        type=str,
        default="part1",
        help="Provenance tag (e.g. part1/part2) carried through to downstream merge/dedup steps.",
    )
    parser.add_argument("--limit-h5", type=int, default=None)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    return ExtractConfig(
        processed_root=args.processed_root,
        raw_root=args.raw_root,
        output_dir=args.output_dir,
        coordinate_contract=args.coordinate_contract,
        max_hours=float(args.max_hours),
        cohort_tag=args.cohort_tag,
        limit_h5=args.limit_h5,
        workers=max(1, int(args.workers)),
    )


def read_window_anchor_times(h5: h5py.File) -> tuple[Optional[np.ndarray], str]:
    """Return (seconds-from-subject-anchor per window, source label)."""
    windows = None
    if "extensions" in h5 and "time_reference" in h5["extensions"] and "windows" in h5["extensions"]["time_reference"]:
        windows = h5["extensions"]["time_reference"]["windows"]
    if windows is not None and "window_start_from_anchor_sec" in windows:
        return np.asarray(windows["window_start_from_anchor_sec"][:], dtype=float), "time_reference_windows"
    return None, "missing"


def extract_run_epoch_frame(
    path: Path,
    raw_root: Path,
    coordinate_contract: str,
    max_hours: float,
    cohort_tag: str,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    identity = parse_run_identity(path)
    meta_row = summarize_run(path, raw_root, coordinate_contract)

    qc: Dict[str, Any] = {
        "subject": meta_row.get("subject"),
        "run": meta_row.get("run"),
        "acq": meta_row.get("acq"),
        "processed_h5_path": str(path),
        "cohort_tag": cohort_tag,
        "cpc": meta_row.get("cpc"),
        "hospital": meta_row.get("hospital"),
        "status": "ok",
        "timing_source": "missing",
        "n_total_epochs": 0,
        "n_kept_epochs": 0,
    }

    with h5py.File(path, "r") as h5:
        resolved = resolve_coords_9d(h5, coordinate_contract)
        if resolved is None or resolved.values.size == 0:
            qc["status"] = "missing_coords_9d"
            return pd.DataFrame(), qc

        values = np.asarray(resolved.values, dtype=float)
        names = list(resolved.names)
        qc["n_total_epochs"] = int(values.shape[0])

        anchor_times, timing_source = read_window_anchor_times(h5)
        if anchor_times is None or anchor_times.size != values.shape[0]:
            window_start = (
                np.asarray(h5["window_start"][:], dtype=float)
                if "window_start" in h5
                else np.arange(values.shape[0], dtype=float) * support.EPOCH_STEP_SEC
            )
            resolved_start = meta_row.get("resolved_run_start_elapsed_sec", np.nan)
            if np.isfinite(resolved_start) and window_start.size == values.shape[0]:
                anchor_times = float(resolved_start) + (window_start - window_start[0])
                timing_source = "run_level_fallback"
            else:
                anchor_times = window_start
                timing_source = "unanchored_fallback"
        qc["timing_source"] = timing_source

    hours_from_anchor = anchor_times / 3600.0
    mask = np.isfinite(hours_from_anchor) & (hours_from_anchor >= 0.0) & (hours_from_anchor < max_hours)
    n_kept = int(mask.sum())
    qc["n_kept_epochs"] = n_kept
    if n_kept == 0:
        qc["status"] = "no_epochs_in_window"
        return pd.DataFrame(), qc

    kept_values = values[mask]
    kept_hours = hours_from_anchor[mask]
    composites = support.compute_composites(kept_values, names)

    frame = pd.DataFrame(
        {
            "subject": meta_row.get("subject"),
            "run": meta_row.get("run"),
            "acq": meta_row.get("acq"),
            "cohort_tag": cohort_tag,
            "cpc": meta_row.get("cpc"),
            "hospital": meta_row.get("hospital"),
            "age": meta_row.get("age"),
            "sex": meta_row.get("sex"),
            "epoch_idx": np.arange(n_kept, dtype=int),
            "t_hours_from_anchor": kept_hours,
            "timing_source": timing_source,
        }
    )
    for idx, name in enumerate(names):
        frame[name] = kept_values[:, idx]
    for composite_name, composite_values in composites.items():
        frame[composite_name] = composite_values

    return frame, qc


def build_epoch_table(config: ExtractConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    h5_paths = list(iter_h5_paths(config.processed_root, config.limit_h5))
    if config.workers <= 1 or len(h5_paths) <= 1:
        results = [
            extract_run_epoch_frame(path, config.raw_root, config.coordinate_contract, config.max_hours, config.cohort_tag)
            for path in h5_paths
        ]
    else:
        with ProcessPoolExecutor(max_workers=config.workers) as executor:
            results = list(
                executor.map(
                    extract_run_epoch_frame,
                    h5_paths,
                    repeat(config.raw_root),
                    repeat(config.coordinate_contract),
                    repeat(config.max_hours),
                    repeat(config.cohort_tag),
                    chunksize=8,
                )
            )
    frames: List[pd.DataFrame] = [frame for frame, _ in results if not frame.empty]
    qc_rows: List[Dict[str, Any]] = [qc for _, qc in results]
    epoch_table = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    qc_table = pd.DataFrame(qc_rows)
    return epoch_table, qc_table


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    epoch_table, qc_table = build_epoch_table(config)

    epoch_path = config.output_dir / f"epoch_series_first{config.max_hours:g}h_{config.cohort_tag}.parquet"
    qc_path = config.output_dir / f"epoch_extraction_qc_{config.cohort_tag}.csv"
    epoch_table.to_parquet(epoch_path, index=False)
    qc_table.to_csv(qc_path, index=False)

    print(f"Wrote {len(epoch_table)} epoch rows across {qc_table['subject'].nunique() if not qc_table.empty else 0} subjects to {epoch_path}")
    print(f"Wrote extraction QC ({len(qc_table)} runs) to {qc_path}")
    if not qc_table.empty:
        print("Status counts:", qc_table["status"].value_counts(dropna=False).to_dict())
        print("Timing source counts:", qc_table["timing_source"].value_counts(dropna=False).to_dict())


if __name__ == "__main__":
    sys.exit(main())
