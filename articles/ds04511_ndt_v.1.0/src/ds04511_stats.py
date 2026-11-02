"""Paired within-subject statistics. Exploratory unless a later lock says otherwise."""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np
from scipy import stats

from ds04511_aggregate import sign_test_denominator


def finite_array(values: Any) -> np.ndarray:
    array = np.asarray(values, dtype=float).reshape(-1)
    return array[np.isfinite(array)]


def cohens_dz(differences: Any) -> float:
    array = finite_array(differences)
    if array.size < 2:
        return float("nan")
    sd = float(np.std(array, ddof=1))
    if sd <= 0 or not np.isfinite(sd):
        return float("nan")
    return float(np.mean(array) / sd)


def holm(p_values: Sequence[float]) -> list[float]:
    p = np.asarray(p_values, dtype=float)
    m = p.size
    out = np.full(m, np.nan)
    order = np.argsort(p)
    running = 0.0
    for rank, idx in enumerate(order):
        if not np.isfinite(p[idx]):
            continue
        adj = min(1.0, float(p[idx]) * (m - rank))
        running = max(running, adj)
        out[idx] = running
    return [float(value) for value in out]


def bh_fdr(p_values: Sequence[float]) -> np.ndarray:
    p = np.asarray(p_values, dtype=float)
    q = np.full(p.shape, np.nan, dtype=float)
    valid = np.isfinite(p)
    if not valid.any():
        return q
    work = p[valid]
    order = np.argsort(work)
    ranks = np.arange(1, work.size + 1, dtype=float)
    raw = (work[order] * work.size) / ranks
    adjusted = np.minimum.accumulate(raw[::-1])[::-1]
    q_valid = np.empty_like(work)
    q_valid[order] = np.clip(adjusted, 0.0, 1.0)
    q[valid] = q_valid
    return q


def exact_sign_test_p(differences: Any) -> float:
    counts = sign_test_denominator(differences)
    n = int(counts["n_nonzero"])
    if n < 1:
        return float("nan")
    n_pos = int(counts["n_positive"])
    return float(stats.binomtest(n_pos, n, 0.5, alternative="two-sided").pvalue)


def wilcoxon_p(differences: Any) -> float:
    array = finite_array(differences)
    array = array[array != 0.0]
    if array.size < 1:
        return float("nan")
    try:
        return float(stats.wilcoxon(array, alternative="two-sided", zero_method="wilcox").pvalue)
    except ValueError:
        return float("nan")


def friedman_p(*groups: Any) -> tuple[float, float, int]:
    arrays = [np.asarray(group, dtype=float).reshape(-1) for group in groups]
    if not arrays:
        return float("nan"), float("nan"), 0
    n = arrays[0].size
    if any(item.size != n for item in arrays) or n < 3 or len(arrays) < 3:
        return float("nan"), float("nan"), int(n)
    mask = np.ones(n, dtype=bool)
    for item in arrays:
        mask &= np.isfinite(item)
    kept = [item[mask] for item in arrays]
    if kept[0].size < 3:
        return float("nan"), float("nan"), int(kept[0].size)
    try:
        stat, p_value = stats.friedmanchisquare(*kept)
        return float(stat), float(p_value), int(kept[0].size)
    except ValueError:
        return float("nan"), float("nan"), int(kept[0].size)


def percentile_bootstrap(
    differences: Any,
    stat_fn,
    *,
    n_boot: int,
    seed: int,
    alpha: float = 0.05,
) -> tuple[float, float, int]:
    array = finite_array(differences)
    if array.size < 2:
        return float("nan"), float("nan"), 0
    rng = np.random.default_rng(seed)
    stats_boot = np.empty(n_boot, dtype=float)
    for index in range(n_boot):
        sample = array[rng.integers(0, array.size, size=array.size)]
        stats_boot[index] = float(stat_fn(sample))
    stats_boot = stats_boot[np.isfinite(stats_boot)]
    if stats_boot.size < max(50, int(0.5 * n_boot)):
        return float("nan"), float("nan"), int(stats_boot.size)
    lo = float(np.percentile(stats_boot, 100 * (alpha / 2)))
    hi = float(np.percentile(stats_boot, 100 * (1 - alpha / 2)))
    return lo, hi, int(stats_boot.size)
