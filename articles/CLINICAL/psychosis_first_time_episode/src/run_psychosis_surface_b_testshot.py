from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence

import h5py
import numpy as np
import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.reachability_core import compute_reachability_cones_from_mnps  # noqa: E402


DEFAULT_CLEANED_ROOT = REPO_ROOT / "data" / "cleaned" / "psychosis_cohort_anchor_20260520"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "psychosis_surface_b_testshot_20260526"
DEFAULT_DATASETS = ("ds003944", "ds003947")
DEFAULT_WORKERS = 8
DEFAULT_MAX_POINTS_PER_RUN = 250
DEFAULT_REACHABILITY_K = 25
DEFAULT_REACHABILITY_HORIZON = 4
DEFAULT_REACHABILITY_SUPER_WINDOW_SIZE = 3
DEFAULT_REACHABILITY_RIDGE_ALPHA = 1e-3
DEFAULT_REACHABILITY_JITTER = 1e-6
DEFAULT_SIGMA_REG_EPS = 1e-6
DEFAULT_SPATIAL_NEIGHBORS = 8
DIST_EPS = 1e-9
SPD_EPS = 1e-12


@dataclass(frozen=True)
class Config:
    cleaned_root: Path
    output_dir: Path
    datasets: tuple[str, ...]
    workers: int
    max_points_per_run: int
    reachability_k: int
    reachability_horizon: int
    reachability_super_window_size: int
    reachability_ridge_alpha: float
    reachability_jitter: float
    sigma_reg_eps: float
    spatial_neighbors: int


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description=(
            "Run a short Surface B-like psychosis pilot on article-local ds003944/ds003947 data "
            "using per-window reachability covariance deformation."
        )
    )
    parser.add_argument("--cleaned-root", type=Path, default=DEFAULT_CLEANED_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--datasets", type=str, default=",".join(DEFAULT_DATASETS))
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--max-points-per-run", type=int, default=DEFAULT_MAX_POINTS_PER_RUN)
    parser.add_argument("--reachability-k", type=int, default=DEFAULT_REACHABILITY_K)
    parser.add_argument("--reachability-horizon", type=int, default=DEFAULT_REACHABILITY_HORIZON)
    parser.add_argument("--reachability-super-window-size", type=int, default=DEFAULT_REACHABILITY_SUPER_WINDOW_SIZE)
    parser.add_argument("--reachability-ridge-alpha", type=float, default=DEFAULT_REACHABILITY_RIDGE_ALPHA)
    parser.add_argument("--reachability-jitter", type=float, default=DEFAULT_REACHABILITY_JITTER)
    parser.add_argument("--sigma-reg-eps", type=float, default=DEFAULT_SIGMA_REG_EPS)
    parser.add_argument("--spatial-neighbors", type=int, default=DEFAULT_SPATIAL_NEIGHBORS)
    args = parser.parse_args()
    datasets = tuple(item.strip() for item in str(args.datasets).split(",") if item.strip())
    return Config(
        cleaned_root=args.cleaned_root,
        output_dir=args.output_dir,
        datasets=datasets,
        workers=max(1, int(args.workers)),
        max_points_per_run=max(50, int(args.max_points_per_run)),
        reachability_k=max(5, int(args.reachability_k)),
        reachability_horizon=max(1, int(args.reachability_horizon)),
        reachability_super_window_size=max(1, int(args.reachability_super_window_size)),
        reachability_ridge_alpha=float(args.reachability_ridge_alpha),
        reachability_jitter=float(args.reachability_jitter),
        sigma_reg_eps=float(args.sigma_reg_eps),
        spatial_neighbors=max(1, int(args.spatial_neighbors)),
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def latest_cleaned_file(cleaned_root: Path, dataset: str, stem: str) -> Path:
    matches = sorted(cleaned_root.glob(f"{dataset}_{stem}_*.parquet"))
    if not matches:
        raise FileNotFoundError(f"No cleaned {stem} file found for {dataset} under {cleaned_root}")
    return matches[-1]


def sample_indices(n_points: int, max_points: int) -> np.ndarray:
    if n_points <= max_points:
        return np.arange(n_points, dtype=int)
    return np.linspace(0, n_points - 1, num=max_points, dtype=int)


def cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    if left.size < 2 or right.size < 2:
        return float("nan")
    left_var = left.var(ddof=1)
    right_var = right.var(ddof=1)
    pooled_var = ((left.size - 1) * left_var + (right.size - 1) * right_var) / (left.size + right.size - 2)
    if not np.isfinite(pooled_var) or pooled_var <= 0:
        return float("nan")
    return float((right.mean() - left.mean()) / np.sqrt(pooled_var))


def cliffs_delta(left: np.ndarray, right: np.ndarray) -> float:
    if left.size == 0 or right.size == 0:
        return float("nan")
    diff = np.subtract.outer(right, left)
    return float((np.sum(diff > 0) - np.sum(diff < 0)) / diff.size)


def regularize_spd(sigma: np.ndarray, eps: float) -> np.ndarray:
    sigma = 0.5 * (sigma + sigma.T)
    trace_term = float(np.trace(sigma)) / float(sigma.shape[0])
    scale = max(abs(trace_term), SPD_EPS)
    return sigma + np.eye(sigma.shape[0], dtype=float) * (eps * scale)


def flatten_symmetric(matrix: np.ndarray) -> np.ndarray:
    return np.asarray(
        [matrix[0, 0], matrix[0, 1], matrix[0, 2], matrix[1, 1], matrix[1, 2], matrix[2, 2]],
        dtype=float,
    )


def spd_log_and_spectrum(sigma: np.ndarray, eps: float) -> tuple[np.ndarray, np.ndarray]:
    sigma_reg = regularize_spd(sigma, eps)
    eigvals, eigvecs = np.linalg.eigh(sigma_reg)
    eigvals = np.clip(eigvals, SPD_EPS, np.inf)
    log_eigvals = np.log(eigvals)
    log_sigma = eigvecs @ np.diag(log_eigvals) @ eigvecs.T
    return log_sigma, log_eigvals


def arcsinh_scale(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return 1.0
    scale = float(np.nanmedian(np.abs(values)))
    return scale if np.isfinite(scale) and scale > DIST_EPS else 1.0


def add_asinh_columns(frame: pd.DataFrame, columns: Sequence[str]) -> tuple[pd.DataFrame, Dict[str, float]]:
    out = frame.copy()
    scales: Dict[str, float] = {}
    for column in columns:
        if column not in out.columns:
            continue
        scale = arcsinh_scale(out[column])
        scales[column] = scale
        out[f"{column}_asinh"] = np.arcsinh(pd.to_numeric(out[column], errors="coerce") / scale)
    return out, scales


def add_residuals(frame: pd.DataFrame, metrics: Sequence[str]) -> tuple[pd.DataFrame, Dict[str, Dict[str, float]]]:
    out = frame.copy()
    diagnostics: Dict[str, Dict[str, float]] = {}
    baseline_cols = ["tube_d_eff_median", "tube_a_operator_norm_median"]
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
            "r2": float(1.0 - ss_res / (ss_tot + DIST_EPS)),
            "n_rows": int(np.sum(mask)),
        }
    return out, diagnostics


def summarize_distribution(values: np.ndarray, prefix: str) -> Dict[str, float]:
    values = np.asarray(values, dtype=float)
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return {f"{prefix}_median": float("nan"), f"{prefix}_p95": float("nan")}
    return {
        f"{prefix}_median": float(np.median(finite)),
        f"{prefix}_p95": float(np.quantile(finite, 0.95)),
    }


def compute_spatial_gradient(coords: np.ndarray, values: np.ndarray, n_neighbors: int) -> np.ndarray:
    out = np.full(len(values), np.nan, dtype=float)
    for idx in range(len(values)):
        dist = np.linalg.norm(coords - coords[idx], axis=1)
        order = np.argsort(dist)
        neighbor_idx = [j for j in order if j != idx][:n_neighbors]
        if not neighbor_idx:
            continue
        grads = [float(np.linalg.norm(values[idx] - values[j]) / (dist[j] + DIST_EPS)) for j in neighbor_idx]
        out[idx] = float(np.median(grads))
    return out


def compute_temporal_gradient(times: np.ndarray, values: np.ndarray) -> np.ndarray:
    out = np.full(len(values), np.nan, dtype=float)
    order = np.argsort(times)
    sorted_times = times[order]
    sorted_values = values[order]
    for idx in range(1, len(order)):
        dt = float(sorted_times[idx] - sorted_times[idx - 1])
        if not np.isfinite(dt) or dt <= 0.0:
            continue
        out[order[idx]] = float(np.linalg.norm(sorted_values[idx] - sorted_values[idx - 1]) / (dt + DIST_EPS))
    return out


def load_run_frame(cleaned_root: Path, dataset: str) -> pd.DataFrame:
    frame = pd.read_parquet(latest_cleaned_file(cleaned_root, dataset, "global_mnps_3d"))
    frame = frame.copy()
    frame["dataset"] = dataset
    frame["subject"] = frame["subject_id"].astype(str)
    frame["run_key"] = (
        frame["subject"].astype(str)
        + "|"
        + frame["session"].fillna("none").astype(str)
        + "|"
        + frame["run"].fillna("none").astype(str)
        + "|"
        + frame["acq"].fillna("none").astype(str)
    )
    frame["group_label"] = frame["medication_group"].astype(str)
    frame["pooled_group"] = np.where(frame["group"].astype(str) == "Control", "Healthy", "FEP")
    return frame


def load_reachability_subject_metrics(cleaned_root: Path, dataset: str) -> pd.DataFrame:
    frame = pd.read_parquet(latest_cleaned_file(cleaned_root, dataset, "reachability_cones")).copy()
    keep = [
        "subject_id",
        "tube_d_eff_median",
        "tube_a_operator_norm_median",
        "tube_capture_gate_median",
        "tube_log_det_median",
        "tube_log_det_mean",
    ]
    present = [column for column in keep if column in frame.columns]
    out = frame[present].copy()
    out = out.rename(columns={"subject_id": "subject"})
    return out.drop_duplicates(subset=["subject"]).reset_index(drop=True)


def load_run_state_series(run_row: pd.Series, config: Config) -> tuple[np.ndarray, np.ndarray]:
    dataset_path = str(run_row["source_dataset_path"])
    h5_path = Path(str(run_row["source_h5_path"]))
    if not dataset_path or not h5_path.exists():
        return np.asarray([], dtype=float), np.asarray([], dtype=float)
    with h5py.File(h5_path, "r") as h5:
        if dataset_path not in h5:
            return np.asarray([], dtype=float), np.asarray([], dtype=float)
        coords = np.asarray(h5[dataset_path], dtype=float)
        if coords.ndim != 2 or coords.shape[1] < 3:
            return np.asarray([], dtype=float), np.asarray([], dtype=float)
        coords = coords[:, :3]
        if "window_start" in h5 and "window_end" in h5:
            starts = np.asarray(h5["window_start"], dtype=float)
            ends = np.asarray(h5["window_end"], dtype=float)
            time = (starts + ends) / 2.0
        elif "time" in h5:
            time = np.asarray(h5["time"], dtype=float)
        else:
            time = np.arange(coords.shape[0], dtype=float)
    limit = min(coords.shape[0], time.shape[0])
    coords = coords[:limit]
    time = time[:limit]
    finite = np.isfinite(coords).all(axis=1) & np.isfinite(time)
    coords = coords[finite]
    time = time[finite]
    if coords.size == 0:
        return np.asarray([], dtype=float), np.asarray([], dtype=float)
    keep_idx = sample_indices(len(coords), config.max_points_per_run)
    return coords[keep_idx], time[keep_idx]


def analyze_run_surface_b(run_row: pd.Series, config: Config) -> pd.DataFrame:
    x, time = load_run_state_series(run_row, config)
    if x.size == 0 or len(x) < max(config.reachability_k + 2, 12):
        return pd.DataFrame()
    results = compute_reachability_cones_from_mnps(
        x=x,
        time=time,
        k=config.reachability_k,
        super_window_size=config.reachability_super_window_size,
        method="ridge",
        alpha_grid=[config.reachability_ridge_alpha],
        cv_folds=5,
        horizon=config.reachability_horizon,
        sigma0=0.0,
        jitter=config.reachability_jitter,
        agg="median",
        cov_estimator="empirical",
        eps=1e-12,
    )
    centers = np.asarray(results["reachability_centers"], dtype=int)
    sigmas = np.asarray(results["sigmas"], dtype=float)
    if sigmas.ndim != 4 or len(centers) == 0:
        return pd.DataFrame()
    sigma_final = sigmas[:, -1, :, :]
    center_coords = x[centers]
    center_time = time[centers]
    rows: List[Dict[str, Any]] = []
    for idx in range(len(centers)):
        sigma = sigma_final[idx]
        if not np.isfinite(sigma).all():
            continue
        try:
            log_sigma, log_eigs = spd_log_and_spectrum(sigma, config.sigma_reg_eps)
        except Exception:
            continue
        flat_log = flatten_symmetric(log_sigma)
        rows.append(
            {
                "dataset": str(run_row["dataset"]),
                "subject": str(run_row["subject"]),
                "run_key": str(run_row["run_key"]),
                "group_label": str(run_row["group_label"]),
                "pooled_group": str(run_row["pooled_group"]),
                "time_sec": float(center_time[idx]),
                "center_m": float(center_coords[idx, 0]),
                "center_d": float(center_coords[idx, 1]),
                "center_e": float(center_coords[idx, 2]),
                "sigma_trace": float(np.trace(sigma)),
                "log_sigma_xx": float(flat_log[0]),
                "log_sigma_xy": float(flat_log[1]),
                "log_sigma_xz": float(flat_log[2]),
                "log_sigma_yy": float(flat_log[3]),
                "log_sigma_yz": float(flat_log[4]),
                "log_sigma_zz": float(flat_log[5]),
                "log_eig_1": float(log_eigs[0]),
                "log_eig_2": float(log_eigs[1]),
                "log_eig_3": float(log_eigs[2]),
            }
        )
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    coords = frame[["center_m", "center_d", "center_e"]].to_numpy(dtype=float)
    times = frame["time_sec"].to_numpy(dtype=float)
    log_sigma_stack = frame[["log_sigma_xx", "log_sigma_xy", "log_sigma_xz", "log_sigma_yy", "log_sigma_yz", "log_sigma_zz"]].to_numpy(dtype=float)
    log_eig_stack = frame[["log_eig_1", "log_eig_2", "log_eig_3"]].to_numpy(dtype=float)
    frame["surface_b_logeuc_spatial_grad"] = compute_spatial_gradient(coords, log_sigma_stack, config.spatial_neighbors)
    frame["surface_b_spectral_spatial_grad"] = compute_spatial_gradient(coords, log_eig_stack, config.spatial_neighbors)
    frame["surface_b_logeuc_temporal_grad"] = compute_temporal_gradient(times, log_sigma_stack)
    frame["surface_b_spectral_temporal_grad"] = compute_temporal_gradient(times, log_eig_stack)
    return frame


def summarize_subject_surface_b(subject_runs: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, Dict[str, Any]]:
    ordered_runs = subject_runs.sort_values(["run", "acq"]).reset_index(drop=True)
    frames = [analyze_run_surface_b(run_row, config) for _, run_row in ordered_runs.iterrows()]
    anchor_frame = pd.concat([frame for frame in frames if not frame.empty], ignore_index=True) if frames else pd.DataFrame()
    base = {
        "dataset": str(ordered_runs["dataset"].iloc[0]),
        "subject": str(ordered_runs["subject"].iloc[0]),
        "group_label": str(ordered_runs["group_label"].iloc[0]),
        "pooled_group": str(ordered_runs["pooled_group"].iloc[0]),
        "n_runs": int(len(ordered_runs)),
    }
    if anchor_frame.empty:
        summary = dict(base)
        summary.update({"surface_b_anchor_count": 0, "status": "no_surface_b_anchors"})
        return anchor_frame, summary
    summary = dict(base)
    summary.update(
        {
            "surface_b_anchor_count": int(len(anchor_frame)),
            "surface_b_sigma_trace_median": float(np.nanmedian(pd.to_numeric(anchor_frame["sigma_trace"], errors="coerce"))),
            "status": "ok",
        }
    )
    metric_prefixes = [
        "surface_b_logeuc_spatial_grad",
        "surface_b_spectral_spatial_grad",
        "surface_b_logeuc_temporal_grad",
        "surface_b_spectral_temporal_grad",
    ]
    for metric in metric_prefixes:
        summary.update(summarize_distribution(pd.to_numeric(anchor_frame[metric], errors="coerce").to_numpy(dtype=float), metric))
    return anchor_frame, summary


def subject_worker(payload: tuple[List[Dict[str, Any]], Config]) -> tuple[pd.DataFrame, Dict[str, Any]]:
    rows, config = payload
    return summarize_subject_surface_b(pd.DataFrame(rows), config)


def run_subject_batch(run_frame: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    payloads = [([*group.to_dict("records")], config) for _, group in run_frame.groupby(["dataset", "subject"], sort=False)]
    anchor_frames: List[pd.DataFrame] = []
    summaries: List[Dict[str, Any]] = []
    if config.workers <= 1:
        for payload in payloads:
            anchor_frame, summary = subject_worker(payload)
            anchor_frames.append(anchor_frame)
            summaries.append(summary)
    else:
        with ProcessPoolExecutor(max_workers=config.workers) as executor:
            futures = [executor.submit(subject_worker, payload) for payload in payloads]
            for future in as_completed(futures):
                anchor_frame, summary = future.result()
                anchor_frames.append(anchor_frame)
                summaries.append(summary)
    anchor_metrics = pd.concat(anchor_frames, ignore_index=True) if anchor_frames else pd.DataFrame()
    subject_metrics = pd.DataFrame(summaries)
    return anchor_metrics, subject_metrics


def summarize_effect_metric(frame: pd.DataFrame, metric: str, label: str, left_group: str, right_group: str) -> Dict[str, Any]:
    values = pd.to_numeric(frame[metric], errors="coerce")
    usable = frame.loc[np.isfinite(values.to_numpy(dtype=float))].copy()
    x = pd.to_numeric(usable[metric], errors="coerce").to_numpy(dtype=float)
    y = usable["contrast_label"].astype(str).to_numpy(dtype=str)
    left = x[y == left_group]
    right = x[y == right_group]
    if x.size == 0 or left.size == 0 or right.size == 0:
        return {
            "metric": metric,
            "label": label,
            "status": "insufficient_groups",
            "left_group": left_group,
            "right_group": right_group,
            "left_n": int(left.size),
            "right_n": int(right.size),
            "left_median": float(np.median(left)) if left.size else float("nan"),
            "right_median": float(np.median(right)) if right.size else float("nan"),
            "cohens_d": float("nan"),
            "cliffs_delta": float("nan"),
            "mannwhitney_p": float("nan"),
            "direct_auc": float("nan"),
        }
    direction = 1.0 if np.median(right) >= np.median(left) else -1.0
    labels = np.where(y == right_group, 1, 0)
    from scipy import stats  # local import
    from sklearn.metrics import roc_auc_score  # local import
    return {
        "metric": metric,
        "label": label,
        "status": "ok",
        "left_group": left_group,
        "right_group": right_group,
        "left_n": int(left.size),
        "right_n": int(right.size),
        "left_median": float(np.median(left)),
        "right_median": float(np.median(right)),
        "delta_median_right_minus_left": float(np.median(right) - np.median(left)),
        "cohens_d": cohens_d(left, right),
        "cliffs_delta": cliffs_delta(left, right),
        "mannwhitney_p": float(stats.mannwhitneyu(left, right, alternative="two-sided").pvalue),
        "direct_auc": float(roc_auc_score(labels, direction * x)),
    }


def build_effect_table(frame: pd.DataFrame, left_group: str, right_group: str) -> pd.DataFrame:
    specs = [
        ("tube_d_eff_median", "Reachability d_eff median"),
        ("tube_a_operator_norm_median", "Reachability A-operator norm median"),
        ("tube_capture_gate_median", "Reachability capture gate median"),
        ("surface_b_logeuc_spatial_grad_median", "Surface B log-Euclidean spatial deformation median"),
        ("surface_b_logeuc_spatial_grad_p95", "Surface B log-Euclidean spatial deformation p95"),
        ("surface_b_spectral_spatial_grad_median", "Surface B spectral spatial deformation median"),
        ("surface_b_spectral_spatial_grad_p95", "Surface B spectral spatial deformation p95"),
        ("surface_b_logeuc_temporal_grad_median", "Surface B log-Euclidean temporal deformation median"),
        ("surface_b_logeuc_temporal_grad_p95", "Surface B log-Euclidean temporal deformation p95"),
        ("surface_b_spectral_temporal_grad_median", "Surface B spectral temporal deformation median"),
        ("surface_b_spectral_temporal_grad_p95", "Surface B spectral temporal deformation p95"),
    ]
    specs.extend(
        (metric, metric.replace("_resid_reachability", " residualized vs reachability"))
        for metric in frame.columns
        if metric.endswith("_resid_reachability")
    )
    rows = [summarize_effect_metric(frame, metric, label, left_group, right_group) for metric, label in specs if metric in frame.columns]
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["abs_cliffs_delta"] = np.abs(pd.to_numeric(out["cliffs_delta"], errors="coerce"))
    out["abs_cohens_d"] = np.abs(pd.to_numeric(out["cohens_d"], errors="coerce"))
    return out.sort_values(["abs_cliffs_delta", "direct_auc", "abs_cohens_d"], ascending=[False, False, False], na_position="last").reset_index(drop=True)


def build_contrasts(subject_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: List[pd.DataFrame] = []
    contrast_specs = [
        ("Healthy_vs_FEP", "pooled_group", "Healthy", "FEP"),
        ("Healthy_vs_FEP_medicated", "group_label", "Healthy", "FEP medicated"),
        ("Healthy_vs_FEP_unmedicated", "group_label", "Healthy", "FEP unmedicated"),
        ("FEP_medicated_vs_FEP_unmedicated", "group_label", "FEP unmedicated", "FEP medicated"),
    ]
    for dataset in sorted(subject_metrics["dataset"].dropna().astype(str).unique()):
        dataset_frame = subject_metrics[subject_metrics["dataset"].astype(str) == dataset].copy()
        for contrast_name, column, left_group, right_group in contrast_specs:
            sub = dataset_frame[dataset_frame[column].astype(str).isin([left_group, right_group])].copy()
            if sub.empty:
                continue
            sub["contrast_name"] = contrast_name
            sub["contrast_column"] = column
            sub["contrast_label"] = sub[column].astype(str)
            sub["left_group"] = left_group
            sub["right_group"] = right_group
            rows.append(sub)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def write_summary_markdown(summary_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Psychosis Surface B Testshot",
        "",
        "Short article-local pilot using per-window reachability covariance deformation on raw psychosis H5 trajectories.",
        "",
    ]
    if not summary_rows:
        lines.extend(["No contrasts were estimable.", ""])
        return "\n".join(lines)
    for row in summary_rows:
        lines.extend(
            [
                f"## {row['dataset']} / {row['contrast_name']}",
                "",
                f"- groups: `{row['left_group']}` vs `{row['right_group']}`",
                f"- n: `{row['left_n']}` vs `{row['right_n']}`",
                f"- top raw Surface B: `{row['top_raw_metric']}` (Cliff's delta `{row['top_raw_cliffs_delta']:.3f}`, AUROC `{row['top_raw_auc']:.3f}`)",
                f"- top residualized Surface B: `{row['top_resid_metric']}` (Cliff's delta `{row['top_resid_cliffs_delta']:.3f}`, AUROC `{row['top_resid_auc']:.3f}`)",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    config = parse_args()
    ensure_dir(config.output_dir)

    run_frames = [load_run_frame(config.cleaned_root, dataset) for dataset in config.datasets]
    run_frame = pd.concat(run_frames, ignore_index=True)
    anchor_metrics, subject_metrics = run_subject_batch(run_frame, config)

    reachability_frames = [load_reachability_subject_metrics(config.cleaned_root, dataset).assign(dataset=dataset) for dataset in config.datasets]
    reachability_metrics = pd.concat(reachability_frames, ignore_index=True)
    subject_metrics = subject_metrics.merge(reachability_metrics, on=["dataset", "subject"], how="left")

    metric_cols = [
        "surface_b_logeuc_spatial_grad_median",
        "surface_b_logeuc_spatial_grad_p95",
        "surface_b_spectral_spatial_grad_median",
        "surface_b_spectral_spatial_grad_p95",
        "surface_b_logeuc_temporal_grad_median",
        "surface_b_logeuc_temporal_grad_p95",
        "surface_b_spectral_temporal_grad_median",
        "surface_b_spectral_temporal_grad_p95",
    ]
    subject_metrics, asinh_scales = add_asinh_columns(subject_metrics, metric_cols)
    residual_inputs = [f"{metric}_asinh" for metric in metric_cols if f"{metric}_asinh" in subject_metrics.columns]
    subject_metrics, residual_models = add_residuals(subject_metrics, residual_inputs)

    contrast_frame = build_contrasts(subject_metrics)
    effect_tables: List[pd.DataFrame] = []
    summary_rows: list[dict[str, Any]] = []
    for (dataset, contrast_name, left_group, right_group), sub in contrast_frame.groupby(
        ["dataset", "contrast_name", "left_group", "right_group"],
        sort=False,
    ):
        effects = build_effect_table(sub, str(left_group), str(right_group))
        if effects.empty:
            continue
        effects.insert(0, "dataset", str(dataset))
        effects.insert(1, "contrast_name", str(contrast_name))
        effect_tables.append(effects)
        raw_surface_b = effects[
            effects["metric"].astype(str).str.startswith("surface_b_")
            & ~effects["metric"].astype(str).str.contains("_resid_reachability")
        ].copy()
        resid_surface_b = effects[effects["metric"].astype(str).str.endswith("_resid_reachability")].copy()
        if raw_surface_b.empty or resid_surface_b.empty:
            continue
        top_raw = raw_surface_b.iloc[0]
        top_resid = resid_surface_b.iloc[0]
        summary_rows.append(
            {
                "dataset": str(dataset),
                "contrast_name": str(contrast_name),
                "left_group": str(left_group),
                "right_group": str(right_group),
                "left_n": int(top_raw["left_n"]),
                "right_n": int(top_raw["right_n"]),
                "top_raw_metric": str(top_raw["metric"]),
                "top_raw_cliffs_delta": float(top_raw["cliffs_delta"]),
                "top_raw_auc": float(top_raw["direct_auc"]),
                "top_resid_metric": str(top_resid["metric"]),
                "top_resid_cliffs_delta": float(top_resid["cliffs_delta"]),
                "top_resid_auc": float(top_resid["direct_auc"]),
            }
        )

    effect_table = pd.concat(effect_tables, ignore_index=True) if effect_tables else pd.DataFrame()
    summary_df = pd.DataFrame(summary_rows)
    summary_text = write_summary_markdown(summary_rows)
    manifest = {
        "cleaned_root": str(config.cleaned_root),
        "datasets": list(config.datasets),
        "workers": config.workers,
        "max_points_per_run": config.max_points_per_run,
        "reachability_k": config.reachability_k,
        "reachability_horizon": config.reachability_horizon,
        "reachability_super_window_size": config.reachability_super_window_size,
        "reachability_ridge_alpha": config.reachability_ridge_alpha,
        "reachability_jitter": config.reachability_jitter,
        "sigma_reg_eps": config.sigma_reg_eps,
        "spatial_neighbors": config.spatial_neighbors,
        "asinh_scales": asinh_scales,
    }

    anchor_metrics.to_csv(config.output_dir / "psychosis_surface_b_anchor_metrics.csv", index=False)
    subject_metrics.to_csv(config.output_dir / "psychosis_surface_b_subject_metrics.csv", index=False)
    contrast_frame.to_csv(config.output_dir / "psychosis_surface_b_contrast_frame.csv", index=False)
    effect_table.to_csv(config.output_dir / "psychosis_surface_b_effect_sizes.csv", index=False)
    summary_df.to_csv(config.output_dir / "psychosis_surface_b_summary.csv", index=False)
    (config.output_dir / "psychosis_surface_b_summary.md").write_text(summary_text, encoding="utf-8")
    (config.output_dir / "psychosis_surface_b_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (config.output_dir / "psychosis_surface_b_residual_models.json").write_text(json.dumps(residual_models, indent=2), encoding="utf-8")

    print(f"Wrote psychosis Surface B subject metrics to {config.output_dir / 'psychosis_surface_b_subject_metrics.csv'}")
    print(f"Wrote psychosis Surface B effects to {config.output_dir / 'psychosis_surface_b_effect_sizes.csv'}")
    print(f"Wrote psychosis Surface B summary to {config.output_dir / 'psychosis_surface_b_summary.md'}")


if __name__ == "__main__":
    main()
