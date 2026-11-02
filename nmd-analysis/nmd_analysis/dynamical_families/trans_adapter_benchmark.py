"""Bounded analysis-side comparison of the unchanged O2b committor adapter.

This module is deliberately small and fail-closed.  It generates the frozen
one-dimensional TRANS reference paths, fits the ingest O2b adapter on each
training packet only, and scores the returned grid on independent held-out
first-exit paths.  It does not modify ingest code, produce an HDF5 overlay, or
make a biological claim.
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
from scipy.integrate import quad
from scipy.stats import beta


SCHEMA_VERSION = "nmd_analysis.trans_adapter_benchmark.v1"
PROTOCOL_VERSION = "ndt_trans_adapter_001_20260907.v1"
ROOT_ENTROPY = 2_026_090_702
D = 0.2
DIFFUSION_VARIANCE = 2.0 * D
DT = 0.000625
HORIZON = 20.0
MAX_STEPS = int(round(HORIZON / DT))
TARGET_A = -1.0
TARGET_B = 1.0
STARTS = (-0.75, -0.25, 0.0, 0.25, 0.75)
GRID_RESOLUTION = 65
N_FITS = 8
N_TRAIN_PATHS = 512
N_HELDOUT_PATHS = 8_000
MIN_SAMPLES = 30
MIN_SUPPORT_PER_GRID = 30
MIN_TRANSITION_SEGMENTS = 5
MAX_DT_RELATIVE_DEVIATION = 0.05
WRONG_DIFFUSION_VARIANCE = D
RECOVERY_TOLERANCE = 0.05
CP_ALPHA = 0.05 / 15.0
CONSTANT_BASELINE = 0.5
FROZEN_GRID = np.linspace(TARGET_A, TARGET_B, GRID_RESOLUTION, dtype=float)


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


def _sha256_array(value: np.ndarray) -> str:
    return _sha256_bytes(np.ascontiguousarray(np.asarray(value)).tobytes())


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _integer(value: Any, name: str, minimum: int = 1) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer")
    result = int(value)
    if result < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return result


def _finite_float(value: Any, name: str, *, positive: bool = False) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not np.isfinite(result) or (result <= 0.0 if positive else False):
        raise ValueError(f"{name} must be finite" + (" and positive" if positive else ""))
    return result


def _seed_info(seed: np.random.SeedSequence) -> dict[str, Any]:
    entropy = seed.entropy
    if isinstance(entropy, np.integer):
        entropy = int(entropy)
    elif isinstance(entropy, tuple):
        entropy = [int(item) for item in entropy]
    return {
        "entropy": entropy,
        "spawn_key": [int(item) for item in seed.spawn_key],
        "pool_size": int(seed.pool_size),
        "rng": "numpy.random.default_rng",
        "bit_generator": "PCG64",
    }


def build_spec() -> dict[str, Any]:
    """Return the frozen TRANS-ADAPTER-001 numeric contract."""

    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "model": {
            "D": D,
            "diffusion_variance_rate": DIFFUSION_VARIANCE,
            "sde": "dX=(X-X^3)dt+sqrt(2D)dW",
            "drift": "b(x)=x-x^3",
            "dt_sec": DT,
            "horizon_sec": HORIZON,
            "target_A": "x <= -1",
            "target_B": "x >= 1",
            "absorption": "endpoint first exit; time-zero targets included",
            "bridge_correction": False,
        },
        "starts": list(STARTS),
        "grid": {"min": TARGET_A, "max": TARGET_B, "resolution": GRID_RESOLUTION},
        "training": {
            "n_fits": N_FITS,
            "n_paths_per_fit": N_TRAIN_PATHS,
            "initial_states": "cycle [-.75,-.25,0,.25,.75] in order",
            "seed": "SeedSequence([2026090702, 0, fit_index])",
            "raw_storage": "compressed_npz; reaction, offsets, terminal_labels; unclipped overshoots",
            "support": "ordinary first-exit paths only; no probes, top-up, padding or cross-segment pairs",
        },
        "heldout": {
            "n_paths_per_query": N_HELDOUT_PATHS,
            "seed": "SeedSequence([2026090702, 1, query_index])",
            "shared_across_fits": True,
            "denominator": "n_A+n_B+n_unresolved=8000; never resolved-only",
        },
        "adapter": {
            "state_shape": "(N,1)",
            "coordinate_layer": "synthetic_scalar_double_well",
            "coordinate_name": "x",
            "set_A": [0],
            "set_B": [1],
            "grid_resolution": GRID_RESOLUTION,
            "min_samples": MIN_SAMPLES,
            "min_support_per_grid": MIN_SUPPORT_PER_GRID,
            "min_transition_segments": MIN_TRANSITION_SEGMENTS,
            "max_dt_relative_deviation": MAX_DT_RELATIVE_DEVIATION,
            "correct_diffusion_coefficient": DIFFUSION_VARIANCE,
            "wrong_convention_control": WRONG_DIFFUSION_VARIANCE,
        },
        "evaluation": {
            "truth": "continuous q integral of exp(U/D), independently quadrature-computed",
            "constant_baseline": CONSTANT_BASELINE,
            "recovery_tolerance": RECOVERY_TOLERANCE,
            "recovery_gate": "all 40 correct-convention fit/query errors <= .05",
            "cp_tail_alpha": CP_ALPHA,
            "cp_bounds_per_query": 3,
            "cp_familywise_statement": "at least 95 percent over 15 held-out count bounds under ideal independent paths",
            "fit_interval_claim": "none; eight fits are finite descriptive repetitions",
        },
    }


def spec_hash(spec: Mapping[str, Any] | None = None) -> str:
    return _sha256_bytes(_canonical_json(build_spec() if spec is None else spec))


def _path_starts(starts: float | Sequence[float], n_paths: int | None) -> np.ndarray:
    values = np.asarray(starts, dtype=float)
    if values.ndim == 0:
        n = _integer(1 if n_paths is None else n_paths, "n_paths")
        values = np.full(n, float(values), dtype=float)
    else:
        values = values.reshape(-1)
        if n_paths is not None and values.size != int(n_paths):
            raise ValueError("starts length and n_paths disagree")
        if values.size == 0:
            raise ValueError("starts must not be empty")
    if not np.isfinite(values).all() or np.any((values < TARGET_A) | (values > TARGET_B)):
        raise ValueError("starts must be finite and lie in [-1, 1]")
    return values


def simulate_paths(
    starts: float | Sequence[float],
    *,
    n_paths: int | None = None,
    seed: int | np.random.SeedSequence,
    dt: float = DT,
    horizon: float = HORIZON,
) -> dict[str, Any]:
    """Simulate ordinary endpoint-absorbed Euler paths with raw overshoots.

    The returned ``reaction`` is ragged data flattened by ``offsets``.  Every
    path stops at its first endpoint crossing or at ``horizon``.  Labels are
    ``-1`` until the terminal row, where they are ``0`` for A or ``1`` for B.
    """

    path_starts = _path_starts(starts, n_paths)
    step = _finite_float(dt, "dt", positive=True)
    duration = _finite_float(horizon, "horizon")
    steps_float = duration / step
    n_steps = int(round(steps_float))
    if n_steps < 1 or not np.isclose(steps_float, n_steps, rtol=0.0, atol=1e-10):
        raise ValueError("horizon/dt must be a positive integer")
    if seed is None:
        raise ValueError("seed is required")
    rng = np.random.default_rng(seed)
    n = int(path_starts.size)
    paths: list[list[float]] = [[float(value)] for value in path_starts]
    current = path_starts.copy()
    active = np.ones(n, dtype=bool)
    terminal_labels = np.full(n, -1, dtype=np.int8)
    initial_a = current <= TARGET_A
    initial_b = current >= TARGET_B
    terminal_labels[initial_a] = 0
    terminal_labels[initial_b] = 1
    active &= ~(initial_a | initial_b)
    noise_scale = float(np.sqrt(2.0 * D * step))
    for _ in range(n_steps):
        active_indices = np.flatnonzero(active)
        if active_indices.size == 0:
            break
        previous = current[active_indices]
        updated = previous + (previous - previous**3) * step + noise_scale * rng.standard_normal(active_indices.size)
        if not np.isfinite(updated).all():
            raise FloatingPointError("Euler-Maruyama state became non-finite")
        current[active_indices] = updated
        for path_index, value in zip(active_indices, updated):
            paths[int(path_index)].append(float(value))
        hit_a = updated <= TARGET_A
        hit_b = updated >= TARGET_B
        if np.any(hit_a):
            terminal_labels[active_indices[hit_a]] = 0
        if np.any(hit_b):
            terminal_labels[active_indices[hit_b]] = 1
        active[active_indices[hit_a | hit_b]] = False

    lengths = np.asarray([len(path) for path in paths], dtype=np.int64)
    offsets = np.concatenate(([0], np.cumsum(lengths, dtype=np.int64)))
    reaction = np.concatenate([np.asarray(path, dtype=np.float64) for path in paths])
    return {
        "reaction": reaction,
        "offsets": offsets,
        "terminal_labels": terminal_labels,
        "path_lengths": lengths,
        "path_starts": path_starts.astype(np.float64),
        "n_paths": n,
        "n_steps": n_steps,
        "dt": step,
        "horizon": duration,
        "D": D,
        "seed": _seed_info(seed if isinstance(seed, np.random.SeedSequence) else np.random.SeedSequence(int(seed))),
        "rng_type": type(rng.bit_generator).__name__,
        "absorption": "endpoint first exit; time-zero targets included",
        "overshoot_retained": True,
    }


def simulate_counts(
    starts: float | Sequence[float],
    *,
    n_paths: int | None = None,
    seed: int | np.random.SeedSequence,
    dt: float = DT,
    horizon: float = HORIZON,
) -> dict[str, Any]:
    """Simulate only A/B/unresolved counts using the raw path RNG sequence.

    The active-index update and draw order intentionally mirror
    :func:`simulate_paths`; this is the bounded held-out path implementation.
    """

    path_starts = _path_starts(starts, n_paths)
    step = _finite_float(dt, "dt", positive=True)
    duration = _finite_float(horizon, "horizon")
    steps_float = duration / step
    n_steps = int(round(steps_float))
    if n_steps < 1 or not np.isclose(steps_float, n_steps, rtol=0.0, atol=1e-10):
        raise ValueError("horizon/dt must be a positive integer")
    if seed is None:
        raise ValueError("seed is required")
    rng = np.random.default_rng(seed)
    n = int(path_starts.size)
    current = path_starts.copy()
    active = np.ones(n, dtype=bool)
    n_a = int(np.sum(current <= TARGET_A))
    n_b = int(np.sum(current >= TARGET_B))
    active &= ~((current <= TARGET_A) | (current >= TARGET_B))
    noise_scale = float(np.sqrt(2.0 * D * step))
    for _ in range(n_steps):
        active_indices = np.flatnonzero(active)
        if active_indices.size == 0:
            break
        previous = current[active_indices]
        updated = previous + (previous - previous**3) * step + noise_scale * rng.standard_normal(active_indices.size)
        if not np.isfinite(updated).all():
            raise FloatingPointError("Euler-Maruyama state became non-finite")
        current[active_indices] = updated
        hit_a = updated <= TARGET_A
        hit_b = updated >= TARGET_B
        n_a += int(np.sum(hit_a))
        n_b += int(np.sum(hit_b))
        active[active_indices[hit_a | hit_b]] = False
    n_unresolved = int(np.sum(active))
    return {
        "n_A": n_a,
        "n_B": n_b,
        "n_unresolved": n_unresolved,
        "n_total": n,
        "n_paths": n,
        "n_steps": n_steps,
        "dt": step,
        "horizon": duration,
        "D": D,
        "path_starts": path_starts.astype(np.float64),
        "seed": _seed_info(seed if isinstance(seed, np.random.SeedSequence) else np.random.SeedSequence(int(seed))),
        "rng_type": type(rng.bit_generator).__name__,
        "absorption": "endpoint first exit; time-zero targets included",
    }


def _validate_packet(packet: Mapping[str, Any], *, name: str = "packet") -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    required = ("reaction", "offsets", "terminal_labels")
    if any(key not in packet for key in required):
        raise ValueError(f"{name} requires reaction, offsets and terminal_labels")
    reaction = np.asarray(packet["reaction"], dtype=float).reshape(-1)
    offsets = np.asarray(packet["offsets"])
    labels = np.asarray(packet["terminal_labels"])
    if offsets.ndim != 1 or offsets.size < 2 or offsets.dtype.kind not in {"i", "u"}:
        raise ValueError(f"{name}.offsets must be integer and have length n_paths+1")
    offsets = offsets.astype(np.int64, copy=False)
    labels = labels.reshape(-1)
    if labels.dtype.kind not in {"i", "u"}:
        raise ValueError(f"{name}.terminal_labels must be integer")
    if not np.all(np.isin(labels, [-1, 0, 1])):
        raise ValueError(f"{name}.terminal_labels must contain only -1, 0 or 1")
    labels = labels.astype(np.int8, copy=False)
    if offsets[0] != 0 or offsets[-1] != reaction.size or np.any(np.diff(offsets) < 1):
        raise ValueError(f"{name}.offsets must cover contiguous non-empty paths")
    if labels.size != offsets.size - 1 or not np.isfinite(reaction).all():
        raise ValueError(f"{name} arrays are misaligned or nonfinite")
    if "dt" not in packet:
        raise ValueError(f"{name}.dt is required")
    packet_dt = _finite_float(packet["dt"], f"{name}.dt", positive=True)
    if not np.isclose(packet_dt, DT, rtol=0.0, atol=1e-12):
        raise ValueError(f"{name}.dt must equal the frozen dt {DT}")
    if "D" in packet and not np.isclose(_finite_float(packet["D"], f"{name}.D", positive=True), D, rtol=0.0, atol=1e-12):
        raise ValueError(f"{name}.D must equal the frozen D {D}")
    if "n_paths" in packet and _integer(packet["n_paths"], f"{name}.n_paths") != labels.size:
        raise ValueError(f"{name}.n_paths does not match offsets")
    if "n_steps" in packet:
        n_steps = _integer(packet["n_steps"], f"{name}.n_steps")
        if "horizon" in packet:
            horizon = _finite_float(packet["horizon"], f"{name}.horizon")
            expected_steps = int(round(horizon / packet_dt))
            if expected_steps != n_steps or not np.isclose(horizon / packet_dt, n_steps, rtol=0.0, atol=1e-10):
                raise ValueError(f"{name}.n_steps and horizon are inconsistent")
    if "path_lengths" in packet:
        path_lengths = np.asarray(packet["path_lengths"])
        if path_lengths.shape != labels.shape or path_lengths.dtype.kind not in {"i", "u"} or not np.array_equal(path_lengths.astype(np.int64), np.diff(offsets)):
            raise ValueError(f"{name}.path_lengths do not match offsets")
    if "overshoot_retained" in packet and (
        not isinstance(packet["overshoot_retained"], (bool, np.bool_))
        or not bool(packet["overshoot_retained"])
    ):
        raise ValueError(f"{name}.overshoot_retained must be true")
    path_starts = packet.get("path_starts")
    if path_starts is not None:
        path_starts_array = np.asarray(path_starts, dtype=float).reshape(-1)
        if path_starts_array.shape != labels.shape or not np.isfinite(path_starts_array).all():
            raise ValueError(f"{name}.path_starts must align with terminal_labels")
        if not np.array_equal(path_starts_array, reaction[offsets[:-1]]):
            raise ValueError(f"{name}.path_starts must match the first state of every path")
    segment_id = np.repeat(np.arange(labels.size, dtype=np.int32), np.diff(offsets))
    for index, (start, end) in enumerate(zip(offsets[:-1], offsets[1:])):
        values = reaction[start:end]
        label = int(labels[index])
        if label >= 0:
            if (label == 0 and values[-1] > TARGET_A) or (label == 1 and values[-1] < TARGET_B):
                raise ValueError(f"{name} terminal label does not match final state")
            if np.any((values[:-1] <= TARGET_A) | (values[:-1] >= TARGET_B)):
                raise ValueError(f"{name} contains post-terminal rows before its terminal label")
        elif np.any((values <= TARGET_A) | (values >= TARGET_B)):
            raise ValueError(f"{name} unresolved path crosses a target")
    return reaction, offsets, labels, segment_id


def pack_training(packet: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Build the unchanged adapter input from one or more path packets."""

    packets = [packet] if isinstance(packet, Mapping) else list(packet)
    if not packets:
        raise ValueError("at least one path packet is required")
    parts = [_validate_packet(item, name=f"packet[{i}]") for i, item in enumerate(packets)]
    reaction = np.concatenate([part[0] for part in parts])
    labels = np.concatenate([part[2] for part in parts])
    offsets_parts: list[np.ndarray] = [np.asarray([0], dtype=np.int64)]
    n_paths_before = 0
    for _, offsets, _, _ in parts:
        offsets_parts.append(offsets[1:] + offsets_parts[-1][-1])
        n_paths_before += offsets.size - 1
    offsets = np.concatenate(offsets_parts)
    if labels.size != offsets.size - 1:
        raise RuntimeError("packed path offsets are misaligned")
    time = np.concatenate([
        np.arange(int(end - start), dtype=float) * DT
        for start, end in zip(offsets[:-1], offsets[1:])
    ])
    adapter_labels = np.full(reaction.size, -1, dtype=np.int8)
    for index, (start, end) in enumerate(zip(offsets[:-1], offsets[1:])):
        if labels[index] >= 0:
            adapter_labels[end - 1] = labels[index]
    segment_id = np.repeat(np.arange(n_paths_before, dtype=np.int32), np.diff(offsets))
    same_segment = segment_id[1:] == segment_id[:-1]
    if not np.allclose(np.diff(time)[same_segment], DT, rtol=0.0, atol=1e-12):
        raise ValueError("packed path timestep is not exactly the frozen dt")
    return {
        "state": reaction[:, None],
        "time": time,
        "reaction_coordinate": reaction,
        "regime_labels": adapter_labels,
        "segment_id": segment_id,
        "reaction": reaction,
        "offsets": offsets,
        "terminal_labels": labels,
        "n_paths": n_paths_before,
        "dt": DT,
    }


def _adapter_input(training: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a raw or already packed packet without rebuilding its time."""

    reaction, offsets, terminal_labels, expected_segment_id = _validate_packet(training, name="training")
    packed = pack_training(training)
    if "state" in training:
        state = np.asarray(training["state"], dtype=float)
        if state.shape != (reaction.size, 1) or not np.array_equal(state[:, 0], reaction):
            raise ValueError("training.state must be the finite (N,1) reaction coordinate")
    if "reaction_coordinate" in training and not np.array_equal(np.asarray(training["reaction_coordinate"], dtype=float).reshape(-1), reaction):
        raise ValueError("training.reaction_coordinate must match reaction")
    if "segment_id" in training:
        supplied_segment_id = np.asarray(training["segment_id"])
        if supplied_segment_id.shape != expected_segment_id.shape or supplied_segment_id.dtype.kind not in {"i", "u"} or not np.array_equal(supplied_segment_id, expected_segment_id):
            raise ValueError("training.segment_id must contain one contiguous segment per path")
    if "regime_labels" in training:
        supplied_labels = np.asarray(training["regime_labels"])
        if supplied_labels.shape != (reaction.size,) or supplied_labels.dtype.kind not in {"i", "u"} or not np.all(np.isin(supplied_labels, [-1, 0, 1])):
            raise ValueError("training.regime_labels must be integer -1/0/1 labels")
        expected_labels = packed["regime_labels"]
        if not np.array_equal(supplied_labels, expected_labels):
            raise ValueError("training.regime_labels do not match terminal_labels")
    if "time" in training:
        supplied_time = np.asarray(training["time"], dtype=float).reshape(-1)
        if supplied_time.shape != reaction.shape or not np.isfinite(supplied_time).all():
            raise ValueError("training.time must be finite and aligned with reaction")
        if not np.allclose(supplied_time[offsets[:-1]], 0.0, rtol=0.0, atol=1e-12):
            raise ValueError("training.time must reset to zero for each path")
        same_segment = expected_segment_id[1:] == expected_segment_id[:-1]
        dt_pairs = np.diff(supplied_time)[same_segment]
        if not np.allclose(dt_pairs, DT, rtol=0.0, atol=1e-12):
            raise ValueError("training increments must use the frozen regular dt")
        packed["time"] = supplied_time
    return packed


def _adapter_and_closure(ingest_root: str | Path):
    root = Path(ingest_root).expanduser().resolve()
    mndm_src = root / "mndm" / "src"
    core_src = root / "core" / "src"
    if not mndm_src.is_dir() or not core_src.is_dir():
        raise ValueError("ingest_root must contain mndm/src and core/src")
    for path in (str(core_src), str(mndm_src)):
        if path not in sys.path:
            sys.path.insert(0, path)
    from mndm.dynamical_families.committor import estimate_committor_local_law_dense_grid_o2b

    module_path = Path(inspect.getsourcefile(estimate_committor_local_law_dense_grid_o2b) or "").resolve()
    try:
        module_path.relative_to(root)
    except ValueError as exc:
        raise ValueError("imported O2b source is outside the requested ingest_root") from exc
    closure = [
        module_path,
        module_path.with_name("contracts.py"),
        module_path.with_name("validity.py"),
        module_path.parents[1] / "measurement_certificate.py",
        module_path.parents[1] / "inferential_grain.py",
    ]
    closure_hashes = {}
    for path in closure:
        if not path.is_file():
            raise ValueError(f"ingest dependency is missing: {path}")
        try:
            key = str(path.relative_to(root))
        except ValueError:
            key = str(path)
        closure_hashes[key] = _sha256_file(path)
    return estimate_committor_local_law_dense_grid_o2b, closure_hashes


def fit_adapter(
    training: Mapping[str, Any],
    *,
    ingest_root: str | Path,
    diffusion_coefficient: float = DIFFUSION_VARIANCE,
) -> dict[str, Any]:
    """Fit O2b on a validated training packet and retain only grid outputs."""

    reaction, offsets, terminal_labels, _ = _validate_packet(training, name="training")
    adapter_input = _adapter_input(training)
    estimator, closure_hashes = _adapter_and_closure(ingest_root)
    coefficient = _finite_float(diffusion_coefficient, "diffusion_coefficient", positive=True)
    raw = estimator(
        adapter_input["state"],
        adapter_input["time"],
        adapter_input["reaction_coordinate"],
        adapter_input["regime_labels"],
        set_A=[0],
        set_B=[1],
        grid_min=TARGET_A,
        grid_max=TARGET_B,
        diffusion_coefficient=coefficient,
        segment_id=adapter_input["segment_id"],
        coordinate_layer="synthetic_scalar_double_well",
        coordinate_names=["x"],
        reaction_coordinate_name="x",
        grid_resolution=GRID_RESOLUTION,
        min_samples=MIN_SAMPLES,
        min_support_per_grid=MIN_SUPPORT_PER_GRID,
        min_transition_segments=MIN_TRANSITION_SEGMENTS,
        max_dt_relative_deviation=MAX_DT_RELATIVE_DEVIATION,
    )
    series = raw.get("series", {}) if isinstance(raw, Mapping) else {}
    status = str(raw.get("computation_status", "not_recorded"))
    q_grid = np.asarray(series["q_grid"], dtype=float) if status == "computed" and "q_grid" in series else None
    drift_grid = np.asarray(series["drift_estimate_grid"], dtype=float) if status == "computed" and "drift_estimate_grid" in series else None
    query_grid = np.asarray(series["query_grid"], dtype=float) if status == "computed" and "query_grid" in series else None
    raw_support = np.asarray(series["grid_support_count"]) if status == "computed" and "grid_support_count" in series else None
    grid_support = raw_support.astype(np.int64, copy=False) if raw_support is not None and raw_support.dtype.kind in {"i", "u"} else None
    query_grid_valid = query_grid is not None and query_grid.shape == (GRID_RESOLUTION,) and np.isfinite(query_grid).all() and np.allclose(query_grid, FROZEN_GRID, rtol=0.0, atol=1e-7)
    support_valid = raw_support is not None and raw_support.shape == (GRID_RESOLUTION,) and raw_support.dtype.kind in {"i", "u"} and np.isfinite(raw_support).all() and np.all(raw_support >= MIN_SUPPORT_PER_GRID)
    failure_reason = raw.get("failure_reason")
    if status == "computed":
        valid_output = (
            query_grid_valid
            and q_grid is not None and q_grid.shape == (GRID_RESOLUTION,) and np.isfinite(q_grid).all()
            and np.all((q_grid >= 0.0) & (q_grid <= 1.0))
            and np.all(np.diff(q_grid) >= -1e-8)
            and np.isclose(q_grid[0], 0.0, rtol=0.0, atol=1e-7)
            and np.isclose(q_grid[-1], 1.0, rtol=0.0, atol=1e-7)
            and drift_grid is not None and drift_grid.shape == (GRID_RESOLUTION,) and np.isfinite(drift_grid).all()
            and support_valid
        )
        if not valid_output:
            status = "invalid"
            failure_reason = "computed_q_grid_contract_violation"
            q_grid = drift_grid = grid_support = None
    return {
        "computation_status": status,
        "failure_reason": failure_reason,
        "diffusion_coefficient": coefficient,
        "q_grid": q_grid,
        "query_grid": query_grid,
        "drift_estimate_grid": drift_grid,
        "grid_support_count": grid_support,
        "provenance": _plain(raw.get("provenance", {})),
        "certificate": {
            "schema_version": raw.get("schema_version"),
            "measurement_validity": raw.get("measurement_validity"),
            "claim_status": raw.get("claim_status"),
        },
        "ingest_closure_hashes": closure_hashes,
        "training_reaction_sha256": _sha256_array(reaction.astype(np.float64)),
        "training_offsets_sha256": _sha256_array(offsets.astype(np.int64)),
        "training_terminal_labels_sha256": _sha256_array(terminal_labels.astype(np.int8)),
    }


def _validated_q_grid(q_grid: Sequence[float] | np.ndarray) -> np.ndarray:
    grid = np.asarray(q_grid, dtype=float).reshape(-1)
    if grid.shape != (GRID_RESOLUTION,) or not np.isfinite(grid).all():
        raise ValueError("q_grid must be a finite 65-point vector")
    if not np.all((grid >= 0.0) & (grid <= 1.0)) or not np.all(np.diff(grid) >= -1e-8):
        raise ValueError("q_grid must be monotone and lie in [0, 1]")
    if not np.isclose(grid[0], 0.0, rtol=0.0, atol=1e-7) or not np.isclose(grid[-1], 1.0, rtol=0.0, atol=1e-7):
        raise ValueError("q_grid must have boundary values 0 and 1")
    return grid


def predict_grid(q_grid: Sequence[float] | np.ndarray, queries: Sequence[float] | np.ndarray) -> np.ndarray:
    """Interpolate an adapter q-grid at in-grid query points only."""

    grid = _validated_q_grid(q_grid)
    values = np.asarray(queries, dtype=float)
    if not np.isfinite(values).all() or np.any((values < TARGET_A) | (values > TARGET_B)):
        raise ValueError("queries must be finite and inside [-1, 1]")
    return np.interp(values, np.linspace(TARGET_A, TARGET_B, GRID_RESOLUTION), grid)


def _counts_from_packet(packet: Mapping[str, Any]) -> dict[str, int]:
    _, offsets, labels, _ = _validate_packet(packet, name="heldout")
    counts = {"n_A": int(np.sum(labels == 0)), "n_B": int(np.sum(labels == 1)), "n_unresolved": int(np.sum(labels < 0))}
    counts["n_total"] = int(offsets.size - 1)
    if sum(counts[key] for key in ("n_A", "n_B", "n_unresolved")) != counts["n_total"]:
        raise RuntimeError("heldout count partition is invalid")
    return counts


def _cp_lower(successes: int, total: int, alpha: float) -> float:
    return 0.0 if successes == 0 else float(beta.ppf(alpha, successes, total - successes + 1))


def _cp_upper(successes: int, total: int, alpha: float) -> float:
    return 1.0 if successes == total else float(beta.ppf(1.0 - alpha, successes + 1, total - successes))


def score_counts(predicted: float, counts: Mapping[str, int], *, alpha: float = CP_ALPHA) -> dict[str, Any]:
    """Score one prediction against held-out A/B/U counts with CP bounds."""

    p = _finite_float(predicted, "predicted")
    if p < 0.0 or p > 1.0:
        raise ValueError("predicted must lie in [0, 1]")
    values = {key: _integer(counts.get(key), key, minimum=0) for key in ("n_A", "n_B", "n_unresolved")}
    total = sum(values.values())
    if total < 1:
        raise ValueError("heldout counts must have positive total")
    if "n_total" in counts:
        declared_total = _integer(counts["n_total"], "n_total", minimum=0)
        if declared_total != total:
            raise ValueError("n_total does not match n_A+n_B+n_unresolved")
    requested_alpha = _finite_float(alpha, "alpha", positive=True)
    if requested_alpha >= 1.0:
        raise ValueError("alpha must be below one")
    n_a, n_b, n_u = values["n_A"], values["n_B"], values["n_unresolved"]
    p_not_a_successes = n_b + n_u
    lower_b = _cp_lower(n_b, total, requested_alpha)
    upper_not_a = _cp_upper(p_not_a_successes, total, requested_alpha)
    upper_unresolved = _cp_upper(n_u, total, requested_alpha)
    resolved_loss = n_b * (1.0 - p) ** 2 + n_a * p**2
    low_loss = (resolved_loss + n_u * min(p**2, (1.0 - p) ** 2)) / total
    high_loss = (resolved_loss + n_u * max(p**2, (1.0 - p) ** 2)) / total
    return {
        **values,
        "n_total": total,
        "predicted": p,
        "alpha": requested_alpha,
        "p_B_plugin": n_b / total,
        "p_not_A_plugin": (n_b + n_u) / total,
        "p_unresolved_plugin": n_u / total,
        "lower_p_B": lower_b,
        "upper_p_not_A": upper_not_a,
        "upper_p_unresolved": upper_unresolved,
        "brier_lower": low_loss,
        "brier_upper": high_loss,
    }


def continuous_q(queries: Sequence[float] | np.ndarray) -> np.ndarray:
    """Compute the continuous double-well committor by independent quadrature."""

    values = np.asarray(queries, dtype=float)
    if not np.isfinite(values).all() or np.any((values < TARGET_A) | (values > TARGET_B)):
        raise ValueError("queries must be finite and inside [-1, 1]")

    def integrand(x: float) -> float:
        potential = x**4 / 4.0 - x**2 / 2.0
        return float(np.exp(potential / D))

    denominator, _ = quad(integrand, TARGET_A, TARGET_B, epsabs=1e-12, epsrel=1e-12, limit=200)
    flat = values.reshape(-1)
    result = np.empty(flat.size, dtype=float)
    for index, value in enumerate(flat):
        numerator, _ = quad(integrand, TARGET_A, float(value), epsabs=1e-12, epsrel=1e-12, limit=200)
        result[index] = numerator / denominator
    return result.reshape(values.shape)


def _fit_query_rows(fits: Sequence[Mapping[str, Any]], truth: np.ndarray) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for fit in fits:
        fit_index = int(fit.get("fit_index", len(rows)))
        label = str(fit.get("convention", "correct"))
        q_grid = fit.get("q_grid")
        if q_grid is None or str(fit.get("computation_status")) != "computed":
            rows.extend({"fit_index": fit_index, "convention": label, "query_index": i, "status": str(fit.get("computation_status")), "failure_reason": fit.get("failure_reason"), "prediction": None, "truth": float(truth[i]), "absolute_error": None} for i in range(len(truth)))
            continue
        try:
            predictions = predict_grid(q_grid, STARTS)
        except ValueError:
            rows.extend({"fit_index": fit_index, "convention": label, "query_index": i, "status": "invalid_output", "failure_reason": "q_grid_contract_violation", "prediction": None, "truth": float(truth[i]), "absolute_error": None} for i in range(len(truth)))
            continue
        rows.extend({"fit_index": fit_index, "convention": label, "query_index": i, "status": "computed", "failure_reason": None, "prediction": float(predictions[i]), "truth": float(truth[i]), "absolute_error": abs(float(predictions[i]) - float(truth[i]))} for i in range(len(truth)))
    return rows


def summarize(
    fits: Sequence[Mapping[str, Any]],
    heldout: Sequence[Mapping[str, Any]],
    *,
    truth: Sequence[float] | np.ndarray | None = None,
) -> dict[str, Any]:
    """Summarize fit/query errors, count envelopes and the fixed recovery screen."""

    q_truth = continuous_q(STARTS) if truth is None else np.asarray(truth, dtype=float).reshape(-1)
    if q_truth.shape != (len(STARTS),) or not np.isfinite(q_truth).all():
        raise ValueError("truth must be a finite vector aligned with the five fixed starts")
    if len(heldout) != len(STARTS):
        raise ValueError("heldout must contain one count mapping per fixed query")
    known_conventions = {"correct", "wrong_convention"}
    unknown = [str(fit.get("convention")) for fit in fits if str(fit.get("convention")) not in known_conventions]
    if unknown:
        raise ValueError(f"unknown fit convention: {unknown[0]}")
    for fit in fits:
        if "fit_index" not in fit:
            raise ValueError("each fit must have an explicit fit_index")
        fit_index = _integer(fit["fit_index"], "fit_index", minimum=0)
        if fit_index >= N_FITS:
            raise ValueError("fit_index must be in the frozen range 0..7")
        convention = str(fit["convention"])
        expected_coefficient = DIFFUSION_VARIANCE if convention == "correct" else WRONG_DIFFUSION_VARIANCE
        if "diffusion_coefficient" not in fit or not np.isclose(float(fit["diffusion_coefficient"]), expected_coefficient, rtol=0.0, atol=1e-12):
            raise ValueError(f"{convention} fit has the wrong diffusion coefficient")
    correct = [fit for fit in fits if str(fit["convention"]) == "correct"]
    wrong = [fit for fit in fits if str(fit.get("convention", "")) == "wrong_convention"]
    for label, group in (("correct", correct), ("wrong_convention", wrong)):
        fit_ids = [int(fit["fit_index"]) for fit in group if "fit_index" in fit]
        if len(fit_ids) != len(group) or len(set(fit_ids)) != len(fit_ids):
            raise ValueError(f"{label} fits must have unique fit_index values")
    expected_fit_ids = list(range(N_FITS))
    correct_fit_ids = sorted(int(fit["fit_index"]) for fit in correct)
    wrong_fit_ids = sorted(int(fit["fit_index"]) for fit in wrong)
    missing_correct_fit_ids = [fit_id for fit_id in expected_fit_ids if fit_id not in correct_fit_ids]
    missing_wrong_fit_ids = [fit_id for fit_id in expected_fit_ids if fit_id not in wrong_fit_ids]
    fit_id_completeness = {
        "expected_fit_ids": expected_fit_ids,
        "correct_fit_ids": correct_fit_ids,
        "wrong_convention_fit_ids": wrong_fit_ids,
        "missing_correct_fit_ids": missing_correct_fit_ids,
        "missing_wrong_convention_fit_ids": missing_wrong_fit_ids,
        "complete": not missing_correct_fit_ids and not missing_wrong_fit_ids,
    }
    correct_rows = _fit_query_rows(correct, q_truth)
    wrong_rows = _fit_query_rows(wrong, q_truth)
    supported = [row for row in correct_rows if row["status"] == "computed" and row["absolute_error"] is not None]
    if supported and any(float(row["absolute_error"]) > RECOVERY_TOLERANCE for row in supported):
        recovery_decision = "FAIL"
    elif len(supported) == N_FITS * len(STARTS):
        recovery_decision = "PASS"
    else:
        recovery_decision = "INCONCLUSIVE"

    count_rows: list[dict[str, Any]] = []
    oracle_rows: list[dict[str, Any]] = []
    baseline_rows: list[dict[str, Any]] = []
    for query_index, counts in enumerate(heldout):
        baseline_rows.append({"query_index": query_index, "truth": float(q_truth[query_index]), **score_counts(CONSTANT_BASELINE, counts)})
        oracle_rows.append({"query_index": query_index, "truth": float(q_truth[query_index]), "prediction": float(q_truth[query_index]), "convention": "oracle_continuous_q", **score_counts(float(q_truth[query_index]), counts)})
        for row in correct_rows + wrong_rows:
            if row["query_index"] != query_index or row["prediction"] is None:
                continue
            count_rows.append({**row, **score_counts(float(row["prediction"]), counts)})
    grid = np.linspace(TARGET_A, TARGET_B, GRID_RESOLUTION)
    grid_truth = continuous_q(grid)
    grid_rows: list[dict[str, Any]] = []
    for fit in fits:
        q_grid = fit.get("q_grid")
        if q_grid is None or str(fit.get("computation_status")) != "computed":
            grid_rows.append({"fit_index": int(fit.get("fit_index", -1)), "convention": str(fit.get("convention", "unknown")), "status": str(fit.get("computation_status")), "mae": None, "rmse": None, "max_abs_error": None, "min_grid_step": None, "q_min": None, "q_max": None, "min_grid_support": None, "left_endpoint_abs_error": None, "right_endpoint_abs_error": None, "monotonicity_violation": None})
            continue
        values = np.asarray(q_grid, dtype=float).reshape(-1)
        try:
            values = _validated_q_grid(values)
        except ValueError:
            grid_rows.append({"fit_index": int(fit.get("fit_index", -1)), "convention": str(fit.get("convention", "unknown")), "status": "invalid_output", "mae": None, "rmse": None, "max_abs_error": None, "min_grid_step": None, "q_min": None, "q_max": None, "min_grid_support": None, "left_endpoint_abs_error": None, "right_endpoint_abs_error": None, "monotonicity_violation": None})
            continue
        support_values = fit.get("grid_support_count")
        support_min = int(np.min(np.asarray(support_values))) if support_values is not None else None
        error = values - grid_truth
        grid_rows.append({"fit_index": int(fit.get("fit_index", -1)), "convention": str(fit.get("convention", "unknown")), "status": "computed", "mae": float(np.mean(np.abs(error))), "rmse": float(np.sqrt(np.mean(error**2))), "max_abs_error": float(np.max(np.abs(error))), "min_grid_step": float(np.min(np.diff(values))), "q_min": float(np.min(values)), "q_max": float(np.max(values)), "min_grid_support": support_min, "left_endpoint_abs_error": abs(float(values[0])), "right_endpoint_abs_error": abs(float(values[-1]) - 1.0), "monotonicity_violation": float(max(0.0, -float(np.min(np.diff(values)))))})
    return {
        "recovery_decision": recovery_decision,
        "recovery_tolerance": RECOVERY_TOLERANCE,
        "correct_fit_query_rows": correct_rows,
        "wrong_convention_fit_query_rows": wrong_rows,
        "n_correct_supported_predictions": len(supported),
        "n_correct_expected_predictions": N_FITS * len(STARTS),
        "max_correct_absolute_error": max((float(row["absolute_error"]) for row in supported), default=None),
        "fit_id_completeness": fit_id_completeness,
        "report_status": "complete" if fit_id_completeness["complete"] else "INCONCLUSIVE",
        "all_grid_metrics": grid_rows,
        "heldout_score_rows": count_rows,
        "heldout_oracle_rows": oracle_rows,
        "constant_baseline_rows": baseline_rows,
        "heldout_cp_tail_alpha": CP_ALPHA,
        "heldout_count_pools_reused_across_fits": True,
        "fit_interval_claim": "none",
    }


def _save_npz_once(path: Path, packet: Mapping[str, Any]) -> str:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing artifact: {path}")
    metadata = {
        key: packet[key]
        for key in ("n_paths", "n_steps", "dt", "horizon", "D", "seed", "rng_type", "absorption", "overshoot_retained")
        if key in packet
    }
    with path.open("xb") as handle:
        np.savez_compressed(
            handle,
            reaction=np.asarray(packet["reaction"], dtype=np.float64),
            offsets=np.asarray(packet["offsets"], dtype=np.int64),
            terminal_labels=np.asarray(packet["terminal_labels"], dtype=np.int8),
            path_starts=np.asarray(packet["path_starts"], dtype=np.float64),
            metadata_json=np.asarray(json.dumps(_plain(metadata), sort_keys=True)),
        )
    return _sha256_file(path)


def _protocol_hash(ingest_root: Path) -> tuple[str, str | None]:
    path = ingest_root / "project" / "astra" / "ndt_trans_adapter_001_20260907" / "protocol.md"
    if path.is_file():
        return _sha256_file(path), str(path)
    raise ValueError(f"frozen protocol is missing under ingest_root: {path}")


def _read_frozen_spec(path: str | Path) -> dict[str, Any]:
    spec_path = Path(path).expanduser().resolve()
    with spec_path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    supplied = loaded.get("spec") if isinstance(loaded, Mapping) and "spec" in loaded else loaded
    if supplied != build_spec():
        raise ValueError("supplied --spec does not match the frozen specification")
    return supplied


def run_benchmark(*, output_dir: str | Path, ingest_root: str | Path, spec_path: str | Path | None = None) -> dict[str, Any]:
    """Run the frozen primary benchmark and write artifacts exactly once."""

    out = Path(output_dir).expanduser().resolve()
    root = Path(ingest_root).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    spec = build_spec()
    if spec_path is not None:
        _read_frozen_spec(spec_path)
    expected = [out / "benchmark.json", *(out / f"training_fit_{i:02d}.npz" for i in range(N_FITS))]
    existing = [path for path in expected if path.exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite existing artifacts: {existing[0]}")
    adapter_source, closure_hashes = _adapter_and_closure(root)
    del adapter_source
    protocol_sha256, protocol_path = _protocol_hash(root)
    fits: list[dict[str, Any]] = []
    for fit_index in range(N_FITS):
        seed = np.random.SeedSequence([ROOT_ENTROPY, 0, fit_index])
        starts = np.resize(np.asarray(STARTS, dtype=float), N_TRAIN_PATHS)
        packet = simulate_paths(starts, seed=seed)
        artifact = _save_npz_once(out / f"training_fit_{fit_index:02d}.npz", packet)
        for convention, coefficient in (("correct", DIFFUSION_VARIANCE), ("wrong_convention", WRONG_DIFFUSION_VARIANCE)):
            fit = fit_adapter(packet, ingest_root=root, diffusion_coefficient=coefficient)
            fit["fit_index"] = fit_index
            fit["convention"] = convention
            fit["training_artifact"] = f"training_fit_{fit_index:02d}.npz"
            fit["training_artifact_sha256"] = artifact
            fits.append(fit)
    heldout: list[dict[str, Any]] = []
    for query_index, start in enumerate(STARTS):
        seed = np.random.SeedSequence([ROOT_ENTROPY, 1, query_index])
        count_packet = simulate_counts(float(start), n_paths=N_HELDOUT_PATHS, seed=seed)
        heldout.append({
            "query_index": query_index,
            "start": float(start),
            "seed": count_packet["seed"],
            "n_paths": count_packet["n_paths"],
            "n_steps": count_packet["n_steps"],
            "dt": count_packet["dt"],
            "horizon": count_packet["horizon"],
            "D": count_packet["D"],
            "rng_type": count_packet["rng_type"],
            "absorption": count_packet["absorption"],
            "counts": {key: count_packet[key] for key in ("n_A", "n_B", "n_unresolved", "n_total")},
        })
    summary = summarize(fits, [row["counts"] for row in heldout])
    source_path = Path(__file__).resolve()
    source_sha = _sha256_file(source_path)
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "spec": spec,
        "spec_sha256": spec_hash(spec),
        "protocol_sha256": protocol_sha256,
        "protocol_path": protocol_path,
        "source_module_sha256": source_sha,
        "ingest_closure_hashes": closure_hashes,
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "scipy": __import__("scipy").__version__, "platform": platform.platform()},
        "fit_seed_contract": "SeedSequence([2026090702, 0, fit_index])",
        "heldout_seed_contract": "SeedSequence([2026090702, 1, query_index])",
        "heldout": heldout,
        "fits": fits,
        "summary": summary,
        "scientific_status": "bounded synthetic comparison; no production or biological qualification",
    }
    with (out / "benchmark.json").open("x", encoding="utf-8") as handle:
        json.dump(_plain(result), handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec-only", action="store_true", help="print the frozen specification without simulation")
    parser.add_argument("--spec", type=Path, help="frozen spec JSON to validate before running")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--ingest-root", type=Path)
    args = parser.parse_args(argv)
    if args.spec_only:
        payload = {"spec": build_spec(), "spec_sha256": spec_hash()}
        if args.output_dir is not None:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            path = args.output_dir / "spec.json"
            if path.exists():
                raise FileExistsError(f"refusing to overwrite existing artifact: {path}")
            with path.open("x", encoding="utf-8") as handle:
                json.dump(_plain(payload), handle, indent=2, sort_keys=True)
                handle.write("\n")
        print(json.dumps(_plain(payload), indent=2, sort_keys=True))
        return 0
    if args.spec is None or args.output_dir is None or args.ingest_root is None:
        parser.error("--spec requires --output-dir and --ingest-root; use --spec-only for the frozen spec")
    result = run_benchmark(output_dir=args.output_dir, ingest_root=args.ingest_root, spec_path=args.spec)
    print(json.dumps({"output_dir": str(Path(args.output_dir).resolve()), "spec_sha256": result["spec_sha256"], "recovery_decision": result["summary"]["recovery_decision"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
