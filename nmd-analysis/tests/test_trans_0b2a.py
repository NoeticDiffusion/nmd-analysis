"""Independent nonprimary tests for TRANS-0B2a semantics.

These tests deliberately use fixtures, seeds, and a transition calculation
that are independent of the prospective primary namespace.  They exercise
the public analysis contract rather than reproducing the simulator's private
implementation.
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import types
from pathlib import Path

import numpy as np
import pytest
from scipy.linalg import expm

from nmd_analysis.dynamical_families import trans_0b2a as b


UNIT_ROOT = 87_431_209
J_REFERENCE = np.asarray([[-1.0, 3.0], [0.0, -2.0]], dtype=float)
Q_REFERENCE = np.diag([0.04, 0.40]).astype(float)


def _state_for_projection(projection: float) -> np.ndarray:
    """Return a full 2-D state on the target normal, with given projection."""

    # Dividing by one component makes the subsequent floating-point dot
    # product equal to the requested representable threshold (including .75).
    return np.asarray([projection / b.TARGET_DIRECTION[0], 0.0], dtype=float)


def _fixture(*projections: float) -> np.ndarray:
    return np.vstack([_state_for_projection(value) for value in projections])


def test_spec_freezes_semantics_and_amended_resource_budget() -> None:
    spec = b.build_spec()
    assert spec["experiment"] == "TRANS-0B2a"
    assert spec["semantics"]["state_dimension"] == 2
    assert spec["semantics"]["continuous_time_truth"] is False
    assert spec["semantics"]["terminal"].startswith("continuation state")
    assert tuple(spec["dt_grid"]) == b.DT_GRID
    assert spec["n_paths_per_cell"] == 1_000
    assert b.expected_primary_cells() == 48
    budget = b.validate_primary_budget()
    assert budget["estimated_state_step_updates"] == 28_672_000
    assert budget["within_cap"] is True


@pytest.mark.parametrize(
    ("projections", "first_label", "terminal_label", "first_time"),
    [
        ((0.0, 0.75, 0.0), "B", "U", 1 / 128),
        ((0.0, -0.75, 0.75), "A", "B", 1 / 128),
        ((0.0, 0.0, 0.0), "unresolved", "U", None),
        ((0.0, 0.75), "B", "B", 1 / 128),
        ((0.0, 0.75, -0.75, 0.0), "B", "U", 1 / 128),
    ],
)
def test_hand_fixtures_preserve_first_hit_and_terminal_semantics(
    projections: tuple[float, ...],
    first_label: str,
    terminal_label: str,
    first_time: float | None,
) -> None:
    result = b.classify_trajectory(_fixture(*projections), dt=b.DT_GRID[0])
    assert result["first_label"] == first_label
    assert result["terminal_label"] == terminal_label
    if first_time is None:
        assert result["first_time"] is None
        assert result["first_hit_state"] is None
    else:
        assert result["first_time"] == pytest.approx(first_time)
        assert result["first_hit_state"] is not None


def test_initial_boundary_is_an_inclusive_t0_hit() -> None:
    result = b.classify_trajectory(
        _fixture(-0.75, 0.0), dt=b.DT_GRID[0]
    )
    assert result["first_label"] == "A"
    assert result["first_time"] == 0.0
    np.testing.assert_allclose(result["first_hit_state"], _state_for_projection(-0.75))


def test_classification_requires_complete_finite_regular_grid() -> None:
    with pytest.raises(ValueError):
        b.classify_trajectory(np.zeros((3, 2)), dt=1 / 1000)
    with pytest.raises(ValueError):
        b.classify_trajectory(np.zeros((3, 2)), dt=b.DT_GRID[0], horizon=4 * b.DT_GRID[0])
    with pytest.raises(ValueError):
        b.classify_trajectory(np.zeros((3, 2)), dt=b.DT_GRID[0], horizon=float("nan"))
    with pytest.raises(ValueError):
        b.classify_trajectory(np.asarray([[0.0, 0.0], [np.nan, 0.0]]), dt=b.DT_GRID[0])
    with pytest.raises(ValueError):
        b.classify_trajectory(np.zeros((3, 3)), dt=b.DT_GRID[0])
    with pytest.raises(ValueError):
        b.classify_trajectory(np.zeros((0, 2)), dt=b.DT_GRID[0])


def test_full_two_dimensional_em_drift_is_applied(monkeypatch: pytest.MonkeyPatch) -> None:
    # Remove only the innovation in this test.  A scalar projected update
    # would produce a different second coordinate and fail this check.
    monkeypatch.setattr(b.np.linalg, "cholesky", lambda _: np.zeros((2, 2)))
    start = np.asarray([0.2, -0.1], dtype=float)
    result = b.simulate_first_hit(
        start,
        n_paths=1,
        seed=UNIT_ROOT,
        engine="em_endpoint",
        dt=b.DT_GRID[0],
        horizon=b.T,
        return_path_rows=False,
        return_states=True,
    )
    expected = start @ np.linalg.matrix_power(np.eye(2) + J_REFERENCE * b.DT_GRID[0], int(round(b.T / b.DT_GRID[0]))).T
    np.testing.assert_allclose(result["continuation_states"][0], expected, rtol=0, atol=1e-14)
    np.testing.assert_allclose(result["first_hit_states"][0], np.full(2, np.nan), equal_nan=True)


def test_exact_ou_coefficients_match_independent_gauss_legendre_quadrature() -> None:
    dt = b.DT_GRID[1]
    phi, covariance, chol = b.transition_coefficients(dt)
    np.testing.assert_allclose(phi, expm(J_REFERENCE * dt), rtol=0, atol=1e-14)

    # This calculation does not use the implementation's block exponential.
    nodes, weights = np.polynomial.legendre.leggauss(64)
    times = (nodes + 1.0) * dt / 2.0
    independent_covariance = np.zeros((2, 2), dtype=float)
    for time, weight in zip(times, weights):
        transition = expm(J_REFERENCE * float(time))
        independent_covariance += float(weight) * (transition @ Q_REFERENCE @ transition.T)
    independent_covariance *= dt / 2.0
    np.testing.assert_allclose(covariance, independent_covariance, rtol=0, atol=1e-13)
    assert np.all(np.linalg.eigvalsh(covariance) > 0)
    np.testing.assert_allclose(chol @ chol.T, covariance, rtol=0, atol=1e-13)
    # The off-diagonal innovation covariance is a useful check that the full
    # non-normal 2-D law was retained.
    assert abs(float(covariance[0, 1])) > 1e-8


@pytest.mark.parametrize("engine", b.ENGINES)
def test_replay_is_deterministic_for_both_engines_and_both_state_copies(engine: str) -> None:
    seed = np.random.SeedSequence([UNIT_ROOT, 3, b.ENGINES.index(engine), 2, 1])
    kwargs = dict(
        start=b.STARTS[1],
        n_paths=64,
        seed=seed,
        engine=engine,
        dt=b.DT_GRID[0],
        horizon=b.T,
        engine_index=b.ENGINES.index(engine),
        rep=2,
        start_index=1,
        dt_index=0,
        return_path_rows=True,
        return_states=True,
    )
    first = b.simulate_first_hit(**kwargs)
    second = b.simulate_first_hit(**kwargs)
    assert first["continuation_state_checksum"] == second["continuation_state_checksum"]
    assert first["first_hit_state_checksum"] == second["first_hit_state_checksum"]
    assert first["path_rows_checksum"] == second["path_rows_checksum"]
    np.testing.assert_array_equal(first["continuation_states"], second["continuation_states"])
    np.testing.assert_array_equal(first["first_hit_states"], second["first_hit_states"])
    assert first["continuation_states"] is not first["first_hit_states"]
    assert len(first["path_rows"]) == 64


def test_counts_joint_table_and_path_roles_partition_exactly() -> None:
    seed = np.random.SeedSequence([UNIT_ROOT, 4, 0, 1, 0], spawn_key=(2,))
    result = b.simulate_first_hit(
        b.STARTS[0],
        n_paths=128,
        seed=seed,
        engine="em_endpoint",
        dt=b.DT_GRID[2],
        horizon=b.T,
        engine_index=0,
        rep=1,
        start_index=0,
        dt_index=2,
        return_path_rows=True,
        return_states=True,
    )
    assert sum(result["first_hit_counts"].values()) == 128
    assert sum(result["terminal_counts"].values()) == 128
    joint = np.asarray(result["joint_counts"]["values"])
    assert joint.shape == (3, 3)
    assert int(joint.sum()) == 128
    np.testing.assert_array_equal(joint.sum(axis=1), [result["first_hit_counts"][label] for label in b.FIRST_LABELS])
    np.testing.assert_array_equal(joint.sum(axis=0), [result["terminal_counts"][label] for label in b.TERMINAL_LABELS])
    assert len({row["path_id"] for row in result["path_rows"]}) == 128
    for row in result["path_rows"]:
        assert row["seed_tuple"] is None
        assert row["seed_spawn_key"] == [2]
        assert row["terminal_source"] if "terminal_source" in row else True
        if row["first_label"] == "unresolved":
            assert row["first_time"] is None
            assert row["first_hit_state"] is None
        else:
            assert row["first_time"] is not None
            assert row["first_hit_state"] is not None


def test_declared_seed_metadata_is_bound_and_strictly_typed() -> None:
    declared_seed, seed_tuple, spawn_key = b.seed_for_cell(0, 0, 0, 0)
    assert list(declared_seed.entropy) == seed_tuple
    assert list(declared_seed.spawn_key) == spawn_key

    common = dict(
        start=b.STARTS[0],
        n_paths=1,
        engine="em_endpoint",
        dt=b.DT_GRID[0],
        horizon=b.DT_GRID[0],
        engine_index=0,
        rep=0,
        start_index=0,
        dt_index=0,
        seed_spawn_key=spawn_key,
        return_path_rows=False,
    )
    # Metadata must describe the actual supplied stream, before any random
    # draw.  This uses an unrelated unit-test stream and never draws from the
    # primary namespace.
    with pytest.raises(ValueError):
        b.simulate_first_hit(
            seed=np.random.SeedSequence([UNIT_ROOT, 5]),
            seed_tuple=seed_tuple,
            **common,
        )
    # Even a correctly formed replacement primary seed is denied by default;
    # only the frozen runner may explicitly opt in after its freeze check.
    with pytest.raises(RuntimeError, match="primary"):
        b.simulate_first_hit(
            seed=declared_seed,
            seed_tuple=seed_tuple,
            **common,
        )
    for malformed in (
        [b.ROOT_ENTROPY, b.STAGE_INDEX, 0, 0, 0.5],
        [b.ROOT_ENTROPY, b.STAGE_INDEX, 0, 0, True],
    ):
        with pytest.raises(ValueError):
            b.simulate_first_hit(
                seed=np.random.SeedSequence([UNIT_ROOT, 6]),
                seed_tuple=malformed,
                **common,
            )
    for malformed_spawn in ([0.5], [True]):
        with pytest.raises(ValueError):
            b.simulate_first_hit(
                seed=np.random.SeedSequence([UNIT_ROOT, 6]),
                seed_tuple=seed_tuple,
                seed_spawn_key=malformed_spawn,
                **{key: value for key, value in common.items() if key != "seed_spawn_key"},
            )


def test_seed_identity_includes_dt_without_reusing_streams() -> None:
    first, first_entropy, first_spawn = b.seed_for_cell(1, 0, 1, 0)
    second, second_entropy, second_spawn = b.seed_for_cell(1, 0, 1, 1)
    assert first_entropy == second_entropy == [b.ROOT_ENTROPY, b.STAGE_INDEX, 1, 0, 1]
    assert first_spawn == [0]
    assert second_spawn == [1]
    assert first.spawn_key != second.spawn_key
    # Compare generated words only on an unrelated unit-test namespace; the
    # frozen primary streams are never consumed by this test.
    unit_first = np.random.SeedSequence([UNIT_ROOT, b.STAGE_INDEX, 1, 0, 1], spawn_key=(0,))
    unit_second = np.random.SeedSequence([UNIT_ROOT, b.STAGE_INDEX, 1, 0, 1], spawn_key=(1,))
    assert not np.array_equal(unit_first.generate_state(8), unit_second.generate_state(8))
    with pytest.raises(ValueError):
        b.seed_for_cell(1, 0, 1, 3)


def test_simulator_rejects_unsupported_or_malformed_cell_inputs() -> None:
    common = dict(n_paths=4, seed=UNIT_ROOT, engine="em_endpoint", dt=b.DT_GRID[0])
    with pytest.raises(ValueError):
        b.simulate_first_hit([0.0, 0.0], **{**common, "engine": "bad"})
    with pytest.raises(ValueError):
        b.simulate_first_hit([0.0, 0.0], **{**common, "dt": 1 / 1000})
    with pytest.raises(ValueError):
        b.simulate_first_hit([0.0, 0.0], **{**common, "horizon": b.DT_GRID[0] / 2})
    with pytest.raises(ValueError):
        b.simulate_first_hit([0.0, 0.0], **{**common, "horizon": 2 * b.T})
    with pytest.raises(ValueError):
        b.simulate_first_hit([0.0, float("nan")], **common)
    with pytest.raises(ValueError):
        b.simulate_first_hit([0.0, 0.0], **{**common, "n_paths": 0})
    with pytest.raises(ValueError):
        b.simulate_first_hit([0.0, 0.0], **{**common, "n_paths": b.N_PATHS_PER_CELL + 1})
    with pytest.raises(ValueError):
        b.simulate_first_hit(
            b.STARTS[0],
            **{**common, "engine_index": 1},
        )


def test_censor_bracket_rejects_inconsistent_counts() -> None:
    bracket = b.censor_bracket(2, 3, 10)
    assert 0.0 <= bracket[0] <= bracket[1] <= 1.0
    with pytest.raises(ValueError):
        b.censor_bracket(8, 3, 10)
    with pytest.raises(ValueError):
        b.censor_bracket(1, 1, 0)


def test_runner_tiny_nonprimary_serialization_and_overwrite_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise runner closure, gzip rows, counts, and fail-closed reruns.

    A tiny fake module is injected after the runner is imported.  The runner
    still verifies a complete temporary freeze manifest and writes the same
    output file families used by the primary path; no primary cell is drawn.
    """

    runner_path = Path(
        "H:/SourceRepo2/NeuralManifoldDynamics/project/astra/"
        "ndt_trans_0b2a_20260908/execute_primary.py"
    )
    loader = importlib.util.spec_from_file_location("test_trans_0b2a_runner", runner_path)
    assert loader is not None and loader.loader is not None
    runner = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(runner)

    source_path = tmp_path / "source.py"
    spec_path = tmp_path / "spec.json"
    protocol_path = tmp_path / "protocol.md"
    test_path = tmp_path / "tests.py"
    verifier_path = tmp_path / "verify.py"
    for path, contents in (
        (source_path, "# tiny frozen simulator source\n"),
        (protocol_path, "tiny protocol\n"),
        (test_path, "# tiny independent tests\n"),
        (verifier_path, "# tiny verifier\n"),
    ):
        path.write_text(contents, encoding="utf-8")

    tiny_spec = {
        "horizon_grid": [1.0],
        "n_paths_per_cell": 2,
        "max_state_step_updates": 10,
        "tiny": True,
    }
    spec_path.write_text(json.dumps(tiny_spec), encoding="utf-8")
    tiny = types.SimpleNamespace()
    tiny.SCHEMA_VERSION = "tiny.v1"
    tiny.STAGE = "TRANS-0B2a"
    tiny.ROLE = "semantic_pilot"
    tiny.ENGINES = ("em_endpoint",)
    tiny.N_REPS = 1
    tiny.STARTS = np.asarray([[0.0, 0.0]])
    tiny.DT_GRID = (1.0,)

    def tiny_build_spec() -> dict[str, object]:
        return dict(tiny_spec)

    def tiny_runtime_metadata() -> dict[str, str]:
        return {"python": "tiny", "numpy": "tiny", "scipy": "tiny", "rng": "tiny"}

    def tiny_validate_primary_budget(*, n_paths: int, max_updates: int) -> dict[str, object]:
        assert n_paths == 2 and max_updates == 10
        return {"n_cells": 1, "n_paths_per_cell": n_paths, "within_cap": True}

    def tiny_seed_for_cell(engine_index: int, rep: int, start_index: int, dt_index: int):
        return np.random.SeedSequence([UNIT_ROOT, 99], spawn_key=(0,)), [UNIT_ROOT, 99], [0]

    def tiny_simulate_first_hit(
        start, *, n_paths, seed, engine, dt, horizon, engine_index, rep,
        start_index, dt_index, seed_tuple, seed_spawn_key,
        return_path_rows, return_audit_traces, allow_primary,
    ):
        assert n_paths == 2 and return_path_rows and return_audit_traces and allow_primary
        rows = []
        traces = []
        for local_index in range(n_paths):
            path_id = f"tiny-path-{local_index}"
            rows.append({
                "stage": tiny.STAGE, "role": tiny.ROLE, "engine": engine,
                "engine_index": engine_index, "rep": rep, "start_index": start_index,
                "dt_index": dt_index, "dt": dt, "horizon": horizon,
                "n_steps": 1, "path_id": path_id, "local_path_index": local_index,
                "seed_tuple": seed_tuple, "seed_spawn_key": seed_spawn_key,
                "initial_state": [0.0, 0.0], "first_label": "unresolved",
                "first_time": None, "first_hit_state": None,
                "terminal_label": "U", "terminal_state": [0.0, 0.0],
                "continuation_state_checksum": "tiny", "terminal_state_checksum": "tiny",
            })
            traces.append({
                "local_path_index": local_index, "path_id": path_id,
                "states": [[0.0, 0.0], [0.0, 0.0]], "trace_checksum": "tiny",
                "trace_source": "unabsorbed continuation state at t=0..T",
            })
        return {
            "stage": tiny.STAGE, "role": tiny.ROLE, "engine": engine,
            "engine_index": engine_index, "rep": rep, "start_index": start_index,
            "dt_index": dt_index, "dt": dt, "horizon": horizon, "n_steps": 1,
            "n_total": n_paths,
            "first_hit_counts": {"A": 0, "B": 0, "unresolved": n_paths},
            "terminal_counts": {"A": 0, "B": 0, "U": n_paths},
            "joint_counts": {
                "first_hit_rows": ["A", "B", "unresolved"],
                "terminal_columns": ["A", "B", "U"],
                "values": [[0, 0, 0], [0, 0, 0], [0, 0, n_paths]],
            },
            "unresolved_fraction": 1.0, "terminal_p_B": 0.0,
            "censor_bracket_p_B": [0.0, 1.0],
            "continuation_state_checksum": "tiny", "first_hit_state_checksum": "tiny",
            "terminal_state_checksum": "tiny", "path_rows_checksum": "tiny",
            "terminal_source": "continuation_state at horizon; never first-hit state",
            "seed": {"entropy": [UNIT_ROOT, 99], "spawn_key": [0]},
            "seed_tuple": seed_tuple, "seed_spawn_key": seed_spawn_key,
            "rng_contract": "tiny", "path_rows": rows, "audit_traces": traces,
        }

    tiny.build_spec = tiny_build_spec
    tiny.runtime_metadata = tiny_runtime_metadata
    tiny.validate_primary_budget = tiny_validate_primary_budget
    tiny.expected_primary_cells = lambda: 1
    tiny.seed_for_cell = tiny_seed_for_cell
    tiny.simulate_first_hit = tiny_simulate_first_hit
    monkeypatch.setattr(runner, "SOURCE", source_path)
    monkeypatch.setattr(runner, "load_module", lambda: tiny)

    manifest_paths = (source_path, spec_path, protocol_path, test_path, verifier_path, runner_path)
    manifest = {
        "status": "FROZEN",
        "runtime": tiny_runtime_metadata(),
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
    assert len(path_rows) == 2
    assert len(trace_rows) == 2
    assert counts["status"] == "COMPLETE"
    assert counts["completed_cells"] == 1
    assert counts["n_path_rows"] == 2
    assert counts["n_audit_traces"] == 2
    with pytest.raises(FileExistsError):
        runner.execute_primary(
            spec_path=spec_path, protocol_path=protocol_path,
            freeze_manifest_path=manifest_path, test_path=test_path,
            verifier_path=verifier_path, primary_root=primary_root,
        )
