"""Small, deterministic CHART audit for the M3 chart-drift candidate.

The functions in this module are deliberately limited to mathematical and
contract checks.  They do not qualify an empirical drift, change the MNPS
chart, or assign a biological interpretation to any result.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import platform
import warnings
from pathlib import Path
from typing import Any, Callable

import numpy as np
import scipy

from .drift import DriftContractError, crossfit_local_chart_b


# These values are the primary CHART specification.  Keep them explicit and
# serializable: the coordinator must be able to freeze and hash the numerical
# experiment before inspecting its outcome.
FROZEN_SEED = 20260906
FROZEN_DT = 0.2
FROZEN_N_POINTS = 96
FROZEN_TRAIN_INDICES = tuple(range(0, 48))
FROZEN_EVALUATION_INDICES = tuple(range(64, 72))
FROZEN_N_NEIGHBORS = 8
FROZEN_MIN_TRAIN_SUPPORT = 4
FROZEN_IDENTITY_TOLERANCE = 1.0e-10

FROZEN_A = np.array(
    [
        [0.82, 0.08, -0.03],
        [0.02, 0.77, 0.05],
        [-0.04, 0.03, 0.68],
    ],
    dtype=float,
)
FROZEN_Q = np.array(
    [
        [0.45, 0.08, 0.03],
        [0.08, 0.32, 0.05],
        [0.03, 0.05, 0.21],
    ],
    dtype=float,
)
FROZEN_ORTHOGONAL = np.array(
    [
        [0.8, -0.6, 0.0],
        [0.6, 0.8, 0.0],
        [0.0, 0.0, 1.0],
    ],
    dtype=float,
)
FROZEN_ISOTROPIC_SCALE = 1.75
FROZEN_ANISOTROPIC = np.diag([2.0, 0.5, 1.5]).astype(float)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _provenance() -> dict[str, Any]:
    """Return source and runtime provenance without embedding machine paths."""
    drift_file = Path(inspect.getsourcefile(crossfit_local_chart_b) or "")
    return {
        "source": {
            "chart_module": "nmd_analysis/dynamical_families/chart_benchmark.py",
            "chart_module_sha256": _sha256_file(Path(__file__).resolve()),
            "drift_module": "nmd_analysis/dynamical_families/drift.py",
            "drift_module_sha256": _sha256_file(drift_file.resolve()) if drift_file.is_file() else None,
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
    }


def _spec(
    *,
    seed: int,
    n_neighbors: int,
    min_train_support: int,
    identity_tolerance: float,
) -> dict[str, Any]:
    return {
        "seed": int(seed),
        "dt": float(FROZEN_DT),
        "n_points": int(FROZEN_N_POINTS),
        "train_increment_indices": list(FROZEN_TRAIN_INDICES),
        "evaluation_increment_indices": list(FROZEN_EVALUATION_INDICES),
        "n_neighbors": int(n_neighbors),
        "min_train_support": int(min_train_support),
        "identity_tolerance": float(identity_tolerance),
        "A": FROZEN_A.tolist(),
        "Q": FROZEN_Q.tolist(),
        "orthogonal_map": FROZEN_ORTHOGONAL.tolist(),
        "isotropic_scale": float(FROZEN_ISOTROPIC_SCALE),
        "anisotropic_map": FROZEN_ANISOTROPIC.tolist(),
    }


def _trajectory(seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Generate the fixed linear-Gaussian trajectory used by CHART."""
    rng = np.random.default_rng(int(seed))
    x = np.empty((FROZEN_N_POINTS, FROZEN_A.shape[0]), dtype=float)
    x[0] = rng.normal(loc=0.0, scale=0.25, size=FROZEN_A.shape[0])
    chol = np.linalg.cholesky(FROZEN_Q)
    innovations = rng.normal(size=(FROZEN_N_POINTS - 1, FROZEN_A.shape[0])) @ chol.T
    for index in range(FROZEN_N_POINTS - 1):
        x[index + 1] = x[index] @ FROZEN_A.T + innovations[index]
    time = np.arange(FROZEN_N_POINTS, dtype=float) * FROZEN_DT
    return x, time


def _truth_velocity(x: np.ndarray, matrix: np.ndarray = FROZEN_A) -> np.ndarray:
    """Return the conditional discrete chart velocity ``(A-I)x/dt``."""
    return (np.asarray(x, dtype=float) @ (np.asarray(matrix, dtype=float) - np.eye(3)).T) / FROZEN_DT


def _transform_rows(values: np.ndarray, transform: np.ndarray) -> np.ndarray:
    """Apply a column-vector map to a row-major state/velocity array."""
    return np.asarray(values, dtype=float) @ np.asarray(transform, dtype=float).T


def _max_abs(values: np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return 0.0
    with np.errstate(over="ignore", invalid="ignore"):
        result = np.max(np.abs(array))
    return float(result)


def _rmse(values: np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    with np.errstate(over="ignore", invalid="ignore"):
        result = np.sqrt(np.mean(np.square(array)))
    return float(result)


def _relative_error(observed: np.ndarray, expected: np.ndarray) -> float:
    denominator = max(1.0, _max_abs(expected))
    return _max_abs(np.asarray(observed) - np.asarray(expected)) / denominator


def _nearest_indices(
    trajectory: np.ndarray,
    train_indices: np.ndarray,
    evaluation_indices: np.ndarray,
    n_neighbors: int,
) -> list[list[int]]:
    """Reproduce the existing estimator's stable nearest-neighbour ordering."""
    output: list[list[int]] = []
    for index in evaluation_indices:
        distances = np.linalg.norm(trajectory[train_indices] - trajectory[index], axis=1)
        nearest = np.argsort(distances, kind="mergesort")[: min(n_neighbors, train_indices.size)]
        output.append(train_indices[nearest].astype(int).tolist())
    return output


def _candidate(
    trajectory: np.ndarray,
    time: np.ndarray,
    estimator: str,
    *,
    n_neighbors: int,
    min_train_support: int,
    train_indices: np.ndarray | None = None,
    evaluation_indices: np.ndarray | None = None,
    embargo: float = 0.0,
    train_window_support: np.ndarray | None = None,
    evaluation_window_support: np.ndarray | None = None,
):
    train = np.asarray(
        FROZEN_TRAIN_INDICES if train_indices is None else train_indices,
        dtype=np.int64,
    )
    evaluation = np.asarray(
        FROZEN_EVALUATION_INDICES if evaluation_indices is None else evaluation_indices,
        dtype=np.int64,
    )
    return crossfit_local_chart_b(
        trajectory,
        time,
        train,
        evaluation,
        estimator=estimator,
        n_neighbors=n_neighbors,
        min_train_support=min_train_support,
        embargo=embargo,
        train_window_support=train_window_support,
        evaluation_window_support=evaluation_window_support,
    )


def _equivariance_audit(
    trajectory: np.ndarray,
    time: np.ndarray,
    truth: np.ndarray,
    transform_name: str,
    transform: np.ndarray,
    *,
    n_neighbors: int,
    min_train_support: int,
    identity_tolerance: float,
) -> dict[str, Any]:
    transformed_trajectory = _transform_rows(trajectory, transform)
    transformed_truth = _transform_rows(truth, transform)
    transformed_matrix = transform @ FROZEN_A @ np.linalg.inv(transform)
    oracle_from_transformed_coordinates = _truth_velocity(
        transformed_trajectory[np.asarray(FROZEN_EVALUATION_INDICES)],
        transformed_matrix,
    )
    oracle_discrepancy = _max_abs(oracle_from_transformed_coordinates - transformed_truth)

    estimators: dict[str, Any] = {}
    for estimator in ("local_mean", "local_linear"):
        original = _candidate(
            trajectory,
            time,
            estimator,
            n_neighbors=n_neighbors,
            min_train_support=min_train_support,
        )
        transformed = _candidate(
            transformed_trajectory,
            time,
            estimator,
            n_neighbors=n_neighbors,
            min_train_support=min_train_support,
        )
        expected = _transform_rows(original.b_hat, transform)
        discrepancy = _max_abs(transformed.b_hat - expected)
        base_neighbors = _nearest_indices(
            trajectory,
            np.asarray(FROZEN_TRAIN_INDICES),
            np.asarray(FROZEN_EVALUATION_INDICES),
            n_neighbors,
        )
        transformed_neighbors = _nearest_indices(
            transformed_trajectory,
            np.asarray(FROZEN_TRAIN_INDICES),
            np.asarray(FROZEN_EVALUATION_INDICES),
            n_neighbors,
        )
        estimators[estimator] = {
            "max_abs_estimator_discrepancy": discrepancy,
            "relative_estimator_discrepancy": _relative_error(transformed.b_hat, expected),
            "within_identity_tolerance": bool(discrepancy <= identity_tolerance),
            "truth_recovery_rmse_original": _rmse(original.b_hat - truth),
            "truth_recovery_rmse_transformed": _rmse(transformed.b_hat - transformed_truth),
            "neighbor_identity_unchanged": bool(base_neighbors == transformed_neighbors),
        }

    return {
        "map": transform_name,
        "matrix": transform.tolist(),
        "oracle_coordinate_identity": {
            "max_abs_discrepancy": oracle_discrepancy,
            "within_identity_tolerance": bool(oracle_discrepancy <= identity_tolerance),
            "interpretation": "truth-known transformed conditional velocity identity",
        },
        "estimators": estimators,
    }


def _effective_dimension(covariance: np.ndarray) -> float:
    matrix = np.asarray(covariance, dtype=float)
    trace = float(np.trace(matrix))
    denominator = float(np.trace(matrix @ matrix))
    return float(trace * trace / denominator) if denominator > 0.0 else float("nan")


def _alignment(b: np.ndarray, covariance: np.ndarray) -> float | None:
    """Return an unregularized chart alignment diagnostic.

    This deliberately omits an epsilon.  It is a mathematical CHART audit
    metric and is not the ingest production C1/A_bD alignment contract.
    """
    vector = np.asarray(b, dtype=float).reshape(-1)
    matrix = np.asarray(covariance, dtype=float)
    denominator = float(vector @ vector) * float(np.trace(matrix))
    if denominator <= 0.0 or not np.isfinite(denominator):
        return None
    return float(vector @ matrix @ vector / denominator)


def _attempt(
    label: str,
    operation: Callable[[], Any],
    *,
    expected_error: str,
) -> dict[str, Any]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            value = operation()
        except DriftContractError as error:
            return {
                "status": "refused",
                "error": str(error),
                "expected_error": expected_error,
                "contract_check": bool(expected_error in str(error)),
                "runtime_warnings": [str(item.message) for item in caught],
            }
    finite_output = True
    if hasattr(value, "b_hat"):
        finite_output = bool(np.isfinite(np.asarray(value.b_hat, dtype=float)).all())
    return {
        "status": "accepted" if finite_output else "accepted_nonfinite_output",
        "error": None,
        "expected_error": expected_error,
        "contract_check": False,
        "finite_output": finite_output,
        "runtime_warnings": [str(item.message) for item in caught],
        "case": label,
    }


def _failure_contract_audit(
    trajectory: np.ndarray,
    time: np.ndarray,
    *,
    n_neighbors: int,
    min_train_support: int,
) -> dict[str, Any]:
    train = np.asarray(FROZEN_TRAIN_INDICES, dtype=np.int64)
    evaluation = np.asarray(FROZEN_EVALUATION_INDICES, dtype=np.int64)
    cases: dict[str, Any] = {}

    irregular_time = time.copy()
    irregular_time[12] += 0.01
    cases["irregular_dt"] = _attempt(
        "irregular_dt",
        lambda: _candidate(
            trajectory,
            irregular_time,
            "local_mean",
            n_neighbors=n_neighbors,
            min_train_support=min_train_support,
        ),
        expected_error="irregular dt",
    )

    nonfinite_trajectory = trajectory.copy()
    nonfinite_trajectory[4, 1] = np.nan
    cases["nonfinite_input"] = _attempt(
        "nonfinite_input",
        lambda: _candidate(
            nonfinite_trajectory,
            time,
            "local_mean",
            n_neighbors=n_neighbors,
            min_train_support=min_train_support,
        ),
        expected_error="finite array",
    )

    cases["insufficient_support"] = _attempt(
        "insufficient_support",
        lambda: _candidate(
            trajectory,
            time,
            "local_mean",
            n_neighbors=n_neighbors,
            min_train_support=3,
            train_indices=np.asarray([0, 1]),
            evaluation_indices=np.asarray([64]),
        ),
        expected_error="insufficient training support",
    )

    rank_deficient = np.column_stack(
        (
            np.arange(FROZEN_N_POINTS, dtype=float),
            2.0 * np.arange(FROZEN_N_POINTS, dtype=float),
            -0.5 * np.arange(FROZEN_N_POINTS, dtype=float),
        )
    )
    cases["rank_deficient_local_linear"] = _attempt(
        "rank_deficient_local_linear",
        lambda: _candidate(
            rank_deficient,
            time,
            "local_linear",
            n_neighbors=n_neighbors,
            min_train_support=min_train_support,
        ),
        expected_error="insufficient local rank",
    )

    cases["increment_overlap"] = _attempt(
        "increment_overlap",
        lambda: _candidate(
            trajectory,
            time,
            "local_mean",
            n_neighbors=1,
            min_train_support=1,
            train_indices=np.asarray([0, 1]),
            evaluation_indices=np.asarray([1, 2]),
        ),
        expected_error="overlap",
    )

    cases["shared_endpoint"] = _attempt(
        "shared_endpoint",
        lambda: _candidate(
            trajectory,
            time,
            "local_mean",
            n_neighbors=1,
            min_train_support=1,
            train_indices=np.asarray([0]),
            evaluation_indices=np.asarray([1]),
            embargo=0.0,
        ),
        expected_error="embargo",
    )

    cases["raw_support_overlap"] = _attempt(
        "raw_support_overlap",
        lambda: _candidate(
            trajectory,
            time,
            "local_mean",
            n_neighbors=1,
            min_train_support=1,
            train_indices=np.asarray([5]),
            evaluation_indices=np.asarray([10]),
            train_window_support=np.asarray([[0.8, 1.4]]),
            evaluation_window_support=np.asarray([[1.4, 2.4]]),
        ),
        expected_error="embargo",
    )

    cases["positive_embargo"] = _attempt(
        "positive_embargo",
        lambda: _candidate(
            trajectory,
            time,
            "local_mean",
            n_neighbors=1,
            min_train_support=1,
            train_indices=np.asarray([0]),
            evaluation_indices=np.asarray([4]),
            embargo=0.7,
        ),
        expected_error="embargo",
    )

    # Non-contiguous selected increments are allowed when their temporal
    # supports remain disjoint.  The estimator does not bridge missing rows.
    gap_train = np.asarray([0, 2, 4, 6])
    gap_evaluation = np.asarray([64])
    try:
        gap_result = _candidate(
            trajectory,
            time,
            "local_mean",
            n_neighbors=4,
            min_train_support=3,
            train_indices=gap_train,
            evaluation_indices=gap_evaluation,
            embargo=0.0,
        )
        cases["noncontiguous_gap"] = {
            "status": "accepted",
            "contract_check": bool(np.isfinite(gap_result.b_hat).all()),
            "interpretation": "selected increments remain explicit; no missingness bridging",
            "train_increment_indices": gap_train.tolist(),
            "evaluation_increment_indices": gap_evaluation.tolist(),
        }
    except DriftContractError as error:
        cases["noncontiguous_gap"] = {
            "status": "refused",
            "contract_check": False,
            "error": str(error),
            "interpretation": "unexpected refusal for separated explicit supports",
        }

    huge = np.full_like(trajectory, 1.0e308)
    huge[1::2] = -1.0e308
    cases["finite_huge_overflow_guard"] = _attempt(
        "finite_huge_overflow_guard",
        lambda: _candidate(
            huge,
            time,
            "local_mean",
            n_neighbors=n_neighbors,
            min_train_support=min_train_support,
        ),
        expected_error="overflow",
    )
    return cases


def _evaluation_target_independence(
    trajectory: np.ndarray,
    time: np.ndarray,
    *,
    n_neighbors: int,
    min_train_support: int,
    identity_tolerance: float,
) -> dict[str, Any]:
    changed = trajectory.copy()
    # Use separated evaluation increments so changing x[i+1] cannot also
    # change x[j] for another evaluation current state.
    evaluation = np.asarray(FROZEN_EVALUATION_INDICES[::2], dtype=np.int64)
    changed[evaluation + 1] += np.array([100.0, -75.0, 50.0])
    output: dict[str, Any] = {}
    for estimator in ("local_mean", "local_linear"):
        first = _candidate(
            trajectory,
            time,
            estimator,
            n_neighbors=n_neighbors,
            min_train_support=min_train_support,
            evaluation_indices=evaluation,
        )
        second = _candidate(
            changed,
            time,
            estimator,
            n_neighbors=n_neighbors,
            min_train_support=min_train_support,
            evaluation_indices=evaluation,
        )
        discrepancy = _max_abs(first.b_hat - second.b_hat)
        output[estimator] = {
            "max_abs_prediction_change": discrepancy,
            "within_identity_tolerance": bool(discrepancy <= identity_tolerance),
            "interpretation": "evaluation targets are excluded from cross-fit fitting",
        }
    return output


def _projection_information_loss() -> dict[str, Any]:
    """Construct the truth-known 3D-to-2D hidden-coordinate counterexample."""
    projection = np.asarray([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    current = np.asarray([[0.0, 0.0, 1.0], [0.0, 0.0, -1.0]])
    velocity = np.asarray([[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]])
    future = current + FROZEN_DT * velocity
    projected_current = _transform_rows(current, projection)
    projected_future = _transform_rows(future, projection)
    return {
        "classification": "projection_information_loss",
        "failed_coordinate_invariance": False,
        "projection_matrix": projection.tolist(),
        "same_projected_current": bool(np.array_equal(projected_current[0], projected_current[1])),
        "projected_expected_future_equal": bool(np.array_equal(projected_future[0], projected_future[1])),
        "projected_current": projected_current.tolist(),
        "projected_expected_future": projected_future.tolist(),
        "hidden_coordinate_values": current[:, 2].tolist(),
        "interpretation": "equal projected present does not identify the projected future when a hidden coordinate drives it",
    }


def run_chart_benchmark(
    *,
    seed: int = FROZEN_SEED,
    n_neighbors: int = FROZEN_N_NEIGHBORS,
    min_train_support: int = FROZEN_MIN_TRAIN_SUPPORT,
    identity_tolerance: float = FROZEN_IDENTITY_TOLERANCE,
) -> dict[str, Any]:
    """Run the bounded CHART mathematical audit and return a JSON-safe dict."""
    if int(n_neighbors) < 1 or int(min_train_support) < 1:
        raise ValueError("n_neighbors and min_train_support must be positive")
    if not np.isfinite(identity_tolerance) or identity_tolerance < 0:
        raise ValueError("identity_tolerance must be finite and non-negative")

    numeric_spec = _spec(
        seed=seed,
        n_neighbors=n_neighbors,
        min_train_support=min_train_support,
        identity_tolerance=identity_tolerance,
    )
    spec_hash = _sha256_text(_canonical_json(numeric_spec))
    trajectory, time = _trajectory(seed)
    evaluation = trajectory[np.asarray(FROZEN_EVALUATION_INDICES)]
    truth = _truth_velocity(evaluation)

    maps = {
        "orthogonal": FROZEN_ORTHOGONAL,
        "isotropic": FROZEN_ISOTROPIC_SCALE * np.eye(3),
        "anisotropic": FROZEN_ANISOTROPIC,
    }
    map_audits = {
        name: _equivariance_audit(
            trajectory,
            time,
            truth,
            name,
            transform,
            n_neighbors=n_neighbors,
            min_train_support=min_train_support,
            identity_tolerance=identity_tolerance,
        )
        for name, transform in maps.items()
    }

    base_truth_vector = truth.mean(axis=0)
    covariance_audits: dict[str, Any] = {}
    for name, transform in maps.items():
        # Construct the observed transformed covariance through a transformed
        # Cholesky factor.  Keeping this pathway separate from the analytic
        # expression makes the audit sensitive to a mistaken implementation
        # of the covariance transform (rather than comparing an expression
        # with itself).
        base_cholesky = np.linalg.cholesky(FROZEN_Q)
        transformed_factor = transform @ base_cholesky
        transformed_covariance = transformed_factor @ transformed_factor.T
        expected_covariance = transform @ FROZEN_Q @ transform.T
        discrepancy = _max_abs(transformed_covariance - expected_covariance)
        covariance_audits[name] = {
            "construction": "L_prime = H @ chol(Q); actual = L_prime @ L_prime.T",
            "transformed_factor": transformed_factor.tolist(),
            "actual_covariance": transformed_covariance.tolist(),
            "expected_covariance": expected_covariance.tolist(),
            "max_abs_covariance_transform_discrepancy": discrepancy,
            "within_identity_tolerance": bool(discrepancy <= identity_tolerance),
            # Keep Q_prime as a compatibility alias for consumers of the
            # preliminary audit output; it is the expected analytical value.
            "Q_prime": expected_covariance.tolist(),
            "formula": "Q_prime = H Q H.T",
        }

    failure_contracts = _failure_contract_audit(
        trajectory,
        time,
        n_neighbors=n_neighbors,
        min_train_support=min_train_support,
    )
    unexpected_contracts = [
        name for name, audit in failure_contracts.items()
        if not bool(audit.get("contract_check", False))
    ]
    contract_status = (
        "all_expected_contracts_refused"
        if not unexpected_contracts
        else "unexpected_contract_behavior"
    )

    anisotropic_covariance = FROZEN_ANISOTROPIC @ FROZEN_Q @ FROZEN_ANISOTROPIC.T
    anisotropic_truth_vector = _transform_rows(base_truth_vector[None, :], FROZEN_ANISOTROPIC)[0]
    original_alignment = _alignment(base_truth_vector, FROZEN_Q)
    anisotropic_alignment = _alignment(anisotropic_truth_vector, anisotropic_covariance)
    original_effective_dimension = _effective_dimension(FROZEN_Q)
    anisotropic_effective_dimension = _effective_dimension(anisotropic_covariance)
    anisotropic_estimators = map_audits["anisotropic"]["estimators"]

    return {
        "schema_version": "nmd_analysis.chart_benchmark.v1",
        "benchmark_status": "audit_complete",
        "purpose": "mathematical_chart_audit_only",
        "scientific_qualification": "not_assessed",
        "claim_status": "no_biological_claim",
        "m3_gate": "not_applicable",
        "canonical_chart": {
            "mnps_3d": ["m", "d", "e"],
            "coords_9d": ["m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m"],
            "chart_replacement": False,
        },
        "numeric_spec": numeric_spec,
        "numeric_spec_sha256": spec_hash,
        "provenance": _provenance(),
        "truth": {
            "model": "stable_linear_gaussian_discrete_dynamics",
            "A": FROZEN_A.tolist(),
            "Q_simulation_innovation_covariance": FROZEN_Q.tolist(),
            "dt": float(FROZEN_DT),
            "conditional_velocity": "(A-I)x/dt",
            "trajectory_shape": list(trajectory.shape),
            "time_range_sec": [float(time[0]), float(time[-1])],
        },
        "coordinate_maps": map_audits,
        "covariance_transform": covariance_audits,
        "anisotropic_scaling": {
            "euclidean_neighbor_estimator_sensitivity": {
                estimator: {
                    "max_abs_discrepancy": values["max_abs_estimator_discrepancy"],
                    "neighbor_identity_unchanged": values["neighbor_identity_unchanged"],
                    "interpretation": "expected finite-sample sensitivity of Euclidean neighbor selection",
                }
                for estimator, values in anisotropic_estimators.items()
            },
            "oracle_coordinate_identity": map_audits["anisotropic"]["oracle_coordinate_identity"],
            "alignment": {
                "metric_name": "unregularized_chart_alignment_diagnostic",
                "formula": "b.T Q b / ((b.T b) trace(Q))",
                "regularization": "none",
                "not_production_C1_alignment": True,
                "original": original_alignment,
                "anisotropically_transformed": anisotropic_alignment,
                "absolute_difference": (
                    None
                    if original_alignment is None or anisotropic_alignment is None
                    else abs(original_alignment - anisotropic_alignment)
                ),
                "invariance_expected": False,
            },
            "effective_dimension": {
                "formula": "trace(Q)^2 / trace(Q Q)",
                "original": original_effective_dimension,
                "anisotropically_transformed": anisotropic_effective_dimension,
                "absolute_difference": abs(original_effective_dimension - anisotropic_effective_dimension),
                "invariance_expected": False,
            },
        },
        "projection_information_loss": _projection_information_loss(),
        "evaluation_target_independence": _evaluation_target_independence(
            trajectory,
            time,
            n_neighbors=n_neighbors,
            min_train_support=min_train_support,
            identity_tolerance=identity_tolerance,
        ),
        "failure_contracts": failure_contracts,
        "contract_failure_count": len(unexpected_contracts),
        "contract_status": contract_status,
        "unexpected_contracts": unexpected_contracts,
        "discrepancy_policy": {
            "anisotropic_neighbor_discrepancy": "neutral_metric_sensitivity",
            "projection_counterexample": "information_loss_not_coordinate_failure",
            "undefined_or_unsupported": "retain status/reason; never replace with zero",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="write the JSON audit to this path; stdout is used when omitted",
    )
    args = parser.parse_args(argv)
    result = run_chart_benchmark()
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through the CLI
    raise SystemExit(main())


__all__ = [
    "FROZEN_A",
    "FROZEN_ANISOTROPIC",
    "FROZEN_DT",
    "FROZEN_EVALUATION_INDICES",
    "FROZEN_IDENTITY_TOLERANCE",
    "FROZEN_ISOTROPIC_SCALE",
    "FROZEN_MIN_TRAIN_SUPPORT",
    "FROZEN_N_NEIGHBORS",
    "FROZEN_N_POINTS",
    "FROZEN_ORTHOGONAL",
    "FROZEN_Q",
    "FROZEN_SEED",
    "FROZEN_TRAIN_INDICES",
    "run_chart_benchmark",
]
