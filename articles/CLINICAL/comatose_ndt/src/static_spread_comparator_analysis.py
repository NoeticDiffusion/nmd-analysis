from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats

from incremental_validity_analysis import (
    CLINICAL_BASELINE_COLUMNS,
    CLINICAL_BOOLEAN_COLUMNS,
    CLINICAL_CATEGORICAL_COLUMNS,
    EEG_BASELINE_COLUMNS,
    compute_metrics,
    evaluate_leave_one_site_out,
    evaluate_repeated_cv,
    format_feature_list,
    get_active_feature_sets,
    load_geometry_frame,
    load_timeline_frame,
    resolve_split_count,
    summarize_coefficients,
    summarize_scores,
)


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TIMELINE_DIR = ARTICLE_DIR / "results" / "timeline_analysis_20260522_combined_cpc15_primary12h"
DEFAULT_MNPS_DIR = ARTICLE_DIR / "results" / "mnps_summary_20260522_combined_cpc15_primary12h"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "static_spread_comparator_20260523_combined_cpc15"
DEFAULT_PRIMARY_TIME_BIN = "0_12h"
DEFAULT_GOOD_LABEL = "CPC1"
DEFAULT_POOR_LABEL = "CPC5"
DEFAULT_GOOD_CPC = 1
DEFAULT_POOR_CPC = 5
DEFAULT_RANDOM_STATE = 20260517
DEFAULT_N_SPLITS = 5
DEFAULT_N_REPEATS = 20

STATIC_SPREAD_COLUMNS = ["m_iqr", "d_iqr", "e_iqr"]
MODEL_DISPLAY_LABELS = {
    "clinical_plus_eeg": "Clinical+qEEG",
    "clinical_plus_eeg_plus_static_spread": "Clinical+qEEG+StaticSpread",
    "clinical_plus_eeg_plus_geometry": "Clinical+qEEG+Geometry",
}


@dataclass(frozen=True)
class Config:
    timeline_dir: Path
    mnps_dir: Path
    output_dir: Path
    primary_time_bin: str
    good_label: str
    poor_label: str
    good_cpc: int
    poor_cpc: int
    n_splits: int
    n_repeats: int
    random_state: int


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Compare pooled static MNPS spread against the geometry layer for the coma cohort."
    )
    parser.add_argument("--timeline-dir", type=Path, default=DEFAULT_TIMELINE_DIR)
    parser.add_argument("--mnps-dir", type=Path, default=DEFAULT_MNPS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--primary-time-bin", type=str, default=DEFAULT_PRIMARY_TIME_BIN)
    parser.add_argument("--good-label", type=str, default=DEFAULT_GOOD_LABEL)
    parser.add_argument("--poor-label", type=str, default=DEFAULT_POOR_LABEL)
    parser.add_argument("--good-cpc", type=int, default=DEFAULT_GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=DEFAULT_POOR_CPC)
    parser.add_argument("--n-splits", type=int, default=DEFAULT_N_SPLITS)
    parser.add_argument("--n-repeats", type=int, default=DEFAULT_N_REPEATS)
    parser.add_argument("--random-state", type=int, default=DEFAULT_RANDOM_STATE)
    args = parser.parse_args()
    return Config(
        timeline_dir=args.timeline_dir,
        mnps_dir=args.mnps_dir,
        output_dir=args.output_dir,
        primary_time_bin=args.primary_time_bin,
        good_label=args.good_label,
        poor_label=args.poor_label,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        n_splits=args.n_splits,
        n_repeats=args.n_repeats,
        random_state=args.random_state,
    )


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    if good.size < 2 or poor.size < 2:
        return float("nan")
    pooled = ((good.size - 1) * np.var(good, ddof=1) + (poor.size - 1) * np.var(poor, ddof=1)) / (good.size + poor.size - 2)
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(good) - np.mean(poor)) / np.sqrt(pooled))


def load_static_spread_frame(config: Config) -> pd.DataFrame:
    frame = pd.read_csv(config.timeline_dir / "patient_timebin_summaries.csv")
    frame = frame[frame["time_bin"] == config.primary_time_bin].copy()
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)])].copy()
    keep = ["subject", *[column for column in STATIC_SPREAD_COLUMNS if column in frame.columns]]
    if len(keep) == 1:
        return pd.DataFrame(columns=keep)
    return frame[keep].drop_duplicates(subset=["subject"]).reset_index(drop=True)


def build_model_frame(config: Config) -> pd.DataFrame:
    timeline = load_timeline_frame(config)
    missing_static = [column for column in STATIC_SPREAD_COLUMNS if column not in timeline.columns]
    if missing_static:
        static_spread = load_static_spread_frame(config)
        available = ["subject", *[column for column in missing_static if column in static_spread.columns]]
        if len(available) > 1:
            timeline = timeline.merge(static_spread[available], on="subject", how="left")
    geometry = load_geometry_frame(config)
    frame = timeline.merge(geometry, on="subject", how="left")

    clinical_frame = frame[["subject", "hospital", "label", "label_name"]].copy()
    for column in CLINICAL_BASELINE_COLUMNS:
        if column in frame.columns:
            clinical_frame[f"clinical__{column}"] = pd.to_numeric(frame[column], errors="coerce")
    for column in CLINICAL_BOOLEAN_COLUMNS:
        if column in frame.columns:
            clinical_frame[f"clinical__{column}"] = pd.to_numeric(frame[column], errors="coerce")

    categorical = frame[CLINICAL_CATEGORICAL_COLUMNS].copy()
    categorical = categorical.fillna("missing").astype(str)
    categorical.columns = [f"cat__{column}" for column in categorical.columns]
    categorical_dummies = pd.get_dummies(categorical, prefix=list(categorical.columns), dtype=float)

    eeg_frame = frame[["subject"]].copy()
    for column in EEG_BASELINE_COLUMNS:
        if column in frame.columns:
            eeg_frame[f"eeg__{column}"] = pd.to_numeric(frame[column], errors="coerce")

    static_frame = frame[["subject"]].copy()
    for column in STATIC_SPREAD_COLUMNS:
        static_frame[f"static__{column}"] = pd.to_numeric(frame[column], errors="coerce")
    static_frame["static__mnps_static_spread_mean"] = static_frame[
        [f"static__{column}" for column in STATIC_SPREAD_COLUMNS]
    ].mean(axis=1, skipna=True)

    geometry_frame = frame[["subject"]].copy()
    for column in (
        "geom_tube_d_eff_median",
        "geom_persistence_kappa_median",
        "geom_persistence_log_eig_var_median",
        "geom_tube_a_operator_norm_median",
        "geom_tube_capture_gate_median",
    ):
        if column in frame.columns:
            geometry_frame[column] = pd.to_numeric(frame[column], errors="coerce")

    merged = clinical_frame.merge(categorical_dummies, left_index=True, right_index=True, how="left")
    merged = merged.merge(eeg_frame, on="subject", how="left")
    merged = merged.merge(static_frame, on="subject", how="left")
    merged = merged.merge(geometry_frame, on="subject", how="left")

    feature_columns = [column for column in merged.columns if column not in {"subject", "hospital", "label", "label_name"}]
    all_missing = [
        column for column in feature_columns if pd.to_numeric(merged[column], errors="coerce").notna().sum() == 0
    ]
    if all_missing:
        merged = merged.drop(columns=all_missing)
    return merged


def get_feature_sets(frame: pd.DataFrame) -> Dict[str, List[str]]:
    clinical = sorted(column for column in frame.columns if column.startswith("clinical__") or column.startswith("cat__"))
    eeg = sorted(column for column in frame.columns if column.startswith("eeg__"))
    static = sorted(column for column in frame.columns if column.startswith("static__"))
    geometry = sorted(column for column in frame.columns if column.startswith("geom_"))
    return {
        "clinical_plus_eeg": clinical + eeg,
        "clinical_plus_eeg_plus_static_spread": clinical + eeg + static,
        "clinical_plus_eeg_plus_geometry": clinical + eeg + geometry,
    }


def build_static_contrast_table(cohort: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    specs = [
        ("static__m_iqr", "MNPS axis spread (`m_iqr`)"),
        ("static__d_iqr", "MNPS axis spread (`d_iqr`)"),
        ("static__e_iqr", "MNPS axis spread (`e_iqr`)"),
        ("static__mnps_static_spread_mean", "Mean MNPS static spread"),
    ]
    for metric, label in specs:
        good = pd.to_numeric(cohort.loc[cohort["label"] == 1, metric], errors="coerce").dropna().to_numpy(dtype=float)
        poor = pd.to_numeric(cohort.loc[cohort["label"] == 0, metric], errors="coerce").dropna().to_numpy(dtype=float)
        row: Dict[str, Any] = {
            "metric": metric,
            "label": label,
            "n_cpc1": int(good.size),
            "n_cpc5": int(poor.size),
            "cpc1_median": float(np.median(good)) if good.size else float("nan"),
            "cpc5_median": float(np.median(poor)) if poor.size else float("nan"),
            "delta_median_good_minus_poor": float(np.median(good) - np.median(poor)) if good.size and poor.size else float("nan"),
            "cohens_d": cohens_d(good, poor),
        }
        if good.size and poor.size:
            mannwhitney = stats.mannwhitneyu(good, poor, alternative="two-sided")
            row["mannwhitney_u"] = float(mannwhitney.statistic)
            row["mannwhitney_p"] = float(mannwhitney.pvalue)
            row["status"] = "ok"
        else:
            row["mannwhitney_u"] = float("nan")
            row["mannwhitney_p"] = float("nan")
            row["status"] = "insufficient_groups"
        rows.append(row)
    return pd.DataFrame(rows)


def restrict_to_static_complete_case(cohort: pd.DataFrame) -> pd.DataFrame:
    required = [f"static__{column}" for column in STATIC_SPREAD_COLUMNS]
    if any(column not in cohort.columns for column in required):
        return cohort.iloc[0:0].copy()
    mask = cohort[required].notna().all(axis=1)
    return cohort.loc[mask].reset_index(drop=True)


def write_markdown(
    config: Config,
    cohort: pd.DataFrame,
    static_contrasts: pd.DataFrame,
    repeated_summary: pd.DataFrame,
    site_summary: pd.DataFrame,
    coefficient_summary: pd.DataFrame,
    feature_sets: Dict[str, List[str]],
) -> str:
    effective_n_splits = resolve_split_count(cohort["label"].astype(int).to_numpy(), config.n_splits)
    lines = [
        "# Static MNPS Spread Comparator",
        "",
        f"Primary endpoint cohort: `{config.good_label}` vs `{config.poor_label}` in `{config.primary_time_bin}`.",
        "",
        "## Comparator rationale",
        "",
        "This appendix-grade control asks whether a low-order static spread summary in the same pooled MNPS space can explain the improvement otherwise attributed to reachability geometry.",
        "The static comparator uses only axiswise MNPS spread summaries (`m_iqr`, `d_iqr`, `e_iqr`) from the timeline export, with no propagation or horizon-specific reachability estimation.",
        "In the current manuscript-facing bundle, those static spread fields are available only in the subset carrying the older MNPS trajectory export, so this comparator is evaluated on the complete-case subset rather than on the full pooled cohort.",
        "",
        "## Cohort",
        "",
        f"- n_subjects: {len(cohort)}",
        f"- {config.good_label}: {int((cohort['label'] == 1).sum())}",
        f"- {config.poor_label}: {int((cohort['label'] == 0).sum())}",
        "",
        "## Feature sets",
        "",
        f"- `clinical_plus_eeg` ({len(feature_sets['clinical_plus_eeg'])}): fixed union of clinical and qEEG features",
        f"- `clinical_plus_eeg_plus_static_spread` ({len(feature_sets['clinical_plus_eeg_plus_static_spread'])}): clinical + qEEG plus {format_feature_list([column for column in feature_sets['clinical_plus_eeg_plus_static_spread'] if column.startswith('static__')])}",
        f"- `clinical_plus_eeg_plus_geometry` ({len(feature_sets['clinical_plus_eeg_plus_geometry'])}): clinical + qEEG plus the five discovery-frozen geometry features",
        "",
        "## Static spread contrasts",
        "",
        "| Metric | CPC1 median | CPC5 median | Cohen's d | Mann-Whitney p |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, row in static_contrasts.iterrows():
        lines.append(
            f"| {row['label']} | {row['cpc1_median']:.3f} | {row['cpc5_median']:.3f} | {row['cohens_d']:.3f} | {row['mannwhitney_p']:.3g} |"
        )

    lines.extend(
        [
            "",
            "## Repeated Stratified CV",
            "",
            f"- splitter: `RepeatedStratifiedKFold(n_splits={effective_n_splits}, n_repeats={config.n_repeats}, random_state={config.random_state})`",
            f"- LOSO sensitivity: `LeaveOneGroupOut()` with held-out hospital",
            "",
            "| Model | Features | ROC AUC | AUPRC | Brier | Delta AUC vs clinical+qEEG |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )

    repeated = repeated_summary[repeated_summary["evaluation"] == "repeated_stratified_cv"].copy()
    for _, row in repeated.iterrows():
        lines.append(
            f"| {MODEL_DISPLAY_LABELS.get(row['model'], row['model'])} | {int(row['n_features_median'])} | "
            f"{row['roc_auc_mean']:.3f} [{row['roc_auc_ci_low']:.3f}, {row['roc_auc_ci_high']:.3f}] | "
            f"{row['average_precision_mean']:.3f} [{row['average_precision_ci_low']:.3f}, {row['average_precision_ci_high']:.3f}] | "
            f"{row['brier_score_mean']:.3f} [{row['brier_score_ci_low']:.3f}, {row['brier_score_ci_high']:.3f}] | "
            f"{row.get('delta_roc_auc_mean', np.nan):+.3f} |"
        )

    static_row = repeated[repeated["model"] == "clinical_plus_eeg_plus_static_spread"]
    geometry_row = repeated[repeated["model"] == "clinical_plus_eeg_plus_geometry"]
    if not static_row.empty and not geometry_row.empty:
        static_auc = float(static_row.iloc[0]["roc_auc_mean"])
        geom_auc = float(geometry_row.iloc[0]["roc_auc_mean"])
        static_auprc = float(static_row.iloc[0]["average_precision_mean"])
        geom_auprc = float(geometry_row.iloc[0]["average_precision_mean"])
        lines.extend(
            [
                "",
                "## Interpretation",
                "",
                f"- static MNPS spread raises repeated-CV AUROC to `{static_auc:.3f}`, whereas the geometry layer reaches `{geom_auc:.3f}`.",
                f"- static MNPS spread reaches AUPRC `{static_auprc:.3f}`, whereas the geometry layer reaches `{geom_auprc:.3f}`.",
                "- This is therefore a useful non-dynamical comparator, but it does not match the pooled reachability layer.",
            ]
        )

    if not site_summary.empty:
        lines.extend(["", "## Leave-One-Site-Out", ""])
        for _, row in site_summary.iterrows():
            lines.append(
                f"- `{MODEL_DISPLAY_LABELS.get(row['model'], row['model'])}`: roc_auc={row['roc_auc_mean']:.3f}, "
                f"auprc={row['average_precision_mean']:.3f}, brier={row['brier_score_mean']:.3f}"
            )

    if not coefficient_summary.empty:
        top = coefficient_summary[coefficient_summary["model"] == "clinical_plus_eeg_plus_static_spread"].head(8)
        if not top.empty:
            lines.extend(["", "## Top static-spread coefficients", "", "| Feature | Mean abs coef | Mean signed coef |", "|---|---:|---:|"])
            for _, row in top.iterrows():
                lines.append(f"| {row['feature']} | {row['mean_abs_coef']:.3f} | {row['mean_coef']:+.3f} |")

    return "\n".join(lines) + "\n"


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    full_cohort = build_model_frame(config)
    cohort = restrict_to_static_complete_case(full_cohort)
    static_feature_columns = [column for column in full_cohort.columns if column.startswith("static__")]
    if not static_feature_columns or cohort.empty:
        empty_df = pd.DataFrame()
        full_cohort.to_csv(config.output_dir / "static_spread_comparator_cohort.csv", index=False)
        empty_df.to_csv(config.output_dir / "static_spread_contrasts.csv", index=False)
        empty_df.to_csv(config.output_dir / "static_spread_fold_scores.csv", index=False)
        empty_df.to_csv(config.output_dir / "static_spread_predictions.csv", index=False)
        empty_df.to_csv(config.output_dir / "static_spread_feature_coefficients.csv", index=False)
        empty_df.to_csv(config.output_dir / "static_spread_summary.csv", index=False)
        empty_df.to_csv(config.output_dir / "static_spread_site_summary.csv", index=False)
        empty_df.to_csv(config.output_dir / "static_spread_feature_summary.csv", index=False)
        unavailable_reason = (
            "Static spread fields (`m_iqr`, `d_iqr`, `e_iqr`) are absent or fully missing in the refreshed bundle, "
            "so the complete-case static comparator could not be recomputed."
        )
        (config.output_dir / "static_spread_comparator_manifest.json").write_text(
            json.dumps(
                {
                    "timeline_dir": str(config.timeline_dir),
                    "mnps_dir": str(config.mnps_dir),
                    "primary_time_bin": config.primary_time_bin,
                    "good_cpc": config.good_cpc,
                    "poor_cpc": config.poor_cpc,
                    "full_cohort_subjects": int(len(full_cohort)),
                    "static_complete_case_subjects": int(len(cohort)),
                    "static_spread_columns": STATIC_SPREAD_COLUMNS,
                    "available_static_feature_columns": static_feature_columns,
                    "status": "unavailable_in_refreshed_bundle",
                    "unavailable_reason": unavailable_reason,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (config.output_dir / "static_spread_summary.md").write_text(
            "\n".join(
                [
                    "# Static MNPS Spread Comparator",
                    "",
                    f"Primary endpoint cohort: `{config.good_label}` vs `{config.poor_label}` in `{config.primary_time_bin}`.",
                    "",
                    "## Status",
                    "",
                    f"- unavailable reason: {unavailable_reason}",
                    f"- full cohort subjects: {len(full_cohort)}",
                    f"- static complete-case subjects: {len(cohort)}",
                    "",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"Static spread comparator unavailable in refreshed bundle; wrote status summary to {config.output_dir}")
        return

    feature_sets = get_feature_sets(cohort)
    active_feature_sets = get_active_feature_sets(feature_sets)

    repeated_scores, predictions, coefficients = evaluate_repeated_cv(cohort, active_feature_sets, config)
    site_scores = evaluate_leave_one_site_out(cohort, active_feature_sets, config)
    repeated_summary = summarize_scores(repeated_scores)
    site_summary = summarize_scores(site_scores)
    coefficient_summary = summarize_coefficients(coefficients)
    static_contrasts = build_static_contrast_table(cohort)

    cohort.to_csv(config.output_dir / "static_spread_comparator_cohort.csv", index=False)
    static_contrasts.to_csv(config.output_dir / "static_spread_contrasts.csv", index=False)
    repeated_scores.to_csv(config.output_dir / "static_spread_fold_scores.csv", index=False)
    predictions.to_csv(config.output_dir / "static_spread_predictions.csv", index=False)
    coefficients.to_csv(config.output_dir / "static_spread_feature_coefficients.csv", index=False)
    repeated_summary.to_csv(config.output_dir / "static_spread_summary.csv", index=False)
    site_summary.to_csv(config.output_dir / "static_spread_site_summary.csv", index=False)
    coefficient_summary.to_csv(config.output_dir / "static_spread_feature_summary.csv", index=False)
    (config.output_dir / "static_spread_comparator_manifest.json").write_text(
        json.dumps(
            {
                "timeline_dir": str(config.timeline_dir),
                "mnps_dir": str(config.mnps_dir),
                "primary_time_bin": config.primary_time_bin,
                "good_cpc": config.good_cpc,
                "poor_cpc": config.poor_cpc,
                "n_splits": config.n_splits,
                "n_repeats": config.n_repeats,
                "full_cohort_subjects": int(len(full_cohort)),
                "static_complete_case_subjects": int(len(cohort)),
                "effective_n_splits": resolve_split_count(cohort["label"].astype(int).to_numpy(), config.n_splits),
                "static_spread_columns": STATIC_SPREAD_COLUMNS,
                "feature_sets": active_feature_sets,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (config.output_dir / "static_spread_summary.md").write_text(
        write_markdown(config, cohort, static_contrasts, repeated_summary, site_summary, coefficient_summary, active_feature_sets),
        encoding="utf-8",
    )

    print(f"Wrote static spread contrasts to {config.output_dir / 'static_spread_contrasts.csv'}")
    print(f"Wrote repeated-CV comparator summary to {config.output_dir / 'static_spread_summary.csv'}")
    print(f"Wrote comparator markdown to {config.output_dir / 'static_spread_summary.md'}")


if __name__ == "__main__":
    main()
