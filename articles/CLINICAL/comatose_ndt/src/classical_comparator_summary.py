from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy import stats


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TIMELINE_DIR = ARTICLE_DIR / "results" / "timeline_analysis_20260517_cpc15_primary12h"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "classical_comparators_20260518_cpc15"
PRIMARY_TIME_BIN = "0_12h"
GOOD_CPC = 1
POOR_CPC = 5

COMPARATOR_SPECS = [
    ("MNPS 3D", "mnps_path_length", "MNPS path length"),
    ("MNPS 3D", "mnps_step_norm_median", "MNPS step norm"),
    ("MNPS 3D", "mnps_displacement", "MNPS displacement"),
    ("MNPS 9D", "coords_9d_global_std_mean", "9D global std mean"),
    ("MNJ", "jacobian_fro_median", "MNJ Frobenius norm"),
    ("MNJ", "jacobian_spectral_radius_median", "MNJ spectral radius"),
    ("MNJ", "jacobian_trace_median", "MNJ trace"),
    ("MNJ", "jacobian_condition_median", "MNJ condition"),
]

UNAVAILABLE_NOTES = {
    "coords_9d_global_std_mean": (
        "9D summaries were omitted from the locked export because the upstream ingest used a temporary "
        "stability override with `mnps_9d.enabled: false` after duplicated / degenerate 9D coordinate columns "
        "triggered a fail-fast validation stop. This was a data-integrity safeguard to avoid silently writing "
        "misleading 9D Jacobian / trajectory summaries, not evidence that 9D lacks value."
    )
}


@dataclass(frozen=True)
class Config:
    timeline_dir: Path
    output_dir: Path
    primary_time_bin: str
    good_cpc: int
    poor_cpc: int


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Summarize exploratory classical MNPS/MNJ comparator metrics.")
    parser.add_argument("--timeline-dir", type=Path, default=DEFAULT_TIMELINE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--primary-time-bin", type=str, default=PRIMARY_TIME_BIN)
    parser.add_argument("--good-cpc", type=int, default=GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=POOR_CPC)
    args = parser.parse_args()
    return Config(
        timeline_dir=args.timeline_dir,
        output_dir=args.output_dir,
        primary_time_bin=args.primary_time_bin,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
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


def load_frame(config: Config) -> pd.DataFrame:
    frame = pd.read_csv(config.timeline_dir / "patient_timebin_summaries.csv")
    frame = frame[frame["time_bin"] == config.primary_time_bin].copy()
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)])].copy()
    return frame.reset_index(drop=True)


def build_summary(frame: pd.DataFrame, config: Config) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for family, metric, label in COMPARATOR_SPECS:
        if metric not in frame.columns:
            rows.append(
                {
                    "family": family,
                    "metric": metric,
                    "label": label,
                    "status": "missing_column",
                    "note": UNAVAILABLE_NOTES.get(metric, ""),
                }
            )
            continue
        values = pd.to_numeric(frame[metric], errors="coerce")
        good = values[frame["cpc_numeric"] == float(config.good_cpc)].dropna().to_numpy(dtype=float)
        poor = values[frame["cpc_numeric"] == float(config.poor_cpc)].dropna().to_numpy(dtype=float)
        if good.size == 0 or poor.size == 0:
            rows.append(
                {
                    "family": family,
                    "metric": metric,
                    "label": label,
                    "status": "unavailable",
                    "n_cpc1": int(good.size),
                    "n_cpc5": int(poor.size),
                    "note": UNAVAILABLE_NOTES.get(metric, ""),
                }
            )
            continue
        u_stat, p_value = stats.mannwhitneyu(good, poor, alternative="two-sided")
        rows.append(
            {
                "family": family,
                "metric": metric,
                "label": label,
                "status": "ok",
                "n_cpc1": int(good.size),
                "n_cpc5": int(poor.size),
                "cpc1_median": float(np.median(good)),
                "cpc5_median": float(np.median(poor)),
                "cohens_d": cohens_d(good, poor),
                "mannwhitney_u": float(u_stat),
                "mannwhitney_p": float(p_value),
                "note": "",
            }
        )
    summary = pd.DataFrame(rows)
    ok_mask = summary["status"] == "ok"
    if ok_mask.any() and "mannwhitney_p" in summary.columns:
        summary.loc[ok_mask, "bh_fdr_q"] = bh_fdr(summary.loc[ok_mask, "mannwhitney_p"])
    if ok_mask.any() and "cohens_d" in summary.columns:
        summary.loc[ok_mask, "abs_d"] = pd.to_numeric(summary.loc[ok_mask, "cohens_d"], errors="coerce").abs()
    return summary


def write_markdown(summary: pd.DataFrame, config: Config) -> str:
    lines = [
        "# Classical Comparator Summary",
        "",
        f"- primary time bin: `{config.primary_time_bin}`",
        f"- comparison: `CPC {config.good_cpc}` vs `CPC {config.poor_cpc}`",
        "",
        "## Available comparator metrics",
        "",
    ]
    ok = summary[summary["status"] == "ok"].copy()
    if "abs_d" not in ok.columns:
        ok["abs_d"] = np.nan
    for _, row in ok.sort_values(["family", "abs_d"], ascending=[True, False]).iterrows():
        lines.append(
            f"- `{row['label']}` (`{row['metric']}`): medians `{row['cpc1_median']:.3f}` vs `{row['cpc5_median']:.3f}`, "
            f"Cohen's `d = {row['cohens_d']:.3f}`, Mann-Whitney `p = {row['mannwhitney_p']:.3g}`, BH-FDR `q = {row['bh_fdr_q']:.3g}`"
        )
    unavailable = summary[summary["status"] != "ok"].copy()
    if not unavailable.empty:
        lines.extend(["", "## Unavailable in this bundle", ""])
        for _, row in unavailable.iterrows():
            suffix = f" {row['note']}" if str(row.get("note", "")).strip() else ""
            lines.append(f"- `{row['label']}` (`{row['metric']}`): `{row['status']}`.{suffix}")
    return "\n".join(lines) + "\n"


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    frame = load_frame(config)
    summary = build_summary(frame, config)
    summary.to_csv(config.output_dir / "classical_comparator_summary.csv", index=False)
    (config.output_dir / "classical_comparator_summary.md").write_text(write_markdown(summary, config), encoding="utf-8")
    (config.output_dir / "classical_comparator_manifest.json").write_text(
        json.dumps(
            {
                "timeline_dir": str(config.timeline_dir),
                "primary_time_bin": config.primary_time_bin,
                "good_cpc": config.good_cpc,
                "poor_cpc": config.poor_cpc,
                "comparator_specs": COMPARATOR_SPECS,
                "unavailable_notes": UNAVAILABLE_NOTES,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote classical comparator summary to {config.output_dir}")


if __name__ == "__main__":
    main()
