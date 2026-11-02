from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import h5py
import pyarrow.parquet as pq


ARTICLE = Path(r"J:\repos\nmd-analysis\articles\BOAS_sleep_dataset_ndt_v.1.0_C1_C2")
INPUT_ROOT = ARTICLE / "results" / "producer_support_sidecar_export_pilot_20261002_v1"
SPLIT = Path(r"J:\repos\nmd-analysis\articles\BOAS_sleep_dataset_ndt._v.1.0\results\continuous_full_surface_support_audit_20260929_v4\fold_manifests\fold_1.json")
CLEAN_CHECKOUT = Path(r"C:\Users\Robin\.codex\worktrees\boas-support-pilot\NeuralManifoldDynamics")
SUBJECT_ID = "sub-073"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit outcome-blind signal-support provenance through the emitted H5.")
    parser.add_argument("--input-root", type=Path, default=INPUT_ROOT)
    parser.add_argument("--h5-run-dir", default="fold_1_apply_support_cachefix")
    args = parser.parse_args()
    input_root = args.input_root.expanduser().resolve()
    sys.path.insert(0, str(CLEAN_CHECKOUT / "mndm" / "src"))
    sys.path.insert(0, str(CLEAN_CHECKOUT / "core" / "src"))
    from mndm.pipeline.signal_support_export import build_signal_support_export, validate_support_record

    ds = input_root / "processed" / "ds005555"
    feature_path = ds / "features.parquet"
    manifest_path = input_root / "control" / "input_manifest.json"
    columns = [
        "subject", "file", "epoch_id", "t_start", "t_end",
        "source_sample_mapping_status", "source_sample_mapping_reason",
        "nominal_source_sample_start", "nominal_source_sample_end_exclusive",
        "nominal_source_sample_absolute_start", "nominal_source_sample_absolute_end_exclusive",
        "source_first_samp", "source_sfreq_hz",
        "nominal_source_time_start_sec", "nominal_source_time_end_sec",
        "actual_sample_contributors_status", "actual_sample_contributors_reason",
        "actual_source_sample_start", "actual_source_sample_end_exclusive",
        "actual_source_time_start_sec", "actual_source_time_end_sec",
        "preprocessed_sample_start", "preprocessed_sample_end_exclusive", "preprocessed_sfreq_hz",
        "input_sample_finite_status", "input_sample_finite_fraction", "input_sample_gap_count",
        "input_sample_gap_spans", "input_sample_invalid_reason",
    ]
    frame = pq.read_table(feature_path, columns=columns).to_pandas()
    frame = frame[frame["subject"].astype(str).eq(SUBJECT_ID)].copy()
    files = sorted(frame["file"].astype(str).unique().tolist())
    if len(files) != 1 or frame.empty:
        raise RuntimeError(f"expected exactly one non-empty apply recording for {SUBJECT_ID}; got {files}")
    raw_file = Path(files[0]).name

    sidecar_path = ds / "qc_artifacts" / f"{Path(raw_file).stem}_qc_artifacts.json"
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    record = dict(sidecar.get("signal_support_provenance", {}))
    record["raw_file"] = sidecar.get("file", raw_file)
    sidecar_valid, sidecar_reason = validate_support_record(record, raw_file)
    payload = build_signal_support_export(frame, [record])
    execution = payload.get("execution_records", [])
    if len(execution) != 1:
        raise RuntimeError(f"expected one execution record; got {len(execution)}")
    execution_record = execution[0]
    nested_record = execution_record.get("record", {})
    flatline = nested_record.get("raw_joint_eeg_flatline_qc", {})
    flatline_intervals = flatline.get("intervals", []) if isinstance(flatline, dict) else []
    if not isinstance(flatline_intervals, list):
        flatline_intervals = []

    # The MNDM helper computes row overlap for source annotation intervals.
    # Compute the raw flatline overlap independently from the same recorded
    # original-raw-second clock, without loading any feature values.
    flatline_overlaps = []
    for row in payload.get("per_epoch_input_extent", []):
        start = row.get("nominal_original_time_start_sec")
        end = row.get("nominal_original_time_end_sec")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            continue
        for interval in flatline_intervals:
            try:
                interval_file = Path(str(interval.get("raw_file", ""))).name
                lo, hi = float(interval["start_sec"]), float(interval["end_sec"])
            except (KeyError, TypeError, ValueError):
                continue
            if interval_file == raw_file and hi > float(start) and lo < float(end):
                flatline_overlaps.append({
                    "epoch_id": row.get("epoch_id"),
                    "interval_start_sec": lo,
                    "interval_end_sec": hi,
                })

    fold = json.loads(SPLIT.read_text(encoding="utf-8"))
    expected_hash = str(fold["source_file_sha256"].get(raw_file, "")).lower()
    actual_hash = str(record.get("source", {}).get("sha256", "")).lower()
    extents = payload.get("per_epoch_input_extent", [])
    source_quality_intervals = payload.get("source_quality_intervals", [])
    run_dir = ds / args.h5_run_dir
    h5_candidates = sorted(run_dir.rglob("*.h5")) if run_dir.is_dir() else []
    if len(h5_candidates) != 1:
        raise RuntimeError(f"expected one H5 under {run_dir}; found {len(h5_candidates)}")
    h5_path = h5_candidates[0]

    def _text_scalar(dataset: h5py.Dataset) -> str:
        value = dataset[()]
        return value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)

    with h5py.File(h5_path, "r") as h5:
        support_group = h5["provenance/signal_support_provenance"]
        h5_extents = json.loads(_text_scalar(support_group["per_epoch_input_extent_json"]))
        h5_quality_intervals = json.loads(_text_scalar(support_group["source_quality_intervals_json"]))
        if not isinstance(h5_extents, list) or not isinstance(h5_quality_intervals, list):
            raise RuntimeError("H5 signal-support provenance does not contain JSON arrays")

        def _epoch(value: Any) -> str:
            try:
                return str(int(float(value)))
            except (TypeError, ValueError):
                return str(value or "").strip()

        candidate_clocks = {
            _epoch(row.epoch_id): (float(row.t_start), float(row.t_end))
            for row in frame.itertuples()
        }
        helper_clocks = {
            _epoch(row.get("epoch_id")): (
                float(row["nominal_time_start_sec"]),
                float(row["nominal_time_end_sec"]),
            )
            for row in extents
        }
        h5_clocks = {
            _epoch(row.get("epoch_id")): (
                float(row["nominal_time_start_sec"]),
                float(row["nominal_time_end_sec"]),
            )
            for row in h5_extents
        }
        h5_epoch_values = [_epoch(value) for value in h5["epoch_id"][:]]
        h5_epoch_ids = set(h5_epoch_values)
        source_support_start = "actual_source_sample_start"
        source_support_end = "actual_source_sample_end_exclusive"
        nominal_support_start = "original_sample_start"
        nominal_support_end = "original_sample_end"
        sample_bounds_valid = all(
            isinstance(row.get(source_support_start), int)
            and isinstance(row.get(source_support_end), int)
            and isinstance(row.get(nominal_support_start), int)
            and isinstance(row.get(nominal_support_end), int)
            and 0 <= row[nominal_support_start] < row[nominal_support_end]
            and 0 <= row[source_support_start] <= row[nominal_support_start]
            and row[source_support_start] < row[source_support_end] <= row[nominal_support_end]
            for row in h5_extents
        )
        chart_shapes = {
            name: list(h5[name].shape)
            for name in (
                "coords_3d_cohort_anchored/values",
                "coords_9d_cohort_anchored/values",
                "time",
                "window_start",
                "window_end",
                "epoch_id",
            )
            if name in h5
        }
        h5_support_summary = {
            "schema": _text_scalar(support_group["schema"]),
            "status": _text_scalar(support_group["status"]),
            "temporal_support_status": _text_scalar(support_group["temporal_support_status"]),
            "temporal_support_reason": _text_scalar(support_group["temporal_support_reason"]),
            "extent_records": len(h5_extents),
            "quality_interval_records": len(h5_quality_intervals),
            "support_status_counts": {},
            "sample_mapping_status_counts": {},
            "execution_record_validation": [],
            "sample_bounds_valid": sample_bounds_valid,
            "candidate_epoch_ids_match_h5": set(candidate_clocks) == h5_epoch_ids,
            "h5_epoch_ids_unique": len(h5_epoch_ids) == len(h5_epoch_values),
            "candidate_epoch_ids_match_h5_support": set(candidate_clocks) == set(h5_clocks),
            "candidate_rows_match_h5_support_count": len(frame) == len(h5_extents),
            "helper_to_h5_epoch_clocks_match": set(helper_clocks) == set(h5_clocks)
            and all(
                abs(helper_clocks[key][0] - h5_clocks[key][0]) <= 1e-9
                and abs(helper_clocks[key][1] - h5_clocks[key][1]) <= 1e-9
                for key in helper_clocks
            ),
            "candidate_to_h5_nominal_clocks_match": set(candidate_clocks) == set(h5_clocks)
            and all(
                abs(candidate_clocks[key][0] - h5_clocks[key][0]) <= 1e-9
                and abs(candidate_clocks[key][1] - h5_clocks[key][1]) <= 1e-9
                for key in candidate_clocks
            ),
            "chart_shapes": chart_shapes,
            "chart_value_arrays_read": False,
        }
        for row in h5_extents:
            key = str(row.get("support_status"))
            h5_support_summary["support_status_counts"][key] = h5_support_summary["support_status_counts"].get(key, 0) + 1
            key = str(row.get("sample_mapping_status"))
            h5_support_summary["sample_mapping_status_counts"][key] = h5_support_summary["sample_mapping_status_counts"].get(key, 0) + 1

        # Only extract the execution-record validation and source identity hash.
        executions = json.loads(_text_scalar(support_group["execution_records_json"]))
        h5_support_summary["execution_record_validation"] = [
            {
                "raw_file": item.get("raw_file"),
                "validation_status": item.get("validation_status"),
                "source_sha256": item.get("record", {}).get("source", {}).get("sha256"),
            }
            for item in executions
        ]
        h5_support_summary["execution_source_hashes_match_fold_manifest"] = all(
            str(item.get("record", {}).get("source", {}).get("sha256", "")).lower()
            == str(fold["source_file_sha256"].get(Path(str(item.get("raw_file", ""))).name, "")).lower()
            for item in executions
        )

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    run_support = manifest.get("extra", {}).get("signal_support_provenance", {})
    h5_support_bound = (
        sidecar_valid
        and payload.get("status") == "recorded"
        and h5_support_summary["status"] == "recorded"
        and h5_support_summary["temporal_support_status"] == "finite_causal_conservative_bound"
        and h5_support_summary["sample_bounds_valid"]
        and h5_support_summary["execution_source_hashes_match_fold_manifest"]
        and h5_support_summary["candidate_rows_match_h5_support_count"]
        and h5_support_summary["candidate_epoch_ids_match_h5"]
        and h5_support_summary["h5_epoch_ids_unique"]
        and h5_support_summary["candidate_epoch_ids_match_h5_support"]
        and h5_support_summary["helper_to_h5_epoch_clocks_match"]
        and h5_support_summary["candidate_to_h5_nominal_clocks_match"]
    )
    validation = {
        "schema_version": "boas.c1_c2_support_sidecar_export_binding_audit.v3",
        "status": "h5_support_bound" if h5_support_bound else "partial",
        "scope": "Outcome-blind H5 provenance audit. Reads support/QC columns, H5 identity/provenance metadata, and dataset shapes; does not read chart coordinate arrays or calculate scores/effects.",
        "mndm_revision": "53bae391015a5bad51b8013c312745a8d90e52f5",
        "mndm_export_helper_sha256": sha256(CLEAN_CHECKOUT / "mndm" / "src" / "mndm" / "pipeline" / "signal_support_export.py"),
        "input_manifest_sha256": sha256(manifest_path),
        "input_feature_table_sha256": sha256(feature_path),
        "apply_subject_id": SUBJECT_ID,
        "apply_raw_file": raw_file,
        "apply_rows": int(len(frame)),
        "sidecar_sha256": sha256(sidecar_path),
        "sidecar_validation": {"valid": sidecar_valid, "reason": sidecar_reason},
        "source_hash_matches_fold_manifest": bool(actual_hash and actual_hash == expected_hash),
        "source_hash": actual_hash,
        "fold_manifest_source_hash": expected_hash,
        "helper_payload_status": payload.get("status"),
        "helper_temporal_support_status": payload.get("temporal_support_status"),
        "helper_temporal_support_reason": payload.get("temporal_support_reason"),
        "epoch_extent_records": len(extents),
        "finite_causal_bounded_rows": sum(row.get("support_status") == "finite_causal_conservative_bound" for row in extents),
        "nominally_mapped_rows": sum(row.get("sample_mapping_status") == "nominal_bounds_mapped" for row in extents),
        "source_hash_bound_rows": sum(str(row.get("source_file_sha256", "")).lower() == actual_hash for row in extents),
        "source_quality_interval_records": len(source_quality_intervals),
        "source_quality_overlap_records": sum(len(row.get("source_quality_overlap", [])) for row in extents),
        "full_execution_record_validation": execution_record.get("validation_status"),
        "raw_flatline_status_in_full_execution_record": flatline.get("status") if isinstance(flatline, dict) else None,
        "raw_flatline_interval_records_in_full_execution_record": len(flatline_intervals),
        "raw_flatline_overlap_records_for_selected_rows": len(flatline_overlaps),
        "raw_flatline_overlap_examples": flatline_overlaps[:10],
        "h5_path": str(h5_path),
        "h5_support_provenance": h5_support_summary,
        "h5_support_quality_overlap_records": sum(len(row.get("source_quality_overlap", [])) for row in h5_extents),
        "top_level_run_manifest_temporal_support_status": run_support.get("temporal_support_status"),
        "h5_binary_written_or_verified": True,
        "scores_or_effects_calculated": False,
    }
    output_path = input_root / "control" / "sidecar_export_binding_audit.json"
    output_path.write_text(json.dumps(validation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(validation, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
