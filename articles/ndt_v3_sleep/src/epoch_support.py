"""Read-only, exact per-epoch MNPS export for one verified v3 sleep H5."""
from __future__ import annotations

import argparse
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
import pandas as pd
import yaml

from nmd_analysis.h5_contract import resolve_coords_3d, resolve_coords_9d
from nmd_analysis.dynamical_families.readers import read_family
from sleep_pilot import _read_stage_audit

SOURCE_LEAF = "sub-99_Sleep_acq-psg.h5"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe(v: Any) -> Any:
    if isinstance(v, dict): return {str(k): safe(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)): return [safe(x) for x in v]
    if isinstance(v, np.ndarray): return safe(v.tolist())
    if isinstance(v, np.generic): return safe(v.item())
    if isinstance(v, (bytes, np.bytes_)): return bytes(v).decode("utf-8", "replace")
    if isinstance(v, float) and not np.isfinite(v): return None
    return v

def _validate_stage(source: Path) -> None:
    with h5py.File(source, "r") as h:
        for p in ("/time", "/window_start", "/window_end"):
            if p not in h or not np.issubdtype(np.asarray(h[p][:]).dtype, np.number):
                raise ValueError(f"missing or nonnumeric {p}")
        for p in ("/epoch_id", "/labels/stage"):
            if p not in h or not np.issubdtype(np.asarray(h[p][:]).dtype, np.integer):
                raise ValueError(f"{p} must be an integer dataset; no truncating coercion")

def _coords(resolved: Any, dims: int, n: int) -> dict[str, Any]:
    if resolved is None: raise ValueError(f"missing subject_anchored {dims}D coordinates")
    values = np.asarray(resolved.values)
    if values.ndim != 2 or values.shape != (n, dims):
        raise ValueError(f"{dims}D coordinate shape {values.shape}; expected {(n, dims)}")
    names = [x.decode("utf-8", "replace") if isinstance(x, bytes) else str(x) for x in resolved.names]
    if len(names) != dims or any(not x for x in names) or len(set(names)) != dims:
        raise ValueError(f"{dims}D coordinate names must be unique and length {dims}")
    return {"values": values, "names": names, "values_path": resolved.values_path,
            "names_path": resolved.names_path, "provenance": safe(resolved.provenance()),
            "shape": list(values.shape), "finite_count": int(np.isfinite(values).sum()),
            "nonfinite_count": int(values.size - np.isfinite(values).sum())}

def _masks(h: h5py.File, n: int) -> dict[str, Any]:
    known = ("/qc/windows/coverage_ok", "/qc/windows/retained_after_qc",
             "/qc/windows/geometry_valid", "/qc/windows/coords_9d_valid")
    out = []
    for p in known:
        if p not in h:
            out.append({"path": p, "shape": None, "dtype": None, "aligned_first_dimension": False,
                        "raw_values_retained": False, "status": "not_recorded", "values": None,
                        "unknown_count": n})
            continue
        d = h[p]
        if d.ndim != 1 or d.shape != (n,):
            raise ValueError(f"{p} must have exact shape ({n},), got {d.shape}")
        if d.dtype.kind not in "biuf":
            raise ValueError(f"{p} must be boolean or numeric 0/1/NaN, got {d.dtype}")
        raw = np.asarray(d[:])
        finite = np.isfinite(raw)
        nan = np.isnan(raw) if d.dtype.kind == "f" else np.zeros(raw.shape, dtype=bool)
        if np.any(~finite & ~nan) or np.any(finite & (raw != 0) & (raw != 1)):
            raise ValueError(f"{p} contains values other than 0, 1, or NaN")
        out.append({"path": p, "shape": list(d.shape), "dtype": str(d.dtype),
                    "aligned_first_dimension": True, "raw_values_retained": True,
                    "status": "recorded_aligned", "values": raw.tolist(),
                    "unknown_count": int(np.count_nonzero(nan))})
    any_recorded = any(item["status"] == "recorded_aligned" for item in out)
    return {"status": "recorded" if any_recorded else "not_recorded", "unknown_when_not_recorded": not any_recorded,
            "datasets": out}

def _provenance() -> dict[str, Any]:
    mods = {"runner": sys.modules[__name__], "h5_contract": sys.modules[resolve_coords_3d.__module__],
            "stage_audit": sys.modules[_read_stage_audit.__module__], "family_reader": sys.modules[read_family.__module__]}
    files = {}
    for name, mod in mods.items():
        p = inspect.getsourcefile(mod)
        if p: files[name] = {"path": str(Path(p).resolve()), "sha256": sha256(Path(p))}
    versions = {}
    for pkg in ("numpy", "h5py", "pandas", "pyarrow", "PyYAML"):
        try: versions[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError: versions[pkg] = "not_installed"
    return {"files": files, "aggregate_sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
            "package_versions": versions, "python": sys.version, "platform": platform.platform()}

def run_epoch_export(source: Path, output_root: Path, config_path: Path) -> dict[str, Any]:
    source, output_root, config_path = Path(source).resolve(), Path(output_root).resolve(), Path(config_path).resolve()
    if not source.is_file(): raise ValueError("unexpected source leaf")
    if output_root.exists() and any(output_root.iterdir()): raise FileExistsError("output must be fresh and empty")
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    expected = cfg.get("source", {})
    expected_leaf = str(expected.get("leaf_name") or SOURCE_LEAF)
    if source.name != expected_leaf: raise ValueError(f"unexpected source leaf; expected {expected_leaf}")
    if Path(str(expected.get("h5", "")).replace("/", "\\")).resolve() != source: raise ValueError("configured H5 mismatch")
    before = sha256(source)
    if before != str(expected.get("sha256", "")): raise ValueError("source SHA mismatch")
    if len(list(source.parent.glob("*.h5"))) != int(expected.get("expected_h5_count", 1)): raise ValueError("H5 leaf count mismatch")
    _validate_stage(source)
    stages = _read_stage_audit(source, [])
    with h5py.File(source, "r") as h:
        c3, c9 = _coords(resolve_coords_3d(h, "subject_anchored"), 3, len(stages)), _coords(resolve_coords_9d(h, "subject_anchored"), 9, len(stages))
        masks = _masks(h, len(stages))
        diffusion_support = read_family(source, "diffusion")
    rows = []
    for i, stage in enumerate(stages):
        row = {k: v for k, v in stage.items() if k not in {"diffusion_available", "diffusion_finite_ok"}}
        row["coordinate_finite_3d"] = bool(np.isfinite(c3["values"][i]).all())
        row["coordinate_finite_9d"] = bool(np.isfinite(c9["values"][i]).all())
        for c, v in zip(c3["names"], c3["values"][i]): row[f"mnps_3d_{c}"] = v
        for c, v in zip(c9["names"], c9["values"][i]): row[f"mnps_9d_{c}"] = v
        for record in masks["datasets"]:
            leaf = record["path"].rsplit("/", 1)[-1]
            values = record.get("values")
            row[f"producer_mask_{leaf}"] = values[i] if values is not None else np.nan
        rows.append(row)
    output_root.mkdir(parents=True, exist_ok=True)
    table = output_root / "epoch_coordinates.parquet"
    frame = pd.DataFrame(rows)
    frame.to_parquet(table, index=False)
    if len(pd.read_parquet(table)) != len(rows):
        raise ValueError("Parquet round-trip row count changed")
    after = sha256(source)
    if after != before: raise ValueError("source changed during read-only export")
    manifest = {"schema_version": "ndt_v3_sleep_article.epoch_support.v1", "status": "descriptive_epoch_export",
                "source_h5": str(source), "source_sha256_before": before, "source_sha256_after": after,
                "source_leaf_assertion": {"expected_name": expected_leaf, "matched": source.name == expected_leaf},
                "config": {"path": str(config_path), "sha256": sha256(config_path)}, "n_epochs": len(rows),
                "epoch_alignment": "exact_equal_length_and_window_index", "stage_source": "/labels/stage",
                "stage_purity_status": "not_assessed", "recorded_epoch_timestamp_alignment": "exact",
                "claim_status": "no_biological_claim", "measurement_validity": "not_assessed",
                "feature_filter_full_support": "not_assessed", "diffusion_neighbor_stage_purity": "not_assessed",
                "recording_wq_exported": False, "no_biological_claim": True, "measurement_status": "not_assessed",
                "diffusion_support_signature": safe({k: v for k, v in diffusion_support.items() if k not in {"series", "amplitude_curve"}}),
                "coordinates": {"3d": {k: v for k, v in c3.items() if k != "values"},
                "9d": {k: v for k, v in c9.items() if k != "values"}}, "producer_masks": masks,
                "output": {"parquet": str(table), "columns": list(frame.columns)},
                "checks": {"all_stage_rows_exported": True, "nonfinite_values_preserved": True,
                           "unknown_stage_codes_retained": True, "recording_q_excluded": True}, "code_provenance": _provenance()}
    manifest["output"]["table_sha256"] = sha256(table)
    manifest["output"]["table_size_bytes"] = table.stat().st_size
    (output_root / "epoch_manifest.json").write_text(json.dumps(safe(manifest), indent=2, sort_keys=True), encoding="utf-8")
    return manifest

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--source", type=Path); p.add_argument("--output", type=Path); p.add_argument("--config", type=Path, required=True)
    args = p.parse_args()
    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
    source = args.source or Path(str(cfg["source"]["h5"]))
    output = args.output or Path(str(cfg["output_root"]))
    print(json.dumps({"status": run_epoch_export(source, output, args.config)["status"]}))
