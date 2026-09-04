"""Export a compact, article-local report for the paired hypoglycemia analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy import stats


REPO_ROOT = Path(__file__).resolve().parents[3]
ARTICLE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_ROOT = (
    REPO_ROOT
    / "data"
    / "raw"
    / "neuralmanifolddynamics_hypoglycemia_t1d_20260723_180515"
)
DEFAULT_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "hypoglycemia_t1d_20260723"
DEFAULT_RESULTS_ROOT = (
    ARTICLE_ROOT / "results" / "hypoglycemia_t1d_20260723"
)
FEATURES = [
    "eeg_delta",
    "eeg_theta",
    "eeg_alpha",
    "eeg_sample_entropy",
    "eeg_permutation_entropy",
    "eeg_hjorth_complexity",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--analysis-root", type=Path, default=DEFAULT_ANALYSIS_ROOT)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    return parser.parse_args()


def _decode(values: np.ndarray) -> list[str]:
    return [value.decode() if isinstance(value, bytes) else str(value) for value in values]


def _h5_feature_medians(raw_root: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for h5_path in sorted(raw_root.rglob("*.h5")):
        with h5py.File(h5_path, "r") as handle:
            mapped = json.loads(handle["participant/mapped_json"][()].decode())
            subject_id = str(handle.attrs["subject_id"])
            condition = str(mapped["task"])
            names = _decode(handle["features_raw/names"][:])
            values = np.asarray(handle["features_raw/values"][:], dtype=float)
        row: dict[str, object] = {"subject_id": subject_id, "condition": condition}
        for feature in FEATURES:
            if feature not in names:
                row[feature] = np.nan
                continue
            row[feature] = float(np.nanmedian(values[:, names.index(feature)]))
        rows.append(row)
    return pd.DataFrame(rows)


def _paired_feature_results(feature_medians: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for feature in FEATURES:
        pivot = feature_medians.pivot(index="subject_id", columns="condition", values=feature)
        if not {"euglycemia", "hypoglycemia"}.issubset(pivot.columns):
            continue
        paired = pivot[["euglycemia", "hypoglycemia"]].dropna()
        delta = paired["hypoglycemia"] - paired["euglycemia"]
        try:
            statistic, p_value = stats.wilcoxon(delta, alternative="two-sided")
        except ValueError:
            statistic, p_value = np.nan, np.nan
        sd = float(delta.std(ddof=1))
        records.append(
            {
                "analysis_type": "raw_eeg_feature",
                "metric": feature,
                "n_pairs": int(len(delta)),
                "euglycemia_median": float(paired["euglycemia"].median()),
                "hypoglycemia_median": float(paired["hypoglycemia"].median()),
                "effect_estimate": float(delta.mean()),
                "cohen_dz": float(delta.mean() / sd) if sd > 0 else np.nan,
                "wilcoxon_statistic": statistic,
                "p_value": p_value,
                "direction": "hypoglycemia_minus_euglycemia",
            }
        )
    result = pd.DataFrame(records)
    if not result.empty:
        result["q_value"] = _bh_fdr(result["p_value"])
    return result


def _bh_fdr(values: pd.Series) -> np.ndarray:
    p = values.to_numpy(dtype=float)
    order = np.argsort(p)
    ranked = p[order]
    adjusted = ranked * len(p) / np.arange(1, len(p) + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    out = np.empty_like(adjusted)
    out[order] = np.clip(adjusted, 0.0, 1.0)
    return out


def _latest_parquet(root: Path, token: str) -> Path:
    matches = sorted(root.glob(f"*{token}*.parquet"), key=lambda path: path.stat().st_mtime)
    if not matches:
        raise FileNotFoundError(f"No {token} parquet found in {root}.")
    return matches[-1]


def _write_report(
    output_path: Path,
    raw_features: pd.DataFrame,
    feature_results: pd.DataFrame,
    contrast_results: pd.DataFrame,
    qc_summary: pd.DataFrame,
) -> None:
    n_pairs = raw_features.pivot(index="subject_id", columns="condition", values="eeg_delta").dropna().shape[0]
    primary_metrics = {
        "global_mnps_3d": ["m_median", "d_median", "e_median"],
        "global_mnps_9d": [
            "m_a_median",
            "m_e_median",
            "m_o_median",
            "d_n_median",
            "d_l_median",
            "d_s_median",
            "e_e_median",
            "e_s_median",
            "e_m_median",
        ],
        "global_mnps_jacobian_3d": ["frobenius_norm_median", "rotation_norm_median", "trace_median"],
        "global_mnps_jacobian_9d": [
            "a_operator_norm_median",
            "frobenius_norm_median",
            "rotation_norm_median",
        ],
        "reachability_cones": ["tube_log_det_median", "tube_d_eff_median", "tube_kappa_median", "tube_dir_entropy_median", "tube_rotation_median"],
    }
    primary_ndt = pd.concat(
        [
            contrast_results[
                (contrast_results["analysis_type"] == analysis_type)
                & contrast_results["metric"].isin(metrics)
            ]
            for analysis_type, metrics in primary_metrics.items()
        ],
        ignore_index=True,
    )
    lines = [
        "# Hypoglycemia T1D: paired NDT analysis",
        "",
        "## Design and evidence status",
        "",
        f"- {n_pairs} complete subject pairs; contrast direction is hypoglycemia minus euglycemia.",
        "- This is an internal empirical analysis of discrete five-minute EEG excerpts.",
        "- It contains no continuous clamp trajectory, recovery segment, participant-level glucose value, or awareness subgroup metadata.",
        "- Cohort-anchored coordinates use a pooled eu+hy feature anchor; they are not euglycemia-anchored coordinates.",
        "- Reachability outputs are exploratory and validity-limited under the frozen split-half criteria; they are not confirmatory endpoints.",
        "",
        "## NDT contrast results",
        "",
        f"- Engine contrast rows: {len(contrast_results)}; the table below is the prespecified coordinate and audit subset.",
        f"- QC summary rows: {len(qc_summary)}.",
        "",
        "| analysis | metric | n_pairs | effect (HYPO-EU) | p | q |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, row in primary_ndt.sort_values(["analysis_type", "metric"]).iterrows():
        lines.append(
            f"| {row.get('analysis_type', '')} | {row.get('metric', '')} | "
            f"{row.get('n_pairs', np.nan)} | {row.get('effect_estimate', np.nan):.4g} | "
            f"{row.get('p_value', np.nan):.4g} | {row.get('q_value', np.nan):.4g} |"
        )
    lines += [
        "",
        "## Classical EEG sanity check",
        "",
        "| feature | n_pairs | effect (HYPO-EU) | Cohen dz | p | q |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in feature_results.sort_values("q_value", na_position="last").iterrows():
        lines.append(
            f"| {row['metric']} | {row['n_pairs']} | {row['effect_estimate']:.4g} | "
            f"{row['cohen_dz']:.4g} | {row['p_value']:.4g} | {row['q_value']:.4g} |"
        )
    lines += [
        "",
        "## Interpretation boundary",
        "",
        "Any paired NDT differences are condition-associated changes in this batch, not evidence that glucose directly measures consciousness or that a metabolic gate is causally identified.",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.results_root.mkdir(parents=True, exist_ok=True)
    raw_features = _h5_feature_medians(args.raw_root)
    feature_results = _paired_feature_results(raw_features)
    contrast_results = pd.read_parquet(_latest_parquet(args.analysis_root, "contrast_results"))
    qc_summary = pd.read_parquet(_latest_parquet(args.analysis_root, "qc_summary"))

    raw_features.to_csv(args.results_root / "raw_eeg_feature_medians.csv", index=False)
    feature_results.to_csv(args.results_root / "raw_eeg_feature_paired_results.csv", index=False)
    contrast_results.to_csv(args.results_root / "ndt_paired_contrast_results.csv", index=False)
    qc_summary.to_csv(args.results_root / "ndt_qc_summary.csv", index=False)
    _write_report(
        args.results_root / "hypoglycemia_t1d_report.md",
        raw_features,
        feature_results,
        contrast_results,
        qc_summary,
    )
    print(f"results_root={args.results_root}")


if __name__ == "__main__":
    main()
