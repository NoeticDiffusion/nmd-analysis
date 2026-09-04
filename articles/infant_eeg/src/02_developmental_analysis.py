"""Within-child age-days analysis for cohort-anchored Figshare infant MNJ/reachability metrics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from figshare_infant_support import DEFAULT_RESULTS_ROOT, PRIMARY_ENDPOINTS, within_child_age_associations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-metrics", type=Path, default=DEFAULT_RESULTS_ROOT / "01_session_metrics" / "session_metrics.csv")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_ROOT / "02_developmental_analysis")
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    parser.add_argument("--n-permutation", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def age_associations(metrics: pd.DataFrame, endpoints: tuple[str, ...], label: str, args: argparse.Namespace, direct_age_only: bool = False) -> pd.DataFrame:
    return within_child_age_associations(
        metrics, endpoints, label, n_bootstrap=args.n_bootstrap, n_permutation=args.n_permutation, seed=args.seed, direct_age_only=direct_age_only
    )


def first_last_change(metrics: pd.DataFrame, endpoints: tuple[str, ...]) -> pd.DataFrame:
    rows = []
    for endpoint in endpoints:
        frame = metrics[["subject_id", "age_days", endpoint]].dropna().sort_values(["subject_id", "age_days"])
        pairs = frame.groupby("subject_id").filter(lambda group: len(group) >= 2).groupby("subject_id").agg(
            age_first=("age_days", "first"), age_last=("age_days", "last"), value_first=(endpoint, "first"), value_last=(endpoint, "last")
        )
        difference = pairs.value_last - pairs.value_first
        rows.append({"endpoint": endpoint, "n_children": len(pairs), "median_age_span_days": float(np.median(pairs.age_last - pairs.age_first)) if len(pairs) else np.nan, "mean_first_to_last_change": float(difference.mean()) if len(pairs) else np.nan, "median_first_to_last_change": float(np.median(difference)) if len(pairs) else np.nan})
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics = pd.read_csv(args.session_metrics)
    required = set(PRIMARY_ENDPOINTS) | {"subject_id", "age_days", "visit", "geometry_contract_status"}
    missing = required - set(metrics)
    if missing:
        raise ValueError(f"Session metrics lack required columns: {sorted(missing)}")
    valid = metrics[metrics.geometry_contract_status.isin(("ok", "adjusted"))].copy()
    primary = age_associations(valid, PRIMARY_ENDPOINTS, "3d_primary_within_child", args)
    endpoints_9d = tuple(column for column in valid if column.startswith("mn9d_") and column.endswith("_median"))
    secondary_9d = age_associations(valid, endpoints_9d, "9d_mnj_within_child_sensitivity", args) if endpoints_9d else pd.DataFrame()
    direct_age = age_associations(valid, PRIMARY_ENDPOINTS, "3d_primary_direct_age_sensitivity", args, direct_age_only=True)
    first_last = first_last_change(valid, PRIMARY_ENDPOINTS)
    primary.to_csv(args.output_dir / "within_child_age_associations.csv", index=False)
    secondary_9d.to_csv(args.output_dir / "within_child_age_associations_9d.csv", index=False)
    direct_age.to_csv(args.output_dir / "direct_age_metadata_sensitivity.csv", index=False)
    first_last.to_csv(args.output_dir / "first_to_last_change.csv", index=False)
    manifest = {
        "n_valid_sessions": int(len(valid)),
        "n_subjects": int(valid.subject_id.nunique()),
        "n_subjects_with_two_or_more_visits": int((valid.groupby("subject_id").size() >= 2).sum()),
        "age_days_range": [float(valid.age_days.min()), float(valid.age_days.max())],
        "primary_output": "within_child_age_associations.csv",
        "nine_d_output": "within_child_age_associations_9d.csv",
        "direct_age_sensitivity_output": "direct_age_metadata_sensitivity.csv",
        "coordinate_contract": "cohort_anchored",
        "accepted_geometry_statuses": ["ok", "adjusted"],
    }
    (args.output_dir / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
