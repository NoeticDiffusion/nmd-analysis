"""Create figures for the Figshare infant EEG developmental study."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from figshare_infant_support import DEFAULT_RESULTS_ROOT

DISPLAY = {
    "tube_d_eff_median": "Reachability effective dimension",
    "spectral_radius_median": "MNJ spectral radius",
    "tube_dir_entropy_median": "Reachability directional entropy",
}
PLOT_ENDPOINTS = tuple(DISPLAY)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_RESULTS_ROOT / "01_session_metrics" / "session_metrics.csv")
    parser.add_argument("--primary", type=Path, default=DEFAULT_RESULTS_ROOT / "02_developmental_analysis" / "within_child_age_associations.csv")
    parser.add_argument("--nine-d", type=Path, default=DEFAULT_RESULTS_ROOT / "02_developmental_analysis" / "within_child_age_associations_9d.csv")
    parser.add_argument("--cohort-age", type=Path, default=DEFAULT_RESULTS_ROOT / "03_cohort_coordinate_age" / "cohort_coordinate_gee_results.csv")
    parser.add_argument("--cohort-predictions", type=Path, default=DEFAULT_RESULTS_ROOT / "03_cohort_coordinate_age" / "cohort_coordinate_gee_predictions.csv")
    parser.add_argument("--pooled-reachability", type=Path, default=DEFAULT_RESULTS_ROOT / "05_cohort_pooled_reachability" / "cohort_pooled_reachability_age_associations.csv")
    parser.add_argument("--pooled-reachability-per-visit", type=Path, default=DEFAULT_RESULTS_ROOT / "05_cohort_pooled_reachability" / "cohort_pooled_reachability_per_visit.csv")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_ROOT / "04_figures")
    return parser.parse_args()


def save(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(path.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def coverage(metrics: pd.DataFrame, output_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.4))
    subjects = sorted(metrics.subject_id.unique())
    positions = {subject: index for index, subject in enumerate(subjects)}
    axes[0].scatter(metrics.age_days, metrics.subject_id.map(positions), color="#4C78A8", s=30)
    axes[0].set(yticks=range(len(subjects)), yticklabels=subjects, xlabel="Age at recording (days)", ylabel="Child", title="Irregular longitudinal age coverage")
    counts = metrics.groupby("subject_id").size().value_counts().sort_index()
    axes[1].bar(counts.index.astype(str), counts.values, color="#F58518")
    axes[1].set(xlabel="Number of visits per child", ylabel="Children", title="Visit-count distribution")
    fig.suptitle("Figshare infant EEG cohort: 70 visits from 22 children", y=1.03)
    save(fig, output_dir / "fig1_age_coverage")


def trajectories(metrics: pd.DataFrame, output_dir: Path) -> None:
    fig, axes = plt.subplots(1, len(PLOT_ENDPOINTS), figsize=(11, 3.5))
    for axis, endpoint in zip(axes, PLOT_ENDPOINTS):
        frame = metrics[["subject_id", "age_days", endpoint]].dropna()
        for _, child in frame.groupby("subject_id"):
            axis.plot(child.age_days, child[endpoint], color="#A6CEE3", alpha=0.75, linewidth=1)
            axis.scatter(child.age_days, child[endpoint], color="#4C78A8", s=12)
        axis.set(title=DISPLAY[endpoint], xlabel="Age (days)")
    axes[0].set_ylabel("Visit-level summary")
    fig.suptitle("Within-child cohort-anchored developmental trajectories", y=1.03)
    save(fig, output_dir / "fig2_within_child_trajectories")


def effects(primary: pd.DataFrame, output_dir: Path) -> None:
    results = primary[primary.endpoint.isin(PLOT_ENDPOINTS)].copy()
    results.endpoint = pd.Categorical(results.endpoint, PLOT_ENDPOINTS, ordered=True)
    results = results.sort_values("endpoint")
    fig, ax = plt.subplots(figsize=(8.4, 3.5))
    labels = [DISPLAY[endpoint] for endpoint in results.endpoint]
    colors = ["#4C78A8" if value < 0 else "#E45756" for value in results.standardized_within_slope]
    bars = ax.barh(labels, results.standardized_within_slope, color=colors)
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set(xlabel="Standardized within-child age slope", title="Exploratory within-child developmental associations")
    for bar, (_, row) in zip(bars, results.iterrows()):
        ax.text(row.standardized_within_slope, bar.get_y() + bar.get_height() / 2, f"  p={row.sign_permutation_p_raw:.3f}", va="center", fontsize=8)
    ax.text(0.01, 0.01, "Child-cluster sign-permutation raw p-values; exploratory.", transform=ax.transAxes, fontsize=8)
    save(fig, output_dir / "fig3_primary_age_effects")


def nine_d_qc(metrics: pd.DataFrame, nine_d: pd.DataFrame, output_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4))
    availability = metrics.groupby("subject_id").jacobian_9d_available.mean()
    axes[0].bar(range(len(availability)), availability.values, color="#59A14F")
    axes[0].set(ylim=(0, 1.05), xlabel="Child", ylabel="Fraction of visits with 9D MNJ", title="9D MNJ availability")
    if not nine_d.empty:
        values = nine_d.sort_values("sign_permutation_p_raw").head(8)
        axes[1].barh(values.endpoint.str.replace("mn9d_", "").str.replace("_median", ""), values.standardized_within_slope, color="#B07AA1")
        axes[1].axvline(0, color="#333333", linewidth=0.8)
    axes[1].set(xlabel="Standardized within-child slope", title="Top 9D sensitivity effects")
    fig.suptitle("Secondary QC-masked 9D MNJ sensitivity analysis", y=1.03)
    save(fig, output_dir / "fig4_nine_d_qc_sensitivity")


def cohort_age_models(results: pd.DataFrame, predictions: pd.DataFrame, output_dir: Path) -> None:
    endpoints = ("cohort_m_median", "cohort_d_median", "cohort_e_median")
    labels = ("Mobility coordinate", "Deviation coordinate", "Entropy-related coordinate")
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    for axis, endpoint, label in zip(axes, endpoints, labels):
        curve = predictions[predictions.endpoint.eq(endpoint)]
        summary = results.set_index("endpoint").loc[endpoint]
        axis.plot(curve.age_days, curve.predicted_mean, color="#E45756", linewidth=2)
        axis.fill_between(curve.age_days, curve.ci95_low, curve.ci95_high, color="#E45756", alpha=0.2)
        axis.set(title=label, xlabel="Age (days)")
        axis.text(0.02, 0.02, f"GEE omnibus p={summary.p_raw:.2g}\nFDR p={summary.p_fdr:.2g}", transform=axis.transAxes, fontsize=8)
    axes[0].set_ylabel("Cohort-anchored coordinate")
    fig.suptitle("Primary cohort-anchored age trajectories (child-clustered GEE)", y=1.03)
    save(fig, output_dir / "fig5_cohort_coordinate_age_models")


POOLED_DISPLAY = {
    "cohort_pooled_tube_log_det": "log-volume",
    "cohort_pooled_tube_d_eff": "effective dimension",
    "cohort_pooled_tube_kappa": "anisotropy",
    "cohort_pooled_tube_dir_entropy": "directional entropy",
    "cohort_pooled_tube_rotation": "rotational proxy",
}


def pooled_reachability(pooled: pd.DataFrame, per_visit: pd.DataFrame, output_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.6))
    results = pooled[pooled.endpoint.isin(POOLED_DISPLAY)].copy()
    results.endpoint = pd.Categorical(results.endpoint, list(POOLED_DISPLAY), ordered=True)
    results = results.sort_values("endpoint")
    labels = [POOLED_DISPLAY[endpoint] for endpoint in results.endpoint]
    colors = ["#4C78A8" if value < 0 else "#E45756" for value in results.standardized_within_slope]
    bars = axes[0].barh(labels, results.standardized_within_slope, color=colors)
    axes[0].axvline(0, color="#333333", linewidth=0.8)
    axes[0].set(xlabel="Standardized within-child age slope", title="Cohort-pooled reachability age effects")
    for bar, (_, row) in zip(bars, results.iterrows()):
        axes[0].text(row.standardized_within_slope, bar.get_y() + bar.get_height() / 2, f"  p={row.sign_permutation_p_raw:.3f}", va="center", fontsize=8)

    testable = per_visit[~per_visit.not_testable]
    for _, child in testable.groupby("subject_id"):
        axes[1].plot(child.age_days, child.cohort_pooled_tube_rotation, color="#B07AA1", alpha=0.6, linewidth=1)
        axes[1].scatter(child.age_days, child.cohort_pooled_tube_rotation, color="#59A14F", s=14)
    axes[1].set(xlabel="Age (days)", ylabel="Cohort-pooled rotational proxy", title="Smallest raw-p endpoint (not FDR-supported)")
    fig.suptitle("Cohort-pooled reachability: leave-one-child-out local flow field", y=1.03)
    save(fig, output_dir / "fig6_cohort_pooled_reachability")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics = pd.read_csv(args.metrics)
    primary = pd.read_csv(args.primary)
    nine_d = pd.read_csv(args.nine_d)
    cohort_results = pd.read_csv(args.cohort_age)
    cohort_predictions = pd.read_csv(args.cohort_predictions)
    coverage(metrics, args.output_dir)
    trajectories(metrics, args.output_dir)
    effects(primary, args.output_dir)
    nine_d_qc(metrics, nine_d, args.output_dir)
    cohort_age_models(cohort_results, cohort_predictions, args.output_dir)
    if args.pooled_reachability.exists() and args.pooled_reachability_per_visit.exists():
        pooled_reachability(pd.read_csv(args.pooled_reachability), pd.read_csv(args.pooled_reachability_per_visit), args.output_dir)


if __name__ == "__main__":
    main()
