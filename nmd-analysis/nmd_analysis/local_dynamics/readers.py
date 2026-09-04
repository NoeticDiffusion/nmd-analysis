"""Versioned HDF5 readers for local-dynamics measurement contracts."""

from __future__ import annotations

from typing import Any, Iterator, Mapping

import h5py
import numpy as np


def as_scalar(value: Any) -> Any:
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        return bytes(value).decode("utf-8")
    return value


def scalar(handle: h5py.File | h5py.Group, path: str, default: Any = None) -> Any:
    if path not in handle:
        return default
    value = handle[path][()]
    return as_scalar(value)


def branch_name(dimension: int) -> str:
    if dimension == 3:
        return "primary"
    if dimension == 9:
        return "stratified_9d"
    raise ValueError(f"Unsupported local-dynamics dimension: {dimension}")


def jacobian_metrics_path(dimension: int) -> str:
    return "/jacobian/derived_metrics/v1" if dimension == 3 else "/jacobian_9D/derived_metrics/v1"


def jacobian_centers_path(dimension: int) -> str:
    return "/jacobian/centers" if dimension == 3 else "/jacobian_9D/centers"


def local_dynamics_paths(dimension: int) -> Mapping[str, str]:
    branch = branch_name(dimension)
    return {
        "jacobian_metrics": jacobian_metrics_path(dimension),
        "finite_time_response": f"/finite_time_response/v1/{branch}",
        "transition_residuals": f"/transition_residuals/v1/{branch}",
        "transition_q_proxy": f"/transition_residual_covariance_proxy/v1/{branch}",
        "stochastic_reachability": f"/stochastic_reachability/v1/{branch}",
    }


def availability(handle: h5py.File, dimension: int) -> dict[str, bool]:
    return {name: path in handle for name, path in local_dynamics_paths(dimension).items()}


def read_group_scalars(group: h5py.Group, *, prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in group.items():
        if isinstance(value, h5py.Dataset) and value.shape == ():
            result[f"{prefix}{name}"] = as_scalar(value[()])
    return result


def group_provenance(group: h5py.Group) -> dict[str, Any]:
    provenance = group.get("provenance")
    return read_group_scalars(provenance, prefix="") if isinstance(provenance, h5py.Group) else {}


def iter_horizon_groups(group: h5py.Group) -> Iterator[tuple[str, h5py.Group]]:
    horizons = group.get("horizons")
    if not isinstance(horizons, h5py.Group):
        return
    for name in sorted(horizons.keys(), key=lambda item: int(item[1:]) if item[1:].isdigit() else item):
        horizon = horizons[name]
        if isinstance(horizon, h5py.Group):
            yield name, horizon


def metric_valid_fraction(summary: Mapping[str, Any]) -> float:
    total = float(summary.get("n_windows_total") or 0)
    valid = float(summary.get("n_windows_metrics_valid") or 0)
    return valid / total if total > 0 else float("nan")
