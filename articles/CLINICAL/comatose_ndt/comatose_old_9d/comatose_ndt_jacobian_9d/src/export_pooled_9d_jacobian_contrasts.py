from __future__ import annotations

import argparse
import json
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PART1_DIR = (
    ARTICLE_DIR.parent / "comatose_ndt" / "results" / "mnps_summary_20260524_part1_primary12h_9d_targeted"
)
DEFAULT_PART2_DIR = ARTICLE_DIR.parent / "comatose_ndt" / "results" / "mnps_summary_20260523_part2_primary12h_9d"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "outcome_contrasts_9d_jacobian_20260525_cpc15_primary12h"
DEFAULT_ANALYSIS_TYPE = "global_mnps_jacobian_9d"
DEFAULT_PRIMARY_TIME_BIN = "0_12h"
DEFAULT_GOOD_LABEL = "Good"
DEFAULT_POOR_LABEL = "Poor"
DEFAULT_GOOD_CPC = 1
DEFAULT_POOR_CPC = 5
POOL_LABEL = "all_time_bins"
EXCLUDED_METRIC_NAMES = {
    "dims",
    "horizon",
    "k",
    "in_dim",
    "out_dim",
    "source_dim",
    "target_dim",
}
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
MANUSCRIPT_CANDIDATES: tuple[str, ...] = (
    "spectral_radius_median",
    "anisotropy_abs_eig_median",
    "a_operator_norm_median",
    "frobenius_norm_median",
    "rotation_norm_median",
)


@dataclass(frozen=True)
class Config:
    part1_input_dir: Path
    part2_input_dir: Path
    output_dir: Path
    analysis_type: str
    primary_time_bin: str
    good_label: str
    poor_label: str
    good_cpc: int
    poor_cpc: int


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Export part1/part2/pooled 9D Jacobian outcome contrasts in the coma article style."
    )
    parser.add_argument("--part1-input-dir", type=Path, default=DEFAULT_PART1_DIR)
    parser.add_argument("--part2-input-dir", type=Path, default=DEFAULT_PART2_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--analysis-type", type=str, default=DEFAULT_ANALYSIS_TYPE)
    parser.add_argument("--primary-time-bin", type=str, default=DEFAULT_PRIMARY_TIME_BIN)
    parser.add_argument("--good-label", type=str, default=DEFAULT_GOOD_LABEL)
    parser.add_argument("--poor-label", type=str, default=DEFAULT_POOR_LABEL)
    parser.add_argument("--good-cpc", type=int, default=DEFAULT_GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=DEFAULT_POOR_CPC)
    args = parser.parse_args()
    return Config(
        part1_input_dir=args.part1_input_dir,
        part2_input_dir=args.part2_input_dir,
        output_dir=args.output_dir,
        analysis_type=args.analysis_type,
        primary_time_bin=args.primary_time_bin,
        good_label=args.good_label,
        poor_label=args.poor_label,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
    )


def is_signal_metric(metric: str) -> bool:
    if metric in EXCLUDED_METRIC_NAMES:
        return False
    if metric.endswith("_finite_frac"):
        return False
    return True


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
    return float((np.mean(good) - np.mean(poor)) / float(np.sqrt(pooled_denom)))


def load_manifest(input_dir: Path) -> dict[str, Any]:
    return json.loads((input_dir / "metric_handoff_manifest.json").read_text(encoding="utf-8"))


def load_metric_frame(input_dir: Path, manifest: dict[str, Any], *, summary_level: str, analysis_type: str) -> pd.DataFrame:
    if summary_level == "patient_timebin":
        path = input_dir / "patient_timebin_signal_metrics.csv"
    elif summary_level == "run":
        path = input_dir / "run_level_signal_metrics.csv"
    else:
        raise ValueError(f"Unsupported summary_level: {summary_level}")
    frame = pd.read_csv(path, low_memory=False)
    available_metrics = {
        key: {metric for metric in metrics if is_signal_metric(metric)}
        for key, metrics in (manifest.get("available_metrics_by_analysis") or {}).items()
    }
    frame = frame[frame["analysis_type"] == analysis_type].copy()
    frame = frame[frame["metric"].astype(str).map(is_signal_metric)].copy()
    frame = frame[
        frame["metric"].astype(str).map(lambda metric: metric in available_metrics.get(analysis_type, set()))
    ].copy()
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[frame["value"].notna()].copy()
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
    good_cpc: int,
    poor_cpc: int,
) -> pd.DataFrame:
    out = frame.copy()
    cpc_numeric = pd.to_numeric(out["cpc"], errors="coerce")
    out["outcome"] = np.where(
        cpc_numeric == float(good_cpc),
        good_label,
        np.where(cpc_numeric == float(poor_cpc), poor_label, None),
    )
    out = out[pd.notna(out["outcome"])].copy()
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
        row.update(summary_stats(vals))
        row["n_subjects"] = int(group["subject"].astype(str).nunique()) if "subject" in group.columns else 0
        rows.append(row)
    return pd.DataFrame(rows)


def build_contrast_table(frame: pd.DataFrame, *, good_label: str, poor_label: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    keep = frame[frame["outcome"].isin([good_label, poor_label])].copy()
    if keep.empty:
        return pd.DataFrame()
    for keys, group in keep.groupby(["summary_level", *GROUPING_COLUMNS], dropna=False, sort=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(["summary_level", *GROUPING_COLUMNS], keys))
        good_rows = group[group["outcome"] == good_label].copy()
        poor_rows = group[group["outcome"] == poor_label].copy()
        good_values = pd.to_numeric(good_rows["value"], errors="coerce").dropna().to_numpy(dtype=float)
        poor_values = pd.to_numeric(poor_rows["value"], errors="coerce").dropna().to_numpy(dtype=float)
        good_stats = summary_stats(good_values)
        poor_stats = summary_stats(poor_values)
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
                "cohens_d": cohens_d_independent(good_values, poor_values),
                "cliffs_delta": cliffs_delta(good_values, poor_values),
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
        mannwhitney = stats.mannwhitneyu(good_values, poor_values, alternative="two-sided")
        row["mannwhitney_u"] = float(mannwhitney.statistic)
        row["mannwhitney_p"] = float(mannwhitney.pvalue)
        if good_values.size >= 2 and poor_values.size >= 2:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                welch = stats.ttest_ind(good_values, poor_values, equal_var=False, nan_policy="omit")
            row["welch_t"] = float(welch.statistic)
            row["welch_p"] = float(welch.pvalue)
            row["status"] = "ok"
        else:
            row["welch_t"] = np.nan
            row["welch_p"] = np.nan
            row["status"] = "limited_n"
        delta_median = row["delta_median_good_minus_poor"]
        row["contrast_direction"] = (
            "good_gt_poor" if delta_median > 0 else "good_lt_poor" if delta_median < 0 else "equal"
        )
        rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["bh_fdr_q"] = np.nan
    for keys, group in out.groupby(["summary_level", "analysis_type", "time_bin"], sort=False):
        ok_mask = group["status"] == "ok"
        if ok_mask.any():
            q_values = bh_fdr(group.loc[ok_mask, "mannwhitney_p"])
            out.loc[group.loc[ok_mask].index, "bh_fdr_q"] = q_values.to_numpy(dtype=float)
    return out


def ensure_no_subject_overlap(part1_dir: Path, part2_dir: Path) -> int:
    part1 = pd.read_csv(part1_dir / "subject_outcome_index.csv")
    part2 = pd.read_csv(part2_dir / "subject_outcome_index.csv")
    overlap = set(part1["subject"].astype(str)) & set(part2["subject"].astype(str))
    if overlap:
        sample = sorted(overlap)[:10]
        raise ValueError(f"Subject overlap detected between 9D bundles: {sample}")
    return 0


def ensure_no_run_overlap(part1_run: pd.DataFrame, part2_run: pd.DataFrame) -> int:
    required = {"subject", "run", "acq"}
    if not required.issubset(part1_run.columns) or not required.issubset(part2_run.columns):
        return -1
    key1 = {
        f"{s}|{r}|{a}"
        for s, r, a in zip(
            part1_run["subject"].astype(str),
            part1_run["run"].astype(str),
            part1_run["acq"].astype(str),
        )
    }
    key2 = {
        f"{s}|{r}|{a}"
        for s, r, a in zip(
            part2_run["subject"].astype(str),
            part2_run["run"].astype(str),
            part2_run["acq"].astype(str),
        )
    }
    overlap = key1 & key2
    if overlap:
        sample = sorted(overlap)[:10]
        raise ValueError(f"Run overlap detected between 9D bundles: {sample}")
    return 0


def write_summary_markdown(
    cohort_name: str,
    patient_contrasts: pd.DataFrame,
    *,
    analysis_type: str,
    primary_time_bin: str,
) -> str:
    focus = patient_contrasts[
        (patient_contrasts["analysis_type"] == analysis_type)
        & (patient_contrasts["time_bin"] == primary_time_bin)
        & (patient_contrasts["status"] == "ok")
    ].copy()
    focus["abs_d"] = pd.to_numeric(focus["cohens_d"], errors="coerce").abs()
    lines = [
        f"# {cohort_name} 9D Jacobian Outcome Contrasts",
        "",
        f"- analysis type: `{analysis_type}`",
        f"- primary time bin: `{primary_time_bin}`",
        "",
        "## Top primary-bin contrasts by |d|",
        "",
    ]
    for _, row in focus.sort_values(["abs_d", "mannwhitney_p"], ascending=[False, True]).head(10).iterrows():
        lines.append(
            f"- `{row['metric']}`: medians `{row['good_median']:.6g}` vs `{row['poor_median']:.6g}`, "
            f"Cohen's `d = {row['cohens_d']:.3f}`, Mann-Whitney `p = {row['mannwhitney_p']:.3g}`, "
            f"BH-FDR `q = {row['bh_fdr_q']:.3g}`"
        )
    return "\n".join(lines) + "\n"


def build_article_candidate_table(
    cohort_name: str,
    patient_contrasts: pd.DataFrame,
    *,
    analysis_type: str,
    primary_time_bin: str,
) -> pd.DataFrame:
    focus = patient_contrasts[
        (patient_contrasts["analysis_type"] == analysis_type)
        & (patient_contrasts["time_bin"] == primary_time_bin)
        & (patient_contrasts["status"] == "ok")
    ].copy()
    if focus.empty:
        return pd.DataFrame()
    focus["cohort"] = cohort_name
    focus["abs_d"] = pd.to_numeric(focus["cohens_d"], errors="coerce").abs()
    focus["candidate_rank"] = np.arange(1, len(focus) + 1)
    focus["is_manuscript_candidate"] = focus["metric"].isin(MANUSCRIPT_CANDIDATES)
    focus = focus.sort_values(["abs_d", "mannwhitney_p"], ascending=[False, True]).reset_index(drop=True)
    focus["candidate_rank"] = np.arange(1, len(focus) + 1)
    return focus[
        [
            "cohort",
            "candidate_rank",
            "metric",
            "is_manuscript_candidate",
            "good_median",
            "poor_median",
            "delta_median_good_minus_poor",
            "cohens_d",
            "cliffs_delta",
            "mannwhitney_p",
            "bh_fdr_q",
            "n_good_subjects",
            "n_poor_subjects",
        ]
    ].copy()


def write_cohort_outputs(
    cohort_name: str,
    patient_frame: pd.DataFrame,
    run_frame: pd.DataFrame,
    *,
    output_dir: Path,
    analysis_type: str,
    primary_time_bin: str,
    good_label: str,
    poor_label: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    patient_desc = build_descriptive_table(patient_frame, good_label=good_label, poor_label=poor_label)
    patient_contrasts = build_contrast_table(patient_frame, good_label=good_label, poor_label=poor_label)
    run_desc = build_descriptive_table(run_frame, good_label=good_label, poor_label=poor_label)
    run_contrasts = build_contrast_table(run_frame, good_label=good_label, poor_label=poor_label)
    patient_desc.to_csv(output_dir / "patient_timebin_group_descriptives.csv", index=False)
    patient_contrasts.to_csv(output_dir / "patient_timebin_outcome_contrasts.csv", index=False)
    run_desc.to_csv(output_dir / "run_level_group_descriptives.csv", index=False)
    run_contrasts.to_csv(output_dir / "run_level_outcome_contrasts.csv", index=False)
    candidate_table = build_article_candidate_table(
        cohort_name,
        patient_contrasts,
        analysis_type=analysis_type,
        primary_time_bin=primary_time_bin,
    )
    candidate_table.to_csv(output_dir / "article_candidate_ranking.csv", index=False)
    manuscript_candidate_table = candidate_table[candidate_table["is_manuscript_candidate"]].copy()
    manuscript_candidate_table.to_csv(output_dir / "selection_audit_top5.csv", index=False)
    (output_dir / "summary.md").write_text(
        write_summary_markdown(
            cohort_name,
            patient_contrasts,
            analysis_type=analysis_type,
            primary_time_bin=primary_time_bin,
        ),
        encoding="utf-8",
    )


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    subject_overlap_count = ensure_no_subject_overlap(config.part1_input_dir, config.part2_input_dir)

    part1_manifest = load_manifest(config.part1_input_dir)
    part2_manifest = load_manifest(config.part2_input_dir)
    part1_patient = load_metric_frame(
        config.part1_input_dir, part1_manifest, summary_level="patient_timebin", analysis_type=config.analysis_type
    )
    part2_patient = load_metric_frame(
        config.part2_input_dir, part2_manifest, summary_level="patient_timebin", analysis_type=config.analysis_type
    )
    part1_run = load_metric_frame(config.part1_input_dir, part1_manifest, summary_level="run", analysis_type=config.analysis_type)
    part2_run = load_metric_frame(config.part2_input_dir, part2_manifest, summary_level="run", analysis_type=config.analysis_type)
    run_overlap_count = ensure_no_run_overlap(part1_run, part2_run)

    part1_patient = apply_endpoint_filter(
        part1_patient,
        good_label=config.good_label,
        poor_label=config.poor_label,
        good_cpc=config.good_cpc,
        poor_cpc=config.poor_cpc,
    )
    part2_patient = apply_endpoint_filter(
        part2_patient,
        good_label=config.good_label,
        poor_label=config.poor_label,
        good_cpc=config.good_cpc,
        poor_cpc=config.poor_cpc,
    )
    part1_run = apply_endpoint_filter(
        part1_run,
        good_label=config.good_label,
        poor_label=config.poor_label,
        good_cpc=config.good_cpc,
        poor_cpc=config.poor_cpc,
    )
    part2_run = apply_endpoint_filter(
        part2_run,
        good_label=config.good_label,
        poor_label=config.poor_label,
        good_cpc=config.good_cpc,
        poor_cpc=config.poor_cpc,
    )

    part1_patient = expand_with_pooled_timebin(part1_patient)
    part2_patient = expand_with_pooled_timebin(part2_patient)
    part1_run = expand_with_pooled_timebin(part1_run)
    part2_run = expand_with_pooled_timebin(part2_run)

    pooled_patient = pd.concat([part1_patient, part2_patient], ignore_index=True)
    pooled_run = pd.concat([part1_run, part2_run], ignore_index=True)

    write_cohort_outputs(
        "part1",
        part1_patient,
        part1_run,
        output_dir=config.output_dir / "part1",
        analysis_type=config.analysis_type,
        primary_time_bin=config.primary_time_bin,
        good_label=config.good_label,
        poor_label=config.poor_label,
    )
    write_cohort_outputs(
        "part2",
        part2_patient,
        part2_run,
        output_dir=config.output_dir / "part2",
        analysis_type=config.analysis_type,
        primary_time_bin=config.primary_time_bin,
        good_label=config.good_label,
        poor_label=config.poor_label,
    )
    write_cohort_outputs(
        "pooled",
        pooled_patient,
        pooled_run,
        output_dir=config.output_dir / "pooled",
        analysis_type=config.analysis_type,
        primary_time_bin=config.primary_time_bin,
        good_label=config.good_label,
        poor_label=config.poor_label,
    )

    part1_input_manifest = load_manifest(config.part1_input_dir)
    part2_input_manifest = load_manifest(config.part2_input_dir)
    manifest = {
        "part1_input_dir": str(config.part1_input_dir),
        "part2_input_dir": str(config.part2_input_dir),
        "output_dir": str(config.output_dir),
        "analysis_type": config.analysis_type,
        "primary_time_bin": config.primary_time_bin,
        "good_label": config.good_label,
        "poor_label": config.poor_label,
        "good_cpc": config.good_cpc,
        "poor_cpc": config.poor_cpc,
        "subject_overlap_count": subject_overlap_count,
        "run_overlap_count": run_overlap_count,
        "primary_time_bin_scope": {
            "part1": str((config.output_dir / "part1" / "selection_audit_top5.csv").resolve()),
            "part2": str((config.output_dir / "part2" / "selection_audit_top5.csv").resolve()),
            "pooled": str((config.output_dir / "pooled" / "selection_audit_top5.csv").resolve()),
        },
        "manuscript_candidates": list(MANUSCRIPT_CANDIDATES),
        "part1_input_manifest": part1_input_manifest,
        "part2_input_manifest": part2_input_manifest,
    }
    (config.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote 9D Jacobian outcome contrasts to {config.output_dir}")


if __name__ == "__main__":
    main()
