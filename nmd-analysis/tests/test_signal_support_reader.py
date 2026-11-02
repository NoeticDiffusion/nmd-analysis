from __future__ import annotations

import json
from pathlib import Path

import h5py
import numpy as np

from nmd_analysis.signal_support import read_signal_support


REAL_H5 = Path(
    r"H:\SourceRepo2\NeuralManifoldDynamics\project\v3\signal_support_20260910\pipeline_final_r3\ds005555\neuralmanifolddynamics_ds005555_20260910_093247\sub-99_Sleep_acq-psg\sub-99_Sleep_acq-psg.h5"
)


def test_final_r3_reader_preserves_unknown_support_and_rows() -> None:
    result = read_signal_support(REAL_H5)
    assert result["status"] == "recorded"
    assert result["source_hash_status"] == "recorded_only"
    assert result["row_alignment_status"] == "validated"
    assert result["temporal_support"]["status"] == "unknown"
    assert result["scientific_qualification"] == "not_assessed"
    assert len(result["per_epoch_input_extent"]) == 30
    assert len(result["source_quality_intervals"]) == 9
    assert all(row["support_status"] == "unknown" for row in result["per_epoch_input_extent"])


def test_missing_group_is_explicit_unknown(tmp_path: Path) -> None:
    path = tmp_path / "legacy.h5"
    with h5py.File(path, "w") as handle:
        handle.create_dataset("epoch_id", data=np.arange(2, dtype=np.int64))
    result = read_signal_support(path)
    assert result["status"] == "legacy_missing"
    assert "signal_support_group_missing" in result["validation"]["reasons"]
    assert result["scientific_qualification"] == "not_assessed"


def _write_minimal_export(path: Path, *, support_status: str = "unknown", end: float = 10.0) -> None:
    record = {
        "raw_file": "raw.edf",
        "schema": "mndm.signal_support_provenance.v1",
        "status": "completed",
        "source": {
            "path": "raw.edf",
            "sha256": "a" * 64,
            "sha256_after": "a" * 64,
            "hash_stable": True,
        },
        "operations": [],
    }
    rows = [{
        "row_index": 0,
        "epoch_id": 0,
        "raw_file": "raw.edf",
        "nominal_time_start_sec": 0.0,
        "nominal_time_end_sec": end,
        "support_status": support_status,
    }]
    with h5py.File(path, "w") as handle:
        handle.create_dataset("epoch_id", data=np.array([0], dtype=np.int64))
        handle.create_dataset("window_start", data=np.array([0.0], dtype=np.float32))
        handle.create_dataset("window_end", data=np.array([10.0], dtype=np.float32))
        handle.create_dataset("row_source/raw_file", data=np.asarray(["raw.edf"], dtype=h5py.string_dtype()))
        group = handle.create_group("provenance/signal_support_provenance")
        group.create_dataset("schema", data="mndm.signal_support_export.v1")
        group.create_dataset("status", data="recorded")
        group.create_dataset("temporal_support_status", data="unknown")
        group.create_dataset("temporal_support_reason", data="unknown")
        group.create_dataset("execution_records_json", data=json.dumps([{"record": record}]))
        group.create_dataset("per_epoch_input_extent_json", data=json.dumps(rows))
        group.create_dataset("source_quality_intervals_json", data="[]")


def test_positive_finite_support_and_row_mismatch_never_qualify(tmp_path: Path) -> None:
    forged = tmp_path / "forged.h5"
    _write_minimal_export(forged, support_status="finite")
    result = read_signal_support(forged)
    assert result["status"] == "malformed"
    assert any(reason.startswith("finite_or_unsupported_support_status") for reason in result["validation"]["reasons"])

    mismatched = tmp_path / "mismatched.h5"
    _write_minimal_export(mismatched, end=11.0)
    result = read_signal_support(mismatched)
    assert result["status"] == "malformed"
    assert "nominal_time_end_sec_mismatch:0" in result["validation"]["reasons"]
