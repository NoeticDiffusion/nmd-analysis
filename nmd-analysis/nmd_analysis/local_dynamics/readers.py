"""Versioned HDF5 readers for local-dynamics measurement contracts."""

from __future__ import annotations

from typing import Any, Iterator, Mapping
import json

import h5py
import numpy as np


def as_scalar(value: Any) -> Any:
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        return bytes(value).decode("utf-8")
    return value


def scalar(handle: h5py.File | h5py.Group, path: str, default: Any = None) -> Any:
    if path not in handle:
        return default
    value = handle[path][()]
    return as_scalar(value)


def branch_name(dimension: int) -> str:
    if dimension == 3:
        return "primary"
    if dimension == 9:
        return "stratified_9d"
    raise ValueError(f"Unsupported local-dynamics dimension: {dimension}")


def jacobian_metrics_path(dimension: int) -> str:
    return "/jacobian/derived_metrics/v1" if dimension == 3 else "/jacobian_9D/derived_metrics/v1"


def jacobian_centers_path(dimension: int) -> str:
    return "/jacobian/centers" if dimension == 3 else "/jacobian_9D/centers"


def jacobian_diagnostics_path(dimension: int) -> str:
    return "/jacobian/diagnostics" if dimension == 3 else "/jacobian_9D/diagnostics"


def local_dynamics_paths(dimension: int) -> Mapping[str, str]:
    branch = branch_name(dimension)
    return {
        "jacobian_metrics": jacobian_metrics_path(dimension),
        "finite_time_response": f"/finite_time_response/v1/{branch}",
        "transition_residuals": f"/transition_residuals/v1/{branch}",
        "transition_q_proxy": f"/transition_residual_covariance_proxy/v1/{branch}",
        "stochastic_reachability": f"/stochastic_reachability/v1/{branch}",
    }


def availability(handle: h5py.File, dimension: int) -> dict[str, bool]:
    return {name: path in handle for name, path in local_dynamics_paths(dimension).items()}


def read_group_scalars(group: h5py.Group, *, prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in group.items():
        if isinstance(value, h5py.Dataset) and value.shape == ():
            result[f"{prefix}{name}"] = as_scalar(value[()])
    return result


def group_provenance(group: h5py.Group) -> dict[str, Any]:
    provenance = group.get("provenance")
    return read_group_scalars(provenance, prefix="") if isinstance(provenance, h5py.Group) else {}


def _group_scalar(group: Any, name: str) -> Any:
    if group is None or name not in group:
        return None
    try:
        return as_scalar(group[name][()])
    except (TypeError, ValueError, KeyError, OSError):
        return None


def measurement_certificate(group: Any) -> dict[str, str]:
    """Read v3 certificate fields without promoting scientific qualification."""
    computation = _group_scalar(group, "computation_status")
    validity = _group_scalar(group, "measurement_validity")
    claim = _group_scalar(group, "claim_status")
    provenance_claim = _group_scalar(group.get("provenance") if group is not None else None, "claim_status")
    origin = "canonical"
    if computation is None or validity is None or claim is None:
        origin = "legacy_absent"
        if claim is None and provenance_claim is not None:
            claim = provenance_claim
            origin = "legacy_promoted_provenance"
        computation = computation if computation is not None else "not_recorded"
        validity = validity if validity is not None else "not_recorded"
        claim = claim if claim is not None else "not_recorded"
    return {
        "computation_status": str(computation),
        "measurement_validity": str(validity),
        "claim_status": str(claim),
        "certificate_origin": origin,
    }


def semantic_field(group: Any, name: str) -> str:
    """Read a Gate F semantic tag from the group, then its provenance."""
    value = _group_scalar(group, name)
    if value in (None, ""):
        provenance = group.get("provenance") if group is not None else None
        value = _group_scalar(provenance, name)
    return str(value) if value not in (None, "") else "not_recorded"


def schema_status(group: Any, expected: str) -> dict[str, str]:
    """Return certificate plus an explicit invalid status for a known schema mismatch."""
    out = measurement_certificate(group)
    actual = _group_scalar(group, "schema_version")
    if actual is not None and str(actual) != expected:
        out["computation_status"] = "invalid"
        out["failure_reason"] = "invalid_schema_version"
    return out


def inferential_grain(group: Any) -> dict[str, str]:
    """Read nested v3 grain metadata; never infer it from paths or series."""
    grain = group.get("grain") if group is not None else None
    keys = ("native", "parent", "biological_unit", "repeated_measure", "direct_between_subject_inference")
    values = {f"grain_{key}": str(_group_scalar(grain, key) or "not_recorded") for key in keys}
    values["grain_origin"] = "canonical" if grain is not None and all(
        _group_scalar(grain, key) is not None for key in keys
    ) else "legacy_absent"
    return values


def support_signature(handle: h5py.File) -> dict[str, Any]:
    """Read file-level support metadata without inferring capability from paths."""
    root = handle.get("support_signature")
    group = root.get("v1") if isinstance(root, h5py.Group) else None
    if group is None and isinstance(root, h5py.Group) and any(k in root for k in ("modality", "capability", "coordinates")):
        group = root
    out: dict[str, Any] = {
        "support_signature_schema_version": str(_group_scalar(group, "schema_version") or "not_recorded"),
        "support_signature_modality": str(_group_scalar(group, "modality") or "not_recorded"),
        "support_signature_origin": "canonical" if group is not None else "legacy_absent",
    }
    capability = group.get("capability") if group is not None else None
    capability_values: dict[str, str] = {}
    for key in ("chart_3d", "chart_9d", "mnj_3d", "mnj_9d", "diffusion", "spread", "destination", "resilience"):
        value = str(_group_scalar(capability, key) or "not_recorded")
        capability_values[key] = value
        out[f"support_{key}"] = str(_group_scalar(capability, key) or "not_recorded")
    coordinates: dict[str, dict[str, str]] = {}
    coordinates_group = group.get("coordinates") if group is not None else None
    for name in ("m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m"):
        child = coordinates_group.get(name) if isinstance(coordinates_group, h5py.Group) else None
        coordinates[name] = {
            key: str(_group_scalar(child, key) or "not_recorded")
            for key in ("source", "fallback_feature", "semantic_equivalence")
        }
    axes: dict[str, dict[str, str]] = {}
    axes_group = group.get("axes_3d") if group is not None else None
    for name in ("m", "d", "e"):
        child = axes_group.get(name) if isinstance(axes_group, h5py.Group) else None
        axes[name] = {"source": str(_group_scalar(child, "source") or "not_recorded")}
    out["support_signature_json"] = json.dumps({
        "schema_version": out["support_signature_schema_version"],
        "modality": out["support_signature_modality"],
        "coordinates": coordinates,
        "axes_3d": axes,
        "capability": capability_values,
    }, sort_keys=True, separators=(",", ":"))
    return out


def iter_horizon_groups(group: h5py.Group) -> Iterator[tuple[str, h5py.Group]]:
    horizons = group.get("horizons")
    if not isinstance(horizons, h5py.Group):
        return
    for name in sorted(horizons.keys(), key=lambda item: int(item[1:]) if item[1:].isdigit() else item):
        horizon = horizons[name]
        if isinstance(horizon, h5py.Group):
            yield name, horizon


def metric_valid_fraction(summary: Mapping[str, Any]) -> float:
    total = float(summary.get("n_windows_total") or 0)
    valid = float(summary.get("n_windows_metrics_valid") or 0)
    return valid / total if total > 0 else float("nan")
