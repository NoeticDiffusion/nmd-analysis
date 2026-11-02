"""Nonprimary tests for the bounded TRANS-0B1 terminal-occupancy gate."""

from __future__ import annotations

import copy

import numpy as np
import pytest

from nmd_analysis.dynamical_families import trans_0b1 as b


def test_spec_and_local_stability_are_frozen():
    spec = b.build_spec()
    assert spec["semantics"]["object"] == "finite_horizon_terminal_occupancy"
    assert spec["semantics"]["eventual_committor"] is False
    local = b.local_stability()
    assert local["spectral_abscissa_alpha"] == pytest.approx(-1.0)
    assert local["numerical_abscissa_omega"] > 0
    assert np.linalg.norm(b.STARTS[0]) == pytest.approx(np.linalg.norm(b.STARTS[1]))
    np.testing.assert_allclose(b.STARTS @ b.TARGET_DIRECTION, np.full(2, .6 / np.sqrt(2)))


def test_exact_truth_has_same_local_operator_but_different_directional_probabilities():
    first = b.ou_truth(b.STARTS[0])
    second = b.ou_truth(b.STARTS[1])
    assert first["p_B"] != pytest.approx(second["p_B"], abs=1e-3)
    assert first["p_A"] + first["p_B"] + first["p_U"] == pytest.approx(1.0)
    assert second["p_A"] + second["p_B"] + second["p_U"] == pytest.approx(1.0)
    np.testing.assert_allclose(first["covariance"], second["covariance"], rtol=0, atol=1e-12)


def test_covariance_independent_check_matches_van_loan():
    exact = b._covariance_van_loan()
    independent = b._covariance_independent(n_steps=4000)
    np.testing.assert_allclose(exact, independent, rtol=0, atol=2e-7)


def test_paired_simulator_has_shared_fine_coarse_paths_and_partition():
    paired = b.simulate_paired_terminal_events(
        b.STARTS[0], n_paths=128, seed=991, horizon=16 * b.FINE_DT
    )
    assert paired["shared_noise_stream"] is True
    assert paired["coarse_from_fine_stride"] == 4
    for key in ("fine", "coarse"):
        row = paired[key]
        assert row["n_A"] + row["n_B"] + row["n_U"] == 128
        assert row["terminal_mean"].shape == (2,)
        assert row["terminal_covariance"].shape == (2, 2)
    assert paired["fine"]["n_steps"] == 16
    assert paired["coarse"]["n_steps"] == 4


def test_score_events_uses_all_three_categories_and_cp_distance():
    truth = np.asarray([.1, .2, .7])
    result = b.score_events({"n_A": 10, "n_B": 20, "n_U": 70, "n_total": 100}, truth)
    assert result["intervals"].shape == (3, 2)
    assert result["max_endpoint_distance"] >= 0
    with pytest.raises(ValueError):
        b.score_events({"n_A": 10, "n_B": 20, "n_U": 70, "n_total": 99}, truth)


def _summary_rows():
    truth = [{"start_index": i, "truth": b.ou_truth(start)["category_probabilities"]} for i, start in enumerate(b.STARTS)]
    rows = []
    for rep in range(b.N_REPS):
        for start_index in range(len(b.STARTS)):
            truth_vector = truth[start_index]["truth"]
            counts = np.rint(truth_vector * 200000).astype(int)
            counts[2] += 200000 - int(np.sum(counts))
            rows.append({"rep": rep, "start_index": start_index, "dt": b.FINE_DT, **{key: int(value) for key, value in zip(("n_A", "n_B", "n_U"), counts)}, "n_total": 200000})
    return rows, truth


def test_summary_pass_and_fail_precedence():
    rows, truths = _summary_rows()
    passed = b.summarize_0b1(rows, truths)
    assert passed["primary_decision"] == "PASS"
    failed = copy.deepcopy(rows)
    failed[0]["n_A"], failed[0]["n_B"], failed[0]["n_U"] = 200000, 0, 0
    assert b.summarize_0b1(failed, truths)["primary_decision"] == "FAIL"
    assert b.summarize_0b1(rows[:-1], truths)["primary_decision"] == "INCONCLUSIVE"


def test_terminal_event_input_validation():
    with pytest.raises(ValueError):
        b.simulate_terminal_events([0.0, 0.0], n_paths=4, seed=1, dt=.01, horizon=.005)
    with pytest.raises(ValueError):
        b.ou_truth([0.0, np.nan])
    with pytest.raises(ValueError):
        b.local_stability(np.zeros((3, 3)))
