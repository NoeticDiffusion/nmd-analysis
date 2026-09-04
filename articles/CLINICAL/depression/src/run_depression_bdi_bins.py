from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats


DATASET = "ds003478"
REPO_ROOT = Path(__file__).resolve().parents[4]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "depression_ds003478_20260521"
FALLBACK_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis"
RESULTS_ROOT = ARTICLE_DIR / "results"
PARTICIPANTS_PATH = ARTICLE_DIR / "metadata" / "participants.tsv"

CONTEXT_COLUMNS = [
    "block_scope",
    "block_space",
    "source_group",
    "target_group",
    "source_dim",
    "target_dim",
]
BLOCK_SPECS = [
    ("mnps_3d", "global_mnps_3d", ["d_median", "d_mean", "d_std", "m_std", "m_mean"]),
    ("mnps_9d", "global_mnps_9d", ["d_s_mean", "e_m_std", "d_l_std", "d_s_median", "m_a_mean"]),
    (
        "mnj_3d",
        "global_mnps_jacobian_3d",
        ["spectral_radius_median", "spectral_radius_mean", "rotation_norm_median", "trace_median"],
    ),
    (
        "mnj_9d",
        "global_mnps_jacobian_9d",
        ["rotational_power_mean", "rotational_power_median", "frobenius_norm_median", "rotation_norm_median"],
    ),
    (
        "block_mnj",
        "global_mnps_jacobian_9d_block_jacobian",
        ["block_anisotropy_mean", "block_trace_mean", "block_frobenius_mean"],
    ),
    (
        "reachability",
        "reachability_cones",
        (
            "tube_log_eig_var_mean",
            "tube_log_eig_var_median",
            "cone_log_eig_var_h3_median",
            "cone_log_eig_var_h4_median",
            "tube_log_det_split_half_a_median",
            "cone_log_det_h2_median",
        ),
    ),
    ("emmi", "tier2_emmi", ["mv_median", "mv_abs_median", "mv_over_speed_median", "speed_median"]),
    ("distribution", "dist_summary", ["e_m_mad_sigma", "e_m_mad", "e_m_iqr", "d_skewness", "d_kurtosis_excess"]),
]
BDI_BAND_ORDER = ["BDI 0-13", "BDI 14-19", "BDI 20-63"]
SPLIT_SPECS = [
    ("bdi_0_13_vs_14_19", "BDI 0-13", "BDI 14-19"),
    ("bdi_0_13_vs_20_63", "BDI 0-13", "BDI 20-63"),
    ("bdi_14_19_vs_20_63", "BDI 14-19", "BDI 20-63"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run clinical BDI-bin analyses for ds003478.")
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


def _pick_metric(frame: pd.DataFrame, preferred: list[str] | tuple[str, ...] | None = None) -> pd.Series:
    ordered = _sorted_results(frame)
    for metric in preferred or []:
        match = ordered[ordered["metric"] == metric]
        if not match.empty:
            return match.iloc[0]
    return ordered.iloc[0]


def _load_participants() -> pd.DataFrame:
    phenos = pd.read_csv(PARTICIPANTS_PATH, sep="\t")
    phenos["BDI"] = pd.to_numeric(phenos["BDI"], errors="coerce")
    phenos["age"] = pd.to_numeric(phenos["age"], errors="coerce")
    phenos["female"] = pd.to_numeric(phenos["sex"], errors="coerce").eq(1)
    phenos["bdi_band"] = pd.cut(
        phenos["BDI"],
        bins=[-0.1, 13, 19, 63],
        labels=BDI_BAND_ORDER,
        include_lowest=True,
    )
    phenos["bdi_band"] = phenos["bdi_band"].astype(object)
    return phenos


def _run_split_tests(frame: pd.DataFrame, split_name: str, left_label: str, right_label: str) -> pd.DataFrame:
    group_cols = ["analysis_type", "metric"] + [column for column in CONTEXT_COLUMNS if column in frame.columns]
    rows: list[dict[str, object]] = []

    work = frame[frame["bdi_band"].isin([left_label, right_label])].copy()
    for keys, sub in work.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        context = dict(zip(group_cols, keys))
        left = pd.to_numeric(sub.loc[sub["bdi_band"] == left_label, "value"], errors="coerce").dropna()
        right = pd.to_numeric(sub.loc[sub["bdi_band"] == right_label, "value"], errors="coerce").dropna()
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


def _summarize_split_results(split_name: str, frame: pd.DataFrame, phenos: pd.DataFrame) -> list[dict[str, object]]:
    counts = phenos["bdi_band"].value_counts(dropna=False).to_dict()
    rows: list[dict[str, object]] = []
    for block_key, analysis_type, preferred in BLOCK_SPECS:
        sub = frame[frame["analysis_type"] == analysis_type].copy()
        if sub.empty:
            continue
        pick = _pick_metric(sub, preferred)
        rows.append(
            {
                "dataset": DATASET,
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
                "group_counts": json.dumps({str(k): int(v) for k, v in counts.items() if pd.notna(k)}, sort_keys=True),
                "block_scope": pick.get("block_scope"),
                "block_space": pick.get("block_space"),
                "source_group": pick.get("source_group"),
                "target_group": pick.get("target_group"),
                "source_dim": pick.get("source_dim"),
                "target_dim": pick.get("target_dim"),
            }
        )
    return rows


def _build_summary_markdown(summary: pd.DataFrame) -> str:
    lines = [
        "# Clinical BDI bin summary",
        "",
        "- Bands: `BDI 0-13`, `BDI 14-19`, `BDI 20-63`",
        "",
    ]
    if summary.empty:
        lines.extend(["No BDI-bin contrasts were estimable.", ""])
        return "\n".join(lines)

    for split_name in ("bdi_0_13_vs_14_19", "bdi_0_13_vs_20_63", "bdi_14_19_vs_20_63"):
        sub = summary[summary["split_name"] == split_name].copy()
        if sub.empty:
            continue
        lines.extend([f"## {split_name}", ""])
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
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    roots = _analysis_roots(args.analysis_root)
    results_root = args.results_root
    results_root.mkdir(parents=True, exist_ok=True)

    subject_metrics_path = _latest_parquet(roots, "subject_metrics")
    subject_metrics = pd.read_parquet(subject_metrics_path)
    phenos = _load_participants()

    merged = subject_metrics.merge(
        phenos[["participant_id", "BDI", "age", "female", "bdi_band"]],
        left_on="subject_id",
        right_on="participant_id",
        how="left",
    ).drop(columns=["participant_id"], errors="ignore")

    detail_frames: list[pd.DataFrame] = []
    summary_rows: list[dict[str, object]] = []
    for split_name, left_label, right_label in SPLIT_SPECS:
        result = _run_split_tests(merged, split_name, left_label, right_label)
        if result.empty:
            continue
        detail_frames.append(result)
        summary_rows.extend(_summarize_split_results(split_name, result, phenos))

    summary = pd.DataFrame(summary_rows)
    detail = pd.concat(detail_frames, ignore_index=True) if detail_frames else pd.DataFrame()

    if not detail.empty:
        detail.to_csv(results_root / "clinical_bdi_bin_detail.csv", index=False)
    summary.to_csv(results_root / "clinical_bdi_bin_summary.csv", index=False)

    manifest = {
        "dataset": DATASET,
        "subject_metrics_path": str(subject_metrics_path),
        "participants_path": str(PARTICIPANTS_PATH),
        "bdi_band_counts": {
            str(k): int(v) for k, v in phenos["bdi_band"].value_counts(dropna=False).to_dict().items() if pd.notna(k)
        },
        "split_specs": [
            {"split_name": split_name, "left_group": left_label, "right_group": right_label}
            for split_name, left_label, right_label in SPLIT_SPECS
        ],
    }
    (results_root / "clinical_bdi_bin_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (results_root / "clinical_bdi_bin_summary.md").write_text(_build_summary_markdown(summary), encoding="utf-8")

    print(f"Wrote clinical BDI-bin summary to {results_root / 'clinical_bdi_bin_summary.csv'}")
    print(f"Wrote clinical BDI-bin detail to {results_root / 'clinical_bdi_bin_detail.csv'}")


if __name__ == "__main__":
    main()
