"""HDF5-to-row adapters for versioned local-dynamics measurement surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import h5py
import numpy as np

from ..legacy_adapters import _base_h5_metadata_from_handle
from .readers import (
    availability,
    as_scalar,
    branch_name,
    group_provenance,
    iter_horizon_groups,
    jacobian_centers_path,
    jacobian_diagnostics_path,
    jacobian_metrics_path,
    local_dynamics_paths,
    inferential_grain,
    measurement_certificate,
    metric_valid_fraction,
    read_group_scalars,
    schema_status,
    semantic_field,
    scalar,
    support_signature,
)
from .schemas import with_table_identity

RowsFn = Callable[[Path], list[dict[str, Any]]]


def _text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _base(
    handle: h5py.File,
    h5_path: Path,
    *,
    dimension: int,
    grain: str,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    base = _base_h5_metadata_from_handle(handle, h5_path)
    base["participant_id"] = base.get("subject_id")
    base["source_h5"] = str(h5_path)
    contract = provenance.get("primary_coordinate_contract") or provenance.get("coordinate_contract")
    layer = provenance.get("primary_coordinate_layer") or provenance.get("coordinate_layer")
    row = with_table_identity(
        base,
        grain=grain,
        coordinate_dimension=dimension,
        coordinate_contract=contract or base.get("primary_coordinate_contract"),
        coordinate_layer=layer or base.get("primary_coordinate_layer"),
    )
    row.update({f"ld_{key}": value for key, value in provenance.items()})
    row.update(support_signature(handle))
    return row


def _contract_fields(group: h5py.Group, expected_schema: str) -> dict[str, Any]:
    out = schema_status(group, expected_schema)
    out.setdefault("failure_reason", scalar(group, "failure_reason"))
    out.update(inferential_grain(group))
    return out


def _unavailable_row(
    handle: h5py.File,
    h5_path: Path,
    *,
    dimension: int,
    grain: str,
    source_path: str,
) -> dict[str, Any]:
    row = _base(handle, h5_path, dimension=dimension, grain=grain, provenance={})
    row.update(
        {
            "source_dataset_path": source_path,
            "computation_status": "unavailable",
            "failure_reason": "capability_missing",
            "finite_ok": False,
            "not_testable": True,
            "not_testable_reason": "capability_missing",
        }
    )
    row.update({"measurement_validity": "not_recorded", "claim_status": "not_recorded", "certificate_origin": "legacy_absent"})
    row.update({f"{key}": "not_recorded" for key in ("grain_native", "grain_parent", "grain_biological_unit", "grain_repeated_measure", "grain_direct_between_subject_inference")})
    row["grain_origin"] = "legacy_absent"
    return row


def _jacobian_oos_recording_fields(handle: h5py.File, dimension: int) -> dict[str, Any]:
    """Additive holdout diagnostics; they do not replace the in-sample gate."""
    path = jacobian_diagnostics_path(dimension)
    out: dict[str, Any] = {
        "rel_mse_baseline_oos_median": "not_recorded",
        "oos_holdout_stride": "not_recorded",
    }
    if path not in handle:
        return out
    diag = handle[path]
    if "rel_mse_baseline_oos_median" in diag.attrs:
        out["rel_mse_baseline_oos_median"] = float(diag.attrs["rel_mse_baseline_oos_median"])
    elif "rel_mse_baseline_oos_median" in diag:
        out["rel_mse_baseline_oos_median"] = float(as_scalar(diag["rel_mse_baseline_oos_median"][()]))
    if "oos_holdout_stride" in diag.attrs:
        out["oos_holdout_stride"] = int(diag.attrs["oos_holdout_stride"])
    elif "oos_holdout_stride" in diag:
        out["oos_holdout_stride"] = int(as_scalar(diag["oos_holdout_stride"][()]))
    return out


def _jacobian_oos_window_arrays(handle: h5py.File, dimension: int, n_rows: int) -> dict[str, np.ndarray]:
    path = jacobian_diagnostics_path(dimension)
    if path not in handle:
        return {}
    diag = handle[path]
    arrays: dict[str, np.ndarray] = {}
    mapping = {
        "rel_mse_baseline_oos_windows": "rel_mse_baseline_oos",
        "n_holdout_samples": "n_holdout_samples",
    }
    for source, dest in mapping.items():
        if source not in diag:
            continue
        values = np.asarray(diag[source][:])
        if values.shape[0] != n_rows:
            continue
        arrays[dest] = values
    return arrays


def jacobian_metrics_recording_rows(h5_path: Path, *, dimension: int) -> list[dict[str, Any]]:
    path = jacobian_metrics_path(dimension)
    with h5py.File(h5_path, "r") as handle:
        if path not in handle:
            row = _unavailable_row(handle, h5_path, dimension=dimension, grain="recording", source_path=path)
            row.update(_jacobian_oos_recording_fields(handle, dimension))
            return [row]
        group = handle[path]
        provenance = group_provenance(group)
        row = _base(handle, h5_path, dimension=dimension, grain="recording", provenance=provenance)
        row.update(_contract_fields(group, "mndm.jacobian_metrics.v1"))
        summary = read_group_scalars(group["summary"]) if "summary" in group else {}
        row.update(summary)
        row.update(_jacobian_oos_recording_fields(handle, dimension))
        row.update(
            {
                "source_dataset_path": path,
                "computation_status": schema_status(group, "mndm.jacobian_metrics.v1")["computation_status"],
                "schema_version": scalar(group, "schema_version"),
                "jacobian_metrics_valid_fraction": metric_valid_fraction(summary),
                "finite_ok": schema_status(group, "mndm.jacobian_metrics.v1")["computation_status"] == "computed"
                and bool(int(summary.get("n_windows_metrics_valid") or 0) > 0),
                "not_testable": False,
            }
        )
        row["not_testable"] = not row["finite_ok"]
        row["not_testable_reason"] = None if row["finite_ok"] else "no_valid_jacobian_metrics"
        return [row]


def jacobian_metrics_window_rows(h5_path: Path, *, dimension: int) -> list[dict[str, Any]]:
    path = jacobian_metrics_path(dimension)
    with h5py.File(h5_path, "r") as handle:
        if path not in handle or "series" not in handle[path]:
            return []
        group = handle[path]
        series = group["series"]
        provenance = group_provenance(group)
        fields = {name: np.asarray(dataset[:]) for name, dataset in series.items() if isinstance(dataset, h5py.Dataset)}
        n_rows = max((values.shape[0] for values in fields.values()), default=0)
        fields.update(_jacobian_oos_window_arrays(handle, dimension, n_rows))
        centers = (
            np.asarray(handle[jacobian_centers_path(dimension)][:]).reshape(-1)
            if jacobian_centers_path(dimension) in handle
            else np.arange(n_rows, dtype=int)
        )
        base_row = _base(handle, h5_path, dimension=dimension, grain="window", provenance=provenance)
        contract_fields = _contract_fields(group, "mndm.jacobian_metrics.v1")
        schema_version = scalar(group, "schema_version")
        computation_status = contract_fields["computation_status"]
        rows: list[dict[str, Any]] = []
        for index in range(n_rows):
            row = dict(base_row)
            row.update(contract_fields)
            row.update(
                {
                    "source_dataset_path": f"{path}/series",
                    "window_id": int(index),
                    "center": int(centers[index]) if index < centers.size else None,
                    "schema_version": schema_version,
                    "computation_status": computation_status,
                }
            )
            for name, values in fields.items():
                if index < values.shape[0]:
                    value = values[index]
                    row[name] = value.item() if isinstance(value, np.generic) else value
            valid = row["computation_status"] == "computed" and bool(np.isfinite(float(row.get("spectral_abscissa", np.nan))))
            row["finite_ok"] = valid
            row["not_testable"] = not valid
            row["not_testable_reason"] = None if valid else "invalid_jacobian_window"
            rows.append(row)
        return rows


def finite_time_response_recording_rows(h5_path: Path, *, dimension: int) -> list[dict[str, Any]]:
    path = local_dynamics_paths(dimension)["finite_time_response"]
    with h5py.File(h5_path, "r") as handle:
        if path not in handle:
            return [_unavailable_row(handle, h5_path, dimension=dimension, grain="recording", source_path=path)]
        group = handle[path]
        row = _base(handle, h5_path, dimension=dimension, grain="recording", provenance=group_provenance(group))
        row.update(_contract_fields(group, "mndm.finite_time_response.v1"))
        row.update(read_group_scalars(group["summary"]) if "summary" in group else {})
        row.update(
            {
                "source_dataset_path": path,
                "schema_version": scalar(group, "schema_version"),
                "computation_status": schema_status(group, "mndm.finite_time_response.v1")["computation_status"],
                "validation_level": _text(scalar(group, "validation_level")),
                "n_windows": scalar(group, "n_windows"),
            }
        )
        row["finite_ok"] = row["computation_status"] == "computed" and np.isfinite(
            float(row.get("g_peak_over_horizons", np.nan))
        )
        row["not_testable"] = not row["finite_ok"]
        row["not_testable_reason"] = None if row["finite_ok"] else f"ftr_{row['computation_status']}"
        return [row]


def finite_time_response_horizon_rows(h5_path: Path, *, dimension: int) -> list[dict[str, Any]]:
    path = local_dynamics_paths(dimension)["finite_time_response"]
    with h5py.File(h5_path, "r") as handle:
        if path not in handle:
            return [_unavailable_row(handle, h5_path, dimension=dimension, grain="recording_horizon", source_path=path)]
        group = handle[path]
        provenance = group_provenance(group)
        base_row = _base(handle, h5_path, dimension=dimension, grain="recording_horizon", provenance=provenance)
        contract_fields = schema_status(group, "mndm.finite_time_response.v1")
        group_grain = inferential_grain(group)
        rows: list[dict[str, Any]] = []
        status = contract_fields["computation_status"]
        for name, horizon in iter_horizon_groups(group):
            row = dict(base_row)
            row.update(contract_fields)
            row.update(group_grain)
            row.update(read_group_scalars(horizon))
            row.update(
                {
                    "source_dataset_path": f"{path}/horizons/{name}",
                    "horizon_name": name,
                    "horizon_steps": scalar(horizon, "horizon_steps"),
                    "schema_version": scalar(group, "schema_version"),
                    "computation_status": status,
                    "validation_level": _text(scalar(group, "validation_level")),
                }
            )
            row["finite_ok"] = status == "computed" and int(row.get("n_sequences_valid") or 0) > 0
            row["not_testable"] = not row["finite_ok"]
            row["not_testable_reason"] = None if row["finite_ok"] else f"ftr_{status}"
            rows.append(row)
        return rows or [_unavailable_row(handle, h5_path, dimension=dimension, grain="recording_horizon", source_path=path)]


def finite_time_response_sequence_rows(h5_path: Path, *, dimension: int) -> list[dict[str, Any]]:
    path = local_dynamics_paths(dimension)["finite_time_response"]
    with h5py.File(h5_path, "r") as handle:
        if path not in handle:
            return []
        group = handle[path]
        provenance = group_provenance(group)
        base_row = _base(handle, h5_path, dimension=dimension, grain="sequence", provenance=provenance)
        contract_fields = _contract_fields(group, "mndm.finite_time_response.v1")
        schema_version = scalar(group, "schema_version")
        computation_status = contract_fields["computation_status"]
        rows: list[dict[str, Any]] = []
        for name, horizon in iter_horizon_groups(group):
            series = horizon.get("series")
            if not isinstance(series, h5py.Group):
                continue
            fields = {field: np.asarray(dataset[:]) for field, dataset in series.items() if isinstance(dataset, h5py.Dataset)}
            starts = np.asarray(horizon.get("start_windows", np.arange(0))[:]).reshape(-1) if "start_windows" in horizon else np.arange(max((len(x) for x in fields.values()), default=0))
            n_rows = max((len(values) for values in fields.values()), default=0)
            horizon_steps = scalar(horizon, "horizon_steps")
            for index in range(n_rows):
                row = dict(base_row)
                row.update(contract_fields)
                row.update(
                    {
                        "source_dataset_path": f"{path}/horizons/{name}/series",
                        "horizon_name": name,
                        "horizon_steps": horizon_steps,
                        "start_window_id": int(starts[index]) if index < len(starts) else int(index),
                        "sequence_id": int(index),
                        "schema_version": schema_version,
                        "computation_status": computation_status,
                    }
                )
                for field, values in fields.items():
                    if index < len(values):
                        value = values[index]
                        row[field] = value.item() if isinstance(value, np.generic) else value
                valid = row["computation_status"] == "computed" and bool(np.isfinite(float(row.get("g_max", np.nan))))
                row["finite_ok"] = valid
                row["not_testable"] = not valid
                row["not_testable_reason"] = None if valid else "invalid_ftr_sequence"
                rows.append(row)
        return rows


def transition_residual_summary_rows(h5_path: Path, *, dimension: int) -> list[dict[str, Any]]:
    path = local_dynamics_paths(dimension)["transition_residuals"]
    with h5py.File(h5_path, "r") as handle:
        if path not in handle:
            return [_unavailable_row(handle, h5_path, dimension=dimension, grain="recording", source_path=path)]
        group = handle[path]
        summary = read_group_scalars(group["summary"]) if "summary" in group else {}
        residual_mean = np.asarray(group["summary/residual_mean"][:], dtype=float) if "summary/residual_mean" in group else np.asarray([], dtype=float)
        row = _base(handle, h5_path, dimension=dimension, grain="recording", provenance=group_provenance(group))
        row.update(_contract_fields(group, "mndm.transition_residuals.v1"))
        row.update(summary)
        row.update(
            {
                "source_dataset_path": path,
                "schema_version": scalar(group, "schema_version"),
                "computation_status": schema_status(group, "mndm.transition_residuals.v1")["computation_status"],
                "transition_residual_mean_norm": float(np.linalg.norm(residual_mean)) if residual_mean.size else float("nan"),
            }
        )
        row["finite_ok"] = row["computation_status"] == "computed" and int(summary.get("n_transitions_valid") or 0) > 0
        row["not_testable"] = not row["finite_ok"]
        row["not_testable_reason"] = None if row["finite_ok"] else f"transitions_{row['computation_status']}"
        return [row]


def transition_rows(h5_path: Path, *, dimension: int) -> list[dict[str, Any]]:
    path = local_dynamics_paths(dimension)["transition_residuals"]
    with h5py.File(h5_path, "r") as handle:
        if path not in handle or "series" not in handle[path]:
            return []
        group = handle[path]
        series = group["series"]
        provenance = group_provenance(group)
        base_row = _base(handle, h5_path, dimension=dimension, grain="transition", provenance=provenance)
        contract_fields = _contract_fields(group, "mndm.transition_residuals.v1")
        schema_version = scalar(group, "schema_version")
        computation_status = contract_fields["computation_status"]
        indexed_fields = {
            name: np.asarray(series[name][()])
            for name in ("source_window_id", "target_window_id", "source_center", "target_center", "dt_sec")
            if name in series
        }
        n_rows = int(series["dt_sec"].shape[0]) if "dt_sec" in series else 0
        rows: list[dict[str, Any]] = []
        for index in range(n_rows):
            residual = np.asarray(series["transition_residual"][index], dtype=float) if "transition_residual" in series else np.asarray([], dtype=float)
            predicted = np.asarray(series["x_pred_next"][index], dtype=float) if "x_pred_next" in series else np.asarray([], dtype=float)
            row = dict(base_row)
            row.update(contract_fields)
            row.update(
                {
                    "source_dataset_path": f"{path}/series",
                    "transition_id": index,
                    "source_window_id": indexed_fields["source_window_id"][index] if "source_window_id" in indexed_fields else index,
                    "target_window_id": indexed_fields["target_window_id"][index] if "target_window_id" in indexed_fields else index + 1,
                    "source_center": indexed_fields["source_center"][index] if "source_center" in indexed_fields else None,
                    "target_center": indexed_fields["target_center"][index] if "target_center" in indexed_fields else None,
                    "dt_sec": indexed_fields["dt_sec"][index] if "dt_sec" in indexed_fields else float("nan"),
                    "transition_residual_norm": float(np.linalg.norm(residual)),
                    "schema_version": schema_version,
                    "computation_status": computation_status,
                }
            )
            for component, value in enumerate(residual):
                row[f"transition_residual_{component}"] = float(value)
            for component, value in enumerate(predicted):
                row[f"x_pred_next_{component}"] = float(value)
            row["finite_ok"] = row["computation_status"] == "computed" and bool(np.isfinite(residual).all())
            row["not_testable"] = not row["finite_ok"]
            row["not_testable_reason"] = None if row["finite_ok"] else "nonfinite_transition_residual"
            rows.append(row)
        return rows


def transition_q_proxy_rows(h5_path: Path, *, dimension: int) -> list[dict[str, Any]]:
    path = local_dynamics_paths(dimension)["transition_q_proxy"]
    with h5py.File(h5_path, "r") as handle:
        if path not in handle:
            return [_unavailable_row(handle, h5_path, dimension=dimension, grain="recording", source_path=path)]
        group = handle[path]
        covariance = np.asarray(group["covariance"][:], dtype=float) if "covariance" in group else np.asarray([], dtype=float)
        row = _base(handle, h5_path, dimension=dimension, grain="recording", provenance={})
        row.update(_contract_fields(group, "mndm.transition_residual_covariance_proxy.v1"))
        row.update(read_group_scalars(group))
        row.update(
            {
                "source_dataset_path": path,
                "schema_version": scalar(group, "schema_version"),
                "computation_status": schema_status(group, "mndm.transition_residual_covariance_proxy.v1")["computation_status"],
                "trace_Q": float(np.trace(covariance)) if covariance.ndim == 2 else float("nan"),
            }
        )
        for key in ("q_time_semantics", "q_units", "conversion_model", "q_source"):
            row[key] = semantic_field(group, key)
        if covariance.ndim == 2 and covariance.shape[0] == covariance.shape[1]:
            sign, logdet = np.linalg.slogdet(covariance)
            row["q_logdet_regularized"] = float(logdet) if sign > 0 else float("nan")
        semantics_ok = (
            row["q_time_semantics"] == "one_step_transition_covariance"
            and row["q_units"] == "state_squared"
            and row["conversion_model"] == "not_applicable"
        )
        row["finite_ok"] = (row["computation_status"] == "computed"
                            and covariance.shape == (dimension, dimension)
                            and bool(np.isfinite(covariance).all()) and semantics_ok)
        row["not_testable"] = not row["finite_ok"]
        row["not_testable_reason"] = None if row["finite_ok"] else (
            "q_contract_not_admissible" if row["computation_status"] == "computed" and not semantics_ok
            else f"q_proxy_{row['computation_status']}"
        )
        return [row]


def stochastic_reachability_rows(h5_path: Path, *, dimension: int) -> list[dict[str, Any]]:
    path = local_dynamics_paths(dimension)["stochastic_reachability"]
    with h5py.File(h5_path, "r") as handle:
        if path not in handle:
            return [_unavailable_row(handle, h5_path, dimension=dimension, grain="recording", source_path=path)]
        group = handle[path]
        row = _base(handle, h5_path, dimension=dimension, grain="recording", provenance=group_provenance(group))
        row.update(_contract_fields(group, "mndm.stochastic_reachability.v1"))
        row.update(read_group_scalars(group.get("summary", group)))
        row.update(
            {
                "source_dataset_path": path,
                "schema_version": scalar(group, "schema_version"),
                "computation_status": schema_status(group, "mndm.stochastic_reachability.v1")["computation_status"],
            }
        )
        for key in ("q_time_semantics", "q_units", "conversion_model", "q_source"):
            row[key] = semantic_field(group, key)
        semantics_ok = (
            row["q_time_semantics"] == "one_step_transition_covariance"
            and row["q_units"] == "state_squared"
            and row["conversion_model"] == "not_applicable"
        )
        row["finite_ok"] = row["computation_status"] == "computed" and semantics_ok
        row["not_testable"] = not row["finite_ok"]
        row["not_testable_reason"] = None if row["finite_ok"] else (
            "q_contract_not_admissible" if row["computation_status"] == "computed" and not semantics_ok
            else f"stochastic_reachability_{row['computation_status']}"
        )
        return [row]


def availability_rows(h5_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with h5py.File(h5_path, "r") as handle:
        for dimension in (3, 9):
            surface = availability(handle, dimension)
            row = _base(handle, h5_path, dimension=dimension, grain="recording", provenance={})
            row.update({f"{name}_available": present for name, present in surface.items()})
            for name, path in local_dynamics_paths(dimension).items():
                row[f"{name}_computation_status"] = (_text(scalar(handle, f"{path}/computation_status")) or "not_recorded") if path in handle else "unavailable"
            row.update(
                {
                    "source_dataset_path": "/",
                    "finite_ok": True,
                    "not_testable": False,
                    "availability_schema_version": "nmd_analysis.local_dynamics_availability.v1",
                }
            )
            rows.append(row)
    return rows


def collectors() -> dict[str, RowsFn]:
    out: dict[str, RowsFn] = {"local_dynamics_availability": availability_rows}
    for dimension in (3, 9):
        suffix = f"{dimension}d"
        out.update(
            {
                f"jacobian_metrics_{suffix}_recording": lambda path, dimension=dimension: jacobian_metrics_recording_rows(path, dimension=dimension),
                f"jacobian_metrics_{suffix}_window": lambda path, dimension=dimension: jacobian_metrics_window_rows(path, dimension=dimension),
                f"finite_time_response_{suffix}_recording": lambda path, dimension=dimension: finite_time_response_recording_rows(path, dimension=dimension),
                f"finite_time_response_{suffix}_recording_horizon": lambda path, dimension=dimension: finite_time_response_horizon_rows(path, dimension=dimension),
                f"finite_time_response_{suffix}_sequence": lambda path, dimension=dimension: finite_time_response_sequence_rows(path, dimension=dimension),
                f"transition_residual_summary_{suffix}_recording": lambda path, dimension=dimension: transition_residual_summary_rows(path, dimension=dimension),
                f"transition_residuals_{suffix}_transition": lambda path, dimension=dimension: transition_rows(path, dimension=dimension),
                f"transition_q_proxy_{suffix}_recording": lambda path, dimension=dimension: transition_q_proxy_rows(path, dimension=dimension),
                f"stochastic_reachability_{suffix}_recording": lambda path, dimension=dimension: stochastic_reachability_rows(path, dimension=dimension),
            }
        )
    return out
