from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml


ARTICLE = Path(r"J:\repos\nmd-analysis\articles\BOAS_sleep_dataset_ndt_v.1.0_C1_C2")
PILOT = ARTICLE / "results" / "producer_support_pilot_20261001"
CANDIDATE = Path(r"K:\processed\boas_sleep_c1c2_qc_filtered_fold_chart_replay_20261002_v2\processed\ds005555")
REPLAY_CONTROL = Path(r"K:\processed\boas_sleep_c1c2_qc_filtered_fold_chart_replay_20261002_v2\control")
SPLIT = Path(r"J:\repos\nmd-analysis\articles\BOAS_sleep_dataset_ndt._v.1.0\results\continuous_full_surface_support_audit_20260929_v4\fold_manifests\fold_1.json")
OUT = ARTICLE / "results" / "producer_support_sidecar_export_pilot_20261002_v1"
TARGETS = ("100", "105")
EXPECTED_FEATURE_SHA256 = "139a9c5b685d2050107479d12ee8dc0070ae997ca4e1a31ecfb2af30226482c6"
EXPECTED_INDEX_SHA256 = "d7905146bd216e32104ad999ff9970f1f8fafada070d39756b776d8ccec73767"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def epoch_key(value: Any) -> str:
    return str(int(float(value)))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage a two-recording, outcome-blind sidecar export pilot.")
    parser.add_argument("--output-root", type=Path, default=OUT)
    parser.add_argument("--max-training-rows", type=int)
    parser.add_argument("--max-apply-rows", type=int)
    parser.add_argument("--pilot-index-only", action="store_true", help="Keep only the two pilot recordings in file_index.csv.")
    args = parser.parse_args()
    output_root = args.output_root.expanduser().resolve()
    candidate_features = CANDIDATE / "features.parquet"
    candidate_index = CANDIDATE / "file_index.csv"
    if sha256(candidate_features) != EXPECTED_FEATURE_SHA256:
        raise RuntimeError("candidate feature table hash differs from the recorded QC-filtered input")
    if sha256(candidate_index) != EXPECTED_INDEX_SHA256:
        raise RuntimeError("candidate file_index hash differs from the recorded QC-filtered input")
    if any(value is not None and value < 1 for value in (args.max_training_rows, args.max_apply_rows)):
        raise ValueError("row limits must be positive integers")
    if output_root.exists() and any(output_root.rglob("*")):
        raise RuntimeError(f"refusing to reuse non-empty pilot output: {output_root}")

    # Read only identities from the candidate table. Its feature/outcome-like
    # columns are not part of this export-pilot input selection.
    identity_columns = ["subject", "pid", "file", "epoch_id", "t_start", "t_end"]
    candidate_ids = pq.read_table(candidate_features, columns=identity_columns).to_pandas()
    candidate_ids = candidate_ids[candidate_ids["file"].astype(str).str.startswith(("sub-100_", "sub-105_"))].copy()
    candidate_ids["_epoch_key"] = candidate_ids["epoch_id"].map(epoch_key)
    candidate_ids["_subject_id"] = candidate_ids["subject"].astype(str)
    if candidate_ids.duplicated(["file", "_epoch_key"]).any():
        raise RuntimeError("candidate identity table has duplicate recording/epoch keys")

    fold = json.loads(SPLIT.read_text(encoding="utf-8"))
    files: list[pd.DataFrame] = []
    record_rows: list[dict[str, Any]] = []
    for sub in TARGETS:
        file_name = f"sub-{sub}_task-Sleep_acq-psg_eeg.edf"
        selected = candidate_ids[candidate_ids["file"].astype(str).eq(file_name)].copy()
        if selected.empty:
            raise RuntimeError(f"candidate identity table has no rows for {file_name}")
        subject_ids = sorted(selected["_subject_id"].unique().tolist())
        if len(subject_ids) != 1:
            raise RuntimeError(f"candidate file {file_name} maps to multiple participant IDs")
        subject_id = subject_ids[0]
        role = "training" if subject_id in fold["training_pids"] else "apply" if subject_id in fold["apply_pids"] else "missing"
        if role == "missing":
            raise RuntimeError(f"candidate participant {subject_id} is absent from fold 1")
        row_limit = args.max_training_rows if role == "training" else args.max_apply_rows
        if row_limit is not None:
            selected = selected.assign(_epoch_order=selected["epoch_id"].map(epoch_key).astype(int))
            selected = selected.sort_values("_epoch_order", kind="stable").head(row_limit).drop(columns="_epoch_order")

        source_table = PILOT / f"sub-{sub}" / "ds005555" / "features.parquet"
        source = pd.read_parquet(source_table)
        producer_rows_before_filter = int(len(source))
        source["_epoch_key"] = source["epoch_id"].map(epoch_key)
        source = source[source["file"].astype(str).eq(file_name)].copy()
        expected_epochs = set(selected["_epoch_key"])
        source = source[source["_epoch_key"].isin(expected_epochs)].copy()
        source_epochs = set(source["_epoch_key"])
        if source_epochs != expected_epochs or source.duplicated("_epoch_key").any():
            raise RuntimeError(f"raw-pilot feature rows do not exactly bind candidate keys for {file_name}")
        selected_by_epoch = selected.set_index("_epoch_key")
        source_start = source["_epoch_key"].map(selected_by_epoch["t_start"]).to_numpy(dtype=np.float64)
        source_end = source["_epoch_key"].map(selected_by_epoch["t_end"]).to_numpy(dtype=np.float64)
        if not (
            np.allclose(source["t_start"].to_numpy(dtype=np.float64), source_start, rtol=0.0, atol=1e-9)
            and np.allclose(source["t_end"].to_numpy(dtype=np.float64), source_end, rtol=0.0, atol=1e-9)
        ):
            raise RuntimeError(f"raw-pilot feature clocks differ from candidate identity keys for {file_name}")
        source["subject"] = subject_id
        source["pid"] = int(selected["pid"].iloc[0])
        # Keep epoch keys canonical and non-falsey for the downstream fold
        # selector, which otherwise turns numeric epoch 0 into an empty key.
        source["epoch_id"] = source["_epoch_key"]
        source.drop(columns=["_epoch_key"], inplace=True)
        files.append(source)
        record_rows.append({
            "file": file_name,
            "subject_id": subject_id,
            "pid": int(selected["pid"].iloc[0]),
            "fold_1_role": role,
            "candidate_identity_rows": int(len(selected)),
            "producer_feature_rows_before_key_filter": producer_rows_before_filter,
            "export_input_rows": int(len(source)),
            "sidecar_source": str(PILOT / f"sub-{sub}" / "ds005555" / "qc_artifacts" / f"{Path(file_name).stem}_qc_artifacts.json"),
        })

    roles = {row["fold_1_role"] for row in record_rows}
    if roles != {"training", "apply"}:
        raise RuntimeError(f"pilot requires one training and one apply recording; found {sorted(roles)}")

    ds_out = output_root / "processed" / "ds005555"
    qc_out = ds_out / "qc_artifacts"
    qc_out.mkdir(parents=True, exist_ok=True)
    combined = pd.concat(files, ignore_index=True)
    combined.to_parquet(ds_out / "features.parquet", index=False)
    if args.pilot_index_only:
        index_frame = pd.read_csv(candidate_index)
        pilot_basenames = {str(row["file"]) for row in record_rows}
        index_subset = index_frame[
            index_frame["path"].astype(str).map(lambda value: Path(value.replace("\\", "/")).name).isin(pilot_basenames)
        ].copy()
        if set(index_subset["path"].astype(str).map(lambda value: Path(value.replace("\\", "/")).name)) != pilot_basenames:
            raise RuntimeError("candidate file_index does not resolve exactly the two pilot recordings")
        indexed_subjects = {
            Path(str(row["path"]).replace("\\", "/")).name: int(row["subject"])
            for _, row in index_subset.iterrows()
        }
        expected_subjects = {str(row["file"]): int(row["pid"]) for row in record_rows}
        if indexed_subjects != expected_subjects:
            raise RuntimeError(f"pilot file_index subject mapping differs: {indexed_subjects} != {expected_subjects}")
        staged_index = ds_out / "file_index.csv"
        index_subset.to_csv(staged_index, index=False)
        staged_index_rows = len(index_subset)
        staged_index_scope = "two pilot recordings only"
    else:
        staged_index = ds_out / "file_index.csv"
        shutil.copy2(candidate_index, staged_index)
        staged_index_rows = len(pd.read_csv(staged_index, usecols=["path"]))
        staged_index_scope = "full QC-filtered candidate index"
    sidecar_hashes: dict[str, str] = {}
    for row in record_rows:
        source_sidecar = Path(row["sidecar_source"])
        target_sidecar = qc_out / source_sidecar.name
        shutil.copy2(source_sidecar, target_sidecar)
        sidecar_hashes[source_sidecar.name] = sha256(target_sidecar)

    config = yaml.safe_load((REPLAY_CONTROL / "configs" / "fold_1_apply_qc_v1.yaml").read_text(encoding="utf-8"))
    config["paths"]["processed_dir"] = str(output_root / "processed").replace("\\", "/")
    config_path = output_root / "control" / "fold_1_apply_support_pilot.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")

    write_json(output_root / "control" / "input_manifest.json", {
        "schema_version": "boas.c1_c2_support_sidecar_export_pilot_input.v1",
        "status": "staged",
        "scope": "two-recording MNDM fold-1 apply export plumbing pilot; no coordinate-value inspection, outcome scoring, or effects",
        "candidate_feature_table": str(candidate_features),
        "candidate_feature_table_sha256": EXPECTED_FEATURE_SHA256,
        "candidate_file_index": str(candidate_index),
        "candidate_file_index_sha256": EXPECTED_INDEX_SHA256,
        "staged_file_index": str(staged_index),
        "staged_file_index_sha256": sha256(staged_index),
        "staged_file_index_rows": int(staged_index_rows),
        "staged_file_index_scope": staged_index_scope,
        "fold_manifest": str(SPLIT),
        "fold_manifest_sha256": sha256(SPLIT),
        "source_feature_table_sha256": {
            sub: sha256(PILOT / f"sub-{sub}" / "ds005555" / "features.parquet") for sub in TARGETS
        },
        "export_input_feature_table": str(ds_out / "features.parquet"),
        "export_input_feature_table_sha256": sha256(ds_out / "features.parquet"),
        "export_input_rows": int(len(combined)),
        "epoch_id_representation": "canonical strings matching the support ledger",
        "recordings": record_rows,
        "qc_sidecar_sha256": sidecar_hashes,
        "config": str(config_path),
        "raw_edf_copied": False,
        "raw_edf_parsed_for_chart_export": False,
        "mndm_source_hash_verification_may_read_raw_edf_bytes_from_k": True,
        "candidate_numeric_columns_read_for_selection": False,
        "scores_or_effects_calculated": False,
        "row_limit_policy": {
            "training": args.max_training_rows,
            "apply": args.max_apply_rows,
            "selection_order": "ascending epoch_id when a row limit is supplied",
        },
    })
    print(json.dumps({"output_root": str(output_root), "rows": len(combined), "recordings": record_rows}, indent=2))


if __name__ == "__main__":
    main()
