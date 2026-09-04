from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from trajectory_support import ARTICLE_FACING_METRICS, CONTRAST_DIR, FIGURE_DIR, ensure_dir


METRIC_LABELS = {
    "irreversibility": "Irreversibility",
    "entropy_rate": "Entropy rate",
    "noetic_action": "Noetic action",
}
ANALYSIS_LABELS = {
    "trajectory_geometry_subject_anchored_3d": "3D subject-anchored",
    "trajectory_geometry_subject_anchored_9d": "9D subject-anchored",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build simple exploratory figures for trajectory metrics.")
    parser.add_argument(
        "--contrast-csv",
        type=Path,
        default=CONTRAST_DIR / "patient_timebin_outcome_contrasts.csv",
    )
    parser.add_argument("--output-dir", type=Path, default=FIGURE_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)

    contrasts = pd.read_csv(args.contrast_csv, low_memory=False)
    contrasts = contrasts[contrasts["metric"].isin(ARTICLE_FACING_METRICS)].copy()
    if contrasts.empty:
        raise RuntimeError("No article-facing patient-level contrasts were available to plot.")

    contrasts["metric_label"] = contrasts["metric"].map(METRIC_LABELS).fillna(contrasts["metric"])
    contrasts["analysis_label"] = contrasts["analysis_type"].map(ANALYSIS_LABELS).fillna(contrasts["analysis_type"])
    contrasts["row_label"] = contrasts["analysis_label"] + " | " + contrasts["metric_label"]
    contrasts = contrasts.sort_values(["analysis_label", "metric_label"]).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    positions = list(range(len(contrasts)))
    values = contrasts["cohens_d"].to_numpy(dtype=float)
    colors = ["#4c78a8" if "3D" in label else "#f58518" for label in contrasts["analysis_label"]]
    ax.barh(positions, values, color=colors, alpha=0.9)
    ax.axvline(0.0, color="black", linewidth=0.9)
    ax.set_yticks(positions)
    ax.set_yticklabels(contrasts["row_label"])
    ax.set_xlabel("Cohen's d (CPC1 minus CPC5)")
    ax.set_title("Exploratory trajectory effect sizes in 0-12 h")
    ax.grid(axis="x", linestyle=":", alpha=0.35)
    fig.tight_layout()

    svg_path = args.output_dir / "figure_1_trajectory_effect_sizes.svg"
    png_path = args.output_dir / "figure_1_trajectory_effect_sizes.png"
    fig.savefig(svg_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
