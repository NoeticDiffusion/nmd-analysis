"""Outcome-blind support preflight for the BOAS C1 chart forecast surface.

Binds selected fold-safe H5 identities, times and QC flags to frozen participant
splits and row-level source support. Never reads coordinate arrays, stage fields,
future chart values or prediction scores.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd

ARTICLE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ARTICLE = ARTICLE_ROOT.parent / "BOAS_sleep_dataset_ndt._v.1.0"
CHART_ROOT = SOURCE_ARTICLE / "results" / "fold_safe_chart_qualification_20260930_v1"
CHART_DATA_ROOT = CHART_ROOT / "processed" / "ds005555"
SUPPORT_ROOT = SOURCE_ARTICLE / "results" / "continuous_full_surface_support_audit_20260929_v4"
FOLD_MANIFEST_ROOT = SUPPORT_ROOT / "fold_manifests"
SUPPORT_AUDIT_PATH = SUPPORT_ROOT / "row_support_audit.csv"
SUPPORT_AUDIT_VALIDATION_PATH = SUPPORT_ROOT / "validation.json"
CHART_MAP_VALIDATION_PATH = CHART_ROOT / "support_map_all_folds_v3" / "validation.json"
CHART_MAP_PATH = CHART_ROOT / "support_map_all_folds_v3" / "all_fold_apply_chart_support_map.parquet"
DEFAULT_OUTPUT_ROOT = ARTICLE_ROOT / "results" / "c1_outcome_blind_preflight_20260930_v1"

# Fold 0 has several retained variants; select only its latest label-free run.
SELECTED_RUNS = {
    0: {"training": "fold_0_training_label_free_v2", "apply": "fold_0_apply_label_free_v2"},
    1: {"training": "fold_1_training_label_free_v1", "apply": "fold_1_apply_label_free_v1"},
    2: {"training": "fold_2_training_label_free_v1", "apply": "fold_2_apply_label_free_v1"},
    3: {"training": "fold_3_training_label_free_v1", "apply": "fold_3_apply_label_free_v1"},
    4: {"training": "fold_4_training_label_free_v1", "apply": "fold_4_apply_label_free_v1"},
}
HORIZONS = {"h1": 1, "h2": 2, "h4": 4}
DIMENSIONS = ("3d", "9d")
HISTORY_ROWS = 2
WINDOW_SECONDS = 30.0
TIME_TOLERANCE_SECONDS = 1e-6

# Explicit allow-list: outcome/stage columns in the source CSV are never parsed.
SUPPORT_COLUMNS = [
    "file", "subject", "bids_subject", "pid", "epoch_id", "t_start", "t_end",
    "source_stratum", "primary_surface_eligible", "support_exclusion_reasons",
    "segment_id", "source_sha256", "source_sample_mapping_status",
    "actual_sample_contributors_status", "input_sample_finite_status",
    "input_sample_gap_count", "qc_ok_eeg", "qc_ok_ppg",
]
SUPPORT_KEY = ["file", "epoch_id"]


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text(value: Any) -> str:
    if isinstance(value, (bytes, np.bytes_)):
        return bytes(value).decode("utf-8", errors="strict")
    return str(value)


def truth(value: Any) -> bool:
    if value is None or pd.isna(value):
        return False
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return value != 0
    return str(value).strip().lower() in {"true", "1", "yes"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized(value: Any) -> Any:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value if isinstance(value, (str, int, float, bool)) else str(value)


def projection_sha256(frame: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    for row in frame[SUPPORT_COLUMNS].itertuples(index=False, name=None):
        payload = [normalized(value) for value in row]
        digest.update(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n")
    return digest.hexdigest()


def validate_inputs() -> dict[str, Any]:
    for path in (SUPPORT_AUDIT_PATH, SUPPORT_AUDIT_VALIDATION_PATH, CHART_MAP_PATH, CHART_MAP_VALIDATION_PATH):
        require(path.is_file(), f"Required support artifact missing: {path}")
    v4 = read_json(SUPPORT_AUDIT_VALIDATION_PATH)
    require(v4.get("schema") == "nmd_analysis.continuous_full_surface_audit.v1", "Unexpected source-support schema")
    require(v4.get("status") == "PARTIAL_PASS_SOURCE_SUPPORT_ONLY", "Source-support status changed")
    require(v4.get("outcomes_calculated") is False and v4.get("full_cohort_scoring_authorized") is False,
            "Source-support audit has an invalid outcome/authorization state")
    chart_map = read_json(CHART_MAP_VALIDATION_PATH)
    require(chart_map.get("schema_version") == "boas.all_fold_apply_chart_support_map.v2", "Unexpected chart-map schema")
    require(chart_map.get("label_join_performed") is False, "Chart map is not stage-blind")
    require(chart_map.get("stage_horizon_intersection_computed") is False, "Chart map contains a horizon intersection")
    require(chart_map.get("contrasts_computed") is False and chart_map.get("biological_claim_authorized") is False,
            "Chart map has an invalid scope")
    require(chart_map.get("output_parquet_sha256") == sha256_file(CHART_MAP_PATH), "Chart map digest mismatch")
    return {
        "source_support_validation": {
            "path": SUPPORT_AUDIT_VALIDATION_PATH.relative_to(SOURCE_ARTICLE).as_posix(),
            "sha256": sha256_file(SUPPORT_AUDIT_VALIDATION_PATH),
            "status": v4.get("status"),
            "outcomes_calculated": v4.get("outcomes_calculated"),
            "full_cohort_scoring_authorized": v4.get("full_cohort_scoring_authorized"),
        },
        "chart_map_validation": {
            "path": CHART_MAP_VALIDATION_PATH.relative_to(SOURCE_ARTICLE).as_posix(),
            "sha256": sha256_file(CHART_MAP_VALIDATION_PATH),
            "schema_version": chart_map.get("schema_version"),
            "label_join_performed": chart_map.get("label_join_performed"),
            "stage_horizon_intersection_computed": chart_map.get("stage_horizon_intersection_computed"),
            "parquet_path": CHART_MAP_PATH.relative_to(SOURCE_ARTICLE).as_posix(),
            "parquet_sha256": chart_map.get("output_parquet_sha256"),
        },
    }


def load_support() -> tuple[pd.DataFrame, str]:
    dtype = {name: "string" for name in (
        "file", "subject", "bids_subject", "source_stratum", "support_exclusion_reasons",
        "segment_id", "source_sha256", "source_sample_mapping_status",
        "actual_sample_contributors_status", "input_sample_finite_status",
    )}
    frame = pd.read_csv(SUPPORT_AUDIT_PATH, usecols=SUPPORT_COLUMNS, dtype=dtype, low_memory=False)
    frame["epoch_id"] = pd.to_numeric(frame["epoch_id"], errors="raise").astype(np.int64)
    frame["pid"] = pd.to_numeric(frame["pid"], errors="raise").astype(np.int64)
    for col in ("t_start", "t_end", "input_sample_gap_count"):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    require(not frame.duplicated(SUPPORT_KEY).any(), "Duplicate source-support (file, epoch_id) rows")
    no_reason = frame["support_exclusion_reasons"].fillna("").astype(str).str.strip().eq("")
    frame["source_support_eligible"] = (
        frame["primary_surface_eligible"].map(truth)
        & frame["source_stratum"].eq("pure_ppg")
        & frame["source_sample_mapping_status"].eq("nominal_bounds_mapped")
        & frame["actual_sample_contributors_status"].eq("finite_causal_conservative_bound")
        & frame["input_sample_finite_status"].eq("all_finite")
        & frame["input_sample_gap_count"].eq(0)
        & frame["qc_ok_eeg"].map(truth)
        & frame["qc_ok_ppg"].map(truth)
        & no_reason
    )
    return frame, projection_sha256(frame)


def load_fold(fold: int) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    path = FOLD_MANIFEST_ROOT / f"fold_{fold}.json"
    require(path.is_file(), f"Fold manifest missing: {path}")
    manifest = read_json(path)
    train, apply = set(manifest.get("training_pids", [])), set(manifest.get("apply_pids", []))
    require(train and apply and train.isdisjoint(apply), f"Invalid train/apply PID split in fold {fold}")
    assignment: dict[str, dict[str, str]] = {"training": {}, "apply": {}}
    for role, pids, key in (("training", train, "training_ranges"), ("apply", apply, "apply_ranges")):
        for item in manifest.get(key, []):
            file_name, subject = str(item["recording_id"]), str(item["subject_id"])
            require(subject in pids, f"{role} range subject absent from fold PID set: {item}")
            previous = assignment[role].setdefault(file_name, subject)
            require(previous == subject, f"Recording maps to multiple subjects in fold {fold}: {file_name}")
    require(set(assignment["training"]).isdisjoint(assignment["apply"]), f"Recording leakage in fold {fold}")
    return manifest, assignment


def validate_run(fold: int, role: str, run: str) -> dict[str, Any]:
    root = CHART_DATA_ROOT / run
    manifest_path = root / "run_manifest.json"
    require(manifest_path.is_file(), f"Run manifest missing: {manifest_path}")
    info = read_json(manifest_path)
    extra, config = info.get("extra", {}), info.get("config", {})
    errors, stage_qc = extra.get("run_errors", {}), extra.get("stage_mapping_qc", {})
    require(extra.get("run_status") == "completed" and extra.get("fatal_error") is None, f"Run incomplete: {run}")
    require(errors.get("count") == 0, f"Run records errors: {run}")
    require(stage_qc.get("status") == "none", f"Stage mapping was enabled: {run}")
    config_path = Path(config.get("yaml_source", {}).get("provided_path", ""))
    require(config_path.is_file(), f"Run config missing: {config_path}")
    return {
        "fold": fold, "fold_role": role, "run_name": run,
        "h5_file_count": len(list(root.glob("sub-*/sub-*.h5"))),
        "run_manifest": manifest_path.relative_to(SOURCE_ARTICLE).as_posix(),
        "run_manifest_sha256": sha256_file(manifest_path),
        "run_status": extra.get("run_status"), "run_error_count": errors.get("count"),
        "stage_mapping_qc_status": stage_qc.get("status"),
        "resolved_config_digest_sha256": config.get("digest_sha256"),
        "provided_config": config_path.relative_to(SOURCE_ARTICLE).as_posix(),
        "provided_config_sha256": sha256_file(config_path),
    }


def bool_vector(h5: h5py.File, path: str, n: int) -> np.ndarray:
    require(path in h5, f"QC metadata missing: {path}")
    value = np.asarray(h5[path][:])
    require(value.shape == (n,), f"QC metadata shape mismatch: {path}")
    return value != 0


def read_run(fold: int, role: str, run: str, assignment: dict[str, dict[str, str]],
             source_hashes: dict[str, str], metadata_digest: Any) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    paths = sorted((CHART_DATA_ROOT / run).glob("sub-*/sub-*.h5"))
    require(paths, f"No H5 chart files in selected run: {run}")
    expected_files, actual_files = set(assignment[role]), set()
    frames, inventory = [], []
    for path in paths:
        with h5py.File(path, "r") as h5:
            require("subject_id" in h5.attrs and "meta_pid" in h5.attrs, f"Participant IDs missing: {path}")
            bids_subject, pid = text(h5.attrs["subject_id"]), int(h5.attrs["meta_pid"])
            require("row_source/raw_file" in h5, f"Raw-file identity missing: {path}")
            raw_files = [text(item) for item in np.asarray(h5["row_source/raw_file"][:]).tolist()]
            require(raw_files and len(set(raw_files)) == 1, f"Mixed raw-file identity in {path}")
            file_name = raw_files[0]
            require(file_name in assignment[role],
                    f"H5 recording is absent from frozen fold {fold} {role} assignment: {file_name}")
            require(file_name in source_hashes, f"Source hash absent from fold manifest: {file_name}")
            actual_files.add(file_name)

            epoch = np.asarray(h5["epoch_id"][:], dtype=np.int64)
            center = np.asarray(h5["time"][:], dtype=np.float64)
            start = np.asarray(h5["window_start"][:], dtype=np.float64)
            end = np.asarray(h5["window_end"][:], dtype=np.float64)
            n = len(epoch)
            require(n > 0 and len(set(epoch.tolist())) == n, f"Empty/duplicate epoch identities in {path}")
            for name, values in (("time", center), ("window_start", start), ("window_end", end)):
                require(values.shape == (n,) and np.isfinite(values).all(), f"Invalid {name} metadata in {path}")

            # Read only dataset shapes for chart payloads; never index coordinate values.
            require(h5["coords_3d_cohort_anchored/values"].shape == (n, 3), f"Unexpected 3D chart shape: {path}")
            require(h5["coords_9d_cohort_anchored/values"].shape == (n, 9), f"Unexpected 9D chart shape: {path}")
            valid3 = (bool_vector(h5, "qc/windows/mnps_3d_valid", n)
                      & bool_vector(h5, "qc/windows/geometry_valid", n)
                      & bool_vector(h5, "qc/windows/retained_after_qc", n))
            valid9 = (bool_vector(h5, "qc/windows/coords_9d_valid", n)
                      & bool_vector(h5, "qc/windows/geometry_valid", n)
                      & bool_vector(h5, "qc/windows/retained_after_qc", n))

        metadata_digest.update(run.encode() + b"\0" + path.relative_to(CHART_DATA_ROOT).as_posix().encode() + b"\0")
        metadata_digest.update(file_name.encode() + b"\0" + bids_subject.encode() + b"\0")
        for values, dtype in (([pid], "<i8"), (epoch, "<i8"), (center, "<f8"), (start, "<f8"),
                              (end, "<f8"), (valid3, "u1"), (valid9, "u1")):
            metadata_digest.update(np.asarray(values, dtype=dtype).tobytes())
        frames.append(pd.DataFrame({
            "fold": fold, "fold_role": role, "fold_subject": assignment[role][file_name],
            "bids_subject": bids_subject, "pid": pid, "file": file_name,
            "epoch_id": epoch, "chart_time_center_sec": center, "chart_window_start_sec": start,
            "chart_window_end_sec": end, "chart_qc_valid_3d": valid3, "chart_qc_valid_9d": valid9,
        }))
        inventory.append({
            "fold": fold, "fold_role": role, "run_name": run, "bids_subject": bids_subject, "pid": pid,
            "file": file_name, "h5_relative_path": path.relative_to(CHART_DATA_ROOT).as_posix(),
            "h5_size_bytes": path.stat().st_size, "chart_rows": n,
            "chart_3d_qc_valid_rows": int(valid3.sum()), "chart_9d_qc_valid_rows": int(valid9.sum()),
            "manifest_source_sha256": source_hashes[file_name],
        })
    require(actual_files == expected_files, f"H5 recording set differs from fold {fold} {role} split")
    return pd.concat(frames, ignore_index=True), inventory


def assess_recording(rows: pd.DataFrame) -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[float]]]:
    rows = rows.sort_values("epoch_id", kind="stable")
    by_epoch = {int(row.epoch_id): row for row in rows.itertuples(index=False)}
    require(len(by_epoch) == len(rows), "Duplicate epochs in selected recording")
    cells, horizon_values = [], {}
    for dimension in DIMENSIONS:
        chart_col = "chart_qc_valid_3d" if dimension == "3d" else "chart_qc_valid_9d"
        for horizon, lag in HORIZONS.items():
            counts: Counter[str] = Counter()
            actual_values = []
            for origin_id in sorted(epoch for epoch in by_epoch if epoch >= HISTORY_ROWS):
                counts["candidate_origins_epoch_id_ge_2"] += 1
                target_id = origin_id + lag
                ids = list(range(origin_id - HISTORY_ROWS, target_id + 1))
                path = [by_epoch.get(epoch) for epoch in ids]
                if any(row is None for row in path):
                    counts["failure_missing_intermediate_or_target_row"] += 1
                    continue
                concrete = [row for row in path if row is not None]
                origin, target = by_epoch[origin_id], by_epoch[target_id]
                counts["target_rows_present"] += 1
                counts["required_path_rows_present"] += 1

                segments = [row.segment_id for row in concrete]
                same_segment = all(pd.notna(x) for x in segments) and len({str(x) for x in segments}) == 1
                starts = np.asarray([row.chart_window_start_sec for row in concrete], dtype=float)
                ends = np.asarray([row.chart_window_end_sec for row in concrete], dtype=float)
                finite = np.isfinite(starts).all() and np.isfinite(ends).all()
                if finite:
                    lengths_ok = np.isclose(ends - starts, WINDOW_SECONDS, rtol=0.0, atol=TIME_TOLERANCE_SECONDS).all()
                    edges_ok = np.isclose(ends[:-1], starts[1:], rtol=0.0, atol=TIME_TOLERANCE_SECONDS).all()
                else:
                    lengths_ok = edges_ok = False
                time_ok = bool(same_segment and finite and lengths_ok and edges_ok)
                counts["time_contiguous_paths" if time_ok else "failure_gap_or_segment_break"] += 1

                source_ok = all(bool(row.source_support_eligible) for row in concrete)
                counts["source_support_eligible_paths" if source_ok else "failure_source_support_ineligible_path"] += 1
                predictors = concrete[:HISTORY_ROWS + 1]
                predictors_ok = all(bool(getattr(row, chart_col)) for row in predictors)
                target_ok = bool(getattr(target, chart_col))
                counts["predictor_history_chart_qc_valid_paths" if predictors_ok else "failure_predictor_chart_qc_invalid_path"] += 1
                counts["target_chart_qc_valid_paths" if target_ok else "failure_target_chart_qc_invalid"] += 1

                actual = float(target.chart_time_center_sec) - float(origin.chart_time_center_sec)
                horizon_ok = np.isfinite(actual) and actual > 0 and np.isclose(
                    actual, lag * WINDOW_SECONDS, rtol=0.0, atol=TIME_TOLERANCE_SECONDS
                )
                if not horizon_ok:
                    counts["failure_actual_horizon_mismatch"] += 1
                eligible = time_ok and source_ok and predictors_ok and target_ok and bool(horizon_ok)
                if eligible:
                    counts["outcome_blind_eligible_paths"] += 1
                    actual_values.append(actual)
                else:
                    counts["ineligible_paths"] += 1

            # Include missing target/intermediate rows among unqualified
            # candidate origins; the detailed failure column preserves why.
            counts["ineligible_paths"] = (
                counts["candidate_origins_epoch_id_ge_2"] - counts["outcome_blind_eligible_paths"]
            )
            cells.append({
                "fold": int(rows["fold"].iloc[0]), "fold_role": str(rows["fold_role"].iloc[0]),
                "pid": int(rows["pid"].iloc[0]), "source_subject": str(rows["source_subject"].iloc[0]),
                "bids_subject": str(rows["bids_subject"].iloc[0]), "file": str(rows["file"].iloc[0]),
                "dimension": dimension, "horizon": horizon, "nominal_lag_rows": lag,
                **{key: int(counts.get(key, 0)) for key in (
                    "candidate_origins_epoch_id_ge_2", "target_rows_present", "required_path_rows_present",
                    "time_contiguous_paths", "source_support_eligible_paths",
                    "predictor_history_chart_qc_valid_paths", "target_chart_qc_valid_paths",
                    "outcome_blind_eligible_paths", "ineligible_paths",
                    "failure_missing_intermediate_or_target_row", "failure_gap_or_segment_break",
                    "failure_source_support_ineligible_path", "failure_predictor_chart_qc_invalid_path",
                    "failure_target_chart_qc_invalid", "failure_actual_horizon_mismatch",
                )},
                "actual_horizon_min_sec": min(actual_values) if actual_values else None,
                "actual_horizon_median_sec": float(np.median(actual_values)) if actual_values else None,
                "actual_horizon_max_sec": max(actual_values) if actual_values else None,
            })
            horizon_values[(dimension, horizon)] = actual_values
    return cells, horizon_values


COUNT_COLUMNS = [
    "candidate_origins_epoch_id_ge_2", "target_rows_present", "required_path_rows_present",
    "time_contiguous_paths", "source_support_eligible_paths", "predictor_history_chart_qc_valid_paths",
    "target_chart_qc_valid_paths", "outcome_blind_eligible_paths", "ineligible_paths",
    "failure_missing_intermediate_or_target_row", "failure_gap_or_segment_break",
    "failure_source_support_ineligible_path", "failure_predictor_chart_qc_invalid_path",
    "failure_target_chart_qc_invalid", "failure_actual_horizon_mismatch",
]


def make_summary(cells: pd.DataFrame, actual: dict[tuple[int, str, str, str], list[float]]) -> pd.DataFrame:
    output = []
    for keys, block in cells.groupby(["fold", "fold_role", "dimension", "horizon"], sort=True):
        fold, role, dimension, horizon = keys
        row = {
            "fold": int(fold), "fold_role": str(role), "dimension": str(dimension), "horizon": str(horizon),
            "nominal_lag_rows": int(block["nominal_lag_rows"].iloc[0]),
            "pid_count": int(block["pid"].nunique()), "pid_recording_count": int(block["file"].nunique()),
            "pids_with_eligible_paths": int(block.loc[block["outcome_blind_eligible_paths"].gt(0), "pid"].nunique()),
            "pid_recording_cells_with_eligible_paths": int(block["outcome_blind_eligible_paths"].gt(0).sum()),
        }
        row.update({name: int(block[name].sum()) for name in COUNT_COLUMNS})
        times = actual.get((int(fold), str(role), str(dimension), str(horizon)), [])
        row.update({
            "actual_horizon_min_sec": min(times) if times else None,
            "actual_horizon_median_sec": float(np.median(times)) if times else None,
            "actual_horizon_max_sec": max(times) if times else None,
        })
        output.append(row)
    return pd.DataFrame(output)


def build(output_root: Path) -> dict[str, Any]:
    require(not output_root.exists(), f"Refusing to overwrite existing preflight output: {output_root}")
    artifact_validation = validate_inputs()
    support, support_projection_hash = load_support()
    primary_support = support.loc[support["primary_surface_eligible"].map(truth)]
    require(
        len(primary_support) == 92545
        and primary_support["file"].nunique() == 100
        and primary_support["pid"].nunique() == 78,
        "Unexpected primary-surface support recording/PID coverage",
    )

    all_h5 = sorted(CHART_DATA_ROOT.rglob("*.h5"))
    require(len(all_h5) == 660, f"Handover 530 expected 660 H5 files; found {len(all_h5)}")
    selected_names = {run for runs in SELECTED_RUNS.values() for run in runs.values()}
    selected_paths = {p.resolve() for run in selected_names for p in (CHART_DATA_ROOT / run).glob("sub-*/sub-*.h5")}
    require(len(selected_paths) == 500, f"Expected 500 H5 files in selected fold surface; found {len(selected_paths)}")
    run_inventory = []
    for root in sorted(p for p in CHART_DATA_ROOT.iterdir() if p.is_dir()):
        n = len(list(root.glob("sub-*/sub-*.h5")))
        run_inventory.append({
            "run_name": root.name, "h5_file_count": n,
            "selected_for_c1_preflight": root.name in selected_names,
            "selection_reason": "explicit_fold_label_free_run" if root.name in selected_names else "retained_variant_not_selected",
        })

    metadata_digest = hashlib.sha256()
    run_records, chart_frames, h5_inventory, fold_records = [], [], [], []
    all_apply_pids: list[str] = []
    for fold, runs in SELECTED_RUNS.items():
        manifest, assignments = load_fold(fold)
        all_apply_pids.extend(str(pid) for pid in manifest["apply_pids"])
        source_hashes = {str(k): str(v) for k, v in manifest["source_file_sha256"].items()}
        require(set(assignments["training"]) | set(assignments["apply"]) == set(source_hashes),
                f"Fold {fold} assignments do not match source-hash ledger")
        manifest_path = FOLD_MANIFEST_ROOT / f"fold_{fold}.json"
        fold_records.append({
            "fold": fold, "split_id": manifest.get("split_id"), "grouping_unit": manifest.get("grouping_unit"),
            "training_pid_count": len(manifest["training_pids"]), "apply_pid_count": len(manifest["apply_pids"]),
            "training_recording_count": len(assignments["training"]), "apply_recording_count": len(assignments["apply"]),
            "fold_manifest": manifest_path.relative_to(SOURCE_ARTICLE).as_posix(),
            "fold_manifest_sha256": sha256_file(manifest_path),
        })
        for role in ("training", "apply"):
            run = runs[role]
            run_records.append(validate_run(fold, role, run))
            frame, inventory = read_run(fold, role, run, assignments, source_hashes, metadata_digest)
            chart_frames.append(frame)
            h5_inventory.extend(inventory)

    require(len(all_apply_pids) == len(set(all_apply_pids)), "A participant appears in more than one apply fold")
    expected_primary_pids = set(primary_support["subject"].dropna().astype(str))
    require(set(all_apply_pids) == expected_primary_pids, "Apply folds do not partition the primary-surface participant set")

    charts = pd.concat(chart_frames, ignore_index=True)
    require(not charts.duplicated(["fold", "fold_role", "file", "epoch_id"]).any(), "Duplicate selected chart identity rows")
    audit = support.rename(columns={
        "subject": "source_subject", "bids_subject": "source_bids_subject", "pid": "source_pid",
        "t_start": "source_t_start", "t_end": "source_t_end",
    })
    joined = charts.merge(audit, on=SUPPORT_KEY, how="left", validate="many_to_one", indicator=True)
    require(joined["_merge"].eq("both").all(), "Selected H5 row has no source-support record")
    joined = joined.drop(columns="_merge")
    require(joined["bids_subject"].eq(joined["source_bids_subject"]).all(), "H5/source BIDS subject mismatch")
    require(joined["fold_subject"].eq(joined["source_subject"]).all(), "Fold/source participant grouping ID mismatch")
    require(joined["pid"].eq(joined["source_pid"]).all(), "H5/source PID mismatch")
    require(np.isclose(joined["chart_window_start_sec"], joined["source_t_start"], rtol=0.0, atol=TIME_TOLERANCE_SECONDS).all(),
            "H5/source window-start mismatch")
    require(np.isclose(joined["chart_window_end_sec"], joined["source_t_end"], rtol=0.0, atol=TIME_TOLERANCE_SECONDS).all(),
            "H5/source window-end mismatch")

    ledger = {}
    for fold_info in fold_records:
        manifest = read_json(SOURCE_ARTICLE / fold_info["fold_manifest"])
        for file_name, digest in manifest["source_file_sha256"].items():
            ledger[(fold_info["fold"], str(file_name))] = str(digest)
    expected_hashes = joined.apply(lambda row: ledger[(int(row["fold"]), str(row["file"]))], axis=1)
    require(joined["source_sha256"].astype(str).eq(expected_hashes.astype(str)).all(),
            "Source-support hash differs from frozen fold manifest")

    cell_rows, actual_by_group = [], {}
    for _, block in joined.groupby(["fold", "fold_role", "pid", "file"], sort=True, dropna=False):
        rows, horizon_values = assess_recording(block)
        cell_rows.extend(rows)
        for (dimension, horizon), values in horizon_values.items():
            key = (int(block["fold"].iloc[0]), str(block["fold_role"].iloc[0]), dimension, horizon)
            actual_by_group.setdefault(key, []).extend(values)
    cells = pd.DataFrame(cell_rows).sort_values(
        ["fold", "fold_role", "pid", "file", "dimension", "horizon"], kind="stable"
    )
    summary = make_summary(cells, actual_by_group)
    support_counts = {
        "source_support_rows": int(len(support)), "source_support_recordings": int(support["file"].nunique()),
        "source_support_pids": int(support["pid"].nunique()),
        "source_support_eligible_rows": int(support["source_support_eligible"].sum()),
        "primary_surface_rows": int(len(primary_support)),
        "primary_surface_recordings": int(primary_support["file"].nunique()),
        "primary_surface_pids": int(primary_support["pid"].nunique()),
        "rows_with_input_sample_gaps": int(support["input_sample_gap_count"].fillna(0).gt(0).sum()),
        "rows_with_missing_gap_count": int(support["input_sample_gap_count"].isna().sum()),
    }

    output_root.mkdir(parents=True, exist_ok=False)
    pd.DataFrame(run_inventory).to_csv(output_root / "chart_run_inventory.csv", index=False)
    pd.DataFrame(fold_records).to_csv(output_root / "fold_inventory.csv", index=False)
    pd.DataFrame(h5_inventory).to_csv(output_root / "selected_h5_inventory.csv", index=False)
    cells.to_csv(output_root / "c1_path_support_by_fold_pid_recording.csv", index=False)
    summary.to_csv(output_root / "c1_path_support_summary.csv", index=False)

    result = {
        "schema_version": "boas.c1_outcome_blind_chart_preflight.v1",
        "verdict": "PARTIAL_PASS_OUTCOME_BLIND_C1_SUPPORT_PREFLIGHT",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Fold-safe chart identity, participant split, source-gap/segment and h1/h2/h4 support only; no chart values, score, contrast or effect estimate.",
        "measurement_boundary": {
            "measurement_implementation_changed": False, "numerical_behavior_changed": False,
            "measurement_semantics_changed": False, "mnps_definition_changed": False,
            "future_chart_numeric_values_read": False, "future_chart_values_scored": False,
            "sleep_stage_or_outcome_fields_parsed": False, "outcomes_calculated": False,
            "contrasts_computed": False, "full_cohort_scoring_authorized": False,
            "c1_score_amended_or_locked_by_this_preflight": False, "c2_feature_qualified": False,
        },
        "selected_surface": {
            "h5_files_in_qualification_directory": len(all_h5), "selected_h5_files": len(h5_inventory),
            "selected_runs": sorted(selected_names), "unselected_h5_files": len(all_h5) - len(h5_inventory),
            "coordinate_shapes_checked_only": {"3d": ["n_rows", 3], "9d": ["n_rows", 9]},
            "coordinate_arrays_read": False,
            "qc_metadata_read": ["mnps_3d_valid", "coords_9d_valid", "geometry_valid", "retained_after_qc"],
        },
        "folds": fold_records,
        "fold_partition": {
            "apply_pids_disjoint_across_folds": True,
            "apply_pids_cover_primary_surface": True,
            "unique_apply_pid_count": len(set(all_apply_pids)),
        },
        "run_manifests": run_records, "source_support": support_counts,
        "rows_bound_to_source_support": int(len(joined)),
        "input_projection_sha256": {
            "outcome_blind_source_support_columns": support_projection_hash,
            "h5_identity_time_and_qc_metadata": metadata_digest.hexdigest(),
        },
        "input_artifact_validation": artifact_validation,
        "horizon_support": {
            "history_rows_before_origin": HISTORY_ROWS, "horizon_row_lags": HORIZONS,
            "window_seconds": WINDOW_SECONDS, "primary_c1_support_cell": {"dimension": "3d", "horizon": "h1"},
            "secondary_support_cells": ([{"dimension": "3d", "horizon": h} for h in ("h2", "h4")]
                                        + [{"dimension": "9d", "horizon": h} for h in HORIZONS]),
            "summary_csv": "c1_path_support_summary.csv",
            "pid_recording_csv": "c1_path_support_by_fold_pid_recording.csv",
        },
        "limitations": [
            "Support/provenance preflight only; C1 score, effect protocol and authorization gate remain separate.",
            "H5 generic temporal support remains unknown and H5 source-quality status remains not_recorded; external row support remains a separate source-audit object.",
            "QC flags and timestamps are used only as metadata; no future coordinate array is opened.",
            "C2 remains unqualified; chart or nearest-neighbour payload presence is not an accessibility predictor qualification.",
        ],
    }
    (output_root / "validation.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    result = build(output_root)
    print(json.dumps({
        "verdict": result["verdict"], "output_root": str(output_root),
        "selected_h5_files": result["selected_surface"]["selected_h5_files"],
        "rows_bound_to_source_support": result["rows_bound_to_source_support"],
        "summary_csv": result["horizon_support"]["summary_csv"],
    }, indent=2))


if __name__ == "__main__":
    main()
