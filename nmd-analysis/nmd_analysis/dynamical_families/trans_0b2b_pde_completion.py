"""Deterministic PDE completion arm for TRANS-0B2b.

This module is deliberately separate from the control runner and never creates
or consumes a random number generator.  It reuses the frozen wide-stencil
assembly in :mod:`trans_0b2b` for operator coefficients and rates, adds a
resource preflight, and uses one sparse LU factorization per parabolic ``dt``
followed by repeated triangular solves.  This is deterministic independence
from path output, not a claim that the stencil was reimplemented in a second
source file.
The wrapper does not alter the frozen control source or any existing primary
output.
"""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix
from scipy.sparse.linalg import splu

from nmd_analysis.dynamical_families import trans_0b2b as _base


SCHEMA_VERSION = "nmd_analysis.trans_0b2b_pde_completion.v1"
STAGE = _base.STAGE
ROLE = _base.PDE_ROLE
PDE_R_GRID = tuple(float(value) for value in _base.PDE_R_GRID)
PDE_MESH_GRID = {key: tuple(tuple(int(x) for x in mesh) for mesh in value) for key, value in _base.PDE_MESH_GRID.items()}
PDE_T_GRID = tuple(float(value) for value in _base.PDE_T_GRID)
PDE_DT_GRID = tuple(float(value) for value in _base.PDE_DT_GRID)
NODE_CAP = int(_base.PDE_SPATIAL_NODE_CAP)
ELLIPTIC_RESIDUAL_GATE = 1.0e-6
REFINEMENT_GATE = 0.005
PARABOLIC_TIME_GATE = 0.005


def _plain(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [_plain(item) for item in value.tolist()]
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, (np.floating, float)):
        result = float(value)
        if not np.isfinite(result):
            raise ValueError("nonfinite value cannot be serialized")
        return result
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if value is None or isinstance(value, (bool, str)):
        return value
    raise TypeError(f"unsupported value {type(value).__name__}")


def _sha_json(value: Any) -> str:
    raw = json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _mesh(R: float, level: int) -> tuple[int, int]:
    key = str(int(float(R)))
    meshes = PDE_MESH_GRID.get(key)
    if meshes is None or not 0 <= int(level) < len(meshes):
        raise ValueError(f"R/level is outside the frozen PDE mesh family: {R!r}, {level!r}")
    nr, ns = meshes[int(level)]
    if nr * ns > NODE_CAP:
        raise ValueError("PDE mesh exceeds the frozen node cap")
    h_r = 1.5 / (nr - 1)
    h_s = 2.0 * float(R) / (ns - 1)
    if not 9.0 / 11.0 <= h_r / h_s <= 11.0 / 9.0:
        raise ValueError("PDE mesh ratio is outside the frozen monotone interval")
    return nr, ns


def build_spec() -> dict[str, Any]:
    """Return the immutable PDE completion contract."""

    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "role": ROLE,
        "source_schema_version": _base.SCHEMA_VERSION,
        "operator": {
            "coordinates": "r=u.T@x, s=w.T@x",
            "drift": _base.TRANSFORMED_J.tolist(),
            "diffusion": _base.TRANSFORMED_Q.tolist(),
            "generator": "-s*q_r + (2*r-3*s)*q_s + 0.11*q_rr - 0.18*q_rs + 0.11*q_ss",
            "stencil": "first-order upwind drift plus axis/anti-diagonal wide jump generator",
            "artificial_boundary": "homogeneous numerical Neumann at s=+-R; fixed-side 0/1 stress runs",
        },
        "elliptic": {
            "R_grid": list(PDE_R_GRID),
            "mesh_grid": {key: [list(mesh) for mesh in meshes] for key, meshes in PDE_MESH_GRID.items()},
            "levels_per_R": 3,
            "node_cap": NODE_CAP,
            "residual_gate": ELLIPTIC_RESIDUAL_GATE,
            "domain_gate": REFINEMENT_GATE,
            "spatial_gate": REFINEMENT_GATE,
        },
        "stress": {
            "boundary_modes": ["fixed0", "fixed1"],
            "scope": "R=6, finest declared mesh, because the protocol gate is at the largest domain",
            "comparison_principle_required": True,
            "gate": REFINEMENT_GATE,
        },
        "parabolic": {
            "horizons": list(PDE_T_GRID),
            "dt_grid": list(PDE_DT_GRID),
            "time_integrator": "implicit Euler in remaining horizon",
            "initial_interior": 0.0,
            "weak_corner_compatibility": True,
            "time_gate": PARABOLIC_TIME_GATE,
            "solver_reuse": "one sparse LU factorization per dt; triangular solve per time step",
            "scope": "all declared horizons and dt values at an explicitly selected frozen spatial mesh",
        },
        "provenance": "deterministic PDE only; no control paths, primary output or RNG state are read; frozen operator assembly is reused from trans_0b2b",
    }


def runtime_metadata() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": __import__("scipy").__version__,
        "randomness": "none",
    }


def resource_preflight(*, parabolic_R: Sequence[float] = PDE_R_GRID, parabolic_level: int = 0) -> dict[str, Any]:
    """Enumerate exact PDE work without allocating matrices or solving.

    The preflight retains every declared elliptic mesh and every declared
    domain/time combination.  It reports work estimates so a caller can
    choose a bounded parabolic spatial scope explicitly; no grid is changed
    implicitly by this function.
    """

    elliptic: list[dict[str, Any]] = []
    for R in PDE_R_GRID:
        for level, (nr, ns) in enumerate(PDE_MESH_GRID[str(int(R))]):
            elliptic.append({
                "R": R, "level": level, "n_r": nr, "n_s": ns,
                "nodes": nr * ns, "unknowns": (nr - 2) * ns,
                "status": "DECLARED",
            })
    parabolic: list[dict[str, Any]] = []
    parabolic_scope = tuple(float(value) for value in parabolic_R)
    if not parabolic_scope:
        raise ValueError("parabolic_R must contain at least one declared radius")
    for R in parabolic_scope:
        nr, ns = _mesh(R, parabolic_level)
        unknowns = (nr - 2) * ns
        for horizon in PDE_T_GRID:
            for dt in PDE_DT_GRID:
                steps_float = horizon / dt
                steps = int(round(steps_float))
                if not np.isclose(steps_float, steps, rtol=0.0, atol=1.0e-10):
                    raise ValueError("declared parabolic horizon/dt is not an integer grid")
                parabolic.append({
                    "R": R, "level": int(parabolic_level), "n_r": nr, "n_s": ns,
                    "horizon": horizon, "dt_pde": dt, "n_steps": steps,
                    "unknowns": unknowns, "triangular_solves": steps,
                    "work_units_upper_bound": unknowns * steps,
                    "status": "DECLARED",
                })
    stress_R = 6.0
    stress_nr, stress_ns = _mesh(stress_R, 2)
    shared_steps_by_dt = {
        str(dt): max(int(round(horizon / dt)) for horizon in PDE_T_GRID)
        for dt in PDE_DT_GRID
    }
    shared_triangular_solves = sum(shared_steps_by_dt.values())
    scope_nr, scope_ns = _mesh(parabolic_scope[0], parabolic_level)
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "role": ROLE,
        "status": "PREFLIGHT_ONLY",
        "elliptic": elliptic,
        "stress": [{
            "R": stress_R, "level": 2, "n_r": stress_nr, "n_s": stress_ns,
            "nodes": stress_nr * stress_ns, "boundary": mode, "status": "DECLARED",
        } for mode in ("fixed0", "fixed1")],
        "parabolic": parabolic,
        "parabolic_shared_horizon_plan": {
            "factorizations": len(PDE_DT_GRID),
            "triangular_solves": shared_triangular_solves,
            "work_units_upper_bound": ((scope_nr - 2) * scope_ns) * shared_triangular_solves,
            "reuse": "each dt is advanced once to T=16; T=1 and T=4 are snapshots of the same deterministic run",
        },
        "runtime": runtime_metadata(),
        "no_rng": True,
        "grid_unchanged": True,
    }


def _implicit_matrix(system: Mapping[str, Any], dt: float) -> csr_matrix:
    matrix = system["matrix"].tolil(copy=True)
    interior = {int(row) for row in system["interior_rows"]}
    for row in interior:
        matrix[row, :] = -system["matrix"].getrow(row)
        matrix[row, row] += 1.0 / float(dt)
    for row in system["constraint_rows"]:
        matrix[row, :] = system["matrix"].getrow(int(row))
    return csr_matrix(matrix).tocsc()


def _initial_values(system: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    values = np.zeros(int(system["matrix"].shape[0]), dtype=float)
    boundary_rhs = np.asarray(system["boundary_rhs"], dtype=float).copy()
    for row, boundary_value in system["constraint_rows"].items():
        values[int(row)] = float(boundary_value)
        boundary_rhs[int(row)] = float(boundary_value)
    return values, boundary_rhs


def _mesh_metadata(R: float, n_r: int, n_s: int, system: Mapping[str, Any]) -> dict[str, Any]:
    """Bind every serialized parabolic row to one frozen mesh identity."""

    meshes = PDE_MESH_GRID.get(str(int(float(R))), ())
    mesh = (int(n_r), int(n_s))
    levels = [level for level, candidate in enumerate(meshes) if tuple(candidate) == mesh]
    if len(levels) != 1:
        raise ValueError(f"mesh is not uniquely identified by the frozen PDE grid: R={R}, mesh={mesh}")
    level = int(levels[0])
    unknowns = int(system["matrix"].shape[0])
    nnz = int(system["matrix"].nnz)
    return {
        "n_r": int(n_r), "n_s": int(n_s),
        "h_r": system["h_r"], "h_s": system["h_s"],
        "nodes": int(n_r * n_s), "unknowns": unknowns, "nnz": nnz,
        "completion_level": level,
        "mesh_id": f"R{int(float(R))}_L{level}_{int(n_r)}x{int(n_s)}",
    }


def _parabolic_entry(system: Mapping[str, Any], values: np.ndarray, previous: np.ndarray, *, R: float, n_r: int, n_s: int, horizon: float, dt: float, n_steps: int, lu: Any) -> dict[str, Any]:
    grid = _base._solution_grid(system, values)
    previous_grid = _base._solution_grid(system, previous)
    diagnostics = _base._pde_diagnostics(system, grid, "neumann")
    final_l = np.asarray(system["matrix"] @ _base._pde_vector(system, grid) - system["boundary_rhs"], dtype=float)
    interior_rows = np.asarray(system["interior_rows"], dtype=int)
    final_dt = (values - previous) / float(dt)
    temporal_residual = float(np.max(np.abs(final_dt[interior_rows] - final_l[interior_rows]))) if interior_rows.size else 0.0
    starts = _base.STARTS @ _base.TRANSFORM_BASIS
    mesh_metadata = _mesh_metadata(R, n_r, n_s, system)
    return {
        "schema_version": SCHEMA_VERSION, "stage": STAGE, "role": ROLE,
        "problem": "parabolic_q_T", "R": float(R),
        "completion_level": mesh_metadata["completion_level"], "mesh_id": mesh_metadata["mesh_id"],
        "n_r": mesh_metadata["n_r"], "n_s": mesh_metadata["n_s"],
        "unknowns": mesh_metadata["unknowns"], "nnz": mesh_metadata["nnz"],
        "domain": {"r": [-_base.CONTROL_THRESHOLD, _base.CONTROL_THRESHOLD], "s": [-float(R), float(R)]},
        "mesh": mesh_metadata,
        "horizon": float(horizon), "dt_pde": float(dt), "n_steps": int(n_steps),
        "r_grid": system["r_grid"], "s_grid": system["s_grid"], "values": grid,
        "start_coordinates_rs": starts, "start_values": _base._bilinear_values(grid, system["r_grid"], system["s_grid"], starts),
        "transformed_drift": _base.TRANSFORMED_J, "transformed_diffusion": _base.TRANSFORMED_Q,
        "operator": "-s*q_r + (2*r-3*s)*q_s + 0.11*q_rr - 0.18*q_rs + 0.11*q_ss",
        "boundary_condition": {"initial_interior": 0.0, "r=-a": 0.0, "r=+a": 1.0, "s": "neumann"},
        "weak_corner_compatibility": "initial interior value 0 and B boundary value 1 are discontinuous at the T=0 corner",
        "partial_T_q_equals_L_q": True, "partial_T_q_minus_L_q_final_step_max": temporal_residual,
        "cross_diffusion": "axis/anti-diagonal wide jump representation",
        "drift_discretization": "first-order upwind", "time_integrator": "implicit Euler in remaining horizon",
        "solver": "scipy.sparse.linalg.splu (one factorization per dt)", "solver_tolerance": _base.PDE_SOLVER_TOL,
        "n_factorizations": 1, "triangular_solves": int(n_steps),
        "monotone_generator": True,
        "monotonicity_certificate": {"status": "JUSTIFIED", "reason": "declared ratio-1 mesh gives nonnegative axis and anti-diagonal rates"},
        "method_status": "NUMERICAL_REFERENCE_CANDIDATE", "factorization_checksum": _sha_json({"shape": system["matrix"].shape, "dt": dt, "nnz": int(lu.L.nnz + lu.U.nnz)}),
        **diagnostics,
    }


def solve_parabolic_grid(*, R: float, n_r: int, n_s: int, horizons: Sequence[float] = PDE_T_GRID, dts: Sequence[float] = PDE_DT_GRID) -> list[dict[str, Any]]:
    """Solve all requested time rows at one explicitly chosen frozen mesh."""

    radius = float(R)
    _mesh(radius, next((i for i, mesh in enumerate(PDE_MESH_GRID[str(int(radius))]) if mesh == (int(n_r), int(n_s))), -1))
    requested_horizons = tuple(float(value) for value in horizons)
    requested_dts = tuple(float(value) for value in dts)
    system = _base._assemble_pde_operator(radius, int(n_r), int(n_s), "neumann")
    results: list[dict[str, Any]] = []
    for dt in requested_dts:
        if dt not in PDE_DT_GRID:
            raise ValueError("dt is outside the declared parabolic grid")
        step_counts = {}
        for horizon in requested_horizons:
            count = int(round(horizon / dt))
            if horizon not in PDE_T_GRID or count < 1 or not np.isclose(horizon / dt, count, rtol=0.0, atol=1.0e-10):
                raise ValueError("horizon/dt is outside the declared parabolic grid")
            step_counts[count] = horizon
        max_steps = max(step_counts)
        matrix = _implicit_matrix(system, dt)
        lu = splu(matrix)
        values, boundary_rhs = _initial_values(system)
        previous = values.copy()
        for step in range(1, max_steps + 1):
            previous = values
            rhs = values / dt - boundary_rhs
            for row, boundary_value in system["constraint_rows"].items():
                rhs[int(row)] = float(boundary_value)
            values = np.asarray(lu.solve(rhs), dtype=float)
            if not np.isfinite(values).all():
                raise FloatingPointError("nonfinite optimized parabolic state")
            if step in step_counts:
                results.append(_parabolic_entry(system, values.copy(), previous.copy(), R=radius, n_r=int(n_r), n_s=int(n_s), horizon=step_counts[step], dt=dt, n_steps=step, lu=lu))
    results.sort(key=lambda row: (float(row["horizon"]), float(row["dt_pde"])))
    return results


def solve_parabolic_optimized(*, R: float, n_r: int, n_s: int, horizon: float, dt_pde: float) -> dict[str, Any]:
    rows = solve_parabolic_grid(R=R, n_r=n_r, n_s=n_s, horizons=(horizon,), dts=(dt_pde,))
    if len(rows) != 1:
        raise RuntimeError("optimized parabolic solver returned an unexpected row count")
    return rows[0]


def solve_elliptic_completion(*, include_stress: bool = True) -> dict[str, Any]:
    """Compute all 12 declared Neumann rows and the largest-domain stress pair."""

    elliptic: list[dict[str, Any]] = []
    for R in PDE_R_GRID:
        for level, (n_r, n_s) in enumerate(PDE_MESH_GRID[str(int(R))]):
            row = _base.solve_elliptic_reference(R=R, n_r=n_r, n_s=n_s, artificial_boundary="neumann")
            row.update({"R": float(R), "completion_level": level, "completion_scope": "all declared elliptic spatial/domain rows"})
            elliptic.append(row)
    stress: list[dict[str, Any]] = []
    if include_stress:
        R, (n_r, n_s) = 6.0, PDE_MESH_GRID["6"][2]
        for mode in ("fixed0", "fixed1"):
            row = _base.solve_elliptic_reference(R=R, n_r=n_r, n_s=n_s, artificial_boundary=mode)
            row.update({"R": float(R), "completion_level": 2, "stress_boundary": mode, "completion_scope": "largest declared domain and finest mesh"})
            stress.append(row)
    return {
        "schema_version": SCHEMA_VERSION, "stage": STAGE, "role": ROLE,
        "status": "COMPUTED_ELLIPTIC_WITH_STRESS" if include_stress else "COMPUTED_ELLIPTIC",
        "elliptic": elliptic, "stress": stress,
        "parabolic_status": "UNRUN/METHOD-LIMITED",
        "source_independence": "deterministic PDE only; no RNG or path output",
    }


__all__ = [
    "ELLIPTIC_RESIDUAL_GATE", "PDE_DT_GRID", "PDE_MESH_GRID", "PDE_R_GRID", "PDE_T_GRID", "PARABOLIC_TIME_GATE",
    "REFINEMENT_GATE", "ROLE", "SCHEMA_VERSION", "STAGE", "build_spec", "resource_preflight",
    "runtime_metadata", "solve_elliptic_completion", "solve_parabolic_grid", "solve_parabolic_optimized",
]
