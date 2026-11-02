from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nmd_analysis.continuous_full_surface_audit import (
    _FEATURE_EXPORT_COLUMNS,
    _contiguous_segments,
    _pair_availability,
    _qualify_primary_row,
    _recording_source_stratum,
    audit_continuous_full_surface,
)
from nmd_analysis.continuous_pilot_audit import _row_support_status, _stage_at_point, _stage_purity


def _write_edf_and_sidecar(root: Path, subject: str, qc_dir: Path) -> tuple[Path, Path]:
    eeg_dir = root / subject / "eeg"
    eeg_dir.mkdir(parents=True)
    filename = f"{subject}_task-Sleep_acq-psg_eeg.edf"
    source_path = eeg_dir / filename
    source_path.write_bytes(f"synthetic continuous EDF for {subject}".encode())
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    sample_count = 180 * 256
    record = {
        "schema": "mndm.signal_support_provenance.v1",
        "status": "completed",
        "source": {
            "path": str(source_path), "exists": True, "sha256": source_hash,
            "sha256_after": source_hash, "hash_stable": True,
        },
        "temporal_support_mode": "causal_finite",
        "input_sfreq_hz": 256.0,
        "target_sfreq_hz": 256.0,
        "temporal_support": {"status": "finite_causal"},
        "effective_time_support": {
            "status": "finite_causal",
            "mode": "causal_finite_edf_identity_grid",
            "resampler": {"method": "identity_sample_grid", "phase": "identity", "up": 1, "down": 1, "tap_count": 1, "output_sample_count": sample_count},
            "eeg_bandpass": {
                "method": "mne.filter.filter_data_fir", "phase": "minimum", "pad": "constant",
                "tap_count": 11, "sfreq_hz": 256.0,
                "support_interpretation": "output k depends on input [max(0,k-tap_count+1),k]",
            },
        },
        "edf_sample_grid": {
            "continuity_status": "verified_continuous", "continuity_marker": "EDF",
            "continuity_verification": "EDF+D rejected; EDF/EDF+C record grid checked; no BAD_ACQ_SKIP, BAD boundary, or EDGE boundary annotations",
            "boundary_annotation_check": {"status": "verified_absent", "rejected_prefixes": ["BAD_ACQ_SKIP", "BAD BOUNDARY", "EDGE"]},
            "channel_count": 3, "samples_per_record_by_channel": [256, 256, 256],
            "sample_rate_hz": 256.0, "sample_count": sample_count, "records": 180,
            "samples_per_record": 256, "record_duration_seconds": 1.0,
        },
        "raw_clock_before_crop": {"sfreq_hz": 256.0, "n_times": sample_count},
        "raw_clock_after_crop": {"sfreq_hz": 256.0, "n_times": sample_count},
        "ppg_source_selection": {
            "rule": "source_channel_name_regex", "channel_names": ["PSG_PULSE"],
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
    qc_dir.mkdir(exist_ok=True)
    (qc_dir / f"{Path(filename).stem}_qc_artifacts.json").write_text(
        json.dumps({"signal_support_provenance": record}), encoding="utf-8"
    )
    event_path = eeg_dir / filename.replace("_eeg.edf", "_events.tsv")
    pd.DataFrame({
        "onset": [0.0, 90.0],
        "duration": [90.0, 90.0],
        "stage_hum": [0, 2],
    }).to_csv(event_path, sep="\t", index=False)
    return source_path, event_path


def _full_surface_fixture(root: Path):
    source_root = root / "ds005555"
    qc_dir = root / "qc_artifacts"
    qc_dir.mkdir()
    # Two BIDS subject labels share one biological PID; eight independent PIDs
    # remain, so removing one recording still leaves a valid five-fold roster.
    participant_rows = [("sub-1", "10"), ("sub-2", "10")]
    participant_rows.extend((f"sub-{number}", str(number * 10)) for number in range(3, 10))
    feature_rows = []
    for subject, _pid in participant_rows:
        source_path, _ = _write_edf_and_sidecar(source_root, subject, qc_dir)
        filename = source_path.name
        for epoch in range(6):
            start, end = epoch * 30.0, (epoch + 1) * 30.0
            nominal_start, nominal_end = epoch * 30 * 256, (epoch + 1) * 30 * 256
            actual_start = max(0, nominal_start - 10)
            rate = 60.0 + epoch
            feature_row = {
                "file": filename,
                "epoch_id": epoch,
                "t_start": start,
                "t_end": end,
                "embodied_arousal_proxy_source": "ppg_rate_bpm",
                "embodied_arousal_proxy": rate,
                "ppg_rate_bpm": rate,
                "qc_ok_ppg": True,
                "qc_ok_eeg": True,
                "source_sample_mapping_status": "nominal_bounds_mapped",
                "source_sample_mapping_reason": "preprocessed_epoch_clock_mapped",
                "nominal_source_sample_start": nominal_start,
                "nominal_source_sample_end_exclusive": nominal_end,
                "nominal_source_time_start_sec": start,
                "nominal_source_time_end_sec": end,
                "actual_sample_contributors_status": "finite_causal_conservative_bound",
                "actual_source_sample_start": actual_start,
                "actual_source_sample_end_exclusive": nominal_end,
                "actual_source_time_start_sec": actual_start / 256.0,
                "actual_source_time_end_sec": end,
                "source_sfreq_hz": 256.0,
                "input_sample_finite_status": "all_finite",
                "input_sample_finite_fraction": 1.0,
                "input_sample_gap_count": 0,
                "input_sample_gap_spans": "[]",
                "input_sample_invalid_reason": "",
                "eeg_alpha": 0.1 + epoch,
                "eeg_entropy_metric": "permutation_entropy",
                "stage": 0 if epoch < 3 else 2,
                "eog_blink_rate": 1.0 + epoch,
                "resp_rate_bpm": 12.0 + epoch,
            }
            for column in _FEATURE_EXPORT_COLUMNS:
                if column not in feature_row:
                    feature_row[column] = 0.1 + epoch if column.startswith("eeg_") else "fixture"
            feature_rows.append(feature_row)
    features = root / "features.csv"
    pd.DataFrame(feature_rows).to_csv(features, index=False)
    participants = source_root / "participants.tsv"
    pd.DataFrame(participant_rows, columns=["participant_id", "pid"]).to_csv(participants, sep="\t", index=False)
    protocol = root / "protocol.md"
    protocol.write_text("frozen protocol fixture\n", encoding="utf-8")
    config = root / "config.yaml"
    config.write_text("measurement-only fixture\n", encoding="utf-8")
    return features, qc_dir, participants, source_root, protocol, config


def test_recording_mixed_source_and_invalid_ppg_qc_fail_closed():
    assert _recording_source_stratum(["ppg_rate_bpm", "eog_blink_rate"])[0] == "mixed"
    ppg_row = {
        "embodied_arousal_proxy_source": "ppg_rate_bpm",
        "embodied_arousal_proxy": 60.0,
        "ppg_rate_bpm": 60.0,
    }
    mixed_ok, _, mixed_reasons = _qualify_primary_row(
        ppg_row, stratum="mixed", base_support_ok=True, base_reasons=[]
    )
    qc_ok, _, qc_reasons = _qualify_primary_row(
        ppg_row, stratum="pure_ppg", base_support_ok=False,
        base_reasons=["present_window_ppg_measurement_unavailable"],
    )
    assert not mixed_ok and any(reason.startswith("recording_source_stratum_not_pure_ppg") for reason in mixed_reasons)
    assert not qc_ok and "present_window_ppg_measurement_unavailable" in qc_reasons


def test_quality_interval_is_checked_against_exact_causal_support_not_only_window():
    row = {
        "source_sample_mapping_status": "nominal_bounds_mapped",
        "nominal_source_sample_start": 30 * 256,
        "nominal_source_sample_end_exclusive": 60 * 256,
        "actual_sample_contributors_status": "finite_causal_conservative_bound",
        "actual_source_sample_start": 30 * 256 - 10,
        "actual_source_sample_end_exclusive": 60 * 256,
        "actual_source_time_start_sec": (30 * 256 - 10) / 256,
        "actual_source_time_end_sec": 60.0,
        "source_sfreq_hz": 256.0,
        "nominal_source_time_start_sec": 30.0,
        "nominal_source_time_end_sec": 60.0,
        "t_start": 30.0,
        "t_end": 60.0,
        "input_sample_finite_status": "all_finite",
        "input_sample_gap_count": 0,
        "qc_ok_eeg": True,
        "qc_ok_ppg": True,
        "ppg_rate_bpm": 60.0,
    }
    record = {
        "effective_time_support": {"eeg_bandpass": {"tap_count": 11}},
        "edf_sample_grid": {"sample_count": 180 * 256},
    }
    gap_before_nominal_window = [{"clock": "original_raw_seconds", "start_sec": 29.96, "end_sec": 29.97}]
    eligible, reasons = _row_support_status(row, record, [], gap_before_nominal_window)
    assert not eligible
    assert "support_overlaps_rejected_source_quality_interval" in reasons
    assert row["t_start"] > gap_before_nominal_window[0]["end_sec"]


def test_stage_mapping_and_window_purity_use_half_open_source_intervals():
    events = [
        {"onset": 0.0, "duration": 60.0, "stage_hum": 0},
        {"onset": 60.0, "duration": 60.0, "stage_hum": 2},
    ]
    origin_stage, status = _stage_at_point(events, 60.0)
    assert origin_stage == 2 and status == "unique_source_stage_at_origin"
    pure, reason = _stage_purity(events, 30.0, 60.0, origin_stage)
    assert not pure and reason == "window_stage_differs_from_origin_stage"
    pure, reason = _stage_purity(events, 60.0, 90.0, 2)
    assert pure and reason == "stage_pure_at_origin"


def test_pair_support_rejects_epoch_and_timestamp_gaps():
    rows = []
    for epoch in range(6):
        rows.append({
            "file": "sub-1_task-Sleep_acq-psg_eeg.edf", "epoch_id": epoch,
            "pid": "10", "t_start": epoch * 30.0 + (1.0 if epoch == 3 else 0.0),
            "t_end": (epoch + 1) * 30.0 + (1.0 if epoch == 3 else 0.0),
            "source_stratum": "pure_ppg",
            "primary_surface_eligible": epoch != 2,
            "stage_at_origin_code": 2, "stage_window_pure": True,
        })
    for epoch in range(6):
        rows.append({
            "file": "sub-2_task-Sleep_acq-psg_eeg.edf", "epoch_id": epoch,
            "pid": "20", "t_start": epoch * 30.0, "t_end": (epoch + 1) * 30.0,
            "source_stratum": "pure_eog_blink", "primary_surface_eligible": False,
            "stage_at_origin_code": 2, "stage_window_pure": True,
        })
    frame = pd.DataFrame(rows)
    frame["segment_id"] = [
        _contiguous_segments(frame, 30.0)[(row.file, int(row.epoch_id))]
        for row in frame.itertuples()
    ]
    availability = _pair_availability(frame, 30.0)
    bad = availability.loc[
        (availability["model_scope"] == "C1_history2")
        & (availability["horizon"] == "h1")
    ]
    assert bad["support_and_contiguity_eligible"].sum() == 0
    assert set(availability["file"]) == {"sub-1_task-Sleep_acq-psg_eeg.edf"}


def test_full_audit_emits_hash_bound_pid_grouped_manifests_without_outcomes(tmp_path):
    features, qc_dir, participants, source_root, protocol, config = _full_surface_fixture(tmp_path)
    output = tmp_path / "full_audit"
    report = audit_continuous_full_surface(
        features, qc_dir, participants, source_root, protocol, config, output
    )
    assert report["status"] == "PARTIAL_PASS_SOURCE_SUPPORT_ONLY"
    assert report["charts_generated"] is False
    assert report["outcomes_calculated"] is False
    assert report["C1_C3_scores_opened"] is False
    assert report["full_cohort_scoring_authorized"] is False
    assert report["surface_replay_status"] == "PENDING_FULL_COHORT_REPLAY"
    assert report["counts"]["primary_eligible_pids"] == 8
    assert report["counts"]["primary_eligible_recordings"] == 9
    assert report["input_paths"]["features_table"] == str(features.resolve())
    assert report["input_paths"]["participants_tsv"] == str(participants.resolve())
    assert report["input_paths"]["protocol"] == str(protocol.resolve())
    assert report["input_paths"]["mndm_config"] == str(config.resolve())
    assert report["input_paths"]["audit_code"] == str(Path(audit_continuous_full_surface.__code__.co_filename).resolve())
    assert report["input_paths"]["qc_dir"] == str(qc_dir.resolve())
    assert report["input_paths"]["source_root"] == str(source_root.resolve())

    ledger_bytes = (output / "signal_support_ledger.json").read_bytes()
    ledger = json.loads(ledger_bytes)
    assert hashlib.sha256(ledger_bytes).hexdigest() == report["fold_assignment"]["signal_support_ledger_sha256"]
    assert ledger["schema"] == "mndm.signal_support_export.v1"
    assert ledger["temporal_support_status"] == "finite_causal_conservative_bound"
    assert "EOG/respiration" in ledger["temporal_support_reason"]
    assert len(ledger["per_epoch_input_extent"]) == 9 * 6

    primary = pd.read_parquet(output / "features_primary_ppg.parquet")
    assert primary["subject"].nunique() == 8
    assert primary.loc[primary["file"].str.startswith(("sub-1_", "sub-2_")), "subject"].nunique() == 1
    assert tuple(primary.columns) == _FEATURE_EXPORT_COLUMNS
    assert "stage" not in primary.columns
    assert not any(column.startswith(("eog_", "resp_")) for column in primary.columns)
    assert {"embodied_arousal_proxy", "ppg_rate_bpm", "eeg_alpha", "qc_ok_eeg"}.issubset(primary.columns)
    assert set(primary["eeg_entropy_metric"]) == {"permutation_entropy"}
    export_contract = report["feature_surface_export"]
    assert export_contract["label_free_predictor_overlay"] is True
    assert export_contract["stage_label_exported"] is False
    assert "eeg_entropy_metric" in export_contract["provenance_only_columns"]
    row_audit = pd.read_csv(output / "row_support_audit.csv")
    assert row_audit["primary_surface_eligible"].all()
    assert set(row_audit["stage_at_origin"].dropna()).issuperset({"wake", "n2"})

    fold_dir = output / "fold_manifests"
    manifests = sorted(fold_dir.glob("fold_*.json"))
    assert len(manifests) == 5
    for path in manifests:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["schema_version"] == "mndm.fold_split.v1"
        assert payload["signal_support_ledger_sha256"] == hashlib.sha256(ledger_bytes).hexdigest()
        assert set(payload["training_pids"]).isdisjoint(payload["apply_pids"])
        assert payload["training_ranges"] and payload["apply_ranges"]
        # The two BIDS identities sharing PID 10 stay on the same side.
        pid_subject = "sub-010"
        train_files = {item["recording_id"] for item in payload["training_ranges"] if item["subject_id"] == pid_subject}
        apply_files = {item["recording_id"] for item in payload["apply_ranges"] if item["subject_id"] == pid_subject}
        assert bool(train_files) ^ bool(apply_files)
        assert {"sub-1_task-Sleep_acq-psg_eeg.edf", "sub-2_task-Sleep_acq-psg_eeg.edf"}.issubset(train_files | apply_files)

    expected_output_hashes = {
        path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in output.rglob("*")
        if path.is_file() and path.name != "validation.json"
    }
    assert report["output_sha256"] == expected_output_hashes
    assert "validation.json is excluded" in report["output_hash_scope"]

    with pytest.raises(FileExistsError):
        audit_continuous_full_surface(features, qc_dir, participants, source_root, protocol, config, output)
