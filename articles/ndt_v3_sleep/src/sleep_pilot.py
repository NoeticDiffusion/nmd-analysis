"""Bounded, descriptive pilot audit for one verified NMD v3 sleep H5."""

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
from typing import Any

import h5py
import numpy as np
import yaml

from nmd_analysis.dynamical_families.readers import family_availability, read_family
from nmd_analysis.dynamical_families.adapters import diffusion_window_rows, family_recording_rows
from nmd_analysis.h5_contract import resolve_coords_3d, resolve_coords_9d
from nmd_analysis.pipeline import run_dataset_pipeline
from nmd_analysis.v3_audit import write_audit


SOURCE_LEAF_NAME = "sub-99_Sleep_acq-psg.h5"
FAMILIES = ("diffusion", "destination", "resilience")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _scalar(value: Any) -> Any:
    if isinstance(value, (bytes, np.bytes_)):
        return value.decode("utf-8")
    return value.item() if isinstance(value, np.generic) else value


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _read_stage_audit(source: Path, diffusion_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    with h5py.File(source, "r") as handle:
        required = ("/time", "/labels/stage", "/epoch_id", "/window_start", "/window_end")
        missing = [path for path in required if path not in handle]
        if missing:
            raise ValueError(f"missing exact stage/time provenance: {missing}")
        time = np.asarray(handle["/time"][:]).reshape(-1)
        stage = np.asarray(handle["/labels/stage"][:]).reshape(-1)
        epoch = np.asarray(handle["/epoch_id"][:]).reshape(-1)
        window_start = np.asarray(handle["/window_start"][:]).reshape(-1)
        window_end = np.asarray(handle["/window_end"][:]).reshape(-1)
        codebook = handle.get("/codebooks/stage")
        codes = np.asarray(codebook["codes"][:]).reshape(-1) if codebook is not None and "codes" in codebook else np.asarray([])
        labels = np.asarray(codebook["labels"][:]).reshape(-1) if codebook is not None and "labels" in codebook else np.asarray([])
    arrays = {"time": time, "stage": stage, "epoch_id": epoch, "window_start": window_start, "window_end": window_end}
    n = len(time)
    if any(len(values) != n for values in arrays.values()) or (diffusion_rows and len(diffusion_rows) != n):
        raise ValueError("stage/time/family alignment mismatch")
    if not np.isfinite(time).all() or np.any(np.diff(time) <= 0):
        raise ValueError("time must be finite and strictly increasing")
    if len(np.unique(epoch)) != n:
        raise ValueError("epoch_id must be unique")
    if not np.isfinite(window_start).all() or not np.isfinite(window_end).all() or np.any(window_start >= window_end):
        raise ValueError("window bounds must be finite with start < end")
    if np.any(time < window_start) or np.any(time > window_end):
        raise ValueError("timestamps must lie within exact window bounds")
    gap_before = np.zeros(n, dtype=bool)
    overlap_before = np.zeros(n, dtype=bool)
    for index in range(1, n):
        delta = float(window_start[index] - window_end[index - 1])
        gap_before[index] = delta > 1e-6
        overlap_before[index] = delta < -1e-6
    if diffusion_rows:
        for index, row in enumerate(diffusion_rows):
            if "window_id" not in row or "timestamp" not in row:
                raise ValueError("diffusion identifiers/timestamps are missing")
            if row.get("window_id") != index or row.get("timestamp") is None or float(row["timestamp"]) != float(time[index]):
                raise ValueError("diffusion window identifiers/timestamps do not align exactly")
    mapping = {_scalar(code): str(_scalar(label)) for code, label in zip(codes, labels) if int(_scalar(code)) >= 0}
    rows = []
    for index in range(n):
        code = int(stage[index])
        label = mapping.get(code)
        rows.append({
            "window_id": index,
            "epoch_id": int(epoch[index]),
            "timestamp": float(time[index]),
            "window_start": float(window_start[index]),
            "window_end": float(window_end[index]),
            "stage_code": code,
            "stage_label": label,
            "stage_label_status": "recorded" if label is not None else "missing_or_unknown",
            "stage_purity_status": "not_assessed",
            "stage_source": "/labels/stage",
            "recording_wq_used_as_stage": False,
            "diffusion_finite_ok": (bool(diffusion_rows[index].get("finite_ok", False)) if diffusion_rows else None),
            "time_gap_before": bool(gap_before[index]),
            "window_overlap_before": bool(overlap_before[index]),
            "diffusion_available": bool(diffusion_rows),
        })
    return rows


def _family_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Retain family contract metadata without embedding series tensors."""
    return {
        key: _json_safe(value)
        for key, value in payload.items()
        if key not in {"series", "amplitude_curve"}
    }


def _primary_mnps_audit(source: Path) -> dict[str, Any]:
    with h5py.File(source, "r") as handle:
        outputs = {}
        for name, resolver in (("3d", resolve_coords_3d), ("9d", resolve_coords_9d)):
            resolved = resolver(handle, "subject_anchored")
            if resolved is None:
                outputs[name] = {"status": "missing", "qualification_status": "not_assessed"}
                continue
            values = np.asarray(resolved.values)
            outputs[name] = {
                "status": "recorded",
                "values_path": resolved.values_path,
                "names_path": resolved.names_path,
                "shape": list(values.shape),
                "finite_fraction": float(np.isfinite(values).mean()),
                "provenance": _json_safe(resolved.provenance()),
                "qualification_status": "not_assessed",
            }
    return outputs


def _code_provenance() -> dict[str, Any]:
    modules = {
        "runner": sys.modules[__name__],
        "pipeline": sys.modules[run_dataset_pipeline.__module__],
        "v3_audit": sys.modules[write_audit.__module__],
        "family_readers": sys.modules[read_family.__module__],
        "family_adapters": sys.modules[diffusion_window_rows.__module__],
        "h5_contract": sys.modules[resolve_coords_3d.__module__],
    }
    files = {}
    for name, module in modules.items():
        path = inspect.getsourcefile(module)
        if path:
            resolved = Path(path).resolve()
            files[name] = {"path": str(resolved), "sha256": _sha256(resolved)}
    aggregate = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    versions = {}
    for package in ("numpy", "h5py", "pandas", "pyarrow", "PyYAML"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not_installed"
    return {"files": files, "aggregate_sha256": aggregate, "package_versions": versions}


def run_pilot(source: Path, output_root: Path, config_path: Path | None = None) -> dict[str, Any]:
    source = source.resolve()
    if source.name != SOURCE_LEAF_NAME or not source.is_file():
        raise ValueError(f"source must be the explicit verified leaf H5 named {SOURCE_LEAF_NAME}")
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"pilot output must be fresh and empty: {output_root}")
    config_raw: dict[str, Any] = {}
    source_sha256_before = _sha256(source)
    extraction = None
    audit_files = None
    if config_path is not None:
        config_path = config_path.resolve()
        config_raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        expected = config_raw.get("expected_source", {})
        expected_leaf = Path(str(expected.get("leaf_path", "")).replace("/", "\\")).resolve()
        if expected_leaf != source:
            raise ValueError("source does not match config expected_source.leaf_path")
        expected_count = int(expected.get("expected_h5_count", -1))
        discovered = sorted(source.parent.rglob("*.h5"))
        if len(discovered) != expected_count or discovered != [source]:
            raise ValueError("source parent does not contain exactly the configured H5 leaf")
        if source_sha256_before != str(expected.get("sha256", "")):
            raise ValueError("source H5 SHA-256 does not match config")
    output_root.mkdir(parents=True, exist_ok=True)
    availability = family_availability(source)
    family_payloads = {family: read_family(source, family) for family in FAMILIES}
    diffusion_rows = diffusion_window_rows(source)
    stage_rows = _read_stage_audit(source, diffusion_rows)
    recording_rows = {family: family_recording_rows(source, family) for family in FAMILIES}
    primary_mnps = _primary_mnps_audit(source)
    if config_path is not None:
        extraction_root = output_root / "extraction"
        extraction = run_dataset_pipeline(
            config_path=config_path,
            input_root=source.parent,
            output_root=extraction_root,
            workers=1,
        )
        audit_files = write_audit(extraction, extraction_root)
    manifest = {
        "schema_version": "ndt_v3_sleep_article.pilot.v1",
        "pilot_status": "descriptive_support_audit",
        "source_h5": str(source),
        "source_sha256_before": source_sha256_before,
        "source_leaf_assertion": {"expected_name": SOURCE_LEAF_NAME, "matched": True},
        "families": {family: _family_summary(payload) for family, payload in family_payloads.items()},
        "family_availability": _json_safe(availability),
        "recording_rows": _json_safe(recording_rows),
        "n_windows": len(stage_rows),
        "n_stage_missing_or_unknown": sum(row["stage_label_status"] != "recorded" for row in stage_rows),
        "primary_mnps": primary_mnps,
        "time_audit": {
            "strictly_increasing": True,
            "gap_flags_are_descriptive": True,
            "stage_purity_claim": "not_assessed",
        },
        "stage_contract": {
            "source_dataset": "/labels/stage",
            "time_dataset": "/time",
            "alignment": "exact_equal_length_and_window_index",
            "unknown_policy": "retain_missing_or_unknown",
            "recording_wq_used_as_stage": False,
        },
        "qualification_status": "not_assessed",
        "claim_status": "no_biological_claim",
        "runtime": {"python": sys.version, "platform": platform.platform()},
        "code_provenance": _code_provenance(),
    }
    if config_path is not None:
        manifest["config"] = {
            "path": str(config_path),
            "sha256": _sha256(config_path),
            "extraction": _json_safe(extraction),
            "audit_files": audit_files,
        }
        expected_analyses = [key for key, enabled in (config_raw.get("analyses") or {}).items() if enabled]
        written = set((extraction or {}).get("written_files", {}))
        errors = list((extraction or {}).get("errors", []))
        missing_tables = [key for key in expected_analyses if key not in written]
        manifest["extraction_gate"] = {"errors": errors, "missing_expected_tables": missing_tables}
        if errors or missing_tables or not written:
            manifest["pilot_status"] = "extraction_errors"
    source_sha256_after = _sha256(source)
    if source_sha256_after != source_sha256_before:
        raise ValueError("source H5 changed during read-only pilot preparation")
    manifest["source_sha256_after"] = source_sha256_after
    (output_root / "pilot_manifest.json").write_text(json.dumps(_json_safe(manifest), indent=2, allow_nan=False), encoding="utf-8")
    with (output_root / "stage_window_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(stage_rows[0]))
        writer.writeheader()
        writer.writerows(stage_rows)
    with (output_root / "family_availability.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(availability[0]))
        writer.writeheader()
        writer.writerows(availability)
    with (output_root / "diffusion_windows.json").open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(diffusion_rows), handle, indent=2, allow_nan=False)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    raw = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
    source = args.source or Path(str(raw["expected_source"]["leaf_path"]))
    output = args.output_root or Path(str((raw.get("output") or {}).get("directory", "articles/ndt_v3_sleep/results/pilot_20260906")))
    result = run_pilot(source, output, args.config)
    print(json.dumps({"pilot_manifest": str(output / "pilot_manifest.json"), "pilot_status": result["pilot_status"]}, indent=2))
    return 1 if result["pilot_status"] == "extraction_errors" else 0


if __name__ == "__main__":
    raise SystemExit(main())
