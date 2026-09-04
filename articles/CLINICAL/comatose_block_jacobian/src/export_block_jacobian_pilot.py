from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy import stats


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_DIR = ARTICLE_DIR / "results" / "mnps_summary_20260528_part1_block_jacobian_cpc15_primary12h"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "block_pilot_20260528_part1_cpc15_primary12h"
DEFAULT_ANALYSIS_TYPE = "global_mnps_jacobian_9d_block_jacobian"
DEFAULT_PRIMARY_TIME_BIN = "0_12h"
DEFAULT_GOOD_CPC = 1
DEFAULT_POOR_CPC = 5
RAW_METRIC_COLUMNS: tuple[str, ...] = (
    "block_trace_mean",
    "block_frobenius_mean",
    "block_anisotropy_mean",
    "c_sym_mean",
    "c_rot_mean",
)
DIAGONAL_BLOCKS: tuple[tuple[str, str], ...] = (("m", "m"), ("d", "d"), ("e", "e"))
OFFDIAGONAL_BLOCKS: tuple[tuple[str, str], ...] = (
    ("m", "d"),
    ("m", "e"),
    ("d", "m"),
    ("d", "e"),
    ("e", "m"),
    ("e", "d"),
)
DIRECTIONAL_PAIRS: tuple[tuple[tuple[str, str], tuple[str, str]], ...] = (
    (("m", "d"), ("d", "m")),
    (("m", "e"), ("e", "m")),
    (("d", "e"), ("e", "d")),
)


@dataclass(frozen=True)
class Config:
    summary_dir: Path
    output_dir: Path
    analysis_type: str
    primary_time_bin: str
    good_cpc: int
    poor_cpc: int


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Export pilot outcome contrasts for the I-CARE block-Jacobian coma wrapper."
    )
    parser.add_argument("--summary-dir", type=Path, default=DEFAULT_SUMMARY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--analysis-type", type=str, default=DEFAULT_ANALYSIS_TYPE)
    parser.add_argument("--primary-time-bin", type=str, default=DEFAULT_PRIMARY_TIME_BIN)
    parser.add_argument("--good-cpc", type=int, default=DEFAULT_GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=DEFAULT_POOR_CPC)
    args = parser.parse_args()
    return Config(
        summary_dir=args.summary_dir,
        output_dir=args.output_dir,
        analysis_type=args.analysis_type,
        primary_time_bin=args.primary_time_bin,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
    )


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    good = np.asarray(good, dtype=float)
    poor = np.asarray(poor, dtype=float)
    good = good[np.isfinite(good)]
    poor = poor[np.isfinite(poor)]
    if good.size < 2 or poor.size < 2:
        return float("nan")
    pooled = ((good.size - 1) * np.var(good, ddof=1) + (poor.size - 1) * np.var(poor, ddof=1)) / (
        good.size + poor.size - 2
    )
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(good) - np.mean(poor)) / np.sqrt(pooled))


def cliffs_delta(good: np.ndarray, poor: np.ndarray) -> float:
    good = np.asarray(good, dtype=float)
    poor = np.asarray(poor, dtype=float)
    good = good[np.isfinite(good)]
    poor = poor[np.isfinite(poor)]
    if good.size == 0 or poor.size == 0:
        return float("nan")
    diff = np.subtract.outer(good, poor)
    return float((np.sum(diff > 0) - np.sum(diff < 0)) / diff.size)


def mean_or_nan(values: Iterable[Any]) -> float:
    arr = pd.to_numeric(pd.Series(list(values)), errors="coerce").to_numpy(dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return float("nan")
    return float(np.mean(arr))


def label_from_cpc(value: Any, *, good_cpc: int, poor_cpc: int) -> str | None:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if not np.isfinite(numeric):
        return None
    if int(numeric) == int(good_cpc):
        return "CPC1"
    if int(numeric) == int(poor_cpc):
        return "CPC5"
    return None


def load_summary_manifest(summary_dir: Path) -> dict[str, Any]:
    return json.loads((summary_dir / "metric_handoff_manifest.json").read_text(encoding="utf-8"))


def load_block_frame(config: Config) -> pd.DataFrame:
    frame = pd.read_csv(config.summary_dir / "patient_timebin_adapter_summaries.csv", low_memory=False)
    frame = frame[frame["analysis_type"] == config.analysis_type].copy()
    if "time_bin" in frame.columns:
        frame = frame[frame["time_bin"].astype(str) == config.primary_time_bin].copy()
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)])].copy()
    frame["outcome_label"] = frame["cpc_numeric"].map(
        lambda value: label_from_cpc(value, good_cpc=config.good_cpc, poor_cpc=config.poor_cpc)
    )
    frame = frame[frame["outcome_label"].notna()].copy()
    frame["source_group"] = frame["source_group"].astype(str)
    frame["target_group"] = frame["target_group"].astype(str)
    frame["block_id"] = frame["target_group"] + frame["source_group"]
    frame["block_class"] = np.where(
        frame["source_group"] == frame["target_group"],
        "within_family_deformation",
        "cross_family_coupling",
    )
    for column in RAW_METRIC_COLUMNS:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.reset_index(drop=True)


def build_raw_metric_long(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    id_columns = [
        column
        for column in (
            "analysis_type",
            "subject",
            "time_bin",
            "cpc",
            "cpc_numeric",
            "outcome",
            "outcome_label",
            "hospital",
            "age",
            "sex",
            "shockable_rhythm",
            "source_group",
            "target_group",
            "block_id",
            "block_class",
            "n_runs",
            "n_rows",
            "n_timepoints",
            "aggregation_weight_total",
        )
        if column in frame.columns
    ]
    for metric in RAW_METRIC_COLUMNS:
        if metric not in frame.columns:
            continue
        metric_frame = frame[id_columns].copy()
        metric_frame["metric"] = metric
        metric_frame["value"] = pd.to_numeric(frame[metric], errors="coerce")
        metric_frame = metric_frame[np.isfinite(metric_frame["value"].to_numpy(dtype=float))].copy()
        if metric_frame.empty:
            continue
        metric_frame["contrast_kind"] = "raw_block"
        rows.append(metric_frame)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def _group_metadata(frame: pd.DataFrame) -> list[str]:
    preferred = (
        "analysis_type",
        "subject",
        "time_bin",
        "cpc",
        "cpc_numeric",
        "outcome",
        "outcome_label",
        "hospital",
        "age",
        "sex",
        "shockable_rhythm",
    )
    return [column for column in preferred if column in frame.columns]


def _block_metric_lookup(group: pd.DataFrame, *, target: str, source: str, metric: str) -> float:
    subset = group[(group["target_group"] == target) & (group["source_group"] == source)]
    if subset.empty or metric not in subset.columns:
        return float("nan")
    values = pd.to_numeric(subset[metric], errors="coerce").to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan")
    return float(values[0])


def build_aggregate_feature_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    metadata = _group_metadata(frame)
    rows: list[dict[str, Any]] = []
    for keys, group in frame.groupby(metadata, dropna=False, sort=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(metadata, keys))
        diagonal = group[group["source_group"] == group["target_group"]].copy()
        offdiag = group[group["source_group"] != group["target_group"]].copy()
        row["diag_block_frobenius_mean"] = mean_or_nan(diagonal.get("block_frobenius_mean", []))
        row["offdiag_block_frobenius_mean"] = mean_or_nan(offdiag.get("block_frobenius_mean", []))
        if np.isfinite(row["diag_block_frobenius_mean"]) and np.isfinite(row["offdiag_block_frobenius_mean"]):
            row["diag_minus_offdiag_frobenius"] = (
                row["diag_block_frobenius_mean"] - row["offdiag_block_frobenius_mean"]
            )
        else:
            row["diag_minus_offdiag_frobenius"] = float("nan")
        row["diag_block_trace_mean"] = mean_or_nan(diagonal.get("block_trace_mean", []))
        row["diag_block_anisotropy_mean"] = mean_or_nan(diagonal.get("block_anisotropy_mean", []))
        row["offdiag_c_sym_mean"] = mean_or_nan(offdiag.get("c_sym_mean", []))
        row["offdiag_c_rot_mean"] = mean_or_nan(offdiag.get("c_rot_mean", []))
        for metric, short_name in (
            ("block_frobenius_mean", "frobenius"),
            ("c_sym_mean", "c_sym"),
            ("c_rot_mean", "c_rot"),
        ):
            for (target_a, source_a), (target_b, source_b) in DIRECTIONAL_PAIRS:
                forward_name = f"{target_a}{source_a}"
                reverse_name = f"{target_b}{source_b}"
                forward = _block_metric_lookup(group, target=target_a, source=source_a, metric=metric)
                reverse = _block_metric_lookup(group, target=target_b, source=source_b, metric=metric)
                if np.isfinite(forward) and np.isfinite(reverse):
                    row[f"{short_name}_{forward_name}_minus_{reverse_name}"] = forward - reverse
                    row[f"{short_name}_{forward_name}_{reverse_name}_absdiff"] = abs(forward - reverse)
                else:
                    row[f"{short_name}_{forward_name}_minus_{reverse_name}"] = float("nan")
                    row[f"{short_name}_{forward_name}_{reverse_name}_absdiff"] = float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def build_aggregate_metric_long(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    id_columns = _group_metadata(frame)
    value_columns = [column for column in frame.columns if column not in set(id_columns)]
    rows: list[pd.DataFrame] = []
    for column in value_columns:
        values = pd.to_numeric(frame[column], errors="coerce")
        if not np.isfinite(values.to_numpy(dtype=float)).any():
            continue
        finite_values = values.to_numpy(dtype=float)
        finite_values = finite_values[np.isfinite(finite_values)]
        if finite_values.size > 0 and float(np.nanstd(finite_values)) == 0.0:
            continue
        metric_frame = frame[id_columns].copy()
        metric_frame["metric"] = column
        metric_frame["value"] = values
        metric_frame = metric_frame[np.isfinite(metric_frame["value"].to_numpy(dtype=float))].copy()
        if metric_frame.empty:
            continue
        metric_frame["source_group"] = None
        metric_frame["target_group"] = None
        metric_frame["block_id"] = None
        if column.startswith("diag_") or column.startswith("offdiag_") or column.startswith("diag_minus_offdiag_"):
            metric_frame["contrast_kind"] = "aggregate_balance"
            metric_frame["block_class"] = "diagonal_vs_offdiagonal_balance"
        elif "_minus_" in column or column.endswith("_absdiff"):
            metric_frame["contrast_kind"] = "directional_asymmetry"
            metric_frame["block_class"] = "directional_asymmetry"
        else:
            metric_frame["contrast_kind"] = "aggregate_summary"
            metric_frame["block_class"] = "aggregate_summary"
        rows.append(metric_frame)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


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


def build_contrast_table(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    group_columns = [
        column
        for column in ("contrast_kind", "block_class", "metric", "source_group", "target_group", "block_id")
        if column in frame.columns
    ]
    rows: list[dict[str, Any]] = []
    for keys, group in frame.groupby(group_columns, dropna=False, sort=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_columns, keys))
        good_rows = group[group["outcome_label"] == "CPC1"].copy()
        poor_rows = group[group["outcome_label"] == "CPC5"].copy()
        good = pd.to_numeric(good_rows["value"], errors="coerce").dropna().to_numpy(dtype=float)
        poor = pd.to_numeric(poor_rows["value"], errors="coerce").dropna().to_numpy(dtype=float)
        good_stats = summary_stats(good)
        poor_stats = summary_stats(poor)
        row.update(
            {
                "n_cpc1_rows": int(good.size),
                "n_cpc5_rows": int(poor.size),
                "n_cpc1_subjects": int(good_rows["subject"].astype(str).nunique()) if not good_rows.empty else 0,
                "n_cpc5_subjects": int(poor_rows["subject"].astype(str).nunique()) if not poor_rows.empty else 0,
                "cpc1_mean": good_stats["mean"],
                "cpc1_median": good_stats["median"],
                "cpc1_sd": good_stats["sd"],
                "cpc1_iqr": good_stats["iqr"],
                "cpc5_mean": poor_stats["mean"],
                "cpc5_median": poor_stats["median"],
                "cpc5_sd": poor_stats["sd"],
                "cpc5_iqr": poor_stats["iqr"],
                "delta_mean_cpc1_minus_cpc5": (
                    good_stats["mean"] - poor_stats["mean"]
                    if np.isfinite(good_stats["mean"]) and np.isfinite(poor_stats["mean"])
                    else np.nan
                ),
                "delta_median_cpc1_minus_cpc5": (
                    good_stats["median"] - poor_stats["median"]
                    if np.isfinite(good_stats["median"]) and np.isfinite(poor_stats["median"])
                    else np.nan
                ),
                "cohens_d": cohens_d(good, poor),
                "cliffs_delta": cliffs_delta(good, poor),
            }
        )
        if good.size == 0 or poor.size == 0:
            row["status"] = "insufficient_groups"
            row["mannwhitney_u"] = np.nan
            row["mannwhitney_p"] = np.nan
            row["contrast_direction"] = "unavailable"
            rows.append(row)
            continue
        test = stats.mannwhitneyu(good, poor, alternative="two-sided")
        row["status"] = "ok"
        row["mannwhitney_u"] = float(test.statistic)
        row["mannwhitney_p"] = float(test.pvalue)
        delta = row["delta_median_cpc1_minus_cpc5"]
        row["contrast_direction"] = "cpc1_gt_cpc5" if delta > 0 else "cpc1_lt_cpc5" if delta < 0 else "equal"
        rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["abs_d"] = pd.to_numeric(out["cohens_d"], errors="coerce").abs()
    out["bh_fdr_q_all"] = np.nan
    ok_mask = out["status"] == "ok"
    if ok_mask.any():
        out.loc[ok_mask, "bh_fdr_q_all"] = bh_fdr(out.loc[ok_mask, "mannwhitney_p"]).to_numpy(dtype=float)
    out["bh_fdr_q_within_kind"] = np.nan
    for contrast_kind, subset in out.groupby("contrast_kind", sort=False):
        ok_subset = subset["status"] == "ok"
        if ok_subset.any():
            q_values = bh_fdr(subset.loc[ok_subset, "mannwhitney_p"])
            out.loc[subset.loc[ok_subset].index, "bh_fdr_q_within_kind"] = q_values.to_numpy(dtype=float)
    return out.sort_values(
        ["contrast_kind", "block_class", "abs_d", "mannwhitney_p"],
        ascending=[True, True, False, True],
    ).reset_index(drop=True)


def build_selection_audit(contrasts: pd.DataFrame) -> pd.DataFrame:
    if contrasts.empty:
        return pd.DataFrame()
    focus = contrasts[contrasts["status"] == "ok"].copy()
    if focus.empty:
        return focus
    focus["selection_rank"] = np.arange(1, len(focus) + 1)
    focus = focus.sort_values(["contrast_kind", "abs_d", "mannwhitney_p"], ascending=[True, False, True]).reset_index(drop=True)
    focus["selection_rank"] = np.arange(1, len(focus) + 1)
    return focus[
        [
            "selection_rank",
            "contrast_kind",
            "block_class",
            "metric",
            "block_id",
            "source_group",
            "target_group",
            "cpc1_median",
            "cpc5_median",
            "delta_median_cpc1_minus_cpc5",
            "cohens_d",
            "cliffs_delta",
            "mannwhitney_p",
            "bh_fdr_q_all",
            "bh_fdr_q_within_kind",
            "n_cpc1_subjects",
            "n_cpc5_subjects",
        ]
    ].copy()


def load_run_error_counts(processed_root: Path, subject_index: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    path = processed_root / "run_errors.json"
    if not path.exists():
        return pd.DataFrame(), {"run_errors_present": False}
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors = payload.get("errors") or []
    rows = []
    for error in errors:
        rows.append(
            {
                "subject": error.get("subject"),
                "run": error.get("run"),
                "acq": error.get("acq"),
                "error_type": error.get("error_type"),
                "error_message": error.get("error_message"),
                "rows": error.get("rows"),
            }
        )
    frame = pd.DataFrame(rows)
    if not frame.empty and not subject_index.empty:
        frame = frame.merge(subject_index, on="subject", how="left")
    subject_counts = (
        frame.groupby(["subject", "cpc", "outcome"], dropna=False).size().reset_index(name="n_failed_groupings")
        if not frame.empty
        else pd.DataFrame(columns=["subject", "cpc", "outcome", "n_failed_groupings"])
    )
    summary = {
        "run_errors_present": True,
        "errors_total": int(payload.get("counts", {}).get("errors_total", len(frame))),
        "groupings_total": int(payload.get("counts", {}).get("groupings_total", 0)),
        "subjects_with_errors": int(subject_counts["subject"].astype(str).nunique()) if not subject_counts.empty else 0,
        "errors_by_cpc": (
            subject_counts.groupby("cpc", dropna=False)["n_failed_groupings"].sum().to_dict()
            if not subject_counts.empty and "cpc" in subject_counts.columns
            else {}
        ),
        "errors_by_outcome": (
            subject_counts.groupby("outcome", dropna=False)["n_failed_groupings"].sum().to_dict()
            if not subject_counts.empty and "outcome" in subject_counts.columns
            else {}
        ),
    }
    return subject_counts.sort_values(["n_failed_groupings", "subject"], ascending=[False, True]), summary


def build_summary_markdown(
    *,
    patient_frame: pd.DataFrame,
    contrasts: pd.DataFrame,
    selection_audit: pd.DataFrame,
    run_error_summary: dict[str, Any],
) -> str:
    lines = [
        "# Block-Jacobian Pilot Summary",
        "",
        f"- patient rows: `{int(len(patient_frame))}`",
        f"- unique subjects: `{int(patient_frame['subject'].astype(str).nunique()) if not patient_frame.empty else 0}`",
        f"- CPC1 subjects: `{int(patient_frame.loc[patient_frame['outcome_label'] == 'CPC1', 'subject'].astype(str).nunique()) if not patient_frame.empty else 0}`",
        f"- CPC5 subjects: `{int(patient_frame.loc[patient_frame['outcome_label'] == 'CPC5', 'subject'].astype(str).nunique()) if not patient_frame.empty else 0}`",
        "",
        "## Top within-family raw block contrasts",
        "",
    ]
    for _, row in selection_audit[
        (selection_audit["contrast_kind"] == "raw_block")
        & (selection_audit["block_class"] == "within_family_deformation")
    ].head(6).iterrows():
        lines.append(
            f"- `{row['metric']}` on `{row['block_id']}`: medians `{row['cpc1_median']:.6g}` vs `{row['cpc5_median']:.6g}`, "
            f"`d = {row['cohens_d']:.3f}`, `p = {row['mannwhitney_p']:.3g}`"
        )
    lines.extend(["", "## Top cross-family raw block contrasts", ""])
    for _, row in selection_audit[
        (selection_audit["contrast_kind"] == "raw_block")
        & (selection_audit["block_class"] == "cross_family_coupling")
    ].head(6).iterrows():
        lines.append(
            f"- `{row['metric']}` on `{row['block_id']}`: medians `{row['cpc1_median']:.6g}` vs `{row['cpc5_median']:.6g}`, "
            f"`d = {row['cohens_d']:.3f}`, `p = {row['mannwhitney_p']:.3g}`"
        )
    lines.extend(["", "## Balance and asymmetry aggregates", ""])
    for _, row in selection_audit[selection_audit["contrast_kind"] != "raw_block"].head(8).iterrows():
        lines.append(
            f"- `{row['metric']}`: medians `{row['cpc1_median']:.6g}` vs `{row['cpc5_median']:.6g}`, "
            f"`d = {row['cohens_d']:.3f}`, `p = {row['mannwhitney_p']:.3g}`"
        )
    lines.extend(
        [
            "",
            "## Upstream run errors",
            "",
            f"- run errors present: `{run_error_summary.get('run_errors_present', False)}`",
            f"- errors total: `{run_error_summary.get('errors_total', 0)}`",
            f"- subjects with errors: `{run_error_summary.get('subjects_with_errors', 0)}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    config = parse_args()
    ensure_output_dir(config.output_dir)

    manifest = load_summary_manifest(config.summary_dir)
    patient_frame = load_block_frame(config)
    raw_long = build_raw_metric_long(patient_frame)
    aggregate_frame = build_aggregate_feature_frame(patient_frame)
    aggregate_long = build_aggregate_metric_long(aggregate_frame)
    combined_long = pd.concat([raw_long, aggregate_long], ignore_index=True)
    contrasts = build_contrast_table(combined_long)
    selection_audit = build_selection_audit(contrasts)

    subject_index = pd.read_csv(config.summary_dir / "subject_outcome_index.csv", low_memory=False)
    processed_root = Path(str(manifest["processed_root"]))
    run_error_subject_counts, run_error_summary = load_run_error_counts(processed_root, subject_index)

    raw_long.to_csv(config.output_dir / "patient_block_raw_metrics_long.csv", index=False)
    aggregate_frame.to_csv(config.output_dir / "patient_block_aggregate_features.csv", index=False)
    aggregate_long.to_csv(config.output_dir / "patient_block_aggregate_metrics_long.csv", index=False)
    combined_long.to_csv(config.output_dir / "patient_block_metric_long.csv", index=False)
    contrasts.to_csv(config.output_dir / "block_metric_outcome_contrasts.csv", index=False)
    selection_audit.to_csv(config.output_dir / "selection_audit_top_candidates.csv", index=False)
    run_error_subject_counts.to_csv(config.output_dir / "run_error_subject_counts.csv", index=False)

    summary_md = build_summary_markdown(
        patient_frame=patient_frame,
        contrasts=contrasts,
        selection_audit=selection_audit,
        run_error_summary=run_error_summary,
    )
    (config.output_dir / "block_pilot_summary.md").write_text(summary_md, encoding="utf-8")

    pilot_manifest = {
        "summary_dir": str(config.summary_dir),
        "output_dir": str(config.output_dir),
        "analysis_type": config.analysis_type,
        "primary_time_bin": config.primary_time_bin,
        "good_cpc": config.good_cpc,
        "poor_cpc": config.poor_cpc,
        "processed_root": str(processed_root),
        "n_patient_rows": int(len(patient_frame)),
        "n_unique_subjects": int(patient_frame["subject"].astype(str).nunique()) if not patient_frame.empty else 0,
        "n_cpc1_subjects": (
            int(patient_frame.loc[patient_frame["outcome_label"] == "CPC1", "subject"].astype(str).nunique())
            if not patient_frame.empty
            else 0
        ),
        "n_cpc5_subjects": (
            int(patient_frame.loc[patient_frame["outcome_label"] == "CPC5", "subject"].astype(str).nunique())
            if not patient_frame.empty
            else 0
        ),
        "raw_metric_columns": list(RAW_METRIC_COLUMNS),
        "available_block_ids": sorted(patient_frame["block_id"].dropna().astype(str).unique().tolist()) if not patient_frame.empty else [],
        "run_error_summary": run_error_summary,
        "input_manifest": manifest,
    }
    (config.output_dir / "block_pilot_manifest.json").write_text(
        json.dumps(pilot_manifest, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote block-Jacobian pilot exports to {config.output_dir}")


if __name__ == "__main__":
    main()
