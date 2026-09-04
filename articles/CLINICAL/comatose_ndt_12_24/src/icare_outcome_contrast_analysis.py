from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np
import pandas as pd
from scipy import stats


# ---------------------------------------------------------------------------
# Physical bounds for persistence / recovery reachability metrics.
# Persistence effective dimension is computed on the 3-D MNPS tube, so
# d_eff <= 3.  log_det and log_eig_var diverge when the recovery covariance
# becomes singular; beyond PERSISTENCE_LOG_BOUND the number represents a
# numerical blow-up, not real geometry.  kappa (condition number) >= 1 always
# and is capped at PERSISTENCE_KAPPA_MAX.
# ---------------------------------------------------------------------------
PERSISTENCE_D_EFF_MAX: float = 3.0
PERSISTENCE_LOG_BOUND: float = 50.0
PERSISTENCE_KAPPA_MAX: float = 1.0e6


def cohens_d_rank(good: np.ndarray, poor: np.ndarray) -> float:
    """Cohen's d on rank-transformed pooled values.

    This is an outlier-robust parametric effect size: it behaves like Cohen's d
    in terms of scale and interpretability but is insensitive to extreme values
    in heavy-tailed distributions such as the persistence family.
    """
    if good.size < 2 or poor.size < 2:
        return float("nan")
    pooled = np.concatenate([good, poor])
    ranks = stats.rankdata(pooled)
    good_ranks = ranks[: good.size]
    poor_ranks = ranks[good.size :]
    return cohens_d_independent(good_ranks, poor_ranks)


def clamp_persistence_metric(values: np.ndarray, metric: str) -> tuple[np.ndarray, int]:
    """Clamp known-bounded persistence / recovery metrics to physical ranges.

    Returns ``(clamped_array, n_values_clamped)``.  Only the named persistence
    families are touched; all other metrics pass through unchanged.
    """
    v = values.copy()
    if "persistence_d_eff" in metric:
        mask = np.isfinite(v) & (v > PERSISTENCE_D_EFF_MAX)
        v[mask] = PERSISTENCE_D_EFF_MAX
        return v, int(mask.sum())
    if "persistence_log_det" in metric or "persistence_log_eig_var" in metric:
        mask = np.isfinite(v) & (v > PERSISTENCE_LOG_BOUND)
        v[mask] = PERSISTENCE_LOG_BOUND
        return v, int(mask.sum())
    if "persistence_kappa" in metric:
        mask = np.isfinite(v) & (v > PERSISTENCE_KAPPA_MAX)
        v[mask] = PERSISTENCE_KAPPA_MAX
        return v, int(mask.sum())
    return v, 0


def apply_persistence_bounds_to_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Apply physical bound clamping to the ``value`` column for all persistence metrics.

    Operates on the long-format signal-metrics frame used by both the
    descriptive and contrast tables.  Reports a summary line to stdout.
    """
    if frame.empty:
        return frame.copy()
    out = frame.copy()
    n_clamped_total = 0
    for metric_name, group_idx in out.groupby("metric", sort=False).groups.items():
        v = out.loc[group_idx, "value"].to_numpy(dtype=float)
        clamped, n = clamp_persistence_metric(v, str(metric_name))
        if n > 0:
            out.loc[group_idx, "value"] = clamped
            n_clamped_total += n
    if n_clamped_total:
        print(
            f"Persistence bound clamping: {n_clamped_total} value(s) clamped to physical limits "
            f"(d_eff <= {PERSISTENCE_D_EFF_MAX}, log_bound <= {PERSISTENCE_LOG_BOUND}, "
            f"kappa <= {PERSISTENCE_KAPPA_MAX:.0e}).",
            flush=True,
        )
    return out


ARTICLE_DIR = Path(__file__).resolve().parents[1]
INPUT_DIR = ARTICLE_DIR / "results" / "mnps_summary"
OUTPUT_DIR = ARTICLE_DIR / "results" / "outcome_contrasts"
DEFAULT_GOOD_LABEL = "Good"
DEFAULT_POOR_LABEL = "Poor"
POOL_LABEL = "all_time_bins"
GROUPING_COLUMNS: tuple[str, ...] = (
    "analysis_type",
    "metric",
    "time_bin",
    "block_scope",
    "block_space",
    "source_group",
    "target_group",
)
DESCRIPTIVE_GROUP_COLUMNS: tuple[str, ...] = (
    "summary_level",
    "analysis_type",
    "metric",
    "time_bin",
    "block_scope",
    "block_space",
    "source_group",
    "target_group",
    "outcome",
)
EXCLUDED_METRIC_NAMES = {
    "dims",
    "horizon",
    "k",
    "in_dim",
    "out_dim",
    "source_dim",
    "target_dim",
}


@dataclass(frozen=True)
class OutcomeContrastConfig:
    input_dir: Path
    output_dir: Path
    good_label: str = DEFAULT_GOOD_LABEL
    poor_label: str = DEFAULT_POOR_LABEL
    good_cpc: int | None = None
    poor_cpc: int | None = None
    rank_effect_sizes: bool = False
    clamp_persistence_bounds: bool = False


def parse_args() -> OutcomeContrastConfig:
    parser = argparse.ArgumentParser(
        description="Build paper-facing Good vs Poor outcome contrasts from coma mnps_summary outputs."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=INPUT_DIR,
        help="Directory containing mnps_summary handoff outputs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory where outcome contrast outputs will be written.",
    )
    parser.add_argument("--good-label", type=str, default=DEFAULT_GOOD_LABEL)
    parser.add_argument("--poor-label", type=str, default=DEFAULT_POOR_LABEL)
    parser.add_argument("--good-cpc", type=int, default=None, help="Optional CPC value mapped to good-label.")
    parser.add_argument("--poor-cpc", type=int, default=None, help="Optional CPC value mapped to poor-label.")
    parser.add_argument(
        "--rank-effect-sizes",
        action="store_true",
        default=False,
        help=(
            "Add rank-based effect sizes (cohens_d_rank, cles) alongside the standard parametric cohens_d. "
            "Robust to heavy-tailed distributions such as the persistence family."
        ),
    )
    parser.add_argument(
        "--clamp-persistence-bounds",
        action="store_true",
        default=False,
        help=(
            "Clamp persistence / recovery metrics to physically plausible ranges before computing effect sizes "
            "and descriptive statistics.  Removes numerical blow-up artefacts "
            "(persistence_d_eff > 3, persistence_log_det > 50, persistence_kappa > 1e6) that "
            "otherwise inflate pooled variance and collapse parametric Cohen's d."
        ),
    )
    args = parser.parse_args()
    return OutcomeContrastConfig(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        good_label=args.good_label,
        poor_label=args.poor_label,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        rank_effect_sizes=args.rank_effect_sizes,
        clamp_persistence_bounds=args.clamp_persistence_bounds,
    )


def cliffs_delta(good: np.ndarray, poor: np.ndarray) -> float:
    if good.size == 0 or poor.size == 0:
        return float("nan")
    diff = np.subtract.outer(good, poor)
    gt = np.sum(diff > 0)
    lt = np.sum(diff < 0)
    return float((gt - lt) / diff.size)


def cohens_d_independent(good: np.ndarray, poor: np.ndarray) -> float:
    if good.size < 2 or poor.size < 2:
        return float("nan")
    good_var = float(np.var(good, ddof=1))
    poor_var = float(np.var(poor, ddof=1))
    pooled_denom = ((good.size - 1) * good_var + (poor.size - 1) * poor_var) / (good.size + poor.size - 2)
    if pooled_denom <= 0 or not np.isfinite(pooled_denom):
        return float("nan")
    pooled_sd = float(np.sqrt(pooled_denom))
    return float((np.mean(good) - np.mean(poor)) / pooled_sd)


def summary_stats(values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {
            "n_rows": 0.0,
            "mean": float("nan"),
            "median": float("nan"),
            "sd": float("nan"),
            "iqr": float("nan"),
        }
    return {
        "n_rows": float(values.size),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "sd": float(np.std(values, ddof=1)) if values.size > 1 else float("nan"),
        "iqr": float(np.quantile(values, 0.75) - np.quantile(values, 0.25)),
    }


def load_manifest(input_dir: Path) -> dict[str, Any]:
    return json.loads((input_dir / "metric_handoff_manifest.json").read_text(encoding="utf-8"))


def is_signal_metric(metric: str) -> bool:
    if metric in EXCLUDED_METRIC_NAMES:
        return False
    if metric.endswith("_finite_frac"):
        return False
    return True


def prepare_metric_frame(path: Path, manifest: dict[str, Any], *, summary_level: str) -> pd.DataFrame:
    frame = pd.read_csv(path, low_memory=False)
    classical_analyses = set(manifest.get("classical_outcome_ready_analyses", []))
    available_metrics = {
        analysis_type: {metric for metric in metrics if is_signal_metric(metric)}
        for analysis_type, metrics in (manifest.get("available_metrics_by_analysis") or {}).items()
    }
    frame = frame[frame["analysis_type"].isin(classical_analyses)].copy()
    frame = frame[frame["metric"].astype(str).map(is_signal_metric)].copy()
    frame = frame[
        frame.apply(
            lambda row: str(row["metric"]) in available_metrics.get(str(row["analysis_type"]), set()),
            axis=1,
        )
    ].copy()
    frame = frame[pd.to_numeric(frame["value"], errors="coerce").notna()].copy()
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame["summary_level"] = summary_level
    frame["time_bin"] = frame["time_bin"].fillna("unassigned")
    for column in ("block_scope", "block_space", "source_group", "target_group"):
        if column not in frame.columns:
            frame[column] = None
    return frame.reset_index(drop=True)


def apply_endpoint_filter(
    frame: pd.DataFrame,
    *,
    good_label: str,
    poor_label: str,
    good_cpc: int | None,
    poor_cpc: int | None,
) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    out = frame.copy()
    if good_cpc is not None and poor_cpc is not None:
        cpc_numeric = pd.to_numeric(out["cpc"], errors="coerce")
        out["outcome"] = np.where(
            cpc_numeric == float(good_cpc),
            good_label,
            np.where(cpc_numeric == float(poor_cpc), poor_label, None),
        )
        out = out[pd.notna(out["outcome"])].copy()
    else:
        out = out[out["outcome"].isin([good_label, poor_label])].copy()
    return out.reset_index(drop=True)


def expand_with_pooled_timebin(frame: pd.DataFrame) -> pd.DataFrame:
    pooled = frame.copy()
    pooled["time_bin"] = POOL_LABEL
    return pd.concat([frame, pooled], ignore_index=True)


def build_descriptive_table(frame: pd.DataFrame, *, good_label: str, poor_label: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    keep = frame[frame["outcome"].isin([good_label, poor_label])].copy()
    if keep.empty:
        return pd.DataFrame()

    for keys, group in keep.groupby(list(DESCRIPTIVE_GROUP_COLUMNS), dropna=False, sort=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(DESCRIPTIVE_GROUP_COLUMNS, keys))
        vals = pd.to_numeric(group["value"], errors="coerce").dropna().to_numpy(dtype=float)
        stats_row = summary_stats(vals)
        row["n_subjects"] = int(group["subject"].astype(str).nunique()) if "subject" in group.columns else 0
        row.update(stats_row)
        rows.append(row)
    return pd.DataFrame(rows)


def build_contrast_table(frame: pd.DataFrame, *, good_label: str, poor_label: str, rank_effect_sizes: bool = False) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    keep = frame[frame["outcome"].isin([good_label, poor_label])].copy()
    if keep.empty:
        return pd.DataFrame()

    contrast_group_cols = ["summary_level", *GROUPING_COLUMNS]
    for keys, group in keep.groupby(contrast_group_cols, dropna=False, sort=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(contrast_group_cols, keys))
        good_rows = group[group["outcome"] == good_label].copy()
        poor_rows = group[group["outcome"] == poor_label].copy()
        good_values = pd.to_numeric(good_rows["value"], errors="coerce").dropna().to_numpy(dtype=float)
        poor_values = pd.to_numeric(poor_rows["value"], errors="coerce").dropna().to_numpy(dtype=float)

        good_stats = summary_stats(good_values)
        poor_stats = summary_stats(poor_values)
        cd = cliffs_delta(good_values, poor_values)
        effect_row: Dict[str, Any] = {
            "cohens_d": cohens_d_independent(good_values, poor_values),
            "cliffs_delta": cd,
        }
        if rank_effect_sizes:
            effect_row["cohens_d_rank"] = cohens_d_rank(good_values, poor_values)
            effect_row["cles"] = float((cd + 1.0) / 2.0) if np.isfinite(cd) else float("nan")
        row.update(
            {
                "good_label": good_label,
                "poor_label": poor_label,
                "n_good_rows": int(good_values.size),
                "n_poor_rows": int(poor_values.size),
                "n_good_subjects": int(good_rows["subject"].astype(str).nunique()) if not good_rows.empty else 0,
                "n_poor_subjects": int(poor_rows["subject"].astype(str).nunique()) if not poor_rows.empty else 0,
                "good_mean": good_stats["mean"],
                "good_median": good_stats["median"],
                "good_sd": good_stats["sd"],
                "good_iqr": good_stats["iqr"],
                "poor_mean": poor_stats["mean"],
                "poor_median": poor_stats["median"],
                "poor_sd": poor_stats["sd"],
                "poor_iqr": poor_stats["iqr"],
                "delta_mean_good_minus_poor": good_stats["mean"] - poor_stats["mean"]
                if np.isfinite(good_stats["mean"]) and np.isfinite(poor_stats["mean"])
                else np.nan,
                "delta_median_good_minus_poor": good_stats["median"] - poor_stats["median"]
                if np.isfinite(good_stats["median"]) and np.isfinite(poor_stats["median"])
                else np.nan,
                **effect_row,
            }
        )

        if good_values.size == 0 or poor_values.size == 0:
            row["status"] = "insufficient_outcome_groups"
            row["mannwhitney_u"] = np.nan
            row["mannwhitney_p"] = np.nan
            row["welch_t"] = np.nan
            row["welch_p"] = np.nan
            row["contrast_direction"] = "unavailable"
            rows.append(row)
            continue

        try:
            mannwhitney = stats.mannwhitneyu(good_values, poor_values, alternative="two-sided")
            row["mannwhitney_u"] = float(mannwhitney.statistic)
            row["mannwhitney_p"] = float(mannwhitney.pvalue)
        except Exception:
            row["mannwhitney_u"] = np.nan
            row["mannwhitney_p"] = np.nan

        if good_values.size >= 2 and poor_values.size >= 2:
            welch = stats.ttest_ind(good_values, poor_values, equal_var=False, nan_policy="omit")
            row["welch_t"] = float(welch.statistic)
            row["welch_p"] = float(welch.pvalue)
            row["status"] = "ok"
        else:
            row["welch_t"] = np.nan
            row["welch_p"] = np.nan
            row["status"] = "limited_n"

        delta_median = row["delta_median_good_minus_poor"]
        if np.isfinite(delta_median):
            row["contrast_direction"] = "good_gt_poor" if delta_median > 0 else "good_lt_poor" if delta_median < 0 else "equal"
        else:
            row["contrast_direction"] = "unavailable"
        rows.append(row)

    return pd.DataFrame(rows)


def count_outcomes(frame: pd.DataFrame) -> dict[str, int]:
    if frame.empty:
        return {}
    return {str(key): int(value) for key, value in frame["outcome"].fillna("missing").value_counts(dropna=False).to_dict().items()}


def build_qc_summary(
    config: OutcomeContrastConfig,
    patient_frame: pd.DataFrame,
    run_frame: pd.DataFrame,
    patient_contrasts: pd.DataFrame,
    run_contrasts: pd.DataFrame,
    *,
    good_label: str,
    poor_label: str,
    good_cpc: int | None,
    poor_cpc: int | None,
) -> dict[str, Any]:
    return {
        "input_dir": str(config.input_dir),
        "output_dir": str(config.output_dir),
        "good_label": good_label,
        "poor_label": poor_label,
        "good_cpc": good_cpc,
        "poor_cpc": poor_cpc,
        "patient_timebin_rows": int(len(patient_frame)),
        "run_level_rows": int(len(run_frame)),
        "patient_timebin_outcome_counts": count_outcomes(patient_frame),
        "run_level_outcome_counts": count_outcomes(run_frame),
        "patient_timebin_unique_subjects": int(patient_frame["subject"].astype(str).nunique()) if not patient_frame.empty else 0,
        "run_level_unique_subjects": int(run_frame["subject"].astype(str).nunique()) if not run_frame.empty else 0,
        "patient_timebin_contrast_status_counts": patient_contrasts["status"].value_counts(dropna=False).to_dict()
        if not patient_contrasts.empty
        else {},
        "run_level_contrast_status_counts": run_contrasts["status"].value_counts(dropna=False).to_dict()
        if not run_contrasts.empty
        else {},
        "has_both_outcome_groups_patient_timebin": bool(
            {good_label, poor_label}.issubset(set(patient_frame["outcome"].dropna().astype(str)))
        )
        if not patient_frame.empty
        else False,
        "has_both_outcome_groups_run_level": bool(
            {good_label, poor_label}.issubset(set(run_frame["outcome"].dropna().astype(str)))
        )
        if not run_frame.empty
        else False,
    }


def build_summary_markdown(
    qc_summary: dict[str, Any],
    patient_contrasts: pd.DataFrame,
    run_contrasts: pd.DataFrame,
) -> str:
    lines = [
        "# Outcome contrast summary",
        "",
        "## Inputs",
        "",
        f"- patient_timebin_rows: {qc_summary['patient_timebin_rows']}",
        f"- run_level_rows: {qc_summary['run_level_rows']}",
        f"- patient_timebin_outcome_counts: {qc_summary['patient_timebin_outcome_counts']}",
        f"- run_level_outcome_counts: {qc_summary['run_level_outcome_counts']}",
        "",
        "## Status",
        "",
        f"- patient_timebin_contrast_status_counts: {qc_summary['patient_timebin_contrast_status_counts']}",
        f"- run_level_contrast_status_counts: {qc_summary['run_level_contrast_status_counts']}",
        "",
    ]

    ok_patient = patient_contrasts[patient_contrasts["status"] == "ok"].copy() if not patient_contrasts.empty else pd.DataFrame()
    ok_run = run_contrasts[run_contrasts["status"] == "ok"].copy() if not run_contrasts.empty else pd.DataFrame()
    if ok_patient.empty and ok_run.empty:
        lines.extend(
            [
                "## Interpretation",
                "",
                f"No valid `{qc_summary['good_label']}` vs `{qc_summary['poor_label']}` outcome contrast was estimable in the current export.",
                "The analysis code is in place, but the current validation slice does not yet contain both outcome groups at the required comparison level.",
            ]
        )
        return "\n".join(lines) + "\n"

    if not ok_patient.empty:
        top_patient = ok_patient.sort_values("mannwhitney_p", ascending=True, na_position="last").head(10)
        lines.extend(["## Top Patient/Time-Bin Contrasts", ""])
        for _, row in top_patient.iterrows():
            lines.append(
                f"- `{row['analysis_type']}` / `{row['metric']}` / `{row['time_bin']}`: "
                f"delta_median={row['delta_median_good_minus_poor']:.4g}, "
                f"mannwhitney_p={row['mannwhitney_p']:.4g}"
            )
        lines.append("")

    if not ok_run.empty:
        top_run = ok_run.sort_values("mannwhitney_p", ascending=True, na_position="last").head(10)
        lines.extend(["## Top Run-Level Contrasts", ""])
        for _, row in top_run.iterrows():
            lines.append(
                f"- `{row['analysis_type']}` / `{row['metric']}` / `{row['time_bin']}`: "
                f"delta_median={row['delta_median_good_minus_poor']:.4g}, "
                f"mannwhitney_p={row['mannwhitney_p']:.4g}"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_outputs(
    config: OutcomeContrastConfig,
    patient_descriptives: pd.DataFrame,
    run_descriptives: pd.DataFrame,
    patient_contrasts: pd.DataFrame,
    run_contrasts: pd.DataFrame,
    qc_summary: dict[str, Any],
) -> None:
    ensure_dir(config.output_dir)
    patient_descriptives.to_csv(config.output_dir / "patient_timebin_group_descriptives.csv", index=False)
    run_descriptives.to_csv(config.output_dir / "run_level_group_descriptives.csv", index=False)
    patient_contrasts.to_csv(config.output_dir / "patient_timebin_outcome_contrasts.csv", index=False)
    run_contrasts.to_csv(config.output_dir / "run_level_outcome_contrasts.csv", index=False)
    (config.output_dir / "outcome_contrast_qc.json").write_text(json.dumps(qc_summary, indent=2), encoding="utf-8")
    (config.output_dir / "outcome_contrast_summary.md").write_text(
        build_summary_markdown(qc_summary, patient_contrasts, run_contrasts),
        encoding="utf-8",
    )


def main() -> None:
    config = parse_args()
    manifest = load_manifest(config.input_dir)
    patient_frame = apply_endpoint_filter(
        prepare_metric_frame(
            config.input_dir / "patient_timebin_signal_metrics.csv",
            manifest,
            summary_level="patient_timebin",
        ),
        good_label=config.good_label,
        poor_label=config.poor_label,
        good_cpc=config.good_cpc,
        poor_cpc=config.poor_cpc,
    )
    run_frame = apply_endpoint_filter(
        prepare_metric_frame(
            config.input_dir / "run_level_signal_metrics.csv",
            manifest,
            summary_level="run_level",
        ),
        good_label=config.good_label,
        poor_label=config.poor_label,
        good_cpc=config.good_cpc,
        poor_cpc=config.poor_cpc,
    )

    patient_expanded = expand_with_pooled_timebin(patient_frame)
    run_expanded = expand_with_pooled_timebin(run_frame)

    if config.clamp_persistence_bounds:
        patient_expanded = apply_persistence_bounds_to_frame(patient_expanded)
        run_expanded = apply_persistence_bounds_to_frame(run_expanded)

    patient_descriptives = build_descriptive_table(
        patient_expanded,
        good_label=config.good_label,
        poor_label=config.poor_label,
    )
    run_descriptives = build_descriptive_table(
        run_expanded,
        good_label=config.good_label,
        poor_label=config.poor_label,
    )
    patient_contrasts = build_contrast_table(
        patient_expanded,
        good_label=config.good_label,
        poor_label=config.poor_label,
        rank_effect_sizes=config.rank_effect_sizes,
    )
    run_contrasts = build_contrast_table(
        run_expanded,
        good_label=config.good_label,
        poor_label=config.poor_label,
        rank_effect_sizes=config.rank_effect_sizes,
    )

    qc_summary = build_qc_summary(
        config,
        patient_frame,
        run_frame,
        patient_contrasts,
        run_contrasts,
        good_label=config.good_label,
        poor_label=config.poor_label,
        good_cpc=config.good_cpc,
        poor_cpc=config.poor_cpc,
    )
    qc_summary["rank_effect_sizes"] = config.rank_effect_sizes
    qc_summary["clamp_persistence_bounds"] = config.clamp_persistence_bounds
    write_outputs(
        config,
        patient_descriptives,
        run_descriptives,
        patient_contrasts,
        run_contrasts,
        qc_summary,
    )

    print(f"Wrote patient outcome contrasts to {config.output_dir / 'patient_timebin_outcome_contrasts.csv'}")
    print(f"Wrote run-level outcome contrasts to {config.output_dir / 'run_level_outcome_contrasts.csv'}")
    print(f"Wrote QC summary to {config.output_dir / 'outcome_contrast_qc.json'}")


if __name__ == "__main__":
    main()
