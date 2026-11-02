"""Read-only canonical/legacy family readers; metadata never licenses biology."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import h5py
import numpy as np

from ..legacy_adapters import _base_h5_metadata_from_handle
from .schemas import (
    FAMILY_IDS,
    FAMILY_SCHEMA,
    LEGACY_NAME,
    PARENT_SUBGROUPS,
    h5_family_name,
    validate_schema,
)
from .validity import status


def _value(obj: Any) -> Any:
    if isinstance(obj, h5py.Group):
        return {str(key): _value(obj[key]) for key in obj}
    value = obj[()]
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return _scalar(value.item())
        if value.dtype.kind in "SUO":
            return [_scalar(item) for item in value.reshape(-1)]
        return value
    return _scalar(value)


def _scalar(value: Any) -> Any:
    if isinstance(value, (bytes, np.bytes_)):
        return value.decode("utf-8")
    return value.item() if isinstance(value, np.generic) else value


def _parent_payload(group: h5py.Group) -> dict[str, Any]:
    """Read a family or identity group without flattening nested identities."""
    payload: dict[str, Any] = {}
    for key, obj in group.items():
        if isinstance(obj, h5py.Group):
            if key in PARENT_SUBGROUPS:
                payload[key] = _value(obj)
            continue
        payload[key] = _value(obj)
    return payload


def _group(handle: h5py.File, family: str) -> tuple[Any, Any, Any]:
    h5_name = h5_family_name(family)
    candidates = [(f"/dynamical_families/{h5_name}/v1", "canonical")]
    legacy = LEGACY_NAME.get(family)
    if legacy:
        candidates.append((f"/orthogonal_dynamics/{legacy}/v1", "legacy_orthogonal_dynamics"))
    for path, origin in candidates:
        if path in handle:
            if not isinstance(handle[path], h5py.Group):
                raise ValueError(f"family path {path} must be an HDF5 group")
            return handle[path], path, origin
    return None, None, None


def _missing_payload(base: dict[str, Any], family: str, *, failure_reason: str, signature: Any) -> dict[str, Any]:
    return {
        **base,
        "family_id": family,
        "schema_version": "not_recorded",
        "computation_status": "not_recorded",
        "measurement_validity": "not_recorded",
        "claim_status": "not_recorded",
        "failure_reason": failure_reason,
        "namespace_origin": "not_recorded",
        "source_dataset_path": None,
        "series": {},
        "summary": {},
        "provenance": {},
        "availability": False,
        "support_signature": signature,
    }


def family_availability(handle_or_path: Any) -> list[dict[str, Any]]:
    if isinstance(handle_or_path, (str, Path)):
        with h5py.File(handle_or_path, "r") as handle:
            return family_availability(handle)
    result = []
    for family in FAMILY_IDS:
        group, _, origin = _group(handle_or_path, family)
        result.append({"family_id": family, "available": group is not None,
                       "namespace_origin": origin or "not_recorded"})
    return result


def _finalize_family_payload(
    handle: h5py.File,
    family: str,
    group: Any,
    source_path: str | None,
    origin: str | None,
    *,
    validate_parent_schema: bool,
) -> dict[str, Any]:
    base = _base_h5_metadata_from_handle(handle, Path(handle.filename))
    signature = _value(handle["/support_signature/v1"]) if "/support_signature/v1" in handle else {}
    if group is None:
        return _missing_payload(base, family, failure_reason="family_group_missing", signature=signature)
    payload = _parent_payload(group)
    schema = payload.get("schema_version", group.attrs.get("_schema_version", group.attrs.get("schema_version")))
    schema = _scalar(schema) if schema is not None else None
    if validate_parent_schema:
        schema = validate_schema(family, schema)
    for key, value in base.items():
        payload.setdefault(key, value)
    payload.update(
        family_id=family,
        source_dataset_path=source_path,
        namespace_origin=origin,
        availability=True,
        schema_version=schema if schema is not None else "not_recorded",
        support_signature=signature,
    )
    payload["computation_status"] = status(payload.get("computation_status"))
    payload.setdefault("measurement_validity", "not_recorded")
    payload.setdefault("claim_status", "not_recorded")
    payload.setdefault("series", {})
    payload.setdefault("summary", {})
    payload.setdefault("provenance", {})
    payload.setdefault("grain", {})
    return payload


def read_family(handle_or_path: Any, family: str) -> dict[str, Any]:
    if family not in FAMILY_SCHEMA:
        raise KeyError(f"unknown dynamical family: {family}")
    if isinstance(handle_or_path, (str, Path)):
        with h5py.File(handle_or_path, "r") as handle:
            return read_family(handle, family)
    handle = handle_or_path
    group, source_path, origin = _group(handle, family)
    return _finalize_family_payload(
        handle, family, group, source_path, origin, validate_parent_schema=group is not None,
    )


def _declared_lag(identity_path: str) -> int:
    first = identity_path.strip("/").split("/", 1)[0]
    if first.startswith("declared_lag_"):
        token = first.removeprefix("declared_lag_")
        if token.isdigit():
            return int(token)
    return 1


def read_identity(handle_or_path: Any, family: str, identity_path: str) -> dict[str, Any]:
    """Read a nested identity group without flattening sibling identities."""
    if family not in FAMILY_SCHEMA:
        raise KeyError(f"unknown dynamical family: {family}")
    if isinstance(handle_or_path, (str, Path)):
        with h5py.File(handle_or_path, "r") as handle:
            return read_identity(handle, family, identity_path)
    handle = handle_or_path
    group, source_path, origin = _group(handle, family)
    base = _base_h5_metadata_from_handle(handle, Path(handle.filename))
    signature = _value(handle["/support_signature/v1"]) if "/support_signature/v1" in handle else {}
    relative = identity_path.strip("/")
    if group is None:
        payload = _missing_payload(base, family, failure_reason="family_group_missing", signature=signature)
        payload["identity_id"] = relative
        payload["declared_lag"] = _declared_lag(relative)
        return payload
    node: Any = group
    for part in relative.split("/"):
        if part not in node or not isinstance(node[part], h5py.Group):
            payload = _missing_payload(base, family, failure_reason="identity_group_missing", signature=signature)
            payload["identity_id"] = relative
            payload["declared_lag"] = _declared_lag(relative)
            payload["namespace_origin"] = origin
            payload["source_dataset_path"] = f"{source_path}/{relative}"
            return payload
        node = node[part]
    payload = _parent_payload(node)
    schema = payload.get("schema_version", node.attrs.get("_schema_version", node.attrs.get("schema_version")))
    for key, value in base.items():
        payload.setdefault(key, value)
    payload.update(
        family_id=family,
        identity_id=relative.split("/")[-1],
        identity_path=relative,
        declared_lag=_declared_lag(relative),
        source_dataset_path=f"{source_path}/{relative}",
        namespace_origin=origin,
        availability=True,
        schema_version=_scalar(schema) if schema is not None else "not_recorded",
        support_signature=signature,
    )
    payload["computation_status"] = status(payload.get("computation_status"))
    payload.setdefault("measurement_validity", "not_recorded")
    payload.setdefault("claim_status", "not_recorded")
    payload.setdefault("qualification_status", "not_recorded")
    payload.setdefault("series", {})
    payload.setdefault("summary", {})
    payload.setdefault("provenance", {})
    payload.setdefault("grain", {})
    return payload


def read_all_families(handle_or_path: Any) -> dict[str, dict[str, Any]]:
    return {family: read_family(handle_or_path, family) for family in FAMILY_IDS}


read_dynamical_family = read_family
read_dynamical_families = read_all_families
