from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats


REPO_ROOT = Path(__file__).resolve().parents[4]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "psychosis_cohort_anchor_20260520"
RESULTS_ROOT = ARTICLE_DIR / "results"

DATASETS = ("ds003944", "ds003947")
GROUP_LABELS = {"Control": "Healthy", "FEP": "FEP"}
SUMMARY_EXCLUDE_PATTERNS = (
    "_split_half_n",
    "_split_half_rho",
)


def _latest_parquet(dataset: str, stem: str) -> Path:
    matches = sorted(ANALYSIS_ROOT.glob(f"{dataset}_{stem}_*.parquet"))
    if not matches:
        raise FileNotFoundError(f"No {stem} parquet found for {dataset} under {ANALYSIS_ROOT}")
    return matches[-1]


def _cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    if left.size < 2 or right.size < 2:
        return float("nan")
    left_var = left.var(ddof=1)
    right_var = right.var(ddof=1)
    pooled_var = ((left.size - 1) * left_var + (right.size - 1) * right_var) / (left.size + right.size - 2)
    if not np.isfinite(pooled_var) or pooled_var <= 0:
        return float("nan")
    return float((right.mean() - left.mean()) / np.sqrt(pooled_var))


def _bh_fdr(values: pd.Series) -> pd.Series:
    arr = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    valid = np.isfinite(arr)
    if not valid.any():
        return pd.Series(out, index=values.index, dtype=float)
    p = arr[valid]
    order = np.argsort(p)
    ranked = p[order]
    n = ranked.size
    adjusted = ranked * n / np.arange(1, n + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    out_valid = np.empty_like(adjusted)
    out_valid[order] = adjusted
    out[valid] = out_valid
    return pd.Series(out, index=values.index, dtype=float)


def _sig_tier(row: pd.Series) -> str:
    q = row.get("q_value")
    p = row.get("p_value")
    if pd.notna(q) and float(q) <= 0.05:
        return "q<=0.05"
    if pd.notna(p) and float(p) < 0.05:
        return "p<0.05"
    if pd.notna(p) and float(p) < 0.1:
        return "p<0.1"
    return "ns"


def _sorted_results(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["abs_effect"] = pd.to_numeric(out["effect_size"], errors="coerce").abs()
    out["sig_rank"] = out.apply(_sig_tier, axis=1).map({"q<=0.05": 0, "p<0.05": 1, "p<0.1": 2, "ns": 3}).fillna(9)
    return out.sort_values(
        by=["sig_rank", "q_value", "p_value", "abs_effect", "metric"],
        ascending=[True, True, True, False, True],
        na_position="last",
    ).reset_index(drop=True)


def _prepare_subject_metrics(dataset: str) -> pd.DataFrame:
    subject_metrics = pd.read_parquet(_latest_parquet(dataset, "subject_metrics"))
    reachability = subject_metrics[subject_metrics["analysis_type"] == "reachability_cones"].copy()
    if reachability.empty:
        return reachability

    keep_groups = set(GROUP_LABELS)
    reachability = reachability[reachability["group"].isin(keep_groups)].copy()
    reachability["group_label"] = reachability["group"].map(GROUP_LABELS)
    reachability["value"] = pd.to_numeric(reachability["value"], errors="coerce")
    reachability = reachability[reachability["value"].notna()].copy()
    dedupe_cols = [
        "subject_id",
        "metric",
        "group",
        "group_label",
        "analysis_type",
        "metric_family",
    ]
    return (
        reachability.groupby(dedupe_cols, dropna=False, as_index=False)
        .agg(value=("value", "mean"))
        .reset_index(drop=True)
    )


def build_pooled_reachability() -> tuple[pd.DataFrame, pd.DataFrame]:
    detail_rows: list[dict[str, object]] = []

    for dataset in DATASETS:
        prepared = _prepare_subject_metrics(dataset)
        if prepared.empty:
            continue
        for metric, group_frame in prepared.groupby("metric", dropna=False):
            left = pd.to_numeric(
                group_frame.loc[group_frame["group_label"] == "Healthy", "value"],
                errors="coerce",
            ).dropna()
            right = pd.to_numeric(
                group_frame.loc[group_frame["group_label"] == "FEP", "value"],
                errors="coerce",
            ).dropna()
            if len(left) < 3 or len(right) < 3:
                continue
            t_stat, p_value = stats.ttest_ind(left.to_numpy(), right.to_numpy(), equal_var=False, nan_policy="omit")
            detail_rows.append(
                {
                    "dataset": dataset,
                    "analysis_type": "reachability_cones",
                    "contrast_name": "Healthy_vs_FEP",
                    "contrast_label": "Healthy vs FEP",
                    "metric_family": "reachability",
                    "metric": metric,
                    "left_group": "Healthy",
                    "right_group": "FEP",
                    "left_n": int(len(left)),
                    "right_n": int(len(right)),
                    "left_mean": float(left.mean()),
                    "right_mean": float(right.mean()),
                    "effect_estimate": float(right.mean() - left.mean()),
                    "effect_size": _cohens_d(left.to_numpy(), right.to_numpy()),
                    "t_stat": float(t_stat) if np.isfinite(t_stat) else np.nan,
                    "p_value": float(p_value) if np.isfinite(p_value) else np.nan,
                }
            )

    detail = pd.DataFrame(detail_rows)
    if detail.empty:
        return detail, pd.DataFrame()

    detail["q_value"] = detail.groupby("dataset", dropna=False)["p_value"].transform(_bh_fdr)
    detail["sig_tier"] = detail.apply(_sig_tier, axis=1)
    detail = _sorted_results(detail).drop(columns=["abs_effect", "sig_rank"], errors="ignore")

    summary_rows: list[dict[str, object]] = []
    for dataset in DATASETS:
        dataset_frame = detail[detail["dataset"] == dataset].copy()
        if dataset_frame.empty:
            continue
        summary_frame = dataset_frame[
            ~dataset_frame["metric"].astype(str).str.endswith(SUMMARY_EXCLUDE_PATTERNS)
        ].copy()
        if summary_frame.empty:
            summary_frame = dataset_frame
        summary_rows.extend(summary_frame.head(8).to_dict("records"))

    return detail, pd.DataFrame(summary_rows)


def build_markdown(summary: pd.DataFrame) -> str:
    lines = [
        "# Pooled psychosis reachability summary",
        "",
        f"- Analysis root: `{ANALYSIS_ROOT}`",
        f"- Contrast: `Healthy vs FEP`",
        "",
    ]
    if summary.empty:
        lines.extend(["No pooled reachability results were estimable.", ""])
        return "\n".join(lines)

    for dataset in DATASETS:
        dataset_frame = summary[summary["dataset"] == dataset].copy()
        if dataset_frame.empty:
            continue
        lines.extend([f"## {dataset}", ""])
        for _, row in dataset_frame.iterrows():
            lines.append(
                f"- `{row['metric']}`: d={float(row['effect_size']):.4f}, "
                f"p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)

    detail, summary = build_pooled_reachability()
    detail_path = RESULTS_ROOT / "pooled_fep_reachability_detail.csv"
    summary_path = RESULTS_ROOT / "pooled_fep_reachability_summary.csv"
    markdown_path = RESULTS_ROOT / "pooled_fep_reachability_summary.md"
    manifest_path = RESULTS_ROOT / "pooled_fep_reachability_manifest.json"

    if not detail.empty:
        detail.to_csv(detail_path, index=False)
    if not summary.empty:
        summary.to_csv(summary_path, index=False)
    markdown_path.write_text(build_markdown(summary), encoding="utf-8")
    manifest = {
        "analysis_root": str(ANALYSIS_ROOT),
        "results_root": str(RESULTS_ROOT),
        "datasets": list(DATASETS),
        "detail_csv": str(detail_path),
        "summary_csv": str(summary_path),
        "markdown_path": str(markdown_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote pooled reachability detail to {detail_path}")
    print(f"Wrote pooled reachability summary to {summary_path}")


if __name__ == "__main__":
    main()
