"""CPC1 vs CPC5 contrast on first-12h turning-angle geometry features.

This is the direct test of plan.md's hypothesis, adapted from psychosis
medication groups to coma outcome groups: does turning-angle frequency,
magnitude, diversity, or null-normalized persistence in the first 12h
separate good (CPC1) from poor (CPC5) outcome, for any of the five charts
(native 3D, native 9D, and the three m*/d*/e* family 3D subspaces) at any of
the three lags?

Statistics follow the same convention as
``comatose_ndt/src/icare_outcome_contrast_analysis.py`` and the sibling
phase-shift pipeline's ``04_cpc_contrast.py``: Mann-Whitney U + Welch's
t-test, Cohen's d + Cliff's delta, then BH-FDR across the full predeclared
family of (chart x lag x metric) cells.

Input: ``patient_chart_lag_turning_features.csv`` from
``02_aggregate_patient_features.py``.
Output: ranked contrast table + markdown summary of FDR-significant cells.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats

import coma_angle_support  # noqa: F401  (side effect: extends sys.path)
from classical_comparator_summary import bh_fdr  # noqa: E402
from icare_outcome_contrast_analysis import cliffs_delta, cohens_d_independent  # noqa: E402


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "cpc_contrast"
DEFAULT_GOOD_LABEL = "Good"
DEFAULT_POOR_LABEL = "Poor"

TURNING_METRIC_COLUMNS: tuple[str, ...] = (
    "turn_cos_mean",
    "turn_angle_median",
    "turn_angle_mad",
    "turn_angle_iqr",
    "turn_angle_p90",
    "turn_fraction_gt_90",
    "turn_fraction_gt_120",
    "turn_entropy",
    "turn_length_coupling",
    "null_z_median_angle",
)


@dataclass(frozen=True)
class ContrastConfig:
    patient_features_path: Path
    output_dir: Path
    good_cpc: int
    poor_cpc: int
    good_label: str
    poor_label: str
    min_valid_angles: float


def parse_args() -> ContrastConfig:
    parser = argparse.ArgumentParser(description="CPC1 vs CPC5 contrast on first-12h turning-angle geometry features.")
    parser.add_argument("--patient-features-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--good-cpc", type=int, default=1)
    parser.add_argument("--poor-cpc", type=int, default=5)
    parser.add_argument("--good-label", type=str, default=DEFAULT_GOOD_LABEL)
    parser.add_argument("--poor-label", type=str, default=DEFAULT_POOR_LABEL)
    parser.add_argument(
        "--min-valid-angles",
        type=float,
        default=0.0,
        help="Drop (patient, chart, lag) rows whose total valid-angle count is below this threshold before contrast.",
    )
    args = parser.parse_args()
    return ContrastConfig(
        patient_features_path=args.patient_features_path,
        output_dir=args.output_dir,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        good_label=args.good_label,
        poor_label=args.poor_label,
        min_valid_angles=args.min_valid_angles,
    )


def build_long_metric_table(patient_features: pd.DataFrame, config: ContrastConfig) -> pd.DataFrame:
    if patient_features.empty:
        return pd.DataFrame()

    filtered = patient_features.copy()
    if config.min_valid_angles > 0 and "n_valid_angles_total" in filtered.columns:
        filtered = filtered[pd.to_numeric(filtered["n_valid_angles_total"], errors="coerce") >= config.min_valid_angles]

    cpc_numeric = pd.to_numeric(filtered["cpc"], errors="coerce")
    filtered["outcome"] = np.where(
        cpc_numeric == float(config.good_cpc),
        config.good_label,
        np.where(cpc_numeric == float(config.poor_cpc), config.poor_label, None),
    )
    filtered = filtered[pd.notna(filtered["outcome"])].copy()

    frames: List[pd.DataFrame] = []
    for feature in TURNING_METRIC_COLUMNS:
        if feature not in filtered.columns:
            continue
        long = filtered[["subject", "chart", "lag_epochs", "outcome"]].copy()
        long["turning_feature"] = feature
        long["metric"] = (
            filtered["chart"].astype(str) + "__lag" + filtered["lag_epochs"].astype(str) + "__" + feature
        )
        long["value"] = pd.to_numeric(filtered[feature], errors="coerce")
        frames.append(long)
    if not frames:
        return pd.DataFrame()
    long_table = pd.concat(frames, ignore_index=True)
    return long_table[np.isfinite(long_table["value"].to_numpy(dtype=float))].reset_index(drop=True)


def summary_stats(values: np.ndarray) -> Dict[str, float]:
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {"n": 0.0, "mean": np.nan, "median": np.nan, "sd": np.nan}
    return {
        "n": float(values.size),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "sd": float(np.std(values, ddof=1)) if values.size > 1 else np.nan,
    }


def build_contrast_table(long_table: pd.DataFrame, config: ContrastConfig) -> pd.DataFrame:
    if long_table.empty:
        return pd.DataFrame()

    rows: List[Dict[str, Any]] = []
    for (chart, lag, turning_feature, metric), group in long_table.groupby(
        ["chart", "lag_epochs", "turning_feature", "metric"], dropna=False, sort=False
    ):
        good_values = group.loc[group["outcome"] == config.good_label, "value"].to_numpy(dtype=float)
        poor_values = group.loc[group["outcome"] == config.poor_label, "value"].to_numpy(dtype=float)
        good_stats = summary_stats(good_values)
        poor_stats = summary_stats(poor_values)

        row: Dict[str, Any] = {
            "chart": chart,
            "lag_epochs": lag,
            "turning_feature": turning_feature,
            "metric": metric,
            "n_good": good_stats["n"],
            "n_poor": poor_stats["n"],
            "good_mean": good_stats["mean"],
            "good_median": good_stats["median"],
            "poor_mean": poor_stats["mean"],
            "poor_median": poor_stats["median"],
            "delta_median_good_minus_poor": (
                good_stats["median"] - poor_stats["median"]
                if np.isfinite(good_stats["median"]) and np.isfinite(poor_stats["median"])
                else np.nan
            ),
            "cohens_d": cohens_d_independent(good_values, poor_values),
            "cliffs_delta": cliffs_delta(good_values, poor_values),
        }

        if good_values.size >= 2 and poor_values.size >= 2:
            mw = stats.mannwhitneyu(good_values, poor_values, alternative="two-sided")
            welch = stats.ttest_ind(good_values, poor_values, equal_var=False, nan_policy="omit")
            row.update(
                {
                    "mannwhitney_u": float(mw.statistic),
                    "mannwhitney_p": float(mw.pvalue),
                    "welch_t": float(welch.statistic),
                    "welch_p": float(welch.pvalue),
                    "status": "ok",
                }
            )
        else:
            row.update(
                {
                    "mannwhitney_u": np.nan,
                    "mannwhitney_p": np.nan,
                    "welch_t": np.nan,
                    "welch_p": np.nan,
                    "status": "limited_n",
                }
            )
        rows.append(row)

    table = pd.DataFrame(rows)
    table["mannwhitney_q_bh"] = bh_fdr(table["mannwhitney_p"])
    table["welch_q_bh"] = bh_fdr(table["welch_p"])
    return table.sort_values("mannwhitney_p", na_position="last").reset_index(drop=True)


def build_summary_markdown(contrast_table: pd.DataFrame, config: ContrastConfig) -> str:
    lines = [
        "# CPC1 vs CPC5 first-12h turning-angle contrast",
        "",
        f"- good_cpc={config.good_cpc} ({config.good_label}), poor_cpc={config.poor_cpc} ({config.poor_label})",
        f"- n_cells_tested={len(contrast_table)}",
        "",
        "Adapted from plan.md (originally written for FEP psychosis vs. Healthy, "
        "medication-stratified). Here the contrast is CPC1 vs. CPC5; the metric-adjusted "
        "(shrinkage-covariance) 9D angle from plan.md section 3 is not included in this pass "
        "(see coma_angle_support.py module docstring and README.md).",
        "",
    ]
    if contrast_table.empty:
        lines.append("No contrast cells were estimable (check upstream QC counts).")
        return "\n".join(lines) + "\n"

    significant = contrast_table[contrast_table["mannwhitney_q_bh"] < 0.05].copy()
    lines.append(f"## FDR-significant cells (q < 0.05): {len(significant)}")
    lines.append("")
    if significant.empty:
        lines.append("None of the tested (chart x lag x turning-feature) cells survived BH-FDR at q < 0.05.")
    else:
        for _, row in significant.sort_values("mannwhitney_q_bh").iterrows():
            lines.append(
                f"- `{row['metric']}`: delta_median={row['delta_median_good_minus_poor']:.4g}, "
                f"cohens_d={row['cohens_d']:.3g}, cliffs_delta={row['cliffs_delta']:.3g}, "
                f"mannwhitney_p={row['mannwhitney_p']:.4g}, q_bh={row['mannwhitney_q_bh']:.4g}"
            )
    lines.append("")
    lines.append("## Top 10 cells by raw p-value (uncorrected, for context only)")
    lines.append("")
    for _, row in contrast_table.head(10).iterrows():
        lines.append(
            f"- `{row['metric']}`: delta_median={row['delta_median_good_minus_poor']:.4g}, "
            f"mannwhitney_p={row['mannwhitney_p']:.4g}, q_bh={row['mannwhitney_q_bh']:.4g}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    patient_features = pd.read_csv(config.patient_features_path)
    long_table = build_long_metric_table(patient_features, config)
    contrast_table = build_contrast_table(long_table, config)

    contrast_path = config.output_dir / "cpc1_vs_cpc5_turning_angle_contrasts.csv"
    summary_path = config.output_dir / "cpc1_vs_cpc5_turning_angle_summary.md"
    contrast_table.to_csv(contrast_path, index=False)
    summary_path.write_text(build_summary_markdown(contrast_table, config), encoding="utf-8")

    print(f"Wrote {len(contrast_table)} contrast cells to {contrast_path}")
    print(f"Wrote summary to {summary_path}")
    if not contrast_table.empty:
        n_sig = int((contrast_table["mannwhitney_q_bh"] < 0.05).sum())
        print(f"FDR-significant cells (q<0.05): {n_sig}/{len(contrast_table)}")


if __name__ == "__main__":
    sys.exit(main())
