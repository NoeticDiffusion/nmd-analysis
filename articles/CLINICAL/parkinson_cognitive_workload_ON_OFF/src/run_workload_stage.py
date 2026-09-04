from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
ARTICLE_DIR = SRC_DIR.parent
REPO_ROOT = ARTICLE_DIR.parents[2]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))


def _append_status(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line.rstrip("\n") + "\n")


def _run_analysis(args: argparse.Namespace) -> None:
    from ndt_analysis.analysis_pipeline import run_cleaned_analysis_pipeline  # noqa: E402

    status_path = Path(args.status_path)
    status_path.write_text("", encoding="utf-8")
    _append_status(status_path, "start")
    _append_status(status_path, f"config={args.config_path}")
    _append_status(status_path, f"cleaned_root={args.cleaned_root}")
    _append_status(status_path, f"output_root={args.output_root}")
    result = run_cleaned_analysis_pipeline(
        config_path=Path(args.config_path),
        cleaned_root=Path(args.cleaned_root),
        output_root=Path(args.output_root),
    )
    _append_status(status_path, "done")
    _append_status(status_path, json.dumps(result, indent=2, default=str))


def _run_wrapper(args: argparse.Namespace) -> None:
    from compute_parkinson_cognitive_workload_metrics import (  # noqa: E402
        MANIFEST_JSON as EVENT_MANIFEST_JSON,
        RUN_METRICS_CSV,
        SUBJECT_METRICS_CSV,
        aggregate_subject_metrics,
        build_reference_model,
        build_run_metric_rows,
        build_segment_info_map,
        gather_reference_segments,
        infer_dataset_spec,
        load_runs,
    )
    from export_parkinson_cognitive_workload_contrasts import (  # noqa: E402
        EVENT_CONTRASTS_CSV,
        WRAPPER_SUMMARY_FILENAME,
        apply_fdr,
        build_summary as build_wrapper_summary,
        load_subject_long,
        paired_contrast_rows,
        unpaired_contrast_rows,
    )
    from parkinson_cognitive_workload_support import ensure_dir, write_json  # noqa: E402

    status_path = Path(args.status_path)
    status_path.write_text("", encoding="utf-8")
    _append_status(status_path, "start")
    spec = infer_dataset_spec(dataset_root=Path(args.dataset_root), dataset_id=args.dataset_id)
    dataset_root = Path(args.dataset_root) if args.dataset_root else spec.dataset_root
    metrics_dir = Path(args.event_metrics_dir)
    wrapper_dir = Path(args.wrapper_dir)
    ensure_dir(metrics_dir)
    ensure_dir(wrapper_dir)
    _append_status(status_path, f"dataset_id={spec.dataset_id}")
    _append_status(status_path, f"contract={args.coordinate_contract}")

    runs = load_runs(
        dataset_root,
        spec,
        coordinate_contract=str(args.coordinate_contract),
        limit_h5=args.limit_h5,
    )
    _append_status(status_path, f"loaded_runs={len(runs)}")
    if not runs:
        raise RuntimeError(f"No H5 files were found under {dataset_root}.")

    segment_info = build_segment_info_map(spec)
    _append_status(status_path, f"segment_info={len(segment_info)}")
    sampled_by_key = gather_reference_segments(runs)
    _append_status(status_path, f"reference_keys={len(sampled_by_key)}")
    references = {}
    for key, blocks in sampled_by_key.items():
        _append_status(status_path, f"build_reference={key.level}:{key.network}:{key.dim}d blocks={len(blocks)}")
        references[key] = build_reference_model(blocks, dim=key.dim)
    run_rows = build_run_metric_rows(
        runs,
        segment_info,
        references=references,
        pre_windows=int(args.pre_event_windows),
        post_windows=int(args.post_event_windows),
    )
    _append_status(status_path, f"run_rows={len(run_rows)}")
    run_frame = pd.DataFrame(run_rows).sort_values(
        ["analysis_type", "segment_kind", "segment_family", "segment_label", "group", "condition", "subject_id", "network"]
    )
    subject_frame = aggregate_subject_metrics(run_frame)
    run_frame.to_csv(metrics_dir / RUN_METRICS_CSV, index=False)
    subject_frame.to_csv(metrics_dir / SUBJECT_METRICS_CSV, index=False)
    _append_status(status_path, f"subject_rows={len(subject_frame)}")

    reference_manifest = {
        f"{key.level}:{key.network}:{key.dim}d": {
            "n_fit_blocks": int(len(sampled_by_key.get(key, []))),
            "n_fit_points": int((references.get(key) or {}).get("n_fit_points") or 0),
            "n_states": (references.get(key) or {}).get("n_states"),
        }
        for key in sorted(references.keys(), key=lambda item: (item.level, item.network, item.dim))
    }
    event_manifest = {
        "dataset_id": spec.dataset_id,
        "task": spec.task,
        "dataset_root": str(dataset_root),
        "coordinate_contract": str(args.coordinate_contract),
        "pre_event_windows": int(args.pre_event_windows),
        "post_event_windows": int(args.post_event_windows),
        "n_input_runs": int(len(runs)),
        "n_run_metric_rows": int(len(run_frame)),
        "n_subject_metric_rows": int(len(subject_frame)),
        "segment_labels": sorted(run_frame["segment_label"].dropna().unique().tolist()) if not run_frame.empty else [],
        "analysis_types": sorted(run_frame["analysis_type"].dropna().unique().tolist()) if not run_frame.empty else [],
        "reference_models": reference_manifest,
    }
    write_json(metrics_dir / EVENT_MANIFEST_JSON, event_manifest)

    event_long = load_subject_long(metrics_dir)
    contrast_rows = paired_contrast_rows(event_long) + unpaired_contrast_rows(event_long)
    event_contrasts = apply_fdr(pd.DataFrame(contrast_rows))
    event_contrasts.to_csv(wrapper_dir / EVENT_CONTRASTS_CSV, index=False)
    (wrapper_dir / WRAPPER_SUMMARY_FILENAME).write_text(build_wrapper_summary(event_contrasts), encoding="utf-8")
    write_json(
        wrapper_dir / EVENT_MANIFEST_JSON,
        {
            "input_dir": str(metrics_dir),
            "output_dir": str(wrapper_dir),
            "event_contrasts": str(wrapper_dir / EVENT_CONTRASTS_CSV),
            "n_rows": int(len(event_contrasts)),
        },
    )
    _append_status(status_path, f"contrast_rows={len(event_contrasts)}")
    _append_status(status_path, "done")


def _run_merge(args: argparse.Namespace) -> None:
    from parkinson_cognitive_workload_support import (  # noqa: E402
        COHORT_COORDINATE_CONTRACT,
        PRIMARY_EVENT_CONTRASTS_CSV,
        PRIMARY_STANDARD_CONTRASTS_CSV,
        SUBJECT_COORDINATE_CONTRACT,
        SUMMARY_FILENAME,
        ensure_dir,
        infer_dataset_spec,
        results_dir_for_spec,
    )
    from run_parkinson_cognitive_workload_pipeline import (  # noqa: E402
        CONTRAST_PRIORITY,
        EVENT_CONTRASTS_CSV as MERGE_EVENT_CONTRASTS_CSV,
        build_summary as build_primary_summary,
        load_csv_if_exists,
        select_primary_rows,
    )

    status_path = Path(args.status_path)
    status_path.write_text("", encoding="utf-8")
    _append_status(status_path, "start")
    spec = infer_dataset_spec(dataset_root=Path(args.dataset_root), dataset_id=args.dataset_id)
    results_dir = Path(args.results_dir) if args.results_dir else results_dir_for_spec(spec)
    ensure_dir(results_dir)

    subject_contrast_files = sorted((results_dir / "standard_analysis_subject").glob(f"{spec.dataset_id}_contrast_results_*.parquet"))
    cohort_contrast_files = sorted((results_dir / "standard_analysis_cohort").glob(f"{spec.dataset_id}_contrast_results_*.parquet"))
    if not subject_contrast_files or not cohort_contrast_files:
        raise FileNotFoundError("Missing contrast_results parquet in subject or cohort analysis directory.")

    standard_by_contract = {
        SUBJECT_COORDINATE_CONTRACT: pd.read_parquet(subject_contrast_files[-1]),
        COHORT_COORDINATE_CONTRACT: pd.read_parquet(cohort_contrast_files[-1]),
    }
    wrapper_by_contract = {
        SUBJECT_COORDINATE_CONTRACT: load_csv_if_exists(results_dir / "wrapper_subject" / MERGE_EVENT_CONTRASTS_CSV),
        COHORT_COORDINATE_CONTRACT: load_csv_if_exists(results_dir / "wrapper_cohort" / MERGE_EVENT_CONTRASTS_CSV),
    }

    primary_standard = select_primary_rows(standard_by_contract)
    primary_wrapper = select_primary_rows(wrapper_by_contract)
    primary_standard.to_csv(results_dir / PRIMARY_STANDARD_CONTRASTS_CSV, index=False)
    primary_wrapper.to_csv(results_dir / PRIMARY_EVENT_CONTRASTS_CSV, index=False)
    (results_dir / SUMMARY_FILENAME).write_text(build_primary_summary(spec, primary_standard, primary_wrapper), encoding="utf-8")

    manifest = {
        "dataset_id": spec.dataset_id,
        "task": spec.task,
        "dataset_root": str(Path(args.dataset_root) if args.dataset_root else spec.dataset_root),
        "results_dir": str(results_dir),
        "contrast_priority": CONTRAST_PRIORITY,
        "primary_standard_contrasts": str(results_dir / PRIMARY_STANDARD_CONTRASTS_CSV),
        "primary_event_contrasts": str(results_dir / PRIMARY_EVENT_CONTRASTS_CSV),
        "summary_path": str(results_dir / SUMMARY_FILENAME),
        "subject_contrast_path": str(subject_contrast_files[-1]),
        "cohort_contrast_path": str(cohort_contrast_files[-1]),
        "wrapper_subject_event_contrasts": str(results_dir / "wrapper_subject" / MERGE_EVENT_CONTRASTS_CSV),
        "wrapper_cohort_event_contrasts": str(results_dir / "wrapper_cohort" / MERGE_EVENT_CONTRASTS_CSV),
    }
    (results_dir / "pipeline_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    _append_status(status_path, f"primary_standard_rows={len(primary_standard)}")
    _append_status(status_path, f"primary_event_rows={len(primary_wrapper)}")
    _append_status(status_path, "done")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single Parkinson cognitive workload stage with a status file.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    analysis = subparsers.add_parser("analysis")
    analysis.add_argument("--config-path", required=True)
    analysis.add_argument("--cleaned-root", required=True)
    analysis.add_argument("--output-root", required=True)
    analysis.add_argument("--status-path", required=True)

    wrapper = subparsers.add_parser("wrapper")
    wrapper.add_argument("--dataset-id", required=True)
    wrapper.add_argument("--dataset-root", required=True)
    wrapper.add_argument("--coordinate-contract", required=True)
    wrapper.add_argument("--event-metrics-dir", required=True)
    wrapper.add_argument("--wrapper-dir", required=True)
    wrapper.add_argument("--status-path", required=True)
    wrapper.add_argument("--limit-h5", type=int, default=None)
    wrapper.add_argument("--pre-event-windows", type=int, default=2)
    wrapper.add_argument("--post-event-windows", type=int, default=3)

    merge = subparsers.add_parser("merge")
    merge.add_argument("--dataset-id", required=True)
    merge.add_argument("--dataset-root", required=True)
    merge.add_argument("--results-dir", required=True)
    merge.add_argument("--status-path", required=True)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        if args.mode == "analysis":
            _run_analysis(args)
        elif args.mode == "wrapper":
            _run_wrapper(args)
        elif args.mode == "merge":
            _run_merge(args)
        else:
            raise ValueError(f"Unsupported mode: {args.mode}")
    except BaseException as exc:  # noqa: BLE001
        status_path = Path(args.status_path)
        status_path.parent.mkdir(parents=True, exist_ok=True)
        _append_status(status_path, "error")
        _append_status(status_path, "".join(traceback.format_exception(exc)))
        raise


if __name__ == "__main__":
    main()
