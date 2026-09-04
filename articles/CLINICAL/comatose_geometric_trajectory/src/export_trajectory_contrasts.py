from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from scipy.stats import mannwhitneyu

from trajectory_support import (
    ALL_METRICS,
    ARTICLE_FACING_METRICS,
    CONTRAST_DIR,
    GOOD_CPC,
    PATIENT_TIMEBIN_METRICS_CSV,
    POOR_CPC,
    RESULT_LEDGER_DIR,
    RUN_LEVEL_METRICS_CSV,
    bh_fdr,
    cohens_d,
    ensure_dir,
    resolve_metric_dir,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export exploratory CPC1-vs-CPC5 contrasts for geometric trajectory metrics."
    )
    parser.add_argument("--input-dir", type=Path, default=resolve_metric_dir("part1"))
    parser.add_argument("--contrast-dir", type=Path, default=CONTRAST_DIR)
    parser.add_argument("--ledger-dir", type=Path, default=RESULT_LEDGER_DIR)
    parser.add_argument("--cohort-tag", type=str, default="part1_exploratory")
    return parser.parse_args()


def summarize_long(frame: pd.DataFrame, *, cohort_tag: str, level_tag: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (analysis_type, metric), group in frame.groupby(["analysis_type", "metric"], dropna=False):
        good = pd.to_numeric(group.loc[group["cpc_numeric"] == float(GOOD_CPC), "value"], errors="coerce").dropna()
        poor = pd.to_numeric(group.loc[group["cpc_numeric"] == float(POOR_CPC), "value"], errors="coerce").dropna()
        if good.empty or poor.empty:
            continue
        p_value = float(mannwhitneyu(good, poor, alternative="two-sided").pvalue)
        rows.append(
            {
                "cohort_tag": cohort_tag,
                "level_tag": level_tag,
                "analysis_type": analysis_type,
                "metric": metric,
                "cpc1_median": float(good.median()),
                "cpc5_median": float(poor.median()),
                "cohens_d": cohens_d(good.to_numpy(dtype=float), poor.to_numpy(dtype=float)),
                "mw_p": p_value,
                "n_cpc1": int(good.shape[0]),
                "n_cpc5": int(poor.shape[0]),
                "article_facing": bool(metric in ARTICLE_FACING_METRICS),
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["mw_q"] = out.groupby("analysis_type", dropna=False)["mw_p"].transform(bh_fdr)
    out["abs_d"] = out["cohens_d"].abs()
    return out.sort_values(["analysis_type", "article_facing", "abs_d"], ascending=[True, False, False]).reset_index(drop=True)


def build_ledger(patient_contrasts: pd.DataFrame, *, cohort_tag: str) -> pd.DataFrame:
    if patient_contrasts.empty:
        return pd.DataFrame()
    ledger = patient_contrasts.copy()
    ledger["metric_rank"] = ledger.groupby("analysis_type", dropna=False)["abs_d"].rank(method="first", ascending=False).astype(int)
    ledger["selection_status"] = ledger["article_facing"].map(
        lambda value: "article_facing_initial_set" if value else "supportive_exploratory"
    )
    ledger["validation_status"] = "exploratory_part1_only"
    ledger["cohort_tag"] = cohort_tag
    return ledger[
        [
            "cohort_tag",
            "analysis_type",
            "metric",
            "metric_rank",
            "selection_status",
            "validation_status",
            "cpc1_median",
            "cpc5_median",
            "cohens_d",
            "abs_d",
            "mw_p",
            "mw_q",
            "n_cpc1",
            "n_cpc5",
        ]
    ].reset_index(drop=True)


def main() -> None:
    args = parse_args()
    ensure_dir(args.contrast_dir)
    ensure_dir(args.ledger_dir)

    patient_long = pd.read_csv(args.input_dir / PATIENT_TIMEBIN_METRICS_CSV, low_memory=False)
    run_long = pd.read_csv(args.input_dir / RUN_LEVEL_METRICS_CSV, low_memory=False)
    for frame in (patient_long, run_long):
        frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
        frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
        frame.dropna(subset=["cpc_numeric", "value"], inplace=True)
        drop_idx = frame.index[~frame["metric"].isin(ALL_METRICS)]
        if len(drop_idx):
            frame.drop(index=drop_idx, inplace=True)

    patient_contrasts = summarize_long(patient_long, cohort_tag=args.cohort_tag, level_tag="patient_timebin")
    run_contrasts = summarize_long(run_long, cohort_tag=args.cohort_tag, level_tag="run_level")
    patient_contrasts.to_csv(args.contrast_dir / "patient_timebin_outcome_contrasts.csv", index=False)
    run_contrasts.to_csv(args.contrast_dir / "run_level_outcome_contrasts.csv", index=False)

    ranking = build_ledger(patient_contrasts, cohort_tag=args.cohort_tag)
    ranking.to_csv(args.contrast_dir / "article_candidate_ranking.csv", index=False)
    ranking.to_csv(args.ledger_dir / "metric_result_ledger.csv", index=False)


if __name__ == "__main__":
    main()
