"""Independent adversarial checks for analysis-side signal support ingestion.

The reader owns H5/schema/row validation.  These tests deliberately exercise
real temporary H5 files for that boundary and reserve monkeypatching for the
audit's orchestration/error and input-integrity paths.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nmd_analysis import signal_support_audit as audit_module
from nmd_analysis.signal_support_audit import audit_signal_support


def _source_record(raw_name: str = "raw.edf") -> dict[str, Any]:
    digest = "a" * 64
    return {
        "raw_file": raw_name,
        "schema": "mndm.signal_support_provenance.v1",
        "status": "completed",
        "source": {
            "path": f"K:/external/{raw_name}",
            "exists": True,
            "sha256": digest,
            "sha256_after": digest,
            "hash_stable": True,
        },
        "input_sfreq_hz": 256.0,
        "target_sfreq_hz": 250.0,
        "operations": [],
        "temporal_support": {"status": "unknown", "reason": "not certified"},
    }


def _extent(row_index: int = 0, *, raw_file: str = "raw.edf", support: str = "unknown") -> dict[str, Any]:
    return {
        "row_index": row_index,
        "epoch_id": row_index,
        "raw_file": raw_file,
        "nominal_time_start_sec": float(row_index * 30),
        "nominal_time_end_sec": float((row_index + 1) * 30),
        "original_sample_start": None,
        "original_sample_end": None,
        "sample_mapping_status": "unknown",
        "support_status": support,
        "support_reason": "effective support unknown",
        "source_identity": {"path": f"K:/external/{raw_file}", "sha256": "a" * 64},
        "source_clock": {"input_sfreq_hz": 256.0, "target_sfreq_hz": 250.0},
        "upstream_operation_ids": [],
    }


def _export_record(*, extents: list[dict[str, Any]] | None = None, schema: str = "mndm.signal_support_export.v1") -> dict[str, Any]:
    raw_file = "raw.edf"
    return {
        "schema": schema,
        "status": "recorded",
        "temporal_support_status": "unknown",
        "temporal_support_reason": "effective support is not certified",
        "per_epoch_input_extent": extents if extents is not None else [_extent(0), _extent(1)],
        "execution_records": [{
            "raw_file": raw_file,
            "validation_status": "valid",
            "validation_reason": None,
            "record": _source_record(raw_file),
        }],
        "source_quality_intervals": [],
        "source_quality_status": "not_recorded",
        "reference_fit_population": {"status": "unknown", "features": {}},
        "claim_status": "no_biological_claim",
    }


def _write_export_h5(path: Path, record: dict[str, Any], *, aliases: dict[str, Any] | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, "w") as handle:
        group = handle.create_group("provenance/signal_support_provenance")
        for key, value in record.items():
            if key in {"per_epoch_input_extent", "execution_records", "source_quality_intervals", "reference_fit_population"}:
                group.create_dataset(f"{key}_json", data=np.bytes_(json.dumps(value, allow_nan=False)))
            elif isinstance(value, str):
                group.create_dataset(key, data=np.bytes_(value))
            else:
                group.create_dataset(key, data=np.bytes_(json.dumps(value, allow_nan=False)))
        for key, value in (aliases or {}).items():
            group.create_dataset(key, data=np.bytes_(json.dumps(value, allow_nan=False)))
        rows = record.get("per_epoch_input_extent", [])
        handle.create_dataset("epoch_id", data=np.asarray([row["epoch_id"] for row in rows], dtype=np.int64))
        handle.create_dataset("window_start", data=np.asarray([row["nominal_time_start_sec"] for row in rows], dtype=np.float64))
        handle.create_dataset("window_end", data=np.asarray([row["nominal_time_end_sec"] for row in rows], dtype=np.float64))
        row_source = handle.create_group("row_source")
        row_source.create_dataset("raw_file", data=np.asarray([row["raw_file"].encode() for row in rows], dtype="S64"))
    return path


def _read_h5(path: Path) -> dict[str, Any]:
    from nmd_analysis.signal_support import read_signal_support

    result = read_signal_support(path)
    assert isinstance(result, dict)
    return result


def _assert_fail_closed(read_fn, *, path: Path) -> None:
    try:
        result = read_fn(path)
    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        return
    assert result.get("status") in {"malformed", "unsupported", "legacy_missing"}


def test_v1_reader_keeps_source_hash_recorded_only_and_support_unknown(tmp_path: Path) -> None:
    path = _write_export_h5(tmp_path / "v1.h5", _export_record())
    result = _read_h5(path)
    assert result["status"] == "recorded"
    assert result["source_hash_status"] == "recorded_only"
    assert result["row_alignment_status"] == "validated"
    assert result["temporal_support"]["status"] == "unknown"
    assert all(row["support_status"] == "unknown" for row in result["per_epoch_input_extent"])


def test_unknown_future_schema_cannot_become_recorded(tmp_path: Path) -> None:
    path = _write_export_h5(
        tmp_path / "future.h5",
        _export_record(schema="mndm.signal_support_export.v99"),
    )
    _assert_fail_closed(_read_h5, path=path)


def test_h5_plain_and_json_alias_collision_is_rejected(tmp_path: Path) -> None:
    path = _write_export_h5(
        tmp_path / "collision.h5",
        _export_record(),
        aliases={"per_epoch_input_extent": [_extent(99)]},
    )
    _assert_fail_closed(_read_h5, path=path)


def test_signal_support_dataset_instead_of_group_is_malformed(tmp_path: Path) -> None:
    path = tmp_path / "not_a_group.h5"
    with h5py.File(path, "w") as handle:
        handle.create_dataset("provenance/signal_support_provenance", data=np.bytes_("{}"))
    result = _read_h5(path)
    assert result["status"] == "malformed"
    assert result["temporal_support"]["status"] == "unknown"


def test_empty_recorded_export_is_malformed(tmp_path: Path) -> None:
    path = _write_export_h5(tmp_path / "empty.h5", _export_record(extents=[]))
    result = _read_h5(path)
    assert result["status"] == "malformed"
    assert result["temporal_support"]["status"] == "unknown"


def test_exact_finite_support_token_is_rejected(tmp_path: Path) -> None:
    path = _write_export_h5(tmp_path / "finite_support.h5", _export_record(extents=[_extent(0, support="exact_finite")]))
    result = _read_h5(path)
    assert result["status"] == "malformed"
    assert result["temporal_support"]["status"] == "unknown"


def test_nonfinite_json_value_is_rejected_or_unknown(tmp_path: Path) -> None:
    path = tmp_path / "nan.h5"
    record = _export_record()
    with h5py.File(path, "w") as handle:
        group = handle.create_group("provenance/signal_support_provenance")
        group.create_dataset("schema", data=np.bytes_(record["schema"]))
        group.create_dataset("status", data=np.bytes_("recorded"))
        group.create_dataset(
            "per_epoch_input_extent_json",
            data=np.bytes_(json.dumps([_extent(0) | {"nominal_time_start_sec": float("nan")}], allow_nan=True)),
        )
    _assert_fail_closed(_read_h5, path=path)


def test_duplicate_or_misaligned_extent_cannot_be_recorded(tmp_path: Path) -> None:
    duplicate = _write_export_h5(
        tmp_path / "duplicate.h5",
        _export_record(extents=[_extent(0), _extent(0)]),
    )
    _assert_fail_closed(_read_h5, path=duplicate)

    wrong_file = _write_export_h5(
        tmp_path / "wrong_file.h5",
        _export_record(extents=[_extent(0), _extent(1, raw_file="other.edf")]),
    )
    _assert_fail_closed(_read_h5, path=wrong_file)


def test_stage_label_or_exact_support_token_does_not_qualify_measurement(tmp_path: Path) -> None:
    path = _write_export_h5(
        tmp_path / "stage_match.h5",
        _export_record(extents=[_extent(0, support="exact")]),
    )
    result = _read_h5(path)
    assert result["status"] != "recorded" or result["temporal_support"]["status"] == "unknown"
    assert result.get("scientific_qualification") == "not_assessed"


def test_legacy_h5_is_explicitly_missing_support(tmp_path: Path) -> None:
    path = tmp_path / "legacy.h5"
    with h5py.File(path, "w") as handle:
        handle.create_dataset("mnps_3d", data=np.zeros((2, 3), dtype=np.float32))
    result = _read_h5(path)
    assert result["status"] == "legacy_missing"
    assert result["temporal_support"]["status"] == "unknown"
    assert result["scientific_qualification"] == "not_assessed"


def test_audit_reports_recorded_only_and_never_pools_subjects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first = tmp_path / "one.h5"
    second = tmp_path / "two.h5"
    first.write_bytes(b"one")
    second.write_bytes(b"two")
    monkeypatch.setattr(audit_module, "_read", lambda path: {
        "status": "recorded",
        "validation": {"status": "valid", "reasons": []},
        "source_hash_status": "recorded_only",
        "row_alignment_status": "aligned",
        "per_epoch_input_extent": [_extent(0)],
        "temporal_support": {"status": "unknown"},
        "execution_records": [],
        "reference_fit_population": {"status": "unknown"},
    })
    report = audit_signal_support([first, second], tmp_path / "audit")
    assert report["status"] == "audited"
    assert report["subject_pooling"] == "not_performed"
    assert len(report["sources"]) == 2
    assert all(source["source_hash_status"] == "recorded_only" for source in report["sources"])
    assert all(source["claim_status"] == "no_biological_claim" for source in report["sources"])


def test_audit_rejects_nonfinite_reader_payload_with_strict_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "nan_payload.h5"
    source.write_bytes(b"source")
    monkeypatch.setattr(audit_module, "_read", lambda path: {
        "status": "unknown",
        "per_epoch_input_extent": [{"nominal_time_start_sec": float("nan")}],
    })
    out = tmp_path / "audit_nan"
    with pytest.raises(RuntimeError):
        audit_signal_support([source], out)
    payload = json.loads((out / "signal_support_audit.json").read_text(encoding="utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    assert payload["status"] == "failed"


def test_audit_detects_input_mutation_between_hashes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "mutating.h5"
    source.write_bytes(b"source")
    monkeypatch.setattr(audit_module, "_read", lambda path: {"status": "unknown"})
    calls = iter(["a" * 64, "b" * 64, "c" * 64, "c" * 64, "c" * 64])
    monkeypatch.setattr(audit_module, "_sha256", lambda path: next(calls))
    with pytest.raises(RuntimeError, match="InputChanged"):
        audit_signal_support([source], tmp_path / "audit_changed")
