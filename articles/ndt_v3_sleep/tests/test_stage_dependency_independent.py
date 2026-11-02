"""Independent adversarial checks for the stage-dependency policy boundary."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType

import h5py
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.stage_dependency_audit import audit


POLICY_SOURCE = Path(__file__).resolve().parents[1] / "stage_dependency_policy_20260910.json"


def _write_policy(path: Path, **updates: object) -> Path:
    policy = json.loads(POLICY_SOURCE.read_text(encoding="utf-8"))
    policy.update(updates)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(policy), encoding="utf-8")
    return path


def _write_h5(
    path: Path,
    *,
    epoch_id: object = (0, 1, 2),
    time: object = (0.0, 30.0, 60.0),
    window_start: object = (0.0, 30.0, 60.0),
    window_end: object = (30.0, 60.0, 90.0),
    stage: object = (0, 8, 2),
    raw_files: object | None = None,
) -> Path:
    with h5py.File(path, "w") as handle:
        handle.create_dataset("epoch_id", data=np.asarray(epoch_id))
        handle.create_dataset("time", data=np.asarray(time))
        handle.create_dataset("window_start", data=np.asarray(window_start))
        handle.create_dataset("window_end", data=np.asarray(window_end))
        handle.create_dataset("labels/stage", data=np.asarray(stage))
        if raw_files is not None:
            handle.create_dataset("row_source/raw_file", data=np.asarray(raw_files, dtype="S64"))
    return path


def _reader_module(monkeypatch: pytest.MonkeyPatch, *, status: str = "legacy_missing") -> None:
    module = ModuleType("nmd_analysis.signal_support")
    module.__file__ = "J:/repos/nmd-analysis/nmd-analysis/nmd_analysis/signal_support.py"
    module.read_signal_support = lambda path: {
        "status": status,
        "reference_fit_population": {"status": "unknown"},
        "source_quality_intervals": [],
    }
    package = ModuleType("nmd_analysis")
    package.signal_support = module
    monkeypatch.setitem(sys.modules, "nmd_analysis", package)
    monkeypatch.setitem(sys.modules, "nmd_analysis.signal_support", module)


def _run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, h5: Path, **policy_updates: object) -> dict:
    _reader_module(monkeypatch)
    policy = _write_policy(tmp_path / "policy.json", **policy_updates)
    return audit([h5], policy, tmp_path / "out")


def _assert_fail_closed(callable_obj) -> None:
    with pytest.raises((ValueError, RuntimeError, TypeError, OverflowError)):
        callable_obj()


def test_fractional_ids_and_stage_codes_are_rejected_without_truncation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fractional_ids = _write_h5(
        tmp_path / "fractional_ids.h5",
        epoch_id=(0.0, 1.5, 2.0),
    )
    _assert_fail_closed(lambda: _run(tmp_path / "ids", monkeypatch, fractional_ids))

    fractional_stage = _write_h5(tmp_path / "fractional_stage.h5", stage=(0.0, 8.9, 2.0))
    _assert_fail_closed(lambda: _run(tmp_path / "stage", monkeypatch, fractional_stage))


def test_nonfinite_ids_and_labels_are_not_cast_to_unknown_or_known(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    h5 = _write_h5(tmp_path / "nan_stage.h5", stage=(0.0, np.nan, 2.0))
    _assert_fail_closed(lambda: _run(tmp_path, monkeypatch, h5))


def test_two_dimensional_and_boolean_label_arrays_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    two_dimensional = _write_h5(tmp_path / "two_dimensional.h5", stage=np.asarray([[0], [8], [2]], dtype=np.int64))
    _assert_fail_closed(lambda: _run(tmp_path / "two_dimensional", monkeypatch, two_dimensional))

    boolean_labels = _write_h5(tmp_path / "boolean_labels.h5", stage=np.asarray([True, False, True], dtype=bool))
    _assert_fail_closed(lambda: _run(tmp_path / "boolean_labels", monkeypatch, boolean_labels))


def test_positive_gap_overlap_and_id_break_remain_explicit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    h5 = _write_h5(
        tmp_path / "geometry_breaks.h5",
        epoch_id=(0, 2, 3),
        time=(0.0, 30.0, 60.0),
        window_start=(0.0, 35.0, 55.0),
        window_end=(30.0, 65.0, 85.0),
        stage=(0, 1, 2),
    )
    report = _run(tmp_path, monkeypatch, h5)
    source = report["sources"][0]
    assert source["epoch_id_break_count"] == 1
    assert source.get("window_gap_count") == 1
    assert source.get("window_overlap_count") == 1
    assert source["intrinsic_support_status"] == "not_assessed"
    assert source["full_support_status"] == "unknown"
    assert source["qualified_increment_count"] is None


def test_known_labels_do_not_create_stage_intrinsic_qualification(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    h5 = _write_h5(tmp_path / "all_known.h5", stage=(0, 1, 2))
    report = _run(tmp_path, monkeypatch, h5)
    source = report["sources"][0]
    assert source["descriptive_stage_label_association"]["stage_purity"] == "not_established"
    assert source["intrinsic_support_status"] == "not_assessed"
    assert source["full_support_status"] == "unknown"
    assert source["qualified_increment_count"] is None
    assert report["subject_pooling"] == "not_performed"


def test_policy_schema_and_status_are_frozen_and_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    h5 = _write_h5(tmp_path / "policy_input.h5")
    _reader_module(monkeypatch)
    future = _write_policy(tmp_path / "future.json", schema="ndt.sleep.stage_dependency_policy.v99")
    _assert_fail_closed(lambda: audit([h5], future, tmp_path / "future_out"))

    invalid = _write_policy(tmp_path / "invalid.json", status="not_assessed")
    _assert_fail_closed(lambda: audit([h5], invalid, tmp_path / "invalid_out"))


def test_multiple_recordings_remain_separate_and_unknown_counts_are_null(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first = _write_h5(tmp_path / "first.h5", stage=(0, 1, 2))
    second = _write_h5(tmp_path / "second.h5", stage=(2, 3, 4))
    _reader_module(monkeypatch)
    policy = _write_policy(tmp_path / "policy.json")
    report = audit([first, second], policy, tmp_path / "out")
    assert report["status"] == "audited"
    assert len(report["sources"]) == 2
    assert all(source["qualified_increment_count"] is None for source in report["sources"])
    assert report["subject_pooling"] == "not_performed"


def test_raw_file_identity_rows_cannot_have_a_different_length(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    h5 = _write_h5(tmp_path / "raw_file_mismatch.h5", raw_files=("one.edf",))
    _assert_fail_closed(lambda: _run(tmp_path, monkeypatch, h5))
