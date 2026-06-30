from __future__ import annotations

"""Deprecated adapter import path kept for compatibility.

Prefer importing adapter APIs from ``nmd_analysis.adapters``.
"""

from dataclasses import dataclass
from functools import partial
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import warnings

import h5py
import numpy as np
import re

from .config import load_dataset_config
from .h5_contract import (
    read_run_contract,
    resolve_coords_3d,
    resolve_coords_9d,
    resolve_jacobian_3d,
    resolve_jacobian_9d,
)
from .participant_metadata import derive_medication_metadata, read_json_dataset


LegacyRowsFn = Callable[[Path], List[Dict[str, Any]]]
SLEEP_STAGE_CODE_TO_LABEL: Dict[int, str] = {
    0: "awake",
    2: "nrem2",
    3: "nrem3",
    4: "rem",
}
MIN_SLEEP_STAGE_TIMEPOINTS = 20
ACTIVE_STAGE_CODE_TO_LABEL: Dict[int, str] = dict(SLEEP_STAGE_CODE_TO_LABEL)
ACTIVE_MIN_STAGE_TIMEPOINTS = MIN_SLEEP_STAGE_TIMEPOINTS
_LEGACY_ADAPTER_WARNING_EMITTED = False


@dataclass(frozen=True)
class LegacyAnalysisAdapter:
    analysis_type: str
    collect_rows: LegacyRowsFn


def _to_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        try:
            return bytes(value).decode("utf-8")
        except Exception:
            return str(value)
    return str(value)


def _nan_stats(values: np.ndarray) -> Dict[str, float]:
    arr0 = np.asarray(values, dtype=float).ravel()
    finite = np.isfinite(arr0)
    arr = arr0[finite]
    out = {
        "n_total": float(arr0.size),
        "n_finite": float(arr.size),
        "finite_frac": float(arr.size / arr0.size) if arr0.size else float("nan"),
    }
    if arr.size == 0:
        out.update({"mean": float("nan"), "median": float("nan"), "std": float("nan")})
        return out
    out.update({"mean": float(arr.mean()), "median": float(np.median(arr)), "std": float(arr.std())})
    return out


def _safe_col(name: str) -> str:
    clean = re.sub(r"[^0-9A-Za-z_]+", "_", str(name)).strip("_")
    return clean or "feature"


def _to_python_scalar(value: Any) -> Any:
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        return _to_str(value)
    return value


def _first_existing_dataset(handle: h5py.File, candidates: List[str]) -> Optional[str]:
    for candidate in candidates:
        if candidate in handle:
            return candidate
    return None


def _stage_base_metadata(base: Dict[str, Any], label: str) -> Dict[str, Any]:
    row = dict(base)
    if row.get("dataset_id"):
        row["dataset_id"] = f"{row['dataset_id']}:stage_{label}"
    row["condition"] = label
    row["stage"] = label
    return row


def _sleep_stage_labels(handle: h5py.File) -> Optional[np.ndarray]:
    if "/labels/stage" not in handle:
        return None
    stage = np.asarray(handle["/labels/stage"][:], dtype=int).reshape(-1)
    return stage if stage.size else None


def _iter_sleep_stage_indices(
    stage: Optional[np.ndarray],
    n_samples: int,
    *,
    min_points: Optional[int] = None,
) -> List[Tuple[int, str, np.ndarray]]:
    if stage is None or n_samples <= 0:
        return []
    usable = np.asarray(stage[:n_samples], dtype=int).reshape(-1)
    resolved_min_points = int(min_points if min_points is not None else ACTIVE_MIN_STAGE_TIMEPOINTS)
    out: List[Tuple[int, str, np.ndarray]] = []
    for code, label in ACTIVE_STAGE_CODE_TO_LABEL.items():
        idx = np.flatnonzero(usable == int(code))
        if idx.size >= resolved_min_points:
            out.append((int(code), label, idx))
    return out


def _resolve_centers(handle: h5py.File, candidates: List[str], n_windows: int) -> np.ndarray:
    centers_path = _first_existing_dataset(handle, candidates)
    if centers_path is None:
        return np.arange(n_windows, dtype=int)
    centers = np.asarray(handle[centers_path][:], dtype=int).reshape(-1)
    if centers.shape[0] != n_windows:
        return np.arange(min(n_windows, centers.shape[0]), dtype=int)
    return centers


def _with_qc(base: Dict[str, Any], *, finite_ok: bool, not_testable: bool = False, reason: Optional[str] = None) -> Dict[str, Any]:
    row = dict(base)
    row["finite_ok"] = bool(finite_ok)
    row["not_testable"] = bool(not_testable)
    if reason:
        row["not_testable_reason"] = reason
    return row


def _read_participant_mapped_json(handle: h5py.File) -> Dict[str, Any]:
    """Read participant/mapped_json from an open H5 file.

    This is the new standard metadata source embedded by the ingest pipeline.
    Returns an empty dict if the dataset is absent or cannot be parsed.
    """
    return read_json_dataset(handle, "participant/mapped_json")


def _pick_meta(
    mapped: Dict[str, Any],
    attrs: Dict[str, Any],
    key: str,
    *fallback_attr_keys: str,
) -> Optional[str]:
    """Return the first non-empty value: participant/mapped_json → H5 root attrs.

    ``mapped`` is the dict from ``participant/mapped_json`` (new standard).
    ``attrs`` are the raw H5 root attributes (old fallback).
    ``key`` is checked in both; extra ``fallback_attr_keys`` are only checked in attrs.
    """
    v = mapped.get(key)
    if v is not None and str(v).strip():
        return _to_str(v)
    for fk in (key,) + fallback_attr_keys:
        v = attrs.get(fk)
        if v is not None:
            return _to_str(v)
    return None


def _base_h5_metadata_from_handle(handle: h5py.File, h5_path: Path) -> Dict[str, Any]:
    attrs = dict(handle.attrs.items())
    mapped = _read_participant_mapped_json(handle)
    row_json = read_json_dataset(handle, "participant/row_json")
    group_value = _pick_meta(mapped, attrs, "group", "meta_type", "type")
    base = {
        "dataset_id": _to_str(attrs.get("dataset_id")),
        "subject_id": _to_str(attrs.get("subject_id")),
        "session": _to_str(attrs.get("session")),
        "run": _to_str(attrs.get("run") or "run-01"),
        "acq": _to_str(attrs.get("acq")),
        "group": group_value,
        "condition": _pick_meta(mapped, attrs, "condition"),
        "task": _pick_meta(mapped, attrs, "task"),
        "modality": _to_str(attrs.get("modality")),
        "source_h5_path": str(h5_path),
    }
    base.update(derive_medication_metadata(group_value, row_json))
    base.update(read_run_contract(handle).provenance())
    return base


def _base_h5_metadata(h5_path: Path) -> Dict[str, Any]:
    with h5py.File(h5_path, "r") as handle:
        return _base_h5_metadata_from_handle(handle, h5_path)


def _summarize_global_mnps_3d_row(
    base: Dict[str, Any],
    values: np.ndarray,
    *,
    source_dataset_path: str,
) -> Optional[Dict[str, Any]]:
    x = np.asarray(values, dtype=float)
    if x.ndim != 2 or x.shape[1] < 3:
        return None
    names = ["m", "d", "e"]
    finite_ok = bool(np.isfinite(x[:, :3]).all())
    row: Dict[str, Any] = _with_qc(base, finite_ok=finite_ok)
    row["source_dataset_path"] = source_dataset_path
    row["n_timepoints"] = int(x.shape[0])
    for idx, name in enumerate(names):
        stats = _nan_stats(x[:, idx])
        row[f"{name}_mean"] = stats["mean"]
        row[f"{name}_median"] = stats["median"]
        row[f"{name}_std"] = stats["std"]
        row[f"{name}_finite_frac"] = stats["finite_frac"]
    return row


def _rows_global_mnps_3d(
    h5_path: Path,
    *,
    coordinate_contract: str,
) -> List[Dict[str, Any]]:
    with h5py.File(h5_path, "r") as handle:
        resolved = resolve_coords_3d(handle, coordinate_contract)
        if resolved is None:
            return []
        base = _base_h5_metadata_from_handle(handle, h5_path)
    base.update(resolved.provenance())
    row = _summarize_global_mnps_3d_row(base, resolved.values, source_dataset_path=resolved.values_path)
    return [row] if row is not None else []


def _summarize_global_mnps_jacobian_row(
    base: Dict[str, Any],
    j_hat: np.ndarray,
    j_dot: Optional[np.ndarray],
    *,
    source_dataset_path: str,
    dims: int,
) -> Optional[Dict[str, Any]]:
    j_hat = np.asarray(j_hat, dtype=float)
    if j_hat.ndim != 3 or j_hat.shape[1] != j_hat.shape[2] or j_hat.shape[1] != dims:
        return None
    finite_ok = bool(np.isfinite(j_hat).all())
    row: Dict[str, Any] = _with_qc(
        base,
        finite_ok=finite_ok,
        not_testable=not finite_ok,
        reason="jacobian_nonfinite" if not finite_ok else None,
    )
    row["n_windows"] = int(j_hat.shape[0])
    row["dims"] = int(j_hat.shape[1])
    row["source_dataset_path"] = source_dataset_path
    trace = np.trace(j_hat, axis1=1, axis2=2)
    omega = 0.5 * (j_hat - np.swapaxes(j_hat, 1, 2))
    fro = np.linalg.norm(j_hat, axis=(1, 2))
    rot = np.linalg.norm(omega, axis=(1, 2))
    op_norm = np.full((j_hat.shape[0],), np.nan, dtype=float)
    aci = np.full((j_hat.shape[0],), np.nan, dtype=float)
    for w in range(j_hat.shape[0]):
        try:
            sing = np.linalg.svd(j_hat[w], compute_uv=False)
            if sing.size:
                op_norm[w] = float(sing[0])
            if sing.size >= 3:
                aci[w] = float(sing[0] / (sing[1] + sing[2] + 1e-12))
        except Exception:
            continue
    row["trace_mean"] = _nan_stats(trace)["mean"]
    row["trace_median"] = _nan_stats(trace)["median"]
    row["rotation_norm_mean"] = _nan_stats(rot)["mean"]
    row["rotation_norm_median"] = _nan_stats(rot)["median"]
    row["frobenius_norm_mean"] = _nan_stats(fro)["mean"]
    row["frobenius_norm_median"] = _nan_stats(fro)["median"]
    row["a_operator_norm_mean"] = _nan_stats(op_norm)["mean"]
    row["a_operator_norm_median"] = _nan_stats(op_norm)["median"]
    row["aci_mean"] = _nan_stats(aci)["mean"]
    row["aci_median"] = _nan_stats(aci)["median"]

    try:
        eigvals = np.linalg.eigvals(j_hat)
        # Keep rotational content visible instead of discarding imaginary parts.
        eig_abs = np.abs(eigvals)
        row["eig_ok"] = True
        row["anisotropy_abs_eig_mean"] = _nan_stats(np.var(eig_abs, axis=1))["mean"]
        row["anisotropy_abs_eig_median"] = _nan_stats(np.var(eig_abs, axis=1))["median"]
        row["spectral_radius_mean"] = _nan_stats(np.max(eig_abs, axis=1))["mean"]
        row["spectral_radius_median"] = _nan_stats(np.max(eig_abs, axis=1))["median"]
        row["rotational_power_mean"] = _nan_stats(np.mean(np.abs(np.imag(eigvals)), axis=1))["mean"]
        row["rotational_power_median"] = _nan_stats(np.mean(np.abs(np.imag(eigvals)), axis=1))["median"]
    except Exception:
        row["eig_ok"] = False
        row["anisotropy_abs_eig_mean"] = float("nan")
        row["anisotropy_abs_eig_median"] = float("nan")
        row["spectral_radius_mean"] = float("nan")
        row["spectral_radius_median"] = float("nan")
        row["rotational_power_mean"] = float("nan")
        row["rotational_power_median"] = float("nan")

    # Basic near-singular signal for reviewer-facing QC.
    cond_vals: List[float] = []
    for w in range(j_hat.shape[0]):
        try:
            cond_vals.append(float(np.linalg.cond(j_hat[w])))
        except Exception:
            cond_vals.append(float("nan"))
    cond_arr = np.asarray(cond_vals, dtype=float)
    row["jacobian_cond_median"] = _nan_stats(cond_arr)["median"]
    row["jacobian_near_singular_rate"] = float(np.mean(cond_arr > 1e8)) if np.isfinite(cond_arr).any() else float("nan")
    if j_dot is not None:
        j_dot = np.asarray(j_dot, dtype=float)
        if j_dot.ndim == 3 and j_dot.shape == j_hat.shape:
            j_dot_fro = np.linalg.norm(j_dot, axis=(1, 2))
            mdr = j_dot_fro / (fro + 1e-12)
            row["mdr_mean"] = _nan_stats(mdr)["mean"]
            row["mdr_median"] = _nan_stats(mdr)["median"]
    return row


def _rows_global_mnps_jacobian(
    h5_path: Path,
    *,
    coordinate_contract: str,
    dims: int,
) -> List[Dict[str, Any]]:
    with h5py.File(h5_path, "r") as handle:
        resolved = (
            resolve_jacobian_3d(handle, coordinate_contract)
            if dims == 3
            else resolve_jacobian_9d(handle, coordinate_contract)
        )
        if resolved is None:
            return []
        base = _base_h5_metadata_from_handle(handle, h5_path)
    base.update(resolved.provenance())
    row = _summarize_global_mnps_jacobian_row(
        base,
        resolved.j_hat,
        resolved.j_dot,
        source_dataset_path=resolved.dataset_path,
        dims=dims,
    )
    return [row] if row is not None else []


def _rows_global_mnps_jacobian_3d(
    h5_path: Path,
    *,
    coordinate_contract: str,
) -> List[Dict[str, Any]]:
    return _rows_global_mnps_jacobian(h5_path, coordinate_contract=coordinate_contract, dims=3)


def _estimate_temporal_jacobian_delta(j_hat: np.ndarray) -> Optional[np.ndarray]:
    arr = np.asarray(j_hat, dtype=float)
    if arr.ndim != 3 or arr.shape[0] <= 0:
        return None
    if arr.shape[0] == 1:
        return np.zeros_like(arr)
    delta = np.empty_like(arr)
    delta[0] = arr[1] - arr[0]
    delta[-1] = arr[-1] - arr[-2]
    if arr.shape[0] > 2:
        delta[1:-1] = 0.5 * (arr[2:] - arr[:-2])
    return delta


def _rows_regional_mnps_jacobian_3d(h5_path: Path) -> List[Dict[str, Any]]:
    with h5py.File(h5_path, "r") as handle:
        if "/regional_mnps" not in handle:
            return []
        reg = handle["/regional_mnps"]
        base = _base_h5_metadata_from_handle(handle, h5_path)
        rows: List[Dict[str, Any]] = []
        for net in reg.keys():
            if net == "time":
                continue
            net_grp = reg[net]
            if "jacobian" not in net_grp:
                continue
            j_hat = np.asarray(net_grp["jacobian"][:], dtype=float)
            if j_hat.ndim != 3 or j_hat.shape[1:] != (3, 3):
                continue
            j_dot = None
            if "jacobian_dot" in net_grp:
                candidate = np.asarray(net_grp["jacobian_dot"][:], dtype=float)
                if candidate.shape == j_hat.shape:
                    j_dot = candidate
            if j_dot is None:
                # Regional EEG exports currently expose the Jacobian tensor but not always
                # an explicit Jacobian derivative. A centered finite-difference fallback
                # preserves the MDR contract used by the manuscript-facing summaries.
                j_dot = _estimate_temporal_jacobian_delta(j_hat)
            row = _summarize_global_mnps_jacobian_row(
                dict(base),
                j_hat,
                j_dot,
                source_dataset_path=f"/regional_mnps/{net}/jacobian",
                dims=3,
            )
            if row is None:
                continue
            row["network"] = net
            row["block_scope"] = net
            row["block_space"] = "mnps_3d"
            row["source_group"] = net
            row["target_group"] = net
            row["n_regions"] = int(net_grp.attrs.get("n_regions", 0))
            rows.append(row)
    return rows


def _summarize_global_mnps_9d_row(
    base: Dict[str, Any],
    values: np.ndarray,
    names: List[str],
    *,
    source_dataset_path: str,
) -> Optional[Dict[str, Any]]:
    values = np.asarray(values, dtype=float)
    if values.ndim != 2:
        return None
    row: Dict[str, Any] = dict(base)
    row["source_dataset_path"] = source_dataset_path
    row["n_timepoints"] = int(values.shape[0])
    for idx, name in enumerate(names):
        stats = _nan_stats(values[:, idx])
        key = _safe_col(str(name))
        row[f"{key}_mean"] = stats["mean"]
        row[f"{key}_median"] = stats["median"]
        row[f"{key}_std"] = stats["std"]
        row[f"{key}_finite_frac"] = stats["finite_frac"]
    row["finite_ok"] = bool(np.isfinite(values).all())
    row["not_testable"] = not row["finite_ok"]
    return row


def _rows_global_mnps_9d(
    h5_path: Path,
    *,
    coordinate_contract: str,
) -> List[Dict[str, Any]]:
    with h5py.File(h5_path, "r") as handle:
        resolved = resolve_coords_9d(handle, coordinate_contract)
        if resolved is None:
            return []
        base = _base_h5_metadata_from_handle(handle, h5_path)
    base.update(resolved.provenance())
    row = _summarize_global_mnps_9d_row(
        base,
        resolved.values,
        resolved.names,
        source_dataset_path=resolved.values_path,
    )
    return [row] if row is not None else []


def _rows_global_mnps_jacobian_9d(
    h5_path: Path,
    *,
    coordinate_contract: str,
) -> List[Dict[str, Any]]:
    return _rows_global_mnps_jacobian(h5_path, coordinate_contract=coordinate_contract, dims=9)


def _rows_regional_mnps_jacobian_3d_sleep(h5_path: Path) -> List[Dict[str, Any]]:
    with h5py.File(h5_path, "r") as handle:
        stage = _sleep_stage_labels(handle)
        if stage is None or "/regional_mnps" not in handle:
            return []
        reg = handle["/regional_mnps"]
        centers = _resolve_centers(handle, ["/jacobian/centers"], n_windows=int(stage.shape[0]))
        base = _base_h5_metadata(h5_path)
        rows: List[Dict[str, Any]] = []
        for net in reg.keys():
            if net == "time":
                continue
            net_grp = reg[net]
            if "jacobian" not in net_grp:
                continue
            j_hat = np.asarray(net_grp["jacobian"][:], dtype=float)
            if j_hat.ndim != 3 or j_hat.shape[1:] != (3, 3):
                continue
            n = min(int(j_hat.shape[0]), int(centers.shape[0]))
            if n <= 0:
                continue
            aligned_centers = np.asarray(centers[:n], dtype=int).reshape(-1)
            valid = (aligned_centers >= 0) & (aligned_centers < stage.shape[0])
            if not np.any(valid):
                continue
            j_hat = j_hat[:n][valid]
            aligned_centers = aligned_centers[valid]
            stage_at_window = np.asarray(stage[aligned_centers], dtype=int).reshape(-1)
            for _, label, idx in _iter_sleep_stage_indices(stage_at_window, j_hat.shape[0]):
                row = _summarize_global_mnps_jacobian_row(
                    _stage_base_metadata(base, label),
                    j_hat[idx],
                    source_dataset_path=f"/regional_mnps/{net}/jacobian",
                    dims=3,
                )
                if row is None:
                    continue
                row["network"] = net
                row["block_scope"] = net
                row["block_space"] = "mnps_3d"
                rows.append(row)
    return rows


def _rows_global_mnps_3d_sleep(
    h5_path: Path,
    *,
    coordinate_contract: str,
) -> List[Dict[str, Any]]:
    with h5py.File(h5_path, "r") as handle:
        resolved = resolve_coords_3d(handle, coordinate_contract)
        stage = _sleep_stage_labels(handle)
        if resolved is None or stage is None:
            return []
        base = _base_h5_metadata_from_handle(handle, h5_path)
    base.update(resolved.provenance())
    x = resolved.values
    n = min(int(x.shape[0]), int(stage.shape[0]))
    rows: List[Dict[str, Any]] = []
    for _, label, idx in _iter_sleep_stage_indices(stage, n):
        row = _summarize_global_mnps_3d_row(
            _stage_base_metadata(base, label),
            x[idx],
            source_dataset_path=resolved.values_path,
        )
        if row is not None:
            rows.append(row)
    return rows


def _rows_global_mnps_9d_sleep(
    h5_path: Path,
    *,
    coordinate_contract: str,
) -> List[Dict[str, Any]]:
    with h5py.File(h5_path, "r") as handle:
        resolved = resolve_coords_9d(handle, coordinate_contract)
        stage = _sleep_stage_labels(handle)
        if resolved is None or stage is None:
            return []
        base = _base_h5_metadata_from_handle(handle, h5_path)
    base.update(resolved.provenance())
    values = resolved.values
    n = min(int(values.shape[0]), int(stage.shape[0]))
    rows: List[Dict[str, Any]] = []
    for _, label, idx in _iter_sleep_stage_indices(stage, n):
        row = _summarize_global_mnps_9d_row(
            _stage_base_metadata(base, label),
            values[idx],
            resolved.names,
            source_dataset_path=resolved.values_path,
        )
        if row is not None:
            rows.append(row)
    return rows


def _rows_global_mnps_jacobian_sleep(
    h5_path: Path,
    *,
    coordinate_contract: str,
    dims: int,
) -> List[Dict[str, Any]]:
    with h5py.File(h5_path, "r") as handle:
        resolved = (
            resolve_jacobian_3d(handle, coordinate_contract)
            if dims == 3
            else resolve_jacobian_9d(handle, coordinate_contract)
        )
        stage = _sleep_stage_labels(handle)
        if resolved is None or stage is None:
            return []
        base = _base_h5_metadata_from_handle(handle, h5_path)
    base.update(resolved.provenance())
    centers = resolved.centers if resolved.centers is not None else np.arange(int(resolved.j_hat.shape[0]), dtype=int)
    n_windows = min(int(resolved.j_hat.shape[0]), int(centers.shape[0]))
    j_hat = resolved.j_hat[:n_windows]
    j_dot = resolved.j_dot[:n_windows] if resolved.j_dot is not None else None
    centers = centers[:n_windows]
    rows: List[Dict[str, Any]] = []
    for code, label, idx in _iter_sleep_stage_indices(stage, int(stage.shape[0])):
        keep_w = (centers >= 0) & (centers < int(stage.shape[0])) & (stage[centers] == int(code))
        j_stage = j_hat[keep_w]
        j_dot_stage = j_dot[keep_w] if j_dot is not None else None
        row = _summarize_global_mnps_jacobian_row(
            _stage_base_metadata(base, label),
            j_stage,
            j_dot_stage,
            source_dataset_path=resolved.dataset_path,
            dims=dims,
        )
        if row is not None:
            row["n_timepoints"] = int(idx.size)
            rows.append(row)
    return rows


def _rows_global_mnps_jacobian_3d_sleep(
    h5_path: Path,
    *,
    coordinate_contract: str,
) -> List[Dict[str, Any]]:
    return _rows_global_mnps_jacobian_sleep(h5_path, coordinate_contract=coordinate_contract, dims=3)


def _rows_global_mnps_jacobian_9d_sleep(
    h5_path: Path,
    *,
    coordinate_contract: str,
) -> List[Dict[str, Any]]:
    return _rows_global_mnps_jacobian_sleep(h5_path, coordinate_contract=coordinate_contract, dims=9)


def _rows_tabular_export(
    h5_path: Path,
    export_path: str,
    *,
    export_kind: str,
    required_numeric_cols: List[str],
    default_source_dim: Optional[float] = None,
    default_target_dim: Optional[float] = None,
    block_space: Optional[str] = None,
) -> List[Dict[str, Any]]:
    with h5py.File(h5_path, "r") as handle:
        if export_path not in handle:
            return []
        grp = handle[export_path]
        dataset_names = list(grp.keys())
        if not dataset_names:
            return []
        lengths = {name: int(np.asarray(grp[name][:]).shape[0]) for name in dataset_names}
        n_rows = max(lengths.values(), default=0)
        if n_rows <= 0:
            return []

        columns: Dict[str, np.ndarray] = {}
        for name in dataset_names:
            arr = np.asarray(grp[name][:])
            if arr.ndim == 0:
                arr = np.repeat(arr.reshape(1), n_rows)
            if arr.shape[0] != n_rows:
                return []
            columns[name] = arr

    base = _base_h5_metadata(h5_path)
    rows: List[Dict[str, Any]] = []
    for idx in range(n_rows):
        row: Dict[str, Any] = dict(base)
        row["source_dataset_path"] = export_path
        row["block_export_kind"] = export_kind
        for name, arr in columns.items():
            row[_safe_col(name)] = _to_python_scalar(arr[idx])

        if row.get("session") is None and row.get("session_id") is not None:
            row["session"] = row["session_id"]
        if row.get("task") is None and row.get("task_label") is not None:
            row["task"] = row["task_label"]
        if row.get("condition") is None and row.get("condition_label") not in (None, ""):
            row["condition"] = row["condition_label"]

        if row.get("network") is None and row.get("network_label") is not None:
            row["network"] = row["network_label"]
        if row.get("source_block") is None and row.get("in_group") is not None:
            row["source_block"] = row["in_group"]
        if row.get("target_block") is None and row.get("out_group") is not None:
            row["target_block"] = row["out_group"]
        if row.get("in_group") is None and row.get("source_block") is not None:
            row["in_group"] = row["source_block"]
        if row.get("out_group") is None and row.get("target_block") is not None:
            row["out_group"] = row["target_block"]
        if row.get("in_dim") is None and default_source_dim is not None:
            row["in_dim"] = float(default_source_dim)
        if row.get("out_dim") is None and default_target_dim is not None:
            row["out_dim"] = float(default_target_dim)

        # Harmonized downstream-facing aliases shared by both block-export schemas.
        row["block_scope"] = row.get("network") or "global"
        row["block_space"] = block_space or export_kind
        row["source_group"] = row.get("source_block") or row.get("in_group")
        row["target_group"] = row.get("target_block") or row.get("out_group")
        row["source_dim"] = row.get("in_dim")
        row["target_dim"] = row.get("out_dim")

        required_values = []
        for name in required_numeric_cols:
            value = row.get(name)
            if value is None:
                required_values.append(float("nan"))
            else:
                try:
                    required_values.append(float(value))
                except Exception:
                    required_values.append(float("nan"))
        finite_ok = bool(np.isfinite(np.asarray(required_values, dtype=float)).all())
        row["finite_ok"] = finite_ok
        row["not_testable"] = not finite_ok
        if not finite_ok:
            row["not_testable_reason"] = f"{export_kind}_missing_or_nonfinite"
        rows.append(row)
    return rows


def _rows_regional_block_jacobian(h5_path: Path) -> List[Dict[str, Any]]:
    return _rows_tabular_export(
        h5_path,
        "/extensions/tabular_exports/regional_block_jacobians_subjects",
        export_kind="regional_block_jacobians",
        default_source_dim=1.0,
        default_target_dim=1.0,
        block_space="mnps_3d",
        required_numeric_cols=[
            "block_anisotropy_mean",
            "block_frobenius_mean",
            "block_trace_mean",
            "n_timepoints",
        ],
    )


def _rows_stratified_block_jacobian(h5_path: Path) -> List[Dict[str, Any]]:
    return _rows_tabular_export(
        h5_path,
        "/extensions/tabular_exports/stratified_block_jacobians_subjects",
        export_kind="stratified_block_jacobians",
        block_space="coords_9d",
        required_numeric_cols=[
            "block_anisotropy_mean",
            "block_frobenius_mean",
            "block_trace_mean",
            "n_timepoints",
            "in_dim",
            "out_dim",
        ],
    )


def _rows_reachability_cones(
    h5_path: Path,
    *,
    coordinate_contract: str,
) -> List[Dict[str, Any]]:
    from .reachability_cones import collect_subject_csv_rows, summarize_reachability_h5

    summary = summarize_reachability_h5(h5_path, coordinate_contract=coordinate_contract)
    rows = collect_subject_csv_rows([summary])
    return [dict(row) for row in rows]


def _rows_reachability_cones_sleep(
    h5_path: Path,
    *,
    coordinate_contract: str,
) -> List[Dict[str, Any]]:
    from .reachability_cones import summarize_reachability_h5

    with h5py.File(h5_path, "r") as handle:
        stage = _sleep_stage_labels(handle)
        resolved = resolve_coords_9d(handle, coordinate_contract) or resolve_coords_3d(handle, coordinate_contract)
        if stage is None or resolved is None:
            return []
        values = resolved.values
    n = min(int(values.shape[0]), int(stage.shape[0]))
    finite_mask = np.isfinite(values[:n]).all(axis=1)
    rows: List[Dict[str, Any]] = []
    for _, label, idx in _iter_sleep_stage_indices(stage[:n], n):
        keep_idx = idx[finite_mask[idx]]
        if keep_idx.size < MIN_SLEEP_STAGE_TIMEPOINTS:
            continue
        summary = summarize_reachability_h5(
            h5_path,
            sample_indices=keep_idx,
            condition_override=label,
            dataset_id_suffix=f":stage_{label}",
            coordinate_contract=coordinate_contract,
        )
        row = dict(summary["flat"])
        row["stage"] = label
        rows.append(row)
    return rows


def _rows_regional_reachability_cones_3d(h5_path: Path) -> List[Dict[str, Any]]:
    from .reachability_cones import summarize_reachability_h5

    with h5py.File(h5_path, "r") as handle:
        if "/regional_mnps" not in handle:
            return []
        grp = handle["/regional_mnps"]
        rows: List[Dict[str, Any]] = []
        for net in grp.keys():
            if net == "time":
                continue
            net_grp = grp[net]
            if "mnps" not in net_grp:
                continue
            summary = summarize_reachability_h5(
                h5_path,
                dataset_path=f"/regional_mnps/{net}/mnps",
                used_space_override="regional_mnps_3d",
                flat_overrides={
                    "network": net,
                    "n_regions": int(net_grp.attrs.get("n_regions", 0)),
                    "source_dataset_path": f"/regional_mnps/{net}/mnps",
                },
            )
            rows.append(dict(summary["flat"]))
    return rows


def _rows_regional_reachability_cones_3d_sleep(h5_path: Path) -> List[Dict[str, Any]]:
    from .reachability_cones import summarize_reachability_h5

    with h5py.File(h5_path, "r") as handle:
        stage = _sleep_stage_labels(handle)
        if "/regional_mnps" not in handle or stage is None:
            return []
        grp = handle["/regional_mnps"]
        rows: List[Dict[str, Any]] = []
        for net in grp.keys():
            if net == "time":
                continue
            net_grp = grp[net]
            if "mnps" not in net_grp:
                continue
            mnps = np.asarray(net_grp["mnps"][:], dtype=float)
            n = min(int(mnps.shape[0]), int(stage.shape[0]))
            if n <= 0 or mnps.ndim != 2 or mnps.shape[1] < 3:
                continue
            finite_mask = np.isfinite(mnps[:n]).all(axis=1)
            for _, label, idx in _iter_sleep_stage_indices(stage[:n], n):
                keep_idx = idx[finite_mask[idx]]
                if keep_idx.size < MIN_SLEEP_STAGE_TIMEPOINTS:
                    continue
                summary = summarize_reachability_h5(
                    h5_path,
                    sample_indices=keep_idx,
                    condition_override=label,
                    dataset_id_suffix=f":stage_{label}",
                    dataset_path=f"/regional_mnps/{net}/mnps",
                    used_space_override="regional_mnps_3d",
                    flat_overrides={
                        "network": net,
                        "stage": label,
                        "n_regions": int(net_grp.attrs.get("n_regions", 0)),
                        "source_dataset_path": f"/regional_mnps/{net}/mnps",
                    },
                )
                rows.append(dict(summary["flat"]))
    return rows


def _rows_regional_3d(h5_path: Path) -> List[Dict[str, Any]]:
    # No proxy computation here. We only map precomputed regional artifacts.
    with h5py.File(h5_path, "r") as handle:
        if "/regional_mnps" not in handle:
            return []
        grp = handle["/regional_mnps"]
        rows: List[Dict[str, Any]] = []
        base = _base_h5_metadata(h5_path)
        for net in grp.keys():
            if net == "time":
                continue
            net_grp = grp[net]
            if "mnps" in net_grp:
                mnps = np.asarray(net_grp["mnps"][:], dtype=float)
                m = mnps[:, 0] if mnps.ndim == 2 and mnps.shape[1] >= 1 else np.array([])
                d = mnps[:, 1] if mnps.ndim == 2 and mnps.shape[1] >= 2 else np.array([])
                e = mnps[:, 2] if mnps.ndim == 2 and mnps.shape[1] >= 3 else np.array([])
                source_dataset_path = f"/regional_mnps/{net}/mnps"
            else:
                m = np.asarray(net_grp["m"][:], dtype=float) if "m" in net_grp else np.array([])
                d = np.asarray(net_grp["d"][:], dtype=float) if "d" in net_grp else np.array([])
                e = np.asarray(net_grp["e"][:], dtype=float) if "e" in net_grp else np.array([])
                source_dataset_path = f"/regional_mnps/{net}"
            row: Dict[str, Any] = dict(base)
            row["network"] = net
            row["source_dataset_path"] = source_dataset_path
            row["n_regions"] = int(net_grp.attrs.get("n_regions", 0))
            row["n_timepoints"] = int(m.size if m.size else (d.size if d.size else e.size))
            row["m_mean"] = _nan_stats(m)["mean"]
            row["d_mean"] = _nan_stats(d)["mean"]
            row["e_mean"] = _nan_stats(e)["mean"]
            row["m_median"] = _nan_stats(m)["median"]
            row["d_median"] = _nan_stats(d)["median"]
            row["e_median"] = _nan_stats(e)["median"]
            row["m_std"] = _nan_stats(m)["std"]
            row["d_std"] = _nan_stats(d)["std"]
            row["e_std"] = _nan_stats(e)["std"]
            finite_ok = bool(np.isfinite(np.concatenate([m, d, e]) if (m.size or d.size or e.size) else np.array([np.nan])).all())
            row["finite_ok"] = finite_ok
            row["not_testable"] = not finite_ok
            rows.append(row)
    return rows


def _rows_regional_3d_sleep(h5_path: Path) -> List[Dict[str, Any]]:
    with h5py.File(h5_path, "r") as handle:
        stage = _sleep_stage_labels(handle)
        if "/regional_mnps" not in handle or stage is None:
            return []
        grp = handle["/regional_mnps"]
        base = _base_h5_metadata(h5_path)
        rows: List[Dict[str, Any]] = []
        for net in grp.keys():
            if net == "time":
                continue
            net_grp = grp[net]
            if "mnps" not in net_grp:
                continue
            mnps = np.asarray(net_grp["mnps"][:], dtype=float)
            n = min(int(mnps.shape[0]), int(stage.shape[0]))
            if n <= 0 or mnps.ndim != 2 or mnps.shape[1] < 3:
                continue
            for _, label, idx in _iter_sleep_stage_indices(stage, n):
                stage_vals = mnps[idx]
                row: Dict[str, Any] = _stage_base_metadata(base, label)
                row["network"] = net
                row["source_dataset_path"] = f"/regional_mnps/{net}/mnps"
                row["n_regions"] = int(net_grp.attrs.get("n_regions", 0))
                row["n_timepoints"] = int(stage_vals.shape[0])
                row["m_mean"] = _nan_stats(stage_vals[:, 0])["mean"]
                row["d_mean"] = _nan_stats(stage_vals[:, 1])["mean"]
                row["e_mean"] = _nan_stats(stage_vals[:, 2])["mean"]
                row["m_median"] = _nan_stats(stage_vals[:, 0])["median"]
                row["d_median"] = _nan_stats(stage_vals[:, 1])["median"]
                row["e_median"] = _nan_stats(stage_vals[:, 2])["median"]
                row["m_std"] = _nan_stats(stage_vals[:, 0])["std"]
                row["d_std"] = _nan_stats(stage_vals[:, 1])["std"]
                row["e_std"] = _nan_stats(stage_vals[:, 2])["std"]
                row["finite_ok"] = bool(np.isfinite(stage_vals).all())
                row["not_testable"] = not row["finite_ok"]
                rows.append(row)
    return rows


def _rows_regional_9d(h5_path: Path) -> List[Dict[str, Any]]:
    # No proxy computation here. We only map precomputed regional stratified artifacts.
    with h5py.File(h5_path, "r") as handle:
        if "/regional_mnps" in handle:
            grp = handle["/regional_mnps"]
            uses_new_layout = True
        elif "/regional_stratified_mnps" in handle:
            grp = handle["/regional_stratified_mnps"]
            uses_new_layout = False
        else:
            return []
        base = _base_h5_metadata(h5_path)
        rows: List[Dict[str, Any]] = []
        for net in grp.keys():
            if net == "time":
                continue
            net_grp = grp[net]
            row: Dict[str, Any] = dict(base)
            row["network"] = net
            row["n_regions"] = int(net_grp.attrs.get("n_regions", 0))
            finite_all: List[np.ndarray] = []
            if uses_new_layout and "stratified" in net_grp:
                arr2d = np.asarray(net_grp["stratified"][:], dtype=float)
                row["source_dataset_path"] = f"/regional_mnps/{net}/stratified"
                coord_names = ("m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m")
                for idx, key in enumerate(coord_names):
                    if arr2d.ndim != 2 or arr2d.shape[1] <= idx:
                        continue
                    arr = arr2d[:, idx]
                    stats = _nan_stats(arr)
                    row[f"{key}_mean"] = stats["mean"]
                    row[f"{key}_median"] = stats["median"]
                    row[f"{key}_std"] = stats["std"]
                    finite_all.append(arr)
            else:
                row["source_dataset_path"] = f"/regional_stratified_mnps/{net}"
                for key in ("m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m"):
                    if key not in net_grp:
                        continue
                    arr = np.asarray(net_grp[key][:], dtype=float)
                    stats = _nan_stats(arr)
                    row[f"{key}_mean"] = stats["mean"]
                    row[f"{key}_median"] = stats["median"]
                    row[f"{key}_std"] = stats["std"]
                    finite_all.append(arr)
            if finite_all:
                concat = np.concatenate(finite_all)
                finite_ok = bool(np.isfinite(concat).all())
                row["n_timepoints"] = int(finite_all[0].size)
            else:
                finite_ok = False
                row["n_timepoints"] = 0
            row["finite_ok"] = finite_ok
            row["not_testable"] = not finite_ok
            if not finite_ok:
                row["not_testable_reason"] = "regional_stratified_missing_or_nonfinite"
            rows.append(row)
    return rows


def _rows_regional_9d_sleep(h5_path: Path) -> List[Dict[str, Any]]:
    with h5py.File(h5_path, "r") as handle:
        stage = _sleep_stage_labels(handle)
        if stage is None:
            return []
        if "/regional_mnps" in handle:
            grp = handle["/regional_mnps"]
            uses_new_layout = True
        elif "/regional_stratified_mnps" in handle:
            grp = handle["/regional_stratified_mnps"]
            uses_new_layout = False
        else:
            return []
        base = _base_h5_metadata(h5_path)
        rows: List[Dict[str, Any]] = []
        coord_names = ("m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m")
        for net in grp.keys():
            if net == "time":
                continue
            net_grp = grp[net]
            if uses_new_layout and "stratified" in net_grp:
                arr2d = np.asarray(net_grp["stratified"][:], dtype=float)
                n = min(int(arr2d.shape[0]), int(stage.shape[0]))
                if arr2d.ndim != 2 or n <= 0:
                    continue
                for _, label, idx in _iter_sleep_stage_indices(stage, n):
                    stage_vals = arr2d[idx]
                    row: Dict[str, Any] = _stage_base_metadata(base, label)
                    row["network"] = net
                    row["n_regions"] = int(net_grp.attrs.get("n_regions", 0))
                    row["source_dataset_path"] = f"/regional_mnps/{net}/stratified"
                    row["n_timepoints"] = int(stage_vals.shape[0])
                    for col_idx, key in enumerate(coord_names):
                        if stage_vals.shape[1] <= col_idx:
                            continue
                        stats = _nan_stats(stage_vals[:, col_idx])
                        row[f"{key}_mean"] = stats["mean"]
                        row[f"{key}_median"] = stats["median"]
                        row[f"{key}_std"] = stats["std"]
                    row["finite_ok"] = bool(np.isfinite(stage_vals).all())
                    row["not_testable"] = not row["finite_ok"]
                    rows.append(row)
            elif not uses_new_layout:
                arrays = {
                    key: np.asarray(net_grp[key][:], dtype=float)
                    for key in coord_names
                    if key in net_grp
                }
                if not arrays:
                    continue
                n = min(min(int(arr.shape[0]) for arr in arrays.values()), int(stage.shape[0]))
                for _, label, idx in _iter_sleep_stage_indices(stage, n):
                    row = _stage_base_metadata(base, label)
                    row["network"] = net
                    row["n_regions"] = int(net_grp.attrs.get("n_regions", 0))
                    row["source_dataset_path"] = f"/regional_stratified_mnps/{net}"
                    row["n_timepoints"] = int(idx.size)
                    finite_all: List[np.ndarray] = []
                    for key, arr in arrays.items():
                        stage_vals = arr[:n][idx]
                        stats = _nan_stats(stage_vals)
                        row[f"{key}_mean"] = stats["mean"]
                        row[f"{key}_median"] = stats["median"]
                        row[f"{key}_std"] = stats["std"]
                        finite_all.append(stage_vals)
                    concat = np.concatenate(finite_all) if finite_all else np.array([], dtype=float)
                    row["finite_ok"] = bool(concat.size and np.isfinite(concat).all())
                    row["not_testable"] = not row["finite_ok"]
                    rows.append(row)
    return rows


def _build_adapters_impl(config_path: Path) -> Dict[str, LegacyAnalysisAdapter]:
    cfg = load_dataset_config(config_path)
    global ACTIVE_STAGE_CODE_TO_LABEL, ACTIVE_MIN_STAGE_TIMEPOINTS
    ACTIVE_STAGE_CODE_TO_LABEL = dict(cfg.flags.stage_code_map or SLEEP_STAGE_CODE_TO_LABEL)
    ACTIVE_MIN_STAGE_TIMEPOINTS = int(cfg.flags.min_stage_timepoints or MIN_SLEEP_STAGE_TIMEPOINTS)
    coordinate_contract = cfg.coordinate_contract
    adapters = {
        "global_mnps_3d": LegacyAnalysisAdapter(
            "global_mnps_3d",
            partial(_rows_global_mnps_3d, coordinate_contract=coordinate_contract),
        ),
        "global_mnps_jacobian_3d": LegacyAnalysisAdapter(
            "global_mnps_jacobian_3d",
            partial(_rows_global_mnps_jacobian_3d, coordinate_contract=coordinate_contract),
        ),
        "global_mnps_9d": LegacyAnalysisAdapter(
            "global_mnps_9d",
            partial(_rows_global_mnps_9d, coordinate_contract=coordinate_contract),
        ),
        "global_mnps_jacobian_9d": LegacyAnalysisAdapter(
            "global_mnps_jacobian_9d",
            partial(_rows_global_mnps_jacobian_9d, coordinate_contract=coordinate_contract),
        ),
        "global_mnps_9d_block_jacobian": LegacyAnalysisAdapter(
            "global_mnps_9d_block_jacobian", _rows_regional_block_jacobian
        ),
        "global_mnps_jacobian_9d_block_jacobian": LegacyAnalysisAdapter(
            "global_mnps_jacobian_9d_block_jacobian", _rows_stratified_block_jacobian
        ),
        # Backward-compatible aliases with names that match the actual H5 export surface.
        "regional_mnps_jacobian_3d": LegacyAnalysisAdapter(
            "regional_mnps_jacobian_3d", _rows_regional_mnps_jacobian_3d
        ),
        "regional_mnps_jacobian_9d": LegacyAnalysisAdapter(
            "regional_mnps_jacobian_9d", _rows_stratified_block_jacobian
        ),
        "regional_3d": LegacyAnalysisAdapter("regional_3d", _rows_regional_3d),
        "regional_9d": LegacyAnalysisAdapter("regional_9d", _rows_regional_9d),
        "reachability_cones": LegacyAnalysisAdapter(
            "reachability_cones",
            partial(_rows_reachability_cones, coordinate_contract=coordinate_contract),
        ),
        "regional_reachability_cones_3d": LegacyAnalysisAdapter(
            "regional_reachability_cones_3d", _rows_regional_reachability_cones_3d
        ),
    }
    if cfg.flags.sleep_data_contrast:
        adapters.update(
            {
                "global_mnps_3d": LegacyAnalysisAdapter(
                    "global_mnps_3d",
                    partial(_rows_global_mnps_3d_sleep, coordinate_contract=coordinate_contract),
                ),
                "global_mnps_jacobian_3d": LegacyAnalysisAdapter(
                    "global_mnps_jacobian_3d",
                    partial(_rows_global_mnps_jacobian_3d_sleep, coordinate_contract=coordinate_contract),
                ),
                "global_mnps_9d": LegacyAnalysisAdapter(
                    "global_mnps_9d",
                    partial(_rows_global_mnps_9d_sleep, coordinate_contract=coordinate_contract),
                ),
                "global_mnps_jacobian_9d": LegacyAnalysisAdapter(
                    "global_mnps_jacobian_9d",
                    partial(_rows_global_mnps_jacobian_9d_sleep, coordinate_contract=coordinate_contract),
                ),
                "regional_3d": LegacyAnalysisAdapter("regional_3d", _rows_regional_3d_sleep),
                "regional_9d": LegacyAnalysisAdapter("regional_9d", _rows_regional_9d_sleep),
                "regional_mnps_jacobian_3d": LegacyAnalysisAdapter(
                    "regional_mnps_jacobian_3d", _rows_regional_mnps_jacobian_3d_sleep
                ),
                "reachability_cones": LegacyAnalysisAdapter(
                    "reachability_cones",
                    partial(_rows_reachability_cones_sleep, coordinate_contract=coordinate_contract),
                ),
                "regional_reachability_cones_3d": LegacyAnalysisAdapter(
                    "regional_reachability_cones_3d", _rows_regional_reachability_cones_3d_sleep
                ),
            }
        )
    return adapters


def build_adapters(config_path: Path) -> Dict[str, LegacyAnalysisAdapter]:
    """Deprecated compatibility path for adapter registry.

    Prefer ``nmd_analysis.adapters.build_adapters`` for new code.
    """
    global _LEGACY_ADAPTER_WARNING_EMITTED
    if not _LEGACY_ADAPTER_WARNING_EMITTED:
        warnings.warn(
            "nmd_analysis.legacy_adapters.build_adapters is deprecated; "
            "use nmd_analysis.adapters.build_adapters instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        _LEGACY_ADAPTER_WARNING_EMITTED = True
    return _build_adapters_impl(config_path)
