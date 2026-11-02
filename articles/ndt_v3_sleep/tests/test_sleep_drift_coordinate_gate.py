"""Fail-closed tests for the frozen adjusted-coordinate sleep gate."""

from __future__ import annotations

import json
from pathlib import Path

import h5py
import numpy as np
import pytest

import sleep_drift_candidate as candidate
import sleep_drift_coordinate_gate as gate


ARTICLE = Path(gate.__file__).parents[1]
POLICY_TEMPLATE = ARTICLE / "config" / "sleep_drift_coordinate_gate_20260912.json"
BASE_CONFIG_TEMPLATE = ARTICLE / "config" / "sleep_drift_candidate_20260910.json"


def _write_dataset(handle: h5py.File, path: str, value: object) -> None:
    handle.create_dataset(path, data=value)


def _write_source(
    path: Path,
    *,
    geometry_status: str = "ok",
    j9_status: str = "ok",
    j9_invalid: int = 0,
    j9_condition: int = 0,
    j9_nonfinite: int = 0,
    j9_raw: int = 803,
    j9_retained: int = 803,
    inconsistent_attr: bool = False,
    gap: bool = False,
    rank_deficient_9d: bool = False,
    extra_drop_reason: bool = False,
    j9_invalid_attr: object | None = None,
    epochs_before: object = 805,
    epochs_retained: object = 805,
    drop_reason_value: object = 0,
    retained_nonfinite: object = 0,
    finite_fraction: object = 1.0,
    omit_3d_geometry: bool = False,
    mnps3d_nonfinite: object = 0,
    mnps3d_degenerate: bool = False,
) -> str:
    n = 805
    time = np.arange(n, dtype=float) * 30.0 + 15.0
    if gap:
        time[700:] += 30.0
    starts = np.arange(n, dtype=float) * 30.0
    ends = starts + 30.0
    rng = np.random.default_rng(42)
    x3 = rng.normal(size=(n, 3))
    x9 = np.column_stack((x3, x3, x3)) if rank_deficient_9d else rng.normal(size=(n, 9))
    with h5py.File(path, "w") as handle:
        handle.attrs["schema_version"] = "mnps_tensor_spec_v2_4"
        handle.attrs["primary_coordinate_contract"] = "subject_anchored"
        handle.attrs["primary_coordinate_layer"] = "coords_3d_subject_anchored"
        handle.attrs["mnps_axis_names"] = np.asarray([b"m", b"d", b"e"])
        handle.attrs["normalize_mode"] = "robust_z"
        handle.attrs["geometry_contract_status"] = "ok" if inconsistent_attr else geometry_status
        handle.attrs["geometry_jacobian_invalid_windows"] = 0
        handle.attrs["geometry_jacobian_9d_invalid_windows"] = j9_invalid if j9_invalid_attr is None else j9_invalid_attr
        handle.attrs["dropped_geometry_invalid_epochs"] = 0
        handle.attrs["epochs_after_geometry_policy"] = n
        _write_dataset(handle, "time", time)
        _write_dataset(handle, "window_start", starts)
        _write_dataset(handle, "window_end", ends)
        _write_dataset(handle, "epoch_id", np.arange(n, dtype=np.int64))
        _write_dataset(handle, "mnps_3d", x3)
        _write_dataset(handle, "coords_3d_subject_anchored/values", x3)
        _write_dataset(handle, "coords_9d/values", x9)
        _write_dataset(handle, "coords_9d_subject_anchored/values", x9)
        _write_dataset(handle, "coords_9d/names", np.asarray([b"m_a", b"m_e", b"m_o", b"d_n", b"d_l", b"d_s", b"e_e", b"e_s", b"e_m"]))

        _write_dataset(handle, "provenance/geometry_contract/status", np.bytes_(geometry_status))
        _write_dataset(handle, "provenance/geometry_contract/policy_version", np.bytes_("standard_invalidity_v1"))
        _write_dataset(handle, "provenance/geometry_contract/time_grid/status", np.bytes_("ok"))
        _write_dataset(handle, "provenance/geometry_contract/shared_time_grid/epochs_before_policy", epochs_before)
        _write_dataset(handle, "provenance/geometry_contract/shared_time_grid/epochs_retained", epochs_retained)
        _write_dataset(handle, "provenance/geometry_contract/shared_time_grid/epochs_dropped", 0)
        _write_dataset(handle, "provenance/geometry_contract/shared_time_grid/drop_reason_counts/coords_9d_nonfinite_rows_affecting_primary", drop_reason_value)
        _write_dataset(handle, "provenance/geometry_contract/shared_time_grid/drop_reason_counts/mnps_3d_nonfinite_rows", 0)
        if extra_drop_reason:
            _write_dataset(handle, "provenance/geometry_contract/shared_time_grid/drop_reason_counts/unknown_reason", 0)
        _write_dataset(handle, "provenance/geometry_contract/coords_9d/available", True)
        _write_dataset(handle, "provenance/geometry_contract/coords_9d/shape_matches_time_grid", True)
        _write_dataset(handle, "provenance/geometry_contract/coords_9d/finite_row_fraction_before", finite_fraction)
        _write_dataset(handle, "provenance/geometry_contract/coords_9d/degenerate_axes", np.asarray([], dtype=np.int64))
        _write_dataset(handle, "provenance/geometry_contract/coords_9d/all_nan_axes", np.asarray([], dtype=np.int64))
        _write_dataset(handle, "provenance/geometry_contract/coords_9d/nonfinite_row_count", 0)
        _write_dataset(handle, "provenance/geometry_contract/coords_9d/nonfinite_rows_retained_on_shared_grid", retained_nonfinite)
        if not omit_3d_geometry:
            _write_dataset(handle, "provenance/geometry_contract/mnps_3d/finite_row_fraction_before", 1.0)
            _write_dataset(handle, "provenance/geometry_contract/mnps_3d/nonfinite_row_count", mnps3d_nonfinite)
            _write_dataset(handle, "provenance/geometry_contract/mnps_3d/degenerate_axes", np.asarray([0], dtype=np.int64) if mnps3d_degenerate else np.asarray([], dtype=np.int64))
            _write_dataset(handle, "provenance/geometry_contract/mnps_3d/all_nan_axes", np.asarray([], dtype=np.int64))
        _write_dataset(handle, "provenance/geometry_contract/jacobian/status", np.bytes_("ok"))
        _write_dataset(handle, "provenance/geometry_contract/jacobian/invalid_windows", 0)
        _write_dataset(handle, "provenance/geometry_contract/jacobian/windows_raw", 803)
        _write_dataset(handle, "provenance/geometry_contract/jacobian/windows_retained", 803)
        _write_dataset(handle, "provenance/geometry_contract/jacobian/invalid_reason_counts/condition_number_windows", 0)
        _write_dataset(handle, "provenance/geometry_contract/jacobian/invalid_reason_counts/nonfinite_windows", 0)
        _write_dataset(handle, "provenance/geometry_contract/jacobian_9d/status", np.bytes_(j9_status))
        _write_dataset(handle, "provenance/geometry_contract/jacobian_9d/invalid_windows", j9_invalid)
        _write_dataset(handle, "provenance/geometry_contract/jacobian_9d/windows_raw", j9_raw)
        _write_dataset(handle, "provenance/geometry_contract/jacobian_9d/windows_retained", j9_retained)
        _write_dataset(handle, "provenance/geometry_contract/jacobian_9d/invalid_reason_counts/condition_number_windows", j9_condition)
        _write_dataset(handle, "provenance/geometry_contract/jacobian_9d/invalid_reason_counts/nonfinite_windows", j9_nonfinite)

        _write_dataset(handle, "provenance/signal_support_provenance/status", np.bytes_("recorded"))
        _write_dataset(handle, "provenance/signal_support_provenance/schema", np.bytes_("mndm.signal_support_export.v1"))
        _write_dataset(handle, "provenance/signal_support_provenance/temporal_support_status", np.bytes_("unknown"))
        _write_dataset(handle, "provenance/signal_support_provenance/temporal_support_reason", np.bytes_("effective support unknown"))
        _write_dataset(handle, "provenance/signal_support_provenance/per_epoch_input_extent_json", np.bytes_(json.dumps([{"support_status": "unknown", "support_reason": "effective support unknown"}])))
        _write_dataset(handle, "support_signature/v1/status", np.bytes_("recorded"))
        _write_dataset(handle, "support_signature/v1/capability/chart_3d", np.bytes_("yes"))
        _write_dataset(handle, "support_signature/v1/capability/chart_9d", np.bytes_("yes"))
    return gate.sha256_file(path)


def _fixture(tmp_path: Path, *, first_kwargs: dict | None = None, second_kwargs: dict | None = None, wrong_hash: bool = False) -> tuple[Path, Path, str, str]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    first = tmp_path / "sub99.h5"
    second = tmp_path / "sub1.h5"
    first_hash = _write_source(first, **(first_kwargs or {}))
    second_hash = _write_source(second, geometry_status="adjusted", j9_status="adjusted", j9_invalid=2, j9_condition=2, j9_raw=803, j9_retained=801, **(second_kwargs or {}))
    policy = json.loads(POLICY_TEMPLATE.read_text(encoding="utf-8"))
    base = json.loads(BASE_CONFIG_TEMPLATE.read_text(encoding="utf-8"))
    sources = [
        {"recording": "sub-99", "path": str(first), "sha256": ("0" * 64 if wrong_hash else first_hash)},
        {"recording": "sub-1", "path": str(second), "sha256": second_hash},
    ]
    base["spec"]["sources"] = sources
    base["frozen_spec_sha256"] = candidate.sha256_bytes(candidate._canonical_json(base["spec"]))
    base_path = tmp_path / "sleep_drift_candidate_20260910.json"
    base_path.write_text(json.dumps(base, indent=2), encoding="utf-8")
    policy["spec"]["sources"] = sources
    policy["frozen_spec_sha256"] = gate.sha256_bytes(gate._canonical_json(policy["spec"]))
    policy_path = tmp_path / "sleep_drift_coordinate_gate_20260912.json"
    policy_path.write_text(json.dumps(policy, indent=2), encoding="utf-8")
    return policy_path, base_path, first_hash, second_hash


def test_gate_accepts_ok_and_condition_only_adjusted_sources(tmp_path, monkeypatch):
    policy_path, _, first_hash, second_hash = _fixture(tmp_path)
    monkeypatch.setattr(candidate, "EXPECTED_SOURCE_HASHES", {"sub-99": first_hash, "sub-1": second_hash})
    report = gate.run(policy_path, tmp_path / "out")
    assert len(report["rows"]) == 8
    by_recording = {name: [row for row in report["rows"] if row["recording"] == name] for name in ("sub-99", "sub-1")}
    assert all(row["strict_status"] == "computed_candidate" and row["scoped_status"] == "computed_candidate" for row in by_recording["sub-99"])
    assert all(row["strict_status"] == "refused" and row["scoped_status"] == "computed_candidate" and row["n_predictions"] == 100 for row in by_recording["sub-1"])
    assert all(row["source_geometry_status_observed"] == "adjusted" for row in by_recording["sub-1"])


@pytest.mark.parametrize(
    "kwargs, reason",
    [
        ({"first_kwargs": {"geometry_status": "unknown"}}, "overall geometry status"),
        ({"second_kwargs": {"inconsistent_attr": True}}, "inconsistent overall geometry"),
        ({"second_kwargs": {"extra_drop_reason": True}}, "drop reason keys"),
        ({"second_kwargs": {"j9_nonfinite": 1}}, "nonfinite-window"),
    ],
)
def test_gate_refuses_unknown_inconsistent_and_unapproved_geometry(tmp_path, monkeypatch, kwargs, reason):
    policy_path, _, first_hash, second_hash = _fixture(tmp_path, **kwargs)
    monkeypatch.setattr(candidate, "EXPECTED_SOURCE_HASHES", {"sub-99": first_hash, "sub-1": second_hash})
    report = gate.run(policy_path, tmp_path / "out")
    affected = "sub-99" if "first_kwargs" in kwargs else "sub-1"
    affected_rows = [row for row in report["rows"] if row["recording"] == affected]
    assert all(row["scoped_status"] == "refused" and row["predictions"] is None for row in affected_rows)
    assert any(reason.split("-")[0] in row["scoped_refusal_reason"] for row in affected_rows)


def test_gate_refuses_gap_without_bridging(tmp_path, monkeypatch):
    policy_path, _, first_hash, second_hash = _fixture(tmp_path, first_kwargs={"gap": True})
    monkeypatch.setattr(candidate, "EXPECTED_SOURCE_HASHES", {"sub-99": first_hash, "sub-1": second_hash})
    with pytest.raises(candidate.CandidateContractError, match="30-second dt"):
        gate.run(policy_path, tmp_path / "out")


def test_gate_keeps_rank_refusal_as_null(tmp_path, monkeypatch):
    policy_path, _, first_hash, second_hash = _fixture(tmp_path, first_kwargs={"rank_deficient_9d": True})
    monkeypatch.setattr(candidate, "EXPECTED_SOURCE_HASHES", {"sub-99": first_hash, "sub-1": second_hash})
    report = gate.run(policy_path, tmp_path / "out")
    row = next(row for row in report["rows"] if row["recording"] == "sub-99" and row["coordinate"] == "coords_9d" and row["estimator"] == "local_linear")
    assert row["scoped_status"] == "refused"
    assert row["refusal_class"] == "estimator_contract"
    assert row["predictions"] is None and row["n_predictions"] == 0


@pytest.mark.parametrize(
    "second_kwargs, needle",
    [
        ({"j9_invalid_attr": 2.2}, "invalid-window metadata"),
        ({"epochs_before": 804}, "shared time grid"),
        ({"epochs_retained": False}, "epochs_retained"),
        ({"drop_reason_value": 0.5}, "drop-reason"),
        ({"retained_nonfinite": False}, "retained nonfinite"),
        ({"finite_fraction": True}, "finite-row evidence"),
        ({"omit_3d_geometry": True}, "finite-row evidence"),
        ({"mnps3d_nonfinite": False}, "nonfinite rows"),
        ({"mnps3d_degenerate": True}, "degenerate"),
    ],
)
def test_gate_rejects_fractional_boolean_and_row_count_metadata(tmp_path, monkeypatch, second_kwargs, needle):
    policy_path, _, first_hash, second_hash = _fixture(tmp_path, second_kwargs=second_kwargs)
    monkeypatch.setattr(candidate, "EXPECTED_SOURCE_HASHES", {"sub-99": first_hash, "sub-1": second_hash})
    report = gate.run(policy_path, tmp_path / "out")
    rows = [row for row in report["rows"] if row["recording"] == "sub-1"]
    assert all(row["scoped_status"] == "refused" and row["predictions"] is None for row in rows)
    assert any(needle.split()[0] in (row["scoped_refusal_reason"] or "") for row in rows)


def test_gate_refuses_hash_mismatch_and_nonempty_overwrite(tmp_path, monkeypatch):
    policy_path, _, first_hash, second_hash = _fixture(tmp_path, wrong_hash=True)
    monkeypatch.setattr(candidate, "EXPECTED_SOURCE_HASHES", {"sub-99": first_hash, "sub-1": second_hash})
    with pytest.raises(candidate.CandidateContractError, match="hash"):
        gate.run(policy_path, tmp_path / "hash_out")
    good_policy, _, first_hash, second_hash = _fixture(tmp_path / "good")
    monkeypatch.setattr(candidate, "EXPECTED_SOURCE_HASHES", {"sub-99": first_hash, "sub-1": second_hash})
    output = tmp_path / "good" / "out"
    output.mkdir(parents=True)
    (output / "keep.json").write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError):
        gate.run(good_policy, output)
