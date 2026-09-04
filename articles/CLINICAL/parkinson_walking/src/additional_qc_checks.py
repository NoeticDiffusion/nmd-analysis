from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon

from parkinson_walking_support import (
    ARTICLE_DIR,
    DATASET_ROOT as SUPPORT_DATASET_ROOT,
    RESULTS_DIR,
    cohens_d,
    cohens_dz,
    curvature_series,
    ensure_dir,
    fmt,
    noetic_action_metrics,
    path_length,
    robust_median,
    sample_evenly,
    stable_variance_metric,
)


DEFAULT_DATASET_ROOT = ARTICLE_DIR.parents[2] / "data" / "raw" / "neuralmanifolddynamics_ds007526_20260610_121725"
DEFAULT_OUTPUT_DIR = RESULTS_DIR / "additional_qc_20260612_leaveoneout_shuffle"
DEFAULT_SHUFFLE_PERMUTATIONS = 200


@dataclass(frozen=True)
class LeaveOneOutSpec:
    label: str
    branch: str
    source_dir: str
    contrast_name: str
    metric: str
    mode: str
    group: str | None = None


@dataclass(frozen=True)
class TimeShuffleSpec:
    label: str
    contrast_name: str
    task: str
    dimension: int
    metric: str


LEAVE_ONE_OUT_SPECS: tuple[LeaveOneOutSpec, ...] = (
    LeaveOneOutSpec(
        label="Global walk d_n_mean",
        branch="cohort_walk_primary",
        source_dir="contrasts_cohort_121725",
        contrast_name="HC_vs_PD_walk",
        metric="d_n_mean",
        mode="group_walk",
    ),
    LeaveOneOutSpec(
        label="Global walk d_n_median",
        branch="cohort_walk_primary",
        source_dir="contrasts_cohort_121725",
        contrast_name="HC_vs_PD_walk",
        metric="d_n_median",
        mode="group_walk",
    ),
    LeaveOneOutSpec(
        label="Global walk d_mean",
        branch="cohort_walk_primary",
        source_dir="contrasts_cohort_121725",
        contrast_name="HC_vs_PD_walk",
        metric="d_mean",
        mode="group_walk",
    ),
    LeaveOneOutSpec(
        label="Global walk d_median",
        branch="cohort_walk_primary",
        source_dir="contrasts_cohort_121725",
        contrast_name="HC_vs_PD_walk",
        metric="d_median",
        mode="group_walk",
    ),
    LeaveOneOutSpec(
        label="PD paired d_n_mean",
        branch="pd_paired_primary",
        source_dir="contrasts_subject_121725",
        contrast_name="PD_walk_vs_rest",
        metric="d_n_mean",
        mode="paired_group",
        group="PD",
    ),
    LeaveOneOutSpec(
        label="PD paired m_a_iqr",
        branch="pd_paired_primary",
        source_dir="global_subject_121725_iqr_mad",
        contrast_name="PD_walk_vs_rest",
        metric="m_a_iqr",
        mode="paired_group",
        group="PD",
    ),
    LeaveOneOutSpec(
        label="PD paired d_iqr",
        branch="pd_paired_primary",
        source_dir="global_subject_121725_iqr_mad",
        contrast_name="PD_walk_vs_rest",
        metric="d_iqr",
        mode="paired_group",
        group="PD",
    ),
    LeaveOneOutSpec(
        label="PD paired d_mad",
        branch="pd_paired_primary",
        source_dir="global_subject_121725_iqr_mad",
        contrast_name="PD_walk_vs_rest",
        metric="d_mad",
        mode="paired_group",
        group="PD",
    ),
    LeaveOneOutSpec(
        label="HC context m_a_mean",
        branch="hc_paired_context",
        source_dir="contrasts_subject_121725",
        contrast_name="HC_walk_vs_rest",
        metric="m_a_mean",
        mode="paired_group",
        group="HC",
    ),
)

TIME_SHUFFLE_SPECS: tuple[TimeShuffleSpec, ...] = (
    TimeShuffleSpec(
        label="Rest trajectory noetic_action_kinetic (3D)",
        contrast_name="HC_vs_PD_rest_trajectory_3d",
        task="rest",
        dimension=3,
        metric="noetic_action_kinetic",
    ),
    TimeShuffleSpec(
        label="Rest trajectory curvature_median (3D)",
        contrast_name="HC_vs_PD_rest_trajectory_3d",
        task="rest",
        dimension=3,
        metric="curvature_median",
    ),
    TimeShuffleSpec(
        label="Rest trajectory path_length (3D)",
        contrast_name="HC_vs_PD_rest_trajectory_3d",
        task="rest",
        dimension=3,
        metric="path_length",
    ),
    TimeShuffleSpec(
        label="Rest trajectory noetic_action_jerk (3D)",
        contrast_name="HC_vs_PD_rest_trajectory_3d",
        task="rest",
        dimension=3,
        metric="noetic_action_jerk",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run additional leave-one-out and time-reshuffle QC checks for the Parkinson walking article."
    )
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=DEFAULT_DATASET_ROOT if DEFAULT_DATASET_ROOT.exists() else SUPPORT_DATASET_ROOT,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--shuffle-permutations", type=int, default=DEFAULT_SHUFFLE_PERMUTATIONS)
    return parser.parse_args()


def read_csv(results_dir: Path, *parts: str) -> pd.DataFrame:
    return pd.read_csv(results_dir.joinpath(*parts), low_memory=False)


def safe_float_series(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce")


def compute_group_effect(frame: pd.DataFrame, metric: str) -> dict[str, float]:
    work = frame.copy()
    work[metric] = safe_float_series(work, metric)
    left = work.loc[(work["group"] == "HC") & (work["task"] == "walk"), metric].dropna().to_numpy(dtype=float)
    right = work.loc[(work["group"] == "PD") & (work["task"] == "walk"), metric].dropna().to_numpy(dtype=float)
    if left.size < 3 or right.size < 3:
        return {
            "left_n": int(left.size),
            "right_n": int(right.size),
            "left_median": float("nan"),
            "right_median": float("nan"),
            "effect_size": float("nan"),
            "p_value": float("nan"),
        }
    stat, p_value = mannwhitneyu(left, right, alternative="two-sided")
    return {
        "left_n": int(left.size),
        "right_n": int(right.size),
        "left_median": float(np.median(left)),
        "right_median": float(np.median(right)),
        "effect_size": float(cohens_d(left, right)),
        "p_value": float(p_value),
        "test_stat": float(stat),
    }


def paired_frame(frame: pd.DataFrame, metric: str, group: str) -> pd.DataFrame:
    work = frame.copy()
    work = work[work["group"] == group].copy()
    work[metric] = safe_float_series(work, metric)
    rest = work[work["task"] == "rest"][["participant_id", metric]].rename(columns={metric: "value_rest"})
    walk = work[work["task"] == "walk"][["participant_id", metric]].rename(columns={metric: "value_walk"})
    merged = rest.merge(walk, on="participant_id", how="inner")
    merged["diff"] = pd.to_numeric(merged["value_walk"], errors="coerce") - pd.to_numeric(merged["value_rest"], errors="coerce")
    merged = merged[np.isfinite(merged["value_rest"]) & np.isfinite(merged["value_walk"]) & np.isfinite(merged["diff"])].copy()
    return merged.reset_index(drop=True)


def compute_paired_effect(frame: pd.DataFrame, metric: str, group: str) -> dict[str, float]:
    merged = paired_frame(frame, metric, group)
    diff = merged["diff"].to_numpy(dtype=float)
    if diff.size < 3:
        return {
            "left_n": int(diff.size),
            "right_n": int(diff.size),
            "left_median": float("nan"),
            "right_median": float("nan"),
            "effect_size": float("nan"),
            "p_value": float("nan"),
        }
    try:
        stat, p_value = wilcoxon(diff, alternative="two-sided", zero_method="wilcox")
        test_stat = float(stat)
    except ValueError:
        p_value = 1.0
        test_stat = float("nan")
    return {
        "left_n": int(diff.size),
        "right_n": int(diff.size),
        "left_median": float(np.median(merged["value_rest"])),
        "right_median": float(np.median(merged["value_walk"])),
        "effect_size": float(cohens_dz(diff)),
        "p_value": float(p_value),
        "test_stat": test_stat,
    }


def summarize_leave_one_out(
    spec: LeaveOneOutSpec,
    run_frame: pd.DataFrame,
    contrast_frame: pd.DataFrame,
) -> dict[str, Any]:
    contrast_row = contrast_frame[
        (contrast_frame["contrast_name"] == spec.contrast_name) & (contrast_frame["metric"] == spec.metric)
    ]
    if contrast_row.empty:
        raise KeyError(f"Could not locate contrast row for {spec}")
    contrast_row = contrast_row.iloc[0]
    observed = compute_group_effect(run_frame, spec.metric) if spec.mode == "group_walk" else compute_paired_effect(run_frame, spec.metric, str(spec.group))
    if spec.mode == "group_walk":
        relevant = run_frame.copy()
        relevant[spec.metric] = safe_float_series(relevant, spec.metric)
        relevant = relevant[
            (relevant["task"] == "walk")
            & (relevant["group"].isin(["HC", "PD"]))
            & np.isfinite(relevant[spec.metric])
        ].copy()
        participant_ids = sorted(relevant["participant_id"].dropna().astype(str).unique().tolist())
    else:
        participant_ids = sorted(paired_frame(run_frame, spec.metric, str(spec.group))["participant_id"].dropna().astype(str).unique().tolist())
    loo_effects: list[float] = []
    loo_ps: list[float] = []
    omitted_ids: list[str] = []
    for participant_id in participant_ids:
        reduced = run_frame[run_frame["participant_id"].astype(str) != participant_id].copy()
        result = compute_group_effect(reduced, spec.metric) if spec.mode == "group_walk" else compute_paired_effect(reduced, spec.metric, str(spec.group))
        if np.isfinite(result["effect_size"]):
            loo_effects.append(float(result["effect_size"]))
            loo_ps.append(float(result["p_value"]))
            omitted_ids.append(str(participant_id))
    observed_effect = float(observed["effect_size"])
    sign_consistency = (
        float(np.mean(np.sign(np.asarray(loo_effects, dtype=float)) == np.sign(observed_effect)))
        if loo_effects and np.isfinite(observed_effect)
        else float("nan")
    )
    weakest_index = int(np.argmin(np.abs(np.asarray(loo_effects, dtype=float)))) if loo_effects else -1
    return {
        "label": spec.label,
        "branch": spec.branch,
        "mode": spec.mode,
        "contrast_name": spec.contrast_name,
        "metric": spec.metric,
        "group": spec.group,
        "source_dir": spec.source_dir,
        "full_effect_size": observed_effect,
        "full_p_value": float(observed["p_value"]),
        "full_q_value": float(contrast_row["q_value"]),
        "full_left_median": float(observed["left_median"]),
        "full_right_median": float(observed["right_median"]),
        "left_n": int(observed["left_n"]),
        "right_n": int(observed["right_n"]),
        "leave_one_out_effect_min": float(np.min(loo_effects)) if loo_effects else float("nan"),
        "leave_one_out_effect_max": float(np.max(loo_effects)) if loo_effects else float("nan"),
        "leave_one_out_effect_median": float(np.median(loo_effects)) if loo_effects else float("nan"),
        "leave_one_out_p_min": float(np.min(loo_ps)) if loo_ps else float("nan"),
        "leave_one_out_p_max": float(np.max(loo_ps)) if loo_ps else float("nan"),
        "sign_consistency": sign_consistency,
        "worst_case_participant": omitted_ids[weakest_index] if weakest_index >= 0 else "",
        "n_omissions": int(len(loo_effects)),
    }


def h5_paths(dataset_root: Path) -> list[Path]:
    return sorted(dataset_root.glob("sub-*_*/*.h5"))


def fit_metric_diag_3d(dataset_root: Path) -> np.ndarray:
    blocks: list[np.ndarray] = []
    for h5_path in h5_paths(dataset_root):
        with h5py.File(h5_path, "r") as handle:
            if "coords_3d_cohort_anchored/values" not in handle:
                continue
            coords = np.asarray(handle["coords_3d_cohort_anchored/values"], dtype=float)
        coords = coords[np.isfinite(coords).all(axis=1)]
        if coords.shape[0] < 16:
            continue
        blocks.append(sample_evenly(coords, 256))
    if not blocks:
        raise RuntimeError(f"No usable 3D coordinates found under {dataset_root}")
    sampled = np.concatenate(blocks, axis=0)
    sampled = sample_evenly(sampled, 40000)
    return stable_variance_metric(sampled)


def load_rest_trajectory_payloads(dataset_root: Path) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for h5_path in h5_paths(dataset_root):
        participant_id = h5_path.stem.split("_")[0]
        task = h5_path.stem.split("_")[1]
        if task != "rest":
            continue
        with h5py.File(h5_path, "r") as handle:
            coords = np.asarray(handle["coords_3d_cohort_anchored/values"], dtype=float)
            time = np.asarray(handle["time"], dtype=float) if "time" in handle else np.full((coords.shape[0],), np.nan)
            participant_json = handle["participant/mapped_json"][()] if "participant/mapped_json" in handle else b"{}"
            try:
                mapped = json.loads(participant_json.decode("utf-8") if isinstance(participant_json, (bytes, bytearray)) else str(participant_json))
            except Exception:
                mapped = {}
            group = str(handle.attrs.get("meta_group") or mapped.get("group") or "").strip()
        finite_mask = np.isfinite(coords).all(axis=1)
        coords = coords[finite_mask]
        time = time[finite_mask]
        if coords.shape[0] < 8:
            continue
        payloads.append(
            {
                "participant_id": participant_id,
                "group": group,
                "coords": coords,
                "time": time,
            }
        )
    return payloads


def shuffled_metrics(coords: np.ndarray, time: np.ndarray, metric_diag: np.ndarray, rng: np.random.Generator) -> dict[str, float]:
    order = rng.permutation(coords.shape[0])
    shuffled = coords[order]
    action = noetic_action_metrics(shuffled, time, metric_diag=metric_diag)
    return {
        "path_length": path_length(shuffled),
        "curvature_median": robust_median(curvature_series(shuffled, time)),
        "noetic_action_kinetic": float(action["noetic_action_kinetic"]),
        "noetic_action_jerk": float(action["noetic_action_jerk"]),
    }


def run_time_reshuffle_null(
    dataset_root: Path,
    trajectory_run_metrics: pd.DataFrame,
    trajectory_group_contrasts: pd.DataFrame,
    *,
    permutations: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_diag = fit_metric_diag_3d(dataset_root)
    payloads = load_rest_trajectory_payloads(dataset_root)
    rng = np.random.default_rng(20260612)
    draw_rows: list[dict[str, Any]] = []
    for perm_idx in range(permutations):
        metric_rows: list[dict[str, Any]] = []
        for payload in payloads:
            shuffled = shuffled_metrics(payload["coords"], payload["time"], metric_diag, rng)
            for metric, value in shuffled.items():
                metric_rows.append(
                    {
                        "participant_id": payload["participant_id"],
                        "group": payload["group"],
                        "task": "rest",
                        "metric": metric,
                        "value": value,
                    }
                )
        perm_frame = pd.DataFrame(metric_rows)
        for spec in TIME_SHUFFLE_SPECS:
            block = perm_frame[perm_frame["metric"] == spec.metric].copy()
            left = pd.to_numeric(block.loc[block["group"] == "HC", "value"], errors="coerce").dropna().to_numpy(dtype=float)
            right = pd.to_numeric(block.loc[block["group"] == "PD", "value"], errors="coerce").dropna().to_numpy(dtype=float)
            effect_size = float(cohens_d(left, right)) if left.size >= 3 and right.size >= 3 else float("nan")
            draw_rows.append(
                {
                    "permutation_idx": int(perm_idx),
                    "label": spec.label,
                    "contrast_name": spec.contrast_name,
                    "metric": spec.metric,
                    "null_effect_size": effect_size,
                    "null_abs_effect_size": abs(effect_size) if np.isfinite(effect_size) else float("nan"),
                    "hc_median": float(np.median(left)) if left.size else float("nan"),
                    "pd_median": float(np.median(right)) if right.size else float("nan"),
                }
            )
    draws = pd.DataFrame(draw_rows)
    summary_rows: list[dict[str, Any]] = []
    for spec in TIME_SHUFFLE_SPECS:
        observed = trajectory_group_contrasts[
            (trajectory_group_contrasts["contrast_name"] == spec.contrast_name)
            & (trajectory_group_contrasts["metric"] == spec.metric)
        ]
        if observed.empty:
            continue
        observed = observed.iloc[0]
        spec_draws = draws[draws["metric"] == spec.metric].copy()
        abs_null = pd.to_numeric(spec_draws["null_abs_effect_size"], errors="coerce").dropna().to_numpy(dtype=float)
        observed_abs = abs(float(observed["effect_size"]))
        exceed = int(np.sum(abs_null >= observed_abs))
        empirical_p = float((exceed + 1) / (abs_null.size + 1)) if abs_null.size else float("nan")
        summary_rows.append(
            {
                "label": spec.label,
                "contrast_name": spec.contrast_name,
                "task": spec.task,
                "dimension": int(spec.dimension),
                "metric": spec.metric,
                "observed_effect_size": float(observed["effect_size"]),
                "observed_p_value": float(observed["p_value"]),
                "observed_q_value": float(observed["q_value"]),
                "observed_hc_median": float(observed["left_median"]),
                "observed_pd_median": float(observed["right_median"]),
                "null_mean_abs_d": float(np.mean(abs_null)) if abs_null.size else float("nan"),
                "null_p95_abs_d": float(np.percentile(abs_null, 95.0)) if abs_null.size else float("nan"),
                "empirical_p": empirical_p,
                "n_permutations": int(abs_null.size),
            }
        )
    return pd.DataFrame(summary_rows), draws


def classical_status_row(results_dir: Path) -> pd.DataFrame:
    manifest = json.loads((results_dir / "classical_cohort_121725" / "classical_manifest.json").read_text(encoding="utf-8"))
    return pd.DataFrame(
        [
            {
                "layer": "classical_eeg_sidecars",
                "status": "unavailable" if int(manifest.get("n_h5_with_classical_extension", 0)) == 0 else "available",
                "n_h5_total": int(manifest.get("n_h5_total", 0)),
                "n_h5_with_classical_extension": int(manifest.get("n_h5_with_classical_extension", 0)),
                "review_implication": (
                    "No direct benchmark claim against classical EEG is justified from this bundle because the conventional_eeg extension is absent."
                    if int(manifest.get("n_h5_with_classical_extension", 0)) == 0
                    else "Classical sidecars are available."
                ),
            }
        ]
    )


def build_summary_markdown(
    classical_status: pd.DataFrame,
    loo_summary: pd.DataFrame,
    time_shuffle_summary: pd.DataFrame,
) -> str:
    lines = [
        "# Additional Parkinson walking QC / robustness summary",
        "",
        "This supplement-facing QC pass adds three checks to the walking manuscript:",
        "",
        "1. explicit classical-comparator availability status,",
        "2. leave-one-subject-out stability for the revised focal rows,",
        "3. and a time-reshuffle null for the leading exploratory trajectory rows.",
        "",
        "## Classical comparator status",
        "",
    ]
    for _, row in classical_status.iterrows():
        lines.append(
            f"- `{row['layer']}`: status `{row['status']}` with `{int(row['n_h5_with_classical_extension'])}` / `{int(row['n_h5_total'])}` H5 files carrying the required extension. {row['review_implication']}"
        )
    lines.extend(["", "## Leave-one-subject-out stability", ""])
    for _, row in loo_summary.iterrows():
        lines.append(
            f"- `{row['label']}`: full effect `{fmt(row['full_effect_size'])}`, full `q = {fmt(row['full_q_value'])}`, "
            f"leave-one-out effect range `{fmt(row['leave_one_out_effect_min'])}` to `{fmt(row['leave_one_out_effect_max'])}`, "
            f"median `{fmt(row['leave_one_out_effect_median'])}`, sign consistency `{fmt(row['sign_consistency'])}`, "
            f"worst-case omission `{row['worst_case_participant']}`."
        )
    lines.extend(["", "## Time-reshuffle null for trajectory rows", ""])
    for _, row in time_shuffle_summary.iterrows():
        lines.append(
            f"- `{row['label']}`: observed `d = {fmt(row['observed_effect_size'])}`, observed `q = {fmt(row['observed_q_value'])}`, "
            f"null mean `|d| = {fmt(row['null_mean_abs_d'])}`, null p95 `|d| = {fmt(row['null_p95_abs_d'])}`, "
            f"empirical `p = {fmt(row['empirical_p'])}` across `{int(row['n_permutations'])}` reshuffles."
        )
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- The leave-one-out pass checks row stability, not external replication.",
            "- The time-reshuffle null permutes exported window order within run. It therefore tests whether trajectory findings depend on temporal order, but it is not a raw-signal permutation analysis.",
            "- Classical EEG remains an availability boundary rather than a comparator result in this bundle.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)

    classical_status = classical_status_row(args.results_dir)

    run_frames = {
        "contrasts_cohort_121725": read_csv(args.results_dir, "contrasts_cohort_121725", "run_metrics_cohort.csv"),
        "contrasts_subject_121725": read_csv(args.results_dir, "contrasts_subject_121725", "run_metrics_subject.csv"),
        "global_subject_121725_iqr_mad": read_csv(args.results_dir, "global_subject_121725_iqr_mad", "run_metrics_subject.csv"),
    }
    contrast_frames = {
        "contrasts_cohort_121725": read_csv(args.results_dir, "contrasts_cohort_121725", "group_contrasts.csv"),
        "contrasts_subject_121725": read_csv(args.results_dir, "contrasts_subject_121725", "paired_task_contrasts.csv"),
        "global_subject_121725_iqr_mad": read_csv(args.results_dir, "global_subject_121725_iqr_mad", "paired_task_contrasts.csv"),
    }

    loo_rows = [
        summarize_leave_one_out(spec, run_frames[spec.source_dir], contrast_frames[spec.source_dir])
        for spec in LEAVE_ONE_OUT_SPECS
    ]
    loo_summary = pd.DataFrame(loo_rows)

    trajectory_run_metrics = read_csv(args.results_dir, "trajectory_cohort_121725", "trajectory_run_metrics.csv")
    trajectory_group_contrasts = read_csv(args.results_dir, "trajectory_cohort_121725", "trajectory_group_contrasts.csv")
    time_shuffle_summary, time_shuffle_draws = run_time_reshuffle_null(
        args.dataset_root,
        trajectory_run_metrics,
        trajectory_group_contrasts,
        permutations=int(args.shuffle_permutations),
    )

    classical_status.to_csv(args.output_dir / "qc_classical_comparator_summary.csv", index=False)
    loo_summary.to_csv(args.output_dir / "qc_leave_one_subject_out_metrics.csv", index=False)
    time_shuffle_summary.to_csv(args.output_dir / "qc_time_reshuffle_summary.csv", index=False)
    time_shuffle_draws.to_csv(args.output_dir / "qc_time_reshuffle_null_draws.csv", index=False)

    summary_md = build_summary_markdown(classical_status, loo_summary, time_shuffle_summary)
    (args.output_dir / "additional_qc_summary.md").write_text(summary_md, encoding="utf-8")

    manifest = {
        "results_dir": str(args.results_dir),
        "dataset_root": str(args.dataset_root),
        "output_dir": str(args.output_dir),
        "shuffle_permutations": int(args.shuffle_permutations),
        "classical_status_csv": str(args.output_dir / "qc_classical_comparator_summary.csv"),
        "leave_one_out_csv": str(args.output_dir / "qc_leave_one_subject_out_metrics.csv"),
        "time_reshuffle_summary_csv": str(args.output_dir / "qc_time_reshuffle_summary.csv"),
        "time_reshuffle_draws_csv": str(args.output_dir / "qc_time_reshuffle_null_draws.csv"),
        "summary_md": str(args.output_dir / "additional_qc_summary.md"),
        "note": "Classical comparator rows remain unavailable because the conventional_eeg extension is absent in this bundle.",
    }
    (args.output_dir / "additional_qc_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
