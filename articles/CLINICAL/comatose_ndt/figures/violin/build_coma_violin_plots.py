from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


FIGURE_DIR = Path(__file__).resolve().parent
ARTICLE_DIR = FIGURE_DIR.parents[1]
DEFAULT_TIMELINE_DIR = ARTICLE_DIR / "results" / "timeline_analysis_20260524_combined_cpc15_primary12h_9d"
DEFAULT_MNPS_DIR = ARTICLE_DIR / "results" / "mnps_summary_20260524_combined_cpc15_primary12h"
DEFAULT_TIME_BIN = "0_12h"
DEFAULT_GOOD_CPC = 1
DEFAULT_POOR_CPC = 5

GOOD_LABEL = "CPC 1"
POOR_LABEL = "CPC 5"
GOOD_COLOR = "#2563eb"
POOR_COLOR = "#dc2626"
NEUTRAL_COLOR = "#0f172a"

PRIMARY_METRICS: list[tuple[str, str]] = [
    ("tube_d_eff_median", "Tube effective dimensionality"),
    ("tube_a_operator_norm_median", "A-operator norm"),
    ("tube_capture_gate_median", "Capture gate"),
    ("persistence_kappa_median", "Persistence kappa"),
    ("persistence_log_eig_var_median", "Persistence log eig var"),
    ("coords_9d_global_std_mean", "9D global std mean"),
]

POOLED_FIVE_METRICS: list[tuple[str, str]] = [
    ("persistence_log_eig_var_median", "Persistence log eig var"),
    ("persistence_kappa_median", "Persistence kappa"),
    ("tube_d_eff_median", "Tube effective dimensionality"),
    ("tube_a_operator_norm_median", "A-operator norm"),
    ("tube_capture_gate_median", "Capture gate"),
]

PERSISTENCE_METRICS: list[tuple[str, str]] = [
    ("persistence_log_eig_var_median", "Persistence log eig var"),
    ("persistence_kappa_median", "Persistence kappa"),
]

CLASSICAL_METRICS: list[tuple[str, str]] = [
    ("jacobian_fro_median", "MNJ Frobenius norm"),
    ("jacobian_spectral_radius_median", "MNJ spectral radius"),
    ("mnps_path_length", "MNPS path length"),
    ("coords_9d_global_std_mean", "9D global std mean"),
]

JACOBIAN_CORE_METRICS: list[tuple[str, str]] = [
    ("jacobian_fro_median", "MNJ Frobenius norm"),
    ("jacobian_spectral_radius_median", "MNJ spectral radius"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build CPC1-vs-CPC5 violin plots for the coma article timeline exports."
    )
    parser.add_argument("--timeline-dir", type=Path, default=DEFAULT_TIMELINE_DIR)
    parser.add_argument("--mnps-dir", type=Path, default=DEFAULT_MNPS_DIR)
    parser.add_argument("--output-dir", type=Path, default=FIGURE_DIR)
    parser.add_argument("--time-bin", type=str, default=DEFAULT_TIME_BIN)
    parser.add_argument("--good-cpc", type=int, default=DEFAULT_GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=DEFAULT_POOR_CPC)
    return parser.parse_args()


def load_timeline_frame(timeline_dir: Path, *, time_bin: str, good_cpc: int, poor_cpc: int) -> pd.DataFrame:
    frame = pd.read_csv(timeline_dir / "patient_timebin_summaries.csv")
    frame = frame[frame["time_bin"] == time_bin].copy()
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([float(good_cpc), float(poor_cpc)])].copy()
    frame["group_label"] = np.where(frame["cpc_numeric"] == float(good_cpc), GOOD_LABEL, POOR_LABEL)
    return frame.reset_index(drop=True)


def load_primary_panel_frame(
    timeline_dir: Path,
    mnps_dir: Path,
    *,
    time_bin: str,
    good_cpc: int,
    poor_cpc: int,
) -> pd.DataFrame:
    timeline = load_timeline_frame(timeline_dir, time_bin=time_bin, good_cpc=good_cpc, poor_cpc=poor_cpc)
    keep_columns = ["subject", "time_bin", "cpc_numeric", "group_label", "coords_9d_global_std_mean"]
    timeline = timeline[[column for column in keep_columns if column in timeline.columns]].copy()

    mnps = pd.read_csv(mnps_dir / "patient_timebin_adapter_summaries.csv", low_memory=False)
    mnps = mnps[
        (mnps["analysis_type"] == "reachability_cones")
        & (mnps["time_bin"] == time_bin)
    ].copy()
    metric_columns = [metric for metric, _ in PRIMARY_METRICS if metric != "coords_9d_global_std_mean" and metric in mnps.columns]
    mnps = mnps[["subject", "time_bin", *metric_columns]].copy()

    frame = timeline.merge(mnps, on=["subject", "time_bin"], how="left")
    return frame.reset_index(drop=True)


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    if good.size < 2 or poor.size < 2:
        return float("nan")
    pooled = ((good.size - 1) * np.var(good, ddof=1) + (poor.size - 1) * np.var(poor, ddof=1)) / (good.size + poor.size - 2)
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(good) - np.mean(poor)) / np.sqrt(pooled))


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
    rng = np.random.default_rng(20260524)
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
    plot_groups = [
        (good, 1.0, GOOD_COLOR),
        (poor, 2.0, POOR_COLOR),
    ]
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


def winsorize_frame(frame: pd.DataFrame, metrics: Iterable[tuple[str, str]], *, lower_q: float = 0.01, upper_q: float = 0.99) -> pd.DataFrame:
    out = frame.copy()
    for metric, _ in metrics:
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


def make_log_safe_frame(frame: pd.DataFrame, metrics: Iterable[tuple[str, str]]) -> pd.DataFrame:
    out = frame.copy()
    for metric, _ in metrics:
        if metric not in out.columns:
            continue
        values = pd.to_numeric(out[metric], errors="coerce")
        positive = values[(pd.notna(values)) & (values > 0)]
        if positive.empty:
            continue
        floor = float(positive.min()) * 0.5
        adjusted = values.where(values > 0, floor)
        out[metric] = np.log10(adjusted)
    return out


def make_metric_grid(
    frame: pd.DataFrame,
    metrics: Iterable[tuple[str, str]],
    *,
    output_path: Path,
    figure_title: str,
    footnote: str | None = None,
    n_cols: int = 2,
    yscale_map: dict[str, str] | None = None,
) -> None:
    metric_list = [(metric, label) for metric, label in metrics if metric in frame.columns]
    if not metric_list:
        raise ValueError(f"No requested metrics were available for {output_path.name}.")

    n_metrics = len(metric_list)
    n_rows = int(np.ceil(n_metrics / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5.4 * n_cols, 3.8 * n_rows))
    axes_array = np.atleast_1d(axes).ravel()

    for ax, (metric, label) in zip(axes_array, metric_list):
        good, poor = prepare_metric_values(frame, metric)
        style_metric_axis(ax, label=label, good=good, poor=poor)
        ax.set_ylabel("")
        ax.grid(axis="y", color="#e2e8f0", linewidth=0.8, alpha=0.75)
        ax.set_axisbelow(True)
        if yscale_map and metric in yscale_map:
            ax.set_yscale(yscale_map[metric])

    for ax in axes_array[len(metric_list) :]:
        ax.axis("off")

    fig.suptitle(figure_title, fontsize=14, y=0.995)
    if footnote:
        fig.text(0.5, 0.012, footnote, ha="center", va="bottom", fontsize=9, color="#475569")
        fig.tight_layout(rect=(0.0, 0.03, 1.0, 0.97))
    else:
        fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.97))
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    timeline_frame = load_timeline_frame(
        args.timeline_dir,
        time_bin=args.time_bin,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
    )
    primary_frame = load_primary_panel_frame(
        args.timeline_dir,
        args.mnps_dir,
        time_bin=args.time_bin,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
    )

    make_metric_grid(
        primary_frame,
        POOLED_FIVE_METRICS,
        output_path=args.output_dir / "violin_pooled_primary_five_metrics.png",
        figure_title="Coma pooled 0-12 h: five article-facing reachability metrics",
        footnote="Raw pooled values. Violin + box + jitter summary; extreme tails retained.",
        n_cols=3,
    )
    make_metric_grid(
        winsorize_frame(primary_frame, POOLED_FIVE_METRICS),
        POOLED_FIVE_METRICS,
        output_path=args.output_dir / "violin_pooled_primary_five_metrics_winsorized.png",
        figure_title="Coma pooled 0-12 h: five reachability metrics (winsorized 1st-99th pct)",
        footnote="Per metric, values are clipped to the pooled 1st-99th percentile range for visualization clarity only.",
        n_cols=3,
    )
    make_metric_grid(
        make_log_safe_frame(primary_frame, PERSISTENCE_METRICS),
        PERSISTENCE_METRICS,
        output_path=args.output_dir / "violin_persistence_metrics_logscale.png",
        figure_title="Coma pooled 0-12 h: persistence metrics (log10 display view)",
        footnote="Display-only log10 transform for the two persistence metrics; inferential statistics in the manuscript use the original untransformed values.",
        n_cols=2,
    )
    make_metric_grid(
        primary_frame,
        PRIMARY_METRICS,
        output_path=args.output_dir / "violin_primary_reachability_and_9d.png",
        figure_title="Coma pooled 0-12 h: primary reachability metrics and 9D support",
        footnote="Raw pooled values with outliers retained.",
    )
    make_metric_grid(
        timeline_frame,
        CLASSICAL_METRICS,
        output_path=args.output_dir / "violin_classical_comparators.png",
        figure_title="Coma pooled 0-12 h: classical comparator violins",
        footnote="Raw pooled values with outliers retained.",
    )
    make_metric_grid(
        timeline_frame,
        JACOBIAN_CORE_METRICS,
        output_path=args.output_dir / "violin_jacobian_core_metrics.png",
        figure_title="Coma pooled 0-12 h: core MNJ comparator violins",
        footnote="Raw pooled Jacobian summaries. These are classical comparator metrics, not the article's primary reachability endpoint family.",
        n_cols=2,
    )

    print(f"Wrote violin plots to {args.output_dir}")


if __name__ == "__main__":
    main()
