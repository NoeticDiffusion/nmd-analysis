"""Fail-closed validity rules for serialized v3 dynamical families."""
from __future__ import annotations
import numpy as np

def status(value: object) -> str:
    return "not_recorded" if value is None or str(value) == "" else str(value)

def finite_ok(value: object) -> bool:
    try:
        return bool(np.isfinite(np.asarray(value, dtype=float)).all())
    except (TypeError, ValueError):
        return False

def family_validity(family: str, payload: dict) -> tuple[bool, str | None]:
    s = status(payload.get("computation_status"))
    if s != "computed":
        return False, f"{family}_{s}"
    if family == "diffusion":
        series = payload.get("series", {})
        if "a_hat" not in series:
            return False, "missing_a_hat"
        tensor = np.asarray(series["a_hat"], dtype=float)
        if tensor.ndim != 3 or tensor.shape[1] < 1 or tensor.shape[1] != tensor.shape[2]:
            raise ValueError("malformed diffusion a_hat tensor")
        valid = np.asarray(series.get("valid", []))
        if valid.shape != (len(tensor),):
            return False, "series_alignment_mismatch"
        if not np.any((valid == 1) & np.isfinite(tensor).all(axis=(1, 2))):
            return False, "no_valid_diffusion_windows"
    elif family == "destination":
        series = payload.get("series", {})
        q = np.asarray(series.get("q_hat", series.get("q_A_to_B", [])), dtype=float)
        mask = np.asarray(series.get("valid", []))
        if q.ndim != 1 or mask.shape != q.shape or not np.any((mask == 1) & np.isfinite(q) & (q >= 0) & (q <= 1)):
            return False, "no_valid_destination_probabilities"
    elif family == "resilience":
        if payload.get("summary", {}).get("n_amplitudes_valid", 0) <= 0:
            return False, "no_valid_perturbation_amplitudes"
    elif family in {"chart_drift", "one_step", "amplification", "history", "turning"}:
        # Parent computed is not an Itô/Family-B/operator license; nested
        # identities carry their own qualification_status.
        return True, None
    return True, None
