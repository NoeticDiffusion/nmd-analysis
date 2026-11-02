"""TRANS-0B1: a bounded 2-D anisotropic OU terminal-occupancy reference.

The experiment is analysis-owned and deliberately separate from the 1-D
committor adapter.  It compares a finite-horizon terminal occupancy event with
an independently computed Gaussian OU truth; it does not define an eventual
first-hit committor or a production measurement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.linalg import expm
from scipy.special import ndtr
from scipy.stats import beta


SCHEMA_VERSION = "nmd_analysis.trans_0b1.v1"
PROTOCOL_VERSION = "ndt_trans_0b1_20260907.v1"
ROOT_ENTROPY = 2_026_090_704
J = np.asarray([[-1.0, 3.0], [0.0, -2.0]], dtype=float)
Q = np.diag([0.04, 0.40]).astype(float)
T = 1.0
FINE_DT = 1.0 / 512.0
COARSE_DT = 1.0 / 128.0
N_REPS = 8
N_PATHS_PER_START = 20_000
STARTS = np.asarray([[0.6, 0.0], [0.0, 0.6]], dtype=float)
START_NAMES = ("x_axis", "y_axis")
TARGET_DIRECTION = np.asarray([1.0, 1.0], dtype=float) / np.sqrt(2.0)
TARGET_THRESHOLD = 0.75
RECOVERY_TOLERANCE = 0.01
CP_ALPHA = 0.05 / 12.0


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


def _canonical_json(value: Any) -> bytes:
    return json.dumps(_plain(value), sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _integer(value: Any, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer")
    result = int(value)
    if result < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return result


def _finite_float(value: Any, name: str, *, positive: bool = False) -> float:
    result = float(value)
    if not np.isfinite(result) or (positive and result <= 0):
        raise ValueError(f"{name} must be finite" + (" and positive" if positive else ""))
    return result


def build_spec() -> dict[str, Any]:
    """Return the frozen TRANS-0B1 contract."""

    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "experiment": "TRANS-0B1",
        # Flat aliases make the frozen numeric contract easy for an
        # independent verifier to consume without changing the report shape.
        "J": J.tolist(),
        "Q": Q.tolist(),
        "T": T,
        "u": TARGET_DIRECTION.tolist(),
        "starts": STARTS.tolist(),
        "target_a": -TARGET_THRESHOLD,
        "target_b": TARGET_THRESHOLD,
        "dt": FINE_DT,
        "dt_coarse": COARSE_DT,
        "n_reps": N_REPS,
        "n_paths_per_start": N_PATHS_PER_START,
        "event_semantics": "terminal_halfspace_at_T",
        "u_is_unit_normal": True,
        "middle_is_censored": False,
        "counts_order": ["A", "B", "U"],
        "semantics": {
            "object": "finite_horizon_terminal_occupancy",
            "B": "u^T X_T >= 0.75",
            "A": "u^T X_T <= -0.75",
            "U": "neither terminal target; not censoring and not a first-hit remainder",
            "event_time": T,
            "eventual_committor": False,
            "paths_may_cross_and_return": True,
        },
        "model": {
            "sde": "dX=JX dt+L dW",
            "J": J.tolist(),
            "Q_LL_transpose": Q.tolist(),
            "state_dimension": 2,
            "anisotropic_noise": True,
            "non_normal": True,
            "start_points": STARTS.tolist(),
            "start_names": list(START_NAMES),
            "target_direction": TARGET_DIRECTION.tolist(),
            "target_threshold": TARGET_THRESHOLD,
            "start_comparability": "equal norm and equal initial target projection; J coupling changes terminal means",
        },
        "sampling": {
            "n_repetitions": N_REPS,
            "n_paths_per_start": N_PATHS_PER_START,
            "fine_dt": FINE_DT,
            "coarse_dt": COARSE_DT,
            "horizon": T,
            "coarse_from_fine": "state at every fourth fine Euler endpoint",
            "seed": "SeedSequence([2026090704, 0, rep, start_index])",
            "noise": "default_rng PCG64; one independent stream per repetition/start",
            "shared_paths_across_dt": True,
        },
        "truth": {
            "distribution": "Gaussian OU terminal law",
            "mean": "expm(J*T) @ x0",
            "covariance": "integral_0^T expm(J*s) Q expm(J.T*s) ds",
            "category_probabilities": "normal CDF of u^T X_T",
            "independent_verification": "matrix exponential plus independently coded covariance calculation",
        },
        "evaluation": {
            "primary_dt": FINE_DT,
            "cp_two_sided_tail_alpha": CP_ALPHA,
            "cp_bounds": 12,
            "recovery_tolerance": RECOVERY_TOLERANCE,
            "gate": "all six fine-dt category CP intervals within .01 of analytic probabilities",
            "coarse_role": "paired descriptive timestep comparison; no second gate",
            "claims": "finite-horizon synthetic dissociation only; no biological or production claim",
        },
    }


def spec_hash(spec: Mapping[str, Any] | None = None) -> str:
    return _sha256_bytes(_canonical_json(build_spec() if spec is None else spec))


def local_stability(jacobian: Sequence[Sequence[float]] | np.ndarray = J) -> dict[str, Any]:
    """Compute fixed local linear stability and transient-growth diagnostics."""

    matrix = np.asarray(jacobian, dtype=float)
    if matrix.shape != (2, 2) or not np.isfinite(matrix).all():
        raise ValueError("jacobian must be a finite 2x2 matrix")
    eigenvalues = np.linalg.eigvals(matrix)
    symmetric = 0.5 * (matrix + matrix.T)
    return {
        "J": matrix,
        "eigenvalues": eigenvalues,
        "spectral_abscissa_alpha": float(np.max(np.real(eigenvalues))),
        "numerical_abscissa_omega": float(np.max(np.linalg.eigvalsh(symmetric))),
        "symmetric_part": symmetric,
    }


def _validate_model() -> None:
    stability = local_stability(J)
    if stability["spectral_abscissa_alpha"] >= 0 or stability["numerical_abscissa_omega"] <= 0:
        raise RuntimeError("frozen J no longer has alpha<0 and omega>0")
    if not np.allclose(Q, Q.T, rtol=0, atol=0) or np.min(np.linalg.eigvalsh(Q)) <= 0:
        raise RuntimeError("frozen Q must be positive definite")


def _covariance_van_loan(horizon: float = T) -> np.ndarray:
    """Compute OU covariance with a block matrix exponential."""

    duration = _finite_float(horizon, "horizon", positive=True)
    block = np.block([[J, Q], [np.zeros((2, 2)), -J.T]])
    exponential = expm(block * duration)
    phi = exponential[:2, :2]
    cross = exponential[:2, 2:]
    covariance = cross @ phi.T
    return 0.5 * (covariance + covariance.T)


def _covariance_independent(horizon: float = T, *, n_steps: int = 200_000) -> np.ndarray:
    """Independent deterministic midpoint quadrature for verification/tests."""

    duration = _finite_float(horizon, "horizon", positive=True)
    steps = _integer(n_steps, "n_steps", minimum=2)
    times = (np.arange(steps, dtype=float) + 0.5) * duration / steps
    values = np.empty((steps, 2, 2), dtype=float)
    for index, time in enumerate(times):
        transition = expm(J * float(time))
        values[index] = transition @ Q @ transition.T
    return np.mean(values, axis=0) * duration


def ou_truth(start: Sequence[float] | np.ndarray, *, horizon: float = T) -> dict[str, Any]:
    """Return exact Gaussian terminal category probabilities for one start."""

    _validate_model()
    initial = np.asarray(start, dtype=float).reshape(-1)
    if initial.shape != (2,) or not np.isfinite(initial).all():
        raise ValueError("start must be a finite two-dimensional vector")
    duration = _finite_float(horizon, "horizon", positive=True)
    transition = expm(J * duration)
    mean = transition @ initial
    covariance = _covariance_van_loan(duration)
    projected_mean = float(TARGET_DIRECTION @ mean)
    projected_variance = float(TARGET_DIRECTION @ covariance @ TARGET_DIRECTION)
    if projected_variance <= 0 or not np.isfinite(projected_variance):
        raise ValueError("projected terminal variance must be positive")
    standard_deviation = float(np.sqrt(projected_variance))
    p_a = float(ndtr((-TARGET_THRESHOLD - projected_mean) / standard_deviation))
    p_b = float(ndtr((projected_mean - TARGET_THRESHOLD) / standard_deviation))
    p_u = 1.0 - p_a - p_b
    probabilities = np.asarray([p_a, p_b, p_u], dtype=float)
    if np.any(probabilities < -1e-14) or not np.isfinite(probabilities).all():
        raise ValueError("terminal category probabilities are malformed")
    return {
        "start": initial,
        "horizon": duration,
        "transition": transition,
        "mean": mean,
        "covariance": covariance,
        "projected_mean": projected_mean,
        "projected_variance": projected_variance,
        "category_probabilities": probabilities,
        "p_A": p_a,
        "p_B": p_b,
        "p_U": p_u,
    }


def simulate_terminal_events(
    start: Sequence[float] | np.ndarray,
    *,
    n_paths: int,
    seed: int | np.random.SeedSequence,
    dt: float,
    horizon: float = T,
    return_terminal_states: bool = False,
) -> dict[str, Any]:
    """Simulate terminal occupancy with endpoint Euler updates.

    ``U`` means neither threshold at the terminal endpoint.  A path may cross
    either threshold before the endpoint and later return to U or the other
    category; no first-hit label is assigned.
    """

    initial = np.asarray(start, dtype=float).reshape(-1)
    if initial.shape != (2,) or not np.isfinite(initial).all():
        raise ValueError("start must be a finite two-dimensional vector")
    count = _integer(n_paths, "n_paths", minimum=1)
    step = _finite_float(dt, "dt", positive=True)
    duration = _finite_float(horizon, "horizon", positive=True)
    steps_float = duration / step
    n_steps = int(round(steps_float))
    if n_steps < 1 or not np.isclose(steps_float, n_steps, rtol=0, atol=1e-12):
        raise ValueError("horizon/dt must be a positive integer")
    rng = np.random.default_rng(seed)
    state = np.repeat(initial[None, :], count, axis=0)
    noise_scale = float(np.sqrt(step))
    for _ in range(n_steps):
        state += (state @ J.T) * step + rng.standard_normal((count, 2)) @ np.linalg.cholesky(Q).T * noise_scale
    projection = state @ TARGET_DIRECTION
    labels = np.full(count, 2, dtype=np.int8)
    labels[projection <= -TARGET_THRESHOLD] = 0
    labels[projection >= TARGET_THRESHOLD] = 1
    result: dict[str, Any] = {
        "n_A": int(np.sum(labels == 0)),
        "n_B": int(np.sum(labels == 1)),
        "n_U": int(np.sum(labels == 2)),
        "n_total": count,
        "start": initial,
        "dt": step,
        "horizon": duration,
        "n_steps": n_steps,
        "seed": seed.entropy if isinstance(seed, np.random.SeedSequence) else int(seed),
        "labels_checksum": hashlib.sha256(labels.tobytes()).hexdigest(),
        "terminal_mean": np.mean(state, axis=0),
        "terminal_covariance": np.cov(state, rowvar=False, ddof=0),
    }
    if return_terminal_states:
        result["terminal_states"] = state
        result["labels"] = labels
    result["terminal_state_checksum"] = hashlib.sha256(np.ascontiguousarray(state).tobytes()).hexdigest()
    return result


def simulate_paired_terminal_events(
    start: Sequence[float] | np.ndarray,
    *,
    n_paths: int,
    seed: int | np.random.SeedSequence,
    fine_dt: float = FINE_DT,
    coarse_dt: float = COARSE_DT,
    horizon: float = T,
    return_terminal_states: bool = False,
) -> dict[str, Any]:
    """Simulate paired fine and every-fourth-endpoint coarse terminal states."""

    fine_step = _finite_float(fine_dt, "fine_dt", positive=True)
    coarse_step = _finite_float(coarse_dt, "coarse_dt", positive=True)
    ratio = coarse_step / fine_step
    stride = int(round(ratio))
    if stride < 1 or not np.isclose(ratio, stride, rtol=0, atol=1e-12):
        raise ValueError("coarse_dt must be an integer multiple of fine_dt")
    count = _integer(n_paths, "n_paths", minimum=1)
    initial = np.asarray(start, dtype=float).reshape(-1)
    if initial.shape != (2,) or not np.isfinite(initial).all():
        raise ValueError("start must be a finite two-dimensional vector")
    duration = _finite_float(horizon, "horizon", positive=True)
    fine_steps_float = duration / fine_step
    fine_steps = int(round(fine_steps_float))
    if fine_steps < 1 or not np.isclose(fine_steps_float, fine_steps, rtol=0, atol=1e-12) or fine_steps % stride:
        raise ValueError("horizon must contain an integer number of complete coarse intervals")
    rng = np.random.default_rng(seed)
    state = np.repeat(initial[None, :], count, axis=0)
    coarse_state = state.copy()
    chol = np.linalg.cholesky(Q)
    for step_index in range(1, fine_steps + 1):
        state += (state @ J.T) * fine_step + rng.standard_normal((count, 2)) @ chol.T * np.sqrt(fine_step)
        if step_index % stride == 0:
            coarse_state = state.copy()

    def summarize_state(terminal: np.ndarray, dt: float) -> dict[str, Any]:
        projection = terminal @ TARGET_DIRECTION
        labels = np.full(count, 2, dtype=np.int8)
        labels[projection <= -TARGET_THRESHOLD] = 0
        labels[projection >= TARGET_THRESHOLD] = 1
        return {
            "n_A": int(np.sum(labels == 0)),
            "n_B": int(np.sum(labels == 1)),
            "n_U": int(np.sum(labels == 2)),
            "n_total": count,
            "dt": dt,
            "horizon": duration,
            "n_steps": int(round(duration / dt)),
            "terminal_mean": np.mean(terminal, axis=0),
            "terminal_covariance": np.cov(terminal, rowvar=False, ddof=0),
            "labels_checksum": hashlib.sha256(labels.tobytes()).hexdigest(),
            "terminal_state_checksum": hashlib.sha256(np.ascontiguousarray(terminal).tobytes()).hexdigest(),
        }

    result: dict[str, Any] = {
        "start": initial,
        "seed": seed.entropy if isinstance(seed, np.random.SeedSequence) else int(seed),
        "fine": summarize_state(state, fine_step),
        "coarse": summarize_state(coarse_state, coarse_step),
        "shared_noise_stream": True,
        "coarse_from_fine_stride": stride,
    }
    if return_terminal_states:
        result["fine_terminal_states"] = state
        result["coarse_terminal_states"] = coarse_state
    return result


def _cp_interval(successes: int, total: int, alpha: float) -> tuple[float, float]:
    if successes == 0:
        lower = 0.0
    else:
        lower = float(beta.ppf(alpha / 2.0, successes, total - successes + 1))
    if successes == total:
        upper = 1.0
    else:
        upper = float(beta.ppf(1.0 - alpha / 2.0, successes + 1, total - successes))
    return lower, upper


def score_events(counts: Mapping[str, Any], truth: Sequence[float] | np.ndarray, *, alpha: float = CP_ALPHA) -> dict[str, Any]:
    """Score A/B/U counts with two-sided Clopper-Pearson intervals."""

    values = {key: _integer(counts.get(key), key, minimum=0) for key in ("n_A", "n_B", "n_U")}
    total = sum(values.values())
    if total < 1 or ("n_total" in counts and _integer(counts["n_total"], "n_total") != total):
        raise ValueError("counts must have a consistent positive total")
    requested_alpha = _finite_float(alpha, "alpha", positive=True)
    if requested_alpha >= 1:
        raise ValueError("alpha must be below one")
    reference = np.asarray(truth, dtype=float).reshape(-1)
    if reference.shape != (3,) or not np.isfinite(reference).all() or not np.isclose(np.sum(reference), 1.0, atol=1e-12):
        raise ValueError("truth must be a three-category probability vector")
    intervals = np.asarray([_cp_interval(values[key], total, requested_alpha) for key in ("n_A", "n_B", "n_U")], dtype=float)
    distances = np.maximum(np.abs(intervals[:, 0] - reference), np.abs(intervals[:, 1] - reference))
    return {
        **values,
        "n_total": total,
        "truth": reference,
        "intervals": intervals,
        "endpoint_distances": distances,
        "max_endpoint_distance": float(np.max(distances)),
        "alpha": requested_alpha,
    }


def summarize_0b1(
    rows: Sequence[Mapping[str, Any]],
    truths: Sequence[Mapping[str, Any]],
    *,
    fine_dt: float = FINE_DT,
) -> dict[str, Any]:
    """Summarize fixed two-start/two-timestep rows and the fine gate."""

    entries = list(rows)
    if not entries:
        raise ValueError("rows must not be empty")
    truth_by_start = {int(item["start_index"]): np.asarray(item["truth"], dtype=float) for item in truths}
    scored: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    seen_cells: set[tuple[int, int, float]] = set()
    for row in entries:
        start_index = _integer(row.get("start_index"), "start_index", minimum=0)
        if start_index not in truth_by_start:
            raise ValueError("row has no matching analytic truth")
        cell = (_integer(row.get("rep"), "rep", minimum=0), start_index, float(row.get("dt")))
        if cell in seen_cells:
            raise ValueError("duplicate repetition/start/timestep row")
        seen_cells.add(cell)
        counts = {key: row.get(key) for key in ("n_A", "n_B", "n_U", "n_total")}
        try:
            result = score_events(counts, truth_by_start[start_index])
        except (TypeError, ValueError) as exc:
            invalid_rows.append({"rep": cell[0], "start_index": start_index, "dt": cell[2], "error": str(exc)})
            continue
        scored.append({**dict(row), "score": result})
    fine = [row for row in scored if np.isclose(float(row["dt"]), fine_dt, rtol=0, atol=1e-15)]
    expected_fine = N_REPS * len(STARTS)
    pooled_fine: list[dict[str, Any]] = []
    for start_index in range(len(STARTS)):
        cells = [row for row in fine if int(row["start_index"]) == start_index]
        if len(cells) != N_REPS:
            continue
        counts = {key: int(sum(int(row[key]) for row in cells)) for key in ("n_A", "n_B", "n_U", "n_total")}
        pooled_fine.append({"start_index": start_index, **counts, "score": score_events(counts, truth_by_start[start_index])})
    if invalid_rows:
        primary_decision = "INCONCLUSIVE"
    elif any(not np.isfinite(float(row["score"]["max_endpoint_distance"])) for row in pooled_fine):
        primary_decision = "INCONCLUSIVE"
    elif len(fine) != expected_fine or len(pooled_fine) != len(STARTS):
        primary_decision = "INCONCLUSIVE"
    elif any(float(row["score"]["max_endpoint_distance"]) > RECOVERY_TOLERANCE for row in pooled_fine):
        primary_decision = "FAIL"
    else:
        primary_decision = "PASS"
    return {
        "primary_decision": primary_decision,
        "primary_dt": fine_dt,
        "recovery_tolerance": RECOVERY_TOLERANCE,
        "n_fine_rows": len(fine),
        "n_expected_fine_rows": expected_fine,
        "n_pooled_fine_rows": len(pooled_fine),
        "max_fine_endpoint_distance": max((float(row["score"]["max_endpoint_distance"]) for row in pooled_fine), default=None),
        "pooled_fine_rows": pooled_fine,
        "invalid_rows": invalid_rows,
        "rows": scored,
        "semantics": "terminal occupancy at T; U is neither terminal target and is not censoring",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.spec_only:
        parser.error("only --spec-only is provided by the analysis module; use the frozen runner for primary draws")
    payload = {"spec": build_spec(), "spec_sha256": spec_hash(), "local_stability": local_stability()}
    print(json.dumps(_plain(payload), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
