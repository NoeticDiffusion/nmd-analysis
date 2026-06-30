from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import h5py
import numpy as np


DEFAULT_COORDINATE_CONTRACT = "cohort_anchored"
KNOWN_COORDINATE_CONTRACTS = ("cohort_anchored", "subject_anchored", "legacy")
_CONTRACT_ALIASES = {
    "cohort": "cohort_anchored",
    "cohort_anchor": "cohort_anchored",
    "cohort_anchored": "cohort_anchored",
    "cohortanchored": "cohort_anchored",
    "subject": "subject_anchored",
    "subject_anchor": "subject_anchored",
    "subject_anchored": "subject_anchored",
    "subjectanchored": "subject_anchored",
    "legacy": "legacy",
    "mndm_2_0": "legacy",
    "mndm2_0": "legacy",
    "mndm20": "legacy",
}


def _to_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return _to_str(value.item())
        return str(value.tolist())
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        try:
            return bytes(value).decode("utf-8")
        except Exception:
            return str(value)
    return str(value)


def _normalize_contract_or_none(value: Any) -> Optional[str]:
    text = _to_str(value)
    if text is None:
        return None
    cleaned = text.strip().lower().replace("-", "_").replace(" ", "_")
    if not cleaned:
        return None
    return _CONTRACT_ALIASES.get(cleaned, cleaned)


def normalize_coordinate_contract(value: Any, *, default: str = DEFAULT_COORDINATE_CONTRACT) -> str:
    resolved_default = _normalize_contract_or_none(default) or DEFAULT_COORDINATE_CONTRACT
    raw = _normalize_contract_or_none(value)
    if raw is None:
        return resolved_default
    if raw not in KNOWN_COORDINATE_CONTRACTS:
        valid = ", ".join(KNOWN_COORDINATE_CONTRACTS)
        raise ValueError(f"Unsupported coordinate_contract={value!r}. Expected one of: {valid}.")
    return raw


def _normalize_h5_path(path: Any) -> Optional[str]:
    text = _to_str(path)
    if text is None:
        return None
    cleaned = text.strip()
    if not cleaned:
        return None
    if not cleaned.startswith("/"):
        cleaned = f"/{cleaned}"
    return cleaned.rstrip("/")


@dataclass(frozen=True)
class RunContract:
    schema_version: Optional[str]
    mndm_version: Optional[str]
    primary_coordinate_layer: Optional[str]
    primary_coordinate_contract: Optional[str]
    anchor_id: Optional[str]
    anchor_hash: Optional[str]
    anchor_source: Optional[str]
    is_mndm_2_1: bool

    def provenance(self) -> Dict[str, Any]:
        return {
            "primary_coordinate_contract": self.primary_coordinate_contract,
            "primary_coordinate_layer": self.primary_coordinate_layer,
            "anchor_id": self.anchor_id,
            "anchor_hash": self.anchor_hash,
            "anchor_source": self.anchor_source,
            "schema_version": self.schema_version,
            "mndm_version": self.mndm_version,
        }


@dataclass(frozen=True)
class ResolvedCoordinateData:
    values: np.ndarray
    names: list[str]
    values_path: str
    names_path: Optional[str]
    requested_coordinate_contract: str
    resolved_coordinate_contract: str
    primary_coordinate_contract: Optional[str]
    primary_coordinate_layer: Optional[str]
    anchor_id: Optional[str]
    anchor_hash: Optional[str]
    anchor_source: Optional[str]
    schema_version: Optional[str]
    mndm_version: Optional[str]

    def provenance(self) -> Dict[str, Any]:
        return {
            "requested_coordinate_contract": self.requested_coordinate_contract,
            "resolved_coordinate_contract": self.resolved_coordinate_contract,
            "primary_coordinate_contract": self.primary_coordinate_contract,
            "primary_coordinate_layer": self.primary_coordinate_layer,
            "anchor_id": self.anchor_id,
            "anchor_hash": self.anchor_hash,
            "anchor_source": self.anchor_source,
            "schema_version": self.schema_version,
            "mndm_version": self.mndm_version,
        }


@dataclass(frozen=True)
class ResolvedJacobianData:
    j_hat: np.ndarray
    j_dot: Optional[np.ndarray]
    centers: Optional[np.ndarray]
    dataset_path: str
    j_dot_path: Optional[str]
    centers_path: Optional[str]
    requested_coordinate_contract: str
    resolved_coordinate_contract: str
    primary_coordinate_contract: Optional[str]
    primary_coordinate_layer: Optional[str]
    anchor_id: Optional[str]
    anchor_hash: Optional[str]
    anchor_source: Optional[str]
    schema_version: Optional[str]
    mndm_version: Optional[str]

    def provenance(self) -> Dict[str, Any]:
        return {
            "requested_coordinate_contract": self.requested_coordinate_contract,
            "resolved_coordinate_contract": self.resolved_coordinate_contract,
            "primary_coordinate_contract": self.primary_coordinate_contract,
            "primary_coordinate_layer": self.primary_coordinate_layer,
            "anchor_id": self.anchor_id,
            "anchor_hash": self.anchor_hash,
            "anchor_source": self.anchor_source,
            "schema_version": self.schema_version,
            "mndm_version": self.mndm_version,
        }


@dataclass(frozen=True)
class GeometryContractState:
    status: Optional[str]
    invalidity_policy: Optional[str]
    coords_9d_degenerate_axes: tuple[str, ...]
    jacobian_9d_windows_retained: Optional[int]
    jacobian_9d_invalid_windows: Optional[int]

    def has_coords_9d_degenerate_axes(self) -> bool:
        return len(self.coords_9d_degenerate_axes) > 0

    def has_zero_retained_jacobian_9d(self) -> bool:
        return self.jacobian_9d_windows_retained is not None and self.jacobian_9d_windows_retained <= 0

    def provenance(self) -> Dict[str, Any]:
        return {
            "geometry_contract_status": self.status,
            "geometry_invalidity_policy": self.invalidity_policy,
            "geometry_coords_9d_degenerate_axes": list(self.coords_9d_degenerate_axes),
            "geometry_coords_9d_degenerate_axes_n": int(len(self.coords_9d_degenerate_axes)),
            "geometry_jacobian_9d_windows_retained": self.jacobian_9d_windows_retained,
            "geometry_jacobian_9d_invalid_windows": self.jacobian_9d_invalid_windows,
        }


def read_run_contract(handle: h5py.File) -> RunContract:
    attrs = handle.attrs
    schema_version = _to_str(attrs.get("schema_version"))
    mndm_version = _to_str(attrs.get("mndm_version"))
    primary_coordinate_layer = _normalize_h5_path(attrs.get("primary_coordinate_layer"))
    primary_coordinate_contract = _normalize_contract_or_none(attrs.get("primary_coordinate_contract"))
    anchor_id = _to_str(attrs.get("anchor_id"))
    anchor_hash = _to_str(attrs.get("anchor_hash"))
    anchor_source = _to_str(attrs.get("anchor_source"))
    explicit_layers_present = any(
        group_name in handle
        for group_name in (
            "/coords_3d_subject_anchored",
            "/coords_3d_cohort_anchored",
            "/coords_9d_subject_anchored",
            "/coords_9d_cohort_anchored",
        )
    )
    is_mndm_2_1 = bool(
        schema_version == "mnps_tensor_spec_v2_1"
        or (mndm_version or "").startswith("2.1")
        or explicit_layers_present
    )
    return RunContract(
        schema_version=schema_version,
        mndm_version=mndm_version,
        primary_coordinate_layer=primary_coordinate_layer,
        primary_coordinate_contract=primary_coordinate_contract,
        anchor_id=anchor_id,
        anchor_hash=anchor_hash,
        anchor_source=anchor_source,
        is_mndm_2_1=is_mndm_2_1,
    )


def _dataset_exists(handle: h5py.File, dataset_path: Optional[str]) -> bool:
    return bool(dataset_path and dataset_path in handle and isinstance(handle[dataset_path], h5py.Dataset))


def _read_dataset_value(handle: h5py.File, dataset_path: str) -> Any:
    if not _dataset_exists(handle, dataset_path):
        return None
    raw = handle[dataset_path][()]
    if isinstance(raw, np.ndarray) and raw.ndim == 0:
        return raw.item()
    return raw


def _read_dataset_or_attr(handle: h5py.File, dataset_path: str, *, attr_key: Optional[str] = None) -> Any:
    value = _read_dataset_value(handle, dataset_path)
    if value is not None:
        return value
    if attr_key is not None:
        return handle.attrs.get(attr_key)
    return None


def _to_optional_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return _to_optional_int(value.item())
        if value.size == 0:
            return None
        return _to_optional_int(value.reshape(-1)[0])
    try:
        return int(value)
    except Exception:
        try:
            return int(float(value))
        except Exception:
            return None


def _to_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return _to_str_list(value.item())
        out: list[str] = []
        for item in value.reshape(-1).tolist():
            text = _to_str(item)
            if text is None:
                continue
            cleaned = text.strip()
            if cleaned:
                out.append(cleaned)
        return out
    text = _to_str(value)
    if text is None:
        return []
    cleaned = text.strip()
    if not cleaned:
        return []
    return [cleaned]


def read_geometry_contract_state(handle: h5py.File) -> GeometryContractState:
    status = _to_str(
        _read_dataset_or_attr(
            handle,
            "/provenance/geometry_contract/status",
            attr_key="geometry_contract_status",
        )
    ) or _to_str(_read_dataset_value(handle, "/provenance/contract/geometry_contract_status"))
    invalidity_policy = _to_str(
        _read_dataset_or_attr(
            handle,
            "/provenance/contract/geometry_invalidity_policy",
            attr_key="geometry_invalidity_policy",
        )
    )
    degenerate_axes = tuple(
        _to_str_list(
            _read_dataset_value(handle, "/provenance/geometry_contract/coords_9d/degenerate_axes")
        )
    )
    jacobian_9d_windows_retained = _to_optional_int(
        _read_dataset_value(handle, "/provenance/geometry_contract/jacobian_9d/windows_retained")
    )
    jacobian_9d_invalid_windows = _to_optional_int(
        _read_dataset_or_attr(
            handle,
            "/provenance/geometry_contract/jacobian_9d/invalid_windows",
            attr_key="geometry_jacobian_9d_invalid_windows",
        )
    )
    return GeometryContractState(
        status=status,
        invalidity_policy=invalidity_policy,
        coords_9d_degenerate_axes=degenerate_axes,
        jacobian_9d_windows_retained=jacobian_9d_windows_retained,
        jacobian_9d_invalid_windows=jacobian_9d_invalid_windows,
    )


def _group_exists(handle: h5py.File, group_path: Optional[str]) -> bool:
    return bool(group_path and group_path in handle and isinstance(handle[group_path], h5py.Group))


def _dedupe_paths(*paths: Optional[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if not path or path in seen:
            continue
        seen.add(path)
        out.append(path)
    return out


def _layer_values_path(group_path: Optional[str]) -> Optional[str]:
    group_path = _normalize_h5_path(group_path)
    if group_path is None:
        return None
    return f"{group_path}/values"


def _layer_names_path(group_path: Optional[str]) -> Optional[str]:
    group_path = _normalize_h5_path(group_path)
    if group_path is None:
        return None
    return f"{group_path}/names"


def _candidate_primary_layer(run: RunContract, *, dims: int, coordinate_contract: str) -> Optional[str]:
    layer = run.primary_coordinate_layer
    if layer is None or run.primary_coordinate_contract != coordinate_contract:
        return None
    token = f"coords_{dims}d_"
    return layer if token in layer else None


def _first_existing_coordinate_group(
    handle: h5py.File,
    *,
    dims: int,
    coordinate_contract: str,
    run: RunContract,
) -> Optional[str]:
    return next(
        iter(
            (
                candidate
                for candidate in _dedupe_paths(
                    _candidate_primary_layer(run, dims=dims, coordinate_contract=coordinate_contract),
                    f"/coords_{dims}d_{coordinate_contract}",
                )
                if _group_exists(handle, candidate) and _dataset_exists(handle, _layer_values_path(candidate))
            )
        ),
        None,
    )


def _default_coordinate_names(values: np.ndarray, *, dims: int) -> list[str]:
    if dims == 3:
        return ["m", "d", "e"]
    width = int(values.shape[1]) if values.ndim == 2 else 0
    return [f"f{i}" for i in range(width)]


def _load_names(handle: h5py.File, names_path: Optional[str], values: np.ndarray, *, dims: int) -> list[str]:
    if names_path and _dataset_exists(handle, names_path):
        raw_names = np.asarray(handle[names_path][:]).reshape(-1).tolist()
        decoded = [_to_str(item) or f"f{i}" for i, item in enumerate(raw_names)]
        if decoded:
            return decoded
    return _default_coordinate_names(values, dims=dims)


def _resolved_coordinate_data(
    handle: h5py.File,
    *,
    values_path: str,
    names_path: Optional[str],
    requested_coordinate_contract: str,
    resolved_coordinate_contract: str,
    run: RunContract,
) -> ResolvedCoordinateData:
    values = np.asarray(handle[values_path][:], dtype=float)
    names = _load_names(handle, names_path, values, dims=3 if values.shape[1] >= 3 and len(values.shape) == 2 and values.shape[1] <= 3 else 9)
    return ResolvedCoordinateData(
        values=values,
        names=names,
        values_path=values_path,
        names_path=names_path if names_path and _dataset_exists(handle, names_path) else None,
        requested_coordinate_contract=requested_coordinate_contract,
        resolved_coordinate_contract=resolved_coordinate_contract,
        primary_coordinate_contract=run.primary_coordinate_contract,
        primary_coordinate_layer=run.primary_coordinate_layer,
        anchor_id=run.anchor_id,
        anchor_hash=run.anchor_hash,
        anchor_source=run.anchor_source,
        schema_version=run.schema_version,
        mndm_version=run.mndm_version,
    )


def _resolve_legacy_coords(handle: h5py.File, *, dims: int, requested_coordinate_contract: str, run: RunContract) -> Optional[ResolvedCoordinateData]:
    if dims == 3:
        values_path = next((candidate for candidate in ("/mnps_3d", "/x") if _dataset_exists(handle, candidate)), None)
        if values_path is None:
            return None
        return _resolved_coordinate_data(
            handle,
            values_path=values_path,
            names_path=None,
            requested_coordinate_contract=requested_coordinate_contract,
            resolved_coordinate_contract="legacy",
            run=run,
        )
    values_path = next(
        (candidate for candidate in ("/coords_9d/values", "/coords_v2/values") if _dataset_exists(handle, candidate)),
        None,
    )
    if values_path is None:
        return None
    names_path = next(
        (candidate for candidate in ("/coords_9d/names", "/coords_v2/names") if _dataset_exists(handle, candidate)),
        None,
    )
    return _resolved_coordinate_data(
        handle,
        values_path=values_path,
        names_path=names_path,
        requested_coordinate_contract=requested_coordinate_contract,
        resolved_coordinate_contract="legacy",
        run=run,
    )


def resolve_coords_3d(handle: h5py.File, coordinate_contract: Any = DEFAULT_COORDINATE_CONTRACT) -> Optional[ResolvedCoordinateData]:
    requested = normalize_coordinate_contract(coordinate_contract)
    run = read_run_contract(handle)
    if requested == "legacy":
        return _resolve_legacy_coords(handle, dims=3, requested_coordinate_contract=requested, run=run)
    group_path = _first_existing_coordinate_group(handle, dims=3, coordinate_contract=requested, run=run)
    if group_path is not None:
        return _resolved_coordinate_data(
            handle,
            values_path=_layer_values_path(group_path) or "",
            names_path=_layer_names_path(group_path),
            requested_coordinate_contract=requested,
            resolved_coordinate_contract=requested,
            run=run,
        )
    if run.is_mndm_2_1:
        return None
    return _resolve_legacy_coords(handle, dims=3, requested_coordinate_contract=requested, run=run)


def resolve_coords_9d(handle: h5py.File, coordinate_contract: Any = DEFAULT_COORDINATE_CONTRACT) -> Optional[ResolvedCoordinateData]:
    requested = normalize_coordinate_contract(coordinate_contract)
    run = read_run_contract(handle)
    if requested == "legacy":
        return _resolve_legacy_coords(handle, dims=9, requested_coordinate_contract=requested, run=run)
    group_path = _first_existing_coordinate_group(handle, dims=9, coordinate_contract=requested, run=run)
    if group_path is not None:
        return _resolved_coordinate_data(
            handle,
            values_path=_layer_values_path(group_path) or "",
            names_path=_layer_names_path(group_path),
            requested_coordinate_contract=requested,
            resolved_coordinate_contract=requested,
            run=run,
        )
    if run.is_mndm_2_1:
        return None
    return _resolve_legacy_coords(handle, dims=9, requested_coordinate_contract=requested, run=run)


def _resolve_legacy_jacobian(
    handle: h5py.File,
    *,
    dims: int,
    requested_coordinate_contract: str,
    resolved_coordinate_contract: str,
    run: RunContract,
) -> Optional[ResolvedJacobianData]:
    candidate_triplets = (
        [("/jacobian/J_hat", "/jacobian/J_dot", "/jacobian/centers")]
        if dims == 3
        else [
            ("/jacobian_9D/J_hat", "/jacobian_9D/J_dot", "/jacobian_9D/centers"),
            ("/jacobian_v2/J_hat", "/jacobian_v2/J_dot", "/jacobian_v2/centers"),
        ]
    )
    for dataset_path, j_dot_path, centers_path in candidate_triplets:
        if not _dataset_exists(handle, dataset_path):
            continue
        return ResolvedJacobianData(
            j_hat=np.asarray(handle[dataset_path][:], dtype=float),
            j_dot=np.asarray(handle[j_dot_path][:], dtype=float) if _dataset_exists(handle, j_dot_path) else None,
            centers=np.asarray(handle[centers_path][:], dtype=int).reshape(-1)
            if _dataset_exists(handle, centers_path)
            else None,
            dataset_path=dataset_path,
            j_dot_path=j_dot_path if _dataset_exists(handle, j_dot_path) else None,
            centers_path=centers_path if _dataset_exists(handle, centers_path) else None,
            requested_coordinate_contract=requested_coordinate_contract,
            resolved_coordinate_contract=resolved_coordinate_contract,
            primary_coordinate_contract=run.primary_coordinate_contract,
            primary_coordinate_layer=run.primary_coordinate_layer,
            anchor_id=run.anchor_id,
            anchor_hash=run.anchor_hash,
            anchor_source=run.anchor_source,
            schema_version=run.schema_version,
            mndm_version=run.mndm_version,
        )
    return None


def resolve_jacobian_3d(handle: h5py.File, coordinate_contract: Any = DEFAULT_COORDINATE_CONTRACT) -> Optional[ResolvedJacobianData]:
    requested = normalize_coordinate_contract(coordinate_contract)
    run = read_run_contract(handle)
    if requested == "legacy":
        return _resolve_legacy_jacobian(
            handle,
            dims=3,
            requested_coordinate_contract=requested,
            resolved_coordinate_contract="legacy",
            run=run,
        )
    if run.is_mndm_2_1:
        if run.primary_coordinate_contract != requested:
            return None
        return _resolve_legacy_jacobian(
            handle,
            dims=3,
            requested_coordinate_contract=requested,
            resolved_coordinate_contract=requested,
            run=run,
        )
    return _resolve_legacy_jacobian(
        handle,
        dims=3,
        requested_coordinate_contract=requested,
        resolved_coordinate_contract="legacy",
        run=run,
    )


def resolve_jacobian_9d(handle: h5py.File, coordinate_contract: Any = DEFAULT_COORDINATE_CONTRACT) -> Optional[ResolvedJacobianData]:
    requested = normalize_coordinate_contract(coordinate_contract)
    run = read_run_contract(handle)
    if requested == "legacy":
        return _resolve_legacy_jacobian(
            handle,
            dims=9,
            requested_coordinate_contract=requested,
            resolved_coordinate_contract="legacy",
            run=run,
        )
    if run.is_mndm_2_1:
        if run.primary_coordinate_contract != requested:
            return None
        return _resolve_legacy_jacobian(
            handle,
            dims=9,
            requested_coordinate_contract=requested,
            resolved_coordinate_contract=requested,
            run=run,
        )
    return _resolve_legacy_jacobian(
        handle,
        dims=9,
        requested_coordinate_contract=requested,
        resolved_coordinate_contract="legacy",
        run=run,
    )
