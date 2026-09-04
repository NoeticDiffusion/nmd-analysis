from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import patches
import numpy as np
import pandas as pd
from scipy import stats


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_ROOT = ARTICLE_DIR / "results"
DEFAULT_REFERENCE_ROOT = ARTICLE_DIR / "results" / "rest_vs_photic_reference"
DEFAULT_FIGURES_ROOT = ARTICLE_DIR / "figures"

GROUP_COLORS = {
    "AD": "#d64f4f",
    "Healthy": "#2b6cb0",
    "FTD": "#2f855a",
}
STAGE_SHORT_LABELS = {
    "rest_baseline": "Rest",
    "photo_5hz": "5 Hz",
    "photo_10hz": "10 Hz",
    "photo_15hz": "15 Hz",
    "photo_20hz": "20 Hz",
}
NETWORK_SHORT_LABELS = {
    "frontal": "F",
    "central": "C",
    "parietal_occipital": "P/O",
    "temporal": "T",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build photic manuscript figures in both SVG and PNG.")
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--reference-root", type=Path, default=DEFAULT_REFERENCE_ROOT)
    parser.add_argument("--figures-root", type=Path, default=DEFAULT_FIGURES_ROOT)
    return parser.parse_args()


def save_figure_dual(fig: plt.Figure, base_path: Path) -> dict[str, str]:
    base_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path = base_path.with_suffix(".svg")
    png_path = base_path.with_suffix(".png")
    fig.savefig(svg_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=240, bbox_inches="tight")
    plt.close(fig)
    return {
        "svg": str(svg_path),
        "png": str(png_path),
    }


def _short_stage_label(stage_label: str) -> str:
    return STAGE_SHORT_LABELS.get(str(stage_label), str(stage_label))


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def draw_paradigm_pipeline(base_path: Path) -> dict[str, str]:
    fig = plt.figure(figsize=(12, 5.8))
    grid = fig.add_gridspec(1, 2, width_ratios=[1.1, 1.4], wspace=0.18)

    ax_timeline = fig.add_subplot(grid[0, 0])
    ax_pipeline = fig.add_subplot(grid[0, 1])

    ax_timeline.set_axis_off()
    ax_pipeline.set_axis_off()

    ax_timeline.set_title("A. Clinical paradigm", loc="left", fontsize=12, fontweight="bold")
    timeline_steps = [
        ("Rest", "#CBD5E0"),
        ("5 Hz", "#90CDF4"),
        ("10 Hz", "#63B3ED"),
        ("15 Hz", "#4299E1"),
        ("20 Hz", "#2B6CB0"),
    ]
    x_positions = np.linspace(0.08, 0.92, len(timeline_steps))
    y = 0.55
    for idx, ((label, color), xpos) in enumerate(zip(timeline_steps, x_positions)):
        rect = patches.FancyBboxPatch(
            (xpos - 0.085, y - 0.08),
            0.17,
            0.16,
            boxstyle="round,pad=0.02,rounding_size=0.02",
            facecolor=color,
            edgecolor="#1A202C",
            linewidth=1.2,
        )
        ax_timeline.add_patch(rect)
        ax_timeline.text(xpos, y, label, ha="center", va="center", fontsize=11, fontweight="bold")
        if idx < len(timeline_steps) - 1:
            ax_timeline.annotate(
                "",
                xy=(x_positions[idx + 1] - 0.105, y),
                xytext=(xpos + 0.105, y),
                arrowprops=dict(arrowstyle="->", lw=1.5, color="#2D3748"),
            )
    ax_timeline.text(
        0.5,
        0.2,
        "Eyes-closed resting baseline is used as an internal reference,\nfollowed by the frozen photic stages used in the article.",
        ha="center",
        va="center",
        fontsize=10,
    )
    ax_timeline.set_xlim(0, 1)
    ax_timeline.set_ylim(0, 1)

    ax_pipeline.set_title("B. Article-local analysis path", loc="left", fontsize=12, fontweight="bold")
    pipeline_boxes = [
        ("EEG window", 0.08, 0.72, "#E2E8F0"),
        ("CSD / denoise", 0.32, 0.72, "#E2E8F0"),
        ("9D coordinate\ncontract", 0.56, 0.72, "#BEE3F8"),
        ("Local Jacobian\n+ reachability", 0.80, 0.72, "#BEE3F8"),
        ("Group contrasts\n+ MMSE", 0.56, 0.32, "#FED7D7"),
    ]
    for label, xpos, ypos, color in pipeline_boxes:
        rect = patches.FancyBboxPatch(
            (xpos - 0.10, ypos - 0.09),
            0.20,
            0.18,
            boxstyle="round,pad=0.025,rounding_size=0.02",
            facecolor=color,
            edgecolor="#1A202C",
            linewidth=1.2,
        )
        ax_pipeline.add_patch(rect)
        ax_pipeline.text(xpos, ypos, label, ha="center", va="center", fontsize=10)

    arrow_pairs = [
        ((0.18, 0.72), (0.22, 0.72)),
        ((0.42, 0.72), (0.46, 0.72)),
        ((0.66, 0.72), (0.70, 0.72)),
        ((0.80, 0.62), (0.62, 0.40)),
        ((0.50, 0.32), (0.32, 0.62)),
    ]
    for start, end in arrow_pairs:
        ax_pipeline.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", lw=1.4, color="#2D3748"))
    ax_pipeline.text(
        0.56,
        0.10,
        "The same export path writes all manuscript figures in both SVG and PNG.",
        ha="center",
        va="center",
        fontsize=10,
    )
    ax_pipeline.set_xlim(0, 1)
    ax_pipeline.set_ylim(0, 1)

    fig.suptitle("Photic paradigm and analysis pipeline", fontsize=14, y=0.98)
    return save_figure_dual(fig, base_path)


def draw_frequency_stress_plot(group_summary: pd.DataFrame, effect_summary: pd.DataFrame, base_path: Path) -> dict[str, str]:
    curve = group_summary[group_summary["analysis_key"] == "global_mnj_9d"].copy()
    curve = curve[curve["group_label"].isin(["AD", "Healthy"])].copy()
    if curve.empty:
        raise RuntimeError("Missing global_mnj_9d group summary for Figure 2.")

    effects = effect_summary[effect_summary["analysis_key"] == "global_mnj_9d"].copy()
    if effects.empty:
        raise RuntimeError("Missing global_mnj_9d effect summary for Figure 2.")

    stage_order = (
        curve[["stage_code", "stage_label", "stage_display_label"]]
        .drop_duplicates()
        .sort_values("stage_code")
        .reset_index(drop=True)
    )
    stage_map = {
        row.stage_label: idx
        for idx, row in enumerate(stage_order.itertuples(index=False), start=0)
    }
    x_positions = np.arange(len(stage_order))

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(10.8, 7.2),
        sharex=True,
        gridspec_kw={"height_ratios": [2.6, 1.2], "hspace": 0.08},
    )
    ax_top, ax_bottom = axes

    for group_label in ("Healthy", "AD"):
        sub = curve[curve["group_label"] == group_label].copy()
        sub["x"] = sub["stage_label"].map(stage_map)
        sub = sub.sort_values("x")
        ax_top.plot(
            sub["x"],
            sub["mean_value"],
            marker="o",
            linewidth=2.2,
            color=GROUP_COLORS[group_label],
            label=group_label,
        )
        ax_top.errorbar(
            sub["x"],
            sub["mean_value"],
            yerr=sub["sem_value"].fillna(0.0),
            fmt="none",
            ecolor=GROUP_COLORS[group_label],
            elinewidth=1.4,
            capsize=3,
            alpha=0.9,
        )
        ax_top.scatter(
            sub["x"],
            sub["mean_value"],
            s=70,
            color=GROUP_COLORS[group_label],
            edgecolor="white",
            linewidth=0.9,
            zorder=3,
        )

    ax_top.set_ylabel("Global 9D MNJ `mdr_median`")
    ax_top.set_title("Resting baseline vs photic stress", loc="left", fontsize=12, fontweight="bold")
    ax_top.grid(axis="y", alpha=0.25)
    ax_top.legend(frameon=False, loc="best")

    effects["x"] = effects["stage_label"].map(stage_map)
    colors = ["#4A5568" if row.stage_label == "rest_baseline" else "#805AD5" for row in effects.itertuples()]
    ax_bottom.bar(effects["x"], effects["effect_size"], color=colors, alpha=0.85)
    ax_bottom.axhline(0.0, color="#2D3748", linewidth=1.0)
    for row in effects.itertuples():
        q_text = f"q={row.q_value:.3g}" if pd.notna(row.q_value) else "q=NA"
        ax_bottom.text(row.x, row.effect_size, q_text, ha="center", va="bottom" if row.effect_size >= 0 else "top", fontsize=8)
    ax_bottom.set_ylabel("AD - Healthy\nCohen's d")
    ax_bottom.grid(axis="y", alpha=0.2)

    ax_bottom.set_xticks(x_positions)
    ax_bottom.set_xticklabels([_short_stage_label(label) for label in stage_order["stage_label"]])
    ax_bottom.set_xlabel("State")

    return save_figure_dual(fig, base_path)


def _pick_region_metric(contrasts: pd.DataFrame) -> tuple[str, str, str]:
    stage_label = "photo_10hz"
    candidates = contrasts[
        (contrasts["contrast_name"].astype(str) == "AD_vs_Healthy")
        & (contrasts["stage_label"].astype(str) == stage_label)
        & (contrasts["analysis_type"].astype(str) == "regional_mnj_3d")
        & (contrasts["network"].astype(str) != "global")
    ].copy()
    if candidates.empty:
        raise RuntimeError("No regional 10 Hz contrast rows were available for Figure 3.")
    chosen = candidates.sort_values(["q_value", "p_value", "effect_size"], ascending=[True, True, False]).iloc[0]
    return stage_label, str(chosen["analysis_type"]), str(chosen["metric"])


def _draw_head_panel(ax: plt.Axes, values: dict[str, float], title: str, vmax: float) -> None:
    ax.set_aspect("equal")
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.25, 1.2)
    ax.axis("off")
    cmap = plt.get_cmap("coolwarm")

    def color_for(value: float | None) -> tuple[float, float, float, float]:
        if value is None or not np.isfinite(value):
            return (0.9, 0.9, 0.9, 1.0)
        scaled = 0.5 if vmax <= 0 else 0.5 + 0.5 * float(value) / vmax
        scaled = min(1.0, max(0.0, scaled))
        return cmap(scaled)

    head = patches.Circle((0, 0), radius=1.0, fill=False, linewidth=2, edgecolor="#1A202C")
    ax.add_patch(head)
    nose = patches.Polygon([(-0.12, 1.02), (0.0, 1.18), (0.12, 1.02)], closed=True, fill=False, edgecolor="#1A202C", linewidth=1.5)
    ax.add_patch(nose)
    left_ear = patches.Arc((-1.02, 0.05), 0.25, 0.55, theta1=260, theta2=100, linewidth=1.5, color="#1A202C")
    right_ear = patches.Arc((1.02, 0.05), 0.25, 0.55, theta1=80, theta2=280, linewidth=1.5, color="#1A202C")
    ax.add_patch(left_ear)
    ax.add_patch(right_ear)

    region_specs = [
        ("frontal", patches.Ellipse((0, 0.55), 1.1, 0.5)),
        ("central", patches.Ellipse((0, 0.02), 0.85, 0.55)),
        ("parietal_occipital", patches.Ellipse((0, -0.58), 1.0, 0.45)),
        ("temporal", patches.Ellipse((-0.72, 0.0), 0.36, 0.72)),
        ("temporal", patches.Ellipse((0.72, 0.0), 0.36, 0.72)),
    ]
    for network, shape in region_specs:
        shape.set_facecolor(color_for(values.get(network)))
        shape.set_edgecolor("#2D3748")
        shape.set_alpha(0.9)
        ax.add_patch(shape)

    text_positions = {
        "frontal": (0.0, 0.55),
        "central": (0.0, 0.02),
        "parietal_occipital": (0.0, -0.58),
        "temporal": (0.0, -1.04),
    }
    for network, (xpos, ypos) in text_positions.items():
        value = values.get(network)
        if value is None or not np.isfinite(value):
            label = f"{NETWORK_SHORT_LABELS[network]}\nNA"
        else:
            label = f"{NETWORK_SHORT_LABELS[network]}\n{value:+.2f}"
        ax.text(xpos, ypos, label, ha="center", va="center", fontsize=9, fontweight="bold")

    ax.set_title(title, fontsize=11, pad=10)


def draw_four_region_effect_map(contrasts: pd.DataFrame, base_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    stage_label, analysis_type, metric = _pick_region_metric(contrasts)
    stage_display = contrasts.loc[contrasts["stage_label"] == stage_label, "stage_display_label"].dropna().astype(str).unique()
    stage_display_label = stage_display[0] if len(stage_display) else stage_label

    plot_rows = contrasts[
        (contrasts["stage_label"].astype(str) == stage_label)
        & (contrasts["analysis_type"].astype(str) == analysis_type)
        & (contrasts["metric"].astype(str) == metric)
        & (contrasts["network"].astype(str) != "global")
        & (contrasts["contrast_name"].astype(str).isin(["AD_vs_Healthy", "FTD_vs_Healthy"]))
    ].copy()
    if plot_rows.empty:
        raise RuntimeError("No rows were available for the Figure 3 four-region map.")

    panel_order = ["AD_vs_Healthy", "FTD_vs_Healthy"]
    vmax = plot_rows["effect_size"].abs().max()
    vmax = float(vmax) if np.isfinite(vmax) and vmax > 0 else 1.0

    fig, axes = plt.subplots(1, 2, figsize=(10.6, 5.5))
    for ax, contrast_name in zip(axes, panel_order):
        sub = plot_rows[plot_rows["contrast_name"] == contrast_name].copy()
        values = {
            network: float(value)
            for network, value in sub.set_index("network")["effect_size"].to_dict().items()
        }
        title = "AD vs Healthy" if contrast_name == "AD_vs_Healthy" else "FTD vs Healthy"
        _draw_head_panel(ax, values, title, vmax)

    fig.suptitle(
        f"Four-region {stage_display_label} summary\n{metric} on the frozen four-region regional MNJ surface",
        fontsize=13,
        y=0.97,
    )
    norm = plt.Normalize(-vmax, vmax)
    sm = plt.cm.ScalarMappable(cmap="coolwarm", norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes, fraction=0.035, pad=0.04)
    cbar.set_label("Cohen's d")

    return save_figure_dual(fig, base_path), {
        "stage_label": stage_label,
        "stage_display_label": stage_display_label,
        "analysis_type": analysis_type,
        "metric": metric,
    }


def _linear_fit_with_ci(x: np.ndarray, y: np.ndarray, grid: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    if x.size < 3 or np.unique(x).size < 2:
        return None
    slope, intercept, _, _, _ = stats.linregress(x, y)
    fit = intercept + slope * grid
    n = x.size
    dof = n - 2
    if dof <= 0:
        return fit, fit, fit
    x_mean = x.mean()
    ssx = np.sum((x - x_mean) ** 2)
    if ssx <= 0:
        return fit, fit, fit
    residuals = y - (intercept + slope * x)
    s_err = np.sqrt(np.sum(residuals**2) / dof)
    t_value = stats.t.ppf(0.975, dof)
    delta = t_value * s_err * np.sqrt(1.0 / n + (grid - x_mean) ** 2 / ssx)
    return fit, fit - delta, fit + delta


def _pick_primary_mmse_row(mmse_summary: pd.DataFrame) -> pd.Series:
    rows = mmse_summary.copy()
    rows["q_value"] = pd.to_numeric(rows["q_value"], errors="coerce")
    rows["p_value"] = pd.to_numeric(rows["p_value"], errors="coerce")
    rows["spearman_rho"] = pd.to_numeric(rows["spearman_rho"], errors="coerce")
    rows = rows.dropna(subset=["q_value", "p_value", "spearman_rho"])
    if rows.empty:
        raise RuntimeError("No MMSE summary rows were available for the Figure 4 scatter.")

    corrected = rows[rows["q_value"] <= 0.05].copy()
    if corrected.empty:
        corrected = rows.copy()
    corrected["abs_rho"] = corrected["spearman_rho"].abs()
    return corrected.sort_values(["q_value", "p_value", "abs_rho"], ascending=[True, True, False]).iloc[0]


def _pick_best_mmse_row_for_cohort(mmse_summary: pd.DataFrame, cohort_key: str) -> pd.Series:
    rows = mmse_summary.copy()
    rows["q_value"] = pd.to_numeric(rows["q_value"], errors="coerce")
    rows["p_value"] = pd.to_numeric(rows["p_value"], errors="coerce")
    rows["spearman_rho"] = pd.to_numeric(rows["spearman_rho"], errors="coerce")
    rows = rows[rows["cohort_key"].astype(str) == str(cohort_key)].dropna(subset=["q_value", "p_value", "spearman_rho"])
    if rows.empty:
        raise RuntimeError(f"No MMSE summary rows were available for cohort {cohort_key}.")
    rows["abs_rho"] = rows["spearman_rho"].abs()
    return rows.sort_values(["q_value", "p_value", "abs_rho"], ascending=[True, True, False]).iloc[0]


def _mmse_ylabel(stat_row: pd.Series) -> str:
    analysis_label = str(stat_row.get("analysis_label", "")).strip()
    metric = str(stat_row["metric"])
    network = str(stat_row["network"])
    if analysis_label:
        if network == "global":
            return f"{analysis_label} `{metric}`"
        return f"{analysis_label} ({network}) `{metric}`"
    if network == "global":
        return str(metric)
    return f"{network} `{metric}`"


def _mmse_title(stat_row: pd.Series) -> str:
    cohort_key = str(stat_row["cohort_key"])
    stage_display = str(stat_row.get("stage_display_label") or stat_row["stage_label"])
    cohort_title = {
        "Dementia_all": "Pooled dementia",
        "AD_only": "AD",
        "FTD_only": "FTD",
    }.get(cohort_key, cohort_key)
    return f"{cohort_title} MMSE association at {stage_display}"


def draw_mmse_scatter(metric_frame: pd.DataFrame, stat_row: pd.Series, base_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    stage_label = str(stat_row["stage_label"])
    analysis_type = str(stat_row["analysis_type"])
    network = str(stat_row["network"])
    metric = str(stat_row["metric"])
    cohort_key = str(stat_row["cohort_key"])

    plot_rows = metric_frame[
        (metric_frame["stage_label"].astype(str) == stage_label)
        & (metric_frame["analysis_type"].astype(str) == analysis_type)
        & (metric_frame["network"].astype(str) == network)
        & (metric_frame["metric"].astype(str) == metric)
    ].copy()
    plot_rows["mmse"] = pd.to_numeric(plot_rows["mmse"], errors="coerce")
    plot_rows["value"] = pd.to_numeric(plot_rows["value"], errors="coerce")
    plot_rows = plot_rows.dropna(subset=["mmse", "value"])
    if plot_rows.empty:
        raise RuntimeError("Missing subject-level rows for the Figure 4 MMSE scatter.")

    if cohort_key == "Dementia_all":
        focus_groups = ["AD", "FTD"]
        background_groups = ["Healthy"]
    elif cohort_key == "AD_only":
        focus_groups = ["AD"]
        background_groups = ["Healthy", "FTD"]
    else:
        focus_groups = ["FTD"]
        background_groups = ["Healthy", "AD"]

    background = plot_rows[plot_rows["group_label"].astype(str).isin(background_groups)].copy()
    focus = plot_rows[plot_rows["group_label"].astype(str).isin(focus_groups)].copy()
    if focus.empty:
        raise RuntimeError(f"No focus rows were available for cohort {cohort_key} in MMSE scatter.")

    fig, ax = plt.subplots(figsize=(8.6, 6.2))

    if not background.empty:
        ax.scatter(
            background["mmse"],
            background["value"],
            s=28,
            color="#A0AEC0",
            alpha=0.45,
            edgecolor="none",
            label="Background",
        )

    for group_label in focus_groups:
        sub = focus[focus["group_label"].astype(str) == group_label].copy()
        if sub.empty:
            continue
        ax.scatter(
            sub["mmse"],
            sub["value"],
            s=55,
            color=GROUP_COLORS.get(group_label, "#2D3748"),
            alpha=0.95,
            edgecolor="white",
            linewidth=0.8,
            label=group_label,
        )

    x = focus["mmse"].to_numpy(dtype=float)
    y = focus["value"].to_numpy(dtype=float)
    grid = np.linspace(float(np.min(x)) - 0.5, float(np.max(x)) + 0.5, 200)
    fit_bundle = _linear_fit_with_ci(x, y, grid)
    if fit_bundle is not None:
        fit, lower, upper = fit_bundle
        ax.plot(grid, fit, color="#2D3748", linewidth=2.0)
        ax.fill_between(grid, lower, upper, color="#2D3748", alpha=0.14)

    ax.set_xlabel("MMSE")
    ax.set_ylabel(_mmse_ylabel(stat_row))
    ax.set_title(_mmse_title(stat_row), loc="left", fontsize=12, fontweight="bold")
    ax.grid(alpha=0.22)
    ax.legend(frameon=False, loc="upper left")

    annotation = (
        f"Cohort = {cohort_key}\n"
        f"Spearman rho = {float(stat_row['spearman_rho']):.3f}\n"
        f"p = {float(stat_row['p_value']):.3g}\n"
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
        fontsize=10,
        bbox=dict(facecolor="white", alpha=0.85, edgecolor="#CBD5E0"),
    )

    meta = {
        "cohort_key": cohort_key,
        "stage_label": stage_label,
        "stage_display_label": str(stat_row.get("stage_display_label") or stage_label),
        "analysis_type": analysis_type,
        "analysis_label": str(stat_row.get("analysis_label", "")),
        "metric": metric,
        "network": network,
        "spearman_rho": float(stat_row["spearman_rho"]),
        "p_value": float(stat_row["p_value"]),
        "q_value": float(stat_row["q_value"]),
        "n_subjects": int(stat_row["n_subjects"]),
    }
    return save_figure_dual(fig, base_path), meta


def main() -> None:
    args = parse_args()
    args.figures_root.mkdir(parents=True, exist_ok=True)

    group_summary = _load_csv(args.reference_root / "rest_vs_photic_mdr_group_summary.csv")
    effect_summary = _load_csv(args.reference_root / "rest_vs_photic_mdr_ad_vs_healthy_effects.csv")
    contrast_summary = _load_csv(args.results_root / "group_frequency_contrasts.csv")
    metric_frame = _load_csv(args.results_root / "subject_stage_region_metrics.csv")
    mmse_summary = _load_csv(args.results_root / "mmse_correlations_summary.csv")

    figure_manifest: dict[str, object] = {}
    figure_manifest["figure_1"] = draw_paradigm_pipeline(args.figures_root / "figure_1_paradigm_pipeline")
    figure_manifest["figure_2"] = draw_frequency_stress_plot(
        group_summary,
        effect_summary,
        args.figures_root / "figure_2_rest_vs_photic_stress",
    )
    figure_3_paths, figure_3_meta = draw_four_region_effect_map(
        contrast_summary,
        args.figures_root / "figure_3_four_region_map",
    )
    figure_manifest["figure_3"] = figure_3_paths
    figure_manifest["figure_3_meta"] = figure_3_meta
    figure_4_paths, figure_4_meta = draw_mmse_scatter(
        metric_frame,
        _pick_primary_mmse_row(mmse_summary),
        args.figures_root / "figure_4_ftd_frontal_mmse_scatter",
    )
    figure_manifest["figure_4"] = figure_4_paths
    figure_manifest["figure_4_meta"] = figure_4_meta
    figure_5_paths, figure_5_meta = draw_mmse_scatter(
        metric_frame,
        _pick_best_mmse_row_for_cohort(mmse_summary, "FTD_only"),
        args.figures_root / "figure_5_ftd_only_mmse_scatter",
    )
    figure_manifest["figure_5"] = figure_5_paths
    figure_manifest["figure_5_meta"] = figure_5_meta

    manifest_path = args.figures_root / "figure_manifest.json"
    manifest_path.write_text(json.dumps(figure_manifest, indent=2), encoding="utf-8")
    print(f"Wrote figure outputs to {args.figures_root}")


if __name__ == "__main__":
    main()
