from __future__ import annotations

import json
from pathlib import Path

import pytest

import sleep_cohort_analysis as analysis


def _config(expected_count: int = 3) -> dict:
    return {
        "source": {
            "expected_subject_count": expected_count,
            "expected_subject_ids": {"prefix": "sub-", "numeric_min": 1, "numeric_max": expected_count},
        }
    }


def test_manifest_keeps_explicit_missing_h5_failure_and_coverage() -> None:
    entries = analysis._validate_entries(
        [
            {"subject": "sub-1", "recording": "sub-1", "h5": "one.h5", "pid": "89"},
            {"subject": "sub-2", "recording": "sub-2", "h5": None, "pid": "89", "failure_reason": "producer_failed"},
            {"subject": "sub-3", "recording": "sub-3", "h5": "three.h5", "pid": "1"},
        ],
        _config(),
    )
    assert len(entries) == 3
    assert entries[1]["h5"] is None
    assert entries[1]["manifest_failure_reason"] == "producer_failed"


def test_manifest_rejects_duplicate_recording_identity() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        analysis._validate_entries(
            [
                {"subject": "sub-1", "recording": "night", "h5": "one.h5", "pid": "89"},
                {"subject": "sub-1", "recording": "night", "h5": "two.h5", "pid": "89"},
            ],
            {"source": {"expected_subject_count": 2}},
        )


def test_repeated_nights_reduce_to_one_pid_before_cohort() -> None:
    recording_rows = []
    for recording_id, pid, value in (("sub-1", "89", 1.0), ("sub-2", "89", 9.0), ("sub-3", "1", 100.0)):
        recording_rows.append(
            {
                "recording_id": recording_id,
                "participant_id": pid,
                "family": "local_jacobian",
                "dimension": 3,
                "metric": "spectral_abscissa",
                "stage_key": "Wake",
                "median": value,
                "prior_development2": recording_id == "sub-1",
            }
        )
    participant_rows = analysis.participant_stage_summaries(recording_rows, ["89", "1"])
    selected = [row for row in participant_rows if row["stage_key"] == "Wake" and row["metric"] == "spectral_abscissa" and row["dimension"] == 3]
    by_pid = {row["participant_id"]: row for row in selected}
    assert by_pid["89"]["median"] == 5.0
    assert by_pid["89"]["recording_count"] == 2
    cohort = analysis.cohort_stage_summaries(participant_rows)
    result = next(row for row in cohort if row["stage_key"] == "Wake" and row["metric"] == "spectral_abscissa" and row["dimension"] == 3)
    assert result["n_participants"] == 2
    assert result["median"] == 52.5


def test_repeated_night_contrasts_reduce_to_one_pid() -> None:
    rows = []
    for recording_id, value in (("sub-1", 1.0), ("sub-2", 9.0), ("sub-3", 100.0)):
        rows.append({"recording_id": recording_id, "participant_id": "89" if recording_id != "sub-3" else "1", "family": "local_jacobian", "dimension": 3, "metric": "spectral_abscissa", "n2_minus_wake_median": value, "prior_development2": recording_id == "sub-1"})
    participant_rows = analysis.participant_contrasts(rows, ["89", "1"])
    selected = next(row for row in participant_rows if row["metric"] == "spectral_abscissa" and row["dimension"] == 3)
    assert selected["participant_id"] == "1" or selected["participant_id"] == "89"
    pid89 = next(row for row in participant_rows if row["participant_id"] == "89" and row["metric"] == "spectral_abscissa")
    assert pid89["n2_minus_wake_median"] == 5.0
    cohort = analysis.cohort_contrasts(participant_rows)
    result = next(row for row in cohort if row["metric"] == "spectral_abscissa" and row["dimension"] == 3)
    assert result["n_participants"] == 2
    assert result["median"] == 52.5


def test_prior_development_flag_uses_unsupported_recording_rows() -> None:
    stage_rows = [
        {
            "recording_id": "sub-1",
            "participant_id": "89",
            "family": "local_jacobian",
            "dimension": 3,
            "metric": "spectral_abscissa",
            "stage_key": "Wake",
            "median": None,
            "prior_development2": True,
        },
        {
            "recording_id": "sub-2",
            "participant_id": "89",
            "family": "local_jacobian",
            "dimension": 3,
            "metric": "spectral_abscissa",
            "stage_key": "Wake",
            "median": 4.0,
            "prior_development2": False,
        },
    ]
    stage = next(
        row
        for row in analysis.participant_stage_summaries(stage_rows, ["89"])
        if row["family"] == "local_jacobian"
        and row["dimension"] == 3
        and row["metric"] == "spectral_abscissa"
        and row["stage_key"] == "Wake"
    )
    assert stage["prior_development2"] is True
    assert stage["recording_count"] == 1
    assert stage["median"] == 4.0

    contrast_rows = [
        {
            "recording_id": "sub-1",
            "participant_id": "89",
            "family": "local_jacobian",
            "dimension": 3,
            "metric": "spectral_abscissa",
            "n2_minus_wake_median": None,
            "prior_development2": True,
        },
        {
            "recording_id": "sub-2",
            "participant_id": "89",
            "family": "local_jacobian",
            "dimension": 3,
            "metric": "spectral_abscissa",
            "n2_minus_wake_median": 2.0,
            "prior_development2": False,
        },
    ]
    contrast = next(
        row
        for row in analysis.participant_contrasts(contrast_rows, ["89"])
        if row["family"] == "local_jacobian"
        and row["dimension"] == 3
        and row["metric"] == "spectral_abscissa"
    )
    assert contrast["prior_development2"] is True
    assert contrast["recording_count"] == 1
    assert contrast["n2_minus_wake_median"] == 2.0


def test_participant_tables_bind_recording_id_to_pid(tmp_path: Path) -> None:
    tsv = tmp_path / "participants.tsv"
    tsv.write_text("participant_id\tpid\nsub-1\t89\nsub-2\t89\n", encoding="utf-8")
    metadata = tmp_path / "participants.json"
    metadata.write_text(json.dumps({"participant_id": {}, "pid": {}}), encoding="utf-8")
    cfg = {"source": {"participant_tables": {"tsv": {"path": str(tsv)}, "json": {"path": str(metadata)}}}}
    rows, provenance = analysis._participant_tables(cfg)
    assert rows["sub-1"]["participant_id"] == "89"
    assert provenance["recording_rows"] == 2
    assert provenance["unique_participants"] == 1


def test_mixed_fixture_run_preserves_computed_and_failure_denominators(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    h5 = tmp_path / "sub-1.h5"
    import h5py
    import numpy as np

    with h5py.File(h5, "w") as handle:
        handle.create_dataset("time", data=np.array([15.0, 45.0, 75.0]))
        handle.create_dataset("window_start", data=np.array([0.0, 30.0, 60.0]))
        handle.create_dataset("window_end", data=np.array([30.0, 60.0, 90.0]))
        handle.create_dataset("epoch_id", data=np.array([0, 1, 2]))
        handle.attrs["coverage_seconds_measured"] = 90.0
        handle.attrs["epochs_raw"] = 3
        handle.attrs["dt_sec_epoch_config"] = 30.0
    tsv = tmp_path / "participants.tsv"
    tsv.write_text("participant_id\tpid\nsub-1\t89\nsub-2\t89\nsub-3\t1\n", encoding="utf-8")
    metadata = tmp_path / "participants.json"
    metadata.write_text(json.dumps({"participant_id": {}, "pid": {}}), encoding="utf-8")

    def fake_reader(path: Path, recording: str):
        return [
            {"recording": recording, "family": "local_jacobian", "dimension": 3, "metric": "spectral_abscissa", "stage_key": "Wake", "value": 1.0, "finite": True, "producer_finite_ok": True, "producer_valid_flag": True, "used": True},
            {"recording": recording, "family": "local_jacobian", "dimension": 3, "metric": "spectral_abscissa", "stage_key": "N2", "value": 3.0, "finite": True, "producer_finite_ok": True, "producer_valid_flag": True, "used": True},
        ], {"availability": {"E1_3D": {"available": True}}}

    monkeypatch.setattr(analysis.e1e2, "endpoint_rows_for_recording", fake_reader)
    config_file = Path(__file__).resolve().parents[1] / "config" / "sleep_cohort_analysis_20260912.json"
    config = json.loads(config_file.read_text(encoding="utf-8"))
    config["source"].update(
        {
            "manifest_path": str(tmp_path / "manifest.json"),
            "ingest_inventory_path": "",
            "ingest_execution_manifest_path": "",
            "participant_tables": {"tsv": {"path": str(tsv)}, "json": {"path": str(metadata)}},
            "expected_subject_count": 3,
            "expected_unique_participant_count": 2,
            "expected_subject_ids": {"prefix": "sub-", "numeric_min": 1, "numeric_max": 3},
        }
    )
    manifest_path = Path(config["source"]["manifest_path"])
    manifest_path.write_text(
        json.dumps(
            {
                "continuous_fullnight": True,
                "recordings": [
                    {"recording_id": "sub-1", "h5_path": str(h5), "h5_sha256": analysis.sha256(h5)},
                    {"recording_id": "sub-2", "h5_path": None, "failure_reason": "producer_failed"},
                    {"recording_id": "sub-3", "h5_path": str(h5), "h5_sha256": "0" * 64},
                ],
            }
        ),
        encoding="utf-8",
    )
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    output = tmp_path / "out"
    result = analysis.run(config_path, output)
    assert result["recording_count"] == 3
    assert result["source_count_ok"] == 1
    outcomes = json.loads((output / "source_outcomes.json").read_text(encoding="utf-8"))
    assert [row["status"] for row in outcomes] == ["ok", "failed", "failed"]
    assert outcomes[1]["failure_reason"] == "producer_failed"
    assert outcomes[2]["failure_reason"] == "h5_hash_mismatch"
    participant = json.loads((output / "participant_stage_summaries.json").read_text(encoding="utf-8"))
    row = next(item for item in participant if item["participant_id"] == "89" and item["dimension"] == 3 and item["metric"] == "spectral_abscissa" and item["stage_key"] == "Wake")
    assert row["median"] == 1.0

    def fail_inventory(_: Path):
        raise RuntimeError("inventory_failure")

    monkeypatch.setattr(analysis, "_surface_inventory", fail_inventory)
    output_failed = tmp_path / "out_inventory_failure"
    result_failed = analysis.run(config_path, output_failed)
    assert result_failed["source_count_ok"] == 0
    assert json.loads((output_failed / "endpoint_rows.json").read_text(encoding="utf-8")) == []
    failed_summaries = json.loads((output_failed / "recording_stage_summaries.json").read_text(encoding="utf-8"))
    assert all(item["source_status"] == "failed" for item in failed_summaries)
