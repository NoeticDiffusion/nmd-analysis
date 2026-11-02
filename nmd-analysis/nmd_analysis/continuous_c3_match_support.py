"""Pre-outcome C3 N2/Wake matched-origin support gate for qualified charts.

This driver reads only current forecast-origin chart coordinates, source/stage
support metadata, and time. It never loads future coordinates or score tables.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import h5py
import numpy as np
import pandas as pd

from .continuous_c123_estimators import (
    build_grouped_pid_manifest,
    c3_overlap_gate,
    combine_c3_matched_origins_out_of_fold,
    fit_c3_caliper,
    fit_c3_distance_transform,
    match_c3_origins,
)


_CHART_COLUMNS = ("m", "d", "e")
_UNIQUE_STAGE_STATUS = "unique_source_stage_at_origin"
_C3_CONTEXT = "human-scored N2 versus Wake at forecast origin"


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


def _require_false(payload: Mapping[str, Any], key: str, label: str) -> None:
    if payload.get(key) is not False:
        raise ValueError(f"{label} must retain {key}=false")


def _verify_declared_outputs(validation_path: Path, payload: Mapping[str, Any]) -> None:
    hashes = payload.get("output_sha256")
    output_names = payload.get("outputs", {})
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError(f"Validation has no output hash inventory: {validation_path}")
    for name, expected in hashes.items():
        if not isinstance(name, str) or not isinstance(expected, str):
            raise ValueError(f"Malformed output hash inventory: {validation_path}")
        filename = output_names.get(name, name) if isinstance(output_names, dict) else name
        if not isinstance(filename, str):
            raise ValueError(f"Malformed declared output path for {name}: {validation_path}")
        path = (validation_path.parent / filename).resolve()
        try:
            path.relative_to(validation_path.parent.resolve())
        except ValueError as exc:
            raise ValueError(f"Declared output escapes validation directory: {name}") from exc
        if not path.is_file() or _sha256(path) != expected:
            raise ValueError(f"Declared validation output is missing or changed: {name}")


def _pid_key(value: Any) -> str:
    token = str(value).strip()
    numeric = token[4:] if token.casefold().startswith("sub-") else token
    if numeric.isdigit():
        return str(int(numeric))
    return token


def _text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, np.bytes_):
        return bytes(value).decode("utf-8")
    return str(value)


def _selected_chart_payload_sha256(
    *,
    epoch_ids: np.ndarray,
    starts: np.ndarray,
    ends: np.ndarray,
    values: np.ndarray,
    geometry: np.ndarray,
    mnps_valid: np.ndarray,
    retained: np.ndarray,
    metadata: Mapping[str, str],
) -> str:
    digest = hashlib.sha256()
    digest.update(json.dumps(dict(metadata), sort_keys=True, separators=(",", ":")).encode("utf-8"))
    for name, array in (
        ("epoch_id", np.asarray(epoch_ids, dtype="<i8")),
        ("window_start", np.asarray(starts, dtype="<f8")),
        ("window_end", np.asarray(ends, dtype="<f8")),
        ("coords_3d", np.asarray(values, dtype="<f8")),
        ("geometry_valid", np.asarray(geometry, dtype=np.uint8)),
        ("mnps_3d_valid", np.asarray(mnps_valid, dtype=np.uint8)),
        ("retained_after_qc", np.asarray(retained, dtype=np.uint8)),
    ):
        digest.update(name.encode("ascii"))
        digest.update(json.dumps({"shape": array.shape, "dtype": array.dtype.str}, separators=(",", ":")).encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _read_current_chart_h5(
    path: Path,
    *,
    expected_bids_subject: str,
    expected_pid: str,
    expected_anchor_id: str,
    expected_anchor_hash: str,
    expected_file_sha256: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read and hash only the origin payload; optionally verify the full apply H5."""
    if not path.is_file():
        raise FileNotFoundError(f"Missing fold chart H5: {path}")
    file_hash = _sha256(path) if expected_file_sha256 is not None else None
    if expected_file_sha256 is not None and file_hash != expected_file_sha256:
        raise ValueError(f"Current apply H5 file hash differs from frozen support map: {path}")
    with h5py.File(path, "r") as h5:
        chart = h5.get("coords_3d_cohort_anchored")
        if chart is None or "values" not in chart or "names" not in chart:
            raise ValueError(f"Qualified 3D cohort-anchored coordinates are missing: {path}")
        names = tuple(_text(value) for value in chart["names"][:])
        if names != _CHART_COLUMNS:
            raise ValueError(f"Unexpected C3 chart axes in {path}: {names}")
        values = np.asarray(chart["values"][:], dtype=float)
        epoch_ids = np.asarray(h5["epoch_id"][:])
        starts = np.asarray(h5["window_start"][:], dtype=float)
        ends = np.asarray(h5["window_end"][:], dtype=float)
        geom = np.asarray(h5["qc/windows/geometry_valid"][:], dtype=bool)
        mnps = np.asarray(h5["qc/windows/mnps_3d_valid"][:], dtype=bool)
        retained = np.asarray(h5["qc/windows/retained_after_qc"][:], dtype=bool)

        attr_subject = _text(h5.attrs.get("meta_participant_id", ""))
        attr_pid = _pid_key(h5.attrs.get("meta_pid", ""))
        anchor_id = _text(chart.attrs.get("anchor_id", ""))
        anchor_hash = _text(chart.attrs.get("anchor_hash", ""))
        anchor_source = _text(chart.attrs.get("anchor_source", ""))
        coordinate_contract = _text(chart.attrs.get("coordinate_contract", ""))

    lengths = {len(values), len(epoch_ids), len(starts), len(ends), len(geom), len(mnps), len(retained)}
    if len(lengths) != 1 or values.ndim != 2 or values.shape[1] != len(_CHART_COLUMNS):
        raise ValueError(f"C3 chart H5 arrays have inconsistent row counts or dimensions: {path}")
    if pd.Series(epoch_ids).duplicated().any():
        raise ValueError(f"C3 chart H5 has duplicate epoch IDs: {path}")
    if attr_subject.casefold() != expected_bids_subject.casefold():
        raise ValueError(f"Chart H5 BIDS identity mismatch: {path}")
    if attr_pid != _pid_key(expected_pid):
        raise ValueError(f"Chart H5 biological PID mismatch: {path}")
    if anchor_id != expected_anchor_id or anchor_hash != expected_anchor_hash:
        raise ValueError(f"Chart H5 fold anchor does not match its frozen fold manifest: {path}")
    if anchor_source != "mndm.fold_split.training_ranges_only" or coordinate_contract != "cohort_anchored":
        raise ValueError(f"Chart H5 is not the qualified training-range-only chart: {path}")

    content_hash = _selected_chart_payload_sha256(
        epoch_ids=epoch_ids,
        starts=starts,
        ends=ends,
        values=values,
        geometry=geom,
        mnps_valid=mnps,
        retained=retained,
        metadata={
            "bids_subject": attr_subject,
            "pid": attr_pid,
            "anchor_id": anchor_id,
            "anchor_hash": anchor_hash,
            "anchor_source": anchor_source,
            "coordinate_contract": coordinate_contract,
            "chart_names": ",".join(names),
        },
    )

    result = pd.DataFrame({
        "epoch_id": pd.to_numeric(epoch_ids, errors="raise").astype("int64"),
        "h5_window_start": starts,
        "h5_window_end": ends,
        "m": values[:, 0],
        "d": values[:, 1],
        "e": values[:, 2],
        "chart3d_all_finite": np.isfinite(values).all(axis=1),
        "h5_geometry_valid": geom,
        "h5_mnps_3d_valid": mnps,
        "h5_retained_after_qc": retained,
        "coordinate_qc_valid": geom & mnps & retained & np.isfinite(values).all(axis=1),
    })
    evidence = {
        "path": str(path.resolve()),
        "container_sha256": file_hash,
        "container_sha256_verified_against_apply_map": expected_file_sha256 is not None,
        "selected_chart_payload_sha256": content_hash,
        "file_size_bytes": path.stat().st_size,
        "anchor_id": anchor_id,
        "anchor_hash": anchor_hash,
        "anchor_source": anchor_source,
        "coordinate_contract": coordinate_contract,
        "row_count": int(len(result)),
    }
    return result, evidence


def _validate_gate_inputs(
    *,
    article_root: Path,
    audit_validation_path: Path,
    replay_validation_path: Path,
    chart_map_validation_path: Path,
    chart_map_path: Path,
    stage_support_validation_path: Path,
    row_audit_path: Path,
    protocol_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, str]]:
    audit = _read_json(audit_validation_path)
    replay = _read_json(replay_validation_path)
    chart_map = _read_json(chart_map_validation_path)
    stage_support = _read_json(stage_support_validation_path)

    if audit.get("status") != "PARTIAL_PASS_SOURCE_SUPPORT_ONLY":
        raise ValueError("Full-surface source-support audit is not the expected partial-pass artifact")
    for key in ("outcomes_calculated", "C1_C3_scores_opened", "full_cohort_scoring_authorized"):
        _require_false(audit, key, "Source-support audit")
    if audit.get("c3_context", "").casefold().find(_C3_CONTEXT.casefold()) < 0:
        raise ValueError("Source-support audit does not bind the frozen N2-versus-Wake context")
    audit_hash = audit.get("output_sha256", {}).get("row_support_audit.csv")
    if not isinstance(audit_hash, str) or _sha256(row_audit_path) != audit_hash:
        raise ValueError("The supplied row-support audit is not the hash-bound source-support output")

    if replay.get("status") != "PASS_DETERMINISTIC_FEATURE_REPLAY":
        raise ValueError("Gate 7 deterministic full-surface replay has not passed")
    for key in ("outcomes_calculated", "C1_C3_scores_opened", "full_cohort_scoring_authorized"):
        _require_false(replay, key, "Replay validation")
    if not str(replay.get("gate_8_status", "")).startswith("NOT_OPEN"):
        raise ValueError("Gate 8 must remain NOT_OPEN during pre-outcome matching")
    replay_code = replay.get("validator_code", {})
    if not isinstance(replay_code, dict):
        raise ValueError("Replay validation lacks its validator code provenance")
    replay_code_path = Path(str(replay_code.get("path", ""))).resolve()
    replay_code_hash = replay_code.get("sha256")
    if not replay_code_path.is_file() or not isinstance(replay_code_hash, str):
        raise ValueError("Replay validator code path/hash is unavailable")
    if _sha256(replay_code_path) != replay_code_hash:
        raise ValueError("Replay validator code changed after the replay evidence was written")

    if chart_map.get("verdict") != "PARTIAL_PASS_ALL_FOLD_APPLY_SUPPORT_CROSSWALK":
        raise ValueError("All-fold apply support map is not the expected support-only artifact")
    for key in ("biological_claim_authorized", "contrasts_computed", "label_join_performed", "stage_horizon_intersection_computed"):
        _require_false(chart_map, key, "All-fold apply support map")
    if chart_map.get("output_parquet_sha256") != _sha256(chart_map_path):
        raise ValueError("All-fold apply support map parquet hash differs from validation")
    map_declared_path = Path(str(chart_map.get("output_parquet", "")))
    resolved_map_declared = map_declared_path if map_declared_path.is_absolute() else article_root / map_declared_path
    if resolved_map_declared.resolve() != chart_map_path.resolve():
        raise ValueError("All-fold support validation does not bind the supplied map parquet")

    if stage_support.get("verdict") != "PARTIAL_PASS_STAGE_HORIZON_SUPPORT_ONLY":
        raise ValueError("Stage/horizon support audit is not the expected support-only artifact")
    for key in ("outcomes_calculated", "matching_performed", "C1_C2_C3_scores_opened", "biological_claim_authorized"):
        _require_false(stage_support, key, "Stage/horizon support audit")
    if stage_support.get("c3_context", "").casefold().find(_C3_CONTEXT.casefold()) < 0:
        raise ValueError("Stage/horizon audit does not bind the frozen N2-versus-Wake context")
    stage_inputs = stage_support.get("input_sha256", {})
    if not isinstance(stage_inputs, dict):
        raise ValueError("Stage/horizon audit lacks its source hash bindings")
    if stage_inputs.get("v4_row_support_audit") != _sha256(row_audit_path):
        raise ValueError("Stage/horizon audit was not built from the supplied row-support audit")
    if stage_inputs.get("apply_support_map") != _sha256(chart_map_path):
        raise ValueError("Stage/horizon audit was not built from the supplied all-fold chart map")
    if stage_inputs.get("registered_protocol") != _sha256(protocol_path):
        raise ValueError("Stage/horizon audit does not bind the supplied preregistration")
    _verify_declared_outputs(stage_support_validation_path, stage_support)

    protocol_text = protocol_path.read_text(encoding="utf-8")
    if (
        "human-scored n2 versus wake" not in protocol_text.casefold()
        or "forecast origin" not in protocol_text.casefold()
    ):
        raise ValueError("Registered protocol does not contain the frozen N2-versus-Wake context")
    input_hashes = {
        "source_support_validation": _sha256(audit_validation_path),
        "row_support_audit": _sha256(row_audit_path),
        "replay_validation": _sha256(replay_validation_path),
        "all_fold_chart_map_validation": _sha256(chart_map_validation_path),
        "all_fold_chart_map_parquet": _sha256(chart_map_path),
        "stage_horizon_validation": _sha256(stage_support_validation_path),
        "registered_protocol": _sha256(protocol_path),
        "replay_validator_code": replay_code_hash,
        "c3_match_support_driver": _sha256(Path(__file__).resolve()),
        "c3_estimator_code": _sha256(Path(__file__).with_name("continuous_c123_estimators.py").resolve()),
    }
    return audit, replay, chart_map, stage_support, input_hashes


def _expected_chart_path(
    processed_root: Path,
    *,
    fold_id: int,
    role: str,
    version: str,
    bids_subject: str,
) -> Path:
    directory = f"fold_{fold_id}_{role}_label_free_{version}"
    stem = f"{bids_subject}_Sleep_acq-psg"
    return processed_root / directory / stem / f"{stem}.h5"


def _load_fold_rows(
    base_rows: pd.DataFrame,
    *,
    fold_id: int,
    role: str,
    fold_roster: Any,
    version: str,
    anchor_id: str,
    anchor_hash: str,
    article_root: Path,
    processed_root: Path,
    apply_map: pd.DataFrame | None,
    h5_evidence: list[dict[str, Any]],
) -> pd.DataFrame:
    pids = fold_roster.evaluation_pids if role == "apply" else fold_roster.training_pids
    selected = base_rows.loc[base_rows["pid"].astype(str).isin(pids)].copy()
    if selected.empty:
        raise ValueError(f"Fold {fold_id} {role} partition has no source-support rows")
    if set(selected["pid"].astype(str)) != set(pids):
        raise ValueError(f"Fold {fold_id} {role} roster differs from source-support rows")

    if role == "apply":
        if apply_map is None:
            raise ValueError("Apply partition requires its all-fold support-map rows")
        map_rows = apply_map.loc[apply_map["fold"].astype(int).eq(fold_id)].copy()
        selected = selected.merge(
            map_rows,
            on=["file", "epoch_id"],
            how="left",
            validate="one_to_one",
            suffixes=("", "_map"),
        )
        if selected["chart_h5_relative_path"].isna().any():
            raise ValueError(f"Fold {fold_id} apply rows are not fully bound to chart H5 paths")
        if not selected["audit_primary_surface_eligible"].astype(bool).all():
            raise ValueError(f"Fold {fold_id} apply chart map contains non-primary source rows")
    else:
        selected = selected.reset_index(drop=True)

    output: list[pd.DataFrame] = []
    files = selected[["file", "bids_subject", "pid"]].drop_duplicates()
    if files.duplicated("file").any() or files.duplicated("bids_subject").any():
        raise ValueError(f"Fold {fold_id} {role} recording identities are not one-to-one")
    for row in files.sort_values("file").itertuples(index=False):
        h5_path = _expected_chart_path(
            processed_root,
            fold_id=fold_id,
            role=role,
            version=version,
            bids_subject=str(row.bids_subject),
        )
        file_rows = selected.loc[selected["file"].eq(row.file)].copy()
        if role == "apply":
            declared_paths = file_rows["chart_h5_relative_path"].dropna().astype(str).unique()
            declared_hashes = file_rows["chart_h5_sha256"].dropna().astype(str).unique()
            if len(declared_paths) != 1 or len(declared_hashes) != 1:
                raise ValueError(f"Fold {fold_id} apply map has inconsistent H5 binding for {row.file}")
            declared_path = (article_root / Path(declared_paths[0])).resolve()
            if declared_path != h5_path.resolve():
                raise ValueError(f"Fold {fold_id} apply H5 path differs from support map: {row.file}")
            expected_file_hash = declared_hashes[0]
        else:
            expected_file_hash = None

        chart_rows, evidence = _read_current_chart_h5(
            h5_path,
            expected_bids_subject=str(row.bids_subject),
            expected_pid=str(row.pid),
            expected_anchor_id=anchor_id,
            expected_anchor_hash=anchor_hash,
            expected_file_sha256=expected_file_hash,
        )
        evidence.update({"fold": fold_id, "role": role, "recording_id": str(row.file), "pid": str(row.pid)})
        h5_evidence.append(evidence)

        joined = file_rows.merge(chart_rows, on="epoch_id", how="left", validate="one_to_one")
        if joined["coordinate_qc_valid"].isna().any():
            raise ValueError(f"Fold {fold_id} H5 is missing a primary source-supported epoch: {row.file}")
        if not np.allclose(joined["t_start"], joined["h5_window_start"], rtol=0, atol=0.01):
            raise ValueError(f"Fold {fold_id} chart H5 window starts differ from source audit: {row.file}")
        if not np.allclose(joined["t_end"], joined["h5_window_end"], rtol=0, atol=0.01):
            raise ValueError(f"Fold {fold_id} chart H5 window ends differ from source audit: {row.file}")

        if role == "apply":
            for map_column, h5_column in (
                ("chart_geometry_valid", "h5_geometry_valid"),
                ("chart_mnps_3d_valid", "h5_mnps_3d_valid"),
                ("chart_retained_after_qc", "h5_retained_after_qc"),
            ):
                if not np.array_equal(
                    joined[map_column].astype(bool).to_numpy(),
                    joined[h5_column].astype(bool).to_numpy(),
                ):
                    raise ValueError(f"Fold {fold_id} apply H5/map chart validity differs: {map_column}")
            if not np.array_equal(
                joined["chart_coords_3d_all_finite"].astype(bool).to_numpy(),
                joined["chart3d_all_finite"].astype(bool).to_numpy(),
            ):
                raise ValueError(f"Fold {fold_id} apply support map contains non-finite 3D chart values")
            if not joined["coordinate_qc_valid"].astype(bool).all():
                raise ValueError(f"Fold {fold_id} apply H5 chart QC differs from qualified map")

        joined["recording_id"] = joined["file"].astype(str)
        joined["recording_relative_seconds"] = pd.to_numeric(joined["t_end"], errors="coerce")
        joined["stage"] = joined["stage_at_origin"].astype("string")
        joined["stage_conflict"] = joined["stage_at_origin_status"].ne(_UNIQUE_STAGE_STATUS)
        joined["stage_window_pure"] = joined["stage_window_pure"].astype(bool)
        joined["source_support_eligible"] = joined["primary_surface_eligible"].astype(bool)
        output.append(joined[[
            "pid", "recording_id", "segment_id", "stage", "epoch_id", "t_end",
            "recording_relative_seconds", "stage_window_pure", "stage_conflict",
            "coordinate_qc_valid", "source_support_eligible", *_CHART_COLUMNS,
        ]])
    combined = pd.concat(output, ignore_index=True)
    if combined.duplicated(["pid", "recording_id", "epoch_id"]).any():
        raise ValueError(f"Fold {fold_id} {role} chart rows have duplicate origin identities")
    return combined


def _origin_support_by_pid(rows: pd.DataFrame, matches: pd.DataFrame, expected_pids: tuple[str, ...]) -> pd.DataFrame:
    eligible = rows.loc[
        rows["source_support_eligible"].astype(bool)
        & rows["coordinate_qc_valid"].astype(bool)
        & rows["stage_window_pure"].astype(bool)
        & ~rows["stage_conflict"].astype(bool)
        & rows["stage"].astype("string").str.casefold().isin(("n2", "wake"))
    ].copy()
    eligible["stage_key"] = eligible["stage"].astype("string").str.casefold()
    origin_counts = eligible.groupby(["pid", "stage_key"], sort=True).size().unstack(fill_value=0)
    recording_sets: dict[tuple[str, str], set[str]] = {
        (str(pid), str(stage)): set(block["recording_id"].astype(str))
        for (pid, stage), block in eligible.groupby(["pid", "stage_key"], sort=True)
    }
    match_counts = matches.groupby("pid", sort=True).size() if not matches.empty else pd.Series(dtype="int64")
    matched_recordings = (
        matches.groupby("pid", sort=True)["recording_id"].nunique()
        if not matches.empty else pd.Series(dtype="int64")
    )
    records: list[dict[str, Any]] = []
    for pid in expected_pids:
        n2_recordings = recording_sets.get((pid, "n2"), set())
        wake_recordings = recording_sets.get((pid, "wake"), set())
        records.append({
            "pid": pid,
            "support_eligible_n2_origins": int(origin_counts.loc[pid, "n2"]) if pid in origin_counts.index and "n2" in origin_counts else 0,
            "support_eligible_wake_origins": int(origin_counts.loc[pid, "wake"]) if pid in origin_counts.index and "wake" in origin_counts else 0,
            "n2_recording_count": len(n2_recordings),
            "wake_recording_count": len(wake_recordings),
            "shared_recording_count": len(n2_recordings & wake_recordings),
            "matched_h1_pair_count": int(match_counts.get(pid, 0)),
            "matched_recording_count": int(matched_recordings.get(pid, 0)),
            "meets_minimum_10_pairs": int(match_counts.get(pid, 0)) >= 10,
        })
    return pd.DataFrame(records)


def run_c3_preoutcome_match_support(
    *,
    article_root: Path,
    processed_root: Path,
    audit_validation_path: Path,
    replay_validation_path: Path,
    chart_map_validation_path: Path,
    chart_map_path: Path,
    stage_support_validation_path: Path,
    row_audit_path: Path,
    protocol_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Run only the frozen C3 h1 common-state match and balance gate."""
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing C3 support output: {output_dir}")
    article_root = article_root.resolve()
    processed_root = processed_root.resolve()
    audit, replay, chart_map_validation, stage_support, input_hashes = _validate_gate_inputs(
        article_root=article_root,
        audit_validation_path=audit_validation_path,
        replay_validation_path=replay_validation_path,
        chart_map_validation_path=chart_map_validation_path,
        chart_map_path=chart_map_path,
        stage_support_validation_path=stage_support_validation_path,
        row_audit_path=row_audit_path,
        protocol_path=protocol_path,
    )
    if audit["fold_assignment"].get("method") != "deterministic GroupKFold(5) by biological pid":
        raise ValueError("Source-support fold assignment is not the registered five-fold PID split")

    row_columns = [
        "file", "subject", "bids_subject", "pid", "epoch_id", "t_start", "t_end",
        "primary_surface_eligible", "stage_at_origin", "stage_at_origin_status",
        "stage_window_pure", "segment_id",
    ]
    source_rows = pd.read_csv(row_audit_path, usecols=row_columns)
    source_rows = source_rows.loc[source_rows["primary_surface_eligible"].astype(bool)].copy()
    source_rows["pid"] = source_rows["pid"].map(_pid_key)
    source_rows["epoch_id"] = pd.to_numeric(source_rows["epoch_id"], errors="raise").astype("int64")
    if source_rows.duplicated(["file", "epoch_id"]).any():
        raise ValueError("Source-support audit has duplicate recording/epoch identities")
    manifest = build_grouped_pid_manifest(source_rows[["pid"]])
    if manifest.sha256 != audit["fold_assignment"].get("manifest_sha256"):
        raise ValueError("Reconstructed C3 PID split does not match the source-support audit manifest")

    chart_map = pd.read_parquet(chart_map_path)
    if len(chart_map) != int(chart_map_validation.get("row_count", -1)):
        raise ValueError("All-fold apply chart map row count differs from its validation")
    chart_map["epoch_id"] = pd.to_numeric(chart_map["epoch_id"], errors="raise").astype("int64")
    crosswalk = chart_map.merge(
        source_rows[["file", "epoch_id", "subject", "bids_subject", "pid"]],
        on=["file", "epoch_id"],
        how="left",
        validate="one_to_one",
        suffixes=("_map", "_audit"),
    )
    if crosswalk["pid"].isna().any() or len(crosswalk) != len(source_rows):
        raise ValueError("All-fold apply chart map and source-support rows are not an exact one-to-one join")
    if not crosswalk["subject_map"].astype(str).equals(crosswalk["subject_audit"].astype(str)):
        raise ValueError("All-fold chart-map source subject differs from the stage/support audit")
    if not crosswalk["bids_subject_map"].astype(str).equals(crosswalk["bids_subject_audit"].astype(str)):
        raise ValueError("All-fold chart-map BIDS identity differs from the stage/support audit")
    if not crosswalk["audit_primary_surface_eligible"].astype(bool).all():
        raise ValueError("All-fold chart map includes a row outside the frozen primary source surface")

    anchor_records = chart_map_validation.get("fold_anchors")
    if not isinstance(anchor_records, dict) or set(anchor_records) != {str(index) for index in range(5)}:
        raise ValueError("All-fold support validation does not contain all five chart anchors")
    h5_evidence: list[dict[str, Any]] = []
    matches_by_fold: list[pd.DataFrame] = []
    fold_diagnostics: list[dict[str, Any]] = []
    pid_support_by_fold: list[pd.DataFrame] = []

    for fold in manifest.folds:
        anchor = anchor_records[str(fold.fold_id)]
        anchor_id = str(anchor["anchor_id"])
        anchor_hash = str(anchor["anchor_hash"])
        version = anchor_id.rsplit("_", 1)[-1]
        if version not in {"v1", "v2"}:
            raise ValueError(f"Unrecognized frozen label-free chart version for fold {fold.fold_id}")

        apply_fold_map = crosswalk.loc[crosswalk["fold"].astype(int).eq(fold.fold_id)].copy()
        map_pids = set(apply_fold_map["pid"].astype(str))
        if map_pids != set(fold.evaluation_pids):
            raise ValueError(f"Fold {fold.fold_id} apply-map PID roster differs from GroupKFold")
        training_rows = _load_fold_rows(
            source_rows,
            fold_id=fold.fold_id,
            role="training",
            fold_roster=fold,
            version=version,
            anchor_id=anchor_id,
            anchor_hash=anchor_hash,
            article_root=article_root,
            processed_root=processed_root,
            apply_map=None,
            h5_evidence=h5_evidence,
        )
        evaluation_rows = _load_fold_rows(
            source_rows,
            fold_id=fold.fold_id,
            role="apply",
            fold_roster=fold,
            version=version,
            anchor_id=anchor_id,
            anchor_hash=anchor_hash,
            article_root=article_root,
            processed_root=processed_root,
            apply_map=apply_fold_map,
            h5_evidence=h5_evidence,
        )

        transform = fit_c3_distance_transform(
            training_rows,
            _CHART_COLUMNS,
            time_col="recording_relative_seconds",
            valid_col="coordinate_qc_valid",
            support_col="source_support_eligible",
        )
        caliper = fit_c3_caliper(
            training_rows,
            transform,
            stage_col="stage",
            epoch_col="epoch_id",
            time_col="recording_relative_seconds",
            stage_pure_col="stage_window_pure",
            stage_conflict_col="stage_conflict",
            valid_col="coordinate_qc_valid",
            support_col="source_support_eligible",
        )
        fold_matches = match_c3_origins(
            evaluation_rows,
            transform,
            caliper,
            stage_col="stage",
            epoch_col="epoch_id",
            time_col="recording_relative_seconds",
            stage_pure_col="stage_window_pure",
            stage_conflict_col="stage_conflict",
            valid_col="coordinate_qc_valid",
            support_col="source_support_eligible",
            fold_id=fold.fold_id,
        )
        if any(column.startswith(("outcome", "future", "displacement")) for column in fold_matches.columns):
            raise RuntimeError("Origin matching unexpectedly produced an outcome/future column")
        matches_by_fold.append(fold_matches)
        pid_support = _origin_support_by_pid(evaluation_rows, fold_matches, fold.evaluation_pids)
        pid_support.insert(0, "outer_fold_id", fold.fold_id)
        pid_support_by_fold.append(pid_support)

        fold_diagnostics.append({
            "fold_id": fold.fold_id,
            "anchor_id": anchor_id,
            "anchor_hash": anchor_hash,
            "training_pid_count": len(fold.training_pids),
            "apply_pid_count": len(fold.evaluation_pids),
            "training_row_count": int(len(training_rows)),
            "apply_row_count": int(len(evaluation_rows)),
            "matched_h1_pair_count": int(len(fold_matches)),
            "matched_pid_count": int(fold_matches["pid"].nunique()) if not fold_matches.empty else 0,
            "training_context_cell_count": caliper.training_context_cell_count,
            "caliper_threshold": caliper.threshold,
            "training_transform": {
                "chart_center": dict(zip(_CHART_COLUMNS, map(float, transform.chart.center))),
                "chart_iqr": dict(zip(_CHART_COLUMNS, map(float, transform.chart.scale))),
                "recording_relative_seconds_center": transform.time_center,
                "recording_relative_seconds_iqr": transform.time_scale,
            },
        })

    oof = combine_c3_matched_origins_out_of_fold(
        matches_by_fold,
        fold_ids=tuple(range(5)),
        split_manifest=manifest,
        chart_columns=_CHART_COLUMNS,
    )
    gate = c3_overlap_gate(oof)
    matched = oof.matched_pairs
    pid_support = pd.concat(pid_support_by_fold, ignore_index=True)
    if len(pid_support) != len(manifest.expected_pids) or pid_support["pid"].duplicated().any():
        raise ValueError("C3 per-PID support table does not retain exactly one row per expected PID")

    output_dir.mkdir(parents=True, exist_ok=False)
    matched_path = output_dir / "matched_origins_h1.parquet"
    pid_path = output_dir / "match_support_by_pid.csv"
    h5_manifest_path = output_dir / "chart_h5_input_manifest.csv"
    matched.to_parquet(matched_path, index=False)
    pid_support.sort_values("pid").to_csv(pid_path, index=False)
    pd.DataFrame(h5_evidence).drop_duplicates("path").sort_values(["fold", "role", "path"]).to_csv(
        h5_manifest_path, index=False
    )
    output_hashes = {
        path.name: _sha256(path)
        for path in (matched_path, pid_path, h5_manifest_path)
    }
    gate_payload = {
        "gate_status": gate.gate_status,
        "expected_pid_count": gate.expected_pid_count,
        "pids_without_matches": list(gate.pids_without_matches),
        "eligible_pid_count": gate.eligible_pid_count,
        "qualifying_pid_count": gate.qualifying_pid_count,
        "pair_count": gate.pair_count,
        "matched_pid_count": gate.matched_pid_count,
        "matched_recording_pair_count": gate.matched_pair_count,
        "smd_iqr": dict(gate.smd_iqr),
        "reasons": list(gate.reasons),
        "matched_pair_identity_sha256": gate.matched_pair_digest,
        "matched_origin_content_sha256": gate.matched_content_sha256,
    }
    report = {
        "schema": "boas.c3_preoutcome_match_support.v1",
        "verdict": "PASS_C3_PREOUTCOME_OVERLAP_GATE" if gate.gate_status == "OVERLAP_GATE_PASS" else "INCONCLUSIVE_C3_PREOUTCOME_OVERLAP_GATE",
        "scope": "C3 N2-versus-Wake h1 origin matching and common-state support/balance only; no future chart, outcome, effect, contrast, or score is read or calculated",
        "c3_context": _C3_CONTEXT,
        "gate_5_status": gate.gate_status,
        "gate_8_status": "NOT_OPEN; separately dated amendment/hash freeze/authorization still required",
        "matching_performed": True,
        "outcomes_calculated": False,
        "future_chart_coordinates_read": False,
        "future_stage_values_read": False,
        "C1_C2_C3_scores_opened": False,
        "biological_claim_authorized": False,
        "full_cohort_protocol_authorization": "NOT_GRANTED",
        "measurement_semantics_changed": False,
        "time_of_night_definition": "source-audit t_end in seconds from recording start; forecast/stage origin is defined at t_end",
        "matching_rule": "frozen greedy closest-edge one-to-one without replacement within PID and recording; fold-local training-only robust scaling and training-only 95th-percentile participant-weighted nearest-origin caliper",
        "chart_columns": list(_CHART_COLUMNS),
        "horizon_lag": 1,
        "thresholds": {"minimum_independent_pids": 20, "minimum_h1_pairs_per_pid": 10, "maximum_absolute_smd_iqr": 0.10},
        "split_manifest_sha256": manifest.sha256,
        "split_pid_count": len(manifest.expected_pids),
        "eligible_source_row_count": int(len(source_rows)),
        "matched_origin_pair_count": int(len(matched)),
        "matched_pid_count": int(matched["pid"].nunique()) if not matched.empty else 0,
        "gate": gate_payload,
        "fold_diagnostics": fold_diagnostics,
        "input_paths": {
            "source_support_validation": str(audit_validation_path.resolve()),
            "row_support_audit": str(row_audit_path.resolve()),
            "replay_validation": str(replay_validation_path.resolve()),
            "all_fold_chart_map_validation": str(chart_map_validation_path.resolve()),
            "all_fold_chart_map_parquet": str(chart_map_path.resolve()),
            "stage_horizon_validation": str(stage_support_validation_path.resolve()),
            "registered_protocol": str(protocol_path.resolve()),
            "replay_validator_code": str(Path(replay["validator_code"]["path"]).resolve()),
            "c3_match_support_driver": str(Path(__file__).resolve()),
            "c3_estimator_code": str(Path(__file__).with_name("continuous_c123_estimators.py").resolve()),
        },
        "input_sha256": input_hashes,
        "chart_h5_input_count": int(len(pd.DataFrame(h5_evidence).drop_duplicates("path"))),
        "chart_h5_input_manifest": h5_manifest_path.name,
        "outputs": {"matched_origins": matched_path.name, "pid_support": pid_path.name},
        "output_sha256": output_hashes,
        "output_hash_scope": "all generated files listed before validation.json is written; validation.json is excluded to avoid a self-referential hash",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output_dir / "validation.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "article-root", "processed-root", "audit-validation", "replay-validation",
        "chart-map-validation", "chart-map", "stage-support-validation", "row-audit",
        "protocol", "output-dir",
    ):
        parser.add_argument(f"--{name}", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    report = run_c3_preoutcome_match_support(
        article_root=args.article_root,
        processed_root=args.processed_root,
        audit_validation_path=args.audit_validation,
        replay_validation_path=args.replay_validation,
        chart_map_validation_path=args.chart_map_validation,
        chart_map_path=args.chart_map,
        stage_support_validation_path=args.stage_support_validation,
        row_audit_path=args.row_audit,
        protocol_path=args.protocol,
        output_dir=args.output_dir,
    )
    print(json.dumps({
        "verdict": report["verdict"],
        "gate_5_status": report["gate_5_status"],
        "matched_origin_pair_count": report["matched_origin_pair_count"],
        "matched_pid_count": report["matched_pid_count"],
        "output_dir": str(args.output_dir.resolve()),
    }, indent=2))


if __name__ == "__main__":
    main()
