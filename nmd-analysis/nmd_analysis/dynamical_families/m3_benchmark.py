"""Bounded synthetic M3 benchmark for chart-conditional velocity recovery.

This module is analysis-side experiment code.  It deliberately does not add
an estimator to ingest and it never presents a benchmark result as an M3
qualification.  The simulated target is the conditional *discrete-chart*
velocity

    b_dt(x) = (A - I) x / dt,

for a stable linear-Gaussian transition ``x[i + 1] = A @ x[i] + eps[i]``.
That target is useful for checking the existing ``crossfit_local_chart_b``
candidate, but it is not an Ito drift.  The observed evaluation increment
covariance is calculated once per scenario at fixed evaluation-only local
neighbourhoods and its hash is shared by every comparator when the ingest
``A_bD`` operational quantity is evaluated.

The unsafe same-sample and shuffled controls are implemented locally and are
kept separate from the production cross-fit API.  The time-displaced control
uses the production API with a deliberately displaced evaluation order while
remaining temporally disjoint from training.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import platform
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from .drift import DriftContractError, crossfit_local_chart_b


BENCHMARK_SCHEMA_VERSION = "nmd_analysis.m3_benchmark.v1"
SPEC_VERSION = "df_drift_c1_m3_synthetic.v1"

# These numbers are the prospective primary specification.  Keep them in a
# single immutable mapping so the CLI and the Python API cannot drift apart.
DEFAULT_A = np.asarray(
    [
        [0.72, 0.12, -0.05],
        [0.03, 0.61, 0.14],
        [-0.02, 0.05, 0.55],
    ],
    dtype=float,
)
DEFAULT_Q = np.asarray(
    [
        [0.09, 0.015, 0.000],
        [0.015, 0.16, 0.010],
        [0.000, 0.010, 0.04],
    ],
    dtype=float,
)
DEFAULT_BASE_DT = 0.05
DEFAULT_SEEDS = (17, 29, 43)
DEFAULT_DT_VALUES = (0.05, 0.10, 0.20)
DEFAULT_EMBARGO_MULTIPLES = (0.0, 1.0, 2.0)
DEFAULT_N_SAMPLES = 1200
DEFAULT_BURN_IN = 200
DEFAULT_TRAIN_FRACTION = 0.45
DEFAULT_N_NEIGHBORS = 24
DEFAULT_MIN_TRAIN_SUPPORT = 8
DEFAULT_TIME_SHIFT_STEPS = 7
DEFAULT_A_B_D_EPSILON = 1e-12


def _plain(value: Any) -> Any:
    """Convert numpy values to JSON-safe Python values, retaining nulls."""

    if isinstance(value, np.ndarray):
        return [_plain(item) for item in value.tolist()]
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_array(value: np.ndarray) -> str:
    array = np.ascontiguousarray(np.asarray(value))
    return _sha256_bytes(array.tobytes())


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(_plain(value), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(encoded)


def _module_hash(module_file: Path) -> str | None:
    try:
        return _sha256_bytes(module_file.read_bytes())
    except OSError:
        return None


def _effective_transition(
    base_A: np.ndarray, base_Q: np.ndarray, stride: int
) -> tuple[np.ndarray, np.ndarray]:
    """Return the exact ``stride``-step transition of the base chain."""

    if isinstance(stride, (bool, np.bool_)) or int(stride) != stride or int(stride) < 1:
        raise ValueError("stride must be a positive integer")
    stride = int(stride)
    effective_A = np.linalg.matrix_power(np.asarray(base_A, dtype=float), stride)
    effective_Q = np.zeros_like(np.asarray(base_Q, dtype=float))
    power = np.eye(effective_A.shape[0], dtype=float)
    for _ in range(stride):
        effective_Q += power @ base_Q @ power.T
        power = power @ base_A
    effective_Q = 0.5 * (effective_Q + effective_Q.T)
    return effective_A, effective_Q


def _frozen_spec(
    *,
    A: np.ndarray | None = None,
    Q: np.ndarray | None = None,
    base_dt: float = DEFAULT_BASE_DT,
    seeds: Sequence[int] = DEFAULT_SEEDS,
    dt_values: Sequence[float] = DEFAULT_DT_VALUES,
    embargo_multiples: Sequence[float] = DEFAULT_EMBARGO_MULTIPLES,
    n_samples: int = DEFAULT_N_SAMPLES,
    burn_in: int = DEFAULT_BURN_IN,
    train_fraction: float = DEFAULT_TRAIN_FRACTION,
    n_neighbors: int = DEFAULT_N_NEIGHBORS,
    min_train_support: int = DEFAULT_MIN_TRAIN_SUPPORT,
    time_shift_steps: int = DEFAULT_TIME_SHIFT_STEPS,
) -> dict[str, Any]:
    """Return the exact numeric specification used by one benchmark call."""

    base_A = np.asarray(A if A is not None else DEFAULT_A, dtype=float)
    base_Q = np.asarray(Q if Q is not None else DEFAULT_Q, dtype=float)
    dt_checked = tuple(float(value) for value in dt_values)
    strides = tuple(int(round(value / float(base_dt))) for value in dt_checked)
    effective = []
    for dt, stride in zip(dt_checked, strides):
        effective_A, effective_Q = _effective_transition(base_A, base_Q, stride)
        effective.append(
            {
                "dt_sec": float(dt),
                "stride": int(stride),
                "A_k": effective_A.tolist(),
                "Q_k": effective_Q.tolist(),
            }
        )
    return {
        "spec_version": SPEC_VERSION,
        "state_dimension": 3,
        "base_dt_sec": float(base_dt),
        "base_A": base_A.tolist(),
        "base_Q": base_Q.tolist(),
        "dt_sampling_mode": "same_seed_base_path_subsampled",
        "effective_transitions": effective,
        "seeds": [int(seed) for seed in seeds],
        "dt_values_sec": [float(dt) for dt in dt_values],
        "embargo_multiples_of_dt": [float(value) for value in embargo_multiples],
        "n_samples": int(n_samples),
        "burn_in": int(burn_in),
        "train_fraction": float(train_fraction),
        "n_neighbors": int(n_neighbors),
        "min_train_support": int(min_train_support),
        "time_shift_steps": int(time_shift_steps),
        "a_b_d_epsilon": DEFAULT_A_B_D_EPSILON,
        "split": "chronological_train_then_gap_then_evaluation",
        "time_support": "raw_increment_endpoints_[t_i,t_{i+1}]",
    }


DEFAULT_SPEC = _frozen_spec()
DEFAULT_SPEC_SHA256 = _sha256_json(DEFAULT_SPEC)


def _as_int_sequence(value: Sequence[int], name: str) -> tuple[int, ...]:
    result: list[int] = []
    for item in value:
        if isinstance(item, (bool, np.bool_)) or not isinstance(item, (int, np.integer)):
            raise ValueError(f"{name} must contain integers")
        result.append(int(item))
    if not result:
        raise ValueError(f"{name} must not be empty")
    return tuple(result)


def _as_float_sequence(value: Sequence[float], name: str, *, nonnegative: bool = False) -> tuple[float, ...]:
    result: list[float] = []
    for item in value:
        number = float(item)
        if not np.isfinite(number) or (number < 0 if nonnegative else number <= 0):
            relation = "non-negative" if nonnegative else "positive"
            raise ValueError(f"{name} must contain finite {relation} values")
        result.append(number)
    if not result:
        raise ValueError(f"{name} must not be empty")
    return tuple(result)


def _validate_matrices(A: np.ndarray, Q: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    matrix_a = np.asarray(A, dtype=float)
    matrix_q = np.asarray(Q, dtype=float)
    if matrix_a.shape != (3, 3) or not np.isfinite(matrix_a).all():
        raise ValueError("A must be a finite 3x3 matrix")
    if matrix_q.shape != (3, 3) or not np.isfinite(matrix_q).all():
        raise ValueError("Q must be a finite 3x3 matrix")
    if not np.allclose(matrix_q, matrix_q.T, rtol=0.0, atol=1e-14):
        raise ValueError("Q must be symmetric")
    eigenvalues = np.linalg.eigvalsh(matrix_q)
    if float(np.min(eigenvalues)) <= 0.0:
        raise ValueError("Q must be positive definite")
    spectral_radius = float(np.max(np.abs(np.linalg.eigvals(matrix_a))))
    if not np.isfinite(spectral_radius) or spectral_radius >= 1.0:
        raise ValueError("A must be stable in discrete time (spectral radius < 1)")
    return matrix_a.copy(), matrix_q.copy()


def _simulation_seed(seed: int) -> np.random.SeedSequence:
    return np.random.SeedSequence([int(seed), 2_026_090_6])


def _simulate_base_path(
    *, seed: int, A: np.ndarray, Q: np.ndarray, n_base_steps: int
) -> np.ndarray:
    """Simulate one base-dt chain which all effective-dt scenarios subsample."""

    rng = np.random.default_rng(_simulation_seed(seed))
    innovations = rng.multivariate_normal(np.zeros(3), Q, size=int(n_base_steps) - 1)
    state = np.zeros((int(n_base_steps), 3), dtype=float)
    for index in range(int(n_base_steps) - 1):
        state[index + 1] = A @ state[index] + innovations[index]
    return state


def _subsample_base_path(
    base_path: np.ndarray, *, burn_in: int, stride: int, n_samples: int, base_dt: float
) -> tuple[np.ndarray, np.ndarray]:
    start = int(burn_in)
    stop = start + (int(n_samples) - 1) * int(stride)
    trajectory = np.asarray(base_path[start : stop + 1 : int(stride)], dtype=float)
    if trajectory.shape[0] != int(n_samples):
        raise AssertionError("base path is too short for requested subsampling")
    time = np.arange(int(n_samples), dtype=float) * float(stride) * float(base_dt)
    return trajectory, time


def _split_indices(
    *, n_samples: int, dt: float, embargo: float, train_fraction: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
    """Build a chronological split with raw endpoint supports and a strict gap."""

    n_increments = int(n_samples) - 1
    gap_steps = int(np.ceil(float(embargo) / float(dt))) + 1
    usable = n_increments - gap_steps
    n_train = int(np.floor(usable * float(train_fraction)))
    n_eval = usable - n_train
    if n_train < 1 or n_eval < 1:
        raise ValueError("split leaves insufficient train or evaluation increments")
    train = np.arange(0, n_train, dtype=np.int64)
    evaluation = np.arange(n_train + gap_steps, n_increments, dtype=np.int64)
    if evaluation.size != n_eval:
        raise AssertionError("internal split count mismatch")
    return train, evaluation, gap_steps, np.intersect1d(train, evaluation), np.int64(n_train)


def _raw_support(time: np.ndarray, indices: np.ndarray) -> np.ndarray:
    return np.column_stack((time[indices], time[indices + 1])).astype(float, copy=False)


def _fixed_local_neighborhoods(
    trajectory: np.ndarray, evaluation: np.ndarray, n_neighbors: int
) -> tuple[np.ndarray, ...]:
    """Choose deterministic eval-centre neighbours once per scenario."""

    states = np.asarray(trajectory, dtype=float)[np.asarray(evaluation, dtype=np.int64)]
    used = min(int(n_neighbors), int(states.shape[0]))
    if used < 1:
        return tuple()
    result: list[np.ndarray] = []
    for row, query in enumerate(states):
        distances = np.linalg.norm(states - query, axis=1)
        if not np.isfinite(distances).all():
            raise DriftContractError("non-finite evaluation neighbourhood distance")
        result.append(np.argsort(distances, kind="mergesort")[:used].astype(np.int64))
    return tuple(result)


def _local_increment_covariance(
    increment: np.ndarray,
    evaluation: np.ndarray,
    neighborhoods: Sequence[np.ndarray],
    dt: float,
) -> np.ndarray:
    """Mirror ingest local raw-increment covariance semantics per centre."""

    increments = np.asarray(increment, dtype=float)
    evaluation = np.asarray(evaluation, dtype=np.int64)
    tensors: list[np.ndarray] = []
    for neighborhood in neighborhoods:
        local_indices = evaluation[np.asarray(neighborhood, dtype=np.int64)]
        local = increments[local_indices]
        if local.shape[0] < 2 or not np.isfinite(local).all():
            tensors.append(np.full((increments.shape[1], increments.shape[1]), np.nan))
            continue
        tensor = np.atleast_2d(np.cov(local, rowvar=False, ddof=1)) / float(dt)
        tensor = 0.5 * (tensor + tensor.T)
        tensors.append(np.asarray(tensor, dtype=float))
    return np.asarray(tensors, dtype=float)


def _support_summary(support: np.ndarray) -> dict[str, Any]:
    values = np.asarray(support, dtype=float)
    return {
        "kind": "raw_increment_endpoints",
        "n_intervals": int(values.shape[0]),
        "first_interval": values[0].tolist(),
        "last_interval": values[-1].tolist(),
        "sha256": _sha256_array(values.astype(np.float64)),
    }


def _nearest_predict(
    train_states: np.ndarray,
    train_velocity: np.ndarray,
    query_states: np.ndarray,
    *,
    estimator: str,
    n_neighbors: int,
    min_train_support: int,
) -> np.ndarray:
    """Benchmark-only predictor used for controls that cannot call production API."""

    if estimator not in {"local_mean", "local_linear"}:
        raise DriftContractError(f"unsupported benchmark estimator {estimator!r}")
    if train_states.shape[0] < min_train_support:
        raise DriftContractError("insufficient training support")
    used = min(int(n_neighbors), int(train_states.shape[0]))
    if used < min_train_support:
        raise DriftContractError("insufficient local training support")
    result = np.full((query_states.shape[0], train_velocity.shape[1]), np.nan, dtype=float)
    for row, query in enumerate(query_states):
        distances = np.linalg.norm(train_states - query, axis=1)
        nearest = np.argsort(distances, kind="mergesort")[:used]
        if estimator == "local_mean":
            result[row] = np.mean(train_velocity[nearest], axis=0)
            continue
        offsets = train_states[nearest] - query
        design = np.column_stack((np.ones(nearest.size), offsets))
        if design.shape[0] < train_states.shape[1] + 1:
            raise DriftContractError("local_linear estimator has insufficient local rank")
        if np.linalg.matrix_rank(design) < train_states.shape[1] + 1:
            raise DriftContractError("local_linear estimator has insufficient local rank")
        coefficients, *_ = np.linalg.lstsq(design, train_velocity[nearest], rcond=None)
        result[row] = coefficients[0]
    return result


def _same_sample_local_mean(
    trajectory: np.ndarray,
    time: np.ndarray,
    evaluation: np.ndarray,
    *,
    n_neighbors: int,
    min_train_support: int,
) -> np.ndarray:
    """Intentionally contaminated same-sample local mean control.

    This is not routed through ``crossfit_local_chart_b`` because that API
    correctly refuses train/evaluation overlap.  It exists only to quantify
    the optimistic bias caused by using evaluation increments in the fit.
    """

    dt = np.diff(time)
    states = trajectory[evaluation]
    velocities = (trajectory[evaluation + 1] - states) / dt[evaluation, None]
    return _nearest_predict(
        states,
        velocities,
        states,
        estimator="local_mean",
        n_neighbors=n_neighbors,
        min_train_support=min_train_support,
    )


def _shuffled_train_velocity(
    trajectory: np.ndarray,
    time: np.ndarray,
    train: np.ndarray,
    evaluation: np.ndarray,
    *,
    estimator: str,
    n_neighbors: int,
    min_train_support: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Benchmark-only negative control with training velocities permuted."""

    dt = np.diff(time)
    train_states = trajectory[train]
    velocities = (trajectory[train + 1] - train_states) / dt[train, None]
    shuffled = velocities[rng.permutation(velocities.shape[0])]
    return _nearest_predict(
        train_states,
        shuffled,
        trajectory[evaluation],
        estimator=estimator,
        n_neighbors=n_neighbors,
        min_train_support=min_train_support,
    )


def _rankdata(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float).reshape(-1)
    order = np.argsort(values, kind="mergesort")
    sorted_values = values[order]
    ranks = np.empty(values.size, dtype=float)
    start = 0
    while start < values.size:
        end = start + 1
        while end < values.size and sorted_values[end] == sorted_values[start]:
            end += 1
        ranks[order[start:end]] = 0.5 * (start + end - 1) + 1.0
        start = end
    return ranks


def _spearman(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=float).reshape(-1)
    right = np.asarray(right, dtype=float).reshape(-1)
    if left.size < 2 or right.size != left.size:
        return float("nan")
    if not np.isfinite(left).all() or not np.isfinite(right).all():
        return float("nan")
    left_rank = _rankdata(left)
    right_rank = _rankdata(right)
    left_centered = left_rank - np.mean(left_rank)
    right_centered = right_rank - np.mean(right_rank)
    denominator = float(np.linalg.norm(left_centered) * np.linalg.norm(right_centered))
    if denominator <= 0.0:
        return float("nan")
    return float(np.dot(left_centered, right_centered) / denominator)


def _a_b_d(values: np.ndarray, covariance: np.ndarray, epsilon: float) -> np.ndarray:
    """Apply the exact ingest operational definition to each velocity row.

    ``covariance`` is one fixed local observed tensor per evaluation centre.
    This mirrors ingest's ``np.cov(raw_neighbor_increments)/dt`` followed by
    ``_metrics(tensor, mean(drift_neighbor_values), ...)``.
    """

    b = np.asarray(values, dtype=float)
    a = np.asarray(covariance, dtype=float)
    if a.ndim == 2:
        a = np.broadcast_to(a, (b.shape[0],) + a.shape)
    if a.ndim != 3 or a.shape != (b.shape[0], b.shape[1], b.shape[1]):
        raise ValueError("covariance must have shape (n_rows, dimension, dimension)")
    trace = np.trace(a, axis1=1, axis2=2)
    norm_sq = np.einsum("ij,ij->i", b, b)
    numerator = np.einsum("ni,nij,nj->n", b, a, b)
    denominator = norm_sq * trace + float(epsilon)
    result = np.full(norm_sq.shape, np.nan, dtype=float)
    valid = np.isfinite(b).all(axis=1) & np.isfinite(denominator) & (norm_sq > 0.0)
    result[valid] = numerator[valid] / denominator[valid]
    return result


def _metrics(
    predicted: np.ndarray,
    truth: np.ndarray,
    covariance: np.ndarray,
    alignment_neighborhoods: Sequence[np.ndarray],
) -> dict[str, Any]:
    pred = np.asarray(predicted, dtype=float)
    target = np.asarray(truth, dtype=float)
    finite = np.isfinite(pred).all(axis=1) & np.isfinite(target).all(axis=1)
    n_valid = int(np.sum(finite))
    n_total = int(target.shape[0])
    result: dict[str, Any] = {
        "n_eval": n_total,
        "n_valid": n_valid,
        "support_fraction": n_valid / n_total if n_total else None,
        "rmse": None,
        "normalized_rmse": None,
        "bias_vector": None,
        "bias_norm": None,
        "a_b_d_mean": None,
        "a_b_d_median": None,
        "a_b_d_true_mean": None,
        "a_b_d_bias": None,
        "rank_correlation": None,
        "a_b_d_rank_correlation": None,
        "rank_correlation_components": None,
        "prediction_component_variance": None,
        "prediction_variance_mean": None,
        "error_component_variance": None,
        "alignment_n_valid": 0,
        "alignment_support_fraction": None,
    }
    if n_valid == 0:
        return result
    estimate = pred[finite]
    target_valid = target[finite]
    error = estimate - target_valid
    bias = np.mean(error, axis=0)
    # The ingest implementation evaluates local covariance at a centre and
    # uses the mean drift over that same local neighbourhood.  Keep those
    # neighbourhoods fixed for every comparator so A_bD differs only because
    # the candidate velocity differs.
    valid_indices = np.flatnonzero(finite)
    aligned_pred: list[np.ndarray] = []
    aligned_truth: list[np.ndarray] = []
    aligned_covariance: list[np.ndarray] = []
    for original in valid_indices:
        neighborhood = np.asarray(alignment_neighborhoods[int(original)], dtype=np.int64)
        if neighborhood.size == 0 or not np.isfinite(pred[neighborhood]).all() or not np.isfinite(target[neighborhood]).all():
            continue
        aligned_pred.append(np.mean(pred[neighborhood], axis=0))
        aligned_truth.append(np.mean(target[neighborhood], axis=0))
        aligned_covariance.append(np.asarray(covariance[int(original)], dtype=float))
    aligned_pred_array = np.asarray(aligned_pred, dtype=float)
    aligned_truth_array = np.asarray(aligned_truth, dtype=float)
    aligned_covariance_array = np.asarray(aligned_covariance, dtype=float)
    alignment_n_valid = int(aligned_pred_array.shape[0])
    result["alignment_n_valid"] = alignment_n_valid
    result["alignment_support_fraction"] = alignment_n_valid / n_total if n_total else None
    if alignment_n_valid:
        pred_a = _a_b_d(aligned_pred_array, aligned_covariance_array, DEFAULT_A_B_D_EPSILON)
        true_a = _a_b_d(aligned_truth_array, aligned_covariance_array, DEFAULT_A_B_D_EPSILON)
    else:
        pred_a = np.asarray([], dtype=float)
        true_a = np.asarray([], dtype=float)
    a_pair = np.isfinite(pred_a) & np.isfinite(true_a)
    pred_speed = np.linalg.norm(estimate, axis=1)
    target_speed = np.linalg.norm(target_valid, axis=1)
    result.update(
        {
            "rmse": float(np.sqrt(np.mean(error**2))),
            "bias_vector": bias.tolist(),
            "bias_norm": float(np.linalg.norm(bias)),
            "a_b_d_mean": float(np.mean(pred_a)) if np.isfinite(pred_a).any() else None,
            "a_b_d_median": float(np.median(pred_a[np.isfinite(pred_a)])) if np.isfinite(pred_a).any() else None,
            "a_b_d_true_mean": float(np.mean(true_a)) if np.isfinite(true_a).any() else None,
            "a_b_d_bias": float(np.mean(pred_a[a_pair] - true_a[a_pair])) if np.any(a_pair) else None,
            "rank_correlation": _spearman(pred_speed, target_speed),
            "a_b_d_rank_correlation": _spearman(pred_a[a_pair], true_a[a_pair]) if np.any(a_pair) else None,
            "rank_correlation_components": _spearman(estimate.reshape(-1), target_valid.reshape(-1)),
            "prediction_component_variance": np.var(estimate, axis=0, ddof=1).tolist() if n_valid > 1 else [None] * estimate.shape[1],
            "prediction_variance_mean": float(np.mean(np.var(estimate, axis=0, ddof=1))) if n_valid > 1 else None,
            "error_component_variance": np.var(error, axis=0, ddof=1).tolist() if n_valid > 1 else [None] * error.shape[1],
        }
    )
    target_scale = float(np.sqrt(np.mean(target_valid**2)))
    result["normalized_rmse"] = result["rmse"] / target_scale if target_scale > 0.0 else None
    return _plain(result)


def _refused_metrics(*, n_eval: int, reason: str) -> dict[str, Any]:
    metrics = _metrics(
        np.full((0, 3), np.nan),
        np.empty((0, 3)),
        np.empty((0, 3, 3)),
        [],
    )
    metrics["n_eval"] = int(n_eval)
    metrics["n_valid"] = 0
    metrics["support_fraction"] = 0.0 if n_eval else None
    metrics["refusal_reason"] = str(reason)
    return metrics


def _result_row(
    *,
    seed: int,
    dt: float,
    embargo: float,
    embargo_multiple: float,
    gap_steps: int,
    train: np.ndarray,
    evaluation: np.ndarray,
    overlap: np.ndarray,
    train_support: np.ndarray,
    evaluation_support: np.ndarray,
    covariance: np.ndarray,
    alignment_neighborhoods: Sequence[np.ndarray],
    q_over_dt: np.ndarray,
    comparator: str,
    estimator: str,
    predicted: np.ndarray | None,
    truth: np.ndarray,
    production_api: bool,
    candidate_status: str,
    refusal_reason: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "seed": int(seed),
        "dt_sec": float(dt),
        "embargo_sec": float(embargo),
        "embargo_multiple_of_dt": float(embargo_multiple),
        "gap_steps": int(gap_steps),
        "train_increment_count": int(train.size),
        "evaluation_increment_count": int(evaluation.size),
        "train_evaluation_overlap": overlap.tolist(),
        "train_evaluation_overlap_count": int(overlap.size),
        "embargo_violations": 0,
        "train_time_support": _support_summary(train_support),
        "evaluation_time_support": _support_summary(evaluation_support),
        "eval_increment_covariance_semantics": "observed_raw_local_neighbor_increment_covariance_divided_by_dt",
        "eval_increment_covariance_shape": list(covariance.shape),
        "eval_increment_covariance_sha256": _sha256_array(covariance.astype(np.float64)),
        "eval_increment_covariance_trace_mean": float(np.mean(np.trace(covariance, axis1=1, axis2=2))),
        "oracle_conditional_covariance_semantics": "Q_divided_by_dt",
        "oracle_conditional_Q_over_dt_sha256": _sha256_array(q_over_dt.astype(np.float64)),
        "comparator": comparator,
        "estimator": estimator,
        "production_crossfit_api": bool(production_api),
        "candidate_status": candidate_status,
        "claim_status": "no_biological_claim",
        "refused": refusal_reason is not None,
        "refusal_reason": refusal_reason,
        "metrics": _refused_metrics(n_eval=evaluation.size, reason=refusal_reason) if predicted is None else _metrics(predicted, truth, covariance, alignment_neighborhoods),
    }
    if extra:
        row.update(dict(extra))
    return _plain(row)


def _aggregate(rows: Iterable[Mapping[str, Any]], keys: Sequence[str]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[Mapping[str, Any]]] = {}
    for row in rows:
        key = tuple(row.get(name) for name in keys)
        groups.setdefault(key, []).append(row)
    metric_names = (
        "rmse",
        "normalized_rmse",
        "bias_norm",
        "a_b_d_mean",
        "a_b_d_bias",
        "rank_correlation",
        "a_b_d_rank_correlation",
        "prediction_variance_mean",
    )
    output: list[dict[str, Any]] = []
    for key, members in sorted(groups.items(), key=lambda item: tuple(str(part) for part in item[0])):
        summary: dict[str, Any] = {name: value for name, value in zip(keys, key)}
        valid_members = [member for member in members if not member.get("refused")]
        summary.update(
            {
                "n_runs": len(members),
                "n_refused": sum(1 for member in members if member.get("refused")),
                "refusal_rate": sum(1 for member in members if member.get("refused")) / len(members) if members else None,
            }
        )
        for metric in metric_names:
            values = [member.get("metrics", {}).get(metric) for member in valid_members]
            numeric = np.asarray([value for value in values if value is not None], dtype=float)
            summary[f"{metric}_mean"] = float(np.mean(numeric)) if numeric.size else None
            summary[f"{metric}_sd"] = float(np.std(numeric, ddof=1)) if numeric.size > 1 else None
        output.append(_plain(summary))
    return output


def _control_rng(seed: int, dt: float, embargo_multiple: float, label: str) -> np.random.Generator:
    token = int(_sha256_json([int(seed), float(dt), float(embargo_multiple), label])[:8], 16)
    return np.random.default_rng(np.random.SeedSequence([token, 2_026_090_6]))


def run_m3_benchmark(
    seeds: Sequence[int] = DEFAULT_SEEDS,
    dt_values: Sequence[float] = DEFAULT_DT_VALUES,
    embargo_multiples: Sequence[float] = DEFAULT_EMBARGO_MULTIPLES,
    *,
    base_dt: float = DEFAULT_BASE_DT,
    n_samples: int = DEFAULT_N_SAMPLES,
    burn_in: int = DEFAULT_BURN_IN,
    train_fraction: float = DEFAULT_TRAIN_FRACTION,
    n_neighbors: int = DEFAULT_N_NEIGHBORS,
    min_train_support: int = DEFAULT_MIN_TRAIN_SUPPORT,
    time_shift_steps: int = DEFAULT_TIME_SHIFT_STEPS,
    A: np.ndarray | None = None,
    Q: np.ndarray | None = None,
) -> dict[str, Any]:
    """Run the bounded truth-known M3 benchmark and return JSON-safe results.

    The default numeric specification is frozen in ``DEFAULT_SPEC``.  Custom
    arguments are intended for small algebra/contract smoke checks and are
    labelled ``custom_test_spec`` in the returned provenance.  No result is
    assigned a scientific pass/fail cutoff.
    """

    seed_values = _as_int_sequence(seeds, "seeds")
    dt_values_checked = _as_float_sequence(dt_values, "dt_values")
    embargo_values = _as_float_sequence(embargo_multiples, "embargo_multiples", nonnegative=True)
    base_dt = float(base_dt)
    if not np.isfinite(base_dt) or base_dt <= 0.0:
        raise ValueError("base_dt must be finite and positive")
    dt_strides: list[int] = []
    for dt in dt_values_checked:
        stride = int(round(float(dt) / base_dt))
        if stride < 1 or not np.isclose(float(stride) * base_dt, float(dt), rtol=0.0, atol=1e-12):
            raise ValueError("each dt must be an integer multiple of base_dt")
        dt_strides.append(stride)
    if isinstance(n_samples, (bool, np.bool_)) or int(n_samples) != n_samples or int(n_samples) < 20:
        raise ValueError("n_samples must be an integer >= 20")
    if isinstance(burn_in, (bool, np.bool_)) or int(burn_in) != burn_in or int(burn_in) < 0:
        raise ValueError("burn_in must be a non-negative integer")
    if not np.isfinite(train_fraction) or not (0.0 < float(train_fraction) < 1.0):
        raise ValueError("train_fraction must lie strictly between 0 and 1")
    if isinstance(n_neighbors, (bool, np.bool_)) or int(n_neighbors) != n_neighbors or int(n_neighbors) < 1:
        raise ValueError("n_neighbors must be a positive integer")
    if isinstance(min_train_support, (bool, np.bool_)) or int(min_train_support) != min_train_support or int(min_train_support) < 1:
        raise ValueError("min_train_support must be a positive integer")
    if isinstance(time_shift_steps, (bool, np.bool_)) or not isinstance(time_shift_steps, (int, np.integer)):
        raise ValueError("time_shift_steps must be a positive integer")
    time_shift_steps = int(time_shift_steps)
    if time_shift_steps < 1:
        raise ValueError("time_shift_steps must be a positive integer")
    for dt in dt_values_checked:
        for embargo_multiple in embargo_values:
            _, evaluation, _, _, _ = _split_indices(
                n_samples=int(n_samples),
                dt=dt,
                embargo=float(embargo_multiple) * float(dt),
                train_fraction=float(train_fraction),
            )
            if time_shift_steps >= evaluation.size:
                raise ValueError(
                    "time_shift_steps must be strictly smaller than every evaluation support size"
                )
    matrix_a, matrix_q = _validate_matrices(
        np.asarray(A if A is not None else DEFAULT_A, dtype=float),
        np.asarray(Q if Q is not None else DEFAULT_Q, dtype=float),
    )
    actual_spec = _frozen_spec(
        A=matrix_a,
        Q=matrix_q,
        base_dt=base_dt,
        seeds=seed_values,
        dt_values=dt_values_checked,
        embargo_multiples=embargo_values,
        n_samples=int(n_samples),
        burn_in=int(burn_in),
        train_fraction=float(train_fraction),
        n_neighbors=int(n_neighbors),
        min_train_support=int(min_train_support),
        time_shift_steps=int(time_shift_steps),
    )
    is_default_spec = actual_spec == DEFAULT_SPEC
    source_artifact_hash = _sha256_json({"A": matrix_a.tolist(), "Q": matrix_q.tolist(), "spec": actual_spec})
    drift_file = Path(inspect.getsourcefile(crossfit_local_chart_b) or "")
    rows: list[dict[str, Any]] = []
    scenario_covariance_hashes: dict[str, str] = {}
    total_scenarios = 0

    for seed in seed_values:
        total_base_steps = int(burn_in) + (int(n_samples) - 1) * max(dt_strides) + 1
        base_path = _simulate_base_path(
            seed=seed, A=matrix_a, Q=matrix_q, n_base_steps=total_base_steps
        )
        for dt, stride in zip(dt_values_checked, dt_strides):
            effective_A, effective_Q = _effective_transition(matrix_a, matrix_q, stride)
            trajectory, time = _subsample_base_path(
                base_path,
                burn_in=int(burn_in),
                stride=stride,
                n_samples=int(n_samples),
                base_dt=base_dt,
            )
            increment = trajectory[1:] - trajectory[:-1]
            for embargo_multiple in embargo_values:
                embargo = float(embargo_multiple) * float(dt)
                train, evaluation, gap_steps, overlap, _ = _split_indices(
                    n_samples=int(n_samples),
                    dt=dt,
                    embargo=embargo,
                    train_fraction=float(train_fraction),
                )
                train_support = _raw_support(time, train)
                evaluation_support = _raw_support(time, evaluation)
                alignment_neighborhoods = _fixed_local_neighborhoods(
                    trajectory, evaluation, int(n_neighbors)
                )
                covariance = _local_increment_covariance(
                    increment, evaluation, alignment_neighborhoods, float(dt)
                )
                q_over_dt = effective_Q / float(dt)
                true_b = ((effective_A - np.eye(3)) @ trajectory[evaluation].T).T / float(dt)
                scenario_key = f"seed={seed}|dt={dt:.12g}|embargo_multiple={embargo_multiple:.12g}"
                covariance_hash = _sha256_array(covariance.astype(np.float64))
                scenario_covariance_hashes[scenario_key] = covariance_hash
                total_scenarios += 1

                rows.append(
                    _result_row(
                        seed=seed,
                        dt=dt,
                        embargo=embargo,
                        embargo_multiple=embargo_multiple,
                        gap_steps=gap_steps,
                        train=train,
                        evaluation=evaluation,
                        overlap=overlap,
                        train_support=train_support,
                        evaluation_support=evaluation_support,
                        covariance=covariance,
                        alignment_neighborhoods=alignment_neighborhoods,
                        q_over_dt=q_over_dt,
                        comparator="oracle_truth_known",
                        estimator="analytic_discrete_chart_conditional_velocity",
                        predicted=true_b,
                        truth=true_b,
                        production_api=False,
                        candidate_status="truth_known_positive_control",
                    )
                )

                try:
                    contaminated = _same_sample_local_mean(
                        trajectory,
                        time,
                        evaluation,
                        n_neighbors=int(n_neighbors),
                        min_train_support=int(min_train_support),
                    )
                    contaminated_reason = None
                except (DriftContractError, ValueError, np.linalg.LinAlgError) as exc:
                    contaminated = None
                    contaminated_reason = str(exc)
                rows.append(
                    _result_row(
                        seed=seed,
                        dt=dt,
                        embargo=embargo,
                        embargo_multiple=embargo_multiple,
                        gap_steps=gap_steps,
                        train=train,
                        evaluation=evaluation,
                        overlap=overlap,
                        train_support=train_support,
                        evaluation_support=evaluation_support,
                        covariance=covariance,
                        alignment_neighborhoods=alignment_neighborhoods,
                        q_over_dt=q_over_dt,
                        comparator="contaminated_same_sample_local_mean",
                        estimator="local_mean",
                        predicted=contaminated,
                        truth=true_b,
                        production_api=False,
                        candidate_status="benchmark_only_contaminated_control",
                        refusal_reason=contaminated_reason,
                        extra={
                            "provenance_scope": "nominal_scenario_split_fields_plus_effective_contaminated_fit_fields",
                            "same_sample_overlap_count": int(evaluation.size),
                            "effective_fit_train_increment_count": int(evaluation.size),
                            "effective_fit_train_increment_indices_hash": _sha256_array(evaluation),
                            "effective_fit_train_evaluation_overlap_count": int(evaluation.size),
                            "effective_fit_time_support": _support_summary(evaluation_support),
                            "effective_fit_embargo_status": "not_applicable_contaminated_same_sample",
                        },
                    )
                )

                for estimator in ("local_mean", "local_linear"):
                    try:
                        crossfit = crossfit_local_chart_b(
                            trajectory,
                            time,
                            train,
                            evaluation,
                            estimator=estimator,
                            n_neighbors=int(n_neighbors),
                            min_train_support=int(min_train_support),
                            embargo=embargo,
                            train_window_support=train_support,
                            evaluation_window_support=evaluation_support,
                            source_artifact_hash=source_artifact_hash,
                            source_nmd_schema="synthetic.discrete_linear_gaussian.v1",
                            nmd_code_revision=_module_hash(drift_file) if drift_file else None,
                        )
                        crossfit_values = crossfit.b_hat
                        crossfit_reason = None
                        crossfit_status = str(crossfit.provenance.get("candidate_status", "candidate_not_qualified"))
                    except (DriftContractError, ValueError, np.linalg.LinAlgError) as exc:
                        crossfit_values = None
                        crossfit_reason = str(exc)
                        crossfit_status = "candidate_not_qualified"
                    rows.append(
                        _result_row(
                            seed=seed,
                            dt=dt,
                            embargo=embargo,
                            embargo_multiple=embargo_multiple,
                            gap_steps=gap_steps,
                            train=train,
                            evaluation=evaluation,
                            overlap=overlap,
                            train_support=train_support,
                            evaluation_support=evaluation_support,
                            covariance=covariance,
                            alignment_neighborhoods=alignment_neighborhoods,
                            q_over_dt=q_over_dt,
                            comparator=f"crossfit_{estimator}",
                            estimator=estimator,
                            predicted=crossfit_values,
                            truth=true_b,
                            production_api=True,
                            candidate_status=crossfit_status,
                            refusal_reason=crossfit_reason,
                        )
                    )

                    shuffled_rng = _control_rng(seed, dt, embargo_multiple, f"shuffled:{estimator}")
                    try:
                        shuffled = _shuffled_train_velocity(
                            trajectory,
                            time,
                            train,
                            evaluation,
                            estimator=estimator,
                            n_neighbors=int(n_neighbors),
                            min_train_support=int(min_train_support),
                            rng=shuffled_rng,
                        )
                        shuffled_reason = None
                    except (DriftContractError, ValueError, np.linalg.LinAlgError) as exc:
                        shuffled = None
                        shuffled_reason = str(exc)
                    rows.append(
                        _result_row(
                            seed=seed,
                            dt=dt,
                            embargo=embargo,
                            embargo_multiple=embargo_multiple,
                            gap_steps=gap_steps,
                            train=train,
                            evaluation=evaluation,
                            overlap=overlap,
                            train_support=train_support,
                            evaluation_support=evaluation_support,
                            covariance=covariance,
                            alignment_neighborhoods=alignment_neighborhoods,
                            q_over_dt=q_over_dt,
                            comparator=f"negative_shuffled_train_velocity_{estimator}",
                            estimator=estimator,
                            predicted=shuffled,
                            truth=true_b,
                            production_api=False,
                            candidate_status="benchmark_only_negative_control",
                            refusal_reason=shuffled_reason,
                            extra={"shuffled_train_velocity": True},
                        )
                    )

                    shifted_evaluation = np.roll(evaluation, int(time_shift_steps))
                    shifted_support = np.roll(evaluation_support, int(time_shift_steps), axis=0)
                    try:
                        displaced = crossfit_local_chart_b(
                            trajectory,
                            time,
                            train,
                            shifted_evaluation,
                            estimator=estimator,
                            n_neighbors=int(n_neighbors),
                            min_train_support=int(min_train_support),
                            embargo=embargo,
                            train_window_support=train_support,
                            evaluation_window_support=shifted_support,
                            source_artifact_hash=source_artifact_hash,
                            source_nmd_schema="synthetic.discrete_linear_gaussian.v1",
                            nmd_code_revision=_module_hash(drift_file) if drift_file else None,
                        )
                        # Keep the production rows in shifted source order:
                        # scoring row j therefore receives b(x[source[j]])
                        # while truth remains at the original scoring centre.
                        # This is the intentionally index-corrupted surrogate.
                        displaced_values = displaced.b_hat
                        displaced_reason = None
                    except (DriftContractError, ValueError, np.linalg.LinAlgError) as exc:
                        displaced_values = None
                        displaced_reason = str(exc)
                    rows.append(
                        _result_row(
                            seed=seed,
                            dt=dt,
                            embargo=embargo,
                            embargo_multiple=embargo_multiple,
                            gap_steps=gap_steps,
                            train=train,
                            evaluation=evaluation,
                            overlap=overlap,
                            train_support=train_support,
                            evaluation_support=evaluation_support,
                            covariance=covariance,
                            alignment_neighborhoods=alignment_neighborhoods,
                            q_over_dt=q_over_dt,
                            comparator=f"negative_time_displaced_{estimator}",
                            estimator=estimator,
                            predicted=displaced_values,
                            truth=true_b,
                            production_api=True,
                            candidate_status="benchmark_only_negative_control",
                            refusal_reason=displaced_reason,
                            extra={
                                "time_displacement_steps": int(time_shift_steps),
                                "time_displacement_order": "evaluation_increment_indices_circularly_rolled",
                                "time_displacement_boundary": "circular_wrap",
                                "time_displacement_mapping": "scoring_index_j_uses_source_evaluation_index_shifted_evaluation[j]",
                                "time_displacement_source_evaluation_indices_by_scoring_index": shifted_evaluation.tolist(),
                                "time_displacement_source_evaluation_indices_sha256": _sha256_array(shifted_evaluation),
                            },
                        )
                    )

    # All rows for a scenario point to the same immutable covariance object.
    # Recompute the fingerprints from the rows as an explicit audit rather than
    # relying only on construction by convention.
    for key, expected_hash in scenario_covariance_hashes.items():
        matching = [row for row in rows if f"seed={row['seed']}|dt={row['dt_sec']:.12g}|embargo_multiple={row['embargo_multiple_of_dt']:.12g}" == key]
        observed = {row["eval_increment_covariance_sha256"] for row in matching}
        if observed != {expected_hash}:
            raise AssertionError(f"evaluation covariance changed across comparators for {key}")
        if not matching or any(row["eval_increment_covariance_shape"] != matching[0]["eval_increment_covariance_shape"] for row in matching):
            raise AssertionError(f"evaluation covariance shape changed across comparators for {key}")

    refused = [row for row in rows if row.get("refused")]
    by_comparator = _aggregate(rows, ["comparator", "estimator"])
    by_dt = _aggregate(rows, ["dt_sec", "comparator", "estimator"])
    by_embargo = _aggregate(rows, ["embargo_multiple_of_dt", "comparator", "estimator"])
    result = {
        "benchmark_schema_version": BENCHMARK_SCHEMA_VERSION,
        "spec_version": SPEC_VERSION,
        "spec_status": "frozen_primary_spec" if is_default_spec else "custom_test_spec",
        "spec": actual_spec,
        "spec_sha256": _sha256_json(actual_spec),
        "primary_default_spec_sha256": DEFAULT_SPEC_SHA256,
        "candidate_status": "candidate_not_qualified",
        "claim_status": "no_biological_claim",
        "truth_semantics": "discrete_chart_conditional_velocity",
        "truth_formula": "b_dt(x)=(A-I)x/dt",
        "not_an_ito_drift": True,
        "transition_model": "x[i+1]=A@x[i]+epsilon[i], epsilon~N(0,Q)",
        "a_b_d_definition": "b.T@a@b / ((b.T@b)*trace(a)+epsilon)",
        "a_b_d_covariance_input": "same_observed_evaluation_only_local_raw_increment_covariance_divided_by_dt_for_all_comparators",
        "a_b_d_local_semantics": "at_each_fixed_eval_centre_use_mean_b_over_the_same_eval_neighbourhood_and_that_neighbourhood_covariance",
        "alignment_diagnostic": {
            "status": "restricted_synthetic_alignment_diagnostic",
            "production_c1_qualification": False,
            "uses_fixed_eval_only_neighbourhoods": True,
            "uses_raw_increment_covariance": True,
            "residualization": "none",
            "not_full_ingest_end_to_end": True,
        },
        "oracle_covariance_distinction": "oracle conditional Q/dt is reported separately and is not substituted for observed evaluation covariance",
        "metric_definitions": {
            "rank_correlation": "Spearman correlation of centrewise velocity speeds",
            "a_b_d_rank_correlation": "Spearman correlation of local ingest-style A_bD values",
            "normalized_rmse": "RMSE divided by sqrt(mean(truth**2)) within the evaluation set; null for zero target scale",
            "prediction_variance_mean": "within-evaluation point prediction variance averaged over components",
            "*_sd_in_summary": "between-scenario standard deviation over the grouped seed/dt/embargo cells, not pointwise estimator variance at a shared x",
        },
        "simulation": {
            "base_dt_sec": float(base_dt),
            "base_A": matrix_a.tolist(),
            "base_Q": matrix_q.tolist(),
            "dt_sampling_mode": "same_seed_base_path_subsampled",
            "effective_transitions": actual_spec["effective_transitions"],
            "discrete_spectral_radius": float(np.max(np.abs(np.linalg.eigvals(matrix_a)))),
            "innovation_covariance_positive_definite": True,
        },
        "split_contract": {
            "train_evaluation_overlap_required": [],
            "embargo_violations_required": 0,
            "support": "explicit raw [t_i,t_{i+1}] endpoints passed to production crossfit",
            "evaluation_targets_used_by_crossfit": False,
        },
        "n_scenarios": total_scenarios,
        "n_result_rows": len(rows),
        "n_refused_rows": len(refused),
        "refusal_rate": len(refused) / len(rows) if rows else None,
        "refusal_counts_by_reason": {
            reason: sum(1 for row in refused if row.get("refusal_reason") == reason)
            for reason in sorted({str(row.get("refusal_reason")) for row in refused})
        },
        "evaluation_covariance_audit": {
            "n_scenarios": total_scenarios,
            "one_fixed_local_tensor_per_eval_centre_and_scenario": True,
            "all_comparators_share_scenario_tensors": True,
            "source": "evaluation_only_raw_neighbour_increments",
            "scenario_hashes": scenario_covariance_hashes,
        },
        "code_hashes": {
            "benchmark_module_sha256": _module_hash(Path(__file__).resolve()),
            "drift_module_sha256": _module_hash(drift_file) if drift_file else None,
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "platform": platform.platform(),
            "argv": list(sys.argv),
        },
        "summary": {
            "by_comparator": by_comparator,
            "by_dt": by_dt,
            "by_embargo_multiple_of_dt": by_embargo,
        },
        "rows": rows,
    }
    return _plain(result)


def _parse_number_list(value: str, *, integer: bool = False) -> tuple[Any, ...]:
    parts = [part.strip() for part in str(value).split(",") if part.strip()]
    if not parts:
        raise argparse.ArgumentTypeError("comma-separated list must not be empty")
    try:
        return tuple(int(part) if integer else float(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid comma-separated list: {value!r}") from exc


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the bounded synthetic DF-DRIFT-C1-M3 benchmark.")
    parser.add_argument("--output", type=Path, required=True, help="JSON output path")
    parser.add_argument("--seeds", type=lambda value: _parse_number_list(value, integer=True), default=DEFAULT_SEEDS)
    parser.add_argument("--dt-values", type=_parse_number_list, default=DEFAULT_DT_VALUES)
    parser.add_argument("--embargo-multiples", type=_parse_number_list, default=DEFAULT_EMBARGO_MULTIPLES)
    parser.add_argument("--base-dt", type=float, default=DEFAULT_BASE_DT)
    parser.add_argument("--n-samples", type=int, default=DEFAULT_N_SAMPLES)
    parser.add_argument("--burn-in", type=int, default=DEFAULT_BURN_IN)
    parser.add_argument("--train-fraction", type=float, default=DEFAULT_TRAIN_FRACTION)
    parser.add_argument("--n-neighbors", type=int, default=DEFAULT_N_NEIGHBORS)
    parser.add_argument("--min-train-support", type=int, default=DEFAULT_MIN_TRAIN_SUPPORT)
    parser.add_argument("--time-shift-steps", type=int, default=DEFAULT_TIME_SHIFT_STEPS)
    args = parser.parse_args(argv)
    result = run_m3_benchmark(
        seeds=args.seeds,
        dt_values=args.dt_values,
        embargo_multiples=args.embargo_multiples,
        base_dt=args.base_dt,
        n_samples=args.n_samples,
        burn_in=args.burn_in,
        train_fraction=args.train_fraction,
        n_neighbors=args.n_neighbors,
        min_train_support=args.min_train_support,
        time_shift_steps=args.time_shift_steps,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "spec_sha256": result["spec_sha256"],
        "spec_status": result["spec_status"],
        "n_scenarios": result["n_scenarios"],
        "n_result_rows": result["n_result_rows"],
        "n_refused_rows": result["n_refused_rows"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
