"""
Embodied anchor surface reader for MNDM 2.3+ H5 outputs.

This module reads the embodied/interoceptive anchor surface from H5 files:
  - /anchor_state        : body-state indices (sympathetic, vagal, vascular, pupil, composite)
  - /anchor_state_dot    : time derivatives of anchor state
  - /anchor_quality      : per-window quality scores for each anchor dimension
  - /anchor_coupling     : Jacobian coupling between anchor and MNPS (optional)

IMPORTANT: keep ``anchor_state`` distinct from ``feature_anchors``.
  - ``feature_anchors``  : frozen cohort/external scaling artifacts for coordinate contracts
  - ``anchor_state``     : embodied/interoceptive time-aligned surface (this module)

These are different objects with different purposes. Do not conflate them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import h5py
import numpy as np


# ---------------------------------------------------------------------------
# Default column names (mirrors MNDM 2.3 contract)
# ---------------------------------------------------------------------------

ANCHOR_STATE_DEFAULT_NAMES = [
    "sympathetic_index",
    "vagal_index",
    "vascular_index",
    "pupil_arousal_index",
    "anchor_index",
]

ANCHOR_QUALITY_DEFAULT_NAMES = [
    "ecg_quality",
    "ppg_quality",
    "pupil_quality",
    "anchor_support_fraction",
]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _to_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return _to_str(value.item())
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        try:
            return bytes(value).decode("utf-8")
        except Exception:
            return str(value)
    return str(value)


def _read_str_list(dataset: h5py.Dataset) -> List[str]:
    raw = dataset[()].reshape(-1).tolist()
    out: List[str] = []
    for item in raw:
        text = _to_str(item)
        if text is not None:
            out.append(text.strip())
    return out


def _dataset_exists(handle: h5py.File, path: str) -> bool:
    return path in handle and isinstance(handle[path], h5py.Dataset)


def _group_exists(handle: h5py.File, path: str) -> bool:
    return path in handle and isinstance(handle[path], h5py.Group)


def _read_names(handle: h5py.File, names_path: str, default: List[str]) -> List[str]:
    if _dataset_exists(handle, names_path):
        names = _read_str_list(handle[names_path])
        if names:
            return names
    return list(default)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AnchorState:
    """Time-aligned embodied anchor state loaded from a single H5 file."""

    values: np.ndarray
    """Shape (T, A) where T = number of timepoints, A = number of anchor dimensions."""

    names: List[str]
    """Anchor dimension names, length A."""

    values_path: str
    """H5 path of the values dataset."""

    subject_id: Optional[str] = None
    task: Optional[str] = None
    n_timepoints: int = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "n_timepoints", int(self.values.shape[0]))

    def as_dict(self) -> Dict[str, np.ndarray]:
        return {name: self.values[:, i] for i, name in enumerate(self.names)}

    def quality_mask(self, quality: "AnchorQuality", min_support: float = 0.3) -> np.ndarray:
        """Return boolean mask for timepoints with anchor_support_fraction >= min_support.

        Uses the ``anchor_support_fraction`` quality column when available,
        otherwise returns all-True mask.
        """
        if quality is None:
            return np.ones(self.n_timepoints, dtype=bool)
        if "anchor_support_fraction" in quality.names:
            idx = quality.names.index("anchor_support_fraction")
            support = quality.values[:, idx]
            finite = np.isfinite(support)
            mask = np.ones(self.n_timepoints, dtype=bool)
            mask[finite] = support[finite] >= min_support
            return mask
        return np.ones(self.n_timepoints, dtype=bool)


@dataclass(frozen=True)
class AnchorStateDot:
    """Time derivatives of the embodied anchor state."""

    values: np.ndarray
    names: List[str]
    values_path: str
    subject_id: Optional[str] = None
    task: Optional[str] = None


@dataclass(frozen=True)
class AnchorQuality:
    """Per-window quality scores for each anchor dimension."""

    values: np.ndarray
    """Shape (T, Q) where Q = number of quality dimensions."""

    names: List[str]
    values_path: str
    subject_id: Optional[str] = None
    task: Optional[str] = None

    def ok_mask(
        self,
        min_support: float = 0.3,
        max_artifact: float = 0.25,
        min_coverage: float = 0.5,
    ) -> np.ndarray:
        """Return boolean quality-pass mask across timepoints.

        Parameters
        ----------
        min_support:
            Minimum ``anchor_support_fraction`` required (0–1).
        max_artifact:
            Maximum ``ecg_quality`` artifact fraction permitted (lower is better).
        min_coverage:
            Minimum ``ecg_quality`` coverage fraction required.
        """
        T = int(self.values.shape[0])
        mask = np.ones(T, dtype=bool)
        col = {name: i for i, name in enumerate(self.names)}

        if "anchor_support_fraction" in col:
            v = self.values[:, col["anchor_support_fraction"]]
            finite = np.isfinite(v)
            mask[finite] &= v[finite] >= min_support

        return mask


@dataclass(frozen=True)
class AnchorCouplingDiagnostics:
    """Diagnostics from the anchor coupling Jacobian estimation."""

    windows_raw: int
    windows_retained: int
    invalid_windows: int
    invalid_window_fraction: float
    status: Optional[str]
    condition_number_threshold: float
    forward_drive_median: Optional[float]
    reverse_drive_median: Optional[float]
    directional_asymmetry_median: Optional[float]
    rotational_exchange_median: Optional[float]

    @property
    def retention_fraction(self) -> float:
        if self.windows_raw <= 0:
            return 0.0
        return self.windows_retained / self.windows_raw

    def is_usable(self, min_retained: int = 10, min_retention: float = 0.05) -> bool:
        return (
            self.status in ("ok", "adjusted")
            and self.windows_retained >= min_retained
            and self.retention_fraction >= min_retention
        )


@dataclass(frozen=True)
class AnchorCoupling:
    """Jacobian coupling between anchor state and MNPS coordinates.

    This surface is optional: only present when enough windows passed the
    condition-number validity check during MNDM processing.

    J_ax : shape (W, A, X) — how anchor axes drive MNPS axes
    J_xa : shape (W, X, A) — how MNPS axes drive anchor axes
    J_z  : shape (W, Z, Z) — joint system Jacobian (Z = X + A)
    centers : shape (W,) — window center indices into the full time series
    """

    J_ax: np.ndarray
    J_xa: np.ndarray
    J_z: np.ndarray
    J_ax_dot: Optional[np.ndarray]
    J_xa_dot: Optional[np.ndarray]
    J_z_dot: Optional[np.ndarray]
    centers: np.ndarray
    metrics: Optional[np.ndarray]
    metric_names: List[str]
    diagnostics: AnchorCouplingDiagnostics
    subject_id: Optional[str] = None
    task: Optional[str] = None

    @property
    def n_windows(self) -> int:
        return int(self.J_ax.shape[0])

    @property
    def anchor_dim(self) -> int:
        return int(self.J_ax.shape[1])

    @property
    def mnps_dim(self) -> int:
        return int(self.J_ax.shape[2])

    def forward_drive(self) -> np.ndarray:
        """Per-window Frobenius norm of J_ax (anchor -> MNPS drive)."""
        return np.linalg.norm(self.J_ax.reshape(self.n_windows, -1), axis=1)

    def reverse_drive(self) -> np.ndarray:
        """Per-window Frobenius norm of J_xa (MNPS -> anchor drive)."""
        return np.linalg.norm(self.J_xa.reshape(self.n_windows, -1), axis=1)


@dataclass
class AnchorSurface:
    """Complete embodied anchor surface for one subject/task H5 file.

    Attributes
    ----------
    state : AnchorState or None
        Time-aligned anchor state values.
    state_dot : AnchorStateDot or None
        Time derivatives of anchor state.
    quality : AnchorQuality or None
        Per-window quality scores.
    coupling : AnchorCoupling or None
        Optional Jacobian coupling (only present when windows_retained > 0).
    subject_id, task : str or None
        Provenance identifiers.
    """

    state: Optional[AnchorState] = None
    state_dot: Optional[AnchorStateDot] = None
    quality: Optional[AnchorQuality] = None
    coupling: Optional[AnchorCoupling] = None
    subject_id: Optional[str] = None
    task: Optional[str] = None

    @property
    def has_state(self) -> bool:
        return self.state is not None

    @property
    def has_quality(self) -> bool:
        return self.quality is not None

    @property
    def has_coupling(self) -> bool:
        return self.coupling is not None

    def quality_mask(self, **kwargs: Any) -> Optional[np.ndarray]:
        if self.quality is None:
            return None
        return self.quality.ok_mask(**kwargs)

    def summary(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "subject_id": self.subject_id,
            "task": self.task,
            "has_state": self.has_state,
            "has_quality": self.has_quality,
            "has_coupling": self.has_coupling,
        }
        if self.state is not None:
            out["n_timepoints"] = self.state.n_timepoints
            out["anchor_names"] = self.state.names
        if self.quality is not None:
            out["quality_names"] = self.quality.names
        if self.coupling is not None:
            d = self.coupling.diagnostics
            out["coupling_windows_retained"] = d.windows_retained
            out["coupling_windows_raw"] = d.windows_raw
            out["coupling_retention_fraction"] = d.retention_fraction
            out["coupling_status"] = d.status
        return out


# ---------------------------------------------------------------------------
# H5 readers
# ---------------------------------------------------------------------------

def _read_anchor_state(
    handle: h5py.File,
    *,
    subject_id: Optional[str] = None,
    task: Optional[str] = None,
) -> Optional[AnchorState]:
    group_path = "/anchor_state"
    values_path = "/anchor_state/values"
    names_path = "/anchor_state/names"

    if not _group_exists(handle, group_path) or not _dataset_exists(handle, values_path):
        return None

    values = np.asarray(handle[values_path][:], dtype=float)
    names = _read_names(handle, names_path, ANCHOR_STATE_DEFAULT_NAMES)

    return AnchorState(
        values=values,
        names=names,
        values_path=values_path,
        subject_id=subject_id,
        task=task,
    )


def _read_anchor_state_dot(
    handle: h5py.File,
    *,
    subject_id: Optional[str] = None,
    task: Optional[str] = None,
) -> Optional[AnchorStateDot]:
    group_path = "/anchor_state_dot"
    values_path = "/anchor_state_dot/values"
    names_path = "/anchor_state_dot/names"

    if not _group_exists(handle, group_path) or not _dataset_exists(handle, values_path):
        return None

    values = np.asarray(handle[values_path][:], dtype=float)
    names = _read_names(handle, names_path, ANCHOR_STATE_DEFAULT_NAMES)

    return AnchorStateDot(
        values=values,
        names=names,
        values_path=values_path,
        subject_id=subject_id,
        task=task,
    )


def _read_anchor_quality(
    handle: h5py.File,
    *,
    subject_id: Optional[str] = None,
    task: Optional[str] = None,
) -> Optional[AnchorQuality]:
    group_path = "/anchor_quality"
    values_path = "/anchor_quality/values"
    names_path = "/anchor_quality/names"

    if not _group_exists(handle, group_path) or not _dataset_exists(handle, values_path):
        return None

    values = np.asarray(handle[values_path][:], dtype=float)
    names = _read_names(handle, names_path, ANCHOR_QUALITY_DEFAULT_NAMES)

    return AnchorQuality(
        values=values,
        names=names,
        values_path=values_path,
        subject_id=subject_id,
        task=task,
    )


def _read_coupling_diagnostics(handle: h5py.File) -> Optional[AnchorCouplingDiagnostics]:
    base = "/anchor_coupling/diagnostics"
    policy = f"{base}/policy"

    if not _group_exists(handle, base):
        return None

    def _scalar(path: str, dtype: type = float) -> Any:
        if _dataset_exists(handle, path):
            val = handle[path][()]
            if isinstance(val, np.ndarray) and val.ndim == 0:
                val = val.item()
            try:
                return dtype(val)
            except Exception:
                return None
        return None

    def _str_scalar(path: str) -> Optional[str]:
        if _dataset_exists(handle, path):
            return _to_str(handle[path][()])
        return None

    windows_raw = _scalar(f"{base}/windows_raw", int) or _scalar(f"{policy}/windows_raw", int) or 0
    windows_retained = _scalar(f"{policy}/windows_retained", int) or 0
    invalid_windows = _scalar(f"{policy}/invalid_windows", int) or 0
    invalid_window_fraction = _scalar(f"{policy}/invalid_window_fraction", float) or 0.0
    status = _str_scalar(f"{policy}/status")
    cond_thresh = _scalar(f"{policy}/condition_number_threshold", float) or 1e6
    fwd = _scalar(f"{base}/forward_drive_median", float)
    rev = _scalar(f"{base}/reverse_drive_median", float)
    da = _scalar(f"{base}/directional_asymmetry_median", float)
    re = _scalar(f"{base}/rotational_exchange_median", float)

    return AnchorCouplingDiagnostics(
        windows_raw=int(windows_raw),
        windows_retained=int(windows_retained),
        invalid_windows=int(invalid_windows),
        invalid_window_fraction=float(invalid_window_fraction),
        status=status,
        condition_number_threshold=float(cond_thresh),
        forward_drive_median=fwd,
        reverse_drive_median=rev,
        directional_asymmetry_median=da,
        rotational_exchange_median=re,
    )


def _read_anchor_coupling(
    handle: h5py.File,
    *,
    subject_id: Optional[str] = None,
    task: Optional[str] = None,
) -> Optional[AnchorCoupling]:
    base = "/anchor_coupling"

    if not _group_exists(handle, base):
        return None

    def _arr(path: str) -> Optional[np.ndarray]:
        if _dataset_exists(handle, path):
            return np.asarray(handle[path][:], dtype=float)
        return None

    J_ax = _arr(f"{base}/J_ax")
    J_xa = _arr(f"{base}/J_xa")
    J_z = _arr(f"{base}/J_z")

    if J_ax is None or J_xa is None or J_z is None:
        return None

    centers_path = f"{base}/centers"
    centers = (
        np.asarray(handle[centers_path][:], dtype=int).reshape(-1)
        if _dataset_exists(handle, centers_path)
        else np.arange(J_ax.shape[0], dtype=int)
    )

    metric_names_path = f"{base}/metric_names"
    metric_names = (
        _read_str_list(handle[metric_names_path])
        if _dataset_exists(handle, metric_names_path)
        else []
    )

    metrics_path = f"{base}/metrics"
    metrics = _arr(metrics_path)

    diagnostics = _read_coupling_diagnostics(handle)
    if diagnostics is None:
        diagnostics = AnchorCouplingDiagnostics(
            windows_raw=int(J_ax.shape[0]),
            windows_retained=int(J_ax.shape[0]),
            invalid_windows=0,
            invalid_window_fraction=0.0,
            status="unknown",
            condition_number_threshold=1e6,
            forward_drive_median=None,
            reverse_drive_median=None,
            directional_asymmetry_median=None,
            rotational_exchange_median=None,
        )

    return AnchorCoupling(
        J_ax=J_ax,
        J_xa=J_xa,
        J_z=J_z,
        J_ax_dot=_arr(f"{base}/J_ax_dot"),
        J_xa_dot=_arr(f"{base}/J_xa_dot"),
        J_z_dot=_arr(f"{base}/J_z_dot"),
        centers=centers,
        metrics=metrics,
        metric_names=metric_names,
        diagnostics=diagnostics,
        subject_id=subject_id,
        task=task,
    )


def read_anchor_surface(
    h5_path: str | Path,
    *,
    subject_id: Optional[str] = None,
    task: Optional[str] = None,
    load_coupling: bool = True,
) -> AnchorSurface:
    """Read the embodied anchor surface from one MNDM H5 file.

    Parameters
    ----------
    h5_path:
        Path to the subject/task H5 file.
    subject_id, task:
        Provenance labels attached to each returned dataclass.
    load_coupling:
        Whether to load the optional anchor coupling Jacobian. Set to False
        when only the per-timepoint anchor state is needed.

    Returns
    -------
    AnchorSurface
        Container with state, state_dot, quality, and optional coupling.
        Missing surfaces are None rather than raising exceptions.
    """
    h5_path = Path(h5_path)

    with h5py.File(h5_path, "r") as handle:
        state = _read_anchor_state(handle, subject_id=subject_id, task=task)
        state_dot = _read_anchor_state_dot(handle, subject_id=subject_id, task=task)
        quality = _read_anchor_quality(handle, subject_id=subject_id, task=task)
        coupling = (
            _read_anchor_coupling(handle, subject_id=subject_id, task=task)
            if load_coupling
            else None
        )

    return AnchorSurface(
        state=state,
        state_dot=state_dot,
        quality=quality,
        coupling=coupling,
        subject_id=subject_id,
        task=task,
    )


# ---------------------------------------------------------------------------
# Run-manifest capability probe
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AnchorCapabilityProbe:
    """Anchor surface availability as reported by a run manifest."""

    has_anchor_state: bool
    has_anchor_quality: bool
    has_anchor_coupling: bool
    n_with_anchor_state: int
    n_with_anchor_quality: int
    n_with_anchor_coupling: int
    anchor_state_names: List[str]
    anchor_quality_names: List[str]

    def is_usable(self, min_state_fraction: float = 0.5) -> bool:
        total = self.n_with_anchor_state + self.n_with_anchor_quality
        return self.has_anchor_state and total > 0


def probe_anchor_capabilities_from_manifest(manifest: Dict[str, Any]) -> AnchorCapabilityProbe:
    """Extract anchor capability summary from a loaded ``run_manifest.json`` dict.

    Parameters
    ----------
    manifest:
        Dict loaded from ``run_manifest.json``.

    Returns
    -------
    AnchorCapabilityProbe
    """
    caps = manifest.get("capabilities", {})
    counts = caps.get("counts", {})

    # state names and quality names come from the per-subject summary.json;
    # use module defaults as fallback
    state_names = list(ANCHOR_STATE_DEFAULT_NAMES)
    quality_names = list(ANCHOR_QUALITY_DEFAULT_NAMES)

    return AnchorCapabilityProbe(
        has_anchor_state=bool(caps.get("anchor_state", False)),
        has_anchor_quality=bool(caps.get("anchor_quality", False)),
        has_anchor_coupling=bool(caps.get("anchor_coupling", False)),
        n_with_anchor_state=int(counts.get("h5_with_anchor_state", 0)),
        n_with_anchor_quality=int(counts.get("h5_with_anchor_quality", 0)),
        n_with_anchor_coupling=int(counts.get("h5_with_anchor_coupling", 0)),
        anchor_state_names=state_names,
        anchor_quality_names=quality_names,
    )


__all__ = [
    "ANCHOR_STATE_DEFAULT_NAMES",
    "ANCHOR_QUALITY_DEFAULT_NAMES",
    "AnchorState",
    "AnchorStateDot",
    "AnchorQuality",
    "AnchorCouplingDiagnostics",
    "AnchorCoupling",
    "AnchorSurface",
    "AnchorCapabilityProbe",
    "read_anchor_surface",
    "probe_anchor_capabilities_from_manifest",
]
