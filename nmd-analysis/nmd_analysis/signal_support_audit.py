"""Fail-closed audit of executed signal-support provenance in explicit H5 files."""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
from typing import Any, Iterable, Mapping


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read(path: Path) -> Mapping[str, Any]:
    from .signal_support import read_signal_support  # theory-owned public API
    value = read_signal_support(path)
    if not isinstance(value, Mapping):
        raise ValueError("signal-support reader returned a non-mapping")
    return value


def audit_signal_support(input_h5: Iterable[Path], output_root: Path) -> dict[str, Any]:
    paths = [Path(p).resolve() for p in input_h5]
    if not paths or len(set(paths)) != len(paths):
        raise ValueError("at least one unique H5 input is required")
    if any(not p.is_file() or p.suffix.lower() not in {".h5", ".hdf5"} for p in paths):
        raise ValueError("all inputs must be existing H5 files")
    out = Path(output_root).resolve()
    if out.exists():
        raise FileExistsError(f"refusing to overwrite output: {out}")
    before = {str(p): _sha256(p) for p in paths}
    sources = []
    errors = []
    for path in paths:
        try:
            record = dict(_read(path))
            status = str(record.get("status", "unknown"))
            if status == "recorded" and (not isinstance(record.get("validation"), Mapping) or record["validation"].get("status") != "valid"):
                raise ValueError("recorded signal-support validation is not valid")
            if status not in {"recorded", "legacy_missing"}:
                raise ValueError(f"unsupported signal-support status: {status}; validation={record.get('validation')}")
            if status == "recorded" and record.get("source_hash_status") != "recorded_only":
                raise ValueError("recorded source hash must be explicitly recorded_only")
            # Reject invalid payloads inside the per-input boundary, so a
            # strict-JSON failure still produces a diagnostic report.
            json.dumps(record, allow_nan=False)
            extents = record.get("per_epoch_input_extent", [])
            if extents is not None and not isinstance(extents, list):
                raise ValueError("per_epoch_input_extent must be a list")
            sources.append({
                **record,
                "input_h5": str(path),
                "input_h5_sha256": before[str(path)],
                "status": status,
                "execution_records": record.get("execution_records", []),
                "per_epoch_input_extent_count": len(extents or []),
                "temporal_support_status": record.get("temporal_support", {}).get("status", "unknown"),
                "source_quality_status": record.get("source_quality_status", "not_recorded"),
                "reference_fit_population": record.get("reference_fit_population", {"status": "unknown"}),
                "claim_status": "no_biological_claim",
                "scientific_qualification": "not_assessed",
            })
        except Exception as exc:
            errors.append({"input_h5": str(path), "error_type": type(exc).__name__, "error": str(exc)})
    after = {str(p): _sha256(p) for p in paths}
    if before != after:
        errors.append({"error_type": "InputChanged", "error": "input H5 changed during audit"})
    report = {
        "schema": "nmd_analysis.signal_support_audit.v1",
        "status": "failed" if errors else "audited",
        "claim_status": "no_biological_claim",
        "scientific_qualification": "not_assessed",
        "subject_pooling": "not_performed",
        "sources": sources,
        "errors": errors,
        "provenance": {
            "input_h5_sha256_before": before,
            "input_h5_sha256_after": after,
            "audit_code_sha256": _sha256(Path(__file__).resolve()),
            "reader_code_sha256": _sha256(Path(__file__).with_name("signal_support.py")) if Path(__file__).with_name("signal_support.py").exists() else None,
            "cli_code_sha256": _sha256(Path(__file__).with_name("cli.py")),
            "python": platform.python_version(),
        },
    }
    if errors:
        # Preserve a diagnostic report while still failing the CLI.
        out.mkdir(parents=True, exist_ok=False)
        (out / "signal_support_audit.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        raise RuntimeError(json.dumps(report))
    out.mkdir(parents=True, exist_ok=False)
    (out / "signal_support_audit.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report
