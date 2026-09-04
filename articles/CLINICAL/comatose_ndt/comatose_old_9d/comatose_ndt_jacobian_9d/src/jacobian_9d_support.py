from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
COMA_DIR = ARTICLE_DIR.parent / "comatose_ndt"

FORMAL_CONTRAST_DIR = ARTICLE_DIR / "results" / "outcome_contrasts_9d_jacobian_20260525_cpc15_primary12h"
RESULT_LEDGER_DIR = ARTICLE_DIR / "results" / "result_ledger_20260525_cpc15_primary12h"
ROBUSTNESS_DIR = ARTICLE_DIR / "results" / "robustness_20260525_cpc15_primary12h"
PREDICTION_DIR = ARTICLE_DIR / "results" / "incremental_validity_20260525_cpc15_primary12h"
VIOLIN_DIR = ARTICLE_DIR / "results" / "violin_20260525_revised_9d"
HOURLY_DIR = ARTICLE_DIR / "results" / "hourly_20260525_best_available_metrics"
HOURLY_EXACT_DIR = ARTICLE_DIR / "results" / "hourly_20260525_exact_revised_9d"
FIGURE_DIR = ARTICLE_DIR / "figures" / "20260525_jacobian_9d"

PART1_9D_TIMELINE_DIR = COMA_DIR / "results" / "timeline_analysis_20260524_part1_primary12h_9d"
PART2_9D_TIMELINE_DIR = COMA_DIR / "results" / "timeline_analysis_20260523_part2_primary12h_9d"
PART1_9D_MNPS_DIR = COMA_DIR / "results" / "mnps_summary_20260524_part1_primary12h_9d_targeted"
PART2_9D_MNPS_DIR = COMA_DIR / "results" / "mnps_summary_20260523_part2_primary12h_9d"
PART1_HOURLY_9D_TIMELINE_DIR = COMA_DIR / "results" / "timeline_analysis_20260524_part1_hourly12h_9d"
PART2_HOURLY_9D_TIMELINE_DIR = COMA_DIR / "results" / "timeline_analysis_20260524_part2_hourly12h_9d"
PART1_HOURLY_9D_MNPS_DIR = COMA_DIR / "results" / "mnps_summary_20260525_part1_hourly12h_9d_cpc15"
PART2_HOURLY_9D_MNPS_DIR = COMA_DIR / "results" / "mnps_summary_20260525_part2_hourly12h_9d_cpc15"

# part1 keeps the reachability metrics from the locked manuscript-facing export.
PART1_REACHABILITY_MNPS_DIR = COMA_DIR / "results" / "mnps_summary_20260525_part1_primary12h_cpc15_prefiltered"
PART2_REACHABILITY_MNPS_DIR = PART2_9D_MNPS_DIR

PRIMARY_TIME_BIN = "0_12h"
HOURLY_BINS: tuple[str, ...] = tuple(f"{hour}_{hour + 1}h" for hour in range(12))
GOOD_CPC = 1
POOR_CPC = 5

REVISED_CORE_METRICS: tuple[str, ...] = (
    "spectral_radius_median",
    "anisotropy_abs_eig_median",
    "mdr_median",
    "rotational_power_mean",
    "rotational_power_median",
)
MAIN_ARTICLE_METRICS: tuple[str, ...] = REVISED_CORE_METRICS + ("frobenius_norm_median",)
LEGACY_SUPPORTIVE_METRICS: tuple[str, ...] = (
    "a_operator_norm_median",
    "frobenius_norm_median",
    "rotation_norm_median",
)
ALL_ARTICLE_METRICS: tuple[str, ...] = REVISED_CORE_METRICS + LEGACY_SUPPORTIVE_METRICS
REACHABILITY_FEATURES: tuple[str, ...] = (
    "tube_d_eff_median",
    "persistence_kappa_median",
    "persistence_log_eig_var_median",
    "tube_a_operator_norm_median",
    "tube_capture_gate_median",
)
JACOBIAN_3D_FEATURES: tuple[str, ...] = (
    "jacobian_spectral_radius_median",
    "jacobian_fro_median",
    "jacobian_condition_median",
)
COORDINATE_COMPARATORS: tuple[str, ...] = ("coords_9d_global_std_mean",)
HOURLY_BEST_AVAILABLE_METRICS: tuple[str, ...] = (
    "jacobian_fro_median",
    "jacobian_spectral_radius_median",
    "coords_9d_global_std_mean",
)

EEG_BASELINE_COLUMNS: tuple[str, ...] = (
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
)


def bh_fdr(p_values: pd.Series) -> pd.Series:
    values = pd.to_numeric(p_values, errors="coerce").to_numpy(dtype=float)
    out = np.full(values.shape, np.nan, dtype=float)
    mask = np.isfinite(values)
    if not mask.any():
        return pd.Series(out, index=p_values.index, dtype=float)
    valid = values[mask]
    order = np.argsort(valid)
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(valid) + 1)
    q = valid * len(valid) / ranks
    q_sorted = np.minimum.accumulate(q[order][::-1])[::-1]
    q_final = np.empty_like(q_sorted)
    q_final[order] = np.clip(q_sorted, 0.0, 1.0)
    out[np.where(mask)[0]] = q_final
    return pd.Series(out, index=p_values.index, dtype=float)


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


def winsorize(values: pd.Series | np.ndarray, *, lower_q: float = 0.01, upper_q: float = 0.99) -> np.ndarray:
    arr = pd.to_numeric(pd.Series(values), errors="coerce").dropna().to_numpy(dtype=float)
    if arr.size == 0:
        return arr
    low, high = np.quantile(arr, [lower_q, upper_q])
    return np.clip(arr, low, high)


def normalize_bool_series(series: pd.Series) -> pd.Series:
    mapping = {
        "true": 1.0,
        "false": 0.0,
        "1": 1.0,
        "0": 0.0,
        "yes": 1.0,
        "no": 0.0,
    }
    return series.astype(str).str.strip().str.lower().map(mapping).astype(float)


def _convert_numeric_columns(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    out = frame.copy()
    for column in columns:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce")
    return out


def load_timeline_cohort(timeline_dir: Path, *, cohort_tag: str) -> pd.DataFrame:
    frame = pd.read_csv(timeline_dir / "patient_timebin_summaries.csv", low_memory=False)
    frame = frame[frame["time_bin"] == PRIMARY_TIME_BIN].copy()
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([float(GOOD_CPC), float(POOR_CPC)])].copy()
    frame["label"] = np.where(frame["cpc_numeric"] == float(GOOD_CPC), 1, 0)
    frame["label_name"] = np.where(frame["label"] == 1, "CPC1", "CPC5")
    frame["cohort_tag"] = cohort_tag
    numeric_columns = (
        "age",
        "rosc_minutes",
        "ttm_celsius",
        "channel_count_median",
        "channel_coverage_frac_median",
        "n_windows_total",
        "artifact_burden_mean",
        *EEG_BASELINE_COLUMNS,
        *JACOBIAN_3D_FEATURES,
        *COORDINATE_COMPARATORS,
    )
    frame = _convert_numeric_columns(frame, numeric_columns)
    if "shockable_rhythm" in frame.columns:
        frame["shockable_rhythm"] = normalize_bool_series(frame["shockable_rhythm"])
    if "ohca" in frame.columns:
        frame["ohca"] = normalize_bool_series(frame["ohca"])
    return frame.reset_index(drop=True)


def load_timeline_bins(
    timeline_dir: Path,
    *,
    cohort_tag: str,
    time_bins: Iterable[str],
    extra_numeric_columns: Iterable[str] = (),
) -> pd.DataFrame:
    frame = pd.read_csv(timeline_dir / "patient_timebin_summaries.csv", low_memory=False)
    frame = frame[frame["time_bin"].isin(tuple(time_bins))].copy()
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([float(GOOD_CPC), float(POOR_CPC)])].copy()
    frame["label"] = np.where(frame["cpc_numeric"] == float(GOOD_CPC), 1, 0)
    frame["label_name"] = np.where(frame["label"] == 1, "CPC1", "CPC5")
    frame["cohort_tag"] = cohort_tag
    numeric_columns = (
        "age",
        "rosc_minutes",
        "ttm_celsius",
        "channel_count_median",
        "channel_coverage_frac_median",
        "n_windows_total",
        "artifact_burden_mean",
        *EEG_BASELINE_COLUMNS,
        *JACOBIAN_3D_FEATURES,
        *COORDINATE_COMPARATORS,
        *tuple(extra_numeric_columns),
    )
    frame = _convert_numeric_columns(frame, numeric_columns)
    if "shockable_rhythm" in frame.columns:
        frame["shockable_rhythm"] = normalize_bool_series(frame["shockable_rhythm"])
    if "ohca" in frame.columns:
        frame["ohca"] = normalize_bool_series(frame["ohca"])
    return frame.reset_index(drop=True)


def load_metric_long(input_dir: Path, *, analysis_type: str, metrics: Iterable[str]) -> pd.DataFrame:
    frame = pd.read_csv(input_dir / "patient_timebin_signal_metrics.csv", low_memory=False)
    frame = frame[
        (frame["analysis_type"] == analysis_type)
        & (frame["time_bin"] == PRIMARY_TIME_BIN)
        & (frame["metric"].isin(tuple(metrics)))
    ].copy()
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([float(GOOD_CPC), float(POOR_CPC)])].copy()
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[frame["value"].notna()].copy()
    return frame.reset_index(drop=True)


def load_metric_long_bins(
    input_dir: Path,
    *,
    analysis_type: str,
    metrics: Iterable[str],
    time_bins: Iterable[str],
) -> pd.DataFrame:
    frame = pd.read_csv(input_dir / "patient_timebin_signal_metrics.csv", low_memory=False)
    frame = frame[
        (frame["analysis_type"] == analysis_type)
        & (frame["time_bin"].isin(tuple(time_bins)))
        & (frame["metric"].isin(tuple(metrics)))
    ].copy()
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([float(GOOD_CPC), float(POOR_CPC)])].copy()
    frame["label"] = np.where(frame["cpc_numeric"] == float(GOOD_CPC), 1, 0)
    frame["label_name"] = np.where(frame["label"] == 1, "CPC1", "CPC5")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[frame["value"].notna()].copy()
    return frame.reset_index(drop=True)


def load_metric_matrix(input_dir: Path, *, analysis_type: str, metrics: Iterable[str]) -> pd.DataFrame:
    frame = load_metric_long(input_dir, analysis_type=analysis_type, metrics=metrics)
    if frame.empty:
        return pd.DataFrame(columns=["subject"])
    matrix = frame.pivot_table(index="subject", columns="metric", values="value", aggfunc="first").reset_index()
    matrix.columns.name = None
    return matrix


def _part_paths(part: str) -> tuple[Path, Path, Path]:
    if part == "part1":
        return PART1_9D_TIMELINE_DIR, PART1_9D_MNPS_DIR, PART1_REACHABILITY_MNPS_DIR
    if part == "part2":
        return PART2_9D_TIMELINE_DIR, PART2_9D_MNPS_DIR, PART2_REACHABILITY_MNPS_DIR
    raise ValueError(f"Unsupported cohort part: {part}")


def assemble_part_cohort(*, part: str, include_reachability: bool = False) -> pd.DataFrame:
    timeline_dir, jacobian_dir, reachability_dir = _part_paths(part)
    timeline = load_timeline_cohort(timeline_dir, cohort_tag=part)
    jacobian = load_metric_matrix(jacobian_dir, analysis_type="global_mnps_jacobian_9d", metrics=ALL_ARTICLE_METRICS)
    out = timeline.merge(jacobian, on="subject", how="left")
    if include_reachability:
        reachability = load_metric_matrix(
            reachability_dir,
            analysis_type="reachability_cones",
            metrics=REACHABILITY_FEATURES,
        )
        out = out.merge(reachability, on="subject", how="left")
    return out


def assemble_pooled_cohort(*, include_reachability: bool = False) -> pd.DataFrame:
    part1 = assemble_part_cohort(part="part1", include_reachability=include_reachability)
    part2 = assemble_part_cohort(part="part2", include_reachability=include_reachability)
    overlap = set(part1["subject"].astype(str)) & set(part2["subject"].astype(str))
    if overlap:
        sample = sorted(overlap)[:10]
        raise ValueError(f"Unexpected subject overlap in pooled 9D cohort: {sample}")
    return pd.concat([part1, part2], ignore_index=True)
