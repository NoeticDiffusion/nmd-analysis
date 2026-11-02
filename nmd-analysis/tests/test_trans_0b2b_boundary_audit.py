"""Deterministic boundary-contract audit for the TRANS-0B2b PDE arm.

These tests inspect the assembled finite-grid system directly.  They define
the cell masks independently, verify the target and artificial-side row
contracts, and ensure that incompatible corner conditions remain visible in
the reported boundary residual instead of being treated as a valid PDE
certificate.  No simulator or random stream is used.
"""

from __future__ import annotations

import numpy as np
import pytest

from nmd_analysis.dynamical_families import trans_0b2b as b


def _row(i: int, j: int, n_s: int) -> int:
    """Independent inverse of the assembler's interior row ordering."""

    return (i - 1) * n_s + j


def _cell_class(i: int, j: int, n_r: int, n_s: int) -> str:
    target = i in (0, n_r - 1)
    artificial = j in (0, n_s - 1)
    if target and artificial:
        return "target_artificial_corner"
    if target:
        return "target_edge"
    if artificial:
        return "artificial_side_interior"
    return "pde_interior"


def _raw_residual(system: dict[str, object], grid: np.ndarray) -> np.ndarray:
    vector = b._pde_vector(system, grid)
    rhs = np.asarray(system["boundary_rhs"], dtype=float).copy()
    for row, value in system["constraint_rows"].items():
        rhs[int(row)] = float(value)
    return np.asarray(system["matrix"] @ vector - rhs, dtype=float)


def _contract_grid(n_r: int, n_s: int, artificial_boundary: str) -> np.ndarray:
    grid = np.full((n_r, n_s), 0.25, dtype=float)
    # Target edges include their corners and are fixed independently of the
    # artificial side contract.
    grid[0, :] = 0.0
    grid[-1, :] = 1.0
    if artificial_boundary == "neumann":
        grid[1:-1, 0] = grid[1:-1, 1]
        grid[1:-1, -1] = grid[1:-1, -2]
    elif artificial_boundary == "fixed0":
        grid[1:-1, 0] = 0.0
        grid[1:-1, -1] = 0.0
    elif artificial_boundary == "fixed1":
        grid[1:-1, 0] = 1.0
        grid[1:-1, -1] = 1.0
    else:  # pragma: no cover - modes are parameterized below
        raise AssertionError(artificial_boundary)
    return grid


def test_boundary_masks_partition_target_edges_sides_corners_and_pde_domain() -> None:
    n_r, n_s = 7, 25
    masks = {
        "target_edge": set(),
        "artificial_side_interior": set(),
        "target_artificial_corner": set(),
        "pde_interior": set(),
    }
    for i in range(n_r):
        for j in range(n_s):
            masks[_cell_class(i, j, n_r, n_s)].add((i, j))

    assert len(masks["target_edge"]) == 2 * (n_s - 2)
    assert len(masks["artificial_side_interior"]) == 2 * (n_r - 2)
    assert len(masks["target_artificial_corner"]) == 4
    assert len(masks["pde_interior"]) == (n_r - 2) * (n_s - 2)
    assert sum(map(len, masks.values())) == n_r * n_s
    assert not (masks["target_edge"] & masks["pde_interior"])
    assert not (masks["artificial_side_interior"] & masks["pde_interior"])

    system = b._assemble_pde_operator(3.0, n_r, n_s, "neumann")
    expected_interior_rows = {
        _row(i, j, n_s)
        for i, j in masks["pde_interior"]
    }
    expected_constraint_rows = {
        _row(i, j, n_s)
        for i, j in masks["artificial_side_interior"]
    }
    interior_rows = set(map(int, system["interior_rows"]))
    constraint_rows = set(map(int, system["constraint_rows"]))
    all_rows = set(range((n_r - 2) * n_s))
    assert interior_rows == expected_interior_rows
    assert constraint_rows == expected_constraint_rows
    assert interior_rows.isdisjoint(constraint_rows)
    assert interior_rows | constraint_rows == all_rows
    # Target edges and all four corners are represented through boundary RHS
    # terms, never as unknown rows in the reduced system.
    assert all(row < (n_r - 2) * n_s for row in interior_rows | constraint_rows)


@pytest.mark.parametrize(
    ("mode", "side_value"),
    (("neumann", None), ("fixed0", 0.0), ("fixed1", 1.0)),
)
def test_assembled_artificial_side_rows_match_neumann_or_fixed_contract(
    mode: str, side_value: float | None
) -> None:
    n_r, n_s = 7, 25
    system = b._assemble_pde_operator(3.0, n_r, n_s, mode)
    matrix = np.asarray(system["matrix"].toarray(), dtype=float)
    boundary_rhs = np.asarray(system["boundary_rhs"], dtype=float)

    for i in range(1, n_r - 1):
        left = _row(i, 0, n_s)
        right = _row(i, n_s - 1, n_s)
        for row, neighbor in ((left, _row(i, 1, n_s)), (right, _row(i, n_s - 2, n_s))):
            nonzero = np.flatnonzero(np.abs(matrix[row]) > 1.0e-14)
            if side_value is None:
                assert set(nonzero) == {row, neighbor}
                assert matrix[row, row] == pytest.approx(1.0)
                assert matrix[row, neighbor] == pytest.approx(-1.0)
                assert system["constraint_rows"][row] == pytest.approx(0.0)
            else:
                assert set(nonzero) == {row}
                assert matrix[row, row] == pytest.approx(1.0)
                assert system["constraint_rows"][row] == pytest.approx(side_value)
            assert boundary_rhs[row] == pytest.approx(0.0)

        for j in range(1, n_s - 1):
            interior = _row(i, j, n_s)
            assert interior in set(map(int, system["interior_rows"]))
            assert interior not in system["constraint_rows"]
            assert matrix[interior, interior] < 0.0


def test_residual_mask_excludes_constraints_but_boundary_diagnostic_catches_them() -> None:
    n_r, n_s = 7, 25
    system = b._assemble_pde_operator(3.0, n_r, n_s, "fixed1")
    # The lower target edge remains zero while fixed1 artificial sides are
    # applied only to side-interior cells.  Thus the side/corner conflict is
    # deterministic and has magnitude one.
    grid = _contract_grid(n_r, n_s, "fixed1")
    raw = _raw_residual(system, grid)
    diagnostics = b._pde_diagnostics(system, grid, "fixed1")
    interior_rows = np.asarray(system["interior_rows"], dtype=int)
    constraint_rows = np.asarray(sorted(system["constraint_rows"]), dtype=int)

    independent_masked_max = float(np.max(np.abs(raw[interior_rows])))
    assert diagnostics["max_scaled_residual"] == pytest.approx(independent_masked_max, abs=1.0e-12)
    # The side-interior constraints themselves are satisfied.  The conflict is
    # at the lower target/artificial corners, which have no reduced-system row
    # and therefore must be caught by the separate boundary residual.
    assert float(np.max(np.abs(raw[constraint_rows]))) <= 1.0e-12
    assert diagnostics["target_boundary_residual_max"] == pytest.approx(0.0, abs=1.0e-12)
    assert diagnostics["artificial_boundary_residual_max"] >= 1.0 - 1.0e-12
    assert diagnostics["boundary_residual_max"] >= 1.0 - 1.0e-12
    assert diagnostics["within_unit_interval"] is True

    # A separately malformed side-interior value produces a constraint-row
    # residual, while the PDE residual mask continues to include only the
    # true interior stencil rows.
    malformed = grid.copy()
    malformed[2, 0] = 0.0
    malformed_raw = _raw_residual(system, malformed)
    malformed_diagnostics = b._pde_diagnostics(system, malformed, "fixed1")
    assert float(np.max(np.abs(malformed_raw[constraint_rows]))) >= 1.0 - 1.0e-12
    assert malformed_diagnostics["max_scaled_residual"] == pytest.approx(
        float(np.max(np.abs(malformed_raw[interior_rows]))), abs=1.0e-12
    )


@pytest.mark.parametrize("mode", ("fixed0", "fixed1"))
def test_artificial_corner_conflict_is_reported_and_cannot_qualify_stress_run(mode: str) -> None:
    result = b.solve_elliptic_reference(
        R=3.0,
        n_r=7,
        n_s=25,
        artificial_boundary=mode,
    )
    assert result["target_boundary_residual_max"] <= 1.0e-12
    assert result["artificial_boundary_residual_max"] >= 1.0 - 1.0e-10
    assert result["boundary_residual_max"] >= 1.0 - 1.0e-10
    assert result["within_unit_interval"] is True
    # Independently apply the qualification boundary gate.  The implementation
    # may retain a numerical candidate status, but this conflict cannot be a
    # qualified stress result.
    qualifies = (
        float(result["max_scaled_residual"]) <= 1.0e-6
        and float(result["boundary_residual_max"]) <= 1.0e-6
        and bool(result["within_unit_interval"])
    )
    assert qualifies is False


def test_neumann_target_edges_and_artificial_sides_are_compatible() -> None:
    result = b.solve_elliptic_reference(
        R=3.0,
        n_r=7,
        n_s=25,
        artificial_boundary="neumann",
    )
    values = np.asarray(result["values"], dtype=float)
    assert np.all(values[0, :] == 0.0)
    assert np.all(values[-1, :] == 1.0)
    assert result["target_boundary_residual_max"] <= 1.0e-12
    assert result["artificial_boundary_residual_max"] <= 1.0e-10
    assert result["boundary_residual_max"] <= 1.0e-10
    assert result["within_unit_interval"] is True
