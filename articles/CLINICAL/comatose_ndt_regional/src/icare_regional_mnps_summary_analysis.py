from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import sys
from pathlib import Path
from typing import Any, Iterable, List
import warnings

import pandas as pd

warnings.filterwarnings(
    "ignore",
    message=r"`sklearn\.utils\.parallel\.delayed` should be used with `sklearn\.utils\.parallel\.Parallel`.*",
    category=UserWarning,
)


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
COMA_SRC_DIR = ARTICLE_DIR.parent / "comatose_ndt" / "src"
if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))
if str(COMA_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(COMA_SRC_DIR))

from ndt_analysis.analysis_pipeline import _parse_feature_name_parts  # noqa: E402
from ndt_analysis.config import load_dataset_config  # noqa: E402

from icare_mnps_summary_analysis import (  # noqa: E402
    SummaryConfig,
    DEFAULT_RAW_ROOT,
    build_handoff_manifest,
    build_metric_long_table,
    build_qc_summary,
    build_subject_index,
    collect_adapter_rows_for_h5,
    ensure_output_dir,
    init_adapter_worker,
    iter_h5_paths,
    join_time_metadata,
    load_or_build_run_table,
    prefilter_run_table,
    select_h5_paths_from_run_table,
    write_outputs,
    aggregate_patient_bins,
)
from icare_patient_timeline_analysis import (  # noqa: E402
    DEFAULT_TIME_BIN_SCHEME,
    TIME_BIN_SCHEMES,
)


DEFAULT_ANALYSES: tuple[str, ...] = (
    "regional_3d",
    "regional_mnps_jacobian_3d",
    "regional_reachability_cones_3d",
)
DEFAULT_PROCESSED_ROOT = Path(
    "E:/Science_Datasets/physionet/processed/physionet_icare_2_1/"
    "neuralmanifolddynamics_physionet_icare_2_1_20260525_141608"
)
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "mnps_summary_20260526_regional_primary12h"
DEFAULT_CONFIG_PATH = ARTICLE_DIR / "config" / "icare_ndt_analysis_regional.yaml"
REGIONAL_ROOT_CSV_GLOB = "regional_mnps_subjects_*.csv"


def parse_args() -> SummaryConfig:
    parser = argparse.ArgumentParser(
        description="Run the regional I-CARE coma wrapper on top of ndt_analysis regional adapters."
    )
    parser.add_argument(
        "--processed-root",
        type=Path,
        default=DEFAULT_PROCESSED_ROOT,
        help="Processed I-CARE root containing per-run H5 files with /regional_mnps exports.",
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
        help="Directory where regional run-level, patient-bin, and QC outputs will be written.",
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
        help="Optional analysis type to run. Repeat to narrow the regional default set.",
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
        help="Optional upstream CPC value to keep before adapter extraction.",
    )
    parser.add_argument(
        "--prefilter-poor-cpc",
        type=int,
        default=None,
        help="Optional upstream CPC value to keep before adapter extraction.",
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
    )


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_feature_names(payload: Any) -> List[str]:
    if isinstance(payload, list):
        return [str(value) for value in payload]
    if isinstance(payload, dict):
        for key in ("feature_names", "features", "columns"):
            value = payload.get(key)
            if isinstance(value, list):
                return [str(item) for item in value]
    return []


def build_feature_inventory(processed_root: Path) -> pd.DataFrame:
    payload = _load_json(processed_root / "features_snapshot.json")
    feature_names = _extract_feature_names(payload)
    if not feature_names:
        return pd.DataFrame(columns=["feature_name", "feature_base", "region", "is_regional"])
    rows = []
    for feature_name in feature_names:
        try:
            feature_base, region = _parse_feature_name_parts(feature_name, {})
        except Exception:
            feature_base, region = str(feature_name), None
        rows.append(
            {
                "feature_name": str(feature_name),
                "feature_base": str(feature_base),
                "region": str(region) if region is not None else None,
                "is_regional": bool(region),
            }
        )
    frame = pd.DataFrame(rows)
    return frame.sort_values(["is_regional", "region", "feature_base", "feature_name"], ascending=[False, True, True, True])


def _regional_root_csv_columns(processed_root: Path) -> List[str]:
    paths = sorted(processed_root.glob(REGIONAL_ROOT_CSV_GLOB))
    if not paths:
        return []
    return pd.read_csv(paths[0], nrows=0).columns.astype(str).tolist()


def _normalize_path(value: Any) -> str:
    if value is None:
        return ""
    return str(Path(str(value))).replace("\\", "/").lower()


def _path_tail_key(value: Any, *, depth: int = 2) -> str:
    normalized = _normalize_path(value)
    if not normalized:
        return ""
    parts = [part for part in normalized.split("/") if part]
    if not parts:
        return ""
    return "/".join(parts[-depth:])


def force_align_run_table_paths(run_table: pd.DataFrame, processed_root: Path) -> pd.DataFrame:
    if run_table.empty or "processed_h5_path" not in run_table.columns:
        return run_table
    actual_h5_paths = iter_h5_paths(processed_root)
    if not actual_h5_paths:
        return run_table
    out = run_table.copy()
    suffix_lookup = {}
    ambiguous_keys = set()
    for h5_path in actual_h5_paths:
        key = _path_tail_key(h5_path)
        if not key:
            continue
        if key in suffix_lookup and suffix_lookup[key] != h5_path:
            ambiguous_keys.add(key)
            continue
        suffix_lookup[key] = h5_path
    for key in ambiguous_keys:
        suffix_lookup.pop(key, None)
    remapped = 0
    for idx in out.index:
        key = _path_tail_key(out.at[idx, "processed_h5_path"])
        mapped = suffix_lookup.get(key)
        if mapped is None:
            continue
        current = str(out.at[idx, "processed_h5_path"])
        if current != str(mapped):
            out.at[idx, "processed_h5_path"] = str(mapped)
            remapped += 1
    out["normalized_source_h5_path"] = out["processed_h5_path"].map(_normalize_path)
    if remapped:
        print(f"Force-remapped {remapped} run-table H5 paths into {processed_root}.", flush=True)
    return out


def build_adapter_rows_threaded(config: SummaryConfig, h5_paths: List[Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
    row_records: List[dict[str, Any]] = []
    qc_records: List[dict[str, Any]] = []
    init_adapter_worker(str(config.adapter_config_path))

    if config.workers <= 1 or len(h5_paths) <= 1:
        for idx, path in enumerate(h5_paths, start=1):
            h5_rows, h5_qc = collect_adapter_rows_for_h5(
                str(path),
                list(config.analyses),
                str(config.adapter_config_path),
            )
            row_records.extend(h5_rows)
            qc_records.extend(h5_qc)
            print(f"Processed {idx}/{len(h5_paths)} H5 files.", flush=True)
    else:
        with ThreadPoolExecutor(max_workers=config.workers) as executor:
            futures = [
                executor.submit(
                    collect_adapter_rows_for_h5,
                    str(path),
                    list(config.analyses),
                    str(config.adapter_config_path),
                )
                for path in h5_paths
            ]
            for idx, future in enumerate(as_completed(futures), start=1):
                h5_rows, h5_qc = future.result()
                row_records.extend(h5_rows)
                qc_records.extend(h5_qc)
                if idx % 25 == 0 or idx == len(h5_paths):
                    print(f"Processed {idx}/{len(h5_paths)} H5 files.", flush=True)

    return pd.DataFrame(row_records), pd.DataFrame(qc_records)


def build_contract_summary(
    processed_root: Path,
    run_rows: pd.DataFrame,
    patient_rows: pd.DataFrame,
    feature_inventory: pd.DataFrame,
) -> dict[str, Any]:
    run_manifest = _load_json(processed_root / "run_manifest.json") or {}
    regional_run_rows = run_rows[run_rows["analysis_type"].isin(DEFAULT_ANALYSES)].copy() if not run_rows.empty else pd.DataFrame()
    patient_networks = (
        sorted(patient_rows["network"].dropna().astype(str).unique().tolist())
        if not patient_rows.empty and "network" in patient_rows.columns
        else []
    )
    feature_networks = (
        sorted(feature_inventory["region"].dropna().astype(str).unique().tolist())
        if not feature_inventory.empty and "region" in feature_inventory.columns
        else []
    )
    analysis_counts = (
        regional_run_rows.groupby("analysis_type")["network"].nunique().to_dict()
        if not regional_run_rows.empty and "network" in regional_run_rows.columns
        else {}
    )
    return {
        "processed_root": str(processed_root),
        "regional_outputs": run_manifest.get("regional_outputs"),
        "regional_outputs_path": run_manifest.get("regional_outputs_path"),
        "regional_networks_patient_rows": patient_networks,
        "regional_networks_feature_snapshot": feature_networks,
        "regional_root_csv_columns": _regional_root_csv_columns(processed_root),
        "regional_feature_count": int(feature_inventory["is_regional"].sum()) if not feature_inventory.empty else 0,
        "regional_feature_bases": (
            sorted(feature_inventory.loc[feature_inventory["is_regional"], "feature_base"].dropna().astype(str).unique().tolist())
            if not feature_inventory.empty
            else []
        ),
        "unique_network_counts_by_analysis": {str(key): int(value) for key, value in analysis_counts.items()},
        "n_regional_run_rows": int(len(regional_run_rows)),
        "n_regional_patient_rows": int(len(patient_rows)),
    }


def main() -> None:
    config = parse_args()
    all_h5_paths = iter_h5_paths(config.processed_root, None)
    adapter_cfg = load_dataset_config(config.adapter_config_path)
    run_table = load_or_build_run_table(config, coordinate_contract=adapter_cfg.coordinate_contract)
    run_table = force_align_run_table_paths(run_table, config.processed_root)
    filtered_run_table, prefilter_summary = prefilter_run_table(
        run_table,
        good_cpc=config.prefilter_good_cpc,
        poor_cpc=config.prefilter_poor_cpc,
        time_bin=config.prefilter_time_bin,
    )
    h5_paths = select_h5_paths_from_run_table(all_h5_paths, filtered_run_table)
    if config.limit_h5 is not None and config.limit_h5 > 0:
        h5_paths = h5_paths[: config.limit_h5]
    if not h5_paths:
        raise ValueError(f"No H5 files remain after prefilter: {prefilter_summary}")
    run_rows, qc_rows = build_adapter_rows_threaded(config, h5_paths)
    run_rows = join_time_metadata(run_rows, filtered_run_table)
    patient_rows = aggregate_patient_bins(run_rows)
    run_metrics = build_metric_long_table(run_rows, level="run")
    patient_metrics = build_metric_long_table(patient_rows, level="patient_timebin")
    handoff_manifest = build_handoff_manifest(run_metrics, patient_metrics)
    handoff_manifest.update(
        {
            "processed_root": str(config.processed_root),
            "raw_root": str(config.raw_root),
            "adapter_config_path": str(config.adapter_config_path),
            "analyses": list(config.analyses),
            "classical_outcome_ready_analyses": list(config.analyses),
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

    feature_inventory = build_feature_inventory(config.processed_root)
    contract_summary = build_contract_summary(config.processed_root, run_rows, patient_rows, feature_inventory)
    ensure_output_dir(config.output_dir)
    feature_inventory.to_csv(config.output_dir / "regional_feature_inventory.csv", index=False)
    (config.output_dir / "regional_contract_summary.json").write_text(
        json.dumps(contract_summary, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote regional run-level adapter summaries to {config.output_dir / 'run_level_adapter_summaries.csv'}")
    print(f"Wrote regional patient-bin adapter summaries to {config.output_dir / 'patient_timebin_adapter_summaries.csv'}")
    print(f"Wrote regional signal-metric handoff files to {config.output_dir}")
    print(f"Wrote regional feature inventory to {config.output_dir / 'regional_feature_inventory.csv'}")
    print(f"Wrote regional contract summary to {config.output_dir / 'regional_contract_summary.json'}")


if __name__ == "__main__":
    main()
