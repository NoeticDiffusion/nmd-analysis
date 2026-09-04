from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
COMA_SRC_DIR = ARTICLE_DIR.parent / "comatose_ndt" / "src"
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
if str(COMA_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(COMA_SRC_DIR))
if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from icare_patient_timeline_analysis import (  # noqa: E402
    AnalysisConfig,
    PRIMARY_12H_TIME_BINS_HOURS,
    build_patient_bin_summary,
    build_run_table,
    build_subject_outcome_index,
)
from ndt_analysis.h5_contract import read_run_contract, resolve_coords_3d, resolve_coords_9d  # noqa: E402

from trajectory_support import (  # noqa: E402
    ACTION_JERK_WEIGHT,
    ACTION_POTENTIAL_WEIGHT,
    ALL_METRICS,
    ANALYSIS_TYPE_BY_DIM,
    ARTICLE_FACING_METRICS,
    DIMENSIONS,
    EPS,
    GOOD_CPC,
    MANIFEST_JSON,
    MAX_CODEBOOK_POINTS_BY_DIM,
    MAX_POINTS_PER_RUN_FOR_FIT_BY_DIM,
    MIN_POINTS_PER_RUN,
    MIN_TRANSITIONS_PER_RUN,
    PATIENT_TIMEBIN_METRICS_CSV,
    POOR_CPC,
    PRIMARY_COORDINATE_CONTRACT,
    PRIMARY_TIME_BIN,
    RAW_WFDB_ROOT,
    REPERTOIRE_STATES_BY_DIM,
    RNG_SEED,
    RUN_LEVEL_METRICS_CSV,
    stable_variance_metric,
    potential_from_coords,
    resolve_metric_dir,
    resolve_part_root,
    resolve_timeline_dir,
    ensure_dir,
    write_json,
)


@dataclass(frozen=True)
class Config:
    part: str
    processed_root: Path
    raw_root: Path
    timeline_dir: Path
    output_dir: Path
    coordinate_contract: str
    primary_time_bin: str
    limit_h5: int | None
    dims: tuple[int, ...]


def parse_dims(raw_dims: str) -> tuple[int, ...]:
    dims: list[int] = []
    for token in str(raw_dims).split(","):
        token = token.strip()
        if not token:
            continue
        try:
            dim = int(token)
        except ValueError as exc:
            raise ValueError(f"Invalid dimension token {token!r}. Expected comma-separated integers.") from exc
        if dim not in DIMENSIONS:
            raise ValueError(f"Unsupported dimension {dim}. Expected one of {DIMENSIONS}.")
        if dim not in dims:
            dims.append(dim)
    if not dims:
        raise ValueError("At least one analysis dimension must be requested.")
    return tuple(dims)


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description=(
            "Compute exploratory trajectory/repertoire metrics for the I-CARE coma cohort "
            "using subject-anchored 3D and 9D MNPS trajectories."
        )
    )
    parser.add_argument("--part", choices=("part1", "part2"), default="part1")
    parser.add_argument("--processed-root", type=Path, default=None)
    parser.add_argument("--raw-root", type=Path, default=RAW_WFDB_ROOT)
    parser.add_argument("--timeline-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--coordinate-contract", type=str, default=PRIMARY_COORDINATE_CONTRACT)
    parser.add_argument("--primary-time-bin", type=str, default=PRIMARY_TIME_BIN)
    parser.add_argument("--limit-h5", type=int, default=None)
    parser.add_argument("--dims", type=str, default="3,9")
    args = parser.parse_args()
    part = str(args.part)
    processed_root = args.processed_root or resolve_part_root(part)
    timeline_dir = args.timeline_dir or resolve_timeline_dir(part)
    output_dir = args.output_dir or resolve_metric_dir(part)
    return Config(
        part=part,
        processed_root=processed_root,
        raw_root=args.raw_root,
        timeline_dir=timeline_dir,
        output_dir=output_dir,
        coordinate_contract=str(args.coordinate_contract),
        primary_time_bin=str(args.primary_time_bin),
        limit_h5=args.limit_h5,
        dims=parse_dims(args.dims),
    )


def ensure_timeline_outputs(config: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    run_path = config.timeline_dir / "run_timing_metadata.csv"
    patient_path = config.timeline_dir / "patient_timebin_summaries.csv"
    subject_path = config.timeline_dir / "subject_outcome_index.csv"
    if run_path.exists() and patient_path.exists():
        run_table = pd.read_csv(run_path, low_memory=False)
        patient_table = pd.read_csv(patient_path, low_memory=False)
        return run_table, patient_table

    ensure_dir(config.timeline_dir)
    timeline_config = AnalysisConfig(
        processed_root=config.processed_root,
        raw_root=config.raw_root,
        output_dir=config.timeline_dir,
        coordinate_contract=config.coordinate_contract,
        time_bins_hours=PRIMARY_12H_TIME_BINS_HOURS,
        time_bin_scheme="primary_12h",
        limit_h5=config.limit_h5,
    )
    run_table = build_run_table(timeline_config)
    patient_table = build_patient_bin_summary(run_table)
    subject_table = build_subject_outcome_index(run_table)
    run_table.to_csv(run_path, index=False)
    patient_table.to_csv(patient_path, index=False)
    subject_table.to_csv(subject_path, index=False)
    return run_table, patient_table


def filtered_run_table(run_table: pd.DataFrame, *, primary_time_bin: str) -> pd.DataFrame:
    frame = run_table.copy()
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[
        (frame["time_bin"] == primary_time_bin)
        & (frame["cpc_numeric"].isin([float(GOOD_CPC), float(POOR_CPC)]))
    ].copy()
    frame["label"] = np.where(frame["cpc_numeric"] == float(GOOD_CPC), 1, 0)
    frame["label_name"] = np.where(frame["label"] == 1, "CPC1", "CPC5")
    frame["processed_h5_path"] = frame["processed_h5_path"].astype(str)
    frame = frame[frame["processed_h5_path"].map(lambda value: Path(value).exists())].copy()
    return frame.sort_values(["subject", "run_start_from_anchor_sec", "run", "acq"]).reset_index(drop=True)


def read_run_coords(run_row: pd.Series, *, dim: int, coordinate_contract: str) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    path = Path(str(run_row["processed_h5_path"]))
    if not path.exists():
        return np.empty((0, dim)), np.empty(0), {}
    with h5py.File(path, "r") as h5:
        resolved = resolve_coords_3d(h5, coordinate_contract) if dim == 3 else resolve_coords_9d(h5, coordinate_contract)
        if resolved is None:
            return np.empty((0, dim)), np.empty(0), read_run_contract(h5).provenance()
        coords = np.asarray(resolved.values, dtype=float)
        if "time" in h5:
            time = np.asarray(h5["time"][:], dtype=float)
        elif "window_start" in h5 and "window_end" in h5:
            starts = np.asarray(h5["window_start"][:], dtype=float)
            ends = np.asarray(h5["window_end"][:], dtype=float)
            time = 0.5 * (starts + ends)
        else:
            time = np.arange(coords.shape[0], dtype=float)
        provenance = resolved.provenance() | {"values_path": resolved.values_path}

    limit = min(len(coords), len(time))
    coords = coords[:limit, :dim]
    time = time[:limit]
    finite_mask = np.isfinite(time) & np.isfinite(coords).all(axis=1)
    coords = coords[finite_mask]
    time = time[finite_mask]
    return coords, time, provenance


def sample_evenly(coords: np.ndarray, max_points: int) -> np.ndarray:
    if len(coords) <= max_points:
        return coords
    indices = np.linspace(0, len(coords) - 1, num=max_points, dtype=int)
    return coords[indices]


def fit_codebook(run_table: pd.DataFrame, *, dim: int, coordinate_contract: str) -> tuple[MiniBatchKMeans, np.ndarray, dict[str, Any]]:
    sampled_blocks: list[np.ndarray] = []
    skipped_runs = 0
    for _, run_row in run_table.iterrows():
        coords, _, _ = read_run_coords(run_row, dim=dim, coordinate_contract=coordinate_contract)
        if len(coords) < MIN_POINTS_PER_RUN:
            skipped_runs += 1
            continue
        sampled_blocks.append(sample_evenly(coords, MAX_POINTS_PER_RUN_FOR_FIT_BY_DIM[dim]))
    if not sampled_blocks:
        raise RuntimeError(f"No usable {dim}D trajectories were available for codebook fitting.")
    sampled = np.concatenate(sampled_blocks, axis=0)
    sampled = sample_evenly(sampled, MAX_CODEBOOK_POINTS_BY_DIM[dim])
    model = MiniBatchKMeans(
        n_clusters=REPERTOIRE_STATES_BY_DIM[dim],
        random_state=RNG_SEED + dim,
        n_init=10,
        batch_size=min(4096, max(512, len(sampled))),
        reassignment_ratio=0.01,
    )
    model.fit(sampled)
    metric_diag = stable_variance_metric(sampled)
    manifest = {
        "n_fit_points": int(len(sampled)),
        "n_fit_runs": int(len(sampled_blocks)),
        "n_skipped_runs": int(skipped_runs),
        "n_clusters": int(REPERTOIRE_STATES_BY_DIM[dim]),
        "metric_diag": metric_diag.tolist(),
    }
    return model, metric_diag, manifest


def repertoire_metrics(states: np.ndarray, *, n_states: int) -> dict[str, float]:
    states = np.asarray(states, dtype=int).reshape(-1)
    if len(states) < (MIN_TRANSITIONS_PER_RUN + 1):
        return {metric: float("nan") for metric in ("entropy_rate", "irreversibility", "entropy_production", "self_loop_rate", "transition_sparsity")}
    transition_counts = np.zeros((n_states, n_states), dtype=float)
    for src, dst in zip(states[:-1], states[1:], strict=False):
        transition_counts[int(src), int(dst)] += 1.0
    occupancy = np.bincount(states, minlength=n_states).astype(float)
    if occupancy.sum() <= 0:
        return {metric: float("nan") for metric in ("entropy_rate", "irreversibility", "entropy_production", "self_loop_rate", "transition_sparsity")}
    pi = occupancy / occupancy.sum()
    row_sums = transition_counts.sum(axis=1, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        P = np.divide(transition_counts, row_sums, out=np.zeros_like(transition_counts), where=row_sums > 0)
    entropy_rate = -np.sum(pi[:, None] * P * np.log(P + EPS))
    flow = pi[:, None] * P
    irreversibility = 0.5 * np.sum(np.abs(flow - flow.T))
    entropy_production = np.sum(flow * np.log((flow + EPS) / (flow.T + EPS)))
    self_loop_rate = float(np.sum(pi * np.diag(P)))
    transition_sparsity = float(1.0 - (np.count_nonzero(transition_counts) / transition_counts.size))
    return {
        "entropy_rate": float(entropy_rate),
        "irreversibility": float(irreversibility),
        "entropy_production": float(entropy_production),
        "self_loop_rate": self_loop_rate,
        "transition_sparsity": transition_sparsity,
    }


def weighted_quad(vecs: np.ndarray, metric_diag: np.ndarray) -> np.ndarray:
    return np.sum((vecs * vecs) * metric_diag[None, :], axis=1)


def noetic_action_metrics(coords: np.ndarray, time: np.ndarray, *, metric_diag: np.ndarray) -> dict[str, float]:
    coords = np.asarray(coords, dtype=float)
    time = np.asarray(time, dtype=float)
    if len(coords) < 3 or len(time) < 3:
        return {
            "noetic_action": float("nan"),
            "noetic_action_kinetic": float("nan"),
            "noetic_action_jerk": float("nan"),
            "noetic_action_potential": float("nan"),
        }

    dt_prev = time[1:-1] - time[:-2]
    dt_next = time[2:] - time[1:-1]
    valid = np.isfinite(dt_prev) & np.isfinite(dt_next) & (dt_prev > 0) & (dt_next > 0)
    if not valid.any():
        return {
            "noetic_action": float("nan"),
            "noetic_action_kinetic": float("nan"),
            "noetic_action_jerk": float("nan"),
            "noetic_action_potential": float("nan"),
        }

    delta = coords[2:] - coords[1:-1]
    delta2 = coords[2:] - 2.0 * coords[1:-1] + coords[:-2]
    dt_center = 0.5 * (dt_prev + dt_next)
    potential = potential_from_coords(coords[1:-1])

    delta = delta[valid]
    delta2 = delta2[valid]
    dt_next = dt_next[valid]
    dt_center = dt_center[valid]
    potential = potential[valid]

    kinetic_density = 0.5 * weighted_quad(delta, metric_diag) / np.maximum(dt_next, EPS) ** 2
    jerk_density = ACTION_JERK_WEIGHT * weighted_quad(delta2, metric_diag) / np.maximum(dt_center, EPS) ** 4
    potential_density = ACTION_POTENTIAL_WEIGHT * potential
    total_density = kinetic_density + jerk_density + potential_density

    def _median(values: np.ndarray) -> float:
        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]
        return float(np.median(values)) if values.size else float("nan")

    return {
        "noetic_action": _median(total_density),
        "noetic_action_kinetic": _median(kinetic_density),
        "noetic_action_jerk": _median(jerk_density),
        "noetic_action_potential": _median(potential_density),
    }


def build_run_metric_rows(
    run_table: pd.DataFrame,
    *,
    dim: int,
    coordinate_contract: str,
    model: MiniBatchKMeans,
    metric_diag: np.ndarray,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    analysis_type = ANALYSIS_TYPE_BY_DIM[dim]
    for _, run_row in run_table.iterrows():
        coords, time, provenance = read_run_coords(run_row, dim=dim, coordinate_contract=coordinate_contract)
        if len(coords) < MIN_POINTS_PER_RUN:
            continue
        states = model.predict(coords)
        metrics = repertoire_metrics(states, n_states=REPERTOIRE_STATES_BY_DIM[dim])
        metrics.update(noetic_action_metrics(coords, time, metric_diag=metric_diag))
        for metric_name, value in metrics.items():
            rows.append(
                {
                    "subject": run_row["subject"],
                    "run": run_row["run"],
                    "acq": run_row["acq"],
                    "cpc": run_row["cpc"],
                    "outcome": run_row["outcome"],
                    "time_bin": run_row["time_bin"],
                    "analysis_type": analysis_type,
                    "metric": metric_name,
                    "value": value,
                    "label": run_row["label"],
                    "label_name": run_row["label_name"],
                    "n_windows": run_row["n_windows"],
                    "run_start_from_anchor_sec": run_row["run_start_from_anchor_sec"],
                    "run_midpoint_from_anchor_sec": run_row["run_midpoint_from_anchor_sec"],
                    "processed_h5_path": run_row["processed_h5_path"],
                    "resolved_coordinate_contract": provenance.get("resolved_coordinate_contract"),
                    "coordinate_values_path": provenance.get("values_path"),
                }
            )
    return rows


def aggregate_patient_timebin(run_metric_long: pd.DataFrame) -> pd.DataFrame:
    if run_metric_long.empty:
        return pd.DataFrame(columns=["subject", "time_bin", "analysis_type", "metric", "value"])
    group_cols = ["subject", "cpc", "outcome", "time_bin", "analysis_type", "metric", "label", "label_name"]
    patient_metric = (
        run_metric_long.groupby(group_cols, as_index=False)
        .agg(
            value=("value", "median"),
            n_runs_support=("processed_h5_path", "nunique"),
            n_windows_total=("n_windows", "sum"),
        )
        .sort_values(["subject", "analysis_type", "metric"])
        .reset_index(drop=True)
    )
    return patient_metric


def main() -> None:
    config = parse_args()
    ensure_dir(config.output_dir)
    run_table_full, patient_summary = ensure_timeline_outputs(config)
    run_table = filtered_run_table(run_table_full, primary_time_bin=config.primary_time_bin)
    if run_table.empty:
        raise RuntimeError("No CPC1/CPC5 runs were available in the requested primary time bin.")

    run_metric_rows: list[dict[str, Any]] = []
    manifest: dict[str, Any] = {
        "part": config.part,
        "processed_root": str(config.processed_root),
        "raw_root": str(config.raw_root),
        "timeline_dir": str(config.timeline_dir),
        "output_dir": str(config.output_dir),
        "coordinate_contract": config.coordinate_contract,
        "primary_time_bin": config.primary_time_bin,
        "n_input_runs": int(len(run_table)),
        "n_input_subjects": int(run_table["subject"].nunique()),
        "article_facing_metrics": list(ARTICLE_FACING_METRICS),
        "all_metrics": list(ALL_METRICS),
        "dimensions": {},
    }

    for dim in config.dims:
        model, metric_diag, fit_manifest = fit_codebook(run_table, dim=dim, coordinate_contract=config.coordinate_contract)
        manifest["dimensions"][str(dim)] = fit_manifest
        run_metric_rows.extend(
            build_run_metric_rows(
                run_table,
                dim=dim,
                coordinate_contract=config.coordinate_contract,
                model=model,
                metric_diag=metric_diag,
            )
        )

    run_metric_long = pd.DataFrame(run_metric_rows)
    if run_metric_long.empty:
        raise RuntimeError("Trajectory metric computation produced no usable run-level rows.")
    patient_metric = aggregate_patient_timebin(run_metric_long)
    run_metric_long.to_csv(config.output_dir / RUN_LEVEL_METRICS_CSV, index=False)
    patient_metric.to_csv(config.output_dir / PATIENT_TIMEBIN_METRICS_CSV, index=False)

    manifest["n_run_metric_rows"] = int(len(run_metric_long))
    manifest["n_patient_metric_rows"] = int(len(patient_metric))
    manifest["run_support_by_analysis_type"] = (
        run_metric_long.groupby("analysis_type")["processed_h5_path"].nunique().to_dict()
    )
    manifest["subject_support_by_analysis_type"] = (
        patient_metric.groupby("analysis_type")["subject"].nunique().to_dict()
    )
    manifest["timeline_subjects"] = int(patient_summary["subject"].nunique()) if not patient_summary.empty else 0
    write_json(config.output_dir / MANIFEST_JSON, manifest)


if __name__ == "__main__":
    main()
