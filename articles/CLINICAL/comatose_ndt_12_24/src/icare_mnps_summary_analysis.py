from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from itertools import repeat
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Physical bounds for persistence / recovery reachability metrics.
# See icare_outcome_contrast_analysis.py for rationale.
# ---------------------------------------------------------------------------
PERSISTENCE_D_EFF_MAX: float = 3.0
PERSISTENCE_LOG_BOUND: float = 50.0
PERSISTENCE_KAPPA_MAX: float = 1.0e6


def clamp_persistence_metric(values: np.ndarray, metric: str) -> tuple[np.ndarray, int]:
    """Clamp known-bounded persistence / recovery metrics to physical ranges.

    Returns ``(clamped_array, n_values_clamped)``.  Only the named persistence
    families are touched; all other metrics pass through unchanged.
    """
    v = values.copy()
    if "persistence_d_eff" in metric:
        mask = np.isfinite(v) & (v > PERSISTENCE_D_EFF_MAX)
        v[mask] = PERSISTENCE_D_EFF_MAX
        return v, int(mask.sum())
    if "persistence_log_det" in metric or "persistence_log_eig_var" in metric:
        mask = np.isfinite(v) & (v > PERSISTENCE_LOG_BOUND)
        v[mask] = PERSISTENCE_LOG_BOUND
        return v, int(mask.sum())
    if "persistence_kappa" in metric:
        mask = np.isfinite(v) & (v > PERSISTENCE_KAPPA_MAX)
        v[mask] = PERSISTENCE_KAPPA_MAX
        return v, int(mask.sum())
    return v, 0


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.config import load_dataset_config  # noqa: E402
from ndt_analysis.legacy_adapters import build_adapters  # noqa: E402

from icare_patient_timeline_analysis import (  # noqa: E402
    AnalysisConfig as TimelineConfig,
    DEFAULT_TIME_BIN_SCHEME,
    TIME_BIN_SCHEMES,
    build_run_table,
    resolve_default_processed_root,
)


DEFAULT_ANALYSES: tuple[str, ...] = (
    "global_mnps_3d",
    "global_mnps_9d",
    "global_mnps_jacobian_3d",
    "global_mnps_jacobian_9d",
    "global_mnps_jacobian_9d_block_jacobian",
    "reachability_cones",
)
DEFAULT_RAW_ROOT = Path("E:/Science_Datasets/physionet/received/i-care_2_1_random100_longitudinal/training")
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "mnps_summary"
DEFAULT_CONFIG_PATH = ARTICLE_DIR / "config" / "icare_ndt_analysis.yaml"
TIME_JOIN_COLUMNS: tuple[str, ...] = (
    "subject",
    "subject_numeric",
    "processed_h5_path",
    "hospital",
    "age",
    "sex",
    "rosc_minutes",
    "ohca",
    "shockable_rhythm",
    "ttm_celsius",
    "outcome",
    "cpc",
    "header_path",
    "header_exists",
    "recording_start_clock",
    "recording_end_clock",
    "recording_start_elapsed_sec",
    "recording_end_elapsed_sec",
    "recording_duration_sec_from_header",
    "time_reference_available",
    "time_reference_enabled",
    "time_reference_schema_version",
    "time_reference_parser",
    "time_reference_status",
    "time_reference_source",
    "time_reference_anchor_mode",
    "time_reference_header_path",
    "time_reference_run_start_clock_raw",
    "time_reference_run_end_clock_raw",
    "time_reference_run_start_clock_sec",
    "time_reference_run_end_clock_sec",
    "time_reference_run_start_elapsed_sec",
    "time_reference_run_end_elapsed_sec",
    "time_reference_run_duration_sec",
    "time_reference_subject_anchor_start_sec",
    "time_reference_parse_errors",
    "time_reference_bins_hours",
    "time_reference_bins_seconds",
    "time_reference_window_start_from_anchor_sec_min",
    "time_reference_window_end_from_anchor_sec_max",
    "time_reference_window_count",
    "time_reference_window_bin_label_unique",
    "resolved_run_start_elapsed_sec",
    "resolved_run_end_elapsed_sec",
    "resolved_run_duration_sec",
    "resolved_timing_source",
    "run_start_from_anchor_sec",
    "run_end_from_anchor_sec",
    "run_midpoint_from_anchor_sec",
    "run_start_from_anchor_hours",
    "run_end_from_anchor_hours",
    "run_midpoint_from_anchor_hours",
    "run_anchor_source",
    "time_bin",
)
STRUCTURAL_GROUP_COLUMNS: tuple[str, ...] = (
    "analysis_type",
    "subject",
    "time_bin",
    "network",
    "block_scope",
    "block_space",
    "source_group",
    "target_group",
    "source_dataset_path",
)
METRIC_EXCLUDE_COLUMNS: set[str] = {
    "subject_numeric",
    "run",
    "acq",
    "age",
    "rosc_minutes",
    "cpc",
    "header_exists",
    "time_reference_available",
    "time_reference_enabled",
    "time_reference_run_start_clock_sec",
    "time_reference_run_end_clock_sec",
    "time_reference_run_start_elapsed_sec",
    "time_reference_run_end_elapsed_sec",
    "time_reference_run_duration_sec",
    "time_reference_subject_anchor_start_sec",
    "time_reference_window_start_from_anchor_sec_min",
    "time_reference_window_end_from_anchor_sec_max",
    "time_reference_window_count",
    "resolved_run_start_elapsed_sec",
    "resolved_run_end_elapsed_sec",
    "resolved_run_duration_sec",
    "run_start_from_anchor_sec",
    "run_end_from_anchor_sec",
    "run_midpoint_from_anchor_sec",
    "run_start_from_anchor_hours",
    "run_end_from_anchor_hours",
    "run_midpoint_from_anchor_hours",
    "n_runs",
    "n_rows",
    "n_windows_total",
    "aggregation_weight_total",
    "metric_count",
}
HANDOFF_CLASSICAL_ANALYSES: tuple[str, ...] = (
    "global_mnps_3d",
    "global_mnps_9d",
    "global_mnps_jacobian_3d",
    "global_mnps_jacobian_9d",
    "reachability_cones",
)
HANDOFF_CTIP_METRICS: tuple[str, ...] = (
    "rotation_norm_median",
    "frobenius_norm_median",
    "spectral_radius_median",
    "condition_number_median",
    "aci_median",
    "mdr_median",
    "q_ratio_h4_median",
    "tube_capture_gate_median",
    "block_frobenius_mean",
)
_WORKER_ADAPTERS: Dict[str, Any] | None = None


@dataclass(frozen=True)
class SummaryConfig:
    processed_root: Path
    raw_root: Path
    output_dir: Path
    adapter_config_path: Path
    analyses: tuple[str, ...]
    time_bins_hours: tuple[tuple[float, float, str], ...]
    time_bin_scheme: str
    timeline_input_dir: Path | None = None
    prefilter_good_cpc: int | None = None
    prefilter_poor_cpc: int | None = None
    prefilter_time_bin: str | None = None
    workers: int = 1
    limit_h5: int | None = None
    clamp_persistence_bounds: bool = False


def parse_args() -> SummaryConfig:
    parser = argparse.ArgumentParser(
        description="Run a thin I-CARE coma wrapper on top of ndt_analysis legacy adapters."
    )
    parser.add_argument(
        "--processed-root",
        type=Path,
        default=resolve_default_processed_root(),
        help="Processed I-CARE root containing per-run H5 files.",
    )
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=DEFAULT_RAW_ROOT,
        help="Raw I-CARE root used only for timing fallback via WFDB headers.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where run-level, patient-bin, and QC outputs will be written.",
    )
    parser.add_argument(
        "--adapter-config-path",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Config file passed into ndt_analysis.legacy_adapters.build_adapters(...).",
    )
    parser.add_argument(
        "--analysis",
        dest="analyses",
        action="append",
        default=[],
        help="Optional analysis type to run. Repeat to narrow the default set.",
    )
    parser.add_argument(
        "--time-bin-scheme",
        type=str,
        choices=sorted(TIME_BIN_SCHEMES),
        default=DEFAULT_TIME_BIN_SCHEME,
        help="Named time-bin scheme used when assigning anchor-relative windows.",
    )
    parser.add_argument(
        "--timeline-input-dir",
        type=Path,
        default=None,
        help="Optional existing timeline_analysis directory to reuse instead of rebuilding run timing metadata.",
    )
    parser.add_argument(
        "--prefilter-good-cpc",
        type=int,
        default=None,
        help="Optional upstream CPC value to keep before adapter extraction. Use together with --prefilter-poor-cpc.",
    )
    parser.add_argument(
        "--prefilter-poor-cpc",
        type=int,
        default=None,
        help="Optional upstream CPC value to keep before adapter extraction. Use together with --prefilter-good-cpc.",
    )
    parser.add_argument(
        "--prefilter-time-bin",
        type=str,
        default=None,
        help="Optional upstream time bin to keep before adapter extraction, e.g. 0_12h.",
    )
    parser.add_argument(
        "--limit-h5",
        type=int,
        default=None,
        help="Optional cap on the number of H5 files to inspect, for smoke tests.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Process workers for adapter collection. Use >1 to parallelize over H5 batches.",
    )
    parser.add_argument(
        "--clamp-persistence-bounds",
        action="store_true",
        default=False,
        help=(
            "Clamp persistence / recovery metrics to physically plausible ranges before writing "
            "run-level and patient-bin signal-metrics files.  Removes numerical blow-up artefacts "
            "(persistence_d_eff > 3, persistence_log_det > 50, persistence_kappa > 1e6) at the "
            "aggregation layer so downstream contrast analyses receive clean values."
        ),
    )
    args = parser.parse_args()
    if (args.prefilter_good_cpc is None) != (args.prefilter_poor_cpc is None):
        parser.error("--prefilter-good-cpc and --prefilter-poor-cpc must be provided together.")
    analyses = tuple(args.analyses) if args.analyses else DEFAULT_ANALYSES
    return SummaryConfig(
        processed_root=args.processed_root,
        raw_root=args.raw_root,
        output_dir=args.output_dir,
        adapter_config_path=args.adapter_config_path,
        analyses=analyses,
        time_bins_hours=TIME_BIN_SCHEMES[args.time_bin_scheme],
        time_bin_scheme=args.time_bin_scheme,
        timeline_input_dir=args.timeline_input_dir,
        prefilter_good_cpc=args.prefilter_good_cpc,
        prefilter_poor_cpc=args.prefilter_poor_cpc,
        prefilter_time_bin=args.prefilter_time_bin,
        workers=max(1, int(args.workers)),
        limit_h5=args.limit_h5,
        clamp_persistence_bounds=args.clamp_persistence_bounds,
    )


def normalize_path(value: Any) -> str:
    if value is None:
        return ""
    return str(Path(str(value))).replace("\\", "/").lower()


def iter_h5_paths(processed_root: Path, limit: int | None = None) -> List[Path]:
    paths = sorted(processed_root.rglob("*.h5"))
    if limit is not None and limit > 0:
        return paths[:limit]
    return paths


def path_tail_key(value: Any, *, depth: int = 2) -> str:
    normalized = normalize_path(value)
    if not normalized:
        return ""
    parts = [part for part in normalized.split("/") if part]
    if not parts:
        return ""
    return "/".join(parts[-depth:])


def remap_run_table_processed_paths(run_table: pd.DataFrame, processed_root: Path) -> pd.DataFrame:
    if run_table.empty or "processed_h5_path" not in run_table.columns:
        return run_table

    out = run_table.copy()
    recorded_paths = out["processed_h5_path"].fillna("").astype(str)
    missing_mask = ~recorded_paths.map(lambda value: Path(value).exists())
    if not missing_mask.any():
        out["normalized_source_h5_path"] = out["processed_h5_path"].map(normalize_path)
        return out

    actual_h5_paths = iter_h5_paths(processed_root)
    if not actual_h5_paths:
        out["normalized_source_h5_path"] = out["processed_h5_path"].map(normalize_path)
        return out

    suffix_lookup: Dict[str, Path] = {}
    ambiguous_keys: set[str] = set()
    for h5_path in actual_h5_paths:
        key = path_tail_key(h5_path)
        if not key:
            continue
        if key in suffix_lookup and suffix_lookup[key] != h5_path:
            ambiguous_keys.add(key)
            continue
        suffix_lookup[key] = h5_path
    for key in ambiguous_keys:
        suffix_lookup.pop(key, None)

    remapped_count = 0
    for idx in out.index[missing_mask]:
        key = path_tail_key(out.at[idx, "processed_h5_path"])
        mapped_path = suffix_lookup.get(key)
        if mapped_path is None:
            continue
        out.at[idx, "processed_h5_path"] = str(mapped_path)
        remapped_count += 1

    remaining_missing = (~out["processed_h5_path"].fillna("").astype(str).map(lambda value: Path(value).exists())).sum()
    if remapped_count:
        print(
            f"Remapped {remapped_count} run-table H5 paths into existing processed root {processed_root}.",
            flush=True,
        )
    if remaining_missing:
        print(f"Run-table remap left {int(remaining_missing)} missing processed_h5_path rows.", flush=True)

    out["normalized_source_h5_path"] = out["processed_h5_path"].map(normalize_path)
    return out


def select_time_join_columns(run_table: pd.DataFrame) -> pd.DataFrame:
    columns = [column for column in TIME_JOIN_COLUMNS if column in run_table.columns]
    out = run_table[columns].copy()
    out["normalized_source_h5_path"] = out["processed_h5_path"].map(normalize_path)
    return out


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    v = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    w = pd.to_numeric(weights, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(v) & np.isfinite(w) & (w > 0)
    if not np.any(mask):
        return float("nan")
    return float(np.average(v[mask], weights=w[mask]))


def coalesce_text(values: pd.Series) -> Any:
    non_null = [value for value in values.tolist() if pd.notna(value) and str(value).strip()]
    return non_null[0] if non_null else None


def load_or_build_run_table(config: SummaryConfig, *, coordinate_contract: str) -> pd.DataFrame:
    if config.timeline_input_dir is not None:
        path = config.timeline_input_dir / "run_timing_metadata.csv"
        if not path.exists():
            raise FileNotFoundError(f"Timeline input dir is missing run_timing_metadata.csv: {path}")
        run_table = pd.read_csv(path, low_memory=False)
        if "processed_h5_path" in run_table.columns:
            run_table = remap_run_table_processed_paths(run_table, config.processed_root)
        return run_table

    timeline_config = TimelineConfig(
        processed_root=config.processed_root,
        raw_root=config.raw_root,
        output_dir=config.output_dir,
        coordinate_contract=coordinate_contract,
        time_bins_hours=config.time_bins_hours,
        time_bin_scheme=config.time_bin_scheme,
        limit_h5=config.limit_h5,
    )
    return build_run_table(timeline_config)


def prefilter_run_table(
    run_table: pd.DataFrame,
    *,
    good_cpc: int | None,
    poor_cpc: int | None,
    time_bin: str | None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    filtered = run_table.copy()
    if "normalized_source_h5_path" not in filtered.columns and "processed_h5_path" in filtered.columns:
        filtered["normalized_source_h5_path"] = filtered["processed_h5_path"].map(normalize_path)

    summary = {
        "enabled": False,
        "good_cpc": good_cpc,
        "poor_cpc": poor_cpc,
        "time_bin": time_bin,
        "n_full_rows": int(len(run_table)),
        "n_full_subjects": int(run_table["subject"].astype(str).nunique()) if "subject" in run_table.columns else 0,
        "n_full_h5_paths": int(run_table["processed_h5_path"].astype(str).nunique()) if "processed_h5_path" in run_table.columns else 0,
    }

    if time_bin is not None:
        filtered = filtered[filtered["time_bin"].astype(str) == str(time_bin)].copy()
        summary["enabled"] = True

    if good_cpc is not None and poor_cpc is not None:
        cpc_numeric = pd.to_numeric(filtered["cpc"], errors="coerce")
        filtered = filtered[cpc_numeric.isin([float(good_cpc), float(poor_cpc)])].copy()
        summary["enabled"] = True

    summary.update(
        {
            "n_selected_rows": int(len(filtered)),
            "n_selected_subjects": int(filtered["subject"].astype(str).nunique()) if "subject" in filtered.columns else 0,
            "n_selected_h5_paths": int(filtered["processed_h5_path"].astype(str).nunique()) if "processed_h5_path" in filtered.columns else 0,
        }
    )
    return filtered.reset_index(drop=True), summary


def select_h5_paths_from_run_table(h5_paths: Sequence[Path], run_table: pd.DataFrame) -> List[Path]:
    if run_table.empty:
        return []
    allowed = set(run_table["normalized_source_h5_path"].astype(str))
    return [path for path in h5_paths if normalize_path(path) in allowed]


def init_adapter_worker(adapter_config_path: str) -> None:
    global _WORKER_ADAPTERS
    _WORKER_ADAPTERS = build_adapters(Path(adapter_config_path))


def collect_adapter_rows_for_h5(
    h5_path_str: str,
    analyses: Sequence[str],
    adapter_config_path: str,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    adapters = _WORKER_ADAPTERS if _WORKER_ADAPTERS is not None else build_adapters(Path(adapter_config_path))
    h5_paths = [h5_path_str]
    row_records: List[Dict[str, Any]] = []
    qc_records: List[Dict[str, Any]] = []

    for h5_path_str in h5_paths:
        h5_path = Path(h5_path_str)
        normalized_path = normalize_path(h5_path)
        for analysis_type in analyses:
            adapter = adapters.get(analysis_type)
            if adapter is None:
                qc_records.append(
                    {
                        "source_h5_path": str(h5_path),
                        "normalized_source_h5_path": normalized_path,
                        "analysis_type": analysis_type,
                        "status": "missing_adapter",
                        "row_count": 0,
                        "error": None,
                    }
                )
                continue
            try:
                rows = adapter.collect_rows(h5_path)
                status = "ok" if rows else "empty"
                qc_records.append(
                    {
                        "source_h5_path": str(h5_path),
                        "normalized_source_h5_path": normalized_path,
                        "analysis_type": analysis_type,
                        "status": status,
                        "row_count": int(len(rows)),
                        "error": None,
                    }
                )
                for row in rows:
                    enriched = dict(row)
                    enriched["analysis_type"] = analysis_type
                    enriched["normalized_source_h5_path"] = normalized_path
                    row_records.append(enriched)
            except Exception as exc:
                qc_records.append(
                    {
                        "source_h5_path": str(h5_path),
                        "normalized_source_h5_path": normalized_path,
                        "analysis_type": analysis_type,
                        "status": "error",
                        "row_count": 0,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
    return row_records, qc_records


def build_adapter_rows(config: SummaryConfig, h5_paths: Sequence[Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
    row_records: List[Dict[str, Any]] = []
    qc_records: List[Dict[str, Any]] = []

    if config.workers <= 1 or len(h5_paths) <= 1:
        if len(h5_paths) > 1:
            row_records = []
            qc_records = []
            for idx, path in enumerate(h5_paths, start=1):
                h5_rows, h5_qc = collect_adapter_rows_for_h5(
                    str(path),
                    list(config.analyses),
                    str(config.adapter_config_path),
                )
                row_records.extend(h5_rows)
                qc_records.extend(h5_qc)
                if idx % 100 == 0 or idx == len(h5_paths):
                    print(f"Processed {idx}/{len(h5_paths)} H5 files.", flush=True)
        elif h5_paths:
            batch_rows, batch_qc = collect_adapter_rows_for_h5(
                str(h5_paths[0]),
                list(config.analyses),
                str(config.adapter_config_path),
            )
            row_records.extend(batch_rows)
            qc_records.extend(batch_qc)
    else:
        with ProcessPoolExecutor(
            max_workers=config.workers,
            initializer=init_adapter_worker,
            initargs=(str(config.adapter_config_path),),
        ) as executor:
            mapped = executor.map(
                collect_adapter_rows_for_h5,
                (str(path) for path in h5_paths),
                repeat(list(config.analyses)),
                repeat(str(config.adapter_config_path)),
                chunksize=8,
            )
            for idx, (h5_rows, h5_qc) in enumerate(mapped, start=1):
                row_records.extend(h5_rows)
                qc_records.extend(h5_qc)
                if idx % 100 == 0 or idx == len(h5_paths):
                    print(f"Processed {idx}/{len(h5_paths)} H5 files.", flush=True)

    run_rows = pd.DataFrame(row_records)
    qc_rows = pd.DataFrame(qc_records)
    return run_rows, qc_rows


def join_time_metadata(run_rows: pd.DataFrame, run_table: pd.DataFrame) -> pd.DataFrame:
    if run_rows.empty:
        return run_rows.copy()
    time_lookup = select_time_join_columns(run_table)
    merged = run_rows.merge(
        time_lookup,
        on="normalized_source_h5_path",
        how="left",
        suffixes=("", "_time"),
    )
    if "source_h5_path" not in merged.columns and "processed_h5_path" in merged.columns:
        merged["source_h5_path"] = merged["processed_h5_path"]
    merged["join_matched"] = merged["processed_h5_path"].notna()
    return merged


def choose_weight_column(frame: pd.DataFrame) -> str:
    for candidate in ("n_timepoints", "n_windows", "jacobian_windows"):
        if candidate in frame.columns:
            values = pd.to_numeric(frame[candidate], errors="coerce")
            if np.isfinite(values).any():
                return candidate
    return "__unit_weight__"


def is_metric_column(frame: pd.DataFrame, column: str) -> bool:
    if column in METRIC_EXCLUDE_COLUMNS:
        return False
    if column in TIME_JOIN_COLUMNS or column in STRUCTURAL_GROUP_COLUMNS:
        return False
    if column.endswith("_path") or column.endswith("_clock_raw"):
        return False
    if column.startswith("time_reference_") or column.startswith("resolved_"):
        return False
    if column in {"finite_ok", "not_testable", "join_matched"}:
        return False
    if column in {"source_h5_path", "normalized_source_h5_path", "processed_h5_path", "run_anchor_source"}:
        return False
    if column.startswith("recording_"):
        return False
    if column.startswith("n_"):
        return False
    return pd.api.types.is_numeric_dtype(frame[column])


def aggregate_patient_bins(run_rows: pd.DataFrame) -> pd.DataFrame:
    if run_rows.empty:
        return pd.DataFrame()

    out = run_rows.copy()
    out["__unit_weight__"] = 1.0
    group_columns = [column for column in STRUCTURAL_GROUP_COLUMNS if column in out.columns]
    rows: List[Dict[str, Any]] = []

    for group_keys, group in out.groupby(group_columns, dropna=False):
        if not isinstance(group_keys, tuple):
            group_keys = (group_keys,)
        row: Dict[str, Any] = dict(zip(group_columns, group_keys))
        weight_column = choose_weight_column(group)
        weights = pd.to_numeric(group[weight_column], errors="coerce").fillna(1.0 if weight_column == "__unit_weight__" else 0.0)
        row["weight_column"] = weight_column
        row["aggregation_weight_total"] = float(weights.sum())
        row["n_runs"] = int(group["normalized_source_h5_path"].nunique()) if "normalized_source_h5_path" in group else int(len(group))
        row["n_rows"] = int(len(group))
        for meta_column in (
            "outcome",
            "cpc",
            "hospital",
            "age",
            "sex",
            "rosc_minutes",
            "ttm_celsius",
            "time_reference_status",
            "run_anchor_source",
        ):
            if meta_column in group.columns:
                row[meta_column] = coalesce_text(group[meta_column])
        for time_column in ("run_start_from_anchor_hours", "run_end_from_anchor_hours"):
            if time_column in group.columns:
                numeric = pd.to_numeric(group[time_column], errors="coerce")
                row[f"{time_column}_{'min' if 'start' in time_column else 'max'}"] = (
                    float(numeric.min()) if np.isfinite(numeric).any() else np.nan
                )
        for column in group.columns:
            if not is_metric_column(group, column):
                continue
            row[column] = weighted_mean(group[column], weights)
        rows.append(row)

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values([column for column in group_columns if column in {"analysis_type", "subject", "time_bin"}]).reset_index(drop=True)


def build_metric_long_table(frame: pd.DataFrame, *, level: str, clamp_persistence_bounds: bool = False) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()

    id_columns = [column for column in frame.columns if not is_metric_column(frame, column)]
    metric_frames: List[pd.DataFrame] = []
    n_clamped_total = 0
    for column in frame.columns:
        if not is_metric_column(frame, column):
            continue
        metric_frame = frame[id_columns].copy()
        metric_frame["metric"] = column
        metric_frame["value"] = pd.to_numeric(frame[column], errors="coerce")
        if clamp_persistence_bounds:
            v, n = clamp_persistence_metric(metric_frame["value"].to_numpy(dtype=float), column)
            if n > 0:
                metric_frame["value"] = v
                n_clamped_total += n
        metric_frame = metric_frame[np.isfinite(metric_frame["value"].to_numpy(dtype=float))]
        if metric_frame.empty:
            continue
        metric_frame["summary_level"] = level
        metric_frame["metric_family"] = metric_frame["analysis_type"].astype(str)
        metric_frames.append(metric_frame)
    if clamp_persistence_bounds and n_clamped_total:
        print(
            f"build_metric_long_table [{level}]: persistence bound clamping applied to {n_clamped_total} value(s).",
            flush=True,
        )
    if not metric_frames:
        return pd.DataFrame()
    return pd.concat(metric_frames, ignore_index=True)


def build_handoff_manifest(run_metrics: pd.DataFrame, patient_metrics: pd.DataFrame) -> dict:
    available_by_analysis = {}
    if not run_metrics.empty:
        for analysis_type, group in run_metrics.groupby("analysis_type", dropna=False):
            available_by_analysis[str(analysis_type)] = sorted(group["metric"].dropna().astype(str).unique().tolist())

    ctip_available = sorted(
        metric
        for metric in HANDOFF_CTIP_METRICS
        if not run_metrics.empty and metric in set(run_metrics["metric"].dropna().astype(str))
    )

    return {
        "run_level_metrics_file": "run_level_signal_metrics.csv",
        "patient_timebin_metrics_file": "patient_timebin_signal_metrics.csv",
        "classical_outcome_ready_analyses": list(HANDOFF_CLASSICAL_ANALYSES),
        "available_metrics_by_analysis": available_by_analysis,
        "ctip_light_handoff_metrics_available": ctip_available,
        "ctip_light_handoff_note": (
            "The coma wrapper preserves Jacobian, block-Jacobian, and reachability metrics so the next slice can "
            "derive adaptive-collapse aliases such as ati_reduced, q_ratio_h4, capture_gate, and cfca without "
            "rewriting ndt_analysis core logic."
        ),
        "patient_timebin_metric_count": int(len(patient_metrics)),
        "run_level_metric_count": int(len(run_metrics)),
    }


def build_qc_summary(
    h5_paths: Sequence[Path],
    run_table: pd.DataFrame,
    run_rows: pd.DataFrame,
    qc_rows: pd.DataFrame,
) -> dict:
    status_counts = qc_rows["status"].value_counts(dropna=False).to_dict() if not qc_rows.empty else {}
    missing_join_rows = int((~run_rows["join_matched"]).sum()) if not run_rows.empty and "join_matched" in run_rows.columns else 0
    time_reference_status_counts = (
        run_table["time_reference_status"].fillna("missing").value_counts(dropna=False).to_dict()
        if not run_table.empty and "time_reference_status" in run_table.columns
        else {}
    )
    anchor_source_counts = (
        run_table["run_anchor_source"].fillna("missing").value_counts(dropna=False).to_dict()
        if not run_table.empty and "run_anchor_source" in run_table.columns
        else {}
    )
    parse_warning_rows = []
    if not run_table.empty and "time_reference_parse_errors" in run_table.columns:
        parse_error_series = run_table["time_reference_parse_errors"].fillna("").astype(str).str.strip()
        valid_parse_errors = ~parse_error_series.isin({"", "[]", "[\"\"]", "None"})
        for row in run_table.loc[valid_parse_errors, [
            "subject",
            "run",
            "acq",
            "processed_h5_path",
            "time_reference_status",
            "time_reference_parse_errors",
        ]].to_dict(orient="records"):
            parse_warning_rows.append(row)

    return {
        "n_h5_files": int(len(h5_paths)),
        "n_run_rows": int(len(run_rows)),
        "n_qc_rows": int(len(qc_rows)),
        "adapter_status_counts": status_counts,
        "missing_join_rows": missing_join_rows,
        "time_reference_status_counts": time_reference_status_counts,
        "anchor_source_counts": anchor_source_counts,
        "parse_warning_rows": parse_warning_rows,
        "missing_adapter_analyses": sorted(
            qc_rows.loc[qc_rows["status"] == "missing_adapter", "analysis_type"].dropna().astype(str).unique().tolist()
        )
        if not qc_rows.empty
        else [],
        "error_rows": qc_rows.loc[qc_rows["status"] == "error"].to_dict(orient="records") if not qc_rows.empty else [],
        "unmatched_paths": (
            run_rows.loc[~run_rows["join_matched"], "source_h5_path"].dropna().astype(str).unique().tolist()
            if not run_rows.empty and "join_matched" in run_rows.columns
            else []
        ),
    }


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_outputs(
    config: SummaryConfig,
    run_rows: pd.DataFrame,
    patient_rows: pd.DataFrame,
    run_metrics: pd.DataFrame,
    patient_metrics: pd.DataFrame,
    qc_rows: pd.DataFrame,
    qc_summary: dict,
    handoff_manifest: dict,
    subject_index: pd.DataFrame,
) -> None:
    ensure_output_dir(config.output_dir)
    run_rows.to_csv(config.output_dir / "run_level_adapter_summaries.csv", index=False)
    patient_rows.to_csv(config.output_dir / "patient_timebin_adapter_summaries.csv", index=False)
    run_metrics.to_csv(config.output_dir / "run_level_signal_metrics.csv", index=False)
    patient_metrics.to_csv(config.output_dir / "patient_timebin_signal_metrics.csv", index=False)
    qc_rows.to_csv(config.output_dir / "adapter_qc.csv", index=False)
    subject_index.to_csv(config.output_dir / "subject_outcome_index.csv", index=False)
    (config.output_dir / "qc_summary.json").write_text(json.dumps(qc_summary, indent=2), encoding="utf-8")
    (config.output_dir / "metric_handoff_manifest.json").write_text(
        json.dumps(handoff_manifest, indent=2),
        encoding="utf-8",
    )


def build_subject_index(run_table: pd.DataFrame) -> pd.DataFrame:
    if run_table.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for subject, group in run_table.groupby("subject", dropna=False):
        row: Dict[str, Any] = {"subject": subject}
        for text_column in ("hospital", "sex", "ohca", "shockable_rhythm", "outcome", "cohort_tag", "bundle_tag"):
            if text_column in group.columns:
                row[text_column] = coalesce_text(group[text_column])
        for numeric_column in ("age", "rosc_minutes", "ttm_celsius", "cpc"):
            if numeric_column in group.columns:
                numeric = pd.to_numeric(group[numeric_column], errors="coerce")
                row[numeric_column] = float(numeric.median()) if np.isfinite(numeric).any() else np.nan
        rows.append(row)
    return pd.DataFrame(rows).sort_values("subject").reset_index(drop=True)


def main() -> None:
    config = parse_args()
    all_h5_paths = iter_h5_paths(config.processed_root, config.limit_h5)
    adapter_cfg = load_dataset_config(config.adapter_config_path)
    run_table = load_or_build_run_table(config, coordinate_contract=adapter_cfg.coordinate_contract)
    filtered_run_table, prefilter_summary = prefilter_run_table(
        run_table,
        good_cpc=config.prefilter_good_cpc,
        poor_cpc=config.prefilter_poor_cpc,
        time_bin=config.prefilter_time_bin,
    )
    h5_paths = select_h5_paths_from_run_table(all_h5_paths, filtered_run_table)
    if not h5_paths:
        raise ValueError(f"No H5 files remain after prefilter: {prefilter_summary}")
    run_rows, qc_rows = build_adapter_rows(config, h5_paths)
    run_rows = join_time_metadata(run_rows, filtered_run_table)
    patient_rows = aggregate_patient_bins(run_rows)
    run_metrics = build_metric_long_table(run_rows, level="run", clamp_persistence_bounds=config.clamp_persistence_bounds)
    patient_metrics = build_metric_long_table(patient_rows, level="patient_timebin", clamp_persistence_bounds=config.clamp_persistence_bounds)
    handoff_manifest = build_handoff_manifest(run_metrics, patient_metrics)
    handoff_manifest.update(
        {
            "processed_root": str(config.processed_root),
            "raw_root": str(config.raw_root),
            "adapter_config_path": str(config.adapter_config_path),
            "analyses": list(config.analyses),
            "time_bin_scheme": config.time_bin_scheme,
            "timeline_input_dir": str(config.timeline_input_dir) if config.timeline_input_dir is not None else None,
            "prefilter": prefilter_summary,
            "output_dir": str(config.output_dir),
        }
    )
    qc_summary = build_qc_summary(h5_paths, filtered_run_table, run_rows, qc_rows)
    qc_summary["prefilter"] = prefilter_summary
    subject_index = build_subject_index(filtered_run_table)
    write_outputs(
        config,
        run_rows,
        patient_rows,
        run_metrics,
        patient_metrics,
        qc_rows,
        qc_summary,
        handoff_manifest,
        subject_index,
    )

    print(f"Wrote run-level adapter summaries to {config.output_dir / 'run_level_adapter_summaries.csv'}")
    print(f"Wrote patient-bin adapter summaries to {config.output_dir / 'patient_timebin_adapter_summaries.csv'}")
    print(f"Wrote signal-metric handoff files to {config.output_dir}")
    print(f"Wrote QC bundle to {config.output_dir / 'qc_summary.json'}")


if __name__ == "__main__":
    main()
