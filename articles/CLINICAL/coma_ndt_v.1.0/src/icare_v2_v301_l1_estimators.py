"""Registered L1 estimators for SL-004A cohort-frame confirmation.

The producer write-gate refuses amplification on non-subject-anchored
layer names. Confirmatory analysis applies the same numerical functions
to `coords_3d_cohort_anchored` values without claiming a new ingest
product. Diffusion has no such layer-name refuse.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import numpy as np

DEFAULT_MNDM_SRC = Path(
    os.environ.get("MNDM_SRC", r"H:\SourceRepo2\NeuralManifoldDynamics\mndm\src")
)
AMP_WRITE_LAYER = "coords_3d_subject_anchored"


def ensure_mndm(src: Path | None = None) -> Path:
    root = Path(src) if src is not None else DEFAULT_MNDM_SRC
    if not (root / "mndm").is_dir():
        raise FileNotFoundError(f"MNDM src not found: {root}")
    text = str(root)
    if text not in sys.path:
        sys.path.insert(0, text)
    return root


def _segment_id(raw_file: np.ndarray | None, n: int) -> np.ndarray:
    if raw_file is None:
        return np.zeros(n, dtype=np.int32)
    names = np.asarray(
        [
            item.decode("utf-8", errors="replace") if isinstance(item, (bytes, np.bytes_)) else str(item)
            for item in raw_file
        ],
        dtype=object,
    )
    if names.size != n:
        return np.zeros(n, dtype=np.int32)
    _, inverse = np.unique(names, return_inverse=True)
    return np.asarray(inverse, dtype=np.int32)


def estimate_g90(state: np.ndarray, time: np.ndarray, *, segment_id: np.ndarray | None, chart_name: str) -> dict[str, Any]:
    """Same-pair G90. `chart_name` is analysis provenance, not a write path."""
    ensure_mndm()
    from mndm.dynamical_families.amplification import estimate_neighbor_gain_q90

    del chart_name
    return estimate_neighbor_gain_q90(
        np.asarray(state, dtype=float),
        np.asarray(time, dtype=float),
        segment_id=segment_id,
        coordinate_layer=AMP_WRITE_LAYER,
        coordinate_names=["m", "d", "e"],
    )


def estimate_diffusion(state: np.ndarray, time: np.ndarray, *, segment_id: np.ndarray | None, chart_name: str) -> dict[str, Any]:
    ensure_mndm()
    from mndm.dynamical_families.diffusion_geometry import estimate_local_diffusion_geometry

    return estimate_local_diffusion_geometry(
        np.asarray(state, dtype=float),
        np.asarray(time, dtype=float),
        segment_id=segment_id,
        coordinate_layer=str(chart_name),
        coordinate_names=["m", "d", "e"],
        neighborhood_k=20,
        min_samples=30,
        min_neighborhood_samples=10,
        max_dt_relative_deviation=0.05,
        min_valid_fraction=0.1,
        psd_floor=1e-8,
        epsilon=1e-12,
    )


def series_median(result: dict[str, Any], name: str) -> float:
    series = (result.get("series") or {}).get(name)
    if series is None:
        return float("nan")
    values = np.asarray(series, dtype=float).reshape(-1)
    finite = values[np.isfinite(values)]
    return float(np.median(finite)) if finite.size else float("nan")


def series_mae(left: np.ndarray | None, right: np.ndarray | None) -> tuple[float, float, int]:
    if left is None or right is None:
        return float("nan"), float("nan"), 0
    a = np.asarray(left, dtype=float).reshape(-1)
    b = np.asarray(right, dtype=float).reshape(-1)
    n = min(a.size, b.size)
    mask = np.isfinite(a[:n]) & np.isfinite(b[:n])
    if not mask.any():
        return float("nan"), float("nan"), 0
    delta = np.abs(a[:n][mask] - b[:n][mask])
    return float(np.mean(delta)), float(np.max(delta)), int(mask.sum())
