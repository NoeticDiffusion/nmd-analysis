"""Bounded E1/E2 summaries for the frozen sleep new-family analysis plan.

This runner only reads existing HDF5 family surfaces through the installed
``nmd_analysis`` readers.  Jacobian labels are attached through the producer's
explicit ``centers`` positions; diffusion labels are checked against the
canonical query row identifiers.  No rows are joined across gaps and no
family estimator is refit by stage.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import inspect
import json
import platform
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import h5py
import numpy as np

from nmd_analysis.dynamical_families.adapters import diffusion_window_rows
from nmd_analysis.dynamical_families.readers import read_family
from nmd_analysis.local_dynamics.adapters import jacobian_metrics_window_rows


KNOWN_STAGES: tuple[tuple[int, str], ...] = (
    (0, "Wake"),
    (1, "N1"),
    (2, "N2"),
    (3, "N3"),
    (4, "REM"),
)
E1_METRICS = ("spectral_abscissa", "numerical_abscissa", "reactivity_gap")
E2_METRICS = ("D_total", "d_diff", "c_diff")
STAGE_KEYS = tuple(label for _, label in KNOWN_STAGES) + ("Code8", "Unknown")
EXPECTED_ENDPOINTS: tuple[tuple[str, int, str], ...] = tuple(
    [("local_jacobian", dimension, metric) for dimension in (3, 9) for metric in E1_METRICS]
    + [("diffusion_geometry", 3, metric) for metric in E2_METRICS]
)
PLAN_SCHEMA = "ndt.sleep.new_family_analysis_plan.v1"
RUN_SCHEMA = "ndt.sleep.new_family_analysis.v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_value(value: Any) -> Any:
    """Convert numpy/HDF5 values and non-finite floats to strict JSON values."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        return bytes(value).decode("utf-8")
    if isinstance(value, np.generic):
        return _json_value(value.item())
    if isinstance(value, np.ndarray):
        return [_json_value(item) for item in value.tolist()]
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    return str(value)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(_json_value(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _finite_scalar(value: Any) -> bool:
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError):
        return False
    return array.ndim == 0 and bool(np.isfinite(array).all())


def _finite_any(value: Any) -> bool:
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError):
        return False
    return bool(array.size and np.isfinite(array).all())


def _number(value: Any) -> float | None:
    return float(value) if _finite_scalar(value) else None


def _integer(value: Any, *, field: str) -> int:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{field} must be an integer position, not boolean")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} is not an integer position: {value!r}") from exc
    if not np.isfinite(number) or not number.is_integer():
        raise ValueError(f"{field} is not an integer position: {value!r}")
    return int(number)


def _stage_info(value: Any) -> dict[str, Any]:
    """Return a stable stage group while keeping code 8 separate."""
    raw = _json_value(value)
    try:
        code = _integer(value, field="stage_code")
    except ValueError:
        return {"stage_code": None, "stage_label": "Unknown", "stage_label_status": "unknown", "stage_code_raw": raw, "stage_key": "Unknown"}
    for known_code, label in KNOWN_STAGES:
        if code == known_code:
            return {"stage_code": code, "stage_label": label, "stage_label_status": "recorded", "stage_code_raw": raw, "stage_key": label}
    if code == 8:
        return {"stage_code": code, "stage_label": "Code8", "stage_label_status": "code8", "stage_code_raw": raw, "stage_key": "Code8"}
    return {"stage_code": code, "stage_label": "Unknown", "stage_label_status": "unknown", "stage_code_raw": raw, "stage_key": "Unknown"}


def read_epoch_reference(h5_path: Path) -> dict[str, Any]:
    """Read the exact epoch arrays used for label alignment.

    No epoch IDs, timestamps or labels are synthesized.  The stage array is
    the producer's canonical ``/labels/stage`` surface.
    """
    with h5py.File(h5_path, "r") as handle:
        required = ("/epoch_id", "/time", "/labels/stage")
        missing = [name for name in required if name not in handle]
        if missing:
            raise ValueError(f"missing canonical epoch reference datasets: {missing}")
        arrays = {name: np.asarray(handle[name][:]).reshape(-1) for name in required}
    lengths = {name: len(value) for name, value in arrays.items()}
    if len(set(lengths.values())) != 1:
        raise ValueError(f"epoch reference arrays are not aligned: {lengths}")
    if len(np.unique(arrays["/epoch_id"])) != len(arrays["/epoch_id"]):
        raise ValueError("canonical epoch_id array is not unique")
    if not _finite_any(arrays["/time"]):
        raise ValueError("canonical time array is not finite")
    return {
        "epoch_id": arrays["/epoch_id"],
        "time": arrays["/time"].astype(float),
        "stage": arrays["/labels/stage"],
        "n_rows": len(arrays["/epoch_id"]),
    }


def _reference_arrays(reference: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    try:
        epoch_id = np.asarray(reference["epoch_id"]).reshape(-1)
        time = np.asarray(reference["time"], dtype=float).reshape(-1)
        stage = np.asarray(reference["stage"]).reshape(-1)
    except KeyError as exc:
        raise ValueError(f"epoch reference missing {exc.args[0]}") from exc
    if not (len(epoch_id) == len(time) == len(stage)):
        raise ValueError("epoch reference arrays are not aligned")
    return epoch_id, time, stage


def map_jacobian_rows(rows: Sequence[Mapping[str, Any]], reference: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Attach exact epoch metadata to Jacobian rows using explicit centers.

    Centers are validated as unique integer positions in the canonical epoch
    arrays.  Missing, duplicated, out-of-range or fractional centers fail
    closed; an adapter fallback to ``arange`` is never accepted here.
    """
    epoch_id, time, stage = _reference_arrays(reference)
    centers: list[int] = []
    for row_index, row in enumerate(rows):
        if "center" not in row or row.get("center") is None:
            raise ValueError(f"Jacobian row {row_index} has no explicit center")
        centers.append(_integer(row["center"], field=f"center[{row_index}]"))
    if len(set(centers)) != len(centers):
        raise ValueError("Jacobian centers are not unique")
    bad = [center for center in centers if center < 0 or center >= len(epoch_id)]
    if bad:
        raise ValueError(f"Jacobian centers out of epoch range: {bad[:5]}")
    mapped: list[dict[str, Any]] = []
    previous: int | None = None
    for row, center in zip(rows, centers):
        item = dict(row)
        item.update(
            {
                "mapped_epoch_position": center,
                "epoch_id": _json_value(epoch_id[center]),
                "time": float(time[center]),
                "timestamp": float(time[center]),
                "center_gap_before": None if previous is None else center - previous,
                "center_gap_before_is_nonconsecutive": False if previous is None else center - previous != 1,
            }
        )
        item.update(_stage_info(stage[center]))
        mapped.append(item)
        previous = center
    return mapped


def validate_jacobian_source(h5_path: Path, dimension: int) -> tuple[np.ndarray, np.ndarray]:
    """Validate the explicit centers and retain per-row actual-J finiteness."""
    center_path = "/jacobian/centers" if dimension == 3 else "/jacobian_9D/centers"
    jacobian_path = "/jacobian/J_hat" if dimension == 3 else "/jacobian_9D/J_hat"
    with h5py.File(h5_path, "r") as handle:
        if center_path not in handle:
            raise ValueError(f"missing explicit Jacobian centers: {center_path}")
        raw_centers = np.asarray(handle[center_path][:])
        if raw_centers.ndim != 1:
            raise ValueError(f"Jacobian centers must be one-dimensional: {center_path}")
        centers = np.asarray([_integer(value, field=f"center[{i}]") for i, value in enumerate(raw_centers)], dtype=int)
        n_epochs = len(np.asarray(handle["/epoch_id"][:]).reshape(-1)) if "/epoch_id" in handle else 0
        if len(set(centers.tolist())) != len(centers) or np.any(centers < 0) or np.any(centers >= n_epochs):
            raise ValueError(f"Jacobian centers are invalid for {n_epochs} epoch rows")
        if jacobian_path not in handle:
            raise ValueError(f"missing serialized Jacobian surface: {jacobian_path}")
        jacobian = np.asarray(handle[jacobian_path][:])
        expected_shape = (len(centers), dimension, dimension)
        if jacobian.shape != expected_shape:
            raise ValueError(f"Jacobian shape mismatch: got {jacobian.shape}, expected {expected_shape}")
        actual_finite = np.isfinite(jacobian).all(axis=(1, 2))
    return centers, actual_finite


def map_diffusion_rows(rows: Sequence[Mapping[str, Any]], reference: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Validate canonical diffusion query identifiers and attach stage groups."""
    epoch_id, time, stage = _reference_arrays(reference)
    positions: list[int] = []
    for row_index, row in enumerate(rows):
        if row.get("window_id") is None:
            raise ValueError(f"diffusion row {row_index} has no canonical window_id")
        position = _integer(row["window_id"], field=f"window_id[{row_index}]")
        if position < 0 or position >= len(epoch_id):
            raise ValueError(f"diffusion window_id out of epoch range: {position}")
        positions.append(position)
    if len(set(positions)) != len(positions):
        raise ValueError("diffusion window_id values are not unique")
    mapped: list[dict[str, Any]] = []
    for row, position in zip(rows, positions):
        item = dict(row)
        expected_id = _json_value(epoch_id[position])
        if "epoch_id" not in row or row.get("epoch_id") is None:
            raise ValueError(f"diffusion epoch_id missing at window_id={position}")
        if "timestamp" not in row or row.get("timestamp") is None:
            raise ValueError(f"diffusion timestamp missing at window_id={position}")
        if "stage" not in row or row.get("stage") is None:
            raise ValueError(f"diffusion stage missing at window_id={position}")
        if _json_value(row.get("epoch_id")) != expected_id:
            raise ValueError(f"diffusion epoch_id mismatch at window_id={position}")
        row_time = _number(row.get("timestamp"))
        if row_time is None or not np.isclose(row_time, time[position], rtol=0, atol=1e-9):
            raise ValueError(f"diffusion timestamp mismatch at window_id={position}")
        if _json_value(row.get("stage")) != _json_value(stage[position]):
            raise ValueError(f"diffusion stage mismatch at window_id={position}")
        item.update(
            {
                "mapped_epoch_position": position,
                "epoch_id": expected_id,
                "time": float(time[position]),
                "timestamp": float(time[position]),
            }
        )
        item.update(_stage_info(stage[position]))
        mapped.append(item)
    return mapped


def _support_fields(row: Mapping[str, Any], family: str) -> dict[str, Any]:
    if family in {"diffusion", "diffusion_geometry"}:
        return {
            "support_count": _json_value(row.get("support_count")),
            "support_n": _json_value(row.get("support_n")),
            "producer_valid_flag": _json_value(row.get("valid")),
            "validity_status": _json_value(row.get("validity_status")),
            "psd_floor_applied": _json_value(row.get("psd_floor_applied")),
            "raw_min_eigenvalue": _json_value(row.get("raw_min_eigenvalue")),
            "support_status": "recorded" if row.get("support_count") is not None or row.get("support_n") is not None else "not_recorded",
        }
    fields = {key: _json_value(row.get(key)) for key in ("support_mnj_3d", "support_mnj_9d", "support_chart_3d", "support_chart_9d")}
    fields.update({"support_count": None, "support_n": None, "producer_valid_flag": None, "validity_status": None, "psd_floor_applied": None, "raw_min_eigenvalue": None, "support_status": "not_recorded"})
    return fields


def _producer_status(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize recorded producer status without inferring it from row presence."""
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get("computation_status")
        status = "not_recorded" if value in (None, "") else str(_json_value(value))
        counts[status] = counts.get(status, 0) + 1
    if not counts:
        status = "unavailable"
    elif len(counts) == 1:
        status = next(iter(counts))
    else:
        status = "mixed"
    return {"status": status, "computation_status_counts": counts}


def _endpoint_row(row: Mapping[str, Any], *, recording: str, family: str, dimension: int, metric: str) -> dict[str, Any]:
    value = row.get(metric)
    finite = _finite_scalar(value)
    actual_jacobian_finite = row.get("actual_jacobian_finite")
    producer_finite_ok = bool(row.get("finite_ok", False)) and finite
    if family == "local_jacobian" and actual_jacobian_finite is False:
        producer_finite_ok = False
    item = {
        "recording": recording,
        "recording_id": recording,
        "source_h5": _json_value(row.get("source_h5")),
        "family": family,
        "dimension": dimension,
        "metric": metric,
        "value": _number(value),
        "window_id": _json_value(row.get("window_id")),
        "center": _json_value(row.get("center")),
        "center_position": _json_value(row.get("mapped_epoch_position", row.get("center"))),
        "query_position": _json_value(row.get("mapped_epoch_position", row.get("window_id"))),
        "mapped_epoch_position": _json_value(row.get("mapped_epoch_position")),
        "center_gap_before": _json_value(row.get("center_gap_before")),
        "center_gap_before_is_nonconsecutive": _json_value(row.get("center_gap_before_is_nonconsecutive")),
        "epoch_id": _json_value(row.get("epoch_id")),
        "center_epoch_id": _json_value(row.get("epoch_id")),
        "time": _number(row.get("time", row.get("timestamp"))),
        "timestamp": _number(row.get("timestamp", row.get("time"))),
        "center_time_sec": _number(row.get("time", row.get("timestamp"))),
        "stage_code": _json_value(row.get("stage_code")),
        "stage_code_raw": _json_value(row.get("stage_code_raw")),
        "stage_label": _json_value(row.get("stage_label")),
        "stage_label_status": _json_value(row.get("stage_label_status")),
        "stage_key": _json_value(row.get("stage_key")),
        "computation_status": _json_value(row.get("computation_status", "not_recorded")),
        "measurement_validity": _json_value(row.get("measurement_validity", "not_recorded")),
        "claim_status": _json_value(row.get("claim_status", "not_recorded")),
        "finite": finite,
        "producer_finite_ok": producer_finite_ok,
        "actual_jacobian_finite": _json_value(actual_jacobian_finite),
        "used": producer_finite_ok,
        "coordinate_layer": _json_value(row.get("coordinate_layer", row.get("primary_coordinate_layer", "not_recorded"))),
        "coordinate_contract": _json_value(row.get("coordinate_contract", row.get("primary_coordinate_contract", "not_recorded"))),
        "source_dataset_path": _json_value(row.get("source_dataset_path")),
        "grain_native": _json_value(row.get("grain_native", row.get("grain", "not_recorded"))),
        "grain_parent": _json_value(row.get("grain_parent", "not_recorded")),
        "qualification_status": "not_evaluated",
        "qualification_valid": None,
    }
    item.update(_support_fields(row, family))
    return item


def endpoint_rows_for_recording(h5_path: Path, recording: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read and map the six frozen endpoints for one recording."""
    reference = read_epoch_reference(h5_path)
    output: list[dict[str, Any]] = []
    availability: dict[str, Any] = {}
    for dimension in (3, 9):
        raw = jacobian_metrics_window_rows(h5_path, dimension=dimension)
        key = f"E1_{dimension}D"
        availability[key] = {"available": bool(raw), "stored_rows": len(raw), **_producer_status(raw)}
        if raw:
            expected_centers, actual_jacobian_finite = validate_jacobian_source(h5_path, dimension)
            if len(raw) != len(expected_centers):
                raise ValueError(f"Jacobian reader row count differs from explicit centers for {dimension}D")
            if any(_integer(row.get("center"), field="reader center") != int(center) for row, center in zip(raw, expected_centers)):
                raise ValueError(f"Jacobian reader did not preserve explicit centers for {dimension}D")
            mapped = map_jacobian_rows(raw, reference)
            for row, finite in zip(mapped, actual_jacobian_finite):
                row["actual_jacobian_finite"] = bool(finite)
            for metric in E1_METRICS:
                availability[key][metric] = {"available": any(metric in row for row in mapped)}
                output.extend(_endpoint_row(row, recording=recording, family="local_jacobian", dimension=dimension, metric=metric) for row in mapped)
    raw_diffusion = diffusion_window_rows(h5_path)
    availability["E2_3D"] = {"available": bool(raw_diffusion), "stored_rows": len(raw_diffusion), **_producer_status(raw_diffusion)}
    if raw_diffusion:
        mapped_diffusion = map_diffusion_rows(raw_diffusion, reference)
        for metric in E2_METRICS:
            availability["E2_3D"][metric] = {"available": any(metric in row for row in mapped_diffusion)}
            output.extend(_endpoint_row(row, recording=recording, family="diffusion_geometry", dimension=3, metric=metric) for row in mapped_diffusion)
    return output, {"epoch_rows": reference["n_rows"], "availability": availability}


def _groups(rows: Sequence[Mapping[str, Any]]) -> Iterable[tuple[str, list[Mapping[str, Any]]]]:
    for key in STAGE_KEYS:
        yield key, [row for row in rows if row.get("stage_key") == key]


def _denominators(group: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    finite_rows = [row for row in group if bool(row.get("finite"))]
    producer_rows = [row for row in group if bool(row.get("producer_finite_ok"))]
    support_known = [row for row in group if row.get("support_count") is not None or row.get("support_n") is not None]
    support_valid = [row for row in support_known if row.get("producer_valid_flag") in (1, True)]
    used_rows = [row for row in group if bool(row.get("used"))]
    return {
        "stored_rows": len(group),
        "mapped_rows": len(group),
        "finite_rows": len(finite_rows),
        "producer_finite_valid_rows": len(producer_rows),
        "producer_support_rows": len(support_valid) if support_known else None,
        "support_known_rows": len(support_known),
        "used_rows": len(used_rows),
        "qualification_rows": None,
        "qualification_evaluated": False,
    }


def _stats(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "median": None, "q25": None, "q75": None}
    array = np.asarray(values, dtype=float)
    return {"n": len(array), "median": float(np.median(array)), "q25": float(np.quantile(array, 0.25)), "q75": float(np.quantile(array, 0.75))}


def summarize_endpoint_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Summarize one endpoint's row-level data by known and unknown stages."""
    if not rows:
        return []
    first = rows[0]
    summaries: list[dict[str, Any]] = []
    for stage_key, group in _groups(rows):
        used = [float(row["value"]) for row in group if bool(row.get("used")) and _finite_scalar(row.get("value"))]
        denominator = _denominators(group)
        stage_code = next((code for code, label in KNOWN_STAGES if label == stage_key), 8 if stage_key == "Code8" else None)
        stage_status = "recorded" if stage_key in {label for _, label in KNOWN_STAGES} else ("code8" if stage_key == "Code8" else "unknown")
        item = {
            "recording": first.get("recording"),
            "family": first.get("family"),
            "dimension": first.get("dimension"),
            "metric": first.get("metric"),
            "stage_key": stage_key,
            "stage_code": stage_code,
            "stage_label": stage_key,
            "stage_label_status": stage_status,
            **_stats(used),
            **denominator,
            "denominators": denominator,
        }
        summaries.append(item)
    return summaries


def _empty_endpoint_summaries(recording: str, family: str, dimension: int, metric: str) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for stage_key in STAGE_KEYS:
        stage_code = next((code for code, label in KNOWN_STAGES if label == stage_key), 8 if stage_key == "Code8" else None)
        stage_status = "recorded" if stage_key in {label for _, label in KNOWN_STAGES} else ("code8" if stage_key == "Code8" else "unknown")
        denominator = _denominators([])
        summaries.append({
            "recording": recording, "family": family, "dimension": dimension, "metric": metric,
            "stage_key": stage_key, "stage_code": stage_code, "stage_label": stage_key,
            "stage_label_status": stage_status, **_stats([]), **denominator,
            "denominators": denominator,
        })
    return summaries


def summarize_all(rows: Sequence[Mapping[str, Any]], recordings: Sequence[str] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    keys = []
    for row in rows:
        key = (row.get("recording"), row.get("family"), row.get("dimension"), row.get("metric"))
        if key not in keys:
            keys.append(key)
    for recording in recordings or ():
        for family, dimension, metric in EXPECTED_ENDPOINTS:
            key = (recording, family, dimension, metric)
            if key not in keys:
                keys.append(key)
    summaries: list[dict[str, Any]] = []
    contrasts: list[dict[str, Any]] = []
    for recording, family, dimension, metric in keys:
        endpoint = [row for row in rows if (row.get("recording"), row.get("family"), row.get("dimension"), row.get("metric")) == (recording, family, dimension, metric)]
        if endpoint:
            summaries.extend(summarize_endpoint_rows(endpoint))
        else:
            summaries.extend(_empty_endpoint_summaries(recording, family, dimension, metric))
        by_stage = {key: [row for row in endpoint if row.get("stage_key") == key and bool(row.get("used")) and _finite_scalar(row.get("value"))] for key in ("Wake", "N2")}
        wake = [float(row["value"]) for row in by_stage["Wake"]]
        n2 = [float(row["value"]) for row in by_stage["N2"]]
        delta = float(np.median(n2) - np.median(wake)) if wake and n2 else None
        contrasts.append({
            "recording": recording, "family": family, "dimension": dimension, "metric": metric,
            "contrast": "N2_minus_Wake", "wake_n": len(wake), "n2_n": len(n2),
            "wake_median": float(np.median(wake)) if wake else None,
            "n2_median": float(np.median(n2)) if n2 else None,
            "n2_minus_wake_median": delta,
            "direction": None if delta is None else (1 if delta > 0 else -1 if delta < 0 else 0),
            "qualification_status": "not_evaluated", "qualification_valid": None,
        })
    return summaries, contrasts


def _reader_provenance() -> dict[str, Any]:
    functions = (read_family, diffusion_window_rows, jacobian_metrics_window_rows)
    paths: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for function in functions:
        source = Path(inspect.getsourcefile(function) or "").resolve()
        paths[function.__name__] = str(source)
        hashes[str(source)] = sha256(source)
    return {"reader_source_paths": paths, "reader_sha256": hashes}


def _load_inventory(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _expected_hashes(plan: Mapping[str, Any] | None, inventory: Mapping[str, Any] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    if inventory:
        for item in inventory.get("inputs", []):
            if item.get("h5") and item.get("h5_sha256_before"):
                result[str(Path(item["h5"]).resolve()).lower()] = str(item["h5_sha256_before"]).lower()
    if not result and plan:
        for value in plan.get("source_h5_sha256", []):
            result[str(value).lower()] = str(value).lower()
    return result


def _write_wide_tables(output: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    """Write stable wide tables for figure consumers while retaining long rows."""
    base_fields = [
        "recording_id", "source_h5", "dimension", "window_id", "center_position", "query_position",
        "center_epoch_id", "epoch_id", "center_time_sec", "timestamp", "stage_code", "stage_label",
        "stage_label_status", "computation_status", "measurement_validity", "claim_status",
        "support_count", "support_n", "producer_valid_flag", "psd_floor_applied", "raw_min_eigenvalue",
        "coordinate_layer", "coordinate_contract",
    ]
    for family, metrics, filename in (
        ("local_jacobian", E1_METRICS, "jacobian_rows.csv"),
        ("diffusion_geometry", E2_METRICS, "diffusion_rows.csv"),
    ):
        selected = [row for row in rows if row.get("family") == family]
        grouped: dict[tuple[Any, ...], dict[str, Any]] = {}
        for row in selected:
            key = (row.get("recording_id"), row.get("dimension"), row.get("window_id"), row.get("mapped_epoch_position"), row.get("epoch_id"))
            target = grouped.setdefault(key, {field: _json_value(row.get(field)) for field in base_fields})
            metric = str(row.get("metric"))
            target[metric] = _json_value(row.get("value"))
            target[f"finite_{metric}"] = _json_value(row.get("finite"))
            target[f"producer_finite_ok_{metric}"] = _json_value(row.get("producer_finite_ok"))
            target[f"used_{metric}"] = _json_value(row.get("used"))
        fields = base_fields + [metric for metric in metrics] + [flag for metric in metrics for flag in (f"finite_{metric}", f"producer_finite_ok_{metric}", f"used_{metric}")]
        with (output / filename).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for target in grouped.values():
                writer.writerow({field: target.get(field) for field in fields})


def run(h5_paths: Sequence[Path], output: Path, *, plan_path: Path | None = None, inventory_path: Path | None = None) -> dict[str, Any]:
    """Execute the bounded two-recording E1/E2 report into a fresh directory."""
    h5_paths = [Path(path).resolve() for path in h5_paths]
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    if not h5_paths:
        raise ValueError("at least one H5 input is required")
    if len({str(path).lower() for path in h5_paths}) != len(h5_paths):
        raise ValueError("duplicate H5 inputs are not allowed")
    plan = json.loads(plan_path.read_text(encoding="utf-8")) if plan_path else None
    if plan is not None:
        if plan.get("schema") != PLAN_SCHEMA:
            raise ValueError(f"unsupported analysis plan schema: {plan.get('schema')!r}")
        if tuple(plan.get("E1", {}).get("dimensions", ())) != (3, 9) or tuple(plan.get("E1", {}).get("primary_metrics", ())) != ("spectral_abscissa", "numerical_abscissa") or tuple(plan.get("E1", {}).get("derived_metric", ())) != ("reactivity_gap",):
            raise ValueError("analysis plan E1 scope does not match frozen runner")
        if plan.get("E2", {}).get("dimension") != 3 or tuple(plan.get("E2", {}).get("metrics", ())) != E2_METRICS:
            raise ValueError("analysis plan E2 scope does not match frozen runner")
    inventory = _load_inventory(inventory_path)
    expected = _expected_hashes(plan, inventory)
    output.mkdir(parents=True, exist_ok=False)
    source_records: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for h5_path in h5_paths:
        before = sha256(h5_path)
        expected_hash = expected.get(str(h5_path).lower())
        if expected_hash is not None and before.lower() != expected_hash.lower():
            raise ValueError(f"H5 hash mismatch against frozen inventory: {h5_path}")
        if expected_hash is None and expected and before.lower() not in set(expected.values()):
            raise ValueError(f"H5 hash is not in the frozen inventory: {h5_path}")
        recording = h5_path.parent.name or h5_path.stem
        rows, metadata = endpoint_rows_for_recording(h5_path, recording)
        after = sha256(h5_path)
        if before != after:
            raise RuntimeError(f"source H5 changed during analysis: {h5_path}")
        source_records.append({"recording": recording, "h5": str(h5_path), "h5_sha256_before": before, "h5_sha256_after": after, "input_unchanged": True, "expected_h5_sha256": expected_hash, **metadata})
        all_rows.extend(rows)
    all_summaries, all_contrasts = summarize_all(all_rows, recordings=[item["recording"] for item in source_records])
    manifest = {
        "schema": RUN_SCHEMA,
        "status": "bounded_descriptive_development_pilot",
        "claim_status": "no_biological_claim",
        "scope": "E1 local-Jacobian alpha/omega/reactivity-gap and E2 3D diffusion D_total/d_diff/c_diff; existing surfaces only",
        "h5_inputs": source_records,
        "plan": {"path": str(plan_path.resolve()), "sha256": sha256(plan_path.resolve())} if plan_path else None,
        "inventory": {"path": str(inventory_path.resolve()), "sha256": sha256(inventory_path.resolve())} if inventory_path else None,
        "analysis_code": str(Path(__file__).resolve()),
        "analysis_code_sha256": sha256(Path(__file__).resolve()),
        "reader_provenance": _reader_provenance(),
        "python": sys.version,
        "platform": platform.platform(),
        "package_versions": {name: importlib.metadata.version(name) for name in ("numpy", "h5py")},
        "mapping_policy": {"jacobian_centers": "explicit_integer_epoch_array_positions", "diffusion_queries": "canonical_window_id_epoch_id_time_stage_checked", "gap_policy": "retain_nonconsecutive_center_gaps; no joining", "stage_purity_status": "not_assessed"},
        "qualification": {"evaluated": False, "counts": None, "unknown_values": "null"},
        "outputs": ["endpoint_rows.json", "endpoint_rows.csv", "jacobian_rows.csv", "diffusion_rows.csv", "endpoint_summaries.json", "n2_minus_wake_contrasts.json", "analysis_manifest.json"],
    }
    _write_json(output / "endpoint_rows.json", all_rows)
    _write_json(output / "endpoint_summaries.json", all_summaries)
    _write_json(output / "n2_minus_wake_contrasts.json", all_contrasts)
    _write_wide_tables(output, all_rows)
    csv_rows = [{key: _json_value(row.get(key)) for key in ("recording", "family", "dimension", "metric", "value", "stage_key", "stage_code", "stage_label", "mapped_epoch_position", "epoch_id", "time", "center", "center_gap_before", "center_gap_before_is_nonconsecutive", "finite", "producer_finite_ok", "used", "support_count", "support_n", "producer_valid_flag", "psd_floor_applied", "raw_min_eigenvalue", "measurement_validity", "qualification_valid")} for row in all_rows]
    with (output / "endpoint_rows.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]) if csv_rows else ["recording", "family", "dimension", "metric", "value"])
        writer.writeheader()
        writer.writerows(csv_rows)
    _write_json(output / "analysis_manifest.json", manifest)
    return manifest


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--h5", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--inventory", type=Path)
    args = parser.parse_args(argv)
    manifest = run(args.h5, args.output, plan_path=args.plan, inventory_path=args.inventory)
    print(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
