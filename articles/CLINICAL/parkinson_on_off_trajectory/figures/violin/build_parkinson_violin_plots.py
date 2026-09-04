from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


FIGURE_DIR = Path(__file__).resolve().parent
ARTICLE_DIR = FIGURE_DIR.parents[1]
RESULTS_DIR = ARTICLE_DIR / "results" / "parkinson_on_off_dual_contract_20260602"

CONTROL_COLOR = "#2563eb"
OFF_COLOR = "#dc2626"
ON_COLOR = "#7c3aed"
NEUTRAL_COLOR = "#0f172a"


@dataclass(frozen=True)
class GroupSpec:
    label: str
    group: str
    condition: str
    color: str


@dataclass(frozen=True)
class MetricSpec:
    label: str
    source: str
    analysis_type: str
    metric: str
    contract: str
    network: str | None = None
    segment_label: str | None = None


@dataclass(frozen=True)
class PanelSpec:
    slug: str
    title: str
    left: GroupSpec
    right: GroupSpec
    paired: bool
    metrics: tuple[MetricSpec, ...]


CONTROL = GroupSpec("Control", "Control", "not_applicable", CONTROL_COLOR)
PARKINSON_OFF = GroupSpec("Parkinson OFF", "Parkinson", "OFF", OFF_COLOR)
PARKINSON_ON = GroupSpec("Parkinson ON", "Parkinson", "ON", ON_COLOR)


CONTROL_VS_OFF_NDT = PanelSpec(
    slug="control_vs_off_ndt",
    title="Control vs Parkinson OFF: focal NDT/NMD metrics",
    left=CONTROL,
    right=PARKINSON_OFF,
    paired=False,
    metrics=(
        MetricSpec("Frontal 9D d_n SD", "standard", "regional_9d", "d_n_std", "cohort_anchored", network="frontal"),
        MetricSpec("Global 9D d_n SD", "standard", "global_mnps_9d", "d_n_std", "cohort_anchored"),
        MetricSpec(
            "Eyes-closed speed (3D)",
            "event",
            "global_event_locked_trajectory_3d",
            "speed_median",
            "cohort_anchored",
            network="global",
            segment_label="eyes_closed",
        ),
        MetricSpec(
            "Eyes-closed kinetic action (9D)",
            "event",
            "global_event_locked_trajectory_9d",
            "noetic_action_kinetic",
            "cohort_anchored",
            network="global",
            segment_label="eyes_closed",
        ),
    ),
)

CONTROL_VS_ON_NDT = PanelSpec(
    slug="control_vs_on_ndt",
    title="Control vs Parkinson ON: focal NDT/NMD metrics",
    left=CONTROL,
    right=PARKINSON_ON,
    paired=False,
    metrics=(
        MetricSpec("Global 9D MDR", "standard", "global_mnps_jacobian_9d", "mdr_median", "cohort_anchored"),
        MetricSpec("Global 9D d_n SD", "standard", "global_mnps_9d", "d_n_std", "cohort_anchored"),
        MetricSpec(
            "Novel-tone hysteresis (m,e)",
            "event",
            "global_event_locked_trajectory_3d",
            "hysteresis_area_me",
            "cohort_anchored",
            network="global",
            segment_label="novel_tone",
        ),
        MetricSpec(
            "Standard-tone hysteresis (m,e)",
            "event",
            "global_event_locked_trajectory_3d",
            "hysteresis_area_me",
            "cohort_anchored",
            network="global",
            segment_label="standard_tone",
        ),
    ),
)

OFF_VS_ON_NDT = PanelSpec(
    slug="off_vs_on_ndt",
    title="Parkinson OFF vs ON: paired focal metrics",
    left=PARKINSON_OFF,
    right=PARKINSON_ON,
    paired=True,
    metrics=(
        MetricSpec(
            "Negative divergence balance",
            "standard",
            "tier2_jacobian",
            "signed_divergence_balance_mean_neg",
            "subject_anchored",
        ),
    ),
)

CONTROL_VS_OFF_CLASSICAL = PanelSpec(
    slug="control_vs_off_classical",
    title="Control vs Parkinson OFF: classical EEG comparators",
    left=CONTROL,
    right=PARKINSON_OFF,
    paired=False,
    metrics=(
        MetricSpec(
            "Relative delta (median)",
            "classical",
            "eeg_classical_comparators",
            "eeg_classical_relative_delta_median",
            "cohort_anchored",
        ),
        MetricSpec(
            "Relative alpha (median)",
            "classical",
            "eeg_classical_comparators",
            "eeg_classical_relative_alpha_median",
            "cohort_anchored",
        ),
        MetricSpec(
            "Theta/alpha ratio (median)",
            "classical",
            "eeg_classical_comparators",
            "eeg_classical_ratio_theta_alpha_median",
            "cohort_anchored",
        ),
        MetricSpec(
            "Peak alpha frequency (median)",
            "classical",
            "eeg_classical_comparators",
            "eeg_classical_peak_alpha_frequency_median",
            "cohort_anchored",
        ),
        MetricSpec(
            "Spectral entropy (median)",
            "classical",
            "eeg_classical_comparators",
            "eeg_classical_complexity_spectral_entropy_median",
            "cohort_anchored",
        ),
        MetricSpec(
            "Hjorth mobility (median)",
            "classical",
            "eeg_classical_comparators",
            "eeg_classical_complexity_hjorth_mobility_median",
            "cohort_anchored",
        ),
    ),
)

OFF_VS_ON_CLASSICAL = PanelSpec(
    slug="off_vs_on_classical",
    title="Parkinson OFF vs ON: classical EEG comparators",
    left=PARKINSON_OFF,
    right=PARKINSON_ON,
    paired=True,
    metrics=(
        MetricSpec(
            "Relative delta (median)",
            "classical",
            "eeg_classical_comparators",
            "eeg_classical_relative_delta_median",
            "subject_anchored",
        ),
        MetricSpec(
            "Relative beta (median)",
            "classical",
            "eeg_classical_comparators",
            "eeg_classical_relative_beta_median",
            "subject_anchored",
        ),
        MetricSpec(
            "Theta/alpha ratio (median)",
            "classical",
            "eeg_classical_comparators",
            "eeg_classical_ratio_theta_alpha_median",
            "subject_anchored",
        ),
        MetricSpec(
            "Peak alpha frequency (median)",
            "classical",
            "eeg_classical_comparators",
            "eeg_classical_peak_alpha_frequency_median",
            "subject_anchored",
        ),
    ),
)

DEFAULT_PANELS: tuple[PanelSpec, ...] = (
    CONTROL_VS_OFF_NDT,
    CONTROL_VS_ON_NDT,
    OFF_VS_ON_NDT,
    CONTROL_VS_OFF_CLASSICAL,
    OFF_VS_ON_CLASSICAL,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build article-facing violin plots for Parkinson ON/OFF metrics.")
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--output-dir", type=Path, default=FIGURE_DIR)
    parser.add_argument("--format", choices=("png", "svg"), default="png")
    parser.add_argument(
        "--panels",
        type=str,
        default="all",
        help="Comma-separated panel slugs or 'all'.",
    )
    return parser.parse_args()


def latest_parquet(root: Path, analysis_type: str) -> Path:
    matches = sorted(root.glob(f"ds003490_{analysis_type}_*.parquet"), key=lambda path: path.stat().st_mtime_ns)
    if not matches:
        raise FileNotFoundError(f"No {analysis_type} parquet found under {root}")
    return matches[-1]


def load_standard_metrics(results_dir: Path, contract: str) -> pd.DataFrame:
    analysis_dirname = "standard_analysis_cohort" if contract == "cohort_anchored" else "standard_analysis_subject"
    path = latest_parquet(results_dir / analysis_dirname, "subject_metrics")
    return pd.read_parquet(path)


def load_event_metrics(results_dir: Path, contract: str) -> pd.DataFrame:
    dirname = "event_metrics_cohort" if contract == "cohort_anchored" else "event_metrics_subject"
    return pd.read_csv(results_dir / dirname / "event_subject_metrics.csv", low_memory=False)


def load_classical_metrics(results_dir: Path, contract: str) -> pd.DataFrame:
    filename = (
        "eeg_classical_subject_metrics_cohort_anchor.csv"
        if contract == "cohort_anchored"
        else "eeg_classical_subject_metrics_subject_anchor.csv"
    )
    return pd.read_csv(results_dir / filename, low_memory=False)


def cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    if left.size < 2 or right.size < 2:
        return float("nan")
    pooled = ((left.size - 1) * np.var(left, ddof=1) + (right.size - 1) * np.var(right, ddof=1)) / (left.size + right.size - 2)
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(left) - np.mean(right)) / np.sqrt(pooled))


def cohens_dz(left: pd.DataFrame, right: pd.DataFrame) -> float:
    merged = left.merge(right, on="subject_id", suffixes=("_left", "_right"), how="inner")
    if merged.shape[0] < 2:
        return float("nan")
    diff = merged["value_left"].to_numpy(dtype=float) - merged["value_right"].to_numpy(dtype=float)
    diff = diff[np.isfinite(diff)]
    if diff.size < 2:
        return float("nan")
    sd = float(np.std(diff, ddof=1))
    if not np.isfinite(sd) or sd <= 0:
        return float("nan")
    return float(np.mean(diff) / sd)


def fmt_effect(value: float) -> str:
    return "n/a" if not np.isfinite(value) else f"{value:+.3f}"


def add_violin(ax: plt.Axes, values: Sequence[np.ndarray], positions: Sequence[float], colors: Sequence[str]) -> None:
    violin = ax.violinplot(values, positions=positions, widths=0.8, showmeans=False, showmedians=False, showextrema=False)
    for body, color in zip(violin["bodies"], colors):
        body.set_facecolor(color)
        body.set_alpha(0.32)
        body.set_edgecolor(color)
        body.set_linewidth(1.2)


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


def add_scatter(ax: plt.Axes, values: Sequence[np.ndarray], positions: Sequence[float], colors: Sequence[str], *, seed: int) -> None:
    rng = np.random.default_rng(seed)
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


def filter_long_metric(frame: pd.DataFrame, spec: MetricSpec, group_spec: GroupSpec) -> pd.DataFrame:
    work = frame.copy()
    if "analysis_type" in work.columns:
        work = work[work["analysis_type"] == spec.analysis_type]
    if "metric" in work.columns:
        work = work[work["metric"] == spec.metric]
    if "group" in work.columns:
        work = work[work["group"] == group_spec.group]
    if "condition" in work.columns:
        work = work[work["condition"] == group_spec.condition]
    if spec.network is not None and "network" in work.columns:
        work = work[work["network"].astype(str) == spec.network]
    if "requested_coordinate_contract" in work.columns:
        contract_values = work["requested_coordinate_contract"].dropna().astype(str).unique().tolist()
        if contract_values:
            work = work[work["requested_coordinate_contract"].astype(str) == spec.contract]
    value_column = "value"
    work[value_column] = pd.to_numeric(work[value_column], errors="coerce")
    work = work[np.isfinite(work[value_column].to_numpy(dtype=float))].copy()
    keep_cols = [column for column in ["subject_id", value_column] if column in work.columns]
    return work[keep_cols].drop_duplicates(subset=["subject_id"], keep="first") if "subject_id" in keep_cols else work[keep_cols]


def filter_event_metric(frame: pd.DataFrame, spec: MetricSpec, group_spec: GroupSpec) -> pd.DataFrame:
    work = frame.copy()
    work = work[
        (work["analysis_type"] == spec.analysis_type)
        & (work["group"] == group_spec.group)
        & (work["condition"] == group_spec.condition)
        & (work["segment_label"] == spec.segment_label)
    ].copy()
    if spec.network is not None:
        work = work[work["network"] == spec.network].copy()
    if "requested_coordinate_contract" in work.columns:
        work = work[work["requested_coordinate_contract"] == spec.contract].copy()
    work["value"] = pd.to_numeric(work[spec.metric], errors="coerce")
    work = work[np.isfinite(work["value"].to_numpy(dtype=float))].copy()
    return work[["subject_id", "value"]].drop_duplicates(subset=["subject_id"], keep="first")


def metric_frame(standard_frames: dict[str, pd.DataFrame], event_frames: dict[str, pd.DataFrame], classical_frames: dict[str, pd.DataFrame], spec: MetricSpec, group_spec: GroupSpec) -> pd.DataFrame:
    if spec.source == "standard":
        return filter_long_metric(standard_frames[spec.contract], spec, group_spec)
    if spec.source == "event":
        return filter_event_metric(event_frames[spec.contract], spec, group_spec)
    if spec.source == "classical":
        return filter_long_metric(classical_frames[spec.contract], spec, group_spec)
    raise ValueError(f"Unsupported source: {spec.source}")


def draw_metric_axis(
    ax: plt.Axes,
    *,
    spec: MetricSpec,
    panel: PanelSpec,
    left_frame: pd.DataFrame,
    right_frame: pd.DataFrame,
    seed: int,
) -> None:
    left_values = left_frame["value"].to_numpy(dtype=float) if not left_frame.empty else np.zeros((0,), dtype=float)
    right_values = right_frame["value"].to_numpy(dtype=float) if not right_frame.empty else np.zeros((0,), dtype=float)
    plot_groups = [
        (left_values, 1.0, panel.left.color),
        (right_values, 2.0, panel.right.color),
    ]
    nonempty = [(values, pos, color) for values, pos, color in plot_groups if values.size > 0]
    if nonempty:
        values, positions, colors = zip(*nonempty)
        add_violin(ax, values, positions, colors)
        add_box(ax, values, positions, colors)
        add_scatter(ax, values, positions, colors, seed=seed)

    if left_values.size:
        ax.hlines(np.median(left_values), 0.72, 1.28, color=panel.left.color, linewidth=2.2, zorder=4)
    if right_values.size:
        ax.hlines(np.median(right_values), 1.72, 2.28, color=panel.right.color, linewidth=2.2, zorder=4)

    effect = cohens_dz(left_frame, right_frame) if panel.paired else cohens_d(left_values, right_values)
    effect_label = "d_z" if panel.paired else "d"
    ax.text(
        0.02,
        0.98,
        f"{effect_label} = {fmt_effect(effect)}\n"
        f"n = {left_values.size}/{right_values.size}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        bbox={"facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.9, "boxstyle": "round,pad=0.2"},
    )
    ax.set_xticks([1.0, 2.0])
    ax.set_xticklabels([panel.left.label, panel.right.label], rotation=12)
    ax.set_title(spec.label, fontsize=10)
    ax.grid(axis="y", color="#e2e8f0", linewidth=0.8, alpha=0.75)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)


def make_panel(
    panel: PanelSpec,
    *,
    output_dir: Path,
    output_format: str,
    standard_frames: dict[str, pd.DataFrame],
    event_frames: dict[str, pd.DataFrame],
    classical_frames: dict[str, pd.DataFrame],
) -> Path:
    n_metrics = len(panel.metrics)
    n_cols = 2 if n_metrics > 1 else 1
    n_rows = int(np.ceil(n_metrics / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5.4 * n_cols, 3.9 * n_rows))
    axes_array = np.atleast_1d(axes).ravel()

    for idx, (ax, spec) in enumerate(zip(axes_array, panel.metrics, strict=False)):
        left_frame = metric_frame(standard_frames, event_frames, classical_frames, spec, panel.left)
        right_frame = metric_frame(standard_frames, event_frames, classical_frames, spec, panel.right)
        draw_metric_axis(ax, spec=spec, panel=panel, left_frame=left_frame, right_frame=right_frame, seed=20260603 + idx)

    for ax in axes_array[len(panel.metrics) :]:
        ax.axis("off")

    fig.suptitle(panel.title, fontsize=14, y=0.995)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.97))
    output_path = output_dir / f"{panel.slug}.{output_format}"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def selected_panels(raw: str) -> tuple[PanelSpec, ...]:
    if raw.strip().lower() == "all":
        return DEFAULT_PANELS
    requested = {item.strip() for item in raw.split(",") if item.strip()}
    return tuple(panel for panel in DEFAULT_PANELS if panel.slug in requested)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    standard_frames = {
        "cohort_anchored": load_standard_metrics(args.results_dir, "cohort_anchored"),
        "subject_anchored": load_standard_metrics(args.results_dir, "subject_anchored"),
    }
    event_frames = {
        "cohort_anchored": load_event_metrics(args.results_dir, "cohort_anchored"),
        "subject_anchored": load_event_metrics(args.results_dir, "subject_anchored"),
    }
    classical_frames = {
        "cohort_anchored": load_classical_metrics(args.results_dir, "cohort_anchored"),
        "subject_anchored": load_classical_metrics(args.results_dir, "subject_anchored"),
    }

    written: list[Path] = []
    for panel in selected_panels(args.panels):
        written.append(
            make_panel(
                panel,
                output_dir=args.output_dir,
                output_format=args.format,
                standard_frames=standard_frames,
                event_frames=event_frames,
                classical_frames=classical_frames,
            )
        )
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
