"""Analyze APPLESEED test--retest reliability and within-subject development."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from appleseed_support import (
    CONVENTIONAL_ENDPOINTS,
    DEFAULT_RESULTS_ROOT,
    PRIMARY_ENDPOINTS,
    bh_fdr,
    bootstrap_icc,
    icc_a1,
    paired_summary,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-metrics", type=Path, default=DEFAULT_RESULTS_ROOT / "01_session_metrics" / "session_metrics.csv")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_ROOT / "02_reliability_longitudinal")
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def reliability_table(
    metrics: pd.DataFrame,
    endpoints: tuple[str, ...],
    n_bootstrap: int,
    seed: int,
    fdr_family: str,
) -> pd.DataFrame:
    paired = metrics.pivot(index="subject_id", columns="session", values=list(endpoints))
    rows = []
    for endpoint in endpoints:
        a = paired[(endpoint, 1)].to_numpy() if (endpoint, 1) in paired else np.full(len(paired), np.nan)
        b = paired[(endpoint, 2)].to_numpy() if (endpoint, 2) in paired else np.full(len(paired), np.nan)
        row = {"endpoint": endpoint, "fdr_family": fdr_family, **icc_a1(a, b), **paired_summary(a, b)}
        row["icc_ci95_low"], row["icc_ci95_high"] = bootstrap_icc(a, b, n_bootstrap, seed)
        rows.append(row)
    output = pd.DataFrame(rows)
    output["p_fdr"] = bh_fdr(output["p_raw"])
    return output


def _bootstrap_difference(difference: np.ndarray, n_bootstrap: int, seed: int) -> tuple[float, float]:
    difference = np.asarray(difference, dtype=float)
    difference = difference[np.isfinite(difference)]
    if len(difference) < 2:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    draws = np.array([np.mean(difference[rng.integers(0, len(difference), len(difference))]) for _ in range(n_bootstrap)])
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def longitudinal_table(metrics: pd.DataFrame, n_bootstrap: int, seed: int) -> pd.DataFrame:
    """Use the complete 11-subject panel; session 1 is the frozen baseline."""
    complete_subjects = metrics.groupby("subject_id").filter(lambda x: set(x["session"]) == {1, 2, 3, 4})["subject_id"].unique()
    panel = metrics[metrics["subject_id"].isin(complete_subjects)].pivot(index="subject_id", columns="session", values=list(PRIMARY_ENDPOINTS))
    rows = []
    friedman_p_by_endpoint = {}
    if panel.empty:
        return pd.DataFrame(
            {"endpoint": list(PRIMARY_ENDPOINTS) * 2, "contrast": ["ses-3_minus_ses-1"] * len(PRIMARY_ENDPOINTS) + ["ses-4_minus_ses-1"] * len(PRIMARY_ENDPOINTS)}
        )
    for endpoint in PRIMARY_ENDPOINTS:
        values = [panel[(endpoint, session)].to_numpy() for session in (1, 2, 3, 4)]
        try:
            friedman_stat, friedman_p = stats.friedmanchisquare(*values)
        except ValueError:
            friedman_stat, friedman_p = np.nan, np.nan
        friedman_p_by_endpoint[endpoint] = friedman_p
        for target in (3, 4):
            baseline, follow_up = panel[(endpoint, 1)].to_numpy(), panel[(endpoint, target)].to_numpy()
            row = {
                "endpoint": endpoint,
                "contrast": f"ses-{target}_minus_ses-1",
                "n_complete_subjects": len(panel),
                "friedman_stat": friedman_stat,
                "friedman_p_raw": friedman_p,
                **paired_summary(baseline, follow_up),
            }
            row["bootstrap_ci95_low"], row["bootstrap_ci95_high"] = _bootstrap_difference(
                follow_up - baseline, n_bootstrap, seed + target
            )
            rows.append(row)
    output = pd.DataFrame(rows)
    output["p_fdr"] = bh_fdr(output["p_raw"]) if "p_raw" in output else np.nan
    friedman_endpoints = list(friedman_p_by_endpoint)
    friedman_fdr = dict(
        zip(friedman_endpoints, bh_fdr([friedman_p_by_endpoint[endpoint] for endpoint in friedman_endpoints]))
    )
    output["friedman_p_fdr"] = output["endpoint"].map(friedman_fdr)
    return output


def baseline_sensitivity(metrics: pd.DataFrame) -> pd.DataFrame:
    """Retest-mean baseline sensitivity: mean(ses-1,ses-2) vs ses-3/ses-4."""
    complete = metrics.groupby("subject_id").filter(lambda x: set(x["session"]) == {1, 2, 3, 4})
    if complete.empty:
        return pd.DataFrame(
            {"endpoint": list(PRIMARY_ENDPOINTS) * 2, "contrast": ["ses-3_minus_retest_mean"] * len(PRIMARY_ENDPOINTS) + ["ses-4_minus_retest_mean"] * len(PRIMARY_ENDPOINTS)}
        )
    panel = complete.pivot(index="subject_id", columns="session", values=list(PRIMARY_ENDPOINTS))
    rows = []
    for endpoint in PRIMARY_ENDPOINTS:
        baseline = 0.5 * (panel[(endpoint, 1)] + panel[(endpoint, 2)])
        for target in (3, 4):
            rows.append({"endpoint": endpoint, "contrast": f"ses-{target}_minus_retest_mean", **paired_summary(baseline, panel[(endpoint, target)])})
    output = pd.DataFrame(rows)
    output["p_fdr"] = bh_fdr(output["p_raw"]) if "p_raw" in output else np.nan
    return output


def cohort_age_contrast(
    metrics: pd.DataFrame,
    endpoints: tuple[str, ...],
    label: str,
    target_session: int,
    n_bootstrap: int,
    seed: int,
) -> pd.DataFrame:
    """Balanced paired age contrast: mean(session 1,2) at 4m versus a follow-up."""
    target_label = {3: "8m", 4: "12m"}[target_session]
    eligible = metrics.groupby("subject_id")["session"].agg(set)
    eligible = eligible[eligible.apply(lambda visits: {1, 2, target_session}.issubset(visits))].index
    panel = metrics[metrics["subject_id"].isin(eligible)].pivot(index="subject_id", columns="session", values=list(endpoints))
    if panel.empty or not {1, 2, target_session}.issubset(set(panel.columns.get_level_values(1))):
        return pd.DataFrame(
            {"analysis_layer": [label] * len(endpoints), "endpoint": endpoints, "contrast": [f"age_{target_label}_minus_age_4m_mean"] * len(endpoints)}
        )
    rows = []
    for endpoint in endpoints:
        baseline = 0.5 * (panel[(endpoint, 1)] + panel[(endpoint, 2)])
        follow_up = panel[(endpoint, target_session)]
        difference = follow_up - baseline
        rows.append({
            "analysis_layer": label,
            "endpoint": endpoint,
            "contrast": f"age_{target_label}_minus_age_4m_mean",
            "n_eligible_subjects": len(panel),
            **paired_summary(baseline, follow_up),
        })
        rows[-1]["bootstrap_ci95_low"], rows[-1]["bootstrap_ci95_high"] = _bootstrap_difference(
            difference, n_bootstrap, seed + target_session
        )
    output = pd.DataFrame(rows)
    output["p_fdr_sensitivity"] = bh_fdr(output["p_raw"]) if "p_raw" in output else np.nan
    return output


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics = pd.read_csv(args.session_metrics)
    required = set(PRIMARY_ENDPOINTS) | {"subject_id", "session"}
    missing = required - set(metrics)
    if missing:
        raise ValueError(f"Session metrics lack required columns: {sorted(missing)}")
    reliability = reliability_table(
        metrics, PRIMARY_ENDPOINTS, args.n_bootstrap, args.seed, "reliability_primary_9_endpoints"
    )
    coordinate_reliability = reliability_table(
        metrics,
        ("cohort_m_median", "cohort_d_median", "cohort_e_median"),
        args.n_bootstrap,
        args.seed + 1,
        "reliability_coordinate_3_endpoints",
    )
    conventional_reliability = reliability_table(
        metrics, CONVENTIONAL_ENDPOINTS, args.n_bootstrap, args.seed + 2, "reliability_conventional_4_endpoints"
    )
    longitudinal = longitudinal_table(metrics, args.n_bootstrap, args.seed)
    sensitivity = baseline_sensitivity(metrics)
    cohort_age = cohort_age_contrast(
        metrics, PRIMARY_ENDPOINTS, "cohort_anchored_3d_primary", 3, args.n_bootstrap, args.seed + 10
    )
    cohort_age_12m = cohort_age_contrast(
        metrics, PRIMARY_ENDPOINTS, "cohort_anchored_3d_primary", 4, args.n_bootstrap, args.seed + 20
    )
    cohort_coordinates = cohort_age_contrast(
        metrics,
        ("cohort_m_median", "cohort_d_median", "cohort_e_median"),
        "cohort_anchored_3d_coordinate_positions",
        3,
        args.n_bootstrap,
        args.seed + 30,
    )
    cohort_coordinates_12m = cohort_age_contrast(
        metrics,
        ("cohort_m_median", "cohort_d_median", "cohort_e_median"),
        "cohort_anchored_3d_coordinate_positions",
        4,
        args.n_bootstrap,
        args.seed + 40,
    )
    endpoints_9d = tuple(column for column in metrics.columns if column.startswith("mn9d_") and column.endswith("_median"))
    cohort_age_9d = (
        cohort_age_contrast(
            metrics, endpoints_9d, "cohort_anchored_9d_complete_case", 3, args.n_bootstrap, args.seed + 50
        )
        if endpoints_9d
        else pd.DataFrame()
    )
    cohort_age_9d_12m = (
        cohort_age_contrast(
            metrics, endpoints_9d, "cohort_anchored_9d_complete_case", 4, args.n_bootstrap, args.seed + 60
        )
        if endpoints_9d
        else pd.DataFrame()
    )
    reliability.to_csv(args.output_dir / "reliability_metrics.csv", index=False)
    coordinate_reliability.to_csv(args.output_dir / "reliability_coordinates.csv", index=False)
    conventional_reliability.to_csv(args.output_dir / "reliability_conventional.csv", index=False)
    longitudinal.to_csv(args.output_dir / "longitudinal_contrasts.csv", index=False)
    sensitivity.to_csv(args.output_dir / "retest_mean_sensitivity.csv", index=False)
    cohort_age.to_csv(args.output_dir / "cohort_4m_to_8m.csv", index=False)
    cohort_age_12m.to_csv(args.output_dir / "cohort_4m_to_12m.csv", index=False)
    cohort_coordinates.to_csv(args.output_dir / "cohort_coordinate_4m_to_8m.csv", index=False)
    cohort_coordinates_12m.to_csv(args.output_dir / "cohort_coordinate_4m_to_12m.csv", index=False)
    cohort_age_9d.to_csv(args.output_dir / "cohort_4m_to_8m_9d_complete_case.csv", index=False)
    cohort_age_9d_12m.to_csv(args.output_dir / "cohort_4m_to_12m_9d_complete_case.csv", index=False)
    results = {
        "n_reliability_subjects": int(metrics[metrics["session"].isin([1, 2])]["subject_id"].nunique()),
        "n_complete_longitudinal_subjects": int((metrics.groupby("subject_id").size() == 4).sum()),
        "n_bootstrap": args.n_bootstrap,
        "primary_endpoints": list(PRIMARY_ENDPOINTS),
        "reliability_output": "reliability_metrics.csv",
        "coordinate_reliability_output": "reliability_coordinates.csv",
        "conventional_reliability_output": "reliability_conventional.csv",
        "longitudinal_output": "longitudinal_contrasts.csv",
        "cohort_age_output": "cohort_4m_to_8m.csv",
        "cohort_age_12m_output": "cohort_4m_to_12m.csv",
        "cohort_coordinate_output": "cohort_coordinate_4m_to_8m.csv",
        "cohort_coordinate_12m_output": "cohort_coordinate_4m_to_12m.csv",
        "cohort_age_9d_output": "cohort_4m_to_8m_9d_complete_case.csv",
        "cohort_age_9d_12m_output": "cohort_4m_to_12m_9d_complete_case.csv",
        "fdr_families": {
            "reliability_primary": 9,
            "reliability_coordinates": 3,
            "reliability_conventional": 4,
            "cohort_dynamics_4m_to_8m": 9,
            "cohort_dynamics_4m_to_12m": 9,
            "cohort_coordinates_4m_to_8m": 3,
            "cohort_coordinates_4m_to_12m": 3,
            "retest_mean_sensitivity": 18,
            "nine_dimensional_4m_to_8m": 10,
            "nine_dimensional_4m_to_12m": 10,
        },
        "n_9d_complete_case_4m_to_8m": int(cohort_age_9d["n"].max())
        if not cohort_age_9d.empty and "n" in cohort_age_9d
        else 0,
        "n_9d_complete_case_4m_to_12m": int(cohort_age_9d_12m["n"].max())
        if not cohort_age_9d_12m.empty and "n" in cohort_age_9d_12m
        else 0,
    }
    (args.output_dir / "analysis_manifest.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
