"""HDF5-to-row adapters for versioned local-dynamics measurement surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import h5py
import numpy as np

from ..legacy_adapters import _base_h5_metadata_from_handle
from .readers import (
    availability,
    branch_name,
    group_provenance,
    iter_horizon_groups,
    jacobian_centers_path,
    jacobian_metrics_path,
    local_dynamics_paths,
    metric_valid_fraction,
    read_group_scalars,
    scalar,
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
    return row


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
    return row


def jacobian_metrics_recording_rows(h5_path: Path, *, dimension: int) -> list[dict[str, Any]]:
    path = jacobian_metrics_path(dimension)
    with h5py.File(h5_path, "r") as handle:
        if path not in handle:
            return [_unavailable_row(handle, h5_path, dimension=dimension, grain="recording", source_path=path)]
        group = handle[path]
        provenance = group_provenance(group)
        row = _base(handle, h5_path, dimension=dimension, grain="recording", provenance=provenance)
        summary = read_group_scalars(group["summary"]) if "summary" in group else {}
        row.update(summary)
        row.update(
            {
                "source_dataset_path": path,
                "computation_status": "computed",
                "schema_version": scalar(group, "schema_version"),
                "jacobian_metrics_valid_fraction": metric_valid_fraction(summary),
                "finite_ok": bool(int(summary.get("n_windows_metrics_valid") or 0) > 0),
                "not_testable": not bool(int(summary.get("n_windows_metrics_valid") or 0) > 0),
            }
        )
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
        centers = (
            np.asarray(handle[jacobian_centers_path(dimension)][:]).reshape(-1)
            if jacobian_centers_path(dimension) in handle
            else np.arange(n_rows, dtype=int)
        )
        rows: list[dict[str, Any]] = []
        for index in range(n_rows):
            row = _base(handle, h5_path, dimension=dimension, grain="window", provenance=provenance)
            row.update(
                {
                    "source_dataset_path": f"{path}/series",
                    "window_id": int(index),
                    "center": int(centers[index]) if index < centers.size else None,
                    "schema_version": scalar(group, "schema_version"),
                    "computation_status": "computed",
                }
            )
            for name, values in fields.items():
                if index < values.shape[0]:
                    value = values[index]
                    row[name] = value.item() if isinstance(value, np.generic) else value
            valid = bool(np.isfinite(float(row.get("spectral_abscissa", np.nan))))
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
        row.update(read_group_scalars(group["summary"]) if "summary" in group else {})
        row.update(
            {
                "source_dataset_path": path,
                "schema_version": scalar(group, "schema_version"),
                "computation_status": _text(scalar(group, "computation_status")) or "unavailable",
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
        rows: list[dict[str, Any]] = []
        status = _text(scalar(group, "computation_status")) or "unavailable"
        for name, horizon in iter_horizon_groups(group):
            row = _base(handle, h5_path, dimension=dimension, grain="recording_horizon", provenance=provenance)
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
        rows: list[dict[str, Any]] = []
        for name, horizon in iter_horizon_groups(group):
            series = horizon.get("series")
            if not isinstance(series, h5py.Group):
                continue
            fields = {field: np.asarray(dataset[:]) for field, dataset in series.items() if isinstance(dataset, h5py.Dataset)}
            starts = np.asarray(horizon.get("start_windows", np.arange(0))[:]).reshape(-1) if "start_windows" in horizon else np.arange(max((len(x) for x in fields.values()), default=0))
            n_rows = max((len(values) for values in fields.values()), default=0)
            for index in range(n_rows):
                row = _base(handle, h5_path, dimension=dimension, grain="sequence", provenance=provenance)
                row.update(
                    {
                        "source_dataset_path": f"{path}/horizons/{name}/series",
                        "horizon_name": name,
                        "horizon_steps": scalar(horizon, "horizon_steps"),
                        "start_window_id": int(starts[index]) if index < len(starts) else int(index),
                        "sequence_id": int(index),
                        "schema_version": scalar(group, "schema_version"),
                        "computation_status": _text(scalar(group, "computation_status")) or "unavailable",
                    }
                )
                for field, values in fields.items():
                    if index < len(values):
                        value = values[index]
                        row[field] = value.item() if isinstance(value, np.generic) else value
                valid = bool(np.isfinite(float(row.get("g_max", np.nan))))
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
        row.update(summary)
        row.update(
            {
                "source_dataset_path": path,
                "schema_version": scalar(group, "schema_version"),
                "computation_status": _text(scalar(group, "computation_status")) or "unavailable",
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
        n_rows = int(series["dt_sec"].shape[0]) if "dt_sec" in series else 0
        rows: list[dict[str, Any]] = []
        for index in range(n_rows):
            residual = np.asarray(series["transition_residual"][index], dtype=float) if "transition_residual" in series else np.asarray([], dtype=float)
            predicted = np.asarray(series["x_pred_next"][index], dtype=float) if "x_pred_next" in series else np.asarray([], dtype=float)
            row = _base(handle, h5_path, dimension=dimension, grain="transition", provenance=provenance)
            row.update(
                {
                    "source_dataset_path": f"{path}/series",
                    "transition_id": index,
                    "source_window_id": scalar(series, f"source_window_id")[index] if "source_window_id" in series else index,
                    "target_window_id": scalar(series, f"target_window_id")[index] if "target_window_id" in series else index + 1,
                    "source_center": scalar(series, f"source_center")[index] if "source_center" in series else None,
                    "target_center": scalar(series, f"target_center")[index] if "target_center" in series else None,
                    "dt_sec": scalar(series, f"dt_sec")[index] if "dt_sec" in series else float("nan"),
                    "transition_residual_norm": float(np.linalg.norm(residual)),
                    "schema_version": scalar(group, "schema_version"),
                    "computation_status": _text(scalar(group, "computation_status")) or "unavailable",
                }
            )
            for component, value in enumerate(residual):
                row[f"transition_residual_{component}"] = float(value)
            for component, value in enumerate(predicted):
                row[f"x_pred_next_{component}"] = float(value)
            row["finite_ok"] = bool(np.isfinite(residual).all())
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
        row.update(read_group_scalars(group))
        row.update(
            {
                "source_dataset_path": path,
                "schema_version": scalar(group, "schema_version"),
                "computation_status": _text(scalar(group, "computation_status")) or "unavailable",
                "trace_Q": float(np.trace(covariance)) if covariance.ndim == 2 else float("nan"),
            }
        )
        if covariance.ndim == 2 and covariance.shape[0] == covariance.shape[1]:
            sign, logdet = np.linalg.slogdet(covariance)
            row["q_logdet_regularized"] = float(logdet) if sign > 0 else float("nan")
        row["finite_ok"] = row["computation_status"] == "computed" and bool(np.isfinite(covariance).all())
        row["not_testable"] = not row["finite_ok"]
        row["not_testable_reason"] = None if row["finite_ok"] else f"q_proxy_{row['computation_status']}"
        return [row]


def stochastic_reachability_rows(h5_path: Path, *, dimension: int) -> list[dict[str, Any]]:
    path = local_dynamics_paths(dimension)["stochastic_reachability"]
    with h5py.File(h5_path, "r") as handle:
        if path not in handle:
            return [_unavailable_row(handle, h5_path, dimension=dimension, grain="recording", source_path=path)]
        group = handle[path]
        row = _base(handle, h5_path, dimension=dimension, grain="recording", provenance=group_provenance(group))
        row.update(read_group_scalars(group.get("summary", group)))
        row.update(
            {
                "source_dataset_path": path,
                "schema_version": scalar(group, "schema_version"),
                "computation_status": _text(scalar(group, "computation_status")) or "computed",
            }
        )
        row["finite_ok"] = row["computation_status"] == "computed"
        row["not_testable"] = not row["finite_ok"]
        row["not_testable_reason"] = None if row["finite_ok"] else f"stochastic_reachability_{row['computation_status']}"
        return [row]


def availability_rows(h5_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with h5py.File(h5_path, "r") as handle:
        for dimension in (3, 9):
            surface = availability(handle, dimension)
            row = _base(handle, h5_path, dimension=dimension, grain="recording", provenance={})
            row.update({f"{name}_available": present for name, present in surface.items()})
            for name, path in local_dynamics_paths(dimension).items():
                row[f"{name}_computation_status"] = _text(scalar(handle, f"{path}/computation_status")) if path in handle else "unavailable"
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
