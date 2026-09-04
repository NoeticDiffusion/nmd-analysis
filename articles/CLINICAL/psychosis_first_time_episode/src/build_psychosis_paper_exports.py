from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[4]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "psychosis_cohort_anchor_20260520"
RESULTS_ROOT = ARTICLE_DIR / "results"
FIGURES_ROOT = ARTICLE_DIR / "figures"

DATASET_LABELS = {
    "ds003944": "ds003944",
    "ds003947": "ds003947",
}
CONTRAST_LABELS = {
    "FEP_unmedicated_vs_Healthy": "FEP unmedicated vs Healthy",
    "FEP_medicated_vs_Healthy": "FEP medicated vs Healthy",
    "FEP_medicated_vs_FEP_unmedicated": "FEP medicated vs FEP unmedicated",
}


@dataclass(frozen=True)
class ExportSpec:
    key: str
    title: str
    analysis_types: tuple[str, ...]
    preferred_metrics: tuple[str, ...]


BLOCK_EXPORTS: tuple[ExportSpec, ...] = (
    ExportSpec(
        key="mnps",
        title="Global MNPS and trajectory dynamics",
        analysis_types=("global_mnps_3d", "trajectory_dynamics"),
        preferred_metrics=("m_mean", "m_median", "m_std", "m_delta_mean_median"),
    ),
    ExportSpec(
        key="stratified",
        title="Stratified 9D MNPS",
        analysis_types=("global_mnps_9d",),
        preferred_metrics=("m_o_mean", "m_o_median", "m_e_mean", "m_e_median", "m_a_mean", "m_a_median"),
    ),
    ExportSpec(
        key="mnj",
        title="Global 3D MNJ",
        analysis_types=("global_mnps_jacobian_3d",),
        preferred_metrics=(
            "spectral_radius_mean",
            "spectral_radius_median",
            "rotation_norm_mean",
            "rotation_norm_median",
            "frobenius_norm_mean",
            "frobenius_norm_median",
            "trace_mean",
            "trace_median",
        ),
    ),
    ExportSpec(
        key="stratified_mnj",
        title="Stratified 9D MNJ",
        analysis_types=("global_mnps_jacobian_9d",),
        preferred_metrics=(
            "mdr_mean",
            "mdr_median",
            "aci_mean",
            "aci_median",
            "spectral_radius_mean",
            "spectral_radius_median",
        ),
    ),
    ExportSpec(
        key="block_mnj",
        title="9x9 block MNJ",
        analysis_types=("global_mnps_jacobian_9d_block_jacobian",),
        preferred_metrics=("block_trace_mean", "block_frobenius_mean", "block_anisotropy_mean"),
    ),
    ExportSpec(
        key="reachability",
        title="Reachability cones",
        analysis_types=("reachability_cones",),
        preferred_metrics=(
            "tube_log_det_mean",
            "tube_log_det_median",
            "tube_log_eig_var_mean",
            "tube_d_eff_mean",
            "cone_log_det_h2_median",
            "cone_d_eff_h2_median",
        ),
    ),
)

ANALYSIS_LABELS = {
    "global_mnps_3d": "Global 3D MNPS",
    "global_mnps_9d": "Stratified 9D MNPS",
    "trajectory_dynamics": "Trajectory dynamics",
    "global_mnps_jacobian_3d": "Global 3D MNJ",
    "global_mnps_jacobian_9d": "Stratified 9D MNJ",
    "global_mnps_jacobian_9d_block_jacobian": "9x9 block MNJ",
    "reachability_cones": "Reachability cones",
    "adaptive_collapse": "Adaptive collapse",
}

FAMILY_ORDER = [
    "location",
    "spread",
    "shape",
    "trajectory",
    "timescale",
    "jacobian",
    "block_jacobian",
    "reachability",
    "other",
]


def _latest_parquet(dataset: str, stem: str) -> Path:
    matches = sorted(ANALYSIS_ROOT.glob(f"{dataset}_{stem}_*.parquet"))
    if not matches:
        raise FileNotFoundError(f"No {stem} parquet found for {dataset} under {ANALYSIS_ROOT}")
    return matches[-1]


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        if np.isfinite(value):
            return float(value)
        return None
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if pd.isna(value):
        return None
    return value


def _sig_tier(row: pd.Series) -> str:
    q = row.get("q_value")
    p = row.get("p_value")
    if pd.notna(q) and float(q) <= 0.05:
        return "q<=0.05"
    if pd.notna(p) and float(p) < 0.05:
        return "p<0.05"
    if pd.notna(p) and float(p) < 0.1:
        return "p<0.1"
    return "ns"


def _sig_star(row: pd.Series) -> str:
    tier = _sig_tier(row)
    if tier == "q<=0.05":
        return "q"
    if tier == "p<0.05":
        return "*"
    if tier == "p<0.1":
        return "~"
    return ""


def _sorted_results(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["abs_effect"] = out["effect_size"].abs()
    out["sig_tier"] = out.apply(_sig_tier, axis=1)
    out["sig_rank"] = out["sig_tier"].map({"q<=0.05": 0, "p<0.05": 1, "p<0.1": 2, "ns": 3}).fillna(9)
    return out.sort_values(
        by=["sig_rank", "q_value", "p_value", "abs_effect", "metric"],
        ascending=[True, True, True, False, True],
        na_position="last",
    ).reset_index(drop=True)


def _choose_preferred_metric(frame: pd.DataFrame, preferred_metrics: Iterable[str]) -> pd.Series:
    ordered = _sorted_results(frame)
    for metric in preferred_metrics:
        match = ordered[ordered["metric"] == metric]
        if not match.empty:
            return match.iloc[0]
    return ordered.iloc[0]


def _choose_m_focus_metric(frame: pd.DataFrame, analysis_type: str) -> Optional[pd.Series]:
    sub = frame[frame["analysis_type"] == analysis_type].copy()
    if sub.empty:
        return None
    if analysis_type == "trajectory_dynamics":
        sub = sub[sub["metric"] == "m_delta_mean_median"].copy()
    else:
        sub = sub[sub["metric"].astype(str).str.contains(r"(?:^m_|_m_|^m$)", regex=True)].copy()
    if sub.empty:
        return None
    return _sorted_results(sub).iloc[0]


def _analysis_label(analysis_type: str) -> str:
    return ANALYSIS_LABELS.get(str(analysis_type), str(analysis_type))


def _metric_family(analysis_type: str, metric: str) -> str:
    analysis_type = str(analysis_type)
    metric = str(metric)
    if analysis_type in {"global_mnps_3d", "global_mnps_9d"}:
        if metric.endswith(("_skewness", "_kurtosis_excess", "_delta_mean_median")):
            return "shape"
        if metric.endswith(("_mean", "_median")):
            return "location"
        if metric.endswith(("_std", "_iqr", "_mad", "_mad_sigma", "_n", "_nan_frac", "_finite_frac")):
            return "spread"
        return "other"
    if analysis_type in {"trajectory_dynamics", "adaptive_collapse"}:
        if metric.endswith(("_tau_sec", "_dt_sec", "_max_lag_sec", "_threshold")):
            return "timescale"
        if any(
            token in metric
            for token in ("speed", "curvature", "corner_", "collapse", "transition", "path_length", "endpoint_dist", "efficiency")
        ):
            return "trajectory"
        if metric.endswith(("_delta_mean_median", "_skewness", "_kurtosis_excess")):
            return "shape"
        if metric.endswith(("_std", "_iqr", "_mad", "_mad_sigma")):
            return "spread"
        return "other"
    if analysis_type in {"global_mnps_jacobian_3d", "global_mnps_jacobian_9d"}:
        return "jacobian"
    if analysis_type == "global_mnps_jacobian_9d_block_jacobian":
        return "block_jacobian"
    if analysis_type == "reachability_cones":
        return "reachability"
    return "other"


def _group_counts(subject_metrics: pd.DataFrame) -> Dict[str, int]:
    cols = [column for column in ("subject_id", "medication_group") if column in subject_metrics.columns]
    deduped = subject_metrics[cols].dropna(subset=["medication_group"]).drop_duplicates()
    counts = deduped.groupby("medication_group", dropna=False).size().to_dict()
    return {str(key): int(value) for key, value in counts.items()}


def _subject_level_counts_by_contrast(subject_metrics: pd.DataFrame, contrast_name: str) -> Dict[str, int]:
    allowed_groups = {
        "FEP_unmedicated_vs_Healthy": ["Healthy", "FEP unmedicated"],
        "FEP_medicated_vs_Healthy": ["Healthy", "FEP medicated"],
        "FEP_medicated_vs_FEP_unmedicated": ["FEP unmedicated", "FEP medicated"],
    }[contrast_name]
    cols = [column for column in ("subject_id", "medication_group") if column in subject_metrics.columns]
    deduped = subject_metrics[cols].dropna(subset=["medication_group"]).drop_duplicates()
    deduped = deduped[deduped["medication_group"].isin(allowed_groups)].copy()
    counts = deduped.groupby("medication_group", dropna=False).size().to_dict()
    return {str(key): int(value) for key, value in counts.items()}


def _row_dict(row: pd.Series) -> Dict[str, Any]:
    return {column: _json_ready(value) for column, value in row.to_dict().items()}


def export_dataset(dataset: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    subject_metrics = pd.read_parquet(_latest_parquet(dataset, "subject_metrics"))
    contrast_results = pd.read_parquet(_latest_parquet(dataset, "contrast_results"))
    dataset_dir = RESULTS_ROOT / dataset
    dataset_dir.mkdir(parents=True, exist_ok=True)

    group_counts = _group_counts(subject_metrics)
    (dataset_dir / "group_counts.json").write_text(json.dumps(group_counts, indent=2), encoding="utf-8")

    summary_rows: List[Dict[str, Any]] = []
    m_focus_rows: List[Dict[str, Any]] = []

    for contrast_name in sorted(contrast_results["contrast_name"].dropna().unique().tolist()):
        contrast_frame = contrast_results[contrast_results["contrast_name"] == contrast_name].copy()
        contrast_subject_counts = _subject_level_counts_by_contrast(subject_metrics, contrast_name)

        for spec in BLOCK_EXPORTS:
            block_frame = contrast_frame[contrast_frame["analysis_type"].isin(spec.analysis_types)].copy()
            if block_frame.empty:
                continue
            block_frame = _sorted_results(block_frame)
            selected = _choose_preferred_metric(block_frame, spec.preferred_metrics)
            csv_path = dataset_dir / f"{spec.key}_{contrast_name}.csv"
            json_path = dataset_dir / f"{spec.key}_{contrast_name}.json"
            block_frame.drop(columns=["abs_effect", "sig_rank"], errors="ignore").to_csv(csv_path, index=False)
            payload = {
                "dataset": dataset,
                "contrast_name": contrast_name,
                "contrast_label": CONTRAST_LABELS.get(contrast_name, contrast_name),
                "block_key": spec.key,
                "block_title": spec.title,
                "analysis_types": list(spec.analysis_types),
                "source_contrast_results": str(_latest_parquet(dataset, "contrast_results")),
                "group_counts_all": group_counts,
                "group_counts_contrast": contrast_subject_counts,
                "n_rows": int(len(block_frame)),
                "n_q05": int(((block_frame["q_value"] <= 0.05) & block_frame["q_value"].notna()).sum()),
                "n_p05": int(((block_frame["p_value"] < 0.05) & block_frame["p_value"].notna()).sum()),
                "n_p10": int(((block_frame["p_value"] < 0.1) & block_frame["p_value"].notna()).sum()),
                "selected_metric": _row_dict(selected),
                "highlights": [_row_dict(row) for _, row in block_frame.head(10).iterrows()],
                "results": [
                    _row_dict(row)
                    for _, row in block_frame.drop(columns=["abs_effect", "sig_rank"], errors="ignore").iterrows()
                ],
            }
            json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            summary_rows.append(
                {
                    "dataset": dataset,
                    "contrast_name": contrast_name,
                    "contrast_label": CONTRAST_LABELS.get(contrast_name, contrast_name),
                    "block_key": spec.key,
                    "block_title": spec.title,
                    "analysis_type": selected["analysis_type"],
                    "metric": selected["metric"],
                    "effect_size": selected["effect_size"],
                    "effect_estimate": selected["effect_estimate"],
                    "p_value": selected["p_value"],
                    "q_value": selected["q_value"],
                    "left_n": selected["left_n"],
                    "right_n": selected["right_n"],
                    "left_mean": selected["left_mean"],
                    "right_mean": selected["right_mean"],
                    "sig_tier": _sig_tier(selected),
                    "export_csv": str(csv_path.relative_to(REPO_ROOT)),
                    "export_json": str(json_path.relative_to(REPO_ROOT)),
                    "group_counts_contrast": json.dumps(contrast_subject_counts, sort_keys=True),
                }
            )

        for block_label, analysis_type in (
            ("mnps_3d", "global_mnps_3d"),
            ("mnps_9d", "global_mnps_9d"),
            ("trajectory", "trajectory_dynamics"),
        ):
            chosen = _choose_m_focus_metric(contrast_frame, analysis_type)
            if chosen is None:
                continue
            m_focus_rows.append(
                {
                    "dataset": dataset,
                    "contrast_name": contrast_name,
                    "contrast_label": CONTRAST_LABELS.get(contrast_name, contrast_name),
                    "block_key": block_label,
                    "analysis_type": analysis_type,
                    "metric": chosen["metric"],
                    "effect_size": chosen["effect_size"],
                    "p_value": chosen["p_value"],
                    "q_value": chosen["q_value"],
                    "sig_tier": _sig_tier(chosen),
                }
            )

    return pd.DataFrame(summary_rows), pd.DataFrame(m_focus_rows)


def build_metric_family_exports(dataset: str) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    contrast_results = pd.read_parquet(_latest_parquet(dataset, "contrast_results"))
    group_counts_all = _group_counts(pd.read_parquet(_latest_parquet(dataset, "subject_metrics")))
    detail = contrast_results.copy()
    detail["dataset"] = dataset
    detail["contrast_label"] = detail["contrast_name"].map(lambda value: CONTRAST_LABELS.get(str(value), str(value)))
    detail["analysis_label"] = detail["analysis_type"].map(_analysis_label)
    detail["metric_family"] = [
        _metric_family(analysis_type, metric)
        for analysis_type, metric in zip(detail["analysis_type"], detail["metric"], strict=True)
    ]
    detail["sig_tier"] = detail.apply(_sig_tier, axis=1)
    detail = _sorted_results(detail)
    detail = detail.drop(columns=["abs_effect", "sig_rank"], errors="ignore")

    summary_rows: List[Dict[str, Any]] = []
    coverage_rows: List[Dict[str, Any]] = []

    for contrast_name in sorted(detail["contrast_name"].dropna().astype(str).unique().tolist()):
        contrast_frame = detail[detail["contrast_name"] == contrast_name].copy()
        subject_metrics = pd.read_parquet(_latest_parquet(dataset, "subject_metrics"))
        group_counts_contrast = _subject_level_counts_by_contrast(subject_metrics, contrast_name)
        for analysis_type in sorted(contrast_frame["analysis_type"].dropna().astype(str).unique().tolist()):
            analysis_frame = contrast_frame[contrast_frame["analysis_type"] == analysis_type].copy()
            families = {}
            for family in FAMILY_ORDER:
                family_frame = analysis_frame[analysis_frame["metric_family"] == family].copy()
                metrics = sorted(family_frame["metric"].dropna().astype(str).unique().tolist())
                if metrics:
                    families[family] = metrics
                    selected = _sorted_results(family_frame).iloc[0]
                    summary_rows.append(
                        {
                            "dataset": dataset,
                            "contrast_name": contrast_name,
                            "contrast_label": CONTRAST_LABELS.get(contrast_name, contrast_name),
                            "analysis_type": analysis_type,
                            "analysis_label": _analysis_label(analysis_type),
                            "metric_family": family,
                            "metric": selected["metric"],
                            "effect_size": selected["effect_size"],
                            "effect_estimate": selected["effect_estimate"],
                            "p_value": selected["p_value"],
                            "q_value": selected["q_value"],
                            "left_n": selected["left_n"],
                            "right_n": selected["right_n"],
                            "left_mean": selected["left_mean"],
                            "right_mean": selected["right_mean"],
                            "sig_tier": _sig_tier(selected),
                            "block_scope": selected.get("block_scope"),
                            "block_space": selected.get("block_space"),
                            "source_group": selected.get("source_group"),
                            "target_group": selected.get("target_group"),
                            "source_dim": selected.get("source_dim"),
                            "target_dim": selected.get("target_dim"),
                            "group_counts_contrast": json.dumps(group_counts_contrast, sort_keys=True),
                        }
                    )
            coverage_rows.append(
                {
                    "dataset": dataset,
                    "contrast_name": contrast_name,
                    "contrast_label": CONTRAST_LABELS.get(contrast_name, contrast_name),
                    "analysis_type": analysis_type,
                    "analysis_label": _analysis_label(analysis_type),
                    "metric_families": families,
                    "group_counts_all": group_counts_all,
                    "group_counts_contrast": group_counts_contrast,
                }
            )

    coverage = {
        "analysis_root": str(ANALYSIS_ROOT),
        "results_root": str(RESULTS_ROOT),
        "datasets": coverage_rows,
    }
    return detail, pd.DataFrame(summary_rows), coverage


def build_metric_family_markdown(summary: pd.DataFrame, coverage: dict[str, Any]) -> str:
    lines = [
        "# Psychosis metric family summary",
        "",
        f"- Analysis root: `{ANALYSIS_ROOT}`",
        "",
    ]
    if not coverage:
        lines.extend(["No metric-family coverage was available.", ""])
        return "\n".join(lines)

    lines.extend(["## Available families", ""])
    for item in coverage.get("datasets", []):
        families = ", ".join(sorted(item["metric_families"].keys())) if item["metric_families"] else "none"
        lines.append(
            f"- `{item['dataset']}` / `{item['contrast_label']}` / `{item['analysis_label']}`: {families}"
        )
    lines.append("")

    if summary.empty:
        lines.extend(["No metric-family summary rows were estimable.", ""])
        return "\n".join(lines)

    lines.extend(["## Strongest metric by family", ""])
    for dataset in ("ds003944", "ds003947"):
        dataset_frame = summary[summary["dataset"] == dataset].copy()
        if dataset_frame.empty:
            continue
        lines.extend([f"### {dataset}", ""])
        for contrast_name in sorted(dataset_frame["contrast_name"].dropna().astype(str).unique().tolist()):
            contrast_frame = dataset_frame[dataset_frame["contrast_name"] == contrast_name].copy()
            lines.extend([f"#### {CONTRAST_LABELS.get(contrast_name, contrast_name)}", ""])
            for _, row in contrast_frame.iterrows():
                lines.append(
                    f"- `{row['analysis_label']}` / `{row['metric_family']}`: "
                    f"`{row['metric']}`, d={float(row['effect_size']):.4f}, "
                    f"p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}"
                )
            lines.append("")
    return "\n".join(lines)


def _draw_selected_effect_heatmap(summary: pd.DataFrame, output_path: Path) -> None:
    blocks = ["mnps", "stratified", "mnj", "stratified_mnj", "block_mnj"]
    labels = {
        "mnps": "3D MNPS",
        "stratified": "9D MNPS",
        "mnj": "3D MNJ",
        "stratified_mnj": "9D MNJ",
        "block_mnj": "Block-MNJ",
    }
    row_labels: List[str] = []
    values: List[List[float]] = []
    annotations: List[List[str]] = []

    for dataset in ("ds003944", "ds003947"):
        dataset_frame = summary[summary["dataset"] == dataset].copy()
        for contrast_name in (
            "FEP_unmedicated_vs_Healthy",
            "FEP_medicated_vs_Healthy",
            "FEP_medicated_vs_FEP_unmedicated",
        ):
            row_labels.append(f"{dataset}\n{CONTRAST_LABELS[contrast_name]}")
            row_vals: List[float] = []
            row_ann: List[str] = []
            for block in blocks:
                match = dataset_frame[
                    (dataset_frame["contrast_name"] == contrast_name) & (dataset_frame["block_key"] == block)
                ]
                if match.empty:
                    row_vals.append(np.nan)
                    row_ann.append("")
                    continue
                row = match.iloc[0]
                row_vals.append(float(row["effect_size"]))
                row_ann.append(f"{row['metric']}\n{_sig_star(row)}")
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
    fig.savefig(output_path, dpi=220)
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
        x_positions: List[float] = []
        x_labels: List[str] = []
        bar_values: List[float] = []
        bar_colors: List[str] = []
        annotations: List[str] = []
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
                annotations.append(f"{series['metric']}\n{_sig_star(series)}")
                tier = str(series["sig_tier"])
                if tier == "q<=0.05":
                    bar_colors.append("#1f77b4")
                elif tier == "p<0.05":
                    bar_colors.append("#ff7f0e")
                elif tier == "p<0.1":
                    bar_colors.append("#d62728")
                else:
                    bar_colors.append("#7f7f7f")
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
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def main() -> None:
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    FIGURES_ROOT.mkdir(parents=True, exist_ok=True)

    summary_frames: List[pd.DataFrame] = []
    m_focus_frames: List[pd.DataFrame] = []
    family_detail_frames: List[pd.DataFrame] = []
    family_summary_frames: List[pd.DataFrame] = []
    family_coverage: Dict[str, Any] = {"analysis_root": str(ANALYSIS_ROOT), "results_root": str(RESULTS_ROOT), "datasets": []}
    for dataset in ("ds003944", "ds003947"):
        summary, m_focus = export_dataset(dataset)
        family_detail, family_summary, coverage = build_metric_family_exports(dataset)
        summary_frames.append(summary)
        m_focus_frames.append(m_focus)
        family_detail_frames.append(family_detail)
        family_summary_frames.append(family_summary)
        family_coverage["datasets"].extend(coverage.get("datasets", []))

    summary_frame = pd.concat(summary_frames, ignore_index=True)
    m_focus_frame = pd.concat(m_focus_frames, ignore_index=True)
    family_detail_frame = pd.concat(family_detail_frames, ignore_index=True)
    family_summary_frame = pd.concat(family_summary_frames, ignore_index=True)
    summary_csv = RESULTS_ROOT / "psychosis_selected_metrics_summary.csv"
    m_focus_csv = RESULTS_ROOT / "psychosis_m_focus_summary.csv"
    family_detail_csv = RESULTS_ROOT / "psychosis_metric_family_detail.csv"
    family_summary_csv = RESULTS_ROOT / "psychosis_metric_family_summary.csv"
    summary_frame.to_csv(summary_csv, index=False)
    m_focus_frame.to_csv(m_focus_csv, index=False)
    family_detail_frame.to_csv(family_detail_csv, index=False)
    family_summary_frame.to_csv(family_summary_csv, index=False)
    (RESULTS_ROOT / "psychosis_metric_family_summary.md").write_text(
        build_metric_family_markdown(family_summary_frame, family_coverage),
        encoding="utf-8",
    )
    (RESULTS_ROOT / "psychosis_metric_family_coverage.json").write_text(
        json.dumps(family_coverage, indent=2),
        encoding="utf-8",
    )

    _draw_selected_effect_heatmap(summary_frame, FIGURES_ROOT / "psychosis_selected_effect_heatmap.png")
    _draw_m_focus_bars(m_focus_frame, FIGURES_ROOT / "psychosis_m_axis_focus.png")

    manifest = {
        "analysis_root": str(ANALYSIS_ROOT),
        "results_root": str(RESULTS_ROOT),
        "figures_root": str(FIGURES_ROOT),
        "summary_csv": str(summary_csv),
        "m_focus_csv": str(m_focus_csv),
        "metric_family_detail_csv": str(family_detail_csv),
        "metric_family_summary_csv": str(family_summary_csv),
        "datasets": ["ds003944", "ds003947"],
    }
    (RESULTS_ROOT / "paper_exports_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
