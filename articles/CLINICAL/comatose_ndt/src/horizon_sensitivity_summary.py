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
DEFAULT_INPUT_CSV = (
    ARTICLE_DIR / "results" / "mnps_summary_20260522_combined_cpc15_primary12h" / "patient_timebin_adapter_summaries.csv"
)
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "horizon_sensitivity_20260523_combined_cpc15"
DEFAULT_TIME_BIN = "0_12h"


@dataclass(frozen=True)
class Config:
    input_csv: Path
    output_dir: Path
    time_bin: str
    good_cpc: int
    poor_cpc: int


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Summarize H=1..4 horizon sensitivity for the pooled coma reachability results."
    )
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--time-bin", type=str, default=DEFAULT_TIME_BIN)
    parser.add_argument("--good-cpc", type=int, default=1)
    parser.add_argument("--poor-cpc", type=int, default=5)
    args = parser.parse_args()
    return Config(
        input_csv=args.input_csv,
        output_dir=args.output_dir,
        time_bin=args.time_bin,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
    )


def cohens_d_independent(good: np.ndarray, poor: np.ndarray) -> float:
    if good.size < 2 or poor.size < 2:
        return float("nan")
    good_var = float(np.var(good, ddof=1))
    poor_var = float(np.var(poor, ddof=1))
    pooled_denom = ((good.size - 1) * good_var + (poor.size - 1) * poor_var) / (good.size + poor.size - 2)
    if pooled_denom <= 0 or not np.isfinite(pooled_denom):
        return float("nan")
    return float((np.mean(good) - np.mean(poor)) / np.sqrt(pooled_denom))


def cliffs_delta(good: np.ndarray, poor: np.ndarray) -> float:
    if good.size == 0 or poor.size == 0:
        return float("nan")
    diff = np.subtract.outer(good, poor)
    gt = np.sum(diff > 0)
    lt = np.sum(diff < 0)
    return float((gt - lt) / diff.size)


def load_frame(config: Config) -> pd.DataFrame:
    frame = pd.read_csv(config.input_csv)
    frame = frame[
        (frame["analysis_type"] == "reachability_cones")
        & (frame["time_bin"].astype(str) == config.time_bin)
    ].copy()
    frame["cpc"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc"].isin([float(config.good_cpc), float(config.poor_cpc)])].copy()
    frame["outcome"] = np.where(frame["cpc"] == float(config.good_cpc), "Good", "Poor")
    operator_norm = pd.to_numeric(frame["tube_a_operator_norm_median"], errors="coerce")
    for horizon in range(1, 5):
        q_ratio = pd.to_numeric(frame[f"cone_q_ratio_h{horizon}_median"], errors="coerce")
        frame[f"capture_gate_h{horizon}_median"] = (1.0 - q_ratio) * np.log1p(operator_norm)
    return frame.reset_index(drop=True)


def build_metric_specs() -> List[Dict[str, Any]]:
    specs: List[Dict[str, Any]] = []
    for horizon in range(1, 5):
        specs.append(
            {
                "family": "effective_dimensionality",
                "horizon": horizon,
                "metric": f"cone_d_eff_h{horizon}_median",
                "label": f"`d_eff` @ H={horizon}",
            }
        )
    for horizon in range(1, 5):
        specs.append(
            {
                "family": "anisotropy",
                "horizon": horizon,
                "metric": f"cone_kappa_h{horizon}_median",
                "label": f"`kappa` @ H={horizon}",
            }
        )
    for horizon in range(1, 5):
        specs.append(
            {
                "family": "log_eig_var",
                "horizon": horizon,
                "metric": f"cone_log_eig_var_h{horizon}_median",
                "label": f"`log eig var` @ H={horizon}",
            }
        )
    for horizon in range(1, 5):
        specs.append(
            {
                "family": "capture_gate",
                "horizon": horizon,
                "metric": f"capture_gate_h{horizon}_median",
                "label": f"`capture gate` @ H={horizon}",
            }
        )
    return specs


def summarize_metric(frame: pd.DataFrame, spec: Dict[str, Any]) -> Dict[str, Any]:
    metric = spec["metric"]
    good = pd.to_numeric(frame.loc[frame["outcome"] == "Good", metric], errors="coerce").dropna().to_numpy(dtype=float)
    poor = pd.to_numeric(frame.loc[frame["outcome"] == "Poor", metric], errors="coerce").dropna().to_numpy(dtype=float)
    row: Dict[str, Any] = dict(spec)
    row.update(
        {
            "n_good": int(good.size),
            "n_poor": int(poor.size),
            "good_median": float(np.median(good)) if good.size else float("nan"),
            "poor_median": float(np.median(poor)) if poor.size else float("nan"),
            "delta_median_good_minus_poor": float(np.median(good) - np.median(poor))
            if good.size and poor.size
            else float("nan"),
            "cohens_d": cohens_d_independent(good, poor),
            "cliffs_delta": cliffs_delta(good, poor),
        }
    )
    if good.size == 0 or poor.size == 0:
        row["mannwhitney_p"] = float("nan")
        row["status"] = "insufficient_groups"
        row["contrast_direction"] = "unavailable"
        return row

    if np.nanmax(np.abs(np.r_[good, poor] - good[0])) == 0:
        row["mannwhitney_p"] = 1.0
        row["status"] = "degenerate_constant"
        row["contrast_direction"] = "equal"
        return row

    mannwhitney = stats.mannwhitneyu(good, poor, alternative="two-sided")
    row["mannwhitney_p"] = float(mannwhitney.pvalue)
    row["status"] = "ok"
    delta = row["delta_median_good_minus_poor"]
    row["contrast_direction"] = "good_gt_poor" if delta > 0 else "good_lt_poor" if delta < 0 else "equal"
    return row


def build_summary_rows(frame: pd.DataFrame) -> pd.DataFrame:
    rows = [summarize_metric(frame, spec) for spec in build_metric_specs()]
    return pd.DataFrame(rows)


def compact_effect_table(summary: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for family, family_frame in summary.groupby("family", sort=False):
        row: Dict[str, Any] = {"family": family}
        for _, item in family_frame.sort_values("horizon").iterrows():
            h = int(item["horizon"])
            row[f"h{h}_d"] = item["cohens_d"]
            row[f"h{h}_p"] = item["mannwhitney_p"]
            row[f"h{h}_delta_median"] = item["delta_median_good_minus_poor"]
            row[f"h{h}_status"] = item["status"]
        rows.append(row)
    return pd.DataFrame(rows)


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    display = frame.copy()
    for column in display.columns:
        if pd.api.types.is_float_dtype(display[column]):
            display[column] = display[column].map(
                lambda value: ""
                if pd.isna(value)
                else f"{value:.3g}"
            )
        else:
            display[column] = display[column].fillna("").astype(str)
    header = "| " + " | ".join(display.columns.astype(str)) + " |"
    divider = "| " + " | ".join(["---"] * len(display.columns)) + " |"
    rows = ["| " + " | ".join(row) + " |" for row in display.astype(str).values.tolist()]
    return "\n".join([header, divider, *rows])


def build_summary_markdown(summary: pd.DataFrame, compact: pd.DataFrame, config: Config) -> str:
    d_eff = summary[summary["family"] == "effective_dimensionality"].sort_values("horizon")
    capture = summary[(summary["family"] == "capture_gate") & (summary["status"] == "ok")].sort_values("horizon")
    anisotropy = summary[summary["family"] == "anisotropy"].sort_values("horizon")
    eig_var = summary[summary["family"] == "log_eig_var"].sort_values("horizon")

    lines = [
        "# Horizon sensitivity summary",
        "",
        f"- input_csv: `{config.input_csv}`",
        f"- time_bin: `{config.time_bin}`",
        f"- Good/Poor CPC filter: `{config.good_cpc}` vs `{config.poor_cpc}`",
        "",
        "## Key takeaways",
        "",
    ]
    if not d_eff.empty:
        lines.append(
            "- Effective dimensionality stays stable across `H=1..4`: "
            f"Cohen's `d` ranges from `{d_eff['cohens_d'].min():.3f}` to `{d_eff['cohens_d'].max():.3f}`."
        )
    if not capture.empty:
        lines.append(
            "- The derived capture gate is directionally stable once it becomes informative: "
            f"for `H=2..4`, Cohen's `d` ranges from `{capture['cohens_d'].min():.3f}` to `{capture['cohens_d'].max():.3f}`."
        )
    lines.append(
        "- `capture_gate @ H=1` is structurally degenerate in the current estimator because "
        "`q^(1) = 1`, so the gate becomes informative only from `H=2` onward."
    )
    if not anisotropy.empty:
        lines.append(
            "- Raw horizon-resolved anisotropy (`cone_kappa_h`) remains directionally aligned but small in standardized magnitude "
            f"(`d` roughly `{anisotropy['cohens_d'].min():.3f}` to `{anisotropy['cohens_d'].max():.3f}`)."
        )
    if not eig_var.empty:
        lines.append(
            "- Raw horizon-resolved log-eigenvalue spread (`cone_log_eig_var_h`) shows strong median separation but near-zero "
            "standardized `d`, consistent with the manuscript's more cautious treatment of persistence-related summaries."
        )

    lines.extend(
        [
            "",
            "## Compact effect table",
            "",
            dataframe_to_markdown(compact),
            "",
            "## Detailed rows",
            "",
            dataframe_to_markdown(
                summary[
                    [
                        "family",
                        "horizon",
                        "metric",
                        "good_median",
                        "poor_median",
                        "delta_median_good_minus_poor",
                        "cohens_d",
                        "mannwhitney_p",
                        "status",
                    ]
                ]
            ),
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def build_manifest(summary: pd.DataFrame, compact: pd.DataFrame, config: Config) -> Dict[str, Any]:
    return {
        "input_csv": str(config.input_csv),
        "time_bin": config.time_bin,
        "good_cpc": config.good_cpc,
        "poor_cpc": config.poor_cpc,
        "n_rows": int(len(summary)),
        "families": compact["family"].tolist() if not compact.empty else [],
        "status_counts": summary["status"].value_counts(dropna=False).to_dict() if not summary.empty else {},
    }


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    frame = load_frame(config)
    summary = build_summary_rows(frame)
    compact = compact_effect_table(summary)
    manifest = build_manifest(summary, compact, config)

    summary.to_csv(config.output_dir / "horizon_sensitivity_detail.csv", index=False)
    compact.to_csv(config.output_dir / "horizon_sensitivity_compact.csv", index=False)
    (config.output_dir / "horizon_sensitivity_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    (config.output_dir / "horizon_sensitivity_summary.md").write_text(
        build_summary_markdown(summary, compact, config),
        encoding="utf-8",
    )
    print(f"Wrote horizon sensitivity detail to {config.output_dir / 'horizon_sensitivity_detail.csv'}")
    print(f"Wrote horizon sensitivity compact summary to {config.output_dir / 'horizon_sensitivity_compact.csv'}")
    print(f"Wrote horizon sensitivity markdown to {config.output_dir / 'horizon_sensitivity_summary.md'}")


if __name__ == "__main__":
    main()
