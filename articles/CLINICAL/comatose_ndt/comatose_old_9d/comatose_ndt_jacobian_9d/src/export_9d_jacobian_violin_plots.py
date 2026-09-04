from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from jacobian_9d_support import (
    FIGURE_DIR,
    MAIN_ARTICLE_METRICS,
    PART1_9D_MNPS_DIR,
    PART2_9D_MNPS_DIR,
    VIOLIN_DIR,
    cohens_d,
    load_metric_long,
)


GOOD_LABEL = "CPC 1"
POOR_LABEL = "CPC 5"
GOOD_COLOR = "#2563eb"
POOR_COLOR = "#dc2626"
NEUTRAL_COLOR = "#0f172a"

DISPLAY_NAMES = {
    "spectral_radius_median": "Spectral radius",
    "anisotropy_abs_eig_median": "Anisotropy abs eig",
    "frobenius_norm_median": "Frobenius norm",
    "mdr_median": "MDR",
    "rotational_power_mean": "Rotational power mean",
    "rotational_power_median": "Rotational power median",
}


def load_pooled_frame() -> pd.DataFrame:
    rows = []
    for cohort_tag, input_dir in (("part1", PART1_9D_MNPS_DIR), ("part2", PART2_9D_MNPS_DIR)):
        frame = load_metric_long(input_dir, analysis_type="global_mnps_jacobian_9d", metrics=MAIN_ARTICLE_METRICS).copy()
        frame["cohort_tag"] = cohort_tag
        rows.append(frame)
    pooled = pd.concat(rows, ignore_index=True)
    pooled["group_label"] = np.where(pooled["cpc_numeric"] == 1.0, GOOD_LABEL, POOR_LABEL)
    wide = pooled.pivot_table(
        index=["subject", "cpc_numeric", "group_label", "cohort_tag"],
        columns="metric",
        values="value",
        aggfunc="first",
    ).reset_index()
    wide.columns.name = None
    return wide


def prepare_metric_values(frame: pd.DataFrame, metric: str) -> tuple[np.ndarray, np.ndarray]:
    values = pd.to_numeric(frame[metric], errors="coerce")
    good = values[frame["group_label"] == GOOD_LABEL].dropna().to_numpy(dtype=float)
    poor = values[frame["group_label"] == POOR_LABEL].dropna().to_numpy(dtype=float)
    return good, poor


def add_violin(ax: plt.Axes, values: Sequence[np.ndarray], positions: Sequence[float], colors: Sequence[str]) -> None:
    violin = ax.violinplot(
        dataset=values,
        positions=positions,
        widths=0.8,
        showmeans=False,
        showmedians=False,
        showextrema=False,
    )
    for body, color in zip(violin["bodies"], colors):
        body.set_facecolor(color)
        body.set_alpha(0.35)
        body.set_edgecolor(color)
        body.set_linewidth(1.2)


def add_scatter(ax: plt.Axes, values: Sequence[np.ndarray], positions: Sequence[float], colors: Sequence[str]) -> None:
    rng = np.random.default_rng(20260525)
    for group_values, x_pos, color in zip(values, positions, colors):
        if group_values.size == 0:
            continue
        jitter = rng.normal(loc=0.0, scale=0.05, size=group_values.size)
        ax.scatter(
            np.full(group_values.shape, x_pos, dtype=float) + jitter,
            group_values,
            s=16,
            alpha=0.45,
            color=color,
            edgecolors="none",
            zorder=3,
        )


def add_box(ax: plt.Axes, values: Sequence[np.ndarray], positions: Sequence[float], colors: Sequence[str]) -> None:
    box = ax.boxplot(
        values,
        positions=positions,
        widths=0.26,
        patch_artist=True,
        showfliers=False,
        medianprops={"linewidth": 2.0, "color": NEUTRAL_COLOR},
        whiskerprops={"linewidth": 1.1, "color": "#64748b"},
        capprops={"linewidth": 1.1, "color": "#64748b"},
        boxprops={"linewidth": 1.0, "color": "#64748b"},
    )
    for patch, color in zip(box["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.18)
        patch.set_edgecolor(color)


def style_metric_axis(ax: plt.Axes, *, label: str, good: np.ndarray, poor: np.ndarray) -> None:
    plot_groups = [(good, 1.0, GOOD_COLOR), (poor, 2.0, POOR_COLOR)]
    nonempty_groups = [(values, pos, color) for values, pos, color in plot_groups if values.size > 0]
    if nonempty_groups:
        values, positions, colors = zip(*nonempty_groups)
        add_violin(ax, values, positions, colors)
        add_box(ax, values, positions, colors)
        add_scatter(ax, values, positions, colors)
    if good.size:
        ax.hlines(np.median(good), 0.72, 1.28, color=GOOD_COLOR, linewidth=2.2, zorder=4)
    if poor.size:
        ax.hlines(np.median(poor), 1.72, 2.28, color=POOR_COLOR, linewidth=2.2, zorder=4)
    ax.set_xticks([1.0, 2.0])
    ax.set_xticklabels([GOOD_LABEL, POOR_LABEL])
    ax.set_title(label, fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    d_value = cohens_d(good, poor)
    d_label = "n/a" if not np.isfinite(d_value) else f"{d_value:+.3f}"
    ax.text(
        0.02,
        0.98,
        f"d = {d_label}\n"
        f"n = {good.size}/{poor.size}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        bbox={"facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.9, "boxstyle": "round,pad=0.2"},
    )


def winsorize_frame(frame: pd.DataFrame, metrics: Iterable[str], *, lower_q: float = 0.01, upper_q: float = 0.99) -> pd.DataFrame:
    out = frame.copy()
    for metric in metrics:
        if metric not in out.columns:
            continue
        values = pd.to_numeric(out[metric], errors="coerce")
        valid = values.dropna()
        if valid.empty:
            continue
        lo = float(valid.quantile(lower_q))
        hi = float(valid.quantile(upper_q))
        out[metric] = values.clip(lower=lo, upper=hi)
    return out


def make_metric_grid(
    frame: pd.DataFrame,
    metrics: Sequence[str],
    *,
    output_path: Path,
    figure_title: str,
    footnote: str,
) -> None:
    n_metrics = len(metrics)
    n_cols = 3
    n_rows = int(np.ceil(n_metrics / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5.4 * n_cols, 3.8 * n_rows))
    axes_array = np.atleast_1d(axes).ravel()
    for ax, metric in zip(axes_array, metrics):
        good, poor = prepare_metric_values(frame, metric)
        style_metric_axis(ax, label=DISPLAY_NAMES.get(metric, metric), good=good, poor=poor)
        ax.set_ylabel("")
        ax.grid(axis="y", color="#e2e8f0", linewidth=0.8, alpha=0.75)
        ax.set_axisbelow(True)
    for ax in axes_array[len(metrics) :]:
        ax.axis("off")
    fig.suptitle(figure_title, fontsize=14, y=0.995)
    fig.text(0.5, 0.012, footnote, ha="center", va="bottom", fontsize=9, color="#475569")
    fig.tight_layout(rect=(0.0, 0.03, 1.0, 0.97))
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    VIOLIN_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    pooled = load_pooled_frame()
    make_metric_grid(
        pooled,
        list(MAIN_ARTICLE_METRICS),
        output_path=VIOLIN_DIR / "violin_revised_9d_core_metrics.png",
        figure_title="Refreshed 9D Jacobian article: pooled 0-12 h main metrics",
        footnote="Raw pooled values from the formal part1+part2 9D manuscript cohort.",
    )
    make_metric_grid(
        pooled,
        list(MAIN_ARTICLE_METRICS),
        output_path=FIGURE_DIR / "fig3a_9d_revised_metric_violins.png",
        figure_title="Refreshed 9D Jacobian article: pooled 0-12 h main metrics",
        footnote="Raw pooled 0-12 h values from the formal part1+part2 9D manuscript cohort.",
    )
    make_metric_grid(
        winsorize_frame(pooled, MAIN_ARTICLE_METRICS),
        list(MAIN_ARTICLE_METRICS),
        output_path=VIOLIN_DIR / "violin_revised_9d_core_metrics_winsorized.png",
        figure_title="Refreshed 9D Jacobian article: main metrics (winsorized 1st-99th pct)",
        footnote="Per metric, values are clipped to the pooled 1st-99th percentile range for display clarity only.",
    )
    make_metric_grid(
        winsorize_frame(pooled, MAIN_ARTICLE_METRICS),
        list(MAIN_ARTICLE_METRICS),
        output_path=FIGURE_DIR / "fig3b_9d_revised_metric_violins_winsorized.png",
        figure_title="Refreshed 9D Jacobian article: main metrics (winsorized 1st-99th pct)",
        footnote="Per metric, values are clipped to the pooled 1st-99th percentile range for display clarity only.",
    )
    print(f"Wrote revised 9D violin plots to {VIOLIN_DIR} and {FIGURE_DIR}")


if __name__ == "__main__":
    main()
