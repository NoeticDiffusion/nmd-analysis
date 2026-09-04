"""Aggregate hourly run-level turning-angle features to patient level.

Input: ``run_hour_level_turning_features.csv`` from stage 04.
Output: one weighted row per (patient, hour_bin, chart, lag), where a run's
weight is its valid turning-triple count.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

import coma_angle_support  # noqa: F401


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "patient_features_hourly"
METRIC_COLUMNS = (
    "turn_cos_mean",
    "turn_angle_median",
    "turn_angle_mad",
    "turn_angle_iqr",
    "turn_angle_p90",
    "turn_fraction_gt_90",
    "turn_fraction_gt_120",
    "turn_entropy",
    "turn_length_coupling",
    "null_z_median_angle",
)


@dataclass(frozen=True)
class Config:
    run_level_path: Path
    output_dir: Path


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Aggregate hourly turning-angle features to patient level.")
    parser.add_argument("--run-level-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    return Config(run_level_path=args.run_level_path, output_dir=args.output_dir)


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    value_array = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    weight_array = pd.to_numeric(weights, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(value_array) & np.isfinite(weight_array) & (weight_array > 0)
    return float(np.average(value_array[mask], weights=weight_array[mask])) if mask.any() else float("nan")


def aggregate_patient_hour_features(run_features: pd.DataFrame) -> pd.DataFrame:
    if run_features.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    group_columns = ["subject", "hour_bin", "time_bin", "chart", "lag_epochs"]
    for keys, group in run_features.groupby(group_columns, dropna=False, sort=False):
        subject, hour_bin, time_bin, chart, lag = keys
        ok = group[group["status"] == "ok"]
        weights = pd.to_numeric(ok.get("n_valid", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
        row: Dict[str, Any] = {
            "subject": subject,
            "hour_bin": hour_bin,
            "time_bin": time_bin,
            "chart": chart,
            "lag_epochs": lag,
            "n_runs_total": int(len(group)),
            "n_runs_ok": int(len(ok)),
            "n_valid_angles_total": float(weights.sum()),
            "cpc": group["cpc"].dropna().iloc[0] if group["cpc"].notna().any() else np.nan,
            "hospital": group["hospital"].dropna().iloc[0] if group["hospital"].notna().any() else None,
            "cohort_tags_present": ",".join(sorted(set(group["cohort_tag"].dropna().astype(str)))),
        }
        for metric in METRIC_COLUMNS:
            row[metric] = weighted_mean(ok[metric], weights) if metric in ok.columns else np.nan
        rows.append(row)
    return pd.DataFrame(rows).sort_values(group_columns).reset_index(drop=True)


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    features = aggregate_patient_hour_features(pd.read_csv(config.run_level_path))
    output_path = config.output_dir / "patient_hour_chart_lag_turning_features.csv"
    features.to_csv(output_path, index=False)
    print(f"Wrote patient x hour x chart x lag turning features ({len(features)} rows) to {output_path}")
    if not features.empty:
        print(f"Distinct patients: {features['subject'].nunique()}")


if __name__ == "__main__":
    sys.exit(main())
