"""Merge source-sidecar evidence into the ds004100 G1--G3 ledger.

Sidecar linkage can document label/entity consistency, but it cannot certify an
original-sample mapping, crop resolution, processed contacts, or reference.
Those distinctions are deliberately retained as failed/unclosed gates.
"""
from __future__ import annotations

import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _key(path: str) -> str:
    return path.replace("\\", "/")


def _entity(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return tuple(str(row[field]) for field in ("subject_id", "session", "task", "acq", "run"))


def merge_source_evidence(primary_ledger: dict[str, Any], source_audit: dict[str, Any]) -> dict[str, Any]:
    """Add source evidence without upgrading G1/G2 beyond its available proof."""
    source_rows = source_audit["rows"]
    by_path = {_key(row["h5"]): row for row in source_rows}
    if len(by_path) != len(source_rows):
        raise ValueError("Source audit contains duplicate H5 paths")
    entities = Counter(_entity(row) for row in source_rows)
    ledger_paths = {row["relative_path"] for row in primary_ledger["rows"]}
    if ledger_paths != set(by_path):
        raise ValueError("Source audit and frozen primary ledger inventories differ")

    rows = []
    for ledger_row in primary_ledger["rows"]:
        source = by_path[ledger_row["relative_path"]]
        evidence = {
            "sidecars_present": bool(source["source_ieeg_json"] and source["source_channels_tsv"]),
            "task_matches_source": bool(source["TaskName"] == source["task"] == ledger_row["label"]),
            "unique_source_entity": entities[_entity(source)] == 1,
            "source_window_within_one_sample": bool(source["h5_end_within_one_source_sample"]),
            "raw_channel_signature": source.get("channel_name_type_status_hash", "not_recorded"),
            "raw_channel_count": source.get("n_source_channels"),
            "source_reference": source.get("iEEGReference", "not_recorded"),
            "crop_resolution": "not_certified_from_sidecars",
            "original_sample_mapping": "not_certified_from_sidecars",
        }
        row = copy.deepcopy(ledger_row)
        row["source_sidecar_evidence"] = evidence
        row["g1_source_identity_evidence"] = all(
            evidence[key] for key in ("sidecars_present", "task_matches_source", "unique_source_entity", "source_window_within_one_sample")
        )
        # A source entity is not a certified source-sample/crop identity.
        row["gates"]["G1"] = False
        # n/a reference and raw-only channel signatures cannot establish the
        # processing contact/reference policy required by G2.
        row["gates"]["G2"] = False
        rows.append(row)
    return {
        "scope": "Source-sidecar G1/G2 evidence only; no endpoint values, medians, effects, or p-values",
        "source_audit_summary": source_audit["summary"],
        "n_files": len(rows),
        "g1_source_identity_evidence_count": sum(row["g1_source_identity_evidence"] for row in rows),
        "g1_gate_pass_count": sum(row["gates"]["G1"] for row in rows),
        "g2_gate_pass_count": sum(row["gates"]["G2"] for row in rows),
        "rows": rows,
    }


def load_and_merge(primary_ledger_path: Path, source_audit_path: Path) -> dict[str, Any]:
    primary = json.loads(primary_ledger_path.read_text(encoding="utf-8"))
    source = json.loads(source_audit_path.read_text(encoding="utf-8"))
    return merge_source_evidence(primary, source)


def write_ledger(ledger: dict[str, Any], output: Path) -> None:
    output.write_text(json.dumps(ledger, indent=2, sort_keys=True), encoding="utf-8")
