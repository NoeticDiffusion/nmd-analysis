"""Metadata-only scan of selected apply-H5 rows against recorded raw QC intervals.

This audit reads allow-listed source-support CSV columns, QC sidecar metadata,
and the previously validated outcome-blind H5 identity/time map. It never
indexes chart coordinates or feature matrices and never reads stage/outcome
columns.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


ARTICLE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ARTICLE = ARTICLE_ROOT.parent / "BOAS_sleep_dataset_ndt._v.1.0"
CHART_ROOT = SOURCE_ARTICLE / "results" / "fold_safe_chart_qualification_20260930_v1" / "processed" / "ds005555"
CHART_MAP_PATH = SOURCE_ARTICLE / "results" / "fold_safe_chart_qualification_20260930_v1" / "support_map_all_folds_v3" / "all_fold_apply_chart_support_map.parquet"
CHART_MAP_VALIDATION_PATH = CHART_MAP_PATH.parent / "validation.json"
SUPPORT_AUDIT_PATH = SOURCE_ARTICLE / "results" / "continuous_full_surface_support_audit_20260929_v4" / "row_support_audit.csv"
PREFLIGHT_ROOT = ARTICLE_ROOT / "results" / "c1_outcome_blind_preflight_20260930_v1"
INVENTORY_PATH = PREFLIGHT_ROOT / "selected_h5_inventory.csv"
PREFLIGHT_VALIDATION_PATH = PREFLIGHT_ROOT / "validation.json"
QC_ROOT = Path(r"K:\processed\ds005555_continuous_c123_prediction_safe_full_cohort_features_20260929\ds005555\qc_artifacts")
RAW_EDF_ROOT = Path(r"K:\ExternalReceivedDatasets\openneuro\received\ds005555")
OUTPUT_ROOT = ARTICLE_ROOT / "results" / "full_surface_quality_overlap_audit_20261001_v2"

SUPPORT_COLUMNS = [
    "file", "bids_subject", "pid", "epoch_id", "t_start", "t_end",
    "source_stratum", "primary_surface_eligible", "support_exclusion_reasons", "segment_id", "source_sha256",
    "source_sample_mapping_status",
    "actual_sample_contributors_status", "actual_source_time_start_sec",
    "actual_source_time_end_sec", "input_sample_finite_status",
    "input_sample_gap_count", "qc_ok_eeg", "qc_ok_ppg",
]
INVENTORY_COLUMNS = [
    "fold", "fold_role", "bids_subject", "pid", "file", "h5_relative_path",
    "manifest_source_sha256",
]
HORIZONS = {"h1": 1, "h2": 2, "h4": 4}
HISTORY_ROWS = 2
WINDOW_SECONDS = 30.0
TIME_TOLERANCE_SECONDS = 1e-6


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def basename(value: Any) -> str:
    return Path(str(value).replace("\\", "/")).name


def truth(value: Any) -> bool:
    if value is None or pd.isna(value):
        return False
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    return str(value).strip().casefold() in {"true", "1", "yes"}


def qualify_source_rows(frame: pd.DataFrame) -> pd.Series:
    no_reason = frame["support_exclusion_reasons"].fillna("").astype(str).str.strip().eq("")
    return (
        frame["primary_surface_eligible"].map(truth)
        & frame["source_stratum"].astype(str).eq("pure_ppg")
        & frame["source_sample_mapping_status"].astype(str).eq("nominal_bounds_mapped")
        & frame["actual_sample_contributors_status"].astype(str).eq("finite_causal_conservative_bound")
        & frame["input_sample_finite_status"].astype(str).eq("all_finite")
        & pd.to_numeric(frame["input_sample_gap_count"], errors="coerce").eq(0)
        & frame["qc_ok_eeg"].map(truth)
        & frame["qc_ok_ppg"].map(truth)
        & no_reason
    )


def assess_quality_aware_paths(rows: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Compare prior preflight counts with full protocol path eligibility."""
    ordered = rows.sort_values("epoch_id", kind="stable")
    by_epoch = {int(row.epoch_id): row for row in ordered.itertuples(index=False)}
    require(len(by_epoch) == len(ordered), "Duplicate apply chart-map epochs in path audit")
    path_summaries: list[dict[str, Any]] = []
    affected_paths: list[dict[str, Any]] = []
    for dimension, chart_col in (("3d", "chart_valid_3d"), ("9d", "chart_valid_9d")):
        for horizon, lag in HORIZONS.items():
            candidate_count = preflight_eligible = protocol_eligible = quality_affected = 0
            missing_path = intervening_chart_qc_exclusions = invalid_support_bound_exclusions = 0
            for origin_id in sorted(epoch for epoch in by_epoch if epoch >= HISTORY_ROWS):
                candidate_count += 1
                target_id = origin_id + lag
                dependency_ids = list(range(origin_id - HISTORY_ROWS, target_id + 1))
                path = [by_epoch.get(epoch) for epoch in dependency_ids]
                if any(row is None for row in path):
                    missing_path += 1
                    continue
                concrete = [row for row in path if row is not None]
                origin, target = by_epoch[origin_id], by_epoch[target_id]
                segments = [row.segment_id for row in concrete]
                same_segment = all(pd.notna(segment) for segment in segments) and len({str(x) for x in segments}) == 1
                starts = np.asarray([row.chart_window_start_sec for row in concrete], dtype=float)
                ends = np.asarray([row.chart_window_end_sec for row in concrete], dtype=float)
                finite_times = np.isfinite(starts).all() and np.isfinite(ends).all()
                if finite_times:
                    lengths_ok = np.isclose(ends - starts, WINDOW_SECONDS, rtol=0.0, atol=TIME_TOLERANCE_SECONDS).all()
                    edges_ok = np.isclose(ends[:-1], starts[1:], rtol=0.0, atol=TIME_TOLERANCE_SECONDS).all()
                else:
                    lengths_ok = edges_ok = False
                time_ok = bool(same_segment and finite_times and lengths_ok and edges_ok)
                source_ok = all(bool(row.source_support_eligible) for row in concrete)
                predictors_ok = all(bool(getattr(row, chart_col)) for row in concrete[:HISTORY_ROWS + 1])
                target_ok = bool(getattr(target, chart_col))
                actual_horizon = float(target.chart_time_center_sec) - float(origin.chart_time_center_sec)
                horizon_ok = np.isfinite(actual_horizon) and actual_horizon > 0 and np.isclose(
                    actual_horizon, lag * WINDOW_SECONDS, rtol=0.0, atol=TIME_TOLERANCE_SECONDS
                )
                if not (time_ok and source_ok and predictors_ok and target_ok and bool(horizon_ok)):
                    continue
                preflight_eligible += 1
                all_dependency_chart_rows_valid = all(bool(getattr(row, chart_col)) for row in concrete)
                all_dependency_support_bounds_valid = all(bool(row.source_bounds_valid) for row in concrete)
                if not all_dependency_chart_rows_valid:
                    intervening_chart_qc_exclusions += 1
                if not all_dependency_support_bounds_valid:
                    invalid_support_bound_exclusions += 1
                if not (all_dependency_chart_rows_valid and all_dependency_support_bounds_valid):
                    continue
                protocol_eligible += 1
                affected_epoch_ids = [int(row.epoch_id) for row in concrete if bool(row.quality_interval_overlap)]
                if affected_epoch_ids:
                    quality_affected += 1
                    affected_paths.append({
                        "fold": int(origin.fold), "pid": int(origin.pid), "file": str(origin.file),
                        "dimension": dimension, "horizon": horizon,
                        "origin_epoch_id": origin_id, "target_epoch_id": target_id,
                        "dependency_epoch_ids": ";".join(str(value) for value in dependency_ids),
                        "quality_overlap_dependency_epoch_ids": ";".join(str(value) for value in affected_epoch_ids),
                        "actual_origin_to_target_seconds": actual_horizon,
                    })
            path_summaries.append({
                "dimension": dimension, "horizon": horizon, "lag_rows": lag,
                "candidate_origins": candidate_count, "missing_dependency_paths": missing_path,
                "preflight_baseline_eligible_paths": preflight_eligible,
                "protocol_excluded_for_intervening_chart_qc_paths": intervening_chart_qc_exclusions,
                "protocol_excluded_for_invalid_support_bound_paths": invalid_support_bound_exclusions,
                "protocol_eligible_paths": protocol_eligible,
                "protocol_eligible_paths_with_quality_interval_dependency": quality_affected,
                "quality_aware_protocol_eligible_paths": protocol_eligible - quality_affected,
            })
    return path_summaries, affected_paths


def interval_collection(
    container: Any, *, name: str, expected_source_path: str
) -> tuple[list[tuple[float, float, str]], dict[str, Any]]:
    if not isinstance(container, dict):
        return [], {"valid": False, "status": "missing_or_malformed", "interval_count": None, "invalid_count": None, "clock_match": False, "source_path_match": False}
    status = container.get("status")
    intervals = container.get("intervals")
    if not isinstance(intervals, list) or status not in {"observed", "none_observed"}:
        return [], {"valid": False, "status": str(status), "interval_count": None, "invalid_count": None, "clock_match": False, "source_path_match": False}
    declared = container.get("interval_count")
    if declared is not None and int(declared) != len(intervals):
        return [], {"valid": False, "status": str(status), "interval_count": len(intervals), "invalid_count": len(intervals), "clock_match": False, "source_path_match": False}
    if (status == "observed") != bool(intervals):
        return [], {"valid": False, "status": str(status), "interval_count": len(intervals), "invalid_count": len(intervals), "clock_match": False, "source_path_match": False}
    bounds: list[tuple[float, float, str]] = []
    invalid = 0
    expected_path = expected_source_path.replace("/", "\\").casefold()
    declared_clock = container.get("clock")
    clocks = [item.get("clock") for item in intervals if isinstance(item, dict)]
    # Source-quality metadata declares its clock and EDF at collection level.
    # Flatline metadata declares them on each observed interval. Missing provenance
    # must fail closed instead of being accepted as a matching value.
    clock_match = (
        (name != "source_quality" or declared_clock == "original_raw_seconds")
        and all(clock == "original_raw_seconds" for clock in clocks)
    )
    declared_raw_file = container.get("raw_file")
    source_path_match = (
        (name != "source_quality" or (
            declared_raw_file is not None
            and str(declared_raw_file).replace("/", "\\").casefold() == expected_path
        ))
        and all(
            isinstance(item, dict)
            and item.get("raw_file") is not None
            and str(item["raw_file"]).replace("/", "\\").casefold() == expected_path
            for item in intervals
        )
    )
    for item in intervals:
        try:
            if not isinstance(item, dict):
                raise TypeError("interval is not a mapping")
            start, end = float(item["start_sec"]), float(item["end_sec"])
            kind = str(item.get("source_kind", name))
        except (TypeError, KeyError, ValueError):
            invalid += 1
            continue
        if not np.isfinite([start, end]).all() or end <= start:
            invalid += 1
            continue
        bounds.append((start, end, kind))
    valid = invalid == 0 and len(bounds) == len(intervals) and clock_match and source_path_match
    return bounds, {
        "valid": valid, "status": str(status), "interval_count": len(intervals), "invalid_count": invalid,
        "clock_match": bool(clock_match), "source_path_match": bool(source_path_match),
    }


def main() -> int:
    for path in (SUPPORT_AUDIT_PATH, INVENTORY_PATH, PREFLIGHT_VALIDATION_PATH, QC_ROOT, CHART_MAP_PATH, CHART_MAP_VALIDATION_PATH):
        require(path.exists(), f"Required audit input missing: {path}")
    preflight = json.loads(PREFLIGHT_VALIDATION_PATH.read_text(encoding="utf-8"))
    require(preflight.get("measurement_boundary", {}).get("future_chart_numeric_values_read") is False,
            "Referenced outcome-blind preflight no longer records the expected scope")
    require(preflight.get("selected_surface", {}).get("selected_h5_files") == 500,
            "Referenced H5 selection changed from 500 files")
    chart_map_validation = json.loads(CHART_MAP_VALIDATION_PATH.read_text(encoding="utf-8"))
    require(chart_map_validation.get("schema_version") == "boas.all_fold_apply_chart_support_map.v2",
            "Unexpected all-fold apply chart-map schema")
    require(chart_map_validation.get("label_join_performed") is False
            and chart_map_validation.get("stage_horizon_intersection_computed") is False,
            "Referenced chart map is not outcome-blind")
    chart_map_sha256 = sha256_file(CHART_MAP_PATH)
    require(chart_map_validation.get("output_parquet_sha256") == chart_map_sha256,
            "Chart-map parquet digest does not match its validation record")
    support = pd.read_csv(
        SUPPORT_AUDIT_PATH,
        usecols=SUPPORT_COLUMNS,
        dtype={name: "string" for name in ("file", "bids_subject", "source_stratum", "support_exclusion_reasons", "segment_id", "source_sha256", "source_sample_mapping_status", "actual_sample_contributors_status", "input_sample_finite_status")},
        low_memory=False,
    )
    inventory = pd.read_csv(
        INVENTORY_PATH,
        usecols=INVENTORY_COLUMNS,
        dtype={name: "string" for name in ("fold_role", "bids_subject", "file", "h5_relative_path", "manifest_source_sha256")},
    )
    support["file"] = support["file"].map(basename)
    support["epoch_id"] = pd.to_numeric(support["epoch_id"], errors="raise").astype(np.int64)
    support["pid"] = pd.to_numeric(support["pid"], errors="raise").astype(np.int64)
    for column in ("t_start", "t_end", "actual_source_time_start_sec", "actual_source_time_end_sec", "input_sample_gap_count"):
        support[column] = pd.to_numeric(support[column], errors="coerce")
    support["support_source_eligible"] = qualify_source_rows(support)
    require(not support.duplicated(["file", "epoch_id"]).any(), "Duplicate source-support row identities")
    apply_inventory = inventory.loc[inventory["fold_role"].eq("apply")].copy()
    require(len(apply_inventory) == 100 and not apply_inventory["file"].duplicated().any(),
            f"Expected 100 unique apply recordings; found {len(apply_inventory)}")
    chart_columns = [
        "fold", "fold_role", "subject", "bids_subject", "file", "epoch_id",
        "chart_window_start_sec", "chart_window_end_sec", "chart_time_center_sec",
        "chart_mnps_3d_valid", "chart_coords_9d_valid", "chart_geometry_valid", "chart_retained_after_qc",
        "audit_primary_surface_eligible", "expected_source_sha256",
        "source_hashes_match_fold_manifest", "chart_h5_relative_path",
    ]
    chart_rows = pq.read_table(CHART_MAP_PATH, columns=chart_columns).to_pandas()
    chart_rows = chart_rows.loc[chart_rows["fold_role"].eq("apply")].copy()
    chart_rows["file"] = chart_rows["file"].map(basename)
    chart_rows["epoch_id"] = pd.to_numeric(chart_rows["epoch_id"], errors="raise").astype(np.int64)
    chart_rows["fold"] = pd.to_numeric(chart_rows["fold"], errors="raise").astype(np.int64)
    chart_rows["chart_valid_3d"] = (
        chart_rows["chart_mnps_3d_valid"].map(truth)
        & chart_rows["chart_geometry_valid"].map(truth)
        & chart_rows["chart_retained_after_qc"].map(truth)
    )
    chart_rows["chart_valid_9d"] = (
        chart_rows["chart_coords_9d_valid"].map(truth)
        & chart_rows["chart_geometry_valid"].map(truth)
        & chart_rows["chart_retained_after_qc"].map(truth)
    )
    require(not chart_rows.duplicated(["fold", "file", "epoch_id"]).any(), "Duplicate apply chart-map row identities")
    require(set(chart_rows["file"].astype(str)) == set(apply_inventory["file"].map(basename).astype(str)),
            "Apply chart-map recording set differs from the selected-H5 inventory")

    recording_rows: list[dict[str, Any]] = []
    overlap_rows: list[dict[str, Any]] = []
    chart_map_metadata_digest = hashlib.sha256()
    sidecar_digest = hashlib.sha256()
    total_h5_rows = 0
    all_hashes_match = True
    all_source_paths_match = True
    all_row_joins_pass = True
    all_interval_maps_valid = True
    all_h5_support_bounds_valid = True
    support_projection = hashlib.sha256()
    per_recording_path_summaries: list[dict[str, Any]] = []
    affected_path_rows: list[dict[str, Any]] = []
    invalid_support_bound_rows: list[dict[str, Any]] = []

    for item in apply_inventory.sort_values(["fold", "file"], kind="stable").itertuples(index=False):
        raw_file = basename(item.file)
        file_support = support.loc[support["file"].eq(raw_file)].sort_values("epoch_id", kind="stable").copy()
        require(not file_support.empty, f"Source-support audit has no rows for {raw_file}")
        support_hashes = sorted(set(file_support["source_sha256"].dropna().astype(str)))
        require(len(support_hashes) == 1, f"Source-support audit has inconsistent source hashes for {raw_file}")

        qc_path = QC_ROOT / f"{Path(raw_file).stem}_qc_artifacts.json"
        qc = json.loads(qc_path.read_text(encoding="utf-8")) if qc_path.is_file() else {}
        provenance = qc.get("signal_support_provenance", {})
        source = provenance.get("source", {})
        source_hash = source.get("sha256")
        source_subject = raw_file.split("_task-", maxsplit=1)[0]
        expected_source_path = str(RAW_EDF_ROOT / source_subject / "eeg" / raw_file)
        source_path_match = str(source.get("path", "")).replace("/", "\\").casefold() == expected_source_path.replace("/", "\\").casefold()
        all_source_paths_match &= bool(source_path_match)
        source_hash_match = (
            source_hash == support_hashes[0] == str(item.manifest_source_sha256)
            and source.get("hash_stable") is True
            and source.get("sha256_after") == source_hash
        )
        all_hashes_match &= bool(source_hash_match)
        if qc_path.is_file():
            sidecar_digest.update(raw_file.encode() + b"\0" + bytes.fromhex(sha256_file(qc_path)))

        support_intervals, source_interval_check = interval_collection(
            provenance.get("source_quality_intervals"), name="source_quality", expected_source_path=expected_source_path
        )
        flatline_qc = provenance.get("raw_joint_eeg_flatline_qc")
        flatline_intervals, flatline_interval_check = interval_collection(
            flatline_qc, name="raw_joint_eeg_flatline", expected_source_path=expected_source_path
        )
        intervals = support_intervals + flatline_intervals
        interval_checks_valid = source_interval_check["valid"] and flatline_interval_check["valid"] and source_path_match
        policy_count = qc.get("quality_interval_policy", {}).get("selected_source_interval_count")
        policy_count_match = policy_count is not None and int(policy_count) == len(intervals)
        interval_checks_valid &= bool(policy_count_match)
        all_interval_maps_valid &= bool(interval_checks_valid)

        h5_path = CHART_ROOT / str(item.h5_relative_path)
        require(h5_path.is_file(), f"Selected apply H5 is missing: {h5_path}")
        h5_rows = chart_rows.loc[
            chart_rows["file"].eq(raw_file) & chart_rows["fold"].eq(int(item.fold))
        ].copy().sort_values("epoch_id", kind="stable")
        require(not h5_rows.empty, f"Outcome-blind chart map has no apply rows for {raw_file}")
        identity_match = (
            h5_rows["bids_subject"].astype(str).eq(str(item.bids_subject)).all()
            and h5_rows["subject"].astype(str).eq(f"sub-{int(item.pid):03d}").all()
        )
        raw_match = bool(h5_rows["file"].eq(raw_file).all())
        inventory_suffix = str(item.h5_relative_path).replace("\\", "/")
        h5_path_match = bool(h5_rows["chart_h5_relative_path"].astype(str).str.replace("\\", "/", regex=False).str.endswith(inventory_suffix).all())
        joined = h5_rows.merge(file_support, on=["file", "epoch_id"], how="left", validate="one_to_one", sort=True)
        keys_joined = joined["source_sha256"].notna()
        h5_keys = set(zip(h5_rows["file"].astype(str), h5_rows["epoch_id"].astype(int)))
        eligible_mask = file_support["primary_surface_eligible"].map(truth)
        eligible_keys = set(zip(file_support.loc[eligible_mask, "file"].astype(str), file_support.loc[eligible_mask, "epoch_id"].astype(int)))
        key_set_match = h5_keys == eligible_keys
        support_key_match = bool(keys_joined.all()) and key_set_match
        starts = joined["actual_source_time_start_sec"].to_numpy(dtype=float)
        ends = joined["actual_source_time_end_sec"].to_numpy(dtype=float)
        support_bounds_valid = np.isfinite(starts) & np.isfinite(ends) & (ends > starts)
        all_h5_support_bounds_valid &= bool(support_bounds_valid.all())
        joined["source_bounds_valid"] = support_bounds_valid
        for index in np.flatnonzero(~support_bounds_valid):
            invalid_support_bound_rows.append({
                "fold": int(item.fold), "pid": int(item.pid), "file": raw_file,
                "epoch_id": int(joined.iloc[index]["epoch_id"]),
                "actual_source_time_start_sec": starts[index] if np.isfinite(starts[index]) else None,
                "actual_source_time_end_sec": ends[index] if np.isfinite(ends[index]) else None,
                "reason": "nonfinite_or_nonpositive_contributor_bound",
            })
        eligible_joined = joined["primary_surface_eligible"].map(truth).to_numpy()
        observed_time_start = pd.to_numeric(joined["t_start"], errors="coerce").to_numpy(dtype=float)
        observed_time_end = pd.to_numeric(joined["t_end"], errors="coerce").to_numpy(dtype=float)
        time_bounds_match = (
            np.isfinite(observed_time_start).all()
            and np.isfinite(observed_time_end).all()
            and np.all(np.abs(joined["chart_window_start_sec"].to_numpy(dtype=float) - observed_time_start) <= 1e-9)
            and np.all(np.abs(joined["chart_window_end_sec"].to_numpy(dtype=float) - observed_time_end) <= 1e-9)
        )
        manifest_hash_match = bool(
            h5_rows["expected_source_sha256"].astype(str).eq(str(item.manifest_source_sha256)).all()
            and h5_rows["source_hashes_match_fold_manifest"].map(truth).all()
        )
        all_row_joins_pass &= bool(identity_match and raw_match and h5_path_match and support_key_match and time_bounds_match and manifest_hash_match)

        for row in joined[["file", "epoch_id", "pid", "t_start", "t_end", "actual_source_time_start_sec", "actual_source_time_end_sec", "primary_surface_eligible", "source_sha256"]].itertuples(index=False, name=None):
            payload = json.dumps([str(v) if pd.notna(v) else None for v in row], separators=(",", ":")).encode("utf-8")
            support_projection.update(payload + b"\n")

        interval_row_hits = Counter()
        interval_rows_by_kind: dict[str, set[int]] = {}
        # Invalid contributor bounds fail closed above; they are never silently
        # treated as non-overlapping with an interval.
        intervals_valid_row_times = support_bounds_valid
        for q_start, q_end, kind in intervals:
            mask = intervals_valid_row_times & (starts < q_end) & (q_start < ends)
            interval_row_hits[kind] += int(mask.sum())
            interval_rows_by_kind.setdefault(kind, set()).update(np.flatnonzero(mask).tolist())
        any_overlap = np.zeros(len(joined), dtype=bool)
        for q_start, q_end, _ in intervals:
            any_overlap |= intervals_valid_row_times & (starts < q_end) & (q_start < ends)
        joined["source_support_eligible"] = joined["support_source_eligible"].map(truth)
        joined["quality_interval_overlap"] = any_overlap
        recording_path_summary, recording_affected_paths = assess_quality_aware_paths(joined)
        for summary_row in recording_path_summary:
            per_recording_path_summaries.append({
                "fold": int(item.fold), "pid": int(item.pid), "file": raw_file, **summary_row,
            })
        affected_path_rows.extend(recording_affected_paths)
        overlap_indices = np.flatnonzero(any_overlap)
        for index in overlap_indices:
            matching_intervals = [
                {"source_kind": kind, "start_sec": q_start, "end_sec": q_end}
                for q_start, q_end, kind in intervals
                if starts[index] < q_end and q_start < ends[index]
            ]
            overlap_rows.append({
                "fold": int(item.fold), "pid": int(item.pid), "bids_subject": str(item.bids_subject),
                "file": raw_file, "epoch_id": int(joined.iloc[index]["epoch_id"]),
                "actual_source_time_start_sec": float(starts[index]),
                "actual_source_time_end_sec": float(ends[index]),
                "support_primary_surface_eligible": bool(eligible_joined[index]),
                "included_in_apply_h5": True,
                "quality_kinds": ";".join(sorted(kind for kind, indices in interval_rows_by_kind.items() if index in indices)),
                "overlapping_quality_interval_bounds": json.dumps(matching_intervals, sort_keys=True),
            })

        chart_map_metadata_digest.update(str(item.h5_relative_path).encode() + b"\0")
        for values, dtype in ((joined["epoch_id"].to_numpy(), "<i8"), (joined["chart_time_center_sec"].to_numpy(), "<f8"),
                              (joined["chart_window_start_sec"].to_numpy(), "<f8"), (joined["chart_window_end_sec"].to_numpy(), "<f8")):
            chart_map_metadata_digest.update(np.asarray(values, dtype=dtype).tobytes())
        total_h5_rows += len(h5_rows)
        recording_rows.append({
            "fold": int(item.fold), "pid": int(item.pid), "bids_subject": str(item.bids_subject), "file": raw_file,
            "h5_relative_path": str(item.h5_relative_path), "h5_rows": int(len(h5_rows)),
            "support_rows": int(len(file_support)), "support_primary_eligible_rows": int(eligible_mask.sum()),
            "source_hash_match": bool(source_hash_match), "h5_identity_matches_inventory": bool(identity_match),
            "source_path_matches_expected_edf": bool(source_path_match),
            "h5_raw_file_identity_matches": bool(raw_match), "h5_path_matches_inventory": bool(h5_path_match),
            "h5_keys_equal_primary_eligible_support_keys": bool(key_set_match),
            "h5_source_hash_matches_fold_manifest": bool(manifest_hash_match),
            "h5_window_bounds_match_support_rows": bool(time_bounds_match),
            "h5_contributor_bounds_valid_rows": int(support_bounds_valid.sum()),
            "h5_contributor_bounds_invalid_rows": int((~support_bounds_valid).sum()),
            "source_quality_interval_count": int(source_interval_check["interval_count"] or 0),
            "raw_flatline_interval_count": int(flatline_interval_check["interval_count"] or 0),
            "selected_quality_interval_count": int(policy_count or 0), "quality_interval_map_valid": bool(interval_checks_valid),
            "quality_overlap_apply_h5_rows": int(any_overlap.sum()),
            "quality_overlap_primary_eligible_h5_rows": int((any_overlap & eligible_joined).sum()),
            "quality_overlap_apply_h5_rows_by_kind": json.dumps({kind: len(indices) for kind, indices in sorted(interval_rows_by_kind.items())}, sort_keys=True),
            "quality_interval_row_hits_by_kind": json.dumps(dict(sorted(interval_row_hits.items())), sort_keys=True),
            "quality_interval_source_status": source_interval_check["status"],
            "raw_flatline_interval_source_status": flatline_interval_check["status"],
            "support_schema": provenance.get("schema"), "support_status": provenance.get("status"),
            "effective_support_status": provenance.get("effective_time_support", {}).get("status"),
            "effective_support_mode": provenance.get("effective_time_support", {}).get("mode"),
            "qc_sidecar_path": str(qc_path), "qc_sidecar_sha256": sha256_file(qc_path) if qc_path.is_file() else None,
        })

    recording_frame = pd.DataFrame(recording_rows).sort_values(["fold", "pid", "file"], kind="stable")
    overlap_frame = pd.DataFrame(overlap_rows, columns=[
        "fold", "pid", "bids_subject", "file", "epoch_id", "actual_source_time_start_sec",
        "actual_source_time_end_sec", "support_primary_surface_eligible", "included_in_apply_h5", "quality_kinds",
        "overlapping_quality_interval_bounds",
    ]).sort_values(["fold", "pid", "file", "epoch_id"], kind="stable")
    path_by_recording = pd.DataFrame(per_recording_path_summaries)
    path_by_fold = path_by_recording.groupby(["fold", "dimension", "horizon"], as_index=False, sort=True)[
            ["candidate_origins", "missing_dependency_paths", "preflight_baseline_eligible_paths",
         "protocol_excluded_for_intervening_chart_qc_paths", "protocol_excluded_for_invalid_support_bound_paths",
         "protocol_eligible_paths", "protocol_eligible_paths_with_quality_interval_dependency",
         "quality_aware_protocol_eligible_paths"]
    ].sum()
    previous_support_path = PREFLIGHT_ROOT / "c1_path_support_summary.csv"
    previous_support = pd.read_csv(
        previous_support_path,
        usecols=["fold", "fold_role", "dimension", "horizon", "outcome_blind_eligible_paths"],
    )
    previous_apply = previous_support.loc[previous_support["fold_role"].eq("apply")].copy()
    path_by_fold = path_by_fold.merge(
        previous_apply,
        on=["fold", "dimension", "horizon"],
        how="left",
        validate="one_to_one",
    ).rename(columns={"outcome_blind_eligible_paths": "prior_preflight_eligible_paths"})
    path_by_fold["preflight_baseline_count_matches_prior"] = (
        path_by_fold["preflight_baseline_eligible_paths"] == path_by_fold["prior_preflight_eligible_paths"]
    )
    path_counts_reconstruct_preflight = bool(path_by_fold["preflight_baseline_count_matches_prior"].all())
    affected_path_frame = pd.DataFrame(affected_path_rows, columns=[
        "fold", "pid", "file", "dimension", "horizon", "origin_epoch_id", "target_epoch_id",
        "dependency_epoch_ids", "quality_overlap_dependency_epoch_ids", "actual_origin_to_target_seconds",
    ]).sort_values(["fold", "pid", "file", "dimension", "horizon", "origin_epoch_id"], kind="stable")
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    recording_csv = OUTPUT_ROOT / "recording_quality_support_summary.csv"
    overlap_csv = OUTPUT_ROOT / "apply_h5_quality_overlap_rows.csv"
    path_summary_csv = OUTPUT_ROOT / "quality_aware_path_support_summary.csv"
    affected_paths_csv = OUTPUT_ROOT / "quality_affected_forecast_paths.csv"
    invalid_support_bounds_csv = OUTPUT_ROOT / "invalid_h5_contributor_bounds.csv"
    recording_frame.to_csv(recording_csv, index=False)
    overlap_frame.to_csv(overlap_csv, index=False)
    path_by_fold.to_csv(path_summary_csv, index=False)
    affected_path_frame.to_csv(affected_paths_csv, index=False)
    pd.DataFrame(invalid_support_bound_rows, columns=[
        "fold", "pid", "file", "epoch_id", "actual_source_time_start_sec",
        "actual_source_time_end_sec", "reason",
    ]).to_csv(invalid_support_bounds_csv, index=False)
    overlap_counts = recording_frame["quality_overlap_apply_h5_rows"].sum()
    source_ledger_hashes = sorted(set(support.loc[support["file"].isin(apply_inventory["file"].map(basename)), "source_sha256"].dropna().astype(str)))
    validation = {
        "schema_version": "boas.c1_full_surface_quality_overlap_audit.v2",
        "verdict": (
            "INCOMPLETE_INPUT_OR_LINEAGE" if not (all_hashes_match and all_source_paths_match and all_row_joins_pass and all_interval_maps_valid and all_h5_support_bounds_valid and path_counts_reconstruct_preflight)
            else "QUALITY_OVERLAPS_PRESENT_REQUIRE_SUPPORT_REVIEW" if overlap_counts > 0
            else "NO_RECORDED_QUALITY_OVERLAPS_IN_METADATA_SCAN"
        ),
        "scope": "Selected 100 apply-H5 recordings: row identity/time, protocol-complete chart-QC path flags, contributor-bound validity, and raw source-quality interval overlap metadata only; no feature/chart values or outcome scoring.",
        "outcome_boundary": {
            "chart_coordinate_arrays_read": False, "feature_value_arrays_read": False,
            "stage_or_outcome_columns_parsed": False, "future_chart_values_read": False,
            "predictions_or_scores_calculated": False,
        },
        "inputs": {
            "support_audit_path": str(SUPPORT_AUDIT_PATH), "selected_h5_inventory_path": str(INVENTORY_PATH),
            "qc_sidecar_root": str(QC_ROOT), "preflight_validation_sha256": sha256_file(PREFLIGHT_VALIDATION_PATH),
            "apply_h5_files": int(len(apply_inventory)), "apply_recordings": int(len(recording_frame)),
            "apply_h5_row_instances": int(total_h5_rows), "unique_source_hash_count": len(source_ledger_hashes),
            "selected_source_hashes_match_qc_support_and_h5_manifest": bool(all_hashes_match),
            "qc_source_paths_match_expected_raw_edfs": bool(all_source_paths_match),
            "h5_row_identity_support_and_window_join_pass": bool(all_row_joins_pass),
            "quality_interval_maps_complete_and_well_formed": bool(all_interval_maps_valid),
            "all_apply_h5_contributor_bounds_finite_and_ordered": bool(all_h5_support_bounds_valid),
            "prior_preflight_path_counts_reconstructed": path_counts_reconstruct_preflight,
            "support_metadata_projection_sha256": support_projection.hexdigest(),
            "chart_map_identity_time_metadata_sha256": chart_map_metadata_digest.hexdigest(),
            "qc_sidecar_sha256_projection": sidecar_digest.hexdigest(),
            "chart_map_path": str(CHART_MAP_PATH), "chart_map_sha256": chart_map_sha256,
            "chart_map_validation_sha256": sha256_file(CHART_MAP_VALIDATION_PATH),
        },
        "summary": {
            "quality_interval_overlap_h5_rows": int(overlap_counts),
            "invalid_apply_h5_contributor_bound_rows": int(len(invalid_support_bound_rows)),
            "recordings_with_any_quality_overlap": int((recording_frame["quality_overlap_apply_h5_rows"] > 0).sum()),
            "recordings_with_invalid_quality_interval_metadata": int((~recording_frame["quality_interval_map_valid"]).sum()),
            "preflight_primary_c1_3d_h1_paths": int(path_by_fold.loc[path_by_fold["dimension"].eq("3d") & path_by_fold["horizon"].eq("h1"), "preflight_baseline_eligible_paths"].sum()),
            "protocol_primary_c1_3d_h1_paths_before_quality_exclusion": int(path_by_fold.loc[path_by_fold["dimension"].eq("3d") & path_by_fold["horizon"].eq("h1"), "protocol_eligible_paths"].sum()),
            "quality_affected_primary_c1_3d_h1_paths": int(path_by_fold.loc[path_by_fold["dimension"].eq("3d") & path_by_fold["horizon"].eq("h1"), "protocol_eligible_paths_with_quality_interval_dependency"].sum()),
            "quality_aware_primary_c1_3d_h1_paths": int(path_by_fold.loc[path_by_fold["dimension"].eq("3d") & path_by_fold["horizon"].eq("h1"), "quality_aware_protocol_eligible_paths"].sum()),
        },
        "artifacts": {
            "recording_summary_csv": recording_csv.name, "overlap_rows_csv": overlap_csv.name,
            "quality_aware_path_summary_csv": path_summary_csv.name, "quality_affected_forecast_paths_csv": affected_paths_csv.name,
            "invalid_h5_contributor_bounds_csv": invalid_support_bounds_csv.name,
        },
        "interpretation": "Protocol eligibility requires every history, origin, intervening, and target chart row to pass its dimension-specific validity flag, and every row to have finite ordered causal contributor bounds. Recorded QC intervals intersecting any dependency bound exclude the path. This metadata scan is not a producer qualification or scoring authorization.",
    }
    (OUTPUT_ROOT / "validation.json").write_text(json.dumps(validation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": validation["verdict"], "apply_h5_files": int(len(apply_inventory)),
        "apply_h5_row_instances": int(total_h5_rows), "quality_overlap_h5_rows": int(overlap_counts),
        "recordings_with_overlap": validation["summary"]["recordings_with_any_quality_overlap"],
        "recordings_with_invalid_interval_metadata": validation["summary"]["recordings_with_invalid_quality_interval_metadata"],
        "prior_preflight_path_counts_reconstructed": path_counts_reconstruct_preflight,
        "all_apply_h5_contributor_bounds_finite_and_ordered": all_h5_support_bounds_valid,
        "protocol_primary_c1_3d_h1_paths_before_quality_exclusion": validation["summary"]["protocol_primary_c1_3d_h1_paths_before_quality_exclusion"],
        "quality_affected_primary_c1_3d_h1_paths": validation["summary"]["quality_affected_primary_c1_3d_h1_paths"],
        "quality_aware_primary_c1_3d_h1_paths": validation["summary"]["quality_aware_primary_c1_3d_h1_paths"],
        "output_root": str(OUTPUT_ROOT),
    }, indent=2))
    return 0 if all_hashes_match and all_source_paths_match and all_row_joins_pass and all_interval_maps_valid and all_h5_support_bounds_valid and path_counts_reconstruct_preflight else 1


if __name__ == "__main__":
    raise SystemExit(main())
