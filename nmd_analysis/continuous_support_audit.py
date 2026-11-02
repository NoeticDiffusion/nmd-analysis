"""Read-only continuity and future-pair support audit for MNDM HDF5 runs.

This module reports timestamp/QC eligibility only. It never upgrades signal
support, measurement validity, or scientific qualification.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import h5py
import numpy as np


SCHEMA_VERSION = "nmd_analysis.continuous_support_audit.v1.1"
DEFAULT_HORIZONS = (1, 2, 4)
STAGE_LABELS = {
    -2: "artifact_or_missing",
    -1: "unknown_or_unscored",
    0: "Wake",
    1: "N1",
    2: "N2",
    3: "N3",
    4: "REM",
    8: "PSG_disconnection",
}
STAGE_TEXT_MAP = {
    "W": 0,
    "WAKE": 0,
    "N1": 1,
    "N2": 2,
    "N3": 3,
    "R": 4,
    "REM": 4,
    "L": -1,
    "PSG_DISCONNECTION": 8,
    "ARTIFACT_OR_MISSING": -2,
}


def _text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def contiguous_segment_ids(
    window_start: Sequence[float],
    window_end: Sequence[float],
    *,
    tolerance_sec: float = 1e-3,
) -> tuple[np.ndarray, list[dict[str, Any]], int, int, float]:
    """Split rows whenever consecutive observed windows do not touch."""
    starts = np.asarray(window_start, dtype=float)
    ends = np.asarray(window_end, dtype=float)
    if starts.ndim != 1 or ends.ndim != 1 or starts.size != ends.size:
        raise ValueError("window_start and window_end must be equal-length vectors")
    if not np.isfinite(starts).all() or not np.isfinite(ends).all():
        raise ValueError("window bounds must be finite")
    if np.any(ends < starts):
        raise ValueError("window_end precedes window_start")
    if starts.size == 0:
        return np.empty(0, dtype=np.int64), [], 0, 0, 0.0
    if np.any(np.diff(starts) <= 0):
        raise ValueError("window_start must be strictly increasing")

    edge_delta = starts[1:] - ends[:-1]
    touches = np.isclose(edge_delta, 0.0, atol=tolerance_sec, rtol=0.0)
    gaps = edge_delta > tolerance_sec
    overlaps = edge_delta < -tolerance_sec
    breaks = np.r_[True, ~touches]
    segment_ids = np.cumsum(breaks, dtype=np.int64) - 1
    segments: list[dict[str, Any]] = []
    for segment_id in np.unique(segment_ids):
        idx = np.flatnonzero(segment_ids == segment_id)
        first, last = int(idx[0]), int(idx[-1])
        segments.append(
            {
                "segment_id": int(segment_id),
                "first_index": first,
                "last_index_exclusive": last + 1,
                "first_epoch_id_index": first,
                "last_epoch_id_index": last,
                "window_count": int(last - first + 1),
                "start_sec": float(starts[first]),
                "end_sec": float(ends[last]),
                "duration_sec": float(ends[last] - starts[first]),
                "gap_before_sec": float(edge_delta[first - 1]) if first else 0.0,
                "gap_after_sec": float(edge_delta[last]) if last < starts.size - 1 else 0.0,
            }
        )
    return (
        segment_ids,
        segments,
        int(gaps.sum()),
        int(overlaps.sum()),
        float(edge_delta[gaps].sum()),
    )


def pair_support_by_stage(
    stage: Sequence[int],
    segment_ids: Sequence[int],
    valid_3d: Sequence[bool],
    valid_9d: Sequence[bool],
    *,
    horizons: Iterable[int] = DEFAULT_HORIZONS,
) -> list[dict[str, Any]]:
    """Count within-segment pairs, requiring valid rows at every step."""
    labels = np.asarray(stage, dtype=np.int64)
    segments = np.asarray(segment_ids, dtype=np.int64)
    mask3 = np.asarray(valid_3d, dtype=bool)
    mask9 = np.asarray(valid_9d, dtype=bool)
    if not (labels.ndim == segments.ndim == mask3.ndim == mask9.ndim == 1):
        raise ValueError("stage, segment IDs, and validity masks must be vectors")
    if len({labels.size, segments.size, mask3.size, mask9.size}) != 1:
        raise ValueError("stage, segment IDs, and validity masks must have equal length")
    hs_values = tuple(sorted({int(h) for h in horizons}))
    if any(h < 1 for h in hs_values):
        raise ValueError("horizons must be positive row lags")

    rows: list[dict[str, Any]] = []
    # Keep the canonical sleep-stage cells even when a recording has no rows
    # in that stage; unavailable support must remain visible as zero rows.
    stage_codes = set(STAGE_LABELS).intersection({0, 1, 2, 3, 4})
    stage_codes.update(int(v) for v in np.unique(labels))
    for code in sorted(stage_codes):
        start_mask = labels == code
        row: dict[str, Any] = {
            "stage_code": code,
            "stage_label": STAGE_LABELS.get(code, f"unmapped_{code}"),
            "n_windows_start_stage": int(start_mask.sum()),
        }
        for horizon in hs_values:
            counts3 = 0
            counts9 = 0
            contiguous_count = 0
            n = labels.size
            if horizon < n:
                starts = np.arange(n - horizon)
                same_segment = segments[starts] == segments[starts + horizon]
                stage_selected = start_mask[starts]
                eligible = same_segment & stage_selected
                contiguous_count = int(eligible.sum())
                path3 = eligible.copy()
                path9 = eligible.copy()
                for offset in range(horizon + 1):
                    path3 &= mask3[starts + offset]
                    path9 &= mask9[starts + offset]
                counts3 = int(path3.sum())
                counts9 = int(path9.sum())
            row[f"h{horizon}_timestamp_contiguous_pairs"] = contiguous_count
            row[f"h{horizon}_valid_3d_pairs"] = counts3
            row[f"h{horizon}_valid_9d_pairs"] = counts9
        rows.append(row)
    return rows


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_code(value: Any) -> int | None:
    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text)
        if np.isfinite(number) and number.is_integer():
            return int(number)
    except (TypeError, ValueError):
        pass
    return STAGE_TEXT_MAP.get(text.upper())


def audit_stage_midpoints(
    events_path: str | Path | None,
    midpoints_sec: Sequence[float],
    observed_stage: Sequence[int],
    *,
    stage_columns: Sequence[str] = ("stage_hum", "stage_ai", "stage", "sleep_stage"),
    tolerance_sec: float = 1e-6,
) -> dict[str, Any]:
    """Recheck stored labels against the first configured source event column."""
    if not events_path:
        return {"status": "unavailable", "reason": "stage_events_path_missing"}
    path = Path(str(events_path))
    if not path.is_file():
        return {"status": "unavailable", "reason": "stage_events_file_missing", "path": str(path)}
    hash_before = _sha256(path)
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        fields = list(reader.fieldnames or [])
        stage_column = next((name for name in stage_columns if name in fields), None)
        if stage_column is None or "onset" not in fields:
            return {
                "status": "unavailable",
                "reason": "stage_or_onset_column_missing",
                "path": str(path),
                "source_sha256": hash_before,
                "source_columns": fields,
            }
        duration_column = "duration" if "duration" in fields else None
        events = []
        source_event_count = 0
        invalid_timing_count = 0
        unmapped_stage_count = 0
        skipped_event_count = 0
        for row_number, row in enumerate(reader, start=2):
            source_event_count += 1
            code = _source_code(row.get(stage_column))
            if code is None:
                unmapped_stage_count += 1
            try:
                onset = float(row["onset"])
                duration = float(row[duration_column]) if duration_column else 0.0
            except (TypeError, ValueError, KeyError):
                onset = float("nan")
                duration = float("nan")
            if not np.isfinite([onset, duration]).all() or duration < 0:
                invalid_timing_count += 1
            if code is None or not np.isfinite([onset, duration]).all() or duration < 0:
                skipped_event_count += 1
                continue
            events.append((onset, onset + max(duration, 0.0), code, row_number))
    hash_after = _sha256(path)
    stable = hash_before == hash_after
    events.sort(key=lambda item: (item[0], item[3]))
    onsets = [item[0] for item in events]
    ends = [item[1] for item in events]
    codes = [item[2] for item in events]
    mids = np.asarray(midpoints_sec, dtype=float)
    labels = np.asarray(observed_stage, dtype=np.int64)
    if mids.size != labels.size:
        raise ValueError("midpoints and stored stage labels must have equal length")

    overlap_count = 0
    max_end = float("-inf")
    for event_start, event_end, _, _ in events:
        if event_start < max_end - tolerance_sec:
            overlap_count += 1
        max_end = max(max_end, event_end)

    expected = np.full(labels.size, -999, dtype=np.int64)
    covered = np.zeros(labels.size, dtype=bool)
    for idx, midpoint in enumerate(mids):
        event_idx = bisect.bisect_right(onsets, float(midpoint)) - 1
        if event_idx < 0:
            continue
        if ends[event_idx] > onsets[event_idx] and midpoint < ends[event_idx]:
            expected[idx] = codes[event_idx]
            covered[idx] = True
        elif abs(midpoint - onsets[event_idx]) <= tolerance_sec:
            expected[idx] = codes[event_idx]
            covered[idx] = True
    mismatch = covered & (expected != labels)
    uncovered_labeled = (~covered) & (labels != -1)
    status = (
        "pass"
        if stable
        and not overlap_count
        and not mismatch.any()
        and not uncovered_labeled.any()
        and not skipped_event_count
        else "partial"
    )
    return {
        "status": status,
        "path": str(path),
        "source_sha256": hash_after,
        "source_hash_stable_during_read": stable,
        "source_stage_column": stage_column,
        "source_event_count": source_event_count,
        "source_event_count_mapped": len(events),
        "source_event_count_skipped": skipped_event_count,
        "source_event_count_invalid_timing": invalid_timing_count,
        "source_event_count_unmapped_stage": unmapped_stage_count,
        "source_interval_overlap_count": int(overlap_count),
        "window_midpoint_count": int(labels.size),
        "window_midpoint_covered_count": int(covered.sum()),
        "stored_label_match_count": int((covered & ~mismatch).sum()),
        "stored_label_mismatch_count": int(mismatch.sum()),
        "uncovered_labeled_window_count": int(uncovered_labeled.sum()),
    }


def _read_recording(
    path: Path,
    *,
    tolerance_sec: float,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    with h5py.File(path, "r") as h5:
        starts = np.asarray(h5["window_start"], dtype=float)
        ends = np.asarray(h5["window_end"], dtype=float)
        epoch_ids = np.asarray(h5["epoch_id"], dtype=np.int64)
        stage = np.asarray(h5["labels/stage"], dtype=np.int64)
        n = len(epoch_ids)
        if any(len(array) != n for array in (starts, ends, stage)):
            raise ValueError(f"array-length mismatch in {path}")

        segment_ids, segments, gap_count, overlap_count, gap_sec = contiguous_segment_ids(
            starts, ends, tolerance_sec=tolerance_sec
        )
        window_durations = ends - starts
        centers = (starts + ends) / 2.0
        center_steps = np.diff(centers)
        touching_edges = np.isclose(starts[1:] - ends[:-1], 0.0, atol=tolerance_sec, rtol=0.0)
        contiguous_center_steps = center_steps[touching_edges]
        qc = h5["qc/windows"]
        common_valid = np.asarray(qc["retained_after_qc"], dtype=bool)
        common_valid &= np.asarray(qc["coverage_ok"], dtype=bool)
        if "rejected_flag" in qc:
            common_valid &= ~np.asarray(qc["rejected_flag"], dtype=bool)
        coordinates3 = np.asarray(h5["mnps_3d"], dtype=float)
        coordinates9 = np.asarray(h5["coords_9d/values"], dtype=float)
        valid3 = (
            common_valid
            & np.asarray(qc["geometry_valid"], dtype=bool)
            & np.asarray(qc["mnps_3d_valid"], dtype=bool)
            & np.isfinite(coordinates3).all(axis=1)
        )
        valid9 = (
            common_valid
            & np.asarray(qc["coords_9d_valid"], dtype=bool)
            & np.isfinite(coordinates9).all(axis=1)
        )
        if len(valid3) != n or len(valid9) != n:
            raise ValueError(f"QC/coordinate length mismatch in {path}")

        stage_audit = audit_stage_midpoints(
            _text(h5.attrs.get("stage_events_path", "")),
            (starts + ends) / 2.0,
            stage,
        )
        pid_raw = h5.attrs.get("meta_pid")
        pid = int(pid_raw) if pid_raw is not None else None
        subject_id = _text(h5.attrs.get("subject_id", ""))
        dataset_id = _text(h5.attrs.get("dataset_id", ""))
        recording_id = dataset_id.split(":", 1)[-1] if ":" in dataset_id else path.stem
        temporal_status = _text(h5["provenance/signal_support_provenance/temporal_support_status"][()])
        quality_status = _text(h5["provenance/signal_support_provenance/source_quality_status"][()])
        support_rows = pair_support_by_stage(stage, segment_ids, valid3, valid9)

        segment_rows: list[dict[str, Any]] = []
        for segment in segments:
            first = int(segment["first_index"])
            stop = int(segment["last_index_exclusive"])
            last = stop - 1
            item = dict(segment)
            item.update(
                {
                    "dataset_id": dataset_id,
                    "recording_id": recording_id,
                    "subject_id": subject_id,
                    "pid": pid,
                    "first_epoch_id": int(epoch_ids[first]),
                    "last_epoch_id": int(epoch_ids[last]),
                    "stage_codes": json.dumps(sorted(int(x) for x in np.unique(stage[first:stop]))),
                }
            )
            for internal in ("first_index", "last_index_exclusive", "first_epoch_id_index", "last_epoch_id_index"):
                item.pop(internal, None)
            segment_rows.append(item)

        pair_rows = []
        for row in support_rows:
            pair_rows.append(
                {
                    "dataset_id": dataset_id,
                    "recording_id": recording_id,
                    "subject_id": subject_id,
                    "pid": pid,
                    **row,
                    "temporal_support_status": temporal_status,
                    "source_quality_status": quality_status,
                    "pair_count_scope": "timestamp_contiguous_and_h5_qc_only",
                }
            )

        window_rows = [
            {
                "dataset_id": dataset_id,
                "recording_id": recording_id,
                "subject_id": subject_id,
                "pid": pid,
                "epoch_id": int(epoch_ids[index]),
                "window_start_sec": float(starts[index]),
                "window_end_sec": float(ends[index]),
                "window_center_sec": float((starts[index] + ends[index]) / 2.0),
                "segment_id": int(segment_ids[index]),
                "stage_code": int(stage[index]),
                "stage_label": STAGE_LABELS.get(int(stage[index]), f"unmapped_{int(stage[index])}"),
                "valid_3d_by_h5_qc": bool(valid3[index]),
                "valid_9d_by_h5_qc": bool(valid9[index]),
                "temporal_support_status": temporal_status,
                "source_quality_status": quality_status,
            }
            for index in range(n)
        ]

        segment_durations = [float(row["duration_sec"]) for row in segments]
        row = {
            "dataset_id": dataset_id,
            "recording_id": recording_id,
            "subject_id": subject_id,
            "pid": pid,
            "n_windows": n,
            "n_stage_codes": int(len(np.unique(stage))),
            "n_segments": len(segments),
            "n_timestamp_gaps": gap_count,
            "timestamp_gap_duration_sec": gap_sec,
            "n_overlapping_edges": overlap_count,
            "window_duration_min_sec": float(window_durations.min()) if n else 0.0,
            "window_duration_median_sec": float(np.median(window_durations)) if n else 0.0,
            "window_duration_max_sec": float(window_durations.max()) if n else 0.0,
            "contiguous_center_step_median_sec": (
                float(np.median(contiguous_center_steps)) if contiguous_center_steps.size else None
            ),
            "contiguous_center_step_min_sec": (
                float(contiguous_center_steps.min()) if contiguous_center_steps.size else None
            ),
            "contiguous_center_step_max_sec": (
                float(contiguous_center_steps.max()) if contiguous_center_steps.size else None
            ),
            "segment_duration_min_sec": min(segment_durations) if segment_durations else 0.0,
            "segment_duration_median_sec": float(np.median(segment_durations)) if segment_durations else 0.0,
            "segment_duration_max_sec": max(segment_durations) if segment_durations else 0.0,
            "observed_segment_duration_sum_sec": float(sum(segment_durations)),
            "n_valid_3d_windows": int(valid3.sum()),
            "n_valid_9d_windows": int(valid9.sum()),
            "stage_source_column": stage_audit.get("source_stage_column"),
            "stage_source_audit_status": stage_audit.get("status"),
            "stage_source_sha256": stage_audit.get("source_sha256"),
            "stage_source_hash_stable_during_read": stage_audit.get("source_hash_stable_during_read"),
            "stage_midpoint_count": stage_audit.get("window_midpoint_count"),
            "stage_midpoint_covered_count": stage_audit.get("window_midpoint_covered_count"),
            "stage_label_matches": stage_audit.get("stored_label_match_count"),
            "stage_label_mismatches": stage_audit.get("stored_label_mismatch_count"),
            "stage_uncovered_labeled_windows": stage_audit.get("uncovered_labeled_window_count"),
            "stage_source_interval_overlaps": stage_audit.get("source_interval_overlap_count"),
            "stage_source_events": stage_audit.get("source_event_count"),
            "stage_source_events_skipped": stage_audit.get("source_event_count_skipped"),
            "stage_source_events_invalid_timing": stage_audit.get("source_event_count_invalid_timing"),
            "stage_source_events_unmapped": stage_audit.get("source_event_count_unmapped_stage"),
            "temporal_support_status": temporal_status,
            "source_quality_status": quality_status,
        }
    return row, segment_rows, pair_rows, window_rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def run_audit(
    input_root: str | Path,
    output_dir: str | Path,
    *,
    tolerance_sec: float = 1e-3,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Audit all HDF5 recordings under ``input_root`` without modifying them."""
    source_root = Path(input_root)
    target = Path(output_dir)
    files = sorted(source_root.rglob("*.h5"))
    if not files:
        raise FileNotFoundError(f"no HDF5 recordings beneath {source_root}")
    names = (
        "recording_temporal_support_audit.csv",
        "temporal_segments_by_recording.csv",
        "temporal_pair_support_by_recording_stage.csv",
        "window_segment_index.csv",
        "temporal_support_audit_metadata.json",
    )
    target.mkdir(parents=True, exist_ok=True)
    existing = [target / name for name in names if (target / name).exists()]
    if existing and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing outputs: {existing}")

    recording_rows: list[dict[str, Any]] = []
    segment_rows: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    window_rows: list[dict[str, Any]] = []
    for path in files:
        rec, segments, pairs, windows = _read_recording(path, tolerance_sec=tolerance_sec)
        recording_rows.append(rec)
        segment_rows.extend(segments)
        pair_rows.extend(pairs)
        window_rows.extend(windows)

    _write_csv(target / names[0], recording_rows)
    _write_csv(target / names[1], segment_rows)
    _write_csv(target / names[2], pair_rows)
    _write_csv(target / names[3], window_rows)
    metadata = {
        "schema": SCHEMA_VERSION,
        "status": "audited",
        "claim_status": "no_biological_claim",
        "scientific_qualification": "not_assessed",
        "input_root": str(source_root),
        "recording_count": len(recording_rows),
        "window_count": int(sum(row["n_windows"] for row in recording_rows)),
        "pid_count": len({row["pid"] for row in recording_rows if row["pid"] is not None}),
        "segment_count": len(segment_rows),
        "timestamp_gap_count": int(sum(row["n_timestamp_gaps"] for row in recording_rows)),
        "timestamp_gap_duration_sec": float(sum(row["timestamp_gap_duration_sec"] for row in recording_rows)),
        "stage_label_mismatch_count": int(sum(row["stage_label_mismatches"] or 0 for row in recording_rows)),
        "stage_label_uncovered_count": int(sum(row["stage_uncovered_labeled_windows"] or 0 for row in recording_rows)),
        "stage_source_event_skipped_count": int(sum(row["stage_source_events_skipped"] or 0 for row in recording_rows)),
        "stage_source_event_invalid_timing_count": int(sum(row["stage_source_events_invalid_timing"] or 0 for row in recording_rows)),
        "stage_source_event_unmapped_count": int(sum(row["stage_source_events_unmapped"] or 0 for row in recording_rows)),
        "stage_source_audit_status_counts": _counts(
            row["stage_source_audit_status"] or "unavailable" for row in recording_rows
        ),
        "temporal_support_status_counts": _counts(row["temporal_support_status"] for row in recording_rows),
        "source_quality_status_counts": _counts(row["source_quality_status"] for row in recording_rows),
        "pair_rule": "same recording; all intervening window edges touch within tolerance; every window from t through t+h passes the coordinate-specific H5 QC mask and is finite",
        "pair_count_scope": "timestamp_contiguous_and_h5_qc_only; raw-sample/effective-filter support not qualified",
        "stage_rule": "stored stage label compared with first available source column in stage_hum, stage_ai, stage, sleep_stage at each window midpoint",
        "window_edge_tolerance_sec": float(tolerance_sec),
        "horizons_rows": list(DEFAULT_HORIZONS),
        "window_duration_min_sec": min(row["window_duration_min_sec"] for row in recording_rows),
        "window_duration_max_sec": max(row["window_duration_max_sec"] for row in recording_rows),
        "contiguous_center_step_min_sec": min(
            row["contiguous_center_step_min_sec"] for row in recording_rows
            if row["contiguous_center_step_min_sec"] is not None
        ),
        "contiguous_center_step_max_sec": max(
            row["contiguous_center_step_max_sec"] for row in recording_rows
            if row["contiguous_center_step_max_sec"] is not None
        ),
        "outputs": list(names[:-1]),
    }
    step_values = [
        row["contiguous_center_step_median_sec"]
        for row in recording_rows
        if row["contiguous_center_step_median_sec"] is not None
    ]
    metadata["nominal_horizon_seconds_by_row_lag"] = (
        {
            str(horizon): float(np.median(step_values) * horizon)
            for horizon in DEFAULT_HORIZONS
        }
        if metadata["contiguous_center_step_max_sec"] - metadata["contiguous_center_step_min_sec"] <= tolerance_sec
        else None
    )
    with (target / names[4]).open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(metadata, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return metadata


def _counts(values: Iterable[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[str(value)] = result.get(str(value), 0) + 1
    return dict(sorted(result.items()))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", required=True, help="Root containing MNDM HDF5 recording files")
    parser.add_argument("--output-dir", required=True, help="Fresh output directory for support CSV/JSON files")
    parser.add_argument("--tolerance-sec", type=float, default=1e-3)
    parser.add_argument("--overwrite", action="store_true", help="Replace only the five named audit outputs")
    args = parser.parse_args(argv)
    result = run_audit(
        args.input_root,
        args.output_dir,
        tolerance_sec=args.tolerance_sec,
        overwrite=args.overwrite,
    )
    print(
        f"status={result['status']} recordings={result['recording_count']} "
        f"windows={result['window_count']} segments={result['segment_count']} "
        f"gaps={result['timestamp_gap_count']} gap_sec={result['timestamp_gap_duration_sec']:.3f} "
        f"stage_mismatches={result['stage_label_mismatch_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
