from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from itertools import repeat
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import h5py
import numpy as np
import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.h5_contract import (  # noqa: E402
    DEFAULT_COORDINATE_CONTRACT,
    read_run_contract,
    resolve_coords_3d,
    resolve_coords_9d,
    resolve_jacobian_3d,
)


RUN_ID_RE = re.compile(
    r"^sub-(?P<subject>\d+)_post_cardiac_arrest_coma_continuous_eeg_run-(?P<run>\d+)_acq-(?P<acq>\d+)$"
)
DEFAULT_PROCESSED_ROOT_PARENT = Path("E:/Science_Datasets/physionet/processed/physionet_icare_2_1")
DEFAULT_RAW_ROOT = Path("E:/Science_Datasets/physionet/received/i-care_2_1_random100_longitudinal/training")
DEFAULT_MNPS_AXES: tuple[str, ...] = ("m", "d", "e")
DEFAULT_TIME_BINS_HOURS: tuple[tuple[float, float, str], ...] = (
    (0.0, 24.0, "0_24h"),
    (24.0, 48.0, "24_48h"),
    (48.0, 72.0, "48_72h"),
    (72.0, float("inf"), "72h_plus"),
)
PRIMARY_12H_TIME_BINS_HOURS: tuple[tuple[float, float, str], ...] = (
    (0.0, 12.0, "0_12h"),
    (12.0, 24.0, "12_24h"),
    (24.0, 48.0, "24_48h"),
    (48.0, 72.0, "48_72h"),
    (72.0, float("inf"), "72h_plus"),
)
PHASE_6H_TIME_BINS_HOURS: tuple[tuple[float, float, str], ...] = (
    (0.0, 6.0, "0_6h"),
    (6.0, 12.0, "6_12h"),
    (12.0, 24.0, "12_24h"),
    (24.0, 48.0, "24_48h"),
    (48.0, 72.0, "48_72h"),
    (72.0, float("inf"), "72h_plus"),
)
HOURLY_12H_TIME_BINS_HOURS: tuple[tuple[float, float, str], ...] = tuple(
    (float(hour), float(hour + 1), f"{hour}_{hour + 1}h")
    for hour in range(12)
) + (
    (12.0, 24.0, "12_24h"),
    (24.0, 48.0, "24_48h"),
    (48.0, 72.0, "48_72h"),
    (72.0, float("inf"), "72h_plus"),
)
TIME_BIN_SCHEMES: Dict[str, tuple[tuple[float, float, str], ...]] = {
    "legacy_24h": DEFAULT_TIME_BINS_HOURS,
    "primary_12h": PRIMARY_12H_TIME_BINS_HOURS,
    "phase_6h": PHASE_6H_TIME_BINS_HOURS,
    "hourly_12h": HOURLY_12H_TIME_BINS_HOURS,
}
DEFAULT_TIME_BIN_SCHEME = "legacy_24h"
EXPECTED_MAX_CHANNELS = 21.0


@dataclass(frozen=True)
class AnalysisConfig:
    processed_root: Path
    raw_root: Path
    output_dir: Path
    coordinate_contract: str = DEFAULT_COORDINATE_CONTRACT
    time_bins_hours: tuple[tuple[float, float, str], ...] = DEFAULT_TIME_BINS_HOURS
    time_bin_scheme: str = DEFAULT_TIME_BIN_SCHEME
    limit_h5: int | None = None
    workers: int = 1


def resolve_default_processed_root() -> Path:
    if DEFAULT_PROCESSED_ROOT_PARENT.exists():
        candidates = sorted(
            (
                path
                for path in DEFAULT_PROCESSED_ROOT_PARENT.iterdir()
                if path.is_dir() and path.name.startswith("neuralmanifolddynamics_physionet_icare_2_1_")
            ),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            return candidates[0]
    article_dir = Path(__file__).resolve().parents[1]
    return article_dir.parents[1] / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260512_191310"


def parse_args() -> AnalysisConfig:
    parser = argparse.ArgumentParser(
        description="Build run-level and patient-bin summaries for I-CARE H5 exports."
    )
    parser.add_argument(
        "--processed-root",
        type=Path,
        default=resolve_default_processed_root(),
        help="Processed NeuralManifoldDynamics run directory containing per-run H5 files.",
    )
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=DEFAULT_RAW_ROOT,
        help="Raw I-CARE training root containing subject folders and WFDB headers for fallback timing.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ARTICLE_DIR / "results" / "timeline_analysis",
        help="Directory where CSV and JSON outputs will be written.",
    )
    parser.add_argument(
        "--coordinate-contract",
        type=str,
        default=DEFAULT_COORDINATE_CONTRACT,
        choices=["cohort_anchored", "subject_anchored", "legacy"],
        help="Which MNDM coordinate contract to summarize for global MNPS/Jacobian-derived fields.",
    )
    parser.add_argument(
        "--time-bin-scheme",
        type=str,
        choices=sorted(TIME_BIN_SCHEMES),
        default=DEFAULT_TIME_BIN_SCHEME,
        help="Named time-bin scheme used to assign runs from anchor-relative time.",
    )
    parser.add_argument(
        "--limit-h5",
        type=int,
        default=None,
        help="Optional cap on the number of H5 files to inspect, for smoke tests.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel worker processes for H5 summarization. Use >1 to parallelize.",
    )
    args = parser.parse_args()
    return AnalysisConfig(
        processed_root=args.processed_root,
        raw_root=args.raw_root,
        output_dir=args.output_dir,
        coordinate_contract=args.coordinate_contract,
        time_bins_hours=TIME_BIN_SCHEMES[args.time_bin_scheme],
        time_bin_scheme=args.time_bin_scheme,
        limit_h5=args.limit_h5,
        workers=int(args.workers),
    )


def parse_elapsed_clock(value: str) -> float:
    parts = [int(part) for part in value.strip().split(":")]
    if len(parts) != 3:
        raise ValueError(f"Expected HH:MM:SS clock string, got {value!r}")
    hours, minutes, seconds = parts
    return float(hours * 3600 + minutes * 60 + seconds)


def format_hours(value: float) -> str:
    if not np.isfinite(value):
        return "nan"
    return f"{value:.3f}"


def _to_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return _to_text(value.item())
        return json.dumps([_to_text(item) for item in value.tolist()], ensure_ascii=True)
    if isinstance(value, (list, tuple)):
        return json.dumps([_to_text(item) for item in value], ensure_ascii=True)
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        try:
            return bytes(value).decode("utf-8")
        except Exception:
            return str(value)
    return str(value)


def _to_float(value: Any) -> float:
    if value is None:
        return float("nan")
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return _to_float(value.item())
        return float("nan")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _read_optional_array(group: h5py.Group, key: str) -> np.ndarray:
    if key not in group:
        return np.array([], dtype=float)
    return np.asarray(group[key][()])


def _read_optional_scalar(group: h5py.Group, key: str) -> Any:
    if key not in group:
        return None
    value = group[key][()]
    if isinstance(value, np.ndarray) and value.ndim == 0:
        return value.item()
    return value


def _read_json_dataset(group: h5py.Group, key: str) -> dict:
    if key not in group:
        return {}
    raw = group[key][()]
    if isinstance(raw, (bytes, bytearray, np.bytes_)):
        raw = raw.decode("utf-8")
    try:
        parsed = json.loads(str(raw))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _decode_name(value: Any) -> str:
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        return bytes(value).decode("utf-8")
    return str(value)


def summarize_feature_matrix(
    feature_names: np.ndarray,
    feature_values: np.ndarray,
    *,
    prefix: str,
) -> dict[str, float]:
    if feature_values.size == 0 or feature_names.size == 0:
        return {}

    values = np.asarray(feature_values, dtype=float)
    if values.ndim != 2 or values.shape[1] != len(feature_names):
        return {}

    rows: dict[str, float] = {}
    decoded_names = [_decode_name(name) for name in feature_names]
    for column_idx, feature_name in enumerate(decoded_names):
        column = finite_array(values[:, column_idx])
        rows[f"{prefix}_{feature_name}_median"] = float(np.median(column)) if column.size else np.nan
    return rows


def iter_h5_paths(processed_root: Path, limit: int | None = None) -> Iterable[Path]:
    paths = sorted(processed_root.rglob("*.h5"))
    if limit is not None and limit > 0:
        return paths[:limit]
    return paths


def parse_run_identity(path: Path) -> dict:
    match = RUN_ID_RE.match(path.stem)
    if not match:
        raise ValueError(f"Could not parse subject/run/acq from {path.stem}")
    parsed = match.groupdict()
    parsed["subject"] = parsed["subject"].zfill(4)
    parsed["run"] = parsed["run"].zfill(3)
    parsed["acq"] = parsed["acq"].zfill(3)
    return parsed


def read_header_times(raw_root: Path, subject: str, run: str, acq: str) -> dict:
    header_path = raw_root / subject / f"{subject}_{run}_{acq}_EEG.hea"
    if not header_path.exists():
        return {
            "header_path": str(header_path),
            "header_exists": False,
            "channel_count_from_header": np.nan,
            "recording_start_clock": None,
            "recording_end_clock": None,
            "recording_start_elapsed_sec": np.nan,
            "recording_end_elapsed_sec": np.nan,
            "recording_duration_sec_from_header": np.nan,
        }

    start_clock: Optional[str] = None
    end_clock: Optional[str] = None
    channel_count = np.nan
    for line in header_path.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and not np.isfinite(channel_count):
            tokens = line.strip().split()
            if len(tokens) >= 2:
                try:
                    channel_count = float(int(tokens[1]))
                except ValueError:
                    channel_count = np.nan
        if line.startswith("#Start time:"):
            start_clock = line.split(":", 1)[1].strip()
        elif line.startswith("#End time:"):
            end_clock = line.split(":", 1)[1].strip()

    start_elapsed = parse_elapsed_clock(start_clock) if start_clock else np.nan
    end_elapsed = parse_elapsed_clock(end_clock) if end_clock else np.nan
    duration = end_elapsed - start_elapsed if np.isfinite(start_elapsed) and np.isfinite(end_elapsed) else np.nan
    if np.isfinite(duration) and duration < 0:
        duration = np.nan

    return {
        "header_path": str(header_path),
        "header_exists": True,
        "channel_count_from_header": channel_count,
        "recording_start_clock": start_clock,
        "recording_end_clock": end_clock,
        "recording_start_elapsed_sec": start_elapsed,
        "recording_end_elapsed_sec": end_elapsed,
        "recording_duration_sec_from_header": duration,
    }


def finite_array(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim == 0:
        arr = arr.reshape(1)
    return arr[np.isfinite(arr)]


def summarize_jacobian(jacobian: np.ndarray) -> dict:
    if jacobian.size == 0:
        return {
            "jacobian_windows": 0,
            "jacobian_fro_median": np.nan,
            "jacobian_trace_median": np.nan,
            "jacobian_spectral_radius_median": np.nan,
            "jacobian_condition_median": np.nan,
        }

    finite_mask = np.isfinite(jacobian).all(axis=(1, 2))
    mats = jacobian[finite_mask]
    if mats.size == 0:
        return {
            "jacobian_windows": 0,
            "jacobian_fro_median": np.nan,
            "jacobian_trace_median": np.nan,
            "jacobian_spectral_radius_median": np.nan,
            "jacobian_condition_median": np.nan,
        }

    fro = np.linalg.norm(mats, axis=(1, 2))
    trace = np.trace(mats, axis1=1, axis2=2)
    spectral_radius = np.array([np.max(np.abs(np.linalg.eigvals(mat))) for mat in mats], dtype=float)
    condition = np.array([np.linalg.cond(mat) for mat in mats], dtype=float)

    return {
        "jacobian_windows": int(mats.shape[0]),
        "jacobian_fro_median": float(np.median(finite_array(fro))) if finite_array(fro).size else np.nan,
        "jacobian_trace_median": float(np.median(finite_array(trace))) if finite_array(trace).size else np.nan,
        "jacobian_spectral_radius_median": float(np.median(finite_array(spectral_radius)))
        if finite_array(spectral_radius).size
        else np.nan,
        "jacobian_condition_median": float(np.median(finite_array(condition)))
        if finite_array(condition).size
        else np.nan,
    }


def summarize_stage_labels(labels: np.ndarray) -> dict:
    if labels.size == 0:
        return {"stage_label_unique": "", "stage_n2_proxy_fraction": np.nan, "stage_unknown_fraction": np.nan}
    numeric = pd.to_numeric(pd.Series(labels), errors="coerce").to_numpy(dtype=float)
    valid = numeric[np.isfinite(numeric)]
    if valid.size == 0:
        return {"stage_label_unique": "", "stage_n2_proxy_fraction": np.nan, "stage_unknown_fraction": np.nan}
    unique_codes = sorted({int(code) for code in valid})
    return {
        "stage_label_unique": ",".join(str(code) for code in unique_codes),
        "stage_n2_proxy_fraction": float(np.mean(valid == 2)),
        "stage_unknown_fraction": float(np.mean(valid == -1)),
    }


def read_time_reference(h5: h5py.File) -> dict:
    attrs = h5.attrs
    has_extension = "extensions" in h5 and "time_reference" in h5["extensions"]
    run_group = h5["extensions"]["time_reference"]["run"] if has_extension and "run" in h5["extensions"]["time_reference"] else None
    window_group = (
        h5["extensions"]["time_reference"]["windows"]
        if has_extension and "windows" in h5["extensions"]["time_reference"]
        else None
    )

    window_start_from_anchor = (
        np.asarray(window_group["window_start_from_anchor_sec"][:], dtype=float)
        if window_group is not None and "window_start_from_anchor_sec" in window_group
        else np.array([], dtype=float)
    )
    window_end_from_anchor = (
        np.asarray(window_group["window_end_from_anchor_sec"][:], dtype=float)
        if window_group is not None and "window_end_from_anchor_sec" in window_group
        else np.array([], dtype=float)
    )
    window_bin_labels_raw = (
        _read_optional_array(window_group, "window_bin_label") if window_group is not None else np.array([], dtype=object)
    )
    if window_bin_labels_raw.size:
        labels = [_to_text(value) or "" for value in np.asarray(window_bin_labels_raw).reshape(-1)]
        unique_labels = sorted({label for label in labels if label})
        bin_label_summary = ",".join(unique_labels)
    else:
        bin_label_summary = ""

    parse_errors_value = _to_text(_read_optional_scalar(run_group, "parse_errors")) if run_group is not None else None
    if parse_errors_value in {None, "", "[]", "[\"\"]"}:
        parse_errors_value = None

    return {
        "time_reference_available": bool(has_extension),
        "time_reference_enabled": bool(attrs.get("time_reference_enabled", has_extension)),
        "time_reference_schema_version": _to_text(
            _read_optional_scalar(run_group, "schema_version") if run_group is not None else attrs.get("time_reference_schema_version")
        ),
        "time_reference_parser": _to_text(_read_optional_scalar(run_group, "parser")) if run_group is not None else None,
        "time_reference_status": _to_text(
            _read_optional_scalar(run_group, "status") if run_group is not None else attrs.get("time_reference_status")
        ),
        "time_reference_source": _to_text(attrs.get("time_reference_source")),
        "time_reference_anchor_mode": _to_text(
            _read_optional_scalar(run_group, "anchor_mode") if run_group is not None else attrs.get("time_reference_anchor_mode")
        ),
        "time_reference_header_path": _to_text(
            _read_optional_scalar(run_group, "header_path") if run_group is not None else attrs.get("time_reference_header_path")
        ),
        "time_reference_run_start_clock_raw": _to_text(_read_optional_scalar(run_group, "run_start_clock_raw"))
        if run_group is not None
        else None,
        "time_reference_run_end_clock_raw": _to_text(_read_optional_scalar(run_group, "run_end_clock_raw"))
        if run_group is not None
        else None,
        "time_reference_run_start_clock_sec": _to_float(_read_optional_scalar(run_group, "run_start_clock_sec"))
        if run_group is not None
        else np.nan,
        "time_reference_run_end_clock_sec": _to_float(_read_optional_scalar(run_group, "run_end_clock_sec"))
        if run_group is not None
        else np.nan,
        "time_reference_run_start_elapsed_sec": _to_float(
            _read_optional_scalar(run_group, "run_start_elapsed_sec")
            if run_group is not None
            else attrs.get("time_reference_run_start_elapsed_sec")
        ),
        "time_reference_run_end_elapsed_sec": _to_float(
            _read_optional_scalar(run_group, "run_end_elapsed_sec")
            if run_group is not None
            else attrs.get("time_reference_run_end_elapsed_sec")
        ),
        "time_reference_run_duration_sec": _to_float(_read_optional_scalar(run_group, "run_duration_sec"))
        if run_group is not None
        else np.nan,
        "time_reference_subject_anchor_start_sec": _to_float(
            _read_optional_scalar(run_group, "subject_anchor_start_sec")
            if run_group is not None
            else attrs.get("time_reference_subject_anchor_start_sec")
        ),
        "time_reference_parse_errors": parse_errors_value,
        "time_reference_bins_hours": _to_text(_read_optional_scalar(run_group, "bins_hours")) if run_group is not None else None,
        "time_reference_bins_seconds": _to_text(_read_optional_scalar(run_group, "bins_seconds")) if run_group is not None else None,
        "time_reference_window_start_from_anchor_sec_min": float(window_start_from_anchor.min())
        if window_start_from_anchor.size
        else np.nan,
        "time_reference_window_end_from_anchor_sec_max": float(window_end_from_anchor.max())
        if window_end_from_anchor.size
        else np.nan,
        "time_reference_window_count": int(window_start_from_anchor.size),
        "time_reference_window_bin_label_unique": bin_label_summary,
    }


def summarize_run(path: Path, raw_root: Path, coordinate_contract: str = DEFAULT_COORDINATE_CONTRACT) -> dict:
    identity = parse_run_identity(path)
    header_info = read_header_times(raw_root, identity["subject"], identity["run"], identity["acq"])

    with h5py.File(path, "r") as h5:
        participant = _read_json_dataset(h5["participant"], "row_json") if "participant" in h5 else {}
        mapped = _read_json_dataset(h5["participant"], "mapped_json") if "participant" in h5 else {}
        time_reference = read_time_reference(h5)
        raw_feature_names = np.asarray(h5["features_raw"]["names"]) if "features_raw" in h5 and "names" in h5["features_raw"] else np.array([])
        raw_feature_values = (
            np.asarray(h5["features_raw"]["values"], dtype=float)
            if "features_raw" in h5 and "values" in h5["features_raw"]
            else np.empty((0, 0), dtype=float)
        )
        run_contract = read_run_contract(h5)
        resolved_mnps_3d = resolve_coords_3d(h5, coordinate_contract)
        resolved_coords_9d = resolve_coords_9d(h5, coordinate_contract)
        resolved_jacobian_3d = resolve_jacobian_3d(h5, coordinate_contract)

        mnps_3d = (
            np.asarray(resolved_mnps_3d.values, dtype=float)
            if resolved_mnps_3d is not None
            else np.empty((0, 3), dtype=float)
        )
        time = np.asarray(h5["time"], dtype=float) if "time" in h5 else np.array([], dtype=float)
        window_start = np.asarray(h5["window_start"], dtype=float) if "window_start" in h5 else np.array([], dtype=float)
        window_end = np.asarray(h5["window_end"], dtype=float) if "window_end" in h5 else np.array([], dtype=float)
        coords_9d = (
            np.asarray(resolved_coords_9d.values, dtype=float)
            if resolved_coords_9d is not None
            else np.empty((0, 0), dtype=float)
        )
        jacobian = (
            np.asarray(resolved_jacobian_3d.j_hat, dtype=float)
            if resolved_jacobian_3d is not None
            else np.empty((0, 0, 0), dtype=float)
        )
        stage_labels = (
            np.asarray(h5["labels"]["stage"])
            if "labels" in h5 and "stage" in h5["labels"]
            else np.array([], dtype=float)
        )

    resolved_start = time_reference["time_reference_run_start_elapsed_sec"]
    resolved_end = time_reference["time_reference_run_end_elapsed_sec"]
    resolved_source = "time_reference"
    if not np.isfinite(resolved_start) or not np.isfinite(resolved_end):
        resolved_start = header_info["recording_start_elapsed_sec"]
        resolved_end = header_info["recording_end_elapsed_sec"]
        resolved_source = "wfdb_header" if np.isfinite(resolved_start) and np.isfinite(resolved_end) else "missing"

    row: Dict[str, object] = {
        "subject": f"sub-{identity['subject']}",
        "subject_numeric": identity["subject"],
        "run": int(identity["run"]),
        "acq": int(identity["acq"]),
        "processed_h5_path": str(path),
        "group": mapped.get("group"),
        "condition": mapped.get("condition"),
        "task": mapped.get("task"),
        "hospital": participant.get("hospital"),
        "age": participant.get("age"),
        "sex": participant.get("sex"),
        "rosc_minutes": participant.get("rosc"),
        "ohca": participant.get("ohca"),
        "shockable_rhythm": participant.get("shockable_rhythm"),
        "ttm_celsius": participant.get("ttm"),
        "outcome": participant.get("outcome"),
        "cpc": participant.get("cpc"),
        "requested_coordinate_contract": coordinate_contract,
        "resolved_coordinate_contract": (
            resolved_mnps_3d.resolved_coordinate_contract
            if resolved_mnps_3d is not None
            else None
        ),
        "primary_coordinate_contract": run_contract.primary_coordinate_contract,
        "primary_coordinate_layer": run_contract.primary_coordinate_layer,
        "anchor_id": run_contract.anchor_id,
        "anchor_hash": run_contract.anchor_hash,
        "schema_version": run_contract.schema_version,
        "mndm_version": run_contract.mndm_version,
        "mnps_source_dataset_path": resolved_mnps_3d.values_path if resolved_mnps_3d is not None else None,
        "coords_9d_source_dataset_path": resolved_coords_9d.values_path if resolved_coords_9d is not None else None,
        "jacobian_source_dataset_path": resolved_jacobian_3d.dataset_path if resolved_jacobian_3d is not None else None,
        "n_windows": int(mnps_3d.shape[0]),
        "n_coords_9d_rows": int(coords_9d.shape[0]),
        "h5_time_start_sec": float(time[0]) if time.size else np.nan,
        "h5_time_end_sec": float(time[-1]) if time.size else np.nan,
        "h5_window_start_sec": float(window_start[0]) if window_start.size else np.nan,
        "h5_window_end_sec": float(window_end[-1]) if window_end.size else np.nan,
        "h5_duration_sec": float(window_end[-1] - window_start[0]) if window_start.size and window_end.size else np.nan,
        "resolved_run_start_elapsed_sec": resolved_start,
        "resolved_run_end_elapsed_sec": resolved_end,
        "resolved_run_duration_sec": resolved_end - resolved_start
        if np.isfinite(resolved_start) and np.isfinite(resolved_end)
        else np.nan,
        "resolved_timing_source": resolved_source,
        "artifact_detector_enabled": False,
        "artifact_burden": np.nan,
    }
    row.update(header_info)
    row.update(time_reference)
    row["channel_coverage_frac_of_21"] = (
        float(row["channel_count_from_header"]) / EXPECTED_MAX_CHANNELS
        if np.isfinite(float(row["channel_count_from_header"]))
        else np.nan
    )
    row.update(summarize_feature_matrix(raw_feature_names, raw_feature_values, prefix="rawfeat"))

    if mnps_3d.size:
        diffs = np.diff(mnps_3d, axis=0)
        step_norm = np.linalg.norm(diffs, axis=1) if diffs.size else np.array([], dtype=float)
        displacement = float(np.linalg.norm(mnps_3d[-1] - mnps_3d[0])) if mnps_3d.shape[0] >= 2 else np.nan
        row.update(
            {
                "m_median": float(np.nanmedian(mnps_3d[:, 0])),
                "d_median": float(np.nanmedian(mnps_3d[:, 1])),
                "e_median": float(np.nanmedian(mnps_3d[:, 2])),
                "m_iqr": float(np.nanpercentile(mnps_3d[:, 0], 75) - np.nanpercentile(mnps_3d[:, 0], 25)),
                "d_iqr": float(np.nanpercentile(mnps_3d[:, 1], 75) - np.nanpercentile(mnps_3d[:, 1], 25)),
                "e_iqr": float(np.nanpercentile(mnps_3d[:, 2], 75) - np.nanpercentile(mnps_3d[:, 2], 25)),
                "mnps_path_length": float(np.nansum(step_norm)) if step_norm.size else 0.0,
                "mnps_step_norm_median": float(np.nanmedian(step_norm)) if step_norm.size else np.nan,
                "mnps_displacement": displacement,
            }
        )

    if coords_9d.size:
        row["coords_9d_row_valid_fraction"] = float(np.mean(np.isfinite(coords_9d).all(axis=1)))
        row["coords_9d_global_std_mean"] = float(np.nanmean(np.nanstd(coords_9d, axis=0)))

    row.update(summarize_jacobian(jacobian))
    row.update(summarize_stage_labels(stage_labels))
    return row


def assign_relative_time(run_table: pd.DataFrame) -> pd.DataFrame:
    if run_table.empty:
        return run_table.copy()

    out = run_table.copy()
    out["run_start_from_anchor_sec"] = np.nan
    out["run_end_from_anchor_sec"] = np.nan
    out["run_midpoint_from_anchor_sec"] = np.nan
    out["run_anchor_source"] = None
    out["subject_anchor_inconsistent"] = False
    out["subject_anchor_candidate_count"] = 0

    for subject, group in out.groupby("subject", dropna=False):
        idx = group.index
        time_ref_start = pd.to_numeric(group["time_reference_run_start_elapsed_sec"], errors="coerce")
        time_ref_end = pd.to_numeric(group["time_reference_run_end_elapsed_sec"], errors="coerce")
        header_start = pd.to_numeric(group["recording_start_elapsed_sec"], errors="coerce")
        header_end = pd.to_numeric(group["recording_end_elapsed_sec"], errors="coerce")
        anchor_candidates = pd.to_numeric(group["time_reference_subject_anchor_start_sec"], errors="coerce")
        finite_anchor = anchor_candidates[np.isfinite(anchor_candidates)]
        anchor_unique = pd.Series(finite_anchor).dropna().astype(float).nunique() if not finite_anchor.empty else 0
        anchor_inconsistent = bool(anchor_unique > 1)
        subject_anchor_start = float(finite_anchor.iloc[0]) if not finite_anchor.empty else np.nan
        fallback_origin = float(header_start[np.isfinite(header_start)].min()) if np.isfinite(header_start).any() else np.nan

        start_values = np.full(len(group), np.nan, dtype=float)
        end_values = np.full(len(group), np.nan, dtype=float)
        source_values = np.full(len(group), "", dtype=object)

        for offset, row_index in enumerate(idx):
            start_val = time_ref_start.loc[row_index]
            end_val = time_ref_end.loc[row_index]
            if np.isfinite(start_val) and np.isfinite(end_val):
                start_values[offset] = float(start_val)
                end_values[offset] = float(end_val)
                source_values[offset] = "time_reference"
                continue

            hdr_start = header_start.loc[row_index]
            hdr_end = header_end.loc[row_index]
            if np.isfinite(hdr_start) and np.isfinite(hdr_end) and np.isfinite(subject_anchor_start):
                start_values[offset] = float(hdr_start - subject_anchor_start)
                end_values[offset] = float(hdr_end - subject_anchor_start)
                source_values[offset] = "wfdb_header_subject_anchor"
                continue

            if np.isfinite(hdr_start) and np.isfinite(hdr_end) and np.isfinite(fallback_origin):
                start_values[offset] = float(hdr_start - fallback_origin)
                end_values[offset] = float(hdr_end - fallback_origin)
                source_values[offset] = "wfdb_header_first_recording"
                continue

            source_values[offset] = "missing"

        out.loc[idx, "run_start_from_anchor_sec"] = start_values
        out.loc[idx, "run_end_from_anchor_sec"] = end_values
        out.loc[idx, "run_midpoint_from_anchor_sec"] = (start_values + end_values) / 2.0
        out.loc[idx, "run_anchor_source"] = source_values
        out.loc[idx, "subject_anchor_inconsistent"] = anchor_inconsistent
        out.loc[idx, "subject_anchor_candidate_count"] = int(anchor_unique)

    for col in [
        "run_start_from_anchor_sec",
        "run_end_from_anchor_sec",
        "run_midpoint_from_anchor_sec",
    ]:
        out[col.replace("_sec", "_hours")] = pd.to_numeric(out[col], errors="coerce") / 3600.0

    # Backward-compatible aliases for older article code and existing result names.
    out["recording_start_from_first_sec"] = out["run_start_from_anchor_sec"]
    out["recording_end_from_first_sec"] = out["run_end_from_anchor_sec"]
    out["recording_midpoint_from_first_sec"] = out["run_midpoint_from_anchor_sec"]
    out["recording_start_from_first_hours"] = out["run_start_from_anchor_hours"]
    out["recording_end_from_first_hours"] = out["run_end_from_anchor_hours"]
    out["recording_midpoint_from_first_hours"] = out["run_midpoint_from_anchor_hours"]
    return out


def assign_time_bins(run_table: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    out = run_table.copy()
    labels: List[Optional[str]] = []
    for midpoint in pd.to_numeric(out["run_midpoint_from_anchor_hours"], errors="coerce"):
        label: Optional[str] = None
        if np.isfinite(midpoint):
            for lower, upper, name in config.time_bins_hours:
                if lower <= float(midpoint) < upper:
                    label = name
                    break
        labels.append(label)
    out["time_bin"] = labels
    out["time_bin_assignment_method"] = "run_midpoint"
    out["time_bin_assignment_note"] = (
        "Runs are assigned to bins by run_midpoint_from_anchor_hours; runs spanning multiple bins contribute to one bin only."
    )
    return out


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    v = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    w = pd.to_numeric(weights, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(v) & np.isfinite(w) & (w > 0)
    if not np.any(mask):
        return float("nan")
    return float(np.average(v[mask], weights=w[mask]))


def choose_patient_metric_weight_column(group: pd.DataFrame) -> str:
    for candidate in ("n_windows", "time_reference_window_count", "jacobian_windows"):
        if candidate not in group.columns:
            continue
        values = pd.to_numeric(group[candidate], errors="coerce")
        if (np.isfinite(values) & (values > 0)).any():
            return candidate
    return "__unit_weight__"


def build_patient_bin_summary(run_table: pd.DataFrame) -> pd.DataFrame:
    if run_table.empty:
        return pd.DataFrame()

    rows: List[Dict[str, object]] = []
    metric_cols = [
        "m_median",
        "d_median",
        "e_median",
        "m_iqr",
        "d_iqr",
        "e_iqr",
        "mnps_path_length",
        "mnps_step_norm_median",
        "mnps_displacement",
        "jacobian_fro_median",
        "jacobian_trace_median",
        "jacobian_spectral_radius_median",
        "jacobian_condition_median",
        "coords_9d_global_std_mean",
        "stage_n2_proxy_fraction",
        "stage_unknown_fraction",
    ]
    metric_cols.extend(sorted(column for column in run_table.columns if column.startswith("rawfeat_")))
    run_table = run_table.copy()
    run_table["__unit_weight__"] = 1.0

    for (subject, time_bin), group in run_table.groupby(["subject", "time_bin"], dropna=False):
        weight_column = choose_patient_metric_weight_column(group)
        weights = pd.to_numeric(group[weight_column], errors="coerce").fillna(
            1.0 if weight_column == "__unit_weight__" else 0.0
        )
        row: Dict[str, object] = {
            "subject": subject,
            "time_bin": time_bin,
            "n_runs": int(len(group)),
            "n_windows_total": int(pd.to_numeric(group["n_windows"], errors="coerce").fillna(0).sum()),
            "metric_weight_column": weight_column,
            "metric_weight_total": float(weights.sum()),
            "outcome": group["outcome"].dropna().iloc[0] if group["outcome"].notna().any() else None,
            "cpc": group["cpc"].dropna().iloc[0] if group["cpc"].notna().any() else np.nan,
            "hospital": group["hospital"].dropna().iloc[0] if group["hospital"].notna().any() else None,
            "age": float(pd.to_numeric(group["age"], errors="coerce").median())
            if np.isfinite(pd.to_numeric(group["age"], errors="coerce")).any()
            else np.nan,
            "sex": group["sex"].dropna().iloc[0] if group["sex"].notna().any() else None,
            "rosc_minutes": float(pd.to_numeric(group["rosc_minutes"], errors="coerce").median())
            if np.isfinite(pd.to_numeric(group["rosc_minutes"], errors="coerce")).any()
            else np.nan,
            "ohca": group["ohca"].dropna().iloc[0] if group["ohca"].notna().any() else None,
            "shockable_rhythm": group["shockable_rhythm"].dropna().iloc[0]
            if group["shockable_rhythm"].notna().any()
            else None,
            "ttm_celsius": float(pd.to_numeric(group["ttm_celsius"], errors="coerce").median())
            if np.isfinite(pd.to_numeric(group["ttm_celsius"], errors="coerce")).any()
            else np.nan,
            "run_start_from_anchor_hours_min": float(
                pd.to_numeric(group["run_start_from_anchor_hours"], errors="coerce").min()
            ),
            "run_end_from_anchor_hours_max": float(
                pd.to_numeric(group["run_end_from_anchor_hours"], errors="coerce").max()
            ),
            "time_reference_available_all": bool(group["time_reference_available"].fillna(False).all()),
            "time_reference_status_unique": ",".join(
                sorted({str(value) for value in group["time_reference_status"].dropna() if str(value).strip()})
            ),
            "run_anchor_source_unique": ",".join(
                sorted({str(value) for value in group["run_anchor_source"].dropna() if str(value).strip()})
            ),
            "recording_start_after_anchor_hours": float(
                pd.to_numeric(group["run_start_from_anchor_hours"], errors="coerce").min()
            ),
            "recording_end_after_anchor_hours": float(
                pd.to_numeric(group["run_end_from_anchor_hours"], errors="coerce").max()
            ),
            "channel_count_median": float(
                pd.to_numeric(group["channel_count_from_header"], errors="coerce").median()
            )
            if np.isfinite(pd.to_numeric(group["channel_count_from_header"], errors="coerce")).any()
            else np.nan,
            "channel_coverage_frac_median": float(
                pd.to_numeric(group["channel_coverage_frac_of_21"], errors="coerce").median()
            )
            if np.isfinite(pd.to_numeric(group["channel_coverage_frac_of_21"], errors="coerce")).any()
            else np.nan,
            "artifact_detector_enabled_all": bool(group["artifact_detector_enabled"].fillna(False).all()),
            "artifact_burden_mean": float(
                pd.to_numeric(group["artifact_burden"], errors="coerce").mean()
            )
            if np.isfinite(pd.to_numeric(group["artifact_burden"], errors="coerce")).any()
            else np.nan,
        }
        for metric in metric_cols:
            if metric not in group.columns:
                row[metric] = np.nan
                continue
            row[metric] = weighted_mean(group[metric], weights)
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["subject", "time_bin"]).reset_index(drop=True)


def build_subject_outcome_index(run_table: pd.DataFrame) -> pd.DataFrame:
    if run_table.empty:
        return pd.DataFrame()
    columns = [
        "subject",
        "hospital",
        "age",
        "sex",
        "rosc_minutes",
        "ohca",
        "shockable_rhythm",
        "ttm_celsius",
        "outcome",
        "cpc",
    ]
    return run_table[columns].drop_duplicates().sort_values("subject").reset_index(drop=True)


def build_run_table(config: AnalysisConfig) -> pd.DataFrame:
    h5_paths = list(iter_h5_paths(config.processed_root, config.limit_h5))
    if config.workers <= 1 or len(h5_paths) <= 1:
        run_rows = [
            summarize_run(path, config.raw_root, config.coordinate_contract)
            for path in h5_paths
        ]
    else:
        with ProcessPoolExecutor(max_workers=config.workers) as executor:
            run_rows = list(
                executor.map(
                    summarize_run,
                    h5_paths,
                    repeat(config.raw_root),
                    repeat(config.coordinate_contract),
                    chunksize=8,
                )
            )
    if not run_rows:
        return pd.DataFrame()
    run_table = pd.DataFrame(run_rows).sort_values(["subject", "run", "acq"]).reset_index(drop=True)
    run_table = assign_relative_time(run_table)
    run_table = assign_time_bins(run_table, config)
    return run_table


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    run_table = build_run_table(config)
    subject_outcomes = build_subject_outcome_index(run_table)
    patient_bin_summary = build_patient_bin_summary(run_table)

    run_table.to_csv(config.output_dir / "run_timing_metadata.csv", index=False)
    subject_outcomes.to_csv(config.output_dir / "subject_outcome_index.csv", index=False)
    patient_bin_summary.to_csv(config.output_dir / "patient_timebin_summaries.csv", index=False)

    summary_payload = {
        "processed_root": str(config.processed_root),
        "raw_root": str(config.raw_root),
        "coordinate_contract": config.coordinate_contract,
        "n_h5_runs": int(len(run_table)),
        "n_subjects": int(run_table["subject"].nunique()) if not run_table.empty else 0,
        "time_bin_scheme": config.time_bin_scheme,
        "time_axis_note": (
            "Primary run-level timing now comes from H5 time_reference.v1 when available; "
            "WFDB header parsing is retained as a fallback for older exports or missing extensions."
        ),
        "time_reference_available_runs": int(run_table["time_reference_available"].fillna(False).sum())
        if not run_table.empty
        else 0,
        "time_anchor_sources": (
            run_table["run_anchor_source"].fillna("missing").value_counts(dropna=False).to_dict()
            if not run_table.empty
            else {}
        ),
        "time_status_counts": (
            run_table["time_reference_status"].fillna("missing").value_counts(dropna=False).to_dict()
            if not run_table.empty
            else {}
        ),
        "time_bins_hours": [
            {"label": label, "start_h": lower, "end_h": upper if np.isfinite(upper) else None}
            for lower, upper, label in config.time_bins_hours
        ],
        "time_bin_assignment_method": "run_midpoint",
        "time_bin_assignment_note": (
            "Runs are assigned to time bins by run midpoint. This is exact for aggregate windows such as 0_12h, "
            "but hourly bins should be interpreted as localized summaries rather than exact window-splitting counts."
        ),
        "subjects_with_inconsistent_anchor_candidates": (
            int(run_table.groupby("subject")["subject_anchor_inconsistent"].max().fillna(False).sum())
            if not run_table.empty
            else 0
        ),
        "subjects": subject_outcomes.to_dict(orient="records"),
    }
    (config.output_dir / "timeline_summary.json").write_text(
        json.dumps(summary_payload, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote run timing metadata to {config.output_dir / 'run_timing_metadata.csv'}")
    print(f"Wrote subject outcome index to {config.output_dir / 'subject_outcome_index.csv'}")
    print(f"Wrote patient time-bin summaries to {config.output_dir / 'patient_timebin_summaries.csv'}")
    if not run_table.empty:
        first_row = run_table.iloc[0]
        print(
            "Example timing:",
            first_row["subject"],
            f"run={int(first_row['run']):03d}",
            f"time_status={first_row['time_reference_status']}",
            f"anchor_source={first_row['run_anchor_source']}",
            f"start_from_anchor_h={format_hours(float(first_row['run_start_from_anchor_hours']))}",
            f"outcome={first_row['outcome']}",
            f"cpc={first_row['cpc']}",
        )


if __name__ == "__main__":
    main()
