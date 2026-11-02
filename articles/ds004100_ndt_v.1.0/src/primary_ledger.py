"""G1--G3 evidence ledger for ds004100 primary endpoints.

The ledger deliberately audits identities, provenance and native support without
calculating a recording median or any label/participant contrast.  It reports
unknown and failed qualifications as such; it never supplies a default value.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import h5py
import numpy as np


H1_PRODUCT = "dynamical_families/diffusion/v1"
H2_PRODUCT = "dynamical_families/amplification/v1/neighbor_gain_q90_level1"


def _text(value: Any, default: str = "not_recorded") -> str:
    if value is None:
        return default
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _scalar(group: h5py.Group, name: str, default: str = "not_recorded") -> str:
    if name not in group or not isinstance(group[name], h5py.Dataset) or group[name].shape != ():
        return default
    return _text(group[name][()], default)


def _json_signature(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _endpoint_evidence(f: h5py.File, endpoint: str) -> dict[str, Any]:
    product_path = H1_PRODUCT if endpoint == "H1" else H2_PRODUCT
    if product_path not in f:
        return {"product_path": f"/{product_path}", "structurally_eligible": False, "failure": "product_absent"}
    product = f[product_path]
    result = {
        "product_path": f"/{product_path}",
        "computation_status": _scalar(product, "computation_status"),
        "support_status": _scalar(product, "support_status"),
        "measurement_validity": _scalar(product, "measurement_validity"),
        "claim_status": _scalar(product, "claim_status"),
    }
    try:
        series = product["series"]
        values = np.asarray(series["diffusion_effective_dimension" if endpoint == "H1" else "neighbor_gain_q90"][:])
        n_native = len(values)
        if endpoint == "H1":
            valid = np.asarray(series["valid"][:])
            if values.ndim != 1 or valid.shape != values.shape or not np.all(np.isin(valid, (0, 1, False, True))):
                raise ValueError("H1 T-length values/valid mask mismatch")
            usable = np.isfinite(values) & valid.astype(bool)
            index_contract = "T_length_valid_query_mask"
        else:
            pairs = np.asarray(series["n_neighbor_pairs"][:])
            source_idx = np.asarray(series["source_idx"][:])
            if values.ndim != 1 or pairs.shape != values.shape:
                raise ValueError("H2 T-length values/n_neighbor_pairs mismatch")
            if source_idx.ndim != 1 or not np.issubdtype(source_idx.dtype, np.integer):
                raise ValueError("H2 source_idx is not a 1D integer array")
            if len(np.unique(source_idx)) != len(source_idx) or np.any(source_idx < 0) or np.any(source_idx >= n_native - 1):
                raise ValueError("H2 source_idx is duplicate, negative, or terminal")
            source_mask = np.zeros(n_native, dtype=bool)
            source_mask[source_idx] = True
            usable = np.isfinite(values) & source_mask & (pairs > 0)
            index_contract = "T_length_series_indexed_by_unique_nonterminal_source_idx"
        n_usable = int(usable.sum())
        result.update(
            native_centers=n_native,
            valid_centers=n_usable,
            support_fraction=(n_usable / n_native if n_native else 0.0),
            index_contract=index_contract,
            structurally_eligible=(
                result["computation_status"] == "computed"
                and result["support_status"] == "sufficient"
                and n_usable >= 30
                and n_usable >= 0.5 * n_native
            ),
        )
    except (KeyError, ValueError, TypeError) as exc:
        result.update(structurally_eligible=False, failure=str(exc))
    return result


def inspect_record(path: Path, manifest_row: dict[str, str]) -> dict[str, Any]:
    """Read only audit evidence; endpoint values are never retained or summarized."""
    with h5py.File(path, "r") as f:
        task = _text(f.attrs.get("task"), "")
        filename_task = manifest_row.get("filename_task", "")
        source_raw = manifest_row.get("source_raw_files", "")
        normalization = f.get("provenance/normalization")
        support = f.get("provenance/signal_support_provenance")
        times = np.asarray(f["time"][:])
        time_ok = times.ndim == 1 and len(times) > 1 and np.all(np.isfinite(times)) and np.all(np.diff(times) > 0)
        reference_fit_group = support.get("reference_fit_population") if support else None
        reference_fit = _scalar(reference_fit_group, "status") if isinstance(reference_fit_group, h5py.Group) else "absent"
        signatures = {
            "coordinate": _text(f.attrs.get("primary_coordinate_contract")),
            "coordinate_layer": _text(f.attrs.get("primary_coordinate_layer")),
            "normalization": {
                "status": _scalar(normalization, "status") if normalization else "absent",
                "method": _scalar(normalization, "method") if normalization else "absent",
                "scope": _scalar(normalization, "scope") if normalization else "absent",
            },
            "feature": {
                "names_hash": _text(f.attrs.get("feature_export_names_hash")),
                "fit_population_hash": manifest_row.get("feature_fit_population_hashes", "not_recorded"),
                "fit_scope": manifest_row.get("feature_fit_scopes", "not_recorded"),
            },
            "fallback": _text(f.attrs.get("mnps_9d_constructs")),
            "support": manifest_row.get("support_signature", "not_recorded"),
            "source_contact": manifest_row.get("source_raw_files", "not_recorded"),
            "reference": reference_fit,
        }
        temporal_status = _scalar(support, "temporal_support_status") if support else "absent"
        row = {
            "relative_path": path.as_posix(),
            "export_sha256": manifest_row["sha256"],
            "subject_id": _text(f.attrs.get("subject_id")),
            "session": _text(f.attrs.get("session")),
            "acquisition": _text(f.attrs.get("acq")),
            "run": _text(f.attrs.get("run")),
            "label": task,
            "original_recording_id": source_raw,
            "crop_resolution": "unadjudicated",
            "temporal_support_status": temporal_status,
            "reference_fit_population": reference_fit,
            "signatures": signatures,
            "signature_hash": _json_signature(signatures),
            "time_grid_positive": bool(time_ok),
            "endpoint_evidence": {key: _endpoint_evidence(f, key) for key in ("H1", "H2")},
        }
        # A consistent export label is only one G1 evidence item. G1 itself
        # remains false until an independent original-recording/crop ledger
        # resolves duplicates and source identity.
        row["g1_label_identity_evidence"] = bool(task in {"ictal", "interictal"} and task == filename_task and source_raw)
        row["gates"] = {
            "G1": False,
            "G2": False,  # H5 records no actual processing-reference comparability proof.
            "G3": bool(time_ok and all(row["endpoint_evidence"][e].get("structurally_eligible", False) for e in ("H1", "H2"))),
            "G4": False,
        }
        return row


def build_ledger(h5_root: Path, manifest_csv: Path) -> dict[str, Any]:
    """Build a manifest-locked audit ledger without any condition aggregation."""
    with manifest_csv.open(newline="", encoding="utf-8") as handle:
        manifest = {row["relative_path"].replace("\\", "/"): row for row in csv.DictReader(handle)}
    files = sorted(h5_root.rglob("*.h5"))
    rows = []
    for path in files:
        relative = path.relative_to(h5_root).as_posix()
        if relative not in manifest:
            raise ValueError(f"H5 absent from frozen manifest: {relative}")
        row = inspect_record(path, manifest[relative])
        row["relative_path"] = relative
        rows.append(row)
    if set(manifest) != {row["relative_path"] for row in rows}:
        raise ValueError("Frozen manifest and discovered H5 inventory differ")
    return {
        "scope": "G1-G3 evidence only; no recording medians, participant aggregation, effects, or p-values",
        "h5_root": str(h5_root),
        "manifest": str(manifest_csv),
        "n_files": len(rows),
        "rows": rows,
    }


def write_ledger(ledger: dict[str, Any], output: Path) -> None:
    output.write_text(json.dumps(ledger, indent=2, sort_keys=True), encoding="utf-8")
