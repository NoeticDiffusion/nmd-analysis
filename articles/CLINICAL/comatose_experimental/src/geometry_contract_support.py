from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import h5py


REPO_ROOT = Path(__file__).resolve().parents[4]
NDT_ANALYSIS_DIR = REPO_ROOT / "ndt-analysis"
if str(NDT_ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_DIR))

from ndt_analysis.h5_contract import read_geometry_contract_state  # noqa: E402


@dataclass(frozen=True)
class Geometry9DValidity:
    """Whether an H5 run can contribute mathematically valid 9D geometry."""

    usable: bool
    status: str | None
    invalidity_policy: str | None
    degenerate_axes: tuple[str, ...]
    jacobian_windows_retained: int | None
    jacobian_invalid_windows: int | None
    gate_reason: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "geometry_contract_status": self.status,
            "geometry_invalidity_policy": self.invalidity_policy,
            "geometry_9d_usable": self.usable,
            "geometry_9d_degenerate_axes": "|".join(self.degenerate_axes),
            "geometry_9d_jacobian_windows_retained": self.jacobian_windows_retained,
            "geometry_9d_jacobian_invalid_windows": self.jacobian_invalid_windows,
            "geometry_9d_gate_reason": self.gate_reason,
        }


def read_geometry_9d_validity(handle: h5py.File) -> Geometry9DValidity:
    """Apply the same invalidity rules used by the NDT reachability adapter."""

    state = read_geometry_contract_state(handle)
    reasons: list[str] = []
    if state.has_coords_9d_degenerate_axes():
        reasons.append(f"coords_9d_degenerate_axes={','.join(state.coords_9d_degenerate_axes)}")
    if state.has_zero_retained_jacobian_9d():
        reasons.append("jacobian_9d_windows_retained<=0")
    return Geometry9DValidity(
        usable=not reasons,
        status=state.status,
        invalidity_policy=state.invalidity_policy,
        degenerate_axes=state.coords_9d_degenerate_axes,
        jacobian_windows_retained=state.jacobian_9d_windows_retained,
        jacobian_invalid_windows=state.jacobian_9d_invalid_windows,
        gate_reason="; ".join(reasons) if reasons else None,
    )
