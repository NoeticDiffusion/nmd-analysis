"""
Regional Stratified MNPS: 9D sub-coordinate projection per network.

Extends Regional MNPS from 3D (m, d, e) to 9D Stratified coordinates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import h5py
import numpy as np

from .network_grouping import PRIMARY_NETWORKS, map_rois_to_networks
from .regional_mnps import robust_normalize

STRATIFIED_COORDS = ["m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m"]

STRATIFIED_WEIGHTS = {
    "m_a": {"entropy": -0.7, "lf_power": 0.3, "modularity": 0.0},
    "m_e": {"entropy": -0.3, "lf_power": 0.7, "modularity": 0.0},
    "m_o": {"entropy": 0.0, "lf_power": 1.0, "modularity": 0.0},
    "d_n": {"entropy": 0.0, "lf_power": 0.0, "modularity": 1.0},
    "d_l": {"entropy": 0.5, "lf_power": 0.0, "modularity": 0.5},
    "d_s": {"entropy": 0.0, "lf_power": 0.5, "modularity": 0.5},
    "e_e": {"entropy": 1.0, "lf_power": 0.0, "modularity": 0.0},
    "e_s": {"entropy": 0.5, "lf_power": 0.0, "modularity": -0.5},
    "e_m": {"entropy": 0.0, "lf_power": 0.5, "modularity": -0.5},
}


@dataclass
class NetworkStratifiedMNPS:
    """Stratified MNPS coordinates for a single network."""

    network: str
    time: np.ndarray
    m_a: np.ndarray
    m_e: np.ndarray
    m_o: np.ndarray
    d_n: np.ndarray
    d_l: np.ndarray
    d_s: np.ndarray
    e_e: np.ndarray
    e_s: np.ndarray
    e_m: np.ndarray
    n_regions: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def x9(self) -> np.ndarray:
        """Return stacked 9D coordinates."""

        return np.column_stack(
            [
                self.m_a,
                self.m_e,
                self.m_o,
                self.d_n,
                self.d_l,
                self.d_s,
                self.e_e,
                self.e_s,
                self.e_m,
            ]
        )

    @property
    def coords_dict(self) -> Dict[str, np.ndarray]:
        """Return coordinates as a dictionary."""

        return {
            "m_a": self.m_a,
            "m_e": self.m_e,
            "m_o": self.m_o,
            "d_n": self.d_n,
            "d_l": self.d_l,
            "d_s": self.d_s,
            "e_e": self.e_e,
            "e_s": self.e_s,
            "e_m": self.e_m,
        }

    def summary_stats(self) -> Dict[str, Dict[str, float]]:
        """Compute summary statistics for each sub-coordinate."""

        stats: Dict[str, Dict[str, float]] = {}
        for name in STRATIFIED_COORDS:
            arr = getattr(self, name)
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
class RegionalStratifiedResult:
    """Complete Regional Stratified result for a subject."""

    subject_id: str
    networks: Dict[str, NetworkStratifiedMNPS]
    global_time: np.ndarray
    sfreq: float
    window_sec: float
    step_sec: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "sfreq": self.sfreq,
            "window_sec": self.window_sec,
            "step_sec": self.step_sec,
            "networks": {
                net: {
                    "n_regions": nm.n_regions,
                    "n_windows": len(nm.time),
                    "stats": nm.summary_stats(),
                }
                for net, nm in self.networks.items()
            },
        }


def compute_windowed_features(
    bold: np.ndarray,
    sfreq: float,
    window_sec: float = 8.0,
    step_sec: float = 4.0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute entropy, low-frequency power, and modularity proxy per window."""

    if bold.ndim == 1:
        bold = bold.reshape(1, -1)

    n_regions, n_times = bold.shape
    w_samp = int(window_sec * sfreq)
    s_samp = int(step_sec * sfreq)

    if n_times < w_samp or s_samp <= 0:
        return np.array([]), np.array([]), np.array([]), np.array([])

    n_windows = (n_times - w_samp) // s_samp + 1
    time = np.array([(i * s_samp + w_samp / 2) / sfreq for i in range(n_windows)])

    entropy = np.zeros(n_windows)
    lf_power = np.zeros(n_windows)
    modularity_proxy = np.zeros(n_windows)

    for i in range(n_windows):
        start = i * s_samp
        end = start + w_samp
        segment = bold[:, start:end]

        var_per_region = np.var(segment, axis=1)
        entropy[i] = np.mean(np.log(var_per_region + 1e-12))
        lf_power[i] = np.mean(segment**2)

        if n_regions >= 2:
            segment_z = segment - segment.mean(axis=1, keepdims=True)
            std = segment.std(axis=1, keepdims=True)
            std[std < 1e-12] = 1e-12
            segment_z = segment_z / std
            corr = segment_z @ segment_z.T / w_samp
            mask = ~np.eye(n_regions, dtype=bool)
            modularity_proxy[i] = np.mean(corr[mask])
        else:
            modularity_proxy[i] = 0.0

    return time, entropy, lf_power, modularity_proxy


def project_to_stratified(
    entropy: np.ndarray,
    lf_power: np.ndarray,
    modularity: np.ndarray,
) -> Dict[str, np.ndarray]:
    """Project three base features into 9D stratified coordinates."""

    entropy_norm = robust_normalize(entropy)
    lf_power_norm = robust_normalize(lf_power)
    modularity_norm = robust_normalize(modularity)

    coords: Dict[str, np.ndarray] = {}
    for name, weights in STRATIFIED_WEIGHTS.items():
        raw = (
            weights["entropy"] * entropy_norm
            + weights["lf_power"] * lf_power_norm
            + weights["modularity"] * modularity_norm
        )
        coords[name] = robust_normalize(raw)

    return coords


def compute_network_stratified(
    bold: np.ndarray,
    roi_names: List[str],
    sfreq: float,
    network: str,
    network_indices: List[int],
    window_sec: float = 8.0,
    step_sec: float = 4.0,
) -> Optional[NetworkStratifiedMNPS]:
    """Compute stratified coordinates for a single network."""

    if not network_indices or len(network_indices) < 2:
        return None

    network_bold = bold[network_indices, :]
    time, entropy, lf_power, modularity = compute_windowed_features(
        network_bold, sfreq, window_sec, step_sec
    )

    if len(time) == 0:
        return None

    coords = project_to_stratified(entropy, lf_power, modularity)
    return NetworkStratifiedMNPS(
        network=network,
        time=time,
        m_a=coords["m_a"],
        m_e=coords["m_e"],
        m_o=coords["m_o"],
        d_n=coords["d_n"],
        d_l=coords["d_l"],
        d_s=coords["d_s"],
        e_e=coords["e_e"],
        e_s=coords["e_s"],
        e_m=coords["e_m"],
        n_regions=len(network_indices),
        metadata={"roi_names": [roi_names[i] for i in network_indices]},
    )


def compute_regional_stratified(
    bold: np.ndarray,
    roi_names: List[str],
    sfreq: float,
    subject_id: str = "unknown",
    window_sec: float = 8.0,
    step_sec: float = 4.0,
    networks: Optional[List[str]] = None,
) -> RegionalStratifiedResult:
    """Compute Regional Stratified MNPS for all networks."""

    if networks is None:
        networks = PRIMARY_NETWORKS

    network_indices = map_rois_to_networks(roi_names)
    network_stratified: Dict[str, NetworkStratifiedMNPS] = {}
    global_time = None

    for net in networks:
        indices = network_indices.get(net, [])
        result = compute_network_stratified(
            bold, roi_names, sfreq, net, indices, window_sec, step_sec
        )
        if result is not None:
            network_stratified[net] = result
            if global_time is None:
                global_time = result.time

    if global_time is None:
        n_times = bold.shape[1]
        w_samp = int(window_sec * sfreq)
        s_samp = int(step_sec * sfreq)
        n_windows = max(1, (n_times - w_samp) // s_samp + 1)
        global_time = np.array([(i * s_samp + w_samp / 2) / sfreq for i in range(n_windows)])

    return RegionalStratifiedResult(
        subject_id=subject_id,
        networks=network_stratified,
        global_time=global_time,
        sfreq=sfreq,
        window_sec=window_sec,
        step_sec=step_sec,
    )


def load_and_compute_regional_stratified(
    h5_path: Path,
    window_sec: float = 8.0,
    step_sec: float = 4.0,
    networks: Optional[List[str]] = None,
) -> Optional[RegionalStratifiedResult]:
    """Load regional BOLD from HDF5 and compute Regional Stratified MNPS."""

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

    return compute_regional_stratified(
        bold, names, sfreq, subject_id, window_sec, step_sec, networks
    )
