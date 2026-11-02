"""Analyze MNPS-BENCH-001 H1 outputs from the frozen NMDM HDF5 export.

This script reads only the selected, processed HDF5 recordings. It does not
load EDFs, participant tables, or event tables. The H1 analysis follows the
frozen protocol and amendment 1 in the NMD repository.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import h5py
import numpy as np
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


MIN_SUPPORTED_SEC = 60.0
MIN_COHORT = 80
OUTER_REPEATS = 20
OUTER_FOLDS = 5
INNER_FOLDS = 4
C_GRID = (0.01, 0.1, 1.0, 10.0, 100.0)
H1_V3_SCALARS = ("PCV", "TP", "NIE", "RD", "OI", "SC", "ED")
AR_FEATURES = tuple(f"AR_pair_{index:02d}" for index in range(1, 10))
H1_V3_FEATURES = ("PCV", "TP", *AR_FEATURES, "NIE", "RD", "OI", "SC", "ED")
LEGACY_FEATURES = ("m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m")
RAW_INPUT_FEATURES = (
    "eeg_delta", "eeg_theta", "eeg_alpha", "eeg_beta_alpha", "eeg_gamma",
    "eeg_hjorth_mobility", "eeg_alpha_theta", "eeg_permutation_entropy",
    "eeg_hjorth_complexity", "embodied_arousal_proxy",
)
CONVENTIONAL_FEATURES = ("delta", "theta", "alpha", "beta", "gamma")
STATES = ("EyesClosed", "EyesOpen")
ARM_FEATURES = {
    "v3_full": H1_V3_FEATURES,
    "legacy_v2": LEGACY_FEATURES,
    "raw_v2_inputs": RAW_INPUT_FEATURES,
    "conventional_relative_power": CONVENTIONAL_FEATURES,
}
V3_CANDIDATE_FOR_FEATURE = {
    "PCV": "M1", "TP": "M2", "AR": "M3", "NIE": "D1", "RD": "D3",
    "OI": "E1", "SC": "E2", "ED": "E3",
}
V3_EXPECTED_LENGTH = {candidate: 1 for candidate in V3_CANDIDATE_FOR_FEATURE.values()}
V3_EXPECTED_LENGTH["M3"] = 9
FILE_PATTERN = re.compile(
    r"(?P<subject>sub-\d+).*?ses-1.*?task-(?P<state>EyesClosed|EyesOpen).*?acq-pre.*?\.edf$",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class InnerFold:
    train_local: np.ndarray
    valid_local: np.ndarray


@dataclass(frozen=True)
class OuterFold:
    train: np.ndarray
    test: np.ndarray
    inner: tuple[InnerFold, ...]


@dataclass(frozen=True)
class Recording:
    subject: str
    state: str
    raw_file: str
    features: Mapping[str, Mapping[str, float]]
    coverage: tuple[Mapping[str, Any], ...]
    qc: Mapping[str, Any]


def _decode(value: Any) -> str:
    if isinstance(value, (bytes, np.bytes_)):
        return value.decode("utf-8")
    return str(value)


def _decode_names(dataset: h5py.Dataset) -> list[str]:
    return [_decode(item) for item in np.asarray(dataset).reshape(-1)]


def _json_dataset(dataset: h5py.Dataset) -> Any:
    return json.loads(_decode(dataset[()]))


def union_duration(intervals: Iterable[tuple[float, float]]) -> float:
    """Return total duration of the union of valid half-open intervals."""
    valid = sorted((float(start), float(end)) for start, end in intervals
                   if np.isfinite(start) and np.isfinite(end) and end > start)
    if not valid:
        return 0.0
    total = 0.0
    left, right = valid[0]
    for start, end in valid[1:]:
        if start <= right:
            right = max(right, end)
        else:
            total += right - left
            left, right = start, end
    return float(total + right - left)


def minimum_union_duration_for_count(
    intervals: Sequence[tuple[float, float]],
    count: int,
) -> float:
    """Lower-bound supported time when only the finite-window count is saved.

    Conventional tier-1 summaries store a per-recording median and finite `n`,
    not a per-window validity vector. This dynamic program finds the smallest
    possible union among any `count` intervals on the saved window grid, so a
    support pass is guaranteed even when the locations of finite windows are
    unavailable.
    """
    valid = sorted(
        (float(start), float(end)) for start, end in intervals
        if np.isfinite(start) and np.isfinite(end) and end > start
    )
    if count <= 0 or count > len(valid):
        return 0.0
    if count == 1:
        return min(end - start for start, end in valid)

    inf = float("inf")
    dp = [[inf] * (count + 1) for _ in valid]
    for i, (start, end) in enumerate(valid):
        dp[i][1] = end - start
        for k in range(2, min(count, i + 1) + 1):
            for j in range(i):
                previous_end = valid[j][1]
                added = max(0.0, end - max(start, previous_end))
                dp[i][k] = min(dp[i][k], dp[j][k - 1] + added)
    return float(min(row[count] for row in dp))


def _conventional_summary_features(
    relative: h5py.Group,
    intervals: Sequence[tuple[float, float]],
    *,
    subject: str,
    state: str,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    """Read frozen tier-1 per-recording medians and conservatively audit support."""
    features: dict[str, float] = {}
    coverage: list[dict[str, Any]] = []
    for name in CONVENTIONAL_FEATURES:
        finite_windows = 0
        value = math.nan
        reason = "summary_missing"
        if name in relative and isinstance(relative[name], h5py.Group):
            band = relative[name]
            try:
                finite_windows = int(np.asarray(band["n"][()]).item())
                value = float(np.asarray(band["median"][()]).item())
                reason = "nonfinite_recording_median" if not np.isfinite(value) else ""
            except (KeyError, TypeError, ValueError, OverflowError):
                finite_windows = 0
                value = math.nan
                reason = "summary_statistic_or_count_missing"

        supported_seconds = minimum_union_duration_for_count(intervals, finite_windows)
        support_pass = (
            np.isfinite(value)
            and 0 < finite_windows <= len(intervals)
            and supported_seconds >= MIN_SUPPORTED_SEC
        )
        if not support_pass and not reason:
            reason = (
                "finite_window_count_exceeds_time_grid"
                if finite_windows > len(intervals)
                else "conservative_unique_supported_time_below_60_seconds"
            )
        features[name] = value if support_pass else math.nan
        coverage.append({
            "subject": subject,
            "state": state,
            "arm": "conventional_relative_power",
            "feature": name,
            "finite_window_count": finite_windows,
            "total_window_count": len(intervals),
            "supported_seconds": supported_seconds,
            "minimum_supported_seconds": MIN_SUPPORTED_SEC,
            "support_pass": bool(support_pass),
            "support_basis": "minimum_possible_interval_union_for_saved_finite_window_count",
            "reason": None if support_pass else reason,
        })
    return features, coverage


def _supported_aggregate(
    name: str,
    values: Sequence[Any],
    intervals: Sequence[tuple[float, float]],
    *,
    subject: str,
    state: str,
    arm: str,
    min_supported_sec: float = MIN_SUPPORTED_SEC,
    expected_size: int = 1,
    prevalidated: Sequence[bool] | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Median finite windows, retaining the exact support interval union."""
    usable: list[tuple[np.ndarray, tuple[float, float]]] = []
    for index, value in enumerate(values):
        if prevalidated is not None and not bool(prevalidated[index]):
            continue
        try:
            vector = np.asarray(value, dtype=np.float64).reshape(-1)
        except (TypeError, ValueError):
            continue
        if vector.size != expected_size or not np.isfinite(vector).all():
            continue
        start, end = intervals[index]
        if not (np.isfinite(start) and np.isfinite(end) and end > start):
            continue
        usable.append((vector, (float(start), float(end))))
    seconds = union_duration(interval for _, interval in usable)
    supported = seconds >= min_supported_sec
    if supported and usable:
        aggregate = np.median(np.stack([value for value, _ in usable]), axis=0)
    else:
        aggregate = np.full(expected_size, np.nan, dtype=np.float64)
    record = {
        "subject": subject,
        "state": state,
        "arm": arm,
        "feature": name,
        "finite_window_count": len(usable),
        "total_window_count": len(values),
        "supported_seconds": seconds,
        "minimum_supported_seconds": min_supported_sec,
        "support_pass": bool(supported),
        "reason": None if supported else "unique_supported_time_below_60_seconds",
    }
    return aggregate, record


def _row_source_file(h5: h5py.File) -> str:
    raw = np.asarray(h5["row_source/raw_file"]).reshape(-1)
    if raw.size == 0:
        raise ValueError("HDF5 row_source/raw_file is empty")
    return _decode(raw[0])


def _recording_qc(h5: h5py.File, *, raw_file: str, subject: str, state: str) -> dict[str, Any]:
    payloads = _json_dataset(h5["measurements/v3_1/recordings_json"])
    measurement_payload = payloads[0]["measurement_payload"] if payloads else {}
    windows = measurement_payload.get("windows", [])
    first_window = windows[0] if windows else {}
    realization = first_window.get("realization", {})
    measurement_rows = [
        row for window in windows for row in window.get("measurements", [])
        if isinstance(row, Mapping)
    ]
    detail_rows = [row.get("details", {}) for row in measurement_rows if isinstance(row.get("details"), Mapping)]
    detail = next((row for row in detail_rows if row.get("channel_set_sha256")), {})
    support_audit_counts: dict[str, int] = {}
    filter_support_counts: dict[str, int] = {}
    for window in windows:
        status = str(window.get("support_audit_status", "not_recorded"))
        support_audit_counts[status] = support_audit_counts.get(status, 0) + 1
    for row in measurement_rows:
        support_qc = row.get("details", {}).get("filter_support_qc", {}) if isinstance(row.get("details"), Mapping) else {}
        status = str(support_qc.get("effective_filter_support_status", "not_recorded")) if isinstance(support_qc, Mapping) else "not_recorded"
        filter_support_counts[status] = filter_support_counts.get(status, 0) + 1

    technical_rows: list[Mapping[str, Any]] = []
    status_group_path = "extensions/conventional_eeg/row_level_status"
    if status_group_path in h5 and "rows_json" in h5[status_group_path]:
        raw_status = _json_dataset(h5[f"{status_group_path}/rows_json"])
        technical_rows = [row for row in raw_status if isinstance(row, Mapping)]
    technical_status_counts: dict[str, int] = {}
    for row in technical_rows:
        status = str(row.get("technical_eeg_status", "not_recorded"))
        technical_status_counts[status] = technical_status_counts.get(status, 0) + 1
    channel_labels = realization.get("channel_labels", []) if isinstance(realization, Mapping) else []
    acquisition_qc = detail.get("acquisition_qc", {}) if isinstance(detail, Mapping) else {}
    return {
        "subject": subject,
        "state": state,
        "raw_file": raw_file,
        "v3_window_count": len(windows),
        "legacy_window_count": len(h5["window_start"]),
        "eeg_channel_count": len(channel_labels) or detail.get("channel_count"),
        "ordered_channel_labels_json": json.dumps(channel_labels, ensure_ascii=False),
        "channel_order_sha256": detail.get("channel_order_sha256"),
        "channel_set_sha256": detail.get("channel_set_sha256"),
        "reference_mode": detail.get("input_reference_mode"),
        "reference_set_sha256": detail.get("reference_set_sha256"),
        "input_filter_band_hz_json": json.dumps(detail.get("input_filter_band_hz"), ensure_ascii=False),
        "support_audit_status_counts_json": json.dumps(support_audit_counts, sort_keys=True),
        "effective_filter_support_status_counts_json": json.dumps(filter_support_counts, sort_keys=True),
        "technical_eeg_status_counts_json": json.dumps(technical_status_counts, sort_keys=True),
        "technical_qc_row_count": len(technical_rows),
        "technical_gap_count": int(sum(int(row.get("technical_eeg_gap_count", 0) or 0) for row in technical_rows)),
        "technical_flatline_channel_count": int(sum(int(row.get("technical_eeg_flatline_channel_count", 0) or 0) for row in technical_rows)),
        "acquisition_qc_json": json.dumps(acquisition_qc, ensure_ascii=False, sort_keys=True),
    }


def _get_v3_features(
    h5: h5py.File,
    *,
    subject: str,
    state: str,
    coverage_rows: list[dict[str, Any]],
) -> dict[str, float]:
    payloads = _json_dataset(h5["measurements/v3_1/recordings_json"])
    if len(payloads) != 1:
        raise ValueError("Expected one recording payload per selected H1 HDF5 file")
    measurement_payload = payloads[0]["measurement_payload"]
    windows = measurement_payload.get("windows", [])
    # v3.1 has its own 20-second grid; top-level window_start/window_end align
    # with the separate legacy 8-second feature grid.
    intervals = [
        (float(window.get("window_start_sec", math.nan)),
         float(window.get("window_end_sec", math.nan)))
        for window in windows
    ]

    rows_by_candidate: dict[str, list[Any]] = {key: [] for key in V3_CANDIDATE_FOR_FEATURE.values()}
    for window in windows:
        values_for_window = {
            str(row.get("candidate_id")): row
            for row in window.get("measurements", [])
            if isinstance(row, Mapping)
        }
        for candidate in rows_by_candidate:
            row = values_for_window.get(candidate)
            rows_by_candidate[candidate].append(row)

    result: dict[str, float] = {}
    for feature in H1_V3_SCALARS:
        candidate = V3_CANDIDATE_FOR_FEATURE[feature]
        entries = rows_by_candidate[candidate]
        vals = [entry.get("value") if entry is not None else None for entry in entries]
        valid = [bool(entry and entry.get("computed") and entry.get("valid")) for entry in entries]
        aggregate, coverage = _supported_aggregate(
            feature, vals, intervals, subject=subject, state=state, arm="v3_full",
            expected_size=1, prevalidated=valid,
        )
        coverage_rows.append(coverage)
        result[feature] = float(aggregate[0])

    entries = rows_by_candidate["M3"]
    vals = [entry.get("value") if entry is not None else None for entry in entries]
    valid = [bool(entry and entry.get("computed") and entry.get("valid")) for entry in entries]
    aggregate, coverage = _supported_aggregate(
        "AR_vector", vals, intervals, subject=subject, state=state, arm="v3_full",
        expected_size=9, prevalidated=valid,
    )
    coverage_rows.append(coverage)
    result.update({name: float(value) for name, value in zip(AR_FEATURES, aggregate, strict=True)})
    return result


def _column_features(
    values: np.ndarray,
    names: Sequence[str],
    requested: Sequence[str],
    intervals: Sequence[tuple[float, float]],
    *,
    subject: str,
    state: str,
    arm: str,
    coverage_rows: list[dict[str, Any]],
    row_valid: Sequence[bool] | None = None,
) -> dict[str, float]:
    matrix = np.asarray(values)
    if matrix.ndim != 2 or matrix.shape[0] != len(intervals):
        raise ValueError(f"{arm} matrix must be rows x features and align with the HDF5 time grid")
    if matrix.shape[1] != len(names):
        raise ValueError(f"{arm} feature-name count does not match its value matrix")
    positions = {str(name): index for index, name in enumerate(names)}
    result: dict[str, float] = {}
    for feature in requested:
        if feature not in positions:
            raise ValueError(f"Required {arm} feature is missing: {feature}")
        vector = matrix[:, positions[feature]]
        mask = np.isfinite(vector)
        if row_valid is not None:
            mask &= np.asarray(row_valid, dtype=bool)
        chosen = [float(vector[i]) if mask[i] else None for i in range(len(vector))]
        aggregate, coverage = _supported_aggregate(
            feature, chosen, intervals, subject=subject, state=state, arm=arm,
        )
        coverage_rows.append(coverage)
        result[feature] = float(aggregate[0])
    return result


def load_h1_recording(path: Path) -> Recording:
    """Read one processed HDF5 recording and build prespecified H1 vectors."""
    coverage_rows: list[dict[str, Any]] = []
    with h5py.File(path, "r") as h5:
        raw_file = _row_source_file(h5)
        match = FILE_PATTERN.search(Path(raw_file).name)
        if not match:
            raise ValueError(f"Not a session-1 acq-pre EO/EC file: {raw_file}")
        subject = match.group("subject")
        state_raw = match.group("state")
        state = "EyesClosed" if state_raw.lower() == "eyesclosed" else "EyesOpen"
        qc = _recording_qc(h5, raw_file=raw_file, subject=subject, state=state)
        starts = np.asarray(h5["window_start"], dtype=np.float64).reshape(-1)
        ends = np.asarray(h5["window_end"], dtype=np.float64).reshape(-1)
        if starts.shape != ends.shape:
            raise ValueError("HDF5 window start/end shapes do not match")
        intervals = list(zip(starts.tolist(), ends.tolist(), strict=True))

        v3 = _get_v3_features(
            h5, subject=subject, state=state,
            coverage_rows=coverage_rows,
        )

        legacy_values = np.asarray(h5["coords_9d/values"], dtype=np.float64)
        legacy_names = _decode_names(h5["coords_9d/names"])
        legacy_valid = np.asarray(h5["qc/windows/coords_9d_valid"], dtype=bool).reshape(-1)
        legacy = _column_features(
            legacy_values, legacy_names, LEGACY_FEATURES, intervals,
            subject=subject, state=state, arm="legacy_v2",
            coverage_rows=coverage_rows, row_valid=legacy_valid,
        )

        raw_values = np.asarray(h5["features_raw/values"], dtype=np.float64)
        raw_names = _decode_names(h5["features_raw/names"])
        raw_inputs = _column_features(
            raw_values, raw_names, RAW_INPUT_FEATURES, intervals,
            subject=subject, state=state, arm="raw_v2_inputs",
            coverage_rows=coverage_rows,
        )

        relative = h5["extensions/conventional_eeg/families/relative"]
        conventional, conventional_coverage = _conventional_summary_features(
            relative,
            intervals,
            subject=subject,
            state=state,
        )
        coverage_rows.extend(conventional_coverage)

    return Recording(
        subject=subject,
        state=state,
        raw_file=raw_file,
        features={
            "v3_full": v3,
            "legacy_v2": legacy,
            "raw_v2_inputs": raw_inputs,
            "conventional_relative_power": conventional,
        },
        coverage=tuple(coverage_rows),
        qc=qc,
    )


def load_selected_subjects(selection_manifest: Path) -> list[str]:
    manifest = json.loads(selection_manifest.read_text(encoding="utf-8"))
    subjects = manifest.get("selection", {}).get("subjects")
    if not isinstance(subjects, list) or len(subjects) != 100:
        raise ValueError("Selection manifest must contain exactly 100 frozen subjects")
    if len(set(subjects)) != 100:
        raise ValueError("Selection manifest has duplicate subject IDs")
    return [str(subject) for subject in subjects]


def load_run(run_dir: Path, selected_subjects: Sequence[str]) -> tuple[dict[tuple[str, str], Recording], list[dict[str, Any]]]:
    files = sorted(run_dir.rglob("*.h5"))
    expected = len(selected_subjects) * 2
    if len(files) != expected:
        raise ValueError(f"Expected exactly {expected} H1 HDF5 recordings; found {len(files)}")
    selected = set(selected_subjects)
    records: dict[tuple[str, str], Recording] = {}
    coverage: list[dict[str, Any]] = []
    for path in files:
        recording = load_h1_recording(path)
        if recording.subject not in selected:
            raise ValueError(f"Non-selected subject appeared in analysis output: {recording.subject}")
        key = (recording.subject, recording.state)
        if key in records:
            raise ValueError(f"Duplicate processed recording for {key}")
        records[key] = recording
        coverage.extend(recording.coverage)
    expected_keys = {(subject, state) for subject in selected_subjects for state in STATES}
    if set(records) != expected_keys:
        missing = sorted(expected_keys - set(records))
        extra = sorted(set(records) - expected_keys)
        raise ValueError(f"H1 output pairing mismatch; missing={missing[:5]}, extra={extra[:5]}")
    return records, coverage


def complete_subjects(
    records: Mapping[tuple[str, str], Recording],
    selected_subjects: Sequence[str],
    arms: Sequence[str],
) -> list[str]:
    complete: list[str] = []
    for subject in selected_subjects:
        valid = True
        for state in STATES:
            recording = records[(subject, state)]
            for arm in arms:
                values = np.asarray([recording.features[arm][name] for name in ARM_FEATURES[arm]])
                if not np.isfinite(values).all():
                    valid = False
                    break
            if not valid:
                break
        if valid:
            complete.append(subject)
    return complete


def summarize_cohort_support(
    coverage: Sequence[Mapping[str, Any]],
    subjects: Sequence[str],
    states: Sequence[str],
    arms: Sequence[str],
    *,
    contrast: str,
    stage: str,
) -> list[dict[str, Any]]:
    subject_set = set(subjects)
    state_set = set(states)
    arm_set = set(arms)
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = {}
    for row in coverage:
        if row["subject"] in subject_set and row["state"] in state_set and row["arm"] in arm_set:
            key = (str(row["arm"]), str(row["feature"]), str(row["state"]))
            grouped.setdefault(key, []).append(row)
    summaries: list[dict[str, Any]] = []
    for (arm, feature, state), rows in sorted(grouped.items()):
        support_seconds = [float(row["supported_seconds"]) for row in rows]
        finite_windows = [int(row["finite_window_count"]) for row in rows]
        total_windows = [int(row["total_window_count"]) for row in rows]
        passing = sum(bool(row["support_pass"]) for row in rows)
        summaries.append({
            "contrast": contrast,
            "stage": stage,
            "arm": arm,
            "feature": feature,
            "state": state,
            "n_recordings": len(rows),
            "n_recordings_meeting_support": passing,
            "support_pass_fraction": passing / len(rows) if rows else math.nan,
            "median_supported_seconds": float(np.median(support_seconds)) if rows else math.nan,
            "minimum_supported_seconds": float(np.min(support_seconds)) if rows else math.nan,
            "maximum_supported_seconds": float(np.max(support_seconds)) if rows else math.nan,
            "median_finite_windows": float(np.median(finite_windows)) if rows else math.nan,
            "median_total_windows": float(np.median(total_windows)) if rows else math.nan,
        })
    return summaries


def summarize_realizations(
    records: Mapping[tuple[str, str], Recording],
    subjects: Sequence[str],
    *,
    contrast: str,
    stage: str,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], set[str]] = {}
    for subject in subjects:
        for state in STATES:
            qc = records[(subject, state)].qc
            key = (
                state,
                str(qc.get("eeg_channel_count")),
                str(qc.get("channel_set_sha256")),
                str(qc.get("reference_mode")),
                str(qc.get("reference_set_sha256")),
            )
            grouped.setdefault(key, set()).add(subject)
    return [{
        "contrast": contrast,
        "stage": stage,
        "state": key[0],
        "eeg_channel_count": key[1],
        "channel_set_sha256": key[2],
        "reference_mode": key[3],
        "reference_set_sha256": key[4],
        "n_participants": len(subjects_for_key),
    } for key, subjects_for_key in sorted(grouped.items())]


def matrix_for_arm(
    records: Mapping[tuple[str, str], Recording],
    subjects: Sequence[str],
    arm: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows: list[list[float]] = []
    labels: list[int] = []
    groups: list[str] = []
    for subject in subjects:
        for state, label in (("EyesClosed", 0), ("EyesOpen", 1)):
            values = records[(subject, state)].features[arm]
            rows.append([float(values[name]) for name in ARM_FEATURES[arm]])
            labels.append(label)
            groups.append(subject)
    return np.asarray(rows, dtype=np.float64), np.asarray(labels, dtype=np.int8), np.asarray(groups)


def paired_auc_by_subject(
    labels: Sequence[int],
    groups: Sequence[str],
    probabilities: Sequence[float],
) -> dict[str, float]:
    labels_array = np.asarray(labels, dtype=np.int8)
    groups_array = np.asarray(groups)
    probs = np.asarray(probabilities, dtype=np.float64)
    scores: dict[str, float] = {}
    for subject in dict.fromkeys(groups_array.tolist()):
        idx = np.flatnonzero(groups_array == subject)
        if idx.size != 2 or set(labels_array[idx].tolist()) != {0, 1}:
            raise ValueError(f"Expected one held-out observation per state for {subject}")
        p_closed = probs[idx[labels_array[idx] == 0][0]]
        p_open = probs[idx[labels_array[idx] == 1][0]]
        scores[str(subject)] = 1.0 if p_open > p_closed else 0.0 if p_open < p_closed else 0.5
    return scores


def make_split_schedule(
    subjects: Sequence[str],
    *,
    n_repeats: int = OUTER_REPEATS,
    n_outer: int = OUTER_FOLDS,
    n_inner: int = INNER_FOLDS,
) -> tuple[tuple[OuterFold, ...], ...]:
    """Precompute identical grouped folds for every arm in one contrast."""
    y = np.tile(np.asarray([0, 1], dtype=np.int8), len(subjects))
    groups = np.repeat(np.asarray(subjects), 2)
    dummy = np.zeros((len(y), 1), dtype=np.float64)
    schedules: list[tuple[OuterFold, ...]] = []
    for repeat_index in range(n_repeats):
        outer_seed = 20261007 + repeat_index
        outer_splitter = StratifiedGroupKFold(n_splits=n_outer, shuffle=True, random_state=outer_seed)
        repeat_folds: list[OuterFold] = []
        for outer_fold, (train, test) in enumerate(outer_splitter.split(dummy, y, groups)):
            if set(groups[train]) & set(groups[test]):
                raise AssertionError("Outer split leaked participant groups")
            inner_seed = 20271007 + 100 * repeat_index + outer_fold
            inner_splitter = StratifiedGroupKFold(n_splits=n_inner, shuffle=True, random_state=inner_seed)
            train_dummy = np.zeros((len(train), 1), dtype=np.float64)
            inner_folds: list[InnerFold] = []
            for inner_train, inner_valid in inner_splitter.split(train_dummy, y[train], groups[train]):
                if set(groups[train][inner_train]) & set(groups[train][inner_valid]):
                    raise AssertionError("Inner split leaked participant groups")
                inner_folds.append(InnerFold(inner_train, inner_valid))
            repeat_folds.append(OuterFold(train, test, tuple(inner_folds)))
        schedules.append(tuple(repeat_folds))
    return tuple(schedules)


def _model(c_value: float):
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(
            C=float(c_value), penalty="l2", class_weight=None, solver="lbfgs",
            max_iter=5000,
        ),
    )


def nested_grouped_cv(
    matrix: np.ndarray,
    labels: np.ndarray,
    groups: np.ndarray,
    schedule: Sequence[Sequence[OuterFold]],
) -> dict[str, Any]:
    """Run the frozen repeated nested grouped CV and keep row predictions."""
    prediction_repeats = np.full((len(schedule), len(labels)), np.nan, dtype=np.float64)
    choices: list[dict[str, Any]] = []
    for repeat_index, folds in enumerate(schedule):
        for outer_fold_index, fold in enumerate(folds):
            best_c = C_GRID[0]
            best_score = -np.inf
            for c_value in C_GRID:
                inner_predictions = np.full(len(fold.train), np.nan, dtype=np.float64)
                for inner in fold.inner:
                    train_global = fold.train[inner.train_local]
                    valid_global = fold.train[inner.valid_local]
                    estimator = _model(c_value)
                    estimator.fit(matrix[train_global], labels[train_global])
                    inner_predictions[inner.valid_local] = estimator.predict_proba(matrix[valid_global])[:, 1]
                if not np.isfinite(inner_predictions).all():
                    raise ValueError("Inner CV did not generate exactly one prediction per validation row")
                score = float(np.mean(list(paired_auc_by_subject(
                    labels[fold.train], groups[fold.train], inner_predictions,
                ).values())))
                if score > best_score:  # ascending grid retains the smallest C on exact ties
                    best_score = score
                    best_c = c_value
            estimator = _model(best_c)
            estimator.fit(matrix[fold.train], labels[fold.train])
            prediction_repeats[repeat_index, fold.test] = estimator.predict_proba(matrix[fold.test])[:, 1]
            choices.append({
                "repeat_index": repeat_index,
                "outer_fold": outer_fold_index,
                "selected_C": float(best_c),
                "inner_participant_paired_auc": float(best_score),
            })
    if not np.isfinite(prediction_repeats).all():
        raise ValueError("Outer CV did not produce one out-of-fold prediction per row and repeat")
    mean_probability = np.mean(prediction_repeats, axis=0)
    scores = paired_auc_by_subject(labels, groups, mean_probability)
    y = np.asarray(labels, dtype=np.int8)
    predicted = (mean_probability >= 0.5).astype(np.int8)
    sensitivity = float(np.mean(predicted[y == 1] == 1))
    specificity = float(np.mean(predicted[y == 0] == 0))
    return {
        "predictions_by_repeat": prediction_repeats,
        "mean_probability": mean_probability,
        "participant_auc": scores,
        "paired_auc": float(np.mean(list(scores.values()))),
        "balanced_accuracy": (sensitivity + specificity) / 2.0,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "c_choices": choices,
    }


def paired_bootstrap_interval(
    participant_differences: Sequence[float],
    *,
    n_draws: int = 2000,
    seed: int = 20261008,
) -> tuple[float, float]:
    values = np.asarray(participant_differences, dtype=np.float64)
    if values.size == 0 or not np.isfinite(values).all():
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, values.size, size=(n_draws, values.size))
    means = np.mean(values[draws], axis=1)
    return tuple(float(x) for x in np.percentile(means, [2.5, 97.5]))


def sign_flip_p_value(
    differences: Sequence[float],
    *,
    n_draws: int = 100_000,
    rng: np.random.Generator | None = None,
    chunk_size: int = 5000,
) -> float:
    values = np.asarray(differences, dtype=np.float64)
    if values.size == 0 or not np.isfinite(values).all():
        return 1.0
    if rng is None:
        rng = np.random.default_rng(20261010)
    observed = abs(float(np.mean(values)))
    at_least_as_extreme = 0
    remaining = n_draws
    while remaining:
        count = min(chunk_size, remaining)
        signs = rng.choice(np.asarray([-1.0, 1.0]), size=(count, values.size))
        randomized = np.abs(signs @ values / values.size)
        at_least_as_extreme += int(np.count_nonzero(randomized >= observed))
        remaining -= count
    return float((at_least_as_extreme + 1) / (n_draws + 1))


def holm_adjust(p_values: Sequence[float]) -> np.ndarray:
    values = np.asarray(p_values, dtype=np.float64)
    adjusted = np.ones_like(values)
    order = np.argsort(values, kind="mergesort")
    running = 0.0
    count = len(values)
    for rank, index in enumerate(order):
        running = max(running, (count - rank) * float(values[index]))
        adjusted[index] = min(1.0, running)
    return adjusted


def spearman_pairs(matrix: np.ndarray, feature_names: Sequence[str], *, scope: str) -> list[dict[str, Any]]:
    correlation = stats.spearmanr(np.asarray(matrix, dtype=np.float64), axis=0).statistic
    correlation = np.asarray(correlation)
    if correlation.ndim == 0:
        correlation = np.asarray([[1.0]])
    result: list[dict[str, Any]] = []
    for i, left in enumerate(feature_names):
        for j in range(i + 1, len(feature_names)):
            result.append({
                "scope": scope,
                "feature_a": left,
                "feature_b": feature_names[j],
                "spearman_rho": float(correlation[i, j]),
            })
    return result


def pca_spectrum(matrix: np.ndarray, feature_names: Sequence[str], *, scope: str) -> list[dict[str, Any]]:
    data = np.asarray(matrix, dtype=np.float64)
    if data.ndim != 2 or data.shape[0] < 2:
        return []
    centered = data - np.mean(data, axis=0, keepdims=True)
    scale = np.std(centered, axis=0, ddof=1, keepdims=True)
    scale[~np.isfinite(scale) | (scale == 0.0)] = 1.0
    standardized = centered / scale
    covariance = standardized.T @ standardized / (data.shape[0] - 1)
    eigenvalues = np.maximum(np.linalg.eigvalsh(covariance)[::-1], 0.0)
    total = float(np.sum(eigenvalues))
    proportions = eigenvalues / total if total > 0 else np.zeros_like(eigenvalues)
    nonzero = proportions > 0
    effective_rank = float(np.exp(-np.sum(proportions[nonzero] * np.log(proportions[nonzero])))) if np.any(nonzero) else 0.0
    rank_tolerance = float(np.max(eigenvalues) * max(data.shape) * np.finfo(float).eps) if eigenvalues.size else 0.0
    numerical_rank = int(np.count_nonzero(eigenvalues > rank_tolerance))
    return [{
        "scope": scope,
        "component": index + 1,
        "eigenvalue": float(eigenvalue),
        "variance_fraction": float(proportions[index]),
        "effective_rank_shannon": effective_rank,
        "numerical_rank": numerical_rank,
        "n_participants": int(data.shape[0]),
        "n_features": len(feature_names),
    } for index, eigenvalue in enumerate(eigenvalues)]


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(str(key))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_analysis_freeze(
    run_dir: Path,
    selection_manifest: Path,
    execution_manifest: Path,
    protocol: Path,
    amendment: Path,
    h1_config: Path,
    out_path: Path,
) -> dict[str, Any]:
    """Hash the complete H1 output and analysis inputs before contrasts."""
    selected = load_selected_subjects(selection_manifest)
    files = sorted(run_dir.rglob("*.h5"))
    if len(files) != len(selected) * 2:
        raise ValueError(f"Expected exactly {len(selected) * 2} H1 HDF5 files; found {len(files)}")
    test_path = Path(__file__).resolve().with_name("test_analyze_h1.py")
    nmd_root = protocol.resolve().parents[3]
    nmd_code_relpaths = (
        "mndm/src/mndm/mnps/v3_1/pipeline_measurements.py",
        "mndm/src/mndm/features/eeg.py",
        "mndm/src/mndm/projection.py",
        "mndm/src/mndm/pipeline/summary.py",
        "mndm/src/mndm/pipeline/summary_io.py",
        "mndm/src/mndm/pipeline/export_contract.py",
        "mndm/src/mndm/parallel.py",
        "core/src/core/io/h5_writer.py",
    )
    nmd_code = {
        relpath: {"path": str((nmd_root / relpath).resolve()), "sha256": _sha256(nmd_root / relpath)}
        for relpath in nmd_code_relpaths
    }
    file_records = [{"path": str(path.resolve()), "sha256": _sha256(path)} for path in files]
    payload = {
        "schema": "mnps_bench_001_h1_analysis_freeze.v1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "benchmark": "MNPS-BENCH-001",
        "analysis_arm": "H1 v3.1 full versus MNPS 2.0 default",
        "run_dir": str(run_dir.resolve()),
        "execution_manifest": {"path": str(execution_manifest.resolve()), "sha256": _sha256(execution_manifest)},
        "selection_manifest": {"path": str(selection_manifest.resolve()), "sha256": _sha256(selection_manifest)},
        "protocol": {"path": str(protocol.resolve()), "sha256": _sha256(protocol)},
        "amendment_1": {"path": str(amendment.resolve()), "sha256": _sha256(amendment)},
        "h1_config": {"path": str(h1_config.resolve()), "sha256": _sha256(h1_config)},
        "analysis_script": {"path": str(Path(__file__).resolve()), "sha256": _sha256(Path(__file__).resolve())},
        "analysis_test": {"path": str(test_path), "sha256": _sha256(test_path)},
        "nmd_pipeline_code": nmd_code,
        "selected_subject_count": len(selected),
        "selected_recording_count": len(files),
        "input_h5_sha256": file_records,
        "analysis_contract": {
            "h1_v3_features": list(H1_V3_FEATURES),
            "legacy_v2_features": list(LEGACY_FEATURES),
            "min_unique_supported_seconds": MIN_SUPPORTED_SEC,
            "min_complete_participants": MIN_COHORT,
            "outer_folds": OUTER_FOLDS,
            "outer_repeats": OUTER_REPEATS,
            "inner_folds": INNER_FOLDS,
            "C_grid": list(C_GRID),
            "bootstrap_draws": 2000,
            "bootstrap_seed": 20261008,
            "coordinate_family_size": len(H1_V3_FEATURES),
            "holm_draws": 100000,
            "holm_seed": 20261010,
        },
        "software": {
            "python": __import__("platform").python_version(),
            "numpy": np.__version__,
            "h5py": h5py.__version__,
            "scikit_learn": __import__("sklearn").__version__,
            "scipy": __import__("scipy").__version__,
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def validate_analysis_freeze(
    freeze_path: Path,
    run_dir: Path,
    selection_manifest: Path,
    execution_manifest: Path,
) -> dict[str, Any]:
    """Fail closed unless code, protocol, selection, config, and H5 files match."""
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze.get("schema") != "mnps_bench_001_h1_analysis_freeze.v1":
        raise ValueError("Unknown H1 analysis freeze schema")
    if Path(freeze["run_dir"]).resolve() != run_dir.resolve():
        raise ValueError("H1 run directory differs from the frozen run directory")
    if Path(freeze["selection_manifest"]["path"]).resolve() != selection_manifest.resolve():
        raise ValueError("Selection-manifest path differs from the frozen path")
    if Path(freeze["execution_manifest"]["path"]).resolve() != execution_manifest.resolve():
        raise ValueError("Execution-manifest path differs from the frozen path")
    files = sorted(run_dir.rglob("*.h5"))
    frozen_files = {str(Path(item["path"]).resolve()): item["sha256"] for item in freeze["input_h5_sha256"]}
    if {str(path.resolve()) for path in files} != set(frozen_files):
        raise ValueError("H1 HDF5 file set changed after the analysis freeze")
    for path in files:
        if _sha256(path) != frozen_files[str(path.resolve())]:
            raise ValueError(f"H1 HDF5 changed after analysis freeze: {path}")
    expected_paths = {
        "selection_manifest": selection_manifest.resolve(),
        "execution_manifest": execution_manifest.resolve(),
        "protocol": Path(freeze["protocol"]["path"]).resolve(),
        "amendment_1": Path(freeze["amendment_1"]["path"]).resolve(),
        "h1_config": Path(freeze["h1_config"]["path"]).resolve(),
        "analysis_script": Path(__file__).resolve(),
        "analysis_test": Path(__file__).resolve().with_name("test_analyze_h1.py"),
    }
    for key, expected_path in expected_paths.items():
        item = freeze[key] if key in freeze else freeze["selection_manifest"]
        if Path(item["path"]).resolve() != expected_path:
            raise ValueError(f"Frozen {key} path changed")
        if _sha256(expected_path) != item["sha256"]:
            raise ValueError(f"Frozen {key} changed after analysis freeze")
    nmd_root = Path(freeze["protocol"]["path"]).resolve().parents[3]
    for relpath, item in freeze["nmd_pipeline_code"].items():
        code_path = Path(item["path"]).resolve()
        if code_path != (nmd_root / relpath).resolve():
            raise ValueError(f"Frozen pipeline-code path changed: {relpath}")
        if _sha256(code_path) != item["sha256"]:
            raise ValueError(f"Frozen pipeline code changed after analysis freeze: {relpath}")
    return freeze


def analyze_h1(
    run_dir: Path,
    selection_manifest: Path,
    execution_manifest: Path,
    out_dir: Path,
    *,
    freeze_manifest: Path,
    run_models: bool = True,
) -> dict[str, Any]:
    frozen = validate_analysis_freeze(freeze_manifest, run_dir, selection_manifest, execution_manifest)
    selected = load_selected_subjects(selection_manifest)
    records, coverage = load_run(run_dir, selected)
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "feature_support.csv", coverage)

    both_primary = complete_subjects(records, selected, ("v3_full", "legacy_v2"))
    coverage_summary = {
        arm: {
            "complete_paired_participants": len(complete_subjects(records, selected, (arm,))),
            "eligible_participants": len(selected),
        }
        for arm in ARM_FEATURES
    }
    coverage_summary["primary_v3_full_vs_legacy_v2"] = {
        "complete_paired_participants": len(both_primary),
        "eligible_participants": len(selected),
    }
    raw_input_complete = complete_subjects(records, selected, ("raw_v2_inputs",))
    conventional_complete = complete_subjects(records, selected, ("conventional_relative_power",))
    support_summary_rows: list[dict[str, Any]] = []
    realization_rows: list[dict[str, Any]] = []
    cohort_specs = (
        ("H1_v3_full_vs_legacy_v2", "before_complete_case_restriction", selected, ("v3_full", "legacy_v2")),
        ("H1_v3_full_vs_legacy_v2", "after_complete_case_restriction", both_primary, ("v3_full", "legacy_v2")),
        ("raw_v2_inputs_baseline", "before_complete_case_restriction", selected, ("raw_v2_inputs",)),
        ("raw_v2_inputs_baseline", "after_complete_case_restriction", raw_input_complete, ("raw_v2_inputs",)),
        ("conventional_baseline", "before_complete_case_restriction", selected, ("conventional_relative_power",)),
        ("conventional_baseline", "after_complete_case_restriction", conventional_complete, ("conventional_relative_power",)),
    )
    for contrast, stage, subjects, arms in cohort_specs:
        support_summary_rows.extend(summarize_cohort_support(
            coverage, subjects, STATES, arms, contrast=contrast, stage=stage,
        ))
        realization_rows.extend(summarize_realizations(
            records, subjects, contrast=contrast, stage=stage,
        ))
    _write_csv(out_dir / "recording_qc.csv", [records[(subject, state)].qc for subject in selected for state in STATES])
    _write_csv(out_dir / "cohort_support.csv", support_summary_rows)
    _write_csv(out_dir / "cohort_realization.csv", realization_rows)
    summary: dict[str, Any] = {
        "schema": "mnps_bench_001_h1_analysis.v1",
        "status": "coverage_only",
        "run_dir": str(run_dir),
        "analysis_freeze_sha256": _sha256(freeze_manifest),
        "execution_manifest_sha256": frozen["execution_manifest"]["sha256"],
        "selection_manifest_sha256": _sha256(selection_manifest),
        "complete_case_counts": coverage_summary,
        "minimum_confirmatory_cohort": MIN_COHORT,
        "analysis_unit": "participant; both states grouped in the same outer and inner folds",
    }

    primary_result_rows: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
    cv_choice_rows: list[dict[str, Any]] = []
    secondary_rows: list[dict[str, Any]] = []
    correlation_rows: list[dict[str, Any]] = []
    pca_rows: list[dict[str, Any]] = []
    if run_models and len(both_primary) >= MIN_COHORT:
        schedule = make_split_schedule(both_primary)
        primary_evals: dict[str, dict[str, Any]] = {}
        for arm in ("v3_full", "legacy_v2"):
            x, y, groups = matrix_for_arm(records, both_primary, arm)
            primary_evals[arm] = nested_grouped_cv(x, y, groups, schedule)
            cv_choice_rows.extend({"arm": arm, **row} for row in primary_evals[arm]["c_choices"])

        v3_auc = primary_evals["v3_full"]["participant_auc"]
        v2_auc = primary_evals["legacy_v2"]["participant_auc"]
        paired_differences = np.asarray([v3_auc[s] - v2_auc[s] for s in both_primary])
        ci_low, ci_high = paired_bootstrap_interval(paired_differences)
        primary_result_rows = [
            {
                "contrast": "H1_v3_full_minus_legacy_v2",
                "arm": "v3_full",
                "participant_paired_auc": primary_evals["v3_full"]["paired_auc"],
                "balanced_accuracy": primary_evals["v3_full"]["balanced_accuracy"],
                "sensitivity": primary_evals["v3_full"]["sensitivity"],
                "specificity": primary_evals["v3_full"]["specificity"],
                "n_participants": len(both_primary),
            },
            {
                "contrast": "H1_v3_full_minus_legacy_v2",
                "arm": "legacy_v2",
                "participant_paired_auc": primary_evals["legacy_v2"]["paired_auc"],
                "balanced_accuracy": primary_evals["legacy_v2"]["balanced_accuracy"],
                "sensitivity": primary_evals["legacy_v2"]["sensitivity"],
                "specificity": primary_evals["legacy_v2"]["specificity"],
                "n_participants": len(both_primary),
            },
            {
                "contrast": "H1_v3_full_minus_legacy_v2",
                "arm": "paired_difference",
                "participant_paired_auc": float(np.mean(paired_differences)),
                "ci95_low_conditional_on_fitted_repeated_cv": ci_low,
                "ci95_high_conditional_on_fitted_repeated_cv": ci_high,
                "n_participants": len(both_primary),
            },
        ]
        for arm, result in primary_evals.items():
            for row_index, subject in enumerate(both_primary):
                for state_index, (state, label) in enumerate((("EyesClosed", 0), ("EyesOpen", 1))):
                    index = 2 * row_index + state_index
                    prediction_rows.append({
                        "arm": arm,
                        "subject": subject,
                        "state": state,
                        "label": label,
                        "mean_out_of_fold_probability": float(result["mean_probability"][index]),
                    })
        summary["status"] = "confirmatory_h1_complete"
        summary["primary_h1"] = {
            "participant_paired_auc_difference": float(np.mean(paired_differences)),
            "conditional_bootstrap_ci95": [ci_low, ci_high],
            "bootstrap_draws": 2000,
            "bootstrap_seed": 20261008,
            "n_participants": len(both_primary),
            "folds": {"outer": OUTER_FOLDS, "repeats": OUTER_REPEATS, "inner": INNER_FOLDS},
            "C_grid": list(C_GRID),
        }

        v3_features = ARM_FEATURES["v3_full"]
        closed = np.asarray([
            [records[(subject, "EyesClosed")].features["v3_full"][name] for name in v3_features]
            for subject in both_primary
        ], dtype=np.float64)
        opened = np.asarray([
            [records[(subject, "EyesOpen")].features["v3_full"][name] for name in v3_features]
            for subject in both_primary
        ], dtype=np.float64)
        changes = opened - closed
        rng = np.random.default_rng(20261009)
        sign_rng = np.random.default_rng(20261010)
        raw_p: list[float] = []
        for index, feature in enumerate(v3_features):
            delta = changes[:, index]
            if len(delta) >= MIN_COHORT and np.isfinite(delta).all():
                ci = np.percentile(
                    np.mean(delta[rng.integers(0, len(delta), size=(2000, len(delta)))], axis=1),
                    [2.5, 97.5],
                )
                p_value = sign_flip_p_value(delta, n_draws=100_000, rng=sign_rng)
                testable = True
            else:
                ci = (math.nan, math.nan)
                p_value = 1.0
                testable = False
            raw_p.append(p_value)
            secondary_rows.append({
                "feature": feature,
                "mean_EyesOpen_minus_EyesClosed": float(np.mean(delta)) if len(delta) else math.nan,
                "ci95_low": float(ci[0]),
                "ci95_high": float(ci[1]),
                "sign_flip_p_two_sided": p_value,
                "testable": testable,
                "n_participants": len(delta),
                "bootstrap_draws": 2000,
                "bootstrap_seed": 20261009,
                "sign_flip_draws": 100_000,
                "sign_flip_seed": 20261010,
            })
        adjusted = holm_adjust(raw_p)
        for row, value in zip(secondary_rows, adjusted, strict=True):
            row["holm_p_16"] = float(value)

        correlation_rows.extend(spearman_pairs(closed, v3_features, scope="v3_full_EyesClosed"))
        correlation_rows.extend(spearman_pairs(opened, v3_features, scope="v3_full_EyesOpen"))
        correlation_rows.extend(spearman_pairs(changes, v3_features, scope="v3_full_state_change"))
        pca_rows.extend(pca_spectrum(closed, v3_features, scope="v3_full_EyesClosed"))
        pca_rows.extend(pca_spectrum(opened, v3_features, scope="v3_full_EyesOpen"))
        pca_rows.extend(pca_spectrum(changes, v3_features, scope="v3_full_state_change"))

        # Secondary arms use their own supported complete cases and the same
        # frozen classifier only when the protocol's 80-participant floor holds.
        secondary_arm_results: dict[str, Any] = {}
        for arm in ("raw_v2_inputs", "conventional_relative_power"):
            subjects = complete_subjects(records, selected, (arm,))
            arm_result: dict[str, Any] = {"n_participants": len(subjects), "status": "coverage_only"}
            if len(subjects) >= MIN_COHORT:
                arm_schedule = make_split_schedule(subjects)
                x, y, groups = matrix_for_arm(records, subjects, arm)
                evaluated = nested_grouped_cv(x, y, groups, arm_schedule)
                arm_result.update({
                    "status": "estimated",
                    "participant_paired_auc": evaluated["paired_auc"],
                    "balanced_accuracy": evaluated["balanced_accuracy"],
                    "sensitivity": evaluated["sensitivity"],
                    "specificity": evaluated["specificity"],
                })
                cv_choice_rows.extend({"arm": arm, **row} for row in evaluated["c_choices"])
                primary_result_rows.append({
                    "contrast": "secondary_baseline_only",
                    "arm": arm,
                    "participant_paired_auc": evaluated["paired_auc"],
                    "balanced_accuracy": evaluated["balanced_accuracy"],
                    "sensitivity": evaluated["sensitivity"],
                    "specificity": evaluated["specificity"],
                    "n_participants": len(subjects),
                })
            secondary_arm_results[arm] = arm_result
        summary["secondary_arms"] = secondary_arm_results
        summary["secondary_h1_feature_tests"] = {
            "family_size": len(H1_V3_FEATURES),
            "holm_family": "16 component-wise v3.1 features (seven scalar streams and nine AR pair components)",
            "n_testable": sum(bool(row["testable"]) for row in secondary_rows),
        }
    elif run_models:
        summary["status"] = "coverage_only_below_80_participants"
        summary["reason"] = "primary H1 complete-case cohort is below the frozen 80-participant minimum"
    else:
        summary["status"] = "coverage_only"
        summary["reason"] = "model fitting and confirmatory contrasts were intentionally skipped for QC-only review"

    _write_csv(out_dir / "primary_h1_results.csv", primary_result_rows)
    _write_csv(out_dir / "outer_predictions.csv", prediction_rows)
    _write_csv(out_dir / "inner_c_choices.csv", cv_choice_rows)
    _write_csv(out_dir / "v3_feature_state_changes.csv", secondary_rows)
    _write_csv(out_dir / "v3_spearman_correlations.csv", correlation_rows)
    _write_csv(out_dir / "v3_pca_spectrum.csv", pca_rows)
    (out_dir / "analysis_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8",
    )
    run_files = sorted(run_dir.rglob("*.h5"))
    input_hashes = frozen["input_h5_sha256"]
    if any(_sha256(path) != item["sha256"] for path, item in zip(run_files, input_hashes, strict=True)):
        raise ValueError("H1 source HDF5 changed while the analysis was running")
    run_manifest = {
        "schema": "mnps_bench_001_h1_run_manifest.v1",
        "analysis_script_sha256": _sha256(Path(__file__).resolve()),
        "analysis_freeze_sha256": _sha256(freeze_manifest),
        "selection_manifest_sha256": _sha256(selection_manifest),
        "h1_run_dir": str(run_dir),
        "h1_input_file_count": len(run_files),
        "h1_input_h5_sha256": input_hashes,
        "summary_status": summary["status"],
    }
    (out_dir / "run_manifest.json").write_text(
        json.dumps(run_manifest, indent=2, ensure_ascii=False), encoding="utf-8",
    )
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    freeze_parser = subparsers.add_parser("freeze", help="hash finalized inputs before contrasts")
    freeze_parser.add_argument("--h1-run-dir", required=True, type=Path)
    freeze_parser.add_argument("--selection-manifest", required=True, type=Path)
    freeze_parser.add_argument("--execution-manifest", required=True, type=Path)
    freeze_parser.add_argument("--protocol", required=True, type=Path)
    freeze_parser.add_argument("--amendment", required=True, type=Path)
    freeze_parser.add_argument("--h1-config", required=True, type=Path)
    freeze_parser.add_argument("--out", required=True, type=Path)

    analyze_parser = subparsers.add_parser("analyze", help="run the frozen H1 analysis")
    analyze_parser.add_argument("--h1-run-dir", required=True, type=Path)
    analyze_parser.add_argument("--selection-manifest", required=True, type=Path)
    analyze_parser.add_argument("--execution-manifest", required=True, type=Path)
    analyze_parser.add_argument("--freeze-manifest", required=True, type=Path)
    analyze_parser.add_argument("--out-dir", required=True, type=Path)
    analyze_parser.add_argument("--coverage-only", action="store_true", help="skip model fitting; intended for QC only")
    args = parser.parse_args(argv)
    if args.command == "freeze":
        payload = create_analysis_freeze(
            args.h1_run_dir, args.selection_manifest, args.execution_manifest,
            args.protocol, args.amendment,
            args.h1_config, args.out,
        )
        print(json.dumps({"schema": payload["schema"], "recordings": payload["selected_recording_count"], "out": str(args.out)}, indent=2))
        return 0
    freeze = validate_analysis_freeze(
        args.freeze_manifest, args.h1_run_dir, args.selection_manifest,
        args.execution_manifest,
    )
    summary = analyze_h1(
        args.h1_run_dir, args.selection_manifest, args.execution_manifest, args.out_dir,
        freeze_manifest=args.freeze_manifest,
        run_models=not args.coverage_only,
    )
    print(json.dumps({"status": summary["status"], "complete_case_counts": summary["complete_case_counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
