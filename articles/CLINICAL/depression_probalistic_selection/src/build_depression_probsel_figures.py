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
EVENT_FAMILIES = [
    "feedback_correct",
    "feedback_incorrect",
    "train_stim_any",
    "test_stim_any",
    "left_response",
    "right_response",
]
EVENT_LABELS = {
    "feedback_correct": "Feedback correct",
    "feedback_incorrect": "Feedback incorrect",
    "train_stim_any": "Train stimulus",
    "test_stim_any": "Test stimulus",
    "left_response": "Left response",
    "right_response": "Right response",
}
EVENT_BINS = ["pre_near", "event", "post_near"]
EVENT_BIN_LABELS = {"pre_near": "Pre-near", "event": "Event", "post_near": "Post-near"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build task/rest depression figures from article results.")
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


def _draw_heatmap(matrix: np.ndarray, xlabels: list[str], ylabels: list[str], annotations: list[list[str]], title: str, cbar_label: str, output_path: Path, *, cmap: str = "coolwarm", symmetric: bool = True, vmin: float | None = None, vmax: float | None = None) -> None:
    if symmetric:
        vmax = np.nanmax(np.abs(matrix)) if vmax is None else vmax
        if not np.isfinite(vmax):
            vmax = 1.0
        vmin = -vmax if vmin is None else vmin
    else:
        if vmin is None:
            vmin = np.nanmin(matrix) if np.isfinite(matrix).any() else -1.0
        if vmax is None:
            vmax = np.nanmax(matrix) if np.isfinite(matrix).any() else 1.0
    fig, ax = plt.subplots(figsize=(13.0, 4.8))
    im = ax.imshow(matrix, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(len(xlabels)))
    ax.set_xticklabels(xlabels, rotation=20, ha="right")
    ax.set_yticks(np.arange(len(ylabels)))
    ax.set_yticklabels(ylabels)
    ax.set_title(title)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if np.isfinite(matrix[i, j]) and annotations[i][j]:
                ax.text(j, i, annotations[i][j], ha="center", va="center", fontsize=8, color="black")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(cbar_label)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def draw_selected_effect_heatmap(summary: pd.DataFrame, output_path: Path) -> None:
    if summary.empty:
        return
    values: List[List[float]] = [[]]
    annotations: List[List[str]] = [[]]
    for block in BLOCK_ORDER:
        match = summary[summary["block_key"] == block]
        if match.empty:
            values[0].append(np.nan)
            annotations[0].append("")
            continue
        row = match.iloc[0]
        values[0].append(float(row["effect_size"]))
        label = str(row["metric"])
        star = _sig_star(row)
        if star:
            label = f"{label}\n{star}"
        annotations[0].append(label)
    _draw_heatmap(
        np.asarray(values, dtype=float),
        [BLOCK_LABELS[key] for key in BLOCK_ORDER],
        ["BDI 0-13 vs 20-63"],
        annotations,
        "Selected task-state low-vs-high BDI effects",
        "Effect size (Cohen's d)",
        output_path,
    )


def draw_bdi_correlation_panel(summary: pd.DataFrame, output_path: Path) -> None:
    if summary.empty:
        return
    row_labels: List[str] = []
    values: List[List[float]] = []
    annotations: List[List[str]] = []
    for cohort_key in CORRELATION_ORDER:
        cohort = summary[summary["cohort_key"] == cohort_key].copy()
        if cohort.empty:
            continue
        row_labels.append(CORRELATION_LABELS.get(cohort_key, cohort_key))
        row_vals: List[float] = []
        row_ann: List[str] = []
        for block in BLOCK_ORDER:
            match = cohort[cohort["block_key"] == block]
            if match.empty:
                row_vals.append(np.nan)
                row_ann.append("")
                continue
            row = match.iloc[0]
            row_vals.append(float(row["spearman_rho"]))
            label = str(row["metric"])
            star = _sig_star(row)
            if star:
                label = f"{label}\n{star}"
            row_ann.append(label)
        values.append(row_vals)
        annotations.append(row_ann)
    _draw_heatmap(
        np.asarray(values, dtype=float),
        [BLOCK_LABELS[key] for key in BLOCK_ORDER],
        row_labels,
        annotations,
        "Selected task-state BDI correlations",
        "Spearman rho",
        output_path,
        cmap="PiYG",
        vmin=-1.0,
        vmax=1.0,
    )


def draw_bdi_bin_heatmap(summary: pd.DataFrame, output_path: Path) -> None:
    if summary.empty:
        return
    row_labels: List[str] = []
    values: List[List[float]] = []
    annotations: List[List[str]] = []
    for split_name in BDI_BIN_ORDER:
        split = summary[summary["split_name"] == split_name].copy()
        if split.empty:
            continue
        row_labels.append(BDI_BIN_LABELS.get(split_name, split_name))
        row_vals: List[float] = []
        row_ann: List[str] = []
        for block in BLOCK_ORDER:
            match = split[split["block_key"] == block]
            if match.empty:
                row_vals.append(np.nan)
                row_ann.append("")
                continue
            row = match.iloc[0]
            row_vals.append(float(row["effect_size"]))
            label = str(row["metric"])
            star = _sig_star(row)
            if star:
                label = f"{label}\n{star}"
            row_ann.append(label)
        values.append(row_vals)
        annotations.append(row_ann)
    _draw_heatmap(
        np.asarray(values, dtype=float),
        [BLOCK_LABELS[key] for key in BLOCK_ORDER],
        row_labels,
        annotations,
        "Task-state clinical BDI-bin effects",
        "Effect size (Cohen's d)",
        output_path,
    )


def draw_event_locked_heatmap(summary: pd.DataFrame, output_path: Path) -> None:
    if summary.empty:
        return
    row_labels: List[str] = []
    values: List[List[float]] = []
    annotations: List[List[str]] = []
    for family in EVENT_FAMILIES:
        fam = summary[summary["event_family"] == family].copy()
        if fam.empty:
            continue
        row_labels.append(EVENT_LABELS.get(family, family))
        row_vals: List[float] = []
        row_ann: List[str] = []
        for bin_label in EVENT_BINS:
            match = fam[fam["bin_label"] == bin_label]
            if match.empty:
                row_vals.append(np.nan)
                row_ann.append("")
                continue
            row = match.iloc[0]
            row_vals.append(float(row["effect_size"]))
            label = str(row["metric"])
            star = _sig_star(row)
            if star:
                label = f"{label}\n{star}"
            row_ann.append(label)
        values.append(row_vals)
        annotations.append(row_ann)
    _draw_heatmap(
        np.asarray(values, dtype=float),
        [EVENT_BIN_LABELS[key] for key in EVENT_BINS],
        row_labels,
        annotations,
        "Event-locked low-vs-high BDI effects",
        "Effect size (Cohen's d)",
        output_path,
    )


def draw_paired_delta_panel(summary: pd.DataFrame, corr_summary: pd.DataFrame, output_path: Path) -> None:
    if summary.empty and corr_summary.empty:
        return
    row_labels = ["Low-vs-high delta", "Delta vs BDI"]
    values: List[List[float]] = [[], []]
    annotations: List[List[str]] = [[], []]
    for block in BLOCK_ORDER:
        match = summary[summary["block_key"] == block]
        if match.empty:
            values[0].append(np.nan)
            annotations[0].append("")
        else:
            row = match.iloc[0]
            values[0].append(float(row["effect_size"]))
            label = str(row["metric"])
            star = _sig_star(row)
            if star:
                label = f"{label}\n{star}"
            annotations[0].append(label)
        match_corr = corr_summary[corr_summary["block_key"] == block]
        if match_corr.empty:
            values[1].append(np.nan)
            annotations[1].append("")
        else:
            row = match_corr.iloc[0]
            values[1].append(float(row["spearman_rho"]))
            label = str(row["metric"])
            star = _sig_star(row)
            if star:
                label = f"{label}\n{star}"
            annotations[1].append(label)
    _draw_heatmap(
        np.asarray(values, dtype=float),
        [BLOCK_LABELS[key] for key in BLOCK_ORDER],
        row_labels,
        annotations,
        "Task-minus-rest paired effects",
        "Effect size / rho",
        output_path,
    )


def main() -> None:
    args = parse_args()
    args.figures_root.mkdir(parents=True, exist_ok=True)

    selected_metrics_path = args.results_root / "selected_metrics_summary.csv"
    bdi_summary_path = args.results_root / "bdi_correlations_summary.csv"
    bdi_bin_summary_path = args.results_root / "clinical_bdi_bin_summary.csv"
    event_summary_path = args.results_root / "event_locked_summary.csv"
    paired_summary_path = args.results_root / "paired_delta_summary.csv"
    paired_corr_path = args.results_root / "paired_delta_correlation_summary.csv"

    if selected_metrics_path.exists():
        draw_selected_effect_heatmap(pd.read_csv(selected_metrics_path), args.figures_root / "probsel_selected_effect_heatmap.png")
    if bdi_summary_path.exists():
        draw_bdi_correlation_panel(pd.read_csv(bdi_summary_path), args.figures_root / "probsel_bdi_correlation_panel.png")
    if bdi_bin_summary_path.exists():
        draw_bdi_bin_heatmap(pd.read_csv(bdi_bin_summary_path), args.figures_root / "probsel_bdi_bin_heatmap.png")
    if event_summary_path.exists():
        draw_event_locked_heatmap(pd.read_csv(event_summary_path), args.figures_root / "probsel_event_locked_heatmap.png")
    if paired_summary_path.exists() and paired_corr_path.exists():
        draw_paired_delta_panel(
            pd.read_csv(paired_summary_path),
            pd.read_csv(paired_corr_path),
            args.figures_root / "probsel_paired_delta_panel.png",
        )

    print(f"Wrote figure outputs to {args.figures_root}")


if __name__ == "__main__":
    main()
