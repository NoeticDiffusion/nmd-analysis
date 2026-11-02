import hashlib
import inspect
import json
from pathlib import Path

import numpy as np
import nmd_analysis.dynamical_families.chart_benchmark as chart_benchmark

from nmd_analysis.dynamical_families.chart_benchmark import (
    FROZEN_IDENTITY_TOLERANCE,
    main,
    run_chart_benchmark,
)


def test_chart_benchmark_is_json_safe_and_spec_hash_is_frozen():
    first = run_chart_benchmark()
    second = run_chart_benchmark()

    assert json.loads(json.dumps(first)) == first
    assert first["numeric_spec_sha256"] == second["numeric_spec_sha256"]
    assert first["m3_gate"] == "not_applicable"
    assert first["claim_status"] == "no_biological_claim"
    assert first["scientific_qualification"] == "not_assessed"
    assert first["contract_status"] == "all_expected_contracts_refused"
    assert first["contract_failure_count"] == 0
    assert first["unexpected_contracts"] == []
    provenance = first["provenance"]
    assert provenance["source"]["chart_module_sha256"]
    assert provenance["source"]["drift_module_sha256"]
    assert provenance["runtime"]["python"]
    assert provenance["runtime"]["numpy"]
    assert provenance["runtime"]["scipy"]
    chart_path = Path(chart_benchmark.__file__).resolve()
    drift_path = Path(inspect.getsourcefile(chart_benchmark.crossfit_local_chart_b)).resolve()
    assert provenance["source"]["chart_module_sha256"] == hashlib.sha256(
        chart_path.read_bytes()
    ).hexdigest()
    assert provenance["source"]["drift_module_sha256"] == hashlib.sha256(
        drift_path.read_bytes()
    ).hexdigest()


def test_orthogonal_and_isotropic_maps_are_equivariant_for_both_estimators():
    result = run_chart_benchmark()
    for map_name in ("orthogonal", "isotropic"):
        audit = result["coordinate_maps"][map_name]
        assert audit["oracle_coordinate_identity"]["within_identity_tolerance"]
        for estimator in ("local_mean", "local_linear"):
            check = audit["estimators"][estimator]
            assert check["neighbor_identity_unchanged"]
            assert check["within_identity_tolerance"]
            assert check["max_abs_estimator_discrepancy"] <= FROZEN_IDENTITY_TOLERANCE


def test_anisotropic_map_separates_metric_sensitivity_from_oracle_identity():
    result = run_chart_benchmark()
    audit = result["anisotropic_scaling"]

    assert audit["oracle_coordinate_identity"]["within_identity_tolerance"]
    for estimator in ("local_mean", "local_linear"):
        check = audit["euclidean_neighbor_estimator_sensitivity"][estimator]
        assert not check["neighbor_identity_unchanged"]
        assert check["max_abs_discrepancy"] > FROZEN_IDENTITY_TOLERANCE
    assert not audit["alignment"]["invariance_expected"]
    assert audit["alignment"]["regularization"] == "none"
    assert audit["alignment"]["not_production_C1_alignment"] is True
    assert audit["alignment"]["absolute_difference"] > FROZEN_IDENTITY_TOLERANCE
    assert not audit["effective_dimension"]["invariance_expected"]
    assert audit["effective_dimension"]["absolute_difference"] > FROZEN_IDENTITY_TOLERANCE


def test_projection_counterexample_is_information_loss_not_coordinate_failure():
    projection = run_chart_benchmark()["projection_information_loss"]

    assert projection["classification"] == "projection_information_loss"
    assert projection["failed_coordinate_invariance"] is False
    assert projection["same_projected_current"] is True
    assert projection["projected_expected_future_equal"] is False


def test_covariance_transform_is_explicit_for_all_maps():
    result = run_chart_benchmark()
    for audit in result["covariance_transform"].values():
        assert audit["formula"] == "Q_prime = H Q H.T"
        assert audit["construction"] == "L_prime = H @ chol(Q); actual = L_prime @ L_prime.T"
        assert audit["within_identity_tolerance"]
        assert audit["max_abs_covariance_transform_discrepancy"] <= FROZEN_IDENTITY_TOLERANCE
        actual = np.asarray(audit["actual_covariance"])
        expected = np.asarray(audit["expected_covariance"])
        factor = np.asarray(audit["transformed_factor"])
        assert actual.shape == expected.shape == factor.shape == (3, 3)
        assert np.allclose(actual, factor @ factor.T, rtol=0.0, atol=FROZEN_IDENTITY_TOLERANCE)
        assert np.allclose(expected, np.asarray(audit["Q_prime"]), rtol=0.0, atol=0.0)


def test_failure_contract_audit_reports_unexpected_behavior_separately():
    result = run_chart_benchmark()
    failure_contracts = result["failure_contracts"]
    assert set(failure_contracts) >= {
        "irregular_dt",
        "nonfinite_input",
        "insufficient_support",
        "rank_deficient_local_linear",
        "increment_overlap",
        "shared_endpoint",
        "raw_support_overlap",
        "positive_embargo",
        "noncontiguous_gap",
        "finite_huge_overflow_guard",
    }
    assert result["contract_failure_count"] == len(result["unexpected_contracts"])
    assert result["contract_failure_count"] == sum(
        not bool(case.get("contract_check", False)) for case in failure_contracts.values()
    )


def test_cli_writes_json_to_requested_output_path(tmp_path):
    output = tmp_path / "chart_benchmark.json"
    assert main(["--output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "nmd_analysis.chart_benchmark.v1"
    assert payload["numeric_spec_sha256"] == run_chart_benchmark()["numeric_spec_sha256"]
