from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.spatial.distance import cdist
from sklearn.covariance import LedoitWolf, OAS
from sklearn.linear_model import Ridge, RidgeCV


def build_knn_neighborhoods(x: np.ndarray, k: int = 20) -> np.ndarray:
    t = x.shape[0]
    k = min(max(1, int(k)), t)
    if t < 2:
        return np.zeros((t, k), dtype=np.int32)
    valid_mask = ~np.isnan(x).any(axis=1)
    valid_indices = np.where(valid_mask)[0]
    if valid_indices.size == 0:
        return np.zeros((t, k), dtype=np.int32)
    x_valid = x[valid_mask]
    distances = cdist(x_valid, x_valid, metric="euclidean")
    nn_indices = np.zeros((t, k), dtype=np.int32)
    for i in range(t):
        if valid_mask[i]:
            v_idx = np.where(valid_indices == i)[0][0]
            nearest = np.argsort(distances[v_idx])[:k]
            nn_indices[i] = valid_indices[nearest]
        else:
            nn_indices[i] = valid_indices[:k] if valid_indices.size >= k else np.pad(
                valid_indices, (0, k - valid_indices.size), constant_values=valid_indices[0]
            )
    return nn_indices


def build_knn_neighborhoods_grouped(x: np.ndarray, group_ids: np.ndarray, k: int = 20) -> np.ndarray:
    if x.shape[0] != len(group_ids):
        raise ValueError("group_ids length must match x rows")
    nn_indices = np.zeros((x.shape[0], min(max(1, int(k)), x.shape[0])), dtype=np.int32)
    for gid in np.unique(group_ids):
        idx = np.where(group_ids == gid)[0]
        if idx.size == 0:
            continue
        local = build_knn_neighborhoods(x[idx], k=k)
        nn_indices[idx] = idx[local]
    return nn_indices


def form_super_windows(window_indices: List[int], n_windows: int = 3) -> List[List[int]]:
    if len(window_indices) < n_windows:
        return [window_indices] if window_indices else []
    return [window_indices[i : i + n_windows] for i in range(len(window_indices) - n_windows + 1)]


def _fit_covariance(residuals: np.ndarray, cov_estimator: str = "empirical") -> Tuple[np.ndarray, float]:
    dim = residuals.shape[1]
    if residuals.shape[0] < 2:
        return np.eye(dim), float("nan")
    cov = None
    shrinkage = float("nan")
    estimator = (cov_estimator or "empirical").lower().strip()
    if estimator in {"oas", "ledoit_wolf"}:
        try:
            model = OAS().fit(residuals) if estimator == "oas" else LedoitWolf().fit(residuals)
            cov = model.covariance_
            shrinkage = float(getattr(model, "shrinkage_", float("nan")))
        except Exception:
            cov = None
    if cov is None:
        cov = np.cov(residuals, rowvar=False)
    if np.ndim(cov) == 0:
        cov = np.eye(dim) * float(cov)
    return cov, shrinkage


def estimate_local_linear_model(
    x: np.ndarray,
    nn_indices: Optional[np.ndarray] = None,
    super_window_indices: Optional[List[List[int]]] = None,
    method: str = "ridge",
    alpha_grid: Optional[List[float]] = None,
    cv_folds: int = 5,
    fit_intercept: bool = True,
    cov_estimator: str = "empirical",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
    if alpha_grid is None:
        alpha_grid = [1e-4, 1e-3, 1e-2, 1e-1]
    t, dim = x.shape
    max_idx = max(0, t - 2)
    if super_window_indices is None:
        windows = list(range(t - 1))
        super_window_indices = [[i] for i in windows]

    w_count = len(super_window_indices)
    A_hat = np.full((w_count, dim, dim), np.nan, dtype=float)
    b_hat = np.full((w_count, dim), np.nan, dtype=float)
    Q_hat = np.full((w_count, dim, dim), np.nan, dtype=float)
    alpha_used = np.full(w_count, np.nan, dtype=float)
    n_samples = np.zeros(w_count, dtype=int)
    r2_scores = np.full(w_count, np.nan, dtype=float)
    shrinkage_used = np.full(w_count, np.nan, dtype=float)

    for w_idx, group in enumerate(super_window_indices):
        candidates: List[int] = []
        for win_idx in group:
            if nn_indices is not None and win_idx < nn_indices.shape[0]:
                candidates.extend(nn_indices[win_idx].tolist())
            else:
                candidates.append(win_idx)
        candidates = np.unique(candidates)
        candidates = candidates[candidates <= max_idx]
        if len(candidates) < dim + 1:
            n_samples[w_idx] = len(candidates)
            continue
        X = x[candidates]
        Y = x[candidates + 1]
        valid = ~(np.isnan(X).any(axis=1) | np.isnan(Y).any(axis=1))
        X = X[valid]
        Y = Y[valid]
        if X.shape[0] < dim + 1:
            n_samples[w_idx] = X.shape[0]
            continue
        n_samples[w_idx] = X.shape[0]
        if method != "ridge":
            method = "ridge"
        if X.shape[0] >= cv_folds:
            model = RidgeCV(alphas=alpha_grid, cv=min(cv_folds, X.shape[0]), fit_intercept=fit_intercept)
        else:
            model = Ridge(alpha=alpha_grid[0], fit_intercept=fit_intercept)
        model.fit(X, Y)
        coef = model.coef_
        intercept = model.intercept_
        if coef.ndim == 1:
            coef = coef[None, :]
        A_hat[w_idx] = coef
        b_hat[w_idx] = np.full(dim, float(intercept)) if np.ndim(intercept) == 0 else intercept
        alpha_used[w_idx] = float(getattr(model, "alpha_", alpha_grid[0]))
        Y_hat = X @ coef.T + b_hat[w_idx]
        residuals = Y - Y_hat
        cov, shrinkage = _fit_covariance(residuals, cov_estimator=cov_estimator)
        Q_hat[w_idx] = cov + np.eye(dim) * 1e-8
        shrinkage_used[w_idx] = shrinkage
        ss_res = np.sum((Y - Y_hat) ** 2)
        ss_tot = np.sum((Y - np.mean(Y, axis=0)) ** 2)
        r2_scores[w_idx] = 1.0 - (ss_res / (ss_tot + 1e-10))

    meta = {
        "alpha_used": alpha_used,
        "n_samples": n_samples,
        "r2_score": r2_scores,
        "method": np.array([method] * w_count, dtype=object),
        "shrinkage_used": shrinkage_used,
    }
    return A_hat, b_hat, Q_hat, meta


def propagate_reachability_covariance(A: np.ndarray, Q: np.ndarray, horizon: int, sigma0: float, jitter: float) -> np.ndarray:
    dim = A.shape[0]
    sigmas = np.zeros((horizon + 1, dim, dim), dtype=float)
    sigmas[0] = np.eye(dim) * (sigma0**2)
    for h in range(horizon):
        sigma_next = A @ sigmas[h] @ A.T + Q
        sigma_next = sigma_next + np.eye(dim) * jitter
        sigmas[h + 1] = sigma_next
    return sigmas


def compute_reachability_metrics(sigmas: np.ndarray, A: np.ndarray, eps: float, jitter: float, eig_floor_scale: float = 0.0) -> Dict[str, np.ndarray]:
    horizons = sigmas.shape[0] - 1
    log_det = np.full(horizons, np.nan, dtype=float)
    kappa = np.full(horizons, np.nan, dtype=float)
    log_eig_var = np.full(horizons, np.nan, dtype=float)
    d_eff = np.full(horizons, np.nan, dtype=float)
    dir_entropy = np.full(horizons, np.nan, dtype=float)
    dir_entropy_norm = np.full(horizons, np.nan, dtype=float)
    for h in range(1, horizons + 1):
        sigma_h = sigmas[h]
        if not np.isfinite(sigma_h).all():
            continue
        sign, ld = np.linalg.slogdet(sigma_h + np.eye(sigma_h.shape[0]) * eps)
        log_det[h - 1] = np.nan if sign <= 0 else 0.5 * ld
        eigvals = np.linalg.eigvalsh(sigma_h)
        eigvals = np.clip(np.sort(eigvals)[::-1], eps, np.inf)
        kappa[h - 1] = eigvals[0] / (eigvals[-1] + eps)
        log_eig_var[h - 1] = np.var(np.log(eigvals + eps))
        eigvals_deff = np.clip(eigvals, max(eps, float(eig_floor_scale) * float(jitter)), np.inf) if eig_floor_scale and eig_floor_scale > 0 else eigvals
        denom = np.sum(eigvals_deff**2) + eps
        d_eff[h - 1] = (np.sum(eigvals_deff) ** 2) / denom
        p = eigvals / (np.sum(eigvals) + eps)
        ent = -float(np.sum(p * np.log(p + eps)))
        dir_entropy[h - 1] = ent
        dir_entropy_norm[h - 1] = ent / (np.log(float(len(eigvals))) + eps)
    try:
        W, _, Vt = np.linalg.svd(A)
        U = W @ Vt
        rotation = np.linalg.norm((U - U.T) / 2.0, ord="fro")
    except Exception:
        rotation = np.nan
    return {
        "log_det": log_det,
        "kappa": kappa,
        "log_eig_var": log_eig_var,
        "d_eff": d_eff,
        "dir_entropy": dir_entropy,
        "dir_entropy_norm": dir_entropy_norm,
        "rotation": rotation,
    }


def compute_q_ratio_series(sigmas: np.ndarray, A: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    horizons = sigmas.shape[0] - 1
    q_ratio = np.full(horizons, np.nan, dtype=float)
    for h in range(1, horizons + 1):
        sigma_prev = sigmas[h - 1]
        sigma_now = sigmas[h]
        if not np.isfinite(sigma_prev).all() or not np.isfinite(sigma_now).all() or not np.isfinite(A).all():
            continue
        transport = A @ sigma_prev @ A.T
        innovation = sigma_now - transport
        tr_transport = float(np.trace(transport))
        tr_innovation = float(np.trace(innovation))
        denom = tr_transport + tr_innovation
        if np.isfinite(denom) and denom > float(eps):
            q_ratio[h - 1] = float(tr_innovation / denom)
    return q_ratio


def compute_operator_norm(A: np.ndarray) -> float:
    try:
        return float(np.linalg.norm(A, ord=2))
    except Exception:
        return float("nan")


def aggregate_metrics(metrics: Dict[str, np.ndarray], agg: str = "median") -> Dict[str, float]:
    agg_fn = np.nanmedian if agg == "median" else np.nanmean
    out: Dict[str, float] = {}
    for key, values in metrics.items():
        out[f"tube_{key}"] = float(values) if key == "rotation" else float(agg_fn(values))
    return out


def compute_persistence(series: np.ndarray, window: int, eps: float) -> np.ndarray:
    n = len(series)
    if n == 0:
        return series
    window = max(3, int(window))
    if window % 2 == 0:
        window += 1
    half = window // 2
    out = np.full(n, np.nan, dtype=float)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        seg = series[lo:hi]
        seg = seg[np.isfinite(seg)]
        if seg.size < 2:
            continue
        out[i] = 1.0 / (np.nanstd(seg) + eps)
    return out


def compute_return_time(series: np.ndarray, baseline_quantile: float, low_alpha: float, recover_alpha: float, time: Optional[np.ndarray] = None) -> np.ndarray:
    series = np.asarray(series, dtype=float)
    n = series.size
    if n == 0:
        return series
    base = np.nanquantile(series, baseline_quantile)
    if not np.isfinite(base):
        return np.full(n, np.nan, dtype=float)
    low_thr = low_alpha * base
    rec_thr = recover_alpha * base
    out = np.full(n, np.nan, dtype=float)
    tvec = np.asarray(time, dtype=float) if time is not None and len(time) >= n else None
    for i in range(n):
        val = series[i]
        if not np.isfinite(val) or val >= low_thr:
            continue
        hit = np.where(series[i + 1 :] >= rec_thr)[0]
        if hit.size == 0:
            continue
        j = i + 1 + int(hit[0])
        out[i] = float(tvec[j] - tvec[i]) if tvec is not None else float(j - i)
    return out


def compute_hysteresis(series: np.ndarray, window: int, time: Optional[np.ndarray] = None) -> np.ndarray:
    series = np.asarray(series, dtype=float)
    n = series.size
    if n == 0:
        return series
    window = max(3, int(window))
    if window % 2 == 0:
        window += 1
    half = window // 2
    dif = np.diff(series, prepend=series[0])
    down_mask = dif < 0
    up_mask = dif > 0
    down = np.full(n, np.nan, dtype=float)
    up = np.full(n, np.nan, dtype=float)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        seg = series[lo:hi]
        dseg = seg[down_mask[lo:hi]]
        useg = seg[up_mask[lo:hi]]
        if dseg.size:
            down[i] = float(np.nanmedian(dseg))
        if useg.size:
            up[i] = float(np.nanmedian(useg))
    gap = np.abs(down - up)
    if time is None or len(time) < n:
        return gap
    dt = np.gradient(np.asarray(time[:n], dtype=float))
    return gap * dt


def compute_cone_kappa(log_det_series: np.ndarray) -> np.ndarray:
    series = np.asarray(log_det_series, dtype=float)
    n = series.size
    out = np.full(n, np.nan, dtype=float)
    if n < 2:
        return out
    for i in range(1, n):
        a, b = series[i - 1], series[i]
        if np.isfinite(a) and np.isfinite(b):
            out[i] = float(np.exp(b - a))
    return out


def _prediction_errors_from_dynamics(x: np.ndarray, centers: np.ndarray, A_hat: np.ndarray, b_hat: np.ndarray, horizon: int) -> Dict[str, float]:
    n = int(x.shape[0])
    errors: Dict[int, List[float]] = {h: [] for h in range(1, int(horizon) + 1)}
    for w, t_raw in enumerate(np.asarray(centers)):
        try:
            t = int(t_raw)
        except Exception:
            continue
        if t < 0 or t >= n - 1:
            continue
        A = A_hat[w]
        b = b_hat[w]
        if not np.isfinite(A).all() or not np.isfinite(b).all():
            continue
        x_pred = x[t].copy()
        for h in range(1, int(horizon) + 1):
            idx = t + h
            if idx >= n:
                break
            x_pred = A @ x_pred + b
            err = np.linalg.norm(x[idx] - x_pred)
            if np.isfinite(err):
                errors[h].append(float(err))
    return {f"pred_err_h{h}": float(np.median(vals)) if vals else float("nan") for h, vals in errors.items()}


def _split_half_summary(series: np.ndarray) -> Dict[str, float]:
    vals = np.asarray(series, dtype=float)
    n = int(vals.size)
    if n < 4:
        return {"split_half_a_median": np.nan, "split_half_b_median": np.nan, "split_half_rho": np.nan, "split_half_n": 0.0}
    mid = n // 2
    a = vals[:mid]
    b = vals[mid : mid + mid]
    a_med = float(np.nanmedian(a)) if a.size else float("nan")
    b_med = float(np.nanmedian(b)) if b.size else float("nan")
    mask = np.isfinite(a) & np.isfinite(b)
    n_eff = int(mask.sum())
    if n_eff < 3:
        rho = float("nan")
    else:
        ra = np.argsort(np.argsort(a[mask])).astype(float)
        rb = np.argsort(np.argsort(b[mask])).astype(float)
        rho = float(np.corrcoef(ra, rb)[0, 1]) if np.std(ra) > 0 and np.std(rb) > 0 else float("nan")
    return {"split_half_a_median": a_med, "split_half_b_median": b_med, "split_half_rho": rho, "split_half_n": float(n_eff)}


def _near_singular_rate(sigmas: np.ndarray, jitter: float, threshold_scale: float = 10.0) -> float:
    if sigmas.ndim != 4:
        return float("nan")
    W, H, _, _ = sigmas.shape
    thresh = float(jitter) * float(threshold_scale)
    total = 0
    bad = 0
    for w in range(W):
        for h in range(1, H):
            S = sigmas[w, h]
            total += 1
            if not np.isfinite(S).all():
                bad += 1
                continue
            eigvals = np.linalg.eigvalsh(S)
            if eigvals.size == 0 or np.nanmin(eigvals) <= thresh:
                bad += 1
    return float(bad / total) if total else float("nan")


def _numerics_health(sigmas: np.ndarray, eps: float) -> Dict[str, float]:
    cond_vals: List[float] = []
    min_over_med_vals: List[float] = []
    if sigmas.ndim != 4:
        return {"median_cond": float("nan"), "median_min_eig_over_median_eig": float("nan")}
    W, H, _, _ = sigmas.shape
    for w in range(W):
        for h in range(1, H):
            S = sigmas[w, h]
            if not np.isfinite(S).all():
                continue
            eigvals = np.linalg.eigvalsh(S)
            if eigvals.size == 0:
                continue
            min_eig = float(np.nanmin(eigvals))
            med_eig = float(np.nanmedian(eigvals))
            max_eig = float(np.nanmax(eigvals))
            cond_vals.append(float(max_eig / max(min_eig, float(eps))))
            min_over_med_vals.append(float(min_eig / max(med_eig, float(eps))))
    return {
        "median_cond": float(np.nanmedian(cond_vals)) if cond_vals else float("nan"),
        "median_min_eig_over_median_eig": float(np.nanmedian(min_over_med_vals)) if min_over_med_vals else float("nan"),
    }


def compute_reachability_cones_from_mnps(
    x: np.ndarray,
    time: np.ndarray,
    k: int = 20,
    super_window_size: int = 3,
    method: str = "ridge",
    alpha_grid: Optional[List[float]] = None,
    cv_folds: int = 5,
    horizon: int = 3,
    sigma0: float = 1e-3,
    jitter: float = 1e-8,
    agg: str = "median",
    cov_estimator: str = "empirical",
    eig_floor_scale: float = 0.0,
    persistence_window: int = 11,
    persistence_mode: str = "stability",
    persistence_baseline_quantile: float = 0.5,
    persistence_low_alpha: float = 0.8,
    persistence_recover_alpha: float = 0.9,
    persistence_hysteresis_window: int = 11,
    eps: float = 1e-10,
    knn_groups: Optional[np.ndarray] = None,
    knn_scope: str = "all",
    nn_indices_override: Optional[np.ndarray] = None,
) -> Dict[str, np.ndarray]:
    T = len(x)
    if T < 2:
        raise ValueError("Need at least 2 timepoints to estimate reachability.")
    if nn_indices_override is not None:
        nn_indices = np.asarray(nn_indices_override)
        nn_source = "override"
    elif knn_groups is not None and knn_scope != "all":
        nn_indices = build_knn_neighborhoods_grouped(x, knn_groups, k=k)
        nn_source = "grouped"
    else:
        nn_indices = build_knn_neighborhoods(x, k=k)
        nn_source = "computed"

    windows = list(range(T - 1))
    super_windows = form_super_windows(windows, n_windows=super_window_size)
    A_hat, b_hat, Q_hat, model_meta = estimate_local_linear_model(
        x,
        nn_indices=nn_indices,
        super_window_indices=super_windows,
        method=method,
        alpha_grid=alpha_grid,
        cv_folds=cv_folds,
        cov_estimator=cov_estimator,
    )
    W = A_hat.shape[0]
    sigmas = np.full((W, horizon + 1, x.shape[1], x.shape[1]), np.nan, dtype=float)
    metrics_by_h = {
        "log_det": np.full((W, horizon), np.nan, dtype=float),
        "kappa": np.full((W, horizon), np.nan, dtype=float),
        "log_eig_var": np.full((W, horizon), np.nan, dtype=float),
        "d_eff": np.full((W, horizon), np.nan, dtype=float),
        "dir_entropy": np.full((W, horizon), np.nan, dtype=float),
        "dir_entropy_norm": np.full((W, horizon), np.nan, dtype=float),
        "q_ratio": np.full((W, horizon), np.nan, dtype=float),
        "rotation": np.full(W, np.nan, dtype=float),
    }
    tube_metrics = {
        "tube_log_det": np.full(W, np.nan, dtype=float),
        "tube_kappa": np.full(W, np.nan, dtype=float),
        "tube_log_eig_var": np.full(W, np.nan, dtype=float),
        "tube_d_eff": np.full(W, np.nan, dtype=float),
        "tube_dir_entropy": np.full(W, np.nan, dtype=float),
        "tube_dir_entropy_norm": np.full(W, np.nan, dtype=float),
        "tube_rotation": np.full(W, np.nan, dtype=float),
        "tube_q_ratio_h4": np.full(W, np.nan, dtype=float),
        "tube_a_operator_norm": np.full(W, np.nan, dtype=float),
        "tube_capture_gate": np.full(W, np.nan, dtype=float),
    }
    for w in range(W):
        A = A_hat[w]
        Q = Q_hat[w]
        if not np.isfinite(A).all() or not np.isfinite(Q).all():
            continue
        sigmas[w] = propagate_reachability_covariance(A, Q, horizon, sigma0, jitter)
        metrics = compute_reachability_metrics(sigmas[w], A, eps=eps, jitter=jitter, eig_floor_scale=eig_floor_scale)
        metrics["q_ratio"] = compute_q_ratio_series(sigmas[w], A, eps=eps)
        for key in ("log_det", "kappa", "log_eig_var", "d_eff", "dir_entropy", "dir_entropy_norm", "q_ratio"):
            metrics_by_h[key][w] = metrics[key]
        metrics_by_h["rotation"][w] = metrics["rotation"]
        tube = aggregate_metrics(metrics, agg=agg)
        q_ratio_h4 = float(metrics["q_ratio"][min(max(horizon, 1), 4) - 1]) if metrics["q_ratio"].size else float("nan")
        a_operator_norm = compute_operator_norm(A)
        tube["tube_q_ratio_h4"] = q_ratio_h4
        tube["tube_a_operator_norm"] = a_operator_norm
        tube["tube_capture_gate"] = (
            float((1.0 - q_ratio_h4) * np.log1p(a_operator_norm))
            if np.isfinite(q_ratio_h4) and np.isfinite(a_operator_norm)
            else float("nan")
        )
        for key in tube_metrics:
            tube_metrics[key][w] = tube[key]

    tube_metrics["cone_kappa"] = compute_cone_kappa(tube_metrics["tube_log_det"])
    persistence: Dict[str, np.ndarray] = {}
    if persistence_mode in {"stability", "all"}:
        persistence.update(
            {
                "persistence_log_det": compute_persistence(tube_metrics["tube_log_det"], persistence_window, eps),
                "persistence_kappa": compute_persistence(tube_metrics["tube_kappa"], persistence_window, eps),
                "persistence_log_eig_var": compute_persistence(tube_metrics["tube_log_eig_var"], persistence_window, eps),
                "persistence_d_eff": compute_persistence(tube_metrics["tube_d_eff"], persistence_window, eps),
            }
        )
    if persistence_mode in {"return_time", "all"}:
        time_w = time[:W] if len(time) >= W else None
        persistence.update(
            {
                "persistence_tau_log_det": compute_return_time(
                    tube_metrics["tube_log_det"], persistence_baseline_quantile, persistence_low_alpha, persistence_recover_alpha, time=time_w
                ),
                "persistence_tau_kappa": compute_return_time(
                    tube_metrics["tube_kappa"], persistence_baseline_quantile, persistence_low_alpha, persistence_recover_alpha, time=time_w
                ),
                "persistence_tau_log_eig_var": compute_return_time(
                    tube_metrics["tube_log_eig_var"], persistence_baseline_quantile, persistence_low_alpha, persistence_recover_alpha, time=time_w
                ),
                "persistence_tau_d_eff": compute_return_time(
                    tube_metrics["tube_d_eff"], persistence_baseline_quantile, persistence_low_alpha, persistence_recover_alpha, time=time_w
                ),
            }
        )
    if persistence_mode in {"hysteresis", "all"}:
        time_w = time[:W] if len(time) >= W else None
        persistence.update(
            {
                "persistence_hysteresis_log_det": compute_hysteresis(tube_metrics["tube_log_det"], persistence_hysteresis_window, time=time_w),
                "persistence_hysteresis_kappa": compute_hysteresis(tube_metrics["tube_kappa"], persistence_hysteresis_window, time=time_w),
                "persistence_hysteresis_log_eig_var": compute_hysteresis(
                    tube_metrics["tube_log_eig_var"], persistence_hysteresis_window, time=time_w
                ),
                "persistence_hysteresis_d_eff": compute_hysteresis(tube_metrics["tube_d_eff"], persistence_hysteresis_window, time=time_w),
            }
        )

    centers = np.zeros(len(super_windows), dtype=np.int32)
    for i, sw in enumerate(super_windows):
        centers[i] = int(min(sw[len(sw) // 2], T - 2)) if sw else 0

    validity: Dict[str, float] = {}
    validity.update(_prediction_errors_from_dynamics(x=x, centers=centers, A_hat=A_hat, b_hat=b_hat, horizon=horizon))
    validity["near_singular_rate"] = _near_singular_rate(sigmas=sigmas, jitter=jitter, threshold_scale=10.0)
    validity.update({f"tube_log_det_{k}": v for k, v in _split_half_summary(tube_metrics["tube_log_det"]).items()})
    validity.update({f"tube_d_eff_{k}": v for k, v in _split_half_summary(tube_metrics["tube_d_eff"]).items()})
    validity.update(_numerics_health(sigmas=sigmas, eps=eps))

    return {
        "time": time,
        "x": x,
        "A_hat": A_hat,
        "b_hat": b_hat,
        "Q_hat": Q_hat,
        "sigmas": sigmas,
        "metrics_by_h": metrics_by_h,
        "tube_metrics": tube_metrics,
        "persistence": persistence,
        "nn_indices": nn_indices,
        "super_window_indices": super_windows,
        "reachability_centers": centers,
        "model_metadata": model_meta,
        "horizon": horizon,
        "nn_indices_source": nn_source,
        "validity": validity,
    }
