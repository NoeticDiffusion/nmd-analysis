from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import h5py
import mne
import numpy as np
import pandas as pd

ARTICLE = Path(__file__).resolve().parent
NMD_ROOT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics")
DATA_ROOT = Path(r"K:\ExternalReceivedDatasets\openneuro\received\ds003838")
COVERAGE = ARTICLE / "outputs" / "v3_coverage_001_pilot_v1_20261008"
PILOT = ARTICLE / "outputs" / "bench_002_pilot_v1_20261008"
OUT = ARTICLE / "outputs" / "bench_002_fast_gate_fix_validation_20261009"
SUBJECT = "sub-032"
FAST_IDS = {"M1": "PCV", "M2": "TP", "E1": "OI", "E2": "SC"}
FULL_IDS = {"M1": "PCV", "M2": "TP", "M3": "AR", "D1": "NIE", "D3": "RD", "E1": "OI", "E2": "SC", "E3": "ED"}

sys.path.insert(0, str(NMD_ROOT / "core" / "src"))
sys.path.insert(0, str(NMD_ROOT / "mndm" / "src"))
sys.path.insert(0, str(ARTICLE))

import run_bench_002_pilot_v1 as bench  # noqa: E402
from mndm.mnps.v3_1.pipeline_measurements import compute_pipeline_window_measurements  # noqa: E402
from mndm.mnps.v3_1.realizations import CORE19_CHANNELS  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def parsed_value(value: object) -> Any:
    return json.loads(str(value))


def close_value(actual: object, expected: object) -> bool:
    left = np.asarray(actual, dtype=np.float64)
    right = np.asarray(expected, dtype=np.float64)
    return left.shape == right.shape and bool(np.allclose(left, right, rtol=0.0, atol=1e-10))


def read_set_crop(path: Path, labels: list[str], start: int, end: int) -> np.ndarray:
    with h5py.File(path, "r") as handle:
        data = handle["data"]
        if data.ndim != 2 or int(data.shape[1]) != len(labels):
            raise ValueError(f"EEGLAB data shape {data.shape} mismatches BIDS labels {len(labels)}")
        block = np.asarray(data[int(start):int(end), :], dtype=np.float64)
    result = block.T * 1e-6
    if not np.isfinite(result).all():
        raise ValueError(f"non-finite crop samples: {path}")
    return result


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"refusing to overwrite validation output: {OUT}")
    coverage_manifest_path = COVERAGE / "run_manifest.json"
    candidate_path = COVERAGE / "candidate_probe_status.csv"
    coverage_manifest = json.loads(coverage_manifest_path.read_text(encoding="utf-8"))
    require(
        bench.sha256_file(candidate_path) == coverage_manifest["outputs"][candidate_path.name]["sha256"],
        "coverage candidate table hash does not match its manifest",
    )
    coverage = pd.read_csv(candidate_path, keep_default_na=False)
    short = coverage.loc[
        coverage.subject.eq(SUBJECT)
        & coverage.duration_sec.astype(int).eq(4)
        & coverage.candidate_id.isin(FAST_IDS)
    ].copy()
    saved_twenty = coverage.loc[
        coverage.subject.eq(SUBJECT)
        & coverage.duration_sec.astype(int).eq(20)
        & coverage.load.astype(int).eq(13)
    ].copy()
    require(not short.empty and not saved_twenty.empty, "frozen parity rows are missing")

    mne.set_log_level("ERROR")
    eeg_dir = DATA_ROOT / SUBJECT / "eeg"
    eeg_set = eeg_dir / f"{SUBJECT}_task-memory_eeg.set"
    channels_tsv = eeg_dir / f"{SUBJECT}_task-memory_channels.tsv"
    events_tsv = eeg_dir / f"{SUBJECT}_task-memory_events.tsv"
    labels, _ = bench.load_labels(channels_tsv)
    with h5py.File(eeg_set, "r") as handle:
        source_sample_count = int(handle["data"].shape[0])
    trials, malformed = bench.parse_trials(events_tsv, SUBJECT, source_sample_count)
    require(malformed == 0 and len(trials) == 162, "unexpected parsed trial support")
    trial_by_id = {str(row["trial_id"]): row for row in trials}
    index_by_name = {name.casefold(): i for i, name in enumerate(labels)}
    surfaces = {
        "native": (labels, np.arange(len(labels), dtype=int)),
        "core19": (list(CORE19_CHANNELS), np.asarray([index_by_name[x.casefold()] for x in CORE19_CHANNELS], dtype=int)),
    }
    source_identity = coverage_manifest["source_file_sha256"][str(eeg_set)]
    sample_checks: list[dict[str, Any]] = []
    entries: list[dict[str, Any]] = []
    for surface in surfaces:
        for load in (5, 9, 13):
            rows = short.loc[short.surface.eq(surface) & short.load.astype(int).eq(load)]
            pcv_rows = rows.loc[rows.candidate_id.eq("M1")].sort_values(["trial_id", "window_start_sample_250hz"])
            require(not pcv_rows.empty, f"no saved four-second row for {surface}/load-{load}")
            chosen = pcv_rows.iloc[0]
            trial_rows = rows.loc[rows.trial_id.eq(chosen.trial_id)]
            require(set(trial_rows.candidate_id) == set(FAST_IDS), "fast-core parity candidates are incomplete")
            trial = trial_by_id[str(chosen.trial_id)]
            require(float(trial["source_duration_sec"]) < 20.0, "selected fast-core trial is not shorter than 20 seconds")
            require(
                len(bench.trial_window_starts(trial, source_sample_count // 4, bench.S20, bench.S20)) == 0,
                f"load-{load} test unexpectedly supports a 20-second window",
            )
            starts = bench.trial_window_starts(trial, source_sample_count // 4, bench.S4, bench.S4)
            require(len(starts) >= 1 and int(starts[0]) == int(chosen.window_start_sample_250hz), "fast-core grid differs from saved probe grid")
            if surface == "native" and load == 5:
                entries.append({
                    "surface": surface, "load": load, "duration": 4, "trial_id": str(chosen.trial_id),
                    "left": int(chosen.window_start_sample_250hz),
                    "right": int(chosen.window_end_sample_250hz_exclusive), "rows": trial_rows,
                })
        pcv_twenty = saved_twenty.loc[
            saved_twenty.surface.eq(surface) & saved_twenty.candidate_id.eq("M1")
        ].sort_values(["trial_id", "window_start_sample_250hz"])
        require(not pcv_twenty.empty, f"no saved 20-second baseline for {surface}")
        chosen20 = pcv_twenty.iloc[0]
        rows20 = saved_twenty.loc[saved_twenty.surface.eq(surface) & saved_twenty.trial_id.eq(chosen20.trial_id)]
        require(set(rows20.candidate_id) == set(FULL_IDS), "saved full-v3 candidate rows are incomplete")
        if surface == "core19":
            entries.append({
                "surface": surface, "load": 13, "duration": 20, "trial_id": str(chosen20.trial_id),
                "left": int(chosen20.window_start_sample_250hz),
                "right": int(chosen20.window_end_sample_250hz_exclusive), "rows": rows20,
            })

    # Process only short recording crops with ample filter context. Each crop
    # starts on the 250 Hz grid and contains complete target windows.
    source_context_samples_250hz = 30 * 250
    preprocessing_crops: list[dict[str, Any]] = []
    for trial_id in sorted({entry["trial_id"] for entry in entries}):
        trial = trial_by_id[trial_id]
        trial_entries = [entry for entry in entries if entry["trial_id"] == trial_id]
        crop_left_250 = max(0, min(int(entry["left"]) for entry in trial_entries) - source_context_samples_250hz)
        crop_right_250 = min(
            source_sample_count // 4,
            max(int(entry["right"]) for entry in trial_entries) + source_context_samples_250hz,
        )
        crop_left_source = crop_left_250 * 4
        crop_right_source = min(source_sample_count, crop_right_250 * 4)
        eeg_crop = read_set_crop(eeg_set, labels, crop_left_source, crop_right_source)
        filtered_crop, preprocessing = bench.preprocess_eeg(eeg_crop, labels)
        preprocessing_crops.append({
            "trial_id": trial_id, "source_start_sample": crop_left_source,
            "source_end_sample_exclusive": crop_right_source, "preprocessing": preprocessing,
        })
        for surface, (surface_labels, indices) in surfaces.items():
            surface_data = np.asarray(filtered_crop[indices], dtype=np.float64).copy()
            surface_data -= surface_data.mean(axis=0, keepdims=True)
            branch = {
                "branch_id": "mnps_bench_002_mne_common_preprocessing_v1",
                "reference_mode": "average_over_surface",
                "reference_set_sha256": bench.label_hash(surface_labels, ordered=False),
                "filter_band_hz": [1.0, 45.0], "amplitude_unit": "volts", "reference_status": "verified",
            }
            for entry in [item for item in trial_entries if item["surface"] == surface]:
                left = int(entry["left"])
                right = int(entry["right"])
                local_left = left - crop_left_250
                local_right = right - crop_left_250
                window = surface_data[:, local_left:local_right]
                require(window.shape == (len(surface_labels), (right - left)), "cropped window support mismatch")
                trial_start = (int(trial["source_start_sample"]) + 3) // 4
                trial_end = int(trial["source_end_sample_exclusive"]) // 4
                require(trial_start <= left < right <= trial_end, "saved window crosses a trial boundary")
                if int(entry["duration"]) == 4:
                    require(float(trial["source_duration_sec"]) < 20.0, "selected fast-core trial is not shorter than 20 seconds")
                    require(
                        len(bench.trial_window_starts(trial, source_sample_count // 4, bench.S20, bench.S20)) == 0,
                        f"load-{entry['load']} test unexpectedly supports a 20-second window",
                    )
                    starts = bench.trial_window_starts(trial, source_sample_count // 4, bench.S4, bench.S4)
                    require(len(starts) >= 1 and int(starts[0]) == left, "fast-core grid differs from saved probe grid")
                    actual, repeat_result = bench.compute_fast_core_window(
                        surface_data, surface_labels, trial, SUBJECT, surface, 0, local_left,
                        source_identity, branch, sample_origin=crop_left_250,
                    )
                    repeated, _ = bench.compute_fast_core_window(
                        surface_data, surface_labels, trial, SUBJECT, surface, 0, local_left,
                        source_identity, branch, sample_origin=crop_left_250,
                    )
                    require(
                        all(close_value(actual[feature], repeated[feature]) and np.array_equal(
                            np.asarray(actual[feature]), np.asarray(repeated[feature])
                        ) for feature in FAST_IDS.values()),
                        "identical input window did not reproduce exact fast-core values",
                    )
                    for candidate, feature in FAST_IDS.items():
                        expected_row = entry["rows"].loc[entry["rows"].candidate_id.eq(candidate)].iloc[0]
                        expected = parsed_value(expected_row.value_json)
                        require(close_value(actual[feature], expected), f"{surface}/load-{entry['load']}/{feature} parity mismatch")
                        require(str(expected_row.measurement_supported).casefold() == "true", "saved parity value is unsupported")
                        sample_checks.append({
                            "surface": surface, "load": entry["load"], "trial_id": trial_id,
                            "candidate_id": candidate, "feature": feature, "duration_sec": 4,
                            "start_sample_250hz": left, "end_sample_250hz_exclusive": right,
                            "within_1e-10_saved_value": True, "identical_window_repeat_exact": True,
                        })
                else:
                    support_qc = {
                        "source_is_continuous": True, "timestamps_uniform": True,
                        "input_samples_finite": bool(np.isfinite(window).all()), "gap_free": True,
                        "bad_interval_free": None, "within_recording_bounds": True,
                        "effective_filter_support_valid": True,
                        "effective_filter_support_status": "whole_recording_MNE_resample_notch_bandpass_context",
                    }
                    result20 = compute_pipeline_window_measurements(
                        window, surface_labels, sample_rate_hz=bench.TARGET_SFREQ,
                        window_start_sec=left / bench.TARGET_SFREQ, window_end_sec=right / bench.TARGET_SFREQ,
                        segment_id=f"{SUBJECT}_task-memory_{trial_id}",
                        source_identity=source_identity, input_branch=branch,
                        support_qc=support_qc, sequence_complexity_reference_count=32, activity_block_sec=2.0,
                    )
                    values20 = bench.v3_values(result20)
                    for candidate, feature in FULL_IDS.items():
                        expected_row = entry["rows"].loc[entry["rows"].candidate_id.eq(candidate)].iloc[0]
                        expected = parsed_value(expected_row.value_json)
                        actual_value = (
                            [values20[f"AR_pair_{i:02d}"] for i in range(1, 10)]
                            if candidate == "M3" else values20[feature]
                        )
                        require(close_value(actual_value, expected), f"{surface}/20s/{feature} parity mismatch")
                        sample_checks.append({
                            "surface": surface, "load": 13, "trial_id": trial_id,
                            "candidate_id": candidate, "feature": feature, "duration_sec": 20,
                            "start_sample_250hz": left, "end_sample_250hz_exclusive": right,
                            "within_1e-10_saved_value": True, "identical_window_repeat_exact": None,
                        })
            del surface_data
        del filtered_crop, eeg_crop

    OUT.mkdir(parents=True, exist_ok=False)
    checks_path = OUT / "parity_checks.csv"
    pd.DataFrame(sample_checks).to_csv(checks_path, index=False)
    report = [
        "# BENCH-002-FAST-GATE-FIX validation",
        "",
        "This bounded code-path check uses sub-032 and the frozen ds003838 v1.0.6 input. It does not rerun the six-participant benchmark.",
        "",
        "- Recomputed one saved 4 s load-5 native63 window; all four fast-core values matched the coverage audit within 1e-10 and a repeated identical input produced bitwise-identical values.",
        "- Recomputed one saved 20 s load-13 Core19 window; all eight full-v3 candidates, including the nine-element AR output, matched within 1e-10.",
        "- Checked the 4 s support grid against the parsed trial boundaries for each load and surface. Each selected load-5/9 trial returned no 20 s window. The frozen coverage table already contains supported fast-core values at all three loads on both surfaces.",
        "- The 4 s output is a separate realization. The full-v3 formulas and 20 s extraction loop were not changed; historical pilot outputs remain untouched.",
        "- This is a bounded parity check on one four-second and one twenty-second window. It is not a complete rerun of all trial windows and says nothing about short-window fidelity or qualification.",
        "",
        "See `parity_checks.csv` for the exact subject, surface, load, trial, sample interval, candidate, and parity outcome.",
    ]
    report_path = OUT / "results.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    output_files = [checks_path, report_path]
    manifest = {
        "schema": "mnps_bench_002_fast_gate_fix_validation.v1",
        "status": "passed",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "subject": SUBJECT,
        "dataset": "OpenNeuro ds003838 v1.0.6",
        "coverage_manifest_sha256": bench.sha256_file(coverage_manifest_path),
        "coverage_candidate_table_sha256": bench.sha256_file(candidate_path),
        "runner_path": str(ARTICLE / "run_bench_002_pilot_v1.py"),
        "runner_sha256": bench.sha256_file(ARTICLE / "run_bench_002_pilot_v1.py"),
        "validation_runner_sha256": bench.sha256_file(Path(__file__)),
        "input_set_sha256": source_identity,
        "preprocessing_crops": preprocessing_crops,
        "exact_value_checks": len(sample_checks),
        "four_second_windows_tested": 1,
        "four_second_exact_repeat_count": 1,
        "twenty_second_windows_tested": 1,
        "outputs": {p.name: {"bytes": p.stat().st_size, "sha256": bench.sha256_file(p)} for p in output_files},
        "claim_ceiling": "bounded deterministic implementation parity only; no estimator fidelity or scientific qualification",
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "output": str(OUT), "checks": len(sample_checks)}, indent=2))


if __name__ == "__main__":
    main()
