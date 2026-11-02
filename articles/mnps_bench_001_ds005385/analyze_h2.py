"""Analyze the frozen MNPS-BENCH-001 H2 fast-core/MNJ comparison.

This downstream analysis reads only the selected processed HDF5 recordings.
It consumes the saved 4-second M1/M2/E1/E2 values, derives local 4D Jacobians
with the frozen NMD projection/Jacobian kernels, and never re-computes EEG
measurements from EDF data.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_h1 as h1


DEFAULT_NMD_ROOT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics")
DEFAULT_SELECTION = Path(
    r"H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\bench_001\selection_manifest_outcome_blind.json"
)
DEFAULT_PROTOCOL = Path(
    r"H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\bench_001\mnps_bench_001_protocol_frozen_v1_20261007.md"
)
DEFAULT_AMENDMENT = Path(
    r"H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\bench_001\mnps_bench_001_amendment_1_m3_vector_20261007.md"
)
DEFAULT_CONFIG = Path(
    r"H:\SourceRepo2\NeuralManifoldDynamics\mndm\config\sources\openneuro\config_ingest_mnps_bench_001_ds005385_fast4s.yaml"
)
DEFAULT_INDEX = Path(
    r"K:\ExternalReceivedDatasets\mnps_bench_001_ds005385\fast4s_processed\ds005385\file_index.csv"
)

FAST_FEATURES = ("PCV", "TP", "OI", "SC")
FAST_CANDIDATES = {"PCV": "M1", "TP": "M2", "OI": "E1", "SC": "E2"}
MNJ_FEATURES = (
    "mnj_frobenius_norm",
    "mnj_antisymmetric_frobenius_norm",
    "mnj_symmetric_frobenius_norm",
    "mnj_singular_value_anisotropy",
)
FAST_ARM = "fast_core_4s"
MNJ_ARM = "fast_core_4s_plus_mnj"
FAST_PLUS_FEATURES = FAST_FEATURES + MNJ_FEATURES
MIN_SUPPORTED_SEC = 60.0
MIN_COHORT = 80
MIN_MNJ_CENTERS = 30
MIN_MNJ_CENTER_FRACTION = 0.50
WINDOW_SEC = 4.0
STEP_SEC = 4.0
MAX_TIME_GAP_SEC = 5.0
MAX_JUMP_SIGMA = 5.0
SAVGOL_WINDOW = 7
SAVGOL_POLYORDER = 3
MIN_SEGMENT = 9
KNN_K = 20
SUPER_WINDOW = 3
RIDGE_ALPHA = 1.0
DISTANCE_WEIGHTED = True
ANISOTROPY_MIN_SINGULAR = 1e-10
ANISOTROPY_MAX = 1e6

NMD_ANALYSIS_CODE = (
    "mndm/src/mndm/projection.py",
    "mndm/src/mndm/jacobian.py",
    "mndm/src/mndm/pipeline/regional_mnps.py",
)
H2_FILE_PATTERN = re.compile(
    r"(?P<subject>sub-\d+).*?ses-1.*?task-(?P<state>EyesClosed|EyesOpen).*?acq-pre.*?\.edf$",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class H2Recording:
    subject: str
    state: str
    raw_file: str
    features: Mapping[str, Mapping[str, float]]
    coverage: tuple[Mapping[str, Any], ...]
    qc: Mapping[str, Any]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_nmd_kernels(nmd_root: Path = DEFAULT_NMD_ROOT):
    """Import the exact upstream derivative, kNN and local-Jacobian kernels."""
    source = (nmd_root / "mndm" / "src").resolve()
    if not source.is_dir():
        raise FileNotFoundError(f"NMDM source directory is missing: {source}")
    source_text = str(source)
    if source_text not in sys.path:
        sys.path.insert(0, source_text)
    from mndm import jacobian, projection  # imported after the path is set

    return projection, jacobian


def matrix_mnj_metrics(jacobian_matrix: np.ndarray) -> dict[str, float]:
    """Return the four frozen scalar summaries for one finite square J."""
    matrix = np.asarray(jacobian_matrix, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or not np.isfinite(matrix).all():
        return {name: math.nan for name in MNJ_FEATURES}
    symmetric = 0.5 * (matrix + matrix.T)
    antisymmetric = 0.5 * (matrix - matrix.T)
    try:
        singular_values = np.linalg.svd(matrix, compute_uv=False)
        largest = float(singular_values[0]) if singular_values.size else math.nan
        smallest = float(singular_values[-1]) if singular_values.size else math.nan
        anisotropy = (
            float(np.clip(largest / smallest, 1.0, ANISOTROPY_MAX))
            if np.isfinite(largest) and np.isfinite(smallest) and smallest > ANISOTROPY_MIN_SINGULAR
            else math.nan
        )
    except np.linalg.LinAlgError:
        anisotropy = math.nan
    return {
        "mnj_frobenius_norm": float(np.linalg.norm(matrix, ord="fro")),
        "mnj_antisymmetric_frobenius_norm": float(np.linalg.norm(antisymmetric, ord="fro")),
        "mnj_symmetric_frobenius_norm": float(np.linalg.norm(symmetric, ord="fro")),
        "mnj_singular_value_anisotropy": anisotropy,
    }


def _validate_h2_time_grid(starts: np.ndarray, ends: np.ndarray | None = None) -> None:
    """Require the frozen cadence within time segments; retain larger gaps."""
    t = np.asarray(starts, dtype=np.float64).reshape(-1)
    if not np.isfinite(t).all():
        raise ValueError("Invalid H2 window start times")
    deltas = np.diff(t)
    if np.any(deltas <= 0):
        raise ValueError("H2 window start times must be strictly increasing")
    within_segment = deltas <= MAX_TIME_GAP_SEC
    if np.any(~np.isclose(deltas[within_segment], STEP_SEC, rtol=0.0, atol=1e-6)):
        raise ValueError("H2 realization is not on the frozen 4-second cadence")
    if ends is not None:
        e = np.asarray(ends, dtype=np.float64).reshape(-1)
        if e.shape != t.shape or not np.isfinite(e).all():
            raise ValueError("Invalid H2 window intervals")
        if np.any(~np.isclose(e - t, WINDOW_SEC, rtol=0.0, atol=1e-6)):
            raise ValueError("H2 realization is not on the frozen 4-second window grid")


def _trajectory_segments(
    values: np.ndarray,
    starts: np.ndarray,
    *,
    projection: Any,
    step_sec: float = STEP_SEC,
    max_gap_sec: float = MAX_TIME_GAP_SEC,
    max_jump_sigma: float = MAX_JUMP_SIGMA,
) -> list[np.ndarray]:
    """Split complete rows at time gaps and the frozen robust-jump threshold."""
    x = np.asarray(values, dtype=np.float64)
    t = np.asarray(starts, dtype=np.float64).reshape(-1)
    if x.ndim != 2 or x.shape[0] != t.size:
        raise ValueError("trajectory values and start times must have matching row counts")
    _validate_h2_time_grid(t)
    finite_indices = np.flatnonzero(np.isfinite(x).all(axis=1) & np.isfinite(t))
    if finite_indices.size == 0:
        return []

    gap_breaks: list[int] = []
    for position in range(1, finite_indices.size):
        previous = int(finite_indices[position - 1])
        current = int(finite_indices[position])
        delta = float(t[current] - t[previous])
        if current != previous + 1 or not np.isfinite(delta) or delta <= 0 or delta > max_gap_sec:
            gap_breaks.append(position)
    gap_blocks = np.split(finite_indices, gap_breaks)

    robust_scale = float(getattr(projection, "ROBUST_MAD_TO_SIGMA", 1.4826))
    segments: list[np.ndarray] = []
    for block in gap_blocks:
        if block.size == 0:
            continue
        block_values = x[block]
        if block.size < 2:
            segments.append(block)
            continue
        jumps = np.linalg.norm(np.diff(block_values, axis=0), axis=1)
        median = float(np.median(jumps)) if jumps.size else 0.0
        mad = float(np.median(np.abs(jumps - median))) if jumps.size else 0.0
        sigma = robust_scale * mad if np.isfinite(mad) and mad > 0 else float(np.std(jumps))
        if not np.isfinite(sigma) or sigma <= 0:
            sigma = 1.0
        threshold = median + float(max_jump_sigma) * sigma
        jump_breaks = np.flatnonzero(jumps > threshold) + 1
        segments.extend(segment for segment in np.split(block, jump_breaks) if segment.size)
    return segments


def _finite_center_under_determined_count(
    centers: Sequence[int],
    nn_indices: np.ndarray,
    jacobian_module: Any,
    *,
    total: int,
    dim: int = 4,
    super_window: int = SUPER_WINDOW,
) -> int:
    """Count attempted centers with fewer than d(d+1) unique fit rows."""
    required = int(dim * (dim + 1))
    count = 0
    gather = getattr(jacobian_module, "_gather_indices")
    for center in centers:
        support = gather(int(center), nn_indices, int(super_window), int(total))
        if int(np.asarray(support).size) < required:
            count += 1
    return count


def compute_mnj_series(
    values: np.ndarray,
    starts: Sequence[float],
    ends: Sequence[float],
    *,
    projection: Any,
    jacobian_module: Any,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    """Estimate H2 4D MNJ metrics from saved fast-core window values."""
    x = np.asarray(values, dtype=np.float64)
    t = np.asarray(starts, dtype=np.float64).reshape(-1)
    _validate_h2_time_grid(t, np.asarray(ends, dtype=np.float64))
    intervals = list(zip(t.tolist(), np.asarray(ends, dtype=np.float64).reshape(-1).tolist(), strict=True))
    collected: dict[str, list[tuple[float, tuple[float, float]]]] = {name: [] for name in MNJ_FEATURES}
    attempted = 0
    finite_jacobians = 0
    underdetermined = 0

    for absolute_rows in _trajectory_segments(x, t, projection=projection):
        if absolute_rows.size < 3:
            continue
        segment_values = np.asarray(x[absolute_rows], dtype=np.float32)
        segment_starts = t[absolute_rows]
        attempted_centers = np.arange(SUPER_WINDOW // 2, segment_values.shape[0] - SUPER_WINDOW // 2, dtype=np.int32)
        attempted += int(attempted_centers.size)
        if attempted_centers.size == 0:
            continue
        x_dot = projection.estimate_derivatives_segmented(
            segment_values,
            STEP_SEC,
            method="sav_gol",
            max_jump=MAX_JUMP_SIGMA,
            min_seg=MIN_SEGMENT,
            savgol_window=SAVGOL_WINDOW,
            polyorder=SAVGOL_POLYORDER,
        )
        nn_indices = projection.build_knn_indices(
            segment_values,
            k=KNN_K,
            metric="euclidean",
            whiten=True,
        )
        underdetermined += _finite_center_under_determined_count(
            attempted_centers,
            nn_indices,
            jacobian_module,
            total=segment_values.shape[0],
        )
        result = jacobian_module.estimate_local_jacobians(
            segment_values,
            x_dot,
            nn_indices,
            super_window=SUPER_WINDOW,
            ridge_alpha=RIDGE_ALPHA,
            distance_weighted=DISTANCE_WEIGHTED,
            j_dot_dt=STEP_SEC,
            knn_k=KNN_K,
            require_determined_support=False,
        )
        center_lookup = np.asarray(result.centers, dtype=np.int64)
        for local_center, matrix in zip(center_lookup, result.j_hat, strict=True):
            j = np.asarray(matrix, dtype=np.float64)
            if j.shape != (4, 4) or not np.isfinite(j).all():
                continue
            finite_jacobians += 1
            global_row = int(absolute_rows[int(local_center)])
            interval = intervals[global_row]
            for name, metric_value in matrix_mnj_metrics(j).items():
                if np.isfinite(metric_value):
                    collected[name].append((float(metric_value), interval))

    features: dict[str, float] = {}
    coverage_rows: list[dict[str, Any]] = []
    for name in MNJ_FEATURES:
        usable = collected[name]
        finite_count = len(usable)
        fraction = finite_count / attempted if attempted else 0.0
        support_seconds = h1.union_duration(interval for _, interval in usable)
        support_pass = (
            finite_count >= MIN_MNJ_CENTERS
            and fraction >= MIN_MNJ_CENTER_FRACTION
            and support_seconds >= MIN_SUPPORTED_SEC
        )
        features[name] = float(np.median([value for value, _ in usable])) if support_pass else math.nan
        reason = None
        if not support_pass:
            if attempted == 0:
                reason = "no_attempted_jacobian_centers"
            elif finite_count < MIN_MNJ_CENTERS:
                reason = "fewer_than_30_finite_centers"
            elif fraction < MIN_MNJ_CENTER_FRACTION:
                reason = "finite_center_fraction_below_50_percent"
            else:
                reason = "unique_supported_time_below_60_seconds"
        coverage_rows.append({
            "arm": MNJ_ARM,
            "feature": name,
            "finite_window_count": finite_count,
            "total_window_count": attempted,
            "supported_seconds": support_seconds,
            "minimum_supported_seconds": MIN_SUPPORTED_SEC,
            "support_pass": bool(support_pass),
            "attempted_center_count": attempted,
            "finite_jacobian_center_count": finite_jacobians,
            "finite_mnj_center_count": finite_count,
            "underdetermined_center_count": underdetermined,
            "finite_center_fraction": fraction,
            "support_basis": "saved_4s_fast_core; finite_4x4_jacobian_centers",
            "reason": reason,
        })
    return features, coverage_rows


def _candidate_value(rows: Sequence[Mapping[str, Any]], candidate_id: str) -> float | None:
    matches = [row for row in rows if str(row.get("candidate_id")) == candidate_id]
    if not matches:
        return None
    row = matches[0]
    if not bool(row.get("computed")) or not bool(row.get("valid")):
        return None
    try:
        value = np.asarray(row.get("value"), dtype=np.float64).reshape(-1)
    except (TypeError, ValueError):
        return None
    if value.size != 1 or not np.isfinite(value[0]):
        return None
    return float(value[0])


def load_h2_recording(path: Path, *, projection: Any, jacobian_module: Any) -> H2Recording:
    """Read and summarize one selected H2 HDF5 recording."""
    coverage_rows: list[dict[str, Any]] = []
    with h5py.File(path, "r") as h5file:
        raw_file = h1._row_source_file(h5file)
        match = H2_FILE_PATTERN.search(Path(raw_file).name)
        if not match:
            raise ValueError(f"Not a session-1 acq-pre EO/EC file: {raw_file}")
        subject = match.group("subject")
        state = "EyesClosed" if match.group("state").lower() == "eyesclosed" else "EyesOpen"
        payloads = h1._json_dataset(h5file["measurements/v3_1/recordings_json"])
        if len(payloads) != 1:
            raise ValueError(f"Expected one v3.1 recording payload in {path}")
        windows = payloads[0]["measurement_payload"].get("windows", [])
        if not windows:
            raise ValueError(f"No saved 4-second v3.1 windows in {path}")
        starts = np.asarray([float(window["window_start_sec"]) for window in windows], dtype=np.float64)
        ends = np.asarray([float(window["window_end_sec"]) for window in windows], dtype=np.float64)
        _validate_h2_time_grid(starts, ends)
        intervals = list(zip(starts.tolist(), ends.tolist(), strict=True))

        candidate_series: dict[str, list[float | None]] = {name: [] for name in FAST_FEATURES}
        for window in windows:
            rows = window.get("measurements", [])
            for feature, candidate_id in FAST_CANDIDATES.items():
                candidate_series[feature].append(_candidate_value(rows, candidate_id))

        fast_features: dict[str, float] = {}
        for feature in FAST_FEATURES:
            aggregate, support = h1._supported_aggregate(
                feature,
                candidate_series[feature],
                intervals,
                subject=subject,
                state=state,
                arm=FAST_ARM,
            )
            fast_features[feature] = float(aggregate[0])
            coverage_rows.append(support)

        matrix = np.asarray([
            [np.nan if value is None else float(value) for value in candidate_series[feature]]
            for feature in FAST_FEATURES
        ], dtype=np.float64).T
        mnj_features, mnj_coverage = compute_mnj_series(
            matrix,
            starts,
            ends,
            projection=projection,
            jacobian_module=jacobian_module,
        )
        for row in mnj_coverage:
            row.update({"subject": subject, "state": state})
        coverage_rows.extend(mnj_coverage)
        qc = h1._recording_qc(h5file, raw_file=raw_file, subject=subject, state=state)

    combined = {**fast_features, **mnj_features}
    return H2Recording(
        subject=subject,
        state=state,
        raw_file=raw_file,
        features={FAST_ARM: fast_features, MNJ_ARM: combined},
        coverage=tuple(coverage_rows),
        qc=qc,
    )


def load_selected_subjects(selection_manifest: Path) -> list[str]:
    return h1.load_selected_subjects(selection_manifest)


def load_h2_run(
    run_dir: Path,
    selected_subjects: Sequence[str],
    *,
    projection: Any,
    jacobian_module: Any,
) -> tuple[dict[tuple[str, str], H2Recording], list[dict[str, Any]]]:
    files = sorted(run_dir.rglob("*.h5"))
    expected = {(subject, state) for subject in selected_subjects for state in h1.STATES}
    records: dict[tuple[str, str], H2Recording] = {}
    coverage: list[dict[str, Any]] = []
    for path in files:
        record = load_h2_recording(path, projection=projection, jacobian_module=jacobian_module)
        key = (record.subject, record.state)
        if key in records:
            raise ValueError(f"Duplicate H2 recording for {key}: {path}")
        records[key] = record
        coverage.extend(record.coverage)
    if set(records) != expected:
        raise ValueError(
            f"H2 recording set mismatch: missing={sorted(expected-set(records))[:10]}, "
            f"extra={sorted(set(records)-expected)[:10]}"
        )
    return records, coverage


def complete_subjects(
    records: Mapping[tuple[str, str], H2Recording],
    subjects: Sequence[str],
    arm: str,
) -> list[str]:
    features = FAST_FEATURES if arm == FAST_ARM else FAST_PLUS_FEATURES
    complete: list[str] = []
    for subject in subjects:
        if all(
            np.isfinite([records[(subject, state)].features[arm][feature] for feature in features]).all()
            for state in h1.STATES
        ):
            complete.append(subject)
    return complete


def summarize_support(
    coverage: Sequence[Mapping[str, Any]],
    subjects: Sequence[str],
    *,
    stage: str,
) -> list[dict[str, Any]]:
    subject_set = set(subjects)
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = {}
    for row in coverage:
        if row.get("subject") in subject_set:
            key = (str(row["arm"]), str(row["feature"]), str(row["state"]))
            grouped.setdefault(key, []).append(row)
    output: list[dict[str, Any]] = []
    for (arm, feature, state), rows in sorted(grouped.items()):
        seconds = [float(row["supported_seconds"]) for row in rows]
        finite = [int(row["finite_window_count"]) for row in rows]
        total = [int(row["total_window_count"]) for row in rows]
        passing = sum(bool(row["support_pass"]) for row in rows)
        output.append({
            "contrast": "H2_fast_core_plus_mnj_vs_fast_core",
            "stage": stage,
            "arm": arm,
            "feature": feature,
            "state": state,
            "n_recordings": len(rows),
            "n_recordings_meeting_support": passing,
            "support_pass_fraction": passing / len(rows) if rows else math.nan,
            "median_supported_seconds": float(np.median(seconds)) if rows else math.nan,
            "minimum_supported_seconds": min(seconds) if rows else math.nan,
            "maximum_supported_seconds": max(seconds) if rows else math.nan,
            "median_finite_centers_or_windows": float(np.median(finite)) if rows else math.nan,
            "median_attempted_centers_or_windows": float(np.median(total)) if rows else math.nan,
            "median_finite_center_fraction": float(np.median([
                float(row.get("finite_center_fraction", 1.0)) for row in rows
            ])) if rows else math.nan,
            "median_underdetermined_center_count": float(np.median([
                float(row.get("underdetermined_center_count", 0)) for row in rows
            ])) if rows else math.nan,
        })
    return output


def _feature_matrix(
    records: Mapping[tuple[str, str], H2Recording],
    subjects: Sequence[str],
    arm: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    columns = FAST_FEATURES if arm == FAST_ARM else FAST_PLUS_FEATURES
    rows: list[list[float]] = []
    labels: list[int] = []
    groups: list[str] = []
    for subject in subjects:
        for state, label in (("EyesClosed", 0), ("EyesOpen", 1)):
            features = records[(subject, state)].features[arm]
            rows.append([float(features[name]) for name in columns])
            labels.append(label)
            groups.append(subject)
    return np.asarray(rows, dtype=np.float64), np.asarray(labels, dtype=np.int8), np.asarray(groups)


def create_analysis_freeze(
    run_dir: Path,
    selection_manifest: Path,
    execution_manifest: Path,
    protocol: Path,
    amendment: Path,
    h2_config: Path,
    h2_index: Path,
    nmd_root: Path,
    out_path: Path,
) -> dict[str, Any]:
    subjects = load_selected_subjects(selection_manifest)
    files = sorted(run_dir.rglob("*.h5"))
    if len(files) != len(subjects) * 2:
        raise ValueError(f"Expected {len(subjects) * 2} H2 HDF5 files; found {len(files)}")
    h2_script = Path(__file__).resolve()
    h2_test = h2_script.with_name("test_analyze_h2.py")
    h1_script = Path(h1.__file__).resolve()
    h1_test = h1_script.with_name("test_analyze_h1.py")
    nmd_code = {
        relpath: {"path": str((nmd_root / relpath).resolve()), "sha256": _sha256(nmd_root / relpath)}
        for relpath in NMD_ANALYSIS_CODE
    }
    file_records = [{"path": str(path.resolve()), "sha256": _sha256(path)} for path in files]
    payload = {
        "schema": "mnps_bench_001_h2_analysis_freeze.v1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "benchmark": "MNPS-BENCH-001",
        "analysis_arm": "H2 fast core plus MNJ versus the identical fast core",
        "run_dir": str(run_dir.resolve()),
        "execution_manifest": {"path": str(execution_manifest.resolve()), "sha256": _sha256(execution_manifest)},
        "selection_manifest": {"path": str(selection_manifest.resolve()), "sha256": _sha256(selection_manifest)},
        "protocol": {"path": str(protocol.resolve()), "sha256": _sha256(protocol)},
        "amendment_1": {"path": str(amendment.resolve()), "sha256": _sha256(amendment)},
        "h2_config": {"path": str(h2_config.resolve()), "sha256": _sha256(h2_config)},
        "h2_index": {"path": str(h2_index.resolve()), "sha256": _sha256(h2_index)},
        "h2_analysis_script": {"path": str(h2_script), "sha256": _sha256(h2_script)},
        "h2_analysis_test": {"path": str(h2_test), "sha256": _sha256(h2_test)},
        "h1_cv_script_dependency": {"path": str(h1_script), "sha256": _sha256(h1_script)},
        "h1_cv_test_dependency": {"path": str(h1_test), "sha256": _sha256(h1_test)},
        "nmd_pipeline_code": nmd_code,
        "selected_subject_count": len(subjects),
        "selected_recording_count": len(files),
        "input_h5_sha256": file_records,
        "analysis_contract": {
            "fast_core_features": list(FAST_FEATURES),
            "mnj_features": list(MNJ_FEATURES),
            "minimum_supported_seconds": MIN_SUPPORTED_SEC,
            "minimum_mnj_centers": MIN_MNJ_CENTERS,
            "minimum_mnj_center_fraction": MIN_MNJ_CENTER_FRACTION,
            "window_sec": WINDOW_SEC,
            "step_sec": STEP_SEC,
            "max_time_gap_sec": MAX_TIME_GAP_SEC,
            "savgol_window": SAVGOL_WINDOW,
            "savgol_polyorder": SAVGOL_POLYORDER,
            "minimum_derivative_segment": MIN_SEGMENT,
            "max_jump_sigma": MAX_JUMP_SIGMA,
            "knn_k": KNN_K,
            "knn_metric": "euclidean",
            "knn_whiten": True,
            "super_window": SUPER_WINDOW,
            "ridge_alpha": RIDGE_ALPHA,
            "distance_weighted": DISTANCE_WEIGHTED,
            "ridge_underdetermined_parameter_count": 20,
            "anisotropy_definition": "largest/smallest singular value; NaN if smallest <= 1e-10; capped at 1e6",
            "outer_folds": h1.OUTER_FOLDS,
            "outer_repeats": h1.OUTER_REPEATS,
            "inner_folds": h1.INNER_FOLDS,
            "C_grid": list(h1.C_GRID),
            "bootstrap_draws": 2000,
            "bootstrap_seed": 20261008,
            "minimum_complete_participants": MIN_COHORT,
        },
        "software": {
            "python": __import__("platform").python_version(),
            "numpy": np.__version__,
            "h5py": h5py.__version__,
            "scikit_learn": __import__("sklearn").__version__,
            "scipy": __import__("scipy").__version__,
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def validate_analysis_freeze(
    freeze_path: Path,
    run_dir: Path,
    selection_manifest: Path,
    execution_manifest: Path,
    nmd_root: Path,
) -> dict[str, Any]:
    frozen = json.loads(freeze_path.read_text(encoding="utf-8"))
    if frozen.get("schema") != "mnps_bench_001_h2_analysis_freeze.v1":
        raise ValueError("Unknown H2 analysis freeze schema")
    if Path(frozen["run_dir"]).resolve() != run_dir.resolve():
        raise ValueError("H2 run directory differs from the frozen run directory")
    fixed_paths = {
        "selection_manifest": selection_manifest.resolve(),
        "execution_manifest": execution_manifest.resolve(),
        "protocol": Path(frozen["protocol"]["path"]).resolve(),
        "amendment_1": Path(frozen["amendment_1"]["path"]).resolve(),
        "h2_config": Path(frozen["h2_config"]["path"]).resolve(),
        "h2_index": Path(frozen["h2_index"]["path"]).resolve(),
        "h2_analysis_script": Path(__file__).resolve(),
        "h2_analysis_test": Path(__file__).resolve().with_name("test_analyze_h2.py"),
        "h1_cv_script_dependency": Path(h1.__file__).resolve(),
        "h1_cv_test_dependency": Path(h1.__file__).resolve().with_name("test_analyze_h1.py"),
    }
    for key, expected_path in fixed_paths.items():
        item = frozen[key]
        if Path(item["path"]).resolve() != expected_path or _sha256(expected_path) != item["sha256"]:
            raise ValueError(f"Frozen H2 input changed: {key}")
    for relpath, item in frozen["nmd_pipeline_code"].items():
        path = Path(item["path"]).resolve()
        if path != (nmd_root / relpath).resolve() or _sha256(path) != item["sha256"]:
            raise ValueError(f"Frozen NMD kernel changed: {relpath}")
    files = sorted(run_dir.rglob("*.h5"))
    input_hashes = {str(Path(item["path"]).resolve()): item["sha256"] for item in frozen["input_h5_sha256"]}
    if {str(path.resolve()) for path in files} != set(input_hashes):
        raise ValueError("H2 HDF5 file set changed after analysis freeze")
    for path in files:
        if _sha256(path) != input_hashes[str(path.resolve())]:
            raise ValueError(f"H2 HDF5 changed after analysis freeze: {path}")
    for key in ("selection_manifest", "execution_manifest"):
        item = frozen[key]
        if _sha256(Path(item["path"])) != item["sha256"]:
            raise ValueError(f"Frozen H2 {key} changed")
    return frozen


def analyze_h2(
    run_dir: Path,
    selection_manifest: Path,
    execution_manifest: Path,
    out_dir: Path,
    *,
    freeze_manifest: Path,
    nmd_root: Path = DEFAULT_NMD_ROOT,
    run_models: bool = True,
) -> dict[str, Any]:
    frozen = validate_analysis_freeze(
        freeze_manifest, run_dir, selection_manifest, execution_manifest, nmd_root,
    )
    projection, jacobian_module = load_nmd_kernels(nmd_root)
    selected = load_selected_subjects(selection_manifest)
    records, coverage = load_h2_run(
        run_dir, selected, projection=projection, jacobian_module=jacobian_module,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    h1._write_csv(out_dir / "feature_support.csv", coverage)
    _write_recording_qc(out_dir / "recording_qc.csv", records, selected)

    fast_complete = complete_subjects(records, selected, FAST_ARM)
    paired_complete = complete_subjects(records, selected, MNJ_ARM)
    coverage_summary = {
        FAST_ARM: {"complete_paired_participants": len(fast_complete), "eligible_participants": len(selected)},
        MNJ_ARM: {"complete_paired_participants": len(paired_complete), "eligible_participants": len(selected)},
        "primary_H2_fast_plus_mnj_vs_fast": {
            "complete_paired_participants": len(paired_complete),
            "eligible_participants": len(selected),
        },
    }
    support_rows = summarize_support(coverage, selected, stage="before_complete_case_restriction")
    support_rows.extend(summarize_support(coverage, paired_complete, stage="after_complete_case_restriction"))
    h1._write_csv(out_dir / "cohort_support.csv", support_rows)
    realization_rows = [
        {"state": records[(subject, state)].state,
         "eeg_channel_count": records[(subject, state)].qc.get("eeg_channel_count"),
         "channel_set_sha256": records[(subject, state)].qc.get("channel_set_sha256"),
         "reference_mode": records[(subject, state)].qc.get("reference_mode"),
         "reference_set_sha256": records[(subject, state)].qc.get("reference_set_sha256"),
         "subject": subject}
        for subject in selected for state in h1.STATES
    ]
    h1._write_csv(out_dir / "cohort_realization.csv", realization_rows)

    status = "coverage_only"
    reason = "model fitting and confirmatory contrasts were intentionally skipped for QC-only review" if not run_models else None
    primary_rows: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
    choice_rows: list[dict[str, Any]] = []
    primary_summary: dict[str, Any] = {}
    if run_models and len(paired_complete) >= MIN_COHORT:
        schedule = h1.make_split_schedule(paired_complete)
        labels = np.tile(np.asarray([0, 1], dtype=np.int8), len(paired_complete))
        groups = np.repeat(np.asarray(paired_complete), 2)
        evaluations: dict[str, dict[str, Any]] = {}
        for arm in (FAST_ARM, MNJ_ARM):
            matrix, arm_labels, arm_groups = _feature_matrix(records, paired_complete, arm)
            if not np.array_equal(arm_labels, labels) or not np.array_equal(arm_groups, groups):
                raise AssertionError("H2 arm row order changed across the paired CV comparison")
            evaluations[arm] = h1.nested_grouped_cv(matrix, labels, groups, schedule)
            choice_rows.extend({"arm": arm, **row} for row in evaluations[arm]["c_choices"])
        differences = np.asarray([
            evaluations[MNJ_ARM]["participant_auc"][subject]
            - evaluations[FAST_ARM]["participant_auc"][subject]
            for subject in paired_complete
        ], dtype=np.float64)
        ci_low, ci_high = h1.paired_bootstrap_interval(differences, n_draws=2000, seed=20261008)
        primary_rows = [
            {"contrast": "H2_fast_plus_mnj_minus_fast_core", "arm": arm,
             "participant_paired_auc": evaluation["paired_auc"],
             "balanced_accuracy": evaluation["balanced_accuracy"],
             "sensitivity": evaluation["sensitivity"],
             "specificity": evaluation["specificity"],
             "n_participants": len(paired_complete)}
            for arm, evaluation in evaluations.items()
        ]
        primary_rows.append({
            "contrast": "H2_fast_plus_mnj_minus_fast_core",
            "arm": "paired_difference",
            "participant_paired_auc": float(np.mean(differences)),
            "ci95_low_conditional_on_fitted_repeated_cv": ci_low,
            "ci95_high_conditional_on_fitted_repeated_cv": ci_high,
            "n_participants": len(paired_complete),
        })
        for arm, evaluation in evaluations.items():
            for index, subject in enumerate(paired_complete):
                for state_index, (state, label) in enumerate((("EyesClosed", 0), ("EyesOpen", 1))):
                    row_index = 2 * index + state_index
                    prediction_rows.append({
                        "arm": arm,
                        "subject": subject,
                        "state": state,
                        "label": label,
                        "mean_out_of_fold_probability": float(evaluation["mean_probability"][row_index]),
                    })
        status = "confirmatory_h2_complete"
        primary_summary = {
            "participant_paired_auc_difference": float(np.mean(differences)),
            "conditional_bootstrap_ci95": [ci_low, ci_high],
            "bootstrap_draws": 2000,
            "bootstrap_seed": 20261008,
            "n_participants": len(paired_complete),
            "folds": {"outer": h1.OUTER_FOLDS, "repeats": h1.OUTER_REPEATS, "inner": h1.INNER_FOLDS},
            "C_grid": list(h1.C_GRID),
        }
    elif run_models:
        status = "coverage_only_below_80_participants"
        reason = "H2 complete-case cohort is below the frozen 80-participant minimum"

    summary = {
        "schema": "mnps_bench_001_h2_analysis.v1",
        "status": status,
        "reason": reason,
        "run_dir": str(run_dir),
        "analysis_freeze_sha256": _sha256(freeze_manifest),
        "execution_manifest_sha256": frozen["execution_manifest"]["sha256"],
        "selection_manifest_sha256": _sha256(selection_manifest),
        "complete_case_counts": coverage_summary,
        "minimum_confirmatory_cohort": MIN_COHORT,
        "primary_h2": primary_summary,
        "analysis_unit": "participant; both states grouped in the same outer and inner folds",
        "h2_fast_core_features": list(FAST_FEATURES),
        "h2_mnj_features": list(MNJ_FEATURES),
    }
    h1._write_csv(out_dir / "primary_h2_results.csv", primary_rows)
    h1._write_csv(out_dir / "outer_predictions.csv", prediction_rows)
    h1._write_csv(out_dir / "inner_c_choices.csv", choice_rows)
    (out_dir / "analysis_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    frozen_files = frozen["input_h5_sha256"]
    run_files = sorted(run_dir.rglob("*.h5"))
    if any(_sha256(path) != item["sha256"] for path, item in zip(run_files, frozen_files, strict=True)):
        raise ValueError("H2 source HDF5 changed while the analysis was running")
    run_manifest = {
        "schema": "mnps_bench_001_h2_run_manifest.v1",
        "analysis_script_sha256": _sha256(Path(__file__).resolve()),
        "analysis_freeze_sha256": _sha256(freeze_manifest),
        "selection_manifest_sha256": _sha256(selection_manifest),
        "h2_run_dir": str(run_dir),
        "h2_input_file_count": len(run_files),
        "h2_input_h5_sha256": frozen_files,
        "summary_status": status,
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def _write_recording_qc(path: Path, records: Mapping[tuple[str, str], H2Recording], subjects: Sequence[str]) -> None:
    rows: list[dict[str, Any]] = []
    for subject in subjects:
        for state in h1.STATES:
            record = records[(subject, state)]
            row = dict(record.qc)
            row.update({"h2_core_feature_count": len(record.features[FAST_ARM]), "h2_mnj_feature_count": len(record.features[MNJ_ARM]) - len(FAST_FEATURES)})
            rows.append(row)
    h1._write_csv(path, rows)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    freeze = subparsers.add_parser("freeze", help="hash finalized H2 inputs before contrasts")
    freeze.add_argument("--h2-run-dir", required=True, type=Path)
    freeze.add_argument("--selection-manifest", required=True, type=Path)
    freeze.add_argument("--execution-manifest", required=True, type=Path)
    freeze.add_argument("--protocol", required=True, type=Path)
    freeze.add_argument("--amendment", required=True, type=Path)
    freeze.add_argument("--h2-config", type=Path, default=DEFAULT_CONFIG)
    freeze.add_argument("--h2-index", type=Path, default=DEFAULT_INDEX)
    freeze.add_argument("--nmd-root", type=Path, default=DEFAULT_NMD_ROOT)
    freeze.add_argument("--out", required=True, type=Path)
    analyze = subparsers.add_parser("analyze", help="run the frozen H2 analysis")
    analyze.add_argument("--h2-run-dir", required=True, type=Path)
    analyze.add_argument("--selection-manifest", required=True, type=Path)
    analyze.add_argument("--execution-manifest", required=True, type=Path)
    analyze.add_argument("--freeze-manifest", required=True, type=Path)
    analyze.add_argument("--out-dir", required=True, type=Path)
    analyze.add_argument("--nmd-root", type=Path, default=DEFAULT_NMD_ROOT)
    analyze.add_argument("--coverage-only", action="store_true", help="skip model fitting; intended for QC only")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "freeze":
        payload = create_analysis_freeze(
            args.h2_run_dir, args.selection_manifest, args.execution_manifest,
            args.protocol, args.amendment, args.h2_config, args.h2_index,
            args.nmd_root, args.out,
        )
        print(json.dumps({"schema": payload["schema"], "recordings": payload["selected_recording_count"], "out": str(args.out)}, indent=2))
        return 0
    summary = analyze_h2(
        args.h2_run_dir, args.selection_manifest, args.execution_manifest,
        args.out_dir, freeze_manifest=args.freeze_manifest,
        nmd_root=args.nmd_root, run_models=not args.coverage_only,
    )
    print(json.dumps({"status": summary["status"], "complete_case_counts": summary["complete_case_counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
