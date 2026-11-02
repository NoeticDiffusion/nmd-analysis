#!/usr/bin/env python3
"""Read-only structural coverage audit for the corrected September ds004100 export.

The audit reads every recursive ``*.h5`` below ``--data-root`` and hashes the
H5 files plus direct root sidecars.  It writes only manifests and an English
report below ``--output-dir``.  It records structure, support, provenance,
status fields, shapes and finite counts.  It deliberately does not read or
write endpoint means, condition effects, contrasts, fits, or hypothesis
outcomes, and it never replaces missing values with zero.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np


FAMILIES = (
    "amplification",
    "diffusion",
    "drift",
    "one_step",
    "history",
    "turning",
    "destination",
    "resilience",
)

STATUS_FIELDS = (
    "computation_status",
    "measurement_validity",
    "support_status",
    "claim_status",
    "qualification_status",
    "claim_class",
)

CORE_ARRAYS = {
    "mnps_3d": "/mnps_3d",
    "mnps_3d_dot": "/mnps_3d_dot",
    "coords_3d_subject": "/coords_3d_subject_anchored/values",
    "coords_9d": "/coords_9d/values",
    "coords_9d_subject": "/coords_9d_subject_anchored/values",
    "J_3d": "/jacobian/J_hat",
    "J_3d_dot": "/jacobian/J_dot",
    "J_9d": "/jacobian_9D/J_hat",
    "J_9d_dot": "/jacobian_9D/J_dot",
    "J_3d_subject": "/jacobian_subject_anchored/J_hat",
    "J_3d_subject_dot": "/jacobian_subject_anchored/J_dot",
    "J_9d_subject": "/jacobian_9D_subject_anchored/J_hat",
    "J_9d_subject_dot": "/jacobian_9D_subject_anchored/J_dot",
}

FEATURE_ARRAYS = {
    "features_raw": "/features_raw/values",
    "features_robust_z": "/features_robust_z/values",
    "features_projection_z": "/features_projection_z/values",
}

PROVENANCE_KEYS = (
    "coordinate_layer",
    "coordinate_contract",
    "estimator",
    "estimand",
    "time_semantics",
    "validation_level",
    "distance_metric_id",
    "transition_support_id",
    "lag1_transition_support_id",
    "support_status",
    "qualification_status",
    "identity_relation",
    "relation",
)

CSV_FIELDS = [
    "relative_path", "sha256", "size_bytes", "mtime_utc", "subject", "session",
    "run", "task", "filename_task", "task_matches_filename", "acq", "group",
    "dataset_id", "n_time", "time_finite", "time_first_sec", "time_last_sec",
    "time_span_sec", "dt_finite", "median_dt_sec", "max_dt_sec",
    "gap_count_gt_expected", "gap_count_gt_1_5x_expected", "nonpositive_dt_count",
    "expected_step_sec", "window_support_first_sec", "window_support_last_sec",
    "window_support_span_sec", "window_len_median_sec", "window_len_mismatch_count",
    "coverage_seconds_measured", "coverage_seconds_effective", "coverage_seconds_assumed",
    "coverage_min_seconds", "coverage_min_epochs", "coverage_seconds_method",
    "epochs_raw", "epochs_after_qc", "epochs_after_nan_mask", "epochs_after_geometry",
    "geometry_contract_status", "coords_9d_all_non_finite_count", "primary_coordinate_contract",
    "primary_coordinate_layer", "feature_count_raw", "feature_count_robust_z",
    "feature_count_projection_z", "feature_finite_rows_raw", "feature_finite_rows_robust_z",
    "feature_finite_rows_projection_z", "normalization_status", "normalization_method",
    "normalization_scope", "feature_fit_status", "feature_fit_temporal_support_status",
    "feature_fit_source_quality_status", "feature_fit_population_count_min",
    "feature_fit_population_count_max", "feature_fit_population_hashes",
    "feature_fit_scopes", "row_source_formats", "source_raw_files", "events_group_present",
    "labels_group_present", "manifest_events_count", "manifest_labels_count",
    "time_reference_status", "time_reference_enabled", "stage_codebook_present",
    "representative_core_paths", "core_array_stats", "family_presence", "family_statuses",
    "family_metric_paths", "family_metric_stats", "family_provenance", "family_nested_statuses", "ftr_statuses",
    "ftr_metric_stats", "q_statuses", "q_metric_stats", "residual_statuses",
    "residual_metric_stats", "reachability_status", "reachability_metric_stats",
    "support_signature", "H1_native_n_centers", "H1_native_finite_count",
    "H1_native_supported_count", "H1_native_support_fraction", "H1_ge30",
    "H1_ge50pct", "H1_source_idx_finite_count", "H1_metric_finite_outside_source_idx",
    "H1_query_mask_path", "H1_source_idx_used_as_query_mask", "H2_native_n_centers",
    "H2_native_finite_count", "H2_native_supported_count", "H2_native_support_fraction",
    "H2_ge30", "H2_ge50pct", "H2_source_idx_finite_count",
    "H2_metric_finite_outside_source_idx", "H2_source_idx_path", "error",
]


def plain(value):
    """Convert an H5 scalar/array to JSON-safe values without losing missingness."""
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    if isinstance(value, np.bytes_):
        return bytes(value).decode("utf-8", "replace")
    if isinstance(value, np.generic):
        return plain(value.item())
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return plain(value.item())
        return [plain(x) for x in value.tolist()]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def scalar_node(node, key, default=""):
    if node is None:
        return default
    if key in node.attrs:
        return plain(node.attrs[key])
    if key in node and isinstance(node[key], h5py.Dataset) and node[key].shape == ():
        return plain(node[key][()])
    return default


def get_path(f, path):
    path = path.lstrip("/")
    return f[path] if path in f else None


def finite_stats(node):
    """Return shape and finite counts only; never return array values."""
    if node is None or not isinstance(node, h5py.Dataset):
        return None
    result = {"shape": list(node.shape), "dtype": str(node.dtype), "size": int(node.size)}
    if np.issubdtype(node.dtype, np.number):
        array = np.asarray(node[()])
        result["finite"] = int(np.isfinite(array).sum())
        if array.ndim >= 2 and array.shape[0]:
            result["finite_rows"] = int(
                np.isfinite(array).reshape(array.shape[0], -1).all(axis=1).sum()
            )
        elif array.ndim == 1:
            result["finite_rows"] = int(np.isfinite(array).sum())
    return result


def scalar_finite(node):
    if node is None or not isinstance(node, h5py.Dataset) or node.shape != ():
        return None
    if not np.issubdtype(node.dtype, np.number):
        return None
    value = node[()]
    return int(bool(np.isfinite(value)))


def first_task(text: str) -> str:
    match = re.search(r"_(ictal|interictal)_", text)
    return match.group(1) if match else ""


def series_stats(group, include_index_alignment=True):
    """Summarize numeric series leaves and their native source-index lengths."""
    if group is None:
        return {}, {}, []
    stats = {}
    paths = []
    alignments = []

    def visitor(name, node):
        if not isinstance(node, h5py.Dataset):
            return
        if "/series/" not in f"/{name}" and not name.endswith("/series"):
            return
        item = finite_stats(node)
        if item is None or not np.issubdtype(node.dtype, np.number):
            return
        rel = name.replace("\\", "/")
        paths.append(rel)
        stats[rel] = item

    group.visititems(visitor)

    if include_index_alignment:
        def align_visitor(name, node):
            if not isinstance(node, h5py.Group) or "series" not in node:
                return
            series = node["series"]
            source = series.get("source_idx")
            if source is None:
                return
            source_len = int(source.size)
            metrics = {}
            for metric_name, metric in series.items():
                if metric_name == "source_idx" or not isinstance(metric, h5py.Dataset):
                    continue
                if metric.shape and np.issubdtype(metric.dtype, np.number):
                    metrics[metric_name] = int(metric.shape[0])
            if metrics:
                alignments.append({
                    "group": name,
                    "source_idx_length": source_len,
                    "source_idx_finite": int(np.isfinite(source[()]).sum()) if np.issubdtype(source.dtype, np.number) else None,
                    "metric_first_axis_lengths": metrics,
                    "length_mismatch": any(v != source_len for v in metrics.values()),
                })
        group.visititems(align_visitor)

    return dict(sorted(stats.items())), {"paths": sorted(paths), "source_index_alignments": alignments}, alignments


def scalar_statuses(group):
    if group is None:
        return {key: "" for key in STATUS_FIELDS}
    return {key: scalar_node(group, key, "") for key in STATUS_FIELDS}


def nested_family_statuses(group):
    """Capture direct metric-variant status blocks without reading metric values."""
    if group is None:
        return {}
    result = {}

    def visit(prefix, node):
        for name, child in node.items():
            if not isinstance(child, h5py.Group):
                continue
            full_name = f"{prefix}/{name}" if prefix else name
            statuses = scalar_statuses(child)
            # Metric blocks carry computation_status. This excludes the
            # family grain/provenance containers while retaining declared-lag
            # nested variants such as one_step/v1/declared_lag_2/*.
            if "computation_status" in child:
                result[full_name] = statuses
            visit(full_name, child)

    visit("", group)
    return dict(sorted(result.items()))


def collect_selected_provenance(group):
    found = defaultdict(set)
    if group is None:
        return {}

    def visitor(name, node):
        if not isinstance(node, h5py.Dataset) or node.shape != ():
            return
        key = name.rsplit("/", 1)[-1]
        if key in PROVENANCE_KEYS:
            found[key].add(str(plain(node[()])))

    group.visititems(visitor)
    return {key: sorted(values) for key, values in sorted(found.items())}


def all_scalar_metric_finiteness(group):
    """Record finite flags for numeric scalar metrics but never scalar values."""
    out = {}
    if group is None:
        return out

    def visitor(name, node):
        if not isinstance(node, h5py.Dataset) or node.shape != ():
            return
        if not np.issubdtype(node.dtype, np.number):
            return
        out[name] = scalar_finite(node)

    group.visititems(visitor)
    return dict(sorted(out.items()))


def parse_manifest(f):
    events = labels = ""
    node = get_path(f, "/manifest_json")
    if node is None or node.shape != ():
        return events, labels
    try:
        manifest = json.loads(str(plain(node[()])))
    except Exception:
        return events, labels
    if isinstance(manifest, dict):
        if isinstance(manifest.get("events"), list):
            events = len(manifest["events"])
        if isinstance(manifest.get("labels"), list):
            labels = len(manifest["labels"])
    return events, labels


def native_endpoint_support(f, metric_path, support_path=None, source_idx_path=None, support_threshold=0):
    """Count native-grid finite and supported centers without using source_idx as a query mask."""
    metric = get_path(f, metric_path)
    if metric is None or not isinstance(metric, h5py.Dataset) or metric.ndim == 0:
        return {
            "n_centers": "", "finite_count": "", "supported_count": "", "support_fraction": "",
            "ge30": False, "ge50pct": False, "source_idx_finite_count": "",
            "metric_finite_outside_source_idx": "", "query_mask_path": support_path or "",
            "source_idx_used_as_query_mask": False, "source_idx_path": source_idx_path or "",
        }
    values = np.asarray(metric[()])
    n_centers = int(values.shape[0])
    finite = np.isfinite(values.reshape(n_centers, -1)).all(axis=1)
    source_idx_finite_count = ""
    outside_source_idx = ""
    source_positions = None
    if source_idx_path:
        source = get_path(f, source_idx_path)
        if source is not None:
            indices = np.asarray(source[()]).reshape(-1)
            source_idx_finite_count = int(np.isfinite(indices).sum()) if np.issubdtype(indices.dtype, np.number) else ""
            if np.issubdtype(indices.dtype, np.number):
                valid_indices = indices[np.isfinite(indices)].astype(int)
                source_positions = set(int(i) for i in valid_indices if 0 <= int(i) < n_centers)
                outside_source_idx = int(np.sum(finite & ~np.array([i in source_positions for i in range(n_centers)])))
    support = np.ones(n_centers, dtype=bool)
    if support_path:
        support_node = get_path(f, support_path)
        if support_node is not None:
            support_values = np.asarray(support_node[()]).reshape(-1)
            if support_values.size == n_centers:
                if np.issubdtype(support_values.dtype, np.bool_) or np.issubdtype(support_values.dtype, np.number):
                    support = np.isfinite(support_values) & (support_values > support_threshold)
    supported = finite & support
    fraction = float(supported.sum() / n_centers) if n_centers else ""
    return {
        "n_centers": n_centers,
        "finite_count": int(finite.sum()),
        "supported_count": int(supported.sum()),
        "support_fraction": fraction,
        "ge30": bool(supported.sum() >= 30),
        "ge50pct": bool(fraction >= 0.5) if n_centers else False,
        "source_idx_finite_count": source_idx_finite_count,
        "metric_finite_outside_source_idx": outside_source_idx,
        "query_mask_path": support_path or "",
        "source_idx_used_as_query_mask": False,
        "source_idx_path": source_idx_path or "",
    }


def sidecar_names(root: Path):
    return sorted(
        p for p in root.iterdir()
        if p.is_file() and p.suffix.lower() in {".json", ".yaml", ".yml", ".txt"}
    )


def support_signature(f):
    base = get_path(f, "/support_signature/v1")
    if base is None:
        return {}
    result = {}
    for key in (
        "schema_version", "modality", "capability/chart_3d", "capability/chart_9d",
        "capability/destination", "capability/diffusion", "capability/mnj_3d",
        "capability/mnj_9d", "capability/resilience", "capability/spread",
    ):
        result[key.replace("/", "_")] = scalar_node(base, key.split("/")[-1], "") if "/" not in key else ""
        node = get_path(f, f"/support_signature/v1/{key}")
        if isinstance(node, h5py.Dataset) and node.shape == ():
            result[key.replace("/", "_")] = plain(node[()])
    for coordinate in ("m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m"):
        for field in ("source", "fallback_feature", "semantic_equivalence"):
            node = get_path(f, f"/support_signature/v1/coordinates/{coordinate}/{field}")
            if isinstance(node, h5py.Dataset) and node.shape == ():
                result[f"{coordinate}_{field}"] = plain(node[()])
    for axis in ("m", "d", "e"):
        node = get_path(f, f"/support_signature/v1/axes_3d/{axis}/source")
        if isinstance(node, h5py.Dataset) and node.shape == ():
            result[f"axis_{axis}_source"] = plain(node[()])
    return dict(sorted(result.items()))


def audit_one(path: Path, root: Path, do_hash=True):
    row = {key: "" for key in CSV_FIELDS}
    row["relative_path"] = path.relative_to(root).as_posix()
    stat = path.stat()
    row["size_bytes"] = int(stat.st_size)
    row["mtime_utc"] = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
    if do_hash:
        row["sha256"] = sha256_file(path)

    try:
        with h5py.File(path, "r") as f:
            subject = str(scalar_node(f, "subject", ""))
            if not subject:
                match = re.search(r"(sub-[^_]+)", path.name)
                subject = match.group(1) if match else ""
            task = str(scalar_node(f, "task", ""))
            filename_task = first_task(path.name)
            row.update({
                "subject": subject,
                "session": scalar_node(f, "session", ""),
                "run": scalar_node(f, "run", ""),
                "task": task,
                "filename_task": filename_task,
                "task_matches_filename": bool(task and filename_task and task == filename_task),
                "acq": scalar_node(f, "acq", ""),
                "group": scalar_node(f, "group", ""),
                "dataset_id": scalar_node(f, "dataset_id", ""),
                "epochs_raw": scalar_node(f, "epochs_raw", ""),
                "epochs_after_qc": scalar_node(f, "epochs_after_qc", ""),
                "epochs_after_nan_mask": scalar_node(f, "epochs_after_nan_mask", ""),
                "epochs_after_geometry": scalar_node(f, "epochs_after_geometry_policy", ""),
                "geometry_contract_status": scalar_node(f, "geometry_contract_status", ""),
                "coords_9d_all_non_finite_count": scalar_node(f, "coords_9d_all_non_finite_count", ""),
                "primary_coordinate_contract": scalar_node(f, "primary_coordinate_contract", ""),
                "primary_coordinate_layer": scalar_node(f, "primary_coordinate_layer", ""),
                "time_reference_status": scalar_node(f, "time_reference_status", ""),
                "time_reference_enabled": scalar_node(f, "time_reference_enabled", ""),
                "stage_codebook_present": int("codebooks/stage" in f),
                "events_group_present": int("events" in f),
                "labels_group_present": int("labels" in f),
            })
            manifest_events, manifest_labels = parse_manifest(f)
            row["manifest_events_count"] = manifest_events
            row["manifest_labels_count"] = manifest_labels

            time = get_path(f, "/time")
            if time is not None:
                t = np.asarray(time[()], dtype=float)
                finite_t = np.isfinite(t)
                row.update(n_time=int(t.size), time_finite=int(finite_t.sum()))
                if t.size and finite_t.all():
                    row.update(time_first_sec=float(t[0]), time_last_sec=float(t[-1]), time_span_sec=float(t[-1] - t[0]))
                if t.size > 1:
                    dt = np.diff(t)
                    finite_dt = np.isfinite(dt)
                    row["dt_finite"] = int(finite_dt.sum())
                    if finite_dt.any():
                        valid_dt = dt[finite_dt]
                        row["median_dt_sec"] = float(np.median(valid_dt))
                        row["max_dt_sec"] = float(np.max(valid_dt))
                        row["nonpositive_dt_count"] = int(np.sum(valid_dt <= 0))
                        window_sec = scalar_node(f, "window_sec", "")
                        overlap = scalar_node(f, "overlap", "")
                        try:
                            expected = float(window_sec) * (1.0 - float(overlap))
                        except (TypeError, ValueError):
                            expected = float(np.median(valid_dt))
                        row["expected_step_sec"] = expected
                        row["gap_count_gt_expected"] = int(np.sum(valid_dt > expected + 1e-6))
                        row["gap_count_gt_1_5x_expected"] = int(np.sum(valid_dt > 1.5 * expected + 1e-6))

            ws = get_path(f, "/window_start")
            we = get_path(f, "/window_end")
            if ws is not None and we is not None:
                starts = np.asarray(ws[()], dtype=float)
                ends = np.asarray(we[()], dtype=float)
                if starts.size and ends.size:
                    row.update(
                        window_support_first_sec=float(starts[0]),
                        window_support_last_sec=float(ends[-1]),
                        window_support_span_sec=float(ends[-1] - starts[0]),
                    )
                    lengths = ends - starts
                    row["window_len_median_sec"] = float(np.median(lengths))
                    configured = scalar_node(f, "window_sec", "")
                    try:
                        row["window_len_mismatch_count"] = int(np.sum(np.abs(lengths - float(configured)) > 1e-5))
                    except (TypeError, ValueError):
                        row["window_len_mismatch_count"] = ""

            for name, attr_name in (
                ("coverage_seconds_measured", "coverage_seconds_measured"),
                ("coverage_seconds_effective", "coverage_seconds_effective"),
                ("coverage_seconds_assumed", "coverage_seconds_assumed"),
                ("coverage_min_seconds", "coverage_min_seconds_effective"),
                ("coverage_min_epochs", "coverage_min_epochs_effective"),
                ("coverage_seconds_method", "coverage_seconds_method"),
            ):
                row[name] = scalar_node(f, attr_name, "")

            core_stats = {}
            core_paths = []
            for name, h5_path in CORE_ARRAYS.items():
                node = get_path(f, h5_path)
                item = finite_stats(node)
                if item is not None:
                    core_paths.append(h5_path)
                    core_stats[name] = item
            row["representative_core_paths"] = compact(core_paths)
            row["core_array_stats"] = compact(core_stats)

            feature_counts = {}
            for name, h5_path in FEATURE_ARRAYS.items():
                node = get_path(f, h5_path)
                item = finite_stats(node)
                if item is None:
                    continue
                feature_counts[name] = item
                row[f"feature_count_{name.removeprefix('features_')}"] = item["shape"][1] if len(item["shape"]) > 1 else ""
                row[f"feature_finite_rows_{name.removeprefix('features_')}"] = item.get("finite_rows", "")

            normalization = get_path(f, "/provenance/normalization")
            row.update(
                normalization_status=scalar_node(normalization, "status", ""),
                normalization_method=scalar_node(normalization, "method", ""),
                normalization_scope=scalar_node(normalization, "scope", ""),
            )

            signal_support = get_path(f, "/provenance/signal_support_provenance")
            fit_counts, fit_hashes, fit_scopes = [], set(), set()
            fit_status = scalar_node(signal_support, "status", "")
            temporal_status = scalar_node(signal_support, "temporal_support_status", "")
            source_quality_status = scalar_node(signal_support, "source_quality_status", "")
            if signal_support is not None:
                def fit_visitor(name, node):
                    if not isinstance(node, h5py.Dataset) or node.shape != ():
                        return
                    leaf = name.rsplit("/", 1)[-1]
                    value = plain(node[()])
                    if leaf == "fit_population_count" and isinstance(value, (int, float)):
                        fit_counts.append(int(value))
                    elif leaf == "fit_population_hash":
                        fit_hashes.add(str(value))
                    elif leaf == "fit_scope":
                        fit_scopes.add(str(value))
                signal_support.visititems(fit_visitor)
            row.update(
                feature_fit_status=fit_status,
                feature_fit_temporal_support_status=temporal_status,
                feature_fit_source_quality_status=source_quality_status,
                feature_fit_population_count_min=min(fit_counts) if fit_counts else "",
                feature_fit_population_count_max=max(fit_counts) if fit_counts else "",
                feature_fit_population_hashes=compact(sorted(fit_hashes)),
                feature_fit_scopes=compact(sorted(fit_scopes)),
            )

            row_source = get_path(f, "/row_source")
            if row_source is not None:
                for key, out_key in (("source_format", "row_source_formats"), ("raw_file", "source_raw_files")):
                    node = row_source.get(key)
                    if node is not None:
                        values = sorted({str(plain(value)) for value in node[()]})
                        row[out_key] = ";".join(values)

            family_presence, family_statuses, family_paths, family_stats, family_prov, family_nested = {}, {}, {}, {}, {}, {}
            families = get_path(f, "/dynamical_families")
            for family in FAMILIES:
                group = get_path(f, f"/dynamical_families/{family}/v1")
                family_presence[family] = int(group is not None)
                family_statuses[family] = scalar_statuses(group)
                family_paths[family] = []
                family_stats[family] = {}
                family_prov[family] = collect_selected_provenance(get_path(f, f"/dynamical_families/{family}/v1/provenance"))
                family_nested[family] = nested_family_statuses(group)
                if group is not None:
                    stats, path_meta, _ = series_stats(group)
                    family_paths[family] = path_meta
                    family_stats[family] = stats
            row["family_presence"] = compact(family_presence)
            row["family_statuses"] = compact(family_statuses)
            row["family_metric_paths"] = compact(family_paths)
            row["family_metric_stats"] = compact(family_stats)
            row["family_provenance"] = compact(family_prov)
            row["family_nested_statuses"] = compact(family_nested)

            ftr_statuses, ftr_stats = {}, {}
            for variant in ("primary", "stratified_9d"):
                group = get_path(f, f"/finite_time_response/v1/{variant}")
                ftr_statuses[variant] = scalar_statuses(group)
                if group is not None:
                    stats, _, _ = series_stats(group, include_index_alignment=False)
                    ftr_stats[variant] = stats
            row["ftr_statuses"] = compact(ftr_statuses)
            row["ftr_metric_stats"] = compact(ftr_stats)

            q_statuses, q_stats = {}, {}
            for variant in ("primary", "stratified_9d"):
                group = get_path(f, f"/transition_residual_covariance_proxy/v1/{variant}")
                q_statuses[variant] = scalar_statuses(group)
                if group is not None:
                    stats = {}
                    for name in ("covariance", "residual_mean"):
                        item = finite_stats(group.get(name))
                        if item is not None:
                            stats[name] = item
                    q_stats[variant] = stats
            row["q_statuses"] = compact(q_statuses)
            row["q_metric_stats"] = compact(q_stats)

            residual_statuses, residual_stats = {}, {}
            for variant in ("primary", "stratified_9d"):
                group = get_path(f, f"/transition_residuals/v1/{variant}")
                residual_statuses[variant] = scalar_statuses(group)
                if group is not None:
                    stats, _, _ = series_stats(group, include_index_alignment=False)
                    residual_stats[variant] = stats
            row["residual_statuses"] = compact(residual_statuses)
            row["residual_metric_stats"] = compact(residual_stats)

            reach_group = get_path(f, "/stochastic_reachability/v1/primary")
            row["reachability_status"] = compact(scalar_statuses(reach_group))
            row["reachability_metric_stats"] = compact({
                "series": series_stats(reach_group, include_index_alignment=False)[0] if reach_group is not None else {},
                "numeric_scalar_finite": all_scalar_metric_finiteness(reach_group),
            })
            row["support_signature"] = compact(support_signature(f))

            # Preregistration support gates: H1 is a native T-grid diffusion
            # endpoint with its explicit valid mask. The diffusion source_idx
            # is retained as a training increment pool diagnostic and is never
            # used as the H1 query mask. H2 is a native T-grid neighbour-gain
            # endpoint supported by its neighbour-count threshold; source_idx
            # is checked separately for out-of-index values and never zipped.
            h1 = native_endpoint_support(
                f,
                "/dynamical_families/diffusion/v1/series/diffusion_effective_dimension",
                support_path="/dynamical_families/diffusion/v1/series/valid",
                source_idx_path="/dynamical_families/diffusion/v1/series/source_idx",
                support_threshold=0,
            )
            h2 = native_endpoint_support(
                f,
                "/dynamical_families/amplification/v1/series/neighbor_gain_q90",
                support_path="/dynamical_families/amplification/v1/series/n_neighbor_pairs",
                source_idx_path="/dynamical_families/amplification/v1/series/source_idx",
                support_threshold=0,
            )
            for prefix, info in (("H1", h1), ("H2", h2)):
                row[f"{prefix}_native_n_centers"] = info["n_centers"]
                row[f"{prefix}_native_finite_count"] = info["finite_count"]
                row[f"{prefix}_native_supported_count"] = info["supported_count"]
                row[f"{prefix}_native_support_fraction"] = info["support_fraction"]
                row[f"{prefix}_ge30"] = info["ge30"]
                row[f"{prefix}_ge50pct"] = info["ge50pct"]
                row[f"{prefix}_source_idx_finite_count"] = info["source_idx_finite_count"]
                row[f"{prefix}_metric_finite_outside_source_idx"] = info["metric_finite_outside_source_idx"]
            row["H1_query_mask_path"] = h1["query_mask_path"]
            row["H1_source_idx_used_as_query_mask"] = h1["source_idx_used_as_query_mask"]
            row["H2_source_idx_path"] = h2["source_idx_path"]

    except Exception as exc:  # retain the row so one malformed file is visible
        row["error"] = f"{type(exc).__name__}: {exc}"
    return row


def parse_json_cell(row, key, default=None):
    try:
        return json.loads(row.get(key, ""))
    except Exception:
        return default


def count_field(rows, field):
    return dict(sorted(Counter(str(row.get(field, "")) for row in rows).items()))


def aggregate(rows, root, sidecars, exemplar):
    by_subject = defaultdict(Counter)
    by_subject_session_acq = defaultdict(Counter)
    for row in rows:
        by_subject[str(row.get("subject", ""))][str(row.get("task", ""))] += 1
        key = "|".join(str(row.get(k, "")) for k in ("subject", "session", "acq"))
        by_subject_session_acq[key][str(row.get("task", ""))] += 1

    family_summary = {}
    for family in FAMILIES:
        statuses = []
        presence = 0
        metric_path_counts = Counter()
        stats_presence = Counter()
        for row in rows:
            pres = parse_json_cell(row, "family_presence", {}) or {}
            status = parse_json_cell(row, "family_statuses", {}) or {}
            paths = parse_json_cell(row, "family_metric_paths", {}) or {}
            stats = parse_json_cell(row, "family_metric_stats", {}) or {}
            presence += int(bool(pres.get(family, 0)))
            statuses.append(status.get(family, {}))
            for path in (paths.get(family, {}) or {}).get("paths", []):
                metric_path_counts[path] += 1
            for path in (stats.get(family, {}) or {}):
                stats_presence[path] += 1
        family_summary[family] = {
            "present_files": presence,
            "status_counts": {field: dict(sorted(Counter(str(s.get(field, "")) for s in statuses).items())) for field in STATUS_FIELDS},
            "representative_metric_path_counts": dict(sorted(metric_path_counts.items())),
            "metric_stats_path_counts": dict(sorted(stats_presence.items())),
        }

    nested_family_summary = {}
    for family in FAMILIES:
        children = defaultdict(lambda: defaultdict(Counter))
        child_presence = Counter()
        for row in rows:
            nested = parse_json_cell(row, "family_nested_statuses", {}) or {}
            for child, statuses in (nested.get(family, {}) or {}).items():
                child_presence[child] += 1
                for field in STATUS_FIELDS:
                    children[child][field][str((statuses or {}).get(field, ""))] += 1
        nested_family_summary[family] = {
            child: {
                "present_files": int(child_presence[child]),
                "status_counts": {field: dict(sorted(counter.items())) for field, counter in fields.items()},
            }
            for child, fields in sorted(children.items())
        }

    def presence_count(field):
        return sum(1 for row in rows if parse_json_cell(row, field, {}) is not None and parse_json_cell(row, field, {}) != {})

    support_signatures = Counter(row.get("support_signature", "") for row in rows)
    core_presence = Counter()
    for row in rows:
        stats = parse_json_cell(row, "core_array_stats", {}) or {}
        for name in stats:
            core_presence[name] += 1

    sidecar_hashes = {}
    for path in sidecars:
        sidecar_hashes[path.name] = {
            "bytes": int(path.stat().st_size),
            "sha256": sha256_file(path),
        }

    native_support = {}
    for prefix in ("H1", "H2"):
        native_support[prefix] = {
            "files_ge30": sum(bool(row.get(f"{prefix}_ge30")) for row in rows),
            "files_ge50pct": sum(bool(row.get(f"{prefix}_ge50pct")) for row in rows),
            "files_ge30_and_ge50pct": sum(bool(row.get(f"{prefix}_ge30")) and bool(row.get(f"{prefix}_ge50pct")) for row in rows),
            "native_n_centers_counts": count_field(rows, f"{prefix}_native_n_centers"),
            "native_finite_count_counts": count_field(rows, f"{prefix}_native_finite_count"),
            "native_supported_count_counts": count_field(rows, f"{prefix}_native_supported_count"),
            "source_idx_finite_count_counts": count_field(rows, f"{prefix}_source_idx_finite_count"),
            "metric_finite_outside_source_idx_counts": count_field(rows, f"{prefix}_metric_finite_outside_source_idx"),
        }
        # Pairability eligible on the same task-labelled subject: each task
        # must have at least one file passing both support gates.
        eligible_by_subject = defaultdict(Counter)
        for row in rows:
            if bool(row.get(f"{prefix}_ge30")) and bool(row.get(f"{prefix}_ge50pct")):
                eligible_by_subject[str(row.get("subject", ""))][str(row.get("task", ""))] += 1
        native_support[prefix]["paired_subjects_with_eligible_files"] = sum(
            counts.get("ictal", 0) > 0 and counts.get("interictal", 0) > 0
            for counts in eligible_by_subject.values()
        )
        native_support[prefix]["eligible_subject_task_counts"] = {
            subject: dict(sorted(counts.items())) for subject, counts in sorted(eligible_by_subject.items())
        }

    return {
        "audit_scope": "All recursive H5 files in the corrected September export; structural metadata, time/gap support, coordinate/J/Jdot finite counts, family paths and statuses, FTR/Q/reachability finite counts, support signatures, labels/events versus filename task, and provenance. No endpoint means, effects, contrasts, fits, or biological validity claims.",
        "root": str(root),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "runtime": {"python": platform.python_version(), "h5py": h5py.__version__, "numpy": np.__version__},
        "script_sha256": sha256_file(Path(__file__)),
        "files_found": len(rows),
        "files_read": sum(1 for row in rows if not row.get("error")),
        "files_with_errors": [row["relative_path"] for row in rows if row.get("error")],
        "bytes": sum(int(row.get("size_bytes", 0) or 0) for row in rows),
        "subjects": len(by_subject),
        "task_file_counts": count_field(rows, "task"),
        "filename_task_counts": count_field(rows, "filename_task"),
        "task_filename_match_counts": count_field(rows, "task_matches_filename"),
        "acquisition_counts": count_field(rows, "acq"),
        "group_counts": count_field(rows, "group"),
        "subject_file_counts": {key: dict(sorted(value.items())) for key, value in sorted(by_subject.items())},
        "paired_subjects": sum(c.get("ictal", 0) > 0 and c.get("interictal", 0) > 0 for c in by_subject.values()),
        "paired_subject_session_acq": sum(c.get("ictal", 0) > 0 and c.get("interictal", 0) > 0 for c in by_subject_session_acq.values()),
        "subject_session_acq_keys": len(by_subject_session_acq),
        "time": {
            "n_time_range": [min(int(row.get("n_time", 0) or 0) for row in rows), max(int(row.get("n_time", 0) or 0) for row in rows)],
            "gap_count_gt_expected": count_field(rows, "gap_count_gt_expected"),
            "gap_count_gt_1_5x_expected": count_field(rows, "gap_count_gt_1_5x_expected"),
            "nonpositive_dt_count": count_field(rows, "nonpositive_dt_count"),
            "time_reference_status": count_field(rows, "time_reference_status"),
        },
        "core_array_presence": dict(sorted(core_presence.items())),
        "family_summary": family_summary,
        "nested_family_summary": nested_family_summary,
        "ftr_status_counts": {
            variant: {field: dict(sorted(Counter(str((parse_json_cell(row, "ftr_statuses", {}) or {}).get(variant, {}).get(field, "")) for row in rows).items())) for field in STATUS_FIELDS}
            for variant in ("primary", "stratified_9d")
        },
        "q_status_counts": {
            variant: {field: dict(sorted(Counter(str((parse_json_cell(row, "q_statuses", {}) or {}).get(variant, {}).get(field, "")) for row in rows).items())) for field in STATUS_FIELDS}
            for variant in ("primary", "stratified_9d")
        },
        "residual_status_counts": {
            variant: {field: dict(sorted(Counter(str((parse_json_cell(row, "residual_statuses", {}) or {}).get(variant, {}).get(field, "")) for row in rows).items())) for field in STATUS_FIELDS}
            for variant in ("primary", "stratified_9d")
        },
        "reachability_status_counts": {field: dict(sorted(Counter(str((parse_json_cell(row, "reachability_status", {}) or {}).get(field, "")) for row in rows).items())) for field in STATUS_FIELDS},
        "support_signature_counts": {signature: count for signature, count in sorted(support_signatures.items())},
        "normalization_status_counts": count_field(rows, "normalization_status"),
        "feature_fit_temporal_support_counts": count_field(rows, "feature_fit_temporal_support_status"),
        "feature_fit_source_quality_counts": count_field(rows, "feature_fit_source_quality_status"),
        "events_group_files": sum(int(row.get("events_group_present", 0) or 0) for row in rows),
        "labels_group_files": sum(int(row.get("labels_group_present", 0) or 0) for row in rows),
        "manifest_event_count_counts": count_field(rows, "manifest_events_count"),
        "manifest_label_count_counts": count_field(rows, "manifest_labels_count"),
        "all_file_label_task_mismatches": [row["relative_path"] for row in rows if row.get("task_matches_filename") is False],
        "native_support_gates": native_support,
        "root_sidecars": sidecar_hashes,
        "exemplar_relative_path": exemplar.get("relative_path", ""),
        "limitations": [
            "Filename and H5 task are export labels; empty events/labels do not verify seizure onset, offset, or event-locked windows.",
            "Temporal support provenance records unknown effective filter support when epoch bounds are not certified; source quality is not recorded.",
            "Computed status, finite arrays, or support_status are not scientific measurement validity or biological qualification.",
            "Mixed acq-seeg and acq-ecog exports retain no channel-level comparability proof in this audit.",
            "Metric series and native source_idx arrays are summarized separately; no positional zip is assumed when lengths differ.",
        ],
    }


def write_csv(rows, path):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") if not isinstance(row.get(key, ""), (dict, list)) else compact(row[key]) for key in CSV_FIELDS})


def write_report(summary, rows, output_path):
    first = rows[0] if rows else {}
    families = summary["family_summary"]
    def family_line(name):
        item = families[name]
        comp = item["status_counts"]["computation_status"]
        support = item["status_counts"]["support_status"]
        valid = item["status_counts"]["measurement_validity"]
        claim = item["status_counts"]["claim_status"]
        return f"- **{name}**: present in {item['present_files']}/{summary['files_found']}; computation `{compact(comp)}`; support `{compact(support)}`; measurement validity `{compact(valid)}`; claim `{compact(claim)}`."

    nested_lines = []
    for family in FAMILIES:
        for child, item in summary.get("nested_family_summary", {}).get(family, {}).items():
            comp = item["status_counts"].get("computation_status", {})
            support = item["status_counts"].get("support_status", {})
            validity = item["status_counts"].get("measurement_validity", {})
            missing = summary["files_found"] - int(item.get("present_files", 0))
            # Keep the report compact while preserving every nontrivial nested
            # status and all presence deficits for lag/variant paths.
            if missing or len(comp) > 1 or any(key not in {"computed", ""} for key in comp):
                nested_lines.append(
                    f"- `{family}/{child}` present {item.get('present_files', 0)}/{summary['files_found']}"
                    + (f" (absent {missing})" if missing else "")
                    + f"; computation `{compact(comp)}`; support `{compact(support)}`; validity `{compact(validity)}`."
                )
    if not nested_lines:
        nested_lines.append("- No nested metric status deviations were found.")

    gate_lines = []
    for endpoint, gate in summary.get("native_support_gates", {}).items():
        gate_lines.append(f"- **{endpoint}**: {gate['files_ge30_and_ge50pct']}/{summary['files_found']} files meet >=30 centers and >=50% support; {gate['paired_subjects_with_eligible_files']} structurally paired subjects.")

    report = f"""# ds004100 NDT v1.0 September coverage report

Audit date: {summary['created_utc']}. The audited export is exactly
`{summary['root']}`. This is the corrected September export; no August export
was read. The audit is read-only and covers all recursive `*.h5` files.

## Reproduction and scope

```powershell
& J:\\repos\\nmd-analysis\\.venv\\Scripts\\python.exe `
  J:\\repos\\nmd-analysis\\articles\\ds004100_ndt_v.1.0\\coverage_september\\audit_ds004100_september_coverage.py `
  --data-root {summary['root']} `
  --output-dir J:\\repos\\nmd-analysis\\articles\\ds004100_ndt_v.1.0\\coverage_september
```

Outputs are the reproducible [audit script](audit_ds004100_september_coverage.py),
the [per-file CSV manifest](ds004100_h5_manifest_september.csv), and the
[JSON manifest](ds004100_h5_manifest_september.json). The JSON and CSV record
shapes, finite counts, status fields, support signatures, and provenance. They
do not record endpoint means/effects, condition contrasts, or new fits.

## Inventory, labels, and pairability

The all-file audit read **{summary['files_read']}** of **{summary['files_found']}**
H5 files ({summary['bytes']:,} bytes) from **{summary['subjects']}** subjects.
H5 task counts are `{compact(summary['task_file_counts'])}` and filename task
counts are `{compact(summary['filename_task_counts'])}`; task/filename matches
are `{compact(summary['task_filename_match_counts'])}`. There are
{summary['paired_subjects']} task-paired subjects and
{summary['paired_subject_session_acq']} task-paired subject/session/acquisition
keys. These are export-label pairability counts, not evidence of true seizure
intervals.

The first lexicographic exemplar is `{summary['exemplar_relative_path']}`.
Its selected metadata are shown here only to distinguish exemplar inspection
from all-file counts: subject `{first.get('subject','')}`, task
`{first.get('task','')}`, `{first.get('n_time','')} time rows`, coverage
`{first.get('coverage_seconds_effective','')} effective seconds`, geometry
`{first.get('geometry_contract_status','')}`, and coordinate contract
`{first.get('primary_coordinate_contract','')}`. The complete per-file record
is in the manifests.

## Time, windows, coordinates, and finite support

Per-file `n_time` ranges from {summary['time']['n_time_range'][0]} to
{summary['time']['n_time_range'][1]}. Gap count distributions for the expected
step and the FTR 1.5x hard-break rule are recorded in the JSON manifest; the
audit found `{compact(summary['time']['nonpositive_dt_count'])}` non-positive-step
counts. Window and coverage support are recorded per file without inferring
seizure onset/offset intervals.

Core-array presence counts are `{compact(summary['core_array_presence'])}`.
Finite counts are per array and per file; no missing value is converted to
zero. The canonical MNPS and 9D coordinate definitions remain structural
exports, and their finite rows do not establish biological validity.

## Features and provenance

Normalization status is `{compact(summary['normalization_status_counts'])}`.
Feature-fit temporal support status is
`{compact(summary['feature_fit_temporal_support_counts'])}` and source-quality
status is `{compact(summary['feature_fit_source_quality_counts'])}`. The H5
records local input-frame fit populations, hashes, scopes, chart coordinate
layers, distance metric identifiers, and family estimator/time semantics; the
manifest retains these provenance strings without exposing numerical endpoint
values. The mixed `{compact(summary['acquisition_counts'])}` acquisitions do not
carry a channel-level comparability certificate in this audit.

## Events and labels

Top-level events groups occur in {summary['events_group_files']}/{summary['files_found']}
files and labels groups in {summary['labels_group_files']}/{summary['files_found']}.
Manifest event-count distribution is `{compact(summary['manifest_event_count_counts'])}`
and label-count distribution is `{compact(summary['manifest_label_count_counts'])}`.
The exported ictal/interictal task is therefore filename/H5 metadata here; a
true event-locked interval is not established. Absence of H5 `events`/`labels`
groups does not imply that source-side annotation files are absent; external
source metadata and alignment are a separate audit boundary. The coordinator's
[source-sidecar audit](../source_metadata/README.md) found all 208 ictal event
TSV files in the accessible K: source; nominal annotation containment is not
proof of filter support or event-pure estimator neighborhoods.

## Dynamical families and qualification status

Every family row keeps computation, measurement-validity, support, claim, and
qualification fields separate. All-file family summaries are:

{chr(10).join(family_line(name) for name in FAMILIES)}

Nested metric-variant status counts (including absent variants) are:

{chr(10).join(nested_lines)}

Metric paths and finite counts are listed without aggregating or contrasting
their values. Native metric series and `source_idx` support indices are kept as
separate arrays; any length mismatch is an audit finding rather than a reason
to zip them positionally. Computed outputs and `support_status` are not
upgraded to qualified biological measurements.

## Native support gates used by the preregistration

The audit also records the two preregistered native-grid support gates without
calculating endpoint means or effects. H1 is the diffusion
`diffusion_effective_dimension` series on the native T grid. Its explicit
`valid` mask defines supported centers; the diffusion `source_idx` is retained
as a training increment-pool diagnostic and is explicitly not used as the H1
query mask. H2 is the amplification `neighbor_gain_q90` series on the native T
grid; its neighbour-count support is checked separately from its `source_idx`.
Neither series is positionally zipped to `source_idx`.

The per-file H1/H2 finite counts, supported counts, fractions, `>=30` and
`>=50%` flags, source-index finite counts, and finite metric values outside the
source-index set are in both manifests. Aggregate gate counts are:

{chr(10).join(gate_lines)}

These are structural eligibility
records only; they do not establish event purity, temporal filter support,
measurement validity, or a biological claim.

Finite-time response, transition-residual covariance (Q), transition residuals,
and stochastic reachability status/finite-count records are included when
present. The Q and reachability rows retain only structural finite counts and
support metadata. No means, effects, or condition comparisons are produced.

## Verdict and limitations

**PARTIAL PASS — structural coverage is reproducible for all {summary['files_found']}
September H5 files.** The export supports complete inventory, task-pairability
counts, observed time/window support, canonical coordinate/J finite accounting,
family schema/status enumeration, support-signature enumeration, and provenance
hashes. It does not establish event-locked seizure intervals, channel
comparability, filter temporal support, scientific measurement validity, or
biological qualification. Scientific contrasts remain outside this audit.

Root sidecars are hashed in the JSON manifest. The script records its own hash
as `{summary['script_sha256']}`.
"""
    output_path.write_text(report, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", "--root", dest="data_root", type=Path, required=True)
    parser.add_argument("--output-dir", "--out", dest="output_dir", type=Path, required=True)
    parser.add_argument("--no-hash", action="store_true", help="Skip H5 SHA-256 hashing for a quick dry run.")
    args = parser.parse_args()
    root = args.data_root.resolve()
    output_dir = args.output_dir.resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(root)
    if output_dir == root or root in output_dir.parents:
        raise ValueError("Audit output must be outside the source-data root")
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = sorted(root.rglob("*.h5"))
    if not paths:
        raise RuntimeError(f"No H5 files found below {root}")
    rows = [audit_one(path, root, do_hash=not args.no_hash) for path in paths]
    sidecars = sidecar_names(root)
    exemplar = rows[0]
    summary = aggregate(rows, root, sidecars, exemplar)

    write_csv(rows, output_dir / "ds004100_h5_manifest_september.csv")
    manifest = {"summary": summary, "rows": rows}
    (output_dir / "ds004100_h5_manifest_september.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    write_report(summary, rows, output_dir / "coverage_report_september.md")
    print(json.dumps({key: summary[key] for key in ("files_found", "files_read", "subjects", "paired_subjects", "paired_subject_session_acq", "files_with_errors")}, default=str))
    if summary["files_with_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
