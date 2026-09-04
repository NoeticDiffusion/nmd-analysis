from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, ttest_ind


ARTICLE_DIR = Path(__file__).resolve().parents[1]
RESULTS_ROOT = ARTICLE_DIR / "results"
DEFAULT_OUTPUT_DIR = RESULTS_ROOT / "additional_qc_20260609"
MANIFEST_PATH = RESULTS_ROOT / "paper_exports_manifest.json"
PARTICIPANTS_PATH = ARTICLE_DIR / "metadata" / "participants.tsv"
BDI_BAND_ORDER = ["BDI 0-13", "BDI 14-19", "BDI 20-63"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run additional QC / robustness summaries for the paired depression PST article."
    )
    parser.add_argument("--results-root", type=Path, default=RESULTS_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def fmt(value: object) -> str:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return "nan"
    if not math.isfinite(parsed):
        return "nan"
    return f"{parsed:.4g}"


def load_participants(path: Path = PARTICIPANTS_PATH) -> pd.DataFrame:
    phenos = pd.read_csv(path, sep="\t")
    phenos["BDI"] = pd.to_numeric(phenos["BDI"], errors="coerce")
    phenos["bdi_band"] = pd.cut(
        phenos["BDI"],
        bins=[-0.1, 13, 19, 63],
        labels=BDI_BAND_ORDER,
        include_lowest=True,
    )
    phenos["bdi_band"] = phenos["bdi_band"].astype(object)
    return phenos


def cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    left = left[np.isfinite(left)]
    right = right[np.isfinite(right)]
    if left.size < 2 or right.size < 2:
        return float("nan")
    pooled = ((left.size - 1) * np.var(left, ddof=1) + (right.size - 1) * np.var(right, ddof=1)) / (
        left.size + right.size - 2
    )
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(right) - np.mean(left)) / math.sqrt(pooled))


def safe_spearman(left: pd.Series, right: pd.Series) -> tuple[float, float]:
    x = pd.to_numeric(left, errors="coerce").to_numpy(dtype=float)
    y = pd.to_numeric(right, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 6:
        return float("nan"), float("nan")
    x = x[mask]
    y = y[mask]
    if np.unique(x).size < 2 or np.unique(y).size < 2:
        return float("nan"), float("nan")
    rho, p_value = spearmanr(x, y)
    return float(rho), float(p_value)


def load_subject_metric_series(
    subject_metrics: pd.DataFrame,
    *,
    analysis_type: str,
    metric: str,
    source_group: str | None = None,
    target_group: str | None = None,
) -> pd.DataFrame:
    frame = subject_metrics[
        (subject_metrics["analysis_type"] == analysis_type)
        & (subject_metrics["metric"] == metric)
    ].copy()
    if source_group is not None and "source_group" in frame.columns:
        frame = frame[frame["source_group"] == source_group].copy()
    if target_group is not None and "target_group" in frame.columns:
        frame = frame[frame["target_group"] == target_group].copy()
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[frame["value"].notna()].copy()
    if frame.empty:
        return pd.DataFrame(columns=["subject_id", "value"])
    return frame.groupby("subject_id", as_index=False).agg(value=("value", "mean"))


def summarize_band_counts(frame: pd.DataFrame) -> dict[str, int]:
    out: dict[str, int] = {}
    for band in BDI_BAND_ORDER:
        out[band] = int(frame.loc[frame["bdi_band"] == band, "subject_id"].nunique())
    return out


def compute_lowhigh_and_rho(frame: pd.DataFrame) -> tuple[float, float, int, float, float]:
    low = pd.to_numeric(frame.loc[frame["bdi_band"] == "BDI 0-13", "value"], errors="coerce").dropna().to_numpy(dtype=float)
    high = pd.to_numeric(frame.loc[frame["bdi_band"] == "BDI 20-63", "value"], errors="coerce").dropna().to_numpy(dtype=float)
    if low.size >= 3 and high.size >= 3:
        _, p_value = ttest_ind(low, high, equal_var=False, nan_policy="omit")
        d_value = cohens_d(low, high)
        n_value = int(min(low.size, high.size))
    else:
        d_value, p_value, n_value = float("nan"), float("nan"), 0
    rho, rho_p = safe_spearman(frame["value"], frame["BDI"])
    return d_value, float(p_value) if np.isfinite(p_value) else float("nan"), n_value, rho, rho_p


def leave_one_out_summary(frame: pd.DataFrame) -> dict[str, float]:
    full_d, full_p, _, full_rho, full_rho_p = compute_lowhigh_and_rho(frame)
    d_values: list[float] = []
    rho_values: list[float] = []
    for subject_id in sorted(frame["subject_id"].dropna().astype(str).unique().tolist()):
        reduced = frame[frame["subject_id"].astype(str) != subject_id].copy()
        d_value, _, _, rho, _ = compute_lowhigh_and_rho(reduced)
        if np.isfinite(d_value):
            d_values.append(float(d_value))
        if np.isfinite(rho):
            rho_values.append(float(rho))
    sign_consistency_d = (
        float(np.mean(np.sign(np.asarray(d_values, dtype=float)) == np.sign(full_d)))
        if d_values and np.isfinite(full_d)
        else float("nan")
    )
    sign_consistency_rho = (
        float(np.mean(np.sign(np.asarray(rho_values, dtype=float)) == np.sign(full_rho)))
        if rho_values and np.isfinite(full_rho)
        else float("nan")
    )
    return {
        "full_d": full_d,
        "full_p": full_p,
        "full_rho": full_rho,
        "full_rho_p": full_rho_p,
        "loo_d_min": float(np.min(d_values)) if d_values else float("nan"),
        "loo_d_max": float(np.max(d_values)) if d_values else float("nan"),
        "loo_rho_min": float(np.min(rho_values)) if rho_values else float("nan"),
        "loo_rho_max": float(np.max(rho_values)) if rho_values else float("nan"),
        "loo_d_sign_consistency": sign_consistency_d,
        "loo_rho_sign_consistency": sign_consistency_rho,
    }


def build_selected_block_coverage(
    selected_summary: pd.DataFrame,
    subject_metrics: pd.DataFrame,
    participants: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in selected_summary.iterrows():
        series = load_subject_metric_series(
            subject_metrics,
            analysis_type=str(row["analysis_type"]),
            metric=str(row["metric"]),
            source_group=None if pd.isna(row.get("source_group")) else str(row.get("source_group")),
            target_group=None if pd.isna(row.get("target_group")) else str(row.get("target_group")),
        )
        merged = series.merge(
            participants[["participant_id", "BDI", "bdi_band"]],
            left_on="subject_id",
            right_on="participant_id",
            how="left",
        ).drop(columns=["participant_id"], errors="ignore")
        counts = summarize_band_counts(merged)
        rows.append(
            {
                "scope": "task_only",
                "block_key": row["block_key"],
                "block_title": row["block_title"],
                "analysis_type": row["analysis_type"],
                "metric": row["metric"],
                "n_subjects_total": int(merged["subject_id"].nunique()),
                "n_with_bdi": int(merged["BDI"].notna().sum()),
                "n_low": counts["BDI 0-13"],
                "n_mid": counts["BDI 14-19"],
                "n_high": counts["BDI 20-63"],
            }
        )
    return pd.DataFrame(rows)


def build_paired_block_coverage(paired_detail: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (block_key, block_title, analysis_type, metric), group in paired_detail.groupby(
        ["block_key", "block_title", "analysis_type", "metric"], dropna=False
    ):
        counts = summarize_band_counts(group)
        rows.append(
            {
                "scope": "paired_delta",
                "block_key": block_key,
                "block_title": block_title,
                "analysis_type": analysis_type,
                "metric": metric,
                "n_subjects_total": int(group["subject_id"].nunique()),
                "n_with_bdi": int(group["BDI"].notna().sum()),
                "n_low": counts["BDI 0-13"],
                "n_mid": counts["BDI 14-19"],
                "n_high": counts["BDI 20-63"],
            }
        )
    return pd.DataFrame(rows)


def build_event_coverage(event_subjects: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (family, bin_label), group in event_subjects.groupby(["event_family", "bin_label"], dropna=False):
        rows.append(
            {
                "event_family": family,
                "bin_label": bin_label,
                "n_subjects": int(group["subject_id"].nunique()),
                "n_rows_median": float(group["n_rows"].median()),
                "n_rows_min": int(group["n_rows"].min()),
                "n_rows_max": int(group["n_rows"].max()),
                "n_events_median": float(group["n_events"].median()),
                "n_events_min": int(group["n_events"].min()),
                "n_events_max": int(group["n_events"].max()),
                "speed_mean_median": float(pd.to_numeric(group["speed_mean"], errors="coerce").median()),
            }
        )
    return pd.DataFrame(rows).sort_values(["event_family", "bin_label"]).reset_index(drop=True)


def build_leave_one_out_tables(
    selected_summary: pd.DataFrame,
    paired_summary: pd.DataFrame,
    subject_metrics: pd.DataFrame,
    paired_detail: pd.DataFrame,
    participants: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in selected_summary.iterrows():
        series = load_subject_metric_series(
            subject_metrics,
            analysis_type=str(row["analysis_type"]),
            metric=str(row["metric"]),
            source_group=None if pd.isna(row.get("source_group")) else str(row.get("source_group")),
            target_group=None if pd.isna(row.get("target_group")) else str(row.get("target_group")),
        )
        merged = series.merge(
            participants[["participant_id", "BDI", "bdi_band"]],
            left_on="subject_id",
            right_on="participant_id",
            how="left",
        ).drop(columns=["participant_id"], errors="ignore")
        loo = leave_one_out_summary(merged)
        rows.append(
            {
                "scope": "task_only",
                "block_key": row["block_key"],
                "block_title": row["block_title"],
                "analysis_type": row["analysis_type"],
                "metric": row["metric"],
                **loo,
            }
        )

    for _, row in paired_summary.iterrows():
        group = paired_detail[
            (paired_detail["block_key"] == row["block_key"])
            & (paired_detail["analysis_type"] == row["analysis_type"])
            & (paired_detail["metric"] == row["metric"])
        ].copy()
        group = group.rename(columns={"delta_value": "value"})
        loo = leave_one_out_summary(group)
        rows.append(
            {
                "scope": "paired_delta",
                "block_key": row["block_key"],
                "block_title": row["block_title"],
                "analysis_type": row["analysis_type"],
                "metric": row["metric"],
                **loo,
            }
        )
    return pd.DataFrame(rows)


def build_summary_markdown(
    coverage: pd.DataFrame,
    event_coverage: pd.DataFrame,
    loo: pd.DataFrame,
) -> str:
    lines = [
        "# Depression PST supplementary QC / robustness summary",
        "",
        "This supplement-facing QC pass focuses on three practical review questions:",
        "",
        "1. how many usable subjects support each selected task and paired block,",
        "2. how stable the event-family coverage is across subjects,",
        "3. and whether the selected rows preserve direction under leave-one-subject-out omission.",
        "",
        "## Selected block coverage",
        "",
    ]
    for _, row in coverage.iterrows():
        lines.append(
            f"- `{row['scope']}` / `{row['block_title']}` / `{row['metric']}`: "
            f"total `{int(row['n_subjects_total'])}`, low `{int(row['n_low'])}`, mid `{int(row['n_mid'])}`, high `{int(row['n_high'])}`."
        )
    lines.extend(["", "## Event coverage", ""])
    for _, row in event_coverage.iterrows():
        lines.append(
            f"- `{row['event_family']}` / `{row['bin_label']}`: "
            f"`n_subjects = {int(row['n_subjects'])}`, median events `{fmt(row['n_events_median'])}`, median rows `{fmt(row['n_rows_median'])}`."
        )
    lines.extend(["", "## Leave-one-subject-out stability", ""])
    for _, row in loo.iterrows():
        lines.append(
            f"- `{row['scope']}` / `{row['block_title']}` / `{row['metric']}`: "
            f"full `d = {fmt(row['full_d'])}`, leave-one-out `d` range `{fmt(row['loo_d_min'])}` to `{fmt(row['loo_d_max'])}`, "
            f"sign consistency `{fmt(row['loo_d_sign_consistency'])}`; "
            f"full `rho = {fmt(row['full_rho'])}`, leave-one-out `rho` range `{fmt(row['loo_rho_min'])}` to `{fmt(row['loo_rho_max'])}`."
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- The `9D` Jacobian, block-MNJ, and reachability rows use smaller valid denominators than the full cohort and should be read with those denominators visible.",
            "- Leave-one-subject-out omission is a directional stability check only; it is not an external replication test.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)

    manifest = json.loads((args.results_root / "paper_exports_manifest.json").read_text(encoding="utf-8"))
    participants = load_participants()
    task_subject_metrics = pd.read_parquet(manifest["task_subject_metrics_path"])
    rest_subject_metrics = pd.read_parquet(manifest["rest_subject_metrics_path"])

    selected_summary = pd.read_csv(args.results_root / "selected_metrics_summary.csv", low_memory=False)
    paired_summary = pd.read_csv(args.results_root / "paired_delta_summary.csv", low_memory=False)
    paired_detail = pd.read_csv(args.results_root / "paired_delta_detail.csv", low_memory=False)
    event_subjects = pd.read_csv(args.results_root / "event_locked_subject_summary.csv", low_memory=False)

    task_coverage = build_selected_block_coverage(selected_summary, task_subject_metrics, participants)
    paired_coverage = build_paired_block_coverage(paired_detail)
    coverage = pd.concat([task_coverage, paired_coverage], ignore_index=True)
    event_coverage = build_event_coverage(event_subjects)
    loo = build_leave_one_out_tables(
        selected_summary,
        paired_summary,
        task_subject_metrics,
        paired_detail,
        participants,
    )

    task_subject_counts = (
        task_subject_metrics.groupby("analysis_type", dropna=False)["subject_id"].nunique().reset_index(name="n_subjects")
    )
    rest_subject_counts = (
        rest_subject_metrics.groupby("analysis_type", dropna=False)["subject_id"].nunique().reset_index(name="n_subjects")
    )
    task_subject_counts.to_csv(args.output_dir / "qc_task_analysis_subject_counts.csv", index=False)
    rest_subject_counts.to_csv(args.output_dir / "qc_rest_analysis_subject_counts.csv", index=False)
    coverage.to_csv(args.output_dir / "qc_selected_block_coverage.csv", index=False)
    event_coverage.to_csv(args.output_dir / "qc_event_coverage_summary.csv", index=False)
    loo.to_csv(args.output_dir / "qc_leave_one_subject_out.csv", index=False)

    summary_md = build_summary_markdown(coverage, event_coverage, loo)
    (args.output_dir / "additional_qc_summary.md").write_text(summary_md, encoding="utf-8")

    manifest_out = {
        "results_root": str(args.results_root),
        "output_dir": str(args.output_dir),
        "task_subject_metrics_path": manifest["task_subject_metrics_path"],
        "rest_subject_metrics_path": manifest["rest_subject_metrics_path"],
        "written_files": {
            "task_subject_counts": str(args.output_dir / "qc_task_analysis_subject_counts.csv"),
            "rest_subject_counts": str(args.output_dir / "qc_rest_analysis_subject_counts.csv"),
            "selected_block_coverage": str(args.output_dir / "qc_selected_block_coverage.csv"),
            "event_coverage": str(args.output_dir / "qc_event_coverage_summary.csv"),
            "leave_one_out": str(args.output_dir / "qc_leave_one_subject_out.csv"),
            "summary_md": str(args.output_dir / "additional_qc_summary.md"),
        },
    }
    (args.output_dir / "additional_qc_manifest.json").write_text(json.dumps(manifest_out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
