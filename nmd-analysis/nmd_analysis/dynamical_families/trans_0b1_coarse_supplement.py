"""Supplementary TRANS-0B1 paired replay with an owned coarse Euler step.

The frozen primary artifact retains its original fourth-fine-endpoint coarse
view.  This module is a separate analysis artifact: it consumes the same
fine normal draws, updates the fine state with 512 Euler steps, and updates a
second state every four draws with its own 1/128 Euler drift step and the sum
of those four Brownian increments.  It does not alter the primary gate.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from . import trans_0b1 as base


SUPPLEMENT_SCHEMA_VERSION = "nmd_analysis.trans_0b1.coarse_supplement.v1"


def _integer(value: Any, name: str, *, minimum: int = 1) -> int:
    if isinstance(value, (bool, np.bool_)):
        raise TypeError(f"{name} must be an integer")
    integer = int(value)
    if integer != value or integer < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return integer


def _finite_float(value: Any, name: str, *, positive: bool = False) -> float:
    number = float(value)
    if not np.isfinite(number) or (positive and number <= 0.0):
        raise ValueError(f"{name} must be finite and positive")
    return number


def _terminal_summary(state: np.ndarray, *, start: np.ndarray, dt: float,
                      horizon: float, seed: Any) -> dict[str, Any]:
    projection = state @ base.TARGET_DIRECTION
    labels = np.full(state.shape[0], 2, dtype=np.int8)
    labels[projection <= -base.TARGET_THRESHOLD] = 0
    labels[projection >= base.TARGET_THRESHOLD] = 1
    return {
        "n_A": int(np.sum(labels == 0)),
        "n_B": int(np.sum(labels == 1)),
        "n_U": int(np.sum(labels == 2)),
        "n_total": int(state.shape[0]),
        "start": np.asarray(start, dtype=float),
        "dt": float(dt),
        "horizon": float(horizon),
        "n_steps": int(round(horizon / dt)),
        "seed": seed.entropy if isinstance(seed, np.random.SeedSequence) else int(seed),
        "labels_checksum": hashlib.sha256(labels.tobytes()).hexdigest(),
        "terminal_state_checksum": hashlib.sha256(np.ascontiguousarray(state).tobytes()).hexdigest(),
        "terminal_mean": np.mean(state, axis=0),
        "terminal_covariance": np.cov(state, rowvar=False, ddof=0),
    }


def simulate_owned_coarse_pair(
    start: Sequence[float] | np.ndarray,
    *,
    n_paths: int,
    seed: int | np.random.SeedSequence,
    fine_dt: float = base.FINE_DT,
    coarse_dt: float = base.COARSE_DT,
    horizon: float = base.T,
) -> dict[str, Any]:
    """Replay one seed with fine and genuine coarse Euler states.

    The RNG calls and fine update are byte-for-byte aligned with the frozen
    primary simulator.  Coarse noise is ``sum(z_4)*sqrt(fine_dt)`` and coarse
    drift is evaluated from the coarse state at the coarse interval start.
    """

    initial = np.asarray(start, dtype=float).reshape(-1)
    if initial.shape != (2,) or not np.isfinite(initial).all():
        raise ValueError("start must be a finite two-dimensional vector")
    count = _integer(n_paths, "n_paths")
    fine_step = _finite_float(fine_dt, "fine_dt", positive=True)
    coarse_step = _finite_float(coarse_dt, "coarse_dt", positive=True)
    duration = _finite_float(horizon, "horizon", positive=True)
    ratio = coarse_step / fine_step
    stride = int(round(ratio))
    if stride < 1 or not np.isclose(ratio, stride, rtol=0, atol=1e-12):
        raise ValueError("coarse_dt must be an integer multiple of fine_dt")
    fine_steps_float = duration / fine_step
    fine_steps = int(round(fine_steps_float))
    if fine_steps < 1 or not np.isclose(fine_steps_float, fine_steps, rtol=0, atol=1e-12):
        raise ValueError("horizon/fine_dt must be a positive integer")
    if fine_steps % stride:
        raise ValueError("horizon must contain complete coarse intervals")

    rng = np.random.default_rng(seed)
    chol = np.linalg.cholesky(base.Q)
    fine = np.repeat(initial[None, :], count, axis=0)
    coarse = fine.copy()
    aggregate_z = np.zeros((count, 2), dtype=float)
    for step_index in range(1, fine_steps + 1):
        z = rng.standard_normal((count, 2))
        fine += (fine @ base.J.T) * fine_step + z @ chol.T * np.sqrt(fine_step)
        aggregate_z += z
        if step_index % stride == 0:
            coarse += (coarse @ base.J.T) * coarse_step + aggregate_z @ chol.T * np.sqrt(fine_step)
            aggregate_z.fill(0.0)

    return {
        "fine": _terminal_summary(fine, start=initial, dt=fine_step, horizon=duration, seed=seed),
        "coarse": _terminal_summary(coarse, start=initial, dt=coarse_step, horizon=duration, seed=seed),
        "shared_noise_stream": True,
        "coarse_from_fine_stride": stride,
        "coarse_update": "own Euler drift step plus sum of four fine Gaussian draws",
        "seed_contract": [base.ROOT_ENTROPY, 0],
    }


def compare_fine_to_primary(pair: dict[str, Any], primary_row: dict[str, Any]) -> dict[str, Any]:
    """Require exact fine count/checksum parity with one primary rich row."""

    fine = pair["fine"]
    fields = ("n_A", "n_B", "n_U", "n_total", "labels_checksum", "terminal_state_checksum")
    mismatches = {
        field: {"supplement": fine[field], "primary": primary_row[field]}
        for field in fields if fine[field] != primary_row[field]
    }
    return {"matches": not mismatches, "mismatches": mismatches}


def _plain(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def run_supplement(primary_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    """Replay all frozen seeds and write a separate coarse supplement."""

    primary_file = Path(primary_path)
    output_file = Path(output_path)
    if output_file.exists():
        raise FileExistsError(f"refusing pre-existing supplement output: {output_file}")
    primary = json.loads(primary_file.read_text(encoding="utf-8"))
    primary_rows = {
        (int(row["rep"]), int(row["start_index"])): row
        for row in primary["rows"]
        if float(row["dt"]) == base.FINE_DT
    }
    if len(primary_rows) != base.N_REPS * len(base.STARTS):
        raise ValueError("primary does not contain exactly one fine row per rep/start")
    replay_rows: list[dict[str, Any]] = []
    fine_matches = []
    for rep in range(base.N_REPS):
        for start_index, start in enumerate(base.STARTS):
            seed = np.random.SeedSequence([base.ROOT_ENTROPY, 0, rep, start_index])
            pair = simulate_owned_coarse_pair(start, n_paths=base.N_PATHS_PER_START, seed=seed)
            parity = compare_fine_to_primary(pair, primary_rows[(rep, start_index)])
            fine_matches.append(parity["matches"])
            replay_rows.append({
                "rep": rep,
                "start_index": start_index,
                "seed": [base.ROOT_ENTROPY, 0, rep, start_index],
                "fine": pair["fine"],
                "coarse": pair["coarse"],
                "fine_primary_parity": parity,
                "coarse_fine_category_rate_difference": np.asarray([
                    pair["coarse"][key] - pair["fine"][key]
                    for key in ("n_A", "n_B", "n_U")
                ], dtype=float) / base.N_PATHS_PER_START,
            })
    if not all(fine_matches):
        raise RuntimeError("supplement fine replay does not match the frozen primary")
    report = {
        "schema_version": SUPPLEMENT_SCHEMA_VERSION,
        "status": "PASS" if all(fine_matches) else "FAIL",
        "primary_coarse_status": "INVALID_AS_OWN_COARSE_EULER_STEP",
        "scope": "supplementary descriptive timestep replay; no primary gate",
        "primary_path": str(primary_file),
        "primary_sha256": hashlib.sha256(primary_file.read_bytes()).hexdigest(),
        "spec": base.build_spec(),
        "coarse_contract": {
            "fine_dt": base.FINE_DT,
            "coarse_dt": base.COARSE_DT,
            "stride": 4,
            "same_seed_contract": [base.ROOT_ENTROPY, 0, "rep", "start_index"],
            "coarse_drift": "coarse_state @ J.T * coarse_dt",
            "coarse_noise": "sum(four fine z) @ chol(Q).T * sqrt(fine_dt)",
        },
        "fine_primary_parity": {"all_match": bool(all(fine_matches)), "n_rows": len(fine_matches)},
        "rows": replay_rows,
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(_plain(report), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return report

