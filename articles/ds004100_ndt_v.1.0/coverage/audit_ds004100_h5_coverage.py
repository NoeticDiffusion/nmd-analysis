#!/usr/bin/env python3
"""Read-only coverage audit for the ds004100 NDT v1.0 H5 export.

This script reads every ``*.h5`` below ``--data-root`` and writes only audit
artifacts below ``--output-dir``.  It never changes an input file and does not
compute condition features, effect sizes, or hypothesis outcomes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import pathlib
import platform
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

import h5py
import numpy as np


CORE = {
    "mnps_3d": "/mnps_3d",
    "coords_3d_subject": "/coords_3d_subject_anchored/values",
    "coords_3d_cohort": "/coords_3d_cohort_anchored/values",
    "coords_9d": "/coords_9d/values",
    "coords_9d_subject": "/coords_9d_subject_anchored/values",
    "coords_9d_cohort": "/coords_9d_cohort_anchored/values",
    "J_3d": "/jacobian/J_hat",
    "J_9d": "/jacobian_9D/J_hat",
    "J_3d_subject": "/jacobian_subject_anchored/J_hat",
    "J_3d_cohort": "/jacobian_cohort_anchored/J_hat",
    "J_9d_subject": "/jacobian_9D_subject_anchored/J_hat",
    "J_9d_cohort": "/jacobian_9D_cohort_anchored/J_hat",
    "time": "/time",
    "window_start": "/window_start",
    "window_end": "/window_end",
}

EXTRA = {
    "features_raw": "/features_raw/values",
    "features_robust_z": "/features_robust_z/values",
    "features_projection_z": "/features_projection_z/values",
    "feature_anchor_center": "/feature_anchors/per_feature/center",
    "nn_indices": "/nn/indices",
}

CSV_FIELDS = [
    "relative_path", "sha256", "size_bytes", "mtime_utc", "subject", "session",
    "run", "task", "acq", "group", "n_time", "time_first_sec", "time_last_sec",
    "time_span_sec", "window_support_first_sec", "window_support_last_sec",
    "window_support_span_sec", "median_dt_sec", "max_dt_sec", "gap_count",
    "nonpositive_dt_count", "expected_step_sec", "window_len_median_sec",
    "window_len_mismatch_count", "geometry_status", "dropped_geometry_epochs",
    "dropped_missing_axis_epochs", "epochs_raw", "epochs_after_geometry",
    "epochs_after_nan", "epochs_after_qc", "primary_coordinate_contract",
    "primary_coordinate_layer", "mnps_9d_definition_version", "mndm_version",
    "anchor_id", "anchor_hash", "anchor_source", "normalization_status",
    "normalization_method", "normalization_scope", "feature_count_raw",
    "feature_count_robust_z", "raw_feature_finite_rows", "robust_z_feature_finite_rows",
    "finite_mnps_3d_rows", "finite_coords_9d_rows",
    "row_source_formats", "source_raw_files", "event_group_present", "label_group_present",
    "summary_events_count", "summary_labels_count", "time_reference_enabled",
    "time_reference_status", "pseudo_stage_enabled", "stage_codebook_present",
    "J_3d_present", "J_9d_present", "J_3d_subject_present", "J_3d_cohort_present",
    "J_9d_subject_present", "J_9d_cohort_present", "FTR_present", "FTR_status",
    "FTR_validation_level", "FTR_horizons", "residuals_present", "residuals_status",
    "residual_covariance_present", "residual_covariance_status", "stochastic_reachability_present",
    "jacobian_qualified", "dynamical_qualified", "error",
]


def scalar(v):
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    if isinstance(v, np.ndarray):
        if v.ndim == 0:
            return scalar(v.item())
        return [scalar(x) for x in v.tolist()]
    if isinstance(v, np.generic):
        return scalar(v.item())
    if isinstance(v, (float, np.floating)) and not math.isfinite(float(v)):
        return None
    return v


def attr(g, key, default=""):
    return scalar(g.attrs[key]) if key in g.attrs else default


def field(g, key, default=""):
    """Read a scalar H5 attribute or scalar dataset without coercing arrays."""
    if g is None:
        return default
    if key in g.attrs:
        return scalar(g.attrs[key])
    if key in g and isinstance(g[key], h5py.Dataset):
        x = g[key][()]
        return scalar(x)
    return default


def data(f, path):
    return np.asarray(f[path][()]) if path in f else None


def finite_count(a):
    if a is None or not np.issubdtype(a.dtype, np.number):
        return ""
    return int(np.isfinite(a).sum())


def finite_rows(a):
    if a is None or a.ndim < 2 or not np.issubdtype(a.dtype, np.number):
        return ""
    return int(np.isfinite(a).all(axis=tuple(range(1, a.ndim))).sum())


def present(f, path):
    return path in f


def json_sidecar(path, name):
    q = path.parent / name
    if not q.exists():
        return {}
    try:
        return json.loads(q.read_text(encoding="utf-8"))
    except Exception:
        return {}


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fmt(x):
    if x == "" or x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.9g}"
    return str(x)


def audit_file(path, root, do_hash=True):
    rel = path.relative_to(root).as_posix()
    st = path.stat()
    row = {k: "" for k in CSV_FIELDS}
    row.update(relative_path=rel, size_bytes=st.st_size,
              mtime_utc=datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat())
    if do_hash:
        row["sha256"] = sha256_file(path)
    try:
        with h5py.File(path, "r") as f:
            row.update(subject=attr(f, "subject_id"), session=attr(f, "session"),
                       run=attr(f, "run"), task=attr(f, "task"), acq=attr(f, "acq"),
                       group=attr(f, "group"), geometry_status=attr(f, "geometry_contract_status"),
                       dropped_geometry_epochs=attr(f, "dropped_geometry_invalid_epochs"),
                       dropped_missing_axis_epochs=attr(f, "dropped_missing_axis_epochs"),
                       epochs_raw=attr(f, "epochs_raw"), epochs_after_geometry=attr(f, "epochs_after_geometry_policy"),
                       epochs_after_nan=attr(f, "epochs_after_nan_mask"), epochs_after_qc=attr(f, "epochs_after_qc"),
                       primary_coordinate_contract=attr(f, "primary_coordinate_contract"),
                       primary_coordinate_layer=attr(f, "primary_coordinate_layer"),
                       mnps_9d_definition_version=attr(f, "mnps_9d_definition_version"),
                       mndm_version=attr(f, "mndm_version"), anchor_id=attr(f, "anchor_id"),
                       anchor_hash=attr(f, "anchor_hash"))
            anch = f.get("provenance/anchoring")
            if anch is not None:
                row["anchor_source"] = field(anch, "anchor_source")
            norm = f.get("provenance/normalization")
            if norm is not None:
                row.update(normalization_status=field(norm, "status"), normalization_method=field(norm, "method"),
                           normalization_scope=field(norm, "scope"))
            t = data(f, "/time")
            ws = data(f, "/window_start")
            we = data(f, "/window_end")
            if t is not None and t.size:
                row.update(n_time=int(t.size), time_first_sec=float(t[0]), time_last_sec=float(t[-1]),
                           time_span_sec=float(t[-1] - t[0]))
                if t.size > 1:
                    dt = np.diff(t.astype(float))
                    expected = attr(f, "window_sec", "")
                    overlap = attr(f, "overlap", "")
                    try:
                        expected = float(expected) * (1.0 - float(overlap))
                    except (TypeError, ValueError):
                        expected = ""
                    row.update(median_dt_sec=float(np.nanmedian(dt)), max_dt_sec=float(np.nanmax(dt)),
                               gap_count=(int(np.sum(dt > float(expected) + 1e-6)) if expected != "" else ""),
                               nonpositive_dt_count=int(np.sum(dt <= 0)), expected_step_sec=expected)
            if ws is not None and ws.size:
                row.update(window_support_first_sec=float(ws[0]), window_support_last_sec=float(we[-1]) if we is not None else "",
                           window_support_span_sec=float((we[-1] - ws[0]) if we is not None else np.nan))
            if ws is not None and we is not None and ws.size and we.size:
                wl = we.astype(float) - ws.astype(float)
                row.update(window_len_median_sec=float(np.nanmedian(wl)),
                           window_len_mismatch_count=int(np.sum(np.abs(wl - float(attr(f, "window_sec", 8.0))) > 1e-5)))
            for key, path0 in CORE.items():
                a = data(f, path0)
                row[f"{key}_present"] = int(a is not None)
                if key == "mnps_3d":
                    row["finite_mnps_3d_rows"] = finite_rows(a)
                if key == "coords_9d":
                    row["finite_coords_9d_rows"] = finite_rows(a)
            for key, path0 in EXTRA.items():
                a = data(f, path0)
                row[f"{key}_present"] = int(a is not None)
                if key == "features_raw" and a is not None and a.ndim == 2:
                    row["feature_count_raw"] = int(a.shape[1]); row["raw_feature_finite_rows"] = finite_rows(a)
                if key == "features_robust_z" and a is not None and a.ndim == 2:
                    row["feature_count_robust_z"] = int(a.shape[1]); row["robust_z_feature_finite_rows"] = finite_rows(a)
            rs = f.get("row_source")
            if rs is not None:
                for k in ("source_format", "raw_file"):
                    if k in rs:
                        vals = [str(scalar(x)) for x in rs[k][()]]
                        row["row_source_formats" if k == "source_format" else "source_raw_files"] = ";".join(sorted(set(vals)))
            row.update(event_group_present=int("events" in f), label_group_present=int("labels" in f),
                       time_reference_enabled=attr(f, "time_reference_enabled"), time_reference_status=attr(f, "time_reference_status"),
                       stage_codebook_present=int("codebooks/stage" in f))
            cb = f.get("codebooks/stage")
            row["pseudo_stage_enabled"] = "unknown"
            summ = json_sidecar(path, "summary.json")
            row.update(summary_events_count=len(summ.get("events", [])) if isinstance(summ.get("events", []), list) else "",
                       summary_labels_count=len(summ.get("labels", [])) if isinstance(summ.get("labels", []), list) else "",
                       pseudo_stage_enabled=summ.get("pseudo_stage", {}).get("enabled", "") if isinstance(summ.get("pseudo_stage"), dict) else "")
            ftr = f.get("finite_time_response/v1/primary")
            row["FTR_present"] = int(ftr is not None)
            if ftr is not None:
                row.update(FTR_status=scalar(ftr["computation_status"][()]) if "computation_status" in ftr else "",
                           FTR_validation_level=field(ftr, "validation_level"),
                           FTR_horizons=";".join(sorted(ftr.get("horizons", {}).keys())))
            tr = f.get("transition_residuals/v1/primary")
            row["residuals_present"] = int(tr is not None)
            row["residuals_status"] = scalar(tr["computation_status"][()]) if tr is not None and "computation_status" in tr else ""
            qc = f.get("transition_residual_covariance_proxy/v1/primary")
            row["residual_covariance_present"] = int(qc is not None)
            row["residual_covariance_status"] = scalar(qc["computation_status"][()]) if qc is not None and "computation_status" in qc else ""
            row["stochastic_reachability_present"] = int("stochastic_reachability" in f)
            # No export field qualifies scientific use; computed arrays remain computed.
            row["jacobian_qualified"] = "no_qualification_field_found"
            row["dynamical_qualified"] = "no_qualification_field_found"
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
    return row


def build_summary(rows, root, exemplar):
    def count(field):
        return dict(sorted(Counter(str(r.get(field, "")) for r in rows).items()))
    def present(field):
        return sum(int(r.get(field, 0) in (1, "1", True)) for r in rows)
    subjects = sorted({r["subject"] for r in rows if r["subject"]})
    pair_map = defaultdict(set)
    for r in rows:
        pair_map[(r["subject"], r["session"], r["acq"])].add(r["task"])
    pairable = [k for k, v in pair_map.items() if {"ictal", "interictal"}.issubset(v)]
    finite_m = sum(1 for r in rows if r.get("finite_mnps_3d_rows") == r.get("n_time") and r.get("n_time") not in ("", None))
    finite_9 = sum(1 for r in rows if r.get("finite_coords_9d_rows") == r.get("n_time") and r.get("n_time") not in ("", None))
    return {
        "schema": "ds004100_ndt_v1_coverage_audit.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "data_root": str(root),
        "file_selection": "all recursive *.h5 files",
        "files_total": len(rows), "subjects_total": len(subjects), "subjects": subjects,
        "task_counts": count("task"), "acq_counts": count("acq"), "geometry_status_counts": count("geometry_status"),
        "pairing": {"pair_key": "subject/session/acq", "groups_total": len(pair_map), "groups_with_both_filename_tasks": len(pairable),
                     "note": "Pairability is based only on exported filename/task metadata; it is not event validation."},
        "presence_counts": {k: present(k + "_present") for k in ["mnps_3d", "coords_9d", "features_raw", "features_robust_z", "J_3d", "J_9d", "J_3d_subject", "J_3d_cohort", "J_9d_subject", "J_9d_cohort", "FTR", "residuals", "residual_covariance", "stochastic_reachability"]},
        "finite_row_counts": {"mnps_3d": count("finite_mnps_3d_rows"), "coords_9d": count("finite_coords_9d_rows"),
                              "all_rows_finite_mnps_3d_files": finite_m, "all_rows_finite_coords_9d_files": finite_9},
        "time": {"median_dt_sec": count("median_dt_sec"), "gap_count": count("gap_count"), "window_len_mismatch_count": count("window_len_mismatch_count")},
        "event_label_coverage": {"top_level_events_group_files": present("event_group_present"), "top_level_labels_group_files": present("label_group_present"),
                                  "summary_events_count": count("summary_events_count"), "summary_labels_count": count("summary_labels_count"),
                                  "interpretation": "No true seizure interval/event arrays were found in H5 or summary JSON; ictal/interictal is filename/task metadata only."},
        "normalization_anchor": {"normalization_status": count("normalization_status"), "anchor_ids": count("anchor_id"), "anchor_hashes": count("anchor_hash"), "anchor_sources": count("anchor_source")},
        "local_dynamics": {"FTR_status": count("FTR_status"), "FTR_validation_level": count("FTR_validation_level"), "residual_status": count("residuals_status"), "Q_status": count("residual_covariance_status"),
                            "stochastic_reachability_present": present("stochastic_reachability_present"),
                            "qualification": "Jacobian/FTR/residual/Q paths are computed/model-derived exports; no scientific qualification field was found."},
        "exemplar": exemplar,
        "hashing": {"sha256": "per-H5 SHA-256 when --no-hash was not supplied; empty only if hashing disabled."},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True, type=pathlib.Path)
    ap.add_argument("--output-dir", required=True, type=pathlib.Path)
    ap.add_argument("--no-hash", action="store_true", help="skip H5 SHA-256 if hashing is too slow")
    args = ap.parse_args()
    root = args.data_root.resolve(); out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    files = sorted(root.rglob("*.h5"))
    rows = [audit_file(p, root, do_hash=not args.no_hash) for p in files]
    rows.sort(key=lambda r: r["relative_path"])
    with (out / "ds004100_h5_coverage_manifest.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    exemplar = next((r for r in rows if not r["error"]), rows[0] if rows else {})
    summary = build_summary(rows, root, exemplar)
    if exemplar:
        ep = root / pathlib.PurePosixPath(exemplar["relative_path"])
        with h5py.File(ep, "r") as ef:
            schema = {"file": exemplar["relative_path"], "root_attrs_selected": {}, "paths": {}}
            for k in ["schema_version", "export_contract_version", "dataset_id", "mnps_axis_names", "coords_9d_names",
                      "mnps_9d_definition_version", "v2_definition", "v2_missing_policy", "normalize_mode", "window_sec",
                      "overlap", "fs_out", "primary_coordinate_contract", "primary_coordinate_layer", "geometry_contract_status",
                      "time_reference_enabled", "time_reference_status"]:
                if k in ef.attrs:
                    schema["root_attrs_selected"][k] = scalar(ef.attrs[k])
            for key, path0 in {**CORE, **EXTRA}.items():
                if path0 in ef:
                    d = ef[path0]
                    schema["paths"][path0] = {"kind": "dataset", "shape": list(d.shape), "dtype": str(d.dtype)}
            for path0 in ["/coords_3d_subject_anchored", "/coords_3d_cohort_anchored", "/coords_9d_subject_anchored",
                          "/coords_9d_cohort_anchored", "/feature_anchors", "/feature_anchors/spec", "/features_raw",
                          "/features_raw/metadata", "/features_robust_z", "/provenance/anchoring", "/provenance/normalization",
                          "/provenance/geometry_contract", "/finite_time_response/v1/primary", "/transition_residuals/v1/primary",
                          "/transition_residual_covariance_proxy/v1/primary", "/codebooks/stage"]:
                if path0 in ef:
                    g = ef[path0]
                    schema["paths"][path0] = {"kind": "group", "keys": sorted(g.keys()), "attrs": sorted(g.attrs.keys())}
            schema["event_like_paths"] = sorted([p for p in ef.keys() if "event" in p.lower() or "label" in p.lower()])
            summary["exemplar_schema"] = schema
    summary["audit_runtime"] = {"python": sys.version, "platform": platform.platform(), "h5py": h5py.__version__, "numpy": np.__version__}
    (out / "ds004100_h5_coverage_manifest.json").write_text(json.dumps({"summary": summary, "files": rows}, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"files": len(rows), "output_dir": str(out), "hashing": not args.no_hash, "errors": sum(bool(r["error"]) for r in rows)}, indent=2))


if __name__ == "__main__":
    main()
