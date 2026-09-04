from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd

from parkinson_trajectory_support import (
    DATASET_ROOT,
    DIMENSIONS,
    EVENT_METRIC_DIR,
    MANIFEST_JSON,
    MIN_SEGMENT_POINTS,
    POST_EVENT_WINDOWS,
    PRE_EVENT_WINDOWS,
    PRIMARY_COORDINATE_CONTRACT,
    RUN_METRICS_CSV,
    SUBJECT_METRICS_CSV,
    LoadedRun,
    SpaceKey,
    aggregate_metric_rows,
    build_reference_model,
    ensure_dir,
    load_run,
    sample_evenly,
    summarize_segment_metrics,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute exploratory event-locked Parkinson trajectory metrics for ds003490."
    )
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--output-dir", type=Path, default=EVENT_METRIC_DIR)
    parser.add_argument("--coordinate-contract", type=str, default=PRIMARY_COORDINATE_CONTRACT)
    parser.add_argument("--pre-event-windows", type=int, default=PRE_EVENT_WINDOWS)
    parser.add_argument("--post-event-windows", type=int, default=POST_EVENT_WINDOWS)
    parser.add_argument("--limit-h5", type=int, default=None)
    return parser.parse_args()


def iter_h5_paths(dataset_root: Path, *, limit_h5: int | None = None) -> list[Path]:
    h5_paths = sorted(dataset_root.glob("sub-*/sub-*.h5"))
    if limit_h5 is not None:
        h5_paths = h5_paths[: int(limit_h5)]
    return h5_paths


def load_runs(
    dataset_root: Path,
    *,
    coordinate_contract: str,
    limit_h5: int | None = None,
) -> list[LoadedRun]:
    runs: list[LoadedRun] = []
    for h5_path in iter_h5_paths(dataset_root, limit_h5=limit_h5):
        with h5py.File(h5_path, "r") as handle:
            runs.append(load_run(handle, h5_path, coordinate_contract=coordinate_contract))
    return runs


def analysis_type_for_key(key: SpaceKey) -> str:
    return f"{key.level}_event_locked_trajectory_{key.dim}d"


def trimmed_indices(block: np.ndarray, n_points: int) -> np.ndarray:
    block = np.asarray(block, dtype=int).reshape(-1)
    keep = block[(block >= 0) & (block < n_points)]
    return keep


def build_local_window(
    block: np.ndarray,
    *,
    n_points: int,
    pre_windows: int,
    post_windows: int,
) -> tuple[int, int, np.ndarray]:
    start = max(0, int(block[0]) - int(pre_windows))
    end = min(n_points - 1, int(block[-1]) + int(post_windows))
    local_block = np.arange(int(block[0]) - start, int(block[-1]) - start + 1, dtype=int)
    return start, end, local_block


def gather_reference_segments(runs: list[LoadedRun]) -> dict[SpaceKey, list[np.ndarray]]:
    sampled_by_key: dict[SpaceKey, list[np.ndarray]] = defaultdict(list)
    for run in runs:
        for key, payload in run.spaces.items():
            coords = np.asarray(payload["coords"], dtype=float)
            n_points = min(coords.shape[0], run.time.shape[0])
            if n_points < MIN_SEGMENT_POINTS:
                continue
            coords = coords[:n_points]
            for blocks in run.event_blocks.values():
                for block in blocks:
                    keep = trimmed_indices(block, n_points)
                    if keep.size == 0:
                        continue
                    start, end, _ = build_local_window(
                        keep,
                        n_points=n_points,
                        pre_windows=PRE_EVENT_WINDOWS,
                        post_windows=POST_EVENT_WINDOWS,
                    )
                    segment = coords[start : end + 1]
                    if segment.shape[0] >= MIN_SEGMENT_POINTS:
                        sampled_by_key[key].append(sample_evenly(segment, 64))
            for blocks in run.stage_blocks.values():
                for block in blocks:
                    keep = trimmed_indices(block, n_points)
                    if keep.size < MIN_SEGMENT_POINTS:
                        continue
                    segment = coords[int(keep[0]) : int(keep[-1]) + 1]
                    if segment.shape[0] >= MIN_SEGMENT_POINTS:
                        sampled_by_key[key].append(sample_evenly(segment, 64))
    return sampled_by_key


def build_run_metric_rows(
    runs: list[LoadedRun],
    *,
    references: dict[SpaceKey, dict[str, Any]],
    pre_windows: int,
    post_windows: int,
) -> list[dict[str, Any]]:
    run_rows: list[dict[str, Any]] = []
    for run in runs:
        for key, payload in run.spaces.items():
            coords = np.asarray(payload["coords"], dtype=float)
            n_points = min(coords.shape[0], run.time.shape[0])
            if n_points < MIN_SEGMENT_POINTS:
                continue
            coords = coords[:n_points]
            time = run.time[:n_points]
            reference = references.get(key) or {}
            metric_diag = reference.get("metric_diag")
            model = reference.get("model")
            n_states = reference.get("n_states")

            for segment_label, blocks in run.stage_blocks.items():
                metric_rows: list[dict[str, Any]] = []
                for block in blocks:
                    keep = trimmed_indices(block, n_points)
                    if keep.size < MIN_SEGMENT_POINTS:
                        continue
                    segment_coords = coords[int(keep[0]) : int(keep[-1]) + 1]
                    segment_time = time[int(keep[0]) : int(keep[-1]) + 1]
                    metrics = summarize_segment_metrics(
                        segment_coords,
                        segment_time,
                        metric_diag=metric_diag,
                        model=model,
                        n_states=n_states,
                    )
                    metric_rows.append(
                        {
                            **run.metadata,
                            "analysis_type": analysis_type_for_key(key),
                            "level": key.level,
                            "network": key.network,
                            "dims": int(key.dim),
                            "segment_kind": "baseline",
                            "segment_label": segment_label,
                            "source_dataset_path": payload["source_dataset_path"],
                            "requested_coordinate_contract": run.metadata.get("requested_coordinate_contract"),
                            "resolved_coordinate_contract": payload.get(
                                "resolved_coordinate_contract",
                                run.metadata.get("resolved_coordinate_contract"),
                            ),
                            "segment_points": int(segment_coords.shape[0]),
                            "event_windows": 0,
                            "segment_duration_sec": float(segment_time[-1] - segment_time[0]) if segment_time.size >= 2 else 0.0,
                            **metrics,
                        }
                    )
                aggregated = aggregate_metric_rows(metric_rows)
                if aggregated:
                    run_rows.append(aggregated)

            for segment_label, blocks in run.event_blocks.items():
                metric_rows = []
                for block in blocks:
                    keep = trimmed_indices(block, n_points)
                    if keep.size == 0:
                        continue
                    start, end, local_block = build_local_window(
                        keep,
                        n_points=n_points,
                        pre_windows=pre_windows,
                        post_windows=post_windows,
                    )
                    segment_coords = coords[start : end + 1]
                    segment_time = time[start : end + 1]
                    if segment_coords.shape[0] < MIN_SEGMENT_POINTS:
                        continue
                    metrics = summarize_segment_metrics(
                        segment_coords,
                        segment_time,
                        metric_diag=metric_diag,
                        model=model,
                        n_states=n_states,
                        event_block=local_block,
                    )
                    metric_rows.append(
                        {
                            **run.metadata,
                            "analysis_type": analysis_type_for_key(key),
                            "level": key.level,
                            "network": key.network,
                            "dims": int(key.dim),
                            "segment_kind": "event",
                            "segment_label": segment_label,
                            "source_dataset_path": payload["source_dataset_path"],
                            "requested_coordinate_contract": run.metadata.get("requested_coordinate_contract"),
                            "resolved_coordinate_contract": payload.get(
                                "resolved_coordinate_contract",
                                run.metadata.get("resolved_coordinate_contract"),
                            ),
                            "segment_points": int(segment_coords.shape[0]),
                            "event_windows": int(keep.size),
                            "segment_duration_sec": float(segment_time[-1] - segment_time[0]) if segment_time.size >= 2 else 0.0,
                            **metrics,
                        }
                    )
                aggregated = aggregate_metric_rows(metric_rows)
                if aggregated:
                    run_rows.append(aggregated)
    return run_rows


def aggregate_subject_metrics(run_frame: pd.DataFrame) -> pd.DataFrame:
    if run_frame.empty:
        return pd.DataFrame()
    group_cols = [
        "dataset_id",
        "subject_id",
        "group",
        "condition",
        "task",
        "session",
        "analysis_type",
        "level",
        "network",
        "dims",
        "segment_kind",
        "segment_label",
        "requested_coordinate_contract",
        "resolved_coordinate_contract",
    ]
    agg_map: dict[str, Any] = {
        metric: "median" for metric in run_frame.columns if metric in {"n_blocks", *run_frame.columns.intersection(set())}
    }
    for metric in (
        "n_blocks",
        "segment_points_median",
        "event_windows_median",
        "segment_duration_sec_median",
    ):
        if metric in run_frame.columns:
            agg_map[metric] = "median"
    for metric in run_frame.columns:
        if metric in {
            "speed_median",
            "curvature_median",
            "tortuosity",
            "path_length",
            "peak_displacement",
            "recovery_residual",
            "hysteresis_area_md",
            "hysteresis_area_me",
            "hysteresis_area_de",
            "hysteresis_area_mean",
            "entropy_rate",
            "irreversibility",
            "entropy_production",
            "self_loop_rate",
            "transition_sparsity",
            "noetic_action",
            "noetic_action_kinetic",
            "noetic_action_jerk",
            "noetic_action_potential",
        }:
            agg_map[metric] = "median"
    subject_frame = (
        run_frame.groupby(group_cols, as_index=False, dropna=False)
        .agg(
            **{metric: (metric, agg) for metric, agg in agg_map.items()},
            run_support=("source_h5_path", "nunique"),
        )
        .sort_values(["subject_id", "analysis_type", "segment_label", "network"])
        .reset_index(drop=True)
    )
    return subject_frame


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)
    runs = load_runs(
        args.dataset_root,
        coordinate_contract=str(args.coordinate_contract),
        limit_h5=args.limit_h5,
    )
    if not runs:
        raise RuntimeError(f"No H5 files were found under {args.dataset_root}.")

    sampled_by_key = gather_reference_segments(runs)
    references = {
        key: build_reference_model(blocks, dim=key.dim)
        for key, blocks in sampled_by_key.items()
    }
    run_rows = build_run_metric_rows(
        runs,
        references=references,
        pre_windows=int(args.pre_event_windows),
        post_windows=int(args.post_event_windows),
    )
    run_frame = pd.DataFrame(run_rows).sort_values(
        ["analysis_type", "segment_kind", "segment_label", "group", "condition", "subject_id", "network"]
    )
    subject_frame = aggregate_subject_metrics(run_frame)
    run_frame.to_csv(args.output_dir / RUN_METRICS_CSV, index=False)
    subject_frame.to_csv(args.output_dir / SUBJECT_METRICS_CSV, index=False)

    reference_manifest = {
        f"{key.level}:{key.network}:{key.dim}d": {
            "n_fit_blocks": int(len(sampled_by_key.get(key, []))),
            "n_fit_points": int((references.get(key) or {}).get("n_fit_points") or 0),
            "n_states": (references.get(key) or {}).get("n_states"),
        }
        for key in sorted(references.keys(), key=lambda item: (item.level, item.network, item.dim))
    }
    manifest = {
        "dataset_root": str(args.dataset_root),
        "coordinate_contract": str(args.coordinate_contract),
        "pre_event_windows": int(args.pre_event_windows),
        "post_event_windows": int(args.post_event_windows),
        "n_input_runs": int(len(runs)),
        "n_run_metric_rows": int(len(run_frame)),
        "n_subject_metric_rows": int(len(subject_frame)),
        "segment_labels": sorted(run_frame["segment_label"].dropna().unique().tolist()) if not run_frame.empty else [],
        "analysis_types": sorted(run_frame["analysis_type"].dropna().unique().tolist()) if not run_frame.empty else [],
        "reference_models": reference_manifest,
    }
    write_json(args.output_dir / MANIFEST_JSON, manifest)


if __name__ == "__main__":
    main()
