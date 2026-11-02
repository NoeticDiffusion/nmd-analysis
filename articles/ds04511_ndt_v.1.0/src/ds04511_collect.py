"""Collect ds004511 H5 into article tables. No task contrasts."""
from __future__ import annotations

import argparse
import inspect
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ds04511_common import (
    ARTICLE_DIR,
    DEFAULT_CONFIG,
    DEFAULT_H5_ROOT,
    EXPECTED_N_H5,
    EXPECTED_N_SUBJECTS,
    PINNED_RELATIVE,
    PINNED_SHA256,
    assert_fresh_output,
    pin_source_bundle,
    sha256_file,
    write_json,
)
from ds04511_g0_inventory import build_inventory
from ds04511_g1_labels import assign_labels, label_audit
from ds04511_g2_support import build_support_table, support_audit

RECORDING_TABLE_COLUMNS = (
    "subject_id",
    "session",
    "run",
    "run_index",
    "task_label",
    "task_label_status",
    "task_label_source",
    "source_h5",
    "relative_path",
    "sha256",
    "h5_condition",
    "h5_task",
    "h5_group",
    "h5_stem_task_agree",
    "label_join_status",
    "n_timepoints",
    "time_start_sec",
    "time_end_sec",
    "modal_dt_sec",
    "regular_grid",
    "has_nonpositive_dt",
    "feature_fit_scopes",
    "provenance__normalization__status",
    "provenance__anchoring__primary_coordinate_contract",
    "diffusion_computation_status",
    "diffusion_n_valid",
    "diffusion_valid_fraction",
    "h1_h2_support_included",
    "h1_h2_support_reason",
    "h1_h2_psd_floor_excluded_included",
    "jacobian__derived_metrics__v1__computation_status",
    "stochastic_reachability__v1__primary__computation_status",
)


def _code_provenance() -> dict[str, Any]:
    modules = {
        "collect": sys.modules[__name__],
    }
    files = {}
    for name, module in modules.items():
        path = inspect.getsourcefile(module)
        if path:
            resolved = Path(path).resolve()
            files[name] = {"path": str(resolved), "sha256": sha256_file(resolved)}
    return files


def collect(
    *,
    h5_root: Path,
    output_root: Path,
    config_path: Path,
    skip_ingest: bool = True,
) -> dict[str, Any]:
    h5_root = h5_root.resolve()
    output_root = output_root.resolve()
    config_path = config_path.resolve()
    assert_fresh_output(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    pin = pin_source_bundle(h5_root)
    files = pin["files"]
    inventory = build_inventory(files, root=h5_root)
    inventory.to_csv(output_root / "g0_file_inventory.csv", index=False)
    write_json(output_root / "g0_sidecar_hashes.json", pin["sidecar_sha256"])

    labeled = assign_labels(inventory)
    g1_report = label_audit(labeled)
    labeled.to_csv(output_root / "g1_recording_labels.csv", index=False)
    write_json(output_root / "g1_label_audit.json", g1_report)

    support = build_support_table(files)
    g2_report = support_audit(support)
    support.to_csv(output_root / "g2_recording_support.csv", index=False)
    write_json(output_root / "g2_support_audit.json", g2_report)

    recording = labeled.merge(
        support.drop(columns=["stem"], errors="ignore"),
        on="source_h5",
        how="left",
        suffixes=("", "_support"),
    )
    present = [column for column in RECORDING_TABLE_COLUMNS if column in recording.columns]
    recording[present].to_csv(output_root / "recording_table.csv", index=False)

    n_subjects = int(inventory["subject_id"].nunique()) if not inventory.empty else 0
    manifest = {
        "schema": "ds004511_ndt_v1.collection.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_status": "no_biological_claim",
        "scientific_qualification": "not_assessed",
        "confirmatory_contrasts": False,
        "h5_root": str(h5_root),
        "n_h5": int(len(files)),
        "n_subjects": n_subjects,
        "expected_n_h5": EXPECTED_N_H5,
        "expected_n_subjects": EXPECTED_N_SUBJECTS,
        "pinned_relative": PINNED_RELATIVE,
        "pinned_sha256": PINNED_SHA256,
        "gates": {
            "G0": "pass" if len(files) == EXPECTED_N_H5 and n_subjects == EXPECTED_N_SUBJECTS else "fail",
            "G1": g1_report.get("status"),
            "G2": g2_report.get("status"),
            "G3": "synthetic_helpers_only; independent code review not run",
            "G4": "not_locked",
        },
        "g1": g1_report,
        "g2": g2_report,
        "ingest_status": "skipped" if skip_ingest else "not_implemented",
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path) if config_path.is_file() else None,
        "runtime": {"python": sys.version, "platform": platform.platform()},
        "code_provenance": _code_provenance(),
        "note": (
            "Collection writes identity, stem task labels, and support. "
            "It does not compute paired task contrasts, sign tests, effect sizes or classifiers. "
            "Parquet ingest is not part of this first cut; contrasts read H5 directly."
        ),
    }
    write_json(output_root / "collection_manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_H5_ROOT)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ARTICLE_DIR / "results" / "ingest_20260921",
    )
    parser.add_argument("--skip-ingest", action="store_true", default=True)
    args = parser.parse_args(argv)
    if args.config.is_file():
        raw = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
        if raw.get("expected_source", {}).get("confirmatory_contrasts"):
            raise SystemExit("config must not enable confirmatory contrasts during collection")
    manifest = collect(
        h5_root=args.input_root,
        output_root=args.output_root,
        config_path=args.config,
        skip_ingest=args.skip_ingest,
    )
    print(json.dumps({
        "output_root": str(args.output_root),
        "n_h5": manifest.get("n_h5"),
        "gates": manifest.get("gates"),
        "ingest_status": manifest.get("ingest_status"),
        "g1_status": (manifest.get("g1") or {}).get("status"),
        "confirmatory_contrasts": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
