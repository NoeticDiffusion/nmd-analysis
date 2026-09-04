from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr, wilcoxon

from compute_parkinson_cognitive_workload_metrics import (
    build_local_window,
    gather_reference_segments,
    load_runs,
    trimmed_indices,
)
from parkinson_cognitive_workload_focal_specs import (
    MetricSpec,
    event_qc_specs_for_dataset,
    standard_qc_specs_for_dataset,
)
from parkinson_cognitive_workload_support import (
    COHORT_COORDINATE_CONTRACT,
    MANIFEST_JSON,
    PRE_EVENT_WINDOWS,
    POST_EVENT_WINDOWS,
    SUBJECT_COORDINATE_CONTRACT,
    SpaceKey,
    build_reference_model,
    cohens_d,
    cohens_dz,
    ensure_dir,
    get_dataset_spec,
    results_dir_for_spec,
    summarize_segment_metrics,
    write_json,
)


SUMMARY_MD = "additional_qc_summary.md"
SUMMARY_MANIFEST = "additional_qc_manifest.json"
GEOMETRY_VS_CLASSICAL_CSV = "qc_geometry_vs_classical_summary.csv"
FOCAL_CLASSICAL_SUMMARY_CSV = "qc_focal_nmd_vs_classical_summary.csv"
FOCAL_CLASSICAL_ALL_CSV = "qc_focal_nmd_vs_classical_all.csv"
LEAVE_ONE_OUT_CSV = "qc_leave_one_subject_out_metrics.csv"
TIME_SHIFT_SUMMARY_CSV = "qc_time_shift_summary.csv"
TIME_SHIFT_DRAWS_CSV = "qc_time_shift_null_draws.csv"
STANDARD_PERMUTATION_CSV = "qc_standard_permutation_summary.csv"
DEFAULT_SHIFT_PERMUTATIONS = 4
DEFAULT_STANDARD_PERMUTATIONS = 128


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run additional QC / robustness checks for Parkinson cognitive workload metrics."
    )
    parser.add_argument("--dataset-id", type=str, required=True)
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--dataset-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--shift-permutations", type=int, default=DEFAULT_SHIFT_PERMUTATIONS)
    parser.add_argument("--standard-permutations", type=int, default=DEFAULT_STANDARD_PERMUTATIONS)
    return parser.parse_args()


def latest_parquet(root: Path, dataset_id: str, analysis_type: str) -> Path:
    matches = sorted(root.glob(f"{dataset_id}_{analysis_type}_*.parquet"), key=lambda path: path.stat().st_mtime_ns)
    if not matches:
        raise FileNotFoundError(f"No {analysis_type} parquet found under {root}")
    return matches[-1]


def fmt(value: object) -> str:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return "nan"
    if not pd.notna(parsed):
        return "nan"
    return f"{parsed:.4g}"


def load_standard_metrics(results_dir: Path, dataset_id: str, contract: str) -> pd.DataFrame:
    analysis_dirname = "standard_analysis_cohort" if contract == COHORT_COORDINATE_CONTRACT else "standard_analysis_subject"
    frame = pd.read_parquet(latest_parquet(results_dir / analysis_dirname, dataset_id, "subject_metrics"))
    frame["requested_coordinate_contract"] = frame.get("requested_coordinate_contract", contract)
    frame["resolved_coordinate_contract"] = frame.get("resolved_coordinate_contract", contract)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame


def load_primary_contrasts(results_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    standard = pd.read_csv(results_dir / "primary_standard_contrasts.csv", low_memory=False)
    event = pd.read_csv(results_dir / "primary_event_contrasts.csv", low_memory=False)
    for frame in (standard, event):
        for col in ("q_value", "p_value", "effect_size"):
            if col in frame.columns:
                frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return standard, event


def filter_long_metric(frame: pd.DataFrame, spec: MetricSpec) -> pd.DataFrame:
    work = frame.copy()
    if "analysis_type" in work.columns:
        work = work[work["analysis_type"] == spec.analysis_type]
    if "metric" in work.columns:
        work = work[work["metric"] == spec.metric]
    if spec.network is not None and "network" in work.columns:
        work = work[work["network"].fillna("").astype(str) == spec.network]
    if "requested_coordinate_contract" in work.columns:
        work = work[work["requested_coordinate_contract"].fillna("").astype(str) == spec.contract]
    work["value"] = pd.to_numeric(work["value"], errors="coerce")
    work = work[np.isfinite(work["value"])].copy()
    return work


def metric_subject_frame(spec: MetricSpec, standard_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if spec.source not in {"standard", "classical"}:
        raise ValueError(f"Unsupported standard QC source {spec.source!r}")
    return filter_long_metric(standard_frames[spec.contract], spec)


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
    raise ValueError(f"Unknown contrast {contrast_name!r}")


def contrast_effect(frame: pd.DataFrame, contrast_name: str) -> tuple[float, float, int]:
    left, right = contrast_value_frames(frame, contrast_name)
    if contrast_name == "Parkinson_OFF_vs_ON":
        merged = left[["subject_id", "value"]].merge(
            right[["subject_id", "value"]],
            on="subject_id",
            suffixes=("_off", "_on"),
            how="inner",
        )
        if merged.shape[0] < 3:
            return float("nan"), float("nan"), int(merged.shape[0])
        diff = pd.to_numeric(merged["value_on"], errors="coerce").to_numpy(dtype=float) - pd.to_numeric(
            merged["value_off"], errors="coerce"
        ).to_numpy(dtype=float)
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
        "analysis_type": spec.analysis_type,
        "network": spec.network,
        "metric": spec.metric,
        "exploratory": bool(spec.exploratory),
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
    raise ValueError(f"Unknown contrast {contrast_name!r}")


def paired_delta_frame(frame: pd.DataFrame) -> pd.DataFrame:
    off = frame[frame["condition"] == "OFF"][["subject_id", "value"]].rename(columns={"value": "value_off"})
    on = frame[frame["condition"] == "ON"][["subject_id", "value"]].rename(columns={"value": "value_on"})
    merged = off.merge(on, on="subject_id", how="inner")
    merged["delta"] = pd.to_numeric(merged["value_on"], errors="coerce") - pd.to_numeric(
        merged["value_off"], errors="coerce"
    )
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


def summarize_geometry_vs_classical(standard_primary: pd.DataFrame, event_primary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    geometry_primary = pd.concat(
        [
            standard_primary[standard_primary["analysis_type"] != "eeg_classical_comparators"].copy(),
            event_primary.copy(),
        ],
        ignore_index=True,
    )
    classical_primary = standard_primary[standard_primary["analysis_type"] == "eeg_classical_comparators"].copy()
    for contrast_name in ["Control_vs_Parkinson_OFF", "Control_vs_Parkinson_ON", "Parkinson_OFF_vs_ON"]:
        geometry_block = geometry_primary[geometry_primary["contrast_name"] == contrast_name].copy()
        classical_block = classical_primary[classical_primary["contrast_name"] == contrast_name].copy()
        if geometry_block.empty or classical_block.empty:
            continue
        geometry_block["abs_d"] = pd.to_numeric(geometry_block["effect_size"], errors="coerce").abs()
        classical_block["abs_d"] = pd.to_numeric(classical_block["effect_size"], errors="coerce").abs()
        geometry_row = geometry_block.sort_values(
            ["q_value", "p_value", "abs_d"],
            ascending=[True, True, False],
            na_position="last",
        ).iloc[0]
        classical_row = classical_block.sort_values(
            ["q_value", "p_value", "abs_d"],
            ascending=[True, True, False],
            na_position="last",
        ).iloc[0]
        rows.append(
            {
                "contrast_name": contrast_name,
                "best_geometry_layer": str(geometry_row["analysis_type"]),
                "best_geometry_metric": str(geometry_row["metric"]),
                "best_geometry_network": str(geometry_row.get("network", "")),
                "best_geometry_effect_size": float(geometry_row["effect_size"]),
                "best_geometry_q": float(geometry_row["q_value"]),
                "best_classical_metric": str(classical_row["metric"]),
                "best_classical_effect_size": float(classical_row["effect_size"]),
                "best_classical_q": float(classical_row["q_value"]),
                "abs_d_gap_geometry_minus_classical": float(
                    abs(float(geometry_row["effect_size"])) - abs(float(classical_row["effect_size"]))
                ),
            }
        )
    return pd.DataFrame(rows)


def summarize_focal_vs_classical(
    geometry_specs: tuple[MetricSpec, ...],
    standard_frames: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    for spec in geometry_specs:
        focal = metric_subject_frame(spec, standard_frames)
        if focal.empty:
            continue
        focal = subset_frame_for_contrast(focal, spec.contrast_name)
        classical_candidates = standard_frames[spec.contract]
        classical_candidates = classical_candidates[classical_candidates["analysis_type"] == "eeg_classical_comparators"].copy()
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
            if best_row is None or association_priority_score(row) > association_priority_score(best_row):
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


def summarize_standard_permutation(
    specs: tuple[MetricSpec, ...],
    standard_frames: dict[str, pd.DataFrame],
    *,
    n_permutations: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(20260605)
    rows: list[dict[str, Any]] = []
    for idx, spec in enumerate(specs, start=1):
        if idx == 1 or idx % 4 == 0 or idx == len(specs):
            print(f"[standard-null] metric {idx}/{len(specs)}: {spec.label}", flush=True)
        frame = metric_subject_frame(spec, standard_frames)
        if frame.empty:
            continue
        observed_d, _, observed_n = contrast_effect(frame, spec.contrast_name)
        null_values: list[float] = []
        left, right = contrast_value_frames(frame, spec.contrast_name)
        if spec.contrast_name == "Parkinson_OFF_vs_ON":
            merged = left[["subject_id", "value"]].merge(
                right[["subject_id", "value"]],
                on="subject_id",
                suffixes=("_off", "_on"),
                how="inner",
            )
            if merged.shape[0] < 3:
                continue
            diff = pd.to_numeric(merged["value_on"], errors="coerce").to_numpy(dtype=float) - pd.to_numeric(
                merged["value_off"], errors="coerce"
            ).to_numpy(dtype=float)
            diff = diff[np.isfinite(diff)]
            if diff.size < 3:
                continue
            for _ in range(n_permutations):
                signs = rng.choice(np.array([-1.0, 1.0]), size=diff.size, replace=True)
                null_values.append(float(cohens_dz(diff * signs)))
        else:
            left_values = pd.to_numeric(left["value"], errors="coerce").dropna().to_numpy(dtype=float)
            right_values = pd.to_numeric(right["value"], errors="coerce").dropna().to_numpy(dtype=float)
            if left_values.size < 3 or right_values.size < 3:
                continue
            all_values = np.concatenate([left_values, right_values])
            left_n = left_values.size
            for _ in range(n_permutations):
                perm = rng.permutation(all_values.size)
                perm_left = all_values[perm[:left_n]]
                perm_right = all_values[perm[left_n:]]
                null_values.append(float(cohens_d(perm_left, perm_right)))
        if not null_values:
            continue
        null_arr = np.asarray(null_values, dtype=float)
        empirical_p = float((1.0 + np.sum(np.abs(null_arr) >= abs(observed_d))) / (null_arr.size + 1.0))
        rows.append(
            {
                "label": spec.label,
                "contrast_name": spec.contrast_name,
                "source": spec.source,
                "analysis_type": spec.analysis_type,
                "network": spec.network,
                "metric": spec.metric,
                "exploratory": bool(spec.exploratory),
                "observed_effect_size": observed_d,
                "full_n": observed_n,
                "null_mean_abs_d": float(np.mean(np.abs(null_arr))),
                "null_p95_abs_d": float(np.quantile(np.abs(null_arr), 0.95)),
                "empirical_p": empirical_p,
                "n_permutations": int(null_arr.size),
            }
        )
    return pd.DataFrame(rows).sort_values(["contrast_name", "source", "analysis_type", "metric"], na_position="last").reset_index(drop=True)


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
    blocks = run.segment_blocks.get(spec.segment_label or "", [])
    values: list[float] = []
    n_points = rolled_coords.shape[0]
    for block in blocks:
        keep = trimmed_indices(block, n_points)
        if keep.size < 1:
            continue
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
    dataset_id: str,
    dataset_root: Path,
    *,
    results_dir: Path,
    shift_permutations: int,
    event_specs: tuple[MetricSpec, ...],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not event_specs:
        return pd.DataFrame(), pd.DataFrame()
    spec_obj = get_dataset_spec(dataset_id)
    observed_frame = pd.read_csv(results_dir / "primary_event_contrasts.csv", low_memory=False)
    for col in ("effect_size", "q_value", "p_value"):
        if col in observed_frame.columns:
            observed_frame[col] = pd.to_numeric(observed_frame[col], errors="coerce")
    observed_lookup = {
        (
            row["contrast_name"],
            row["analysis_type"],
            row["segment_kind"],
            row["segment_label"],
            row["network"],
            row["metric"],
        ): row
        for _, row in observed_frame.iterrows()
    }
    rng = np.random.default_rng(20260605)
    draw_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    specs_by_contract: dict[str, tuple[MetricSpec, ...]] = {
        contract: tuple(spec for spec in event_specs if spec.contract == contract)
        for contract in {spec.contract for spec in event_specs}
    }
    runs_by_contract: dict[str, list[Any]] = {}
    references_by_contract: dict[str, dict[SpaceKey, dict[str, Any]]] = {}
    for contract, specs in specs_by_contract.items():
        if not specs:
            continue
        runs = load_runs(dataset_root, spec_obj, coordinate_contract=contract)
        runs_by_contract[contract] = runs
        sampled_by_key = gather_reference_segments(runs)
        references_by_contract[contract] = {
            key: build_reference_model(blocks, dim=key.dim)
            for key, blocks in sampled_by_key.items()
        }

    print(f"[time-shift] loaded {len(event_specs)} focal event specs", flush=True)
    for perm_idx in range(shift_permutations):
        if perm_idx == 0 or (perm_idx + 1) % 3 == 0 or perm_idx + 1 == shift_permutations:
            print(f"[time-shift] permutation {perm_idx + 1}/{shift_permutations}", flush=True)
        perm_rows: list[dict[str, Any]] = []
        for contract, specs in specs_by_contract.items():
            runs = runs_by_contract.get(contract, [])
            references = references_by_contract.get(contract, {})
            for run in runs:
                for spec in specs:
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
                    perm_rows.append(
                        {
                            "subject_id": run.metadata.get("subject_id"),
                            "group": run.metadata.get("group"),
                            "condition": run.metadata.get("condition"),
                            "contrast_name": spec.contrast_name,
                            "analysis_type": spec.analysis_type,
                            "segment_kind": spec.segment_kind,
                            "segment_label": spec.segment_label,
                            "network": spec.network,
                            "metric": spec.metric,
                            "value": value,
                        }
                    )
        perm_frame = pd.DataFrame(perm_rows)
        if perm_frame.empty:
            continue
        for spec in event_specs:
            sub = perm_frame[
                (perm_frame["contrast_name"] == spec.contrast_name)
                & (perm_frame["analysis_type"] == spec.analysis_type)
                & (perm_frame["segment_kind"] == spec.segment_kind)
                & (perm_frame["segment_label"] == spec.segment_label)
                & (perm_frame["metric"] == spec.metric)
                & (perm_frame["network"].fillna("").astype(str) == str(spec.network))
            ].copy()
            d_value, _, n_value = contrast_effect(sub, spec.contrast_name) if not sub.empty else (float("nan"), float("nan"), 0)
            draw_rows.append(
                {
                    "permutation": perm_idx,
                    "label": spec.label,
                    "contrast_name": spec.contrast_name,
                    "analysis_type": spec.analysis_type,
                    "segment_kind": spec.segment_kind,
                    "segment_label": spec.segment_label,
                    "network": spec.network,
                    "metric": spec.metric,
                    "null_effect_size": d_value,
                    "n": n_value,
                }
            )

    draw_frame = pd.DataFrame(draw_rows)
    for spec in event_specs:
        draw_block = draw_frame[draw_frame["label"] == spec.label].copy()
        observed_key = (
            spec.contrast_name,
            spec.analysis_type,
            spec.segment_kind,
            spec.segment_label,
            spec.network,
            spec.metric,
        )
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
                "segment_kind": spec.segment_kind,
                "segment_label": spec.segment_label,
                "network": spec.network,
                "metric": spec.metric,
                "exploratory": bool(spec.exploratory),
                "observed_effect_size": observed_d,
                "null_mean_abs_d": float(np.mean(np.abs(null_values))),
                "null_p95_abs_d": float(np.quantile(np.abs(null_values), 0.95)),
                "empirical_p": empirical_p,
                "n_permutations": int(null_values.size),
            }
        )
    return pd.DataFrame(summary_rows), draw_frame


def build_summary_markdown(
    dataset_id: str,
    geometry_vs_classical: pd.DataFrame,
    focal_classical_summary: pd.DataFrame,
    loo_summary: pd.DataFrame,
    standard_permutation_summary: pd.DataFrame,
    time_shift_summary: pd.DataFrame,
) -> str:
    lines = [
        f"# Additional Parkinson cognitive workload QC summary (`{dataset_id}`)",
        "",
        "This QC pass adds four checks to the cognitive workload article-facing results:",
        "",
        "1. geometry versus classical EEG comparison,",
        "2. focal geometry-versus-classical association checks,",
        "3. leave-one-subject-out and standard-metric permutation robustness,",
        "4. and a circular time-shift null for focal event rows.",
        "",
        "## Geometry versus classical EEG",
        "",
    ]
    for _, row in geometry_vs_classical.iterrows():
        lines.append(
            f"- `{row['contrast_name']}`: best geometry row `{row['best_geometry_layer']} / {row['best_geometry_metric']}` "
            f"(`d = {fmt(row['best_geometry_effect_size'])}`, `q = {fmt(row['best_geometry_q'])}`) "
            f"vs best classical row `{row['best_classical_metric']}` "
            f"(`d = {fmt(row['best_classical_effect_size'])}`, `q = {fmt(row['best_classical_q'])}`); "
            f"`|d|` gap = `{fmt(row['abs_d_gap_geometry_minus_classical'])}`."
        )
    lines.extend(["", "## Focal geometry versus classical alignment", ""])
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
    lines.extend(["", "## Standard permutation null", ""])
    for _, row in standard_permutation_summary.iterrows():
        lines.append(
            f"- `{row['label']}`: observed `d = {fmt(row['observed_effect_size'])}`, "
            f"null mean `|d| = {fmt(row['null_mean_abs_d'])}`, null p95 `|d| = {fmt(row['null_p95_abs_d'])}`, "
            f"empirical `p = {fmt(row['empirical_p'])}`."
        )
    lines.extend(["", "## Circular time-shift null", ""])
    for _, row in time_shift_summary.iterrows():
        lines.append(
            f"- `{row['label']}`: observed `d = {fmt(row['observed_effect_size'])}`, "
            f"null mean `|d| = {fmt(row['null_mean_abs_d'])}`, null p95 `|d| = {fmt(row['null_p95_abs_d'])}`, "
            f"empirical `p = {fmt(row['empirical_p'])}`."
        )
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- Cross-fit / split validation was intentionally not used because the current cohort is too small for that to be a strong primary robustness claim.",
            "- The time-shift null preserves within-run autocorrelation and segment counts while destroying the original event-to-trajectory alignment.",
            "- Exploratory rows remain explicitly exploratory even when they are visually or robustly interesting.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    spec = get_dataset_spec(args.dataset_id)
    results_dir = args.results_dir or results_dir_for_spec(spec)
    dataset_root = args.dataset_root or spec.dataset_root
    output_dir = args.output_dir or (results_dir / "additional_qc_20260605")
    ensure_dir(output_dir)

    print(f"[qc] dataset={spec.dataset_id}", flush=True)
    print("[qc] loading primary contrast tables", flush=True)
    standard_primary, event_primary = load_primary_contrasts(results_dir)
    print("[qc] loading subject-metric parquets", flush=True)
    standard_frames = {
        COHORT_COORDINATE_CONTRACT: load_standard_metrics(results_dir, spec.dataset_id, COHORT_COORDINATE_CONTRACT),
        SUBJECT_COORDINATE_CONTRACT: load_standard_metrics(results_dir, spec.dataset_id, SUBJECT_COORDINATE_CONTRACT),
    }
    standard_specs = standard_qc_specs_for_dataset(spec.dataset_id)
    geometry_specs = tuple(metric for metric in standard_specs if metric.source == "standard")
    event_specs = event_qc_specs_for_dataset(spec.dataset_id)

    print("[qc] summarizing geometry vs classical", flush=True)
    geometry_vs_classical = summarize_geometry_vs_classical(standard_primary, event_primary)
    print("[qc] computing focal geometry-vs-classical alignment", flush=True)
    focal_classical_summary, focal_classical_all = summarize_focal_vs_classical(geometry_specs, standard_frames)

    print("[qc] leave-one-subject-out", flush=True)
    loo_rows: list[dict[str, Any]] = []
    for metric_spec in standard_specs:
        frame = metric_subject_frame(metric_spec, standard_frames)
        if frame.empty:
            continue
        loo_rows.append(summarize_leave_one_out(frame, metric_spec))
    loo_summary = pd.DataFrame(loo_rows)

    print("[qc] standard permutation null", flush=True)
    standard_permutation_summary = summarize_standard_permutation(
        standard_specs,
        standard_frames,
        n_permutations=int(args.standard_permutations),
    )
    print("[qc] circular time-shift null", flush=True)
    time_shift_summary, time_shift_draws = run_time_shift_null(
        spec.dataset_id,
        dataset_root,
        results_dir=results_dir,
        shift_permutations=int(args.shift_permutations),
        event_specs=event_specs,
    )

    print("[qc] writing outputs", flush=True)
    geometry_vs_classical.to_csv(output_dir / GEOMETRY_VS_CLASSICAL_CSV, index=False)
    focal_classical_summary.to_csv(output_dir / FOCAL_CLASSICAL_SUMMARY_CSV, index=False)
    focal_classical_all.to_csv(output_dir / FOCAL_CLASSICAL_ALL_CSV, index=False)
    loo_summary.to_csv(output_dir / LEAVE_ONE_OUT_CSV, index=False)
    standard_permutation_summary.to_csv(output_dir / STANDARD_PERMUTATION_CSV, index=False)
    time_shift_summary.to_csv(output_dir / TIME_SHIFT_SUMMARY_CSV, index=False)
    time_shift_draws.to_csv(output_dir / TIME_SHIFT_DRAWS_CSV, index=False)

    summary_md = build_summary_markdown(
        spec.dataset_id,
        geometry_vs_classical,
        focal_classical_summary,
        loo_summary,
        standard_permutation_summary,
        time_shift_summary,
    )
    (output_dir / SUMMARY_MD).write_text(summary_md, encoding="utf-8")
    write_json(
        output_dir / SUMMARY_MANIFEST,
        {
            "dataset_id": spec.dataset_id,
            "results_dir": str(results_dir),
            "dataset_root": str(dataset_root),
            "output_dir": str(output_dir),
            "shift_permutations": int(args.shift_permutations),
            "standard_permutations": int(args.standard_permutations),
            "geometry_vs_classical_csv": str(output_dir / GEOMETRY_VS_CLASSICAL_CSV),
            "focal_classical_summary_csv": str(output_dir / FOCAL_CLASSICAL_SUMMARY_CSV),
            "focal_classical_all_csv": str(output_dir / FOCAL_CLASSICAL_ALL_CSV),
            "leave_one_out_csv": str(output_dir / LEAVE_ONE_OUT_CSV),
            "standard_permutation_csv": str(output_dir / STANDARD_PERMUTATION_CSV),
            "time_shift_summary_csv": str(output_dir / TIME_SHIFT_SUMMARY_CSV),
            "time_shift_draws_csv": str(output_dir / TIME_SHIFT_DRAWS_CSV),
            "summary_md": str(output_dir / SUMMARY_MD),
        },
    )
    print("[qc] done", flush=True)


if __name__ == "__main__":
    main()
