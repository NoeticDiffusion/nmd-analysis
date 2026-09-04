from __future__ import annotations

import argparse
import math
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, ttest_ind, wilcoxon

from depression_probsel_event_support import (
    BDI_CORRELATIONS_CSV,
    BDI_GROUP_CONTRASTS_CSV,
    EVENT_METRIC_DIR,
    EVENT_SUMMARY_MD,
    NUMERIC_METRIC_COLUMNS,
    RESULTS_DIR,
    SUBJECT_METRICS_CSV,
    WITHIN_SUBJECT_CONTRASTS_CSV,
    WITHIN_SUBJECT_DIFFS_CSV,
    bh_fdr,
    cohens_d,
    cohens_dz,
    ensure_dir,
    load_participants,
)


@dataclass(frozen=True)
class ContrastSpec:
    contrast_name: str
    left_label: str
    right_label: str
    priority: str
    title: str


CONTRAST_SPECS: tuple[ContrastSpec, ...] = (
    ContrastSpec(
        contrast_name="feedback_correct_vs_incorrect",
        left_label="feedback_correct",
        right_label="feedback_incorrect",
        priority="primary",
        title="Feedback correct vs incorrect",
    ),
    ContrastSpec(
        contrast_name="train_high_vs_low_certainty",
        left_label="train_high_certainty",
        right_label="train_low_certainty",
        priority="co_primary",
        title="Training high-certainty vs low-certainty pairs",
    ),
    ContrastSpec(
        contrast_name="train_mid_vs_low_certainty",
        left_label="train_mid_certainty",
        right_label="train_low_certainty",
        priority="secondary",
        title="Training mid-certainty vs low-certainty pairs",
    ),
    ContrastSpec(
        contrast_name="train_vs_test",
        left_label="train_any",
        right_label="test_any",
        priority="secondary",
        title="Training vs test",
    ),
    ContrastSpec(
        contrast_name="left_vs_right_response",
        left_label="left_response",
        right_label="right_response",
        priority="exploratory",
        title="Left vs right response",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export within-subject PST contrasts and BDI modulation from ds003474 event metrics."
    )
    parser.add_argument("--input-dir", type=Path, default=EVENT_METRIC_DIR)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    return parser.parse_args()


def fmt(value: object) -> str:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return "nan"
    if not math.isfinite(parsed):
        return "nan"
    return f"{parsed:.4g}"


def sig_tier(row: pd.Series | dict[str, Any]) -> str:
    q = pd.to_numeric(pd.Series([row.get("q_value")]), errors="coerce").iloc[0]
    p = pd.to_numeric(pd.Series([row.get("p_value")]), errors="coerce").iloc[0]
    if pd.notna(q) and float(q) <= 0.05:
        return "q<=0.05"
    if pd.notna(p) and float(p) < 0.05:
        return "p<0.05"
    if pd.notna(p) and float(p) < 0.1:
        return "p<0.1"
    return "ns"


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
    long_frame = long_frame.dropna(subset=["value"]).reset_index(drop=True)
    return long_frame


def build_within_subject_details(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    detail_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    group_cols = ["analysis_type", "network", "dims", "metric"]

    for spec in CONTRAST_SPECS:
        use = frame[frame["segment_label"].isin([spec.left_label, spec.right_label])].copy()
        for keys, group in use.groupby(group_cols, dropna=False):
            pivot = group.pivot_table(index="subject_id", columns="segment_label", values="value", aggfunc="median")
            if spec.left_label not in pivot.columns or spec.right_label not in pivot.columns:
                continue
            paired = pivot.dropna(subset=[spec.left_label, spec.right_label]).reset_index()
            if paired.shape[0] < 3:
                continue
            diff = paired[spec.right_label].to_numpy(dtype=float) - paired[spec.left_label].to_numpy(dtype=float)
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=UserWarning)
                    p_value = float(wilcoxon(diff, alternative="two-sided", zero_method="wilcox").pvalue)
            except ValueError:
                p_value = 1.0
            for _, row in paired.iterrows():
                detail_rows.append(
                    {
                        "contrast_name": spec.contrast_name,
                        "contrast_title": spec.title,
                        "priority": spec.priority,
                        "analysis_type": keys[0],
                        "network": keys[1],
                        "dims": keys[2],
                        "metric": keys[3],
                        "subject_id": row["subject_id"],
                        "left_label": spec.left_label,
                        "right_label": spec.right_label,
                        "left_value": float(row[spec.left_label]),
                        "right_value": float(row[spec.right_label]),
                        "diff_value": float(row[spec.right_label] - row[spec.left_label]),
                    }
                )
            summary_rows.append(
                {
                    "contrast_name": spec.contrast_name,
                    "contrast_title": spec.title,
                    "priority": spec.priority,
                    "analysis_type": keys[0],
                    "network": keys[1],
                    "dims": keys[2],
                    "metric": keys[3],
                    "contrast_type": "paired",
                    "n": int(paired.shape[0]),
                    "left_label": spec.left_label,
                    "right_label": spec.right_label,
                    "left_median": float(np.median(paired[spec.left_label].to_numpy(dtype=float))),
                    "right_median": float(np.median(paired[spec.right_label].to_numpy(dtype=float))),
                    "median_diff": float(np.median(diff)),
                    "effect_size": cohens_dz(diff),
                    "p_value": p_value,
                }
            )

    detail = pd.DataFrame(detail_rows)
    summary = pd.DataFrame(summary_rows)
    if not summary.empty:
        summary["q_value"] = np.nan
        for _, idx in summary.groupby(["contrast_name", "analysis_type"], dropna=False).groups.items():
            block = summary.loc[list(idx)].copy()
            summary.loc[block.index, "q_value"] = bh_fdr(block["p_value"]).to_numpy(dtype=float)
        summary["sig_tier"] = summary.apply(sig_tier, axis=1)
        summary["abs_effect_size"] = pd.to_numeric(summary["effect_size"], errors="coerce").abs()
        summary = summary.sort_values(
            ["contrast_name", "q_value", "p_value", "abs_effect_size", "metric"],
            ascending=[True, True, True, False, True],
            na_position="last",
        ).reset_index(drop=True)
    return detail, summary


def build_bdi_group_contrasts(diff_detail: pd.DataFrame) -> pd.DataFrame:
    phenos = load_participants()[["participant_id", "BDI", "bdi_band"]].rename(columns={"participant_id": "subject_id"})
    merged = diff_detail.merge(phenos, on="subject_id", how="left")
    rows: list[dict[str, Any]] = []
    group_cols = ["contrast_name", "contrast_title", "priority", "analysis_type", "network", "dims", "metric"]
    for keys, group in merged.groupby(group_cols, dropna=False):
        low = pd.to_numeric(group.loc[group["bdi_band"] == "BDI 0-13", "diff_value"], errors="coerce").dropna()
        high = pd.to_numeric(group.loc[group["bdi_band"] == "BDI 20-63", "diff_value"], errors="coerce").dropna()
        if low.shape[0] < 3 or high.shape[0] < 3:
            continue
        _, p_value = ttest_ind(low.to_numpy(dtype=float), high.to_numpy(dtype=float), equal_var=False, nan_policy="omit")
        rows.append(
            {
                "contrast_name": keys[0],
                "contrast_title": keys[1],
                "priority": keys[2],
                "analysis_type": keys[3],
                "network": keys[4],
                "dims": keys[5],
                "metric": keys[6],
                "left_group": "BDI 0-13",
                "right_group": "BDI 20-63",
                "left_n": int(low.shape[0]),
                "right_n": int(high.shape[0]),
                "left_mean": float(np.mean(low)),
                "right_mean": float(np.mean(high)),
                "effect_estimate": float(np.mean(high) - np.mean(low)),
                "effect_size": cohens_d(low.to_numpy(dtype=float), high.to_numpy(dtype=float)),
                "p_value": float(p_value) if np.isfinite(p_value) else np.nan,
            }
        )
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["q_value"] = np.nan
        for _, idx in frame.groupby(["contrast_name", "analysis_type"], dropna=False).groups.items():
            block = frame.loc[list(idx)].copy()
            frame.loc[block.index, "q_value"] = bh_fdr(block["p_value"]).to_numpy(dtype=float)
        frame["sig_tier"] = frame.apply(sig_tier, axis=1)
        frame["abs_effect_size"] = pd.to_numeric(frame["effect_size"], errors="coerce").abs()
        frame = frame.sort_values(
            ["contrast_name", "q_value", "p_value", "abs_effect_size", "metric"],
            ascending=[True, True, True, False, True],
            na_position="last",
        ).reset_index(drop=True)
    return frame


def build_bdi_correlations(diff_detail: pd.DataFrame) -> pd.DataFrame:
    phenos = load_participants()[["participant_id", "BDI"]].rename(columns={"participant_id": "subject_id"})
    merged = diff_detail.merge(phenos, on="subject_id", how="left")
    rows: list[dict[str, Any]] = []
    group_cols = ["contrast_name", "contrast_title", "priority", "analysis_type", "network", "dims", "metric"]
    for keys, group in merged.groupby(group_cols, dropna=False):
        work = group[["subject_id", "BDI", "diff_value"]].dropna().drop_duplicates(subset=["subject_id"])
        if work.shape[0] < 6 or work["BDI"].nunique() < 2 or work["diff_value"].nunique() < 2:
            continue
        rho, p_value = spearmanr(work["diff_value"], work["BDI"])
        rows.append(
            {
                "contrast_name": keys[0],
                "contrast_title": keys[1],
                "priority": keys[2],
                "analysis_type": keys[3],
                "network": keys[4],
                "dims": keys[5],
                "metric": keys[6],
                "n_subjects": int(work.shape[0]),
                "spearman_rho": float(rho) if np.isfinite(rho) else np.nan,
                "p_value": float(p_value) if np.isfinite(p_value) else np.nan,
            }
        )
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["q_value"] = np.nan
        for _, idx in frame.groupby(["contrast_name", "analysis_type"], dropna=False).groups.items():
            block = frame.loc[list(idx)].copy()
            frame.loc[block.index, "q_value"] = bh_fdr(block["p_value"]).to_numpy(dtype=float)
        frame["sig_tier"] = frame.apply(sig_tier, axis=1)
        frame["abs_rho"] = pd.to_numeric(frame["spearman_rho"], errors="coerce").abs()
        frame = frame.sort_values(
            ["contrast_name", "q_value", "p_value", "abs_rho", "metric"],
            ascending=[True, True, True, False, True],
            na_position="last",
        ).reset_index(drop=True)
    return frame


def build_summary(
    within_subject: pd.DataFrame,
    bdi_groups: pd.DataFrame,
    bdi_corr: pd.DataFrame,
) -> str:
    lines = [
        "# Depression PST event-first summary",
        "",
        "This wrapper treats subject-anchored PST event segments as the primary inferential layer, then asks whether BDI modulates the resulting within-subject contrast scores.",
        "",
        "## Within-subject PST contrasts",
        "",
    ]
    if within_subject.empty:
        lines.extend(["No within-subject contrast rows were produced.", ""])
    else:
        for spec in CONTRAST_SPECS:
            block = within_subject[within_subject["contrast_name"] == spec.contrast_name].copy()
            if block.empty:
                continue
            lines.extend([f"### {spec.title}", ""])
            for _, row in block.head(8).iterrows():
                lines.append(
                    f"- `{row['analysis_type']}` / `{row['metric']}`: "
                    f"d_z={fmt(row.get('effect_size'))}, p={fmt(row.get('p_value'))}, q={fmt(row.get('q_value'))}"
                )
            lines.append("")

    lines.extend(["## BDI low vs high modulation", ""])
    if bdi_groups.empty:
        lines.extend(["No BDI low-vs-high modulation rows were produced.", ""])
    else:
        for spec in CONTRAST_SPECS:
            block = bdi_groups[bdi_groups["contrast_name"] == spec.contrast_name].copy()
            if block.empty:
                continue
            lines.extend([f"### {spec.title}", ""])
            for _, row in block.head(6).iterrows():
                lines.append(
                    f"- `{row['analysis_type']}` / `{row['metric']}`: "
                    f"d={fmt(row.get('effect_size'))}, p={fmt(row.get('p_value'))}, q={fmt(row.get('q_value'))}"
                )
            lines.append("")

    lines.extend(["## Continuous BDI modulation", ""])
    if bdi_corr.empty:
        lines.extend(["No continuous BDI modulation rows were produced.", ""])
    else:
        for spec in CONTRAST_SPECS:
            block = bdi_corr[bdi_corr["contrast_name"] == spec.contrast_name].copy()
            if block.empty:
                continue
            lines.extend([f"### {spec.title}", ""])
            for _, row in block.head(6).iterrows():
                lines.append(
                    f"- `{row['analysis_type']}` / `{row['metric']}`: "
                    f"rho={fmt(row.get('spearman_rho'))}, p={fmt(row.get('p_value'))}, q={fmt(row.get('q_value'))}"
                )
            lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)
    event_long = load_subject_long(args.input_dir)
    diff_detail, within_subject = build_within_subject_details(event_long)
    bdi_groups = build_bdi_group_contrasts(diff_detail)
    bdi_corr = build_bdi_correlations(diff_detail)

    diff_detail.to_csv(args.output_dir / WITHIN_SUBJECT_DIFFS_CSV, index=False)
    within_subject.to_csv(args.output_dir / WITHIN_SUBJECT_CONTRASTS_CSV, index=False)
    bdi_groups.to_csv(args.output_dir / BDI_GROUP_CONTRASTS_CSV, index=False)
    bdi_corr.to_csv(args.output_dir / BDI_CORRELATIONS_CSV, index=False)
    (args.output_dir / EVENT_SUMMARY_MD).write_text(
        build_summary(within_subject, bdi_groups, bdi_corr),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
