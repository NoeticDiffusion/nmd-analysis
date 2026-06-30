"""
Regional MNPS: Per-network MNPS coordinate construction from fMRI BOLD.

This module computes network-level m/d/e coordinates for Regional MNPS analysis,
treating each canonical network as a separate sub-manifold.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import h5py
import numpy as np

from .network_grouping import (
    PRIMARY_NETWORKS,
    get_network_summary,
    map_rois_to_networks,
)


@dataclass
class NetworkMNPS:
    """MNPS coordinates for a single network."""

    network: str
    time: np.ndarray
    m: np.ndarray
    d: np.ndarray
    e: np.ndarray
    n_regions: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def x(self) -> np.ndarray:
        """Return stacked ``[m, d, e]`` coordinates."""

        return np.column_stack([self.m, self.d, self.e])

    def summary_stats(self) -> Dict[str, Dict[str, float]]:
        """Compute summary statistics for each axis."""

        stats: Dict[str, Dict[str, float]] = {}
        for name, arr in [("m", self.m), ("d", self.d), ("e", self.e)]:
            finite = arr[np.isfinite(arr)]
            if len(finite) == 0:
                stats[name] = {
                    "mean": np.nan,
                    "std": np.nan,
                    "median": np.nan,
                    "mad": np.nan,
                    "iqr": np.nan,
                }
            else:
                med = float(np.median(finite))
                mad = float(np.median(np.abs(finite - med)))
                q25, q75 = np.percentile(finite, [25, 75])
                stats[name] = {
                    "mean": float(np.mean(finite)),
                    "std": float(np.std(finite)),
                    "median": med,
                    "mad": mad,
                    "iqr": float(q75 - q25),
                    "min": float(np.min(finite)),
                    "max": float(np.max(finite)),
                }
        return stats


@dataclass
class RegionalMNPSResult:
    """Complete Regional MNPS result for a subject."""

    subject_id: str
    networks: Dict[str, NetworkMNPS]
    global_time: np.ndarray
    roi_names: List[str]
    network_summary: Dict[str, Dict[str, int]]
    sfreq: float
    window_sec: float
    step_sec: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dictionary."""

        return {
            "subject_id": self.subject_id,
            "sfreq": self.sfreq,
            "window_sec": self.window_sec,
            "step_sec": self.step_sec,
            "n_rois": len(self.roi_names),
            "network_summary": self.network_summary,
            "networks": {
                net: {
                    "n_regions": nm.n_regions,
                    "n_windows": len(nm.time),
                    "stats": nm.summary_stats(),
                }
                for net, nm in self.networks.items()
            },
        }


def compute_windowed_entropy(
    bold: np.ndarray,
    sfreq: float,
    window_sec: float = 8.0,
    step_sec: float = 4.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute windowed log-variance entropy proxy."""

    if bold.ndim == 1:
        bold = bold.reshape(1, -1)

    n_regions, n_times = bold.shape
    w_samp = int(window_sec * sfreq)
    s_samp = int(step_sec * sfreq)

    if n_times < w_samp or s_samp <= 0:
        return np.array([]), np.array([])

    n_windows = (n_times - w_samp) // s_samp + 1
    time_centers = np.array([(i * s_samp + w_samp / 2) / sfreq for i in range(n_windows)])

    entropy_values = np.zeros(n_windows)
    for i in range(n_windows):
        start = i * s_samp
        end = start + w_samp
        segment = bold[:, start:end]
        var_per_region = np.var(segment, axis=1)
        entropy_values[i] = np.mean(np.log(var_per_region + 1e-12))

    return time_centers, entropy_values


def compute_windowed_mobility(
    bold: np.ndarray,
    sfreq: float,
    window_sec: float = 8.0,
    step_sec: float = 4.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute windowed mobility from centroid derivative variance."""

    if bold.ndim == 1:
        bold = bold.reshape(1, -1)

    centroid = np.mean(bold, axis=0)
    n_times = len(centroid)
    w_samp = int(window_sec * sfreq)
    s_samp = int(step_sec * sfreq)

    if n_times < w_samp or s_samp <= 0:
        return np.array([]), np.array([])

    n_windows = (n_times - w_samp) // s_samp + 1
    time_centers = np.array([(i * s_samp + w_samp / 2) / sfreq for i in range(n_windows)])

    mobility_values = np.zeros(n_windows)
    for i in range(n_windows):
        start = i * s_samp
        end = start + w_samp
        segment = centroid[start:end]
        deriv = np.diff(segment)
        mobility_values[i] = np.var(deriv)

    return time_centers, mobility_values


def compute_windowed_diffusivity(
    bold: np.ndarray,
    sfreq: float,
    window_sec: float = 8.0,
    step_sec: float = 4.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute windowed intra-network spread."""

    if bold.ndim == 1:
        bold = bold.reshape(1, -1)

    n_regions, n_times = bold.shape
    w_samp = int(window_sec * sfreq)
    s_samp = int(step_sec * sfreq)

    if n_times < w_samp or s_samp <= 0 or n_regions < 2:
        return np.array([]), np.array([])

    n_windows = (n_times - w_samp) // s_samp + 1
    time_centers = np.array([(i * s_samp + w_samp / 2) / sfreq for i in range(n_windows)])

    diffusivity_values = np.zeros(n_windows)
    for i in range(n_windows):
        start = i * s_samp
        end = start + w_samp
        segment = bold[:, start:end]
        if segment.shape[1] > 1:
            centroid = np.mean(segment, axis=0, keepdims=True)
            deviations = np.abs(segment - centroid)
            diffusivity_values[i] = np.mean(deviations)
        else:
            diffusivity_values[i] = 0.0

    return time_centers, diffusivity_values


def robust_normalize(arr: np.ndarray, epsilon: float = 1e-12) -> np.ndarray:
    """Robust z-normalization followed by logistic squashing to ``[0, 1]``."""

    arr = np.asarray(arr, dtype=np.float64)
    finite_mask = np.isfinite(arr)
    if not np.any(finite_mask):
        return np.full_like(arr, 0.5)

    finite_vals = arr[finite_mask]
    median = np.median(finite_vals)
    mad = np.median(np.abs(finite_vals - median))

    if mad < epsilon:
        std = np.std(finite_vals)
        if std < epsilon:
            return np.full_like(arr, 0.5)
        z = (arr - np.mean(finite_vals)) / std
    else:
        z = (arr - median) / (1.4826 * mad)

    return 1 / (1 + np.exp(-z))


def compute_network_mnps(
    bold: np.ndarray,
    roi_names: List[str],
    sfreq: float,
    network: str,
    network_indices: List[int],
    window_sec: float = 8.0,
    step_sec: float = 4.0,
) -> Optional[NetworkMNPS]:
    """Compute MNPS coordinates for a single network."""

    if not network_indices or len(network_indices) < 2:
        return None

    network_bold = bold[network_indices, :]

    time_e, entropy_raw = compute_windowed_entropy(network_bold, sfreq, window_sec, step_sec)
    _, mobility_raw = compute_windowed_mobility(network_bold, sfreq, window_sec, step_sec)
    _, diffusivity_raw = compute_windowed_diffusivity(network_bold, sfreq, window_sec, step_sec)

    if len(time_e) == 0:
        return None

    return NetworkMNPS(
        network=network,
        time=time_e,
        m=robust_normalize(mobility_raw),
        d=robust_normalize(diffusivity_raw),
        e=robust_normalize(entropy_raw),
        n_regions=len(network_indices),
        metadata={"roi_names": [roi_names[i] for i in network_indices]},
    )


def compute_regional_mnps(
    bold: np.ndarray,
    roi_names: List[str],
    sfreq: float,
    subject_id: str = "unknown",
    window_sec: float = 8.0,
    step_sec: float = 4.0,
    networks: Optional[List[str]] = None,
) -> RegionalMNPSResult:
    """Compute Regional MNPS for all selected networks from BOLD data."""

    if networks is None:
        networks = PRIMARY_NETWORKS

    network_indices = map_rois_to_networks(roi_names)
    network_summary = get_network_summary(roi_names)

    network_mnps: Dict[str, NetworkMNPS] = {}
    global_time = None

    for net in networks:
        indices = network_indices.get(net, [])
        result = compute_network_mnps(
            bold, roi_names, sfreq, net, indices, window_sec, step_sec
        )
        if result is not None:
            network_mnps[net] = result
            if global_time is None:
                global_time = result.time

    if global_time is None:
        n_times = bold.shape[1]
        w_samp = int(window_sec * sfreq)
        s_samp = int(step_sec * sfreq)
        n_windows = max(1, (n_times - w_samp) // s_samp + 1)
        global_time = np.array([(i * s_samp + w_samp / 2) / sfreq for i in range(n_windows)])

    return RegionalMNPSResult(
        subject_id=subject_id,
        networks=network_mnps,
        global_time=global_time,
        roi_names=roi_names,
        network_summary=network_summary,
        sfreq=sfreq,
        window_sec=window_sec,
        step_sec=step_sec,
    )


def load_and_compute_regional_mnps(
    h5_path: Path,
    window_sec: float = 8.0,
    step_sec: float = 4.0,
    networks: Optional[List[str]] = None,
) -> Optional[RegionalMNPSResult]:
    """Load regional BOLD from HDF5 and compute Regional MNPS."""

    with h5py.File(h5_path, "r") as handle:
        if "regions" not in handle:
            return None

        bold = handle["regions"]["bold"][:]
        try:
            names = [n.decode("utf-8") for n in handle["regions"]["names"][:]]
        except Exception:
            names = [f"ROI_{i}" for i in range(bold.shape[0])]

        attrs = dict(handle["regions"].attrs.items())
        sfreq = attrs.get("sfreq", 0.5)
        subject_id = Path(h5_path).stem

    return compute_regional_mnps(
        bold, names, sfreq, subject_id, window_sec, step_sec, networks
    )


def save_regional_mnps_to_h5(
    result: RegionalMNPSResult,
    h5_path: Path,
    group_name: str = "regional_mnps",
) -> None:
    """Save a Regional MNPS result to HDF5."""

    with h5py.File(h5_path, "a") as handle:
        if group_name in handle:
            del handle[group_name]

        grp = handle.create_group(group_name)
        grp.attrs["subject_id"] = result.subject_id
        grp.attrs["sfreq"] = result.sfreq
        grp.attrs["window_sec"] = result.window_sec
        grp.attrs["step_sec"] = result.step_sec
        grp.attrs["n_networks"] = len(result.networks)
        grp.create_dataset("time", data=result.global_time)

        for net, nm in result.networks.items():
            net_grp = grp.create_group(net)
            net_grp.attrs["n_regions"] = nm.n_regions
            net_grp.create_dataset("x", data=nm.x)
            net_grp.create_dataset("m", data=nm.m)
            net_grp.create_dataset("d", data=nm.d)
            net_grp.create_dataset("e", data=nm.e)


def load_regional_mnps_from_h5(
    h5_path: Path,
    group_name: str = "regional_mnps",
) -> Optional[RegionalMNPSResult]:
    """Load a Regional MNPS result from HDF5."""

    with h5py.File(h5_path, "r") as handle:
        if group_name not in handle:
            return None

        grp = handle[group_name]
        subject_id = grp.attrs.get("subject_id", Path(h5_path).stem)
        sfreq = grp.attrs.get("sfreq", 0.5)
        window_sec = grp.attrs.get("window_sec", 8.0)
        step_sec = grp.attrs.get("step_sec", 4.0)
        global_time = grp["time"][:]

        networks: Dict[str, NetworkMNPS] = {}
        for net in grp.keys():
            if net == "time":
                continue
            net_grp = grp[net]
            networks[net] = NetworkMNPS(
                network=net,
                time=global_time,
                m=net_grp["m"][:],
                d=net_grp["d"][:],
                e=net_grp["e"][:],
                n_regions=int(net_grp.attrs.get("n_regions", 0)),
            )

        return RegionalMNPSResult(
            subject_id=subject_id,
            networks=networks,
            global_time=global_time,
            roi_names=[],
            network_summary={},
            sfreq=sfreq,
            window_sec=window_sec,
            step_sec=step_sec,
        )
