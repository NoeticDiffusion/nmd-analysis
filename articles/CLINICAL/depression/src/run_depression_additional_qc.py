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
        description="Run supplementary QC / robustness summaries for the resting-state depression article."
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


def build_leave_one_out_table(
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
        rows.append(
            {
                "block_key": row["block_key"],
                "block_title": row["block_title"],
                "analysis_type": row["analysis_type"],
                "metric": row["metric"],
                **leave_one_out_summary(merged),
            }
        )
    return pd.DataFrame(rows)


def build_summary_markdown(
    coverage: pd.DataFrame,
    loo: pd.DataFrame,
    centroid_focus: pd.DataFrame,
) -> str:
    lines = [
        "# Resting-state depression supplementary QC / robustness summary",
        "",
        "This QC pass focuses on three review-facing questions:",
        "",
        "1. how many usable subjects support each selected article block,",
        "2. whether the selected low/high and continuous-BDI rows are directionally stable under leave-one-subject-out omission,",
        "3. and which centroid-adjusted rows remain most relevant after accounting for baseline coordinate position.",
        "",
        "## Selected block coverage",
        "",
    ]
    for _, row in coverage.iterrows():
        lines.append(
            f"- `{row['block_title']}` / `{row['metric']}`: "
            f"total `{int(row['n_subjects_total'])}`, low `{int(row['n_low'])}`, mid `{int(row['n_mid'])}`, high `{int(row['n_high'])}`."
        )
    lines.extend(["", "## Leave-one-subject-out stability", ""])
    for _, row in loo.iterrows():
        lines.append(
            f"- `{row['block_title']}` / `{row['metric']}`: "
            f"full `d = {fmt(row['full_d'])}`, leave-one-out `d` range `{fmt(row['loo_d_min'])}` to `{fmt(row['loo_d_max'])}`, "
            f"sign consistency `{fmt(row['loo_d_sign_consistency'])}`; "
            f"full `rho = {fmt(row['full_rho'])}`, leave-one-out `rho` range `{fmt(row['loo_rho_min'])}` to `{fmt(row['loo_rho_max'])}`."
        )
    lines.extend(["", "## Centroid-adjusted focus", ""])
    for _, row in centroid_focus.iterrows():
        label = str(row["block_title"])
        if pd.notna(row.get("source_group")) or pd.notna(row.get("target_group")):
            label = f"{label} ({row.get('source_group')}->{row.get('target_group')})"
        lines.append(
            f"- `{label}` / `{row['metric']}`: "
            f"adjusted beta `{fmt(row['adjusted_group_beta'])}`, adjusted q `{fmt(row['adjusted_q_value'])}`, residualized d `{fmt(row['residualized_effect_size'])}`."
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- The strongest unadjusted resting-state task surface remains reachability, 9D MNJ, and distribution; the centroid-adjusted pass is a sensitivity analysis rather than a replacement endpoint.",
            "- Leave-one-subject-out omission is a directional stability check only and should not be over-read as external replication.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)

    manifest = json.loads((args.results_root / "paper_exports_manifest.json").read_text(encoding="utf-8"))
    participants = load_participants()
    subject_metrics = pd.read_parquet(manifest["subject_metrics_path"])
    selected_summary = pd.read_csv(args.results_root / "selected_metrics_summary.csv", low_memory=False)
    centroid_adjusted = pd.read_csv(args.results_root / "centroid_adjusted_dynamic_summary.csv", low_memory=False)

    coverage = build_selected_block_coverage(selected_summary, subject_metrics, participants)
    loo = build_leave_one_out_table(selected_summary, subject_metrics, participants)
    centroid_focus = centroid_adjusted.sort_values(
        ["adjusted_q_value", "adjusted_p_value", "abs_adjusted_beta"],
        ascending=[True, True, False],
        na_position="last",
    ).reset_index(drop=True)

    analysis_subject_counts = (
        subject_metrics.groupby("analysis_type", dropna=False)["subject_id"].nunique().reset_index(name="n_subjects")
    )

    coverage.to_csv(args.output_dir / "qc_selected_block_coverage.csv", index=False)
    loo.to_csv(args.output_dir / "qc_leave_one_subject_out.csv", index=False)
    centroid_focus.to_csv(args.output_dir / "qc_centroid_adjusted_focus.csv", index=False)
    analysis_subject_counts.to_csv(args.output_dir / "qc_analysis_subject_counts.csv", index=False)

    summary_md = build_summary_markdown(coverage, loo, centroid_focus.head(6))
    (args.output_dir / "additional_qc_summary.md").write_text(summary_md, encoding="utf-8")

    manifest_out = {
        "results_root": str(args.results_root),
        "output_dir": str(args.output_dir),
        "subject_metrics_path": manifest["subject_metrics_path"],
        "written_files": {
            "selected_block_coverage": str(args.output_dir / "qc_selected_block_coverage.csv"),
            "leave_one_out": str(args.output_dir / "qc_leave_one_subject_out.csv"),
            "centroid_adjusted_focus": str(args.output_dir / "qc_centroid_adjusted_focus.csv"),
            "analysis_subject_counts": str(args.output_dir / "qc_analysis_subject_counts.csv"),
            "summary_md": str(args.output_dir / "additional_qc_summary.md"),
        },
    }
    (args.output_dir / "additional_qc_manifest.json").write_text(json.dumps(manifest_out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
