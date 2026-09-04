from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_ROOT = ARTICLE_DIR / "results"
DEFAULT_FIGURES_ROOT = ARTICLE_DIR / "figures"

BLOCK_ORDER = ["emmi", "mnj_3d", "mnj_9d", "block_mnj"]
BLOCK_LABELS = {
    "emmi": "EMMI",
    "mnj_3d": "3D MNJ",
    "mnj_9d": "9D MNJ",
    "block_mnj": "Block-MNJ",
}
CONTRAST_ORDER = ["AD_vs_Healthy", "FTD_vs_Healthy", "AD_vs_FTD"]
CONTRAST_LABELS = {
    "AD_vs_Healthy": "AD vs Healthy",
    "FTD_vs_Healthy": "FTD vs Healthy",
    "AD_vs_FTD": "AD vs FTD",
}
COHORT_ORDER = ["Dementia_all", "AD_only", "FTD_only"]
COHORT_LABELS = {
    "Dementia_all": "All dementia",
    "AD_only": "AD only",
    "FTD_only": "FTD only",
}
MMSE_BIN_ORDER = [
    "mmse_median",
    "mmse_tertiles_low_vs_mid",
    "mmse_tertiles_low_vs_high",
    "mmse_tertiles_mid_vs_high",
]
MMSE_BIN_LABELS = {
    "mmse_median": "Lower vs Higher MMSE",
    "mmse_tertiles_low_vs_mid": "Lower vs Middle tertile",
    "mmse_tertiles_low_vs_high": "Lower vs Upper tertile",
    "mmse_tertiles_mid_vs_high": "Middle vs Upper tertile",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Alzheimer/FTD paper-facing figures from article results.")
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--figures-root", type=Path, default=DEFAULT_FIGURES_ROOT)
    return parser.parse_args()


def _sig_star(row: pd.Series) -> str:
    q = pd.to_numeric(pd.Series([row.get("q_value")]), errors="coerce").iloc[0]
    p = pd.to_numeric(pd.Series([row.get("p_value")]), errors="coerce").iloc[0]
    if pd.notna(q) and float(q) <= 0.05:
        return "q"
    if pd.notna(p) and float(p) < 0.05:
        return "*"
    if pd.notna(p) and float(p) < 0.1:
        return "~"
    return ""


def draw_selected_effect_heatmap(summary: pd.DataFrame, output_path: Path) -> None:
    if summary.empty:
        return

    row_labels: List[str] = []
    values: List[List[float]] = []
    annotations: List[List[str]] = []

    for contrast_name in CONTRAST_ORDER:
        contrast_frame = summary[summary["contrast_name"] == contrast_name].copy()
        if contrast_frame.empty:
            continue
        row_labels.append(CONTRAST_LABELS.get(contrast_name, contrast_name))
        row_vals: List[float] = []
        row_ann: List[str] = []
        for block in BLOCK_ORDER:
            match = contrast_frame[contrast_frame["block_key"] == block]
            if match.empty:
                row_vals.append(np.nan)
                row_ann.append("")
                continue
            row = match.iloc[0]
            row_vals.append(float(row["effect_size"]))
            label = str(row["metric"])
            if pd.notna(row.get("source_group")) or pd.notna(row.get("target_group")):
                label = f"{label}\n{row.get('source_group')}->{row.get('target_group')}"
            star = _sig_star(row)
            if star:
                label = f"{label}\n{star}"
            row_ann.append(label)
        values.append(row_vals)
        annotations.append(row_ann)

    if not values:
        return

    matrix = np.asarray(values, dtype=float)
    vmax = np.nanmax(np.abs(matrix)) if np.isfinite(matrix).any() else 1.0
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    im = ax.imshow(matrix, cmap="coolwarm", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(len(BLOCK_ORDER)))
    ax.set_xticklabels([BLOCK_LABELS[key] for key in BLOCK_ORDER], rotation=20, ha="right")
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels)
    ax.set_title("Selected AD/FTD contrast effects by block")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if np.isfinite(matrix[i, j]):
                ax.text(j, i, annotations[i][j], ha="center", va="center", fontsize=8, color="black")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Effect size (Cohen's d)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def draw_mmse_correlation_panel(summary: pd.DataFrame, output_path: Path) -> None:
    if summary.empty:
        return

    row_labels: List[str] = []
    values: List[List[float]] = []
    annotations: List[List[str]] = []

    for cohort_key in COHORT_ORDER:
        cohort_frame = summary[summary["cohort_key"] == cohort_key].copy()
        if cohort_frame.empty:
            continue
        row_labels.append(COHORT_LABELS.get(cohort_key, cohort_key))
        row_vals: List[float] = []
        row_ann: List[str] = []
        for block in BLOCK_ORDER:
            match = cohort_frame[cohort_frame["block_key"] == block]
            if match.empty:
                row_vals.append(np.nan)
                row_ann.append("")
                continue
            row = match.iloc[0]
            row_vals.append(float(row["spearman_rho"]))
            label = str(row["metric"])
            if pd.notna(row.get("source_group")) or pd.notna(row.get("target_group")):
                label = f"{label}\n{row.get('source_group')}->{row.get('target_group')}"
            star = _sig_star(row)
            if star:
                label = f"{label}\n{star}"
            row_ann.append(label)
        values.append(row_vals)
        annotations.append(row_ann)

    if not values:
        return

    matrix = np.asarray(values, dtype=float)
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    im = ax.imshow(matrix, cmap="PiYG", vmin=-1.0, vmax=1.0, aspect="auto")
    ax.set_xticks(np.arange(len(BLOCK_ORDER)))
    ax.set_xticklabels([BLOCK_LABELS[key] for key in BLOCK_ORDER], rotation=20, ha="right")
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels)
    ax.set_title("Selected MMSE correlations by block")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if np.isfinite(matrix[i, j]):
                ax.text(j, i, annotations[i][j], ha="center", va="center", fontsize=8, color="black")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Spearman rho with MMSE")
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def draw_mmse_bin_heatmap(summary: pd.DataFrame, output_path: Path) -> None:
    if summary.empty:
        return

    row_labels: List[str] = []
    values: List[List[float]] = []
    annotations: List[List[str]] = []

    has_cohort_key = "cohort_key" in summary.columns
    cohort_order = COHORT_ORDER if has_cohort_key else [None]
    for cohort_key in cohort_order:
        cohort_frame = summary[summary["cohort_key"] == cohort_key].copy() if cohort_key is not None else summary.copy()
        if cohort_frame.empty:
            continue
        for split_name in MMSE_BIN_ORDER:
            split_frame = cohort_frame[cohort_frame["split_name"] == split_name].copy()
            if split_frame.empty:
                continue
            row_label = MMSE_BIN_LABELS.get(split_name, split_name)
            if cohort_key is not None:
                row_label = f"{COHORT_LABELS.get(str(cohort_key), str(cohort_key))}\n{row_label}"
            row_labels.append(row_label)
            row_vals: List[float] = []
            row_ann: List[str] = []
            for block in BLOCK_ORDER:
                match = split_frame[split_frame["block_key"] == block]
                if match.empty:
                    row_vals.append(np.nan)
                    row_ann.append("")
                    continue
                row = match.iloc[0]
                row_vals.append(float(row["effect_size"]))
                label = str(row["metric"])
                if pd.notna(row.get("source_group")) or pd.notna(row.get("target_group")):
                    label = f"{label}\n{row.get('source_group')}->{row.get('target_group')}"
                star = _sig_star(row)
                if star:
                    label = f"{label}\n{star}"
                row_ann.append(label)
            values.append(row_vals)
            annotations.append(row_ann)

    if not values:
        return

    matrix = np.asarray(values, dtype=float)
    vmax = np.nanmax(np.abs(matrix)) if np.isfinite(matrix).any() else 1.0
    height = max(5.5, 0.5 * len(row_labels) + 1.5)
    fig, ax = plt.subplots(figsize=(10.8, height))
    im = ax.imshow(matrix, cmap="coolwarm", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(len(BLOCK_ORDER)))
    ax.set_xticklabels([BLOCK_LABELS[key] for key in BLOCK_ORDER], rotation=20, ha="right")
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels)
    ax.set_title("MMSE-bin effects by cohort and block")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if np.isfinite(matrix[i, j]):
                ax.text(j, i, annotations[i][j], ha="center", va="center", fontsize=8, color="black")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Effect size (Cohen's d)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    args.figures_root.mkdir(parents=True, exist_ok=True)

    selected_metrics_path = args.results_root / "selected_metrics_summary.csv"
    mmse_summary_path = args.results_root / "mmse_correlations_summary.csv"
    mmse_bin_summary_path = args.results_root / "cohort_mmse_bin_summary.csv"

    if selected_metrics_path.exists():
        selected_metrics = pd.read_csv(selected_metrics_path)
        draw_selected_effect_heatmap(selected_metrics, args.figures_root / "ad_ftd_selected_effect_heatmap.png")
    if mmse_summary_path.exists():
        mmse_summary = pd.read_csv(mmse_summary_path)
        draw_mmse_correlation_panel(mmse_summary, args.figures_root / "ad_ftd_mmse_correlation_panel.png")
    if mmse_bin_summary_path.exists():
        mmse_bin_summary = pd.read_csv(mmse_bin_summary_path)
        draw_mmse_bin_heatmap(mmse_bin_summary, args.figures_root / "ad_ftd_mmse_bin_heatmap.png")

    print(f"Wrote figure outputs to {args.figures_root}")


if __name__ == "__main__":
    main()
