"""TRANS-0B2b boundary-contract v2 PDE wrapper.

The frozen wide-stencil operator is unchanged.  This version only makes the
boundary mask explicit: r-target Dirichlet rows include all s nodes and take
precedence at the four corners; artificial s-side conditions apply only to
interior r rows.  Fixed-side diagnostics report that strict interior mask and
retain the historical full-side value, including corner conflicts.
"""

from __future__ import annotations

import platform
from typing import Any, Mapping

import numpy as np

from nmd_analysis.dynamical_families import trans_0b2b as _base


SCHEMA_VERSION = "nmd_analysis.trans_0b2b_boundary_contract.v2"
STAGE = _base.STAGE
ROLE = _base.PDE_ROLE
PDE_R_GRID = tuple(float(x) for x in _base.PDE_R_GRID)
PDE_MESH_GRID = {key: tuple(tuple(int(x) for x in mesh) for mesh in value) for key, value in _base.PDE_MESH_GRID.items()}
BOUNDARY_MODES = ("neumann", "fixed0", "fixed1")
BOUNDARY_TOL = 1.0e-10


CORNER_MASK = (
    {"corner": "r=-a,s=-R", "r_target": 0.0, "artificial_side": "s=-R", "s_condition_applies": False},
    {"corner": "r=-a,s=+R", "r_target": 0.0, "artificial_side": "s=+R", "s_condition_applies": False},
    {"corner": "r=+a,s=-R", "r_target": 1.0, "artificial_side": "s=-R", "s_condition_applies": False},
    {"corner": "r=+a,s=+R", "r_target": 1.0, "artificial_side": "s=+R", "s_condition_applies": False},
)


def _plain(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [_plain(item) for item in value.tolist()]
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        if not np.isfinite(number):
            raise ValueError("nonfinite boundary-contract value")
        return number
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def build_spec() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "role": ROLE,
        "operator_source_schema": _base.SCHEMA_VERSION,
        "boundary_contract": {
            "target_r": "Dirichlet values 0/1 on all s nodes, including corners",
            "artificial_s": "Neumann or fixed0/fixed1 values on strict interior r rows only",
            "corner_precedence": "r-target Dirichlet takes precedence at all four corners",
            "corner_mask": list(CORNER_MASK),
            "strict_interior_residual_tolerance": BOUNDARY_TOL,
            "historical_full_corner_residual": "retained separately for fixed-side stress rows",
        },
        "R_grid": list(PDE_R_GRID),
        "mesh_grid": {key: [list(mesh) for mesh in meshes] for key, meshes in PDE_MESH_GRID.items()},
        "stress_scope": "R=6, finest declared mesh, fixed0 and fixed1",
        "comparison_principle": False,
        "randomness": "none",
    }


def runtime_metadata() -> dict[str, str]:
    return {"python": platform.python_version(), "numpy": np.__version__, "scipy": __import__("scipy").__version__, "randomness": "none"}


def _side_residuals(values: np.ndarray, hs: float, mode: str) -> tuple[float, float]:
    if mode == "neumann":
        full = max(float(np.max(np.abs((values[:, 1] - values[:, 0]) / hs))), float(np.max(np.abs((values[:, -1] - values[:, -2]) / hs))))
        inner = max(float(np.max(np.abs((values[1:-1, 1] - values[1:-1, 0]) / hs))), float(np.max(np.abs((values[1:-1, -1] - values[1:-1, -2]) / hs))))
    elif mode in ("fixed0", "fixed1"):
        target = 0.0 if mode == "fixed0" else 1.0
        full = max(float(np.max(np.abs(values[:, 0] - target))), float(np.max(np.abs(values[:, -1] - target))))
        inner = max(float(np.max(np.abs(values[1:-1, 0] - target))), float(np.max(np.abs(values[1:-1, -1] - target))))
    else:
        raise ValueError(f"unknown artificial boundary mode: {mode}")
    return inner, full


def solve_elliptic_reference(*, R: float, n_r: int, n_s: int, artificial_boundary: str = "neumann") -> dict[str, Any]:
    """Solve the frozen elliptic operator with the v2 boundary contract."""

    mode = str(artificial_boundary).lower()
    if mode not in BOUNDARY_MODES:
        raise ValueError("artificial_boundary must be neumann, fixed0, or fixed1")
    result = _base.solve_elliptic_reference(R=R, n_r=n_r, n_s=n_s, artificial_boundary=mode, include_stress_envelope=False)
    values = np.asarray(result["values"], dtype=float)
    inner, full = _side_residuals(values, float(result["mesh"]["h_s"]), mode)
    target_residual = float(result["target_boundary_residual_max"])
    boundary = dict(result["boundary_condition"])
    boundary.update({"s_scope": "strict interior r rows only", "corner_precedence": "r-target Dirichlet"})
    result.update({
        "schema_version": SCHEMA_VERSION,
        "role": ROLE,
        "boundary_condition": boundary,
        "boundary_contract": {
            "version": SCHEMA_VERSION,
            "target_r_scope": "all s nodes including corners",
            "artificial_s_scope": "strict interior r rows only",
            "corner_precedence": "r-target Dirichlet",
            "corner_mask": list(CORNER_MASK),
        },
        "artificial_boundary_residual_max": inner,
        "strict_interior_artificial_boundary_residual_max": inner,
        "historical_full_corner_artificial_boundary_residual_max": full,
        "boundary_residual_max": max(target_residual, inner),
        "corner_conflict": bool(mode in ("fixed0", "fixed1") and full > BOUNDARY_TOL and inner <= BOUNDARY_TOL),
        "corner_compatibility": "compatible" if mode == "neumann" else "disjoint artificial-side mask with r-target precedence",
        "comparison_principle": False,
        "method_status": "NUMERICAL_REFERENCE_CANDIDATE",
    })
    return result


def solve_elliptic_completion(*, include_stress: bool = True) -> dict[str, Any]:
    """Compute all 12 Neumann rows and the declared two-row stress scope."""

    elliptic: list[dict[str, Any]] = []
    for R in PDE_R_GRID:
        for level, (n_r, n_s) in enumerate(PDE_MESH_GRID[str(int(R))]):
            row = solve_elliptic_reference(R=R, n_r=n_r, n_s=n_s, artificial_boundary="neumann")
            row["completion_level"] = level
            row["completion_scope"] = "all declared elliptic spatial/domain rows"
            elliptic.append(row)
    stress: list[dict[str, Any]] = []
    if include_stress:
        R = 6.0
        n_r, n_s = PDE_MESH_GRID["6"][2]
        for mode in ("fixed0", "fixed1"):
            row = solve_elliptic_reference(R=R, n_r=n_r, n_s=n_s, artificial_boundary=mode)
            row["stress_boundary"] = mode
            row["completion_scope"] = "largest declared domain and finest mesh"
            stress.append(row)
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "role": ROLE,
        "status": "COMPUTED_BOUNDARY_CONTRACT_V2",
        "elliptic": elliptic,
        "stress": stress,
        "comparison_principle": False,
        "stress_envelope_status": "METHOD-LIMITED",
        "parabolic_status": "UNRUN/METHOD-LIMITED",
        "corner_mask": list(CORNER_MASK),
        "source_independence": "deterministic elliptic/stress only; no RNG or control path output",
    }


__all__ = ["BOUNDARY_MODES", "BOUNDARY_TOL", "CORNER_MASK", "PDE_MESH_GRID", "PDE_R_GRID", "ROLE", "SCHEMA_VERSION", "STAGE", "build_spec", "runtime_metadata", "solve_elliptic_completion", "solve_elliptic_reference"]
