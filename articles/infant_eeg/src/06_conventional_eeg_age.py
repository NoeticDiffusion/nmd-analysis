"""Conventional-EEG (qEEG) comparator age analysis — robustness/context family.

A hard reviewer's obvious question for a developmental-EEG article (peer_review/pr_02.md):
would well-known, classical qEEG summaries (relative band power, band ratios, alpha peak /
median frequency, spectral/permutation entropy, connectivity) already show the same
age-related change that motivates the cohort-anchored MNPS-coordinate result (Results R2,
03_cohort_coordinate_age.py)? Age-related shifts in these classical measures are among the
best-established findings in infant EEG maturation research, so this comparator lets a
reader judge whether the state-space coordinate result tracks that well-known signal, adds
to it, or is dissociable from it.

This script does NOT replace or get pooled with the primary 12-endpoint cohort-coordinate
family or either local-dynamics robustness family (02_developmental_analysis.py,
05_cohort_pooled_reachability.py). It is a separate, descriptive comparator family with its
own FDR correction, using the identical cohort-level GEE and within-child estimators as the
rest of the pipeline so results are directly comparable in method, not conflated in family.

Requires a re-export with `conventional_eeg.enabled=true` (packs `tier1`, `complexity`,
optionally `connectivity`) in the upstream ingest config
(config_ingest_figshare_infant_eeg.yaml), so that `eeg_conventional_*` comparator columns
are present in the H5 export pointed to by --data-root.

Outputs (in --output-dir):
  conventional_eeg_coverage.csv                       — per-endpoint non-missing coverage
  conventional_eeg_cohort_gee_results.csv              — cohort-level spline GEE (own FDR family)
  conventional_eeg_cohort_gee_predictions.csv          — fitted age curves for figures
  conventional_eeg_within_child_age_associations.csv   — within-child slope/bootstrap/permutation
  conventional_eeg_within_child_direct_age_sensitivity.csv — direct-age-only subset of the above
  session_metrics_with_conventional_eeg.csv            — session_metrics.csv + conventional columns
  conventional_eeg_age_manifest.json                   — provenance/manifest
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from figshare_infant_support import (
    DEFAULT_DATA_ROOT,
    DEFAULT_RESULTS_ROOT,
    bh_fdr,
    cluster_permutation_p,
    conventional_eeg_medians,
    fit_spline_gee_family,
    fit_within_between_family,
    h5_paths,
    participant_metadata,
    session_identity,
    within_child_age_associations,
)

CONVENTIONAL_DATA_ROOT_NAME = "neuralmanifolddynamics_figshare_infant_eeg_20260806_122539"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--session-metrics", type=Path, default=DEFAULT_RESULTS_ROOT / "01_session_metrics" / "session_metrics.csv")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_ROOT / "06_conventional_eeg_age")
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    parser.add_argument("--n-permutation", type=int, default=5000)
    parser.add_argument("--n-cluster-permutation", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.data_root.name != CONVENTIONAL_DATA_ROOT_NAME:
        parser.error(
            "--data-root must name the coverage-fixed "
            f"export {CONVENTIONAL_DATA_ROOT_NAME!r}; the default artifact-masked "
            "export has no testable connectivity columns."
        )
    if args.output_dir.resolve() == (DEFAULT_RESULTS_ROOT / "06_conventional_eeg_age").resolve():
        parser.error(
            "--output-dir must be separate from the canonical primary result tree; "
            "use a separate result tree for the coverage-fixed re-extraction."
        )
    return args


def extract_conventional(data_root: Path) -> pd.DataFrame:
    rows = []
    for h5_path in h5_paths(data_root):
        with h5py.File(h5_path, "r") as handle:
            participant = participant_metadata(handle)
            identity = session_identity(h5_path, participant)
            rows.append({**identity, **conventional_eeg_medians(handle)})
    return pd.DataFrame(rows).sort_values(["subject_id", "visit"])


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    conventional = extract_conventional(args.data_root)
    conv_columns = tuple(sorted(column for column in conventional.columns if column.startswith("eeg_conventional_")))
    if not conv_columns:
        raise SystemExit(
            "No eeg_conventional_* columns found under --data-root. Confirm conventional_eeg "
            "is enabled (config_ingest_figshare_infant_eeg.yaml: tier1/complexity/connectivity) "
            "and that --data-root points at the re-extracted, conventional-EEG-enabled export."
        )
    print(f"Found {len(conv_columns)} conventional-EEG columns: {list(conv_columns)}")

    session_metrics = pd.read_csv(args.session_metrics)
    merged = session_metrics.merge(
        conventional[["subject_id", "visit", *conv_columns]],
        on=["subject_id", "visit"],
        how="left",
        validate="one_to_one",
    )
    valid = merged[merged.geometry_contract_status.isin(("ok", "adjusted"))].copy()

    coverage = (
        valid[list(conv_columns)]
        .notna()
        .mean()
        .rename("coverage_fraction")
        .reset_index()
        .rename(columns={"index": "endpoint"})
    )
    coverage["n_sessions"] = len(valid)

    cohort_results, cohort_predictions = fit_spline_gee_family(valid, conv_columns, "conventional_eeg_cohort_age")

    # Same M3/M4-style robustness checks already applied to the primary 12-endpoint
    # cohort-coordinate family (03_cohort_coordinate_age.py), since a cohort-level
    # comparator effect can equally be a between-child artifact for this family.
    within_between = fit_within_between_family(valid, conv_columns)
    rng = np.random.default_rng(args.seed)
    cluster_permutation = cohort_results[["endpoint", "wald_chi2", "p_raw", "p_fdr", "not_testable_reason"]].copy()
    cluster_permutation["n_permutation"] = args.n_cluster_permutation
    cluster_permutation["cluster_permutation_p"] = [
        cluster_permutation_p(valid, endpoint, chi2, args.n_cluster_permutation, rng)
        for endpoint, chi2 in zip(cohort_results.endpoint, cohort_results.wald_chi2)
    ]
    cluster_permutation["cluster_permutation_p_fdr"] = bh_fdr(cluster_permutation.cluster_permutation_p)

    within_child = within_child_age_associations(
        valid, conv_columns, "conventional_eeg_within_child",
        n_bootstrap=args.n_bootstrap, n_permutation=args.n_permutation, seed=args.seed,
    )
    direct_age = valid[valid.age_source.astype(str).str.contains("direct", case=False, na=False)]
    direct_within_child = within_child_age_associations(
        direct_age, conv_columns, "conventional_eeg_within_child_direct_age_sensitivity",
        n_bootstrap=args.n_bootstrap, n_permutation=args.n_permutation, seed=args.seed, direct_age_only=True,
    )

    coverage.to_csv(args.output_dir / "conventional_eeg_coverage.csv", index=False)
    cohort_results.to_csv(args.output_dir / "conventional_eeg_cohort_gee_results.csv", index=False)
    cohort_predictions.to_csv(args.output_dir / "conventional_eeg_cohort_gee_predictions.csv", index=False)
    within_between.to_csv(args.output_dir / "conventional_eeg_within_between_decomposition.csv", index=False)
    cluster_permutation.to_csv(args.output_dir / "conventional_eeg_cohort_gee_cluster_permutation.csv", index=False)
    within_child.to_csv(args.output_dir / "conventional_eeg_within_child_age_associations.csv", index=False)
    direct_within_child.to_csv(args.output_dir / "conventional_eeg_within_child_direct_age_sensitivity.csv", index=False)
    merged.to_csv(args.output_dir / "session_metrics_with_conventional_eeg.csv", index=False)

    manifest = {
        "data_root": str(args.data_root),
        "n_conventional_columns": len(conv_columns),
        "conventional_columns": list(conv_columns),
        "n_sessions": int(len(valid)),
        "n_children": int(valid.subject_id.nunique()),
        "n_direct_age_sessions": int(len(direct_age)),
        "n_direct_age_children": int(direct_age.subject_id.nunique()) if len(direct_age) else 0,
        "n_cohort_gee_fdr_supported": int((cohort_results.p_fdr < 0.05).sum()),
        "n_within_child_fdr_supported": int((within_child.p_fdr_sensitivity < 0.05).sum()),
        "n_within_child_wald_fdr_supported": int((within_between.within_p_raw.notna() & (bh_fdr(within_between.within_p_raw) < 0.05)).sum()),
        "n_between_child_wald_fdr_supported": int((within_between.between_p_raw.notna() & (bh_fdr(within_between.between_p_raw) < 0.05)).sum()),
        "n_cluster_permutation_fdr_supported": int((cluster_permutation.cluster_permutation_p_fdr < 0.05).sum()),
        "coverage_output": "conventional_eeg_coverage.csv",
        "cohort_gee_output": "conventional_eeg_cohort_gee_results.csv",
        "within_between_decomposition_output": "conventional_eeg_within_between_decomposition.csv",
        "cluster_permutation_output": "conventional_eeg_cohort_gee_cluster_permutation.csv",
        "within_child_output": "conventional_eeg_within_child_age_associations.csv",
        "direct_age_sensitivity_output": "conventional_eeg_within_child_direct_age_sensitivity.csv",
        "note": (
            "Separate, descriptive comparator family (peer_review/pr_02.md). FDR is computed "
            "within this family only, independent of the 12-endpoint primary cohort-coordinate "
            "family (03_cohort_coordinate_age.py) and both local-dynamics families "
            "(02_developmental_analysis.py, 05_cohort_pooled_reachability.py)."
        ),
    }
    (args.output_dir / "conventional_eeg_age_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
