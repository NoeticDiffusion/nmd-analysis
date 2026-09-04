from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath
import textwrap

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from jacobian_9d_support import (
    FORMAL_CONTRAST_DIR,
    PART1_9D_MNPS_DIR,
    PART2_9D_MNPS_DIR,
    PREDICTION_DIR,
    PRIMARY_TIME_BIN,
    RESULT_LEDGER_DIR,
    ROBUSTNESS_DIR,
    REVISED_CORE_METRICS,
    load_metric_long,
    winsorize,
)


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_FIGURE_DIR = ARTICLE_DIR / "figures" / "20260525_jacobian_9d"
DISPLAY_NAMES = {
    "spectral_radius_median": "Spectral radius",
    "anisotropy_abs_eig_median": "Anisotropy abs eig",
    "mdr_median": "MDR",
    "rotational_power_mean": "Rotational power mean",
    "rotational_power_median": "Rotational power median",
    "a_operator_norm_median": "A-operator norm",
    "frobenius_norm_median": "Frobenius norm",
    "rotation_norm_median": "Rotation norm",
}
COHORT_STYLES = {
    "part1": {"label": "part1", "color": "#2563eb"},
    "part2": {"label": "part2", "color": "#dc2626"},
    "pooled": {"label": "pooled", "color": "#111827"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build manuscript-facing figures for the refreshed coma 9D Jacobian article.")
    parser.add_argument("--figure-dir", type=Path, default=DEFAULT_FIGURE_DIR)
    return parser.parse_args()


def load_manifest() -> dict:
    return json.loads((FORMAL_CONTRAST_DIR / "manifest.json").read_text(encoding="utf-8"))


def load_candidate_tables() -> pd.DataFrame:
    rows = []
    for cohort in ("part1", "part2", "pooled"):
        frame = pd.read_csv(FORMAL_CONTRAST_DIR / cohort / "article_candidate_ranking.csv")
        frame["cohort"] = cohort
        rows.append(frame)
    return pd.concat(rows, ignore_index=True)


def load_result_ledger() -> pd.DataFrame:
    return pd.read_csv(RESULT_LEDGER_DIR / "metric_result_ledger.csv")


def load_metric_values(input_dir: Path, *, metric: str) -> pd.DataFrame:
    frame = load_metric_long(input_dir, analysis_type="global_mnps_jacobian_9d", metrics=[metric]).copy()
    frame["outcome_label"] = np.where(frame["cpc_numeric"] == 1.0, "CPC 1", "CPC 5")
    return frame


def build_pooled_values(metric: str) -> pd.DataFrame:
    return pd.concat(
        [load_metric_values(PART1_9D_MNPS_DIR, metric=metric), load_metric_values(PART2_9D_MNPS_DIR, metric=metric)],
        ignore_index=True,
    )


def build_display_values(metric: str, *, apply_winsorization: bool) -> dict[str, pd.DataFrame]:
    values_by_cohort = {
        "part1": load_metric_values(PART1_9D_MNPS_DIR, metric=metric),
        "part2": load_metric_values(PART2_9D_MNPS_DIR, metric=metric),
    }
    values_by_cohort["pooled"] = pd.concat(values_by_cohort.values(), ignore_index=True)
    if not apply_winsorization:
        return values_by_cohort
    pooled_values = values_by_cohort["pooled"]["value"].to_numpy(dtype=float)
    clipped = winsorize(pooled_values, lower_q=0.01, upper_q=0.99)
    if clipped.size == 0:
        return values_by_cohort
    low, high = float(np.min(clipped)), float(np.max(clipped))
    out: dict[str, pd.DataFrame] = {}
    for cohort, frame in values_by_cohort.items():
        clipped_frame = frame.copy()
        clipped_frame["value"] = pd.to_numeric(clipped_frame["value"], errors="coerce").clip(lower=low, upper=high)
        out[cohort] = clipped_frame
    return out


def _repo_relative_path(path_str: str) -> str:
    text = str(path_str or "").replace("\\", "/")
    marker = "NoeticDiffusion/"
    if marker in text:
        return text.split(marker, 1)[1]
    return text


def _wrap_path_lines(path_str: str, *, width: int = 34) -> list[str]:
    text = _repo_relative_path(path_str)
    if not text:
        return [""]
    parts = [part for part in text.split("/") if part]
    lines: list[str] = []
    current = ""
    for part in parts:
        candidate = part if not current else f"{current}/{part}"
        if len(candidate) <= width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = part
        else:
            lines.extend(textwrap.wrap(part, width=width, break_long_words=True, break_on_hyphens=False))
            current = ""
    if current:
        lines.append(current)
    return lines


def _wrap_text_lines(text: str, *, width: int = 34) -> list[str]:
    if not text:
        return [""]
    return textwrap.wrap(text, width=width, break_long_words=True, break_on_hyphens=False)


def write_provenance_overview(manifest: dict, figure_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(12.8, 4.8))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    boxes = [
        (
            0.04,
            0.17,
            0.25,
            0.64,
            "#dbeafe",
            "part1 9D",
            [
                "discovery bundle",
                "0-12 h primary window",
                "MNPS 9D + Jacobian 9D",
            ],
        ),
        (
            0.375,
            0.17,
            0.25,
            0.64,
            "#fee2e2",
            "part2 9D",
            [
                "verification bundle",
                "0-12 h primary window",
                "later 9D-enabled rerun",
            ],
        ),
        (
            0.71,
            0.17,
            0.25,
            0.64,
            "#e5e7eb",
            "pooled 9D",
            [
                f"{manifest.get('subject_overlap_count', 0)} subject overlap",
                f"{manifest.get('run_overlap_count', 0)} run overlap",
                "",
                "audited merge",
                "article-facing synthesis",
            ],
        ),
    ]
    for x, y, w, h, color, title, body_lines in boxes:
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="#374151", linewidth=1.2))
        ax.text(x + 0.015, y + h - 0.055, title, fontsize=12, weight="bold", va="top", color="#111827")
        ax.text(
            x + 0.015,
            y + h - 0.135,
            "\n".join(body_lines),
            fontsize=8.3,
            va="top",
            color="#111827",
            family="monospace",
            linespacing=1.2,
        )
    ax.annotate("", xy=(0.375, 0.49), xytext=(0.29, 0.49), arrowprops=dict(arrowstyle="->", lw=1.5, color="#374151"))
    ax.annotate("", xy=(0.71, 0.49), xytext=(0.625, 0.49), arrowprops=dict(arrowstyle="->", lw=1.5, color="#374151"))
    ax.text(0.332, 0.54, "compare", fontsize=9, color="#374151", ha="center")
    ax.text(0.667, 0.54, "merge after audit", fontsize=9, color="#374151", ha="center")
    ax.set_title("9D Jacobian provenance chain", fontsize=14, weight="bold", pad=12)
    fig.tight_layout()
    fig.savefig(figure_dir / "fig1_9d_provenance_overview.svg", bbox_inches="tight")
    plt.close(fig)


def write_metric_hierarchy_forest(candidates: pd.DataFrame, ledger: pd.DataFrame, figure_dir: Path) -> None:
    ordered_metrics = ledger["metric"].tolist()
    y_positions = np.arange(len(ordered_metrics))[::-1]
    offsets = {"part1": -0.22, "part2": 0.0, "pooled": 0.22}
    fig, ax = plt.subplots(figsize=(10.2, 6.0))
    ax.axvline(0.0, color="#9ca3af", linestyle="--", linewidth=1)
    for cohort in ("part1", "part2", "pooled"):
        sub = candidates[candidates["cohort"] == cohort].copy()
        for idx, metric in enumerate(ordered_metrics):
            row = sub[sub["metric"] == metric]
            if row.empty:
                continue
            d_value = float(row.iloc[0]["cohens_d"])
            p_value = float(row.iloc[0]["mannwhitney_p"])
            ax.scatter(
                d_value,
                y_positions[idx] + offsets[cohort],
                s=52,
                color=COHORT_STYLES[cohort]["color"],
                label=COHORT_STYLES[cohort]["label"] if idx == 0 else None,
                zorder=3,
            )
            ax.text(d_value + 0.015, y_positions[idx] + offsets[cohort], f"p={p_value:.2g}", fontsize=7.5, va="center")

    for boundary in (5.5, 2.5):
        ax.axhline(boundary, color="#d1d5db", linewidth=0.9)

    ax.set_yticks(y_positions)
    ax.set_yticklabels([DISPLAY_NAMES.get(metric, metric) for metric in ordered_metrics])
    ax.set_xlabel("Cohen's d (CPC 1 minus CPC 5)")
    ax.set_title("Revised 9D Jacobian hierarchy across discovery, verification, and pooled synthesis")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(figure_dir / "fig2_9d_revised_forest.svg", bbox_inches="tight")
    plt.close(fig)


def _violin_positions(base: float) -> dict[str, float]:
    return {"CPC 1": base - 0.16, "CPC 5": base + 0.16}


def write_distribution_panel(figure_dir: Path) -> None:
    metrics = ["spectral_radius_median", "anisotropy_abs_eig_median", "frobenius_norm_median", "rotational_power_mean"]
    fig, axes = plt.subplots(1, 4, figsize=(18.0, 4.6))
    for ax, metric in zip(axes, metrics):
        values_by_cohort = build_display_values(metric, apply_winsorization=True)
        for cohort_idx, cohort in enumerate(("part1", "part2", "pooled")):
            values = values_by_cohort[cohort]
            base = cohort_idx + 1
            positions = _violin_positions(base)
            for outcome_label, color in [("CPC 1", "#2563eb"), ("CPC 5", "#dc2626")]:
                sub = values[values["outcome_label"] == outcome_label]["value"].to_numpy(dtype=float)
                if sub.size == 0:
                    continue
                parts = ax.violinplot([sub], positions=[positions[outcome_label]], widths=0.24, showmedians=True)
                for body in parts["bodies"]:
                    body.set_facecolor(color)
                    body.set_alpha(0.30)
                    body.set_edgecolor(color)
                for key in ("cbars", "cmins", "cmaxes", "cmedians"):
                    if key in parts:
                        parts[key].set_edgecolor(color)
                        parts[key].set_linewidth(1.0)
        ax.set_xticks([1, 2, 3])
        ax.set_xticklabels(["part1", "part2", "pooled"])
        ax.set_title(DISPLAY_NAMES.get(metric, metric))
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xlabel("Cohort")
        ax.set_ylabel("Patient-level value")
    fig.suptitle("Replicated leads, restored Frobenius comparator, and a pooled-promoted rotational metric (winsorized 1st-99th pct)")
    fig.tight_layout()
    fig.savefig(figure_dir / "fig3_9d_distribution_panel.svg", bbox_inches="tight")
    plt.close(fig)


def write_top_metric_violins(figure_dir: Path) -> None:
    metrics = ["spectral_radius_median", "anisotropy_abs_eig_median", "frobenius_norm_median"]
    fig, axes = plt.subplots(1, 3, figsize=(15.8, 4.6))
    for ax, metric in zip(axes, metrics):
        values_by_cohort = build_display_values(metric, apply_winsorization=True)
        for cohort_idx, cohort in enumerate(("part1", "part2", "pooled")):
            values = values_by_cohort[cohort]
            base = cohort_idx + 1
            positions = _violin_positions(base)
            for outcome_label, color in [("CPC 1", "#2563eb"), ("CPC 5", "#dc2626")]:
                sub = values[values["outcome_label"] == outcome_label]["value"].to_numpy(dtype=float)
                if sub.size == 0:
                    continue
                parts = ax.violinplot([sub], positions=[positions[outcome_label]], widths=0.24, showmedians=True)
                for body in parts["bodies"]:
                    body.set_facecolor(color)
                    body.set_alpha(0.30)
                    body.set_edgecolor(color)
                for key in ("cbars", "cmins", "cmaxes", "cmedians"):
                    if key in parts:
                        parts[key].set_edgecolor(color)
                        parts[key].set_linewidth(1.0)
        ax.set_xticks([1, 2, 3])
        ax.set_xticklabels(["part1", "part2", "pooled"])
        ax.set_title(DISPLAY_NAMES.get(metric, metric))
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xlabel("Cohort")
        ax.set_ylabel("Patient-level value")
    fig.suptitle("Top 9D Jacobian metrics and restored Frobenius comparator in CPC 1 vs CPC 5 (winsorized 1st-99th pct)")
    fig.tight_layout()
    fig.savefig(figure_dir / "fig3_9d_top_metric_violins.svg", bbox_inches="tight")
    plt.close(fig)


def write_robustness_heatmap(ledger: pd.DataFrame, figure_dir: Path) -> None:
    subset = pd.read_csv(ROBUSTNESS_DIR / "subset_metric_contrasts.csv")
    winsorized = pd.read_csv(ROBUSTNESS_DIR / "winsorization_sensitivity.csv")
    metric_order = ledger["metric"].tolist()
    matrix = pd.DataFrame(index=metric_order, columns=["full", "shockable_only", "nonshockable_only", "winsorized"], dtype=float)
    for subset_name in ("full", "shockable_only", "nonshockable_only"):
        sub = subset[subset["subset"] == subset_name].copy().set_index("metric")
        matrix.loc[sub.index, subset_name] = sub["cohens_d"]
    wins = winsorized.set_index("metric")
    matrix.loc[wins.index, "winsorized"] = wins["winsorized_d"]

    fig, ax = plt.subplots(figsize=(8.8, 5.8))
    im = ax.imshow(matrix.to_numpy(dtype=float), cmap="coolwarm_r", vmin=-0.8, vmax=0.8, aspect="auto")
    ax.set_xticks(np.arange(matrix.shape[1]))
    ax.set_xticklabels(["full", "shock", "non-shock", "winsorized"])
    ax.set_yticks(np.arange(matrix.shape[0]))
    ax.set_yticklabels([DISPLAY_NAMES.get(metric, metric) for metric in metric_order])
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix.iloc[i, j]
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=8, color="#111827")
    ax.set_title("Robustness map for revised and legacy 9D Jacobian metrics")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Cohen's d")
    fig.tight_layout()
    fig.savefig(figure_dir / "fig4_9d_robustness_heatmap.svg", bbox_inches="tight")
    plt.close(fig)


def write_prediction_panel(figure_dir: Path) -> None:
    repeated = pd.read_csv(PREDICTION_DIR / "incremental_validity_summary.csv")
    loso = pd.read_csv(PREDICTION_DIR / "incremental_validity_site_summary.csv")
    wanted = [
        "clinical_plus_eeg",
        "jacobian9d_only",
        "reachability_only",
        "jacobian3d_only",
        "clinical_plus_eeg_plus_jacobian9d",
        "clinical_plus_eeg_plus_reachability",
        "clinical_plus_eeg_plus_reachability_plus_jacobian9d",
    ]
    label_map = {
        "clinical_plus_eeg": "Clinical+qEEG",
        "jacobian9d_only": "9D only",
        "reachability_only": "Reach only",
        "jacobian3d_only": "3D Jacobian only",
        "clinical_plus_eeg_plus_jacobian9d": "Clinical+qEEG+9D",
        "clinical_plus_eeg_plus_reachability": "Clinical+qEEG+Reach",
        "clinical_plus_eeg_plus_reachability_plus_jacobian9d": "Clinical+qEEG+Reach+9D",
    }
    repeated = repeated[repeated["model"].isin(wanted)].copy()
    loso = loso[loso["model"].isin(wanted)].copy()
    repeated["display"] = repeated["model"].map(label_map)
    loso["display"] = loso["model"].map(label_map)
    repeated = repeated.set_index("model").loc[wanted].reset_index()
    loso = loso.set_index("model").loc[wanted].reset_index()
    y_pos = np.arange(len(wanted))[::-1]

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.8), sharey=True)
    axes[0].errorbar(
        repeated["roc_auc_mean"],
        y_pos,
        xerr=[
            repeated["roc_auc_mean"] - repeated["roc_auc_ci_low"],
            repeated["roc_auc_ci_high"] - repeated["roc_auc_mean"],
        ],
        fmt="o",
        color="#111827",
        ecolor="#6b7280",
        capsize=3,
    )
    axes[0].set_title("Repeated CV AUROC")
    axes[1].errorbar(
        loso["roc_auc_mean"],
        y_pos,
        xerr=loso["roc_auc_sd"],
        fmt="o",
        color="#111827",
        ecolor="#6b7280",
        capsize=3,
    )
    axes[1].set_title("Leave-One-Site-Out AUROC")
    for ax in axes:
        ax.set_yticks(y_pos)
        ax.set_yticklabels(repeated["display"])
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xlabel("AUROC")
        ax.set_xlim(0.5, 0.85)
    fig.suptitle("Prediction ladder for revised 9D, reachability, and combined models")
    fig.tight_layout()
    fig.savefig(figure_dir / "fig5_9d_prediction_panel.svg", bbox_inches="tight")
    plt.close(fig)


def write_correlation_heatmap(figure_dir: Path) -> None:
    corr = pd.read_csv(PREDICTION_DIR / "joint_signal_correlation_matrix.csv", index_col=0)
    fig, ax = plt.subplots(figsize=(8.8, 7.2))
    im = ax.imshow(corr.to_numpy(dtype=float), cmap="coolwarm", vmin=-1.0, vmax=1.0)
    ax.set_xticks(np.arange(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=90, fontsize=8)
    ax.set_yticks(np.arange(len(corr.index)))
    ax.set_yticklabels(corr.index, fontsize=8)
    ax.set_title("Joint signal correlation map")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Spearman rho")
    fig.tight_layout()
    fig.savefig(figure_dir / "fig6_joint_signal_correlation_heatmap.svg", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    args.figure_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    candidates = load_candidate_tables()
    ledger = load_result_ledger()
    write_provenance_overview(manifest, args.figure_dir)
    write_metric_hierarchy_forest(candidates, ledger, args.figure_dir)
    write_distribution_panel(args.figure_dir)
    write_top_metric_violins(args.figure_dir)
    write_robustness_heatmap(ledger, args.figure_dir)
    write_prediction_panel(args.figure_dir)
    write_correlation_heatmap(args.figure_dir)
    print(f"Wrote 9D Jacobian figures to {args.figure_dir}")


if __name__ == "__main__":
    main()
