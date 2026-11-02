"""Inventory existing NMD-v3 abscissa, diffusion, and drift surfaces."""
from __future__ import annotations
import argparse, hashlib, inspect, json
from pathlib import Path
import numpy as np

from nmd_analysis.dynamical_families.readers import read_family
from nmd_analysis.dynamical_families.adapters import diffusion_window_rows
from nmd_analysis.local_dynamics.adapters import jacobian_metrics_window_rows
from nmd_analysis.local_dynamics.readers import local_dynamics_paths

def row_counts(rows, value_key):
    values = [r.get(value_key) for r in rows]
    def is_finite(value):
        try:
            return bool(np.asarray(value).size and np.isfinite(np.asarray(value, dtype=float)).all())
        except (TypeError, ValueError):
            return False
    finite_values = [v for v in values if is_finite(v)]
    computed = sum(str(r.get("computation_status", "not_recorded")) == "computed" for r in rows)
    finite = sum(is_finite(r.get(value_key)) for r in rows)
    producer_valid = sum(bool(r.get("finite_ok", False)) and is_finite(r.get(value_key)) for r in rows)
    qualified = None
    validity_counts = {}
    for row in rows:
        key = str(row.get("measurement_validity", "not_recorded"))
        validity_counts[key] = validity_counts.get(key, 0) + 1
    return {"n_rows": len(rows), "n_family_computed_rows": computed, "n_finite": finite,
            "n_adapter_finite_valid": producer_valid, "n_measurement_valid": None,
            "n_qualified": qualified, "measurement_validity_counts": validity_counts,
            "n_finite_metric_value": len(finite_values), "value_key": value_key,
            "qualification_evaluated": False}

def inventory_one(path: Path) -> dict:
    before = digest(path)
    out = {"h5": str(path), "h5_sha256_before": before, "metrics": [], "reader": "installed nmd_analysis dynamical_families/local_dynamics readers and adapters"}
    for dim in (3, 9):
        rows = jacobian_metrics_window_rows(path, dimension=dim)
        for metric in ("spectral_abscissa", "numerical_abscissa", "reactivity_gap"):
            if any(metric in r for r in rows):
                out["metrics"].append({"metric": metric, "family": "local_jacobian", "grain": "window",
                    "definition_code": "mndm/src/mndm/dynamics/jacobian_metrics.py",
                    "reader_source_path": "/jacobian/derived_metrics/v1/series" if dim == 3 else "/jacobian_9D/derived_metrics/v1/series",
                    "coordinate_contract": rows[0].get("ld_primary_coordinate_contract", "not_recorded") if rows else "not_recorded",
                    "counts": row_counts(rows, metric), "dimension": dim, "parent_grain": "recording", "coordinate_layer": rows[0].get("coordinate_layer", "not_recorded"), "metric_norm": "euclidean", "units": "per_time; exact scale metadata not recorded by adapter"})
    for family in ("diffusion",):
        payload = read_family(path, family)
        series = payload.get("series", {})
        rows = diffusion_window_rows(path)
        for metric in ("a_hat", "diffusion_tensor", "d_diff", "D_total", "c_diff", "diffusion_concentration", "diffusion_effective_dimension", "drift_diffusion_alignment", "A_bD", "R_b_over_a"):
            if metric in series:
                out["metrics"].append({"metric": metric, "family": "diffusion_geometry", "grain": "window",
                    "definition_code": "mndm/src/mndm/dynamical_families/diffusion_geometry.py",
                    "reader_source_path": "/dynamical_families/diffusion/v1/series/" + metric,
                    "coordinate_contract": payload.get("primary_coordinate_contract", "not_recorded"),
                    "dimension": len(payload.get("provenance", {}).get("coordinate_names", [])), "provenance": payload.get("provenance", {}), "grain_contract": payload.get("grain", {}), "counts": row_counts(rows, metric), "metric_computation_status": payload.get("summary", {}).get(metric + "_computation_status", "not_recorded"), "units": "not_recorded; tensor/increment metric semantics in family provenance",
                    "drift_semantics": "alignment/statistic only; not an independently supplied SDE drift" if "drift" in metric or metric in {"A_bD", "R_b_over_a"} else None})
    out["h5_sha256_after"] = digest(path)
    out["input_unchanged"] = out["h5_sha256_before"] == out["h5_sha256_after"]
    return out

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""): h.update(block)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--h5", action="append", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists(): raise SystemExit(f"refusing to overwrite existing inventory: {args.out}")
    reader_files = [Path(inspect.getsourcefile(read_family)).resolve(), Path(inspect.getsourcefile(jacobian_metrics_window_rows)).resolve(), Path(inspect.getsourcefile(diffusion_window_rows)).resolve()]
    report = {"status": "inventory_only", "inventory_code_sha256": digest(Path(__file__)), "reader_files": [str(p) for p in reader_files], "reader_sha256": {str(p): digest(p) for p in reader_files}, "inputs": [inventory_one(p) for p in args.h5]}
    if not all(item["input_unchanged"] for item in report["inputs"]): raise RuntimeError("source H5 changed during inventory")
    args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+"\n", encoding="utf-8"); print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
if __name__ == "__main__": main()
