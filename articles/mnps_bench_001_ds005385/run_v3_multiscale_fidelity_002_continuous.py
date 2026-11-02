from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy import signal

NMD_ROOT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics")
ARTICLE = Path(r"J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385")
DATA = Path(r"K:\ExternalReceivedDatasets\openneuro\received\ds003838")
OUT = ARTICLE / "outputs" / "v3_multiscale_fidelity_002_pilot_v1_20261009"
AMENDMENT = ARTICLE / "v3_multiscale_fidelity_002_continuous_input_amendment_v1_20261009.md"
sys.path.insert(0, str(NMD_ROOT / "mndm" / "src"))
from mndm.mnps.v3_1.pipeline_measurements import compute_pipeline_window_measurements
from mndm.mnps.v3_1.realizations import CORE19_CHANNELS

PARTICIPANTS = ("sub-032", "sub-033", "sub-034", "sub-035", "sub-036", "sub-038")
DURATIONS = (4, 8, 12, 20)
SFREQ = 250.0
MARGIN_SAMPLES = 5 * int(SFREQ)
WINDOW_20_SAMPLES = 20 * int(SFREQ)
SHORT = {"M1": "PCV", "M2": "TP", "M3": "AR", "D1": "NIE",
         "D3": "RD", "E1": "OI", "E2": "SC", "E3": "ED"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def json_value(value: Any) -> str:
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if isinstance(value, np.generic):
        value = value.item()
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temp, index=False)
    temp.replace(path)


def atomic_text(value: str, path: Path) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(value, encoding="utf-8", newline="\n")
    temp.replace(path)


def ccc(a: np.ndarray, b: np.ndarray) -> float | None:
    if len(a) < 2 or len(a) != len(b):
        return None
    vx = float(np.var(a, ddof=1))
    vy = float(np.var(b, ddof=1))
    den = vx + vy + float((np.mean(a) - np.mean(b)) ** 2)
    if den <= 0 or not math.isfinite(den):
        return None
    cov = float(np.cov(a, b, ddof=1)[0, 1])
    return float(2 * cov / den)


def correlation(a: np.ndarray, b: np.ndarray) -> float | None:
    if len(a) < 2 or len(a) != len(b) or np.std(a) == 0 or np.std(b) == 0:
        return None
    return float(pd.Series(a).corr(pd.Series(b), method="spearman"))


def read_bids_recording(subject: str) -> tuple[list[str], np.ndarray, dict[str, Any], dict[str, str]]:
    eeg_dir = DATA / subject / "eeg"
    stem = f"{subject}_task-rest"
    set_path = eeg_dir / f"{stem}_eeg.set"
    channels_path = eeg_dir / f"{stem}_channels.tsv"
    json_path = eeg_dir / f"{stem}_eeg.json"
    if not all(path.is_file() for path in (set_path, channels_path, json_path)):
        raise FileNotFoundError(f"missing task-rest BIDS EEG files for {subject}")
    channels = pd.read_csv(channels_path, sep="\t", dtype=str, keep_default_na=False)
    labels = channels["name"].astype(str).str.strip().tolist()
    if channels["type"].str.upper().ne("EEG").any() or len(labels) != 63:
        raise ValueError(f"{subject}: expected 63 ordered EEG channels")
    units = channels["units"].str.casefold()
    if not units.eq("microv").all():
        raise ValueError(f"{subject}: BIDS channel units are not all microV: {units.unique().tolist()}")
    metadata = json.loads(json_path.read_text(encoding="utf-8"))
    if metadata.get("RecordingType") != "continuous":
        raise ValueError(f"{subject}: source is not declared continuous")
    source_rate = float(metadata["SamplingFrequency"])
    if not math.isclose(source_rate, 1000.0):
        raise ValueError(f"{subject}: unexpected source rate {source_rate}")
    with h5py.File(set_path, "r") as handle:
        dataset = handle["data"]
        if dataset.ndim != 2 or int(dataset.shape[1]) != len(labels):
            raise ValueError(f"{subject}: EEGLAB/HDF5 data shape does not match BIDS channels")
        raw_v = np.asarray(dataset[:], dtype=np.float64).T * 1e-6
    if not np.isfinite(raw_v).all():
        raise ValueError(f"{subject}: raw input contains nonfinite samples")
    resampled = signal.resample_poly(raw_v, up=1, down=4, axis=-1)
    paths = {"set": str(set_path), "channels_tsv": str(channels_path), "eeg_json": str(json_path)}
    return labels, np.asarray(resampled, dtype=np.float64), metadata, paths


def context_pcv(values: np.ndarray) -> np.ndarray:
    try:
        sos = signal.butter(4, [8.0, 13.0], btype="bandpass", fs=SFREQ, output="sos")
        filtered = signal.sosfiltfilt(sos, values, axis=-1, padtype=None, padlen=0)
        analytic = signal.hilbert(filtered, axis=-1)
        amplitude = np.abs(analytic)
        if not np.isfinite(amplitude).all() or np.any(amplitude == 0.0):
            return np.full(values.shape[-1], np.nan)
        return np.abs(np.mean(analytic / amplitude, axis=0))
    except (ValueError, FloatingPointError, np.linalg.LinAlgError):
        return np.full(values.shape[-1], np.nan)


def signal_qc(window: np.ndarray) -> dict[str, Any]:
    uv = window * 1e6
    med = np.median(uv, axis=1, keepdims=True)
    robust = 1.4826 * np.median(np.abs(uv - med), axis=1)
    p2p = np.ptp(uv, axis=1)
    freqs, psd = signal.welch(
        window, fs=SFREQ, window="hann", nperseg=min(window.shape[1], 4 * int(SFREQ)),
        noverlap=min(window.shape[1], 4 * int(SFREQ)) // 2, detrend="constant",
        scaling="density", axis=-1,
    )
    low = (freqs >= 1.0) & (freqs <= 45.0)
    line = (freqs >= 48.0) & (freqs <= 52.0)
    high = (freqs >= 30.0) & (freqs <= 45.0)
    channel_low = np.mean(psd[:, low], axis=1) if np.any(low) else np.asarray([])
    channel_line = np.mean(psd[:, line], axis=1) if np.any(line) else np.asarray([])
    line_ratio = None
    if channel_low.size and channel_line.size:
        usable = channel_low > 0
        if np.any(usable):
            line_ratio = float(np.median(channel_line[usable] / channel_low[usable]))
    return {
        "flat_channel_fraction_exact": float(np.mean(np.ptp(window, axis=1) == 0.0)),
        "robust_amplitude_mad_uv_median": float(np.median(robust)),
        "robust_amplitude_mad_uv_p95": float(np.quantile(robust, 0.95)),
        "peak_to_peak_uv_median": float(np.median(p2p)),
        "peak_to_peak_uv_p95": float(np.quantile(p2p, 0.95)),
        "power_30_45_hz_v2_per_hz_channel_median": (
            float(np.median(np.mean(psd[:, high], axis=1))) if np.any(high) else None
        ),
        "line_noise_48_52_to_1_45_ratio_median": line_ratio,
        "qc_is_descriptive_only": True,
    }


def channel_hash(labels: list[str] | tuple[str, ...]) -> str:
    return sha256_text("\n".join(sorted(x.strip().casefold() for x in labels)))


def json_numeric(value: object) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value


def summarize_participants(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    supported = frame.loc[frame["computed"].astype(bool) & frame["value_json"].astype(str).ne("")]
    for keys, group in supported.groupby(["subject", "surface_id", "duration_sec", "candidate_id"]):
        subject, surface, duration, cid = keys
        vectors = [np.asarray(json_numeric(value), dtype=float).reshape(-1)
                   for value in group["value_json"]]
        if cid == "M3":
            matrix = np.vstack(vectors)
            median = np.median(matrix, axis=0).tolist()
            mad = np.median(np.abs(matrix - np.median(matrix, axis=0)), axis=0).tolist()
        else:
            values = np.asarray([float(v[0]) for v in vectors], dtype=float)
            median = float(np.median(values))
            mad = float(np.median(np.abs(values - np.median(values))))
        rows.append({
            "subject": subject, "surface_id": surface, "duration_sec": duration,
            "candidate_id": cid, "candidate": SHORT[cid], "anchor_count": int(group["anchor_index"].nunique()),
            "median_value_json": json_value(median), "median_absolute_deviation_json": json_value(mad),
        })
    return pd.DataFrame(rows)


def compare_durations(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    supported = frame.loc[frame["computed"].astype(bool) & frame["value_json"].astype(str).ne("")]
    for (subject, surface, cid), group in supported.groupby(["subject", "surface_id", "candidate_id"]):
        wide = {int(d): subset.set_index("anchor_index")["value_json"]
                for d, subset in group.groupby("duration_sec")}
        if 20 not in wide:
            continue
        for duration in (4, 8, 12):
            if duration not in wide:
                continue
            common = sorted(set(wide[duration].index) & set(wide[20].index))
            if cid == "M3":
                abs_values = []
                for anchor in common:
                    short = np.asarray(json_numeric(wide[duration].loc[anchor]), dtype=float).reshape(-1)
                    long = np.asarray(json_numeric(wide[20].loc[anchor]), dtype=float).reshape(-1)
                    abs_values.extend(np.abs(short - long[:len(short)]).tolist())
                rows.append({
                    "subject": subject, "surface_id": surface, "candidate_id": cid,
                    "duration_sec": duration, "reference_duration_sec": 20,
                    "paired_anchor_count": len(common), "spearman_rank_correlation": None,
                    "lin_concordance_correlation": None, "median_signed_difference": None,
                    "median_absolute_difference": float(np.median(abs_values)) if abs_values else None,
                    "p95_absolute_component_difference": float(np.quantile(abs_values, 0.95)) if abs_values else None,
                    "max_absolute_component_difference": float(np.max(abs_values)) if abs_values else None,
                    "comparison_type": "AR component-wise duration vector prefix",
                })
            else:
                a = np.asarray([float(json_numeric(wide[duration].loc[i])) for i in common])
                b = np.asarray([float(json_numeric(wide[20].loc[i])) for i in common])
                rows.append({
                    "subject": subject, "surface_id": surface, "candidate_id": cid,
                    "duration_sec": duration, "reference_duration_sec": 20,
                    "paired_anchor_count": len(common), "spearman_rank_correlation": correlation(a, b),
                    "lin_concordance_correlation": ccc(a, b),
                    "median_signed_difference": float(np.median(a - b)),
                    "median_absolute_difference": float(np.median(np.abs(a - b))),
                    "p95_absolute_component_difference": float(np.quantile(np.abs(a - b), 0.95)),
                    "max_absolute_component_difference": float(np.max(np.abs(a - b))),
                    "comparison_type": "same-start nested duration vs 20 s comparator",
                })
    return pd.DataFrame(rows)


def repeat_stability(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    supported = frame.loc[frame["computed"].astype(bool) & frame["value_json"].astype(str).ne("")]
    for keys, group in supported.groupby(["subject", "surface_id", "duration_sec", "candidate_id"]):
        subject, surface, duration, cid = keys
        group = group.sort_values("anchor_index")
        vals = [np.asarray(json_numeric(value), dtype=float).reshape(-1)
                for value in group["value_json"]]
        matrix = np.vstack(vals)
        diffs = np.abs(np.diff(matrix, axis=0)) if len(matrix) > 1 else np.empty((0, matrix.shape[1]))
        for component in range(matrix.shape[1]):
            series = matrix[:, component]
            rows.append({
                "subject": subject, "surface_id": surface, "duration_sec": duration,
                "candidate_id": cid, "candidate": SHORT[cid],
                "component_index_1based": component + 1 if cid == "M3" else None,
                "anchor_count": len(matrix),
                "across_anchor_median": float(np.median(series)),
                "across_anchor_mad": float(np.median(np.abs(series - np.median(series)))),
                "adjacent_anchor_median_absolute_difference": (
                    float(np.median(diffs[:, component])) if diffs.size else None
                ),
                "adjacent_anchor_p95_absolute_difference": (
                    float(np.quantile(diffs[:, component], 0.95)) if diffs.size else None
                ),
                "reliability_claim": "descriptive repeat-window stability; not test-retest reliability",
            })
    return pd.DataFrame(rows)


def sensitivity(frame: pd.DataFrame, left_surface: str,
                right_surface: str, comparison: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    supported = frame.loc[frame["computed"].astype(bool) & frame["value_json"].astype(str).ne("")]
    left = supported.loc[supported["surface_id"].eq(left_surface)]
    right = supported.loc[supported["surface_id"].eq(right_surface)]
    keys = ["subject", "anchor_index", "duration_sec", "candidate_id"]
    merged = left.merge(right, on=keys, suffixes=("_left", "_right"), how="inner")
    for (subject, duration, cid), group in merged.groupby(["subject", "duration_sec", "candidate_id"]):
        abs_diff: list[float] = []
        signed_diff: list[float] = []
        for a_json, b_json in zip(group["value_json_left"], group["value_json_right"], strict=True):
            a = np.asarray(json_numeric(a_json), dtype=float).reshape(-1)
            b = np.asarray(json_numeric(b_json), dtype=float).reshape(-1)
            n = min(len(a), len(b))
            signed_diff.extend((a[:n] - b[:n]).tolist())
            abs_diff.extend(np.abs(a[:n] - b[:n]).tolist())
        rows.append({
            "subject": subject, "duration_sec": duration, "candidate_id": cid,
            "candidate": SHORT[cid], "comparison": comparison,
            "paired_anchor_count": int(group["anchor_index"].nunique()),
            "paired_component_count": len(abs_diff),
            "median_signed_difference_left_minus_right": float(np.median(signed_diff)),
            "median_absolute_difference": float(np.median(abs_diff)),
            "p95_absolute_difference": float(np.quantile(abs_diff, 0.95)),
            "max_absolute_difference": float(np.max(abs_diff)),
            "claim_ceiling": "descriptive realization sensitivity; no equivalence",
        })
    return pd.DataFrame(rows)


def main() -> None:
    manifest_path = OUT / "run_manifest.json"
    if not manifest_path.is_file() or not AMENDMENT.is_file():
        raise FileNotFoundError("V002 base outputs or continuous-input amendment missing")
    existing = json.loads(manifest_path.read_text(encoding="utf-8"))
    if "continuous_empirical" in existing.get("stages", {}):
        raise FileExistsError("continuous empirical stage already exists; refusing overwrite")
    output_names = (
        "continuous_window_measurements.csv", "continuous_window_signal_qc.csv",
        "continuous_participant_window_summary.csv", "continuous_duration_agreement.csv",
        "continuous_repeat_window_stability.csv", "continuous_reference_sensitivity.csv",
        "continuous_pcv_local_vs_full_context.csv", "continuous_input_manifest.json",
        "continuous_results.md",
    )
    if any((OUT / name).exists() for name in output_names):
        raise FileExistsError("continuous output exists; refusing overwrite")
    progress_measurements = OUT / "continuous_progress_measurements.csv"
    progress_qc = OUT / "continuous_progress_signal_qc.csv"
    progress_manifest = OUT / "continuous_progress_input_manifest.json"
    started = time.perf_counter()
    measurement_rows: list[dict[str, Any]] = []
    qc_rows: list[dict[str, Any]] = []
    input_manifest: dict[str, Any] = {}
    all_subject_anchor_counts: dict[str, int] = {}
    if progress_manifest.is_file():
        saved = json.loads(progress_manifest.read_text(encoding="utf-8"))
        input_manifest = dict(saved.get("participants", {}))
        all_subject_anchor_counts = dict(saved.get("anchor_counts", {}))
        if progress_measurements.is_file():
            measurement_rows = pd.read_csv(progress_measurements, keep_default_na=False).to_dict(orient="records")
        if progress_qc.is_file():
            qc_rows = pd.read_csv(progress_qc, keep_default_na=False).to_dict(orient="records")

    for subject in PARTICIPANTS:
        if subject in input_manifest:
            continue
        labels, data, metadata, paths = read_bids_recording(subject)
        input_manifest[subject] = {
            "source_paths": paths,
            "source_sha256": {key: sha256_file(Path(value)) for key, value in paths.items()},
            "source_metadata": {
                "recording_type": metadata["RecordingType"],
                "sampling_frequency_hz": metadata["SamplingFrequency"],
                "recording_duration_sec": metadata["RecordingDuration"],
                "source_reference": metadata.get("EEGReference"),
                "power_line_frequency_hz": metadata.get("PowerLineFrequency"),
            },
            "resampled_sample_count": int(data.shape[1]),
            "resampled_sample_rate_hz": SFREQ,
        }
        label_idx = {label.casefold(): i for i, label in enumerate(labels)}
        missing = [label for label in CORE19_CHANNELS if label.casefold() not in label_idx]
        if missing:
            raise ValueError(f"{subject}: Core19 channels missing: {missing}")
        native_idx = np.arange(len(labels), dtype=int)
        core_idx = np.asarray([label_idx[label.casefold()] for label in CORE19_CHANNELS], dtype=int)
        mastoid_names = ("TP9", "TP10")
        mastoid_missing = [label for label in mastoid_names if label.casefold() not in label_idx]
        anchors = list(range(
            MARGIN_SAMPLES,
            data.shape[1] - WINDOW_20_SAMPLES - MARGIN_SAMPLES + 1,
            WINDOW_20_SAMPLES,
        ))
        if not anchors:
            raise ValueError(f"{subject}: no complete 20 s windows after 5 s edge margins")
        all_subject_anchor_counts[subject] = len(anchors)
        regions = {
            0: "early",
            len(anchors) // 2: "middle",
            len(anchors) - 1: "late",
        }

        surface_inputs: list[tuple[str, list[str], np.ndarray, str, str | None]] = []
        native = data[native_idx].copy()
        native_avg = native - native.mean(axis=0, keepdims=True)
        surface_inputs.append((
            "native63_average", list(labels), native_avg, "average_over_native63",
            sha256_text("\n".join(sorted(x.casefold() for x in labels))),
        ))
        core = data[core_idx].copy()
        core_labels = list(CORE19_CHANNELS)
        core_avg = core - core.mean(axis=0, keepdims=True)
        surface_inputs.append((
            "core19_average", core_labels, core_avg, "average_over_core19",
            sha256_text("\n".join(sorted(x.casefold() for x in core_labels))),
        ))
        if not mastoid_missing:
            mastoid_idx = np.asarray([label_idx[x.casefold()] for x in mastoid_names], dtype=int)
            linked = native - native[mastoid_idx].mean(axis=0, keepdims=True)
            surface_inputs.append((
                "native63_linked_mastoid", list(labels), linked, "linked_mastoid_TP9_TP10",
                sha256_text("\n".join(sorted(x.casefold() for x in mastoid_names))),
            ))
        input_manifest[subject]["surfaces"] = [item[0] for item in surface_inputs]
        input_manifest[subject]["linked_mastoid_status"] = (
            "supported" if not mastoid_missing else f"unsupported_missing_{mastoid_missing}"
        )

        for surface_id, surface_labels, surface_data, reference_mode, reference_hash in surface_inputs:
            full_context_order = context_pcv(surface_data)
            branch = {
                "branch_id": "v3_multiscale_fidelity_002_raw_resampled_continuous_amendment_v1",
                "reference_mode": reference_mode, "reference_set_sha256": reference_hash,
                "filter_band_hz": None,
            }
            for anchor_index, start in enumerate(anchors):
                region = regions.get(anchor_index, "other")
                for duration in DURATIONS:
                    n = duration * int(SFREQ)
                    stop = start + n
                    window = surface_data[:, start:stop]
                    if window.shape != (len(surface_labels), n):
                        raise ValueError(f"window support mismatch for {subject}/{surface_id}/{anchor_index}/{duration}")
                    qc = {
                        "source_is_continuous": True, "timestamps_uniform": True,
                        "input_samples_finite": bool(np.isfinite(window).all()),
                        "gap_free": True, "bad_interval_free": None,
                        "within_recording_bounds": True, "effective_filter_support_valid": None,
                        "effective_filter_support_status": (
                            "scipy_resample_poly_antialias_context; exact composite edge-safe margin unassessed"
                        ),
                    }
                    result = compute_pipeline_window_measurements(
                        window, surface_labels, sample_rate_hz=SFREQ,
                        window_start_sec=start / SFREQ, window_end_sec=stop / SFREQ,
                        segment_id=f"{subject}_task-rest_anchor{anchor_index:02d}",
                        source_identity=f"ds003838_{subject}_task-rest",
                        input_branch=branch, support_qc=qc,
                        sequence_complexity_reference_count=32, activity_block_sec=2.0,
                    )
                    for row in result["measurements"]:
                        value = row.get("value") if row.get("computed") else None
                        measurement_rows.append({
                            "subject": subject, "surface_id": surface_id,
                            "reference_mode": reference_mode, "reference_set_sha256": reference_hash,
                            "channel_count": len(surface_labels),
                            "anchor_index": anchor_index, "time_region": region,
                            "window_start_sample_250hz": start,
                            "window_start_sec": start / SFREQ, "duration_sec": duration,
                            "candidate_id": row["candidate_id"], "candidate": SHORT[row["candidate_id"]],
                            "value_json": json_value(value) if value is not None else "",
                            "computed": bool(row["computed"]),
                            "valid": bool(row["valid"]), "qualified": bool(row["qualified"]),
                            "status": row.get("status"), "reason": row.get("reason"),
                            "support_audit_status": result.get("support_audit_status"),
                            "bad_interval_free": None,
                            "preprocessing_branch": "BIDS_microV_to_volts_then_scipy_resample_poly_1_over_4_only",
                        })
                    full_order = full_context_order[start:stop]
                    full_context_value = (
                        float(np.std(full_order, ddof=0)) if np.isfinite(full_order).all() else None
                    )
                    pcv_result = next(
                        row for row in result["measurements"] if row["candidate_id"] == "M1"
                    )
                    local_pcv = (
                        float(pcv_result["value"]) if pcv_result.get("computed") else None
                    )
                    # Attach context comparison to the PCV row without changing its estimator output.
                    pcv_row = next(r for r in reversed(measurement_rows)
                                   if r["subject"] == subject and r["surface_id"] == surface_id
                                   and r["anchor_index"] == anchor_index and r["duration_sec"] == duration
                                   and r["candidate_id"] == "M1")
                    pcv_row["full_context_filtered_pcv"] = full_context_value
                    pcv_row["local_minus_full_context_pcv"] = (
                        local_pcv - full_context_value
                        if local_pcv is not None and full_context_value is not None else None
                    )

                    qc_rows.append({
                        "subject": subject, "surface_id": surface_id,
                        "reference_mode": reference_mode, "anchor_index": anchor_index,
                        "time_region": region, "window_start_sec": start / SFREQ,
                        "duration_sec": duration, "channel_count": len(surface_labels),
                        "source_bad_interval_free": "unknown_not_inferred_from_absence",
                        "filter_edge_support": "unquantified; see continuous-input amendment",
                        **signal_qc(window),
                    })
        print(
            f"[continuous] {subject}: {len(anchors)} anchors, surfaces="
            f"{len(surface_inputs)}, elapsed={time.perf_counter()-started:.1f}s",
            flush=True,
        )
        atomic_csv(pd.DataFrame(measurement_rows), progress_measurements)
        atomic_csv(pd.DataFrame(qc_rows), progress_qc)
        atomic_text(json.dumps({
            "participants": input_manifest,
            "anchor_counts": all_subject_anchor_counts,
        }, indent=2, ensure_ascii=False, sort_keys=True) + "\n", progress_manifest)

    frame = pd.DataFrame(measurement_rows)
    qc_frame = pd.DataFrame(qc_rows)
    outputs = {
        "continuous_window_measurements.csv": frame,
        "continuous_window_signal_qc.csv": qc_frame,
        "continuous_participant_window_summary.csv": summarize_participants(frame),
        "continuous_duration_agreement.csv": compare_durations(frame),
        "continuous_repeat_window_stability.csv": repeat_stability(frame),
    }
    sensitivity_frames = [
        sensitivity(frame, "native63_average", "core19_average", "native63_average_vs_core19_average"),
        sensitivity(frame, "native63_average", "native63_linked_mastoid", "native63_average_vs_linked_mastoid"),
    ]
    outputs["continuous_reference_sensitivity.csv"] = pd.concat(
        [x for x in sensitivity_frames if not x.empty], ignore_index=True
    )
    pcv_rows = []
    pcv_frame = frame.loc[
        frame["candidate_id"].eq("M1") & frame["computed"].astype(bool)
        & frame["value_json"].astype(str).ne("")
    ]
    for keys, group in pcv_frame.groupby(["subject", "surface_id", "duration_sec"]):
        diffs = pd.to_numeric(group["local_minus_full_context_pcv"], errors="coerce").dropna().to_numpy()
        pcv_rows.append({
            "subject": keys[0], "surface_id": keys[1], "duration_sec": keys[2],
            "anchor_count": len(diffs), "median_signed_local_minus_context": float(np.median(diffs)),
            "median_absolute_local_minus_context": float(np.median(np.abs(diffs))),
            "p95_absolute_local_minus_context": float(np.quantile(np.abs(diffs), 0.95)),
            "max_absolute_local_minus_context": float(np.max(np.abs(diffs))),
            "comparison": "same sample interval; window-local vs full-recording-context alpha filter/Hilbert",
        })
    outputs["continuous_pcv_local_vs_full_context.csv"] = pd.DataFrame(pcv_rows)

    for filename, data_frame in outputs.items():
        atomic_csv(data_frame, OUT / filename)
    input_manifest_path = OUT / "continuous_input_manifest.json"
    atomic_text(json.dumps({
        "schema": "mndm.v3_multiscale_fidelity_002_continuous_input_manifest.v1",
        "dataset": "OpenNeuro ds003838 v1.0.6",
        "task_file": "task-rest; event/task labels were not read or used",
        "participants": input_manifest,
        "resampling": "scipy.signal.resample_poly(up=1,down=4); default Kaiser antialias filter",
        "upstream_notch_or_bandpass": "none in this amended input branch",
        "durations_sec": list(DURATIONS),
        "anchor_policy": "nonoverlapping 20s starts; 5s recording-edge margin; nested durations",
        "anchor_counts": all_subject_anchor_counts,
        "amendment_path": str(AMENDMENT), "amendment_sha256": sha256_file(AMENDMENT),
        "signal_values_qualified": False, "bad_interval_free": "unknown",
    }, indent=2, ensure_ascii=False, sort_keys=True) + "\n", input_manifest_path)

    report = [
        "# V3-MULTISCALE-FIDELITY-002 continuous empirical results",
        "",
        "Descriptive, label-free analysis of the six frozen participants' continuous BIDS task-rest EEG files.",
        "The preprocessing amendment is explicit: BIDS microvolts to volts, polyphase resampling to 250 Hz, no BENCH-002 notch/bandpass.",
        "No task event labels were read or used. No condition contrast, classifier, qualification, or full-cohort analysis was run.",
        "",
        f"- Participants: {len(PARTICIPANTS)}; anchor counts: {json.dumps(all_subject_anchor_counts, sort_keys=True)}.",
        f"- Measurement rows: {len(frame)}; QC rows: {len(qc_frame)}; surfaces: native63 average, Core19 average, and native63 linked mastoid where available.",
        "- Every emitted measurement remains unqualified. Source bad-interval-free evidence and polyphase edge support remain unknown.",
        "- See continuous_duration_agreement.csv, continuous_repeat_window_stability.csv, continuous_reference_sensitivity.csv, and continuous_pcv_local_vs_full_context.csv for descriptive per-participant results.",
        "- Because this input branch is not preprocessing-matched to the prior MNE-filtered 648-window pilot, these values do not establish direct comparability to that pilot.",
    ]
    atomic_text("\n".join(report) + "\n", OUT / "continuous_results.md")
    for path in (progress_measurements, progress_qc, progress_manifest):
        path.unlink(missing_ok=True)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.setdefault("stages", {})["continuous_empirical"] = {
        "status": "complete_with_preprocessing_amendment",
        "completed_utc": datetime.now(timezone.utc).isoformat(),
    }
    manifest["continuous_empirical_stage"] = "complete_raw_resampled_amended_branch"
    manifest["continuous_runner_path"] = str(Path(__file__).resolve())
    manifest["continuous_runner_sha256"] = sha256_file(Path(__file__).resolve())
    manifest["continuous_amendment_path"] = str(AMENDMENT)
    manifest["continuous_amendment_sha256"] = sha256_file(AMENDMENT)
    manifest["status"] = "complete_with_continuous_preprocessing_amendment"
    manifest["claim_ceiling"] = (
        "bounded estimator-fidelity and descriptive empirical screening only; "
        "no qualification, equivalence, task contrast, classifier, or full-cohort authorization"
    )
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.name != "run_manifest.json" and not path.name.endswith(".tmp"):
            manifest.setdefault("outputs", {})[path.name] = {
                "bytes": path.stat().st_size, "sha256": sha256_file(path),
            }
    manifest["continuous_input_manifest_path"] = str(input_manifest_path)
    manifest["continuous_input_manifest_sha256"] = sha256_file(input_manifest_path)
    atomic_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", manifest_path)
    print(
        f"[continuous] complete; measurements={len(frame)}; QC={len(qc_frame)}; "
        f"elapsed={time.perf_counter()-started:.1f}s; output={OUT}",
        flush=True,
    )


if __name__ == "__main__":
    main()
