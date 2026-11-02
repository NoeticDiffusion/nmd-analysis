"""TRANS-0B2b control truth and independent oblique PDE reference.

The control arm simulates the complete two-dimensional OU process and applies
the horizontal target rule only after each full-state grid update.  Paths stop
at their first observed target.  An unresolved path is advanced to its
declared horizon and has an endpoint record; a stopped path has no terminal
record.  This deliberately keeps first-hit evidence separate from terminal
occupancy.

The PDE arm is independent of the path simulator.  It uses a rectangular
operator in ``(r,s)`` coordinates with first-order upwind drift and a wide
axis/anti-diagonal jump stencil for the mixed diffusion.  The declared mesh
family keeps those jump rates nonnegative.  The implementation reports
generator rates, residuals, boundary residuals, range, mesh, transformed
coefficients, and solver metadata for later review.
"""

from __future__ import annotations

import hashlib
import json
import platform
from functools import lru_cache
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.linalg import expm
from scipy.special import erfi
from scipy.sparse import csr_matrix, lil_matrix
from scipy.sparse.linalg import spsolve
from scipy.stats import beta


SCHEMA_VERSION = "nmd_analysis.trans_0b2b.v1"
PROTOCOL_VERSION = "ndt_trans_0b2b_20260908.v1"
STAGE = "TRANS-0B2b"
CONTROL_ROLE = "control_truth"
PDE_ROLE = "pde_reference"
ROLE = CONTROL_ROLE
ROOT_ENTROPY = 2_026_090_801
STAGE_INDEX = 1

J = np.asarray([[-1.0, 3.0], [0.0, -2.0]], dtype=float)
Q = np.diag([0.04, 0.40]).astype(float)
T = 32.0
HORIZON_GRID = (16.0, 32.0)
DT_GRID = (1.0 / 256.0, 1.0 / 512.0)
ENGINES = ("em_endpoint", "exact_ou_grid")
STARTS = np.asarray([[0.6, 0.0], [0.0, 0.6]], dtype=float)
START_NAMES = ("x_axis", "y_axis")
CONTROL_DIRECTION = np.asarray([0.0, 1.0], dtype=float)
CONTROL_THRESHOLD = 0.75
TARGET_DIRECTION = CONTROL_DIRECTION
TARGET_THRESHOLD = CONTROL_THRESHOLD
A = "v.T @ x <= -a (inclusive)"
B = "v.T @ x >= a (inclusive)"
N_REPS = 4
N_PATHS_PER_CELL = 500
MAX_STATE_STEP_UPDATES = 300_000_000
DECLARED_STATE_STEP_UPDATES = 294_912_000
CP_ALPHA = 0.025
CONTROL_GATE_ALPHA = 0.05 / 8.0

# The orthonormal columns are u and w.  These are the coordinates for the
# independent oblique PDE arm, not the horizontal control projection.
OBLIQUE_DIRECTION = np.asarray([1.0, 1.0], dtype=float) / np.sqrt(2.0)
TRANSVERSE_DIRECTION = np.asarray([1.0, -1.0], dtype=float) / np.sqrt(2.0)
TRANSFORM_BASIS = np.column_stack((OBLIQUE_DIRECTION, TRANSVERSE_DIRECTION))
TRANSFORMED_J = TRANSFORM_BASIS.T @ J @ TRANSFORM_BASIS
TRANSFORMED_Q = TRANSFORM_BASIS.T @ Q @ TRANSFORM_BASIS
PDE_R_GRID = (3.0, 4.0, 5.0, 6.0)
PDE_T_GRID = (1.0, 4.0, 16.0)
PDE_DT_GRID = (1.0 / 256.0, 1.0 / 512.0, 1.0 / 1024.0)
# Each level keeps h_r/h_s close to one, as required by the wide-stencil rates
# below.  The old 0B2a mesh ratios are intentionally absent.
PDE_MESH_GRID = {
    "3": ((67, 265), (97, 385), (127, 505)),
    "4": ((67, 353), (97, 513), (127, 673)),
    "5": ((67, 441), (97, 641), (127, 841)),
    "6": ((67, 529), (97, 769), (127, 1009)),
}
PDE_SPATIAL_NODE_CAP = 1_000_000
PDE_SOLVER_TOL = 1.0e-12

FIRST_LABELS = ("A", "B", "unresolved")
ENDPOINT_LABELS = ("A", "B", "U", "no_endpoint_absorbed")
TERMINAL_LABELS = ENDPOINT_LABELS
_FIRST_CODE = {"A": 0, "B": 1, "unresolved": -1}


def _plain(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [_plain(item) for item in value.tolist()]
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        if not np.isfinite(number):
            raise ValueError("cannot serialize a nonfinite value")
        return number
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if value is None or isinstance(value, str):
        return value
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def _canonical_json(value: Any) -> bytes:
    return json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_array(value: np.ndarray) -> str:
    return _sha256_bytes(np.ascontiguousarray(value).tobytes(order="C"))


def _integer(value: Any, name: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer")
    result = int(value)
    if result < minimum or (maximum is not None and result > maximum):
        bound = f" in [{minimum}, {maximum}]" if maximum is not None else f" >= {minimum}"
        raise ValueError(f"{name} must be an integer{bound}")
    return result


def _finite_float(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be finite")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not np.isfinite(result) or (positive and result <= 0.0):
        raise ValueError(f"{name} must be finite" + (" and positive" if positive else ""))
    return result


def _validate_start(start: Sequence[float] | np.ndarray) -> np.ndarray:
    value = np.asarray(start, dtype=float)
    if value.shape != (2,) or not np.isfinite(value).all():
        raise ValueError("start must be a finite two-dimensional vector")
    return value.copy()


def _grid_value(value: Any, name: str, grid: Sequence[float]) -> float:
    number = _finite_float(value, name, positive=True)
    for candidate in grid:
        if np.isclose(number, candidate, rtol=0.0, atol=1.0e-15):
            return float(candidate)
    raise ValueError(f"{name} must be one of the frozen grid values {tuple(grid)}")


def _grid_steps(dt: float, horizon: float) -> int:
    ratio = horizon / dt
    steps = int(round(ratio))
    if steps < 1 or not np.isclose(ratio, steps, rtol=0.0, atol=1.0e-10):
        raise ValueError("horizon/dt must be a positive integer")
    return steps


def _validate_engine(engine: Any) -> str:
    if not isinstance(engine, str) or engine not in ENGINES:
        raise ValueError(f"engine must be one of {ENGINES}")
    return engine


def _validate_index(value: Any, name: str, size: int) -> int:
    return _integer(value, name, minimum=0, maximum=size - 1)


def build_spec() -> dict[str, Any]:
    """Return the coordinator-freezable 0B2b specification."""

    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "experiment": STAGE,
        "stage": STAGE,
        "role": CONTROL_ROLE,
        "roles": {"control": CONTROL_ROLE, "pde": PDE_ROLE},
        "J": J.tolist(),
        "Q": Q.tolist(),
        "starts": STARTS.tolist(),
        "start_names": list(START_NAMES),
        "control": {
            "direction": CONTROL_DIRECTION.tolist(),
            "threshold": CONTROL_THRESHOLD,
            "A": A,
            "B": B,
            "analytic": "integral[-a,y] exp(5*s^2) ds / integral[-a,a] exp(5*s^2) ds",
        },
        "engines": list(ENGINES),
        "dt_grid": list(DT_GRID),
        "horizon_grid": list(HORIZON_GRID),
        "n_starts": len(STARTS),
        "n_reps": N_REPS,
        "n_paths_per_cell": N_PATHS_PER_CELL,
        "expected_cells": expected_primary_cells(),
        "max_state_step_updates": MAX_STATE_STEP_UPDATES,
        "declared_worst_case_state_step_updates": DECLARED_STATE_STEP_UPDATES,
        "counts_order": {
            "first_hit": list(FIRST_LABELS),
            "endpoint": list(ENDPOINT_LABELS),
        },
        "semantics": {
            "state_dimension": 2,
            "first_hit": "endpoint-observed earliest inclusive A/B target at t=0 or grid endpoint",
            "unresolved": "no endpoint target observed by the declared horizon",
            "stopping": "a resolved path stops at its first observed target and is not advanced or assigned a terminal label",
            "endpoint": "only unresolved paths receive an endpoint state/category at T",
            "missed_crossings": "between-grid crossings are not corrected",
            "continuous_time_truth": False,
            "committor_truth": "analytic eventual control only; finite-grid paths are a bounded check",
        },
        "engines_definition": {
            "em_endpoint": "x_next=x+Jx*dt+L*z*sqrt(dt), LL.T=Q; full-state endpoint Euler-Maruyama",
            "exact_ou_grid": "x_next=expm(J*dt)@x+L_dt*z; covariance integral_0^dt expm(Js)Qexpm(J.Ts) ds",
        },
        "sampling": {
            "seed_entropy": [ROOT_ENTROPY, STAGE_INDEX, "engine_index", "rep", "start_index"],
            "child_spawn_key": ["horizon_index", "dt_index"],
            "seed_contract": "SeedSequence([2026090801, 1, engine_index, rep, start_index], spawn_key=(horizon_index, dt_index))",
            "rng": "numpy.random.default_rng with PCG64",
            "paired_refinement": {
                "em": "coarse Brownian increment is normalized sum of the two fine increments and coarse drift uses coarse state",
                "exact_ou": "coarse noise is Phi_h L_h z_1 + L_h z_2, with Phi_h=expm(J*h)",
                "primary_cell_claim": False,
            },
        },
        "artifacts": {
            "path_format": "gzip JSONL; one row per path; no padding or missing rows",
            "path_key_fields": [
                "stage", "role", "engine", "engine_index", "rep", "start_index", "horizon_index", "dt_index",
                "dt", "horizon", "path_id", "local_path_index", "seed_tuple", "seed_spawn_key",
            ],
            "checksums": "sha256 of float64 C-order first-hit/endpoint state bytes where present",
            "coupling": "coupling.json records the primary unpaired declaration; helper exposes validated paired refinement",
        },
        "pde": {
            "role": PDE_ROLE,
            "coordinates": "r=u.T@x, s=w.T@x; u=(1,1)/sqrt(2), w=(1,-1)/sqrt(2)",
            "transformed_drift": TRANSFORMED_J.tolist(),
            "transformed_diffusion": TRANSFORMED_Q.tolist(),
            "operator": "-s*q_r + (2*r-3*s)*q_s + 0.11*q_rr - 0.18*q_rs + 0.11*q_ss",
            "R_grid": list(PDE_R_GRID),
            "mesh_grid": {key: [list(item) for item in value] for key, value in PDE_MESH_GRID.items()},
            "spatial_node_cap": PDE_SPATIAL_NODE_CAP,
            "artificial_boundary": "homogeneous numerical Neumann at s=+-R; fixed-side 0/1 stress runs",
            "stencil": "first-order upwind drift plus axis/anti-diagonal wide jump generator",
            "monotone_generator_claim": True,
            "comparison_principle": "finite-grid generator with nonnegative off-diagonal jump rates and Dirichlet/Neumann constraints",
            "method_status": "NUMERICAL_REFERENCE_CANDIDATE",
            "parabolic_T_grid": list(PDE_T_GRID),
            "parabolic_dt_grid": list(PDE_DT_GRID),
            "solver_tolerance": PDE_SOLVER_TOL,
        },
        "validation": {
            "cp_censor_bracket_alpha": CP_ALPHA,
            "control_gate_alpha": CONTROL_GATE_ALPHA,
            "control_gate": "each pooled (engine,start) cell at T=32,dt=1/512 contains analytic q and width <=0.08",
            "pde_gate": "method-limited unless monotone/convergence/boundary/parabolic checks independently pass",
        },
    }


def spec_hash(spec: Mapping[str, Any] | None = None) -> str:
    return _sha256_bytes(_canonical_json(build_spec() if spec is None else spec))


def seed_for_cell(
    engine_index: int,
    rep: int,
    start_index: int,
    horizon_index: int,
    dt_index: int,
) -> tuple[np.random.SeedSequence, list[int], list[int]]:
    """Return the exact namespace stream for one frozen control cell."""

    engine_i = _validate_index(engine_index, "engine_index", len(ENGINES))
    rep_i = _validate_index(rep, "rep", N_REPS)
    start_i = _validate_index(start_index, "start_index", len(STARTS))
    horizon_i = _validate_index(horizon_index, "horizon_index", len(HORIZON_GRID))
    dt_i = _validate_index(dt_index, "dt_index", len(DT_GRID))
    seed_tuple = [ROOT_ENTROPY, STAGE_INDEX, engine_i, rep_i, start_i]
    spawn_key = [horizon_i, dt_i]
    return np.random.SeedSequence(seed_tuple, spawn_key=tuple(spawn_key)), seed_tuple, spawn_key


def _validate_seed(seed: int | np.random.SeedSequence) -> int | np.random.SeedSequence:
    if isinstance(seed, (bool, np.bool_)):
        raise ValueError("seed must be an integer or SeedSequence")
    if isinstance(seed, (int, np.integer)):
        if int(seed) < 0:
            raise ValueError("seed integer must be nonnegative")
        return int(seed)
    if not isinstance(seed, np.random.SeedSequence):
        raise ValueError("seed must be an integer or SeedSequence")
    return seed


def _uses_primary_namespace(seed: int | np.random.SeedSequence) -> bool:
    if isinstance(seed, (int, np.integer)):
        return int(seed) == ROOT_ENTROPY
    entropy = seed.entropy
    if isinstance(entropy, np.ndarray):
        entropy = entropy.tolist()
    if isinstance(entropy, (list, tuple)):
        return bool(entropy) and int(entropy[0]) == ROOT_ENTROPY
    try:
        return int(entropy) == ROOT_ENTROPY
    except (TypeError, ValueError):
        return False


def _seed_metadata(seed: int | np.random.SeedSequence) -> dict[str, Any]:
    if isinstance(seed, np.random.SeedSequence):
        entropy = seed.entropy
        if isinstance(entropy, np.ndarray):
            entropy = entropy.tolist()
        elif isinstance(entropy, tuple):
            entropy = list(entropy)
        return {
            "entropy": _plain(entropy),
            "spawn_key": list(seed.spawn_key),
            "pool_size": int(seed.pool_size),
            "bit_generator": "PCG64",
            "rng": "numpy.random.default_rng",
        }
    return {
        "entropy": int(seed),
        "spawn_key": [],
        "pool_size": None,
        "bit_generator": "PCG64",
        "rng": "numpy.random.default_rng",
    }


def _check_cell_metadata(
    seed: int | np.random.SeedSequence,
    *,
    engine_index: int | None,
    rep: int | None,
    start_index: int | None,
    horizon_index: int | None,
    dt_index: int | None,
    seed_tuple: Sequence[int] | None,
    seed_spawn_key: Sequence[int] | None,
    allow_primary: bool,
) -> None:
    if seed_tuple is not None:
        if len(seed_tuple) != 5 or any(isinstance(x, (bool, np.bool_)) or not isinstance(x, (int, np.integer)) for x in seed_tuple):
            raise ValueError("seed_tuple must contain five integer fields")
        expected = [ROOT_ENTROPY, STAGE_INDEX, engine_index, rep, start_index]
        if any(x is None for x in expected) or [int(x) for x in seed_tuple] != [int(x) for x in expected]:
            raise ValueError("seed_tuple does not match the cell identity")
    if seed_spawn_key is not None:
        if len(seed_spawn_key) != 2 or any(isinstance(x, (bool, np.bool_)) or not isinstance(x, (int, np.integer)) for x in seed_spawn_key):
            raise ValueError("seed_spawn_key must contain horizon_index and dt_index")
        expected_spawn = [horizon_index, dt_index]
        if any(x is None for x in expected_spawn) or [int(x) for x in seed_spawn_key] != [int(x) for x in expected_spawn]:
            raise ValueError("seed_spawn_key does not match the cell identity")
    if seed_tuple is not None or seed_spawn_key is not None:
        if not isinstance(seed, np.random.SeedSequence):
            raise ValueError("declared cell seed identity requires a SeedSequence")
        entropy = seed.entropy
        if isinstance(entropy, np.ndarray):
            entropy = entropy.tolist()
        elif isinstance(entropy, tuple):
            entropy = list(entropy)
        if seed_tuple is not None and list(entropy) != list(seed_tuple):
            raise ValueError("seed_tuple does not match actual SeedSequence entropy")
        if seed_spawn_key is not None and list(seed.spawn_key) != list(seed_spawn_key):
            raise ValueError("seed_spawn_key does not match actual SeedSequence spawn_key")
    if allow_primary and _uses_primary_namespace(seed) and (seed_tuple is None or seed_spawn_key is None):
        raise ValueError("primary draws require explicit seed_tuple and seed_spawn_key metadata")


def _validate_primary_permission(seed: int | np.random.SeedSequence, allow_primary: bool) -> None:
    if not isinstance(allow_primary, (bool, np.bool_)):
        raise ValueError("allow_primary must be boolean")
    if _uses_primary_namespace(seed) and not bool(allow_primary):
        raise RuntimeError("primary seed namespace is denied until the frozen runner explicitly enables it")


@lru_cache(maxsize=16)
def transition_coefficients(dt: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return exact OU ``Phi``, innovation covariance, and its Cholesky factor."""

    step = _grid_value(dt, "dt", DT_GRID)
    phi = expm(J * step)
    # Van Loan block exponential gives integral exp(Js)Qexp(J.Ts) ds.
    block = np.zeros((4, 4), dtype=float)
    block[:2, :2] = J
    block[:2, 2:] = Q
    block[2:, 2:] = -J.T
    van_loan = expm(block * step)
    covariance = van_loan[:2, 2:] @ phi.T
    covariance = 0.5 * (covariance + covariance.T)
    chol = np.linalg.cholesky(covariance)
    return phi, covariance, chol


def _step_state(state: np.ndarray, z: np.ndarray, *, engine: str, dt: float, chol_q: np.ndarray | None = None, phi: np.ndarray | None = None, chol_exact: np.ndarray | None = None) -> np.ndarray:
    if engine == "em_endpoint":
        assert chol_q is not None
        result = state + (state @ J.T) * dt + (z @ chol_q.T) * np.sqrt(dt)
    else:
        assert phi is not None and chol_exact is not None
        result = state @ phi.T + z @ chol_exact.T
    if not np.isfinite(result).all():
        raise FloatingPointError("nonfinite state generated")
    return result


def _control_codes(states: np.ndarray) -> np.ndarray:
    y = states[:, 1]
    code = np.full(states.shape[0], -1, dtype=np.int8)
    code[y <= -CONTROL_THRESHOLD] = 0
    code[y >= CONTROL_THRESHOLD] = 1
    return code


def classify_control_trajectory(states: np.ndarray, *, dt: float, horizon: float | None = None) -> dict[str, Any]:
    """Classify a complete full-state trajectory using inclusive control targets."""

    trajectory = np.asarray(states, dtype=float)
    if trajectory.ndim != 2 or trajectory.shape[1] != 2 or trajectory.shape[0] < 1 or not np.isfinite(trajectory).all():
        raise ValueError("states must have finite shape (n_steps+1,2)")
    step = _grid_value(dt, "dt", DT_GRID)
    if horizon is None:
        duration = float((trajectory.shape[0] - 1) * step)
    else:
        duration = _finite_float(horizon, "horizon", positive=False)
    if trajectory.shape[0] == 1:
        if duration != 0.0:
            raise ValueError("a one-state trajectory must have horizon zero")
    elif _grid_steps(step, duration) != trajectory.shape[0] - 1:
        raise ValueError("states length does not match horizon/dt")
    codes = _control_codes(trajectory)
    hit = np.flatnonzero(codes >= 0)
    if hit.size:
        index = int(hit[0])
        label = "A" if int(codes[index]) == 0 else "B"
        first_time: float | None = float(index * step)
        first_state: list[float] | None = trajectory[index].tolist()
    else:
        label = "unresolved"
        first_time = None
        first_state = None
    return {
        "first_label": label,
        "first_time": first_time,
        "first_hit_state": first_state,
        "n_steps": int(trajectory.shape[0] - 1),
        "dt": step,
        "horizon": duration,
    }


# Generic alias used by reviewers who treat the control projection as the
# target classifier for this stage.
classify_trajectory = classify_control_trajectory


def classify_endpoint_state(state: Sequence[float] | np.ndarray) -> str:
    value = _validate_start(state)
    y = float(value[1])
    if y <= -CONTROL_THRESHOLD:
        return "A"
    if y >= CONTROL_THRESHOLD:
        return "B"
    return "U"


def _cp_lower(successes: int, total: int, alpha: float) -> float:
    return 0.0 if successes == 0 else float(beta.ppf(alpha, successes, total - successes + 1))


def _cp_upper(successes: int, total: int, alpha: float) -> float:
    return 1.0 if successes == total else float(beta.ppf(1.0 - alpha, successes + 1, total - successes))


def censor_bracket(n_b: int, n_unresolved: int, n_total: int, *, alpha: float = CP_ALPHA) -> list[float]:
    total = _integer(n_total, "n_total", minimum=1)
    successes = _integer(n_b, "n_B", minimum=0)
    unresolved = _integer(n_unresolved, "n_unresolved", minimum=0)
    if successes + unresolved > total:
        raise ValueError("n_B+n_unresolved must not exceed n_total")
    tail = _finite_float(alpha, "alpha", positive=True)
    if tail >= 1.0:
        raise ValueError("alpha must be below one")
    return [_cp_lower(successes, total, tail), _cp_upper(successes + unresolved, total, tail)]


def _empty_summary_counts() -> dict[str, int]:
    return {label: 0 for label in ENDPOINT_LABELS}


def _seed_fields(seed: int | np.random.SeedSequence, seed_tuple: Sequence[int] | None, seed_spawn_key: Sequence[int] | None) -> tuple[dict[str, Any], list[int] | None, list[int] | None]:
    return _seed_metadata(seed), (list(seed_tuple) if seed_tuple is not None else None), (list(seed_spawn_key) if seed_spawn_key is not None else list(_seed_metadata(seed)["spawn_key"]))


def _summary_from_codes(
    *,
    first_codes: np.ndarray,
    endpoint_codes: np.ndarray,
    first_states: np.ndarray,
    endpoint_states: np.ndarray,
    initial: np.ndarray,
    engine: str,
    engine_index: int,
    rep: int,
    start_index: int,
    horizon_index: int,
    dt_index: int,
    dt: float,
    horizon: float,
    seed: int | np.random.SeedSequence,
    seed_tuple: Sequence[int] | None,
    seed_spawn_key: Sequence[int] | None,
) -> dict[str, Any]:
    n = int(first_codes.size)
    first_counts = {label: int(np.count_nonzero(first_codes == code)) for label, code in (("A", 0), ("B", 1), ("unresolved", -1))}
    endpoint_counts = _empty_summary_counts()
    endpoint_counts["A"] = int(np.count_nonzero(endpoint_codes == 0))
    endpoint_counts["B"] = int(np.count_nonzero(endpoint_codes == 1))
    endpoint_counts["U"] = int(np.count_nonzero(endpoint_codes == 2))
    endpoint_counts["no_endpoint_absorbed"] = int(np.count_nonzero(endpoint_codes == -2))
    joint = np.zeros((3, 4), dtype=np.int64)
    for first_code, endpoint_code in zip(first_codes, endpoint_codes):
        row = 0 if int(first_code) == 0 else 1 if int(first_code) == 1 else 2
        col = 0 if int(endpoint_code) == 0 else 1 if int(endpoint_code) == 1 else 2 if int(endpoint_code) == 2 else 3
        joint[row, col] += 1
    metadata, tuple_value, spawn_value = _seed_fields(seed, seed_tuple, seed_spawn_key)
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "role": CONTROL_ROLE,
        "engine": engine,
        "engine_index": engine_index,
        "rep": rep,
        "start_index": start_index,
        "horizon_index": horizon_index,
        "dt_index": dt_index,
        "start": initial.copy(),
        "dt": dt,
        "horizon": horizon,
        "n_steps": _grid_steps(dt, horizon),
        "n_total": n,
        "n_first_A": first_counts["A"],
        "n_first_B": first_counts["B"],
        "n_first_unresolved": first_counts["unresolved"],
        "first_hit_counts": first_counts,
        "endpoint_counts": endpoint_counts,
        "terminal_counts": endpoint_counts.copy(),
        "joint_counts": {"first_hit_rows": list(FIRST_LABELS), "endpoint_columns": list(ENDPOINT_LABELS), "values": joint},
        "unresolved_fraction": float(first_counts["unresolved"] / n),
        "p_B_observed": float(first_counts["B"] / n),
        "p_not_A_observed": float(1.0 - first_counts["A"] / n),
        "terminal_p_B": None,
        "censor_bracket_p_B": censor_bracket(first_counts["B"], first_counts["unresolved"], n),
        "first_hit_state_checksum": _sha256_array(first_states),
        "endpoint_state_checksum": _sha256_array(endpoint_states),
        "terminal_state_checksum": None,
        "seed": metadata,
        "seed_tuple": tuple_value,
        "seed_spawn_key": spawn_value,
        "rng_contract": "numpy.random.default_rng PCG64",
        "endpoint_source": "unresolved paths only; stopped paths have no endpoint or terminal label",
    }


def _run_with_innovations(
    start: np.ndarray,
    *,
    innovations: np.ndarray,
    engine: str,
    dt: float,
    horizon: float,
    engine_index: int,
    rep: int,
    start_index: int,
    horizon_index: int,
    dt_index: int,
    seed: int | np.random.SeedSequence,
    seed_tuple: Sequence[int] | None,
    seed_spawn_key: Sequence[int] | None,
    innovations_are_exact_noise: bool = False,
    return_path_rows: bool = True,
    return_audit_traces: bool = False,
) -> dict[str, Any]:
    count, n_steps, dimensions = innovations.shape
    if dimensions != 2 or n_steps != _grid_steps(dt, horizon):
        raise ValueError("innovations shape does not match cell grid")
    state = np.repeat(start[None, :], count, axis=0)
    first_codes = _control_codes(state)
    first_times = np.full(count, np.nan, dtype=float)
    first_states = np.full((count, 2), np.nan, dtype=float)
    endpoint_codes = np.full(count, -2, dtype=np.int8)
    endpoint_states = np.full((count, 2), np.nan, dtype=float)
    initial_hit = first_codes >= 0
    first_times[initial_hit] = 0.0
    first_states[initial_hit] = state[initial_hit]
    active = ~initial_hit
    trace_count = min(2, count)
    traces: list[list[list[float] | None]] = []
    if return_audit_traces:
        traces = [[start.tolist()] for _ in range(trace_count)]
    chol_q = np.linalg.cholesky(Q) if engine == "em_endpoint" else None
    phi, _, chol_exact = transition_coefficients(dt) if engine == "exact_ou_grid" else (None, None, None)
    for step_index in range(n_steps):
        active_before = active.copy()
        if np.any(active):
            active_indices = np.flatnonzero(active)
            if innovations_are_exact_noise:
                state[active_indices] = state[active_indices] @ phi.T + innovations[active_indices, step_index]
                if not np.isfinite(state[active_indices]).all():
                    raise FloatingPointError("nonfinite state generated")
            else:
                state[active_indices] = _step_state(
                    state[active_indices], innovations[active_indices, step_index], engine=engine, dt=dt,
                    chol_q=chol_q, phi=phi, chol_exact=chol_exact,
                )
            hit_codes = _control_codes(state[active_indices])
            hit = hit_codes >= 0
            if np.any(hit):
                indices = active_indices[hit]
                first_codes[indices] = hit_codes[hit]
                first_times[indices] = float((step_index + 1) * dt)
                first_states[indices] = state[indices]
                active[indices] = False
        if return_audit_traces:
            for local_index in range(trace_count):
                # Keep the observed hit endpoint in the trace.  A path that
                # was already stopped before this step contributes ``None``;
                # the step on which it first crosses remains finite so an
                # independent audit can recover the declared hit time/state.
                traces[local_index].append(
                    state[local_index].tolist() if active_before[local_index] else None
                )
    endpoint_indices = np.flatnonzero(active)
    if endpoint_indices.size:
        endpoint_states[endpoint_indices] = state[endpoint_indices]
        endpoint_codes[endpoint_indices] = np.asarray([0 if y <= -CONTROL_THRESHOLD else 1 if y >= CONTROL_THRESHOLD else 2 for y in state[endpoint_indices, 1]], dtype=np.int8)
    summary = _summary_from_codes(
        first_codes=first_codes, endpoint_codes=endpoint_codes, first_states=first_states, endpoint_states=endpoint_states,
        initial=start, engine=engine, engine_index=engine_index, rep=rep, start_index=start_index,
        horizon_index=horizon_index, dt_index=dt_index, dt=dt, horizon=horizon, seed=seed,
        seed_tuple=seed_tuple, seed_spawn_key=seed_spawn_key,
    )
    path_rows: list[dict[str, Any]] = []
    if return_path_rows:
        for local_index in range(count):
            first_code = int(first_codes[local_index])
            endpoint_code = int(endpoint_codes[local_index])
            path_id = f"{STAGE}|{CONTROL_ROLE}|{engine}|rep{rep}|start{start_index}|T{horizon_index}|dt{dt_index}|path{local_index:06d}"
            resolved = first_code >= 0
            path_rows.append({
                "schema_version": SCHEMA_VERSION, "stage": STAGE, "role": CONTROL_ROLE, "engine": engine,
                "engine_index": engine_index, "rep": rep, "start_index": start_index,
                "horizon_index": horizon_index, "dt_index": dt_index, "dt": dt, "horizon": horizon,
                "n_steps": n_steps, "path_id": path_id, "local_path_index": local_index,
                "seed_tuple": list(seed_tuple) if seed_tuple is not None else None,
                "seed_spawn_key": list(seed_spawn_key) if seed_spawn_key is not None else _seed_metadata(seed)["spawn_key"],
                "initial_state": start.tolist(),
                "first_label": "A" if first_code == 0 else "B" if first_code == 1 else "unresolved",
                "first_time": None if not resolved else float(first_times[local_index]),
                "first_hit_state": None if not resolved else first_states[local_index].tolist(),
                "endpoint_state": None if resolved else endpoint_states[local_index].tolist(),
                "endpoint_label": None if resolved else ENDPOINT_LABELS[endpoint_code],
                "terminal_state": None if resolved else endpoint_states[local_index].tolist(),
                "terminal_label": None if resolved else ENDPOINT_LABELS[endpoint_code],
                "endpoint_state_checksum": None if resolved else _sha256_array(endpoint_states[local_index]),
                "first_hit_state_checksum": None if not resolved else _sha256_array(first_states[local_index]),
                "terminal_source": "no terminal label for stopped path" if resolved else "unresolved endpoint at declared horizon",
            })
        summary["path_rows_checksum"] = _sha256_bytes(_canonical_json(path_rows))
        summary["path_rows"] = path_rows
    if return_audit_traces:
        summary["audit_traces"] = [
            {
                "local_path_index": index,
                "path_id": path_rows[index]["path_id"] if path_rows else f"trace-{index}",
                "states": traces[index],
                "trace_source": "full path until first hit; null after stopped path",
                "trace_checksum": _sha256_bytes(_canonical_json(traces[index])),
            }
            for index in range(trace_count)
        ]
    summary["first_hit_times"] = first_times
    summary["first_hit_states"] = first_states
    summary["endpoint_states"] = endpoint_states
    summary["endpoint_codes"] = endpoint_codes
    return summary


def simulate_control_cell(
    start: Sequence[float] | np.ndarray,
    *,
    n_paths: int,
    seed: int | np.random.SeedSequence,
    engine: str,
    dt: float,
    horizon: float,
    engine_index: int | None = None,
    rep: int | None = None,
    start_index: int | None = None,
    horizon_index: int | None = None,
    dt_index: int | None = None,
    seed_tuple: Sequence[int] | None = None,
    seed_spawn_key: Sequence[int] | None = None,
    return_path_rows: bool = True,
    return_audit_traces: bool = False,
    allow_primary: bool = False,
) -> dict[str, Any]:
    """Simulate one stopped-path control cell."""

    initial = _validate_start(start)
    count = _integer(n_paths, "n_paths", minimum=1, maximum=N_PATHS_PER_CELL)
    selected_engine = _validate_engine(engine)
    step = _grid_value(dt, "dt", DT_GRID)
    duration = _finite_float(horizon, "horizon", positive=True)
    if duration > T + 1.0e-10:
        raise ValueError("horizon must not exceed the frozen maximum horizon")
    n_steps = _grid_steps(step, duration)
    checked_seed = _validate_seed(seed)
    _validate_primary_permission(checked_seed, allow_primary)
    engine_i = ENGINES.index(selected_engine) if engine_index is None else _validate_index(engine_index, "engine_index", len(ENGINES))
    if engine_i != ENGINES.index(selected_engine):
        raise ValueError("engine_index does not match engine")
    rep_i = -1 if rep is None else _validate_index(rep, "rep", N_REPS)
    start_i = -1 if start_index is None else _validate_index(start_index, "start_index", len(STARTS))
    if start_i >= 0 and not np.array_equal(initial, STARTS[start_i]):
        raise ValueError("start does not match start_index")
    horizon_i = -1 if horizon_index is None else _validate_index(horizon_index, "horizon_index", len(HORIZON_GRID))
    if horizon_i >= 0 and not np.isclose(duration, HORIZON_GRID[horizon_i], rtol=0.0, atol=1.0e-12):
        raise ValueError("horizon does not match horizon_index")
    dt_i = -1 if dt_index is None else _validate_index(dt_index, "dt_index", len(DT_GRID))
    if dt_i >= 0 and not np.isclose(step, DT_GRID[dt_i], rtol=0.0, atol=1.0e-15):
        raise ValueError("dt does not match dt_index")
    _check_cell_metadata(
        checked_seed, engine_index=engine_i if engine_index is not None else None, rep=rep if rep is not None else None,
        start_index=start_index, horizon_index=horizon_index, dt_index=dt_index,
        seed_tuple=seed_tuple, seed_spawn_key=seed_spawn_key, allow_primary=bool(allow_primary),
    )
    rng = np.random.default_rng(checked_seed)
    innovations = rng.standard_normal((count, n_steps, 2))
    return _run_with_innovations(
        initial, innovations=innovations, engine=selected_engine, dt=step, horizon=duration,
        engine_index=engine_i, rep=rep_i, start_index=start_i, horizon_index=horizon_i, dt_index=dt_i,
        seed=checked_seed, seed_tuple=seed_tuple, seed_spawn_key=seed_spawn_key,
        return_path_rows=return_path_rows, return_audit_traces=return_audit_traces,
    )


simulate_first_hit = simulate_control_cell
simulate_control = simulate_control_cell


def _coupled_coarse_innovations(z_fine: np.ndarray, *, engine: str, fine_dt: float, coarse_dt: float) -> tuple[np.ndarray, dict[str, Any]]:
    ratio_float = coarse_dt / fine_dt
    ratio = int(round(ratio_float))
    if ratio < 2 or not np.isclose(ratio_float, ratio, rtol=0.0, atol=1.0e-12):
        raise ValueError("coarse_dt/fine_dt must be an integer ratio >=2")
    if z_fine.shape[1] % ratio:
        raise ValueError("fine innovation length must be divisible by coarse/fine ratio")
    n_paths, n_steps, _ = z_fine.shape
    coarse_steps = n_steps // ratio
    blocks = z_fine.reshape(n_paths, coarse_steps, ratio, 2)
    if engine == "em_endpoint":
        result = blocks.sum(axis=2) / np.sqrt(float(ratio))
        method = "normalized sum of fine Brownian standard normals"
    else:
        phi, _, chol = transition_coefficients(fine_dt)
        result = np.empty((n_paths, coarse_steps, 2), dtype=float)
        for coarse_index in range(coarse_steps):
            noise = np.zeros((n_paths, 2), dtype=float)
            for fine_index in range(ratio):
                fine_noise = blocks[:, coarse_index, fine_index] @ chol.T
                power = np.linalg.matrix_power(phi, ratio - 1 - fine_index)
                noise += fine_noise @ power.T
            result[:, coarse_index] = noise
        method = "Phi_h L_h z_1 + L_h z_2 semigroup noise recurrence"
    return result, {"valid": True, "engine": engine, "ratio": ratio, "method": method, "shared_parent_innovations": True}


def simulate_control_refinement(
    start: Sequence[float] | np.ndarray,
    *,
    n_paths: int,
    seed: int | np.random.SeedSequence,
    engine: str,
    fine_dt: float,
    coarse_dt: float,
    horizon: float,
    engine_index: int | None = None,
    rep: int | None = None,
    start_index: int | None = None,
    horizon_index: int | None = None,
    fine_dt_index: int | None = None,
    coarse_dt_index: int | None = None,
    seed_tuple: Sequence[int] | None = None,
    seed_spawn_key: Sequence[int] | None = None,
    allow_primary: bool = False,
) -> dict[str, Any]:
    """Simulate a validated fine/coarse pair from one parent innovation stream.

    This helper is for a paired refinement check and is not an additional
    primary sample.  Exact OU coarse noise is constructed from fine OU noises,
    while EM uses normalized sums of Brownian increments.
    """

    initial = _validate_start(start)
    count = _integer(n_paths, "n_paths", minimum=1, maximum=N_PATHS_PER_CELL)
    selected_engine = _validate_engine(engine)
    fine = _grid_value(fine_dt, "fine_dt", DT_GRID)
    coarse = _grid_value(coarse_dt, "coarse_dt", DT_GRID)
    duration = _finite_float(horizon, "horizon", positive=True)
    if duration > T + 1.0e-10:
        raise ValueError("horizon must not exceed the frozen maximum horizon")
    fine_steps = _grid_steps(fine, duration)
    coarse_steps = _grid_steps(coarse, duration)
    if fine >= coarse or fine_steps != coarse_steps * int(round(coarse / fine)):
        raise ValueError("fine_dt must be smaller than coarse_dt on a shared grid")
    checked_seed = _validate_seed(seed)
    _validate_primary_permission(checked_seed, allow_primary)
    engine_i = ENGINES.index(selected_engine) if engine_index is None else _validate_index(engine_index, "engine_index", len(ENGINES))
    if engine_i != ENGINES.index(selected_engine):
        raise ValueError("engine_index does not match engine")
    rep_i = -1 if rep is None else _validate_index(rep, "rep", N_REPS)
    start_i = -1 if start_index is None else _validate_index(start_index, "start_index", len(STARTS))
    horizon_i = -1 if horizon_index is None else _validate_index(horizon_index, "horizon_index", len(HORIZON_GRID))
    fine_i = DT_GRID.index(fine) if fine_dt_index is None else _validate_index(fine_dt_index, "fine_dt_index", len(DT_GRID))
    coarse_i = DT_GRID.index(coarse) if coarse_dt_index is None else _validate_index(coarse_dt_index, "coarse_dt_index", len(DT_GRID))
    rng = np.random.default_rng(checked_seed)
    z_fine = rng.standard_normal((count, fine_steps, 2))
    coarse_innovations, coupling = _coupled_coarse_innovations(z_fine, engine=selected_engine, fine_dt=fine, coarse_dt=coarse)
    fine_result = _run_with_innovations(
        initial, innovations=z_fine, engine=selected_engine, dt=fine, horizon=duration,
        engine_index=engine_i, rep=rep_i, start_index=start_i, horizon_index=horizon_i, dt_index=fine_i,
        seed=checked_seed, seed_tuple=seed_tuple, seed_spawn_key=seed_spawn_key,
        return_path_rows=True, return_audit_traces=False,
    )
    coarse_result = _run_with_innovations(
        initial, innovations=coarse_innovations, engine=selected_engine, dt=coarse, horizon=duration,
        engine_index=engine_i, rep=rep_i, start_index=start_i, horizon_index=horizon_i, dt_index=coarse_i,
        seed=checked_seed, seed_tuple=seed_tuple, seed_spawn_key=seed_spawn_key,
        innovations_are_exact_noise=(selected_engine == "exact_ou_grid"), return_path_rows=True, return_audit_traces=False,
    )
    coupling["fine_dt"] = fine
    coupling["coarse_dt"] = coarse
    coupling["fine_checksum"] = _sha256_array(z_fine)
    coupling["coarse_innovation_checksum"] = _sha256_array(coarse_innovations)
    coupling["claim_scope"] = "paired descriptive grid-method check only"
    return {"fine": fine_result, "coarse": coarse_result, "coupling": coupling}


def expected_primary_cells() -> int:
    return len(ENGINES) * N_REPS * len(STARTS) * len(HORIZON_GRID) * len(DT_GRID)


def expected_primary_updates(*, n_paths: int = N_PATHS_PER_CELL) -> int:
    count = _integer(n_paths, "n_paths", minimum=1, maximum=N_PATHS_PER_CELL)
    groups = len(ENGINES) * N_REPS * len(STARTS)
    return int(groups * count * sum(_grid_steps(dt, horizon) for horizon in HORIZON_GRID for dt in DT_GRID))


def validate_primary_budget(*, n_paths: int = N_PATHS_PER_CELL, max_updates: int = MAX_STATE_STEP_UPDATES) -> dict[str, int | bool]:
    cap = _integer(max_updates, "max_updates", minimum=1)
    updates = expected_primary_updates(n_paths=n_paths)
    if updates > cap:
        raise ValueError(f"prospective state-step cap exceeded: {updates} > {cap}")
    return {
        "n_cells": expected_primary_cells(), "n_paths_per_cell": int(n_paths),
        "estimated_state_step_updates": updates, "max_state_step_updates": cap, "within_cap": True,
    }


def runtime_metadata() -> dict[str, str]:
    return {"python": platform.python_version(), "numpy": np.__version__, "scipy": __import__("scipy").__version__, "rng": "numpy.random.default_rng PCG64"}


# ------------------------------ independent PDE arm ---------------------

def _validate_pde_mesh(R: float, n_r: int, n_s: int) -> tuple[float, int, int]:
    radius = _finite_float(R, "R", positive=True)
    nr = _integer(n_r, "n_r", minimum=5)
    ns = _integer(n_s, "n_s", minimum=5)
    if nr * ns > PDE_SPATIAL_NODE_CAP:
        raise ValueError("PDE mesh exceeds the spatial-node cap")
    return radius, nr, ns


def _pde_boundary_value(mode: str, side: str) -> float | None:
    if mode == "neumann":
        return None
    if mode == "fixed0":
        return 0.0
    if mode == "fixed1":
        return 1.0
    raise ValueError("artificial_boundary must be 'neumann', 'fixed0', or 'fixed1'")


def _pde_index(i: int, j: int, n_s: int) -> int:
    return (i - 1) * n_s + j


def _add_coeff(matrix: lil_matrix, row: int, i: int, j: int, n_r: int, n_s: int, coefficient: float, rhs: float, *, r_boundary_values: tuple[float, float]) -> float:
    if abs(coefficient) == 0.0:
        return rhs
    if i == 0:
        return rhs - coefficient * r_boundary_values[0]
    if i == n_r - 1:
        return rhs - coefficient * r_boundary_values[1]
    matrix[row, _pde_index(i, j, n_s)] += coefficient
    return rhs


def _assemble_pde_operator(R: float, n_r: int, n_s: int, artificial_boundary: str) -> dict[str, Any]:
    radius, nr, ns = _validate_pde_mesh(R, n_r, n_s)
    mode = str(artificial_boundary).lower()
    _pde_boundary_value(mode, "s")
    r_grid = np.linspace(-CONTROL_THRESHOLD, CONTROL_THRESHOLD, nr, dtype=float)
    s_grid = np.linspace(-radius, radius, ns, dtype=float)
    hr = float(r_grid[1] - r_grid[0])
    hs = float(s_grid[1] - s_grid[0])
    n_unknown = (nr - 2) * ns
    matrix = lil_matrix((n_unknown, n_unknown), dtype=float)
    boundary_rhs = np.zeros(n_unknown, dtype=float)
    interior_rows: list[int] = []
    constraint_rows: dict[int, float] = {}
    ar = float(0.5 * TRANSFORMED_Q[0, 0])
    ass = float(0.5 * TRANSFORMED_Q[1, 1])
    ars = float(TRANSFORMED_Q[0, 1])
    for i in range(1, nr - 1):
        r = float(r_grid[i])
        for j in range(ns):
            row = _pde_index(i, j, ns)
            if j in (0, ns - 1):
                artificial_value = _pde_boundary_value(mode, "s")
                if artificial_value is not None:
                    matrix[row, row] = 1.0
                    constraint_rows[row] = artificial_value
                else:
                    neighbor = _pde_index(i, 1 if j == 0 else ns - 2, ns)
                    matrix[row, row] = 1.0
                    matrix[row, neighbor] = -1.0
                    constraint_rows[row] = 0.0
                continue
            interior_rows.append(row)
            s = float(s_grid[j])
            # A diagonal pair with rate rho contributes
            # rho*(h_r^2 q_rr + h_s^2 q_ss - 2 h_r h_s q_rs).
            # The remaining coordinate diffusion rates are nonnegative when
            # 9/11 <= h_r/h_s <= 11/9, which is true for the declared mesh.
            cross_rate = abs(ars) / (2.0 * hr * hs)
            r_axis_rate = (ar - cross_rate * hr * hr) / (hr * hr)
            s_axis_rate = (ass - cross_rate * hs * hs) / (hs * hs)
            if r_axis_rate < -1.0e-12 or s_axis_rate < -1.0e-12:
                raise ValueError("mesh ratio cannot support the declared monotone wide stencil")
            rhs = 0.0
            jump_terms = (
                (i - 1, j, r_axis_rate), (i + 1, j, r_axis_rate),
                (i, j - 1, s_axis_rate), (i, j + 1, s_axis_rate),
                (i - 1, j + 1, cross_rate), (i + 1, j - 1, cross_rate),
            )
            total_rate = 2.0 * (r_axis_rate + s_axis_rate + cross_rate)
            rhs = _add_coeff(matrix, row, i, j, nr, ns, -total_rate, rhs, r_boundary_values=(0.0, 1.0))
            for ii, jj, coefficient in jump_terms:
                rhs = _add_coeff(matrix, row, ii, jj, nr, ns, coefficient, rhs, r_boundary_values=(0.0, 1.0))
            # Positive drift uses a forward difference and negative drift a
            # backward difference, giving nonnegative off-diagonal rates.
            br = -s
            bs = 2.0 * r - 3.0 * s
            if br >= 0.0:
                rhs = _add_coeff(matrix, row, i, j, nr, ns, -br / hr, rhs, r_boundary_values=(0.0, 1.0))
                rhs = _add_coeff(matrix, row, i + 1, j, nr, ns, br / hr, rhs, r_boundary_values=(0.0, 1.0))
            else:
                rhs = _add_coeff(matrix, row, i, j, nr, ns, br / hr, rhs, r_boundary_values=(0.0, 1.0))
                rhs = _add_coeff(matrix, row, i - 1, j, nr, ns, -br / hr, rhs, r_boundary_values=(0.0, 1.0))
            if bs >= 0.0:
                rhs = _add_coeff(matrix, row, i, j, nr, ns, -bs / hs, rhs, r_boundary_values=(0.0, 1.0))
                matrix[row, _pde_index(i, j + 1, ns)] += bs / hs
            else:
                rhs = _add_coeff(matrix, row, i, j, nr, ns, bs / hs, rhs, r_boundary_values=(0.0, 1.0))
                matrix[row, _pde_index(i, j - 1, ns)] += -bs / hs
            boundary_rhs[row] = rhs
    matrix_csr = csr_matrix(matrix)
    return {
        "R": radius, "n_r": nr, "n_s": ns, "r_grid": r_grid, "s_grid": s_grid,
        "h_r": hr, "h_s": hs, "matrix": matrix_csr, "boundary_rhs": boundary_rhs,
        "interior_rows": np.asarray(interior_rows, dtype=int), "constraint_rows": constraint_rows,
        "ar": ar, "ass": ass, "ars": ars, "monotone_generator": True,
    }


def _solution_grid(system: Mapping[str, Any], vector: np.ndarray) -> np.ndarray:
    grid = np.empty((int(system["n_r"]), int(system["n_s"])), dtype=float)
    grid[0, :] = 0.0
    grid[-1, :] = 1.0
    for i in range(1, int(system["n_r"]) - 1):
        for j in range(int(system["n_s"])):
            grid[i, j] = vector[_pde_index(i, j, int(system["n_s"]))]
    return grid


def _bilinear_values(grid: np.ndarray, r_grid: np.ndarray, s_grid: np.ndarray, points: np.ndarray) -> list[float]:
    values: list[float] = []
    for point in points:
        r, s = float(point[0]), float(point[1])
        if not (-CONTROL_THRESHOLD < r < CONTROL_THRESHOLD and s_grid[0] <= s <= s_grid[-1]):
            values.append(float("nan"))
            continue
        i = int(np.clip(np.searchsorted(r_grid, r) - 1, 0, len(r_grid) - 2))
        j = int(np.clip(np.searchsorted(s_grid, s) - 1, 0, len(s_grid) - 2))
        fr = (r - r_grid[i]) / (r_grid[i + 1] - r_grid[i])
        fs = (s - s_grid[j]) / (s_grid[j + 1] - s_grid[j])
        values.append(float((1 - fr) * (1 - fs) * grid[i, j] + fr * (1 - fs) * grid[i + 1, j] + (1 - fr) * fs * grid[i, j + 1] + fr * fs * grid[i + 1, j + 1]))
    return values


def _pde_vector(system: Mapping[str, Any], grid: np.ndarray) -> np.ndarray:
    ns = int(system["n_s"])
    return np.asarray([grid[i, j] for i in range(1, int(system["n_r"]) - 1) for j in range(ns)], dtype=float)


def _pde_diagnostics(system: Mapping[str, Any], grid: np.ndarray, artificial_boundary: str) -> dict[str, Any]:
    """Report residuals for the actual declared wide-jump stencil."""

    vector = _pde_vector(system, grid)
    rhs = np.asarray(system["boundary_rhs"], dtype=float).copy()
    for row, value in system["constraint_rows"].items():
        rhs[int(row)] = float(value)
    residual = np.asarray(system["matrix"] @ vector - rhs, dtype=float)
    interior_rows = np.asarray(system["interior_rows"], dtype=int)
    interior_residual = residual[interior_rows]
    max_residual = float(np.max(np.abs(interior_residual))) if interior_residual.size else 0.0
    target_residual = max(float(np.max(np.abs(grid[0, :]))), float(np.max(np.abs(grid[-1, :] - 1.0))))
    hr, hs = float(system["h_r"]), float(system["h_s"])
    if artificial_boundary == "neumann":
        boundary_residual = max(float(np.max(np.abs((grid[:, 1] - grid[:, 0]) / hs))), float(np.max(np.abs((grid[:, -1] - grid[:, -2]) / hs))))
    else:
        value = 0.0 if artificial_boundary == "fixed0" else 1.0
        boundary_residual = max(float(np.max(np.abs(grid[:, 0] - value))), float(np.max(np.abs(grid[:, -1] - value))))
    minimum, maximum = float(np.min(grid)), float(np.max(grid))
    return {
        "discrete_residual_max": max_residual,
        "max_scaled_residual": max_residual,
        "boundary_residual_max": max(target_residual, boundary_residual),
        "target_boundary_residual_max": target_residual,
        "artificial_boundary_residual_max": boundary_residual,
        "range": [minimum, maximum],
        "within_unit_interval": bool(minimum >= -1.0e-12 and maximum <= 1.0 + 1.0e-12),
    }


def solve_elliptic_reference(
    *,
    R: float = 5.0,
    n_r: int = 65,
    n_s: int | None = None,
    artificial_boundary: str = "neumann",
    solver_tol: float = PDE_SOLVER_TOL,
    include_stress_envelope: bool = False,
) -> dict[str, Any]:
    """Solve the finite-domain eventual oblique PDE diagnostic."""

    radius = _finite_float(R, "R", positive=True)
    if n_s is None:
        declared = PDE_MESH_GRID.get(str(int(radius)))
        n_s = declared[0][1] if declared else 257
    tolerance = _finite_float(solver_tol, "solver_tol", positive=True)
    system = _assemble_pde_operator(radius, n_r, n_s, artificial_boundary)
    rhs = np.asarray(system["boundary_rhs"], dtype=float)
    for row, value in system["constraint_rows"].items():
        rhs[row] = value
    vector = np.asarray(spsolve(system["matrix"], rhs), dtype=float)
    if not np.isfinite(vector).all():
        raise FloatingPointError("nonfinite elliptic solution")
    grid = _solution_grid(system, vector)
    diagnostics = _pde_diagnostics(system, grid, str(artificial_boundary).lower())
    transformed_starts = STARTS @ TRANSFORM_BASIS
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "role": PDE_ROLE,
        "problem": "elliptic_q_inf",
        "solution": grid,
        "values": grid,
        "r_grid": system["r_grid"],
        "s_grid": system["s_grid"],
        "start_coordinates_rs": transformed_starts,
        "start_values": _bilinear_values(grid, system["r_grid"], system["s_grid"], transformed_starts),
        "transformed_drift": TRANSFORMED_J,
        "transformed_diffusion": TRANSFORMED_Q,
        "operator": "-s*q_r + (2*r-3*s)*q_s + 0.11*q_rr - 0.18*q_rs + 0.11*q_ss",
        "domain": {"r": [-CONTROL_THRESHOLD, CONTROL_THRESHOLD], "s": [-radius, radius]},
        "mesh": {"n_r": int(n_r), "n_s": int(n_s), "h_r": system["h_r"], "h_s": system["h_s"], "nodes": int(n_r * n_s)},
        "boundary_condition": {"r=-a": 0.0, "r=+a": 1.0, "s": str(artificial_boundary).lower()},
        "cross_diffusion": "axis/anti-diagonal wide jump representation",
        "drift_discretization": "first-order upwind",
        "solver": "scipy.sparse.linalg.spsolve",
        "solver_tolerance": tolerance,
        "monotone_generator": True,
        "monotonicity_certificate": {"status": "DECLARED", "reason": "nonnegative axis and anti-diagonal jump rates on the declared mesh ratio family"},
        "method_status": "NUMERICAL_REFERENCE_CANDIDATE",
        **diagnostics,
    }
    if include_stress_envelope and str(artificial_boundary).lower() == "neumann":
        result["stress_envelope"] = {
            "fixed0": solve_elliptic_reference(R=radius, n_r=n_r, n_s=n_s, artificial_boundary="fixed0", solver_tol=tolerance, include_stress_envelope=False),
            "fixed1": solve_elliptic_reference(R=radius, n_r=n_r, n_s=n_s, artificial_boundary="fixed1", solver_tol=tolerance, include_stress_envelope=False),
            "comparison_envelope_claim": False,
        }
    return result


def solve_parabolic_reference(
    *,
    horizon: float = 1.0,
    dt_pde: float = 1.0 / 256.0,
    R: float = 5.0,
    n_r: int = 65,
    n_s: int | None = None,
    artificial_boundary: str = "neumann",
    solver_tol: float = PDE_SOLVER_TOL,
) -> dict[str, Any]:
    """Solve ``partial_T q_T = L q_T`` by implicit Euler in remaining time."""

    duration = _finite_float(horizon, "horizon", positive=True)
    if duration > max(PDE_T_GRID) + 1.0e-12:
        raise ValueError("parabolic horizon exceeds declared grid")
    step = _grid_value(dt_pde, "dt_pde", PDE_DT_GRID)
    n_steps = int(round(duration / step))
    if n_steps < 1 or not np.isclose(duration / step, n_steps, rtol=0.0, atol=1.0e-10):
        raise ValueError("horizon/dt_pde must be a positive integer")
    radius = _finite_float(R, "R", positive=True)
    if n_s is None:
        declared = PDE_MESH_GRID.get(str(int(radius)))
        n_s = declared[0][1] if declared else 257
    tolerance = _finite_float(solver_tol, "solver_tol", positive=True)
    system = _assemble_pde_operator(radius, n_r, n_s, artificial_boundary)
    base_matrix = system["matrix"].tolil(copy=True)
    interior_rows = set(int(row) for row in system["interior_rows"])
    parabolic_matrix = lil_matrix(base_matrix.shape, dtype=float)
    for row in range(base_matrix.shape[0]):
        if row in interior_rows:
            parabolic_matrix[row, :] = -base_matrix.getrow(row)
            parabolic_matrix[row, row] += 1.0 / step
        else:
            parabolic_matrix[row, :] = base_matrix.getrow(row)
    parabolic_matrix = csr_matrix(parabolic_matrix)
    values = np.zeros(base_matrix.shape[0], dtype=float)
    for row, boundary_value in system["constraint_rows"].items():
        values[int(row)] = float(boundary_value)
    old_values = values.copy()
    target_rhs_boundary = np.asarray(system["boundary_rhs"], dtype=float)
    for row, boundary_value in system["constraint_rows"].items():
        target_rhs_boundary[int(row)] = float(boundary_value)
    for _ in range(n_steps):
        rhs = values / step - target_rhs_boundary
        for row in system["constraint_rows"]:
            rhs[int(row)] = float(system["constraint_rows"][row])
        old_values = values
        values = np.asarray(spsolve(parabolic_matrix, rhs), dtype=float)
        if not np.isfinite(values).all():
            raise FloatingPointError("nonfinite parabolic solution")
    grid = _solution_grid(system, values)
    diagnostics = _pde_diagnostics(system, grid, str(artificial_boundary).lower())
    # The reported derivative uses the final implicit step and the same
    # spatial operator.  It is a diagnostic of the backward-parabolic solve.
    previous_grid = _solution_grid(system, old_values)
    dt_residual = (grid - previous_grid) / step
    time_derivative_max = float(np.max(np.abs(dt_residual[1:-1, 1:-1])))
    final_vector = _pde_vector(system, grid)
    l_vector = np.asarray(system["matrix"] @ final_vector - system["boundary_rhs"], dtype=float)
    interior_rows_array = np.asarray(system["interior_rows"], dtype=int)
    final_dt_vector = (values - old_values) / step
    parabolic_residual = float(np.max(np.abs(final_dt_vector[interior_rows_array] - l_vector[interior_rows_array]))) if interior_rows_array.size else 0.0
    transformed_starts = STARTS @ TRANSFORM_BASIS
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "role": PDE_ROLE,
        "problem": "parabolic_q_T",
        "solution": grid,
        "values": grid,
        "r_grid": system["r_grid"],
        "s_grid": system["s_grid"],
        "start_coordinates_rs": transformed_starts,
        "start_values": _bilinear_values(grid, system["r_grid"], system["s_grid"], transformed_starts),
        "transformed_drift": TRANSFORMED_J,
        "transformed_diffusion": TRANSFORMED_Q,
        "operator": "-s*q_r + (2*r-3*s)*q_s + 0.11*q_rr - 0.18*q_rs + 0.11*q_ss",
        "domain": {"r": [-CONTROL_THRESHOLD, CONTROL_THRESHOLD], "s": [-radius, radius]},
        "mesh": {"n_r": int(n_r), "n_s": int(n_s), "h_r": system["h_r"], "h_s": system["h_s"], "nodes": int(n_r * n_s)},
        "horizon": duration,
        "dt_pde": step,
        "n_steps": n_steps,
        "boundary_condition": {"initial_interior": 0.0, "r=-a": 0.0, "r=+a": 1.0, "s": str(artificial_boundary).lower()},
        "weak_corner_compatibility": "initial interior value 0 and B boundary value 1 are discontinuous at the T=0 corner",
        "partial_T_q_equals_L_q": True,
        "partial_T_q_minus_L_q_final_step_max": parabolic_residual,
        "final_time_derivative_max": time_derivative_max,
        "cross_diffusion": "axis/anti-diagonal wide jump representation",
        "drift_discretization": "first-order upwind",
        "time_integrator": "implicit Euler in remaining horizon",
        "solver": "scipy.sparse.linalg.spsolve",
        "solver_tolerance": tolerance,
        "monotone_generator": True,
        "monotonicity_certificate": {"status": "DECLARED", "reason": "nonnegative axis and anti-diagonal jump rates on the declared mesh ratio family"},
        "method_status": "NUMERICAL_REFERENCE_CANDIDATE",
        **diagnostics,
    }


__all__ = [
    "A", "B", "CONTROL_DIRECTION", "CONTROL_GATE_ALPHA", "CONTROL_ROLE", "CONTROL_THRESHOLD", "CP_ALPHA",
    "DT_GRID", "ENGINES", "ENDPOINT_LABELS", "FIRST_LABELS", "HORIZON_GRID", "J", "MAX_STATE_STEP_UPDATES",
    "N_PATHS_PER_CELL", "N_REPS", "OBLIQUE_DIRECTION", "PDE_DT_GRID", "PDE_MESH_GRID", "PDE_R_GRID", "PDE_ROLE",
    "PDE_T_GRID", "PROTOCOL_VERSION", "Q", "ROLE", "ROOT_ENTROPY", "SCHEMA_VERSION", "STARTS", "START_NAMES",
    "STAGE", "STAGE_INDEX", "T", "TARGET_DIRECTION", "TARGET_THRESHOLD", "TERMINAL_LABELS", "TRANSFORMED_J",
    "TRANSFORMED_Q", "TRANSFORM_BASIS", "TRANSVERSE_DIRECTION", "analytic_q_control", "build_spec", "censor_bracket",
    "classify_control_trajectory", "classify_endpoint_state", "classify_trajectory", "expected_primary_cells",
    "expected_primary_updates", "runtime_metadata", "seed_for_cell", "simulate_control", "simulate_control_cell",
    "simulate_control_refinement", "simulate_first_hit", "solve_elliptic_reference", "solve_parabolic_reference",
    "spec_hash", "transition_coefficients", "validate_primary_budget",
]


def analytic_q_control(y: Any) -> Any:
    """Evaluate the independent eventual B-before-A control committor."""

    values = np.asarray(y, dtype=float)
    if not np.isfinite(values).all() or np.any(values < -CONTROL_THRESHOLD) or np.any(values > CONTROL_THRESHOLD):
        raise ValueError("y must be finite and inside the closed control interval")
    scale = np.sqrt(5.0)
    denominator = 2.0 * erfi(scale * CONTROL_THRESHOLD)
    result = (erfi(scale * values) + erfi(scale * CONTROL_THRESHOLD)) / denominator
    if values.ndim == 0:
        return float(result)
    return result
