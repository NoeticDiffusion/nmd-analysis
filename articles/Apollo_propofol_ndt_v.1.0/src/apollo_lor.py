"""Chennu-style binomial LOR labels. Occupancy-blind."""
from __future__ import annotations

import numpy as np
from scipy.stats import binomtest

N_TRIALS = 40
CI_LEVEL = 0.95


def binomial_ci(k: float, n: int = N_TRIALS, level: float = CI_LEVEL) -> tuple[float, float]:
    if not np.isfinite(k) or n < 1:
        return float("nan"), float("nan")
    count = int(round(float(k)))
    if count < 0 or count > n:
        return float("nan"), float("nan")
    interval = binomtest(count, n).proportion_ci(confidence_level=level, method="exact")
    return float(interval.low), float(interval.high)


def intervals_nonoverlap_later_below(base_lo: float, base_hi: float, later_lo: float, later_hi: float) -> bool:
    return all(np.isfinite([base_lo, base_hi, later_lo, later_hi])) and later_hi < base_lo


def lor_status(k_baseline: float, k_moderate: float, n: int = N_TRIALS) -> str:
    base_lo, base_hi = binomial_ci(k_baseline, n)
    later_lo, later_hi = binomial_ci(k_moderate, n)
    if not all(np.isfinite([base_lo, base_hi, later_lo, later_hi])):
        return "missing"
    if intervals_nonoverlap_later_below(base_lo, base_hi, later_lo, later_hi):
        return "lor_impaired"
    return "responsive"


def ror_status(k_baseline: float, k_recovery: float, lor: str, n: int = N_TRIALS) -> str:
    if lor != "lor_impaired":
        return "not_applicable"
    base_lo, base_hi = binomial_ci(k_baseline, n)
    rec_lo, rec_hi = binomial_ci(k_recovery, n)
    if not all(np.isfinite([base_lo, base_hi, rec_lo, rec_hi])):
        return "missing"
    if rec_hi < base_lo or rec_lo > base_hi:
        return "not_returned"
    return "returned"
