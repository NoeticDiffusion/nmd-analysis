from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import h5py
import numpy as np
import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.reachability_cones import ReachabilityConfig  # noqa: E402
from ndt_analysis.reachability_core import compute_reachability_cones_from_mnps  # noqa: E402

from laguerre_subject_pilot_v2 import (  # noqa: E402
    add_reachability_residuals,
    build_subject_pool,
    load_reachability_subject_metrics,
    load_run_frame,
    select_subjects,
    summarize_distribution,
    summarize_effect_metric,
    sample_indices,
)


DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "laguerre_surface_b_20260525_part2_fullbatch"
DEFAULT_PRIMARY_TIME_BIN = "0_12h"
DEFAULT_COHORT_TAG = "part2"
DEFAULT_GOOD_CPC = 1
DEFAULT_POOR_CPC = 5
DEFAULT_SUBJECTS_PER_GROUP = 0
DEFAULT_MIN_RUNS = 8
DEFAULT_MAX_POINTS_PER_RUN = 400
DEFAULT_GRADIENT_NEIGHBORS = 8
DEFAULT_WORKERS = 8
SPD_EPS = 1e-8
DIST_EPS = 1e-9


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
    gradient_neighbors: int
    workers: int
    reachability_k: int
    reachability_horizon: int
    reachability_super_window_size: int
    reachability_ridge_alpha: float
    reachability_jitter: float


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description=(
            "Run a Surface B coma pilot using per-window reachability covariance deformation "
            "rather than MNPS point-cloud patch geometry."
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
    parser.add_argument("--gradient-neighbors", type=int, default=DEFAULT_GRADIENT_NEIGHBORS)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--reachability-k", type=int, default=25)
    parser.add_argument("--reachability-horizon", type=int, default=4)
    parser.add_argument("--reachability-super-window-size", type=int, default=3)
    parser.add_argument("--reachability-ridge-alpha", type=float, default=1e-3)
    parser.add_argument("--reachability-jitter", type=float, default=1e-6)
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
        gradient_neighbors=max(1, int(args.gradient_neighbors)),
        workers=max(1, int(args.workers)),
        reachability_k=max(5, int(args.reachability_k)),
        reachability_horizon=max(1, int(args.reachability_horizon)),
        reachability_super_window_size=max(1, int(args.reachability_super_window_size)),
        reachability_ridge_alpha=float(args.reachability_ridge_alpha),
        reachability_jitter=float(args.reachability_jitter),
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


def spd_log_and_spectrum(sigma: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    sigma = 0.5 * (sigma + sigma.T)
    eigvals, eigvecs = np.linalg.eigh(sigma)
    eigvals = np.clip(eigvals, SPD_EPS, np.inf)
    log_eigvals = np.log(eigvals)
    log_sigma = eigvecs @ np.diag(log_eigvals) @ eigvecs.T
    return log_sigma, log_eigvals


def compute_surface_b_gradients(frame: pd.DataFrame, config: Config) -> pd.DataFrame:
    if frame.empty:
        return frame
    coords = frame[["center_m", "center_d", "center_e"]].to_numpy(dtype=float)
    log_sigma_stack = frame[
        [
            "log_sigma_xx",
            "log_sigma_xy",
            "log_sigma_xz",
            "log_sigma_yy",
            "log_sigma_yz",
            "log_sigma_zz",
        ]
    ].to_numpy(dtype=float)
    log_eigs = frame[["log_eig_1", "log_eig_2", "log_eig_3"]].to_numpy(dtype=float)
    full_grad = np.full(len(frame), np.nan, dtype=float)
    spectral_grad = np.full(len(frame), np.nan, dtype=float)
    for idx in range(len(frame)):
        dist = np.linalg.norm(coords - coords[idx], axis=1)
        order = np.argsort(dist)
        neighbor_idx = [j for j in order if j != idx][: config.gradient_neighbors]
        if not neighbor_idx:
            continue
        full_vals: List[float] = []
        spectral_vals: List[float] = []
        for jdx in neighbor_idx:
            full_vals.append(float(np.linalg.norm(log_sigma_stack[idx] - log_sigma_stack[jdx]) / (dist[jdx] + DIST_EPS)))
            spectral_vals.append(float(np.linalg.norm(log_eigs[idx] - log_eigs[jdx]) / (dist[jdx] + DIST_EPS)))
        full_grad[idx] = float(np.median(full_vals))
        spectral_grad[idx] = float(np.median(spectral_vals))
    out = frame.copy()
    out["surface_b_logeuc_grad"] = full_grad
    out["surface_b_spectral_grad"] = spectral_grad
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
            log_sigma, log_eigs = spd_log_and_spectrum(sigma)
        except Exception:
            continue
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
                "log_sigma_xx": float(log_sigma[0, 0]),
                "log_sigma_xy": float(log_sigma[0, 1]),
                "log_sigma_xz": float(log_sigma[0, 2]),
                "log_sigma_yy": float(log_sigma[1, 1]),
                "log_sigma_yz": float(log_sigma[1, 2]),
                "log_sigma_zz": float(log_sigma[2, 2]),
                "log_eig_1": float(log_eigs[0]),
                "log_eig_2": float(log_eigs[1]),
                "log_eig_3": float(log_eigs[2]),
            }
        )
    if not rows:
        return pd.DataFrame()
    return compute_surface_b_gradients(pd.DataFrame(rows), config)


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
                "surface_b_logeuc_grad_median": float("nan"),
                "surface_b_logeuc_grad_p95": float("nan"),
                "surface_b_spectral_grad_median": float("nan"),
                "surface_b_spectral_grad_p95": float("nan"),
                "surface_b_sigma_trace_median": float("nan"),
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
        summarize_distribution(
            pd.to_numeric(anchor_frame["surface_b_logeuc_grad"], errors="coerce").to_numpy(dtype=float),
            "surface_b_logeuc_grad",
        )
    )
    summary.update(
        summarize_distribution(
            pd.to_numeric(anchor_frame["surface_b_spectral_grad"], errors="coerce").to_numpy(dtype=float),
            "surface_b_spectral_grad",
        )
    )
    return anchor_frame, summary


def subject_worker(payload: tuple[List[Dict[str, Any]], Config]) -> tuple[pd.DataFrame, Dict[str, Any]]:
    rows, config = payload
    subject_runs = pd.DataFrame(rows)
    return summarize_subject_surface_b(subject_runs, config)


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

    anchor_metrics = pd.concat(anchor_frames, ignore_index=True) if anchor_frames else pd.DataFrame()
    subject_metrics = pd.DataFrame(summaries)
    return anchor_metrics, subject_metrics


def build_effect_table(subject_metrics: pd.DataFrame) -> pd.DataFrame:
    specs = [
        ("tube_d_eff_median", "Reachability d_eff median"),
        ("tube_a_operator_norm_median", "Reachability A-operator norm median"),
        ("tube_capture_gate_median", "Reachability capture gate median"),
        ("surface_b_logeuc_grad_median", "Surface B log-Euclidean deformation median"),
        ("surface_b_logeuc_grad_p95", "Surface B log-Euclidean deformation p95"),
        ("surface_b_spectral_grad_median", "Surface B spectral deformation median"),
        ("surface_b_spectral_grad_p95", "Surface B spectral deformation p95"),
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
    out["abs_cohens_d"] = np.abs(pd.to_numeric(out["cohens_d"], errors="coerce"))
    return out.sort_values(["abs_cohens_d", "direct_auc"], ascending=[False, False], na_position="last").reset_index(drop=True)


def write_summary_markdown(config: Config, subject_pool: pd.DataFrame, selected_subjects: pd.DataFrame, effects: pd.DataFrame) -> str:
    lines = [
        "# Laguerre Surface B Pilot",
        "",
        "This pilot estimates deformation of per-window reachability covariance objects rather than point-cloud patch curvature.",
        "",
        "## Batch",
        "",
        f"- cohort: `{config.cohort_tag}` / `{config.primary_time_bin}`",
        f"- selected CPC1: {int((selected_subjects['label'] == 1).sum()) if not selected_subjects.empty else 0}",
        f"- selected CPC5: {int((selected_subjects['label'] == 0).sum()) if not selected_subjects.empty else 0}",
        f"- workers: `{config.workers}`",
        f"- max_points_per_run: `{config.max_points_per_run}`",
        f"- reachability_k: `{config.reachability_k}`",
        f"- reachability_horizon: `{config.reachability_horizon}`",
        "",
    ]
    if effects.empty:
        lines.extend(["## Status", "", "No Surface B effect table could be built.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "## Effect Sizes",
            "",
            "| Metric | CPC1 median | CPC5 median | Cohen's d | Cliff's delta | Mann-Whitney p | Direct AUROC |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for _, row in effects.head(16).iterrows():
        lines.append(
            f"| {row['label']} | {row['cpc1_median']:.3f} | {row['cpc5_median']:.3f} | "
            f"{row['cohens_d']:.3f} | {row['cliffs_delta']:.3f} | {row['mannwhitney_p']:.3g} | {row['direct_auc']:.3f} |"
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
        raise ValueError("No eligible subjects were found for Surface B.")

    selected_run_frame = run_frame[run_frame["subject"].isin(selected_subjects["subject"])].copy()
    anchor_metrics, subject_metrics = run_subject_batch(selected_run_frame, config)
    subject_metrics = selected_subjects.merge(subject_metrics, on=["subject", "label", "cpc", "hospital"], how="left")

    reachability_metrics = load_reachability_subject_metrics(config)
    if not reachability_metrics.empty:
        subject_metrics = subject_metrics.merge(reachability_metrics, on="subject", how="left")

    residual_metrics = [
        "surface_b_logeuc_grad_median",
        "surface_b_logeuc_grad_p95",
        "surface_b_spectral_grad_median",
        "surface_b_spectral_grad_p95",
    ]
    subject_metrics, residual_models = add_reachability_residuals(subject_metrics, residual_metrics)
    effects = build_effect_table(subject_metrics)
    summary_text = write_summary_markdown(config, subject_pool, selected_subjects, effects)

    manifest = {
        "timeline_dir": str(config.timeline_dir),
        "mnps_dir": str(config.mnps_dir),
        "output_dir": str(config.output_dir),
        "primary_time_bin": config.primary_time_bin,
        "cohort_tag": config.cohort_tag,
        "selected_subjects_cpc1": int((selected_subjects["label"] == 1).sum()) if not selected_subjects.empty else 0,
        "selected_subjects_cpc5": int((selected_subjects["label"] == 0).sum()) if not selected_subjects.empty else 0,
        "workers": config.workers,
        "max_points_per_run": config.max_points_per_run,
        "reachability_k": config.reachability_k,
        "reachability_horizon": config.reachability_horizon,
        "reachability_super_window_size": config.reachability_super_window_size,
        "reachability_ridge_alpha": config.reachability_ridge_alpha,
        "reachability_jitter": config.reachability_jitter,
    }

    selected_subjects.to_csv(config.output_dir / "pilot_selected_subjects.csv", index=False)
    anchor_metrics.to_csv(config.output_dir / "surface_b_anchor_metrics.csv", index=False)
    subject_metrics.to_csv(config.output_dir / "surface_b_subject_metrics.csv", index=False)
    effects.to_csv(config.output_dir / "surface_b_effect_sizes.csv", index=False)
    (config.output_dir / "surface_b_summary.md").write_text(summary_text, encoding="utf-8")
    (config.output_dir / "surface_b_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (config.output_dir / "surface_b_residual_models.json").write_text(json.dumps(residual_models, indent=2), encoding="utf-8")

    print(f"Wrote Surface B subject metrics to {config.output_dir / 'surface_b_subject_metrics.csv'}")
    print(f"Wrote Surface B effects to {config.output_dir / 'surface_b_effect_sizes.csv'}")
    print(f"Wrote Surface B summary to {config.output_dir / 'surface_b_summary.md'}")


if __name__ == "__main__":
    main()
