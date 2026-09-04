from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
DATASET_ROOT = REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds007526_20260610_121725"
PARTICIPANTS_PATH = ARTICLE_DIR / "metadata" / "participants.tsv"
RESULT_STAMP = "20260610"
RESULTS_DIR = ARTICLE_DIR / "results" / f"parkinson_walking_{RESULT_STAMP}"
INVENTORY_DIR = RESULTS_DIR / "inventory"
CONTRASTS_DIR = RESULTS_DIR / "contrasts"
CLINICAL_DIR = RESULTS_DIR / "clinical_associations"
RUN_METRICS_CSV = "run_metrics.csv"
RUN_SLUG_RE = re.compile(r"^(?P<participant_id>sub-\d+)_(?P<task>rest|walk)$")
TASK_ORDER: tuple[str, ...] = ("rest", "walk")
GROUP_ORDER: tuple[str, ...] = ("HC", "PD")
NETWORK_ORDER: tuple[str, ...] = ("frontal", "central", "parietal_occipital", "temporal")
MNPS_AXIS_NAMES: tuple[str, ...] = ("m", "d", "e")
STRATIFIED_AXIS_NAMES: tuple[str, ...] = ("m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m")
NUMERIC_PARTICIPANT_COLUMNS: tuple[str, ...] = (
    "updrs_part_iii",
    "updrs_total",
    "moca",
    "age",
    "disease_duration",
    "ledd",
    "pigd_score",
    "td_score",
    "ctt",
)
PD_CLINICAL_COLUMNS: tuple[str, ...] = (
    "updrs_part_iii",
    "updrs_total",
    "moca",
    "disease_duration",
    "ledd",
    "pigd_score",
    "td_score",
    "ctt",
    "age",
)
RUN_CONTEXT_COLUMNS: tuple[str, ...] = (
    "participant_id",
    "source_subject_code",
    "group",
    "task",
    "sex",
    "age",
    "dataset_id",
    "h5_path",
    "n_timepoints",
    "n_jacobian_windows",
    "coverage_seconds_effective",
    "epochs_raw",
    "epochs_after_qc",
)
EPS = 1e-12
ANCHOR_OPTIONS: tuple[str, ...] = ("auto", "cohort", "subject")
TRAJECTORY_PRIMARY_METRICS: tuple[str, ...] = (
    "entropy_rate",
    "irreversibility",
    "noetic_action",
    "curvature_median",
    "tortuosity",
)
TRAJECTORY_SUPPORTIVE_METRICS: tuple[str, ...] = (
    "entropy_production",
    "self_loop_rate",
    "transition_sparsity",
    "noetic_action_kinetic",
    "noetic_action_jerk",
    "noetic_action_potential",
    "path_length",
)
TRAJECTORY_ALL_METRICS: tuple[str, ...] = TRAJECTORY_PRIMARY_METRICS + TRAJECTORY_SUPPORTIVE_METRICS


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def fmt(value: object, digits: int = 4) -> str:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return "nan"
    if not np.isfinite(parsed):
        return "nan"
    return f"{parsed:.{digits}g}"


def decode_scalar(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return decode_scalar(value.item())
        return [decode_scalar(item) for item in value.tolist()]
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        try:
            return bytes(value).decode("utf-8")
        except Exception:
            return str(value)
    if isinstance(value, np.generic):
        return value.item()
    return value


def read_json_dict(handle: h5py.File, path: str) -> dict[str, Any]:
    if path not in handle:
        return {}
    raw = handle[path][()]
    decoded = decode_scalar(raw)
    if decoded in (None, ""):
        return {}
    try:
        parsed = json.loads(str(decoded))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def base_h5_metadata_from_handle(handle: h5py.File, h5_path: Path) -> dict[str, Any]:
    attrs = {key: decode_scalar(value) for key, value in handle.attrs.items()}
    mapped_json = read_json_dict(handle, "participant/mapped_json")

    def _pick(key: str, *fallback_attr_keys: str) -> str | None:
        value = mapped_json.get(key)
        if value is not None and str(value).strip():
            return str(value)
        for fallback_key in (key,) + fallback_attr_keys:
            value = attrs.get(fallback_key)
            if value is not None:
                return str(value)
        return None

    return {
        "dataset_id": str(attrs.get("dataset_id")) if attrs.get("dataset_id") is not None else None,
        "subject_id": str(attrs.get("subject_id")) if attrs.get("subject_id") is not None else h5_path.stem,
        "session": str(attrs.get("session")) if attrs.get("session") is not None else None,
        "run": str(attrs.get("run") or "run-01"),
        "acq": str(attrs.get("acq")) if attrs.get("acq") is not None else None,
        "group": _pick("group", "meta_group", "meta_type", "type"),
        "condition": _pick("condition"),
        "task": _pick("task"),
        "modality": str(attrs.get("modality")) if attrs.get("modality") is not None else None,
        "source_h5_path": str(h5_path),
        "source_dataset_path": "/manifest_json",
    }


def parse_run_slug(h5_path: Path) -> dict[str, str]:
    match = RUN_SLUG_RE.match(h5_path.stem)
    if not match:
        raise ValueError(f"Could not parse run slug from {h5_path.name}.")
    return match.groupdict()


def list_h5_paths(dataset_root: Path = DATASET_ROOT) -> list[Path]:
    return sorted(dataset_root.glob("sub-*_*/*.h5"))


def load_participants(participants_path: Path = PARTICIPANTS_PATH) -> pd.DataFrame:
    participants = pd.read_csv(participants_path, sep="\t", na_values=["n/a", "N/A", "NA", ""])
    participants = participants.rename(columns={"subject_id": "source_subject_code"}).copy()
    participants["group"] = participants["group"].astype(str).str.strip()
    participants["sex"] = participants["sex"].astype("string")
    for column in NUMERIC_PARTICIPANT_COLUMNS:
        participants[column] = pd.to_numeric(participants[column], errors="coerce")
    participants["sex_numeric"] = participants["sex"].map({"F": 1.0, "M": 0.0}).astype(float)
    return participants


def participant_lookup(participants: pd.DataFrame) -> dict[str, dict[str, Any]]:
    rows = participants.to_dict(orient="records")
    return {str(row["participant_id"]): row for row in rows}


def robust_mean(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float).reshape(-1)
    arr = arr[np.isfinite(arr)]
    return float(arr.mean()) if arr.size else float("nan")


def robust_median(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float).reshape(-1)
    arr = arr[np.isfinite(arr)]
    return float(np.median(arr)) if arr.size else float("nan")


def robust_std(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float).reshape(-1)
    arr = arr[np.isfinite(arr)]
    return float(arr.std(ddof=1)) if arr.size >= 2 else float("nan")


def robust_iqr(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float).reshape(-1)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return float("nan")
    q25, q75 = np.percentile(arr, [25.0, 75.0])
    return float(q75 - q25)


def robust_mad(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float).reshape(-1)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return float("nan")
    med = np.median(arr)
    return float(np.median(np.abs(arr - med)))


def _first_existing_array(handle: h5py.File, paths: list[str]) -> tuple[np.ndarray | None, str | None]:
    for path in paths:
        if path in handle:
            return np.asarray(handle[path], dtype=float), path
    return None, None


def _normalize_anchor(anchor: str) -> str:
    normalized = str(anchor).strip().lower()
    if normalized not in ANCHOR_OPTIONS:
        raise ValueError(f"Unsupported anchor {anchor!r}; expected one of {ANCHOR_OPTIONS}.")
    return normalized


def _array_paths_for_anchor(kind: str, anchor: str) -> list[str]:
    normalized = _normalize_anchor(anchor)
    if kind == "coords3":
        anchor_specific = {
            "cohort": ["coords_3d_cohort_anchored/values"],
            "subject": ["coords_3d_subject_anchored/values"],
            "auto": [],
        }[normalized]
        return [*anchor_specific, "mnps_3d"]
    if kind == "coords9":
        anchor_specific = {
            "cohort": ["coords_9d_cohort_anchored/values"],
            "subject": ["coords_9d_subject_anchored/values"],
            "auto": [],
        }[normalized]
        return [*anchor_specific, "coords_9d/values"]
    if kind == "jac3":
        anchor_specific = {
            "cohort": ["jacobian_cohort_anchored/J_hat"],
            "subject": ["jacobian_subject_anchored/J_hat"],
            "auto": [],
        }[normalized]
        return [*anchor_specific, "jacobian/J_hat"]
    if kind == "jac9":
        anchor_specific = {
            "cohort": ["jacobian_9D_cohort_anchored/J_hat"],
            "subject": ["jacobian_9D_subject_anchored/J_hat"],
            "auto": [],
        }[normalized]
        return [*anchor_specific, "jacobian_9D/J_hat"]
    raise ValueError(f"Unsupported array kind {kind!r}.")


def _regional_array_paths_for_anchor(network: str, kind: str, anchor: str) -> list[str]:
    normalized = _normalize_anchor(anchor)
    root = f"regional_mnps/{network}"
    if kind == "coords3":
        anchor_specific = {
            "cohort": [f"{root}/cohort_anchored/mnps"],
            "subject": [f"{root}/subject_anchored/mnps"],
            "auto": [],
        }[normalized]
        return [*anchor_specific, f"{root}/mnps"]
    if kind == "coords9":
        anchor_specific = {
            "cohort": [f"{root}/cohort_anchored/stratified"],
            "subject": [f"{root}/subject_anchored/stratified"],
            "auto": [],
        }[normalized]
        return [*anchor_specific, f"{root}/stratified"]
    if kind == "jac3":
        anchor_specific = {
            "cohort": [f"{root}/cohort_anchored/jacobian"],
            "subject": [f"{root}/subject_anchored/jacobian"],
            "auto": [],
        }[normalized]
        return [*anchor_specific, f"{root}/jacobian"]
    raise ValueError(f"Unsupported regional array kind {kind!r}.")


def _matrix_sequence_summary(mats: np.ndarray, prefix: str) -> dict[str, float]:
    seq = np.asarray(mats, dtype=float)
    if seq.ndim != 3 or seq.shape[1] != seq.shape[2] or seq.shape[0] == 0:
        return {
            f"{prefix}_trace_median": float("nan"),
            f"{prefix}_trace_iqr": float("nan"),
            f"{prefix}_trace_mad": float("nan"),
            f"{prefix}_frobenius_median": float("nan"),
            f"{prefix}_frobenius_iqr": float("nan"),
            f"{prefix}_frobenius_mad": float("nan"),
            f"{prefix}_spectral_radius_median": float("nan"),
            f"{prefix}_spectral_radius_iqr": float("nan"),
            f"{prefix}_spectral_radius_mad": float("nan"),
            f"{prefix}_rotation_norm_median": float("nan"),
            f"{prefix}_rotation_norm_iqr": float("nan"),
            f"{prefix}_rotation_norm_mad": float("nan"),
            f"{prefix}_anisotropy_abs_eig_median": float("nan"),
            f"{prefix}_anisotropy_abs_eig_iqr": float("nan"),
            f"{prefix}_anisotropy_abs_eig_mad": float("nan"),
        }
    valid = np.isfinite(seq).all(axis=(1, 2))
    seq = seq[valid]
    if seq.shape[0] == 0:
        return {
            f"{prefix}_trace_median": float("nan"),
            f"{prefix}_trace_iqr": float("nan"),
            f"{prefix}_trace_mad": float("nan"),
            f"{prefix}_frobenius_median": float("nan"),
            f"{prefix}_frobenius_iqr": float("nan"),
            f"{prefix}_frobenius_mad": float("nan"),
            f"{prefix}_spectral_radius_median": float("nan"),
            f"{prefix}_spectral_radius_iqr": float("nan"),
            f"{prefix}_spectral_radius_mad": float("nan"),
            f"{prefix}_rotation_norm_median": float("nan"),
            f"{prefix}_rotation_norm_iqr": float("nan"),
            f"{prefix}_rotation_norm_mad": float("nan"),
            f"{prefix}_anisotropy_abs_eig_median": float("nan"),
            f"{prefix}_anisotropy_abs_eig_iqr": float("nan"),
            f"{prefix}_anisotropy_abs_eig_mad": float("nan"),
        }
    trace = np.trace(seq, axis1=1, axis2=2)
    frobenius = np.linalg.norm(seq, axis=(1, 2))
    antisym = 0.5 * (seq - np.swapaxes(seq, 1, 2))
    rotation = np.linalg.norm(antisym, axis=(1, 2))
    eigvals = np.linalg.eigvals(seq)
    abs_eigs = np.abs(eigvals)
    spectral_radius = np.nanmax(abs_eigs, axis=1)
    anisotropy = np.nanmax(abs_eigs, axis=1) / np.maximum(np.nanmean(abs_eigs, axis=1), EPS)
    return {
        f"{prefix}_trace_median": robust_median(trace),
        f"{prefix}_trace_iqr": robust_iqr(trace),
        f"{prefix}_trace_mad": robust_mad(trace),
        f"{prefix}_frobenius_median": robust_median(frobenius),
        f"{prefix}_frobenius_iqr": robust_iqr(frobenius),
        f"{prefix}_frobenius_mad": robust_mad(frobenius),
        f"{prefix}_spectral_radius_median": robust_median(spectral_radius),
        f"{prefix}_spectral_radius_iqr": robust_iqr(spectral_radius),
        f"{prefix}_spectral_radius_mad": robust_mad(spectral_radius),
        f"{prefix}_rotation_norm_median": robust_median(rotation),
        f"{prefix}_rotation_norm_iqr": robust_iqr(rotation),
        f"{prefix}_rotation_norm_mad": robust_mad(rotation),
        f"{prefix}_anisotropy_abs_eig_median": robust_median(anisotropy),
        f"{prefix}_anisotropy_abs_eig_iqr": robust_iqr(anisotropy),
        f"{prefix}_anisotropy_abs_eig_mad": robust_mad(anisotropy),
    }


def path_length(coords: np.ndarray) -> float:
    arr = np.asarray(coords, dtype=float)
    if arr.ndim != 2 or arr.shape[0] < 2:
        return float("nan")
    return float(np.sum(np.linalg.norm(np.diff(arr, axis=0), axis=1)))


def tortuosity(coords: np.ndarray) -> float:
    arr = np.asarray(coords, dtype=float)
    if arr.ndim != 2 or arr.shape[0] < 2:
        return float("nan")
    total = path_length(arr)
    displacement = float(np.linalg.norm(arr[-1] - arr[0]))
    if not np.isfinite(total) or not np.isfinite(displacement):
        return float("nan")
    return float(total / max(displacement, EPS))


def curvature_series(coords: np.ndarray, time: np.ndarray) -> np.ndarray:
    arr = np.asarray(coords, dtype=float)
    time = np.asarray(time, dtype=float).reshape(-1)
    if arr.shape[0] < 3 or time.size < 3:
        return np.zeros((0,), dtype=float)
    curves: list[float] = []
    for idx in range(1, arr.shape[0] - 1):
        dt_prev = float(time[idx] - time[idx - 1])
        dt_next = float(time[idx + 1] - time[idx])
        if not np.isfinite(dt_prev) or not np.isfinite(dt_next) or dt_prev <= 0 or dt_next <= 0:
            continue
        v_prev = (arr[idx] - arr[idx - 1]) / dt_prev
        v_next = (arr[idx + 1] - arr[idx]) / dt_next
        v = 0.5 * (v_prev + v_next)
        dt_center = 0.5 * (dt_prev + dt_next)
        a = (v_next - v_prev) / max(dt_center, EPS)
        numer = np.linalg.norm(v) ** 2 * np.linalg.norm(a) ** 2 - float(np.dot(v, a)) ** 2
        denom = max(np.linalg.norm(v) ** 3, EPS)
        curves.append(math.sqrt(max(numer, 0.0)) / denom)
    return np.asarray(curves, dtype=float)


def stable_variance_metric(sampled_coords: np.ndarray) -> np.ndarray:
    coords = np.asarray(sampled_coords, dtype=float)
    var = np.nanvar(coords, axis=0, ddof=1)
    var = np.where(np.isfinite(var) & (var > EPS), var, 1.0)
    return 1.0 / var


def weighted_quad(vecs: np.ndarray, metric_diag: np.ndarray) -> np.ndarray:
    return np.sum((vecs * vecs) * metric_diag[None, :], axis=1)


def family_projection(coords: np.ndarray) -> np.ndarray:
    arr = np.asarray(coords, dtype=float)
    if arr.ndim != 2:
        raise ValueError("coords must be 2D.")
    if arr.shape[1] == 3:
        return arr[:, :3]
    if arr.shape[1] >= 9:
        return np.column_stack(
            [
                np.nanmean(arr[:, 0:3], axis=1),
                np.nanmean(arr[:, 3:6], axis=1),
                np.nanmean(arr[:, 6:9], axis=1),
            ]
        )
    raise ValueError(f"Unsupported coordinate width {arr.shape[1]}.")


def potential_from_coords(coords: np.ndarray) -> np.ndarray:
    projected = family_projection(np.asarray(coords, dtype=float))
    return projected[:, 2] - projected[:, 0] + projected[:, 1]


def noetic_action_metrics(coords: np.ndarray, time: np.ndarray, *, metric_diag: np.ndarray) -> dict[str, float]:
    coords = np.asarray(coords, dtype=float)
    time = np.asarray(time, dtype=float)
    nan_result = {metric: float("nan") for metric in ("noetic_action", "noetic_action_kinetic", "noetic_action_jerk", "noetic_action_potential")}
    if len(coords) < 3 or len(time) < 3:
        return nan_result
    dt_prev = time[1:-1] - time[:-2]
    dt_next = time[2:] - time[1:-1]
    valid = np.isfinite(dt_prev) & np.isfinite(dt_next) & (dt_prev > 0) & (dt_next > 0)
    if not valid.any():
        return nan_result
    delta = coords[2:] - coords[1:-1]
    delta2 = coords[2:] - 2.0 * coords[1:-1] + coords[:-2]
    dt_center = 0.5 * (dt_prev + dt_next)
    potential = potential_from_coords(coords[1:-1])
    delta = delta[valid]
    delta2 = delta2[valid]
    dt_next = dt_next[valid]
    dt_center = dt_center[valid]
    potential = potential[valid]
    kinetic_density = 0.5 * weighted_quad(delta, metric_diag) / np.maximum(dt_next, EPS) ** 2
    jerk_density = weighted_quad(delta2, metric_diag) / np.maximum(dt_center, EPS) ** 4
    potential_density = potential
    total_density = kinetic_density + jerk_density + potential_density
    return {
        "noetic_action": robust_median(total_density),
        "noetic_action_kinetic": robust_median(kinetic_density),
        "noetic_action_jerk": robust_median(jerk_density),
        "noetic_action_potential": robust_median(potential_density),
    }


def repertoire_metrics(states: np.ndarray, *, n_states: int) -> dict[str, float]:
    states = np.asarray(states, dtype=int).reshape(-1)
    if len(states) < 9:
        return {
            "entropy_rate": float("nan"),
            "irreversibility": float("nan"),
            "entropy_production": float("nan"),
            "self_loop_rate": float("nan"),
            "transition_sparsity": float("nan"),
        }
    transition_counts = np.zeros((n_states, n_states), dtype=float)
    for src, dst in zip(states[:-1], states[1:], strict=False):
        transition_counts[int(src), int(dst)] += 1.0
    occupancy = np.bincount(states, minlength=n_states).astype(float)
    if occupancy.sum() <= 0:
        return {
            "entropy_rate": float("nan"),
            "irreversibility": float("nan"),
            "entropy_production": float("nan"),
            "self_loop_rate": float("nan"),
            "transition_sparsity": float("nan"),
        }
    pi = occupancy / occupancy.sum()
    row_sums = transition_counts.sum(axis=1, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        transition_prob = np.divide(transition_counts, row_sums, out=np.zeros_like(transition_counts), where=row_sums > 0)
    entropy_rate = -np.sum(pi[:, None] * transition_prob * np.log(transition_prob + EPS))
    flow = pi[:, None] * transition_prob
    irreversibility = 0.5 * np.sum(np.abs(flow - flow.T))
    entropy_production = np.sum(flow * np.log((flow + EPS) / (flow.T + EPS)))
    self_loop_rate = float(np.sum(pi * np.diag(transition_prob)))
    transition_sparsity = float(1.0 - (np.count_nonzero(transition_counts) / transition_counts.size))
    return {
        "entropy_rate": float(entropy_rate),
        "irreversibility": float(irreversibility),
        "entropy_production": float(entropy_production),
        "self_loop_rate": self_loop_rate,
        "transition_sparsity": transition_sparsity,
    }


def sample_evenly(coords: np.ndarray, max_points: int) -> np.ndarray:
    arr = np.asarray(coords, dtype=float)
    if arr.shape[0] <= max_points:
        return arr
    indices = np.linspace(0, arr.shape[0] - 1, num=max_points, dtype=int)
    return arr[indices]


def run_metric_columns() -> list[str]:
    columns: list[str] = []
    for axis in MNPS_AXIS_NAMES:
        columns.extend([f"{axis}_mean", f"{axis}_median", f"{axis}_std", f"{axis}_iqr", f"{axis}_mad"])
    for axis in STRATIFIED_AXIS_NAMES:
        columns.extend([f"{axis}_mean", f"{axis}_median", f"{axis}_iqr", f"{axis}_mad"])
    columns.extend(
        [
            "jac3_trace_median",
            "jac3_trace_iqr",
            "jac3_trace_mad",
            "jac3_frobenius_median",
            "jac3_frobenius_iqr",
            "jac3_frobenius_mad",
            "jac3_spectral_radius_median",
            "jac3_spectral_radius_iqr",
            "jac3_spectral_radius_mad",
            "jac3_rotation_norm_median",
            "jac3_rotation_norm_iqr",
            "jac3_rotation_norm_mad",
            "jac3_anisotropy_abs_eig_median",
            "jac3_anisotropy_abs_eig_iqr",
            "jac3_anisotropy_abs_eig_mad",
            "jac9_trace_median",
            "jac9_trace_iqr",
            "jac9_trace_mad",
            "jac9_frobenius_median",
            "jac9_frobenius_iqr",
            "jac9_frobenius_mad",
            "jac9_spectral_radius_median",
            "jac9_spectral_radius_iqr",
            "jac9_spectral_radius_mad",
            "jac9_rotation_norm_median",
            "jac9_rotation_norm_iqr",
            "jac9_rotation_norm_mad",
            "jac9_anisotropy_abs_eig_median",
            "jac9_anisotropy_abs_eig_iqr",
            "jac9_anisotropy_abs_eig_mad",
        ]
    )
    return columns


RUN_METRIC_COLUMNS = run_metric_columns()


def regional_run_metric_columns() -> list[str]:
    columns: list[str] = []
    for axis in MNPS_AXIS_NAMES:
        columns.extend([f"{axis}_mean", f"{axis}_median", f"{axis}_std", f"{axis}_iqr", f"{axis}_mad"])
    for axis in STRATIFIED_AXIS_NAMES:
        columns.extend([f"{axis}_mean", f"{axis}_median", f"{axis}_iqr", f"{axis}_mad"])
    columns.extend(
        [
            "jac3_trace_median",
            "jac3_trace_iqr",
            "jac3_trace_mad",
            "jac3_frobenius_median",
            "jac3_frobenius_iqr",
            "jac3_frobenius_mad",
            "jac3_spectral_radius_median",
            "jac3_spectral_radius_iqr",
            "jac3_spectral_radius_mad",
            "jac3_rotation_norm_median",
            "jac3_rotation_norm_iqr",
            "jac3_rotation_norm_mad",
            "jac3_anisotropy_abs_eig_median",
            "jac3_anisotropy_abs_eig_iqr",
            "jac3_anisotropy_abs_eig_mad",
        ]
    )
    return columns


REGIONAL_RUN_METRIC_COLUMNS = regional_run_metric_columns()


def summarize_run(h5_path: Path, participants_by_id: dict[str, dict[str, Any]], *, anchor: str = "auto") -> dict[str, Any]:
    parsed = parse_run_slug(h5_path)
    participant_id = parsed["participant_id"]
    participant_row = participants_by_id.get(participant_id, {})
    anchor = _normalize_anchor(anchor)

    with h5py.File(h5_path, "r") as handle:
        attrs = {key: decode_scalar(value) for key, value in handle.attrs.items()}
        mapped_json = read_json_dict(handle, "participant/mapped_json")
        row_json = read_json_dict(handle, "participant/row_json")

        task = str(attrs.get("task") or mapped_json.get("task") or parsed["task"])
        group = str(
            participant_row.get("group")
            or attrs.get("meta_group")
            or mapped_json.get("group")
            or row_json.get("group")
            or attrs.get("group")
            or ""
        )
        group = group.strip() or "unknown"
        coords_3d, coords_3d_path = _first_existing_array(handle, _array_paths_for_anchor("coords3", anchor))
        coords_9d, coords_9d_path = _first_existing_array(handle, _array_paths_for_anchor("coords9", anchor))
        jac3, jac3_path = _first_existing_array(handle, _array_paths_for_anchor("jac3", anchor))
        jac9, jac9_path = _first_existing_array(handle, _array_paths_for_anchor("jac9", anchor))
        time = np.asarray(handle["time"], dtype=float) if "time" in handle else np.full((0,), np.nan)

    out: dict[str, Any] = {
        "participant_id": participant_id,
        "source_subject_code": participant_row.get("source_subject_code") or attrs.get("meta_subject_id"),
        "group": group,
        "task": task,
        "sex": participant_row.get("sex") or attrs.get("meta_sex"),
        "dataset_id": attrs.get("dataset_id"),
        "h5_path": str(h5_path),
        "anchor_mode_requested": anchor,
        "primary_coordinate_contract": attrs.get("primary_coordinate_contract"),
        "primary_coordinate_layer": attrs.get("primary_coordinate_layer"),
        "coords_3d_path": coords_3d_path,
        "coords_9d_path": coords_9d_path,
        "jac3_path": jac3_path,
        "jac9_path": jac9_path,
        "n_timepoints": int(time.shape[0]),
        "n_jacobian_windows": int(jac3.shape[0]) if isinstance(jac3, np.ndarray) and jac3.ndim == 3 else 0,
        "coverage_seconds_effective": pd.to_numeric(pd.Series([attrs.get("coverage_seconds_effective")]), errors="coerce").iloc[0],
        "epochs_raw": pd.to_numeric(pd.Series([attrs.get("epochs_raw")]), errors="coerce").iloc[0],
        "epochs_after_qc": pd.to_numeric(pd.Series([attrs.get("epochs_after_qc")]), errors="coerce").iloc[0],
    }

    for column in NUMERIC_PARTICIPANT_COLUMNS:
        out[column] = participant_row.get(column, float("nan"))
    out["sex_numeric"] = participant_row.get("sex_numeric", float("nan"))

    if isinstance(coords_3d, np.ndarray) and coords_3d.ndim == 2 and coords_3d.shape[1] >= 3:
        for axis_idx, axis_name in enumerate(MNPS_AXIS_NAMES):
            axis_values = coords_3d[:, axis_idx]
            out[f"{axis_name}_mean"] = robust_mean(axis_values)
            out[f"{axis_name}_median"] = robust_median(axis_values)
            out[f"{axis_name}_std"] = robust_std(axis_values)
            out[f"{axis_name}_iqr"] = robust_iqr(axis_values)
            out[f"{axis_name}_mad"] = robust_mad(axis_values)
    else:
        for axis_name in MNPS_AXIS_NAMES:
            out[f"{axis_name}_mean"] = float("nan")
            out[f"{axis_name}_median"] = float("nan")
            out[f"{axis_name}_std"] = float("nan")
            out[f"{axis_name}_iqr"] = float("nan")
            out[f"{axis_name}_mad"] = float("nan")

    if isinstance(coords_9d, np.ndarray) and coords_9d.ndim == 2 and coords_9d.shape[1] >= 9:
        for axis_idx, axis_name in enumerate(STRATIFIED_AXIS_NAMES):
            axis_values = coords_9d[:, axis_idx]
            out[f"{axis_name}_mean"] = robust_mean(axis_values)
            out[f"{axis_name}_median"] = robust_median(axis_values)
            out[f"{axis_name}_iqr"] = robust_iqr(axis_values)
            out[f"{axis_name}_mad"] = robust_mad(axis_values)
    else:
        for axis_name in STRATIFIED_AXIS_NAMES:
            out[f"{axis_name}_mean"] = float("nan")
            out[f"{axis_name}_median"] = float("nan")
            out[f"{axis_name}_iqr"] = float("nan")
            out[f"{axis_name}_mad"] = float("nan")

    out.update(_matrix_sequence_summary(jac3 if isinstance(jac3, np.ndarray) else np.asarray([]), "jac3"))
    out.update(_matrix_sequence_summary(jac9 if isinstance(jac9, np.ndarray) else np.asarray([]), "jac9"))
    return out


def summarize_regional_run(
    h5_path: Path,
    participants_by_id: dict[str, dict[str, Any]],
    *,
    anchor: str = "auto",
) -> list[dict[str, Any]]:
    parsed = parse_run_slug(h5_path)
    participant_id = parsed["participant_id"]
    participant_row = participants_by_id.get(participant_id, {})
    anchor = _normalize_anchor(anchor)

    with h5py.File(h5_path, "r") as handle:
        attrs = {key: decode_scalar(value) for key, value in handle.attrs.items()}
        mapped_json = read_json_dict(handle, "participant/mapped_json")
        row_json = read_json_dict(handle, "participant/row_json")
        task = str(attrs.get("task") or mapped_json.get("task") or parsed["task"])
        group = str(
            participant_row.get("group")
            or attrs.get("meta_group")
            or mapped_json.get("group")
            or row_json.get("group")
            or attrs.get("group")
            or ""
        )
        group = group.strip() or "unknown"
        rows: list[dict[str, Any]] = []
        for network in NETWORK_ORDER:
            coords_3d, coords_3d_path = _first_existing_array(handle, _regional_array_paths_for_anchor(network, "coords3", anchor))
            coords_9d, coords_9d_path = _first_existing_array(handle, _regional_array_paths_for_anchor(network, "coords9", anchor))
            jac3, jac3_path = _first_existing_array(handle, _regional_array_paths_for_anchor(network, "jac3", anchor))
            if coords_3d is None and coords_9d is None and jac3 is None:
                continue
            out: dict[str, Any] = {
                "participant_id": participant_id,
                "source_subject_code": participant_row.get("source_subject_code") or attrs.get("meta_subject_id"),
                "group": group,
                "task": task,
                "sex": participant_row.get("sex") or attrs.get("meta_sex"),
                "dataset_id": attrs.get("dataset_id"),
                "network": network,
                "h5_path": str(h5_path),
                "anchor_mode_requested": anchor,
                "primary_coordinate_contract": attrs.get("primary_coordinate_contract"),
                "primary_coordinate_layer": attrs.get("primary_coordinate_layer"),
                "coords_3d_path": coords_3d_path,
                "coords_9d_path": coords_9d_path,
                "jac3_path": jac3_path,
            }
            for column in NUMERIC_PARTICIPANT_COLUMNS:
                out[column] = participant_row.get(column, float("nan"))
            out["sex_numeric"] = participant_row.get("sex_numeric", float("nan"))
            if isinstance(coords_3d, np.ndarray) and coords_3d.ndim == 2 and coords_3d.shape[1] >= 3:
                for axis_idx, axis_name in enumerate(MNPS_AXIS_NAMES):
                    axis_values = coords_3d[:, axis_idx]
                    out[f"{axis_name}_mean"] = robust_mean(axis_values)
                    out[f"{axis_name}_median"] = robust_median(axis_values)
                    out[f"{axis_name}_std"] = robust_std(axis_values)
                    out[f"{axis_name}_iqr"] = robust_iqr(axis_values)
                    out[f"{axis_name}_mad"] = robust_mad(axis_values)
            else:
                for axis_name in MNPS_AXIS_NAMES:
                    out[f"{axis_name}_mean"] = float("nan")
                    out[f"{axis_name}_median"] = float("nan")
                    out[f"{axis_name}_std"] = float("nan")
                    out[f"{axis_name}_iqr"] = float("nan")
                    out[f"{axis_name}_mad"] = float("nan")
            if isinstance(coords_9d, np.ndarray) and coords_9d.ndim == 2 and coords_9d.shape[1] >= 9:
                for axis_idx, axis_name in enumerate(STRATIFIED_AXIS_NAMES):
                    axis_values = coords_9d[:, axis_idx]
                    out[f"{axis_name}_mean"] = robust_mean(axis_values)
                    out[f"{axis_name}_median"] = robust_median(axis_values)
                    out[f"{axis_name}_iqr"] = robust_iqr(axis_values)
                    out[f"{axis_name}_mad"] = robust_mad(axis_values)
            else:
                for axis_name in STRATIFIED_AXIS_NAMES:
                    out[f"{axis_name}_mean"] = float("nan")
                    out[f"{axis_name}_median"] = float("nan")
                    out[f"{axis_name}_iqr"] = float("nan")
                    out[f"{axis_name}_mad"] = float("nan")
            out.update(_matrix_sequence_summary(jac3 if isinstance(jac3, np.ndarray) else np.asarray([]), "jac3"))
            rows.append(out)
    return rows


def build_run_metrics_frame(
    dataset_root: Path = DATASET_ROOT,
    participants_path: Path = PARTICIPANTS_PATH,
    *,
    anchor: str = "auto",
) -> pd.DataFrame:
    participants = load_participants(participants_path)
    participants_by_id = participant_lookup(participants)
    rows = [summarize_run(h5_path, participants_by_id, anchor=anchor) for h5_path in list_h5_paths(dataset_root)]
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    for column in RUN_METRIC_COLUMNS + list(NUMERIC_PARTICIPANT_COLUMNS) + ["sex_numeric", "coverage_seconds_effective", "epochs_raw", "epochs_after_qc"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["group"] = pd.Categorical(frame["group"], categories=GROUP_ORDER, ordered=True)
    frame["task"] = pd.Categorical(frame["task"], categories=TASK_ORDER, ordered=True)
    return frame.sort_values(["group", "participant_id", "task"], na_position="last").reset_index(drop=True)


def build_regional_run_metrics_frame(
    dataset_root: Path = DATASET_ROOT,
    participants_path: Path = PARTICIPANTS_PATH,
    *,
    anchor: str = "auto",
) -> pd.DataFrame:
    participants = load_participants(participants_path)
    participants_by_id = participant_lookup(participants)
    rows: list[dict[str, Any]] = []
    for h5_path in list_h5_paths(dataset_root):
        rows.extend(summarize_regional_run(h5_path, participants_by_id, anchor=anchor))
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    for column in REGIONAL_RUN_METRIC_COLUMNS + list(NUMERIC_PARTICIPANT_COLUMNS) + ["sex_numeric"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["group"] = pd.Categorical(frame["group"], categories=GROUP_ORDER, ordered=True)
    frame["task"] = pd.Categorical(frame["task"], categories=TASK_ORDER, ordered=True)
    frame["network"] = pd.Categorical(frame["network"], categories=NETWORK_ORDER, ordered=True)
    return frame.sort_values(["group", "participant_id", "task", "network"], na_position="last").reset_index(drop=True)


def load_or_build_run_metrics(
    csv_path: Path,
    *,
    dataset_root: Path = DATASET_ROOT,
    participants_path: Path = PARTICIPANTS_PATH,
    rebuild: bool = False,
    anchor: str = "auto",
) -> pd.DataFrame:
    anchor = _normalize_anchor(anchor)
    if csv_path.exists() and not rebuild:
        frame = pd.read_csv(csv_path, low_memory=False)
        if "group" in frame.columns:
            frame["group"] = pd.Categorical(frame["group"], categories=GROUP_ORDER, ordered=True)
        if "task" in frame.columns:
            frame["task"] = pd.Categorical(frame["task"], categories=TASK_ORDER, ordered=True)
        return frame
    frame = build_run_metrics_frame(dataset_root=dataset_root, participants_path=participants_path, anchor=anchor)
    ensure_dir(csv_path.parent)
    frame.to_csv(csv_path, index=False)
    return frame


def load_or_build_regional_run_metrics(
    csv_path: Path,
    *,
    dataset_root: Path = DATASET_ROOT,
    participants_path: Path = PARTICIPANTS_PATH,
    rebuild: bool = False,
    anchor: str = "auto",
) -> pd.DataFrame:
    anchor = _normalize_anchor(anchor)
    if csv_path.exists() and not rebuild:
        frame = pd.read_csv(csv_path, low_memory=False)
        if "group" in frame.columns:
            frame["group"] = pd.Categorical(frame["group"], categories=GROUP_ORDER, ordered=True)
        if "task" in frame.columns:
            frame["task"] = pd.Categorical(frame["task"], categories=TASK_ORDER, ordered=True)
        if "network" in frame.columns:
            frame["network"] = pd.Categorical(frame["network"], categories=NETWORK_ORDER, ordered=True)
        return frame
    frame = build_regional_run_metrics_frame(dataset_root=dataset_root, participants_path=participants_path, anchor=anchor)
    ensure_dir(csv_path.parent)
    frame.to_csv(csv_path, index=False)
    return frame


def bh_fdr(values: pd.Series) -> pd.Series:
    arr = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    mask = np.isfinite(arr)
    if not mask.any():
        return pd.Series(out, index=values.index, dtype=float)
    valid = arr[mask]
    order = np.argsort(valid)
    ranked = valid[order]
    n = ranked.size
    adjusted = ranked * n / np.arange(1, n + 1, dtype=float)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    back = np.empty_like(adjusted)
    back[order] = adjusted
    out[np.where(mask)[0]] = back
    return pd.Series(out, index=values.index, dtype=float)


def cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    left = left[np.isfinite(left)]
    right = right[np.isfinite(right)]
    if left.size < 2 or right.size < 2:
        return float("nan")
    pooled = ((left.size - 1) * np.var(left, ddof=1) + (right.size - 1) * np.var(right, ddof=1)) / (left.size + right.size - 2)
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(right) - np.mean(left)) / math.sqrt(pooled))


def cohens_dz(diff: np.ndarray) -> float:
    diff = np.asarray(diff, dtype=float)
    diff = diff[np.isfinite(diff)]
    if diff.size < 2:
        return float("nan")
    sd = float(np.std(diff, ddof=1))
    if not np.isfinite(sd) or sd <= 0:
        return float("nan")
    return float(np.mean(diff) / sd)
