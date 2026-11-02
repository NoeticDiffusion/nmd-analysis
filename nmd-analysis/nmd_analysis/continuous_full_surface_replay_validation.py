"""Hash-bound validation of a deterministic full-surface feature replay.

This validator checks measurement-file identity and QC-sidecar semantic
reproducibility only. It does not qualify scientific objects, fit charts,
calculate outcomes, or authorize full-cohort scoring.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


_RUN_ONLY_QC_KEYS = frozenset({"timings", "started_at_utc", "finished_at_utc"})
_AUDIT_SCHEMA = "nmd_analysis.continuous_full_surface_audit.v1"
_AUDIT_STATUS = "PARTIAL_PASS_SOURCE_SUPPORT_ONLY"
_SOURCE_EDF_SUFFIX_CASEFOLD = "_task-sleep_acq-psg_eeg.edf"


def _is_canonical_psg_source(path: Path) -> bool:
    """Match the BIDS PSG suffix explicitly, independent of filesystem casing."""
    return path.name.casefold().endswith(_SOURCE_EDF_SUFFIX_CASEFOLD)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _normalized_qc(value: Any) -> Any:
    """Remove only explicitly volatile execution telemetry, recursively."""
    if isinstance(value, dict):
        return {
            key: _normalized_qc(item)
            for key, item in sorted(value.items())
            if key not in _RUN_ONLY_QC_KEYS and not key.startswith("worker_rss_gb_")
        }
    if isinstance(value, list):
        return [_normalized_qc(item) for item in value]
    return value


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _file_inventory(root: Path, *, exclude_validation: bool = True) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and not (exclude_validation and path.relative_to(root).as_posix() == "validation.json")
    }


def _assert_inventory(root: Path, declared: Mapping[str, str], label: str) -> dict[str, str]:
    actual = _file_inventory(root)
    if actual != dict(declared):
        missing = sorted(set(declared) - set(actual))
        extra = sorted(set(actual) - set(declared))
        changed = sorted(key for key in set(actual) & set(declared) if actual[key] != declared[key])
        raise ValueError(
            f"{label} output inventory mismatch; missing={missing}, extra={extra}, changed={changed}"
        )
    return actual


def _resolve_manifested_output(validation_path: Path, declared_path: str, expected_sha256: str) -> Path:
    declared = Path(declared_path)
    expected = (validation_path.parent / declared.name).resolve()
    if declared.is_absolute():
        resolves_to_expected = declared.resolve() == expected
    else:
        resolved_candidates = {
            (parent / declared).resolve()
            for parent in (validation_path.parent, *validation_path.parent.parents)
        }
        resolves_to_expected = expected in resolved_candidates
    if not resolves_to_expected or not expected.is_file() or _sha256(expected) != expected_sha256:
        raise ValueError(f"Manifested output path/hash does not bind to its validation directory: {declared_path}")
    return expected


def _required_path(paths: Mapping[str, Any], key: str, *, directory: bool = False) -> Path:
    value = paths.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Audit input_paths is missing {key!r}")
    path = Path(value).resolve()
    missing = not path.is_dir() if directory else not path.is_file()
    if missing:
        raise ValueError(f"Audit input path is missing: {key}={path}")
    return path


def _verify_audit_binding(
    audit_path: Path,
    replay_root: Path,
    replay_qc_dir: Path,
    audit: Mapping[str, Any],
) -> dict[str, Any]:
    if audit.get("schema") != _AUDIT_SCHEMA or audit.get("status") != _AUDIT_STATUS:
        raise ValueError("Replay audit schema/status is not the expected support-only audit")
    for key in ("charts_generated", "outcomes_calculated", "C1_C3_scores_opened", "full_cohort_scoring_authorized"):
        if audit.get(key) is not False:
            raise ValueError(f"Replay audit must keep {key}=false")
    if audit.get("surface_replay_status") != "PENDING_FULL_COHORT_REPLAY":
        raise ValueError("The source-support audit replay gate must remain pending")

    before = audit.get("input_hashes_before")
    after = audit.get("input_hashes_after")
    paths = audit.get("input_paths")
    if not isinstance(before, dict) or not isinstance(after, dict) or not isinstance(paths, dict):
        raise ValueError("Replay audit is missing hash-bound input paths/hashes")
    if set(before) != set(after) or before != after:
        raise ValueError("Replay audit detected changed inputs during the support audit")

    expected_recordings = int(audit["counts"]["recordings"])
    path_groups = {
        "events": paths.get("events"),
        "qc_sidecars": paths.get("qc_sidecars"),
        "raw_sources": paths.get("raw_sources"),
    }
    if any(not isinstance(group, dict) or len(group) != expected_recordings for group in path_groups.values()):
        raise ValueError("Event, QC-sidecar and raw-source path inventories must cover every audited recording")

    scalar_roles = {
        "features_table": "features_table",
        "participants_tsv": "participants_tsv",
        "protocol": "protocol",
        "mndm_config": "mndm_config",
        "audit_code": "audit_code",
    }
    current_hashes: dict[str, str] = {}
    for path_role, hash_role in scalar_roles.items():
        path = _required_path(paths, path_role)
        expected = before.get(hash_role)
        if not isinstance(expected, str) or _sha256(path) != expected:
            raise ValueError(f"Current audit input hash no longer matches: {path_role}")
        current_hashes[hash_role] = expected

    source_root = _required_path(paths, "source_root", directory=True)
    _required_path(paths, "qc_dir", directory=True)

    declared_source_paths = {Path(value).resolve() for value in paths["raw_sources"].values()}
    enumerated_source_paths = {
        path.resolve()
        for path in source_root.rglob("*")
        if path.is_file() and _is_canonical_psg_source(path)
    }
    if declared_source_paths != enumerated_source_paths:
        missing = sorted(str(path) for path in declared_source_paths - enumerated_source_paths)
        extra = sorted(str(path) for path in enumerated_source_paths - declared_source_paths)
        raise ValueError(
            f"Raw-source inventory differs from the case-insensitive PSG suffix "
            f"{_SOURCE_EDF_SUFFIX_CASEFOLD}; missing={missing}, extra={extra}"
        )

    replay_csv = (replay_root / "features.csv").resolve()
    replay_parquet = (replay_root / "features.parquet").resolve()
    replay_qc_dir = replay_qc_dir.resolve()
    if Path(paths["features_table"]).resolve() != replay_csv:
        raise ValueError("The support audit did not consume this replay's features.csv")
    if Path(paths.get("qc_dir", "")).resolve() != replay_qc_dir:
        raise ValueError("The support audit did not consume this replay's QC directory")
    if current_hashes["features_table"] != _sha256(replay_csv):
        raise ValueError("Replay CSV hash differs from the support audit's bound input")

    for subject, value in paths["events"].items():
        path = Path(value).resolve()
        key = f"events:{subject}"
        if not path.is_file() or before.get(key) != _sha256(path):
            raise ValueError(f"Event input is missing or changed: {subject}")

    expected_event_keys = {f"events:{subject}" for subject in paths["events"]}
    expected_qc_keys = {f"qc_sidecar:{recording}" for recording in paths["qc_sidecars"]}
    expected_raw_keys = {f"raw_source:{name.lower()}" for name in paths["raw_sources"]}
    for prefix, expected_keys in (
        ("events:", expected_event_keys),
        ("qc_sidecar:", expected_qc_keys),
        ("raw_source:", expected_raw_keys),
    ):
        actual_keys = {key for key in before if key.startswith(prefix)}
        if actual_keys != expected_keys:
            raise ValueError(f"Audit {prefix} hash inventory does not match its input paths")

    qc_paths = paths["qc_sidecars"]
    for recording, value in qc_paths.items():
        path = Path(value).resolve()
        key = f"qc_sidecar:{recording}"
        expected_filename = f"{Path(recording).stem}_qc_artifacts.json"
        if path.name.casefold() != expected_filename.casefold():
            raise ValueError(f"QC-sidecar path is not bound to recording identity: {recording}")
        if path.parent != replay_qc_dir:
            raise ValueError(f"QC-sidecar path is outside the replay QC inventory: {recording}")
        if not path.is_file() or before.get(key) != _sha256(path):
            raise ValueError(f"QC-sidecar input is missing or changed: {recording}")

    raw_source_hashes_current: dict[str, str] = {}
    for source_name, value in paths["raw_sources"].items():
        path = Path(value).resolve()
        key = f"raw_source:{source_name.lower()}"
        if path.name.casefold() != source_name.casefold():
            raise ValueError(f"Raw-source path is not bound to its declared filename: {source_name}")
        try:
            path.relative_to(source_root)
        except ValueError as exc:
            raise ValueError(f"Raw source is outside the declared source root: {source_name}") from exc
        if not path.is_file() or not isinstance(before.get(key), str) or _sha256(path) != before[key]:
            raise ValueError(f"Raw source is missing or its current SHA-256 changed: {source_name}")
        raw_source_hashes_current[source_name] = before[key]

    declared_outputs = audit.get("output_sha256")
    if not isinstance(declared_outputs, dict):
        raise ValueError("Replay audit has no generated-output hash inventory")
    if "validation.json is excluded" not in str(audit.get("output_hash_scope", "")):
        raise ValueError("Replay audit does not declare its validation.json self-hash exclusion")
    _assert_inventory(audit_path.parent, declared_outputs, "Support audit")

    return {
        "audit_validation_path": str(audit_path.resolve()),
        "audit_validation_sha256": _sha256(audit_path),
        "audit_schema": audit["schema"],
        "audit_status": audit["status"],
        "audit_output_inventory_count": len(declared_outputs),
        "audit_input_hash_count": len(before),
        "source_hashes_unchanged_during_audit": True,
        "recording_input_inventory_counts": {
            name: len(group) for name, group in path_groups.items()
        },
        "replay_csv_sha256": _sha256(replay_csv),
        "replay_parquet_sha256": _sha256(replay_parquet),
        "fixed_input_sha256": current_hashes,
        "fixed_input_paths": {
            role: str(Path(paths[role]).resolve()) for role in scalar_roles
        },
        "raw_source_sha256_current_verified": raw_source_hashes_current,
        "raw_source_inventory": {
            "filename_suffix_casefold": _SOURCE_EDF_SUFFIX_CASEFOLD,
            "enumerated_count": len(enumerated_source_paths),
            "declared_count": len(declared_source_paths),
            "exact_inventory_match": True,
        },
        "qc_sidecar_filenames": sorted(Path(value).name for value in paths["qc_sidecars"].values()),
    }


def _qc_sidecars(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        raise ValueError(f"QC-sidecar directory does not exist: {root}")
    all_json = {path.name: path for path in sorted(root.glob("*.json")) if path.is_file()}
    unexpected = sorted(name for name in all_json if not name.endswith("_qc_artifacts.json"))
    if unexpected:
        raise ValueError(f"Unexpected non-QC JSON files in QC inventory: {unexpected}")
    return all_json


def _verify_auxiliary_support_artifacts(
    support_map_validation: Path | None,
    stage_support_validation: Path | None,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if support_map_validation is not None:
        path = support_map_validation.resolve()
        payload = _read_json(path)
        if payload.get("verdict") != "PARTIAL_PASS_ALL_FOLD_APPLY_SUPPORT_CROSSWALK":
            raise ValueError("Unexpected all-fold apply support-map verdict")
        for key in (
            "biological_claim_authorized",
            "contrasts_computed",
            "label_join_performed",
            "stage_horizon_intersection_computed",
        ):
            if payload.get(key) is not False:
                raise ValueError(f"Support-map evidence must keep {key}=false")
        declared_parquet = payload.get("output_parquet")
        declared_parquet_hash = payload.get("output_parquet_sha256")
        if not isinstance(declared_parquet, str) or not isinstance(declared_parquet_hash, str):
            raise ValueError("All-fold support map is missing its parquet path/hash")
        parquet = _resolve_manifested_output(path, declared_parquet, declared_parquet_hash)
        expected_parquet = (path.parent / Path(declared_parquet).name).resolve()
        if parquet != expected_parquet:
            raise ValueError("All-fold support-map parquet hash mismatch")
        result["all_fold_apply_support_map"] = {
            "validation_path": str(path),
            "validation_sha256": _sha256(path),
            "verdict": payload["verdict"],
            "parquet_path": str(parquet.resolve()),
            "parquet_sha256": _sha256(parquet),
            "row_count": payload.get("row_count"),
            "recording_count": payload.get("recording_count"),
        }

    if stage_support_validation is not None:
        path = stage_support_validation.resolve()
        payload = _read_json(path)
        if payload.get("verdict") != "PARTIAL_PASS_STAGE_HORIZON_SUPPORT_ONLY":
            raise ValueError("Unexpected all-fold stage/horizon support verdict")
        for key in ("outcomes_calculated", "matching_performed", "C1_C2_C3_scores_opened", "biological_claim_authorized"):
            if payload.get(key) is not False:
                raise ValueError(f"Stage/horizon support evidence must keep {key}=false")
        if payload.get("full_surface_replay_gate") != "NOT_ASSESSED_BY_THIS_AUDIT":
            raise ValueError("Stage/horizon audit must not claim full-surface replay closure")
        if payload.get("full_cohort_protocol_authorization") != "NOT_GRANTED":
            raise ValueError("Stage/horizon audit must not authorize full-cohort outcomes")
        inventory = payload.get("output_sha256")
        output_names = payload.get("outputs")
        if not isinstance(inventory, dict) or not isinstance(output_names, dict) or set(inventory) != set(output_names):
            raise ValueError("Stage/horizon support evidence has no aligned output hash/path inventory")
        declared_files = {}
        for name, digest in inventory.items():
            output_name = output_names.get(name)
            if not isinstance(output_name, str) or Path(output_name).name != output_name or not isinstance(digest, str):
                raise ValueError("Stage/horizon support output inventory contains invalid paths or hashes")
            declared_files[output_name] = digest
        if len(declared_files) != len(inventory):
            raise ValueError("Stage/horizon support output inventory contains invalid entries")
        actual_files = {
            name: _sha256(path.parent / name)
            for name in declared_files
            if (path.parent / name).is_file()
        }
        if actual_files != declared_files:
            raise ValueError("Stage/horizon support output files do not match their declared hashes")
        unexpected = {
            child.name for child in path.parent.iterdir()
            if child.is_file() and child.name != path.name and child.name not in declared_files
        }
        if unexpected:
            raise ValueError(f"Stage/horizon support audit has unmanifested files: {sorted(unexpected)}")
        result["all_fold_stage_horizon_support"] = {
            "validation_path": str(path),
            "validation_sha256": _sha256(path),
            "verdict": payload["verdict"],
            "output_sha256": inventory,
        }
    return result


def validate_full_surface_replay(
    reference_root: Path,
    replay_root: Path,
    audit_validation: Path,
    output_dir: Path,
    *,
    support_map_validation: Path | None = None,
    stage_support_validation: Path | None = None,
) -> dict[str, Any]:
    """Validate exact feature replay and QC semantics, without opening outcomes."""
    reference_root = reference_root.resolve()
    replay_root = replay_root.resolve()
    audit_validation = audit_validation.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(f"Replay validation output already exists: {output_dir}")

    reference_csv = reference_root / "features.csv"
    reference_parquet = reference_root / "features.parquet"
    replay_csv = replay_root / "features.csv"
    replay_parquet = replay_root / "features.parquet"
    for path in (reference_csv, reference_parquet, replay_csv, replay_parquet):
        if not path.is_file():
            raise ValueError(f"Required replay feature artifact is missing: {path}")

    failed_files = replay_root / "failed_files.txt"
    failed_entries = []
    if failed_files.exists():
        failed_entries = [line.strip() for line in failed_files.read_text(encoding="utf-8").splitlines() if line.strip()]
        if failed_entries:
            raise ValueError(f"Replay contains failed-file entries: {failed_entries[:10]}")

    feature_hashes = {
        "reference_csv_sha256": _sha256(reference_csv),
        "replay_csv_sha256": _sha256(replay_csv),
        "reference_parquet_sha256": _sha256(reference_parquet),
        "replay_parquet_sha256": _sha256(replay_parquet),
    }
    if feature_hashes["reference_csv_sha256"] != feature_hashes["replay_csv_sha256"]:
        raise ValueError("Reference and replay features.csv are not byte-identical")
    if feature_hashes["reference_parquet_sha256"] != feature_hashes["replay_parquet_sha256"]:
        raise ValueError("Reference and replay features.parquet are not byte-identical")

    with reference_csv.open("r", encoding="utf-8-sig", newline="") as stream:
        csv_rows = sum(1 for _ in csv.reader(stream)) - 1
    audit = _read_json(audit_validation)
    if csv_rows != int(audit["counts"]["feature_rows"]):
        raise ValueError("Replayed CSV row count does not match the source-support audit")

    qc_reference = _qc_sidecars(reference_root / "qc_artifacts")
    qc_replay = _qc_sidecars(replay_root / "qc_artifacts")
    if set(qc_reference) != set(qc_replay):
        raise ValueError("Reference and replay QC-sidecar filename inventories differ")
    expected_recordings = int(audit["counts"]["recordings"])
    if len(qc_replay) != expected_recordings:
        raise ValueError("QC-sidecar inventory does not cover every audited recording")

    audit_binding = _verify_audit_binding(
        audit_validation,
        replay_root,
        replay_root / "qc_artifacts",
        audit,
    )
    if set(audit_binding["qc_sidecar_filenames"]) != set(qc_replay):
        raise ValueError("Replay audit QC paths do not match the replay QC filename inventory")
    qc_records: dict[str, Any] = {}
    for filename in sorted(qc_reference):
        reference_path = qc_reference[filename]
        replay_path = qc_replay[filename]
        reference_value = _read_json(reference_path)
        replay_value = _read_json(replay_path)
        normalized_reference = _normalized_qc(reference_value)
        normalized_replay = _normalized_qc(replay_value)
        if normalized_reference != normalized_replay:
            raise ValueError(f"QC semantic mismatch after run-only normalization: {filename}")
        qc_records[filename] = {
            "reference_raw_sha256": _sha256(reference_path),
            "replay_raw_sha256": _sha256(replay_path),
            "normalized_semantic_sha256": _canonical_sha256(normalized_replay),
        }

    auxiliary = _verify_auxiliary_support_artifacts(support_map_validation, stage_support_validation)
    report = {
        "schema": "nmd_analysis.continuous_full_surface_replay_validation.v1",
        "status": "PASS_DETERMINISTIC_FEATURE_REPLAY",
        "scope": "feature-byte identity and QC-sidecar semantic replay only",
        "feature_hashes": feature_hashes,
        "feature_rows": csv_rows,
        "recordings": expected_recordings,
        "qc_sidecar_count": len(qc_records),
        "qc_normalization_policy": {
            "excluded_run_only_keys": sorted(_RUN_ONLY_QC_KEYS),
            "excluded_key_prefixes": ["worker_rss_gb_"],
            "unknown_fields_remain_comparison_relevant": True,
        },
        "qc_sidecars": qc_records,
        "failed_files": {
            "path": str(failed_files.resolve()),
            "exists": failed_files.exists(),
            "nonempty_entries": failed_entries,
        },
        "audit_binding": audit_binding,
        "validator_code": {
            "path": str(Path(__file__).resolve()),
            "sha256": _sha256(Path(__file__).resolve()),
        },
        "auxiliary_support_artifacts": auxiliary,
        "charts_generated": False,
        "outcomes_calculated": False,
        "C1_C3_scores_opened": False,
        "full_cohort_scoring_authorized": False,
        "gate_7_status": "REPLAY_EVIDENCE_PASS; independent full-surface review remains required",
        "gate_8_status": "NOT_OPEN; dated amendment and separate authorization required",
        "interpretation": "Deterministic feature/QC replay is evidenced; this does not establish scientific qualification or authorize outcome analysis.",
        "inputs": {
            "reference_root": str(reference_root),
            "replay_root": str(replay_root),
            "audit_validation": str(audit_validation),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=False)
    validation_path = output_dir / "validation.json"
    validation_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-root", type=Path, required=True, help="Frozen reference ds005555 feature root")
    parser.add_argument("--replay-root", type=Path, required=True, help="Fresh replay ds005555 feature root")
    parser.add_argument("--audit-validation", type=Path, required=True)
    parser.add_argument("--support-map-validation", type=Path)
    parser.add_argument("--stage-support-validation", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    report = validate_full_surface_replay(
        args.reference_root,
        args.replay_root,
        args.audit_validation,
        args.out_dir,
        support_map_validation=args.support_map_validation,
        stage_support_validation=args.stage_support_validation,
    )
    print(json.dumps({key: report[key] for key in ("status", "feature_rows", "recordings", "qc_sidecar_count", "gate_7_status", "gate_8_status")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
