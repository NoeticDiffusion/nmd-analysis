"""Audit outcome-blind stage-origin and horizon support on five-fold apply charts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


ARTICLE_ROOT = Path(__file__).resolve().parents[1]
RESULTS_ROOT = ARTICLE_ROOT / "results"
CHART_ROOT = RESULTS_ROOT / "fold_safe_chart_qualification_20260930_v1"
MAP_ROOT = CHART_ROOT / "support_map_all_folds_v3"
V4_ROOT = RESULTS_ROOT / "continuous_full_surface_support_audit_20260929_v4"
PROTOCOL_PATH = ARTICLE_ROOT / "preregistration_continuous_C123_20260929.md"
DEFAULT_OUTPUT = CHART_ROOT / "stage_horizon_support_all_folds_v4"

HORIZONS = {"h1": 1, "h2": 2, "h4": 4}
CONTEXTS = {0: "Wake", 2: "N2"}
DIMENSIONS = ("3d", "9d")
KEYS = ["file", "epoch_id"]
MAP_COLUMNS = [
    "fold", "subject", "bids_subject", "file", "epoch_id", "chart_window_start_sec",
    "chart_window_end_sec", "chart_coords_3d_all_finite", "chart_coords_9d_all_finite",
    "chart_geometry_valid", "chart_coords_9d_valid", "chart_mnps_3d_valid",
    "chart_retained_after_qc", "audit_source_stratum", "audit_primary_surface_eligible",
    "audit_base_support_eligible", "audit_support_exclusion_reasons", "recording_source_sha256",
    "expected_source_sha256", "source_hashes_match_fold_manifest",
]
AUDIT_COLUMNS = [
    "file", "subject", "bids_subject", "pid", "epoch_id", "t_start", "t_end",
    "source_stratum", "primary_surface_eligible", "support_exclusion_reasons",
    "source_sha256", "source_sample_mapping_status", "actual_sample_contributors_status",
    "input_sample_finite_status", "input_sample_gap_count",
    "qc_ok_eeg", "qc_ok_ppg", "stage_at_origin_code", "stage_at_origin_status",
    "stage_window_pure", "stage_window_status", "segment_id",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def truth(value: Any) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return value != 0
    return str(value).strip().lower() in {"true", "1", "yes"}


def _support_ok(row: Mapping[str, Any]) -> bool:
    if "_support_eligible_cached" in row:
        return bool(row["_support_eligible_cached"])
    try:
        no_gaps = float(row.get("input_sample_gap_count")) == 0
    except (TypeError, ValueError):
        no_gaps = False
    reasons = row.get("support_exclusion_reasons")
    no_exclusion_reason = pd.isna(reasons) or not str(reasons).strip()
    return bool(
        truth(row.get("primary_surface_eligible"))
        and str(row.get("source_stratum")) == "pure_ppg"
        and str(row.get("source_sample_mapping_status")) == "nominal_bounds_mapped"
        and str(row.get("actual_sample_contributors_status")) == "finite_causal_conservative_bound"
        and str(row.get("input_sample_finite_status")) == "all_finite"
        and no_gaps
        and truth(row.get("qc_ok_eeg"))
        and truth(row.get("qc_ok_ppg"))
        and no_exclusion_reason
    )


def _chart_ok(row: Mapping[str, Any], dimension: str) -> bool:
    cache_key = f"_chart_valid_{dimension}_cached"
    if cache_key in row:
        return bool(row[cache_key])
    valid_key = "chart_mnps_3d_valid" if dimension == "3d" else "chart_coords_9d_valid"
    finite_key = "chart_coords_3d_all_finite" if dimension == "3d" else "chart_coords_9d_all_finite"
    return bool(
        truth(row.get("chart_row_present"))
        and truth(row.get("chart_geometry_valid"))
        and truth(row.get("chart_retained_after_qc"))
        and truth(row.get(finite_key))
        and truth(row.get(valid_key))
    )


def _stage_origin_ok(row: Mapping[str, Any], stage_code: int) -> bool:
    try:
        observed = float(row.get("stage_at_origin_code"))
    except (TypeError, ValueError):
        return False
    return bool(
        truth(row.get("chart_row_present"))
        and _support_ok(row)
        and str(row.get("stage_at_origin_status")) == "unique_source_stage_at_origin"
        and truth(row.get("stage_window_pure"))
        and str(row.get("stage_window_status")) == "stage_pure_at_origin"
        and observed == stage_code
    )


def _time_path_ok(path: list[Mapping[str, Any]], window_sec: float, tolerance_sec: float) -> bool:
    if not path:
        return False
    segment_ids = [row.get("segment_id") for row in path]
    if any(pd.isna(value) for value in segment_ids) or len({str(value) for value in segment_ids}) != 1:
        return False
    if all("_window_time_valid_cached" in row for row in path):
        return all(bool(row["_window_time_valid_cached"]) for row in path) and all(
            bool(row.get("_time_edge_next_valid_cached", False)) for row in path[:-1]
        )
    try:
        starts = [float(row["t_start"]) for row in path]
        ends = [float(row["t_end"]) for row in path]
    except (KeyError, TypeError, ValueError):
        return False
    if not np.isfinite(starts + ends).all():
        return False
    if any(not np.isclose(end - start, window_sec, rtol=0.0, atol=tolerance_sec) for start, end in zip(starts, ends)):
        return False
    return all(np.isclose(left_end, right_start, rtol=0.0, atol=tolerance_sec) for left_end, right_start in zip(ends, starts[1:]))


def _assess_path(
    rows_by_epoch: Mapping[int, Mapping[str, Any]],
    *,
    origin_id: int,
    lag: int,
    dimension: str,
    history_rows: int = 0,
    window_sec: float = 30.0,
    tolerance_sec: float = 1e-6,
) -> dict[str, Any]:
    """Check a fixed row-lag path; never reads future stage fields."""
    target_id = origin_id + lag
    target_present = target_id in rows_by_epoch
    ids = list(range(origin_id - history_rows, target_id + 1))
    path = [rows_by_epoch.get(epoch_id) for epoch_id in ids]
    present = all(row is not None for row in path)
    if not present:
        return {
            "target_present": target_present,
            "required_path_rows_present": False,
            "time_contiguous": False,
            "source_support_path_valid": False,
            "chart_rows_present": False,
            "chart_qc_path_valid": False,
            "pair_eligible": False,
            "failure_reason": "missing_intermediate_or_target_row",
            "actual_horizon_sec": None,
        }

    concrete = [row for row in path if row is not None]
    origin = rows_by_epoch[origin_id]
    target = rows_by_epoch[target_id]
    time_ok = _time_path_ok(concrete, window_sec, tolerance_sec)
    support_ok = all(_support_ok(row) for row in concrete)
    chart_present = all(truth(row.get("chart_row_present")) for row in concrete)
    chart_ok = all(_chart_ok(row, dimension) for row in concrete)
    actual_horizon = float(target["t_end"]) - float(origin["t_end"])
    positive_horizon = np.isfinite(actual_horizon) and actual_horizon > 0
    pair_ok = time_ok and support_ok and chart_present and chart_ok and positive_horizon
    if not time_ok:
        failure = "gap_or_segment_break"
    elif not support_ok:
        failure = "source_support_ineligible_path"
    elif not chart_present:
        failure = "chart_row_unavailable"
    elif not chart_ok:
        failure = "coordinate_or_geometry_qc_invalid"
    elif not positive_horizon:
        failure = "nonpositive_actual_horizon"
    else:
        failure = "eligible"
    return {
        "target_present": target_present,
        "required_path_rows_present": True,
        "time_contiguous": bool(time_ok),
        "source_support_path_valid": bool(support_ok),
        "chart_rows_present": bool(chart_present),
        "chart_qc_path_valid": bool(chart_ok),
        "pair_eligible": bool(pair_ok),
        "failure_reason": failure,
        "actual_horizon_sec": actual_horizon if positive_horizon else None,
    }


def _assert_input_provenance(map_validation: dict[str, Any], surface_validation: dict[str, Any]) -> None:
    require(map_validation.get("schema_version") == "boas.all_fold_apply_chart_support_map.v2", "Unexpected support-map schema")
    require(map_validation.get("label_join_performed") is False, "Expected a stage-blind support map as input")
    require(map_validation.get("stage_horizon_intersection_computed") is False, "Support map already contains a stage/horizon intersection")
    require(map_validation.get("contrasts_computed") is False and map_validation.get("biological_claim_authorized") is False, "Support map has an invalid outcome scope")
    require(surface_validation.get("schema") == "nmd_analysis.continuous_full_surface_audit.v1", "Unexpected V4 full-surface audit schema")
    require(surface_validation.get("status") == "PARTIAL_PASS_SOURCE_SUPPORT_ONLY", "V4 source-support audit status changed")
    require(surface_validation.get("c3_context") == "human-scored N2 versus Wake at forecast origin; frozen preregistration context", "Registered C3 context mismatch")
    require(surface_validation.get("provenance", {}).get("source_stage_column") == "stage_hum", "Human-scored stage source column mismatch")
    require(surface_validation.get("outcomes_calculated") is False and surface_validation.get("full_cohort_scoring_authorized") is False, "V4 audit unexpectedly includes outcomes or authorization")
    before = surface_validation.get("input_hashes_before", {})
    after = surface_validation.get("input_hashes_after", {})
    event_keys = [key for key in before if key.startswith("events:")]
    after_event_keys = [key for key in after if key.startswith("events:")]
    require(set(event_keys) == set(after_event_keys), "V4 event-source key set changed during the full-surface audit")
    require(len(event_keys) == 128, "V4 validation must bind exactly 128 event sources for the frozen full apply surface")
    require(all(before.get(key) == after.get(key) for key in event_keys), "A human-scored event source changed during the V4 audit")


def _output_row_counts(rows: list[dict[str, Any]], keys: list[str], field: str) -> dict[str, int]:
    if not rows:
        return {}
    frame = pd.DataFrame(rows)
    return {"|".join(map(str, key if isinstance(key, tuple) else (key,))): int(value) for key, value in frame.groupby(keys, dropna=False)[field].sum().items()}


def build(output_dir: Path, *, window_sec: float = 30.0, tolerance_sec: float = 1e-6) -> dict[str, Any]:
    map_path = MAP_ROOT / "all_fold_apply_chart_support_map.parquet"
    map_validation_path = MAP_ROOT / "validation.json"
    audit_path = V4_ROOT / "row_support_audit.csv"
    surface_validation_path = V4_ROOT / "validation.json"
    for path in (map_path, map_validation_path, audit_path, surface_validation_path, PROTOCOL_PATH):
        require(path.is_file(), f"Required input is missing: {path}")
    require(not output_dir.exists(), f"Refusing to overwrite existing output directory: {output_dir}")

    map_validation = json.loads(map_validation_path.read_text(encoding="utf-8"))
    surface_validation = json.loads(surface_validation_path.read_text(encoding="utf-8"))
    _assert_input_provenance(map_validation, surface_validation)
    require(map_validation.get("output_parquet_sha256") == sha256_file(map_path), "Apply support map hash mismatch")

    chart = pd.read_parquet(map_path, columns=MAP_COLUMNS)
    audit = pd.read_csv(audit_path, usecols=AUDIT_COLUMNS, low_memory=False)
    require(not chart.duplicated(KEYS).any(), "Duplicate (file, epoch_id) keys in apply chart map")
    require(not audit.duplicated(KEYS).any(), "Duplicate (file, epoch_id) keys in V4 stage/support audit")
    require(len(chart) == 92_545 and chart["file"].nunique() == 100 and chart["subject"].nunique() == 78, "Unexpected apply map coverage")

    stage_audit = audit.rename(columns={
        "subject": "audit_subject", "bids_subject": "audit_bids_subject", "pid": "pid",
        "t_start": "t_start", "t_end": "t_end", "source_stratum": "source_stratum",
        "primary_surface_eligible": "primary_surface_eligible",
    })
    joined = stage_audit.merge(chart, on=KEYS, how="right", validate="one_to_one", indicator=True)
    require(joined["_merge"].eq("both").all(), "An apply chart row has no V4 stage/support-audit match")
    joined = joined.drop(columns="_merge")
    require(joined["audit_subject"].eq(joined["subject"]).all(), "Stage-audit biological subject mismatch")
    require(joined["audit_bids_subject"].eq(joined["bids_subject"]).all(), "Stage-audit BIDS identity mismatch")
    require(joined["source_stratum"].eq("pure_ppg").all(), "Apply chart source stratum is not pure PPG")
    require(joined["primary_surface_eligible"].astype(bool).all(), "An apply chart row is not primary-surface eligible in V4")
    require(joined["audit_primary_surface_eligible"].astype(bool).all(), "Apply map eligibility field changed")
    require(joined["source_sha256"].eq(joined["expected_source_sha256"]).all(), "Stage-audit source hash differs from the frozen fold manifest")
    require(joined["source_sha256"].eq(joined["recording_source_sha256"]).all(), "Stage-audit source hash differs from the separate support map")
    require(joined["source_hashes_match_fold_manifest"].astype(bool).all(), "Map contains an unbound source hash")
    require(np.isclose(joined["t_start"].to_numpy(float), joined["chart_window_start_sec"].to_numpy(float), rtol=0.0, atol=tolerance_sec).all(), "Stage-audit/chart start-time mismatch")
    require(np.isclose(joined["t_end"].to_numpy(float), joined["chart_window_end_sec"].to_numpy(float), rtol=0.0, atol=tolerance_sec).all(), "Stage-audit/chart end-time mismatch")
    require(joined["stage_at_origin_status"].isin(["unique_source_stage_at_origin", "no_source_stage_at_origin"]).all(), "Unexpected stage-origin mapping status")
    require(joined["stage_window_status"].isin(["stage_pure_at_origin", "window_stage_differs_from_origin_stage", "origin_or_window_invalid"]).all(), "Unexpected stage-window status")

    c3_rows: list[dict[str, Any]] = []
    c1_rows: list[dict[str, Any]] = []
    stage_rows: list[dict[str, Any]] = []
    failure_counts: Counter[str] = Counter()
    fold_by_file: dict[str, tuple[int, str]] = {}
    audit_by_file = {str(name): block.copy() for name, block in audit.groupby("file", sort=False)}

    all_audit_files = set(joined["file"].astype(str))
    for filename, chart_group in joined.groupby("file", sort=True):
        chart_group = chart_group.sort_values("epoch_id", kind="stable")
        folds = set(pd.to_numeric(chart_group["fold"], errors="raise").astype(int))
        pids = set(chart_group["pid"].astype(str))
        require(len(folds) == len(pids) == 1, f"File crosses apply fold/PID assignment: {filename}")
        fold = next(iter(folds))
        pid = next(iter(pids))
        subject = str(chart_group["subject"].iloc[0])
        bids_subject = str(chart_group["bids_subject"].iloc[0])
        fold_by_file[str(filename)] = (fold, pid)

        # Retain the full V4 row sequence. Non-exported/ineligible rows remain
        # explicit blockers in a fixed-lag path rather than being skipped over.
        full_rows = audit_by_file[str(filename)].copy()
        full_rows = full_rows.merge(chart_group, on=KEYS, how="left", validate="one_to_one", suffixes=("", "_chart"))
        full_rows["chart_row_present"] = full_rows["fold"].notna()
        full_rows = full_rows.sort_values("epoch_id", kind="stable")
        require(not full_rows["epoch_id"].duplicated().any(), f"Duplicate full-sequence epoch IDs: {filename}")
        rows_by_epoch = {int(row["epoch_id"]): row for row in full_rows.to_dict(orient="records")}
        for row in rows_by_epoch.values():
            row["_support_eligible_cached"] = _support_ok(row)
            row["_chart_valid_3d_cached"] = _chart_ok(row, "3d")
            row["_chart_valid_9d_cached"] = _chart_ok(row, "9d")
            try:
                row_start, row_end = float(row["t_start"]), float(row["t_end"])
                row["_window_time_valid_cached"] = bool(np.isfinite([row_start, row_end]).all() and np.isclose(row_end - row_start, window_sec, rtol=0.0, atol=tolerance_sec))
            except (KeyError, TypeError, ValueError):
                row["_window_time_valid_cached"] = False
        for epoch_id, row in rows_by_epoch.items():
            next_row = rows_by_epoch.get(epoch_id + 1)
            row["_time_edge_next_valid_cached"] = bool(
                next_row is not None
                and not pd.isna(row.get("segment_id"))
                and not pd.isna(next_row.get("segment_id"))
                and str(row.get("segment_id")) == str(next_row.get("segment_id"))
                and row["_window_time_valid_cached"]
                and next_row["_window_time_valid_cached"]
                and np.isclose(float(row["t_end"]), float(next_row["t_start"]), rtol=0.0, atol=tolerance_sec)
            )
        apply_origins = [row for row in rows_by_epoch.values() if truth(row.get("chart_row_present")) and _support_ok(row)]

        for stage_code, stage_name in CONTEXTS.items():
            stage_origins = [row for row in apply_origins if _stage_origin_ok(row, stage_code)]
            stage_rows.append({
                "fold": fold, "pid": pid, "subject": subject, "bids_subject": bids_subject,
                "file": str(filename), "source_stratum": "pure_ppg", "stage_origin": stage_name,
                "stage_source_column": "stage_hum",
                "support_eligible_stage_pure_origins": len(stage_origins),
                "origin_chart_qc_valid_3d": sum(_chart_ok(row, "3d") for row in stage_origins),
                "origin_chart_qc_valid_9d": sum(_chart_ok(row, "9d") for row in stage_origins),
            })
            for horizon_name, lag in HORIZONS.items():
                for dimension in DIMENSIONS:
                    checks = [
                        _assess_path(rows_by_epoch, origin_id=int(origin["epoch_id"]), lag=lag, dimension=dimension,
                                     window_sec=window_sec, tolerance_sec=tolerance_sec)
                        for origin in stage_origins
                    ]
                    eligible_horizons = [item["actual_horizon_sec"] for item in checks if item["pair_eligible"]]
                    failure_counts.update(item["failure_reason"] for item in checks if not item["pair_eligible"])
                    c3_rows.append({
                        "fold": fold, "pid": pid, "subject": subject, "bids_subject": bids_subject,
                        "file": str(filename), "source_stratum": "pure_ppg", "stage_origin": stage_name,
                        "dimension": dimension, "horizon": horizon_name, "nominal_lag_rows": lag,
                        "support_eligible_stage_pure_origins": len(stage_origins),
                        "candidate_origins_with_valid_origin_chart": sum(_chart_ok(row, dimension) for row in stage_origins),
                        "target_rows_present": sum(item["target_present"] for item in checks),
                        "required_path_rows_present": sum(item["required_path_rows_present"] for item in checks),
                        "time_contiguous_paths": sum(item["time_contiguous"] for item in checks),
                        "source_support_eligible_paths": sum(item["source_support_path_valid"] for item in checks),
                        "chart_rows_present_paths": sum(item["chart_rows_present"] for item in checks),
                        "chart_qc_eligible_paths": sum(item["chart_qc_path_valid"] for item in checks),
                        "outcome_blind_eligible_origin_target_paths": sum(item["pair_eligible"] for item in checks),
                        "actual_horizon_min_sec": min(eligible_horizons) if eligible_horizons else None,
                        "actual_horizon_median_sec": float(np.median(eligible_horizons)) if eligible_horizons else None,
                        "actual_horizon_max_sec": max(eligible_horizons) if eligible_horizons else None,
                    })

        c1_origins = [row for row in apply_origins if int(row["epoch_id"]) >= 2]
        for horizon_name, lag in HORIZONS.items():
            for dimension in DIMENSIONS:
                checks = [
                    _assess_path(rows_by_epoch, origin_id=int(origin["epoch_id"]), lag=lag, dimension=dimension,
                                 history_rows=2, window_sec=window_sec, tolerance_sec=tolerance_sec)
                    for origin in c1_origins
                ]
                eligible_horizons = [item["actual_horizon_sec"] for item in checks if item["pair_eligible"]]
                failure_counts.update(item["failure_reason"] for item in checks if not item["pair_eligible"])
                c1_rows.append({
                    "fold": fold, "pid": pid, "subject": subject, "bids_subject": bids_subject,
                    "file": str(filename), "source_stratum": "pure_ppg", "dimension": dimension,
                    "horizon": horizon_name, "nominal_lag_rows": lag,
                    "candidate_origins_epoch_id_ge_2": len(c1_origins),
                    "candidate_origins_with_valid_origin_chart": sum(_chart_ok(row, dimension) for row in c1_origins),
                    "target_rows_present": sum(item["target_present"] for item in checks),
                    "required_path_rows_present": sum(item["required_path_rows_present"] for item in checks),
                    "time_contiguous_history_origin_target_paths": sum(item["time_contiguous"] for item in checks),
                    "source_support_eligible_paths": sum(item["source_support_path_valid"] for item in checks),
                    "chart_rows_present_paths": sum(item["chart_rows_present"] for item in checks),
                    "chart_qc_eligible_history_origin_target_paths": sum(item["chart_qc_path_valid"] for item in checks),
                    "outcome_blind_eligible_history_origin_target_paths": sum(item["pair_eligible"] for item in checks),
                    "actual_horizon_min_sec": min(eligible_horizons) if eligible_horizons else None,
                    "actual_horizon_median_sec": float(np.median(eligible_horizons)) if eligible_horizons else None,
                    "actual_horizon_max_sec": max(eligible_horizons) if eligible_horizons else None,
                })

    require(len(fold_by_file) == 100 and set(fold_by_file) == all_audit_files, "Apply map/file inventory mismatch")
    apply_pids_by_fold: dict[int, set[str]] = {}
    for fold, pid in fold_by_file.values():
        apply_pids_by_fold.setdefault(fold, set()).add(pid)
    flattened = [pid for values in apply_pids_by_fold.values() for pid in values]
    require(len(flattened) == len(set(flattened)) == 78, "A PID appears in more than one apply fold or is missing")

    stage_df = pd.DataFrame(stage_rows)
    c3_df = pd.DataFrame(c3_rows)
    c1_df = pd.DataFrame(c1_rows)
    require(len(stage_df) == 200 and len(c3_df) == 1_200 and len(c1_df) == 600, "Unexpected PID/recording/context/horizon table shape")
    require(not c3_df.duplicated(["pid", "file", "stage_origin", "dimension", "horizon"]).any(), "Duplicate C3 support cell")
    require(not c1_df.duplicated(["pid", "file", "dimension", "horizon"]).any(), "Duplicate C1 support cell")

    stage_summary = stage_df.groupby("stage_origin", as_index=False).agg(
        pid_recording_cells=("file", "size"),
        pids_with_stage_pure_origins=("pid", lambda values: int(values[stage_df.loc[values.index, "support_eligible_stage_pure_origins"].gt(0)].nunique())),
        support_eligible_stage_pure_origins=("support_eligible_stage_pure_origins", "sum"),
        origin_chart_qc_valid_3d=("origin_chart_qc_valid_3d", "sum"),
        origin_chart_qc_valid_9d=("origin_chart_qc_valid_9d", "sum"),
    )
    c3_summary = c3_df.groupby(["stage_origin", "dimension", "horizon"], as_index=False).agg(
        pid_recording_cells=("file", "size"),
        pids_with_any_eligible_paths=("outcome_blind_eligible_origin_target_paths", lambda values: int(c3_df.loc[values.index[values.gt(0)], "pid"].nunique())),
        support_eligible_stage_pure_origins=("support_eligible_stage_pure_origins", "sum"),
        eligible_origin_target_paths=("outcome_blind_eligible_origin_target_paths", "sum"),
        target_rows_present=("target_rows_present", "sum"),
        time_contiguous_paths=("time_contiguous_paths", "sum"),
        actual_horizon_median_sec=("actual_horizon_median_sec", "median"),
    )
    c1_summary = c1_df.groupby(["dimension", "horizon"], as_index=False).agg(
        pid_recording_cells=("file", "size"),
        pids_with_any_eligible_paths=("outcome_blind_eligible_history_origin_target_paths", lambda values: int(c1_df.loc[values.index[values.gt(0)], "pid"].nunique())),
        candidate_origins_epoch_id_ge_2=("candidate_origins_epoch_id_ge_2", "sum"),
        eligible_history_origin_target_paths=("outcome_blind_eligible_history_origin_target_paths", "sum"),
        target_rows_present=("target_rows_present", "sum"),
        time_contiguous_paths=("time_contiguous_history_origin_target_paths", "sum"),
        actual_horizon_median_sec=("actual_horizon_median_sec", "median"),
    )

    output_dir.mkdir(parents=True, exist_ok=False)
    stage_path = output_dir / "stage_origin_support_by_pid_recording.csv"
    c3_path = output_dir / "c3_stage_horizon_support_by_pid_recording.csv"
    c1_path = output_dir / "c1_history_horizon_support_by_pid_recording.csv"
    stage_summary_path = output_dir / "stage_origin_support_summary.csv"
    c3_summary_path = output_dir / "c3_stage_horizon_support_summary.csv"
    c1_summary_path = output_dir / "c1_history_horizon_support_summary.csv"
    stage_df.to_csv(stage_path, index=False)
    c3_df.to_csv(c3_path, index=False)
    c1_df.to_csv(c1_path, index=False)
    stage_summary.to_csv(stage_summary_path, index=False)
    c3_summary.to_csv(c3_summary_path, index=False)
    c1_summary.to_csv(c1_summary_path, index=False)

    input_paths = {
        "apply_support_map": map_path,
        "apply_support_map_validation": map_validation_path,
        "v4_row_support_audit": audit_path,
        "v4_full_surface_validation": surface_validation_path,
        "registered_protocol": PROTOCOL_PATH,
        "stage_horizon_audit_code": Path(__file__).resolve(),
    }
    input_hashes = {name: sha256_file(path) for name, path in input_paths.items()}
    result = {
        "schema_version": "boas.all_fold_apply_stage_horizon_support.v4",
        "verdict": "PARTIAL_PASS_STAGE_HORIZON_SUPPORT_ONLY",
        "scope": "five-fold apply chart eligibility and human-scored stage-origin/horizon support; no matching, contrast, score or biological interpretation",
        "c3_context": "human-scored N2 versus Wake at forecast origin; frozen preregistration context",
        "row_count": int(len(chart)),
        "recording_count": int(chart["file"].nunique()),
        "biological_pid_count": int(chart["subject"].nunique()),
        "apply_fold_count": int(chart["fold"].nunique()),
        "apply_epochs_by_fold": {str(k): int(v) for k, v in chart.groupby("fold").size().to_dict().items()},
        "recordings_by_fold": {str(k): int(v) for k, v in chart.groupby("fold")["file"].nunique().to_dict().items()},
        "support_and_identity_join": {
            "one_to_one_chart_stage_audit_join": True,
            "all_apply_chart_rows_bound_to_v4_stage_audit": int(len(joined)),
            "all_rows_pure_ppg_primary_surface": True,
            "fold_pid_partition_disjoint": True,
            "source_hashes_match_v4_and_fold_manifests": True,
        },
        "stage_origin_counts": json.loads(stage_summary.to_json(orient="records")),
        "c3_support_counts": json.loads(c3_summary.to_json(orient="records")),
        "c1_support_counts": json.loads(c1_summary.to_json(orient="records")),
        "pair_failure_counts_first_failure": dict(sorted(failure_counts.items())),
        "stage_source": {
            "column": "stage_hum",
            "provenance": "V4 hash-bound full-surface stage/support audit; all 128 event-source hashes were stable during that audit",
            "stage_used_only_at_forecast_origin": True,
            "future_stage_values_used": False,
            "origin_requires_unique_source_label_and_stage_pure_window": True,
        },
        "pair_rule": "fixed row lags h1/h2/h4; all required rows must exist, remain in the same verified segment, touch at 30 s, pass separate source-support checks, and have present finite chart coordinates plus geometry/QC validity; C1 additionally requires two prior contiguous valid rows",
        "h5_generic_signal_support_status": "unknown",
        "h5_generic_source_quality_status": "not_recorded",
        "external_v4_support_object_remains_separate": True,
        "label_join_performed": True,
        "outcomes_calculated": False,
        "matching_performed": False,
        "C1_C2_C3_scores_opened": False,
        "biological_claim_authorized": False,
        "full_surface_replay_gate": "NOT_ASSESSED_BY_THIS_AUDIT",
        "full_cohort_protocol_authorization": "NOT_GRANTED",
        "limitations": [
            "Counts describe chart/source/stage support only and are not accepted pairs after C3 matching.",
            "The V4 external row-support object does not rewrite generic H5 temporal_support_status=unknown or source_quality_status=not_recorded.",
            "This audit does not perform the full-surface deterministic replay required by gate 7.",
            "Gate 7 and the separately dated gate-8 protocol amendment/hash freeze/authorization remain open; no outcomes may be computed yet.",
        ],
        "outputs": {name: path.name for name, path in {
            "stage_origin_support_by_pid_recording": stage_path,
            "c3_stage_horizon_support_by_pid_recording": c3_path,
            "c1_history_horizon_support_by_pid_recording": c1_path,
            "stage_origin_support_summary": stage_summary_path,
            "c3_stage_horizon_support_summary": c3_summary_path,
            "c1_history_horizon_support_summary": c1_summary_path,
        }.items()},
        "output_sha256": {
            name: sha256_file(path)
            for name, path in {
                "stage_origin_support_by_pid_recording": stage_path,
                "c3_stage_horizon_support_by_pid_recording": c3_path,
                "c1_history_horizon_support_by_pid_recording": c1_path,
                "stage_origin_support_summary": stage_summary_path,
                "c3_stage_horizon_support_summary": c3_summary_path,
                "c1_history_horizon_support_summary": c1_summary_path,
            }.items()
        },
        "input_sha256": input_hashes,
    }
    (output_dir / "validation.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT, help="Fresh output directory; never overwritten.")
    parser.add_argument("--window-sec", type=float, default=30.0)
    parser.add_argument("--tolerance-sec", type=float, default=1e-6)
    args = parser.parse_args()
    result = build(args.out_dir.resolve(), window_sec=args.window_sec, tolerance_sec=args.tolerance_sec)
    print(json.dumps({
        "verdict": result["verdict"], "row_count": result["row_count"],
        "recording_count": result["recording_count"], "biological_pid_count": result["biological_pid_count"],
        "c3_support_counts": result["c3_support_counts"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
