import hashlib
import inspect
import json
from pathlib import Path

import numpy as np
import pytest

import nmd_analysis.dynamical_families.m3_extension as extension


TEST_TRAIN_SEEDS = (201, 202, 203)
TEST_QUERY_SEEDS = (9901, 9902, 9903)
TEST_TRAIN_STATES = 180
TEST_BURN_IN = 30
TEST_QUERY_STATES = 17
TEST_N_NEIGHBORS = 24
TEST_MIN_TRAIN_SUPPORT = 12
TEST_EMBARGO_MULTIPLE = 2.0
TEST_TIME_SHIFT_STEPS = 7
TEST_QUERY_SOURCES_PER_SEGMENT = TEST_QUERY_STATES - 1
TEST_QUERY_SOURCES = len(TEST_QUERY_SEEDS) * TEST_QUERY_SOURCES_PER_SEGMENT


@pytest.fixture(scope="module")
def reduced_extension_result():
    """Run a reduced, non-primary seed grid across all declared systems."""
    return extension.run_m3_extension(
        systems=extension.SYSTEM_NAMES,
        train_seeds=TEST_TRAIN_SEEDS,
        query_seeds=TEST_QUERY_SEEDS,
        train_states=TEST_TRAIN_STATES,
        burn_in=TEST_BURN_IN,
        query_states=TEST_QUERY_STATES,
        n_neighbors=TEST_N_NEIGHBORS,
        min_train_support=TEST_MIN_TRAIN_SUPPORT,
        embargo_multiple=TEST_EMBARGO_MULTIPLE,
        time_shift_steps=TEST_TIME_SHIFT_STEPS,
    )


def _independent_stationary_covariance(a, q):
    """Independent Lyapunov check using a finite covariance series, not kron solve."""
    covariance = np.zeros_like(q, dtype=float)
    power = np.eye(a.shape[0], dtype=float)
    for _ in range(150):
        covariance += power @ q @ power.T
        power = power @ a
    return 0.5 * (covariance + covariance.T)


def _a_b_d(values, covariance):
    values = np.asarray(values, dtype=float)
    covariance = np.asarray(covariance, dtype=float)
    numerator = np.einsum("ni,nij,nj->n", values, covariance, values)
    denominator = (
        np.einsum("ni,ni->n", values, values)
        * np.trace(covariance, axis1=1, axis2=2)
        + extension.EPSILON
    )
    result = np.full(values.shape[0], np.nan)
    valid = np.isfinite(values).all(axis=1) & np.isfinite(denominator) & (denominator > 0)
    result[valid] = numerator[valid] / denominator[valid]
    return result


def test_frozen_spec_lists_all_six_systems_and_exposes_hidden_9d_shape():
    result = extension.spec_only()
    spec = result["spec"]
    assert tuple(system["name"] for system in spec["systems"]) == extension.SYSTEM_NAMES
    assert spec["dt_sec"] == extension.DT
    assert spec["n_query_sources"] == 144
    assert spec["n_neighbors"] == 64
    assert spec["min_train_support"] == 16
    assert spec["target_contract"]["not_ito_drift"] is True
    assert "continuous" not in json.dumps(spec, sort_keys=True).lower()

    for system in spec["systems"]:
        latent = int(system["dimension_latent"])
        observed = int(system["dimension_observed"])
        assert np.asarray(system["A"]).shape == (latent, latent)
        assert np.asarray(system["Q"]).shape == (latent, latent)
        assert np.asarray(system["H"]).shape == (observed, latent)
        assert np.asarray(system["R"]).shape == (observed, observed)

    hidden = next(item for item in spec["systems"] if item["name"] == "linear_hidden9_observed3")
    assert hidden["dimension_latent"] == 9
    assert hidden["dimension_observed"] == 3
    assert np.asarray(hidden["A"]).shape == (9, 9)
    assert np.asarray(hidden["H"]).shape == (3, 9)


def test_default_run_serializes_the_same_frozen_spec_without_running_primary_simulation(monkeypatch):
    calls = []

    def stub_run_system(system, drift_hash, **kwargs):
        calls.append((system, kwargs))
        return {"stub": True, "system": system}

    monkeypatch.setattr(extension, "_run_system", stub_run_system)
    result = extension.run_m3_extension()
    spec_only = extension.spec_only()
    assert result["spec_status"] == "frozen_primary_spec"
    assert result["spec"] == spec_only["spec"]
    assert result["spec_sha256"] == spec_only["spec_sha256"] == extension.DEFAULT_SPEC_SHA256
    assert [system for system, _ in calls] == list(extension.SYSTEM_NAMES)


def test_reduced_extension_is_strict_json_and_has_source_runtime_provenance(
    reduced_extension_result,
):
    result = reduced_extension_result
    json.loads(json.dumps(result, allow_nan=False))
    assert result["spec_status"] != "frozen_primary_spec"
    assert result["spec_sha256"] != extension.DEFAULT_SPEC_SHA256
    assert result["candidate_status"] == "candidate_not_qualified"
    assert result["claim_status"] == "no_biological_claim"
    assert result["scientific_gate"] == "no_automatic_pass"
    provenance = result["provenance"]
    assert provenance["code_hash"]
    assert provenance["drift_code_hash"]
    assert provenance["runtime"]["python"]
    assert provenance["runtime"]["numpy"]
    module_hash = hashlib.sha256(Path(extension.__file__).resolve().read_bytes()).hexdigest()
    drift_path = Path(inspect.getsourcefile(extension.crossfit_local_chart_b)).resolve()
    drift_hash = hashlib.sha256(drift_path.read_bytes()).hexdigest()
    assert provenance["code_hash"] == module_hash
    assert provenance["drift_code_hash"] == drift_hash


def test_each_system_has_fixed_queries_and_seam_safe_support(reduced_extension_result):
    for name in extension.SYSTEM_NAMES:
        system = reduced_extension_result["systems"][name]
        spec = system["system_spec"]
        observed = int(spec["dimension_observed"])
        truth = np.asarray(system["query_truth"], dtype=float)
        observed_states = np.asarray(system["query_observed"], dtype=float)
        covariance = np.asarray(system["query_covariance"], dtype=float)
        assert truth.shape == (TEST_QUERY_SOURCES, observed)
        assert observed_states.shape == (TEST_QUERY_SOURCES, observed)
        assert covariance.shape == (TEST_QUERY_SOURCES, observed, observed)
        assert np.isfinite(truth).all()
        assert np.isfinite(observed_states).all()
        assert np.isfinite(covariance).all()
        assert len(system["query_index_records"]) == TEST_QUERY_SOURCES
        neighborhood_lists = [
            record["neighbour_indices_in_query_order"]
            for record in system["query_index_records"]
        ]
        assert len(neighborhood_lists) == TEST_QUERY_SOURCES
        assert all(len(indices) == TEST_N_NEIGHBORS for indices in neighborhood_lists)

        metadata = system["segment_metadata"]
        assert metadata["all_seam_and_padding_increments_excluded"] is True
        segments = metadata["heldout_segments"]
        assert len(segments) == 3
        assert sum(int(segment["n_genuine_sources"]) for segment in segments) == TEST_QUERY_SOURCES
        assert all(int(segment["n_states"]) == TEST_QUERY_STATES for segment in segments)
        assert all(int(segment["n_genuine_sources"]) == TEST_QUERY_SOURCES_PER_SEGMENT for segment in segments)
        excluded = set(metadata["excluded_carrier_indices"])
        assert set(range(TEST_TRAIN_STATES - 1, TEST_TRAIN_STATES + 3)).issubset(excluded)
        assert all(
            int(source) not in excluded
            for segment in segments
            for source in segment["source_indices"]
        )
        assert all(len(seed_run["comparators"]) == 4 for seed_run in system["training_replicates"])
        assert len(system["training_replicates"]) == len(TEST_TRAIN_SEEDS)


@pytest.mark.parametrize("system_name", ["full_linear3d", "linear_hidden9_observed3", "linear_noisy3_observed3"])
def test_observed_linear_truth_matches_independent_gaussian_conditioning(
    reduced_extension_result, system_name
):
    system = reduced_extension_result["systems"][system_name]
    settings = system["system_spec"]
    a = np.asarray(settings["A"], dtype=float)
    q = np.asarray(settings["Q"], dtype=float)
    h = np.asarray(settings["H"], dtype=float)
    r = np.asarray(settings["R"], dtype=float)
    p = _independent_stationary_covariance(a, q)
    np.testing.assert_allclose(system["stationary_covariance_P"], p, rtol=0.0, atol=1e-10)

    y = np.asarray(system["query_observed"], dtype=float)
    v = h @ p @ h.T + r
    c = h @ a @ p @ h.T
    gain = c @ np.linalg.inv(v)
    expected_truth = (y @ gain.T - y) / extension.DT
    np.testing.assert_allclose(system["query_truth"], expected_truth, rtol=0.0, atol=1e-10)

    expected_variance = v - c @ np.linalg.inv(v) @ c.T
    expected_variance = 0.5 * (expected_variance + expected_variance.T)
    np.testing.assert_allclose(
        system["analytic_observed_conditional_variance"],
        expected_variance,
        rtol=0.0,
        atol=1e-10,
    )


def test_observation_noise_changes_conditional_truth_from_latent_noiseless_formula(
    reduced_extension_result,
):
    system = reduced_extension_result["systems"]["linear_noisy3_observed3"]
    settings = system["system_spec"]
    assert np.linalg.norm(np.asarray(settings["R"], dtype=float)) > 0.0
    y = np.asarray(system["query_observed"], dtype=float)
    a = np.asarray(settings["A"], dtype=float)
    noiseless = (y @ a.T - y) / extension.DT
    observed_truth = np.asarray(system["query_truth"], dtype=float)
    assert np.max(np.abs(observed_truth - noiseless)) > 1e-8


@pytest.mark.parametrize(
    "label",
    [
        "crossfit_mean",
        "crossfit_linear",
        "cross_segment_order_corruption_mean",
        "cross_segment_order_corruption_linear",
    ],
)
def test_pointwise_bias_variance_and_mse_identity_are_recomputed_at_common_queries(
    reduced_extension_result, label
):
    system = reduced_extension_result["systems"]["full_linear3d"]
    pointwise = system["pointwise"][label]
    predictions = np.asarray(pointwise["predictions"], dtype=float)
    truth = np.asarray(system["query_truth"], dtype=float)
    finite = np.isfinite(predictions).all(axis=2)
    errors = np.where(finite[:, :, None], predictions - truth[None, :, :], np.nan)
    bias = np.nanmean(errors, axis=0)
    variance = np.nanvar(np.where(finite[:, :, None], predictions, np.nan), axis=0, ddof=0)
    mse = np.nanmean(errors**2, axis=0)
    np.testing.assert_allclose(pointwise["metrics"]["component_bias"], bias, rtol=0.0, atol=1e-12)
    np.testing.assert_allclose(
        pointwise["metrics"]["component_variance_population"], variance, rtol=0.0, atol=1e-12
    )
    np.testing.assert_allclose(pointwise["metrics"]["component_mse"], mse, rtol=0.0, atol=1e-12)
    np.testing.assert_allclose(
        pointwise["metrics"]["component_mse_identity_residual"],
        mse - (bias**2 + variance),
        rtol=0.0,
        atol=1e-12,
    )
    assert np.all(np.asarray(pointwise["metrics"]["n_replicates_by_query"]) == len(TEST_TRAIN_SEEDS))
    sample_variance = np.asarray(pointwise["metrics"]["component_variance_sample_ddof1"], dtype=float)
    counts = np.asarray(pointwise["metrics"]["n_replicates_by_query"], dtype=float)
    expected_mcse = np.sqrt(sample_variance / counts[:, None])
    np.testing.assert_allclose(pointwise["metrics"]["component_mcse"], expected_mcse, rtol=0.0, atol=1e-12)


def test_pointwise_a_b_d_uses_the_reported_fixed_neighborhoods_and_covariance(
    reduced_extension_result,
):
    system = reduced_extension_result["systems"]["full_linear3d"]
    pointwise = system["pointwise"]["crossfit_linear"]
    predictions = np.asarray(pointwise["predictions"], dtype=float)
    truth = np.asarray(system["query_truth"], dtype=float)
    covariance = np.asarray(system["query_covariance"], dtype=float)
    neighborhoods = [
        np.asarray(record["neighbour_indices_in_query_order"], dtype=int)
        for record in system["query_index_records"]
    ]
    aligned_predictions = np.asarray(
        [[np.mean(predictions[row, indices], axis=0) for indices in neighborhoods]
         for row in range(predictions.shape[0])],
        dtype=float,
    )
    aligned_truth = np.asarray(
        [np.mean(truth[indices], axis=0) for indices in neighborhoods], dtype=float
    )
    expected_values = np.asarray(
        [_a_b_d(aligned_predictions[row], covariance) for row in range(predictions.shape[0])]
    )
    expected_truth = _a_b_d(aligned_truth, covariance)
    metrics = pointwise["metrics"]
    np.testing.assert_allclose(metrics["a_b_d_values"], expected_values, rtol=0.0, atol=1e-12)
    np.testing.assert_allclose(metrics["a_b_d_truth"], expected_truth, rtol=0.0, atol=1e-12)
    finite = np.isfinite(expected_values)
    counts = np.sum(finite, axis=0)
    errors = expected_values - expected_truth[None, :]
    bias = np.full(expected_truth.shape, np.nan)
    population = np.full(expected_truth.shape, np.nan)
    valid = counts > 0
    bias[valid] = np.sum(np.where(finite[:, valid], errors[:, valid], 0.0), axis=0) / counts[valid]
    means = np.sum(np.where(finite[:, valid], expected_values[:, valid], 0.0), axis=0) / counts[valid]
    centered = np.where(finite[:, valid], expected_values[:, valid] - means[None, :], 0.0)
    population[valid] = np.sum(centered**2, axis=0) / counts[valid]
    np.testing.assert_array_equal(metrics["a_b_d_n_replicates_by_query"], counts)
    np.testing.assert_allclose(metrics["a_b_d_bias"], bias, rtol=0.0, atol=1e-12)
    np.testing.assert_allclose(metrics["a_b_d_variance_population"], population, rtol=0.0, atol=1e-12)


def test_shifted_controls_are_ordered_distinct_and_future_labels_are_excluded(
    reduced_extension_result,
):
    system = reduced_extension_result["systems"]["full_linear3d"]
    original = np.asarray(
        [record["carrier_source_index"] for record in system["query_index_records"]], dtype=np.int64
    )
    expected_shifted = np.roll(original, TEST_TIME_SHIFT_STEPS)
    assert not np.array_equal(original, expected_shifted)
    for seed_run in system["training_replicates"]:
        comparators = seed_run["comparators"]
        for label in (
            "cross_segment_order_corruption_mean",
            "cross_segment_order_corruption_linear",
        ):
            entry = comparators[label]
            source = np.asarray(
                entry["order_corruption_source_indices_by_scoring_index"], dtype=np.int64
            )
            np.testing.assert_array_equal(source, expected_shifted)
            assert entry["order_corruption_steps"] == TEST_TIME_SHIFT_STEPS
            assert entry["order_corruption_boundary"] == "circular_wrap_across_heldout_segments"

    predictions = system["pointwise"]
    for base, shifted in (
        ("crossfit_mean", "cross_segment_order_corruption_mean"),
        ("crossfit_linear", "cross_segment_order_corruption_linear"),
    ):
        assert not np.array_equal(
            np.asarray(predictions[base]["predictions"]),
            np.asarray(predictions[shifted]["predictions"]),
        )
        np.testing.assert_array_equal(
            np.asarray(predictions[shifted]["predictions"]),
            np.roll(np.asarray(predictions[base]["predictions"]), TEST_TIME_SHIFT_STEPS, axis=1),
        )


@pytest.mark.parametrize("estimator", ["local_mean", "local_linear"])
def test_m3_fit_is_independent_of_heldout_target_states_and_excludes_seams(estimator):
    index = np.arange(120, dtype=float)
    base = np.column_stack(
        (
            np.sin(0.17 * index) + 0.01 * index,
            np.cos(0.11 * index) + 0.02 * np.sin(0.07 * index),
            0.3 * np.sin(0.13 * index + 0.4) + 0.012 * index,
        )
    )
    train = base[:80]
    heldout = [base[80:89].copy(), base[89:98].copy()]
    combined, time, train_indices, evaluation, metadata = extension._concat_segments(train, heldout)
    assert set(evaluation).isdisjoint(metadata["excluded_carrier_indices"])
    assert all(
        int(source) not in set(metadata["excluded_carrier_indices"])
        for segment in metadata["heldout_segments"]
        for source in segment["source_indices"]
    )
    train_support = np.column_stack((time[train_indices], time[train_indices + 1]))
    eval_support = np.column_stack((time[evaluation], time[evaluation + 1]))
    kwargs = dict(
        estimator=estimator,
        n_neighbors=8,
        min_train_support=4,
        embargo=0.0,
        train_window_support=train_support,
        evaluation_window_support=eval_support,
        source_artifact_hash="synthetic-m3-extension",
        source_nmd_schema="synthetic.m3_extension.v1",
        nmd_code_revision=None,
    )
    first = extension.crossfit_local_chart_b(
        combined, time, train_indices, evaluation, **kwargs
    )
    changed = combined.copy()
    for segment in metadata["heldout_segments"]:
        changed[int(segment["carrier_state_stop"])] += np.asarray([1000.0, -700.0, 500.0])
    second = extension.crossfit_local_chart_b(
        changed, time, train_indices, evaluation, **kwargs
    )
    assert np.isfinite(first.b_hat).all()
    np.testing.assert_array_equal(first.b_hat, second.b_hat)


def test_missing_replicates_use_valid_count_for_mcse_and_report_null_support():
    truth = np.zeros((3, 2), dtype=float)
    covariance = np.tile(np.eye(2, dtype=float), (3, 1, 1))
    neighborhoods = (np.asarray([0, 1]), np.asarray([1, 2]), np.asarray([0, 2]))
    predictions = np.asarray(
        [
            [[1.0, 1.0], [2.0, 2.0], [np.nan, np.nan]],
            [[3.0, 3.0], [4.0, 4.0], [np.nan, np.nan]],
            [[5.0, 5.0], [np.nan, np.nan], [np.nan, np.nan]],
        ]
    )
    metrics = extension._pointwise_replicate_metrics(predictions, truth, covariance, neighborhoods)
    np.testing.assert_array_equal(metrics["n_replicates_by_query"], [3, 2, 0])
    np.testing.assert_allclose(metrics["component_variance_sample_ddof1"][1], [2.0, 2.0])
    np.testing.assert_allclose(metrics["component_mcse"][1], [1.0, 1.0])
    assert metrics["pointwise_validity_reason"][2] == "no_finite_replicate"
    assert np.isnan(np.asarray(metrics["component_mcse"], dtype=float)[2]).all()


def test_invalid_extension_configurations_refuse_without_partial_results():
    with pytest.raises(ValueError, match="unknown systems"):
        extension.run_m3_extension(systems=("not_a_declared_system",))
    with pytest.raises(ValueError, match="nonempty|non-empty|at least one"):
        extension.run_m3_extension(systems=())
    reduced = dict(
        systems=("full_linear3d",),
        train_states=TEST_TRAIN_STATES,
        burn_in=TEST_BURN_IN,
        query_states=TEST_QUERY_STATES,
        n_neighbors=TEST_N_NEIGHBORS,
        min_train_support=TEST_MIN_TRAIN_SUPPORT,
        embargo_multiple=TEST_EMBARGO_MULTIPLE,
        time_shift_steps=TEST_TIME_SHIFT_STEPS,
    )
    with pytest.raises(ValueError, match="disjoint|overlap"):
        extension.run_m3_extension(
            **reduced, train_seeds=(201, 202), query_seeds=(202, 9902, 9903)
        )
    with pytest.raises(ValueError, match="integer seeds"):
        extension.run_m3_extension(
            **reduced, train_seeds=(201.5, 202, 203), query_seeds=TEST_QUERY_SEEDS
        )
    with pytest.raises(ValueError, match="integer seeds"):
        extension.run_m3_extension(
            **reduced, train_seeds=(True, 202, 203), query_seeds=TEST_QUERY_SEEDS
        )
