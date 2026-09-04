"""Cohort-anchored, child-clustered spline age models for coordinate positions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from figshare_infant_support import (
    DEFAULT_RESULTS_ROOT,
    bh_fdr,
    cluster_permutation_p,
    fit_spline_gee_family,
    fit_within_between_family,
)

COHORT_ENDPOINTS = (
    "cohort_m_median", "cohort_d_median", "cohort_e_median",
    "cohort_9d_m_a_median", "cohort_9d_m_e_median", "cohort_9d_m_o_median",
    "cohort_9d_d_n_median", "cohort_9d_d_l_median", "cohort_9d_d_s_median",
    "cohort_9d_e_e_median", "cohort_9d_e_s_median", "cohort_9d_e_m_median",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-metrics", type=Path, default=DEFAULT_RESULTS_ROOT / "01_session_metrics" / "session_metrics.csv")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_ROOT / "03_cohort_coordinate_age")
    parser.add_argument("--n-cluster-permutation", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def fit_family(metrics: pd.DataFrame, endpoints: tuple[str, ...], label: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    return fit_spline_gee_family(metrics, endpoints, label)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics = pd.read_csv(args.session_metrics)
    required = set(COHORT_ENDPOINTS) | {"subject_id", "age_days", "age_source", "geometry_contract_status", "cohort_anchor_id"}
    missing = required - set(metrics)
    if missing:
        raise ValueError(f"Session metrics lack cohort fields: {sorted(missing)}")
    valid = metrics[metrics.geometry_contract_status.isin(("ok", "adjusted"))].copy()
    anchors = valid.cohort_anchor_id.dropna().unique().tolist()
    if len(anchors) != 1:
        raise ValueError(f"Expected exactly one cohort anchor; found {anchors}")
    primary, predictions = fit_family(valid, COHORT_ENDPOINTS, "cohort_age_primary")
    direct = valid[valid.age_source.astype(str).str.contains("direct", case=False, na=False)]
    direct_results, direct_predictions = fit_family(direct, COHORT_ENDPOINTS, "cohort_age_direct_sensitivity")
    within_between = fit_within_between_family(valid, COHORT_ENDPOINTS)
    rng = np.random.default_rng(args.seed)
    cluster_permutation = primary[["endpoint", "wald_chi2", "p_raw", "p_fdr"]].copy()
    cluster_permutation["n_permutation"] = args.n_cluster_permutation
    cluster_permutation["cluster_permutation_p"] = [
        cluster_permutation_p(valid, endpoint, chi2, args.n_cluster_permutation, rng)
        for endpoint, chi2 in zip(primary.endpoint, primary.wald_chi2)
    ]
    cluster_permutation["cluster_permutation_p_fdr"] = bh_fdr(cluster_permutation.cluster_permutation_p)
    primary.to_csv(args.output_dir / "cohort_coordinate_gee_results.csv", index=False)
    predictions.to_csv(args.output_dir / "cohort_coordinate_gee_predictions.csv", index=False)
    direct_results.to_csv(args.output_dir / "cohort_coordinate_gee_direct_age_sensitivity.csv", index=False)
    direct_predictions.to_csv(args.output_dir / "cohort_coordinate_gee_direct_age_predictions.csv", index=False)
    within_between.to_csv(args.output_dir / "cohort_coordinate_within_between_decomposition.csv", index=False)
    cluster_permutation.to_csv(args.output_dir / "cohort_coordinate_gee_cluster_permutation.csv", index=False)
    manifest = {
        "coordinate_contract": "cohort_anchored",
        "cohort_anchor_id": anchors[0],
        "n_primary_sessions": len(valid),
        "n_primary_children": valid.subject_id.nunique(),
        "n_direct_age_sessions": len(direct),
        "n_direct_age_children": direct.subject_id.nunique(),
        "model": "Gaussian GEE, exchangeable child cluster, cubic B-spline df=3",
        "endpoints": list(COHORT_ENDPOINTS),
        "within_between_decomposition_output": "cohort_coordinate_within_between_decomposition.csv",
        "within_between_decomposition_note": "Exploratory diagnostic (pr_01.md M3), not part of the primary FDR family.",
        "cluster_permutation_output": "cohort_coordinate_gee_cluster_permutation.csv",
        "cluster_permutation_n": args.n_cluster_permutation,
        "cluster_permutation_note": "Row-permutation robustness check on the asymptotic GEE omnibus test (pr_01.md M4).",
    }
    (args.output_dir / "cohort_coordinate_gee_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
