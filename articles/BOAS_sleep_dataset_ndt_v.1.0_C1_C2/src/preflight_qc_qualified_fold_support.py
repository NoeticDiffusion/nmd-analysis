from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ARTICLE = Path(r"J:\repos\nmd-analysis\articles\BOAS_sleep_dataset_ndt_v.1.0_C1_C2")
CANDIDATE_ROOT = ARTICLE / "results" / "qc_qualified_fold_safe_chart_replay_20261002_v2"
SOURCE_SUPPORT_ROOT = Path(
    r"J:\repos\nmd-analysis\articles\BOAS_sleep_dataset_ndt._v.1.0\results\continuous_full_surface_support_audit_20260929_v4"
)
CLEAN_CHECKOUT = Path(r"C:\Users\Robin\.codex\worktrees\boas-support-pilot\NeuralManifoldDynamics")
EXPECTED_MNDM_REVISION = "53bae391015a5bad51b8013c312745a8d90e52f5"
OUTPUT_PATH = CANDIDATE_ROOT / "provenance" / "fold_support_metadata_preflight.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    sys.path[:0] = [str(CLEAN_CHECKOUT / "mndm" / "src"), str(CLEAN_CHECKOUT / "core" / "src")]
    from mndm.pipeline.fold_safe import (
        load_fold_split,
        load_signal_support_ledger,
        select_fold_rows,
        validate_fold_signal_support,
    )

    feature_path = CANDIDATE_ROOT / "processed" / "ds005555" / "features.parquet"
    manifest_path = CANDIDATE_ROOT / "provenance" / "input_manifest.json"
    require(feature_path.is_file() and manifest_path.is_file(), "Candidate input table or manifest is missing.")
    input_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(input_manifest.get("schema_version") == "boas.qc_qualified_fold_safe_chart_replay_input.v2", "Candidate input manifest is not v2.")
    require(sha256(feature_path) == input_manifest["filtered_feature_table_sha256"], "Candidate feature table hash differs from manifest.")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=CLEAN_CHECKOUT, text=True).strip()
    require(revision == EXPECTED_MNDM_REVISION, f"MNDM revision changed: {revision}")

    # Load only fields needed to bind fold membership to the source-support ledger.
    features = pd.read_parquet(feature_path, columns=["subject", "file", "epoch_id", "t_start", "t_end"])
    require(pd.api.types.is_string_dtype(features["epoch_id"].dtype), "epoch_id must be serialized as a string identifier.")
    require(features["epoch_id"].eq("0").any(), "String-form epoch zero is absent from candidate inputs.")
    ledger_path = SOURCE_SUPPORT_ROOT / "signal_support_ledger.json"
    summaries: list[dict[str, Any]] = []
    for fold in range(5):
        split_path = SOURCE_SUPPORT_ROOT / "fold_manifests" / f"fold_{fold}.json"
        split = load_fold_split(split_path)
        ledger = load_signal_support_ledger(
            ledger_path,
            expected_sha256=split.payload["signal_support_ledger_sha256"],
        )
        training = select_fold_rows(features, split, "training")
        apply = select_fold_rows(features, split, "apply")
        validation = validate_fold_signal_support(training, apply, split, ledger)
        summaries.append(
            {
                "fold": fold,
                "training_rows": len(training.row_records),
                "apply_rows": len(apply.row_records),
                "training_rows_support_verified": validation["training_rows_verified"],
                "apply_rows_support_verified": validation["apply_rows_verified"],
                "epoch_zero_selected": any(
                    row["epoch_id"] == "0" for row in training.row_records + apply.row_records
                ),
                "status": validation["status"],
                "shared_source_sample_intersection_count": validation["shared_source_sample_intersection_count"],
                "split_manifest_sha256": split.sha256,
                "signal_support_ledger_sha256": ledger.sha256,
            }
        )

    payload = {
        "schema_version": "boas.qc_filtered_fold_support_metadata_preflight.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_input_manifest": str(manifest_path),
        "candidate_input_manifest_sha256": sha256(manifest_path),
        "candidate_feature_table_sha256": sha256(feature_path),
        "mndm_checkout": str(CLEAN_CHECKOUT),
        "mndm_revision": revision,
        "rows": int(len(features)),
        "recordings": int(features["file"].nunique()),
        "folds": summaries,
        "raw_edf_read": False,
        "chart_h5_read": False,
        "future_values_scored": False,
        "outcomes_calculated": False,
        "scope": "Fold membership and conservative feature-row support binding only; estimator history/horizon embargo is not certified.",
    }
    require(all(item["status"] == "verified_no_shared_source_samples" for item in summaries), "At least one fold failed support validation.")
    require(all(item["training_rows"] == item["training_rows_support_verified"] for item in summaries), "A fold training row was not bound to support.")
    require(all(item["apply_rows"] == item["apply_rows_support_verified"] for item in summaries), "A fold apply row was not bound to support.")
    require(all(item["epoch_zero_selected"] for item in summaries), "Epoch zero was not preserved in every fold.")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
