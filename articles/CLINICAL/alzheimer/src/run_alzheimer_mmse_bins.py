from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats


DATASET = "ds004504"
REPO_ROOT = Path(__file__).resolve().parents[3]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "alzheimer_ds004504_20260521"
FALLBACK_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis"
RESULTS_ROOT = ARTICLE_DIR / "results"
PARTICIPANTS_PATH = ARTICLE_DIR / "metadata" / "ds004504_alzheimer_FTD_eeg" / "participants.tsv"

CONTEXT_COLUMNS = [
    "block_scope",
    "block_space",
    "source_group",
    "target_group",
    "source_dim",
    "target_dim",
]

BLOCK_SPECS = [
    ("emmi", "tier2_emmi", ["speed_median", "speed_mean", "mv_over_speed_median"]),
    (
        "mnj_3d",
        "global_mnps_jacobian_3d",
        ["spectral_radius_median", "spectral_radius_mean", "rotation_norm_median", "trace_median"],
    ),
    (
        "mnj_9d",
        "global_mnps_jacobian_9d",
        ["spectral_radius_median", "spectral_radius_mean", "rotation_norm_median", "anisotropy_abs_eig_median"],
    ),
    (
        "block_mnj",
        "global_mnps_jacobian_9d_block_jacobian",
        ["block_frobenius_mean", "block_trace_mean", "block_anisotropy_mean", "c_sym_mean", "c_rot_mean"],
    ),
]
COHORT_GROUPS = {
    "Dementia_all": ["A", "F"],
    "AD_only": ["A"],
    "FTD_only": ["F"],
}
SPLIT_SPECS = [
    ("mmse_median", "mmse_median_group", "Lower MMSE", "Higher MMSE"),
    ("mmse_tertiles_low_vs_mid", "mmse_tertile_group", "Lower tertile", "Middle tertile"),
    ("mmse_tertiles_low_vs_high", "mmse_tertile_group", "Lower tertile", "Upper tertile"),
    ("mmse_tertiles_mid_vs_high", "mmse_tertile_group", "Middle tertile", "Upper tertile"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run dementia-only MMSE bin analyses for ds004504.")
    parser.add_argument("--analysis-root", type=Path, default=None)
    parser.add_argument("--results-root", type=Path, default=RESULTS_ROOT)
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


def _cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    if left.size < 2 or right.size < 2:
        return float("nan")
    left_var = left.var(ddof=1)
    right_var = right.var(ddof=1)
    pooled_var = ((left.size - 1) * left_var + (right.size - 1) * right_var) / (left.size + right.size - 2)
    if not np.isfinite(pooled_var) or pooled_var <= 0:
        return float("nan")
    return float((right.mean() - left.mean()) / np.sqrt(pooled_var))


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
    if pd.notna(row.get("q_value")) and float(row["q_value"]) <= 0.05:
        return "q<=0.05"
    if pd.notna(row.get("p_value")) and float(row["p_value"]) < 0.05:
        return "p<0.05"
    if pd.notna(row.get("p_value")) and float(row["p_value"]) < 0.1:
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


def _pick_metric(frame: pd.DataFrame, preferred: list[str] | None = None) -> pd.Series:
    ordered = _sorted_results(frame)
    for metric in preferred or []:
        match = ordered[ordered["metric"] == metric]
        if not match.empty:
            return match.iloc[0]
    return ordered.iloc[0]


def _load_participants() -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    phenos = pd.read_csv(PARTICIPANTS_PATH, sep="\t")
    phenos["MMSE"] = pd.to_numeric(phenos["MMSE"], errors="coerce")
    phenos["Age"] = pd.to_numeric(phenos["Age"], errors="coerce")

    thresholds: dict[str, dict[str, float]] = {}
    for cohort_key, groups in COHORT_GROUPS.items():
        cohort = phenos[phenos["Group"].isin(groups)].copy()
        if cohort.empty:
            continue
        median_cut = float(cohort["MMSE"].median())
        lower_tertile_cut = float(cohort["MMSE"].quantile(1.0 / 3.0))
        upper_tertile_cut = float(cohort["MMSE"].quantile(2.0 / 3.0))

        median_column = f"{cohort_key}_mmse_median_group"
        tertile_column = f"{cohort_key}_mmse_tertile_group"
        phenos[median_column] = pd.Series([None] * len(phenos), dtype=object)
        phenos[tertile_column] = pd.Series([None] * len(phenos), dtype=object)

        cohort_mask = phenos["Group"].isin(groups)
        phenos.loc[cohort_mask & (phenos["MMSE"] <= median_cut), median_column] = "Lower MMSE"
        phenos.loc[cohort_mask & (phenos["MMSE"] > median_cut), median_column] = "Higher MMSE"

        phenos.loc[cohort_mask & (phenos["MMSE"] <= lower_tertile_cut), tertile_column] = "Lower tertile"
        phenos.loc[
            cohort_mask & (phenos["MMSE"] > lower_tertile_cut) & (phenos["MMSE"] <= upper_tertile_cut),
            tertile_column,
        ] = "Middle tertile"
        phenos.loc[cohort_mask & (phenos["MMSE"] > upper_tertile_cut), tertile_column] = "Upper tertile"

        thresholds[cohort_key] = {
            "median_cut": median_cut,
            "lower_tertile_cut": lower_tertile_cut,
            "upper_tertile_cut": upper_tertile_cut,
        }
    return phenos, thresholds


def _run_split_tests(
    frame: pd.DataFrame,
    cohort_key: str,
    split_name: str,
    split_column: str,
    left_label: str,
    right_label: str,
) -> pd.DataFrame:
    group_cols = ["analysis_type", "metric"] + [column for column in CONTEXT_COLUMNS if column in frame.columns]
    rows: list[dict[str, object]] = []

    work = frame[frame["cohort_key"] == cohort_key].copy()
    work = work[work[split_column].isin([left_label, right_label])].copy()

    for keys, sub in work.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        context = dict(zip(group_cols, keys))
        left = pd.to_numeric(sub.loc[sub[split_column] == left_label, "value"], errors="coerce").dropna()
        right = pd.to_numeric(sub.loc[sub[split_column] == right_label, "value"], errors="coerce").dropna()
        if len(left) < 3 or len(right) < 3:
            continue
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Precision loss occurred in moment calculation due to catastrophic cancellation.*",
                category=RuntimeWarning,
            )
            t_stat, p_value = stats.ttest_ind(
                left.to_numpy(),
                right.to_numpy(),
                equal_var=False,
                nan_policy="omit",
            )
        row: dict[str, object] = {
            "dataset": DATASET,
            "cohort_key": cohort_key,
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
            "t_stat": float(t_stat) if np.isfinite(t_stat) else np.nan,
            "p_value": float(p_value) if np.isfinite(p_value) else np.nan,
        }
        for column in CONTEXT_COLUMNS:
            row[column] = context.get(column)
        rows.append(row)

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["q_value"] = result.groupby("analysis_type", dropna=False)["p_value"].transform(_bh_fdr)
    result["sig_tier"] = result.apply(_sig_tier, axis=1)
    return result


def _summarize_split_results(cohort_key: str, split_name: str, frame: pd.DataFrame, phenos: pd.DataFrame) -> list[dict[str, object]]:
    count_column = (
        f"{cohort_key}_mmse_median_group"
        if split_name == "mmse_median"
        else f"{cohort_key}_mmse_tertile_group"
    )
    counts = phenos.loc[phenos["Group"].isin(COHORT_GROUPS[cohort_key]), count_column].value_counts(dropna=False).to_dict()

    rows: list[dict[str, object]] = []
    for block_key, analysis_type, preferred in BLOCK_SPECS:
        sub = frame[frame["analysis_type"] == analysis_type].copy()
        if sub.empty:
            continue
        pick = _pick_metric(sub, preferred)
        rows.append(
            {
                "dataset": DATASET,
                "cohort_key": cohort_key,
                "split_name": split_name,
                "block_key": block_key,
                "analysis_type": analysis_type,
                "metric": pick["metric"],
                "effect_size": float(pick["effect_size"]),
                "effect_estimate": float(pick["effect_estimate"]),
                "p_value": float(pick["p_value"]),
                "q_value": float(pick["q_value"]) if pd.notna(pick["q_value"]) else np.nan,
                "left_n": int(pick["left_n"]) if pd.notna(pick["left_n"]) else None,
                "right_n": int(pick["right_n"]) if pd.notna(pick["right_n"]) else None,
                "left_mean": float(pick["left_mean"]) if pd.notna(pick["left_mean"]) else np.nan,
                "right_mean": float(pick["right_mean"]) if pd.notna(pick["right_mean"]) else np.nan,
                "left_group": pick["left_group"],
                "right_group": pick["right_group"],
                "sig_tier": _sig_tier(pick),
                "group_counts": json.dumps({str(k): int(v) for k, v in counts.items() if k is not None}, sort_keys=True),
                "block_scope": pick.get("block_scope"),
                "block_space": pick.get("block_space"),
                "source_group": pick.get("source_group"),
                "target_group": pick.get("target_group"),
                "source_dim": pick.get("source_dim"),
                "target_dim": pick.get("target_dim"),
            }
        )
    return rows


def _build_summary_markdown(summary: pd.DataFrame, thresholds: dict[str, dict[str, float]]) -> str:
    lines = [
        "# Cohort MMSE bin summary",
        "",
    ]
    if summary.empty:
        lines.append("No MMSE-bin contrasts were estimable.")
        lines.append("")
        return "\n".join(lines)

    for cohort_key in ("Dementia_all", "AD_only", "FTD_only"):
        cohort_thresholds = thresholds.get(cohort_key)
        cohort_summary = summary[summary["cohort_key"] == cohort_key].copy()
        if cohort_thresholds is None or cohort_summary.empty:
            continue
        lines.extend(
            [
                f"## {cohort_key}",
                "",
                f"- Median cut: `{cohort_thresholds['median_cut']:.3f}`",
                f"- Lower tertile cut: `{cohort_thresholds['lower_tertile_cut']:.3f}`",
                f"- Upper tertile cut: `{cohort_thresholds['upper_tertile_cut']:.3f}`",
                "",
            ]
        )
        for split_name, _, _, _ in SPLIT_SPECS:
            sub = cohort_summary[cohort_summary["split_name"] == split_name].copy()
            if sub.empty:
                continue
            lines.extend([f"### {split_name}", ""])
            for _, row in sub.iterrows():
                extra = []
                if pd.notna(row.get("source_group")) or pd.notna(row.get("target_group")):
                    extra.append(f"block={row.get('source_group')}->{row.get('target_group')}")
                if pd.notna(row.get("block_space")):
                    extra.append(f"space={row.get('block_space')}")
                suffix = f" ({', '.join(extra)})" if extra else ""
                lines.append(
                    f"- `{row['block_key']}` / `{row['metric']}`{suffix}: "
                    f"{row['left_group']} vs {row['right_group']}, "
                    f"d={float(row['effect_size']):.4f}, p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}"
                )
            lines.append("")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    roots = _analysis_roots(args.analysis_root)
    results_root = args.results_root
    results_root.mkdir(parents=True, exist_ok=True)

    subject_metrics_path = _latest_parquet(roots, "subject_metrics")
    subject_metrics = pd.read_parquet(subject_metrics_path)
    phenos, thresholds = _load_participants()

    merged = subject_metrics.merge(
        phenos[
            [
                "participant_id",
                "Group",
                "MMSE",
                "Age",
                "Gender",
                *[f"{cohort_key}_mmse_median_group" for cohort_key in COHORT_GROUPS],
                *[f"{cohort_key}_mmse_tertile_group" for cohort_key in COHORT_GROUPS],
            ]
        ],
        left_on="subject_id",
        right_on="participant_id",
        how="left",
    ).drop(columns=["participant_id"], errors="ignore")

    detail_frames: list[pd.DataFrame] = []
    summary_rows: list[dict[str, object]] = []

    for cohort_key in ("Dementia_all", "AD_only", "FTD_only"):
        cohort_groups = COHORT_GROUPS[cohort_key]
        cohort_frame = merged[merged["Group"].isin(cohort_groups)].copy()
        cohort_frame["cohort_key"] = cohort_key
        for split_name, split_kind, left_label, right_label in SPLIT_SPECS:
            split_column = (
                f"{cohort_key}_mmse_median_group"
                if split_kind == "mmse_median_group"
                else f"{cohort_key}_mmse_tertile_group"
            )
            result = _run_split_tests(cohort_frame, cohort_key, split_name, split_column, left_label, right_label)
            if result.empty:
                continue
            detail_frames.append(result)
            summary_rows.extend(_summarize_split_results(cohort_key, split_name, result, phenos))

    summary = pd.DataFrame(summary_rows)
    detail = pd.concat(detail_frames, ignore_index=True) if detail_frames else pd.DataFrame()

    if not detail.empty:
        detail.to_csv(results_root / "cohort_mmse_bin_detail.csv", index=False)
        detail.to_csv(results_root / "dementia_mmse_bin_detail.csv", index=False)
    summary.to_csv(results_root / "cohort_mmse_bin_summary.csv", index=False)
    summary.to_csv(results_root / "dementia_mmse_bin_summary.csv", index=False)

    manifest = {
        "dataset": DATASET,
        "subject_metrics_path": str(subject_metrics_path),
        "participants_path": str(PARTICIPANTS_PATH),
        "thresholds": thresholds,
        "cohort_group_counts": {
            cohort_key: {
                "median_groups": {
                    str(k): int(v)
                    for k, v in phenos.loc[
                        phenos["Group"].isin(groups),
                        f"{cohort_key}_mmse_median_group",
                    ].value_counts(dropna=False).to_dict().items()
                    if k is not None
                },
                "tertile_groups": {
                    str(k): int(v)
                    for k, v in phenos.loc[
                        phenos["Group"].isin(groups),
                        f"{cohort_key}_mmse_tertile_group",
                    ].value_counts(dropna=False).to_dict().items()
                    if k is not None
                },
            }
            for cohort_key, groups in COHORT_GROUPS.items()
        },
        "split_specs": [
            {
                "split_name": split_name,
                "left_group": left_label,
                "right_group": right_label,
            }
            for split_name, _, left_label, right_label in SPLIT_SPECS
        ],
    }
    (results_root / "cohort_mmse_bin_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (results_root / "dementia_mmse_bin_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    summary_markdown = _build_summary_markdown(summary, thresholds)
    (results_root / "cohort_mmse_bin_summary.md").write_text(
        summary_markdown,
        encoding="utf-8",
    )
    (results_root / "dementia_mmse_bin_summary.md").write_text(
        summary_markdown,
        encoding="utf-8",
    )

    print(f"Wrote cohort MMSE-bin summary to {results_root / 'cohort_mmse_bin_summary.csv'}")
    print(f"Wrote cohort MMSE-bin detail to {results_root / 'cohort_mmse_bin_detail.csv'}")


if __name__ == "__main__":
    main()
