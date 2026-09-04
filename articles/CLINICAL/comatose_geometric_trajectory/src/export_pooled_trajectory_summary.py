from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from export_trajectory_contrasts import build_ledger, summarize_long
from trajectory_support import (
    ARTICLE_DIR,
    PATIENT_TIMEBIN_METRICS_CSV,
    RESULT_STAMP,
    RUN_LEVEL_METRICS_CSV,
    ensure_dir,
    resolve_metric_dir,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pool part1 and part2 trajectory outputs and export pooled contrast summaries."
    )
    parser.add_argument("--part1-dir", type=Path, default=resolve_metric_dir("part1"))
    parser.add_argument("--part2-dir", type=Path, default=resolve_metric_dir("part2"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ARTICLE_DIR / "results" / f"outcome_contrasts_trajectory_{RESULT_STAMP}_pooled_cpc15_primary12h",
    )
    parser.add_argument(
        "--ledger-dir",
        type=Path,
        default=ARTICLE_DIR / "results" / f"metric_result_ledger_{RESULT_STAMP}_pooled",
    )
    parser.add_argument("--cohort-tag", type=str, default="pooled_part1_part2")
    return parser.parse_args()


def load_concat(csv_name: str, *, part1_dir: Path, part2_dir: Path) -> pd.DataFrame:
    part1 = pd.read_csv(part1_dir / csv_name, low_memory=False)
    part2 = pd.read_csv(part2_dir / csv_name, low_memory=False)
    part1["source_cohort"] = "part1"
    part2["source_cohort"] = "part2"
    return pd.concat([part1, part2], ignore_index=True)


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)
    ensure_dir(args.ledger_dir)

    patient_long = load_concat(
        PATIENT_TIMEBIN_METRICS_CSV,
        part1_dir=args.part1_dir,
        part2_dir=args.part2_dir,
    )
    run_long = load_concat(
        RUN_LEVEL_METRICS_CSV,
        part1_dir=args.part1_dir,
        part2_dir=args.part2_dir,
    )

    for frame in (patient_long, run_long):
        frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
        frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
        frame.dropna(subset=["cpc_numeric", "value"], inplace=True)

    patient_contrasts = summarize_long(patient_long, cohort_tag=args.cohort_tag, level_tag="patient_timebin")
    run_contrasts = summarize_long(run_long, cohort_tag=args.cohort_tag, level_tag="run_level")

    patient_contrasts.to_csv(args.output_dir / "patient_timebin_outcome_contrasts.csv", index=False)
    run_contrasts.to_csv(args.output_dir / "run_level_outcome_contrasts.csv", index=False)

    ranking = build_ledger(patient_contrasts, cohort_tag=args.cohort_tag)
    ranking["validation_status"] = "pooled_synthesis_after_part1_part2"
    ranking.to_csv(args.output_dir / "article_candidate_ranking.csv", index=False)
    ranking.to_csv(args.ledger_dir / "metric_result_ledger.csv", index=False)


if __name__ == "__main__":
    main()
