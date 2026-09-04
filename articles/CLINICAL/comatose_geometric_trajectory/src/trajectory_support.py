from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
COMA_DIR = ARTICLE_DIR.parent / "comatose_ndt"
JACOBIAN_9D_DIR = ARTICLE_DIR.parent / "comatose_ndt_jacobian_9d"

RESULT_STAMP = "20260606"
PRIMARY_TIME_BIN = "0_12h"
PRIMARY_COORDINATE_CONTRACT = "subject_anchored"
GOOD_CPC = 1
POOR_CPC = 5

RAW_WFDB_ROOT = Path("E:/Science_Datasets/physionet/received/i-care_2_1_random100_longitudinal/training")

# Part1 roots: newest first so first_existing_path picks the most recent available.
PART1_ROOT_CANDIDATES: tuple[Path, ...] = (
    Path("J:/repos/NoeticDiffusion/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260605_202236"),
    Path("E:/Science_Datasets/physionet/processed/physionet_icare_2_1/neuralmanifolddynamics_physionet_icare_2_1_20260527_151403"),
    Path("E:/Science_Datasets/physionet/processed/physionet_icare_2_1/neuralmanifolddynamics_physionet_icare_2_1_20260525_141608"),
    Path("E:/Science_Datasets/physionet/processed/physionet_icare_2_1/neuralmanifolddynamics_physionet_icare_2_1_20260523_173059"),
)
PART2_ROOT_CANDIDATES: tuple[Path, ...] = (
    Path("J:/repos/NoeticDiffusion/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260605_210700"),
    Path(
        "E:/Science_Datasets/physionet/processed_next140_0_12h_no_regional_rerun_20260522_clean/physionet_icare_2_1/"
        "neuralmanifolddynamics_physionet_icare_2_1_20260522_144827_part2_140sub_9d"
    ),
)

COMA_NDT_RESULTS = ARTICLE_DIR.parent / "comatose_ndt" / "results"

TIMELINE_PART1_DIR = COMA_NDT_RESULTS / "timeline_analysis_20260606_part1_invalidityfix_primary12h"
TIMELINE_PART2_DIR = COMA_NDT_RESULTS / "timeline_analysis_20260606_part2_invalidityfix_primary12h"
SMOKE_DIR = ARTICLE_DIR / "results" / f"trajectory_smoke_{RESULT_STAMP}"
PART1_METRIC_DIR = ARTICLE_DIR / "results" / f"trajectory_metrics_{RESULT_STAMP}_part1_primary12h"
PART2_METRIC_DIR = ARTICLE_DIR / "results" / f"trajectory_metrics_{RESULT_STAMP}_part2_primary12h"
CONTRAST_DIR = ARTICLE_DIR / "results" / f"outcome_contrasts_trajectory_{RESULT_STAMP}_cpc15_primary12h"
RESULT_LEDGER_DIR = ARTICLE_DIR / "results" / f"metric_result_ledger_{RESULT_STAMP}"
FIGURE_DIR = ARTICLE_DIR / "figures" / f"{RESULT_STAMP}_geometric_trajectory"

RUN_LEVEL_METRICS_CSV = "run_level_trajectory_metrics.csv"
PATIENT_TIMEBIN_METRICS_CSV = "patient_timebin_trajectory_metrics.csv"
MANIFEST_JSON = "trajectory_metric_manifest.json"

DIMENSIONS: tuple[int, ...] = (3, 9)
ANALYSIS_TYPE_3D = "trajectory_geometry_subject_anchored_3d"
ANALYSIS_TYPE_9D = "trajectory_geometry_subject_anchored_9d"
ANALYSIS_TYPE_BY_DIM = {3: ANALYSIS_TYPE_3D, 9: ANALYSIS_TYPE_9D}

ARTICLE_FACING_METRICS: tuple[str, ...] = (
    "irreversibility",
    "entropy_rate",
    "noetic_action",
)
SUPPORTIVE_METRICS: tuple[str, ...] = (
    "entropy_production",
    "self_loop_rate",
    "transition_sparsity",
    "noetic_action_kinetic",
    "noetic_action_jerk",
    "noetic_action_potential",
)
ALL_METRICS: tuple[str, ...] = ARTICLE_FACING_METRICS + SUPPORTIVE_METRICS

REPERTOIRE_STATES_BY_DIM = {
    3: 12,
    9: 24,
}
MAX_CODEBOOK_POINTS_BY_DIM = {
    3: 40000,
    9: 60000,
}
MAX_POINTS_PER_RUN_FOR_FIT_BY_DIM = {
    3: 256,
    9: 256,
}
MIN_POINTS_PER_RUN = 16
MIN_TRANSITIONS_PER_RUN = 8
MIN_VALID_RUNS_PER_SUBJECT = 1

ACTION_JERK_WEIGHT = 1.0
ACTION_POTENTIAL_WEIGHT = 1.0
EPS = 1e-12
RNG_SEED = 20260601


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def first_existing_path(candidates: Iterable[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def resolve_part_root(part: str) -> Path:
    if part == "part1":
        resolved = first_existing_path(PART1_ROOT_CANDIDATES)
    elif part == "part2":
        resolved = first_existing_path(PART2_ROOT_CANDIDATES)
    else:
        raise ValueError(f"Unsupported part={part!r}. Expected 'part1' or 'part2'.")
    if resolved is None:
        raise FileNotFoundError(f"Could not resolve a processed root for {part}.")
    return resolved


def resolve_timeline_dir(part: str) -> Path:
    if part == "part1":
        return TIMELINE_PART1_DIR
    if part == "part2":
        return TIMELINE_PART2_DIR
    raise ValueError(f"Unsupported part={part!r}. Expected 'part1' or 'part2'.")


def resolve_metric_dir(part: str) -> Path:
    if part == "part1":
        return PART1_METRIC_DIR
    if part == "part2":
        return PART2_METRIC_DIR
    raise ValueError(f"Unsupported part={part!r}. Expected 'part1' or 'part2'.")


def write_json(path: Path, payload: dict) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


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


def stable_variance_metric(sampled_coords: np.ndarray) -> np.ndarray:
    coords = np.asarray(sampled_coords, dtype=float)
    if coords.ndim != 2 or coords.shape[1] == 0:
        raise ValueError("sampled_coords must be a non-empty 2D array.")
    var = np.nanvar(coords, axis=0, ddof=1)
    var = np.where(np.isfinite(var) & (var > EPS), var, 1.0)
    return 1.0 / var


def potential_from_coords(coords: np.ndarray) -> np.ndarray:
    arr = np.asarray(coords, dtype=float)
    if arr.ndim != 2:
        raise ValueError("coords must be a 2D array.")
    if arr.shape[1] == 3:
        m = arr[:, 0]
        d = arr[:, 1]
        e = arr[:, 2]
        return e - m + d
    if arr.shape[1] >= 9:
        m_bar = np.nanmean(arr[:, 0:3], axis=1)
        d_bar = np.nanmean(arr[:, 3:6], axis=1)
        e_bar = np.nanmean(arr[:, 6:9], axis=1)
        return e_bar - m_bar + d_bar
    raise ValueError(f"Unsupported coordinate width {arr.shape[1]} for potential calculation.")
