from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import h5py
import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.h5_contract import read_run_contract, resolve_coords_3d, resolve_coords_9d  # noqa: E402


RESULT_STAMP = "20260602"
PRIMARY_COORDINATE_CONTRACT = "subject_anchored"
DATASET_ID = "ds004574"
DATASET_ROOT = REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds004574_20260602_062756"
RESULTS_DIR = ARTICLE_DIR / "results" / f"parkinson_auditory_recall_{RESULT_STAMP}"
STANDARD_CLEANED_DIR = RESULTS_DIR / "standard_cleaned"
STANDARD_ANALYSIS_DIR = RESULTS_DIR / "standard_analysis"
EVENT_METRIC_DIR = RESULTS_DIR / "event_metrics"
SUMMARY_PATH = RESULTS_DIR / "analysis_summary.md"
ARTICLE_METRIC_RANKING_CSV = "article_metric_ranking.csv"
ARTICLE_METRIC_SUMMARY_MD = "article_metric_summary.md"
MANIFEST_JSON = "pipeline_manifest.json"
RUN_METRICS_CSV = "event_run_metrics.csv"
SUBJECT_METRICS_CSV = "event_subject_metrics.csv"
EVENT_CONTRASTS_CSV = "event_contrasts.csv"
WRAPPER_SUMMARY_MD = "wrapper_event_summary.md"

RUN_CONFIG_PATH = NDT_ANALYSIS_ROOT / "config" / "ndt-analysis-ds004574.yaml"
ANALYZE_CONFIG_PATH = NDT_ANALYSIS_ROOT / "config" / "analysis-ds004574.yaml"

RUN_SLUG_RE = re.compile(r"^(?P<subject>sub-\d+)_(?P<condition>.+)_(?P<task>[^_]+)$")
GROUP_MAP = {
    "PD": "Parkinson",
    "CTL": "Control",
    "Parkinson": "Parkinson",
    "Control": "Control",
    "pd": "Parkinson",
    "control": "Control",
    "1": "Parkinson",
    "0": "Control",
}
DIMENSIONS: tuple[int, ...] = (3, 9)
REPERTOIRE_STATES_BY_DIM = {
    3: 12,
    9: 18,
}
MAX_POINTS_PER_SEGMENT_FOR_FIT = 64
MAX_POINTS_PER_KEY_FOR_FIT = 40000
MIN_SEGMENT_POINTS = 5
MIN_REPERTOIRE_POINTS = 8
PRE_EVENT_WINDOWS = 2
POST_EVENT_WINDOWS = 3
EPS = 1e-12
PHASE_ORDER = ("precue", "arrowcue", "response")
SUBTYPE_ORDER = ("standard", "auditory", "visual")

STRATIFIED_NAMES = [
    "m_a",
    "m_e",
    "m_o",
    "d_n",
    "d_l",
    "d_s",
    "e_e",
    "e_s",
    "e_m",
]

NUMERIC_METRIC_COLUMNS = [
    "speed_median",
    "curvature_median",
    "tortuosity",
    "path_length",
    "peak_displacement",
    "recovery_residual",
    "hysteresis_area_md",
    "hysteresis_area_me",
    "hysteresis_area_de",
    "hysteresis_area_mean",
    "entropy_rate",
    "irreversibility",
    "entropy_production",
    "self_loop_rate",
    "transition_sparsity",
    "noetic_action",
    "noetic_action_kinetic",
    "noetic_action_jerk",
    "noetic_action_potential",
]


@dataclass(frozen=True)
class SpaceKey:
    level: str
    network: str
    dim: int


@dataclass(frozen=True)
class SegmentSpec:
    label: str
    segment_kind: str
    event_subtype: str
    event_phase: str
    label_key: str | None = None


EXACT_PHASE_SEGMENTS = (
    SegmentSpec("standard_precue", "event_phase", "standard", "precue", "raw_standard_precue_onset_sec"),
    SegmentSpec("standard_arrowcue", "event_phase", "standard", "arrowcue", "raw_standard_arrowcue_onset_sec"),
    SegmentSpec("standard_response", "event_phase", "standard", "response", "raw_standard_response_onset_sec"),
    SegmentSpec("auditory_precue", "event_phase", "auditory", "precue", "raw_oddball_auditory_precue_onset_sec"),
    SegmentSpec("auditory_arrowcue", "event_phase", "auditory", "arrowcue", "raw_oddball_auditory_arrowcue_onset_sec"),
    SegmentSpec("auditory_response", "event_phase", "auditory", "response", "raw_oddball_auditory_response_onset_sec"),
    SegmentSpec("visual_precue", "event_phase", "visual", "precue", "raw_oddball_visual_precue_onset_sec"),
    SegmentSpec("visual_arrowcue", "event_phase", "visual", "arrowcue", "raw_oddball_visual_arrowcue_onset_sec"),
    SegmentSpec("visual_response", "event_phase", "visual", "response", "raw_oddball_visual_response_onset_sec"),
)

SUBTYPE_SEGMENTS = tuple(
    SegmentSpec(f"{subtype}_all", "subtype", subtype, "all")
    for subtype in SUBTYPE_ORDER
)
PHASE_SEGMENTS = tuple(
    SegmentSpec(f"all_{phase}", "phase_collapsed", "all", phase)
    for phase in PHASE_ORDER
)
SEGMENT_SPEC_BY_LABEL = {
    spec.label: spec
    for spec in (*EXACT_PHASE_SEGMENTS, *SUBTYPE_SEGMENTS, *PHASE_SEGMENTS)
}


@dataclass
class LoadedRun:
    metadata: dict[str, Any]
    time: np.ndarray
    segment_blocks: dict[str, list[np.ndarray]]
    reference_blocks: dict[str, list[np.ndarray]]
    spaces: dict[SpaceKey, dict[str, Any]]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def decode_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return decode_text(value.item())
        return json.dumps([decode_text(item) for item in value.tolist()], ensure_ascii=True)
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        try:
            return bytes(value).decode("utf-8")
        except Exception:
            return str(value)
    return str(value)


def read_json_dataset(handle: h5py.File, dataset_path: str) -> dict[str, Any]:
    if dataset_path not in handle:
        return {}
    try:
        raw = handle[dataset_path][()]
        if isinstance(raw, (bytes, bytearray, np.bytes_)):
            raw = bytes(raw).decode("utf-8")
        parsed = json.loads(str(raw))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def parse_run_slug(h5_path: Path) -> dict[str, str]:
    match = RUN_SLUG_RE.match(h5_path.stem)
    if not match:
        raise ValueError(f"Could not parse ds004574 run slug from {h5_path.name}.")
    return match.groupdict()


def contiguous_runs(indices: np.ndarray, *, max_gap: int = 1) -> list[np.ndarray]:
    values = np.unique(np.asarray(indices, dtype=int).reshape(-1))
    if values.size == 0:
        return []
    breaks = np.where(np.diff(values) > int(max_gap))[0]
    starts = np.r_[0, breaks + 1]
    ends = np.r_[breaks + 1, values.size]
    return [values[start:end] for start, end in zip(starts, ends)]


def merge_blocks(blocks: Sequence[np.ndarray]) -> list[np.ndarray]:
    if not blocks:
        return []
    merged = np.concatenate([np.asarray(block, dtype=int).reshape(-1) for block in blocks if len(block)], axis=0)
    if merged.size == 0:
        return []
    return contiguous_runs(merged, max_gap=1)


def robust_median(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float).reshape(-1)
    arr = arr[np.isfinite(arr)]
    return float(np.median(arr)) if arr.size else float("nan")


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


def path_length(coords: np.ndarray) -> float:
    arr = np.asarray(coords, dtype=float)
    if arr.ndim != 2 or arr.shape[0] < 2:
        return float("nan")
    diff = np.diff(arr, axis=0)
    return float(np.sum(np.linalg.norm(diff, axis=1)))


def tortuosity(coords: np.ndarray) -> float:
    arr = np.asarray(coords, dtype=float)
    if arr.ndim != 2 or arr.shape[0] < 2:
        return float("nan")
    total = path_length(arr)
    displacement = float(np.linalg.norm(arr[-1] - arr[0]))
    if not np.isfinite(total) or not np.isfinite(displacement):
        return float("nan")
    return float(total / max(displacement, EPS))


def step_speed(coords: np.ndarray, time: np.ndarray) -> np.ndarray:
    arr = np.asarray(coords, dtype=float)
    time = np.asarray(time, dtype=float).reshape(-1)
    if arr.shape[0] < 2 or time.size < 2:
        return np.zeros((0,), dtype=float)
    dt = np.diff(time)
    diff = np.linalg.norm(np.diff(arr, axis=0), axis=1)
    valid = np.isfinite(dt) & np.isfinite(diff) & (dt > 0)
    if not valid.any():
        return np.zeros((0,), dtype=float)
    return diff[valid] / dt[valid]


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


def hysteresis_plane_area(forward: np.ndarray, recovery: np.ndarray, dim_i: int, dim_j: int) -> float:
    if forward.shape[0] < 2 or recovery.shape[0] < 2:
        return float("nan")
    polygon = np.vstack([forward[:, [dim_i, dim_j]], recovery[::-1][:, [dim_i, dim_j]]])
    if polygon.shape[0] < 3:
        return float("nan")
    x = polygon[:, 0]
    y = polygon[:, 1]
    return float(0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


def stable_variance_metric(sampled_coords: np.ndarray) -> np.ndarray:
    coords = np.asarray(sampled_coords, dtype=float)
    if coords.ndim != 2 or coords.shape[1] == 0:
        raise ValueError("sampled_coords must be a non-empty 2D array.")
    var = np.nanvar(coords, axis=0, ddof=1)
    var = np.where(np.isfinite(var) & (var > EPS), var, 1.0)
    return 1.0 / var


def weighted_quad(vecs: np.ndarray, metric_diag: np.ndarray) -> np.ndarray:
    return np.sum((vecs * vecs) * metric_diag[None, :], axis=1)


def potential_from_coords(coords: np.ndarray) -> np.ndarray:
    arr = np.asarray(coords, dtype=float)
    if arr.ndim != 2:
        raise ValueError("coords must be 2D.")
    projected = family_projection(arr)
    m = projected[:, 0]
    d = projected[:, 1]
    e = projected[:, 2]
    return e - m + d


def noetic_action_metrics(coords: np.ndarray, time: np.ndarray, *, metric_diag: np.ndarray) -> dict[str, float]:
    coords = np.asarray(coords, dtype=float)
    time = np.asarray(time, dtype=float)
    if len(coords) < 3 or len(time) < 3:
        return {
            "noetic_action": float("nan"),
            "noetic_action_kinetic": float("nan"),
            "noetic_action_jerk": float("nan"),
            "noetic_action_potential": float("nan"),
        }
    dt_prev = time[1:-1] - time[:-2]
    dt_next = time[2:] - time[1:-1]
    valid = np.isfinite(dt_prev) & np.isfinite(dt_next) & (dt_prev > 0) & (dt_next > 0)
    if not valid.any():
        return {
            "noetic_action": float("nan"),
            "noetic_action_kinetic": float("nan"),
            "noetic_action_jerk": float("nan"),
            "noetic_action_potential": float("nan"),
        }
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
    if len(states) < MIN_REPERTOIRE_POINTS:
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
        transition_prob = np.divide(
            transition_counts,
            row_sums,
            out=np.zeros_like(transition_counts),
            where=row_sums > 0,
        )
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


def summarize_segment_metrics(
    coords: np.ndarray,
    time: np.ndarray,
    *,
    metric_diag: np.ndarray | None = None,
    model: MiniBatchKMeans | None = None,
    n_states: int | None = None,
    event_block: np.ndarray | None = None,
) -> dict[str, float]:
    coords = np.asarray(coords, dtype=float)
    time = np.asarray(time, dtype=float)
    out = {
        "speed_median": robust_median(step_speed(coords, time)),
        "curvature_median": robust_median(curvature_series(coords, time)),
        "tortuosity": tortuosity(coords),
        "path_length": path_length(coords),
        "peak_displacement": float("nan"),
        "recovery_residual": float("nan"),
        "hysteresis_area_md": float("nan"),
        "hysteresis_area_me": float("nan"),
        "hysteresis_area_de": float("nan"),
        "hysteresis_area_mean": float("nan"),
        "entropy_rate": float("nan"),
        "irreversibility": float("nan"),
        "entropy_production": float("nan"),
        "self_loop_rate": float("nan"),
        "transition_sparsity": float("nan"),
        "noetic_action": float("nan"),
        "noetic_action_kinetic": float("nan"),
        "noetic_action_jerk": float("nan"),
        "noetic_action_potential": float("nan"),
    }
    if coords.shape[0] < MIN_SEGMENT_POINTS:
        return out

    projected = family_projection(coords)
    center = np.nanmedian(projected, axis=0)
    out["peak_displacement"] = float(np.nanmax(np.linalg.norm(projected - center[None, :], axis=1)))

    if metric_diag is not None:
        out.update(noetic_action_metrics(coords, time, metric_diag=metric_diag))
    if model is not None and n_states is not None and coords.shape[0] >= MIN_REPERTOIRE_POINTS:
        states = model.predict(coords)
        out.update(repertoire_metrics(states, n_states=n_states))

    if event_block is None or event_block.size == 0:
        return out

    local_start = 0
    local_event_start = int(event_block[0])
    local_event_end = int(event_block[-1])
    pre = projected[local_start:local_event_start]
    forward = projected[local_start : local_event_end + 1]
    recovery = projected[local_event_end:]
    baseline_center = np.nanmedian(pre, axis=0) if pre.size else projected[local_event_start]
    post = projected[local_event_end + 1 :]
    recovery_anchor = np.nanmedian(post[-2:], axis=0) if post.shape[0] >= 2 else projected[-1]
    out["recovery_residual"] = float(np.linalg.norm(recovery_anchor - baseline_center))
    out["hysteresis_area_md"] = hysteresis_plane_area(forward, recovery, 0, 1)
    out["hysteresis_area_me"] = hysteresis_plane_area(forward, recovery, 0, 2)
    out["hysteresis_area_de"] = hysteresis_plane_area(forward, recovery, 1, 2)
    out["hysteresis_area_mean"] = robust_median(
        np.asarray(
            [
                out["hysteresis_area_md"],
                out["hysteresis_area_me"],
                out["hysteresis_area_de"],
            ],
            dtype=float,
        )
    )
    return out


def aggregate_metric_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    base: dict[str, Any] = {}
    for key, value in rows[0].items():
        if key not in NUMERIC_METRIC_COLUMNS and key not in {"segment_points", "event_windows", "segment_duration_sec"}:
            base[key] = value
    base["n_blocks"] = int(len(rows))
    for key in NUMERIC_METRIC_COLUMNS:
        values = np.asarray([row.get(key, float("nan")) for row in rows], dtype=float)
        base[key] = robust_median(values)
    for key in ("segment_points", "event_windows", "segment_duration_sec"):
        values = np.asarray([row.get(key, float("nan")) for row in rows], dtype=float)
        base[f"{key}_median"] = robust_median(values)
    return base


def sample_evenly(coords: np.ndarray, max_points: int) -> np.ndarray:
    arr = np.asarray(coords, dtype=float)
    if arr.shape[0] <= max_points:
        return arr
    idx = np.linspace(0, arr.shape[0] - 1, num=max_points, dtype=int)
    return arr[idx]


def build_reference_model(sampled_blocks: list[np.ndarray], *, dim: int) -> dict[str, Any]:
    if not sampled_blocks:
        return {"metric_diag": None, "model": None, "n_states": None, "n_fit_points": 0}
    sampled = np.concatenate(sampled_blocks, axis=0)
    sampled = sample_evenly(sampled, MAX_POINTS_PER_KEY_FOR_FIT)
    metric_diag = stable_variance_metric(sampled)
    target_states = REPERTOIRE_STATES_BY_DIM[dim]
    effective_states = min(target_states, max(4, sampled.shape[0] // 8), sampled.shape[0])
    if effective_states < 2:
        return {
            "metric_diag": metric_diag,
            "model": None,
            "n_states": None,
            "n_fit_points": int(sampled.shape[0]),
        }
    model = MiniBatchKMeans(
        n_clusters=int(effective_states),
        random_state=20260602 + dim,
        n_init=10,
        batch_size=min(4096, max(256, sampled.shape[0])),
        reassignment_ratio=0.01,
    )
    model.fit(sampled)
    return {
        "metric_diag": metric_diag,
        "model": model,
        "n_states": int(effective_states),
        "n_fit_points": int(sampled.shape[0]),
    }


def bh_fdr(values: pd.Series) -> pd.Series:
    arr = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    mask = np.isfinite(arr)
    if not mask.any():
        return pd.Series(out, index=values.index, dtype=float)
    valid = arr[mask]
    order = np.argsort(valid)
    ranks = np.arange(1, len(valid) + 1, dtype=float)
    q_sorted = np.minimum.accumulate((valid[order] * len(valid) / ranks)[::-1])[::-1]
    q = np.empty_like(q_sorted)
    q[order] = np.clip(q_sorted, 0.0, 1.0)
    out[np.where(mask)[0]] = q
    return pd.Series(out, index=values.index, dtype=float)


def cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    left = left[np.isfinite(left)]
    right = right[np.isfinite(right)]
    if left.size < 2 or right.size < 2:
        return float("nan")
    pooled = ((left.size - 1) * np.var(left, ddof=1) + (right.size - 1) * np.var(right, ddof=1)) / (
        left.size + right.size - 2
    )
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


def winsorize_array(values: np.ndarray, *, lower_q: float = 0.025, upper_q: float = 0.975) -> np.ndarray:
    arr = np.asarray(values, dtype=float).copy()
    mask = np.isfinite(arr)
    if mask.sum() < 3:
        return arr
    lo = float(np.nanquantile(arr[mask], lower_q))
    hi = float(np.nanquantile(arr[mask], upper_q))
    arr[mask] = np.clip(arr[mask], lo, hi)
    return arr


def load_run(handle: h5py.File, h5_path: Path, *, coordinate_contract: str) -> LoadedRun:
    attrs = dict(handle.attrs.items())
    slug = parse_run_slug(h5_path)
    mapped_json = read_json_dataset(handle, "participant/mapped_json")
    row_json = read_json_dataset(handle, "participant/row_json")
    group = (
        mapped_json.get("group")
        or decode_text(attrs.get("mapped_group"))
        or GROUP_MAP.get(str(row_json.get("GROUP") or row_json.get("Type") or row_json.get("TYPE") or "").strip())
        or "Control"
    )
    group = GROUP_MAP.get(str(group).strip(), str(group).strip())
    condition = mapped_json.get("condition") or decode_text(attrs.get("mapped_condition")) or slug["condition"]
    task = mapped_json.get("task") or decode_text(attrs.get("mapped_task")) or slug["task"]
    subject_id = decode_text(attrs.get("subject_id")) or slug["subject"]
    metadata = {
        "dataset_id": decode_text(attrs.get("dataset_id")) or f"{DATASET_ID}:{subject_id}:{task}",
        "subject_id": subject_id,
        "group": group,
        "condition": condition,
        "task": task,
        "session": decode_text(attrs.get("session")) or "ses-01",
        "run": decode_text(attrs.get("run")) or "run-01",
        "acq": decode_text(attrs.get("acq")),
        "source_h5_path": str(h5_path),
    }
    metadata.update(read_run_contract(handle).provenance())

    time = np.asarray(handle["time"][:], dtype=float).reshape(-1) if "/time" in handle else np.zeros((0,), dtype=float)
    segment_blocks: dict[str, list[np.ndarray]] = {}
    reference_blocks: dict[str, list[np.ndarray]] = {}

    for spec in EXACT_PHASE_SEGMENTS:
        dataset_path = f"labels/{spec.label_key}"
        if dataset_path not in handle:
            segment_blocks[spec.label] = []
            reference_blocks[spec.label] = []
            continue
        raw = np.asarray(handle[dataset_path][:], dtype=float).reshape(-1)
        n_points = min(time.shape[0], raw.shape[0])
        idx = np.flatnonzero(np.isfinite(raw[:n_points]) & (raw[:n_points] > 0))
        blocks = contiguous_runs(idx, max_gap=1)
        segment_blocks[spec.label] = blocks
        reference_blocks[spec.label] = blocks

    for spec in SUBTYPE_SEGMENTS:
        subtype_blocks = [
            block
            for phase_spec in EXACT_PHASE_SEGMENTS
            if phase_spec.event_subtype == spec.event_subtype
            for block in segment_blocks.get(phase_spec.label, [])
        ]
        segment_blocks[spec.label] = merge_blocks(subtype_blocks)

    for spec in PHASE_SEGMENTS:
        phase_blocks = [
            block
            for phase_spec in EXACT_PHASE_SEGMENTS
            if phase_spec.event_phase == spec.event_phase
            for block in segment_blocks.get(phase_spec.label, [])
        ]
        segment_blocks[spec.label] = merge_blocks(phase_blocks)

    spaces: dict[SpaceKey, dict[str, Any]] = {}
    resolved_3d = resolve_coords_3d(handle, coordinate_contract)
    resolved_9d = resolve_coords_9d(handle, coordinate_contract)
    if resolved_3d is not None:
        spaces[SpaceKey("global", "global", 3)] = {
            "coords": np.asarray(resolved_3d.values, dtype=float),
            "source_dataset_path": resolved_3d.values_path,
        }
    if resolved_9d is not None:
        spaces[SpaceKey("global", "global", 9)] = {
            "coords": np.asarray(resolved_9d.values, dtype=float),
            "source_dataset_path": resolved_9d.values_path,
        }

    return LoadedRun(
        metadata=metadata,
        time=time,
        segment_blocks=segment_blocks,
        reference_blocks=reference_blocks,
        spaces=spaces,
    )
