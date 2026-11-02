"""Bounded sample-size convergence study for the unchanged TRANS O2b law.

This is analysis-owned synthetic validation.  It reuses the frozen ADAPTER-001
Euler path generator, archives independent raw 512-path chunks, and evaluates
the same 65-bin local law from sufficient statistics.  The streaming evaluator
does not replace the ingest adapter and this module makes no production or
biological claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from . import trans_adapter_benchmark as adapter001


SCHEMA_VERSION = "nmd_analysis.trans_adapter_convergence.v1"
PROTOCOL_VERSION = "ndt_trans_adapter_002_20260907.v1"
ROOT_ENTROPY = 2_026_090_703
CHUNK_PATHS = 512
N_CHUNKS = 16
N_REPS = 16
PREFIX_LEVELS = (512, 2048, 8192)
CONTROL_RESOLUTIONS = (65, 129, 257)
GRID_RESOLUTION = adapter001.GRID_RESOLUTION
MIN_SUPPORT_PER_GRID = adapter001.MIN_SUPPORT_PER_GRID
MIN_TRANSITION_SEGMENTS = adapter001.MIN_TRANSITION_SEGMENTS
DIFFUSION_VARIANCE = adapter001.DIFFUSION_VARIANCE
RECOVERY_TOLERANCE = adapter001.RECOVERY_TOLERANCE
DRIFT_TOLERANCE = 2e-6
Q_TOLERANCE = 2e-7
D = adapter001.D
DT = adapter001.DT
HORIZON = adapter001.HORIZON
TARGET_A = adapter001.TARGET_A
TARGET_B = adapter001.TARGET_B
STARTS = adapter001.STARTS
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


def _integer(value: Any, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer")
    result = int(value)
    if result < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return result


def build_spec() -> dict[str, Any]:
    """Return the frozen TRANS-ADAPTER-002 numeric and sampling contract."""

    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "model": {
            "D": D,
            "diffusion_variance_rate": DIFFUSION_VARIANCE,
            "sde": "dX=(X-X^3)dt+sqrt(.4)dW",
            "drift": "b(x)=x-x^3",
            "dt_sec": DT,
            "horizon_sec": HORIZON,
            "target_A": "x <= -1",
            "target_B": "x >= 1",
            "absorption": "endpoint first exit; time-zero targets included",
            "bridge_correction": False,
        },
        "sampling": {
            "n_repetitions": N_REPS,
            "n_chunks_per_repetition": N_CHUNKS,
            "paths_per_chunk": CHUNK_PATHS,
            "prefix_levels": list(PREFIX_LEVELS),
            "nesting": "chunks 0 through j-1 are cumulative prefixes",
            "seed": "SeedSequence([2026090703, 0, rep, chunk])",
            "starts": "STARTS[(512*chunk+k) modulo 5]",
            "raw_storage": "compressed_npz per raw 512-path chunk; actual overshoots retained",
            "segments": "one contiguous independent segment per path",
        },
        "streaming": {
            "grid_min": TARGET_A,
            "grid_max": TARGET_B,
            "grid_resolution": GRID_RESOLUTION,
            "diffusion_coefficient": DIFFUSION_VARIANCE,
            "min_samples": adapter001.MIN_SAMPLES,
            "min_support_per_grid": MIN_SUPPORT_PER_GRID,
            "min_transition_segments": MIN_TRANSITION_SEGMENTS,
            "sufficient_statistics": ["support", "drift_sum", "oracle_drift_sum"],
            "law": "same nearest-grid bins and trapezoidal potential/integral as O2b",
            "q_storage": "grid only; no q_series",
        },
        "controls": {
            "deterministic_grid_resolutions": list(CONTROL_RESOLUTIONS),
            "occupancy_oracle": "mean exact b(x) at observed source coordinates per 65-bin prefix",
            "decomposition": "q_est-q_occupancy, q_occupancy-q_grid_oracle, q_grid_oracle-q_continuous",
        },
        "evaluation": {
            "truth": "independent quadrature of exp((x^4/4-x^2/2)/.2)",
            "queries": list(STARTS),
            "recovery_level": 8192,
            "recovery_predictions": N_REPS * len(STARTS),
            "recovery_tolerance": RECOVERY_TOLERANCE,
            "equivalence_drift_tolerance": DRIFT_TOLERANCE,
            "equivalence_q_tolerance": Q_TOLERANCE,
            "fit_interval_claim": "none; sixteen repetitions are finite descriptive replicates",
        },
    }


def spec_hash(spec: Mapping[str, Any] | None = None) -> str:
    return _sha256_bytes(_canonical_json(build_spec() if spec is None else spec))


def _rep_chunk(rep: Any, chunk: Any) -> tuple[int, int]:
    rep_i = _integer(rep, "rep", minimum=0)
    chunk_i = _integer(chunk, "chunk", minimum=0)
    if rep_i >= N_REPS:
        raise ValueError(f"rep must be in 0..{N_REPS - 1}")
    if chunk_i >= N_CHUNKS:
        raise ValueError(f"chunk must be in 0..{N_CHUNKS - 1}")
    return rep_i, chunk_i


def chunk_seed(rep: int, chunk: int) -> np.random.SeedSequence:
    """Return the exact independent seed for one primary chunk."""

    rep_i, chunk_i = _rep_chunk(rep, chunk)
    return np.random.SeedSequence([ROOT_ENTROPY, 0, rep_i, chunk_i])


def chunk_starts(rep: int, chunk: int, *, n_paths: int = CHUNK_PATHS) -> np.ndarray:
    """Return starts using the global path index within one repetition."""

    _, chunk_i = _rep_chunk(rep, chunk)
    count = _integer(n_paths, "n_paths", minimum=1)
    global_indices = chunk_i * CHUNK_PATHS + np.arange(count, dtype=np.int64)
    return np.asarray(STARTS, dtype=float)[global_indices % len(STARTS)]


def simulate_chunk(
    rep: int,
    chunk: int,
    *,
    dt: float = DT,
    horizon: float = HORIZON,
) -> dict[str, Any]:
    """Generate one exact 512-path raw chunk using ADAPTER-001 simulation."""

    rep_i, chunk_i = _rep_chunk(rep, chunk)
    starts = chunk_starts(rep_i, chunk_i)
    packet = adapter001.simulate_paths(starts, seed=chunk_seed(rep_i, chunk_i), dt=dt, horizon=horizon)
    packet.update(
        {
            "rep": rep_i,
            "chunk": chunk_i,
            "global_path_offset": chunk_i * CHUNK_PATHS,
            "seed_contract": "SeedSequence([2026090703, 0, rep, chunk])",
        }
    )
    return packet


def _increment_data(packet: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return source x, dx/dt, exact b(source), and path labels without joins."""

    reaction, offsets, labels, _ = adapter001._validate_packet(packet, name="chunk")
    source_parts: list[np.ndarray] = []
    increment_parts: list[np.ndarray] = []
    dt_parts: list[np.ndarray] = []
    time = packet.get("time")
    if time is not None:
        supplied_time = np.asarray(time, dtype=float).reshape(-1)
        if supplied_time.shape != reaction.shape or not np.isfinite(supplied_time).all():
            raise ValueError("chunk.time must be finite and aligned with reaction")
    else:
        supplied_time = None
    for start, end in zip(offsets[:-1], offsets[1:]):
        if supplied_time is not None and not np.isclose(supplied_time[start], 0.0, rtol=0.0, atol=1e-12):
            raise ValueError("chunk.time must reset to zero for each path")
        if end - start <= 1:
            continue
        indices = np.arange(start, end - 1, dtype=np.int64)
        if supplied_time is None:
            # Match adapter001.pack_training: reconstruct each segment's time
            # from arange before taking differences, preserving its floating
            # point increments rather than relabeling them to a scalar DT.
            dts = np.diff(np.arange(int(end - start), dtype=float) * DT)
        else:
            dts = np.diff(supplied_time[start:end])
            if not np.allclose(dts, DT, rtol=0.0, atol=1e-12):
                raise ValueError("chunk increments must use the frozen regular dt")
        source_parts.append(reaction[indices])
        increment_parts.append(np.diff(reaction[start:end]))
        dt_parts.append(dts)
    if source_parts:
        source = np.concatenate(source_parts)
        increments = np.concatenate(increment_parts)
        dts = np.concatenate(dt_parts)
    else:
        source = np.empty(0, dtype=float)
        increments = np.empty(0, dtype=float)
        dts = np.empty(0, dtype=float)
    if not np.all(np.isfinite(dts)) or np.any(dts <= 0):
        raise ValueError("chunk increments have invalid dt")
    return source, increments / dts, source - source**3, labels


def compute_chunk_statistics(
    packet: Mapping[str, Any],
    *,
    grid_resolution: int = GRID_RESOLUTION,
) -> dict[str, Any]:
    """Accumulate O2b bin statistics for one raw chunk."""

    resolution = _integer(grid_resolution, "grid_resolution", minimum=GRID_RESOLUTION)
    if resolution % 2 == 0:
        raise ValueError("grid_resolution must be odd")
    grid = np.linspace(TARGET_A, TARGET_B, resolution, dtype=float)
    source, drift_values, true_drift_values, labels = _increment_data(packet)
    in_bounds = (source >= TARGET_A) & (source <= TARGET_B)
    source = source[in_bounds]
    drift_values = drift_values[in_bounds]
    true_drift_values = true_drift_values[in_bounds]
    nearest = np.argmin(np.abs(source[:, None] - grid[None, :]), axis=1)
    support = np.bincount(nearest, minlength=resolution).astype(np.int64)
    drift_sum = np.bincount(nearest, weights=drift_values, minlength=resolution).astype(float)
    oracle_drift_sum = np.bincount(nearest, weights=true_drift_values, minlength=resolution).astype(float)
    n_a = int(np.sum(labels == 0))
    n_b = int(np.sum(labels == 1))
    n_unresolved = int(np.sum(labels < 0))
    result = {
        "grid_resolution": resolution,
        "query_grid": grid,
        "support": support,
        "drift_sum": drift_sum,
        "oracle_drift_sum": oracle_drift_sum,
        "n_paths": int(labels.size),
        "n_rows": int(np.asarray(packet["reaction"]).size),
        "n_A": n_a,
        "n_B": n_b,
        "n_unresolved": n_unresolved,
        "n_total": int(labels.size),
        "n_increment_pairs": int(source.size),
        "n_transition_segments": int(np.sum(labels >= 0)),
        "n_segments_with_A_first_hit": n_a,
        "n_segments_with_B_first_hit": n_b,
    }
    for key in ("rep", "chunk", "global_path_offset"):
        if key in packet:
            result[key] = int(packet[key])
    return result


def aggregate_statistics(stats: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Sum independent chunk statistics for one nested prefix."""

    entries = list(stats)
    if not entries:
        raise ValueError("at least one chunk statistic is required")
    resolution = _integer(entries[0].get("grid_resolution", GRID_RESOLUTION), "grid_resolution", minimum=GRID_RESOLUTION)
    grid_value = entries[0].get("query_grid")
    grid = np.linspace(TARGET_A, TARGET_B, resolution, dtype=float) if grid_value is None else np.asarray(grid_value, dtype=float).reshape(-1)
    if grid.shape != (resolution,) or not np.isfinite(grid).all() or not np.all(np.diff(grid) > 0):
        raise ValueError("chunk query_grid is malformed")
    arrays: dict[str, np.ndarray] = {}
    for key in ("support", "drift_sum", "oracle_drift_sum"):
        first = np.asarray(entries[0].get(key))
        if first.shape != (resolution,) or not np.isfinite(first).all() or (key == "support" and first.dtype.kind not in {"i", "u"}):
            raise ValueError(f"chunk {key} is malformed")
        arrays[key] = first.astype(np.float64 if key != "support" else np.int64, copy=True)
    for entry in entries[1:]:
        entry_grid_value = entry.get("query_grid")
        entry_grid = np.linspace(TARGET_A, TARGET_B, resolution, dtype=float) if entry_grid_value is None else np.asarray(entry_grid_value, dtype=float).reshape(-1)
        if int(entry.get("grid_resolution", resolution)) != resolution or entry_grid.shape != grid.shape or not np.array_equal(entry_grid, grid):
            raise ValueError("chunk statistics use different grids")
        for key in ("support", "drift_sum", "oracle_drift_sum"):
            values = np.asarray(entry.get(key))
            if values.shape != (resolution,) or not np.isfinite(values).all():
                raise ValueError(f"chunk {key} is malformed")
            if key == "support":
                if values.dtype.kind not in {"i", "u"}:
                    raise ValueError("support must be integer")
                arrays[key] += values.astype(np.int64)
            else:
                arrays[key] += values.astype(float)
    counts: dict[str, int] = {}
    for key in ("n_paths", "n_A", "n_B", "n_unresolved"):
        counts[key] = int(sum(_integer(entry.get(key), key, minimum=0) for entry in entries))
    counts["n_rows"] = int(sum(_integer(entry.get("n_rows", entry.get("n_paths")), "n_rows", minimum=1) for entry in entries))
    counts["n_increment_pairs"] = int(sum(_integer(entry.get("n_increment_pairs", np.sum(np.asarray(entry["support"]))), "n_increment_pairs", minimum=0) for entry in entries))
    counts["n_transition_segments"] = int(sum(_integer(entry.get("n_transition_segments", int(entry["n_A"]) + int(entry["n_B"])), "n_transition_segments", minimum=0) for entry in entries))
    counts["n_segments_with_A_first_hit"] = int(sum(_integer(entry.get("n_segments_with_A_first_hit", entry["n_A"]), "n_segments_with_A_first_hit", minimum=0) for entry in entries))
    counts["n_segments_with_B_first_hit"] = int(sum(_integer(entry.get("n_segments_with_B_first_hit", entry["n_B"]), "n_segments_with_B_first_hit", minimum=0) for entry in entries))
    counts["n_total"] = counts["n_paths"]
    if counts["n_A"] + counts["n_B"] + counts["n_unresolved"] != counts["n_total"]:
        raise ValueError("chunk outcome counts do not partition paths")
    result = {"grid_resolution": resolution, "query_grid": grid, **arrays, **counts, "n_chunks": len(entries)}
    indices = [entry.get("chunk") for entry in entries]
    reps = [entry.get("rep") for entry in entries]
    if all(index is not None for index in indices):
        chunk_indices = [_integer(index, "chunk", minimum=0) for index in indices]
        if chunk_indices != list(range(len(entries))):
            raise ValueError("cumulative chunks must be contiguous from chunk zero")
        result["chunk_indices"] = chunk_indices
    if all(rep is not None for rep in reps):
        rep_values = {_integer(rep, "rep", minimum=0) for rep in reps}
        if len(rep_values) != 1:
            raise ValueError("a prefix cannot combine repetitions")
        result["rep"] = rep_values.pop()
    return result


def integrate_drift(
    drift: Sequence[float] | np.ndarray,
    grid: Sequence[float] | np.ndarray,
    *,
    diffusion_coefficient: float = DIFFUSION_VARIANCE,
) -> np.ndarray:
    """Apply O2b's trapezoidal potential and committor integration."""

    grid = np.asarray(grid, dtype=float).reshape(-1)
    drift = np.asarray(drift, dtype=float).reshape(-1)
    coefficient = float(diffusion_coefficient)
    if grid.size < 2 or drift.shape != grid.shape or not np.isfinite(grid).all() or not np.isfinite(drift).all() or coefficient <= 0:
        raise ValueError("grid, drift and diffusion coefficient are malformed")
    spacing = np.diff(grid)
    if not np.all(spacing > 0):
        raise ValueError("grid must be strictly increasing")
    potential = np.concatenate(([0.0], np.cumsum(-0.5 * (drift[1:] + drift[:-1]) * spacing)))
    exponent = 2.0 * (potential - np.max(potential)) / coefficient
    integrand = np.exp(exponent)
    cumulative = np.concatenate(([0.0], np.cumsum(0.5 * (integrand[1:] + integrand[:-1]) * spacing)))
    total = float(cumulative[-1])
    if not np.isfinite(total) or total <= 0:
        raise ValueError("nonfinite committor quadrature")
    return cumulative / total


def _grid_metrics(values: np.ndarray, truth: np.ndarray) -> dict[str, float]:
    error = np.asarray(values, dtype=float) - np.asarray(truth, dtype=float)
    return {
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "max_abs_error": float(np.max(np.abs(error))),
        "mean_signed_error": float(np.mean(error)),
    }


def deterministic_grid_control(resolution: int) -> dict[str, Any]:
    """Integrate exact b(x) on a known grid to isolate grid quadrature error."""

    resolution_i = _integer(resolution, "resolution", minimum=GRID_RESOLUTION)
    if resolution_i not in CONTROL_RESOLUTIONS:
        raise ValueError(f"resolution must be one of {CONTROL_RESOLUTIONS}")
    grid = np.linspace(TARGET_A, TARGET_B, resolution_i, dtype=float)
    drift = grid - grid**3
    q_grid = integrate_drift(drift, grid)
    grid_truth = adapter001.continuous_q(grid)
    query_truth = adapter001.continuous_q(STARTS)
    query_predictions = np.interp(STARTS, grid, q_grid)
    return {
        "grid_resolution": resolution_i,
        "query_grid": grid,
        "drift": drift,
        "q_grid": q_grid,
        "query_predictions": query_predictions,
        "query_truth": query_truth,
        "query_errors": query_predictions - query_truth,
        "all_grid_metrics": _grid_metrics(q_grid, grid_truth),
        "query_metrics": _grid_metrics(query_predictions, query_truth),
        "status": "computed",
        "failure_reason": None,
    }


def evaluate_streaming(stats: Mapping[str, Any]) -> dict[str, Any]:
    """Apply the exact 65-bin O2b law to aggregated sufficient statistics."""

    resolution = _integer(stats.get("grid_resolution", GRID_RESOLUTION), "grid_resolution", minimum=GRID_RESOLUTION)
    if resolution != GRID_RESOLUTION:
        raise ValueError("streaming O2b evaluation requires the frozen 65-point grid")
    grid_value = stats.get("query_grid")
    grid = np.linspace(TARGET_A, TARGET_B, resolution, dtype=float) if grid_value is None else np.asarray(grid_value, dtype=float).reshape(-1)
    support = np.asarray(stats.get("support"))
    drift_sum = np.asarray(stats.get("drift_sum"), dtype=float).reshape(-1)
    oracle_sum = np.asarray(stats.get("oracle_drift_sum"), dtype=float).reshape(-1)
    if grid.shape != (resolution,) or not np.isfinite(grid).all() or not np.array_equal(grid, FROZEN_GRID):
        raise ValueError("streaming query_grid must equal the frozen 65-point grid")
    if support.shape != (resolution,) or support.dtype.kind not in {"i", "u"} or not np.isfinite(support).all() or np.any(support < 0):
        raise ValueError("streaming support is malformed")
    if drift_sum.shape != (resolution,) or oracle_sum.shape != (resolution,) or not np.isfinite(drift_sum).all() or not np.isfinite(oracle_sum).all():
        raise ValueError("streaming drift sums are malformed")
    n_paths = _integer(stats.get("n_paths"), "n_paths", minimum=1)
    n_a = _integer(stats.get("n_A"), "n_A", minimum=0)
    n_b = _integer(stats.get("n_B"), "n_B", minimum=0)
    n_u = _integer(stats.get("n_unresolved"), "n_unresolved", minimum=0)
    n_rows = _integer(stats.get("n_rows", n_paths), "n_rows", minimum=1)
    if n_a + n_b + n_u != n_paths:
        raise ValueError("streaming counts do not partition paths")
    drift = np.divide(drift_sum, support, out=np.full(resolution, np.nan), where=support > 0)
    occupancy_drift = np.divide(oracle_sum, support, out=np.full(resolution, np.nan), where=support > 0)
    q_grid_oracle = integrate_drift(grid - grid**3, grid)
    query_truth = adapter001.continuous_q(STARTS)
    q_grid: np.ndarray | None = None
    occupancy_q_grid: np.ndarray | None = None
    status = "computed"
    failure_reason: str | None = None
    n_transition = _integer(stats.get("n_transition_segments", n_a + n_b), "n_transition_segments", minimum=0)
    if n_rows < adapter001.MIN_SAMPLES:
        status = "insufficient_support"
        failure_reason = "insufficient_samples"
    elif n_transition < MIN_TRANSITION_SEGMENTS or n_a == 0 or n_b == 0:
        status = "not_testable"
        failure_reason = "insufficient_independent_A_B_transition_segments"
    elif _integer(stats.get("n_increment_pairs", int(np.sum(support))), "n_increment_pairs", minimum=0) < MIN_SUPPORT_PER_GRID:
        status = "insufficient_support"
        failure_reason = "insufficient_reaction_coordinate_increment_pairs"
    elif np.any(support < MIN_SUPPORT_PER_GRID):
        status = "insufficient_support"
        failure_reason = "dense_query_grid_has_under_supported_points"
    else:
        try:
            q_grid = integrate_drift(drift, grid)
            occupancy_q_grid = integrate_drift(occupancy_drift, grid)
        except ValueError:
            status = "invalid"
            failure_reason = "nonfinite_committor_quadrature"
    result: dict[str, Any] = {
        "status": status,
        "computation_status": status,
        "failure_reason": failure_reason,
        "grid_resolution": resolution,
        "query_grid": grid,
        "support": support.astype(np.int64, copy=True),
        "drift": drift,
        "occupancy_drift": occupancy_drift,
        "q_grid": q_grid,
        "occupancy_q_grid": occupancy_q_grid,
        "q_grid_oracle": q_grid_oracle,
        "n_paths": n_paths,
        "n_rows": n_rows,
        "n_A": n_a,
        "n_B": n_b,
        "n_unresolved": n_u,
        "n_total": n_paths,
        "n_chunks": int(stats.get("n_chunks", 1)),
        "query_truth": query_truth,
        "oracle_query_predictions": np.interp(STARTS, grid, q_grid_oracle),
        "all_grid_metrics": None,
        "query_metrics": None,
        "query_predictions": None,
        "query_errors": None,
        "decomposition": None,
    }
    if "rep" in stats:
        result["rep"] = _integer(stats["rep"], "rep", minimum=0)
    if "chunk_indices" in stats:
        result["chunk_indices"] = list(stats["chunk_indices"])
    if q_grid is not None and occupancy_q_grid is not None:
        query_predictions = np.interp(STARTS, grid, q_grid)
        occupancy_predictions = np.interp(STARTS, grid, occupancy_q_grid)
        oracle_predictions = np.interp(STARTS, grid, q_grid_oracle)
        result.update(
            {
                "query_predictions": query_predictions,
                "query_errors": query_predictions - query_truth,
                "all_grid_metrics": _grid_metrics(q_grid, adapter001.continuous_q(grid)),
                "query_metrics": _grid_metrics(query_predictions, query_truth),
                "decomposition": {
                    "q_est_minus_q_occupancy": query_predictions - occupancy_predictions,
                    "q_occupancy_minus_q_grid_oracle": occupancy_predictions - oracle_predictions,
                    "q_grid_oracle_minus_q_continuous": oracle_predictions - query_truth,
                },
            }
        )
    return result


def pack_chunk(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Build the unchanged adapter input for one chunk."""

    return adapter001.pack_training(packet)


def fit_adapter_reference(packet: Mapping[str, Any], *, ingest_root: str | Path) -> dict[str, Any]:
    """Run unchanged O2b on a nonprimary-sized raw chunk for equivalence."""

    return adapter001.fit_adapter(packet, ingest_root=ingest_root, diffusion_coefficient=DIFFUSION_VARIANCE)


def compare_streaming_to_adapter(
    packet: Mapping[str, Any],
    *,
    ingest_root: str | Path,
    streaming: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare streaming 65-bin statistics with unchanged O2b on 512 paths."""

    stats = compute_chunk_statistics(packet)
    aggregate = aggregate_statistics([stats])
    streamed = evaluate_streaming(aggregate) if streaming is None else dict(streaming)
    reference = fit_adapter_reference(packet, ingest_root=ingest_root)
    ref_status = str(reference.get("computation_status"))
    ref_reason = reference.get("failure_reason")
    status_equal = streamed["status"] == ref_status
    reason_equal = streamed["failure_reason"] == ref_reason
    support_equal = False
    drift_max: float | None = None
    q_max: float | None = None
    numerical_equal = False
    if status_equal and ref_status == "computed":
        ref_support = np.asarray(reference.get("grid_support_count"))
        ref_drift = np.asarray(reference.get("drift_estimate_grid"), dtype=float)
        ref_q = np.asarray(reference.get("q_grid"), dtype=float)
        support_equal = ref_support.shape == streamed["support"].shape and np.array_equal(ref_support, streamed["support"])
        if support_equal and ref_drift.shape == streamed["drift"].shape and ref_q.shape == streamed["q_grid"].shape:
            drift_max = float(np.max(np.abs(ref_drift - streamed["drift"])))
            q_max = float(np.max(np.abs(ref_q - streamed["q_grid"])))
            numerical_equal = drift_max <= DRIFT_TOLERANCE and q_max <= Q_TOLERANCE
    elif status_equal:
        support_equal = reference.get("grid_support_count") is None and streamed.get("q_grid") is None
        numerical_equal = support_equal
    return {
        "reference": reference,
        "reference_status": ref_status,
        "reference_failure_reason": ref_reason,
        "streaming_status": streamed["status"],
        "streaming_failure_reason": streamed["failure_reason"],
        "status_equal": status_equal,
        "failure_reason_equal": reason_equal,
        "support_equal": support_equal,
        "max_abs_drift_difference": drift_max,
        "max_abs_q_difference": q_max,
        "numerical_equal": numerical_equal,
        "equivalent": status_equal and reason_equal and numerical_equal,
        "drift_tolerance": DRIFT_TOLERANCE,
        "q_tolerance": Q_TOLERANCE,
    }


def _available_query_metrics(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    errors = [_valid_query_errors(result) for result in results]
    errors = [error for error in errors if error is not None]
    if not errors:
        return {"n_available": 0, "per_query_sd": None, "per_query_mean_signed_error": None, "per_query_empirical_rmse": None, "mae_median": None, "mae_range": None, "rmse_median": None, "rmse_range": None, "max_abs_error_median": None, "max_abs_error_range": None, "all_grid_median": None, "all_grid_range": None}
    matrix = np.stack(errors)
    maes = np.mean(np.abs(matrix), axis=1)
    rmses = np.sqrt(np.mean(matrix**2, axis=1))
    maxima = np.max(np.abs(matrix), axis=1)
    grid_metrics = [result.get("all_grid_metrics") for result in results if _valid_query_errors(result) is not None and isinstance(result.get("all_grid_metrics"), Mapping)]
    grid_summary: dict[str, Any] | None = None
    if grid_metrics:
        grid_summary = {}
        for key in ("mae", "rmse", "max_abs_error"):
            values = [float(metric[key]) for metric in grid_metrics if key in metric and np.isfinite(float(metric[key]))]
            grid_summary[key] = {"median": float(np.median(values)), "range": [float(np.min(values)), float(np.max(values))]} if values else None
    return {
        "n_available": int(matrix.shape[0]),
        "per_query_sd": np.std(matrix, axis=0, ddof=1).tolist() if matrix.shape[0] >= 2 else None,
        "per_query_mean_signed_error": np.mean(matrix, axis=0).tolist(),
        "per_query_empirical_rmse": np.sqrt(np.mean(matrix**2, axis=0)).tolist(),
        "mae_median": float(np.median(maes)),
        "mae_range": [float(np.min(maes)), float(np.max(maes))],
        "rmse_median": float(np.median(rmses)),
        "rmse_range": [float(np.min(rmses)), float(np.max(rmses))],
        "max_abs_error_median": float(np.median(maxima)),
        "max_abs_error_range": [float(np.min(maxima)), float(np.max(maxima))],
        "all_grid_median": None if grid_summary is None else {key: value["median"] for key, value in grid_summary.items() if value is not None},
        "all_grid_range": None if grid_summary is None else {key: value["range"] for key, value in grid_summary.items() if value is not None},
    }


def _valid_query_errors(result: Mapping[str, Any]) -> np.ndarray | None:
    """Return finite five-query errors only for a genuinely computed result."""

    if str(result.get("status", result.get("computation_status"))) != "computed":
        return None
    predictions = result.get("query_predictions")
    errors = result.get("query_errors")
    if predictions is None or errors is None:
        return None
    prediction_array = np.asarray(predictions, dtype=float).reshape(-1)
    error_array = np.asarray(errors, dtype=float).reshape(-1)
    if prediction_array.shape != (len(STARTS),) or error_array.shape != (len(STARTS),):
        return None
    if not np.isfinite(prediction_array).all() or not np.isfinite(error_array).all():
        return None
    return error_array


def summarize_convergence(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize nested levels, paired changes, and the frozen 8192 screen."""

    rows = list(results)
    seen: set[tuple[int, int]] = set()
    by_level: dict[int, list[Mapping[str, Any]]] = {level: [] for level in PREFIX_LEVELS}
    for result in rows:
        rep = _integer(result.get("rep"), "rep", minimum=0)
        n_paths = _integer(result.get("n_paths"), "n_paths", minimum=1)
        if rep >= N_REPS or n_paths not in PREFIX_LEVELS:
            raise ValueError("result rep or sample-size level is outside the frozen design")
        key = (rep, n_paths)
        if key in seen:
            raise ValueError("duplicate repetition/sample-size result")
        seen.add(key)
        by_level[n_paths].append(result)
    for level in PREFIX_LEVELS:
        by_level[level].sort(key=lambda result: int(result["rep"]))
    level_summary: dict[str, Any] = {}
    for level, level_results in by_level.items():
        level_summary[str(level)] = {
            "n_repetitions": len(level_results),
            "repetitions": [int(result["rep"]) for result in level_results],
            "per_fit": [
                {
                    "rep": int(result["rep"]),
                    "status": result.get("status"),
                    "failure_reason": result.get("failure_reason"),
                    "query_predictions": result.get("query_predictions"),
                    "query_errors": result.get("query_errors"),
                    "all_grid_metrics": result.get("all_grid_metrics"),
                    "query_metrics": result.get("query_metrics"),
                }
                for result in level_results
            ],
            "aggregate": _available_query_metrics(level_results),
        }
    paired_changes: list[dict[str, Any]] = []
    for rep in range(N_REPS):
        rep_levels = {level: next((result for result in by_level[level] if int(result["rep"]) == rep), None) for level in PREFIX_LEVELS}
        for lower, upper in zip(PREFIX_LEVELS[:-1], PREFIX_LEVELS[1:]):
            low = rep_levels[lower]
            high = rep_levels[upper]
            low_errors = _valid_query_errors(low) if low is not None else None
            high_errors = _valid_query_errors(high) if high is not None else None
            if low_errors is None or high_errors is None:
                continue
            paired_changes.append(
                {
                    "rep": rep,
                    "from_paths": lower,
                    "to_paths": upper,
                    "delta_mae": float(np.mean(np.abs(high_errors)) - np.mean(np.abs(low_errors))),
                    "delta_rmse": float(np.sqrt(np.mean(high_errors**2)) - np.sqrt(np.mean(low_errors**2))),
                    "delta_max_abs_error": float(np.max(np.abs(high_errors)) - np.max(np.abs(low_errors))),
                    "delta_query_prediction": np.asarray(high["query_predictions"], dtype=float) - np.asarray(low["query_predictions"], dtype=float),
                }
            )
    largest = by_level[PREFIX_LEVELS[-1]]
    largest_errors = [error for error in (_valid_query_errors(result) for result in largest) if error is not None]
    supported_errors = np.concatenate([np.abs(error).reshape(-1) for error in largest_errors]) if largest_errors else np.empty(0, dtype=float)
    equivalence_rows = [result.get("equivalence") for result in by_level[PREFIX_LEVELS[0]] if result.get("equivalence") is not None]
    equivalence_complete = len(equivalence_rows) == N_REPS
    equivalence_failed = any(not bool(row.get("equivalent")) for row in equivalence_rows)
    if not equivalence_complete:
        equivalence_decision = "INCONCLUSIVE"
    elif equivalence_failed:
        equivalence_decision = "FAIL"
    else:
        equivalence_decision = "PASS"
    if supported_errors.size and np.any(supported_errors > RECOVERY_TOLERANCE):
        raw_recovery_decision = "FAIL"
    elif supported_errors.size < N_REPS * len(STARTS):
        raw_recovery_decision = "INCONCLUSIVE"
    else:
        raw_recovery_decision = "PASS"
    # The raw screen preserves negative evidence, while the qualified screen
    # cannot pass until all 512-path numerical equivalence checks pass.
    recovery_decision = raw_recovery_decision if equivalence_decision == "PASS" else "INCONCLUSIVE"
    return {
        "recovery_decision": recovery_decision,
        "raw_recovery_screen_decision": raw_recovery_decision,
        "recovery_level": PREFIX_LEVELS[-1],
        "recovery_tolerance": RECOVERY_TOLERANCE,
        "n_largest_supported_predictions": int(supported_errors.size),
        "n_largest_expected_predictions": N_REPS * len(STARTS),
        "max_largest_absolute_error": float(np.max(supported_errors)) if supported_errors.size else None,
        "numerical_equivalence_decision": equivalence_decision,
        "equivalence_results": equivalence_rows,
        "levels": level_summary,
        "paired_changes": paired_changes,
        "fit_interval_claim": "none",
        "scientific_status": "finite synthetic convergence diagnostics; no production qualification",
    }


def _save_chunk_npz_once(path: Path, packet: Mapping[str, Any], stats: Mapping[str, Any]) -> str:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing artifact: {path}")
    metadata = {
        key: packet[key]
        for key in ("rep", "chunk", "global_path_offset", "n_paths", "n_steps", "dt", "horizon", "D", "seed", "rng_type", "absorption", "overshoot_retained", "seed_contract")
        if key in packet
    }
    metadata["statistics"] = {
        "grid_resolution": int(stats["grid_resolution"]),
        "n_rows": int(stats["n_rows"]),
        "n_increment_pairs": int(stats["n_increment_pairs"]),
        "n_A": int(stats["n_A"]),
        "n_B": int(stats["n_B"]),
        "n_unresolved": int(stats["n_unresolved"]),
    }
    with path.open("xb") as handle:
        np.savez_compressed(
            handle,
            reaction=np.asarray(packet["reaction"], dtype=np.float64),
            offsets=np.asarray(packet["offsets"], dtype=np.int64),
            terminal_labels=np.asarray(packet["terminal_labels"], dtype=np.int8),
            path_starts=np.asarray(packet["path_starts"], dtype=np.float64),
            support=np.asarray(stats["support"], dtype=np.int64),
            drift_sum=np.asarray(stats["drift_sum"], dtype=np.float64),
            oracle_drift_sum=np.asarray(stats["oracle_drift_sum"], dtype=np.float64),
            metadata_json=np.asarray(json.dumps(_plain(metadata), sort_keys=True)),
        )
    return _sha256_file(path)


def load_chunk_artifact(path: str | Path) -> dict[str, Any]:
    """Reload one archived chunk for independent verification."""

    with np.load(Path(path), allow_pickle=False) as loaded:
        metadata_raw = loaded["metadata_json"].item()
        return {
            "reaction": loaded["reaction"].copy(),
            "offsets": loaded["offsets"].copy(),
            "terminal_labels": loaded["terminal_labels"].copy(),
            "path_starts": loaded["path_starts"].copy(),
            "support": loaded["support"].copy(),
            "drift_sum": loaded["drift_sum"].copy(),
            "oracle_drift_sum": loaded["oracle_drift_sum"].copy(),
            "metadata": json.loads(str(metadata_raw)),
        }


def _protocol_hash(ingest_root: str | Path) -> tuple[str, str]:
    path = Path(ingest_root).expanduser().resolve() / "project" / "astra" / "ndt_trans_adapter_002_20260907" / "protocol.md"
    if not path.is_file():
        raise ValueError(f"frozen protocol is missing under ingest_root: {path}")
    return _sha256_file(path), str(path)


def _read_frozen_spec(path: str | Path) -> dict[str, Any]:
    with Path(path).expanduser().resolve().open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    supplied = loaded.get("spec") if isinstance(loaded, Mapping) and "spec" in loaded else loaded
    if supplied != build_spec():
        raise ValueError("supplied --spec does not match the frozen specification")
    return supplied


def run_convergence(*, output_dir: str | Path, ingest_root: str | Path, spec_path: str | Path | None = None) -> dict[str, Any]:
    """Run TRANS-ADAPTER-002 and write each artifact exactly once."""

    if spec_path is None:
        raise ValueError("primary convergence requires an explicit matching spec_path")
    out = Path(output_dir).expanduser().resolve()
    root = Path(ingest_root).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    spec = _read_frozen_spec(spec_path)
    protocol_sha, protocol_path = _protocol_hash(root)
    source_path = Path(__file__).resolve()
    source_sha_before = _sha256_file(source_path)
    _, closure_before = adapter001._adapter_and_closure(root)
    final_path = out / "convergence.json"
    if final_path.exists():
        raise FileExistsError(f"refusing to overwrite existing artifact: {final_path}")
    chunks_manifest: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    for rep in range(N_REPS):
        chunk_stats: list[dict[str, Any]] = []
        for chunk in range(N_CHUNKS):
            packet = simulate_chunk(rep, chunk)
            stats = compute_chunk_statistics(packet)
            artifact_path = out / f"rep_{rep:02d}_chunk_{chunk:02d}.npz"
            artifact_sha = _save_chunk_npz_once(artifact_path, packet, stats)
            chunk_stats.append(stats)
            chunks_manifest.append({"rep": rep, "chunk": chunk, "artifact": artifact_path.name, "sha256": artifact_sha, "n_paths": CHUNK_PATHS, "n_rows": stats["n_rows"], "n_A": stats["n_A"], "n_B": stats["n_B"], "n_unresolved": stats["n_unresolved"], "seed": packet["seed"], "support_sha256": _sha256_array(stats["support"]), "drift_sum_sha256": _sha256_array(stats["drift_sum"]), "oracle_drift_sum_sha256": _sha256_array(stats["oracle_drift_sum"])})
            prefix_size = (chunk + 1) * CHUNK_PATHS
            if prefix_size in PREFIX_LEVELS:
                aggregate = aggregate_statistics(chunk_stats)
                result = evaluate_streaming(aggregate)
                result["rep"] = rep
                result["n_paths"] = prefix_size
                result["n_chunks"] = chunk + 1
                if prefix_size == CHUNK_PATHS:
                    result["equivalence"] = compare_streaming_to_adapter(packet, ingest_root=root, streaming=result)
                results.append(result)
    source_sha_after = _sha256_file(source_path)
    _, closure_after = adapter001._adapter_and_closure(root)
    if source_sha_before != source_sha_after or closure_before != closure_after:
        raise RuntimeError("source or unchanged-ingest closure changed during convergence run")
    controls = [deterministic_grid_control(resolution) for resolution in CONTROL_RESOLUTIONS]
    summary = summarize_convergence(results)
    adapter_source_hash = next((digest for path, digest in closure_after.items() if path.replace("\\", "/").endswith("/committor.py")), None)
    if adapter_source_hash is None:
        raise RuntimeError("unchanged-ingest closure does not contain committor.py")
    report = {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "spec": spec,
        "spec_sha256": spec_hash(spec),
        "protocol_sha256": protocol_sha,
        "protocol_path": protocol_path,
        "source_module_sha256": source_sha_after,
        "adapter_001_module_sha256": adapter_source_hash,
        "adapter_001_analysis_wrapper_sha256": _sha256_file(Path(adapter001.__file__).resolve()),
        "ingest_closure_hashes": closure_after,
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform()},
        "chunks": chunks_manifest,
        "prefixes": results,
        "oracle": controls,
        "summary": summary,
        "scientific_status": "finite synthetic convergence diagnostics; no production or biological qualification",
    }
    with final_path.open("x", encoding="utf-8") as handle:
        json.dump(_plain(report), handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    return report


# Public names used by independent tests and verification.  These are direct function
# bindings, so there is one implementation of each operation and no alternate
# sampling or estimation path.
chunk_statistics = compute_chunk_statistics
merge_statistics = aggregate_statistics
fit_statistics = evaluate_streaming


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec-only", action="store_true")
    parser.add_argument("--spec", type=Path)
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
        parser.error("--spec, --output-dir and --ingest-root are required; use --spec-only for the frozen spec")
    report = run_convergence(output_dir=args.output_dir, ingest_root=args.ingest_root, spec_path=args.spec)
    print(json.dumps({"output_dir": str(Path(args.output_dir).resolve()), "spec_sha256": report["spec_sha256"], "recovery_decision": report["summary"]["recovery_decision"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
