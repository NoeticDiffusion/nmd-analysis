from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


FIGURE_DIR = Path(__file__).resolve().parent
ARTICLE_DIR = FIGURE_DIR.parents[1]
SRC_DIR = ARTICLE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from parkinson_cognitive_workload_focal_specs import (  # noqa: E402
    GroupSpec,
    MetricSpec,
    PanelSpec,
    contrast_view,
    violin_panels_for_dataset,
)
from parkinson_cognitive_workload_support import (  # noqa: E402
    cohens_d,
    cohens_dz,
    get_dataset_spec,
    results_dir_for_spec,
)


NEUTRAL_COLOR = "#0f172a"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build article-facing violin plots for Parkinson cognitive workload metrics."
    )
    parser.add_argument("--dataset-id", type=str, required=True)
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=FIGURE_DIR)
    parser.add_argument("--format", choices=("png", "svg"), default="png")
    parser.add_argument(
        "--panels",
        type=str,
        default="all",
        help="Comma-separated panel slugs or 'all'.",
    )
    return parser.parse_args()


def latest_parquet(root: Path, dataset_id: str, analysis_type: str) -> Path:
    matches = sorted(root.glob(f"{dataset_id}_{analysis_type}_*.parquet"), key=lambda path: path.stat().st_mtime_ns)
    if not matches:
        raise FileNotFoundError(f"No {analysis_type} parquet found under {root}")
    return matches[-1]


def load_standard_metrics(results_dir: Path, dataset_id: str, contract: str) -> pd.DataFrame:
    analysis_dirname = "standard_analysis_cohort" if contract == "cohort_anchored" else "standard_analysis_subject"
    frame = pd.read_parquet(latest_parquet(results_dir / analysis_dirname, dataset_id, "subject_metrics"))
    if "requested_coordinate_contract" not in frame.columns:
        frame["requested_coordinate_contract"] = contract
    if "resolved_coordinate_contract" not in frame.columns:
        frame["resolved_coordinate_contract"] = contract
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame


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
        work = work[work["network"].fillna("").astype(str) == spec.network]
    if "requested_coordinate_contract" in work.columns:
        work = work[work["requested_coordinate_contract"].fillna("").astype(str) == spec.contract]
    work["value"] = pd.to_numeric(work["value"], errors="coerce")
    work = work[np.isfinite(work["value"])].copy()
    keep_cols = [column for column in ["subject_id", "value"] if column in work.columns]
    if "subject_id" in keep_cols:
        return work[keep_cols].drop_duplicates(subset=["subject_id"], keep="first")
    return work[keep_cols]


def metric_frame(standard_frames: dict[str, pd.DataFrame], spec: MetricSpec, group_spec: GroupSpec) -> pd.DataFrame:
    return filter_long_metric(standard_frames[spec.contract], spec, group_spec)


def fmt_effect(value: float) -> str:
    return "n/a" if not np.isfinite(value) else f"{value:+.3f}"


def paired_effect(left_frame: pd.DataFrame, right_frame: pd.DataFrame) -> tuple[float, int]:
    merged = left_frame.merge(right_frame, on="subject_id", suffixes=("_left", "_right"), how="inner")
    if merged.shape[0] < 2:
        return float("nan"), int(merged.shape[0])
    diff = (
        pd.to_numeric(merged["value_right"], errors="coerce") - pd.to_numeric(merged["value_left"], errors="coerce")
    ).to_numpy(dtype=float)
    return cohens_dz(diff), int(merged.shape[0])


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


def draw_metric_axis(
    ax: plt.Axes,
    *,
    spec: MetricSpec,
    standard_frames: dict[str, pd.DataFrame],
    seed: int,
) -> None:
    view = contrast_view(spec.contrast_name)
    left_frame = metric_frame(standard_frames, spec, view.left)
    right_frame = metric_frame(standard_frames, spec, view.right)
    left_values = left_frame["value"].to_numpy(dtype=float) if not left_frame.empty else np.zeros((0,), dtype=float)
    right_values = right_frame["value"].to_numpy(dtype=float) if not right_frame.empty else np.zeros((0,), dtype=float)

    plot_groups = [
        (left_values, 1.0, view.left.color),
        (right_values, 2.0, view.right.color),
    ]
    nonempty = [(values, pos, color) for values, pos, color in plot_groups if values.size > 0]
    if nonempty:
        values, positions, colors = zip(*nonempty)
        add_violin(ax, values, positions, colors)
        add_box(ax, values, positions, colors)
        add_scatter(ax, values, positions, colors, seed=seed)

    if left_values.size:
        ax.hlines(np.median(left_values), 0.72, 1.28, color=view.left.color, linewidth=2.2, zorder=4)
    if right_values.size:
        ax.hlines(np.median(right_values), 1.72, 2.28, color=view.right.color, linewidth=2.2, zorder=4)

    if view.paired:
        effect, n_pairs = paired_effect(left_frame, right_frame)
        effect_label = "d_z"
        n_line = f"n = {left_values.size}/{right_values.size}\npairs = {n_pairs}"
    else:
        effect = cohens_d(left_values, right_values)
        effect_label = "d"
        n_line = f"n = {left_values.size}/{right_values.size}"
    ax.text(
        0.02,
        0.98,
        f"{effect_label} = {fmt_effect(effect)}\n{n_line}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        bbox={"facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.9, "boxstyle": "round,pad=0.2"},
    )
    ax.set_xticks([1.0, 2.0])
    ax.set_xticklabels([view.left.label, view.right.label], rotation=12)
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
) -> Path:
    n_metrics = len(panel.metrics)
    n_cols = 2 if n_metrics > 1 else 1
    n_rows = int(np.ceil(n_metrics / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5.6 * n_cols, 4.0 * n_rows))
    axes_array = np.atleast_1d(axes).ravel()

    for idx, (ax, spec) in enumerate(zip(axes_array, panel.metrics, strict=False)):
        draw_metric_axis(ax, spec=spec, standard_frames=standard_frames, seed=20260605 + idx)

    for ax in axes_array[len(panel.metrics) :]:
        ax.axis("off")

    fig.suptitle(panel.title, fontsize=14, y=0.995)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.97))
    output_path = output_dir / f"{panel.slug}.{output_format}"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def selected_panels(dataset_id: str, raw: str) -> tuple[PanelSpec, ...]:
    panels = violin_panels_for_dataset(dataset_id)
    if raw.strip().lower() == "all":
        return panels
    requested = {item.strip() for item in raw.split(",") if item.strip()}
    return tuple(panel for panel in panels if panel.slug in requested)


def main() -> None:
    args = parse_args()
    spec = get_dataset_spec(args.dataset_id)
    results_dir = args.results_dir or results_dir_for_spec(spec)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    standard_frames = {
        "cohort_anchored": load_standard_metrics(results_dir, spec.dataset_id, "cohort_anchored"),
        "subject_anchored": load_standard_metrics(results_dir, spec.dataset_id, "subject_anchored"),
    }

    written: list[Path] = []
    for panel in selected_panels(spec.dataset_id, args.panels):
        written.append(
            make_panel(
                panel,
                output_dir=args.output_dir,
                output_format=args.format,
                standard_frames=standard_frames,
            )
        )

    manifest = {
        "dataset_id": spec.dataset_id,
        "results_dir": str(results_dir),
        "output_dir": str(args.output_dir),
        "format": args.format,
        "panels": [panel.slug for panel in selected_panels(spec.dataset_id, args.panels)],
        "written_files": [str(path) for path in written],
    }
    (args.output_dir / f"violin_manifest_{spec.dataset_id}.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
