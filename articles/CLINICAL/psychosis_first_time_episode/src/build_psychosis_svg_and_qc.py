from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


REPO_ROOT = Path(__file__).resolve().parents[4]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
RESULTS_ROOT = ARTICLE_DIR / "results"
FIGURES_ROOT = ARTICLE_DIR / "figures"
MAIN_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "psychosis_cohort_anchor_20260520"
POOLED_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "psychosis_control_vs_fep_20260520"


def _sig_tier(p_value: float | None, q_value: float | None) -> str:
    if q_value is not None and np.isfinite(q_value) and q_value <= 0.05:
        return "q<=0.05"
    if p_value is not None and np.isfinite(p_value) and p_value < 0.05:
        return "p<0.05"
    if p_value is not None and np.isfinite(p_value) and p_value < 0.1:
        return "p<0.1"
    return "ns"


def _sig_star(p_value: float | None, q_value: float | None) -> str:
    tier = _sig_tier(p_value, q_value)
    return {"q<=0.05": "q", "p<0.05": "*", "p<0.1": "~"}.get(tier, "")


def _cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    if left.size < 2 or right.size < 2:
        return float("nan")
    left_var = left.var(ddof=1)
    right_var = right.var(ddof=1)
    pooled_var = ((left.size - 1) * left_var + (right.size - 1) * right_var) / (left.size + right.size - 2)
    if not np.isfinite(pooled_var) or pooled_var <= 0:
        return float("nan")
    return float((right.mean() - left.mean()) / np.sqrt(pooled_var))


def _latest_file(root: Path, dataset: str, stem: str) -> Path:
    matches = sorted(root.glob(f"{dataset}_{stem}_*.parquet"))
    if not matches:
        raise FileNotFoundError(f"No {stem} file for {dataset} under {root}")
    return matches[-1]


def _load_summary(name: str) -> pd.DataFrame:
    return pd.read_csv(RESULTS_ROOT / name)


def _draw_selected_effect_heatmap(summary: pd.DataFrame, output_path: Path) -> None:
    blocks = ["mnps", "stratified", "mnj", "stratified_mnj", "block_mnj"]
    labels = {
        "mnps": "3D MNPS",
        "stratified": "9D MNPS",
        "mnj": "3D MNJ",
        "stratified_mnj": "9D MNJ",
        "block_mnj": "Block-MNJ",
    }
    row_labels: list[str] = []
    values: list[list[float]] = []
    annotations: list[list[str]] = []

    for dataset in ("ds003944", "ds003947"):
        dataset_frame = summary[summary["dataset"] == dataset].copy()
        for contrast_name in (
            "FEP_unmedicated_vs_Healthy",
            "FEP_medicated_vs_Healthy",
            "FEP_medicated_vs_FEP_unmedicated",
        ):
            row_labels.append(f"{dataset}\n{contrast_name.replace('_', ' ')}")
            row_vals: list[float] = []
            row_ann: list[str] = []
            for block in blocks:
                match = dataset_frame[
                    (dataset_frame["contrast_name"] == contrast_name) & (dataset_frame["block_key"] == block)
                ]
                if match.empty:
                    row_vals.append(np.nan)
                    row_ann.append("")
                    continue
                row = match.iloc[0]
                p_value = float(row["p_value"]) if pd.notna(row["p_value"]) else None
                q_value = float(row["q_value"]) if pd.notna(row["q_value"]) else None
                row_vals.append(float(row["effect_size"]))
                row_ann.append(f"{row['metric']}\n{_sig_star(p_value, q_value)}")
            values.append(row_vals)
            annotations.append(row_ann)

    matrix = np.asarray(values, dtype=float)
    fig, ax = plt.subplots(figsize=(12.5, 7.5))
    vmax = np.nanmax(np.abs(matrix)) if np.isfinite(matrix).any() else 1.0
    im = ax.imshow(matrix, cmap="coolwarm", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(len(blocks)))
    ax.set_xticklabels([labels[key] for key in blocks], rotation=20, ha="right")
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels)
    ax.set_title("Selected cohort-anchor effects by block and contrast")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if np.isfinite(matrix[i, j]):
                ax.text(j, i, annotations[i][j], ha="center", va="center", fontsize=8, color="black")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Effect size (Cohen's d)")
    fig.tight_layout()
    fig.savefig(output_path, format="svg")
    plt.close(fig)


def _draw_m_focus_bars(m_focus: pd.DataFrame, output_path: Path) -> None:
    block_order = ["mnps_3d", "mnps_9d", "trajectory"]
    block_labels = {
        "mnps_3d": "3D MNPS",
        "mnps_9d": "9D MNPS",
        "trajectory": "Trajectory m-delta",
    }
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for ax, dataset in zip(axes, ("ds003944", "ds003947"), strict=True):
        dataset_frame = m_focus[m_focus["dataset"] == dataset].copy()
        x_positions: list[float] = []
        x_labels: list[str] = []
        bar_values: list[float] = []
        bar_colors: list[str] = []
        annotations: list[str] = []
        x = 0
        for contrast_name in (
            "FEP_unmedicated_vs_Healthy",
            "FEP_medicated_vs_Healthy",
            "FEP_medicated_vs_FEP_unmedicated",
        ):
            contrast_frame = dataset_frame[dataset_frame["contrast_name"] == contrast_name].copy()
            for block in block_order:
                row = contrast_frame[contrast_frame["block_key"] == block]
                if row.empty:
                    continue
                series = row.iloc[0]
                x_positions.append(x)
                x_labels.append(block_labels[block])
                bar_values.append(float(series["effect_size"]))
                q_value = float(series["q_value"]) if pd.notna(series["q_value"]) else None
                p_value = float(series["p_value"]) if pd.notna(series["p_value"]) else None
                annotations.append(f"{series['metric']}\n{_sig_star(p_value, q_value)}")
                tier = _sig_tier(p_value, q_value)
                bar_colors.append(
                    {
                        "q<=0.05": "#1f77b4",
                        "p<0.05": "#ff7f0e",
                        "p<0.1": "#d62728",
                    }.get(tier, "#7f7f7f")
                )
                x += 1
            x += 1
        ax.bar(x_positions, bar_values, color=bar_colors)
        ax.axhline(0.0, color="black", linewidth=0.8)
        ax.set_xticks(x_positions)
        ax.set_xticklabels(x_labels, rotation=35, ha="right")
        ax.set_title(dataset)
        for xpos, value, label in zip(x_positions, bar_values, annotations, strict=True):
            ax.text(
                xpos,
                value + (0.05 if value >= 0 else -0.08),
                label,
                ha="center",
                va="bottom" if value >= 0 else "top",
                fontsize=8,
            )
    axes[0].set_ylabel("Effect size (Cohen's d)")
    fig.suptitle("m-axis focused cohort-anchor signals")
    fig.tight_layout()
    fig.savefig(output_path, format="svg")
    plt.close(fig)


def _draw_flow_diagram(output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 4.6))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis("off")

    boxes = [
        (0.5, 3.2, 2.2, 1.0, "2026-05-20\nMNDM 2.1 runs"),
        (3.2, 3.2, 2.2, 1.0, "Cohort-anchored\ncleaned tables"),
        (5.9, 3.2, 2.2, 1.0, "Main contrasts\n3-group design"),
        (8.6, 4.3, 2.2, 0.9, "Pooled\nHealthy vs FEP"),
        (8.6, 3.05, 2.2, 0.9, "Baseline\ncomparators"),
        (8.6, 1.8, 2.2, 0.9, "FEP-only phenotypes\nSAPS_Q7 / BPRST19"),
        (11.3, 3.2, 2.2, 1.0, "Paper-facing\nSVG + tables"),
    ]

    for x, y, w, h, label in boxes:
        patch = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            linewidth=1.0,
            edgecolor="#333333",
            facecolor="#f5f7fb",
        )
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=10)

    arrow_style = dict(arrowstyle="->", color="#555555", lw=1.4)
    ax.annotate("", xy=(3.2, 3.7), xytext=(2.7, 3.7), arrowprops=arrow_style)
    ax.annotate("", xy=(5.9, 3.7), xytext=(5.4, 3.7), arrowprops=arrow_style)
    ax.annotate("", xy=(11.3, 3.7), xytext=(8.1, 3.7), arrowprops=arrow_style)
    ax.annotate("", xy=(8.6, 4.75), xytext=(8.1, 3.8), arrowprops=arrow_style)
    ax.annotate("", xy=(8.6, 3.5), xytext=(8.1, 3.72), arrowprops=arrow_style)
    ax.annotate("", xy=(8.6, 2.25), xytext=(8.1, 3.62), arrowprops=arrow_style)
    ax.set_title("Psychosis article workflow")
    fig.tight_layout()
    fig.savefig(output_path, format="svg")
    plt.close(fig)


def _qc_summary(dataset: str) -> pd.DataFrame:
    path = _latest_file(MAIN_ANALYSIS_ROOT, dataset, "subject_metrics")
    frame = pd.read_parquet(path)
    interesting = [
        "global_mnps_3d",
        "global_mnps_9d",
        "global_mnps_jacobian_3d",
        "global_mnps_jacobian_9d",
        "global_mnps_jacobian_9d_block_jacobian",
        "trajectory_dynamics",
    ]
    work = frame[frame["analysis_type"].isin(interesting)].copy()
    rows: list[dict[str, Any]] = []
    for analysis_type, sub in work.groupby("analysis_type", dropna=False):
        finite = pd.to_numeric(sub["finite_ok"], errors="coerce").fillna(False).astype(bool)
        not_testable = pd.to_numeric(sub["not_testable"], errors="coerce").fillna(False).astype(bool)
        validity = pd.to_numeric(sub["validity_limited"], errors="coerce").fillna(False).astype(bool)
        qc_pass = finite & (~not_testable) & (~validity)
        rows.append(
            {
                "dataset": dataset,
                "analysis_type": analysis_type,
                "n_rows": int(len(sub)),
                "n_subjects": int(sub["subject_id"].nunique()),
                "finite_ok_rate": float(finite.mean()),
                "not_testable_rate": float(not_testable.mean()),
                "validity_limited_rate": float(validity.mean()),
                "qc_pass_rate": float(qc_pass.mean()),
            }
        )
    return pd.DataFrame(rows)


def _case_frame(root: Path, dataset: str, analysis_type: str, metric: str) -> pd.DataFrame:
    path = _latest_file(root, dataset, "subject_metrics")
    frame = pd.read_parquet(path, columns=["subject_id", "analysis_type", "metric", "value", "group", "medication_group"])
    sub = frame[(frame["analysis_type"] == analysis_type) & (frame["metric"] == metric)].copy()
    return sub.drop_duplicates(subset=["subject_id"])


def _welch(left: np.ndarray, right: np.ndarray) -> tuple[float, float]:
    t_stat, p_value = stats.ttest_ind(left, right, equal_var=False, nan_policy="omit")
    return float(t_stat), float(p_value)


def _loo_summary(frame: pd.DataFrame, group_column: str, left_label: str, right_label: str) -> dict[str, Any]:
    left_frame = frame[frame[group_column] == left_label].copy()
    right_frame = frame[frame[group_column] == right_label].copy()
    left = pd.to_numeric(left_frame["value"], errors="coerce").dropna().to_numpy(dtype=float)
    right = pd.to_numeric(right_frame["value"], errors="coerce").dropna().to_numpy(dtype=float)
    _, p_value = _welch(left, right)
    effect = _cohens_d(left, right)
    _, mwu_p = stats.mannwhitneyu(left, right, alternative="two-sided")

    loo_effects: list[float] = []
    loo_pvalues: list[float] = []
    for subject_id in frame["subject_id"].dropna().unique().tolist():
        reduced = frame[frame["subject_id"] != subject_id].copy()
        left_r = pd.to_numeric(
            reduced.loc[reduced[group_column] == left_label, "value"],
            errors="coerce",
        ).dropna().to_numpy(dtype=float)
        right_r = pd.to_numeric(
            reduced.loc[reduced[group_column] == right_label, "value"],
            errors="coerce",
        ).dropna().to_numpy(dtype=float)
        if left_r.size < 3 or right_r.size < 3:
            continue
        _, p_r = _welch(left_r, right_r)
        d_r = _cohens_d(left_r, right_r)
        loo_effects.append(d_r)
        loo_pvalues.append(p_r)
    sign_consistency = float(np.mean(np.sign(loo_effects) == np.sign(effect))) if loo_effects else float("nan")
    return {
        "effect_size": effect,
        "welch_p": p_value,
        "mannwhitney_p": float(mwu_p),
        "leave_one_out_d_min": float(np.min(loo_effects)) if loo_effects else np.nan,
        "leave_one_out_d_max": float(np.max(loo_effects)) if loo_effects else np.nan,
        "leave_one_out_p_min": float(np.min(loo_pvalues)) if loo_pvalues else np.nan,
        "leave_one_out_p_max": float(np.max(loo_pvalues)) if loo_pvalues else np.nan,
        "sign_consistency": sign_consistency,
        "left_n": int(left.size),
        "right_n": int(right.size),
    }


def _robustness_cases() -> pd.DataFrame:
    cases = [
        {
            "case": "ds003944 primary",
            "dataset": "ds003944",
            "root": MAIN_ANALYSIS_ROOT,
            "analysis_type": "global_mnps_3d",
            "metric": "m_mean",
            "group_column": "medication_group",
            "left_label": "Healthy",
            "right_label": "FEP medicated",
        },
        {
            "case": "ds003947 primary",
            "dataset": "ds003947",
            "root": MAIN_ANALYSIS_ROOT,
            "analysis_type": "trajectory_dynamics",
            "metric": "m_delta_mean_median",
            "group_column": "medication_group",
            "left_label": "Healthy",
            "right_label": "FEP unmedicated",
        },
        {
            "case": "ds003944 pooled",
            "dataset": "ds003944",
            "root": POOLED_ANALYSIS_ROOT,
            "analysis_type": "global_mnps_9d",
            "metric": "m_e_mean",
            "group_column": "group",
            "left_label": "Control",
            "right_label": "FEP",
        },
    ]
    rows: list[dict[str, Any]] = []
    for case in cases:
        frame = _case_frame(case["root"], case["dataset"], case["analysis_type"], case["metric"])
        summary = _loo_summary(frame, case["group_column"], case["left_label"], case["right_label"])
        rows.append({**case, **summary})
    return pd.DataFrame(rows)


def _draw_qc_robustness(qc_summary: pd.DataFrame, robustness: pd.DataFrame, output_path: Path) -> None:
    analysis_order = [
        "global_mnps_3d",
        "global_mnps_9d",
        "global_mnps_jacobian_3d",
        "global_mnps_jacobian_9d",
        "global_mnps_jacobian_9d_block_jacobian",
        "trajectory_dynamics",
    ]
    labels = {
        "global_mnps_3d": "3D MNPS",
        "global_mnps_9d": "9D MNPS",
        "global_mnps_jacobian_3d": "3D MNJ",
        "global_mnps_jacobian_9d": "9D MNJ",
        "global_mnps_jacobian_9d_block_jacobian": "Block-MNJ",
        "trajectory_dynamics": "Trajectory",
    }
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.3), gridspec_kw={"width_ratios": [1.1, 1.0]})

    qc_pivot = (
        qc_summary.assign(label=qc_summary["analysis_type"].map(labels))
        .pivot(index="label", columns="dataset", values="qc_pass_rate")
        .reindex([labels[a] for a in analysis_order])
    )
    matrix = qc_pivot.to_numpy(dtype=float)
    ax = axes[0]
    im = ax.imshow(matrix, cmap="Greens", vmin=0.8, vmax=1.0, aspect="auto")
    ax.set_xticks(np.arange(len(qc_pivot.columns)))
    ax.set_xticklabels(qc_pivot.columns)
    ax.set_yticks(np.arange(len(qc_pivot.index)))
    ax.set_yticklabels(qc_pivot.index)
    ax.set_title("QC pass rates by analysis family")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if np.isfinite(matrix[i, j]):
                ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", fontsize=9)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("QC pass rate")

    ax = axes[1]
    y = np.arange(len(robustness))
    effects = robustness["effect_size"].to_numpy(dtype=float)
    mins = robustness["leave_one_out_d_min"].to_numpy(dtype=float)
    maxs = robustness["leave_one_out_d_max"].to_numpy(dtype=float)
    ax.hlines(y, mins, maxs, color="#4c78a8", linewidth=3)
    ax.scatter(effects, y, color="#d62728", s=45, zorder=3)
    ax.axvline(0.0, color="black", linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(robustness["case"])
    ax.set_xlabel("Effect size (Cohen's d)")
    ax.set_title("Primary findings: leave-one-out robustness")
    for idx, row in robustness.iterrows():
        ax.text(
            row["leave_one_out_d_max"] + 0.04,
            idx,
            f"MWU p={row['mannwhitney_p']:.3f}\nLOO sign={row['sign_consistency']:.2f}",
            va="center",
            fontsize=8,
        )

    fig.suptitle("Psychosis article QC and robustness checks")
    fig.tight_layout()
    fig.savefig(output_path, format="svg")
    plt.close(fig)


def main() -> None:
    FIGURES_ROOT.mkdir(parents=True, exist_ok=True)
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)

    selected_summary = _load_summary("psychosis_selected_metrics_summary.csv")
    m_focus = _load_summary("psychosis_m_focus_summary.csv")

    _draw_selected_effect_heatmap(selected_summary, FIGURES_ROOT / "psychosis_selected_effect_heatmap.svg")
    _draw_m_focus_bars(m_focus, FIGURES_ROOT / "psychosis_m_axis_focus.svg")
    _draw_flow_diagram(FIGURES_ROOT / "psychosis_analysis_flow.svg")

    qc_frames = [_qc_summary("ds003944"), _qc_summary("ds003947")]
    qc_summary = pd.concat(qc_frames, ignore_index=True)
    robustness = _robustness_cases()
    qc_summary.to_csv(RESULTS_ROOT / "qc_summary_article.csv", index=False)
    robustness.to_csv(RESULTS_ROOT / "robustness_checks_summary.csv", index=False)
    _draw_qc_robustness(qc_summary, robustness, FIGURES_ROOT / "psychosis_qc_robustness.svg")

    manifest = {
        "svg_figures": [
            str(FIGURES_ROOT / "psychosis_selected_effect_heatmap.svg"),
            str(FIGURES_ROOT / "psychosis_m_axis_focus.svg"),
            str(FIGURES_ROOT / "psychosis_analysis_flow.svg"),
            str(FIGURES_ROOT / "psychosis_qc_robustness.svg"),
        ],
        "qc_summary_csv": str(RESULTS_ROOT / "qc_summary_article.csv"),
        "robustness_summary_csv": str(RESULTS_ROOT / "robustness_checks_summary.csv"),
    }
    (RESULTS_ROOT / "qc_robustness_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
