"""Recording-level aggregation helpers. Tested on synthetics; not a contrast runner."""
from __future__ import annotations

from typing import Any

import numpy as np

from apollo_common import MIN_VALID_FRACTION, MIN_VALID_TIMEPOINTS


def recording_median(
    values: Any,
    valid: Any,
    *,
    min_n: int = MIN_VALID_TIMEPOINTS,
    min_frac: float = MIN_VALID_FRACTION,
    extra_exclude: Any | None = None,
) -> dict[str, Any]:
    """Median over valid finite samples. Gaps/NaNs stay missing; never filled with zero."""
    array = np.asarray(values, dtype=float).reshape(-1)
    mask = np.asarray(valid, dtype=float).reshape(-1) == 1
    if extra_exclude is not None:
        exclude = np.asarray(extra_exclude, dtype=float).reshape(-1) == 1
        if exclude.size != array.size:
            raise ValueError("extra_exclude length must match values")
        mask = mask & ~exclude
    if mask.size != array.size:
        raise ValueError("valid mask length must match values")
    n_exported = int(array.size)
    finite_valid = mask & np.isfinite(array)
    n_valid = int(np.sum(finite_valid))
    frac = float(n_valid / n_exported) if n_exported else float("nan")
    included = bool(n_valid >= min_n and n_exported > 0 and frac >= min_frac)
    median = float(np.median(array[finite_valid])) if included else float("nan")
    return {
        "n_exported": n_exported,
        "n_valid": n_valid,
        "valid_fraction": frac,
        "included": included,
        "median": median,
        "missing_filled_with_zero": False,
    }


def paired_subject_difference(sedation: float, baseline: float) -> dict[str, Any]:
    """Sedation minus baseline. Zero differences are retained for reporting."""
    if not (np.isfinite(sedation) and np.isfinite(baseline)):
        return {"difference": float("nan"), "sign": 0, "nonzero": False, "testable": False}
    difference = float(sedation - baseline)
    if difference == 0.0:
        return {"difference": 0.0, "sign": 0, "nonzero": False, "testable": False}
    return {
        "difference": difference,
        "sign": 1 if difference > 0 else -1,
        "nonzero": True,
        "testable": True,
    }


def inferential_units(*, grain: str, n_rows: int, broadcast_recording_operator: bool) -> int:
    """Window-shaped copies of a recording operator are one observation, not n_rows."""
    if grain == "recording" or broadcast_recording_operator:
        return 1
    return int(n_rows)


def sign_test_denominator(differences: Any) -> dict[str, Any]:
    """Exact zeros leave the paired table but drop from the binomial denominator."""
    array = np.asarray(differences, dtype=float).reshape(-1)
    finite = array[np.isfinite(array)]
    n_zero = int(np.sum(finite == 0.0))
    nonzero = finite[finite != 0.0]
    return {
        "n_finite": int(finite.size),
        "n_zero": n_zero,
        "n_nonzero": int(nonzero.size),
        "n_positive": int(np.sum(nonzero > 0)),
        "n_negative": int(np.sum(nonzero < 0)),
    }
