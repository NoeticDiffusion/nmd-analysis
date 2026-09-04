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


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.h5_contract import read_run_contract, resolve_coords_3d, resolve_coords_9d  # noqa: E402


RESULT_STAMP = "20260605"
SUBJECT_COORDINATE_CONTRACT = "subject_anchored"
COHORT_COORDINATE_CONTRACT = "cohort_anchored"
PRIMARY_COORDINATE_CONTRACT = SUBJECT_COORDINATE_CONTRACT
MANIFEST_JSON = "pipeline_manifest.json"
RUN_METRICS_CSV = "event_run_metrics.csv"
SUBJECT_METRICS_CSV = "event_subject_metrics.csv"
EVENT_CONTRASTS_CSV = "event_contrasts.csv"
PRIMARY_STANDARD_CONTRASTS_CSV = "primary_standard_contrasts.csv"
PRIMARY_EVENT_CONTRASTS_CSV = "primary_event_contrasts.csv"
SUMMARY_FILENAME = "analysis_summary.md"
RUN_SLUG_RE = re.compile(r"^(?P<subject>sub-\d+)_(?P<condition>ON|OFF|not_applicable)_(?P<task>.+)$")
GROUP_MAP = {
    "PD": "Parkinson",
    "CTL": "Control",
    "Parkinson": "Parkinson",
    "Control": "Control",
}
DIMS: tuple[int, ...] = (3, 9)
REPERTOIRE_STATES_BY_DIM = {3: 12, 9: 18}
MAX_POINTS_PER_SEGMENT_FOR_FIT = 64
MAX_POINTS_PER_KEY_FOR_FIT = 40000
MIN_SEGMENT_POINTS = 5
MIN_REPERTOIRE_POINTS = 8
PRE_EVENT_WINDOWS = 2
POST_EVENT_WINDOWS = 3
EPS = 1e-12
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
class SegmentSpec:
    label: str
    segment_kind: str
    members: tuple[str, ...]
    family: str


@dataclass(frozen=True)
class DatasetSpec:
    dataset_id: str
    task: str
    task_label: str
    dataset_root: Path
    results_slug: str
    run_config_path: Path
    analyze_config_path: Path
    cohort_run_config_path: Path
    cohort_analyze_config_path: Path
    exact_event_labels: tuple[str, ...]
    derived_segments: tuple[SegmentSpec, ...]


@dataclass(frozen=True)
class SpaceKey:
    level: str
    network: str
    dim: int


@dataclass
class LoadedRun:
    metadata: dict[str, Any]
    time: np.ndarray
    segment_blocks: dict[str, list[np.ndarray]]
    spaces: dict[SpaceKey, dict[str, Any]]


@dataclass
class SimpleStateModel:
    centers: np.ndarray

    def predict(self, coords: np.ndarray) -> np.ndarray:
        arr = np.asarray(coords, dtype=float)
        if arr.ndim != 2 or arr.shape[0] == 0:
            return np.zeros((0,), dtype=int)
        diff = arr[:, None, :] - self.centers[None, :, :]
        dist2 = np.sum(diff * diff, axis=2)
        return np.argmin(dist2, axis=1).astype(int)


DS003509_EVENTS = (
    "training_stimulus_congruent",
    "training_stimulus_incongruent",
    "training_response_correct",
    "training_response_incorrect",
    "training_no_response",
    "training_feedback_reward",
    "training_feedback_punishment",
    "training_feedback_timeout",
    "training_feedback_error",
    "test_stimulus_easy",
    "test_stimulus_direct_conflict",
    "test_stimulus_relative_conflict",
    "test_stimulus_other",
    "test_response_correct",
    "test_response_incorrect",
    "test_no_response",
)

DS003506_EVENTS = (
    "choose_instruction",
    "choose_stimulus",
    "choose_response_left",
    "choose_response_right",
    "choose_feedback_reward",
    "choose_feedback_punishment",
    "choose_feedback_timeout",
    "choose_feedback_error",
    "match_instruction",
    "match_stimulus",
    "match_response_left",
    "match_response_right",
    "match_feedback_reward",
    "match_feedback_punishment",
    "match_feedback_timeout",
    "match_feedback_error",
)

DATASET_SPECS: dict[str, DatasetSpec] = {
    "ds003509": DatasetSpec(
        dataset_id="ds003509",
        task="simon_conflict",
        task_label="Simon conflict",
        dataset_root=REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds003509_20260605_071616",
        results_slug=f"parkinson_simon_conflict_{RESULT_STAMP}",
        run_config_path=NDT_ANALYSIS_ROOT / "config" / "ndt-analysis-ds003509.yaml",
        analyze_config_path=NDT_ANALYSIS_ROOT / "config" / "analysis-ds003509.yaml",
        cohort_run_config_path=NDT_ANALYSIS_ROOT / "config" / "ndt-analysis-ds003509-cohort.yaml",
        cohort_analyze_config_path=NDT_ANALYSIS_ROOT / "config" / "analysis-ds003509-cohort.yaml",
        exact_event_labels=DS003509_EVENTS,
        derived_segments=(
            SegmentSpec("training_all", "event_family", tuple(label for label in DS003509_EVENTS if label.startswith("training_")), "training"),
            SegmentSpec("test_all", "event_family", tuple(label for label in DS003509_EVENTS if label.startswith("test_")), "test"),
            SegmentSpec(
                "training_stimulus_all",
                "event_family",
                ("training_stimulus_congruent", "training_stimulus_incongruent"),
                "training_stimulus",
            ),
            SegmentSpec(
                "training_response_all",
                "event_family",
                ("training_response_correct", "training_response_incorrect", "training_no_response"),
                "training_response",
            ),
            SegmentSpec(
                "training_feedback_all",
                "event_family",
                (
                    "training_feedback_reward",
                    "training_feedback_punishment",
                    "training_feedback_timeout",
                    "training_feedback_error",
                ),
                "training_feedback",
            ),
            SegmentSpec(
                "test_stimulus_all",
                "event_family",
                (
                    "test_stimulus_easy",
                    "test_stimulus_direct_conflict",
                    "test_stimulus_relative_conflict",
                    "test_stimulus_other",
                ),
                "test_stimulus",
            ),
            SegmentSpec(
                "test_conflict_all",
                "event_family",
                ("test_stimulus_direct_conflict", "test_stimulus_relative_conflict"),
                "test_conflict",
            ),
            SegmentSpec(
                "test_response_all",
                "event_family",
                ("test_response_correct", "test_response_incorrect", "test_no_response"),
                "test_response",
            ),
            SegmentSpec(
                "feedback_reward_all",
                "event_family",
                ("training_feedback_reward",),
                "reward",
            ),
            SegmentSpec(
                "feedback_punishment_all",
                "event_family",
                ("training_feedback_punishment",),
                "punishment",
            ),
        ),
    ),
    "ds003506": DatasetSpec(
        dataset_id="ds003506",
        task="reinforcement_learning",
        task_label="Reinforcement learning",
        dataset_root=REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds003506_20260605_064641",
        results_slug=f"parkinson_reinforcement_learning_{RESULT_STAMP}",
        run_config_path=NDT_ANALYSIS_ROOT / "config" / "ndt-analysis-ds003506.yaml",
        analyze_config_path=NDT_ANALYSIS_ROOT / "config" / "analysis-ds003506.yaml",
        cohort_run_config_path=NDT_ANALYSIS_ROOT / "config" / "ndt-analysis-ds003506-cohort.yaml",
        cohort_analyze_config_path=NDT_ANALYSIS_ROOT / "config" / "analysis-ds003506-cohort.yaml",
        exact_event_labels=DS003506_EVENTS,
        derived_segments=(
            SegmentSpec("choose_all", "event_family", tuple(label for label in DS003506_EVENTS if label.startswith("choose_")), "choose"),
            SegmentSpec("match_all", "event_family", tuple(label for label in DS003506_EVENTS if label.startswith("match_")), "match"),
            SegmentSpec(
                "choose_feedback_all",
                "event_family",
                (
                    "choose_feedback_reward",
                    "choose_feedback_punishment",
                    "choose_feedback_timeout",
                    "choose_feedback_error",
                ),
                "choose_feedback",
            ),
            SegmentSpec(
                "match_feedback_all",
                "event_family",
                (
                    "match_feedback_reward",
                    "match_feedback_punishment",
                    "match_feedback_timeout",
                    "match_feedback_error",
                ),
                "match_feedback",
            ),
            SegmentSpec(
                "choose_response_all",
                "event_family",
                ("choose_response_left", "choose_response_right"),
                "choose_response",
            ),
            SegmentSpec(
                "match_response_all",
                "event_family",
                ("match_response_left", "match_response_right"),
                "match_response",
            ),
            SegmentSpec(
                "reward_all",
                "event_family",
                ("choose_feedback_reward", "match_feedback_reward"),
                "reward",
            ),
            SegmentSpec(
                "punishment_all",
                "event_family",
                ("choose_feedback_punishment", "match_feedback_punishment"),
                "punishment",
            ),
            SegmentSpec(
                "timeout_all",
                "event_family",
                ("choose_feedback_timeout", "match_feedback_timeout"),
                "timeout",
            ),
            SegmentSpec(
                "error_all",
                "event_family",
                ("choose_feedback_error", "match_feedback_error"),
                "error",
            ),
        ),
    ),
}


def get_dataset_spec(dataset_id: str) -> DatasetSpec:
    try:
        return DATASET_SPECS[str(dataset_id)]
    except KeyError as exc:
        raise KeyError(f"Unsupported dataset_id {dataset_id!r}.") from exc


def infer_dataset_spec(dataset_root: Path | None = None, dataset_id: str | None = None) -> DatasetSpec:
    if dataset_id:
        return get_dataset_spec(dataset_id)
    if dataset_root is not None:
        root_str = str(dataset_root)
        for known_id in DATASET_SPECS:
            if known_id in root_str:
                return DATASET_SPECS[known_id]
    raise ValueError("Could not infer dataset spec; provide --dataset-id explicitly.")


def results_dir_for_spec(spec: DatasetSpec) -> Path:
    return ARTICLE_DIR / "results" / spec.results_slug


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
        raise ValueError(f"Could not parse run slug from {h5_path.name}.")
    return match.groupdict()


def infer_session(condition: str | None, group: str | None) -> str | None:
    if group == "Parkinson" and condition == "ON":
        return "ses-01"
    if group == "Parkinson" and condition == "OFF":
        return "ses-02"
    if group == "Control":
        return "ses-01"
    return None


def contiguous_runs(indices: np.ndarray, *, max_gap: int = 1) -> list[np.ndarray]:
    values = np.unique(np.asarray(indices, dtype=int).reshape(-1))
    if values.size == 0:
        return []
    breaks = np.where(np.diff(values) > int(max_gap))[0]
    starts = np.r_[0, breaks + 1]
    ends = np.r_[breaks + 1, values.size]
    return [values[start:end] for start, end in zip(starts, ends)]


def merge_blocks(blocks: Sequence[np.ndarray]) -> list[np.ndarray]:
    merged = np.concatenate([np.asarray(block, dtype=int).reshape(-1) for block in blocks if len(block)], axis=0) if blocks else np.asarray([], dtype=int)
    return contiguous_runs(merged, max_gap=1) if merged.size else []


def nearest_time_indices(time: np.ndarray, onset_sec: Sequence[float]) -> np.ndarray:
    if len(time) == 0:
        return np.zeros((0,), dtype=int)
    time = np.asarray(time, dtype=float).reshape(-1)
    picks: list[int] = []
    for raw in onset_sec:
        try:
            onset = float(raw)
        except (TypeError, ValueError):
            continue
        if not np.isfinite(onset):
            continue
        picks.append(int(np.argmin(np.abs(time - onset))))
    return np.asarray(sorted(set(picks)), dtype=int)


def build_exact_event_blocks(handle: h5py.File, spec: DatasetSpec, *, n_points: int) -> dict[str, list[np.ndarray]]:
    event_blocks = {label: [] for label in spec.exact_event_labels}
    required = {
        "event_windows/event_id",
        "event_windows/event_label",
        "event_windows/event_start_window_index",
        "event_windows/event_stop_window_index",
    }
    if all(path in handle for path in required):
        raw_event_ids = np.asarray(handle["event_windows/event_id"][:]).reshape(-1)
        raw_labels = [decode_text(value) or "" for value in handle["event_windows/event_label"][:]]
        raw_start = np.asarray(handle["event_windows/event_start_window_index"][:]).reshape(-1)
        raw_stop = np.asarray(handle["event_windows/event_stop_window_index"][:]).reshape(-1)
        n_rows = min(len(raw_labels), raw_event_ids.size, raw_start.size, raw_stop.size)
        frame = pd.DataFrame(
            {
                "event_id": raw_event_ids[:n_rows],
                "event_label": raw_labels[:n_rows],
                "event_start_window_index": raw_start[:n_rows],
                "event_stop_window_index": raw_stop[:n_rows],
            }
        )
        for label in spec.exact_event_labels:
            subset = frame[frame["event_label"] == label].copy()
            if subset.empty:
                continue
            dedup = (
                subset.groupby("event_id", dropna=False, as_index=False)
                .agg(
                    event_start_window_index=("event_start_window_index", "min"),
                    event_stop_window_index=("event_stop_window_index", "max"),
                )
                .sort_values(["event_start_window_index", "event_stop_window_index", "event_id"])
            )
            blocks: list[np.ndarray] = []
            for _, row in dedup.iterrows():
                start = pd.to_numeric(pd.Series([row["event_start_window_index"]]), errors="coerce").iloc[0]
                stop = pd.to_numeric(pd.Series([row["event_stop_window_index"]]), errors="coerce").iloc[0]
                if not np.isfinite(start) or not np.isfinite(stop):
                    continue
                start_i = max(0, int(start))
                stop_i = min(int(stop), n_points - 1)
                if stop_i < start_i:
                    continue
                blocks.append(np.arange(start_i, stop_i + 1, dtype=int))
            event_blocks[label] = blocks
        return event_blocks

    events_df = pd.DataFrame()
    if "/events/onset_sec" in handle and "/events/raw_event_label" in handle:
        raw_labels = [decode_text(value) or "" for value in handle["/events/raw_event_label"][:]]
        onset = np.asarray(handle["/events/onset_sec"][:], dtype=float).reshape(-1)
        n_rows = min(len(raw_labels), onset.size)
        events_df = pd.DataFrame({"raw_event_label": raw_labels[:n_rows], "onset_sec": onset[:n_rows]})
    for label in spec.exact_event_labels:
        subset = events_df.loc[events_df["raw_event_label"] == label, "onset_sec"].to_numpy(dtype=float)
        picks = nearest_time_indices(np.asarray(handle["time"][:], dtype=float).reshape(-1), subset)
        event_blocks[label] = contiguous_runs(picks, max_gap=1)
    return event_blocks


def build_segment_blocks(handle: h5py.File, spec: DatasetSpec, *, n_points: int) -> dict[str, list[np.ndarray]]:
    exact_blocks = build_exact_event_blocks(handle, spec, n_points=n_points)
    segment_blocks: dict[str, list[np.ndarray]] = {label: blocks for label, blocks in exact_blocks.items()}
    for segment in spec.derived_segments:
        members = [exact_blocks.get(member, []) for member in segment.members]
        segment_blocks[segment.label] = merge_blocks([block for blocks in members for block in blocks])
    return segment_blocks


def resolve_regional_coords(
    network_group: h5py.Group,
    *,
    coordinate_contract: str,
    dim: int,
) -> tuple[np.ndarray, str, str] | None:
    dataset_name = "mnps" if dim == 3 else "stratified"
    contract_group_path = f"{coordinate_contract}/{dataset_name}"
    if contract_group_path in network_group:
        subgroup = network_group[coordinate_contract]
        return (
            np.asarray(subgroup[dataset_name][:], dtype=float),
            f"{network_group.name}/{coordinate_contract}/{dataset_name}",
            coordinate_contract,
        )
    if dataset_name in network_group:
        resolved = decode_text(network_group.attrs.get("coordinate_contract")) or "legacy"
        return (
            np.asarray(network_group[dataset_name][:], dtype=float),
            f"{network_group.name}/{dataset_name}",
            resolved,
        )
    return None


def load_run(handle: h5py.File, h5_path: Path, spec: DatasetSpec, *, coordinate_contract: str) -> LoadedRun:
    attrs = dict(handle.attrs.items())
    slug = parse_run_slug(h5_path)
    mapped_json = read_json_dataset(handle, "participant/mapped_json")
    row_json = read_json_dataset(handle, "participant/row_json")
    clinical_json = read_json_dataset(handle, "participant/clinical_json")
    participant_json = clinical_json.get("participant") if isinstance(clinical_json.get("participant"), dict) else {}
    group = mapped_json.get("group") or GROUP_MAP.get(str(row_json.get("Group") or "").strip()) or (
        "Control" if slug["condition"] == "not_applicable" else "Parkinson"
    )
    condition = mapped_json.get("condition") or slug["condition"]
    task = mapped_json.get("task") or slug["task"]
    subject_id = decode_text(attrs.get("subject_id")) or slug["subject"]
    session = decode_text(attrs.get("session")) or infer_session(condition, group)
    metadata = {
        "dataset_id": decode_text(attrs.get("dataset_id")) or f"{spec.dataset_id}:{subject_id}:{condition}_{task}",
        "subject_id": subject_id,
        "group": group,
        "condition": condition,
        "task": task,
        "session": session,
        "run": decode_text(attrs.get("run")) or "run-01",
        "acq": decode_text(attrs.get("acq")),
        "age": participant_json.get("age"),
        "sex": participant_json.get("sex"),
        "source_h5_path": str(h5_path),
        "requested_coordinate_contract": str(coordinate_contract),
        "resolved_coordinate_contract": str(coordinate_contract),
    }
    metadata.update(read_run_contract(handle).provenance())

    time = np.asarray(handle["time"][:], dtype=float).reshape(-1) if "/time" in handle else np.zeros((0,), dtype=float)
    segment_blocks = build_segment_blocks(handle, spec, n_points=time.shape[0])

    spaces: dict[SpaceKey, dict[str, Any]] = {}
    resolved_3d = resolve_coords_3d(handle, coordinate_contract)
    resolved_9d = resolve_coords_9d(handle, coordinate_contract)
    if resolved_3d is not None:
        metadata["requested_coordinate_contract"] = resolved_3d.requested_coordinate_contract
        metadata["resolved_coordinate_contract"] = resolved_3d.resolved_coordinate_contract
        metadata["primary_coordinate_contract"] = resolved_3d.primary_coordinate_contract
        spaces[SpaceKey("global", "global", 3)] = {
            "coords": np.asarray(resolved_3d.values, dtype=float),
            "source_dataset_path": resolved_3d.values_path,
        }
    if resolved_9d is not None:
        metadata["requested_coordinate_contract"] = resolved_9d.requested_coordinate_contract
        metadata["resolved_coordinate_contract"] = resolved_9d.resolved_coordinate_contract
        metadata["primary_coordinate_contract"] = resolved_9d.primary_coordinate_contract
        spaces[SpaceKey("global", "global", 9)] = {
            "coords": np.asarray(resolved_9d.values, dtype=float),
            "source_dataset_path": resolved_9d.values_path,
        }
    if "/regional_mnps" in handle:
        for network in sorted(handle["/regional_mnps"].keys()):
            network_group = handle["/regional_mnps"][network]
            regional_3d = resolve_regional_coords(network_group, coordinate_contract=coordinate_contract, dim=3)
            if regional_3d is not None:
                spaces[SpaceKey("regional", str(network), 3)] = {
                    "coords": regional_3d[0],
                    "source_dataset_path": regional_3d[1],
                    "resolved_coordinate_contract": regional_3d[2],
                }
            regional_9d = resolve_regional_coords(network_group, coordinate_contract=coordinate_contract, dim=9)
            if regional_9d is not None:
                spaces[SpaceKey("regional", str(network), 9)] = {
                    "coords": regional_9d[0],
                    "source_dataset_path": regional_9d[1],
                    "resolved_coordinate_contract": regional_9d[2],
                }
    return LoadedRun(metadata=metadata, time=time, segment_blocks=segment_blocks, spaces=spaces)


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


def step_speed(coords: np.ndarray, time: np.ndarray) -> np.ndarray:
    arr = np.asarray(coords, dtype=float)
    time = np.asarray(time, dtype=float).reshape(-1)
    if arr.shape[0] < 2 or time.size < 2:
        return np.zeros((0,), dtype=float)
    dt = np.diff(time)
    diff = np.linalg.norm(np.diff(arr, axis=0), axis=1)
    valid = np.isfinite(dt) & np.isfinite(diff) & (dt > 0)
    return diff[valid] / dt[valid] if valid.any() else np.zeros((0,), dtype=float)


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
    var = np.nanvar(coords, axis=0, ddof=1)
    var = np.where(np.isfinite(var) & (var > EPS), var, 1.0)
    return 1.0 / var


def weighted_quad(vecs: np.ndarray, metric_diag: np.ndarray) -> np.ndarray:
    return np.sum((vecs * vecs) * metric_diag[None, :], axis=1)


def potential_from_coords(coords: np.ndarray) -> np.ndarray:
    projected = family_projection(np.asarray(coords, dtype=float))
    return projected[:, 2] - projected[:, 0] + projected[:, 1]


def noetic_action_metrics(coords: np.ndarray, time: np.ndarray, *, metric_diag: np.ndarray) -> dict[str, float]:
    coords = np.asarray(coords, dtype=float)
    time = np.asarray(time, dtype=float)
    if len(coords) < 3 or len(time) < 3:
        return {key: float("nan") for key in ("noetic_action", "noetic_action_kinetic", "noetic_action_jerk", "noetic_action_potential")}
    dt_prev = time[1:-1] - time[:-2]
    dt_next = time[2:] - time[1:-1]
    valid = np.isfinite(dt_prev) & np.isfinite(dt_next) & (dt_prev > 0) & (dt_next > 0)
    if not valid.any():
        return {key: float("nan") for key in ("noetic_action", "noetic_action_kinetic", "noetic_action_jerk", "noetic_action_potential")}
    delta = coords[2:] - coords[1:-1]
    delta2 = coords[2:] - 2.0 * coords[1:-1] + coords[:-2]
    dt_center = 0.5 * (dt_prev + dt_next)
    potential = potential_from_coords(coords[1:-1])
    kinetic_density = 0.5 * weighted_quad(delta[valid], metric_diag) / np.maximum(dt_next[valid], EPS) ** 2
    jerk_density = weighted_quad(delta2[valid], metric_diag) / np.maximum(dt_center[valid], EPS) ** 4
    potential_density = potential[valid]
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
        return {key: float("nan") for key in ("entropy_rate", "irreversibility", "entropy_production", "self_loop_rate", "transition_sparsity")}
    transition_counts = np.zeros((n_states, n_states), dtype=float)
    for src, dst in zip(states[:-1], states[1:], strict=False):
        transition_counts[int(src), int(dst)] += 1.0
    occupancy = np.bincount(states, minlength=n_states).astype(float)
    if occupancy.sum() <= 0:
        return {key: float("nan") for key in ("entropy_rate", "irreversibility", "entropy_production", "self_loop_rate", "transition_sparsity")}
    pi = occupancy / occupancy.sum()
    row_sums = transition_counts.sum(axis=1, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        transition_prob = np.divide(
            transition_counts,
            row_sums,
            out=np.zeros_like(transition_counts),
            where=row_sums > 0,
        )
    flow = pi[:, None] * transition_prob
    return {
        "entropy_rate": float(-np.sum(flow * np.log(transition_prob + EPS))),
        "irreversibility": float(0.5 * np.sum(np.abs(flow - flow.T))),
        "entropy_production": float(np.sum(flow * np.log((flow + EPS) / (flow.T + EPS)))),
        "self_loop_rate": float(np.sum(pi * np.diag(transition_prob))),
        "transition_sparsity": float(1.0 - (np.count_nonzero(transition_counts) / transition_counts.size)),
    }


def summarize_segment_metrics(
    coords: np.ndarray,
    time: np.ndarray,
    *,
    metric_diag: np.ndarray | None = None,
    model: SimpleStateModel | None = None,
    n_states: int | None = None,
    event_block: np.ndarray | None = None,
) -> dict[str, float]:
    coords = np.asarray(coords, dtype=float)
    time = np.asarray(time, dtype=float)
    out = {key: float("nan") for key in NUMERIC_METRIC_COLUMNS}
    out["speed_median"] = robust_median(step_speed(coords, time))
    out["curvature_median"] = robust_median(curvature_series(coords, time))
    out["tortuosity"] = tortuosity(coords)
    out["path_length"] = path_length(coords)
    if coords.shape[0] < MIN_SEGMENT_POINTS:
        return out
    projected = family_projection(coords)
    center = np.nanmedian(projected, axis=0)
    out["peak_displacement"] = float(np.nanmax(np.linalg.norm(projected - center[None, :], axis=1)))
    if metric_diag is not None:
        out.update(noetic_action_metrics(coords, time, metric_diag=metric_diag))
    if model is not None and n_states is not None and coords.shape[0] >= MIN_REPERTOIRE_POINTS:
        out.update(repertoire_metrics(model.predict(coords), n_states=n_states))
    if event_block is None or event_block.size == 0:
        return out
    local_event_start = int(event_block[0])
    local_event_end = int(event_block[-1])
    pre = projected[:local_event_start]
    forward = projected[: local_event_end + 1]
    recovery = projected[local_event_end:]
    baseline_center = np.nanmedian(pre, axis=0) if pre.size else projected[local_event_start]
    post = projected[local_event_end + 1 :]
    recovery_anchor = np.nanmedian(post[-2:], axis=0) if post.shape[0] >= 2 else projected[-1]
    out["recovery_residual"] = float(np.linalg.norm(recovery_anchor - baseline_center))
    out["hysteresis_area_md"] = hysteresis_plane_area(forward, recovery, 0, 1)
    out["hysteresis_area_me"] = hysteresis_plane_area(forward, recovery, 0, 2)
    out["hysteresis_area_de"] = hysteresis_plane_area(forward, recovery, 1, 2)
    out["hysteresis_area_mean"] = robust_median(
        np.asarray([out["hysteresis_area_md"], out["hysteresis_area_me"], out["hysteresis_area_de"]], dtype=float)
    )
    return out


def aggregate_metric_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    base = {key: value for key, value in rows[0].items() if key not in NUMERIC_METRIC_COLUMNS and key not in {"segment_points", "event_windows", "segment_duration_sec"}}
    base["n_blocks"] = int(len(rows))
    for key in NUMERIC_METRIC_COLUMNS:
        base[key] = robust_median(np.asarray([row.get(key, float("nan")) for row in rows], dtype=float))
    for key in ("segment_points", "event_windows", "segment_duration_sec"):
        base[f"{key}_median"] = robust_median(np.asarray([row.get(key, float("nan")) for row in rows], dtype=float))
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
        return {"metric_diag": metric_diag, "model": None, "n_states": None, "n_fit_points": int(sampled.shape[0])}
    center_idx = np.linspace(0, sampled.shape[0] - 1, num=int(effective_states), dtype=int)
    centers = sampled[center_idx].copy()
    for _ in range(8):
        diff = sampled[:, None, :] - centers[None, :, :]
        dist2 = np.sum(diff * diff, axis=2)
        assignment = np.argmin(dist2, axis=1)
        updated = centers.copy()
        for cluster_idx in range(int(effective_states)):
            members = sampled[assignment == cluster_idx]
            if members.shape[0]:
                updated[cluster_idx] = np.nanmean(members, axis=0)
        if np.allclose(updated, centers, equal_nan=True):
            centers = updated
            break
        centers = updated
    model = SimpleStateModel(centers=centers)
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
