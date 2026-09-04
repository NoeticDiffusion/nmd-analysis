"""Summarize lag consistency and coordinate-contract sensitivity for angles."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RUN_ROOT = ARTICLE_DIR / "results" / "psychosis_angles_20260719"
TARGETED_METRICS = ("turn_angle_p90", "turn_angle_iqr", "turn_angle_mad")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize psychosis angle lag and contract robustness.")
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--dataset", choices=["both", "ds003944", "ds003947"], default="both")
    return parser.parse_args()


def load_contract(root: Path, contract: str, dataset: str) -> pd.DataFrame:
    path = root / contract / dataset / "turning_angle_contrasts.csv"
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    frame["coordinate_contract"] = contract
    return frame


def summarize_dataset(root: Path, dataset: str) -> pd.DataFrame:
    cohort = load_contract(root, "cohort_anchored", dataset)
    subject = load_contract(root, "subject_anchored", dataset)
    if cohort.empty:
        return pd.DataFrame()
    primary = cohort[(cohort["analysis_scope"] == "primary") & cohort["metric"].isin(TARGETED_METRICS)].copy()
    primary = primary.rename(
        columns={
            "cohens_d_right_minus_left": "cohort_anchored_d",
            "mannwhitney_q_bh_targeted": "cohort_anchored_q_targeted",
        }
    )
    keep = ["dataset", "contrast", "chart", "lag_epochs", "metric", "cohort_anchored_d", "cohort_anchored_q_targeted"]
    primary = primary[keep]
    if not subject.empty:
        sensitivity = subject[(subject["analysis_scope"] == "primary") & subject["metric"].isin(TARGETED_METRICS)].copy()
        sensitivity = sensitivity.rename(
            columns={
                "cohens_d_right_minus_left": "subject_anchored_d",
                "mannwhitney_q_bh_targeted": "subject_anchored_q_targeted",
            }
        )[["dataset", "contrast", "chart", "lag_epochs", "metric", "subject_anchored_d", "subject_anchored_q_targeted"]]
        primary = primary.merge(sensitivity, on=["dataset", "contrast", "chart", "lag_epochs", "metric"], how="left")
        primary["contract_direction_agrees"] = np.sign(primary["cohort_anchored_d"]) == np.sign(primary["subject_anchored_d"])
    else:
        primary["subject_anchored_d"] = np.nan
        primary["subject_anchored_q_targeted"] = np.nan
        primary["contract_direction_agrees"] = np.nan

    lag_key = ["dataset", "contrast", "chart", "metric"]
    primary["n_lags_targeted_significant"] = primary.groupby(lag_key)["cohort_anchored_q_targeted"].transform(
        lambda q: int((q < 0.05).sum())
    )
    primary["lag_direction_consistent"] = primary.groupby(lag_key)["cohort_anchored_d"].transform(
        lambda d: d.dropna().pipe(lambda values: len(values) > 0 and values.gt(0).all() or len(values) > 0 and values.lt(0).all())
    )
    primary["dynamic_coherence"] = (primary["n_lags_targeted_significant"] >= 2) & primary["lag_direction_consistent"]
    return primary


def main() -> None:
    args = parse_args()
    datasets = ("ds003944", "ds003947") if args.dataset == "both" else (args.dataset,)
    for dataset in datasets:
        summary = summarize_dataset(args.run_root, dataset)
        if summary.empty:
            print(f"[{dataset}] No cohort-anchored contrast table found; skipping robustness summary.")
            continue
        out_dir = args.run_root / "robustness"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{dataset}_lag_contract_robustness.csv"
        summary.to_csv(path, index=False)
        n_coherent = summary[["dataset", "contrast", "chart", "metric", "dynamic_coherence"]].drop_duplicates()["dynamic_coherence"].sum()
        print(f"[{dataset}] Wrote lag/contract robustness ({len(summary)} rows; coherent cells={int(n_coherent)}) to {path}")


if __name__ == "__main__":
    sys.exit(main())
