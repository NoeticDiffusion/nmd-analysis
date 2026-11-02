"""Contract tests for the bounded E1/E2 sleep family runner."""
from __future__ import annotations

import json
from pathlib import Path

import h5py
import numpy as np
import pytest

import new_family_sleep_analysis as analysis


def reference(n: int = 6) -> dict[str, object]:
    return {"epoch_id": np.arange(100, 100 + n), "time": np.arange(n, dtype=float) * 30 + 15, "stage": np.array([0, 2, 8, 99, 2, 0], dtype=np.int8)[:n], "n_rows": n}


def test_jacobian_centers_are_explicit_and_gaps_are_retained():
    rows = [
        {"center": 1, "window_id": 0, "spectral_abscissa": 1.0},
        {"center": 3, "window_id": 1, "spectral_abscissa": 2.0},
    ]
    mapped = analysis.map_jacobian_rows(rows, reference())
    assert [row["mapped_epoch_position"] for row in mapped] == [1, 3]
    assert [row["epoch_id"] for row in mapped] == [101, 103]
    assert mapped[1]["center_gap_before"] == 2
    assert mapped[1]["center_gap_before_is_nonconsecutive"] is True
    assert [row["stage_key"] for row in mapped] == ["N2", "Unknown"]


@pytest.mark.parametrize(
    "rows",
    [
        [{"center": 1}, {"center": 1}],
        [{"center": 6}],
        [{"center": 1.5}],
        [{"center": None}],
    ],
)
def test_invalid_jacobian_center_mapping_fails_closed(rows):
    with pytest.raises(ValueError):
        analysis.map_jacobian_rows(rows, reference())


def test_diffusion_mapping_preserves_support_floor_and_unknown_stage():
    ref = reference()
    rows = [{
        "window_id": 2,
        "epoch_id": 102,
        "timestamp": 75.0,
        "stage": 8,
        "D_total": 3.0,
        "finite_ok": True,
        "support_count": None,
        "support_n": None,
        "valid": None,
        "psd_floor_applied": 1,
        "raw_min_eigenvalue": -1e-7,
    }]
    mapped = analysis.map_diffusion_rows(rows, ref)
    endpoint = analysis._endpoint_row(mapped[0], recording="rec", family="diffusion_geometry", dimension=3, metric="D_total")
    assert endpoint["stage_key"] == "Code8"
    assert endpoint["support_status"] == "not_recorded"
    assert endpoint["support_count"] is None
    assert endpoint["psd_floor_applied"] == 1
    assert endpoint["raw_min_eigenvalue"] == pytest.approx(-1e-7)
    assert endpoint["used"] is True


@pytest.mark.parametrize("missing", ["epoch_id", "timestamp", "stage"])
def test_diffusion_mapping_requires_exact_query_identifiers(missing):
    row = {
        "window_id": 2,
        "epoch_id": 102,
        "timestamp": 75.0,
        "stage": 8,
        "D_total": 3.0,
        "finite_ok": True,
    }
    row.pop(missing)
    with pytest.raises(ValueError, match=f"diffusion {missing} missing"):
        analysis.map_diffusion_rows([row], reference())


def test_unknown_qualification_is_null_and_n2_wake_is_separate():
    rows = [
        analysis._endpoint_row({"center": 1, "window_id": 0, "mapped_epoch_position": 1, "epoch_id": 101, "time": 45.0, "timestamp": 45.0, "stage_code": 2, "stage_code_raw": 2, "stage_label": "N2", "stage_label_status": "recorded", "stage_key": "N2", "D_total": 4.0, "finite_ok": True, "measurement_validity": "not_assessed"}, recording="rec", family="diffusion_geometry", dimension=3, metric="D_total"),
        analysis._endpoint_row({"center": 5, "window_id": 1, "mapped_epoch_position": 5, "epoch_id": 105, "time": 165.0, "timestamp": 165.0, "stage_code": 0, "stage_code_raw": 0, "stage_label": "Wake", "stage_label_status": "recorded", "stage_key": "Wake", "D_total": 1.0, "finite_ok": True, "measurement_validity": "not_assessed"}, recording="rec", family="diffusion_geometry", dimension=3, metric="D_total"),
        analysis._endpoint_row({"center": 2, "window_id": 2, "mapped_epoch_position": 2, "epoch_id": 102, "time": 75.0, "timestamp": 75.0, "stage_code": 8, "stage_code_raw": 8, "stage_label": "Code8", "stage_label_status": "code8", "stage_key": "Code8", "D_total": 2.0, "finite_ok": True, "measurement_validity": "not_assessed"}, recording="rec", family="diffusion_geometry", dimension=3, metric="D_total"),
    ]
    summaries, contrasts = analysis.summarize_all(rows)
    code8 = next(row for row in summaries if row["stage_key"] == "Code8")
    assert code8["n"] == 1
    assert code8["producer_finite_valid_rows"] == 1
    assert "producer_valid_rows" not in code8
    assert code8["qualification_rows"] is None
    assert code8["qualification_evaluated"] is False
    contrast = contrasts[0]
    assert contrast["n2_minus_wake_median"] == pytest.approx(3.0)
    assert contrast["qualification_valid"] is None


def test_missing_family_groups_are_reported_as_unavailable(tmp_path, monkeypatch):
    h5 = tmp_path / "missing.h5"
    with h5py.File(h5, "w") as handle:
        handle.create_dataset("epoch_id", data=np.arange(3))
        handle.create_dataset("time", data=np.array([15.0, 45.0, 75.0]))
        handle.create_dataset("labels/stage", data=np.array([0, 2, 0], dtype=np.int8))
    monkeypatch.setattr(analysis, "jacobian_metrics_window_rows", lambda *args, **kwargs: [])
    monkeypatch.setattr(analysis, "diffusion_window_rows", lambda *args, **kwargs: [])
    rows, metadata = analysis.endpoint_rows_for_recording(h5, "missing")
    assert rows == []
    assert metadata["availability"]["E1_3D"]["status"] == "unavailable"
    assert metadata["availability"]["E1_9D"]["status"] == "unavailable"
    assert metadata["availability"]["E2_3D"]["status"] == "unavailable"


def test_availability_uses_recorded_producer_status_and_counts_mixed_rows():
    status = analysis._producer_status([
        {"computation_status": "computed"},
        {"computation_status": "invalid"},
        {},
    ])
    assert status["status"] == "mixed"
    assert status["computation_status_counts"] == {"computed": 1, "invalid": 1, "not_recorded": 1}
    assert analysis._producer_status([]) == {"status": "unavailable", "computation_status_counts": {}}


def test_strict_json_conversion_turns_nonfinite_values_into_null(tmp_path):
    path = tmp_path / "strict.json"
    analysis._write_json(path, {"finite": 1.0, "missing": float("nan"), "nested": [float("inf")]})
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload == {"finite": 1.0, "missing": None, "nested": [None]}


def test_missing_fixed_endpoint_has_empty_stage_rows_and_null_contrast():
    summaries, contrasts = analysis.summarize_all([], recordings=["missing"])
    assert len(summaries) == len(analysis.EXPECTED_ENDPOINTS) * len(analysis.STAGE_KEYS)
    assert len(contrasts) == len(analysis.EXPECTED_ENDPOINTS)
    assert all(row["n"] == 0 and row["median"] is None and row["q25"] is None and row["q75"] is None for row in summaries)
    assert all(row["producer_finite_valid_rows"] == 0 and row["qualification_rows"] is None for row in summaries)
    assert all(row["n2_minus_wake_median"] is None and row["wake_n"] == 0 and row["n2_n"] == 0 for row in contrasts)
