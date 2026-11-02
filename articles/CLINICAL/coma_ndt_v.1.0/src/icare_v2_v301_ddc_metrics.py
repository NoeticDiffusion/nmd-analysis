"""COMA-DDC-001 analysis-side drift-spread coupling (sl_008).

Not ingest A_bD / R_b_over_a. Not Ito. Cohort-anchored re-kNN with
blocked chronological cross-fitting (n_blocks=2, embargo_steps=4).
"""
from __future__ import annotations

from typing import Any

import numpy as np

from icare_v2_v301_l1_estimators import ensure_mndm

EPS = 1e-12
K = 20
MIN_NEIGH = 10
EMBARGO_STEPS = 4
PSD_FLOOR = 1e-8
MIN_SAMPLES = 30
MAX_DT_REL = 0.05
MIN_VALID_FRAC = 0.1


def coupling_metrics(b: np.ndarray, a: np.ndarray, *, dt: float, eps: float = EPS) -> dict[str, float]:
    """Algebraic coupling of one local mean and one local increment covariance."""
    drift = np.asarray(b, dtype=float).reshape(-1)
    tensor = np.asarray(a, dtype=float)
    if drift.size != 3 or tensor.shape != (3, 3) or not np.isfinite(dt) or dt <= 0:
        return _nan_metrics()
    tensor = 0.5 * (tensor + tensor.T)
    if not np.isfinite(drift).all() or not np.isfinite(tensor).all():
        return _nan_metrics()
    tr_a = float(np.trace(tensor))
    b_norm = float(np.linalg.norm(drift))
    if tr_a > eps:
        r_ba = float(dt * (b_norm**2) / tr_a)
    else:
        r_ba = float("nan")
    out = {
        "f_parallel": float("nan"),
        "f_perp": float("nan"),
        "r_ba": r_ba,
        "d_perp_eff": float("nan"),
        "a_dom": float("nan"),
        "b_norm": b_norm,
        "tr_a": tr_a,
    }
    if b_norm <= eps or tr_a <= eps:
        return out
    u = drift / b_norm
    rayleigh = float(u @ tensor @ u)
    f_par = float(rayleigh / tr_a)
    out["f_parallel"] = f_par
    out["f_perp"] = float(1.0 - f_par)
    evals = np.clip(np.linalg.eigvalsh(tensor), 0.0, None)
    lam_max = float(evals[-1])
    if lam_max > eps:
        out["a_dom"] = float(np.clip(rayleigh / lam_max, 0.0, 1.0))
    p = np.eye(3) - np.outer(u, u)
    a_perp = p @ tensor @ p
    tr_p = float(np.trace(a_perp))
    tr_p2 = float(np.trace(a_perp @ a_perp))
    if tr_p2 > eps:
        out["d_perp_eff"] = float((tr_p**2) / tr_p2)
    return out


def _nan_metrics() -> dict[str, float]:
    return {
        "f_parallel": float("nan"),
        "f_perp": float("nan"),
        "r_ba": float("nan"),
        "d_perp_eff": float("nan"),
        "a_dom": float("nan"),
        "b_norm": float("nan"),
        "tr_a": float("nan"),
    }


def _finite_iqr(values: np.ndarray) -> float:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size < 4:
        return float("nan")
    q75, q25 = np.percentile(finite, [75.0, 25.0])
    return float(q75 - q25)


def _average_pair(left: dict[str, float], right: dict[str, float]) -> dict[str, float]:
    out: dict[str, float] = {}
    for key in left:
        vals = np.asarray([left[key], right[key]], dtype=float)
        finite = vals[np.isfinite(vals)]
        out[key] = float(np.mean(finite)) if finite.size else float("nan")
    return out


def estimate_crossfit_coupling(
    state: np.ndarray,
    time: np.ndarray,
    *,
    segment_id: np.ndarray | None = None,
    dt_fallback: float = 4.0,
) -> dict[str, Any]:
    """Estimate F_perp, R_b/a, d_perp_eff with (b_A, a_B) and (b_B, a_A)."""
    ensure_mndm()
    from mndm.dynamical_families.finite_lag_drift import _fill_conditional_mean
    from mndm.dynamical_families.transition_support import build_transition_support
    from mndm.dynamical_families.validity import chunked_nearest_neighbors, project_to_psd, validate_trajectory

    x, t, segments, finite_state, reason = validate_trajectory(
        np.asarray(state, dtype=float),
        np.asarray(time, dtype=float),
        min_samples=MIN_SAMPLES,
        segment_id=segment_id,
    )
    empty = {
        "status": "insufficient_support",
        "failure_reason": reason or "invalid_trajectory",
        "medians": {k: float("nan") for k in ("f_perp", "f_parallel", "r_ba", "d_perp_eff", "a_dom", "b_norm", "tr_a")},
        "iqrs": {k: float("nan") for k in ("f_perp", "r_ba", "a_dom")},
        "n_valid": 0,
        "n_time": int(np.asarray(state).shape[0]) if np.asarray(state).ndim == 2 else 0,
        "nominal_dt_sec": float("nan"),
    }
    if reason is not None or x is None or t is None or segments is None or finite_state is None:
        return empty
    support = build_transition_support(
        x, t, segments, lag=1, max_gap_sec=None, max_dt_relative_deviation=MAX_DT_REL
    )
    source_idx = np.asarray(support.source_idx, dtype=np.int32)
    increments = np.asarray(support.increments, dtype=float)
    dt = float(support.nominal_dt_sec) if np.isfinite(support.nominal_dt_sec) and support.nominal_dt_sec > 0 else float(dt_fallback)
    min_support = max(MIN_NEIGH, 3 * x.shape[1] + 1)
    n_time = int(x.shape[0])
    if (
        source_idx.size < min_support
        or int(K) >= int(source_idx.size)
        or support.failure_reason in {"non_positive_nominal_dt", "materially_irregular_increment_timestep"}
    ):
        empty["failure_reason"] = support.failure_reason or "insufficient_valid_increment_pairs"
        empty["n_time"] = n_time
        empty["nominal_dt_sec"] = dt
        return empty
    split_index = int(np.median(source_idx))
    fold1_mask = source_idx < (split_index - EMBARGO_STEPS)
    fold2_mask = source_idx > (split_index + EMBARGO_STEPS)
    fold1_idx = source_idx[fold1_mask]
    fold2_idx = source_idx[fold2_mask]
    fold1_dx = increments[fold1_mask]
    fold2_dx = increments[fold2_mask]
    if (
        fold1_idx.size < min_support
        or fold2_idx.size < min_support
        or int(K) >= int(fold1_idx.size)
        or int(K) >= int(fold2_idx.size)
    ):
        empty["failure_reason"] = "insufficient_crossfit_folds"
        empty["n_time"] = n_time
        empty["nominal_dt_sec"] = dt
        return empty
    finite_idx = np.flatnonzero(finite_state)
    query = finite_idx[(finite_idx < (split_index - EMBARGO_STEPS)) | (finite_idx > (split_index + EMBARGO_STEPS))]
    b1 = _fill_conditional_mean(
        x, t, query, ref_source_idx=fold1_idx, ref_increments=fold1_dx,
        neighborhood_k=K, minimum_support=min_support, max_neighborhood_radius=None,
        min_temporal_span_sec=None, weight_mode="inverse_distance", nominal_dt=dt,
        epsilon=EPS, store_neighbor_source_idx=False,
    )
    b2 = _fill_conditional_mean(
        x, t, query, ref_source_idx=fold2_idx, ref_increments=fold2_dx,
        neighborhood_k=K, minimum_support=min_support, max_neighborhood_radius=None,
        min_temporal_span_sec=None, weight_mode="inverse_distance", nominal_dt=dt,
        epsilon=EPS, store_neighbor_source_idx=False,
    )
    a1 = _fill_local_covariance(
        x, query, fold1_idx, fold1_dx, dt=dt, min_support=min_support, knn_fn=chunked_nearest_neighbors, psd_fn=project_to_psd
    )
    a2 = _fill_local_covariance(
        x, query, fold2_idx, fold2_dx, dt=dt, min_support=min_support, knn_fn=chunked_nearest_neighbors, psd_fn=project_to_psd
    )
    series = {name: np.full(n_time, np.nan, dtype=float) for name in ("f_perp", "f_parallel", "r_ba", "d_perp_eff", "a_dom", "b_norm", "tr_a")}
    n_valid = 0
    for center in query:
        pair_ab = coupling_metrics(b1["b_hat"][center], a2[center], dt=dt)
        pair_ba = coupling_metrics(b2["b_hat"][center], a1[center], dt=dt)
        avg = _average_pair(pair_ab, pair_ba)
        if np.isfinite(avg["f_perp"]) or np.isfinite(avg["r_ba"]):
            n_valid += 1
        for key in series:
            series[key][int(center)] = avg[key]
    if n_valid < max(1, int(np.ceil(MIN_VALID_FRAC * n_time))):
        empty["failure_reason"] = "insufficient_valid_neighborhood_coverage"
        empty["n_time"] = n_time
        empty["n_valid"] = n_valid
        empty["nominal_dt_sec"] = dt
        return empty
    medians = {key: float(np.nanmedian(vals)) if np.isfinite(vals).any() else float("nan") for key, vals in series.items()}
    iqrs = {key: _finite_iqr(series[key]) for key in ("f_perp", "r_ba", "a_dom")}
    return {
        "status": "computed",
        "failure_reason": None,
        "series": series,
        "medians": medians,
        "iqrs": iqrs,
        "n_valid": int(n_valid),
        "n_time": n_time,
        "nominal_dt_sec": dt,
        "split_index": split_index,
        "fold1_n": int(fold1_idx.size),
        "fold2_n": int(fold2_idx.size),
        "qualification": "analysis_owned_crossfit_not_ingest_A_bD",
    }


def _fill_local_covariance(
    x: np.ndarray,
    query_idx: np.ndarray,
    ref_source_idx: np.ndarray,
    ref_increments: np.ndarray,
    *,
    dt: float,
    min_support: int,
    knn_fn,
    psd_fn,
) -> np.ndarray:
    n_time, dim = x.shape
    out = np.full((n_time, dim, dim), np.nan, dtype=float)
    n_refs = int(ref_source_idx.size)
    if n_refs < min_support or int(K) >= n_refs or query_idx.size == 0:
        return out
    k_use = min(int(K), n_refs)
    nearest_indices, _ = knn_fn(x[query_idx], x[ref_source_idx], k_use)
    for row, center in enumerate(query_idx):
        nearest = np.asarray(nearest_indices[row], dtype=np.intp)
        keep = ref_source_idx[nearest] != int(center)
        nearest = nearest[keep]
        local = np.asarray(ref_increments[nearest], dtype=float)
        finite = np.isfinite(local).all(axis=1)
        local = local[finite]
        if local.shape[0] < min_support:
            continue
        cov = np.atleast_2d(np.cov(local, rowvar=False, ddof=1)) / float(dt)
        try:
            tensor, _ = psd_fn(cov, eigenvalue_floor=PSD_FLOOR)
        except (ValueError, np.linalg.LinAlgError):
            continue
        out[int(center)] = tensor
    return out
