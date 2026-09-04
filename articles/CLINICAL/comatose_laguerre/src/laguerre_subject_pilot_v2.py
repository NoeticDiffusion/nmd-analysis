from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import h5py
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
COMA_NDT_DIR = REPO_ROOT / "articles" / "CLINICAL" / "comatose_ndt"

DEFAULT_TIMELINE_DIR = COMA_NDT_DIR / "results" / "timeline_analysis_20260525_combined_cpc15_primary12h"
DEFAULT_MNPS_DIR = COMA_NDT_DIR / "results" / "mnps_summary_20260525_combined_cpc15_primary12h"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "laguerre_pilot_20260525_part2_v2_fullbatch"
DEFAULT_PRIMARY_TIME_BIN = "0_12h"
DEFAULT_COHORT_TAG = "part2"
DEFAULT_GOOD_CPC = 1
DEFAULT_POOR_CPC = 5
DEFAULT_SUBJECTS_PER_GROUP = 0
DEFAULT_MIN_RUNS = 8
DEFAULT_MAX_POINTS_PER_RUN = 60
DEFAULT_NEIGHBORHOOD_SIZE = 25
DEFAULT_GRADIENT_NEIGHBORS = 8
DEFAULT_TIME_CHANGE_WINDOW = 6
DEFAULT_SHAPE_HIST_BINS = 12
DEFAULT_S3_OVER_S2_MAX = 0.75
DEFAULT_SURFACE_FIT_R2_MIN = 0.02
DEFAULT_WORKERS = min(8, max(1, (os.cpu_count() or 2) - 1))
EPS = 1e-9


@dataclass(frozen=True)
class Config:
    timeline_dir: Path
    mnps_dir: Path
    output_dir: Path
    primary_time_bin: str
    cohort_tag: str
    good_cpc: int
    poor_cpc: int
    subjects_per_group: int
    min_runs: int
    max_points_per_run: int
    neighborhood_size: int
    gradient_neighbors: int
    time_change_window: int
    shape_hist_bins: int
    s3_over_s2_max: float
    surface_fit_r2_min: float
    workers: int


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description=(
            "Run a larger-batch Laguerre v2 coma pilot with estimator fixes, additional "
            "geometry metrics, reachability residualization, and optional subject-level parallelization."
        )
    )
    parser.add_argument("--timeline-dir", type=Path, default=DEFAULT_TIMELINE_DIR)
    parser.add_argument("--mnps-dir", type=Path, default=DEFAULT_MNPS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--primary-time-bin", type=str, default=DEFAULT_PRIMARY_TIME_BIN)
    parser.add_argument("--cohort-tag", type=str, default=DEFAULT_COHORT_TAG)
    parser.add_argument("--good-cpc", type=int, default=DEFAULT_GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=DEFAULT_POOR_CPC)
    parser.add_argument(
        "--subjects-per-group",
        type=int,
        default=DEFAULT_SUBJECTS_PER_GROUP,
        help="0 means use all eligible subjects in each endpoint group.",
    )
    parser.add_argument("--min-runs", type=int, default=DEFAULT_MIN_RUNS)
    parser.add_argument("--max-points-per-run", type=int, default=DEFAULT_MAX_POINTS_PER_RUN)
    parser.add_argument("--neighborhood-size", type=int, default=DEFAULT_NEIGHBORHOOD_SIZE)
    parser.add_argument("--gradient-neighbors", type=int, default=DEFAULT_GRADIENT_NEIGHBORS)
    parser.add_argument("--time-change-window", type=int, default=DEFAULT_TIME_CHANGE_WINDOW)
    parser.add_argument("--shape-hist-bins", type=int, default=DEFAULT_SHAPE_HIST_BINS)
    parser.add_argument("--s3-over-s2-max", type=float, default=DEFAULT_S3_OVER_S2_MAX)
    parser.add_argument("--surface-fit-r2-min", type=float, default=DEFAULT_SURFACE_FIT_R2_MIN)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    args = parser.parse_args()
    return Config(
        timeline_dir=args.timeline_dir,
        mnps_dir=args.mnps_dir,
        output_dir=args.output_dir,
        primary_time_bin=args.primary_time_bin,
        cohort_tag=args.cohort_tag,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        subjects_per_group=int(args.subjects_per_group),
        min_runs=max(1, int(args.min_runs)),
        max_points_per_run=max(8, int(args.max_points_per_run)),
        neighborhood_size=max(8, int(args.neighborhood_size)),
        gradient_neighbors=max(1, int(args.gradient_neighbors)),
        time_change_window=max(1, int(args.time_change_window)),
        shape_hist_bins=max(4, int(args.shape_hist_bins)),
        s3_over_s2_max=float(args.s3_over_s2_max),
        surface_fit_r2_min=float(args.surface_fit_r2_min),
        workers=max(1, int(args.workers)),
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def normalize_path(value: Any) -> str:
    return str(value).replace("\\", "/").lower().strip()


def cliffs_delta(good: np.ndarray, poor: np.ndarray) -> float:
    if good.size == 0 or poor.size == 0:
        return float("nan")
    diff = np.subtract.outer(good, poor)
    gt = np.sum(diff > 0)
    lt = np.sum(diff < 0)
    return float((gt - lt) / diff.size)


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    if good.size < 2 or poor.size < 2:
        return float("nan")
    pooled = ((good.size - 1) * np.var(good, ddof=1) + (poor.size - 1) * np.var(poor, ddof=1)) / (good.size + poor.size - 2)
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(good) - np.mean(poor)) / np.sqrt(pooled))


def sample_indices(length: int, max_points: int) -> np.ndarray:
    if length <= max_points:
        return np.arange(length, dtype=int)
    return np.unique(np.linspace(0, length - 1, max_points, dtype=int))


def frobenius_from_symmetric_upper(delta: np.ndarray) -> float:
    return float(
        np.sqrt(
            delta[0] * delta[0]
            + 2.0 * delta[1] * delta[1]
            + 2.0 * delta[2] * delta[2]
            + delta[3] * delta[3]
            + 2.0 * delta[4] * delta[4]
            + delta[5] * delta[5]
        )
    )


def trajectory_curvature(points: np.ndarray) -> np.ndarray:
    if len(points) < 3:
        return np.asarray([], dtype=float)
    values: List[float] = []
    for idx in range(1, len(points) - 1):
        p0 = points[idx - 1]
        p1 = points[idx]
        p2 = points[idx + 1]
        a = np.linalg.norm(p1 - p0)
        b = np.linalg.norm(p2 - p1)
        c = np.linalg.norm(p2 - p0)
        if min(a, b, c) <= EPS:
            continue
        cross = np.linalg.norm(np.cross(p1 - p0, p2 - p0))
        values.append(float(2.0 * cross / (a * b * c + EPS)))
    return np.asarray(values, dtype=float)


def load_coordinate_lookup(config: Config) -> pd.DataFrame:
    frame = pd.read_csv(config.mnps_dir / "run_level_adapter_summaries.csv")
    required = ["processed_h5_path", "time_bin", "cohort_tag", "cpc", "analysis_type", "source_dataset_path"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"run_level_adapter_summaries is missing required columns: {missing}")
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["time_bin"] == config.primary_time_bin].copy()
    frame = frame[frame["cohort_tag"].astype(str) == config.cohort_tag].copy()
    frame = frame[frame["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)])].copy()
    frame = frame[frame["analysis_type"] == "reachability_cones"].copy()
    frame["processed_h5_norm"] = frame["processed_h5_path"].map(normalize_path)
    if "source_dataset_path" in frame.columns:
        use_3d = frame["source_dataset_path"].astype(str).str.contains("coords_3d", case=False, na=False)
        if use_3d.any():
            frame = frame[use_3d].copy()
    sort_cols = ["processed_h5_norm"]
    ascending = [True]
    if "join_matched" in frame.columns:
        sort_cols.append("join_matched")
        ascending.append(False)
    if "n_timepoints" in frame.columns:
        sort_cols.append("n_timepoints")
        ascending.append(False)
    frame = frame.sort_values(sort_cols, ascending=ascending)
    collapsed = frame.groupby("processed_h5_norm", as_index=False).first()
    return collapsed[["processed_h5_norm", "source_dataset_path"]].copy()


def load_run_frame(config: Config) -> pd.DataFrame:
    frame = pd.read_csv(config.timeline_dir / "run_timing_metadata.csv")
    required = [
        "subject",
        "time_bin",
        "cpc",
        "cohort_tag",
        "processed_h5_path",
        "run_midpoint_from_anchor_hours",
        "run_start_from_anchor_sec",
        "run_end_from_anchor_sec",
        "run_key",
    ]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"run_timing_metadata is missing required columns: {missing}")

    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["time_bin"] == config.primary_time_bin].copy()
    frame = frame[frame["cohort_tag"].astype(str) == config.cohort_tag].copy()
    frame = frame[frame["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)])].copy()
    frame["label"] = np.where(frame["cpc_numeric"] == float(config.good_cpc), 1, 0)
    for column in ("run_midpoint_from_anchor_hours", "run_start_from_anchor_sec", "run_end_from_anchor_sec"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["hospital"] = frame["hospital"].fillna("missing").astype(str)
    frame["processed_h5_norm"] = frame["processed_h5_path"].map(normalize_path)
    frame = frame.merge(load_coordinate_lookup(config), on="processed_h5_norm", how="left")
    return frame.sort_values(["subject", "run_midpoint_from_anchor_hours", "run", "acq"]).reset_index(drop=True)


def build_subject_pool(run_frame: pd.DataFrame, config: Config) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for subject, group in run_frame.groupby("subject", sort=False):
        has_coords = group["source_dataset_path"].notna()
        rows.append(
            {
                "subject": str(subject),
                "label": int(group["label"].iloc[0]),
                "cpc": float(group["cpc_numeric"].iloc[0]),
                "hospital": str(group["hospital"].iloc[0]),
                "n_runs": int(len(group)),
                "n_runs_with_coords": int(has_coords.sum()),
                "coverage_hours": float(
                    np.nanmax(pd.to_numeric(group["run_end_from_anchor_sec"], errors="coerce").to_numpy(dtype=float))
                    - np.nanmin(pd.to_numeric(group["run_start_from_anchor_sec"], errors="coerce").to_numpy(dtype=float))
                )
                / 3600.0,
                "eligible_for_pilot": bool(has_coords.sum() >= config.min_runs),
            }
        )
    return pd.DataFrame(rows)


def select_subjects(subject_pool: pd.DataFrame, config: Config) -> pd.DataFrame:
    if subject_pool.empty:
        return subject_pool.copy()
    selected_parts: List[pd.DataFrame] = []
    for label in (1, 0):
        group = subject_pool[(subject_pool["label"] == label) & (subject_pool["eligible_for_pilot"])].copy()
        group = group.sort_values(
            ["n_runs_with_coords", "coverage_hours", "n_runs", "subject"],
            ascending=[False, False, False, True],
        ).reset_index(drop=True)
        if config.subjects_per_group > 0:
            group = group.head(config.subjects_per_group).copy()
        group["selection_rank"] = np.arange(1, len(group) + 1)
        selected_parts.append(group)
    selected = pd.concat(selected_parts, ignore_index=True) if selected_parts else pd.DataFrame()
    return selected.sort_values(["label", "selection_rank", "subject"], ascending=[False, True, True]).reset_index(drop=True)


def load_run_point_cloud(run_row: pd.Series, config: Config) -> pd.DataFrame:
    dataset_path = str(run_row["source_dataset_path"])
    processed_h5_path = Path(str(run_row["processed_h5_path"]))
    if not dataset_path or not processed_h5_path.exists():
        return pd.DataFrame()

    with h5py.File(processed_h5_path, "r") as h5:
        if dataset_path not in h5:
            return pd.DataFrame()
        coords = np.asarray(h5[dataset_path], dtype=float)
        if coords.ndim != 2 or coords.shape[1] < 3:
            return pd.DataFrame()
        coords = coords[:, :3]

        if "window_start" in h5 and "window_end" in h5:
            starts = np.asarray(h5["window_start"], dtype=float)
            ends = np.asarray(h5["window_end"], dtype=float)
            local_mid_sec = (starts + ends) / 2.0
        elif "time" in h5:
            local_mid_sec = np.asarray(h5["time"], dtype=float)
        else:
            local_mid_sec = np.arange(coords.shape[0], dtype=float)

    limit = min(coords.shape[0], local_mid_sec.shape[0])
    coords = coords[:limit]
    local_mid_sec = local_mid_sec[:limit]
    finite_mask = np.isfinite(coords).all(axis=1) & np.isfinite(local_mid_sec)
    coords = coords[finite_mask]
    local_mid_sec = local_mid_sec[finite_mask]
    if coords.size == 0:
        return pd.DataFrame()

    keep_idx = sample_indices(len(coords), config.max_points_per_run)
    coords = coords[keep_idx]
    local_mid_sec = local_mid_sec[keep_idx]

    global_time_h = (float(run_row["run_start_from_anchor_sec"]) + local_mid_sec) / 3600.0
    return pd.DataFrame(
        {
            "subject": str(run_row["subject"]),
            "run_key": str(run_row["run_key"]),
            "hospital": str(run_row["hospital"]),
            "label": int(run_row["label"]),
            "cpc": float(run_row["cpc_numeric"]),
            "processed_h5_path": str(run_row["processed_h5_path"]),
            "time_hour": global_time_h,
            "m_coord": coords[:, 0],
            "d_coord": coords[:, 1],
            "e_coord": coords[:, 2],
        }
    )


def fit_local_quadratic_patch(points: np.ndarray, anchor_idx: int, config: Config) -> Dict[str, Any]:
    anchor = points[anchor_idx]
    distances = np.linalg.norm(points - anchor, axis=1)
    neighbor_idx = np.argsort(distances)[: min(config.neighborhood_size, len(points))]
    local = points[neighbor_idx]
    centered = local - anchor
    if centered.shape[0] < 6:
        return {"status": "too_few_neighbors"}
    if np.linalg.matrix_rank(centered) < 2:
        return {"status": "rank_lt_2"}

    _, singular_values, vt = np.linalg.svd(centered, full_matrices=False)
    s2 = float(singular_values[1]) if len(singular_values) >= 2 else float("nan")
    s3 = float(singular_values[2]) if len(singular_values) >= 3 else float("nan")
    s3_over_s2 = s3 / (s2 + EPS) if np.isfinite(s2) else float("nan")
    tangent = vt[:2].T
    normal = vt[2]
    uv = centered @ tangent
    w = centered @ normal
    u = uv[:, 0]
    v = uv[:, 1]

    design = np.column_stack([u * u, u * v, v * v])
    if np.linalg.matrix_rank(design) < 3:
        return {"status": "design_rank_lt_3"}
    coef, _, _, _ = np.linalg.lstsq(design, w, rcond=None)
    fitted = design @ coef
    residual = w - fitted
    ss_res = float(np.sum(residual**2))
    ss_tot = float(np.sum((w - np.mean(w)) ** 2))
    fit_r2 = 1.0 - ss_res / (ss_tot + EPS)

    a, b, c = coef
    hessian = np.array([[2.0 * a, b], [b, 2.0 * c]], dtype=float)
    eigvals, eigvecs = np.linalg.eigh(hessian)
    lam_min = float(eigvals[0])
    lam_max = float(eigvals[1])
    ambient_ii = tangent @ hessian @ tangent.T
    dom_idx = int(np.argmax(np.abs(eigvals)))
    dominant_dir = tangent @ eigvecs[:, dom_idx]
    dominant_norm = np.linalg.norm(dominant_dir)
    if dominant_norm > EPS:
        dominant_dir = dominant_dir / dominant_norm

    if np.isfinite(s3_over_s2) and s3_over_s2 > config.s3_over_s2_max:
        status = "non_surface_blob"
    elif fit_r2 < config.surface_fit_r2_min:
        status = "low_fit_r2"
    else:
        status = "ok"

    return {
        "status": status,
        "neighbor_count": int(len(neighbor_idx)),
        "surface_fit_r2": fit_r2,
        "s3_over_s2": s3_over_s2,
        "hessian_00": float(hessian[0, 0]),
        "hessian_01": float(hessian[0, 1]),
        "hessian_11": float(hessian[1, 1]),
        "ambient_ii_xx": float(ambient_ii[0, 0]),
        "ambient_ii_xy": float(ambient_ii[0, 1]),
        "ambient_ii_xz": float(ambient_ii[0, 2]),
        "ambient_ii_yy": float(ambient_ii[1, 1]),
        "ambient_ii_yz": float(ambient_ii[1, 2]),
        "ambient_ii_zz": float(ambient_ii[2, 2]),
        "lam_min": lam_min,
        "lam_max": lam_max,
        "curvedness": float(np.sqrt(0.5 * (lam_max * lam_max + lam_min * lam_min))),
        "shape_index": float((2.0 / np.pi) * np.arctan2(lam_max + lam_min, lam_max - lam_min + EPS)),
        "saddle_indicator": float(lam_min * lam_max < 0.0),
        "bending_norm": float(np.linalg.norm(hessian)),
        "dominant_dir_x": float(dominant_dir[0]) if dominant_norm > EPS else float("nan"),
        "dominant_dir_y": float(dominant_dir[1]) if dominant_norm > EPS else float("nan"),
        "dominant_dir_z": float(dominant_dir[2]) if dominant_norm > EPS else float("nan"),
    }


def robust_within_subject_scale(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    median = np.nanmedian(values, axis=0)
    iqr = np.nanquantile(values, 0.75, axis=0) - np.nanquantile(values, 0.25, axis=0)
    iqr = np.where(np.isfinite(iqr) & (iqr > EPS), iqr, 1.0)
    return (values - median) / iqr


def compute_state_space_gradients(valid: pd.DataFrame, config: Config) -> np.ndarray:
    if len(valid) <= 1:
        return np.full(len(valid), np.nan, dtype=float)
    coords = valid[["m_coord", "d_coord", "e_coord"]].to_numpy(dtype=float)
    ambient_ii = valid[
        ["ambient_ii_xx", "ambient_ii_xy", "ambient_ii_xz", "ambient_ii_yy", "ambient_ii_yz", "ambient_ii_zz"]
    ].to_numpy(dtype=float)
    gradients = np.full(len(valid), np.nan, dtype=float)
    for idx in range(len(valid)):
        dist = np.linalg.norm(coords - coords[idx], axis=1)
        order = np.argsort(dist)
        neighbor_idx = [j for j in order if j != idx][: config.gradient_neighbors]
        if not neighbor_idx:
            continue
        values: List[float] = []
        for jdx in neighbor_idx:
            delta = ambient_ii[idx] - ambient_ii[jdx]
            values.append(float(frobenius_from_symmetric_upper(delta) / (dist[jdx] + EPS)))
        gradients[idx] = float(np.median(values))
    return gradients


def compute_legacy_change(valid: pd.DataFrame, config: Config) -> np.ndarray:
    if len(valid) <= 1:
        return np.full(len(valid), np.nan, dtype=float)
    descriptors = valid[["curvedness", "shape_index", "lam_min", "lam_max"]].to_numpy(dtype=float)
    scaled = robust_within_subject_scale(descriptors)
    out = np.full(len(valid), np.nan, dtype=float)
    for idx in range(len(valid)):
        lo = max(0, idx - config.time_change_window)
        hi = min(len(valid), idx + config.time_change_window + 1)
        neighbor_idx = [j for j in range(lo, hi) if j != idx]
        if not neighbor_idx:
            continue
        dist = np.linalg.norm(scaled[neighbor_idx] - scaled[idx], axis=1)
        out[idx] = float(np.median(dist))
    return out


def compute_shape_change(valid: pd.DataFrame, config: Config) -> np.ndarray:
    if len(valid) <= 1:
        return np.full(len(valid), np.nan, dtype=float)
    descriptors = valid[["curvedness", "shape_index"]].to_numpy(dtype=float)
    scaled = robust_within_subject_scale(descriptors)
    out = np.full(len(valid), np.nan, dtype=float)
    for idx in range(len(valid)):
        lo = max(0, idx - config.time_change_window)
        hi = min(len(valid), idx + config.time_change_window + 1)
        neighbor_idx = [j for j in range(lo, hi) if j != idx]
        if not neighbor_idx:
            continue
        dist = np.linalg.norm(scaled[neighbor_idx] - scaled[idx], axis=1)
        out[idx] = float(np.median(dist))
    return out


def compute_shape_entropy(values: np.ndarray, bins: int) -> float:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return float("nan")
    hist, _ = np.histogram(np.clip(finite, -1.0, 1.0), bins=bins, range=(-1.0, 1.0), density=False)
    prob = hist.astype(float) / max(np.sum(hist), 1.0)
    prob = prob[prob > 0]
    entropy = -np.sum(prob * np.log(prob))
    return float(entropy / np.log(bins))


def compute_direction_coherence(valid: pd.DataFrame) -> float:
    dirs = valid[["dominant_dir_x", "dominant_dir_y", "dominant_dir_z"]].to_numpy(dtype=float)
    finite = np.isfinite(dirs).all(axis=1)
    dirs = dirs[finite]
    if len(dirs) == 0:
        return float("nan")
    dirs = dirs / (np.linalg.norm(dirs, axis=1, keepdims=True) + EPS)
    orient = np.mean(np.einsum("ni,nj->nij", dirs, dirs), axis=0)
    eigvals = np.linalg.eigvalsh(orient)
    return float(np.clip((3.0 * eigvals[-1] - 1.0) / 2.0, 0.0, 1.0))


def compute_mann_kendall(valid: pd.DataFrame, metric_column: str) -> float:
    frame = valid[["time_hour", metric_column]].copy()
    frame["hour_bin"] = np.floor(pd.to_numeric(frame["time_hour"], errors="coerce")).astype("Int64")
    hourly = frame.groupby("hour_bin", as_index=False)[metric_column].median()
    values = pd.to_numeric(hourly[metric_column], errors="coerce").to_numpy(dtype=float)
    hours = pd.to_numeric(hourly["hour_bin"], errors="coerce").to_numpy(dtype=float)
    finite = np.isfinite(values) & np.isfinite(hours)
    if np.sum(finite) < 3 or np.unique(values[finite]).size < 2:
        return float("nan")
    tau, _ = stats.kendalltau(hours[finite], values[finite])
    return float(tau) if np.isfinite(tau) else float("nan")


def summarize_distribution(values: np.ndarray, prefix: str) -> Dict[str, float]:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return {
            f"{prefix}_median": float("nan"),
            f"{prefix}_p95": float("nan"),
        }
    return {
        f"{prefix}_median": float(np.median(finite)),
        f"{prefix}_p95": float(np.quantile(finite, 0.95)),
    }


def compute_subject_laguerre(subject_runs: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, Dict[str, Any]]:
    ordered_runs = subject_runs.sort_values(["run_midpoint_from_anchor_hours", "run", "acq"]).reset_index(drop=True)
    clouds = [load_run_point_cloud(run_row, config) for _, run_row in ordered_runs.iterrows()]
    anchor_frame = pd.concat([cloud for cloud in clouds if not cloud.empty], ignore_index=True) if clouds else pd.DataFrame()

    subject = str(ordered_runs["subject"].iloc[0])
    hospital = str(ordered_runs["hospital"].iloc[0])
    label = int(ordered_runs["label"].iloc[0])
    cpc = float(ordered_runs["cpc_numeric"].iloc[0])
    base_summary: Dict[str, Any] = {
        "subject": subject,
        "hospital": hospital,
        "label": label,
        "cpc": cpc,
        "n_runs": int(len(ordered_runs)),
    }
    if anchor_frame.empty:
        empty_summary = dict(base_summary)
        empty_summary.update(
            {
                "sampled_point_count": 0,
                "laguerre_anchor_count": 0,
                "laguerre_valid_fraction": 0.0,
                "laguerre_surface_fit_r2_median": float("nan"),
                "laguerre_s3_over_s2_median": float("nan"),
                "laguerre_curvedness_median": float("nan"),
                "laguerre_curvedness_p95": float("nan"),
                "laguerre_shape_index_median": float("nan"),
                "laguerre_grad_ii_norm_median": float("nan"),
                "laguerre_grad_ii_norm_p95": float("nan"),
                "laguerre_legacy_change_norm_median": float("nan"),
                "laguerre_legacy_change_norm_p95": float("nan"),
                "laguerre_shape_change_norm_median": float("nan"),
                "laguerre_shape_change_norm_p95": float("nan"),
                "laguerre_saddle_fraction": float("nan"),
                "laguerre_direction_coherence": float("nan"),
                "laguerre_shape_entropy": float("nan"),
                "laguerre_grad_ii_mk_tau": float("nan"),
                "laguerre_trajectory_curvature_median": float("nan"),
                "laguerre_trajectory_curvature_p95": float("nan"),
                "status": "no_sampled_points",
            }
        )
        return anchor_frame, empty_summary

    anchor_frame = anchor_frame.sort_values(["time_hour", "run_key"]).reset_index(drop=True)
    points = anchor_frame[["m_coord", "d_coord", "e_coord"]].to_numpy(dtype=float)
    patch_rows = [fit_local_quadratic_patch(points, idx, config) for idx in range(len(anchor_frame))]
    anchor_frame = pd.concat([anchor_frame, pd.DataFrame(patch_rows)], axis=1)

    valid = anchor_frame[anchor_frame["status"] == "ok"].copy().reset_index(drop=True)
    if valid.empty:
        empty_summary = dict(base_summary)
        empty_summary.update(
            {
                "sampled_point_count": int(len(anchor_frame)),
                "laguerre_anchor_count": 0,
                "laguerre_valid_fraction": 0.0,
                "laguerre_surface_fit_r2_median": float("nan"),
                "laguerre_s3_over_s2_median": float("nan"),
                "laguerre_curvedness_median": float("nan"),
                "laguerre_curvedness_p95": float("nan"),
                "laguerre_shape_index_median": float("nan"),
                "laguerre_grad_ii_norm_median": float("nan"),
                "laguerre_grad_ii_norm_p95": float("nan"),
                "laguerre_legacy_change_norm_median": float("nan"),
                "laguerre_legacy_change_norm_p95": float("nan"),
                "laguerre_shape_change_norm_median": float("nan"),
                "laguerre_shape_change_norm_p95": float("nan"),
                "laguerre_saddle_fraction": float("nan"),
                "laguerre_direction_coherence": float("nan"),
                "laguerre_shape_entropy": float("nan"),
                "laguerre_grad_ii_mk_tau": float("nan"),
                "laguerre_trajectory_curvature_median": float("nan"),
                "laguerre_trajectory_curvature_p95": float("nan"),
                "status": "no_valid_anchors",
            }
        )
        return anchor_frame, empty_summary

    valid["laguerre_grad_ii_norm"] = compute_state_space_gradients(valid, config)
    valid["laguerre_legacy_change_norm"] = compute_legacy_change(valid, config)
    valid["laguerre_shape_change_norm"] = compute_shape_change(valid, config)
    anchor_frame = anchor_frame.merge(
        valid[
            [
                "time_hour",
                "run_key",
                "laguerre_grad_ii_norm",
                "laguerre_legacy_change_norm",
                "laguerre_shape_change_norm",
            ]
        ],
        on=["time_hour", "run_key"],
        how="left",
    )

    trajectory = trajectory_curvature(anchor_frame[["m_coord", "d_coord", "e_coord"]].to_numpy(dtype=float))
    summary = dict(base_summary)
    summary.update(
        {
            "sampled_point_count": int(len(anchor_frame)),
            "laguerre_anchor_count": int(len(valid)),
            "laguerre_valid_fraction": float(len(valid) / max(len(anchor_frame), 1)),
            "laguerre_surface_fit_r2_median": float(np.nanmedian(pd.to_numeric(valid["surface_fit_r2"], errors="coerce"))),
            "laguerre_s3_over_s2_median": float(np.nanmedian(pd.to_numeric(valid["s3_over_s2"], errors="coerce"))),
            "laguerre_shape_index_median": float(np.nanmedian(pd.to_numeric(valid["shape_index"], errors="coerce"))),
            "laguerre_saddle_fraction": float(np.nanmean(pd.to_numeric(valid["saddle_indicator"], errors="coerce"))),
            "laguerre_direction_coherence": compute_direction_coherence(valid),
            "laguerre_shape_entropy": compute_shape_entropy(
                pd.to_numeric(valid["shape_index"], errors="coerce").to_numpy(dtype=float),
                config.shape_hist_bins,
            ),
            "laguerre_grad_ii_mk_tau": compute_mann_kendall(valid, "laguerre_grad_ii_norm"),
            "status": "ok",
        }
    )
    summary.update(
        summarize_distribution(
            pd.to_numeric(valid["curvedness"], errors="coerce").to_numpy(dtype=float),
            "laguerre_curvedness",
        )
    )
    summary.update(
        summarize_distribution(
            pd.to_numeric(valid["laguerre_grad_ii_norm"], errors="coerce").to_numpy(dtype=float),
            "laguerre_grad_ii_norm",
        )
    )
    summary.update(
        summarize_distribution(
            pd.to_numeric(valid["laguerre_legacy_change_norm"], errors="coerce").to_numpy(dtype=float),
            "laguerre_legacy_change_norm",
        )
    )
    summary.update(
        summarize_distribution(
            pd.to_numeric(valid["laguerre_shape_change_norm"], errors="coerce").to_numpy(dtype=float),
            "laguerre_shape_change_norm",
        )
    )
    summary.update(
        summarize_distribution(
            trajectory,
            "laguerre_trajectory_curvature",
        )
    )
    return anchor_frame, summary


def subject_worker(payload: tuple[Dict[str, Any], List[Dict[str, Any]], Config]) -> tuple[pd.DataFrame, Dict[str, Any]]:
    _, rows, config = payload
    subject_runs = pd.DataFrame(rows)
    return compute_subject_laguerre(subject_runs, config)


def run_subject_batch(selected_run_frame: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    payloads = [
        ({"subject": str(subject)}, group.to_dict("records"), config)
        for subject, group in selected_run_frame.groupby("subject", sort=False)
    ]
    anchor_frames: List[pd.DataFrame] = []
    summaries: List[Dict[str, Any]] = []

    if config.workers <= 1:
        for payload in payloads:
            anchor_frame, summary = subject_worker(payload)
            anchor_frames.append(anchor_frame)
            summaries.append(summary)
    else:
        with ProcessPoolExecutor(max_workers=config.workers) as executor:
            future_map = {executor.submit(subject_worker, payload): payload[0]["subject"] for payload in payloads}
            for future in as_completed(future_map):
                anchor_frame, summary = future.result()
                anchor_frames.append(anchor_frame)
                summaries.append(summary)

    anchor_metrics = pd.concat(anchor_frames, ignore_index=True) if anchor_frames else pd.DataFrame()
    subject_metrics = pd.DataFrame(summaries)
    return anchor_metrics, subject_metrics


def load_reachability_subject_metrics(config: Config) -> pd.DataFrame:
    frame = pd.read_csv(config.mnps_dir / "patient_timebin_signal_metrics.csv")
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["time_bin"] == config.primary_time_bin].copy()
    frame = frame[frame["cohort_tag"].astype(str) == config.cohort_tag].copy()
    frame = frame[frame["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)])].copy()
    frame = frame[frame["analysis_type"] == "reachability_cones"].copy()
    frame = frame[
        frame["metric"].astype(str).isin(
            {"tube_d_eff_median", "tube_a_operator_norm_median", "tube_capture_gate_median"}
        )
    ].copy()
    if "source_dataset_path" in frame.columns:
        use_3d = frame["source_dataset_path"].astype(str).str.contains("coords_3d", case=False, na=False)
        if use_3d.any():
            frame = frame[use_3d].copy()
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[frame["value"].notna()].copy()
    collapsed = (
        frame.groupby(["subject", "metric"], as_index=False)
        .agg(value=("value", "median"))
        .pivot(index="subject", columns="metric", values="value")
        .reset_index()
    )
    collapsed.columns.name = None
    return collapsed


def add_scale_invariant_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if {"laguerre_grad_ii_norm_median", "tube_d_eff_median"}.issubset(out.columns):
        out["laguerre_grad_ii_scaled_median"] = (
            pd.to_numeric(out["laguerre_grad_ii_norm_median"], errors="coerce")
            * pd.to_numeric(out["tube_d_eff_median"], errors="coerce")
        )
    if {"laguerre_curvedness_median", "tube_d_eff_median"}.issubset(out.columns):
        out["laguerre_curvedness_scaled_median"] = (
            pd.to_numeric(out["laguerre_curvedness_median"], errors="coerce")
            * pd.to_numeric(out["tube_d_eff_median"], errors="coerce")
        )
    return out


def add_reachability_residuals(frame: pd.DataFrame, metrics: Sequence[str]) -> tuple[pd.DataFrame, Dict[str, Dict[str, float]]]:
    out = frame.copy()
    diagnostics: Dict[str, Dict[str, float]] = {}
    baseline_cols = ["tube_d_eff_median", "tube_a_operator_norm_median"]
    if not set(baseline_cols).issubset(out.columns):
        return out, diagnostics

    baselines = out[baseline_cols].apply(pd.to_numeric, errors="coerce")
    for metric in metrics:
        if metric not in out.columns:
            continue
        y = pd.to_numeric(out[metric], errors="coerce")
        mask = np.isfinite(y.to_numpy(dtype=float)) & baselines.notna().all(axis=1).to_numpy()
        if int(np.sum(mask)) < 5:
            continue
        x = np.column_stack(
            [
                np.ones(int(np.sum(mask)), dtype=float),
                baselines.loc[mask, "tube_d_eff_median"].to_numpy(dtype=float),
                baselines.loc[mask, "tube_a_operator_norm_median"].to_numpy(dtype=float),
            ]
        )
        y_fit = y.loc[mask].to_numpy(dtype=float)
        beta, _, _, _ = np.linalg.lstsq(x, y_fit, rcond=None)
        fitted = x @ beta
        resid = y_fit - fitted
        resid_col = f"{metric}_resid_reachability"
        out[resid_col] = float("nan")
        out.loc[mask, resid_col] = resid
        ss_res = float(np.sum((y_fit - fitted) ** 2))
        ss_tot = float(np.sum((y_fit - np.mean(y_fit)) ** 2))
        diagnostics[resid_col] = {
            "intercept": float(beta[0]),
            "beta_tube_d_eff_median": float(beta[1]),
            "beta_tube_a_operator_norm_median": float(beta[2]),
            "r2": float(1.0 - ss_res / (ss_tot + EPS)),
            "n_rows": int(np.sum(mask)),
        }
    return out, diagnostics


def summarize_effect_metric(frame: pd.DataFrame, metric: str, label: str) -> Dict[str, Any]:
    values = pd.to_numeric(frame[metric], errors="coerce")
    usable = frame.loc[np.isfinite(values.to_numpy(dtype=float))].copy()
    x = pd.to_numeric(usable[metric], errors="coerce").to_numpy(dtype=float)
    y = usable["label"].astype(int).to_numpy(dtype=int)
    good = x[y == 1]
    poor = x[y == 0]
    if x.size == 0 or good.size == 0 or poor.size == 0:
        return {
            "metric": metric,
            "label": label,
            "status": "insufficient_groups",
            "n_cpc1": int(good.size),
            "n_cpc5": int(poor.size),
            "cpc1_median": float(np.median(good)) if good.size else float("nan"),
            "cpc5_median": float(np.median(poor)) if poor.size else float("nan"),
            "delta_median_good_minus_poor": float("nan"),
            "cohens_d": float("nan"),
            "cliffs_delta": float("nan"),
            "mannwhitney_p": float("nan"),
            "direct_auc": float("nan"),
        }
    direction = -1.0 if np.median(good) < np.median(poor) else 1.0
    score = direction * x
    mannwhitney = stats.mannwhitneyu(good, poor, alternative="two-sided")
    return {
        "metric": metric,
        "label": label,
        "status": "ok",
        "n_cpc1": int(good.size),
        "n_cpc5": int(poor.size),
        "cpc1_median": float(np.median(good)),
        "cpc5_median": float(np.median(poor)),
        "delta_median_good_minus_poor": float(np.median(good) - np.median(poor)),
        "cohens_d": cohens_d(good, poor),
        "cliffs_delta": cliffs_delta(good, poor),
        "mannwhitney_p": float(mannwhitney.pvalue),
        "direct_auc": float(roc_auc_score(y, score)),
    }


def build_effect_table(subject_metrics: pd.DataFrame) -> pd.DataFrame:
    specs: List[Tuple[str, str]] = [
        ("tube_d_eff_median", "Reachability d_eff median"),
        ("tube_a_operator_norm_median", "Reachability A-operator norm median"),
        ("tube_capture_gate_median", "Reachability capture gate median"),
        ("laguerre_grad_ii_norm_median", "Laguerre grad-II norm median"),
        ("laguerre_grad_ii_norm_p95", "Laguerre grad-II norm p95"),
        ("laguerre_curvedness_median", "Laguerre curvedness median"),
        ("laguerre_curvedness_p95", "Laguerre curvedness p95"),
        ("laguerre_shape_index_median", "Laguerre shape index median"),
        ("laguerre_saddle_fraction", "Laguerre saddle fraction"),
        ("laguerre_direction_coherence", "Laguerre bending-direction coherence"),
        ("laguerre_shape_entropy", "Laguerre shape entropy"),
        ("laguerre_grad_ii_mk_tau", "Laguerre Mann-Kendall tau"),
        ("laguerre_legacy_change_norm_median", "Legacy change norm median"),
        ("laguerre_legacy_change_norm_p95", "Legacy change norm p95"),
        ("laguerre_shape_change_norm_median", "Shape-only change norm median"),
        ("laguerre_shape_change_norm_p95", "Shape-only change norm p95"),
        ("laguerre_grad_ii_scaled_median", "Reachability-weighted grad-II interaction"),
        ("laguerre_curvedness_scaled_median", "Reachability-weighted curvedness interaction"),
        ("laguerre_trajectory_curvature_median", "Trajectory curvature median"),
        ("laguerre_trajectory_curvature_p95", "Trajectory curvature p95"),
    ]
    resid_metrics = [
        metric
        for metric in subject_metrics.columns
        if metric.endswith("_resid_reachability")
    ]
    specs.extend((metric, metric.replace("_resid_reachability", " residualized vs reachability")) for metric in sorted(resid_metrics))

    rows = [summarize_effect_metric(subject_metrics, metric, label) for metric, label in specs if metric in subject_metrics.columns]
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["abs_cohens_d"] = np.abs(pd.to_numeric(out["cohens_d"], errors="coerce"))
    return out.sort_values(["abs_cohens_d", "direct_auc"], ascending=[False, False], na_position="last").reset_index(drop=True)


def describe_selected_subjects(selected_subjects: pd.DataFrame, label: int) -> str:
    subset = selected_subjects[selected_subjects["label"] == label].copy()
    if subset.empty:
        return "none"
    subjects = subset["subject"].astype(str).tolist()
    if len(subjects) <= 20:
        return ", ".join(subjects)
    return ", ".join(subjects[:10]) + f", ... ({len(subjects)} total)"


def write_summary_markdown(
    config: Config,
    subject_pool: pd.DataFrame,
    selected_subjects: pd.DataFrame,
    effects: pd.DataFrame,
) -> str:
    lines = [
        "# Laguerre Pilot V2 Summary",
        "",
        f"Batch cohort: `{config.cohort_tag}` / `{config.primary_time_bin}`.",
        "",
        "## Design",
        "",
        "- Geometry is computed from subject-anchored 3D MNPS coordinates read directly from the H5 files referenced by the coma wrappers.",
        "- This v2 batch adds shape index, curvedness, an ambient-Frobenius state-space grad-II proxy, saddle fraction, direction coherence, curvature entropy, a Mann-Kendall trend, residualization against reachability, and a trajectory-curvature negative control.",
        f"- `subjects_per_group={config.subjects_per_group}` (`0` means all eligible subjects)",
        f"- `workers={config.workers}`",
        f"- `max_points_per_run={config.max_points_per_run}`",
        f"- `neighborhood_size={config.neighborhood_size}`",
        f"- `gradient_neighbors={config.gradient_neighbors}`",
        f"- `s3_over_s2_max={config.s3_over_s2_max}`",
        f"- `surface_fit_r2_min={config.surface_fit_r2_min}`",
        "",
        "## Cohort Triage",
        "",
        f"- eligible CPC1 subjects: {int(((subject_pool['label'] == 1) & subject_pool['eligible_for_pilot']).sum()) if not subject_pool.empty else 0}",
        f"- eligible CPC5 subjects: {int(((subject_pool['label'] == 0) & subject_pool['eligible_for_pilot']).sum()) if not subject_pool.empty else 0}",
        f"- selected CPC1 subjects: {int((selected_subjects['label'] == 1).sum()) if not selected_subjects.empty else 0}",
        f"- selected CPC5 subjects: {int((selected_subjects['label'] == 0).sum()) if not selected_subjects.empty else 0}",
        "",
        "## Selected Subjects",
        "",
        f"- CPC1: {describe_selected_subjects(selected_subjects, 1)}",
        f"- CPC5: {describe_selected_subjects(selected_subjects, 0)}",
        "",
    ]

    if effects.empty:
        lines.extend(["## Status", "", "No effect-size table could be built from the selected batch.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "## Effect Sizes",
            "",
            "| Metric | CPC1 median | CPC5 median | Cohen's d | Cliff's delta | Mann-Whitney p | Direct AUROC |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for _, row in effects.head(18).iterrows():
        lines.append(
            f"| {row['label']} | {row['cpc1_median']:.3f} | {row['cpc5_median']:.3f} | "
            f"{row['cohens_d']:.3f} | {row['cliffs_delta']:.3f} | {row['mannwhitney_p']:.3g} | {row['direct_auc']:.3f} |"
        )

    raw_laguerre = effects[
        effects["metric"].astype(str).str.startswith("laguerre_")
        & ~effects["metric"].astype(str).str.endswith("_resid_reachability")
    ].copy()
    residual_laguerre = effects[effects["metric"].astype(str).str.endswith("_resid_reachability")].copy()
    baseline = effects[effects["metric"] == "tube_d_eff_median"].copy()
    lines.extend(["", "## Quick Read", ""])
    if not raw_laguerre.empty:
        top_raw = raw_laguerre.iloc[0]
        lines.append(
            f"- strongest raw Laguerre metric: `{top_raw['metric']}` with Cohen's d `{top_raw['cohens_d']:.3f}` and direct AUROC `{top_raw['direct_auc']:.3f}`."
        )
    if not residual_laguerre.empty:
        top_resid = residual_laguerre.iloc[0]
        lines.append(
            f"- strongest reachability-residualized Laguerre metric: `{top_resid['metric']}` with Cohen's d `{top_resid['cohens_d']:.3f}` and direct AUROC `{top_resid['direct_auc']:.3f}`."
        )
    if not baseline.empty:
        base = baseline.iloc[0]
        lines.append(
            f"- reachability reference (`tube_d_eff_median`) shows Cohen's d `{base['cohens_d']:.3f}` and direct AUROC `{base['direct_auc']:.3f}` in the same batch."
        )
    lines.append("- Residual metrics are the stricter test of whether the Laguerre layer adds information beyond reachability severity.")
    lines.append("- Reachability-weighted metrics are interaction terms by construction, not independent geometry-only measures.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    config = parse_args()
    ensure_dir(config.output_dir)

    run_frame = load_run_frame(config)
    subject_pool = build_subject_pool(run_frame, config)
    selected_subjects = select_subjects(subject_pool, config)
    if selected_subjects.empty:
        raise ValueError("No eligible subjects were found for the requested batch settings.")

    selected_run_frame = run_frame[run_frame["subject"].isin(selected_subjects["subject"])].copy()
    anchor_metrics, subject_metrics = run_subject_batch(selected_run_frame, config)
    subject_metrics = selected_subjects.merge(subject_metrics, on=["subject", "label", "cpc", "hospital"], how="left")

    reachability_metrics = load_reachability_subject_metrics(config)
    if not reachability_metrics.empty:
        subject_metrics = subject_metrics.merge(reachability_metrics, on="subject", how="left")
    subject_metrics = add_scale_invariant_metrics(subject_metrics)

    laguerre_metrics_for_residuals = [
        "laguerre_grad_ii_norm_median",
        "laguerre_grad_ii_norm_p95",
        "laguerre_curvedness_median",
        "laguerre_curvedness_p95",
        "laguerre_shape_index_median",
        "laguerre_saddle_fraction",
        "laguerre_direction_coherence",
        "laguerre_shape_entropy",
        "laguerre_grad_ii_mk_tau",
        "laguerre_legacy_change_norm_median",
        "laguerre_legacy_change_norm_p95",
        "laguerre_shape_change_norm_median",
        "laguerre_shape_change_norm_p95",
        "laguerre_trajectory_curvature_median",
        "laguerre_trajectory_curvature_p95",
        "laguerre_grad_ii_scaled_median",
        "laguerre_curvedness_scaled_median",
    ]
    subject_metrics, residual_diagnostics = add_reachability_residuals(subject_metrics, laguerre_metrics_for_residuals)
    effects = build_effect_table(subject_metrics)
    summary_text = write_summary_markdown(config, subject_pool, selected_subjects, effects)

    manifest = {
        "timeline_dir": str(config.timeline_dir),
        "mnps_dir": str(config.mnps_dir),
        "output_dir": str(config.output_dir),
        "primary_time_bin": config.primary_time_bin,
        "cohort_tag": config.cohort_tag,
        "good_cpc": config.good_cpc,
        "poor_cpc": config.poor_cpc,
        "subjects_per_group": config.subjects_per_group,
        "min_runs": config.min_runs,
        "max_points_per_run": config.max_points_per_run,
        "neighborhood_size": config.neighborhood_size,
        "gradient_neighbors": config.gradient_neighbors,
        "time_change_window": config.time_change_window,
        "shape_hist_bins": config.shape_hist_bins,
        "s3_over_s2_max": config.s3_over_s2_max,
        "surface_fit_r2_min": config.surface_fit_r2_min,
        "workers": config.workers,
        "eligible_subjects_cpc1": int(((subject_pool["label"] == 1) & subject_pool["eligible_for_pilot"]).sum()) if not subject_pool.empty else 0,
        "eligible_subjects_cpc5": int(((subject_pool["label"] == 0) & subject_pool["eligible_for_pilot"]).sum()) if not subject_pool.empty else 0,
        "selected_subjects_cpc1": int((selected_subjects["label"] == 1).sum()) if not selected_subjects.empty else 0,
        "selected_subjects_cpc5": int((selected_subjects["label"] == 0).sum()) if not selected_subjects.empty else 0,
        "selected_subjects": selected_subjects["subject"].astype(str).tolist(),
    }

    selected_subjects.to_csv(config.output_dir / "pilot_selected_subjects.csv", index=False)
    anchor_metrics.to_csv(config.output_dir / "laguerre_anchor_metrics.csv", index=False)
    subject_metrics.to_csv(config.output_dir / "laguerre_subject_metrics.csv", index=False)
    effects.to_csv(config.output_dir / "laguerre_effect_sizes.csv", index=False)
    (config.output_dir / "laguerre_pilot_summary.md").write_text(summary_text, encoding="utf-8")
    (config.output_dir / "laguerre_pilot_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (config.output_dir / "reachability_residual_models.json").write_text(json.dumps(residual_diagnostics, indent=2), encoding="utf-8")

    print(f"Wrote selected subjects to {config.output_dir / 'pilot_selected_subjects.csv'}")
    print(f"Wrote anchor metrics to {config.output_dir / 'laguerre_anchor_metrics.csv'}")
    print(f"Wrote subject metrics to {config.output_dir / 'laguerre_subject_metrics.csv'}")
    print(f"Wrote effect-size summary to {config.output_dir / 'laguerre_effect_sizes.csv'}")
    print(f"Wrote markdown summary to {config.output_dir / 'laguerre_pilot_summary.md'}")


if __name__ == "__main__":
    main()
