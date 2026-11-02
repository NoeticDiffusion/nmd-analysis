"""COMA-RESID-001 analysis-side cross-fitted residual spread (sl_022).

Blocked chronological split matches COMA-DDC-001. Primary object is the
held-out increment residual after an opposite-fold kNN conditional mean.
This is not innovation, not Ito, not Family B, and not the ingest
transition_residual series (frozen affine generator, no_biological_claim).
"""
from __future__ import annotations

from typing import Any

import numpy as np

from icare_v2_common import diffusion_geometry_from_tensor
from icare_v2_v301_l1_estimators import ensure_mndm

EPS = 1e-12
K = 20
MIN_NEIGH = 10
EMBARGO_STEPS = 4
PSD_FLOOR = 1e-8
MIN_SAMPLES = 30
MAX_DT_REL = 0.05
MIN_VALID_FRAC = 0.1
MEDIAN_KEYS = ("tr_a_raw", "tr_c_resid", "d_eff_resid", "h_tilde_resid", "tr_c_over_a")


def _nan_medians() -> dict[str, float]:
    return {k: float("nan") for k in MEDIAN_KEYS}


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


def _geometry_scalars(tensor: np.ndarray) -> dict[str, float]:
    mat = np.asarray(tensor, dtype=float)
    empty = {"tr_c_resid": float("nan"), "d_eff_resid": float("nan"), "h_tilde_resid": float("nan")}
    if mat.shape != (3, 3) or not np.isfinite(mat).all():
        return empty
    geo = diffusion_geometry_from_tensor(0.5 * (mat + mat.T), eps=EPS)
    return {
        "tr_c_resid": float(geo["d_total"]),
        "d_eff_resid": float(geo["d_eff_a"]),
        "h_tilde_resid": float(geo["h_tilde_a"]),
    }


def _trace_raw(tensor: np.ndarray) -> float:
    mat = np.asarray(tensor, dtype=float)
    if mat.shape != (3, 3) or not np.isfinite(mat).all():
        return float("nan")
    return float(np.trace(0.5 * (mat + mat.T)))


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
    """Matched DDC neighborhood covariance: unweighted sample cov(increments)/dt, PSD floor."""
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


def _predicted_increments(
    x: np.ndarray,
    t: np.ndarray,
    heldout_idx: np.ndarray,
    *,
    ref_source_idx: np.ndarray,
    ref_increments: np.ndarray,
    dt: float,
    min_support: int,
    fill_mean,
) -> np.ndarray:
    """Opposite-fold kNN mean increment. b_hat is velocity, so mu_hat = b_hat * dt."""
    n_held = int(heldout_idx.size)
    dim = int(x.shape[1])
    out = np.full((n_held, dim), np.nan, dtype=float)
    if n_held == 0:
        return out
    packed = fill_mean(
        x,
        t,
        heldout_idx,
        ref_source_idx=ref_source_idx,
        ref_increments=ref_increments,
        neighborhood_k=K,
        minimum_support=min_support,
        max_neighborhood_radius=None,
        min_temporal_span_sec=None,
        weight_mode="inverse_distance",
        nominal_dt=dt,
        epsilon=EPS,
        store_neighbor_source_idx=False,
    )
    b_hat = np.asarray(packed["b_hat"], dtype=float)
    valid = np.asarray(packed["valid"], dtype=float)
    for i, src in enumerate(heldout_idx):
        if valid[int(src)] <= 0:
            continue
        vel = b_hat[int(src)]
        if vel.shape != (dim,) or not np.isfinite(vel).all():
            continue
        out[i] = vel * float(dt)
    return out


def estimate_crossfit_residual_spread(
    state: np.ndarray,
    time: np.ndarray,
    *,
    segment_id: np.ndarray | None = None,
    dt_fallback: float = 4.0,
) -> dict[str, Any]:
    """Cross-fitted residual spread C_r and matched raw increment covariance a_raw.

    Folds are chronological on increment source_idx (median split, embargo 4).
    Residuals are formed on the held-out fold only. Local C_r uses opposite-fold
    neighbors of those residuals. Directions are averaged like DDC.
    """
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
        "medians": _nan_medians(),
        "iqrs": {k: float("nan") for k in ("tr_a_raw", "tr_c_resid", "tr_c_over_a")},
        "n_valid": 0,
        "n_time": int(np.asarray(state).shape[0]) if np.asarray(state).ndim == 2 else 0,
        "nominal_dt_sec": float("nan"),
        "qualification": "analysis_owned_crossfit_residual_spread_not_innovation",
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
    mu2 = _predicted_increments(
        x, t, fold2_idx, ref_source_idx=fold1_idx, ref_increments=fold1_dx, dt=dt, min_support=min_support, fill_mean=_fill_conditional_mean
    )
    mu1 = _predicted_increments(
        x, t, fold1_idx, ref_source_idx=fold2_idx, ref_increments=fold2_dx, dt=dt, min_support=min_support, fill_mean=_fill_conditional_mean
    )
    r2 = fold2_dx - mu2
    r1 = fold1_dx - mu1
    cov_kw = {"dt": dt, "min_support": min_support, "knn_fn": chunked_nearest_neighbors, "psd_fn": project_to_psd}
    c_r_from_fold2 = _fill_local_covariance(x, query, fold2_idx, r2, **cov_kw)
    c_r_from_fold1 = _fill_local_covariance(x, query, fold1_idx, r1, **cov_kw)
    a_raw_fold2 = _fill_local_covariance(x, query, fold2_idx, fold2_dx, **cov_kw)
    a_raw_fold1 = _fill_local_covariance(x, query, fold1_idx, fold1_dx, **cov_kw)
    series = {name: np.full(n_time, np.nan, dtype=float) for name in MEDIAN_KEYS}
    n_valid = 0
    for center in query:
        geo_ab = _geometry_scalars(c_r_from_fold2[int(center)])
        geo_ba = _geometry_scalars(c_r_from_fold1[int(center)])
        avg = _average_pair(geo_ab, geo_ba)
        tr_raw = _average_pair(
            {"tr_a_raw": _trace_raw(a_raw_fold2[int(center)])},
            {"tr_a_raw": _trace_raw(a_raw_fold1[int(center)])},
        )["tr_a_raw"]
        tr_c = avg["tr_c_resid"]
        ratio = float("nan")
        if np.isfinite(tr_c) and np.isfinite(tr_raw) and tr_raw > EPS:
            ratio = float(tr_c / tr_raw)
        if np.isfinite(tr_c):
            n_valid += 1
        i = int(center)
        series["tr_c_resid"][i] = tr_c
        series["d_eff_resid"][i] = avg["d_eff_resid"]
        series["h_tilde_resid"][i] = avg["h_tilde_resid"]
        series["tr_a_raw"][i] = tr_raw
        series["tr_c_over_a"][i] = ratio
    if n_valid < max(1, int(np.ceil(MIN_VALID_FRAC * n_time))):
        empty["failure_reason"] = "insufficient_valid_neighborhood_coverage"
        empty["n_time"] = n_time
        empty["n_valid"] = n_valid
        empty["nominal_dt_sec"] = dt
        return empty
    medians = {key: float(np.nanmedian(vals)) if np.isfinite(vals).any() else float("nan") for key, vals in series.items()}
    iqrs = {key: _finite_iqr(series[key]) for key in ("tr_a_raw", "tr_c_resid", "tr_c_over_a")}
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
        "qualification": "analysis_owned_crossfit_residual_spread_not_innovation",
    }


def estimate_crossfit_r2_mu(
    state: np.ndarray,
    time: np.ndarray,
    *,
    segment_id: np.ndarray | None = None,
    dt_fallback: float = 4.0,
) -> dict[str, Any]:
    """CPC-blind OOS R^2 of the opposite-fold kNN mean (sl_027 QC, not a new family).

    R2_mu = 1 - sum||dX - mu_hat||^2 / sum||dX - mean_train||^2, with SSE and SST
    pooled over both held-out folds. Residual-under-this-mean-model quality, not
    proof that spread is intrinsically unpredictable.
    """
    ensure_mndm()
    from mndm.dynamical_families.finite_lag_drift import _fill_conditional_mean
    from mndm.dynamical_families.transition_support import build_transition_support
    from mndm.dynamical_families.validity import validate_trajectory

    x, t, segments, finite_state, reason = validate_trajectory(
        np.asarray(state, dtype=float),
        np.asarray(time, dtype=float),
        min_samples=MIN_SAMPLES,
        segment_id=segment_id,
    )
    empty = {
        "status": "insufficient_support",
        "failure_reason": reason or "invalid_trajectory",
        "r2_mu": float("nan"),
        "n_held": 0,
        "n_time": int(np.asarray(state).shape[0]) if np.asarray(state).ndim == 2 else 0,
        "nominal_dt_sec": float("nan"),
        "qualification": "crossfit_knn_mean_r2_not_innovation",
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
    empty["n_time"] = n_time
    empty["nominal_dt_sec"] = dt
    if (
        source_idx.size < min_support
        or int(K) >= int(source_idx.size)
        or support.failure_reason in {"non_positive_nominal_dt", "materially_irregular_increment_timestep"}
    ):
        empty["failure_reason"] = support.failure_reason or "insufficient_valid_increment_pairs"
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
        return empty
    mu2 = _predicted_increments(
        x, t, fold2_idx, ref_source_idx=fold1_idx, ref_increments=fold1_dx, dt=dt, min_support=min_support, fill_mean=_fill_conditional_mean
    )
    mu1 = _predicted_increments(
        x, t, fold1_idx, ref_source_idx=fold2_idx, ref_increments=fold2_dx, dt=dt, min_support=min_support, fill_mean=_fill_conditional_mean
    )
    sse = 0.0
    sst = 0.0
    n_held = 0
    for dx_h, mu_h, dx_tr in ((fold2_dx, mu2, fold1_dx), (fold1_dx, mu1, fold2_dx)):
        ok = np.isfinite(dx_h).all(axis=1) & np.isfinite(mu_h).all(axis=1)
        dx_u = dx_h[ok]
        mu_u = mu_h[ok]
        tr = dx_tr[np.isfinite(dx_tr).all(axis=1)]
        if dx_u.shape[0] < 1 or tr.shape[0] < 1:
            continue
        mean_tr = np.mean(tr, axis=0)
        sse += float(np.sum((dx_u - mu_u) ** 2))
        sst += float(np.sum((dx_u - mean_tr) ** 2))
        n_held += int(dx_u.shape[0])
    r2 = float("nan")
    if n_held >= 2 and sst > EPS:
        r2 = float(1.0 - sse / sst)
    if not np.isfinite(r2):
        empty["failure_reason"] = "insufficient_r2_pairs"
        empty["n_held"] = n_held
        return empty
    return {
        "status": "computed",
        "failure_reason": None,
        "r2_mu": r2,
        "n_held": int(n_held),
        "n_time": n_time,
        "nominal_dt_sec": dt,
        "split_index": split_index,
        "fold1_n": int(fold1_idx.size),
        "fold2_n": int(fold2_idx.size),
        "qualification": "crossfit_knn_mean_r2_not_innovation",
    }
