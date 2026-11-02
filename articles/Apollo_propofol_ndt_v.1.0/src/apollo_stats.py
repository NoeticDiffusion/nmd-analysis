"""Paired within-subject statistics. Exploratory unless a later lock says otherwise."""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np
from scipy import stats

from apollo_aggregate import sign_test_denominator


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


def cohens_d(group_a: Any, group_b: Any) -> float:
    a = finite_array(group_a)
    b = finite_array(group_b)
    if a.size < 2 or b.size < 2:
        return float("nan")
    pooled = (a.size - 1) * float(np.var(a, ddof=1)) + (b.size - 1) * float(np.var(b, ddof=1))
    pooled = np.sqrt(pooled / (a.size + b.size - 2))
    if pooled <= 0 or not np.isfinite(pooled):
        return float("nan")
    return float((np.mean(a) - np.mean(b)) / pooled)


def mannwhitney_p(group_a: Any, group_b: Any) -> float:
    a = finite_array(group_a)
    b = finite_array(group_b)
    if a.size < 1 or b.size < 1:
        return float("nan")
    try:
        return float(stats.mannwhitneyu(a, b, alternative="two-sided").pvalue)
    except ValueError:
        return float("nan")


def spearman_rho_p(x: Any, y: Any) -> tuple[float, float]:
    left = np.asarray(x, dtype=float).reshape(-1)
    right = np.asarray(y, dtype=float).reshape(-1)
    ok = np.isfinite(left) & np.isfinite(right)
    if int(ok.sum()) < 3:
        return float("nan"), float("nan")
    result = stats.spearmanr(left[ok], right[ok])
    return float(result.statistic), float(result.pvalue)


def percentile_bootstrap_median_diff(
    group_a: Any,
    group_b: Any,
    *,
    n_boot: int,
    seed: int,
    alpha: float = 0.05,
) -> tuple[float, float, int]:
    a = finite_array(group_a)
    b = finite_array(group_b)
    if a.size < 1 or b.size < 1:
        return float("nan"), float("nan"), 0
    rng = np.random.default_rng(seed)
    stats_boot = np.empty(n_boot, dtype=float)
    for index in range(n_boot):
        sample_a = a[rng.integers(0, a.size, size=a.size)]
        sample_b = b[rng.integers(0, b.size, size=b.size)]
        stats_boot[index] = float(np.median(sample_a) - np.median(sample_b))
    stats_boot = stats_boot[np.isfinite(stats_boot)]
    if stats_boot.size < max(50, int(0.5 * n_boot)):
        return float("nan"), float("nan"), int(stats_boot.size)
    lo = float(np.percentile(stats_boot, 100 * (alpha / 2)))
    hi = float(np.percentile(stats_boot, 100 * (1 - alpha / 2)))
    return lo, hi, int(stats_boot.size)


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
