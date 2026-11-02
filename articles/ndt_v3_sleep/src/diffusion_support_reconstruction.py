"""Candidate-only reconstruction of the stored diffusion neighborhoods.

This module is deliberately separate from the producer.  It first reproduces
the stored diffusion tensor, support count, and validity series exactly.  The
neighbor table is written only after that gate passes.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import math
import numbers
import platform
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping

import h5py
import numpy as np
import yaml


KNOWN_STAGES = {0, 1, 2, 3, 4}
REQUIRED_PRODUCER_FILES = {
    "mndm/src/mndm/dynamical_families/diffusion_geometry.py",
    "mndm/src/mndm/dynamical_families/validity.py",
    "mndm/src/mndm/pipeline/dynamical_families_export.py",
    "mndm/src/mndm/dynamical_families/chart_drift.py",
    "mndm/src/mndm/dynamical_families/contracts.py",
    "mndm/src/mndm/measurement_certificate.py",
    "mndm/src/mndm/inferential_grain.py",
}

REQUIRED_SETTINGS = {
    "neighborhood_k",
    "min_samples",
    "min_neighborhood_samples",
    "max_gap_sec",
    "max_dt_relative_deviation",
    "min_valid_fraction",
    "psd_floor",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _package_versions() -> dict[str, str | None]:
    return {
        name: (importlib.metadata.version(name) if _has_package(name) else None)
        for name in ("numpy", "h5py", "PyYAML", "scipy")
    }


def _has_package(name: str) -> bool:
    try:
        importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return False
    return True


def _text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _scalar(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value.item() if hasattr(value, "item") else value


def _equal_nan_exact(left: np.ndarray, right: np.ndarray) -> bool:
    return bool(np.array_equal(np.asarray(left), np.asarray(right), equal_nan=True))


def _load_producer(root: Path):
    source_root = root / "mndm" / "src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    diffusion = importlib.import_module("mndm.dynamical_families.diffusion_geometry")
    validity = importlib.import_module("mndm.dynamical_families.validity")
    expected_diffusion = (root / "mndm/src/mndm/dynamical_families/diffusion_geometry.py").resolve()
    expected_validity = (root / "mndm/src/mndm/dynamical_families/validity.py").resolve()
    if Path(diffusion.__file__).resolve() != expected_diffusion:
        raise RuntimeError(f"loaded diffusion module is not pinned: {diffusion.__file__}")
    if Path(validity.__file__).resolve() != expected_validity:
        raise RuntimeError(f"loaded validity module is not pinned: {validity.__file__}")
    return diffusion, validity


def _segments(raw_files: np.ndarray) -> np.ndarray:
    values = np.asarray([_text(value) for value in raw_files], dtype=object)
    _, inverse = np.unique(values, return_inverse=True)
    return np.asarray(inverse, dtype=np.int32)


def _settings(config: Mapping[str, Any]) -> dict[str, Any]:
    raw = config.get("settings")
    if not isinstance(raw, Mapping) or set(raw) != REQUIRED_SETTINGS:
        raise ValueError("settings must contain exactly the seven reconstruction settings")

    settings = dict(raw)

    def integer(name: str, minimum: int) -> int:
        value = settings[name]
        if isinstance(value, bool) or not isinstance(value, numbers.Real):
            raise ValueError(f"{name} must be a finite integer")
        numeric = float(value)
        if not math.isfinite(numeric) or numeric != math.floor(numeric) or numeric < minimum:
            raise ValueError(f"{name} must be a finite integer >= {minimum}")
        return int(numeric)

    def real(name: str, minimum: float, maximum: float | None = None) -> float:
        value = settings[name]
        if isinstance(value, bool) or not isinstance(value, numbers.Real):
            raise ValueError(f"{name} must be a finite number")
        numeric = float(value)
        if not math.isfinite(numeric) or numeric < minimum or (maximum is not None and numeric > maximum):
            bound = f" in [{minimum}, {maximum}]" if maximum is not None else f" >= {minimum}"
            raise ValueError(f"{name} must be a finite number{bound}")
        return numeric

    settings["neighborhood_k"] = integer("neighborhood_k", 1)
    settings["min_samples"] = integer("min_samples", 1)
    settings["min_neighborhood_samples"] = integer("min_neighborhood_samples", 1)
    settings["max_gap_sec"] = (None if settings["max_gap_sec"] is None
                                 else real("max_gap_sec", 0.0))
    settings["max_dt_relative_deviation"] = real("max_dt_relative_deviation", 0.0)
    settings["min_valid_fraction"] = real("min_valid_fraction", 0.0, 1.0)
    settings["psd_floor"] = real("psd_floor", 0.0)
    return settings


def _load_input(path: Path) -> dict[str, np.ndarray]:
    with h5py.File(path, "r") as handle:
        return {
            "x": np.asarray(handle["/coords_3d_subject_anchored/values"][()]),
            "time": np.asarray(handle["/time"][()]),
            "epoch_id": np.asarray(handle["/epoch_id"][()]),
            "window_start": np.asarray(handle["/window_start"][()]),
            "window_end": np.asarray(handle["/window_end"][()]),
            "stage": np.asarray(handle["/labels/stage"][()]),
            "raw_file": np.asarray(handle["/row_source/raw_file"][()]),
            "stored_tensor": np.asarray(handle["/dynamical_families/diffusion/v1/series/diffusion_tensor"][()]),
            "stored_support": np.asarray(handle["/dynamical_families/diffusion/v1/series/support_count"][()]),
            "stored_valid": np.asarray(handle["/dynamical_families/diffusion/v1/series/valid"][()]),
            "stored_settings": {
                key: _scalar(value[()])
                for key, value in handle["/dynamical_families/diffusion/v1/provenance/settings"].items()
            },
        }


def _candidate_rows(
    data: Mapping[str, np.ndarray],
    source_idx: np.ndarray,
    nearest_indices: np.ndarray,
    nearest_distances: np.ndarray,
    finite_idx: np.ndarray,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    query_summary: list[dict[str, Any]] = []
    stage = np.asarray(data["stage"], dtype=int)
    epoch_id = np.asarray(data["epoch_id"], dtype=int)
    time = np.asarray(data["time"], dtype=float)
    for row, query in enumerate(finite_idx):
        distances = np.asarray(nearest_distances[row], dtype=float)
        kth = float(np.max(distances))
        tie_ambiguous = False
        if nearest_indices.shape[1] < int(data["reference_count"]):
            query_state = np.asarray(data["state_for_estimator"][int(query)], dtype=float)
            references = np.asarray(data["state_for_estimator"][source_idx], dtype=float)
            full_distances = np.sum((references - query_state) ** 2, axis=1)
            selected = np.zeros(full_distances.size, dtype=bool)
            selected[np.asarray(nearest_indices[row], dtype=int)] = True
            tie_ambiguous = bool(np.any(full_distances[~selected] == kth))
        known_query = int(stage[query]) in KNOWN_STAGES
        same_known = 0
        for rank, ref_pos in enumerate(np.asarray(nearest_indices[row], dtype=int)):
            source = int(source_idx[ref_pos])
            target = source + 1
            source_stage = int(stage[source])
            target_stage = int(stage[target])
            same = bool(known_query and source_stage == int(stage[query]) and target_stage == int(stage[query]))
            same_known += int(same)
            rows.append({
                "query_epoch_id": int(epoch_id[query]),
                "query_index": int(query),
                "query_stage_code": int(stage[query]),
                "query_stage_unknown": int(stage[query]) not in KNOWN_STAGES,
                "query_window_start": float(data["window_start"][query]),
                "query_window_end": float(data["window_end"][query]),
                "selection_index": int(rank),
                "source_epoch_id": int(epoch_id[source]),
                "source_index": source,
                "source_stage_code": source_stage,
                "source_stage_unknown": source_stage not in KNOWN_STAGES,
                "source_window_start": float(data["window_start"][source]),
                "source_window_end": float(data["window_end"][source]),
                "target_epoch_id": int(epoch_id[target]),
                "target_index": target,
                "target_stage_code": target_stage,
                "target_stage_unknown": target_stage not in KNOWN_STAGES,
                "target_window_start": float(data["window_start"][target]),
                "target_window_end": float(data["window_end"][target]),
                "distance_squared": float(distances[rank]),
                "dt_sec": float(time[target] - time[source]),
                "kth_distance_tie_ambiguous": tie_ambiguous,
            })
        query_summary.append({
            "query_epoch_id": int(epoch_id[query]),
            "query_stage_code": int(stage[query]),
            "query_stage_known": known_query,
            "same_known_stage_source_target_count": int(same_known) if known_query else None,
            "same_known_stage_source_target_fraction": float(same_known / len(nearest_indices[row])) if known_query else None,
            "kth_distance_tie_ambiguous": tie_ambiguous,
        })
    return rows, query_summary


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    import csv

    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _finish_output(output: Path, manifest: dict[str, Any]) -> None:
    """Write manifests and a non-self-referential output hash index."""
    for name in ("gate_report.json", "manifest.json"):
        (output / name).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    hashes = {
        path.relative_to(output).as_posix(): _sha256(path)
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name not in {"output_hashes.json", "output_hashes.sha256"}
    }
    hash_index = {"schema_version": "ndt_v3_sleep.output_hashes.v1", "files": hashes}
    hash_path = output / "output_hashes.json"
    hash_path.write_text(json.dumps(hash_index, indent=2, sort_keys=True), encoding="utf-8")
    (output / "output_hashes.sha256").write_text(_sha256(hash_path) + "  output_hashes.json\n", encoding="utf-8")


def run(config_path: Path) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, Mapping):
        raise ValueError("configuration must be a mapping")
    h5_path = Path(config["input_h5"]).resolve()
    producer_root = Path(config["producer_root"]).resolve()
    output = Path(config["output"]).resolve()
    settings = _settings(config)
    analysis_code = Path(config["analysis_code"]).resolve()
    expected_input_hash = str(config.get("input_h5_sha256", "")).strip()
    expected_analysis_hash = str(config.get("analysis_code_sha256", "")).strip()
    if analysis_code != Path(__file__).resolve():
        raise ValueError("analysis_code must pin this reconstruction runner")
    if not expected_input_hash or not expected_analysis_hash:
        raise ValueError("input_h5_sha256 and analysis_code_sha256 are mandatory pins")
    producer_hashes = dict(config.get("producer_file_sha256") or {})
    producer_list = list(config.get("producer_files") or [])
    if set(producer_list) != REQUIRED_PRODUCER_FILES or set(producer_hashes) != REQUIRED_PRODUCER_FILES:
        raise ValueError("producer_files must contain the exact required seven-file pin set")
    actual_input_hash = _sha256(h5_path)
    if actual_input_hash.lower() != expected_input_hash.lower():
        raise ValueError("input HDF5 hash does not match frozen config pin")
    for relative, expected in producer_hashes.items():
        actual = _sha256(producer_root / relative)
        if actual.lower() != str(expected).lower():
            raise ValueError(f"producer file hash does not match frozen config pin: {relative}")
    if _sha256(analysis_code).lower() != expected_analysis_hash.lower():
        raise ValueError("analysis runner hash does not match frozen config pin")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"candidate output must be fresh: {output}")
    output.mkdir(parents=True, exist_ok=True)
    snapshot_dir = output / "source_snapshot"
    snapshot_dir.mkdir()
    snapshot_files: dict[str, str] = {}
    for relative in producer_list:
        source = producer_root / relative
        target = snapshot_dir / (Path(relative).as_posix().replace("/", "__").replace("\\", "__"))
        shutil.copy2(source, target)
        snapshot_files[target.name] = _sha256(target)
    shutil.copy2(analysis_code, snapshot_dir / "reconstruction_runner.py")
    snapshot_files["reconstruction_runner.py"] = _sha256(snapshot_dir / "reconstruction_runner.py")
    diffusion, validity = _load_producer(producer_root)
    data = _load_input(h5_path)
    segments = _segments(data["raw_file"])
    result = diffusion.estimate_local_diffusion_geometry(
        data["x"], data["time"], segment_id=segments,
        coordinate_layer="coords_3d_subject_anchored", coordinate_names=["m", "d", "e"],
        **settings,
    )
    series = result.get("series", {})
    recomputed_tensor = np.asarray(series.get("diffusion_tensor"))
    stored_tensor = np.asarray(data["stored_tensor"])
    input_hash_after = _sha256(h5_path)
    producer_hashes_after = {relative: _sha256(producer_root / relative) for relative in producer_hashes}
    tensor_match = _equal_nan_exact(recomputed_tensor.astype(stored_tensor.dtype), stored_tensor)
    support_match = _equal_nan_exact(np.asarray(series.get("support_count")), data["stored_support"])
    valid_match = _equal_nan_exact(np.asarray(series.get("valid")), data["stored_valid"])
    gate = {
        "tensor_exact_after_stored_dtype_cast": tensor_match,
        "support_count_exact": support_match,
        "valid_exact": valid_match,
        "input_h5_stable_before_after": actual_input_hash == input_hash_after,
        "producer_files_stable_before_after": all(
            str(producer_hashes.get(relative, actual)).lower() == actual.lower()
            for relative, actual in producer_hashes_after.items()
        ),
        "computation_status_computed": result.get("computation_status") == "computed",
        "settings_match_stored_provenance": (
            all(
                key in data["stored_settings"] and data["stored_settings"].get(key) == value
                for key, value in settings.items() if key != "max_gap_sec"
            )
            and ("max_gap_sec" not in data["stored_settings"] and settings.get("max_gap_sec") is None
                 or data["stored_settings"].get("max_gap_sec") == settings.get("max_gap_sec"))
        ),
        "producer_computation_status": result.get("computation_status"),
        "producer_failure_reason": result.get("failure_reason"),
    }
    gate_ok = all(gate[key] for key in (
        "tensor_exact_after_stored_dtype_cast", "support_count_exact", "valid_exact",
        "input_h5_stable_before_after", "producer_files_stable_before_after",
        "computation_status_computed", "settings_match_stored_provenance",
    ))
    manifest: dict[str, Any] = {
        "schema_version": "ndt_v3_sleep.diffusion_support_reconstruction.v1",
        "status": "candidate_only_gate_failed" if not gate_ok else "candidate_only_gate_passed",
        "claim_status": "no_biological_claim",
        "full_support_status": "not_assessed",
        "historical_membership_status": "not_claimed",
        "input_h5": str(h5_path),
        "input_h5_sha256": _sha256(h5_path),
        "input_h5_sha256_before": actual_input_hash,
        "input_h5_sha256_after": input_hash_after,
        "runtime": {"python": platform.python_version(), "executable": sys.executable, "packages": _package_versions()},
        "config": str(config_path.resolve()),
        "config_sha256": _sha256(config_path.resolve()),
        "producer_root": str(producer_root),
        "producer_git_revision_recorded": config.get("producer_git_revision_recorded"),
        "producer_files": {},
        "producer_files_sha256_after": producer_hashes_after,
        "source_snapshot": snapshot_files,
        "settings": settings,
        "gate": gate,
    }
    for relative in config["producer_files"]:
        path = producer_root / relative
        manifest["producer_files"][relative] = {"path": str(path), "sha256": _sha256(path)}
    if not gate_ok:
        _finish_output(output, manifest)
        return manifest

    # The producer's validate_trajectory converts state to float64 before
    # forming increments and distances, even though the HDF5 export is float32.
    state_for_estimator = np.asarray(data["x"], dtype=float)
    source_idx, increments, dts = validity.increment_pairs(
        state_for_estimator, data["time"], segments, max_gap_sec=settings.get("max_gap_sec")
    )
    finite_idx = np.flatnonzero(np.isfinite(data["time"]) & np.all(np.isfinite(state_for_estimator), axis=1))
    k = min(settings["neighborhood_k"], len(source_idx))
    nearest_indices, nearest_distances = validity.chunked_nearest_neighbors(
        state_for_estimator[finite_idx], state_for_estimator[source_idx], k
    )
    # Recompute every selected covariance through the producer PSD helper and
    # require exact agreement before exposing candidate memberships.
    algebra_match = True
    for row, _query in enumerate(finite_idx):
        local = increments[np.asarray(nearest_indices[row], dtype=int)]
        covariance = np.atleast_2d(np.cov(local, rowvar=False, ddof=1)) / float(np.median(dts))
        projected, _ = validity.project_to_psd(covariance, eigenvalue_floor=settings["psd_floor"])
        if not _equal_nan_exact(projected.astype(stored_tensor.dtype), stored_tensor[int(_query)]):
            algebra_match = False
            break
    if not algebra_match:
        manifest["status"] = "candidate_only_algebra_gate_failed"
        manifest["gate"]["selected_covariance_algebra_exact"] = False
        _finish_output(output, manifest)
        return manifest
    producer_hashes_final = {relative: _sha256(producer_root / relative) for relative in producer_hashes}
    input_hash_final = _sha256(h5_path)
    final_input_stable = actual_input_hash == input_hash_final
    final_sources_stable = all(
        str(producer_hashes.get(relative, actual)).lower() == actual.lower()
        for relative, actual in producer_hashes_final.items()
    )
    manifest["producer_files_sha256_final"] = producer_hashes_final
    manifest["input_h5_sha256_final"] = input_hash_final
    manifest["gate"]["producer_files_stable_after_all_usage"] = final_sources_stable
    manifest["gate"]["input_h5_stable_after_all_usage"] = final_input_stable
    if not final_sources_stable or not final_input_stable:
        manifest["status"] = "candidate_only_source_gate_failed"
        _finish_output(output, manifest)
        return manifest
    candidate_data = dict(data)
    candidate_data["reference_count"] = len(source_idx)
    candidate_data["state_for_estimator"] = state_for_estimator
    rows, query_summary = _candidate_rows(candidate_data, source_idx, nearest_indices, nearest_distances, finite_idx)
    _write_csv(output / "candidate_neighbors.csv", rows)
    _write_csv(output / "candidate_query_stage_support.csv", query_summary)
    known = [r for r in query_summary if r["query_stage_known"]]
    source_counts: dict[str, int] = {}
    target_counts: dict[str, int] = {}
    for row in rows:
        source_counts[str(row["source_stage_code"])] = source_counts.get(str(row["source_stage_code"]), 0) + 1
        target_counts[str(row["target_stage_code"])] = target_counts.get(str(row["target_stage_code"]), 0) + 1
    manifest["gate"]["selected_covariance_algebra_exact"] = True
    manifest["candidate"] = {
        "query_count": len(query_summary),
        "neighbor_row_count": len(rows),
        "known_query_count": len(known),
        "unknown_query_count": len(query_summary) - len(known),
        "tie_ambiguous_query_count": sum(int(r["kth_distance_tie_ambiguous"]) for r in query_summary),
        "source_stage_distribution": source_counts,
        "target_stage_distribution": target_counts,
        "same_known_stage_source_target_fraction_mean_among_known_queries": (
            float(np.mean([r["same_known_stage_source_target_fraction"] for r in known])) if known else None
        ),
        "known_queries_with_all_neighbors_same_known_stage_fraction": (
            float(sum(r["same_known_stage_source_target_count"] == settings["neighborhood_k"] for r in known) / len(known)) if known else None
        ),
    }
    manifest["status"] = "candidate_only_membership_exported"
    _finish_output(output, manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.config), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
