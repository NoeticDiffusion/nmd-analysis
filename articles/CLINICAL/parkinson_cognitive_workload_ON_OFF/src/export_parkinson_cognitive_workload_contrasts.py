from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon

from parkinson_cognitive_workload_support import (
    EVENT_CONTRASTS_CSV,
    MANIFEST_JSON,
    NUMERIC_METRIC_COLUMNS,
    SUBJECT_METRICS_CSV,
    bh_fdr,
    cohens_d,
    cohens_dz,
    ensure_dir,
    write_json,
)


WRAPPER_SUMMARY_FILENAME = "wrapper_event_summary.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export Parkinson cognitive workload event contrasts."
    )
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def load_subject_long(input_dir: Path) -> pd.DataFrame:
    subject_frame = pd.read_csv(input_dir / SUBJECT_METRICS_CSV, low_memory=False)
    metric_cols = [metric for metric in NUMERIC_METRIC_COLUMNS if metric in subject_frame.columns]
    long_frame = subject_frame.melt(
        id_vars=[column for column in subject_frame.columns if column not in metric_cols],
        value_vars=metric_cols,
        var_name="metric",
        value_name="value",
    )
    long_frame["value"] = pd.to_numeric(long_frame["value"], errors="coerce")
    return long_frame.dropna(subset=["value"]).reset_index(drop=True)


def paired_contrast_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    group_cols = [
        "analysis_type",
        "network",
        "dims",
        "segment_kind",
        "segment_family",
        "segment_label",
        "requested_coordinate_contract",
        "resolved_coordinate_contract",
        "metric",
    ]
    parkinson = frame[(frame["group"] == "Parkinson") & (frame["condition"].isin(["OFF", "ON"]))].copy()
    for keys, group in parkinson.groupby(group_cols, dropna=False):
        pivot = group.pivot_table(index="subject_id", columns="condition", values="value", aggfunc="median")
        if "OFF" not in pivot.columns or "ON" not in pivot.columns:
            continue
        paired = pivot.dropna(subset=["OFF", "ON"])
        if paired.shape[0] < 3:
            continue
        diff = paired["ON"].to_numpy(dtype=float) - paired["OFF"].to_numpy(dtype=float)
        try:
            p_value = float(wilcoxon(diff, alternative="two-sided", zero_method="wilcox").pvalue)
        except ValueError:
            p_value = 1.0
        rows.append(
            {
                "contrast_name": "Parkinson_OFF_vs_ON",
                "analysis_type": keys[0],
                "network": keys[1],
                "dims": keys[2],
                "segment_kind": keys[3],
                "segment_family": keys[4],
                "segment_label": keys[5],
                "requested_coordinate_contract": keys[6],
                "resolved_coordinate_contract": keys[7],
                "metric": keys[8],
                "contrast_type": "paired",
                "n": int(paired.shape[0]),
                "left_median": float(np.median(paired["OFF"].to_numpy(dtype=float))),
                "right_median": float(np.median(paired["ON"].to_numpy(dtype=float))),
                "effect_size": cohens_dz(diff),
                "p_value": p_value,
            }
        )
    return rows


def unpaired_contrast_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    group_cols = [
        "analysis_type",
        "network",
        "dims",
        "segment_kind",
        "segment_family",
        "segment_label",
        "requested_coordinate_contract",
        "resolved_coordinate_contract",
        "metric",
    ]
    controls = frame[(frame["group"] == "Control") & (frame["condition"] == "not_applicable")].copy()
    comparisons = [("Control_vs_Parkinson_OFF", "OFF"), ("Control_vs_Parkinson_ON", "ON")]
    for contrast_name, pd_condition in comparisons:
        pd_frame = frame[(frame["group"] == "Parkinson") & (frame["condition"] == pd_condition)].copy()
        merged = pd.concat([controls, pd_frame], ignore_index=True)
        for keys, group in merged.groupby(group_cols, dropna=False):
            left = pd.to_numeric(
                group.loc[(group["group"] == "Control") & (group["condition"] == "not_applicable"), "value"],
                errors="coerce",
            ).dropna()
            right = pd.to_numeric(
                group.loc[(group["group"] == "Parkinson") & (group["condition"] == pd_condition), "value"],
                errors="coerce",
            ).dropna()
            if left.shape[0] < 3 or right.shape[0] < 3:
                continue
            rows.append(
                {
                    "contrast_name": contrast_name,
                    "analysis_type": keys[0],
                    "network": keys[1],
                    "dims": keys[2],
                    "segment_kind": keys[3],
                    "segment_family": keys[4],
                    "segment_label": keys[5],
                    "requested_coordinate_contract": keys[6],
                    "resolved_coordinate_contract": keys[7],
                    "metric": keys[8],
                    "contrast_type": "unpaired",
                    "n_left": int(left.shape[0]),
                    "n_right": int(right.shape[0]),
                    "left_median": float(np.median(left.to_numpy(dtype=float))),
                    "right_median": float(np.median(right.to_numpy(dtype=float))),
                    "effect_size": cohens_d(left.to_numpy(dtype=float), right.to_numpy(dtype=float)),
                    "p_value": float(mannwhitneyu(left, right, alternative="two-sided").pvalue),
                }
            )
    return rows


def apply_fdr(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        frame["q_value"] = pd.Series(dtype=float)
        return frame
    out = frame.copy()
    out["q_value"] = np.nan
    for _, idx in out.groupby(["contrast_name", "analysis_type"], dropna=False).groups.items():
        block = out.loc[list(idx)].copy()
        out.loc[block.index, "q_value"] = bh_fdr(block["p_value"]).to_numpy(dtype=float)
    return out.sort_values(
        ["contrast_name", "q_value", "p_value", "analysis_type", "segment_family", "segment_label", "network", "metric"],
        na_position="last",
    ).reset_index(drop=True)


def build_summary(event_contrasts: pd.DataFrame) -> str:
    lines = ["# Parkinson cognitive workload wrapper summary", ""]
    if event_contrasts.empty:
        lines.extend(["No event contrast rows were produced.", ""])
        return "\n".join(lines)
    for contrast_name in ["Parkinson_OFF_vs_ON", "Control_vs_Parkinson_OFF", "Control_vs_Parkinson_ON"]:
        block = event_contrasts[event_contrasts["contrast_name"] == contrast_name].copy()
        if block.empty:
            continue
        block["abs_effect_size"] = pd.to_numeric(block["effect_size"], errors="coerce").abs()
        block = block.sort_values(["q_value", "p_value", "abs_effect_size"], ascending=[True, True, False], na_position="last")
        lines.append(f"## {contrast_name}")
        lines.append("")
        for _, row in block.head(8).iterrows():
            lines.append(
                f"- `{row['analysis_type']}` / `{row['segment_label']}` / `{row['network']}` / `{row['metric']}`: "
                f"d={row['effect_size']:.3f}, p={row['p_value']:.4g}, q={row['q_value']:.4g}"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)
    event_long = load_subject_long(args.input_dir)
    contrast_rows = paired_contrast_rows(event_long) + unpaired_contrast_rows(event_long)
    event_contrasts = apply_fdr(pd.DataFrame(contrast_rows))
    event_contrasts.to_csv(args.output_dir / EVENT_CONTRASTS_CSV, index=False)
    (args.output_dir / WRAPPER_SUMMARY_FILENAME).write_text(build_summary(event_contrasts), encoding="utf-8")
    write_json(
        args.output_dir / MANIFEST_JSON,
        {
            "input_dir": str(args.input_dir),
            "output_dir": str(args.output_dir),
            "event_contrasts": str(args.output_dir / EVENT_CONTRASTS_CSV),
            "n_rows": int(len(event_contrasts)),
        },
    )


if __name__ == "__main__":
    main()
