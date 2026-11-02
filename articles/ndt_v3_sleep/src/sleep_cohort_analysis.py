"""Descriptive full-cohort delivery for the continuous ds005555 H5 manifest.

The article-local driver reuses ``new_family_sleep_analysis`` for exact
Jacobian-center and diffusion-query mapping.  It adds only source-manifest
coverage, explicit per-recording failures, and subject-level aggregation.
There is no estimator, stage refit, or pooled-window inference here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import h5py
import numpy as np

import new_family_sleep_analysis as e1e2


CONFIG_SCHEMA = "ndt.sleep.cohort_delivery_config.v1"
RUN_SCHEMA = "ndt.sleep.cohort_analysis.v1"
SUBJECT_RE = re.compile(r"sub-(\d+)")
EXPECTED_STATUS = {"computed", "not_testable", "unavailable", "invalid", "failed", "not_recorded"}
STAGE_KEYS = tuple(e1e2.STAGE_KEYS) if hasattr(e1e2, "STAGE_KEYS") else ("Wake", "N1", "N2", "N3", "REM", "Code8", "Unknown")
SURFACES: dict[str, str] = {
    "local_jacobian_3d": "/jacobian/derived_metrics/v1",
    "local_jacobian_9d": "/jacobian_9D/derived_metrics/v1",
    "finite_time_response": "/finite_time_response/v1/primary",
    "transition_residuals": "/transition_residuals/v1/primary",
    "transition_residual_covariance_proxy": "/transition_residual_covariance_proxy/v1/primary",
    "stochastic_reachability": "/stochastic_reachability/v1/primary",
    "diffusion_geometry": "/dynamical_families/diffusion/v1",
    "destination": "/dynamical_families/destination/v1",
    "resilience": "/dynamical_families/resilience/v1",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(e1e2._json_value(value), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _scalar(handle: h5py.File, path: str) -> Any:
    if path not in handle:
        return None
    value = handle[path][()]
    if isinstance(value, (bytes, np.bytes_)):
        return bytes(value).decode("utf-8", "replace")
    if isinstance(value, np.generic):
        value = value.item()
    return value


def _config(path: Path) -> dict[str, Any]:
    value = _json(path)
    if value.get("schema") != CONFIG_SCHEMA:
        raise ValueError(f"unsupported cohort config schema: {value.get('schema')!r}")
    endpoints = value.get("endpoints", [])
    expected = {
        ("local_jacobian", 3, "spectral_abscissa"),
        ("local_jacobian", 3, "numerical_abscissa"),
        ("local_jacobian", 3, "reactivity_gap"),
        ("local_jacobian", 9, "spectral_abscissa"),
        ("local_jacobian", 9, "numerical_abscissa"),
        ("local_jacobian", 9, "reactivity_gap"),
        ("diffusion_geometry", 3, "D_total"),
        ("diffusion_geometry", 3, "d_diff"),
        ("diffusion_geometry", 3, "c_diff"),
    }
    observed = {(str(item["family"]), int(item["dimension"]), str(metric)) for item in endpoints for metric in item.get("metrics", [])}
    if observed != expected:
        raise ValueError("cohort endpoint scope does not match the frozen E1/E2 contract")
    return value


def _subject_number(subject: str) -> int | None:
    match = SUBJECT_RE.fullmatch(str(subject))
    return int(match.group(1)) if match else None


def _continuous_marker(value: Mapping[str, Any]) -> bool:
    for key in ("cohort_role", "source_role", "run_role", "study_role", "delivery_role", "sampling_mode", "kind"):
        raw = value.get(key)
        if isinstance(raw, str):
            text = raw.lower().replace("-", "_").replace(" ", "_")
            if "stage_sample" in text or "stage_stratified" in text or "historical" in text:
                return False
            if "continuous_fullnight" in text or "continuous_full_night" in text:
                return True
    for key in ("continuous_fullnight", "continuous_full_night", "fullnight_continuous"):
        if value.get(key) is True:
            return True
    sampling = value.get("sampling")
    if isinstance(sampling, Mapping) and sampling.get("enabled") is False and value.get("full_night") is True:
        return True
    return False


def _entry_list(manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    for key in ("recordings", "entries", "h5_inputs", "inputs", "sources"):
        value = manifest.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, Mapping)]
    raise ValueError("source manifest has no recording entry list")


def _participant_tables(cfg: Mapping[str, Any]) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    """Load and hash the raw recording-to-participant identity tables."""
    table_cfg = cfg["source"].get("participant_tables")
    if not isinstance(table_cfg, Mapping):
        raise ValueError("source.participant_tables is required for participant-level aggregation")
    paths: dict[str, Path] = {}
    hashes: dict[str, str] = {}
    for name in ("tsv", "json"):
        item = table_cfg.get(name)
        if isinstance(item, str):
            item = {"path": item}
        if not isinstance(item, Mapping) or not item.get("path"):
            raise ValueError(f"participant table {name!r} requires a path")
        path = Path(str(item["path"])).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"participant table missing: {path}")
        digest = sha256(path)
        expected = item.get("sha256")
        if expected and digest.lower() != str(expected).lower():
            raise ValueError(f"participant table hash mismatch: {name}")
        paths[name], hashes[name] = path, digest
    rows: dict[str, dict[str, str]] = {}
    with paths["tsv"].open("r", encoding="utf-8", newline="") as stream:
        for raw in csv.DictReader(stream, delimiter="\t"):
            recording = str(raw.get("participant_id") or "").strip()
            participant = str(raw.get("pid") or "").strip()
            if not recording or not participant:
                raise ValueError("participants.tsv requires participant_id and pid for every row")
            if recording in rows:
                raise ValueError(f"duplicate recording in participants.tsv: {recording}")
            rows[recording] = {"recording_id": recording, "participant_id": participant}
    metadata = _json(paths["json"])
    if not isinstance(metadata, Mapping) or "participant_id" not in metadata or "pid" not in metadata:
        raise ValueError("participants.json does not describe participant_id and pid")
    if sha256(paths["tsv"]) != hashes["tsv"] or sha256(paths["json"]) != hashes["json"]:
        raise ValueError("participant identity tables changed while being read")
    provenance = {
        "tsv": {"path": str(paths["tsv"]), "sha256": hashes["tsv"]},
        "json": {"path": str(paths["json"]), "sha256": hashes["json"]},
        "recording_rows": len(rows),
        "unique_participants": len({row["participant_id"] for row in rows.values()}),
    }
    expected_unique = cfg["source"].get("expected_unique_participant_count")
    if expected_unique is not None and provenance["unique_participants"] != int(expected_unique):
        raise ValueError("participant table unique PID count does not match the frozen contract")
    return rows, provenance


def _validate_entries(
    entries: Sequence[Mapping[str, Any]],
    cfg: Mapping[str, Any],
    participant_rows: Mapping[str, Mapping[str, str]] | None = None,
) -> list[dict[str, Any]]:
    if not entries:
        raise ValueError("source manifest has no eligible recording entries")
    source_cfg = cfg["source"]
    expected_count = source_cfg.get("expected_subject_count")
    if expected_count is not None and len(entries) != int(expected_count):
        raise ValueError(f"expected {expected_count} recordings, found {len(entries)}")
    expected_ids = source_cfg.get("expected_subject_ids", {})
    if expected_ids:
        lo, hi = int(expected_ids["numeric_min"]), int(expected_ids["numeric_max"])
        expected = {f"{expected_ids['prefix']}{n}" for n in range(lo, hi + 1)}
    else:
        expected = None
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for raw in entries:
        subject = str(raw.get("subject") or raw.get("recording_id") or raw.get("participant") or "")
        path_text = str(raw.get("h5") or raw.get("h5_path") or raw.get("path") or "")
        if not subject:
            raise ValueError("every source entry requires a recording/subject identity")
        if _subject_number(subject) is None:
            raise ValueError(f"invalid numeric subject identity: {subject}")
        recording = str(raw.get("recording") or raw.get("recording_id") or Path(path_text).parent.name)
        if not recording:
            recording = subject
        key = (subject, recording)
        if key in seen:
            raise ValueError(f"duplicate subject/recording identity: {key}")
        seen.add(key)
        identity = participant_rows.get(recording) if participant_rows is not None else None
        if identity is None and participant_rows is not None:
            identity = participant_rows.get(subject)
        if participant_rows is not None and identity is None:
            raise ValueError(f"recording is absent from participants.tsv: {recording}")
        participant_id = str((identity or {}).get("participant_id") or raw.get("pid") or raw.get("participant_id") or "")
        if not participant_id:
            raise ValueError(f"missing unique participant identifier for {recording}")
        item = {
            "subject": subject,
            "recording": recording,
            "recording_id": recording,
            "participant_id": participant_id,
            "h5": path_text or None,
            "manifest_failure_reason": str(raw.get("failure_reason") or raw.get("error") or "h5_missing_in_manifest") if not path_text else None,
        }
        if path_text and source_cfg.get("require_one_h5_and_sha256_per_expected_recording") and not (raw.get("sha256") or raw.get("h5_sha256")):
            raise ValueError(f"existing H5 entry lacks required SHA-256: {recording}")
        if raw.get("sha256") or raw.get("h5_sha256"):
            item["expected_sha256"] = str(raw.get("sha256") or raw.get("h5_sha256")).lower()
        result.append(item)
    if expected is not None and {str(item["subject"]) for item in result} != expected:
        missing = sorted(expected - {str(item["subject"]) for item in result})
        extra = sorted({str(item["subject"]) for item in result} - expected)
        raise ValueError(f"subject manifest mismatch; missing={missing[:5]} extra={extra[:5]}")
    return sorted(result, key=lambda item: (_subject_number(item["subject"]) or 10**9, item["recording"]))


def _load_direct_manifest(path: Path, cfg: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    before = sha256(path)
    manifest = _json(path)
    if not isinstance(manifest, Mapping) or not _continuous_marker(manifest):
        raise ValueError("source manifest is not explicitly marked continuous_fullnight")
    participant_rows, participant_provenance = _participant_tables(cfg)
    entries = _validate_entries(_entry_list(manifest), cfg, participant_rows)
    after = sha256(path)
    if before != after:
        raise ValueError("source manifest changed while being read")
    return entries, {
        "mode": "direct_manifest",
        "path": str(path.resolve()),
        "sha256": before,
        "manifest": manifest,
        "participant_tables": participant_provenance,
    }


def _producer_h5_entries(execution: Mapping[str, Any]) -> tuple[list[Mapping[str, Any]], dict[str, Any] | None]:
    """Return the producer's explicit output list; directory discovery is forbidden."""
    for key in ("h5_outputs", "h5_entries", "recordings", "outputs"):
        value = execution.get(key)
        if isinstance(value, list):
            rows = [item for item in value if isinstance(item, Mapping)]
            if rows:
                return rows, None
        if isinstance(value, str) and Path(value).is_file():
            linked_path = Path(value).resolve()
            linked_before = sha256(linked_path)
            nested = _json(linked_path)
            if isinstance(nested, Mapping):
                linked_after = sha256(linked_path)
                if linked_before != linked_after:
                    raise ValueError("linked producer H5 manifest changed while being read")
                return _entry_list(nested), {"path": str(linked_path), "sha256": linked_before}
    manifest_path = execution.get("h5_manifest") or execution.get("output_manifest") or execution.get("analysis_input_manifest")
    if isinstance(manifest_path, Mapping):
        return _entry_list(manifest_path), None
    if isinstance(manifest_path, str) and Path(manifest_path).is_file():
        linked_path = Path(manifest_path).resolve()
        linked_before = sha256(linked_path)
        nested = _json(linked_path)
        if isinstance(nested, Mapping):
            linked_after = sha256(linked_path)
            if linked_before != linked_after:
                raise ValueError("linked producer H5 manifest changed while being read")
            return _entry_list(nested), {"path": str(linked_path), "sha256": linked_before}
    raise ValueError("completed ingest execution manifest has no explicit H5 output list")


def _discover_ingest_entries(cfg: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source = cfg["source"]
    inventory_path = Path(source["ingest_inventory_path"]).resolve()
    execution_path = Path(source["ingest_execution_manifest_path"]).resolve()
    if not inventory_path.is_file() or not execution_path.is_file():
        raise FileNotFoundError("current ingest inventory and completed execution manifest are required")
    inventory_before, execution_before = sha256(inventory_path), sha256(execution_path)
    inventory, execution = _json(inventory_path), _json(execution_path)
    if inventory.get("schema") != "nmdm.sleep_dataset_delivery_inventory.v1":
        raise ValueError("unexpected ingest inventory schema")
    if inventory.get("dataset") != cfg.get("dataset_id"):
        raise ValueError("ingest inventory dataset mismatch")
    if execution.get("status") != "completed" or execution.get("scope") != "full":
        raise ValueError("ingest execution manifest is not a completed full cohort")
    config_text = str(execution.get("config", "")).lower()
    if "continuous_delivery" not in config_text:
        raise ValueError("execution manifest is not the continuous delivery run")
    if execution.get("source_hashes_stable") is not True or execution.get("config_stable") is not True or execution.get("config_tree_stable") is not True:
        raise ValueError("ingest execution manifest has unstable source/config provenance")
    processed = Path(source["processed_root"]).resolve()
    recorded_processed = Path(str(execution.get("processed_root", ""))).resolve()
    if recorded_processed != processed:
        raise ValueError(f"processed root mismatch: config={processed} execution={recorded_processed}")
    subjects = [str(item) for item in inventory.get("subject_ids", [])]
    if len(subjects) != int(source.get("expected_subject_count", len(subjects))):
        raise ValueError("ingest inventory subject count does not match the frozen cohort size")
    if int(inventory.get("counts", {}).get("eligible_psg_subjects", -1)) != len(subjects):
        raise ValueError("ingest inventory has ineligible PSG subjects")
    participant_rows, participant_provenance = _participant_tables(cfg)
    producer_entries, linked_h5_manifest = _producer_h5_entries(execution)
    entries_by_subject: dict[str, Mapping[str, Any]] = {}
    for raw in producer_entries:
        subject = str(raw.get("subject") or raw.get("recording_id") or raw.get("participant") or "")
        if subject:
            if subject in entries_by_subject:
                raise ValueError(f"duplicate producer H5 output for {subject}")
            entries_by_subject[subject] = raw
    extra_subjects = set(entries_by_subject) - set(subjects)
    if extra_subjects:
        raise ValueError(f"producer H5 output list has subjects outside the frozen inventory: {sorted(extra_subjects)[:5]}")
    entries: list[Mapping[str, Any]] = []
    for subject in subjects:
        entries.append(entries_by_subject.get(subject, {"subject": subject, "recording": subject, "h5": None, "failure_reason": "producer_h5_missing"}))
    if sha256(inventory_path) != inventory_before or sha256(execution_path) != execution_before:
        raise ValueError("ingest manifest changed while being read")
    entries = _validate_entries(entries, cfg, participant_rows)
    return entries, {
        "mode": "ingest_inventory_and_execution_manifest",
        "inventory_path": str(inventory_path),
        "inventory_sha256": inventory_before,
        "execution_manifest_path": str(execution_path),
        "execution_manifest_sha256": execution_before,
        "processed_root": str(processed),
        "execution": execution,
        "participant_tables": participant_provenance,
        "linked_h5_manifest": linked_h5_manifest,
    }


def load_sources(cfg: Mapping[str, Any], *, source_manifest: Path | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    direct = source_manifest or (Path(cfg["source"]["manifest_path"]).resolve() if cfg["source"].get("manifest_path") else None)
    if direct is not None:
        return _load_direct_manifest(direct, cfg)
    return _discover_ingest_entries(cfg)


def _surface_inventory(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    with h5py.File(path, "r") as handle:
        for name, base in SURFACES.items():
            present = base in handle
            item: dict[str, Any] = {"available": present, "path": base}
            if present:
                item.update({key: e1e2._json_value(_scalar(handle, f"{base}/{key}")) for key in ("computation_status", "measurement_validity", "claim_status", "failure_reason")})
            else:
                item.update({"computation_status": "unavailable", "measurement_validity": "not_recorded", "claim_status": "not_recorded", "failure_reason": "surface_missing"})
            result[name] = item
    return result


def _recording_stats(
    rows: Sequence[Mapping[str, Any]],
    recording_id: str,
    participant_id: str,
    *,
    source_status: str = "ok",
    failure_reason: str | None = None,
    prior_development2: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    recording = str(rows[0].get("recording")) if rows else recording_id
    summaries, contrasts = e1e2.summarize_all(rows, recordings=[recording])
    for item in summaries:
        item["subject"] = recording_id
        item["recording_id"] = recording_id
        item["participant_id"] = participant_id
        item["recording"] = item.get("recording") or recording
        item["source_status"] = source_status
        item["failure_reason"] = failure_reason
        item["prior_development2"] = prior_development2
    for item in contrasts:
        item["subject"] = recording_id
        item["recording_id"] = recording_id
        item["participant_id"] = participant_id
        item["source_status"] = source_status
        item["failure_reason"] = failure_reason
        item["prior_development2"] = prior_development2
    return summaries, contrasts


def _fullnight_evidence(path: Path) -> dict[str, Any]:
    """Check executed H5 continuity and 30-second cadence, not legacy attrs."""
    with h5py.File(path, "r") as handle:
        required = ("/time", "/window_start", "/window_end", "/epoch_id")
        missing = [name for name in required if name not in handle]
        if missing:
            raise ValueError(f"fullnight evidence missing datasets: {missing}")
        time_values = np.asarray(handle["/time"][()], dtype=float)
        starts = np.asarray(handle["/window_start"][()], dtype=float)
        ends = np.asarray(handle["/window_end"][()], dtype=float)
        if time_values.size < 2 or starts.size == 0 or ends.size != starts.size:
            raise ValueError("fullnight evidence has insufficient time bounds")
        dt = np.diff(time_values)
        start_dt = np.diff(starts)
        end_dt = np.diff(ends)
        widths = ends - starts
        if not np.all(np.isfinite(dt)) or not np.all(np.isfinite(start_dt)) or not np.all(np.isfinite(end_dt)) or not np.all(np.isfinite(widths)):
            raise ValueError("fullnight evidence contains nonfinite time bounds")
        dt_median = float(np.median(dt))
        width_median = float(np.median(widths))
        gap_count = int(np.count_nonzero(~np.isclose(start_dt, 30.0, rtol=0.0, atol=1e-6)))
        end_gap_count = int(np.count_nonzero(~np.isclose(end_dt, 30.0, rtol=0.0, atol=1e-6)))
        center_mismatch_count = int(np.count_nonzero(~np.isclose(time_values, (starts + ends) / 2.0, rtol=0.0, atol=1e-6)))
        measured = handle.attrs.get("coverage_seconds_measured")
        measured = float(measured) if measured is not None else float(time_values[-1] - time_values[0] + width_median)
        if not np.isfinite(measured) or measured <= 0:
            raise ValueError("H5 has no positive measured recording coverage")
        span = float(ends[-1] - starts[0])
        epoch_raw = handle.attrs.get("epochs_raw")
        epoch_raw = int(epoch_raw) if epoch_raw is not None else int(time_values.size)
        config_dt = _scalar(handle, "/provenance/geometry_contract/time_grid/dt_sec_epoch_config")
        if config_dt is None:
            config_dt = handle.attrs.get("dt_sec_epoch_config")
        if not np.isclose(dt_median, 30.0, rtol=0.0, atol=1e-6) or not np.isclose(width_median, 30.0, rtol=0.0, atol=1e-6) or gap_count or end_gap_count or center_mismatch_count or epoch_raw != int(time_values.size) or config_dt is None or not np.isclose(float(config_dt), 30.0, rtol=0.0, atol=1e-6) or not np.isclose(measured, span, rtol=0.0, atol=1e-6):
            raise ValueError(
                "H5 is not a continuous 30-second full-night execution: "
                f"dt={dt_median}, width={width_median}, gaps={gap_count + end_gap_count}, "
                f"center_mismatch={center_mismatch_count}, epochs_raw={epoch_raw}, "
                f"config_dt={config_dt}, measured={measured}, span={span}"
            )
        support = {}
        support_base = "/provenance/signal_support_provenance"
        for key in ("status", "temporal_support_status", "temporal_support_reason"):
            support[key] = e1e2._json_value(_scalar(handle, f"{support_base}/{key}"))
        return {
            "time_points": int(time_values.size),
            "window_count": int(starts.size),
            "dt_seconds_median": dt_median,
            "window_width_seconds_median": width_median,
            "coverage_seconds_measured": measured,
            "coverage_span_seconds": span,
            "gap_count": gap_count + end_gap_count,
            "center_mismatch_count": center_mismatch_count,
            "epochs_raw": epoch_raw,
            "support_provenance": support,
        }


def _aggregate(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {"n_participants": 0, "median": None, "q25": None, "q75": None}
    array = np.asarray(values, dtype=float)
    return {"n_participants": int(len(array)), "median": float(np.median(array)), "q25": float(np.quantile(array, 0.25)), "q75": float(np.quantile(array, 0.75))}


def participant_stage_summaries(rows: Sequence[Mapping[str, Any]], participant_ids: Sequence[str]) -> list[dict[str, Any]]:
    """Collapse recording-stage medians to one row per unique participant."""
    keys = [(family, dimension, metric, stage) for family, dimension, metric in e1e2.EXPECTED_ENDPOINTS for stage in STAGE_KEYS]
    output: list[dict[str, Any]] = []
    for family, dimension, metric, stage in keys:
        for participant_id in sorted(set(str(item) for item in participant_ids)):
            selected = [row for row in rows if (row.get("family"), row.get("dimension"), row.get("metric"), row.get("stage_key"), str(row.get("participant_id"))) == (family, dimension, metric, stage, participant_id) and row.get("median") is not None]
            values = [float(row["median"]) for row in selected]
            participant_recordings = [row for row in rows if str(row.get("participant_id")) == participant_id]
            output.append({
                "participant_id": participant_id,
                "family": family,
                "dimension": dimension,
                "metric": metric,
                "stage_key": stage,
                "recording_count": len(values),
                "prior_development2": any(bool(row.get("prior_development2")) for row in participant_recordings),
                **e1e2._stats(values),
            })
    return output


def participant_contrasts(rows: Sequence[Mapping[str, Any]], participant_ids: Sequence[str]) -> list[dict[str, Any]]:
    """Collapse recording paired contrasts to one row per unique participant."""
    keys = list(e1e2.EXPECTED_ENDPOINTS)
    output: list[dict[str, Any]] = []
    for family, dimension, metric in keys:
        for participant_id in sorted(set(str(item) for item in participant_ids)):
            selected = [row for row in rows if (row.get("family"), row.get("dimension"), row.get("metric"), str(row.get("participant_id"))) == (family, dimension, metric, participant_id) and row.get("n2_minus_wake_median") is not None]
            values = [float(row["n2_minus_wake_median"]) for row in selected]
            participant_recordings = [row for row in rows if str(row.get("participant_id")) == participant_id]
            output.append({
                "participant_id": participant_id,
                "family": family,
                "dimension": dimension,
                "metric": metric,
                "contrast": "N2_minus_Wake",
                "recording_count": len(values),
                "prior_development2": any(bool(row.get("prior_development2")) for row in participant_recordings),
                "n2_minus_wake_median": float(np.median(values)) if values else None,
                "n2_minus_wake_q25": float(np.quantile(values, 0.25)) if values else None,
                "n2_minus_wake_q75": float(np.quantile(values, 0.75)) if values else None,
            })
    return output


def cohort_stage_summaries(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    keys = sorted({(row.get("family"), row.get("dimension"), row.get("metric"), row.get("stage_key")) for row in rows}, key=str)
    return [{"family": family, "dimension": dimension, "metric": metric, "stage_key": stage, **_aggregate([float(row["median"]) for row in rows if (row.get("family"), row.get("dimension"), row.get("metric"), row.get("stage_key")) == (family, dimension, metric, stage) and row.get("median") is not None])} for family, dimension, metric, stage in keys]


def cohort_contrasts(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    keys = sorted({(row.get("family"), row.get("dimension"), row.get("metric")) for row in rows}, key=str)
    return [{"family": family, "dimension": dimension, "metric": metric, "contrast": "N2_minus_Wake", **_aggregate([float(row["n2_minus_wake_median"]) for row in rows if (row.get("family"), row.get("dimension"), row.get("metric")) == (family, dimension, metric) and row.get("n2_minus_wake_median") is not None])} for family, dimension, metric in keys]


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fields = sorted({str(key) for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or ["status"])
        writer.writeheader()
        writer.writerows({field: e1e2._json_value(row.get(field)) for field in fields} for row in rows)


def run(config_path: Path, output: Path, *, source_manifest: Path | None = None) -> dict[str, Any]:
    config_path, output = Path(config_path).resolve(), Path(output).resolve()
    cfg = _config(config_path)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite output: {output}")
    entries, source_provenance = load_sources(cfg, source_manifest=source_manifest)
    output.mkdir(parents=True, exist_ok=False)
    source_outcomes: list[dict[str, Any]] = []
    endpoint_rows: list[dict[str, Any]] = []
    recording_summaries: list[dict[str, Any]] = []
    recording_contrasts: list[dict[str, Any]] = []
    family_inventory: list[dict[str, Any]] = []
    prior_subjects = {str(item) for item in cfg["source"].get("prior_development_subjects", [])}
    for entry in entries:
        recording_id = str(entry["recording_id"])
        participant_id = str(entry["participant_id"])
        prior_development2 = str(entry["subject"]) in prior_subjects
        path = Path(entry["h5"]).resolve() if entry.get("h5") else None
        outcome: dict[str, Any] = {
            **entry,
            "h5": str(path) if path else None,
            "status": "failed",
            "failure_reason": None,
            "prior_development2": prior_development2,
        }
        if path is None:
            outcome["failure_reason"] = entry.get("manifest_failure_reason") or "h5_missing"
            summaries, contrasts = _recording_stats([], recording_id, participant_id, source_status="failed", failure_reason=outcome["failure_reason"], prior_development2=prior_development2)
            recording_summaries.extend(summaries)
            recording_contrasts.extend(contrasts)
            source_outcomes.append(outcome)
            continue
        if not path.is_file():
            outcome["failure_reason"] = "h5_missing"
            summaries, contrasts = _recording_stats([], recording_id, participant_id, source_status="failed", failure_reason=outcome["failure_reason"], prior_development2=prior_development2)
            recording_summaries.extend(summaries)
            recording_contrasts.extend(contrasts)
            source_outcomes.append(outcome)
            continue
        before = sha256(path)
        outcome["h5_sha256_before"] = before
        expected = entry.get("expected_sha256")
        if expected and before.lower() != str(expected).lower():
            outcome["failure_reason"] = "h5_hash_mismatch"
            summaries, contrasts = _recording_stats([], recording_id, participant_id, source_status="failed", failure_reason=outcome["failure_reason"], prior_development2=prior_development2)
            recording_summaries.extend(summaries)
            recording_contrasts.extend(contrasts)
            source_outcomes.append(outcome)
            continue
        pending_rows: list[dict[str, Any]] = []
        pending_summaries: list[dict[str, Any]] = []
        pending_contrasts: list[dict[str, Any]] = []
        pending_inventory: dict[str, Any] | None = None
        try:
            outcome["fullnight_evidence"] = _fullnight_evidence(path)
            rows, metadata = e1e2.endpoint_rows_for_recording(path, str(entry["recording"]))
            pending_rows = [{**row, "subject": recording_id, "recording_id": recording_id, "participant_id": participant_id, "prior_development2": prior_development2} for row in rows]
            pending_summaries, pending_contrasts = _recording_stats(rows, recording_id, participant_id, prior_development2=prior_development2)
            pending_inventory = {"subject": recording_id, "recording_id": recording_id, "participant_id": participant_id, "prior_development2": prior_development2, "surfaces": _surface_inventory(path)}
        except Exception as exc:  # preserve a per-entry failure and continue coverage
            outcome["failure_reason"] = f"analysis_error:{type(exc).__name__}:{exc}"
        after = sha256(path)
        outcome["h5_sha256_after"] = after
        if before != after and outcome.get("failure_reason") is None:
            outcome["status"] = "failed"
            outcome["failure_reason"] = "h5_changed_during_read"
        if outcome.get("failure_reason") is not None:
            outcome["status"] = "failed"
            summaries, contrasts = _recording_stats([], recording_id, participant_id, source_status="failed", failure_reason=outcome["failure_reason"], prior_development2=prior_development2)
            recording_summaries.extend(summaries)
            recording_contrasts.extend(contrasts)
        else:
            outcome.update({"status": "ok", "failure_reason": None})
            endpoint_rows.extend(pending_rows)
            recording_summaries.extend(pending_summaries)
            recording_contrasts.extend(pending_contrasts)
            if pending_inventory is not None:
                family_inventory.append(pending_inventory)
        source_outcomes.append(outcome)
    failed = [item for item in source_outcomes if item.get("status") != "ok"]
    participant_ids = sorted({str(entry["participant_id"]) for entry in entries})
    participant_summaries = participant_stage_summaries(recording_summaries, participant_ids)
    participant_contrast_rows = participant_contrasts(recording_contrasts, participant_ids)
    manifest = {
        "schema": RUN_SCHEMA,
        "status": "completed" if not failed else "completed_with_failures",
        "claim_status": cfg.get("claim_status", "no_biological_claim"),
        "dataset_id": cfg.get("dataset_id"),
        "source_provenance": source_provenance,
        "source_count_expected": len(entries),
        "source_count_ok": len(entries) - len(failed),
        "source_count_failed": len(failed),
        "recording_count": len(entries),
        "participant_count_expected": len(participant_ids),
        "participant_ids": participant_ids,
        "config": {"path": str(config_path), "sha256": sha256(config_path)},
        "runner": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
        "aggregation": cfg["aggregation"],
        "reference": cfg["reference"],
        "prior_development2_subjects": sorted(prior_subjects),
        "development2_files_excluded": True,
        "outputs": [
            "analysis_manifest.json", "source_outcomes.json", "endpoint_rows.json",
            "recording_stage_summaries.json", "recording_n2_minus_wake.json",
            "participant_stage_summaries.json", "participant_n2_minus_wake.json",
            "cohort_stage_summaries.json", "cohort_n2_minus_wake.json", "family_inventory.json",
        ],
    }
    _write_json(output / "source_outcomes.json", source_outcomes)
    _write_json(output / "endpoint_rows.json", endpoint_rows)
    _write_json(output / "recording_stage_summaries.json", recording_summaries)
    _write_json(output / "recording_n2_minus_wake.json", recording_contrasts)
    _write_json(output / "participant_stage_summaries.json", participant_summaries)
    _write_json(output / "participant_n2_minus_wake.json", participant_contrast_rows)
    _write_json(output / "cohort_stage_summaries.json", cohort_stage_summaries(participant_summaries))
    _write_json(output / "cohort_n2_minus_wake.json", cohort_contrasts(participant_contrast_rows))
    _write_json(output / "family_inventory.json", family_inventory)
    _write_csv(output / "endpoint_rows.csv", endpoint_rows)
    _write_csv(output / "recording_stage_summaries.csv", recording_summaries)
    _write_csv(output / "recording_n2_minus_wake.csv", recording_contrasts)
    _write_csv(output / "participant_stage_summaries.csv", participant_summaries)
    _write_csv(output / "participant_n2_minus_wake.csv", participant_contrast_rows)
    _write_json(output / "analysis_manifest.json", manifest)
    return manifest


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(run(args.config, args.output, source_manifest=args.source_manifest), indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
