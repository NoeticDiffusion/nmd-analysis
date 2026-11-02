from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from nmd_analysis.continuous_full_surface_replay_validation import (
    _is_canonical_psg_source,
    _normalized_qc,
    _verify_auxiliary_support_artifacts,
    validate_full_surface_replay,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, content: bytes | str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
    return path


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path, dict[str, object]]:
    reference = tmp_path / "reference"
    replay = tmp_path / "replay"
    source_edf_name = "sub-01_task-sleep_acq-psg_eeg.edf"
    recording_name = "sub-01_task-Sleep_acq-psg_eeg.edf"
    qc_filename = "sub-01_task-Sleep_acq-psg_eeg_qc_artifacts.json"
    feature_bytes = b"epoch,value\n0,1.0\n1,2.0\n"
    parquet_bytes = b"synthetic parquet bytes"
    for root in (reference, replay):
        _write(root / "features.csv", feature_bytes)
        _write(root / "features.parquet", parquet_bytes)

    reference_qc = {
        "contract": {"version": 3, "valid": True},
        "timings": {"elapsed_sec": 12.0},
        "worker_rss_gb_peak": 1.2,
        "started_at_utc": "2026-09-30T00:00:00Z",
        "nested": {"finished_at_utc": "2026-09-30T00:01:00Z", "stable": [1, 2]},
    }
    replay_qc = {
        "contract": {"version": 3, "valid": True},
        "timings": {"elapsed_sec": 9.0},
        "worker_rss_gb_peak": 2.1,
        "started_at_utc": "2026-09-30T01:00:00Z",
        "nested": {"finished_at_utc": "2026-09-30T01:01:00Z", "stable": [1, 2]},
    }
    _write(reference / "qc_artifacts" / qc_filename, json.dumps(reference_qc))
    replay_qc_path = _write(replay / "qc_artifacts" / qc_filename, json.dumps(replay_qc))

    participants = _write(tmp_path / "participants.tsv", "participant_id\nsub-01\n")
    protocol = _write(tmp_path / "protocol.md", "frozen protocol\n")
    config = _write(tmp_path / "config.yaml", "summarize_forbidden: true\n")
    audit_code = _write(tmp_path / "audit.py", "# fixture audit code\n")
    event = _write(tmp_path / "events.tsv", "onset\tduration\tstage\n0\t30\tWake\n")
    source_root = tmp_path / "source"
    source_root.mkdir()
    raw_source = _write(source_root / source_edf_name, b"synthetic raw source bytes")
    _write(source_root / "sub-01_task-Sleep_acq-headband_eeg.edf", b"non-PSG source file")
    audit_output = tmp_path / "support_audit"
    audit_output.mkdir()
    generated = _write(audit_output / "row_support.csv", "recording,rows\nsub-01,2\n")
    audit_path = _write(audit_output / "validation.json", "{}")

    paths: dict[str, object] = {
        "features_table": str((replay / "features.csv").resolve()),
        "participants_tsv": str(participants.resolve()),
        "protocol": str(protocol.resolve()),
        "mndm_config": str(config.resolve()),
        "audit_code": str(audit_code.resolve()),
        "qc_dir": str((replay / "qc_artifacts").resolve()),
        "source_root": str(source_root.resolve()),
        "events": {"sub-01": str(event.resolve())},
        "qc_sidecars": {recording_name: str(replay_qc_path.resolve())},
        "raw_sources": {source_edf_name: str(raw_source.resolve())},
    }
    hashes = {
        "features_table": _sha(replay / "features.csv"),
        "participants_tsv": _sha(participants),
        "protocol": _sha(protocol),
        "mndm_config": _sha(config),
        "audit_code": _sha(audit_code),
        "events:sub-01": _sha(event),
        f"qc_sidecar:{recording_name}": _sha(replay_qc_path),
        f"raw_source:{source_edf_name.lower()}": _sha(raw_source),
    }
    report: dict[str, object] = {
        "schema": "nmd_analysis.continuous_full_surface_audit.v1",
        "status": "PARTIAL_PASS_SOURCE_SUPPORT_ONLY",
        "charts_generated": False,
        "outcomes_calculated": False,
        "C1_C3_scores_opened": False,
        "full_cohort_scoring_authorized": False,
        "surface_replay_status": "PENDING_FULL_COHORT_REPLAY",
        "counts": {"feature_rows": 2, "recordings": 1},
        "input_paths": paths,
        "input_hashes_before": hashes,
        "input_hashes_after": dict(hashes),
        "output_sha256": {"row_support.csv": _sha(generated)},
        "output_hash_scope": "all generated audit files present before validation.json is written; validation.json is excluded to avoid a self-referential hash",
    }
    audit_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return reference, replay, audit_path, audit_output, report


def _aux_support_fixtures(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    support_map_dir = tmp_path / "support_map"
    stage_support_dir = tmp_path / "stage_support"
    parquet = _write(support_map_dir / "all_fold_support.parquet", b"support map")
    map_payload = {
        "verdict": "PARTIAL_PASS_ALL_FOLD_APPLY_SUPPORT_CROSSWALK",
        "biological_claim_authorized": False,
        "contrasts_computed": False,
        "label_join_performed": False,
        "stage_horizon_intersection_computed": False,
        "output_parquet": str(parquet.resolve()),
        "output_parquet_sha256": _sha(parquet),
        "row_count": 2,
        "recording_count": 1,
    }
    map_validation = _write(
        support_map_dir / "validation.json", json.dumps(map_payload, indent=2)
    )

    stage_csv = _write(stage_support_dir / "stage_support.csv", "stage,count\nN2,1\n")
    stage_payload = {
        "verdict": "PARTIAL_PASS_STAGE_HORIZON_SUPPORT_ONLY",
        "outcomes_calculated": False,
        "matching_performed": False,
        "C1_C2_C3_scores_opened": False,
        "biological_claim_authorized": False,
        "full_surface_replay_gate": "NOT_ASSESSED_BY_THIS_AUDIT",
        "full_cohort_protocol_authorization": "NOT_GRANTED",
        "outputs": {"stage_support": stage_csv.name},
        "output_sha256": {"stage_support": _sha(stage_csv)},
    }
    stage_validation = _write(
        stage_support_dir / "validation.json", json.dumps(stage_payload, indent=2)
    )
    return map_validation, stage_validation, parquet, stage_csv


def test_run_only_qc_normalization_is_narrow_and_recursive():
    reference = {
        "stable": {"value": 7, "finished_at_utc": "old"},
        "timings": {"elapsed_sec": 1},
        "worker_rss_gb_peak": 1.0,
    }
    replay = {
        "stable": {"value": 7, "finished_at_utc": "new"},
        "timings": {"elapsed_sec": 99},
        "worker_rss_gb_peak": 4.0,
    }
    assert _normalized_qc(reference) == _normalized_qc(replay)
    changed_contract = {**replay, "new_contract_field": "different"}
    assert _normalized_qc(reference) != _normalized_qc(changed_contract)


def test_canonical_psg_filename_selection_is_case_insensitive_and_excludes_headband():
    assert _is_canonical_psg_source(Path("sub-01_task-sleep_acq-psg_eeg.edf"))
    assert _is_canonical_psg_source(Path("sub-01_TASK-SLEEP_ACQ-PSG_EEG.EDF"))
    assert not _is_canonical_psg_source(Path("sub-01_task-Sleep_acq-headband_eeg.edf"))


def test_exact_feature_replay_and_semantic_qc_replay_are_support_only(tmp_path: Path):
    reference, replay, audit_path, _, _ = _fixture(tmp_path)
    output = tmp_path / "replay_validation"
    report = validate_full_surface_replay(reference, replay, audit_path, output)

    assert report["status"] == "PASS_DETERMINISTIC_FEATURE_REPLAY"
    assert report["feature_rows"] == 2
    assert report["recordings"] == report["qc_sidecar_count"] == 1
    assert report["charts_generated"] is False
    assert report["outcomes_calculated"] is False
    assert report["full_cohort_scoring_authorized"] is False
    assert report["gate_8_status"].startswith("NOT_OPEN")
    assert len(report["audit_binding"]["raw_source_sha256_current_verified"]) == 1
    saved = json.loads((output / "validation.json").read_text(encoding="utf-8"))
    assert saved["feature_hashes"]["reference_csv_sha256"] == saved["feature_hashes"]["replay_csv_sha256"]


def test_feature_hash_mismatch_fails_closed_without_output(tmp_path: Path):
    reference, replay, audit_path, _, _ = _fixture(tmp_path)
    (replay / "features.csv").write_text("epoch,value\n0,999\n", encoding="utf-8")
    output = tmp_path / "replay_validation"
    with pytest.raises(ValueError, match="hash|byte-identical"):
        validate_full_surface_replay(reference, replay, audit_path, output)
    assert not output.exists()


def test_unknown_qc_field_difference_is_not_normalized_away(tmp_path: Path):
    reference, replay, audit_path, _, report = _fixture(tmp_path)
    recording = "sub-01_task-Sleep_acq-psg_eeg.edf"
    qc_path = replay / "qc_artifacts" / "sub-01_task-Sleep_acq-psg_eeg_qc_artifacts.json"
    qc_value = json.loads(qc_path.read_text(encoding="utf-8"))
    qc_value["new_contract_field"] = "changed"
    qc_path.write_text(json.dumps(qc_value), encoding="utf-8")
    new_hash = _sha(qc_path)
    report["input_hashes_before"][f"qc_sidecar:{recording}"] = new_hash  # type: ignore[index]
    report["input_hashes_after"][f"qc_sidecar:{recording}"] = new_hash  # type: ignore[index]
    audit_path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError, match="QC semantic mismatch"):
        validate_full_surface_replay(reference, replay, audit_path, tmp_path / "replay_validation")


def test_nonempty_failed_files_blocks_replay_pass(tmp_path: Path):
    reference, replay, audit_path, _, _ = _fixture(tmp_path)
    (replay / "failed_files.txt").write_text("sub-01_task-Sleep_acq-psg_eeg.edf\n", encoding="utf-8")
    with pytest.raises(ValueError, match="failed-file"):
        validate_full_surface_replay(reference, replay, audit_path, tmp_path / "replay_validation")


def test_raw_source_mutation_after_audit_fails_closed(tmp_path: Path):
    reference, replay, audit_path, _, _ = _fixture(tmp_path)
    raw_source = tmp_path / "source" / "sub-01_task-sleep_acq-psg_eeg.edf"
    raw_source.write_bytes(b"changed raw source bytes")
    with pytest.raises(ValueError, match="Raw source.*SHA-256 changed"):
        validate_full_surface_replay(reference, replay, audit_path, tmp_path / "replay_validation")


def test_unmanifested_canonical_raw_source_fails_closed(tmp_path: Path):
    reference, replay, audit_path, _, _ = _fixture(tmp_path)
    _write(
        tmp_path / "source" / "sub-02_task-Sleep_acq-psg_eeg.edf",
        b"unexpected canonical PSG source",
    )
    with pytest.raises(ValueError, match="Raw-source inventory differs"):
        validate_full_surface_replay(reference, replay, audit_path, tmp_path / "replay_validation")


def test_audit_qc_path_must_reside_in_replay_inventory(tmp_path: Path):
    reference, replay, audit_path, _, report = _fixture(tmp_path)
    recording = "sub-01_task-Sleep_acq-psg_eeg.edf"
    report["input_paths"]["qc_sidecars"][recording] = str(  # type: ignore[index]
        (reference / "qc_artifacts" / "sub-01_task-Sleep_acq-psg_eeg_qc_artifacts.json").resolve()
    )
    audit_path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="outside the replay QC inventory"):
        validate_full_surface_replay(reference, replay, audit_path, tmp_path / "replay_validation")


def test_stale_support_audit_output_hash_fails_closed(tmp_path: Path):
    reference, replay, audit_path, audit_output, _ = _fixture(tmp_path)
    (audit_output / "row_support.csv").write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ValueError, match="output inventory mismatch"):
        validate_full_surface_replay(reference, replay, audit_path, tmp_path / "replay_validation")


def test_auxiliary_support_artifacts_verify_declared_outputs_and_closed_flags(tmp_path: Path):
    map_validation, stage_validation, _, _ = _aux_support_fixtures(tmp_path)
    result = _verify_auxiliary_support_artifacts(map_validation, stage_validation)
    assert result["all_fold_apply_support_map"]["verdict"] == "PARTIAL_PASS_ALL_FOLD_APPLY_SUPPORT_CROSSWALK"
    assert result["all_fold_stage_horizon_support"]["verdict"] == "PARTIAL_PASS_STAGE_HORIZON_SUPPORT_ONLY"


def test_tampered_support_map_gate_flag_fails_closed(tmp_path: Path):
    map_validation, _, _, _ = _aux_support_fixtures(tmp_path)
    payload = json.loads(map_validation.read_text(encoding="utf-8"))
    payload["biological_claim_authorized"] = True
    map_validation.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="biological_claim_authorized=false"):
        _verify_auxiliary_support_artifacts(map_validation, None)


def test_tampered_support_map_parquet_fails_closed(tmp_path: Path):
    map_validation, _, parquet, _ = _aux_support_fixtures(tmp_path)
    parquet.write_bytes(b"tampered support map")
    with pytest.raises(ValueError, match="path/hash does not bind"):
        _verify_auxiliary_support_artifacts(map_validation, None)


def test_support_map_declared_path_must_resolve_to_its_output_directory(tmp_path: Path):
    map_validation, _, parquet, _ = _aux_support_fixtures(tmp_path)
    external = _write(tmp_path / "external" / parquet.name, parquet.read_bytes())
    payload = json.loads(map_validation.read_text(encoding="utf-8"))
    payload["output_parquet"] = str(external.resolve())
    map_validation.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="path/hash does not bind"):
        _verify_auxiliary_support_artifacts(map_validation, None)


def test_tampered_stage_support_outcome_flag_fails_closed(tmp_path: Path):
    _, stage_validation, _, _ = _aux_support_fixtures(tmp_path)
    payload = json.loads(stage_validation.read_text(encoding="utf-8"))
    payload["outcomes_calculated"] = True
    stage_validation.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="outcomes_calculated=false"):
        _verify_auxiliary_support_artifacts(None, stage_validation)


def test_tampered_stage_support_output_hash_fails_closed(tmp_path: Path):
    _, stage_validation, _, stage_csv = _aux_support_fixtures(tmp_path)
    stage_csv.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ValueError, match="output files do not match"):
        _verify_auxiliary_support_artifacts(None, stage_validation)


def test_stage_support_manifest_rejects_output_path_traversal(tmp_path: Path):
    _, stage_validation, _, _ = _aux_support_fixtures(tmp_path)
    payload = json.loads(stage_validation.read_text(encoding="utf-8"))
    payload["outputs"]["stage_support"] = "../stage_support.csv"
    stage_validation.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid paths or hashes"):
        _verify_auxiliary_support_artifacts(None, stage_validation)
