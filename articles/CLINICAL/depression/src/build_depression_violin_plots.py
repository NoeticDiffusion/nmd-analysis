from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
RESULTS_ROOT = ARTICLE_DIR / "results"
FIGURES_DIR = ARTICLE_DIR / "figures"
PARTICIPANTS_PATH = ARTICLE_DIR / "metadata" / "participants.tsv"
BDI_BAND_ORDER = ["BDI 0-13", "BDI 14-19", "BDI 20-63"]
BDI_COLORS = ["#4C78A8", "#F58518", "#E45756"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build supplementary violin plots for the resting-state depression article."
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


def violin_on_axis(ax: plt.Axes, frame: pd.DataFrame, *, value_col: str, title: str, subtitle: str, ylabel: str) -> None:
    values = [
        pd.to_numeric(frame.loc[frame["bdi_band"] == band, value_col], errors="coerce").dropna().to_numpy(dtype=float)
        for band in BDI_BAND_ORDER
    ]
    cleaned = [arr if arr.size else np.asarray([np.nan]) for arr in values]
    parts = ax.violinplot(cleaned, positions=np.arange(1, len(BDI_BAND_ORDER) + 1), widths=0.8, showmedians=True)
    for body, color in zip(parts["bodies"], BDI_COLORS, strict=False):
        body.set_facecolor(color)
        body.set_edgecolor("black")
        body.set_alpha(0.72)
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
        ax.scatter(np.full(arr.size, idx, dtype=float) + jitter, arr, s=10, color="black", alpha=0.33, linewidths=0.0)

    labels = []
    for band in BDI_BAND_ORDER:
        n_value = int(frame.loc[frame["bdi_band"] == band, "subject_id"].nunique())
        labels.append(f"{band}\n(n={n_value})")
    ax.set_xticks(np.arange(1, len(BDI_BAND_ORDER) + 1))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_title(title, fontsize=10, pad=10)
    ax.text(0.5, 1.01, subtitle, ha="center", va="bottom", transform=ax.transAxes, fontsize=8)
    ax.set_ylabel(ylabel, fontsize=8)
    ax.grid(True, axis="y", alpha=0.2)


def build_selected_block_violins(
    figures_dir: Path,
    participants: pd.DataFrame,
    subject_metrics: pd.DataFrame,
    selected_summary: pd.DataFrame,
) -> None:
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), constrained_layout=True)
    axes = axes.flatten()
    for ax, (_, row) in zip(axes, selected_summary.iterrows(), strict=False):
        series = load_subject_metric_series(
            subject_metrics,
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
        violin_on_axis(
            ax,
            merged,
            value_col="value",
            title=str(row["block_title"]),
            subtitle=subtitle,
            ylabel="value",
        )
    fig.suptitle("Supplementary violins for selected resting-state blocks", fontsize=14)
    fig.savefig(figures_dir / "supp_violin_selected_blocks.png", dpi=220)
    plt.close(fig)


def build_centroid_baseline_violins(
    figures_dir: Path,
    participants: pd.DataFrame,
    subject_metrics: pd.DataFrame,
    centroid_baseline: pd.DataFrame,
) -> None:
    top = centroid_baseline.sort_values(["q_value", "p_value", "abs_effect"], ascending=[True, True, False], na_position="last").head(8)
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), constrained_layout=True)
    axes = axes.flatten()
    for ax, (_, row) in zip(axes, top.iterrows(), strict=False):
        series = load_subject_metric_series(
            subject_metrics,
            analysis_type=str(row["analysis_type"]),
            metric=str(row["metric"]),
        )
        merged = series.merge(
            participants[["participant_id", "bdi_band"]],
            left_on="subject_id",
            right_on="participant_id",
            how="left",
        ).drop(columns=["participant_id"], errors="ignore")
        subtitle = f"{row['analysis_type']} | q={float(row['q_value']):.3g}" if pd.notna(row.get("q_value")) else str(row["analysis_type"])
        violin_on_axis(
            ax,
            merged,
            value_col="value",
            title=str(row["metric"]),
            subtitle=subtitle,
            ylabel="value",
        )
    fig.suptitle("Supplementary violins for baseline centroid metrics", fontsize=14)
    fig.savefig(figures_dir / "supp_violin_centroid_baseline.png", dpi=220)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    ensure_dir(args.figures_dir)

    manifest = json.loads((args.results_root / "paper_exports_manifest.json").read_text(encoding="utf-8"))
    participants = load_participants()
    subject_metrics = pd.read_parquet(manifest["subject_metrics_path"])
    selected_summary = pd.read_csv(args.results_root / "selected_metrics_summary.csv", low_memory=False)
    centroid_baseline = pd.read_csv(args.results_root / "centroid_baseline_summary.csv", low_memory=False)

    build_selected_block_violins(args.figures_dir, participants, subject_metrics, selected_summary)
    build_centroid_baseline_violins(args.figures_dir, participants, subject_metrics, centroid_baseline)


if __name__ == "__main__":
    main()
