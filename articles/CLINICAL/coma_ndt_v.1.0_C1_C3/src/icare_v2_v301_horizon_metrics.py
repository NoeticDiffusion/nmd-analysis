"""COMA-HORIZON-001 finite-horizon increment geometry (sl_027).

C_h(x) = Cov(X_{t+h}-X_t | X_t ~ x) on cohort-anchored coords.
Neighbors are chosen among source states and followed to t+h; destinations
are never re-neighbored. Primary object is raw C_h, not C_h/(h dt) and not
a diffusion coefficient. No Jacobian, no generator.

Primary analysis uses common support: a source counts only if it has valid
successors at h in {2,4,8}. Sensitivity uses each horizon's maximal support.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from icare_v2_common import diffusion_geometry_from_tensor
from icare_v2_v301_l1_estimators import ensure_mndm

EPS = 1e-12
K = 20
MIN_NEIGH = 10
PSD_FLOOR = 1e-8
MIN_SAMPLES = 30
MAX_DT_REL = 0.05
MIN_VALID_FRAC = 0.1
HORIZONS = (2, 4, 8)
MODES = ("cs", "ms")
SCALAR_NAMES = ("tr", "d_eff", "h_tilde", "rate")


def _median_keys() -> tuple[str, ...]:
    keys: list[str] = []
    for mode in MODES:
        for h in HORIZONS:
            for name in SCALAR_NAMES:
                keys.append(f"{mode}_{name}_h{h}")
        keys.append(f"{mode}_beta_s")
    return tuple(keys)


MEDIAN_KEYS = _median_keys()


def _nan_medians() -> dict[str, float]:
    return {k: float("nan") for k in MEDIAN_KEYS}


def _geometry_scalars(tensor: np.ndarray) -> dict[str, float]:
    mat = np.asarray(tensor, dtype=float)
    empty = {"tr": float("nan"), "d_eff": float("nan"), "h_tilde": float("nan")}
    if mat.shape != (3, 3) or not np.isfinite(mat).all():
        return empty
    geo = diffusion_geometry_from_tensor(0.5 * (mat + mat.T), eps=EPS)
    return {
        "tr": float(geo["d_total"]),
        "d_eff": float(geo["d_eff_a"]),
        "h_tilde": float(geo["h_tilde_a"]),
    }


def _increment_map(source_idx: np.ndarray, increments: np.ndarray) -> dict[int, np.ndarray]:
    out: dict[int, np.ndarray] = {}
    for i, src in enumerate(np.asarray(source_idx, dtype=np.int32)):
        out[int(src)] = np.asarray(increments[i], dtype=float)
    return out


def _fill_horizon_covariance(
    x: np.ndarray,
    source_idx: np.ndarray,
    increment_lookup: dict[int, np.ndarray],
    *,
    min_support: int,
    knn_fn,
    psd_fn,
    neighbor_idx: np.ndarray | None = None,
) -> np.ndarray:
    """Local cov of source-neighbor increments. neighbor_idx shares kNN across horizons."""
    n_time, dim = x.shape
    out = np.full((n_time, dim, dim), np.nan, dtype=float)
    refs = np.asarray(source_idx, dtype=np.int32)
    n_refs = int(refs.size)
    if n_refs < min_support or int(K) >= n_refs:
        return out
    k_use = min(int(K), n_refs)
    if neighbor_idx is None:
        neighbor_idx, _ = knn_fn(x[refs], x[refs], k_use)
    if neighbor_idx.shape[0] != n_refs:
        return out
    for row, center in enumerate(refs):
        nearest = np.asarray(neighbor_idx[row], dtype=np.intp)
        neigh_src = refs[nearest]
        keep = neigh_src != int(center)
        neigh_src = neigh_src[keep]
        local = []
        for src in neigh_src:
            vec = increment_lookup.get(int(src))
            if vec is None or vec.shape != (dim,) or not np.isfinite(vec).all():
                continue
            local.append(vec)
        if len(local) < min_support:
            continue
        cov = np.atleast_2d(np.cov(np.asarray(local, dtype=float), rowvar=False, ddof=1))
        try:
            tensor, _ = psd_fn(cov, eigenvalue_floor=PSD_FLOOR)
        except (ValueError, np.linalg.LinAlgError):
            continue
        out[int(center)] = tensor
    return out


def _beta_s(tr2: float, tr8: float) -> float:
    if not (np.isfinite(tr2) and np.isfinite(tr8) and tr2 > EPS and tr8 > EPS):
        return float("nan")
    return float((np.log(tr8) - np.log(tr2)) / (np.log(8.0) - np.log(2.0)))


def _mode_medians(series: dict[str, np.ndarray], prefix: str, dt_step: float) -> dict[str, float]:
    out: dict[str, float] = {}
    traces: dict[int, float] = {}
    for h in HORIZONS:
        tr = series[f"{prefix}_tr_h{h}"]
        de = series[f"{prefix}_d_eff_h{h}"]
        ht = series[f"{prefix}_h_tilde_h{h}"]
        tr_med = float(np.nanmedian(tr)) if np.isfinite(tr).any() else float("nan")
        traces[h] = tr_med
        out[f"{prefix}_tr_h{h}"] = tr_med
        out[f"{prefix}_d_eff_h{h}"] = float(np.nanmedian(de)) if np.isfinite(de).any() else float("nan")
        out[f"{prefix}_h_tilde_h{h}"] = float(np.nanmedian(ht)) if np.isfinite(ht).any() else float("nan")
        denom = float(h) * float(dt_step) if np.isfinite(dt_step) and dt_step > 0 else float("nan")
        rate = series[f"{prefix}_rate_h{h}"]
        out[f"{prefix}_rate_h{h}"] = float(np.nanmedian(rate)) if np.isfinite(rate).any() else (
            float(tr_med / denom) if np.isfinite(tr_med) and np.isfinite(denom) and denom > 0 else float("nan")
        )
    out[f"{prefix}_beta_s"] = _beta_s(traces.get(2, float("nan")), traces.get(8, float("nan")))
    return out


def estimate_horizon_geometry(
    state: np.ndarray,
    time: np.ndarray,
    *,
    segment_id: np.ndarray | None = None,
    dt_fallback: float = 4.0,
) -> dict[str, Any]:
    """Empirical C_h for h in {2,4,8}. Common-support primary; max-support sensitivity."""
    ensure_mndm()
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
        "n_valid_cs": 0,
        "n_valid_ms": {h: 0 for h in HORIZONS},
        "n_source": {h: 0 for h in HORIZONS},
        "n_common": 0,
        "n_time": int(np.asarray(state).shape[0]) if np.asarray(state).ndim == 2 else 0,
        "nominal_dt_sec": float("nan"),
        "qualification": "empirical_finite_horizon_increment_geometry_not_diffusion",
    }
    if reason is not None or x is None or t is None or segments is None or finite_state is None:
        return empty
    n_time = int(x.shape[0])
    min_support = max(MIN_NEIGH, 3 * x.shape[1] + 1)
    pairs: dict[int, Any] = {}
    lookups: dict[int, dict[int, np.ndarray]] = {}
    source_sets: dict[int, set[int]] = {}
    dt_step = float("nan")
    for h in HORIZONS:
        support = build_transition_support(
            x, t, segments, lag=int(h), max_gap_sec=None, max_dt_relative_deviation=MAX_DT_REL
        )
        src = np.asarray(support.source_idx, dtype=np.int32)
        dx = np.asarray(support.increments, dtype=float)
        pairs[h] = support
        lookups[h] = _increment_map(src, dx)
        source_sets[h] = {int(v) for v in src}
        empty["n_source"][h] = int(src.size)
        if h == 2 and np.isfinite(support.nominal_dt_sec) and support.nominal_dt_sec > 0:
            dt_step = float(support.nominal_dt_sec) / 2.0
    if not np.isfinite(dt_step) or dt_step <= 0:
        dt_step = float(dt_fallback)
    empty["n_time"] = n_time
    empty["nominal_dt_sec"] = dt_step
    for h in HORIZONS:
        if pairs[h].failure_reason in {"non_positive_nominal_dt", "materially_irregular_increment_timestep"}:
            empty["failure_reason"] = f"h{h}_{pairs[h].failure_reason}"
            return empty
        if int(pairs[h].source_idx.size) < min_support or int(K) >= int(pairs[h].source_idx.size):
            empty["failure_reason"] = f"h{h}_insufficient_valid_increment_pairs"
            return empty
    common = source_sets[2] & source_sets[4] & source_sets[8]
    common_idx = np.asarray(sorted(common), dtype=np.int32)
    empty["n_common"] = int(common_idx.size)
    series = {key: np.full(n_time, np.nan, dtype=float) for key in MEDIAN_KEYS if not key.endswith("beta_s")}
    n_valid_cs = 0
    n_valid_ms = {h: 0 for h in HORIZONS}

    if common_idx.size >= min_support and int(K) < int(common_idx.size):
        k_use = min(int(K), int(common_idx.size))
        neighbor_idx, _ = chunked_nearest_neighbors(x[common_idx], x[common_idx], k_use)
        tensors = {}
        for h in HORIZONS:
            tensors[h] = _fill_horizon_covariance(
                x,
                common_idx,
                lookups[h],
                min_support=min_support,
                knn_fn=chunked_nearest_neighbors,
                psd_fn=project_to_psd,
                neighbor_idx=neighbor_idx,
            )
        for center in common_idx:
            geos = {h: _geometry_scalars(tensors[h][int(center)]) for h in HORIZONS}
            if all(np.isfinite(geos[h]["tr"]) for h in HORIZONS):
                n_valid_cs += 1
            i = int(center)
            for h in HORIZONS:
                series[f"cs_tr_h{h}"][i] = geos[h]["tr"]
                series[f"cs_d_eff_h{h}"][i] = geos[h]["d_eff"]
                series[f"cs_h_tilde_h{h}"][i] = geos[h]["h_tilde"]
                denom = float(h) * dt_step
                tr = geos[h]["tr"]
                series[f"cs_rate_h{h}"][i] = float(tr / denom) if np.isfinite(tr) and denom > 0 else float("nan")

    for h in HORIZONS:
        src = np.asarray(pairs[h].source_idx, dtype=np.int32)
        tensors_h = _fill_horizon_covariance(
            x,
            src,
            lookups[h],
            min_support=min_support,
            knn_fn=chunked_nearest_neighbors,
            psd_fn=project_to_psd,
            neighbor_idx=None,
        )
        for center in src:
            geo = _geometry_scalars(tensors_h[int(center)])
            if np.isfinite(geo["tr"]):
                n_valid_ms[h] += 1
            i = int(center)
            series[f"ms_tr_h{h}"][i] = geo["tr"]
            series[f"ms_d_eff_h{h}"][i] = geo["d_eff"]
            series[f"ms_h_tilde_h{h}"][i] = geo["h_tilde"]
            denom = float(h) * dt_step
            series[f"ms_rate_h{h}"][i] = float(geo["tr"] / denom) if np.isfinite(geo["tr"]) and denom > 0 else float("nan")

    min_cov = max(1, int(np.ceil(MIN_VALID_FRAC * n_time)))
    cs_ok = n_valid_cs >= min_cov
    ms_ok = any(n_valid_ms[h] >= min_cov for h in HORIZONS)
    if not cs_ok and not ms_ok:
        empty["failure_reason"] = "insufficient_horizon_coverage"
        empty["n_valid_cs"] = n_valid_cs
        empty["n_valid_ms"] = n_valid_ms
        return empty
    medians = _nan_medians()
    if cs_ok:
        medians.update(_mode_medians(series, "cs", dt_step))
    medians.update(_mode_medians(series, "ms", dt_step))
    return {
        "status": "computed" if cs_ok else "computed_max_support_only",
        "failure_reason": None if cs_ok else "insufficient_common_support_coverage",
        "series": series,
        "medians": medians,
        "n_valid_cs": int(n_valid_cs),
        "n_valid_ms": {int(h): int(n_valid_ms[h]) for h in HORIZONS},
        "n_source": {int(h): int(empty["n_source"][h]) for h in HORIZONS},
        "n_common": int(common_idx.size),
        "n_time": n_time,
        "nominal_dt_sec": dt_step,
        "qualification": "empirical_finite_horizon_increment_geometry_not_diffusion",
    }
