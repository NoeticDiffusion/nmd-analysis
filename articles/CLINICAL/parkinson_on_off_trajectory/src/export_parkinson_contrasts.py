from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon

from parkinson_trajectory_support import (
    ESB_CONTRASTS_CSV,
    ESB_SUBJECT_SCORES_CSV,
    ESB_TEMPLATE_CSV,
    EVENT_CONTRASTS_CSV,
    EVENT_METRIC_DIR,
    RESULTS_DIR,
    SUBJECT_METRICS_CSV,
    bh_fdr,
    cohens_d,
    cohens_dz,
    ensure_dir,
)


EVENT_METRICS = [
    "speed_median",
    "curvature_median",
    "tortuosity",
    "path_length",
    "peak_displacement",
    "recovery_residual",
    "hysteresis_area_md",
    "hysteresis_area_me",
    "hysteresis_area_de",
    "hysteresis_area_mean",
    "entropy_rate",
    "irreversibility",
    "entropy_production",
    "self_loop_rate",
    "transition_sparsity",
    "noetic_action",
    "noetic_action_kinetic",
    "noetic_action_jerk",
    "noetic_action_potential",
]
ESB_COMPONENT_METRICS = {
    "tortuosity": "z_tortuosity",
    "hysteresis_area_mean": "z_hysteresis",
    "recovery_residual": "z_recovery",
}
ESB_SCORE_METRICS = ["trajectory_esb2", "trajectory_esb3", "z_tortuosity", "z_hysteresis", "z_recovery"]
WRAPPER_SUMMARY_FILENAME = "wrapper_event_summary.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export exploratory Parkinson ON/OFF contrasts and trajectory ESB scores."
    )
    parser.add_argument("--input-dir", type=Path, default=EVENT_METRIC_DIR)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    return parser.parse_args()


def load_subject_long(input_dir: Path) -> pd.DataFrame:
    subject_frame = pd.read_csv(input_dir / SUBJECT_METRICS_CSV, low_memory=False)
    metric_cols = [metric for metric in EVENT_METRICS if metric in subject_frame.columns]
    long_frame = subject_frame.melt(
        id_vars=[column for column in subject_frame.columns if column not in metric_cols],
        value_vars=metric_cols,
        var_name="metric",
        value_name="value",
    )
    long_frame["value"] = pd.to_numeric(long_frame["value"], errors="coerce")
    long_frame = long_frame.dropna(subset=["value"]).reset_index(drop=True)
    return long_frame


def paired_contrast_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    group_cols = [
        "analysis_type",
        "network",
        "dims",
        "segment_kind",
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
                "segment_label": keys[4],
                "requested_coordinate_contract": keys[5],
                "resolved_coordinate_contract": keys[6],
                "metric": keys[7],
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
        "segment_label",
        "requested_coordinate_contract",
        "resolved_coordinate_contract",
        "metric",
    ]
    controls = frame[(frame["group"] == "Control") & (frame["condition"] == "not_applicable")].copy()
    comparisons = [
        ("Control_vs_Parkinson_OFF", "OFF"),
        ("Control_vs_Parkinson_ON", "ON"),
    ]
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
            p_value = float(mannwhitneyu(left, right, alternative="two-sided").pvalue)
            rows.append(
                {
                    "contrast_name": contrast_name,
                    "analysis_type": keys[0],
                    "network": keys[1],
                    "dims": keys[2],
                    "segment_kind": keys[3],
                    "segment_label": keys[4],
                    "requested_coordinate_contract": keys[5],
                    "resolved_coordinate_contract": keys[6],
                    "metric": keys[7],
                    "contrast_type": "unpaired",
                    "n_left": int(left.shape[0]),
                    "n_right": int(right.shape[0]),
                    "left_median": float(np.median(left.to_numpy(dtype=float))),
                    "right_median": float(np.median(right.to_numpy(dtype=float))),
                    "effect_size": cohens_d(left.to_numpy(dtype=float), right.to_numpy(dtype=float)),
                    "p_value": p_value,
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
        ["contrast_name", "q_value", "p_value", "analysis_type", "segment_label", "network", "metric"],
        na_position="last",
    ).reset_index(drop=True)


def build_esb_scores(subject_frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    event_frame = subject_frame[
        (subject_frame["segment_kind"] == "event")
        & (pd.to_numeric(subject_frame["dims"], errors="coerce") == 3)
        & subject_frame["segment_label"].isin(["standard_tone", "novel_tone", "target_tone"])
    ].copy()
    if event_frame.empty:
        return pd.DataFrame(), pd.DataFrame()

    template_rows: list[dict[str, Any]] = []
    score_rows: list[dict[str, Any]] = []
    context_cols = ["analysis_type", "network", "segment_label"]
    for context, group in event_frame.groupby(context_cols, dropna=False):
        controls = group[group["group"] == "Control"].copy()
        if controls.shape[0] < 2:
            continue
        template_rows.append(
            {
                "analysis_type": context[0],
                "network": context[1],
                "segment_label": context[2],
                "n_controls": int(controls.shape[0]),
                **{
                    f"{metric}_median": float(pd.to_numeric(controls[metric], errors="coerce").median())
                    for metric in ESB_COMPONENT_METRICS
                },
                **{
                    f"{metric}_mad": float(
                        np.median(
                            np.abs(
                                pd.to_numeric(controls[metric], errors="coerce").dropna().to_numpy(dtype=float)
                                - float(pd.to_numeric(controls[metric], errors="coerce").median())
                            )
                        )
                    )
                    for metric in ESB_COMPONENT_METRICS
                },
            }
        )
        for _, row in group.iterrows():
            if row["group"] == "Control" and controls.shape[0] >= 3:
                template = controls[controls["subject_id"] != row["subject_id"]].copy()
                if template.shape[0] < 2:
                    template = controls.copy()
            else:
                template = controls.copy()
            values = {}
            z_values = {}
            for metric, z_name in ESB_COMPONENT_METRICS.items():
                template_values = pd.to_numeric(template[metric], errors="coerce").dropna().to_numpy(dtype=float)
                if template_values.size < 2:
                    values[z_name] = float("nan")
                    z_values[z_name] = float("nan")
                    continue
                median = float(np.median(template_values))
                mad = float(np.median(np.abs(template_values - median)))
                raw_value = float(pd.to_numeric(pd.Series([row[metric]]), errors="coerce").iloc[0])
                z_score = (raw_value - median) / max(mad, 0.1)
                values[z_name] = z_score
                z_values[z_name] = z_score
            z_t = z_values["z_tortuosity"]
            z_h = z_values["z_hysteresis"]
            z_r = z_values["z_recovery"]
            trajectory_esb2 = math.sqrt((z_t * z_t + z_h * z_h) / 2.0) if np.isfinite(z_t) and np.isfinite(z_h) else float("nan")
            trajectory_esb3 = (
                math.sqrt((z_t * z_t + z_h * z_h + z_r * z_r) / 3.0)
                if np.isfinite(z_t) and np.isfinite(z_h) and np.isfinite(z_r)
                else float("nan")
            )
            score_rows.append(
                {
                    **{column: row[column] for column in row.index if column not in ESB_COMPONENT_METRICS},
                    **values,
                    "trajectory_esb2": trajectory_esb2,
                    "trajectory_esb3": trajectory_esb3,
                    "template_n": int(template.shape[0]),
                }
            )
    return pd.DataFrame(template_rows), pd.DataFrame(score_rows)


def esb_contrast_rows(score_frame: pd.DataFrame) -> pd.DataFrame:
    if score_frame.empty:
        return pd.DataFrame()
    score_long = score_frame.melt(
        id_vars=[column for column in score_frame.columns if column not in ESB_SCORE_METRICS],
        value_vars=ESB_SCORE_METRICS,
        var_name="metric",
        value_name="value",
    )
    score_long["value"] = pd.to_numeric(score_long["value"], errors="coerce")
    score_long = score_long.dropna(subset=["value"]).reset_index(drop=True)
    contrast_rows = paired_contrast_rows(score_long) + unpaired_contrast_rows(score_long)
    contrast_frame = apply_fdr(pd.DataFrame(contrast_rows))
    return contrast_frame


def build_wrapper_summary(event_contrasts: pd.DataFrame, esb_contrasts: pd.DataFrame) -> str:
    lines = ["# Parkinson wrapper event summary", ""]
    if event_contrasts.empty:
        lines.extend(["No event contrast rows were produced.", ""])
    else:
        paired = event_contrasts[event_contrasts["contrast_name"] == "Parkinson_OFF_vs_ON"].copy()
        top_paired = paired.sort_values(["q_value", "p_value", "effect_size"], na_position="last").head(8)
        lines.extend(["## Top paired event rows", ""])
        for _, row in top_paired.iterrows():
            lines.append(
                f"- `{row['analysis_type']}` / `{row['segment_label']}` / `{row['network']}` / `{row['metric']}`: "
                f"d={row['effect_size']:.3f}, p={row['p_value']:.4g}, q={row['q_value']:.4g}"
            )
        lines.append("")
    if esb_contrasts.empty:
        lines.extend(["## Trajectory ESB", "", "No ESB contrast rows were produced.", ""])
    else:
        top_esb = esb_contrasts.sort_values(["q_value", "p_value", "effect_size"], na_position="last").head(8)
        lines.extend(["## Trajectory ESB", ""])
        for _, row in top_esb.iterrows():
            lines.append(
                f"- `{row['contrast_name']}` / `{row['segment_label']}` / `{row['network']}` / `{row['metric']}`: "
                f"d={row['effect_size']:.3f}, p={row['p_value']:.4g}, q={row['q_value']:.4g}"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)
    subject_frame = pd.read_csv(args.input_dir / SUBJECT_METRICS_CSV, low_memory=False)
    event_long = load_subject_long(args.input_dir)
    contrast_rows = paired_contrast_rows(event_long) + unpaired_contrast_rows(event_long)
    event_contrasts = apply_fdr(pd.DataFrame(contrast_rows))
    event_contrasts.to_csv(args.output_dir / EVENT_CONTRASTS_CSV, index=False)

    esb_template, esb_scores = build_esb_scores(subject_frame)
    esb_template.to_csv(args.output_dir / ESB_TEMPLATE_CSV, index=False)
    esb_scores.to_csv(args.output_dir / ESB_SUBJECT_SCORES_CSV, index=False)
    esb_contrasts = esb_contrast_rows(esb_scores)
    esb_contrasts.to_csv(args.output_dir / ESB_CONTRASTS_CSV, index=False)

    (args.output_dir / WRAPPER_SUMMARY_FILENAME).write_text(
        build_wrapper_summary(event_contrasts, esb_contrasts),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
