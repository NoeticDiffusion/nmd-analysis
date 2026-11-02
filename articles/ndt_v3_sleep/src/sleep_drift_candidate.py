"""Run the frozen, bounded sleep drift candidate pilot.

This article-local runner is deliberately small and read-only.  It freezes the
two source H5 identities and the M3 split before reading predictions, calls the
installed analysis-owned ``crossfit_local_chart_b`` estimator, and writes
candidate diagnostics.  The output is not an empirical drift estimate,
qualification, stage contrast, or biological result.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
from typing import Any, Iterable

import h5py
import numpy as np

from nmd_analysis.dynamical_families import drift


EXPECTED_SOURCE_HASHES = {
    "sub-99": "217991681011397acd4493cd97cc74e7a982d361a04e6e94d29b40c8261ef8a1",
    "sub-1": "1eba1d7d9a470647992ab729f26a4ee5cea9249586e7e98cbad814759cff94db",
}
EXPECTED_COORDINATES = {
    "mnps_3d": {
        "h5_path": "mnps_3d",
        "dimension": 3,
        "axis_names": ["m", "d", "e"],
        "coordinate_layer": "mnps_3d",
    },
    "coords_9d": {
        "h5_path": "coords_9d/values",
        "dimension": 9,
        "axis_names": ["m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m"],
        "coordinate_layer": "coords_9d/values",
    },
}


class CandidateContractError(ValueError):
    """Raised when the frozen article candidate contract is violated."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, (bytes, np.bytes_)):
        return value.decode("utf-8")
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _scalar(value: Any) -> Any:
    if isinstance(value, (bytes, np.bytes_)):
        return value.decode("utf-8")
    return value.item() if isinstance(value, np.generic) else value


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _read_config(path: Path) -> tuple[dict[str, Any], str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema") != "ndt.sleep.sleep_drift_candidate.v1":
        raise CandidateContractError("unexpected sleep drift candidate config schema")
    spec = raw.get("spec")
    expected = raw.get("frozen_spec_sha256")
    if not isinstance(spec, dict) or not isinstance(expected, str):
        raise CandidateContractError("config must contain a frozen spec and frozen_spec_sha256")
    actual = sha256_bytes(_canonical_json(spec))
    if actual != expected:
        raise CandidateContractError("frozen spec hash does not match config spec")
    if raw.get("status") != "frozen_candidate_not_qualified":
        raise CandidateContractError("config status must remain frozen_candidate_not_qualified")
    return raw, actual, sha256_file(path)


def _check_frozen_spec(spec: dict[str, Any]) -> None:
    sources = spec.get("sources")
    if not isinstance(sources, list) or len(sources) != 2:
        raise CandidateContractError("exactly two frozen E1/E2 source H5s are required")
    seen_names: set[str] = set()
    seen_hashes: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise CandidateContractError("source entries must be objects")
        recording = str(source.get("recording", ""))
        if recording in seen_names or recording not in EXPECTED_SOURCE_HASHES:
            raise CandidateContractError("sources must be the exact sub-99 and sub-1 pair")
        expected_hash = str(source.get("sha256", "")).lower()
        if expected_hash != EXPECTED_SOURCE_HASHES[recording] or expected_hash in seen_hashes:
            raise CandidateContractError(f"unexpected frozen H5 hash for {recording}")
        seen_names.add(recording)
        seen_hashes.add(expected_hash)
    if seen_names != set(EXPECTED_SOURCE_HASHES):
        raise CandidateContractError("the frozen source set is incomplete")

    split = spec.get("split")
    if split != {
        "train_increment_range": [0, 600],
        "evaluation_increment_range": [700, 800],
        "embargo_sec": 60.0,
        "n_neighbors": 32,
        "min_train_support": 12,
        "estimators": ["local_mean", "local_linear"],
    }:
        raise CandidateContractError("candidate split or estimator settings differ from the frozen M3 spec")
    coordinates = spec.get("coordinates")
    if not isinstance(coordinates, list) or [row.get("name") for row in coordinates] != ["mnps_3d", "coords_9d"]:
        raise CandidateContractError("candidate coordinate order must be mnps_3d then coords_9d")
    for row in coordinates:
        name = row.get("name")
        expected = EXPECTED_COORDINATES.get(name)
        if expected is None or any(row.get(key) != value for key, value in expected.items()):
            raise CandidateContractError(f"coordinate specification is not frozen for {name}")


def _support_intervals(time: np.ndarray, starts: np.ndarray, ends: np.ndarray, indices: np.ndarray) -> np.ndarray:
    if any(array.shape != time.shape for array in (starts, ends)):
        raise CandidateContractError("time and epoch support arrays are not aligned")
    actual = np.column_stack((time[indices], time[indices + 1]))
    support = np.column_stack((np.minimum(starts[indices], starts[indices + 1]), np.maximum(ends[indices], ends[indices + 1])))
    if not np.isfinite(support).all() or np.any(support[:, 1] < support[:, 0]):
        raise CandidateContractError("epoch support bounds are nonfinite or unordered")
    if np.any(support[:, 0] > actual[:, 0]) or np.any(support[:, 1] < actual[:, 1]):
        raise CandidateContractError("epoch support does not contain increment endpoints")
    return support


def _support_audit(train_support: np.ndarray, evaluation_support: np.ndarray, embargo: float) -> dict[str, Any]:
    if (
        train_support.ndim != 2
        or evaluation_support.ndim != 2
        or train_support.shape[1] != 2
        or evaluation_support.shape[1] != 2
        or not np.isfinite(train_support).all()
        or not np.isfinite(evaluation_support).all()
        or np.any(train_support[:, 1] < train_support[:, 0])
        or np.any(evaluation_support[:, 1] < evaluation_support[:, 0])
    ):
        raise CandidateContractError("epoch support audit requires finite ordered intervals")
    with np.errstate(over="raise", invalid="raise"):
        distances = np.maximum(
            train_support[:, None, 0] - evaluation_support[None, :, 1],
            evaluation_support[None, :, 0] - train_support[:, None, 1],
        )
    if not np.isfinite(distances).all():
        raise CandidateContractError("epoch support separation is nonfinite")
    violations = np.argwhere(distances <= embargo)
    minimum = float(np.min(distances))
    return {
        "embargo_sec": float(embargo),
        "minimum_train_evaluation_support_distance_sec": minimum,
        "embargo_satisfied": bool(not len(violations)),
        "embargo_violation_count": int(len(violations)),
        "embargo_violation_pairs": [[int(i), int(j)] for i, j in violations.tolist()],
        "support_separation_semantics": "epoch_window_union_distance; full upstream signal support unknown",
        "full_signal_support_status": "unknown",
        "coordinate_fit_population_status": "unknown_global_upstream_fit_population",
    }


def _attribute_provenance(handle: h5py.File, name: str, path: str, names: list[str]) -> dict[str, Any]:
    dataset = handle[path]
    root_attrs = {str(key): _json_safe(_scalar(value)) for key, value in handle.attrs.items() if key in {
        "schema_version", "primary_coordinate_contract", "primary_coordinate_layer", "mnps_axis_names",
        "coords_9d_hash_saved", "coords_9d_hash_knn_input", "coords_9d_hash_jacobian_input",
        "x_hash_saved", "x_hash_knn_input", "x_hash_jacobian_input", "subject_id", "normalize_mode",
        "mnps_9d_definition_version", "x_definition", "v2_definition", "v2_missing_policy",
    }}
    anchored_path = "coords_3d_subject_anchored/values" if name == "mnps_3d" else "coords_9d_subject_anchored/values"
    equality_observed: bool | None = None
    anchored_hash: str | None = None
    if anchored_path in handle:
        anchored = np.asarray(handle[anchored_path], dtype=float)
        explicit = np.asarray(dataset, dtype=float)
        equality_observed = bool(anchored.shape == explicit.shape and np.array_equal(anchored, explicit, equal_nan=False))
        anchored_hash = sha256_bytes(np.ascontiguousarray(anchored.astype(np.float64)).tobytes())
    return {
        "name": name,
        "dataset_path": path,
        "dimension": int(dataset.shape[1]),
        "axis_names": names,
        "dtype_on_disk": str(dataset.dtype),
        "source_primary_coordinate_contract": root_attrs.get("primary_coordinate_contract", "not_recorded"),
        "source_primary_coordinate_layer": root_attrs.get("primary_coordinate_layer", "not_recorded"),
        "source_root_attrs": root_attrs,
        "observed_equality_to_subject_anchored_path": equality_observed,
        "subject_anchored_values_hash_observed": anchored_hash,
        "comparison_to_e1_e2": "explicit candidate chart path; any equality to a subject_anchored path is observed in this H5 only and is not a general alias guarantee",
    }


def _signal_support_provenance(handle: h5py.File) -> dict[str, Any]:
    """Retain source temporal-support and whole-record fit-population limits."""
    base = "provenance/signal_support_provenance"
    result: dict[str, Any] = {
        "status": "not_recorded",
        "schema": "not_recorded",
        "temporal_support_status": "unknown",
        "temporal_support_reason": "not_recorded",
        "per_feature_dependency_status": "not_assessed",
        "reference_fit_population_status": "not_recorded",
        "reference_fit_population_counts": [],
        "reference_fit_population_hashes": [],
        "reference_fit_scopes": [],
        "operation_scope": "not_recorded",
        "per_epoch_support_status": "unknown",
        "per_epoch_support_reason": "not_recorded",
    }
    if base not in handle:
        return result
    result["status"] = "recorded"
    for key in ("status", "schema", "temporal_support_status", "temporal_support_reason"):
        path = f"{base}/{key}"
        if path in handle:
            result[key] = _scalar(handle[path][()])
    extent_path = f"{base}/per_epoch_input_extent_json"
    if extent_path in handle:
        try:
            first_extent = json.loads(_scalar(handle[extent_path][()]))[0]
            result["operation_scope"] = first_extent.get("operation_scope", "not_recorded")
            result["per_epoch_support_status"] = first_extent.get("support_status", "unknown")
            result["per_epoch_support_reason"] = first_extent.get("support_reason", "not_recorded")
        except (IndexError, TypeError, json.JSONDecodeError):
            result["operation_scope"] = "malformed_or_unavailable"
            result["per_epoch_support_status"] = "malformed_or_unavailable"
    result["per_feature_dependency_status"] = "effective feature/filter support not certified by epoch bounds"
    fit_base = f"{base}/reference_fit_population"
    if fit_base not in handle:
        return result
    status_path = f"{fit_base}/status"
    if status_path in handle:
        result["reference_fit_population_status"] = _scalar(handle[status_path][()])
    features = handle.get(f"{fit_base}/features")
    if features is None:
        return result
    counts: set[int] = set()
    hashes: set[str] = set()
    scopes: set[str] = set()
    for feature in features:
        for field, target in (("fit_population_count", counts), ("fit_population_hash", hashes), ("fit_scope", scopes)):
            path = f"{fit_base}/features/{feature}/{field}"
            if path not in handle:
                continue
            value = _scalar(handle[path][()])
            target.add(int(value) if field == "fit_population_count" else str(value))
    result["reference_fit_population_counts"] = sorted(counts)
    result["reference_fit_population_hashes"] = sorted(hashes)
    result["reference_fit_scopes"] = sorted(scopes)
    return result


def _support_signature(handle: h5py.File) -> dict[str, Any]:
    """Record compact per-coordinate fallback/source provenance."""
    base = "support_signature/v1"
    result: dict[str, Any] = {"status": "not_recorded", "capability": {}, "coordinates": {}}
    if base not in handle:
        return result
    result["status"] = "recorded"
    schema_path = f"{base}/schema_version"
    result["schema_version"] = _scalar(handle[schema_path][()]) if schema_path in handle else "not_recorded"
    for capability in ("chart_3d", "chart_9d", "diffusion"):
        path = f"{base}/capability/{capability}"
        if path in handle:
            result["capability"][capability] = _scalar(handle[path][()])
    for coordinate in ("e_m",):
        result["coordinates"][coordinate] = {}
        for field in ("source", "fallback_feature", "semantic_equivalence"):
            path = f"{base}/coordinates/{coordinate}/{field}"
            if path in handle:
                result["coordinates"][coordinate][field] = _scalar(handle[path][()])
    return result


def _read_source(source: dict[str, Any], spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, np.ndarray], str, str]:
    path = Path(str(source["path"])).resolve()
    before = sha256_file(path)
    if before != str(source["sha256"]).lower():
        raise CandidateContractError(f"source H5 hash does not match frozen spec: {path}")
    split = spec["split"]
    train = np.arange(*split["train_increment_range"], dtype=np.int64)
    evaluation = np.arange(*split["evaluation_increment_range"], dtype=np.int64)
    with h5py.File(path, "r") as handle:
        required = ["time", "window_start", "window_end", "epoch_id", "mnps_3d", "coords_9d/values", "coords_9d/names"]
        missing = [item for item in required if item not in handle]
        if missing:
            raise CandidateContractError(f"source is missing required explicit datasets: {missing}")
        time = np.asarray(handle["time"], dtype=float)
        starts = np.asarray(handle["window_start"], dtype=float)
        ends = np.asarray(handle["window_end"], dtype=float)
        epoch_id = np.asarray(handle["epoch_id"])
        n = len(time)
        if n <= int(np.max(evaluation)) + 1 or any(array.shape != (n,) for array in (starts, ends, epoch_id)):
            raise CandidateContractError("source cannot support the frozen split or aligned epoch arrays")
        if not np.isfinite(time).all() or np.any(np.diff(time) <= 0):
            raise CandidateContractError("source time must be finite and strictly increasing")
        dt = np.diff(time)
        if not np.isfinite(dt).all() or not np.all(dt == 30.0):
            raise CandidateContractError("source does not satisfy the frozen 30-second dt contract")
        if not np.isfinite(starts).all() or not np.isfinite(ends).all() or np.any(starts >= ends):
            raise CandidateContractError("source epoch support bounds are invalid")
        if not np.all(ends - starts == 30.0) or not np.all(ends[:-1] == starts[1:]):
            raise CandidateContractError("source does not satisfy the frozen contiguous 30-second window contract")
        if np.any(time < starts) or np.any(time > ends):
            raise CandidateContractError("source timepoints are outside their epoch support")
        if np.unique(epoch_id).size != n:
            raise CandidateContractError("source epoch_id values are not unique")
        schema = _scalar(handle.attrs.get("schema_version", "not_recorded"))
        if schema != "mnps_tensor_spec_v2_4":
            raise CandidateContractError(f"unexpected source schema: {schema!r}")
        train_support = _support_intervals(time, starts, ends, train)
        evaluation_support = _support_intervals(time, starts, ends, evaluation)
        metadata: dict[str, Any] = {
            "recording": str(source["recording"]),
            "source_h5": str(path),
            "source_h5_sha256_before": before,
            "source_schema": schema,
            "n_epochs": n,
            "epoch_id_hash": sha256_bytes(np.ascontiguousarray(epoch_id).tobytes()),
            "time_hash": sha256_bytes(np.ascontiguousarray(time.astype(np.float64)).tobytes()),
            "dt_sec": float(dt[0]),
            "unique_dt_sec": np.unique(dt).tolist(),
            "epoch_support": {
                "start_path": "window_start",
                "end_path": "window_end",
                "semantics": "validated recorded epoch window support for source/destination endpoints",
                "full_signal_support_status": "unknown",
            },
            "coordinate_fit_population": {
                "normalize_mode": _scalar(handle.attrs.get("normalize_mode", "not_recorded")),
                "source_metadata_status": "whole_record robust-z provenance is recorded; exact feature-specific coordinate fit population is carried below",
            },
            "coordinate_provenance": {},
            "source_status": {
                "geometry_contract_status": "not_recorded",
                "geometry_time_grid_status": "not_recorded",
            },
            "signal_support_provenance": _signal_support_provenance(handle),
            "support_signature": _support_signature(handle),
        }
        arrays: dict[str, np.ndarray] = {"time": time, "epoch_id": epoch_id, "train_support": train_support, "evaluation_support": evaluation_support}
        for name, expected in EXPECTED_COORDINATES.items():
            values = np.asarray(handle[expected["h5_path"]], dtype=float)
            if values.shape != (n, expected["dimension"]):
                raise CandidateContractError(f"{name} has unexpected shape {values.shape}")
            if not np.isfinite(values).all():
                raise CandidateContractError(f"{name} contains nonfinite values; no imputation is permitted")
            raw_names = np.asarray(handle["coords_9d/names"] if name == "coords_9d" else handle.attrs.get("mnps_axis_names", []))
            axis_names = [str(_scalar(value)) for value in raw_names.reshape(-1)]
            if axis_names != expected["axis_names"]:
                raise CandidateContractError(f"{name} axis names do not match frozen canonical order")
            arrays[name] = values
            metadata["coordinate_provenance"][name] = _attribute_provenance(handle, name, expected["h5_path"], axis_names)
        source_status = metadata["source_status"]
        source_status["geometry_contract_status"] = _scalar(handle["provenance/geometry_contract/status"][()]) if "provenance/geometry_contract/status" in handle else "not_recorded"
        source_status["geometry_time_grid_status"] = _scalar(handle["provenance/geometry_contract/time_grid/status"][()]) if "provenance/geometry_contract/time_grid/status" in handle else "not_recorded"
        invalid_9d_path = "provenance/geometry_contract/jacobian_9d/invalid_windows"
        source_status["jacobian_9d_invalid_windows"] = int(handle[invalid_9d_path][()]) if invalid_9d_path in handle else None
        fit_population = metadata["signal_support_provenance"]
        metadata["coordinate_fit_population"].update({
            "reference_fit_population_status": fit_population.get("reference_fit_population_status"),
            "reference_fit_population_counts": fit_population.get("reference_fit_population_counts", []),
            "reference_fit_population_hashes": fit_population.get("reference_fit_population_hashes", []),
            "reference_fit_scopes": fit_population.get("reference_fit_scopes", []),
        })
    after = sha256_file(path)
    if after != before:
        raise CandidateContractError(f"source H5 changed during read-only candidate run: {path}")
    metadata["source_h5_sha256_after"] = after
    metadata["input_unchanged"] = True
    return metadata, arrays, before, after


def _evaluation_rows(result: drift.DriftCandidateResult, arrays: dict[str, np.ndarray]) -> list[dict[str, Any]]:
    indices = result.evaluation_increment_indices
    x = arrays["trajectory"]
    time = arrays["time"]
    epoch_id = arrays["epoch_id"]
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        increments = x[indices + 1] - x[indices]
        velocities = increments / np.diff(time)[indices, None]
    if not np.isfinite(increments).all() or not np.isfinite(velocities).all():
        raise CandidateContractError("held-out increment diagnostics are nonfinite")
    rows = []
    for row, index in enumerate(indices):
        rows.append({
            "increment_index": int(index),
            "source_epoch_id": int(epoch_id[index]),
            "destination_epoch_id": int(epoch_id[index + 1]),
            "source_time_sec": float(time[index]),
            "destination_time_sec": float(time[index + 1]),
            "dt_sec": float(time[index + 1] - time[index]),
            "b_hat": result.b_hat[row].tolist(),
            "heldout_increment": increments[row].tolist(),
            "heldout_increment_velocity": velocities[row].tolist(),
        })
    return rows


def _run_one(source_metadata: dict[str, Any], arrays: dict[str, np.ndarray], coordinate: str, estimator: str, spec: dict[str, Any], source_hash: str, code_hashes: dict[str, str]) -> dict[str, Any]:
    split = spec["split"]
    train = np.arange(*split["train_increment_range"], dtype=np.int64)
    evaluation = np.arange(*split["evaluation_increment_range"], dtype=np.int64)
    x = arrays[coordinate]
    arrays_for_result = {**arrays, "trajectory": x}
    support_audit = _support_audit(arrays["train_support"], arrays["evaluation_support"], float(split["embargo_sec"]))
    row: dict[str, Any] = {
        "recording": source_metadata["recording"],
        "coordinate": coordinate,
        "coordinate_dataset_path": EXPECTED_COORDINATES[coordinate]["h5_path"],
        "estimator": estimator,
        "candidate_status": "candidate_not_qualified",
        "claim_status": "no_biological_claim",
        "qualification_status": "not_assessed",
        "stage_contrast": "not_run",
        "source_h5_sha256": source_hash,
        "code_provenance": code_hashes,
        "coordinate_provenance": source_metadata["coordinate_provenance"][coordinate],
        "support_audit": support_audit,
        "train_window_support": arrays["train_support"].tolist(),
        "evaluation_window_support": arrays["evaluation_support"].tolist(),
        "train_window_support_hash": sha256_bytes(np.ascontiguousarray(arrays["train_support"].astype(np.float64)).tobytes()),
        "evaluation_window_support_hash": sha256_bytes(np.ascontiguousarray(arrays["evaluation_support"].astype(np.float64)).tobytes()),
        "train_increment_indices": train.tolist(),
        "evaluation_increment_indices": evaluation.tolist(),
        "train_increment_indices_hash": sha256_bytes(np.ascontiguousarray(train).tobytes()),
        "evaluation_increment_indices_hash": sha256_bytes(np.ascontiguousarray(evaluation).tobytes()),
        "endpoint_overlap": np.intersect1d(
            np.unique(np.concatenate((train, train + 1))),
            np.unique(np.concatenate((evaluation, evaluation + 1))),
        ).tolist(),
        "increment_overlap": [],
        "dt_sec": source_metadata["dt_sec"],
        "epoch_support_status": "recorded_epoch_windows_only",
        "full_signal_support_status": source_metadata["signal_support_provenance"].get("temporal_support_status", "unknown"),
        "coordinate_fit_population_status": "known_whole_recording_reference_fit; not held-out",
        "coordinate_fit_population": source_metadata["coordinate_fit_population"],
        "signal_support_provenance": source_metadata["signal_support_provenance"],
        "support_signature": source_metadata["support_signature"],
    }
    if source_metadata["source_status"].get("geometry_contract_status") != "ok":
        row.update(
            status="refused",
            refusal_class="source_contract",
            refusal_reason=(
                "accepted M3 reference requires provenance/geometry_contract/status='ok'; "
                f"source reports {source_metadata['source_status'].get('geometry_contract_status')!r}"
            ),
            predictions=None,
            heldout_rows=None,
            n_predictions=0,
            predictions_finite=None,
        )
        return row
    try:
        result = drift.crossfit_local_chart_b(
            x,
            arrays["time"],
            train,
            evaluation,
            estimator=estimator,
            n_neighbors=int(split["n_neighbors"]),
            min_train_support=int(split["min_train_support"]),
            embargo=float(split["embargo_sec"]),
            train_window_support=arrays["train_support"],
            evaluation_window_support=arrays["evaluation_support"],
            source_artifact_hash=source_hash,
            source_nmd_schema=source_metadata["source_schema"],
            nmd_code_revision=None,
        )
    except drift.DriftContractError as exc:
        row.update(
            status="refused",
            refusal_class="estimator_contract",
            refusal_reason=str(exc),
            predictions=None,
            heldout_rows=None,
            n_predictions=0,
            predictions_finite=None,
        )
        return row
    row.update(
        status="computed_candidate",
        refusal_reason=None,
        increment_overlap=result.provenance["train_evaluation_overlap"],
        estimator_provenance=dict(result.provenance),
        predictions=result.b_hat.tolist(),
        heldout_rows=_evaluation_rows(result, arrays_for_result),
        n_predictions=int(len(result.b_hat)),
        predictions_finite=bool(np.isfinite(result.b_hat).all()),
    )
    return row


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(_json_safe(value), indent=2, allow_nan=False), encoding="utf-8")


def run(config_path: str | Path, output_root: str | Path) -> dict[str, Any]:
    """Run the frozen two-record pilot into a fresh output directory."""
    config_path = Path(config_path).resolve()
    output_root = Path(output_root).resolve()
    config, spec_hash, config_hash = _read_config(config_path)
    spec = deepcopy(config["spec"])
    _check_frozen_spec(spec)
    if output_root.exists():
        if any(output_root.iterdir()):
            raise FileExistsError(f"candidate output must be fresh and empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    runner_hash = sha256_file(Path(__file__).resolve())
    drift_hash = sha256_file(Path(drift.__file__).resolve())
    code_hashes = {"runner_sha256": runner_hash, "drift_sha256": drift_hash, "config_sha256": config_hash}
    report: dict[str, Any] = {
        "schema": "ndt.sleep.sleep_drift_candidate_result.v1",
        "status": "candidate_not_qualified",
        "claim_status": "no_biological_claim",
        "scientific_qualification": "not_assessed",
        "stage_contrast": "not_run",
        "question": "Can the frozen analysis-owned cross-fit chart-velocity candidate be evaluated on held-out increments under an explicit chart and epoch-support contract?",
        "scope": "bounded two-recording engineering candidate pilot; no tuning, stage contrast, qualification, or Ito drift claim",
        "frozen_spec_sha256": spec_hash,
        "config_sha256_before": config_hash,
        "config_path": str(config_path),
        "code_provenance": code_hashes,
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "h5py": h5py.__version__,
            "nmd_analysis": importlib.metadata.version("nmd-analysis") if importlib.metadata.packages_distributions().get("nmd_analysis") else "source_checkout",
        },
        "spec": spec,
        "sources": [],
        "rows": [],
        "limitations": {
            "full_upstream_signal_support": "source export records temporal_support_status=unknown and effective feature/filter support is not certified by epoch bounds",
            "global_coordinate_fit_population": "source export records whole-record robust-z fit populations; these include evaluation rows and are not held-out",
            "coordinate_comparison_to_e1_e2": "mnps_3d and coords_9d/values are explicit candidate paths; E1/E2 subject_anchored family layers are not asserted identical",
            "candidate_interpretation": "computed diagnostics only; no empirical drift, Ito drift, C1 qualification, biological interpretation, or sleep-stage contrast",
            "missingness": "nonfinite coordinates/support are refused; no imputation or zero substitution",
        },
    }
    for source in spec["sources"]:
        source_metadata, arrays, before, after = _read_source(source, spec)
        report["sources"].append(source_metadata)
        for coordinate in ("mnps_3d", "coords_9d"):
            for estimator in spec["split"]["estimators"]:
                report["rows"].append(_run_one(source_metadata, arrays, coordinate, estimator, spec, before, code_hashes))
    config_after = sha256_file(config_path)
    if config_after != config_hash:
        raise CandidateContractError("config changed during candidate run")
    report["config_sha256_after"] = config_after
    _write_json(output_root / "candidate_report.json", report)
    _write_json(output_root / "candidate_predictions.json", {
        "schema": "ndt.sleep.sleep_drift_candidate_predictions.v1",
        "frozen_spec_sha256": spec_hash,
        "rows": [
            {
                "recording": row["recording"],
                "coordinate": row["coordinate"],
                "estimator": row["estimator"],
                "status": row["status"],
                "predictions": row.get("predictions"),
                "heldout_rows": row.get("heldout_rows"),
            }
            for row in report["rows"]
        ],
    })
    output_hashes = {path.name: sha256_file(path) for path in sorted(output_root.iterdir()) if path.is_file()}
    _write_json(output_root / "output_hashes.json", output_hashes)
    return report


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.config, args.output_root)
    print(json.dumps({"output_root": str(args.output_root.resolve()), "status": report["status"], "rows": len(report["rows"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
