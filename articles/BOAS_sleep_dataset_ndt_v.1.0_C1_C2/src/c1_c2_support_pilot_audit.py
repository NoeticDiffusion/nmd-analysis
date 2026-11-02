"""Outcome-score-blind audit of the two-recording BOAS support pilot.

Reads only row identity/time/source-support columns from pilot Parquet, the
source-support audit, and selected fold-safe H5 metadata. It never loads feature
values or chart-coordinate datasets. Sidecar source-quality intervals are
summarized by source kind and checked against actual contributor bounds.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml


ARTICLE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ARTICLE = ARTICLE_ROOT.parent / "BOAS_sleep_dataset_ndt._v.1.0"
PILOT_ROOT = ARTICLE_ROOT / "results" / "producer_support_pilot_20261001"
CHART_DATA_ROOT = (
    SOURCE_ARTICLE
    / "results"
    / "fold_safe_chart_qualification_20260930_v1"
    / "processed"
    / "ds005555"
)
SUPPORT_AUDIT_PATH = (
    SOURCE_ARTICLE
    / "results"
    / "continuous_full_surface_support_audit_20260929_v4"
    / "row_support_audit.csv"
)
H5_INVENTORY_PATH = (
    ARTICLE_ROOT
    / "results"
    / "c1_outcome_blind_preflight_20260930_v1"
    / "selected_h5_inventory.csv"
)
OUTPUT_PATH = PILOT_ROOT / "validation.json"
PREFLIGHT_VALIDATION_PATH = ARTICLE_ROOT / "results" / "c1_outcome_blind_preflight_20260930_v1" / "validation.json"
PRODUCER_WORKTREE = Path(r"C:\Users\Robin\.codex\worktrees\boas-support-pilot\NeuralManifoldDynamics")
PRODUCER_CODE_FILES = [
    Path("mndm/src/mndm/preprocess.py"),
    Path("mndm/src/mndm/signal_support_provenance.py"),
    Path("mndm/src/mndm/features/eeg.py"),
]
PILOT_CONFIG_RELATIVE_PATH = Path("mndm/config/sources/openneuro/config_ingest_ds005555_continuous_c123_prediction_safe_pilot_20260929.yaml")
PILOT_CONFIG_PATH = PRODUCER_WORKTREE / PILOT_CONFIG_RELATIVE_PATH
PILOT_SUBJECTS = ("100", "105")

PILOT_COLUMNS = [
    "file",
    "epoch_id",
    "t_start",
    "t_end",
    "source_sample_mapping_status",
    "actual_sample_contributors_status",
    "actual_source_sample_start",
    "actual_source_sample_end_exclusive",
    "actual_source_time_start_sec",
    "actual_source_time_end_sec",
    "input_sample_finite_status",
    "input_sample_gap_count",
    "qc_ok_eeg",
    "qc_ok_ppg",
]
SUPPORT_COLUMNS = [
    "file",
    "epoch_id",
    "t_start",
    "t_end",
    "primary_surface_eligible",
    "support_exclusion_reasons",
    "source_sha256",
    "source_sample_mapping_status",
    "actual_sample_contributors_status",
    "actual_source_sample_start",
    "actual_source_sample_end_exclusive",
    "actual_source_time_start_sec",
    "actual_source_time_end_sec",
    "input_sample_finite_status",
    "input_sample_gap_count",
    "qc_ok_eeg",
    "qc_ok_ppg",
]
INVENTORY_COLUMNS = [
    "fold",
    "fold_role",
    "run_name",
    "bids_subject",
    "pid",
    "file",
    "h5_relative_path",
    "manifest_source_sha256",
]
TIME_COLUMNS = ["t_start", "t_end", "actual_source_time_start_sec", "actual_source_time_end_sec"]
SAMPLE_COLUMNS = ["actual_source_sample_start", "actual_source_sample_end_exclusive"]
STATUS_COLUMNS = [
    "source_sample_mapping_status",
    "actual_sample_contributors_status",
    "input_sample_finite_status",
    "input_sample_gap_count",
    "qc_ok_eeg",
    "qc_ok_ppg",
]


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


def text(value: Any) -> str:
    if isinstance(value, (bytes, np.bytes_)):
        return bytes(value).decode("utf-8", errors="strict")
    return str(value)


def numeric_equal(left: pd.Series, right: pd.Series, *, atol: float) -> bool:
    a = pd.to_numeric(left, errors="coerce").to_numpy(dtype=float)
    b = pd.to_numeric(right, errors="coerce").to_numpy(dtype=float)
    if a.shape != b.shape or not np.array_equal(np.isnan(a), np.isnan(b)):
        return False
    finite = np.isfinite(a) & np.isfinite(b)
    return bool(np.all(np.abs(a[finite] - b[finite]) <= atol))


def read_pilot_config_chain() -> tuple[list[tuple[Path, dict[str, Any]]], dict[str, Any]]:
    """Resolve and verify the declared YAML import chain without executing it."""
    require(PILOT_CONFIG_PATH.is_file(), f"Pilot config missing: {PILOT_CONFIG_PATH}")
    visited: set[Path] = set()
    ordered: list[tuple[Path, dict[str, Any]]] = []

    def visit(path: Path) -> None:
        resolved = path.resolve()
        require(resolved not in visited, f"Cycle or duplicate in pilot config imports: {resolved}")
        visited.add(resolved)
        content = yaml.safe_load(resolved.read_text(encoding="utf-8"))
        require(isinstance(content, dict), f"Pilot config is not a YAML mapping: {resolved}")
        imports = content.get("imports", [])
        require(isinstance(imports, list), f"Pilot config imports must be a list: {resolved}")
        for imported in imports:
            require(isinstance(imported, str), f"Unsupported pilot config import entry in {resolved}")
            child = (resolved.parent / imported).resolve()
            require(child.is_file(), f"Pilot config import missing: {child}")
            visit(child)
        ordered.append((resolved, content))

    visit(PILOT_CONFIG_PATH)
    root_config = next(config for path, config in ordered if path == PILOT_CONFIG_PATH.resolve())
    feature_flag = root_config.get("features", {}).get("read_sleep_stage_annotations")
    codebook_declarations = [
        (path, config.get("mnps", {}).get("stage_codebook", {}).get("PSG_disconnection"))
        for path, config in ordered
        if isinstance(config.get("mnps", {}).get("stage_codebook", {}), dict)
        and "PSG_disconnection" in config.get("mnps", {}).get("stage_codebook", {})
    ]
    config_checks = {
        "all_declared_imports_resolved": True,
        "feature_sleep_stage_annotation_read_disabled": feature_flag is False,
        "psg_disconnection_code_8_declared": bool(codebook_declarations)
        and all(value == 8 for _, value in codebook_declarations),
        "stage_codebook_declarations": [
            {"path": path.relative_to(PRODUCER_WORKTREE).as_posix(), "PSG_disconnection": value}
            for path, value in codebook_declarations
        ],
        "feature_sleep_stage_annotation_read_flag": feature_flag,
    }
    return ordered, config_checks


def checked_interval_bounds(collection: Any, *, name: str) -> tuple[list[tuple[float, float, str]], dict[str, Any]]:
    """Fail closed on absent, malformed, or internally inconsistent quality intervals."""
    require(isinstance(collection, dict), f"Quality interval collection missing or malformed: {name}")
    status = collection.get("status")
    raw_intervals = collection.get("intervals")
    require(isinstance(raw_intervals, list), f"Quality intervals must be a list: {name}")
    declared_count = collection.get("interval_count")
    if declared_count is not None:
        require(int(declared_count) == len(raw_intervals), f"Quality interval count disagrees with payload: {name}")
    require(status in {"observed", "none_observed"}, f"Unqualified quality interval status {status!r}: {name}")
    require((status == "observed") == bool(raw_intervals), f"Quality interval status/count conflict: {name}")

    bounds: list[tuple[float, float, str]] = []
    for index, item in enumerate(raw_intervals):
        require(isinstance(item, dict), f"Quality interval entry is malformed: {name}[{index}]")
        try:
            start, end = float(item["start_sec"]), float(item["end_sec"])
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError(f"Quality interval bounds are missing or nonnumeric: {name}[{index}]") from error
        require(np.isfinite([start, end]).all() and end > start, f"Invalid quality interval bounds: {name}[{index}]")
        bounds.append((start, end, str(item.get("source_kind", name))))
    return bounds, {"status": status, "interval_count": len(bounds), "invalid_interval_count": 0}


def read_pilot_rows(subject: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    ds_root = PILOT_ROOT / f"sub-{subject}" / "ds005555"
    parquet_path = ds_root / "features.parquet"
    qc_path = ds_root / "qc_artifacts" / f"sub-{subject}_task-Sleep_acq-psg_eeg_qc_artifacts.json"
    meta_path = ds_root / "intermediate" / f"sub-{subject}_task-Sleep_acq-psg_eeg.meta.json"
    require(parquet_path.is_file() and qc_path.is_file() and meta_path.is_file(), f"Pilot outputs incomplete for sub-{subject}")
    parquet = pq.ParquetFile(parquet_path)
    require(set(PILOT_COLUMNS).issubset(parquet.schema.names), f"Required support columns absent for sub-{subject}")
    # Explicit column projection prevents reading EEG/PPG feature values.
    frame = pq.read_table(parquet_path, columns=PILOT_COLUMNS).to_pandas()
    frame["file"] = frame["file"].map(basename)
    frame["epoch_id"] = pd.to_numeric(frame["epoch_id"], errors="raise").astype(np.int64)
    require(not frame.duplicated(["file", "epoch_id"]).any(), f"Duplicate pilot file/epoch rows for sub-{subject}")
    qc = json.loads(qc_path.read_text(encoding="utf-8"))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return frame, {
        "dataset_root": str(ds_root),
        "feature_rows": int(len(frame)),
        "feature_columns_count": int(len(parquet.schema.names)),
        "stage_named_columns_present": any(
            name.casefold() == "stage" or name.casefold().startswith("stage_")
            for name in parquet.schema.names
        ),
        "qc_sidecar_sha256": sha256_file(qc_path),
        "meta_sidecar_sha256": sha256_file(meta_path),
        "meta": meta,
        "qc": qc,
    }


def read_source_audit() -> pd.DataFrame:
    require(SUPPORT_AUDIT_PATH.is_file(), f"Source-support audit missing: {SUPPORT_AUDIT_PATH}")
    frame = pd.read_csv(
        SUPPORT_AUDIT_PATH,
        usecols=SUPPORT_COLUMNS,
        dtype={name: "string" for name in ("file", "support_exclusion_reasons", "source_sha256", "source_sample_mapping_status", "actual_sample_contributors_status", "input_sample_finite_status")},
        low_memory=False,
    )
    frame["file"] = frame["file"].map(basename)
    frame["epoch_id"] = pd.to_numeric(frame["epoch_id"], errors="raise").astype(np.int64)
    require(not frame.duplicated(["file", "epoch_id"]).any(), "Duplicate source-support file/epoch rows")
    return frame


def read_h5_identity(path: Path) -> tuple[pd.DataFrame, str, int]:
    with h5py.File(path, "r") as h5:
        require("epoch_id" in h5 and "time" in h5 and "window_start" in h5 and "window_end" in h5, f"H5 identity/time fields missing: {path}")
        require("row_source/raw_file" in h5, f"H5 raw-file identity missing: {path}")
        epoch = np.asarray(h5["epoch_id"][:], dtype=np.int64)
        center = np.asarray(h5["time"][:], dtype=float)
        start = np.asarray(h5["window_start"][:], dtype=float)
        end = np.asarray(h5["window_end"][:], dtype=float)
        raw_files = [basename(text(value)) for value in np.asarray(h5["row_source/raw_file"][:]).tolist()]
        require(epoch.ndim == center.ndim == start.ndim == end.ndim == 1, f"H5 identity fields have invalid rank: {path}")
        require(len(epoch) == len(center) == len(start) == len(end) == len(raw_files), f"H5 identity field lengths differ: {path}")
        require(len(set(raw_files)) == 1, f"H5 contains multiple raw files: {path}")
        require(not pd.Index(epoch).has_duplicates, f"Duplicate H5 epoch identities: {path}")
        return pd.DataFrame({"file": raw_files, "epoch_id": epoch, "h5_time": center, "h5_t_start": start, "h5_t_end": end}), raw_files[0], int(h5.attrs["meta_pid"])


def collect_quality_bounds(qc: dict[str, Any]) -> tuple[list[tuple[float, float, str]], dict[str, Any]]:
    support = qc.get("signal_support_provenance", {})
    source_quality = support.get("source_quality_intervals", {})
    flatline = support.get("raw_joint_eeg_flatline_qc", {})
    source_bounds, source_status = checked_interval_bounds(source_quality, name="source_quality_intervals")
    flatline_bounds, flatline_status = checked_interval_bounds(flatline, name="raw_joint_eeg_flatline_qc")
    all_bounds = source_bounds + flatline_bounds
    policy = qc.get("quality_interval_policy", {})
    selected_count = policy.get("selected_source_interval_count")
    require(selected_count is not None and int(selected_count) == len(all_bounds),
            "Selected quality-interval count disagrees with source-quality and raw-flatline interval payloads")
    return all_bounds, {
        "source_quality_interval_collection": source_status,
        "raw_flatline_interval_collection": flatline_status,
        "combined_interval_count": len(all_bounds),
        "quality_policy_selected_interval_count": int(selected_count),
        "all_interval_bounds_valid": True,
    }


def summarize_quality(qc: dict[str, Any], interval_audit: dict[str, Any]) -> dict[str, Any]:
    support = qc.get("signal_support_provenance", {})
    source = support.get("source", {})
    source_quality = support.get("source_quality_intervals", {})
    intervals = source_quality.get("intervals", [])
    interval_counts = Counter(str(item.get("source_kind", "unknown")) for item in intervals if isinstance(item, dict))
    event_hashes = sorted({
        str(item.get("source_sha256"))
        for item in intervals
        if isinstance(item, dict) and item.get("source_kind") == "source_stage_hum_code_8" and item.get("source_sha256")
    })
    event_paths = sorted({
        str(item.get("source_path"))
        for item in intervals
        if isinstance(item, dict) and item.get("source_kind") == "source_stage_hum_code_8" and item.get("source_path")
    })
    raw_flatline = support.get("raw_joint_eeg_flatline_qc", {})
    intersection = qc.get("quality_interval_epoch_intersection", {})
    return {
        "source_sha256": source.get("sha256"),
        "source_sha256_after": source.get("sha256_after"),
        "source_exists": source.get("exists"),
        "source_hash_stable": source.get("hash_stable"),
        "support_schema": support.get("schema"),
        "support_status": support.get("status"),
        "temporal_support_mode": support.get("temporal_support_mode"),
        "edf_grid_status": support.get("edf_sample_grid", {}).get("status"),
        "edf_continuity_status": support.get("edf_sample_grid", {}).get("continuity_status"),
        "effective_support_status": support.get("effective_time_support", {}).get("status"),
        "effective_support_mode": support.get("effective_time_support", {}).get("mode"),
        "identity_grid_method": support.get("effective_time_support", {}).get("resampler", {}).get("method"),
        "identity_grid_coefficient_sha256": support.get("effective_time_support", {}).get("resampler", {}).get("coefficient_sha256"),
        "eeg_filter_method": support.get("effective_time_support", {}).get("eeg_bandpass", {}).get("method"),
        "eeg_filter_phase": support.get("effective_time_support", {}).get("eeg_bandpass", {}).get("phase"),
        "eeg_filter_tap_count": support.get("effective_time_support", {}).get("eeg_bandpass", {}).get("tap_count"),
        "eeg_filter_coefficient_sha256": support.get("effective_time_support", {}).get("eeg_bandpass", {}).get("coefficient_sha256"),
        "source_quality_status": source_quality.get("status"),
        "source_quality_annotation_status": source_quality.get("annotation_status"),
        "stage_hum_code_8_quality_status": source_quality.get("source_stage_hum_code_8_status"),
        "source_quality_interval_counts_by_kind": dict(sorted(interval_counts.items())),
        "stage_hum_code_8_event_hashes": event_hashes,
        "stage_hum_code_8_event_paths": event_paths,
        "flatline_interval_count": raw_flatline.get("interval_count"),
        "quality_policy_status": qc.get("quality_interval_policy", {}).get("status"),
        "quality_policy_selected_interval_count": qc.get("quality_interval_policy", {}).get("selected_source_interval_count"),
        "validated_quality_interval_collections": interval_audit,
        "quality_epoch_intersection_status": intersection.get("status"),
        "quality_epoch_rows_before": intersection.get("rows_before"),
        "quality_epoch_rows_after": intersection.get("rows_after"),
        "feature_source_time_grid": {
            "rows_before": intersection.get("rows_before"),
            "rows_after": intersection.get("rows_after"),
        },
    }


def audit_subject(subject: str, source_audit: pd.DataFrame, inventory: pd.DataFrame) -> dict[str, Any]:
    pilot, pilot_info = read_pilot_rows(subject)
    raw_file = f"sub-{subject}_task-Sleep_acq-psg_eeg.edf"
    pilot = pilot.loc[pilot["file"].eq(raw_file)].copy()
    require(not pilot.empty, f"Pilot table has no expected PSG rows for sub-{subject}")

    support = source_audit.loc[source_audit["file"].eq(raw_file)].copy()
    require(not support.empty, f"Source audit has no rows for {raw_file}")
    source_hashes = sorted(set(support["source_sha256"].dropna().astype(str)))
    require(len(source_hashes) == 1, f"Source audit has inconsistent source hashes for {raw_file}")

    candidates = inventory.loc[
        inventory["file"].map(basename).eq(raw_file)
        & inventory["fold_role"].astype(str).eq("apply")
    ]
    require(len(candidates) == 1, f"Expected one apply H5 inventory row for {raw_file}; found {len(candidates)}")
    h5_item = candidates.iloc[0]
    h5_path = CHART_DATA_ROOT / str(h5_item["h5_relative_path"])
    require(h5_path.is_file(), f"Selected apply H5 missing: {h5_path}")
    h5_rows, h5_raw_file, h5_pid = read_h5_identity(h5_path)

    pilot = pilot.sort_values(["file", "epoch_id"]).reset_index(drop=True)
    support = support.sort_values(["file", "epoch_id"]).reset_index(drop=True)
    h5_rows = h5_rows.sort_values(["file", "epoch_id"]).reset_index(drop=True)
    require(pilot[["file", "epoch_id"]].equals(support[["file", "epoch_id"]]), f"Pilot/source support key mismatch for {raw_file}")
    pilot_keys = set(zip(pilot["file"].astype(str), pilot["epoch_id"].astype(int)))
    h5_keys = set(zip(h5_rows["file"].astype(str), h5_rows["epoch_id"].astype(int)))
    primary_eligible_mask = support["primary_surface_eligible"].astype(str).str.strip().str.lower().isin({"true", "1", "yes"})
    eligible_keys = set(zip(
        support.loc[primary_eligible_mask, "file"].astype(str),
        support.loc[primary_eligible_mask, "epoch_id"].astype(int),
    ))
    require(h5_keys.issubset(pilot_keys), f"H5 contains rows absent from the raw-EDF pilot for {raw_file}")
    require(h5_keys == eligible_keys, f"Apply-H5 keys do not equal primary-surface-eligible source-support keys for {raw_file}")
    pilot_h5 = pilot.merge(h5_rows, on=["file", "epoch_id"], how="inner", validate="one_to_one", sort=True)

    exact_checks: dict[str, bool] = {}
    for column in TIME_COLUMNS:
        exact_checks[f"pilot_matches_source_{column}"] = numeric_equal(pilot[column], support[column], atol=1e-9)
    for column in SAMPLE_COLUMNS:
        exact_checks[f"pilot_matches_source_{column}"] = numeric_equal(pilot[column], support[column], atol=0.0)
    for column in STATUS_COLUMNS:
        if column == "input_sample_gap_count":
            exact_checks[f"pilot_matches_source_{column}"] = numeric_equal(pilot[column], support[column], atol=0.0)
        else:
            a = pilot[column].astype("string").fillna("<NA>")
            b = support[column].astype("string").fillna("<NA>")
            exact_checks[f"pilot_matches_source_{column}"] = bool(a.equals(b))
    exact_checks["h5_apply_keys_equal_primary_surface_support_keys"] = h5_keys == eligible_keys
    exact_checks["h5_apply_keys_are_subset_of_pilot_keys"] = h5_keys.issubset(pilot_keys)
    exact_checks["pilot_t_start_matches_h5_window_start"] = numeric_equal(pilot_h5["t_start"], pilot_h5["h5_t_start"], atol=1e-9)
    exact_checks["pilot_t_end_matches_h5_window_end"] = numeric_equal(pilot_h5["t_end"], pilot_h5["h5_t_end"], atol=1e-9)
    exact_checks["pilot_stage_column_absent"] = not pilot_info["stage_named_columns_present"]
    center = (pd.to_numeric(pilot_h5["t_start"], errors="coerce") + pd.to_numeric(pilot_h5["t_end"], errors="coerce")) / 2.0
    exact_checks["h5_time_matches_window_midpoint"] = numeric_equal(center, pilot_h5["h5_time"], atol=1e-9)

    pilot_info["h5_apply_path"] = str(h5_path)
    pilot_info["source_file"] = raw_file
    pilot_info["h5_raw_file_identity_matches"] = h5_raw_file == raw_file
    pilot_info["h5_pid_matches_inventory"] = int(h5_item["pid"]) == h5_pid
    pilot_info["source_sha256_pilot"] = pilot_info["qc"].get("signal_support_provenance", {}).get("source", {}).get("sha256")
    pilot_info["source_sha256_source_audit"] = source_hashes[0]
    pilot_info["source_sha256_h5_manifest"] = str(h5_item["manifest_source_sha256"])
    pilot_info["source_hashes_match"] = (
        pilot_info["source_sha256_pilot"]
        == pilot_info["source_sha256_source_audit"]
        == pilot_info["source_sha256_h5_manifest"]
        and pilot_info["qc"].get("signal_support_provenance", {}).get("source", {}).get("sha256_after")
        == pilot_info["source_sha256_pilot"]
        and pilot_info["qc"].get("signal_support_provenance", {}).get("source", {}).get("hash_stable") is True
    )

    quality_bounds, interval_audit = collect_quality_bounds(pilot_info["qc"])
    exact_checks["quality_interval_bounds_and_counts_valid"] = interval_audit["all_interval_bounds_valid"]
    exact_checks["quality_policy_selected_interval_count_matches_payload"] = (
        interval_audit["quality_policy_selected_interval_count"] == interval_audit["combined_interval_count"]
    )
    starts = pd.to_numeric(pilot["actual_source_time_start_sec"], errors="coerce").to_numpy(dtype=float)
    ends = pd.to_numeric(pilot["actual_source_time_end_sec"], errors="coerce").to_numpy(dtype=float)
    interval_row_hits = Counter()
    intersected_rows_by_kind: dict[str, set[int]] = {}
    quality_interval_overlap_details = []
    for start, end, kind in quality_bounds:
        mask = np.isfinite(starts) & np.isfinite(ends) & (starts < end) & (start < ends)
        interval_row_hits[kind] += int(np.count_nonzero(mask))
        indices = np.flatnonzero(mask).tolist()
        intersected_rows_by_kind.setdefault(kind, set()).update(indices)
        if indices:
            epoch_ids = [int(pilot.iloc[index]["epoch_id"]) for index in indices]
            quality_interval_overlap_details.append({
                "source_kind": kind,
                "interval_start_sec": start,
                "interval_end_sec": end,
                "overlapping_epoch_ids": epoch_ids,
                "overlapping_apply_h5_epoch_ids": [epoch for epoch in epoch_ids if (raw_file, epoch) in h5_keys],
            })
    any_intersection_rows = np.zeros(len(pilot), dtype=bool)
    for start, end, _ in quality_bounds:
        any_intersection_rows |= np.isfinite(starts) & np.isfinite(ends) & (starts < end) & (start < ends)
    primary_eligible = primary_eligible_mask.to_numpy()
    overlap_indices = np.flatnonzero(any_intersection_rows)
    overlap_records = []
    for index in overlap_indices:
        key = (raw_file, int(pilot.iloc[index]["epoch_id"]))
        overlap_records.append({
            "epoch_id": key[1],
            "actual_source_time_start_sec": float(starts[index]),
            "actual_source_time_end_sec": float(ends[index]),
            "intersecting_quality_kinds": sorted(
                kind for kind, indices in intersected_rows_by_kind.items() if index in indices
            ),
            "primary_surface_eligible": bool(primary_eligible[index]),
            "included_in_apply_h5": key in h5_keys,
        })
    h5_quality_intersection_rows = int(sum(record["included_in_apply_h5"] for record in overlap_records))

    pilot_info["support_row_counts"] = {
        "pilot_rows": int(len(pilot)),
        "source_audit_rows": int(len(support)),
        "h5_rows": int(len(h5_rows)),
        "source_audit_primary_eligible_rows": int(primary_eligible.sum()),
        "source_audit_primary_ineligible_rows": int((~primary_eligible).sum()),
        "h5_keys_equal_source_primary_eligible_keys": bool(h5_keys == eligible_keys),
        "pilot_actual_contributor_finite_rows": int((np.isfinite(starts) & np.isfinite(ends)).sum()),
        "pilot_source_gap_rows": int((pd.to_numeric(pilot["input_sample_gap_count"], errors="coerce") > 0).sum()),
        "quality_interval_row_hits_by_kind": dict(sorted(interval_row_hits.items())),
        "rows_with_quality_interval_intersection_by_kind": {
            kind: len(indices) for kind, indices in sorted(intersected_rows_by_kind.items())
        },
        "rows_with_any_source_quality_intersection": int(any_intersection_rows.sum()),
        "source_quality_intersection_epoch_ids": pilot.loc[any_intersection_rows, "epoch_id"].astype(int).tolist(),
        "source_primary_ineligible_epoch_ids": support.loc[~primary_eligible, "epoch_id"].astype(int).tolist(),
        "quality_overlap_records": overlap_records,
        "quality_interval_overlap_details": quality_interval_overlap_details,
        "quality_intersection_rows_still_primary_eligible": int((any_intersection_rows & primary_eligible).sum()),
        "quality_intersection_rows_present_in_apply_h5": h5_quality_intersection_rows,
    }
    pilot_info["identity_support_checks"] = exact_checks
    pilot_info["identity_support_checks_pass"] = bool(
        all(exact_checks.values())
        and pilot_info["h5_raw_file_identity_matches"]
        and pilot_info["h5_pid_matches_inventory"]
        and pilot_info["source_hashes_match"]
        and pilot_info["support_row_counts"]["quality_intersection_rows_still_primary_eligible"] == 0
        and pilot_info["support_row_counts"]["quality_intersection_rows_present_in_apply_h5"] == 0
    )
    pilot_info["source_quality"] = summarize_quality(pilot_info["qc"], interval_audit)
    pilot_info.pop("qc")
    return pilot_info


def main() -> int:
    require(SUPPORT_AUDIT_PATH.is_file(), f"Source-support audit missing: {SUPPORT_AUDIT_PATH}")
    require(H5_INVENTORY_PATH.is_file(), f"Selected-H5 inventory missing: {H5_INVENTORY_PATH}")
    source_audit = read_source_audit()
    inventory = pd.read_csv(H5_INVENTORY_PATH, usecols=INVENTORY_COLUMNS, dtype={"file": "string", "fold_role": "string", "h5_relative_path": "string", "manifest_source_sha256": "string"})
    config_chain, config_checks = read_pilot_config_chain()
    require(config_checks["feature_sleep_stage_annotation_read_disabled"],
            "Pilot config does not explicitly disable sleep-stage annotation reads")
    require(config_checks["psg_disconnection_code_8_declared"],
            "Pilot config import chain does not consistently map PSG_disconnection to code 8")
    rows = [audit_subject(subject, source_audit, inventory) for subject in PILOT_SUBJECTS]
    require(PREFLIGHT_VALIDATION_PATH.is_file(), f"Outcome-blind preflight validation missing: {PREFLIGHT_VALIDATION_PATH}")
    preflight = json.loads(PREFLIGHT_VALIDATION_PATH.read_text(encoding="utf-8"))
    source_projection_sha256 = preflight.get("input_projection_sha256", {}).get("outcome_blind_source_support_columns")
    require(bool(source_projection_sha256), "Outcome-blind source-support projection digest missing from prior validation")
    producer_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=PRODUCER_WORKTREE, capture_output=True, text=True, check=True
    ).stdout.strip()
    producer_status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=PRODUCER_WORKTREE, capture_output=True, text=True, check=True
    ).stdout
    producer_hashes = {
        path.as_posix(): sha256_file(PRODUCER_WORKTREE / path)
        for path in PRODUCER_CODE_FILES
    }
    config_hashes = {
        path.relative_to(PRODUCER_WORKTREE).as_posix(): sha256_file(path)
        for path, _ in config_chain
    }
    validation = {
        "schema_version": "boas.c1_c2_support_pilot_audit.v2",
        "verdict": "PARTIAL_PASS_TWO_RECORDING_SUPPORT_PILOT" if all(row["identity_support_checks_pass"] for row in rows) and all(config_checks[key] for key in ("feature_sleep_stage_annotation_read_disabled", "psg_disconnection_code_8_declared")) else "INCOMPLETE_TWO_RECORDING_SUPPORT_PILOT",
        "scope": "Two-recording raw-EDF feature/support replay linked to selected apply-H5 identity/time/source metadata; no prediction or effect scoring.",
        "producer": {
            "worktree": str(PRODUCER_WORKTREE),
            "base_revision": "2b61d3eca37dfca4892dee488ad211e3f7ae037d",
            "checkout_revision_at_audit": producer_commit,
            "checkout_clean_at_audit": not bool(producer_status.strip()),
            "execution_revision_embedded_in_feature_sidecars": False,
            "execution_revision_captured_at_run_time": False,
            "mndm_version": rows[0]["meta"].get("mndm_version"),
            "python_version": platform.python_version(),
            "code_sha256": producer_hashes,
            "resolved_import_chain_config_sha256": config_hashes,
            "config_contract_checks": config_checks,
        },
        "outcome_boundary": {
            "chart_coordinate_arrays_read": False,
            "future_chart_values_read": False,
            "predictions_or_scores_calculated": False,
            "feature_values_generated_by_pilot_but_not_loaded_by_audit": True,
            "feature_stage_named_columns_present": [row["stage_named_columns_present"] for row in rows],
            "feature_sleep_stage_annotation_read_disabled_in_config": config_checks["feature_sleep_stage_annotation_read_disabled"],
            "stage_hum_code_8_mapping_verified_in_config_chain": config_checks["psg_disconnection_code_8_declared"],
            "stage_hum_code_8_semantics_from_config": "PSG_disconnection" if config_checks["psg_disconnection_code_8_declared"] else None,
        },
        "source_support_audit_path": str(SUPPORT_AUDIT_PATH),
        "source_support_projection_sha256_from_outcome_blind_preflight": source_projection_sha256,
        "prior_preflight_validation_sha256": sha256_file(PREFLIGHT_VALIDATION_PATH),
        "selected_h5_inventory_path": str(H5_INVENTORY_PATH),
        "pilot_subjects": rows,
    }
    OUTPUT_PATH.write_text(json.dumps(validation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": validation["verdict"],
        "output": str(OUTPUT_PATH),
        "subjects": [
            {
                "source_file": row["source_file"],
                "pilot_rows": row["feature_rows"],
                "identity_support_checks_pass": row["identity_support_checks_pass"],
                "source_hashes_match": row["source_hashes_match"],
                "quality": row["source_quality"]["source_quality_status"],
                "quality_intersections": row["support_row_counts"]["rows_with_quality_interval_intersection_by_kind"],
                "quality_intersection_rows_still_primary_eligible": row["support_row_counts"]["quality_intersection_rows_still_primary_eligible"],
            }
            for row in rows
        ],
    }, indent=2, ensure_ascii=False))
    return 0 if validation["verdict"] == "PARTIAL_PASS_TWO_RECORDING_SUPPORT_PILOT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
