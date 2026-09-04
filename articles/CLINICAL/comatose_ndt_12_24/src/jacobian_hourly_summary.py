from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PART1_TIMELINE_DIR = ARTICLE_DIR / "results" / "timeline_analysis_20260524_part1_hourly12h_9d"
DEFAULT_PART2_TIMELINE_DIR = ARTICLE_DIR / "results" / "timeline_analysis_20260524_part2_hourly12h_9d"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "jacobian_hourly_20260524_combined_cpc15"
DEFAULT_GOOD_CPC = 1
DEFAULT_POOR_CPC = 5
TARGET_METRIC = "jacobian_fro_median"
HOURLY_BINS = tuple(f"{hour}_{hour + 1}h" for hour in range(12))


@dataclass(frozen=True)
class Config:
    part1_timeline_dir: Path
    part2_timeline_dir: Path
    output_dir: Path
    good_cpc: int
    poor_cpc: int
    metric: str


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Summarize pooled hour-by-hour Jacobian contrasts.")
    parser.add_argument("--part1-timeline-dir", type=Path, default=DEFAULT_PART1_TIMELINE_DIR)
    parser.add_argument("--part2-timeline-dir", type=Path, default=DEFAULT_PART2_TIMELINE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--good-cpc", type=int, default=DEFAULT_GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=DEFAULT_POOR_CPC)
    parser.add_argument("--metric", type=str, default=TARGET_METRIC)
    args = parser.parse_args()
    return Config(
        part1_timeline_dir=args.part1_timeline_dir,
        part2_timeline_dir=args.part2_timeline_dir,
        output_dir=args.output_dir,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        metric=args.metric,
    )


def bh_fdr(p_values: pd.Series) -> pd.Series:
    vals = pd.to_numeric(p_values, errors="coerce").to_numpy(dtype=float)
    out = np.full(vals.shape, np.nan, dtype=float)
    mask = np.isfinite(vals)
    if not mask.any():
        return pd.Series(out, index=p_values.index, dtype=float)
    valid = vals[mask]
    order = np.argsort(valid)
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(valid) + 1)
    q = valid * len(valid) / ranks
    q_sorted = np.minimum.accumulate(q[order][::-1])[::-1]
    q_final = np.empty_like(q_sorted)
    q_final[order] = np.clip(q_sorted, 0.0, 1.0)
    out[np.where(mask)[0]] = q_final
    return pd.Series(out, index=p_values.index, dtype=float)


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    if good.size < 2 or poor.size < 2:
        return float("nan")
    pooled = ((good.size - 1) * np.var(good, ddof=1) + (poor.size - 1) * np.var(poor, ddof=1)) / (good.size + poor.size - 2)
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(good) - np.mean(poor)) / np.sqrt(pooled))


def load_patient_bins(timeline_dir: Path, cohort_tag: str, config: Config) -> pd.DataFrame:
    frame = pd.read_csv(timeline_dir / "patient_timebin_summaries.csv")
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)])].copy()
    frame = frame[frame["time_bin"].isin(HOURLY_BINS)].copy()
    frame[config.metric] = pd.to_numeric(frame[config.metric], errors="coerce")
    frame["cohort_tag"] = cohort_tag
    return frame.reset_index(drop=True)


def combine_patient_bins(config: Config) -> pd.DataFrame:
    part1 = load_patient_bins(config.part1_timeline_dir, "part1", config)
    part2 = load_patient_bins(config.part2_timeline_dir, "part2", config)
    combined = pd.concat([part1, part2], ignore_index=True)
    duplicate_mask = combined.duplicated(["subject", "time_bin"], keep=False)
    if duplicate_mask.any():
        sample = combined.loc[duplicate_mask, ["subject", "time_bin", "cohort_tag"]].head(10).to_dict(orient="records")
        raise ValueError(f"Found overlapping subject/time_bin rows across part1/part2: {sample}")
    return combined.sort_values(["time_bin", "subject"]).reset_index(drop=True)


def summarize_hour(frame: pd.DataFrame, time_bin: str, config: Config) -> Dict[str, Any]:
    sub = frame[frame["time_bin"] == time_bin].copy()
    values = pd.to_numeric(sub[config.metric], errors="coerce")
    good = values[sub["cpc_numeric"] == float(config.good_cpc)].dropna().to_numpy(dtype=float)
    poor = values[sub["cpc_numeric"] == float(config.poor_cpc)].dropna().to_numpy(dtype=float)
    row: Dict[str, Any] = {
        "time_bin": time_bin,
        "hour_start": int(time_bin.split("_")[0]),
        "hour_end": int(time_bin.split("_")[1].replace("h", "")),
        "n_cpc1": int(good.size),
        "n_cpc5": int(poor.size),
        "cpc1_median": float(np.median(good)) if good.size else float("nan"),
        "cpc5_median": float(np.median(poor)) if poor.size else float("nan"),
        "cohens_d": cohens_d(good, poor),
    }
    if good.size and poor.size:
        _, p_value = stats.mannwhitneyu(good, poor, alternative="two-sided")
        row["mannwhitney_p"] = float(p_value)
    else:
        row["mannwhitney_p"] = float("nan")
    return row


def build_summary(frame: pd.DataFrame, config: Config) -> pd.DataFrame:
    summary = pd.DataFrame([summarize_hour(frame, time_bin, config) for time_bin in HOURLY_BINS])
    summary["bh_fdr_q"] = bh_fdr(summary["mannwhitney_p"])
    summary["abs_d"] = pd.to_numeric(summary["cohens_d"], errors="coerce").abs()
    summary["direction"] = np.where(summary["cohens_d"] >= 0.0, "higher in CPC1", "higher in CPC5")
    return summary


def find_critical_points(summary: pd.DataFrame) -> Dict[str, Any]:
    significant = summary[pd.to_numeric(summary["bh_fdr_q"], errors="coerce") < 0.05].copy()
    critical: Dict[str, Any] = {}
    if not significant.empty:
        first = significant.sort_values("hour_start").iloc[0]
        strongest = significant.sort_values("abs_d", ascending=False).iloc[0]
        critical["first_fdr_significant_bin"] = first["time_bin"]
        critical["first_fdr_significant_d"] = float(first["cohens_d"])
        critical["strongest_abs_d_bin"] = strongest["time_bin"]
        critical["strongest_abs_d"] = float(strongest["cohens_d"])
    else:
        strongest = summary.sort_values("abs_d", ascending=False).iloc[0]
        critical["first_fdr_significant_bin"] = None
        critical["first_fdr_significant_d"] = None
        critical["strongest_abs_d_bin"] = strongest["time_bin"]
        critical["strongest_abs_d"] = float(strongest["cohens_d"])
    return critical


def write_markdown(summary: pd.DataFrame, critical: Dict[str, Any], config: Config) -> str:
    lines = [
        "# Hourly Jacobian Frobenius Summary",
        "",
        f"- metric: `{config.metric}`",
        f"- comparison: `CPC {config.good_cpc}` vs `CPC {config.poor_cpc}`",
        "",
        "| Time bin | n CPC1 | n CPC5 | CPC1 median | CPC5 median | d | p | q |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['time_bin']} | {int(row['n_cpc1'])} | {int(row['n_cpc5'])} | "
            f"{row['cpc1_median']:.3f} | {row['cpc5_median']:.3f} | "
            f"{row['cohens_d']:+.3f} | {row['mannwhitney_p']:.3g} | {row['bh_fdr_q']:.3g} |"
        )
    lines.extend(
        [
            "",
            "## Critical points",
            "",
            f"- first FDR-significant bin: `{critical['first_fdr_significant_bin']}`",
            f"- strongest absolute effect bin: `{critical['strongest_abs_d_bin']}` (`d = {critical['strongest_abs_d']:+.3f}`)",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    combined = combine_patient_bins(config)
    summary = build_summary(combined, config)
    critical = find_critical_points(summary)

    combined.to_csv(config.output_dir / "jacobian_hourly_patient_timebin_combined.csv", index=False)
    summary.to_csv(config.output_dir / "jacobian_hourly_summary.csv", index=False)
    (config.output_dir / "jacobian_hourly_summary.md").write_text(write_markdown(summary, critical, config), encoding="utf-8")
    (config.output_dir / "jacobian_hourly_manifest.json").write_text(
        json.dumps(
            {
                "part1_timeline_dir": str(config.part1_timeline_dir),
                "part2_timeline_dir": str(config.part2_timeline_dir),
                "good_cpc": config.good_cpc,
                "poor_cpc": config.poor_cpc,
                "metric": config.metric,
                "hourly_bins": list(HOURLY_BINS),
                "critical_points": critical,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote hourly Jacobian summary to {config.output_dir}")


if __name__ == "__main__":
    main()
