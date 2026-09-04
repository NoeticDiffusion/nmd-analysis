from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy import stats


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_DIR = ARTICLE_DIR / "results"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "reviewer_checks_20260518_cpc15"
PRIMARY_TIME_BIN = "0_12h"
GOOD_CPC = 1
POOR_CPC = 5
SELECTED_METRICS = [
    "tube_d_eff_median",
    "persistence_log_det_median",
    "persistence_log_eig_var_median",
    "persistence_hysteresis_log_det_median",
    "tube_capture_gate_median",
]


@dataclass(frozen=True)
class Config:
    results_dir: Path
    timeline_dir: Path
    contrast_dir: Path
    mnps_dir: Path
    output_dir: Path
    primary_time_bin: str
    good_cpc: int
    poor_cpc: int


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Build reviewer-facing checks for the CPC1-vs-CPC5 coma manuscript.")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument(
        "--timeline-dir",
        type=Path,
        default=ARTICLE_DIR / "results" / "timeline_analysis_20260517_cpc15_primary12h",
    )
    parser.add_argument(
        "--contrast-dir",
        type=Path,
        default=ARTICLE_DIR / "results" / "outcome_contrasts_20260517_cpc15_primary12h",
    )
    parser.add_argument(
        "--mnps-dir",
        type=Path,
        default=ARTICLE_DIR / "results" / "mnps_summary_20260517_cpc15_primary12h",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--primary-time-bin", type=str, default=PRIMARY_TIME_BIN)
    parser.add_argument("--good-cpc", type=int, default=GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=POOR_CPC)
    args = parser.parse_args()
    return Config(
        results_dir=args.results_dir,
        timeline_dir=args.timeline_dir,
        contrast_dir=args.contrast_dir,
        mnps_dir=args.mnps_dir,
        output_dir=args.output_dir,
        primary_time_bin=args.primary_time_bin,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
    )


def bh_fdr(p_values: pd.Series) -> pd.Series:
    values = pd.to_numeric(p_values, errors="coerce").to_numpy(dtype=float)
    out = np.full(values.shape, np.nan, dtype=float)
    mask = np.isfinite(values)
    if not mask.any():
        return pd.Series(out, index=p_values.index, dtype=float)
    valid = values[mask]
    order = np.argsort(valid)
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(valid) + 1)
    q = valid * len(valid) / ranks
    q_sorted = np.minimum.accumulate(q[order][::-1])[::-1]
    q_final = np.empty_like(q_sorted)
    q_final[order] = np.clip(q_sorted, 0.0, 1.0)
    out[np.where(mask)[0]] = q_final
    return pd.Series(out, index=p_values.index, dtype=float)


def cohens_d(good: pd.Series, poor: pd.Series) -> float:
    good_arr = pd.to_numeric(good, errors="coerce").dropna().to_numpy(dtype=float)
    poor_arr = pd.to_numeric(poor, errors="coerce").dropna().to_numpy(dtype=float)
    if good_arr.size < 2 or poor_arr.size < 2:
        return float("nan")
    pooled = ((good_arr.size - 1) * np.var(good_arr, ddof=1) + (poor_arr.size - 1) * np.var(poor_arr, ddof=1)) / (
        good_arr.size + poor_arr.size - 2
    )
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(good_arr) - np.mean(poor_arr)) / np.sqrt(pooled))


def load_contrasts(config: Config) -> pd.DataFrame:
    path = config.contrast_dir / "patient_timebin_outcome_contrasts.csv"
    return pd.read_csv(path)


def load_timeline(config: Config) -> pd.DataFrame:
    path = config.timeline_dir / "patient_timebin_summaries.csv"
    frame = pd.read_csv(path)
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    return frame[(frame["time_bin"] == config.primary_time_bin) & (frame["cpc_numeric"].isin([config.good_cpc, config.poor_cpc]))].copy()


def load_metrics(config: Config) -> pd.DataFrame:
    path = config.mnps_dir / "patient_timebin_signal_metrics.csv"
    frame = pd.read_csv(path)
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    return frame[(frame["time_bin"] == config.primary_time_bin) & (frame["cpc_numeric"].isin([config.good_cpc, config.poor_cpc]))].copy()


def build_selection_audit(contrasts: pd.DataFrame, config: Config) -> pd.DataFrame:
    frame = contrasts[
        (contrasts["summary_level"] == "patient_timebin")
        & (contrasts["analysis_type"] == "reachability_cones")
        & (contrasts["time_bin"] == config.primary_time_bin)
        & (contrasts["status"] == "ok")
    ].copy()
    frame = frame[frame["metric"].astype(str).str.endswith("_median")].copy()
    frame = frame[frame["metric"] != "__unit_weight__"].copy()
    frame["bh_fdr_q"] = bh_fdr(frame["mannwhitney_p"])
    return frame.sort_values("mannwhitney_p").reset_index(drop=True)


def build_metric_matrix(metrics: pd.DataFrame) -> pd.DataFrame:
    frame = metrics[
        (metrics["analysis_type"] == "reachability_cones") & (metrics["metric"].isin(SELECTED_METRICS))
    ].copy()
    return frame.pivot_table(index="subject", columns="metric", values="value", aggfunc="first")


def build_shockable_subset_contrasts(metric_matrix: pd.DataFrame, timeline: pd.DataFrame, config: Config) -> pd.DataFrame:
    shockable = timeline[["subject", "cpc_numeric", "shockable_rhythm"]].copy()
    shockable["shockable_bin"] = (
        shockable["shockable_rhythm"].astype(str).str.strip().str.lower().map({"true": 1.0, "false": 0.0})
    )
    shockable = shockable[shockable["shockable_bin"] == 1.0].copy()
    merged = metric_matrix.merge(shockable[["subject", "cpc_numeric"]], left_index=True, right_on="subject", how="inner")
    rows: List[Dict[str, float | str | int]] = []
    for metric in SELECTED_METRICS:
        good = pd.to_numeric(merged[merged["cpc_numeric"] == float(config.good_cpc)][metric], errors="coerce").dropna()
        poor = pd.to_numeric(merged[merged["cpc_numeric"] == float(config.poor_cpc)][metric], errors="coerce").dropna()
        if good.empty or poor.empty:
            continue
        u_stat, p_value = stats.mannwhitneyu(good.to_numpy(dtype=float), poor.to_numpy(dtype=float), alternative="two-sided")
        rows.append(
            {
                "metric": metric,
                "n_cpc1": int(good.size),
                "n_cpc5": int(poor.size),
                "cpc1_median": float(good.median()),
                "cpc5_median": float(poor.median()),
                "cohens_d": cohens_d(good, poor),
                "mannwhitney_u": float(u_stat),
                "mannwhitney_p": float(p_value),
            }
        )
    return pd.DataFrame(rows).sort_values("mannwhitney_p").reset_index(drop=True)


def write_summary(
    config: Config,
    selection_audit: pd.DataFrame,
    selected_only: pd.DataFrame,
    corr: pd.DataFrame,
    shockable: pd.DataFrame,
    subject_index: pd.DataFrame,
) -> str:
    counts = subject_index["cpc"].value_counts(dropna=False).sort_index().to_dict()
    lines = [
        "# Reviewer Checks Summary",
        "",
        f"- primary time bin: `{config.primary_time_bin}`",
        f"- total subjects with analyzable `{config.primary_time_bin}` summaries in local subject index: `{int(subject_index['subject'].nunique())}`",
        f"- CPC breakdown in local subject index: `{counts}`",
        f"- exploratory reachability selection pool size (patient-level `reachability_cones` median summaries): `{len(selection_audit)}`",
        "",
        "## Selected metrics with BH-FDR",
        "",
    ]
    for _, row in selected_only.iterrows():
        lines.append(
            f"- `{row['metric']}`: Cohen's `d = {row['cohens_d']:.3f}`, Mann-Whitney `p = {row['mannwhitney_p']:.3g}`, BH-FDR `q = {row['bh_fdr_q']:.3g}`"
        )
    lines.extend(["", "## Inter-metric correlations (Spearman rho)", ""])
    for metric in corr.index:
        parts = [f"`{other}`={corr.loc[metric, other]:.3f}" for other in corr.columns if other != metric]
        lines.append(f"- `{metric}`: " + ", ".join(parts))
    if not shockable.empty:
        lines.extend(
            [
                "",
                "## Shockable-only subgroup",
                "",
                f"- subgroup counts: `{config.good_cpc}` = {int(shockable['n_cpc1'].iloc[0])}, `{config.poor_cpc}` = {int(shockable['n_cpc5'].iloc[0])}",
            ]
        )
        for _, row in shockable.iterrows():
            lines.append(
                f"- `{row['metric']}`: medians `{row['cpc1_median']:.3f}` vs `{row['cpc5_median']:.3f}`, "
                f"Cohen's `d = {row['cohens_d']:.3f}`, Mann-Whitney `p = {row['mannwhitney_p']:.3g}`"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    contrasts = load_contrasts(config)
    timeline = load_timeline(config)
    metrics = load_metrics(config)
    subject_index = pd.read_csv(config.timeline_dir / "subject_outcome_index.csv")

    selection_audit = build_selection_audit(contrasts, config)
    selected_only = selection_audit[selection_audit["metric"].isin(SELECTED_METRICS)].copy()
    metric_matrix = build_metric_matrix(metrics)
    corr = metric_matrix[SELECTED_METRICS].corr(method="spearman")
    shockable = build_shockable_subset_contrasts(metric_matrix[SELECTED_METRICS], timeline, config)

    selection_audit.to_csv(config.output_dir / "selection_audit_reachability_medians.csv", index=False)
    selected_only.to_csv(config.output_dir / "selection_audit_top5.csv", index=False)
    corr.to_csv(config.output_dir / "selected_metric_spearman_correlation.csv")
    shockable.to_csv(config.output_dir / "shockable_only_selected_metric_contrasts.csv", index=False)
    (config.output_dir / "reviewer_checks_summary.md").write_text(
        write_summary(config, selection_audit, selected_only, corr, shockable, subject_index),
        encoding="utf-8",
    )
    (config.output_dir / "reviewer_checks_manifest.json").write_text(
        json.dumps(
            {
                "primary_time_bin": config.primary_time_bin,
                "good_cpc": config.good_cpc,
                "poor_cpc": config.poor_cpc,
                "selected_metrics": SELECTED_METRICS,
                "selection_pool_size": int(len(selection_audit)),
                "timeline_dir": str(config.timeline_dir),
                "contrast_dir": str(config.contrast_dir),
                "mnps_dir": str(config.mnps_dir),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote reviewer checks to {config.output_dir}")


if __name__ == "__main__":
    main()
