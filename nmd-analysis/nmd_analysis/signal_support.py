"""Conservative reader for the v1 executed signal-support export."""

from __future__ import annotations

import json
import math
from pathlib import Path
import re
from typing import Any, Mapping

import h5py
import numpy as np


SCHEMA = "mndm.signal_support_export.v1"
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_OP_STATUSES = {"applied", "skipped", "fallback", "failed"}
_ALLOWED_UNKNOWN_SUPPORT = {"unknown", "nonlocal", "not_assessed"}


def _scalar(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, np.generic):
        return _scalar(value.item())
    return value


def _json_dataset(group: h5py.Group, name: str, *, default: Any = None) -> Any:
    alias = name.removesuffix("_json")
    if alias in group and name in group:
        raise ValueError(f"ambiguous H5 alias: {name}/{alias}")
    if name not in group:
        if alias in group:
            node = group[alias]
            if isinstance(node, h5py.Dataset) and node.shape == (0,):
                return []
            raise ValueError(f"unsupported non-JSON representation: {alias}")
        return default
    value = _scalar(group[name][()])
    if not isinstance(value, str):
        raise ValueError(f"{name} is not a JSON string")
    def reject_constant(token: str) -> Any:
        raise ValueError(f"non-finite JSON constant: {token}")

    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(value, parse_constant=reject_constant, object_pairs_hook=unique_keys)


def _text_array(handle: h5py.File, path: str) -> list[str]:
    if path not in handle or not isinstance(handle[path], h5py.Dataset):
        return []
    return [str(_scalar(item)) for item in handle[path][:]]


def _unknown(reason: str, *, schema: Any = None, status: str = "unknown") -> dict[str, Any]:
    return {
        "status": status,
        "schema": schema,
        "validation": {"status": "invalid_or_unavailable", "reasons": [reason]},
        "source_hash_status": "unknown",
        "row_alignment_status": "unknown",
        "temporal_support": {"status": "unknown", "reason": reason},
        "scientific_qualification": "not_assessed",
        "execution_records": [],
        "per_epoch_input_extent": [],
        "source_quality_intervals": [],
        "reference_fit_population": {},
    }


def _validate_source(record: Mapping[str, Any], reasons: list[str]) -> None:
    source = record.get("source")
    if not isinstance(source, Mapping):
        reasons.append("source_identity_missing")
        return
    if not isinstance(source.get("path"), str) or not source.get("path"):
        reasons.append("source_path_missing")
    if source.get("exists") is not True:
        reasons.append("source_existence_not_verified")
    digest = source.get("sha256")
    if not isinstance(digest, str) or not _HASH_RE.fullmatch(digest):
        reasons.append("source_sha256_invalid")
    if source.get("sha256_after") != digest:
        reasons.append("source_hash_not_stable")
    if source.get("hash_stable") is not True:
        reasons.append("source_hash_stability_not_verified")


def _validate_execution(record: Mapping[str, Any], reasons: list[str]) -> None:
    operations = record.get("operations")
    if not isinstance(operations, list):
        reasons.append("execution_operations_missing")
        return
    ids: set[str] = set()
    for operation in operations:
        if not isinstance(operation, Mapping):
            reasons.append("operation_not_object")
            continue
        operation_id = operation.get("operation_id")
        if not isinstance(operation_id, str) or not operation_id or operation_id in ids:
            reasons.append("operation_id_missing_or_duplicate")
        ids.add(str(operation_id))
        if operation.get("status") not in _OP_STATUSES:
            reasons.append(f"operation_status_invalid:{operation.get('status')}")


def _strict_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        return None
    return int(value)


def _validate_rows(
    handle: h5py.File,
    rows: Any,
    execution_records: list[Mapping[str, Any]],
    reasons: list[str],
) -> None:
    if not isinstance(rows, list):
        reasons.append("per_epoch_input_extent_missing_or_not_list")
        return
    required = {"row_index", "epoch_id", "nominal_time_start_sec", "nominal_time_end_sec", "raw_file", "support_status"}
    epoch_ids = np.asarray(handle["epoch_id"][:]) if "epoch_id" in handle else np.asarray([])
    starts = np.asarray(handle["window_start"][:], dtype=float) if "window_start" in handle else np.asarray([])
    ends = np.asarray(handle["window_end"][:], dtype=float) if "window_end" in handle else np.asarray([])
    raw_files = _text_array(handle, "row_source/raw_file")
    if not rows or not (epoch_ids.ndim == starts.ndim == ends.ndim == 1) or not (len(epoch_ids) == len(starts) == len(ends) == len(raw_files) == len(rows)):
        reasons.append("per_epoch_length_mismatch")
        return
    if len(np.unique(epoch_ids)) != len(epoch_ids):
        reasons.append("h5_epoch_ids_not_unique")
    if any(_strict_int(v) is None for v in epoch_ids):
        reasons.append("h5_epoch_ids_not_integer")
    if not np.all(np.isfinite(starts) & np.isfinite(ends) & (ends > starts)):
        reasons.append("h5_nominal_bounds_invalid")
    operation_ids_by_raw_file = {
        str(record.get("raw_file")): {
            str(operation.get("operation_id"))
            for operation in record.get("operations", [])
            if isinstance(operation, Mapping)
        }
        for record in execution_records
    }
    record_by_raw_file = {str(record.get("raw_file")): record for record in execution_records}
    seen: set[int] = set()
    for expected_index, row in enumerate(rows):
        if not isinstance(row, Mapping) or not required.issubset(row):
            reasons.append(f"row_required_field_missing:{expected_index}")
            continue
        idx = row.get("row_index")
        idx_int = _strict_int(idx)
        if idx_int is None:
            reasons.append(f"row_index_invalid:{expected_index}")
            continue
        if idx_int != expected_index or idx_int in seen:
            reasons.append(f"row_index_alignment_invalid:{expected_index}")
        seen.add(idx_int)
        row_epoch = _strict_int(row.get("epoch_id"))
        if row_epoch is None:
            reasons.append(f"epoch_id_invalid:{expected_index}")
        elif row_epoch != int(epoch_ids[expected_index]):
            reasons.append(f"epoch_id_mismatch:{expected_index}")
        for key, expected in (("nominal_time_start_sec", starts[expected_index]), ("nominal_time_end_sec", ends[expected_index])):
            try:
                actual = float(row[key])
            except Exception:
                reasons.append(f"{key}_invalid:{expected_index}")
                continue
            if not math.isfinite(actual) or not math.isclose(actual, float(expected), rel_tol=0.0, abs_tol=1e-6):
                reasons.append(f"{key}_mismatch:{expected_index}")
        row_raw_file = str(row.get("raw_file"))
        if row_raw_file != raw_files[expected_index]:
            reasons.append(f"raw_file_mismatch:{expected_index}")
        if str(row.get("support_status")) not in _ALLOWED_UNKNOWN_SUPPORT:
            reasons.append(f"finite_or_unsupported_support_status:{expected_index}")
        record = record_by_raw_file.get(row_raw_file)
        if record is None:
            reasons.append(f"execution_record_missing_for_raw_file:{expected_index}")
        else:
            row_identity = row.get("source_identity")
            record_identity = record.get("source")
            if not isinstance(row_identity, Mapping) or not isinstance(record_identity, Mapping):
                reasons.append(f"row_source_identity_missing:{expected_index}")
            elif row_identity.get("sha256") != record_identity.get("sha256"):
                reasons.append(f"row_source_hash_mismatch:{expected_index}")
            elif str(row_identity.get("path", "")).replace("\\", "/").rsplit("/", 1)[-1] != row_raw_file:
                reasons.append(f"row_source_path_mismatch:{expected_index}")
        refs = row.get("upstream_operation_ids", [])
        if not isinstance(refs, list) or any(str(ref) not in operation_ids_by_raw_file.get(row_raw_file, set()) for ref in refs):
            reasons.append(f"row_operation_reference_invalid:{expected_index}")
        clock = row.get("source_clock")
        if not isinstance(clock, Mapping) or record is None:
            reasons.append(f"row_source_clock_missing:{expected_index}")
        else:
            for key, record_key in (("input_sfreq_hz", "input_sfreq_hz"), ("target_sfreq_hz", "target_sfreq_hz")):
                try:
                    values = (float(clock[key]), float(record.get(record_key)))
                    if not all(math.isfinite(value) and value > 0 for value in values) or not math.isclose(*values, rel_tol=0.0, abs_tol=1e-9):
                        reasons.append(f"row_source_clock_mismatch:{expected_index}")
                except Exception:
                    reasons.append(f"row_source_clock_invalid:{expected_index}")
        for key in ("support_start_sec", "support_end_sec", "effective_start_sec", "effective_end_sec"):
            if key in row and row[key] is not None:
                reasons.append(f"effective_support_must_remain_unknown:{expected_index}")
        if row.get("nominal_clock_mapping_status") == "crop_offset_recorded" and record is not None:
            crop = record.get("crop", {})
            offset = crop.get("actual_tmin_sec") if crop.get("applied") else 0.0 if crop.get("reason") == "not_configured" else None
            if record.get("feature_time_clock", {}).get("reference") != "preprocessed_array_start" or offset is None:
                reasons.append(f"crop_clock_evidence_missing:{expected_index}")
            else:
                for mapped, nominal in (("nominal_original_time_start_sec", "nominal_time_start_sec"), ("nominal_original_time_end_sec", "nominal_time_end_sec")):
                    if row.get(mapped) is None or not math.isclose(float(row[mapped]), float(row[nominal]) + float(offset), rel_tol=0., abs_tol=1e-6):
                        reasons.append(f"crop_clock_mismatch:{expected_index}")


def _read(handle: h5py.File) -> dict[str, Any]:
    group_path = "provenance/signal_support_provenance"
    if group_path not in handle:
        return _unknown("signal_support_group_missing", status="legacy_missing")
    if not isinstance(handle[group_path], h5py.Group):
        return _unknown("signal_support_not_group", status="malformed")
    group = handle[group_path]
    schema = _scalar(group["schema"][()]) if "schema" in group else None
    if schema != SCHEMA:
        return _unknown("legacy_or_unsupported_signal_support_schema", schema=schema, status="unsupported")
    reasons: list[str] = []
    if _scalar(group["status"][()]) != "recorded" if "status" in group else True:
        reasons.append("export_status_not_recorded")
    temporal_status = _scalar(group["temporal_support_status"][()]) if "temporal_support_status" in group else "unknown"
    if temporal_status not in _ALLOWED_UNKNOWN_SUPPORT:
        reasons.append("top_level_support_status_not_unknown")
    execution_payload = _json_dataset(group, "execution_records_json", default=[])
    rows = _json_dataset(group, "per_epoch_input_extent_json", default=[])
    quality = _json_dataset(group, "source_quality_intervals_json", default=[])
    if not isinstance(execution_payload, list):
        reasons.append("execution_records_not_list")
        execution_payload = []
    if not execution_payload:
        reasons.append("execution_records_empty")
    records: list[Mapping[str, Any]] = []
    for item in execution_payload:
        outer_raw_file = item.get("raw_file") if isinstance(item, Mapping) else None
        record = item.get("record") if isinstance(item, Mapping) and isinstance(item.get("record"), Mapping) else item
        if not isinstance(record, Mapping):
            reasons.append("execution_record_not_object")
            continue
        record = dict(record)
        if outer_raw_file is not None:
            record.setdefault("raw_file", str(outer_raw_file))
        source_name = str(record.get("source", {}).get("path", "")).replace("\\", "/").rsplit("/", 1)[-1]
        if not outer_raw_file or record.get("raw_file") != outer_raw_file or source_name != outer_raw_file:
            reasons.append("execution_source_identity_mismatch")
        if item.get("validation_status") != "valid":
            reasons.append("producer_execution_validation_not_valid")
        if record.get("schema") != "mndm.signal_support_provenance.v1" or record.get("status") != "completed":
            reasons.append("execution_schema_or_completion_invalid")
        if any(existing.get("raw_file") == record.get("raw_file") for existing in records):
            reasons.append("duplicate_execution_source")
        records.append(record)
        _validate_source(record, reasons)
        _validate_execution(record, reasons)
    _validate_rows(handle, rows, records, reasons)
    if not isinstance(quality, list):
        reasons.append("source_quality_intervals_not_list")
        quality = []
    for interval in quality:
        if not isinstance(interval, Mapping):
            reasons.append("source_quality_interval_not_object")
            continue
        try:
            start, end = float(interval["start_sec"]), float(interval["end_sec"])
            if not math.isfinite(start) or not math.isfinite(end) or end < start:
                reasons.append("source_quality_interval_bounds_invalid")
        except (KeyError, TypeError, ValueError):
            reasons.append("source_quality_interval_bounds_missing")
    if "reference_fit_population_json" in group:
        fits = _json_dataset(group, "reference_fit_population_json")
        if not isinstance(fits, Mapping):
            raise ValueError("reference_fit_population is not an object")
    else:
        fits = _read_group_plain(group.get("reference_fit_population"))
    return {
        "status": "recorded" if not reasons else "malformed",
        "schema": schema,
        "validation": {"status": "valid" if not reasons else "invalid_or_unavailable", "reasons": reasons,
                       "scope": "recorded_source_identity_operations_and_epoch_alignment; fit_hashes_and_quality_interpretation_not_recomputed"},
        "source_hash_status": "recorded_only" if not reasons else "unknown",
        "row_alignment_status": "validated" if not reasons else "unknown",
        "temporal_support": {
            "status": "unknown",
            "reason": _scalar(group["temporal_support_reason"][()]) if "temporal_support_reason" in group else "not_certified",
        },
        "scientific_qualification": "not_assessed",
        "execution_records": records,
        "per_epoch_input_extent": rows,
        "source_quality_intervals": quality,
        "source_quality_status": _scalar(group["source_quality_status"][()]) if "source_quality_status" in group else "not_recorded",
        "reference_fit_population": fits,
    }


def _read_group_plain(group: h5py.Group | None) -> dict[str, Any]:
    if group is None:
        return {}
    result: dict[str, Any] = {}
    for key, item in group.items():
        if isinstance(item, h5py.Group):
            result[key] = _read_group_plain(item)
        else:
            value = item[()]
            value = _scalar(value)
            result[key] = value.tolist() if isinstance(value, np.ndarray) else value
    return result


def read_signal_support(path_or_handle: str | Path | h5py.File) -> dict[str, Any]:
    """Read and validate signal-support provenance conservatively.

    Recorded hashes are checked for shape and internal stability only. The
    reader does not rehash external source files and never upgrades unknown
    support to a finite or scientifically qualified status.
    """
    try:
        if isinstance(path_or_handle, h5py.File):
            result = _read(path_or_handle)
        else:
            with h5py.File(Path(path_or_handle), "r") as handle:
                result = _read(handle)
        json.dumps(result, allow_nan=False)
        return result
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, OSError, UnicodeError, OverflowError) as exc:
        return _unknown(f"malformed_signal_support:{type(exc).__name__}:{exc}", status="malformed")


__all__ = ["read_signal_support"]
