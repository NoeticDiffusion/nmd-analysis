"""Outcome-blind support audit for the full continuous ds005555 surface.

This audit qualifies only the frozen PPG-fallback input stratum and emits
PID-grouped MNDM fold manifests. It does not create MNPS charts or calculate
C1/C3 outcomes. Temporal support is explicitly scoped to current-window PPG
and EEG features with the recorded finite-causal FIR; EOG/run-level features
are not qualified by the aggregate MNDM support record and are excluded from
the admitted predictor scope.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from . import continuous_pilot_audit as _pilot
from .continuous_c123_estimators import build_grouped_pid_manifest


_HORIZONS = {"h1": 1, "h2": 2, "h4": 4}
_CONTEXT_STAGES = {0: "Wake", 2: "N2"}
_SOURCE_COLUMN = "embodied_arousal_proxy_source"
_PROXY_MATCH_ATOL = 1e-4
_LEDGER_ROW_CONVENTION = "half_open_0_based_source_array_indices; conservative_dependency_superset"
_NOMINAL_ROW_CONVENTION = "half_open_0_based_source_array_indices_within_nominal_window"
_FEATURE_EXPORT_COLUMNS = (
    "subject", "pid", "file", "epoch_id", "t_start", "t_end", "source_stratum",
    "eeg_delta", "eeg_theta", "eeg_alpha", "eeg_beta", "eeg_gamma",
    "eeg_highfreq_power_30_45", "eeg_alpha_theta", "eeg_beta_alpha",
    "eeg_hjorth_mobility", "eeg_hjorth_complexity", "eeg_sample_entropy",
    "eeg_permutation_entropy", "eeg_entropy_metric", "embodied_arousal_proxy",
    "embodied_arousal_proxy_source", "ppg_rate_bpm", "qc_ok_eeg", "qc_ok_ppg",
    "source_sample_mapping_status", "source_sample_mapping_reason",
    "nominal_source_sample_start", "nominal_source_sample_end_exclusive",
    "nominal_source_sample_absolute_start", "nominal_source_sample_absolute_end_exclusive",
    "source_first_samp", "source_sfreq_hz", "nominal_source_time_start_sec",
    "nominal_source_time_end_sec", "preprocessed_sample_start",
    "preprocessed_sample_end_exclusive", "preprocessed_sfreq_hz",
    "actual_sample_contributors_status", "actual_sample_contributors_reason",
    "actual_source_sample_start", "actual_source_sample_end_exclusive",
    "actual_source_time_start_sec", "actual_source_time_end_sec",
    "input_sample_finite_status", "input_sample_finite_fraction",
    "input_sample_gap_count", "input_sample_gap_spans", "input_sample_invalid_reason",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _subject_from_file(filename: str) -> str:
    match = re.search(r"sub-[A-Za-z0-9]+", Path(filename).name, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"BIDS subject identity is missing from recording filename: {filename}")
    return match.group(0).casefold()


def _mndm_subject_id(pid: str) -> str:
    value = str(pid).strip()
    if not value:
        raise ValueError("biological PID is empty")
    return f"sub-{value.zfill(3)}" if value.isdigit() else f"sub-{value}"


def _recording_source_stratum(values: Sequence[Any]) -> tuple[str, tuple[str, ...]]:
    normalized = tuple(sorted({str(value).strip() for value in values if str(value).strip() and str(value).strip().casefold() not in {"nan", "none", "<na>"}}))
    if normalized == ("ppg_rate_bpm",):
        return "pure_ppg", normalized
    if len(normalized) > 1:
        return "mixed", normalized
    if normalized == ("eog_blink_rate",):
        return "pure_eog_blink", normalized
    if normalized == ("eeg_highfreq_power_30_45",):
        return "pure_eeg_highfreq", normalized
    return "unknown_or_other", normalized


def _qualify_primary_row(
    row: Mapping[str, Any],
    *,
    stratum: str,
    base_support_ok: bool,
    base_reasons: Sequence[str],
) -> tuple[bool, bool, list[str]]:
    """Apply the frozen recording- and row-level PPG source contract."""
    reasons = list(base_reasons)
    if stratum != "pure_ppg":
        reasons.append(f"recording_source_stratum_not_pure_ppg:{stratum}")
    if str(row.get(_SOURCE_COLUMN, "")).strip() != "ppg_rate_bpm":
        reasons.append("row_proxy_source_not_ppg_rate_bpm")
    proxy = _pilot._finite(row.get("embodied_arousal_proxy"))
    ppg_rate = _pilot._finite(row.get("ppg_rate_bpm"))
    if proxy is None or ppg_rate is None:
        reasons.append("ppg_proxy_or_rate_missing")
        proxy_match = False
    else:
        proxy_match = math.isclose(proxy, ppg_rate, rel_tol=0.0, abs_tol=_PROXY_MATCH_ATOL)
        if not proxy_match:
            reasons.append("embodied_proxy_differs_from_declared_ppg_rate")
    source_ok = not any(reason.startswith((
        "recording_source_stratum_not_pure_ppg", "row_proxy_source_not_ppg_rate_bpm",
        "ppg_proxy_or_rate_missing", "embodied_proxy_differs_from_declared_ppg_rate",
    )) for reason in reasons)
    return bool(base_support_ok and source_ok), proxy_match, sorted(set(reasons))


def _participant_map(path: Path) -> tuple[dict[str, str], str]:
    table = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
    if not {"participant_id", "pid"}.issubset(table.columns):
        raise ValueError("participants.tsv must contain participant_id and pid")
    if table["participant_id"].duplicated().any():
        raise ValueError("participants.tsv has duplicate participant_id rows")
    mapping: dict[str, str] = {}
    for subject, pid in zip(table["participant_id"], table["pid"]):
        subject = str(subject).strip().casefold()
        pid = str(pid).strip()
        if not subject or not pid or pid.casefold() in {"n/a", "na", "nan", "none"}:
            raise ValueError("participants.tsv contains an empty/unmapped participant_id or pid")
        mapping[subject] = pid
    return mapping, _sha256(path)


def _contiguous_segments(rows: pd.DataFrame, window_sec: float) -> dict[tuple[str, int], int | None]:
    """Assign segments only across adjacent, fully eligible feature windows."""
    segments: dict[tuple[str, int], int | None] = {}
    next_segment = 0
    for filename, group in rows.groupby("file", sort=True):
        previous: Mapping[str, Any] | None = None
        current_segment: int | None = None
        for item in group.sort_values("epoch_id", kind="stable").to_dict(orient="records"):
            key = (str(filename), int(item["epoch_id"]))
            if not item["primary_surface_eligible"]:
                segments[key] = None
                previous = None
                current_segment = None
                continue
            start, end = _pilot._finite(item.get("t_start")), _pilot._finite(item.get("t_end"))
            contiguous = (
                previous is not None
                and int(item["epoch_id"]) == int(previous["epoch_id"]) + 1
                and _pilot._finite(previous.get("t_end")) is not None
                and start is not None
                and math.isclose(start, float(previous["t_end"]), rel_tol=0.0, abs_tol=1e-6)
                and end is not None
                and math.isclose(end - start, window_sec, rel_tol=0.0, abs_tol=1e-6)
            )
            if not contiguous:
                next_segment += 1
                current_segment = next_segment
            segments[key] = current_segment
            previous = item
    return segments


def _pair_availability(rows: pd.DataFrame, window_sec: float) -> pd.DataFrame:
    """Aggregate support-only availability; no chart values enter this step."""
    output: list[dict[str, Any]] = []
    for filename, group in rows.groupby("file", sort=True):
        ordered = group.sort_values("epoch_id", kind="stable").to_dict(orient="records")
        by_epoch = {int(row["epoch_id"]): row for row in ordered}
        if len(by_epoch) != len(ordered):
            raise ValueError(f"duplicate epoch identity in pair audit: {filename}")
        pid = str(ordered[0]["pid"])
        for horizon, lag in _HORIZONS.items():
            buckets: dict[tuple[str, str], dict[str, Any]] = {}
            for origin in ordered:
                # Candidate denominators are the preregistered pure-PPG
                # population too; other fallback strata are availability
                # diagnostics, never members of the primary candidate pool.
                if str(origin.get("source_stratum", "")) != "pure_ppg":
                    continue
                origin_id = int(origin["epoch_id"])
                stage = int(origin["stage_at_origin_code"]) if origin.get("stage_at_origin_code") is not None and not pd.isna(origin.get("stage_at_origin_code")) else None
                pure = bool(origin.get("stage_window_pure"))
                contexts: list[tuple[str, int]] = []
                if origin_id >= 2:
                    contexts.append(("C1_history2", -1))
                if pure and stage in _CONTEXT_STAGES:
                    contexts.append((f"C3_{_CONTEXT_STAGES[stage]}", stage))
                for context_name, context_stage in contexts:
                    key = (context_name, str(context_stage))
                    bucket = buckets.setdefault(key, {
                        "pid": pid,
                        "file": str(filename),
                        "model_scope": context_name,
                        "origin_stage": _CONTEXT_STAGES.get(context_stage, "all"),
                        "horizon": horizon,
                        "nominal_lag_rows": lag,
                        "candidate_origins": 0,
                        "target_present": 0,
                        "support_and_contiguity_eligible": 0,
                        "actual_horizon_min_sec": None,
                        "actual_horizon_median_sec": None,
                        "actual_horizon_max_sec": None,
                    })
                    bucket["candidate_origins"] += 1
                    target = by_epoch.get(origin_id + lag)
                    if target is None:
                        continue
                    bucket["target_present"] += 1
                    first = origin_id - 2 if context_name == "C1_history2" else origin_id
                    required_ids = list(range(first, origin_id + lag + 1))
                    path = [by_epoch.get(epoch) for epoch in required_ids]
                    if any(row is None for row in path):
                        continue
                    path_rows = [row for row in path if row is not None]
                    path_segments = {row.get("segment_id") for row in path_rows}
                    if (
                        len(path_segments) != 1
                        or None in path_segments
                        or not all(bool(row["primary_surface_eligible"]) for row in path_rows)
                    ):
                        continue
                    times_ok = True
                    for left, right in zip(path_rows, path_rows[1:]):
                        left_start, left_end = _pilot._finite(left.get("t_start")), _pilot._finite(left.get("t_end"))
                        right_start, right_end = _pilot._finite(right.get("t_start")), _pilot._finite(right.get("t_end"))
                        if (
                            left_start is None or left_end is None or right_start is None or right_end is None
                            or not math.isclose(left_end - left_start, window_sec, rel_tol=0.0, abs_tol=1e-6)
                            or not math.isclose(right_end - right_start, window_sec, rel_tol=0.0, abs_tol=1e-6)
                            or not math.isclose(left_end, right_start, rel_tol=0.0, abs_tol=1e-6)
                        ):
                            times_ok = False
                            break
                    if not times_ok:
                        continue
                    origin_end, target_end = _pilot._finite(origin.get("t_end")), _pilot._finite(target.get("t_end"))
                    if origin_end is None or target_end is None or target_end <= origin_end:
                        continue
                    horizon_sec = target_end - origin_end
                    bucket["support_and_contiguity_eligible"] += 1
                    vals = bucket.setdefault("_horizons", [])
                    vals.append(horizon_sec)
            for bucket in buckets.values():
                values = bucket.pop("_horizons", [])
                if values:
                    bucket["actual_horizon_min_sec"] = float(min(values))
                    bucket["actual_horizon_median_sec"] = float(np.median(values))
                    bucket["actual_horizon_max_sec"] = float(max(values))
                output.append(bucket)
    return pd.DataFrame(output, columns=[
        "pid", "file", "model_scope", "origin_stage", "horizon", "nominal_lag_rows",
        "candidate_origins", "target_present", "support_and_contiguity_eligible",
        "actual_horizon_min_sec", "actual_horizon_median_sec", "actual_horizon_max_sec",
    ])


def _ranges_for_rows(rows: pd.DataFrame) -> list[dict[str, Any]]:
    ranges: list[dict[str, Any]] = []
    if rows.empty:
        return ranges
    keys = ["subject", "file", "segment_id"]
    for (subject, filename, _segment_id), group in rows.groupby(keys, sort=True):
        ordered = group.sort_values(["t_start", "epoch_id"], kind="stable")
        start = float(ordered["t_start"].iloc[0])
        end = float(ordered["t_end"].iloc[-1])
        ranges.append({
            "subject_id": str(subject),
            "recording_id": str(filename),
            "start_sec": start,
            "end_sec": end,
        })
    return ranges


def _make_support_ledger(
    eligible: pd.DataFrame,
    records: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    extents: list[dict[str, Any]] = []
    for row in eligible.sort_values(["file", "epoch_id"], kind="stable").to_dict(orient="records"):
        record = records[str(row["file"])]
        source = record.get("source", {})
        source_hash = str(source.get("sha256", "")).lower()
        extents.append({
            "row_index": int(row["audit_row_index"]),
            "epoch_id": int(row["epoch_id"]),
            "raw_file": str(row["file"]),
            "recording_id": Path(str(row["file"])).stem,
            "recording_id_method": "feature_row",
            "source_file_sha256": source_hash,
            "nominal_time_start_sec": float(row["t_start"]),
            "nominal_time_end_sec": float(row["t_end"]),
            "original_sample_start": int(row["nominal_source_sample_start"]),
            "original_sample_end": int(row["nominal_source_sample_end_exclusive"]),
            "original_sample_interval_convention": _NOMINAL_ROW_CONVENTION,
            "source_sample_rate_hz": float(row["source_sfreq_hz"]),
            "sample_mapping_status": "nominal_bounds_mapped",
            "sample_mapping_reason": row.get("source_sample_mapping_reason"),
            "actual_sample_contributors_status": "finite_causal_conservative_bound",
            "actual_contributor_interval_convention": _LEDGER_ROW_CONVENTION,
            "actual_source_sample_start": int(row["actual_source_sample_start"]),
            "actual_source_sample_end_exclusive": int(row["actual_source_sample_end_exclusive"]),
            "actual_source_time_start_sec": float(row["actual_source_time_start_sec"]),
            "actual_source_time_end_sec": float(row["actual_source_time_end_sec"]),
            "input_sample_finite_status": row.get("input_sample_finite_status"),
            "input_sample_gap_count": int(row["input_sample_gap_count"]),
            "input_sample_gap_spans": [],
            "source_identity": source,
            "support_scope": "EEG current-window features with recorded causal FIR plus window-local ppg_rate_bpm only; EOG/respiration/run-level features are excluded",
        })
    execution: list[dict[str, Any]] = []
    for filename in sorted(eligible["file"].astype(str).unique()):
        scoped_record = json.loads(json.dumps(records[filename]))
        scoped_record["analysis_feature_support_scope"] = {
            "status": "qualified_for_declared_chart_inputs_only",
            "qualified_features": ["recorded EEG current-window feature family", "ppg_rate_bpm"],
            "ppg_temporal_class": "PRESENT_ONLY",
            "eeg_temporal_class": "PRESENT_ONLY_WITH_FINITE_CAUSAL_FIR_SUPPORT",
            "excluded_features": {
                "eog_*": "USES_FUTURE_OR_WHOLE_RECORDING_STATISTIC; not qualified",
                "resp_*": "UNKNOWN_OR_WITHHELD; not qualified",
                "unlisted_features": "UNKNOWN; not admitted as predictors",
            },
            "aggregate_effective_time_support_scope_not_used": "all raw modalities conservatively bounded by the union of the EEG FIR and identity-grid dependencies",
            "note": "The MNDM aggregate support statement is not extended to EOG/respiration. The ledger bounds only the fixed EEG chart inputs and window-local PPG feature used by this primary stratum.",
        }
        execution.append({"raw_file": filename, "validation_status": "valid", "validation_reason": None, "record": scoped_record})
    quality: list[dict[str, Any]] = []
    for filename in sorted(eligible["file"].astype(str).unique()):
        block = records[filename].get("source_quality_intervals", {})
        intervals = block.get("intervals", []) if isinstance(block, Mapping) else []
        for interval in intervals if isinstance(intervals, list) else []:
            if isinstance(interval, Mapping):
                item = dict(interval)
                item.setdefault("raw_file", filename)
                item.setdefault("source_file_sha256", str(records[filename].get("source", {}).get("sha256", "")).lower())
                quality.append(item)
    return {
        "schema": "mndm.signal_support_export.v1",
        "status": "recorded" if extents else "unknown",
        "temporal_support_status": "finite_causal_conservative_bound" if extents and execution else "unknown",
        "temporal_support_reason": "Support applies only to the fixed EEG chart inputs and present-window ppg_rate_bpm in the primary source stratum; EOG/respiration and other unlisted modalities are unqualified and excluded.",
        "measurement_scope": "ds005555 primary pure-PPG fallback rows; analysis-side source and feature qualification",
        "per_epoch_input_extent": extents,
        "execution_records": execution,
        "source_quality_intervals": quality,
        "source_quality_status": "recorded" if quality else "recorded_none_for_eligible_recordings",
        "reference_fit_population": {"status": "unknown", "features": {}},
    }


def audit_continuous_full_surface(
    features_table: Path | str,
    qc_dir: Path | str,
    participants_tsv: Path | str,
    source_root: Path | str,
    protocol_path: Path | str,
    mndm_config_path: Path | str,
    output_dir: Path | str,
    *,
    window_sec: float = 30.0,
    expected_sfreq_hz: float = 256.0,
    n_folds: int = 5,
) -> dict[str, Any]:
    """Audit the full-cohort measurement inventory without opening outcomes."""
    if n_folds != 5:
        raise ValueError("the frozen outer split is exactly GroupKFold(5)")
    if not math.isfinite(window_sec) or window_sec <= 0 or not math.isfinite(expected_sfreq_hz) or expected_sfreq_hz <= 0:
        raise ValueError("window_sec and expected_sfreq_hz must be finite and positive")
    features_table = Path(features_table).resolve()
    qc_dir = Path(qc_dir).resolve()
    participants_tsv = Path(participants_tsv).resolve()
    source_root = Path(source_root).resolve()
    protocol_path = Path(protocol_path).resolve()
    mndm_config_path = Path(mndm_config_path).resolve()
    output_dir = Path(output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing audit output: {output_dir}")
    for path in (features_table, participants_tsv, protocol_path, mndm_config_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    if not qc_dir.is_dir() or not source_root.is_dir():
        raise FileNotFoundError(qc_dir if not qc_dir.is_dir() else source_root)

    source_files = sorted(source_root.rglob("*_task-Sleep_acq-psg_eeg.edf"))
    source_by_name: dict[str, Path] = {}
    for source_path in source_files:
        key = source_path.name.casefold()
        if key in source_by_name:
            raise ValueError(f"duplicate PSG source EDF basename: {source_path.name}")
        source_by_name[key] = source_path
    if not source_by_name:
        raise ValueError("no PSG source EDFs found")
    source_subjects = {_subject_from_file(path.name) for path in source_files}

    participant_map, participant_hash = _participant_map(participants_tsv)
    if not source_subjects.issubset(participant_map):
        raise ValueError(f"source EDF participants missing from participants.tsv: {sorted(source_subjects - set(participant_map))}")
    event_paths: dict[str, Path] = {}
    for event_path in source_root.rglob("*_task-Sleep_acq-psg_events.tsv"):
        subject = _subject_from_file(event_path.name)
        if subject in event_paths:
            raise ValueError(f"duplicate PSG events TSV for {subject}")
        event_paths[subject] = event_path.resolve()
    if set(event_paths) != source_subjects:
        raise ValueError("PSG source EDF and events TSV subject rosters differ")

    frame_hash = _sha256(features_table)
    frame = pd.read_csv(features_table, low_memory=False)
    required = {
        "file", "epoch_id", "t_start", "t_end", _SOURCE_COLUMN,
        "embodied_arousal_proxy", "ppg_rate_bpm", "qc_ok_ppg", "qc_ok_eeg",
        "source_sample_mapping_status", "nominal_source_sample_start",
        "nominal_source_sample_end_exclusive", "nominal_source_time_start_sec",
        "nominal_source_time_end_sec", "actual_sample_contributors_status",
        "actual_source_sample_start", "actual_source_sample_end_exclusive",
        "actual_source_time_start_sec", "actual_source_time_end_sec", "source_sfreq_hz",
        "input_sample_finite_status", "input_sample_gap_count",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"full feature table missing support/stratum columns: {missing}")
    if frame["file"].isna().any() or frame["epoch_id"].isna().any():
        raise ValueError("feature table has missing recording or epoch identity")
    frame["file"] = frame["file"].astype(str).map(lambda value: Path(value).name)
    numeric_epoch = pd.to_numeric(frame["epoch_id"], errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(numeric_epoch).all() or np.any(numeric_epoch < 0) or np.any(numeric_epoch > 2**53) or np.any(numeric_epoch != np.rint(numeric_epoch)):
        raise ValueError("feature epoch IDs must be exact nonnegative integers")
    frame["epoch_id"] = np.rint(numeric_epoch).astype(np.int64)
    if frame.duplicated(["file", "epoch_id"]).any():
        raise ValueError("duplicate (file, epoch_id) rows in feature table")
    feature_files = set(frame["file"].astype(str))
    if {name.casefold() for name in feature_files} != set(source_by_name):
        raise ValueError("full feature recording inventory does not exactly match the PSG source EDF inventory")
    file_subject = {filename: _subject_from_file(filename) for filename in sorted(feature_files)}
    if set(file_subject.values()) != source_subjects:
        raise ValueError("feature-file subject roster does not exactly match source EDFs")
    frame["pid"] = frame["file"].map(lambda filename: participant_map[file_subject[filename]])
    frame["subject"] = frame["pid"].map(_mndm_subject_id)
    frame = frame.sort_values(["file", "epoch_id"], kind="stable").reset_index(drop=True)
    frame["audit_row_index"] = np.arange(len(frame), dtype=np.int64)

    strata: dict[str, tuple[str, tuple[str, ...]]] = {}
    for filename, group in frame.groupby("file", sort=True):
        strata[str(filename)] = _recording_source_stratum(group[_SOURCE_COLUMN].tolist())

    event_rows: dict[str, list[dict[str, Any]]] = {}
    input_hashes_before: dict[str, str] = {
        "features_table": frame_hash,
        "participants_tsv": participant_hash,
        "protocol": _sha256(protocol_path),
        "mndm_config": _sha256(mndm_config_path),
        "audit_code": _sha256(Path(__file__).resolve()),
    }
    for subject, path in sorted(event_paths.items()):
        event_rows[subject], digest = _pilot._events(path)
        input_hashes_before[f"events:{subject}"] = str(digest)

    records: dict[str, dict[str, Any]] = {}
    record_reasons: dict[str, list[str]] = {}
    sidecar_paths: dict[str, Path] = {}
    source_hashes: dict[str, str] = {}
    for filename in sorted(feature_files):
        sidecar = qc_dir / f"{Path(filename).stem}_qc_artifacts.json"
        sidecar_paths[filename] = sidecar
        input_hashes_before[f"qc_sidecar:{filename}"] = _sha256(sidecar) if sidecar.is_file() else "missing"
        record, reasons = _pilot._support_record(qc_dir, filename, expected_sfreq_hz)
        if record is not None:
            records[filename] = record
            source = record.get("source", {})
            if isinstance(source, Mapping) and source.get("sha256"):
                source_hashes[filename] = str(source["sha256"]).lower()
        record_reasons[filename] = list(reasons)

    row_records: list[dict[str, Any]] = []
    for row in frame.to_dict(orient="records"):
        filename = str(row["file"])
        subject = file_subject[filename]
        pid = str(row["pid"])
        record = records.get(filename, {})
        quality = record.get("source_quality_intervals", {})
        quality_intervals = quality.get("intervals", []) if isinstance(quality, Mapping) else []
        quality_intervals = [item for item in quality_intervals if isinstance(item, Mapping)] if isinstance(quality_intervals, list) else []
        base_ok, reasons = _pilot._row_support_status(row, record, record_reasons[filename], quality_intervals)
        stratum, source_values = strata[filename]
        proxy_source = str(row.get(_SOURCE_COLUMN, "")).strip()
        primary_ok, proxy_match, reasons = _qualify_primary_row(
            row,
            stratum=stratum,
            base_support_ok=base_ok,
            base_reasons=reasons,
        )
        start, end = _pilot._finite(row.get("t_start")), _pilot._finite(row.get("t_end"))
        stage_code, stage_status = (None, "window_time_invalid")
        stage_pure, stage_purity_status = False, "window_time_invalid"
        if start is not None and end is not None and end > start:
            stage_code, stage_status = _pilot._stage_at_point(event_rows[subject], end)
            stage_pure, stage_purity_status = _pilot._stage_purity(event_rows[subject], start, end, stage_code)
        row_records.append({
            "audit_row_index": int(row["audit_row_index"]),
            "file": filename,
            "subject": str(row["subject"]),
            "bids_subject": subject,
            "pid": pid,
            "epoch_id": int(row["epoch_id"]),
            "t_start": start,
            "t_end": end,
            "source_stratum": stratum,
            "recording_proxy_sources": ";".join(source_values),
            "row_proxy_source": proxy_source,
            "proxy_matches_ppg_rate": proxy_match,
            "base_support_eligible": bool(base_ok),
            "primary_surface_eligible": primary_ok,
            "support_exclusion_reasons": ";".join(sorted(set(reasons))),
            "stage_at_origin_code": stage_code,
            "stage_at_origin": _pilot._STAGES.get(stage_code) if stage_code is not None else None,
            "stage_at_origin_status": stage_status,
            "stage_window_pure": bool(stage_pure),
            "stage_window_status": stage_purity_status,
            "segment_id": None,
            "source_sha256": str(record.get("source", {}).get("sha256", "")).lower() if isinstance(record.get("source"), Mapping) else None,
            "source_sample_mapping_status": row.get("source_sample_mapping_status"),
            "source_sample_mapping_reason": row.get("source_sample_mapping_reason"),
            "nominal_source_sample_start": _pilot._finite(row.get("nominal_source_sample_start")),
            "nominal_source_sample_end_exclusive": _pilot._finite(row.get("nominal_source_sample_end_exclusive")),
            "actual_sample_contributors_status": row.get("actual_sample_contributors_status"),
            "actual_source_sample_start": _pilot._finite(row.get("actual_source_sample_start")),
            "actual_source_sample_end_exclusive": _pilot._finite(row.get("actual_source_sample_end_exclusive")),
            "actual_source_time_start_sec": _pilot._finite(row.get("actual_source_time_start_sec")),
            "actual_source_time_end_sec": _pilot._finite(row.get("actual_source_time_end_sec")),
            "source_sfreq_hz": _pilot._finite(row.get("source_sfreq_hz")),
            "input_sample_finite_status": row.get("input_sample_finite_status"),
            "input_sample_gap_count": _pilot._finite(row.get("input_sample_gap_count")),
            "qc_ok_eeg": _pilot._truth(row.get("qc_ok_eeg")),
            "qc_ok_ppg": _pilot._truth(row.get("qc_ok_ppg")),
        })
    row_audit = pd.DataFrame(row_records)
    segments = _contiguous_segments(row_audit, window_sec)
    row_audit["segment_id"] = [segments[(str(row.file), int(row.epoch_id))] for row in row_audit.itertuples()]

    eligible_rows = row_audit.loc[row_audit["primary_surface_eligible"]].copy()
    if eligible_rows.empty:
        raise ValueError("no rows passed the frozen pure-PPG source and support requirements")
    pid_count = eligible_rows["pid"].nunique()
    if pid_count < n_folds:
        raise ValueError(f"only {pid_count} biological PIDs qualify; cannot create GroupKFold(5)")
    fold_roster = build_grouped_pid_manifest(eligible_rows[["pid"]].rename(columns={"pid": "pid"}), pid_col="pid")
    eligible_rows["pid"] = eligible_rows["pid"].astype(str)
    eligible_rows["subject"] = eligible_rows["subject"].astype(str)
    eligible_frame = frame.loc[eligible_rows["audit_row_index"].astype(int).to_numpy()].copy().reset_index(drop=True)
    eligible_frame["pid"] = eligible_rows["pid"].to_numpy()
    eligible_frame["subject"] = eligible_rows["subject"].to_numpy()
    eligible_frame["source_stratum"] = "pure_ppg"
    missing_export_columns = sorted(set(_FEATURE_EXPORT_COLUMNS) - set(eligible_frame.columns))
    if missing_export_columns:
        raise ValueError(f"feature overlay lacks required fixed chart/support columns: {missing_export_columns}")
    eligible_frame = eligible_frame.loc[:, _FEATURE_EXPORT_COLUMNS].copy()

    pair_table = _pair_availability(row_audit, window_sec)
    stage_eligible = row_audit.loc[
        row_audit["primary_surface_eligible"] & row_audit["stage_window_pure"] & row_audit["stage_at_origin_code"].isin([0, 2])
    ]
    stage_coverage_rows: list[dict[str, Any]] = []
    for pid in sorted(eligible_rows["pid"].astype(str).unique()):
        block = stage_eligible.loc[stage_eligible["pid"].astype(str).eq(pid)]
        for stage_code, stage_label in _CONTEXT_STAGES.items():
            selected = block.loc[block["stage_at_origin_code"].eq(stage_code)]
            stage_coverage_rows.append({
                "pid": pid,
                "stage": stage_label,
                "support_eligible_stage_pure_origins": int(len(selected)),
                "recordings": int(selected["file"].nunique()),
            })
    stage_coverage = pd.DataFrame(stage_coverage_rows)

    support_ledger = _make_support_ledger(eligible_rows, records)
    ledger_bytes = _json_bytes(support_ledger)
    ledger_hash = hashlib.sha256(ledger_bytes).hexdigest()
    source_hashes_primary = {
        filename: source_hashes[filename]
        for filename in sorted(eligible_rows["file"].astype(str).unique())
    }
    fold_dir = output_dir / "fold_manifests"
    fold_payloads: list[dict[str, Any]] = []
    for fold in fold_roster.folds:
        training = eligible_rows.loc[eligible_rows["pid"].astype(str).isin(fold.training_pids)]
        apply = eligible_rows.loc[eligible_rows["pid"].astype(str).isin(fold.evaluation_pids)]
        if set(training["pid"].astype(str)) & set(apply["pid"].astype(str)):
            raise RuntimeError(f"biological PID leakage in fold {fold.fold_id}")
        payload = {
            "schema_version": "mndm.fold_split.v1",
            "split_id": f"ds005555-continuous-c123-ppg-fold-{fold.fold_id}-20260929-v1",
            "time_reference": {
                "status": "verified",
                "start_column": "t_start",
                "end_column": "t_end",
                "unit": "seconds",
                "origin": "recording_start",
            },
            "source_file_sha256": source_hashes_primary,
            "signal_support_ledger_sha256": ledger_hash,
            "grouping_unit": "biological_pid_from_participants.tsv",
            "training_pids": [_mndm_subject_id(pid) for pid in fold.training_pids],
            "apply_pids": [_mndm_subject_id(pid) for pid in fold.evaluation_pids],
            "training_ranges": _ranges_for_rows(training),
            "apply_ranges": _ranges_for_rows(apply),
            "scope": "measurement-only fold identity; no charts or outcomes calculated",
        }
        fold_payloads.append(payload)

    recording_rows: list[dict[str, Any]] = []
    for filename, group in frame.groupby("file", sort=True):
        stratum, source_values = strata[str(filename)]
        pid_values = sorted(group["pid"].astype(str).unique())
        audit_block = row_audit.loc[row_audit["file"].eq(filename)]
        recording_rows.append({
            "file": str(filename),
            "bids_subject": file_subject[str(filename)],
            "pid": ";".join(pid_values),
            "source_stratum": stratum,
            "recording_proxy_sources": ";".join(source_values),
            "feature_rows": int(len(group)),
            "base_support_eligible_rows": int(audit_block["base_support_eligible"].sum()),
            "primary_surface_eligible_rows": int(audit_block["primary_surface_eligible"].sum()),
            "support_record_status": "valid" if not record_reasons[str(filename)] else "unknown",
            "support_record_reasons": ";".join(record_reasons[str(filename)]),
            "source_sha256": source_hashes.get(str(filename)),
        })
    recording_audit = pd.DataFrame(recording_rows)

    leakage = {
        "schema": "nmd_analysis.continuous_full_surface_leakage_ledger.v1",
        "claim_status": "no_biological_claim",
        "full_cohort_scoring_authorized": False,
        "admitted_predictors": [],
        "variables": [
            {"name": "ppg_rate_bpm / embodied_arousal_proxy when source=ppg_rate_bpm", "class": "PRESENT_ONLY", "scope": "one current 30-s raw PPG window; window-local median and peak detection", "primary_stratum": "qualified subject to row-level QC/support"},
            {"name": "fixed EEG window features", "class": "PRESENT_ONLY", "scope": "current 30-s window after recorded finite-causal minimum-phase FIR; support checked per row"},
            {"name": "eog_*", "class": "USES_FUTURE", "scope": "whole-recording zero-phase filtering/run-level threshold identified in implementation review; excluded from chart/predictor scope"},
            {"name": "resp_*", "class": "UNKNOWN", "scope": "gap-safe extraction withheld/unsupported; excluded"},
            {"name": "all unlisted candidate variables", "class": "UNKNOWN", "scope": "not admitted by this support-only audit"},
        ],
    }

    # Re-hash every input, including the full raw PSG EDF inventory. This is
    # deliberately expensive: support manifests must not bind a changed file.
    input_hashes_after: dict[str, str] = {
        "features_table": _sha256(features_table),
        "participants_tsv": _sha256(participants_tsv),
        "protocol": _sha256(protocol_path),
        "mndm_config": _sha256(mndm_config_path),
        "audit_code": _sha256(Path(__file__).resolve()),
    }
    for subject, path in sorted(event_paths.items()):
        input_hashes_after[f"events:{subject}"] = _sha256(path)
    for filename, path in sidecar_paths.items():
        input_hashes_after[f"qc_sidecar:{filename}"] = _sha256(path) if path.is_file() else "missing"
    for filename, path in sorted(source_by_name.items()):
        input_hashes_after[f"raw_source:{filename}"] = _sha256(path)
    for filename, digest in source_hashes.items():
        input_hashes_before[f"raw_source:{filename.casefold()}"] = digest
        if input_hashes_after.get(f"raw_source:{filename.casefold()}") != digest:
            raise ValueError(f"raw PSG source changed or disagrees with sidecar hash during audit: {filename}")
    if input_hashes_before.get("features_table") != input_hashes_after.get("features_table"):
        raise ValueError("feature table changed during audit")
    for key, value in input_hashes_before.items():
        after_key = key if key in {"features_table", "participants_tsv", "protocol", "mndm_config", "audit_code"} else key
        if key.startswith(("events:", "qc_sidecar:")) and input_hashes_after.get(after_key) != value:
            raise ValueError(f"audit input changed during run: {key}")
        if key in {"participants_tsv", "protocol", "mndm_config", "audit_code"} and input_hashes_after.get(key) != value:
            raise ValueError(f"audit input changed during run: {key}")

    output_dir.mkdir(parents=True, exist_ok=False)
    fold_dir.mkdir(parents=False, exist_ok=False)
    row_audit.to_csv(output_dir / "row_support_audit.csv", index=False)
    recording_audit.to_csv(output_dir / "recording_audit.csv", index=False)
    stage_coverage.to_csv(output_dir / "stage_coverage_by_pid.csv", index=False)
    pair_table.to_csv(output_dir / "pair_availability.csv", index=False)
    feature_surface_path = output_dir / "features_primary_ppg.parquet"
    eligible_frame.to_parquet(feature_surface_path, index=False)
    (output_dir / "signal_support_ledger.json").write_bytes(ledger_bytes)
    (output_dir / "leakage_ledger.json").write_text(json.dumps(leakage, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    fold_manifest_hashes: dict[str, str] = {}
    for payload in fold_payloads:
        path = fold_dir / f"fold_{payload['split_id'].split('-fold-')[-1].split('-')[0]}.json"
        path.write_bytes(_json_bytes(payload))
        fold_manifest_hashes[path.name] = _sha256(path)

    output_sha256 = {
        path.relative_to(output_dir).as_posix(): _sha256(path)
        for path in sorted(output_dir.rglob("*"))
        if path.is_file()
    }
    input_paths = {
        "features_table": str(features_table),
        "participants_tsv": str(participants_tsv),
        "protocol": str(protocol_path),
        "mndm_config": str(mndm_config_path),
        "audit_code": str(Path(__file__).resolve()),
        "qc_dir": str(qc_dir),
        "source_root": str(source_root),
        "events": {subject: str(path.resolve()) for subject, path in sorted(event_paths.items())},
        "qc_sidecars": {filename: str(path.resolve()) for filename, path in sorted(sidecar_paths.items())},
        "raw_sources": {name: str(path.resolve()) for name, path in sorted(source_by_name.items())},
    }

    summary_counts = {
        "feature_rows": int(len(frame)),
        "recordings": int(frame["file"].nunique()),
        "biological_pids_in_inventory": int(frame["pid"].nunique()),
        "primary_eligible_rows": int(len(eligible_rows)),
        "primary_eligible_recordings": int(eligible_rows["file"].nunique()),
        "primary_eligible_pids": int(eligible_rows["pid"].nunique()),
        "recordings_by_source_stratum": {str(key): int(value) for key, value in recording_audit["source_stratum"].value_counts().sort_index().items()},
        "primary_rows_by_pid": {str(key): int(value) for key, value in eligible_rows["pid"].value_counts().sort_index().items()},
        "support_eligible_stage_pure_origins": {
            stage: int(((stage_eligible["stage_at_origin_code"] == code)).sum())
            for code, stage in _CONTEXT_STAGES.items()
        },
        "pids_with_stage_pure_support": {
            stage: int(stage_coverage.loc[(stage_coverage["stage"] == stage) & (stage_coverage["support_eligible_stage_pure_origins"] > 0), "pid"].nunique())
            for stage in _CONTEXT_STAGES.values()
        },
        "pids_with_both_n2_and_wake": int(sum(
            all(int(stage_coverage.loc[(stage_coverage["pid"] == pid) & (stage_coverage["stage"] == stage), "support_eligible_stage_pure_origins"].iloc[0]) > 0 for stage in ("Wake", "N2"))
            for pid in stage_coverage["pid"].unique()
        )),
    }
    pair_summary = {}
    for model in ("C1_history2", "C3_Wake", "C3_N2"):
        for horizon in _HORIZONS:
            block = pair_table.loc[(pair_table["model_scope"] == model) & (pair_table["horizon"] == horizon)]
            pair_summary[f"{model}:{horizon}"] = {
                "candidate_origins": int(block["candidate_origins"].sum()) if not block.empty else 0,
                "target_present": int(block["target_present"].sum()) if not block.empty else 0,
                "support_and_contiguity_eligible": int(block["support_and_contiguity_eligible"].sum()) if not block.empty else 0,
                "pids_with_eligible_pairs": int(block.loc[block["support_and_contiguity_eligible"] > 0, "pid"].nunique()) if not block.empty else 0,
            }
    report = {
        "schema": "nmd_analysis.continuous_full_surface_audit.v1",
        "status": "PARTIAL_PASS_SOURCE_SUPPORT_ONLY",
        "claim_status": "no_biological_claim",
        "scientific_qualification": "not_assessed",
        "stage": "full_cohort_measurement_support_audit",
        "charts_generated": False,
        "outcomes_calculated": False,
        "C1_C3_scores_opened": False,
        "full_cohort_scoring_authorized": False,
        "surface_replay_status": "PENDING_FULL_COHORT_REPLAY",
        "chart_support_signature_status": "PENDING_FOLD_SAFE_CHART_SURFACE",
        "c3_context": "human-scored N2 versus Wake at forecast origin; frozen preregistration context",
        "counts": summary_counts,
        "pair_availability_support_only": pair_summary,
        "feature_surface_export": {
            "path": feature_surface_path.name,
            "sha256": _sha256(feature_surface_path),
            "columns": list(eligible_frame.columns),
            "label_free_predictor_overlay": True,
            "stage_label_exported": False,
            "provenance_only_columns": {
                "eeg_entropy_metric": (
                    "MNDM entropy estimator identity (for example permutation_entropy or spectral_entropy); "
                    "required to classify direct versus fallback support and not a predictor input"
                ),
            },
            "omitted_by_design": {
                "stage": "human-scored context/outcome label; retained only in the separate stage/support audit",
                "eog_*": "USES_FUTURE/run-level statistic; unqualified and excluded",
                "resp_*": "UNKNOWN/withheld; unqualified and excluded",
                "all unlisted input columns": "not part of the fixed chart/support allowlist",
            },
        },
        "fold_assignment": {
            "method": "deterministic GroupKFold(5) by biological pid",
            "manifest_sha256": fold_roster.sha256,
            "eligible_pid_count": len(fold_roster.expected_pids),
            "folds": [
                {"fold_id": item.fold_id, "training_pids": list(item.training_pids), "apply_pids": list(item.evaluation_pids)}
                for item in fold_roster.folds
            ],
            "signal_support_ledger_sha256": ledger_hash,
            "manifest_hashes": fold_manifest_hashes,
            "note": "All repeated BIDS recordings for a biological pid are placed on one side; MNDM subject identity is overlaid with biological pid for participant-balanced fitting.",
        },
        "support_record_status": {filename: "valid" if not reasons else "unknown" for filename, reasons in record_reasons.items()},
        "support_record_reasons": record_reasons,
        "input_paths": input_paths,
        "input_hashes_before": input_hashes_before,
        "input_hashes_after": input_hashes_after,
        "output_sha256": output_sha256,
        "output_hash_scope": "all generated audit files present before validation.json is written; validation.json is excluded to avoid a self-referential hash",
        "provenance": {
            "audit_code_sha256": input_hashes_after["audit_code"],
            "audit_code_path": str(Path(__file__).resolve()),
            "mndm_config_path": str(mndm_config_path),
            "features_table_sha256": frame_hash,
            "participants_tsv_sha256": participant_hash,
            "signal_support_ledger_sha256": ledger_hash,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "window_sec": float(window_sec),
            "source_sfreq_hz": float(expected_sfreq_hz),
            "horizons_rows": dict(_HORIZONS),
            "source_stage_column": "stage_hum",
            "stage_codebook": {str(code): label for code, label in _pilot._STAGES.items()},
            "proxy_equality_absolute_tolerance": _PROXY_MATCH_ATOL,
        },
    }
    (output_dir / "validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--qc-dir", type=Path, required=True)
    parser.add_argument("--participants", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--mndm-config", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--window-sec", type=float, default=30.0)
    parser.add_argument("--sfreq-hz", type=float, default=256.0)
    args = parser.parse_args(argv)
    report = audit_continuous_full_surface(
        args.features,
        args.qc_dir,
        args.participants,
        args.source_root,
        args.protocol,
        args.mndm_config,
        args.out_dir,
        window_sec=args.window_sec,
        expected_sfreq_hz=args.sfreq_hz,
    )
    print(json.dumps({"status": report["status"], "counts": report["counts"], "output_dir": str(args.out_dir.resolve())}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
