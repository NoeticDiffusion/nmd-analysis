"""Run PELT changepoint ("phase-shift") detection on the extracted epoch series.

Input: the ``epoch_series_first<N>h_<cohort_tag>.parquet`` file written by
``01_extract_epoch_series.py``.

For every (subject, run, acq, coordinate) series (coordinate in the 9D chart
plus the m/d/e composites - see ``coma_phase_shift_support.ALL_COORDINATES``),
this script:

1. Robust-z-scores the series (median/MAD) so the PELT penalty is comparable
   across runs of different absolute scale.
2. Runs PELT (``ruptures``, default model "rbf") to find changepoints.
3. Computes, per detected changepoint, a normalized level-jump magnitude and
   a Welch-style "quality" score (see ``coma_phase_shift_support.detect_shifts_pelt``
   for the exact, explicit definitions - neither is a native ruptures cost
   value or a p-value).
4. Summarizes to one row per (run, coordinate): shift count, shift rate per
   hour of analyzed data, and magnitude/quality summary statistics.

Output: ``run_level_shift_features_<cohort_tag>.csv``.
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

import coma_phase_shift_support as support


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ARTICLE_DIR / "results" / "epoch_series"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "shift_detection"


@dataclass(frozen=True)
class DetectConfig:
    epoch_series_path: Path
    output_dir: Path
    cohort_tag: str
    pelt_model: str
    pelt_penalty_scale: float
    min_epochs: int
    workers: int


def parse_args() -> DetectConfig:
    parser = argparse.ArgumentParser(description="Detect PELT phase-shifts in per-epoch MNPS chart coordinates.")
    parser.add_argument("--epoch-series-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--cohort-tag", type=str, default="part1")
    parser.add_argument("--pelt-model", type=str, default=support.PELT_MODEL, choices=["rbf", "l2", "l1"])
    parser.add_argument("--pelt-penalty-scale", type=float, default=support.PELT_PENALTY_SCALE)
    parser.add_argument("--min-epochs", type=int, default=support.MIN_EPOCHS_FOR_PELT)
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Process workers, parallelized over (subject, run, acq) groups. PELT is the bottleneck, so >1 is recommended for real cohorts.",
    )
    args = parser.parse_args()
    return DetectConfig(
        epoch_series_path=args.epoch_series_path,
        output_dir=args.output_dir,
        cohort_tag=args.cohort_tag,
        pelt_model=args.pelt_model,
        pelt_penalty_scale=args.pelt_penalty_scale,
        min_epochs=args.min_epochs,
        workers=max(1, int(args.workers)),
    )


def detect_shifts_for_series(series: pd.DataFrame, coordinate: str, config: DetectConfig) -> Dict[str, Any]:
    ordered = series.sort_values("t_hours_from_anchor")
    raw = ordered[coordinate].to_numpy(dtype=float)
    hours = ordered["t_hours_from_anchor"].to_numpy(dtype=float)
    duration_hours = float(hours[-1] - hours[0]) if hours.size >= 2 else float("nan")

    base_row: Dict[str, Any] = {
        "coordinate": coordinate,
        "n_epochs_available": int(raw.size),
        "duration_hours": duration_hours,
        "pelt_model": config.pelt_model,
    }

    if raw.size < config.min_epochs:
        return {
            **base_row,
            "status": "insufficient_epochs",
            "n_epochs_analyzed": int(np.isfinite(raw).sum()),
            "n_shifts": np.nan,
            "shift_rate_per_hour": np.nan,
            "mean_shift_magnitude": np.nan,
            "median_shift_magnitude": np.nan,
            "mean_shift_quality": np.nan,
            "median_shift_quality": np.nan,
            "median_segment_length_epochs": np.nan,
            "pelt_penalty": np.nan,
        }

    zscored = support.robust_zscore(raw)
    result = support.detect_shifts_pelt(zscored, model=config.pelt_model, penalty_scale=config.pelt_penalty_scale)
    if result is None:
        return {
            **base_row,
            "status": "insufficient_epochs",
            "n_epochs_analyzed": int(np.isfinite(raw).sum()),
            "n_shifts": np.nan,
            "shift_rate_per_hour": np.nan,
            "mean_shift_magnitude": np.nan,
            "median_shift_magnitude": np.nan,
            "mean_shift_quality": np.nan,
            "median_shift_quality": np.nan,
            "median_segment_length_epochs": np.nan,
            "pelt_penalty": np.nan,
        }

    magnitudes = np.asarray(result["shift_magnitudes"], dtype=float)
    qualities = np.asarray(result["shift_qualities"], dtype=float)
    n_shifts = result["n_shifts"]
    shift_rate_per_hour = (
        float(n_shifts / duration_hours) if np.isfinite(duration_hours) and duration_hours > 0 else np.nan
    )

    return {
        **base_row,
        "status": "ok",
        "n_epochs_analyzed": result["n_epochs_analyzed"],
        "n_shifts": n_shifts,
        "shift_rate_per_hour": shift_rate_per_hour,
        "mean_shift_magnitude": float(np.nanmean(magnitudes)) if magnitudes.size else np.nan,
        "median_shift_magnitude": float(np.nanmedian(magnitudes)) if magnitudes.size else np.nan,
        "mean_shift_quality": float(np.nanmean(qualities)) if qualities.size else np.nan,
        "median_shift_quality": float(np.nanmedian(qualities)) if qualities.size else np.nan,
        "median_segment_length_epochs": result["median_segment_length_epochs"],
        "pelt_penalty": result["pelt_penalty"],
    }


def process_run_group(group: pd.DataFrame, available_coordinates: List[str], config: DetectConfig) -> List[Dict[str, Any]]:
    meta = {
        "subject": group["subject"].iloc[0],
        "run": group["run"].iloc[0],
        "acq": group["acq"].iloc[0],
        "cohort_tag": group["cohort_tag"].iloc[0] if "cohort_tag" in group.columns else config.cohort_tag,
        "cpc": group["cpc"].iloc[0] if "cpc" in group.columns else np.nan,
        "hospital": group["hospital"].iloc[0] if "hospital" in group.columns else None,
    }
    rows: List[Dict[str, Any]] = []
    for coordinate in available_coordinates:
        row = dict(meta)
        row.update(detect_shifts_for_series(group, coordinate, config))
        rows.append(row)
    return rows


def build_shift_feature_table(epoch_table: pd.DataFrame, config: DetectConfig) -> pd.DataFrame:
    if epoch_table.empty:
        return pd.DataFrame()

    available_coordinates = [coord for coord in support.ALL_COORDINATES if coord in epoch_table.columns]
    group_columns = ["subject", "run", "acq"]
    groups = [group for _, group in epoch_table.groupby(group_columns, dropna=False, sort=False)]

    rows: List[Dict[str, Any]] = []
    if config.workers <= 1 or len(groups) <= 1:
        for idx, group in enumerate(groups, start=1):
            rows.extend(process_run_group(group, available_coordinates, config))
            if idx % 100 == 0 or idx == len(groups):
                print(f"Processed {idx}/{len(groups)} runs.", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=config.workers) as executor:
            futures = [
                executor.submit(process_run_group, group, available_coordinates, config) for group in groups
            ]
            for idx, future in enumerate(futures, start=1):
                rows.extend(future.result())
                if idx % 100 == 0 or idx == len(futures):
                    print(f"Processed {idx}/{len(futures)} runs.", flush=True)
    return pd.DataFrame(rows)


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    epoch_table = pd.read_parquet(config.epoch_series_path)
    shift_features = build_shift_feature_table(epoch_table, config)

    output_path = config.output_dir / f"run_level_shift_features_{config.cohort_tag}.csv"
    shift_features.to_csv(output_path, index=False)

    print(f"Wrote {len(shift_features)} run x coordinate shift-feature rows to {output_path}")
    if not shift_features.empty:
        print("Status counts:", shift_features["status"].value_counts(dropna=False).to_dict())


if __name__ == "__main__":
    sys.exit(main())
