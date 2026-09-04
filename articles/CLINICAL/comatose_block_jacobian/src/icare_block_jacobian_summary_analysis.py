from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
COMA_SRC_DIR = ARTICLE_DIR.parent / "comatose_ndt" / "src"
if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))
if str(COMA_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(COMA_SRC_DIR))

from ndt_analysis.config import load_dataset_config  # noqa: E402

from icare_mnps_summary_analysis import (  # noqa: E402
    DEFAULT_RAW_ROOT,
    SummaryConfig,
    aggregate_patient_bins,
    build_adapter_rows,
    build_handoff_manifest,
    build_metric_long_table,
    build_qc_summary,
    build_subject_index,
    ensure_output_dir,
    iter_h5_paths,
    join_time_metadata,
    load_or_build_run_table,
    prefilter_run_table,
    select_h5_paths_from_run_table,
    write_outputs,
)
from icare_patient_timeline_analysis import (  # noqa: E402
    DEFAULT_TIME_BIN_SCHEME,
    TIME_BIN_SCHEMES,
)


DEFAULT_ANALYSES: tuple[str, ...] = ("global_mnps_jacobian_9d_block_jacobian",)
DEFAULT_PROCESSED_ROOT = Path(
    "J:/repos/NoeticDiffusion/data/raw/"
    "neuralmanifolddynamics_physionet_icare_2_1_20260527_151403"
)
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "mnps_summary_20260528_part1_block_jacobian_cpc15_primary12h"
DEFAULT_CONFIG_PATH = ARTICLE_DIR.parent / "comatose_ndt" / "config" / "icare_ndt_analysis.yaml"
DEFAULT_TIMELINE_INPUT_DIR = (
    ARTICLE_DIR.parent / "comatose_ndt" / "results" / "timeline_analysis_20260524_part1_primary12h_9d"
)


def parse_args() -> SummaryConfig:
    parser = argparse.ArgumentParser(
        description="Run a thin I-CARE block-Jacobian wrapper on top of ndt_analysis legacy adapters."
    )
    parser.add_argument("--processed-root", type=Path, default=DEFAULT_PROCESSED_ROOT)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--adapter-config-path", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument(
        "--timeline-input-dir",
        type=Path,
        default=DEFAULT_TIMELINE_INPUT_DIR,
        help="Existing timeline_analysis directory reused for timing metadata and CPC filtering.",
    )
    parser.add_argument(
        "--analysis",
        dest="analyses",
        action="append",
        default=[],
        help="Optional analysis type to run. Repeat to override the block-Jacobian default.",
    )
    parser.add_argument(
        "--time-bin-scheme",
        type=str,
        choices=sorted(TIME_BIN_SCHEMES),
        default=DEFAULT_TIME_BIN_SCHEME,
    )
    parser.add_argument("--prefilter-good-cpc", type=int, default=None)
    parser.add_argument("--prefilter-poor-cpc", type=int, default=None)
    parser.add_argument("--prefilter-time-bin", type=str, default=None)
    parser.add_argument("--limit-h5", type=int, default=None)
    parser.add_argument("--workers", type=int, default=6)
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
    suffix_lookup: dict[str, Path] = {}
    ambiguous_keys: set[str] = set()
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


def build_block_contract_summary(
    *,
    processed_root: Path,
    run_rows: pd.DataFrame,
    patient_rows: pd.DataFrame,
    run_metrics: pd.DataFrame,
    patient_metrics: pd.DataFrame,
) -> dict[str, Any]:
    def _block_pairs(frame: pd.DataFrame) -> list[str]:
        if frame.empty or "source_group" not in frame.columns or "target_group" not in frame.columns:
            return []
        pairs = {
            f"{str(target)}{str(source)}"
            for source, target in zip(frame["source_group"], frame["target_group"])
            if pd.notna(source) and pd.notna(target)
        }
        return sorted(pairs)

    def _metric_list(frame: pd.DataFrame) -> list[str]:
        if frame.empty or "metric" not in frame.columns:
            return []
        return sorted(frame["metric"].dropna().astype(str).unique().tolist())

    return {
        "processed_root": str(processed_root),
        "analysis_type": DEFAULT_ANALYSES[0],
        "n_run_rows": int(len(run_rows)),
        "n_patient_rows": int(len(patient_rows)),
        "n_run_metrics": int(len(run_metrics)),
        "n_patient_metrics": int(len(patient_metrics)),
        "block_pairs_run_level": _block_pairs(run_rows),
        "block_pairs_patient_level": _block_pairs(patient_rows),
        "metrics_run_level": _metric_list(run_metrics),
        "metrics_patient_level": _metric_list(patient_metrics),
        "subjects_patient_level": int(patient_rows["subject"].astype(str).nunique()) if "subject" in patient_rows.columns else 0,
        "time_bins_patient_level": (
            sorted(patient_rows["time_bin"].dropna().astype(str).unique().tolist())
            if "time_bin" in patient_rows.columns
            else []
        ),
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

    run_rows, qc_rows = build_adapter_rows(config, h5_paths)
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

    contract_summary = build_block_contract_summary(
        processed_root=config.processed_root,
        run_rows=run_rows,
        patient_rows=patient_rows,
        run_metrics=run_metrics,
        patient_metrics=patient_metrics,
    )
    ensure_output_dir(config.output_dir)
    (config.output_dir / "block_contract_summary.json").write_text(
        json.dumps(contract_summary, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote block-Jacobian run-level adapter summaries to {config.output_dir / 'run_level_adapter_summaries.csv'}")
    print(f"Wrote block-Jacobian patient-bin adapter summaries to {config.output_dir / 'patient_timebin_adapter_summaries.csv'}")
    print(f"Wrote block-Jacobian signal-metric handoff files to {config.output_dir}")
    print(f"Wrote block contract summary to {config.output_dir / 'block_contract_summary.json'}")


if __name__ == "__main__":
    main()
