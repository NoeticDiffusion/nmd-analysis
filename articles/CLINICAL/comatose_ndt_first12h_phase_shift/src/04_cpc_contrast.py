"""CPC1 vs CPC5 contrast on first-12h phase-shift features.

This is the direct test of the hypothesis: do shift *frequency* and/or shift
*quality/magnitude* in the first 12h separate good (CPC1) from poor (CPC5)
outcome, for any of the nine 9D-chart coordinates or the three m/d/e
composites (``d_n`` included but not privileged - see the naming caveat in
``coma_phase_shift_support.py``)?

Statistics follow the exact convention already used by
``comatose_ndt/src/icare_outcome_contrast_analysis.py``: Mann-Whitney U +
Welch's t-test, Cohen's d + Cliff's delta, then BH-FDR (reusing
``classical_comparator_summary.bh_fdr``) across the full predeclared family
of (coordinate x shift-feature) cells - instead of re-deriving the stats.

Input: ``patient_coordinate_shift_features.csv`` from
``03_aggregate_patient_features.py``.
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

import coma_phase_shift_support  # noqa: F401  (side effect: extends sys.path)
from classical_comparator_summary import bh_fdr  # noqa: E402
from icare_outcome_contrast_analysis import cliffs_delta, cohens_d_independent  # noqa: E402


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "cpc_contrast"
DEFAULT_GOOD_LABEL = "Good"
DEFAULT_POOR_LABEL = "Poor"

SHIFT_FEATURE_COLUMNS: tuple[str, ...] = (
    "shift_rate_per_hour",
    "mean_shift_magnitude",
    "median_shift_magnitude",
    "mean_shift_quality",
    "median_shift_quality",
    "median_segment_length_epochs",
)


@dataclass(frozen=True)
class ContrastConfig:
    patient_features_path: Path
    output_dir: Path
    good_cpc: int
    poor_cpc: int
    good_label: str
    poor_label: str
    min_epochs_analyzed: float


def parse_args() -> ContrastConfig:
    parser = argparse.ArgumentParser(
        description="CPC1 vs CPC5 contrast on first-12h phase-shift rate/magnitude/quality features."
    )
    parser.add_argument("--patient-features-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--good-cpc", type=int, default=1)
    parser.add_argument("--poor-cpc", type=int, default=5)
    parser.add_argument("--good-label", type=str, default=DEFAULT_GOOD_LABEL)
    parser.add_argument("--poor-label", type=str, default=DEFAULT_POOR_LABEL)
    parser.add_argument(
        "--min-epochs-analyzed",
        type=float,
        default=0.0,
        help="Drop (patient, coordinate) rows whose total analyzed epoch count is below this threshold before contrast.",
    )
    args = parser.parse_args()
    return ContrastConfig(
        patient_features_path=args.patient_features_path,
        output_dir=args.output_dir,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        good_label=args.good_label,
        poor_label=args.poor_label,
        min_epochs_analyzed=args.min_epochs_analyzed,
    )


def build_long_metric_table(patient_features: pd.DataFrame, config: ContrastConfig) -> pd.DataFrame:
    if patient_features.empty:
        return pd.DataFrame()

    filtered = patient_features.copy()
    if config.min_epochs_analyzed > 0 and "n_epochs_analyzed_total" in filtered.columns:
        filtered = filtered[pd.to_numeric(filtered["n_epochs_analyzed_total"], errors="coerce") >= config.min_epochs_analyzed]

    cpc_numeric = pd.to_numeric(filtered["cpc"], errors="coerce")
    filtered["outcome"] = np.where(
        cpc_numeric == float(config.good_cpc),
        config.good_label,
        np.where(cpc_numeric == float(config.poor_cpc), config.poor_label, None),
    )
    filtered = filtered[pd.notna(filtered["outcome"])].copy()

    frames: List[pd.DataFrame] = []
    for feature in SHIFT_FEATURE_COLUMNS:
        if feature not in filtered.columns:
            continue
        long = filtered[["subject", "coordinate", "outcome"]].copy()
        long["shift_feature"] = feature
        long["metric"] = filtered["coordinate"].astype(str) + "__" + feature
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
    for (coordinate, shift_feature, metric), group in long_table.groupby(
        ["coordinate", "shift_feature", "metric"], dropna=False, sort=False
    ):
        good_values = group.loc[group["outcome"] == config.good_label, "value"].to_numpy(dtype=float)
        poor_values = group.loc[group["outcome"] == config.poor_label, "value"].to_numpy(dtype=float)
        good_stats = summary_stats(good_values)
        poor_stats = summary_stats(poor_values)

        row: Dict[str, Any] = {
            "coordinate": coordinate,
            "shift_feature": shift_feature,
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
        "# CPC1 vs CPC5 first-12h phase-shift contrast",
        "",
        f"- good_cpc={config.good_cpc} ({config.good_label}), poor_cpc={config.poor_cpc} ({config.poor_label})",
        f"- n_cells_tested={len(contrast_table)}",
        "",
        "Caveat: `d_n` here is the I-CARE EEG-contract alias for `eeg_gamma`, "
        "not the RVC_SLEEP heat-kernel network-diffusivity `d_n`. See "
        "`coma_phase_shift_support.py` module docstring.",
        "",
    ]
    if contrast_table.empty:
        lines.append("No contrast cells were estimable (check upstream QC counts).")
        return "\n".join(lines) + "\n"

    significant = contrast_table[contrast_table["mannwhitney_q_bh"] < 0.05].copy()
    lines.append(f"## FDR-significant cells (q < 0.05): {len(significant)}")
    lines.append("")
    if significant.empty:
        lines.append("None of the tested (coordinate x shift-feature) cells survived BH-FDR at q < 0.05.")
    else:
        for _, row in significant.sort_values("mannwhitney_q_bh").iterrows():
            lines.append(
                f"- `{row['metric']}`: delta_median={row['delta_median_good_minus_poor']:.4g}, "
                f"cohens_d={row['cohens_d']:.3g}, mannwhitney_p={row['mannwhitney_p']:.4g}, "
                f"q_bh={row['mannwhitney_q_bh']:.4g}"
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

    contrast_path = config.output_dir / "cpc1_vs_cpc5_phase_shift_contrasts.csv"
    summary_path = config.output_dir / "cpc1_vs_cpc5_phase_shift_summary.md"
    contrast_table.to_csv(contrast_path, index=False)
    summary_path.write_text(build_summary_markdown(contrast_table, config), encoding="utf-8")

    print(f"Wrote {len(contrast_table)} contrast cells to {contrast_path}")
    print(f"Wrote summary to {summary_path}")
    if not contrast_table.empty:
        n_sig = int((contrast_table["mannwhitney_q_bh"] < 0.05).sum())
        print(f"FDR-significant cells (q<0.05): {n_sig}/{len(contrast_table)}")


if __name__ == "__main__":
    sys.exit(main())
