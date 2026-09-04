from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List

import numpy as np
import pandas as pd
from scipy import stats


DATASET = "ds003478"
CONTRAST_NAME = "BDI_0_13_vs_BDI_20_63"
REPO_ROOT = Path(__file__).resolve().parents[4]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "depression_ds003478_20260521"
FALLBACK_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis"
DEFAULT_RESULTS_ROOT = ARTICLE_DIR / "results"
PARTICIPANTS_PATH = ARTICLE_DIR / "metadata" / "participants.tsv"

BDI_BAND_LABELS = ["BDI 0-13", "BDI 14-19", "BDI 20-63"]
CORRELATION_COHORTS = {
    "All_valid": None,
    "LowHigh_only": {"BDI 0-13", "BDI 20-63"},
    "High_BDI_only": {"BDI 20-63"},
}
CONTEXT_COLUMNS = [
    "block_scope",
    "block_space",
    "source_group",
    "target_group",
    "source_dim",
    "target_dim",
]


@dataclass(frozen=True)
class ExportSpec:
    key: str
    title: str
    analysis_types: tuple[str, ...]
    preferred_metrics: tuple[str, ...]


BLOCK_EXPORTS: tuple[ExportSpec, ...] = (
    ExportSpec(
        key="mnps_3d",
        title="Global 3D MNPS",
        analysis_types=("global_mnps_3d",),
        preferred_metrics=("d_median", "d_mean", "d_std", "m_std", "m_mean"),
    ),
    ExportSpec(
        key="mnps_9d",
        title="Global 9D MNPS",
        analysis_types=("global_mnps_9d",),
        preferred_metrics=("d_s_mean", "e_m_std", "d_l_std", "d_s_median", "m_a_mean"),
    ),
    ExportSpec(
        key="mnj_3d",
        title="Global 3D MNJ",
        analysis_types=("global_mnps_jacobian_3d",),
        preferred_metrics=("spectral_radius_median", "spectral_radius_mean", "rotation_norm_median", "trace_median"),
    ),
    ExportSpec(
        key="mnj_9d",
        title="Global 9D MNJ",
        analysis_types=("global_mnps_jacobian_9d",),
        preferred_metrics=(
            "rotational_power_mean",
            "rotational_power_median",
            "frobenius_norm_median",
            "rotation_norm_median",
        ),
    ),
    ExportSpec(
        key="block_mnj",
        title="9x9 block MNJ",
        analysis_types=("global_mnps_jacobian_9d_block_jacobian",),
        preferred_metrics=("block_anisotropy_mean", "block_trace_mean", "block_frobenius_mean"),
    ),
    ExportSpec(
        key="reachability",
        title="Reachability cones",
        analysis_types=("reachability_cones",),
        preferred_metrics=(
            "tube_log_eig_var_mean",
            "tube_log_eig_var_median",
            "cone_log_eig_var_h3_median",
            "cone_log_eig_var_h4_median",
            "tube_log_det_split_half_a_median",
            "cone_log_det_h2_median",
        ),
    ),
    ExportSpec(
        key="emmi",
        title="Tier-2 EMMI",
        analysis_types=("tier2_emmi",),
        preferred_metrics=("mv_median", "mv_abs_median", "mv_over_speed_median", "speed_median"),
    ),
    ExportSpec(
        key="distribution",
        title="Distribution summary",
        analysis_types=("dist_summary",),
        preferred_metrics=("e_m_mad_sigma", "e_m_mad", "e_m_iqr", "d_skewness", "d_kurtosis_excess"),
    ),
)

ANALYSIS_LABELS = {
    "global_mnps_3d": "Global 3D MNPS",
    "global_mnps_9d": "Global 9D MNPS",
    "global_mnps_jacobian_3d": "Global 3D MNJ",
    "global_mnps_jacobian_9d": "Global 9D MNJ",
    "global_mnps_jacobian_9d_block_jacobian": "9x9 block MNJ",
    "reachability_cones": "Reachability cones",
    "tier2_emmi": "Tier-2 EMMI",
    "dist_summary": "Distribution summary",
    "tau_summary": "Tau summary",
    "tier2_jacobian": "Tier-2 Jacobian",
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build paper-facing ds003478 depression exports.")
    parser.add_argument("--analysis-root", type=Path, default=None)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    return parser.parse_args()


def _analysis_roots(preferred: Path | None) -> list[Path]:
    ordered: list[Path] = []
    for root in (preferred, DEFAULT_ANALYSIS_ROOT, FALLBACK_ANALYSIS_ROOT):
        if root is None:
            continue
        if root not in ordered:
            ordered.append(root)
    return ordered


def _latest_parquet(roots: Iterable[Path], stem: str) -> Path:
    for root in roots:
        matches = sorted(root.glob(f"{DATASET}_{stem}_*.parquet"))
        if matches:
            return matches[-1]
    searched = ", ".join(str(root) for root in roots)
    raise FileNotFoundError(f"No {stem} parquet found for {DATASET} under: {searched}")


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        if np.isfinite(value):
            return float(value)
        return None
    if pd.isna(value):
        return None
    return value


def _row_dict(row: pd.Series) -> dict[str, Any]:
    return {column: _json_ready(value) for column, value in row.to_dict().items()}


def _bh_fdr(values: pd.Series) -> pd.Series:
    arr = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    valid = np.isfinite(arr)
    if not valid.any():
        return pd.Series(out, index=values.index, dtype=float)
    p = arr[valid]
    order = np.argsort(p)
    ranked = p[order]
    n = ranked.size
    adjusted = ranked * n / np.arange(1, n + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    out_valid = np.empty_like(adjusted)
    out_valid[order] = adjusted
    out[valid] = out_valid
    return pd.Series(out, index=values.index, dtype=float)


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


def _sorted_results(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["abs_effect"] = pd.to_numeric(out["effect_size"], errors="coerce").abs()
    out["sig_rank"] = out.apply(_sig_tier, axis=1).map({"q<=0.05": 0, "p<0.05": 1, "p<0.1": 2, "ns": 3}).fillna(9)
    return out.sort_values(
        by=["sig_rank", "q_value", "p_value", "abs_effect", "metric"],
        ascending=[True, True, True, False, True],
        na_position="last",
    ).reset_index(drop=True)


def _sorted_correlations(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["abs_spearman_rho"] = pd.to_numeric(out["spearman_rho"], errors="coerce").abs()
    out["sig_rank"] = out.apply(_sig_tier, axis=1).map({"q<=0.05": 0, "p<0.05": 1, "p<0.1": 2, "ns": 3}).fillna(9)
    return out.sort_values(
        by=["sig_rank", "q_value", "p_value", "abs_spearman_rho", "metric"],
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


def _choose_preferred_correlation(frame: pd.DataFrame, preferred_metrics: Iterable[str]) -> pd.Series:
    ordered = _sorted_correlations(frame)
    for metric in preferred_metrics:
        match = ordered[ordered["metric"] == metric]
        if not match.empty:
            return match.iloc[0]
    return ordered.iloc[0]


def _analysis_label(analysis_type: str) -> str:
    return ANALYSIS_LABELS.get(str(analysis_type), str(analysis_type))


def _metric_family(analysis_type: str, metric: str) -> str:
    analysis_type = str(analysis_type)
    metric = str(metric)
    if analysis_type in {"global_mnps_3d", "global_mnps_9d", "dist_summary"}:
        if metric.endswith(("_skewness", "_kurtosis_excess", "_delta_mean_median")):
            return "shape"
        if metric.endswith(("_mean", "_median")):
            return "location"
        if metric.endswith(("_std", "_iqr", "_mad", "_mad_sigma", "_n", "_nan_frac", "_finite_frac")):
            return "spread"
        return "other"
    if analysis_type == "tier2_emmi":
        if "speed" in metric or metric.startswith(("mv_", "emmi_")):
            return "trajectory"
        return "other"
    if analysis_type == "tau_summary":
        return "timescale"
    if analysis_type in {"global_mnps_jacobian_3d", "global_mnps_jacobian_9d", "tier2_jacobian"}:
        return "jacobian"
    if analysis_type == "global_mnps_jacobian_9d_block_jacobian":
        return "block_jacobian"
    if analysis_type == "reachability_cones":
        return "reachability"
    return "other"


def load_participants() -> pd.DataFrame:
    phenos = pd.read_csv(PARTICIPANTS_PATH, sep="\t")
    phenos["age"] = pd.to_numeric(phenos["age"], errors="coerce")
    phenos["BDI"] = pd.to_numeric(phenos["BDI"], errors="coerce")
    phenos["female"] = pd.to_numeric(phenos["sex"], errors="coerce").eq(1)
    phenos["bdi_band"] = pd.cut(
        phenos["BDI"],
        bins=[-0.1, 13, 19, 63],
        labels=BDI_BAND_LABELS,
        include_lowest=True,
    )
    phenos["bdi_band"] = phenos["bdi_band"].astype(object)
    return phenos


def build_demography_summary(phenos: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    valid = phenos[phenos["BDI"].notna()].copy()
    for label in BDI_BAND_LABELS:
        sub = valid[valid["bdi_band"] == label].copy()
        rows.append(
            {
                "dataset": DATASET,
                "bdi_band": label,
                "n": int(len(sub)),
                "age_mean": float(sub["age"].mean()),
                "age_sd": float(sub["age"].std()),
                "female_n": int(sub["female"].sum()),
                "female_pct": float(sub["female"].mean() * 100.0),
                "bdi_mean": float(sub["BDI"].mean()),
                "bdi_median": float(sub["BDI"].median()),
            }
        )
    return pd.DataFrame(rows)


def build_selected_contrast_exports(contrast_results: pd.DataFrame, results_root: Path) -> pd.DataFrame:
    dataset_dir = results_root / DATASET
    dataset_dir.mkdir(parents=True, exist_ok=True)

    contrast_frame = contrast_results[contrast_results["contrast_name"] == CONTRAST_NAME].copy()
    summary_rows: list[dict[str, object]] = []
    for spec in BLOCK_EXPORTS:
        block_frame = contrast_frame[contrast_frame["analysis_type"].isin(spec.analysis_types)].copy()
        if block_frame.empty:
            continue
        ordered = _sorted_results(block_frame)
        selected = _choose_preferred_metric(ordered, spec.preferred_metrics)
        csv_path = dataset_dir / f"{spec.key}_{CONTRAST_NAME}.csv"
        json_path = dataset_dir / f"{spec.key}_{CONTRAST_NAME}.json"
        ordered.drop(columns=["abs_effect", "sig_rank"], errors="ignore").to_csv(csv_path, index=False)
        payload = {
            "dataset": DATASET,
            "contrast_name": CONTRAST_NAME,
            "block_key": spec.key,
            "block_title": spec.title,
            "analysis_types": list(spec.analysis_types),
            "n_rows": int(len(ordered)),
            "selected_metric": _row_dict(selected),
            "highlights": [
                _row_dict(row)
                for _, row in ordered.drop(columns=["abs_effect", "sig_rank"], errors="ignore").head(12).iterrows()
            ],
        }
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        summary_rows.append(
            {
                "dataset": DATASET,
                "contrast_name": CONTRAST_NAME,
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
                "block_scope": selected.get("block_scope"),
                "block_space": selected.get("block_space"),
                "source_group": selected.get("source_group"),
                "target_group": selected.get("target_group"),
                "source_dim": selected.get("source_dim"),
                "target_dim": selected.get("target_dim"),
                "export_csv": str(csv_path.relative_to(REPO_ROOT)),
                "export_json": str(json_path.relative_to(REPO_ROOT)),
            }
        )
    return pd.DataFrame(summary_rows)


def build_metric_family_exports(contrast_results: pd.DataFrame, results_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    contrast_frame = contrast_results[contrast_results["contrast_name"] == CONTRAST_NAME].copy()
    if contrast_frame.empty:
        return pd.DataFrame(), pd.DataFrame(), {}

    detail = contrast_frame.copy()
    detail["analysis_label"] = detail["analysis_type"].map(_analysis_label)
    detail["metric_family"] = [
        _metric_family(analysis_type, metric)
        for analysis_type, metric in zip(detail["analysis_type"], detail["metric"], strict=True)
    ]
    detail["sig_tier"] = detail.apply(_sig_tier, axis=1)
    detail = _sorted_results(detail)
    detail = detail.drop(columns=["abs_effect", "sig_rank"], errors="ignore")

    summary_rows: list[dict[str, object]] = []
    for analysis_type in sorted(detail["analysis_type"].dropna().unique().tolist()):
        analysis_frame = detail[detail["analysis_type"] == analysis_type].copy()
        for family in FAMILY_ORDER:
            family_frame = analysis_frame[analysis_frame["metric_family"] == family].copy()
            if family_frame.empty:
                continue
            selected = _sorted_results(family_frame).iloc[0]
            summary_rows.append(
                {
                    "dataset": DATASET,
                    "contrast_name": CONTRAST_NAME,
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
                }
            )

    coverage_rows = []
    for analysis_type in sorted(detail["analysis_type"].dropna().unique().tolist()):
        analysis_frame = detail[detail["analysis_type"] == analysis_type].copy()
        families = {}
        for family in FAMILY_ORDER:
            metrics = sorted(analysis_frame.loc[analysis_frame["metric_family"] == family, "metric"].dropna().astype(str).unique().tolist())
            if metrics:
                families[family] = metrics
        coverage_rows.append(
            {
                "analysis_type": analysis_type,
                "analysis_label": _analysis_label(analysis_type),
                "metric_families": families,
            }
        )

    coverage = {
        "dataset": DATASET,
        "contrast_name": CONTRAST_NAME,
        "analysis_types": coverage_rows,
    }
    return detail, pd.DataFrame(summary_rows), coverage


def _prepare_correlation_frame(subject_metrics: pd.DataFrame, phenos: pd.DataFrame) -> pd.DataFrame:
    merged = subject_metrics.merge(
        phenos[["participant_id", "BDI", "bdi_band", "age", "female"]],
        left_on="subject_id",
        right_on="participant_id",
        how="left",
    ).drop(columns=["participant_id"], errors="ignore")
    keep = merged[pd.to_numeric(merged["value"], errors="coerce").notna()].copy()
    keep["value"] = pd.to_numeric(keep["value"], errors="coerce")
    keep["BDI"] = pd.to_numeric(keep["BDI"], errors="coerce")
    keep = keep[pd.notna(keep["BDI"])].copy()
    dedupe_cols = ["subject_id", "analysis_type", "metric"] + [column for column in CONTEXT_COLUMNS if column in keep.columns]
    return (
        keep.groupby(dedupe_cols + ["bdi_band"], dropna=False, as_index=False)
        .agg(value=("value", "mean"), BDI=("BDI", "first"))
        .reset_index(drop=True)
    )


def build_bdi_correlations(subject_metrics: pd.DataFrame, phenos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    prepared = _prepare_correlation_frame(subject_metrics, phenos)
    rows: list[dict[str, object]] = []
    group_cols = ["analysis_type", "metric"] + [column for column in CONTEXT_COLUMNS if column in prepared.columns]

    for cohort_key, allowed_bands in CORRELATION_COHORTS.items():
        cohort = prepared.copy()
        if allowed_bands is not None:
            cohort = cohort[cohort["bdi_band"].isin(allowed_bands)].copy()
        if cohort.empty:
            continue
        for keys, group_frame in cohort.groupby(group_cols, dropna=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            row = dict(zip(group_cols, keys))
            work = group_frame[["subject_id", "value", "BDI"]].dropna().copy().drop_duplicates(subset=["subject_id"])
            if len(work) < 6 or work["value"].nunique() < 2 or work["BDI"].nunique() < 2:
                continue
            spearman_rho, spearman_p = stats.spearmanr(work["value"], work["BDI"])
            pearson_r, pearson_p = stats.pearsonr(work["value"], work["BDI"])
            row.update(
                {
                    "dataset": DATASET,
                    "cohort_key": cohort_key,
                    "n_subjects": int(len(work)),
                    "bdi_mean": float(work["BDI"].mean()),
                    "bdi_median": float(work["BDI"].median()),
                    "spearman_rho": float(spearman_rho) if np.isfinite(spearman_rho) else np.nan,
                    "p_value": float(spearman_p) if np.isfinite(spearman_p) else np.nan,
                    "pearson_r": float(pearson_r) if np.isfinite(pearson_r) else np.nan,
                    "pearson_p": float(pearson_p) if np.isfinite(pearson_p) else np.nan,
                }
            )
            rows.append(row)

    detail = pd.DataFrame(rows)
    if detail.empty:
        return detail, pd.DataFrame()
    detail["q_value"] = detail.groupby(["cohort_key", "analysis_type"], dropna=False)["p_value"].transform(_bh_fdr)
    detail["sig_tier"] = detail.apply(_sig_tier, axis=1)

    summary_rows: list[dict[str, object]] = []
    for cohort_key in CORRELATION_COHORTS:
        cohort_frame = detail[detail["cohort_key"] == cohort_key].copy()
        if cohort_frame.empty:
            continue
        for spec in BLOCK_EXPORTS:
            block_frame = cohort_frame[cohort_frame["analysis_type"].isin(spec.analysis_types)].copy()
            if block_frame.empty:
                continue
            selected = _choose_preferred_correlation(block_frame, spec.preferred_metrics)
            summary_rows.append(
                {
                    "dataset": DATASET,
                    "cohort_key": cohort_key,
                    "block_key": spec.key,
                    "block_title": spec.title,
                    "analysis_type": selected["analysis_type"],
                    "metric": selected["metric"],
                    "n_subjects": selected["n_subjects"],
                    "spearman_rho": selected["spearman_rho"],
                    "pearson_r": selected["pearson_r"],
                    "p_value": selected["p_value"],
                    "q_value": selected["q_value"],
                    "sig_tier": _sig_tier(selected),
                    "block_scope": selected.get("block_scope"),
                    "block_space": selected.get("block_space"),
                    "source_group": selected.get("source_group"),
                    "target_group": selected.get("target_group"),
                    "source_dim": selected.get("source_dim"),
                    "target_dim": selected.get("target_dim"),
                }
            )
    return detail, pd.DataFrame(summary_rows)


def build_bdi_markdown(summary: pd.DataFrame) -> str:
    lines = [
        "# BDI correlation summary",
        "",
        f"- Dataset: `{DATASET}`",
        "",
    ]
    if summary.empty:
        lines.extend(["No BDI correlations were estimable.", ""])
        return "\n".join(lines)

    for cohort_key in ("All_valid", "LowHigh_only", "High_BDI_only"):
        cohort = summary[summary["cohort_key"] == cohort_key].copy()
        if cohort.empty:
            continue
        lines.extend([f"## {cohort_key}", ""])
        for _, row in cohort.iterrows():
            extra = []
            if pd.notna(row.get("source_group")) or pd.notna(row.get("target_group")):
                extra.append(f"block={row.get('source_group')}->{row.get('target_group')}")
            if pd.notna(row.get("block_space")):
                extra.append(f"space={row.get('block_space')}")
            suffix = f" ({', '.join(extra)})" if extra else ""
            lines.append(
                f"- `{row['block_title']}` / `{row['metric']}`{suffix}: "
                f"rho={float(row['spearman_rho']):.4f}, p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}"
            )
        lines.append("")
    return "\n".join(lines)


def build_metric_family_markdown(summary: pd.DataFrame, coverage: dict[str, Any]) -> str:
    lines = [
        "# Metric family summary",
        "",
        f"- Dataset: `{DATASET}`",
        f"- Contrast: `{CONTRAST_NAME}`",
        "",
        "## Available analysis families",
        "",
    ]
    if not coverage:
        lines.extend(["No metric-family coverage was available.", ""])
        return "\n".join(lines)

    for item in coverage.get("analysis_types", []):
        lines.append(f"- `{item['analysis_label']}`: {', '.join(sorted(item['metric_families'].keys()))}")
    lines.append("")

    if summary.empty:
        lines.extend(["No metric-family summary rows were estimable.", ""])
        return "\n".join(lines)

    lines.extend(["## Strongest metric by family", ""])
    for analysis_type in sorted(summary["analysis_type"].dropna().unique().tolist()):
        sub = summary[summary["analysis_type"] == analysis_type].copy()
        if sub.empty:
            continue
        lines.extend([f"### {_analysis_label(analysis_type)}", ""])
        for _, row in sub.iterrows():
            extra = []
            if pd.notna(row.get("source_group")) or pd.notna(row.get("target_group")):
                extra.append(f"block={row.get('source_group')}->{row.get('target_group')}")
            suffix = f" ({', '.join(extra)})" if extra else ""
            lines.append(
                f"- `{row['metric_family']}`: `{row['metric']}`{suffix}, "
                f"d={float(row['effect_size']):.4f}, p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    analysis_roots = _analysis_roots(args.analysis_root)
    results_root = args.results_root
    results_root.mkdir(parents=True, exist_ok=True)

    phenos = load_participants()
    subject_metrics_path = _latest_parquet(analysis_roots, "subject_metrics")
    contrast_results_path = _latest_parquet(analysis_roots, "contrast_results")
    subject_metrics = pd.read_parquet(subject_metrics_path)
    contrast_results = pd.read_parquet(contrast_results_path)

    demography = build_demography_summary(phenos)
    selected_metrics = build_selected_contrast_exports(contrast_results, results_root)
    metric_family_detail, metric_family_summary, metric_family_coverage = build_metric_family_exports(contrast_results, results_root)
    bdi_detail, bdi_summary = build_bdi_correlations(subject_metrics, phenos)

    demography.to_csv(results_root / "demography_summary.csv", index=False)
    selected_metrics.to_csv(results_root / "selected_metrics_summary.csv", index=False)
    if not metric_family_detail.empty:
        metric_family_detail.to_csv(results_root / "metric_family_detail.csv", index=False)
    if not metric_family_summary.empty:
        metric_family_summary.to_csv(results_root / "metric_family_summary.csv", index=False)
    (results_root / "metric_family_summary.md").write_text(
        build_metric_family_markdown(metric_family_summary, metric_family_coverage),
        encoding="utf-8",
    )
    (results_root / "metric_family_coverage.json").write_text(
        json.dumps(metric_family_coverage, indent=2),
        encoding="utf-8",
    )
    if not bdi_detail.empty:
        bdi_detail.to_csv(results_root / "bdi_correlations_detail.csv", index=False)
    if not bdi_summary.empty:
        bdi_summary.to_csv(results_root / "bdi_correlations_summary.csv", index=False)
    (results_root / "bdi_correlation_summary.md").write_text(build_bdi_markdown(bdi_summary), encoding="utf-8")

    manifest = {
        "dataset": DATASET,
        "analysis_roots_considered": [str(root) for root in analysis_roots],
        "subject_metrics_path": str(subject_metrics_path),
        "contrast_results_path": str(contrast_results_path),
        "participants_path": str(PARTICIPANTS_PATH),
        "results_root": str(results_root),
        "metric_family_summary_path": str(results_root / "metric_family_summary.csv"),
        "bdi_band_counts": {
            str(key): int(value) for key, value in phenos["bdi_band"].value_counts(dropna=False).to_dict().items() if pd.notna(key)
        },
    }
    (results_root / "paper_exports_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote demography summary to {results_root / 'demography_summary.csv'}")
    print(f"Wrote selected contrast summary to {results_root / 'selected_metrics_summary.csv'}")
    print(f"Wrote metric family summary to {results_root / 'metric_family_summary.csv'}")
    print(f"Wrote BDI correlation summary to {results_root / 'bdi_correlations_summary.csv'}")


if __name__ == "__main__":
    main()
