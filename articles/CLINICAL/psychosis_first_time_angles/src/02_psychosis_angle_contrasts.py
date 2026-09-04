"""Medication-stratified and pooled-FEP psychosis turning-angle contrasts."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats

import psychosis_angle_support as support


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RUN_TAG = "psychosis_angles_20260719"
METRICS = (
    "turn_cos_mean", "turn_angle_median", "turn_angle_mad", "turn_angle_iqr", "turn_angle_p90",
    "turn_fraction_gt_90", "turn_fraction_gt_120", "turn_entropy", "turn_length_coupling", "null_z_median_angle",
)
TARGETED_METRICS = ("turn_angle_p90", "turn_angle_iqr", "turn_angle_mad")


@dataclass(frozen=True)
class Config:
    run_root: Path
    coordinate_contract: str
    datasets: tuple[str, ...]


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Contrast psychosis turning-angle features by medication group.")
    parser.add_argument("--run-root", type=Path, default=ARTICLE_DIR / "results" / DEFAULT_RUN_TAG)
    parser.add_argument("--coordinate-contract", choices=["cohort_anchored", "subject_anchored"], default="cohort_anchored")
    parser.add_argument("--dataset", choices=["both", *support.DATASETS], default="both")
    args = parser.parse_args()
    return Config(args.run_root, args.coordinate_contract, support.DATASETS if args.dataset == "both" else (args.dataset,))


def bh_fdr(values: pd.Series) -> pd.Series:
    array = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    result = np.full(array.shape, np.nan)
    valid = np.isfinite(array)
    if not valid.any():
        return pd.Series(result, index=values.index)
    p = array[valid]
    order = np.argsort(p)
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(p) + 1)
    q = p * len(p) / ranks
    q_sorted = np.minimum.accumulate(q[order][::-1])[::-1]
    q_final = np.empty_like(q_sorted)
    q_final[order] = np.clip(q_sorted, 0, 1)
    result[np.flatnonzero(valid)] = q_final
    return pd.Series(result, index=values.index)


def cohens_d(right: np.ndarray, left: np.ndarray) -> float:
    if right.size < 2 or left.size < 2:
        return float("nan")
    pooled = ((right.size - 1) * np.var(right, ddof=1) + (left.size - 1) * np.var(left, ddof=1)) / (right.size + left.size - 2)
    return float((np.mean(right) - np.mean(left)) / np.sqrt(pooled)) if pooled > 0 else float("nan")


def cliffs_delta(right: np.ndarray, left: np.ndarray) -> float:
    if not right.size or not left.size:
        return float("nan")
    diff = np.subtract.outer(right, left)
    return float((np.sum(diff > 0) - np.sum(diff < 0)) / diff.size)


def contrast_table(features: pd.DataFrame, dataset: str) -> pd.DataFrame:
    features = features[features["status"] == "ok"].copy()
    sensitivity = features.copy()
    sensitivity["analysis_group"] = np.where(sensitivity["group"] == "Healthy", "Healthy", "FEP")
    inputs = [
        ("primary", features, {key: value for key, value in support.CONTRASTS.items() if key != "FEP_vs_Healthy_sensitivity"}),
        ("pooled_sensitivity", sensitivity, {"FEP_vs_Healthy_sensitivity": ("Healthy", "FEP")}),
    ]
    rows: List[Dict[str, Any]] = []
    for analysis_scope, frame, contrasts in inputs:
        for contrast, (left_group, right_group) in contrasts.items():
            for (chart, lag), cell in frame.groupby(["chart", "lag_epochs"], sort=False):
                for metric in METRICS:
                    if metric not in cell:
                        continue
                    left = pd.to_numeric(cell.loc[cell["analysis_group"] == left_group, metric] if "analysis_group" in cell else cell.loc[cell["group"] == left_group, metric], errors="coerce").dropna().to_numpy()
                    right = pd.to_numeric(cell.loc[cell["analysis_group"] == right_group, metric] if "analysis_group" in cell else cell.loc[cell["group"] == right_group, metric], errors="coerce").dropna().to_numpy()
                    row: Dict[str, Any] = {
                        "dataset": dataset, "analysis_scope": analysis_scope, "contrast": contrast,
                        "left_group": left_group, "right_group": right_group, "chart": chart, "lag_epochs": lag,
                        "metric": metric, "n_left": left.size, "n_right": right.size,
                        "left_median": float(np.median(left)) if left.size else np.nan,
                        "right_median": float(np.median(right)) if right.size else np.nan,
                        "cohens_d_right_minus_left": cohens_d(right, left),
                        "cliffs_delta_right_minus_left": cliffs_delta(right, left),
                        "small_group_warning": min(left.size, right.size) < 10,
                    }
                    if left.size >= 2 and right.size >= 2:
                        mw = stats.mannwhitneyu(right, left, alternative="two-sided")
                        welch = stats.ttest_ind(right, left, equal_var=False)
                        row.update(mannwhitney_p=float(mw.pvalue), welch_p=float(welch.pvalue), status="ok")
                    else:
                        row.update(mannwhitney_p=np.nan, welch_p=np.nan, status="limited_n")
                    rows.append(row)
    table = pd.DataFrame(rows)
    if table.empty:
        return table
    grouping = ["dataset", "analysis_scope", "contrast"]
    table["mannwhitney_q_bh_full"] = table.groupby(grouping)["mannwhitney_p"].transform(bh_fdr)
    target_mask = table["metric"].isin(TARGETED_METRICS)
    table["mannwhitney_q_bh_targeted"] = np.nan
    table.loc[target_mask, "mannwhitney_q_bh_targeted"] = (
        table.loc[target_mask].groupby(grouping)["mannwhitney_p"].transform(bh_fdr)
    )
    return table.sort_values(["analysis_scope", "contrast", "mannwhitney_p"], na_position="last")


def write_dataset(dataset: str, config: Config) -> None:
    directory = config.run_root / config.coordinate_contract / dataset
    features = pd.read_csv(directory / "subject_turning_features.csv")
    table = contrast_table(features, dataset)
    table.to_csv(directory / "turning_angle_contrasts.csv", index=False)
    primary = table[table["analysis_scope"] == "primary"]
    lines = [f"# {dataset} medication-stratified turning-angle contrasts", ""]
    for contrast, group in primary.groupby("contrast", sort=False):
        significant = group[group["mannwhitney_q_bh_full"] < 0.05]
        targeted = group[(group["metric"].isin(TARGETED_METRICS)) & (group["mannwhitney_q_bh_targeted"] < 0.05)]
        lines.append(f"## {contrast}")
        lines.append(f"- full-family BH-FDR significant: {len(significant)}/{len(group)}")
        lines.append(f"- targeted tail/spread BH-FDR significant: {len(targeted)}/{len(group[group['metric'].isin(TARGETED_METRICS)])}")
        if not group.empty:
            top = group.iloc[0]
            lines.append(f"- strongest raw-p cell: `{top['chart']}__lag{top['lag_epochs']}__{top['metric']}`, d={top['cohens_d_right_minus_left']:+.3f}, p={top['mannwhitney_p']:.3g}")
        lines.append("")
    (directory / "turning_angle_contrast_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[{dataset}] Wrote {len(table)} contrast rows to {directory}")


def main() -> None:
    config = parse_args()
    for dataset in config.datasets:
        write_dataset(dataset, config)


if __name__ == "__main__":
    sys.exit(main())
