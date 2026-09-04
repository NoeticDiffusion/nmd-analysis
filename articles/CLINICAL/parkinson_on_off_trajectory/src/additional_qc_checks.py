from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr, wilcoxon

from compute_parkinson_event_metrics import (
    analysis_type_for_key,
    build_local_window,
    gather_reference_segments,
    load_runs,
    trimmed_indices,
)
from parkinson_trajectory_support import (
    COHORT_COORDINATE_CONTRACT,
    DATASET_ROOT,
    POST_EVENT_WINDOWS,
    PRE_EVENT_WINDOWS,
    RESULTS_DIR,
    SUBJECT_COORDINATE_CONTRACT,
    SpaceKey,
    build_reference_model,
    cohens_d,
    cohens_dz,
    ensure_dir,
    summarize_segment_metrics,
)


DEFAULT_OUTPUT_DIR = RESULTS_DIR / "additional_qc_20260603_classical_shuffle"
DEFAULT_SHIFT_PERMUTATIONS = 24
EVENT_SUMMARY_FILENAME = "additional_qc_summary.md"
MANIFEST_FILENAME = "additional_qc_manifest.json"
FOCAL_CLASSICAL_SUMMARY_CSV = "qc_focal_nmd_vs_classical_summary.csv"
FOCAL_CLASSICAL_ALL_CSV = "qc_focal_nmd_vs_classical_all.csv"


@dataclass(frozen=True)
class MetricSpec:
    contrast_name: str
    source: str
    contract: str
    analysis_type: str
    metric: str
    label: str
    network: str | None = None
    segment_kind: str | None = None
    segment_label: str | None = None


FOCAL_SPECS: tuple[MetricSpec, ...] = (
    MetricSpec(
        contrast_name="Control_vs_Parkinson_OFF",
        source="standard",
        contract=COHORT_COORDINATE_CONTRACT,
        analysis_type="regional_9d",
        network="frontal",
        metric="d_n_std",
        label="Control vs OFF / frontal 9D d_n_std",
    ),
    MetricSpec(
        contrast_name="Control_vs_Parkinson_OFF",
        source="event",
        contract=COHORT_COORDINATE_CONTRACT,
        analysis_type="global_event_locked_trajectory_3d",
        network="global",
        segment_kind="baseline",
        segment_label="eyes_closed",
        metric="speed_median",
        label="Control vs OFF / eyes_closed speed_median (3D)",
    ),
    MetricSpec(
        contrast_name="Control_vs_Parkinson_OFF",
        source="event",
        contract=COHORT_COORDINATE_CONTRACT,
        analysis_type="global_event_locked_trajectory_9d",
        network="global",
        segment_kind="baseline",
        segment_label="eyes_closed",
        metric="noetic_action_kinetic",
        label="Control vs OFF / eyes_closed noetic_action_kinetic (9D)",
    ),
    MetricSpec(
        contrast_name="Control_vs_Parkinson_ON",
        source="standard",
        contract=COHORT_COORDINATE_CONTRACT,
        analysis_type="global_mnps_jacobian_9d",
        metric="mdr_median",
        label="Control vs ON / global 9D mdr_median",
    ),
    MetricSpec(
        contrast_name="Control_vs_Parkinson_ON",
        source="event",
        contract=COHORT_COORDINATE_CONTRACT,
        analysis_type="global_event_locked_trajectory_3d",
        network="global",
        segment_kind="event",
        segment_label="novel_tone",
        metric="hysteresis_area_me",
        label="Control vs ON / novel_tone hysteresis_area_me",
    ),
    MetricSpec(
        contrast_name="Control_vs_Parkinson_ON",
        source="event",
        contract=COHORT_COORDINATE_CONTRACT,
        analysis_type="global_event_locked_trajectory_3d",
        network="global",
        segment_kind="event",
        segment_label="standard_tone",
        metric="hysteresis_area_me",
        label="Control vs ON / standard_tone hysteresis_area_me",
    ),
    MetricSpec(
        contrast_name="Parkinson_OFF_vs_ON",
        source="standard",
        contract=SUBJECT_COORDINATE_CONTRACT,
        analysis_type="tier2_jacobian",
        metric="signed_divergence_balance_mean_neg",
        label="OFF vs ON / signed_divergence_balance_mean_neg",
    ),
)

CLASSICAL_BEST_SPECS: tuple[MetricSpec, ...] = (
    MetricSpec(
        contrast_name="Control_vs_Parkinson_OFF",
        source="classical",
        contract=COHORT_COORDINATE_CONTRACT,
        analysis_type="eeg_classical_comparators",
        metric="eeg_classical_ratio_theta_alpha_median",
        label="Classical best / Control vs OFF / theta-alpha ratio median",
    ),
    MetricSpec(
        contrast_name="Control_vs_Parkinson_ON",
        source="classical",
        contract=COHORT_COORDINATE_CONTRACT,
        analysis_type="eeg_classical_comparators",
        metric="eeg_classical_ratio_theta_alpha_median",
        label="Classical best / Control vs ON / theta-alpha ratio median",
    ),
    MetricSpec(
        contrast_name="Parkinson_OFF_vs_ON",
        source="classical",
        contract=SUBJECT_COORDINATE_CONTRACT,
        analysis_type="eeg_classical_comparators",
        metric="eeg_classical_relative_theta_median",
        label="Classical best / OFF vs ON / relative theta median",
    ),
)

TIME_SHIFT_SPECS: tuple[MetricSpec, ...] = tuple(spec for spec in FOCAL_SPECS if spec.source == "event")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run additional Parkinson QC / robustness checks for geometry and classical EEG comparators.")
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--shift-permutations", type=int, default=DEFAULT_SHIFT_PERMUTATIONS)
    return parser.parse_args()


def latest_parquet(root: Path, analysis_type: str) -> Path:
    matches = sorted(root.glob(f"ds003490_{analysis_type}_*.parquet"), key=lambda path: path.stat().st_mtime_ns)
    if not matches:
        raise FileNotFoundError(f"No {analysis_type} parquet found under {root}")
    return matches[-1]


def load_standard_metrics(results_dir: Path, contract: str) -> pd.DataFrame:
    analysis_dirname = "standard_analysis_cohort" if contract == COHORT_COORDINATE_CONTRACT else "standard_analysis_subject"
    frame = pd.read_parquet(latest_parquet(results_dir / analysis_dirname, "subject_metrics"))
    frame["requested_coordinate_contract"] = contract
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame


def load_event_metrics(results_dir: Path, contract: str) -> pd.DataFrame:
    dirname = "event_metrics_cohort" if contract == COHORT_COORDINATE_CONTRACT else "event_metrics_subject"
    return pd.read_csv(results_dir / dirname / "event_subject_metrics.csv", low_memory=False)


def load_classical_metrics(results_dir: Path, contract: str) -> pd.DataFrame:
    filename = (
        "eeg_classical_subject_metrics_cohort_anchor.csv"
        if contract == COHORT_COORDINATE_CONTRACT
        else "eeg_classical_subject_metrics_subject_anchor.csv"
    )
    frame = pd.read_csv(results_dir / filename, low_memory=False)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame


def load_primary_contrasts(results_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    standard = pd.read_csv(results_dir / "primary_standard_contrasts.csv", low_memory=False)
    event = pd.read_csv(results_dir / "primary_event_contrasts.csv", low_memory=False)
    classical = pd.read_csv(results_dir / "eeg_classical_primary_contrasts.csv", low_memory=False)
    return standard, event, classical


def filter_long_metric(frame: pd.DataFrame, spec: MetricSpec) -> pd.DataFrame:
    work = frame.copy()
    if "analysis_type" in work.columns:
        work = work[work["analysis_type"] == spec.analysis_type]
    if "metric" in work.columns:
        work = work[work["metric"] == spec.metric]
    if spec.network is not None and "network" in work.columns:
        work = work[work["network"].fillna("").astype(str) == spec.network]
    work["value"] = pd.to_numeric(work["value"], errors="coerce")
    work = work[np.isfinite(work["value"])].copy()
    return work


def filter_event_metric(frame: pd.DataFrame, spec: MetricSpec) -> pd.DataFrame:
    work = frame.copy()
    work = work[
        (work["analysis_type"] == spec.analysis_type)
        & (work["segment_label"] == spec.segment_label)
        & (work["segment_kind"] == spec.segment_kind)
    ].copy()
    if spec.network is not None:
        work = work[work["network"] == spec.network].copy()
    work["value"] = pd.to_numeric(work[spec.metric], errors="coerce")
    work = work[np.isfinite(work["value"])].copy()
    return work


def metric_subject_frame(
    spec: MetricSpec,
    standard_frames: dict[str, pd.DataFrame],
    event_frames: dict[str, pd.DataFrame],
    classical_frames: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    if spec.source == "standard":
        return filter_long_metric(standard_frames[spec.contract], spec)
    if spec.source == "event":
        return filter_event_metric(event_frames[spec.contract], spec)
    if spec.source == "classical":
        return filter_long_metric(classical_frames[spec.contract], spec)
    raise ValueError(f"Unsupported source: {spec.source}")


def contrast_value_frames(frame: pd.DataFrame, contrast_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    if contrast_name == "Parkinson_OFF_vs_ON":
        left = frame[(frame["group"] == "Parkinson") & (frame["condition"] == "OFF")].copy()
        right = frame[(frame["group"] == "Parkinson") & (frame["condition"] == "ON")].copy()
        return left, right
    if contrast_name == "Control_vs_Parkinson_OFF":
        left = frame[(frame["group"] == "Control") & (frame["condition"] == "not_applicable")].copy()
        right = frame[(frame["group"] == "Parkinson") & (frame["condition"] == "OFF")].copy()
        return left, right
    if contrast_name == "Control_vs_Parkinson_ON":
        left = frame[(frame["group"] == "Control") & (frame["condition"] == "not_applicable")].copy()
        right = frame[(frame["group"] == "Parkinson") & (frame["condition"] == "ON")].copy()
        return left, right
    raise ValueError(f"Unknown contrast: {contrast_name}")


def contrast_effect(frame: pd.DataFrame, contrast_name: str) -> tuple[float, float, int]:
    left, right = contrast_value_frames(frame, contrast_name)
    if contrast_name == "Parkinson_OFF_vs_ON":
        merged = left[["subject_id", "value"]].merge(right[["subject_id", "value"]], on="subject_id", suffixes=("_off", "_on"), how="inner")
        if merged.shape[0] < 3:
            return float("nan"), float("nan"), int(merged.shape[0])
        diff = merged["value_on"].to_numpy(dtype=float) - merged["value_off"].to_numpy(dtype=float)
        try:
            p_value = float(wilcoxon(diff, alternative="two-sided", zero_method="wilcox").pvalue)
        except ValueError:
            p_value = 1.0
        return cohens_dz(diff), p_value, int(merged.shape[0])
    left_values = pd.to_numeric(left["value"], errors="coerce").dropna().to_numpy(dtype=float)
    right_values = pd.to_numeric(right["value"], errors="coerce").dropna().to_numpy(dtype=float)
    if left_values.size < 3 or right_values.size < 3:
        return float("nan"), float("nan"), int(min(left_values.size, right_values.size))
    p_value = float(mannwhitneyu(left_values, right_values, alternative="two-sided").pvalue)
    return cohens_d(left_values, right_values), p_value, int(min(left_values.size, right_values.size))


def summarize_leave_one_out(frame: pd.DataFrame, spec: MetricSpec) -> dict[str, Any]:
    observed_d, observed_p, observed_n = contrast_effect(frame, spec.contrast_name)
    loo_ds: list[float] = []
    loo_ps: list[float] = []
    omitted: list[str] = []
    for subject_id in sorted(frame["subject_id"].dropna().astype(str).unique().tolist()):
        reduced = frame[frame["subject_id"].astype(str) != subject_id].copy()
        d_value, p_value, _ = contrast_effect(reduced, spec.contrast_name)
        if np.isfinite(d_value):
            loo_ds.append(float(d_value))
            loo_ps.append(float(p_value))
            omitted.append(str(subject_id))
    sign_consistency = (
        float(np.mean(np.sign(np.asarray(loo_ds, dtype=float)) == np.sign(observed_d)))
        if loo_ds and np.isfinite(observed_d)
        else float("nan")
    )
    return {
        "label": spec.label,
        "contrast_name": spec.contrast_name,
        "source": spec.source,
        "metric": spec.metric,
        "analysis_type": spec.analysis_type,
        "segment_label": spec.segment_label,
        "network": spec.network,
        "full_d": observed_d,
        "full_p": observed_p,
        "full_n": observed_n,
        "leave_one_out_d_min": float(np.min(loo_ds)) if loo_ds else float("nan"),
        "leave_one_out_d_max": float(np.max(loo_ds)) if loo_ds else float("nan"),
        "leave_one_out_d_median": float(np.median(loo_ds)) if loo_ds else float("nan"),
        "leave_one_out_p_min": float(np.min(loo_ps)) if loo_ps else float("nan"),
        "leave_one_out_p_max": float(np.max(loo_ps)) if loo_ps else float("nan"),
        "sign_consistency": sign_consistency,
        "worst_case_subject": omitted[int(np.argmin(np.abs(loo_ds)))] if loo_ds else "",
    }


def fmt(value: object) -> str:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return "nan"
    if not pd.notna(parsed):
        return "nan"
    return f"{parsed:.4g}"


def summarize_classical_vs_geometry(
    standard_primary: pd.DataFrame,
    event_primary: pd.DataFrame,
    classical_primary: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    ndt_frame = pd.concat([standard_primary, event_primary], ignore_index=True)
    for contrast_name in ["Control_vs_Parkinson_OFF", "Control_vs_Parkinson_ON", "Parkinson_OFF_vs_ON"]:
        ndt_block = ndt_frame[ndt_frame["contrast_name"] == contrast_name].copy()
        classical_block = classical_primary[classical_primary["contrast_name"] == contrast_name].copy()
        if ndt_block.empty or classical_block.empty:
            continue
        ndt_block["abs_d"] = pd.to_numeric(ndt_block["effect_size"], errors="coerce").abs()
        classical_block["abs_d"] = pd.to_numeric(classical_block["effect_size"], errors="coerce").abs()
        ndt_row = ndt_block.sort_values(["q_value", "p_value", "abs_d"], ascending=[True, True, False], na_position="last").iloc[0]
        classical_row = classical_block.sort_values(["q_value", "p_value", "abs_d"], ascending=[True, True, False], na_position="last").iloc[0]
        rows.append(
            {
                "contrast_name": contrast_name,
                "best_geometry_metric": str(ndt_row["metric"]),
                "best_geometry_layer": str(ndt_row["analysis_type"]),
                "best_geometry_effect_size": float(ndt_row["effect_size"]),
                "best_geometry_q": float(ndt_row["q_value"]),
                "best_classical_metric": str(classical_row["metric"]),
                "best_classical_effect_size": float(classical_row["effect_size"]),
                "best_classical_q": float(classical_row["q_value"]),
                "abs_d_gap_geometry_minus_classical": float(abs(float(ndt_row["effect_size"])) - abs(float(classical_row["effect_size"]))),
            }
        )
    return pd.DataFrame(rows)


def classical_correlation_candidates(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "metric" not in frame.columns:
        return frame.copy()
    metrics = frame["metric"].astype(str)
    mask = metrics.str.endswith("_median") & ~metrics.str.endswith("delta_mean_median")
    return frame[mask].copy().reset_index(drop=True)


def subset_frame_for_contrast(frame: pd.DataFrame, contrast_name: str) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    if contrast_name == "Control_vs_Parkinson_OFF":
        mask = ((frame["group"] == "Control") & (frame["condition"] == "not_applicable")) | (
            (frame["group"] == "Parkinson") & (frame["condition"] == "OFF")
        )
        return frame[mask].copy()
    if contrast_name == "Control_vs_Parkinson_ON":
        mask = ((frame["group"] == "Control") & (frame["condition"] == "not_applicable")) | (
            (frame["group"] == "Parkinson") & (frame["condition"] == "ON")
        )
        return frame[mask].copy()
    if contrast_name == "Parkinson_OFF_vs_ON":
        return frame[(frame["group"] == "Parkinson") & (frame["condition"].isin(["OFF", "ON"]))].copy()
    raise ValueError(f"Unknown contrast: {contrast_name}")


def paired_delta_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["subject_id", "delta"])
    off = frame[frame["condition"] == "OFF"][["subject_id", "value"]].rename(columns={"value": "value_off"})
    on = frame[frame["condition"] == "ON"][["subject_id", "value"]].rename(columns={"value": "value_on"})
    merged = off.merge(on, on="subject_id", how="inner")
    merged["delta"] = pd.to_numeric(merged["value_on"], errors="coerce") - pd.to_numeric(merged["value_off"], errors="coerce")
    merged = merged[np.isfinite(pd.to_numeric(merged["delta"], errors="coerce"))].copy()
    return merged[["subject_id", "delta"]].reset_index(drop=True)


def safe_spearman(left: pd.Series, right: pd.Series) -> tuple[float, float]:
    x = pd.to_numeric(left, errors="coerce").to_numpy(dtype=float)
    y = pd.to_numeric(right, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 6:
        return float("nan"), float("nan")
    x = x[mask]
    y = y[mask]
    if np.unique(x).size < 2 or np.unique(y).size < 2:
        return float("nan"), float("nan")
    rho, p_value = spearmanr(x, y)
    return float(rho), float(p_value)


def centered_group_spearman(merged: pd.DataFrame) -> tuple[float, float]:
    if merged.empty:
        return float("nan"), float("nan")
    work = merged.copy()
    work["stratum"] = work["group"].astype(str) + "::" + work["condition"].astype(str)
    work["focal_centered"] = work["value_focal"] - work.groupby("stratum")["value_focal"].transform("median")
    work["classical_centered"] = work["value_classical"] - work.groupby("stratum")["value_classical"].transform("median")
    return safe_spearman(work["focal_centered"], work["classical_centered"])


def interpret_classical_alignment(rho: float, adjusted_rho: float, *, paired: bool) -> str:
    reference_rho = adjusted_rho if np.isfinite(adjusted_rho) else rho
    if not np.isfinite(reference_rho):
        return "insufficient overlap"
    abs_rho = abs(float(reference_rho))
    if paired:
        if abs_rho < 0.3:
            return "limited paired alignment"
        if abs_rho < 0.6:
            return "partial paired alignment"
        return "strong paired alignment"
    if abs_rho < 0.3:
        return "contrast-aligned but not reducible in this check"
    if abs_rho < 0.6:
        return "partial alignment, but not reducible in this check"
    return "strong alignment; reducibility remains possible"


def association_priority_score(row: dict[str, Any]) -> float:
    adjusted_rho = float(row.get("group_adjusted_rho", np.nan))
    rho = float(row.get("spearman_rho", np.nan))
    if np.isfinite(adjusted_rho):
        return abs(adjusted_rho)
    if np.isfinite(rho):
        return abs(rho)
    return -1.0


def summarize_focal_vs_classical(
    standard_frames: dict[str, pd.DataFrame],
    event_frames: dict[str, pd.DataFrame],
    classical_frames: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for spec in FOCAL_SPECS:
        focal = metric_subject_frame(spec, standard_frames, event_frames, classical_frames)
        if focal.empty:
            continue
        focal = subset_frame_for_contrast(focal, spec.contrast_name)
        classical_candidates = classical_correlation_candidates(classical_frames[spec.contract])
        classical_candidates = subset_frame_for_contrast(classical_candidates, spec.contrast_name)
        best_row: dict[str, Any] | None = None
        for classical_metric, classical_metric_frame in classical_candidates.groupby("metric", dropna=False):
            if spec.contrast_name == "Parkinson_OFF_vs_ON":
                focal_delta = paired_delta_frame(focal)
                classical_delta = paired_delta_frame(classical_metric_frame)
                merged = focal_delta.merge(classical_delta, on="subject_id", how="inner", suffixes=("_focal", "_classical"))
                merged = merged.rename(columns={"delta_focal": "value_focal", "delta_classical": "value_classical"})
                rho, p_value = safe_spearman(merged["value_focal"], merged["value_classical"]) if not merged.empty else (float("nan"), float("nan"))
                adjusted_rho, adjusted_p = float("nan"), float("nan")
                n_value = int(len(merged))
            else:
                merged = focal[["subject_id", "group", "condition", "value"]].merge(
                    classical_metric_frame[["subject_id", "group", "condition", "value"]],
                    on=["subject_id", "group", "condition"],
                    how="inner",
                    suffixes=("_focal", "_classical"),
                )
                rho, p_value = safe_spearman(merged["value_focal"], merged["value_classical"]) if not merged.empty else (float("nan"), float("nan"))
                adjusted_rho, adjusted_p = centered_group_spearman(merged) if not merged.empty else (float("nan"), float("nan"))
                n_value = int(len(merged))
            row = {
                "label": spec.label,
                "contrast_name": spec.contrast_name,
                "analysis_type": spec.analysis_type,
                "segment_label": spec.segment_label,
                "network": spec.network,
                "metric": spec.metric,
                "classical_metric": str(classical_metric),
                "n": n_value,
                "spearman_rho": rho,
                "spearman_p": p_value,
                "group_adjusted_rho": adjusted_rho,
                "group_adjusted_p": adjusted_p,
                "paired_delta": bool(spec.contrast_name == "Parkinson_OFF_vs_ON"),
            }
            all_rows.append(row)
            score = association_priority_score(row)
            if best_row is None or score > association_priority_score(best_row):
                best_row = row
        if best_row is None:
            continue
        summary_rows.append(
            {
                **best_row,
                "interpretation": interpret_classical_alignment(
                    float(best_row.get("spearman_rho", np.nan)),
                    float(best_row.get("group_adjusted_rho", np.nan)),
                    paired=bool(best_row.get("paired_delta", False)),
                ),
            }
        )
    summary = pd.DataFrame(summary_rows)
    all_frame = pd.DataFrame(all_rows)
    if not summary.empty:
        summary = summary.sort_values(["contrast_name", "label"], na_position="last").reset_index(drop=True)
    if not all_frame.empty:
        all_frame = all_frame.sort_values(["contrast_name", "label", "classical_metric"], na_position="last").reset_index(drop=True)
    return summary, all_frame


def space_key_from_spec(spec: MetricSpec) -> SpaceKey:
    dims = 9 if spec.analysis_type.endswith("_9d") else 3
    if spec.analysis_type.startswith("global_"):
        return SpaceKey("global", "global", dims)
    if spec.analysis_type.startswith("regional_"):
        return SpaceKey("regional", str(spec.network), dims)
    raise ValueError(f"Unsupported event analysis type for time shift: {spec.analysis_type}")


def rolled_segment_metric(
    run: Any,
    spec: MetricSpec,
    *,
    rolled_coords: np.ndarray,
    time: np.ndarray,
    metric_diag: np.ndarray | None,
    model: Any,
    n_states: int | None,
) -> float:
    blocks = run.stage_blocks.get(spec.segment_label, []) if spec.segment_kind == "baseline" else run.event_blocks.get(spec.segment_label, [])
    values: list[float] = []
    n_points = rolled_coords.shape[0]
    for block in blocks:
        keep = trimmed_indices(block, n_points)
        if keep.size < 1:
            continue
        if spec.segment_kind == "baseline":
            segment_coords = rolled_coords[int(keep[0]) : int(keep[-1]) + 1]
            segment_time = time[int(keep[0]) : int(keep[-1]) + 1]
            metrics = summarize_segment_metrics(
                segment_coords,
                segment_time,
                metric_diag=metric_diag,
                model=model,
                n_states=n_states,
            )
        else:
            start, end, local_block = build_local_window(
                keep,
                n_points=n_points,
                pre_windows=PRE_EVENT_WINDOWS,
                post_windows=POST_EVENT_WINDOWS,
            )
            segment_coords = rolled_coords[start : end + 1]
            segment_time = time[start : end + 1]
            metrics = summarize_segment_metrics(
                segment_coords,
                segment_time,
                metric_diag=metric_diag,
                model=model,
                n_states=n_states,
                event_block=local_block,
            )
        raw_value = pd.to_numeric(pd.Series([metrics.get(spec.metric)]), errors="coerce").iloc[0]
        if np.isfinite(raw_value):
            values.append(float(raw_value))
    return float(np.median(values)) if values else float("nan")


def run_time_shift_null(
    dataset_root: Path,
    *,
    results_dir: Path,
    shift_permutations: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    runs = load_runs(dataset_root, coordinate_contract=COHORT_COORDINATE_CONTRACT)
    sampled_by_key = gather_reference_segments(runs)
    references = {key: build_reference_model(blocks, dim=key.dim) for key, blocks in sampled_by_key.items()}

    observed_frame = pd.read_csv(results_dir / "primary_event_contrasts.csv", low_memory=False)
    observed_lookup = {
        (row["contrast_name"], row["analysis_type"], row["segment_label"], row["network"], row["metric"]): row
        for _, row in observed_frame.iterrows()
    }

    rng = np.random.default_rng(20260603)
    draw_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    for perm_idx in range(shift_permutations):
        rows: list[dict[str, Any]] = []
        for run in runs:
            for spec in TIME_SHIFT_SPECS:
                key = space_key_from_spec(spec)
                payload = run.spaces.get(key)
                if payload is None:
                    continue
                coords = np.asarray(payload["coords"], dtype=float)
                n_points = min(coords.shape[0], run.time.shape[0])
                if n_points < 8:
                    continue
                coords = coords[:n_points]
                time = run.time[:n_points]
                shift = int(rng.integers(1, n_points))
                rolled_coords = np.roll(coords, shift=shift, axis=0)
                reference = references.get(key) or {}
                value = rolled_segment_metric(
                    run,
                    spec,
                    rolled_coords=rolled_coords,
                    time=time,
                    metric_diag=reference.get("metric_diag"),
                    model=reference.get("model"),
                    n_states=reference.get("n_states"),
                )
                if not np.isfinite(value):
                    continue
                rows.append(
                    {
                        "subject_id": run.metadata.get("subject_id"),
                        "group": run.metadata.get("group"),
                        "condition": run.metadata.get("condition"),
                        "analysis_type": spec.analysis_type,
                        "segment_kind": spec.segment_kind,
                        "segment_label": spec.segment_label,
                        "network": spec.network,
                        "metric": spec.metric,
                        "contrast_name": spec.contrast_name,
                        "value": value,
                    }
                )
        perm_frame = pd.DataFrame(rows)
        for spec in TIME_SHIFT_SPECS:
            sub = perm_frame[
                (perm_frame["analysis_type"] == spec.analysis_type)
                & (perm_frame["segment_label"] == spec.segment_label)
                & (perm_frame["metric"] == spec.metric)
                & (perm_frame["network"] == spec.network)
                & (perm_frame["contrast_name"] == spec.contrast_name)
            ].copy()
            d_value, _, n_value = contrast_effect(sub, spec.contrast_name) if not sub.empty else (float("nan"), float("nan"), 0)
            draw_rows.append(
                {
                    "permutation": perm_idx,
                    "label": spec.label,
                    "contrast_name": spec.contrast_name,
                    "analysis_type": spec.analysis_type,
                    "segment_label": spec.segment_label,
                    "network": spec.network,
                    "metric": spec.metric,
                    "null_effect_size": d_value,
                    "n": n_value,
                }
            )

    draw_frame = pd.DataFrame(draw_rows)
    for spec in TIME_SHIFT_SPECS:
        draw_block = draw_frame[draw_frame["label"] == spec.label].copy()
        observed_key = (spec.contrast_name, spec.analysis_type, spec.segment_label, spec.network, spec.metric)
        observed_row = observed_lookup.get(observed_key)
        observed_d = float(observed_row["effect_size"]) if observed_row is not None else float("nan")
        null_values = pd.to_numeric(draw_block["null_effect_size"], errors="coerce").dropna().to_numpy(dtype=float)
        if null_values.size == 0:
            continue
        empirical_p = float((1.0 + np.sum(np.abs(null_values) >= abs(observed_d))) / (null_values.size + 1.0))
        summary_rows.append(
            {
                "label": spec.label,
                "contrast_name": spec.contrast_name,
                "analysis_type": spec.analysis_type,
                "segment_label": spec.segment_label,
                "network": spec.network,
                "metric": spec.metric,
                "observed_effect_size": observed_d,
                "null_mean_abs_d": float(np.mean(np.abs(null_values))),
                "null_p95_abs_d": float(np.quantile(np.abs(null_values), 0.95)),
                "empirical_p": empirical_p,
                "n_permutations": int(null_values.size),
            }
        )
    return pd.DataFrame(summary_rows), draw_frame


def build_summary_markdown(
    classical_summary: pd.DataFrame,
    focal_classical_summary: pd.DataFrame,
    loo_summary: pd.DataFrame,
    time_shift_summary: pd.DataFrame,
) -> str:
    lines = [
        "# Additional Parkinson QC / robustness summary",
        "",
        "This supplement-facing QC pass adds three checks to the mixed-contract Parkinson rerun:",
        "",
        "1. direct comparison against the best article-facing conventional EEG comparator rows,",
        "2. leave-one-subject-out stability for focal geometry and classical rows,",
        "3. and a circular time-shift null for the retained event-/stage-locked trajectory rows.",
        "",
        "## Geometry versus conventional EEG comparators",
        "",
    ]
    for _, row in classical_summary.iterrows():
        lines.append(
            f"- `{row['contrast_name']}`: best geometry row `{row['best_geometry_metric']}` (`d = {fmt(row['best_geometry_effect_size'])}`, `q = {fmt(row['best_geometry_q'])}`) "
            f"vs best classical row `{row['best_classical_metric']}` (`d = {fmt(row['best_classical_effect_size'])}`, `q = {fmt(row['best_classical_q'])}`); "
            f"`|d|` gap = `{fmt(row['abs_d_gap_geometry_minus_classical'])}`."
        )
    lines.extend(["", "## Focal NMD rows versus classical sidecars", ""])
    for _, row in focal_classical_summary.iterrows():
        if bool(row.get("paired_delta", False)):
            detail = f"delta rho = {fmt(row['spearman_rho'])}, p = {fmt(row['spearman_p'])}"
        else:
            detail = (
                f"pooled rho = {fmt(row['spearman_rho'])}, p = {fmt(row['spearman_p'])}; "
                f"group-adjusted rho = {fmt(row['group_adjusted_rho'])}, p = {fmt(row['group_adjusted_p'])}"
            )
        lines.append(
            f"- `{row['label']}`: strongest classical correlate `{row['classical_metric']}` "
            f"({detail}; n = `{int(row['n'])}`), interpreted as `{row['interpretation']}`."
        )
    lines.extend(["", "## Leave-one-subject-out stability", ""])
    for _, row in loo_summary.iterrows():
        lines.append(
            f"- `{row['label']}`: full `d = {fmt(row['full_d'])}`, full `p = {fmt(row['full_p'])}`, "
            f"leave-one-out `d` range `{fmt(row['leave_one_out_d_min'])}` to `{fmt(row['leave_one_out_d_max'])}`, "
            f"median `{fmt(row['leave_one_out_d_median'])}`, sign consistency `{fmt(row['sign_consistency'])}`."
        )
    lines.extend(["", "## Time-shift null for event/stage-locked rows", ""])
    for _, row in time_shift_summary.iterrows():
        lines.append(
            f"- `{row['label']}`: observed `d = {fmt(row['observed_effect_size'])}`, null mean `|d| = {fmt(row['null_mean_abs_d'])}`, "
            f"null p95 `|d| = {fmt(row['null_p95_abs_d'])}`, empirical `p = {fmt(row['empirical_p'])}`."
        )
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- Leave-one-site-out was not run because the article-facing ds003490 bundle does not expose a reliable site / hospital variable for this cohort.",
            "- The time-shift null rolls the exported trajectory relative to the original block labels, preserving within-run autocorrelation and block counts while destroying true label alignment.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)

    standard_primary, event_primary, classical_primary = load_primary_contrasts(args.results_dir)
    standard_frames = {
        COHORT_COORDINATE_CONTRACT: load_standard_metrics(args.results_dir, COHORT_COORDINATE_CONTRACT),
        SUBJECT_COORDINATE_CONTRACT: load_standard_metrics(args.results_dir, SUBJECT_COORDINATE_CONTRACT),
    }
    event_frames = {
        COHORT_COORDINATE_CONTRACT: load_event_metrics(args.results_dir, COHORT_COORDINATE_CONTRACT),
        SUBJECT_COORDINATE_CONTRACT: load_event_metrics(args.results_dir, SUBJECT_COORDINATE_CONTRACT),
    }
    classical_frames = {
        COHORT_COORDINATE_CONTRACT: load_classical_metrics(args.results_dir, COHORT_COORDINATE_CONTRACT),
        SUBJECT_COORDINATE_CONTRACT: load_classical_metrics(args.results_dir, SUBJECT_COORDINATE_CONTRACT),
    }

    classical_summary = summarize_classical_vs_geometry(standard_primary, event_primary, classical_primary)
    focal_classical_summary, focal_classical_all = summarize_focal_vs_classical(standard_frames, event_frames, classical_frames)
    loo_rows: list[dict[str, Any]] = []
    for spec in (*FOCAL_SPECS, *CLASSICAL_BEST_SPECS):
        frame = metric_subject_frame(spec, standard_frames, event_frames, classical_frames)
        if frame.empty:
            continue
        loo_rows.append(summarize_leave_one_out(frame, spec))
    loo_summary = pd.DataFrame(loo_rows)

    time_shift_summary, time_shift_draws = run_time_shift_null(
        args.dataset_root,
        results_dir=args.results_dir,
        shift_permutations=args.shift_permutations,
    )

    classical_summary.to_csv(args.output_dir / "qc_classical_comparator_summary.csv", index=False)
    focal_classical_summary.to_csv(args.output_dir / FOCAL_CLASSICAL_SUMMARY_CSV, index=False)
    focal_classical_all.to_csv(args.output_dir / FOCAL_CLASSICAL_ALL_CSV, index=False)
    loo_summary.to_csv(args.output_dir / "qc_leave_one_subject_out_metrics.csv", index=False)
    time_shift_summary.to_csv(args.output_dir / "qc_time_shift_summary.csv", index=False)
    time_shift_draws.to_csv(args.output_dir / "qc_time_shift_null_draws.csv", index=False)

    summary_md = build_summary_markdown(classical_summary, focal_classical_summary, loo_summary, time_shift_summary)
    (args.output_dir / EVENT_SUMMARY_FILENAME).write_text(summary_md, encoding="utf-8")

    manifest = {
        "results_dir": str(args.results_dir),
        "dataset_root": str(args.dataset_root),
        "output_dir": str(args.output_dir),
        "shift_permutations": int(args.shift_permutations),
        "classical_summary_csv": str(args.output_dir / "qc_classical_comparator_summary.csv"),
        "focal_classical_summary_csv": str(args.output_dir / FOCAL_CLASSICAL_SUMMARY_CSV),
        "focal_classical_all_csv": str(args.output_dir / FOCAL_CLASSICAL_ALL_CSV),
        "leave_one_out_csv": str(args.output_dir / "qc_leave_one_subject_out_metrics.csv"),
        "time_shift_summary_csv": str(args.output_dir / "qc_time_shift_summary.csv"),
        "time_shift_draws_csv": str(args.output_dir / "qc_time_shift_null_draws.csv"),
        "summary_md": str(args.output_dir / EVENT_SUMMARY_FILENAME),
        "note": "Leave-one-site-out was not run because no reliable site column is present in the article-facing ds003490 bundle.",
    }
    (args.output_dir / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
