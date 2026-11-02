from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

# MNE imports Numba-cached helpers. The default cache under the user site stalls
# in this Windows sandbox; a task-local temp cache makes the same import/code
# path work without changing the numerical implementation.
os.environ.setdefault(
    "NUMBA_CACHE_DIR",
    r"C:\Users\Robin\AppData\Local\Temp\codex-mne-numba-cache",
)

import numpy as np
import pandas as pd

NMD_ROOT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics")
ARTICLE_ROOT = Path(r"J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385")
DATA_ROOT = Path(r"K:\ExternalReceivedDatasets\openneuro\received\ds003838")
PRIOR_OUT = ARTICLE_ROOT / "outputs" / "bench_002_pilot_v1_20261008"
OUT = ARTICLE_ROOT / "outputs" / "bench_002_preprocessing_parity_001_20261009_v2"
RUNNER_PATH = ARTICLE_ROOT / "run_bench_002_pilot_v1.py"
SUBJECT = "sub-032"
TARGET_CONDITIONS = ("control", "memory")
SURFACES = ("core19", "native")
RTOL = 1e-7
ATOL = 1e-10
COMPONENTS = ("PCV", "TP", "OI", "SC")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_array(data: np.ndarray) -> str:
    return sha256_bytes(np.ascontiguousarray(data).view(np.uint8).tobytes())


def load_runner() -> Any:
    sys.path.insert(0, str(NMD_ROOT / "core" / "src"))
    sys.path.insert(0, str(NMD_ROOT / "mndm" / "src"))
    spec = importlib.util.spec_from_file_location("bench_002_runner_for_parity", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load frozen benchmark runner at {RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def selected_rows(saved: pd.DataFrame) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for condition in TARGET_CONDITIONS:
        core = saved.loc[
            (saved["subject"] == SUBJECT)
            & (saved["surface"] == "core19")
            & (saved["condition"] == condition)
            & (saved["load"] == 13)
            & (saved["window_index"] == 0)
        ].sort_values(["trial_id", "window_start_sample_250hz"])
        if core.empty:
            raise ValueError(f"no frozen Core19 load-13 {condition} window for {SUBJECT}")
        reference = core.iloc[0].to_dict()
        for surface in SURFACES:
            match = saved.loc[
                (saved["subject"] == SUBJECT)
                & (saved["surface"] == surface)
                & (saved["trial_id"] == reference["trial_id"])
                & (saved["condition"] == condition)
                & (saved["load"] == 13)
                & (saved["window_index"] == reference["window_index"])
                & (saved["window_start_sample_250hz"] == reference["window_start_sample_250hz"])
            ]
            if len(match) != 1:
                raise ValueError(f"frozen window has no unique {surface} row: {condition}/{reference['trial_id']}")
            out[(condition, surface)] = match.iloc[0].to_dict()
    return out


def main() -> None:
    started = time.perf_counter()
    if OUT.exists():
        raise FileExistsError(f"refusing to overwrite parity output: {OUT}")
    OUT.mkdir(parents=True, exist_ok=False)

    runner = load_runner()
    prior_manifest = json.loads((PRIOR_OUT / "run_manifest.json").read_text(encoding="utf-8"))
    saved = pd.read_csv(PRIOR_OUT / "v3_window_values.csv")
    selection = selected_rows(saved)

    raw_path = DATA_ROOT / SUBJECT / "eeg" / f"{SUBJECT}_task-memory_eeg.set"
    channels_path = DATA_ROOT / SUBJECT / "eeg" / f"{SUBJECT}_task-memory_channels.tsv"
    expected_input_hash = prior_manifest["input_file_sha256"][str(raw_path)]
    expected_channels_hash = prior_manifest["input_file_sha256"][str(channels_path)]
    raw_hash = runner.sha256_file(raw_path)
    channels_hash = runner.sha256_file(channels_path)
    source_hash_ok = raw_hash == expected_input_hash
    channels_hash_ok = channels_hash == expected_channels_hash

    labels, _ = runner.load_labels(channels_path)
    if len(labels) != 63:
        raise ValueError(f"expected 63 ordered source EEG labels; got {len(labels)}")
    label_indices = {name.casefold(): index for index, name in enumerate(labels)}
    core_labels = list(runner.CORE19_CHANNELS)
    core_indices = np.asarray([label_indices[name.casefold()] for name in core_labels], dtype=int)
    native_indices = np.arange(len(labels), dtype=int)
    surface_specs = {
        "core19": (core_labels, core_indices),
        "native": (labels, native_indices),
    }

    for (condition, surface), row in selection.items():
        labels_for_surface, _ = surface_specs[surface]
        actual_order_hash = runner.label_hash(labels_for_surface)
        if actual_order_hash != str(row["channel_order_sha256"]):
            raise ValueError(f"channel-order hash mismatch in frozen row {condition}/{surface}")
        if int(row["window_end_sample_250hz_exclusive"]) - int(row["window_start_sample_250hz"]) != runner.S20:
            raise ValueError(f"frozen window is not exactly 20 s: {condition}/{surface}")
        if int(row["window_start_sample_250hz"]) * 4 >= 7_395_320:
            raise ValueError(f"frozen window starts beyond source recording: {condition}/{surface}")

    if not source_hash_ok or not channels_hash_ok:
        raise ValueError("current ds003838 source hashes differ from frozen BENCH-002 inputs")

    source_volts = runner.read_set(raw_path, labels, scale=1e-6)
    source_samples = int(source_volts.shape[1])
    filtered, preprocessing = runner.preprocess_eeg(source_volts, labels)
    del source_volts
    if filtered.shape != (len(labels), source_samples // 4):
        raise ValueError(f"unexpected MNE output shape {filtered.shape} from {source_samples} source samples")

    branch_hashes = {surface: runner.label_hash(spec[0], ordered=False) for surface, spec in surface_specs.items()}
    input_branch = {
        "branch_id": "mnps_bench_002_mne_common_preprocessing_v1",
        "reference_mode": "average_over_surface",
        "filter_band_hz": [1.0, 45.0],
        "amplitude_unit": "volts",
        "reference_status": "verified",
    }
    records: list[dict[str, Any]] = []
    for (condition, surface), row in selection.items():
        surface_labels, indices = surface_specs[surface]
        start = int(row["window_start_sample_250hz"])
        end = int(row["window_end_sample_250hz_exclusive"])
        expected_source_start = start * 4
        if expected_source_start % 4 != 0 or end > filtered.shape[1]:
            raise ValueError(f"source/target sample-grid mismatch for {condition}/{surface}")

        # Same continuous preprocessing and surface-average reference as the
        # saved run; retain a hash of each exact post-preprocessing window.
        surface_data = np.asarray(filtered[indices, :], dtype=np.float64).copy()
        surface_data -= surface_data.mean(axis=0, keepdims=True)
        window = surface_data[:, start:end]
        if window.shape != (len(surface_labels), runner.S20):
            raise ValueError(f"bad frozen window support {window.shape} for {condition}/{surface}")
        input_branch["reference_set_sha256"] = branch_hashes[surface]
        support_qc = {
            "source_is_continuous": True,
            "timestamps_uniform": True,
            "input_samples_finite": bool(np.isfinite(window).all()),
            "gap_free": True,
            "bad_interval_free": None,
            "within_recording_bounds": True,
            "effective_filter_support_valid": True,
            "effective_filter_support_status": "whole_recording_MNE_resample_notch_bandpass_context",
        }
        result = runner.compute_pipeline_window_measurements(
            window,
            surface_labels,
            sample_rate_hz=runner.TARGET_SFREQ,
            window_start_sec=start / runner.TARGET_SFREQ,
            window_end_sec=end / runner.TARGET_SFREQ,
            segment_id=f"{SUBJECT}_task-memory_{row['trial_id']}",
            source_identity=raw_hash,
            input_branch=input_branch,
            support_qc=support_qc,
            sequence_complexity_reference_count=32,
            activity_block_sec=2.0,
        )
        observed = runner.v3_values(result)
        filtered_window_hash = sha256_array(filtered[:, start:end])
        referenced_window_hash = sha256_array(window)
        for component in COMPONENTS:
            expected = float(row[component])
            actual = float(observed[component])
            difference = actual - expected
            within_tolerance = bool(np.isclose(actual, expected, rtol=RTOL, atol=ATOL))
            records.append({
                "subject": SUBJECT,
                "condition": condition,
                "trial_id": row["trial_id"],
                "surface": surface,
                "channel_count": len(surface_labels),
                "channel_order_sha256": runner.label_hash(surface_labels),
                "window_start_sample_250hz": start,
                "window_end_sample_250hz_exclusive": end,
                "window_start_source_sample_1000hz": expected_source_start,
                "filtered_input_window_sha256_native63": filtered_window_hash,
                "filtered_input_window_sha256_surface_average_ref": referenced_window_hash,
                "component": component,
                "saved_value": expected,
                "recomputed_value": actual,
                "absolute_difference": abs(difference),
                "rtol": RTOL,
                "atol": ATOL,
                "within_tolerance": within_tolerance,
            })
        del surface_data

    del filtered
    pd.DataFrame(records).to_csv(OUT / "component_parity.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    all_pass = all(bool(row["within_tolerance"]) for row in records)
    manifest = {
        "schema": "mnps_bench_002_preprocessing_parity.v1",
        "status": "pass" if all_pass else "fail",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "objective": "replay exact frozen load-13 20 s EEG windows using MNE preprocessing, then compare PCV/TP/OI/SC with saved BENCH-002 rows",
        "dataset": "OpenNeuro ds003838 v1.0.6",
        "subject": SUBJECT,
        "selected_window_count": len(selection),
        "selected_components": list(COMPONENTS),
        "tolerance": {"rtol": RTOL, "atol": ATOL},
        "source_file_sha256": raw_hash,
        "source_file_sha256_matches_frozen_run": source_hash_ok,
        "channels_file_sha256": channels_hash,
        "channels_file_sha256_matches_frozen_run": channels_hash_ok,
        "source_channel_order_sha256": runner.label_hash(labels),
        "source_channel_count": len(labels),
        "preprocessing": preprocessing,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "mne": runner.mne.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": __import__("scipy").__version__,
            "numba_cache_dir": os.environ.get("NUMBA_CACHE_DIR"),
        },
        "runner_sha256": runner.sha256_file(RUNNER_PATH),
        "measurement_pipeline_sha256": runner.sha256_file(NMD_ROOT / "mndm/src/mndm/mnps/v3_1/pipeline_measurements.py"),
        "historical_filtered_arrays_available": False,
        "interpretation_limit": "The previous run retained measurements and raw input hashes, not filtered sample arrays. This validation reprocessed hash-identical raw input with the recorded MNE pipeline and checks resulting saved component values; post-preprocessing byte identity to a historical array cannot be asserted.",
        "record_count": len(records),
        "all_components_within_tolerance": all_pass,
        "elapsed_seconds": time.perf_counter() - started,
        "output_sha256": {},
    }
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.name != "run_manifest.json":
            manifest["output_sha256"][path.name] = runner.sha256_file(path)
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    max_abs = max((float(row["absolute_difference"]) for row in records), default=0.0)
    print(json.dumps({
        "status": manifest["status"],
        "output": str(OUT),
        "records": len(records),
        "max_absolute_difference": max_abs,
        "mne": runner.mne.__version__,
        "elapsed_seconds": manifest["elapsed_seconds"],
    }, indent=2))


if __name__ == "__main__":
    main()
