"""Shared support for medication-stratified psychosis turning-angle analysis.

The parent article uses cohort-anchored MNPS as its primary between-subject
contract.  This module therefore defaults to that contract; subject-anchored
coordinates are an explicitly labelled robustness sensitivity, never an
unmarked substitute.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

import h5py
import numpy as np
from scipy.stats import spearmanr


SRC_DIR = Path(__file__).resolve().parent
ARTICLE_DIR = SRC_DIR.parent
REPO_ROOT = ARTICLE_DIR.parents[2]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.h5_contract import resolve_coords_3d, resolve_coords_9d  # noqa: E402


DATASETS = ("ds003944", "ds003947")
RAW_ROOTS: Dict[str, Tuple[Path, ...]] = {
    "ds003944": (REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds003944_20260520_121126",),
    "ds003947": (REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds003947_20260520_114135",),
}
NAMES_9D: Tuple[str, ...] = ("m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m")
CHARTS: Dict[str, Tuple[str, ...]] = {
    "3d": ("m", "d", "e"),
    "9d": NAMES_9D,
    "m3": ("m_a", "m_e", "m_o"),
    "d3": ("d_n", "d_l", "d_s"),
    "e3": ("e_e", "e_s", "e_m"),
}
LAGS = (1, 2, 4)
MIN_VALID_ANGLES = 30
STEP_LENGTH_FILTER_PERCENTILE = 10.0
N_PERMUTATIONS = 200
ENTROPY_N_BINS = 12
TIME_GAP_FACTOR = 1.5
EPS = 1e-12

CONTRASTS = {
    "FEP_unmedicated_vs_Healthy": ("Healthy", "FEP unmedicated"),
    "FEP_medicated_vs_Healthy": ("Healthy", "FEP medicated"),
    "FEP_medicated_vs_FEP_unmedicated": ("FEP unmedicated", "FEP medicated"),
    "FEP_vs_Healthy_sensitivity": ("Healthy", "FEP"),
}


def discover_h5_files(dataset: str, raw_root: Optional[Path] = None) -> list[Path]:
    """Discover one resting H5 per subject, preferring the requested root."""
    roots = (raw_root,) if raw_root is not None else RAW_ROOTS[dataset]
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for subject_dir in sorted(root.glob("sub-*")):
            paths.extend(sorted(subject_dir.glob("*.h5")))
        if paths:
            break
    return paths


def assign_medication_group(participant: Dict[str, Any]) -> Optional[str]:
    """Use the parent article's CPZ-at-scan grouping rule."""
    participant_type = str(participant.get("type", "")).strip()
    if participant_type == "Control":
        return "Healthy"
    if participant_type != "Psychosis":
        return None
    try:
        cpz = float(participant.get("CPZ_at_scan"))
        return "FEP medicated" if np.isfinite(cpz) and cpz > 0 else "FEP unmedicated"
    except (TypeError, ValueError):
        return "FEP unmedicated"


def read_participant(handle: h5py.File) -> Dict[str, Any]:
    try:
        raw = handle["participant/row_json"][()]
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)
    except Exception:
        return {}


def read_time(handle: h5py.File, length: int) -> np.ndarray:
    if "time" in handle:
        values = np.asarray(handle["time"], dtype=float)
    elif "window_start" in handle and "window_end" in handle:
        values = 0.5 * (np.asarray(handle["window_start"], dtype=float) + np.asarray(handle["window_end"], dtype=float))
    elif "window_start" in handle:
        values = np.asarray(handle["window_start"], dtype=float)
    else:
        values = np.arange(length, dtype=float)
    return values[:length]


def contiguous_segments(time: np.ndarray) -> list[np.ndarray]:
    """Return row-index segments, breaking at non-positive/large time gaps."""
    time = np.asarray(time, dtype=float)
    if time.size == 0:
        return []
    finite = np.isfinite(time)
    diffs = np.diff(time)
    positive = diffs[np.isfinite(diffs) & (diffs > 0)]
    baseline = float(np.median(positive)) if positive.size else 1.0
    gap = max(baseline * TIME_GAP_FACTOR, baseline + EPS)
    breaks = np.r_[True, ~finite[1:] | ~finite[:-1] | (diffs <= 0) | (diffs > gap)]
    valid_indices = np.flatnonzero(finite)
    if valid_indices.size == 0:
        return []
    segments: list[np.ndarray] = []
    start = 0
    for index in range(1, valid_indices.size):
        if valid_indices[index] != valid_indices[index - 1] + 1 or breaks[valid_indices[index]]:
            segments.append(valid_indices[start:index])
            start = index
    segments.append(valid_indices[start:])
    return [segment for segment in segments if segment.size]


def read_subject_h5(path: Path, coordinate_contract: str) -> Optional[Dict[str, Any]]:
    """Read native 3D and 9D coordinates plus metadata from one psychosis H5."""
    with h5py.File(path, "r") as handle:
        coords3 = resolve_coords_3d(handle, coordinate_contract)
        coords9 = resolve_coords_9d(handle, coordinate_contract)
        if coords3 is None or coords9 is None:
            return None
        n_rows = min(coords3.values.shape[0], coords9.values.shape[0])
        time = read_time(handle, n_rows)
        n_rows = min(n_rows, time.size)
        if n_rows == 0:
            return None
        participant = read_participant(handle)
    return {
        "path": str(path),
        "subject": str(participant.get("participant_id", path.parent.name)),
        "participant": participant,
        "group": assign_medication_group(participant),
        "coords3": np.asarray(coords3.values[:n_rows, :3], dtype=float),
        "coords9": np.asarray(coords9.values[:n_rows], dtype=float),
        "names9": tuple(coords9.names),
        "time": np.asarray(time[:n_rows], dtype=float),
        "coordinate_contract": coordinate_contract,
    }


def chart_arrays(subject: Dict[str, Any]) -> Dict[str, np.ndarray]:
    """Return native 3D, 9D, and family subspaces in the fixed release order."""
    names = list(subject["names9"])
    index = {name: i for i, name in enumerate(names)}
    if not all(name in index for name in NAMES_9D):
        return {}
    coords9 = subject["coords9"]
    return {
        "3d": subject["coords3"],
        "9d": np.column_stack([coords9[:, index[name]] for name in NAMES_9D]),
        "m3": np.column_stack([coords9[:, index[name]] for name in CHARTS["m3"]]),
        "d3": np.column_stack([coords9[:, index[name]] for name in CHARTS["d3"]]),
        "e3": np.column_stack([coords9[:, index[name]] for name in CHARTS["e3"]]),
    }


def unit_vectors(vectors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    norms = np.linalg.norm(vectors, axis=1)
    units = vectors / np.where(norms > EPS, norms, np.nan)[:, None]
    return units, norms


def segment_step_lengths(coords: np.ndarray, segments: Iterable[np.ndarray], lag: int) -> np.ndarray:
    chunks = []
    for segment in segments:
        values = coords[segment]
        if values.shape[0] > lag:
            chunks.append(np.linalg.norm(values[lag:] - values[:-lag], axis=1))
    return np.concatenate(chunks) if chunks else np.empty(0)


def compute_turning_triples(
    coords: np.ndarray, segments: Iterable[np.ndarray], lag: int, step_length_threshold: float
) -> Optional[Dict[str, Any]]:
    """Compute valid triples separately inside contiguous time segments."""
    cos_chunks: list[np.ndarray] = []
    theta_chunks: list[np.ndarray] = []
    step_chunks: list[np.ndarray] = []
    disp_unit_chunks: list[np.ndarray] = []
    n_total = n_short = 0
    for segment in segments:
        values = coords[segment]
        if values.shape[0] <= 2 * lag:
            continue
        t = np.arange(lag, values.shape[0] - lag)
        u, v = values[t] - values[t - lag], values[t + lag] - values[t]
        unit_u, norm_u = unit_vectors(u)
        unit_v, norm_v = unit_vectors(v)
        valid = np.isfinite(values[t - lag]).all(axis=1) & np.isfinite(values[t]).all(axis=1) & np.isfinite(values[t + lag]).all(axis=1)
        valid &= np.isfinite(norm_u) & np.isfinite(norm_v)
        keep = valid & (norm_u >= step_length_threshold) & (norm_v >= step_length_threshold)
        n_total += int(valid.size)
        n_short += int(valid.sum() - keep.sum())
        if keep.any():
            cosine = np.clip(np.sum(unit_u[keep] * unit_v[keep], axis=1), -1.0, 1.0)
            cos_chunks.append(cosine)
            theta_chunks.append(np.degrees(np.arccos(cosine)))
            step_chunks.append(0.5 * (norm_u[keep] + norm_v[keep]))
        disp = values[lag:] - values[:-lag]
        units, norms = unit_vectors(disp)
        disp_unit_chunks.append(units[np.isfinite(norms)])
    if not cos_chunks:
        return None
    cosine, theta, steps = np.concatenate(cos_chunks), np.concatenate(theta_chunks), np.concatenate(step_chunks)
    if theta.size < MIN_VALID_ANGLES:
        return None
    return {
        "cos_theta": cosine,
        "theta_deg": theta,
        "mean_step_length": steps,
        "disp_units": np.concatenate(disp_unit_chunks) if disp_unit_chunks else np.empty((0, coords.shape[1])),
        "n_valid": int(theta.size),
        "n_excluded_short_step": n_short,
        "n_total_triples": n_total,
    }


def angle_entropy(theta: np.ndarray) -> float:
    counts, _ = np.histogram(theta[np.isfinite(theta)], bins=ENTROPY_N_BINS, range=(0, 180))
    probabilities = counts[counts > 0] / counts.sum() if counts.sum() else np.empty(0)
    return float(-np.sum(probabilities * np.log(probabilities))) if probabilities.size else float("nan")


def turn_length_coupling(theta: np.ndarray, steps: np.ndarray) -> float:
    if theta.size < 5 or np.nanstd(theta) < EPS or np.nanstd(steps) < EPS:
        return float("nan")
    value, _ = spearmanr(theta, steps)
    return float(value) if np.isfinite(value) else float("nan")


def stable_seed(*parts: object) -> int:
    digest = int(hashlib.md5("|".join(map(str, parts)).encode()).hexdigest(), 16)
    return digest % (2**32 - 1)


def permutation_null_z(units: np.ndarray, observed_median: float, *, seed: int, n_perms: int) -> tuple[float, float, float]:
    if units.shape[0] < MIN_VALID_ANGLES + 1 or n_perms < 2:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    indices = np.argsort(rng.random((n_perms, units.shape[0])), axis=1)
    shuffled = units[indices]
    cosine = np.clip(np.sum(shuffled[:, :-1] * shuffled[:, 1:], axis=2), -1.0, 1.0)
    null_medians = np.median(np.degrees(np.arccos(cosine)), axis=1)
    null_mean, null_sd = float(np.mean(null_medians)), float(np.std(null_medians, ddof=1))
    return ((float((observed_median - null_mean) / null_sd) if null_sd > EPS else float("nan")), null_mean, null_sd)
