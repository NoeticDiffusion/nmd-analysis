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

os.environ.setdefault(
    "NUMBA_CACHE_DIR",
    r"C:\Users\Robin\AppData\Local\Temp\codex-mne-numba-cache",
)

import numpy as np
import pandas as pd

NMD_ROOT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics")
ARTICLE_ROOT = Path(r"J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385")
DATA_ROOT = Path(r"K:\ExternalReceivedDatasets\openneuro\received\ds003838")
V002 = ARTICLE_ROOT / "outputs" / "v3_multiscale_fidelity_002_pilot_v1_20261009"
PROTOCOL = ARTICLE_ROOT / "v3_reference_sensitivity_001_protocol_v1_20261009.md"
OUT = ARTICLE_ROOT / "outputs" / "v3_reference_sensitivity_001_mne_pilot_v1_20261009"
RUNNER_PATH = ARTICLE_ROOT / "run_bench_002_pilot_v1.py"
DURATIONS = (4, 8, 12, 20)
PARTICIPANTS = ("sub-032", "sub-033", "sub-034", "sub-035", "sub-036", "sub-038")
MASTOID_LABELS = ("TP9", "TP10")
SURFACES = ("core19", "native63")
REFERENCES = ("average", "linked_mastoid")
SCALAR_NAMES = {"M1": "PCV", "M2": "TP", "D1": "NIE", "D3": "RD",
                "E1": "OI", "E2": "SC", "E3": "ED"}


def load_runner() -> Any:
    sys.path.insert(0, str(NMD_ROOT / "core" / "src"))
    sys.path.insert(0, str(NMD_ROOT / "mndm" / "src"))
    spec = importlib.util.spec_from_file_location("bench_002_runner_for_reference", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load benchmark preprocessing at {RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def value_components(candidate_id: str, value: Any) -> dict[str, float] | None:
    if value is None:
        return None
    if candidate_id == "M3":
        if not isinstance(value, list) or len(value) != 9:
            return None
        values = {f"AR_pair_{index:02d}": float(item) for index, item in enumerate(value, 1)}
    else:
        try:
            values = {SCALAR_NAMES.get(str(candidate_id), str(candidate_id)): float(value)}
        except (TypeError, ValueError, OverflowError):
            return None
    return values if all(np.isfinite(item) for item in values.values()) else None


def main() -> None:
    started = time.perf_counter()
    if OUT.exists():
        raise FileExistsError(f"refusing to overwrite reference sensitivity output: {OUT}")
    OUT.mkdir(parents=True, exist_ok=False)
    runner = load_runner()

    old_manifest = json.loads((V002 / "continuous_input_manifest.json").read_text(encoding="utf-8"))
    old_windows_path = V002 / "continuous_window_measurements.csv"
    old_windows = pd.read_csv(old_windows_path, usecols=[
        "subject", "surface_id", "anchor_index", "time_region", "window_start_sample_250hz",
        "duration_sec", "candidate_id",
    ])
    anchors_df = old_windows.loc[
        old_windows["surface_id"].eq("native63_average")
        & old_windows["duration_sec"].eq(20)
        & old_windows["candidate_id"].eq("M1"),
        ["subject", "anchor_index", "time_region", "window_start_sample_250hz"],
    ].drop_duplicates().sort_values(["subject", "anchor_index"])
    if anchors_df.groupby("subject").size().to_dict() != {
        "sub-032": 10, "sub-033": 8, "sub-034": 10,
        "sub-035": 12, "sub-036": 11, "sub-038": 10,
    }:
        raise ValueError("V002 anchor support differs from the frozen six-participant map")
    anchors_df.to_csv(OUT / "anchor_map.csv", index=False)
    anchor_map = {
        subject: group.to_dict(orient="records")
        for subject, group in anchors_df.groupby("subject", sort=False)
    }

    measurement_rows: list[dict[str, Any]] = []
    input_manifest: dict[str, Any] = {}
    for subject in PARTICIPANTS:
        source_record = old_manifest["participants"][subject]
        source_paths = {key: Path(value) for key, value in source_record["source_paths"].items()}
        set_path = source_paths["set"]
        channels_path = source_paths["channels_tsv"]
        sidecar_path = source_paths["eeg_json"]
        source_hashes = {key: file_hash(path) for key, path in source_paths.items()}
        if source_hashes != source_record["source_sha256"]:
            raise ValueError(f"{subject}: task-rest source hashes differ from frozen V002 inputs")
        labels, channel_frame = runner.load_labels(channels_path)
        if len(labels) != 63 or not (channel_frame["type"].astype(str).str.upper() == "EEG").all():
            raise ValueError(f"{subject}: expected 63 ordered EEG channels")
        label_idx = {label.casefold(): index for index, label in enumerate(labels)}
        missing = [name for name in (*runner.CORE19_CHANNELS, *MASTOID_LABELS) if name.casefold() not in label_idx]
        if missing:
            raise ValueError(f"{subject}: missing fixed surface/reference labels {missing}")
        core_labels = list(runner.CORE19_CHANNELS)
        core_indices = np.asarray([label_idx[name.casefold()] for name in core_labels], dtype=int)
        native_indices = np.arange(len(labels), dtype=int)
        mastoid_indices = np.asarray([label_idx[name.casefold()] for name in MASTOID_LABELS], dtype=int)

        source_volts = runner.read_set(set_path, labels, scale=1e-6)
        source_sample_count = int(source_volts.shape[1])
        filtered, prep = runner.preprocess_eeg(source_volts, labels)
        del source_volts
        mne_sample_count = int(prep["target_samples"])
        if filtered.shape != (len(labels), mne_sample_count):
            raise ValueError(f"{subject}: MNE sample grid mismatch {filtered.shape} vs {mne_sample_count}")

        mastoid_reference = filtered[mastoid_indices].mean(axis=0, keepdims=True)
        surfaces: dict[str, tuple[list[str], np.ndarray, np.ndarray]] = {
            "core19": (core_labels, np.asarray(filtered[core_indices], dtype=np.float64),
                       np.asarray(filtered[core_indices], dtype=np.float64) - mastoid_reference),
            "native63": (labels, np.asarray(filtered[native_indices], dtype=np.float64),
                         np.asarray(filtered[native_indices], dtype=np.float64) - mastoid_reference),
        }
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        input_manifest[subject] = {
            "source_paths": {key: str(path) for key, path in source_paths.items()},
            "source_sha256": source_hashes,
            "task_name_sidecar": sidecar.get("TaskName"),
            "task_name_interpreted_as_rest": False,
            "source_channel_order_sha256": runner.label_hash(labels),
            "core19_channel_order_sha256": runner.label_hash(core_labels),
            "mastoid_reference_labels": list(MASTOID_LABELS),
            "source_sample_count_1000hz": source_sample_count,
            "mne_resampled_sample_count_250hz": mne_sample_count,
            "v002_polyphase_resampled_sample_count_250hz": int(source_record["resampled_sample_count"]),
            "mne_minus_v002_sample_count": mne_sample_count - int(source_record["resampled_sample_count"]),
            "preprocessing": prep,
            "anchor_count": len(anchor_map[subject]),
        }

        for anchor in anchor_map[subject]:
            anchor_index = int(anchor["anchor_index"])
            start = int(anchor["window_start_sample_250hz"])
            if start < 0 or start + 20 * int(runner.TARGET_SFREQ) > mne_sample_count:
                raise ValueError(f"{subject}/{anchor_index}: fixed V002 anchor is outside current recording")
            for surface in SURFACES:
                channel_labels, average_source, linked_data = surfaces[surface]
                average_data = average_source - average_source.mean(axis=0, keepdims=True)
                for reference in REFERENCES:
                    data = average_data if reference == "average" else linked_data
                    ref_mode = "average_over_surface" if reference == "average" else "linked_mastoid_TP9_TP10"
                    ref_labels = channel_labels if reference == "average" else list(MASTOID_LABELS)
                    branch = {
                        "branch_id": "v3_reference_sensitivity_001_mne_continuous_v1",
                        "reference_mode": ref_mode,
                        "reference_set_sha256": runner.label_hash(ref_labels, ordered=False),
                        "filter_band_hz": [1.0, 45.0],
                    }
                    for duration in DURATIONS:
                        sample_count = int(duration * runner.TARGET_SFREQ)
                        stop = start + sample_count
                        window = data[:, start:stop]
                        if window.shape != (len(channel_labels), sample_count):
                            raise ValueError(f"{subject}/{anchor_index}/{surface}/{reference}: window support mismatch")
                        support_qc = {
                            "source_is_continuous": True,
                            "timestamps_uniform": True,
                            "input_samples_finite": bool(np.isfinite(window).all()),
                            "gap_free": True,
                            "bad_interval_free": None,
                            "within_recording_bounds": True,
                            "effective_filter_support_valid": None,
                            "effective_filter_support_status": "whole_recording_MNE_resample_notch_bandpass_context; edge support not quantified",
                        }
                        result = runner.compute_pipeline_window_measurements(
                            window,
                            channel_labels,
                            sample_rate_hz=runner.TARGET_SFREQ,
                            window_start_sec=start / runner.TARGET_SFREQ,
                            window_end_sec=stop / runner.TARGET_SFREQ,
                            segment_id=f"{subject}_task-rest_anchor{anchor_index:02d}",
                            source_identity=source_hashes["set"],
                            input_branch=branch,
                            support_qc=support_qc,
                            sequence_complexity_reference_count=32,
                            activity_block_sec=2.0,
                        )
                        for measurement in result.get("measurements", []):
                            measurement_rows.append({
                                "subject": subject,
                                "surface_id": surface,
                                "reference": reference,
                                "reference_mode": ref_mode,
                                "anchor_index": anchor_index,
                                "time_region": str(anchor["time_region"]),
                                "window_start_sample_250hz": start,
                                "window_start_sec": start / runner.TARGET_SFREQ,
                                "duration_sec": duration,
                                "sample_count": sample_count,
                                "candidate_id": measurement.get("candidate_id"),
                                "candidate": measurement.get("short_name"),
                                "value_json": json_value(measurement.get("value")),
                                "computed": bool(measurement.get("computed")),
                                "valid": bool(measurement.get("valid")),
                                "qualified": bool(measurement.get("qualified")),
                                "status": measurement.get("status"),
                                "reason": measurement.get("reason"),
                                "support_audit_status": measurement.get("details", {}).get("support_audit_status"),
                                "bad_interval_free": None,
                                "channel_count": len(channel_labels),
                                "channel_order_sha256": runner.label_hash(channel_labels),
                                "channel_set_sha256": runner.label_hash(channel_labels, ordered=False),
                                "reference_set_sha256": branch["reference_set_sha256"],
                                "source_set_sha256": source_hashes["set"],
                            })
        del filtered

    values = pd.DataFrame(measurement_rows)
    values.to_csv(OUT / "reference_measurements.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    (OUT / "input_manifest.json").write_text(json.dumps({
        "schema": "v3_reference_sensitivity_001_inputs.v1",
        "participants": input_manifest,
        "anchor_map_source": str(old_windows_path),
        "anchor_map_source_sha256": file_hash(old_windows_path),
        "claim_ceiling": "descriptive MNE-preprocessed continuous reference sensitivity; no equivalence or qualification",
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    paired_rows: list[dict[str, Any]] = []
    key_columns = ["subject", "surface_id", "anchor_index", "duration_sec", "candidate_id"]
    for key, group in values.groupby(key_columns, sort=False, dropna=False):
        ref_rows = {str(row["reference"]): row for _, row in group.iterrows()}
        if set(ref_rows) != set(REFERENCES):
            continue
        average_row, linked_row = ref_rows["average"], ref_rows["linked_mastoid"]
        average_values = value_components(str(average_row["candidate_id"]), json.loads(average_row["value_json"]))
        linked_values = value_components(str(linked_row["candidate_id"]), json.loads(linked_row["value_json"]))
        if average_values is None or linked_values is None or average_values.keys() != linked_values.keys():
            continue
        for component in average_values:
            average_value = average_values[component]
            linked_value = linked_values[component]
            paired_rows.append({
                "subject": key[0],
                "surface_id": key[1],
                "anchor_index": key[2],
                "duration_sec": key[3],
                "candidate_id": key[4],
                "component": component,
                "average_reference_value": average_value,
                "linked_mastoid_value": linked_value,
                "signed_difference_average_minus_linked": average_value - linked_value,
                "absolute_difference": abs(average_value - linked_value),
                "channel_count": int(average_row["channel_count"]),
                "channel_order_sha256": average_row["channel_order_sha256"],
                "average_reference_set_sha256": average_row["reference_set_sha256"],
                "linked_reference_set_sha256": linked_row["reference_set_sha256"],
            })
    paired = pd.DataFrame(paired_rows)
    paired.to_csv(OUT / "paired_anchor_differences.csv", index=False)
    by_participant = (
        paired.groupby(["subject", "surface_id", "duration_sec", "candidate_id", "component"], as_index=False)
        .agg(paired_anchor_count=("anchor_index", "nunique"),
             median_signed_difference=("signed_difference_average_minus_linked", "median"),
             median_absolute_difference=("absolute_difference", "median"),
             p95_absolute_difference=("absolute_difference", lambda x: float(np.quantile(x, 0.95))),
             maximum_absolute_difference=("absolute_difference", "max"))
    )
    by_participant["claim_ceiling"] = "descriptive within-participant reference sensitivity; no equivalence"
    by_participant.to_csv(OUT / "reference_sensitivity_by_participant.csv", index=False)

    protocol_hash = file_hash(PROTOCOL)
    estimator_path = NMD_ROOT / "mndm/src/mndm/mnps/v3_1/pipeline_measurements.py"
    manifest: dict[str, Any] = {
        "schema": "v3_reference_sensitivity_001_run.v1",
        "status": "complete",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "protocol_path": str(PROTOCOL),
        "protocol_sha256": protocol_hash,
        "dataset": "OpenNeuro ds003838 v1.0.6; continuous BIDS task-rest files, not assumed physiological rest",
        "participants": list(PARTICIPANTS),
        "anchor_count_by_participant": anchors_df.groupby("subject").size().to_dict(),
        "anchor_count_total": len(anchors_df),
        "durations_sec": list(DURATIONS),
        "surfaces": list(SURFACES),
        "references": list(REFERENCES),
        "measurement_rows": len(values),
        "paired_component_rows": len(paired),
        "participant_summary_rows": len(by_participant),
        "independent_unit": "participant; anchor windows are repeated within participant",
        "source_branch": "MNE Raw.resample, 50 Hz notch, 1-45 Hz zero-phase FIR, then offline reference variants",
        "bad_interval_free": "unknown",
        "effective_filter_support": "not quantified; recorded as QC, no gating",
        "native63_linked_mastoid_note": "TP9/TP10 remain in the 63-channel measurement set and become zero in this linked-mastoid realization",
        "task_labels_or_classifier_used": False,
        "all_values_unqualified": bool(not values["qualified"].any()),
        "estimator_path": str(estimator_path),
        "estimator_sha256": file_hash(estimator_path),
        "runner_path": str(RUNNER_PATH),
        "runner_sha256": file_hash(RUNNER_PATH),
        "v002_anchor_source_sha256": file_hash(old_windows_path),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "mne": runner.mne.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": __import__("scipy").__version__,
            "numba_cache_dir": os.environ.get("NUMBA_CACHE_DIR"),
        },
        "elapsed_seconds": time.perf_counter() - started,
        "outputs_sha256": {},
    }
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.name != "run_manifest.json":
            manifest["outputs_sha256"][path.name] = file_hash(path)
    report_lines = [
        "# V3-REFERENCE-SENSITIVITY-001 MNE-matched results",
        "",
        f"Status: **complete**. Six participants, {len(anchors_df)} fixed continuous anchors, four nested durations, Core19 and native63, with average and linked-mastoid references.",
        "",
        "This branch reuses the exact V002 anchor locations but reprocesses the continuous BIDS task-rest files with the MNE BENCH-002 preprocessing path. The sidecar TaskName is retained as metadata; the files are not assumed to be physiological rest. No events or task labels were read.",
        "",
        "Average-reference versus linked-mastoid differences are paired within identical sample windows and channel labels. Core19 is the primary fixed 19-channel comparison. Native63 is secondary; TP9/TP10 remain in that output channel set and become zero in its linked-mastoid realization.",
        "",
        "The six participants are the independent units; anchors are repeated observations. Source bad-interval status and upstream composite filter-edge support remain unknown. Results are descriptive and unqualified; no equivalence or task-discrimination claim is made. The raw-polyphase V002 values are not pooled with this MNE branch.",
        "",
        "See `anchor_map.csv`, `reference_measurements.csv`, `paired_anchor_differences.csv`, `reference_sensitivity_by_participant.csv`, `input_manifest.json`, and `run_manifest.json`.",
    ]
    (OUT / "results.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    manifest["outputs_sha256"]["results.md"] = file_hash(OUT / "results.md")
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "output": str(OUT),
                      "measurement_rows": len(values), "paired_component_rows": len(paired),
                      "participant_summary_rows": len(by_participant),
                      "elapsed_seconds": manifest["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
