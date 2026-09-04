"""Create APPLESEED reliability and exploratory developmental figures."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from appleseed_support import DEFAULT_RESULTS_ROOT, PRIMARY_ENDPOINTS

DEVELOPMENTAL_ENDPOINTS = (
    "tube_d_eff_median",
    "spectral_radius_median",
    "tube_dir_entropy_median",
)
DISPLAY_NAMES = {
    "tube_d_eff_median": "Reachability effective dimension",
    "spectral_radius_median": "MNJ spectral radius",
    "tube_dir_entropy_median": "Reachability directional entropy",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_RESULTS_ROOT / "01_session_metrics" / "session_metrics.csv")
    parser.add_argument("--reliability", type=Path, default=DEFAULT_RESULTS_ROOT / "02_reliability_longitudinal" / "reliability_metrics.csv")
    parser.add_argument("--cohort-age", type=Path, default=DEFAULT_RESULTS_ROOT / "02_reliability_longitudinal" / "cohort_4m_to_8m.csv")
    parser.add_argument("--longitudinal", type=Path, default=DEFAULT_RESULTS_ROOT / "02_reliability_longitudinal" / "longitudinal_contrasts.csv")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_ROOT / "04_figures")
    return parser.parse_args()


def save(fig: plt.Figure, path: Path) -> None:
    """Write both manuscript-ready raster and vector copies."""
    fig.tight_layout()
    fig.savefig(path.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(path.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def balanced_panel(metrics: pd.DataFrame) -> pd.DataFrame:
    """Retain exactly the 11 children contributing 4- and 8-month data."""
    eligible = metrics.groupby("subject_id")["session"].agg(set)
    eligible = eligible[eligible.apply(lambda sessions: {1, 2, 3}.issubset(sessions))].index
    return metrics[metrics["subject_id"].isin(eligible)].copy()


def make_icc_forest(reliability: pd.DataFrame, output_dir: Path) -> None:
    ordered = reliability.set_index("endpoint").reindex(PRIMARY_ENDPOINTS).reset_index()
    labels = [DISPLAY_NAMES.get(endpoint, endpoint.replace("_median", "").replace("_", " ")) for endpoint in ordered["endpoint"]]
    positions = np.arange(len(ordered))
    fig, ax = plt.subplots(figsize=(8.1, 4.7))
    ax.hlines(positions, ordered["icc_ci95_low"], ordered["icc_ci95_high"], color="#F58518", linewidth=1.8)
    ax.scatter(ordered["icc_a1"], positions, color="#F58518", s=45, zorder=3)
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set(
        yticks=positions,
        yticklabels=labels,
        xlim=(-1, 1),
        xlabel="ICC(A,1), session 1 vs session 2",
        title="Test--retest reliability (n = 13)",
    )
    ax.invert_yaxis()
    ax.text(0.01, 0.01, "Points: ICC(A,1); lines: child-bootstrap 95% intervals.", transform=ax.transAxes, fontsize=8)
    save(fig, output_dir / "fig2_reliability_icc")


def make_exploratory_effects(cohort_age: pd.DataFrame, output_dir: Path) -> None:
    results = cohort_age[cohort_age["endpoint"].isin(DEVELOPMENTAL_ENDPOINTS)].copy()
    results["endpoint"] = pd.Categorical(results["endpoint"], DEVELOPMENTAL_ENDPOINTS, ordered=True)
    results = results.sort_values("endpoint")
    labels = [DISPLAY_NAMES[value] for value in results["endpoint"]]
    colors = ["#4C78A8" if effect < 0 else "#E45756" for effect in results["cohen_dz"]]
    fig, ax = plt.subplots(figsize=(8.0, 3.5))
    bars = ax.barh(labels, results["cohen_dz"], color=colors)
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set(xlabel="Paired effect size (d_z)", title="Exploratory 4-month mean to 8-month effects (n = 11)", xlim=(-1, 1))
    for bar, (_, row) in zip(bars, results.iterrows()):
        label = f"d_z={row['cohen_dz']:.2f}; raw p={row['p_raw']:.3f}"
        if row["cohen_dz"] < 0:
            ax.text(row["cohen_dz"] / 2, bar.get_y() + bar.get_height() / 2, label, va="center", ha="center", color="white", fontsize=8)
        else:
            ax.text(row["cohen_dz"] + 0.035, bar.get_y() + bar.get_height() / 2, label, va="center", ha="left", fontsize=8)
    ax.text(0.01, 0.01, "Exploratory raw-p analysis; not a multiplicity-corrected discovery.", transform=ax.transAxes, fontsize=8)
    save(fig, output_dir / "fig3_exploratory_4to8_effects")


def make_paired_age(panel: pd.DataFrame, output_dir: Path, target_session: int, target_label: str) -> None:
    baseline = panel[panel["session"].isin([1, 2])].groupby("subject_id")[list(DEVELOPMENTAL_ENDPOINTS)].mean()
    follow_up = panel[panel["session"] == target_session].set_index("subject_id")[list(DEVELOPMENTAL_ENDPOINTS)]
    paired = baseline.join(follow_up, lsuffix="_4m", rsuffix="_target", how="inner")
    fig, axes = plt.subplots(1, len(DEVELOPMENTAL_ENDPOINTS), figsize=(10.5, 3.6))
    for axis, endpoint in zip(axes, DEVELOPMENTAL_ENDPOINTS):
        before, after = paired[f"{endpoint}_4m"], paired[f"{endpoint}_target"]
        for value4, value8 in zip(before, after):
            axis.plot([0, 1], [value4, value8], color="#A6CEE3", alpha=0.85, linewidth=1)
        axis.scatter(np.zeros(len(before)), before, color="#4C78A8", s=25, zorder=3, label="4-month mean")
        axis.scatter(np.ones(len(after)), after, color="#E45756", s=25, zorder=3, label=target_label)
        axis.set(xlim=(-0.25, 1.25), xticks=[0, 1], xticklabels=["4 mo\n(mean S1/S2)", f"{target_label}\n(S{target_session})"], title=DISPLAY_NAMES[endpoint])
    axes[0].set_ylabel("Session summary value")
    axes[-1].legend(loc="best", fontsize=7)
    fig.suptitle(f"Within-child 4-month to {target_label} trajectories (balanced n = 11)", y=1.02)
    save(fig, output_dir / f"fig{4 if target_session == 3 else 7}_paired_4to{8 if target_session == 3 else 12}_slopes")


def make_cohort_coordinate_slopes(panel: pd.DataFrame, output_dir: Path, target_session: int, target_label: str) -> None:
    """Display common-scale coordinates without treating them as latent states."""
    endpoints = ("cohort_m_median", "cohort_d_median", "cohort_e_median")
    names = ("Mobility coordinate", "Deviation coordinate", "Entropy-related coordinate")
    baseline = panel[panel["session"].isin([1, 2])].groupby("subject_id")[list(endpoints)].mean()
    follow_up = panel[panel["session"] == target_session].set_index("subject_id")[list(endpoints)]
    paired = baseline.join(follow_up, lsuffix="_4m", rsuffix="_target", how="inner")
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.3))
    for axis, endpoint, name in zip(axes, endpoints, names):
        for value4, value_target in zip(paired[f"{endpoint}_4m"], paired[f"{endpoint}_target"]):
            axis.plot([0, 1], [value4, value_target], color="#A6CEE3", alpha=0.85, linewidth=1)
        axis.scatter(np.zeros(len(paired)), paired[f"{endpoint}_4m"], color="#4C78A8", s=25, zorder=3)
        axis.scatter(np.ones(len(paired)), paired[f"{endpoint}_target"], color="#E45756", s=25, zorder=3)
        axis.set(xlim=(-0.25, 1.25), xticks=[0, 1], xticklabels=["4 mo\n(mean S1/S2)", f"{target_label}\n(S{target_session})"], title=name)
    axes[0].set_ylabel("Cohort-anchored coordinate")
    fig.suptitle(f"Exploratory common-scale 3D coordinate shifts to {target_label} (balanced n = 11)", y=1.02)
    save(fig, output_dir / f"fig{6 if target_session == 3 else 8}_cohort_coordinate_4to{8 if target_session == 3 else 12}_slopes")


def make_full_trajectories(panel: pd.DataFrame, output_dir: Path) -> None:
    fig, axes = plt.subplots(1, len(DEVELOPMENTAL_ENDPOINTS), figsize=(10.5, 3.4), sharex=True)
    for axis, endpoint in zip(axes, DEVELOPMENTAL_ENDPOINTS):
        sns.lineplot(panel, x="session", y=endpoint, units="subject_id", estimator=None, color="#9ECAE1", alpha=0.7, ax=axis)
        sns.pointplot(panel, x="session", y=endpoint, color="#D62728", errorbar=("ci", 95), ax=axis)
        axis.set(title=DISPLAY_NAMES[endpoint], xlabel="Session")
        axis.set(xticks=[1, 2, 3, 4], xticklabels=["S1\n4 mo", "S2\n4 mo", "S3\n8 mo", "S4\n12 mo"])
    axes[0].set_ylabel("Session summary value")
    fig.suptitle("Four-session trajectories for children with longitudinal follow-up (n = 11)", y=1.02)
    save(fig, output_dir / "fig5_balanced_longitudinal_trajectories")


def make_effect_heatmap(cohort_age: pd.DataFrame, longitudinal: pd.DataFrame, output_dir: Path) -> None:
    """Supplementary overview; its colors encode effect direction, not significance."""
    four_to_eight = cohort_age.copy()
    four_to_eight["contrast"] = "4-mo mean → 8 mo"
    follow_up = longitudinal[longitudinal["contrast"].isin(["ses-3_minus_ses-1", "ses-4_minus_ses-1"])].copy()
    follow_up["contrast"] = follow_up["contrast"].map(
        {"ses-3_minus_ses-1": "S1 → 8 mo", "ses-4_minus_ses-1": "S1 → 12 mo"}
    )
    combined = pd.concat([four_to_eight, follow_up], ignore_index=True)
    effects = combined.pivot(index="endpoint", columns="contrast", values="cohen_dz").reindex(PRIMARY_ENDPOINTS)
    labels = [DISPLAY_NAMES.get(endpoint, endpoint.replace("_median", "").replace("_", " ")) for endpoint in effects.index]
    fig, ax = plt.subplots(figsize=(7.0, 5.0))
    sns.heatmap(effects, cmap="coolwarm", center=0, vmin=-1, vmax=1, annot=True, fmt=".2f", linewidths=0.5, cbar_kws={"label": "paired d_z"}, ax=ax)
    ax.set(yticklabels=labels, xlabel="", ylabel="", title="Exploratory developmental effect-size overview")
    ax.text(0.0, -0.12, "Color and labels show effect size only; no cell denotes a corrected discovery.", transform=ax.transAxes, fontsize=8)
    save(fig, output_dir / "figS1_exploratory_effect_heatmap")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics = pd.read_csv(args.metrics)
    reliability = pd.read_csv(args.reliability)
    cohort_age = pd.read_csv(args.cohort_age)
    longitudinal = pd.read_csv(args.longitudinal)
    sns.set_theme(style="whitegrid", context="paper")
    panel = balanced_panel(metrics)
    make_icc_forest(reliability, args.output_dir)
    make_exploratory_effects(cohort_age, args.output_dir)
    make_paired_age(panel, args.output_dir, 3, "8 mo")
    make_paired_age(panel, args.output_dir, 4, "12 mo")
    make_full_trajectories(panel, args.output_dir)
    make_cohort_coordinate_slopes(panel, args.output_dir, 3, "8 mo")
    make_cohort_coordinate_slopes(panel, args.output_dir, 4, "12 mo")
    make_effect_heatmap(cohort_age, longitudinal, args.output_dir)


if __name__ == "__main__":
    main()
