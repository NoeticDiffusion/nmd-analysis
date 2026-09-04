from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut, RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from jacobian_9d_support import (
    COORDINATE_COMPARATORS,
    EEG_BASELINE_COLUMNS,
    JACOBIAN_3D_FEATURES,
    PREDICTION_DIR,
    REACHABILITY_FEATURES,
    REVISED_CORE_METRICS,
    assemble_pooled_cohort,
)


N_SPLITS = 5
N_REPEATS = 20

BOOTSTRAP_DRAWS = 5000


def make_classifier() -> Pipeline:
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
                    random_state=20260525,
                ),
            ),
        ]
    )


def resolve_split_count(y: np.ndarray, requested_splits: int) -> int:
    class_counts = pd.Series(y).value_counts().to_dict()
    if len(class_counts) < 2:
        raise ValueError("Incremental-validity analysis requires both CPC groups in the filtered cohort.")
    return min(requested_splits, int(min(class_counts.values())))


def build_model_frame() -> pd.DataFrame:
    frame = assemble_pooled_cohort(include_reachability=True).copy()
    frame["hospital"] = frame["hospital"].fillna("missing").astype(str)
    frame["sex"] = frame["sex"].fillna("missing").astype(str)

    clinical_numeric = frame[
        [
            "subject",
            "hospital",
            "label",
            "label_name",
            "age",
            "rosc_minutes",
            "ttm_celsius",
            "channel_count_median",
            "channel_coverage_frac_median",
            "shockable_rhythm",
            "ohca",
        ]
    ].copy()
    clinical_numeric = clinical_numeric.rename(
        columns={
            "age": "clinical__age",
            "rosc_minutes": "clinical__rosc_minutes",
            "ttm_celsius": "clinical__ttm_celsius",
            "channel_count_median": "clinical__channel_count_median",
            "channel_coverage_frac_median": "clinical__channel_coverage_frac_median",
            "shockable_rhythm": "clinical__shockable_rhythm",
            "ohca": "clinical__ohca",
        }
    )

    sex_dummies = pd.get_dummies(frame["sex"], prefix="cat__sex")
    hospital_dummies = pd.get_dummies(frame["hospital"], prefix="cat__hospital")

    eeg_frame = frame[list(EEG_BASELINE_COLUMNS)].copy().add_prefix("eeg__")
    jacobian9d_frame = frame[list(REVISED_CORE_METRICS)].copy().add_prefix("jac9d__")
    reachability_frame = frame[list(REACHABILITY_FEATURES)].copy().add_prefix("reach__")
    jacobian3d_frame = frame[list(JACOBIAN_3D_FEATURES)].copy().add_prefix("jac3d__")
    coord_frame = frame[list(COORDINATE_COMPARATORS)].copy().add_prefix("coord9d__")

    out = pd.concat(
        [
            clinical_numeric.reset_index(drop=True),
            sex_dummies.reset_index(drop=True),
            hospital_dummies.reset_index(drop=True),
            eeg_frame.reset_index(drop=True),
            jacobian9d_frame.reset_index(drop=True),
            reachability_frame.reset_index(drop=True),
            jacobian3d_frame.reset_index(drop=True),
            coord_frame.reset_index(drop=True),
        ],
        axis=1,
    )
    return out


def get_feature_sets(frame: pd.DataFrame) -> dict[str, list[str]]:
    clinical = [col for col in frame.columns if col.startswith("clinical__") or col.startswith("cat__")]
    eeg = [col for col in frame.columns if col.startswith("eeg__")]
    jac9d = [col for col in frame.columns if col.startswith("jac9d__")]
    reach = [col for col in frame.columns if col.startswith("reach__")]
    jac3d = [col for col in frame.columns if col.startswith("jac3d__")]
    coord = [col for col in frame.columns if col.startswith("coord9d__")]
    return {
        "clinical_only": clinical,
        "eeg_only": eeg,
        "clinical_plus_eeg": clinical + eeg,
        "jacobian9d_only": jac9d,
        "reachability_only": reach,
        "jacobian3d_only": jac3d,
        "coords9d_only": coord,
        "clinical_plus_eeg_plus_jacobian9d": clinical + eeg + jac9d,
        "clinical_plus_eeg_plus_reachability": clinical + eeg + reach,
        "clinical_plus_eeg_plus_jacobian3d": clinical + eeg + jac3d,
        "clinical_plus_eeg_plus_reachability_plus_jacobian9d": clinical + eeg + reach + jac9d,
    }


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    return {
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "average_precision": float(average_precision_score(y_true, y_prob)),
        "brier_score": float(brier_score_loss(y_true, y_prob)),
    }


def format_feature_list(columns: list[str]) -> str:
    if not columns:
        return "(none)"
    return ", ".join(f"`{column}`" for column in columns)


def bootstrap_mean_interval(values: np.ndarray, *, seed: int) -> tuple[float, float]:
    if values.size == 0:
        return float("nan"), float("nan")
    if values.size == 1:
        return float(values[0]), float(values[0])
    boot = np.random.default_rng(seed)
    samples = boot.choice(values, size=(BOOTSTRAP_DRAWS, len(values)), replace=True)
    means = np.mean(samples, axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def evaluate_repeated_cv(frame: pd.DataFrame, feature_sets: dict[str, list[str]]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    y = frame["label"].astype(int).to_numpy()
    x_all = frame.drop(columns=["subject", "hospital", "label", "label_name"]).copy()
    n_splits = resolve_split_count(y, N_SPLITS)
    splitter = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=N_REPEATS, random_state=20260525)
    fold_rows = []
    prediction_rows = []
    coefficient_rows = []
    baseline_by_fold: dict[int, dict[str, float]] = {}
    reachability_by_fold: dict[int, dict[str, float]] = {}

    for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(x_all, y)):
        for model_name, columns in feature_sets.items():
            if not columns:
                continue
            model = make_classifier()
            x_train = x_all.iloc[train_idx][columns]
            x_test = x_all.iloc[test_idx][columns]
            model.fit(x_train, y[train_idx])
            y_prob = model.predict_proba(x_test)[:, 1]
            metric_row = compute_metrics(y[test_idx], y_prob)
            fold_rows.append(
                {
                    "evaluation": "repeated_stratified_cv",
                    "fold": int(fold_idx),
                    "model": model_name,
                    "n_features": int(len(columns)),
                    **metric_row,
                }
            )
            if model_name == "clinical_plus_eeg":
                baseline_by_fold[fold_idx] = metric_row
            if model_name == "clinical_plus_eeg_plus_reachability":
                reachability_by_fold[fold_idx] = metric_row
            prediction_rows.append(
                pd.DataFrame(
                    {
                        "evaluation": "repeated_stratified_cv",
                        "fold": int(fold_idx),
                        "model": model_name,
                        "subject": frame.iloc[test_idx]["subject"].astype(str).to_numpy(),
                        "label": y[test_idx],
                        "prob_cpc1": y_prob,
                    }
                )
            )
            coefficients = model.named_steps["logreg"].coef_[0]
            for feature, coef in zip(columns, coefficients):
                coefficient_rows.append(
                    {
                        "evaluation": "repeated_stratified_cv",
                        "fold": int(fold_idx),
                        "model": model_name,
                        "feature": feature,
                        "coef": float(coef),
                        "abs_coef": float(abs(coef)),
                    }
                )

    fold_scores = pd.DataFrame(fold_rows)
    for metric in ("roc_auc", "average_precision", "brier_score"):
        fold_scores[f"delta_{metric}_vs_clinical_plus_eeg"] = fold_scores.apply(
            lambda row: float(row[metric] - baseline_by_fold[int(row["fold"])][metric])
            if int(row["fold"]) in baseline_by_fold
            else np.nan,
            axis=1,
        )
        fold_scores[f"delta_{metric}_vs_clinical_plus_eeg_plus_reachability"] = fold_scores.apply(
            lambda row: float(row[metric] - reachability_by_fold[int(row["fold"])][metric])
            if int(row["fold"]) in reachability_by_fold
            else np.nan,
            axis=1,
        )
    predictions = pd.concat(prediction_rows, ignore_index=True)
    coefficients = pd.DataFrame(coefficient_rows)
    return fold_scores, predictions, coefficients


def evaluate_leave_one_site_out(frame: pd.DataFrame, feature_sets: dict[str, list[str]]) -> pd.DataFrame:
    y = frame["label"].astype(int).to_numpy()
    groups = frame["hospital"].fillna("missing").astype(str).to_numpy()
    x_all = frame.drop(columns=["subject", "hospital", "label", "label_name"]).copy()
    splitter = LeaveOneGroupOut()
    rows = []
    for model_name, columns in feature_sets.items():
        loso_columns = [col for col in columns if not col.startswith("cat__hospital_")]
        if not loso_columns:
            continue
        for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(x_all, y, groups)):
            if len(np.unique(y[train_idx])) < 2 or len(np.unique(y[test_idx])) < 2:
                continue
            model = make_classifier()
            model.fit(x_all.iloc[train_idx][loso_columns], y[train_idx])
            y_prob = model.predict_proba(x_all.iloc[test_idx][loso_columns])[:, 1]
            rows.append(
                {
                    "evaluation": "leave_one_site_out",
                    "fold": int(fold_idx),
                    "held_out_site": groups[test_idx][0],
                    "model": model_name,
                    "n_features": int(len(loso_columns)),
                    **compute_metrics(y[test_idx], y_prob),
                }
            )
    return pd.DataFrame(rows)


def summarize_scores(scores: pd.DataFrame, *, delta_columns: list[str] | None = None) -> pd.DataFrame:
    rows = []
    delta_columns = delta_columns or []
    for model_name, group in scores.groupby("model", sort=False):
        row: dict[str, Any] = {
            "model": model_name,
            "n_rows": int(len(group)),
            "n_features": int(group["n_features"].median()),
        }
        for metric in ("roc_auc", "average_precision", "brier_score", *delta_columns):
            if metric not in group.columns:
                continue
            values = pd.to_numeric(group[metric], errors="coerce").dropna().to_numpy(dtype=float)
            if values.size == 0:
                continue
            row[f"{metric}_mean"] = float(np.mean(values))
            row[f"{metric}_sd"] = float(np.std(values, ddof=1)) if values.size > 1 else 0.0
            ci_low, ci_high = bootstrap_mean_interval(values, seed=20260527 + len(rows) + len(metric))
            row[f"{metric}_ci_low"] = ci_low
            row[f"{metric}_ci_high"] = ci_high
            if metric.startswith("delta_"):
                if values.size > 1 and np.isfinite(values).any():
                    _, p_value = stats.ttest_1samp(values, 0.0, nan_policy="omit")
                    row[f"{metric}_p_ttest"] = float(p_value)
                else:
                    row[f"{metric}_p_ttest"] = float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_coefficients(coefficients: pd.DataFrame) -> pd.DataFrame:
    if coefficients.empty:
        return pd.DataFrame()
    rows = []
    for (model_name, feature), group in coefficients.groupby(["model", "feature"], sort=False):
        rows.append(
            {
                "model": model_name,
                "feature": feature,
                "mean_coef": float(group["coef"].mean()),
                "mean_abs_coef": float(group["abs_coef"].mean()),
            }
        )
    out = pd.DataFrame(rows)
    return out.sort_values(["model", "mean_abs_coef"], ascending=[True, False]).reset_index(drop=True)


def build_correlation_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    selected = [
        *[f"jac9d__{metric}" for metric in REVISED_CORE_METRICS],
        *[f"reach__{metric}" for metric in REACHABILITY_FEATURES],
        *[f"jac3d__{metric}" for metric in JACOBIAN_3D_FEATURES],
        *[f"coord9d__{metric}" for metric in COORDINATE_COMPARATORS],
    ]
    selected = [col for col in selected if col in frame.columns]
    return frame[selected].corr(method="spearman")


def build_summary_markdown(
    frame: pd.DataFrame,
    repeated_summary: pd.DataFrame,
    loso_summary: pd.DataFrame,
    coefficient_summary: pd.DataFrame,
    feature_sets: dict[str, list[str]],
) -> str:
    lines = [
        "# 9D Jacobian Incremental Validity Summary",
        "",
        f"- n_subjects: `{int(len(frame))}`",
        f"- CPC1: `{int((frame['label'] == 1).sum())}`",
        f"- CPC5: `{int((frame['label'] == 0).sum())}`",
        "",
        "## Cross-validation procedure",
        "",
        f"- repeated CV splitter: `RepeatedStratifiedKFold(n_splits={N_SPLITS}, n_repeats={N_REPEATS}, random_state=20260525)`",
        "- site sensitivity: `LeaveOneGroupOut()` with hospital as held-out group",
        "- classifier: median imputation -> z-scoring -> `LogisticRegression(solver=liblinear, class_weight=balanced, max_iter=1000)`",
        "- feature handling: fixed feature ladders with no in-fold feature selection or univariate screening",
        "- LOSO handling: `cat__hospital_*` dummy columns are dropped in held-out-site evaluation",
        "",
        "## Feature ladders",
        "",
        f"- `clinical_plus_eeg` ({len(feature_sets['clinical_plus_eeg'])}): fixed union of clinical and EEG baseline features",
        f"- `jacobian9d_only` ({len(feature_sets['jacobian9d_only'])}): {format_feature_list(feature_sets['jacobian9d_only'])}",
        f"- `reachability_only` ({len(feature_sets['reachability_only'])}): {format_feature_list(feature_sets['reachability_only'])}",
        f"- `jacobian3d_only` ({len(feature_sets['jacobian3d_only'])}): {format_feature_list(feature_sets['jacobian3d_only'])}",
        f"- `clinical_plus_eeg_plus_jacobian9d` ({len(feature_sets['clinical_plus_eeg_plus_jacobian9d'])}): clinical + EEG + revised 9D",
        f"- `clinical_plus_eeg_plus_reachability` ({len(feature_sets['clinical_plus_eeg_plus_reachability'])}): clinical + EEG + reachability",
        f"- `clinical_plus_eeg_plus_reachability_plus_jacobian9d` ({len(feature_sets['clinical_plus_eeg_plus_reachability_plus_jacobian9d'])}): clinical + EEG + reachability + revised 9D",
        "",
        "## Repeated CV",
        "",
    ]
    for _, row in repeated_summary.iterrows():
        line = (
            f"- `{row['model']}`: AUROC `{row['roc_auc_mean']:.3f} [{row['roc_auc_ci_low']:.3f}, {row['roc_auc_ci_high']:.3f}]`, "
            f"AUPRC `{row['average_precision_mean']:.3f} [{row['average_precision_ci_low']:.3f}, {row['average_precision_ci_high']:.3f}]`, "
            f"Brier `{row['brier_score_mean']:.3f} [{row['brier_score_ci_low']:.3f}, {row['brier_score_ci_high']:.3f}]`"
        )
        if pd.notna(row.get("delta_roc_auc_vs_clinical_plus_eeg_mean")):
            line += (
                f"; delta AUROC vs `clinical_plus_eeg` "
                f"`{row['delta_roc_auc_vs_clinical_plus_eeg_mean']:+.3f} "
                f"[{row['delta_roc_auc_vs_clinical_plus_eeg_ci_low']:+.3f}, {row['delta_roc_auc_vs_clinical_plus_eeg_ci_high']:+.3f}]`"
            )
        if pd.notna(row.get("delta_roc_auc_vs_clinical_plus_eeg_plus_reachability_mean")):
            line += (
                f"; delta AUROC vs `clinical_plus_eeg_plus_reachability` "
                f"`{row['delta_roc_auc_vs_clinical_plus_eeg_plus_reachability_mean']:+.3f} "
                f"[{row['delta_roc_auc_vs_clinical_plus_eeg_plus_reachability_ci_low']:+.3f}, "
                f"{row['delta_roc_auc_vs_clinical_plus_eeg_plus_reachability_ci_high']:+.3f}]`"
            )
        lines.append(line)
    lines.extend(["", "## Leave-One-Site-Out", ""])
    for _, row in loso_summary.iterrows():
        lines.append(
            f"- `{row['model']}`: AUROC `{row['roc_auc_mean']:.3f} [{row['roc_auc_ci_low']:.3f}, {row['roc_auc_ci_high']:.3f}]`, "
            f"AUPRC `{row['average_precision_mean']:.3f} [{row['average_precision_ci_low']:.3f}, {row['average_precision_ci_high']:.3f}]`, "
            f"Brier `{row['brier_score_mean']:.3f} [{row['brier_score_ci_low']:.3f}, {row['brier_score_ci_high']:.3f}]`"
        )
    lines.extend(["", "## Paired delta summary", ""])
    delta_rows = [
        (
            "clinical_plus_eeg_plus_jacobian9d",
            "`clinical_plus_eeg_plus_jacobian9d` vs `clinical_plus_eeg`",
            "delta_roc_auc_vs_clinical_plus_eeg",
            "delta_average_precision_vs_clinical_plus_eeg",
            "delta_brier_score_vs_clinical_plus_eeg",
        ),
        (
            "clinical_plus_eeg_plus_reachability",
            "`clinical_plus_eeg_plus_reachability` vs `clinical_plus_eeg`",
            "delta_roc_auc_vs_clinical_plus_eeg",
            "delta_average_precision_vs_clinical_plus_eeg",
            "delta_brier_score_vs_clinical_plus_eeg",
        ),
        (
            "clinical_plus_eeg_plus_reachability_plus_jacobian9d",
            "`clinical_plus_eeg_plus_reachability_plus_jacobian9d` vs `clinical_plus_eeg_plus_reachability`",
            "delta_roc_auc_vs_clinical_plus_eeg_plus_reachability",
            "delta_average_precision_vs_clinical_plus_eeg_plus_reachability",
            "delta_brier_score_vs_clinical_plus_eeg_plus_reachability",
        ),
    ]
    for model_name, label, roc_col, pr_col, brier_col in delta_rows:
        subset = repeated_summary[repeated_summary["model"] == model_name]
        if subset.empty:
            continue
        row = subset.iloc[0]
        lines.append(
            f"- {label}: "
            f"delta AUROC `{row[f'{roc_col}_mean']:+.3f} [{row[f'{roc_col}_ci_low']:+.3f}, {row[f'{roc_col}_ci_high']:+.3f}]` "
            f"(paired `p = {row.get(f'{roc_col}_p_ttest', float('nan')):.4g}`), "
            f"delta AUPRC `{row[f'{pr_col}_mean']:+.3f} [{row[f'{pr_col}_ci_low']:+.3f}, {row[f'{pr_col}_ci_high']:+.3f}]`, "
            f"delta Brier `{row[f'{brier_col}_mean']:+.3f} [{row[f'{brier_col}_ci_low']:+.3f}, {row[f'{brier_col}_ci_high']:+.3f}]`"
        )
    combined = coefficient_summary[
        coefficient_summary["model"] == "clinical_plus_eeg_plus_reachability_plus_jacobian9d"
    ].head(10)
    if not combined.empty:
        lines.extend(["", "## Top combined-model coefficients", ""])
        for _, row in combined.iterrows():
            lines.append(
                f"- `{row['feature']}`: mean abs coef `{row['mean_abs_coef']:.3f}`, mean signed coef `{row['mean_coef']:.3f}`"
            )
    lines.append("")
    return "\n".join(lines)


def build_delta_summary(repeated_summary: pd.DataFrame) -> pd.DataFrame:
    comparisons = [
        {
            "model": "clinical_plus_eeg_plus_jacobian9d",
            "comparison": "clinical_plus_eeg_plus_jacobian9d_vs_clinical_plus_eeg",
            "roc_col": "delta_roc_auc_vs_clinical_plus_eeg",
            "pr_col": "delta_average_precision_vs_clinical_plus_eeg",
            "brier_col": "delta_brier_score_vs_clinical_plus_eeg",
        },
        {
            "model": "clinical_plus_eeg_plus_reachability",
            "comparison": "clinical_plus_eeg_plus_reachability_vs_clinical_plus_eeg",
            "roc_col": "delta_roc_auc_vs_clinical_plus_eeg",
            "pr_col": "delta_average_precision_vs_clinical_plus_eeg",
            "brier_col": "delta_brier_score_vs_clinical_plus_eeg",
        },
        {
            "model": "clinical_plus_eeg_plus_reachability_plus_jacobian9d",
            "comparison": "clinical_plus_eeg_plus_reachability_plus_jacobian9d_vs_clinical_plus_eeg_plus_reachability",
            "roc_col": "delta_roc_auc_vs_clinical_plus_eeg_plus_reachability",
            "pr_col": "delta_average_precision_vs_clinical_plus_eeg_plus_reachability",
            "brier_col": "delta_brier_score_vs_clinical_plus_eeg_plus_reachability",
        },
    ]
    rows: list[dict[str, Any]] = []
    for spec in comparisons:
        subset = repeated_summary[repeated_summary["model"] == spec["model"]]
        if subset.empty:
            continue
        row = subset.iloc[0]
        rows.append(
            {
                "model": spec["model"],
                "comparison": spec["comparison"],
                "delta_roc_auc_mean": row[f"{spec['roc_col']}_mean"],
                "delta_roc_auc_ci_low": row[f"{spec['roc_col']}_ci_low"],
                "delta_roc_auc_ci_high": row[f"{spec['roc_col']}_ci_high"],
                "delta_roc_auc_p_ttest": row.get(f"{spec['roc_col']}_p_ttest", float("nan")),
                "delta_average_precision_mean": row[f"{spec['pr_col']}_mean"],
                "delta_average_precision_ci_low": row[f"{spec['pr_col']}_ci_low"],
                "delta_average_precision_ci_high": row[f"{spec['pr_col']}_ci_high"],
                "delta_average_precision_p_ttest": row.get(f"{spec['pr_col']}_p_ttest", float("nan")),
                "delta_brier_score_mean": row[f"{spec['brier_col']}_mean"],
                "delta_brier_score_ci_low": row[f"{spec['brier_col']}_ci_low"],
                "delta_brier_score_ci_high": row[f"{spec['brier_col']}_ci_high"],
                "delta_brier_score_p_ttest": row.get(f"{spec['brier_col']}_p_ttest", float("nan")),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    PREDICTION_DIR.mkdir(parents=True, exist_ok=True)
    frame = build_model_frame()
    feature_sets = get_feature_sets(frame)
    repeated_scores, predictions, coefficients = evaluate_repeated_cv(frame, feature_sets)
    loso_scores = evaluate_leave_one_site_out(frame, feature_sets)
    repeated_summary = summarize_scores(
        repeated_scores,
        delta_columns=[
            "delta_roc_auc_vs_clinical_plus_eeg",
            "delta_average_precision_vs_clinical_plus_eeg",
            "delta_brier_score_vs_clinical_plus_eeg",
            "delta_roc_auc_vs_clinical_plus_eeg_plus_reachability",
            "delta_average_precision_vs_clinical_plus_eeg_plus_reachability",
            "delta_brier_score_vs_clinical_plus_eeg_plus_reachability",
        ],
    )
    loso_summary = summarize_scores(loso_scores)
    coefficient_summary = summarize_coefficients(coefficients)
    correlation_matrix = build_correlation_matrix(frame)
    delta_summary = build_delta_summary(repeated_summary)

    frame.to_csv(PREDICTION_DIR / "incremental_validity_cohort.csv", index=False)
    repeated_scores.to_csv(PREDICTION_DIR / "incremental_validity_fold_scores.csv", index=False)
    predictions.to_csv(PREDICTION_DIR / "incremental_validity_predictions.csv", index=False)
    coefficients.to_csv(PREDICTION_DIR / "incremental_validity_feature_coefficients.csv", index=False)
    coefficient_summary.to_csv(PREDICTION_DIR / "incremental_validity_feature_summary.csv", index=False)
    repeated_summary.to_csv(PREDICTION_DIR / "incremental_validity_summary.csv", index=False)
    delta_summary.to_csv(PREDICTION_DIR / "incremental_validity_delta_summary.csv", index=False)
    loso_summary.to_csv(PREDICTION_DIR / "incremental_validity_site_summary.csv", index=False)
    correlation_matrix.to_csv(PREDICTION_DIR / "joint_signal_correlation_matrix.csv")
    (PREDICTION_DIR / "incremental_validity_summary.md").write_text(
        build_summary_markdown(frame, repeated_summary, loso_summary, coefficient_summary, feature_sets),
        encoding="utf-8",
    )
    manifest = {
        "output_dir": str(PREDICTION_DIR),
        "n_subjects": int(len(frame)),
        "feature_sets": {model: len(columns) for model, columns in feature_sets.items()},
        "revised_core_metrics": list(REVISED_CORE_METRICS),
        "reachability_features": list(REACHABILITY_FEATURES),
        "jacobian3d_features": list(JACOBIAN_3D_FEATURES),
        "coordinate_comparators": list(COORDINATE_COMPARATORS),
        "n_splits": N_SPLITS,
        "n_repeats": N_REPEATS,
    }
    (PREDICTION_DIR / "incremental_validity_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote 9D Jacobian incremental-validity outputs to {PREDICTION_DIR}")


if __name__ == "__main__":
    main()
