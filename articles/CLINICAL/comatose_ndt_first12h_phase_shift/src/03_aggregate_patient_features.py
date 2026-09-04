"""Roll run-level shift features up to one row per (patient, coordinate).

Accepts one or more ``run_level_shift_features_<cohort_tag>.csv`` files (e.g.
part1 and part2, produced independently by ``02_detect_shifts.py`` against
each processed root) and:

1. Deduplicates overlapping runs across cohorts using the same
   ``build_run_key`` / ``deduplicate_by_key`` (prefer_part2 by default)
   convention as ``comatose_ndt/src/merge_coma_cohort_results.py``, instead
   of re-deriving a dedup policy.
2. Aggregates to patient level per coordinate, weighting each run's
   contribution by its analyzed epoch count (``n_epochs_analyzed``), mirroring
   the ``weighted_mean`` convention used throughout the comatose_ndt pipeline.

Output: ``patient_coordinate_shift_features.csv`` with one row per
(subject, coordinate) plus CPC/hospital metadata.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np
import pandas as pd

import coma_phase_shift_support  # noqa: F401  (side effect: extends sys.path)
from merge_coma_cohort_results import build_run_key, deduplicate_by_key  # noqa: E402


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "patient_features"


@dataclass(frozen=True)
class AggregateConfig:
    run_level_paths: tuple[Path, ...]
    output_dir: Path
    dedup_policy: str


def parse_args() -> AggregateConfig:
    parser = argparse.ArgumentParser(
        description="Aggregate run-level phase-shift features to one row per (patient, coordinate)."
    )
    parser.add_argument(
        "--run-level-path",
        dest="run_level_paths",
        type=Path,
        action="append",
        required=True,
        help="Path to a run_level_shift_features_<cohort_tag>.csv file. Repeat for multiple cohorts (e.g. part1, part2).",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--dedup-policy",
        type=str,
        choices=["prefer_part2", "prefer_part1", "error_on_overlap"],
        default="prefer_part2",
    )
    args = parser.parse_args()
    return AggregateConfig(
        run_level_paths=tuple(args.run_level_paths),
        output_dir=args.output_dir,
        dedup_policy=args.dedup_policy,
    )


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    v = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    w = pd.to_numeric(weights, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(v) & np.isfinite(w) & (w > 0)
    if not np.any(mask):
        return float("nan")
    return float(np.average(v[mask], weights=w[mask]))


def load_and_dedup_run_features(paths: Sequence[Path], dedup_policy: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = [pd.read_csv(path) for path in paths]
    if not frames:
        return pd.DataFrame(), pd.DataFrame()
    union = pd.concat(frames, ignore_index=True)
    if "cohort_tag" not in union.columns:
        raise ValueError("Every run-level shift-feature CSV must carry a cohort_tag column.")
    # deduplicate_by_key (reused from merge_coma_cohort_results.py) breaks ties using
    # bundle_tag; we do not track a separate bundle per input file here, so use the
    # cohort_tag itself as the tie-break label.
    if "bundle_tag" not in union.columns:
        union["bundle_tag"] = union["cohort_tag"]
    # Dedup key must include coordinate: the same (subject, run, acq) contributes
    # one row per coordinate, and each is an independent dedup unit.
    union["run_key"] = build_run_key(union) + "|" + union["coordinate"].astype(str)
    deduped, duplicates = deduplicate_by_key(union, key_column="run_key", dedup_policy=dedup_policy)
    return deduped, duplicates


def aggregate_patient_coordinate_features(run_features: pd.DataFrame) -> pd.DataFrame:
    if run_features.empty:
        return pd.DataFrame()

    ok_rows = run_features[run_features["status"] == "ok"].copy()
    weight_cols = ["n_epochs_analyzed"]
    metric_cols = [
        "shift_rate_per_hour",
        "mean_shift_magnitude",
        "median_shift_magnitude",
        "mean_shift_quality",
        "median_shift_quality",
        "median_segment_length_epochs",
    ]

    rows: List[Dict[str, Any]] = []
    for (subject, coordinate), group in run_features.groupby(["subject", "coordinate"], dropna=False, sort=False):
        ok_group = group[group["status"] == "ok"]
        weights = pd.to_numeric(ok_group.get("n_epochs_analyzed", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
        row: Dict[str, Any] = {
            "subject": subject,
            "coordinate": coordinate,
            "n_runs_total": int(len(group)),
            "n_runs_ok": int(len(ok_group)),
            "n_epochs_analyzed_total": float(weights.sum()),
            "cpc": group["cpc"].dropna().iloc[0] if group["cpc"].notna().any() else np.nan,
            "hospital": group["hospital"].dropna().iloc[0] if "hospital" in group.columns and group["hospital"].notna().any() else None,
            "cohort_tags_present": ",".join(sorted(set(group["cohort_tag"].dropna().astype(str)))),
        }
        for metric in metric_cols:
            if metric not in ok_group.columns:
                row[metric] = np.nan
                continue
            row[metric] = weighted_mean(ok_group[metric], weights)
        rows.append(row)

    return pd.DataFrame(rows).sort_values(["subject", "coordinate"]).reset_index(drop=True)


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    deduped_run_features, duplicates = load_and_dedup_run_features(config.run_level_paths, config.dedup_policy)
    patient_features = aggregate_patient_coordinate_features(deduped_run_features)

    run_features_path = config.output_dir / "run_level_shift_features_combined.csv"
    patient_features_path = config.output_dir / "patient_coordinate_shift_features.csv"
    deduped_run_features.to_csv(run_features_path, index=False)
    patient_features.to_csv(patient_features_path, index=False)

    print(f"Wrote combined+deduped run-level shift features ({len(deduped_run_features)} rows) to {run_features_path}")
    print(f"Wrote patient x coordinate shift features ({len(patient_features)} rows) to {patient_features_path}")
    if not duplicates.empty:
        print(f"Dedup policy '{config.dedup_policy}' resolved {duplicates['run_key'].nunique()} overlapping (run, coordinate) keys.")
    if not patient_features.empty:
        print(f"Distinct patients: {patient_features['subject'].nunique()}")


if __name__ == "__main__":
    sys.exit(main())
