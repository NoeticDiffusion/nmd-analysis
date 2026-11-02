"""Descriptive support audit of an explicit extraction run; no biological inference."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


GROUP_COLUMNS = (
    "family_id", "coordinate_contract", "coordinate_layer", "coordinate_dimension",
    "table_grain", "condition", "stage", "stage_label", "computation_status",
    "measurement_validity", "claim_status", "failure_reason", "not_testable_reason",
)


def _count_unique(frame: pd.DataFrame, columns: tuple[str, ...]) -> int:
    for column in columns:
        if column in frame:
            return int(frame[column].dropna().nunique())
    return 0


def _counts(frame: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {
        "n_rows": len(frame),
        "n_subjects_identified": _count_unique(frame, ("subject_id", "participant_id")),
        "n_recordings_identified": _count_unique(frame, ("source_h5",)),
    }
    for column in ("finite_ok", "not_testable", "validity_limited"):
        if column in frame:
            # Missing values stay unknown, rather than being counted as valid.
            values = frame[column]
            result[column] = {
                "true": int(values.eq(True).sum()),
                "false": int(values.eq(False).sum()),
                "unknown": int((~values.isin([True, False])).sum()),
            }
    return result


def audit_tables(written_files: Mapping[str, str | Path]) -> dict[str, Any]:
    """Audit exactly the supplied tables, avoiding unrelated historical runs.

    Counts are descriptive and non-additive across strata. Subject identifiers
    remain scoped to this dataset/run; rows and windows are never treated as N.
    """
    tables: dict[str, Any] = {}
    for analysis_type, path in written_files.items():
        frame = pd.read_parquet(path)
        columns = [column for column in GROUP_COLUMNS if column in frame]
        strata = []
        if columns:
            for key, group in frame.groupby(columns, dropna=False, sort=False):
                keys = key if isinstance(key, tuple) else (key,)
                labels = {
                    column: None if pd.isna(value) else str(value)
                    for column, value in zip(columns, keys)
                }
                strata.append({**labels, **_counts(group)})
        tables[analysis_type] = {
            "source_table": str(Path(path).resolve()),
            **_counts(frame),
            "strata": strata,
        }
    return {
        "schema_version": "nmd_analysis.v3_support_audit.v1",
        "claim_status": "no_biological_claim",
        "purpose": "measurement_support_and_missingness_only",
        "scientific_qualification": "not_assessed",
        "counting_note": "Rows are not subjects; subject counts across strata are not additive.",
        "tables": tables,
    }


def write_audit(result: Mapping[str, Any], output_root: str | Path) -> dict[str, str]:
    """Persist extraction errors and support together; never declare M3 PASS."""
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    report = audit_tables(result.get("written_files", {}))
    report["dataset"] = result.get("dataset")
    report["extraction_errors"] = list(result.get("errors", []))
    report["extraction_skipped"] = list(result.get("skipped", []))
    report["extraction_complete"] = not report["extraction_errors"] and bool(report["tables"])
    audit_path = root / "v3_support_audit.json"
    manifest_path = root / "v3_extraction_manifest.json"
    audit_path.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    manifest_path.write_text(json.dumps(dict(result), indent=2, allow_nan=False), encoding="utf-8")
    return {"audit": str(audit_path), "manifest": str(manifest_path)}
