"""Compute three-point turning-angle geometry features on the coma cohort.

Input: the ``epoch_series_first12h_<cohort_tag>.parquet`` files already
produced by the sibling ``comatose_ndt_first12h_phase_shift`` pipeline's
``01_extract_epoch_series.py`` (no H5 re-extraction here - see
``coma_angle_support.py`` docstring for why that is a valid reuse).

For every (subject, run, acq) group and every (chart, lag) in
``coma_angle_support.CHARTS`` x ``coma_angle_support.LAGS``, this script:

1. Computes elementary lag-``lag`` displacement vectors, pooled across the
   whole deduped cohort, to get a per-(chart, lag) 10th-percentile
   step-length threshold (plan.md section 5).
2. Computes three-point turning-angle triples per run, excluding triples
   with either adjacent step below that pooled threshold.
3. Summarizes: turn_cos_mean, turn_angle_median, turn_angle_mad,
   turn_angle_iqr, turn_angle_p90, turn_fraction_gt_90,
   turn_fraction_gt_120, turn_entropy, turn_length_coupling.
4. Runs a within-run displacement-permutation null (plan.md section 7) and
   reports a Z-score for the observed vs. null median turning angle.

Output: ``run_level_turning_features.csv`` (one row per run x chart x lag)
plus a QC CSV of skipped/insufficient groups.
"""

from __future__ import annotations

import argparse
import gc
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

import coma_angle_support as support  # noqa: E402
from merge_coma_cohort_results import build_run_key, deduplicate_by_key  # noqa: E402


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "turning_angles"
DEFAULT_EPOCH_SERIES_PATHS = (
    support.PHASE_SHIFT_RESULTS / "epoch_series_first12h_part1.parquet",
    support.PHASE_SHIFT_RESULTS / "epoch_series_first12h_part2.parquet",
)


@dataclass(frozen=True)
class Config:
    epoch_series_paths: Tuple[Path, ...]
    output_dir: Path
    dedup_policy: str
    n_perms: int
    workers: int
    limit_groups: int | None


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Compute turning-angle geometry features for the coma cohort.")
    parser.add_argument(
        "--epoch-series-path",
        dest="epoch_series_paths",
        type=Path,
        action="append",
        default=None,
        help="Repeatable. Defaults to both part1/part2 epoch-series parquet files from the phase-shift pipeline.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--dedup-policy", type=str, choices=["prefer_part2", "prefer_part1", "error_on_overlap"], default="prefer_part2"
    )
    parser.add_argument("--n-perms", type=int, default=support.N_PERMUTATIONS)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--limit-groups", type=int, default=None, help="Smoke-test: only process the first N (subject,run,acq) groups.")
    args = parser.parse_args()
    paths = tuple(args.epoch_series_paths) if args.epoch_series_paths else DEFAULT_EPOCH_SERIES_PATHS
    return Config(
        epoch_series_paths=paths,
        output_dir=args.output_dir,
        dedup_policy=args.dedup_policy,
        n_perms=int(args.n_perms),
        workers=max(1, int(args.workers)),
        limit_groups=args.limit_groups,
    )


def load_and_dedup(config: Config) -> pd.DataFrame:
    """Load epoch series and dedup at the (subject, run, acq) level.

    Dedup is computed on a one-row-per-run index (not the full per-epoch
    table, which would apply string ops to millions of rows for no benefit)
    and then used to filter the per-epoch table down to the surviving runs.
    """
    epoch_table = support.load_epoch_series(config.epoch_series_paths)
    if epoch_table.empty:
        return epoch_table
    if "bundle_tag" not in epoch_table.columns:
        epoch_table["bundle_tag"] = epoch_table["cohort_tag"]

    run_index = epoch_table[["subject", "run", "acq", "cohort_tag", "bundle_tag"]].drop_duplicates(
        subset=["subject", "run", "acq", "cohort_tag"]
    ).reset_index(drop=True)
    run_index["run_key"] = build_run_key(run_index)
    deduped_runs, duplicates = deduplicate_by_key(run_index, key_column="run_key", dedup_policy=config.dedup_policy)
    if not duplicates.empty:
        print(f"Dedup policy '{config.dedup_policy}' resolved {duplicates['run_key'].nunique()} overlapping run keys.")

    keep = deduped_runs[["subject", "run", "acq", "cohort_tag"]].copy()
    keep["__keep__"] = True
    merged = epoch_table.merge(keep, on=["subject", "run", "acq", "cohort_tag"], how="inner")
    merged = merged.drop(columns="__keep__").reset_index(drop=True)
    del epoch_table, keep, run_index, deduped_runs
    gc.collect()
    return merged


def compute_pooled_step_thresholds(
    epoch_table: pd.DataFrame, charts: Dict[str, Tuple[str, ...]]
) -> Dict[Tuple[str, int], float]:
    """Pooled 10th-percentile step-length threshold per (chart, lag).

    Vectorized via ``groupby(...).diff(periods=lag)`` across the whole table
    at once (correctly reset at (subject, run, acq) group boundaries),
    rather than looping in Python over thousands of run groups - this is the
    dominant cost of stage 1 on the full cohort, so it needs to run at
    pandas/C speed, not per-group Python speed.
    """
    sorted_table = epoch_table.sort_values(["subject", "run", "acq", "epoch_idx"])
    grouped = sorted_table.groupby(["subject", "run", "acq"], sort=False)

    thresholds: Dict[Tuple[str, int], float] = {}
    for chart_name, columns in charts.items():
        for lag in support.LAGS:
            diffs = grouped[list(columns)].diff(periods=lag)
            norms = np.sqrt(np.square(diffs.to_numpy(dtype=float)).sum(axis=1))
            finite = norms[np.isfinite(norms)]
            thresholds[(chart_name, lag)] = (
                float(np.percentile(finite, support.STEP_LENGTH_FILTER_PERCENTILE)) if finite.size else 0.0
            )
    return thresholds


def process_run_group(
    group: pd.DataFrame,
    charts: Dict[str, Tuple[str, ...]],
    thresholds: Dict[Tuple[str, int], float],
    n_perms: int,
) -> List[Dict[str, Any]]:
    meta = {
        "subject": group["subject"].iloc[0],
        "run": group["run"].iloc[0],
        "acq": group["acq"].iloc[0],
        "cohort_tag": group["cohort_tag"].iloc[0] if "cohort_tag" in group.columns else None,
        "cpc": group["cpc"].iloc[0] if "cpc" in group.columns else np.nan,
        "hospital": group["hospital"].iloc[0] if "hospital" in group.columns else None,
    }
    ordered = group.sort_values("epoch_idx")
    rows: List[Dict[str, Any]] = []

    for chart_name, columns in charts.items():
        coords = ordered[list(columns)].to_numpy(dtype=float)
        for lag in support.LAGS:
            row = dict(meta)
            row["chart"] = chart_name
            row["lag_epochs"] = lag
            threshold = thresholds.get((chart_name, lag), 0.0)
            triples = support.compute_turning_triples(coords, lag, step_length_threshold=threshold)
            if triples is None:
                row.update(
                    {
                        "status": "insufficient_valid_angles",
                        "n_valid": np.nan,
                        "n_excluded_short_step": np.nan,
                        "n_total_triples": np.nan,
                        "turn_cos_mean": np.nan,
                        "turn_angle_median": np.nan,
                        "turn_angle_mad": np.nan,
                        "turn_angle_iqr": np.nan,
                        "turn_angle_p90": np.nan,
                        "turn_fraction_gt_90": np.nan,
                        "turn_fraction_gt_120": np.nan,
                        "turn_entropy": np.nan,
                        "turn_length_coupling": np.nan,
                        "null_z_median_angle": np.nan,
                        "null_mean_median_angle": np.nan,
                        "null_sd_median_angle": np.nan,
                        "step_length_threshold": threshold,
                    }
                )
                rows.append(row)
                continue

            theta = triples["theta_deg"]
            cos_theta = triples["cos_theta"]
            median_theta = float(np.median(theta))
            seed = support.stable_seed(meta["subject"], meta["run"], meta["acq"], chart_name, lag)
            z, null_mean, null_sd = support.permutation_null_z(
                triples["disp_units"], median_theta, seed=seed, n_perms=n_perms
            )

            row.update(
                {
                    "status": "ok",
                    "n_valid": triples["n_valid"],
                    "n_excluded_short_step": triples["n_excluded_short_step"],
                    "n_total_triples": triples["n_total_triples"],
                    "turn_cos_mean": float(np.mean(cos_theta)),
                    "turn_angle_median": median_theta,
                    "turn_angle_mad": float(np.median(np.abs(theta - median_theta))),
                    "turn_angle_iqr": float(np.percentile(theta, 75) - np.percentile(theta, 25)),
                    "turn_angle_p90": float(np.percentile(theta, 90)),
                    "turn_fraction_gt_90": float(np.mean(theta > 90.0)),
                    "turn_fraction_gt_120": float(np.mean(theta > 120.0)),
                    "turn_entropy": support.angle_entropy(theta),
                    "turn_length_coupling": support.turn_length_coupling(theta, triples["mean_step_length"]),
                    "null_z_median_angle": z,
                    "null_mean_median_angle": null_mean,
                    "null_sd_median_angle": null_sd,
                    "step_length_threshold": threshold,
                }
            )
            rows.append(row)
    return rows


def build_turning_feature_table(epoch_table: pd.DataFrame, config: Config) -> pd.DataFrame:
    if epoch_table.empty:
        return pd.DataFrame()

    charts = support.available_charts(epoch_table.columns)
    if not charts:
        raise RuntimeError("None of the configured charts have all required columns in the epoch series.")

    group_columns = ["subject", "run", "acq"]
    if config.limit_groups is not None:
        run_keys = epoch_table[group_columns].drop_duplicates().head(config.limit_groups)
        epoch_table = epoch_table.merge(run_keys, on=group_columns, how="inner")

    print(f"Computing pooled step-length thresholds over {epoch_table.groupby(group_columns, dropna=False).ngroups} runs...")
    thresholds = compute_pooled_step_thresholds(epoch_table, charts)
    for (chart_name, lag), value in sorted(thresholds.items()):
        print(f"  threshold[{chart_name}, lag={lag}] = {value:.6g}")

    groups = [group for _, group in epoch_table.groupby(group_columns, dropna=False, sort=False)]

    rows: List[Dict[str, Any]] = []
    if config.workers <= 1 or len(groups) <= 1:
        for idx, group in enumerate(groups, start=1):
            rows.extend(process_run_group(group, charts, thresholds, config.n_perms))
            if idx % 200 == 0 or idx == len(groups):
                print(f"Processed {idx}/{len(groups)} runs.", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=config.workers) as executor:
            futures = [executor.submit(process_run_group, group, charts, thresholds, config.n_perms) for group in groups]
            for idx, future in enumerate(futures, start=1):
                rows.extend(future.result())
                if idx % 200 == 0 or idx == len(futures):
                    print(f"Processed {idx}/{len(futures)} runs.", flush=True)
    return pd.DataFrame(rows)


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    epoch_table = load_and_dedup(config)
    feature_table = build_turning_feature_table(epoch_table, config)

    output_path = config.output_dir / "run_level_turning_features.csv"
    feature_table.to_csv(output_path, index=False)

    print(f"Wrote {len(feature_table)} run x chart x lag turning-feature rows to {output_path}")
    if not feature_table.empty:
        print("Status counts:", feature_table["status"].value_counts(dropna=False).to_dict())


if __name__ == "__main__":
    sys.exit(main())
