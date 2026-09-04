from __future__ import annotations

import argparse
import json
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import h5py
import numpy as np
import pandas as pd
from scipy import stats


TASK_DATASET = "ds003474"
REST_DATASET = "ds003478"
CONTRAST_NAME = "BDI_0_13_vs_BDI_20_63"

REPO_ROOT = Path(__file__).resolve().parents[4]
ARTICLE_DIR = Path(__file__).resolve().parents[1]

TASK_RAW_ROOT = REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds003474_20260609_044822"
DEFAULT_TASK_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "depression_probsel_ds003474_20260609"
DEFAULT_REST_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "depression_ds003478_20260521"
DEFAULT_RESULTS_ROOT = ARTICLE_DIR / "results"

PARTICIPANTS_PATH = ARTICLE_DIR / "metadata" / "participants.tsv"
TASK_SOURCE_PARTICIPANTS_PATH = Path("N:/received/ds003474/participants.tsv")

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
EVENT_BIN_ORDER = ["pre_far", "pre_near", "event", "post_near", "post_far"]
EVENT_METRIC_PREFERENCE = ("speed_mean", "e_mean", "d_mean", "m_mean", "e_m_mean", "m_o_mean")
EVENT_FAMILY_ORDER = [
    "feedback_correct",
    "feedback_incorrect",
    "train_stim_any",
    "test_stim_any",
    "left_response",
    "right_response",
]


@dataclass(frozen=True)
class ExportSpec:
    key: str
    title: str
    analysis_types: tuple[str, ...]
    preferred_metrics: tuple[str, ...]


@dataclass(frozen=True)
class PairedSpec:
    key: str
    title: str
    analysis_type: str
    metric: str
    source_group: str | None = None
    target_group: str | None = None


BLOCK_EXPORTS: tuple[ExportSpec, ...] = (
    ExportSpec(
        key="mnps_3d",
        title="Task 3D MNPS",
        analysis_types=("global_mnps_3d",),
        preferred_metrics=("d_median", "d_mean", "e_mean", "m_mean"),
    ),
    ExportSpec(
        key="mnps_9d",
        title="Task 9D MNPS",
        analysis_types=("global_mnps_9d",),
        preferred_metrics=("d_s_mean", "e_m_mean", "m_o_mean", "m_a_mean"),
    ),
    ExportSpec(
        key="mnj_3d",
        title="Task 3D MNJ",
        analysis_types=("global_mnps_jacobian_3d",),
        preferred_metrics=("spectral_radius_median", "rotation_norm_median", "trace_median"),
    ),
    ExportSpec(
        key="mnj_9d",
        title="Task 9D MNJ",
        analysis_types=("global_mnps_jacobian_9d",),
        preferred_metrics=("rotational_power_mean", "frobenius_norm_median", "rotation_norm_median"),
    ),
    ExportSpec(
        key="block_mnj",
        title="Task 9x9 block MNJ",
        analysis_types=("global_mnps_jacobian_9d_block_jacobian",),
        preferred_metrics=("block_frobenius_mean", "block_anisotropy_mean", "block_trace_mean"),
    ),
    ExportSpec(
        key="reachability",
        title="Task reachability",
        analysis_types=("reachability_cones",),
        preferred_metrics=(
            "tube_log_eig_var_mean",
            "tube_log_eig_var_median",
            "tube_log_det_mean",
            "cone_log_det_h2_median",
        ),
    ),
    ExportSpec(
        key="emmi",
        title="Task tier-2 EMMI",
        analysis_types=("tier2_emmi",),
        preferred_metrics=("mv_median", "mv_abs_median", "speed_median"),
    ),
    ExportSpec(
        key="distribution",
        title="Task distribution summary",
        analysis_types=("dist_summary",),
        preferred_metrics=("e_m_mad_sigma", "e_m_mad", "e_m_iqr", "d_skewness"),
    ),
)

PAIRED_SPECS: tuple[PairedSpec, ...] = (
    PairedSpec("mnps_3d", "3D MNPS", "global_mnps_3d", "d_median"),
    PairedSpec("mnps_9d", "9D MNPS", "global_mnps_9d", "d_s_mean"),
    PairedSpec("mnj_3d", "3D MNJ", "global_mnps_jacobian_3d", "spectral_radius_median"),
    PairedSpec("mnj_9d", "9D MNJ", "global_mnps_jacobian_9d", "rotational_power_mean"),
    PairedSpec(
        "block_mnj",
        "Block MNJ m->m",
        "global_mnps_jacobian_9d_block_jacobian",
        "block_frobenius_mean",
        source_group="m",
        target_group="m",
    ),
    PairedSpec("reachability", "Reachability", "reachability_cones", "tube_log_eig_var_mean"),
    PairedSpec("emmi", "Tier-2 EMMI", "tier2_emmi", "mv_median"),
    PairedSpec("distribution", "Distribution summary", "dist_summary", "e_m_mad_sigma"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build paired rest-task depression exports for ds003474.")
    parser.add_argument("--task-analysis-root", type=Path, default=DEFAULT_TASK_ANALYSIS_ROOT)
    parser.add_argument("--rest-analysis-root", type=Path, default=DEFAULT_REST_ANALYSIS_ROOT)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    return parser.parse_args()


def _latest_parquet(root: Path, dataset: str, stem: str) -> Path:
    matches = sorted(root.glob(f"{dataset}_{stem}_*.parquet"))
    if not matches:
        raise FileNotFoundError(f"No {stem} parquet found for {dataset} under {root}")
    return matches[-1]


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


def _decode_text(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


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


def _cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    if left.size < 2 or right.size < 2:
        return float("nan")
    left_var = left.var(ddof=1)
    right_var = right.var(ddof=1)
    pooled_var = ((left.size - 1) * left_var + (right.size - 1) * right_var) / (left.size + right.size - 2)
    if not np.isfinite(pooled_var) or pooled_var <= 0:
        return float("nan")
    return float((right.mean() - left.mean()) / np.sqrt(pooled_var))


def _sig_tier(row: pd.Series | dict[str, Any]) -> str:
    q = pd.to_numeric(pd.Series([row.get("q_value")]), errors="coerce").iloc[0]
    p = pd.to_numeric(pd.Series([row.get("p_value")]), errors="coerce").iloc[0]
    if pd.notna(q) and float(q) <= 0.05:
        return "q<=0.05"
    if pd.notna(p) and float(p) < 0.05:
        return "p<0.05"
    if pd.notna(p) and float(p) < 0.1:
        return "p<0.1"
    return "ns"


def _sorted_results(frame: pd.DataFrame, value_col: str = "effect_size") -> pd.DataFrame:
    out = frame.copy()
    out["abs_effect"] = pd.to_numeric(out[value_col], errors="coerce").abs()
    out["sig_rank"] = out.apply(_sig_tier, axis=1).map({"q<=0.05": 0, "p<0.05": 1, "p<0.1": 2, "ns": 3}).fillna(9)
    return out.sort_values(
        by=["sig_rank", "q_value", "p_value", "abs_effect", "metric"],
        ascending=[True, True, True, False, True],
        na_position="last",
    ).reset_index(drop=True)


def _sorted_correlations(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["abs_rho"] = pd.to_numeric(out["spearman_rho"], errors="coerce").abs()
    out["sig_rank"] = out.apply(_sig_tier, axis=1).map({"q<=0.05": 0, "p<0.05": 1, "p<0.1": 2, "ns": 3}).fillna(9)
    return out.sort_values(
        by=["sig_rank", "q_value", "p_value", "abs_rho", "metric"],
        ascending=[True, True, True, False, True],
        na_position="last",
    ).reset_index(drop=True)


def _pick_preferred(frame: pd.DataFrame, metrics: Iterable[str], *, correlation: bool = False) -> pd.Series:
    ordered = _sorted_correlations(frame) if correlation else _sorted_results(frame)
    for metric in metrics:
        match = ordered[ordered["metric"] == metric]
        if not match.empty:
            return match.iloc[0]
    return ordered.iloc[0]


def load_participants(path: Path = PARTICIPANTS_PATH) -> pd.DataFrame:
    phenos = pd.read_csv(path, sep="\t")
    phenos["age"] = pd.to_numeric(phenos["age"], errors="coerce")
    phenos["BDI"] = pd.to_numeric(phenos["BDI"], errors="coerce")
    phenos["STAI"] = pd.to_numeric(phenos["STAI"], errors="coerce")
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
                "dataset": TASK_DATASET,
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


def audit_paired_overlap(
    phenos: pd.DataFrame,
    task_source_phenos: pd.DataFrame,
    task_subject_metrics: pd.DataFrame,
    rest_subject_metrics: pd.DataFrame,
    results_root: Path,
) -> pd.DataFrame:
    task_subjects = sorted(task_subject_metrics["subject_id"].dropna().astype(str).unique().tolist())
    rest_subjects = sorted(rest_subject_metrics["subject_id"].dropna().astype(str).unique().tolist())
    task_subject_set = set(task_subjects)
    rest_subject_set = set(rest_subjects)
    paired_subjects = task_subject_set & rest_subject_set

    merged = phenos.merge(
        task_source_phenos.rename(
            columns={
                "Original_ID": "task_source_Original_ID",
                "BDI": "task_source_BDI",
                "STAI": "task_source_STAI",
            }
        ),
        on="participant_id",
        how="left",
    )
    merged["in_task_analysis"] = merged["participant_id"].isin(task_subject_set)
    merged["in_rest_analysis"] = merged["participant_id"].isin(rest_subject_set)
    merged["in_paired_analysis"] = merged["participant_id"].isin(paired_subjects)
    merged["task_source_original_match"] = pd.to_numeric(merged["Original_ID"], errors="coerce").eq(
        pd.to_numeric(merged["task_source_Original_ID"], errors="coerce")
    )
    merged["task_source_bdi_match"] = pd.to_numeric(merged["BDI"], errors="coerce").eq(
        pd.to_numeric(merged["task_source_BDI"], errors="coerce")
    )
    merged["task_source_stai_match"] = pd.to_numeric(merged["STAI"], errors="coerce").eq(
        pd.to_numeric(merged["task_source_STAI"], errors="coerce")
    )

    summary = {
        "task_dataset": TASK_DATASET,
        "rest_dataset": REST_DATASET,
        "article_metadata_rows": int(len(phenos)),
        "task_source_metadata_rows": int(len(task_source_phenos)),
        "valid_bdi_rows": int(phenos["BDI"].notna().sum()),
        "invalid_participants": phenos.loc[phenos["BDI"].isna(), "participant_id"].astype(str).tolist(),
        "task_subjects_in_analysis": int(len(task_subject_set)),
        "rest_subjects_in_analysis": int(len(rest_subject_set)),
        "paired_subjects_total": int(len(paired_subjects)),
        "paired_subjects_with_valid_bdi": int(
            merged.loc[merged["in_paired_analysis"] & merged["BDI"].notna(), "participant_id"].nunique()
        ),
        "exact_original_id_matches": int(merged["task_source_original_match"].fillna(False).sum()),
        "exact_bdi_matches": int(merged["task_source_bdi_match"].fillna(False).sum()),
        "exact_stai_matches": int(merged["task_source_stai_match"].fillna(False).sum()),
    }
    (results_root / "paired_overlap_subjects.csv").write_text("", encoding="utf-8")
    merged.to_csv(results_root / "paired_overlap_subjects.csv", index=False)
    (results_root / "paired_overlap_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (results_root / "paired_overlap_summary.md").write_text(
        "\n".join(
            [
                "# Paired overlap summary",
                "",
                f"- Task dataset: `{TASK_DATASET}`",
                f"- Rest dataset: `{REST_DATASET}`",
                f"- Task analysis subjects: `{summary['task_subjects_in_analysis']}`",
                f"- Rest analysis subjects: `{summary['rest_subjects_in_analysis']}`",
                f"- Paired subjects: `{summary['paired_subjects_total']}`",
                f"- Paired subjects with usable BDI: `{summary['paired_subjects_with_valid_bdi']}`",
                f"- Exact `Original_ID` metadata matches: `{summary['exact_original_id_matches']}`",
                f"- Exact BDI metadata matches: `{summary['exact_bdi_matches']}`",
                f"- Exact STAI metadata matches: `{summary['exact_stai_matches']}`",
                "",
                "The paired cohort is therefore the shared `sub-001`..`sub-122` subject set, with `sub-038` excluded from inferential summaries because its metadata row is invalid.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return merged


def build_selected_contrast_exports(contrast_results: pd.DataFrame, results_root: Path) -> pd.DataFrame:
    if contrast_results.empty or "contrast_name" not in contrast_results.columns:
        return pd.DataFrame()
    dataset_dir = results_root / TASK_DATASET
    dataset_dir.mkdir(parents=True, exist_ok=True)

    contrast_frame = contrast_results[contrast_results["contrast_name"] == CONTRAST_NAME].copy()
    summary_rows: list[dict[str, object]] = []
    for spec in BLOCK_EXPORTS:
        block_frame = contrast_frame[contrast_frame["analysis_type"].isin(spec.analysis_types)].copy()
        if block_frame.empty:
            continue
        ordered = _sorted_results(block_frame)
        selected = _pick_preferred(ordered, spec.preferred_metrics)
        csv_path = dataset_dir / f"{spec.key}_{CONTRAST_NAME}.csv"
        json_path = dataset_dir / f"{spec.key}_{CONTRAST_NAME}.json"
        ordered.drop(columns=["abs_effect", "sig_rank"], errors="ignore").to_csv(csv_path, index=False)
        payload = {
            "dataset": TASK_DATASET,
            "contrast_name": CONTRAST_NAME,
            "block_key": spec.key,
            "block_title": spec.title,
            "selected_metric": _row_dict(selected),
            "highlights": [
                _row_dict(row)
                for _, row in ordered.drop(columns=["abs_effect", "sig_rank"], errors="ignore").head(12).iterrows()
            ],
        }
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        summary_rows.append(
            {
                "dataset": TASK_DATASET,
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
                    "dataset": TASK_DATASET,
                    "cohort_key": cohort_key,
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
        for spec in BLOCK_EXPORTS:
            block_frame = cohort_frame[cohort_frame["analysis_type"].isin(spec.analysis_types)].copy()
            if block_frame.empty:
                continue
            selected = _pick_preferred(block_frame, spec.preferred_metrics, correlation=True)
            summary_rows.append(
                {
                    "dataset": TASK_DATASET,
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


def build_clinical_bdi_bins(subject_metrics: pd.DataFrame, phenos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    merged = subject_metrics.merge(
        phenos[["participant_id", "BDI", "age", "female", "bdi_band"]],
        left_on="subject_id",
        right_on="participant_id",
        how="left",
    ).drop(columns=["participant_id"], errors="ignore")
    split_specs = [
        ("bdi_0_13_vs_14_19", "BDI 0-13", "BDI 14-19"),
        ("bdi_0_13_vs_20_63", "BDI 0-13", "BDI 20-63"),
        ("bdi_14_19_vs_20_63", "BDI 14-19", "BDI 20-63"),
    ]
    group_cols = ["analysis_type", "metric"] + [column for column in CONTEXT_COLUMNS if column in merged.columns]
    detail_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []

    for split_name, left_label, right_label in split_specs:
        work = merged[merged["bdi_band"].isin([left_label, right_label])].copy()
        for keys, sub in work.groupby(group_cols, dropna=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            context = dict(zip(group_cols, keys))
            left = pd.to_numeric(sub.loc[sub["bdi_band"] == left_label, "value"], errors="coerce").dropna()
            right = pd.to_numeric(sub.loc[sub["bdi_band"] == right_label, "value"], errors="coerce").dropna()
            if len(left) < 3 or len(right) < 3:
                continue
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeWarning)
                _, p_value = stats.ttest_ind(left.to_numpy(), right.to_numpy(), equal_var=False, nan_policy="omit")
            row = {
                "dataset": TASK_DATASET,
                "split_name": split_name,
                "analysis_type": context["analysis_type"],
                "metric": context["metric"],
                "left_group": left_label,
                "right_group": right_label,
                "left_n": int(len(left)),
                "right_n": int(len(right)),
                "left_mean": float(left.mean()),
                "right_mean": float(right.mean()),
                "effect_estimate": float(right.mean() - left.mean()),
                "effect_size": _cohens_d(left.to_numpy(), right.to_numpy()),
                "p_value": float(p_value) if np.isfinite(p_value) else np.nan,
            }
            for column in CONTEXT_COLUMNS:
                row[column] = context.get(column)
            detail_rows.append(row)

    detail = pd.DataFrame(detail_rows)
    if detail.empty:
        return detail, pd.DataFrame()
    detail["q_value"] = detail.groupby(["split_name", "analysis_type"], dropna=False)["p_value"].transform(_bh_fdr)
    detail["sig_tier"] = detail.apply(_sig_tier, axis=1)

    for split_name, *_ in split_specs:
        sub = detail[detail["split_name"] == split_name].copy()
        if sub.empty:
            continue
        for spec in BLOCK_EXPORTS:
            block_frame = sub[sub["analysis_type"].isin(spec.analysis_types)].copy()
            if block_frame.empty:
                continue
            pick = _pick_preferred(block_frame, spec.preferred_metrics)
            summary_rows.append(
                {
                    "dataset": TASK_DATASET,
                    "split_name": split_name,
                    "block_key": spec.key,
                    "block_title": spec.title,
                    "analysis_type": pick["analysis_type"],
                    "metric": pick["metric"],
                    "effect_size": pick["effect_size"],
                    "effect_estimate": pick["effect_estimate"],
                    "p_value": pick["p_value"],
                    "q_value": pick["q_value"],
                    "left_n": pick["left_n"],
                    "right_n": pick["right_n"],
                    "left_mean": pick["left_mean"],
                    "right_mean": pick["right_mean"],
                    "left_group": pick["left_group"],
                    "right_group": pick["right_group"],
                    "sig_tier": _sig_tier(pick),
                    "block_scope": pick.get("block_scope"),
                    "block_space": pick.get("block_space"),
                    "source_group": pick.get("source_group"),
                    "target_group": pick.get("target_group"),
                    "source_dim": pick.get("source_dim"),
                    "target_dim": pick.get("target_dim"),
                }
            )
    return detail, pd.DataFrame(summary_rows)


def build_selected_from_subject_metrics(subject_metrics: pd.DataFrame, phenos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    merged = subject_metrics.merge(
        phenos[["participant_id", "bdi_band"]],
        left_on="subject_id",
        right_on="participant_id",
        how="left",
    ).drop(columns=["participant_id"], errors="ignore")
    group_cols = ["analysis_type", "metric"] + [column for column in CONTEXT_COLUMNS if column in merged.columns]
    detail_rows: list[dict[str, object]] = []
    for keys, sub in merged.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        context = dict(zip(group_cols, keys))
        left = pd.to_numeric(sub.loc[sub["bdi_band"] == "BDI 0-13", "value"], errors="coerce").dropna()
        right = pd.to_numeric(sub.loc[sub["bdi_band"] == "BDI 20-63", "value"], errors="coerce").dropna()
        if len(left) < 3 or len(right) < 3:
            continue
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            _, p_value = stats.ttest_ind(left.to_numpy(), right.to_numpy(), equal_var=False, nan_policy="omit")
        row = {
            "dataset": TASK_DATASET,
            "contrast_name": CONTRAST_NAME,
            "analysis_type": context["analysis_type"],
            "metric": context["metric"],
            "left_group": "BDI 0-13",
            "right_group": "BDI 20-63",
            "left_n": int(len(left)),
            "right_n": int(len(right)),
            "left_mean": float(left.mean()),
            "right_mean": float(right.mean()),
            "effect_estimate": float(right.mean() - left.mean()),
            "effect_size": _cohens_d(left.to_numpy(), right.to_numpy()),
            "p_value": float(p_value) if np.isfinite(p_value) else np.nan,
        }
        for column in CONTEXT_COLUMNS:
            row[column] = context.get(column)
        detail_rows.append(row)
    detail = pd.DataFrame(detail_rows)
    if detail.empty:
        return detail, pd.DataFrame()
    detail["q_value"] = detail.groupby("analysis_type", dropna=False)["p_value"].transform(_bh_fdr)
    detail["sig_tier"] = detail.apply(_sig_tier, axis=1)

    summary_rows: list[dict[str, object]] = []
    for spec in BLOCK_EXPORTS:
        block_frame = detail[detail["analysis_type"].isin(spec.analysis_types)].copy()
        if block_frame.empty:
            continue
        pick = _pick_preferred(block_frame, spec.preferred_metrics)
        summary_rows.append(
            {
                "dataset": TASK_DATASET,
                "contrast_name": CONTRAST_NAME,
                "block_key": spec.key,
                "block_title": spec.title,
                "analysis_type": pick["analysis_type"],
                "metric": pick["metric"],
                "effect_size": pick["effect_size"],
                "effect_estimate": pick["effect_estimate"],
                "p_value": pick["p_value"],
                "q_value": pick["q_value"],
                "left_n": pick["left_n"],
                "right_n": pick["right_n"],
                "left_mean": pick["left_mean"],
                "right_mean": pick["right_mean"],
                "sig_tier": _sig_tier(pick),
                "block_scope": pick.get("block_scope"),
                "block_space": pick.get("block_space"),
                "source_group": pick.get("source_group"),
                "target_group": pick.get("target_group"),
                "source_dim": pick.get("source_dim"),
                "target_dim": pick.get("target_dim"),
                "export_csv": None,
                "export_json": None,
            }
        )
    return detail, pd.DataFrame(summary_rows)


def _event_family(label: str) -> str | None:
    label = label.strip().lower()
    exact = {
        "feedback: correct": "feedback_correct",
        "feedback: incorrect": "feedback_incorrect",
        "left response": "left_response",
        "right response": "right_response",
    }
    if label in exact:
        return exact[label]
    if label.startswith("train stim:"):
        return "train_stim_any"
    if label.startswith("test stim:"):
        return "test_stim_any"
    return None


def collect_event_locked_subject_summary(phenos: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for subject_id in phenos["participant_id"].astype(str):
        h5_path = TASK_RAW_ROOT / f"{subject_id}_task_probabilistic_selection" / f"{subject_id}_task_probabilistic_selection.h5"
        if not h5_path.exists():
            continue
        with h5py.File(h5_path, "r") as handle:
            coords3 = np.asarray(handle["coords_3d_cohort_anchored"]["values"], dtype=float)
            coords9 = np.asarray(handle["coords_9d_cohort_anchored"]["values"], dtype=float)
            coords9_names = [_decode_text(item) for item in handle["coords_9d_cohort_anchored"]["names"][:]]
            mnps_dot = np.asarray(handle["mnps_3d_dot"], dtype=float)
            speed = np.linalg.norm(mnps_dot, axis=1)
            event_windows = handle["event_windows"]
            event_frame = pd.DataFrame(
                {
                    "event_label_key": [_decode_text(item) for item in event_windows["event_label_key"][:]],
                    "bin_label": [_decode_text(item) for item in event_windows["bin_label"][:]],
                    "window_id": pd.to_numeric(event_windows["window_id"][:], errors="coerce"),
                    "event_id": pd.to_numeric(event_windows["event_id"][:], errors="coerce"),
                    "is_event_window": pd.to_numeric(event_windows["is_event_window"][:], errors="coerce"),
                }
            )
        event_frame["family"] = event_frame["event_label_key"].map(_event_family)
        event_frame = event_frame[event_frame["family"].notna()].copy()
        event_frame = event_frame[event_frame["is_event_window"].fillna(0) > 0].copy()
        event_frame = event_frame[event_frame["window_id"].between(0, len(coords3) - 1)].copy()
        if event_frame.empty:
            continue

        e_m_idx = coords9_names.index("e_m") if "e_m" in coords9_names else None
        m_o_idx = coords9_names.index("m_o") if "m_o" in coords9_names else None
        event_frame["window_id"] = event_frame["window_id"].astype(int)

        for (family, bin_label), sub in event_frame.groupby(["family", "bin_label"], dropna=False):
            idx = sub["window_id"].to_numpy(dtype=int)
            row = {
                "subject_id": subject_id,
                "event_family": family,
                "bin_label": str(bin_label),
                "n_rows": int(len(sub)),
                "n_events": int(sub["event_id"].nunique()),
                "m_mean": float(np.nanmean(coords3[idx, 0])),
                "d_mean": float(np.nanmean(coords3[idx, 1])),
                "e_mean": float(np.nanmean(coords3[idx, 2])),
                "speed_mean": float(np.nanmean(speed[idx])),
            }
            row["e_m_mean"] = float(np.nanmean(coords9[idx, e_m_idx])) if e_m_idx is not None else np.nan
            row["m_o_mean"] = float(np.nanmean(coords9[idx, m_o_idx])) if m_o_idx is not None else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def build_event_locked_outputs(event_subjects: pd.DataFrame, phenos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if event_subjects.empty:
        return (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
    merged = event_subjects.merge(
        phenos[["participant_id", "BDI", "bdi_band"]],
        left_on="subject_id",
        right_on="participant_id",
        how="left",
    ).drop(columns=["participant_id"], errors="ignore")
    metrics = ["m_mean", "d_mean", "e_mean", "speed_mean", "e_m_mean", "m_o_mean"]

    contrast_rows: list[dict[str, object]] = []
    corr_rows: list[dict[str, object]] = []
    for (family, bin_label), group_frame in merged.groupby(["event_family", "bin_label"], dropna=False):
        for metric in metrics:
            work = group_frame[["subject_id", "BDI", "bdi_band", metric]].dropna().copy()
            if work.empty:
                continue
            low = work.loc[work["bdi_band"] == "BDI 0-13", metric].to_numpy(dtype=float)
            high = work.loc[work["bdi_band"] == "BDI 20-63", metric].to_numpy(dtype=float)
            if low.size >= 3 and high.size >= 3:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=RuntimeWarning)
                    _, p_value = stats.ttest_ind(low, high, equal_var=False, nan_policy="omit")
                contrast_rows.append(
                    {
                        "event_family": family,
                        "bin_label": bin_label,
                        "metric": metric,
                        "left_group": "BDI 0-13",
                        "right_group": "BDI 20-63",
                        "left_n": int(low.size),
                        "right_n": int(high.size),
                        "left_mean": float(low.mean()),
                        "right_mean": float(high.mean()),
                        "effect_estimate": float(high.mean() - low.mean()),
                        "effect_size": _cohens_d(low, high),
                        "p_value": float(p_value) if np.isfinite(p_value) else np.nan,
                    }
                )
            corr_work = work.drop_duplicates(subset=["subject_id"])
            if len(corr_work) >= 6 and corr_work[metric].nunique() >= 2 and corr_work["BDI"].nunique() >= 2:
                rho, p_value = stats.spearmanr(corr_work[metric], corr_work["BDI"])
                corr_rows.append(
                    {
                        "event_family": family,
                        "bin_label": bin_label,
                        "metric": metric,
                        "n_subjects": int(len(corr_work)),
                        "spearman_rho": float(rho) if np.isfinite(rho) else np.nan,
                        "p_value": float(p_value) if np.isfinite(p_value) else np.nan,
                    }
                )

    contrast_detail = pd.DataFrame(contrast_rows)
    corr_detail = pd.DataFrame(corr_rows)
    contrast_summary_rows: list[dict[str, object]] = []
    corr_summary_rows: list[dict[str, object]] = []

    if not contrast_detail.empty:
        contrast_detail["q_value"] = contrast_detail.groupby(["event_family", "bin_label"], dropna=False)["p_value"].transform(_bh_fdr)
        contrast_detail["sig_tier"] = contrast_detail.apply(_sig_tier, axis=1)
        for family in EVENT_FAMILY_ORDER:
            family_frame = contrast_detail[contrast_detail["event_family"] == family].copy()
            if family_frame.empty:
                continue
            for bin_label in EVENT_BIN_ORDER:
                sub = family_frame[family_frame["bin_label"] == bin_label].copy()
                if sub.empty:
                    continue
                pick = _pick_preferred(sub, EVENT_METRIC_PREFERENCE)
                contrast_summary_rows.append(
                    {
                        "event_family": family,
                        "bin_label": bin_label,
                        "metric": pick["metric"],
                        "effect_size": pick["effect_size"],
                        "effect_estimate": pick["effect_estimate"],
                        "p_value": pick["p_value"],
                        "q_value": pick["q_value"],
                        "left_n": pick["left_n"],
                        "right_n": pick["right_n"],
                        "left_mean": pick["left_mean"],
                        "right_mean": pick["right_mean"],
                        "sig_tier": _sig_tier(pick),
                    }
                )

    if not corr_detail.empty:
        corr_detail["q_value"] = corr_detail.groupby(["event_family", "bin_label"], dropna=False)["p_value"].transform(_bh_fdr)
        corr_detail["sig_tier"] = corr_detail.apply(_sig_tier, axis=1)
        for family in EVENT_FAMILY_ORDER:
            family_frame = corr_detail[corr_detail["event_family"] == family].copy()
            if family_frame.empty:
                continue
            for bin_label in EVENT_BIN_ORDER:
                sub = family_frame[family_frame["bin_label"] == bin_label].copy()
                if sub.empty:
                    continue
                pick = _pick_preferred(sub, EVENT_METRIC_PREFERENCE, correlation=True)
                corr_summary_rows.append(
                    {
                        "event_family": family,
                        "bin_label": bin_label,
                        "metric": pick["metric"],
                        "spearman_rho": pick["spearman_rho"],
                        "p_value": pick["p_value"],
                        "q_value": pick["q_value"],
                        "n_subjects": pick["n_subjects"],
                        "sig_tier": _sig_tier(pick),
                    }
                )

    return (
        contrast_detail,
        pd.DataFrame(contrast_summary_rows),
        corr_detail,
        pd.DataFrame(corr_summary_rows),
    )


def _subject_metric_series(
    subject_metrics: pd.DataFrame,
    *,
    analysis_type: str,
    metric: str,
    source_group: str | None = None,
    target_group: str | None = None,
) -> pd.DataFrame:
    frame = subject_metrics[
        (subject_metrics["analysis_type"] == analysis_type)
        & (subject_metrics["metric"] == metric)
    ].copy()
    if source_group is not None:
        frame = frame[frame["source_group"] == source_group].copy()
    if target_group is not None:
        frame = frame[frame["target_group"] == target_group].copy()
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[frame["value"].notna()].copy()
    if frame.empty:
        return pd.DataFrame(columns=["subject_id", "value"])
    return frame.groupby("subject_id", as_index=False).agg(value=("value", "mean"))


def build_paired_delta_outputs(task_metrics: pd.DataFrame, rest_metrics: pd.DataFrame, phenos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    detail_rows: list[dict[str, object]] = []
    contrast_rows: list[dict[str, object]] = []
    corr_rows: list[dict[str, object]] = []

    for spec in PAIRED_SPECS:
        task_series = _subject_metric_series(
            task_metrics,
            analysis_type=spec.analysis_type,
            metric=spec.metric,
            source_group=spec.source_group,
            target_group=spec.target_group,
        ).rename(columns={"value": "task_value"})
        rest_series = _subject_metric_series(
            rest_metrics,
            analysis_type=spec.analysis_type,
            metric=spec.metric,
            source_group=spec.source_group,
            target_group=spec.target_group,
        ).rename(columns={"value": "rest_value"})
        merged = (
            phenos[["participant_id", "BDI", "bdi_band"]]
            .rename(columns={"participant_id": "subject_id"})
            .merge(task_series, on="subject_id", how="inner")
            .merge(rest_series, on="subject_id", how="inner")
        )
        if merged.empty:
            continue
        merged["delta_value"] = pd.to_numeric(merged["task_value"], errors="coerce") - pd.to_numeric(merged["rest_value"], errors="coerce")
        merged = merged.dropna(subset=["delta_value"]).copy()
        if merged.empty:
            continue

        for _, row in merged.iterrows():
            detail_rows.append(
                {
                    "subject_id": row["subject_id"],
                    "block_key": spec.key,
                    "block_title": spec.title,
                    "analysis_type": spec.analysis_type,
                    "metric": spec.metric,
                    "source_group": spec.source_group,
                    "target_group": spec.target_group,
                    "task_value": row["task_value"],
                    "rest_value": row["rest_value"],
                    "delta_value": row["delta_value"],
                    "BDI": row["BDI"],
                    "bdi_band": row["bdi_band"],
                }
            )

        low = merged.loc[merged["bdi_band"] == "BDI 0-13", "delta_value"].to_numpy(dtype=float)
        high = merged.loc[merged["bdi_band"] == "BDI 20-63", "delta_value"].to_numpy(dtype=float)
        if low.size >= 3 and high.size >= 3:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeWarning)
                _, p_value = stats.ttest_ind(low, high, equal_var=False, nan_policy="omit")
            contrast_rows.append(
                {
                    "block_key": spec.key,
                    "block_title": spec.title,
                    "analysis_type": spec.analysis_type,
                    "metric": spec.metric,
                    "source_group": spec.source_group,
                    "target_group": spec.target_group,
                    "left_group": "BDI 0-13",
                    "right_group": "BDI 20-63",
                    "left_n": int(low.size),
                    "right_n": int(high.size),
                    "left_mean": float(low.mean()),
                    "right_mean": float(high.mean()),
                    "effect_estimate": float(high.mean() - low.mean()),
                    "effect_size": _cohens_d(low, high),
                    "p_value": float(p_value) if np.isfinite(p_value) else np.nan,
                }
            )
        corr_work = merged.dropna(subset=["BDI", "delta_value"]).copy()
        if len(corr_work) >= 6 and corr_work["delta_value"].nunique() >= 2 and corr_work["BDI"].nunique() >= 2:
            rho, p_value = stats.spearmanr(corr_work["delta_value"], corr_work["BDI"])
            corr_rows.append(
                {
                    "block_key": spec.key,
                    "block_title": spec.title,
                    "analysis_type": spec.analysis_type,
                    "metric": spec.metric,
                    "source_group": spec.source_group,
                    "target_group": spec.target_group,
                    "n_subjects": int(len(corr_work)),
                    "spearman_rho": float(rho) if np.isfinite(rho) else np.nan,
                    "p_value": float(p_value) if np.isfinite(p_value) else np.nan,
                }
            )

    detail = pd.DataFrame(detail_rows)
    contrast = pd.DataFrame(contrast_rows)
    corr = pd.DataFrame(corr_rows)
    if not contrast.empty:
        contrast["q_value"] = _bh_fdr(contrast["p_value"])
        contrast["sig_tier"] = contrast.apply(_sig_tier, axis=1)
    if not corr.empty:
        corr["q_value"] = _bh_fdr(corr["p_value"])
        corr["sig_tier"] = corr.apply(_sig_tier, axis=1)
    return detail, contrast, corr


def _write_markdown_summaries(
    results_root: Path,
    bdi_summary: pd.DataFrame,
    bdi_bin_summary: pd.DataFrame,
    event_summary: pd.DataFrame,
    event_corr_summary: pd.DataFrame,
    paired_summary: pd.DataFrame,
    paired_corr: pd.DataFrame,
) -> None:
    lines = ["# Paired rest-task task-state summary", ""]
    if not bdi_summary.empty:
        lines.append("## Task-only continuous BDI")
        lines.append("")
        for _, row in bdi_summary.iterrows():
            if row["cohort_key"] != "All_valid":
                continue
            lines.append(
                f"- `{row['block_title']}` / `{row['metric']}`: rho={float(row['spearman_rho']):.3f}, q={float(row['q_value']):.4g}"
            )
        lines.append("")
    if not bdi_bin_summary.empty:
        low_high = bdi_bin_summary[bdi_bin_summary["split_name"] == "bdi_0_13_vs_20_63"].copy()
        if not low_high.empty:
            lines.append("## Task-only low vs high BDI")
            lines.append("")
            for _, row in low_high.iterrows():
                lines.append(
                    f"- `{row['block_title']}` / `{row['metric']}`: d={float(row['effect_size']):.3f}, q={float(row['q_value']):.4g}"
                )
            lines.append("")
    if not event_summary.empty:
        lines.append("## Event-locked low vs high BDI")
        lines.append("")
        for _, row in event_summary.iterrows():
            if row["bin_label"] != "event":
                continue
            lines.append(
                f"- `{row['event_family']}` / `{row['metric']}`: d={float(row['effect_size']):.3f}, q={float(row['q_value']):.4g}"
            )
        lines.append("")
    if not event_corr_summary.empty:
        lines.append("## Event-locked continuous BDI")
        lines.append("")
        for _, row in event_corr_summary.iterrows():
            if row["bin_label"] != "event":
                continue
            lines.append(
                f"- `{row['event_family']}` / `{row['metric']}`: rho={float(row['spearman_rho']):.3f}, q={float(row['q_value']):.4g}"
            )
        lines.append("")
    if not paired_summary.empty:
        lines.append("## Task-minus-rest low vs high BDI")
        lines.append("")
        for _, row in paired_summary.iterrows():
            lines.append(
                f"- `{row['block_title']}` / `{row['metric']}`: d={float(row['effect_size']):.3f}, q={float(row['q_value']):.4g}"
            )
        lines.append("")
    if not paired_corr.empty:
        lines.append("## Task-minus-rest continuous BDI")
        lines.append("")
        for _, row in paired_corr.iterrows():
            lines.append(
                f"- `{row['block_title']}` / `{row['metric']}`: rho={float(row['spearman_rho']):.3f}, q={float(row['q_value']):.4g}"
            )
        lines.append("")
    (results_root / "paired_task_state_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    results_root = args.results_root
    results_root.mkdir(parents=True, exist_ok=True)

    phenos = load_participants()
    task_source_phenos = load_participants(TASK_SOURCE_PARTICIPANTS_PATH)

    task_subject_metrics_path = _latest_parquet(args.task_analysis_root, TASK_DATASET, "subject_metrics")
    task_contrast_results_path = _latest_parquet(args.task_analysis_root, TASK_DATASET, "contrast_results")
    rest_subject_metrics_path = _latest_parquet(args.rest_analysis_root, REST_DATASET, "subject_metrics")

    task_subject_metrics = pd.read_parquet(task_subject_metrics_path)
    task_contrast_results = pd.read_parquet(task_contrast_results_path)
    rest_subject_metrics = pd.read_parquet(rest_subject_metrics_path)

    audit_paired_overlap(phenos, task_source_phenos, task_subject_metrics, rest_subject_metrics, results_root)
    demography = build_demography_summary(phenos)
    selected_detail = pd.DataFrame()
    selected_metrics = build_selected_contrast_exports(task_contrast_results, results_root)
    if selected_metrics.empty:
        selected_detail, selected_metrics = build_selected_from_subject_metrics(task_subject_metrics, phenos)
    bdi_detail, bdi_summary = build_bdi_correlations(task_subject_metrics, phenos)
    bdi_bin_detail, bdi_bin_summary = build_clinical_bdi_bins(task_subject_metrics, phenos)
    event_subjects = collect_event_locked_subject_summary(phenos)
    event_detail, event_summary, event_corr_detail, event_corr_summary = build_event_locked_outputs(event_subjects, phenos)
    paired_detail, paired_summary, paired_corr = build_paired_delta_outputs(task_subject_metrics, rest_subject_metrics, phenos)

    demography.to_csv(results_root / "demography_summary.csv", index=False)
    selected_metrics.to_csv(results_root / "selected_metrics_summary.csv", index=False)
    if not selected_detail.empty:
        selected_detail.to_csv(results_root / "selected_metrics_detail.csv", index=False)
    if not bdi_detail.empty:
        bdi_detail.to_csv(results_root / "bdi_correlations_detail.csv", index=False)
    if not bdi_summary.empty:
        bdi_summary.to_csv(results_root / "bdi_correlations_summary.csv", index=False)
    if not bdi_bin_detail.empty:
        bdi_bin_detail.to_csv(results_root / "clinical_bdi_bin_detail.csv", index=False)
    if not bdi_bin_summary.empty:
        bdi_bin_summary.to_csv(results_root / "clinical_bdi_bin_summary.csv", index=False)
    if not event_subjects.empty:
        event_subjects.to_csv(results_root / "event_locked_subject_summary.csv", index=False)
    if not event_detail.empty:
        event_detail.to_csv(results_root / "event_locked_contrast_detail.csv", index=False)
    if not event_summary.empty:
        event_summary.to_csv(results_root / "event_locked_summary.csv", index=False)
    if not event_corr_detail.empty:
        event_corr_detail.to_csv(results_root / "event_locked_correlation_detail.csv", index=False)
    if not event_corr_summary.empty:
        event_corr_summary.to_csv(results_root / "event_locked_correlation_summary.csv", index=False)
    if not paired_detail.empty:
        paired_detail.to_csv(results_root / "paired_delta_detail.csv", index=False)
    if not paired_summary.empty:
        paired_summary.to_csv(results_root / "paired_delta_summary.csv", index=False)
    if not paired_corr.empty:
        paired_corr.to_csv(results_root / "paired_delta_correlation_summary.csv", index=False)

    _write_markdown_summaries(
        results_root,
        bdi_summary,
        bdi_bin_summary,
        event_summary,
        event_corr_summary,
        paired_summary,
        paired_corr,
    )

    manifest = {
        "task_dataset": TASK_DATASET,
        "rest_dataset": REST_DATASET,
        "task_analysis_root": str(args.task_analysis_root),
        "rest_analysis_root": str(args.rest_analysis_root),
        "task_subject_metrics_path": str(task_subject_metrics_path),
        "task_contrast_results_path": str(task_contrast_results_path),
        "rest_subject_metrics_path": str(rest_subject_metrics_path),
        "task_raw_root": str(TASK_RAW_ROOT),
        "participants_path": str(PARTICIPANTS_PATH),
        "task_source_participants_path": str(TASK_SOURCE_PARTICIPANTS_PATH),
        "results_root": str(results_root),
        "bdi_band_counts": {
            str(key): int(value) for key, value in phenos["bdi_band"].value_counts(dropna=False).to_dict().items() if pd.notna(key)
        },
        "event_families": EVENT_FAMILY_ORDER,
        "event_bins": EVENT_BIN_ORDER,
        "paired_specs": [
            {
                "key": spec.key,
                "title": spec.title,
                "analysis_type": spec.analysis_type,
                "metric": spec.metric,
                "source_group": spec.source_group,
                "target_group": spec.target_group,
            }
            for spec in PAIRED_SPECS
        ],
    }
    (results_root / "paper_exports_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote task demography summary to {results_root / 'demography_summary.csv'}")
    print(f"Wrote task selected metrics summary to {results_root / 'selected_metrics_summary.csv'}")
    print(f"Wrote event-locked outputs to {results_root}")
    print(f"Wrote paired task-minus-rest outputs to {results_root}")


if __name__ == "__main__":
    main()
