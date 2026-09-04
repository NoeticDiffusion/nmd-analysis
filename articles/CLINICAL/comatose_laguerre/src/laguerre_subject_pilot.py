from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

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
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "laguerre_pilot_20260525_part2_small"
DEFAULT_PRIMARY_TIME_BIN = "0_12h"
DEFAULT_COHORT_TAG = "part2"
DEFAULT_GOOD_CPC = 1
DEFAULT_POOR_CPC = 5
DEFAULT_SUBJECTS_PER_GROUP = 12
DEFAULT_MIN_RUNS = 8
DEFAULT_NEIGHBORHOOD_SIZE = 25
DEFAULT_TIME_CHANGE_WINDOW = 6
DEFAULT_MAX_POINTS_PER_RUN = 60
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
    neighborhood_size: int
    time_change_window: int
    max_points_per_run: int


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description=(
            "Run a small Laguerre-form-inspired coma pilot by selecting a limited CPC1/CPC5 subject subset "
            "and reading subject-anchored 3D MNPS coordinates directly from the existing H5 references."
        )
    )
    parser.add_argument("--timeline-dir", type=Path, default=DEFAULT_TIMELINE_DIR)
    parser.add_argument("--mnps-dir", type=Path, default=DEFAULT_MNPS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--primary-time-bin", type=str, default=DEFAULT_PRIMARY_TIME_BIN)
    parser.add_argument("--cohort-tag", type=str, default=DEFAULT_COHORT_TAG)
    parser.add_argument("--good-cpc", type=int, default=DEFAULT_GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=DEFAULT_POOR_CPC)
    parser.add_argument("--subjects-per-group", type=int, default=DEFAULT_SUBJECTS_PER_GROUP)
    parser.add_argument("--min-runs", type=int, default=DEFAULT_MIN_RUNS)
    parser.add_argument("--neighborhood-size", type=int, default=DEFAULT_NEIGHBORHOOD_SIZE)
    parser.add_argument("--time-change-window", type=int, default=DEFAULT_TIME_CHANGE_WINDOW)
    parser.add_argument("--max-points-per-run", type=int, default=DEFAULT_MAX_POINTS_PER_RUN)
    args = parser.parse_args()
    return Config(
        timeline_dir=args.timeline_dir,
        mnps_dir=args.mnps_dir,
        output_dir=args.output_dir,
        primary_time_bin=args.primary_time_bin,
        cohort_tag=args.cohort_tag,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        subjects_per_group=args.subjects_per_group,
        min_runs=args.min_runs,
        neighborhood_size=max(8, int(args.neighborhood_size)),
        time_change_window=max(1, int(args.time_change_window)),
        max_points_per_run=max(8, int(args.max_points_per_run)),
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
    lookup = load_coordinate_lookup(config)
    frame = frame.merge(lookup, on="processed_h5_norm", how="left")
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
        group = group.head(config.subjects_per_group).copy()
        group["selection_rank"] = np.arange(1, len(group) + 1)
        selected_parts.append(group)
    selected = pd.concat(selected_parts, ignore_index=True) if selected_parts else pd.DataFrame()
    return selected.sort_values(["label", "selection_rank", "subject"], ascending=[False, True, True]).reset_index(drop=True)


def sample_indices(length: int, max_points: int) -> np.ndarray:
    if length <= max_points:
        return np.arange(length, dtype=int)
    return np.unique(np.linspace(0, length - 1, max_points, dtype=int))


def load_run_point_cloud(run_row: pd.Series, config: Config) -> pd.DataFrame:
    source_dataset_path = str(run_row["source_dataset_path"])
    processed_h5_path = Path(str(run_row["processed_h5_path"]))
    if not source_dataset_path or not processed_h5_path.exists():
        return pd.DataFrame()

    with h5py.File(processed_h5_path, "r") as h5:
        if source_dataset_path not in h5:
            return pd.DataFrame()
        coords = np.asarray(h5[source_dataset_path], dtype=float)
        if coords.ndim != 2 or coords.shape[1] < 3:
            return pd.DataFrame()
        coords = coords[:, :3]

        local_mid_sec: np.ndarray
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


def fit_local_quadratic_patch(points: np.ndarray, anchor_idx: int, neighborhood_size: int) -> Dict[str, float]:
    anchor = points[anchor_idx]
    distances = np.linalg.norm(points - anchor, axis=1)
    neighbor_idx = np.argsort(distances)[: min(neighborhood_size, len(points))]
    local = points[neighbor_idx]
    centered = local - anchor
    if centered.shape[0] < 6:
        return {"status": "too_few_neighbors"}
    if np.linalg.matrix_rank(centered) < 2:
        return {"status": "rank_lt_2"}

    _, singular_values, vt = np.linalg.svd(centered, full_matrices=False)
    tangent = vt[:2].T
    normal = vt[2]
    uv = centered @ tangent
    w = centered @ normal
    u = uv[:, 0]
    v = uv[:, 1]
    design = np.column_stack([u * u, u * v, v * v, u, v, np.ones_like(u)])
    rank = int(np.linalg.matrix_rank(design))
    if rank < 6:
        return {"status": "design_rank_lt_6"}

    coef, _, _, _ = np.linalg.lstsq(design, w, rcond=None)
    fitted = design @ coef
    residual = w - fitted
    ss_res = float(np.sum(residual**2))
    ss_tot = float(np.sum((w - np.mean(w)) ** 2))
    fit_r2 = 1.0 - ss_res / (ss_tot + EPS)

    a, b, c, _, _, _ = coef
    hessian = np.array([[2.0 * a, b], [b, 2.0 * c]], dtype=float)
    eigvals = np.linalg.eigvalsh(hessian)
    return {
        "status": "ok",
        "neighbor_count": int(len(neighbor_idx)),
        "surface_fit_r2": fit_r2,
        "bending_norm": float(np.linalg.norm(hessian)),
        "mean_curvature_proxy": float(np.sum(eigvals)),
        "gaussian_curvature_proxy": float(np.prod(eigvals)),
        "anisotropy": float(abs(eigvals[1] - eigvals[0]) / (abs(eigvals[1]) + abs(eigvals[0]) + EPS)),
        "local_singular_value_1": float(singular_values[0]) if len(singular_values) >= 1 else float("nan"),
        "local_singular_value_2": float(singular_values[1]) if len(singular_values) >= 2 else float("nan"),
        "local_singular_value_3": float(singular_values[2]) if len(singular_values) >= 3 else float("nan"),
    }


def robust_within_subject_scale(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    median = np.nanmedian(values, axis=0)
    iqr = np.nanquantile(values, 0.75, axis=0) - np.nanquantile(values, 0.25, axis=0)
    iqr = np.where(np.isfinite(iqr) & (iqr > EPS), iqr, 1.0)
    return (values - median) / iqr


def compute_subject_laguerre(subject_runs: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, Dict[str, Any]]:
    ordered_runs = subject_runs.sort_values(["run_midpoint_from_anchor_hours", "run", "acq"]).reset_index(drop=True)
    clouds = [load_run_point_cloud(run_row, config) for _, run_row in ordered_runs.iterrows()]
    anchor_frame = pd.concat([cloud for cloud in clouds if not cloud.empty], ignore_index=True) if clouds else pd.DataFrame()

    subject = str(ordered_runs["subject"].iloc[0])
    hospital = str(ordered_runs["hospital"].iloc[0])
    label = int(ordered_runs["label"].iloc[0])
    cpc = float(ordered_runs["cpc_numeric"].iloc[0])
    if anchor_frame.empty:
        return anchor_frame, {
            "subject": subject,
            "hospital": hospital,
            "label": label,
            "cpc": cpc,
            "n_runs": int(len(ordered_runs)),
            "sampled_point_count": 0,
            "laguerre_anchor_count": 0,
            "laguerre_valid_fraction": 0.0,
            "laguerre_norm_median": float("nan"),
            "laguerre_norm_p95": float("nan"),
            "laguerre_anisotropy": float("nan"),
            "laguerre_persistence": float("nan"),
            "laguerre_hourly_slope": float("nan"),
            "laguerre_surface_fit_r2_median": float("nan"),
            "laguerre_bending_norm_median": float("nan"),
            "status": "no_sampled_points",
        }

    anchor_frame = anchor_frame.sort_values(["time_hour", "run_key"]).reset_index(drop=True)
    points = anchor_frame[["m_coord", "d_coord", "e_coord"]].to_numpy(dtype=float)
    patch_rows = [fit_local_quadratic_patch(points, idx, config.neighborhood_size) for idx in range(len(anchor_frame))]
    patch_frame = pd.DataFrame(patch_rows)
    anchor_frame = pd.concat([anchor_frame, patch_frame], axis=1)

    valid = anchor_frame[anchor_frame["status"] == "ok"].copy()
    if valid.empty:
        return anchor_frame, {
            "subject": subject,
            "hospital": hospital,
            "label": label,
            "cpc": cpc,
            "n_runs": int(len(ordered_runs)),
            "sampled_point_count": int(len(anchor_frame)),
            "laguerre_anchor_count": 0,
            "laguerre_valid_fraction": 0.0,
            "laguerre_norm_median": float("nan"),
            "laguerre_norm_p95": float("nan"),
            "laguerre_anisotropy": float("nan"),
            "laguerre_persistence": float("nan"),
            "laguerre_hourly_slope": float("nan"),
            "laguerre_surface_fit_r2_median": float("nan"),
            "laguerre_bending_norm_median": float("nan"),
            "status": "no_valid_anchors",
        }

    descriptor_cols = ["bending_norm", "mean_curvature_proxy", "gaussian_curvature_proxy", "anisotropy"]
    valid = valid.sort_values("time_hour").reset_index(drop=True)
    scaled = robust_within_subject_scale(valid[descriptor_cols].to_numpy(dtype=float))

    change_values: List[float] = []
    for idx in range(len(valid)):
        lo = max(0, idx - config.time_change_window)
        hi = min(len(valid), idx + config.time_change_window + 1)
        neighbor_idx = [j for j in range(lo, hi) if j != idx]
        if not neighbor_idx:
            change_values.append(float("nan"))
            continue
        distances = np.linalg.norm(scaled[neighbor_idx] - scaled[idx], axis=1)
        change_values.append(float(np.median(distances)))
    valid["laguerre_change_norm"] = change_values
    anchor_frame = anchor_frame.merge(valid[["time_hour", "run_key", "laguerre_change_norm"]], on=["time_hour", "run_key"], how="left")

    change_arr = pd.to_numeric(valid["laguerre_change_norm"], errors="coerce").to_numpy(dtype=float)
    time_arr = pd.to_numeric(valid["time_hour"], errors="coerce").to_numpy(dtype=float)
    finite_mask = np.isfinite(change_arr) & np.isfinite(time_arr)
    if np.any(finite_mask):
        finite_change = change_arr[finite_mask]
        norm_median = float(np.median(finite_change))
        norm_p95 = float(np.quantile(finite_change, 0.95))
        hotspot = finite_change >= float(np.quantile(finite_change, 0.75))
        persistence = float(np.mean(hotspot[:-1] & hotspot[1:])) if len(hotspot) >= 2 else float("nan")
        slope = float(np.polyfit(time_arr[finite_mask], finite_change, 1)[0]) if np.unique(time_arr[finite_mask]).size >= 2 else float("nan")
    else:
        norm_median = float("nan")
        norm_p95 = float("nan")
        persistence = float("nan")
        slope = float("nan")

    summary = {
        "subject": subject,
        "hospital": hospital,
        "label": label,
        "cpc": cpc,
        "n_runs": int(len(ordered_runs)),
        "sampled_point_count": int(len(anchor_frame)),
        "laguerre_anchor_count": int(len(valid)),
        "laguerre_valid_fraction": float(len(valid) / max(len(anchor_frame), 1)),
        "laguerre_norm_median": norm_median,
        "laguerre_norm_p95": norm_p95,
        "laguerre_anisotropy": float(np.nanmedian(pd.to_numeric(valid["anisotropy"], errors="coerce"))),
        "laguerre_persistence": persistence,
        "laguerre_hourly_slope": slope,
        "laguerre_surface_fit_r2_median": float(np.nanmedian(pd.to_numeric(valid["surface_fit_r2"], errors="coerce"))),
        "laguerre_bending_norm_median": float(np.nanmedian(pd.to_numeric(valid["bending_norm"], errors="coerce"))),
        "status": "ok",
    }
    return anchor_frame, summary


def load_reachability_subject_metrics(config: Config) -> pd.DataFrame:
    frame = pd.read_csv(config.mnps_dir / "patient_timebin_signal_metrics.csv")
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["time_bin"] == config.primary_time_bin].copy()
    frame = frame[frame["cohort_tag"].astype(str) == config.cohort_tag].copy()
    frame = frame[frame["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)])].copy()
    frame = frame[frame["analysis_type"] == "reachability_cones"].copy()
    frame = frame[frame["metric"].astype(str).isin({"tube_d_eff_median", "tube_a_operator_norm_median", "tube_capture_gate_median"})].copy()
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
    specs = [
        ("laguerre_norm_median", "Laguerre change norm median"),
        ("laguerre_norm_p95", "Laguerre change norm p95"),
        ("laguerre_anisotropy", "Laguerre anisotropy"),
        ("laguerre_persistence", "Laguerre persistence"),
        ("laguerre_hourly_slope", "Laguerre hourly slope"),
        ("laguerre_bending_norm_median", "Bending norm median"),
        ("tube_d_eff_median", "Reachability d_eff median"),
        ("tube_a_operator_norm_median", "Reachability A-operator norm median"),
        ("tube_capture_gate_median", "Reachability capture gate median"),
    ]
    rows = [summarize_effect_metric(subject_metrics, metric, label) for metric, label in specs if metric in subject_metrics.columns]
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["abs_cohens_d"] = np.abs(pd.to_numeric(out["cohens_d"], errors="coerce"))
    return out.sort_values(["abs_cohens_d", "direct_auc"], ascending=[False, False], na_position="last").reset_index(drop=True)


def write_summary_markdown(config: Config, subject_pool: pd.DataFrame, selected_subjects: pd.DataFrame, effects: pd.DataFrame) -> str:
    lines = [
        "# Laguerre Pilot Summary",
        "",
        f"Pilot cohort: `{config.cohort_tag}` / `{config.primary_time_bin}` with `{config.subjects_per_group}` selected subjects per endpoint where available.",
        "",
        "## Design",
        "",
        "- Subject selection comes from the existing timeline bundle, but the geometry layer is computed from subject-anchored 3D MNPS coordinates read directly from the referenced H5 files.",
        f"- Maximum sampled MNPS points per run: `{config.max_points_per_run}`",
        f"- Minimum runs with valid coordinate paths per subject: `{config.min_runs}`",
        f"- Local patch neighborhood size: `{config.neighborhood_size}`",
        f"- Temporal change half-window: `{config.time_change_window}`",
        "",
        "## Cohort Triage",
        "",
        f"- eligible CPC1 subjects: {int(((subject_pool['label'] == 1) & subject_pool['eligible_for_pilot']).sum()) if not subject_pool.empty else 0}",
        f"- eligible CPC5 subjects: {int(((subject_pool['label'] == 0) & subject_pool['eligible_for_pilot']).sum()) if not subject_pool.empty else 0}",
        f"- selected CPC1 subjects: {int((selected_subjects['label'] == 1).sum()) if not selected_subjects.empty else 0}",
        f"- selected CPC5 subjects: {int((selected_subjects['label'] == 0).sum()) if not selected_subjects.empty else 0}",
        "",
    ]

    if not selected_subjects.empty:
        lines.extend(["## Selected Subjects", ""])
        for label, title in ((1, "CPC1"), (0, "CPC5")):
            sub = selected_subjects[selected_subjects["label"] == label].copy()
            if not sub.empty:
                lines.append(f"- {title}: {', '.join(sub['subject'].astype(str).tolist())}")
        lines.append("")

    if effects.empty:
        lines.extend(["## Status", "", "No effect-size table could be built from the selected pilot subset.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "## Effect Sizes",
            "",
            "| Metric | CPC1 median | CPC5 median | Cohen's d | Cliff's delta | Mann-Whitney p | Direct AUROC |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for _, row in effects.iterrows():
        lines.append(
            f"| {row['label']} | {row['cpc1_median']:.3f} | {row['cpc5_median']:.3f} | "
            f"{row['cohens_d']:.3f} | {row['cliffs_delta']:.3f} | {row['mannwhitney_p']:.3g} | {row['direct_auc']:.3f} |"
        )

    laguerre_only = effects[effects["metric"].astype(str).str.startswith("laguerre_")].copy()
    baseline = effects[effects["metric"] == "tube_d_eff_median"].copy()
    lines.extend(["", "## Quick Read", ""])
    if not laguerre_only.empty:
        top = laguerre_only.iloc[0]
        lines.append(
            f"- strongest Laguerre pilot metric: `{top['metric']}` with Cohen's d `{top['cohens_d']:.3f}` and direct AUROC `{top['direct_auc']:.3f}`."
        )
    if not baseline.empty:
        base = baseline.iloc[0]
        lines.append(
            f"- reachability reference (`tube_d_eff_median`) shows Cohen's d `{base['cohens_d']:.3f}` and direct AUROC `{base['direct_auc']:.3f}` in the same subset."
        )
    lines.append(
        "- This remains a bounded feasibility screen on a small subset; any apparent separation should be treated as motivation for the next, more exact pass rather than as a manuscript-ready claim."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    config = parse_args()
    ensure_dir(config.output_dir)

    run_frame = load_run_frame(config)
    subject_pool = build_subject_pool(run_frame, config)
    selected_subjects = select_subjects(subject_pool, config)
    if selected_subjects.empty:
        raise ValueError("No eligible subjects were found for the requested pilot settings.")

    selected_run_frame = run_frame[run_frame["subject"].isin(selected_subjects["subject"])].copy()
    anchor_frames: List[pd.DataFrame] = []
    subject_summaries: List[Dict[str, Any]] = []
    for _, group in selected_run_frame.groupby("subject", sort=False):
        anchor_frame, summary = compute_subject_laguerre(group, config)
        anchor_frames.append(anchor_frame)
        subject_summaries.append(summary)

    anchor_metrics = pd.concat(anchor_frames, ignore_index=True) if anchor_frames else pd.DataFrame()
    subject_metrics = pd.DataFrame(subject_summaries)
    subject_metrics = selected_subjects.merge(subject_metrics, on=["subject", "label", "cpc", "hospital"], how="left")

    reachability_metrics = load_reachability_subject_metrics(config)
    if not reachability_metrics.empty:
        subject_metrics = subject_metrics.merge(reachability_metrics, on="subject", how="left")

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
        "neighborhood_size": config.neighborhood_size,
        "time_change_window": config.time_change_window,
        "max_points_per_run": config.max_points_per_run,
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

    print(f"Wrote selected subjects to {config.output_dir / 'pilot_selected_subjects.csv'}")
    print(f"Wrote anchor metrics to {config.output_dir / 'laguerre_anchor_metrics.csv'}")
    print(f"Wrote subject metrics to {config.output_dir / 'laguerre_subject_metrics.csv'}")
    print(f"Wrote effect-size summary to {config.output_dir / 'laguerre_effect_sizes.csv'}")
    print(f"Wrote markdown summary to {config.output_dir / 'laguerre_pilot_summary.md'}")


if __name__ == "__main__":
    main()
