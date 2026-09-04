from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import h5py
import numpy as np
import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.reachability_core import compute_reachability_cones_from_mnps  # noqa: E402

from laguerre_subject_pilot_v2 import (  # noqa: E402
    build_subject_pool,
    cliffs_delta,
    cohens_d,
    load_reachability_subject_metrics,
    load_run_frame,
    sample_indices,
    select_subjects,
)


DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "laguerre_surface_b_v2_20260525_part2_fullbatch"
DEFAULT_PRIMARY_TIME_BIN = "0_12h"
DEFAULT_COHORT_TAG = "part2"
DEFAULT_GOOD_CPC = 1
DEFAULT_POOR_CPC = 5
DEFAULT_SUBJECTS_PER_GROUP = 0
DEFAULT_MIN_RUNS = 8
DEFAULT_MAX_POINTS_PER_RUN = 300
DEFAULT_SPATIAL_NEIGHBORS = 8
DEFAULT_WORKERS = 8
DEFAULT_REACHABILITY_K = 25
DEFAULT_REACHABILITY_HORIZON = 4
DEFAULT_REACHABILITY_SUPER_WINDOW_SIZE = 3
DEFAULT_REACHABILITY_RIDGE_ALPHA = 1e-3
DEFAULT_REACHABILITY_JITTER = 1e-6
DEFAULT_SIGMA_REG_EPS = 1e-6
DIST_EPS = 1e-9
SPD_EPS = 1e-12


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
    spatial_neighbors: int
    workers: int
    reachability_k: int
    reachability_horizon: int
    reachability_super_window_size: int
    reachability_ridge_alpha: float
    reachability_jitter: float
    sigma_reg_eps: float


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description=(
            "Run a minimal Surface B v2 coma pilot with relative-trace SPD regularization "
            "and arcsinh-stabilized residualization."
        )
    )
    parser.add_argument("--timeline-dir", type=Path, default=REPO_ROOT / "articles" / "CLINICAL" / "comatose_ndt" / "results" / "timeline_analysis_20260525_combined_cpc15_primary12h")
    parser.add_argument("--mnps-dir", type=Path, default=REPO_ROOT / "articles" / "CLINICAL" / "comatose_ndt" / "results" / "mnps_summary_20260525_combined_cpc15_primary12h")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--primary-time-bin", type=str, default=DEFAULT_PRIMARY_TIME_BIN)
    parser.add_argument("--cohort-tag", type=str, default=DEFAULT_COHORT_TAG)
    parser.add_argument("--good-cpc", type=int, default=DEFAULT_GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=DEFAULT_POOR_CPC)
    parser.add_argument("--subjects-per-group", type=int, default=DEFAULT_SUBJECTS_PER_GROUP)
    parser.add_argument("--min-runs", type=int, default=DEFAULT_MIN_RUNS)
    parser.add_argument("--max-points-per-run", type=int, default=DEFAULT_MAX_POINTS_PER_RUN)
    parser.add_argument("--spatial-neighbors", type=int, default=DEFAULT_SPATIAL_NEIGHBORS)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--reachability-k", type=int, default=DEFAULT_REACHABILITY_K)
    parser.add_argument("--reachability-horizon", type=int, default=DEFAULT_REACHABILITY_HORIZON)
    parser.add_argument("--reachability-super-window-size", type=int, default=DEFAULT_REACHABILITY_SUPER_WINDOW_SIZE)
    parser.add_argument("--reachability-ridge-alpha", type=float, default=DEFAULT_REACHABILITY_RIDGE_ALPHA)
    parser.add_argument("--reachability-jitter", type=float, default=DEFAULT_REACHABILITY_JITTER)
    parser.add_argument("--sigma-reg-eps", type=float, default=DEFAULT_SIGMA_REG_EPS)
    args = parser.parse_args()
    return Config(
        timeline_dir=args.timeline_dir,
        mnps_dir=args.mnps_dir,
        output_dir=args.output_dir,
        primary_time_bin=args.primary_time_bin,
        cohort_tag=args.cohort_tag,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        subjects_per_group=max(0, int(args.subjects_per_group)),
        min_runs=max(1, int(args.min_runs)),
        max_points_per_run=max(50, int(args.max_points_per_run)),
        spatial_neighbors=max(1, int(args.spatial_neighbors)),
        workers=max(1, int(args.workers)),
        reachability_k=max(5, int(args.reachability_k)),
        reachability_horizon=max(1, int(args.reachability_horizon)),
        reachability_super_window_size=max(1, int(args.reachability_super_window_size)),
        reachability_ridge_alpha=float(args.reachability_ridge_alpha),
        reachability_jitter=float(args.reachability_jitter),
        sigma_reg_eps=float(args.sigma_reg_eps),
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_run_state_series(run_row: pd.Series, config: Config) -> tuple[np.ndarray, np.ndarray]:
    dataset_path = str(run_row["source_dataset_path"])
    processed_h5_path = Path(str(run_row["processed_h5_path"]))
    if not dataset_path or not processed_h5_path.exists():
        return np.asarray([], dtype=float), np.asarray([], dtype=float)

    with h5py.File(processed_h5_path, "r") as h5:
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


def regularize_spd(sigma: np.ndarray, eps: float) -> np.ndarray:
    sigma = 0.5 * (sigma + sigma.T)
    trace_term = float(np.trace(sigma)) / float(sigma.shape[0])
    scale = max(abs(trace_term), SPD_EPS)
    return sigma + np.eye(sigma.shape[0], dtype=float) * (eps * scale)


def spd_log_and_spectrum(sigma: np.ndarray, eps: float) -> tuple[np.ndarray, np.ndarray]:
    sigma_reg = regularize_spd(sigma, eps)
    eigvals, eigvecs = np.linalg.eigh(sigma_reg)
    eigvals = np.clip(eigvals, SPD_EPS, np.inf)
    log_eigvals = np.log(eigvals)
    log_sigma = eigvecs @ np.diag(log_eigvals) @ eigvecs.T
    return log_sigma, log_eigvals


def flatten_symmetric(matrix: np.ndarray) -> np.ndarray:
    return np.asarray(
        [matrix[0, 0], matrix[0, 1], matrix[0, 2], matrix[1, 1], matrix[1, 2], matrix[2, 2]],
        dtype=float,
    )


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


def compute_spatial_gradients(frame: pd.DataFrame, metric_prefix: str, n_neighbors: int) -> np.ndarray:
    coords = frame[["center_m", "center_d", "center_e"]].to_numpy(dtype=float)
    values = frame[
        [f"{metric_prefix}_xx", f"{metric_prefix}_xy", f"{metric_prefix}_xz", f"{metric_prefix}_yy", f"{metric_prefix}_yz", f"{metric_prefix}_zz"]
    ].to_numpy(dtype=float)
    out = np.full(len(frame), np.nan, dtype=float)
    for idx in range(len(frame)):
        dist = np.linalg.norm(coords - coords[idx], axis=1)
        order = np.argsort(dist)
        neighbor_idx = [j for j in order if j != idx][:n_neighbors]
        if not neighbor_idx:
            continue
        grads = [float(np.linalg.norm(values[idx] - values[j]) / (dist[j] + DIST_EPS)) for j in neighbor_idx]
        out[idx] = float(np.median(grads))
    return out


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
    center_time_h = (float(run_row["run_start_from_anchor_sec"]) + time[centers]) / 3600.0
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
                "subject": str(run_row["subject"]),
                "run_key": str(run_row["run_key"]),
                "hospital": str(run_row["hospital"]),
                "label": int(run_row["label"]),
                "cpc": float(run_row["cpc_numeric"]),
                "time_hour": float(center_time_h[idx]),
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
    frame["surface_b_logeuc_grad"] = compute_spatial_gradients(frame, "log_sigma", config.spatial_neighbors)
    log_eigs = frame[["log_eig_1", "log_eig_2", "log_eig_3"]].to_numpy(dtype=float)
    coords = frame[["center_m", "center_d", "center_e"]].to_numpy(dtype=float)
    spectral = np.full(len(frame), np.nan, dtype=float)
    for idx in range(len(frame)):
        dist = np.linalg.norm(coords - coords[idx], axis=1)
        order = np.argsort(dist)
        neighbor_idx = [j for j in order if j != idx][: config.spatial_neighbors]
        if not neighbor_idx:
            continue
        grads = [float(np.linalg.norm(log_eigs[idx] - log_eigs[j]) / (dist[j] + DIST_EPS)) for j in neighbor_idx]
        spectral[idx] = float(np.median(grads))
    frame["surface_b_spectral_grad"] = spectral
    return frame


def summarize_subject_surface_b(subject_runs: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, Dict[str, Any]]:
    ordered_runs = subject_runs.sort_values(["run_midpoint_from_anchor_hours", "run", "acq"]).reset_index(drop=True)
    frames = [analyze_run_surface_b(run_row, config) for _, run_row in ordered_runs.iterrows()]
    anchor_frame = pd.concat([frame for frame in frames if not frame.empty], ignore_index=True) if frames else pd.DataFrame()
    base = {
        "subject": str(ordered_runs["subject"].iloc[0]),
        "hospital": str(ordered_runs["hospital"].iloc[0]),
        "label": int(ordered_runs["label"].iloc[0]),
        "cpc": float(ordered_runs["cpc_numeric"].iloc[0]),
        "n_runs": int(len(ordered_runs)),
    }
    if anchor_frame.empty:
        summary = dict(base)
        summary.update(
            {
                "surface_b_anchor_count": 0,
                "surface_b_sigma_trace_median": float("nan"),
                "surface_b_logeuc_grad_median": float("nan"),
                "surface_b_logeuc_grad_p95": float("nan"),
                "surface_b_spectral_grad_median": float("nan"),
                "surface_b_spectral_grad_p95": float("nan"),
                "status": "no_surface_b_anchors",
            }
        )
        return anchor_frame, summary
    summary = dict(base)
    summary.update(
        {
            "surface_b_anchor_count": int(len(anchor_frame)),
            "surface_b_sigma_trace_median": float(np.nanmedian(pd.to_numeric(anchor_frame["sigma_trace"], errors="coerce"))),
            "status": "ok",
        }
    )
    summary.update(
        summarize_distribution(pd.to_numeric(anchor_frame["surface_b_logeuc_grad"], errors="coerce").to_numpy(dtype=float), "surface_b_logeuc_grad")
    )
    summary.update(
        summarize_distribution(pd.to_numeric(anchor_frame["surface_b_spectral_grad"], errors="coerce").to_numpy(dtype=float), "surface_b_spectral_grad")
    )
    return anchor_frame, summary


def subject_worker(payload: tuple[List[Dict[str, Any]], Config]) -> tuple[pd.DataFrame, Dict[str, Any]]:
    rows, config = payload
    return summarize_subject_surface_b(pd.DataFrame(rows), config)


def run_subject_batch(selected_run_frame: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    payloads = [([*group.to_dict("records")], config) for _, group in selected_run_frame.groupby("subject", sort=False)]
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
    return (
        pd.concat(anchor_frames, ignore_index=True) if anchor_frames else pd.DataFrame(),
        pd.DataFrame(summaries),
    )


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
    mannwhitney = pd.Series(good).combine_first(pd.Series(dtype=float))  # noop for consistency
    _ = mannwhitney
    from scipy import stats  # local import to keep patch simple
    mw = stats.mannwhitneyu(good, poor, alternative="two-sided")
    from sklearn.metrics import roc_auc_score  # local import to keep patch simple
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
        "mannwhitney_p": float(mw.pvalue),
        "direct_auc": float(roc_auc_score(y, score)),
    }


def build_effect_table(subject_metrics: pd.DataFrame) -> pd.DataFrame:
    specs = [
        ("tube_d_eff_median", "Reachability d_eff median"),
        ("tube_a_operator_norm_median", "Reachability A-operator norm median"),
        ("tube_capture_gate_median", "Reachability capture gate median"),
        ("surface_b_logeuc_grad_median", "Surface B log-Euclidean deformation median"),
        ("surface_b_logeuc_grad_p95", "Surface B log-Euclidean deformation p95"),
        ("surface_b_spectral_grad_median", "Surface B spectral deformation median"),
        ("surface_b_spectral_grad_p95", "Surface B spectral deformation p95"),
        ("surface_b_logeuc_grad_median_asinh", "Surface B log-Euclidean deformation median (asinh)"),
        ("surface_b_logeuc_grad_p95_asinh", "Surface B log-Euclidean deformation p95 (asinh)"),
        ("surface_b_spectral_grad_median_asinh", "Surface B spectral deformation median (asinh)"),
        ("surface_b_spectral_grad_p95_asinh", "Surface B spectral deformation p95 (asinh)"),
    ]
    specs.extend(
        (metric, metric.replace("_resid_reachability", " residualized vs reachability"))
        for metric in subject_metrics.columns
        if metric.endswith("_resid_reachability")
    )
    rows = [summarize_effect_metric(subject_metrics, metric, label) for metric, label in specs if metric in subject_metrics.columns]
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["abs_cliffs_delta"] = np.abs(pd.to_numeric(out["cliffs_delta"], errors="coerce"))
    out["abs_cohens_d"] = np.abs(pd.to_numeric(out["cohens_d"], errors="coerce"))
    return out.sort_values(["abs_cliffs_delta", "direct_auc", "abs_cohens_d"], ascending=[False, False, False], na_position="last").reset_index(drop=True)


def write_summary_markdown(config: Config, selected_subjects: pd.DataFrame, effects: pd.DataFrame, asinh_scales: Dict[str, float]) -> str:
    lines = [
        "# Laguerre Surface B Pilot V2",
        "",
        "This minimal v2 adds relative-trace SPD regularization and arcsinh-stabilized residualization.",
        "",
        "## Batch",
        "",
        f"- cohort: `{config.cohort_tag}` / `{config.primary_time_bin}`",
        f"- selected CPC1: {int((selected_subjects['label'] == 1).sum()) if not selected_subjects.empty else 0}",
        f"- selected CPC5: {int((selected_subjects['label'] == 0).sum()) if not selected_subjects.empty else 0}",
        f"- workers: `{config.workers}`",
        f"- sigma_reg_eps: `{config.sigma_reg_eps}`",
        "",
        "## Asinh Scales",
        "",
    ]
    for key, value in asinh_scales.items():
        lines.append(f"- `{key}` scale: `{value:.6g}`")
    lines.append("")
    if effects.empty:
        lines.extend(["## Status", "", "No Surface B effect table could be built.", ""])
        return "\n".join(lines)
    lines.extend(
        [
            "## Effect Sizes",
            "",
            "| Metric | CPC1 median | CPC5 median | Cliff's delta | Cohen's d | Mann-Whitney p | Direct AUROC |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for _, row in effects.head(18).iterrows():
        lines.append(
            f"| {row['label']} | {row['cpc1_median']:.3f} | {row['cpc5_median']:.3f} | "
            f"{row['cliffs_delta']:.3f} | {row['cohens_d']:.3f} | {row['mannwhitney_p']:.3g} | {row['direct_auc']:.3f} |"
        )
    lines.append("")
    lines.append("- In this v2 table, Cliff's delta is the more trustworthy primary effect size because the raw Surface B distributions are heavy-tailed.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    config = parse_args()
    ensure_dir(config.output_dir)

    run_frame = load_run_frame(config)
    subject_pool = build_subject_pool(run_frame, config)
    selected_subjects = select_subjects(subject_pool, config)
    if selected_subjects.empty:
        raise ValueError("No eligible subjects were found for Surface B v2.")

    selected_run_frame = run_frame[run_frame["subject"].isin(selected_subjects["subject"])].copy()
    anchor_metrics, subject_metrics = run_subject_batch(selected_run_frame, config)
    subject_metrics = selected_subjects.merge(subject_metrics, on=["subject", "label", "cpc", "hospital"], how="left")

    reachability_metrics = load_reachability_subject_metrics(config)
    if not reachability_metrics.empty:
        subject_metrics = subject_metrics.merge(reachability_metrics, on="subject", how="left")

    transform_cols = [
        "surface_b_logeuc_grad_median",
        "surface_b_logeuc_grad_p95",
        "surface_b_spectral_grad_median",
        "surface_b_spectral_grad_p95",
    ]
    subject_metrics, asinh_scales = add_asinh_columns(subject_metrics, transform_cols)
    residual_input_metrics = [f"{column}_asinh" for column in transform_cols if f"{column}_asinh" in subject_metrics.columns]
    subject_metrics, residual_models = add_residuals(subject_metrics, residual_input_metrics)

    effects = build_effect_table(subject_metrics)
    summary_text = write_summary_markdown(config, selected_subjects, effects, asinh_scales)
    manifest = {
        "timeline_dir": str(config.timeline_dir),
        "mnps_dir": str(config.mnps_dir),
        "output_dir": str(config.output_dir),
        "primary_time_bin": config.primary_time_bin,
        "cohort_tag": config.cohort_tag,
        "selected_subjects_cpc1": int((selected_subjects["label"] == 1).sum()) if not selected_subjects.empty else 0,
        "selected_subjects_cpc5": int((selected_subjects["label"] == 0).sum()) if not selected_subjects.empty else 0,
        "workers": config.workers,
        "sigma_reg_eps": config.sigma_reg_eps,
        "asinh_scales": asinh_scales,
    }

    selected_subjects.to_csv(config.output_dir / "pilot_selected_subjects.csv", index=False)
    anchor_metrics.to_csv(config.output_dir / "surface_b_anchor_metrics.csv", index=False)
    subject_metrics.to_csv(config.output_dir / "surface_b_subject_metrics.csv", index=False)
    effects.to_csv(config.output_dir / "surface_b_effect_sizes.csv", index=False)
    (config.output_dir / "surface_b_summary.md").write_text(summary_text, encoding="utf-8")
    (config.output_dir / "surface_b_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (config.output_dir / "surface_b_residual_models.json").write_text(json.dumps(residual_models, indent=2), encoding="utf-8")

    print(f"Wrote Surface B v2 subject metrics to {config.output_dir / 'surface_b_subject_metrics.csv'}")
    print(f"Wrote Surface B v2 effects to {config.output_dir / 'surface_b_effect_sizes.csv'}")
    print(f"Wrote Surface B v2 summary to {config.output_dir / 'surface_b_summary.md'}")


if __name__ == "__main__":
    main()
