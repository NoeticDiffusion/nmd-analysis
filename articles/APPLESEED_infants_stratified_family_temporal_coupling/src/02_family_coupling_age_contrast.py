"""Age-association test for Stratified Family Temporal Coupling endpoints.

Reuses the parent APPLESEED_infants article's balanced paired age-contrast
design (mean of session 1+2 at 4m vs. 8m or 12m) and 4m test-retest ICC, so
the new endpoint family is evaluated with the exact same statistical
machinery and multiple-testing discipline as the rest of the cohort.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from family_coupling_support import (
    reliability_table,
    cohort_age_contrast,
    wide_columns,
)

ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_WIDE_CSV = ARTICLE_DIR / "results" / "appleseed_sftc_20260807" / "01_family_coupling" / "family_coupling_wide.csv"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "appleseed_sftc_20260807" / "02_age_contrast"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wide-csv", type=Path, default=DEFAULT_WIDE_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics = pd.read_csv(args.wide_csv)
    endpoints = tuple(column for column in wide_columns() if column in metrics.columns)
    missing = set(wide_columns()) - set(endpoints)

    reliability = reliability_table(metrics, endpoints, args.n_bootstrap, args.seed)
    age_8m = cohort_age_contrast(metrics, endpoints, "sftc_9d_family_coupling", 3)
    age_12m = cohort_age_contrast(metrics, endpoints, "sftc_9d_family_coupling", 4)

    reliability.to_csv(args.output_dir / "reliability_metrics.csv", index=False)
    age_8m.to_csv(args.output_dir / "cohort_4m_to_8m.csv", index=False)
    age_12m.to_csv(args.output_dir / "cohort_4m_to_12m.csv", index=False)

    def _fdr_hits(frame: pd.DataFrame) -> list[str]:
        if "p_fdr" not in frame or frame.empty:
            return []
        return frame.loc[frame["p_fdr"] < 0.05, "endpoint"].tolist()

    manifest = {
        "wide_csv": str(args.wide_csv),
        "n_endpoints": len(endpoints),
        "n_endpoints_missing_from_csv": len(missing),
        "missing_endpoints": sorted(missing),
        "n_sessions": int(len(metrics)),
        "n_subjects": int(metrics["subject_id"].nunique()) if "subject_id" in metrics else 0,
        "reliability_fdr_hits": _fdr_hits(reliability),
        "age_4m_to_8m_fdr_hits": _fdr_hits(age_8m),
        "age_4m_to_12m_fdr_hits": _fdr_hits(age_12m),
        "n_reliability_endpoints_finite": int(reliability["icc_a1"].notna().sum()) if "icc_a1" in reliability else 0,
        "n_age_8m_endpoints_finite": int(age_8m["p_raw"].notna().sum()) if "p_raw" in age_8m else 0,
        "n_age_12m_endpoints_finite": int(age_12m["p_raw"].notna().sum()) if "p_raw" in age_12m else 0,
    }
    (args.output_dir / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
