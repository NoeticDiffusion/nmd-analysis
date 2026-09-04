from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon

from parkinson_oddball_support import (
    EVENT_CONTRASTS_CSV,
    EVENT_METRIC_DIR,
    NUMERIC_METRIC_COLUMNS,
    RESULTS_DIR,
    SUBJECT_METRICS_CSV,
    WRAPPER_SUMMARY_MD,
    bh_fdr,
    cohens_d,
    cohens_dz,
    ensure_dir,
)


WRAPPER_SUMMARY_FILENAME = WRAPPER_SUMMARY_MD


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export ds004574 disease-first oddball trajectory contrasts from subject-level event metrics."
    )
    parser.add_argument("--input-dir", type=Path, default=EVENT_METRIC_DIR)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
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
    long_frame = long_frame.dropna(subset=["value"]).reset_index(drop=True)
    return long_frame


def paired_label_rows(
    frame: pd.DataFrame,
    *,
    label_pairs: list[tuple[str, str, str]],
    subset_group: str | None,
    comparison_scope: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    use = frame.copy()
    if subset_group is not None:
        use = use[use["group"] == subset_group].copy()
    group_cols = ["analysis_type", "network", "dims", "metric"]
    for left_label, right_label, contrast_name in label_pairs:
        labels = [left_label, right_label]
        for keys, group in use[use["segment_label"].isin(labels)].groupby(group_cols, dropna=False):
            pivot = group.pivot_table(index="subject_id", columns="segment_label", values="value", aggfunc="median")
            if left_label not in pivot.columns or right_label not in pivot.columns:
                continue
            paired = pivot.dropna(subset=[left_label, right_label])
            if paired.shape[0] < 3:
                continue
            diff = paired[right_label].to_numpy(dtype=float) - paired[left_label].to_numpy(dtype=float)
            try:
                p_value = float(wilcoxon(diff, alternative="two-sided", zero_method="wilcox").pvalue)
            except ValueError:
                p_value = 1.0
            rows.append(
                {
                    "contrast_name": contrast_name,
                    "comparison_scope": comparison_scope,
                    "subset_group": subset_group or "all",
                    "analysis_type": keys[0],
                    "network": keys[1],
                    "dims": keys[2],
                    "segment_kind": comparison_scope,
                    "segment_label": f"{left_label}__vs__{right_label}",
                    "metric": keys[3],
                    "contrast_type": "paired",
                    "n": int(paired.shape[0]),
                    "left_label": left_label,
                    "right_label": right_label,
                    "left_median": float(np.median(paired[left_label].to_numpy(dtype=float))),
                    "right_median": float(np.median(paired[right_label].to_numpy(dtype=float))),
                    "effect_size": cohens_dz(diff),
                    "p_value": p_value,
                }
            )
    return rows


def paired_auditory_vs_other_rows(frame: pd.DataFrame, *, subset_group: str | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    use = frame[frame["segment_label"].isin(["standard_all", "auditory_all", "visual_all"])].copy()
    if subset_group is not None:
        use = use[use["group"] == subset_group].copy()
    group_cols = ["analysis_type", "network", "dims", "metric"]
    prefix = f"{subset_group}_" if subset_group is not None else "All_"
    contrast_name = f"{prefix}Auditory_vs_OtherMean"
    for keys, group in use.groupby(group_cols, dropna=False):
        pivot = group.pivot_table(index="subject_id", columns="segment_label", values="value", aggfunc="median")
        required = {"auditory_all", "standard_all", "visual_all"}
        if not required.issubset(set(pivot.columns)):
            continue
        paired = pivot.dropna(subset=sorted(required))
        if paired.shape[0] < 3:
            continue
        other_mean = 0.5 * (paired["standard_all"].to_numpy(dtype=float) + paired["visual_all"].to_numpy(dtype=float))
        auditory = paired["auditory_all"].to_numpy(dtype=float)
        diff = auditory - other_mean
        try:
            p_value = float(wilcoxon(diff, alternative="two-sided", zero_method="wilcox").pvalue)
        except ValueError:
            p_value = 1.0
        rows.append(
            {
                "contrast_name": contrast_name,
                "comparison_scope": "subtype_paired",
                "subset_group": subset_group or "all",
                "analysis_type": keys[0],
                "network": keys[1],
                "dims": keys[2],
                "segment_kind": "subtype_paired",
                "segment_label": "other_mean__vs__auditory_all",
                "metric": keys[3],
                "contrast_type": "paired",
                "n": int(paired.shape[0]),
                "left_label": "other_mean",
                "right_label": "auditory_all",
                "left_median": float(np.median(other_mean)),
                "right_median": float(np.median(auditory)),
                "effect_size": cohens_dz(diff),
                "p_value": p_value,
            }
        )
    return rows


def group_contrast_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    group_cols = ["analysis_type", "network", "dims", "segment_kind", "segment_label", "metric"]
    for keys, group in frame.groupby(group_cols, dropna=False):
        left = pd.to_numeric(group.loc[group["group"] == "Control", "value"], errors="coerce").dropna()
        right = pd.to_numeric(group.loc[group["group"] == "Parkinson", "value"], errors="coerce").dropna()
        if left.shape[0] < 3 or right.shape[0] < 3:
            continue
        p_value = float(mannwhitneyu(left, right, alternative="two-sided").pvalue)
        rows.append(
            {
                "contrast_name": "Control_vs_Parkinson",
                "comparison_scope": "group_difference",
                "subset_group": "all",
                "analysis_type": keys[0],
                "network": keys[1],
                "dims": keys[2],
                "segment_kind": keys[3],
                "segment_label": keys[4],
                "metric": keys[5],
                "contrast_type": "unpaired",
                "n_left": int(left.shape[0]),
                "n_right": int(right.shape[0]),
                "left_label": "Control",
                "right_label": "Parkinson",
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
    out["abs_effect_size"] = pd.to_numeric(out["effect_size"], errors="coerce").abs()
    return out.sort_values(
        ["contrast_name", "q_value", "p_value", "abs_effect_size", "analysis_type", "segment_label", "metric"],
        ascending=[True, True, True, False, True, True, True],
        na_position="last",
    ).reset_index(drop=True)


def build_wrapper_summary(event_contrasts: pd.DataFrame) -> str:
    lines = ["# Parkinson oddball wrapper summary", ""]
    if event_contrasts.empty:
        lines.extend(["No event contrast rows were produced.", ""])
        return "\n".join(lines)

    sections = [
        ("Control_vs_Parkinson", "Disease-first group rows"),
        ("All_Auditory_vs_OtherMean", "Task canalization backdrop"),
        ("All_Auditory_vs_Standard", "Subtype boundary"),
        ("All_Auditory_vs_Visual", "Subtype boundary"),
    ]
    for contrast_name, heading in sections:
        block = event_contrasts[event_contrasts["contrast_name"] == contrast_name].copy()
        if block.empty:
            continue
        block = block.sort_values(
            ["q_value", "p_value", "abs_effect_size"],
            ascending=[True, True, False],
            na_position="last",
        )
        lines.extend([f"## {heading}: {contrast_name}", ""])
        for _, row in block.head(10).iterrows():
            lines.append(
                f"- `{row['analysis_type']}` / `{row['segment_label']}` / `{row['metric']}`: "
                f"d={row['effect_size']:.3f}, p={row['p_value']:.4g}, q={row['q_value']:.4g}"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)
    event_long = load_subject_long(args.input_dir)

    subtype_pairs = [
        ("standard_all", "auditory_all", "All_Auditory_vs_Standard"),
        ("visual_all", "auditory_all", "All_Auditory_vs_Visual"),
    ]
    phase_matched_pairs = [
        ("standard_precue", "auditory_precue", "All_Auditory_vs_Standard_precue"),
        ("visual_precue", "auditory_precue", "All_Auditory_vs_Visual_precue"),
        ("standard_arrowcue", "auditory_arrowcue", "All_Auditory_vs_Standard_arrowcue"),
        ("visual_arrowcue", "auditory_arrowcue", "All_Auditory_vs_Visual_arrowcue"),
        ("standard_response", "auditory_response", "All_Auditory_vs_Standard_response"),
        ("visual_response", "auditory_response", "All_Auditory_vs_Visual_response"),
    ]

    contrast_rows: list[dict[str, Any]] = []
    contrast_rows.extend(group_contrast_rows(event_long))
    contrast_rows.extend(
        paired_label_rows(
            event_long,
            label_pairs=subtype_pairs,
            subset_group=None,
            comparison_scope="subtype_paired",
        )
    )
    contrast_rows.extend(
        paired_label_rows(
            event_long,
            label_pairs=phase_matched_pairs,
            subset_group=None,
            comparison_scope="phase_matched_paired",
        )
    )
    contrast_rows.extend(paired_auditory_vs_other_rows(event_long, subset_group=None))
    for subset_group in ("Control", "Parkinson"):
        subset_pairs = [
            ("standard_all", "auditory_all", f"{subset_group}_Auditory_vs_Standard"),
            ("visual_all", "auditory_all", f"{subset_group}_Auditory_vs_Visual"),
        ]
        contrast_rows.extend(
            paired_label_rows(
                event_long,
                label_pairs=subset_pairs,
                subset_group=subset_group,
                comparison_scope="subtype_paired",
            )
        )
        contrast_rows.extend(paired_auditory_vs_other_rows(event_long, subset_group=subset_group))

    event_contrasts = apply_fdr(pd.DataFrame(contrast_rows))
    event_contrasts.to_csv(args.output_dir / EVENT_CONTRASTS_CSV, index=False)
    (args.output_dir / WRAPPER_SUMMARY_FILENAME).write_text(
        build_wrapper_summary(event_contrasts),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
