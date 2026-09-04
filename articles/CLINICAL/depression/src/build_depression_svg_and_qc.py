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

BLOCK_ORDER = ["mnps_3d", "mnps_9d", "mnj_3d", "mnj_9d", "block_mnj", "reachability", "emmi", "distribution"]
BLOCK_LABELS = {
    "mnps_3d": "3D MNPS",
    "mnps_9d": "9D MNPS",
    "mnj_3d": "3D MNJ",
    "mnj_9d": "9D MNJ",
    "block_mnj": "Block-MNJ",
    "reachability": "Reachability",
    "emmi": "EMMI",
    "distribution": "Dist",
}
CORRELATION_ORDER = ["All_valid", "LowHigh_only", "High_BDI_only"]
CORRELATION_LABELS = {
    "All_valid": "All valid BDI",
    "LowHigh_only": "BDI 0-13 + 20-63",
    "High_BDI_only": "BDI 20-63 only",
}
BDI_BIN_ORDER = ["bdi_0_13_vs_14_19", "bdi_0_13_vs_20_63", "bdi_14_19_vs_20_63"]
BDI_BIN_LABELS = {
    "bdi_0_13_vs_14_19": "BDI 0-13 vs 14-19",
    "bdi_0_13_vs_20_63": "BDI 0-13 vs 20-63",
    "bdi_14_19_vs_20_63": "BDI 14-19 vs 20-63",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build depression paper-facing figures from article results.")
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

    row_labels: List[str] = ["BDI 0-13 vs 20-63"]
    values: List[List[float]] = []
    annotations: List[List[str]] = []

    row_vals: List[float] = []
    row_ann: List[str] = []
    for block in BLOCK_ORDER:
        match = summary[summary["block_key"] == block]
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

    matrix = np.asarray(values, dtype=float)
    vmax = np.nanmax(np.abs(matrix)) if np.isfinite(matrix).any() else 1.0
    fig, ax = plt.subplots(figsize=(13.0, 3.8))
    im = ax.imshow(matrix, cmap="coolwarm", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(len(BLOCK_ORDER)))
    ax.set_xticklabels([BLOCK_LABELS[key] for key in BLOCK_ORDER], rotation=20, ha="right")
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels)
    ax.set_title("Selected low-vs-high BDI effects by block")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if np.isfinite(matrix[i, j]):
                ax.text(j, i, annotations[i][j], ha="center", va="center", fontsize=8, color="black")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Effect size (Cohen's d)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def draw_bdi_correlation_panel(summary: pd.DataFrame, output_path: Path) -> None:
    if summary.empty:
        return

    row_labels: List[str] = []
    values: List[List[float]] = []
    annotations: List[List[str]] = []

    for cohort_key in CORRELATION_ORDER:
        cohort_frame = summary[summary["cohort_key"] == cohort_key].copy()
        if cohort_frame.empty:
            continue
        row_labels.append(CORRELATION_LABELS.get(cohort_key, cohort_key))
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
    fig, ax = plt.subplots(figsize=(13.0, 5.0))
    im = ax.imshow(matrix, cmap="PiYG", vmin=-1.0, vmax=1.0, aspect="auto")
    ax.set_xticks(np.arange(len(BLOCK_ORDER)))
    ax.set_xticklabels([BLOCK_LABELS[key] for key in BLOCK_ORDER], rotation=20, ha="right")
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels)
    ax.set_title("Selected BDI correlations by cohort")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if np.isfinite(matrix[i, j]):
                ax.text(j, i, annotations[i][j], ha="center", va="center", fontsize=8, color="black")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Spearman rho with BDI")
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def draw_bdi_bin_heatmap(summary: pd.DataFrame, output_path: Path) -> None:
    if summary.empty:
        return

    row_labels: List[str] = []
    values: List[List[float]] = []
    annotations: List[List[str]] = []

    for split_name in BDI_BIN_ORDER:
        split_frame = summary[summary["split_name"] == split_name].copy()
        if split_frame.empty:
            continue
        row_labels.append(BDI_BIN_LABELS.get(split_name, split_name))
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
    fig, ax = plt.subplots(figsize=(13.0, 4.8))
    im = ax.imshow(matrix, cmap="coolwarm", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(len(BLOCK_ORDER)))
    ax.set_xticklabels([BLOCK_LABELS[key] for key in BLOCK_ORDER], rotation=20, ha="right")
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels)
    ax.set_title("Clinical BDI-bin effects by block")
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
    bdi_summary_path = args.results_root / "bdi_correlations_summary.csv"
    bdi_bin_summary_path = args.results_root / "clinical_bdi_bin_summary.csv"

    if selected_metrics_path.exists():
        selected_metrics = pd.read_csv(selected_metrics_path)
        draw_selected_effect_heatmap(selected_metrics, args.figures_root / "depression_selected_effect_heatmap.png")
    if bdi_summary_path.exists():
        bdi_summary = pd.read_csv(bdi_summary_path)
        draw_bdi_correlation_panel(bdi_summary, args.figures_root / "depression_bdi_correlation_panel.png")
    if bdi_bin_summary_path.exists():
        bdi_bin_summary = pd.read_csv(bdi_bin_summary_path)
        draw_bdi_bin_heatmap(bdi_bin_summary, args.figures_root / "depression_bdi_bin_heatmap.png")

    print(f"Wrote figure outputs to {args.figures_root}")


if __name__ == "__main__":
    main()
