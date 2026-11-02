"""Outcome-blind matching and increment summaries for Apollo C3."""
from __future__ import annotations

from typing import Any

import numpy as np

from apollo_c3_panel import (
    CALIPER_MULTIPLIER,
    DT_MAX,
    DT_MIN,
    MAD_FLOOR,
    MIN_PAIRS,
    RANDOM_MATCH_SEED,
    SPECTRAL_FEATURES,
)


def decode_names(values: Any) -> list[str]:
    out = []
    for item in np.asarray(values).reshape(-1):
        if isinstance(item, bytes):
            out.append(item.decode("utf-8"))
        else:
            out.append(str(item))
    return out


def eligible_mask(x: np.ndarray, dxdt: np.ndarray, valid: np.ndarray, observed_dt: np.ndarray) -> np.ndarray:
    coords = np.asarray(x, dtype=float)
    velocity = np.asarray(dxdt, dtype=float)
    ok = np.asarray(valid, dtype=float).reshape(-1) == 1.0
    dt = np.asarray(observed_dt, dtype=float).reshape(-1)
    finite_x = np.isfinite(coords).all(axis=1)
    finite_v = np.isfinite(velocity).all(axis=1)
    finite_dt = np.isfinite(dt) & (dt >= DT_MIN) & (dt <= DT_MAX)
    n = min(coords.shape[0], velocity.shape[0], ok.size, dt.size)
    mask = np.zeros(coords.shape[0], dtype=bool)
    mask[:n] = finite_x[:n] & finite_v[:n] & ok[:n] & finite_dt[:n]
    return mask


def pairwise_distances(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    left = np.asarray(a, dtype=float)
    right = np.asarray(b, dtype=float)
    delta = left[:, None, :] - right[None, :, :]
    return np.sqrt(np.sum(delta * delta, axis=2))


def median_loo_nn(points: np.ndarray) -> float:
    array = np.asarray(points, dtype=float)
    if array.shape[0] < 2:
        return float("nan")
    dist = pairwise_distances(array, array)
    np.fill_diagonal(dist, np.inf)
    nearest = np.min(dist, axis=1)
    nearest = nearest[np.isfinite(nearest)]
    if nearest.size == 0:
        return float("nan")
    return float(np.median(nearest))


def greedy_match(later: np.ndarray, earlier: np.ndarray, caliper: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if later.size == 0 or earlier.size == 0 or not np.isfinite(caliper) or caliper < 0:
        empty = np.array([], dtype=int)
        return empty, empty, np.array([], dtype=float)
    dist = pairwise_distances(later, earlier)
    order = np.argsort(dist, axis=None)
    used_later = np.zeros(later.shape[0], dtype=bool)
    used_earlier = np.zeros(earlier.shape[0], dtype=bool)
    later_idx: list[int] = []
    earlier_idx: list[int] = []
    kept: list[float] = []
    n_later, n_earlier = dist.shape
    for flat in order:
        i, j = divmod(int(flat), n_earlier)
        d = float(dist[i, j])
        if d > caliper or not np.isfinite(d):
            break
        if used_later[i] or used_earlier[j]:
            continue
        used_later[i] = True
        used_earlier[j] = True
        later_idx.append(i)
        earlier_idx.append(j)
        kept.append(d)
        if used_later.all() or used_earlier.all():
            break
    return (
        np.asarray(later_idx, dtype=int),
        np.asarray(earlier_idx, dtype=int),
        np.asarray(kept, dtype=float),
    )


def random_partners(n_later: int, n_earlier: int, n_pairs: int, seed: int = RANDOM_MATCH_SEED) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    n = min(int(n_later), int(n_earlier), int(n_pairs))
    if n <= 0:
        empty = np.array([], dtype=int)
        return empty, empty
    later = rng.choice(n_later, size=n, replace=False)
    earlier = rng.choice(n_earlier, size=n, replace=False)
    return later.astype(int), earlier.astype(int)


def robust_z(values: np.ndarray, center: np.ndarray, scale: np.ndarray) -> np.ndarray:
    scaled = np.asarray(scale, dtype=float).copy()
    scaled = np.where(np.isfinite(scaled) & (scaled > MAD_FLOOR), scaled, np.nan)
    return (np.asarray(values, dtype=float) - np.asarray(center, dtype=float)) / scaled


def baseline_center_scale(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    array = np.asarray(values, dtype=float)
    center = np.nanmedian(array, axis=0)
    mad = np.nanmedian(np.abs(array - center), axis=0)
    scale = 1.4826 * mad
    scale = np.where(np.isfinite(scale) & (scale > MAD_FLOOR), scale, np.nan)
    return center, scale


def spectral_block(feature_values: np.ndarray, names: list[str], mask: np.ndarray, center: np.ndarray, scale: np.ndarray) -> np.ndarray:
    columns = []
    for name in SPECTRAL_FEATURES:
        if name not in names:
            raise KeyError(f"missing spectral feature {name!r}")
        columns.append(int(names.index(name)))
    block = np.asarray(feature_values, dtype=float)[:, columns]
    return robust_z(block[mask], center, scale)


def speed_scalar(dxdt: np.ndarray) -> float:
    vectors = np.asarray(dxdt, dtype=float)
    if vectors.size == 0:
        return float("nan")
    norms = np.linalg.norm(vectors, axis=1)
    norms = norms[np.isfinite(norms)]
    if norms.size == 0:
        return float("nan")
    return float(np.median(norms))


def occupancy_scalar(points: np.ndarray) -> float:
    array = np.asarray(points, dtype=float)
    if array.size == 0:
        return float("nan")
    norms = np.linalg.norm(array, axis=1)
    norms = norms[np.isfinite(norms)]
    if norms.size == 0:
        return float("nan")
    return float(np.median(norms))


def feature_increments(z: np.ndarray, time: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """One-step Δz/Δt on the same grid. Last sample has no successor."""
    state = np.asarray(z, dtype=float)
    clock = np.asarray(time, dtype=float).reshape(-1)
    n, dim = state.shape[0], state.shape[1] if state.ndim == 2 else 0
    dxdt = np.full((n, dim), np.nan, dtype=float)
    valid = np.zeros(n, dtype=float)
    observed_dt = np.full(n, np.nan, dtype=float)
    if n < 2 or dim == 0 or clock.size != n:
        return dxdt, valid, observed_dt
    delta_t = np.diff(clock)
    delta_z = np.diff(state, axis=0)
    ok = (
        np.isfinite(delta_t)
        & (delta_t >= DT_MIN)
        & (delta_t <= DT_MAX)
        & np.isfinite(state[:-1]).all(axis=1)
        & np.isfinite(state[1:]).all(axis=1)
        & np.isfinite(delta_z).all(axis=1)
    )
    with np.errstate(invalid="ignore", divide="ignore"):
        dxdt[:-1] = np.where(ok[:, None], delta_z / delta_t[:, None], np.nan)
    observed_dt[:-1] = np.where(ok, delta_t, np.nan)
    valid[:-1] = ok.astype(float)
    return dxdt, valid, observed_dt


def spread_scalar(dxdt: np.ndarray) -> float:
    vectors = np.asarray(dxdt, dtype=float)
    finite = vectors[np.isfinite(vectors).all(axis=1)]
    if finite.shape[0] < 2:
        return float("nan")
    cov = np.cov(finite, rowvar=False, ddof=1)
    if np.ndim(cov) == 0:
        return float(cov)
    return float(np.trace(np.atleast_2d(cov)))


def match_subject(
    later_x: np.ndarray,
    earlier_x: np.ndarray,
    later_dx: np.ndarray,
    earlier_dx: np.ndarray,
    later_valid: np.ndarray,
    earlier_valid: np.ndarray,
    later_dt: np.ndarray,
    earlier_dt: np.ndarray,
    *,
    later_match: np.ndarray | None = None,
    earlier_match: np.ndarray | None = None,
) -> dict[str, Any]:
    later_ok = eligible_mask(later_x, later_dx, later_valid, later_dt)
    earlier_ok = eligible_mask(earlier_x, earlier_dx, earlier_valid, earlier_dt)
    later_idx = np.flatnonzero(later_ok)
    earlier_idx = np.flatnonzero(earlier_ok)
    later_space = np.asarray(later_x[later_ok] if later_match is None else later_match, dtype=float)
    earlier_space = np.asarray(earlier_x[earlier_ok] if earlier_match is None else earlier_match, dtype=float)
    unmatched_later = later_dx[later_ok]
    unmatched_earlier = earlier_dx[earlier_ok]
    later_finite = np.isfinite(later_space).all(axis=1)
    earlier_finite = np.isfinite(earlier_space).all(axis=1)
    later_space = later_space[later_finite]
    earlier_space = earlier_space[earlier_finite]
    unmatched_later = unmatched_later[later_finite]
    unmatched_earlier = unmatched_earlier[earlier_finite]
    later_idx = later_idx[later_finite]
    earlier_idx = earlier_idx[earlier_finite]
    caliper = CALIPER_MULTIPLIER * median_loo_nn(earlier_space)
    m_later, m_earlier, distances = greedy_match(later_space, earlier_space, caliper)
    n_pairs = int(m_later.size)
    included = n_pairs >= MIN_PAIRS
    if included:
        matched_later = unmatched_later[m_later]
        matched_earlier = unmatched_earlier[m_earlier]
    else:
        matched_later = np.empty((0, later_dx.shape[1] if later_dx.ndim == 2 else 0))
        matched_earlier = np.empty((0, earlier_dx.shape[1] if earlier_dx.ndim == 2 else 0))
    rand_later, rand_earlier = random_partners(int(later_idx.size), int(earlier_idx.size), n_pairs)
    random_later = unmatched_later[rand_later] if rand_later.size else matched_later
    random_earlier = unmatched_earlier[rand_earlier] if rand_earlier.size else matched_earlier
    return {
        "n_later_eligible": int(later_idx.size),
        "n_earlier_eligible": int(earlier_idx.size),
        "n_pairs": n_pairs,
        "n_later_total": int(later_x.shape[0]),
        "match_fraction": float(n_pairs / later_idx.size) if later_idx.size else float("nan"),
        "caliper": float(caliper) if np.isfinite(caliper) else float("nan"),
        "median_match_distance": float(np.median(distances)) if distances.size else float("nan"),
        "included": included,
        "matched_speed_later": speed_scalar(matched_later) if included else float("nan"),
        "matched_speed_earlier": speed_scalar(matched_earlier) if included else float("nan"),
        "matched_spread_later": spread_scalar(matched_later) if included else float("nan"),
        "matched_spread_earlier": spread_scalar(matched_earlier) if included else float("nan"),
        "unmatched_speed_later": speed_scalar(unmatched_later),
        "unmatched_speed_earlier": speed_scalar(unmatched_earlier),
        "unmatched_spread_later": spread_scalar(unmatched_later),
        "unmatched_spread_earlier": spread_scalar(unmatched_earlier),
        "random_speed_later": speed_scalar(random_later) if n_pairs >= MIN_PAIRS else float("nan"),
        "random_speed_earlier": speed_scalar(random_earlier) if n_pairs >= MIN_PAIRS else float("nan"),
        "random_spread_later": spread_scalar(random_later) if n_pairs >= MIN_PAIRS else float("nan"),
        "random_spread_earlier": spread_scalar(random_earlier) if n_pairs >= MIN_PAIRS else float("nan"),
        "matched_occupancy_later": occupancy_scalar(later_space[m_later]) if included else float("nan"),
        "matched_occupancy_earlier": occupancy_scalar(earlier_space[m_earlier]) if included else float("nan"),
        "unmatched_occupancy_later": occupancy_scalar(later_space),
        "unmatched_occupancy_earlier": occupancy_scalar(earlier_space),
    }
