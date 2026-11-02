"""Build an outcome-blind row-level support crosswalk for fold-0 charts.

This is a measurement/provenance check only. It intentionally does not load
sleep-stage fields, join labels, calculate contrasts, or assess biology.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd


ARTICLE_ROOT = Path(__file__).resolve().parents[1]
RESULTS_ROOT = ARTICLE_ROOT / "results"
CHART_ROOT = RESULTS_ROOT / "fold_safe_chart_qualification_20260930_v1"
V4_ROOT = RESULTS_ROOT / "continuous_full_surface_support_audit_20260929_v4"
DEFAULT_OUTPUT_ROOT = CHART_ROOT / "support_map_v3"

FEATURE_COLUMNS = [
    "file",
    "subject",
    "epoch_id",
    "t_start",
    "t_end",
    "source_stratum",
    "source_sample_mapping_status",
    "source_sample_mapping_reason",
    "nominal_source_sample_start",
    "nominal_source_sample_end_exclusive",
    "source_sfreq_hz",
    "actual_sample_contributors_status",
    "actual_sample_contributors_reason",
    "actual_source_sample_start",
    "actual_source_sample_end_exclusive",
    "actual_source_time_start_sec",
    "actual_source_time_end_sec",
    "input_sample_finite_status",
    "input_sample_gap_count",
]

# Deliberately excludes stage_at_origin*, stage_window*, and every other
# outcome/label field in row_support_audit.csv.
ROW_AUDIT_COLUMNS = [
    "file",
    "subject",
    "bids_subject",
    "epoch_id",
    "t_start",
    "t_end",
    "source_stratum",
    "recording_proxy_sources",
    "row_proxy_source",
    "proxy_matches_ppg_rate",
    "base_support_eligible",
    "primary_surface_eligible",
    "support_exclusion_reasons",
    "source_sha256",
    "source_sample_mapping_status",
    "source_sample_mapping_reason",
    "nominal_source_sample_start",
    "nominal_source_sample_end_exclusive",
    "actual_sample_contributors_status",
    "actual_source_sample_start",
    "actual_source_sample_end_exclusive",
    "actual_source_time_start_sec",
    "actual_source_time_end_sec",
    "source_sfreq_hz",
    "input_sample_finite_status",
    "input_sample_gap_count",
    "qc_ok_eeg",
    "qc_ok_ppg",
]

RECORDING_AUDIT_COLUMNS = [
    "file",
    "source_stratum",
    "recording_proxy_sources",
    "feature_rows",
    "base_support_eligible_rows",
    "primary_surface_eligible_rows",
    "support_record_status",
    "support_record_reasons",
    "source_sha256",
]

SUPPORT_COMPARE_COLUMNS = [
    "source_stratum",
    "source_sample_mapping_status",
    "source_sample_mapping_reason",
    "nominal_source_sample_start",
    "nominal_source_sample_end_exclusive",
    "source_sfreq_hz",
    "actual_sample_contributors_status",
    "actual_source_sample_start",
    "actual_source_sample_end_exclusive",
    "actual_source_time_start_sec",
    "actual_source_time_end_sec",
    "input_sample_finite_status",
    "input_sample_gap_count",
]

KEYS = ["file", "epoch_id"]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="strict")
    if isinstance(value, np.bytes_):
        return bytes(value).decode("utf-8", errors="strict")
    return str(value)


def h5_scalar(group: h5py.Group, path: str) -> str:
    return text(group[path][()])


def normalized_text(value: Any) -> str | None:
    if pd.isna(value):
        return None
    value = str(value).strip()
    return value if value else None


def equal_column(left: pd.Series, right: pd.Series, name: str) -> bool:
    if name in {
        "nominal_source_sample_start",
        "nominal_source_sample_end_exclusive",
        "actual_source_sample_start",
        "actual_source_sample_end_exclusive",
        "input_sample_gap_count",
    }:
        a = pd.to_numeric(left, errors="coerce").to_numpy(dtype=float)
        b = pd.to_numeric(right, errors="coerce").to_numpy(dtype=float)
        return bool(np.isclose(a, b, rtol=0.0, atol=1e-8, equal_nan=True).all())
    if name in {
        "source_sfreq_hz",
        "actual_source_time_start_sec",
        "actual_source_time_end_sec",
    }:
        a = pd.to_numeric(left, errors="coerce").to_numpy(dtype=float)
        b = pd.to_numeric(right, errors="coerce").to_numpy(dtype=float)
        return bool(np.isclose(a, b, rtol=0.0, atol=1e-7, equal_nan=True).all())
    a = left.map(normalized_text).to_numpy(dtype=object)
    b = right.map(normalized_text).to_numpy(dtype=object)
    return bool(np.equal(a, b).all())


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def collect_chart_rows(train_dir: Path, apply_dir: Path, manifest: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    training_pids = set(manifest["training_pids"])
    apply_pids = set(manifest["apply_pids"])
    require(training_pids.isdisjoint(apply_pids), "Fold manifest train/apply PID sets overlap.")
    role_by_subject = {subject: "training" for subject in training_pids}
    role_by_subject.update({subject: "apply" for subject in apply_pids})
    recording_assignment: dict[str, tuple[str, str]] = {}
    for role in ("training", "apply"):
        for interval in manifest[f"{role}_ranges"]:
            recording_id = interval["recording_id"]
            assignment = (interval["subject_id"], role)
            require(interval["subject_id"] in role_by_subject, f"Unknown biological subject in fold range: {interval}")
            require(role_by_subject[interval["subject_id"]] == role, f"Range role disagrees with frozen PID split: {interval}")
            previous = recording_assignment.setdefault(recording_id, assignment)
            require(previous == assignment, f"Recording maps to multiple biological subjects/roles: {recording_id}")

    frames: list[pd.DataFrame] = []
    run_details: dict[str, Any] = {}
    for role, run_dir in (("training", train_dir), ("apply", apply_dir)):
        run_manifest_path = run_dir / "run_manifest.json"
        run_manifest = read_json(run_manifest_path)
        extra = run_manifest.get("extra", {})
        config_info = run_manifest.get("config", {})
        yaml_source = config_info.get("yaml_source", {})
        provided_config_path = Path(yaml_source.get("provided_path", ""))
        require(provided_config_path.is_file(), f"Run-specific input config is missing: {provided_config_path}")
        require(extra.get("run_status") == "completed", f"Run is not complete: {run_dir}")
        require(extra.get("fatal_error") is None, f"Run has fatal error: {run_dir}")
        require(extra.get("run_errors", {}).get("count") == 0, f"Run has recorded errors: {run_dir}")
        require(extra.get("stage_mapping_qc", {}).get("status") == "none", f"Stage mapping QC present: {run_dir}")
        support_manifest = extra.get("signal_support_provenance", {})
        run_details[role] = {
            "run_manifest": run_manifest_path.relative_to(ARTICLE_ROOT).as_posix(),
            "run_manifest_sha256": sha256_file(run_manifest_path),
            "run_status": extra.get("run_status"),
            "run_errors": extra.get("run_errors", {}).get("count"),
            "stage_mapping_qc_status": extra.get("stage_mapping_qc", {}).get("status"),
            "generic_signal_support_status": support_manifest.get("status"),
            "generic_temporal_support_status": support_manifest.get("temporal_support_status"),
            "generic_signal_support_records": len(support_manifest.get("records", [])),
            "resolved_config_digest_sha256": config_info.get("digest_sha256"),
            "config_excerpt_digest_sha256": config_info.get("excerpt_digest_sha256"),
            "provided_config_path": str(provided_config_path),
            "provided_config_sha256": sha256_file(provided_config_path),
        }
        require(run_details[role]["resolved_config_digest_sha256"], f"Missing resolved config digest: {run_dir}")

        h5_files = sorted(run_dir.glob("sub-*/sub-*.h5"))
        require(h5_files, f"No per-recording H5 files found in {run_dir}")
        for h5_path in h5_files:
            with h5py.File(h5_path, "r") as h5:
                bids_subject = text(h5.attrs["subject_id"])
                require("provenance/event_stage_mapping" in h5, f"Missing empty event-stage mapping group: {h5_path}")
                require(len(h5["provenance/event_stage_mapping"].keys()) == 0, f"Stage/event payload present in {h5_path}")

                raw_files = np.asarray(h5["row_source/raw_file"][:]).astype(str)
                require(raw_files.size > 0 and len(set(raw_files.tolist())) == 1, f"Unexpected mixed raw-file rows: {h5_path}")
                raw_file = raw_files[0]
                parsed_bids_subject = raw_file.split("_", maxsplit=1)[0]
                require(
                    bids_subject == parsed_bids_subject and parsed_bids_subject.startswith("sub-"),
                    f"H5 subject_id does not match the BIDS ID in its raw-file name: {h5_path}",
                )
                require(raw_file in recording_assignment, f"Raw recording is absent from frozen fold ranges: {raw_file}")
                subject, assigned_role = recording_assignment[raw_file]
                require(assigned_role == role, f"Unexpected fold role for {raw_file}: {role} vs {assigned_role}")
                epoch_ids = np.asarray(h5["epoch_id"][:], dtype=np.int64)
                starts = np.asarray(h5["window_start"][:], dtype=float)
                ends = np.asarray(h5["window_end"][:], dtype=float)
                centers = np.asarray(h5["time"][:], dtype=float)
                coords3d = np.asarray(h5["coords_3d_cohort_anchored/values"][:])
                coords9d = np.asarray(h5["coords_9d_cohort_anchored/values"][:])
                require(coords3d.shape == (len(epoch_ids), 3), f"Unexpected 3D coordinate shape: {h5_path}")
                require(coords9d.shape == (len(epoch_ids), 9), f"Unexpected 9D coordinate shape: {h5_path}")
                for name, values in (("window_start", starts), ("window_end", ends), ("time", centers)):
                    require(values.shape == epoch_ids.shape and np.isfinite(values).all(), f"Invalid {name} grid: {h5_path}")

                sig_root = "support_signature/v1/coordinates/e_m/"
                signature = {
                    "coordinate_e_m_source": h5_scalar(h5, sig_root + "source"),
                    "coordinate_e_m_fallback_feature": h5_scalar(h5, sig_root + "fallback_feature"),
                    "coordinate_e_m_semantic_equivalence": h5_scalar(h5, sig_root + "semantic_equivalence"),
                }
                provenance_root = "provenance/signal_support_provenance/"
                signal_provenance = {
                    "h5_signal_support_status": h5_scalar(h5, provenance_root + "status"),
                    "h5_temporal_support_status": h5_scalar(h5, provenance_root + "temporal_support_status"),
                    "h5_source_quality_status": h5_scalar(h5, provenance_root + "source_quality_status"),
                }
                h5_config_digest = h5_scalar(h5, "provenance/contract/config_digest_sha256")
                require(
                    h5_config_digest == run_details[role]["resolved_config_digest_sha256"],
                    f"H5 config digest does not match its run manifest: {h5_path}",
                )
                n = len(epoch_ids)
                frame = pd.DataFrame(
                    {
                        "file": raw_file,
                        "epoch_id": epoch_ids,
                        "subject": subject,
                        "bids_subject": bids_subject,
                        "fold_role": role,
                        "chart_window_start_sec": starts,
                        "chart_window_end_sec": ends,
                        "chart_time_center_sec": centers,
                        "chart_coords_3d_all_finite": np.isfinite(coords3d).all(axis=1),
                        "chart_coords_9d_all_finite": np.isfinite(coords9d).all(axis=1),
                        "chart_geometry_valid": np.asarray(h5["qc/windows/geometry_valid"][:], dtype=bool),
                        "chart_coords_9d_valid": np.asarray(h5["qc/windows/coords_9d_valid"][:], dtype=bool),
                        "chart_mnps_3d_valid": np.asarray(h5["qc/windows/mnps_3d_valid"][:], dtype=bool),
                        "chart_retained_after_qc": np.asarray(h5["qc/windows/retained_after_qc"][:], dtype=bool),
                        "anchor_id": text(h5.attrs["anchor_id"]),
                        "anchor_hash": text(h5.attrs["anchor_hash"]),
                        "config_digest_sha256": h5_config_digest,
                        "geometry_contract_status": text(h5.attrs.get("geometry_contract_status", "unknown")),
                        "chart_h5_relative_path": h5_path.relative_to(ARTICLE_ROOT).as_posix(),
                    },
                    index=np.arange(n),
                )
                for key, value in signature.items():
                    frame[key] = value
                for key, value in signal_provenance.items():
                    frame[key] = value
                frames.append(frame)

    charts = pd.concat(frames, ignore_index=True)
    require(not charts.duplicated(KEYS).any(), "Duplicate chart (file, epoch_id) keys.")
    observed = set(charts["subject"].unique())
    require(observed == training_pids | apply_pids, "Chart subject set differs from frozen fold PID sets.")
    return charts, run_details


def build_map(output_dir: Path) -> dict[str, Any]:
    manifest_path = V4_ROOT / "fold_manifests" / "fold_0.json"
    feature_path = V4_ROOT / "features_primary_ppg.parquet"
    row_audit_path = V4_ROOT / "row_support_audit.csv"
    recording_audit_path = V4_ROOT / "recording_audit.csv"
    support_ledger_path = V4_ROOT / "signal_support_ledger.json"
    train_dir = CHART_ROOT / "processed" / "ds005555" / "fold_0_training_label_free_v2"
    apply_dir = CHART_ROOT / "processed" / "ds005555" / "fold_0_apply_label_free_v2"

    inputs = [manifest_path, feature_path, row_audit_path, recording_audit_path, support_ledger_path]
    for path in inputs:
        require(path.is_file(), f"Required input is missing: {path}")
    require(not output_dir.exists(), f"Refusing to overwrite existing output directory: {output_dir}")

    manifest = read_json(manifest_path)
    require(manifest.get("schema_version") == "mndm.fold_split.v1", "Unexpected fold manifest schema.")
    ledger_hash = sha256_file(support_ledger_path)
    require(ledger_hash == manifest["signal_support_ledger_sha256"], "Fold manifest/support ledger hash mismatch.")

    charts, run_details = collect_chart_rows(train_dir, apply_dir, manifest)

    feature = pd.read_parquet(feature_path, columns=FEATURE_COLUMNS)
    row_audit = pd.read_csv(row_audit_path, usecols=ROW_AUDIT_COLUMNS, low_memory=False)
    recording_audit = pd.read_csv(recording_audit_path, usecols=RECORDING_AUDIT_COLUMNS, low_memory=False)
    for label, frame in (("feature table", feature), ("row support audit", row_audit), ("recording audit", recording_audit)):
        require(not frame.duplicated(KEYS if label != "recording audit" else ["file"]).any(), f"Duplicate keys in {label}.")

    # Prefix non-key source columns so the provenance of each checked value is explicit.
    feature = feature.rename(columns={column: f"feature_{column}" for column in feature.columns if column not in KEYS})
    audit = row_audit.rename(columns={column: f"audit_{column}" for column in row_audit.columns if column not in KEYS})
    recording = recording_audit.rename(columns={column: f"recording_{column}" for column in recording_audit.columns if column != "file"})

    joined = charts.merge(feature, on=KEYS, how="left", validate="one_to_one", indicator="feature_join")
    require((joined["feature_join"] == "both").all(), "At least one chart row is missing its V4 feature row.")
    joined = joined.drop(columns="feature_join")
    joined = joined.merge(audit, on=KEYS, how="left", validate="one_to_one", indicator="audit_join")
    require((joined["audit_join"] == "both").all(), "At least one chart row is missing its V4 row-support audit record.")
    joined = joined.drop(columns="audit_join")
    joined = joined.merge(recording, on="file", how="left", validate="many_to_one", indicator="recording_join")
    require((joined["recording_join"] == "both").all(), "At least one chart row is missing its recording audit record.")
    joined = joined.drop(columns="recording_join")

    require((joined["feature_subject"] == joined["subject"]).all(), "Chart and feature subject IDs differ.")
    require((joined["audit_subject"] == joined["subject"]).all(), "Chart and row-audit subject IDs differ.")
    require((joined["audit_bids_subject"] == joined["bids_subject"]).all(), "Chart BIDS subject and row-audit BIDS subject differ.")
    for label, values in (("start", joined["feature_t_start"]), ("audit start", joined["audit_t_start"])):
        require(np.isclose(values.to_numpy(dtype=float), joined["chart_window_start_sec"].to_numpy(dtype=float), rtol=0.0, atol=1e-6).all(), f"Chart and {label} times differ.")
    for label, values in (("end", joined["feature_t_end"]), ("audit end", joined["audit_t_end"])):
        require(np.isclose(values.to_numpy(dtype=float), joined["chart_window_end_sec"].to_numpy(dtype=float), rtol=0.0, atol=1e-6).all(), f"Chart and {label} times differ.")

    for column in SUPPORT_COMPARE_COLUMNS:
        require(
            equal_column(joined[f"feature_{column}"], joined[f"audit_{column}"], column),
            f"Feature/audit disagreement in support field: {column}",
        )

    expected_hashes = manifest["source_file_sha256"]
    joined["expected_source_sha256"] = joined["file"].map(expected_hashes)
    joined["recording_source_sha256"] = joined["recording_source_sha256"]
    require(joined["expected_source_sha256"].notna().all(), "A chart source file is absent from the frozen fold manifest.")
    require((joined["recording_source_sha256"] == joined["expected_source_sha256"]).all(), "Recording-audit source hash differs from frozen manifest.")
    require((joined["audit_source_sha256"] == joined["expected_source_sha256"]).all(), "Row-audit source hash differs from frozen manifest.")
    joined["source_hashes_match_fold_manifest"] = True
    require(joined["recording_support_record_status"].eq("valid").all(), "A recording-level support record is not valid.")
    require(joined["recording_support_record_reasons"].fillna("").astype(str).str.strip().eq("").all(), "A recording-level support exclusion/reason is present.")
    require((joined["recording_source_stratum"] == joined["audit_source_stratum"]).all(), "Recording/row support strata disagree.")
    require(
        (joined["recording_recording_proxy_sources"] == joined["audit_recording_proxy_sources"]).all(),
        "Recording/row proxy-source records disagree.",
    )

    require(joined["audit_primary_surface_eligible"].astype(bool).all(), "Some chart rows are not primary-surface eligible in V4.")
    require(joined["audit_base_support_eligible"].astype(bool).all(), "Some chart rows fail base support eligibility in V4.")
    require(joined["audit_proxy_matches_ppg_rate"].astype(bool).all(), "Some chart rows do not match the declared PPG proxy.")
    require(joined["audit_support_exclusion_reasons"].fillna("").astype(str).str.strip().eq("").all(), "A chart row has a V4 support exclusion reason.")
    require(joined["audit_actual_sample_contributors_status"].eq("finite_causal_conservative_bound").all(), "Unexpected actual contributor support status.")
    require(joined["audit_input_sample_finite_status"].eq("all_finite").all(), "A chart row includes non-finite source samples.")
    require(pd.to_numeric(joined["audit_input_sample_gap_count"], errors="coerce").eq(0).all(), "A chart row has an input sample gap.")
    require(joined["audit_source_sample_mapping_status"].eq("nominal_bounds_mapped").all(), "A chart row has an unmapped nominal source interval.")
    require(joined["chart_coords_3d_all_finite"].all() and joined["chart_coords_9d_all_finite"].all(), "Non-finite chart coordinates found.")
    require(joined["chart_geometry_valid"].all(), "Geometry-invalid chart row found.")
    require(joined["geometry_contract_status"].eq("ok").all(), "Chart H5 geometry contract is not OK.")
    require(joined["coordinate_e_m_source"].eq("fallback").all(), "The frozen e_m fallback signature changed.")
    require(joined["coordinate_e_m_fallback_feature"].eq("ppg_rate_bpm").all(), "The frozen e_m fallback feature changed.")
    require(joined["coordinate_e_m_semantic_equivalence"].eq("false").all(), "Unexpected e_m semantic-equivalence claim.")
    require(joined["h5_temporal_support_status"].eq("unknown").all(), "Unexpected H5 temporal-support qualification; inspect before proceeding.")
    require(joined["h5_source_quality_status"].eq("not_recorded").all(), "Unexpected H5 source-quality qualification; inspect before proceeding.")

    role_files = joined.groupby("fold_role")["file"].nunique().to_dict()
    role_subjects = joined.groupby("fold_role")["subject"].nunique().to_dict()
    require(role_files == {"apply": 20, "training": 80}, f"Unexpected per-role recording counts: {role_files}")
    require(role_subjects == {"apply": 16, "training": 62}, f"Unexpected per-role subject counts: {role_subjects}")
    require(len(joined) == 92_545, f"Unexpected chart/support row count: {len(joined)}")
    mapped_rows_by_file = joined.groupby("file").size().sort_index()
    expected_rows_by_file = (
        joined[["file", "recording_primary_surface_eligible_rows"]]
        .drop_duplicates()
        .set_index("file")["recording_primary_surface_eligible_rows"]
        .astype(int)
        .sort_index()
    )
    require(mapped_rows_by_file.equals(expected_rows_by_file), "Mapped chart row counts differ from recording-level primary-eligible counts.")
    recording_counts = joined[["file", "recording_feature_rows", "recording_primary_surface_eligible_rows"]].drop_duplicates().copy()
    recording_counts["feature_rows_outside_primary_surface"] = (
        pd.to_numeric(recording_counts["recording_feature_rows"], errors="coerce")
        - pd.to_numeric(recording_counts["recording_primary_surface_eligible_rows"], errors="coerce")
    )
    require(
        recording_counts["feature_rows_outside_primary_surface"].ge(0).all(),
        "Primary-eligible count exceeds the recording's feature-row count.",
    )

    output_columns = [
        "fold_role",
        "subject",
        "bids_subject",
        "file",
        "epoch_id",
        "chart_window_start_sec",
        "chart_window_end_sec",
        "chart_time_center_sec",
        "chart_coords_3d_all_finite",
        "chart_coords_9d_all_finite",
        "chart_geometry_valid",
        "chart_coords_9d_valid",
        "chart_mnps_3d_valid",
        "chart_retained_after_qc",
        "geometry_contract_status",
        "anchor_id",
        "anchor_hash",
        "config_digest_sha256",
        "coordinate_e_m_source",
        "coordinate_e_m_fallback_feature",
        "coordinate_e_m_semantic_equivalence",
        "h5_signal_support_status",
        "h5_temporal_support_status",
        "h5_source_quality_status",
        "audit_source_stratum",
        "audit_recording_proxy_sources",
        "audit_row_proxy_source",
        "audit_proxy_matches_ppg_rate",
        "audit_base_support_eligible",
        "audit_primary_surface_eligible",
        "audit_support_exclusion_reasons",
        "audit_source_sample_mapping_status",
        "audit_source_sample_mapping_reason",
        "audit_nominal_source_sample_start",
        "audit_nominal_source_sample_end_exclusive",
        "audit_actual_sample_contributors_status",
        "feature_actual_sample_contributors_reason",
        "audit_actual_source_sample_start",
        "audit_actual_source_sample_end_exclusive",
        "audit_actual_source_time_start_sec",
        "audit_actual_source_time_end_sec",
        "audit_source_sfreq_hz",
        "audit_input_sample_finite_status",
        "audit_input_sample_gap_count",
        "audit_qc_ok_eeg",
        "audit_qc_ok_ppg",
        "recording_support_record_status",
        "recording_support_record_reasons",
        "recording_feature_rows",
        "recording_base_support_eligible_rows",
        "recording_primary_surface_eligible_rows",
        "recording_source_sha256",
        "expected_source_sha256",
        "source_hashes_match_fold_manifest",
        "chart_h5_relative_path",
    ]
    output = joined[output_columns].copy()
    require(not any("stage" in name.lower() or "label" in name.lower() for name in output.columns), "Outcome/label column leaked into support map.")

    output_dir.mkdir(parents=True, exist_ok=False)
    parquet_path = output_dir / "fold_0_chart_support_map.parquet"
    output.to_parquet(parquet_path, index=False, compression="zstd")

    anchor_paths = sorted({train_dir / "anchors" / f"{anchor}.json" for anchor in joined["anchor_id"].unique()})
    require(all(path.is_file() for path in anchor_paths), "A referenced fit anchor file is missing.")
    run_hashes = {
        role: sha256_file(CHART_ROOT / "processed" / "ds005555" / run / "run_manifest.json")
        for role, run in (("training", "fold_0_training_label_free_v2"), ("apply", "fold_0_apply_label_free_v2"))
    }
    provenance_inputs = {
        "fold_manifest": manifest_path,
        "v4_feature_parquet": feature_path,
        "v4_row_support_audit": row_audit_path,
        "v4_recording_audit": recording_audit_path,
        "v4_signal_support_ledger": support_ledger_path,
        "training_run_manifest": train_dir / "run_manifest.json",
        "apply_run_manifest": apply_dir / "run_manifest.json",
        "support_map_builder": Path(__file__).resolve(),
        "training_run_config": Path(run_details["training"]["provided_config_path"]),
        "apply_run_config": Path(run_details["apply"]["provided_config_path"]),
    }
    provenance_sha256 = {name: sha256_file(path) for name, path in provenance_inputs.items()}
    provenance_sha256["fit_anchor_files"] = {path.name: sha256_file(path) for path in anchor_paths}

    summary = {
        "schema_version": "boas.fold_safe_chart_support_map.v1",
        "verdict": "PARTIAL_PASS_SUPPORT_CROSSWALK",
        "scope": "outcome-blind support/provenance crosswalk only; no sleep-stage join, contrast, effect estimate, or biological qualification",
        "row_count": int(len(output)),
        "recording_count": int(output["file"].nunique()),
        "subject_count": int(output["subject"].nunique()),
        "counts_by_role": {key: int(value) for key, value in output.groupby("fold_role").size().to_dict().items()},
        "recordings_by_role": {key: int(value) for key, value in role_files.items()},
        "subjects_by_role": {key: int(value) for key, value in role_subjects.items()},
        "primary_surface_eligible_rows": int(output["audit_primary_surface_eligible"].astype(bool).sum()),
        "base_support_eligible_rows": int(output["audit_base_support_eligible"].astype(bool).sum()),
        "rows_with_nonfinite_3d_or_9d_coordinates": int((~output["chart_coords_3d_all_finite"] | ~output["chart_coords_9d_all_finite"]).sum()),
        "rows_with_geometry_invalidity": int((~output["chart_geometry_valid"]).sum()),
        "rows_with_source_sample_gaps": int(pd.to_numeric(output["audit_input_sample_gap_count"], errors="coerce").fillna(-1).ne(0).sum()),
        "source_strata": sorted(output["audit_source_stratum"].dropna().astype(str).unique().tolist()),
        "e_m_support_signature": {
            "source": sorted(output["coordinate_e_m_source"].unique().tolist()),
            "fallback_feature": sorted(output["coordinate_e_m_fallback_feature"].unique().tolist()),
            "semantic_equivalence": sorted(output["coordinate_e_m_semantic_equivalence"].unique().tolist()),
        },
        "external_v4_row_support": {
            "actual_sample_contributors_status": sorted(output["audit_actual_sample_contributors_status"].dropna().astype(str).unique().tolist()),
            "input_sample_finite_status": sorted(output["audit_input_sample_finite_status"].dropna().astype(str).unique().tolist()),
            "source_sample_mapping_status": sorted(output["audit_source_sample_mapping_status"].dropna().astype(str).unique().tolist()),
            "eligible_and_exclusion_free": bool(output["audit_primary_surface_eligible"].astype(bool).all() and output["audit_support_exclusion_reasons"].fillna("").astype(str).str.strip().eq("").all()),
        },
        "recording_level_support": {
            "recording_status": sorted(output["recording_support_record_status"].dropna().astype(str).unique().tolist()),
            "recording_reason_values": sorted(output["recording_support_record_reasons"].fillna("").astype(str).unique().tolist()),
            "mapped_rows_match_primary_eligible_counts": True,
            "recording_audit_feature_rows_exceed_primary_rows_in_recordings": int(
                recording_counts["feature_rows_outside_primary_surface"].gt(0).sum()
            ),
            "feature_rows_outside_primary_surface_total": int(
                recording_counts["feature_rows_outside_primary_surface"].sum()
            ),
            "count_definition": "recording_audit.feature_rows includes rows outside the primary surface; the chart crosswalk intentionally retains only primary_surface_eligible rows",
        },
        "bids_subject_matches_raw_file_name_for_all_recordings": True,
        "h5_generic_support_provenance": {
            "signal_support_status": sorted(output["h5_signal_support_status"].unique().tolist()),
            "temporal_support_status": sorted(output["h5_temporal_support_status"].unique().tolist()),
            "source_quality_status": sorted(output["h5_source_quality_status"].unique().tolist()),
            "qualification_note": "The external V4 row-level support audit is crosswalked but does not overwrite or promote the H5 generic support-provenance fields.",
        },
        "fold_manifest": {
            "split_id": manifest["split_id"],
            "signal_support_ledger_sha256_matches": ledger_hash == manifest["signal_support_ledger_sha256"],
            "source_file_hashes_match": bool(output["source_hashes_match_fold_manifest"].all()),
        },
        "runs": run_details,
        "fit_anchor_hashes": sorted(output["anchor_hash"].unique().tolist()),
        "config_digest_sha256": sorted(output["config_digest_sha256"].unique().tolist()),
        "resolved_config_digest_by_role": {
            role: run_details[role]["resolved_config_digest_sha256"] for role in ("training", "apply")
        },
        "provided_config_sha256_by_role": {
            role: run_details[role]["provided_config_sha256"] for role in ("training", "apply")
        },
        "label_join_performed": False,
        "contrasts_computed": False,
        "biological_claim_authorized": False,
        "output_parquet": parquet_path.relative_to(ARTICLE_ROOT).as_posix(),
        "output_parquet_sha256": sha256_file(parquet_path),
        "input_sha256": provenance_sha256,
        "limitations": [
            "The H5-level generic temporal-support field remains unknown and source-quality status remains not_recorded.",
            "The crosswalk validates row identity, finite causal source bounds, finite input/gap status, and fold source hashes; it is not an independent temporal-support qualification or outcome analysis.",
            "Recording-level feature_rows can exceed mapped chart rows because the map includes only primary_surface_eligible rows; mapped counts are checked against the primary-eligible count per recording.",
            "This is a support-only artifact and does not establish C1, C2, C3, sleep-stage effects, or biological interpretation.",
        ],
    }
    summary_path = output_dir / "validation.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="New output directory; existing directories are never overwritten.",
    )
    args = parser.parse_args()
    summary = build_map(args.output_dir.resolve())
    print(json.dumps({key: summary[key] for key in ("verdict", "row_count", "recording_count", "subjects_by_role", "output_parquet", "output_parquet_sha256")}, indent=2))


if __name__ == "__main__":
    main()
