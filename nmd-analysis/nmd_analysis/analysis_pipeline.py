from __future__ import annotations

import json
import math
import re
from itertools import product
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import h5py
import numpy as np
import pandas as pd

from .analysis_config import (
    AnalysisBlockConfig,
    AnalysisConfig,
    ContrastConfig,
    NegativeControlConfig,
    load_analysis_config,
)
from .h5_contract import read_run_contract, resolve_coords_3d, resolve_jacobian_3d
from .io_tables import read_parquet_table, write_parquet_frame
from .naming import build_output_filename
from .participant_metadata import derive_medication_metadata, read_json_dataset
from .propofol_depth import annotate_propofol_depth

PACKAGE_ROOT = Path(__file__).resolve().parents[2]

IDENTITY_COLUMNS = {
    "dataset_id",
    "subject_id",
    "session",
    "run",
    "task",
    "condition",
    "group",
    "medication_group",
    "modality",
    "acq",
}
CONTEXT_COLUMNS = [
    "network",
    "space",
    "block_scope",
    "block_space",
    "source_group",
    "target_group",
    "source_dim",
    "target_dim",
    "feature_name",
    "base_feature_name",
    "region_group",
    "feature_group_label",
    "feature_source_column",
    "feature_alignment",
    "feature_export_transform",
    "feature_contract_version",
    "feature_order_hash",
    "feature_backend",
    "feature_fallback_reason",
    "feature_projection_normalize_mode",
    "feature_projection_transform_applied",
    "feature_projection_transform_steps",
    "feature_degraded_mode",
    "feature_is_regional",
    "feature_used_anywhere",
    "feature_used_by_coords_9d",
    "feature_used_by_mnps_3d",
    "feature_used_by_regional_projection",
]
PROVENANCE_COLUMNS = {
    "analysis_type",
    "source_h5_path",
    "source_dataset_path",
    "trajectory_source_dataset_path",
    "jacobian_source_dataset_path",
    "source_file",
    "source_analysis_type",
    "block_export_kind",
    "requested_coordinate_contract",
    "resolved_coordinate_contract",
    "primary_coordinate_contract",
    "primary_coordinate_layer",
    "anchor_id",
    "anchor_hash",
    "anchor_source",
    "schema_version",
    "mndm_version",
}
QC_FLAG_COLUMNS = {
    "finite_ok",
    "not_testable",
    "not_testable_reason",
    "validity_limited",
    "validity_limited_reason",
}
META_NUMERIC_COLUMNS = {
    "dims",
    "horizon",
    "k",
    "n_regions",
    "n_timepoints",
    "n_windows",
    "in_dim",
    "out_dim",
    "source_dim",
    "target_dim",
    "feature_index",
    "feature_n_finite",
    "n_features",
    "feature_raw_abs_mad",
    "feature_raw_abs_median",
    "feature_robust_z_center",
    "feature_robust_z_scale",
    "cpz_at_scan",
}
MANIFEST_BLOCKS = {
    "tier2_emmi",
    "dist_summary",
    "tier2_jacobian",
    "tau_summary",
    "robust_summary",
}
FEATURE_BLOCKS = {
    "features_raw": "/features_raw",
    "features_robust_z": "/features_robust_z",
    "features_raw_sleep": "/features_raw",
    "features_robust_z_sleep": "/features_robust_z",
}
CUSTOM_H5_BUILDERS: Dict[str, Any] = {}
SLEEP_STAGE_CODE_TO_LABEL = {
    0: "awake",
    2: "nrem2",
    3: "nrem3",
    4: "rem",
}
MIN_SLEEP_STAGE_TIMEPOINTS = 20
MIN_TRAJECTORY_DYNAMIC_POINTS = 5


def _parse_cleaned_analysis_type(path: Path, dataset: str) -> Optional[str]:
    pattern = rf"^{re.escape(dataset)}_(.+)_\d{{8}}_\d{{6}}\.parquet$"
    match = re.match(pattern, path.name)
    if not match:
        return None
    return match.group(1)


def _discover_latest_cleaned_files(cleaned_root: Path, dataset: str) -> Dict[str, Path]:
    latest: Dict[str, Path] = {}
    def _priority(path: Path) -> tuple[int, int]:
        path_text = str(path).lower().replace("\\", "/")
        if "stage_port_full" in path_text:
            return (0, 0)
        if "stage_port_contract" in path_text and "contract_nc" not in path_text:
            return (1, 0)
        if "stage_port_smoke" in path_text:
            return (2, 0)
        if "stage_port_contract_nc" in path_text:
            return (3, 0)
        return (4, 0)

    for path in cleaned_root.rglob(f"{dataset}_*.parquet"):
        analysis_type = _parse_cleaned_analysis_type(path, dataset)
        if not analysis_type:
            continue
        prev = latest.get(analysis_type)
        if prev is None:
            latest[analysis_type] = path
            continue
        prev_key = (_priority(prev), -prev.stat().st_mtime_ns)
        path_key = (_priority(path), -path.stat().st_mtime_ns)
        if path_key <= prev_key:
            latest[analysis_type] = path
    return latest


def _resolve_source_h5_path(raw_path: Any) -> Optional[Path]:
    if raw_path is None:
        return None
    candidate = Path(str(raw_path))
    if candidate.exists():
        return candidate.resolve()
    if not candidate.is_absolute():
        cwd_candidate = Path.cwd() / candidate
        if cwd_candidate.exists():
            return cwd_candidate.resolve()
    parts = list(candidate.parts)
    suffix_options: List[Path] = []
    for idx in range(max(0, len(parts) - 1)):
        if str(parts[idx]).lower() == "data" and idx + 1 < len(parts) and str(parts[idx + 1]).lower() == "raw":
            suffix_options.append(Path(*parts[idx + 2 :]))
        if str(parts[idx]).startswith("neuralmanifolddynamics_"):
            suffix_options.append(Path(*parts[idx:]))
    raw_root_hints = [
        PACKAGE_ROOT / "data" / "raw",
        Path.cwd() / "data" / "raw",
        Path.cwd().parent / "data" / "raw",
    ]
    for raw_root in raw_root_hints:
        if not raw_root.exists():
            continue
        for suffix in suffix_options:
            remapped = raw_root / suffix
            if remapped.exists():
                return remapped.resolve()
        matches = list(raw_root.glob(f"**/{candidate.name}"))
        if len(matches) == 1 and matches[0].exists():
            return matches[0].resolve()
    return None


def _sleep_stage_labels(handle: h5py.File) -> Optional[np.ndarray]:
    if "/labels/stage" not in handle:
        return None
    stage = np.asarray(handle["/labels/stage"][:], dtype=int).reshape(-1)
    return stage if stage.size else None


def _iter_sleep_stage_indices(
    stage: Optional[np.ndarray],
    n_samples: int,
    *,
    stage_code_map: Optional[Dict[int, str]] = None,
    min_points: int = MIN_SLEEP_STAGE_TIMEPOINTS,
) -> List[Tuple[int, str, np.ndarray]]:
    if stage is None or n_samples <= 0:
        return []
    usable = np.asarray(stage[:n_samples], dtype=int).reshape(-1)
    out: List[Tuple[int, str, np.ndarray]] = []
    active_map = stage_code_map or SLEEP_STAGE_CODE_TO_LABEL
    for code, label in active_map.items():
        idx = np.flatnonzero(usable == int(code))
        if idx.size >= int(min_points):
            out.append((int(code), label, idx))
    return out


def _stage_base_metadata(base: Dict[str, Any], label: str) -> Dict[str, Any]:
    row = dict(base)
    if row.get("dataset_id"):
        row["dataset_id"] = f"{row['dataset_id']}:stage_{label}"
    row["condition"] = label
    row["stage"] = label
    return row


def _resolve_time_and_dt(handle: h5py.File, n_samples: int) -> Tuple[np.ndarray, float]:
    if "/time" in handle:
        time = np.asarray(handle["/time"][:], dtype=float).reshape(-1)
        if time.size >= n_samples:
            time = time[:n_samples]
            diff = np.diff(time)
            finite = diff[np.isfinite(diff) & (diff > 0)]
            if finite.size:
                dt = float(np.median(finite))
                return time, dt
    return np.arange(n_samples, dtype=float), 1.0


def _contiguous_segments(idx: np.ndarray) -> List[np.ndarray]:
    if idx.size == 0:
        return []
    values = np.unique(np.asarray(idx, dtype=int))
    breaks = np.where(np.diff(values) != 1)[0]
    starts = np.r_[0, breaks + 1]
    ends = np.r_[breaks + 1, values.size]
    return [values[start:end] for start, end in zip(starts, ends)]


def _segmentwise_speed(coords: np.ndarray, segments: Sequence[np.ndarray]) -> np.ndarray:
    chunks: List[np.ndarray] = []
    for seg in segments:
        if seg.size < 2:
            continue
        diff = np.diff(coords[seg], axis=0)
        chunks.append(np.linalg.norm(diff, axis=1))
    return np.concatenate(chunks) if chunks else np.zeros((0,), dtype=float)


def _segmentwise_curvature(coords: np.ndarray, segments: Sequence[np.ndarray]) -> np.ndarray:
    chunks: List[np.ndarray] = []
    for seg in segments:
        if seg.size < 3:
            continue
        window = coords[seg]
        v1 = np.diff(window, axis=0)[:-1]
        v2 = np.diff(window, axis=0)[1:]
        denom = np.linalg.norm(v1, axis=1) * np.linalg.norm(v2, axis=1) + 1e-12
        cosang = np.clip(np.sum(v1 * v2, axis=1) / denom, -1.0, 1.0)
        chunks.append(np.arccos(cosang))
    return np.concatenate(chunks) if chunks else np.zeros((0,), dtype=float)


def _segmentwise_path_length(coords: np.ndarray, segments: Sequence[np.ndarray]) -> float:
    total = 0.0
    for seg in segments:
        if seg.size < 2:
            continue
        diff = np.diff(coords[seg], axis=0)
        step_norm = np.linalg.norm(diff, axis=1)
        if step_norm.size:
            total += float(np.nansum(step_norm))
    return total


def _segmentwise_endpoint_dist(coords: np.ndarray, segments: Sequence[np.ndarray]) -> float:
    total = 0.0
    for seg in segments:
        if seg.size < 2:
            continue
        endpoints = np.asarray(coords[seg[[0, -1]]], dtype=float)
        if endpoints.shape != (2, coords.shape[1]) or not np.isfinite(endpoints).all():
            continue
        total += float(np.linalg.norm(endpoints[1] - endpoints[0]))
    return total


def _trajectory_efficiency(endpoint_dist: float, path_length: float) -> float:
    if not np.isfinite(endpoint_dist) or not np.isfinite(path_length) or path_length <= 0:
        return float("nan")
    ratio = endpoint_dist / path_length
    return float(np.clip(ratio, 0.0, 1.0))


def _robust_median_iqr(values: np.ndarray) -> Tuple[float, Tuple[float, float]]:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return float("nan"), (float("nan"), float("nan"))
    return float(np.median(arr)), (float(np.percentile(arr, 25)), float(np.percentile(arr, 75)))


def _robust_mad(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return float("nan")
    med = float(np.median(arr))
    return float(np.median(np.abs(arr - med)))


def _autocorr_tau_sec(values: np.ndarray, dt_sec: float, threshold: float = 1.0 / math.e) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size < 5 or not np.isfinite(dt_sec) or dt_sec <= 0:
        return float("nan")
    arr = arr - float(np.mean(arr))
    denom = float(np.dot(arr, arr))
    if denom <= 0:
        return float("nan")
    max_lag = max(1, min(arr.size - 1, int(round(300.0 / dt_sec))))
    for lag in range(1, max_lag + 1):
        acf = float(np.dot(arr[:-lag], arr[lag:]) / denom)
        if np.isfinite(acf) and acf < threshold:
            return float(lag * dt_sec)
    return float(max_lag * dt_sec)


def _condition_number_stats(J: np.ndarray) -> Dict[str, float]:
    if not isinstance(J, np.ndarray) or J.ndim != 3 or J.shape[0] == 0:
        return {"median": float("nan"), "iqr": float("nan"), "mad": float("nan")}
    values: List[float] = []
    for idx in range(J.shape[0]):
        matrix = np.asarray(J[idx], dtype=float)
        if not np.isfinite(matrix).all():
            continue
        try:
            singular = np.linalg.svd(matrix, compute_uv=False)
        except Exception:
            continue
        smax = float(np.max(singular))
        smin = float(np.min(singular))
        if not np.isfinite(smax) or not np.isfinite(smin) or smin <= 0:
            continue
        values.append(smax / smin)
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {"median": float("nan"), "iqr": float("nan"), "mad": float("nan")}
    q25, q75 = np.percentile(arr, [25, 75])
    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med)))
    return {"median": med, "iqr": float(q75 - q25), "mad": mad}


def _rotation_coherence_mrl(J: np.ndarray) -> float:
    if not isinstance(J, np.ndarray) or J.ndim != 3 or J.shape[0] == 0 or J.shape[1:] != (3, 3):
        return float("nan")
    axes: List[np.ndarray] = []
    for idx in range(J.shape[0]):
        matrix = np.asarray(J[idx], dtype=float)
        if not np.isfinite(matrix).all():
            continue
        omega = 0.5 * (matrix - matrix.T)
        axis = np.array([omega[2, 1], omega[0, 2], omega[1, 0]], dtype=float)
        norm = float(np.linalg.norm(axis))
        if np.isfinite(norm) and norm > 0:
            axes.append(axis / norm)
    if not axes:
        return float("nan")
    mean_axis = np.mean(np.stack(axes, axis=0), axis=0)
    return float(np.linalg.norm(mean_axis))


def _corner_codes(coords: np.ndarray, thr_low: np.ndarray, thr_high: np.ndarray) -> np.ndarray:
    high = np.asarray(coords, dtype=float) >= np.asarray(thr_high, dtype=float)
    return (high[:, 0].astype(int) << 2) | (high[:, 1].astype(int) << 1) | high[:, 2].astype(int)


def _occupancy_entropy(codes: np.ndarray) -> float:
    counts = np.bincount(np.asarray(codes, dtype=int), minlength=8).astype(float)
    total = float(np.sum(counts))
    if total <= 0:
        return float("nan")
    probs = np.clip(counts / total, 1e-12, 1.0)
    probs = probs / probs.sum()
    return float(-np.sum(probs * np.log(probs)))


def _canonicalize_stage_label(label: Any) -> Optional[str]:
    if label is None:
        return None
    text = str(label).strip().lower()
    if not text:
        return None
    aliases = {
        "awake": "awake",
        "wake": "awake",
        "w": "awake",
        "n1": "n1",
        "nrem2": "nrem2",
        "n2": "nrem2",
        "nrem3": "nrem3",
        "n3": "nrem3",
        "rem": "rem",
        "r": "rem",
        "unresponsive": "unresponsive",
        "recovery": "recovery",
        "pre_lor": "awake",
        "post_ror": "recovery",
    }
    return aliases.get(text, text)


def _coerce_stage_code(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        pass
    try:
        text = str(value).strip()
        if not text:
            return None
        return int(float(text))
    except (TypeError, ValueError):
        return None


def _parse_stage_code_map_candidate(candidate: Any) -> Dict[int, str]:
    parsed = candidate
    if isinstance(parsed, (bytes, bytearray, np.bytes_)):
        try:
            parsed = bytes(parsed).decode("utf-8")
        except Exception:
            parsed = str(parsed)
    if isinstance(parsed, str):
        try:
            parsed = json.loads(parsed)
        except Exception:
            return {}

    out: Dict[int, str] = {}
    if isinstance(parsed, dict):
        for raw_key, raw_value in parsed.items():
            key_code = _coerce_stage_code(raw_key)
            value_label = _canonicalize_stage_label(raw_value)
            if key_code is not None and value_label is not None:
                out[int(key_code)] = value_label

            value_code = _coerce_stage_code(raw_value)
            key_label = _canonicalize_stage_label(raw_key)
            if value_code is not None and key_label is not None:
                out[int(value_code)] = key_label
        return out

    if isinstance(parsed, list):
        for item in parsed:
            if not isinstance(item, dict):
                continue
            raw_code = (
                item.get("code")
                if item.get("code") is not None
                else item.get("stage_code")
                if item.get("stage_code") is not None
                else item.get("value")
                if item.get("value") is not None
                else item.get("id")
            )
            raw_label = (
                item.get("label")
                if item.get("label") is not None
                else item.get("stage_label")
                if item.get("stage_label") is not None
                else item.get("label_key")
                if item.get("label_key") is not None
                else item.get("name")
                if item.get("name") is not None
                else item.get("key")
            )
            code = _coerce_stage_code(raw_code)
            label = _canonicalize_stage_label(raw_label)
            if code is not None and label is not None:
                out[int(code)] = label
    return out


def _read_stage_code_map_from_codebooks(handle: h5py.File) -> Dict[int, str]:
    if "/codebooks/stage/codes" not in handle:
        return {}
    label_path = None
    for candidate in ("/codebooks/stage/labels", "/codebooks/stage/label_keys"):
        if candidate in handle:
            label_path = candidate
            break
    if label_path is None:
        return {}
    codes = np.asarray(handle["/codebooks/stage/codes"][:]).reshape(-1)
    labels = np.asarray(handle[label_path][:]).reshape(-1)
    if codes.size == 0 or labels.size == 0 or codes.size != labels.size:
        return {}
    out: Dict[int, str] = {}
    for raw_code, raw_label in zip(codes.tolist(), labels.tolist()):
        code = _coerce_stage_code(_to_python_scalar(raw_code))
        label = _canonicalize_stage_label(_to_python_scalar(raw_label))
        if code is not None and label is not None:
            out[int(code)] = label
    return out


def _handle_stage_code_map(handle: h5py.File) -> Dict[int, str]:
    codebook_map = _read_stage_code_map_from_codebooks(handle)
    if codebook_map:
        return codebook_map

    candidates: List[Any] = [
        handle.attrs.get("stage_codebook"),
    ]
    try:
        if "/manifest_json" in handle:
            raw_value = handle["/manifest_json"][()]
            text = bytes(raw_value).decode("utf-8") if isinstance(raw_value, (bytes, bytearray, np.bytes_)) else str(raw_value)
            manifest = json.loads(text)
            candidates.extend(
                [
                    ((manifest.get("stage_codes") or {}).get("codebook")),
                    ((manifest.get("within_run_labels") or {}).get("stage_codebook")),
                    manifest.get("stage_codebook"),
                ]
            )
    except Exception:
        pass

    for candidate in candidates:
        out = _parse_stage_code_map_candidate(candidate)
        if out:
            return out
    return dict(SLEEP_STAGE_CODE_TO_LABEL)


def _iter_handle_stage_indices(
    handle: h5py.File,
    n_samples: int,
    *,
    stage_code_map: Optional[Dict[int, str]] = None,
    min_points: int = MIN_TRAJECTORY_DYNAMIC_POINTS,
) -> List[Tuple[int, str, np.ndarray]]:
    stage = _sleep_stage_labels(handle)
    if stage is None or n_samples <= 0:
        return []
    usable = np.asarray(stage[:n_samples], dtype=int).reshape(-1)
    code_map = stage_code_map or _handle_stage_code_map(handle)
    out: List[Tuple[int, str, np.ndarray]] = []
    for code, label in code_map.items():
        idx = np.flatnonzero(usable == int(code))
        if idx.size >= int(min_points):
            out.append((int(code), label, idx))
    return out


def _trajectory_dynamics_row(
    analysis_type: str,
    coords: np.ndarray,
    base_row: Dict[str, Any],
    source_dataset_path: str,
    sample_idx: np.ndarray,
    thr_low: np.ndarray,
    thr_high: np.ndarray,
    *,
    stage: Optional[np.ndarray] = None,
    jacobian: Optional[np.ndarray] = None,
    jacobian_centers: Optional[np.ndarray] = None,
    dt: float = 1.0,
    label: Optional[str] = None,
    stage_code: Optional[int] = None,
    min_points: int = MIN_TRAJECTORY_DYNAMIC_POINTS,
) -> Optional[Dict[str, Any]]:
    n_samples = coords.shape[0]
    if stage is not None:
        n_samples = min(n_samples, int(stage.shape[0]))
    coords = coords[:n_samples]
    sample_idx = np.asarray(sample_idx, dtype=int)
    if sample_idx.size < int(min_points):
        return None
    stage_coords = coords[sample_idx]
    segments = _contiguous_segments(sample_idx)
    speed_values = _segmentwise_speed(coords, segments)
    curvature_values = _segmentwise_curvature(coords, segments)
    path_length = _segmentwise_path_length(coords, segments)
    endpoint_dist = _segmentwise_endpoint_dist(coords, segments)
    traj_efficiency = _trajectory_efficiency(endpoint_dist, path_length)
    speed_median, speed_iqr = _robust_median_iqr(speed_values)
    curv_median, curv_iqr = _robust_median_iqr(curvature_values)
    corner_codes = _corner_codes(stage_coords, thr_low=thr_low, thr_high=thr_high)
    corners_entropy = _occupancy_entropy(corner_codes)
    dwell_entropy = float("nan")
    transition_entropy = float("nan")
    if corner_codes.size:
        dwell_totals = np.zeros((8,), dtype=float)
        run_starts = np.r_[0, np.where(np.diff(corner_codes) != 0)[0] + 1]
        run_ends = np.r_[run_starts[1:], corner_codes.size]
        for start, end in zip(run_starts, run_ends):
            code = int(corner_codes[start])
            if 0 <= code < 8:
                dwell_totals[code] += float(end - start)
        if dwell_totals.sum() > 0:
            probs = np.clip(dwell_totals / dwell_totals.sum(), 1e-12, 1.0)
            probs = probs / probs.sum()
            dwell_entropy = float(-np.sum(probs * np.log(probs)))
    if corner_codes.size >= 2:
        left = corner_codes[:-1]
        right = corner_codes[1:]
        valid = (left >= 0) & (left < 8) & (right >= 0) & (right < 8)
        if np.any(valid):
            counts = np.zeros((8, 8), dtype=float)
            for src, dst in zip(left[valid].tolist(), right[valid].tolist()):
                counts[int(src), int(dst)] += 1.0
            total = float(np.sum(counts))
            if total > 0:
                probs = np.clip(counts.reshape(-1) / total, 1e-12, 1.0)
                probs = probs / probs.sum()
                transition_entropy = float(-np.sum(probs * np.log(probs)))

    kappa = {"median": float("nan"), "iqr": float("nan"), "mad": float("nan")}
    rot_mrl = float("nan")
    if jacobian is not None and jacobian_centers is not None:
        centers = np.asarray(jacobian_centers[: jacobian.shape[0]], dtype=int).reshape(-1)
        keep = (centers >= 0) & (centers < n_samples)
        if label is not None and stage is not None:
            keep = keep & (stage[centers] == int(stage_code))
        j_stage = jacobian[: centers.shape[0]][keep]
        kappa = _condition_number_stats(j_stage)
        rot_mrl = _rotation_coherence_mrl(j_stage)

    base = dict(base_row)
    if label is not None:
        base = _stage_base_metadata(base, label)
        base["stage_code"] = int(stage_code) if stage_code is not None else None
    base["source_dataset_path"] = f"/derived/{analysis_type}"
    base["trajectory_source_dataset_path"] = source_dataset_path
    base["n_timepoints"] = int(sample_idx.size)
    base["finite_ok"] = bool(np.isfinite(stage_coords).all())
    base["not_testable"] = bool(sample_idx.size < int(min_points) or speed_values.size < 1)
    base["not_testable_reason"] = "lt_min_timepoints_or_no_speed" if base["not_testable"] else None
    base["validity_limited"] = False
    base["validity_limited_reason"] = None
    base["speed_mean"] = float(np.mean(speed_values)) if speed_values.size else float("nan")
    base["speed_median"] = speed_median
    base["speed_iqr"] = float(speed_iqr[1] - speed_iqr[0]) if np.isfinite(speed_iqr[0]) and np.isfinite(speed_iqr[1]) else float("nan")
    base["speed_mad"] = _robust_mad(speed_values)
    base["curvature_median"] = curv_median
    base["curvature_iqr"] = float(curv_iqr[1] - curv_iqr[0]) if np.isfinite(curv_iqr[0]) and np.isfinite(curv_iqr[1]) else float("nan")
    base["curvature_mad"] = _robust_mad(curvature_values)
    base["path_length"] = path_length
    base["endpoint_dist"] = endpoint_dist
    base["traj_efficiency"] = traj_efficiency
    base["corner_entropy"] = corners_entropy
    base["corner_dwell_entropy"] = dwell_entropy
    base["corner_transition_entropy"] = transition_entropy
    base["m_tau_sec"] = _autocorr_tau_sec(stage_coords[:, 0], dt)
    base["d_tau_sec"] = _autocorr_tau_sec(stage_coords[:, 1], dt)
    base["e_tau_sec"] = _autocorr_tau_sec(stage_coords[:, 2], dt)
    base["m_delta_mean_median"] = float(np.nanmean(stage_coords[:, 0]) - np.nanmedian(stage_coords[:, 0]))
    base["d_delta_mean_median"] = float(np.nanmean(stage_coords[:, 1]) - np.nanmedian(stage_coords[:, 1]))
    base["e_delta_mean_median"] = float(np.nanmean(stage_coords[:, 2]) - np.nanmedian(stage_coords[:, 2]))
    base["tier2_jacobian_condition_number_median"] = kappa["median"]
    base["tier2_jacobian_condition_number_iqr"] = kappa["iqr"]
    base["tier2_jacobian_condition_number_mad"] = kappa["mad"]
    base["tier2_jacobian_rotation_coherence_mrl"] = rot_mrl
    return base


def _sleep_stage_dynamics_row(
    label: str,
    coords: np.ndarray,
    base_row: Dict[str, Any],
    source_dataset_path: str,
    sample_idx: np.ndarray,
    thr_low: np.ndarray,
    thr_high: np.ndarray,
    *,
    stage_code: Optional[int],
    stage: np.ndarray,
    jacobian: Optional[np.ndarray] = None,
    jacobian_centers: Optional[np.ndarray] = None,
    dt: float = 1.0,
) -> Optional[Dict[str, Any]]:
    n_samples = min(coords.shape[0], int(stage.shape[0]))
    coords = coords[:n_samples]
    sample_idx = np.asarray(sample_idx, dtype=int)
    if sample_idx.size < MIN_SLEEP_STAGE_TIMEPOINTS:
        return None
    stage_coords = coords[sample_idx]
    segments = _contiguous_segments(sample_idx)
    speed_values = _segmentwise_speed(coords, segments)
    curvature_values = _segmentwise_curvature(coords, segments)
    path_length = _segmentwise_path_length(coords, segments)
    endpoint_dist = _segmentwise_endpoint_dist(coords, segments)
    traj_efficiency = _trajectory_efficiency(endpoint_dist, path_length)
    speed_median, speed_iqr = _robust_median_iqr(speed_values)
    curv_median, curv_iqr = _robust_median_iqr(curvature_values)
    corner_codes = _corner_codes(stage_coords, thr_low=thr_low, thr_high=thr_high)
    corners_entropy = _occupancy_entropy(corner_codes)
    dwell_entropy = float("nan")
    transition_entropy = float("nan")
    if corner_codes.size:
        dwell_totals = np.zeros((8,), dtype=float)
        run_starts = np.r_[0, np.where(np.diff(corner_codes) != 0)[0] + 1]
        run_ends = np.r_[run_starts[1:], corner_codes.size]
        for start, end in zip(run_starts, run_ends):
            code = int(corner_codes[start])
            if 0 <= code < 8:
                dwell_totals[code] += float(end - start)
        if dwell_totals.sum() > 0:
            probs = np.clip(dwell_totals / dwell_totals.sum(), 1e-12, 1.0)
            probs = probs / probs.sum()
            dwell_entropy = float(-np.sum(probs * np.log(probs)))
    if corner_codes.size >= 2:
        left = corner_codes[:-1]
        right = corner_codes[1:]
        valid = (left >= 0) & (left < 8) & (right >= 0) & (right < 8)
        if np.any(valid):
            counts = np.zeros((8, 8), dtype=float)
            for src, dst in zip(left[valid].tolist(), right[valid].tolist()):
                counts[int(src), int(dst)] += 1.0
            trans_total = float(np.sum(counts))
            if trans_total > 0:
                probs = np.clip(counts.reshape(-1) / trans_total, 1e-12, 1.0)
                probs = probs / probs.sum()
                transition_entropy = float(-np.sum(probs * np.log(probs)))
    kappa = {"median": float("nan"), "iqr": float("nan"), "mad": float("nan")}
    rot_mrl = float("nan")
    if jacobian is not None and jacobian_centers is not None:
        centers = np.asarray(jacobian_centers[: jacobian.shape[0]], dtype=int).reshape(-1)
        keep = (centers >= 0) & (centers < n_samples)
        if stage_code is not None:
            keep = keep & (stage[centers] == int(stage_code))
        j_stage = jacobian[: centers.shape[0]][keep]
        kappa = _condition_number_stats(j_stage)
        rot_mrl = _rotation_coherence_mrl(j_stage)

    base = _stage_base_metadata(dict(base_row), label)
    base["stage_code"] = int(stage_code) if stage_code is not None else None
    base["source_dataset_path"] = "/derived/sleep_stage_dynamics"
    base["trajectory_source_dataset_path"] = source_dataset_path
    base["n_timepoints"] = int(sample_idx.size)
    base["finite_ok"] = bool(np.isfinite(stage_coords).all())
    base["not_testable"] = bool(sample_idx.size < MIN_SLEEP_STAGE_TIMEPOINTS or speed_values.size < 1)
    base["not_testable_reason"] = "lt_min_stage_timepoints_or_no_speed" if base["not_testable"] else None
    base["validity_limited"] = False
    base["validity_limited_reason"] = None
    base["speed_mean"] = float(np.mean(speed_values)) if speed_values.size else float("nan")
    base["speed_median"] = speed_median
    base["speed_iqr"] = float(speed_iqr[1] - speed_iqr[0]) if np.isfinite(speed_iqr[0]) and np.isfinite(speed_iqr[1]) else float("nan")
    base["speed_mad"] = _robust_mad(speed_values)
    base["curvature_median"] = curv_median
    base["curvature_iqr"] = float(curv_iqr[1] - curv_iqr[0]) if np.isfinite(curv_iqr[0]) and np.isfinite(curv_iqr[1]) else float("nan")
    base["curvature_mad"] = _robust_mad(curvature_values)
    base["path_length"] = path_length
    base["endpoint_dist"] = endpoint_dist
    base["traj_efficiency"] = traj_efficiency
    base["corner_entropy"] = corners_entropy
    base["corner_dwell_entropy"] = dwell_entropy
    base["corner_transition_entropy"] = transition_entropy
    base["m_tau_sec"] = _autocorr_tau_sec(stage_coords[:, 0], dt)
    base["d_tau_sec"] = _autocorr_tau_sec(stage_coords[:, 1], dt)
    base["e_tau_sec"] = _autocorr_tau_sec(stage_coords[:, 2], dt)
    base["m_delta_mean_median"] = float(np.nanmean(stage_coords[:, 0]) - np.nanmedian(stage_coords[:, 0]))
    base["d_delta_mean_median"] = float(np.nanmean(stage_coords[:, 1]) - np.nanmedian(stage_coords[:, 1]))
    base["e_delta_mean_median"] = float(np.nanmean(stage_coords[:, 2]) - np.nanmedian(stage_coords[:, 2]))
    base["tier2_jacobian_condition_number_median"] = kappa["median"]
    base["tier2_jacobian_condition_number_iqr"] = kappa["iqr"]
    base["tier2_jacobian_condition_number_mad"] = kappa["mad"]
    base["tier2_jacobian_rotation_coherence_mrl"] = rot_mrl
    return base


def _build_sleep_stage_dynamics_frame(h5_paths: Sequence[Path], coordinate_contract: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for h5_path in h5_paths:
        with h5py.File(h5_path, "r") as handle:
            resolved_coords = resolve_coords_3d(handle, coordinate_contract)
            if resolved_coords is None or "/labels/stage" not in handle:
                continue
            coords = np.asarray(resolved_coords.values, dtype=float)
            n_samples = min(coords.shape[0], int(handle["/labels/stage"].shape[0]))
            coords = coords[:n_samples]
            finite_mask = np.isfinite(coords).all(axis=1)
            finite_coords = coords[finite_mask]
            if finite_coords.shape[0] < MIN_SLEEP_STAGE_TIMEPOINTS:
                continue
            thr_low = np.nanpercentile(finite_coords, 40, axis=0).astype(float)
            thr_high = np.nanpercentile(finite_coords, 60, axis=0).astype(float)
            stage = _sleep_stage_labels(handle)
            if stage is None:
                continue
            stage = stage[:n_samples]
            stage_code_map = _handle_stage_code_map(handle)
            _, dt = _resolve_time_and_dt(handle, n_samples)
            resolved_jacobian = resolve_jacobian_3d(handle, coordinate_contract)
            base = _base_h5_metadata_from_handle(handle, h5_path)
            base.update(resolved_coords.provenance())
            if resolved_jacobian is not None:
                base.update(resolved_jacobian.provenance())
                base["jacobian_source_dataset_path"] = resolved_jacobian.dataset_path
            for code, label, sample_idx in _iter_sleep_stage_indices(
                stage,
                n_samples,
                stage_code_map=stage_code_map,
            ):
                keep_idx = sample_idx[finite_mask[sample_idx]]
                row = _sleep_stage_dynamics_row(
                    label,
                    coords,
                    base,
                    resolved_coords.values_path,
                    keep_idx,
                    thr_low,
                    thr_high,
                    stage_code=code,
                    stage=stage,
                    jacobian=resolved_jacobian.j_hat if resolved_jacobian is not None else None,
                    jacobian_centers=resolved_jacobian.centers if resolved_jacobian is not None else None,
                    dt=dt,
                )
                if row is not None:
                    rows.append(row)
    return pd.DataFrame(rows)


CUSTOM_H5_BUILDERS["sleep_stage_dynamics"] = _build_sleep_stage_dynamics_frame


def _build_trajectory_dynamics_frame(h5_paths: Sequence[Path], coordinate_contract: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for h5_path in h5_paths:
        with h5py.File(h5_path, "r") as handle:
            resolved_coords = resolve_coords_3d(handle, coordinate_contract)
            if resolved_coords is None:
                continue
            coords = np.asarray(resolved_coords.values, dtype=float)
            n_samples = coords.shape[0]
            if "/labels/stage" in handle:
                n_samples = min(n_samples, int(handle["/labels/stage"].shape[0]))
            coords = coords[:n_samples]
            finite_mask = np.isfinite(coords).all(axis=1)
            finite_coords = coords[finite_mask]
            if finite_coords.shape[0] < MIN_TRAJECTORY_DYNAMIC_POINTS:
                continue
            thr_low = np.nanpercentile(finite_coords, 40, axis=0).astype(float)
            thr_high = np.nanpercentile(finite_coords, 60, axis=0).astype(float)
            stage = _sleep_stage_labels(handle)
            if stage is not None:
                stage = stage[:n_samples]
            stage_code_map = _handle_stage_code_map(handle)
            _, dt = _resolve_time_and_dt(handle, n_samples)
            resolved_jacobian = resolve_jacobian_3d(handle, coordinate_contract)
            base = _base_h5_metadata_from_handle(handle, h5_path)
            base.update(resolved_coords.provenance())
            if resolved_jacobian is not None:
                base.update(resolved_jacobian.provenance())
                base["jacobian_source_dataset_path"] = resolved_jacobian.dataset_path
            stage_slices = _iter_handle_stage_indices(
                handle,
                n_samples,
                stage_code_map=stage_code_map,
                min_points=MIN_TRAJECTORY_DYNAMIC_POINTS,
            )
            if stage_slices:
                for code, label, sample_idx in stage_slices:
                    keep_idx = sample_idx[finite_mask[sample_idx]]
                    row = _trajectory_dynamics_row(
                        "trajectory_dynamics",
                        coords,
                        base,
                        resolved_coords.values_path,
                        keep_idx,
                        thr_low,
                        thr_high,
                        stage=stage,
                        jacobian=resolved_jacobian.j_hat if resolved_jacobian is not None else None,
                        jacobian_centers=resolved_jacobian.centers if resolved_jacobian is not None else None,
                        dt=dt,
                        label=label,
                        stage_code=code,
                        min_points=MIN_TRAJECTORY_DYNAMIC_POINTS,
                    )
                    if row is not None:
                        rows.append(row)
                continue

            sample_idx = np.flatnonzero(finite_mask)
            row = _trajectory_dynamics_row(
                "trajectory_dynamics",
                coords,
                base,
                resolved_coords.values_path,
                sample_idx,
                thr_low,
                thr_high,
                stage=stage,
                jacobian=resolved_jacobian.j_hat if resolved_jacobian is not None else None,
                jacobian_centers=resolved_jacobian.centers if resolved_jacobian is not None else None,
                dt=dt,
                min_points=MIN_TRAJECTORY_DYNAMIC_POINTS,
            )
            if row is not None:
                rows.append(row)
    return pd.DataFrame(rows)


CUSTOM_H5_BUILDERS["trajectory_dynamics"] = _build_trajectory_dynamics_frame


def _build_eeg_classical_comparators_frame(h5_paths: Sequence[Path], coordinate_contract: str) -> pd.DataFrame:
    from .eeg_classical_comparators import build_eeg_classical_comparators_frame

    return build_eeg_classical_comparators_frame(
        h5_paths,
        coordinate_contract=coordinate_contract,
        base_metadata_builder=_base_h5_metadata_from_handle,
    )


CUSTOM_H5_BUILDERS["eeg_classical_comparators"] = _build_eeg_classical_comparators_frame


def _read_source_h5_catalog(latest_files: Dict[str, Path]) -> List[Path]:
    seen: Dict[str, Path] = {}
    for parquet_path in latest_files.values():
        frame = read_parquet_table(parquet_path)
        if "source_h5_path" not in frame.columns:
            continue
        for raw_path in frame["source_h5_path"].dropna().unique().tolist():
            resolved = _resolve_source_h5_path(raw_path)
            if resolved is not None:
                seen[str(resolved)] = resolved
    return sorted(seen.values())


def _metric_role(metric: str) -> str:
    qc_prefixes = ("pred_err_", "split_half_", "near_singular_", "jacobian_cond")
    qc_exact = {
        "n_regions",
        "n_timepoints",
        "n_windows",
        "dims",
        "horizon",
        "k",
    }
    if metric in qc_exact or metric.endswith("_finite_frac") or metric.startswith(qc_prefixes):
        return "qc"
    return "signal"


def _metric_family(metric: str) -> str:
    if metric.startswith("tube_") or metric.startswith("cone_") or metric.startswith("persistence_"):
        return "reachability"
    if "block_" in metric:
        return "block"
    if any(token in metric for token in ("trace", "rotation", "frobenius", "spectral", "anisotropy")):
        return "jacobian"
    if any(
        token in metric
        for token in (
            "speed",
            "curvature",
            "corner_",
            "path_length",
            "endpoint_dist",
            "efficiency",
            "_tau_sec",
            "_delta_mean_median",
        )
    ):
        return "trajectory"
    return metric.split("_", 1)[0]


def _is_metric_column(frame: pd.DataFrame, column: str) -> bool:
    if column in IDENTITY_COLUMNS or column in PROVENANCE_COLUMNS or column in QC_FLAG_COLUMNS:
        return False
    if column in CONTEXT_COLUMNS or column in META_NUMERIC_COLUMNS:
        return False
    if pd.api.types.is_bool_dtype(frame[column]):
        return False
    return pd.api.types.is_numeric_dtype(frame[column])


def _to_optional_bool(value: Any, default: Optional[bool]) -> Optional[bool]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return default
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    return bool(value)


def _to_optional_float(value: Any) -> float:
    if value is None:
        return float("nan")
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return out


def _mean_boolish(series: pd.Series, default: bool) -> float:
    if series.empty:
        return float("nan")
    values = series.map(lambda value: _to_optional_bool(value, default))
    return float(values.fillna(default).astype(bool).mean())


def _flatten_scalar_tree(prefix: str, value: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if isinstance(value, dict):
        for key, inner in value.items():
            child_prefix = f"{prefix}_{key}" if prefix else str(key)
            out.update(_flatten_scalar_tree(child_prefix, inner))
        return out
    if isinstance(value, list):
        for idx, inner in enumerate(value):
            child_prefix = f"{prefix}_{idx}"
            out.update(_flatten_scalar_tree(child_prefix, inner))
        return out
    out[prefix] = value
    return out


def _to_python_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        try:
            return bytes(value).decode("utf-8")
        except Exception:
            return str(value)
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return _to_python_scalar(value.item())
        return [_to_python_scalar(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _to_feature_bool(value: Any) -> Optional[bool]:
    scalar = _to_python_scalar(value)
    if scalar is None or (isinstance(scalar, float) and math.isnan(scalar)):
        return None
    if isinstance(scalar, bool):
        return scalar
    if isinstance(scalar, (int, float)):
        return bool(int(scalar))
    text = str(scalar).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off", ""}:
        return False
    return bool(text)


def _to_feature_float(value: Any) -> float:
    scalar = _to_python_scalar(value)
    if scalar is None:
        return float("nan")
    try:
        return float(scalar)
    except (TypeError, ValueError):
        return float("nan")


def _parse_feature_name_parts(feature_name: str, metadata: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    text = str(feature_name)
    match = re.match(r"^(?P<base>.+?)__g_(?P<region>.+)$", text)
    if match:
        return match.group("base"), match.group("region")
    group_label = _to_python_scalar(metadata.get("group_label"))
    if group_label:
        return text, str(group_label)
    return text, None


def _base_h5_metadata_from_handle(handle: h5py.File, h5_path: Path) -> Dict[str, Any]:
    attrs = dict(handle.attrs.items())

    def _to_str_or_none(value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, (bytes, bytearray, np.bytes_)):
            try:
                return bytes(value).decode("utf-8")
            except Exception:
                return str(value)
        return str(value)

    # New standard: prefer participant/mapped_json for condition/task/group.
    # Fall back to root attrs for datasets that pre-date this convention.
    _mapped: Dict[str, Any] = read_json_dataset(handle, "participant/mapped_json")
    row_json: Dict[str, Any] = read_json_dataset(handle, "participant/row_json")

    def _pick(key: str, *fallback_attr_keys: str) -> Optional[str]:
        v = _mapped.get(key)
        if v is not None and str(v).strip():
            return _to_str_or_none(v)
        for fk in (key,) + fallback_attr_keys:
            v = attrs.get(fk)
            if v is not None:
                return _to_str_or_none(v)
        return None

    group_value = _pick("group", "meta_type", "type")
    base = {
        "dataset_id": _to_str_or_none(attrs.get("dataset_id")),
        "subject_id": _to_str_or_none(attrs.get("subject_id")),
        "session": _to_str_or_none(attrs.get("session")),
        "run": _to_str_or_none(attrs.get("run") or "run-01"),
        "acq": _to_str_or_none(attrs.get("acq")),
        "group": group_value,
        "condition": _pick("condition"),
        "task": _pick("task"),
        "modality": _to_str_or_none(attrs.get("modality")),
        "source_h5_path": str(h5_path),
        "source_dataset_path": "/manifest_json",
    }
    base.update(derive_medication_metadata(group_value, row_json))
    base.update(read_run_contract(handle).provenance())
    return base


def _load_manifest_json(h5_path: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    with h5py.File(h5_path, "r") as handle:
        base = _base_h5_metadata_from_handle(handle, h5_path)
        if "/manifest_json" in handle:
            raw_value = handle["/manifest_json"][()]
            if isinstance(raw_value, (bytes, bytearray, np.bytes_)):
                text = bytes(raw_value).decode("utf-8")
            else:
                text = str(raw_value)
        else:
            attr_value = handle.attrs.get("manifest")
            if attr_value is None:
                raise KeyError(f"No manifest_json or manifest attr in {h5_path}")
            if isinstance(attr_value, (bytes, bytearray, np.bytes_)):
                text = bytes(attr_value).decode("utf-8")
            else:
                text = str(attr_value)
    return base, json.loads(text)


def _read_feature_metadata_rows(metadata_group: h5py.Group, n_features: int) -> List[Dict[str, Any]]:
    if n_features <= 0:
        return []
    columns: Dict[str, List[Any]] = {}
    for key, dataset in metadata_group.items():
        values = np.asarray(dataset[:])
        flat = values.reshape(-1).tolist()
        if len(flat) == 1 and n_features > 1:
            flat = flat * n_features
        if len(flat) != n_features:
            raise ValueError(
                f"Feature metadata column {key} has length {len(flat)} but expected {n_features}."
            )
        columns[key] = [_to_python_scalar(item) for item in flat]
    rows: List[Dict[str, Any]] = []
    for idx in range(n_features):
        rows.append({key: values[idx] for key, values in columns.items()})
    return rows


def _feature_summary_row(
    base: Dict[str, Any],
    feature_block_path: str,
    feature_name: str,
    feature_index: int,
    values: np.ndarray,
    attrs: Dict[str, Any],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    arr = np.asarray(values, dtype=float)
    finite = arr[np.isfinite(arr)]
    n_timepoints = int(arr.size)
    feature_n_finite = int(finite.size)
    finite_frac = float(feature_n_finite / n_timepoints) if n_timepoints else float("nan")
    base_feature_name, region_group = _parse_feature_name_parts(feature_name, metadata)

    row = dict(base)
    row.update(
        {
            "feature_mean": float(np.mean(finite)) if feature_n_finite else float("nan"),
            "feature_median": float(np.median(finite)) if feature_n_finite else float("nan"),
            "feature_std": float(np.std(finite, ddof=1)) if feature_n_finite >= 2 else float("nan"),
            "feature_iqr": float(np.quantile(finite, 0.75) - np.quantile(finite, 0.25))
            if feature_n_finite
            else float("nan"),
            "feature_mad": float(np.median(np.abs(finite - np.median(finite)))) if feature_n_finite else float("nan"),
            "feature_min": float(np.min(finite)) if feature_n_finite else float("nan"),
            "feature_max": float(np.max(finite)) if feature_n_finite else float("nan"),
            "feature_p05": float(np.quantile(finite, 0.05)) if feature_n_finite else float("nan"),
            "feature_p95": float(np.quantile(finite, 0.95)) if feature_n_finite else float("nan"),
            "feature_finite_frac": finite_frac,
        }
    )
    row["source_dataset_path"] = feature_block_path
    row["feature_name"] = feature_name
    row["base_feature_name"] = base_feature_name
    row["region_group"] = region_group
    row["feature_index"] = int(feature_index)
    row["feature_n_finite"] = feature_n_finite
    row["n_timepoints"] = n_timepoints
    row["n_features"] = _to_feature_float(attrs.get("n_features"))
    row["feature_alignment"] = _to_python_scalar(attrs.get("alignment"))
    row["feature_export_transform"] = _to_python_scalar(attrs.get("export_transform"))
    row["feature_contract_version"] = _to_python_scalar(attrs.get("feature_contract_version"))
    row["feature_order_hash"] = _to_python_scalar(attrs.get("feature_order_hash"))
    row["feature_group_label"] = _to_python_scalar(metadata.get("group_label"))
    row["feature_source_column"] = _to_python_scalar(metadata.get("source_column"))
    row["feature_backend"] = _to_python_scalar(metadata.get("backend"))
    row["feature_fallback_reason"] = _to_python_scalar(metadata.get("fallback_reason"))
    row["feature_projection_normalize_mode"] = _to_python_scalar(metadata.get("projection_normalize_mode"))
    row["feature_projection_transform_applied"] = _to_python_scalar(metadata.get("projection_transform_applied"))
    row["feature_projection_transform_steps"] = _to_python_scalar(metadata.get("projection_transform_steps"))
    row["feature_degraded_mode"] = _to_feature_bool(metadata.get("degraded_mode"))
    row["feature_is_regional"] = _to_feature_bool(metadata.get("is_regional"))
    row["feature_used_anywhere"] = _to_feature_bool(metadata.get("used_anywhere"))
    row["feature_used_by_coords_9d"] = _to_feature_bool(metadata.get("used_by_coords_9d"))
    row["feature_used_by_mnps_3d"] = _to_feature_bool(metadata.get("used_by_mnps_3d"))
    row["feature_used_by_regional_projection"] = _to_feature_bool(metadata.get("used_by_regional_projection"))
    row["feature_raw_abs_mad"] = _to_feature_float(metadata.get("raw_abs_mad"))
    row["feature_raw_abs_median"] = _to_feature_float(metadata.get("raw_abs_median"))
    row["feature_robust_z_center"] = _to_feature_float(metadata.get("robust_z_center"))
    row["feature_robust_z_scale"] = _to_feature_float(metadata.get("robust_z_scale"))
    row["finite_ok"] = bool(feature_n_finite == n_timepoints and n_timepoints > 0)
    row["not_testable"] = bool(feature_n_finite < 3)
    row["not_testable_reason"] = "lt3_finite_timepoints" if row["not_testable"] else None
    return row


def _build_feature_block_frame(analysis_type: str, h5_paths: Sequence[Path]) -> pd.DataFrame:
    feature_block_path = FEATURE_BLOCKS[analysis_type]
    sleep_stage_split = analysis_type.endswith("_sleep")
    rows: List[Dict[str, Any]] = []
    for h5_path in h5_paths:
        with h5py.File(h5_path, "r") as handle:
            if feature_block_path not in handle:
                continue
            group = handle[feature_block_path]
            values = np.asarray(group["values"][:], dtype=float)
            if values.ndim != 2:
                raise ValueError(f"{feature_block_path} values must be 2D, got shape {values.shape}.")
            names = [_to_python_scalar(item) for item in np.asarray(group["names"][:]).reshape(-1).tolist()]
            n_timepoints, n_features = values.shape
            if len(names) != n_features:
                raise ValueError(f"{feature_block_path} names length {len(names)} does not match values shape {values.shape}.")
            metadata_rows = _read_feature_metadata_rows(group["metadata"], n_features)
            attrs = {key: _to_python_scalar(value) for key, value in group.attrs.items()}
            base = _base_h5_metadata_from_handle(handle, h5_path)
            stage_slices: List[Tuple[Dict[str, Any], np.ndarray]]
            if sleep_stage_split:
                stage = _sleep_stage_labels(handle)
                finite_mask = np.isfinite(values).all(axis=1)
                stage_code_map = _handle_stage_code_map(handle)
                stage_slices = []
                for _, label, sample_idx in _iter_sleep_stage_indices(
                    stage,
                    n_timepoints,
                    stage_code_map=stage_code_map,
                ):
                    keep_idx = sample_idx[finite_mask[sample_idx]]
                    if keep_idx.size < MIN_SLEEP_STAGE_TIMEPOINTS:
                        continue
                    stage_slices.append((_stage_base_metadata(base, label), keep_idx))
                if not stage_slices:
                    continue
            else:
                stage_slices = [(base, np.arange(n_timepoints, dtype=int))]

            for stage_base, sample_idx in stage_slices:
                for idx, feature_name in enumerate(names):
                    rows.append(
                        _feature_summary_row(
                            base=stage_base,
                            feature_block_path=feature_block_path,
                            feature_name=str(feature_name),
                            feature_index=idx,
                            values=values[sample_idx, idx],
                            attrs=attrs,
                            metadata=metadata_rows[idx],
                        )
                    )
    return pd.DataFrame(rows)


def _manifest_block_row_tier2_emmi(base: Dict[str, Any], manifest: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    block = manifest.get("tier2_emmi")
    if not isinstance(block, dict):
        return None
    row = dict(base)
    row.update(_flatten_scalar_tree("", block))
    return row


def _manifest_block_row_dist_summary(base: Dict[str, Any], manifest: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    block = manifest.get("dist_summary")
    if not isinstance(block, dict):
        return None
    row = dict(base)
    for family_key in ("axes", "subcoords"):
        family = block.get(family_key)
        if not isinstance(family, dict):
            continue
        for name, stats in family.items():
            if not isinstance(stats, dict):
                continue
            for stat_name, stat_value in stats.items():
                row[f"{name}_{stat_name}"] = stat_value
    return row


def _manifest_block_row_tier2_jacobian(base: Dict[str, Any], manifest: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    block = manifest.get("tier2_jacobian")
    if not isinstance(block, dict):
        return None
    row = dict(base)
    for section_name, section_value in block.items():
        row.update(_flatten_scalar_tree(section_name, section_value))
    return row


def _manifest_block_row_tau_summary(base: Dict[str, Any], manifest: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    block = manifest.get("tau_summary")
    if not isinstance(block, dict):
        return None
    row = dict(base)
    for family_key in ("axes", "subcoords"):
        family = block.get(family_key)
        if not isinstance(family, dict):
            continue
        for name, stats in family.items():
            if not isinstance(stats, dict):
                continue
            for stat_name, stat_value in stats.items():
                row[f"{name}_{stat_name}"] = stat_value
    return row


def _manifest_block_row_robust_summary(base: Dict[str, Any], manifest: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    block = manifest.get("robust_summary")
    if not isinstance(block, dict):
        return None
    row = dict(base)
    for family_key in ("axes", "subcoords"):
        family = block.get(family_key)
        if not isinstance(family, dict):
            continue
        summary = family.get("summary")
        if isinstance(summary, dict):
            for name, stats in summary.items():
                if not isinstance(stats, dict):
                    continue
                for stat_name, stat_value in stats.items():
                    row[f"{name}_{stat_name}"] = stat_value
        reliability = family.get("reliability")
        if isinstance(reliability, dict):
            for name, value in reliability.items():
                row[f"{name}_reliability"] = value
    return row


MANIFEST_BUILDERS = {
    "tier2_emmi": _manifest_block_row_tier2_emmi,
    "dist_summary": _manifest_block_row_dist_summary,
    "tier2_jacobian": _manifest_block_row_tier2_jacobian,
    "tau_summary": _manifest_block_row_tau_summary,
    "robust_summary": _manifest_block_row_robust_summary,
}


def _build_manifest_block_frame(analysis_type: str, h5_paths: Sequence[Path]) -> pd.DataFrame:
    builder = MANIFEST_BUILDERS[analysis_type]
    rows: List[Dict[str, Any]] = []
    for h5_path in h5_paths:
        base, manifest = _load_manifest_json(h5_path)
        row = builder(base, manifest)
        if row is None:
            continue
        row["finite_ok"] = True
        row["not_testable"] = False
        rows.append(row)
    return pd.DataFrame(rows)


def _apply_validity_rules(frame: pd.DataFrame, block_cfg: Optional[AnalysisBlockConfig]) -> pd.DataFrame:
    if frame.empty:
        out = frame.copy()
        out["validity_limited"] = False
        out["validity_limited_reason"] = None
        return out

    out = frame.copy()
    if block_cfg is None:
        out["validity_limited"] = False
        out["validity_limited_reason"] = None
        return out

    has_rules = any(
        [
            block_cfg.validity_min,
            block_cfg.validity_max,
            block_cfg.validity_require_true,
            block_cfg.validity_require_false,
            block_cfg.validity_require_nonnull,
        ]
    )
    if not has_rules:
        out["validity_limited"] = False
        out["validity_limited_reason"] = None
        return out

    limited_flags: List[bool] = []
    limited_reasons: List[Optional[str]] = []
    for _, row in out.iterrows():
        reasons: List[str] = []

        for column, threshold in block_cfg.validity_min.items():
            if column not in row.index:
                reasons.append(f"{column}_missing")
                continue
            value = _to_optional_float(row.get(column))
            if not np.isfinite(value):
                reasons.append(f"{column}_nonfinite")
            elif value < threshold:
                reasons.append(f"{column}_lt_{threshold:g}")

        for column, threshold in block_cfg.validity_max.items():
            if column not in row.index:
                reasons.append(f"{column}_missing")
                continue
            value = _to_optional_float(row.get(column))
            if not np.isfinite(value):
                reasons.append(f"{column}_nonfinite")
            elif value > threshold:
                reasons.append(f"{column}_gt_{threshold:g}")

        for column in block_cfg.validity_require_true:
            if column not in row.index:
                reasons.append(f"{column}_missing")
                continue
            value = _to_optional_bool(row.get(column), False)
            if not bool(value):
                reasons.append(f"{column}_false")

        for column in block_cfg.validity_require_false:
            if column not in row.index:
                reasons.append(f"{column}_missing")
                continue
            value = _to_optional_bool(row.get(column), True)
            if bool(value):
                reasons.append(f"{column}_true")

        for column in block_cfg.validity_require_nonnull:
            if column not in row.index:
                reasons.append(f"{column}_missing")
                continue
            value = row.get(column)
            if value is None or (isinstance(value, float) and math.isnan(value)):
                reasons.append(f"{column}_null")

        limited_flags.append(bool(reasons))
        limited_reasons.append(";".join(reasons) if reasons else None)

    out["validity_limited"] = limited_flags
    out["validity_limited_reason"] = limited_reasons
    return out


def _prepare_subject_metrics_frame(
    analysis_type: str,
    frame: pd.DataFrame,
    source_file: Path,
) -> pd.DataFrame:
    metric_columns = [column for column in frame.columns if _is_metric_column(frame, column)]
    rows: List[Dict[str, Any]] = []
    for _, wide_row in frame.iterrows():
        base: Dict[str, Any] = {
            "analysis_type": analysis_type,
            "source_analysis_type": analysis_type,
            "source_file": str(source_file),
        }
        for column in IDENTITY_COLUMNS | PROVENANCE_COLUMNS | QC_FLAG_COLUMNS | set(CONTEXT_COLUMNS) | META_NUMERIC_COLUMNS:
            if column in wide_row.index:
                base[column] = wide_row[column]
        for metric in metric_columns:
            row = dict(base)
            row["metric"] = metric
            row["metric_family"] = _metric_family(metric)
            row["metric_role"] = _metric_role(metric)
            row["value"] = _to_optional_float(wide_row.get(metric))
            rows.append(row)
    return pd.DataFrame(rows)


def _robust_z_series(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    finite = values[np.isfinite(values)]
    if finite.empty:
        return pd.Series(np.nan, index=series.index, dtype=float)
    center = float(np.nanmedian(finite))
    scale = float(np.nanmedian(np.abs(finite - center)))
    if not np.isfinite(scale) or scale <= 0:
        scale = float(np.nanstd(finite))
    if not np.isfinite(scale) or scale <= 0:
        return pd.Series(0.0, index=series.index, dtype=float)
    return (values - center) / scale


def _build_adaptive_collapse_rows(subject_metrics: pd.DataFrame, cfg: AnalysisConfig) -> pd.DataFrame:
    if subject_metrics.empty:
        return pd.DataFrame()
    signal_metrics = subject_metrics[subject_metrics["metric_role"] == "signal"].copy()
    if signal_metrics.empty:
        return pd.DataFrame()

    # For datasets where condition_column = task (e.g. ds004100), the condition
    # column in cleaned parquets is None while task carries the within-subject
    # label (ictal / interictal).  The TRAVERSABILITY join would discard all rows
    # because pandas merge treats NaN != NaN.  Coalesce condition from task so
    # the join keys are consistent across all analysis types.
    if "condition" in signal_metrics.columns and "task" in signal_metrics.columns:
        null_cond = signal_metrics["condition"].isna()
        if null_cond.any():
            signal_metrics.loc[null_cond, "condition"] = signal_metrics.loc[null_cond, "task"]

    rows: List[Dict[str, Any]] = []
    alias_source = signal_metrics[
        (signal_metrics["analysis_type"] == "reachability_cones")
        & (
            signal_metrics["metric"].isin(
                [
                    "q_ratio_h4_median",
                    "tube_capture_gate_median",
                    "tube_a_operator_norm_median",
                    "tube_q_ratio_h4_median",
                ]
            )
        )
    ].copy()
    alias_map = {
        "q_ratio_h4_median": "q_ratio_h4",
        "tube_q_ratio_h4_median": "q_ratio_h4",
        "tube_capture_gate_median": "capture_gate",
        "tube_a_operator_norm_median": "a_operator_norm",
    }
    if not alias_source.empty:
        alias_source["analysis_type"] = "adaptive_collapse"
        alias_source["source_analysis_type"] = "adaptive_collapse"
        alias_source["source_file"] = "derived::adaptive_collapse"
        alias_source["metric_family"] = "adaptive_collapse"
        alias_source["metric"] = alias_source["metric"].map(alias_map).fillna(alias_source["metric"])
        dedupe_cols = [column for column in TRAVERSABILITY_JOIN_COLUMNS if column in alias_source.columns] + ["metric"]
        if dedupe_cols:
            alias_source = alias_source.drop_duplicates(subset=dedupe_cols, keep="first")
        rows.extend(alias_source.to_dict(orient="records"))

    join_cols = [column for column in TRAVERSABILITY_JOIN_COLUMNS if column in signal_metrics.columns]
    if join_cols:
        speed_source = pd.DataFrame()
        for analysis_type in ("trajectory_dynamics", "sleep_stage_dynamics", "tier2_emmi"):
            candidate = signal_metrics[
                (signal_metrics["analysis_type"] == analysis_type)
                & (signal_metrics["metric"].isin(["speed_median", "speed_mean"]))
            ].copy()
            if not candidate.empty:
                speed_source = candidate
                break
        rotation_source = signal_metrics[
            (signal_metrics["analysis_type"] == "global_mnps_jacobian_3d")
            & (signal_metrics["metric"].isin(["rotation_norm_median", "rotation_norm_mean"]))
        ].copy()
        anis_source = signal_metrics[
            (signal_metrics["analysis_type"] == "global_mnps_jacobian_3d")
            & (signal_metrics["metric"].isin(["anisotropy_abs_eig_median", "anisotropy_abs_eig_mean"]))
        ].copy()
        if not speed_source.empty and not rotation_source.empty:
            speed_source = speed_source.drop_duplicates(subset=join_cols).rename(columns={"value": "speed_value", "metric": "speed_metric"})
            rotation_source = rotation_source.drop_duplicates(subset=join_cols).rename(
                columns={"value": "rotation_value", "metric": "rotation_metric"}
            )
            ati_frame = speed_source[join_cols + ["speed_value", "finite_ok", "not_testable", "validity_limited"]].rename(
                columns={
                    "finite_ok": "finite_ok_speed",
                    "not_testable": "not_testable_speed",
                    "validity_limited": "validity_limited_speed",
                }
            ).merge(
                rotation_source[join_cols + ["rotation_value", "finite_ok", "not_testable", "validity_limited"]].rename(
                    columns={
                        "finite_ok": "finite_ok_rotation",
                        "not_testable": "not_testable_rotation",
                        "validity_limited": "validity_limited_rotation",
                    }
                ),
                on=join_cols,
                how="inner",
            )
            if not ati_frame.empty:
                ati_frame["speed_z"] = _robust_z_series(ati_frame["speed_value"])
                ati_frame["rotation_z"] = _robust_z_series(ati_frame["rotation_value"])
                ati_frame["ati_reduced"] = ati_frame["speed_z"] + ati_frame["rotation_z"]
                if not anis_source.empty:
                    anis_source = anis_source.drop_duplicates(subset=join_cols).rename(columns={"value": "anisotropy_value"})
                    ati_frame = ati_frame.merge(anis_source[join_cols + ["anisotropy_value"]], on=join_cols, how="left")
                    ati_frame["anisotropy_z"] = _robust_z_series(ati_frame["anisotropy_value"])
                    ati_frame["ati_full"] = ati_frame["ati_reduced"] - ati_frame["anisotropy_z"]
                base_frame = ati_frame[join_cols].copy()
                base_frame["analysis_type"] = "adaptive_collapse"
                base_frame["source_analysis_type"] = "adaptive_collapse"
                base_frame["source_file"] = "derived::adaptive_collapse"
                base_frame["metric_role"] = "signal"
                base_frame["finite_ok"] = _bool_series(ati_frame, "finite_ok_speed", True) & _bool_series(
                    ati_frame, "finite_ok_rotation", True
                )
                base_frame["not_testable"] = _bool_series(ati_frame, "not_testable_speed", False) | _bool_series(
                    ati_frame, "not_testable_rotation", False
                )
                base_frame["validity_limited"] = _bool_series(
                    ati_frame, "validity_limited_speed", False
                ) | _bool_series(ati_frame, "validity_limited_rotation", False)
                for metric_name in ("ati_reduced", "ati_full"):
                    if metric_name not in ati_frame.columns:
                        continue
                    metric_frame = base_frame.copy()
                    metric_frame["metric"] = metric_name
                    metric_frame["metric_family"] = "adaptive_collapse"
                    metric_frame["value"] = pd.to_numeric(ati_frame[metric_name], errors="coerce")
                    metric_frame = metric_frame[np.isfinite(metric_frame["value"].to_numpy(dtype=float))]
                    rows.extend(metric_frame.to_dict(orient="records"))

    cfca_source = signal_metrics[
        (signal_metrics["analysis_type"] == "global_mnps_jacobian_9d_block_jacobian")
        & (signal_metrics["metric"] == "block_frobenius_mean")
    ].copy()
    if not cfca_source.empty:
        for column in ("source_group", "target_group"):
            if column not in cfca_source.columns:
                cfca_source[column] = None
        block_wide = (
            cfca_source.assign(
                block_key=cfca_source["target_group"].astype(str) + "_" + cfca_source["source_group"].astype(str)
            )
            .pivot_table(
                index=join_cols,
                columns="block_key",
                values="value",
                aggfunc="first",
            )
            .reset_index()
        )
        if not block_wide.empty:
            components = []
            for left, right in (("m_d", "d_m"), ("m_e", "e_m"), ("d_e", "e_d")):
                left_vals = pd.to_numeric(block_wide.get(left), errors="coerce")
                right_vals = pd.to_numeric(block_wide.get(right), errors="coerce")
                comp = (left_vals - right_vals).abs() / (left_vals.abs() + right_vals.abs() + 1e-12)
                components.append(comp.rename(f"cfca_{left}_{right}"))
            comp_frame = pd.concat(components, axis=1)
            block_wide["cfca"] = comp_frame.sum(axis=1, min_count=1)
            base_frame = block_wide[join_cols].copy()
            base_frame["analysis_type"] = "adaptive_collapse"
            base_frame["source_analysis_type"] = "adaptive_collapse"
            base_frame["source_file"] = "derived::adaptive_collapse"
            base_frame["metric_role"] = "signal"
            base_frame["finite_ok"] = np.isfinite(pd.to_numeric(block_wide["cfca"], errors="coerce"))
            base_frame["not_testable"] = False
            base_frame["validity_limited"] = False
            metric_frame = base_frame.copy()
            metric_frame["metric"] = "cfca"
            metric_frame["metric_family"] = "adaptive_collapse"
            metric_frame["value"] = pd.to_numeric(block_wide["cfca"], errors="coerce")
            metric_frame = metric_frame[np.isfinite(metric_frame["value"].to_numpy(dtype=float))]
            rows.extend(metric_frame.to_dict(orient="records"))

    return pd.DataFrame(rows)


TRAVERSABILITY_JOIN_COLUMNS = [
    "dataset_id",
    "subject_id",
    "group",
    "condition",
    "task",
    "session",
    "run",
    "acq",
]


def _minmax_normalize_series(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    finite = values[np.isfinite(values)]
    if finite.empty:
        return pd.Series(np.nan, index=series.index, dtype=float)
    low = float(finite.min())
    high = float(finite.max())
    if np.isfinite(low) and np.isfinite(high) and high > low:
        return (values - low) / (high - low)
    return pd.Series(0.0, index=series.index, dtype=float)


def _bool_series(frame: pd.DataFrame, column: str, default: bool) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=bool)
    return frame[column].map(lambda value: _to_optional_bool(value, default)).fillna(default).astype(bool)


def _build_traversability_rows_for_contrast(
    signal_metrics: pd.DataFrame,
    contrast: ContrastConfig,
    cfg: AnalysisConfig,
    rng: np.random.Generator,
) -> List[Dict[str, Any]]:
    target_analysis = "global_mnps_jacobian_3d"
    if contrast.analyses and target_analysis not in contrast.analyses:
        return []

    speed_source = pd.DataFrame()
    for analysis_type in ("trajectory_dynamics", "sleep_stage_dynamics", "tier2_emmi"):
        candidate = signal_metrics[
            (signal_metrics["analysis_type"] == analysis_type)
            & (signal_metrics["metric"].isin(["speed_mean", "speed_median"]))
        ].copy()
        if not candidate.empty:
            speed_source = candidate
            break
    anis_source = signal_metrics[
        (signal_metrics["analysis_type"] == target_analysis)
        & (signal_metrics["metric"].isin(["anisotropy_abs_eig_mean", "anisotropy_abs_eig_median"]))
    ].copy()
    if speed_source.empty or anis_source.empty:
        return []

    if "condition" in speed_source.columns:
        stage_specific = speed_source["condition"].notna()
        if stage_specific.any():
            speed_source = speed_source[stage_specific].copy()

    if "anisotropy_abs_eig_mean" in anis_source["metric"].unique():
        anis_source = anis_source[anis_source["metric"] == "anisotropy_abs_eig_mean"].copy()
    else:
        anis_source = anis_source[anis_source["metric"] == "anisotropy_abs_eig_median"].copy()

    join_cols = [
        column
        for column in TRAVERSABILITY_JOIN_COLUMNS
        if (
            column in speed_source.columns
            and column in anis_source.columns
            and not speed_source[column].isna().all()
            and not anis_source[column].isna().all()
        )
    ]
    if not join_cols:
        return []

    speed_keep = join_cols + [col for col in ["finite_ok", "not_testable", "validity_limited", "metric", "value"] if col in speed_source.columns]
    anis_keep = join_cols + [col for col in ["finite_ok", "not_testable", "validity_limited", "value"] if col in anis_source.columns]
    merged = speed_source[speed_keep].rename(
        columns={
            "metric": "speed_metric",
            "value": "speed_value",
            "finite_ok": "finite_ok_speed",
            "not_testable": "not_testable_speed",
            "validity_limited": "validity_limited_speed",
        }
    ).merge(
        anis_source[anis_keep].rename(
            columns={
                "value": "anisotropy_value",
                "finite_ok": "finite_ok_anis",
                "not_testable": "not_testable_anis",
                "validity_limited": "validity_limited_anis",
            }
        ),
        on=join_cols,
        how="inner",
    )
    if merged.empty:
        return []

    subset = merged[_match_selector(merged, contrast.subset)].copy() if contrast.subset else merged.copy()
    if subset.empty:
        return []

    pair_keys = contrast.pairing_keys or cfg.design.pairing_keys
    pair_keys = [key for key in pair_keys if key in subset.columns and not subset[key].isna().all()]
    if contrast.type == "paired" and pair_keys:
        subset["anisotropy_norm"] = subset.groupby(pair_keys, dropna=False)["anisotropy_value"].transform(_minmax_normalize_series)
    else:
        subset["anisotropy_norm"] = _minmax_normalize_series(subset["anisotropy_value"])
    subset["TraversabilityIndex"] = pd.to_numeric(subset["speed_value"], errors="coerce") * (1.0 - subset["anisotropy_norm"])

    base_frame = subset[join_cols].copy()
    base_frame["finite_ok"] = _bool_series(subset, "finite_ok_speed", True) & _bool_series(subset, "finite_ok_anis", True)
    base_frame["not_testable"] = _bool_series(subset, "not_testable_speed", False) | _bool_series(subset, "not_testable_anis", False)
    base_frame["validity_limited"] = _bool_series(subset, "validity_limited_speed", False) | _bool_series(subset, "validity_limited_anis", False)
    base_frame["analysis_type"] = target_analysis
    base_frame["metric_role"] = "signal"

    rows: List[Dict[str, Any]] = []
    metric_map = {
        "speed_mean": subset["speed_value"].where(subset["speed_metric"] == "speed_mean"),
        "speed_median": subset["speed_value"].where(subset["speed_metric"] == "speed_median"),
        "anisotropy_norm": subset["anisotropy_norm"],
        "TraversabilityIndex": subset["TraversabilityIndex"],
    }
    for metric_name, values in metric_map.items():
        if contrast.metrics and metric_name not in contrast.metrics:
            continue
        frame = base_frame.copy()
        frame["metric"] = metric_name
        frame["value"] = pd.to_numeric(values, errors="coerce")
        frame = frame[np.isfinite(frame["value"].to_numpy(dtype=float))].copy()
        if frame.empty:
            continue
        row = _run_contrast_for_group(
            frame,
            contrast,
            cfg,
            {"analysis_type": target_analysis, "metric": metric_name},
            rng,
        )
        if row is not None:
            rows.append(row)
    return rows


def _match_selector(frame: pd.DataFrame, selector: Dict[str, Any]) -> pd.Series:
    mask = pd.Series(True, index=frame.index, dtype=bool)
    for column, expected in selector.items():
        if column not in frame.columns:
            return pd.Series(False, index=frame.index, dtype=bool)
        if isinstance(expected, list):
            mask &= frame[column].isin(expected)
        else:
            mask &= frame[column] == expected
    return mask


def _qc_mask(frame: pd.DataFrame, cfg: AnalysisConfig) -> pd.Series:
    mask = pd.Series(True, index=frame.index, dtype=bool)
    if cfg.qc.require_finite_ok and "finite_ok" in frame.columns:
        finite_ok = frame["finite_ok"].map(lambda value: _to_optional_bool(value, True))
        mask &= finite_ok.fillna(True)
    if cfg.qc.exclude_not_testable and "not_testable" in frame.columns:
        not_testable = frame["not_testable"].map(lambda value: _to_optional_bool(value, False))
        mask &= ~not_testable.fillna(False)
    if cfg.qc.exclude_validity_limited and "validity_limited" in frame.columns:
        validity_limited = frame["validity_limited"].map(lambda value: _to_optional_bool(value, False))
        mask &= ~validity_limited.fillna(False)
    mask &= np.isfinite(frame["value"].astype(float))
    return mask


def _collapse_pair_duplicates(frame: pd.DataFrame, pair_keys: Sequence[str], value_name: str) -> pd.DataFrame:
    if frame.empty:
        return frame
    keep = list(pair_keys) + [value_name]
    work = frame[keep].copy()
    if work.duplicated(subset=list(pair_keys)).any():
        work = (
            work.groupby(list(pair_keys), dropna=False, as_index=False)[value_name]
            .mean()
        )
    return work


def _paired_frames_for_contrast(
    group_frame: pd.DataFrame,
    contrast: ContrastConfig,
    cfg: AnalysisConfig,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    subset_frame = group_frame[_match_selector(group_frame, contrast.subset)] if contrast.subset else group_frame
    left_qc = subset_frame[_match_selector(subset_frame, contrast.left) & _qc_mask(subset_frame, cfg)].copy()
    right_qc = subset_frame[_match_selector(subset_frame, contrast.right) & _qc_mask(subset_frame, cfg)].copy()
    pair_keys = contrast.pairing_keys or cfg.design.pairing_keys
    pair_keys = [
        key
        for key in pair_keys
        if key in left_qc.columns
        and key in right_qc.columns
        and not left_qc[key].isna().all()
        and not right_qc[key].isna().all()
    ]
    if not pair_keys:
        return subset_frame, left_qc, right_qc, pd.DataFrame()
    left_small = _collapse_pair_duplicates(
        left_qc.rename(columns={"value": "value_left"}),
        pair_keys,
        "value_left",
    )
    right_small = _collapse_pair_duplicates(
        right_qc.rename(columns={"value": "value_right"}),
        pair_keys,
        "value_right",
    )
    merged = left_small.merge(right_small, on=pair_keys, how="inner")
    return subset_frame, left_qc, right_qc, merged


def _dz_from_diff(diff: np.ndarray) -> float:
    diff = np.asarray(diff, dtype=float)
    diff = diff[np.isfinite(diff)]
    if diff.size < 2:
        return float("nan")
    sd = float(np.std(diff, ddof=1))
    if not np.isfinite(sd):
        return float("nan")
    if sd <= 0:
        return 0.0
    return float(np.mean(diff) / sd)


def _negative_control_stage_table(
    group_frame: pd.DataFrame,
    contrast: ContrastConfig,
    cfg: AnalysisConfig,
    stage_order: Sequence[str],
) -> pd.DataFrame:
    qc_frame = group_frame[_qc_mask(group_frame, cfg)].copy()
    condition_column = cfg.design.condition_column if cfg.design.condition_column in qc_frame.columns else "condition"
    pair_keys = contrast.pairing_keys or cfg.design.pairing_keys
    pair_keys = [key for key in pair_keys if key in qc_frame.columns and not qc_frame[key].isna().all()]
    if not pair_keys or condition_column not in qc_frame.columns:
        return pd.DataFrame()
    stage_frame = qc_frame[qc_frame[condition_column].isin(list(stage_order))].copy()
    if stage_frame.empty:
        return pd.DataFrame()
    pivot = (
        stage_frame.pivot_table(
            index=pair_keys,
            columns=condition_column,
            values="value",
            aggfunc="median",
        )
    )
    if any(stage not in pivot.columns for stage in stage_order):
        return pd.DataFrame()
    pivot = pivot.dropna(subset=list(stage_order), how="any").reset_index()
    return pivot


def _two_sided_permutation_paired(values: np.ndarray, n_perm: int, rng: np.random.Generator) -> float:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return float("nan")
    observed = abs(float(np.mean(values)))
    if values.size <= 16:
        totals = []
        for signs in product((-1.0, 1.0), repeat=values.size):
            signed = values * np.asarray(signs, dtype=float)
            totals.append(abs(float(np.mean(signed))))
        arr = np.asarray(totals, dtype=float)
        return float((np.sum(arr >= observed) + 1) / (arr.size + 1))
    count = 0
    for _ in range(n_perm):
        signs = rng.choice(np.array([-1.0, 1.0]), size=values.size)
        stat = abs(float(np.mean(values * signs)))
        count += int(stat >= observed)
    return float((count + 1) / (n_perm + 1))


def _two_sided_permutation_unpaired(
    left: np.ndarray,
    right: np.ndarray,
    n_perm: int,
    rng: np.random.Generator,
) -> float:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    if left.size == 0 or right.size == 0:
        return float("nan")
    observed = abs(float(np.mean(left) - np.mean(right)))
    pooled = np.concatenate([left, right])
    n_left = left.size
    count = 0
    for _ in range(n_perm):
        perm = rng.permutation(pooled)
        stat = abs(float(np.mean(perm[:n_left]) - np.mean(perm[n_left:])))
        count += int(stat >= observed)
    return float((count + 1) / (n_perm + 1))


def _bootstrap_ci_paired(values: np.ndarray, n_boot: int, rng: np.random.Generator) -> Tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return float("nan"), float("nan")
    stats = []
    for _ in range(n_boot):
        sample = rng.choice(values, size=values.size, replace=True)
        stats.append(float(np.mean(sample)))
    return float(np.quantile(stats, 0.025)), float(np.quantile(stats, 0.975))


def _bootstrap_ci_unpaired(
    left: np.ndarray,
    right: np.ndarray,
    n_boot: int,
    rng: np.random.Generator,
) -> Tuple[float, float]:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    if left.size == 0 or right.size == 0:
        return float("nan"), float("nan")
    stats = []
    for _ in range(n_boot):
        sample_left = rng.choice(left, size=left.size, replace=True)
        sample_right = rng.choice(right, size=right.size, replace=True)
        stats.append(float(np.mean(sample_left) - np.mean(sample_right)))
    return float(np.quantile(stats, 0.025)), float(np.quantile(stats, 0.975))


def _cohens_d_unpaired(left: np.ndarray, right: np.ndarray) -> float:
    if left.size < 2 or right.size < 2:
        return float("nan")
    var_left = float(np.var(left, ddof=1))
    var_right = float(np.var(right, ddof=1))
    pooled_denom = ((left.size - 1) * var_left + (right.size - 1) * var_right) / (left.size + right.size - 2)
    pooled_sd = math.sqrt(pooled_denom) if pooled_denom > 0 else float("nan")
    if not np.isfinite(pooled_sd) or pooled_sd == 0:
        return float("nan")
    return float((np.mean(left) - np.mean(right)) / pooled_sd)


def _cohens_dz_paired(diff: np.ndarray) -> float:
    if diff.size < 2:
        return float("nan")
    sd = float(np.std(diff, ddof=1))
    if not np.isfinite(sd) or sd == 0:
        return float("nan")
    return float(np.mean(diff) / sd)


def _apply_bh_fdr(frame: pd.DataFrame, group_columns: Sequence[str], p_column: str) -> pd.DataFrame:
    result = frame.copy()
    result["q_value"] = np.nan
    if result.empty or p_column not in result.columns:
        return result
    for _, idx in result.groupby(list(group_columns), dropna=False).groups.items():
        block = result.loc[list(idx)].copy()
        valid = block[p_column].notna()
        if not valid.any():
            continue
        work = block.loc[valid, p_column].sort_values()
        ranks = np.arange(1, len(work) + 1, dtype=float)
        qvals = (work.to_numpy(dtype=float) * len(work)) / ranks
        qvals = np.minimum.accumulate(qvals[::-1])[::-1]
        result.loc[work.index, "q_value"] = np.clip(qvals, 0.0, 1.0)
    return result


def _summarize_loaded_block(analysis_type: str, frame: pd.DataFrame, source_file: Path) -> Dict[str, Any]:
    finite_series = frame["finite_ok"] if "finite_ok" in frame.columns else pd.Series([True] * len(frame))
    not_testable_series = frame["not_testable"] if "not_testable" in frame.columns else pd.Series([False] * len(frame))
    validity_limited_series = frame["validity_limited"] if "validity_limited" in frame.columns else pd.Series([False] * len(frame))
    return {
        "summary_scope": "analysis_block",
        "analysis_type": analysis_type,
        "source_file": str(source_file),
        "n_rows": int(len(frame)),
        "n_subjects": int(frame["subject_id"].nunique()) if "subject_id" in frame.columns else 0,
        "finite_ok_rate": _mean_boolish(pd.Series(finite_series), True),
        "not_testable_rate": _mean_boolish(pd.Series(not_testable_series), False),
        "validity_limited_rate": _mean_boolish(pd.Series(validity_limited_series), False),
    }


def _run_contrast_for_group(
    group_frame: pd.DataFrame,
    contrast: ContrastConfig,
    cfg: AnalysisConfig,
    context: Dict[str, Any],
    rng: np.random.Generator,
) -> Optional[Dict[str, Any]]:
    subset_frame = group_frame[_match_selector(group_frame, contrast.subset)] if contrast.subset else group_frame
    left_frame = subset_frame[_match_selector(subset_frame, contrast.left)].copy()
    right_frame = subset_frame[_match_selector(subset_frame, contrast.right)].copy()
    if left_frame.empty or right_frame.empty:
        return None

    left_total = int(left_frame["subject_id"].nunique()) if "subject_id" in left_frame.columns else int(len(left_frame))
    right_total = int(right_frame["subject_id"].nunique()) if "subject_id" in right_frame.columns else int(len(right_frame))

    _, left_qc, right_qc, merged = _paired_frames_for_contrast(group_frame, contrast, cfg)

    out: Dict[str, Any] = dict(context)
    out["contrast_name"] = contrast.name
    out["contrast_type"] = contrast.type
    out["left_n_total"] = left_total
    out["right_n_total"] = right_total
    out["left_n_qc"] = int(left_qc["subject_id"].nunique()) if "subject_id" in left_qc.columns else int(len(left_qc))
    out["right_n_qc"] = int(right_qc["subject_id"].nunique()) if "subject_id" in right_qc.columns else int(len(right_qc))
    out["finite_ok_rate"] = _mean_boolish(subset_frame["finite_ok"], True) if "finite_ok" in subset_frame.columns else float("nan")
    out["not_testable_rate"] = _mean_boolish(subset_frame["not_testable"], False) if "not_testable" in subset_frame.columns else float("nan")
    out["validity_limited_rate"] = _mean_boolish(subset_frame["validity_limited"], False) if "validity_limited" in subset_frame.columns else float("nan")
    out["qc_pass_rate"] = float((_qc_mask(subset_frame, cfg)).mean()) if len(subset_frame) else float("nan")

    if contrast.type == "paired":
        if merged.empty and (left_qc.empty or right_qc.empty):
            return None
        if merged.empty and len(left_qc) and len(right_qc):
            out["n_pairs"] = 0
            out["skip_reason"] = "no_pairing_keys_or_no_overlap"
            return out
        if merged.empty:
            return None
        if len(merged) < cfg.statistics.min_pairs:
            out["n_pairs"] = int(len(merged))
            out["skip_reason"] = "too_few_pairs"
            return out
        diff = merged["value_right"].to_numpy(dtype=float) - merged["value_left"].to_numpy(dtype=float)
        out["n_pairs"] = int(len(merged))
        out["left_mean"] = float(np.mean(merged["value_left"]))
        out["right_mean"] = float(np.mean(merged["value_right"]))
        out["left_median"] = float(np.median(merged["value_left"]))
        out["right_median"] = float(np.median(merged["value_right"]))
        out["effect_estimate"] = float(np.mean(diff))
        out["effect_size"] = _cohens_dz_paired(diff)
        out["p_value"] = _two_sided_permutation_paired(diff, cfg.statistics.permutation_n, rng)
        ci_low, ci_high = _bootstrap_ci_paired(diff, cfg.statistics.bootstrap_n, rng)
        out["effect_ci_low"] = ci_low
        out["effect_ci_high"] = ci_high
        return out

    left_values = left_qc["value"].to_numpy(dtype=float)
    right_values = right_qc["value"].to_numpy(dtype=float)
    if len(left_values) < cfg.statistics.min_group_n or len(right_values) < cfg.statistics.min_group_n:
        out["skip_reason"] = "too_few_group_samples"
        return out
    out["left_mean"] = float(np.mean(left_values))
    out["right_mean"] = float(np.mean(right_values))
    out["left_median"] = float(np.median(left_values))
    out["right_median"] = float(np.median(right_values))
    out["left_n"] = int(len(left_values))
    out["right_n"] = int(len(right_values))
    out["effect_estimate"] = float(np.mean(right_values) - np.mean(left_values))
    out["effect_size"] = _cohens_d_unpaired(right_values, left_values)
    out["p_value"] = _two_sided_permutation_unpaired(right_values, left_values, cfg.statistics.permutation_n, rng)
    ci_low, ci_high = _bootstrap_ci_unpaired(right_values, left_values, cfg.statistics.bootstrap_n, rng)
    out["effect_ci_low"] = ci_low
    out["effect_ci_high"] = ci_high
    return out


def _run_negative_control_for_group(
    group_frame: pd.DataFrame,
    control: NegativeControlConfig,
    source_contrast: ContrastConfig,
    cfg: AnalysisConfig,
    context: Dict[str, Any],
    rng: np.random.Generator,
) -> Optional[Dict[str, Any]]:
    if source_contrast.type != "paired":
        return None
    _, _, _, merged = _paired_frames_for_contrast(group_frame, source_contrast, cfg)
    if merged.empty or len(merged) < cfg.statistics.min_pairs:
        return None

    diff = merged["value_right"].to_numpy(dtype=float) - merged["value_left"].to_numpy(dtype=float)
    observed_dz = _dz_from_diff(diff)
    permutations = int(control.permutation_n or 1000)
    out: Dict[str, Any] = dict(context)
    out["contrast_name"] = control.name
    out["contrast_type"] = control.type
    out["source_contrast_name"] = source_contrast.name
    out["n_pairs"] = int(len(merged))
    out["is_negative_control"] = True

    if control.type == "nc1_within_subject_stage_permutation":
        stage_order = control.stage_order or ["awake", "nrem2", "nrem3", "rem"]
        if len(stage_order) < 4:
            return None
        stage_table = _negative_control_stage_table(group_frame, source_contrast, cfg, stage_order)
        if stage_table.empty or len(stage_table) < cfg.statistics.min_pairs:
            return None
        values = stage_table[list(stage_order)].to_numpy(dtype=float)
        null_dz = np.zeros((permutations,), dtype=float)
        for idx in range(permutations):
            permuted = np.array([row[rng.permutation(len(stage_order))] for row in values], dtype=float)
            null_dz[idx] = _dz_from_diff(permuted[:, 0] - permuted[:, 2])
        null_dz = null_dz[np.isfinite(null_dz)]
        if null_dz.size == 0:
            return None
        k = int(np.sum(np.abs(null_dz) >= abs(observed_dz))) if np.isfinite(observed_dz) else -1
        exceed_prob = float((k + 1) / (int(null_dz.size) + 1)) if k >= 0 else float("nan")
        out["effect_estimate"] = float(np.mean(null_dz))
        out["effect_size"] = float(np.median(null_dz))
        out["effect_ci_low"] = float(np.quantile(null_dz, 0.025))
        out["effect_ci_high"] = float(np.quantile(null_dz, 0.975))
        out["p_value"] = float("nan")
        out["q_value"] = float("nan")
        out["notes"] = (
            "negative control; within-subject stage-label permutation "
            f"(K={permutations}); null_dz_median={np.median(null_dz):.6f}; "
            f"null_dz_mean={np.mean(null_dz):.6f}; observed_dz={observed_dz:.6f}; "
            f"k_abs_ge_obs={k}; p_perm_abs_ge_obs={(exceed_prob if np.isfinite(exceed_prob) else float('nan')):.6f}"
        )
        return out

    if control.type == "nc2_sign_flip_surrogate":
        null_d = np.zeros((permutations,), dtype=float)
        for idx in range(permutations):
            signs = rng.choice(np.array([-1.0, 1.0]), size=diff.size)
            null_d[idx] = _dz_from_diff(diff * signs)
        null_d = null_d[np.isfinite(null_d)]
        if null_d.size == 0:
            return None
        out["effect_estimate"] = float(np.median(np.abs(null_d)))
        out["effect_size"] = float(np.median(null_d))
        out["effect_ci_low"] = float(np.quantile(null_d, 0.025))
        out["effect_ci_high"] = float(np.quantile(null_d, 0.975))
        out["p_value"] = float("nan")
        out["q_value"] = float("nan")
        out["notes"] = "negative control; sign-flip surrogate"
        return out

    return None


def _build_contrast_results(subject_metrics: pd.DataFrame, cfg: AnalysisConfig) -> pd.DataFrame:
    if subject_metrics.empty or not cfg.contrasts:
        return pd.DataFrame()

    signal_metrics = subject_metrics[subject_metrics["metric_role"] == "signal"].copy()
    if signal_metrics.empty:
        return pd.DataFrame()

    group_columns = ["analysis_type", "metric"] + [column for column in CONTEXT_COLUMNS if column in signal_metrics.columns]
    rows: List[Dict[str, Any]] = []
    rng = np.random.default_rng(cfg.statistics.random_seed)

    for contrast in cfg.contrasts:
        contrast_frame = signal_metrics
        if contrast.analyses:
            contrast_frame = contrast_frame[contrast_frame["analysis_type"].isin(contrast.analyses)]
        if contrast.metrics:
            contrast_frame = contrast_frame[contrast_frame["metric"].isin(contrast.metrics)]
        if contrast_frame.empty:
            continue
        grouped = contrast_frame.groupby(group_columns, dropna=False)
        for keys, group_frame in grouped:
            if not isinstance(keys, tuple):
                keys = (keys,)
            context = dict(zip(group_columns, keys))
            row = _run_contrast_for_group(group_frame, contrast, cfg, context, rng)
            if row is not None:
                rows.append(row)
        rows.extend(_build_traversability_rows_for_contrast(signal_metrics, contrast, cfg, rng))

    main_result = pd.DataFrame(rows)
    if not main_result.empty:
        main_result = _apply_bh_fdr(main_result, cfg.statistics.fdr_group_by, "p_value")
        if "is_negative_control" not in main_result.columns:
            main_result["is_negative_control"] = False

    control_rows: List[Dict[str, Any]] = []
    if cfg.negative_controls:
        contrast_by_name = {contrast.name: contrast for contrast in cfg.contrasts}
        for control in cfg.negative_controls:
            source_contrast = contrast_by_name.get(control.source_contrast)
            if source_contrast is None:
                continue
            control_frame = signal_metrics
            analyses = control.analyses or source_contrast.analyses
            metrics = control.metrics or source_contrast.metrics
            if analyses:
                control_frame = control_frame[control_frame["analysis_type"].isin(analyses)]
            if metrics:
                control_frame = control_frame[control_frame["metric"].isin(metrics)]
            if control_frame.empty:
                continue
            grouped = control_frame.groupby(group_columns, dropna=False)
            for keys, group_frame in grouped:
                if not isinstance(keys, tuple):
                    keys = (keys,)
                context = dict(zip(group_columns, keys))
                row = _run_negative_control_for_group(group_frame, control, source_contrast, cfg, context, rng)
                if row is not None:
                    control_rows.append(row)

    control_result = pd.DataFrame(control_rows)
    if not control_result.empty and "q_value" not in control_result.columns:
        control_result["q_value"] = np.nan

    if main_result.empty and control_result.empty:
        return pd.DataFrame()
    if main_result.empty:
        return control_result
    if control_result.empty:
        return main_result
    return pd.concat([main_result, control_result], ignore_index=True, sort=False)


def _build_qc_summary(
    subject_metrics: pd.DataFrame,
    loaded_block_rows: Iterable[Dict[str, Any]],
    contrast_results: pd.DataFrame,
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = [dict(row) for row in loaded_block_rows]
    if not subject_metrics.empty:
        metric_summary = (
            subject_metrics.groupby(["analysis_type", "metric_role"], dropna=False)
            .agg(
                n_metric_rows=("value", "size"),
                n_subjects=("subject_id", "nunique"),
                value_nonnull_rate=("value", lambda s: float(np.isfinite(pd.to_numeric(s, errors="coerce")).mean())),
            )
            .reset_index()
        )
        for _, row in metric_summary.iterrows():
            rows.append(
                {
                    "summary_scope": "metric_role",
                    "analysis_type": row["analysis_type"],
                    "metric_role": row["metric_role"],
                    "n_metric_rows": int(row["n_metric_rows"]),
                    "n_subjects": int(row["n_subjects"]),
                    "value_nonnull_rate": float(row["value_nonnull_rate"]),
                }
            )
    if not contrast_results.empty:
        contrast_frame = contrast_results.copy()
        if "effect_estimate" not in contrast_frame.columns:
            contrast_frame["effect_estimate"] = np.nan
        if "q_value" not in contrast_frame.columns:
            contrast_frame["q_value"] = np.nan
        contrast_summary = (
            contrast_frame.groupby(["contrast_name", "analysis_type"], dropna=False)
            .agg(
                n_metric_tests=("metric", "size"),
                median_qc_pass_rate=("qc_pass_rate", "median"),
                median_validity_limited_rate=("validity_limited_rate", "median"),
                median_effect_abs=(
                    "effect_estimate",
                    lambda s: (
                        lambda vals: float(np.nanmedian(np.abs(vals))) if np.isfinite(vals).any() else float("nan")
                    )(pd.to_numeric(s, errors="coerce").to_numpy(dtype=float)),
                ),
                significant_q05=("q_value", lambda s: int((pd.to_numeric(s, errors="coerce") <= 0.05).fillna(False).sum())),
            )
            .reset_index()
        )
        for _, row in contrast_summary.iterrows():
            rows.append(
                {
                    "summary_scope": "contrast",
                    "contrast_name": row["contrast_name"],
                    "analysis_type": row["analysis_type"],
                    "n_metric_tests": int(row["n_metric_tests"]),
                    "median_qc_pass_rate": float(row["median_qc_pass_rate"]),
                    "median_validity_limited_rate": float(row["median_validity_limited_rate"]),
                    "median_effect_abs": float(row["median_effect_abs"]),
                    "significant_q05": int(row["significant_q05"]),
                }
            )
    return pd.DataFrame(rows)


def run_cleaned_analysis_pipeline(
    config_path: str | Path,
    cleaned_root: str | Path | None = None,
    output_root: str | Path | None = None,
    blocks_filter: Optional[Sequence[str]] = None,
    contrasts_filter: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    config_file = Path(config_path)
    cfg = load_analysis_config(config_file)

    resolved_input = Path(cleaned_root) if cleaned_root else Path(cfg.cleaned_root or "")
    if not str(resolved_input):
        raise ValueError("No cleaned_root provided. Set input.cleaned_root in config or pass --cleaned-root.")
    if not resolved_input.exists():
        if cfg.runtime.fail_on_missing_input:
            raise FileNotFoundError(f"Cleaned root does not exist: {resolved_input}")
        return {"dataset": cfg.dataset, "written_files": {}, "skipped": ["missing_cleaned_root"]}

    latest_files = _discover_latest_cleaned_files(resolved_input, cfg.dataset)
    if not latest_files:
        if cfg.runtime.fail_on_missing_input:
            raise FileNotFoundError(f"No cleaned parquet files found under: {resolved_input}")
        return {"dataset": cfg.dataset, "written_files": {}, "skipped": ["no_cleaned_files"]}

    selected_blocks = {str(item).strip() for item in (blocks_filter or []) if str(item).strip()}
    block_configs = cfg.blocks or {}
    h5_catalog = _read_source_h5_catalog(latest_files)

    loaded_block_rows: List[Dict[str, Any]] = []
    subject_metric_frames: List[pd.DataFrame] = []
    skipped: List[str] = []
    errors: List[str] = []

    for analysis_type, source_file in sorted(latest_files.items()):
        if selected_blocks and analysis_type not in selected_blocks:
            skipped.append(f"{analysis_type}:filtered_out")
            continue
        block_cfg = block_configs.get(analysis_type)
        if block_cfg is not None and not block_cfg.enabled:
            skipped.append(f"{analysis_type}:disabled")
            continue
        try:
            frame = read_parquet_table(source_file)
            frame = _apply_validity_rules(frame, block_cfg)
            loaded_block_rows.append(_summarize_loaded_block(analysis_type, frame, source_file))
            metric_frame = _prepare_subject_metrics_frame(analysis_type, frame, source_file)
            if block_cfg is not None and block_cfg.metrics:
                metric_frame = metric_frame[metric_frame["metric"].isin(block_cfg.metrics)]
            if not metric_frame.empty:
                subject_metric_frames.append(metric_frame)
            else:
                skipped.append(f"{analysis_type}:no_metrics")
        except Exception as exc:  # noqa: BLE001
            msg = f"{analysis_type}:{source_file} -> {exc}"
            errors.append(msg)
            if not cfg.runtime.continue_on_error:
                raise RuntimeError(msg) from exc

    feature_block_names = sorted(FEATURE_BLOCKS.keys() & (set(block_configs.keys()) | selected_blocks))
    for analysis_type in feature_block_names:
        if selected_blocks and analysis_type not in selected_blocks:
            skipped.append(f"{analysis_type}:filtered_out")
            continue
        block_cfg = block_configs.get(analysis_type)
        if block_cfg is not None and not block_cfg.enabled:
            skipped.append(f"{analysis_type}:disabled")
            continue
        try:
            frame = _build_feature_block_frame(analysis_type, h5_catalog)
            if frame.empty:
                skipped.append(f"{analysis_type}:no_rows")
                continue
            frame = _apply_validity_rules(frame, block_cfg)
            loaded_block_rows.append(_summarize_loaded_block(analysis_type, frame, Path(f"h5_features::{analysis_type}")))
            metric_frame = _prepare_subject_metrics_frame(analysis_type, frame, Path(f"h5_features::{analysis_type}"))
            if block_cfg is not None and block_cfg.metrics:
                metric_frame = metric_frame[metric_frame["metric"].isin(block_cfg.metrics)]
            if not metric_frame.empty:
                subject_metric_frames.append(metric_frame)
            else:
                skipped.append(f"{analysis_type}:no_metrics")
        except Exception as exc:  # noqa: BLE001
            msg = f"{analysis_type}:h5_features -> {exc}"
            errors.append(msg)
            if not cfg.runtime.continue_on_error:
                raise RuntimeError(msg) from exc

    custom_block_names = sorted(CUSTOM_H5_BUILDERS.keys() & (set(block_configs.keys()) | selected_blocks))
    for analysis_type in custom_block_names:
        if selected_blocks and analysis_type not in selected_blocks:
            skipped.append(f"{analysis_type}:filtered_out")
            continue
        block_cfg = block_configs.get(analysis_type)
        if block_cfg is not None and not block_cfg.enabled:
            skipped.append(f"{analysis_type}:disabled")
            continue
        try:
            builder = CUSTOM_H5_BUILDERS[analysis_type]
            frame = builder(h5_catalog, cfg.coordinate_contract)
            if frame.empty:
                skipped.append(f"{analysis_type}:no_rows")
                continue
            frame = _apply_validity_rules(frame, block_cfg)
            loaded_block_rows.append(_summarize_loaded_block(analysis_type, frame, Path(f"h5_custom::{analysis_type}")))
            metric_frame = _prepare_subject_metrics_frame(analysis_type, frame, Path(f"h5_custom::{analysis_type}"))
            if block_cfg is not None and block_cfg.metrics:
                metric_frame = metric_frame[metric_frame["metric"].isin(block_cfg.metrics)]
            if not metric_frame.empty:
                subject_metric_frames.append(metric_frame)
            else:
                skipped.append(f"{analysis_type}:no_metrics")
        except Exception as exc:  # noqa: BLE001
            msg = f"{analysis_type}:h5_custom -> {exc}"
            errors.append(msg)
            if not cfg.runtime.continue_on_error:
                raise RuntimeError(msg) from exc

    manifest_block_names = sorted(MANIFEST_BLOCKS.intersection(block_configs.keys()) | (selected_blocks & MANIFEST_BLOCKS))
    for analysis_type in manifest_block_names:
        if selected_blocks and analysis_type not in selected_blocks:
            skipped.append(f"{analysis_type}:filtered_out")
            continue
        block_cfg = block_configs.get(analysis_type)
        if block_cfg is not None and not block_cfg.enabled:
            skipped.append(f"{analysis_type}:disabled")
            continue
        try:
            frame = _build_manifest_block_frame(analysis_type, h5_catalog)
            if frame.empty:
                skipped.append(f"{analysis_type}:no_rows")
                continue
            frame = _apply_validity_rules(frame, block_cfg)
            loaded_block_rows.append(_summarize_loaded_block(analysis_type, frame, Path(f"manifest_json::{analysis_type}")))
            metric_frame = _prepare_subject_metrics_frame(analysis_type, frame, Path(f"manifest_json::{analysis_type}"))
            if block_cfg is not None and block_cfg.metrics:
                metric_frame = metric_frame[metric_frame["metric"].isin(block_cfg.metrics)]
            if not metric_frame.empty:
                subject_metric_frames.append(metric_frame)
            else:
                skipped.append(f"{analysis_type}:no_metrics")
        except Exception as exc:  # noqa: BLE001
            msg = f"{analysis_type}:manifest_json -> {exc}"
            errors.append(msg)
            if not cfg.runtime.continue_on_error:
                raise RuntimeError(msg) from exc

    subject_metrics = pd.concat(subject_metric_frames, ignore_index=True) if subject_metric_frames else pd.DataFrame()
    if not subject_metrics.empty:
        subject_metrics = annotate_propofol_depth(subject_metrics, dataset=cfg.dataset)
        derived_metrics = _build_adaptive_collapse_rows(subject_metrics, cfg)
        if not derived_metrics.empty:
            subject_metrics = pd.concat([subject_metrics, derived_metrics], ignore_index=True, sort=False)
    if contrasts_filter:
        allowed = {str(item).strip() for item in contrasts_filter if str(item).strip()}
        cfg = AnalysisConfig(
            dataset=cfg.dataset,
            cleaned_root=cfg.cleaned_root,
            coordinate_contract=cfg.coordinate_contract,
            output=cfg.output,
            runtime=cfg.runtime,
            qc=cfg.qc,
            statistics=cfg.statistics,
            design=cfg.design,
            blocks=cfg.blocks,
            contrasts=[contrast for contrast in cfg.contrasts if contrast.name in allowed],
            negative_controls=[
                control
                for control in cfg.negative_controls
                if control.name in allowed or control.source_contrast in allowed
            ],
        )

    contrast_results = _build_contrast_results(subject_metrics, cfg)
    qc_summary = _build_qc_summary(subject_metrics, loaded_block_rows, contrast_results)

    out_root = Path(output_root) if output_root else Path(cfg.output.directory)
    out_root.mkdir(parents=True, exist_ok=True)

    written_files: Dict[str, str] = {}
    outputs = {
        "subject_metrics": subject_metrics,
        "contrast_results": contrast_results,
        "qc_summary": qc_summary,
    }
    for analysis_type, frame in outputs.items():
        output_name = build_output_filename(
            dataset=cfg.dataset,
            analysis_type=analysis_type,
            pattern=cfg.output.filename_pattern,
            timestamp_format=cfg.output.timestamp_format,
        )
        out_path = out_root / output_name
        write_parquet_frame(
            frame=frame,
            output_path=out_path,
            compression=cfg.output.parquet_compression,
            index=cfg.output.parquet_index,
        )
        written_files[analysis_type] = str(out_path)

    return {
        "dataset": cfg.dataset,
        "cleaned_root": str(resolved_input),
        "n_cleaned_files": len(latest_files),
        "n_source_h5_files": len(h5_catalog),
        "n_subject_metric_rows": int(len(subject_metrics)),
        "n_contrast_rows": int(len(contrast_results)),
        "written_files": written_files,
        "skipped": skipped,
        "errors": errors,
    }
