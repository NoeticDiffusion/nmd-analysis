"""
Network grouping utilities for Schaefer parcellation.

Maps Schaefer 7-Network parcels to canonical functional networks for Regional MNPS
analysis.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

# Schaefer 7-Network label mapping to canonical network names
SCHAEFER_7NET_MAPPING: Dict[str, str] = {
    "Default": "DMN",
    "Cont": "FPN",
    "SalVentAttn": "SAL",
    "DorsAttn": "DAN",
    "SomMot": "SMN",
    "Vis": "VIS",
    "Limbic": "LIM",
}

# Canonical network order for consistent reporting
CANONICAL_NETWORKS = ["DMN", "FPN", "SAL", "DAN", "SMN", "VIS", "LIM"]

# Primary networks for developmental contrasts
PRIMARY_NETWORKS = ["DMN", "FPN", "SAL", "VIS", "SMN"]


@dataclass
class NetworkAssignment:
    """Assignment of a single ROI to a network."""

    roi_index: int
    roi_name: str
    network: str
    hemisphere: str
    subregion: Optional[str] = None


def parse_schaefer_roi_name(roi_name: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse a Schaefer 7-Network ROI name.

    Expected format: ``7Networks_<HEM>_<Network>_<Subregion>_<Num>``.
    """

    pattern = r"7Networks_(LH|RH)_([A-Za-z]+)_(.+)"
    match = re.match(pattern, roi_name)
    if not match:
        return None

    hemisphere = match.group(1)
    network_key = match.group(2)
    rest = match.group(3)

    subregion_match = re.match(r"(.+?)_?\d*$", rest)
    subregion = subregion_match.group(1) if subregion_match else rest

    return hemisphere, network_key, subregion


def map_rois_to_networks(roi_names: List[str]) -> Dict[str, List[int]]:
    """Map ROI names to canonical network assignments."""

    network_indices: Dict[str, List[int]] = {net: [] for net in CANONICAL_NETWORKS}

    for idx, name in enumerate(roi_names):
        parsed = parse_schaefer_roi_name(name)
        if parsed is None:
            continue

        _, network_key, _ = parsed
        canonical = SCHAEFER_7NET_MAPPING.get(network_key)
        if canonical and canonical in network_indices:
            network_indices[canonical].append(idx)

    return network_indices


def get_network_assignments(roi_names: List[str]) -> List[NetworkAssignment]:
    """Return detailed network assignments for all ROIs."""

    assignments: List[NetworkAssignment] = []

    for idx, name in enumerate(roi_names):
        parsed = parse_schaefer_roi_name(name)
        if parsed is None:
            assignments.append(
                NetworkAssignment(
                    roi_index=idx,
                    roi_name=name,
                    network="UNKNOWN",
                    hemisphere="UNK",
                )
            )
            continue

        hemisphere, network_key, subregion = parsed
        canonical = SCHAEFER_7NET_MAPPING.get(network_key, "UNKNOWN")
        assignments.append(
            NetworkAssignment(
                roi_index=idx,
                roi_name=name,
                network=canonical,
                hemisphere=hemisphere,
                subregion=subregion,
            )
        )

    return assignments


def aggregate_bold_by_network(
    bold: np.ndarray,
    roi_names: List[str],
    method: str = "mean",
) -> Dict[str, np.ndarray]:
    """
    Aggregate regional BOLD signals by network.

    ``method="raw"`` returns the per-network raw regional matrix.
    """

    network_indices = map_rois_to_networks(roi_names)
    network_bold: Dict[str, np.ndarray] = {}

    for network, indices in network_indices.items():
        if not indices:
            continue

        network_data = bold[indices, :]

        if method == "mean":
            network_bold[network] = np.mean(network_data, axis=0)
        elif method == "median":
            network_bold[network] = np.median(network_data, axis=0)
        elif method == "pca_first":
            if network_data.shape[0] > 1:
                centered = network_data - network_data.mean(axis=1, keepdims=True)
                _, _, vt = np.linalg.svd(centered, full_matrices=False)
                network_bold[network] = vt[0, :]
            else:
                network_bold[network] = network_data[0, :]
        elif method == "raw":
            network_bold[network] = network_data
        else:
            raise ValueError(f"Unknown aggregation method: {method}")

    return network_bold


def get_network_summary(roi_names: List[str]) -> Dict[str, Dict[str, int]]:
    """Get summary statistics about network coverage."""

    assignments = get_network_assignments(roi_names)

    summary: Dict[str, Dict[str, int]] = {}
    for net in CANONICAL_NETWORKS:
        net_assignments = [a for a in assignments if a.network == net]
        lh_count = sum(1 for a in net_assignments if a.hemisphere == "LH")
        rh_count = sum(1 for a in net_assignments if a.hemisphere == "RH")
        summary[net] = {
            "total": len(net_assignments),
            "LH": lh_count,
            "RH": rh_count,
        }

    unknown = [a for a in assignments if a.network == "UNKNOWN"]
    summary["UNKNOWN"] = {"total": len(unknown), "LH": 0, "RH": 0}
    return summary


def filter_primary_networks(network_data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """Filter to only primary networks."""

    return {k: v for k, v in network_data.items() if k in PRIMARY_NETWORKS}
