"""Independent structural contract checks for the increment support audit."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import yaml

from src.increment_support_audit import audit_rows, build_pool, run


class _Dataset:
    def __init__(self, value):
        self.value = np.asarray(value)

    def __getitem__(self, _key):
        return self.value


class _H5:
    def __init__(self, *, fractional_id: bool = False, unordered: bool = False):
        ids = np.array([100, 101, 103, 104, 105], dtype=float)
        if fractional_id:
            ids[1] = 101.5
        starts = np.array([0, 30, 60, 90, 120], dtype=float)
        ends = starts + 30
        if unordered:
            ends[0] = -1
        self.values = {
            "/epoch_id": ids,
            "/window_start": starts,
            "/window_end": ends,
            "/time": starts + 15,
            "/labels/stage": np.array([0, 8, 0, 0, 1], dtype=int),
            "/row_source/raw_file": np.array([b"recording.edf"] * 5),
            "/coords_3d_subject_anchored/values": np.ones((5, 3), dtype=float),
        }

    def __getitem__(self, key):
        return _Dataset(self.values[key])


def _row(**overrides):
    row = {
        "query_epoch_id": "100",
        "query_index": "0",
        "query_stage_code": "0",
        "query_stage_unknown": "0",
        "query_window_start": "0",
        "query_window_end": "30",
        "selection_index": "0",
        "source_epoch_id": "100",
        "source_index": "0",
        "source_stage_code": "0",
        "source_stage_unknown": "0",
        "source_window_start": "0",
        "source_window_end": "30",
        "target_epoch_id": "101",
        "target_index": "1",
        "target_stage_code": "8",
        "target_stage_unknown": "1",
        "target_window_start": "30",
        "target_window_end": "60",
        "distance_squared": "1",
        "dt_sec": "30",
        "kth_distance_tie_ambiguous": "0",
    }
    row.update({key: str(value) for key, value in overrides.items()})
    return row


def test_structural_support_is_separate_from_stage_support_and_unknown_is_explicit():
    result = audit_rows([_row()], _H5(), nominal_dt=30.0, max_rel_dt=0.05)[0]

    assert result["structurally_admissible"] == 1
    assert result["same_known_stage"] == 0
    assert result["target_stage_h5"] == 8
    assert result["target_stage_unknown_h5"] == 1
    assert result["full_support_status"] == "not_assessed"


def test_epoch_id_gap_cannot_be_bridged():
    result = audit_rows(
        [
            _row(
                query_epoch_id="101",
                query_index="1",
                query_stage_code="8",
                query_stage_unknown="1",
                query_window_start="30",
                query_window_end="60",
                selection_index="1",
                source_epoch_id="101",
                source_index="1",
                source_stage_code="8",
                source_stage_unknown="1",
                source_window_start="30",
                source_window_end="60",
                target_epoch_id="103",
                target_index="2",
                target_stage_code="0",
                target_stage_unknown="0",
                target_window_start="60",
                target_window_end="90",
            )
        ],
        _H5(),
        nominal_dt=30.0,
        max_rel_dt=0.05,
    )[0]

    assert result["source_target_consecutive"] == 0
    assert result["structurally_admissible"] == 0


def test_full_adjacent_pool_preserves_id_break_and_unknown_endpoint():
    pool = build_pool(_H5(), nominal_dt=30.0, max_rel_dt=0.05)

    assert len(pool) == 4
    id_break = next(row for row in pool if row["source_epoch_id"] == 101)
    assert id_break["source_target_consecutive"] == 0
    assert id_break["structurally_admissible"] == 0
    code8_pair = next(row for row in pool if row["source_stage_h5"] == 8)
    assert code8_pair["touches_code8"] == 1
    assert code8_pair["same_known_endpoint_stage"] == 0


def test_fractional_candidate_id_is_not_truncated_into_a_valid_reference():
    with pytest.raises((ValueError, TypeError)):
        audit_rows([_row(target_epoch_id="101.5")], _H5(), 30.0, 0.05)


def test_fractional_h5_id_is_rejected_before_id_mapping():
    with pytest.raises((ValueError, TypeError)):
        audit_rows([_row()], _H5(fractional_id=True), 30.0, 0.05)


def test_stage_code_mismatch_is_rejected_instead_of_relabelled():
    with pytest.raises(ValueError, match="target_stage_code"):
        audit_rows([_row(target_stage_code="0", target_stage_unknown="0")], _H5(), 30.0, 0.05)


def test_nonordered_window_bounds_are_not_admissible():
    # The candidate row must reproduce the H5 bounds before structural
    # admissibility is evaluated.  A malformed H5 bound therefore fails
    # closed instead of being converted into a structural zero.
    with pytest.raises(ValueError, match="bound"):
        audit_rows([_row()], _H5(unordered=True), 30.0, 0.05)


def test_duplicate_query_selection_is_rejected_instead_of_changing_denominator():
    with pytest.raises(ValueError, match="duplicate"):
        audit_rows([_row(), _row()], _H5(), 30.0, 0.05)


def test_runner_rejects_bad_input_pin_before_creating_output(tmp_path):
    config_path = Path(__file__).parents[1] / "config" / "increment_support_sub99.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["pins"]["input_h5"] = "0" * 64
    config["output_root"] = str(tmp_path / "should_not_exist")
    bad_config = tmp_path / "bad_pin.yaml"
    bad_config.write_text(yaml.safe_dump(config), encoding="utf-8")

    with pytest.raises(ValueError, match="hash mismatch"):
        run(bad_config)
    assert not (tmp_path / "should_not_exist").exists()


def test_runner_rejects_empty_selected_membership_before_export(tmp_path):
    config_path = Path(__file__).parents[1] / "config" / "increment_support_sub99.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    empty_neighbors = tmp_path / "candidate_neighbors.csv"
    empty_neighbors.write_text("query_epoch_id,source_epoch_id,target_epoch_id\n", encoding="utf-8")
    import hashlib

    config["candidate_neighbors"] = str(empty_neighbors)
    config["pins"]["candidate_neighbors"] = hashlib.sha256(empty_neighbors.read_bytes()).hexdigest()
    config["output_root"] = str(tmp_path / "should_not_exist")
    bad_config = tmp_path / "missing_neighbors.yaml"
    bad_config.write_text(yaml.safe_dump(config), encoding="utf-8")

    with pytest.raises(ValueError, match="candidate query coverage mismatch"):
        run(bad_config)
    assert not (tmp_path / "should_not_exist").exists()
