"""Contract tests for the read-only new-family inventory."""
from __future__ import annotations

import numpy as np

from inventory_new_families import row_counts


def test_unknown_qualification_is_null_and_validity_is_not_inferred():
    rows = [
        {"value": 1.0, "computation_status": "computed", "finite_ok": True, "measurement_validity": "not_assessed"},
        {"value": 2.0, "computation_status": "computed", "finite_ok": True, "measurement_validity": "not_recorded"},
    ]
    result = row_counts(rows, "value")
    assert result["n_family_computed_rows"] == 2
    assert result["n_finite"] == 2
    assert result["n_adapter_finite_valid"] == 2
    assert result["n_measurement_valid"] is None
    assert result["n_qualified"] is None
    assert result["qualification_evaluated"] is False
    assert result["measurement_validity_counts"] == {"not_assessed": 1, "not_recorded": 1}


def test_scalar_and_matrix_finiteness_are_row_counts_and_adapter_flag_is_separate():
    rows = [
        {"metric": 1.0, "computation_status": "computed", "finite_ok": True},
        {"metric": np.array([[1.0, 2.0], [3.0, 4.0]]), "computation_status": "computed", "finite_ok": True},
        {"metric": np.array([[1.0, np.nan], [3.0, 4.0]]), "computation_status": "computed", "finite_ok": True},
        {"metric": 5.0, "computation_status": "computed", "finite_ok": False},
    ]
    result = row_counts(rows, "metric")
    assert result["n_rows"] == 4
    assert result["n_family_computed_rows"] == 4
    assert result["n_finite"] == 3
    assert result["n_adapter_finite_valid"] == 2
    assert result["n_finite_metric_value"] == 3


def test_unavailable_drift_is_not_zero_and_not_adapter_valid():
    rows = [
        {"drift": np.nan, "computation_status": "computed", "finite_ok": False},
        {"drift": np.nan, "computation_status": "computed", "finite_ok": False},
    ]
    result = row_counts(rows, "drift")
    assert result["n_family_computed_rows"] == 2
    assert result["n_finite"] == 0
    assert result["n_adapter_finite_valid"] == 0
    assert result["n_measurement_valid"] is None
    assert result["n_qualified"] is None
