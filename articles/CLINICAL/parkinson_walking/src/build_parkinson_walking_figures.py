from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = ARTICLE_DIR / "results" / "parkinson_walking_20260610"
FIGURE_DIR = ARTICLE_DIR / "figures" / "20260610_article"

HC_COLOR = "#2563eb"
PD_COLOR = "#dc2626"
REST_COLOR = "#475569"
WALK_COLOR = "#16a34a"


@dataclass(frozen=True)
class MetricSpec:
    column: str
    label: str


@dataclass(frozen=True)
class ScatterSpec:
    source_key: str
    title: str
    task: str
    clinical_variable: str
    metric: str
    y_label: str
    network: str | None = None


COHORT_METRICS: tuple[MetricSpec, ...] = (
    MetricSpec("d_n_mean", "Walk d_n mean"),
    MetricSpec("d_n_median", "Walk d_n median"),
    MetricSpec("d_mean", "Walk d mean"),
    MetricSpec("d_median", "Walk d median"),
)

PD_PAIRED_METRICS: tuple[MetricSpec, ...] = (
    MetricSpec("d_n_mean", "PD d_n mean"),
    MetricSpec("m_a_iqr", "PD m_a IQR"),
    MetricSpec("d_iqr", "PD d IQR"),
    MetricSpec("d_mad", "PD d MAD"),
)

HC_CONTEXT_METRICS: tuple[MetricSpec, ...] = (
    MetricSpec("m_a_mean", "HC m_a mean"),
    MetricSpec("m_mean", "HC m mean"),
    MetricSpec("d_l_mean", "HC d_l mean"),
)

RHO_SCATTER_SPECS: tuple[ScatterSpec, ...] = (
    ScatterSpec(
        source_key="global_cohort",
        title="A. Rest global d_s_iqr vs age",
        task="rest",
        clinical_variable="age",
        metric="d_s_iqr",
        y_label="Rest global d_s IQR",
    ),
    ScatterSpec(
        source_key="global_cohort",
        title="B. Rest global d_s_iqr vs CTT",
        task="rest",
        clinical_variable="ctt",
        metric="d_s_iqr",
        y_label="Rest global d_s IQR",
    ),
    ScatterSpec(
        source_key="regional_cohort",
        title="C. Rest P/O e_iqr vs CTT",
        task="rest",
        clinical_variable="ctt",
        metric="e_iqr",
        network="parietal_occipital",
        y_label="Rest P/O e IQR",
    ),
    ScatterSpec(
        source_key="regional_subject",
        title="D. Rest temporal e_iqr vs UPDRS total",
        task="rest",
        clinical_variable="updrs_total",
        metric="e_iqr",
        network="temporal",
        y_label="Rest temporal e IQR",
    ),
)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_figure_dual(fig: plt.Figure, base_path: Path) -> dict[str, str]:
    ensure_dir(base_path.parent)
    svg_path = base_path.with_suffix(".svg")
    png_path = base_path.with_suffix(".png")
    fig.savefig(svg_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=240, bbox_inches="tight")
    plt.close(fig)
    return {
        "svg": str(svg_path),
        "png": str(png_path),
    }


def _finite_values(values: Iterable[float]) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    return arr[np.isfinite(arr)]


def _style_violin(body, color: str) -> None:
    body.set_facecolor(color)
    body.set_edgecolor(color)
    body.set_alpha(0.28)


def draw_group_panel(ax: plt.Axes, frame: pd.DataFrame, metric: MetricSpec) -> None:
    left = _finite_values(frame.loc[frame["group"] == "HC", metric.column])
    right = _finite_values(frame.loc[frame["group"] == "PD", metric.column])
    data = [left, right]
    positions = [1, 2]
    violin = ax.violinplot(data, positions=positions, widths=0.72, showmeans=False, showmedians=False, showextrema=False)
    for body, color in zip(violin["bodies"], (HC_COLOR, PD_COLOR), strict=False):
        _style_violin(body, color)

    rng = np.random.default_rng(42)
    for pos, values, color in zip(positions, data, (HC_COLOR, PD_COLOR), strict=False):
        jitter = rng.uniform(-0.08, 0.08, size=len(values))
        ax.scatter(np.full(len(values), pos) + jitter, values, s=12, alpha=0.75, color=color, edgecolors="none")
        if len(values):
            ax.hlines(np.median(values), pos - 0.2, pos + 0.2, color=color, linewidth=2.4)

    ax.set_xticks(positions, ["HC", "PD"])
    ax.set_title(metric.label, fontsize=10)
    ax.grid(axis="y", alpha=0.2)


def draw_paired_panel(ax: plt.Axes, frame: pd.DataFrame, metric: MetricSpec) -> None:
    rest = frame.loc[frame["task"] == "rest", ["participant_id", metric.column]].rename(columns={metric.column: "rest"})
    walk = frame.loc[frame["task"] == "walk", ["participant_id", metric.column]].rename(columns={metric.column: "walk"})
    paired = rest.merge(walk, on="participant_id", how="inner").dropna()

    rest_values = paired["rest"].to_numpy(dtype=float)
    walk_values = paired["walk"].to_numpy(dtype=float)
    violin = ax.violinplot([rest_values, walk_values], positions=[1, 2], widths=0.72, showmeans=False, showmedians=False, showextrema=False)
    for body, color in zip(violin["bodies"], (REST_COLOR, WALK_COLOR), strict=False):
        _style_violin(body, color)

    rng = np.random.default_rng(7)
    rest_jitter = rng.uniform(-0.05, 0.05, size=len(rest_values))
    walk_jitter = rng.uniform(-0.05, 0.05, size=len(walk_values))
    for idx in range(len(paired)):
        ax.plot(
            [1 + rest_jitter[idx], 2 + walk_jitter[idx]],
            [rest_values[idx], walk_values[idx]],
            color="#94a3b8",
            linewidth=0.8,
            alpha=0.45,
            zorder=1,
        )
    ax.scatter(np.full(len(rest_values), 1) + rest_jitter, rest_values, s=12, color=REST_COLOR, alpha=0.85, edgecolors="none", zorder=2)
    ax.scatter(np.full(len(walk_values), 2) + walk_jitter, walk_values, s=12, color=WALK_COLOR, alpha=0.85, edgecolors="none", zorder=2)
    if len(rest_values):
        ax.hlines(np.median(rest_values), 0.8, 1.2, color=REST_COLOR, linewidth=2.4)
        ax.hlines(np.median(walk_values), 1.8, 2.2, color=WALK_COLOR, linewidth=2.4)

    ax.set_xticks([1, 2], ["Rest", "Walk"])
    ax.set_title(metric.label, fontsize=10)
    ax.grid(axis="y", alpha=0.2)


def build_group_figure(frame: pd.DataFrame, metrics: tuple[MetricSpec, ...], title: str, output_path: Path) -> None:
    fig, axes = plt.subplots(1, len(metrics), figsize=(3.2 * len(metrics), 3.6), constrained_layout=True)
    for ax, metric in zip(np.atleast_1d(axes), metrics, strict=False):
        draw_group_panel(ax, frame, metric)
    fig.suptitle(title, fontsize=12, y=1.04)
    save_figure_dual(fig, output_path.with_suffix(""))


def build_paired_figure(frame: pd.DataFrame, metrics: tuple[MetricSpec, ...], title: str, output_path: Path) -> None:
    fig, axes = plt.subplots(1, len(metrics), figsize=(3.2 * len(metrics), 3.8), constrained_layout=True)
    for ax, metric in zip(np.atleast_1d(axes), metrics, strict=False):
        draw_paired_panel(ax, frame, metric)
    fig.suptitle(title, fontsize=12, y=1.04)
    save_figure_dual(fig, output_path.with_suffix(""))


def _pretty_clinical_label(column: str) -> str:
    mapping = {
        "age": "Age",
        "ctt": "CTT",
        "moca": "MoCA",
        "updrs_total": "UPDRS total",
        "updrs_part_iii": "UPDRS III",
    }
    return mapping.get(column, column.replace("_", " "))


def _pick_rho_row(stats_frame: pd.DataFrame, spec: ScatterSpec) -> pd.Series:
    mask = (stats_frame["task"].astype(str) == spec.task) & (
        stats_frame["clinical_variable"].astype(str) == spec.clinical_variable
    ) & (stats_frame["metric"].astype(str) == spec.metric)
    if spec.network is not None and "network" in stats_frame.columns:
        mask &= stats_frame["network"].astype(str) == spec.network
    matched = stats_frame.loc[mask]
    if matched.empty:
        raise RuntimeError(f"No rho row found for {spec}")
    if len(matched) > 1:
        raise RuntimeError(f"Multiple rho rows found for {spec}")
    return matched.iloc[0]


def _prepare_scatter_rows(run_frame: pd.DataFrame, spec: ScatterSpec) -> pd.DataFrame:
    rows = run_frame.loc[(run_frame["group"].astype(str) == "PD") & (run_frame["task"].astype(str) == spec.task)].copy()
    if spec.network is not None and "network" in rows.columns:
        rows = rows.loc[rows["network"].astype(str) == spec.network].copy()
    rows[spec.clinical_variable] = pd.to_numeric(rows[spec.clinical_variable], errors="coerce")
    rows[spec.metric] = pd.to_numeric(rows[spec.metric], errors="coerce")
    rows = rows.dropna(subset=[spec.clinical_variable, spec.metric])
    if rows.empty:
        raise RuntimeError(f"No run rows available for scatter spec {spec}")
    return rows


def draw_rho_panel(ax: plt.Axes, run_frame: pd.DataFrame, stats_frame: pd.DataFrame, spec: ScatterSpec, color: str) -> None:
    stat_row = _pick_rho_row(stats_frame, spec)
    rows = _prepare_scatter_rows(run_frame, spec)
    x = rows[spec.clinical_variable].to_numpy(dtype=float)
    y = rows[spec.metric].to_numpy(dtype=float)

    ax.scatter(
        x,
        y,
        s=42,
        color=color,
        alpha=0.88,
        edgecolor="white",
        linewidth=0.7,
    )
    if len(rows) >= 2:
        slope, intercept = np.polyfit(x, y, 1)
        grid = np.linspace(float(np.min(x)), float(np.max(x)), 200)
        fit = slope * grid + intercept
        ax.plot(grid, fit, color="#1f2937", linewidth=1.8)

    ax.set_title(spec.title, loc="left", fontsize=11, fontweight="bold")
    ax.set_xlabel(_pretty_clinical_label(spec.clinical_variable))
    ax.set_ylabel(spec.y_label)
    ax.grid(alpha=0.22)

    annotation = (
        f"rho = {float(stat_row['rho']):.3f}\n"
        f"q = {float(stat_row['q_value']):.3g}\n"
        f"n = {int(stat_row['n_subjects'])}"
    )
    ax.text(
        0.98,
        0.03,
        annotation,
        ha="right",
        va="bottom",
        transform=ax.transAxes,
        fontsize=9,
        bbox=dict(facecolor="white", alpha=0.88, edgecolor="#CBD5E0"),
    )


def build_rho_scatter_figure(
    source_frames: dict[str, pd.DataFrame],
    stat_frames: dict[str, pd.DataFrame],
    output_path: Path,
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(10.6, 8.2), constrained_layout=True)
    colors = ("#dc2626", "#dc2626", "#2563eb", "#7c3aed")
    for ax, spec, color in zip(axes.reshape(-1), RHO_SCATTER_SPECS, colors, strict=False):
        draw_rho_panel(ax, source_frames[spec.source_key], stat_frames[spec.source_key], spec, color)
    save_figure_dual(fig, output_path.with_suffix(""))


def main() -> None:
    ensure_dir(FIGURE_DIR)

    cohort = pd.read_csv(RESULTS_DIR / "contrasts_cohort_121725" / "run_metrics_cohort.csv")
    subject = pd.read_csv(RESULTS_DIR / "contrasts_subject_121725" / "run_metrics_subject.csv")
    subject_iqr_mad = pd.read_csv(RESULTS_DIR / "global_subject_121725_iqr_mad" / "run_metrics_subject.csv")
    global_cohort_iqr_mad = pd.read_csv(RESULTS_DIR / "global_cohort_121725_iqr_mad" / "run_metrics_cohort.csv")
    regional_cohort_iqr_mad = pd.read_csv(RESULTS_DIR / "regional_cohort_121725_iqr_mad" / "regional_run_metrics_cohort.csv")
    regional_subject_iqr_mad = pd.read_csv(RESULTS_DIR / "regional_subject_121725_iqr_mad" / "regional_run_metrics_subject.csv")
    global_cohort_rho = pd.read_csv(RESULTS_DIR / "global_cohort_121725_iqr_mad" / "pd_clinical_associations.csv")
    regional_cohort_rho = pd.read_csv(RESULTS_DIR / "regional_cohort_121725_iqr_mad" / "regional_pd_clinical_associations.csv")
    regional_subject_rho = pd.read_csv(RESULTS_DIR / "regional_subject_121725_iqr_mad" / "regional_pd_clinical_associations.csv")

    cohort_walk = cohort.loc[cohort["task"] == "walk"].copy()
    pd_subject = subject_iqr_mad.loc[subject_iqr_mad["group"] == "PD"].copy()
    hc_subject = subject.loc[subject["group"] == "HC"].copy()

    build_group_figure(
        cohort_walk,
        COHORT_METRICS,
        "Cohort anchor: PD vs HC during walk",
        FIGURE_DIR / "cohort_walk_focals.png",
    )
    build_paired_figure(
        pd_subject,
        PD_PAIRED_METRICS,
        "Subject anchor: PD walk vs rest with dispersion extension",
        FIGURE_DIR / "pd_walk_vs_rest_focals.png",
    )
    build_paired_figure(
        hc_subject,
        HC_CONTEXT_METRICS,
        "Secondary context: HC walk vs rest",
        FIGURE_DIR / "hc_walk_vs_rest_context.png",
    )
    build_rho_scatter_figure(
        {
            "global_cohort": global_cohort_iqr_mad,
            "regional_cohort": regional_cohort_iqr_mad,
            "regional_subject": regional_subject_iqr_mad,
        },
        {
            "global_cohort": global_cohort_rho,
            "regional_cohort": regional_cohort_rho,
            "regional_subject": regional_subject_rho,
        },
        FIGURE_DIR / "iqr_mad_rho_panels.svg",
    )

    print(f"Wrote article figures to {FIGURE_DIR}")


if __name__ == "__main__":
    main()
