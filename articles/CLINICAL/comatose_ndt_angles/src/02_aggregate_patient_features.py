"""Roll run-level turning-angle features up to one row per (patient, chart, lag).

Input: ``run_level_turning_features.csv`` from ``01_compute_turning_angles.py``
(already deduplicated across cohort parts by that script). Aggregates to
patient level, weighting each run's contribution by its valid-triple count
(``n_valid``), mirroring the ``weighted_mean`` convention used throughout the
comatose_ndt pipeline family.

Output: ``patient_chart_lag_turning_features.csv``.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

import coma_angle_support  # noqa: F401  (side effect: extends sys.path)


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "patient_features"

METRIC_COLUMNS: tuple[str, ...] = (
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
    parser = argparse.ArgumentParser(description="Aggregate run-level turning-angle features to (patient, chart, lag).")
    parser.add_argument("--run-level-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    return Config(run_level_path=args.run_level_path, output_dir=args.output_dir)


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    v = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    w = pd.to_numeric(weights, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(v) & np.isfinite(w) & (w > 0)
    if not np.any(mask):
        return float("nan")
    return float(np.average(v[mask], weights=w[mask]))


def aggregate_patient_features(run_features: pd.DataFrame) -> pd.DataFrame:
    if run_features.empty:
        return pd.DataFrame()

    rows: List[Dict[str, Any]] = []
    for (subject, chart, lag), group in run_features.groupby(["subject", "chart", "lag_epochs"], dropna=False, sort=False):
        ok_group = group[group["status"] == "ok"]
        weights = pd.to_numeric(ok_group.get("n_valid", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
        row: Dict[str, Any] = {
            "subject": subject,
            "chart": chart,
            "lag_epochs": lag,
            "n_runs_total": int(len(group)),
            "n_runs_ok": int(len(ok_group)),
            "n_valid_angles_total": float(weights.sum()),
            "cpc": group["cpc"].dropna().iloc[0] if group["cpc"].notna().any() else np.nan,
            "hospital": group["hospital"].dropna().iloc[0] if "hospital" in group.columns and group["hospital"].notna().any() else None,
            "cohort_tags_present": ",".join(sorted(set(group["cohort_tag"].dropna().astype(str)))),
        }
        for metric in METRIC_COLUMNS:
            if metric not in ok_group.columns:
                row[metric] = np.nan
                continue
            row[metric] = weighted_mean(ok_group[metric], weights)
        rows.append(row)

    return pd.DataFrame(rows).sort_values(["subject", "chart", "lag_epochs"]).reset_index(drop=True)


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    run_features = pd.read_csv(config.run_level_path)
    patient_features = aggregate_patient_features(run_features)

    output_path = config.output_dir / "patient_chart_lag_turning_features.csv"
    patient_features.to_csv(output_path, index=False)

    print(f"Wrote patient x chart x lag turning features ({len(patient_features)} rows) to {output_path}")
    if not patient_features.empty:
        print(f"Distinct patients: {patient_features['subject'].nunique()}")


if __name__ == "__main__":
    sys.exit(main())
