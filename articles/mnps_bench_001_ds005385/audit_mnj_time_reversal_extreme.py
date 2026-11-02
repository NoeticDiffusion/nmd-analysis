"""Audit the H2R sub-380 EO center with the largest reversal anisotropy delta."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import h5py
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_h1 as h1  # noqa: E402
import analyze_h2 as h2  # noqa: E402
import analyze_mnj_information as mnj  # noqa: E402


NMD_ROOT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics")
BENCH_DIR = NMD_ROOT / "project" / "new_mnps_v.3.1" / "bench_001"
FREEZE_PATH = Path(r"I:\AAA_PYTHON_REPOS_BACKUP\homepages\_mnps_mnj_information_001\mnj_information_freeze_v1_20261008.json")
OUT_PATH = Path(r"I:\AAA_PYTHON_REPOS_BACKUP\homepages\_mnps_mnj_information_001\time_reversal_extreme_center_detail.csv")
SUBJECT = "sub-380"
STATE = "EyesOpen"
COHORT = "H2R"
SOURCE_WINDOW_ROW = 36


def main() -> None:
    freeze = mnj.read_json(FREEZE_PATH)
    if freeze.get("schema") != "mnps_mnj_information_001_freeze.v1":
        raise ValueError("Unexpected MNJ analysis freeze schema")
    inputs = [
        row for row in freeze["inputs"]
        if row["cohort"] == COHORT and SUBJECT in Path(row["path"]).name and STATE in Path(row["path"]).name
    ]
    if len(inputs) != 1:
        raise ValueError(f"Expected one frozen input; found {len(inputs)}")
    input_row = inputs[0]
    source_path = Path(input_row["path"])
    observed_source_hash = mnj.sha256_file(source_path)
    if observed_source_hash.lower() != input_row["sha256"].lower():
        raise ValueError("Source HDF5 hash does not match the frozen input")

    h2_freeze_path = BENCH_DIR / "h2_analysis_freeze_v1_20261007.json"
    h2r_freeze_path = BENCH_DIR / "h2r_analysis_freeze_v1_20261008.json"
    h2.validate_analysis_freeze(
        h2r_freeze_path,
        Path(json.loads(h2r_freeze_path.read_text(encoding="utf-8"))["run_dir"]),
        Path(json.loads(h2r_freeze_path.read_text(encoding="utf-8"))["selection_manifest"]["path"]),
        Path(json.loads(h2r_freeze_path.read_text(encoding="utf-8"))["execution_manifest"]["path"]),
        NMD_ROOT,
    )
    projection, jacobian = h2.load_nmd_kernels(NMD_ROOT)

    with h5py.File(source_path, "r") as h5file:
        payloads = h1._json_dataset(h5file["measurements/v3_1/recordings_json"])
        if len(payloads) != 1:
            raise ValueError("Expected one v3.1 recording payload")
        windows = payloads[0]["measurement_payload"].get("windows", [])
        starts = np.asarray([float(window["window_start_sec"]) for window in windows], dtype=np.float64)
        ends = np.asarray([float(window["window_end_sec"]) for window in windows], dtype=np.float64)
        candidate_rows = {name: [] for name in mnj.FAST_FIELDS}
        for window in windows:
            for feature, candidate in h2.FAST_CANDIDATES.items():
                candidate_rows[feature].append(h2._candidate_value(window.get("measurements", []), candidate))
        trajectory = np.asarray([
            [np.nan if value is None else float(value) for value in candidate_rows[feature]]
            for feature in mnj.FAST_FIELDS
        ], dtype=np.float64).T

    original, _ = mnj.estimate_matrices(
        trajectory, starts, ends, subject=SUBJECT, state=STATE, cohort=COHORT,
        source_h5=str(source_path), projection=projection, jacobian_module=jacobian,
    )
    reversed_rows, _ = mnj.estimate_matrices(
        trajectory, starts, ends, subject=SUBJECT, state=STATE, cohort=COHORT,
        source_h5=str(source_path), projection=projection, jacobian_module=jacobian, reverse=True,
    )
    selected = []
    for label, rows in (("original", original), ("reversed", reversed_rows)):
        matches = [row for row in rows if row["window_row"] == SOURCE_WINDOW_ROW]
        if len(matches) != 1:
            raise ValueError(f"Expected one {label} row at source window {SOURCE_WINDOW_ROW}; found {len(matches)}")
        selected.append((label, matches[0]))

    by_label = {label: row for label, row in selected}
    left = np.asarray([[by_label["original"][f"J_{i}{j}"] for j in range(4)] for i in range(4)])
    right = np.asarray([[by_label["reversed"][f"J_{i}{j}"] for j in range(4)] for i in range(4)])
    sign_error = float(np.linalg.norm(left + right))
    relative_sign_error = sign_error / max(float(np.linalg.norm(left)), np.finfo(float).tiny)
    audit_hash = mnj.sha256_file(Path(__file__).resolve())
    analysis_freeze_hash = mnj.sha256_file(FREEZE_PATH)

    fields = [
        "cohort", "subject", "state", "orientation", "source_h5", "source_h5_sha256",
        "source_window_row", "segment_id", "window_start_sec", "window_end_sec", "center_time_sec",
        "mnj_singular_value_anisotropy", "singular_value_1", "singular_value_2",
        "singular_value_3", "singular_value_4", "condition_number", "numerical_rank",
        "relative_J_sign_reversal_error", "analysis_freeze_sha256", "audit_script_sha256",
        *[f"J_{i}{j}" for i in range(4) for j in range(4)],
    ]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for label, row in selected:
            writer.writerow({
                "cohort": COHORT,
                "subject": SUBJECT,
                "state": STATE,
                "orientation": label,
                "source_h5": str(source_path),
                "source_h5_sha256": observed_source_hash,
                "source_window_row": SOURCE_WINDOW_ROW,
                "segment_id": row["segment_id"],
                "window_start_sec": row["window_start_sec"],
                "window_end_sec": row["window_end_sec"],
                "center_time_sec": row["center_time_sec"],
                "mnj_singular_value_anisotropy": row["mnj_singular_value_anisotropy"],
                **{f"singular_value_{index}": row[f"singular_value_{index}"] for index in range(1, 5)},
                "condition_number": row["condition_number"],
                "numerical_rank": row["numerical_rank"],
                "relative_J_sign_reversal_error": relative_sign_error,
                "analysis_freeze_sha256": analysis_freeze_hash,
                "audit_script_sha256": audit_hash,
                **{f"J_{i}{j}": row[f"J_{i}{j}"] for i in range(4) for j in range(4)},
            })
    print(json.dumps({
        "output": str(OUT_PATH),
        "source_h5_sha256": observed_source_hash,
        "analysis_freeze_sha256": analysis_freeze_hash,
        "audit_script_sha256": audit_hash,
        "original_anisotropy": by_label["original"]["mnj_singular_value_anisotropy"],
        "reversed_anisotropy": by_label["reversed"]["mnj_singular_value_anisotropy"],
        "absolute_difference": abs(by_label["original"]["mnj_singular_value_anisotropy"] - by_label["reversed"]["mnj_singular_value_anisotropy"]),
        "relative_J_sign_reversal_error": relative_sign_error,
        "original_singular_values": [by_label["original"][f"singular_value_{index}"] for index in range(1, 5)],
        "reversed_singular_values": [by_label["reversed"][f"singular_value_{index}"] for index in range(1, 5)],
    }, indent=2))


if __name__ == "__main__":
    main()
