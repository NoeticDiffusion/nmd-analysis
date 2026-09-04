from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
RESULTS_ROOT = ARTICLE_DIR / "results"
FIGURES_DIR = ARTICLE_DIR / "figures"
MANIFEST_PATH = RESULTS_ROOT / "paper_exports_manifest.json"
PARTICIPANTS_PATH = ARTICLE_DIR / "metadata" / "participants.tsv"
BDI_BAND_ORDER = ["BDI 0-13", "BDI 14-19", "BDI 20-63"]
BDI_COLORS = ["#4C78A8", "#F58518", "#E45756"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build supplementary violin plots for the paired depression PST article."
    )
    parser.add_argument("--results-root", type=Path, default=RESULTS_ROOT)
    parser.add_argument("--figures-dir", type=Path, default=FIGURES_DIR)
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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


def violin_on_axis(ax: plt.Axes, frame: pd.DataFrame, *, value_col: str, title: str, subtitle: str) -> None:
    values = [
        pd.to_numeric(frame.loc[frame["bdi_band"] == band, value_col], errors="coerce").dropna().to_numpy(dtype=float)
        for band in BDI_BAND_ORDER
    ]
    cleaned = [arr if arr.size else np.asarray([np.nan]) for arr in values]
    parts = ax.violinplot(cleaned, positions=np.arange(1, len(BDI_BAND_ORDER) + 1), widths=0.8, showmedians=True)
    for body, color in zip(parts["bodies"], BDI_COLORS, strict=False):
        body.set_facecolor(color)
        body.set_edgecolor("black")
        body.set_alpha(0.7)
    for key in ("cbars", "cmins", "cmaxes", "cmedians"):
        if key in parts:
            parts[key].set_color("black")
            parts[key].set_linewidth(0.8)

    rng = np.random.default_rng(20260609)
    for idx, band in enumerate(BDI_BAND_ORDER, start=1):
        arr = pd.to_numeric(frame.loc[frame["bdi_band"] == band, value_col], errors="coerce").dropna().to_numpy(dtype=float)
        if arr.size == 0:
            continue
        jitter = rng.uniform(-0.10, 0.10, size=arr.size)
        ax.scatter(np.full(arr.size, idx, dtype=float) + jitter, arr, s=10, color="black", alpha=0.35, linewidths=0.0)

    band_labels = []
    for band in BDI_BAND_ORDER:
        n_value = int(frame.loc[frame["bdi_band"] == band, "subject_id"].nunique())
        band_labels.append(f"{band}\n(n={n_value})")
    ax.set_xticks(np.arange(1, len(BDI_BAND_ORDER) + 1))
    ax.set_xticklabels(band_labels, fontsize=8)
    ax.set_title(title, fontsize=10, pad=10)
    ax.text(0.5, 1.01, subtitle, ha="center", va="bottom", transform=ax.transAxes, fontsize=8)
    ax.grid(True, axis="y", alpha=0.2)


def build_task_violin_plot(
    figures_dir: Path,
    participants: pd.DataFrame,
    task_subject_metrics: pd.DataFrame,
    selected_summary: pd.DataFrame,
) -> None:
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), constrained_layout=True)
    axes = axes.flatten()
    for ax, (_, row) in zip(axes, selected_summary.iterrows(), strict=False):
        series = load_subject_metric_series(
            task_subject_metrics,
            analysis_type=str(row["analysis_type"]),
            metric=str(row["metric"]),
            source_group=None if pd.isna(row.get("source_group")) else str(row.get("source_group")),
            target_group=None if pd.isna(row.get("target_group")) else str(row.get("target_group")),
        )
        merged = series.merge(
            participants[["participant_id", "bdi_band"]],
            left_on="subject_id",
            right_on="participant_id",
            how="left",
        ).drop(columns=["participant_id"], errors="ignore")
        subtitle = f"{row['metric']} | q={float(row['q_value']):.3g}" if pd.notna(row.get("q_value")) else str(row["metric"])
        violin_on_axis(ax, merged, value_col="value", title=str(row["block_title"]), subtitle=subtitle)
        ax.set_ylabel("value", fontsize=8)
    for ax in axes[len(selected_summary) :]:
        ax.axis("off")
    fig.suptitle("Supplementary task-state violins by BDI band", fontsize=14)
    fig.savefig(figures_dir / "supp_violin_task_blocks.png", dpi=220)
    plt.close(fig)


def build_paired_violin_plot(
    figures_dir: Path,
    paired_detail: pd.DataFrame,
    paired_summary: pd.DataFrame,
) -> None:
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), constrained_layout=True)
    axes = axes.flatten()
    for ax, (_, row) in zip(axes, paired_summary.iterrows(), strict=False):
        group = paired_detail[
            (paired_detail["block_key"] == row["block_key"])
            & (paired_detail["analysis_type"] == row["analysis_type"])
            & (paired_detail["metric"] == row["metric"])
        ].copy()
        group = group.rename(columns={"delta_value": "value"})
        subtitle = f"{row['metric']} | q={float(row['q_value']):.3g}" if pd.notna(row.get("q_value")) else str(row["metric"])
        violin_on_axis(ax, group, value_col="value", title=f"{row['block_title']} delta", subtitle=subtitle)
        ax.set_ylabel("task - rest", fontsize=8)
    for ax in axes[len(paired_summary) :]:
        ax.axis("off")
    fig.suptitle("Supplementary paired delta violins by BDI band", fontsize=14)
    fig.savefig(figures_dir / "supp_violin_paired_delta.png", dpi=220)
    plt.close(fig)


def build_event_violin_plot(
    figures_dir: Path,
    event_subjects: pd.DataFrame,
    event_summary: pd.DataFrame,
    participants: pd.DataFrame,
) -> None:
    families = ["feedback_correct", "feedback_incorrect", "train_stim_any", "test_stim_any", "left_response", "right_response"]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    axes = axes.flatten()
    for ax, family in zip(axes, families, strict=False):
        group = event_subjects[event_subjects["event_family"] == family].copy()
        group = group[group["bin_label"] == "event"].copy()
        group = group.merge(
            participants[["participant_id", "bdi_band"]],
            left_on="subject_id",
            right_on="participant_id",
            how="left",
        ).drop(columns=["participant_id"], errors="ignore")
        row = event_summary[
            (event_summary["event_family"] == family)
            & (event_summary["bin_label"] == "event")
        ]
        subtitle = "speed_mean"
        if not row.empty:
            q_value = pd.to_numeric(row.iloc[0]["q_value"], errors="coerce")
            subtitle = f"speed_mean | q={float(q_value):.3g}" if pd.notna(q_value) else "speed_mean"
        violin_on_axis(ax, group, value_col="speed_mean", title=family, subtitle=subtitle)
        ax.set_ylabel("speed_mean", fontsize=8)
    fig.suptitle("Supplementary event-window violins (event bin)", fontsize=14)
    fig.savefig(figures_dir / "supp_violin_event_speed.png", dpi=220)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    ensure_dir(args.figures_dir)

    manifest = json.loads((args.results_root / "paper_exports_manifest.json").read_text(encoding="utf-8"))
    participants = load_participants()
    task_subject_metrics = pd.read_parquet(manifest["task_subject_metrics_path"])

    selected_summary = pd.read_csv(args.results_root / "selected_metrics_summary.csv", low_memory=False)
    paired_summary = pd.read_csv(args.results_root / "paired_delta_summary.csv", low_memory=False)
    paired_detail = pd.read_csv(args.results_root / "paired_delta_detail.csv", low_memory=False)
    event_subjects = pd.read_csv(args.results_root / "event_locked_subject_summary.csv", low_memory=False)
    event_summary = pd.read_csv(args.results_root / "event_locked_summary.csv", low_memory=False)

    build_task_violin_plot(args.figures_dir, participants, task_subject_metrics, selected_summary)
    build_paired_violin_plot(args.figures_dir, paired_detail, paired_summary)
    build_event_violin_plot(args.figures_dir, event_subjects, event_summary, participants)


if __name__ == "__main__":
    main()
