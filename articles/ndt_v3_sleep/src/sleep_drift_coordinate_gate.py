"""Run the frozen coordinate-support continuation gate for the E3 pilot.

The original E3 reference gate is intentionally left unchanged.  This wrapper
records that strict outcome for every row and evaluates a separately frozen,
coordinate-level rule.  An overall ``adjusted`` geometry status can continue
only when the policy proves that the adjustment is the permitted 9D Jacobian
conditioning case; it cannot be inferred from finite arrays or from a desired
prediction.  All source, support and normalization provenance is carried from
the original runner.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
from typing import Any, Iterable

import h5py
import numpy as np

from nmd_analysis.dynamical_families import drift
import sleep_drift_candidate as candidate


GATE_SCHEMA = "ndt.sleep.coordinate_support_gate.v1"
GATE_STATUS = "frozen_candidate_coordinate_support_policy"
EXPECTED_SPEC_SCHEMA = "ndt.sleep.sleep_drift_candidate.v1"


class CoordinateGateContractError(ValueError):
    """Raised when the frozen coordinate gate contract is malformed."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _json_safe(value: Any) -> Any:
    if isinstance(value, (bytes, np.bytes_)):
        return value.decode("utf-8")
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _scalar(value: Any) -> Any:
    if isinstance(value, (bytes, np.bytes_)):
        return value.decode("utf-8")
    return value.item() if isinstance(value, np.generic) else value


def _read_policy(path: Path) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    """Read and hash the policy before any source prediction is attempted."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema") != GATE_SCHEMA:
        raise CoordinateGateContractError("unexpected coordinate gate policy schema")
    if raw.get("status") != GATE_STATUS:
        raise CoordinateGateContractError("coordinate gate policy is not frozen")
    policy = raw.get("spec")
    expected = raw.get("frozen_spec_sha256")
    if not isinstance(policy, dict) or not isinstance(expected, str):
        raise CoordinateGateContractError("policy must contain a frozen policy and hash")
    actual = sha256_bytes(_canonical_json(policy))
    if actual != expected:
        raise CoordinateGateContractError("frozen policy hash does not match policy")
    return raw, policy, sha256_file(path), expected


def _candidate_config_path(policy_path: Path, raw: dict[str, Any], policy: dict[str, Any]) -> Path:
    """Resolve the prior candidate config without changing it."""
    candidates: list[Any] = [
        raw.get("candidate_config_path"),
        raw.get("base_config_path"),
    ]
    candidate_spec = raw.get("candidate_config")
    if isinstance(candidate_spec, dict):
        candidates.extend((candidate_spec.get("path"), candidate_spec.get("config_path")))
    candidates.append(policy_path.parent / "sleep_drift_candidate_20260910.json")
    for value in candidates:
        if value:
            path = Path(str(value))
            if not path.is_absolute():
                path = (policy_path.parent / path).resolve()
            return path
    raise CoordinateGateContractError("frozen policy has no base candidate config path")


def _validate_policy_shape(policy: dict[str, Any]) -> None:
    """Require the policy to freeze all predicates used by the gate.

    The policy author may group fields under ``eligibility`` or
    ``coordinate_support``; the predicate names themselves are fixed here so
    an omitted condition cannot silently become permissive.
    """
    required_top = {"sources", "coordinates", "geometry_evidence", "candidate_split", "time_and_epoch_support_checks", "selected_coordinate_checks"}
    missing = sorted(key for key in required_top if key not in policy)
    if missing:
        raise CoordinateGateContractError(f"policy omitted frozen sections: {missing}")
    evidence = policy["geometry_evidence"]
    if not isinstance(evidence, dict) or not isinstance(evidence.get("required_paths"), dict):
        raise CoordinateGateContractError("geometry evidence required_paths is missing")
    required_paths = {
        "overall_status": "provenance/geometry_contract/status",
        "policy_version": "provenance/geometry_contract/policy_version",
        "time_grid_status": "provenance/geometry_contract/time_grid/status",
        "epochs_before_policy": "provenance/geometry_contract/shared_time_grid/epochs_before_policy",
        "epochs_retained": "provenance/geometry_contract/shared_time_grid/epochs_retained",
        "epochs_dropped": "provenance/geometry_contract/shared_time_grid/epochs_dropped",
        "drop_reason_counts": "provenance/geometry_contract/shared_time_grid/drop_reason_counts",
        "mnps_3d_degenerate_axes": "provenance/geometry_contract/mnps_3d/degenerate_axes",
        "mnps_3d_all_nan_axes": "provenance/geometry_contract/mnps_3d/all_nan_axes",
        "mnps_3d_nonfinite_rows": "provenance/geometry_contract/mnps_3d/nonfinite_row_count",
        "coords_9d_available": "provenance/geometry_contract/coords_9d/available",
        "coords_9d_shape_matches_time_grid": "provenance/geometry_contract/coords_9d/shape_matches_time_grid",
        "coords_9d_degenerate_axes": "provenance/geometry_contract/coords_9d/degenerate_axes",
        "coords_9d_all_nan_axes": "provenance/geometry_contract/coords_9d/all_nan_axes",
        "coords_9d_nonfinite_rows": "provenance/geometry_contract/coords_9d/nonfinite_row_count",
        "coords_9d_nonfinite_rows_retained_on_shared_grid": "provenance/geometry_contract/coords_9d/nonfinite_rows_retained_on_shared_grid",
        "jacobian_3d_status": "provenance/geometry_contract/jacobian/status",
        "jacobian_3d_invalid_windows": "provenance/geometry_contract/jacobian/invalid_windows",
        "jacobian_3d_windows_raw": "provenance/geometry_contract/jacobian/windows_raw",
        "jacobian_3d_windows_retained": "provenance/geometry_contract/jacobian/windows_retained",
        "jacobian_3d_condition_number_windows": "provenance/geometry_contract/jacobian/invalid_reason_counts/condition_number_windows",
        "jacobian_3d_nonfinite_windows": "provenance/geometry_contract/jacobian/invalid_reason_counts/nonfinite_windows",
        "jacobian_9d_status": "provenance/geometry_contract/jacobian_9d/status",
        "jacobian_9d_invalid_windows": "provenance/geometry_contract/jacobian_9d/invalid_windows",
        "jacobian_9d_windows_raw": "provenance/geometry_contract/jacobian_9d/windows_raw",
        "jacobian_9d_windows_retained": "provenance/geometry_contract/jacobian_9d/windows_retained",
        "jacobian_9d_condition_number_windows": "provenance/geometry_contract/jacobian_9d/invalid_reason_counts/condition_number_windows",
        "jacobian_9d_nonfinite_windows": "provenance/geometry_contract/jacobian_9d/invalid_reason_counts/nonfinite_windows",
    }
    if evidence["required_paths"] != required_paths:
        raise CoordinateGateContractError("policy geometry evidence paths do not match the frozen source contract")
    if evidence.get("any_unknown_missing_inconsistent_or_unaccounted_evidence") != "refuse":
        raise CoordinateGateContractError("policy must refuse unknown, missing, inconsistent and unaccounted evidence")
    recognized = evidence.get("recognized_reason_keys")
    if not isinstance(recognized, dict) or recognized.get("shared_time_grid_drop_reason_counts") != ["coords_9d_nonfinite_rows_affecting_primary", "mnps_3d_nonfinite_rows"] or recognized.get("jacobian_invalid_reason_counts") != ["condition_number_windows", "nonfinite_windows"]:
        raise CoordinateGateContractError("policy reason-key allowlist is not frozen")
    overall = policy.get("overall_geometry_status", {})
    if overall != {"allowed": ["ok", "adjusted"], "unknown_missing_or_other": "refuse", "status_is_preserved": True}:
        raise CoordinateGateContractError("policy overall-status allowlist is not frozen")
    strict = policy.get("strict_reference_gate", {})
    if strict.get("required_status") != "ok" or strict.get("strict_refusal_must_remain_visible") is not True or strict.get("strict_gate_is_not_reclassified_by_this_policy") is not True:
        raise CoordinateGateContractError("policy strict-reference preservation rule is not frozen")
    selection = policy.get("coordinate_selection", {})
    if selection.get("must_be_explicit") is not True or selection.get("subject_specific_allowlist") is not False or selection.get("unknown_missing_or_inconsistent_selection") != "refuse":
        raise CoordinateGateContractError("policy coordinate-selection rule is not frozen")
    coordinate_checks = policy.get("selected_coordinate_checks", {})
    required_coordinate_checks = {"dataset_exists", "two_dimensional_numeric_array", "row_count_equals_time_and_epoch_support_row_count", "column_count_equals_configured_dimension", "axis_names_equal_configured_order", "all_values_finite", "no_imputation_or_zero_substitution", "explicit_path_and_layer_are_serialized"}
    if set(coordinate_checks) != required_coordinate_checks or any(value is not True for value in coordinate_checks.values()):
        raise CoordinateGateContractError("policy selected-coordinate checks are not strict")
    support_checks = policy.get("time_and_epoch_support_checks", {})
    if support_checks.get("support_embargo_must_be_checked_by_candidate_runner") is not True or support_checks.get("unknown_missing_invalid_or_gap_support") != "refuse":
        raise CoordinateGateContractError("policy time/support refusal rule is not frozen")


def _gate_spec(policy: dict[str, Any]) -> dict[str, Any]:
    evidence = policy["geometry_evidence"]
    return {
        "require_both_coordinates": True,
        "require_time_grid_ok": True,
        "require_support_recorded": True,
        "require_chart_capabilities": True,
        "adjusted_overall_status": "adjusted",
        "adjusted_jacobian_3d_status": "ok",
        "adjusted_jacobian_3d_invalid_windows": 0,
        "adjusted_jacobian_9d_status": "adjusted",
        "adjusted_jacobian_9d_invalid_windows_min": 1,
        "adjusted_jacobian_9d_condition_count_equals_invalid": True,
        "adjusted_jacobian_9d_nonfinite_windows": 0,
        "adjusted_jacobian_9d_retained_equals_invalid": True,
        "adjusted_no_dropped_epochs": True,
        "adjusted_no_degenerate_axes": True,
        "adjusted_no_all_nan_axes": True,
        "adjusted_no_nonfinite_rows": True,
        "adjusted_shapes_match_time_grid": True,
        "adjusted_no_other_geometry_adjustment": True,
        "required_paths": evidence["required_paths"],
        "drop_reason_keys": evidence["recognized_reason_keys"]["shared_time_grid_drop_reason_counts"],
        "jacobian_reason_keys": evidence["recognized_reason_keys"]["jacobian_invalid_reason_counts"],
    }


def _validate_policy_binding(policy: dict[str, Any], candidate_spec: dict[str, Any]) -> None:
    """Bind the policy to the same sources, coordinates and M3 split as E3."""
    sources = policy.get("sources")
    if not isinstance(sources, list) or len(sources) != 2:
        raise CoordinateGateContractError("policy must bind exactly the two E3 sources")
    expected_sources = {(str(row.get("recording")), str(row.get("path")), str(row.get("sha256")).lower()) for row in candidate_spec["sources"]}
    actual_sources = {(str(row.get("recording")), str(row.get("path")), str(row.get("sha256")).lower()) for row in sources if isinstance(row, dict)}
    if actual_sources != expected_sources:
        raise CoordinateGateContractError("policy source paths or hashes do not match frozen E3 sources")
    if policy.get("candidate_split") != candidate_spec.get("split"):
        raise CoordinateGateContractError("policy candidate split does not match frozen E3 split")
    configured = policy.get("coordinates")
    if not isinstance(configured, list) or len(configured) != 2:
        raise CoordinateGateContractError("policy must bind both explicit coordinate paths")
    expected = {
        "mnps_3d": {"dataset_path": "mnps_3d", "coordinate_layer": "mnps_3d", "dimension": 3, "axis_names": ["m", "d", "e"]},
        "coords_9d": {"dataset_path": "coords_9d/values", "coordinate_layer": "coords_9d/values", "dimension": 9, "axis_names": ["m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m"]},
    }
    for row in configured:
        if not isinstance(row, dict) or row.get("name") not in expected:
            raise CoordinateGateContractError("policy coordinate selection is unknown or duplicated")
        key = row["name"]
        if any(row.get(field) != value for field, value in expected[key].items()):
            raise CoordinateGateContractError(f"policy coordinate selection is not frozen for {key}")
    if [row["name"] for row in configured] != ["mnps_3d", "coords_9d"]:
        raise CoordinateGateContractError("policy coordinate order must be mnps_3d then coords_9d")


def _read_h5_scalar(handle: h5py.File, path: str) -> Any:
    if path not in handle:
        return None
    return _scalar(handle[path][()])


def _read_h5_list(handle: h5py.File, path: str) -> list[Any] | None:
    value = _read_h5_scalar(handle, path)
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if not isinstance(value, list):
        return [value]
    return [_scalar(item) for item in value]


def _read_geometry_metadata(path: Path, n_rows: int) -> dict[str, Any]:
    """Read every status needed by the frozen adjusted branch."""
    with h5py.File(path, "r") as handle:
        def jacobian(prefix: str, attr_invalid: str) -> dict[str, Any]:
            invalid = _read_h5_scalar(handle, f"provenance/geometry_contract/{prefix}/invalid_windows")
            attr = _scalar(handle.attrs.get(attr_invalid)) if attr_invalid in handle.attrs else None
            reason_base = f"provenance/geometry_contract/{prefix}/invalid_reason_counts"
            reason_keys = sorted(handle[reason_base].keys()) if reason_base in handle else None
            return {
                "status": _read_h5_scalar(handle, f"provenance/geometry_contract/{prefix}/status"),
                "invalid_windows": invalid,
                "invalid_windows_attr": attr,
                "condition_number_windows": _read_h5_scalar(handle, f"provenance/geometry_contract/{prefix}/invalid_reason_counts/condition_number_windows"),
                "nonfinite_windows": _read_h5_scalar(handle, f"provenance/geometry_contract/{prefix}/invalid_reason_counts/nonfinite_windows"),
                "invalid_reason_keys": reason_keys,
                "windows_raw": _read_h5_scalar(handle, f"provenance/geometry_contract/{prefix}/windows_raw"),
                "windows_retained": _read_h5_scalar(handle, f"provenance/geometry_contract/{prefix}/windows_retained"),
                "invalid_centers_preview": _read_h5_list(handle, f"provenance/geometry_contract/{prefix}/invalid_centers_preview"),
            }

        def chart(prefix: str) -> dict[str, Any]:
            base = f"provenance/geometry_contract/{prefix}"
            if prefix == "mnps_3d" and "mnps_3d" in handle:
                values = np.asarray(handle["mnps_3d"], dtype=float)
                return {
                    "available": True,
                    "finite_row_fraction_before": _read_h5_scalar(handle, f"{base}/finite_row_fraction_before"),
                    "nonfinite_row_count": _read_h5_scalar(handle, f"{base}/nonfinite_row_count"),
                    "shape_matches_time_grid": bool(values.ndim == 2 and values.shape[0] == n_rows and values.shape[1] == 3),
                    "degenerate_axes": _read_h5_list(handle, f"{base}/degenerate_axes"),
                    "all_nan_axes": _read_h5_list(handle, f"{base}/all_nan_axes"),
                    "nonfinite_rows_retained_on_shared_grid": _read_h5_scalar(handle, f"{base}/nonfinite_rows_retained_on_shared_grid"),
                    "evidence_source": "stored_mnps_3d_geometry_fields_plus_selected_array_shape",
                }
            return {
                "available": _read_h5_scalar(handle, f"{base}/available"),
                "finite_row_fraction_before": _read_h5_scalar(handle, f"{base}/finite_row_fraction_before"),
                "nonfinite_row_count": _read_h5_scalar(handle, f"{base}/nonfinite_row_count"),
                "nonfinite_rows_retained_on_shared_grid": _read_h5_scalar(handle, f"{base}/nonfinite_rows_retained_on_shared_grid"),
                "shape_matches_time_grid": _read_h5_scalar(handle, f"{base}/shape_matches_time_grid"),
                "degenerate_axes": _read_h5_list(handle, f"{base}/degenerate_axes"),
                "all_nan_axes": _read_h5_list(handle, f"{base}/all_nan_axes"),
            }

        shared = "provenance/geometry_contract/shared_time_grid"
        metadata: dict[str, Any] = {
            "overall_status": _read_h5_scalar(handle, "provenance/geometry_contract/status"),
            "overall_status_attr": _scalar(handle.attrs.get("geometry_contract_status")) if "geometry_contract_status" in handle.attrs else None,
            "policy_version": _read_h5_scalar(handle, "provenance/geometry_contract/policy_version"),
            "time_grid_status": _read_h5_scalar(handle, "provenance/geometry_contract/time_grid/status"),
            "three_d": chart("mnps_3d"),
            "nine_d": chart("coords_9d"),
            "jacobian_3d": jacobian("jacobian", "geometry_jacobian_invalid_windows"),
            "jacobian_9d": jacobian("jacobian_9d", "geometry_jacobian_9d_invalid_windows"),
            "shared_time_grid": {
                "epochs_before_policy": _read_h5_scalar(handle, f"{shared}/epochs_before_policy"),
                "epochs_dropped": _read_h5_scalar(handle, f"{shared}/epochs_dropped"),
                "epochs_retained": _read_h5_scalar(handle, f"{shared}/epochs_retained"),
                "drop_fraction": _read_h5_scalar(handle, f"{shared}/drop_fraction"),
                "drop_reason_counts": {},
            },
            "attrs": {
                key: _json_safe(_scalar(value))
                for key, value in handle.attrs.items()
                if key in {"dropped_geometry_invalid_epochs", "epochs_after_geometry_policy", "geometry_jacobian_invalid_windows", "geometry_jacobian_9d_invalid_windows"}
            },
        }
        reason_base = f"{shared}/drop_reason_counts"
        metadata["shared_time_grid"]["drop_reason_keys"] = sorted(handle[reason_base].keys()) if reason_base in handle else None
        for reason in ("coords_9d_nonfinite_rows_affecting_primary", "mnps_3d_nonfinite_rows"):
            value = _read_h5_scalar(handle, f"{shared}/drop_reason_counts/{reason}")
            metadata["shared_time_grid"]["drop_reason_counts"][reason] = value
        # These are intentionally recorded as observations.  The policy decides
        # whether their absence/zero values are enough for continuation.
        metadata["other_geometry_adjustments"] = {
            "dropped_geometry_invalid_epochs": metadata["attrs"].get("dropped_geometry_invalid_epochs"),
            "epochs_after_geometry_policy": metadata["attrs"].get("epochs_after_geometry_policy"),
            "n_rows": n_rows,
        }
        return metadata


def _status_consistency(geometry: dict[str, Any]) -> tuple[bool, str | None]:
    if geometry["overall_status"] is None or geometry["time_grid_status"] is None:
        return False, "unknown geometry or time-grid status"
    if geometry.get("policy_version") != "standard_invalidity_v1":
        return False, "unknown or inconsistent geometry policy version"
    if geometry["overall_status_attr"] is not None and geometry["overall_status_attr"] != geometry["overall_status"]:
        return False, "inconsistent overall geometry status metadata"
    if geometry["shared_time_grid"].get("drop_reason_keys") != ["coords_9d_nonfinite_rows_affecting_primary", "mnps_3d_nonfinite_rows"]:
        return False, "unknown, missing or extra shared-time-grid drop reason keys"
    for name in ("jacobian_3d", "jacobian_9d"):
        row = geometry[name]
        if row["status"] is None or row["invalid_windows"] is None:
            return False, f"unknown {name} status metadata"
        if row.get("invalid_reason_keys") != ["condition_number_windows", "nonfinite_windows"]:
            return False, f"unknown, missing or extra {name} reason keys"
        if row["invalid_windows_attr"] is not None:
            valid, why = _require_int(row["invalid_windows_attr"], f"{name} attribute invalid windows")
            if not valid or int(row["invalid_windows_attr"]) != int(row["invalid_windows"]):
                return False, f"inconsistent {name} invalid-window metadata: {why or 'value mismatch'}"
    return True, None


def _is_int(value: Any, *, positive: bool = False) -> bool:
    """Accept only finite, non-bool integer metadata without truncation."""
    if isinstance(value, (bool, np.bool_)) or value is None:
        return False
    if isinstance(value, (int, np.integer)):
        result = True
    elif isinstance(value, (float, np.floating)):
        result = bool(np.isfinite(value) and float(value).is_integer())
    else:
        return False
    if not result:
        return False
    return int(value) > 0 if positive else int(value) >= 0


def _require_int(value: Any, label: str, *, positive: bool = False) -> tuple[bool, str | None]:
    if not _is_int(value, positive=positive):
        return False, f"{label} is missing, nonfinite, noninteger or out of range"
    return True, None


def _support_eligibility(source_metadata: dict[str, Any], gate: dict[str, Any]) -> tuple[bool, str | None]:
    signal = source_metadata.get("signal_support_provenance", {})
    signature = source_metadata.get("support_signature", {})
    if gate["require_support_recorded"] is True:
        if signal.get("status") != "recorded":
            return False, "signal-support provenance is not recorded"
        if signature.get("status") != "recorded":
            return False, "support signature is not recorded"
    capabilities = signature.get("capability", {})
    if gate["require_chart_capabilities"] is True:
        if capabilities.get("chart_3d") != "yes" or capabilities.get("chart_9d") != "yes":
            return False, "both selected chart capabilities are not available"
    # Unknown effective filter support remains a declared limitation, while
    # missing support provenance is a refusal.  No temporal support is inferred.
    if signal.get("temporal_support_status") != "unknown":
        return False, "effective temporal support status is not the frozen unknown status"
    if signal.get("per_epoch_support_status") != "unknown":
        return False, "per-epoch support status is outside the frozen policy"
    return True, None


def _coordinate_eligibility(source_metadata: dict[str, Any], geometry: dict[str, Any], gate: dict[str, Any], n_rows: int) -> tuple[bool, str | None]:
    consistent, reason = _status_consistency(geometry)
    if not consistent:
        return False, reason
    if gate["require_time_grid_ok"] and geometry["time_grid_status"] != "ok":
        return False, f"time-grid status is {geometry['time_grid_status']!r}"
    if gate["require_both_coordinates"] is not True:
        return False, "policy does not require both coordinates"
    # The producer records these fields for the canonical 9D geometry group.
    # The explicit 3D dataset is validated from the selected array by the
    # legacy reader and is summarized below by this gate.
    for name in ("three_d", "nine_d"):
        row = geometry[name]
        if name == "nine_d" and (row["available"] is not True or row["shape_matches_time_grid"] is not True):
            return False, f"{name} chart availability or shape status is not valid"
        if row["nonfinite_row_count"] is None or row["finite_row_fraction_before"] is None:
            return False, f"{name} finite-row evidence is unknown"
        valid, why = _require_int(row["nonfinite_row_count"], f"{name} nonfinite rows")
        if not valid or int(row["nonfinite_row_count"]) != 0:
            return False, why or f"{name} chart has nonfinite rows"
        fraction = row["finite_row_fraction_before"]
        if isinstance(fraction, (bool, np.bool_)) or not isinstance(fraction, (int, float, np.integer, np.floating)) or not np.isfinite(fraction) or float(fraction) != 1.0:
            return False, f"{name} finite-row evidence is invalid"
        if name == "nine_d":
            retained_nonfinite = row.get("nonfinite_rows_retained_on_shared_grid")
            valid, why = _require_int(retained_nonfinite, f"{name} retained nonfinite rows")
            if not valid or int(retained_nonfinite) != 0:
                return False, why or f"{name} chart retained nonfinite rows on the shared grid"
        if row["degenerate_axes"] != [] or row["all_nan_axes"] != []:
            return False, f"{name} chart reports degenerate or all-NaN axes"
    j3 = geometry["jacobian_3d"]
    j9 = geometry["jacobian_9d"]
    shared = geometry["shared_time_grid"]
    for label, value, positive in (
        ("epochs_before_policy", shared["epochs_before_policy"], True),
        ("epochs_retained", shared["epochs_retained"], True),
        ("epochs_dropped", shared["epochs_dropped"], False),
        ("3D invalid windows", j3["invalid_windows"], False),
        ("3D windows raw", j3["windows_raw"], True),
        ("3D windows retained", j3["windows_retained"], True),
        ("3D condition-number windows", j3["condition_number_windows"], False),
        ("3D nonfinite windows", j3["nonfinite_windows"], False),
        ("9D invalid windows", j9["invalid_windows"], False),
        ("9D windows raw", j9["windows_raw"], True),
        ("9D windows retained", j9["windows_retained"], True),
        ("9D condition-number windows", j9["condition_number_windows"], False),
        ("9D nonfinite windows", j9["nonfinite_windows"], False),
    ):
        valid, why = _require_int(value, label, positive=positive)
        if not valid:
            return False, why
    if int(shared["epochs_before_policy"]) != n_rows or int(shared["epochs_retained"]) != n_rows or int(shared["epochs_dropped"]) != 0:
        return False, "shared time grid was dropped or retained inconsistently"
    for key, value in shared.get("drop_reason_counts", {}).items():
        valid, why = _require_int(value, f"shared drop-reason count {key}")
        if not valid or int(value) != 0:
            return False, why or "shared time grid has nonzero drop-reason counts"
    # Common clean predicates apply to both overall statuses.
    if j3["status"] != "ok" or int(j3["invalid_windows"]) != 0:
        return False, "3D Jacobian is not clean"
    if int(j3["windows_raw"]) != int(j3["windows_retained"]) or int(j3["condition_number_windows"]) != 0 or int(j3["nonfinite_windows"]) != 0:
        return False, "3D Jacobian retained or reason metadata is inconsistent"
    dropped = geometry["attrs"].get("dropped_geometry_invalid_epochs")
    valid, why = _require_int(dropped, "dropped geometry epochs")
    if not valid or int(dropped) != 0:
        return False, "geometry metadata reports dropped epochs"
    retained_epochs = geometry["attrs"].get("epochs_after_geometry_policy")
    valid, why = _require_int(retained_epochs, "epochs after geometry policy", positive=True)
    if not valid or int(retained_epochs) != n_rows:
        return False, "geometry retained-row metadata is inconsistent"
    if geometry["overall_status"] == "ok":
        if j9["status"] != "ok" or int(j9["invalid_windows"]) != 0:
            return False, "strict overall status has an invalid 9D Jacobian status"
        if int(j9["windows_raw"]) != int(j9["windows_retained"]) or int(j9["condition_number_windows"]) != 0 or int(j9["nonfinite_windows"]) != 0:
            return False, "strict 9D Jacobian retained or reason metadata is inconsistent"
    elif geometry["overall_status"] == gate["adjusted_overall_status"]:
        if j9["status"] != gate["adjusted_jacobian_9d_status"]:
            return False, "adjusted continuation requires the permitted adjusted 9D Jacobian"
        if int(j9["invalid_windows"]) < int(gate["adjusted_jacobian_9d_invalid_windows_min"]):
            return False, "adjusted 9D invalid-window count is not positive"
        if gate["adjusted_jacobian_9d_condition_count_equals_invalid"] and int(j9["condition_number_windows"]) != int(j9["invalid_windows"]):
            return False, "9D invalid windows include an unapproved reason"
        if gate["adjusted_jacobian_9d_nonfinite_windows"] == 0 and int(j9["nonfinite_windows"]) != 0:
            return False, "9D nonfinite-window count is nonzero"
        if gate["adjusted_jacobian_9d_retained_equals_invalid"] and int(j9["windows_retained"]) != int(j9["windows_raw"]) - int(j9["invalid_windows"]):
            return False, "9D retained-window count is inconsistent with conditioning adjustment"
        if gate["adjusted_no_other_geometry_adjustment"] and int(j9["windows_raw"]) - int(j9["windows_retained"]) != int(j9["invalid_windows"]):
            return False, "adjusted 9D geometry has an unaccounted adjustment"
    else:
        return False, f"overall geometry status {geometry['overall_status']!r} is not eligible"
    return _support_eligibility(source_metadata, gate)


def _strict_summary(strict: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": strict.get("status"),
        "refusal_class": strict.get("refusal_class"),
        "refusal_reason": strict.get("refusal_reason"),
        "n_predictions": strict.get("n_predictions"),
        "predictions_finite": strict.get("predictions_finite"),
    }


def _run_scoped_one(source_metadata: dict[str, Any], arrays: dict[str, np.ndarray], coordinate: str, estimator: str, spec: dict[str, Any], source_hash: str, code_hashes: dict[str, str], strict: dict[str, Any], geometry: dict[str, Any], gate: dict[str, Any]) -> dict[str, Any]:
    row = deepcopy(strict)
    row["strict_reference_outcome"] = _strict_summary(strict)
    row["strict_status"] = strict.get("status")
    row["strict_refusal_class"] = strict.get("refusal_class")
    row["strict_refusal_reason"] = strict.get("refusal_reason")
    eligible, reason = _coordinate_eligibility(source_metadata, geometry, gate, int(source_metadata["n_epochs"]))
    row["coordinate_gate_status"] = "eligible" if eligible else "refused"
    row["scoped_eligibility_status"] = "eligible" if eligible else "refused"
    row["scoped_refusal_reason"] = reason
    row["source_geometry_status_observed"] = geometry["overall_status"]
    row["coordinate_gate_metadata"] = geometry
    if not eligible:
        row.update(status="refused", refusal_class="coordinate_gate", refusal_reason=reason, predictions=None, heldout_rows=None, n_predictions=0, predictions_finite=None)
        row["scoped_status"] = "refused"
        row["scoped_refusal_class"] = "coordinate_gate"
        return row
    if strict.get("status") == "computed_candidate":
        # Preserve the original strict numerical path byte-for-byte.
        row["scoped_status"] = strict.get("status")
        row["scoped_refusal_class"] = None
        return row
    split = spec["split"]
    train = np.arange(*split["train_increment_range"], dtype=np.int64)
    evaluation = np.arange(*split["evaluation_increment_range"], dtype=np.int64)
    support_audit = candidate._support_audit(arrays["train_support"], arrays["evaluation_support"], float(split["embargo_sec"]))
    try:
        result = drift.crossfit_local_chart_b(
            arrays[coordinate], arrays["time"], train, evaluation,
            estimator=estimator,
            n_neighbors=int(split["n_neighbors"]),
            min_train_support=int(split["min_train_support"]),
            embargo=float(split["embargo_sec"]),
            train_window_support=arrays["train_support"],
            evaluation_window_support=arrays["evaluation_support"],
            source_artifact_hash=source_hash,
            source_nmd_schema=source_metadata["source_schema"],
            nmd_code_revision=None,
        )
    except drift.DriftContractError as exc:
        row.update(status="refused", refusal_class="estimator_contract", refusal_reason=str(exc), predictions=None, heldout_rows=None, n_predictions=0, predictions_finite=None)
        row["scoped_status"] = "refused"
        row["scoped_refusal_class"] = "estimator_contract"
        return row
    scoped = deepcopy(strict)
    scoped.update(
        status="computed_candidate",
        refusal_reason=None,
        increment_overlap=result.provenance["train_evaluation_overlap"],
        estimator_provenance=dict(result.provenance),
        predictions=result.b_hat.tolist(),
        heldout_rows=candidate._evaluation_rows(result, {**arrays, "trajectory": arrays[coordinate]}),
        n_predictions=int(len(result.b_hat)),
        predictions_finite=bool(np.isfinite(result.b_hat).all()),
        support_audit=support_audit,
    )
    row.update(scoped)
    row["strict_reference_outcome"] = _strict_summary(strict)
    row["strict_status"] = strict.get("status")
    row["strict_refusal_class"] = strict.get("refusal_class")
    row["strict_refusal_reason"] = strict.get("refusal_reason")
    row["coordinate_gate_status"] = "eligible"
    row["scoped_eligibility_status"] = "eligible"
    row["scoped_refusal_reason"] = None
    row["refusal_class"] = None
    row["scoped_status"] = row.get("status")
    row["scoped_refusal_class"] = None
    row["source_geometry_status_observed"] = geometry["overall_status"]
    row["coordinate_gate_metadata"] = geometry
    return row


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(_json_safe(value), indent=2, allow_nan=False), encoding="utf-8")


def run(policy_path: str | Path, output_root: str | Path) -> dict[str, Any]:
    policy_path = Path(policy_path).resolve()
    output_root = Path(output_root).resolve()
    raw_policy, policy, policy_hash, policy_spec_hash = _read_policy(policy_path)
    _validate_policy_shape(policy)
    gate = _gate_spec(policy)
    candidate_config_path = _candidate_config_path(policy_path, raw_policy, policy)
    config, spec_hash, config_hash = candidate._read_config(candidate_config_path)
    if config.get("schema") != EXPECTED_SPEC_SCHEMA:
        raise CoordinateGateContractError("base candidate config schema is not frozen E3")
    spec = deepcopy(config["spec"])
    candidate._check_frozen_spec(spec)
    _validate_policy_binding(policy, spec)
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"coordinate gate output must be fresh and empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    gate_hash = sha256_file(Path(__file__).resolve())
    legacy_hash = sha256_file(Path(candidate.__file__).resolve())
    drift_hash = sha256_file(Path(drift.__file__).resolve())
    code_hashes = {
        "runner_sha256": gate_hash,
        "legacy_candidate_runner_sha256": legacy_hash,
        "drift_sha256": drift_hash,
        "candidate_config_sha256": config_hash,
        "policy_sha256": policy_hash,
    }
    report: dict[str, Any] = {
        "schema": "ndt.sleep.sleep_drift_coordinate_gate_result.v1",
        "status": "candidate_not_qualified",
        "claim_status": "no_biological_claim",
        "scientific_qualification": "not_assessed",
        "stage_contrast": "not_run",
        "question": "Does a frozen coordinate-support policy permit continuation of the E3 candidate when the overall H5 geometry status is adjusted?",
        "scope": "bounded two-recording engineering gate; strict E3 status retained beside scoped coordinate eligibility; no tuning, qualification, stage contrast or Ito drift claim",
        "frozen_spec_sha256": spec_hash,
        "frozen_policy_spec_sha256": policy_spec_hash,
        "policy_file_sha256_before": policy_hash,
        "policy_path": str(policy_path),
        "candidate_config_path": str(candidate_config_path),
        "candidate_config_sha256_before": config_hash,
        "code_provenance": code_hashes,
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "h5py": h5py.__version__,
            "nmd_analysis": importlib.metadata.version("nmd-analysis") if importlib.metadata.packages_distributions().get("nmd_analysis") else "source_checkout",
        },
        "policy": policy,
        "spec": spec,
        "sources": [],
        "rows": [],
        "limitations": {
            "strict_reference_outcome": "original E3 overall geometry-status gate is retained for every row",
            "full_upstream_signal_support": "source export records temporal_support_status=unknown and effective feature/filter support is not certified by epoch bounds",
            "global_coordinate_fit_population": "source export records whole-record robust-z fit populations; these include evaluation rows and are not held-out",
            "coordinate_comparison_to_e1_e2": "mnps_3d and coords_9d/values are explicit candidate paths; E1/E2 subject_anchored family layers are not asserted identical",
            "candidate_interpretation": "computed diagnostics only; no empirical drift, Ito drift, C1 qualification, biological interpretation, or sleep-stage contrast",
            "missingness": "nonfinite coordinates/support and unknown/inconsistent eligibility status are refused; no imputation or zero substitution",
            "exploratory_history": "existing sub-1 exploratory predictions were already inspected and are not preregistered or unseen primary outcomes",
        },
    }
    for source in spec["sources"]:
        source_metadata, arrays, before, after = candidate._read_source(source, spec)
        geometry = _read_geometry_metadata(Path(source["path"]).resolve(), int(source_metadata["n_epochs"]))
        for coordinate in ("mnps_3d", "coords_9d"):
            values = np.ascontiguousarray(arrays[coordinate].astype(np.float64))
            source_metadata["coordinate_provenance"][coordinate].update({
                "selected_coordinate_shape": list(values.shape),
                "selected_coordinate_dtype": str(values.dtype),
                "selected_coordinate_array_sha256": sha256_bytes(values.tobytes()),
                "selected_coordinate_finite": bool(np.isfinite(values).all()),
            })
        source_metadata["coordinate_gate_geometry"] = geometry
        report["sources"].append(source_metadata)
        strict_rows = {
            (coordinate, estimator): candidate._run_one(source_metadata, arrays, coordinate, estimator, spec, before, code_hashes)
            for coordinate in ("mnps_3d", "coords_9d")
            for estimator in spec["split"]["estimators"]
        }
        for coordinate in ("mnps_3d", "coords_9d"):
            for estimator in spec["split"]["estimators"]:
                report["rows"].append(_run_scoped_one(source_metadata, arrays, coordinate, estimator, spec, before, code_hashes, strict_rows[(coordinate, estimator)], geometry, gate))
    config_after = sha256_file(candidate_config_path)
    if config_after != config_hash:
        raise CoordinateGateContractError("base candidate config changed during coordinate gate")
    policy_after = sha256_file(policy_path)
    if policy_after != policy_hash:
        raise CoordinateGateContractError("policy changed during coordinate gate")
    report["candidate_config_sha256_after"] = config_after
    report["policy_file_sha256_after"] = policy_after
    _write_json(output_root / "candidate_report.json", report)
    _write_json(output_root / "candidate_predictions.json", {
        "schema": "ndt.sleep.sleep_drift_coordinate_gate_predictions.v1",
        "frozen_spec_sha256": spec_hash,
        "frozen_policy_spec_sha256": policy_spec_hash,
        "rows": [
            {
                "recording": row["recording"],
                "coordinate": row["coordinate"],
                "estimator": row["estimator"],
                "strict_status": row.get("strict_status"),
                "scoped_status": row.get("scoped_status"),
                "status": row["status"],
                "predictions": row.get("predictions"),
                "heldout_rows": row.get("heldout_rows"),
            }
            for row in report["rows"]
        ],
    })
    output_hashes = {path.name: sha256_file(path) for path in sorted(output_root.iterdir()) if path.is_file()}
    _write_json(output_root / "output_hashes.json", output_hashes)
    return report


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.policy, args.output_root)
    print(json.dumps({"output_root": str(args.output_root.resolve()), "status": report["status"], "rows": len(report["rows"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
