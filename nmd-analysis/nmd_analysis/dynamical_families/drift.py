"""Analysis-owned candidate chart drift for DF-DRIFT-C1-M3.

This module deliberately produces a *candidate* velocity field only.  It does
not identify an Ito drift, qualify C1, or alter an increment-covariance
estimate.  The estimator is cross-fit by construction: every prediction uses
only training increments supplied by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

import numpy as np


class DriftContractError(ValueError):
    """Raised when a requested M3 candidate violates a fail-closed contract."""


@dataclass(frozen=True)
class DriftCandidateResult:
    """Auditable held-out chart velocity candidate."""

    b_hat: np.ndarray
    evaluation_increment_indices: np.ndarray
    train_increment_indices: np.ndarray
    provenance: Mapping[str, Any]


def _sha256_array(values: np.ndarray) -> str:
    arr = np.ascontiguousarray(values)
    return hashlib.sha256(arr.tobytes()).hexdigest()


def _indices(value: Sequence[int] | np.ndarray, name: str, n: int) -> np.ndarray:
    raw = np.asarray(value)
    if raw.dtype.kind not in {"i", "u"}:
        raise DriftContractError(f"{name} must contain integer indices")
    result = raw.astype(np.int64, copy=False)
    if result.ndim != 1 or result.size == 0:
        raise DriftContractError(f"{name} must be a non-empty 1-D index array")
    if np.any(result < 0) or np.any(result >= n - 1):
        raise DriftContractError(f"{name} contains an invalid increment index")
    if np.unique(result).size != result.size:
        raise DriftContractError(f"{name} must contain unique increment indices")
    return result


def _support_intervals(time: np.ndarray, indices: np.ndarray,
                       support: np.ndarray | None) -> np.ndarray:
    actual = np.column_stack((time[indices], time[indices + 1]))
    if support is None:
        return actual
    support = np.asarray(support, dtype=float)
    if support.shape != (indices.size, 2) or not np.isfinite(support).all():
        raise DriftContractError("window_support must have shape (n_indices, 2) and be finite")
    if np.any(support[:, 1] < support[:, 0]):
        raise DriftContractError("window_support endpoints must be ordered")
    if np.any(support[:, 0] > actual[:, 0]) or np.any(support[:, 1] < actual[:, 1]):
        raise DriftContractError("window_support must include each increment's time endpoints")
    return support


def crossfit_local_chart_b(
    trajectory: np.ndarray,
    time: np.ndarray,
    train_increment_indices: Sequence[int] | np.ndarray,
    evaluation_increment_indices: Sequence[int] | np.ndarray,
    *,
    estimator: str = "local_mean",
    n_neighbors: int = 8,
    min_train_support: int = 3,
    embargo: float = 0.0,
    train_window_support: np.ndarray | None = None,
    evaluation_window_support: np.ndarray | None = None,
    dt_tolerance: float = 1e-8,
    source_artifact_hash: str | None = None,
    source_nmd_schema: str | None = None,
    nmd_code_revision: str | None = None,
    estimator_id: str = "crossfit_local_chart_b.v1",
) -> DriftCandidateResult:
    """Estimate a held-out chart velocity from training increments.

    ``trajectory[i] -> trajectory[i+1]`` is an increment observation.  For
    each evaluation state, the estimator uses nearest training *source*
    states and their velocity ``(x[i+1]-x[i]) / dt[i]``.  ``local_linear``
    additionally fits an affine response around the evaluation state.
    The output is intentionally marked ``candidate_not_qualified``.
    """
    x = np.asarray(trajectory, dtype=float)
    t = np.asarray(time, dtype=float)
    if x.ndim != 2 or x.shape[0] < 3 or x.shape[1] < 1 or not np.isfinite(x).all():
        raise DriftContractError("trajectory must be a finite array of shape (T, D), T >= 3")
    if t.ndim != 1 or t.size != x.shape[0] or not np.isfinite(t).all():
        raise DriftContractError("time must be a finite vector aligned with trajectory")
    try:
        with np.errstate(over="raise", invalid="raise"):
            dt = np.diff(t)
    except FloatingPointError as exc:
        raise DriftContractError("time differences overflow or are invalid") from exc
    if not np.isfinite(dt).all():
        raise DriftContractError("time differences must be finite")
    if np.any(dt <= 0):
        raise DriftContractError("time must be strictly increasing")
    if not np.allclose(dt, dt[0], rtol=0.0, atol=dt_tolerance):
        raise DriftContractError("irregular dt is unavailable for this candidate estimator")
    if estimator not in {"local_mean", "local_linear"}:
        raise DriftContractError("estimator must be 'local_mean' or 'local_linear'")
    if isinstance(n_neighbors, (bool, np.bool_)) or not isinstance(n_neighbors, (int, np.integer)):
        raise DriftContractError("n_neighbors must be an integer")
    if isinstance(min_train_support, (bool, np.bool_)) or not isinstance(min_train_support, (int, np.integer)):
        raise DriftContractError("min_train_support must be an integer")
    if n_neighbors < 1 or min_train_support < 1:
        raise DriftContractError("n_neighbors and min_train_support must be positive")
    if not np.isfinite(dt_tolerance) or dt_tolerance < 0:
        raise DriftContractError("dt_tolerance must be finite and non-negative")
    if embargo < 0 or not np.isfinite(embargo):
        raise DriftContractError("embargo must be a finite non-negative duration")

    train = _indices(train_increment_indices, "train_increment_indices", x.shape[0])
    evaluation = _indices(evaluation_increment_indices, "evaluation_increment_indices", x.shape[0])
    overlap = np.intersect1d(train, evaluation)
    if overlap.size:
        raise DriftContractError("train/evaluation increment overlap is forbidden")
    train_support = _support_intervals(t, train, train_window_support)
    eval_support = _support_intervals(t, evaluation, evaluation_window_support)
    for a, b in eval_support:
        try:
            with np.errstate(over="raise", invalid="raise"):
                distance = np.maximum(train_support[:, 0] - b, a - train_support[:, 1])
        except FloatingPointError as exc:
            raise DriftContractError("time-window distance overflow or is invalid") from exc
        if not np.isfinite(distance).all():
            raise DriftContractError("time-window distances must be finite")
        if np.any(distance <= embargo):
            raise DriftContractError("train/evaluation windows violate the requested time embargo")

    if train.size < min_train_support:
        raise DriftContractError("insufficient training support")
    train_states = x[train]
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            train_velocity = (x[train + 1] - train_states) / dt[train, None]
    except FloatingPointError as exc:
        raise DriftContractError("training velocity arithmetic overflow or is invalid") from exc
    if not np.isfinite(train_velocity).all():
        raise DriftContractError("training velocity must be finite")
    result = np.full((evaluation.size, x.shape[1]), np.nan, dtype=float)
    used = min(n_neighbors, train.size)
    for row, idx in enumerate(evaluation):
        try:
            with np.errstate(over="raise", invalid="raise"):
                offsets_to_query = train_states - x[idx]
                distances = np.linalg.norm(offsets_to_query, axis=1)
        except FloatingPointError as exc:
            raise DriftContractError("neighbour distance arithmetic overflow or is invalid") from exc
        if not np.isfinite(offsets_to_query).all() or not np.isfinite(distances).all():
            raise DriftContractError("neighbour distances must be finite")
        nearest = np.argsort(distances, kind="mergesort")[:used]
        if nearest.size < min_train_support:
            raise DriftContractError("insufficient local training support")
        if estimator == "local_mean":
            try:
                with np.errstate(over="raise", invalid="raise", divide="raise"):
                    result[row] = np.mean(train_velocity[nearest], axis=0)
            except FloatingPointError as exc:
                raise DriftContractError("local_mean reduction overflow or is invalid") from exc
        else:
            z = train_states[nearest] - x[idx]
            design = np.column_stack((np.ones(nearest.size), z))
            if not np.isfinite(design).all():
                raise DriftContractError("local_linear design must be finite")
            try:
                with np.errstate(over="raise", invalid="raise", divide="raise"):
                    rank = np.linalg.matrix_rank(design)
            except (FloatingPointError, np.linalg.LinAlgError) as exc:
                raise DriftContractError("local_linear rank arithmetic overflow or is invalid") from exc
            if design.shape[0] < x.shape[1] + 1 or rank < x.shape[1] + 1:
                raise DriftContractError("local_linear estimator has insufficient local rank")
            try:
                with np.errstate(over="raise", invalid="raise", divide="raise"):
                    coefficients, *_ = np.linalg.lstsq(design, train_velocity[nearest], rcond=None)
            except (FloatingPointError, np.linalg.LinAlgError) as exc:
                raise DriftContractError("local_linear fitting overflow or is invalid") from exc
            if not np.isfinite(coefficients).all():
                raise DriftContractError("local_linear coefficients must be finite")
            result[row] = coefficients[0]
        if not np.isfinite(result[row]).all():
            raise DriftContractError("candidate velocity must be finite")

    provenance = {
        "estimator_id": estimator_id,
        "estimator": estimator,
        "candidate_status": "candidate_not_qualified",
        "claim_status": "no_biological_claim",
        "drift_mode": "alignment_only",
        "drift_residualization": "none",
        "a_semantics": "raw_increment_covariance",
        "train_increment_indices": train.tolist(),
        "evaluation_increment_indices": evaluation.tolist(),
        "train_increment_indices_hash": _sha256_array(train),
        "evaluation_increment_indices_hash": _sha256_array(evaluation),
        "b_hat_hash": _sha256_array(result.astype(np.float64)),
        "trajectory_hash": _sha256_array(x.astype(np.float64)),
        "time_hash": _sha256_array(t.astype(np.float64)),
        "train_evaluation_overlap": overlap.tolist(),
        "embargo": float(embargo),
        "embargo_violations": 0,
        "train_window_support": train_support.tolist(),
        "evaluation_window_support": eval_support.tolist(),
        "train_window_support_hash": _sha256_array(train_support.astype(np.float64)),
        "evaluation_window_support_hash": _sha256_array(eval_support.astype(np.float64)),
        "window_support_specification": "explicit" if train_window_support is not None or evaluation_window_support is not None else "increment_endpoints",
        "estimator_hyperparameters": {"n_neighbors": int(n_neighbors), "min_train_support": int(min_train_support)},
        "dt": float(dt[0]),
        "dt_tolerance": float(dt_tolerance),
        "source_artifact_hash": source_artifact_hash,
        "source_nmd_schema": source_nmd_schema,
        "nmd_code_revision": nmd_code_revision,
        "qualification_id": None,
    }
    return DriftCandidateResult(result, evaluation.copy(), train.copy(), provenance)


def provenance_json(result: DriftCandidateResult) -> str:
    """Serialize candidate provenance with stable key ordering for audit logs."""
    return json.dumps(dict(result.provenance), sort_keys=True, separators=(",", ":"))
