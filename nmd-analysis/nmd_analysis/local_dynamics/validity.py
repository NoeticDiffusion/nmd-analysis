"""Local-dynamics validity helpers and predeclared fidelity classification."""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np


def classify_model_fidelity(
    *,
    group_validity_gap: float,
    group_residual_gap: float,
    minimum_valid_fraction: float,
    warn_gap: float,
    fail_gap: float,
) -> str:
    """Classify differential model fidelity independently of effect direction."""
    if not np.isfinite(group_validity_gap) or not np.isfinite(group_residual_gap):
        return "fail"
    largest_gap = max(abs(float(group_validity_gap)), abs(float(group_residual_gap)))
    if minimum_valid_fraction <= 0 or largest_gap >= fail_gap:
        return "fail"
    if largest_gap >= warn_gap:
        return "warn"
    return "pass"


def build_model_fidelity_audit(row: Mapping[str, Any]) -> dict[str, Any]:
    """Expose the recording-level ingredients used by fidelity comparison."""
    return {
        "rel_mse_baseline": row.get("rel_mse_baseline"),
        "transition_residual_norm": row.get("transition_residual_norm")
        or row.get("transition_residual_mean_norm"),
        "jacobian_valid_fraction": row.get("jacobian_metrics_valid_fraction"),
        "valid_sequence_fraction": row.get("valid_sequence_fraction"),
        "ftr_valid_support": row.get("n_sequences_valid"),
    }
