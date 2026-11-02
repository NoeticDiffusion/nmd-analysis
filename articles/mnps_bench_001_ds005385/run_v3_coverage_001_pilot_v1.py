from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import platform
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ARTICLE = Path(__file__).resolve().parent
PROTOCOL = ARTICLE / "v3_coverage_001_protocol_v1_20261008.md"
NMD_ROOT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics")
DATA_ROOT = Path(r"K:\ExternalReceivedDatasets\openneuro\received\ds003838")
OUT = ARTICLE / "outputs" / "v3_coverage_001_pilot_v1_20261008"
PILOT = ARTICLE / "outputs" / "bench_002_pilot_v1_20261008"
PARTICIPANTS = ("sub-032", "sub-033", "sub-034", "sub-035", "sub-036", "sub-038")
DURATIONS_SEC = (4, 8, 12, 20)
SFREQ = 250.0
SAMPLES_PER_SEC = 250

sys.path.insert(0, str(NMD_ROOT / "core" / "src"))
sys.path.insert(0, str(NMD_ROOT / "mndm" / "src"))
sys.path.insert(0, str(ARTICLE))

import run_bench_002_pilot_v1 as bench  # noqa: E402
from mndm.mnps.v3_1.pipeline_measurements import (  # noqa: E402
    compute_pipeline_window_measurements,
)
from mndm.mnps.v3_1.realizations import CORE19_CHANNELS  # noqa: E402

SHORT_NAMES = {
    "M1": "PCV",
    "M2": "TP",
    "M3": "AR",
    "D1": "NIE",
    "D3": "RD",
    "E1": "OI",
    "E2": "SC",
    "E3": "ED",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): clean_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(item) for item in value]
    if isinstance(value, np.ndarray):
        return clean_json(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def finite_value(value: object) -> tuple[bool, int]:
    if value is None:
        return False, 0
    try:
        array = np.asarray(value, dtype=np.float64).reshape(-1)
    except (TypeError, ValueError, OverflowError):
        return False, 0
    return bool(array.size and np.isfinite(array).all()), int(array.size)


def candidate_row(
    measurement: dict[str, Any],
    *,
    subject: str,
    surface: str,
    trial: dict[str, Any],
    duration_sec: int,
    start_sample: int,
    end_sample: int,
    source: str,
    support_audit_status: str,
) -> dict[str, Any]:
    is_finite, value_length = finite_value(measurement.get("value"))
    computed = bool(measurement.get("computed"))
    valid = bool(measurement.get("valid"))
    reason = measurement.get("reason")
    return {
        "subject": subject,
        "surface": surface,
        "trial_id": str(trial["trial_id"]),
        "condition": str(trial["condition"]),
        "load": int(trial["load"]),
        "duration_sec": int(duration_sec),
        "window_start_sample_250hz": int(start_sample),
        "window_end_sample_250hz_exclusive": int(end_sample),
        "window_start_sec": start_sample / SFREQ,
        "window_end_sec": end_sample / SFREQ,
        "candidate_id": str(measurement.get("candidate_id", "")),
        "short_name": SHORT_NAMES.get(str(measurement.get("candidate_id", "")), ""),
        "estimator_id": str(measurement.get("estimator_id", "")),
        "units": str(measurement.get("units", "")),
        "computed": computed,
        "valid": valid,
        "qualified": bool(measurement.get("qualified")),
        "finite_value": is_finite,
        "value_length": value_length,
        "measurement_supported": bool(computed and valid and is_finite and reason is None),
        "status": str(measurement.get("status", "")),
        "reason": reason,
        "support_audit_status": support_audit_status,
        "data_origin": source,
        "value_json": json.dumps(clean_json(measurement.get("value")), ensure_ascii=False),
    }


def read_reused_twenty_second_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest_path = PILOT / "run_manifest.json"
    jsonl_path = PILOT / "v3_measurements.jsonl"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest["outputs"][jsonl_path.name]["sha256"]
    if sha256_file(jsonl_path) != expected:
        raise ValueError("frozen 20-second pilot JSONL hash does not match its manifest")

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for line in jsonl_path.open("r", encoding="utf-8"):
        record = json.loads(line)
        trial = record["trial"]
        key = (str(record["subject"]), str(record["surface"]), str(trial["trial_id"]))
        if key in seen:
            raise ValueError(f"duplicate frozen 20-second window for {key}")
        seen.add(key)
        start = int(record["window_start_sample_250hz"])
        end = int(record["window_end_sample_250hz_exclusive"])
        if end - start != 20 * SAMPLES_PER_SEC:
            raise ValueError(f"frozen pilot window is not 20 seconds: {key}")
        result = record["result"]
        if not math.isclose(float(result["window"]["end_sec"]) - float(result["window"]["start_sec"]), 20.0):
            raise ValueError(f"frozen pilot measurement payload is not 20 seconds: {key}")
        for measurement in result.get("measurements", []):
            rows.append(candidate_row(
                measurement,
                subject=str(record["subject"]),
                surface=str(record["surface"]),
                trial=trial,
                duration_sec=20,
                start_sample=start,
                end_sample=end,
                source="reused_frozen_bench_002_20s_pilot",
                support_audit_status=str(result.get("support_audit_status", "unknown")),
            ))
    if len(seen) != 648 or len(rows) != 648 * 8:
        raise ValueError(f"frozen 20-second baseline size mismatch: windows={len(seen)}, rows={len(rows)}")
    return rows, manifest


def main() -> None:
    if not PROTOCOL.is_file():
        raise FileNotFoundError(PROTOCOL)
    if not DATA_ROOT.is_dir():
        raise FileNotFoundError(DATA_ROOT)
    if not PILOT.is_dir():
        raise FileNotFoundError(PILOT)
    if OUT.exists():
        raise FileExistsError(f"refusing to overwrite an existing coverage output: {OUT}")
    OUT.mkdir(parents=True, exist_ok=False)

    import mne
    import yaml

    mne.set_log_level("ERROR")
    dataset_meta = json.loads((DATA_ROOT / "dataset_description.json").read_text(encoding="utf-8"))
    doi = str(dataset_meta.get("DatasetDOI", "")).removeprefix("doi:")
    changes_top = (DATA_ROOT / "CHANGES").read_text(encoding="utf-8").splitlines()[0].strip()
    if doi != "10.18112/openneuro.ds003838.v1.0.6" or not changes_top.startswith("1.0.6 "):
        raise ValueError(f"dataset release mismatch: doi={doi}, CHANGES={changes_top}")
    participants = pd.read_csv(DATA_ROOT / "participants.tsv", sep="\t", dtype=str).set_index("participant_id")
    baseline_rows, baseline_manifest = read_reused_twenty_second_rows()
    candidate_rows = list(baseline_rows)
    trial_rows: list[dict[str, Any]] = []
    input_hashes: dict[str, str] = {}
    source_annotation_rows: dict[str, dict[str, int]] = {}
    expected_labels: list[str] | None = None
    probe_windows_done = 0
    started = time.perf_counter()

    for subject in PARTICIPANTS:
        if subject not in participants.index or str(participants.loc[subject, "EEG_excluded"]).casefold() != "no":
            raise ValueError(f"{subject} is not EEG eligible in the pinned dataset")
        eeg_dir = DATA_ROOT / subject / "eeg"
        eeg_set = eeg_dir / f"{subject}_task-memory_eeg.set"
        channels_tsv = eeg_dir / f"{subject}_task-memory_channels.tsv"
        events_tsv = eeg_dir / f"{subject}_task-memory_events.tsv"
        for path in (eeg_set, channels_tsv, events_tsv):
            if not path.is_file():
                raise FileNotFoundError(path)
            input_hashes[str(path)] = sha256_file(path)

        labels, channel_frame = bench.load_labels(channels_tsv)
        if len(labels) != 63 or not (channel_frame["type"].astype(str).str.upper() == "EEG").all():
            raise ValueError(f"unexpected EEG channel metadata for {subject}")
        if expected_labels is None:
            expected_labels = labels
        elif labels != expected_labels:
            raise ValueError(f"ordered channels differ for {subject}")
        event_frame = pd.read_csv(events_tsv, sep="\t", dtype=str).fillna("")
        text_frame = event_frame.astype(str)
        bad_event_mask = text_frame.apply(
            lambda column: column.str.contains(r"\b(bad|artifact|gap|break)\b", case=False, regex=True)
        ).any(axis=1)
        source_annotation_rows[subject] = {
            "event_row_count": int(len(event_frame)),
            "bad_interval_like_event_row_count": int(bad_event_mask.sum()),
            "boundary_event_row_count": int(text_frame.apply(
                lambda column: column.str.contains(r"\bboundary\b", case=False, regex=True)
            ).any(axis=1).sum()),
        }

        eeg_volts = bench.read_set(eeg_set, labels, scale=1e-6)
        trials, malformed = bench.parse_trials(events_tsv, subject, eeg_volts.shape[1])
        if malformed or len(trials) != 162:
            raise ValueError(f"trial parse mismatch for {subject}: {len(trials)} trials, {malformed} malformed")
        source_sample_count = int(eeg_volts.shape[1])
        filtered, preprocessing = bench.preprocess_eeg(eeg_volts, labels)
        if filtered.shape[1] != source_sample_count // 4:
            raise ValueError(f"resampled grid mismatch for {subject}")
        del eeg_volts

        label_indices = {name.casefold(): index for index, name in enumerate(labels)}
        missing_core = [name for name in CORE19_CHANNELS if name.casefold() not in label_indices]
        if missing_core:
            raise ValueError(f"Core19 unavailable for {subject}: {missing_core}")
        surfaces = (
            ("native", labels, np.arange(len(labels), dtype=int)),
            ("core19", list(CORE19_CHANNELS), np.asarray([label_indices[name.casefold()] for name in CORE19_CHANNELS], dtype=int)),
        )

        for surface, surface_labels, indices in surfaces:
            surface_data = np.asarray(filtered[indices], dtype=np.float64).copy()
            surface_data -= surface_data.mean(axis=0, keepdims=True)
            if not np.isfinite(surface_data).all():
                raise ValueError(f"nonfinite filtered data for {subject}/{surface}")
            surface_hash = bench.label_hash(surface_labels, ordered=False)
            input_branch = {
                "branch_id": "mnps_bench_002_mne_common_preprocessing_v1",
                "reference_mode": "average_over_surface",
                "reference_set_sha256": surface_hash,
                "filter_band_hz": [1.0, 45.0],
                "amplitude_unit": "volts",
                "reference_status": "verified",
            }
            log_prefix = f"{subject}/{surface}"

            for trial in trials:
                trial_id = str(trial["trial_id"])
                grid_start = (int(trial["source_start_sample"]) + 3) // 4
                grid_end = int(trial["source_end_sample_exclusive"]) // 4
                for duration in DURATIONS_SEC:
                    window_samples = duration * SAMPLES_PER_SEC
                    span_samples = max(0, grid_end - grid_start)
                    possible = span_samples // window_samples
                    left = grid_start if possible else None
                    right = grid_start + window_samples if possible else None
                    finite_fraction = None
                    in_recording = None
                    if possible:
                        in_recording = bool(0 <= int(left) < int(right) <= surface_data.shape[1])
                        if not in_recording:
                            raise ValueError(f"trial window outside recording: {subject}/{surface}/{trial_id}/{duration}")
                        probe = surface_data[:, int(left):int(right)]
                        finite_fraction = float(np.isfinite(probe).mean())
                    else:
                        probe = None

                    trial_rows.append({
                        "subject": subject,
                        "surface": surface,
                        "trial_id": trial_id,
                        "condition": str(trial["condition"]),
                        "load": int(trial["load"]),
                        "duration_sec": duration,
                        "trial_source_duration_sec": float(trial["source_duration_sec"]),
                        "grid_span_sample_count": span_samples,
                        "possible_complete_nonoverlap_window_count": int(possible),
                        "structurally_eligible": bool(possible > 0),
                        "first_probe_start_sample_250hz": left,
                        "first_probe_end_sample_250hz_exclusive": right,
                        "first_probe_finite_fraction": finite_fraction,
                        "first_probe_in_recording_bounds": in_recording,
                        "unique_sample_count_available": int(possible * window_samples),
                        "recording_start_margin_sec": None if left is None else float(left / SFREQ),
                        "recording_end_margin_sec": None if right is None else float((surface_data.shape[1] - right) / SFREQ),
                        "source_is_continuous": True,
                        "timestamps_uniform": True,
                        "gap_free": True,
                        "bad_interval_free": None,
                        "upstream_filter_context": "whole_recording_MNE_resample_notch_bandpass; exact composite edge-safe margin not separately audited",
                        "candidate_local_filter_edge_status": "unknown_unassessed_for_PCV; no candidate-local filter for other seven metrics",
                    })

                    if not possible or duration == 20:
                        continue
                    assert probe is not None and left is not None and right is not None
                    support_qc = {
                        "source_is_continuous": True,
                        "timestamps_uniform": True,
                        "input_samples_finite": bool(np.isfinite(probe).all()),
                        "gap_free": True,
                        "bad_interval_free": None,
                        "within_recording_bounds": bool(in_recording),
                        "effective_filter_support_valid": None,
                        "effective_filter_support_status": "whole_recording_MNE_resample_notch_bandpass_context; exact composite edge-safe margin not separately audited",
                    }
                    result = compute_pipeline_window_measurements(
                        probe,
                        surface_labels,
                        sample_rate_hz=SFREQ,
                        window_start_sec=int(left) / SFREQ,
                        window_end_sec=int(right) / SFREQ,
                        segment_id=f"{subject}_task-memory_{trial_id}",
                        source_identity=input_hashes[str(eeg_set)],
                        input_branch=input_branch,
                        support_qc=support_qc,
                        sequence_complexity_reference_count=32,
                        activity_block_sec=2.0,
                    )
                    probe_windows_done += 1
                    for measurement in result.get("measurements", []):
                        candidate_rows.append(candidate_row(
                            measurement,
                            subject=subject,
                            surface=surface,
                            trial=trial,
                            duration_sec=duration,
                            start_sample=int(left),
                            end_sample=int(right),
                            source="computed_first_complete_window_per_trial",
                            support_audit_status=str(result.get("support_audit_status", "unknown")),
                        ))
                    if probe_windows_done % 24 == 0:
                        print(f"{log_prefix}: computed support probes={probe_windows_done}; elapsed={time.perf_counter()-started:.1f}s", flush=True)

            del surface_data
        del filtered

    trial_df = pd.DataFrame(trial_rows)
    candidate_df = pd.DataFrame(candidate_rows)
    if len(trial_df) != 972 * 2 * len(DURATIONS_SEC):
        raise ValueError(f"trial support row count mismatch: {len(trial_df)}")
    if probe_windows_done != 5184:
        raise ValueError(f"expected 5,184 short-duration candidate probes, got {probe_windows_done}")

    expected_twenty = {
        (str(row.subject), str(row.surface), str(row.trial_id)):
            (int(row.first_probe_start_sample_250hz), int(row.first_probe_end_sample_250hz_exclusive))
        for row in trial_df.loc[
            trial_df.duration_sec.eq(20) & trial_df.structurally_eligible
        ].itertuples(index=False)
    }
    reused_twenty = (
        candidate_df.loc[candidate_df.duration_sec.eq(20)]
        .drop_duplicates(["subject", "surface", "trial_id"])
    )
    observed_twenty = {
        (str(row.subject), str(row.surface), str(row.trial_id)):
            (int(row.window_start_sample_250hz), int(row.window_end_sample_250hz_exclusive))
        for row in reused_twenty.itertuples(index=False)
    }
    if observed_twenty != expected_twenty:
        missing = sorted(set(expected_twenty).difference(observed_twenty))[:5]
        unexpected = sorted(set(observed_twenty).difference(expected_twenty))[:5]
        mismatched = sorted(
            key for key in set(expected_twenty).intersection(observed_twenty)
            if expected_twenty[key] != observed_twenty[key]
        )[:5]
        raise ValueError(
            "frozen 20-second pilot keys/windows do not match the audited trial grid: "
            f"expected={len(expected_twenty)}, observed={len(observed_twenty)}, "
            f"missing={missing}, unexpected={unexpected}, mismatched={mismatched}"
        )

    support_summary = (
        trial_df.groupby(["duration_sec", "surface", "load"], as_index=False)
        .agg(
            total_trials=("trial_id", "nunique"),
            eligible_trials=("structurally_eligible", "sum"),
            possible_nonoverlap_windows=("possible_complete_nonoverlap_window_count", "sum"),
            unique_sample_count=("unique_sample_count_available", "sum"),
        )
    )
    candidate_summary = (
        candidate_df.groupby(["duration_sec", "surface", "load", "candidate_id", "short_name"], as_index=False)
        .agg(
            probe_count=("trial_id", "nunique"),
            computed_valid_finite_count=("measurement_supported", "sum"),
            qualified_count=("qualified", "sum"),
        )
    )
    reason_rows = []
    unsupported = candidate_df.loc[~candidate_df["measurement_supported"].astype(bool)]
    if len(unsupported):
        reason_rows = (
            unsupported.groupby(["duration_sec", "surface", "load", "candidate_id", "reason"], dropna=False)
            .size().rename("count").reset_index().to_dict(orient="records")
        )

    trial_df.to_csv(OUT / "trial_support_by_duration.csv", index=False)
    candidate_df.to_csv(OUT / "candidate_probe_status.csv", index=False)
    support_summary.to_csv(OUT / "support_summary.csv", index=False)
    candidate_summary.to_csv(OUT / "candidate_support_summary.csv", index=False)
    (OUT / "bad_interval_inventory.json").write_text(
        json.dumps({"schema": "v3_coverage_001_bad_interval_inventory.v1", "participants": source_annotation_rows,
                    "interpretation": "No bad-interval-free assertion is made; STATUS boundary markers are recording boundaries, not bad-interval annotations."},
                   indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report_lines = [
        "# V3-COVERAGE-001 results",
        "",
        "Six-participant support and implementation-gate audit for OpenNeuro ds003838 v1.0.6.",
        "No classifier or condition contrast was run.",
        "",
        f"- Frozen participants: {', '.join(PARTICIPANTS)}.",
        f"- Trials: {trial_df['trial_id'].nunique()}.",
        f"- Candidate windows computed at 4/8/12 s: {probe_windows_done} (first complete window per structurally eligible trial and surface).",
        "- The 20-second rows reuse the hash-checked BENCH-002 pilot; each is one complete window at load 13.",
        "- Candidate values are computability evidence only. Shorter-duration fidelity and cross-duration equivalence were not tested.",
        "",
        "## Structural trial coverage by load and duration",
        "",
        "Counts are per surface and include all six participants; 324 trials are present at each load.",
        "",
        "| Duration | Surface | Load | Eligible trials | Possible non-overlap windows |",
        "|---:|---|---:|---:|---:|",
    ]
    for row in support_summary.itertuples(index=False):
        report_lines.append(
            f"| {int(row.duration_sec)} s | {row.surface} | {int(row.load)} | "
            f"{int(row.eligible_trials)} / {int(row.total_trials)} | "
            f"{int(row.possible_nonoverlap_windows)} |"
        )
    report_lines.extend([
        "",
        "## Candidate computation",
        "",
        "See `candidate_support_summary.csv` for computed/valid/finite counts by candidate, duration, load, and surface; failures and their reasons are retained in `candidate_probe_status.csv`.",
        "",
        "The fast-core candidates PCV, TP, OI, and SC are extracted independently on the 4-second probes at every load. They are not gated on the presence of a 20-second full-v3 window. The BENCH-002 runner's outer loop caused the previous fast-core coverage restriction: it only invoked the pipeline inside the full-v3 20-second loop.",
        "",
        "## Support limitations",
        "",
        "All probe windows are sliced from the continuous, resampled and filtered recording, and finite in the selected source samples. `bad_interval_free` remains unknown: the BIDS events contain recording boundary markers but no bad-interval annotations. Upstream composite filter edge safety was not separately quantified; PCV's window-local 8–13-Hz IIR plus FFT-Hilbert edge fidelity remains unassessed at every duration. Candidate outputs therefore do not establish measurement fidelity or qualification.",
        "",
        "The named `candidate_id` and estimator formulas are unchanged. Duration is retained as an explicit realization dimension; 4-, 8-, 12-, and 20-second values must not be silently pooled or treated as equivalent.",
        "",
        "## Failure reasons",
        "",
    ])
    if reason_rows:
        report_lines.extend(["| Duration | Surface | Load | Candidate | Reason | Count |", "|---:|---|---:|---|---|---:|"])
        for row in reason_rows:
            report_lines.append(
                f"| {int(row['duration_sec'])} s | {row['surface']} | {int(row['load'])} | {row['candidate_id']} | {row['reason']} | {int(row['count'])} |"
            )
    else:
        report_lines.append("No candidate probe returned an unsupported, invalid, or nonfinite value.")
    report_lines.extend([
        "",
        "## Outputs",
        "",
        "- `v3_coverage_001_protocol_v1_20261008.md`: frozen support audit contract.",
        "- `trial_support_by_duration.csv`: trial-level support and unique-time counts.",
        "- `candidate_probe_status.csv`: per-window candidate status, value, and QC.",
        "- `support_summary.csv`, `candidate_support_summary.csv`: grouped support counts.",
        "- `bad_interval_inventory.json`: BIDS event annotation inventory.",
        "- `run_manifest.json`: source, code, protocol, reused-baseline, and output hashes.",
    ])
    (OUT / "results.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    implementation_paths = [
        NMD_ROOT / "mndm/src/mndm/mnps/v3_1/pipeline_measurements.py",
        NMD_ROOT / "mndm/src/mndm/mnps/v3_1/eeg_metrics.py",
        NMD_ROOT / "mndm/src/mndm/mnps/v3_1/realizations.py",
        ARTICLE / "run_bench_002_pilot_v1.py",
        Path(__file__).resolve(),
    ]
    implementation_hashes = {str(path): sha256_file(path) for path in implementation_paths}
    manifest = {
        "schema": "mndm.v3_coverage_001_pilot_manifest.v1",
        "status": "complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": "OpenNeuro ds003838 v1.0.6",
        "dataset_doi": doi,
        "participants": list(PARTICIPANTS),
        "trial_count": int(trial_df["trial_id"].nunique()),
        "surfaces": sorted(set(trial_df["surface"].astype(str))),
        "duration_sec": list(DURATIONS_SEC),
        "window_step_policy": "step_equals_duration; nonoverlapping; inward-rounded trial start",
        "candidate_probe_policy": "first complete window per structurally eligible trial and surface at 4/8/12 s; reuse verified 20 s pilot rows",
        "short_duration_probe_window_count": int(probe_windows_done),
        "candidate_probe_row_count": int(len(candidate_df)),
        "source_annotation_inventory": source_annotation_rows,
        "source_file_sha256": input_hashes,
        "implementation_sha256": implementation_hashes,
        "protocol_path": str(PROTOCOL),
        "protocol_sha256": sha256_file(PROTOCOL),
        "reused_bench_002_manifest": str(PILOT / "run_manifest.json"),
        "reused_bench_002_manifest_sha256": sha256_file(PILOT / "run_manifest.json"),
        "reused_20s_jsonl_sha256": sha256_file(PILOT / "v3_measurements.jsonl"),
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "mne": importlib.metadata.version("mne"),
        },
        "claim_ceiling": "computability and support only; no fidelity, equivalence, classification, or scientific qualification claim",
        "outputs": {},
        "elapsed_seconds": time.perf_counter() - started,
    }
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.name != "run_manifest.json":
            manifest["outputs"][path.name] = {
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
    (OUT / "run_manifest.json").write_text(
        json.dumps(clean_json(manifest), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": manifest["status"],
        "output": str(OUT),
        "trial_count": manifest["trial_count"],
        "short_duration_probe_window_count": manifest["short_duration_probe_window_count"],
        "candidate_probe_row_count": manifest["candidate_probe_row_count"],
        "elapsed_seconds": manifest["elapsed_seconds"],
    }, indent=2), flush=True)


def log(message: str) -> None:
    print(f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {message}", flush=True)


if __name__ == "__main__":
    main()
