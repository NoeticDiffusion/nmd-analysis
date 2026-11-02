"""Fail-closed, descriptive stage-dependency audit for explicit v3 H5 inputs."""
from __future__ import annotations
import hashlib, json, platform
from pathlib import Path
from typing import Any, Mapping
import h5py
import numpy as np

KNOWN = {0, 1, 2, 3, 4}

def _strict_int_array(a, name):
    a = np.asarray(a)
    if a.ndim != 1 or a.dtype.kind not in "iu": raise ValueError(f"{name} must be a one-dimensional integer array")
    if a.dtype.kind == "b": raise ValueError(f"{name} boolean array is invalid")
    return a

def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()

def _read_policy(path: Path) -> Mapping[str, Any]:
    def pairs(items):
        out = {}
        for key, val in items:
            if key in out: raise ValueError("duplicate policy key")
            out[key] = val
        return out
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite policy constant")))
    if not isinstance(value, Mapping): raise ValueError("policy must be a mapping")
    required = {"schema", "status", "scientific_qualification", "stage_purity_status", "scope", "allowed_descriptive_association", "intrinsic_stage_dynamics", "source_quality", "prohibited_claims"}
    if not required.issubset(value): raise ValueError("policy missing required contract fields")
    if value["schema"] != "ndt.sleep.stage_dependency_policy.v1" or value["status"] != "allowed_description_with_limitations": raise ValueError("unsupported policy contract")
    if value["scientific_qualification"] != "not_assessed" or value["stage_purity_status"] != "not_assessed": raise ValueError("policy qualification relaxed")
    if value["scope"].get("recording_grain") != "recording_parent" or value["scope"].get("population_unit") != "participant" or value["scope"].get("replication_unit") != "independent_participant": raise ValueError("policy scope mismatch")
    if value["allowed_descriptive_association"].get("normalization", {}).get("per_stage_fit") is not False: raise ValueError("per-stage fit policy mismatch")
    if value["intrinsic_stage_dynamics"].get("full_qualified_count", "bad") is not None: raise ValueError("qualified count must remain null")
    return value

def _labels(h5: h5py.File):
    for name in ("labels/stage", "stage"):
        if name in h5: return np.asarray(h5[name][()]), name
    raise ValueError("stage labels missing")

def audit_one(path: Path, policy: Mapping[str, Any]) -> dict[str, Any]:
    with h5py.File(path, "r") as h5:
        ids = _strict_int_array(h5["epoch_id"][()], "epoch_id") if "epoch_id" in h5 else None
        time = np.asarray(h5["time"][()]) if "time" in h5 else None
        start = np.asarray(h5["window_start"][()]) if "window_start" in h5 else None
        end = np.asarray(h5["window_end"][()]) if "window_end" in h5 else None
        stage_values, stage_path = _labels(h5)
        stage = _strict_int_array(stage_values, "stage")
        arrays = [ids, time, start, end, stage]
        if any(a is None for a in arrays): raise ValueError("required epoch arrays missing")
        if any(np.asarray(a).ndim != 1 for a in arrays): raise ValueError("required epoch arrays must be one-dimensional")
        if any(a.dtype.kind not in "fiu" for a in (time, start, end)): raise ValueError("time and bounds must be numeric")
        n = len(ids)
        if any(len(a) != n for a in arrays): raise ValueError("epoch array length mismatch")
        if len(set(int(x) for x in ids)) != n: raise ValueError("epoch IDs are not unique")
        finite = np.isfinite(time) & np.isfinite(start) & np.isfinite(end)
        ordered = finite & (end > start)
        if n == 0: raise ValueError("empty H5 epoch table")
        dt = np.diff(time)
        monotonic = bool(np.isfinite(dt).all() and np.all(dt > 0))
        nonpositive = int(np.sum(~(np.isfinite(dt) & (dt > 0))))
        id_breaks = int(np.sum(np.diff(ids) != 1)) if n > 1 else 0
        bound_breaks = int(np.sum(start[1:] != end[:-1])) if n > 1 else 0
        window_gaps = int(np.sum(start[1:] > end[:-1])) if n > 1 else 0
        window_overlaps = int(np.sum(start[1:] < end[:-1])) if n > 1 else 0
        raw_files = []
        if "row_source/raw_file" in h5:
            raw_values = np.asarray(h5["row_source/raw_file"][()])
            if raw_values.ndim != 1 or len(raw_values) != n: raise ValueError("raw_file row alignment mismatch")
            if raw_values.dtype.kind not in "OUS": raise ValueError("raw_file must contain strings")
            raw_files = [x.decode() if isinstance(x, bytes) else str(x) for x in raw_values]
            if any(not x.strip() for x in raw_files): raise ValueError("raw_file identity is blank")
        raw_switches = int(sum(a != b for a, b in zip(raw_files, raw_files[1:]))) if raw_files else None
        if not monotonic or not np.all(ordered): raise ValueError("nonfinite, unordered, or nonmonotonic epoch records")
        stage_codes, stage_counts = np.unique(stage.astype(int), return_counts=True)
        count_map = {str(int(k)): int(v) for k, v in zip(stage_codes, stage_counts)}
        known = np.isin(stage.astype(int), list(KNOWN))
        code8 = int(np.sum(stage.astype(int) == 8))
        try:
            from nmd_analysis.signal_support import read_signal_support
            support = read_signal_support(path)
        except Exception as exc:
            raise ValueError(f"signal-support reader failed: {type(exc).__name__}: {exc}") from exc
    status = str(support.get("status", "unknown")) if isinstance(support, Mapping) else "unknown"
    if status not in {"recorded", "legacy_missing"}:
        raise ValueError(f"unsupported signal-support status: {status}")
    ppg_operations = [op for record in support.get("execution_records", [])
                      for op in record.get("operations", []) if op.get("name") == "ppg_peak_detection"]
    return {
        "scientific_qualification": "not_assessed", "contrast_computed": False,
        "contrast_readiness": "not_assessed",
        "distinct_known_stage_count": len(set(int(x) for x in stage if int(x) in KNOWN)),
        "at_least_two_known_stages": len(set(int(x) for x in stage if int(x) in KNOWN)) >= 2,
        "ppg_adaptive_dependency": {"status": "recorded" if ppg_operations else "unknown", "operations": ppg_operations},
        "input_h5": str(path), "input_h5_sha256": _sha(path), "n_epochs": n,
        "epoch_id_min": int(np.min(ids)), "epoch_id_max": int(np.max(ids)),
        "finite_ordered_window_rows": int(np.sum(ordered)), "nonfinite_or_unordered_rows": int(np.sum(~ordered)),
        "time_monotonic": monotonic, "time_nonpositive_step_count": nonpositive, "epoch_id_break_count": id_breaks, "window_bound_break_count": bound_breaks, "window_gap_count": window_gaps, "window_overlap_count": window_overlaps, "raw_file_switch_count": raw_switches, "stage_counts": count_map,
        "known_stage_rows": int(np.sum(known)), "unknown_stage_rows": int(np.sum(~known)),
        "code8_source_quality_rows": code8,
        "descriptive_stage_label_association": {"status": "descriptive_recording_parent" if status == "recorded" else "unknown_legacy_support", "stage_label_field": stage_path, "stage_purity": "not_established"},
        "intrinsic_support_status": "not_assessed",
        "full_support_status": "unknown",
        "qualified_increment_count": None,
        "reference_fit_population": support.get("reference_fit_population", {"status": "unknown"}),
        "source_quality_intervals": support.get("source_quality_intervals", []),
        "signal_support_status": status,
    }

def audit(inputs: list[Path], policy_path: Path, output_root: Path) -> dict[str, Any]:
    inputs = [Path(p).resolve() for p in inputs]
    if not inputs or len(set(inputs)) != len(inputs): raise ValueError("unique H5 inputs required")
    if output_root.exists(): raise FileExistsError("output already exists")
    if not policy_path.is_file(): raise FileNotFoundError(policy_path)
    policy_hash_before = _sha(policy_path)
    policy = _read_policy(policy_path)
    canonical_policy_hash = hashlib.sha256(json.dumps(policy, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    if canonical_policy_hash != "97367837c4838746a22450a8750f4c423ebbc3fc9b7920ceb54c174e9032b954": raise ValueError("policy canonical hash mismatch")
    before = {str(p): _sha(p) for p in inputs}
    sources = []; errors = []
    for p in inputs:
        try: sources.append(audit_one(p, policy))
        except Exception as exc: errors.append({"input_h5": str(p), "error_type": type(exc).__name__, "error": str(exc)})
    after = {str(p): _sha(p) for p in inputs}
    if before != after: errors.append({"error_type": "InputChanged", "error": "input changed during audit"})
    policy_hash_after = _sha(policy_path)
    if policy_hash_before != policy_hash_after: errors.append({"error_type": "PolicyChanged", "error": "policy changed during audit"})
    import importlib, sys
    reader = sys.modules.get("nmd_analysis.signal_support") or importlib.import_module("nmd_analysis.signal_support")
    reader_path = Path(getattr(reader, "__file__", ""))
    if not reader_path.is_file(): raise ValueError("reader source hash unavailable")
    reader_hash = _sha(reader_path)
    report = {"schema": "ndt_v3_sleep.stage_dependency_audit.v1", "status": "failed" if errors else "audited", "claim_status": "no_biological_claim", "scientific_qualification": "not_assessed", "policy_canonical_sha256": canonical_policy_hash, "subject_pooling": "not_performed", "policy_sha256": policy_hash_before, "sources": sources, "errors": errors, "provenance": {"input_h5_sha256_before": before, "input_h5_sha256_after": after, "policy_sha256_before": policy_hash_before, "policy_sha256_after": policy_hash_after, "audit_code_sha256": _sha(Path(__file__)), "reader_code_sha256": reader_hash, "python": platform.python_version()}}
    output_root.mkdir(parents=True, exist_ok=False)
    (output_root / "stage_dependency_audit.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if errors: raise RuntimeError(json.dumps(report))
    return report

def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(); p.add_argument("--input-h5", action="append", required=True); p.add_argument("--policy", required=True); p.add_argument("--output-root", required=True)
    a = p.parse_args(argv)
    try: print(json.dumps(audit([Path(x).resolve() for x in a.input_h5], Path(a.policy).resolve(), Path(a.output_root).resolve()), indent=2)); return 0
    except Exception as exc: print(str(exc)); return 1

if __name__ == "__main__": raise SystemExit(main())
