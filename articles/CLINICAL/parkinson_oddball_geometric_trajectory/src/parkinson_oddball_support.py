from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, Sequence

import numpy as np


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
AUDITORY_SRC = REPO_ROOT / "articles" / "CLINICAL" / "parkinson_auditory_recall" / "src"
if str(AUDITORY_SRC) not in sys.path:
    sys.path.insert(0, str(AUDITORY_SRC))

import parkinson_auditory_support as base  # noqa: E402


RESULT_STAMP = "20260602"
PRIMARY_COORDINATE_CONTRACT = base.PRIMARY_COORDINATE_CONTRACT
DATASET_ID = base.DATASET_ID
DATASET_ROOT = base.DATASET_ROOT
RESULTS_DIR = ARTICLE_DIR / "results" / f"parkinson_oddball_geometric_trajectory_{RESULT_STAMP}"
STANDARD_CLEANED_DIR = RESULTS_DIR / "standard_cleaned"
STANDARD_ANALYSIS_DIR = RESULTS_DIR / "standard_analysis"
EVENT_METRIC_DIR = RESULTS_DIR / "event_metrics"
SUMMARY_PATH = RESULTS_DIR / "analysis_summary.md"
ARTICLE_METRIC_RANKING_CSV = "article_metric_ranking.csv"
ARTICLE_METRIC_SUMMARY_MD = "article_metric_summary.md"
MANIFEST_JSON = base.MANIFEST_JSON
RUN_METRICS_CSV = base.RUN_METRICS_CSV
SUBJECT_METRICS_CSV = base.SUBJECT_METRICS_CSV
EVENT_CONTRASTS_CSV = base.EVENT_CONTRASTS_CSV
WRAPPER_SUMMARY_MD = base.WRAPPER_SUMMARY_MD
RUN_CONFIG_PATH = base.RUN_CONFIG_PATH
ANALYZE_CONFIG_PATH = base.ANALYZE_CONFIG_PATH
NDT_ANALYSIS_ROOT = base.NDT_ANALYSIS_ROOT

SpaceKey = base.SpaceKey
SegmentSpec = base.SegmentSpec
LoadedRun = base.LoadedRun

GROUP_MAP = base.GROUP_MAP
DIMENSIONS = base.DIMENSIONS
REPERTOIRE_STATES_BY_DIM = base.REPERTOIRE_STATES_BY_DIM
MAX_POINTS_PER_SEGMENT_FOR_FIT = base.MAX_POINTS_PER_SEGMENT_FOR_FIT
MAX_POINTS_PER_KEY_FOR_FIT = base.MAX_POINTS_PER_KEY_FOR_FIT
MIN_SEGMENT_POINTS = base.MIN_SEGMENT_POINTS
MIN_REPERTOIRE_POINTS = base.MIN_REPERTOIRE_POINTS
PRE_EVENT_WINDOWS = base.PRE_EVENT_WINDOWS
POST_EVENT_WINDOWS = base.POST_EVENT_WINDOWS
EPS = base.EPS
PHASE_ORDER = base.PHASE_ORDER
SUBTYPE_ORDER = base.SUBTYPE_ORDER
STRATIFIED_NAMES = base.STRATIFIED_NAMES
EXACT_PHASE_SEGMENTS = base.EXACT_PHASE_SEGMENTS
SUBTYPE_SEGMENTS = base.SUBTYPE_SEGMENTS
PHASE_SEGMENTS = base.PHASE_SEGMENTS
SEGMENT_SPEC_BY_LABEL = base.SEGMENT_SPEC_BY_LABEL

COUPLING_LAGS: tuple[int, ...] = (1, 2)
RETURN_PROBABILITY_LAGS: tuple[int, ...] = (2, 3)
DIRECTED_FAMILY_PAIRS: tuple[tuple[str, str], ...] = (
    ("m", "d"),
    ("d", "m"),
    ("m", "e"),
    ("e", "m"),
    ("d", "e"),
    ("e", "d"),
)
ASYMMETRY_FAMILY_PAIRS: tuple[tuple[str, str], ...] = (
    ("m", "d"),
    ("m", "e"),
    ("d", "e"),
)

COUPLING_METRIC_COLUMNS = [
    f"coupling_{src}{dst}_tau{lag}"
    for lag in COUPLING_LAGS
    for src, dst in DIRECTED_FAMILY_PAIRS
]
ASYMMETRY_METRIC_COLUMNS = [
    f"asymmetry_{src}{dst}_tau{lag}"
    for lag in COUPLING_LAGS
    for src, dst in ASYMMETRY_FAMILY_PAIRS
]
RETURN_PROBABILITY_COLUMNS = [f"return_probability_tau{lag}" for lag in RETURN_PROBABILITY_LAGS]
EXTRA_NUMERIC_METRIC_COLUMNS = [
    "torsion_median",
    "path_hysteresis",
    *RETURN_PROBABILITY_COLUMNS,
    *COUPLING_METRIC_COLUMNS,
    *ASYMMETRY_METRIC_COLUMNS,
]
NUMERIC_METRIC_COLUMNS = [*base.NUMERIC_METRIC_COLUMNS, *EXTRA_NUMERIC_METRIC_COLUMNS]

ensure_dir = base.ensure_dir
write_json = base.write_json
decode_text = base.decode_text
read_json_dataset = base.read_json_dataset
parse_run_slug = base.parse_run_slug
contiguous_runs = base.contiguous_runs
merge_blocks = base.merge_blocks
robust_median = base.robust_median
family_projection = base.family_projection
path_length = base.path_length
tortuosity = base.tortuosity
step_speed = base.step_speed
curvature_series = base.curvature_series
hysteresis_plane_area = base.hysteresis_plane_area
stable_variance_metric = base.stable_variance_metric
weighted_quad = base.weighted_quad
potential_from_coords = base.potential_from_coords
noetic_action_metrics = base.noetic_action_metrics
repertoire_metrics = base.repertoire_metrics
sample_evenly = base.sample_evenly
build_reference_model = base.build_reference_model
bh_fdr = base.bh_fdr
cohens_d = base.cohens_d
cohens_dz = base.cohens_dz
winsorize_array = base.winsorize_array
load_run = base.load_run


def _default_extra_metrics() -> dict[str, float]:
    defaults = {name: float("nan") for name in EXTRA_NUMERIC_METRIC_COLUMNS}
    return defaults


def _family_series(coords: np.ndarray) -> dict[str, np.ndarray]:
    projected = family_projection(coords)
    return {
        "m": np.asarray(projected[:, 0], dtype=float),
        "d": np.asarray(projected[:, 1], dtype=float),
        "e": np.asarray(projected[:, 2], dtype=float),
    }


def _lagged_corr(delta_source: np.ndarray, target: np.ndarray, lag: int) -> float:
    delta_source = np.asarray(delta_source, dtype=float).reshape(-1)
    target = np.asarray(target, dtype=float).reshape(-1)
    if lag < 0 or target.size < 4 or delta_source.size != target.size - 1:
        return float("nan")
    if lag >= target.size - 2:
        return float("nan")
    idx = np.arange(lag, target.size - 1, dtype=int)
    left = delta_source[idx]
    right = target[idx - lag]
    valid = np.isfinite(left) & np.isfinite(right)
    if valid.sum() < 4:
        return float("nan")
    left = left[valid]
    right = right[valid]
    if np.nanstd(left) <= EPS or np.nanstd(right) <= EPS:
        return float("nan")
    return float(np.corrcoef(left, right)[0, 1])


def family_temporal_coupling_metrics(coords: np.ndarray) -> dict[str, float]:
    metrics = {name: float("nan") for name in [*COUPLING_METRIC_COLUMNS, *ASYMMETRY_METRIC_COLUMNS]}
    series = _family_series(coords)
    delta = {name: np.diff(values) for name, values in series.items()}
    for lag in COUPLING_LAGS:
        for src, dst in DIRECTED_FAMILY_PAIRS:
            metrics[f"coupling_{src}{dst}_tau{lag}"] = _lagged_corr(delta[src], series[dst], lag)
        for src, dst in ASYMMETRY_FAMILY_PAIRS:
            forward = metrics.get(f"coupling_{src}{dst}_tau{lag}", float("nan"))
            reverse = metrics.get(f"coupling_{dst}{src}_tau{lag}", float("nan"))
            metrics[f"asymmetry_{src}{dst}_tau{lag}"] = (
                float(forward - reverse) if np.isfinite(forward) and np.isfinite(reverse) else float("nan")
            )
    return metrics


def return_probability_metrics(states: np.ndarray) -> dict[str, float]:
    states = np.asarray(states, dtype=int).reshape(-1)
    out = {name: float("nan") for name in RETURN_PROBABILITY_COLUMNS}
    for lag in RETURN_PROBABILITY_LAGS:
        if states.size <= lag:
            continue
        out[f"return_probability_tau{lag}"] = float(np.mean(states[:-lag] == states[lag:]))
    return out


def _normalize_path_parameter(path: np.ndarray) -> np.ndarray:
    if path.shape[0] <= 1:
        return np.zeros((path.shape[0],), dtype=float)
    step = np.linalg.norm(np.diff(path, axis=0), axis=1)
    arc = np.r_[0.0, np.cumsum(step)]
    total = float(arc[-1])
    if not np.isfinite(total) or total <= EPS:
        return np.linspace(0.0, 1.0, num=path.shape[0], dtype=float)
    return arc / total


def _resample_path(path: np.ndarray, *, n_points: int = 32) -> np.ndarray:
    arr = np.asarray(path, dtype=float)
    if arr.ndim != 2 or arr.shape[0] < 2:
        return np.full((0, arr.shape[1] if arr.ndim == 2 else 0), np.nan, dtype=float)
    parameter = _normalize_path_parameter(arr)
    grid = np.linspace(0.0, 1.0, num=n_points, dtype=float)
    return np.column_stack([np.interp(grid, parameter, arr[:, dim]) for dim in range(arr.shape[1])])


def path_hysteresis_metric(forward: np.ndarray, recovery: np.ndarray) -> float:
    forward = np.asarray(forward, dtype=float)
    recovery = np.asarray(recovery, dtype=float)
    if forward.ndim != 2 or recovery.ndim != 2 or forward.shape[0] < 2 or recovery.shape[0] < 2:
        return float("nan")
    up = _resample_path(forward, n_points=32)
    down = _resample_path(recovery[::-1], n_points=32)
    if up.size == 0 or down.size == 0 or up.shape != down.shape:
        return float("nan")
    return float(np.nanmean(np.linalg.norm(up - down, axis=1)))


def torsion_series(coords: np.ndarray, time: np.ndarray) -> np.ndarray:
    projected = family_projection(coords)
    time = np.asarray(time, dtype=float).reshape(-1)
    if projected.shape[0] < 4 or time.size < 4:
        return np.zeros((0,), dtype=float)
    valid_time = np.isfinite(time)
    if valid_time.sum() < 4:
        return np.zeros((0,), dtype=float)
    v = np.gradient(projected, time, axis=0)
    a = np.gradient(v, time, axis=0)
    j = np.gradient(a, time, axis=0)
    values: list[float] = []
    for idx in range(1, projected.shape[0] - 1):
        if not (np.isfinite(v[idx]).all() and np.isfinite(a[idx]).all() and np.isfinite(j[idx]).all()):
            continue
        cross = np.cross(v[idx], a[idx])
        denom = float(np.dot(cross, cross))
        if not np.isfinite(denom) or denom <= EPS:
            continue
        numer = float(np.linalg.det(np.stack([v[idx], a[idx], j[idx]], axis=0)))
        if np.isfinite(numer):
            values.append(numer / denom)
    return np.asarray(values, dtype=float)


def summarize_segment_metrics(
    coords: np.ndarray,
    time: np.ndarray,
    *,
    metric_diag: np.ndarray | None = None,
    model: Any | None = None,
    n_states: int | None = None,
    event_block: np.ndarray | None = None,
) -> dict[str, float]:
    out = {**base.summarize_segment_metrics(
        coords,
        time,
        metric_diag=metric_diag,
        model=model,
        n_states=n_states,
        event_block=event_block,
    ), **_default_extra_metrics()}
    coords = np.asarray(coords, dtype=float)
    time = np.asarray(time, dtype=float)
    if coords.shape[0] < MIN_SEGMENT_POINTS:
        return out

    out["torsion_median"] = robust_median(torsion_series(coords, time))
    out.update(family_temporal_coupling_metrics(coords))

    if model is not None and n_states is not None and coords.shape[0] >= MIN_REPERTOIRE_POINTS:
        try:
            states = model.predict(coords)
        except Exception:
            states = np.zeros((0,), dtype=int)
        if len(states):
            out.update(return_probability_metrics(states))

    if event_block is None or np.asarray(event_block).size == 0:
        return out

    projected = family_projection(coords)
    local_event_end = int(np.asarray(event_block, dtype=int).reshape(-1)[-1])
    forward = projected[: local_event_end + 1]
    recovery = projected[local_event_end:]
    out["path_hysteresis"] = path_hysteresis_metric(forward, recovery)
    return out


def aggregate_metric_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    base_row: dict[str, Any] = {}
    for key, value in rows[0].items():
        if key not in NUMERIC_METRIC_COLUMNS and key not in {"segment_points", "event_windows", "segment_duration_sec"}:
            base_row[key] = value
    base_row["n_blocks"] = int(len(rows))
    for key in NUMERIC_METRIC_COLUMNS:
        values = np.asarray([row.get(key, float("nan")) for row in rows], dtype=float)
        base_row[key] = robust_median(values)
    for key in ("segment_points", "event_windows", "segment_duration_sec"):
        values = np.asarray([row.get(key, float("nan")) for row in rows], dtype=float)
        base_row[f"{key}_median"] = robust_median(values)
    return base_row
