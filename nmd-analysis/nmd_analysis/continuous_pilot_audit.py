"""Chart-free audit for preregistered continuous BOAS measurement pilots.

This module deliberately writes support, stage-alignment and timestamp-pair
ledgers only. It does not project features to MNPS coordinates, match contexts,
or calculate C1/C3 outcomes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import re
import shutil
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


_HORIZONS = {"h1": 1, "h2": 2, "h4": 4}
PILOT_SFREQ_HZ = 256.0
_STAGES = {
    0: "wake", 1: "n1", 2: "n2", 3: "n3", 4: "rem",
    8: "disconnection", -2: "artifact",
}
_ALIASES = {name: code for code, name in _STAGES.items()}
_ALIASES.update({"wake": 0, "w": 0, "nrem1": 1, "nrem2": 2, "nrem3": 3, "r": 4})

_EXPECTED_PROTOCOL_SUFFIX = "articles/BOAS_sleep_dataset_ndt._v.1.0/preregistration_continuous_C123_20260929.md"
_EXPECTED_PILOT_CONFIG_SUFFIX = (
    "mndm/config/sources/openneuro/"
    "config_ingest_ds005555_continuous_c123_prediction_safe_pilot_20260929.yaml"
)
_EXPECTED_MNDM_CONFIGS = {
    "config_ingest_ds005555_continuous_c123_cautious_gap_safe_final.yaml",
    "config_ingest_ds005555_continuous_c123_cautious_gap_safe.yaml",
    "config_ingest_ds005555_continuous_c123_cautious_gap_isolated.yaml",
    "config_ingest_ds005555_continuous_c123_cautious_qc.yaml",
    "config_ingest_ds005555_continuous_c123_safe_gap.yaml",
    "config_ingest_ds005555_continuous_c123.yaml",
    "config_ingest_ds005555.yaml",
    "config_ingest_common_eeg.yaml",
}
_EXPECTED_MNDM_CODE_SUFFIXES = {
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
}
_EXPECTED_SUBJECTS = {"sub-100", "sub-105"}
_EXPECTED_SOURCE_BASENAMES = {
    f"{subject}_task-sleep_acq-psg_eeg.edf" for subject in _EXPECTED_SUBJECTS
}
_EXPECTED_EVENT_BASENAMES = {
    f"{subject}_task-sleep_acq-psg_events.tsv" for subject in _EXPECTED_SUBJECTS
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_path(path: str | Path) -> str:
    return Path(path).resolve().as_posix().casefold()


def _path_has_suffix(path: Path, suffix: str) -> bool:
    canonical = path.resolve().as_posix().casefold().rstrip("/")
    expected = suffix.replace("\\", "/").casefold().lstrip("/")
    return canonical.endswith("/" + expected)


def _subject_from_path(path: Path) -> str | None:
    match = re.search(r"sub-[A-Za-z0-9]+", path.name)
    return match.group(0).casefold() if match else None


def _validate_freeze_role_paths(inputs: Sequence[Mapping[str, str]]) -> None:
    """Bind required manifest roles to this pilot's declared files, not labels alone."""
    by_role: dict[str, list[Path]] = {}
    for item in inputs:
        by_role.setdefault(item["role"], []).append(Path(item["path"]).resolve())

    protocol_paths = by_role.get("protocol", [])
    if len(protocol_paths) != 1 or not _path_has_suffix(protocol_paths[0], _EXPECTED_PROTOCOL_SUFFIX):
        raise ValueError("freeze manifest protocol role does not bind the expected continuous C1/C3 preregistration")

    pilot_paths = by_role.get("pilot_config", [])
    if len(pilot_paths) != 1 or not _path_has_suffix(pilot_paths[0], _EXPECTED_PILOT_CONFIG_SUFFIX):
        raise ValueError("freeze manifest pilot_config role does not bind the expected prediction-safe YAML")

    config_paths = by_role.get("mndm_config", [])
    expected_config_suffixes = {
        f"mndm/config/sources/openneuro/{name}" for name in _EXPECTED_MNDM_CONFIGS
        if name != "config_ingest_common_eeg.yaml"
    }
    expected_config_suffixes.add("mndm/config/config_ingest_common_eeg.yaml")
    if (
        len(config_paths) != len(_EXPECTED_MNDM_CONFIGS)
        or {
            suffix for suffix in expected_config_suffixes
            if sum(_path_has_suffix(path, suffix) for path in config_paths) == 1
        } != expected_config_suffixes
    ):
        raise ValueError("freeze manifest mndm_config role does not bind the complete expected YAML import chain")

    code_paths = by_role.get("mndm_code", [])
    missing_code = sorted(
        suffix for suffix in _EXPECTED_MNDM_CODE_SUFFIXES
        if sum(_path_has_suffix(path, suffix) for path in code_paths) != 1
    )
    if missing_code:
        raise ValueError(f"freeze manifest mndm_code role is missing or ambiguously binds expected files: {missing_code}")

    source_paths = by_role.get("source_edf", [])
    if len(source_paths) != len(_EXPECTED_SUBJECTS) or {path.name.casefold() for path in source_paths} != _EXPECTED_SOURCE_BASENAMES:
        raise ValueError("freeze manifest source_edf role does not bind the fixed sub-100/sub-105 EDFs")
    for path in source_paths:
        subject = _subject_from_path(path)
        expected_suffix = f"ExternalReceivedDatasets/openneuro/received/ds005555/{subject}/eeg/{path.name}"
        if subject not in _EXPECTED_SUBJECTS or not _path_has_suffix(path, expected_suffix):
            raise ValueError("freeze manifest source_edf role path is outside the declared ds005555 subject inputs")

    event_paths = by_role.get("events", [])
    if len(event_paths) != len(_EXPECTED_SUBJECTS) or {path.name.casefold() for path in event_paths} != _EXPECTED_EVENT_BASENAMES:
        raise ValueError("freeze manifest events role does not bind the fixed sub-100/sub-105 event TSVs")
    for path in event_paths:
        subject = _subject_from_path(path)
        expected_suffix = f"ExternalReceivedDatasets/openneuro/received/ds005555/{subject}/eeg/{path.name}"
        if subject not in _EXPECTED_SUBJECTS or not _path_has_suffix(path, expected_suffix):
            raise ValueError("freeze manifest events role path is outside the declared ds005555 subject inputs")


def _load_freeze_manifest(path: Path) -> tuple[str, list[dict[str, str]], dict[str, str]]:
    """Validate every declared frozen input and return its identity hashes."""
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"frozen pilot manifest missing: {path}")
    manifest_hash = _sha256(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"invalid frozen pilot manifest: {type(exc).__name__}") from exc
    if not isinstance(payload, Mapping) or payload.get("schema") != "nmd_analysis.continuous_pilot_freeze_manifest.v1":
        raise ValueError("frozen pilot manifest schema mismatch")
    raw_inputs = payload.get("inputs")
    if not isinstance(raw_inputs, list) or not raw_inputs:
        raise ValueError("frozen pilot manifest requires a nonempty inputs list")
    inputs: list[dict[str, str]] = []
    hashes: dict[str, str] = {}
    roles: set[str] = set()
    seen: set[tuple[str, str]] = set()
    for item in raw_inputs:
        if not isinstance(item, Mapping):
            raise ValueError("frozen pilot manifest entries must be objects")
        role = str(item.get("role", "")).strip()
        source = Path(str(item.get("path", ""))).resolve()
        expected = str(item.get("sha256", "")).lower()
        if not role or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("frozen pilot manifest entry has invalid role or SHA-256")
        if not source.is_file():
            raise ValueError(f"frozen pilot input is missing: {source}")
        identity = (role, _canonical_path(source))
        if identity in seen:
            raise ValueError(f"duplicate frozen pilot input entry: {role} {source}")
        seen.add(identity)
        actual = _sha256(source)
        if actual.lower() != expected:
            raise ValueError(f"frozen pilot input hash mismatch: {role} {source}")
        roles.add(role)
        entry = {"role": role, "path": str(source), "sha256": actual}
        inputs.append(entry)
        hashes[f"freeze_input:{role}:{source}"] = actual
    required_roles = {"protocol", "pilot_config", "mndm_config", "mndm_code", "analysis_audit", "source_edf", "events"}
    missing_roles = sorted(required_roles - roles)
    if missing_roles:
        raise ValueError(f"frozen pilot manifest missing required roles: {missing_roles}")
    inputs.sort(key=lambda item: (item["role"], item["path"].casefold()))
    _validate_freeze_role_paths(inputs)
    return manifest_hash, inputs, hashes


def _support_contract_sha256(record: Mapping[str, Any]) -> str:
    """Hash deterministic measurement/support metadata, excluding run timings."""
    keys = (
        "schema", "status", "source", "temporal_support_mode", "input_sfreq_hz",
        "target_sfreq_hz", "sampling_policy", "raw_clock_before_crop",
        "raw_clock_after_crop", "edf_sample_grid", "temporal_support",
        "effective_time_support", "source_sample_grid_supported",
        "source_sample_grid_reason", "channel_types_after_dataset_typing",
        "ppg_source_selection", "ppg_feature_contract", "source_quality_intervals",
        "quality_interval_policy",
    )
    canonical = json.dumps(
        {key: record.get(key) for key in keys},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _finite(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def _truth(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _stage_code(value: Any) -> int | None:
    numeric = _finite(value)
    if numeric is not None and numeric.is_integer() and int(numeric) in _STAGES:
        return int(numeric)
    return _ALIASES.get(str(value).strip().lower())


def _support_record(qc_dir: Path, raw_file: str, expected_sfreq_hz: float) -> tuple[dict[str, Any] | None, list[str]]:
    sidecar = qc_dir / f"{Path(raw_file).stem}_qc_artifacts.json"
    reasons: list[str] = []
    if not sidecar.is_file():
        return None, ["missing_qc_sidecar"]
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [f"invalid_qc_sidecar:{type(exc).__name__}"]
    record = payload.get("signal_support_provenance") if isinstance(payload, Mapping) else None
    if not isinstance(record, Mapping):
        return None, ["signal_support_provenance_missing"]
    record = dict(record)
    if record.get("schema") != "mndm.signal_support_provenance.v1":
        reasons.append("support_schema_mismatch")
    source = record.get("source")
    if not isinstance(source, Mapping):
        reasons.append("source_identity_missing")
    else:
        if Path(str(source.get("path", ""))).name != Path(raw_file).name:
            reasons.append("source_file_identity_mismatch")
        if source.get("exists") is not True:
            reasons.append("source_existence_not_verified")
        digest = str(source.get("sha256", ""))
        if not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            reasons.append("source_hash_missing")
        if source.get("hash_stable") is not True or str(source.get("sha256_after", "")).lower() != digest.lower():
            reasons.append("source_hash_not_stable")
        source_path = Path(str(source.get("path", "")))
        if not source_path.is_file():
            reasons.append("source_file_unavailable_for_hash_verification")
        elif _sha256(source_path).lower() != digest.lower():
            reasons.append("source_file_hash_mismatch")
    if record.get("status") != "completed":
        reasons.append("preprocessing_not_completed")
    if record.get("temporal_support_mode") != "causal_finite":
        reasons.append("causal_finite_mode_not_recorded")
    for key in ("input_sfreq_hz", "target_sfreq_hz"):
        value = _finite(record.get(key))
        if value is None or not math.isclose(value, expected_sfreq_hz, rel_tol=0.0, abs_tol=1e-9):
            reasons.append(f"{key}_does_not_match_pilot_clock")
    temporal = record.get("temporal_support", {})
    effective = record.get("effective_time_support", {})
    if not isinstance(temporal, Mapping) or temporal.get("status") != "finite_causal":
        reasons.append("finite_causal_temporal_support_not_recorded")
    if not isinstance(effective, Mapping) or effective.get("status") != "finite_causal":
        reasons.append("finite_causal_operation_support_not_recorded")
    grid = record.get("edf_sample_grid", {})
    if not isinstance(grid, Mapping) or grid.get("continuity_status") != "verified_continuous":
        reasons.append("continuous_edf_sample_grid_not_verified")
    elif (
        grid.get("continuity_marker") not in {"EDF", "EDF+C"}
        or not isinstance(grid.get("continuity_verification"), str)
        or "EDF+D rejected" not in grid.get("continuity_verification", "")
        or "record grid checked" not in grid.get("continuity_verification", "")
        or _finite(grid.get("sample_rate_hz")) != expected_sfreq_hz
        or _finite(grid.get("sample_count")) is None
        or _finite(grid.get("records")) is None
        or _finite(grid.get("samples_per_record")) is None
        or _finite(grid.get("record_duration_seconds")) is None
        or any(
            _finite(grid.get(key)) is None
            or not _finite(grid.get(key)).is_integer()
            or _finite(grid.get(key)) <= 0
            for key in ("sample_count", "records", "samples_per_record", "channel_count")
        )
        or not isinstance(grid.get("samples_per_record_by_channel"), list)
        or not grid.get("samples_per_record_by_channel")
        or _finite(grid.get("channel_count")) != len(grid.get("samples_per_record_by_channel", []))
        or any(
            _finite(value) is None
            or not _finite(value).is_integer()
            or _finite(value) != _finite(grid.get("samples_per_record"))
            for value in grid.get("samples_per_record_by_channel", [])
        )
        or grid.get("boundary_annotation_check") != {
            "status": "verified_absent",
            "rejected_prefixes": ["BAD_ACQ_SKIP", "BAD BOUNDARY", "EDGE"],
        }
        or not math.isclose(
            float(grid["record_duration_seconds"]),
            float(grid["samples_per_record"]) / expected_sfreq_hz,
            rel_tol=0.0,
            abs_tol=1e-9,
        )
        or not math.isclose(
            float(grid["sample_count"]),
            float(grid["records"]) * float(grid["samples_per_record"]),
            rel_tol=0.0,
            abs_tol=0.0,
        )
    ):
        reasons.append("edf_continuity_grid_fields_invalid")
    if isinstance(effective, Mapping):
        resampler = effective.get("resampler", {})
        fir = effective.get("eeg_bandpass", {})
        tap_count = _finite(fir.get("tap_count")) if isinstance(fir, Mapping) else None
        grid_count = _finite(grid.get("sample_count")) if isinstance(grid, Mapping) else None
        if (
            not isinstance(resampler, Mapping)
            or resampler.get("method") != "identity_sample_grid"
            or resampler.get("phase") != "identity"
            or _finite(resampler.get("up")) != 1
            or _finite(resampler.get("down")) != 1
            or _finite(resampler.get("tap_count")) != 1
            or grid_count is None
            or _finite(resampler.get("output_sample_count")) != grid_count
        ):
            reasons.append("identity_grid_support_contract_invalid")
        if (
            not isinstance(fir, Mapping)
            or fir.get("method") != "mne.filter.filter_data_fir"
            or fir.get("phase") != "minimum"
            or fir.get("pad") != "constant"
            or fir.get("support_interpretation") != "output k depends on input [max(0,k-tap_count+1),k]"
            or tap_count is None
            or tap_count < 1
            or not tap_count.is_integer()
            or _finite(fir.get("sfreq_hz")) != expected_sfreq_hz
        ):
            reasons.append("finite_causal_fir_contract_invalid")
    selected = record.get("ppg_source_selection", {})
    selected_names = selected.get("channel_names", []) if isinstance(selected, Mapping) else []
    selected_types = selected.get("channel_types_after_dataset_typing", []) if isinstance(selected, Mapping) else []
    if not isinstance(selected_names, list) or len(selected_names) != 1:
        reasons.append("ppg_source_channel_not_unique")
    if not isinstance(selected, Mapping) or selected.get("rule") != "source_channel_name_regex":
        reasons.append("ppg_source_selection_rule_not_qualified")
    if not isinstance(selected_types, list) or len(selected_types) != 1:
        reasons.append("ppg_source_channel_type_not_recorded")
    ppg_contract = record.get("ppg_feature_contract", {})
    if not isinstance(ppg_contract, Mapping) or ppg_contract.get("estimator") != "window_local_present_only_v1":
        reasons.append("present_only_ppg_contract_not_recorded")
    elif "present_only" not in str(ppg_contract.get("information_scope", "")):
        reasons.append("ppg_information_scope_not_present_only")
    elif ppg_contract.get("source_channels") != selected_names:
        reasons.append("ppg_contract_source_channel_mismatch")
    elif ppg_contract.get("source_channel_types_after_dataset_typing") != {
        str(name): str(channel_type)
        for name, channel_type in zip(selected_names, selected_types)
    }:
        reasons.append("ppg_contract_source_channel_type_mismatch")
    quality = record.get("source_quality_intervals", {})
    if not isinstance(quality, Mapping) or quality.get("status") not in {"observed", "none_observed"}:
        reasons.append("source_quality_interval_status_unknown")
    elif not isinstance(quality.get("intervals"), list):
        reasons.append("source_quality_intervals_not_list")
    else:
        intervals = quality["intervals"]
        if quality.get("status") == "observed" and not intervals:
            reasons.append("observed_quality_intervals_missing")
        if quality.get("status") == "none_observed" and intervals:
            reasons.append("none_observed_quality_intervals_present")
        for interval in intervals:
            if not isinstance(interval, Mapping):
                reasons.append("source_quality_interval_not_object")
                continue
            left, right = _finite(interval.get("start_sec")), _finite(interval.get("end_sec"))
            if interval.get("clock") != "original_raw_seconds" or left is None or right is None or right < left:
                reasons.append("source_quality_interval_invalid")
    return record, reasons


def _stage_at_point(intervals: Sequence[Mapping[str, Any]], point: float) -> tuple[int | None, str]:
    hits = []
    invalid_hit = False
    for interval in intervals:
        start = _finite(interval.get("onset"))
        duration = _finite(interval.get("duration"))
        code = _stage_code(interval.get("stage_hum"))
        if start is None or duration is None or duration <= 0:
            continue
        if start <= point < start + duration:
            if code is None:
                invalid_hit = True
            else:
                hits.append(code)
    if invalid_hit:
        return None, "unmapped_source_stage_at_origin"
    unique = sorted(set(hits))
    if len(unique) == 1:
        return unique[0], "unique_source_stage_at_origin"
    if not unique:
        return None, "no_source_stage_at_origin"
    return None, "conflicting_source_stages_at_origin"


def _stage_purity(
    intervals: Sequence[Mapping[str, Any]], start: float, end: float, origin_code: int | None
) -> tuple[bool, str]:
    if origin_code is None or not (math.isfinite(start) and math.isfinite(end) and end > start):
        return False, "origin_or_window_invalid"
    spans = []
    invalid_overlap = False
    for interval in intervals:
        onset = _finite(interval.get("onset"))
        duration = _finite(interval.get("duration"))
        code = _stage_code(interval.get("stage_hum"))
        if onset is None or duration is None or duration <= 0:
            continue
        stop = onset + duration
        if stop > start and onset < end:
            if code is None:
                invalid_overlap = True
            else:
                spans.append((max(start, onset), min(end, stop), code))
    if invalid_overlap:
        return False, "unmapped_source_stage_overlaps_window"
    spans.sort(key=lambda item: (item[0], item[1], item[2]))
    cursor = start
    seen: set[int] = set()
    for left, right, code in spans:
        if left > cursor + 1e-6:
            return False, "stage_window_has_gap"
        if code != origin_code:
            return False, "window_stage_differs_from_origin_stage"
        if left < cursor - 1e-6 and code not in seen:
            return False, "overlapping_source_stage_intervals"
        cursor = max(cursor, right)
        seen.add(code)
    if cursor < end - 1e-6:
        return False, "stage_window_not_fully_covered"
    if len(seen) != 1:
        return False, "stage_window_not_stage_pure"
    return True, "stage_pure_at_origin"


def _row_support_status(
    row: Mapping[str, Any],
    record: Mapping[str, Any],
    record_reasons: Sequence[str],
    quality_intervals: Sequence[Mapping[str, Any]],
) -> tuple[bool, list[str]]:
    reasons = list(record_reasons)
    if row.get("source_sample_mapping_status") != "nominal_bounds_mapped":
        reasons.append("nominal_source_sample_mapping_unavailable")
    sample_start = _finite(row.get("nominal_source_sample_start"))
    sample_end = _finite(row.get("nominal_source_sample_end_exclusive"))
    if sample_start is None or sample_end is None or sample_end <= sample_start or not sample_start.is_integer() or not sample_end.is_integer():
        reasons.append("nominal_source_sample_bounds_invalid")
    if row.get("actual_sample_contributors_status") != "finite_causal_conservative_bound":
        reasons.append("finite_causal_sample_contributors_unavailable")
    actual_start = _finite(row.get("actual_source_sample_start"))
    actual_end = _finite(row.get("actual_source_sample_end_exclusive"))
    rate = _finite(row.get("source_sfreq_hz"))
    if rate is None or not math.isclose(rate, PILOT_SFREQ_HZ, rel_tol=0.0, abs_tol=1e-9):
        reasons.append("source_sample_rate_does_not_match_pilot")
    nominal_time_start = _finite(row.get("nominal_source_time_start_sec"))
    nominal_time_end = _finite(row.get("nominal_source_time_end_sec"))
    t_actual_start = _finite(row.get("actual_source_time_start_sec"))
    t_actual_end = _finite(row.get("actual_source_time_end_sec"))
    if actual_start is None or actual_end is None or actual_end <= actual_start or rate is None or rate <= 0:
        reasons.append("actual_source_sample_bounds_invalid")
    elif t_actual_start is None or t_actual_end is None or not math.isclose(t_actual_start, actual_start / rate, rel_tol=0.0, abs_tol=1e-6) or not math.isclose(t_actual_end, actual_end / rate, rel_tol=0.0, abs_tol=1e-6):
        reasons.append("actual_source_sample_time_mismatch")
    effective = record.get("effective_time_support", {})
    fir = effective.get("eeg_bandpass", {}) if isinstance(effective, Mapping) else {}
    grid = record.get("edf_sample_grid", {})
    tap_count = _finite(fir.get("tap_count")) if isinstance(fir, Mapping) else None
    source_count = _finite(grid.get("sample_count")) if isinstance(grid, Mapping) else None
    if (
        sample_start is not None
        and sample_end is not None
        and sample_start.is_integer()
        and sample_end.is_integer()
        and tap_count is not None
        and tap_count.is_integer()
        and source_count is not None
        and source_count.is_integer()
    ):
        expected_actual_start = max(0, int(sample_start) - int(tap_count) + 1)
        expected_actual_end = int(sample_end)
        if int(sample_end) > int(source_count):
            reasons.append("nominal_window_exceeds_verified_source_grid")
        if (
            actual_start is None
            or actual_end is None
            or not actual_start.is_integer()
            or not actual_end.is_integer()
            or int(actual_start) != expected_actual_start
            or int(actual_end) != expected_actual_end
        ):
            reasons.append("actual_support_does_not_match_causal_contract")
    else:
        reasons.append("causal_support_bound_cannot_be_reconstructed")
    t_start, t_end = _finite(row.get("t_start")), _finite(row.get("t_end"))
    if rate is None or nominal_time_start is None or nominal_time_end is None or t_start is None or t_end is None:
        reasons.append("nominal_source_time_mapping_invalid")
    elif (
        not math.isclose(nominal_time_start, t_start, rel_tol=0.0, abs_tol=1e-6)
        or not math.isclose(nominal_time_end, t_end, rel_tol=0.0, abs_tol=1e-6)
        or sample_start is None
        or sample_end is None
        or not math.isclose(sample_start, t_start * rate, rel_tol=0.0, abs_tol=1e-5)
        or not math.isclose(sample_end, t_end * rate, rel_tol=0.0, abs_tol=1e-5)
    ):
        reasons.append("nominal_source_time_sample_mismatch")
    if row.get("input_sample_finite_status") != "all_finite" or _finite(row.get("input_sample_gap_count")) != 0:
        reasons.append("nonfinite_or_gapped_input_window")
    if not _truth(row.get("qc_ok_eeg")):
        reasons.append("eeg_window_qc_not_pass")
    if not _truth(row.get("qc_ok_ppg")) or _finite(row.get("ppg_rate_bpm")) is None:
        reasons.append("present_window_ppg_measurement_unavailable")
    if t_actual_start is not None and t_actual_end is not None:
        for interval in quality_intervals:
            if interval.get("clock") != "original_raw_seconds":
                reasons.append("quality_interval_clock_unknown")
                continue
            left, right = _finite(interval.get("start_sec")), _finite(interval.get("end_sec"))
            if left is None or right is None:
                reasons.append("quality_interval_bounds_invalid")
            elif (
                (right == left and t_actual_start <= left < t_actual_end)
                or (right > left and right > t_actual_start and left < t_actual_end)
            ):
                reasons.append("support_overlaps_rejected_source_quality_interval")
    return not reasons, sorted(set(reasons))


def _events(path: Path) -> tuple[list[dict[str, Any]], str | None]:
    frame = pd.read_csv(path, sep="\t", keep_default_na=False)
    required = {"onset", "duration", "stage_hum"}
    if not required.issubset(frame.columns):
        raise ValueError(f"events TSV missing required source columns: {sorted(required - set(frame.columns))}")
    starts = pd.to_numeric(frame["onset"], errors="coerce")
    durations = pd.to_numeric(frame["duration"], errors="coerce")
    if starts.isna().any() or durations.isna().any() or (durations <= 0).any():
        raise ValueError("source stage intervals contain invalid onset/duration values")
    return frame[["onset", "duration", "stage_hum"]].to_dict(orient="records"), _sha256(path)


def _hash_frame(path: Path) -> str:
    return _sha256(path)


def _compare_replay(current: pd.DataFrame, previous: pd.DataFrame) -> dict[str, Any]:
    if list(current.columns) != list(previous.columns):
        return {"status": "mismatch", "reason": "feature_columns_differ"}
    sort_keys = [key for key in ("file", "epoch_id") if key in current.columns]
    current = current.sort_values(sort_keys, kind="stable").reset_index(drop=True) if sort_keys else current.reset_index(drop=True)
    previous = previous.sort_values(sort_keys, kind="stable").reset_index(drop=True) if sort_keys else previous.reset_index(drop=True)
    if len(current) != len(previous):
        return {"status": "mismatch", "reason": "feature_row_count_differs", "current_rows": len(current), "reference_rows": len(previous)}
    if sort_keys and not current[sort_keys].equals(previous[sort_keys]):
        return {"status": "mismatch", "reason": "feature_row_identity_differs"}
    numeric_columns = []
    nonnumeric_columns = []
    maximum_absolute_difference = 0.0
    for column in current.columns:
        if column in sort_keys:
            continue
        left = pd.to_numeric(current[column], errors="coerce")
        right = pd.to_numeric(previous[column], errors="coerce")
        is_numeric = pd.api.types.is_numeric_dtype(current[column]) or pd.api.types.is_numeric_dtype(previous[column])
        if is_numeric:
            a, b = left.to_numpy(dtype=float), right.to_numpy(dtype=float)
            if not np.array_equal(np.isnan(a), np.isnan(b)) or not np.allclose(a, b, atol=1e-10, rtol=1e-8, equal_nan=True):
                return {"status": "mismatch", "reason": f"numeric_feature_differs:{column}"}
            finite = np.isfinite(a) & np.isfinite(b)
            if np.any(finite):
                maximum_absolute_difference = max(maximum_absolute_difference, float(np.max(np.abs(a[finite] - b[finite]))))
            numeric_columns.append(column)
        else:
            if not current[column].astype(str).equals(previous[column].astype(str)):
                return {"status": "mismatch", "reason": f"categorical_feature_differs:{column}"}
            nonnumeric_columns.append(column)
    return {
        "status": "reproduced",
        "atol": 1e-10,
        "rtol": 1e-8,
        "maximum_absolute_numeric_difference": maximum_absolute_difference,
        "numeric_column_count": len(numeric_columns),
        "nonnumeric_column_count": len(nonnumeric_columns),
    }


def _canonical_surface_text(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize CSV round-trips, including missing values, for exact ledgers."""
    def cell(value: Any) -> str:
        try:
            if pd.isna(value):
                return ""
        except (TypeError, ValueError):
            pass
        return str(value)
    return frame.apply(lambda column: column.map(cell))


def audit_continuous_pilot(
    features_table: Path,
    qc_dir: Path,
    events_by_subject: Mapping[str, Path],
    output_dir: Path,
    *,
    freeze_manifest: Path,
    replay_reference: Path | None = None,
    window_sec: float = 30.0,
) -> dict[str, Any]:
    """Write a chart-free source-support, stage and timestamp-pair audit."""
    features_table, qc_dir, output_dir = Path(features_table).resolve(), Path(qc_dir).resolve(), Path(output_dir).resolve()
    event_paths = {str(key): Path(value).resolve() for key, value in events_by_subject.items()}
    if not features_table.is_file() or not qc_dir.is_dir() or not event_paths:
        raise ValueError("features table, QC sidecar directory and event inputs must exist")
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite pilot audit output: {output_dir}")
    freeze_hash, freeze_inputs, frozen_hashes = _load_freeze_manifest(Path(freeze_manifest))
    frozen_by_role: dict[str, set[str]] = {}
    for item in freeze_inputs:
        frozen_by_role.setdefault(item["role"], set()).add(_canonical_path(item["path"]))
    if _canonical_path(Path(__file__).resolve()) not in frozen_by_role.get("analysis_audit", set()):
        raise ValueError("freeze manifest does not bind the active chart-free audit code")
    audit_events_by_subject: dict[str, str] = {}
    for subject, path in event_paths.items():
        key = subject.casefold()
        path_subject = _subject_from_path(path)
        if key in audit_events_by_subject or path_subject != key:
            raise ValueError("each audit event path must identify the same unique subject as its --events key")
        audit_events_by_subject[key] = _canonical_path(path)
    frozen_events_by_subject: dict[str, str] = {}
    for item in freeze_inputs:
        if item["role"] != "events":
            continue
        event_path = Path(item["path"])
        subject = _subject_from_path(event_path)
        if subject is None or subject in frozen_events_by_subject:
            raise ValueError("freeze manifest event inputs must uniquely identify their subjects")
        frozen_events_by_subject[subject] = _canonical_path(event_path)
    if audit_events_by_subject != frozen_events_by_subject:
        raise ValueError("freeze manifest event subject-to-path bindings do not exactly match audit inputs")
    before_hashes = {
        "features_table": _hash_frame(features_table),
        "freeze_manifest": freeze_hash,
        **frozen_hashes,
    }
    event_rows: dict[str, list[dict[str, Any]]] = {}
    for subject, path in event_paths.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        subject_key = subject.casefold()
        event_rows[subject_key], before_hashes[f"events:{subject_key}"] = _events(path)
    frame = pd.read_csv(features_table, low_memory=False)
    required = {
        "file", "epoch_id", "t_start", "t_end", "ppg_rate_bpm", "qc_ok_ppg",
        "qc_ok_eeg", "source_sample_mapping_status", "nominal_source_sample_start",
        "nominal_source_sample_end_exclusive", "nominal_source_time_start_sec",
        "nominal_source_time_end_sec", "actual_sample_contributors_status",
        "actual_source_sample_start", "actual_source_sample_end_exclusive",
        "actual_source_time_start_sec", "actual_source_time_end_sec", "source_sfreq_hz",
        "input_sample_finite_status", "input_sample_gap_count",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"feature table missing pilot support columns: {missing}")
    if frame["file"].isna().any() or frame["epoch_id"].isna().any():
        raise ValueError("feature table has missing recording or epoch identity")
    frame["file"] = frame["file"].astype(str).map(lambda value: Path(value).name)
    frame["epoch_id"] = pd.to_numeric(frame["epoch_id"], errors="coerce")
    epoch_values = frame["epoch_id"].to_numpy(dtype=float)
    rounded_epoch_values = np.rint(epoch_values)
    if (
        not np.isfinite(epoch_values).all()
        or np.any(epoch_values < 0)
        or np.any(epoch_values > 2**53)
        or np.any(epoch_values != rounded_epoch_values)
    ):
        raise ValueError("feature epoch identity is nonnumeric, non-integral, negative or duplicated")
    frame["epoch_id"] = rounded_epoch_values.astype(np.int64)
    if frame.duplicated(["file", "epoch_id"]).any():
        raise ValueError("feature epoch identity is nonnumeric, non-integral, negative or duplicated")
    frame = frame.sort_values(["file", "epoch_id"], kind="stable").reset_index(drop=True)
    expected_subjects = set(event_rows)
    file_subject = {
        raw_file: (match.group(0).casefold() if (match := re.search(r"sub-[A-Za-z0-9]+", raw_file)) else None)
        for raw_file in frame["file"].unique()
    }
    if set(file_subject.values()) != expected_subjects:
        raise ValueError(f"feature subjects {sorted(set(file_subject.values()))} do not match event inputs {sorted(expected_subjects)}")

    records: dict[str, dict[str, Any]] = {}
    record_errors: dict[str, list[str]] = {}
    for raw_file in frame["file"].unique():
        record, reasons = _support_record(qc_dir, raw_file, PILOT_SFREQ_HZ)
        sidecar_path = qc_dir / f"{Path(raw_file).stem}_qc_artifacts.json"
        before_hashes[f"qc_sidecar:{raw_file}"] = _sha256(sidecar_path) if sidecar_path.is_file() else "missing"
        if record is not None:
            records[raw_file] = record
            source = record.get("source", {})
            source_path = Path(str(source.get("path", ""))) if isinstance(source, Mapping) else Path()
            if source_path.is_file():
                before_hashes[f"raw_source:{raw_file}"] = _sha256(source_path)
        record_errors[raw_file] = reasons
    frozen_source_by_name = {
        Path(item["path"]).name.casefold(): _canonical_path(item["path"])
        for item in freeze_inputs if item["role"] == "source_edf"
    }
    if {Path(name).name.casefold() for name in frame["file"].unique()} != set(frozen_source_by_name):
        raise ValueError("freeze manifest source EDF basenames do not exactly match feature recordings")
    for raw_file, record in records.items():
        source = record.get("source", {})
        source_path = str(source.get("path", "")) if isinstance(source, Mapping) else ""
        if _canonical_path(source_path) != frozen_source_by_name.get(Path(raw_file).name.casefold()):
            record_errors[raw_file].append("source_path_differs_from_freeze_manifest")

    stage_rows: list[dict[str, Any]] = []
    support_rows: list[dict[str, Any]] = []
    support_ok: dict[tuple[str, int], bool] = {}
    quality_by_file: dict[str, list[Mapping[str, Any]]] = {}
    for raw_file, record in records.items():
        quality = record.get("source_quality_intervals", {})
        intervals = quality.get("intervals", []) if isinstance(quality, Mapping) else []
        quality_by_file[raw_file] = [item for item in intervals if isinstance(item, Mapping)] if isinstance(intervals, list) else []

    for _, row_series in frame.iterrows():
        row = row_series.to_dict()
        raw_file = str(row["file"])
        subject = file_subject[raw_file]
        start, end = _finite(row.get("t_start")), _finite(row.get("t_end"))
        epoch_id = int(row["epoch_id"])
        ok, reasons = _row_support_status(
            row,
            records.get(raw_file, {}),
            record_errors[raw_file],
            quality_by_file.get(raw_file, []),
        )
        support_ok[(raw_file, epoch_id)] = ok
        origin_stage, origin_reason = (None, "window_time_invalid")
        pure, pure_reason = False, "window_time_invalid"
        if start is not None and end is not None and end > start:
            origin_stage, origin_reason = _stage_at_point(event_rows[subject], end)
            pure, pure_reason = _stage_purity(event_rows[subject], start, end, origin_stage)
        stage_rows.append({
            "file": raw_file, "subject": subject, "epoch_id": epoch_id,
            "t_start": start, "t_end": end,
            "stage_at_origin_code": origin_stage,
            "stage_at_origin": _STAGES.get(origin_stage) if origin_stage is not None else None,
            "stage_at_origin_status": origin_reason,
            "stage_pure_at_origin": bool(pure),
            "stage_window_status": pure_reason,
            "row_support_eligible": bool(ok),
        })
        support_rows.append({
            "file": raw_file, "subject": subject, "epoch_id": epoch_id,
            "t_start": start, "t_end": end,
            "source_sha256": (records.get(raw_file, {}).get("source", {}) or {}).get("sha256"),
            "sample_mapping_status": row.get("source_sample_mapping_status"),
            "nominal_source_sample_start": _finite(row.get("nominal_source_sample_start")),
            "nominal_source_sample_end_exclusive": _finite(row.get("nominal_source_sample_end_exclusive")),
            "nominal_source_time_start_sec": _finite(row.get("nominal_source_time_start_sec")),
            "nominal_source_time_end_sec": _finite(row.get("nominal_source_time_end_sec")),
            "actual_sample_contributors_status": row.get("actual_sample_contributors_status"),
            "actual_source_sample_start": _finite(row.get("actual_source_sample_start")),
            "actual_source_sample_end_exclusive": _finite(row.get("actual_source_sample_end_exclusive")),
            "actual_source_time_start_sec": _finite(row.get("actual_source_time_start_sec")),
            "actual_source_time_end_sec": _finite(row.get("actual_source_time_end_sec")),
            "input_sample_finite_status": row.get("input_sample_finite_status"),
            "input_sample_gap_count": _finite(row.get("input_sample_gap_count")),
            "qc_ok_eeg": _truth(row.get("qc_ok_eeg")),
            "ppg_rate_present": _finite(row.get("ppg_rate_bpm")) is not None,
            "qc_ok_ppg": _truth(row.get("qc_ok_ppg")),
            "row_support_eligible": ok,
            "exclusion_reasons": ";".join(reasons),
        })

    pair_rows: list[dict[str, Any]] = []
    for raw_file, group in frame.groupby("file", sort=False):
        rows = {int(row["epoch_id"]): row.to_dict() for _, row in group.iterrows()}
        subject = file_subject[raw_file]
        for origin_id in sorted(rows):
            origin = rows[origin_id]
            for horizon, lag in _HORIZONS.items():
                target = rows.get(origin_id + lag)
                reasons: list[str] = []
                if target is None:
                    reasons.append("target_epoch_missing")
                    target_end = None
                else:
                    target_end = _finite(target.get("t_end"))
                    for epoch in range(origin_id, origin_id + lag + 1):
                        item = rows.get(epoch)
                        if item is None:
                            reasons.append(f"intervening_epoch_missing:{epoch}")
                            continue
                        if not support_ok.get((raw_file, epoch), False):
                            reasons.append(f"row_support_invalid:{epoch}")
                        a, b = _finite(item.get("t_start")), _finite(item.get("t_end"))
                        if a is None or b is None or not math.isclose(b - a, window_sec, rel_tol=0.0, abs_tol=1e-6):
                            reasons.append(f"window_duration_invalid:{epoch}")
                        if epoch > origin_id:
                            prev = rows.get(epoch - 1)
                            prev_end = _finite(prev.get("t_end")) if prev else None
                            if a is None or prev_end is None or not math.isclose(a, prev_end, rel_tol=0.0, abs_tol=1e-6):
                                reasons.append(f"timestamp_gap:{epoch - 1}:{epoch}")
                    origin_end = _finite(origin.get("t_end"))
                    if origin_end is None:
                        reasons.append("origin_timestamp_invalid")
                    elif target_end is not None and not math.isclose(target_end - origin_end, lag * window_sec, rel_tol=0.0, abs_tol=1e-6):
                        reasons.append("horizon_timestamp_mismatch")
                pair_rows.append({
                    "file": raw_file, "subject": subject, "origin_epoch_id": origin_id,
                    "target_epoch_id": origin_id + lag, "horizon": horizon,
                    "nominal_lag_rows": lag, "origin_t_end": _finite(origin.get("t_end")),
                    "target_t_end": target_end,
                    "actual_horizon_sec": (
                        target_end - float(origin["t_end"])
                        if target_end is not None and _finite(origin.get("t_end")) is not None else None
                    ),
                    "pair_support_eligible": not reasons,
                    "exclusion_reasons": ";".join(sorted(set(reasons))),
                })

    support_contract_hashes = {
        raw_file: _support_contract_sha256(record)
        for raw_file, record in records.items()
    }
    replay = None
    if replay_reference is not None:
        reference = Path(replay_reference).resolve()
        reference_features = reference / "features.csv"
        if not reference_features.is_file():
            raise FileNotFoundError(f"replay reference features.csv missing: {reference_features}")
        replay = _compare_replay(frame, pd.read_csv(reference_features, low_memory=False))
        reference_validation_path = reference / "pilot_validation.json"
        if not reference_validation_path.is_file():
            replay = {"status": "mismatch", "reason": "replay_reference_missing:pilot_validation.json"}
        else:
            reference_validation = json.loads(reference_validation_path.read_text(encoding="utf-8"))
            if reference_validation.get("freeze_manifest_sha256") != freeze_hash:
                replay = {"status": "mismatch", "reason": "frozen_protocol_config_or_code_identity_differs"}
            elif reference_validation.get("support_contract_sha256") != support_contract_hashes:
                replay = {"status": "mismatch", "reason": "support_provenance_contract_differs"}
        for name in ("pilot_support_ledger.csv", "pilot_stage_audit.csv", "pilot_temporal_pairs.csv"):
            prior = reference / name
            if not prior.is_file():
                replay = {"status": "mismatch", "reason": f"replay_reference_missing:{name}"}
                break
            if name == "pilot_support_ledger.csv":
                current_df = pd.DataFrame(support_rows)
            elif name == "pilot_stage_audit.csv":
                current_df = pd.DataFrame(stage_rows)
            else:
                current_df = pd.DataFrame(pair_rows)
            prior_df = pd.read_csv(prior, keep_default_na=False)
            if list(current_df.columns) != list(prior_df.columns) or not _canonical_surface_text(current_df).equals(_canonical_surface_text(prior_df)):
                replay = {"status": "mismatch", "reason": f"replay_surface_differs:{name}"}
                break

    after_hashes = {
        "features_table": _hash_frame(features_table),
        "freeze_manifest": _sha256(Path(freeze_manifest).resolve()),
    }
    for item in freeze_inputs:
        input_path = Path(item["path"])
        after_hashes[f"freeze_input:{item['role']}:{input_path}"] = (
            _sha256(input_path) if input_path.is_file() else "missing"
        )
    for subject, path in event_paths.items():
        after_hashes[f"events:{subject}"] = _sha256(path)
    for raw_file, record in records.items():
        sidecar_path = qc_dir / f"{Path(raw_file).stem}_qc_artifacts.json"
        after_hashes[f"qc_sidecar:{raw_file}"] = _sha256(sidecar_path) if sidecar_path.is_file() else "missing"
        source = record.get("source", {})
        source_path = Path(str(source.get("path", ""))) if isinstance(source, Mapping) else Path()
        if source_path.is_file():
            after_hashes[f"raw_source:{raw_file}"] = _sha256(source_path)
    changed_inputs = before_hashes != after_hashes
    if changed_inputs:
        replay = {"status": "mismatch", "reason": "input_changed_during_audit"}

    output_dir.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(features_table, output_dir / "features.csv")
    support_frame = pd.DataFrame(support_rows)
    stage_frame = pd.DataFrame(stage_rows)
    pair_frame = pd.DataFrame(pair_rows)
    support_frame.to_csv(output_dir / "pilot_support_ledger.csv", index=False)
    stage_frame.to_csv(output_dir / "pilot_stage_audit.csv", index=False)
    pair_frame.to_csv(output_dir / "pilot_temporal_pairs.csv", index=False)
    leakage = {
        "schema": "nmd_analysis.continuous_pilot_leakage_ledger.v1",
        "claim_status": "no_biological_claim",
        "predictor_scope": "pilot performs no prediction; classifications document measurement scope only",
        "variables": [
            {"name": "ppg_rate_bpm", "class": "PRESENT_ONLY", "scope": "one current 30-s raw PPG window; window-local median/MAD and peak detection"},
            {"name": "all other candidate predictors", "class": "UNKNOWN", "scope": "not admitted by this measurement-only pilot"},
        ],
        "admitted_predictors": [],
    }
    (output_dir / "pilot_leakage_ledger.json").write_text(json.dumps(leakage, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    counts = {
        horizon: {
            "candidate_pairs": int((pair_frame["horizon"] == horizon).sum()),
            "eligible_pairs": int(((pair_frame["horizon"] == horizon) & pair_frame["pair_support_eligible"]).sum()),
        }
        for horizon in _HORIZONS
    }
    expected_subjects = set(event_rows)
    stage_coverage = {
        _STAGES[code]: {
            "eligible_rows": int((
                stage_frame["stage_pure_at_origin"]
                & stage_frame["row_support_eligible"]
                & (stage_frame["stage_at_origin_code"] == code)
            ).sum()),
            "subjects": sorted(
                stage_frame.loc[
                    stage_frame["stage_pure_at_origin"]
                    & stage_frame["row_support_eligible"]
                    & (stage_frame["stage_at_origin_code"] == code),
                    "subject",
                ].astype(str).unique().tolist()
            ),
        }
        for code in (0, 2)
    }
    stage_coverage_pass = all(
        set(stage_coverage[_STAGES[code]]["subjects"]) == expected_subjects
        for code in (0, 2)
    )
    if any(record_errors.values()):
        pilot_gate_status = "FAIL_SUPPORT_PROVENANCE"
    elif not stage_coverage_pass:
        pilot_gate_status = "INCONCLUSIVE_STAGE_COVERAGE"
    elif any(counts[horizon]["eligible_pairs"] == 0 for horizon in _HORIZONS):
        pilot_gate_status = "INCONCLUSIVE_NO_ELIGIBLE_PAIR_AT_FIXED_HORIZON"
    elif replay is None:
        pilot_gate_status = "PENDING_REPLAY"
    elif replay.get("status") != "reproduced":
        pilot_gate_status = "FAIL_REPLAY"
    else:
        pilot_gate_status = "PASS_BOUNDED_TECHNICAL_ONLY"
    report = {
        "schema": "nmd_analysis.continuous_pilot_audit.v1",
        "status": "audited" if not changed_inputs and (replay is None or replay.get("status") == "reproduced") else "inconclusive_or_failed",
        "stage": "measurement_only",
        "charts_generated": False,
        "outcomes_calculated": False,
        "claim_status": "no_biological_claim",
        "scientific_qualification": "not_assessed",
        "bounded_pilot_gate_status": pilot_gate_status,
        "full_cohort_scoring_authorized": False,
        "counts": {
            "feature_rows": int(len(frame)),
            "support_eligible_rows": int(support_frame["row_support_eligible"].sum()),
            "stage_pure_at_origin_rows": int(stage_frame["stage_pure_at_origin"].sum()),
            "stage_pure_origin_counts": {
                str(key): int(value)
                for key, value in stage_frame.loc[stage_frame["stage_pure_at_origin"], "stage_at_origin"].value_counts(dropna=True).items()
            },
            "required_context_stage_coverage": stage_coverage,
            "stage_coverage_gate": "PASS" if stage_coverage_pass else "INCONCLUSIVE",
        "pairs_by_horizon": counts,
        },
        "replay_comparison": replay,
        "freeze_manifest_sha256": freeze_hash,
        "freeze_manifest_inputs": freeze_inputs,
        "support_contract_sha256": support_contract_hashes,
        "input_hashes_before": before_hashes,
        "input_hashes_after": after_hashes,
        "support_record_status": {name: "valid" if not reasons else "unknown" for name, reasons in record_errors.items()},
        "support_record_reasons": record_errors,
        "provenance": {
            "audit_code_sha256": _sha256(Path(__file__).resolve()),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "window_sec": float(window_sec),
            "source_sfreq_hz": PILOT_SFREQ_HZ,
            "horizons": dict(_HORIZONS),
            "stage_source_column": "stage_hum",
            "stage_codebook": {str(code): label for code, label in _STAGES.items()},
        },
    }
    (output_dir / "pilot_validation.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if changed_inputs or (replay is not None and replay.get("status") != "reproduced"):
        report["status"] = "inconclusive_or_failed"
    return report


def _parse_event_arg(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--events must be SUBJECT=PATH")
    subject, path = value.split("=", 1)
    if not subject or not path:
        raise argparse.ArgumentTypeError("--events must be SUBJECT=PATH")
    return subject, Path(path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features-table", type=Path, required=True)
    parser.add_argument("--qc-dir", type=Path, required=True)
    parser.add_argument("--events", type=_parse_event_arg, action="append", required=True, metavar="SUBJECT=PATH")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--freeze-manifest", type=Path, required=True)
    parser.add_argument("--replay-reference", type=Path)
    parser.add_argument("--window-sec", type=float, default=30.0)
    args = parser.parse_args(argv)
    events = dict(args.events)
    if len(events) != len(args.events):
        parser.error("each --events subject may be specified once")
    try:
        report = audit_continuous_pilot(
            args.features_table, args.qc_dir, events, args.out_dir,
            freeze_manifest=args.freeze_manifest,
            replay_reference=args.replay_reference, window_sec=args.window_sec,
        )
    except Exception as exc:
        parser.exit(2, f"pilot audit failed closed: {type(exc).__name__}: {exc}\n")
    print(json.dumps(report, indent=2))
    return 0 if report["bounded_pilot_gate_status"] in {
        "PENDING_REPLAY", "PASS_BOUNDED_TECHNICAL_ONLY"
    } else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
