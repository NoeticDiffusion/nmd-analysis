from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy import stats


REPO_ROOT = Path(__file__).resolve().parents[4]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RAW_ROOT = REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds006036_20260604_132747"
DEFAULT_RESULTS_ROOT = ARTICLE_DIR / "results" / "block_jacobian_exploration_132747"
PARTICIPANTS_PATH = ARTICLE_DIR / "metadata" / "participants.tsv"
DATASET = "ds006036"

GROUP_LABELS = {
    "A": "AD",
    "C": "Healthy",
    "F": "FTD",
}
CONTRAST_GROUPS = {
    "AD_vs_Healthy": ("A", "C"),
    "FTD_vs_Healthy": ("F", "C"),
    "AD_vs_FTD": ("A", "F"),
}
CORRELATION_COHORTS = {
    "Dementia_all": ("A", "F"),
    "AD_only": ("A",),
    "FTD_only": ("F",),
}
PAIR_ORDER = {"m": 0, "d": 1, "e": 2}
ANALYSIS_CONTEXT_COLUMNS = [
    "analysis_type",
    "analysis_label",
    "surface",
    "network",
    "source_group",
    "target_group",
    "pair_label",
    "pair_family",
    "pair_family_kind",
    "is_diagonal",
    "metric",
]
METRIC_COLUMNS = (
    "block_trace_mean",
    "block_frobenius_mean",
    "block_anisotropy_mean",
    "c_sym_mean",
    "c_rot_mean",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Explore ds006036 photic block-Jacobian surfaces.")
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    return parser.parse_args()


def _sanitize_columns(columns: Iterable[object]) -> list[str]:
    cleaned: list[str] = []
    for column in columns:
        text = str(column).replace("\ufeff", "").replace("\xa0", " ").strip()
        cleaned.append(" ".join(text.split()))
    return cleaned


def load_participants() -> pd.DataFrame:
    phenos = pd.read_csv(PARTICIPANTS_PATH, sep="\t")
    phenos.columns = _sanitize_columns(phenos.columns)
    phenos = phenos.rename(
        columns={
            "participant_id": "subject_id",
            "Gender": "gender",
            "Age": "age",
            "Group": "group",
            "MMSE": "mmse",
        }
    )
    phenos["age"] = pd.to_numeric(phenos["age"], errors="coerce")
    phenos["mmse"] = pd.to_numeric(phenos["mmse"], errors="coerce")
    phenos["group"] = phenos["group"].astype(str)
    phenos["group_label"] = phenos["group"].map(GROUP_LABELS).fillna(phenos["group"])
    return phenos


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


def _cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    left = left[np.isfinite(left)]
    right = right[np.isfinite(right)]
    if left.size < 2 or right.size < 2:
        return float("nan")
    pooled = ((left.size - 1) * np.var(left, ddof=1) + (right.size - 1) * np.var(right, ddof=1)) / (
        left.size + right.size - 2
    )
    if pooled <= 0 or not np.isfinite(pooled):
        return float("nan")
    return float((np.mean(left) - np.mean(right)) / np.sqrt(pooled))


def _pair_sort_key(value: Any) -> tuple[int, str]:
    label = str(value)
    return (PAIR_ORDER.get(label, 99), label)


def _pair_label_sort_key(value: Any) -> tuple[tuple[int, str], tuple[int, str]]:
    text = str(value)
    if "->" in text:
        left, right = text.split("->", 1)
        return (_pair_sort_key(left), _pair_sort_key(right))
    if "<->" in text:
        left, right = text.split("<->", 1)
        return (_pair_sort_key(left), _pair_sort_key(right))
    return (_pair_sort_key(text), _pair_sort_key(text))


def _canonical_pair_family_label(source: Any, target: Any) -> str:
    left = str(source)
    right = str(target)
    if left == right:
        return f"{left}->{right}"
    ordered = sorted((left, right), key=_pair_sort_key)
    return f"{ordered[0]}<->{ordered[1]}"


def _melt_block_metrics(
    frame: pd.DataFrame,
    *,
    analysis_type: str,
    analysis_label: str,
    surface: str,
    network_column: str | None,
    source_column: str,
    target_column: str,
    extra_context: dict[str, Any] | None = None,
) -> pd.DataFrame:
    id_vars = ["subject_id", "condition_label", "task_label", "n_timepoints", source_column, target_column]
    if network_column is not None:
        id_vars.append(network_column)
    melted = frame.melt(
        id_vars=id_vars,
        value_vars=[column for column in METRIC_COLUMNS if column in frame.columns],
        var_name="metric",
        value_name="value",
    )
    melted["value"] = pd.to_numeric(melted["value"], errors="coerce")
    melted = melted[melted["value"].notna()].copy()
    melted["analysis_type"] = analysis_type
    melted["analysis_label"] = analysis_label
    melted["surface"] = surface
    melted["source_group"] = melted[source_column].astype(str)
    melted["target_group"] = melted[target_column].astype(str)
    melted["pair_label"] = melted["source_group"] + "->" + melted["target_group"]
    melted["network"] = melted[network_column].astype(str) if network_column is not None else "global"
    if extra_context:
        for key, value in extra_context.items():
            melted[key] = value
    drop_cols = [source_column, target_column]
    if network_column is not None:
        drop_cols.append(network_column)
    return melted.drop(columns=drop_cols, errors="ignore").reset_index(drop=True)


def load_block_metric_frame(raw_root: Path, phenos: pd.DataFrame) -> pd.DataFrame:
    global_matches = sorted(raw_root.glob("stratified_block_jacobians_subjects*.csv"))
    regional_matches = sorted(raw_root.glob("regional_block_jacobians_subjects*.csv"))
    if not global_matches or not regional_matches:
        raise FileNotFoundError(f"Missing block Jacobian CSV exports under {raw_root}")
    global_path = global_matches[-1]
    regional_path = regional_matches[-1]
    global_frame = pd.read_csv(global_path)
    regional_frame = pd.read_csv(regional_path)

    global_frame = global_frame.rename(columns={"out_group": "source_group_raw", "in_group": "target_group_raw"})
    regional_frame = regional_frame.rename(columns={"source_block": "source_group_raw", "target_block": "target_group_raw"})

    global_metrics = _melt_block_metrics(
        global_frame,
        analysis_type="global_block_jacobian_9d",
        analysis_label="Global 9D block Jacobian",
        surface="global_9d",
        network_column=None,
        source_column="source_group_raw",
        target_column="target_group_raw",
    )
    regional_metrics = _melt_block_metrics(
        regional_frame,
        analysis_type="regional_block_jacobian_mde",
        analysis_label="Regional m/d/e family block Jacobian",
        surface="regional_mde",
        network_column="network_label",
        source_column="source_group_raw",
        target_column="target_group_raw",
    )
    metrics = pd.concat([global_metrics, regional_metrics], ignore_index=True)
    metrics = metrics.merge(
        phenos[["subject_id", "group", "group_label", "age", "gender", "mmse"]],
        on="subject_id",
        how="left",
    )
    metrics["is_diagonal"] = metrics["source_group"] == metrics["target_group"]
    return metrics


def build_unique_family_metric_frame(metric_frame: pd.DataFrame) -> pd.DataFrame:
    if metric_frame.empty:
        return metric_frame.copy()
    family_frame = metric_frame.copy()
    family_frame["pair_family"] = [
        _canonical_pair_family_label(source, target)
        for source, target in zip(family_frame["source_group"], family_frame["target_group"])
    ]
    family_frame["pair_family_kind"] = np.where(family_frame["is_diagonal"], "diagonal", "off_diagonal")
    group_cols = [
        "subject_id",
        "condition_label",
        "task_label",
        "n_timepoints",
        "analysis_type",
        "analysis_label",
        "surface",
        "network",
        "metric",
        "pair_family",
        "pair_family_kind",
        "is_diagonal",
        "group",
        "group_label",
        "age",
        "gender",
        "mmse",
    ]
    return (
        family_frame.groupby(group_cols, dropna=False, as_index=False)
        .agg(
            value=("value", "mean"),
            orientation_count=("pair_label", "nunique"),
            orientation_labels=(
                "pair_label",
                lambda values: "|".join(
                    sorted(
                        {str(value) for value in values if pd.notna(value)},
                        key=_pair_label_sort_key,
                    )
                ),
            ),
        )
        .reset_index(drop=True)
    )


def build_group_contrasts(metric_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group_cols = [column for column in ANALYSIS_CONTEXT_COLUMNS if column in metric_frame.columns]
    for contrast_name, (left_group, right_group) in CONTRAST_GROUPS.items():
        contrast_frame = metric_frame[metric_frame["group"].isin((left_group, right_group))].copy()
        for keys, group in contrast_frame.groupby(group_cols, dropna=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            row = dict(zip(group_cols, keys))
            left = group[group["group"] == left_group][["subject_id", "value"]].drop_duplicates(subset=["subject_id"])
            right = group[group["group"] == right_group][["subject_id", "value"]].drop_duplicates(subset=["subject_id"])
            if len(left) < 3 or len(right) < 3:
                continue
            stat = stats.mannwhitneyu(left["value"], right["value"], alternative="two-sided")
            row.update(
                {
                    "dataset": DATASET,
                    "contrast_name": contrast_name,
                    "left_group": GROUP_LABELS.get(left_group, left_group),
                    "right_group": GROUP_LABELS.get(right_group, right_group),
                    "left_n": int(len(left)),
                    "right_n": int(len(right)),
                    "left_mean": float(left["value"].mean()),
                    "right_mean": float(right["value"].mean()),
                    "left_median": float(left["value"].median()),
                    "right_median": float(right["value"].median()),
                    "effect_size": _cohens_d(left["value"].to_numpy(), right["value"].to_numpy()),
                    "effect_estimate": float(left["value"].mean() - right["value"].mean()),
                    "p_value": float(stat.pvalue),
                }
            )
            rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["q_value"] = out.groupby(["contrast_name", "analysis_type"], dropna=False)["p_value"].transform(_bh_fdr)
    out["sig_tier"] = out.apply(_sig_tier, axis=1)
    out["abs_effect"] = pd.to_numeric(out["effect_size"], errors="coerce").abs()
    return out.sort_values(
        ["contrast_name", "q_value", "p_value", "abs_effect"],
        ascending=[True, True, True, False],
        na_position="last",
    ).reset_index(drop=True)


def build_mmse_correlations(metric_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    keep = metric_frame[pd.notna(metric_frame["mmse"])].copy()
    group_cols = [column for column in ANALYSIS_CONTEXT_COLUMNS if column in keep.columns]
    for cohort_key, groups in CORRELATION_COHORTS.items():
        cohort = keep[keep["group"].isin(groups)].copy()
        for keys, group in cohort.groupby(group_cols, dropna=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            row = dict(zip(group_cols, keys))
            work = group[["subject_id", "value", "mmse"]].dropna().drop_duplicates(subset=["subject_id"])
            if len(work) < 4 or work["value"].nunique() < 2 or work["mmse"].nunique() < 2:
                continue
            spearman_rho, spearman_p = stats.spearmanr(work["value"], work["mmse"])
            pearson_r, pearson_p = stats.pearsonr(work["value"], work["mmse"])
            row.update(
                {
                    "dataset": DATASET,
                    "cohort_key": cohort_key,
                    "n_subjects": int(len(work)),
                    "spearman_rho": float(spearman_rho) if np.isfinite(spearman_rho) else np.nan,
                    "pearson_r": float(pearson_r) if np.isfinite(pearson_r) else np.nan,
                    "p_value": float(spearman_p) if np.isfinite(spearman_p) else np.nan,
                    "pearson_p": float(pearson_p) if np.isfinite(pearson_p) else np.nan,
                }
            )
            rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["q_value"] = out.groupby(["cohort_key", "analysis_type"], dropna=False)["p_value"].transform(_bh_fdr)
    out["sig_tier"] = out.apply(_sig_tier, axis=1)
    out["abs_spearman_rho"] = pd.to_numeric(out["spearman_rho"], errors="coerce").abs()
    return out.sort_values(
        ["cohort_key", "q_value", "p_value", "abs_spearman_rho"],
        ascending=[True, True, True, False],
        na_position="last",
    ).reset_index(drop=True)


def _context_pair_label(row: pd.Series) -> str:
    for column in ("pair_family", "pair_label"):
        value = row.get(column)
        if pd.notna(value) and str(value):
            return str(value)
    return "unknown"


def _top_rows_markdown(frame: pd.DataFrame, *, value_column: str, limit: int = 8) -> list[str]:
    if frame.empty:
        return ["- No rows passed the current scan."]
    lines: list[str] = []
    for _, row in frame.head(limit).iterrows():
        context = f"{row['analysis_label']} / {row['metric']} / `{row['network']}` / `{_context_pair_label(row)}`"
        if value_column == "effect_size":
            lines.append(
                f"- `{row['contrast_name']}`: {context}, d={float(row['effect_size']):.3f}, "
                f"p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}"
            )
        else:
            lines.append(
                f"- `{row['cohort_key']}`: {context}, rho={float(row['spearman_rho']):.3f}, "
                f"p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}"
            )
    return lines


def build_summary_markdown(
    metric_frame: pd.DataFrame,
    contrasts: pd.DataFrame,
    correlations: pd.DataFrame,
    raw_root: Path,
) -> str:
    lines = [
        "# Exploratory block-Jacobian check",
        "",
        f"- raw root: `{raw_root}`",
        f"- subject-metric rows: `{len(metric_frame)}`",
        f"- surfaces: `{', '.join(sorted(metric_frame['analysis_label'].dropna().astype(str).unique().tolist()))}`",
        "",
    ]
    if not metric_frame.empty:
        coverage = (
            metric_frame.groupby(["analysis_label", "metric"], dropna=False)["subject_id"]
            .nunique()
            .reset_index(name="n_subjects")
            .sort_values(["analysis_label", "metric"])
        )
        lines.extend(["## Coverage", ""])
        for _, row in coverage.iterrows():
            lines.append(f"- `{row['analysis_label']}` / `{row['metric']}`: {int(row['n_subjects'])} subjects")
    lines.extend(["", "## Group contrasts", ""])
    corrected = contrasts[contrasts["q_value"] <= 0.05].copy() if not contrasts.empty else pd.DataFrame()
    if corrected.empty:
        lines.append("- No corrected group rows at `q <= 0.05` in this exploratory scan.")
    else:
        lines.extend(_top_rows_markdown(corrected.sort_values(["q_value", "p_value", "abs_effect"]), value_column="effect_size"))
    lines.extend(["", "## MMSE correlations", ""])
    corrected_mmse = correlations[correlations["q_value"] <= 0.05].copy() if not correlations.empty else pd.DataFrame()
    if corrected_mmse.empty:
        lines.append("- No corrected MMSE rows at `q <= 0.05` in this exploratory scan.")
    else:
        lines.extend(
            _top_rows_markdown(
                corrected_mmse.sort_values(["q_value", "p_value", "abs_spearman_rho"]),
                value_column="spearman_rho",
            )
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This scan is run-level rather than frequency-stratified; the exported block-Jacobian contracts are whole-run summaries.",
            "- BH-FDR is applied within `contrast x analysis_type` for group rows and within `cohort x analysis_type` for MMSE rows.",
            "- Use this pass as a triage surface for article-vs-appendix decisions rather than as a finalized claim set.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_unique_family_summary_markdown(
    *,
    raw_root: Path,
    original_contrasts: pd.DataFrame,
    original_correlations: pd.DataFrame,
    unique_metric_frame: pd.DataFrame,
    unique_contrasts: pd.DataFrame,
    unique_correlations: pd.DataFrame,
) -> str:
    original_group_hits = int((original_contrasts["q_value"] <= 0.05).sum()) if not original_contrasts.empty else 0
    original_mmse_hits = int((original_correlations["q_value"] <= 0.05).sum()) if not original_correlations.empty else 0
    unique_group_hits = int((unique_contrasts["q_value"] <= 0.05).sum()) if not unique_contrasts.empty else 0
    unique_mmse_hits = int((unique_correlations["q_value"] <= 0.05).sum()) if not unique_correlations.empty else 0
    lines = [
        "# Unique block-family appendix summary",
        "",
        f"- raw root: `{raw_root}`",
        "- Deduplication rule: mirrored off-diagonal pairs such as `m->d` and `d->m` are collapsed into an unordered family such as `m<->d`.",
        "- Family-level values are formed by averaging available mirrored orientations within each subject before running statistics.",
        f"- unique-family subject-metric rows: `{len(unique_metric_frame)}`",
        f"- corrected group rows: `{original_group_hits}` raw pair rows -> `{unique_group_hits}` unique-family rows",
        f"- corrected MMSE rows: `{original_mmse_hits}` raw pair rows -> `{unique_mmse_hits}` unique-family rows",
        "",
        "## Group contrasts",
        "",
    ]
    corrected_group = unique_contrasts[unique_contrasts["q_value"] <= 0.05].copy() if not unique_contrasts.empty else pd.DataFrame()
    if corrected_group.empty:
        lines.append("- No unique-family group rows survive `q <= 0.05`.")
    else:
        count_frame = (
            corrected_group.groupby(["contrast_name", "analysis_label"], dropna=False)
            .size()
            .reset_index(name="n_rows")
            .sort_values(["contrast_name", "analysis_label"])
        )
        for _, row in count_frame.iterrows():
            lines.append(f"- `{row['contrast_name']}` / `{row['analysis_label']}`: {int(row['n_rows'])} corrected unique families")
        lines.append("")
        lines.extend(_top_rows_markdown(corrected_group.sort_values(["q_value", "p_value", "abs_effect"]), value_column="effect_size"))
    lines.extend(["", "## MMSE correlations", ""])
    corrected_mmse = unique_correlations[unique_correlations["q_value"] <= 0.05].copy() if not unique_correlations.empty else pd.DataFrame()
    if corrected_mmse.empty:
        lines.append("- No unique-family MMSE row survives `q <= 0.05`.")
    else:
        count_frame = (
            corrected_mmse.groupby(["cohort_key", "analysis_label"], dropna=False)
            .size()
            .reset_index(name="n_rows")
            .sort_values(["cohort_key", "analysis_label"])
        )
        for _, row in count_frame.iterrows():
            lines.append(f"- `{row['cohort_key']}` / `{row['analysis_label']}`: {int(row['n_rows'])} corrected unique families")
        lines.append("")
        lines.extend(
            _top_rows_markdown(
                corrected_mmse.sort_values(["q_value", "p_value", "abs_spearman_rho"]),
                value_column="spearman_rho",
            )
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Diagonal families such as `m->m` are unchanged by this condensation step.",
            "- Off-diagonal family labels use the unordered notation `m<->d`, `m<->e`, and `d<->e`.",
            "- This appendix-oriented pass is easier to narrate than the raw oriented-pair surface and is the better candidate if block-Jacobian material is carried forward.",
        ]
    )
    return "\n".join(lines) + "\n"


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


def write_outputs(raw_root: Path, results_root: Path) -> dict[str, str]:
    results_root.mkdir(parents=True, exist_ok=True)
    phenos = load_participants()
    metric_frame = load_block_metric_frame(raw_root, phenos)
    contrasts = build_group_contrasts(metric_frame)
    correlations = build_mmse_correlations(metric_frame)
    unique_metric_frame = build_unique_family_metric_frame(metric_frame)
    unique_contrasts = build_group_contrasts(unique_metric_frame)
    unique_correlations = build_mmse_correlations(unique_metric_frame)

    metrics_path = results_root / "block_jacobian_subject_metrics_long.csv"
    contrasts_path = results_root / "block_jacobian_group_contrasts.csv"
    mmse_path = results_root / "block_jacobian_mmse_correlations.csv"
    summary_path = results_root / "block_jacobian_exploration_summary.md"
    unique_metrics_path = results_root / "block_jacobian_unique_family_subject_metrics_long.csv"
    unique_contrasts_path = results_root / "block_jacobian_unique_family_group_contrasts.csv"
    unique_mmse_path = results_root / "block_jacobian_unique_family_mmse_correlations.csv"
    unique_summary_path = results_root / "block_jacobian_unique_family_appendix_summary.md"
    manifest_path = results_root / "block_jacobian_exploration_manifest.json"

    metric_frame.to_csv(metrics_path, index=False)
    contrasts.to_csv(contrasts_path, index=False)
    correlations.to_csv(mmse_path, index=False)
    unique_metric_frame.to_csv(unique_metrics_path, index=False)
    unique_contrasts.to_csv(unique_contrasts_path, index=False)
    unique_correlations.to_csv(unique_mmse_path, index=False)
    summary_path.write_text(build_summary_markdown(metric_frame, contrasts, correlations, raw_root), encoding="utf-8")
    unique_summary_path.write_text(
        build_unique_family_summary_markdown(
            raw_root=raw_root,
            original_contrasts=contrasts,
            original_correlations=correlations,
            unique_metric_frame=unique_metric_frame,
            unique_contrasts=unique_contrasts,
            unique_correlations=unique_correlations,
        ),
        encoding="utf-8",
    )

    manifest = {
        "dataset": DATASET,
        "raw_root": str(raw_root),
        "results_root": str(results_root),
        "participants_path": str(PARTICIPANTS_PATH),
        "n_metric_rows": int(len(metric_frame)),
        "n_group_contrast_rows": int(len(contrasts)),
        "n_mmse_rows": int(len(correlations)),
        "n_unique_family_metric_rows": int(len(unique_metric_frame)),
        "n_unique_family_group_contrast_rows": int(len(unique_contrasts)),
        "n_unique_family_mmse_rows": int(len(unique_correlations)),
        "analysis_types": sorted(metric_frame["analysis_type"].dropna().astype(str).unique().tolist()),
        "networks": sorted(metric_frame["network"].dropna().astype(str).unique().tolist()),
        "metrics": sorted(metric_frame["metric"].dropna().astype(str).unique().tolist()),
        "corrected_group_rows_q05": int((contrasts["q_value"] <= 0.05).sum()) if not contrasts.empty else 0,
        "corrected_mmse_rows_q05": int((correlations["q_value"] <= 0.05).sum()) if not correlations.empty else 0,
        "corrected_unique_family_group_rows_q05": int((unique_contrasts["q_value"] <= 0.05).sum()) if not unique_contrasts.empty else 0,
        "corrected_unique_family_mmse_rows_q05": int((unique_correlations["q_value"] <= 0.05).sum()) if not unique_correlations.empty else 0,
        "output_files": {
            "subject_metrics_long": str(metrics_path),
            "group_contrasts": str(contrasts_path),
            "mmse_correlations": str(mmse_path),
            "summary_md": str(summary_path),
            "unique_family_subject_metrics_long": str(unique_metrics_path),
            "unique_family_group_contrasts": str(unique_contrasts_path),
            "unique_family_mmse_correlations": str(unique_mmse_path),
            "unique_family_summary_md": str(unique_summary_path),
        },
    }
    manifest_path.write_text(json.dumps(_json_ready(manifest), indent=2), encoding="utf-8")
    return {
        "metrics_path": str(metrics_path),
        "contrasts_path": str(contrasts_path),
        "mmse_path": str(mmse_path),
        "summary_path": str(summary_path),
        "unique_metrics_path": str(unique_metrics_path),
        "unique_contrasts_path": str(unique_contrasts_path),
        "unique_mmse_path": str(unique_mmse_path),
        "unique_summary_path": str(unique_summary_path),
        "manifest_path": str(manifest_path),
    }


def main() -> None:
    args = parse_args()
    outputs = write_outputs(args.raw_root, args.results_root)
    print("Exploratory photic block-Jacobian check completed.")
    print(f"summary={outputs['summary_path']}")
    print(f"unique_family_summary={outputs['unique_summary_path']}")
    print(f"manifest={outputs['manifest_path']}")


if __name__ == "__main__":
    main()
