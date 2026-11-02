"""Hourly sign-stability audit of the strongest part1 L1 contrasts (sl_006 / sl_028).

Reuses existing DDC run-level tables. No new H5 extract. Biological unit is
subject-median within each clock hour. Recording-level tables are descriptive
only and are not inferential. No Holm across hours. Not SL-004A. Part2 sealed.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from icare_v2_common import (
    add_common_args,
    assign_time_bin,
    resolve_pipeline_config,
    write_csv,
    write_json,
)
from icare_v2_outcome_contrast_analysis import _contrast_row

HOUR_BINS = tuple(f"{hour}_{hour + 1}h" for hour in range(12))

PRIMARY = (
    ("tr_a_median", "Tr(a)", "CPC1 < CPC5"),
    ("g90_cohort_reknn_median", "G90", "CPC1 < CPC5"),
    ("r_ba_median", "R_b/a", "CPC1 < CPC5"),
)
CONTROL = (
    ("b_norm_median", "b_norm", "CPC1 < CPC5"),
    ("d_eff_cohort_reknn_median", "d_eff", "CPC1 > CPC5"),
)


def _direction_ok(prediction: str, d: float) -> bool | None:
    if not np.isfinite(d):
        return None
    if "CPC1 < CPC5" in prediction:
        return bool(d < 0)
    if "CPC1 > CPC5" in prediction:
        return bool(d > 0)
    return None


def _load_runs(cfg) -> pd.DataFrame:
    path = cfg.output_dir / "ddc_run_level.csv"
    if not path.is_file():
        raise SystemExit(f"missing {path}")
    runs = pd.read_csv(path)
    hours = pd.to_numeric(runs.get("run_midpoint_from_anchor_hours"), errors="coerce")
    runs["hour_bin"] = [assign_time_bin(value, "hourly_12h") for value in hours]
    work = runs[runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    work = work[work["hour_bin"].isin(HOUR_BINS)]
    return work


def _subject_hour(runs: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    agg: dict[str, Any] = {
        "cpc": ("cpc", "first"),
        "contrast_group": ("contrast_group", "first"),
        "n_runs": ("source_h5", "nunique"),
    }
    for metric in metrics:
        if metric in runs.columns:
            agg[metric] = (metric, "median")
    return runs.groupby(["hour_bin", "subject_id"], as_index=False).agg(**agg)


def _coverage(frame: pd.DataFrame, *, grain: str, cfg) -> pd.DataFrame:
    rows = []
    for hour in HOUR_BINS:
        block = frame[frame["hour_bin"] == hour]
        good = block[block["contrast_group"] == cfg.good_label]
        poor = block[block["contrast_group"] == cfg.poor_label]
        rows.append(
            {
                "grain": grain,
                "hour_bin": hour,
                "n_cpc1": int(len(good)),
                "n_cpc5": int(len(poor)),
                "testable": bool(len(good) >= cfg.min_testable_group_n and len(poor) >= cfg.min_testable_group_n),
            }
        )
    return pd.DataFrame(rows)


def _hourly_contrasts(frame: pd.DataFrame, specs: tuple, *, grain: str, cfg) -> pd.DataFrame:
    rows = []
    for hour in HOUR_BINS:
        block = frame[frame["hour_bin"] == hour]
        for metric, hyp, pred in specs:
            if metric not in block.columns:
                continue
            row = _contrast_row(block, metric, cfg=cfg, family=f"hourly_{grain}", hypothesis=hyp, prediction=pred)
            row["hour_bin"] = hour
            row["grain"] = grain
            d = float(row.get("cohens_d_cpc1_minus_cpc5", float("nan")))
            row["direction_matches"] = _direction_ok(pred, d)
            row["sign_audit"] = bool(row["family_testable"])
            rows.append(row)
    return pd.DataFrame(rows)


def _stability(contrasts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if contrasts.empty:
        return pd.DataFrame()
    work = contrasts[contrasts["sign_audit"] == True].copy()
    for (grain, metric), block in work.groupby(["grain", "metric"]):
        match = block["direction_matches"].fillna(False).astype(bool)
        rows.append(
            {
                "grain": grain,
                "metric": metric,
                "hypothesis": block["hypothesis"].iloc[0],
                "n_testable_hours": int(len(block)),
                "n_direction_match": int(match.sum()),
                "frac_direction_match": float(match.mean()) if len(block) else float("nan"),
                "n_mw_p_lt_05": int((pd.to_numeric(block["mannwhitney_p"], errors="coerce") < 0.05).sum()),
                "median_d": float(pd.to_numeric(block["cohens_d_cpc1_minus_cpc5"], errors="coerce").median()),
            }
        )
    return pd.DataFrame(rows)


def _render(*, coverage: pd.DataFrame, contrasts: pd.DataFrame, stability: pd.DataFrame, cfg) -> str:
    lines = [
        "# Hourly audit of strongest L1 contrasts (part1)",
        "",
        f"Bundle `{cfg.bundle_id}`. Clock-hour bins of run midpoint, 0-12 h.",
        "Primary grain: **subject-median within hour**. Recording-level is descriptive only.",
        "No Holm across hours. Not SL-004A. Part2 is not opened. p-values are descriptive.",
        "",
        "Frozen metrics: `Tr(a)`, cohort `G90`, `R_b/a`. Controls: `||b||`, cohort `d_eff`.",
        "",
        "## Subject coverage by hour",
        "",
        "| Hour | n CPC1 | n CPC5 | Testable (n>=10/arm) |",
        "| --- | ---: | ---: | --- |",
    ]
    cov = coverage[coverage["grain"] == "subject"]
    for _, row in cov.iterrows():
        lines.append(f"| {row['hour_bin']} | {int(row['n_cpc1'])} | {int(row['n_cpc5'])} | {bool(row['testable'])} |")
    lines += [
        "",
        "## Subject-within-hour contrasts",
        "",
        "| Hour | Metric | n CPC1 | n CPC5 | CPC1 med | CPC5 med | d | MW p | Direction |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    sub = contrasts[contrasts["grain"] == "subject"].copy()
    for _, row in sub.iterrows():
        if not bool(row.get("sign_audit")):
            continue
        match = row.get("direction_matches")
        mark = "yes" if match is True else ("no" if match is False else "-")
        lines.append(
            f"| {row['hour_bin']} | `{row['metric']}` | {int(row['n_cpc1'])} | {int(row['n_cpc5'])} | "
            f"{row['cpc1_median']:.4g} | {row['cpc5_median']:.4g} | "
            f"{row['cohens_d_cpc1_minus_cpc5']:.3g} | {row['mannwhitney_p']:.3g} | {mark} |"
        )
    lines += [
        "",
        "## Sign stability (testable hours only)",
        "",
        "| Grain | Metric | Hours | Direction match | Fraction | Hours MW p<0.05 | Median d |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    if stability.empty:
        lines.append("| - | - | - | - | - | - | - |")
    else:
        for _, row in stability.iterrows():
            lines.append(
                f"| {row['grain']} | `{row['metric']}` | {int(row['n_testable_hours'])} | "
                f"{int(row['n_direction_match'])} | {row['frac_direction_match']:.2f} | "
                f"{int(row['n_mw_p_lt_05'])} | {row['median_d']:.3g} |"
            )
    lines += [
        "",
        "This is a sign-stability audit, not a new confirmatory family.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--reuse-contrasts", action="store_true", help="Rebuild coverage/stability/md from existing hourly CSVs.")
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    out = cfg.output_dir
    if args.reuse_contrasts:
        runs = pd.read_csv(out / "hourly_strong_run_level.csv")
        subjects = pd.read_csv(out / "hourly_strong_subject_hour.csv")
        coverage = pd.read_csv(out / "hourly_strong_coverage.csv")
        contrasts = pd.read_csv(out / "hourly_strong_contrasts.csv")
        if "direction_matches" in contrasts.columns:
            contrasts["direction_matches"] = contrasts["direction_matches"].map(
                lambda v: True if str(v).lower() in {"true", "1"} else (False if str(v).lower() in {"false", "0"} else None)
            )
        if "sign_audit" in contrasts.columns:
            contrasts["sign_audit"] = contrasts["sign_audit"].map(lambda v: str(v).lower() in {"true", "1"})
    else:
        runs = _load_runs(cfg)
        metrics = [m for m, _, _ in PRIMARY + CONTROL]
        subjects = _subject_hour(runs, metrics)
        coverage = pd.concat(
            [_coverage(subjects, grain="subject", cfg=cfg), _coverage(runs, grain="recording", cfg=cfg)],
            ignore_index=True,
        )
        contrasts = pd.concat(
            [
                _hourly_contrasts(subjects, PRIMARY + CONTROL, grain="subject", cfg=cfg),
                _hourly_contrasts(runs, PRIMARY + CONTROL, grain="recording", cfg=cfg),
            ],
            ignore_index=True,
        )
        write_csv(out / "hourly_strong_run_level.csv", runs)
        write_csv(out / "hourly_strong_subject_hour.csv", subjects)
        write_csv(out / "hourly_strong_coverage.csv", coverage)
        write_csv(out / "hourly_strong_contrasts.csv", contrasts)
    stability = _stability(contrasts)
    write_csv(out / "hourly_strong_stability.csv", stability)
    md = _render(coverage=coverage, contrasts=contrasts, stability=stability, cfg=cfg)
    (out / "hourly_strong_part1.md").write_text(md, encoding="utf-8")
    write_json(
        out / "hourly_strong_part1_manifest.json",
        {
            "experiment": "COMA-HOURLY-STRONG-001",
            "grain_primary": "subject_median_within_clock_hour",
            "recording_level": "descriptive_only",
            "holm": False,
            "not": ["SL-004A", "inferential_hourly_p", "part2"],
            "part2_opened": False,
            "metrics_primary": [m for m, _, _ in PRIMARY],
            "n_runs": int(len(runs)),
        },
    )
    print(f"wrote {out / 'hourly_strong_part1.md'}", flush=True)
    print(coverage[coverage["grain"] == "subject"].to_string(index=False), flush=True)
    if not stability.empty:
        print(stability.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
