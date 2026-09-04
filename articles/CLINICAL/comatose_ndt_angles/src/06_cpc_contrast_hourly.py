"""Hour-resolved CPC1-vs-CPC5 contrasts for turning-angle tail/spread metrics.

The predeclared hourly follow-up is intentionally restricted to the three
tail/spread metrics that dominated the pooled result: p90, IQR, and MAD.
For each (chart, lag, feature) cell, BH-FDR corrects across its 12 hourly
tests only. This asks whether an already-established pooled signal localizes
to a particular hour; it is not a discovery-wide correction over every
possible turning metric.
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

import coma_angle_support as support
from classical_comparator_summary import bh_fdr
from icare_outcome_contrast_analysis import cliffs_delta, cohens_d_independent


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "cpc_contrast_hourly"
DEFAULT_POOLED_PATH = ARTICLE_DIR / "results" / "cpc_contrast" / "cpc1_vs_cpc5_turning_angle_contrasts.csv"
TARGET_FEATURES = ("turn_angle_p90", "turn_angle_iqr", "turn_angle_mad")
N_HOURS = 12


@dataclass(frozen=True)
class Config:
    patient_features_path: Path
    pooled_contrasts_path: Path
    output_dir: Path
    good_cpc: int
    poor_cpc: int
    min_valid_angles: float


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Run hourly CPC1-vs-CPC5 turning-angle tail/spread contrasts.")
    parser.add_argument("--patient-features-path", type=Path, required=True)
    parser.add_argument("--pooled-contrasts-path", type=Path, default=DEFAULT_POOLED_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--good-cpc", type=int, default=1)
    parser.add_argument("--poor-cpc", type=int, default=5)
    parser.add_argument("--min-valid-angles", type=float, default=0.0)
    args = parser.parse_args()
    return Config(
        patient_features_path=args.patient_features_path,
        pooled_contrasts_path=args.pooled_contrasts_path,
        output_dir=args.output_dir,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        min_valid_angles=args.min_valid_angles,
    )


def describe(values: np.ndarray) -> Dict[str, float]:
    values = values[np.isfinite(values)]
    return {
        "n": float(values.size),
        "mean": float(np.mean(values)) if values.size else np.nan,
        "median": float(np.median(values)) if values.size else np.nan,
        "sd": float(np.std(values, ddof=1)) if values.size > 1 else np.nan,
    }


def hourly_contrasts(patient_features: pd.DataFrame, config: Config) -> pd.DataFrame:
    frame = patient_features.copy()
    if config.min_valid_angles > 0:
        frame = frame[pd.to_numeric(frame["n_valid_angles_total"], errors="coerce") >= config.min_valid_angles]
    frame["cpc"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc"].isin([config.good_cpc, config.poor_cpc])].copy()

    rows: List[Dict[str, Any]] = []
    for feature in TARGET_FEATURES:
        if feature not in frame.columns:
            continue
        for (chart, lag, hour_bin), group in frame.groupby(["chart", "lag_epochs", "hour_bin"], sort=False):
            values = pd.to_numeric(group[feature], errors="coerce")
            good = values[group["cpc"] == config.good_cpc].dropna().to_numpy(dtype=float)
            poor = values[group["cpc"] == config.poor_cpc].dropna().to_numpy(dtype=float)
            good_stats, poor_stats = describe(good), describe(poor)
            row: Dict[str, Any] = {
                "chart": chart,
                "lag_epochs": lag,
                "hour_bin": int(hour_bin),
                "time_bin": f"{int(hour_bin)}_{int(hour_bin) + 1}h",
                "turning_feature": feature,
                "metric": f"{chart}__lag{lag}__{feature}",
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
                "cohens_d": cohens_d_independent(good, poor),
                "cliffs_delta": cliffs_delta(good, poor),
            }
            if good.size >= 2 and poor.size >= 2:
                mw = stats.mannwhitneyu(good, poor, alternative="two-sided")
                welch = stats.ttest_ind(good, poor, equal_var=False)
                row.update(
                    mannwhitney_u=float(mw.statistic),
                    mannwhitney_p=float(mw.pvalue),
                    welch_t=float(welch.statistic),
                    welch_p=float(welch.pvalue),
                    status="ok",
                )
            else:
                row.update(mannwhitney_u=np.nan, mannwhitney_p=np.nan, welch_t=np.nan, welch_p=np.nan, status="limited_n")
            rows.append(row)

    table = pd.DataFrame(rows)
    if table.empty:
        return table
    cell_columns = ["chart", "lag_epochs", "turning_feature"]
    table["mannwhitney_q_bh_within_cell"] = table.groupby(cell_columns)["mannwhitney_p"].transform(bh_fdr)
    table["welch_q_bh_within_cell"] = table.groupby(cell_columns)["welch_p"].transform(bh_fdr)
    return table.sort_values(["metric", "hour_bin"]).reset_index(drop=True)


def attach_pooled_comparison(hourly: pd.DataFrame, pooled_path: Path) -> pd.DataFrame:
    if hourly.empty or not pooled_path.exists():
        return hourly
    pooled = pd.read_csv(pooled_path)
    pooled = pooled[pooled["turning_feature"].isin(TARGET_FEATURES)][["metric", "cohens_d"]].rename(
        columns={"cohens_d": "pooled_cohens_d"}
    )
    out = hourly.merge(pooled, on="metric", how="left")
    out["abs_d_exceeds_pooled"] = out["cohens_d"].abs() > out["pooled_cohens_d"].abs()
    return out


def build_localization_summary(hourly: pd.DataFrame) -> pd.DataFrame:
    if hourly.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for metric, group in hourly.groupby("metric", sort=False):
        usable = group[np.isfinite(group["cohens_d"])].copy()
        if usable.empty:
            continue
        strongest = usable.loc[usable["cohens_d"].abs().idxmax()]
        significant = usable[usable["mannwhitney_q_bh_within_cell"] < 0.05].sort_values("hour_bin")
        row = {
            "metric": metric,
            "strongest_hour_bin": int(strongest["hour_bin"]),
            "strongest_time_bin": strongest["time_bin"],
            "strongest_cohens_d": float(strongest["cohens_d"]),
            "strongest_mannwhitney_p": float(strongest["mannwhitney_p"]),
            "strongest_q_bh_within_cell": float(strongest["mannwhitney_q_bh_within_cell"]),
            "pooled_cohens_d": float(strongest["pooled_cohens_d"]) if "pooled_cohens_d" in strongest else np.nan,
            "abs_d_exceeds_pooled": bool(strongest["abs_d_exceeds_pooled"]) if "abs_d_exceeds_pooled" in strongest else False,
            "n_fdr_significant_hours": int(len(significant)),
            "first_fdr_significant_hour": int(significant["hour_bin"].iloc[0]) if not significant.empty else np.nan,
        }
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("strongest_cohens_d", key=lambda s: s.abs(), ascending=False).reset_index(drop=True)


def markdown_summary(localization: pd.DataFrame) -> str:
    lines = [
        "# Hour-resolved CPC1 vs CPC5 turning-angle localization",
        "",
        "This is an exploratory localization follow-up to the pooled first-12h analysis.",
        "BH-FDR is applied within each predeclared (chart x lag x tail/spread feature) cell across its 12 hours.",
        "",
    ]
    if localization.empty:
        return "\n".join(lines + ["No estimable hourly contrast cells."]) + "\n"
    n_sig = int((localization["n_fdr_significant_hours"] > 0).sum())
    stronger = int(localization["abs_d_exceeds_pooled"].sum())
    lines.extend(
        [
            f"- Cells with at least one within-cell FDR-significant hour: {n_sig}/{len(localization)}",
            f"- Cells whose strongest hour has larger |d| than pooled-12h: {stronger}/{len(localization)}",
            "",
            "## Strongest localized effects",
            "",
        ]
    )
    for _, row in localization.head(15).iterrows():
        lines.append(
            f"- `{row['metric']}`: strongest `{row['strongest_time_bin']}`, "
            f"d={row['strongest_cohens_d']:+.3f}, p={row['strongest_mannwhitney_p']:.3g}, "
            f"within-cell q={row['strongest_q_bh_within_cell']:.3g}, "
            f"pooled d={row['pooled_cohens_d']:+.3f}, "
            f"FDR-significant hours={int(row['n_fdr_significant_hours'])}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    hourly = hourly_contrasts(pd.read_csv(config.patient_features_path), config)
    hourly = attach_pooled_comparison(hourly, config.pooled_contrasts_path)
    localization = build_localization_summary(hourly)

    hourly_path = config.output_dir / "cpc1_vs_cpc5_turning_angle_hourly_contrasts.csv"
    summary_path = config.output_dir / "cpc1_vs_cpc5_turning_angle_hourly_summary.csv"
    markdown_path = config.output_dir / "cpc1_vs_cpc5_turning_angle_hourly_summary.md"
    hourly.to_csv(hourly_path, index=False)
    localization.to_csv(summary_path, index=False)
    markdown_path.write_text(markdown_summary(localization), encoding="utf-8")
    print(f"Wrote {len(hourly)} hourly contrast cells to {hourly_path}")
    print(f"Wrote localization summary ({len(localization)} rows) to {summary_path}")


if __name__ == "__main__":
    sys.exit(main())
