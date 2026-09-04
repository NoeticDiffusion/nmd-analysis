from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut, RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TIMELINE_DIR = ARTICLE_DIR / "results" / "timeline_analysis"
DEFAULT_MNPS_DIR = ARTICLE_DIR / "results" / "mnps_summary"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "incremental_validity"
DEFAULT_FIGURE_DIR = ARTICLE_DIR / "figures"

DEFAULT_PRIMARY_TIME_BIN = "0_12h"
DEFAULT_GOOD_LABEL = "CPC1"
DEFAULT_POOR_LABEL = "CPC5"
DEFAULT_GOOD_CPC = 1
DEFAULT_POOR_CPC = 5
DEFAULT_RANDOM_STATE = 20260517
DEFAULT_N_SPLITS = 5
DEFAULT_N_REPEATS = 20
DEFAULT_PROB_THRESHOLD = 0.5

EEG_BASELINE_COLUMNS = [
    "rawfeat_eeg_delta_median",
    "rawfeat_eeg_theta_median",
    "rawfeat_eeg_alpha_median",
    "rawfeat_eeg_beta_median",
    "rawfeat_eeg_gamma_median",
    "rawfeat_eeg_highfreq_power_30_45_median",
    "rawfeat_eeg_alpha_theta_median",
    "rawfeat_eeg_beta_alpha_median",
    "rawfeat_eeg_hjorth_mobility_median",
    "rawfeat_eeg_hjorth_complexity_median",
    "rawfeat_eeg_permutation_entropy_median",
    "rawfeat_eeg_sample_entropy_median",
]
CLINICAL_BASELINE_COLUMNS = [
    "age",
    "rosc_minutes",
    "ttm_celsius",
    "channel_count_median",
    "channel_coverage_frac_median",
]
CLINICAL_BOOLEAN_COLUMNS = [
    "shockable_rhythm",
    "ohca",
]
CLINICAL_CATEGORICAL_COLUMNS = [
    "sex",
    "hospital",
]
GEOMETRY_SPECS = [
    ("reachability_cones", "tube_d_eff_median", "geom_tube_d_eff_median"),
    ("reachability_cones", "persistence_kappa_median", "geom_persistence_kappa_median"),
    ("reachability_cones", "persistence_log_eig_var_median", "geom_persistence_log_eig_var_median"),
    ("reachability_cones", "tube_a_operator_norm_median", "geom_tube_a_operator_norm_median"),
    ("reachability_cones", "tube_capture_gate_median", "geom_tube_capture_gate_median"),
]
MODEL_DISPLAY_LABELS = {
    "clinical_only": "Clinical",
    "eeg_only": "EEG",
    "clinical_plus_eeg": "Clinical+EEG",
    "clinical_plus_eeg_plus_geometry": "Clinical+EEG+Geometry",
}


@dataclass(frozen=True)
class Config:
    timeline_dir: Path
    mnps_dir: Path
    output_dir: Path
    figure_dir: Path
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
        description="Run CPC1-vs-CPC5 incremental-validity analysis for the coma cohort."
    )
    parser.add_argument("--timeline-dir", type=Path, default=DEFAULT_TIMELINE_DIR)
    parser.add_argument("--mnps-dir", type=Path, default=DEFAULT_MNPS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--figure-dir", type=Path, default=DEFAULT_FIGURE_DIR)
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
        figure_dir=args.figure_dir,
        primary_time_bin=args.primary_time_bin,
        good_label=args.good_label,
        poor_label=args.poor_label,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        n_splits=args.n_splits,
        n_repeats=args.n_repeats,
        random_state=args.random_state,
    )


def make_classifier(random_state: int) -> Pipeline:
    return Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            (
                "logreg",
                LogisticRegression(
                    solver="liblinear",
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=random_state,
                ),
            ),
        ]
    )


def safe_logit(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(np.asarray(values, dtype=float), 1e-6, 1.0 - 1e-6)
    return np.log(clipped / (1.0 - clipped))


def calibration_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    if len(np.unique(y_true)) < 2:
        return {"calibration_slope": float("nan"), "calibration_intercept": float("nan")}
    x = safe_logit(y_prob).reshape(-1, 1)
    model = LogisticRegression(solver="lbfgs", C=1e6, max_iter=2000)
    model.fit(x, y_true)
    return {
        "calibration_slope": float(model.coef_[0][0]),
        "calibration_intercept": float(model.intercept_[0]),
    }


def threshold_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = DEFAULT_PROB_THRESHOLD) -> Dict[str, float]:
    y_true = np.asarray(y_true, dtype=int)
    y_hat = (np.asarray(y_prob, dtype=float) >= threshold).astype(int)
    tp = int(np.sum((y_true == 1) & (y_hat == 1)))
    tn = int(np.sum((y_true == 0) & (y_hat == 0)))
    fp = int(np.sum((y_true == 0) & (y_hat == 1)))
    fn = int(np.sum((y_true == 1) & (y_hat == 0)))
    sensitivity = tp / (tp + fn) if (tp + fn) else float("nan")
    specificity = tn / (tn + fp) if (tn + fp) else float("nan")
    return {
        "prob_threshold": float(threshold),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "sensitivity": float(sensitivity),
        "specificity": float(specificity),
    }


def normalize_bool_series(series: pd.Series) -> pd.Series:
    mapping = {
        "true": 1.0,
        "false": 0.0,
        "1": 1.0,
        "0": 0.0,
        "yes": 1.0,
        "no": 0.0,
    }
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .map(mapping)
        .astype(float)
    )


def load_timeline_frame(config: Config) -> pd.DataFrame:
    frame = pd.read_csv(config.timeline_dir / "patient_timebin_summaries.csv")
    frame = frame[frame["time_bin"] == config.primary_time_bin].copy()
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)])].copy()
    frame["label"] = np.where(frame["cpc_numeric"] == float(config.good_cpc), 1, 0)
    frame["label_name"] = np.where(frame["label"] == 1, config.good_label, config.poor_label)
    frame["shockable_rhythm"] = normalize_bool_series(frame["shockable_rhythm"])
    frame["ohca"] = normalize_bool_series(frame["ohca"])
    frame["age"] = pd.to_numeric(frame["age"], errors="coerce")
    frame["rosc_minutes"] = pd.to_numeric(frame["rosc_minutes"], errors="coerce")
    frame["ttm_celsius"] = pd.to_numeric(frame["ttm_celsius"], errors="coerce")
    frame["channel_count_median"] = pd.to_numeric(frame["channel_count_median"], errors="coerce")
    frame["channel_coverage_frac_median"] = pd.to_numeric(frame["channel_coverage_frac_median"], errors="coerce")
    return frame.reset_index(drop=True)


def load_geometry_frame(config: Config) -> pd.DataFrame:
    frame = pd.read_csv(config.mnps_dir / "patient_timebin_signal_metrics.csv")
    frame = frame[frame["time_bin"] == config.primary_time_bin].copy()
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)])].copy()

    rows = []
    for analysis_type, metric, feature_name in GEOMETRY_SPECS:
        sub = frame[(frame["analysis_type"] == analysis_type) & (frame["metric"] == metric)].copy()
        if sub.empty:
            continue
        out = sub[["subject", "value"]].copy()
        out = out.rename(columns={"value": feature_name})
        rows.append(out)

    if not rows:
        return pd.DataFrame(columns=["subject"])

    merged = rows[0]
    for frame_part in rows[1:]:
        merged = merged.merge(frame_part, on="subject", how="outer")
    return merged


def build_model_frame(config: Config) -> pd.DataFrame:
    timeline = load_timeline_frame(config)
    geometry = load_geometry_frame(config)
    frame = timeline.merge(geometry, on="subject", how="left")

    numeric_eeg = [column for column in EEG_BASELINE_COLUMNS if column in frame.columns]
    for column in numeric_eeg:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

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
    for column in numeric_eeg:
        eeg_frame[f"eeg__{column}"] = frame[column]

    geometry_frame = frame[["subject"]].copy()
    for _, _, feature_name in GEOMETRY_SPECS:
        if feature_name in frame.columns:
            geometry_frame[feature_name] = pd.to_numeric(frame[feature_name], errors="coerce")

    merged = clinical_frame.merge(categorical_dummies, left_index=True, right_index=True, how="left")
    merged = merged.merge(eeg_frame, on="subject", how="left")
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
    geometry = sorted(column for column in frame.columns if column.startswith("geom_"))
    return {
        "clinical_only": clinical,
        "eeg_only": eeg,
        "clinical_plus_eeg": clinical + eeg,
        "clinical_plus_eeg_plus_geometry": clinical + eeg + geometry,
    }


def get_active_feature_sets(feature_sets: Dict[str, List[str]]) -> Dict[str, List[str]]:
    return {model_name: columns for model_name, columns in feature_sets.items() if columns}


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    out = {
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "average_precision": float(average_precision_score(y_true, y_prob)),
        "brier_score": float(brier_score_loss(y_true, y_prob)),
    }
    out.update(calibration_metrics(y_true, y_prob))
    out.update(threshold_metrics(y_true, y_prob))
    return out


def resolve_split_count(y: np.ndarray, requested_splits: int) -> int:
    class_counts = pd.Series(y).value_counts().to_dict()
    if len(class_counts) < 2:
        raise ValueError("Incremental-validity analysis requires both CPC groups in the filtered cohort.")
    max_splits = int(min(class_counts.values()))
    if max_splits < 2:
        raise ValueError(
            "Incremental-validity analysis needs at least two subjects in each outcome group for cross-validation."
        )
    return min(requested_splits, max_splits)


def evaluate_repeated_cv(frame: pd.DataFrame, feature_sets: Dict[str, List[str]], config: Config) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    active_feature_sets = get_active_feature_sets(feature_sets)
    if not active_feature_sets:
        raise ValueError("Incremental-validity analysis requires at least one non-empty feature set.")
    y = frame["label"].astype(int).to_numpy()
    n_splits = resolve_split_count(y, config.n_splits)
    folds = RepeatedStratifiedKFold(
        n_splits=n_splits,
        n_repeats=config.n_repeats,
        random_state=config.random_state,
    )
    fold_rows: List[Dict[str, Any]] = []
    prediction_rows: List[pd.DataFrame] = []
    coefficient_rows: List[Dict[str, Any]] = []
    baseline_scores: Dict[int, Dict[str, float]] = {}
    baseline_model = "clinical_plus_eeg" if "clinical_plus_eeg" in active_feature_sets else None

    x_all = frame.drop(columns=["subject", "hospital", "label", "label_name"]).copy()

    for fold_idx, (train_idx, test_idx) in enumerate(folds.split(x_all, y)):
        for model_name, columns in active_feature_sets.items():
            x_train = x_all.iloc[train_idx][columns]
            x_test = x_all.iloc[test_idx][columns]
            model = make_classifier(config.random_state)
            model.fit(x_train, y[train_idx])
            y_prob = model.predict_proba(x_test)[:, 1]
            metric_row = compute_metrics(y[test_idx], y_prob)
            fold_rows.append(
                {
                    "evaluation": "repeated_stratified_cv",
                    "fold": fold_idx,
                    "model": model_name,
                    "n_train": int(len(train_idx)),
                    "n_test": int(len(test_idx)),
                    "n_features": int(len(columns)),
                    **metric_row,
                }
            )
            if model_name == baseline_model:
                baseline_scores[fold_idx] = metric_row
            prediction_rows.append(
                pd.DataFrame(
                    {
                        "evaluation": "repeated_stratified_cv",
                        "fold": fold_idx,
                        "model": model_name,
                        "subject": frame.iloc[test_idx]["subject"].astype(str).to_numpy(),
                        "label": y[test_idx],
                        "prob_cpc1": y_prob,
                    }
                )
            )
            coefficients = model.named_steps["logreg"].coef_[0]
            for feature_name, coef in zip(columns, coefficients):
                coefficient_rows.append(
                    {
                        "evaluation": "repeated_stratified_cv",
                        "fold": fold_idx,
                        "model": model_name,
                        "feature": feature_name,
                        "coef": float(coef),
                        "abs_coef": float(abs(coef)),
                    }
                )

    fold_scores = pd.DataFrame(fold_rows)
    if baseline_model is not None and not fold_scores.empty:
        for metric in ("roc_auc", "average_precision", "brier_score"):
            fold_scores[f"delta_{metric}_vs_clinical_plus_eeg"] = fold_scores.apply(
                lambda row: float(row[metric] - baseline_scores[int(row["fold"])][metric])
                if row["model"] != baseline_model and int(row["fold"]) in baseline_scores
                else 0.0 if row["model"] == baseline_model
                else np.nan,
                axis=1,
            )
    predictions = pd.concat(prediction_rows, ignore_index=True) if prediction_rows else pd.DataFrame()
    return fold_scores, predictions, pd.DataFrame(coefficient_rows)


def evaluate_leave_one_site_out(frame: pd.DataFrame, feature_sets: Dict[str, List[str]], config: Config) -> pd.DataFrame:
    active_feature_sets = get_active_feature_sets(feature_sets)
    if not active_feature_sets:
        return pd.DataFrame()
    y = frame["label"].astype(int).to_numpy()
    groups = frame["hospital"].fillna("missing").astype(str).to_numpy()
    x_all = frame.drop(columns=["subject", "hospital", "label", "label_name"]).copy()
    splitter = LeaveOneGroupOut()
    rows: List[Dict[str, Any]] = []

    for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(x_all, y, groups)):
        if len(np.unique(y[test_idx])) < 2 or len(np.unique(y[train_idx])) < 2:
            continue
        held_out_site = pd.Series(groups[test_idx]).mode().iloc[0]
        for model_name, columns in active_feature_sets.items():
            eval_columns = [column for column in columns if not column.startswith("cat__hospital_")]
            if not eval_columns:
                continue
            model = make_classifier(config.random_state)
            model.fit(x_all.iloc[train_idx][eval_columns], y[train_idx])
            y_prob = model.predict_proba(x_all.iloc[test_idx][eval_columns])[:, 1]
            rows.append(
                {
                    "evaluation": "leave_one_site_out",
                    "fold": fold_idx,
                    "held_out_site": held_out_site,
                    "model": model_name,
                    "n_train": int(len(train_idx)),
                    "n_test": int(len(test_idx)),
                    "n_features": int(len(eval_columns)),
                    "site_dummy_excluded": True,
                    **compute_metrics(y[test_idx], y_prob),
                }
            )
    return pd.DataFrame(rows)


def summarize_scores(scores: pd.DataFrame) -> pd.DataFrame:
    if scores.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for (evaluation, model), group in scores.groupby(["evaluation", "model"], sort=False):
        row: Dict[str, Any] = {
            "evaluation": evaluation,
            "model": model,
            "n_folds": int(len(group)),
            "n_features_median": int(group["n_features"].median()),
        }
        for metric in (
            "roc_auc",
            "average_precision",
            "brier_score",
            "calibration_slope",
            "calibration_intercept",
            "sensitivity",
            "specificity",
        ):
            values = group[metric].to_numpy(dtype=float)
            row[f"{metric}_mean"] = float(np.mean(values))
            row[f"{metric}_sd"] = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
            if len(values) > 1 and np.isfinite(values).any():
                boot = np.random.default_rng(20260517 + len(rows) + len(metric))
                samples = boot.choice(values, size=(5000, len(values)), replace=True)
                means = np.mean(samples, axis=1)
                row[f"{metric}_ci_low"] = float(np.quantile(means, 0.025))
                row[f"{metric}_ci_high"] = float(np.quantile(means, 0.975))
            else:
                row[f"{metric}_ci_low"] = float(values[0]) if len(values) == 1 else float("nan")
                row[f"{metric}_ci_high"] = float(values[0]) if len(values) == 1 else float("nan")
            if f"delta_{metric}_vs_clinical_plus_eeg" in group.columns:
                deltas = group[f"delta_{metric}_vs_clinical_plus_eeg"].to_numpy(dtype=float)
                row[f"delta_{metric}_mean"] = float(np.mean(deltas))
                row[f"delta_{metric}_sd"] = float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0
                if len(deltas) > 1 and np.isfinite(deltas).any():
                    boot = np.random.default_rng(20260617 + len(rows) + len(metric))
                    samples = boot.choice(deltas, size=(5000, len(deltas)), replace=True)
                    means = np.mean(samples, axis=1)
                    row[f"delta_{metric}_ci_low"] = float(np.quantile(means, 0.025))
                    row[f"delta_{metric}_ci_high"] = float(np.quantile(means, 0.975))
                    _, p_value = stats.ttest_1samp(deltas, 0.0, nan_policy="omit")
                    row[f"delta_{metric}_p_ttest"] = float(p_value)
                else:
                    row[f"delta_{metric}_ci_low"] = float(deltas[0]) if len(deltas) == 1 else float("nan")
                    row[f"delta_{metric}_ci_high"] = float(deltas[0]) if len(deltas) == 1 else float("nan")
                    row[f"delta_{metric}_p_ttest"] = float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_coefficients(coefficients: pd.DataFrame) -> pd.DataFrame:
    if coefficients.empty:
        return pd.DataFrame()
    return (
        coefficients.groupby(["evaluation", "model", "feature"], as_index=False)
        .agg(mean_abs_coef=("abs_coef", "mean"), mean_coef=("coef", "mean"), sd_coef=("coef", "std"))
        .sort_values(["evaluation", "model", "mean_abs_coef"], ascending=[True, True, False])
    )


def format_feature_list(columns: List[str]) -> str:
    if not columns:
        return "(none)"
    return ", ".join(f"`{column}`" for column in columns)


def write_markdown(
    config: Config,
    cohort: pd.DataFrame,
    summary: pd.DataFrame,
    site_summary: pd.DataFrame,
    coefficient_summary: pd.DataFrame,
    feature_sets: Dict[str, List[str]],
) -> str:
    effective_n_splits = resolve_split_count(cohort["label"].astype(int).to_numpy(), config.n_splits)
    lines = [
        "# Incremental Validity Summary",
        "",
        f"Primary endpoint cohort: `{config.good_label}` vs `{config.poor_label}` in `{config.primary_time_bin}`.",
        "",
        "## Cohort",
        "",
        f"- n_subjects: {len(cohort)}",
        f"- {config.good_label}: {int((cohort['label'] == 1).sum())}",
        f"- {config.poor_label}: {int((cohort['label'] == 0).sum())}",
        "",
        "## Cross-validation procedure",
        "",
        f"- repeated CV splitter: `RepeatedStratifiedKFold(n_splits={effective_n_splits}, n_repeats={config.n_repeats}, random_state={config.random_state})`",
        "- site sensitivity: `LeaveOneGroupOut()` with hospital as held-out group",
        "- classifier: median imputation -> z-scoring -> `LogisticRegression(solver=liblinear, class_weight=balanced, max_iter=1000)`",
        "- feature handling: fixed feature sets, with no additional fold-wise feature selection or univariate screening inside the CV loop",
        "- selection boundary: the five geometry features were chosen before CV from the same locked cohort and should therefore be read as an internally validated post-selection exploratory layer rather than an externally frozen biomarker panel",
        "- LOSO handling: `cat__hospital_*` dummy columns are excluded from evaluation to avoid out-of-support extrapolation in the held-out site",
        "",
        "## Feature sets",
        "",
        f"- `clinical_only` ({len(feature_sets['clinical_only'])}): {format_feature_list(feature_sets['clinical_only'])}",
        f"- `eeg_only` ({len(feature_sets['eeg_only'])}): {format_feature_list(feature_sets['eeg_only'])}",
        f"- `clinical_plus_eeg` ({len(feature_sets['clinical_plus_eeg'])}): fixed union of clinical and EEG features",
        f"- `clinical_plus_eeg_plus_geometry` ({len(feature_sets['clinical_plus_eeg_plus_geometry'])}): fixed union of clinical, EEG, and geometry features",
        f"- geometry features ({len([column for column in feature_sets['clinical_plus_eeg_plus_geometry'] if column.startswith('geom_')])}): {format_feature_list([column for column in feature_sets['clinical_plus_eeg_plus_geometry'] if column.startswith('geom_')])}",
        "",
        "## Repeated Stratified CV",
        "",
        "| Model | Features | ROC AUC | AUPRC | Brier | Cal. slope | Cal. intercept | Sens. @0.5 | Spec. @0.5 | Delta AUC vs clinical+EEG |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    repeated = summary[summary["evaluation"] == "repeated_stratified_cv"].copy()
    for _, row in repeated.iterrows():
        lines.append(
            f"| {row['model']} | {int(row['n_features_median'])} | "
            f"{row['roc_auc_mean']:.3f} +/- {row['roc_auc_sd']:.3f} [{row['roc_auc_ci_low']:.3f}, {row['roc_auc_ci_high']:.3f}] | "
            f"{row['average_precision_mean']:.3f} +/- {row['average_precision_sd']:.3f} [{row['average_precision_ci_low']:.3f}, {row['average_precision_ci_high']:.3f}] | "
            f"{row['brier_score_mean']:.3f} +/- {row['brier_score_sd']:.3f} [{row['brier_score_ci_low']:.3f}, {row['brier_score_ci_high']:.3f}] | "
            f"{row['calibration_slope_mean']:.3f} | "
            f"{row['calibration_intercept_mean']:+.3f} | "
            f"{row['sensitivity_mean']:.3f} | "
            f"{row['specificity_mean']:.3f} | "
            f"{row.get('delta_roc_auc_mean', 0.0):+.3f} |"
        )
    geometry_row = repeated[repeated["model"] == "clinical_plus_eeg_plus_geometry"]
    if not geometry_row.empty:
        row = geometry_row.iloc[0]
        lines.extend(
            [
                "",
                "## Geometry delta versus clinical + EEG",
                "",
                f"- delta ROC AUC: `{row['delta_roc_auc_mean']:+.3f}` (95% bootstrap CI `{row['delta_roc_auc_ci_low']:+.3f}` to `{row['delta_roc_auc_ci_high']:+.3f}`, paired t-test `p = {row['delta_roc_auc_p_ttest']:.3g}`)",
                f"- delta AUPRC: `{row['delta_average_precision_mean']:+.3f}` (95% bootstrap CI `{row['delta_average_precision_ci_low']:+.3f}` to `{row['delta_average_precision_ci_high']:+.3f}`, paired t-test `p = {row['delta_average_precision_p_ttest']:.3g}`)",
                f"- delta Brier: `{row['delta_brier_score_mean']:+.3f}` (95% bootstrap CI `{row['delta_brier_score_ci_low']:+.3f}` to `{row['delta_brier_score_ci_high']:+.3f}`, paired t-test `p = {row['delta_brier_score_p_ttest']:.3g}`)",
            ]
        )
    if not site_summary.empty:
        lines.extend(["", "## Leave-One-Site-Out", ""])
        for _, row in site_summary.iterrows():
            lines.append(
                f"- `{row['model']}`: roc_auc={row['roc_auc_mean']:.3f} +/- {row['roc_auc_sd']:.3f}, "
                f"auprc={row['average_precision_mean']:.3f} +/- {row['average_precision_sd']:.3f}, "
                f"brier={row['brier_score_mean']:.3f} +/- {row['brier_score_sd']:.3f}, "
                f"cal_slope={row['calibration_slope_mean']:.3f}, cal_intercept={row['calibration_intercept_mean']:+.3f}"
            )
        lines.extend(
            [
                "",
                "Brier deltas follow the usual score orientation, so more negative values indicate improvement.",
                "Sensitivity and specificity are reported at a fixed probability threshold of `0.5` as an internal operating-point summary rather than as a bedside decision threshold recommendation.",
            ]
        )
    if not coefficient_summary.empty:
        lines.extend(["", "## Top geometry-augmented coefficients", ""])
        top = coefficient_summary[coefficient_summary["model"] == "clinical_plus_eeg_plus_geometry"].head(12)
        lines.append("| Feature | Mean abs coef | Mean signed coef |")
        lines.append("|---|---:|---:|")
        for _, row in top.iterrows():
            lines.append(f"| {row['feature']} | {row['mean_abs_coef']:.3f} | {row['mean_coef']:+.3f} |")
    return "\n".join(lines) + "\n"


def write_figures(config: Config, summary: pd.DataFrame, coefficient_summary: pd.DataFrame) -> None:
    config.figure_dir.mkdir(parents=True, exist_ok=True)
    repeated = summary[summary["evaluation"] == "repeated_stratified_cv"].copy()
    if repeated.empty:
        return

    model_order = ["clinical_only", "eeg_only", "clinical_plus_eeg", "clinical_plus_eeg_plus_geometry"]
    repeated = repeated.set_index("model").loc[[model for model in model_order if model in set(repeated["model"])]].reset_index()

    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    x = np.arange(len(repeated))
    ax.bar(x, repeated["roc_auc_mean"], color="#2563eb", alpha=0.85)
    ax.errorbar(x, repeated["roc_auc_mean"], yerr=repeated["roc_auc_sd"], fmt="none", ecolor="#334155", capsize=3, linewidth=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels([MODEL_DISPLAY_LABELS.get(model, model) for model in repeated["model"]], rotation=12)
    ax.set_ylabel("ROC AUC")
    ax.set_ylim(0.45, 1.02)
    ax.set_title("Incremental validity for CPC1 vs CPC5")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(config.figure_dir / "fig_incremental_validity_auc.svg", format="svg", bbox_inches="tight")
    plt.close(fig)

    delta = repeated[repeated["model"] != "clinical_plus_eeg"].copy()
    if not delta.empty:
        fig, ax = plt.subplots(figsize=(8.8, 4.4))
        x = np.arange(len(delta))
        ax.axhline(0, color="#64748b", linestyle="--", linewidth=1.0)
        ax.bar(x, delta["delta_roc_auc_mean"], color="#16a34a", alpha=0.85)
        ax.errorbar(x, delta["delta_roc_auc_mean"], yerr=delta["delta_roc_auc_sd"], fmt="none", ecolor="#334155", capsize=3, linewidth=1.0)
        ax.set_xticks(x)
        ax.set_xticklabels([MODEL_DISPLAY_LABELS.get(model, model) for model in delta["model"]], rotation=12)
        ax.set_ylabel("Delta ROC AUC vs clinical+EEG")
        ax.set_title("Added value of geometry layer")
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        fig.savefig(config.figure_dir / "fig_incremental_validity_delta_auc.svg", format="svg", bbox_inches="tight")
        plt.close(fig)

    if not coefficient_summary.empty:
        top = coefficient_summary[coefficient_summary["model"] == "clinical_plus_eeg_plus_geometry"].head(12).sort_values("mean_abs_coef")
        if not top.empty:
            fig, ax = plt.subplots(figsize=(8.5, 5.0))
            ax.barh(top["feature"], top["mean_abs_coef"], color="#7c3aed", alpha=0.85)
            ax.set_xlabel("Mean absolute standardized coefficient")
            ax.set_title("Top geometry-augmented coefficients")
            ax.spines[["top", "right"]].set_visible(False)
            fig.tight_layout()
            fig.savefig(config.figure_dir / "fig_incremental_validity_feature_weights.svg", format="svg", bbox_inches="tight")
            plt.close(fig)


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    cohort = build_model_frame(config)
    feature_sets = get_feature_sets(cohort)
    repeated_scores, predictions, coefficients = evaluate_repeated_cv(cohort, feature_sets, config)
    site_scores = evaluate_leave_one_site_out(cohort, feature_sets, config)
    repeated_summary = summarize_scores(repeated_scores)
    site_summary = summarize_scores(site_scores)
    coefficient_summary = summarize_coefficients(coefficients)

    cohort.to_csv(config.output_dir / "incremental_validity_cohort.csv", index=False)
    repeated_scores.to_csv(config.output_dir / "incremental_validity_fold_scores.csv", index=False)
    predictions.to_csv(config.output_dir / "incremental_validity_predictions.csv", index=False)
    coefficients.to_csv(config.output_dir / "incremental_validity_feature_coefficients.csv", index=False)
    repeated_summary.to_csv(config.output_dir / "incremental_validity_summary.csv", index=False)
    site_summary.to_csv(config.output_dir / "incremental_validity_site_summary.csv", index=False)
    coefficient_summary.to_csv(config.output_dir / "incremental_validity_feature_summary.csv", index=False)
    (config.output_dir / "incremental_validity_manifest.json").write_text(
        json.dumps(
            {
                "timeline_dir": str(config.timeline_dir),
                "mnps_dir": str(config.mnps_dir),
                "primary_time_bin": config.primary_time_bin,
                "good_label": config.good_label,
                "poor_label": config.poor_label,
                "good_cpc": config.good_cpc,
                "poor_cpc": config.poor_cpc,
                "n_splits": config.n_splits,
                "n_repeats": config.n_repeats,
                "effective_n_splits": resolve_split_count(cohort["label"].astype(int).to_numpy(), config.n_splits),
                "feature_sets": {key: value for key, value in feature_sets.items()},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (config.output_dir / "incremental_validity_summary.md").write_text(
        write_markdown(config, cohort, repeated_summary, site_summary, coefficient_summary, feature_sets),
        encoding="utf-8",
    )

    summary_for_figures = pd.concat([repeated_summary, site_summary], ignore_index=True)
    write_figures(config, summary_for_figures, coefficient_summary)

    print(f"Wrote incremental-validity cohort to {config.output_dir / 'incremental_validity_cohort.csv'}")
    print(f"Wrote repeated-CV scores to {config.output_dir / 'incremental_validity_fold_scores.csv'}")
    print(f"Wrote site-aware summary to {config.output_dir / 'incremental_validity_site_summary.csv'}")
    print(f"Wrote figures to {config.figure_dir}")


if __name__ == "__main__":
    main()
