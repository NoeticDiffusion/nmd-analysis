from __future__ import annotations

from dataclasses import dataclass, replace
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import h5py
import numpy as np

from .h5_contract import (
    GeometryContractState,
    read_geometry_contract_state,
    read_run_contract,
    resolve_coords_3d,
    resolve_coords_9d,
)
from .participant_metadata import derive_medication_metadata, read_json_dataset
from .reachability_core import compute_reachability_cones_from_mnps


@dataclass(frozen=True)
class ReachabilityConfig:
    space: str = "v2"
    k: int = 25
    method: str = "ridge"
    ridge_alpha: float = 1e-3
    cv_folds: int = 5
    super_window_size: int = 3
    jitter: float = 1e-6
    cov_estimator: str = "empirical"
    mnps_dim_cap: Optional[int] = None
    eig_floor_scale: float = 0.0
    standardize: str = "none"
    standardize_eps: float = 1e-6
    sigma0_eps: float = 0.0
    horizon: int = 4
    max_points: int = 2000
    persistence_window: int = 11
    persistence_mode: str = "all"
    persistence_baseline_quantile: float = 0.5
    persistence_low_alpha: float = 0.8
    persistence_recover_alpha: float = 0.9
    persistence_hysteresis_window: int = 11
    agg: str = "median"
    eps: float = 1e-12
    knn_scope: str = "all"
    geometry_gate_9d_enabled: bool = True
    geometry_gate_9d_on_degenerate_axes: bool = True
    geometry_gate_9d_on_zero_retained_jacobian: bool = True


def _to_str(x: Any) -> Optional[str]:
    if x is None:
        return None
    if isinstance(x, (bytes, bytearray, np.bytes_)):
        try:
            return bytes(x).decode("utf-8")
        except Exception:
            return str(x)
    return str(x)


def _summary_stats(arr: np.ndarray) -> Dict[str, float]:
    arr = np.asarray(arr, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {"mean": float("nan"), "std": float("nan"), "median": float("nan"), "iqr": float("nan"), "mad": float("nan")}
    q25, q75 = np.percentile(arr, [25, 75])
    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med)))
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "median": med,
        "iqr": float(q75 - q25),
        "mad": mad,
    }


def _env_bool(name: str) -> Optional[bool]:
    raw = os.getenv(name)
    if raw is None:
        return None
    token = raw.strip().lower()
    if token in {"1", "true", "yes", "on"}:
        return True
    if token in {"0", "false", "no", "off"}:
        return False
    return None


def _apply_env_gate_overrides(cfg: ReachabilityConfig) -> ReachabilityConfig:
    overrides: Dict[str, bool] = {}
    value = _env_bool("NDT_GEOMETRY_GATE_9D_ENABLED")
    if value is not None:
        overrides["geometry_gate_9d_enabled"] = value
    value = _env_bool("NDT_GEOMETRY_GATE_9D_ON_DEGENERATE_AXES")
    if value is not None:
        overrides["geometry_gate_9d_on_degenerate_axes"] = value
    value = _env_bool("NDT_GEOMETRY_GATE_9D_ON_ZERO_RETAINED_JACOBIAN")
    if value is not None:
        overrides["geometry_gate_9d_on_zero_retained_jacobian"] = value
    return replace(cfg, **overrides) if overrides else cfg


def _is_9d_space(space: Optional[str]) -> bool:
    if not space:
        return False
    token = str(space).strip().lower()
    return (
        token in {"9d", "v2", "coords_9d", "coords_v2"}
        or token.startswith("coords_9d")
        or token.startswith("coords_v2")
    )


def _geometry_gate_9d_reason(
    cfg: ReachabilityConfig,
    *,
    used_space: Optional[str],
    geometry_contract: GeometryContractState,
) -> Optional[str]:
    if not cfg.geometry_gate_9d_enabled or not _is_9d_space(used_space):
        return None
    reasons: list[str] = []
    if cfg.geometry_gate_9d_on_degenerate_axes and geometry_contract.has_coords_9d_degenerate_axes():
        axes = ",".join(geometry_contract.coords_9d_degenerate_axes)
        reasons.append(f"coords_9d_degenerate_axes={axes}")
    if cfg.geometry_gate_9d_on_zero_retained_jacobian and geometry_contract.has_zero_retained_jacobian_9d():
        reasons.append("jacobian_9d_windows_retained<=0")
    if not reasons:
        return None
    return "; ".join(reasons)


def _expected_reachability_flat_metric_columns(cfg: ReachabilityConfig) -> list[str]:
    cols: list[str] = []
    tube_keys = (
        "tube_log_det",
        "tube_kappa",
        "tube_log_eig_var",
        "tube_d_eff",
        "tube_dir_entropy",
        "tube_dir_entropy_norm",
        "tube_rotation",
        "tube_q_ratio_h4",
        "tube_a_operator_norm",
        "tube_capture_gate",
        "cone_kappa",
    )
    for key in tube_keys:
        cols.append(f"{key}_median")
        cols.append(f"{key}_mean")
    for key in ("log_det", "kappa", "log_eig_var", "d_eff", "dir_entropy", "dir_entropy_norm", "q_ratio"):
        for h in range(1, int(cfg.horizon) + 1):
            cols.append(f"cone_{key}_h{h}_median")
            if key == "q_ratio":
                cols.append(f"q_ratio_h{h}_median")
    for key in (
        "persistence_log_det",
        "persistence_kappa",
        "persistence_log_eig_var",
        "persistence_d_eff",
        "persistence_tau_log_det",
        "persistence_tau_kappa",
        "persistence_tau_log_eig_var",
        "persistence_tau_d_eff",
        "persistence_hysteresis_log_det",
        "persistence_hysteresis_kappa",
        "persistence_hysteresis_log_eig_var",
        "persistence_hysteresis_d_eff",
    ):
        cols.append(f"{key}_median")
    for h in range(1, int(cfg.horizon) + 1):
        cols.append(f"pred_err_h{h}")
    cols.extend(
        [
            "near_singular_rate",
            "tube_log_det_split_half_a_median",
            "tube_log_det_split_half_b_median",
            "tube_log_det_split_half_rho",
            "tube_log_det_split_half_n",
            "tube_d_eff_split_half_a_median",
            "tube_d_eff_split_half_b_median",
            "tube_d_eff_split_half_rho",
            "tube_d_eff_split_half_n",
            "median_cond",
            "median_min_eig_over_median_eig",
        ]
    )
    return cols


def _build_not_testable_summary(
    *,
    cfg: ReachabilityConfig,
    h5_path: Path,
    metadata: Dict[str, Any],
    source_dataset_path: str,
    reason: str,
    x: np.ndarray,
) -> Dict[str, Any]:
    flat: Dict[str, Any] = {
        "dataset_id": metadata.get("dataset_id"),
        "subject_id": metadata.get("subject_id"),
        "group": metadata.get("group"),
        "medication_group": metadata.get("medication_group"),
        "cpz_at_scan": metadata.get("cpz_at_scan"),
        "condition": metadata.get("condition"),
        "task": metadata.get("task"),
        "session": metadata.get("session"),
        "run": metadata.get("run"),
        "acq": metadata.get("acq"),
        "source_h5_path": metadata.get("source_h5_path"),
        "space": metadata.get("space"),
        "source_dataset_path": source_dataset_path,
        "requested_coordinate_contract": metadata.get("requested_coordinate_contract"),
        "resolved_coordinate_contract": metadata.get("resolved_coordinate_contract"),
        "primary_coordinate_contract": metadata.get("primary_coordinate_contract"),
        "primary_coordinate_layer": metadata.get("primary_coordinate_layer"),
        "anchor_id": metadata.get("anchor_id"),
        "anchor_hash": metadata.get("anchor_hash"),
        "anchor_source": metadata.get("anchor_source"),
        "schema_version": metadata.get("schema_version"),
        "mndm_version": metadata.get("mndm_version"),
        "geometry_contract_status": metadata.get("geometry_contract_status"),
        "geometry_invalidity_policy": metadata.get("geometry_invalidity_policy"),
        "geometry_coords_9d_degenerate_axes": metadata.get("geometry_coords_9d_degenerate_axes"),
        "geometry_coords_9d_degenerate_axes_n": metadata.get("geometry_coords_9d_degenerate_axes_n"),
        "geometry_jacobian_9d_windows_retained": metadata.get("geometry_jacobian_9d_windows_retained"),
        "geometry_jacobian_9d_invalid_windows": metadata.get("geometry_jacobian_9d_invalid_windows"),
        "geometry_gate_9d_triggered": True,
        "geometry_gate_9d_reason": reason,
        "n_timepoints": int(x.shape[0]),
        "dims": int(x.shape[1]),
        "k": cfg.k,
        "horizon": cfg.horizon,
        "finite_ok": False,
        "not_testable": True,
        "not_testable_reason": f"reachability_9d_geometry_gate:{reason}",
    }
    for key in _expected_reachability_flat_metric_columns(cfg):
        flat[key] = np.nan
    return {
        "path": str(h5_path),
        "dataset_id": metadata.get("dataset_id"),
        "subject_id": metadata.get("subject_id"),
        "group": metadata.get("group"),
        "condition": metadata.get("condition"),
        "task": metadata.get("task"),
        "space": metadata.get("space"),
        "source_dataset_path": source_dataset_path,
        "metrics": {},
        "diagnostics": {"valid_windows": 0, "windows": 0},
        "flat": flat,
    }


def _resolve_x_from_h5(
    f: h5py.File,
    space: str,
    *,
    coordinate_contract: str,
) -> tuple[np.ndarray, str, str, Dict[str, Any]]:
    if space in {"v2", "9d"}:
        resolved_9d = resolve_coords_9d(f, coordinate_contract)
        if resolved_9d is not None:
            return (
                resolved_9d.values,
                resolved_9d.values_path.strip("/").replace("/values", ""),
                resolved_9d.values_path,
                resolved_9d.provenance(),
            )
    resolved_3d = resolve_coords_3d(f, coordinate_contract)
    if resolved_3d is not None:
        return (
            resolved_3d.values,
            resolved_3d.values_path.strip("/").replace("/values", ""),
            resolved_3d.values_path,
            resolved_3d.provenance(),
        )
    raise ValueError("No suitable state-space found in H5 (/coords_9d/values, /coords_v2/values, /mnps_3d, or /x).")


def _space_to_dataset_path(space: str) -> str:
    mapping = {
        "coords_9d": "/coords_9d/values",
        "coords_v2": "/coords_v2/values",
        "mnps_3d": "/mnps_3d",
        "x": "/x",
    }
    return mapping.get(space, space)


def _resolve_time(time: Optional[np.ndarray], fs_out: Optional[float], n: int) -> np.ndarray:
    if time is not None and isinstance(time, np.ndarray) and time.size >= 2:
        dt = np.median(np.diff(time))
        if np.isfinite(dt) and dt > 0:
            return time.astype(float)
    if fs_out is not None and np.isfinite(fs_out) and fs_out > 0:
        dt = 1.0 / float(fs_out)
        return np.arange(n, dtype=float) * dt
    return np.arange(n, dtype=float)


def _downsample(x: np.ndarray, time: np.ndarray, max_points: int) -> tuple[np.ndarray, np.ndarray]:
    if max_points is None or max_points <= 0 or x.shape[0] <= max_points:
        return x, time
    stride = int(np.ceil(x.shape[0] / max_points))
    idx = np.arange(0, x.shape[0], stride, dtype=int)
    return x[idx], time[idx]


def _read_participant_mapped_json(handle: h5py.File) -> Dict[str, Any]:
    """Read participant/mapped_json (new standard) from an open H5 file.

    Returns an empty dict if absent or unparseable.
    """
    return read_json_dataset(handle, "participant/mapped_json")


def _pick_meta(
    mapped: Dict[str, Any],
    attrs: Dict[str, Any],
    key: str,
    *fallback_attr_keys: str,
) -> Optional[str]:
    """Prefer participant/mapped_json value; fall back to H5 root attrs."""
    v = mapped.get(key)
    if v is not None and str(v).strip():
        return _to_str(v)
    for fk in (key,) + fallback_attr_keys:
        v = attrs.get(fk)
        if v is not None:
            return _to_str(v)
    return None


def _load_h5_reachability_context(
    h5_path: Path,
) -> tuple[Dict[str, Any], Optional[np.ndarray], Optional[float], GeometryContractState]:
    with h5py.File(h5_path, "r") as f:
        attrs = dict(f.attrs.items())
        mapped = _read_participant_mapped_json(f)
        row_json = read_json_dataset(f, "participant/row_json")
        run_contract = read_run_contract(f)
        geometry_contract = read_geometry_contract_state(f)
        group_value = _pick_meta(mapped, attrs, "group", "meta_type", "type")
        metadata = {
            "dataset_id": _to_str(attrs.get("dataset_id")) or h5_path.parent.name,
            "subject_id": _to_str(attrs.get("subject_id")) or h5_path.stem,
            "group": group_value,
            "condition": _pick_meta(mapped, attrs, "condition"),
            "task": _pick_meta(mapped, attrs, "task"),
            "session": _to_str(attrs.get("session")),
            "run": _to_str(attrs.get("run")),
            "acq": _to_str(attrs.get("acq")),
            "source_h5_path": str(h5_path),
        }
        metadata.update(derive_medication_metadata(group_value, row_json))
        metadata.update(run_contract.provenance())
        metadata.update(geometry_contract.provenance())
        fs_out_raw = attrs.get("fs_out")
        fs_out = float(fs_out_raw) if isinstance(fs_out_raw, (int, float, np.number)) else None
        time_raw = f["/time"][:] if "/time" in f else None
    return metadata, time_raw, fs_out, geometry_contract


def _summarize_reachability_array(
    x: np.ndarray,
    time: np.ndarray,
    cfg: ReachabilityConfig,
    *,
    h5_path: Path,
    metadata: Dict[str, Any],
    source_dataset_path: str,
) -> Dict[str, Any]:
    x, time = _downsample(x, time, cfg.max_points)
    alpha_grid = [cfg.ridge_alpha]
    results = compute_reachability_cones_from_mnps(
        x=x,
        time=time,
        k=cfg.k,
        super_window_size=cfg.super_window_size,
        method=cfg.method,
        alpha_grid=alpha_grid,
        cv_folds=cfg.cv_folds,
        horizon=cfg.horizon,
        sigma0=cfg.sigma0_eps,
        jitter=cfg.jitter,
        agg=cfg.agg,
        cov_estimator=cfg.cov_estimator,
        eig_floor_scale=cfg.eig_floor_scale,
        persistence_window=cfg.persistence_window,
        persistence_mode=cfg.persistence_mode,
        persistence_baseline_quantile=cfg.persistence_baseline_quantile,
        persistence_low_alpha=cfg.persistence_low_alpha,
        persistence_recover_alpha=cfg.persistence_recover_alpha,
        persistence_hysteresis_window=cfg.persistence_hysteresis_window,
        eps=cfg.eps,
        knn_scope=cfg.knn_scope,
    )

    metrics_by_h = results["metrics_by_h"]
    tube_metrics = results["tube_metrics"]
    persistence = results["persistence"]
    flat: Dict[str, Any] = {
        "dataset_id": metadata.get("dataset_id"),
        "subject_id": metadata.get("subject_id"),
        "group": metadata.get("group"),
        "medication_group": metadata.get("medication_group"),
        "cpz_at_scan": metadata.get("cpz_at_scan"),
        "condition": metadata.get("condition"),
        "task": metadata.get("task"),
        "session": metadata.get("session"),
        "run": metadata.get("run"),
        "acq": metadata.get("acq"),
        "source_h5_path": metadata.get("source_h5_path"),
        "space": metadata.get("space"),
        "source_dataset_path": source_dataset_path,
        "requested_coordinate_contract": metadata.get("requested_coordinate_contract"),
        "resolved_coordinate_contract": metadata.get("resolved_coordinate_contract"),
        "primary_coordinate_contract": metadata.get("primary_coordinate_contract"),
        "primary_coordinate_layer": metadata.get("primary_coordinate_layer"),
        "anchor_id": metadata.get("anchor_id"),
        "anchor_hash": metadata.get("anchor_hash"),
        "anchor_source": metadata.get("anchor_source"),
        "schema_version": metadata.get("schema_version"),
        "mndm_version": metadata.get("mndm_version"),
        "geometry_contract_status": metadata.get("geometry_contract_status"),
        "geometry_invalidity_policy": metadata.get("geometry_invalidity_policy"),
        "geometry_coords_9d_degenerate_axes": metadata.get("geometry_coords_9d_degenerate_axes"),
        "geometry_coords_9d_degenerate_axes_n": metadata.get("geometry_coords_9d_degenerate_axes_n"),
        "geometry_jacobian_9d_windows_retained": metadata.get("geometry_jacobian_9d_windows_retained"),
        "geometry_jacobian_9d_invalid_windows": metadata.get("geometry_jacobian_9d_invalid_windows"),
        "geometry_gate_9d_triggered": False,
        "geometry_gate_9d_reason": None,
        "n_timepoints": int(x.shape[0]),
        "dims": int(x.shape[1]),
        "k": cfg.k,
        "horizon": cfg.horizon,
        "finite_ok": bool(np.isfinite(x).all()),
        "not_testable": False,
    }

    for key, arr in tube_metrics.items():
        stats = _summary_stats(np.asarray(arr, dtype=float))
        flat[f"{key}_median"] = stats["median"]
        flat[f"{key}_mean"] = stats["mean"]
    for key, arr in persistence.items():
        stats = _summary_stats(np.asarray(arr, dtype=float))
        flat[f"{key}_median"] = stats["median"]
    for key, arr in metrics_by_h.items():
        vals = np.asarray(arr, dtype=float)
        if vals.ndim == 2:
            for h in range(vals.shape[1]):
                stats = _summary_stats(vals[:, h])
                flat[f"cone_{key}_h{h+1}_median"] = stats["median"]
                if key == "q_ratio":
                    flat[f"q_ratio_h{h+1}_median"] = stats["median"]
        else:
            stats = _summary_stats(vals)
            flat[f"cone_{key}_median"] = stats["median"]

    validity = results.get("validity", {})
    if isinstance(validity, dict):
        for key, value in validity.items():
            flat[key] = value

    return {
        "path": str(h5_path),
        "dataset_id": metadata.get("dataset_id"),
        "subject_id": metadata.get("subject_id"),
        "group": metadata.get("group"),
        "condition": metadata.get("condition"),
        "task": metadata.get("task"),
        "space": metadata.get("space"),
        "source_dataset_path": source_dataset_path,
        "metrics": {k: _summary_stats(np.asarray(v, dtype=float)) for k, v in tube_metrics.items()},
        "diagnostics": {
            "valid_windows": int(np.isfinite(np.asarray(tube_metrics.get("tube_log_det", []))).sum()),
            "windows": int(np.asarray(results.get("A_hat", [])).shape[0]) if "A_hat" in results else 0,
        },
        "flat": flat,
    }


def summarize_reachability_h5(
    h5_path: Path,
    config: ReachabilityConfig | None = None,
    *,
    coordinate_contract: str = "cohort_anchored",
    sample_indices: np.ndarray | None = None,
    condition_override: str | None = None,
    dataset_id_suffix: str | None = None,
    dataset_path: str | None = None,
    used_space_override: str | None = None,
    metadata_overrides: Dict[str, Any] | None = None,
    flat_overrides: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    cfg = config or ReachabilityConfig()
    cfg = _apply_env_gate_overrides(cfg)
    h5_path = Path(h5_path)
    metadata, time_raw, fs_out, geometry_contract = _load_h5_reachability_context(h5_path)
    with h5py.File(h5_path, "r") as f:
        if dataset_path is None:
            x, used_space, source_dataset_path, provenance = _resolve_x_from_h5(
                f,
                cfg.space,
                coordinate_contract=coordinate_contract,
            )
            metadata.update(provenance)
        else:
            if dataset_path not in f:
                raise ValueError(f"Dataset path not found in H5: {dataset_path}")
            x = np.asarray(f[dataset_path][:], dtype=float)
            used_space = used_space_override or dataset_path.strip("/")
            source_dataset_path = dataset_path

    time = _resolve_time(time_raw, fs_out, x.shape[0])
    if sample_indices is not None:
        idx = np.asarray(sample_indices, dtype=int).ravel()
        idx = idx[(idx >= 0) & (idx < x.shape[0])]
        if idx.size == 0:
            raise ValueError("sample_indices resolved to an empty selection.")
        x = x[idx]
        time = time[idx]
    metadata["space"] = used_space
    if metadata_overrides:
        metadata.update(metadata_overrides)
    if dataset_id_suffix and metadata.get("dataset_id"):
        metadata["dataset_id"] = f"{metadata['dataset_id']}{dataset_id_suffix}"
    if condition_override is not None:
        metadata["condition"] = condition_override
    gate_reason = _geometry_gate_9d_reason(
        cfg,
        used_space=used_space,
        geometry_contract=geometry_contract,
    )
    if gate_reason is not None:
        summary = _build_not_testable_summary(
            cfg=cfg,
            h5_path=h5_path,
            metadata=metadata,
            source_dataset_path=source_dataset_path,
            reason=gate_reason,
            x=x,
        )
    else:
        summary = _summarize_reachability_array(
            x,
            time,
            cfg,
            h5_path=h5_path,
            metadata=metadata,
            source_dataset_path=source_dataset_path,
        )
    if flat_overrides:
        summary["flat"].update(flat_overrides)
    return summary


def collect_subject_csv_rows(summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [s["flat"] for s in summaries]
