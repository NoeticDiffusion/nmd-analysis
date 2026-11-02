from __future__ import annotations

import csv
import json

import h5py
import numpy as np

from nmd_analysis.continuous_support_audit import (
    audit_stage_midpoints,
    contiguous_segment_ids,
    pair_support_by_stage,
    run_audit,
)


def test_contiguous_segments_split_on_gap_and_overlap() -> None:
    starts = [0.0, 30.0, 60.0, 120.0, 149.0]
    ends = [30.0, 60.0, 90.0, 150.0, 179.0]

    ids, segments, gaps, overlaps, gap_seconds = contiguous_segment_ids(starts, ends)

    assert ids.tolist() == [0, 0, 0, 1, 2]
    assert len(segments) == 3
    assert gaps == 1
    assert overlaps == 1
    assert gap_seconds == 30.0
    assert [row["duration_sec"] for row in segments] == [90.0, 30.0, 30.0]


def test_pair_support_requires_same_segment_and_valid_intermediate_rows() -> None:
    rows = pair_support_by_stage(
        stage=[0, 0, 1, 1, 1],
        segment_ids=[0, 0, 0, 1, 1],
        valid_3d=[True, True, False, True, True],
        valid_9d=[True, True, True, True, True],
        horizons=(1, 2),
    )
    by_stage = {row["stage_code"]: row for row in rows}

    assert by_stage[0]["h1_timestamp_contiguous_pairs"] == 2
    assert by_stage[0]["h1_valid_3d_pairs"] == 1
    assert by_stage[0]["h1_valid_9d_pairs"] == 2
    assert by_stage[0]["h2_timestamp_contiguous_pairs"] == 1
    assert by_stage[0]["h2_valid_3d_pairs"] == 0
    assert by_stage[0]["h2_valid_9d_pairs"] == 1
    assert by_stage[1]["h1_timestamp_contiguous_pairs"] == 1
    assert by_stage[1]["h2_timestamp_contiguous_pairs"] == 0
    assert by_stage[4]["n_windows_start_stage"] == 0
    assert by_stage[4]["h1_valid_3d_pairs"] == 0


def test_stage_midpoint_audit_maps_human_scored_source(tmp_path) -> None:
    events = tmp_path / "sub-test_events.tsv"
    with events.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["onset", "duration", "stage_hum"], delimiter="\t")
        writer.writeheader()
        writer.writerows(
            [
                {"onset": 0, "duration": 30, "stage_hum": 0},
                {"onset": 30, "duration": 30, "stage_hum": 2},
            ]
        )

    result = audit_stage_midpoints(events, [15.0, 45.0], [0, 2])

    assert result["status"] == "pass"
    assert result["source_stage_column"] == "stage_hum"
    assert result["window_midpoint_covered_count"] == 2
    assert result["stored_label_match_count"] == 2
    assert result["stored_label_mismatch_count"] == 0
    assert result["source_hash_stable_during_read"] is True


def test_unmapped_source_event_cannot_silently_pass_for_unknown_window(tmp_path) -> None:
    events = tmp_path / "sub-test_events.tsv"
    with events.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["onset", "duration", "stage_hum"], delimiter="\t")
        writer.writeheader()
        writer.writerows(
            [
                {"onset": 0, "duration": 30, "stage_hum": 0},
                {"onset": 30, "duration": 30, "stage_hum": "unrecognized"},
            ]
        )

    result = audit_stage_midpoints(events, [15.0, 45.0], [0, -1])

    assert result["status"] == "partial"
    assert result["source_event_count"] == 2
    assert result["source_event_count_mapped"] == 1
    assert result["source_event_count_skipped"] == 1
    assert result["source_event_count_unmapped_stage"] == 1
    assert result["window_midpoint_covered_count"] == 1


def test_invalid_source_event_timing_is_counted_and_prevents_pass(tmp_path) -> None:
    events = tmp_path / "sub-test_events.tsv"
    with events.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["onset", "duration", "stage_hum"], delimiter="\t")
        writer.writeheader()
        writer.writerows(
            [
                {"onset": 0, "duration": 30, "stage_hum": 0},
                {"onset": "invalid", "duration": 30, "stage_hum": 2},
            ]
        )

    result = audit_stage_midpoints(events, [15.0], [0])

    assert result["status"] == "partial"
    assert result["source_event_count_skipped"] == 1
    assert result["source_event_count_invalid_timing"] == 1


def test_run_audit_keeps_window_index_and_metadata_as_distinct_files(tmp_path) -> None:
    input_root = tmp_path / "h5"
    input_root.mkdir()
    events = tmp_path / "sub-test_events.tsv"
    with events.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["onset", "duration", "stage_hum"], delimiter="\t")
        writer.writeheader()
        writer.writerows(
            [
                {"onset": 0, "duration": 30, "stage_hum": 0},
                {"onset": 30, "duration": 30, "stage_hum": 1},
            ]
        )
    h5_path = input_root / "sub-test.h5"
    with h5py.File(h5_path, "w") as h5:
        h5.attrs.update(
            {
                "subject_id": "sub-test",
                "dataset_id": "ds005555:sub-test_task-Sleep_acq-psg",
                "meta_pid": 7,
                "stage_events_path": str(events),
            }
        )
        h5.create_dataset("epoch_id", data=np.array([0, 1], dtype=np.int64))
        h5.create_dataset("window_start", data=np.array([0.0, 30.0]))
        h5.create_dataset("window_end", data=np.array([30.0, 60.0]))
        h5.create_dataset("labels/stage", data=np.array([0, 1], dtype=np.int32))
        h5.create_dataset("mnps_3d", data=np.ones((2, 3), dtype=np.float32))
        h5.create_dataset("coords_9d/values", data=np.ones((2, 9), dtype=np.float32))
        for name in (
            "retained_after_qc",
            "coverage_ok",
            "geometry_valid",
            "mnps_3d_valid",
            "coords_9d_valid",
        ):
            h5.create_dataset(f"qc/windows/{name}", data=np.ones(2, dtype=np.int8))
        h5.create_dataset("qc/windows/rejected_flag", data=np.zeros(2, dtype=np.int8))
        h5.create_dataset(
            "provenance/signal_support_provenance/temporal_support_status",
            data=np.bytes_("unknown"),
        )
        h5.create_dataset(
            "provenance/signal_support_provenance/source_quality_status",
            data=np.bytes_("not_recorded"),
        )

    output = tmp_path / "audit"
    result = run_audit(input_root, output)

    window_index = output / "window_segment_index.csv"
    metadata_path = output / "temporal_support_audit_metadata.json"
    assert window_index.is_file() and metadata_path.is_file()
    with window_index.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2
    assert [row["segment_id"] for row in rows] == ["0", "0"]
    assert rows[0]["temporal_support_status"] == "unknown"
    assert json.loads(metadata_path.read_text(encoding="utf-8"))["window_count"] == 2
    assert "window_segment_index.csv" in result["outputs"]
