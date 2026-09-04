"""Render compact concordance and paired-difference figures from article tables."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from eeg_meg_support import FIGURES_DIR, RESULTS_DIR, TOPOLOGIES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", default=RESULTS_DIR)
    parser.add_argument("--figures-dir", default=FIGURES_DIR)
    return parser.parse_args()


def _heatmap(ax: plt.Axes, frame: pd.DataFrame, value: str, title: str, cmap: str, vmin: float, vmax: float) -> None:
    ordered = frame.pivot(index="feature_family", columns="topology", values=value).reindex(columns=TOPOLOGIES)
    image = ax.imshow(ordered.to_numpy(), aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_title(title)
    ax.set_xticks(range(len(ordered.columns)), [name.replace("_", "\n") for name in ordered.columns], fontsize=8)
    ax.set_yticks(range(len(ordered.index)), ordered.index, fontsize=8)
    plt.colorbar(image, ax=ax, fraction=0.04, pad=0.03)


def main() -> None:
    args = parse_args()
    results_dir = Path(args.results_dir)
    figures_dir = Path(args.figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)

    concordance = pd.read_csv(results_dir / "03_concordance" / "subject_level_feature_concordance.csv")
    differences = pd.read_csv(results_dir / "03_concordance" / "paired_feature_difference_tests.csv")

    regional_concordance = (
        concordance[concordance["level"] == "regional"]
        .groupby(["topology", "feature_family"], as_index=False)["pearson_r"]
        .mean()
    )
    regional_differences = differences[differences["level"] == "regional"]
    figure, axes = plt.subplots(1, 2, figsize=(15, 7), constrained_layout=True)
    _heatmap(
        axes[0], regional_concordance, "pearson_r",
        "EEG--MEG temporal concordance (mean subject Pearson r)",
        "viridis", -1.0, 1.0,
    )
    _heatmap(
        axes[1], regional_differences, "cohens_dz",
        "Paired mean differences (EEG minus MEG; Cohen dz)",
        "coolwarm", -1.5, 1.5,
    )
    figure.savefig(figures_dir / "fig1_regional_eeg_meg_concordance.png", dpi=300, bbox_inches="tight")
    plt.close(figure)

    global_differences = differences[differences["level"] == "global"].sort_values("feature_family")
    figure, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
    colors = ["#1f77b4" if q < 0.05 else "#9da7b1" for q in global_differences["permutation_q"]]
    ax.bar(global_differences["feature_family"], global_differences["cohens_dz"], color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Cohen dz (EEG minus MEG)")
    ax.set_title("Global feature-level paired differences")
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    figure.savefig(figures_dir / "fig2_global_feature_differences.png", dpi=300, bbox_inches="tight")
    plt.close(figure)


if __name__ == "__main__":
    main()
