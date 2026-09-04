from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ARTICLE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = ARTICLE_DIR / "results"
FIGURES_DIR = ARTICLE_DIR / "figures"
PRIMARY_SPEC = "posterior_capacity_global_guidance"
PRIMARY_STAGE = "photo_15hz"
STAGE_ORDER = ["photo_5hz", "photo_10hz", "photo_15hz", "photo_20hz"]
STAGE_LABELS = {
    "photo_5hz": "5 Hz",
    "photo_10hz": "10 Hz",
    "photo_15hz": "15 Hz",
    "photo_20hz": "20 Hz",
}
GROUP_ORDER = ["Healthy", "AD", "FTD"]
GROUP_COLORS = {
    "Healthy": "#2a9d8f",
    "AD": "#d1495b",
    "FTD": "#4f6d7a",
}
COMPARATOR_ORDER = [
    "stage_matched_power_proxy",
    "posterior_alpha_power",
    "posterior_alpha_theta_ratio",
    "posterior_sample_entropy",
]


def _save_dual(fig: plt.Figure, base_name: str, manifest: list[dict[str, str]]) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    png_path = FIGURES_DIR / f"{base_name}.png"
    svg_path = FIGURES_DIR / f"{base_name}.svg"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight")
    manifest.append({"base_name": base_name, "png": str(png_path), "svg": str(svg_path)})
    plt.close(fig)


def _group_order_key(label: str) -> int:
    try:
        return GROUP_ORDER.index(label)
    except ValueError:
        return 999


def build_concept_figure(manifest: list[dict[str, str]]) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.axis("off")
    boxes = [
        (0.06, 0.52, 0.22, 0.26, "Rest anchor\n(ds004504)"),
        (0.39, 0.52, 0.22, 0.26, "Photic response\n(ds006036)"),
        (0.72, 0.52, 0.22, 0.26, "Primary score\nESB-2"),
        (0.39, 0.12, 0.22, 0.22, "Secondary test\nPRL"),
    ]
    for x, y, w, h, text in boxes:
        fill = "#f5f5f5" if "Secondary" not in text else "#fafafa"
        linestyle = "-" if "Secondary" not in text else "--"
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=fill, edgecolor="#555555", linewidth=1.2, linestyle=linestyle))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=12)
    ax.annotate("", xy=(0.39, 0.65), xytext=(0.28, 0.65), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.annotate("", xy=(0.72, 0.65), xytext=(0.61, 0.65), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.annotate("", xy=(0.50, 0.34), xytext=(0.83, 0.52), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.text(0.5, 0.93, "Evoked Structural Brittleness workflow", ha="center", fontsize=14, fontweight="bold")
    ax.text(
        0.5,
        0.02,
        "Local outputs: primary ESB-2 contrasts, specification sensitivity, negative-result checks, and bounded secondary extensions.",
        ha="center",
        fontsize=10,
    )
    _save_dual(fig, "figure_1_esb_prl_schematic", manifest)


def build_esb_trajectory_figure(esb_group: pd.DataFrame, manifest: list[dict[str, str]]) -> None:
    sub = esb_group[esb_group["spec_name"] == PRIMARY_SPEC].copy()
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    x = np.arange(len(STAGE_ORDER), dtype=float)
    for group_label in GROUP_ORDER:
        group = sub[sub["group_label"] == group_label].copy().set_index("stage_label").reindex(STAGE_ORDER)
        y = pd.to_numeric(group["esb2_ds004504_mean"], errors="coerce").to_numpy(dtype=float)
        ax.plot(x, y, marker="o", lw=2, color=GROUP_COLORS[group_label], label=group_label)
    ax.axvline(2, color="#aaaaaa", linestyle="--", linewidth=1)
    ax.set_xticks(x, [STAGE_LABELS[s] for s in STAGE_ORDER])
    ax.set_ylabel("Mean ESB-2 score")
    ax.set_xlabel("Photic stage")
    ax.set_title("Primary ESB-2 trajectory by diagnosis")
    ax.legend(frameon=False)
    ax.grid(alpha=0.2)
    _save_dual(fig, "figure_2_esb2_group_trajectories", manifest)


def build_capacity_guidance_figure(esb_scores: pd.DataFrame, manifest: list[dict[str, str]]) -> None:
    sub = esb_scores[
        (esb_scores["spec_name"] == PRIMARY_SPEC)
        & (esb_scores["stage_label"] == PRIMARY_STAGE)
    ].copy()
    fig, ax = plt.subplots(figsize=(6.8, 5.8))
    for group_label in GROUP_ORDER:
        group = sub[sub["group_label"] == group_label].copy()
        ax.scatter(
            pd.to_numeric(group["delta_capacity_rest"], errors="coerce"),
            pd.to_numeric(group["delta_guidance_rest"], errors="coerce"),
            s=38,
            alpha=0.8,
            label=group_label,
            color=GROUP_COLORS[group_label],
        )
    healthy = sub[sub["group_label"] == "Healthy"].copy()
    hc_x = float(pd.to_numeric(healthy["delta_capacity_rest"], errors="coerce").median())
    hc_y = float(pd.to_numeric(healthy["delta_guidance_rest"], errors="coerce").median())
    ax.axvline(hc_x, color=GROUP_COLORS["Healthy"], linestyle="--", linewidth=1)
    ax.axhline(hc_y, color=GROUP_COLORS["Healthy"], linestyle="--", linewidth=1)
    ax.scatter([hc_x], [hc_y], marker="X", s=120, color=GROUP_COLORS["Healthy"], edgecolor="black", linewidth=0.6)
    ax.set_xlabel("Delta capacity vs ds004504")
    ax.set_ylabel("Delta guidance vs ds004504")
    ax.set_title("Capacity-guidance plane at PHOTO 15 Hz")
    ax.legend(frameon=False)
    ax.grid(alpha=0.2)
    _save_dual(fig, "figure_3_capacity_guidance_plane", manifest)


def build_prl_figure(esb_scores: pd.DataFrame, prl_scores: pd.DataFrame, manifest: list[dict[str, str]]) -> None:
    spec_scores = esb_scores[esb_scores["spec_name"] == PRIMARY_SPEC].copy()
    spec_prl = prl_scores[prl_scores["spec_name"] == PRIMARY_SPEC].copy()
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.8), width_ratios=[1.35, 1.0])

    ax = axes[0]
    x = np.arange(len(STAGE_ORDER), dtype=float)
    for group_label in GROUP_ORDER:
        group = spec_scores[spec_scores["group_label"] == group_label].copy()
        means = (
            group.groupby("stage_label", dropna=False)["esb2_ds004504"]
            .mean()
            .reindex(STAGE_ORDER)
            .to_numpy(dtype=float)
        )
        ax.plot(x, means, marker="o", lw=2, label=group_label, color=GROUP_COLORS[group_label])
    ax.set_xticks(x, [STAGE_LABELS[s] for s in STAGE_ORDER])
    ax.set_ylabel("Mean ESB-2 score")
    ax.set_xlabel("Photic stage")
    ax.set_title("Frequency profile")
    ax.grid(alpha=0.2)
    ax.legend(frameon=False)

    ax = axes[1]
    positions = np.arange(len(GROUP_ORDER), dtype=float)
    box_data = []
    for group_label in GROUP_ORDER:
        values = pd.to_numeric(spec_prl.loc[spec_prl["group_label"] == group_label, "prl_score"], errors="coerce").dropna().to_numpy(dtype=float)
        box_data.append(values)
    box = ax.boxplot(box_data, positions=positions, widths=0.6, patch_artist=True, showfliers=False)
    for patch, group_label in zip(box["boxes"], GROUP_ORDER):
        patch.set(facecolor=GROUP_COLORS[group_label], alpha=0.45)
    for idx, group_label in enumerate(GROUP_ORDER):
        values = box_data[idx]
        jitter = np.linspace(-0.08, 0.08, num=len(values)) if len(values) else np.array([])
        ax.scatter(np.full(len(values), positions[idx]) + jitter, values, color=GROUP_COLORS[group_label], s=18, alpha=0.8)
    ax.set_xticks(positions, GROUP_ORDER)
    ax.set_ylabel("PRL score (1 - r)")
    ax.set_title("Profile deviation by diagnosis")
    ax.grid(alpha=0.2, axis="y")
    _save_dual(fig, "appendix_figure_prl_profiles", manifest)


def build_recovery_figure(esb_group: pd.DataFrame, manifest: list[dict[str, str]]) -> None:
    sub = esb_group[esb_group["spec_name"] == PRIMARY_SPEC].copy()
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    x = np.arange(len(STAGE_ORDER), dtype=float)
    for group_label in GROUP_ORDER:
        group = sub[sub["group_label"] == group_label].copy().set_index("stage_label").reindex(STAGE_ORDER)
        y = pd.to_numeric(group["h_rest_raw_mean"], errors="coerce").to_numpy(dtype=float)
        ax.plot(x, y, marker="o", lw=2, color=GROUP_COLORS[group_label], label=group_label)
    ax.set_xticks(x, [STAGE_LABELS[s] for s in STAGE_ORDER])
    ax.set_ylabel("Mean recovery distance")
    ax.set_xlabel("Photic stage")
    ax.set_title("Exploratory recovery residual")
    ax.legend(frameon=False)
    ax.grid(alpha=0.2)
    _save_dual(fig, "appendix_figure_recovery_residual", manifest)


def build_comparator_correlation_figure(comparator_subject: pd.DataFrame, comparator_corr: pd.DataFrame, manifest: list[dict[str, str]]) -> None:
    stage = comparator_subject[comparator_subject["stage_label"] == PRIMARY_STAGE].copy()
    fig, axes = plt.subplots(2, 2, figsize=(10.8, 8.2), sharey=True)
    axes = axes.flatten()
    for ax, comp_key in zip(axes, COMPARATOR_ORDER, strict=False):
        sub = stage[stage["comparator_key"] == comp_key].copy()
        if sub.empty:
            ax.axis("off")
            continue
        label = str(sub["comparator_label"].dropna().iloc[0])
        x_all = pd.to_numeric(sub["delta_value"], errors="coerce")
        x_mean = float(np.nanmean(x_all))
        x_std = float(np.nanstd(x_all))
        if not np.isfinite(x_std) or x_std <= 0:
            x_std = 1.0
        for group_label in GROUP_ORDER:
            grp = sub[sub["group_label"] == group_label].copy()
            x_vals = (pd.to_numeric(grp["delta_value"], errors="coerce") - x_mean) / x_std
            ax.scatter(
                x_vals,
                pd.to_numeric(grp["esb2_ds004504"], errors="coerce"),
                color=GROUP_COLORS[group_label],
                s=24,
                alpha=0.8,
                label=group_label,
            )
        corr_all = comparator_corr[
            (comparator_corr["comparator_key"] == comp_key)
            & (comparator_corr["cohort_name"] == "all_subjects")
        ].copy()
        corr_dis = comparator_corr[
            (comparator_corr["comparator_key"] == comp_key)
            & (comparator_corr["cohort_name"] == "disease_only")
        ].copy()
        annotation = []
        if not corr_all.empty:
            row = corr_all.iloc[0]
            annotation.append(f"all rho={float(row['spearman_rho']):.2f}")
        if not corr_dis.empty:
            row = corr_dis.iloc[0]
            annotation.append(f"disease rho={float(row['spearman_rho']):.2f}")
        ax.text(0.03, 0.97, "\n".join(annotation), transform=ax.transAxes, ha="left", va="top", fontsize=9)
        ax.set_title(label, fontsize=10)
        ax.set_xlabel("Standardized rest-subtracted comparator")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("ESB-2 score")
    axes[2].set_ylabel("ESB-2 score")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.01))
    fig.suptitle("Conventional comparator association with ESB-2 at PHOTO 15 Hz", y=1.05, fontsize=13, fontweight="bold")
    fig.tight_layout()
    _save_dual(fig, "figure_4_conventional_comparator_correlations", manifest)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    esb_scores = pd.read_csv(RESULTS_DIR / "esb_subject_scores.csv")
    esb_group = pd.read_csv(RESULTS_DIR / "esb_group_summary.csv")
    prl_scores = pd.read_csv(RESULTS_DIR / "prl_subject_scores.csv")
    comparator_subject = pd.read_csv(RESULTS_DIR / "conventional_comparator_subject_stage.csv")
    comparator_corr = pd.read_csv(RESULTS_DIR / "conventional_comparator_esb2_correlations.csv")

    manifest: list[dict[str, str]] = []
    build_concept_figure(manifest)
    build_esb_trajectory_figure(esb_group, manifest)
    build_capacity_guidance_figure(esb_scores, manifest)
    build_comparator_correlation_figure(comparator_subject, comparator_corr, manifest)
    build_prl_figure(esb_scores, prl_scores, manifest)
    build_recovery_figure(esb_group, manifest)

    (FIGURES_DIR / "figure_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote figures to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
