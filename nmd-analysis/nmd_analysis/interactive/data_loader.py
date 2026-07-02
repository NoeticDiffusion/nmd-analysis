"""H5 discovery and loading for the interactive MNPS/MNJ explorer.

This module is read-only with respect to the NDT H5 contract: it reuses
`ndt_analysis.h5_contract` (already validated/used by the analysis pipeline)
rather than re-implementing coordinate/jacobian resolution logic.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import h5py
import numpy as np

# Ensure this module's own directory is importable regardless of how the
# caller was launched (plain `python app.py` already guarantees this, but
# this makes `data_loader.py` safe to import/run standalone too).
_THIS_DIR = str(Path(__file__).resolve().parent)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import _vendor_path  # noqa: F401,E402  (side effect: puts ndt-analysis/ on sys.path)

from ndt_analysis.h5_contract import (  # noqa: E402
    KNOWN_COORDINATE_CONTRACTS,
    read_geometry_contract_state,
    read_run_contract,
    resolve_coords_3d,
    resolve_coords_9d,
    resolve_jacobian_3d,
    resolve_jacobian_9d,
)

# Try the most specific / most commonly exported contract first.
_CONTRACT_FALLBACK_ORDER = ("cohort_anchored", "subject_anchored", "legacy")


def discover_h5_files(root: Path) -> List[Path]:
    """Recursively find all `*.h5` files under `root`.

    Pure filesystem walk, no H5 files are opened here - this keeps discovery
    fast even when `root` contains tens of thousands of files (e.g. pointing
    at a broad `data/raw/` folder rather than a single dataset export).
    """
    root = Path(root)
    if not root.exists() or not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*.h5") if p.is_file())


def group_by_dataset(root: Path, paths: List[Path]) -> Dict[str, List[Path]]:
    """Group H5 file paths by their top-level subfolder under `root`.

    This is a cheap, path-only grouping (no H5 attrs are read), used to
    populate the "dataset" dropdown before any file is opened.
    """
    root = Path(root)
    groups: Dict[str, List[Path]] = {}
    for path in paths:
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        top = rel.parts[0] if len(rel.parts) > 1 else root.name
        groups.setdefault(top, []).append(path)
    for key in groups:
        groups[key].sort()
    return groups


@dataclass(frozen=True)
class JacobianData:
    j_hat: np.ndarray  # (W, dims, dims)
    centers: Optional[np.ndarray]  # (W,) time-index each J_hat window is centered on
    resolved_coordinate_contract: str

    # Per-window scalar invariants derived from `j_hat` (see MNJ_DEFINITION /
    # CANONICAL DECOMPOSITION / DERIVED INVARIANTS in agent/compact_summary.md).
    # Precomputed once at load time so per-frame MNJ callbacks only need to
    # look up a scalar/row, not re-diagonalize matrices on every tick.
    fro_norm: np.ndarray = field(default_factory=lambda: np.zeros(0))  # ||J||_F, shape (W,)
    stretch_norm: np.ndarray = field(default_factory=lambda: np.zeros(0))  # ||S||_F, S=(J+J^T)/2
    rotation_norm: np.ndarray = field(default_factory=lambda: np.zeros(0))  # ||Omega||_F, Omega=(J-J^T)/2
    divergence: np.ndarray = field(default_factory=lambda: np.zeros(0))  # tr(J)
    eig_real_max: np.ndarray = field(default_factory=lambda: np.zeros(0))
    eig_real_min: np.ndarray = field(default_factory=lambda: np.zeros(0))
    eig_imag_abs_max: np.ndarray = field(default_factory=lambda: np.zeros(0))


def _compute_jacobian_invariants(j_hat: np.ndarray) -> Dict[str, np.ndarray]:
    """Per-window scalar invariants of a stack of Jacobian matrices.

    `j_hat` has shape (W, d, d). Returns arrays of shape (W,).
    """
    sym = 0.5 * (j_hat + np.swapaxes(j_hat, -1, -2))
    antisym = 0.5 * (j_hat - np.swapaxes(j_hat, -1, -2))
    fro_norm = np.linalg.norm(j_hat, ord="fro", axis=(-2, -1))
    stretch_norm = np.linalg.norm(sym, ord="fro", axis=(-2, -1))
    rotation_norm = np.linalg.norm(antisym, ord="fro", axis=(-2, -1))
    divergence = np.trace(j_hat, axis1=-2, axis2=-1)
    eigvals = np.linalg.eigvals(j_hat)  # (W, d), possibly complex
    eig_real_max = np.max(eigvals.real, axis=-1)
    eig_real_min = np.min(eigvals.real, axis=-1)
    eig_imag_abs_max = np.max(np.abs(eigvals.imag), axis=-1)
    return {
        "fro_norm": fro_norm,
        "stretch_norm": stretch_norm,
        "rotation_norm": rotation_norm,
        "divergence": np.real(divergence),
        "eig_real_max": eig_real_max,
        "eig_real_min": eig_real_min,
        "eig_imag_abs_max": eig_imag_abs_max,
    }


@dataclass(frozen=True)
class SubjectData:
    path: Path
    dataset_id: str
    subject_id: str
    condition: Optional[str]
    task: Optional[str]
    group: Optional[str]

    coords_3d: np.ndarray  # (T, 3) = [m, d, e]
    coords_3d_names: List[str]
    coords_3d_contract: str

    time: np.ndarray  # (T,)

    coords_9d: Optional[np.ndarray] = None  # (T, 9)
    coords_9d_names: Optional[List[str]] = None
    coords_9d_contract: Optional[str] = None

    jacobian_3d: Optional[JacobianData] = None
    jacobian_9d: Optional[JacobianData] = None
    jacobian_9d_status: Optional[str] = None
    jacobian_9d_windows_retained: Optional[int] = None
    jacobian_9d_invalid_windows: Optional[int] = None

    stage_codes: Optional[np.ndarray] = None  # (T,) int, -1 = unlabeled
    stage_labels: Dict[int, str] = field(default_factory=dict)

    @property
    def n_points(self) -> int:
        return int(self.coords_3d.shape[0])

    def to_store_dict(self) -> Dict[str, Any]:
        """JSON-safe representation for a Dash `dcc.Store`."""
        return {
            "path": str(self.path),
            "dataset_id": self.dataset_id,
            "subject_id": self.subject_id,
            "condition": self.condition,
            "task": self.task,
            "group": self.group,
            "coords_3d": self.coords_3d.tolist(),
            "coords_3d_names": self.coords_3d_names,
            "coords_3d_contract": self.coords_3d_contract,
            "time": self.time.tolist(),
            "coords_9d": self.coords_9d.tolist() if self.coords_9d is not None else None,
            "coords_9d_names": self.coords_9d_names,
            "coords_9d_contract": self.coords_9d_contract,
            "jacobian_3d": (
                {
                    "j_hat": self.jacobian_3d.j_hat.tolist(),
                    "centers": (
                        self.jacobian_3d.centers.tolist() if self.jacobian_3d.centers is not None else None
                    ),
                    "resolved_coordinate_contract": self.jacobian_3d.resolved_coordinate_contract,
                    "fro_norm": self.jacobian_3d.fro_norm.tolist(),
                    "stretch_norm": self.jacobian_3d.stretch_norm.tolist(),
                    "rotation_norm": self.jacobian_3d.rotation_norm.tolist(),
                    "divergence": self.jacobian_3d.divergence.tolist(),
                    "eig_real_max": self.jacobian_3d.eig_real_max.tolist(),
                    "eig_real_min": self.jacobian_3d.eig_real_min.tolist(),
                    "eig_imag_abs_max": self.jacobian_3d.eig_imag_abs_max.tolist(),
                }
                if self.jacobian_3d is not None
                else None
            ),
            "jacobian_9d_status": self.jacobian_9d_status,
            "jacobian_9d_windows_retained": self.jacobian_9d_windows_retained,
            "jacobian_9d_invalid_windows": self.jacobian_9d_invalid_windows,
            "stage_codes": self.stage_codes.tolist() if self.stage_codes is not None else None,
            "stage_labels": {str(k): v for k, v in self.stage_labels.items()},
            "n_points": self.n_points,
        }


def _to_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        try:
            return bytes(value).decode("utf-8")
        except Exception:
            return str(value)
    text = str(value)
    return text if text.strip() else None


def _first_resolved(resolver, handle: h5py.File):
    for contract in _CONTRACT_FALLBACK_ORDER:
        try:
            resolved = resolver(handle, contract)
        except Exception:
            resolved = None
        if resolved is not None:
            return resolved
    return None


def _load_stage_per_window(handle: h5py.File, n_points: int) -> tuple[Optional[np.ndarray], Dict[int, str]]:
    """Best-effort per-timepoint stage code + label lookup.

    Uses `event_windows` (window_id, window_contains_event_onset,
    event_mapped_stage_code) plus `codebooks/stage` (codes/labels) when
    present. Returns (None, {}) if the file does not expose this layout -
    callers should fall back to coloring by time only.
    """
    if "event_windows" not in handle or "codebooks/stage" not in handle:
        return None, {}
    try:
        window_id = np.asarray(handle["event_windows/window_id"][:], dtype=int)
        contains_onset = np.asarray(handle["event_windows/window_contains_event_onset"][:], dtype=int)
        mapped_code = np.asarray(handle["event_windows/event_mapped_stage_code"][:], dtype=float)
        codes = np.asarray(handle["codebooks/stage/codes"][:], dtype=int)
        labels_raw = handle["codebooks/stage/labels"][:]
        labels = [_to_str(item) or f"code_{c}" for item, c in zip(labels_raw, codes)]
        code_to_label = dict(zip(codes.tolist(), labels))
    except Exception:
        return None, {}

    stage_codes = np.full(n_points, -1, dtype=int)
    onset_mask = contains_onset.astype(bool)
    for w_id, code in zip(window_id[onset_mask], mapped_code[onset_mask]):
        if 0 <= w_id < n_points and np.isfinite(code):
            stage_codes[w_id] = int(code)
    code_to_label.setdefault(-1, "unlabeled")
    present_labels = {c: code_to_label.get(c, f"code_{c}") for c in np.unique(stage_codes)}
    return stage_codes, present_labels


def _resolve_time(handle: h5py.File, n_points: int) -> np.ndarray:
    if "/time" in handle:
        try:
            time_arr = np.asarray(handle["/time"][:], dtype=float)
            if time_arr.shape[0] == n_points:
                return time_arr
        except Exception:
            pass
    fs_out = handle.attrs.get("fs_out")
    if isinstance(fs_out, (int, float, np.number)) and float(fs_out) > 0:
        return np.arange(n_points, dtype=float) / float(fs_out)
    return np.arange(n_points, dtype=float)


def load_subject(path: Path) -> SubjectData:
    """Load one subject's MNPS/MNJ data from its H5 file.

    Raises `ValueError` if the file does not expose any usable 3D MNPS
    coordinates under any known coordinate contract.
    """
    path = Path(path)
    with h5py.File(path, "r") as handle:
        run = read_run_contract(handle)
        geometry = read_geometry_contract_state(handle)

        resolved_3d = _first_resolved(resolve_coords_3d, handle)
        if resolved_3d is None:
            raise ValueError(
                f"No usable MNPS 3D coordinates found in {path} "
                f"(tried contracts: {', '.join(KNOWN_COORDINATE_CONTRACTS)})."
            )
        n_points = int(resolved_3d.values.shape[0])

        resolved_9d = _first_resolved(resolve_coords_9d, handle)

        resolved_jac_3d = _first_resolved(resolve_jacobian_3d, handle)
        jacobian_3d = None
        if resolved_jac_3d is not None:
            invariants = _compute_jacobian_invariants(resolved_jac_3d.j_hat)
            jacobian_3d = JacobianData(
                j_hat=resolved_jac_3d.j_hat,
                centers=resolved_jac_3d.centers,
                resolved_coordinate_contract=resolved_jac_3d.resolved_coordinate_contract,
                **invariants,
            )

        resolved_jac_9d = _first_resolved(resolve_jacobian_9d, handle)
        jacobian_9d = None
        if resolved_jac_9d is not None:
            jacobian_9d = JacobianData(
                j_hat=resolved_jac_9d.j_hat,
                centers=resolved_jac_9d.centers,
                resolved_coordinate_contract=resolved_jac_9d.resolved_coordinate_contract,
            )

        time = _resolve_time(handle, n_points)
        stage_codes, stage_labels = _load_stage_per_window(handle, n_points)

        attrs = handle.attrs
        dataset_id = _to_str(attrs.get("dataset")) or _to_str(attrs.get("dataset_id")) or path.parent.name
        subject_id = _to_str(attrs.get("subject_id")) or path.stem
        condition = _to_str(attrs.get("condition"))
        task = _to_str(attrs.get("task"))
        group = _to_str(attrs.get("group"))

    return SubjectData(
        path=path,
        dataset_id=dataset_id,
        subject_id=subject_id,
        condition=condition,
        task=task,
        group=group,
        coords_3d=resolved_3d.values,
        coords_3d_names=list(resolved_3d.names),
        coords_3d_contract=resolved_3d.resolved_coordinate_contract,
        time=time,
        coords_9d=resolved_9d.values if resolved_9d is not None else None,
        coords_9d_names=list(resolved_9d.names) if resolved_9d is not None else None,
        coords_9d_contract=resolved_9d.resolved_coordinate_contract if resolved_9d is not None else None,
        jacobian_3d=jacobian_3d,
        jacobian_9d=jacobian_9d,
        jacobian_9d_status=geometry.status,
        jacobian_9d_windows_retained=geometry.jacobian_9d_windows_retained,
        jacobian_9d_invalid_windows=geometry.jacobian_9d_invalid_windows,
        stage_codes=stage_codes,
        stage_labels=stage_labels,
    )


_SUBJECT_CACHE: Dict[str, SubjectData] = {}
_SUBJECT_CACHE_MAX = 16


def load_subject_cached(path: Path) -> SubjectData:
    """`load_subject` with a small in-process cache keyed by resolved path.

    Avoids re-reading the same H5 file from disk on every Dash callback
    (e.g. when only the time slider changes, the subject data is unchanged).
    """
    key = str(Path(path).resolve())
    cached = _SUBJECT_CACHE.get(key)
    if cached is not None:
        return cached
    data = load_subject(Path(key))
    if len(_SUBJECT_CACHE) >= _SUBJECT_CACHE_MAX:
        _SUBJECT_CACHE.pop(next(iter(_SUBJECT_CACHE)))
    _SUBJECT_CACHE[key] = data
    return data
