"""
Regional manifold geometry metrics for Regional MNPS.

Computes per-network geometry metrics such as volume, spread, curvature, and
attractor density.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist, squareform

from .regional_mnps import NetworkMNPS, RegionalMNPSResult


@dataclass
class NetworkGeometry:
    """Geometry metrics for a single network's MNPS trajectory."""

    network: str
    n_windows: int
    volume_bbox: float
    volume_convex: float
    geodesic_spread: float
    geodesic_max: float
    curvature_mean: float
    curvature_std: float
    attractor_density: float
    recurrence_rate: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "volume_bbox": self.volume_bbox,
            "volume_convex": self.volume_convex,
            "geodesic_spread": self.geodesic_spread,
            "geodesic_max": self.geodesic_max,
            "curvature_mean": self.curvature_mean,
            "curvature_std": self.curvature_std,
            "attractor_density": self.attractor_density,
            "recurrence_rate": self.recurrence_rate,
        }


@dataclass
class RegionalGeometryResult:
    """Complete geometry metrics for all networks."""

    subject_id: str
    networks: Dict[str, NetworkGeometry]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "networks": {net: ng.to_dict() for net, ng in self.networks.items()},
        }


def compute_bounding_box_volume(x: np.ndarray) -> float:
    """Compute axis-aligned bounding-box volume."""

    if x.shape[0] < 2:
        return 0.0
    ranges = np.ptp(x, axis=0)
    return float(np.prod(ranges))


def compute_convex_hull_volume(x: np.ndarray) -> float:
    """Compute convex-hull volume for 3D data."""

    if x.shape[0] < 4 or x.shape[1] != 3:
        return 0.0
    try:
        hull = ConvexHull(x)
        return float(hull.volume)
    except Exception:
        return 0.0


def compute_geodesic_metrics(x: np.ndarray) -> Tuple[float, float]:
    """Return mean pairwise distance and maximum distance."""

    if x.shape[0] < 2:
        return 0.0, 0.0
    distances = pdist(x)
    return float(np.mean(distances)), float(np.max(distances))


def compute_trajectory_curvature(x: np.ndarray, time: np.ndarray) -> Tuple[float, float]:
    """Compute a discrete curvature proxy."""

    n = x.shape[0]
    if n < 3:
        return 0.0, 0.0

    dt = np.median(np.diff(time)) if len(time) > 1 else 1.0
    dx = np.diff(x, axis=0) / dt
    ddx = np.diff(dx, axis=0) / dt
    dx_mid = dx[:-1]
    dx_norm = np.linalg.norm(dx_mid, axis=1) + 1e-10
    ddx_norm = np.linalg.norm(ddx, axis=1)
    kappa = ddx_norm / (dx_norm**2)
    kappa = kappa[np.isfinite(kappa)]
    if len(kappa) > 10:
        kappa = kappa[kappa < np.percentile(kappa, 99)]

    if len(kappa) == 0:
        return 0.0, 0.0
    return float(np.mean(kappa)), float(np.std(kappa))


def compute_attractor_metrics(
    x: np.ndarray,
    recurrence_threshold: float = 0.1,
) -> Tuple[float, float]:
    """Compute mean local density and recurrence rate."""

    if x.shape[0] < 2:
        return 0.0, 0.0

    distances = squareform(pdist(x))
    max_dist = np.max(distances) + 1e-10
    threshold = recurrence_threshold * max_dist

    n = x.shape[0]
    n_pairs = n * (n - 1) / 2
    n_recurrent = np.sum(distances < threshold) - n
    n_recurrent = n_recurrent / 2
    recurrence_rate = n_recurrent / n_pairs if n_pairs > 0 else 0.0

    neighbors = np.sum(distances < threshold, axis=1) - 1
    mean_density = float(np.mean(neighbors))
    return mean_density, float(recurrence_rate)


def compute_network_geometry(
    nm: NetworkMNPS,
    recurrence_threshold: float = 0.1,
) -> NetworkGeometry:
    """Compute geometry metrics for a single network trajectory."""

    x = nm.x
    volume_bbox = compute_bounding_box_volume(x)
    volume_convex = compute_convex_hull_volume(x)
    geodesic_spread, geodesic_max = compute_geodesic_metrics(x)
    curvature_mean, curvature_std = compute_trajectory_curvature(x, nm.time)
    attractor_density, recurrence_rate = compute_attractor_metrics(x, recurrence_threshold)

    return NetworkGeometry(
        network=nm.network,
        n_windows=len(nm.time),
        volume_bbox=volume_bbox,
        volume_convex=volume_convex,
        geodesic_spread=geodesic_spread,
        geodesic_max=geodesic_max,
        curvature_mean=curvature_mean,
        curvature_std=curvature_std,
        attractor_density=attractor_density,
        recurrence_rate=recurrence_rate,
    )


def compute_regional_geometry(
    regional_mnps: RegionalMNPSResult,
    recurrence_threshold: float = 0.1,
) -> RegionalGeometryResult:
    """Compute geometry metrics for all networks in a regional MNPS result."""

    network_geometry: Dict[str, NetworkGeometry] = {}
    for net, nm in regional_mnps.networks.items():
        network_geometry[net] = compute_network_geometry(nm, recurrence_threshold)

    return RegionalGeometryResult(
        subject_id=regional_mnps.subject_id,
        networks=network_geometry,
    )
