#!/usr/bin/env python3
"""Frozen SL-022B comparison for the ds004148 MNPS v2.0 candidate and v3.2."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import math
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import h5py
import numpy as np
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 20261021
BOOTSTRAPS = 10_000
SESSIONS = ("ses-session1", "ses-session2", "ses-session3")
TASKS = ("eyesclosed", "eyesopen", "mathematic", "memory", "music")
CONTRASTS = ("mathematic", "memory", "music")
BASELINES = (
    "log10_median_channel_rms_uV", "relative_delta_1_4hz", "relative_theta_4_8hz",
    "relative_alpha_8_13hz", "relative_beta_13_30hz", "relative_gamma_30_45hz",
    "normalized_spectral_entropy_1_45hz", "median_channel_autocorrelation_lag_1s",
    "mean_absolute_zero_lag_channel_correlation",
)
V2_9D = ("m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m")
V2_3D = ("m", "d", "e")
V3_SCALARS = ("PCV", "TP", "NIE", "RD", "OI", "SC", "ED")
AR4_EXPECTED, AR20_EXPECTED = 1, 9
FOLD_ID = "SL022B-OUTER-FOLDS-001|ds004148|"
V3_PROTOCOL = Path(r"H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.2\protocols\SL-020-MNPS32-RETEST-001.md")
V3_AMENDMENT_001 = Path(r"H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.2\protocols\SL-020-PROTOCOL-AMENDMENT-001.md")
V3_AMENDMENT_002 = Path(r"H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.2\protocols\SL-020-PROTOCOL-AMENDMENT-002.md")
SL020_ANALYSIS = Path(r"J:\repos\nmd-analysis\articles\ds004148_mnps_v3_2_reliability\code\sl020_analysis.py")
V3_RUNNER = Path(r"H:\SourceRepo2\NeuralManifoldDynamics\mndm\src\mndm\mnps\v3_2\experiments\sl020_ds004148.py")
V2_COMMON_CONFIG = Path(r"H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.2\protocols\sl022a_common_eeg_v2_0_2b61d3.yaml")
V2_OVERLAY_CONFIG = Path(r"H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.2\protocols\sl022a_v2_candidate_ds004148.yaml")
V2_GIT_REV = "2b61d3eca37dfca4892dee488ad211e3f7ae037d"
V2_CONFIG_DIGEST = "34cc951b30da55603f0e7c759b9ed501759fea9a12516e0dd90b16f33d901847"
V2_COMMON_CONFIG_SHA256 = "798f53e4fd59e66b17327b60e484a8961d2ef55baab47cbc996f417d393af05e"
V2_OVERLAY_SHA256 = "b3e13ee16dae351d2386c3dc8dd640454fc04de27c6fbe5d11a37eb5015191af"
V2_ALLOWED_SOURCE_FAILURES = frozenset({
    ("sub-28", "ses-session3", "mathematic"),
    ("sub-28", "ses-session3", "memory"),
    ("sub-28", "ses-session3", "music"),
    ("sub-60", "ses-session2", "mathematic"),
})
V2_WINDOWS = 74
V2_FS_OUT = 4.0
V2_WINDOW_SECONDS = 8.0
V2_STEP_SECONDS = 4.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def finite(value: Any) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def stable_rng(*parts: Any) -> np.random.Generator:
    material = f"{SEED}|" + "|".join(str(item) for item in parts)
    return np.random.default_rng(int.from_bytes(hashlib.sha256(material.encode()).digest()[:8], "big"))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            cooked = {}
            for key, value in row.items():
                if isinstance(value, (dict, list, tuple)):
                    value = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
                if isinstance(value, np.generic):
                    value = value.item()
                if isinstance(value, float) and not math.isfinite(value):
                    value = ""
                cooked[key] = "" if value is None else value
            writer.writerow(cooked)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
                    encoding="utf-8")


def holm(pvalues: list[float]) -> list[float]:
    order = sorted(range(len(pvalues)), key=lambda i: (pvalues[i], i))
    output = [1.0] * len(pvalues)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(pvalues) - rank) * pvalues[index])
        output[index] = min(1.0, running)
    return output


def add_window(store: dict, key: tuple, start: float, end: float, value: Any,
               valid: bool, reason: str | None = None) -> None:
    number = finite(value) if valid else None
    store[key].append((float(start), float(end), number,
                       reason or (None if number is not None else "invalid_or_nonfinite")))


def summarize_windows(window_data: dict, metadata: dict, *, trim: bool = False,
                      canonical_only: bool = False) -> tuple[dict, list[dict[str, Any]]]:
    summaries = {}
    support = []
    for key, windows in window_data.items():
        version, duration, pid, session, task, dim = key
        rec = (pid, session, task)
        if canonical_only and not metadata.get(rec, {}).get("canonical_labels", False):
            continue
        selected = [w for w in windows if not trim or (w[0] >= 20 and w[1] <= 280)]
        values = [w[2] for w in selected if w[2] is not None]
        reasons = Counter(w[3] for w in selected if w[2] is None and w[3])
        median = float(np.median(values)) if values else None
        if median is not None:
            summaries[key] = median
        support.append({
            "version": version, "duration_seconds": duration, "participant_id": pid,
            "session_id": session, "condition": task, "dimension": dim,
            "requested_window_rows": len(selected), "valid_window_count": len(values),
            "unsupported_window_count": len(selected) - len(values), "unsupported_reasons": dict(reasons),
            "recording_median": median, "trimmed_endpoints": trim,
            "canonical_source_labels_only": canonical_only, "qualified": False,
        })
    return summaries, support


def load_v3(cohort_root: Path) -> tuple[dict, dict, dict, list[Path], dict]:
    spec = importlib.util.spec_from_file_location("sl020_analysis_for_sl022b", SL020_ANALYSIS)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot_load_sl020_cohort_verifier")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    manifest, shards, hashes = verifier.verify_cohort(
        cohort_root, V3_PROTOCOL, V3_AMENDMENT_001, V3_AMENDMENT_002
    )
    if len(manifest["frozen_identity"]["selected_participants"]) != 60:
        raise RuntimeError("v3_cohort_participant_count_not_60")
    frozen_runner_hash = manifest.get("frozen_identity", {}).get("code_hashes", {}).get("runner")
    current_runner_hash = sha256_file(V3_RUNNER)
    if not frozen_runner_hash or current_runner_hash != frozen_runner_hash:
        raise RuntimeError(f"v3_runner_hash_mismatch:{current_runner_hash}:{frozen_runner_hash}")
    window_data: dict[tuple, list] = defaultdict(list)
    metadata, failures = {}, []
    ar_names = {4: [], 20: []}
    for shard in shards:
        with gzip.open(shard, "rt", encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                kind = row.get("record_type")
                if kind == "recording_manifest":
                    rec = (row["participant_id"], row["session_id"], row.get("task_id", row.get("condition")))
                    aliases = row.get("explicit_casefold_aliases") or []
                    metadata[rec] = {**row, "canonical_labels": len(aliases) == 0}
                    continue
                if kind in ("file_failure", "source_failure", "unsupported_recording"):
                    failures.append(row)
                    continue
                if kind not in ("measurement", "qEEG_baseline"):
                    continue
                pid, session, task = row.get("participant_id"), row.get("session_id"), row.get("condition")
                duration = int(row.get("duration_seconds") or 0)
                if session not in SESSIONS or task not in TASKS or duration not in (4, 20):
                    raise RuntimeError(f"v3_coordinate_outside_frozen_grid:{session}:{task}:{duration}")
                start, end = finite(row.get("start_seconds")), finite(row.get("end_seconds"))
                if start is None or end is None:
                    if row.get("support_status") == "unsupported_file_source" or row.get("window_id") is None:
                        failures.append(row)
                        continue
                    raise RuntimeError("v3_window_bounds_missing")
                if kind == "qEEG_baseline":
                    dim = f"qEEG:{row.get('baseline_feature_id')}"
                    add_window(window_data, ("v3", duration, pid, session, task, dim), start, end,
                               row.get("value"), bool(row.get("valid")) and bool(row.get("computed")), row.get("reason"))
                elif row.get("family_id") == "AR":
                    names = [str(x) for x in (row.get("component_names") or [])]
                    vals = row.get("component_values") or []
                    statuses = row.get("component_status") or []
                    reasons = row.get("component_reasons") or []
                    valids = row.get("component_valid") or []
                    if len(names) != len(vals):
                        raise RuntimeError("v3_AR_component_schema_length_mismatch")
                    if names:
                        if ar_names[duration] and ar_names[duration] != names:
                            raise RuntimeError(f"v3_AR_component_roster_changed:{duration}")
                        ar_names[duration] = names
                    for i, name in enumerate(names):
                        status = statuses[i] if i < len(statuses) else row.get("status")
                        reason = reasons[i] if i < len(reasons) else row.get("reason")
                        valid = status in ("computed", "computed_exploratory", "valid")
                        if i < len(valids):
                            valid = valid and bool(valids[i])
                        add_window(window_data, ("v3", duration, pid, session, task, f"MNPS:AR::{name}"),
                                   start, end, vals[i], valid, reason)
                else:
                    dim = f"MNPS:{row.get('family_id')}"
                    add_window(window_data, ("v3", duration, pid, session, task, dim), start, end,
                               row.get("value"), bool(row.get("valid")) and bool(row.get("computed")), row.get("reason"))
    if len(metadata) != 900:
        raise RuntimeError(f"v3_recording_manifest_count_mismatch:{len(metadata)}")
    if len(ar_names[4]) != AR4_EXPECTED or len(ar_names[20]) != AR20_EXPECTED:
        raise RuntimeError(f"v3_AR_component_count_mismatch:{len(ar_names[4])}:{len(ar_names[20])}")
    if any(not row.get("payload_sha256") for row in metadata.values()):
        raise RuntimeError("v3_source_payload_hash_missing")
    return manifest, window_data, metadata, shards, {
        "hashes": hashes, "ar_names": ar_names, "file_failures": failures,
        "verifier_sha256": sha256_file(SL020_ANALYSIS), "runner_sha256": current_runner_hash,
    }


def parse_v2_recording(path: Path) -> tuple[tuple[str, str, str], dict]:
    with h5py.File(path, "r") as h5:
        raw = h5["manifest_json"][()]
    manifest = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else str(raw))
    parts = str(manifest.get("dataset_id", "")).split(":", 2)
    if len(parts) != 3 or parts[0] != "ds004148":
        raise RuntimeError(f"v2_manifest_dataset_id_malformed:{path}")
    match = re.fullmatch(r"(ses-session[123])_(.+)", parts[2])
    if not match:
        raise RuntimeError(f"v2_manifest_recording_id_malformed:{path}")
    return (parts[1], match.group(1), match.group(2)), manifest


def verify_v2_run_manifests(v2_root: Path) -> list[dict[str, Any]]:
    if sha256_file(V2_COMMON_CONFIG) != V2_COMMON_CONFIG_SHA256:
        raise RuntimeError("v2_common_config_snapshot_hash_mismatch")
    if sha256_file(V2_OVERLAY_CONFIG) != V2_OVERLAY_SHA256:
        raise RuntimeError("v2_overlay_config_hash_mismatch")
    paths = sorted(v2_root.rglob("run_manifest.json"))
    if not paths:
        raise RuntimeError(f"v2_run_manifest_missing:{v2_root}")
    records = []
    for path in paths:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        git_rev = manifest.get("environment", {}).get("git_rev")
        config_digest = manifest.get("config", {}).get("digest_sha256")
        if manifest.get("dataset_id") != "ds004148" or git_rev != V2_GIT_REV or config_digest != V2_CONFIG_DIGEST:
            raise RuntimeError(f"v2_run_identity_mismatch:{path}:{git_rev}:{config_digest}")
        records.append({
            "run_manifest_path": str(path), "run_manifest_sha256": sha256_file(path),
            "git_rev": git_rev, "config_digest_sha256": config_digest,
            "h5_count_in_manifest": manifest.get("counts", {}).get("h5"),
            "bad_files": manifest.get("capabilities", {}).get("bad_files", []),
        })
    return records


def load_v2_h5(v2_root: Path, window_data: dict, metadata: dict) -> tuple[list[Path], list[dict[str, Any]], list[dict[str, Any]], list[tuple[str, str, str]], list[dict[str, Any]]]:
    run_manifests = verify_v2_run_manifests(v2_root)
    files = sorted(v2_root.glob("**/*.h5"))
    seen, audit = set(), []
    for path in files:
        rec, recording_manifest = parse_v2_recording(path)
        if rec in seen:
            raise RuntimeError(f"duplicate_v2_h5_recording:{rec}")
        seen.add(rec)
        if rec not in metadata:
            raise RuntimeError(f"v2_recording_not_in_v3_source_manifest:{rec}")
        n_windows = recording_manifest.get("samples")
        if (not isinstance(n_windows, int) or isinstance(n_windows, bool) or
                n_windows < 1 or n_windows > V2_WINDOWS):
            raise RuntimeError(f"v2_recording_window_count_out_of_range:{rec}:{n_windows}")
        if n_windows < V2_WINDOWS and rec not in V2_ALLOWED_SOURCE_FAILURES:
            raise RuntimeError(f"v2_unexpected_partial_window_grid:{rec}:{n_windows}")
        grid = recording_manifest.get("mnps", {})
        if (finite(grid.get("fs_out")) != V2_FS_OUT or
                finite(grid.get("window_sec")) != V2_WINDOW_SECONDS or
                finite(grid.get("overlap")) != 0.5):
            raise RuntimeError(f"v2_recording_grid_mismatch:{rec}:{grid}")
        axis_names = recording_manifest.get("mnps_axes", {}).get("names", [])
        axis_order = recording_manifest.get("mnps_axes", {}).get("order", {})
        if axis_names != list(V2_3D) or axis_order != {"m": 0, "d": 1, "e": 2}:
            raise RuntimeError(f"v2_recording_mnps_axis_contract_mismatch:{rec}")
        coordinate_names = recording_manifest.get("coords_9d", {}).get("names", [])
        if coordinate_names != list(V2_9D):
            raise RuntimeError(f"v2_recording_9d_contract_mismatch:{rec}")
        with h5py.File(path, "r") as h5:
            if "coords_9d/values" not in h5 or "mnps_3d" not in h5:
                raise RuntimeError(f"v2_coordinate_groups_missing:{path}")
            v9 = np.asarray(h5["coords_9d/values"], dtype=np.float64)
            n9 = [x.decode() if isinstance(x, bytes) else str(x) for x in h5["coords_9d/names"][:]]
            v3 = np.asarray(h5["mnps_3d"], dtype=np.float64)
            n3 = list(axis_names)
            valid9 = np.asarray(h5["qc/windows/coords_9d_valid"], dtype=bool)
            valid3 = np.asarray(h5["qc/windows/mnps_3d_valid"], dtype=bool)
            starts = np.asarray(h5["window_start"], dtype=np.float64)
            ends = np.asarray(h5["window_end"], dtype=np.float64)
            if n9 != list(V2_9D) or n3 != list(V2_3D):
                raise RuntimeError(f"v2_coordinate_order_mismatch:{path}")
            if (v9.shape != (n_windows, 9) or v3.shape != (n_windows, 3) or
                    starts.shape != (n_windows,) or ends.shape != (n_windows,) or
                    valid9.shape != (n_windows,) or valid3.shape != (n_windows,)):
                raise RuntimeError(f"v2_window_schema_mismatch:{path}")
            expected_starts = np.arange(n_windows, dtype=np.float64) * V2_STEP_SECONDS
            expected_ends = expected_starts + V2_WINDOW_SECONDS
            if not (np.allclose(starts, expected_starts, rtol=0, atol=1e-9) and
                    np.allclose(ends, expected_ends, rtol=0, atol=1e-9)):
                raise RuntimeError(f"v2_window_bounds_mismatch:{path}")
            for j, dim in enumerate(V2_9D):
                for i in range(n_windows):
                    valid = bool(valid9[i]) and math.isfinite(float(v9[i, j]))
                    add_window(window_data, ("v2", 8, *rec, f"v2_9D::{dim}"), starts[i], ends[i],
                               v9[i, j], valid, None if valid else "coords_9d_invalid_or_nonfinite")
                for i in range(n_windows, V2_WINDOWS):
                    start = i * V2_STEP_SECONDS
                    add_window(window_data, ("v2", 8, *rec, f"v2_9D::{dim}"), start,
                               start + V2_WINDOW_SECONDS, None, False,
                               "window_not_emitted_by_v2_recording")
            for j, dim in enumerate(V2_3D):
                for i in range(n_windows):
                    valid = bool(valid3[i]) and math.isfinite(float(v3[i, j]))
                    add_window(window_data, ("v2", 8, *rec, f"v2_3D::{dim}"), starts[i], ends[i],
                               v3[i, j], valid, None if valid else "mnps_3d_invalid_or_nonfinite")
                for i in range(n_windows, V2_WINDOWS):
                    start = i * V2_STEP_SECONDS
                    add_window(window_data, ("v2", 8, *rec, f"v2_3D::{dim}"), start,
                               start + V2_WINDOW_SECONDS, None, False,
                               "window_not_emitted_by_v2_recording")
        audit.append({
            "participant_id": rec[0], "session_id": rec[1], "condition": rec[2],
            "status": "present" if n_windows == V2_WINDOWS else "partial_window_support",
            "h5_path": str(path), "sha256": sha256_file(path),
            "valid_9d_window_count": int(valid9.sum()),
            "source_payload_sha256_expected": metadata[rec].get("payload_sha256"),
            "valid_3d_window_count": int(valid3.sum()), "observed_window_count": n_windows,
            "requested_window_count": V2_WINDOWS, "unemitted_window_count": V2_WINDOWS - n_windows,
            "unemitted_window_indices": list(range(n_windows, V2_WINDOWS)),
            "first_window_start": float(starts[0]), "last_window_end": float(ends[-1]), "qualified": False,
        })
    expected_records = set(metadata)
    missing = expected_records - seen
    unexpected_missing = missing - V2_ALLOWED_SOURCE_FAILURES
    if unexpected_missing:
        raise RuntimeError(f"v2_unexpected_missing_recordings:{sorted(unexpected_missing)}")
    missing_audit = []
    for rec in sorted(missing):
        row = {
            "participant_id": rec[0], "session_id": rec[1], "condition": rec[2],
            "status": "unsupported", "reason": "hdf5_output_missing_for_protocol_allowed_source_failure",
            "h5_path": None, "source_payload_sha256_expected": metadata[rec].get("payload_sha256"),
            "valid_9d_window_count": 0, "valid_3d_window_count": 0,
            "requested_window_count": V2_WINDOWS, "qualified": False,
        }
        missing_audit.append(row)
        audit.append(row)
    manifest_h5_counts = [row.get("h5_count_in_manifest") for row in run_manifests]
    if any(count is None for count in manifest_h5_counts) or sum(manifest_h5_counts) != len(files):
        raise RuntimeError(f"v2_run_manifest_h5_count_mismatch:{manifest_h5_counts}:{len(files)}")
    return files, audit, run_manifests, sorted(missing), missing_audit


def parse_header(path: Path) -> tuple[list[str], int, str, float | None, str, str]:
    sections = {"Common Infos": {}, "Binary Infos": {}, "Channel Infos": {}}
    section = ""
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        text = line.strip()
        if not text or text.startswith(";"):
            continue
        if text.startswith("[") and text.endswith("]"):
            section = text[1:-1]
        elif "=" in text and section in sections:
            key, value = text.split("=", 1)
            sections[section][key.strip()] = value.strip()
    channel = sections["Channel Infos"]
    labels = [value.split(",", 1)[0].strip()
              for key, value in sorted(channel.items(),
                  key=lambda item: int(item[0][2:]) if item[0].lower().startswith("ch") and item[0][2:].isdigit() else 10**9)
              if key.lower().startswith("ch") and key[2:].isdigit()]
    common, binary = sections["Common Infos"], sections["Binary Infos"]
    interval = finite(common.get("SamplingInterval"))
    sfreq = 1_000_000.0 / interval if interval and interval > 0 else None
    return (labels, int(common.get("NumberOfChannels", "0")), binary.get("BinaryFormat", ""),
            sfreq, common.get("DataOrientation", ""), common.get("DataFormat", ""))


def read_channel_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def load_baseline(expected_sha256: str):
    actual_sha256 = sha256_file(V3_RUNNER)
    if actual_sha256 != expected_sha256:
        raise RuntimeError(f"v3_baseline_runner_hash_mismatch:{actual_sha256}:{expected_sha256}")
    spec = importlib.util.spec_from_file_location("sl020_runner_for_sl022b_baseline", V3_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot_load_frozen_sl020_baseline")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._baseline, actual_sha256


def extract_v2_qeeg(dataset_root: Path, metadata: dict, window_data: dict,
                    expected_runner_sha256: str) -> tuple[list[dict], dict]:
    baseline, baseline_sha256 = load_baseline(expected_runner_sha256)
    audit, problems, metadata_qc_warnings = [], Counter(), Counter()
    fs, samples = 500.0, 150_000
    for rec, source in sorted(metadata.items()):
        pid, session, task = rec
        relative = source.get("relative_payload_path")
        if not relative:
            raise RuntimeError(f"relative_payload_path_missing:{rec}")
        payload = dataset_root / Path(str(relative))
        if not payload.is_file():
            raise RuntimeError(f"raw_payload_missing:{rec}")
        source_hash = sha256_file(payload)
        expected_hash = source.get("payload_sha256")
        if source_hash != expected_hash:
            raise RuntimeError(f"source_payload_hash_mismatch:{rec}")
        eeg_dir, stem = payload.parent, payload.name.removesuffix("_eeg.eeg")
        vhdr, channels = eeg_dir / f"{stem}_eeg.vhdr", eeg_dir / f"{stem}_channels.tsv"
        eeg_json = eeg_dir / f"{stem}_eeg.json"
        expected_metadata_hashes = source.get("source_metadata_hashes") or {}
        metadata_paths = {"vhdr": vhdr, "channels_tsv": channels, "eeg_json": eeg_json}
        actual_metadata_hashes = {}
        missing_frozen_hashes = []
        for key, sidecar in metadata_paths.items():
            expected_metadata_hash = expected_metadata_hashes.get(key)
            if not expected_metadata_hash:
                missing_frozen_hashes.append(key)
                continue
            if not sidecar.is_file():
                raise RuntimeError(f"frozen_source_metadata_file_missing:{rec}:{key}")
            actual_metadata_hash = sha256_file(sidecar)
            if actual_metadata_hash != expected_metadata_hash:
                raise RuntimeError(f"source_metadata_hash_mismatch:{rec}:{key}")
            actual_metadata_hashes[key] = actual_metadata_hash
        if missing_frozen_hashes:
            reason = "frozen_source_metadata_hash_missing:" + ",".join(missing_frozen_hashes)
            problems["metadata_missing"] += 1
            audit.append({"participant_id": pid, "session_id": session, "condition": task,
                          "status": "unsupported", "reason": reason,
                          "payload_sha256": source_hash, "qualified": False})
            continue
        labels, nchan, binary, header_sfreq, orientation, data_format = parse_header(vhdr)
        channel_rows = read_channel_rows(channels)
        canonical = [str(row.get("name", "")).strip() for row in channel_rows]
        types = [str(row.get("type", "")).strip().upper() for row in channel_rows]
        units = [str(row.get("units", "")).strip() for row in channel_rows]
        channel_rates = [finite(row.get("sampling_frequency")) for row in channel_rows]
        sidecar = json.loads(eeg_json.read_text(encoding="utf-8-sig"))
        try:
            sidecar_channel_count = int(sidecar.get("EEGChannelCount") or 0)
        except (TypeError, ValueError):
            sidecar_channel_count = None
        row_metadata_warnings = []
        if sidecar_channel_count != nchan:
            warning = f"eeg_json_channel_count_mismatch:{sidecar_channel_count}:{nchan}"
            row_metadata_warnings.append(warning)
            metadata_qc_warnings["eeg_json_channel_count_mismatch"] += 1
        size = payload.stat().st_size
        reason = None
        if binary != "IEEE_FLOAT_32":
            reason = f"unsupported_binary_format:{binary}"
        elif data_format.upper() != "BINARY" or orientation.upper() != "MULTIPLEXED":
            reason = f"unsupported_header_layout:{data_format}:{orientation}"
        elif nchan != 61 or len(labels) != 61 or len(canonical) != 61 or len(channel_rows) != 61:
            reason = f"actual_channel_set_not_61:{nchan}:{len(labels)}:{len(canonical)}"
        elif len({label.casefold() for label in labels}) != 61 or len({label.casefold() for label in canonical}) != 61:
            reason = "duplicate_casefold_channel_labels"
        elif any(kind != "EEG" for kind in types):
            reason = "unexpected_non_eeg_channel_in_source_table"
        elif any(unit != "uV" for unit in units):
            reason = "unexpected_source_channel_units"
        elif header_sfreq is None or not math.isclose(header_sfreq, fs, rel_tol=0, abs_tol=1e-9):
            reason = f"header_sampling_frequency_mismatch:{header_sfreq}"
        elif any(rate is None or not math.isclose(rate, fs, rel_tol=0, abs_tol=1e-9) for rate in channel_rates):
            reason = "channels_tsv_sampling_frequency_mismatch"
        elif not math.isclose(finite(sidecar.get("SamplingFrequency")) or -1, fs, rel_tol=0, abs_tol=1e-9):
            reason = "eeg_json_sampling_frequency_mismatch"
        elif sidecar.get("EEGReference") != source.get("declared_reference"):
            reason = "eeg_json_declared_reference_mismatch"
        elif size != samples * nchan * 4:
            reason = f"payload_size_mismatch:{size}:expected_{samples*nchan*4}"
        if reason:
            problems[reason.split(":")[0]] += 1
            audit.append({"participant_id": pid, "session_id": session, "condition": task,
                          "payload_sha256": source_hash, "payload_size_bytes": size,
                          "header_labels": labels, "ordered_eeg_labels": canonical,
                          "verified_metadata_hashes": actual_metadata_hashes,
                          "header_channel_count": nchan, "sidecar_eeg_channel_count": sidecar_channel_count,
                          "source_metadata_qc_warnings": row_metadata_warnings,
                          "status": "unsupported", "reason": reason, "qualified": False})
            continue
        if labels != source.get("source_header_labels") or canonical != source.get("study_common_labels"):
            raise RuntimeError(f"source_label_order_mismatch_frozen_manifest:{rec}")
        by_case = {name.casefold(): i for i, name in enumerate(labels)}
        if len(by_case) != len(labels) or any(name.casefold() not in by_case for name in canonical):
            problems["ambiguous_or_missing_casefold_channel_mapping"] += 1
            audit.append({"participant_id": pid, "session_id": session, "condition": task,
                          "payload_sha256": source_hash, "status": "unsupported",
                          "reason": "ambiguous_or_missing_casefold_channel_mapping", "qualified": False})
            continue
        order = [by_case[name.casefold()] for name in canonical]
        expected_order = source.get("header_to_study_common_column_indices")
        if expected_order is not None and list(expected_order) != order:
            raise RuntimeError(f"source_channel_reorder_mismatch_frozen_manifest:{rec}")
        mem = np.memmap(payload, dtype="<f4", mode="r", shape=(samples, nchan))
        signals = np.asarray(mem[:, order].T, dtype=np.float64)
        del mem
        count_by_feature, reason_by_feature = Counter(), Counter()
        for start_sample in range(0, samples - 8 * int(fs) + 1, 4 * int(fs)):
            start, end = start_sample / fs, (start_sample + 8 * int(fs)) / fs
            values, reasons = baseline(signals[:, start_sample:start_sample + 8 * int(fs)], fs)
            for feature in BASELINES:
                feature_result = values.get(feature)
                if isinstance(feature_result, dict):
                    value = feature_result.get("value")
                    valid = (bool(feature_result.get("computed")) and
                             bool(feature_result.get("valid")) and finite(value) is not None)
                    reason = feature_result.get("reason") or reasons.get(feature)
                else:
                    value = feature_result
                    valid = finite(value) is not None
                    reason = reasons.get(feature)
                add_window(window_data, ("v2", 8, pid, session, task, f"qEEG:{feature}"),
                           start, end, value, valid, reason)
                if not valid:
                    if reason:
                        reason_by_feature[feature] += 1
                else:
                    count_by_feature[feature] += 1
        del signals
        aliases = [{"header": labels[order[j]], "bids": canonical[j]}
                   for j in range(len(canonical)) if labels[order[j]] != canonical[j]]
        audit.append({
            "participant_id": pid, "session_id": session, "condition": task,
            "status": "completed", "payload_sha256": source_hash, "payload_size_bytes": size,
            "header_channel_count": nchan, "header_labels": labels, "source_header_labels": labels,
            "sidecar_eeg_channel_count": sidecar_channel_count,
            "source_metadata_qc_warnings": row_metadata_warnings,
            "ordered_eeg_labels": canonical,
            "verified_metadata_hashes": actual_metadata_hashes,
            "header_order_sha256": sha256_text(json.dumps(labels, separators=(",", ":"))),
            "header_set_sha256": sha256_text(json.dumps(sorted(labels), separators=(",", ":"))),
            "bids_order_sha256": sha256_text(json.dumps(canonical, separators=(",", ":"))),
            "bids_set_sha256": sha256_text(json.dumps(sorted(canonical), separators=(",", ":"))),
            "explicit_casefold_aliases": aliases, "requested_windows": 74,
            "computed_window_count_by_feature": dict(count_by_feature),
            "unsupported_window_count_by_feature": dict(reason_by_feature), "qualified": False,
        })
    return audit, {"support_errors": dict(problems),
                   "metadata_qc_warnings": dict(metadata_qc_warnings),
                   "baseline_runner_sha256": baseline_sha256}


def b1(summary: dict, ar_names: dict, *, trim: bool = False, canonical: bool = False) -> list[dict]:
    dimensions = [("v2", 8, f"v2_3D::{d}") for d in V2_3D]
    dimensions += [("v2", 8, f"v2_9D::{d}") for d in V2_9D]
    for duration in (4, 20):
        dimensions += [("v3", duration, f"MNPS:{d}") for d in V3_SCALARS]
        dimensions += [("v3", duration, f"MNPS:AR::{d}") for d in ar_names[duration]]
    rows = []
    for version, duration, dim in dimensions:
        for task in CONTRASTS:
            deltas = {}
            pids = sorted({k[2] for k in summary if k[0] == version and k[1] == duration})
            for pid in pids:
                paired = []
                for session in SESSIONS:
                    x = summary.get((version, duration, pid, session, task, dim))
                    y = summary.get((version, duration, pid, session, "eyesclosed", dim))
                    if x is not None and y is not None:
                        paired.append(float(x) - float(y))
                if len(paired) >= 2:
                    deltas[pid] = float(np.mean(paired))
            values = np.asarray(list(deltas.values()), dtype=np.float64)
            if len(values):
                indices = stable_rng("B1", trim, canonical, version, duration, dim, task).integers(
                    0, len(values), size=(BOOTSTRAPS, len(values)))
                boot = np.median(values[indices], axis=1)
                lo, hi = float(np.quantile(boot, .025)), float(np.quantile(boot, .975))
                try:
                    p = float(stats.wilcoxon(values, alternative="two-sided", zero_method="wilcox").pvalue)
                except ValueError:
                    p = 1.0
                median = float(np.median(values))
                reason = ""
            else:
                lo = hi = median = None
                p, reason = 1.0, "fewer_than_two_paired_sessions_or_no_supported_recordings"
            rows.append({
                "analysis": "B1", "trimmed_endpoints": trim, "canonical_source_labels_only": canonical,
                "version": version, "duration_seconds": duration, "dimension": dim,
                "contrast": f"{task}-eyesclosed", "eligible_participants": len(values),
                "median_participant_delta": median, "ci95_low": lo, "ci95_high": hi,
                "p_raw_wilcoxon": p, "support_reason": reason, "qualified": False,
            })
    if len(rows) != 108:
        raise RuntimeError(f"B1_primary_or_sensitivity_family_size_mismatch:{len(rows)}")
    key = "p_holm_108_family" if not trim and not canonical else "p_holm_separate_sensitivity_family"
    for row, adjusted in zip(rows, holm([row["p_raw_wilcoxon"] for row in rows])):
        row[key] = adjusted
    return rows


def icc_a1(x: np.ndarray) -> float:
    if x.ndim != 2 or x.shape[1] != 2 or len(x) < 2 or not np.isfinite(x).all():
        return float("nan")
    n, k = x.shape
    grand, row, col = float(x.mean()), x.mean(axis=1), x.mean(axis=0)
    msr = k * np.sum((row - grand) ** 2) / (n - 1)
    msc = n * np.sum((col - grand) ** 2) / (k - 1)
    resid = x - row[:, None] - col[None, :] + grand
    mse = np.sum(resid ** 2) / ((n - 1) * (k - 1))
    den = msr + (k - 1) * mse + k * (msc - mse) / n
    return float((msr - mse) / den) if den != 0 else float("nan")


def b2_dimensions(ar_names: dict) -> list[tuple[str, int, str]]:
    out = [("v2", 8, f"v2_3D::{d}") for d in V2_3D]
    out += [("v2", 8, f"v2_9D::{d}") for d in V2_9D]
    out += [("v2", 8, f"qEEG:{d}") for d in BASELINES]
    for duration in (4, 20):
        out += [("v3", duration, f"MNPS:{d}") for d in V3_SCALARS]
        out += [("v3", duration, f"MNPS:AR::{d}") for d in ar_names[duration]]
        out += [("v3", duration, f"qEEG:{d}") for d in BASELINES]
    return out


def b2(summary: dict, ar_names: dict, *, trim: bool = False, canonical: bool = False) -> list[dict]:
    rows = []
    series_specs = [(("condition", t), t) for t in TASKS]
    series_specs += [(("contrast", t), f"{t}-eyesclosed") for t in CONTRASTS]
    for version, duration, dim in b2_dimensions(ar_names):
        pids = sorted({k[2] for k in summary if k[0] == version and k[1] == duration})
        for series, label in series_specs:
            for s1, s2, pair_label in (("ses-session1", "ses-session2", "S1-S2"),
                                       ("ses-session1", "ses-session3", "S1-S3")):
                pairs = []
                for pid in pids:
                    def get(session):
                        if series[0] == "condition":
                            return summary.get((version, duration, pid, session, label, dim))
                        a = summary.get((version, duration, pid, session, series[1], dim))
                        b = summary.get((version, duration, pid, session, "eyesclosed", dim))
                        return None if a is None or b is None else float(a) - float(b)
                    a, b = get(s1), get(s2)
                    if a is not None and b is not None:
                        pairs.append((float(a), float(b)))
                matrix = np.asarray(pairs, dtype=np.float64).reshape((-1, 2))
                estimate = icc_a1(matrix) if len(matrix) >= 12 else None
                if estimate is not None and math.isfinite(estimate):
                    rng = stable_rng("B2", trim, canonical, version, duration, dim, label, pair_label)
                    boot = matrix[rng.integers(0, len(matrix), size=(BOOTSTRAPS, len(matrix)))]
                    grand = boot.mean(axis=(1, 2))
                    row_means, col_means = boot.mean(axis=2), boot.mean(axis=1)
                    msr = 2 * np.sum((row_means - grand[:, None]) ** 2, axis=1) / (len(matrix) - 1)
                    msc = len(matrix) * np.sum((col_means - grand[:, None]) ** 2, axis=1)
                    resid = boot - row_means[:, :, None] - col_means[:, None, :] + grand[:, None, None]
                    mse = np.sum(resid ** 2, axis=(1, 2)) / (len(matrix) - 1)
                    den = msr + mse + 2 * (msc - mse) / len(matrix)
                    with np.errstate(divide="ignore", invalid="ignore"):
                        ci_values = (msr - mse) / den
                    ci_values = ci_values[np.isfinite(ci_values)]
                    lo = float(np.quantile(ci_values, .025)) if len(ci_values) else None
                    hi = float(np.quantile(ci_values, .975)) if len(ci_values) else None
                    status = "estimable"
                else:
                    lo = hi = None
                    status = "not_estimable_fewer_than_12_pairs" if len(matrix) < 12 else "not_estimable_nonfinite_icc"
                rows.append({
                    "analysis": "B2", "trimmed_endpoints": trim, "canonical_source_labels_only": canonical,
                    "version": version, "duration_seconds": duration, "dimension": dim,
                    "series": label, "session_pair": pair_label, "paired_participants": len(matrix),
                    "icc_a1": estimate, "ci95_low": lo, "ci95_high": hi, "status": status, "qualified": False,
                })
    return rows


def participant_condition(summary: dict, version: str, duration: int, pid: str, condition: str, dim: str):
    vals = [summary.get((version, duration, pid, s, condition, dim)) for s in SESSIONS]
    vals = [float(x) for x in vals if x is not None]
    return float(np.mean(vals)) if vals else None


def b4_dependence(summary: dict, ar_names: dict) -> list[dict]:
    specs = [
        ("v2_8s_plus_3D", "v2", 8, [f"qEEG:{x}" for x in BASELINES] + [f"v2_3D::{x}" for x in V2_3D]),
        ("v2_8s_plus_9D", "v2", 8, [f"qEEG:{x}" for x in BASELINES] + [f"v2_9D::{x}" for x in V2_9D]),
        ("v3_2_4s", "v3", 4, [f"qEEG:{x}" for x in BASELINES] +
         [f"MNPS:{x}" for x in V3_SCALARS] + [f"MNPS:AR::{x}" for x in ar_names[4]]),
        ("v3_2_20s", "v3", 20, [f"qEEG:{x}" for x in BASELINES] +
         [f"MNPS:{x}" for x in V3_SCALARS] + [f"MNPS:AR::{x}" for x in ar_names[20]]),
    ]
    rows = []
    for realization, version, duration, dims in specs:
        pids = sorted({k[2] for k in summary if k[0] == version and k[1] == duration})
        for condition in TASKS:
            vectors = {pid: [participant_condition(summary, version, duration, pid, condition, d) for d in dims]
                       for pid in pids}
            for i, a in enumerate(dims):
                for j in range(i, len(dims)):
                    b = dims[j]
                    pairs = [(vectors[pid][i], vectors[pid][j]) for pid in pids
                             if vectors[pid][i] is not None and vectors[pid][j] is not None]
                    rho = None
                    if len(pairs) >= 3:
                        rho = finite(stats.spearmanr(np.asarray(pairs)[:, 0], np.asarray(pairs)[:, 1]).statistic)
                    rows.append({
                        "analysis": "B4_feature_dependence", "realization": realization, "condition": condition,
                        "dimension_a": a, "dimension_b": b, "participants_pairwise_complete": len(pairs),
                        "spearman_rho": rho, "qualified": False,
                    })
    return rows


def get_recording_features(summary: dict, version: str, duration: int, pid: str, session: str,
                           condition: str, dims: list[str]) -> list[float] | None:
    values = [summary.get((version, duration, pid, session, condition, dim)) for dim in dims]
    if any(v is None or not math.isfinite(float(v)) for v in values):
        return None
    return [float(v) for v in values]


def fold_map(participants: list[str]) -> dict[str, int]:
    ordered = sorted(set(participants), key=lambda pid: hashlib.sha256(f"{FOLD_ID}{pid}".encode()).hexdigest())
    return {pid: i % 5 for i, pid in enumerate(ordered)}


def fit_model(summary: dict, version: str, duration: int, dimensions: list[str], task: str,
              transfer: str, participants: list[str], cohort_participants: list[str]) -> tuple[dict, list[dict]]:
    # Fold identity is assigned over the complete frozen cohort, even when a
    # file-local support failure makes a participant ineligible in this stratum.
    folds = fold_map(cohort_participants)
    predictions, c_values, rows = {}, [], []
    for fold in range(5):
        train_ids = [pid for pid in participants if folds[pid] != fold]
        test_ids = [pid for pid in participants if folds[pid] == fold]
        x, y, groups = [], [], []
        for pid in train_ids:
            for condition, label in ((task, 1), ("eyesclosed", 0)):
                values = get_recording_features(summary, version, duration, pid, "ses-session1", condition, dimensions)
                if values is None:
                    raise RuntimeError(f"inner_training_row_incomplete:{version}:{duration}:{pid}")
                x.append(values); y.append(label); groups.append(pid)
        x, y, groups = np.asarray(x), np.asarray(y), np.asarray(groups)
        if len(set(groups)) < 4:
            raise RuntimeError("inner_group_cv_requires_four_participants")
        splitter = GroupKFold(n_splits=4)
        best_c, best_score = None, -math.inf
        for c in (0.01, 0.1, 1.0, 10.0):
            fold_scores = []
            for train_idx, valid_idx in splitter.split(x, y, groups):
                model = make_pipeline(StandardScaler(), LogisticRegression(C=c, solver="lbfgs", max_iter=5000))
                model.fit(x[train_idx], y[train_idx])
                fold_scores.append(balanced_accuracy_score(y[valid_idx], model.predict(x[valid_idx])))
            score = float(np.mean(fold_scores))
            if score > best_score:
                best_c, best_score = c, score
        model = make_pipeline(StandardScaler(), LogisticRegression(C=best_c, solver="lbfgs", max_iter=5000))
        model.fit(x, y)
        c_values.append(best_c)
        for pid in test_ids:
            preds = []
            for condition, label in ((task, 1), ("eyesclosed", 0)):
                values = get_recording_features(summary, version, duration, pid, transfer, condition, dimensions)
                if values is None:
                    raise RuntimeError(f"outer_test_row_incomplete:{version}:{duration}:{pid}")
                probability = float(model.predict_proba(np.asarray([values]))[0, 1])
                predicted = int(probability >= .5)
                preds.append((label, probability, predicted, condition))
                rows.append({
                    "model": f"{version}_{duration}s", "task": task, "transfer_session": transfer,
                    "participant_id": pid, "outer_fold": fold, "condition": condition, "label": label,
                    "probability_task": probability, "predicted_label": predicted, "selected_C": best_c,
                    "feature_count": len(dimensions), "qualified": False,
                })
            predictions[pid] = {"y": [preds[0][0], preds[1][0]],
                                "prob": [preds[0][1], preds[1][1]], "pred": [preds[0][2], preds[1][2]]}
    return {"predictions": predictions, "C_by_fold": c_values, "folds": folds}, rows


def observed_metrics(predictions: dict, participants: list[str]) -> tuple[float, float]:
    positive = np.asarray([predictions[p]["prob"][0] for p in participants])
    negative = np.asarray([predictions[p]["prob"][1] for p in participants])
    pos_pred = np.asarray([predictions[p]["pred"][0] for p in participants])
    neg_pred = np.asarray([predictions[p]["pred"][1] for p in participants])
    ba = .5 * (np.mean(pos_pred == 1) + np.mean(neg_pred == 0))
    diff = positive[:, None] - negative[None, :]
    auc = np.mean(diff > 0) + .5 * np.mean(diff == 0)
    return float(ba), float(auc)


def bootstrap_metric_distributions(predictions: dict, participants: list[str],
                                   indices: np.ndarray) -> dict[str, np.ndarray]:
    positive = np.asarray([predictions[p]["prob"][0] for p in participants])
    negative = np.asarray([predictions[p]["prob"][1] for p in participants])
    pos_pred = np.asarray([predictions[p]["pred"][0] for p in participants])
    neg_pred = np.asarray([predictions[p]["pred"][1] for p in participants])
    ba = .5 * (np.mean(pos_pred[indices] == 1, axis=1) + np.mean(neg_pred[indices] == 0, axis=1))
    auc = np.empty(len(indices), dtype=np.float64)
    for start in range(0, len(indices), 100):
        ix = indices[start:start + 100]
        positive_sample = positive[ix]
        negative_sample = negative[ix]
        delta = positive_sample[:, :, None] - negative_sample[:, None, :]
        auc[start:start + len(ix)] = np.mean(delta > 0, axis=(1, 2)) + .5 * np.mean(delta == 0, axis=(1, 2))
    return {"balanced_accuracy": ba, "roc_auc": auc}


def two_sided_bootstrap_p(differences: np.ndarray) -> float:
    below = (int(np.count_nonzero(differences <= 0)) + 1) / (len(differences) + 1)
    above = (int(np.count_nonzero(differences >= 0)) + 1) / (len(differences) + 1)
    return min(1.0, 2.0 * min(below, above))


def classification(summary: dict, ar_names: dict, cohort_participants: list[str]) -> tuple[list, list, list, list]:
    qdims = [f"qEEG:{x}" for x in BASELINES]
    candidates = [
        ("v2_3D", "v2", 8, [f"v2_3D::{x}" for x in V2_3D]),
        ("v2_9D", "v2", 8, [f"v2_9D::{x}" for x in V2_9D]),
        ("v3_2_4s", "v3", 4, [f"MNPS:{x}" for x in V3_SCALARS] + [f"MNPS:AR::{x}" for x in ar_names[4]]),
        ("v3_2_20s", "v3", 20, [f"MNPS:{x}" for x in V3_SCALARS] + [f"MNPS:AR::{x}" for x in ar_names[20]]),
    ]
    model_rows, increment_rows, direct_rows, prediction_rows = [], [], [], []
    model_cache = {}
    for task in CONTRASTS:
        for transfer in ("ses-session2", "ses-session3"):
            requirements = [("v2", 8, qdims), ("v3", 4, qdims), ("v3", 20, qdims)]
            requirements += [(ver, dur, qdims + aug) for _, ver, dur, aug in candidates]
            participants = []
            all_pids = sorted(set(cohort_participants))
            for pid in all_pids:
                complete = True
                for version, duration, dims in requirements:
                    for session in ("ses-session1", transfer):
                        for condition in (task, "eyesclosed"):
                            if get_recording_features(summary, version, duration, pid, session, condition, dims) is None:
                                complete = False
                                break
                        if not complete: break
                    if not complete: break
                if complete: participants.append(pid)
            if len(participants) < 12:
                raise RuntimeError(f"classification_common_complete_case_n_below_12:{task}:{transfer}:{len(participants)}")
            indices = stable_rng("B3_participant_bootstrap", task, transfer).integers(
                0, len(participants), size=(BOOTSTRAPS, len(participants)))
            outputs, dists = {}, {}
            all_models = []
            for name, version, duration, augdims in candidates:
                all_models.append((name, version, duration, qdims + augdims, name))
                qname = f"Q0_{version}_{duration}s"
                all_models.append((qname, version, duration, qdims, qname))
            for name, version, duration, dims, cache_name in all_models:
                fitted, pred_rows = fit_model(summary, version, duration, dims, task, transfer,
                                              participants, cohort_participants)
                outputs[name] = fitted
                model_cache[(task, transfer, name)] = fitted["predictions"]
                prediction_rows.extend([{**r, "model": name} for r in pred_rows])
                ba, auc = observed_metrics(fitted["predictions"], participants)
                distribution = bootstrap_metric_distributions(fitted["predictions"], participants, indices)
                dists[name] = distribution
                model_rows.append({
                    "model": name, "version": version, "duration_seconds": duration, "task": task,
                    "transfer_session": transfer, "test_participants": len(participants),
                    "outer_fold_counts": dict(Counter(fitted["folds"][pid] for pid in participants)),
                    "selected_C_by_fold": fitted["C_by_fold"], "balanced_accuracy": ba,
                    "balanced_accuracy_ci95_low": float(np.quantile(distribution["balanced_accuracy"], .025)),
                    "balanced_accuracy_ci95_high": float(np.quantile(distribution["balanced_accuracy"], .975)),
                    "roc_auc": auc, "roc_auc_ci95_low": float(np.quantile(distribution["roc_auc"], .025)),
                    "roc_auc_ci95_high": float(np.quantile(distribution["roc_auc"], .975)),
                    "feature_count": len(dims), "qualified": False,
                })
            q0_for = {"v2_3D": "Q0_v2_8s", "v2_9D": "Q0_v2_8s",
                      "v3_2_4s": "Q0_v3_4s", "v3_2_20s": "Q0_v3_20s"}
            for name, _, _, _ in candidates:
                q0 = q0_for[name]
                for metric in ("balanced_accuracy", "roc_auc"):
                    delta = dists[name][metric] - dists[q0][metric]
                    increment_rows.append({
                        "comparison": f"{name}_minus_{q0}", "model": name, "baseline_model": q0,
                        "task": task, "transfer_session": transfer, "metric": metric,
                        "paired_test_participants": len(participants),
                        "difference": float(observed_metrics(model_cache[(task, transfer, name)], participants)[0 if metric == "balanced_accuracy" else 1] -
                                            observed_metrics(model_cache[(task, transfer, q0)], participants)[0 if metric == "balanced_accuracy" else 1]),
                        "ci95_low": float(np.quantile(delta, .025)), "ci95_high": float(np.quantile(delta, .975)),
                        "p_raw_bootstrap_two_sided": two_sided_bootstrap_p(delta),
                        "qualified": False,
                    })
            for v2name in ("v2_3D", "v2_9D"):
                for v3name in ("v3_2_4s", "v3_2_20s"):
                    a, b = dists[v2name], dists[v3name]
                    for metric in ("balanced_accuracy", "roc_auc"):
                        delta = a[metric] - b[metric]
                        observed_a = observed_metrics(model_cache[(task, transfer, v2name)], participants)
                        observed_b = observed_metrics(model_cache[(task, transfer, v3name)], participants)
                        index = 0 if metric == "balanced_accuracy" else 1
                        direct_rows.append({
                            "comparison": f"{v2name}_minus_{v3name}", "v2_model": v2name, "v3_model": v3name,
                            "task": task, "transfer_session": transfer, "metric": metric,
                            "paired_test_participants": len(participants), "difference": observed_a[index] - observed_b[index],
                            "ci95_low": float(np.quantile(delta, .025)), "ci95_high": float(np.quantile(delta, .975)),
                            "p_raw_bootstrap_two_sided": two_sided_bootstrap_p(delta),
                            "qualified": False,
                        })
    if len(increment_rows) != 48 or len(direct_rows) != 48:
        raise RuntimeError(f"B3_multiplicity_family_size_mismatch:{len(increment_rows)}:{len(direct_rows)}")
    for row, adjusted in zip(increment_rows, holm([r["p_raw_bootstrap_two_sided"] for r in increment_rows])):
        row["p_holm_48_q0_increment_family"] = adjusted
    for row, adjusted in zip(direct_rows, holm([r["p_raw_bootstrap_two_sided"] for r in direct_rows])):
        row["p_holm_48_direct_family"] = adjusted
    return model_rows, increment_rows, direct_rows, prediction_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v2-root", type=Path, required=True)
    parser.add_argument("--v3-cohort-root", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.time()
    args.out.mkdir(parents=True, exist_ok=True)
    if any(args.out.iterdir()):
        raise RuntimeError(f"refusing_nonempty_output_root:{args.out}")
    v3_manifest, window_data, metadata, shards, v3_info = load_v3(args.v3_cohort_root)
    v2_files, v2_h5_audit, v2_run_manifests, v2_missing_recordings, v2_missing_audit = load_v2_h5(
        args.v2_root, window_data, metadata
    )
    qeeg_audit, baseline_info = extract_v2_qeeg(
        args.dataset_root, metadata, window_data, v3_info["runner_sha256"]
    )
    primary, support = summarize_windows(window_data, metadata)
    trimmed, trimmed_support = summarize_windows(window_data, metadata, trim=True)
    canonical, canonical_support = summarize_windows(window_data, metadata, canonical_only=True)
    b1_primary = b1(primary, v3_info["ar_names"])
    b2_primary = b2(primary, v3_info["ar_names"])
    b1_trimmed = b1(trimmed, v3_info["ar_names"], trim=True)
    b2_trimmed = b2(trimmed, v3_info["ar_names"], trim=True)
    b1_canonical = b1(canonical, v3_info["ar_names"], canonical=True)
    b2_canonical = b2(canonical, v3_info["ar_names"], canonical=True)
    cohort_participants = list(v3_manifest["frozen_identity"]["selected_participants"])
    class_metrics, class_increments, direct, predictions = classification(
        primary, v3_info["ar_names"], cohort_participants
    )
    dependence = b4_dependence(primary, v3_info["ar_names"])
    write_csv(args.out / "recording_support.csv", support)
    write_csv(args.out / "B4_trimmed_recording_support.csv", trimmed_support)
    write_csv(args.out / "B4_full_canonical_label_recording_support.csv", canonical_support)
    write_csv(args.out / "B1_task_sensitivity.csv", b1_primary)
    write_csv(args.out / "B2_reliability.csv", b2_primary)
    write_csv(args.out / "B4_trimmed_B1.csv", b1_trimmed)
    write_csv(args.out / "B4_trimmed_B2.csv", b2_trimmed)
    write_csv(args.out / "B4_full_canonical_label_B1.csv", b1_canonical)
    write_csv(args.out / "B4_full_canonical_label_B2.csv", b2_canonical)
    write_csv(args.out / "B3_classification_metrics.csv", class_metrics)
    write_csv(args.out / "B3_q0_increment_comparisons.csv", class_increments)
    write_csv(args.out / "B3_direct_v2_v3_comparisons.csv", direct)
    write_csv(args.out / "B3_predictions.csv", predictions)
    write_csv(args.out / "B4_feature_dependence.csv", dependence)
    write_csv(args.out / "v2_h5_integrity.csv", v2_h5_audit)
    write_csv(args.out / "v2_source_failure_records.csv", v2_missing_audit)
    write_csv(args.out / "v2_qeeg_source_audit.csv", qeeg_audit)
    write_csv(args.out / "B4_source_failure_records.csv", v3_info["file_failures"])
    provenance = []
    for (pid, session, task), source in sorted(metadata.items()):
        provenance.append({
            "version": "v3.2", "participant_id": pid, "session_id": session, "condition": task,
            "realization_id": source.get("sensor_realization_id"), "channel_count": source.get("channel_count"),
            "ordered_channel_labels": source.get("study_common_labels"),
            "source_header_labels": source.get("source_header_labels"),
            "channel_order_sha256": source.get("study_common_order_hash"),
            "channel_set_sha256": source.get("study_common_set_hash"),
            "declared_reference": source.get("declared_reference"),
            "applied_reference": "native source; no rereference applied",
            "reference_set_sha256": source.get("reference_set_hash"),
            "reference_set_reason": source.get("reference_set_hash_reason"),
            "source_aliases": source.get("explicit_casefold_aliases"), "qualified": False,
        })
    qc_root = args.v2_root / "ds004148" / "qc_artifacts"
    for row in qeeg_audit:
        pid, session, task = row["participant_id"], row["session_id"], row["condition"]
        qc_path = qc_root / f"{pid}_{session}_task-{task}_eeg_qc_artifacts.json"
        qc = json.loads(qc_path.read_text(encoding="utf-8")) if qc_path.is_file() else {}
        provenance.append({
            "version": "v2.0_candidate", "participant_id": pid, "session_id": session, "condition": task,
            "realization_id": "active_v2.0_candidate", "channel_count": row.get("header_channel_count"),
            "ordered_channel_labels": row.get("ordered_eeg_labels"),
            "source_header_labels": row.get("source_header_labels"),
            "channel_order_sha256": row.get("bids_order_sha256"),
            "channel_set_sha256": row.get("bids_set_sha256"),
            "declared_reference": "FCz", "applied_reference": qc.get("eeg_reference_mode"),
            "reference_status": qc.get("eeg_reference_status"),
            "reference_reason": qc.get("eeg_reference_reason"),
            "reference_set_sha256": None,
            "reference_set_reason": "applied average-reference set retained in v2 QC/provenance; not independently certified as identical to v3.2",
            "source_aliases": row.get("explicit_casefold_aliases"), "qualified": False,
        })
    write_csv(args.out / "B4_reference_and_channel_provenance.csv", provenance)
    write_json(args.out / "analysis_manifest.json", {
        "protocol_id": "SL-022B-MNPS-V2-V3.2-HEAD-TO-HEAD-001", "status": "complete",
        "qualified": False, "seed": SEED, "bootstrap_replicates": BOOTSTRAPS,
        "v2_h5_file_count": len(v2_files), "v3_shard_count": len(shards),
        "v2_git_rev": V2_GIT_REV, "v2_config_digest_sha256": V2_CONFIG_DIGEST,
        "v2_common_config_sha256": V2_COMMON_CONFIG_SHA256, "v2_overlay_sha256": V2_OVERLAY_SHA256,
        "v2_run_manifests": v2_run_manifests, "v2_missing_recordings": v2_missing_recordings,
        "v2_h5_window_count_distribution": dict(Counter(row["observed_window_count"] for row in v2_h5_audit
                                                          if row.get("observed_window_count") is not None)),
        "v2_partial_window_recordings": [
            {"participant_id": row["participant_id"], "session_id": row["session_id"],
             "condition": row["condition"], "observed_window_count": row["observed_window_count"],
             "requested_window_count": row["requested_window_count"],
             "unemitted_window_indices": row["unemitted_window_indices"],
             "last_window_end": row["last_window_end"]}
            for row in v2_h5_audit if row.get("status") == "partial_window_support"
        ],
        "v3_recording_manifest_count": len(metadata), "v3_qeeg_baseline_runner_sha256": baseline_info["baseline_runner_sha256"],
        "v3_frozen_runner_sha256": v3_info["runner_sha256"],
        "v3_AR_component_names": v3_info["ar_names"], "v3_frozen_hashes": v3_info["hashes"],
        "v3_run_manifest_sha256": sha256_file(args.v3_cohort_root / "run_manifest.json"),
        "sl020_verifier_sha256": v3_info["verifier_sha256"],
        "q0_complete_case_rule": "same participants complete in S1 and transfer session across Q0 at all three durations and all four augmentations",
        "canonical_label_rule": "file-local exclusion when a source BrainVision header has a capitalization alias against channels.tsv",
        "v2_reference": "active candidate configured for average reference; per-recording HDF5 QC/provenance retained",
        "v3_reference": "declared FCz; reference sensor/set unavailable; no rereference applied",
        "source_file_failures": v3_info["file_failures"], "v2_qeeg_source_audit_counts": {
            "status": dict(Counter(row["status"] for row in qeeg_audit)),
            "support_errors": baseline_info["support_errors"],
            "metadata_qc_warnings": baseline_info["metadata_qc_warnings"],
        }, "runtime_seconds": round(time.time() - started, 3),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

