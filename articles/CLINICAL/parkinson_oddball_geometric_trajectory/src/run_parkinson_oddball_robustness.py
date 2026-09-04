from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

import h5py
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from parkinson_oddball_support import (
    DATASET_ROOT,
    POST_EVENT_WINDOWS,
    PRE_EVENT_WINDOWS,
    PRIMARY_COORDINATE_CONTRACT,
    RESULTS_DIR,
    SUBJECT_METRICS_CSV,
    EVENT_METRIC_DIR,
    LoadedRun,
    SpaceKey,
    cohens_d,
    ensure_dir,
    family_projection,
    family_temporal_coupling_metrics,
    load_run,
    robust_median,
    winsorize_array,
)


ROBUSTNESS_CSV = "selected_metric_robustness.csv"
ROBUSTNESS_MD = "selected_metric_robustness.md"
N_SHUFFLE_DRAWS = 32
COUPLING_METRIC_RE = re.compile(r"^(coupling|asymmetry)_[mde]{2}_tau\d+$")

EVENT_GROUP_SPECS = [
    {
        "family": "Disease coupling",
        "metric_id": "auditory_arrowcue_coupling_dm_tau2_3d",
        "analysis_type": "global_event_locked_trajectory_3d",
        "segment_label": "auditory_arrowcue",
        "metric": "coupling_dm_tau2",
        "shuffle_null": True,
    },
    {
        "family": "Disease asymmetry",
        "metric_id": "auditory_response_asymmetry_me_tau2_3d",
        "analysis_type": "global_event_locked_trajectory_3d",
        "segment_label": "auditory_response",
        "metric": "asymmetry_me_tau2",
        "shuffle_null": True,
    },
    {
        "family": "Disease coupling",
        "metric_id": "auditory_all_coupling_me_tau1_9d",
        "analysis_type": "global_event_locked_trajectory_9d",
        "segment_label": "auditory_all",
        "metric": "coupling_me_tau1",
        "shuffle_null": True,
    },
    {
        "family": "Recovery asymmetry",
        "metric_id": "auditory_arrowcue_hysteresis_area_md_9d",
        "analysis_type": "global_event_locked_trajectory_9d",
        "segment_label": "auditory_arrowcue",
        "metric": "hysteresis_area_md",
        "shuffle_null": False,
    },
    {
        "family": "Recurrence",
        "metric_id": "auditory_all_return_probability_tau2_9d",
        "analysis_type": "global_event_locked_trajectory_9d",
        "segment_label": "auditory_all",
        "metric": "return_probability_tau2",
        "shuffle_null": False,
    },
    {
        "family": "Hidden cost",
        "metric_id": "auditory_arrowcue_noetic_action_jerk_9d",
        "analysis_type": "global_event_locked_trajectory_9d",
        "segment_label": "auditory_arrowcue",
        "metric": "noetic_action_jerk",
        "shuffle_null": False,
    },
]

STANDARD_SPECS = [
    {
        "family": "Supportive global",
        "metric_id": "global_m_median_3d",
        "analysis_type": "global_mnps_3d",
        "metric": "m_median",
    },
    {
        "family": "Supportive global",
        "metric_id": "reachability_tube_q_ratio_h4_mean",
        "analysis_type": "reachability_cones",
        "metric": "tube_q_ratio_h4_mean",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run disease-first robustness checks for the Parkinson oddball trajectory article.")
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


def wrapper_group_row(
    event_subject: pd.DataFrame,
    *,
    spec: dict[str, object],
    variant: str,
    exclude_subjects: Iterable[str] = (),
    winsorize: bool = False,
    override_frame: pd.DataFrame | None = None,
) -> dict[str, object]:
    frame = override_frame.copy() if override_frame is not None else event_subject.copy()
    frame = frame[
        (frame["analysis_type"] == spec["analysis_type"])
        & (frame["segment_label"] == spec["segment_label"])
    ].copy()
    if exclude_subjects:
        frame = frame[~frame["subject_id"].isin(set(exclude_subjects))].copy()
    left = pd.to_numeric(frame.loc[frame["group"] == "Control", spec["metric"]], errors="coerce").dropna().to_numpy(dtype=float)
    right = pd.to_numeric(frame.loc[frame["group"] == "Parkinson", spec["metric"]], errors="coerce").dropna().to_numpy(dtype=float)
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
        "segment_label": spec["segment_label"],
        "metric": spec["metric"],
        "comparison_type": "wrapper_group_difference",
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


def standard_group_row(
    standard_subject: pd.DataFrame,
    *,
    spec: dict[str, str],
    variant: str,
    exclude_subjects: Iterable[str] = (),
    winsorize: bool = False,
) -> dict[str, object]:
    frame = standard_subject[
        (standard_subject["analysis_type"] == spec["analysis_type"])
        & (standard_subject["metric"] == spec["metric"])
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
        "segment_label": "global",
        "metric": spec["metric"],
        "comparison_type": "standard_group_difference",
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


def iter_h5_paths(dataset_root: Path) -> list[Path]:
    return sorted(dataset_root.glob("sub-*/sub-*.h5"))


def load_runs(
    dataset_root: Path,
    *,
    coordinate_contract: str,
) -> list[LoadedRun]:
    runs: list[LoadedRun] = []
    for h5_path in iter_h5_paths(dataset_root):
        with h5py.File(h5_path, "r") as handle:
            runs.append(load_run(handle, h5_path, coordinate_contract=coordinate_contract))
    return runs


def trimmed_indices(block: np.ndarray, n_points: int) -> np.ndarray:
    block = np.asarray(block, dtype=int).reshape(-1)
    return block[(block >= 0) & (block < n_points)]


def build_local_window(
    block: np.ndarray,
    *,
    n_points: int,
    pre_windows: int,
    post_windows: int,
) -> tuple[int, int]:
    start = max(0, int(block[0]) - int(pre_windows))
    end = min(n_points - 1, int(block[-1]) + int(post_windows))
    return start, end


def parse_dim_from_analysis_type(analysis_type: str) -> int:
    if analysis_type.endswith("_3d"):
        return 3
    if analysis_type.endswith("_9d"):
        return 9
    raise ValueError(f"Could not infer dimension from {analysis_type}.")


def shuffled_coupling_metric(metric: str, coords: np.ndarray, rng: np.random.Generator) -> float:
    if not COUPLING_METRIC_RE.match(metric):
        raise ValueError(f"Metric {metric} is not a coupling/asymmetry metric.")
    projected = family_projection(coords)
    if projected.shape[0] < 6:
        return float("nan")
    shuffled = projected.copy()
    for dim in range(shuffled.shape[1]):
        shift = int(rng.integers(1, shuffled.shape[0]))
        shuffled[:, dim] = np.roll(shuffled[:, dim], shift)
    metrics = family_temporal_coupling_metrics(shuffled)
    return float(metrics.get(metric, float("nan")))


def build_shuffle_null_frame(
    dataset_root: Path,
    specs: list[dict[str, object]],
    *,
    exclude_subjects: Iterable[str] = (),
) -> pd.DataFrame:
    runs = load_runs(dataset_root, coordinate_contract=PRIMARY_COORDINATE_CONTRACT)
    exclude = set(exclude_subjects)
    rng = np.random.default_rng(20260602)
    rows: list[dict[str, object]] = []
    for spec in specs:
        block_rows: list[dict[str, object]] = []
        dim = parse_dim_from_analysis_type(str(spec["analysis_type"]))
        key = SpaceKey("global", "global", dim)
        for run in runs:
            if run.metadata["subject_id"] in exclude:
                continue
            payload = run.spaces.get(key)
            if payload is None:
                continue
            coords = np.asarray(payload["coords"], dtype=float)
            n_points = min(coords.shape[0], run.time.shape[0])
            if n_points < 6:
                continue
            coords = coords[:n_points]
            blocks = run.segment_blocks.get(str(spec["segment_label"]), [])
            null_block_values: list[float] = []
            for block in blocks:
                keep = trimmed_indices(block, n_points)
                if keep.size == 0:
                    continue
                start, end = build_local_window(
                    keep,
                    n_points=n_points,
                    pre_windows=PRE_EVENT_WINDOWS,
                    post_windows=POST_EVENT_WINDOWS,
                )
                segment_coords = coords[start : end + 1]
                draw_values = [
                    shuffled_coupling_metric(str(spec["metric"]), segment_coords, rng)
                    for _ in range(N_SHUFFLE_DRAWS)
                ]
                draw_values = [value for value in draw_values if np.isfinite(value)]
                if draw_values:
                    null_block_values.append(robust_median(np.asarray(draw_values, dtype=float)))
            if null_block_values:
                block_rows.append(
                    {
                        "subject_id": run.metadata["subject_id"],
                        "group": run.metadata["group"],
                        "analysis_type": spec["analysis_type"],
                        "segment_label": spec["segment_label"],
                        "metric": spec["metric"],
                        "value": robust_median(np.asarray(null_block_values, dtype=float)),
                    }
                )
        rows.extend(block_rows)
    return pd.DataFrame(rows)


def build_summary(frame: pd.DataFrame, raw_nan_subjects: set[str]) -> str:
    lines = [
        "# Parkinson oddball disease-first robustness",
        "",
        f"- subjects with residual `raw_nan_onset_sec`: `{len(raw_nan_subjects)}`",
        "- wrapper rows are rerun after residual-label exclusion, `sub-112` exclusion, and pooled winsorization",
        "- coupling/asymmetry rows also receive a circular-shift family shuffle null",
        "",
    ]
    for metric_id in frame["metric_id"].dropna().unique().tolist():
        block = frame[frame["metric_id"] == metric_id].copy()
        if block.empty:
            continue
        lines.extend([f"## {metric_id}", ""])
        for _, row in block.iterrows():
            lines.append(
                f"- `{row['variant']}`: Control med={row['left_median']:.4g}, Parkinson med={row['right_median']:.4g}, "
                f"d={row['effect_size']:.4g}, p={row['p_value']:.4g}"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    ensure_dir(args.results_dir)
    raw_nan_subjects = detect_raw_nan_subjects(args.dataset_root)
    event_subject = pd.read_csv(args.results_dir / "event_metrics" / SUBJECT_METRICS_CSV, low_memory=False)
    standard_subject = pd.read_parquet(latest_parquet(args.results_dir / "standard_analysis", "subject_metrics"))

    rows: list[dict[str, object]] = []
    for spec in EVENT_GROUP_SPECS:
        rows.append(wrapper_group_row(event_subject, spec=spec, variant="all"))
        rows.append(wrapper_group_row(event_subject, spec=spec, variant="exclude_raw_nan", exclude_subjects=raw_nan_subjects))
        rows.append(wrapper_group_row(event_subject, spec=spec, variant="exclude_sub112", exclude_subjects={"sub-112"}))
        rows.append(wrapper_group_row(event_subject, spec=spec, variant="winsorized_2p5_97p5", winsorize=True))

    coupling_specs = [spec for spec in EVENT_GROUP_SPECS if bool(spec.get("shuffle_null"))]
    shuffle_frame = build_shuffle_null_frame(args.dataset_root, coupling_specs, exclude_subjects=raw_nan_subjects)
    for spec in coupling_specs:
        spec_null = shuffle_frame[shuffle_frame["metric"] == str(spec["metric"])].copy()
        rows.append(
            wrapper_group_row(
                event_subject,
                spec=spec,
                variant="shuffle_null_exclude_raw_nan",
                override_frame=spec_null.rename(columns={"value": str(spec["metric"])}),
            )
        )

    for spec in STANDARD_SPECS:
        rows.append(standard_group_row(standard_subject, spec=spec, variant="all"))
        rows.append(standard_group_row(standard_subject, spec=spec, variant="exclude_sub112", exclude_subjects={"sub-112"}))
        rows.append(standard_group_row(standard_subject, spec=spec, variant="winsorized_2p5_97p5", winsorize=True))

    frame = pd.DataFrame(rows)
    frame.to_csv(args.results_dir / ROBUSTNESS_CSV, index=False)
    (args.results_dir / ROBUSTNESS_MD).write_text(build_summary(frame, raw_nan_subjects), encoding="utf-8")


if __name__ == "__main__":
    main()
