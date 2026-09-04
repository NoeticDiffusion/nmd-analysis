from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import LeaveOneOut, RepeatedStratifiedKFold

from incremental_validity_analysis import compute_metrics, get_feature_sets, make_classifier, summarize_scores


ARTICLE_DIR = Path(__file__).resolve().parents[1]

PRIMARY_TIME_BIN = "0_12h"
HOURLY_BINS = [f"{hour}_{hour + 1}h" for hour in range(12)]
GOOD_CPC = 1
POOR_CPC = 5
DEFAULT_RANDOM_STATE = 20260602
DEFAULT_SHIFT_PERMUTATIONS = 1000
DEFAULT_CROSSFIT_SPLITS = 5
DEFAULT_CROSSFIT_REPEATS = 20
DEFAULT_CROSSFIT_TOP_K = 5

SELECTED_METRICS: tuple[tuple[str, str, str], ...] = (
    ("reachability_cones", "tube_d_eff_median", "reachability_tube_d_eff_median"),
    ("reachability_cones", "persistence_log_eig_var_median", "reachability_persistence_log_eig_var_median"),
    ("reachability_cones", "tube_capture_gate_median", "reachability_tube_capture_gate_median"),
    ("global_mnps_jacobian_3d", "spectral_radius_median", "mnj3d_spectral_radius_median"),
    ("global_mnps_jacobian_9d", "spectral_radius_median", "mnj9d_spectral_radius_median"),
)

REACHABILITY_EXCLUDE = {
    "__unit_weight__",
    "dims",
    "horizon",
    "k",
    "in_dim",
    "out_dim",
    "source_dim",
    "target_dim",
}


@dataclass(frozen=True)
class Config:
    incremental_cohort_path: Path
    primary_metrics_path: Path
    hourly_metrics_path: Path
    output_dir: Path
    random_state: int
    shift_permutations: int
    crossfit_splits: int
    crossfit_repeats: int
    crossfit_top_k: int


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Run additional QC / robustness checks for the corrected-ComBat coma cohort.")
    parser.add_argument("--incremental-cohort-path", type=Path, required=True)
    parser.add_argument("--primary-metrics-path", type=Path, required=True)
    parser.add_argument("--hourly-metrics-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--random-state", type=int, default=DEFAULT_RANDOM_STATE)
    parser.add_argument("--shift-permutations", type=int, default=DEFAULT_SHIFT_PERMUTATIONS)
    parser.add_argument("--crossfit-splits", type=int, default=DEFAULT_CROSSFIT_SPLITS)
    parser.add_argument("--crossfit-repeats", type=int, default=DEFAULT_CROSSFIT_REPEATS)
    parser.add_argument("--crossfit-top-k", type=int, default=DEFAULT_CROSSFIT_TOP_K)
    args = parser.parse_args()
    return Config(
        incremental_cohort_path=args.incremental_cohort_path,
        primary_metrics_path=args.primary_metrics_path,
        hourly_metrics_path=args.hourly_metrics_path,
        output_dir=args.output_dir,
        random_state=args.random_state,
        shift_permutations=args.shift_permutations,
        crossfit_splits=args.crossfit_splits,
        crossfit_repeats=args.crossfit_repeats,
        crossfit_top_k=args.crossfit_top_k,
    )


def cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    left = left[np.isfinite(left)]
    right = right[np.isfinite(right)]
    if left.size < 2 or right.size < 2:
        return float("nan")
    pooled = ((left.size - 1) * np.var(left, ddof=1) + (right.size - 1) * np.var(right, ddof=1)) / (left.size + right.size - 2)
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(left) - np.mean(right)) / np.sqrt(pooled))


def mannwhitney_p(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    left = left[np.isfinite(left)]
    right = right[np.isfinite(right)]
    if left.size < 2 or right.size < 2:
        return float("nan")
    return float(stats.mannwhitneyu(left, right, alternative="two-sided").pvalue)


def load_incremental_cohort(config: Config) -> pd.DataFrame:
    frame = pd.read_csv(config.incremental_cohort_path)
    frame["label"] = pd.to_numeric(frame["label"], errors="coerce").astype(int)
    return frame


def load_selected_primary_metrics(config: Config) -> pd.DataFrame:
    frame = pd.read_csv(config.primary_metrics_path, low_memory=False)
    frame = frame[frame["time_bin"].astype(str) == PRIMARY_TIME_BIN].copy()
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([float(GOOD_CPC), float(POOR_CPC)])].copy()
    rows: list[pd.DataFrame] = []
    for analysis_type, metric, feature_name in SELECTED_METRICS:
        sub = frame[(frame["analysis_type"] == analysis_type) & (frame["metric"] == metric)].copy()
        if sub.empty:
            continue
        keep = sub[["subject", "hospital", "cpc_numeric", "value"]].copy()
        keep["feature_name"] = feature_name
        rows.append(keep)
    if not rows:
        return pd.DataFrame(columns=["subject", "hospital", "cpc_numeric", "feature_name", "value"])
    out = pd.concat(rows, ignore_index=True)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out


def build_primary_metric_wide(selected_primary: pd.DataFrame) -> pd.DataFrame:
    if selected_primary.empty:
        return pd.DataFrame()
    wide = (
        selected_primary.pivot_table(index=["subject", "hospital", "cpc_numeric"], columns="feature_name", values="value", aggfunc="first")
        .reset_index()
    )
    wide["label"] = np.where(wide["cpc_numeric"] == float(GOOD_CPC), 1, 0)
    return wide


def summarize_omit_effects(frame: pd.DataFrame, *, metric_col: str, omit_column: str, omit_kind: str) -> Dict[str, Any]:
    working = frame[["subject", "hospital", "label", metric_col]].copy()
    working[metric_col] = pd.to_numeric(working[metric_col], errors="coerce")
    working = working[np.isfinite(working[metric_col])].copy()
    left = working.loc[working["label"] == 1, metric_col].to_numpy(dtype=float)
    right = working.loc[working["label"] == 0, metric_col].to_numpy(dtype=float)
    full_d = cohens_d(left, right)
    full_p = mannwhitney_p(left, right)
    loo_ds: list[float] = []
    loo_ps: list[float] = []
    omitted_ids: list[str] = []
    for omit_value in working[omit_column].dropna().astype(str).unique().tolist():
        reduced = working[working[omit_column].astype(str) != omit_value].copy()
        left_r = reduced.loc[reduced["label"] == 1, metric_col].to_numpy(dtype=float)
        right_r = reduced.loc[reduced["label"] == 0, metric_col].to_numpy(dtype=float)
        if left_r.size < 3 or right_r.size < 3:
            continue
        d_r = cohens_d(left_r, right_r)
        p_r = mannwhitney_p(left_r, right_r)
        if np.isfinite(d_r):
            loo_ds.append(d_r)
            loo_ps.append(p_r)
            omitted_ids.append(omit_value)
    sign_consistency = float(np.mean(np.sign(loo_ds) == np.sign(full_d))) if loo_ds and np.isfinite(full_d) else float("nan")
    return {
        "metric": metric_col,
        "omit_kind": omit_kind,
        "full_d": full_d,
        "full_mannwhitney_p": full_p,
        "n_omits": int(len(loo_ds)),
        "leave_one_out_d_min": float(np.min(loo_ds)) if loo_ds else float("nan"),
        "leave_one_out_d_max": float(np.max(loo_ds)) if loo_ds else float("nan"),
        "leave_one_out_d_median": float(np.median(loo_ds)) if loo_ds else float("nan"),
        "leave_one_out_p_min": float(np.min(loo_ps)) if loo_ps else float("nan"),
        "leave_one_out_p_max": float(np.max(loo_ps)) if loo_ps else float("nan"),
        "sign_consistency": sign_consistency,
        "worst_case_omission": omitted_ids[int(np.argmin(np.abs(loo_ds)))] if loo_ds else "",
    }


def build_leave_one_out_tables(primary_wide: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_cols = [feature_name for _, _, feature_name in SELECTED_METRICS if feature_name in primary_wide.columns]
    subject_rows = [summarize_omit_effects(primary_wide, metric_col=metric, omit_column="subject", omit_kind="subject") for metric in metric_cols]
    site_rows = [summarize_omit_effects(primary_wide, metric_col=metric, omit_column="hospital", omit_kind="site") for metric in metric_cols]
    return pd.DataFrame(subject_rows), pd.DataFrame(site_rows)


def compute_binary_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    return {
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "average_precision": float(average_precision_score(y_true, y_prob)),
        "brier_score": float(brier_score_loss(y_true, y_prob)),
    }


def evaluate_leave_one_out_prediction(cohort: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_sets = get_feature_sets(cohort)
    models = {
        "clinical_plus_eeg": feature_sets["clinical_plus_eeg"],
        "clinical_plus_eeg_plus_geometry": feature_sets["clinical_plus_eeg_plus_geometry"],
    }
    x_all = cohort.drop(columns=["subject", "hospital", "label", "label_name"]).copy()
    y = cohort["label"].astype(int).to_numpy()
    splitter = LeaveOneOut()
    prediction_rows: list[dict[str, Any]] = []
    for model_name, columns in models.items():
        probs = np.full(len(cohort), np.nan, dtype=float)
        for train_idx, test_idx in splitter.split(x_all):
            model = make_classifier(DEFAULT_RANDOM_STATE)
            model.fit(x_all.iloc[train_idx][columns], y[train_idx])
            probs[test_idx] = model.predict_proba(x_all.iloc[test_idx][columns])[:, 1]
            prediction_rows.append(
                {
                    "model": model_name,
                    "subject": str(cohort.iloc[test_idx[0]]["subject"]),
                    "label": int(y[test_idx[0]]),
                    "prob_cpc1": float(probs[test_idx[0]]),
                }
            )
    predictions = pd.DataFrame(prediction_rows)
    rows: list[dict[str, Any]] = []
    for model_name in models:
        sub = predictions[predictions["model"] == model_name].copy()
        rows.append(
            {
                "evaluation": "leave_one_subject_out",
                "model": model_name,
                "n_subjects": int(len(sub)),
                "n_features": int(len(models[model_name])),
                **compute_binary_metrics(sub["label"].to_numpy(dtype=int), sub["prob_cpc1"].to_numpy(dtype=float)),
            }
        )
    return predictions, pd.DataFrame(rows)


def is_reachability_candidate(metric: str) -> bool:
    return metric.endswith("_median") and metric not in REACHABILITY_EXCLUDE and not metric.endswith("_finite_frac")


def load_reachability_candidate_matrix(config: Config) -> pd.DataFrame:
    frame = pd.read_csv(config.primary_metrics_path, low_memory=False)
    frame = frame[
        (frame["time_bin"].astype(str) == PRIMARY_TIME_BIN)
        & (frame["analysis_type"] == "reachability_cones")
    ].copy()
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([float(GOOD_CPC), float(POOR_CPC)])].copy()
    frame = frame[frame["metric"].astype(str).map(is_reachability_candidate)].copy()
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[np.isfinite(frame["value"])].copy()
    wide = frame.pivot_table(index=["subject", "hospital", "cpc_numeric"], columns="metric", values="value", aggfunc="first").reset_index()
    wide["label"] = np.where(wide["cpc_numeric"] == float(GOOD_CPC), 1, 0)
    return wide


def rank_training_metrics(train_frame: pd.DataFrame, candidate_cols: list[str]) -> list[str]:
    ranked: list[tuple[float, str]] = []
    for metric in candidate_cols:
        sub = train_frame[["label", metric]].copy()
        sub[metric] = pd.to_numeric(sub[metric], errors="coerce")
        sub = sub[np.isfinite(sub[metric])].copy()
        left = sub.loc[sub["label"] == 1, metric].to_numpy(dtype=float)
        right = sub.loc[sub["label"] == 0, metric].to_numpy(dtype=float)
        if left.size < 8 or right.size < 8:
            continue
        ranked.append((mannwhitney_p(left, right), metric))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return [metric for _, metric in ranked]


def run_cross_fitted_selection(cohort: pd.DataFrame, candidate_matrix: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    merged = cohort.merge(
        candidate_matrix.drop(columns=["hospital", "cpc_numeric", "label"], errors="ignore"),
        on="subject",
        how="inner",
    )
    feature_sets = get_feature_sets(cohort)
    base_columns = feature_sets["clinical_plus_eeg"]
    fixed_geometry_columns = feature_sets["clinical_plus_eeg_plus_geometry"]
    candidate_cols = sorted(
        column
        for column in merged.columns
        if column not in {"subject", "hospital", "label", "label_name"} and column not in set(feature_sets["clinical_plus_eeg_plus_geometry"])
    )
    x_all = merged.drop(columns=["subject", "hospital", "label", "label_name"]).copy()
    y = merged["label"].astype(int).to_numpy()
    splitter = RepeatedStratifiedKFold(
        n_splits=min(config.crossfit_splits, int(pd.Series(y).value_counts().min())),
        n_repeats=config.crossfit_repeats,
        random_state=config.random_state,
    )
    fold_rows: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
    for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(x_all, y)):
        train_frame = merged.iloc[train_idx].copy()
        ranked_metrics = rank_training_metrics(train_frame, candidate_cols)
        selected_metrics = ranked_metrics[: config.crossfit_top_k]
        model_specs = {
            "clinical_plus_eeg": base_columns,
            "fixed_clinical_plus_eeg_plus_geometry": fixed_geometry_columns,
        }
        if selected_metrics:
            model_specs["crossfit_clinical_plus_eeg_plus_geometry"] = base_columns + selected_metrics
            model_specs["crossfit_geometry_only"] = selected_metrics
        for model_name, columns in model_specs.items():
            model = make_classifier(config.random_state)
            model.fit(x_all.iloc[train_idx][columns], y[train_idx])
            y_prob = model.predict_proba(x_all.iloc[test_idx][columns])[:, 1]
            fold_rows.append(
                {
                    "evaluation": "cross_fitted_repeated_cv",
                    "fold": fold_idx,
                    "model": model_name,
                    "n_train": int(len(train_idx)),
                    "n_test": int(len(test_idx)),
                    "n_features": int(len(columns)),
                    "selected_metric_count": int(len(selected_metrics)),
                    "selected_metrics": ";".join(selected_metrics),
                    **compute_metrics(y[test_idx], y_prob),
                }
            )
            for subject, label, prob in zip(merged.iloc[test_idx]["subject"].astype(str), y[test_idx], y_prob):
                prediction_rows.append(
                    {
                        "evaluation": "cross_fitted_repeated_cv",
                        "fold": fold_idx,
                        "model": model_name,
                        "subject": subject,
                        "label": int(label),
                        "prob_cpc1": float(prob),
                    }
                )
        for metric in selected_metrics:
            selected_rows.append({"fold": fold_idx, "metric": metric})
    fold_scores = pd.DataFrame(fold_rows)
    selected_df = pd.DataFrame(selected_rows)
    frequency = (
        selected_df.groupby("metric", as_index=False)
        .agg(n_selected=("metric", "size"))
        .sort_values(["n_selected", "metric"], ascending=[False, True])
        .reset_index(drop=True)
        if not selected_df.empty
        else pd.DataFrame(columns=["metric", "n_selected"])
    )
    summary = summarize_scores(fold_scores)
    return fold_scores, summary, frequency


def load_hourly_metric_panel(config: Config) -> pd.DataFrame:
    frame = pd.read_csv(config.hourly_metrics_path, low_memory=False)
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[
        frame["cpc_numeric"].isin([float(GOOD_CPC), float(POOR_CPC)])
        & frame["time_bin"].isin(HOURLY_BINS)
    ].copy()
    rows: list[pd.DataFrame] = []
    for analysis_type, metric, feature_name in SELECTED_METRICS:
        sub = frame[(frame["analysis_type"] == analysis_type) & (frame["metric"] == metric)].copy()
        if sub.empty:
            continue
        keep = sub[["subject", "time_bin", "cpc_numeric", "value"]].copy()
        keep["feature_name"] = feature_name
        keep["value"] = pd.to_numeric(keep["value"], errors="coerce")
        rows.append(keep)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["subject", "time_bin", "cpc_numeric", "value", "feature_name"])


def hourly_effects(values: np.ndarray, labels: np.ndarray) -> np.ndarray:
    out = np.full(values.shape[1], np.nan, dtype=float)
    for idx in range(values.shape[1]):
        column = values[:, idx]
        left = column[(labels == 1) & np.isfinite(column)]
        right = column[(labels == 0) & np.isfinite(column)]
        if left.size < 3 or right.size < 3:
            continue
        out[idx] = cohens_d(left, right)
    return out


def run_time_shift_null(hourly_panel: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(config.random_state)
    summary_rows: list[dict[str, Any]] = []
    draw_rows: list[dict[str, Any]] = []
    if hourly_panel.empty:
        return pd.DataFrame(), pd.DataFrame()
    for feature_name in sorted(hourly_panel["feature_name"].unique()):
        sub = hourly_panel[hourly_panel["feature_name"] == feature_name].copy()
        wide = (
            sub.pivot_table(index=["subject", "cpc_numeric"], columns="time_bin", values="value", aggfunc="first")
            .reindex(columns=HOURLY_BINS)
            .reset_index()
        )
        value_matrix = wide[HOURLY_BINS].to_numpy(dtype=float)
        labels = np.where(pd.to_numeric(wide["cpc_numeric"], errors="coerce").to_numpy(dtype=float) == float(GOOD_CPC), 1, 0)
        observed_effects = hourly_effects(value_matrix, labels)
        if not np.isfinite(observed_effects).any():
            continue
        peak_idx = int(np.nanargmax(np.abs(observed_effects)))
        observed_peak = float(observed_effects[peak_idx])
        observed_peak_abs = float(abs(observed_peak))
        null_max = np.empty(config.shift_permutations, dtype=float)
        for perm_idx in range(config.shift_permutations):
            shifted = np.empty_like(value_matrix)
            shifts = rng.integers(1, len(HOURLY_BINS), size=value_matrix.shape[0])
            for row_idx, shift in enumerate(shifts):
                shifted[row_idx] = np.roll(value_matrix[row_idx], int(shift))
            shifted_effects = hourly_effects(shifted, labels)
            null_max[perm_idx] = float(np.nanmax(np.abs(shifted_effects)))
            draw_rows.append(
                {
                    "metric": feature_name,
                    "permutation": int(perm_idx),
                    "null_max_abs_d": float(null_max[perm_idx]),
                }
            )
        summary_rows.append(
            {
                "metric": feature_name,
                "observed_peak_bin": HOURLY_BINS[peak_idx],
                "observed_peak_d": observed_peak,
                "observed_peak_abs_d": observed_peak_abs,
                "null_mean_max_abs_d": float(np.mean(null_max)),
                "null_p95_max_abs_d": float(np.quantile(null_max, 0.95)),
                "empirical_p": float((1.0 + np.sum(null_max >= observed_peak_abs)) / (len(null_max) + 1.0)),
            }
        )
    return pd.DataFrame(summary_rows), pd.DataFrame(draw_rows)


def format_float(value: Any, digits: int = 3) -> str:
    value = float(value) if value is not None and not pd.isna(value) else float("nan")
    return "nan" if not np.isfinite(value) else f"{value:.{digits}f}"


def build_markdown(
    cohort: pd.DataFrame,
    subject_loo: pd.DataFrame,
    site_loo: pd.DataFrame,
    loo_cv_summary: pd.DataFrame,
    crossfit_summary: pd.DataFrame,
    crossfit_frequency: pd.DataFrame,
    time_shift_summary: pd.DataFrame,
) -> str:
    lines = [
        "# Additional QC / robustness summary",
        "",
        f"- cohort subjects: `{len(cohort)}`",
        f"- CPC1 subjects: `{int((cohort['label'] == 1).sum())}`",
        f"- CPC5 subjects: `{int((cohort['label'] == 0).sum())}`",
        "",
        "## Leave-one-subject-out metric stability",
        "",
    ]
    for _, row in subject_loo.iterrows():
        lines.append(
            f"- `{row['metric']}`: full `d = {format_float(row['full_d'])}`, "
            f"leave-one-subject-out range `{format_float(row['leave_one_out_d_min'])}` to `{format_float(row['leave_one_out_d_max'])}`, "
            f"sign consistency `{format_float(row['sign_consistency'])}`"
        )
    lines.extend(["", "## Leave-one-site-out metric stability", ""])
    for _, row in site_loo.iterrows():
        lines.append(
            f"- `{row['metric']}`: full `d = {format_float(row['full_d'])}`, "
            f"leave-one-site-out range `{format_float(row['leave_one_out_d_min'])}` to `{format_float(row['leave_one_out_d_max'])}`, "
            f"sign consistency `{format_float(row['sign_consistency'])}`"
        )
    lines.extend(["", "## Leave-one-subject-out prediction", ""])
    for _, row in loo_cv_summary.iterrows():
        lines.append(
            f"- `{row['model']}`: `AUROC = {format_float(row['roc_auc'])}`, "
            f"`AUPRC = {format_float(row['average_precision'])}`, `Brier = {format_float(row['brier_score'])}`"
        )
    lines.extend(["", "## Cross-fitted repeated CV", ""])
    for _, row in crossfit_summary.iterrows():
        lines.append(
            f"- `{row['model']}`: `AUROC = {format_float(row['roc_auc_mean'])} +/- {format_float(row['roc_auc_sd'])}`, "
            f"`AUPRC = {format_float(row['average_precision_mean'])} +/- {format_float(row['average_precision_sd'])}`, "
            f"`Brier = {format_float(row['brier_score_mean'])} +/- {format_float(row['brier_score_sd'])}`"
        )
    if not crossfit_frequency.empty:
        lines.extend(["", "Top cross-fitted reachability metrics:", ""])
        for _, row in crossfit_frequency.head(10).iterrows():
            lines.append(f"- `{row['metric']}` selected in `{int(row['n_selected'])}` folds")
    lines.extend(["", "## Hourly time-shift null", ""])
    for _, row in time_shift_summary.iterrows():
        lines.append(
            f"- `{row['metric']}`: observed peak `{row['observed_peak_bin']}` with `d = {format_float(row['observed_peak_d'])}`, "
            f"null mean max `|d| = {format_float(row['null_mean_max_abs_d'])}`, "
            f"null p95 `{format_float(row['null_p95_max_abs_d'])}`, empirical `p = {format_float(row['empirical_p'])}`"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    cohort = load_incremental_cohort(config)
    selected_primary = load_selected_primary_metrics(config)
    primary_wide = build_primary_metric_wide(selected_primary)
    subject_loo, site_loo = build_leave_one_out_tables(primary_wide)
    loo_predictions, loo_cv_summary = evaluate_leave_one_out_prediction(cohort)
    candidate_matrix = load_reachability_candidate_matrix(config)
    crossfit_fold_scores, crossfit_summary, crossfit_frequency = run_cross_fitted_selection(cohort, candidate_matrix, config)
    hourly_panel = load_hourly_metric_panel(config)
    time_shift_summary, time_shift_draws = run_time_shift_null(hourly_panel, config)

    subject_loo.to_csv(config.output_dir / "qc_leave_one_subject_out_metrics.csv", index=False)
    site_loo.to_csv(config.output_dir / "qc_leave_one_site_out_metrics.csv", index=False)
    loo_predictions.to_csv(config.output_dir / "qc_leave_one_subject_out_predictions.csv", index=False)
    loo_cv_summary.to_csv(config.output_dir / "qc_leave_one_subject_out_prediction_summary.csv", index=False)
    crossfit_fold_scores.to_csv(config.output_dir / "qc_cross_fitted_fold_scores.csv", index=False)
    crossfit_summary.to_csv(config.output_dir / "qc_cross_fitted_summary.csv", index=False)
    crossfit_frequency.to_csv(config.output_dir / "qc_cross_fitted_metric_frequency.csv", index=False)
    time_shift_summary.to_csv(config.output_dir / "qc_time_shift_hourly_summary.csv", index=False)
    time_shift_draws.to_csv(config.output_dir / "qc_time_shift_hourly_null_draws.csv", index=False)

    summary_md = build_markdown(
        cohort,
        subject_loo,
        site_loo,
        loo_cv_summary,
        crossfit_summary,
        crossfit_frequency,
        time_shift_summary,
    )
    (config.output_dir / "additional_qc_summary.md").write_text(summary_md, encoding="utf-8")
    (config.output_dir / "additional_qc_manifest.json").write_text(
        json.dumps(
            {
                "incremental_cohort_path": str(config.incremental_cohort_path),
                "primary_metrics_path": str(config.primary_metrics_path),
                "hourly_metrics_path": str(config.hourly_metrics_path),
                "shift_permutations": config.shift_permutations,
                "crossfit_splits": config.crossfit_splits,
                "crossfit_repeats": config.crossfit_repeats,
                "crossfit_top_k": config.crossfit_top_k,
                "selected_metrics": [
                    {"analysis_type": analysis_type, "metric": metric, "feature_name": feature_name}
                    for analysis_type, metric, feature_name in SELECTED_METRICS
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote additional QC outputs to {config.output_dir}")


if __name__ == "__main__":
    main()
