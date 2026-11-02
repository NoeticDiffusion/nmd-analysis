"""Independent nonprimary tests for TRANS-0B2b.

The analytic control values, OU covariance, confidence limits, and transformed
PDE coefficients are recomputed here rather than imported from implementation
helpers.  All trajectories use an unrelated UNIT_ROOT; the frozen primary
namespace is inspected only as metadata and is never drawn from.
"""

from __future__ import annotations

import hashlib
import gzip
import importlib.util
import json
import types
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.linalg import expm
from scipy.stats import beta

from nmd_analysis.dynamical_families import trans_0b2b as b


UNIT_ROOT = 91_827_463
J_REFERENCE = np.asarray([[-1.0, 3.0], [0.0, -2.0]], dtype=float)
Q_REFERENCE = np.diag([0.04, 0.40]).astype(float)
A_REFERENCE = 0.75


def _sha_array(value: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(value).tobytes(order="C")).hexdigest()


def _independent_q(y: float) -> float:
    denominator = quad(
        lambda s: np.exp(5.0 * s * s),
        -A_REFERENCE,
        A_REFERENCE,
        epsabs=2e-13,
        epsrel=2e-13,
    )[0]
    numerator = quad(
        lambda s: np.exp(5.0 * s * s),
        -A_REFERENCE,
        y,
        epsabs=2e-13,
        epsrel=2e-13,
    )[0]
    return float(numerator / denominator)


def _independent_ou_covariance(dt: float) -> tuple[np.ndarray, np.ndarray]:
    nodes, weights = np.polynomial.legendre.leggauss(96)
    times = (nodes + 1.0) * dt / 2.0
    covariance = np.zeros((2, 2), dtype=float)
    for time, weight in zip(times, weights):
        transition = expm(J_REFERENCE * float(time))
        covariance += float(weight) * transition @ Q_REFERENCE @ transition.T
    covariance *= dt / 2.0
    return expm(J_REFERENCE * dt), covariance


def test_spec_freezes_control_grid_seed_namespace_and_budget() -> None:
    spec = b.build_spec()
    assert spec["experiment"] == "TRANS-0B2b"
    assert spec["semantics"]["state_dimension"] == 2
    assert spec["semantics"]["continuous_time_truth"] is False
    assert "between-grid" in spec["semantics"]["missed_crossings"]
    assert tuple(spec["dt_grid"]) == b.DT_GRID
    assert tuple(spec["horizon_grid"]) == b.HORIZON_GRID
    assert spec["n_reps"] == 4
    assert spec["n_paths_per_cell"] == 500
    assert b.expected_primary_cells() == 64
    assert b.expected_primary_updates() == 294_912_000
    assert b.validate_primary_budget()["within_cap"] is True
    with pytest.raises(ValueError):
        b.validate_primary_budget(max_updates=294_911_999)
    # 0B2a owns the same root integer but stage index zero.  This stage's
    # second entropy field is the namespace discriminator.
    assert b.STAGE_INDEX == 1
    assert b.ROOT_ENTROPY == 2_026_090_801
    assert b.build_spec()["sampling"]["seed_entropy"][1] == 1


@pytest.mark.parametrize("y", (-A_REFERENCE, 0.0, 0.6, A_REFERENCE))
def test_analytic_control_matches_independent_quadrature(y: float) -> None:
    assert b.analytic_q_control(y) == pytest.approx(_independent_q(y), abs=2e-13)


def test_analytic_control_rejects_outside_nonfinite_and_preserves_symmetry() -> None:
    assert b.analytic_q_control(0.0) == pytest.approx(0.5, abs=2e-14)
    assert b.analytic_q_control(0.6) == pytest.approx(0.7266191067696346, abs=2e-13)
    with pytest.raises(ValueError):
        b.analytic_q_control(A_REFERENCE + 1e-6)
    with pytest.raises(ValueError):
        b.analytic_q_control(float("nan"))
    assert b.analytic_q_control(np.asarray([-A_REFERENCE, 0.0, A_REFERENCE])).shape == (3,)


@pytest.mark.parametrize(
    ("n_b", "n_unresolved", "n_total"),
    ((0, 0, 10), (0, 10, 10), (10, 0, 10), (3, 0, 10), (3, 4, 10)),
)
def test_censor_bracket_uses_fixed_one_sided_tail_and_handles_edges(
    n_b: int, n_unresolved: int, n_total: int
) -> None:
    alpha = 0.05 / 8.0
    bracket = b.censor_bracket(n_b, n_unresolved, n_total, alpha=alpha)
    upper_successes = n_b + n_unresolved
    expected = [
        0.0 if n_b == 0 else float(beta.ppf(alpha, n_b, n_total - n_b + 1)),
        1.0
        if upper_successes == n_total
        else float(beta.ppf(1.0 - alpha, upper_successes + 1, n_total - upper_successes)),
    ]
    np.testing.assert_allclose(bracket, expected, rtol=0.0, atol=2e-14)
    assert bracket[0] <= bracket[1]
    assert b.CONTROL_GATE_ALPHA == pytest.approx(alpha, abs=0.0)


def test_censor_bracket_rejects_inconsistent_or_malformed_counts() -> None:
    with pytest.raises(ValueError):
        b.censor_bracket(8, 3, 10, alpha=0.05 / 8.0)
    with pytest.raises(ValueError):
        b.censor_bracket(1, 1, 0)
    with pytest.raises(ValueError):
        b.censor_bracket(True, 0, 10)
    with pytest.raises(ValueError):
        b.censor_bracket(1, 0, 10, alpha=0.0)


@pytest.mark.parametrize(
    ("states", "expected_label", "expected_time"),
    (
        (np.asarray([[0.0, 0.0], [0.1, 0.75], [0.0, 0.0]]), "B", 1 / 256),
        (np.asarray([[0.0, 0.0], [0.0, -0.75], [0.0, 0.75]]), "A", 1 / 256),
        (np.asarray([[12.0, 0.0], [3.0, 0.0], [1.0, 0.0]]), "unresolved", None),
        (np.asarray([[0.0, -0.75], [0.0, 0.75]]), "A", 0.0),
        (np.asarray([[0.0, 0.0], [99.0, 0.75], [99.0, -0.75]]), "B", 1 / 256),
    ),
)
def test_control_classifier_has_inclusive_earliest_horizontal_first_hit(
    states: np.ndarray, expected_label: str, expected_time: float | None
) -> None:
    result = b.classify_control_trajectory(states, dt=b.DT_GRID[0])
    assert result["first_label"] == expected_label
    if expected_time is None:
        assert result["first_time"] is None
        assert result["first_hit_state"] is None
    else:
        assert result["first_time"] == pytest.approx(expected_time)
        np.testing.assert_allclose(result["first_hit_state"], states[int(round(expected_time / b.DT_GRID[0]))])


def test_classifier_rejects_nonfinite_malformed_and_incomplete_grids() -> None:
    with pytest.raises(ValueError):
        b.classify_control_trajectory(np.zeros((3, 3)), dt=b.DT_GRID[0])
    with pytest.raises(ValueError):
        b.classify_control_trajectory(np.zeros((3, 2)), dt=1 / 1000)
    with pytest.raises(ValueError):
        b.classify_control_trajectory(np.asarray([[0.0, 0.0], [np.nan, 0.0]]), dt=b.DT_GRID[0])
    with pytest.raises(ValueError):
        b.classify_control_trajectory(np.zeros((3, 2)), dt=b.DT_GRID[0], horizon=3 * b.DT_GRID[0])
    with pytest.raises(ValueError):
        b.classify_control_trajectory(np.zeros((3, 2)), dt=b.DT_GRID[0], horizon=float("nan"))


def test_full_2d_em_state_updates_and_unresolved_endpoint_are_separate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Eliminate innovations so a scalar y-only implementation cannot hide
    # missing x-coordinate drift.  Endpoint U is assigned only to unresolved.
    monkeypatch.setattr(b.np.linalg, "cholesky", lambda _: np.zeros((2, 2)))
    start = np.asarray([0.2, 0.0])
    result = b.simulate_control_cell(
        start,
        n_paths=1,
        seed=UNIT_ROOT,
        engine="em_endpoint",
        dt=b.DT_GRID[0],
        horizon=16.0,
        return_path_rows=True,
        return_audit_traces=True,
    )
    transition = np.eye(2) + J_REFERENCE * b.DT_GRID[0]
    expected = start @ np.linalg.matrix_power(transition, 16 * 256).T
    np.testing.assert_allclose(result["endpoint_states"][0], expected, rtol=0.0, atol=1e-13)
    assert result["first_hit_counts"] == {"A": 0, "B": 0, "unresolved": 1}
    assert result["terminal_counts"]["U"] == 1
    assert result["terminal_counts"]["A"] == result["terminal_counts"]["B"] == 0
    row = result["path_rows"][0]
    assert row["first_label"] == "unresolved"
    assert row["endpoint_label"] == row["terminal_label"] == "U"
    assert row["first_time"] is None and row["first_hit_state"] is None
    assert result["audit_traces"][0]["states"][-1] == pytest.approx(expected.tolist())


def test_audit_trace_retains_first_hit_state_then_null_padding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def deterministic_hit(states: np.ndarray, innovations: np.ndarray, **_kwargs: object) -> np.ndarray:
        stepped = states.copy()
        stepped[:, 1] = 0.8
        return stepped

    monkeypatch.setattr(b, "_step_state", deterministic_hit)
    dt = b.DT_GRID[0]
    result = b.simulate_control_cell(
        np.asarray([0.0, 0.0]),
        n_paths=1,
        seed=UNIT_ROOT,
        engine="em_endpoint",
        dt=dt,
        horizon=2.0 * dt,
        return_path_rows=True,
        return_audit_traces=True,
    )

    row = result["path_rows"][0]
    trace = result["audit_traces"][0]["states"]
    assert row["first_label"] == "B"
    assert row["first_time"] == pytest.approx(dt)
    np.testing.assert_allclose(row["first_hit_state"], [0.0, 0.8])
    assert trace[0] == pytest.approx([0.0, 0.0])
    assert trace[1] == pytest.approx([0.0, 0.8])
    assert trace[2] is None


@pytest.mark.parametrize("engine", b.ENGINES)
def test_control_cells_partition_counts_for_both_engines_and_horizons(engine: str) -> None:
    engine_index = b.ENGINES.index(engine)
    seed = np.random.SeedSequence([UNIT_ROOT, 11, engine_index, 2, 1], spawn_key=(0, 0))
    result = b.simulate_control_cell(
        b.STARTS[1],
        n_paths=8,
        seed=seed,
        engine=engine,
        dt=b.DT_GRID[1],
        horizon=b.HORIZON_GRID[0],
        engine_index=engine_index,
        rep=2,
        start_index=1,
        horizon_index=0,
        dt_index=1,
        return_path_rows=True,
        return_audit_traces=True,
    )
    assert sum(result["first_hit_counts"].values()) == 8
    assert sum(result["terminal_counts"].values()) == 8
    joint = np.asarray(result["joint_counts"]["values"])
    assert joint.shape == (3, 4)
    assert int(joint.sum()) == 8
    np.testing.assert_array_equal(joint.sum(axis=1), [result["first_hit_counts"][x] for x in b.FIRST_LABELS])
    np.testing.assert_array_equal(joint.sum(axis=0), [result["terminal_counts"][x] for x in b.ENDPOINT_LABELS])
    assert len(result["path_rows"]) == 8
    assert len(result["audit_traces"]) == 2
    assert result["endpoint_source"].startswith("unresolved")
    assert "between-grid" in b.build_spec()["semantics"]["missed_crossings"]


def test_exact_ou_coefficients_match_independent_quadrature() -> None:
    dt = b.DT_GRID[1]
    phi, covariance, chol = b.transition_coefficients(dt)
    expected_phi, expected_covariance = _independent_ou_covariance(dt)
    np.testing.assert_allclose(phi, expected_phi, rtol=0.0, atol=2e-14)
    np.testing.assert_allclose(covariance, expected_covariance, rtol=0.0, atol=2e-13)
    assert np.all(np.linalg.eigvalsh(covariance) > 0.0)
    np.testing.assert_allclose(chol @ chol.T, covariance, rtol=0.0, atol=2e-13)
    assert abs(float(covariance[0, 1])) > 1e-8


def test_seed_identity_is_stage_distinct_and_dt_horizon_specific_without_draws() -> None:
    first, entropy0, spawn0 = b.seed_for_cell(0, 0, 0, 0, 0)
    second, entropy1, spawn1 = b.seed_for_cell(0, 0, 0, 1, 0)
    third, entropy2, spawn2 = b.seed_for_cell(0, 0, 0, 0, 1)
    assert entropy0 == entropy1 == entropy2 == [b.ROOT_ENTROPY, 1, 0, 0, 0]
    assert spawn0 == [0, 0]
    assert spawn1 == [1, 0]
    assert spawn2 == [0, 1]
    assert first.spawn_key != second.spawn_key != third.spawn_key
    # Generate only from an unrelated unit namespace for the distinction
    # check.  The declared primary SeedSequences above are never consumed.
    unit0 = np.random.SeedSequence([UNIT_ROOT, 1, 0, 0, 0], spawn_key=(0, 0))
    unit1 = np.random.SeedSequence([UNIT_ROOT, 1, 0, 0, 0], spawn_key=(1, 0))
    assert not np.array_equal(unit0.generate_state(8), unit1.generate_state(8))
    with pytest.raises(ValueError):
        b.seed_for_cell(0, 0, 0, 2, 0)


def test_primary_namespace_default_deny_and_declared_metadata_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    declared, seed_tuple, spawn_key = b.seed_for_cell(0, 0, 0, 0, 0)
    common = dict(
        start=b.STARTS[0], n_paths=1, engine="em_endpoint", dt=b.DT_GRID[0], horizon=16.0,
        engine_index=0, rep=0, start_index=0, horizon_index=0, dt_index=0,
        return_path_rows=False,
    )
    # Guard and metadata failures must occur before an RNG is constructed.
    def no_rng(*_args, **_kwargs):
        raise AssertionError("RNG draw/construction was attempted")

    monkeypatch.setattr(b.np.random, "default_rng", no_rng)
    with pytest.raises(RuntimeError, match="primary"):
        b.simulate_control_cell(seed=declared, **common)
    with pytest.raises(ValueError, match="actual SeedSequence entropy"):
        b.simulate_control_cell(
            seed=np.random.SeedSequence([UNIT_ROOT, 12]),
            seed_tuple=seed_tuple,
            seed_spawn_key=spawn_key,
            **common,
        )
    for malformed in ([b.ROOT_ENTROPY, 1, 0, 0, 0.5], [b.ROOT_ENTROPY, 1, 0, 0, True]):
        with pytest.raises(ValueError, match="seed_tuple"):
            b.simulate_control_cell(
                seed=np.random.SeedSequence([UNIT_ROOT, 12]),
                seed_tuple=malformed,
                seed_spawn_key=spawn_key,
                **common,
            )
    with pytest.raises(ValueError, match="seed_spawn_key"):
        b.simulate_control_cell(
            seed=np.random.SeedSequence([UNIT_ROOT, 12]),
            seed_tuple=seed_tuple,
            seed_spawn_key=[0.5, 0],
            **common,
        )


def test_em_refinement_aggregates_fine_brownian_increments_independently() -> None:
    seed = np.random.SeedSequence([UNIT_ROOT, 13, 0, 0, 0], spawn_key=(1, 0))
    n_paths = 3
    result = b.simulate_control_refinement(
        b.STARTS[0], n_paths=n_paths, seed=seed, engine="em_endpoint",
        fine_dt=b.DT_GRID[1], coarse_dt=b.DT_GRID[0], horizon=16.0,
    )
    fine_steps = 16 * 512
    rng = np.random.default_rng(np.random.SeedSequence([UNIT_ROOT, 13, 0, 0, 0], spawn_key=(1, 0)))
    z_fine = rng.standard_normal((n_paths, fine_steps, 2))
    expected_coarse = z_fine.reshape(n_paths, fine_steps // 2, 2, 2).sum(axis=2) / np.sqrt(2.0)
    assert result["coupling"]["method"].startswith("normalized sum")
    assert result["coupling"]["ratio"] == 2
    assert result["coupling"]["coarse_innovation_checksum"] == _sha_array(expected_coarse)
    assert result["coupling"]["claim_scope"].startswith("paired descriptive")


def test_exact_refinement_uses_ou_semigroup_noise_not_independent_normal_sum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Use a deterministic valid OU-like factorization so the byte checksum is
    # independent of tiny quadrature/Cholesky rounding differences between
    # this test and the production coefficient routine.  The real transition
    # coefficients are checked independently above.
    fixed_phi = np.asarray([[0.91, 0.07], [0.0, 0.83]], dtype=float)
    fixed_chol = np.asarray([[0.20, 0.0], [0.03, 0.17]], dtype=float)
    fixed_cov = fixed_chol @ fixed_chol.T
    monkeypatch.setattr(
        b,
        "transition_coefficients",
        lambda _dt: (fixed_phi.copy(), fixed_cov.copy(), fixed_chol.copy()),
    )
    seed_values = [UNIT_ROOT, 14, 1, 0, 1]
    seed = np.random.SeedSequence(seed_values, spawn_key=(1, 0))
    n_paths = 2
    result = b.simulate_control_refinement(
        b.STARTS[1], n_paths=n_paths, seed=seed, engine="exact_ou_grid",
        fine_dt=b.DT_GRID[1], coarse_dt=b.DT_GRID[0], horizon=16.0,
    )
    fine_steps = 16 * 512
    rng = np.random.default_rng(np.random.SeedSequence(seed_values, spawn_key=(1, 0)))
    z_fine = rng.standard_normal((n_paths, fine_steps, 2))
    phi = fixed_phi
    chol = fixed_chol
    blocks = z_fine.reshape(n_paths, fine_steps // 2, 2, 2)
    expected_coarse = np.empty((n_paths, fine_steps // 2, 2))
    for coarse_index in range(fine_steps // 2):
        noise = np.zeros((n_paths, 2))
        for fine_index in range(2):
            fine_noise = blocks[:, coarse_index, fine_index] @ chol.T
            noise += fine_noise @ np.linalg.matrix_power(phi, 1 - fine_index).T
        expected_coarse[:, coarse_index] = noise
    coupling = result["coupling"]
    assert coupling["method"].startswith("Phi_h L_h")
    assert "independent" not in coupling["method"]
    assert coupling["coarse_innovation_checksum"] == _sha_array(expected_coarse)


def test_refinement_rejects_primary_seed_before_rng() -> None:
    primary, _, _ = b.seed_for_cell(0, 0, 0, 0, 0)
    with pytest.raises(RuntimeError, match="primary"):
        b.simulate_control_refinement(
            b.STARTS[0], n_paths=1, seed=primary, engine="em_endpoint",
            fine_dt=b.DT_GRID[1], coarse_dt=b.DT_GRID[0], horizon=16.0,
        )


def test_runner_tiny_nonprimary_serialization_and_freeze_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise runner closure, gzip serialization, and overwrite refusal.

    The injected module uses UNIT_ROOT and a one-cell grid.  This checks the
    runner's freeze-before/after path and output schema without opening any
    replacement-namespace stream.
    """

    runner_path = Path(
        "H:/SourceRepo2/NeuralManifoldDynamics/project/astra/"
        "ndt_trans_0b2b_20260908/execute_primary.py"
    )
    loader = importlib.util.spec_from_file_location("test_trans_0b2b_runner", runner_path)
    assert loader is not None and loader.loader is not None
    runner = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(runner)

    source_path = tmp_path / "source.py"
    spec_path = tmp_path / "spec.json"
    protocol_path = tmp_path / "protocol.md"
    test_path = tmp_path / "tests.py"
    verifier_path = tmp_path / "verify.py"
    for path, contents in (
        (source_path, "# tiny frozen source\n"),
        (protocol_path, "tiny protocol\n"),
        (test_path, "# tiny independent test\n"),
        (verifier_path, "# tiny verifier\n"),
    ):
        path.write_text(contents, encoding="utf-8")

    tiny_spec = {
        "schema_version": "tiny.v1",
        "stage": "TRANS-0B2b",
        "role": "control_truth",
        "n_paths_per_cell": 2,
        "max_state_step_updates": 10,
        "tiny": True,
    }
    spec_path.write_text(json.dumps(tiny_spec), encoding="utf-8")

    tiny = types.SimpleNamespace(
        SCHEMA_VERSION="tiny.v1",
        STAGE="TRANS-0B2b",
        CONTROL_ROLE="control_truth",
        PDE_ROLE="pde_reference",
        ENGINES=("em_endpoint",),
        N_REPS=1,
        STARTS=np.asarray([[0.0, 0.0]]),
        HORIZON_GRID=(1.0,),
        DT_GRID=(1.0,),
        PDE_R_GRID=(3.0,),
        PDE_MESH_GRID={"3": ((5, 5),)},
        PDE_T_GRID=(1.0,),
        PDE_DT_GRID=(1.0,),
        CONTROL_THRESHOLD=0.75,
    )
    tiny.build_spec = lambda: dict(tiny_spec)
    tiny.runtime_metadata = lambda: {"python": "tiny", "numpy": "tiny", "scipy": "tiny", "rng": "tiny"}

    def tiny_validate_primary_budget(*, n_paths: int, max_updates: int) -> dict[str, object]:
        assert n_paths == 2 and max_updates == 10
        return {"n_cells": 1, "within_cap": True}

    def tiny_seed_for_cell(engine_index: int, rep: int, start_index: int, horizon_index: int, dt_index: int):
        return np.random.SeedSequence([UNIT_ROOT, 88], spawn_key=(0, 0)), [UNIT_ROOT, 88], [0, 0]

    def tiny_simulate_control_cell(
        start, *, n_paths, seed, engine, dt, horizon, engine_index, rep,
        start_index, horizon_index, dt_index, seed_tuple, seed_spawn_key,
        return_path_rows, return_audit_traces, allow_primary,
    ):
        assert n_paths == 2 and return_path_rows and return_audit_traces and allow_primary
        rows, traces = [], []
        for local_index in range(n_paths):
            path_id = f"tiny-{local_index}"
            rows.append({
                "stage": tiny.STAGE, "role": tiny.CONTROL_ROLE, "engine": engine,
                "engine_index": engine_index, "rep": rep, "start_index": start_index,
                "horizon_index": horizon_index, "dt_index": dt_index, "dt": dt,
                "horizon": horizon, "path_id": path_id, "local_path_index": local_index,
                "seed_tuple": seed_tuple, "seed_spawn_key": seed_spawn_key,
                "first_label": "unresolved", "first_time": None, "first_hit_state": None,
                "endpoint_state": [0.0, 0.0], "endpoint_label": "U", "terminal_label": "U",
            })
            traces.append({"path_id": path_id, "local_path_index": local_index, "states": [[0.0, 0.0], [0.0, 0.0]]})
        return {
            "schema_version": tiny.SCHEMA_VERSION, "stage": tiny.STAGE, "role": tiny.CONTROL_ROLE,
            "engine": engine, "engine_index": engine_index, "rep": rep, "start_index": start_index,
            "horizon_index": horizon_index, "dt_index": dt_index, "dt": dt, "horizon": horizon,
            "n_steps": 1, "n_total": n_paths,
            "first_hit_counts": {"A": 0, "B": 0, "unresolved": n_paths},
            "endpoint_counts": {"A": 0, "B": 0, "U": n_paths, "no_endpoint_absorbed": 0},
            "terminal_counts": {"A": 0, "B": 0, "U": n_paths, "no_endpoint_absorbed": 0},
            "joint_counts": {"first_hit_rows": ["A", "B", "unresolved"], "endpoint_columns": ["A", "B", "U", "no_endpoint_absorbed"], "values": [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, n_paths, 0]]},
            "unresolved_fraction": 1.0, "p_B_observed": 0.0, "p_not_A_observed": 1.0,
            "censor_bracket_p_B": [0.0, 1.0], "first_hit_state_checksum": "tiny",
            "endpoint_state_checksum": "tiny", "terminal_state_checksum": None,
            "path_rows_checksum": "tiny", "endpoint_source": "unresolved endpoint at declared horizon",
            "seed": {"entropy": [UNIT_ROOT, 88], "spawn_key": [0, 0]},
            "seed_tuple": seed_tuple, "seed_spawn_key": seed_spawn_key,
            "rng_contract": "tiny", "path_rows": rows, "audit_traces": traces,
        }

    tiny.validate_primary_budget = tiny_validate_primary_budget
    tiny.expected_primary_cells = lambda: 1
    tiny.seed_for_cell = tiny_seed_for_cell
    tiny.simulate_control_cell = tiny_simulate_control_cell

    def tiny_solve_elliptic_reference(*, R, n_r, n_s, artificial_boundary="neumann"):
        r_grid = np.linspace(-0.75, 0.75, n_r)
        s_grid = np.linspace(-R, R, n_s)
        values = np.tile(np.linspace(0.0, 1.0, n_r)[:, None], (1, n_s))
        return {
            "mesh": {"n_r": n_r, "n_s": n_s, "h_r": float(r_grid[1] - r_grid[0]), "h_s": float(s_grid[1] - s_grid[0])},
            "r_grid": r_grid, "s_grid": s_grid, "values": values,
            "start_coordinates_rs": np.asarray([[0.0, 0.0]]), "start_values": [0.5],
            "transformed_drift": np.zeros((2, 2)), "transformed_diffusion": np.eye(2),
            "operator": "tiny operator", "boundary_condition": {"r=-a": 0.0, "r=+a": 1.0, "s": artificial_boundary},
            "cross_diffusion": "axis/anti-diagonal wide jump representation",
            "drift_discretization": "first-order upwind", "solver": "tiny", "solver_tolerance": 1e-12,
            "max_scaled_residual": 0.0, "boundary_residual_max": 0.0, "range": [0.0, 1.0],
            "within_unit_interval": True, "monotone_generator": True,
            "monotonicity_certificate": {"status": "DECLARED", "reason": "tiny nonnegative rates"},
            "method_status": "METHOD_LIMITED",
        }

    tiny.solve_elliptic_reference = tiny_solve_elliptic_reference
    monkeypatch.setattr(runner, "SOURCE", source_path)
    monkeypatch.setattr(runner, "load_module", lambda: tiny)
    manifest_paths = (source_path, spec_path, protocol_path, test_path, verifier_path, runner_path)
    manifest = {
        "status": "FROZEN",
        "runtime": tiny.runtime_metadata(),
        "files": {str(path): runner.sha256_file(path) for path in manifest_paths},
    }
    manifest_path = tmp_path / "freeze_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    primary_root = tmp_path / "primary"
    result = runner.execute_primary(
        spec_path=spec_path, protocol_path=protocol_path,
        freeze_manifest_path=manifest_path, test_path=test_path,
        verifier_path=verifier_path, primary_root=primary_root,
    )
    assert result["status"] == "COMPLETE"
    with gzip.open(primary_root / "paths.jsonl.gz", "rt", encoding="utf-8") as handle:
        path_rows = [json.loads(line) for line in handle]
    with gzip.open(primary_root / "audit_traces.jsonl.gz", "rt", encoding="utf-8") as handle:
        trace_rows = [json.loads(line) for line in handle]
    counts = json.loads((primary_root / "counts.json").read_text(encoding="utf-8"))
    assert len(path_rows) == len(trace_rows) == 2
    assert counts["status"] == "COMPLETE" and counts["completed_cells"] == 1
    assert counts["n_path_rows"] == counts["n_audit_traces"] == 2
    coupling = json.loads((primary_root / "coupling.json").read_text(encoding="utf-8"))
    assert coupling["status"] == "DECLARED_UNPAIRED"
    with pytest.raises(FileExistsError):
        runner.execute_primary(
            spec_path=spec_path, protocol_path=protocol_path,
            freeze_manifest_path=manifest_path, test_path=test_path,
            verifier_path=verifier_path, primary_root=primary_root,
        )


def test_pde_spec_coefficients_mesh_completeness_and_stencil_certificate() -> None:
    spec = b.build_spec()["pde"]
    basis = np.asarray([[1.0, 1.0], [1.0, -1.0]]) / np.sqrt(2.0)
    expected_drift = basis @ J_REFERENCE @ basis.T
    expected_diffusion = basis @ Q_REFERENCE @ basis.T
    np.testing.assert_allclose(spec["transformed_drift"], expected_drift, rtol=0.0, atol=2e-14)
    np.testing.assert_allclose(spec["transformed_diffusion"], expected_diffusion, rtol=0.0, atol=2e-14)
    assert spec["artificial_boundary"].startswith("homogeneous numerical Neumann")
    assert "physical" not in spec["artificial_boundary"].lower()
    # The replacement axis/anti-diagonal stencil is allowed to make a
    # monotone-generator claim only because its declared mesh ratio is checked
    # below.  This prevents a future centred mixed derivative from inheriting
    # that claim silently.
    assert spec["monotone_generator_claim"] is True
    assert "nonnegative" in spec["comparison_principle"]
    assert spec["method_status"] in {"METHOD_LIMITED", "NUMERICAL_REFERENCE_CANDIDATE", "INCONCLUSIVE"}
    assert "wide jump" in spec["stencil"]
    assert len(spec["R_grid"]) == 4
    lo, hi = 9.0 / 11.0, 11.0 / 9.0
    for radius in b.PDE_R_GRID:
        meshes = b.PDE_MESH_GRID[str(int(radius))]
        assert len(meshes) == 3
        for n_r, n_s in meshes:
            assert isinstance(n_r, int) and n_r >= 5
            assert n_r * n_s <= b.PDE_SPATIAL_NODE_CAP
            h_r = 1.5 / (n_r - 1)
            h_s = 2.0 * radius / (n_s - 1)
            assert lo <= h_r / h_s <= hi


def _assert_pde_diagnostics_are_fail_closed(result: dict[str, object]) -> None:
    for key in ("max_scaled_residual", "boundary_residual_max"):
        assert np.isfinite(float(result[key]))
    minimum, maximum = result["range"]
    assert np.isfinite(minimum) and np.isfinite(maximum)
    if float(result["max_scaled_residual"]) > 1e-6 or not bool(result["within_unit_interval"]):
        assert result["method_status"] in {"METHOD_LIMITED", "INCONCLUSIVE", "UNRUN"}


def _independent_wide_residual(result: dict[str, object]) -> tuple[float, dict[str, float]]:
    """Recompute the declared axis/anti-diagonal generator from the grid."""

    r = np.asarray(result["r_grid"], dtype=float)
    s = np.asarray(result["s_grid"], dtype=float)
    values = np.asarray(result["values"], dtype=float)
    h_r = float(r[1] - r[0])
    h_s = float(s[1] - s[0])
    assert np.allclose(np.diff(r), h_r, rtol=0.0, atol=1e-12)
    assert np.allclose(np.diff(s), h_s, rtol=0.0, atol=1e-12)
    # These are the coefficients from Q_rs, written independently of the
    # implementation's stored rates.
    cross = 0.18 / (2.0 * h_r * h_s)
    r_axis = (0.11 - cross * h_r * h_r) / (h_r * h_r)
    s_axis = (0.11 - cross * h_s * h_s) / (h_s * h_s)
    total = 2.0 * (r_axis + s_axis + cross)
    residuals: list[float] = []
    for i in range(1, len(r) - 1):
        for j in range(1, len(s) - 1):
            value = -total * values[i, j]
            value += r_axis * (values[i - 1, j] + values[i + 1, j])
            value += s_axis * (values[i, j - 1] + values[i, j + 1])
            value += cross * (values[i - 1, j + 1] + values[i + 1, j - 1])
            b_r, b_s = -s[j], 2.0 * r[i] - 3.0 * s[j]
            if b_r >= 0.0:
                value += b_r / h_r * (values[i + 1, j] - values[i, j])
            else:
                value += -b_r / h_r * (values[i - 1, j] - values[i, j])
            if b_s >= 0.0:
                value += b_s / h_s * (values[i, j + 1] - values[i, j])
            else:
                value += -b_s / h_s * (values[i, j - 1] - values[i, j])
            residuals.append(float(value))
    return float(np.max(np.abs(residuals))), {
        "r_axis": r_axis,
        "s_axis": s_axis,
        "anti_diagonal": cross,
        "h_r_over_h_s": h_r / h_s,
    }


def test_wide_stencil_rates_and_residual_are_reconstructible_independently() -> None:
    result = b.solve_elliptic_reference(R=3.0, n_r=9, n_s=33)
    independent_residual, rates = _independent_wide_residual(result)
    assert rates["r_axis"] >= 0.0
    assert rates["s_axis"] >= 0.0
    assert rates["anti_diagonal"] > 0.0
    assert 9.0 / 11.0 <= rates["h_r_over_h_s"] <= 11.0 / 9.0
    assert result["monotone_generator"] is True
    np.testing.assert_allclose(
        independent_residual, float(result["max_scaled_residual"]), rtol=0.0, atol=1e-10
    )
    assert result["within_unit_interval"] is True
    assert result["range"][0] >= -1e-12 and result["range"][1] <= 1.0 + 1e-12


def test_elliptic_pde_reports_boundaries_residual_range_and_rejects_stress_claim() -> None:
    result = b.solve_elliptic_reference(
        R=3.0, n_r=9, n_s=33, artificial_boundary="neumann", include_stress_envelope=True
    )
    _assert_pde_diagnostics_are_fail_closed(result)
    assert result["boundary_condition"] == {"r=-a": 0.0, "r=+a": 1.0, "s": "neumann"}
    assert result["cross_diffusion"].startswith("axis/anti-diagonal")
    assert result["drift_discretization"].startswith("first-order upwind")
    assert result["monotone_generator"] is True
    assert result["monotonicity_certificate"]["status"] in {"DECLARED", "PROVED"}
    envelope = result["stress_envelope"]
    assert isinstance(envelope["comparison_envelope_claim"], bool)
    assert envelope["fixed0"]["method_status"] in {"METHOD_LIMITED", "NUMERICAL_REFERENCE_CANDIDATE", "INCONCLUSIVE"}
    assert envelope["fixed1"]["method_status"] in {"METHOD_LIMITED", "NUMERICAL_REFERENCE_CANDIDATE", "INCONCLUSIVE"}
    if envelope["comparison_envelope_claim"]:
        assert result["monotone_generator"] is True
        assert result["monotonicity_certificate"]["status"] in {"DECLARED", "PROVED"}


def test_pde_domain_stress_and_mesh_failure_guards_are_bounded() -> None:
    result = b.solve_elliptic_reference(R=3.0, n_r=9, n_s=33)
    assert result["domain"] == {"r": [-b.CONTROL_THRESHOLD, b.CONTROL_THRESHOLD], "s": [-3.0, 3.0]}
    assert result["solution"].shape == (9, 33)
    np.testing.assert_allclose(result["solution"][0, :], 0.0, rtol=0.0, atol=0.0)
    np.testing.assert_allclose(result["solution"][-1, :], 1.0, rtol=0.0, atol=0.0)
    assert result["boundary_condition"]["s"] == "neumann"
    assert result["artificial_boundary_residual_max"] <= 1e-10
    # This deliberately violates 9/11 <= h_r/h_s <= 11/9 while remaining
    # small enough to reach the stencil-rate guard before allocation limits.
    with pytest.raises(ValueError, match="mesh ratio"):
        b.solve_elliptic_reference(R=3.0, n_r=9, n_s=45)
    with pytest.raises(ValueError, match="artificial_boundary"):
        b.solve_elliptic_reference(R=3.0, n_r=9, n_s=33, artificial_boundary="reflection")
    with pytest.raises(ValueError, match="spatial-node cap"):
        b.solve_elliptic_reference(R=3.0, n_r=1001, n_s=1001)


def test_small_domain_and_spatial_refinement_rows_are_explicit_and_bounded() -> None:
    # Aligned small meshes make h_r/h_s exactly one for these two domains.
    R5 = b.solve_elliptic_reference(R=5.0, n_r=7, n_s=41)
    R6 = b.solve_elliptic_reference(R=6.0, n_r=7, n_s=49)
    assert max(abs(x - y) for x, y in zip(R5["start_values"], R6["start_values"])) <= 0.005
    coarse = b.solve_elliptic_reference(R=3.0, n_r=7, n_s=25)
    refined = b.solve_elliptic_reference(R=3.0, n_r=9, n_s=33)
    assert max(abs(x - y) for x, y in zip(coarse["start_values"], refined["start_values"])) <= 0.005
    for row in (R5, R6, coarse, refined):
        assert row["mesh"]["nodes"] <= b.PDE_SPATIAL_NODE_CAP
        assert row["method_status"] in {"NUMERICAL_REFERENCE_CANDIDATE", "METHOD_LIMITED", "INCONCLUSIVE"}


def test_parabolic_pde_records_time_equation_and_fails_closed_on_bad_range() -> None:
    result = b.solve_parabolic_reference(
        horizon=1.0, dt_pde=1.0 / 256.0, R=3.0, n_r=9, n_s=33,
        artificial_boundary="neumann"
    )
    # The elliptic residual field is not the parabolic evolution residual;
    # require the latter explicitly and fail closed if the solution leaves the
    # probability range.
    for key in ("max_scaled_residual", "boundary_residual_max", "partial_T_q_minus_L_q_final_step_max"):
        assert np.isfinite(float(result[key]))
    assert result["within_unit_interval"] is True
    assert float(result["partial_T_q_minus_L_q_final_step_max"]) <= 1e-6
    assert result["boundary_condition"]["initial_interior"] == 0.0
    assert result["boundary_condition"]["r=-a"] == 0.0
    assert result["boundary_condition"]["r=+a"] == 1.0
    assert result["boundary_condition"]["s"] == "neumann"
    assert result["partial_T_q_equals_L_q"] is True
    assert "corner" in result["weak_corner_compatibility"].lower()
    assert result["time_integrator"].startswith("implicit Euler")
    # A parabolic candidate is acceptable only when its final-step PDE
    # residual is explicitly reported; this test does not promote it to a
    # qualified truth object.
    assert np.isfinite(float(result["partial_T_q_minus_L_q_final_step_max"]))
    if float(result["partial_T_q_minus_L_q_final_step_max"]) > 1e-6:
        assert result["method_status"] in {"METHOD_LIMITED", "INCONCLUSIVE", "NUMERICAL_REFERENCE_CANDIDATE"}
    # A between-grid horizon may be computed for a bounded diagnostic, but it
    # must remain explicitly identified by its requested duration and status;
    # it cannot silently become a declared T={1,4,16} refinement claim.
    between_grid = b.solve_parabolic_reference(
        horizon=2.0, dt_pde=1.0 / 256.0, R=3.0, n_r=9, n_s=33
    )
    assert between_grid["horizon"] == 2.0
    assert between_grid["n_steps"] == 512
    assert between_grid["horizon"] not in b.PDE_T_GRID
    assert between_grid["method_status"] in {
        "METHOD_LIMITED", "INCONCLUSIVE", "NUMERICAL_REFERENCE_CANDIDATE"
    }
    with pytest.raises(ValueError):
        b.solve_parabolic_reference(horizon=1.0, dt_pde=1.0 / 1000.0, R=3.0, n_r=9, n_s=33)
