"""Bounded held-out M3 extension for linear, nonlinear and observed systems.

The extension is analysis-only.  It compares the existing cross-fit chart
velocity candidate on fixed independent query segments.  It does not claim
Markov sufficiency, an Ito drift, biological qualification, or an M3 PASS.
All comparator outputs use the same fixed query neighbourhoods and observed
raw-increment covariance for the operational A_bD diagnostic.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import platform
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .drift import DriftContractError, crossfit_local_chart_b


SCHEMA_VERSION = "nmd_analysis.m3_extension.v1"
SPEC_VERSION = "df_drift_c1_m3_extension.20260906.v1"
DT = 0.1
BASE_A_SCALAR = 0.65
CYCLIC_COUPLING = 0.08
INNOVATION_VARIANCE = 0.09
NONLINEAR_COEFFICIENT = 0.12
NOISY_VARIANCE = 0.09
TRAIN_SEEDS = tuple(range(101, 113))
QUERY_SEEDS = (9001, 9002, 9003)
TRAIN_STATES = 1800
BURN_IN = 300
QUERY_STATES = 49
QUERY_SOURCES_PER_SEGMENT = QUERY_STATES - 1
QUERY_PADDING_STATES = 3
N_QUERY_SOURCES = len(QUERY_SEEDS) * QUERY_SOURCES_PER_SEGMENT
N_NEIGHBORS = 64
MIN_TRAIN_SUPPORT = 16
EMBARGO_MULTIPLE = 2.0
TIME_SHIFT_STEPS = 17
EPSILON = 1e-12


def _plain(value: Any) -> Any:
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
    return _sha256_bytes(np.ascontiguousarray(np.asarray(value)).tobytes())


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(json.dumps(_plain(value), sort_keys=True, separators=(",", ":")).encode())


def _module_hash(path: Path) -> str | None:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError:
        return None


def _cyclic_matrix(dimension: int) -> np.ndarray:
    # np.roll(x, 1) has row j <- x[(j-1) % D].
    return np.roll(np.eye(dimension, dtype=float), 1, axis=0)


def _system_dimension(name: str) -> int:
    return 9 if ("9d" in name or name == "linear_hidden9_observed3") else 3


def _system_spec(name: str) -> dict[str, Any]:
    dimension = _system_dimension(name)
    nonlinear = "nonlinear" in name
    observed_partial = name == "linear_hidden9_observed3"
    observed_noisy = name == "linear_noisy3_observed3"
    H = np.eye(dimension, dtype=float)
    R = np.zeros((dimension, dimension), dtype=float)
    if observed_partial:
        H = np.zeros((3, 9), dtype=float)
        H[:, :3] = np.eye(3)
        R = np.zeros((3, 3), dtype=float)
    elif observed_noisy:
        R = NOISY_VARIANCE * np.eye(3)
    return {
        "name": name,
        "dimension_latent": dimension,
        "dimension_observed": int(H.shape[0]),
        "nonlinear": nonlinear,
        "A": (BASE_A_SCALAR * np.eye(dimension) + CYCLIC_COUPLING * _cyclic_matrix(dimension)).tolist(),
        "Q": (INNOVATION_VARIANCE * np.eye(dimension)).tolist(),
        "c": NONLINEAR_COEFFICIENT if nonlinear else 0.0,
        "H": H.tolist(),
        "R": R.tolist(),
        "initial_law": "N(0,P)" if not nonlinear else "zero_vector",
        "burn_in_transitions": BURN_IN,
        "observation_semantics": (
            "full_state" if not (observed_partial or observed_noisy) else
            "H_x" if observed_partial else "H_x_plus_independent_measurement_noise"
        ),
    }


SYSTEM_NAMES = (
    "full_linear3d",
    "full_nonlinear3d",
    "full_linear9d",
    "full_nonlinear9d",
    "linear_hidden9_observed3",
    "linear_noisy3_observed3",
)


def frozen_spec() -> dict[str, Any]:
    systems = [_system_spec(name) for name in SYSTEM_NAMES]
    return {
        "spec_version": SPEC_VERSION,
        "systems_requested": list(SYSTEM_NAMES),
        "systems": systems,
        "dt_sec": DT,
        "train_seeds": list(TRAIN_SEEDS),
        "query_seeds": list(QUERY_SEEDS),
        "train_states": TRAIN_STATES,
        "burn_in": BURN_IN,
        "query_states_per_segment": QUERY_STATES,
        "genuine_query_sources_per_segment": QUERY_SOURCES_PER_SEGMENT,
        "query_padding_states_after_train": QUERY_PADDING_STATES,
        "n_query_sources": N_QUERY_SOURCES,
        "n_neighbors": N_NEIGHBORS,
        "min_train_support": MIN_TRAIN_SUPPORT,
        "embargo_multiple_of_dt": EMBARGO_MULTIPLE,
        "time_shift_steps": TIME_SHIFT_STEPS,
        "epsilon": EPSILON,
        "segment_contract": {
            "train": "1800 genuine states, 1799 genuine train increments",
            "padding": "three zero carrier states; all padding and seam increments excluded",
            "heldout": f"{len(QUERY_SEEDS)} independent {QUERY_STATES}-state segments; {QUERY_SOURCES_PER_SEGMENT} genuine within-segment sources each",
            "physical_time": "independent segments carried on one regular synthetic time axis",
            "n_query_sources": "3*48=144",
        },
        "target_contract": {
            "full_linear": "(A-I)x/dt",
            "full_nonlinear": "(A@x+c*tanh(roll(x,1))-x)/dt",
            "observed_linear": "(H@A@P@H.T@inv(H@P@H.T+R)@Y-Y)/dt",
            "not_ito_drift": True,
        },
        "estimators": {
            "crossfit_mean": {"estimator": "local_mean", "n_neighbors": N_NEIGHBORS, "min_train_support": MIN_TRAIN_SUPPORT},
            "crossfit_linear": {"estimator": "local_linear", "n_neighbors": N_NEIGHBORS, "min_train_support": MIN_TRAIN_SUPPORT},
            "cross_segment_order_corruption": "np.roll(evaluation_indices, 17) with rows left in shifted source order; artificial cross-segment mapping",
        },
        "covariance_contract": "fixed eval-only raw observed increment covariance divided by dt shared by all comparators and repeats",
        "variance_contract": "pointwise across 12 training replicates at identical heldout queries; population variance, ddof=1 variance and MCSE",
        "no_pass_rule": "computed candidate diagnostics only; no automatic scientific PASS",
        "rng_mapping": {
            "seed_derivation": "token=sha256([seed,system,role])[:8] interpreted base16",
            "seed_sequence": "numpy SeedSequence([token,20260906])",
            "roles": ["trajectory", "observation_noise"],
            "initialization": "linear draw N(0,P) before burn; nonlinear zero before burn",
        },
    }


DEFAULT_SPEC = frozen_spec()
DEFAULT_SPEC_SHA256 = _sha256_json(DEFAULT_SPEC)


def _stationary_covariance(A: np.ndarray, Q: np.ndarray) -> np.ndarray:
    d = A.shape[0]
    system = np.eye(d * d) - np.kron(A, A)
    try:
        values = np.linalg.solve(system, Q.reshape(-1)).reshape(d, d)
    except np.linalg.LinAlgError as exc:
        raise ValueError("stationary covariance Lyapunov system is singular") from exc
    values = 0.5 * (values + values.T)
    eigenvalues = np.linalg.eigvalsh(values)
    if not np.isfinite(values).all() or float(np.min(eigenvalues)) <= 0:
        raise ValueError("stationary covariance is not positive definite")
    return values


def _rng_seed(seed: int, system: str, role: str) -> np.random.SeedSequence:
    token = int(_sha256_json([int(seed), system, role])[:8], 16)
    return np.random.SeedSequence([token, 2_026_090_6])


def _transition(A: np.ndarray, state: np.ndarray, coefficient: float) -> np.ndarray:
    return A @ state + coefficient * np.tanh(np.roll(state, 1))


def _simulate_latent(
    *, system: str, seed: int, n_states: int, burn_in: int, A: np.ndarray, Q: np.ndarray, P: np.ndarray | None
) -> np.ndarray:
    rng = np.random.default_rng(_rng_seed(seed, system, "trajectory"))
    total = int(n_states) + int(burn_in)
    if P is None:
        state = np.zeros(A.shape[0], dtype=float)
    else:
        state = rng.multivariate_normal(np.zeros(A.shape[0]), P)
    result = np.empty((total, A.shape[0]), dtype=float)
    result[0] = state
    coefficient = NONLINEAR_COEFFICIENT if "nonlinear" in system else 0.0
    innovations = rng.multivariate_normal(np.zeros(A.shape[0]), Q, size=total - 1)
    for index in range(total - 1):
        result[index + 1] = _transition(A, result[index], coefficient) + innovations[index]
    return result[int(burn_in) :]


def _observe(system: str, latent: np.ndarray, H: np.ndarray, R: np.ndarray, seed: int) -> np.ndarray:
    observed = (H @ latent.T).T
    if np.any(R):
        rng = np.random.default_rng(_rng_seed(seed, system, "observation_noise"))
        observed = observed + rng.multivariate_normal(np.zeros(observed.shape[1]), R, size=observed.shape[0])
    return observed


def _conditional_truth(system: str, observed: np.ndarray, A: np.ndarray, H: np.ndarray, R: np.ndarray, P: np.ndarray | None) -> tuple[np.ndarray, np.ndarray | None]:
    dt = DT
    if "nonlinear" in system:
        mean_next = (A @ observed.T).T + NONLINEAR_COEFFICIENT * np.tanh(np.roll(observed, 1, axis=1))
        b = (mean_next - observed) / dt
        return b, None
    if P is None:
        raise ValueError("linear observed target requires P")
    syy = H @ P @ H.T + R
    C = H @ A @ P @ H.T
    gain = C @ np.linalg.inv(syy)
    target = (observed @ gain.T - observed) / dt
    conditional_variance = syy - C @ np.linalg.inv(syy) @ C.T
    return target, 0.5 * (conditional_variance + conditional_variance.T)


def _concat_segments(train: np.ndarray, heldout: Sequence[np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    dimension = train.shape[1]
    padding = np.zeros((QUERY_PADDING_STATES, dimension), dtype=float)
    pieces = [train, padding, *heldout]
    trajectory = np.concatenate(pieces, axis=0)
    time = np.arange(trajectory.shape[0], dtype=float) * DT
    train_indices = np.arange(train.shape[0] - 1, dtype=np.int64)
    evaluation: list[int] = []
    segment_rows: list[dict[str, Any]] = []
    cursor = train.shape[0] + QUERY_PADDING_STATES
    for segment_number, block in enumerate(heldout):
        indices = np.arange(cursor, cursor + block.shape[0] - 1, dtype=np.int64)
        evaluation.extend(indices.tolist())
        segment_rows.append({
            "segment_number": segment_number,
            "carrier_state_start": cursor,
            "carrier_state_stop": cursor + block.shape[0] - 1,
            "source_indices": indices.tolist(),
            "n_states": int(block.shape[0]),
            "n_genuine_sources": int(indices.size),
            "segment_source_hash": _sha256_array(indices),
        })
        cursor += block.shape[0]
    evaluation_indices = np.asarray(evaluation, dtype=np.int64)
    train_support = np.column_stack((time[train_indices], time[train_indices + 1]))
    evaluation_support = np.column_stack((time[evaluation_indices], time[evaluation_indices + 1]))
    excluded = list(range(train.shape[0] - 1, train.shape[0] + QUERY_PADDING_STATES))
    excluded.extend(int(segment["carrier_state_stop"]) for segment in segment_rows[:-1])
    metadata = {
        "train_state_indices": [0, int(train.shape[0] - 1)],
        "excluded_carrier_indices": excluded,
        "heldout_segments": segment_rows,
        "all_seam_and_padding_increments_excluded": True,
        "evaluation_index_hash": _sha256_array(evaluation_indices),
        "train_index_hash": _sha256_array(train_indices),
    }
    return trajectory, time, train_indices, evaluation_indices, metadata


def _fixed_neighborhoods(trajectory: np.ndarray, evaluation: np.ndarray, n_neighbors: int) -> tuple[np.ndarray, ...]:
    states = trajectory[evaluation]
    used = min(int(n_neighbors), states.shape[0])
    result: list[np.ndarray] = []
    for query in states:
        with np.errstate(over="raise", invalid="raise"):
            distances = np.linalg.norm(states - query, axis=1)
        if not np.isfinite(distances).all():
            raise DriftContractError("nonfinite query neighbourhood distance")
        result.append(np.argsort(distances, kind="mergesort")[:used].astype(np.int64))
    return tuple(result)


def _local_covariance(trajectory: np.ndarray, evaluation: np.ndarray, neighborhoods: Sequence[np.ndarray]) -> np.ndarray:
    increment = trajectory[1:] - trajectory[:-1]
    tensors = []
    for neighborhood in neighborhoods:
        local = increment[evaluation[np.asarray(neighborhood, dtype=np.int64)]]
        tensor = np.atleast_2d(np.cov(local, rowvar=False, ddof=1)) / DT
        tensors.append(0.5 * (tensor + tensor.T))
    return np.asarray(tensors, dtype=float)


def _a_b_d(values: np.ndarray, covariance: np.ndarray) -> np.ndarray:
    b = np.asarray(values, dtype=float)
    a = np.asarray(covariance, dtype=float)
    trace = np.trace(a, axis1=1, axis2=2)
    norm_sq = np.einsum("ij,ij->i", b, b)
    numerator = np.einsum("ni,nij,nj->n", b, a, b)
    result = np.full(norm_sq.shape, np.nan, dtype=float)
    denominator = norm_sq * trace + EPSILON
    valid = np.isfinite(b).all(axis=1) & np.isfinite(denominator) & (norm_sq > 0)
    result[valid] = numerator[valid] / denominator[valid]
    return result


def _local_aligned_b(values: np.ndarray, neighborhoods: Sequence[np.ndarray]) -> np.ndarray:
    return np.asarray([np.mean(values[np.asarray(index, dtype=np.int64)], axis=0) for index in neighborhoods], dtype=float)


def _rankdata(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    sorted_values = values[order]
    ranks = np.empty(values.size, dtype=float)
    start = 0
    while start < values.size:
        end = start + 1
        while end < values.size and sorted_values[end] == sorted_values[start]:
            end += 1
        ranks[order[start:end]] = 0.5 * (start + end - 1) + 1
        start = end
    return ranks


def _spearman(left: np.ndarray, right: np.ndarray) -> float | None:
    mask = np.isfinite(left) & np.isfinite(right)
    if np.sum(mask) < 2:
        return None
    a, b = _rankdata(left[mask]), _rankdata(right[mask])
    a -= np.mean(a)
    b -= np.mean(b)
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denominator) if denominator > 0 else None


def _single_metrics(predicted: np.ndarray, truth: np.ndarray, covariance: np.ndarray, neighborhoods: Sequence[np.ndarray]) -> dict[str, Any]:
    finite = np.isfinite(predicted).all(axis=1) & np.isfinite(truth).all(axis=1)
    if not finite.any():
        return {"n_valid": 0, "support_fraction": 0.0, "validity_reason": "no_finite_prediction", "rmse": None, "normalized_rmse": None, "bias_vector": None, "bias_norm": None, "a_b_d_mean": None, "a_b_d_bias": None, "a_b_d_rank_correlation": None, "rank_correlation": None}
    pred = predicted[finite]
    target = truth[finite]
    error = pred - target
    aligned_pred = _local_aligned_b(predicted, neighborhoods)
    aligned_truth = _local_aligned_b(truth, neighborhoods)
    aligned_cov = covariance
    pred_a = _a_b_d(aligned_pred, aligned_cov)
    true_a = _a_b_d(aligned_truth, aligned_cov)
    pair = np.isfinite(pred_a) & np.isfinite(true_a)
    pred_a_finite = np.isfinite(pred_a)
    true_a_finite = np.isfinite(true_a)
    rmse = float(np.sqrt(np.mean(error**2)))
    scale = float(np.sqrt(np.mean(target**2)))
    return _plain({
        "n_valid": int(np.sum(finite)),
        "support_fraction": float(np.mean(finite)),
        "validity_reason": "ok" if bool(np.all(finite)) else "partial_prediction_support",
        "rmse": rmse,
        "normalized_rmse": rmse / scale if scale > 0 else None,
        "bias_vector": np.mean(error, axis=0),
        "bias_norm": float(np.linalg.norm(np.mean(error, axis=0))),
        "a_b_d_mean": float(np.mean(pred_a[pred_a_finite])) if pred_a_finite.any() else None,
        "a_b_d_true_mean": float(np.mean(true_a[true_a_finite])) if true_a_finite.any() else None,
        "a_b_d_bias": float(np.mean(pred_a[pair] - true_a[pair])) if pair.any() else None,
        "a_b_d_n_valid": int(np.sum(pair)),
        "a_b_d_validity_reason": "ok" if bool(np.all(pair)) else "partial_or_undefined_alignment",
        "a_b_d_rank_correlation": _spearman(pred_a, true_a),
        "rank_correlation": _spearman(np.linalg.norm(pred, axis=1), np.linalg.norm(target, axis=1)),
    })


def _pointwise_replicate_metrics(predictions: np.ndarray, truth: np.ndarray, covariance: np.ndarray, neighborhoods: Sequence[np.ndarray]) -> dict[str, Any]:
    # predictions: [replicate, query, component]
    finite = np.isfinite(predictions).all(axis=2)
    errors = predictions - truth[None, :, :]
    n = np.sum(finite, axis=0)
    component_count = n[:, None]
    masked_errors = np.where(finite[:, :, None], errors, 0.0)
    masked_predictions = np.where(finite[:, :, None], predictions, 0.0)
    masked_squared_errors = np.where(finite[:, :, None], errors**2, 0.0)
    mean_error = np.full(truth.shape, np.nan, dtype=float)
    population_variance = np.full(truth.shape, np.nan, dtype=float)
    sample_variance = np.full(truth.shape, np.nan, dtype=float)
    mse = np.full(truth.shape, np.nan, dtype=float)
    valid_query = n > 0
    valid_sample = n > 1
    if valid_query.any():
        mean_error[valid_query] = np.sum(masked_errors[:, valid_query, :], axis=0) / component_count[valid_query]
        mse[valid_query] = np.sum(masked_squared_errors[:, valid_query, :], axis=0) / component_count[valid_query]
        mean_prediction = np.sum(masked_predictions[:, valid_query, :], axis=0) / component_count[valid_query]
        centered = masked_predictions[:, valid_query, :] - mean_prediction[None, :, :]
        centered = np.where(finite[:, valid_query, None], centered, 0.0)
        population_variance[valid_query] = np.sum(centered**2, axis=0) / component_count[valid_query]
    if valid_sample.any():
        sample_variance[valid_sample] = population_variance[valid_sample] * n[valid_sample, None] / (n[valid_sample, None] - 1)
    identity = mse - (mean_error**2 + population_variance)
    aligned = np.asarray([_local_aligned_b(predictions[row], neighborhoods) for row in range(predictions.shape[0])])
    aligned_truth = _local_aligned_b(truth, neighborhoods)
    a_values = np.asarray([_a_b_d(aligned[row], covariance) for row in range(aligned.shape[0])])
    a_truth = _a_b_d(aligned_truth, covariance)
    a_finite = np.isfinite(a_values)
    a_error = a_values - a_truth[None, :]
    a_n = np.sum(a_finite, axis=0)
    a_bias = np.full(a_truth.shape, np.nan, dtype=float)
    a_pop = np.full(a_truth.shape, np.nan, dtype=float)
    a_sample = np.full(a_truth.shape, np.nan, dtype=float)
    a_mse = np.full(a_truth.shape, np.nan, dtype=float)
    if np.any(a_n > 0):
        valid_a = a_n > 0
        a_bias[valid_a] = np.sum(np.where(a_finite[:, valid_a], a_error[:, valid_a], 0.0), axis=0) / a_n[valid_a]
        a_mse[valid_a] = np.sum(np.where(a_finite[:, valid_a], a_error[:, valid_a]**2, 0.0), axis=0) / a_n[valid_a]
        a_mean = np.sum(np.where(a_finite[:, valid_a], a_values[:, valid_a], 0.0), axis=0) / a_n[valid_a]
        a_centered = np.where(a_finite[:, valid_a], a_values[:, valid_a] - a_mean[None, :], 0.0)
        a_pop[valid_a] = np.sum(a_centered**2, axis=0) / a_n[valid_a]
    if np.any(a_n > 1):
        valid_a_sample = a_n > 1
        a_sample[valid_a_sample] = a_pop[valid_a_sample] * a_n[valid_a_sample] / (a_n[valid_a_sample] - 1)
    velocity_reasons = ["ok" if count >= 2 else "no_finite_replicate" if count == 0 else "one_finite_replicate" for count in n]
    alignment_reasons = ["ok" if count >= 2 else "no_finite_alignment" if count == 0 else "one_finite_alignment" for count in a_n]
    return _plain({
        "n_replicates_by_query": n,
        "pointwise_validity_reason": velocity_reasons,
        "component_bias": mean_error,
        "component_variance_population": population_variance,
        "component_variance_sample_ddof1": sample_variance,
        "component_mcse": np.sqrt(sample_variance / np.where(component_count > 0, component_count, np.nan)),
        "component_mse": mse,
        "component_mse_identity_residual": identity,
        "prediction_support": finite,
        "prediction_values": predictions,
        "error_values": errors,
        "a_b_d_values": a_values,
        "a_b_d_truth": a_truth,
        "a_b_d_n_replicates_by_query": a_n,
        "a_b_d_validity_reason": alignment_reasons,
        "a_b_d_bias": a_bias,
        "a_b_d_variance_population": a_pop,
        "a_b_d_variance_sample_ddof1": a_sample,
        "a_b_d_mcse": np.sqrt(a_sample / np.where(a_n > 0, a_n, np.nan)),
        "a_b_d_mse": a_mse,
        "a_b_d_mse_identity_residual": a_mse - (a_bias**2 + a_pop),
    })


def _query_records(evaluation: np.ndarray, metadata: Mapping[str, Any], truth: np.ndarray, neighborhoods: Sequence[np.ndarray], covariance: np.ndarray) -> list[dict[str, Any]]:
    records = []
    for index, source in enumerate(evaluation):
        segment_number = None
        for segment in metadata["heldout_segments"]:
            if int(source) in segment["source_indices"]:
                segment_number = int(segment["segment_number"])
                break
        records.append({
            "query_index": index,
            "carrier_source_index": int(source),
            "original_segment_number": segment_number,
            "truth": truth[index].tolist(),
            "neighbour_indices_in_query_order": np.asarray(neighborhoods[index], dtype=int).tolist(),
            "raw_observed_increment_covariance_over_dt": covariance[index].tolist(),
        })
    return records


def _fit_one(
    *, system: str, train_seed: int, trajectory: np.ndarray, time: np.ndarray, train_indices: np.ndarray,
    evaluation: np.ndarray, eval_support: np.ndarray, train_support: np.ndarray, truth: np.ndarray,
    covariance: np.ndarray, neighborhoods: Sequence[np.ndarray], source_hash: str, drift_hash: str | None,
    n_neighbors: int, min_train_support: int, embargo: float, time_shift_steps: int,
) -> dict[str, Any]:
    outputs: dict[str, Any] = {}
    common = {
        "system": system,
        "train_seed": int(train_seed),
        "production_api": True,
        "source_artifact_hash": source_hash,
        "evaluation_source_index_hash": _sha256_array(evaluation),
    }
    for label, estimator in (("crossfit_mean", "local_mean"), ("crossfit_linear", "local_linear")):
        try:
            result = crossfit_local_chart_b(
                trajectory, time, train_indices, evaluation, estimator=estimator,
                n_neighbors=n_neighbors, min_train_support=min_train_support,
                embargo=embargo, train_window_support=train_support,
                evaluation_window_support=eval_support, source_artifact_hash=source_hash,
                source_nmd_schema="synthetic.m3_extension.v1", nmd_code_revision=drift_hash,
            )
            values = np.asarray(result.b_hat, dtype=float)
            reason = None
            status = str(result.provenance.get("candidate_status", "candidate_not_qualified"))
        except (DriftContractError, ValueError, np.linalg.LinAlgError) as exc:
            values = np.full_like(truth, np.nan)
            reason = str(exc)
            status = "candidate_not_qualified"
        outputs[label] = {
            **common, "estimator": estimator, "candidate_status": status, "refusal_reason": reason,
            "predictions": values, "metrics": _single_metrics(values, truth, covariance, neighborhoods),
            "support": np.isfinite(values).all(axis=1),
        }
        shifted = np.roll(evaluation, time_shift_steps)
        shifted_support = np.roll(eval_support, time_shift_steps, axis=0)
        try:
            displaced = crossfit_local_chart_b(
                trajectory, time, train_indices, shifted, estimator=estimator,
                n_neighbors=n_neighbors, min_train_support=min_train_support,
                embargo=embargo, train_window_support=train_support,
                evaluation_window_support=shifted_support, source_artifact_hash=source_hash,
                source_nmd_schema="synthetic.m3_extension.v1", nmd_code_revision=drift_hash,
            )
            displaced_values = np.asarray(displaced.b_hat, dtype=float)
            displaced_reason = None
            displaced_status = str(displaced.provenance.get("candidate_status", "candidate_not_qualified"))
        except (DriftContractError, ValueError, np.linalg.LinAlgError) as exc:
            displaced_values = np.full_like(truth, np.nan)
            displaced_reason = str(exc)
            displaced_status = "candidate_not_qualified"
        outputs[f"cross_segment_order_corruption_{label.removeprefix('crossfit_')}"] = {
            **common, "estimator": estimator, "candidate_status": displaced_status,
            "refusal_reason": displaced_reason, "predictions": displaced_values,
            "metrics": _single_metrics(displaced_values, truth, covariance, neighborhoods),
            "support": np.isfinite(displaced_values).all(axis=1),
            "order_corruption_steps": time_shift_steps,
            "order_corruption_boundary": "circular_wrap_across_heldout_segments",
            "order_corruption_source_indices_by_scoring_index": shifted,
            "order_corruption_source_indices_hash": _sha256_array(shifted),
        }
    return outputs


def _run_system(
    system: str,
    drift_hash: str | None,
    *,
    train_seeds: Sequence[int],
    query_seeds: Sequence[int],
    train_states: int,
    burn_in: int,
    query_states: int,
    n_neighbors: int,
    min_train_support: int,
    embargo_multiple: float,
    time_shift_steps: int,
) -> dict[str, Any]:
    settings = _system_spec(system)
    A = np.asarray(settings["A"], dtype=float)
    Q = np.asarray(settings["Q"], dtype=float)
    H = np.asarray(settings["H"], dtype=float)
    R = np.asarray(settings["R"], dtype=float)
    P = _stationary_covariance(A, Q) if not settings["nonlinear"] else None
    train_latent_paths: dict[int, np.ndarray] = {}
    train_paths: dict[int, np.ndarray] = {}
    for seed in train_seeds:
        latent = _simulate_latent(system=system, seed=seed, n_states=train_states, burn_in=burn_in, A=A, Q=Q, P=P)
        train_latent_paths[seed] = latent
        train_paths[seed] = _observe(system, latent, H, R, seed)
    query_latent_paths: dict[int, np.ndarray] = {}
    query_paths: list[np.ndarray] = []
    for seed in query_seeds:
        latent = _simulate_latent(system=system, seed=seed, n_states=query_states, burn_in=burn_in, A=A, Q=Q, P=P)
        query_latent_paths[seed] = latent
        query_paths.append(_observe(system, latent, H, R, seed))
    combined_for_geometry, _, _, evaluation_for_geometry, segment_metadata = _concat_segments(train_paths[train_seeds[0]], query_paths)
    truth, conditional_variance = _conditional_truth(system, combined_for_geometry[evaluation_for_geometry], A if settings["nonlinear"] else A, H, R, P)
    neighborhoods = _fixed_neighborhoods(combined_for_geometry, evaluation_for_geometry, n_neighbors)
    covariance = _local_covariance(combined_for_geometry, evaluation_for_geometry, neighborhoods)
    eval_support = np.column_stack((evaluation_for_geometry * DT, (evaluation_for_geometry + 1) * DT))
    rows: list[dict[str, Any]] = []
    predictions: dict[str, list[np.ndarray]] = {"crossfit_mean": [], "crossfit_linear": [], "cross_segment_order_corruption_mean": [], "cross_segment_order_corruption_linear": []}
    per_seed: list[dict[str, Any]] = []
    for train_seed in train_seeds:
        combined, time, train_indices, evaluation, metadata = _concat_segments(train_paths[train_seed], query_paths)
        if not np.array_equal(evaluation, evaluation_for_geometry):
            raise AssertionError("evaluation indices changed across training replicates")
        train_support = np.column_stack((time[train_indices], time[train_indices + 1]))
        latent_combined, _, _, latent_evaluation, latent_metadata = _concat_segments(train_latent_paths[train_seed], [query_latent_paths[seed] for seed in query_seeds])
        if not np.array_equal(latent_evaluation, evaluation):
            raise AssertionError("latent and observed segment indices changed")
        source_hash = _sha256_json({
            "system": system,
            "train_seed": train_seed,
            "latent_trajectory": _sha256_array(latent_combined),
            "observed_trajectory": _sha256_array(combined),
            "segments": metadata,
        })
        fitted = _fit_one(system=system, train_seed=train_seed, trajectory=combined, time=time, train_indices=train_indices, evaluation=evaluation, eval_support=eval_support, train_support=train_support, truth=truth, covariance=covariance, neighborhoods=neighborhoods, source_hash=source_hash, drift_hash=drift_hash, n_neighbors=n_neighbors, min_train_support=min_train_support, embargo=embargo_multiple * DT, time_shift_steps=time_shift_steps)
        seed_rows: dict[str, Any] = {"train_seed": train_seed, "source_artifact_hash": source_hash, "segment_metadata": metadata, "comparators": {}}
        for label, entry in fitted.items():
            predictions[label].append(entry["predictions"])
            seed_rows["comparators"][label] = {key: value for key, value in entry.items() if key not in {"predictions", "support"}}
            seed_rows["comparators"][label]["support_count"] = int(np.sum(entry["support"]))
            rows.append({**{key: value for key, value in entry.items() if key not in {"predictions", "support"}}, "support_count": int(np.sum(entry["support"]))})
        per_seed.append(seed_rows)
    oracle_metrics = _single_metrics(truth, truth, covariance, neighborhoods)
    comparator_results: dict[str, Any] = {
        "oracle": {"predictions": truth, "metrics": oracle_metrics, "candidate_status": "truth_known_positive_control", "production_api": False},
        "training_replicates": rows,
    }
    pointwise: dict[str, Any] = {}
    for label, arrays in predictions.items():
        matrix = np.asarray(arrays, dtype=float)
        pointwise[label] = {
            "predictions": matrix,
            "support": np.isfinite(matrix).all(axis=2),
            "metrics": _pointwise_replicate_metrics(matrix, truth, covariance, neighborhoods),
        }
    return {
        "system": system,
        "system_spec": settings,
        "stationary_covariance_P": P,
        "analytic_observed_conditional_variance": conditional_variance,
        "query_truth": truth,
        "query_observed": np.concatenate([query_paths[index][:-1] for index in range(len(query_paths))], axis=0),
        "query_next_observed": np.concatenate([query_paths[index][1:] for index in range(len(query_paths))], axis=0),
        "query_latent": [query_latent_paths[seed] for seed in query_seeds],
        "query_observed_segments": query_paths,
        "query_index_records": _query_records(evaluation_for_geometry, segment_metadata, truth, neighborhoods, covariance),
        "query_evaluation_index_hash": _sha256_array(evaluation_for_geometry),
        "query_covariance": covariance,
        "query_covariance_hash": _sha256_array(covariance),
        "query_covariance_semantics": "fixed_eval_only_raw_observed_increment_covariance_divided_by_dt",
        "segment_metadata": segment_metadata,
        "array_hashes": {
            "training_latent": {str(seed): _sha256_array(train_latent_paths[seed]) for seed in train_seeds},
            "training_observed": {str(seed): _sha256_array(train_paths[seed]) for seed in train_seeds},
            "query_latent": {str(seed): _sha256_array(query_latent_paths[seed]) for seed in query_seeds},
            "query_observed": {str(seed): _sha256_array(query_paths[index]) for index, seed in enumerate(query_seeds)},
        },
        "run_settings": {
            "train_states": train_states, "burn_in": burn_in, "query_states": query_states,
            "n_neighbors": n_neighbors, "min_train_support": min_train_support,
            "embargo_multiple": embargo_multiple, "time_shift_steps": time_shift_steps,
        },
        "oracle": comparator_results["oracle"],
        "training_replicates": per_seed,
        "pointwise": pointwise,
        "rows": rows,
    }


def run_m3_extension(
    *,
    systems: Sequence[str] = SYSTEM_NAMES,
    train_seeds: Sequence[int] = TRAIN_SEEDS,
    query_seeds: Sequence[int] = QUERY_SEEDS,
    train_states: int = TRAIN_STATES,
    burn_in: int = BURN_IN,
    query_states: int = QUERY_STATES,
    n_neighbors: int = N_NEIGHBORS,
    min_train_support: int = MIN_TRAIN_SUPPORT,
    embargo_multiple: float = EMBARGO_MULTIPLE,
    time_shift_steps: int = TIME_SHIFT_STEPS,
) -> dict[str, Any]:
    """Run the frozen held-out M3 extension and return strict JSON-safe data."""

    train_seeds = _validated_seed_tuple(train_seeds, "train_seeds", 2)
    query_seeds = _validated_seed_tuple(query_seeds, "query_seeds", 1)
    if set(train_seeds) & set(query_seeds):
        raise ValueError("train_seeds and query_seeds must be disjoint")
    requested = tuple(systems)
    if not requested or len(set(requested)) != len(requested):
        raise ValueError("systems must be nonempty and unique")
    if any(not isinstance(name, str) for name in requested):
        raise ValueError("systems must contain names")
    unknown = sorted(set(requested) - set(SYSTEM_NAMES))
    if unknown:
        raise ValueError(f"unknown systems: {unknown}")
    if isinstance(train_states, (bool, np.bool_)) or not isinstance(train_states, (int, np.integer)) or train_states < 4:
        raise ValueError("train_states must be an integer >= 4")
    if isinstance(burn_in, (bool, np.bool_)) or not isinstance(burn_in, (int, np.integer)) or burn_in < 0:
        raise ValueError("burn_in must be a non-negative integer")
    if isinstance(query_states, (bool, np.bool_)) or not isinstance(query_states, (int, np.integer)) or query_states < 3:
        raise ValueError("query_states must be an integer >= 3")
    if isinstance(n_neighbors, (bool, np.bool_)) or not isinstance(n_neighbors, (int, np.integer)) or n_neighbors < 2:
        raise ValueError("n_neighbors must be an integer >= 2")
    if isinstance(min_train_support, (bool, np.bool_)) or not isinstance(min_train_support, (int, np.integer)) or min_train_support < 1:
        raise ValueError("min_train_support must be a positive integer")
    if not np.isfinite(embargo_multiple) or embargo_multiple < 0:
        raise ValueError("embargo_multiple must be finite and non-negative")
    if isinstance(time_shift_steps, (bool, np.bool_)) or not isinstance(time_shift_steps, (int, np.integer)):
        raise ValueError("time_shift_steps must be an integer")
    if time_shift_steps < 1 or time_shift_steps >= len(query_seeds) * (int(query_states) - 1):
        raise ValueError("time_shift_steps must be strictly inside the query source set")
    actual_spec = dict(DEFAULT_SPEC)
    actual_spec.update({
        "systems_requested": list(requested),
        "train_seeds": list(train_seeds), "query_seeds": list(query_seeds),
        "train_states": int(train_states), "burn_in": int(burn_in), "query_states_per_segment": int(query_states),
        "genuine_query_sources_per_segment": int(query_states - 1),
        "n_query_sources": int(len(query_seeds) * (query_states - 1)),
        "n_neighbors": int(n_neighbors), "min_train_support": int(min_train_support),
        "embargo_multiple_of_dt": float(embargo_multiple), "time_shift_steps": int(time_shift_steps),
    })
    actual_spec["segment_contract"] = {
        "train": f"{int(train_states)} genuine states, {int(train_states) - 1} genuine train increments",
        "padding": "three zero carrier states; all padding and seam increments excluded",
        "heldout": f"{len(query_seeds)} independent {int(query_states)}-state segments; {int(query_states) - 1} genuine within-segment sources each",
        "physical_time": "independent segments carried on one regular synthetic time axis",
        "n_query_sources": f"{len(query_seeds)}*{int(query_states) - 1}={len(query_seeds) * (int(query_states) - 1)}",
    }
    actual_spec["estimators"] = {
        "crossfit_mean": {"estimator": "local_mean", "n_neighbors": int(n_neighbors), "min_train_support": int(min_train_support)},
        "crossfit_linear": {"estimator": "local_linear", "n_neighbors": int(n_neighbors), "min_train_support": int(min_train_support)},
        "cross_segment_order_corruption": f"np.roll(evaluation_indices, {int(time_shift_steps)}) with rows left in shifted source order; artificial cross-segment mapping",
    }
    default_call = (
        requested == SYSTEM_NAMES and train_seeds == TRAIN_SEEDS and query_seeds == QUERY_SEEDS
        and train_states == TRAIN_STATES and burn_in == BURN_IN and query_states == QUERY_STATES
        and n_neighbors == N_NEIGHBORS and min_train_support == MIN_TRAIN_SUPPORT
        and float(embargo_multiple) == EMBARGO_MULTIPLE and time_shift_steps == TIME_SHIFT_STEPS
    )
    drift_file = Path(inspect.getsourcefile(crossfit_local_chart_b) or "")
    system_results = {
        name: _run_system(
            name, _module_hash(drift_file) if drift_file else None,
            train_seeds=train_seeds, query_seeds=query_seeds, train_states=int(train_states),
            burn_in=int(burn_in), query_states=int(query_states), n_neighbors=int(n_neighbors),
            min_train_support=int(min_train_support), embargo_multiple=float(embargo_multiple),
            time_shift_steps=int(time_shift_steps),
        )
        for name in requested
    }
    result = {
        "schema_version": SCHEMA_VERSION,
        "spec_version": SPEC_VERSION,
        "spec_status": "frozen_primary_spec" if default_call else "custom_test_spec",
        "spec": actual_spec,
        "spec_sha256": _sha256_json(actual_spec),
        "primary_default_spec_sha256": DEFAULT_SPEC_SHA256,
        "candidate_status": "candidate_not_qualified",
        "claim_status": "no_biological_claim",
        "scientific_gate": "no_automatic_pass",
        "truth_semantics": "discrete_observed_conditional_velocity",
        "markov_sufficiency_established": False,
        "systems": system_results,
        "provenance": {
            "code_hash": _module_hash(Path(__file__).resolve()),
            "drift_code_hash": _module_hash(drift_file) if drift_file else None,
            "runtime": {"python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform(), "argv": list(sys.argv)},
        },
    }
    return _plain(result)


def spec_only() -> dict[str, Any]:
    return _plain({
        "schema_version": SCHEMA_VERSION,
        "spec_version": SPEC_VERSION,
        "spec_status": "frozen_primary_spec",
        "spec": DEFAULT_SPEC,
        "spec_sha256": DEFAULT_SPEC_SHA256,
        "candidate_status": "candidate_not_qualified",
        "claim_status": "no_biological_claim",
        "scientific_gate": "no_automatic_pass",
        "simulation_performed": False,
        "fit_performed": False,
        "code_hash": _module_hash(Path(__file__).resolve()),
    })


def _validated_seed_tuple(values: Sequence[int], name: str, minimum: int) -> tuple[int, ...]:
    raw = tuple(values)
    if len(raw) < minimum:
        raise ValueError(f"{name} must contain at least {minimum} seeds")
    if any(isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) for value in raw):
        raise ValueError(f"{name} must contain integer seeds")
    result = tuple(int(value) for value in raw)
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must contain unique seeds")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run or serialize the frozen M3 extension.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--spec-only", action="store_true")
    args = parser.parse_args(argv)
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {args.output}")
    result = spec_only() if args.spec_only else run_m3_extension()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "spec_sha256": result["spec_sha256"], "spec_status": result["spec_status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
