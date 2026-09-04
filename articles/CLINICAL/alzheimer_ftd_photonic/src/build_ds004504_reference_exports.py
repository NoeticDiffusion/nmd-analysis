from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy import stats


DATASET = "ds004504"
REPO_ROOT = Path(__file__).resolve().parents[4]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "alzheimer_ftd_photonic_ds004504_20260528"
FALLBACK_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis"
DEFAULT_RESULTS_ROOT = ARTICLE_DIR / "results" / "ds004504_reference"
PARTICIPANTS_PATH = (
    REPO_ROOT
    / "articles"
    / "CLINICAL"
    / "alzheimer"
    / "metadata"
    / "ds004504_alzheimer_FTD_eeg"
    / "participants.tsv"
)

GROUP_LABELS = {
    "A": "AD",
    "C": "Healthy",
    "F": "FTD",
}
CONTRAST_LABELS = {
    "AD_vs_Healthy": "AD vs Healthy",
    "FTD_vs_Healthy": "FTD vs Healthy",
    "AD_vs_FTD": "AD vs FTD",
}
CORRELATION_COHORTS = {
    "Dementia_all": ["A", "F"],
    "AD_only": ["A"],
    "FTD_only": ["F"],
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


EXPORT_SPECS: tuple[ExportSpec, ...] = (
    ExportSpec(
        key="emmi",
        title="Tier-2 EMMI",
        analysis_types=("tier2_emmi",),
        preferred_metrics=("speed_median", "speed_mean", "mv_over_speed_median"),
    ),
    ExportSpec(
        key="mnj_3d",
        title="Global 3D MNJ",
        analysis_types=("global_mnps_jacobian_3d",),
        preferred_metrics=(
            "mdr_median",
            "spectral_radius_median",
            "rotational_power_median",
            "frobenius_norm_median",
            "trace_median",
            "anisotropy_abs_eig_median",
        ),
    ),
    ExportSpec(
        key="mnj_9d",
        title="Global 9D MNJ",
        analysis_types=("global_mnps_jacobian_9d",),
        preferred_metrics=(
            "mdr_median",
            "spectral_radius_median",
            "rotational_power_median",
            "frobenius_norm_median",
            "trace_median",
            "anisotropy_abs_eig_median",
        ),
    ),
    ExportSpec(
        key="block_mnj",
        title="9x9 Block MNJ",
        analysis_types=("global_mnps_jacobian_9d_block_jacobian",),
        preferred_metrics=(
            "block_frobenius_mean",
            "block_trace_mean",
            "block_anisotropy_mean",
            "c_sym_mean",
            "c_rot_mean",
        ),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build article-local ds004504 resting-state reference exports.")
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


def load_participants() -> pd.DataFrame:
    phenos = pd.read_csv(PARTICIPANTS_PATH, sep="\t")
    phenos = phenos.rename(
        columns={
            "Gender": "gender",
            "Age": "age",
            "Group": "group",
            "MMSE": "mmse",
        }
    )
    phenos["age"] = pd.to_numeric(phenos["age"], errors="coerce")
    phenos["mmse"] = pd.to_numeric(phenos["mmse"], errors="coerce")
    phenos["female"] = phenos["gender"].astype(str).eq("F")
    phenos["group_label"] = phenos["group"].astype(str).map(GROUP_LABELS).fillna(phenos["group"].astype(str))
    return phenos


def build_demography_summary(phenos: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for group_code, group_label in GROUP_LABELS.items():
        sub = phenos[phenos["group"] == group_code].copy()
        rows.append(
            {
                "dataset": DATASET,
                "group_code": group_code,
                "group_label": group_label,
                "n": int(len(sub)),
                "age_mean": float(sub["age"].mean()),
                "age_sd": float(sub["age"].std()),
                "female_n": int(sub["female"].sum()),
                "female_pct": float(sub["female"].mean() * 100.0),
                "mmse_mean": float(sub["mmse"].mean()),
                "mmse_sd": float(sub["mmse"].std()),
                "mmse_median": float(sub["mmse"].median()),
            }
        )
    return pd.DataFrame(rows)


def build_selected_metrics_summary(contrast_results: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for contrast_name in sorted(contrast_results["contrast_name"].dropna().astype(str).unique().tolist()):
        contrast_frame = contrast_results[contrast_results["contrast_name"] == contrast_name].copy()
        for spec in EXPORT_SPECS:
            block_frame = contrast_frame[contrast_frame["analysis_type"].isin(spec.analysis_types)].copy()
            if block_frame.empty:
                continue
            selected = _choose_preferred_metric(block_frame, spec.preferred_metrics)
            row = _row_dict(selected)
            row["dataset"] = DATASET
            row["contrast_label"] = CONTRAST_LABELS.get(contrast_name, contrast_name)
            row["block_key"] = spec.key
            row["block_title"] = spec.title
            rows.append(row)
    return pd.DataFrame(rows)


def _prepare_correlation_frame(subject_metrics: pd.DataFrame, phenos: pd.DataFrame) -> pd.DataFrame:
    merged = subject_metrics.merge(
        phenos[["participant_id", "group", "group_label", "age", "gender", "mmse"]],
        left_on="subject_id",
        right_on="participant_id",
        how="left",
        suffixes=("", "_meta"),
    )
    if "group_meta" in merged.columns:
        merged["group"] = merged["group_meta"].combine_first(merged["group"])
        merged = merged.drop(columns=["group_meta"])
    keep = merged[pd.to_numeric(merged["value"], errors="coerce").notna()].copy()
    keep["value"] = pd.to_numeric(keep["value"], errors="coerce")
    keep["mmse"] = pd.to_numeric(keep["mmse"], errors="coerce")
    keep = keep[pd.notna(keep["mmse"])].copy()
    dedupe_cols = ["subject_id", "group", "group_label", "analysis_type", "metric"] + [
        column for column in CONTEXT_COLUMNS if column in keep.columns
    ]
    return (
        keep.groupby(dedupe_cols, dropna=False, as_index=False)
        .agg(value=("value", "mean"), mmse=("mmse", "first"))
        .reset_index(drop=True)
    )


def build_mmse_correlations(subject_metrics: pd.DataFrame, phenos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    prepared = _prepare_correlation_frame(subject_metrics, phenos)
    rows: list[dict[str, object]] = []
    group_cols = ["analysis_type", "metric"] + [column for column in CONTEXT_COLUMNS if column in prepared.columns]

    for cohort_key, groups in CORRELATION_COHORTS.items():
        cohort = prepared[prepared["group"].astype(str).isin(groups)].copy()
        if cohort.empty:
            continue
        for keys, group_frame in cohort.groupby(group_cols, dropna=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            row = dict(zip(group_cols, keys))
            work = group_frame[["subject_id", "value", "mmse"]].dropna().copy().drop_duplicates(subset=["subject_id"])
            if len(work) < 3 or work["value"].nunique() < 2 or work["mmse"].nunique() < 2:
                continue
            spearman_rho, spearman_p = stats.spearmanr(work["value"], work["mmse"])
            pearson_r, pearson_p = stats.pearsonr(work["value"], work["mmse"])
            row.update(
                {
                    "dataset": DATASET,
                    "cohort_key": cohort_key,
                    "group_codes": ",".join(groups),
                    "n_subjects": int(len(work)),
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
        for spec in EXPORT_SPECS:
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


def build_mmse_markdown(summary: pd.DataFrame) -> str:
    lines = [
        "# ds004504 resting-state MMSE reference summary",
        "",
        f"- Dataset: `{DATASET}`",
        "",
    ]
    if summary.empty:
        lines.extend(
            [
                "No MMSE correlations were estimable with the current resting-state export.",
                "",
            ]
        )
        return "\n".join(lines)

    for cohort_key in ("Dementia_all", "AD_only", "FTD_only"):
        cohort = summary[summary["cohort_key"] == cohort_key].copy()
        if cohort.empty:
            continue
        lines.extend([f"## {cohort_key}", ""])
        for _, row in cohort.iterrows():
            suffix_bits: list[str] = []
            if pd.notna(row.get("source_group")) or pd.notna(row.get("target_group")):
                suffix_bits.append(f"block={row.get('source_group')}->{row.get('target_group')}")
            if pd.notna(row.get("block_space")):
                suffix_bits.append(f"space={row.get('block_space')}")
            suffix = f" ({', '.join(suffix_bits)})" if suffix_bits else ""
            lines.append(
                f"- `{row['block_title']}` / `{row['metric']}`{suffix}: "
                f"rho={float(row['spearman_rho']):.4f}, p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}"
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
    selected_metrics = build_selected_metrics_summary(contrast_results)
    mmse_detail, mmse_summary = build_mmse_correlations(subject_metrics, phenos)

    demography.to_csv(results_root / "demography_summary.csv", index=False)
    selected_metrics.to_csv(results_root / "selected_metrics_summary.csv", index=False)
    if not mmse_detail.empty:
        mmse_detail.to_csv(results_root / "mmse_correlations_detail.csv", index=False)
    if not mmse_summary.empty:
        mmse_summary.to_csv(results_root / "mmse_correlations_summary.csv", index=False)
    (results_root / "mmse_correlation_summary.md").write_text(
        build_mmse_markdown(mmse_summary),
        encoding="utf-8",
    )

    manifest = {
        "dataset": DATASET,
        "analysis_roots_considered": [str(root) for root in analysis_roots],
        "subject_metrics_path": str(subject_metrics_path),
        "contrast_results_path": str(contrast_results_path),
        "participants_path": str(PARTICIPANTS_PATH),
        "results_root": str(results_root),
        "group_counts": {
            GROUP_LABELS.get(str(key), str(key)): int(value)
            for key, value in phenos["group"].value_counts(dropna=False).to_dict().items()
        },
    }
    (results_root / "paper_exports_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote demography summary to {results_root / 'demography_summary.csv'}")
    print(f"Wrote selected contrast summary to {results_root / 'selected_metrics_summary.csv'}")
    print(f"Wrote MMSE summary to {results_root / 'mmse_correlations_summary.csv'}")


if __name__ == "__main__":
    main()
