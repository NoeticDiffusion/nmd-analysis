from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut, RepeatedStratifiedKFold

from incremental_validity_analysis import (
    CLINICAL_BASELINE_COLUMNS,
    CLINICAL_BOOLEAN_COLUMNS,
    CLINICAL_CATEGORICAL_COLUMNS,
    EEG_BASELINE_COLUMNS,
    compute_metrics,
    make_classifier,
    normalize_bool_series,
    resolve_split_count,
)


ARTICLE_DIR = Path(__file__).resolve().parents[1]
TRAJECTORY_ARTICLE_DIR = ARTICLE_DIR.parent / "comatose_geometric_trajectory"
RESULT_STAMP = "20260604"
PRIMARY_TIME_BIN = "0_12h"
GOOD_CPC = 1
POOR_CPC = 5
RDR_PATH_LAMBDA = 0.25
DEFAULT_RANDOM_STATE = 20260604
DEFAULT_N_SPLITS = 5
DEFAULT_N_REPEATS = 20
DEFAULT_N_PERMUTATIONS = 2000

DEFAULT_TIMELINE_DIR = (
    ARTICLE_DIR / "results" / "timeline_analysis_20260602_combined_combat_corrected_primary12h"
)
DEFAULT_MNPS_DIR = (
    ARTICLE_DIR / "results" / "mnps_summary_20260602_combined_combat_corrected_primary12h_cpc15"
)
DEFAULT_TRAJECTORY_PART1_DIR = (
    TRAJECTORY_ARTICLE_DIR / "results" / "trajectory_metrics_20260601_part1_primary12h"
)
DEFAULT_TRAJECTORY_PART2_DIR = (
    TRAJECTORY_ARTICLE_DIR / "results" / "trajectory_metrics_20260601_part2_primary12h"
)
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / f"rdr_composite_{RESULT_STAMP}_cpc15_primary12h"

CORE_FEATURE_SPECS: dict[str, tuple[str, str]] = {
    "reach_tube_d_eff_median": ("reachability_cones", "tube_d_eff_median"),
    "reach_tube_capture_gate_median": ("reachability_cones", "tube_capture_gate_median"),
    "mnj3d_spectral_radius_median": ("global_mnps_jacobian_3d", "spectral_radius_median"),
    "mnj3d_frobenius_norm_median": ("global_mnps_jacobian_3d", "frobenius_norm_median"),
    "mnj9d_spectral_radius_median": ("global_mnps_jacobian_9d", "spectral_radius_median"),
}
TRAJECTORY_FEATURE_SPECS: dict[str, tuple[str, str]] = {
    "trajectory_3d_noetic_action": ("trajectory_geometry_subject_anchored_3d", "noetic_action"),
}
CORE_RDR_COLUMNS = (
    "reach_tube_d_eff_median",
    "reach_tube_capture_gate_median",
    "mnj3d_spectral_radius_median",
    "mnj3d_frobenius_norm_median",
)
RECOVERY_CONE_COLUMNS = CORE_RDR_COLUMNS
QC_COLUMNS = (
    "n_runs",
    "n_windows_total",
    "metric_weight_total",
    "channel_count_median",
    "channel_coverage_frac_median",
)
ORIENTED_BASELINE_SPECS: dict[str, tuple[str, float, str]] = {
    "score_tube_d_eff_median": ("reach_tube_d_eff_median", 1.0, "higher raw value expected in CPC1"),
    "score_tube_capture_gate_median": (
        "reach_tube_capture_gate_median",
        -1.0,
        "lower raw value expected in CPC1",
    ),
    "score_mnj3d_spectral_radius_median": (
        "mnj3d_spectral_radius_median",
        -1.0,
        "lower raw value expected in CPC1",
    ),
    "score_mnj3d_frobenius_norm_median": (
        "mnj3d_frobenius_norm_median",
        -1.0,
        "lower raw value expected in CPC1",
    ),
    "score_mnj9d_spectral_radius_median": (
        "mnj9d_spectral_radius_median",
        -1.0,
        "lower raw value expected in CPC1",
    ),
    "score_trajectory_3d_noetic_action": (
        "trajectory_3d_noetic_action",
        -1.0,
        "lower raw value expected in CPC1",
    ),
}


@dataclass(frozen=True)
class Config:
    timeline_dir: Path
    mnps_dir: Path
    trajectory_part1_dir: Path
    trajectory_part2_dir: Path
    output_dir: Path
    primary_time_bin: str
    good_cpc: int
    poor_cpc: int
    n_splits: int
    n_repeats: int
    random_state: int
    n_permutations: int
    path_lambda: float


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Build and validate Recovery Dynamical Reserve composites for CPC1 vs CPC5."
    )
    parser.add_argument("--timeline-dir", type=Path, default=DEFAULT_TIMELINE_DIR)
    parser.add_argument("--mnps-dir", type=Path, default=DEFAULT_MNPS_DIR)
    parser.add_argument("--trajectory-part1-dir", type=Path, default=DEFAULT_TRAJECTORY_PART1_DIR)
    parser.add_argument("--trajectory-part2-dir", type=Path, default=DEFAULT_TRAJECTORY_PART2_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--primary-time-bin", type=str, default=PRIMARY_TIME_BIN)
    parser.add_argument("--good-cpc", type=int, default=GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=POOR_CPC)
    parser.add_argument("--n-splits", type=int, default=DEFAULT_N_SPLITS)
    parser.add_argument("--n-repeats", type=int, default=DEFAULT_N_REPEATS)
    parser.add_argument("--random-state", type=int, default=DEFAULT_RANDOM_STATE)
    parser.add_argument("--n-permutations", type=int, default=DEFAULT_N_PERMUTATIONS)
    parser.add_argument("--path-lambda", type=float, default=RDR_PATH_LAMBDA)
    args = parser.parse_args()
    return Config(
        timeline_dir=args.timeline_dir,
        mnps_dir=args.mnps_dir,
        trajectory_part1_dir=args.trajectory_part1_dir,
        trajectory_part2_dir=args.trajectory_part2_dir,
        output_dir=args.output_dir,
        primary_time_bin=args.primary_time_bin,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        n_splits=args.n_splits,
        n_repeats=args.n_repeats,
        random_state=args.random_state,
        n_permutations=args.n_permutations,
        path_lambda=args.path_lambda,
    )


def robust_scale_params(values: pd.Series | np.ndarray) -> tuple[float, float]:
    arr = pd.to_numeric(pd.Series(values), errors="coerce").dropna().to_numpy(dtype=float)
    if arr.size == 0:
        return 0.0, 1.0
    center = float(np.median(arr))
    mad = float(np.median(np.abs(arr - center)))
    scale = 1.4826 * mad
    if not np.isfinite(scale) or scale <= 1e-12:
        q75, q25 = np.quantile(arr, [0.75, 0.25])
        scale = float((q75 - q25) / 1.349)
    if not np.isfinite(scale) or scale <= 1e-12:
        scale = float(np.std(arr, ddof=1)) if arr.size > 1 else 1.0
    if not np.isfinite(scale) or scale <= 1e-12:
        scale = 1.0
    return center, scale


def fit_rdr_params(frame: pd.DataFrame) -> dict[str, tuple[float, float]]:
    needed = set(CORE_RDR_COLUMNS) | {"trajectory_3d_noetic_action"}
    return {column: robust_scale_params(frame[column]) for column in needed if column in frame.columns}


def robust_z(frame: pd.DataFrame, column: str, params: dict[str, tuple[float, float]]) -> pd.Series:
    if column not in frame.columns or column not in params:
        return pd.Series(np.nan, index=frame.index, dtype=float)
    center, scale = params[column]
    return (pd.to_numeric(frame[column], errors="coerce") - center) / scale


def compute_rdr_scores(
    frame: pd.DataFrame,
    params: dict[str, tuple[float, float]],
    *,
    prefix: str,
    path_lambda: float,
) -> pd.DataFrame:
    out = frame.copy()
    z_d_eff = robust_z(out, "reach_tube_d_eff_median", params)
    z_capture = robust_z(out, "reach_tube_capture_gate_median", params)
    z_spectral = robust_z(out, "mnj3d_spectral_radius_median", params)
    z_fro = robust_z(out, "mnj3d_frobenius_norm_median", params)
    z_action = robust_z(out, "trajectory_3d_noetic_action", params)

    deformation_load = pd.concat([z_spectral, z_fro], axis=1).mean(axis=1, skipna=False)
    out[f"rdr_core_{prefix}"] = z_d_eff - z_capture - z_spectral - z_fro
    out[f"rdr_3_{prefix}"] = z_d_eff - z_capture - deformation_load
    out[f"rdr_path_{prefix}"] = out[f"rdr_core_{prefix}"] - path_lambda * z_action
    out = compute_recovery_cone_scores(out, prefix, z_d_eff, z_capture, z_spectral, z_fro)
    return out


def compute_recovery_cone_scores(
    frame: pd.DataFrame,
    prefix: str,
    z_d_eff: pd.Series,
    z_capture: pd.Series,
    z_spectral: pd.Series,
    z_fro: pd.Series,
) -> pd.DataFrame:
    out = frame.copy()
    oriented = pd.concat([z_d_eff, -z_capture, -z_spectral, -z_fro], axis=1)
    oriented.columns = [
        "oriented_d_eff",
        "oriented_low_capture",
        "oriented_low_spectral",
        "oriented_low_frobenius",
    ]
    ideal = np.ones(4, dtype=float) / 2.0
    values = oriented.to_numpy(dtype=float)
    valid = np.isfinite(values).all(axis=1)

    projection = np.full(len(out), np.nan, dtype=float)
    off_axis = np.full(len(out), np.nan, dtype=float)
    cosine = np.full(len(out), np.nan, dtype=float)
    nrca = np.full(len(out), np.nan, dtype=float)
    if valid.any():
        valid_values = values[valid]
        valid_projection = valid_values @ ideal
        residual = valid_values - np.outer(valid_projection, ideal)
        valid_off_axis = np.linalg.norm(residual, axis=1)
        valid_norm = np.linalg.norm(valid_values, axis=1)
        valid_cosine = np.divide(
            valid_projection,
            valid_norm,
            out=np.zeros_like(valid_projection),
            where=valid_norm > 1e-12,
        )
        # NRCA is a signed recovery-cone coordinate: high positive projection toward
        # the ideal recovery ray, discounted when the four geometric axes disagree.
        valid_nrca = valid_projection / np.sqrt(1.0 + valid_off_axis**2)
        projection[valid] = valid_projection
        off_axis[valid] = valid_off_axis
        cosine[valid] = valid_cosine
        nrca[valid] = valid_nrca

    out[f"nrca_projection_{prefix}"] = projection
    out[f"nrca_off_axis_{prefix}"] = off_axis
    out[f"nrca_cosine_{prefix}"] = cosine
    out[f"nrca_{prefix}"] = nrca
    return out


def infer_source_cohort(frame: pd.DataFrame, fallback: str | None = None) -> pd.Series:
    if "source_cohort" in frame.columns:
        source = frame["source_cohort"].astype(str)
    elif "cohort_tag" in frame.columns:
        source = frame["cohort_tag"].astype(str)
    elif fallback is not None:
        source = pd.Series(fallback, index=frame.index, dtype=str)
    elif "bundle_tag" in frame.columns:
        source = frame["bundle_tag"].astype(str).str.extract(r"(part[12])", expand=False)
    else:
        source = pd.Series("unknown", index=frame.index, dtype=str)
    return source.fillna(fallback or "unknown")


def add_join_keys(frame: pd.DataFrame, *, fallback_cohort: str | None = None) -> pd.DataFrame:
    out = frame.copy()
    out["source_cohort"] = infer_source_cohort(out, fallback=fallback_cohort)
    out["subject"] = out["subject"].astype(str)
    out["pooled_subject"] = out["source_cohort"].astype(str) + "::" + out["subject"]
    return out


def pivot_long_metrics(
    frame: pd.DataFrame,
    specs: dict[str, tuple[str, str]],
    *,
    index_columns: tuple[str, ...] = ("pooled_subject",),
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for feature_name, (analysis_type, metric) in specs.items():
        sub = frame[(frame["analysis_type"] == analysis_type) & (frame["metric"] == metric)].copy()
        if sub.empty:
            continue
        keep = [*index_columns, "value"]
        part = sub[keep].copy().rename(columns={"value": feature_name})
        part[feature_name] = pd.to_numeric(part[feature_name], errors="coerce")
        rows.append(part.groupby(list(index_columns), as_index=False)[feature_name].first())
    if not rows:
        return pd.DataFrame(columns=list(index_columns))
    merged = rows[0]
    for part in rows[1:]:
        merged = merged.merge(part, on=list(index_columns), how="outer")
    return merged


def load_timeline(config: Config) -> pd.DataFrame:
    path = config.timeline_dir / "patient_timebin_summaries.csv"
    frame = pd.read_csv(path, low_memory=False)
    frame = add_join_keys(frame)
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[
        (frame["time_bin"] == config.primary_time_bin)
        & (frame["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)]))
    ].copy()
    frame["label"] = np.where(frame["cpc_numeric"] == float(config.good_cpc), 1, 0)
    frame["label_name"] = np.where(frame["label"] == 1, "CPC1", "CPC5")
    for column in CLINICAL_BOOLEAN_COLUMNS:
        if column in frame.columns:
            frame[column] = normalize_bool_series(frame[column])
    for column in [*CLINICAL_BASELINE_COLUMNS, *EEG_BASELINE_COLUMNS, *QC_COLUMNS]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.reset_index(drop=True)


def load_mnps_features(config: Config) -> pd.DataFrame:
    path = config.mnps_dir / "patient_timebin_signal_metrics.csv"
    frame = pd.read_csv(path, low_memory=False)
    frame = add_join_keys(frame)
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[
        (frame["time_bin"] == config.primary_time_bin)
        & (frame["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)]))
    ].copy()
    return pivot_long_metrics(frame, CORE_FEATURE_SPECS)


def load_trajectory_part(path: Path, part: str, config: Config) -> pd.DataFrame:
    csv_path = path / "patient_timebin_trajectory_metrics.csv"
    if not csv_path.exists():
        return pd.DataFrame(columns=["pooled_subject"])
    frame = pd.read_csv(csv_path, low_memory=False)
    frame = add_join_keys(frame, fallback_cohort=part)
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[
        (frame["time_bin"] == config.primary_time_bin)
        & (frame["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)]))
    ].copy()
    return pivot_long_metrics(frame, TRAJECTORY_FEATURE_SPECS)


def build_joined_feature_matrix(config: Config) -> pd.DataFrame:
    timeline = load_timeline(config)
    mnps = load_mnps_features(config)
    trajectory = pd.concat(
        [
            load_trajectory_part(config.trajectory_part1_dir, "part1", config),
            load_trajectory_part(config.trajectory_part2_dir, "part2", config),
        ],
        ignore_index=True,
    )
    if not trajectory.empty:
        trajectory = trajectory.groupby("pooled_subject", as_index=False).first()
    joined = timeline.merge(mnps, on="pooled_subject", how="left")
    joined = joined.merge(trajectory, on="pooled_subject", how="left")
    for score_col, (raw_col, sign, _) in ORIENTED_BASELINE_SPECS.items():
        if raw_col in joined.columns:
            joined[score_col] = sign * pd.to_numeric(joined[raw_col], errors="coerce")
    joined = compute_rdr_scores(joined, fit_rdr_params(joined), prefix="allfit", path_lambda=config.path_lambda)
    part1 = joined[joined["source_cohort"] == "part1"].copy()
    joined = compute_rdr_scores(joined, fit_rdr_params(part1), prefix="part1fit", path_lambda=config.path_lambda)
    return joined.reset_index(drop=True)


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    good = np.asarray(good, dtype=float)
    poor = np.asarray(poor, dtype=float)
    good = good[np.isfinite(good)]
    poor = poor[np.isfinite(poor)]
    if good.size < 2 or poor.size < 2:
        return float("nan")
    pooled = ((good.size - 1) * np.var(good, ddof=1) + (poor.size - 1) * np.var(poor, ddof=1)) / (
        good.size + poor.size - 2
    )
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(good) - np.mean(poor)) / np.sqrt(pooled))


def cliffs_delta(good: np.ndarray, poor: np.ndarray) -> float:
    good = np.asarray(good, dtype=float)
    poor = np.asarray(poor, dtype=float)
    good = good[np.isfinite(good)]
    poor = poor[np.isfinite(poor)]
    if good.size == 0 or poor.size == 0:
        return float("nan")
    diff = np.subtract.outer(good, poor)
    return float((np.sum(diff > 0) - np.sum(diff < 0)) / diff.size)


def summarize_contrasts(frame: pd.DataFrame, metrics: dict[str, str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    cohorts = {"pooled": frame.index == frame.index}
    for cohort in sorted(frame["source_cohort"].dropna().astype(str).unique()):
        cohorts[cohort] = frame["source_cohort"].astype(str) == cohort
    for cohort, mask in cohorts.items():
        sub = frame[mask].copy()
        for metric, label in metrics.items():
            if metric not in sub.columns:
                continue
            values = pd.to_numeric(sub[metric], errors="coerce")
            good = values[sub["label"] == 1].dropna().to_numpy(dtype=float)
            poor = values[sub["label"] == 0].dropna().to_numpy(dtype=float)
            if good.size < 2 or poor.size < 2:
                continue
            all_values = pd.concat([values[sub["label"] == 1], values[sub["label"] == 0]], ignore_index=True)
            all_labels = pd.concat(
                [sub.loc[sub["label"] == 1, "label"], sub.loc[sub["label"] == 0, "label"]],
                ignore_index=True,
            )
            finite = np.isfinite(all_values.to_numpy(dtype=float))
            y = all_labels.to_numpy(dtype=int)[finite]
            score = all_values.to_numpy(dtype=float)[finite]
            u_stat, p_value = stats.mannwhitneyu(good, poor, alternative="two-sided")
            rows.append(
                {
                    "cohort": cohort,
                    "metric": metric,
                    "label": label,
                    "n_cpc1": int(good.size),
                    "n_cpc5": int(poor.size),
                    "cpc1_median": float(np.median(good)),
                    "cpc5_median": float(np.median(poor)),
                    "cohens_d": cohens_d(good, poor),
                    "cliffs_delta": cliffs_delta(good, poor),
                    "mannwhitney_u": float(u_stat),
                    "mannwhitney_p": float(p_value),
                    "direct_auroc_cpc1_high": float(roc_auc_score(y, score)) if len(np.unique(y)) == 2 else np.nan,
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["abs_d"] = out["cohens_d"].abs()
    return out.sort_values(["cohort", "abs_d"], ascending=[True, False]).reset_index(drop=True)


def build_model_base(frame: pd.DataFrame) -> pd.DataFrame:
    base = frame[["pooled_subject", "subject", "source_cohort", "hospital", "label", "label_name"]].copy()
    for column in CLINICAL_BASELINE_COLUMNS:
        if column in frame.columns:
            base[f"clinical__{column}"] = pd.to_numeric(frame[column], errors="coerce")
    for column in CLINICAL_BOOLEAN_COLUMNS:
        if column in frame.columns:
            base[f"clinical__{column}"] = pd.to_numeric(frame[column], errors="coerce")
    categorical_cols = [column for column in CLINICAL_CATEGORICAL_COLUMNS if column in frame.columns]
    if categorical_cols:
        categorical = frame[categorical_cols].fillna("missing").astype(str)
        categorical.columns = [f"cat__{column}" for column in categorical.columns]
        base = base.merge(pd.get_dummies(categorical, prefix=list(categorical.columns), dtype=float), left_index=True, right_index=True)
    for column in EEG_BASELINE_COLUMNS:
        if column in frame.columns:
            base[f"eeg__{column}"] = pd.to_numeric(frame[column], errors="coerce")
    for column in CORE_RDR_COLUMNS:
        if column in frame.columns:
            base[f"raw__{column}"] = pd.to_numeric(frame[column], errors="coerce")
    return base


def active_columns(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    out: list[str] = []
    for column in columns:
        if column in frame.columns and pd.to_numeric(frame[column], errors="coerce").notna().sum() > 0:
            out.append(column)
    return out


def model_feature_sets(base: pd.DataFrame, include_path: bool) -> dict[str, list[str]]:
    clinical = sorted(column for column in base.columns if column.startswith("clinical__") or column.startswith("cat__"))
    eeg = sorted(column for column in base.columns if column.startswith("eeg__"))
    raw_core = active_columns(base, [f"raw__{column}" for column in CORE_RDR_COLUMNS])
    sets = {
        "clinical_plus_eeg": clinical + eeg,
        "rdr_core_only": ["rdr_core_fold"],
        "rdr_3_only": ["rdr_3_fold"],
        "nrca_only": ["nrca_fold"],
        "components_core_only": raw_core,
        "clinical_plus_eeg_plus_rdr_core": clinical + eeg + ["rdr_core_fold"],
        "clinical_plus_eeg_plus_rdr_3": clinical + eeg + ["rdr_3_fold"],
        "clinical_plus_eeg_plus_nrca": clinical + eeg + ["nrca_fold"],
        "clinical_plus_eeg_plus_components_core": clinical + eeg + raw_core,
    }
    if include_path:
        sets["rdr_path_only"] = ["rdr_path_fold"]
        sets["clinical_plus_eeg_plus_rdr_path"] = clinical + eeg + ["rdr_path_fold"]
    return {key: value for key, value in sets.items() if value}


def append_fold_scores(
    base_part: pd.DataFrame,
    raw_part: pd.DataFrame,
    params: dict[str, tuple[float, float]],
    *,
    path_lambda: float,
) -> pd.DataFrame:
    scored = compute_rdr_scores(raw_part, params, prefix="fold", path_lambda=path_lambda)
    out = base_part.copy()
    for column in ("rdr_core_fold", "rdr_3_fold", "rdr_path_fold"):
        if column in scored.columns:
            out[column] = scored[column].to_numpy(dtype=float)
    for column in ("nrca_fold", "nrca_projection_fold", "nrca_off_axis_fold", "nrca_cosine_fold"):
        if column in scored.columns:
            out[column] = scored[column].to_numpy(dtype=float)
    return out


def evaluate_repeated_cv(frame: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = build_model_base(frame)
    include_path = "trajectory_3d_noetic_action" in frame.columns and pd.to_numeric(
        frame["trajectory_3d_noetic_action"], errors="coerce"
    ).notna().sum() > 0
    y = frame["label"].astype(int).to_numpy()
    n_splits = resolve_split_count(y, config.n_splits)
    folds = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=config.n_repeats, random_state=config.random_state)
    fold_rows: list[dict[str, Any]] = []
    coef_rows: list[dict[str, Any]] = []
    baseline_scores: dict[int, dict[str, float]] = {}

    for fold_idx, (train_idx, test_idx) in enumerate(folds.split(base, y)):
        params = fit_rdr_params(frame.iloc[train_idx])
        train_base = append_fold_scores(base.iloc[train_idx].reset_index(drop=True), frame.iloc[train_idx].reset_index(drop=True), params, path_lambda=config.path_lambda)
        test_base = append_fold_scores(base.iloc[test_idx].reset_index(drop=True), frame.iloc[test_idx].reset_index(drop=True), params, path_lambda=config.path_lambda)
        feature_sets = model_feature_sets(train_base, include_path=include_path)
        for model_name, columns in feature_sets.items():
            x_train = train_base[columns]
            x_test = test_base[columns]
            model = make_classifier(config.random_state)
            model.fit(x_train, y[train_idx])
            y_prob = model.predict_proba(x_test)[:, 1]
            metric_row = compute_metrics(y[test_idx], y_prob)
            if model_name == "clinical_plus_eeg":
                baseline_scores[fold_idx] = metric_row
            fold_rows.append(
                {
                    "evaluation": "repeated_stratified_cv",
                    "fold": int(fold_idx),
                    "model": model_name,
                    "n_train": int(len(train_idx)),
                    "n_test": int(len(test_idx)),
                    "n_features": int(len(columns)),
                    **metric_row,
                }
            )
            coefficients = model.named_steps["logreg"].coef_[0]
            for feature_name, coef in zip(columns, coefficients):
                coef_rows.append(
                    {
                        "evaluation": "repeated_stratified_cv",
                        "fold": int(fold_idx),
                        "model": model_name,
                        "feature": feature_name,
                        "coef": float(coef),
                        "abs_coef": float(abs(coef)),
                    }
                )
    fold_scores = pd.DataFrame(fold_rows)
    if "clinical_plus_eeg" in set(fold_scores["model"]):
        for metric in ("roc_auc", "average_precision", "brier_score"):
            fold_scores[f"delta_{metric}_vs_clinical_plus_eeg"] = fold_scores.apply(
                lambda row: float(row[metric] - baseline_scores[int(row["fold"])][metric])
                if row["model"] != "clinical_plus_eeg" and int(row["fold"]) in baseline_scores
                else 0.0
                if row["model"] == "clinical_plus_eeg"
                else np.nan,
                axis=1,
            )
    return fold_scores, pd.DataFrame(coef_rows)


def evaluate_leave_one_site_out(frame: pd.DataFrame, config: Config) -> pd.DataFrame:
    base = build_model_base(frame)
    include_path = "trajectory_3d_noetic_action" in frame.columns and pd.to_numeric(
        frame["trajectory_3d_noetic_action"], errors="coerce"
    ).notna().sum() > 0
    y = frame["label"].astype(int).to_numpy()
    groups = frame["hospital"].fillna("missing").astype(str).to_numpy()
    rows: list[dict[str, Any]] = []
    splitter = LeaveOneGroupOut()
    for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(base, y, groups)):
        if len(np.unique(y[train_idx])) < 2 or len(np.unique(y[test_idx])) < 2:
            continue
        params = fit_rdr_params(frame.iloc[train_idx])
        train_base = append_fold_scores(base.iloc[train_idx].reset_index(drop=True), frame.iloc[train_idx].reset_index(drop=True), params, path_lambda=config.path_lambda)
        test_base = append_fold_scores(base.iloc[test_idx].reset_index(drop=True), frame.iloc[test_idx].reset_index(drop=True), params, path_lambda=config.path_lambda)
        feature_sets = model_feature_sets(train_base, include_path=include_path)
        held_out_site = pd.Series(groups[test_idx]).mode().iloc[0]
        for model_name, columns in feature_sets.items():
            eval_columns = [column for column in columns if not column.startswith("cat__hospital_")]
            if not eval_columns:
                continue
            model = make_classifier(config.random_state)
            model.fit(train_base[eval_columns], y[train_idx])
            y_prob = model.predict_proba(test_base[eval_columns])[:, 1]
            rows.append(
                {
                    "evaluation": "leave_one_site_out",
                    "fold": int(fold_idx),
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
    rows: list[dict[str, Any]] = []
    for (evaluation, model), group in scores.groupby(["evaluation", "model"], sort=False):
        row: dict[str, Any] = {
            "evaluation": evaluation,
            "model": model,
            "n_folds": int(len(group)),
            "n_features_median": int(group["n_features"].median()),
        }
        for metric in ("roc_auc", "average_precision", "brier_score", "calibration_slope", "sensitivity", "specificity"):
            values = pd.to_numeric(group[metric], errors="coerce").dropna().to_numpy(dtype=float)
            row[f"{metric}_mean"] = float(np.mean(values)) if values.size else np.nan
            row[f"{metric}_sd"] = float(np.std(values, ddof=1)) if values.size > 1 else 0.0
            if f"delta_{metric}_vs_clinical_plus_eeg" in group.columns:
                deltas = pd.to_numeric(group[f"delta_{metric}_vs_clinical_plus_eeg"], errors="coerce").dropna().to_numpy(dtype=float)
                row[f"delta_{metric}_mean"] = float(np.mean(deltas)) if deltas.size else np.nan
                row[f"delta_{metric}_sd"] = float(np.std(deltas, ddof=1)) if deltas.size > 1 else 0.0
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


def evaluate_part1_fit_part2_test(frame: pd.DataFrame, config: Config) -> pd.DataFrame:
    part1 = frame[frame["source_cohort"] == "part1"].copy()
    part2 = frame[frame["source_cohort"] == "part2"].copy()
    if part1.empty or part2.empty:
        return pd.DataFrame()
    params = fit_rdr_params(part1)
    part1 = compute_rdr_scores(part1, params, prefix="p1test", path_lambda=config.path_lambda)
    part2 = compute_rdr_scores(part2, params, prefix="p1test", path_lambda=config.path_lambda)
    rows: list[dict[str, Any]] = []
    for metric in ("rdr_core_p1test", "rdr_3_p1test", "rdr_path_p1test", "nrca_p1test"):
        if metric not in part2.columns:
            continue
        train = part1[["label", metric]].dropna()
        test = part2[["label", metric]].dropna()
        if train["label"].nunique() < 2 or test["label"].nunique() < 2:
            continue
        direct = roc_auc_score(test["label"].astype(int), test[metric].astype(float))
        model = make_classifier(config.random_state)
        model.fit(train[[metric]], train["label"].astype(int))
        prob = model.predict_proba(test[[metric]])[:, 1]
        rows.append(
            {
                "metric": metric,
                "n_train": int(len(train)),
                "n_test": int(len(test)),
                "direct_auroc_cpc1_high": float(direct),
                "logistic_roc_auc": float(roc_auc_score(test["label"].astype(int), prob)),
                "logistic_average_precision": float(average_precision_score(test["label"].astype(int), prob)),
                "logistic_brier_score": float(brier_score_loss(test["label"].astype(int), prob)),
            }
        )
    return pd.DataFrame(rows)


def run_label_permutation(frame: pd.DataFrame, metrics: list[str], config: Config) -> pd.DataFrame:
    rng = np.random.default_rng(config.random_state)
    labels = frame["label"].astype(int).to_numpy()
    observed: dict[str, float] = {}
    values_by_metric: dict[str, np.ndarray] = {}
    for metric in metrics:
        values = pd.to_numeric(frame[metric], errors="coerce").to_numpy(dtype=float)
        values_by_metric[metric] = values
        observed[metric] = abs(cohens_d(values[labels == 1], values[labels == 0]))
    rows: list[dict[str, Any]] = []
    nulls: dict[str, list[float]] = {metric: [] for metric in metrics}
    max_nulls: list[float] = []
    for _ in range(config.n_permutations):
        shuffled = rng.permutation(labels)
        max_abs_d = 0.0
        for metric in metrics:
            values = values_by_metric[metric]
            perm_d = abs(cohens_d(values[shuffled == 1], values[shuffled == 0]))
            if np.isfinite(perm_d):
                max_abs_d = max(max_abs_d, float(perm_d))
            nulls[metric].append(float(perm_d))
        max_nulls.append(max_abs_d)
    for metric in metrics:
        arr = np.asarray(nulls[metric], dtype=float)
        rows.append(
            {
                "metric": metric,
                "observed_abs_cohens_d": float(observed[metric]),
                "null_mean_abs_cohens_d": float(np.nanmean(arr)),
                "null_p95_abs_cohens_d": float(np.nanquantile(arr, 0.95)),
                "empirical_p": float((1.0 + np.sum(arr >= observed[metric])) / (len(arr) + 1.0)),
            }
        )
    max_arr = np.asarray(max_nulls, dtype=float)
    observed_max = max(value for value in observed.values() if np.isfinite(value))
    rows.append(
        {
            "metric": "max_abs_cohens_d_across_rdr_metrics",
            "observed_abs_cohens_d": float(observed_max),
            "null_mean_abs_cohens_d": float(np.nanmean(max_arr)),
            "null_p95_abs_cohens_d": float(np.nanquantile(max_arr, 0.95)),
            "empirical_p": float((1.0 + np.sum(max_arr >= observed_max)) / (len(max_arr) + 1.0)),
        }
    )
    return pd.DataFrame(rows)


def qc_correlations(frame: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for metric in metrics:
        metric_values = pd.to_numeric(frame[metric], errors="coerce")
        for qc_col in QC_COLUMNS:
            if qc_col not in frame.columns:
                continue
            qc_values = pd.to_numeric(frame[qc_col], errors="coerce")
            mask = np.isfinite(metric_values) & np.isfinite(qc_values)
            if int(mask.sum()) < 3 or metric_values[mask].nunique() < 2 or qc_values[mask].nunique() < 2:
                rows.append({"metric": metric, "qc_variable": qc_col, "n": int(mask.sum()), "spearman_rho": np.nan, "spearman_p": np.nan})
                continue
            rho, p_value = stats.spearmanr(metric_values[mask], qc_values[mask])
            rows.append(
                {
                    "metric": metric,
                    "qc_variable": qc_col,
                    "n": int(mask.sum()),
                    "spearman_rho": float(rho),
                    "spearman_p": float(p_value),
                }
            )
    return pd.DataFrame(rows)


def subset_contrasts(frame: pd.DataFrame, metrics: dict[str, str]) -> pd.DataFrame:
    shockable = pd.to_numeric(frame.get("shockable_rhythm"), errors="coerce")
    rows = []
    subsets = {
        "shockable_only": shockable == 1.0,
        "nonshockable_only": shockable == 0.0,
    }
    for subset, mask in subsets.items():
        sub = frame[mask].copy()
        if sub.empty:
            continue
        out = summarize_contrasts(sub, metrics)
        if out.empty:
            continue
        out["subset"] = subset
        rows.append(out[out["cohort"] == "pooled"].copy())
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def write_summary(
    frame: pd.DataFrame,
    contrasts: pd.DataFrame,
    part2_test: pd.DataFrame,
    cv_summary: pd.DataFrame,
    loso_summary: pd.DataFrame,
    permutation: pd.DataFrame,
    qc: pd.DataFrame,
    subset: pd.DataFrame,
    config: Config,
) -> str:
    counts = frame.groupby(["source_cohort", "label_name"], dropna=False)["pooled_subject"].nunique().unstack(fill_value=0)
    pooled = contrasts[contrasts["cohort"] == "pooled"].copy()
    top = pooled[pooled["metric"].str.contains("nrca|rdr|score_tube_d_eff|score_mnj3d_spectral", regex=True)].head(12)
    lines = [
        "# Recovery Dynamical Reserve Composite",
        "",
        f"- primary time bin: `{config.primary_time_bin}`",
        f"- joined subjects: `{frame['pooled_subject'].nunique()}`",
        f"- path regularization lambda: `{config.path_lambda}`",
        "- score orientation: all score rows are oriented so higher values point toward CPC1.",
        "- train/test discipline: CV and LOSO recompute RDR robust z-scaling from the training fold only; part2-test rows use part1-fitted scaling.",
        "",
        "## Cohort Join",
        "",
        format_count_table(counts),
        "",
        "## Metric Formulae",
        "",
        "```text",
        "RDR_core = z(tube_d_eff_median) - z(tube_capture_gate_median)",
        "           - z(MNJ3D_spectral_radius_median) - z(MNJ3D_frobenius_norm_median)",
        "RDR_3    = z(tube_d_eff_median) - z(tube_capture_gate_median)",
        "           - mean(z(MNJ3D_spectral_radius_median), z(MNJ3D_frobenius_norm_median))",
        f"RDR_path = RDR_core - {config.path_lambda:g} * z(trajectory_3D_noetic_action)",
        "NRCA     = projection_to_recovery_ray / sqrt(1 + off_axis_distance^2)",
        "```",
        "",
        "`NRCA` uses the oriented four-vector `[z(d_eff), -z(capture), -z(spectral_radius), -z(frobenius)]`. The ideal recovery ray is `[1, 1, 1, 1] / 2`; off-axis distance penalizes subjects whose apparent advantage is carried by only one axis rather than by coherent reachability-with-low-deformation geometry.",
        "",
        "## Pooled Oriented Contrasts",
        "",
        "| Metric | n CPC1 | n CPC5 | CPC1 median | CPC5 median | d | Cliff delta | AUROC | p |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in top.iterrows():
        lines.append(
            f"| `{row['metric']}` | {int(row['n_cpc1'])} | {int(row['n_cpc5'])} | "
            f"{row['cpc1_median']:.4g} | {row['cpc5_median']:.4g} | {row['cohens_d']:+.3f} | "
            f"{row['cliffs_delta']:+.3f} | {row['direct_auroc_cpc1_high']:.3f} | {row['mannwhitney_p']:.3g} |"
        )
    if not part2_test.empty:
        lines.extend(["", "## Part1-Fit / Part2-Test", ""])
        for _, row in part2_test.iterrows():
            lines.append(
                f"- `{row['metric']}`: direct AUROC `{row['direct_auroc_cpc1_high']:.3f}`, "
                f"logistic AUROC `{row['logistic_roc_auc']:.3f}`, AUPRC `{row['logistic_average_precision']:.3f}`, "
                f"Brier `{row['logistic_brier_score']:.3f}` (n_test `{int(row['n_test'])}`)"
            )
    if not cv_summary.empty:
        lines.extend(["", "## Repeated Stratified CV", ""])
        for _, row in cv_summary[cv_summary["evaluation"] == "repeated_stratified_cv"].iterrows():
            delta = row.get("delta_roc_auc_mean", np.nan)
            lines.append(
                f"- `{row['model']}`: AUROC `{row['roc_auc_mean']:.3f} +/- {row['roc_auc_sd']:.3f}`, "
                f"AUPRC `{row['average_precision_mean']:.3f} +/- {row['average_precision_sd']:.3f}`, "
                f"Brier `{row['brier_score_mean']:.3f} +/- {row['brier_score_sd']:.3f}`, "
                f"delta AUROC vs clinical+EEG `{delta:+.3f}`"
            )
    if not loso_summary.empty:
        lines.extend(["", "## Leave-One-Site-Out", ""])
        for _, row in loso_summary.iterrows():
            lines.append(
                f"- `{row['model']}`: AUROC `{row['roc_auc_mean']:.3f} +/- {row['roc_auc_sd']:.3f}`, "
                f"AUPRC `{row['average_precision_mean']:.3f} +/- {row['average_precision_sd']:.3f}`, "
                f"Brier `{row['brier_score_mean']:.3f} +/- {row['brier_score_sd']:.3f}`"
            )
    if not permutation.empty:
        lines.extend(["", "## Label Permutation", ""])
        for _, row in permutation.iterrows():
            lines.append(
                f"- `{row['metric']}`: observed |d| `{row['observed_abs_cohens_d']:.3f}`, "
                f"null p95 `{row['null_p95_abs_cohens_d']:.3f}`, empirical p `{row['empirical_p']:.3g}`"
            )
    if not subset.empty:
        lines.extend(["", "## Shockable / Nonshockable Stress Test", ""])
        for _, row in subset[subset["metric"].str.contains("nrca_allfit|rdr_core_allfit|rdr_3_allfit|rdr_path_allfit", regex=True)].iterrows():
            lines.append(
                f"- `{row['subset']}` / `{row['metric']}`: d `{row['cohens_d']:+.3f}`, "
                f"AUROC `{row['direct_auroc_cpc1_high']:.3f}`, p `{row['mannwhitney_p']:.3g}`"
            )
    if not qc.empty:
        strongest = qc[np.isfinite(qc["spearman_rho"])].copy()
        if not strongest.empty:
            strongest["abs_rho"] = strongest["spearman_rho"].abs()
            strongest = strongest.sort_values("abs_rho", ascending=False).head(10)
            lines.extend(["", "## Strongest QC Associations", ""])
            for _, row in strongest.iterrows():
                lines.append(
                    f"- `{row['metric']}` vs `{row['qc_variable']}`: rho `{row['spearman_rho']:+.3f}`, "
                    f"p `{row['spearman_p']:.3g}`, n `{int(row['n'])}`"
                )
    lines.extend(
        [
            "",
            "## Claim Status",
            "",
            "`NRCA` is the new out-of-family geometric proposal: it asks whether a patient lies inside a coherent recovery cone rather than merely having a high linear sum. `RDR_core` remains an internally tested composite proposal, not a bedside biomarker. `RDR_path` remains exploratory because the trajectory layer is not yet a frozen confirmatory family and may mix path roughness with non-neural data quality effects.",
            "",
            "## Limitations And Article Placement",
            "",
            "- `NRCA` is post hoc and should be treated as a new exploratory geometry metric until frozen and externally or prospectively replicated.",
            "- `RDR_3` may remain the strongest pooled linear-family contrast in this run, but it is also a post hoc composite over a cohort already used to characterize the component effects.",
            "- The analysis inherits the manuscript-facing limitations: CPC5 is not a pure neural-viability endpoint, WLST/time-to-death are unavailable, and artifact burden is only represented by coarse coverage/run-count proxies.",
            "- The recommended placement is a short exploratory supplement or Discussion paragraph after the layered reachability/Jacobian result, framed as a compact recovery-linked geometry index. It should not replace the existing primary reachability family unless it is frozen and externally or prospectively replicated.",
            "",
        ]
    )
    return "\n".join(lines)


def format_count_table(counts: pd.DataFrame) -> str:
    columns = [str(column) for column in counts.columns]
    header = "| source_cohort | " + " | ".join(columns) + " |"
    separator = "|---|" + "|".join("---:" for _ in columns) + "|"
    rows = [header, separator]
    for index, row in counts.iterrows():
        values = [str(int(row[column])) for column in counts.columns]
        rows.append(f"| {index} | " + " | ".join(values) + " |")
    return "\n".join(rows)


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    frame = build_joined_feature_matrix(config)
    score_metrics = {
        **{key: label for key, (_, _, label) in ORIENTED_BASELINE_SPECS.items() if key in frame.columns},
        "rdr_core_allfit": "RDR-core descriptive all-fit",
        "rdr_3_allfit": "RDR-3 descriptive all-fit",
        "rdr_path_allfit": "RDR-path descriptive all-fit",
        "nrca_allfit": "Noetic Recovery Cone Alignment descriptive all-fit",
        "nrca_projection_allfit": "NRCA projection onto recovery ray",
        "nrca_off_axis_allfit": "NRCA off-axis distance from recovery ray",
        "nrca_cosine_allfit": "NRCA cosine alignment with recovery ray",
        "rdr_core_part1fit": "RDR-core part1-fit scaling",
        "rdr_3_part1fit": "RDR-3 part1-fit scaling",
        "rdr_path_part1fit": "RDR-path part1-fit scaling",
        "nrca_part1fit": "Noetic Recovery Cone Alignment part1-fit scaling",
        "nrca_projection_part1fit": "NRCA part1-fit projection onto recovery ray",
        "nrca_off_axis_part1fit": "NRCA part1-fit off-axis distance from recovery ray",
        "nrca_cosine_part1fit": "NRCA part1-fit cosine alignment with recovery ray",
    }
    score_metrics = {metric: label for metric, label in score_metrics.items() if metric in frame.columns}

    contrasts = summarize_contrasts(frame, score_metrics)
    subset = subset_contrasts(frame, score_metrics)
    part2_test = evaluate_part1_fit_part2_test(frame, config)
    cv_scores, coefficients = evaluate_repeated_cv(frame, config)
    cv_summary = summarize_scores(cv_scores)
    loso_scores = evaluate_leave_one_site_out(frame, config)
    loso_summary = summarize_scores(loso_scores)
    coefficient_summary = summarize_coefficients(coefficients)
    permutation_metrics = [
        metric
        for metric in ("nrca_allfit", "rdr_core_allfit", "rdr_3_allfit", "rdr_path_allfit")
        if metric in frame.columns
    ]
    permutation = run_label_permutation(frame, permutation_metrics, config)
    qc = qc_correlations(frame, permutation_metrics + [metric for metric in ORIENTED_BASELINE_SPECS if metric in frame.columns])

    frame.to_csv(config.output_dir / "rdr_joined_feature_matrix.csv", index=False)
    contrasts.to_csv(config.output_dir / "rdr_metric_contrasts.csv", index=False)
    subset.to_csv(config.output_dir / "rdr_subset_contrasts.csv", index=False)
    part2_test.to_csv(config.output_dir / "rdr_part1_fit_part2_test.csv", index=False)
    cv_scores.to_csv(config.output_dir / "rdr_repeated_cv_fold_scores.csv", index=False)
    cv_summary.to_csv(config.output_dir / "rdr_repeated_cv_summary.csv", index=False)
    loso_scores.to_csv(config.output_dir / "rdr_leave_one_site_out_scores.csv", index=False)
    loso_summary.to_csv(config.output_dir / "rdr_leave_one_site_out_summary.csv", index=False)
    coefficients.to_csv(config.output_dir / "rdr_model_coefficients.csv", index=False)
    coefficient_summary.to_csv(config.output_dir / "rdr_model_coefficient_summary.csv", index=False)
    permutation.to_csv(config.output_dir / "rdr_label_permutation_summary.csv", index=False)
    qc.to_csv(config.output_dir / "rdr_qc_correlations.csv", index=False)
    (config.output_dir / "rdr_composite_summary.md").write_text(
        write_summary(frame, contrasts, part2_test, cv_summary, loso_summary, permutation, qc, subset, config),
        encoding="utf-8",
    )
    (config.output_dir / "rdr_composite_manifest.json").write_text(
        json.dumps(
            {
                "timeline_dir": str(config.timeline_dir),
                "mnps_dir": str(config.mnps_dir),
                "trajectory_part1_dir": str(config.trajectory_part1_dir),
                "trajectory_part2_dir": str(config.trajectory_part2_dir),
                "output_dir": str(config.output_dir),
                "primary_time_bin": config.primary_time_bin,
                "good_cpc": config.good_cpc,
                "poor_cpc": config.poor_cpc,
                "n_subjects_joined": int(frame["pooled_subject"].nunique()),
                "n_splits": config.n_splits,
                "n_repeats": config.n_repeats,
                "random_state": config.random_state,
                "n_permutations": config.n_permutations,
                "path_lambda": config.path_lambda,
                "core_feature_specs": CORE_FEATURE_SPECS,
                "trajectory_feature_specs": TRAJECTORY_FEATURE_SPECS,
                "score_orientation": {
                    score: {"raw_feature": raw, "sign": sign, "note": note}
                    for score, (raw, sign, note) in ORIENTED_BASELINE_SPECS.items()
                },
            },
            indent=2,
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    print(f"Wrote RDR feature matrix to {config.output_dir / 'rdr_joined_feature_matrix.csv'}")
    print(f"Wrote RDR summary to {config.output_dir / 'rdr_composite_summary.md'}")


if __name__ == "__main__":
    main()
