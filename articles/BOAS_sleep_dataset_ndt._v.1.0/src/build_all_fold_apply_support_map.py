"""Build an outcome-blind apply-chart/support crosswalk across all five folds."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import yaml


ARTICLE_ROOT = Path(__file__).resolve().parents[1]
RESULTS_ROOT = ARTICLE_ROOT / "results"
CHART_ROOT = RESULTS_ROOT / "fold_safe_chart_qualification_20260930_v1"
V4_ROOT = RESULTS_ROOT / "continuous_full_surface_support_audit_20260929_v4"
DEFAULT_OUTPUT = CHART_ROOT / "support_map_all_folds_v3"

KEYS = ["file", "epoch_id"]
FEATURE_COLUMNS = [
    "file", "subject", "epoch_id", "t_start", "t_end", "source_stratum",
    "source_sample_mapping_status", "source_sample_mapping_reason",
    "nominal_source_sample_start", "nominal_source_sample_end_exclusive",
    "source_sfreq_hz", "actual_sample_contributors_status",
    "actual_sample_contributors_reason", "actual_source_sample_start",
    "actual_source_sample_end_exclusive", "actual_source_time_start_sec",
    "actual_source_time_end_sec", "input_sample_finite_status", "input_sample_gap_count",
]
ROW_AUDIT_COLUMNS = [
    "file", "subject", "bids_subject", "epoch_id", "t_start", "t_end",
    "source_stratum", "recording_proxy_sources", "row_proxy_source",
    "proxy_matches_ppg_rate", "base_support_eligible", "primary_surface_eligible",
    "support_exclusion_reasons", "source_sha256", "source_sample_mapping_status",
    "source_sample_mapping_reason", "nominal_source_sample_start",
    "nominal_source_sample_end_exclusive", "actual_sample_contributors_status",
    "actual_source_sample_start", "actual_source_sample_end_exclusive",
    "actual_source_time_start_sec", "actual_source_time_end_sec", "source_sfreq_hz",
    "input_sample_finite_status", "input_sample_gap_count", "qc_ok_eeg", "qc_ok_ppg",
]
RECORDING_AUDIT_COLUMNS = [
    "file", "source_stratum", "recording_proxy_sources", "feature_rows",
    "base_support_eligible_rows", "primary_surface_eligible_rows",
    "support_record_status", "support_record_reasons", "source_sha256",
]
SUPPORT_COMPARE_COLUMNS = [
    "source_stratum", "source_sample_mapping_status", "source_sample_mapping_reason",
    "nominal_source_sample_start", "nominal_source_sample_end_exclusive",
    "source_sfreq_hz", "actual_sample_contributors_status",
    "actual_source_sample_start", "actual_source_sample_end_exclusive",
    "actual_source_time_start_sec", "actual_source_time_end_sec",
    "input_sample_finite_status", "input_sample_gap_count",
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


def read_pretty_json_string_field(path: Path, field: str) -> str:
    """Read one string-valued field from a pretty-printed JSON object by line."""
    matches: list[str] = []
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            key, separator, value = line.partition(":")
            if separator and key.strip().strip('"') == field:
                matches.append(json.loads(value.strip().rstrip(",")))
    require(len(matches) == 1 and isinstance(matches[0], str), f"Expected one string field {field!r} in {path}")
    return matches[0]


def text(value: Any) -> str:
    if isinstance(value, (bytes, np.bytes_)):
        return bytes(value).decode("utf-8", errors="strict")
    return str(value)


def version_suffix(fold: int) -> str:
    return "v2" if fold == 0 else "v1"


def same_path(left: str | Path, right: str | Path) -> bool:
    return Path(left).resolve().as_posix().casefold() == Path(right).resolve().as_posix().casefold()


def validate_copied_yaml(provided_path: Path, copied_path: Path) -> str:
    require(provided_path.is_file() and copied_path.is_file(), "Provided/copied YAML file is missing")
    provided_hash = sha256_file(provided_path)
    copied_hash = sha256_file(copied_path)
    require(provided_hash == copied_hash, f"Copied YAML differs from provided config: {copied_path}")
    return copied_hash


def validate_run_config(
    *, fold: int, role: str, run_dir: Path, manifest_path: Path, ledger_path: Path,
    anchor_path: Path, anchor_id: str,
) -> tuple[dict[str, Any], Path, str]:
    suffix = version_suffix(fold)
    expected_run_name = f"fold_{fold}_{role}_label_free_{suffix}"
    expected_run_dir = CHART_ROOT / "processed" / "ds005555" / expected_run_name
    expected_config_path = CHART_ROOT / "configs" / f"{expected_run_name}.yaml"
    run_manifest_path = run_dir / "run_manifest.json"
    require(same_path(run_dir, expected_run_dir), f"Unexpected {role} run directory for fold {fold}")
    require(run_manifest_path.is_file() and expected_config_path.is_file(), f"Missing {role} run/config for fold {fold}")
    run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    extra = run_manifest.get("extra", {})
    require(run_manifest.get("dataset_id") == "ds005555", f"Unexpected dataset in {role} run: fold {fold}")
    require(run_manifest.get("run_name") == expected_run_name, f"Unexpected run name: fold {fold}/{role}")
    require(same_path(run_manifest.get("run_dir", ""), expected_run_dir), f"Run-manifest path mismatch: fold {fold}/{role}")
    require(extra.get("run_status") == "completed", f"{role} run incomplete: fold {fold}")
    require(extra.get("run_errors", {}).get("count") == 0, f"{role} run has errors: fold {fold}")
    require(extra.get("skipped_recordings", {}).get("count") == 0, f"{role} run skipped recordings: fold {fold}")
    require(extra.get("stage_mapping_qc", {}).get("status") == "none", f"Stage mapping present in {role} run: fold {fold}")
    support = extra.get("signal_support_provenance", {})
    require(support.get("status") == "unknown" and support.get("temporal_support_status") == "unknown", f"Unexpected generic support status in {role} run: fold {fold}")

    source = run_manifest.get("config", {}).get("yaml_source", {})
    require(source.get("status") == "copied", f"{role} config not recorded as copied: fold {fold}")
    require(same_path(source.get("provided_path", ""), expected_config_path), f"Unexpected provided config path: fold {fold}/{role}")
    copied_config_path = Path(source.get("copied_path", ""))
    require(same_path(copied_config_path, run_dir / expected_config_path.name), f"Unexpected copied config path: fold {fold}/{role}")
    validate_copied_yaml(expected_config_path, copied_config_path)
    digest = run_manifest.get("config", {}).get("digest_sha256")
    require(isinstance(digest, str) and len(digest) == 64, f"Missing resolved config digest: fold {fold}/{role}")
    require(same_path(run_manifest.get("paths", {}).get("processed_dir", ""), CHART_ROOT / "processed"), f"Unexpected processed root: fold {fold}/{role}")

    config = yaml.safe_load(expected_config_path.read_text(encoding="utf-8"))
    require(same_path(config.get("paths", {}).get("processed_dir", ""), CHART_ROOT / "processed"), f"Config processed root mismatch: fold {fold}/{role}")
    projection = config.get("mnps_projection", {})
    fold_safe = projection.get("fold_safe", {})
    require(fold_safe.get("enabled") is True, f"Fold-safe mode disabled: fold {fold}/{role}")
    require(same_path(fold_safe.get("manifest", ""), manifest_path), f"Fold manifest mismatch: fold {fold}/{role}")
    require(fold_safe.get("role") == role, f"Fold role mismatch in config: fold {fold}/{role}")
    require(same_path(fold_safe.get("signal_support_ledger", ""), ledger_path), f"Support ledger mismatch: fold {fold}/{role}")
    fit = projection.get("anchor_auto_fit", {})
    anchor = projection.get("anchor", {})
    require(fit.get("anchor_id") == anchor_id, f"Fit anchor ID mismatch: fold {fold}/{role}")
    if role == "training":
        require(fit.get("enabled") is True and anchor.get("enabled") is False, f"Training anchor fit semantics mismatch: fold {fold}")
    else:
        require(fit.get("enabled") is False and anchor.get("enabled") is True, f"Apply anchor reuse semantics mismatch: fold {fold}")
        require(same_path(anchor.get("path", ""), anchor_path), f"Apply config references wrong training anchor: fold {fold}")
    return run_manifest, expected_config_path, digest


def validate_label_free_h5(h5: h5py.File, h5_path: Path) -> int:
    mapping_path = "provenance/event_stage_mapping"
    require(mapping_path in h5 and isinstance(h5[mapping_path], h5py.Group), f"Missing empty event/stage mapping group: {h5_path}")
    require(len(h5[mapping_path].keys()) == 0, f"Event/stage mapping payload present: {h5_path}")
    def require_empty_codebook(value: Any, location: str) -> None:
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="strict")
        require(json.loads(str(value)) == {}, f"Non-empty H5 stage codebook: {h5_path}:{location}")

    require_empty_codebook(h5.attrs.get("stage_codebook", "{}"), "root:stage_codebook")

    empty_label_datasets = 0

    def visit(name: str, obj: h5py.Group | h5py.Dataset) -> None:
        nonlocal empty_label_datasets
        for attr_name in obj.attrs:
            lowered_attr = attr_name.lower()
            if any(token in lowered_attr for token in ("stage", "label", "event")):
                if not name and attr_name == "stage_codebook":
                    require_empty_codebook(obj.attrs[attr_name], "root:stage_codebook")
                    continue
                raise RuntimeError(f"Unexpected stage/label/event H5 object attribute: {h5_path}:{name}:{attr_name}")
        lowered = name.lower()
        if not any(token in lowered for token in ("stage", "label", "event")):
            return
        if name == mapping_path and isinstance(obj, h5py.Group) and len(obj.keys()) == 0:
            return
        if isinstance(obj, h5py.Dataset) and name.endswith("/metadata/group_label"):
            values = np.asarray(obj[:]).reshape(-1)
            require(all(text(value).strip() == "" for value in values), f"Non-empty group-label payload: {h5_path}:{name}")
            empty_label_datasets += 1
            return
        raise RuntimeError(f"Unexpected stage/label/event H5 object: {h5_path}:{name}")

    h5.visititems(visit)
    for key in h5.attrs:
        lowered = key.lower()
        if any(token in lowered for token in ("stage", "label", "event")):
            require(key == "stage_codebook", f"Unexpected stage/label/event H5 attribute: {h5_path}:{key}")
            require_empty_codebook(h5.attrs[key], f"root:{key}")
    return empty_label_datasets


def apply_range_memberships(
    window_starts: np.ndarray,
    window_ends: np.ndarray,
    ranges: list[Mapping[str, Any]],
    *,
    tolerance_sec: float = 1e-6,
) -> tuple[np.ndarray, list[int]]:
    """Count how many declared manifest intervals contain each complete window."""
    starts = np.asarray(window_starts, dtype=float)
    ends = np.asarray(window_ends, dtype=float)
    require(starts.ndim == ends.ndim == 1 and starts.shape == ends.shape, "Window bounds must be aligned vectors")
    require(np.isfinite(starts).all() and np.isfinite(ends).all(), "Window bounds must be finite")
    memberships = np.zeros(starts.size, dtype=np.int64)
    counts: list[int] = []
    for item in ranges:
        start, end = float(item["start_sec"]), float(item["end_sec"])
        contained = (starts >= start - tolerance_sec) & (ends <= end + tolerance_sec)
        counts.append(int(contained.sum()))
        memberships += contained.astype(np.int64)
    return memberships, counts


def h5_scalar(h5: h5py.Group, path: str) -> str:
    return text(h5[path][()])


def normalized(value: Any) -> str | None:
    if pd.isna(value):
        return None
    value = str(value).strip()
    return value or None


def same_column(left: pd.Series, right: pd.Series, name: str) -> bool:
    integer_fields = {
        "nominal_source_sample_start", "nominal_source_sample_end_exclusive",
        "actual_source_sample_start", "actual_source_sample_end_exclusive",
        "input_sample_gap_count",
    }
    float_fields = {
        "source_sfreq_hz", "actual_source_time_start_sec", "actual_source_time_end_sec",
    }
    if name in integer_fields | float_fields:
        a = pd.to_numeric(left, errors="coerce").to_numpy(dtype=float)
        b = pd.to_numeric(right, errors="coerce").to_numpy(dtype=float)
        atol = 1e-8 if name in integer_fields else 1e-7
        return bool(np.isclose(a, b, rtol=0.0, atol=atol, equal_nan=True).all())
    return bool(np.equal(left.map(normalized).to_numpy(dtype=object), right.map(normalized).to_numpy(dtype=object)).all())


def build(output_dir: Path) -> dict[str, Any]:
    manifest_paths = [V4_ROOT / "fold_manifests" / f"fold_{fold}.json" for fold in range(5)]
    feature_path = V4_ROOT / "features_primary_ppg.parquet"
    row_audit_path = V4_ROOT / "row_support_audit.csv"
    recording_audit_path = V4_ROOT / "recording_audit.csv"
    ledger_path = V4_ROOT / "signal_support_ledger.json"
    for path in [*manifest_paths, feature_path, row_audit_path, recording_audit_path, ledger_path]:
        require(path.is_file(), f"Required input is missing: {path}")
    require(not output_dir.exists(), f"Refusing to overwrite existing output directory: {output_dir}")

    manifests = [json.loads(path.read_text(encoding="utf-8")) for path in manifest_paths]
    ledger_hash = sha256_file(ledger_path)
    assignments: dict[str, tuple[str, int]] = {}
    ranges_by_recording: dict[str, list[dict[str, Any]]] = {}
    apply_pid_sets: list[set[str]] = []
    for fold, manifest in enumerate(manifests):
        require(manifest.get("schema_version") == "mndm.fold_split.v1", f"Unexpected manifest schema: fold {fold}")
        require(manifest.get("signal_support_ledger_sha256") == ledger_hash, f"Fold {fold} ledger hash mismatch")
        train_pids = set(manifest["training_pids"])
        apply_pids = set(manifest["apply_pids"])
        require(train_pids.isdisjoint(apply_pids), f"Train/apply PID overlap in fold {fold}")
        apply_pid_sets.append(apply_pids)
        seen_ranges: set[tuple[str, float, float]] = set()
        for entry in manifest["apply_ranges"]:
            recording = entry["recording_id"]
            value = (entry["subject_id"], fold)
            require(entry["subject_id"] in apply_pids, f"Apply range subject not in apply PID set: {entry}")
            start, end = float(entry["start_sec"]), float(entry["end_sec"])
            require(np.isfinite([start, end]).all() and end > start, f"Invalid apply time range: {entry}")
            range_key = (recording, start, end)
            require(range_key not in seen_ranges, f"Duplicate apply range in fold {fold}: {entry}")
            seen_ranges.add(range_key)
            prior = assignments.get(recording)
            require(prior is None or prior == value, f"Recording assigned to conflicting apply PID/fold: {recording}")
            assignments[recording] = value
            ranges_by_recording.setdefault(recording, []).append({"fold": fold, "subject_id": entry["subject_id"], "start_sec": start, "end_sec": end})
        for recording in {entry["recording_id"] for entry in manifest["apply_ranges"]}:
            file_ranges = sorted(
                (item for item in ranges_by_recording[recording] if item["fold"] == fold),
                key=lambda item: (item["start_sec"], item["end_sec"]),
            )
            require(len({item["subject_id"] for item in file_ranges}) == 1, f"Apply ranges map to multiple PIDs: {recording}")
            for left, right in zip(file_ranges, file_ranges[1:]):
                require(right["start_sec"] >= left["end_sec"] - 1e-6, f"Overlapping apply ranges: {recording}")
    all_apply_pids = set.union(*apply_pid_sets)
    require(sum(map(len, apply_pid_sets)) == len(all_apply_pids) == 78, "Apply PID sets are not a disjoint partition of the 78-PID cohort")

    chart_frames: list[pd.DataFrame] = []
    run_hashes: dict[str, str] = {}
    config_hashes: dict[str, str] = {}
    anchor_file_hashes: dict[str, str] = {}
    h5_hashes: dict[str, str] = {}
    range_coverage_by_recording: dict[str, list[int]] = {}
    empty_label_dataset_counts: dict[str, int] = {}
    fold_details: dict[str, Any] = {}
    all_manifest_source_hashes: dict[str, str] = {}

    for fold, manifest in enumerate(manifests):
        suffix = version_suffix(fold)
        run_name = f"fold_{fold}_apply_label_free_{suffix}"
        run_dir = CHART_ROOT / "processed" / "ds005555" / run_name
        run_manifest_path = run_dir / "run_manifest.json"
        anchor_id = f"ds005555_continuous_c123_fold_{fold}_chart_label_free_{'v2' if fold == 0 else 'v1'}"
        train_dir = CHART_ROOT / "processed" / "ds005555" / f"fold_{fold}_training_label_free_{suffix}"
        anchor_path = train_dir / "anchors" / f"{anchor_id}.json"
        require(anchor_path.is_file(), f"Fit anchor missing for fold {fold}: {anchor_path}")
        anchor_file_hashes[f"fold_{fold}"] = sha256_file(anchor_path)
        require(read_pretty_json_string_field(anchor_path, "anchor_id") == anchor_id, f"Anchor artifact ID mismatch: fold {fold}")

        train_manifest, train_config_path, train_digest = validate_run_config(
            fold=fold, role="training", run_dir=train_dir, manifest_path=manifest_paths[fold],
            ledger_path=ledger_path, anchor_path=anchor_path, anchor_id=anchor_id,
        )
        run_manifest, config_path, digest = validate_run_config(
            fold=fold, role="apply", run_dir=run_dir, manifest_path=manifest_paths[fold],
            ledger_path=ledger_path, anchor_path=anchor_path, anchor_id=anchor_id,
        )
        run_hashes[f"fold_{fold}_training"] = sha256_file(train_dir / "run_manifest.json")
        run_hashes[f"fold_{fold}_apply"] = sha256_file(run_manifest_path)
        config_hashes[f"fold_{fold}_training"] = sha256_file(train_config_path)
        config_hashes[f"fold_{fold}_apply"] = sha256_file(config_path)
        all_manifest_source_hashes.update(manifest["source_file_sha256"])

        expected_recordings = {row["recording_id"] for row in manifest["apply_ranges"]}
        require(set(manifest["source_file_sha256"]).issuperset(expected_recordings), f"Manifest lacks source hashes for apply recordings in fold {fold}")
        h5_files = sorted(run_dir.glob("sub-*/sub-*.h5"))
        require(len(h5_files) == len(expected_recordings), f"H5 count does not match apply manifest in fold {fold}")
        run_rows = 0
        run_anchor_hashes: set[str] = set()
        for h5_path in h5_files:
            empty_label_dataset_count = 0
            with h5py.File(h5_path, "r") as h5:
                bids_subject = text(h5.attrs["subject_id"])
                raw_files = np.asarray(h5["row_source/raw_file"][:]).astype(str)
                require(raw_files.size > 0 and len(set(raw_files.tolist())) == 1, f"Mixed raw recordings in {h5_path}")
                recording = raw_files[0]
                parsed_bids_subject = recording.split("_", maxsplit=1)[0]
                require(bids_subject == parsed_bids_subject and parsed_bids_subject.startswith("sub-"), f"BIDS subject mismatch: {h5_path}")
                require(recording in expected_recordings and recording in assignments, f"Unexpected apply recording: {recording}")
                biological_subject, expected_fold = assignments[recording]
                require(expected_fold == fold, f"Recording assigned to wrong apply fold: {recording}")
                epoch_ids = np.asarray(h5["epoch_id"][:], dtype=np.int64)
                window_starts = np.asarray(h5["window_start"][:], dtype=float)
                window_ends = np.asarray(h5["window_end"][:], dtype=float)
                n = len(epoch_ids)
                require(n > 0 and len(np.unique(epoch_ids)) == n, f"Empty or duplicate H5 epoch IDs: {h5_path}")
                require(window_starts.shape == window_ends.shape == (n,), f"H5 time-vector shape mismatch: {h5_path}")
                require(np.isfinite(window_starts).all() and np.isfinite(window_ends).all() and np.all(window_ends > window_starts), f"Invalid H5 window times: {h5_path}")
                file_ranges = sorted(
                    (item for item in ranges_by_recording[recording] if item["fold"] == fold),
                    key=lambda item: (item["start_sec"], item["end_sec"]),
                )
                require(file_ranges, f"No apply time ranges for H5 recording: {recording}")
                memberships, covered_rows = apply_range_memberships(window_starts, window_ends, file_ranges)
                require(all(count > 0 for count in covered_rows), f"An apply range covers no H5 rows: {recording}")
                require(np.all(memberships == 1), f"H5 rows do not map one-to-one to declared apply ranges: {h5_path}")
                range_coverage_by_recording[recording] = covered_rows
                run_rows += n
                coords3d = np.asarray(h5["coords_3d_cohort_anchored/values"][:])
                coords9d = np.asarray(h5["coords_9d_cohort_anchored/values"][:])
                require(coords3d.shape == (n, 3) and coords9d.shape == (n, 9), f"Coordinate shape mismatch: {h5_path}")
                geometry = np.asarray(h5["qc/windows/geometry_valid"][:], dtype=bool)
                valid9 = np.asarray(h5["qc/windows/coords_9d_valid"][:], dtype=bool)
                valid3 = np.asarray(h5["qc/windows/mnps_3d_valid"][:], dtype=bool)
                retained = np.asarray(h5["qc/windows/retained_after_qc"][:], dtype=bool)
                require(all(x.shape == (n,) for x in (geometry, valid9, valid3, retained)), f"QC shape mismatch: {h5_path}")
                empty_label_dataset_count = validate_label_free_h5(h5, h5_path)
                sig = "support_signature/v1/coordinates/e_m/"
                signature = {
                    "coordinate_e_m_source": h5_scalar(h5, sig + "source"),
                    "coordinate_e_m_fallback_feature": h5_scalar(h5, sig + "fallback_feature"),
                    "coordinate_e_m_semantic_equivalence": h5_scalar(h5, sig + "semantic_equivalence"),
                }
                support = "provenance/signal_support_provenance/"
                generic = {
                    "h5_signal_support_status": h5_scalar(h5, support + "status"),
                    "h5_temporal_support_status": h5_scalar(h5, support + "temporal_support_status"),
                    "h5_source_quality_status": h5_scalar(h5, support + "source_quality_status"),
                }
                h5_digest = h5_scalar(h5, "provenance/contract/config_digest_sha256")
                require(h5_digest == digest, f"H5/run-manifest config digest mismatch: {h5_path}")
                require(str(h5.attrs["anchor_id"]) == anchor_id, f"Unexpected anchor ID: {h5_path}")
                anchor_hash = str(h5.attrs["anchor_hash"])
                run_anchor_hashes.add(anchor_hash)

                chart = pd.DataFrame(
                    {
                        "fold": fold,
                        "fold_role": "apply",
                        "subject": biological_subject,
                        "bids_subject": bids_subject,
                        "file": recording,
                        "epoch_id": epoch_ids,
                        "chart_window_start_sec": window_starts,
                        "chart_window_end_sec": window_ends,
                        "chart_time_center_sec": np.asarray(h5["time"][:], dtype=float),
                        "chart_coords_3d_all_finite": np.isfinite(coords3d).all(axis=1),
                        "chart_coords_9d_all_finite": np.isfinite(coords9d).all(axis=1),
                        "chart_geometry_valid": geometry,
                        "chart_coords_9d_valid": valid9,
                        "chart_mnps_3d_valid": valid3,
                        "chart_retained_after_qc": retained,
                        "anchor_id": anchor_id,
                        "anchor_hash": anchor_hash,
                        "config_digest_sha256": h5_digest,
                        "geometry_contract_status": text(h5.attrs.get("geometry_contract_status", "unknown")),
                        "chart_h5_relative_path": h5_path.relative_to(ARTICLE_ROOT).as_posix(),
                        **signature,
                        **generic,
                    }
                )
            empty_label_dataset_counts[h5_path.relative_to(ARTICLE_ROOT).as_posix()] = empty_label_dataset_count
            h5_relative_path = h5_path.relative_to(ARTICLE_ROOT).as_posix()
            h5_sha256 = sha256_file(h5_path)
            h5_hashes[h5_relative_path] = h5_sha256
            chart["chart_h5_sha256"] = h5_sha256
            chart_frames.append(chart)
        require(len(run_anchor_hashes) == 1, f"Apply fold {fold} uses multiple anchors")
        declared_anchor_hash = read_pretty_json_string_field(anchor_path, "anchor_hash")
        require(run_anchor_hashes == {declared_anchor_hash}, f"Apply fold {fold} H5 anchor hash differs from its fit anchor")
        require(set(range_coverage_by_recording).issuperset(expected_recordings), f"Not every apply recording had its ranges checked in fold {fold}")
        fold_details[str(fold)] = {
            "split_id": manifest["split_id"],
            "apply_pids": len(manifest["apply_pids"]),
            "apply_recordings": len(expected_recordings),
            "apply_epochs": run_rows,
            "anchor_id": anchor_id,
            "anchor_hash": next(iter(run_anchor_hashes)),
            "config_digest_sha256": digest,
            "training_config_digest_sha256": train_digest,
            "training_run_manifest_sha256": run_hashes[f"fold_{fold}_training"],
            "apply_run_manifest_sha256": run_hashes[f"fold_{fold}_apply"],
            "training_provided_config_sha256": config_hashes[f"fold_{fold}_training"],
            "apply_provided_config_sha256": config_hashes[f"fold_{fold}_apply"],
            "fit_anchor_file_sha256": anchor_file_hashes[f"fold_{fold}"],
            "apply_range_count": sum(1 for items in ranges_by_recording.values() for item in items if item["fold"] == fold),
        }

    charts = pd.concat(chart_frames, ignore_index=True)
    require(not charts.duplicated(KEYS).any(), "Duplicate apply chart (file, epoch_id) keys across folds")
    require(charts["file"].nunique() == 100 and charts["subject"].nunique() == 78, "Apply surface does not cover 100 recordings/78 biological PIDs")
    require(int(charts.groupby("subject")["fold"].nunique().max()) == 1, "A biological subject appears in apply roles of multiple folds")
    require(len(charts) == 92_545, f"Unexpected total apply-chart epoch count: {len(charts)}")
    require(charts["h5_temporal_support_status"].eq("unknown").all(), "Generic H5 temporal support is not unknown")
    require(charts["h5_source_quality_status"].eq("not_recorded").all(), "Generic H5 source quality is not recorded as not_recorded")
    require(len(h5_hashes) == 100 and len(empty_label_dataset_counts) == 100, "H5 hash/label-payload inventory does not cover all apply files")

    feature = pd.read_parquet(feature_path, columns=FEATURE_COLUMNS)
    row_audit = pd.read_csv(row_audit_path, usecols=ROW_AUDIT_COLUMNS, low_memory=False)
    recording_audit = pd.read_csv(recording_audit_path, usecols=RECORDING_AUDIT_COLUMNS, low_memory=False)
    require(not feature.duplicated(KEYS).any(), "Duplicate keys in feature table")
    require(not row_audit.duplicated(KEYS).any(), "Duplicate keys in row support audit")
    require(not recording_audit["file"].duplicated().any(), "Duplicate files in recording audit")
    feature = feature.rename(columns={c: f"feature_{c}" for c in feature.columns if c not in KEYS})
    audit = row_audit.rename(columns={c: f"audit_{c}" for c in row_audit.columns if c not in KEYS})
    recording = recording_audit.rename(columns={c: f"recording_{c}" for c in recording_audit.columns if c != "file"})

    joined = charts.merge(feature, on=KEYS, how="left", validate="one_to_one", indicator="feature_join")
    require(joined["feature_join"].eq("both").all(), "Missing feature-table match for apply chart row")
    joined = joined.drop(columns="feature_join")
    joined = joined.merge(audit, on=KEYS, how="left", validate="one_to_one", indicator="audit_join")
    require(joined["audit_join"].eq("both").all(), "Missing row-support audit match for apply chart row")
    joined = joined.drop(columns="audit_join")
    joined = joined.merge(recording, on="file", how="left", validate="many_to_one", indicator="recording_join")
    require(joined["recording_join"].eq("both").all(), "Missing recording audit match for apply chart row")
    joined = joined.drop(columns="recording_join")

    require(joined["feature_subject"].eq(joined["subject"]).all(), "Chart/feature biological subject mismatch")
    require(joined["audit_subject"].eq(joined["subject"]).all(), "Chart/row-audit biological subject mismatch")
    require(joined["audit_bids_subject"].eq(joined["bids_subject"]).all(), "Chart/row-audit BIDS subject mismatch")
    require(np.isclose(joined["feature_t_start"].to_numpy(float), joined["chart_window_start_sec"].to_numpy(float), rtol=0, atol=1e-6).all(), "Chart/feature start-time mismatch")
    require(np.isclose(joined["feature_t_end"].to_numpy(float), joined["chart_window_end_sec"].to_numpy(float), rtol=0, atol=1e-6).all(), "Chart/feature end-time mismatch")
    require(np.isclose(joined["audit_t_start"].to_numpy(float), joined["chart_window_start_sec"].to_numpy(float), rtol=0, atol=1e-6).all(), "Chart/audit start-time mismatch")
    require(np.isclose(joined["audit_t_end"].to_numpy(float), joined["chart_window_end_sec"].to_numpy(float), rtol=0, atol=1e-6).all(), "Chart/audit end-time mismatch")
    for column in SUPPORT_COMPARE_COLUMNS:
        require(same_column(joined[f"feature_{column}"], joined[f"audit_{column}"], column), f"Feature/audit support mismatch: {column}")

    expected_hashes = all_manifest_source_hashes
    joined["expected_source_sha256"] = joined["file"].map(expected_hashes)
    require(joined["expected_source_sha256"].notna().all(), "Apply source absent from fold manifests")
    require(joined["audit_source_sha256"].eq(joined["expected_source_sha256"]).all(), "Row audit source hash differs from fold manifest")
    require(joined["recording_source_sha256"].eq(joined["expected_source_sha256"]).all(), "Recording audit source hash differs from fold manifest")
    joined["source_hashes_match_fold_manifest"] = True

    require(joined["recording_support_record_status"].eq("valid").all(), "Invalid recording-level support status")
    require(joined["recording_support_record_reasons"].fillna("").astype(str).str.strip().eq("").all(), "Recording-level support reason present")
    require(joined["recording_source_stratum"].eq(joined["audit_source_stratum"]).all(), "Recording/row source strata differ")
    require(joined["recording_recording_proxy_sources"].eq(joined["audit_recording_proxy_sources"]).all(), "Recording/row proxy sources differ")
    require(joined["audit_primary_surface_eligible"].astype(bool).all(), "A chart row is not primary-surface eligible")
    require(joined["audit_base_support_eligible"].astype(bool).all(), "A chart row fails base support eligibility")
    require(joined["audit_proxy_matches_ppg_rate"].astype(bool).all(), "A chart row does not match declared PPG proxy")
    require(joined["audit_support_exclusion_reasons"].fillna("").astype(str).str.strip().eq("").all(), "Support exclusion in a chart row")
    require(joined["audit_actual_sample_contributors_status"].eq("finite_causal_conservative_bound").all(), "Unexpected actual contributor status")
    require(joined["audit_input_sample_finite_status"].eq("all_finite").all(), "Non-finite source samples in eligible chart row")
    require(pd.to_numeric(joined["audit_input_sample_gap_count"], errors="coerce").eq(0).all(), "Input sample gap in chart row")
    require(joined["audit_source_sample_mapping_status"].eq("nominal_bounds_mapped").all(), "Unmapped source interval in chart row")
    require(joined["audit_qc_ok_eeg"].astype(bool).all() and joined["audit_qc_ok_ppg"].astype(bool).all(), "EEG/PPG QC failure in chart row")
    require(joined["chart_coords_3d_all_finite"].all() and joined["chart_coords_9d_all_finite"].all(), "Non-finite chart coordinates")
    require(joined["chart_geometry_valid"].all() and joined["geometry_contract_status"].eq("ok").all(), "Geometry invalidity in chart outputs")
    require(joined["coordinate_e_m_source"].eq("fallback").all(), "e_m source signature changed")
    require(joined["coordinate_e_m_fallback_feature"].eq("ppg_rate_bpm").all(), "e_m fallback feature changed")
    require(joined["coordinate_e_m_semantic_equivalence"].eq("false").all(), "Unexpected e_m semantic-equivalence claim")
    require(joined["h5_temporal_support_status"].eq("unknown").all(), "H5 temporal-support status unexpectedly changed")
    require(joined["h5_source_quality_status"].eq("not_recorded").all(), "H5 source-quality status unexpectedly changed")

    per_file_rows = joined.groupby("file").size().sort_index()
    per_file_primary = (
        joined[["file", "recording_primary_surface_eligible_rows"]]
        .drop_duplicates()
        .set_index("file")["recording_primary_surface_eligible_rows"]
        .astype(int)
        .sort_index()
    )
    require(per_file_rows.equals(per_file_primary), "Mapped rows differ from per-recording primary-eligible counts")
    recording_counts = joined[["file", "recording_feature_rows", "recording_primary_surface_eligible_rows"]].drop_duplicates().copy()
    recording_counts["feature_rows_outside_primary_surface"] = (
        pd.to_numeric(recording_counts["recording_feature_rows"], errors="coerce")
        - pd.to_numeric(recording_counts["recording_primary_surface_eligible_rows"], errors="coerce")
    )
    require(recording_counts["feature_rows_outside_primary_surface"].ge(0).all(), "Negative per-recording outside-surface count")

    columns = [
        "fold", "fold_role", "subject", "bids_subject", "file", "epoch_id",
        "chart_window_start_sec", "chart_window_end_sec", "chart_time_center_sec",
        "chart_coords_3d_all_finite", "chart_coords_9d_all_finite", "chart_geometry_valid",
        "chart_coords_9d_valid", "chart_mnps_3d_valid", "chart_retained_after_qc",
        "geometry_contract_status", "anchor_id", "anchor_hash", "config_digest_sha256",
        "coordinate_e_m_source", "coordinate_e_m_fallback_feature", "coordinate_e_m_semantic_equivalence",
        "h5_signal_support_status", "h5_temporal_support_status", "h5_source_quality_status",
        "audit_source_stratum", "audit_recording_proxy_sources", "audit_row_proxy_source",
        "audit_proxy_matches_ppg_rate", "audit_base_support_eligible", "audit_primary_surface_eligible",
        "audit_support_exclusion_reasons", "audit_source_sample_mapping_status",
        "audit_source_sample_mapping_reason", "audit_nominal_source_sample_start",
        "audit_nominal_source_sample_end_exclusive", "audit_actual_sample_contributors_status",
        "feature_actual_sample_contributors_reason", "audit_actual_source_sample_start",
        "audit_actual_source_sample_end_exclusive", "audit_actual_source_time_start_sec",
        "audit_actual_source_time_end_sec", "audit_source_sfreq_hz", "audit_input_sample_finite_status",
        "audit_input_sample_gap_count", "audit_qc_ok_eeg", "audit_qc_ok_ppg",
        "recording_support_record_status", "recording_support_record_reasons",
        "recording_feature_rows", "recording_base_support_eligible_rows",
        "recording_primary_surface_eligible_rows", "recording_source_sha256",
        "expected_source_sha256", "source_hashes_match_fold_manifest", "chart_h5_relative_path", "chart_h5_sha256",
    ]
    output = joined[columns].copy()
    require(not any("stage" in c.lower() or "label" in c.lower() for c in output.columns), "Stage/label field leaked into all-fold support map")
    require(output["fold"].nunique() == 5 and output["file"].nunique() == 100 and output["subject"].nunique() == 78, "Unexpected apply coverage counts")

    output_dir.mkdir(parents=True, exist_ok=False)
    parquet_path = output_dir / "all_fold_apply_chart_support_map.parquet"
    output.to_parquet(parquet_path, index=False, compression="zstd")

    hash_inputs = {
        "v4_feature_parquet": feature_path,
        "v4_row_support_audit": row_audit_path,
        "v4_recording_audit": recording_audit_path,
        "v4_signal_support_ledger": ledger_path,
        "all_fold_support_map_builder": Path(__file__).resolve(),
    }
    for fold, path in enumerate(manifest_paths):
        hash_inputs[f"fold_{fold}_manifest"] = path
        suffix = version_suffix(fold)
        for role in ("training", "apply"):
            run_dir = CHART_ROOT / "processed" / "ds005555" / f"fold_{fold}_{role}_label_free_{suffix}"
            hash_inputs[f"fold_{fold}_{role}_run_manifest"] = run_dir / "run_manifest.json"
            hash_inputs[f"fold_{fold}_{role}_config"] = CHART_ROOT / "configs" / f"fold_{fold}_{role}_label_free_{suffix}.yaml"
        hash_inputs[f"fold_{fold}_fit_anchor"] = CHART_ROOT / "processed" / "ds005555" / f"fold_{fold}_training_label_free_{suffix}" / "anchors" / f"ds005555_continuous_c123_fold_{fold}_chart_label_free_{suffix}.json"
    input_hashes = {name: sha256_file(path) for name, path in hash_inputs.items()}

    summary = {
        "schema_version": "boas.all_fold_apply_chart_support_map.v2",
        "verdict": "PARTIAL_PASS_ALL_FOLD_APPLY_SUPPORT_CROSSWALK",
        "scope": "all-fold apply-chart identity/support crosswalk only; no sleep-stage join, stage/horizon intersection, contrast, score, or biological qualification",
        "row_count": int(len(output)),
        "recording_count": int(output["file"].nunique()),
        "biological_subject_count": int(output["subject"].nunique()),
        "fold_count": int(output["fold"].nunique()),
        "epochs_by_fold": {str(k): int(v) for k, v in output.groupby("fold").size().to_dict().items()},
        "recordings_by_fold": {str(k): int(v) for k, v in output.groupby("fold")["file"].nunique().to_dict().items()},
        "apply_manifest_ranges": {
            "range_count": int(sum(len(manifest["apply_ranges"]) for manifest in manifests)),
            "every_h5_window_matches_exactly_one_declared_range": True,
            "every_declared_range_covers_at_least_one_h5_window": True,
            "coverage_by_recording": {
                filename: [
                    {"start_sec": item["start_sec"], "end_sec": item["end_sec"], "h5_window_count": count}
                    for item, count in zip(
                        sorted((x for x in ranges_by_recording[filename] if x["fold"] == assignments[filename][1]), key=lambda x: (x["start_sec"], x["end_sec"])),
                        range_coverage_by_recording[filename],
                    )
                ]
                for filename in sorted(range_coverage_by_recording)
            },
        },
        "h5_artifact_inventory": [
            {"relative_path": name, "sha256": digest}
            for name, digest in sorted(h5_hashes.items())
        ],
        "label_free_h5_payload_check": {
            "event_stage_mapping_groups_empty": True,
            "stage_codebooks_empty": True,
            "nonblank_stage_label_event_dataset_payloads": 0,
            "empty_generic_group_label_dataset_count": int(sum(empty_label_dataset_counts.values())),
            "h5_file_count_checked": len(empty_label_dataset_counts),
        },
        "run_config_semantics_verified_for_training_and_apply": True,
        "apply_pids_by_fold": {str(f): len(manifests[f]["apply_pids"]) for f in range(5)},
        "apply_pid_sets_disjoint_and_complete": True,
        "each_apply_recording_appears_once": True,
        "per_recording_mapped_rows_match_primary_eligible_counts": True,
        "recording_audit_feature_rows_exceed_primary_rows_in_recordings": int(recording_counts["feature_rows_outside_primary_surface"].gt(0).sum()),
        "feature_rows_outside_primary_surface_total": int(recording_counts["feature_rows_outside_primary_surface"].sum()),
        "support_status": {
            "primary_surface_eligible_rows": int(output["audit_primary_surface_eligible"].astype(bool).sum()),
            "base_support_eligible_rows": int(output["audit_base_support_eligible"].astype(bool).sum()),
            "all_finite_source_rows": int(output["audit_input_sample_finite_status"].eq("all_finite").sum()),
            "rows_with_gaps": int(pd.to_numeric(output["audit_input_sample_gap_count"], errors="coerce").ne(0).sum()),
            "actual_sample_contributors_status": sorted(output["audit_actual_sample_contributors_status"].unique().tolist()),
            "source_sample_mapping_status": sorted(output["audit_source_sample_mapping_status"].unique().tolist()),
            "recording_status": sorted(output["recording_support_record_status"].unique().tolist()),
            "source_strata": sorted(output["audit_source_stratum"].unique().tolist()),
            "e_m_source": sorted(output["coordinate_e_m_source"].unique().tolist()),
            "e_m_fallback_feature": sorted(output["coordinate_e_m_fallback_feature"].unique().tolist()),
            "e_m_semantic_equivalence": sorted(output["coordinate_e_m_semantic_equivalence"].unique().tolist()),
        },
        "h5_generic_support_provenance": {
            "temporal_support_status": sorted(output["h5_temporal_support_status"].unique().tolist()),
            "source_quality_status": sorted(output["h5_source_quality_status"].unique().tolist()),
            "note": "External row-level support remains a separate hash-bound object; H5 statuses are not promoted.",
        },
        "fold_anchors": fold_details,
        "label_join_performed": False,
        "stage_horizon_intersection_computed": False,
        "contrasts_computed": False,
        "biological_claim_authorized": False,
        "output_parquet": parquet_path.relative_to(ARTICLE_ROOT).as_posix(),
        "output_parquet_sha256": sha256_file(parquet_path),
        "input_sha256": input_hashes,
        "limitations": [
            "The H5 generic temporal-support field remains unknown and source-quality status remains not_recorded.",
            "This map does not calculate stage/horizon coverage; that is a separate full-surface gate and must not be interpreted as an outcome analysis.",
            "A successful support crosswalk does not by itself authorize C1/C2/C3 outcomes; registered full-surface gate and dated protocol authorization remain required.",
        ],
    }
    (output_dir / "validation.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT, help="Fresh output directory; never overwritten.")
    args = parser.parse_args()
    summary = build(args.output_dir.resolve())
    print(json.dumps({k: summary[k] for k in ("verdict", "row_count", "recording_count", "biological_subject_count", "epochs_by_fold", "output_parquet_sha256")}, indent=2))


if __name__ == "__main__":
    main()
