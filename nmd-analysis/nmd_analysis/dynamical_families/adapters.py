"""Row adapters for NMD v3 family HDF5 exports."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import json
import h5py
import numpy as np

from .readers import family_availability, read_family, read_identity
from .schemas import (
    AMPLIFICATION_IDENTITIES,
    AMPLIFICATION_PRIMARY,
    ONE_STEP_IDENTITIES,
    TRANSITION_INDEX_FIELDS,
    h5_family_name,
    with_table_identity,
)
from .validity import family_validity, status


def _json(value: Any) -> str:
    def convert(item: Any) -> Any:
        if isinstance(item, np.ndarray):
            return item.tolist()
        if isinstance(item, np.generic):
            return item.item()
        raise TypeError(f"Unsupported provenance value: {type(item).__name__}")

    return json.dumps(value if value is not None else "not_recorded", default=convert, sort_keys=True)


def _cell(value: Any) -> Any:
    if isinstance(value, dict):
        return None
    if isinstance(value, (bytes, np.bytes_)):
        return value.decode("utf-8")
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return _cell(value.item())
        return value.reshape(-1).tolist()
    if isinstance(value, np.generic):
        return _cell(value.item())
    return value


def _summary_fields(summary: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in summary.items():
        if isinstance(value, dict):
            continue
        if isinstance(value, np.ndarray) and value.ndim > 0:
            out[f"{key}_json"] = _json(value)
            continue
        cell = _cell(value)
        if cell is not None:
            out[key] = cell
    return out


def _base(payload: dict[str, Any], family: str, grain: str, path: Path) -> dict[str, Any]:
    skip = {"series", "summary", "provenance", "support_signature", "grain", "amplitude_curve"}
    row: dict[str, Any] = {}
    for key, value in payload.items():
        if key in skip or isinstance(value, dict):
            continue
        if isinstance(value, np.ndarray) and value.ndim > 0:
            continue
        cell = _cell(value)
        if cell is not None:
            row[key] = cell
    row["source_h5"] = str(path)
    provenance = payload.get("provenance") if isinstance(payload.get("provenance"), dict) else {}
    row["family_provenance_json"] = _json(provenance)
    for key in ("validation_level", "time_semantics", "estimator"):
        row[key] = provenance.get(key, "not_recorded")
    row["coordinate_layer"] = (
        provenance.get("coordinate_layer")
        or provenance.get("primary_coordinate_layer")
        or payload.get("primary_coordinate_layer")
        or "not_recorded"
    )
    row["coordinate_contract"] = (
        provenance.get("coordinate_contract")
        or provenance.get("primary_coordinate_contract")
        or payload.get("primary_coordinate_contract")
        or "not_recorded"
    )
    row["claim_status"] = payload.get("claim_status", "not_recorded")
    row["measurement_validity"] = payload.get("measurement_validity", "not_recorded")
    row["qualification_status"] = payload.get("qualification_status", "not_recorded")
    row["certificate_json"] = _json({
        key: payload.get(key, "not_recorded")
        for key in ("computation_status", "measurement_validity", "claim_status", "qualification_status")
    })
    source_grain = payload.get("grain", {}) if isinstance(payload.get("grain"), dict) else {}
    for key in ("native", "parent", "biological_unit", "repeated_measure", "direct_between_subject_inference"):
        row[f"grain_{key}"] = source_grain.get(key, "not_recorded")
    row["grain_contract_json"] = _json(payload.get("grain") if isinstance(payload.get("grain"), dict) else {})
    row["support_signature_json"] = _json(payload.get("support_signature"))
    return with_table_identity(row, family=family, grain=grain)


def _attach_source_idx(row: dict[str, Any], series: dict[str, Any]) -> None:
    source_idx = series.get("source_idx") if isinstance(series, dict) else None
    if source_idx is None:
        return
    arr = np.asarray(source_idx)
    row["source_idx"] = arr.reshape(-1).tolist()
    row["source_idx_n"] = int(arr.size)


def family_recording_rows(h5_path: Path, family: str) -> list[dict[str, Any]]:
    payload = read_family(h5_path, family)
    row = _base(payload, family, "recording", h5_path)
    row.update(_summary_fields(payload.get("summary") or {}))
    row["computation_status"] = status(payload.get("computation_status"))
    ok, reason = family_validity(family, payload)
    row.update({"finite_ok": ok, "not_testable": not ok, "not_testable_reason": reason})
    if family == "resilience":
        row["n_curve_rows"] = payload.get("summary", {}).get("n_amplitudes_valid", 0)
    if family == "diffusion":
        series = payload.get("series") or {}
        _attach_source_idx(row, series)
        abd = np.asarray(series.get("A_bD", []), dtype=float)
        if abd.size:
            row["A_bD_finite_fraction"] = float(np.mean(np.isfinite(abd)))
        tensor = np.asarray(series.get("a_hat", []))
        if tensor.ndim == 3:
            row["n_windows"] = int(tensor.shape[0])
    return [row]


def _aligned_series(series: dict[str, Any], n: int, *, label: str) -> dict[str, np.ndarray]:
    fields: dict[str, np.ndarray] = {}
    for key, values in series.items():
        arr = np.asarray(values)
        if arr.ndim < 1:
            raise ValueError(f"{label} series {key} alignment mismatch")
        if key in TRANSITION_INDEX_FIELDS:
            continue
        if arr.shape[0] != n:
            raise ValueError(f"{label} series {key} alignment mismatch")
        fields[key] = arr
    return fields


def _load_window_context(h5_path: Path, n: int, *, computed: bool, label: str) -> dict[str, Any]:
    time = None
    stage = epoch = wstart = wend = None
    with h5py.File(h5_path, "r") as handle:
        for candidate in (
            "/time",
            f"/dynamical_families/{label}/v1/series/time",
            "/orthogonal_dynamics/diffusion_geometry/v1/series/time",
        ):
            if candidate in handle:
                time = np.asarray(handle[candidate][:]).reshape(-1)
                break
        if time is None and computed:
            raise ValueError(f"computed {label} series has no exact timestamp source")
        mapping = (
            ("/labels/stage", "stage"),
            ("/epoch_id", "epoch"),
            ("/window_start", "wstart"),
            ("/window_end", "wend"),
        )
        extras: dict[str, np.ndarray] = {}
        for name, target in mapping:
            if name not in handle:
                continue
            value = np.asarray(handle[name][:]).reshape(-1)
            if len(value) != n:
                raise ValueError(f"{name} alignment mismatch: {len(value)} vs {n} {label} windows")
            extras[target] = value
        stage = extras.get("stage")
        epoch = extras.get("epoch")
        wstart = extras.get("wstart")
        wend = extras.get("wend")
    if time is not None and len(time) != n:
        raise ValueError(f"{label} series/time alignment mismatch: {n} rows vs {len(time)} timestamps")
    if time is not None and (not np.isfinite(time).all() or np.any(np.diff(time) <= 0)):
        raise ValueError(f"{label} timestamps must be finite and strictly increasing")
    return {"time": time, "stage": stage, "epoch": epoch, "wstart": wstart, "wend": wend}


def _stamp_window_context(row: dict[str, Any], context: dict[str, Any], index: int) -> None:
    time = context.get("time")
    row["timestamp"] = float(time[index]) if time is not None and index < len(time) else None
    stage = context.get("stage")
    if stage is not None:
        item = stage[index].item()
        row["stage"] = item.decode("utf-8") if isinstance(item, bytes) else item
    if context.get("epoch") is not None:
        row["epoch_id"] = context["epoch"][index].item()
    if context.get("wstart") is not None:
        row["window_start"] = float(context["wstart"][index])
    if context.get("wend") is not None:
        row["window_end"] = float(context["wend"][index])


def diffusion_window_rows(h5_path: Path) -> list[dict[str, Any]]:
    payload = read_family(h5_path, "diffusion")
    series = payload.get("series", {})
    tensor = np.asarray(series.get("a_hat", []))
    if tensor.ndim == 0 or tensor.size == 0:
        return []
    if tensor.ndim != 3 or tensor.shape[1] != tensor.shape[2]:
        raise ValueError(
            f"malformed diffusion a_hat tensor shape {tensor.shape}; expected (window, dimension, dimension)"
        )
    n = tensor.shape[0]
    fields = _aligned_series(series, n, label="diffusion")
    context = _load_window_context(
        h5_path, n, computed=payload.get("computation_status") == "computed", label="diffusion",
    )
    valid = np.asarray(series.get("valid", []))
    if valid.shape != (n,):
        raise ValueError("diffusion valid mask missing or misaligned")
    rows = []
    for i in range(n):
        row = _base(payload, "diffusion", "window", h5_path)
        row.update({
            "window_id": i,
            "a_hat": np.asarray(tensor[i]).reshape(-1).tolist(),
            "a_hat_shape": tuple(int(x) for x in tensor[i].shape),
            "computation_status": status(payload.get("computation_status")),
        })
        _stamp_window_context(row, context, i)
        for key, values in fields.items():
            item = values[i]
            row[key] = item.item() if np.asarray(item).ndim == 0 else np.asarray(item).reshape(-1).tolist()
        row["finite_ok"] = bool(
            payload.get("computation_status") == "computed"
            and np.isfinite(tensor[i]).all()
            and valid[i] == 1
        )
        row["not_testable"] = not row["finite_ok"]
        row["not_testable_reason"] = (
            None if row["finite_ok"] else payload.get("failure_reason") or "invalid_diffusion_window"
        )
        rows.append(row)
    return rows


def identity_recording_rows(h5_path: Path, family: str, identity_path: str) -> list[dict[str, Any]]:
    payload = read_identity(h5_path, family, identity_path)
    row = _base(payload, family, "recording", h5_path)
    row.update(_summary_fields(payload.get("summary") or {}))
    row["identity_id"] = payload.get("identity_id") or identity_path.split("/")[-1]
    row["identity_path"] = payload.get("identity_path") or identity_path
    row["declared_lag"] = int(payload.get("declared_lag") or 1)
    row["computation_status"] = status(payload.get("computation_status"))
    row["qualification_status"] = payload.get("qualification_status", "not_recorded")
    computed = row["computation_status"] == "computed"
    row["finite_ok"] = computed
    row["not_testable"] = not computed
    row["not_testable_reason"] = None if computed else (
        payload.get("failure_reason") or f"{family}_{row['computation_status']}"
    )
    _attach_source_idx(row, payload.get("series") or {})
    return [row]


def identity_window_rows(
    h5_path: Path,
    family: str,
    identity_path: str,
    *,
    primary: str,
    variant_id: str | None = None,
) -> list[dict[str, Any]]:
    payload = read_identity(h5_path, family, identity_path)
    series = payload.get("series") or {}
    if primary not in series:
        return []
    primary_values = np.asarray(series[primary])
    if primary_values.ndim == 0 or primary_values.size == 0:
        return []
    n = primary_values.shape[0]
    fields = _aligned_series(series, n, label=f"{family}/{identity_path}")
    context = _load_window_context(
        h5_path,
        n,
        computed=payload.get("computation_status") == "computed",
        label=h5_family_name(family),
    )
    valid = np.asarray(series["valid"]) if "valid" in series else None
    rows = []
    for i in range(n):
        row = _base(payload, family, "window", h5_path)
        row.update({
            "window_id": i,
            "identity_id": payload.get("identity_id") or identity_path.split("/")[-1],
            "identity_path": payload.get("identity_path") or identity_path,
            "declared_lag": int(payload.get("declared_lag") or 1),
            "computation_status": status(payload.get("computation_status")),
            "qualification_status": payload.get("qualification_status", "not_recorded"),
        })
        if variant_id is not None:
            row["variant_id"] = variant_id
        _stamp_window_context(row, context, i)
        for key, values in fields.items():
            item = values[i]
            row[key] = item.item() if np.asarray(item).ndim == 0 else np.asarray(item).reshape(-1).tolist()
        finite_primary = np.isfinite(np.asarray(primary_values[i], dtype=float)).all()
        valid_ok = True if valid is None else bool(valid[i] == 1)
        row["finite_ok"] = bool(
            payload.get("computation_status") == "computed" and finite_primary and valid_ok
        )
        row["not_testable"] = not row["finite_ok"]
        row["not_testable_reason"] = (
            None if row["finite_ok"] else payload.get("failure_reason") or f"invalid_{family}_window"
        )
        rows.append(row)
    return rows


def increment_covariance_recording_rows(h5_path: Path) -> list[dict[str, Any]]:
    return identity_recording_rows(h5_path, "diffusion", "increment_covariance_level0")


def chart_drift_realized_velocity_window_rows(h5_path: Path) -> list[dict[str, Any]]:
    return identity_window_rows(
        h5_path, "chart_drift", "realized_velocity_level0", primary="dx_dt",
    )


def chart_drift_conditional_mean_window_rows(h5_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant, path in (
        ("pooled", "conditional_mean_rate_level1/pooled"),
        ("blocked_crossfit", "conditional_mean_rate_level1/blocked_crossfit"),
    ):
        rows.extend(identity_window_rows(
            h5_path, "chart_drift", path, primary="b_hat", variant_id=variant,
        ))
    return rows


def chart_drift_lag_diagnostics_window_rows(h5_path: Path) -> list[dict[str, Any]]:
    return identity_window_rows(
        h5_path, "chart_drift", "conditional_mean_rate_level1/lag_diagnostics", primary="b_hat",
    )


def one_step_recording_rows(h5_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    parent = read_family(h5_path, "one_step")
    has_lag2 = False
    if parent.get("availability"):
        with h5py.File(h5_path, "r") as handle:
            has_lag2 = "/dynamical_families/one_step/v1/declared_lag_2" in handle
    identities = list(ONE_STEP_IDENTITIES)
    for identity in identities:
        rows.extend(identity_recording_rows(h5_path, "one_step", identity))
        if has_lag2:
            rows.extend(identity_recording_rows(h5_path, "one_step", f"declared_lag_2/{identity}"))
    for row in rows:
        row["table_grain"] = "recording"
        row["grain"] = "recording"
        # Window-shaped series on this family are broadcasts, not T replicates.
        if row.get("grain_repeated_measure") not in {"false", False, "not_recorded"}:
            row["grain_repeated_measure_note"] = "one_step_series_are_broadcasts_not_replicates"
    return rows


def history_predictive_gain_recording_rows(h5_path: Path) -> list[dict[str, Any]]:
    return identity_recording_rows(h5_path, "history", "history_predictive_gain_level1")


def history_conditioned_operator_recording_rows(h5_path: Path) -> list[dict[str, Any]]:
    return identity_recording_rows(h5_path, "history", "history_conditioned_operator_level2")


def amplification_window_rows(h5_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for identity in AMPLIFICATION_IDENTITIES:
        rows.extend(identity_window_rows(
            h5_path, "amplification", identity, primary=AMPLIFICATION_PRIMARY[identity],
        ))
    return rows


def turning_window_rows(h5_path: Path) -> list[dict[str, Any]]:
    return identity_window_rows(h5_path, "turning", "turning_angle_level0", primary="turning_angle")


def family_rows(h5_path: Path, family: str, grain: str = "recording") -> list[dict[str, Any]]:
    if grain == "window" and family == "diffusion":
        return diffusion_window_rows(h5_path)
    if grain == "window" and family == "chart_drift":
        return chart_drift_conditional_mean_window_rows(h5_path)
    if grain == "window" and family == "amplification":
        return amplification_window_rows(h5_path)
    if grain == "window" and family == "turning":
        return turning_window_rows(h5_path)
    if grain == "recording" and family == "one_step":
        return one_step_recording_rows(h5_path)
    return family_recording_rows(h5_path, family)


def availability_rows(h5_path: Path) -> list[dict[str, Any]]:
    payload = read_family(h5_path, "diffusion")
    row = _base(payload, "diffusion", "recording", h5_path)
    row.pop("family_id", None)
    row["table_schema"] = "nmd_analysis.dynamical_families_availability.v1"
    for item in family_availability(h5_path):
        family = item["family_id"]
        row[f"{family}_available"] = bool(item["available"])
        row[f"{family}_namespace_origin"] = item["namespace_origin"]
    row["source_dataset_path"] = "/"
    return [row]


def collectors() -> dict[str, Any]:
    return {
        "dynamical_families_availability": availability_rows,
        "diffusion_geometry_recording": lambda path: family_recording_rows(path, "diffusion"),
        "diffusion_geometry_window": diffusion_window_rows,
        "diffusion_increment_covariance_recording": increment_covariance_recording_rows,
        "destination_recording": lambda path: family_recording_rows(path, "destination"),
        "resilience_recording": lambda path: family_recording_rows(path, "resilience"),
        "chart_drift_recording": lambda path: family_recording_rows(path, "chart_drift"),
        "chart_drift_realized_velocity_window": chart_drift_realized_velocity_window_rows,
        "chart_drift_conditional_mean_window": chart_drift_conditional_mean_window_rows,
        "chart_drift_lag_diagnostics_window": chart_drift_lag_diagnostics_window_rows,
        "one_step_recording": one_step_recording_rows,
        "history_predictive_gain_recording": history_predictive_gain_recording_rows,
        "history_conditioned_operator_recording": history_conditioned_operator_recording_rows,
        "amplification_window": amplification_window_rows,
        "turning_window": turning_window_rows,
    }


__all__ = [
    "collectors",
    "diffusion_window_rows",
    "family_recording_rows",
    "family_rows",
    "identity_recording_rows",
    "identity_window_rows",
    "one_step_recording_rows",
]
