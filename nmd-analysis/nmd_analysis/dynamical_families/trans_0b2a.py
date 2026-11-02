"""TRANS-0B2a grid-observed first-hit semantics for a two-dimensional OU law.

This module owns only the synthetic semantic pilot.  It keeps two full state
copies: an endpoint-observed first-hit copy and an unabsorbed continuation
copy.  The latter is always advanced to the horizon and is the sole source of
the terminal record.  The first-hit labels therefore remain distinct from
terminal occupancy labels, including when a path hits a target and later
returns to the middle category.

The public simulation function is intentionally bounded to the prospective
TRANS-0B2a grid.  It accepts non-primary seeds for fixtures and tests, while
the primary runner is responsible for the frozen seed namespace and artifact
serialization.
"""

from __future__ import annotations

import hashlib
import json
import platform
from functools import lru_cache
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.linalg import expm
from scipy.stats import beta


SCHEMA_VERSION = "nmd_analysis.trans_0b2a.v1"
PROTOCOL_VERSION = "ndt_trans_0b2a_20260908.v1"
STAGE = "TRANS-0B2a"
ROLE = "semantic_pilot"
ROOT_ENTROPY = 2_026_090_801
STAGE_INDEX = 0

J = np.asarray([[-1.0, 3.0], [0.0, -2.0]], dtype=float)
Q = np.diag([0.04, 0.40]).astype(float)
T = 1.0
DT_GRID = (1.0 / 128.0, 1.0 / 256.0, 1.0 / 512.0)
HORIZON_GRID = (T,)
ENGINES = ("em_endpoint", "exact_ou_grid")
STARTS = np.asarray([[0.6, 0.0], [0.0, 0.6]], dtype=float)
START_NAMES = ("x_axis", "y_axis")
TARGET_DIRECTION = np.asarray([1.0, 1.0], dtype=float) / np.sqrt(2.0)
TARGET_THRESHOLD = 0.75
A = "u.T @ x <= -a (inclusive)"
B = "u.T @ x >= a (inclusive)"
N_REPS = 4
N_PATHS_PER_CELL = 1_000
MAX_STATE_STEP_UPDATES = 30_000_000
CP_ALPHA = 0.025

FIRST_LABELS = ("A", "B", "unresolved")
TERMINAL_LABELS = ("A", "B", "U")
_FIRST_CODE = {"A": 0, "B": 1, "unresolved": -1}
_TERMINAL_CODE = {"A": 0, "B": 1, "U": 2}


def _plain(value: Any) -> Any:
    """Convert NumPy values to JSON-safe values without replacing invalid data."""

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
    array = np.ascontiguousarray(value)
    return _sha256_bytes(array.tobytes(order="C"))


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
    initial = np.asarray(start, dtype=float)
    if initial.shape != (2,) or not np.isfinite(initial).all():
        raise ValueError("start must be a finite two-dimensional vector")
    return initial.copy()


def _grid_value(value: Any, name: str, grid: Sequence[float]) -> float:
    number = _finite_float(value, name, positive=True)
    if not any(np.isclose(number, candidate, rtol=0.0, atol=1e-15) for candidate in grid):
        raise ValueError(f"{name} must be one of the frozen grid values {tuple(grid)}")
    # Return the canonical binary value from the frozen grid.
    return float(next(candidate for candidate in grid if np.isclose(number, candidate, rtol=0.0, atol=1e-15)))


def _grid_steps(dt: float, horizon: float) -> int:
    ratio = horizon / dt
    steps = int(round(ratio))
    if steps < 1 or not np.isclose(ratio, steps, rtol=0.0, atol=1e-12):
        raise ValueError("horizon/dt must be a positive integer")
    return steps


def _validate_engine(engine: Any) -> str:
    if not isinstance(engine, str) or engine not in ENGINES:
        raise ValueError(f"engine must be one of {ENGINES}")
    return engine


def build_spec() -> dict[str, Any]:
    """Return the prospective TRANS-0B2a contract for coordinator freezing."""

    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "experiment": "TRANS-0B2a",
        "stage": STAGE,
        "role": ROLE,
        "J": J.tolist(),
        "Q": Q.tolist(),
        "T": T,
        "u": TARGET_DIRECTION.tolist(),
        "a": TARGET_THRESHOLD,
        "A": A,
        "B": B,
        "starts": STARTS.tolist(),
        "start_names": list(START_NAMES),
        "engines": list(ENGINES),
        "dt_grid": list(DT_GRID),
        "horizon_grid": list(HORIZON_GRID),
        "n_reps": N_REPS,
        "n_paths_per_cell": N_PATHS_PER_CELL,
        "max_state_step_updates": MAX_STATE_STEP_UPDATES,
        "counts_order": {
            "first_hit": list(FIRST_LABELS),
            "terminal": list(TERMINAL_LABELS),
        },
        "semantics": {
            "state_dimension": 2,
            "first_hit": "endpoint-observed earliest inclusive A/B target at t=0 or grid endpoint",
            "first_unresolved": "no endpoint target observed by T; first_time is null",
            "terminal": "continuation state at T classified A/B/U; U is a resolved terminal category",
            "continuation": "full unabsorbed continuation to T in a separately stored state copy, using the same innovations as the first-hit copy",
            "missed_crossings": "between-grid crossings are not corrected",
            "continuous_time_truth": False,
            "eventual_committor": False,
        },
        "engines_definition": {
            "em_endpoint": "x_next=x+Jx*dt+L*z*sqrt(dt), LL.T=Q; full-state endpoint Euler-Maruyama",
            "exact_ou_grid": "x_next=expm(J*dt)@x+L_dt*z; covariance integral_0^dt expm(Js)Qexpm(J.Ts) ds",
            "shared_innovations": "one innovation per step is applied to both state copies",
        },
        "sampling": {
            "seed_entropy": [ROOT_ENTROPY, STAGE_INDEX, "engine_index", "rep", "start_index"],
            "dt_child_spawn_key": ["dt_index"],
            "seed_contract": "SeedSequence([2026090801, 0, engine_index, rep, start_index], spawn_key=(dt_index,))",
            "rng": "numpy.random.default_rng with PCG64",
            "paired_dt_refinement_claim": False,
        },
        "artifacts": {
            "path_key_fields": [
                "stage", "role", "engine", "engine_index", "rep", "start_index",
                "dt_index", "dt", "horizon", "path_id", "local_path_index",
                "seed_tuple", "seed_spawn_key",
            ],
            "path_format": "gzip JSONL; no padding or missing rows",
            "per_path_continuation_checksum": "sha256(float64 C-order terminal continuation state bytes)",
            "audit_trace_rule": "retain continuation states at t=0..T for local_path_index 0 and 1 in every cell",
        },
        "validation": {
            "cp_censor_bracket_alpha": CP_ALPHA,
            "cp_semantics": "pointwise descriptive [CP(n_B,N), CP(n_B+n_unresolved,N)]",
            "scientific_gate": None,
        },
    }


def spec_hash(spec: Mapping[str, Any] | None = None) -> str:
    return _sha256_bytes(_canonical_json(build_spec() if spec is None else spec))


def seed_for_cell(
    engine_index: int,
    rep: int,
    start_index: int,
    dt_index: int,
) -> tuple[np.random.SeedSequence, list[int], list[int]]:
    """Return the distinct dt child stream for one frozen cell.

    The entropy tuple identifies the engine/replicate/start parent stream and
    the dt index is a child ``spawn_key``.  This makes stream identity explicit
    without suggesting that the dt cells are paired refinements.
    """

    engine_number = _integer(engine_index, "engine_index", minimum=0, maximum=len(ENGINES) - 1)
    repetition = _integer(rep, "rep", minimum=0, maximum=N_REPS - 1)
    start_number = _integer(start_index, "start_index", minimum=0, maximum=len(STARTS) - 1)
    dt_number = _integer(dt_index, "dt_index", minimum=0, maximum=len(DT_GRID) - 1)
    seed_tuple = [ROOT_ENTROPY, STAGE_INDEX, engine_number, repetition, start_number]
    spawn_key = [dt_number]
    return np.random.SeedSequence(seed_tuple, spawn_key=tuple(spawn_key)), seed_tuple, spawn_key


@lru_cache(maxsize=len(DT_GRID))
def transition_coefficients(dt: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``Phi``, exact OU innovation covariance and its Cholesky factor."""

    step = _grid_value(dt, "dt", DT_GRID)
    block = np.block([[J, Q], [np.zeros((2, 2)), -J.T]])
    exponential = expm(block * step)
    phi = np.asarray(exponential[:2, :2], dtype=float)
    cross = np.asarray(exponential[:2, 2:], dtype=float)
    covariance = 0.5 * (cross @ phi.T + (cross @ phi.T).T)
    if not np.isfinite(phi).all() or not np.isfinite(covariance).all():
        raise FloatingPointError("exact OU transition coefficients are nonfinite")
    eigenvalues = np.linalg.eigvalsh(covariance)
    if float(np.min(eigenvalues)) <= 0.0:
        raise ValueError("exact OU innovation covariance is not positive definite")
    chol = np.linalg.cholesky(covariance)
    return phi, covariance, chol


def _step_state(state: np.ndarray, z: np.ndarray, *, engine: str, dt: float, chol_q: np.ndarray | None = None, phi: np.ndarray | None = None, chol_exact: np.ndarray | None = None) -> np.ndarray:
    if engine == "em_endpoint":
        assert chol_q is not None
        updated = state + (state @ J.T) * dt + (z @ chol_q.T) * np.sqrt(dt)
    else:
        assert phi is not None and chol_exact is not None
        updated = state @ phi.T + z @ chol_exact.T
    if not np.isfinite(updated).all():
        raise FloatingPointError("nonfinite state encountered")
    return updated


def _target_code(projection: float) -> int | None:
    if projection <= -TARGET_THRESHOLD:
        return 0
    if projection >= TARGET_THRESHOLD:
        return 1
    return None


def classify_terminal_state(state: Sequence[float] | np.ndarray) -> str:
    """Classify one full state at T as A, B or U with inclusive boundaries."""

    point = _validate_start(state)
    code = _target_code(float(TARGET_DIRECTION @ point))
    return TERMINAL_LABELS[code] if code is not None else "U"


def classify_trajectory(states: Sequence[Sequence[float]] | np.ndarray, *, dt: float, horizon: float | None = None) -> dict[str, Any]:
    """Classify an explicitly supplied endpoint trajectory for hand fixtures.

    ``states`` includes the initial state at index zero.  The returned terminal
    label refers to the last state, while the first-hit result scans every
    endpoint independently.  This helper is deterministic and does not draw
    random numbers.
    """

    step = _grid_value(dt, "dt", DT_GRID)
    trajectory = np.asarray(states, dtype=float)
    if trajectory.ndim != 2 or trajectory.shape[1] != 2 or trajectory.shape[0] < 1 or not np.isfinite(trajectory).all():
        raise ValueError("states must be a finite array with shape (n_steps+1, 2)")
    duration = float((trajectory.shape[0] - 1) * step) if horizon is None else _finite_float(horizon, "horizon", positive=True)
    expected_steps = _grid_steps(step, duration)
    if expected_steps != trajectory.shape[0] - 1:
        raise ValueError("states length does not match horizon/dt")
    projections = trajectory @ TARGET_DIRECTION
    hit_a = projections <= -TARGET_THRESHOLD
    hit_b = projections >= TARGET_THRESHOLD
    hit_indices = np.flatnonzero(hit_a | hit_b)
    if hit_indices.size:
        index = int(hit_indices[0])
        first_label = "A" if bool(hit_a[index]) else "B"
        first_time: float | None = float(index * step)
        first_state: list[float] | None = trajectory[index].tolist()
    else:
        first_label = "unresolved"
        first_time = None
        first_state = None
    terminal = trajectory[-1]
    return {
        "first_label": first_label,
        "first_time": first_time,
        "first_hit_state": first_state,
        "terminal_label": classify_terminal_state(terminal),
        "terminal_state": terminal.tolist(),
        "n_steps": expected_steps,
        "dt": step,
        "horizon": duration,
    }


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
    """Detect the frozen primary root before any generator is constructed."""

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


def _empty_joint() -> np.ndarray:
    return np.zeros((len(FIRST_LABELS), len(TERMINAL_LABELS)), dtype=np.int64)


def _count_labels(labels: Sequence[str], order: Sequence[str]) -> dict[str, int]:
    return {label: int(sum(item == label for item in labels)) for label in order}


def _cp_lower(successes: int, total: int, alpha: float) -> float:
    return 0.0 if successes == 0 else float(beta.ppf(alpha, successes, total - successes + 1))


def _cp_upper(successes: int, total: int, alpha: float) -> float:
    return 1.0 if successes == total else float(beta.ppf(1.0 - alpha, successes + 1, total - successes))


def censor_bracket(n_b: int, n_unresolved: int, n_total: int, *, alpha: float = CP_ALPHA) -> list[float]:
    """Return the pointwise descriptive CP censor bracket for ``p_B``."""

    total = _integer(n_total, "n_total", minimum=1)
    successes = _integer(n_b, "n_B", minimum=0)
    unresolved = _integer(n_unresolved, "n_unresolved", minimum=0)
    if successes + unresolved > total:
        raise ValueError("n_B+n_unresolved must not exceed n_total")
    tail = _finite_float(alpha, "alpha", positive=True)
    if tail >= 1.0:
        raise ValueError("alpha must be below one")
    return [_cp_lower(successes, total, tail), _cp_upper(successes + unresolved, total, tail)]


def _cell_summary(
    *,
    first_labels: np.ndarray,
    terminal_labels: np.ndarray,
    continuation_state: np.ndarray,
    first_hit_state: np.ndarray,
    initial: np.ndarray,
    engine: str,
    engine_index: int,
    rep: int,
    start_index: int,
    dt_index: int,
    dt: float,
    horizon: float,
    seed: int | np.random.SeedSequence,
    seed_tuple: Sequence[int] | None,
    seed_spawn_key: Sequence[int] | None,
) -> dict[str, Any]:
    first_text = np.asarray([FIRST_LABELS[0] if code == 0 else FIRST_LABELS[1] if code == 1 else FIRST_LABELS[2] for code in first_labels], dtype=object)
    terminal_text = np.asarray([TERMINAL_LABELS[int(code)] for code in terminal_labels], dtype=object)
    first_counts = _count_labels(first_text.tolist(), FIRST_LABELS)
    terminal_counts = _count_labels(terminal_text.tolist(), TERMINAL_LABELS)
    joint = _empty_joint()
    for first, terminal in zip(first_text, terminal_text):
        joint[FIRST_LABELS.index(str(first)), TERMINAL_LABELS.index(str(terminal))] += 1
    result: dict[str, Any] = {
        "stage": STAGE,
        "role": ROLE,
        "engine": engine,
        "engine_index": engine_index,
        "rep": rep,
        "start_index": start_index,
        "start": initial.copy(),
        "dt_index": dt_index,
        "dt": dt,
        "horizon": horizon,
        "n_steps": _grid_steps(dt, horizon),
        "n_total": int(first_labels.size),
        "n_first_A": first_counts["A"],
        "n_first_B": first_counts["B"],
        "n_first_unresolved": first_counts["unresolved"],
        "n_terminal_A": terminal_counts["A"],
        "n_terminal_B": terminal_counts["B"],
        "n_terminal_U": terminal_counts["U"],
        "first_hit_counts": first_counts,
        "terminal_counts": terminal_counts,
        "joint_counts": {"first_hit_rows": list(FIRST_LABELS), "terminal_columns": list(TERMINAL_LABELS), "values": joint},
        "unresolved_fraction": float(first_counts["unresolved"] / first_labels.size),
        "terminal_p_B": float(terminal_counts["B"] / first_labels.size),
        "censor_bracket_p_B": censor_bracket(first_counts["B"], first_counts["unresolved"], int(first_labels.size)),
        "continuation_state_checksum": _sha256_array(continuation_state),
        "first_hit_state_checksum": _sha256_array(first_hit_state),
        "terminal_state_checksum": _sha256_array(continuation_state),
        "terminal_mean": np.mean(continuation_state, axis=0),
        "terminal_covariance": np.cov(continuation_state, rowvar=False, ddof=0),
        "seed": _seed_metadata(seed),
        "seed_tuple": list(seed_tuple) if seed_tuple is not None else None,
        "seed_spawn_key": list(seed_spawn_key) if seed_spawn_key is not None else _seed_metadata(seed)["spawn_key"],
        "rng_contract": "numpy.random.default_rng PCG64",
        "terminal_source": "continuation_state at horizon; never first-hit state",
    }
    return result


def simulate_first_hit(
    start: Sequence[float] | np.ndarray,
    *,
    n_paths: int,
    seed: int | np.random.SeedSequence,
    engine: str,
    dt: float,
    horizon: float = T,
    engine_index: int | None = None,
    rep: int | None = None,
    start_index: int | None = None,
    dt_index: int | None = None,
    seed_tuple: Sequence[int] | None = None,
    seed_spawn_key: Sequence[int] | None = None,
    return_path_rows: bool = True,
    return_states: bool = False,
    return_audit_traces: bool = False,
    allow_primary: bool = False,
) -> dict[str, Any]:
    """Simulate one bounded first-hit cell with two independently stored copies.

    The random innovation is generated once per step and applied to both full
    state arrays.  The first-hit array is only semantically read for its first
    target event; terminal labels and states always come from the continuation
    array advanced for the complete horizon.
    """

    initial = _validate_start(start)
    count = _integer(n_paths, "n_paths", minimum=1, maximum=N_PATHS_PER_CELL)
    selected_engine = _validate_engine(engine)
    step = _grid_value(dt, "dt", DT_GRID)
    # The primary runner supplies the frozen T=1 horizon.  Positive
    # integer-grid sub-horizons remain available for deterministic hand
    # fixtures and nonprimary unit tests; the step grid itself stays frozen.
    duration = _finite_float(horizon, "horizon", positive=True)
    if duration > T + 1e-12:
        raise ValueError("horizon must not exceed the frozen primary horizon T")
    n_steps = _grid_steps(step, duration)
    checked_seed = _validate_seed(seed)
    if not isinstance(allow_primary, (bool, np.bool_)):
        raise ValueError("allow_primary must be boolean")
    if _uses_primary_namespace(checked_seed) and not bool(allow_primary):
        raise RuntimeError("primary seed namespace is denied until the frozen runner explicitly enables it")
    if (engine_index is not None and _integer(engine_index, "engine_index", minimum=0, maximum=len(ENGINES) - 1) != ENGINES.index(selected_engine)):
        raise ValueError("engine_index does not match engine")
    if rep is not None:
        _integer(rep, "rep", minimum=0, maximum=N_REPS - 1)
    if start_index is not None:
        index = _integer(start_index, "start_index", minimum=0, maximum=len(STARTS) - 1)
        if not np.array_equal(initial, STARTS[index]):
            raise ValueError("start does not match start_index")
    if dt_index is not None:
        index = _integer(dt_index, "dt_index", minimum=0, maximum=len(DT_GRID) - 1)
        if not np.isclose(step, DT_GRID[index], rtol=0.0, atol=1e-15):
            raise ValueError("dt does not match dt_index")
    if seed_tuple is not None:
        if len(seed_tuple) != 5 or any(isinstance(item, (bool, np.bool_)) or not isinstance(item, (int, np.integer)) for item in seed_tuple):
            raise ValueError("seed_tuple must contain five integer fields")
        expected = [ROOT_ENTROPY, STAGE_INDEX, engine_index, rep, start_index]
        if any(item is None for item in expected) or [int(item) for item in seed_tuple] != [int(item) for item in expected]:
            raise ValueError("seed_tuple does not match the cell identity")
    if seed_spawn_key is not None:
        if len(seed_spawn_key) != 1 or isinstance(seed_spawn_key[0], (bool, np.bool_)) or not isinstance(seed_spawn_key[0], (int, np.integer)) or dt_index is None or int(seed_spawn_key[0]) != int(dt_index):
            raise ValueError("seed_spawn_key must be [dt_index] for the cell")
    if seed_tuple is not None or seed_spawn_key is not None:
        if not isinstance(checked_seed, np.random.SeedSequence):
            raise ValueError("a declared cell seed identity requires a SeedSequence")
        actual_entropy = checked_seed.entropy
        if isinstance(actual_entropy, np.ndarray):
            actual_entropy = actual_entropy.tolist()
        elif isinstance(actual_entropy, tuple):
            actual_entropy = list(actual_entropy)
        if list(actual_entropy) != list(seed_tuple or []):
            raise ValueError("seed_tuple does not match the actual SeedSequence entropy")
        expected_spawn = list(seed_spawn_key or [])
        if list(checked_seed.spawn_key) != expected_spawn:
            raise ValueError("seed_spawn_key does not match the actual SeedSequence spawn_key")
    if bool(allow_primary) and _uses_primary_namespace(checked_seed) and (seed_tuple is None or seed_spawn_key is None):
        raise ValueError("primary draws require explicit seed_tuple and seed_spawn_key metadata")

    continuation = np.repeat(initial[None, :], count, axis=0)
    first_state = continuation.copy()
    first_codes = np.full(count, -1, dtype=np.int8)
    first_times = np.full(count, np.nan, dtype=float)
    first_states = np.full((count, 2), np.nan, dtype=float)
    trace_count = min(2, count)
    audit_traces = np.empty((trace_count, n_steps + 1, 2), dtype=float) if return_audit_traces else None
    if audit_traces is not None:
        audit_traces[:, 0, :] = continuation[:trace_count]
    initial_projection = continuation @ TARGET_DIRECTION
    first_codes[initial_projection <= -TARGET_THRESHOLD] = 0
    first_codes[initial_projection >= TARGET_THRESHOLD] = 1
    initial_hit = first_codes >= 0
    first_times[initial_hit] = 0.0
    first_states[initial_hit] = initial

    chol_q = np.linalg.cholesky(Q) if selected_engine == "em_endpoint" else None
    phi, _, chol_exact = transition_coefficients(step) if selected_engine == "exact_ou_grid" else (None, None, None)
    rng = np.random.default_rng(checked_seed)
    for step_index in range(1, n_steps + 1):
        z = rng.standard_normal((count, 2))
        active = first_codes < 0
        if np.any(active):
            first_state[active] = _step_state(first_state[active], z[active], engine=selected_engine, dt=step, chol_q=chol_q, phi=phi, chol_exact=chol_exact)
            projection = first_state[active] @ TARGET_DIRECTION
            active_indices = np.flatnonzero(active)
            hit_a = projection <= -TARGET_THRESHOLD
            hit_b = projection >= TARGET_THRESHOLD
            hit = hit_a | hit_b
            if np.any(hit):
                indices = active_indices[hit]
                first_codes[indices[hit_a[hit]]] = 0
                first_codes[indices[hit_b[hit]]] = 1
                first_times[indices] = float(step_index * step)
                first_states[indices] = first_state[indices]
        continuation = _step_state(continuation, z, engine=selected_engine, dt=step, chol_q=chol_q, phi=phi, chol_exact=chol_exact)
        if audit_traces is not None:
            audit_traces[:, step_index, :] = continuation[:trace_count]

    terminal_projection = continuation @ TARGET_DIRECTION
    terminal_codes = np.full(count, 2, dtype=np.int8)
    terminal_codes[terminal_projection <= -TARGET_THRESHOLD] = 0
    terminal_codes[terminal_projection >= TARGET_THRESHOLD] = 1
    if not np.isfinite(continuation).all() or np.any(first_codes < -1) or np.any(first_codes > 1):
        raise FloatingPointError("malformed simulation output")
    summary = _cell_summary(
        first_labels=first_codes,
        terminal_labels=terminal_codes,
        continuation_state=continuation,
        first_hit_state=first_states,
        initial=initial,
        engine=selected_engine,
        engine_index=ENGINES.index(selected_engine) if engine_index is None else int(engine_index),
        rep=-1 if rep is None else int(rep),
        start_index=-1 if start_index is None else int(start_index),
        dt_index=-1 if dt_index is None else int(dt_index),
        dt=step,
        horizon=duration,
        seed=checked_seed,
        seed_tuple=seed_tuple,
        seed_spawn_key=seed_spawn_key,
    )

    path_rows: list[dict[str, Any]] = []
    if return_path_rows:
        for local_index in range(count):
            first_code = int(first_codes[local_index])
            terminal_code = int(terminal_codes[local_index])
            path_rows.append({
                "stage": STAGE,
                "role": ROLE,
                "engine": selected_engine,
                "engine_index": summary["engine_index"],
                "rep": summary["rep"],
                "start_index": summary["start_index"],
                "dt_index": summary["dt_index"],
                "dt": step,
                "horizon": duration,
                "n_steps": n_steps,
                "path_id": f"{STAGE}|{ROLE}|{selected_engine}|rep{summary['rep']}|start{summary['start_index']}|dt{summary['dt_index']}|path{local_index:06d}",
                "local_path_index": local_index,
                "seed_tuple": list(seed_tuple) if seed_tuple is not None else None,
                "seed_spawn_key": list(seed_spawn_key) if seed_spawn_key is not None else _seed_metadata(checked_seed)["spawn_key"],
                "initial_state": initial.tolist(),
                "first_label": FIRST_LABELS[0] if first_code == 0 else FIRST_LABELS[1] if first_code == 1 else FIRST_LABELS[2],
                "first_time": None if first_code < 0 else float(first_times[local_index]),
                "first_hit_state": None if first_code < 0 else first_states[local_index].tolist(),
                "terminal_label": TERMINAL_LABELS[terminal_code],
                "terminal_state": continuation[local_index].tolist(),
                "continuation_state_checksum": _sha256_array(continuation[local_index]),
                "terminal_state_checksum": _sha256_array(continuation[local_index]),
            })
        summary["path_rows_checksum"] = _sha256_bytes(_canonical_json(path_rows))
    if return_states:
        summary["first_hit_codes"] = first_codes.copy()
        summary["terminal_codes"] = terminal_codes.copy()
        summary["first_hit_times"] = first_times.copy()
        summary["first_hit_states"] = first_states.copy()
        summary["continuation_states"] = continuation.copy()
    if audit_traces is not None:
        summary["audit_traces"] = [
            {
                "local_path_index": int(index),
                "path_id": f"{STAGE}|{ROLE}|{selected_engine}|rep{summary['rep']}|start{summary['start_index']}|dt{summary['dt_index']}|path{index:06d}",
                "states": audit_traces[index].copy(),
                "trace_checksum": _sha256_array(audit_traces[index]),
                "trace_source": "unabsorbed continuation state at t=0..T",
            }
            for index in range(trace_count)
        ]
    if return_path_rows:
        summary["path_rows"] = path_rows
    return summary


# Descriptive aliases make the intended cell-level API discoverable without
# duplicating implementation or introducing a second simulator.
simulate_first_hit_cell = simulate_first_hit
simulate_grid_observed_first_hits = simulate_first_hit


def expected_primary_cells() -> int:
    return len(ENGINES) * N_REPS * len(STARTS) * len(DT_GRID)


def expected_primary_updates(*, n_paths: int = N_PATHS_PER_CELL) -> int:
    count = _integer(n_paths, "n_paths", minimum=1, maximum=N_PATHS_PER_CELL)
    updates = 0
    for dt in DT_GRID:
        updates += expected_primary_cells() // len(DT_GRID) * count * _grid_steps(dt, T) * 2
    return updates


def validate_primary_budget(*, n_paths: int = N_PATHS_PER_CELL, max_updates: int = MAX_STATE_STEP_UPDATES) -> dict[str, int | bool]:
    cap = _integer(max_updates, "max_updates", minimum=1)
    updates = expected_primary_updates(n_paths=n_paths)
    if updates > cap:
        raise ValueError(f"prospective state-step cap exceeded: {updates} > {cap}")
    return {"n_cells": expected_primary_cells(), "n_paths_per_cell": int(n_paths), "estimated_state_step_updates": updates, "max_state_step_updates": cap, "within_cap": True}


def runtime_metadata() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": __import__("scipy").__version__,
        "rng": "numpy.random.default_rng PCG64",
    }


__all__ = [
    "A", "B", "CP_ALPHA", "DT_GRID", "ENGINES", "FIRST_LABELS", "HORIZON_GRID", "J", "MAX_STATE_STEP_UPDATES",
    "N_PATHS_PER_CELL", "N_REPS", "PROTOCOL_VERSION", "Q", "ROLE", "ROOT_ENTROPY", "SCHEMA_VERSION", "STARTS",
    "START_NAMES", "STAGE", "TARGET_DIRECTION", "TARGET_THRESHOLD", "T", "TERMINAL_LABELS", "build_spec",
    "censor_bracket", "classify_terminal_state", "classify_trajectory", "expected_primary_cells", "expected_primary_updates",
    "runtime_metadata", "seed_for_cell", "simulate_first_hit", "simulate_first_hit_cell", "simulate_grid_observed_first_hits",
    "spec_hash", "transition_coefficients", "validate_primary_budget",
]
