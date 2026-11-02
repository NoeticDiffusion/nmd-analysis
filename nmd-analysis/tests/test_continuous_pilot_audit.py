from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nmd_analysis.continuous_pilot_audit import audit_continuous_pilot as _audit_continuous_pilot


def _test_freeze_manifest(root: Path, qc_dir: Path, events: dict[str, Path]) -> Path:
    audit_source = Path(_audit_continuous_pilot.__code__.co_filename).resolve()
    inputs = []

    def add(role: str, path: Path) -> None:
        path = path.resolve()
        inputs.append({
            "role": role,
            "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })

    def add_stub(role: str, relative_path: str) -> None:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"synthetic frozen input: {relative_path}\n", encoding="utf-8")
        add(role, path)

    add_stub("protocol", "articles/BOAS_sleep_dataset_ndt._v.1.0/preregistration_continuous_C123_20260929.md")
    config_dir = Path("NeuralManifoldDynamics/mndm/config/sources/openneuro")
    add_stub("pilot_config", str(config_dir / "config_ingest_ds005555_continuous_c123_prediction_safe_pilot_20260929.yaml"))
    config_names = (
        "config_ingest_ds005555_continuous_c123_cautious_gap_safe_final.yaml",
        "config_ingest_ds005555_continuous_c123_cautious_gap_safe.yaml",
        "config_ingest_ds005555_continuous_c123_cautious_gap_isolated.yaml",
        "config_ingest_ds005555_continuous_c123_cautious_qc.yaml",
        "config_ingest_ds005555_continuous_c123_safe_gap.yaml",
        "config_ingest_ds005555_continuous_c123.yaml",
        "config_ingest_ds005555.yaml",
    )
    for name in config_names:
        add_stub("mndm_config", str(config_dir / name))
    add_stub("mndm_config", "NeuralManifoldDynamics/mndm/config/config_ingest_common_eeg.yaml")
    code_suffixes = (
        "mndm/src/mndm/parallel.py",
        "mndm/src/mndm/preprocess.py",
        "mndm/src/mndm/signal_support_provenance.py",
        "mndm/src/mndm/features/ppg.py",
        "mndm/src/mndm/features/eeg.py",
        "mndm/src/mndm/pipeline/signal_support_export.py",
        "mndm/src/mndm/orchestrate.py",
        "mndm/src/mndm/cli.py",
        "mndm/src/mndm/__about__.py",
        "core/src/core/config_loader.py",
        "requirements.txt",
        "mndm/tests/test_ds005555_continuous_pilot_config.py",
        "mndm/tests/test_preprocess_modalities.py",
        "mndm/tests/test_signal_support_export.py",
        "mndm/tests/test_signal_support_preprocess.py",
    )
    for suffix in code_suffixes:
        add_stub("mndm_code", f"NeuralManifoldDynamics/{suffix}")
    add("analysis_audit", audit_source)
    for subject, event_path in events.items():
        add("events", event_path)
        sidecar = qc_dir / f"{event_path.name.removesuffix('_events.tsv')}_eeg_qc_artifacts.json"
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        add("source_edf", Path(payload["signal_support_provenance"]["source"]["path"]))
    manifest_path = root / "freeze_manifest.json"
    manifest_path.write_text(json.dumps({
        "schema": "nmd_analysis.continuous_pilot_freeze_manifest.v1",
        "protocol_version": "synthetic-test",
        "inputs": inputs,
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def audit_continuous_pilot(features_table, qc_dir, events_by_subject, output_dir, *, replay_reference=None, window_sec=30.0):
    manifest = _test_freeze_manifest(Path(features_table).resolve().parent, Path(qc_dir), dict(events_by_subject))
    return _audit_continuous_pilot(
        features_table,
        qc_dir,
        events_by_subject,
        output_dir,
        freeze_manifest=manifest,
        replay_reference=replay_reference,
        window_sec=window_sec,
    )


def _fixture(root: Path, *, invalidate_epoch: int | None = None):
    qc_dir = root / "qc_artifacts"
    qc_dir.mkdir(parents=True)
    events_by_subject = {}
    feature_rows = []
    for subject in ("sub-100", "sub-105"):
        raw_name = f"{subject}_task-Sleep_acq-psg_eeg.edf"
        raw = root / "ExternalReceivedDatasets" / "openneuro" / "received" / "ds005555" / subject / "eeg" / raw_name
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(f"synthetic EDF {subject}".encode())
        digest = hashlib.sha256(raw.read_bytes()).hexdigest()
        sidecar = {
            "signal_support_provenance": {
                "schema": "mndm.signal_support_provenance.v1",
                "status": "completed",
                "source": {
                    "path": str(raw), "exists": True, "sha256": digest,
                    "sha256_after": digest, "hash_stable": True,
                },
                "temporal_support_mode": "causal_finite",
                "input_sfreq_hz": 256.0,
                "target_sfreq_hz": 256.0,
                "channel_types_after_dataset_typing": {"F3": "eeg", "F4": "eeg", "PSG_PULSE": "misc"},
                "temporal_support": {"status": "finite_causal"},
                "effective_time_support": {
                    "status": "finite_causal",
                    "mode": "causal_finite_edf_identity_grid",
                    "resampler": {
                        "method": "identity_sample_grid", "phase": "identity",
                        "up": 1, "down": 1, "tap_count": 1,
                        "output_sample_count": 256 * 180,
                    },
                    "eeg_bandpass": {
                        "method": "mne.filter.filter_data_fir", "phase": "minimum",
                        "pad": "constant", "tap_count": 11, "sfreq_hz": 256.0,
                        "support_interpretation": "output k depends on input [max(0,k-tap_count+1),k]",
                    },
                },
                "edf_sample_grid": {
                    "continuity_status": "verified_continuous", "continuity_marker": "EDF",
                    "continuity_verification": "EDF+D rejected; EDF/EDF+C record grid checked; no BAD_ACQ_SKIP, BAD boundary, or EDGE boundary annotations",
                    "boundary_annotation_check": {
                        "status": "verified_absent",
                        "rejected_prefixes": ["BAD_ACQ_SKIP", "BAD BOUNDARY", "EDGE"],
                    },
                    "channel_count": 3,
                    "samples_per_record_by_channel": [256, 256, 256],
                    "sample_rate_hz": 256.0, "sample_count": 256 * 180,
                    "records": 180, "samples_per_record": 256,
                    "record_duration_seconds": 1.0,
                },
                "ppg_source_selection": {
                    "rule": "source_channel_name_regex",
                    "channel_names": ["PSG_PULSE"],
                    "channel_types_after_dataset_typing": ["misc"],
                },
                "ppg_feature_contract": {
                    "estimator": "window_local_present_only_v1",
                    "information_scope": "present_only_within_[t_start,t_end)",
                    "source_channels": ["PSG_PULSE"],
                    "source_channel_types_after_dataset_typing": {"PSG_PULSE": "misc"},
                },
                "source_quality_intervals": {"status": "none_observed", "intervals": []},
            }
        }
        (qc_dir / f"{Path(raw_name).stem}_qc_artifacts.json").write_text(json.dumps(sidecar), encoding="utf-8")
        event_path = root / "ExternalReceivedDatasets" / "openneuro" / "received" / "ds005555" / subject / "eeg" / f"{subject}_task-Sleep_acq-psg_events.tsv"
        pd.DataFrame({
            "onset": [0.0, 90.0], "duration": [90.0, 90.0], "stage_hum": [0, 2],
        }).to_csv(event_path, sep="\t", index=False)
        events_by_subject[subject] = event_path
        for epoch in range(6):
            start, end = epoch * 30.0, (epoch + 1) * 30.0
            nominal_start, nominal_end = int(start * 256), int(end * 256)
            actual_start = max(0, nominal_start - 10)
            row = {
                "file": raw_name,
                "epoch_id": epoch,
                "t_start": start,
                "t_end": end,
                "ppg_rate_bpm": 60.0 + epoch,
                "qc_ok_ppg": True,
                "qc_ok_eeg": True,
                "source_sample_mapping_status": "nominal_bounds_mapped",
                "nominal_source_sample_start": nominal_start,
                "nominal_source_sample_end_exclusive": nominal_end,
                "nominal_source_time_start_sec": start,
                "nominal_source_time_end_sec": end,
                "actual_sample_contributors_status": "finite_causal_conservative_bound",
                "actual_source_sample_start": actual_start,
                "actual_source_sample_end_exclusive": nominal_end,
                "actual_source_time_start_sec": actual_start / 256,
                "actual_source_time_end_sec": end,
                "source_sfreq_hz": 256.0,
                "input_sample_finite_status": "all_finite",
                "input_sample_gap_count": 0,
                "eeg_alpha": 1.0 + epoch,
            }
            if invalidate_epoch == epoch:
                row["actual_sample_contributors_status"] = "unknown"
            feature_rows.append(row)
    features = root / "features.csv"
    pd.DataFrame(feature_rows).to_csv(features, index=False)
    return features, qc_dir, events_by_subject


def test_measurement_pilot_audit_is_chart_free_and_checks_source_stage_and_pairs(tmp_path):
    features, qc_dir, events = _fixture(tmp_path)
    output = tmp_path / "audit"
    report = audit_continuous_pilot(features, qc_dir, events, output)

    assert report["status"] == "audited"
    assert report["bounded_pilot_gate_status"] == "PENDING_REPLAY"
    assert report["full_cohort_scoring_authorized"] is False
    assert report["charts_generated"] is False
    assert report["outcomes_calculated"] is False
    assert report["counts"]["support_eligible_rows"] == 12
    assert report["counts"]["pairs_by_horizon"]["h1"]["eligible_pairs"] == 10
    assert report["counts"]["pairs_by_horizon"]["h2"]["eligible_pairs"] == 8
    assert report["counts"]["pairs_by_horizon"]["h4"]["eligible_pairs"] == 4
    assert (output / "pilot_support_ledger.csv").is_file()
    assert (output / "pilot_stage_audit.csv").is_file()
    assert (output / "pilot_temporal_pairs.csv").is_file()
    leakage = json.loads((output / "pilot_leakage_ledger.json").read_text(encoding="utf-8"))
    assert leakage["admitted_predictors"] == []
    assert all("ppg_rate_bpm" not in field for field in pd.read_csv(output / "pilot_support_ledger.csv").columns)


def test_gap_or_unknown_support_removes_every_pair_using_that_row(tmp_path):
    features, qc_dir, events = _fixture(tmp_path, invalidate_epoch=2)
    output = tmp_path / "audit"
    report = audit_continuous_pilot(features, qc_dir, events, output)
    assert report["counts"]["support_eligible_rows"] == 10
    pairs = pd.read_csv(output / "pilot_temporal_pairs.csv")
    touching = pairs[
        (pairs["file"].str.startswith("sub-100"))
        & (pairs["origin_epoch_id"].between(0, 2))
        & (pairs["target_epoch_id"].between(2, 4))
    ]
    assert not touching["pair_support_eligible"].any()


def test_replay_is_checked_and_existing_outputs_are_not_overwritten(tmp_path):
    features, qc_dir, events = _fixture(tmp_path)
    reference = tmp_path / "first"
    audit_continuous_pilot(features, qc_dir, events, reference)
    replay = audit_continuous_pilot(features, qc_dir, events, tmp_path / "replay", replay_reference=reference)
    assert replay["replay_comparison"]["status"] == "reproduced"
    assert replay["bounded_pilot_gate_status"] == "PASS_BOUNDED_TECHNICAL_ONLY"
    with pytest.raises(FileExistsError):
        audit_continuous_pilot(features, qc_dir, events, reference)


def test_unverified_continuity_is_preserved_as_unknown_not_qualified(tmp_path):
    features, qc_dir, events = _fixture(tmp_path)
    sidecar_path = next(qc_dir.glob("*_qc_artifacts.json"))
    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    payload["signal_support_provenance"]["edf_sample_grid"]["continuity_status"] = "unknown"
    sidecar_path.write_text(json.dumps(payload), encoding="utf-8")
    report = audit_continuous_pilot(features, qc_dir, events, tmp_path / "audit")
    assert report["support_record_status"][sidecar_path.name.removesuffix("_qc_artifacts.json") + ".edf"] == "unknown"
    assert report["counts"]["support_eligible_rows"] == 6


def test_missing_per_channel_edf_grid_evidence_is_not_qualified(tmp_path):
    features, qc_dir, events = _fixture(tmp_path)
    sidecar_path = next(qc_dir.glob("*_qc_artifacts.json"))
    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    del payload["signal_support_provenance"]["edf_sample_grid"]["samples_per_record_by_channel"]
    sidecar_path.write_text(json.dumps(payload), encoding="utf-8")
    report = audit_continuous_pilot(features, qc_dir, events, tmp_path / "audit")
    key = sidecar_path.name.removesuffix("_qc_artifacts.json") + ".edf"
    assert report["support_record_status"][key] == "unknown"
    assert "edf_continuity_grid_fields_invalid" in report["support_record_reasons"][key]


@pytest.mark.parametrize("case", ["missing", "conflicting", "unmapped", "transition_straddling"])
def test_stage_coverage_defects_close_the_measurement_gate(tmp_path, case):
    features, qc_dir, events = _fixture(tmp_path)
    event_path = events["sub-100"]
    if case == "missing":
        rows = [{"onset": 300.0, "duration": 30.0, "stage_hum": 0}]
    elif case == "conflicting":
        rows = [
            {"onset": 0.0, "duration": 180.0, "stage_hum": 0},
            {"onset": 0.0, "duration": 180.0, "stage_hum": 2},
        ]
    elif case == "unmapped":
        rows = [{"onset": 0.0, "duration": 180.0, "stage_hum": 99}]
    else:
        rows = [
            {"onset": i * 15.0, "duration": 15.0, "stage_hum": i % 2 * 2}
            for i in range(12)
        ]
    pd.DataFrame(rows).to_csv(event_path, sep="\t", index=False)
    report = audit_continuous_pilot(features, qc_dir, events, tmp_path / "audit")
    assert report["bounded_pilot_gate_status"] == "INCONCLUSIVE_STAGE_COVERAGE"
    assert report["counts"]["stage_coverage_gate"] == "INCONCLUSIVE"


@pytest.mark.parametrize(
    "quality_record",
    [
        {"status": "observed"},
        {"status": "none_observed", "intervals": [{"clock": "original_raw_seconds", "start_sec": 1.0, "end_sec": 2.0}]},
    ],
)
def test_quality_ledger_status_must_match_an_explicit_interval_list(tmp_path, quality_record):
    features, qc_dir, events = _fixture(tmp_path)
    sidecar_path = next(qc_dir.glob("*_qc_artifacts.json"))
    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    payload["signal_support_provenance"]["source_quality_intervals"] = quality_record
    sidecar_path.write_text(json.dumps(payload), encoding="utf-8")
    report = audit_continuous_pilot(features, qc_dir, events, tmp_path / "audit")
    assert report["bounded_pilot_gate_status"] == "FAIL_SUPPORT_PROVENANCE"
    key = sidecar_path.name.removesuffix("_qc_artifacts.json") + ".edf"
    assert report["support_record_status"][key] == "unknown"


def test_shifted_actual_support_bound_is_rejected(tmp_path):
    features, qc_dir, events = _fixture(tmp_path)
    frame = pd.read_csv(features)
    mask = frame["file"].str.startswith("sub-100") & (frame["epoch_id"] == 2)
    frame.loc[mask, "actual_source_sample_start"] += 2
    frame.loc[mask, "actual_source_time_start_sec"] = frame.loc[mask, "actual_source_sample_start"] / 256.0
    frame.to_csv(features, index=False)
    report = audit_continuous_pilot(features, qc_dir, events, tmp_path / "audit")
    ledger = pd.read_csv(tmp_path / "audit" / "pilot_support_ledger.csv")
    row = ledger.loc[ledger["file"].str.startswith("sub-100") & (ledger["epoch_id"] == 2)].iloc[0]
    assert not bool(row["row_support_eligible"])
    assert "actual_support_does_not_match_causal_contract" in row["exclusion_reasons"]
    assert report["counts"]["support_eligible_rows"] == 11


def test_source_quality_overlap_and_real_timestamp_gap_remove_candidate_pairs(tmp_path):
    features, qc_dir, events = _fixture(tmp_path)
    sidecar_path = next(qc_dir.glob("sub-100*_qc_artifacts.json"))
    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    payload["signal_support_provenance"]["source_quality_intervals"] = {
        "status": "observed",
        "intervals": [{"clock": "original_raw_seconds", "start_sec": 70.0, "end_sec": 80.0}],
    }
    sidecar_path.write_text(json.dumps(payload), encoding="utf-8")
    frame = pd.read_csv(features)
    mask = frame["file"].str.startswith("sub-105") & (frame["epoch_id"] == 3)
    frame.loc[mask, "t_start"] += 1.0
    frame.to_csv(features, index=False)
    audit_continuous_pilot(features, qc_dir, events, tmp_path / "audit")
    pairs = pd.read_csv(tmp_path / "audit" / "pilot_temporal_pairs.csv")
    quality_touching = pairs[
        pairs["file"].str.startswith("sub-100")
        & pairs["origin_epoch_id"].between(0, 2)
        & pairs["target_epoch_id"].between(2, 4)
    ]
    assert not quality_touching["pair_support_eligible"].any()
    gap_touching = pairs[
        pairs["file"].str.startswith("sub-105")
        & (pairs["origin_epoch_id"] < 3)
        & (pairs["target_epoch_id"] >= 3)
    ]
    assert not gap_touching["pair_support_eligible"].any()
    assert gap_touching["exclusion_reasons"].str.contains("timestamp_gap").any()


def test_replay_surface_mismatch_is_a_failed_gate(tmp_path):
    features, qc_dir, events = _fixture(tmp_path)
    reference = tmp_path / "first"
    audit_continuous_pilot(features, qc_dir, events, reference)
    replay_features = tmp_path / "replay_features.csv"
    frame = pd.read_csv(features)
    frame.loc[0, "eeg_alpha"] += 1.0
    frame.to_csv(replay_features, index=False)
    replay = audit_continuous_pilot(
        replay_features, qc_dir, events, tmp_path / "replay",
        replay_reference=reference,
    )
    assert replay["bounded_pilot_gate_status"] == "FAIL_REPLAY"
    assert replay["replay_comparison"]["status"] == "mismatch"


def test_replay_support_provenance_change_fails_even_when_audit_ledgers_match(tmp_path):
    features, qc_dir, events = _fixture(tmp_path)
    reference = tmp_path / "first"
    audit_continuous_pilot(features, qc_dir, events, reference)
    sidecar_path = next(qc_dir.glob("sub-100*_qc_artifacts.json"))
    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    payload["signal_support_provenance"]["channel_types_after_dataset_typing"]["AUX"] = "eeg"
    sidecar_path.write_text(json.dumps(payload), encoding="utf-8")
    replay = audit_continuous_pilot(
        features, qc_dir, events, tmp_path / "replay", replay_reference=reference,
    )
    assert replay["bounded_pilot_gate_status"] == "FAIL_REPLAY"
    assert replay["replay_comparison"]["reason"] == "support_provenance_contract_differs"


def test_fractional_epoch_identity_is_rejected_before_integer_conversion(tmp_path):
    features, qc_dir, events = _fixture(tmp_path)
    frame = pd.read_csv(features)
    frame["epoch_id"] = frame["epoch_id"].astype(float)
    frame.loc[0, "epoch_id"] = 0.5
    frame.to_csv(features, index=False)
    with pytest.raises(ValueError, match="non-integral"):
        audit_continuous_pilot(features, qc_dir, events, tmp_path / "audit")


def test_near_integer_epoch_ids_that_would_collide_after_rounding_are_rejected(tmp_path):
    features, qc_dir, events = _fixture(tmp_path)
    frame = pd.read_csv(features)
    frame["epoch_id"] = frame["epoch_id"].astype(float)
    frame.loc[0, "epoch_id"] = 1e-10
    frame.loc[1, "epoch_id"] = 2e-10
    frame.to_csv(features, index=False)
    with pytest.raises(ValueError, match="non-integral"):
        audit_continuous_pilot(features, qc_dir, events, tmp_path / "audit")


def test_swapped_subject_event_paths_are_rejected_even_when_path_set_matches(tmp_path):
    features, qc_dir, events = _fixture(tmp_path)
    swapped = {"sub-100": events["sub-105"], "sub-105": events["sub-100"]}
    with pytest.raises(ValueError, match="same unique subject"):
        audit_continuous_pilot(features, qc_dir, swapped, tmp_path / "audit")
    assert not (tmp_path / "audit").exists()


def test_freeze_manifest_role_must_bind_expected_pilot_config_path(tmp_path):
    features, qc_dir, events = _fixture(tmp_path)
    manifest_path = _test_freeze_manifest(tmp_path, qc_dir, events)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    wrong_path = tmp_path / "wrong_prediction_config.yaml"
    wrong_path.write_text("not the frozen pilot config\n", encoding="utf-8")
    for entry in payload["inputs"]:
        if entry["role"] == "pilot_config":
            entry["path"] = str(wrong_path.resolve())
            entry["sha256"] = hashlib.sha256(wrong_path.read_bytes()).hexdigest()
            break
    manifest_path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="pilot_config role"):
        _audit_continuous_pilot(
            features, qc_dir, events, tmp_path / "audit", freeze_manifest=manifest_path,
        )
    assert not (tmp_path / "audit").exists()


def test_stale_frozen_source_hash_fails_before_writing_audit(tmp_path):
    features, qc_dir, events = _fixture(tmp_path)
    manifest_path = _test_freeze_manifest(tmp_path, qc_dir, events)
    source_path = next(tmp_path.rglob("sub-100*_eeg.edf"))
    source_path.write_bytes(source_path.read_bytes() + b"changed")
    output = tmp_path / "audit"
    with pytest.raises(ValueError, match="frozen pilot input hash mismatch"):
        _audit_continuous_pilot(
            features, qc_dir, events, output, freeze_manifest=manifest_path,
        )
    assert not output.exists()


def test_zero_duration_quality_marker_excludes_support_containing_its_time(tmp_path):
    features, qc_dir, events = _fixture(tmp_path)
    sidecar_path = next(qc_dir.glob("sub-100*_qc_artifacts.json"))
    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    payload["signal_support_provenance"]["source_quality_intervals"] = {
        "status": "observed",
        "intervals": [{
            "clock": "original_raw_seconds", "start_sec": 80.0, "end_sec": 80.0,
        }],
    }
    sidecar_path.write_text(json.dumps(payload), encoding="utf-8")
    audit_continuous_pilot(features, qc_dir, events, tmp_path / "audit")
    ledger = pd.read_csv(tmp_path / "audit" / "pilot_support_ledger.csv")
    row = ledger.loc[
        ledger["file"].str.startswith("sub-100") & (ledger["epoch_id"] == 2)
    ].iloc[0]
    assert not bool(row["row_support_eligible"])
    assert "support_overlaps_rejected_source_quality_interval" in row["exclusion_reasons"]
