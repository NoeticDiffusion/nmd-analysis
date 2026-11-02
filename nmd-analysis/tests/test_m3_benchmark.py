import numpy as np
from types import SimpleNamespace
import pytest

import nmd_analysis.dynamical_families.m3_benchmark as m3_benchmark
from nmd_analysis.dynamical_families.m3_benchmark import (
    DEFAULT_A_B_D_EPSILON,
    _a_b_d,
    _local_increment_covariance,
    _metrics,
    _nearest_predict,
    run_m3_benchmark,
)


def _small_m3_result():
    return run_m3_benchmark(
        seeds=[17],
        dt_values=[0.1],
        embargo_multiples=[0.0, 1.0],
        n_samples=120,
        burn_in=20,
        train_fraction=0.45,
        n_neighbors=12,
        min_train_support=8,
        time_shift_steps=3,
    )


def test_primary_m3_spec_is_stable_linear_gaussian_and_serializable():
    result = _small_m3_result()
    spec = result["spec"]

    assert result["benchmark_schema_version"] == "nmd_analysis.m3_benchmark.v1"
    assert result["spec_status"] == "custom_test_spec"
    assert spec["state_dimension"] == 3
    base_a = np.asarray(spec["base_A"])
    base_q = np.asarray(spec["base_Q"])
    assert base_a.shape == (3, 3)
    assert base_q.shape == (3, 3)
    assert np.max(np.abs(np.linalg.eigvals(base_a))) < 1.0
    assert np.linalg.eigvalsh(base_q).min() > 0.0
    assert result["truth_semantics"] == "discrete_chart_conditional_velocity"
    assert result["truth_formula"] == "b_dt(x)=(A-I)x/dt"
    assert result["not_an_ito_drift"] is True


def test_m3_effective_k_step_truth_has_analytic_A_and_Q_recursion():
    result = _small_m3_result()
    spec = result["spec"]
    base_a = np.asarray(spec["base_A"], dtype=float)
    base_q = np.asarray(spec["base_Q"], dtype=float)
    for transition in spec["effective_transitions"]:
        stride = transition["stride"]
        expected_a = np.linalg.matrix_power(base_a, stride)
        expected_q = np.zeros_like(base_q)
        power = np.eye(3)
        for _ in range(stride):
            expected_q += power @ base_q @ power.T
            power = power @ base_a
        observed_a = np.asarray(transition["A_k"], dtype=float)
        observed_q = np.asarray(transition["Q_k"], dtype=float)
        assert np.allclose(observed_a, expected_a, rtol=0.0, atol=1e-12)
        assert np.allclose(observed_q, expected_q, rtol=0.0, atol=1e-12)
        assert np.linalg.eigvalsh(observed_q).min() > 0.0
        if stride == 2:
            assert np.allclose(observed_a, base_a @ base_a, rtol=0.0, atol=1e-12)
            assert np.allclose(
                observed_q,
                base_q + base_a @ base_q @ base_a.T,
                rtol=0.0,
                atol=1e-12,
            )


def test_m3_local_covariance_mean_b_and_a_b_d_match_hand_calculation():
    increments = np.asarray(
        [[1.0, 2.0, 0.0], [3.0, 4.0, 0.0], [5.0, 6.0, 0.0]],
    )
    evaluation = np.asarray([0, 1], dtype=np.int64)
    neighborhoods = [np.asarray([0, 1]), np.asarray([0, 1])]
    covariance = _local_increment_covariance(increments, evaluation, neighborhoods, dt=2.0)
    expected_covariance = np.asarray(
        [[[1.0, 1.0, 0.0], [1.0, 1.0, 0.0], [0.0, 0.0, 0.0]]] * 2
    )
    assert np.allclose(covariance, expected_covariance, rtol=0.0, atol=0.0)

    train_states = np.asarray([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    train_velocities = np.asarray([[1.0, 2.0, 0.0], [3.0, 4.0, 0.0]])
    query = np.asarray([[0.5, 0.0, 0.0], [0.5, 0.0, 0.0]])
    mean_b = _nearest_predict(
        train_states,
        train_velocities,
        query,
        estimator="local_mean",
        n_neighbors=2,
        min_train_support=2,
    )
    expected_b = np.asarray([[2.0, 3.0, 0.0], [2.0, 3.0, 0.0]])
    assert np.allclose(mean_b, expected_b, rtol=0.0, atol=0.0)

    expected_a_b_d = (5.0**2) / (13.0 * 2.0 + DEFAULT_A_B_D_EPSILON)
    assert np.allclose(
        _a_b_d(expected_b, covariance, DEFAULT_A_B_D_EPSILON),
        [expected_a_b_d, expected_a_b_d],
        rtol=0.0,
        atol=1e-12,
    )
    metrics = _metrics(mean_b, np.asarray([[1.0, 2.0, 0.0]] * 2), covariance, neighborhoods)
    expected_truth_a_b_d = 3.0**2 / (5.0 * 2.0 + DEFAULT_A_B_D_EPSILON)
    assert np.isclose(metrics["a_b_d_mean"], expected_a_b_d, rtol=0.0, atol=1e-12)
    assert np.isclose(
        metrics["a_b_d_bias"],
        expected_a_b_d - expected_truth_a_b_d,
        rtol=0.0,
        atol=1e-12,
    )


def test_evaluation_target_perturbation_is_not_used_by_either_candidate():
    result = _small_m3_result()
    assert result["split_contract"]["evaluation_targets_used_by_crossfit"] is False


def test_m3_uses_one_observed_evaluation_covariance_for_every_comparator_and_keeps_a_b_d_pairing():
    result = _small_m3_result()
    rows = result["rows"]
    assert result["evaluation_covariance_audit"]["one_fixed_local_tensor_per_eval_centre_and_scenario"] is True
    assert result["evaluation_covariance_audit"]["all_comparators_share_scenario_tensors"] is True
    by_scenario = {}
    for row in rows:
        key = (row["seed"], row["dt_sec"], row["embargo_multiple_of_dt"])
        by_scenario.setdefault(key, set()).add(row["eval_increment_covariance_sha256"])
        assert row["oracle_conditional_covariance_semantics"] == "Q_divided_by_dt"
    assert all(len(hashes) == 1 for hashes in by_scenario.values())
    oracle_rows = [row for row in rows if row["comparator"] == "oracle_truth_known"]
    assert oracle_rows
    assert all(row["metrics"]["rmse"] == 0.0 for row in oracle_rows)
    assert all(row["metrics"]["a_b_d_bias"] == 0.0 for row in oracle_rows)


def test_m3_comparator_inventory_and_split_safety_are_explicit():
    result = _small_m3_result()
    comparators = {row["comparator"] for row in result["rows"]}
    expected = {
        "oracle_truth_known",
        "contaminated_same_sample_local_mean",
        "crossfit_local_mean",
        "crossfit_local_linear",
        "negative_shuffled_train_velocity_local_mean",
        "negative_shuffled_train_velocity_local_linear",
        "negative_time_displaced_local_mean",
        "negative_time_displaced_local_linear",
    }
    assert comparators == expected
    production = [row for row in result["rows"] if row["production_crossfit_api"]]
    assert production
    assert all(row["train_evaluation_overlap_count"] == 0 for row in production)
    assert all(row["embargo_violations"] == 0 for row in production)
    assert all(row["claim_status"] == "no_biological_claim" for row in result["rows"])


def test_time_displaced_control_keeps_shifted_source_order_and_unshifted_truth(monkeypatch):
    """The negative control must score shifted sources against original truth.

    A state dependent fake cross-fit makes the source order observable.  The
    old implementation rolled the returned values back to the original order,
    making this regression fail while the corrected control leaves the shifted
    source values in the order returned by the API.
    """

    calls = []
    displaced_rows = []

    def fake_crossfit(trajectory, time, train, evaluation, **kwargs):
        evaluation = np.asarray(evaluation, dtype=np.int64)
        calls.append(evaluation.copy())
        # Deliberately state-dependent: the value identifies the requested
        # evaluation source, so a hidden reorder cannot pass unnoticed.
        b_hat = np.repeat(evaluation.astype(float)[:, None], 3, axis=1)
        return SimpleNamespace(
            b_hat=b_hat,
            provenance={"candidate_status": "candidate_not_qualified"},
        )

    real_result_row = m3_benchmark._result_row

    def spy_result_row(**kwargs):
        if kwargs["comparator"] == "negative_time_displaced_local_mean":
            displaced_rows.append(
                {
                    "evaluation": np.asarray(kwargs["evaluation"], dtype=np.int64).copy(),
                    "predicted": np.asarray(kwargs["predicted"], dtype=float).copy(),
                    "truth": np.asarray(kwargs["truth"], dtype=float).copy(),
                }
            )
        return real_result_row(**kwargs)

    def deterministic_base_path(*, seed, A, Q, n_base_steps):
        del seed, A, Q
        indices = np.arange(int(n_base_steps), dtype=float)
        return np.column_stack((indices, 2.0 * indices, 3.0 * indices))

    monkeypatch.setattr(m3_benchmark, "crossfit_local_chart_b", fake_crossfit)
    monkeypatch.setattr(m3_benchmark, "_result_row", spy_result_row)
    monkeypatch.setattr(m3_benchmark, "_simulate_base_path", deterministic_base_path)

    zero_a = np.zeros((3, 3), dtype=float)
    identity_q = np.eye(3, dtype=float)
    m3_benchmark.run_m3_benchmark(
        seeds=[1],
        dt_values=[0.1],
        embargo_multiples=[0.0],
        base_dt=0.05,
        n_samples=40,
        burn_in=2,
        train_fraction=0.45,
        n_neighbors=4,
        min_train_support=2,
        time_shift_steps=3,
        A=zero_a,
        Q=identity_q,
    )

    assert len(displaced_rows) == 1
    assert len(calls) >= 2
    original_evaluation = calls[0]
    shifted_candidates = [call for call in calls if not np.array_equal(call, original_evaluation)]
    assert shifted_candidates
    shifted_evaluation = shifted_candidates[0]
    row = displaced_rows[0]
    np.testing.assert_array_equal(row["evaluation"], original_evaluation)
    np.testing.assert_array_equal(
        row["predicted"],
        np.repeat(shifted_evaluation.astype(float)[:, None], 3, axis=1),
    )

    # With A=0, b_dt(x)=-x/dt.  The truth passed to the control is therefore
    # the original evaluation states, while the prediction identifies the
    # shifted source states above.
    trajectory = np.column_stack(
        (
            2.0 + 2.0 * np.arange(40, dtype=float),
            4.0 + 4.0 * np.arange(40, dtype=float),
            6.0 + 6.0 * np.arange(40, dtype=float),
        )
    )
    expected_truth = -trajectory[original_evaluation] / 0.1
    np.testing.assert_array_equal(row["truth"], expected_truth)
    assert not np.array_equal(row["predicted"], row["truth"])


def test_time_displaced_shift_must_be_an_integer():
    with pytest.raises(ValueError, match="positive integer"):
        m3_benchmark.run_m3_benchmark(
            seeds=[1],
            dt_values=[0.1],
            embargo_multiples=[0.0],
            n_samples=40,
            burn_in=2,
            time_shift_steps=1.5,
        )


def test_time_displaced_shift_must_fit_evaluation_support():
    with pytest.raises(ValueError, match="strictly smaller"):
        m3_benchmark.run_m3_benchmark(
            seeds=[1],
            dt_values=[0.1],
            embargo_multiples=[0.0],
            n_samples=40,
            burn_in=2,
            time_shift_steps=21,
        )
