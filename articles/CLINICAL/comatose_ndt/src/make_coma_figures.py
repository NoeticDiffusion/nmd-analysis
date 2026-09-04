from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TIMELINE_DIR = ARTICLE_DIR / "results" / "timeline_analysis_20260606_combined_invalidityfix_primary12h"
DEFAULT_PRIMARY_CONTRAST_DIR = ARTICLE_DIR / "results" / "outcome_contrasts_20260606_combined_invalidityfix_primary12h_cpc15"
DEFAULT_HOURLY_CONTRAST_DIR = ARTICLE_DIR / "results" / "outcome_contrasts_20260606_combined_invalidityfix_hourly12h_cpc15"
DEFAULT_REVIEWER_CHECKS_DIR = ARTICLE_DIR / "results" / "reviewer_checks_20260606_combined_invalidityfix"
DEFAULT_ROBUSTNESS_DIR = ARTICLE_DIR / "results" / "robustness_checks_20260606_combined_invalidityfix_newgeom"
DEFAULT_FIGURE_DIR = ARTICLE_DIR / "figures" / "20260606_combined_invalidityfix"

GOOD_LABEL = "CPC1"
POOR_LABEL = "CPC5"
PRIMARY_TIME_BIN = "0_12h"
HOURLY_BIN_ORDER = [f"{hour}_{hour + 1}h" for hour in range(12)]
PRIMARY_METRICS = [
    ("tube_d_eff_median", "Tube d_eff"),
    ("persistence_log_det_median", "Persistence log-det"),
    ("persistence_hysteresis_log_det_median", "Persistence hysteresis log-det"),
    ("persistence_log_eig_var_median", "Persistence log eig var"),
    ("tube_capture_gate_median", "Capture gate"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate manuscript-facing figures for the coma article.")
    parser.add_argument("--timeline-dir", type=Path, default=DEFAULT_TIMELINE_DIR)
    parser.add_argument("--primary-contrast-dir", type=Path, default=DEFAULT_PRIMARY_CONTRAST_DIR)
    parser.add_argument("--hourly-contrast-dir", type=Path, default=DEFAULT_HOURLY_CONTRAST_DIR)
    parser.add_argument("--reviewer-checks-dir", type=Path, default=DEFAULT_REVIEWER_CHECKS_DIR)
    parser.add_argument("--robustness-dir", type=Path, default=DEFAULT_ROBUSTNESS_DIR)
    parser.add_argument("--figure-dir", type=Path, default=DEFAULT_FIGURE_DIR)
    return parser.parse_args()


def load_primary_cohort(timeline_dir: Path) -> pd.DataFrame:
    frame = pd.read_csv(timeline_dir / "patient_timebin_summaries.csv")
    frame = frame[frame["time_bin"] == PRIMARY_TIME_BIN].copy()
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame["group_label"] = np.where(frame["cpc_numeric"] == 1, GOOD_LABEL, np.where(frame["cpc_numeric"] == 5, POOR_LABEL, None))
    frame = frame[pd.notna(frame["group_label"])].copy()
    frame["recording_start_after_anchor_hours"] = pd.to_numeric(frame["recording_start_after_anchor_hours"], errors="coerce")
    frame["channel_coverage_frac_median"] = pd.to_numeric(frame["channel_coverage_frac_median"], errors="coerce")
    return frame


def load_contrast_frame(contrast_dir: Path) -> pd.DataFrame:
    frame = pd.read_csv(contrast_dir / "patient_timebin_outcome_contrasts.csv")
    frame = frame[frame["status"] == "ok"].copy()
    frame["cohens_d"] = pd.to_numeric(frame["cohens_d"], errors="coerce")
    frame["mannwhitney_p"] = pd.to_numeric(frame["mannwhitney_p"], errors="coerce")
    return frame


def write_fig1_cohort_coverage(cohort: pd.DataFrame, figure_dir: Path) -> None:
    site_counts = (
        cohort.groupby(["hospital", "group_label"], as_index=False)
        .agg(n_subjects=("subject", "nunique"))
        .sort_values(["hospital", "group_label"])
    )

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6))

    pivot = site_counts.pivot(index="hospital", columns="group_label", values="n_subjects").fillna(0.0)
    hospitals = list(pivot.index)
    x = np.arange(len(hospitals))
    width = 0.38
    axes[0].bar(x - width / 2, pivot.get(GOOD_LABEL, pd.Series(index=hospitals, data=0.0)), width=width, color="#2563eb", label=GOOD_LABEL)
    axes[0].bar(x + width / 2, pivot.get(POOR_LABEL, pd.Series(index=hospitals, data=0.0)), width=width, color="#dc2626", label=POOR_LABEL)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(hospitals)
    axes[0].set_ylabel("Subjects in 0-12 h cohort")
    axes[0].set_title("Primary cohort by site")
    axes[0].legend(frameon=False)
    axes[0].spines[["top", "right"]].set_visible(False)

    for label, color in [(GOOD_LABEL, "#2563eb"), (POOR_LABEL, "#dc2626")]:
        sub = cohort[cohort["group_label"] == label].copy()
        axes[1].scatter(
            sub["recording_start_after_anchor_hours"],
            sub["channel_coverage_frac_median"],
            alpha=0.75,
            s=30,
            color=color,
            label=label,
        )
    axes[1].set_xlabel("Recording start after anchor (h)")
    axes[1].set_ylabel("Channel coverage fraction")
    axes[1].set_title("Coverage and timing in primary window")
    axes[1].set_ylim(0, 1.05)
    axes[1].legend(frameon=False)
    axes[1].spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    fig.savefig(figure_dir / "fig1_cohort_coverage_overview.svg", format="svg", bbox_inches="tight")
    plt.close(fig)


def write_fig2_primary_reachability(primary_contrast_dir: Path, figure_dir: Path) -> None:
    frame = load_contrast_frame(primary_contrast_dir)
    frame = frame[
        (frame["analysis_type"] == "reachability_cones")
        & (frame["time_bin"] == PRIMARY_TIME_BIN)
        & (frame["metric"].isin([metric for metric, _ in PRIMARY_METRICS]))
    ].copy()
    if frame.empty:
        return

    label_map = {metric: label for metric, label in PRIMARY_METRICS}
    frame["label"] = frame["metric"].map(label_map)
    frame["label"] = pd.Categorical(frame["label"], categories=[label for _, label in PRIMARY_METRICS], ordered=True)
    frame = frame.sort_values("label")

    fig, ax = plt.subplots(figsize=(7.6, 4.5))
    colors = ["#2563eb" if value > 0 else "#dc2626" for value in frame["cohens_d"]]
    ax.barh(frame["label"], frame["cohens_d"], color=colors, alpha=0.85)
    ax.axvline(0, color="#64748b", linestyle="--", linewidth=1.0)
    ax.set_xlabel("Cohen's d (CPC1 - CPC5)")
    ax.set_title("Core reachability metrics in the 0-12 h window")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(figure_dir / "fig2_primary_reachability_panel.svg", format="svg", bbox_inches="tight")
    plt.close(fig)


def write_fig3_hourly_core_heatmap(hourly_contrast_dir: Path, figure_dir: Path) -> None:
    frame = load_contrast_frame(hourly_contrast_dir)
    frame = frame[
        (frame["analysis_type"] == "reachability_cones")
        & (frame["metric"].isin([metric for metric, _ in PRIMARY_METRICS]))
        & (frame["time_bin"].isin(HOURLY_BIN_ORDER))
    ].copy()
    if frame.empty:
        return

    label_map = {metric: label for metric, label in PRIMARY_METRICS}
    pivot = frame.pivot(index="metric", columns="time_bin", values="cohens_d")
    pivot = pivot.reindex(index=[metric for metric, _ in PRIMARY_METRICS], columns=HOURLY_BIN_ORDER)
    pivot.index = [label_map[metric] for metric in pivot.index]

    fig, ax = plt.subplots(figsize=(9.4, 4.6))
    im = ax.imshow(pivot.to_numpy(dtype=float), cmap="coolwarm", vmin=-1.0, vmax=1.0, aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_title("Hourly reachability effect sizes")
    cbar = fig.colorbar(im, ax=ax, shrink=0.88)
    cbar.set_label("Cohen's d (CPC1 - CPC5)")
    fig.tight_layout()
    fig.savefig(figure_dir / "fig3_hourly_reachability_core_heatmap.svg", format="svg", bbox_inches="tight")
    plt.close(fig)


def write_subset_sensitivity_figure(
    robustness_dir: Path,
    figure_dir: Path,
    subset_filename: str,
    title: str,
    output_name: str,
) -> None:
    path = robustness_dir / subset_filename
    if not path.exists():
        return
    frame = pd.read_csv(path)
    if frame.empty:
        return
    frame["metric"] = frame["metric"].astype(str).str.removeprefix("geom_")
    frame["cohens_d"] = pd.to_numeric(frame["cohens_d"], errors="coerce")
    label_map = {metric: label for metric, label in PRIMARY_METRICS}
    frame = frame[frame["metric"].isin(label_map.keys())].copy()
    frame = frame.dropna(subset=["metric", "cohens_d"])
    if frame.empty:
        return
    frame["metric"] = pd.Categorical(frame["metric"], categories=[metric for metric, _ in PRIMARY_METRICS], ordered=True)
    frame = frame.sort_values("metric")

    fig, ax = plt.subplots(figsize=(7.6, 4.5))
    colors = ["#2563eb" if value > 0 else "#dc2626" for value in frame["cohens_d"]]
    ax.barh([label_map[str(metric)] for metric in frame["metric"]], frame["cohens_d"], color=colors, alpha=0.85)
    ax.axvline(0, color="#64748b", linestyle="--", linewidth=1.0)
    ax.set_xlabel("Cohen's d (CPC1 - CPC5)")
    ax.set_title(title)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(figure_dir / output_name, format="svg", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    args.figure_dir.mkdir(parents=True, exist_ok=True)

    cohort = load_primary_cohort(args.timeline_dir)

    write_fig1_cohort_coverage(cohort, args.figure_dir)
    write_fig2_primary_reachability(args.primary_contrast_dir, args.figure_dir)
    write_fig3_hourly_core_heatmap(args.hourly_contrast_dir, args.figure_dir)
    write_subset_sensitivity_figure(
        args.robustness_dir,
        args.figure_dir,
        "shockable_only_selected_metric_contrasts.csv",
        "Shockable-only sensitivity",
        "fig5_shockable_sensitivity.svg",
    )
    write_subset_sensitivity_figure(
        args.robustness_dir,
        args.figure_dir,
        "nonshockable_only_selected_metric_contrasts.csv",
        "Non-shockable-only sensitivity",
        "fig6_nonshockable_sensitivity.svg",
    )

    print(f"Wrote coma figure set to {args.figure_dir}")


if __name__ == "__main__":
    main()
