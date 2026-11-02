from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ARTICLE = Path(r"J:\repos\nmd-analysis\articles\BOAS_sleep_dataset_ndt_v.1.0_C1_C2")
CANDIDATE_ROOT = ARTICLE / "results" / "qc_qualified_fold_safe_chart_replay_20261002_v2"
CANDIDATE_SPLIT_ROOT = Path(r"J:\repos\nmd-analysis\articles\BOAS_sleep_dataset_ndt._v.1.0\results\continuous_full_surface_support_audit_20260929_v4\fold_manifests")
CLEAN_CHECKOUT = Path(r"C:\Users\Robin\.codex\worktrees\boas-support-pilot\NeuralManifoldDynamics")
EXPECTED_MNDM_REVISION = "53bae391015a5bad51b8013c312745a8d90e52f5"
MNDM_MODULE_PATH = CLEAN_CHECKOUT / "mndm" / "src"
CORE_MODULE_PATH = CLEAN_CHECKOUT / "core" / "src"
N_FOLDS = 5
N_JOBS = 4
OLD_H5_MEDIAN_BYTES = 151_597_856
ESTIMATED_TOTAL_H5 = 500 * OLD_H5_MEDIAN_BYTES
SPACE_MARGIN_BYTES = 5 * 1024**3


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def build_runtime_config(source: Path, target_config: Path, processed_root: Path, dataset_root: Path, fold: int, role: str) -> dict[str, Any]:
    config = yaml.safe_load(source.read_text(encoding="utf-8"))
    require(isinstance(config, dict), f"Malformed YAML config: {source}")
    projection = config["mnps_projection"]
    require(projection["fold_safe"]["role"] == role, f"Unexpected fold role in source config: {source}")
    config["paths"]["processed_dir"] = str(processed_root).replace("\\", "/")
    anchor_id = projection["anchor_auto_fit"]["anchor_id"]
    if role == "training":
        require(projection["anchor_auto_fit"]["enabled"] is True, f"Training anchor fit disabled in {source}")
        require(projection["anchor"]["enabled"] is False, f"Training config unexpectedly applies an anchor: {source}")
    else:
        require(projection["anchor_auto_fit"]["enabled"] is False, f"Apply config unexpectedly fits an anchor: {source}")
        require(projection["anchor"]["enabled"] is True, f"Apply config has no external anchor: {source}")
        projection["anchor"]["path"] = str(
            dataset_root / f"fold_{fold}_training_qc_v1" / "anchors" / f"{anchor_id}.json"
        ).replace("\\", "/")
    serialized = yaml.safe_dump(config, sort_keys=False, allow_unicode=True)
    if target_config.exists():
        existing = yaml.safe_load(target_config.read_text(encoding="utf-8"))
        require(existing == config, f"Existing runtime config differs: {target_config}")
    return config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the five fold QC-filtered BOAS chart replay without scoring outcomes.")
    parser.add_argument("--data-root", type=Path, required=True, help="Isolated output root on a volume with enough free space.")
    parser.add_argument("--plan-only", action="store_true", help="Check inputs/configs/free space without creating outputs or running MNDM.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_root = args.data_root.expanduser().resolve()
    processed_root = data_root / "processed"
    dataset_root = processed_root / "ds005555"
    control_root = data_root / "control"
    config_root = control_root / "configs"
    log_root = data_root / "logs"
    candidate_manifest_path = CANDIDATE_ROOT / "provenance" / "input_manifest.json"
    support_preflight_path = CANDIDATE_ROOT / "provenance" / "fold_support_metadata_preflight.json"
    candidate_feature_path = CANDIDATE_ROOT / "processed" / "ds005555" / "features.parquet"
    candidate_index_path = CANDIDATE_ROOT / "processed" / "ds005555" / "file_index.csv"
    source_configs = CANDIDATE_ROOT / "configs"
    require(candidate_manifest_path.is_file() and candidate_feature_path.is_file() and candidate_index_path.is_file(), "Prepared candidate inputs are incomplete.")
    candidate_manifest = json.loads(candidate_manifest_path.read_text(encoding="utf-8"))
    source_feature_hash = str(candidate_manifest["filtered_feature_table_sha256"])
    require(sha256(candidate_feature_path) == source_feature_hash, "Prepared feature table hash differs from input manifest.")
    require(support_preflight_path.is_file(), "Fold support metadata preflight is missing.")
    support_preflight = json.loads(support_preflight_path.read_text(encoding="utf-8"))
    require(support_preflight.get("schema_version") == "boas.qc_filtered_fold_support_metadata_preflight.v1", "Unexpected support preflight schema.")
    require(support_preflight.get("candidate_input_manifest_sha256") == sha256(candidate_manifest_path), "Support preflight belongs to a different input manifest.")
    require(support_preflight.get("candidate_feature_table_sha256") == source_feature_hash, "Support preflight belongs to a different feature table.")
    support_folds = support_preflight.get("folds", [])
    require(len(support_folds) == N_FOLDS, "Support preflight does not contain all five folds.")
    require(
        all(
            int(item["fold"]) == fold
            and item["status"] == "verified_no_shared_source_samples"
            and int(item["training_rows"]) == int(item["training_rows_support_verified"])
            and int(item["apply_rows"]) == int(item["apply_rows_support_verified"])
            and item["epoch_zero_selected"] is True
            and int(item["training_rows"]) + int(item["apply_rows"]) == int(candidate_manifest["filtered_feature_rows"])
            for fold, item in enumerate(support_folds)
        ),
        "One or more fold support preflight checks failed.",
    )
    expected_recordings_by_fold: dict[int, dict[str, int]] = {}
    for fold in range(N_FOLDS):
        split_path = CANDIDATE_SPLIT_ROOT / f"fold_{fold}.json"
        require(split_path.is_file(), f"Missing split manifest: {split_path}")
        split_payload = json.loads(split_path.read_text(encoding="utf-8"))
        expected_counts = {
            "training": len({str(row["recording_id"]) for row in split_payload["training_ranges"]}),
            "apply": len({str(row["recording_id"]) for row in split_payload["apply_ranges"]}),
        }
        require(
            sum(expected_counts.values()) == int(candidate_manifest["recordings"]),
            f"Fold {fold} split does not account for every candidate recording.",
        )
        expected_recordings_by_fold[fold] = expected_counts
    require(CLEAN_CHECKOUT.is_dir() and (MNDM_MODULE_PATH / "mndm" / "cli.py").is_file(), "Clean MNDM worktree or CLI is missing.")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=CLEAN_CHECKOUT, text=True).strip()
    require(revision == EXPECTED_MNDM_REVISION, f"MNDM checkout changed: expected {EXPECTED_MNDM_REVISION}, found {revision}")
    free_bytes = shutil.disk_usage(Path(data_root.anchor)).free
    required_bytes = ESTIMATED_TOTAL_H5 + SPACE_MARGIN_BYTES
    require(free_bytes >= required_bytes, f"Insufficient disk space: {free_bytes} bytes free; about {required_bytes} bytes required with margin.")

    runtime_configs: dict[str, dict[str, Any]] = {}
    runtime_config_objects: dict[str, dict[str, Any]] = {}
    for fold in range(N_FOLDS):
        for role, suffix in (("training", "training"), ("apply", "apply")):
            run_name = f"fold_{fold}_{suffix}_qc_v1"
            source_config = source_configs / f"{run_name}.yaml"
            require(source_config.is_file(), f"Missing candidate config: {source_config}")
            target_config = config_root / f"{run_name}.yaml"
            config = build_runtime_config(source_config, target_config, processed_root, dataset_root, fold, role)
            serialized_config = yaml.safe_dump(config, sort_keys=False, allow_unicode=True)
            runtime_config_objects[run_name] = config
            runtime_configs[run_name] = {
                "path": str(target_config),
                "sha256": sha256_text(serialized_config),
                "role": role,
                "fold": fold,
                "expected_h5": expected_recordings_by_fold[fold][role],
            }

    plan = {
        "data_root": str(data_root),
        "free_bytes": free_bytes,
        "estimated_h5_bytes": ESTIMATED_TOTAL_H5,
        "required_bytes_with_margin": required_bytes,
        "input_feature_sha256": source_feature_hash,
        "support_preflight_sha256": sha256(support_preflight_path),
        "input_feature_rows": candidate_manifest["filtered_feature_rows"],
        "input_recordings": candidate_manifest["recordings"],
        "mndm_revision": revision,
        "runs": runtime_configs,
        "outcome_scores": False,
    }
    if args.plan_only:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0

    marker_path = data_root / "control" / "replay_input_marker.json"
    status_path = data_root / "control" / "replay_status.json"
    article_status_path = CANDIDATE_ROOT / "provenance" / "chart_replay_execution_status.json"
    if data_root.exists():
        if marker_path.is_file():
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
            require(marker.get("input_feature_sha256") == source_feature_hash, "Existing replay root belongs to a different input surface.")
        else:
            expected_config_paths = {Path(item["path"]).resolve() for item in runtime_configs.values()}
            actual_files = {path.resolve() for path in data_root.rglob("*") if path.is_file()}
            actual_dirs = {path.resolve() for path in data_root.rglob("*") if path.is_dir()}
            expected_dirs = {control_root.resolve(), config_root.resolve()}
            config_hashes_match = all(
                Path(item["path"]).is_file()
                and sha256_text(Path(item["path"]).read_text(encoding="utf-8")) == item["sha256"]
                for item in runtime_configs.values()
            )
            generated_config_bootstrap = (
                actual_files == expected_config_paths
                and actual_dirs == expected_dirs
                and config_hashes_match
            )
            require(
                not any(data_root.iterdir()) or generated_config_bootstrap,
                f"Refusing to reuse non-empty unmarked output root: {data_root}",
            )
    else:
        data_root.mkdir(parents=True)
    control_root.mkdir(parents=True, exist_ok=True)

    marker = {
        "schema_version": "boas.qc_filtered_fold_chart_replay_input_marker.v2",
        "candidate_manifest": str(candidate_manifest_path),
        "candidate_manifest_sha256": sha256(candidate_manifest_path),
        "input_feature_sha256": source_feature_hash,
        "support_preflight_sha256": sha256(support_preflight_path),
        "input_file_index_sha256": candidate_manifest["filtered_file_index_sha256"],
        "qc_exclusion_registry_sha256": candidate_manifest["qc_exclusion_registry_sha256"],
        "mndm_checkout": str(CLEAN_CHECKOUT),
        "mndm_revision": revision,
        "runtime_configs": {name: item["sha256"] for name, item in runtime_configs.items()},
        "raw_edf_copied": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    if marker_path.exists():
        prior_marker = json.loads(marker_path.read_text(encoding="utf-8"))
        require(prior_marker.get("input_feature_sha256") == marker["input_feature_sha256"], "Replay input marker mismatch.")
        require(prior_marker.get("runtime_configs") == marker["runtime_configs"], "Replay runtime configs differ from marker.")
    else:
        write_json(marker_path, marker)

    dataset_root.mkdir(parents=True, exist_ok=True)
    log_root.mkdir(parents=True, exist_ok=True)

    for run_name, config in runtime_config_objects.items():
        target_config = Path(runtime_configs[run_name]["path"])
        serialized_config = yaml.safe_dump(config, sort_keys=False, allow_unicode=True)
        if target_config.exists():
            require(
                sha256_text(target_config.read_text(encoding="utf-8")) == runtime_configs[run_name]["sha256"],
                f"Existing runtime config hash differs: {target_config}",
            )
        else:
            target_config.parent.mkdir(parents=True, exist_ok=True)
            target_config.write_text(serialized_config, encoding="utf-8")

    for source, target, expected_hash in (
        (candidate_feature_path, dataset_root / "features.parquet", source_feature_hash),
        (candidate_index_path, dataset_root / "file_index.csv", candidate_manifest["filtered_file_index_sha256"]),
    ):
        if target.exists():
            require(sha256(target) == expected_hash, f"Existing replay input has changed: {target}")
        else:
            shutil.copy2(source, target)
            require(sha256(target) == expected_hash, f"Copied replay input hash mismatch: {target}")

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = os.pathsep.join((str(MNDM_MODULE_PATH), str(CORE_MODULE_PATH)))
    state: dict[str, Any] = {
        "schema_version": "boas.qc_filtered_fold_chart_replay_progress.v1",
        "status": "RUNNING",
        "data_root": str(data_root),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "mndm_revision": revision,
        "input_feature_sha256": source_feature_hash,
        "runs": [],
        "outcome_scores_calculated": False,
        "effects_calculated": False,
    }
    write_json(status_path, state)
    write_json(article_status_path, {
        "schema_version": "boas.qc_filtered_fold_safe_chart_replay_status.v1",
        "status": "RUNNING",
        "data_root": str(data_root),
        "input_feature_sha256": source_feature_hash,
        "outcome_scores_calculated": False,
        "effects_calculated": False,
        "progress_path": str(status_path),
        "runs_completed": 0,
        "runs_total": 10,
    })

    for fold in range(N_FOLDS):
        for role, suffix in (("training", "training"), ("apply", "apply")):
            run_name = f"fold_{fold}_{suffix}_qc_v1"
            run_dir = dataset_root / run_name
            run_dir.mkdir(parents=True, exist_ok=True)
            config_path = Path(runtime_configs[run_name]["path"])
            run_manifest_path = run_dir / "run_manifest.json"
            expected_h5 = int(runtime_configs[run_name]["expected_h5"])
            existing_h5 = list(run_dir.rglob("*.h5"))
            existing_manifest: dict[str, Any] | None = None
            if run_manifest_path.is_file():
                existing_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
            if existing_manifest and existing_manifest.get("extra", {}).get("run_status") == "completed" and len(existing_h5) == expected_h5:
                record = {
                    "run_name": run_name,
                    "fold": fold,
                    "role": role,
                    "status": "reused_completed",
                    "h5_count": len(existing_h5),
                    "h5_bytes": sum(p.stat().st_size for p in existing_h5),
                    "run_manifest_sha256": sha256(run_manifest_path),
                }
                state["runs"].append(record)
                write_json(status_path, state)
                write_json(article_status_path, {**state, "progress_path": str(status_path), "runs_completed": len(state["runs"]), "runs_total": 10})
                continue

            anchor_path = None
            if role == "apply":
                anchor_id = yaml.safe_load(config_path.read_text(encoding="utf-8"))["mnps_projection"]["anchor"]["path"]
                anchor_path = Path(anchor_id)
                require(anchor_path.is_file(), f"Fold {fold} training anchor missing before apply run: {anchor_path}")

            state.update({"current_run": run_name, "current_run_started_at_utc": datetime.now(timezone.utc).isoformat()})
            write_json(status_path, state)
            write_json(article_status_path, {**state, "progress_path": str(status_path), "runs_completed": len(state["runs"]), "runs_total": 10})
            log_path = log_root / f"{run_name}.log"
            command = [
                sys.executable,
                "-m", "mndm.cli", "summarize",
                "--dataset", "ds005555",
                "--config", str(config_path),
                "--out-dir", str(processed_root),
                "--resume-run", str(run_dir),
                "--n-jobs", str(N_JOBS),
            ]
            started = time.monotonic()
            with log_path.open("w", encoding="utf-8", newline="\n") as log_stream:
                process = subprocess.run(command, cwd=CLEAN_CHECKOUT, env=env, stdout=log_stream, stderr=subprocess.STDOUT, check=False)
            elapsed = time.monotonic() - started
            if process.returncode != 0:
                failed = {
                    "run_name": run_name,
                    "fold": fold,
                    "role": role,
                    "status": "failed",
                    "exit_code": process.returncode,
                    "elapsed_seconds": elapsed,
                    "log_path": str(log_path),
                    "h5_count_at_failure": len(list(run_dir.rglob("*.h5"))),
                }
                state["runs"].append(failed)
                state["status"] = "FAILED"
                state["failed_run"] = run_name
                write_json(status_path, state)
                write_json(article_status_path, {**state, "progress_path": str(status_path), "runs_completed": len(state["runs"])-1, "runs_total": 10})
                print(json.dumps(failed, indent=2, ensure_ascii=False), flush=True)
                return process.returncode or 1

            run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
            actual_h5 = list(run_dir.rglob("*.h5"))
            require(run_manifest.get("extra", {}).get("run_status") == "completed", f"MNDM run is not marked completed: {run_name}")
            require(len(actual_h5) == expected_h5, f"Unexpected H5 count for {run_name}: {len(actual_h5)} != {expected_h5}")
            record = {
                "run_name": run_name,
                "fold": fold,
                "role": role,
                "status": "completed",
                "h5_count": len(actual_h5),
                "h5_bytes": sum(p.stat().st_size for p in actual_h5),
                "elapsed_seconds": elapsed,
                "log_path": str(log_path),
                "run_manifest_sha256": sha256(run_manifest_path),
                "anchor_path": str(anchor_path) if anchor_path else str(run_dir / "anchors"),
                "anchor_sha256": sha256(anchor_path) if anchor_path and anchor_path.is_file() else None,
            }
            state["runs"].append(record)
            state.pop("current_run", None)
            state.pop("current_run_started_at_utc", None)
            write_json(status_path, state)
            write_json(article_status_path, {**state, "progress_path": str(status_path), "runs_completed": len(state["runs"]), "runs_total": 10})
            print(json.dumps(record, indent=2, ensure_ascii=False), flush=True)

    state["status"] = "COMPLETED"
    state["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    state["total_h5_count"] = sum(int(run.get("h5_count", 0)) for run in state["runs"])
    state["total_h5_bytes"] = sum(int(run.get("h5_bytes", 0)) for run in state["runs"])
    write_json(status_path, state)
    write_json(article_status_path, {**state, "progress_path": str(status_path), "runs_completed": 10, "runs_total": 10})
    print(json.dumps(state, indent=2, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
