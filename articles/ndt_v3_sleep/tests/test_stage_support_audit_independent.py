"""Independent known-answer tests for the bounded stage-support audit.

These tests exercise the measurement contract from the outside: contiguous
known-label runs, source alignment and provenance are checked against values
constructed in the fixture rather than against the runner's own summaries.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import stage_support_audit as audit_module
from stage_support_audit import KNOWN, audit_bouts, raw_alignment, run, sha256


def _epoch_frame(stage_codes: list[int], *, ids: list[float] | None = None,
                 starts: list[float] | None = None) -> pd.DataFrame:
    n = len(stage_codes)
    starts = starts or [30.0 * i for i in range(n)]
    ids = ids or [float(i) for i in range(n)]
    labels = [KNOWN.get(int(code)) if int(code) in KNOWN else None for code in stage_codes]
    status = ["recorded" if label is not None else "missing_or_unknown" for label in labels]
    return pd.DataFrame({
        "window_id": ids,
        "window_start": starts,
        "window_end": [start + 30.0 for start in starts],
        "stage_code": stage_codes,
        "stage_label": labels,
        "stage_label_status": status,
    })


def test_known_runs_have_exact_two_sided_retention_and_unknowns_are_boundaries():
    # The known runs have lengths 1, 2, 3 and 4.  With both immediate
    # neighbors required, their retained counts are 0, 0, 1 and 2.
    frame = _epoch_frame([1, 3, 3, 2, 2, 4, 4, 4, 0, 0, 0, 0, 8, 1])
    bouts, summary = audit_bouts(frame)

    assert bouts.n_windows.tolist() == [1, 2, 2, 3, 4, 1, 1]
    assert bouts.two_sided_retained_windows.tolist() == [0, 0, 0, 1, 2, 0, 0]
    # Code 8 is an explicit unknown boundary and is excluded from every
    # known-stage summary; the final N1 is a separate one-window run.
    n1 = summary.loc[summary.stage_code == 1].iloc[0]
    n2 = summary.loc[summary.stage_code == 2].iloc[0]
    n3 = summary.loc[summary.stage_code == 3].iloc[0]
    n4 = summary.loc[summary.stage_code == 4].iloc[0]
    assert (int(n1.n_bouts), int(n1.n_windows), int(n1.two_sided_retained_windows)) == (2, 2, 0)
    assert (int(n2.n_bouts), int(n2.n_windows), int(n2.two_sided_retained_windows)) == (1, 2, 0)
    assert (int(n3.n_bouts), int(n3.n_windows), int(n3.two_sided_retained_windows)) == (1, 2, 0)
    assert (int(n4.n_bouts), int(n4.n_windows), int(n4.two_sided_retained_windows)) == (1, 3, 1)


def test_gaps_and_overlaps_split_runs_without_bridging():
    # The same known label is separated by a gap, then an overlap.  Neither
    # transition may be silently treated as a contiguous stage run.
    frame = _epoch_frame([2, 2, 2, 2], starts=[0.0, 30.0, 65.0, 90.0])
    bouts, _ = audit_bouts(frame)
    assert bouts.n_windows.tolist() == [2, 1, 1]
    assert bouts.start_window_id.tolist() == [0, 2, 3]
    assert bouts.two_sided_retained_windows.tolist() == [0, 0, 0]


def test_raw_alignment_marks_shift_and_rejects_length_mismatch_without_ai_column():
    frame = _epoch_frame([1, 1])
    raw = pd.DataFrame({
        "onset": [0.0, 30.25],  # second epoch is shifted by 250 ms
        "duration": [30.0, 30.0],
        "begsample": [1, 7681],
        "endsample": [7680, 15360],
        "offset": [0, 0],
        "stage_hum": [1, 1],
    })
    aligned = raw_alignment(frame, raw, 256.0)
    assert aligned.stage_hum_match.all()
    assert aligned.onset_matches_window_start.tolist() == [True, False]
    assert aligned.sample_clock_ok.tolist() == [True, False]
    assert "raw_stage_ai" in aligned.columns
    assert aligned.raw_stage_ai.isna().all()

    with pytest.raises(ValueError, match="row count"):
        raw_alignment(frame, raw.iloc[:1], 256.0)


def test_empty_known_stage_group_uses_nan_bounds():
    _, summary = audit_bouts(_epoch_frame([0, 0]))
    wake = summary.loc[summary.stage_code == 0].iloc[0]
    n1 = summary.loc[summary.stage_code == 1].iloc[0]
    assert (int(wake.min_bout_windows), int(wake.max_bout_windows)) == (2, 2)
    assert pd.isna(n1.min_bout_windows) and pd.isna(n1.max_bout_windows)


def _write_run_fixture(tmp_path: Path, *, recording_duration: float | None,
                       sampling_frequency: float = 256.0) -> tuple[Path, Path, Path]:
    table = tmp_path / "epoch_coordinates.parquet"
    frame = _epoch_frame([1, 1, 1])
    frame.to_parquet(table, index=False)

    raw = tmp_path / "events.tsv"
    pd.DataFrame({
        "onset": [0.0, 30.0, 60.0],
        "duration": [30.0, 30.0, 30.0],
        "begsample": [1, 7681, 15361],
        "endsample": [7680, 15360, 23040],
        "offset": [0, 0, 0],
        "stage_hum": [1, 1, 1],
    }).to_csv(raw, sep="\t", index=False)

    epoch_manifest = tmp_path / "epoch_manifest.json"
    epoch_manifest.write_text(
        json.dumps({"status": "synthetic", "output": {"table_sha256": sha256(table)}}),
        encoding="utf-8",
    )
    provenance: dict[str, Path] = {}
    for name, payload in {
        "events_json": {"stage_hum": "human"},
        "eeg_json": ({"SamplingFrequency": sampling_frequency, "RecordingDuration": recording_duration}
                      if recording_duration is not None else {"SamplingFrequency": sampling_frequency}),
        "dataset_readme": "synthetic source README",
        "dataset_description": {"Name": "synthetic"},
    }.items():
        path = tmp_path / name
        if isinstance(payload, dict):
            path.write_text(json.dumps(payload), encoding="utf-8")
        else:
            path.write_text(payload, encoding="utf-8")
        provenance[name] = path

    code = Path(__file__).resolve().parents[1] / "src" / "stage_support_audit.py"
    config = tmp_path / "stage_support.yaml"
    cfg = {
        "epoch_table": str(table),
        "epoch_table_sha256": sha256(table),
        "epoch_manifest": str(epoch_manifest),
        "epoch_manifest_sha256": sha256(epoch_manifest),
        "raw_events": str(raw),
        "raw_events_sha256": sha256(raw),
        "analysis_code": str(code),
        "analysis_code_sha256": sha256(code),
        "provenance_files": {
            name: {"path": str(path), "sha256": sha256(path)}
            for name, path in provenance.items()
        },
    }
    config.write_text(json.dumps(cfg), encoding="utf-8")
    return table, raw, config


def test_run_rejects_noninteger_ids_and_stage_codes_instead_of_truncating(tmp_path):
    table, raw, _ = _write_run_fixture(tmp_path, recording_duration=100.0)
    frame = pd.read_parquet(table)
    frame.loc[1, "window_id"] = 1.5
    frame.to_parquet(table, index=False)
    with pytest.raises(ValueError, match="integer"):
        run(table, raw, tmp_path / "audit_ids")

    frame.loc[1, "window_id"] = 1.0
    frame["stage_code"] = frame["stage_code"].astype(float)
    frame.loc[1, "stage_code"] = 1.5
    frame.to_parquet(table, index=False)
    with pytest.raises(ValueError, match="stage"):
        run(table, raw, tmp_path / "audit_stage")


def test_run_uses_recorded_sampling_frequency_for_sample_bounds(tmp_path):
    table, raw, config = _write_run_fixture(tmp_path, recording_duration=100.0,
                                            sampling_frequency=128.0)
    result = run(table, raw, tmp_path / "audit", config)
    assert result["sampling_frequency_hz"] == 128.0
    assert result["raw_alignment_all_sample_clock"] is False
    assert result["status"] == "mismatch"


def test_run_derives_tail_and_registers_source_code_runtime_and_output_hashes(tmp_path):
    table, raw, config = _write_run_fixture(tmp_path, recording_duration=100.0)
    result = run(table, raw, tmp_path / "audit", config)

    assert result["recording_duration_sec"] == 100.0
    assert result["recording_tail_sec_not_in_epoch_table"] == 10.0
    assert result["epoch_manifest"] == {
        "path": str((tmp_path / "epoch_manifest.json").resolve()),
        "sha256": sha256(tmp_path / "epoch_manifest.json"),
    }
    code = Path(__file__).resolve().parents[1] / "src" / "stage_support_audit.py"
    assert result["analysis_code"] == str(code.resolve())
    assert result["analysis_code_sha256"] == sha256(code)
    assert result.get("python") or result.get("runtime") or result.get("package_versions")
    output_hashes = result["output_sha256"]
    for name in ("stage_bouts.csv", "stage_bout_summary.csv", "raw_annotation_alignment.csv"):
        assert output_hashes[name] == sha256(tmp_path / "audit" / name)


def test_run_keeps_tail_unknown_when_recording_duration_is_unavailable(tmp_path):
    table, raw, config = _write_run_fixture(tmp_path, recording_duration=None)
    result = run(table, raw, tmp_path / "audit", config)
    assert result["recording_duration_sec"] is None
    assert result["recording_tail_sec_not_in_epoch_table"] is None


@pytest.mark.parametrize("bad_duration", [float("nan"), -1.0, 80.0])
def test_run_does_not_treat_invalid_recording_duration_as_real_support(tmp_path, bad_duration):
    table, raw, config = _write_run_fixture(tmp_path, recording_duration=bad_duration)
    result = run(table, raw, tmp_path / "audit", config)
    assert result["recording_duration_sec"] is None
    assert result["recording_tail_sec_not_in_epoch_table"] is None


def test_run_captures_input_hash_before_and_after_read(monkeypatch, tmp_path):
    table, raw, config = _write_run_fixture(tmp_path, recording_duration=100.0)
    original_read_csv = audit_module.pd.read_csv

    def read_then_mutate(*args, **kwargs):
        loaded = original_read_csv(*args, **kwargs)
        raw.write_bytes(raw.read_bytes() + b"\n")
        return loaded

    monkeypatch.setattr(audit_module.pd, "read_csv", read_then_mutate)
    try:
        result = run(table, raw, tmp_path / "audit", config)
    except ValueError as exc:
        # A fail-closed implementation may reject a source that changes while
        # it is being read.  If it returns a manifest, the two snapshots must
        # still expose the change.
        assert "chang" in str(exc).lower()
        return
    assert result["input_hashes_before"]["raw_events"] != result["input_hashes_after"]["raw_events"]
