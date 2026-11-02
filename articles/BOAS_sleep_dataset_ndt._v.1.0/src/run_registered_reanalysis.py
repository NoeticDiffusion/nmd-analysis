"""Run the registered BOAS measurement-family reanalysis.

This module is deliberately read-only with respect to the HDF5 input run.  It
implements the registered A1--A3 reductions from
``preregistration_measurement_families_20260923.md``.  It does not refit an
estimator, impute missing measurements, or turn a serialized computation into
a scientific qualification.

The script is kept in the article so that the exact analysis code can be
hashed and recorded together with the result tables.  It uses the versioned
HDF5 adapters in ``nmd_analysis`` for the stored local-dynamics and family
contracts, while the center eligibility and participant-level reductions are
implemented here because they are article-specific registered estimands.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import h5py
import numpy as np
import pandas as pd

from nmd_analysis.dynamical_families.adapters import (
    family_recording_rows,
    increment_covariance_recording_rows,
    one_step_recording_rows,
)
from nmd_analysis.dynamical_families.readers import read_family, read_identity
from nmd_analysis.local_dynamics.adapters import (
    finite_time_response_horizon_rows,
    jacobian_metrics_recording_rows,
    jacobian_metrics_window_rows,
    stochastic_reachability_rows,
    transition_q_proxy_rows,
    transition_residual_summary_rows,
)


STAGE_LABELS = {0: "Wake", 1: "N1", 2: "N2", 3: "N3", 4: "REM"}
STAGES = (0, 1, 2, 3, 4)
# Each pair is (baseline stage, target stage), so b - a matches the ID label.
PAIRS = ((0, 2, "N2_minus_Wake"), (0, 4, "REM_minus_Wake"), (0, 3, "N3_minus_Wake"))
ENDPOINTS = ("spectral_abscissa", "numerical_abscissa")
DIAGNOSTICS = (
    "spectral_abscissa",
    "numerical_abscissa",
    "reactivity_gap",
    "trace",
    "frobenius_norm",
    "rotation_norm",
    "henrici_departure",
    "spectral_radius",
)
FALLBACKS = ("ppg_rate_bpm", "eog_blink_rate", "eeg_highfreq_power_30_45")
HORIZONS = ("h1", "h2", "h4")
FAMILY_IDS = ("diffusion", "chart_drift", "one_step", "amplification", "history", "turning", "destination", "resilience")
IDENTITIES = {
    "chart_drift": (
        "realized_velocity_level0",
        "conditional_mean_rate_level1/pooled",
        "conditional_mean_rate_level1/blocked_crossfit",
        "conditional_mean_rate_level1/lag_diagnostics",
    ),
    "diffusion": ("increment_covariance_level0",),
}
REQUIRED_QC = (
    "coverage_ok",
    "retained_after_qc",
    "geometry_valid",
)


def _scalar(value: Any) -> Any:
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        return bytes(value).decode("utf-8")
    return value


def _read_scalar(node: Any, path: str, default: Any = None) -> Any:
    if node is None or path not in node:
        return default
    try:
        value = node[path][()]
    except (KeyError, OSError, TypeError, ValueError):
        return default
    return _scalar(value)


def _json_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [_json_value(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return _json_value(value.item())
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        return bytes(value).decode("utf-8")
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _json_text(value: Any) -> str:
    return json.dumps(_json_value(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_tree(root: Path, suffixes: tuple[str, ...] = ()) -> dict[str, str]:
    paths = sorted(path for path in root.rglob("*") if path.is_file() and (not suffixes or path.suffix.lower() in suffixes))
    return {str(path.relative_to(root)): _sha256(path) for path in paths}


def _parse_json(value: Any) -> dict[str, Any]:
    value = _scalar(value)
    if isinstance(value, str):
        try:
            result = json.loads(value)
            return result if isinstance(result, dict) else {}
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def _read_array(handle: h5py.File, path: str, *, dtype: Any | None = None) -> np.ndarray | None:
    if path not in handle or not isinstance(handle[path], h5py.Dataset):
        return None
    values = np.asarray(handle[path][:])
    return values.astype(dtype) if dtype is not None else values


def _fallback_fields(handle: h5py.File) -> tuple[str, str, str]:
    node = handle.get("support_signature/v1/coordinates/e_m")
    return (
        str(_read_scalar(node, "fallback_feature", "unknown")),
        str(_read_scalar(node, "source", "unknown")),
        str(_read_scalar(node, "semantic_equivalence", "unknown")),
    )


def _participant_meta(handle: h5py.File) -> dict[str, Any]:
    meta = _parse_json(handle.attrs.get("participant_meta", "{}"))
    if not meta:
        meta = _parse_json(_read_scalar(handle, "participant/mapped_json", "{}"))
    if "pid" not in meta and "meta_pid" in handle.attrs:
        meta["pid"] = _scalar(handle.attrs["meta_pid"])
    return meta


def _base_identity(handle: h5py.File, path: Path) -> dict[str, Any]:
    meta = _participant_meta(handle)
    fallback, fallback_source, semantic_equivalence = _fallback_fields(handle)
    return {
        "recording_id": path.stem,
        "source_h5": str(path),
        "subject_id": str(_scalar(handle.attrs.get("subject_id", path.parent.name.split("_")[0]))),
        "pid": meta.get("pid"),
        "fallback_feature": fallback,
        "fallback_source": fallback_source,
        "fallback_semantic_equivalence": semantic_equivalence,
        "dataset_id": _scalar(handle.attrs.get("dataset_id")),
        "coordinate_contract": _scalar(handle.attrs.get("primary_coordinate_contract")),
        "coordinate_layer": _scalar(handle.attrs.get("primary_coordinate_layer")),
    }


def _finite(value: Any) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def _finite_array(value: Any) -> bool:
    try:
        return bool(np.isfinite(np.asarray(value, dtype=float)).all())
    except (TypeError, ValueError):
        return False


def _h5_paths(handle: h5py.File) -> list[str]:
    paths: list[str] = []
    handle.visit(paths.append)
    return paths


def _extract_pid_from_path(path: Path) -> str:
    return path.parent.name.split("_")[0]


def audit_recording(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Audit source identity, time windows, gaps, labels and fallback source."""
    with h5py.File(path, "r") as handle:
        base = _base_identity(handle, path)
        epoch = _read_array(handle, "epoch_id")
        window_start = _read_array(handle, "window_start", dtype=float)
        window_end = _read_array(handle, "window_end", dtype=float)
        stage = _read_array(handle, "labels/stage")
        required = {name: name in handle for name in ("epoch_id", "window_start", "window_end", "labels/stage")}
        lengths = {
            "epoch_id": int(len(epoch)) if epoch is not None else None,
            "window_start": int(len(window_start)) if window_start is not None else None,
            "window_end": int(len(window_end)) if window_end is not None else None,
            "stage": int(len(stage)) if stage is not None else None,
        }
        arrays_aligned = len(set(value for value in lengths.values() if value is not None)) == 1 and len(lengths) == sum(required.values())
        gap_seconds = np.asarray([], dtype=float)
        if window_start is not None and window_end is not None and len(window_start) == len(window_end) and len(window_start) > 1:
            gap_seconds = window_start[1:] - window_end[:-1]
        gaps = gap_seconds[gap_seconds > 1e-6]
        known_stage_counts: dict[str, int] = {}
        if stage is not None:
            values, counts = np.unique(stage, return_counts=True)
            known_stage_counts = {str(int(value)): int(count) for value, count in zip(values, counts)}
        source_error = None
        if not all(required.values()):
            source_error = "missing_required_time_or_stage_array"
        elif not arrays_aligned:
            source_error = "per_epoch_array_length_mismatch"
        elif not bool(np.isfinite(window_start).all() and np.isfinite(window_end).all()):
            source_error = "nonfinite_window_bounds"
        elif not bool(np.all(np.diff(window_start) > 0)):
            source_error = "window_start_not_strictly_monotonic"
        elif not bool(np.all(window_end >= window_start)):
            source_error = "window_end_before_window_start"
        elif not bool(np.all(window_start[1:] >= window_end[:-1] - 1e-6)):
            source_error = "overlapping_windows"
        source_row = {
            **base,
            "source_error": source_error,
            "required_arrays_present": bool(all(required.values())),
            "arrays_aligned": bool(arrays_aligned),
            "lengths_json": _json_text(lengths),
            "n_selected_windows": int(len(window_start)) if window_start is not None else 0,
            "n_gap_intervals": int(len(gaps)),
            "total_omitted_seconds": float(np.sum(gaps)) if gaps.size else 0.0,
            "median_gap_seconds": float(np.median(gaps)) if gaps.size else 0.0,
            "maximum_gap_seconds": float(np.max(gaps)) if gaps.size else 0.0,
            "stage_counts_json": _json_text(known_stage_counts),
            "stage_unknown_count": int(sum(count for code, count in known_stage_counts.items() if int(code) not in STAGE_LABELS)),
            "window_start_min": float(np.min(window_start)) if window_start is not None and len(window_start) else None,
            "window_end_max": float(np.max(window_end)) if window_end is not None and len(window_end) else None,
            "window_start_strictly_monotonic": bool(window_start is not None and len(window_start) < 2 or np.all(np.diff(window_start) > 0)) if window_start is not None else False,
            "window_overlap": bool(window_start is not None and window_end is not None and len(window_start) > 1 and np.any(window_start[1:] < window_end[:-1] - 1e-6)),
            "h5_schema_version": _scalar(handle.attrs.get("schema_version")),
            "stage_codebook_json": _json_text(_parse_json(handle.attrs.get("stage_codebook", "{}"))),
            "h5_sha256": _sha256(path),
            "h5_dataset_paths_count": len(_h5_paths(handle)),
        }
        gap_rows = []
        if window_start is not None and window_end is not None:
            for index, seconds in enumerate(gap_seconds):
                if seconds > 1e-6:
                    gap_rows.append({
                        **base,
                        "gap_index": index,
                        "previous_window_end": float(window_end[index]),
                        "next_window_start": float(window_start[index + 1]),
                        "omitted_seconds": float(seconds),
                    })
        return source_row, {"gap_rows": gap_rows, "base": base}


def _read_metric_support(handle: h5py.File, dimension: int) -> dict[str, Any]:
    time_grid = handle.get("provenance/geometry_contract/time_grid")
    provenance_path = "jacobian/derived_metrics/v1/provenance" if dimension == 3 else "jacobian_9D/derived_metrics/v1/provenance"
    provenance = handle.get(provenance_path)
    runtime_dt = _read_scalar(time_grid, "dt_sec_runtime")
    nominal_dt = _read_scalar(provenance, "nominal_dt_sec")
    units = str(_read_scalar(provenance, "abscissa_units", "not_recorded"))
    checks = {
        "runtime_dt_is_30_sec": _finite(runtime_dt) and abs(float(runtime_dt) - 30.0) <= 1e-6,
        "nominal_dt_is_30_sec": _finite(nominal_dt) and abs(float(nominal_dt) - 30.0) <= 1e-6,
        "abscissa_units_recorded": units in {"1/second", "s^-1", "s−1", "s^-1"},
    }
    return {
        "runtime_dt_sec": runtime_dt,
        "nominal_dt_sec": nominal_dt,
        "abscissa_units": units,
        "metric_time_support_ok": bool(all(checks.values())),
        "metric_time_support_reason": None if all(checks.values()) else _json_text(checks),
        "temporal_support_status": _read_scalar(handle, "provenance/signal_support_provenance/temporal_support_status", "not_recorded"),
        "fit_fidelity_gate": _read_scalar(provenance, "fit_fidelity_gate", "not_recorded"),
        "fit_fidelity_threshold": _read_scalar(provenance, "fit_fidelity_threshold"),
    }


def _local_row_context(path: Path, dimension: int) -> dict[str, Any]:
    with h5py.File(path, "r") as handle:
        return {
            **_base_identity(handle, path),
            **_read_metric_support(handle, dimension),
            "signal_support_status": _read_scalar(handle, "provenance/signal_support_provenance/status", "not_recorded"),
        }


def _center_rows(path: Path, dimension: int, *, base: dict[str, Any]) -> list[dict[str, Any]]:
    """Map stored Jacobian centers to epoch labels and apply frozen gates."""
    prefix = "" if dimension == 3 else "_9D"
    jacobian_path = f"jacobian{prefix}"
    metrics_path = f"{jacobian_path}/derived_metrics/v1"
    with h5py.File(path, "r") as handle:
        epochs = _read_array(handle, "epoch_id")
        starts = _read_array(handle, "window_start", dtype=float)
        ends = _read_array(handle, "window_end", dtype=float)
        stages = _read_array(handle, "labels/stage")
        centers = _read_array(handle, f"{jacobian_path}/centers")
        j_hat = _read_array(handle, f"{jacobian_path}/J_hat", dtype=float)
        group = handle.get(metrics_path)
        series = group.get("series") if isinstance(group, h5py.Group) else None
        endpoint_values = {name: _read_array(series, name, dtype=float) if series is not None else None for name in DIAGNOSTICS}
        computation_status = _read_scalar(group, "computation_status", "not_recorded")
        measurement_validity = _read_scalar(group, "measurement_validity", "not_recorded")
        claim_status = _read_scalar(group, "claim_status", "not_recorded")
        required_qc = {name: _read_array(handle, f"qc/windows/{name}") for name in REQUIRED_QC}
        required_qc["mnps_3d_valid" if dimension == 3 else "coords_9d_valid"] = _read_array(
            handle, f"qc/windows/{'mnps_3d_valid' if dimension == 3 else 'coords_9d_valid'}"
        )
        missing_mask_path = "qc/windows/mnps_3d_missing" if dimension == 3 else "qc/windows/coords_9d_missing"
        missing_mask = _read_array(handle, missing_mask_path)
        support = _read_metric_support(handle, dimension)
        n = int(len(centers)) if centers is not None else 0
        duplicate_centers = set()
        if centers is not None:
            numeric_centers = [int(item) for item in centers if np.isfinite(item) and float(item).is_integer()]
            duplicate_centers = {item for item, count in Counter(numeric_centers).items() if count > 1}
        rows: list[dict[str, Any]] = []
        for index in range(n):
            row = {
                **base,
                **support,
                "dimension": dimension,
                "center_row": index,
                "center": None,
                "epoch_id": None,
                "stage_code": None,
                "stage_label": "unknown",
                "computation_status": computation_status,
                "measurement_validity": measurement_validity,
                "claim_status": claim_status,
                "j_hat_finite": False,
                "center_mapping_ok": False,
                "eligibility": False,
                "failure_reason": None,
                "boundary_ok": False,
                "boundary_failure_reason": None,
            }
            reasons: list[str] = []
            center_value = centers[index] if centers is not None and index < len(centers) else None
            valid_center = center_value is not None and np.isfinite(center_value) and float(center_value).is_integer()
            if valid_center:
                center = int(center_value)
                row["center"] = center
                if center in duplicate_centers:
                    reasons.append("duplicate_center")
                if epochs is None or starts is None or ends is None or stages is None:
                    reasons.append("missing_center_alignment_arrays")
                elif not 0 <= center < len(epochs):
                    reasons.append("center_out_of_bounds")
                else:
                    row.update({"epoch_id": int(epochs[center]), "stage_code": int(stages[center]), "stage_label": STAGE_LABELS.get(int(stages[center]), "unknown")})
                    row["center_mapping_ok"] = True
            else:
                reasons.append("center_not_integer")
            if j_hat is None or j_hat.ndim != 3 or index >= len(j_hat) or not _finite_array(j_hat[index]):
                reasons.append("j_hat_nonfinite_or_missing")
            else:
                row["j_hat_finite"] = True
            if computation_status != "computed":
                reasons.append(f"parent_{computation_status}")
            if not support["metric_time_support_ok"]:
                reasons.append("metric_time_support_inconsistent")
            if centers is None or j_hat is None or len(j_hat) != len(centers):
                reasons.append("center_j_hat_length_mismatch")
            for name, values in endpoint_values.items():
                value = values[index] if values is not None and index < len(values) else np.nan
                row[name] = float(value) if np.asarray(value).ndim == 0 and _finite(value) else np.nan
                if name in ENDPOINTS and not _finite(value):
                    reasons.append(f"{name}_nonfinite")
            if any(values is None or index >= len(values) or len(values) != n for values in endpoint_values.values()):
                reasons.append("metric_series_alignment_failure")
            for name, values in required_qc.items():
                value = values[center] if values is not None and row["center_mapping_ok"] and center < len(values) else None
                row[f"qc_{name}"] = int(value) if value is not None else None
                if value is None:
                    reasons.append(f"missing_qc_{name}")
                elif int(value) != 1:
                    reasons.append(f"qc_{name}_false")
            # The canonical export uses the explicit ``*_valid`` arrays as
            # the missingness masks.  If an additive ``*_missing`` mask is
            # present, a true value is an additional failure; its absence is
            # not itself a failure of the canonical contract.
            if missing_mask is not None and row["center_mapping_ok"] and bool(missing_mask[row["center"]]):
                reasons.append("qc_missing_mask_true")
            if row["center_mapping_ok"] and starts is not None and ends is not None:
                center = row["center"]
                if center > 0 and center + 1 < len(starts) and int(stages[center - 1]) in STAGE_LABELS and int(stages[center]) in STAGE_LABELS and int(stages[center + 1]) in STAGE_LABELS:
                    touching = abs(float(ends[center - 1]) - float(starts[center])) <= 1e-6 and abs(float(ends[center]) - float(starts[center + 1])) <= 1e-6
                    same_stage = int(stages[center - 1]) == int(stages[center]) == int(stages[center + 1])
                    row["boundary_ok"] = bool(touching and same_stage)
                    if not row["boundary_ok"]:
                        row["boundary_failure_reason"] = "adjacent_rows_not_touching_or_stage_changed"
                else:
                    row["boundary_failure_reason"] = "adjacent_rows_missing_or_unknown_stage"
            else:
                row["boundary_failure_reason"] = "center_mapping_failed"
            row["eligibility"] = not reasons
            row["failure_reason"] = ";".join(dict.fromkeys(reasons)) or None
            rows.append(row)
        return rows


def _nanmedian(values: Iterable[Any]) -> float | None:
    array = np.asarray([value for value in values if _finite(value)], dtype=float)
    return float(np.median(array)) if array.size else None


def _quantile(values: Iterable[Any], q: float) -> float | None:
    array = np.asarray([value for value in values if _finite(value)], dtype=float)
    return float(np.quantile(array, q)) if array.size else None


def _bootstrap_median(person_recordings: dict[Any, list[float]], *, seed: int, n_bootstrap: int = 10_000) -> tuple[float | None, float | None]:
    if len(person_recordings) < 20:
        return None, None
    rng = np.random.default_rng(seed)
    # The within-person reduction is already the median of that person's
    # eligible recording contrasts.  Resampling those person-level medians
    # is the registered person-cluster bootstrap, and avoids a Python loop
    # over every replicate without changing the estimand.
    person_values = np.asarray([np.median(values) for values in person_recordings.values()], dtype=float)
    sampled_indices = rng.integers(0, len(person_values), size=(n_bootstrap, len(person_values)))
    bootstrap_medians = np.median(person_values[sampled_indices], axis=1)
    return float(np.quantile(bootstrap_medians, 0.025)), float(np.quantile(bootstrap_medians, 0.975))


def _build_contrast_tables(center_df: pd.DataFrame, *, boundary_only: bool = False) -> dict[str, pd.DataFrame]:
    usable = center_df[center_df["eligibility"].astype(bool)].copy()
    if boundary_only:
        usable = usable[usable["boundary_ok"].astype(bool)].copy()
    recording_rows: list[dict[str, Any]] = []
    for keys, group in center_df.groupby(["recording_id", "pid", "fallback_feature", "dimension"], dropna=False):
        recording_id, pid, fallback, dimension = keys
        # ``group`` is already one recording/representation/fallback cell;
        # filtering the full center table again here makes the 128-recording
        # boundary pass needlessly quadratic.
        selected = group[group["eligibility"].astype(bool)].copy()
        if boundary_only:
            selected = selected[selected["boundary_ok"].astype(bool)].copy()
        for stage_a, stage_b, contrast_id in PAIRS:
            values: dict[str, Any] = {
                "recording_id": recording_id,
                "pid": pid,
                "fallback_feature": fallback,
                "dimension": dimension,
                "contrast_id": contrast_id,
                "stage_a": STAGE_LABELS[stage_a],
                "stage_b": STAGE_LABELS[stage_b],
                "boundary_only": boundary_only,
            }
            a = selected[selected["stage_code"] == stage_a]
            b = selected[selected["stage_code"] == stage_b]
            values.update({"n_centers_a": int(len(a)), "n_centers_b": int(len(b))})
            values["support_ok"] = bool(len(a) >= 5 and len(b) >= 5)
            for endpoint in ENDPOINTS + ("reactivity_gap",):
                a_median = _nanmedian(a[endpoint])
                b_median = _nanmedian(b[endpoint])
                values[f"{endpoint}_a_median"] = a_median
                values[f"{endpoint}_b_median"] = b_median
                values[f"{endpoint}_contrast"] = b_median - a_median if values["support_ok"] and a_median is not None and b_median is not None else None
            values["contrast_status"] = "available" if values["support_ok"] else "unavailable_minimum_stage_support"
            recording_rows.append(values)
    recording_df = pd.DataFrame(recording_rows)
    person_rows: list[dict[str, Any]] = []
    if not recording_df.empty:
        for keys, group in recording_df.groupby(["pid", "fallback_feature", "dimension", "contrast_id"], dropna=False):
            pid, fallback, dimension, contrast_id = keys
            values = group["spectral_abscissa_contrast"].dropna().tolist()
            person_row = {
                "pid": pid,
                "fallback_feature": fallback,
                "dimension": dimension,
                "contrast_id": contrast_id,
                "boundary_only": boundary_only,
            }
            for endpoint in ENDPOINTS + ("reactivity_gap",):
                endpoint_values = group[f"{endpoint}_contrast"].dropna().astype(float).tolist()
                person_row[f"n_recordings_{endpoint}"] = int(len(endpoint_values))
                person_row[f"{endpoint}_person_contrast"] = _nanmedian(endpoint_values)
                person_row[f"{endpoint}_recording_contrasts_json"] = _json_text(endpoint_values)
            person_row["n_recordings"] = int(len(values))
            person_row["person_contrast"] = _nanmedian(values)
            person_row["recording_contrasts_json"] = _json_text(values)
            person_rows.append(person_row)
    person_df = pd.DataFrame(person_rows)
    summary_rows: list[dict[str, Any]] = []
    if not person_df.empty:
        for keys, group in person_df.groupby(["fallback_feature", "dimension", "contrast_id"], dropna=False):
            fallback, dimension, contrast_id = keys
            out = {
                "fallback_feature": fallback,
                "dimension": dimension,
                "contrast_id": contrast_id,
                "boundary_only": boundary_only,
                "stage_a": "Wake",
                "stage_b": contrast_id.replace("_minus_Wake", ""),
                "n_people_eligible": int(group["spectral_abscissa_person_contrast"].notna().sum()),
                "n_recordings_eligible": int(group["n_recordings"].sum()),
            }
            alpha_people = group[group["spectral_abscissa_person_contrast"].notna()]
            alpha_recordings = {
                row["pid"]: [float(value) for value in json.loads(row["spectral_abscissa_recording_contrasts_json"])]
                for _, row in alpha_people.iterrows()
            }
            ci_low, ci_high = _bootstrap_median(alpha_recordings, seed=20260923)
            out.update({"bootstrap_seed": 20260923, "bootstrap_replicates": 10_000 if ci_low is not None else None, "bootstrap_q025": ci_low, "bootstrap_q975": ci_high})
            for endpoint in ENDPOINTS + ("reactivity_gap",):
                column = f"{endpoint}_person_contrast"
                values = group[column].dropna().astype(float).to_numpy()
                endpoint_people = group[group[column].notna()]
                endpoint_recordings = {
                    row["pid"]: [float(value) for value in json.loads(row[f"{endpoint}_recording_contrasts_json"])]
                    for _, row in endpoint_people.iterrows()
                }
                endpoint_low, endpoint_high = _bootstrap_median(endpoint_recordings, seed=20260923)
                out.update({
                    f"n_people_{endpoint}_eligible": int(len(endpoint_people)),
                    f"n_recordings_{endpoint}_eligible": int(group[f"n_recordings_{endpoint}"].sum()),
                    f"{endpoint}_median": float(np.median(values)) if values.size else None,
                    f"{endpoint}_q25": float(np.quantile(values, 0.25)) if values.size else None,
                    f"{endpoint}_q75": float(np.quantile(values, 0.75)) if values.size else None,
                    f"{endpoint}_positive_count": int(np.sum(values > 0)) if values.size else 0,
                    f"{endpoint}_negative_count": int(np.sum(values < 0)) if values.size else 0,
                    f"{endpoint}_zero_count": int(np.sum(values == 0)) if values.size else 0,
                    f"{endpoint}_bootstrap_q025": endpoint_low,
                    f"{endpoint}_bootstrap_q975": endpoint_high,
                })
            summary_rows.append(out)
    return {
        "recording": recording_df,
        "person": person_df,
        "summary": pd.DataFrame(summary_rows),
    }


def _metric_inventory(center_df: pd.DataFrame) -> pd.DataFrame:
    if center_df.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    usable = center_df[center_df["eligibility"].astype(bool)]
    for keys, group in center_df.groupby(["recording_id", "pid", "fallback_feature", "dimension"], dropna=False):
        recording_id, pid, fallback, dimension = keys
        selected = usable[(usable["recording_id"] == recording_id) & (usable["dimension"] == dimension)]
        for stage_code in STAGES:
            stage_group = selected[selected["stage_code"] == stage_code]
            row = {
                "recording_id": recording_id,
                "pid": pid,
                "fallback_feature": fallback,
                "dimension": dimension,
                "stage_code": stage_code,
                "stage_label": STAGE_LABELS[stage_code],
                "n_eligible_centers": int(len(stage_group)),
            }
            for metric in DIAGNOSTICS:
                row[f"{metric}_median"] = _nanmedian(stage_group[metric]) if metric in stage_group else None
            rows.append(row)
    return pd.DataFrame(rows)


def _ftr_rows(path: Path, dimension: int, *, base: dict[str, Any]) -> list[dict[str, Any]]:
    rows = finite_time_response_horizon_rows(path, dimension=dimension)
    with h5py.File(path, "r") as handle:
        parent = handle.get(f"finite_time_response/v1/{'primary' if dimension == 3 else 'stratified_9d'}")
        peak = _read_scalar(parent, "summary/g_peak_over_horizons")
        parent_status = _read_scalar(parent, "computation_status", "not_recorded")
        parent_validity = _read_scalar(parent, "measurement_validity", "not_recorded")
        parent_claim = _read_scalar(parent, "claim_status", "not_recorded")
        provenance = parent.get("provenance") if isinstance(parent, h5py.Group) else None
        parent_support = _read_scalar(provenance, "temporal_support_status", "not_recorded")
    output: list[dict[str, Any]] = []
    for row in rows:
        if row.get("horizon_name") not in HORIZONS:
            continue
        row = {**base, **row}
        row.update({
            "dimension": dimension,
            "g_peak_over_horizons_json": _json_text(peak),
            "parent_computation_status": parent_status,
            "parent_measurement_validity": parent_validity,
            "parent_claim_status": parent_claim,
            "parent_temporal_support_status": parent_support,
        })
        nominated = row.get("mean_log_g_max")
        actual = row.get("mean_actual_horizon_sec")
        row["registered_horizon_usable"] = bool(row.get("computation_status") == "computed" and int(row.get("n_sequences_valid") or 0) > 0 and _finite(nominated) and _finite(actual) and float(actual) > 0)
        if not row["registered_horizon_usable"]:
            row["registered_horizon_failure_reason"] = ";".join(filter(None, [
                None if row.get("computation_status") == "computed" else f"parent_{row.get('computation_status')}",
                None if int(row.get("n_sequences_valid") or 0) > 0 else "no_valid_sequences",
                None if _finite(nominated) else "mean_log_g_max_nonfinite",
                None if _finite(actual) and float(actual) > 0 else "actual_horizon_nonpositive_or_nonfinite",
            ]))
        else:
            row["registered_horizon_failure_reason"] = None
        output.append(row)
    return output


def _series_summary(payload: dict[str, Any]) -> dict[str, Any]:
    series = payload.get("series") if isinstance(payload.get("series"), dict) else {}
    arrays = [np.asarray(value) for value in series.values() if isinstance(value, (list, tuple, np.ndarray)) and np.asarray(value).ndim >= 1]
    n_rows = max((int(array.shape[0]) for array in arrays), default=0)
    finite_rows = None
    if arrays:
        finite_rows = int(np.sum(np.isfinite(arrays[0]))) if arrays[0].dtype.kind in "fc" else None
    dt_values = np.asarray([], dtype=float)
    for name in ("dt_sec", "actual_dt_sec", "time_step_sec"):
        if name in series:
            dt_values = np.asarray(series[name], dtype=float).reshape(-1)
            break
    return {
        "n_serialized_series_rows": n_rows,
        "n_finite_values_first_series": finite_rows,
        "temporal_support_n": int(dt_values.size),
        "temporal_support_dt_median_sec": float(np.median(dt_values)) if dt_values.size and np.isfinite(dt_values).any() else None,
        "temporal_support_dt_min_sec": float(np.min(dt_values)) if dt_values.size and np.isfinite(dt_values).all() else None,
        "temporal_support_dt_max_sec": float(np.max(dt_values)) if dt_values.size and np.isfinite(dt_values).all() else None,
    }


def _ledger_row(base: dict[str, Any], *, family: str, role: str, payload: dict[str, Any], source_path: str | None, identity: str | None = None, dimension: int | None = None) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    provenance = payload.get("provenance") if isinstance(payload.get("provenance"), dict) else {}
    grain = payload.get("grain") if isinstance(payload.get("grain"), dict) else {}
    row = {
        **base,
        "family": family,
        "family_role": role,
        "identity_id": identity,
        "dimension": dimension,
        "source_dataset_path": source_path,
        "schema_version": payload.get("schema_version", "not_recorded"),
        "computation_status": payload.get("computation_status", "not_recorded"),
        "measurement_validity": payload.get("measurement_validity", "not_recorded"),
        "support_status": payload.get("support_status", summary.get("support_status", "not_recorded")),
        "qualification_status": payload.get("qualification_status", summary.get("qualification_status", "not_recorded")),
        "claim_status": payload.get("claim_status", "not_recorded"),
        "failure_reason": payload.get("failure_reason"),
        "validation_level": provenance.get("validation_level", "not_recorded"),
        "time_semantics": provenance.get("time_semantics", "not_recorded"),
        "estimator": provenance.get("estimator", "not_recorded"),
        "coordinate_layer": provenance.get("coordinate_layer", payload.get("coordinate_layer", "not_recorded")),
        "grain_native": grain.get("native", "not_recorded"),
        "grain_parent": grain.get("parent", "not_recorded"),
        "grain_biological_unit": grain.get("biological_unit", "not_recorded"),
        "grain_repeated_measure": grain.get("repeated_measure", "not_recorded"),
        "grain_direct_between_subject_inference": grain.get("direct_between_subject_inference", "not_recorded"),
        "not_testable_reason": None,
    }
    row.update(_series_summary(payload))
    if row["computation_status"] != "computed":
        row["not_testable_reason"] = row["failure_reason"] or f"{family}_{row['computation_status']}"
    row["finite_row_status"] = "computed" if row["computation_status"] == "computed" else "not_testable"
    return row


def build_family_ledger(path: Path, *, base: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    covariance_rows: list[dict[str, Any]] = []
    with h5py.File(path, "r") as handle:
        for family in FAMILY_IDS:
            payload = read_family(handle, family)
            rows.append(_ledger_row(base, family=family, role="parent", payload=payload, source_path=payload.get("source_dataset_path")))
            for identity in IDENTITIES.get(family, ()):
                identity_payload = read_identity(handle, family, identity)
                rows.append(_ledger_row(base, family=family, role="identity", payload=identity_payload, source_path=identity_payload.get("source_dataset_path"), identity=identity))
                if family == "diffusion" and identity == "increment_covariance_level0":
                    child_summary = identity_payload.get("summary") if isinstance(identity_payload.get("summary"), dict) else {}
                    series = identity_payload.get("series") if isinstance(identity_payload.get("series"), dict) else {}
                    covariance_rows.append({
                        **base,
                        "family": "diffusion",
                        "identity_id": identity,
                        "computation_status": identity_payload.get("computation_status", "not_recorded"),
                        "measurement_validity": identity_payload.get("measurement_validity", "not_recorded"),
                        "support_status": identity_payload.get("support_status", "not_recorded"),
                        "qualification_status": identity_payload.get("qualification_status", child_summary.get("qualification_status", "not_recorded")),
                        "n_increment_pairs": identity_payload.get("summary", {}).get("n_increment_pairs") if isinstance(identity_payload.get("summary"), dict) else None,
                        "increment_covariance_json": _json_text(identity_payload.get("summary", {}).get("increment_covariance")) if isinstance(identity_payload.get("summary"), dict) else None,
                        "not_divided_by_dt": identity_payload.get("summary", {}).get("not_divided_by_dt", True) if isinstance(identity_payload.get("summary"), dict) else True,
                        "not_local_knn": identity_payload.get("summary", {}).get("not_local_knn", True) if isinstance(identity_payload.get("summary"), dict) else True,
                        "not_ito_diffusion_tensor": identity_payload.get("summary", {}).get("not_ito_diffusion_tensor", True) if isinstance(identity_payload.get("summary"), dict) else True,
                        "source_dataset_path": identity_payload.get("source_dataset_path"),
                    })
        drift = read_family(handle, "chart_drift")
        for identity in IDENTITIES["chart_drift"]:
            identity_payload = read_identity(handle, "chart_drift", identity)
            rows.append(_ledger_row(base, family="chart_drift", role="identity", payload=identity_payload, source_path=identity_payload.get("source_dataset_path"), identity=identity))
        for dimension in (3, 9):
            dimension_rows = [
                ("jacobian_metrics", jacobian_metrics_recording_rows(path, dimension=dimension)[0]),
                ("finite_time_response", finite_time_response_horizon_rows(path, dimension=dimension)[0]),
                ("transition_residuals", transition_residual_summary_rows(path, dimension=dimension)[0]),
                ("transition_residual_covariance_proxy_Q", transition_q_proxy_rows(path, dimension=dimension)[0]),
                ("stochastic_reachability_W_Q", stochastic_reachability_rows(path, dimension=dimension)[0]),
            ]
            for family, adapter_row in dimension_rows:
                rows.append({
                    **base,
                    "family": family,
                    "family_role": "local_dynamics",
                    "identity_id": None,
                    "dimension": dimension,
                    "source_dataset_path": adapter_row.get("source_dataset_path"),
                    "schema_version": adapter_row.get("schema_version", "not_recorded"),
                    "computation_status": adapter_row.get("computation_status", "not_recorded"),
                    "measurement_validity": adapter_row.get("measurement_validity", "not_recorded"),
                    "support_status": adapter_row.get("support_status", "not_recorded"),
                    "qualification_status": adapter_row.get("qualification_status", "not_recorded"),
                    "claim_status": adapter_row.get("claim_status", "not_recorded"),
                    "failure_reason": adapter_row.get("failure_reason"),
                    "validation_level": adapter_row.get("validation_level", "not_recorded"),
                    "time_semantics": adapter_row.get("ld_time_semantics", adapter_row.get("q_time_semantics", "not_recorded")),
                    "estimator": adapter_row.get("ld_estimator", "not_recorded"),
                    "coordinate_layer": adapter_row.get("coordinate_layer", "not_recorded"),
                    "grain_native": adapter_row.get("grain_native", "not_recorded"),
                    "grain_parent": adapter_row.get("grain_parent", "not_recorded"),
                    "grain_biological_unit": adapter_row.get("grain_biological_unit", "not_recorded"),
                    "grain_repeated_measure": adapter_row.get("grain_repeated_measure", "not_recorded"),
                    "grain_direct_between_subject_inference": adapter_row.get("grain_direct_between_subject_inference", "not_recorded"),
                    "n_serialized_series_rows": adapter_row.get("n_transitions_valid", adapter_row.get("n_windows_metrics_valid", adapter_row.get("n_sequences_valid"))),
                    "n_finite_values_first_series": None,
                    "temporal_support_n": None,
                    "temporal_support_dt_median_sec": None,
                    "temporal_support_dt_min_sec": None,
                    "temporal_support_dt_max_sec": None,
                    "not_testable_reason": adapter_row.get("not_testable_reason"),
                    "finite_row_status": "computed" if adapter_row.get("finite_ok") else "not_testable",
                })
    return rows, covariance_rows


def _write_frame(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, na_rep="")


def _write_json(payload: Any, path: Path) -> None:
    path.write_text(json.dumps(_json_value(payload), indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def run(input_root: Path, output_root: Path, *, limit: int | None = None) -> dict[str, Any]:
    input_root = input_root.resolve()
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=False)
    h5_paths = sorted(input_root.glob("sub-*/*.h5"))
    if limit is not None:
        h5_paths = h5_paths[:limit]
    if not h5_paths:
        raise FileNotFoundError(f"No sub-*/*.h5 files found under {input_root}")

    source_rows: list[dict[str, Any]] = []
    gap_rows: list[dict[str, Any]] = []
    center_rows: list[dict[str, Any]] = []
    ftr_rows: list[dict[str, Any]] = []
    ledger_rows: list[dict[str, Any]] = []
    covariance_rows: list[dict[str, Any]] = []
    metric_inventory_rows: list[pd.DataFrame] = []

    for index, path in enumerate(h5_paths, start=1):
        source_row, extra = audit_recording(path)
        source_rows.append(source_row)
        gap_rows.extend(extra["gap_rows"])
        base = extra["base"]
        for dimension in (3, 9):
            local_context = _local_row_context(path, dimension)
            rows = _center_rows(path, dimension, base={**base, **local_context})
            center_rows.extend(rows)
            metric_inventory_rows.append(_metric_inventory(pd.DataFrame(rows)))
            ftr_rows.extend(_ftr_rows(path, dimension, base=base))
        ledger, covariance = build_family_ledger(path, base=base)
        ledger_rows.extend(ledger)
        covariance_rows.extend(covariance)
        if index % 10 == 0 or index == len(h5_paths):
            print(f"processed {index}/{len(h5_paths)} recordings", file=sys.stderr)

    source_df = pd.DataFrame(source_rows)
    gaps_df = pd.DataFrame(gap_rows)
    centers_df = pd.DataFrame(center_rows)
    ftr_df = pd.DataFrame(ftr_rows)
    ledger_df = pd.DataFrame(ledger_rows)
    covariance_df = pd.DataFrame(covariance_rows)
    inventory_df = pd.concat(metric_inventory_rows, ignore_index=True) if metric_inventory_rows else pd.DataFrame()

    outputs: dict[str, str] = {}
    tables = {
        "source_inventory": source_df,
        "gap_intervals": gaps_df,
        "center_eligibility": centers_df,
        "a1_metric_inventory": inventory_df,
        "a2_ftr_recording_horizons": ftr_df,
        "a3_family_ledger": ledger_df,
        "a3_increment_covariance": covariance_df,
    }
    for name, frame in tables.items():
        path = output_root / f"{name}.csv"
        _write_frame(frame, path)
        outputs[name] = str(path)

    contrast_outputs: dict[str, str] = {}
    for boundary_only, prefix in ((False, "a1"), (True, "a1_boundary")):
        contrasts = _build_contrast_tables(centers_df, boundary_only=boundary_only)
        for name, frame in contrasts.items():
            path = output_root / f"{prefix}_{name}_contrasts.csv" if name != "summary" else output_root / f"{prefix}_summary.csv"
            _write_frame(frame, path)
            contrast_outputs[f"{prefix}_{name}"] = str(path)
    outputs.update(contrast_outputs)

    # A2 reductions are deliberately separate from stage-labelled A1 cells.
    ftr_recording = ftr_df.copy()
    if not ftr_recording.empty:
        ftr_recording["fallback_feature"] = ftr_recording["fallback_feature"].astype(str)
        usable = ftr_recording[ftr_recording["registered_horizon_usable"].astype(bool)].copy()
        person_rows: list[dict[str, Any]] = []
        for keys, group in usable.groupby(["pid", "fallback_feature", "dimension", "horizon_name"], dropna=False):
            pid, fallback, dimension, horizon = keys
            person_rows.append({
                "pid": pid,
                "fallback_feature": fallback,
                "dimension": dimension,
                "horizon_name": horizon,
                "n_recordings": int(len(group)),
                "mean_log_g_max_person_median": _nanmedian(group["mean_log_g_max"]),
                "mean_g_max_person_median": _nanmedian(group["mean_g_max"]),
                "mean_d_resp_person_median": _nanmedian(group["mean_d_resp"]),
                "mean_c_1_person_median": _nanmedian(group["mean_c_1"]),
                "actual_horizon_sec_person_median": _nanmedian(group["mean_actual_horizon_sec"]),
            })
        ftr_person_df = pd.DataFrame(person_rows)
        ftr_summary_rows: list[dict[str, Any]] = []
        if not ftr_person_df.empty:
            for keys, group in ftr_person_df.groupby(["fallback_feature", "dimension", "horizon_name"], dropna=False):
                fallback, dimension, horizon = keys
                out = {"fallback_feature": fallback, "dimension": dimension, "horizon_name": horizon, "n_people_eligible": int(len(group)), "n_recordings_eligible": int(group["n_recordings"].sum())}
                for field in ("mean_log_g_max", "mean_g_max", "mean_d_resp", "mean_c_1", "actual_horizon_sec"):
                    values = group[f"{field}_person_median"].dropna().astype(float)
                    out[f"{field}_median"] = float(values.median()) if not values.empty else None
                    out[f"{field}_q25"] = float(values.quantile(0.25)) if not values.empty else None
                    out[f"{field}_q75"] = float(values.quantile(0.75)) if not values.empty else None
                ftr_summary_rows.append(out)
        ftr_person_df = ftr_person_df if not ftr_person_df.empty else pd.DataFrame(columns=["pid", "fallback_feature", "dimension", "horizon_name"])
        ftr_summary_df = pd.DataFrame(ftr_summary_rows)
    else:
        ftr_person_df = pd.DataFrame()
        ftr_summary_df = pd.DataFrame()
    _write_frame(ftr_person_df, output_root / "a2_ftr_person_horizons.csv")
    _write_frame(ftr_summary_df, output_root / "a2_ftr_summary.csv")
    outputs.update({"a2_ftr_person_horizons": str(output_root / "a2_ftr_person_horizons.csv"), "a2_ftr_summary": str(output_root / "a2_ftr_summary.csv")})

    run_manifest = input_root / "run_manifest.json"
    ingest_config = input_root / "config_ingest_ds005555_dynamical_families.yaml"
    code_path = Path(__file__).resolve()
    try:
        git_revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=code_path.parents[3], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        git_revision = None
    runtime = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "h5py": h5py.__version__,
        "git_revision": git_revision,
        "analysis_script": str(code_path),
    }
    _write_json(runtime, output_root / "runtime.json")
    _write_json({
        "analysis": "BOAS_sleep_measurement_families_registered_reanalysis_v1",
        "registration": "preregistration_measurement_families_20260923.md",
        "input_root": str(input_root),
        "output_root": str(output_root),
        "n_h5_files_processed": len(h5_paths),
        "source_run_manifest_sha256": _sha256(run_manifest) if run_manifest.exists() else None,
        "source_ingest_config_sha256": _sha256(ingest_config) if ingest_config.exists() else None,
        "analysis_script_sha256": _sha256(code_path),
        "hdf5_sha256": {row["recording_id"]: row["h5_sha256"] for row in source_rows},
        "exact_command": " ".join(sys.argv),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "registered_constants": {"stage_codebook": STAGE_LABELS, "pairs": PAIRS, "bootstrap_seed": 20260923, "bootstrap_replicates": 10_000, "minimum_centers_per_stage": 5},
        "limitations": ["input run is stage-sampled and contains gaps", "fit fidelity gate is reported but not evaluated", "temporal signal support is reported as recorded", "no biological or confirmatory claim is made"],
    }, output_root / "analysis_manifest.json")
    _write_json({
        "source_run_manifest": str(run_manifest),
        "source_run_manifest_sha256": _sha256(run_manifest) if run_manifest.exists() else None,
        "source_ingest_config": str(ingest_config),
        "source_ingest_config_sha256": _sha256(ingest_config) if ingest_config.exists() else None,
        "analysis_script": str(code_path),
        "analysis_script_sha256": _sha256(code_path),
        "runtime_file": str(output_root / "runtime.json"),
        "input_hdf5_files": {row["recording_id"]: {"path": row["source_h5"], "sha256": row["h5_sha256"]} for row in source_rows},
    }, output_root / "hash_manifest.json")
    outputs.update({"runtime": str(output_root / "runtime.json"), "analysis_manifest": str(output_root / "analysis_manifest.json"), "hash_manifest": str(output_root / "hash_manifest.json")})
    return {"output_root": str(output_root), "n_h5_files": len(h5_paths), "outputs": outputs}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None, help="Bounded reference run; omit for the registered run.")
    args = parser.parse_args(argv)
    result = run(args.input_root, args.output_root, limit=args.limit)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
