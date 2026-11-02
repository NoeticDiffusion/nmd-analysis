"""Synthetic fail-closed tests for the bounded sleep drift candidate wrapper."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import h5py

from nmd_analysis.dynamical_families.drift import DriftContractError, crossfit_local_chart_b
import sleep_drift_candidate as candidate
from sleep_drift_candidate import (
    CandidateContractError,
    _support_audit,
    _canonical_json,
    sha256_bytes,
)


def _trajectory(n: int = 40) -> tuple[np.ndarray, np.ndarray]:
    time = np.arange(n, dtype=float) * 30.0
    index = np.arange(n, dtype=float)
    trajectory = np.column_stack((np.sin(index / 5.0), np.cos(index / 7.0), index / 100.0))
    return trajectory, time


def _write_h5(path: Path, *, geometry_status: str = "ok", width: float = 30.0,
              contiguous: bool = True, gapped_time: bool = False,
              nonfinite: bool = False, bad_shape: bool = False) -> str:
    n = 805
    time = np.arange(n, dtype=float) * 30.0 + 15.0
    if gapped_time:
        time[700:] += 30.0
    starts = np.arange(n, dtype=float) * 30.0
    ends = starts + width
    if not contiguous:
        starts[100] += 1.0
        ends[100] += 1.0
    rng = np.random.default_rng(42)
    x3 = rng.normal(size=(n, 3))
    x9 = rng.normal(size=(n, 9))
    if nonfinite:
        x3[20, 0] = np.nan
    if bad_shape:
        x9 = x9[:, :8]
    with h5py.File(path, "w") as handle:
        handle.attrs["schema_version"] = "mnps_tensor_spec_v2_4"
        handle.attrs["primary_coordinate_contract"] = "subject_anchored"
        handle.attrs["primary_coordinate_layer"] = "coords_3d_subject_anchored"
        handle.attrs["mnps_axis_names"] = np.asarray([b"m", b"d", b"e"])
        handle.attrs["normalize_mode"] = "robust_z"
        handle.create_dataset("time", data=time)
        handle.create_dataset("window_start", data=starts)
        handle.create_dataset("window_end", data=ends)
        handle.create_dataset("epoch_id", data=np.arange(n, dtype=np.int64))
        handle.create_dataset("mnps_3d", data=x3)
        handle.create_dataset("coords_3d_subject_anchored/values", data=x3)
        handle.create_dataset("coords_9d/values", data=x9)
        handle.create_dataset("coords_9d_subject_anchored/values", data=x9)
        handle.create_dataset("coords_9d/names", data=np.asarray([b"m_a", b"m_e", b"m_o", b"d_n", b"d_l", b"d_s", b"e_e", b"e_s", b"e_m"]))
        handle.create_dataset("provenance/geometry_contract/status", data=np.bytes_(geometry_status))
        handle.create_dataset("provenance/geometry_contract/time_grid/status", data=np.bytes_("ok"))
    return candidate.sha256_file(path)


def _fixture_config(tmp_path: Path, sources: list[tuple[str, Path, str]]) -> Path:
    template = json.loads(Path(candidate.__file__).parents[1].joinpath("config/sleep_drift_candidate_20260910.json").read_text(encoding="utf-8"))
    template["spec"]["sources"] = [
        {"recording": name, "path": str(path), "sha256": digest}
        for name, path, digest in sources
    ]
    template["frozen_spec_sha256"] = candidate.sha256_bytes(candidate._canonical_json(template["spec"]))
    config = tmp_path / "candidate.json"
    config.write_text(json.dumps(template, indent=2), encoding="utf-8")
    return config


def test_synthetic_gap_refuses_without_bridging():
    trajectory, time = _trajectory()
    time[25:] += 30.0
    with pytest.raises(DriftContractError, match="irregular dt"):
        crossfit_local_chart_b(trajectory, time, np.arange(0, 10), np.arange(20, 25), n_neighbors=8, min_train_support=3)


def test_synthetic_invalid_coordinate_refuses_without_imputation():
    trajectory, time = _trajectory()
    trajectory[4, 1] = np.nan
    with pytest.raises(DriftContractError, match="finite array"):
        crossfit_local_chart_b(trajectory, time, np.arange(0, 10), np.arange(20, 25), n_neighbors=8, min_train_support=3)


def test_synthetic_support_shortage_refuses():
    trajectory, time = _trajectory()
    with pytest.raises(DriftContractError, match="insufficient training support"):
        crossfit_local_chart_b(trajectory, time, np.arange(0, 2), np.arange(20, 25), n_neighbors=8, min_train_support=12)


def test_support_audit_reports_epoch_embargo_and_unknown_full_signal_support():
    train = np.asarray([[0.0, 30.0], [30.0, 60.0]])
    evaluation = np.asarray([[300.0, 330.0], [330.0, 360.0]])
    report = _support_audit(train, evaluation, 60.0)
    assert report["embargo_satisfied"] is True
    assert report["minimum_train_evaluation_support_distance_sec"] == 240.0
    assert report["full_signal_support_status"] == "unknown"


def test_support_audit_detects_embargo_violation():
    train = np.asarray([[0.0, 30.0]])
    evaluation = np.asarray([[60.0, 90.0]])
    report = _support_audit(train, evaluation, 60.0)
    assert report["embargo_satisfied"] is False
    assert report["embargo_violation_count"] == 1


def test_spec_hash_is_stable_and_strict_json_is_available():
    spec = {"split": {"train": [0, 600], "evaluation": [700, 800]}, "status": "candidate"}
    assert sha256_bytes(_canonical_json(spec)) == sha256_bytes(_canonical_json(json.loads(json.dumps(spec))))


def test_support_audit_refuses_nonfinite_separation():
    with pytest.raises(CandidateContractError):
        _support_audit(np.asarray([[0.0, np.inf]]), np.asarray([[300.0, 330.0]]), 60.0)


def test_wrapper_serializes_adjusted_source_as_four_null_refusals(tmp_path, monkeypatch):
    first = tmp_path / "sub99.h5"
    second = tmp_path / "sub1.h5"
    first_hash = _write_h5(first, geometry_status="ok")
    second_hash = _write_h5(second, geometry_status="adjusted")
    monkeypatch.setattr(candidate, "EXPECTED_SOURCE_HASHES", {"sub-99": first_hash, "sub-1": second_hash})
    config = _fixture_config(tmp_path, [("sub-99", first, first_hash), ("sub-1", second, second_hash)])
    report = candidate.run(config, tmp_path / "out")
    assert len(report["rows"]) == 8
    first_rows = [row for row in report["rows"] if row["recording"] == "sub-99"]
    second_rows = [row for row in report["rows"] if row["recording"] == "sub-1"]
    assert all(row["status"] == "computed_candidate" and row["n_predictions"] == 100 for row in first_rows)
    assert all(row["status"] == "refused" and row["refusal_class"] == "source_contract" and row["predictions"] is None for row in second_rows)
    assert all(row["source_h5_sha256"] == second_hash for row in second_rows)


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"width": 31.0}, "30-second window"),
        ({"contiguous": False}, "contiguous"),
        ({"gapped_time": True}, "30-second dt"),
        ({"nonfinite": True}, "nonfinite"),
        ({"bad_shape": True}, "unexpected shape"),
    ],
)
def test_wrapper_rejects_invalid_source_support_and_coordinates(tmp_path, monkeypatch, kwargs, message):
    path = tmp_path / "source.h5"
    digest = _write_h5(path, **kwargs)
    monkeypatch.setattr(candidate, "EXPECTED_SOURCE_HASHES", {"sub-99": digest, "sub-1": digest})
    config = json.loads(Path(candidate.__file__).parents[1].joinpath("config/sleep_drift_candidate_20260910.json").read_text(encoding="utf-8"))
    with pytest.raises(candidate.CandidateContractError, match=message):
        candidate._read_source({"recording": "sub-99", "path": str(path), "sha256": digest}, config["spec"])


def test_wrapper_rejects_hash_mismatch_and_existing_output(tmp_path):
    config = Path(candidate.__file__).parents[1].joinpath("config/sleep_drift_candidate_20260910.json")
    output = tmp_path / "existing"
    output.mkdir()
    (output / "keep.txt").write_text("preserve", encoding="utf-8")
    source_path = tmp_path / "hash_source.h5"
    source_hash = _write_h5(source_path)
    with pytest.raises(candidate.CandidateContractError, match="hash"):
        source = {"recording": "sub-99", "path": str(source_path), "sha256": "0" * 64}
        candidate._read_source(
            source,
            json.loads(config.read_text(encoding="utf-8"))["spec"],
        )
    with pytest.raises(FileExistsError):
        candidate.run(config, output)


def test_wrapper_serializes_estimator_rank_refusal(tmp_path):
    path = tmp_path / "rank_source.h5"
    digest = _write_h5(path)
    with h5py.File(path, "r+") as handle:
        x3 = np.asarray(handle["mnps_3d"][:])
        x9 = np.column_stack((x3, x3, x3))
        handle["coords_9d/values"][:] = x9
        handle["coords_9d_subject_anchored/values"][:] = x9
    digest = candidate.sha256_file(path)
    config = json.loads(Path(candidate.__file__).parents[1].joinpath("config/sleep_drift_candidate_20260910.json").read_text(encoding="utf-8"))
    metadata, arrays, before, _ = candidate._read_source(
        {"recording": "sub-99", "path": str(path), "sha256": digest}, config["spec"]
    )
    row = candidate._run_one(
        metadata,
        arrays,
        "coords_9d",
        "local_linear",
        config["spec"],
        before,
        {"runner_sha256": "test", "drift_sha256": "test", "config_sha256": "test"},
    )
    assert row["status"] == "refused"
    assert row["refusal_class"] == "estimator_contract"
    assert row["predictions"] is None and row["heldout_rows"] is None
    assert row["n_predictions"] == 0 and row["predictions_finite"] is None
