from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.linalg import expm
from scipy.stats import mannwhitneyu, spearmanr
from sklearn.metrics import roc_auc_score

from run_wave1_geometry_pilots import (
    DEFAULT_PROCESSED_ROOT,
    DEFAULT_TIMELINE_DIR,
    EPS,
    GOOD_CPC,
    MIN_JACOBIAN_WINDOWS,
    POOR_CPC,
    PRIMARY_TIME_BIN,
    cliffs_delta,
    cohens_d,
    ensure_dir,
    load_run_table,
    read_run_arrays,
    sample_evenly_pair,
)


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "wave1_lyapunov_v2_20260527_part1_cpc15"
DEFAULT_WAVE1_SUBJECT_METRICS = (
    ARTICLE_DIR / "results" / "wave1_geometry_pilots_20260526_part1_cpc15" / "subject_wave1_metrics.csv"
)

OUTPUT_METRICS: tuple[str, ...] = (
    "largest_lyapunov_v2_per_hour",
    "lyapunov_positive_sum_v2_per_hour",
    "kaplan_yorke_dimension_v2",
)


@dataclass(frozen=True)
class Config:
    processed_roots: tuple[Path, ...]
    timeline_dir: Path
    output_dir: Path
    good_cpc: int
    poor_cpc: int
    primary_time_bin: str
    max_lyapunov_windows_per_run: int
    max_step_seconds: float
    max_expm_argument: float
    limit_subjects: int | None
    wave1_subject_metrics_path: Path


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description=(
            "Run a stricter Lyapunov v2 pilot using exact matrix exponentials and per-run QR iteration "
            "on the coma wave1 9D Jacobian exports."
        )
    )
    parser.add_argument(
        "--processed-root",
        type=Path,
        action="append",
        default=None,
        help="Repeat for multiple processed roots if needed.",
    )
    parser.add_argument("--timeline-dir", type=Path, default=DEFAULT_TIMELINE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--good-cpc", type=int, default=GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=POOR_CPC)
    parser.add_argument("--primary-time-bin", type=str, default=PRIMARY_TIME_BIN)
    parser.add_argument(
        "--max-lyapunov-windows-per-run",
        type=int,
        default=2500,
        help="Evenly downsampled Jacobian windows used per run before QR iteration.",
    )
    parser.add_argument(
        "--max-step-seconds",
        type=float,
        default=120.0,
        help="Skip steps larger than this to avoid propagating local Jacobians over large temporal gaps.",
    )
    parser.add_argument(
        "--max-expm-argument",
        type=float,
        default=50.0,
        help="Skip steps where ||J||_2 * dt exceeds this threshold before exp(J dt).",
    )
    parser.add_argument("--limit-subjects", type=int, default=None)
    parser.add_argument("--wave1-subject-metrics", type=Path, default=DEFAULT_WAVE1_SUBJECT_METRICS)
    args = parser.parse_args()
    processed_roots = tuple(args.processed_root) if args.processed_root else (DEFAULT_PROCESSED_ROOT,)
    return Config(
        processed_roots=processed_roots,
        timeline_dir=args.timeline_dir,
        output_dir=args.output_dir,
        good_cpc=int(args.good_cpc),
        poor_cpc=int(args.poor_cpc),
        primary_time_bin=str(args.primary_time_bin),
        max_lyapunov_windows_per_run=max(int(args.max_lyapunov_windows_per_run), MIN_JACOBIAN_WINDOWS),
        max_step_seconds=float(args.max_step_seconds),
        max_expm_argument=float(args.max_expm_argument),
        limit_subjects=args.limit_subjects,
        wave1_subject_metrics_path=args.wave1_subject_metrics,
    )


def kaplan_yorke_dimension(lambdas: np.ndarray) -> float:
    lambdas = np.asarray(lambdas, dtype=float)
    if lambdas.size == 0 or not np.isfinite(lambdas).any():
        return float("nan")
    cumulative = np.cumsum(lambdas)
    non_negative_idx = np.where(cumulative >= 0)[0]
    if len(non_negative_idx) == 0:
        return 0.0
    k_idx = int(non_negative_idx[-1])
    if k_idx >= len(lambdas) - 1 or lambdas[k_idx + 1] >= 0:
        return float(k_idx + 1)
    return float(k_idx + 1 + cumulative[k_idx] / abs(lambdas[k_idx + 1]))


def run_qr_lyapunov_exact(
    jacobians: np.ndarray,
    jacobian_time: np.ndarray,
    *,
    max_windows_per_run: int,
    max_step_seconds: float,
    max_expm_argument: float,
) -> dict[str, Any]:
    jacobians = np.asarray(jacobians, dtype=float)
    jacobian_time = np.asarray(jacobian_time, dtype=float)
    if len(jacobians) < MIN_JACOBIAN_WINDOWS:
        return {
            "log_diag": None,
            "n_windows_used": 0,
            "n_steps_used": 0,
            "n_steps_skipped_large_gap": 0,
            "n_steps_skipped_large_expm_argument": 0,
            "observed_dt_hours": 0.0,
        }

    jacobians, jacobian_time = sample_evenly_pair(jacobians, jacobian_time, max_windows_per_run)
    q_matrix = np.eye(jacobians.shape[1], dtype=float)
    log_diag = np.zeros(jacobians.shape[1], dtype=float)
    n_steps_used = 0
    n_steps_skipped_large_gap = 0
    n_steps_skipped_large_expm_argument = 0
    observed_dt_hours = 0.0

    for idx in range(len(jacobians) - 1):
        dt_sec = float(jacobian_time[idx + 1] - jacobian_time[idx])
        if not np.isfinite(dt_sec) or dt_sec <= 0:
            continue
        if np.isfinite(max_step_seconds) and max_step_seconds > 0 and dt_sec > max_step_seconds:
            n_steps_skipped_large_gap += 1
            continue
        step_argument = float(np.linalg.norm(jacobians[idx], ord=2) * dt_sec)
        if np.isfinite(max_expm_argument) and max_expm_argument > 0 and step_argument > max_expm_argument:
            n_steps_skipped_large_expm_argument += 1
            continue
        transition = expm(jacobians[idx] * dt_sec)
        if not np.isfinite(transition).all():
            continue
        z_matrix = transition @ q_matrix
        q_matrix, r_matrix = np.linalg.qr(z_matrix)
        diag = np.clip(np.abs(np.diag(r_matrix)), EPS, None)
        log_diag += np.log(diag)
        observed_dt_hours += dt_sec / 3600.0
        n_steps_used += 1

    return {
        "log_diag": log_diag if n_steps_used else None,
        "n_windows_used": int(len(jacobians)),
        "n_steps_used": int(n_steps_used),
        "n_steps_skipped_large_gap": int(n_steps_skipped_large_gap),
        "n_steps_skipped_large_expm_argument": int(n_steps_skipped_large_expm_argument),
        "observed_dt_hours": float(observed_dt_hours),
    }


def compute_subject_row(subject_runs: pd.DataFrame, config: Config) -> dict[str, Any]:
    anchor_row = subject_runs.iloc[0]
    total_log_diag: np.ndarray | None = None
    total_observed_dt_hours = 0.0
    n_runs_with_jacobian = 0
    n_runs_with_lyapunov = 0
    n_windows_total = 0
    n_windows_used = 0
    n_steps_used = 0
    n_steps_skipped_large_gap = 0
    n_steps_skipped_large_expm_argument = 0

    for _, run_row in subject_runs.iterrows():
        _, _, jacobians, jacobian_time = read_run_arrays(run_row)
        n_windows_total += int(len(jacobians))
        if len(jacobians):
            n_runs_with_jacobian += 1
        qr_result = run_qr_lyapunov_exact(
            jacobians,
            jacobian_time,
            max_windows_per_run=config.max_lyapunov_windows_per_run,
            max_step_seconds=config.max_step_seconds,
            max_expm_argument=config.max_expm_argument,
        )
        log_diag = qr_result["log_diag"]
        if log_diag is None:
            continue
        n_runs_with_lyapunov += 1
        n_windows_used += int(qr_result["n_windows_used"])
        n_steps_used += int(qr_result["n_steps_used"])
        n_steps_skipped_large_gap += int(qr_result["n_steps_skipped_large_gap"])
        n_steps_skipped_large_expm_argument += int(qr_result["n_steps_skipped_large_expm_argument"])
        total_observed_dt_hours += float(qr_result["observed_dt_hours"])
        total_log_diag = log_diag if total_log_diag is None else total_log_diag + log_diag

    if total_log_diag is None or total_observed_dt_hours <= 0:
        largest = float("nan")
        positive_sum = float("nan")
        ky_dimension = float("nan")
    else:
        lambdas = np.sort(total_log_diag / total_observed_dt_hours)[::-1]
        largest = float(lambdas[0])
        positive_sum = float(np.sum(lambdas[lambdas > 0]))
        ky_dimension = kaplan_yorke_dimension(lambdas)

    return {
        "subject": str(anchor_row["subject"]),
        "label": int(anchor_row["label"]),
        "label_name": str(anchor_row["label_name"]),
        "cpc": int(anchor_row["cpc_numeric"]),
        "hospital": str(anchor_row["hospital"]),
        "age": pd.to_numeric(anchor_row["age"], errors="coerce"),
        "sex": anchor_row["sex"],
        "rosc_minutes": pd.to_numeric(anchor_row["rosc_minutes"], errors="coerce"),
        "ttm_celsius": pd.to_numeric(anchor_row["ttm_celsius"], errors="coerce"),
        "n_runs": int(len(subject_runs)),
        "n_runs_with_jacobian": int(n_runs_with_jacobian),
        "n_runs_with_lyapunov_v2": int(n_runs_with_lyapunov),
        "n_jacobian_windows_total": int(n_windows_total),
        "n_jacobian_windows_used_v2": int(n_windows_used),
        "n_lyapunov_steps_used_v2": int(n_steps_used),
        "n_lyapunov_steps_skipped_large_gap_v2": int(n_steps_skipped_large_gap),
        "n_lyapunov_steps_skipped_large_expm_argument_v2": int(n_steps_skipped_large_expm_argument),
        "observed_dt_hours_v2": float(total_observed_dt_hours),
        "largest_lyapunov_v2_per_hour": largest,
        "lyapunov_positive_sum_v2_per_hour": positive_sum,
        "kaplan_yorke_dimension_v2": ky_dimension,
    }


def summarize_metric_contrasts(subject_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    labels = subject_metrics["label"].astype(int).to_numpy()
    for metric in OUTPUT_METRICS:
        values = pd.to_numeric(subject_metrics[metric], errors="coerce")
        metric_frame = pd.DataFrame({"value": values, "label": labels}).dropna()
        if metric_frame.empty:
            continue
        good = metric_frame.loc[metric_frame["label"] == 1, "value"].to_numpy(dtype=float)
        poor = metric_frame.loc[metric_frame["label"] == 0, "value"].to_numpy(dtype=float)
        if len(good) == 0 or len(poor) == 0:
            continue
        try:
            mw_p = float(mannwhitneyu(good, poor, alternative="two-sided").pvalue)
        except ValueError:
            mw_p = float("nan")
        try:
            direct_auroc = float(roc_auc_score(metric_frame["label"].astype(int), metric_frame["value"].astype(float)))
        except ValueError:
            direct_auroc = float("nan")
        rows.append(
            {
                "metric": metric,
                "cpc1_median": float(np.median(good)),
                "cpc5_median": float(np.median(poor)),
                "cohens_d": cohens_d(good, poor),
                "cliffs_delta": cliffs_delta(good, poor),
                "mann_whitney_p": mw_p,
                "direct_auroc": direct_auroc,
                "best_direction_auroc": float(max(direct_auroc, 1.0 - direct_auroc)) if np.isfinite(direct_auroc) else np.nan,
                "good_outcome_higher": bool(direct_auroc >= 0.5) if np.isfinite(direct_auroc) else None,
                "n_cpc1": int(len(good)),
                "n_cpc5": int(len(poor)),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values(["best_direction_auroc", "cohens_d"], ascending=[False, False]).reset_index(drop=True)


def compare_to_v1(subject_metrics: pd.DataFrame, wave1_subject_metrics_path: Path) -> pd.DataFrame:
    v1 = pd.read_csv(wave1_subject_metrics_path)
    columns = [
        "subject",
        "largest_lyapunov_per_hour",
        "lyapunov_positive_sum_per_hour",
        "kaplan_yorke_dimension",
        "label",
    ]
    merged = subject_metrics.merge(v1[columns], on=["subject", "label"], how="left", validate="one_to_one")

    comparisons = [
        ("largest_lyapunov_per_hour", "largest_lyapunov_v2_per_hour"),
        ("lyapunov_positive_sum_per_hour", "lyapunov_positive_sum_v2_per_hour"),
        ("kaplan_yorke_dimension", "kaplan_yorke_dimension_v2"),
    ]
    rows: list[dict[str, Any]] = []
    for v1_metric, v2_metric in comparisons:
        subset = merged[[v1_metric, v2_metric, "label"]].dropna()
        if subset.empty:
            continue
        rho = float(spearmanr(subset[v1_metric], subset[v2_metric]).statistic)
        v1_auc = float(roc_auc_score(subset["label"].astype(int), subset[v1_metric].astype(float)))
        v2_auc = float(roc_auc_score(subset["label"].astype(int), subset[v2_metric].astype(float)))
        v1_best = float(max(v1_auc, 1.0 - v1_auc))
        v2_best = float(max(v2_auc, 1.0 - v2_auc))
        rows.append(
            {
                "v1_metric": v1_metric,
                "v2_metric": v2_metric,
                "n_subjects": int(len(subset)),
                "spearman_rho": rho,
                "v1_best_direction_auroc": v1_best,
                "v2_best_direction_auroc": v2_best,
                "delta_best_direction_auroc": float(v2_best - v1_best),
            }
        )
    return pd.DataFrame(rows)


def build_summary_markdown(
    subject_metrics: pd.DataFrame,
    contrasts: pd.DataFrame,
    v1_v2_comparison: pd.DataFrame,
    config: Config,
) -> str:
    n_subjects = int(subject_metrics["subject"].nunique())
    n_good = int((subject_metrics["label"] == 1).sum())
    n_poor = int((subject_metrics["label"] == 0).sum())
    mean_observed_dt = float(pd.to_numeric(subject_metrics["observed_dt_hours_v2"], errors="coerce").mean())
    lines = [
        "# Wave1 Lyapunov v2 Summary",
        "",
        f"- processed roots: `{', '.join(str(path) for path in config.processed_roots)}`",
        f"- timeline dir: `{config.timeline_dir}`",
        f"- primary time bin: `{config.primary_time_bin}`",
        f"- subjects: `{n_subjects}` (`CPC{config.good_cpc}` = `{n_good}`, `CPC{config.poor_cpc}` = `{n_poor}`)",
        f"- max Lyapunov windows per run: `{config.max_lyapunov_windows_per_run}`",
        f"- max step seconds: `{config.max_step_seconds}`",
        f"- max expm argument: `{config.max_expm_argument}`",
        f"- mean observed Lyapunov horizon per subject (hours): `{mean_observed_dt:.3f}`",
        "",
        "## Lyapunov v2 Contrasts",
        "",
        "| Metric | CPC1 median | CPC5 median | Cohen's d | Best-direction AUROC |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, row in contrasts.iterrows():
        lines.append(
            "| {metric} | {cpc1:.4f} | {cpc5:.4f} | {d:.3f} | {auc:.3f} |".format(
                metric=row["metric"],
                cpc1=float(row["cpc1_median"]),
                cpc5=float(row["cpc5_median"]),
                d=float(row["cohens_d"]),
                auc=float(row["best_direction_auroc"]),
            )
        )
    lines.extend(["", "## V1 vs V2", "", "| V1 metric | V2 metric | Spearman rho | V1 AUROC | V2 AUROC | Delta |", "|---|---|---:|---:|---:|---:|"])
    for _, row in v1_v2_comparison.iterrows():
        lines.append(
            "| {v1} | {v2} | {rho:.3f} | {v1_auc:.3f} | {v2_auc:.3f} | {delta:+.3f} |".format(
                v1=row["v1_metric"],
                v2=row["v2_metric"],
                rho=float(row["spearman_rho"]),
                v1_auc=float(row["v1_best_direction_auroc"]),
                v2_auc=float(row["v2_best_direction_auroc"]),
                delta=float(row["delta_best_direction_auroc"]),
            )
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- V2 estimates use per-run QR iteration over `exp(J dt)` rather than `I + J dt`.",
            "- Cross-run temporal gaps are excluded by resetting the QR state at each run.",
            "- Large within-run time gaps beyond the configured threshold are skipped.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    config = parse_args()
    ensure_dir(config.output_dir)
    run_table = load_run_table(
        type(
            "Wave1CompatConfig",
            (),
            {
                "processed_roots": config.processed_roots,
                "timeline_dir": config.timeline_dir,
                "good_cpc": config.good_cpc,
                "poor_cpc": config.poor_cpc,
                "primary_time_bin": config.primary_time_bin,
                "limit_subjects": config.limit_subjects,
            },
        )()
    )

    subject_rows = [compute_subject_row(group.copy(), config) for _, group in run_table.groupby("subject", sort=True)]
    subject_metrics = pd.DataFrame(subject_rows).sort_values("subject").reset_index(drop=True)
    contrasts = summarize_metric_contrasts(subject_metrics)
    v1_v2_comparison = compare_to_v1(subject_metrics, config.wave1_subject_metrics_path)

    subject_metrics.to_csv(config.output_dir / "subject_lyapunov_v2_metrics.csv", index=False)
    contrasts.to_csv(config.output_dir / "lyapunov_v2_metric_contrasts.csv", index=False)
    v1_v2_comparison.to_csv(config.output_dir / "lyapunov_v1_v2_comparison.csv", index=False)
    (config.output_dir / "lyapunov_v2_summary.md").write_text(
        build_summary_markdown(subject_metrics, contrasts, v1_v2_comparison, config),
        encoding="utf-8",
    )

    manifest = {
        "processed_roots": [str(path) for path in config.processed_roots],
        "timeline_dir": str(config.timeline_dir),
        "output_dir": str(config.output_dir),
        "good_cpc": int(config.good_cpc),
        "poor_cpc": int(config.poor_cpc),
        "primary_time_bin": config.primary_time_bin,
        "max_lyapunov_windows_per_run": int(config.max_lyapunov_windows_per_run),
        "max_step_seconds": float(config.max_step_seconds),
        "max_expm_argument": float(config.max_expm_argument),
        "limit_subjects": config.limit_subjects,
        "wave1_subject_metrics_path": str(config.wave1_subject_metrics_path),
        "n_subjects": int(subject_metrics["subject"].nunique()),
        "config": {
            key: (str(value) if isinstance(value, Path) else [str(item) for item in value] if isinstance(value, tuple) else value)
            for key, value in asdict(config).items()
        },
    }
    (config.output_dir / "lyapunov_v2_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote outputs to {config.output_dir}", flush=True)


if __name__ == "__main__":
    main()
