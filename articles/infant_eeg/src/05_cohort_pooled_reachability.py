"""Cohort-pooled reachability: local flow-field estimates from cross-child neighbors.

Design (see peer_review/pr_01.md, "Explicit answer" section):
    The per-visit MNJ/reachability summaries in `01_export_session_metrics.py` are
    estimated purely from a *single session's own epochs* (k-NN restricted to that
    session's trajectory). This script asks a different, genuinely cohort-level
    question: at each visit's own cohort-anchored 3D coordinate position, what does
    the *local flow field pooled across the rest of the cohort* look like?

    For each visit v of child c:
      1. The query point is v's own median cohort-anchored 3D coordinate (the same
         point already reported as cohort_m/d/e_median in session_metrics.csv).
      2. The neighbor pool is every valid (epoch_t -> epoch_t+1) transition pair from
         every OTHER child's epochs (leave-one-child-out: all of child c's own visits
         are excluded, not just visit v, so the estimate cannot fall back on child c's
         own trajectory smoothness).
      3. The k=12 nearest pool transitions (by Euclidean distance from the query point
         to each pair's source epoch) are used to fit a local ridge linear model
         (A_hat, b_hat) and residual covariance (Q_hat), exactly as in
         `ndt_analysis.reachability_core.estimate_local_linear_model`, then propagated
         and summarized with the same `propagate_reachability_covariance`,
         `compute_reachability_metrics`, and `aggregate_metrics` primitives used by the
         per-session pipeline, so the two estimates are numerically comparable.

    This directly tests whether the shared cohort flow field's local reachability
    covaries with the age-associated coordinate trajectory identified by the primary
    cohort-coordinate GEE (manuscript R2), independent of both that GEE and of the
    per-session within-child robustness check (manuscript R4 / Supplement S2).

Known limitation (documented, not hidden): cohort density is uneven across the chart
(younger vs. older infants are not equally represented), so the same k gives a
different effective neighborhood radius at different ages. The per-visit neighbor
radius (`neighbor_k_distance`) is reported explicitly as a QC diagnostic for this.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.linear_model import Ridge

from figshare_infant_support import (
    DEFAULT_DATA_ROOT,
    DEFAULT_RESULTS_ROOT,
    COORDINATE_CONTRACT,
    bh_fdr,
    h5_paths,
    participant_metadata,
    session_identity,
    within_child_age_associations,
)
from ndt_analysis.h5_contract import read_geometry_contract_state, resolve_coords_3d
from ndt_analysis.reachability_core import (
    _fit_covariance,
    aggregate_metrics,
    compute_operator_norm,
    compute_reachability_metrics,
    propagate_reachability_covariance,
)

K_NEIGHBORS = 12
HORIZON = 3
RIDGE_ALPHA = 1e-3
SIGMA0 = 0.0
JITTER = 1e-6
EPS = 1e-12
DIMS = 3
COHORT_POOLED_ENDPOINTS = (
    "cohort_pooled_tube_log_det",
    "cohort_pooled_tube_d_eff",
    "cohort_pooled_tube_kappa",
    "cohort_pooled_tube_dir_entropy",
    "cohort_pooled_tube_rotation",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--session-metrics", type=Path, default=DEFAULT_RESULTS_ROOT / "01_session_metrics" / "session_metrics.csv")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_ROOT / "05_cohort_pooled_reachability")
    parser.add_argument("--k-neighbors", type=int, default=K_NEIGHBORS)
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    parser.add_argument("--n-permutation", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_pool(paths: list[Path]) -> pd.DataFrame:
    """One row per valid (epoch_t -> epoch_t+1) transition, tagged by subject/visit."""
    rows = []
    for h5_path in paths:
        with h5py.File(h5_path, "r") as handle:
            participant = participant_metadata(handle)
            identity = session_identity(h5_path, participant)
            contract = read_geometry_contract_state(handle)
            if contract.status not in ("ok", "adjusted"):
                continue
            coords = resolve_coords_3d(handle, COORDINATE_CONTRACT)
            if coords is None or coords.values.shape[0] < 2:
                continue
            values = np.asarray(coords.values, dtype=float)
        finite = np.isfinite(values).all(axis=1)
        for t in range(values.shape[0] - 1):
            if not (finite[t] and finite[t + 1]):
                continue
            rows.append({
                "subject_id": identity["subject_id"],
                "visit": identity["visit"],
                "epoch_index": t,
                "source_m": values[t, 0], "source_d": values[t, 1], "source_e": values[t, 2],
                "target_m": values[t + 1, 0], "target_d": values[t + 1, 1], "target_e": values[t + 1, 2],
            })
    return pd.DataFrame(rows)


def fit_local_model(query: np.ndarray, source: np.ndarray, target: np.ndarray, k: int) -> dict:
    if source.shape[0] < k:
        return {"not_testable": True, "not_testable_reason": f"pool_smaller_than_k:{source.shape[0]}<{k}"}
    distances = cdist(query[None, :], source, metric="euclidean")[0]
    order = np.argsort(distances)[:k]
    neighbor_distance_max = float(distances[order].max())
    neighbor_distance_median = float(np.median(distances[order]))
    X = source[order]
    Y = target[order]
    model = Ridge(alpha=RIDGE_ALPHA, fit_intercept=True)
    model.fit(X, Y)
    A_hat = np.atleast_2d(model.coef_)
    b_hat = model.intercept_ if np.ndim(model.intercept_) else np.full(DIMS, float(model.intercept_))
    Y_hat = X @ A_hat.T + b_hat
    residuals = Y - Y_hat
    cov, _ = _fit_covariance(residuals, cov_estimator="empirical")
    Q_hat = cov + np.eye(DIMS) * 1e-8
    ss_res = float(np.sum((Y - Y_hat) ** 2))
    ss_tot = float(np.sum((Y - Y.mean(axis=0)) ** 2))
    r2 = 1.0 - ss_res / (ss_tot + 1e-10)
    if not (np.isfinite(A_hat).all() and np.isfinite(Q_hat).all()):
        return {"not_testable": True, "not_testable_reason": "non_finite_local_model"}
    sigmas = propagate_reachability_covariance(A_hat, Q_hat, horizon=HORIZON, sigma0=SIGMA0, jitter=JITTER)
    metrics = compute_reachability_metrics(sigmas, A_hat, eps=EPS, jitter=JITTER, eig_floor_scale=0.0)
    tube = aggregate_metrics(metrics, agg="median")
    return {
        "not_testable": False,
        "not_testable_reason": None,
        "cohort_pooled_tube_log_det": tube["tube_log_det"],
        "cohort_pooled_tube_kappa": tube["tube_kappa"],
        "cohort_pooled_tube_log_eig_var": tube["tube_log_eig_var"],
        "cohort_pooled_tube_d_eff": tube["tube_d_eff"],
        "cohort_pooled_tube_dir_entropy": tube["tube_dir_entropy"],
        "cohort_pooled_tube_dir_entropy_norm": tube["tube_dir_entropy_norm"],
        "cohort_pooled_tube_rotation": tube["tube_rotation"],
        "cohort_pooled_a_operator_norm": compute_operator_norm(A_hat),
        "cohort_pooled_ridge_r2": r2,
        "neighbor_k_used": k,
        "neighbor_pool_size_available": int(source.shape[0]),
        "neighbor_k_distance_max": neighbor_distance_max,
        "neighbor_k_distance_median": neighbor_distance_median,
    }


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    paths = h5_paths(args.data_root)
    pool = load_pool(paths)
    session_metrics = pd.read_csv(args.session_metrics)
    session_metrics = session_metrics[session_metrics.geometry_contract_status.isin(("ok", "adjusted"))].copy()

    source_all = pool[["source_m", "source_d", "source_e"]].to_numpy()
    target_all = pool[["target_m", "target_d", "target_e"]].to_numpy()
    subject_all = pool.subject_id.to_numpy()

    rows = []
    for _, visit_row in session_metrics.iterrows():
        query = np.array([visit_row["cohort_m_median"], visit_row["cohort_d_median"], visit_row["cohort_e_median"]], dtype=float)
        exclude = subject_all == visit_row["subject_id"]
        fit = fit_local_model(query, source_all[~exclude], target_all[~exclude], k=args.k_neighbors)
        n_distinct_neighbor_children = np.nan
        if not fit.get("not_testable", True):
            distances = cdist(query[None, :], source_all[~exclude], metric="euclidean")[0]
            order = np.argsort(distances)[: args.k_neighbors]
            n_distinct_neighbor_children = int(pd.unique(subject_all[~exclude][order]).size)
        rows.append({
            "subject_id": visit_row["subject_id"],
            "visit": visit_row["visit"],
            "age_days": visit_row["age_days"],
            "age_source": visit_row.get("age_source"),
            "query_cohort_m": query[0], "query_cohort_d": query[1], "query_cohort_e": query[2],
            "n_distinct_neighbor_children": n_distinct_neighbor_children,
            **fit,
        })
    per_visit = pd.DataFrame(rows).sort_values(["subject_id", "visit"])
    per_visit.to_csv(args.output_dir / "cohort_pooled_reachability_per_visit.csv", index=False)

    testable = per_visit[~per_visit.not_testable].copy()
    primary = within_child_age_associations(
        testable, COHORT_POOLED_ENDPOINTS, "cohort_pooled_reachability_within_child",
        n_bootstrap=args.n_bootstrap, n_permutation=args.n_permutation, seed=args.seed,
    )
    direct_age = within_child_age_associations(
        testable, COHORT_POOLED_ENDPOINTS, "cohort_pooled_reachability_direct_age_sensitivity",
        n_bootstrap=args.n_bootstrap, n_permutation=args.n_permutation, seed=args.seed, direct_age_only=True,
    )
    primary.to_csv(args.output_dir / "cohort_pooled_reachability_age_associations.csv", index=False)
    direct_age.to_csv(args.output_dir / "cohort_pooled_reachability_direct_age_sensitivity.csv", index=False)

    manifest = {
        "coordinate_contract": COORDINATE_CONTRACT,
        "space": "3d",
        "k_neighbors": args.k_neighbors,
        "horizon": HORIZON,
        "ridge_alpha": RIDGE_ALPHA,
        "sigma0": SIGMA0,
        "jitter": JITTER,
        "leakage_control": "leave_one_child_out (all visits of the query's own child excluded from the neighbor pool)",
        "n_pool_transitions_total": int(len(pool)),
        "n_visits_total": int(len(per_visit)),
        "n_visits_testable": int(len(testable)),
        "n_visits_not_testable": int(per_visit.not_testable.sum()),
        "median_neighbor_k_distance": float(testable.neighbor_k_distance_max.median()) if not testable.empty else np.nan,
        "median_n_distinct_neighbor_children": float(testable.n_distinct_neighbor_children.median()) if not testable.empty else np.nan,
        "endpoints": list(COHORT_POOLED_ENDPOINTS),
        "per_visit_output": "cohort_pooled_reachability_per_visit.csv",
        "age_associations_output": "cohort_pooled_reachability_age_associations.csv",
        "direct_age_sensitivity_output": "cohort_pooled_reachability_direct_age_sensitivity.csv",
    }
    (args.output_dir / "cohort_pooled_reachability_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
