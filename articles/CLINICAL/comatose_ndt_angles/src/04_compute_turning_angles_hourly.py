"""Compute hour-resolved first-12h turning-angle features for I-CARE coma.

The pooled analysis averages each patient's trajectory over the first 12h.
This follow-up tests whether a localized CPC1-vs-CPC5 difference is diluted
by that averaging.  It uses the same globally pooled per-(chart, lag)
step-length thresholds as ``01_compute_turning_angles.py``, but never forms a
turning triple across an hourly boundary.

Output: one row per (run, hour_bin, chart, lag) in
``results/turning_angles_hourly/run_hour_level_turning_features.csv``.
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

import coma_angle_support as support
from merge_coma_cohort_results import build_run_key, deduplicate_by_key


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "turning_angles_hourly"
DEFAULT_EPOCH_SERIES_PATHS = (
    support.PHASE_SHIFT_RESULTS / "epoch_series_first12h_part1.parquet",
    support.PHASE_SHIFT_RESULTS / "epoch_series_first12h_part2.parquet",
)
N_HOURS = 12


@dataclass(frozen=True)
class Config:
    epoch_series_paths: Tuple[Path, ...]
    output_dir: Path
    dedup_policy: str
    n_perms: int
    workers: int
    limit_groups: int | None


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Compute hourly turning-angle features for the coma cohort.")
    parser.add_argument(
        "--epoch-series-path",
        dest="epoch_series_paths",
        type=Path,
        action="append",
        default=None,
        help="Repeatable; defaults to the part1 and part2 phase-shift epoch-series parquet files.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--dedup-policy",
        choices=["prefer_part2", "prefer_part1", "error_on_overlap"],
        default="prefer_part2",
    )
    parser.add_argument("--n-perms", type=int, default=support.N_PERMUTATIONS)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--limit-groups", type=int, default=None, help="Smoke-test: only process the first N runs.")
    args = parser.parse_args()
    return Config(
        epoch_series_paths=tuple(args.epoch_series_paths) if args.epoch_series_paths else DEFAULT_EPOCH_SERIES_PATHS,
        output_dir=args.output_dir,
        dedup_policy=args.dedup_policy,
        n_perms=max(0, int(args.n_perms)),
        workers=max(1, int(args.workers)),
        limit_groups=args.limit_groups,
    )


def load_and_dedup(config: Config) -> pd.DataFrame:
    """Load epoch series and resolve overlapping part1/part2 runs once."""
    epoch_table = support.load_epoch_series(config.epoch_series_paths)
    if epoch_table.empty:
        return epoch_table
    epoch_table["bundle_tag"] = epoch_table["cohort_tag"]
    run_index = epoch_table[["subject", "run", "acq", "cohort_tag", "bundle_tag"]].drop_duplicates(
        subset=["subject", "run", "acq", "cohort_tag"]
    )
    run_index["run_key"] = build_run_key(run_index)
    kept_runs, duplicates = deduplicate_by_key(run_index, key_column="run_key", dedup_policy=config.dedup_policy)
    if not duplicates.empty:
        print(f"Dedup policy '{config.dedup_policy}' resolved {duplicates['run_key'].nunique()} overlapping run keys.")

    keep = kept_runs[["subject", "run", "acq", "cohort_tag"]].copy()
    keep["__keep__"] = True
    out = epoch_table.merge(keep, on=["subject", "run", "acq", "cohort_tag"], how="inner")
    out = out.drop(columns="__keep__").reset_index(drop=True)
    del epoch_table, run_index, kept_runs, keep
    gc.collect()
    return out


def compute_pooled_step_thresholds(
    epoch_table: pd.DataFrame, charts: Dict[str, Tuple[str, ...]]
) -> Dict[Tuple[str, int], float]:
    """Compute global thresholds exactly once, across full 12h runs."""
    ordered = epoch_table.sort_values(["subject", "run", "acq", "epoch_idx"])
    grouped = ordered.groupby(["subject", "run", "acq"], sort=False)
    thresholds: Dict[Tuple[str, int], float] = {}
    for chart, columns in charts.items():
        for lag in support.LAGS:
            diffs = grouped[list(columns)].diff(periods=lag).to_numpy(dtype=float)
            norms = np.sqrt(np.square(diffs).sum(axis=1))
            finite = norms[np.isfinite(norms)]
            thresholds[(chart, lag)] = (
                float(np.percentile(finite, support.STEP_LENGTH_FILTER_PERCENTILE)) if finite.size else 0.0
            )
    return thresholds


def empty_feature_row(meta: Dict[str, Any], chart: str, lag: int, hour_bin: int, threshold: float) -> Dict[str, Any]:
    return {
        **meta,
        "hour_bin": hour_bin,
        "time_bin": f"{hour_bin}_{hour_bin + 1}h",
        "chart": chart,
        "lag_epochs": lag,
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


def process_run_group(
    run_group: pd.DataFrame,
    charts: Dict[str, Tuple[str, ...]],
    thresholds: Dict[Tuple[str, int], float],
    n_perms: int,
) -> List[Dict[str, Any]]:
    """Compute features independently in each occupied 1h bin of one run."""
    meta = {
        "subject": run_group["subject"].iloc[0],
        "run": run_group["run"].iloc[0],
        "acq": run_group["acq"].iloc[0],
        "cohort_tag": run_group["cohort_tag"].iloc[0],
        "cpc": run_group["cpc"].iloc[0],
        "hospital": run_group["hospital"].iloc[0],
    }
    rows: List[Dict[str, Any]] = []
    for hour_bin, hour_group in run_group.groupby("hour_bin", sort=True):
        ordered = hour_group.sort_values("epoch_idx")
        for chart, columns in charts.items():
            coords = ordered[list(columns)].to_numpy(dtype=float)
            for lag in support.LAGS:
                threshold = thresholds[(chart, lag)]
                triples = support.compute_turning_triples(coords, lag, step_length_threshold=threshold)
                if triples is None:
                    rows.append(empty_feature_row(meta, chart, lag, int(hour_bin), threshold))
                    continue

                theta = triples["theta_deg"]
                median_theta = float(np.median(theta))
                seed = support.stable_seed(meta["subject"], meta["run"], meta["acq"], int(hour_bin), chart, lag)
                z, null_mean, null_sd = support.permutation_null_z(
                    triples["disp_units"], median_theta, seed=seed, n_perms=n_perms
                )
                rows.append(
                    {
                        **meta,
                        "hour_bin": int(hour_bin),
                        "time_bin": f"{int(hour_bin)}_{int(hour_bin) + 1}h",
                        "chart": chart,
                        "lag_epochs": lag,
                        "status": "ok",
                        "n_valid": triples["n_valid"],
                        "n_excluded_short_step": triples["n_excluded_short_step"],
                        "n_total_triples": triples["n_total_triples"],
                        "turn_cos_mean": float(np.mean(triples["cos_theta"])),
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
    return rows


def build_hourly_feature_table(epoch_table: pd.DataFrame, config: Config) -> pd.DataFrame:
    if epoch_table.empty:
        return pd.DataFrame()
    charts = support.available_charts(epoch_table.columns)
    if not charts:
        raise RuntimeError("None of the configured charts are available in the epoch series.")

    epoch_table = epoch_table.copy()
    hour_values = np.floor(pd.to_numeric(epoch_table["t_hours_from_anchor"], errors="coerce")).to_numpy(dtype=float)
    epoch_table["hour_bin"] = hour_values
    epoch_table = epoch_table[
        np.isfinite(epoch_table["hour_bin"]) & epoch_table["hour_bin"].between(0, N_HOURS - 1)
    ].copy()
    epoch_table["hour_bin"] = epoch_table["hour_bin"].astype(int)

    run_columns = ["subject", "run", "acq"]
    if config.limit_groups is not None:
        run_keys = epoch_table[run_columns].drop_duplicates().head(config.limit_groups)
        epoch_table = epoch_table.merge(run_keys, on=run_columns, how="inner")

    n_runs = epoch_table.groupby(run_columns, dropna=False).ngroups
    print(f"Computing global step-length thresholds over {n_runs} full runs...")
    thresholds = compute_pooled_step_thresholds(epoch_table, charts)
    for (chart, lag), threshold in sorted(thresholds.items()):
        print(f"  threshold[{chart}, lag={lag}] = {threshold:.6g}")

    groups = [group for _, group in epoch_table.groupby(run_columns, dropna=False, sort=False)]
    rows: List[Dict[str, Any]] = []
    if config.workers <= 1 or len(groups) <= 1:
        for index, group in enumerate(groups, start=1):
            rows.extend(process_run_group(group, charts, thresholds, config.n_perms))
            if index % 200 == 0 or index == len(groups):
                print(f"Processed {index}/{len(groups)} runs.", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=config.workers) as executor:
            futures = [executor.submit(process_run_group, group, charts, thresholds, config.n_perms) for group in groups]
            for index, future in enumerate(futures, start=1):
                rows.extend(future.result())
                if index % 200 == 0 or index == len(futures):
                    print(f"Processed {index}/{len(futures)} runs.", flush=True)
    return pd.DataFrame(rows)


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    epoch_table = load_and_dedup(config)
    features = build_hourly_feature_table(epoch_table, config)
    output_path = config.output_dir / "run_hour_level_turning_features.csv"
    features.to_csv(output_path, index=False)
    print(f"Wrote {len(features)} run x hour x chart x lag turning-feature rows to {output_path}")
    if not features.empty:
        print("Status counts:", features["status"].value_counts(dropna=False).to_dict())


if __name__ == "__main__":
    sys.exit(main())
