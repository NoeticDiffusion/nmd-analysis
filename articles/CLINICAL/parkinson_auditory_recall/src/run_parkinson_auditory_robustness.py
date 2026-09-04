from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import h5py
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon

from parkinson_auditory_support import (
    DATASET_ROOT,
    RESULTS_DIR,
    SUBJECT_METRICS_CSV,
    cohens_d,
    cohens_dz,
    ensure_dir,
    winsorize_array,
)


ROBUSTNESS_CSV = "selected_metric_robustness.csv"
ROBUSTNESS_MD = "selected_metric_robustness.md"

EVENT_SPECS = [
    {
        "family": "Event primary",
        "metric_id": "auditory_other_transition_sparsity_3d",
        "analysis_type": "global_event_locked_trajectory_3d",
        "metric": "transition_sparsity",
        "comparison_kind": "other_mean",
        "left_label": "other_mean",
        "right_label": "auditory_all",
    },
    {
        "family": "Event primary",
        "metric_id": "auditory_other_entropy_rate_9d",
        "analysis_type": "global_event_locked_trajectory_9d",
        "metric": "entropy_rate",
        "comparison_kind": "other_mean",
        "left_label": "other_mean",
        "right_label": "auditory_all",
    },
    {
        "family": "Event primary",
        "metric_id": "auditory_other_peak_displacement_9d",
        "analysis_type": "global_event_locked_trajectory_9d",
        "metric": "peak_displacement",
        "comparison_kind": "other_mean",
        "left_label": "other_mean",
        "right_label": "auditory_all",
    },
    {
        "family": "Event phase peak",
        "metric_id": "arrowcue_entropy_rate_9d",
        "analysis_type": "global_event_locked_trajectory_9d",
        "metric": "entropy_rate",
        "comparison_kind": "pair",
        "left_label": "standard_arrowcue",
        "right_label": "auditory_arrowcue",
    },
]

STANDARD_SPECS = [
    {
        "family": "Supportive group",
        "metric_id": "global_m_median_3d",
        "analysis_type": "global_mnps_3d",
        "metric": "m_median",
    },
    {
        "family": "Supportive group",
        "metric_id": "tube_q_ratio_h4_mean",
        "analysis_type": "reachability_cones",
        "metric": "tube_q_ratio_h4_mean",
    },
    {
        "family": "Outlier check",
        "metric_id": "jacobian9d_frobenius_norm_median",
        "analysis_type": "global_mnps_jacobian_9d",
        "metric": "frobenius_norm_median",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run selected robustness checks for the Parkinson auditory recall article.")
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    return parser.parse_args()


def latest_parquet(root: Path, stem: str) -> Path:
    matches = sorted(root.glob(f"ds004574_{stem}_*.parquet"), key=lambda path: path.stat().st_mtime_ns)
    if not matches:
        raise FileNotFoundError(f"No parquet matched ds004574_{stem}_*.parquet under {root}.")
    return matches[-1]


def detect_raw_nan_subjects(dataset_root: Path) -> set[str]:
    subjects: set[str] = set()
    for h5_path in sorted(dataset_root.glob("sub-*/sub-*.h5")):
        with h5py.File(h5_path, "r") as handle:
            dataset_path = "labels/raw_nan_onset_sec"
            if dataset_path not in handle:
                continue
            raw = np.asarray(handle[dataset_path][:], dtype=float).reshape(-1)
            if np.isfinite(raw).any() and np.nanmax(raw) > 0:
                subjects.add(h5_path.stem.split("_", 1)[0])
    return subjects


def paired_event_row(
    event_subject: pd.DataFrame,
    *,
    spec: dict[str, str],
    subset_group: str | None,
    exclude_subjects: Iterable[str] = (),
) -> dict[str, object]:
    frame = event_subject[
        (event_subject["analysis_type"] == spec["analysis_type"])
        & event_subject["segment_label"].isin(["standard_all", "visual_all", "auditory_all", "standard_arrowcue", "auditory_arrowcue"])
    ].copy()
    if subset_group is not None:
        frame = frame[frame["group"] == subset_group].copy()
    if exclude_subjects:
        frame = frame[~frame["subject_id"].isin(set(exclude_subjects))].copy()
    pivot = frame.pivot_table(index="subject_id", columns="segment_label", values=spec["metric"], aggfunc="median")
    if spec["comparison_kind"] == "other_mean":
        required = {"standard_all", "visual_all", "auditory_all"}
        paired = pivot.dropna(subset=sorted(required))
        left = 0.5 * (paired["standard_all"].to_numpy(dtype=float) + paired["visual_all"].to_numpy(dtype=float))
        right = paired["auditory_all"].to_numpy(dtype=float)
    else:
        required = {spec["left_label"], spec["right_label"]}
        paired = pivot.dropna(subset=sorted(required))
        left = paired[spec["left_label"]].to_numpy(dtype=float)
        right = paired[spec["right_label"]].to_numpy(dtype=float)
    diff = right - left
    if paired.shape[0] < 3:
        p_value = float("nan")
        effect = float("nan")
    else:
        try:
            p_value = float(wilcoxon(diff, alternative="two-sided", zero_method="wilcox").pvalue)
        except ValueError:
            p_value = 1.0
        effect = cohens_dz(diff)
    return {
        "family": spec["family"],
        "metric_id": spec["metric_id"],
        "analysis_type": spec["analysis_type"],
        "metric": spec["metric"],
        "comparison_type": "paired_event",
        "variant": "exclude_raw_nan" if exclude_subjects else ("all" if subset_group is None else subset_group.lower()),
        "left_label": spec["left_label"],
        "right_label": spec["right_label"],
        "n": int(paired.shape[0]),
        "left_median": float(np.median(left)) if len(left) else float("nan"),
        "right_median": float(np.median(right)) if len(right) else float("nan"),
        "effect_size": effect,
        "p_value": p_value,
    }


def unpaired_standard_row(
    subject_metrics: pd.DataFrame,
    *,
    spec: dict[str, str],
    variant: str,
    exclude_subjects: Iterable[str] = (),
    winsorize: bool = False,
) -> dict[str, object]:
    frame = subject_metrics[
        (subject_metrics["analysis_type"] == spec["analysis_type"])
        & (subject_metrics["metric"] == spec["metric"])
    ].copy()
    if exclude_subjects:
        frame = frame[~frame["subject_id"].isin(set(exclude_subjects))].copy()
    left = pd.to_numeric(frame.loc[frame["group"] == "Control", "value"], errors="coerce").dropna().to_numpy(dtype=float)
    right = pd.to_numeric(frame.loc[frame["group"] == "Parkinson", "value"], errors="coerce").dropna().to_numpy(dtype=float)
    if winsorize:
        pooled = np.r_[left, right]
        if pooled.size >= 6:
            lo = float(np.nanquantile(pooled, 0.025))
            hi = float(np.nanquantile(pooled, 0.975))
            left = np.clip(left, lo, hi)
            right = np.clip(right, lo, hi)
    if left.size < 3 or right.size < 3:
        p_value = float("nan")
        effect = float("nan")
    else:
        p_value = float(mannwhitneyu(left, right, alternative="two-sided").pvalue)
        effect = cohens_d(left, right)
    return {
        "family": spec["family"],
        "metric_id": spec["metric_id"],
        "analysis_type": spec["analysis_type"],
        "metric": spec["metric"],
        "comparison_type": "group_difference",
        "variant": variant,
        "left_label": "Control",
        "right_label": "Parkinson",
        "n_left": int(left.size),
        "n_right": int(right.size),
        "left_median": float(np.median(left)) if left.size else float("nan"),
        "right_median": float(np.median(right)) if right.size else float("nan"),
        "effect_size": effect,
        "p_value": p_value,
    }


def build_summary(frame: pd.DataFrame, raw_nan_subjects: set[str]) -> str:
    lines = [
        "# Selected metric robustness",
        "",
        f"- subjects with residual `raw_nan_onset_sec`: `{len(raw_nan_subjects)}`",
        "- article-local event rows already exclude `raw_nan` events by construction",
        "- group-level follow-up re-runs selected rows after subject exclusion or winsorization",
        "",
    ]
    for metric_id in frame["metric_id"].dropna().unique().tolist():
        block = frame[frame["metric_id"] == metric_id].copy()
        if block.empty:
            continue
        lines.extend([f"## {metric_id}", ""])
        for _, row in block.iterrows():
            if row["comparison_type"] == "group_difference":
                lines.append(
                    f"- `{row['variant']}`: Control med={row['left_median']:.4g}, Parkinson med={row['right_median']:.4g}, "
                    f"d={row['effect_size']:.4g}, p={row['p_value']:.4g}"
                )
            else:
                lines.append(
                    f"- `{row['variant']}`: {row['left_label']} med={row['left_median']:.4g}, {row['right_label']} med={row['right_median']:.4g}, "
                    f"d={row['effect_size']:.4g}, p={row['p_value']:.4g}"
                )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    ensure_dir(args.results_dir)
    standard_subject_path = latest_parquet(args.results_dir / "standard_analysis", "subject_metrics")
    standard_subject = pd.read_parquet(standard_subject_path)
    event_subject = pd.read_csv(args.results_dir / "event_metrics" / SUBJECT_METRICS_CSV, low_memory=False)
    raw_nan_subjects = detect_raw_nan_subjects(args.dataset_root)

    rows: list[dict[str, object]] = []
    for spec in EVENT_SPECS:
        rows.append(paired_event_row(event_subject, spec=spec, subset_group=None))
        rows.append(paired_event_row(event_subject, spec=spec, subset_group=None, exclude_subjects=raw_nan_subjects))
        rows.append(paired_event_row(event_subject, spec=spec, subset_group="Control"))
        rows.append(paired_event_row(event_subject, spec=spec, subset_group="Parkinson"))

    for spec in STANDARD_SPECS:
        rows.append(unpaired_standard_row(standard_subject, spec=spec, variant="all"))
        rows.append(unpaired_standard_row(standard_subject, spec=spec, variant="exclude_sub112", exclude_subjects={"sub-112"}))
        rows.append(unpaired_standard_row(standard_subject, spec=spec, variant="winsorized_2p5_97p5", winsorize=True))

    frame = pd.DataFrame(rows)
    frame.to_csv(args.results_dir / ROBUSTNESS_CSV, index=False)
    (args.results_dir / ROBUSTNESS_MD).write_text(build_summary(frame, raw_nan_subjects), encoding="utf-8")


if __name__ == "__main__":
    main()
