from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "articles"
    / "BOAS_sleep_dataset_ndt._v.1.0"
    / "src"
    / "audit_all_fold_apply_stage_horizon_support.py"
)
SPEC = importlib.util.spec_from_file_location("boas_stage_horizon_support", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def _row(epoch: int, start: float) -> dict[str, object]:
    return {
        "epoch_id": epoch,
        "t_start": start,
        "t_end": start + 30.0,
        "segment_id": 0,
        "primary_surface_eligible": True,
        "source_stratum": "pure_ppg",
        "support_exclusion_reasons": None,
        "source_sample_mapping_status": "nominal_bounds_mapped",
        "actual_sample_contributors_status": "finite_causal_conservative_bound",
        "input_sample_finite_status": "all_finite",
        "input_sample_gap_count": 0,
        "qc_ok_eeg": True,
        "qc_ok_ppg": True,
        "chart_row_present": True,
        "chart_geometry_valid": True,
        "chart_retained_after_qc": True,
        "chart_coords_3d_all_finite": True,
        "chart_coords_9d_all_finite": True,
        "chart_mnps_3d_valid": True,
        "chart_coords_9d_valid": True,
    }


def test_contiguous_horizon_is_eligible_and_uses_actual_time() -> None:
    rows = {i: _row(i, i * 30.0) for i in range(3)}
    # Future/intermediate stage values are intentionally irrelevant to the path gate.
    rows[1]["stage_at_origin_code"] = 3
    result = AUDIT._assess_path(rows, origin_id=0, lag=1, dimension="3d")
    assert result["pair_eligible"] is True
    assert result["actual_horizon_sec"] == 30.0


def test_missing_intermediate_row_is_not_bridged() -> None:
    rows = {0: _row(0, 0.0), 2: _row(2, 60.0)}
    result = AUDIT._assess_path(rows, origin_id=0, lag=2, dimension="3d")
    assert result["target_present"] is True
    assert result["pair_eligible"] is False
    assert result["failure_reason"] == "missing_intermediate_or_target_row"


def test_timestamp_gap_blocks_pair() -> None:
    rows = {0: _row(0, 0.0), 1: _row(1, 31.0)}
    result = AUDIT._assess_path(rows, origin_id=0, lag=1, dimension="3d")
    assert result["pair_eligible"] is False
    assert result["failure_reason"] == "gap_or_segment_break"


def test_invalid_intermediate_coordinate_blocks_pair() -> None:
    rows = {i: _row(i, i * 30.0) for i in range(3)}
    rows[1]["chart_mnps_3d_valid"] = False
    result = AUDIT._assess_path(rows, origin_id=0, lag=2, dimension="3d")
    assert result["time_contiguous"] is True
    assert result["pair_eligible"] is False
    assert result["failure_reason"] == "coordinate_or_geometry_qc_invalid"


def test_c3_origin_requires_unique_stage_and_stage_pure_window() -> None:
    origin = _row(0, 0.0)
    origin.update({
        "stage_at_origin_code": 2,
        "stage_at_origin_status": "unique_source_stage_at_origin",
        "stage_window_pure": True,
        "stage_window_status": "stage_pure_at_origin",
    })
    assert AUDIT._stage_origin_ok(origin, 2) is True
    origin["stage_window_pure"] = False
    assert AUDIT._stage_origin_ok(origin, 2) is False


def test_c3_origin_requires_explicit_stage_pure_status() -> None:
    origin = _row(0, 0.0)
    origin.update({
        "stage_at_origin_code": 2,
        "stage_at_origin_status": "unique_source_stage_at_origin",
        "stage_window_pure": True,
        "stage_window_status": "origin_or_window_invalid",
    })
    assert AUDIT._stage_origin_ok(origin, 2) is False


def test_full_surface_provenance_requires_exactly_128_event_sources() -> None:
    map_validation = {
        "schema_version": "boas.all_fold_apply_chart_support_map.v2",
        "label_join_performed": False,
        "stage_horizon_intersection_computed": False,
        "contrasts_computed": False,
        "biological_claim_authorized": False,
    }
    event_hashes = {f"events:{index}": f"hash-{index}" for index in range(128)}
    surface_validation = {
        "schema": "nmd_analysis.continuous_full_surface_audit.v1",
        "status": "PARTIAL_PASS_SOURCE_SUPPORT_ONLY",
        "c3_context": "human-scored N2 versus Wake at forecast origin; frozen preregistration context",
        "provenance": {"source_stage_column": "stage_hum"},
        "outcomes_calculated": False,
        "full_cohort_scoring_authorized": False,
        "input_hashes_before": event_hashes,
        "input_hashes_after": event_hashes.copy(),
    }
    AUDIT._assert_input_provenance(map_validation, surface_validation)
    surface_validation["input_hashes_before"].pop("events:127")
    surface_validation["input_hashes_after"].pop("events:127")
    with pytest.raises(RuntimeError, match="exactly 128 event sources"):
        AUDIT._assert_input_provenance(map_validation, surface_validation)
    surface_validation["input_hashes_before"] = event_hashes.copy()
    surface_validation["input_hashes_after"] = event_hashes.copy()
    surface_validation["input_hashes_after"]["events:unexpected"] = "extra-hash"
    with pytest.raises(RuntimeError, match="event-source key set changed"):
        AUDIT._assert_input_provenance(map_validation, surface_validation)
