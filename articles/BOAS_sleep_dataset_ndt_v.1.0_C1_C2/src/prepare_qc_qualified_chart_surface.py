from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ARTICLE = Path(r"J:\repos\nmd-analysis\articles\BOAS_sleep_dataset_ndt_v.1.0_C1_C2")
SOURCE_ARTICLE = Path(r"J:\repos\nmd-analysis\articles\BOAS_sleep_dataset_ndt._v.1.0")
SOURCE_CHART_ROOT = SOURCE_ARTICLE / "results" / "fold_safe_chart_qualification_20260930_v1"
SOURCE_SUPPORT_ROOT = SOURCE_ARTICLE / "results" / "continuous_full_surface_support_audit_20260929_v4"
OVERLAP_ROOT = ARTICLE / "results" / "full_surface_quality_overlap_audit_20261001_v2"
OUTPUT_ROOT = ARTICLE / "results" / "qc_qualified_fold_safe_chart_replay_20261002_v2"
FEATURE_SOURCE = SOURCE_SUPPORT_ROOT / "features_primary_ppg.parquet"
OVERLAP_SOURCE = OVERLAP_ROOT / "apply_h5_quality_overlap_rows.csv"
FILE_INDEX_SOURCE = SOURCE_CHART_ROOT / "processed" / "ds005555" / "file_index.csv"


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
    if OUTPUT_ROOT.exists():
        require(not (OUTPUT_ROOT / "provenance" / "input_manifest.json").exists(), f"Preparation manifest already exists in {OUTPUT_ROOT}")
    else:
        OUTPUT_ROOT.mkdir(parents=True)
    for path in (FEATURE_SOURCE, OVERLAP_SOURCE, FILE_INDEX_SOURCE):
        require(path.is_file(), f"Missing input: {path}")

    processed_dataset = OUTPUT_ROOT / "processed" / "ds005555"
    configs_dir = OUTPUT_ROOT / "configs"
    provenance_dir = OUTPUT_ROOT / "provenance"
    processed_dataset.mkdir(parents=True, exist_ok=True)
    configs_dir.mkdir(parents=True, exist_ok=True)
    provenance_dir.mkdir(parents=True, exist_ok=True)

    # The overlap ledger contains support metadata only; no chart values or stages.
    overlaps = pd.read_csv(OVERLAP_SOURCE, dtype={"file": "string", "quality_kinds": "string"})
    required_overlap_columns = {
        "fold", "pid", "bids_subject", "file", "epoch_id", "actual_source_time_start_sec",
        "actual_source_time_end_sec", "support_primary_surface_eligible", "included_in_apply_h5",
        "quality_kinds", "overlapping_quality_interval_bounds",
    }
    require(required_overlap_columns.issubset(overlaps.columns), "Overlap ledger schema changed")
    require(len(overlaps) == 4, f"Expected four reviewed overlap rows, found {len(overlaps)}")
    require(not overlaps.duplicated(["file", "epoch_id"]).any(), "Duplicate QC exclusion keys")
    require(overlaps["support_primary_surface_eligible"].astype(bool).all(), "Overlap rows are no longer primary eligible")
    require(overlaps["included_in_apply_h5"].astype(bool).all(), "Overlap rows are no longer in old apply H5")
    require(overlaps["quality_kinds"].eq("raw_joint_eeg_flatline").all(), "Unexpected quality type in exclusion set")

    features = pd.read_parquet(FEATURE_SOURCE)
    keys = ["file", "epoch_id"]
    require(set(keys + ["actual_source_time_start_sec", "actual_source_time_end_sec"]).issubset(features.columns), "Feature support columns missing")
    features["file"] = features["file"].astype(str).map(lambda x: Path(x.replace("\\", "/")).name)
    features["epoch_id"] = pd.to_numeric(features["epoch_id"], errors="raise").astype("int64")
    overlaps["file"] = overlaps["file"].astype(str).map(lambda x: Path(x.replace("\\", "/")).name)
    overlaps["epoch_id"] = pd.to_numeric(overlaps["epoch_id"], errors="raise").astype("int64")
    require(not features.duplicated(keys).any(), "Duplicate source feature keys")
    merged = overlaps.merge(features[keys + ["actual_source_time_start_sec", "actual_source_time_end_sec"]], on=keys, how="left", validate="one_to_one", suffixes=("_ledger", "_feature"), indicator=True)
    require(merged["_merge"].eq("both").all(), "At least one QC overlap row is absent from the source feature table")
    for row in merged.itertuples(index=False):
        start = float(row.actual_source_time_start_sec_feature)
        end = float(row.actual_source_time_end_sec_feature)
        intervals: Any = json.loads(row.overlapping_quality_interval_bounds)
        require(pd.notna(start) and pd.notna(end) and end > start, f"Invalid contributor bounds for {row.file}/{row.epoch_id}")
        require(isinstance(intervals, list) and intervals, f"No source-quality intervals for {row.file}/{row.epoch_id}")
        require(any(float(item["start_sec"]) < end and start < float(item["end_sec"]) for item in intervals), f"Ledger overlap does not intersect contributor bounds for {row.file}/{row.epoch_id}")

    exclusion_keys = set(zip(overlaps["file"], overlaps["epoch_id"]))
    keep = [(name, int(epoch)) not in exclusion_keys for name, epoch in zip(features["file"], features["epoch_id"])]
    filtered = features.loc[keep].copy()
    require(len(features) - len(filtered) == len(exclusion_keys), "Filter did not remove exactly the reviewed keys")
    require(filtered["file"].nunique() == features["file"].nunique(), "QC filtering removed a recording entirely")
    # MNDM 53bae391 treats numeric epoch_id == 0 as missing in `value or ""`.
    # Keep identity values unchanged while serializing the identifier as text so
    # epoch zero survives fold-safe support-ledger matching.
    filtered["epoch_id"] = filtered["epoch_id"].astype("string")

    output_features = processed_dataset / "features.parquet"
    if output_features.exists():
        existing_keys = pd.read_parquet(output_features, columns=keys)
        existing_keys["file"] = existing_keys["file"].astype(str).map(lambda x: Path(x.replace("\\", "/")).name)
        existing_keys["epoch_id"] = pd.to_numeric(existing_keys["epoch_id"], errors="raise").astype("int64")
        expected_keys = filtered[keys].copy()
        expected_keys["epoch_id"] = pd.to_numeric(expected_keys["epoch_id"], errors="raise").astype("int64")
        require(set(map(tuple, existing_keys[keys].itertuples(index=False, name=None))) == set(map(tuple, expected_keys.itertuples(index=False, name=None))), "Existing filtered feature table keys differ from QC-filtered source keys")
    else:
        filtered.to_parquet(output_features, index=False, compression="zstd")
    exclusion_registry_path = provenance_dir / "qc_excluded_epoch_registry.csv"
    if not exclusion_registry_path.exists():
        overlaps.to_csv(exclusion_registry_path, index=False)

    # Restrict the metadata file index to the exact 100 input recordings.
    index = pd.read_csv(FILE_INDEX_SOURCE, dtype="string", keep_default_na=False)
    require("path" in index.columns and "subject" in index.columns, "Source file index schema changed")
    index["_basename"] = index["path"].map(lambda x: Path(str(x).replace("\\", "/")).name)
    expected_files = set(features["file"].unique())
    selected_index = index[index["_basename"].isin(expected_files)].drop(columns="_basename").copy()
    require(len(selected_index) == len(expected_files), "File index is not one row per feature recording")
    require(set(Path(str(p).replace("\\", "/")).name for p in selected_index["path"]) == expected_files, "File index keys differ from feature table")
    filtered_index_path = processed_dataset / "file_index.csv"
    if not filtered_index_path.exists():
        selected_index.to_csv(filtered_index_path, index=False, quoting=csv.QUOTE_MINIMAL)

    anchor_base = "ds005555_continuous_c123_fold_{fold}_chart_label_free_qc_v1"
    run_names = {}
    for fold in range(5):
        for role, suffix in (("training", "training"), ("apply", "apply")):
            source_version = "v2" if fold == 0 else "v1"
            source_config = SOURCE_CHART_ROOT / "configs" / f"fold_{fold}_{suffix}_label_free_{source_version}.yaml"
            require(source_config.is_file(), f"Missing source chart config: {source_config}")
            config = yaml.safe_load(source_config.read_text(encoding="utf-8"))
            run_name = f"fold_{fold}_{suffix}_qc_v1"
            run_names[f"fold_{fold}_{role}"] = run_name
            config["paths"]["processed_dir"] = str(OUTPUT_ROOT / "processed").replace("\\", "/")
            projection = config["mnps_projection"]
            projection["fold_safe"]["role"] = role
            anchor_id = anchor_base.format(fold=fold)
            projection["anchor_auto_fit"]["anchor_id"] = anchor_id
            if role == "training":
                projection["anchor_auto_fit"]["enabled"] = True
                projection["anchor"]["enabled"] = False
            else:
                projection["anchor_auto_fit"]["enabled"] = False
                projection["anchor"]["enabled"] = True
                projection["anchor"]["path"] = str(
                    processed_dataset / f"fold_{fold}_training_qc_v1" / "anchors" / f"{anchor_id}.json"
                ).replace("\\", "/")
            config_path = configs_dir / f"{run_name}.yaml"
            serialized_config = yaml.safe_dump(config, sort_keys=False, allow_unicode=True)
            if config_path.exists():
                require(yaml.safe_load(config_path.read_text(encoding="utf-8")) == config, f"Existing config differs from generated config: {config_path}")
            else:
                config_path.write_text(serialized_config, encoding="utf-8")

    manifest = {
        "schema_version": "boas.qc_qualified_fold_safe_chart_replay_input.v2",
        "scope": "outcome-blind chart-input preparation; no stages, predictions, scores, or effects",
        "source_feature_table": str(FEATURE_SOURCE),
        "source_feature_table_sha256": sha256(FEATURE_SOURCE),
        "source_feature_rows": int(len(features)),
        "filtered_feature_table": str(output_features),
        "filtered_feature_table_sha256": sha256(output_features),
        "filtered_feature_rows": int(len(filtered)),
        "recordings": int(filtered["file"].nunique()),
        "removed_rows": int(len(features) - len(filtered)),
        "epoch_id_representation": "string identifier; numeric values unchanged, preserving epoch 0 through MNDM fold-safe selection",
        "qc_exclusion_registry": str(provenance_dir / "qc_excluded_epoch_registry.csv"),
        "qc_exclusion_registry_sha256": sha256(exclusion_registry_path),
        "qc_overlap_source": str(OVERLAP_SOURCE),
        "qc_overlap_source_sha256": sha256(OVERLAP_SOURCE),
        "source_file_index_sha256": sha256(FILE_INDEX_SOURCE),
        "filtered_file_index_sha256": sha256(processed_dataset / "file_index.csv"),
        "training_policy": "Re-fit each fold anchor after global removal of every apply-surface row intersecting an audited raw_joint_eeg_flatline interval.",
        "fold_runs": run_names,
        "chart_values_read_by_preparation": False,
        "future_values_scored": False,
        "outcomes_calculated": False,
    }
    (provenance_dir / "input_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
