"""Shared utilities for the ds003645 healthy EEG--MEG concordance study."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

import h5py
import numpy as np
import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[1]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
DATASET_ROOT = REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds003645_20260722_215042"
RESULT_STAMP = "20260723"
RESULTS_DIR = ARTICLE_DIR / "results" / f"eeg_meg_ds003645_{RESULT_STAMP}"
FIGURES_DIR = ARTICLE_DIR / "figures"

TOPOLOGIES = (
    "left_anterior",
    "left_posterior",
    "midline_anterior",
    "midline_posterior",
    "right_anterior",
    "right_posterior",
)
MNPS_AXES = ("m", "d", "e")
REGIONAL_PREFIXES = ("__g_eeg_", "__g_meg_")
RUN_SLUG_RE = re.compile(
    r"^(?P<subject_id>sub-\d+)_meeg_FacePerception_(?P<run>run-\d+)\.h5$"
)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def list_h5_paths(dataset_root: Path = DATASET_ROOT) -> list[Path]:
    """Return participant H5 exports, excluding the empty-room recording."""

    return sorted(
        path
        for path in dataset_root.rglob("*.h5")
        if "emptyroom" not in path.name.lower()
        and RUN_SLUG_RE.match(path.name) is not None
    )


def parse_run_slug(path: Path) -> tuple[str, str]:
    match = RUN_SLUG_RE.match(path.name)
    if match is None:
        raise ValueError(f"Unrecognised ds003645 H5 name: {path.name}")
    return match.group("subject_id"), match.group("run")


def decode(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return decode(value.item())
        return [decode(item) for item in value.tolist()]
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        return bytes(value).decode("utf-8", errors="replace")
    if isinstance(value, np.generic):
        return value.item()
    return value


def json_dataset(handle: h5py.File, path: str) -> dict[str, Any]:
    if path not in handle:
        return {}
    try:
        raw = decode(handle[path][()])
        parsed = json.loads(str(raw))
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, TypeError, OSError):
        return {}


def h5_metadata(handle: h5py.File, h5_path: Path) -> dict[str, Any]:
    subject_id, run = parse_run_slug(h5_path)
    mapped = json_dataset(handle, "participant/mapped_json")
    participant = json_dataset(handle, "participant/row_json")
    return {
        "subject_id": subject_id,
        "run": run,
        "h5_path": str(h5_path),
        "group": str(mapped.get("group") or handle.attrs.get("group") or ""),
        "condition": str(mapped.get("condition") or handle.attrs.get("condition") or ""),
        "task": str(mapped.get("task") or handle.attrs.get("task") or ""),
        "age": participant.get("age"),
        "gender": participant.get("gender"),
    }


def feature_names_and_values(
    handle: h5py.File, surface: str = "features_projection_z"
) -> tuple[list[str], np.ndarray]:
    group = handle[surface]
    names = [str(decode(value)) for value in group["names"][()]]
    values = np.asarray(group["values"][:], dtype=float)
    if values.ndim != 2 or values.shape[1] != len(names):
        raise ValueError(f"Invalid {surface} layout.")
    return names, values


def topography_from_name(name: str) -> str | None:
    for topo in TOPOLOGIES:
        if name.endswith(f"__g_eeg_{topo}") or name.endswith(f"__g_meg_{topo}"):
            return topo
    return None


def family_from_name(name: str) -> str:
    """Remove modality and regional suffixes to produce a paired feature key."""

    base = name.split("__g_", maxsplit=1)[0]
    for prefix in ("eeg_", "meg_mag_", "meg_grad_", "meg_"):
        if base.startswith(prefix):
            return base.removeprefix(prefix)
    return base


def nan_summary(values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=float)
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return {"mean": float("nan"), "std": float("nan"), "median": float("nan")}
    return {
        "mean": float(np.mean(finite)),
        "std": float(np.std(finite, ddof=1)) if finite.size > 1 else 0.0,
        "median": float(np.median(finite)),
    }


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    ensure_dir(path.parent)
    frame.to_csv(path, index=False)


def benjamini_hochberg(p_values: Iterable[float]) -> np.ndarray:
    """Return BH adjusted q-values, retaining NaN for invalid input."""

    values = np.asarray(list(p_values), dtype=float)
    q_values = np.full(values.size, np.nan, dtype=float)
    valid = np.flatnonzero(np.isfinite(values))
    if valid.size == 0:
        return q_values
    order = valid[np.argsort(values[valid])]
    ranked = values[order] * valid.size / np.arange(1, valid.size + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    q_values[order] = np.minimum(ranked, 1.0)
    return q_values
