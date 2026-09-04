from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

import h5py
import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[4]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.h5_contract import resolve_jacobian_3d, resolve_jacobian_9d  # noqa: E402
from ndt_analysis.legacy_adapters import (  # noqa: E402
    _base_h5_metadata_from_handle,
    _estimate_temporal_jacobian_delta,
    _summarize_global_mnps_jacobian_row,
)
from ndt_analysis.reachability_cones import ReachabilityConfig, summarize_reachability_h5  # noqa: E402

from photic_stage_recovery import (  # noqa: E402
    DEFAULT_BLOCK_LENGTH_WINDOWS,
    DEFAULT_DUPLICATE_GAP_WINDOWS,
    PHOTIC_STAGE_LABELS,
    recover_photic_blocks,
    write_stage_qc_outputs,
)

DEFAULT_RAW_ROOT = REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds006036_20260604_132747"
DEFAULT_RESULTS_ROOT = ARTICLE_DIR / "results"
PARTICIPANTS_PATH = ARTICLE_DIR / "metadata" / "participants.tsv"
DATASET = "ds006036"
SELECTION_MODE_EXACT_BLOCK_NATIVE = "exact_block_native"
SELECTION_MODE_STAGE_RECOVERY = "stage_recovery"
DEFAULT_SELECTION_MODE = SELECTION_MODE_EXACT_BLOCK_NATIVE

GROUP_LABELS = {
    "A": "AD",
    "C": "Healthy",
    "F": "FTD",
}
CONTRAST_GROUPS = {
    "AD_vs_Healthy": ("A", "C"),
    "FTD_vs_Healthy": ("F", "C"),
    "AD_vs_FTD": ("A", "F"),
}
CORRELATION_COHORTS = {
    "Dementia_all": ("A", "F"),
    "AD_only": ("A",),
    "FTD_only": ("F",),
}
REACHABILITY_METRICS: tuple[str, ...] = (
    "tube_d_eff_median",
    "tube_capture_gate_median",
    "tube_log_det_median",
    "tube_kappa_median",
    "persistence_kappa_median",
    "persistence_log_eig_var_median",
    "tube_a_operator_norm_median",
)
MNJ_METRICS: tuple[str, ...] = (
    "spectral_radius_median",
    "rotational_power_median",
    "frobenius_norm_median",
    "trace_median",
    "anisotropy_abs_eig_median",
    "mdr_median",
)
PREFERRED_METRICS: dict[str, tuple[str, ...]] = {
    "global_reachability_3d": ("tube_d_eff_median", "tube_capture_gate_median", "tube_log_det_median"),
    "regional_reachability_3d": ("tube_d_eff_median", "tube_capture_gate_median", "tube_log_det_median"),
    "global_mnj_3d": ("spectral_radius_median", "rotational_power_median", "frobenius_norm_median"),
    "global_mnj_9d": ("spectral_radius_median", "rotational_power_median", "frobenius_norm_median"),
    "regional_mnj_3d": ("spectral_radius_median", "rotational_power_median", "frobenius_norm_median"),
}
ANALYSIS_LABELS = {
    "global_reachability_3d": "Global 3D reachability",
    "regional_reachability_3d": "Regional 3D reachability",
    "global_mnj_3d": "Global 3D MNJ",
    "global_mnj_9d": "Global 9D MNJ",
    "regional_mnj_3d": "Regional 3D MNJ",
}
MIN_REACHABILITY_POINTS = 4
MIN_JACOBIAN_WINDOWS = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build ds006036 photic manuscript-facing exports.")
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument(
        "--selection-mode",
        choices=(SELECTION_MODE_EXACT_BLOCK_NATIVE, SELECTION_MODE_STAGE_RECOVERY),
        default=DEFAULT_SELECTION_MODE,
    )
    parser.add_argument("--block-length-windows", type=int, default=DEFAULT_BLOCK_LENGTH_WINDOWS)
    parser.add_argument("--duplicate-gap-windows", type=int, default=DEFAULT_DUPLICATE_GAP_WINDOWS)
    return parser.parse_args()


def _sanitize_columns(columns: Iterable[object]) -> list[str]:
    cleaned: list[str] = []
    for column in columns:
        text = str(column).replace("\ufeff", "").replace("\xa0", " ").strip()
        cleaned.append(" ".join(text.split()))
    return cleaned


def load_participants() -> pd.DataFrame:
    phenos = pd.read_csv(PARTICIPANTS_PATH, sep="\t")
    phenos.columns = _sanitize_columns(phenos.columns)
    rename_map = {
        "participant_id": "subject_id",
        "Gender": "gender",
        "Age": "age",
        "Group": "group",
        "MMSE": "mmse",
    }
    phenos = phenos.rename(columns=rename_map)
    phenos["age"] = pd.to_numeric(phenos["age"], errors="coerce")
    phenos["mmse"] = pd.to_numeric(phenos["mmse"], errors="coerce")
    phenos["female"] = phenos["gender"].astype(str).eq("F")
    phenos["group_label"] = phenos["group"].astype(str).map(GROUP_LABELS).fillna(phenos["group"].astype(str))
    return phenos


def build_demography_summary(phenos: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for group_code, group_label in GROUP_LABELS.items():
        sub = phenos[phenos["group"] == group_code].copy()
        rows.append(
            {
                "dataset": DATASET,
                "group_code": group_code,
                "group_label": group_label,
                "n": int(len(sub)),
                "age_mean": float(sub["age"].mean()),
                "age_sd": float(sub["age"].std()),
                "female_n": int(sub["female"].sum()),
                "female_pct": float(sub["female"].mean() * 100.0),
                "mmse_mean": float(sub["mmse"].mean()),
                "mmse_sd": float(sub["mmse"].std()),
                "mmse_median": float(sub["mmse"].median()),
            }
        )
    return pd.DataFrame(rows)


def _iter_h5_paths(raw_root: Path) -> list[Path]:
    return sorted(raw_root.glob("sub-*/sub-*.h5"))


def _stage_display_label(stage_label: str) -> str:
    return {
        "photo_5hz": "PHOTO 5 Hz",
        "photo_10hz": "PHOTO 10 Hz",
        "photo_15hz": "PHOTO 15 Hz",
        "photo_20hz": "PHOTO 20 Hz",
    }.get(stage_label, stage_label)


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        if np.isfinite(value):
            return float(value)
        return None
    if pd.isna(value):
        return None
    return value


def _row_dict(row: pd.Series) -> dict[str, Any]:
    return {column: _json_ready(value) for column, value in row.to_dict().items()}


def _format_backtick_list(items: Iterable[str]) -> str:
    cleaned = [f"`{str(item)}`" for item in items if str(item)]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return ", ".join(cleaned[:-1]) + f", and {cleaned[-1]}"


def _bh_fdr(values: pd.Series) -> pd.Series:
    arr = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    valid = np.isfinite(arr)
    if not valid.any():
        return pd.Series(out, index=values.index, dtype=float)
    p = arr[valid]
    order = np.argsort(p)
    ranked = p[order]
    n = ranked.size
    adjusted = ranked * n / np.arange(1, n + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    out_valid = np.empty_like(adjusted)
    out_valid[order] = adjusted
    out[valid] = out_valid
    return pd.Series(out, index=values.index, dtype=float)


def _sig_tier(row: pd.Series) -> str:
    q = row.get("q_value")
    p = row.get("p_value")
    if pd.notna(q) and float(q) <= 0.05:
        return "q<=0.05"
    if pd.notna(p) and float(p) < 0.05:
        return "p<0.05"
    if pd.notna(p) and float(p) < 0.1:
        return "p<0.1"
    return "ns"


def _cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    left = left[np.isfinite(left)]
    right = right[np.isfinite(right)]
    if left.size < 2 or right.size < 2:
        return float("nan")
    pooled = ((left.size - 1) * np.var(left, ddof=1) + (right.size - 1) * np.var(right, ddof=1)) / (
        left.size + right.size - 2
    )
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(left) - np.mean(right)) / np.sqrt(pooled))


def _metric_family(analysis_type: str) -> str:
    if "reachability" in analysis_type:
        return "reachability"
    return "mnj"


def _append_metric_rows(
    rows: list[dict[str, Any]],
    flat: dict[str, Any],
    *,
    subject_id: str,
    stage_code: int,
    stage_label: str,
    analysis_type: str,
    network: str,
    metrics: Iterable[str],
    n_points_used: int,
) -> None:
    for metric in metrics:
        value = flat.get(metric)
        if value is None or not np.isfinite(float(value)):
            continue
        rows.append(
            {
                "dataset": DATASET,
                "subject_id": subject_id,
                "group": flat.get("group"),
                "condition_label": flat.get("condition"),
                "task_label": flat.get("task"),
                "analysis_type": analysis_type,
                "analysis_label": ANALYSIS_LABELS.get(analysis_type, analysis_type),
                "metric_family": _metric_family(analysis_type),
                "network": network,
                "stage_code": int(stage_code),
                "stage_label": stage_label,
                "stage_display_label": _stage_display_label(stage_label),
                "metric": metric,
                "value": float(value),
                "n_points_used": int(n_points_used),
                "source_h5_path": flat.get("source_h5_path"),
                "source_dataset_path": flat.get("source_dataset_path"),
                "requested_coordinate_contract": flat.get("requested_coordinate_contract"),
                "resolved_coordinate_contract": flat.get("resolved_coordinate_contract"),
            }
        )


def _selection_mask(centers: np.ndarray | None, selected_lookup: np.ndarray, n_windows: int) -> np.ndarray:
    if centers is None:
        centers_arr = np.arange(n_windows, dtype=int)
    else:
        centers_arr = np.asarray(centers[:n_windows], dtype=int).reshape(-1)
    valid = (centers_arr >= 0) & (centers_arr < selected_lookup.size)
    mask = np.zeros((n_windows,), dtype=bool)
    mask[: centers_arr.shape[0]] = valid & selected_lookup[centers_arr]
    return mask


def _regional_jacobian_row(
    base: dict[str, Any],
    *,
    j_hat: np.ndarray,
    j_dot: np.ndarray | None,
    network: str,
) -> dict[str, Any] | None:
    row = _summarize_global_mnps_jacobian_row(
        dict(base),
        j_hat,
        j_dot,
        source_dataset_path=f"/regional_mnps/{network}/jacobian",
        dims=3,
    )
    if row is None:
        return None
    row["network"] = network
    return row


def load_stage_window_selection(
    raw_root: Path,
    *,
    selection_mode: str = DEFAULT_SELECTION_MODE,
    block_length_windows: int = DEFAULT_BLOCK_LENGTH_WINDOWS,
    duplicate_gap_windows: int = DEFAULT_DUPLICATE_GAP_WINDOWS,
) -> tuple[dict[str, dict[int, set[int]]], pd.DataFrame, dict[str, Any]]:
    if selection_mode == SELECTION_MODE_EXACT_BLOCK_NATIVE:
        return _load_exact_block_selection(raw_root)
    if selection_mode == SELECTION_MODE_STAGE_RECOVERY:
        return _load_stage_recovery_selection(
            raw_root,
            block_length_windows=block_length_windows,
            duplicate_gap_windows=duplicate_gap_windows,
        )
    raise ValueError(f"Unsupported selection mode: {selection_mode}")


def _load_exact_block_selection(
    raw_root: Path,
) -> tuple[dict[str, dict[int, set[int]]], pd.DataFrame, dict[str, Any]]:
    selected: dict[str, dict[int, set[int]]] = {}
    rows: list[dict[str, object]] = []
    stage_totals: dict[int, int] = {int(code): 0 for code in PHOTIC_STAGE_LABELS}
    total_blocks = 0
    for h5_path in _iter_h5_paths(raw_root):
        subject_id = h5_path.stem.split("_")[0]
        with h5py.File(h5_path, "r") as handle:
            if "blocks" not in handle:
                continue
            starts = np.asarray(handle["window_start"][:], dtype=float)
            ends = np.asarray(handle["window_end"][:], dtype=float)
            n = min(len(starts), len(ends))
            centers = (starts[:n] + ends[:n]) / 2.0
            block_group = handle["blocks"]
            block_ids = np.asarray(block_group["block_id"][:], dtype=int)
            stage_codes = np.asarray(block_group["stage_code"][:], dtype=int)
            block_starts = np.asarray(block_group["start_sec"][:], dtype=float)
            block_ends = np.asarray(block_group["end_sec"][:], dtype=float)
            block_freqs = (
                np.asarray(block_group["frequency_hz"][:], dtype=float)
                if "frequency_hz" in block_group
                else np.full(block_ids.shape, np.nan)
            )
            stage_map = selected.setdefault(subject_id, {})
            for block_id, stage_code, block_start, block_end, frequency_hz in zip(
                block_ids,
                stage_codes,
                block_starts,
                block_ends,
                block_freqs,
                strict=False,
            ):
                if int(stage_code) not in PHOTIC_STAGE_LABELS:
                    continue
                sample_idx = np.flatnonzero((centers >= float(block_start) - 1e-6) & (centers <= float(block_end) + 1e-6))
                if sample_idx.size == 0:
                    continue
                stage_map.setdefault(int(stage_code), set()).update(int(i) for i in sample_idx.tolist())
                stage_totals[int(stage_code)] += int(sample_idx.size)
                total_blocks += 1
                rows.append(
                    {
                        "subject_id": subject_id,
                        "block_id": int(block_id),
                        "stage_code": int(stage_code),
                        "stage_label": PHOTIC_STAGE_LABELS[int(stage_code)],
                        "stage_display_label": _stage_display_label(PHOTIC_STAGE_LABELS[int(stage_code)]),
                        "frequency_hz": float(frequency_hz) if np.isfinite(frequency_hz) else np.nan,
                        "block_start_sec": float(block_start),
                        "block_end_sec": float(block_end),
                        "block_duration_sec": float(block_end - block_start),
                        "n_original_windows_selected": int(sample_idx.size),
                        "first_window_index": int(sample_idx.min()),
                        "last_window_index": int(sample_idx.max()),
                        "source_h5_path": str(h5_path),
                    }
                )
    frame = pd.DataFrame(rows)
    summary = {
        "selection_mode": "blocks::center_within_exact_block_interval",
        "contract": "cohort_anchored",
        "raw_root": str(raw_root),
        "n_subjects_with_blocks": int(frame["subject_id"].nunique()) if not frame.empty else 0,
        "n_selected_block_instances": int(total_blocks),
        "n_selected_original_windows": int(frame["n_original_windows_selected"].sum()) if not frame.empty else 0,
        "stage_original_window_counts": {
            PHOTIC_STAGE_LABELS[int(code)]: int(count) for code, count in stage_totals.items()
        },
    }
    return selected, frame, summary


def _load_stage_recovery_selection(
    raw_root: Path,
    *,
    block_length_windows: int = DEFAULT_BLOCK_LENGTH_WINDOWS,
    duplicate_gap_windows: int = DEFAULT_DUPLICATE_GAP_WINDOWS,
) -> tuple[dict[str, dict[int, set[int]]], pd.DataFrame, dict[str, Any]]:
    selected: dict[str, dict[int, set[int]]] = {}
    rows: list[dict[str, object]] = []
    stage_totals: dict[int, int] = {int(code): 0 for code in PHOTIC_STAGE_LABELS}
    total_blocks = 0
    for h5_path in _iter_h5_paths(raw_root):
        subject_id = h5_path.stem.split("_")[0]
        with h5py.File(h5_path, "r") as handle:
            stage = np.asarray(handle["labels/stage"][:], dtype=int).reshape(-1)
            time = np.asarray(handle["time"][:], dtype=float).reshape(-1)
            window_start = np.asarray(handle["window_start"][:], dtype=float).reshape(-1)
            window_end = np.asarray(handle["window_end"][:], dtype=float).reshape(-1)
            n = min(stage.size, time.size, window_start.size, window_end.size)
            stage = stage[:n]
            time = time[:n]
            window_start = window_start[:n]
            window_end = window_end[:n]
            recovered_stage, blocks = recover_photic_blocks(
                stage,
                time,
                window_start,
                window_end,
                subject_id=subject_id,
                source_h5_path=h5_path,
                block_length_windows=block_length_windows,
                duplicate_gap_windows=duplicate_gap_windows,
            )
            stage_map = selected.setdefault(subject_id, {})
            for block in blocks:
                block_indices = range(int(block.onset_idx), int(block.end_idx) + 1)
                stage_map.setdefault(int(block.stage_code), set()).update(int(idx) for idx in block_indices)
                stage_totals[int(block.stage_code)] += int(block.recovered_window_count)
                total_blocks += 1
                rows.append(
                    {
                        "subject_id": subject_id,
                        "block_id": int(total_blocks),
                        "stage_code": int(block.stage_code),
                        "stage_label": block.stage_label,
                        "stage_display_label": _stage_display_label(block.stage_label),
                        "frequency_hz": np.nan,
                        "block_start_sec": float(block.onset_window_start_sec),
                        "block_end_sec": float(block.end_window_end_sec),
                        "block_duration_sec": float(block.end_window_end_sec - block.onset_window_start_sec),
                        "n_original_windows_selected": int(block.recovered_window_count),
                        "first_window_index": int(block.onset_idx),
                        "last_window_index": int(block.end_idx),
                        "source_h5_path": str(h5_path),
                    }
                )
            _ = recovered_stage
    frame = pd.DataFrame(rows)
    summary = {
        "selection_mode": "stage_recovery::bounded_onset_clusters",
        "contract": "cohort_anchored",
        "raw_root": str(raw_root),
        "n_subjects_with_blocks": int(frame["subject_id"].nunique()) if not frame.empty else 0,
        "n_selected_block_instances": int(total_blocks),
        "n_selected_original_windows": int(frame["n_original_windows_selected"].sum()) if not frame.empty else 0,
        "stage_original_window_counts": {
            PHOTIC_STAGE_LABELS[int(code)]: int(count) for code, count in stage_totals.items()
        },
    }
    return selected, frame, summary


def build_subject_stage_metric_rows(
    raw_root: Path,
    selection: dict[str, dict[int, set[int]]],
    *,
    coordinate_contract: str = "cohort_anchored",
    selection_tag: str = "exactblock",
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    reach_cfg = ReachabilityConfig(persistence_mode="stability")

    for h5_path in _iter_h5_paths(raw_root):
        subject_id = h5_path.stem.split("_")[0]
        stage_windows = selection.get(subject_id, {})
        if not stage_windows:
            continue
        with h5py.File(h5_path, "r") as handle:
            time = np.asarray(handle["time"][:], dtype=float).reshape(-1)
            window_start = np.asarray(handle["window_start"][:], dtype=float).reshape(-1)
            window_end = np.asarray(handle["window_end"][:], dtype=float).reshape(-1)
            n = min(time.size, window_start.size, window_end.size)
            time = time[:n]
            window_start = window_start[:n]
            window_end = window_end[:n]

            base = _base_h5_metadata_from_handle(handle, h5_path)
            resolved_j3 = resolve_jacobian_3d(handle, coordinate_contract)
            resolved_j9 = resolve_jacobian_9d(handle, coordinate_contract)
            regional_group = handle["regional_mnps"] if "regional_mnps" in handle else None

            for stage_code, stage_label in PHOTIC_STAGE_LABELS.items():
                winset = stage_windows.get(int(stage_code), set())
                if not winset:
                    continue
                stage_idx = np.array(sorted(idx for idx in winset if 0 <= int(idx) < n), dtype=int)
                if stage_idx.size < MIN_REACHABILITY_POINTS and stage_idx.size < MIN_JACOBIAN_WINDOWS:
                    continue

                if stage_idx.size >= MIN_REACHABILITY_POINTS:
                    global_reach = summarize_reachability_h5(
                        h5_path,
                        config=reach_cfg,
                        coordinate_contract=coordinate_contract,
                        sample_indices=stage_idx,
                        condition_override=stage_label,
                        dataset_id_suffix=f":{selection_tag}_stage_{stage_label}",
                    )
                    _append_metric_rows(
                        rows,
                        global_reach["flat"],
                        subject_id=subject_id,
                        stage_code=stage_code,
                        stage_label=stage_label,
                        analysis_type="global_reachability_3d",
                        network="global",
                        metrics=REACHABILITY_METRICS,
                        n_points_used=int(stage_idx.size),
                    )

                if resolved_j3 is not None:
                    lookup = np.zeros((n,), dtype=bool)
                    lookup[stage_idx] = True
                    mask3 = _selection_mask(resolved_j3.centers, lookup, int(resolved_j3.j_hat.shape[0]))
                    if int(mask3.sum()) >= MIN_JACOBIAN_WINDOWS:
                        row3 = _summarize_global_mnps_jacobian_row(
                            dict(base),
                            resolved_j3.j_hat[mask3],
                            resolved_j3.j_dot[mask3] if resolved_j3.j_dot is not None else None,
                            source_dataset_path=resolved_j3.dataset_path,
                            dims=3,
                        )
                        if row3 is not None:
                            _append_metric_rows(
                                rows,
                                row3,
                                subject_id=subject_id,
                                stage_code=stage_code,
                                stage_label=stage_label,
                                analysis_type="global_mnj_3d",
                                network="global",
                                metrics=MNJ_METRICS,
                                n_points_used=int(mask3.sum()),
                            )

                if resolved_j9 is not None:
                    lookup = np.zeros((n,), dtype=bool)
                    lookup[stage_idx] = True
                    mask9 = _selection_mask(resolved_j9.centers, lookup, int(resolved_j9.j_hat.shape[0]))
                    if int(mask9.sum()) >= MIN_JACOBIAN_WINDOWS:
                        row9 = _summarize_global_mnps_jacobian_row(
                            dict(base),
                            resolved_j9.j_hat[mask9],
                            resolved_j9.j_dot[mask9] if resolved_j9.j_dot is not None else None,
                            source_dataset_path=resolved_j9.dataset_path,
                            dims=9,
                        )
                        if row9 is not None:
                            _append_metric_rows(
                                rows,
                                row9,
                                subject_id=subject_id,
                                stage_code=stage_code,
                                stage_label=stage_label,
                                analysis_type="global_mnj_9d",
                                network="global",
                                metrics=MNJ_METRICS,
                                n_points_used=int(mask9.sum()),
                            )

                if regional_group is None:
                    continue

                for network in sorted(regional_group.keys()):
                    net_grp = regional_group[network]
                    if "mnps" in net_grp:
                        region_idx = stage_idx[stage_idx < int(net_grp["mnps"].shape[0])]
                        if region_idx.size >= MIN_REACHABILITY_POINTS:
                            regional_reach = summarize_reachability_h5(
                                h5_path,
                                config=reach_cfg,
                                sample_indices=region_idx,
                                condition_override=stage_label,
                                dataset_id_suffix=f":stage_{stage_label}",
                                dataset_path=f"/regional_mnps/{network}/mnps",
                                used_space_override="regional_mnps_3d",
                                flat_overrides={
                                    "network": network,
                                    "source_dataset_path": f"/regional_mnps/{network}/mnps",
                                },
                            )
                            _append_metric_rows(
                                rows,
                                regional_reach["flat"],
                                subject_id=subject_id,
                                stage_code=stage_code,
                                stage_label=stage_label,
                                analysis_type="regional_reachability_3d",
                                network=network,
                                metrics=REACHABILITY_METRICS,
                                n_points_used=int(region_idx.size),
                            )

                    if "jacobian" not in net_grp:
                        continue

                    regional_j = np.asarray(net_grp["jacobian"][:], dtype=float)
                    if regional_j.ndim != 3 or regional_j.shape[1:] != (3, 3):
                        continue
                    centers3 = resolved_j3.centers if resolved_j3 is not None else None
                    lookup = np.zeros((n,), dtype=bool)
                    lookup[stage_idx] = True
                    mask_reg = _selection_mask(centers3, lookup, int(regional_j.shape[0]))
                    if int(mask_reg.sum()) < MIN_JACOBIAN_WINDOWS:
                        continue
                    regional_j_dot = None
                    if "jacobian_dot" in net_grp:
                        candidate = np.asarray(net_grp["jacobian_dot"][:], dtype=float)
                        if candidate.shape == regional_j.shape:
                            regional_j_dot = candidate[mask_reg]
                    if regional_j_dot is None:
                        regional_j_dot = _estimate_temporal_jacobian_delta(regional_j)
                        regional_j_dot = regional_j_dot[mask_reg] if regional_j_dot is not None else None
                    row_reg = _regional_jacobian_row(
                        dict(base),
                        j_hat=regional_j[mask_reg],
                        j_dot=regional_j_dot,
                        network=network,
                    )
                    if row_reg is None:
                        continue
                    _append_metric_rows(
                        rows,
                        row_reg,
                        subject_id=subject_id,
                        stage_code=stage_code,
                        stage_label=stage_label,
                        analysis_type="regional_mnj_3d",
                        network=network,
                        metrics=MNJ_METRICS,
                        n_points_used=int(mask_reg.sum()),
                    )

    return pd.DataFrame(rows)


def build_group_frequency_contrasts(metric_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group_cols = ["stage_code", "stage_label", "stage_display_label", "analysis_type", "analysis_label", "metric_family", "network", "metric"]
    for keys, group in metric_frame.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        base = dict(zip(group_cols, keys))
        for contrast_name, (left_group, right_group) in CONTRAST_GROUPS.items():
            left = pd.to_numeric(group.loc[group["group"] == left_group, "value"], errors="coerce").dropna().to_numpy(dtype=float)
            right = pd.to_numeric(group.loc[group["group"] == right_group, "value"], errors="coerce").dropna().to_numpy(dtype=float)
            row = dict(base)
            row.update(
                {
                    "dataset": DATASET,
                    "contrast_name": contrast_name,
                    "left_group": GROUP_LABELS.get(left_group, left_group),
                    "right_group": GROUP_LABELS.get(right_group, right_group),
                    "left_n": int(left.size),
                    "right_n": int(right.size),
                    "left_mean": float(np.mean(left)) if left.size else float("nan"),
                    "right_mean": float(np.mean(right)) if right.size else float("nan"),
                    "left_median": float(np.median(left)) if left.size else float("nan"),
                    "right_median": float(np.median(right)) if right.size else float("nan"),
                    "effect_size": _cohens_d(left, right),
                    "effect_estimate": float(np.mean(left) - np.mean(right)) if left.size and right.size else float("nan"),
                    "status": "ok",
                }
            )
            if left.size and right.size:
                _, p_value = stats.mannwhitneyu(left, right, alternative="two-sided")
                row["p_value"] = float(p_value)
            else:
                row["p_value"] = float("nan")
                row["status"] = "insufficient_groups"
            rows.append(row)

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["q_value"] = np.nan
    for _, group in out.groupby(["contrast_name", "stage_label", "analysis_type"], dropna=False):
        out.loc[group.index, "q_value"] = _bh_fdr(group["p_value"]).to_numpy(dtype=float)
    out["sig_tier"] = out.apply(_sig_tier, axis=1)
    out["abs_effect"] = pd.to_numeric(out["effect_size"], errors="coerce").abs()
    return out.sort_values(
        ["contrast_name", "stage_code", "analysis_type", "network", "q_value", "p_value", "abs_effect"],
        ascending=[True, True, True, True, True, True, False],
        na_position="last",
    ).reset_index(drop=True)


def build_selected_metrics_summary(contrasts: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if contrasts.empty:
        return pd.DataFrame()

    for (contrast_name, stage_label, analysis_type), group in contrasts.groupby(
        ["contrast_name", "stage_label", "analysis_type"],
        dropna=False,
    ):
        ordered = group.sort_values(["q_value", "p_value", "abs_effect"], ascending=[True, True, False], na_position="last")
        preferred = PREFERRED_METRICS.get(str(analysis_type), ())
        chosen = None
        for metric in preferred:
            match = ordered[ordered["metric"] == metric]
            if not match.empty:
                chosen = match.iloc[0]
                break
        if chosen is None:
            chosen = ordered.iloc[0]
        row = _row_dict(chosen)
        row["selected_from_analysis_type"] = analysis_type
        rows.append(row)
    return pd.DataFrame(rows)


def build_mmse_correlations(metric_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group_cols = ["stage_code", "stage_label", "stage_display_label", "analysis_type", "analysis_label", "metric_family", "network", "metric"]
    for cohort_key, allowed_groups in CORRELATION_COHORTS.items():
        cohort = metric_frame[metric_frame["group"].isin(allowed_groups)].copy()
        if cohort.empty:
            continue
        for keys, group in cohort.groupby(group_cols, dropna=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            work = group[["subject_id", "value", "mmse"]].dropna().copy().drop_duplicates(subset=["subject_id"])
            if len(work) < 4 or work["value"].nunique() < 2 or work["mmse"].nunique() < 2:
                continue
            spearman_rho, spearman_p = stats.spearmanr(work["value"], work["mmse"])
            pearson_r, pearson_p = stats.pearsonr(work["value"], work["mmse"])
            row = dict(zip(group_cols, keys))
            row.update(
                {
                    "dataset": DATASET,
                    "cohort_key": cohort_key,
                    "n_subjects": int(len(work)),
                    "spearman_rho": float(spearman_rho) if np.isfinite(spearman_rho) else float("nan"),
                    "pearson_r": float(pearson_r) if np.isfinite(pearson_r) else float("nan"),
                    "p_value": float(spearman_p) if np.isfinite(spearman_p) else float("nan"),
                    "pearson_p": float(pearson_p) if np.isfinite(pearson_p) else float("nan"),
                }
            )
            rows.append(row)

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["q_value"] = np.nan
    for _, group in out.groupby(["cohort_key", "stage_label", "analysis_type"], dropna=False):
        out.loc[group.index, "q_value"] = _bh_fdr(group["p_value"]).to_numpy(dtype=float)
    out["sig_tier"] = out.apply(_sig_tier, axis=1)
    out["abs_spearman_rho"] = pd.to_numeric(out["spearman_rho"], errors="coerce").abs()
    return out.sort_values(
        ["cohort_key", "stage_code", "analysis_type", "q_value", "p_value", "abs_spearman_rho"],
        ascending=[True, True, True, True, True, False],
        na_position="last",
    ).reset_index(drop=True)


def build_article_summary(
    qc_summary: pd.DataFrame,
    selected_metrics: pd.DataFrame,
    mmse_summary: pd.DataFrame,
    *,
    available_networks: Iterable[str] | None = None,
    selection_summary: dict[str, Any] | None = None,
) -> str:
    lines = [
        "# Photonic article summary",
        "",
    ]
    if selection_summary and selection_summary.get("selection_mode") == "blocks::center_within_exact_block_interval":
        lines.append(
            f"- exact block-native selection contributed `{int(selection_summary['n_selected_original_windows'])}` original windows "
            f"across `{int(selection_summary['n_selected_block_instances'])}` photic block instances in "
            f"`{int(selection_summary['n_subjects_with_blocks'])}` subjects."
        )
    elif not qc_summary.empty:
        all_photic = qc_summary[qc_summary["stage_label"] == "all_photic"]
        if not all_photic.empty:
            row = all_photic.iloc[0]
            lines.append(
                f"- stage recovery expanded photic coverage from `{int(row['total_original_markers'])}` explicit photic-labeled windows "
                f"to `{int(row['total_recovered_windows'])}` recovered photic windows "
                f"(`x{float(row['recovery_multiplier']):.2f}` multiplier)."
            )
    if not selected_metrics.empty:
        lines.extend(["", "## Strongest selected contrast rows", ""])
        for contrast_name in ("AD_vs_Healthy", "FTD_vs_Healthy", "AD_vs_FTD"):
            sub = selected_metrics[selected_metrics["contrast_name"] == contrast_name].copy()
            if sub.empty:
                continue
            lines.append(f"### {contrast_name}")
            lines.append("")
            for _, row in sub.sort_values(["stage_code", "analysis_type"]).iterrows():
                lines.append(
                    f"- `{row['stage_display_label']}` / `{row['analysis_label']}` / `{row['metric']}` "
                    f"(`{row['network']}`): d={float(row['effect_size']):.3f}, "
                    f"p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}"
                )
            lines.append("")
    if not mmse_summary.empty:
        lines.extend(["## MMSE overview", ""])
        for cohort_key in ("Dementia_all", "AD_only", "FTD_only"):
            sub = mmse_summary[mmse_summary["cohort_key"] == cohort_key].copy()
            if sub.empty:
                continue
            top = sub.sort_values(["q_value", "p_value", "abs_spearman_rho"], na_position="last").iloc[0]
            lines.append(
                f"- `{cohort_key}` strongest row: `{top['stage_display_label']}` / `{top['analysis_label']}` / "
                f"`{top['metric']}` (`{top['network']}`), rho={float(top['spearman_rho']):.3f}, "
                f"p={float(top['p_value']):.4g}, q={float(top['q_value']):.4g}"
            )
    regional_networks: list[str] = []
    if available_networks is not None:
        regional_networks = sorted({str(item) for item in available_networks if str(item) and str(item) != "global"})
    if regional_networks:
        network_note = f"- Regional photic outputs span {_format_backtick_list(regional_networks)} in the current H5 contracts."
    else:
        network_note = "- Regional photic outputs are available in the current H5 contracts."
    lines.extend(
        [
            "",
            "## Notes",
            "",
            network_note,
            "- Reachability rows use the shared `ndt-analysis` 3D reachability definition on the selected photic window surface.",
            "- Frequency labels are restricted to `PHOTO 5/10/15/20 Hz` in this export pass.",
        ]
    )
    return "\n".join(lines)


def write_photonic_exports(
    raw_root: Path,
    results_root: Path,
    *,
    selection_mode: str = DEFAULT_SELECTION_MODE,
    block_length_windows: int = DEFAULT_BLOCK_LENGTH_WINDOWS,
    duplicate_gap_windows: int = DEFAULT_DUPLICATE_GAP_WINDOWS,
) -> dict[str, str]:
    results_root.mkdir(parents=True, exist_ok=True)
    selection, selection_frame, selection_summary = load_stage_window_selection(
        raw_root,
        selection_mode=selection_mode,
        block_length_windows=block_length_windows,
        duplicate_gap_windows=duplicate_gap_windows,
    )
    qc_outputs: dict[str, str] = {}
    selection_files: dict[str, str] = {}
    qc_summary = pd.DataFrame()
    if selection_mode == SELECTION_MODE_STAGE_RECOVERY:
        qc_outputs = write_stage_qc_outputs(
            raw_root,
            results_root,
            block_length_windows=block_length_windows,
            duplicate_gap_windows=duplicate_gap_windows,
        )
        qc_summary = pd.read_csv(qc_outputs["summary_path"])
    else:
        selection_blocks_path = results_root / "blocknative_selection_blocks.csv"
        selection_summary_path = results_root / "blocknative_selection_summary.json"
        selection_frame.to_csv(selection_blocks_path, index=False)
        selection_summary_path.write_text(json.dumps(_json_ready(selection_summary), indent=2), encoding="utf-8")
        selection_files = {
            "blocknative_selection_blocks": str(selection_blocks_path),
            "blocknative_selection_summary": str(selection_summary_path),
        }

    phenos = load_participants()
    demography = build_demography_summary(phenos)
    metric_frame = build_subject_stage_metric_rows(
        raw_root,
        selection,
        coordinate_contract="cohort_anchored",
        selection_tag="exactblock" if selection_mode == SELECTION_MODE_EXACT_BLOCK_NATIVE else "recovery",
    )
    if metric_frame.empty:
        raise RuntimeError("No photic stage metrics were built from the selected ds006036 exports.")

    metric_frame = metric_frame.merge(
        phenos[["subject_id", "gender", "age", "group", "group_label", "mmse"]],
        on="subject_id",
        how="left",
        suffixes=("", "_meta"),
    )
    metric_frame["group"] = metric_frame["group_meta"].combine_first(metric_frame["group"])
    metric_frame = metric_frame.drop(columns=["group_meta"], errors="ignore")

    contrasts = build_group_frequency_contrasts(metric_frame)
    selected_metrics = build_selected_metrics_summary(contrasts)
    mmse_summary = build_mmse_correlations(metric_frame)

    demography_path = results_root / "demography_summary.csv"
    metric_path = results_root / "subject_stage_region_metrics.csv"
    contrast_path = results_root / "group_frequency_contrasts.csv"
    selected_path = results_root / "selected_stage_metrics_summary.csv"
    mmse_path = results_root / "mmse_correlations_summary.csv"
    summary_md_path = results_root / "photic_article_summary.md"
    manifest_path = results_root / "paper_exports_manifest.json"

    demography.to_csv(demography_path, index=False)
    metric_frame.to_csv(metric_path, index=False)
    contrasts.to_csv(contrast_path, index=False)
    selected_metrics.to_csv(selected_path, index=False)
    mmse_summary.to_csv(mmse_path, index=False)

    summary_md_path.write_text(
        build_article_summary(
            qc_summary,
            selected_metrics,
            mmse_summary,
            available_networks=metric_frame["network"].dropna().astype(str).unique().tolist(),
            selection_summary=selection_summary,
        ),
        encoding="utf-8",
    )

    manifest = {
        "dataset": DATASET,
        "raw_root": str(raw_root),
        "results_root": str(results_root),
        "participants_path": str(PARTICIPANTS_PATH),
        "selection_mode": selection_mode,
        "selection_summary": _json_ready(selection_summary),
        "coordinate_contract": "cohort_anchored",
        "block_length_windows": int(block_length_windows),
        "duplicate_gap_windows": int(duplicate_gap_windows),
        "n_subject_metric_rows": int(len(metric_frame)),
        "analysis_types": sorted(metric_frame["analysis_type"].dropna().astype(str).unique().tolist()),
        "networks": sorted(metric_frame["network"].dropna().astype(str).unique().tolist()),
        "stage_labels": sorted(metric_frame["stage_label"].dropna().astype(str).unique().tolist()),
        "output_files": {
            "demography_summary": str(demography_path),
            "subject_stage_region_metrics": str(metric_path),
            "group_frequency_contrasts": str(contrast_path),
            "selected_stage_metrics_summary": str(selected_path),
            "mmse_correlations_summary": str(mmse_path),
            "photic_article_summary": str(summary_md_path),
        },
    }
    manifest["output_files"].update(qc_outputs)
    manifest["output_files"].update(selection_files)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {
        "demography_path": str(demography_path),
        "metric_path": str(metric_path),
        "contrast_path": str(contrast_path),
        "selected_path": str(selected_path),
        "mmse_path": str(mmse_path),
        "summary_md_path": str(summary_md_path),
        "manifest_path": str(manifest_path),
    }


def main() -> None:
    args = parse_args()
    outputs = write_photonic_exports(
        args.raw_root,
        args.results_root,
        selection_mode=args.selection_mode,
        block_length_windows=args.block_length_windows,
        duplicate_gap_windows=args.duplicate_gap_windows,
    )
    print(f"Wrote demography summary to {outputs['demography_path']}")
    print(f"Wrote stage/region metrics to {outputs['metric_path']}")
    print(f"Wrote group contrasts to {outputs['contrast_path']}")
    print(f"Wrote selected metrics to {outputs['selected_path']}")
    print(f"Wrote MMSE summary to {outputs['mmse_path']}")


if __name__ == "__main__":
    main()
