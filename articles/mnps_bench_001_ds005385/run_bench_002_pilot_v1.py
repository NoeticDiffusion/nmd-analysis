from __future__ import annotations
import copy
import csv
import hashlib
import json
import math
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import h5py
import mne
import numpy as np
import pandas as pd
import yaml

NMD_ROOT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics")
sys.path.insert(0, str(NMD_ROOT / "core" / "src"))
sys.path.insert(0, str(NMD_ROOT / "mndm" / "src"))
from mndm.features.eeg import compute_eeg_features
from mndm.features.ecg import compute_ecg_features
from mndm.features.ppg import compute_ppg_features
from mndm.mnps.v3_1.pipeline_measurements import compute_acquisition_qc, compute_pipeline_window_measurements
from mndm.mnps.v3_1.realizations import CORE19_CHANNELS
from mndm.projection import project_features_v2
from mndm.schema import mnps_9d_CANONICAL_ORDER

DATA_ROOT = Path(r"K:\ExternalReceivedDatasets\openneuro\received\ds003838")
ARTICLE_ROOT = Path(r"J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385")
OUT = ARTICLE_ROOT / "outputs" / "bench_002_pilot_v2_fast_gate_fix_20261009"
PARTICIPANTS = ("sub-032", "sub-033", "sub-034", "sub-035", "sub-036", "sub-038")
SOURCE_SFREQ = 1000.0
TARGET_SFREQ = 250.0
S8 = 8 * 250
STEP4 = 4 * 250
S4 = 4 * 250
S20 = 20 * 250
RAW_INPUTS = ("eeg_delta", "eeg_theta", "eeg_alpha", "eeg_beta_alpha", "eeg_gamma",
              "eeg_hjorth_mobility", "eeg_alpha_theta", "eeg_permutation_entropy",
              "eeg_hjorth_complexity", "embodied_arousal_proxy")
CONVENTIONAL = tuple(f"eeg_conventional_relative_{b}" for b in ("delta", "theta", "alpha", "beta", "gamma"))
V3_SCALARS = {"M1": "PCV", "M2": "TP", "D1": "NIE", "D3": "RD", "E1": "OI", "E2": "SC", "E3": "ED"}
V3_FEATURES = ("PCV", "TP", *(f"AR_pair_{i:02d}" for i in range(1, 10)), "NIE", "RD", "OI", "SC", "ED")
FAST_CORE_COMPONENTS = ("PCV", "TP", "OI", "SC")
FAST_CORE_ARM = "v3_1_fast_core_4s"
FAST_CORE_20S_SUBSET_ARM = "v3_1_fast_core_subset_20s"

def log(message: str) -> None:
    print(f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {message}", flush=True)

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def label_hash(labels: list[str] | tuple[str, ...], ordered: bool = True) -> str:
    keys = [str(x).strip().casefold() for x in labels]
    if not ordered:
        keys.sort()
    return hashlib.sha256("\n".join(keys).encode("utf-8")).hexdigest()

def clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean_json(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, Path):
        return str(value)
    return value

def load_labels(path: Path) -> tuple[list[str], pd.DataFrame]:
    frame = pd.read_csv(path, sep="\t")
    labels = frame["name"].astype(str).str.strip().tolist()
    if not labels or len(set(x.casefold() for x in labels)) != len(labels):
        raise ValueError(f"duplicate/empty channel labels in {path}")
    return labels, frame

def read_set(path: Path, labels: list[str], scale: float) -> np.ndarray:
    with h5py.File(path, "r") as handle:
        data = handle["data"]
        if data.ndim != 2 or int(data.shape[1]) != len(labels):
            raise ValueError(f"EEGLAB data shape {data.shape} mismatches BIDS labels {len(labels)}")
        ns, nc = map(int, data.shape)
        output = np.empty((nc, ns), dtype=np.float64, order="C")
        for left in range(0, ns, 32768):
            right = min(ns, left + 32768)
            block = np.asarray(data[left:right, :], dtype=np.float64)
            output[:, left:right] = block.T * scale
    if not np.isfinite(output).all():
        raise ValueError(f"non-finite input samples: {path}")
    return output

def parse_trials(path: Path, subject: str, sample_count: int) -> tuple[list[dict[str, Any]], int]:
    frame = pd.read_csv(path, sep="\t", dtype={"sample": "Int64", "trial_type": str})
    pattern = re.compile(r"\b(?P<cond>control|memory)\s+(?P<pos>\d+)\s*/\s*(?P<load>\d+)\b", re.I)
    trials: list[dict[str, Any]] = []
    malformed = 0
    current: dict[str, Any] | None = None
    def close() -> None:
        nonlocal current, malformed
        if current is None:
            return
        positions = [int(r["position"]) for r in current["digits"]]
        load = int(current["load"])
        if positions != list(range(1, load + 1)):
            malformed += 1
            current = None
            return
        first = int(current["digits"][0]["sample"])
        last = int(current["digits"][-1]["sample"])
        end = last + 3000
        if first < 0 or end > sample_count:
            malformed += 1
            current = None
            return
        trials.append({
            "subject": subject, "trial_id": f"{subject}_T{len(trials)+1:03d}",
            "condition": str(current["condition"]), "load": load,
            "source_start_sample": first, "source_last_digit_sample": last,
            "source_end_sample_exclusive": end, "source_start_sec": first / 1000.0,
            "source_end_sec": end / 1000.0, "source_duration_sec": (end-first)/1000.0,
            "digit_event_count": len(positions),
            "trigger_values": [str(r.get("value", "")) for r in current["digits"]],
        })
        current = None
    for row in frame.to_dict(orient="records"):
        match = pattern.search(str(row.get("trial_type", "")))
        if not match:
            continue
        if pd.isna(row.get("sample")):
            malformed += 1
            continue
        cond = match.group("cond").casefold()
        pos = int(match.group("pos"))
        load = int(match.group("load"))
        digit = {"condition": cond, "position": pos, "load": load,
                 "sample": int(row["sample"]), "value": row.get("value", "")}
        if pos == 1:
            close()
            current = {"condition": cond, "load": load, "digits": [digit]}
        elif current is not None and (cond, load) == (current["condition"], current["load"]):
            current["digits"].append(digit)
        else:
            malformed += 1
    close()
    counts = Counter(f"{x['condition']}_{x['load']}" for x in trials)
    expected = {f"control_{n}": 18 for n in (5, 9, 13)}
    expected.update({f"memory_{n}": 36 for n in (5, 9, 13)})
    if dict(counts) != expected:
        raise ValueError(f"{subject}: trial counts {dict(counts)} do not match {expected}")
    if len(trials) != 162 or malformed:
        raise ValueError(f"{subject}: complete trials={len(trials)}, malformed={malformed}")
    return trials, malformed

def load_config() -> dict[str, Any]:
    path = NMD_ROOT / "mndm" / "config" / "config_ingest_common_eeg.yaml"
    config = copy.deepcopy(yaml.safe_load(path.read_text(encoding="utf-8")))
    config.setdefault("epoching", {})["length_s"] = 8.0
    config["epoching"]["step_s"] = 4.0
    config["epoching"]["sampling"] = {}
    conventional = config.setdefault("conventional_eeg", {})
    conventional["enabled"] = True
    conventional["packs"] = ["tier1"]
    conventional.setdefault("export", {})["per_epoch_columns"] = True
    conventional["export"]["summaries"] = False
    conventional.setdefault("tier1", {})["relative_bandpower"] = True
    config["mnps_v3_1_measurements"] = {"enabled": False}
    return config

def preprocess_eeg(source_volts: np.ndarray, labels: list[str]) -> tuple[np.ndarray, dict[str, Any]]:
    info = mne.create_info(ch_names=labels, sfreq=SOURCE_SFREQ, ch_types=["eeg"] * len(labels), verbose="ERROR")
    raw = mne.io.RawArray(source_volts, info, copy="auto", verbose="ERROR")
    raw.resample(TARGET_SFREQ, n_jobs=1, verbose="ERROR")
    raw.notch_filter(freqs=[50.0], picks="eeg", n_jobs=1, verbose="ERROR")
    raw.filter(l_freq=1.0, h_freq=45.0, picks="eeg", n_jobs=1, verbose="ERROR")
    data = np.asarray(raw.get_data(), dtype=np.float64)
    if not np.isfinite(data).all():
        raise ValueError("preprocessed EEG contains non-finite values")
    provenance = {
        "source_sfreq_hz": SOURCE_SFREQ, "output_sfreq_hz": TARGET_SFREQ,
        "resample": "MNE Raw.resample defaults", "notch_hz": [50.0],
        "bandpass_hz": [1.0, 45.0], "filter_phase": "MNE default FIR zero-phase",
        "source_unit": "microV", "working_unit": "V", "native_reference": "FCz",
        "offline_reference": "average separately over each emitted surface",
        "source_samples": int(source_volts.shape[1]), "target_samples": int(data.shape[1]),
    }
    del raw
    return data, provenance

def features_for_surface(data: np.ndarray, labels: list[str], config: dict[str, Any]) -> pd.DataFrame:
    referenced = np.asarray(data, dtype=np.float64).copy()
    referenced -= referenced.mean(axis=0, keepdims=True)
    meta = {
        "eeg_amplitude_unit": "volts",
        "eeg_amplitude_unit_status": "verified_from_BIDS_microV_to_volts_conversion",
        "eeg_reference_mode": "average_over_surface",
        "eeg_reference_status": "verified",
        "reference_set_hash": label_hash(labels, ordered=False),
        "channel_set_hash": label_hash(labels, ordered=False),
        "eeg_channel_count": len(labels),
    }
    frame = compute_eeg_features({
        "signals": {"eeg": referenced}, "sfreq": TARGET_SFREQ,
        "dataset_id": "ds003838", "channels": {"eeg": labels}, "meta": meta,
    }, config)
    if frame.empty:
        raise ValueError("empty EEG feature frame")
    return frame

def add_proxy(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    proxy = np.full(len(output), np.nan, dtype=np.float64)
    source = np.full(len(output), "", dtype=object)
    for col in ("ecg_rmssd", "ecg_hr_bpm", "ppg_rate_bpm", "ppg_amplitude_mean",
                "pupil_dilation_velocity", "pupil_diameter_std", "eog_blink_rate",
                "meg_highfreq_power_30_45", "eeg_highfreq_power_30_45"):
        if col not in output.columns:
            continue
        values = pd.to_numeric(output[col], errors="coerce").to_numpy(dtype=np.float64)
        use = np.isfinite(values) & ~np.isfinite(proxy)
        proxy[use], source[use] = values[use], col
    output["embodied_arousal_proxy"] = proxy.astype(np.float32)
    output["embodied_arousal_proxy_source"] = source
    return output

def project_v2(frame: pd.DataFrame, config: dict[str, Any]) -> tuple[np.ndarray, list[str], dict[str, Any]]:
    v2 = config["mnps_9d"]["versions"]["2.0"]["subcoords"]
    subcoords = {name: v2[name] for name in mnps_9d_CANONICAL_ORDER if name in v2}
    if tuple(subcoords) != tuple(mnps_9d_CANONICAL_ORDER):
        raise ValueError("v2.0 coordinate definition/order is incomplete")
    projection = config["mnps_projection"]
    values, names, baselines = project_features_v2(
        frame, subcoords, normalize=projection["normalize"],
        feature_standardization=projection["feature_standardization"],
        clip_threshold=float(projection["clip_threshold"]),
    )
    return values, names, baselines

def attach_event_windows(frame: pd.DataFrame, coords: np.ndarray, names: list[str],
                         trials: list[dict[str, Any]], subject: str, surface: str,
                         labels: list[str]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows = frame.copy()
    if coords.shape != (len(rows), len(names)):
        raise ValueError("v2 coordinate shape mismatch")
    for j, name in enumerate(names):
        rows[f"hist_v2_{name}"] = coords[:, j]
    starts = np.rint(pd.to_numeric(rows["t_start"]).to_numpy(dtype=float) * TARGET_SFREQ).astype(np.int64)
    ends = starts + S8
    rows["grid_start_sample_250hz"] = starts
    rows["grid_end_sample_250hz_exclusive"] = ends
    output: list[dict[str, Any]] = []
    counts = {str(t["trial_id"]): 0 for t in trials}
    for trial in trials:
        t0 = (int(trial["source_start_sample"]) + 3) // 4
        t1 = int(trial["source_end_sample_exclusive"]) // 4
        for i in np.flatnonzero((starts >= t0) & (ends <= t1)):
            record = rows.iloc[int(i)].to_dict()
            record.update({
                "subject": subject, "surface": surface, "trial_id": trial["trial_id"],
                "condition": trial["condition"], "load": int(trial["load"]),
                "source_trial_start_sample": trial["source_start_sample"],
                "source_trial_end_sample_exclusive": trial["source_end_sample_exclusive"],
                "trial_grid_start_sample_250hz": t0, "trial_grid_end_sample_250hz_exclusive": t1,
                "surface_channel_labels": json.dumps(labels, separators=(",", ":")),
                "surface_channel_count": len(labels),
                "surface_channel_order_sha256": label_hash(labels),
                "surface_channel_set_sha256": label_hash(labels, ordered=False),
                "event_window_contained_in_one_trial": True,
            })
            output.append(record)
            counts[str(trial["trial_id"])] += 1
    return output, counts

def v3_values(result: dict[str, Any]) -> dict[str, Any]:
    values = {}
    for row in result.get("measurements", []):
        cid = str(row.get("candidate_id", ""))
        value = row.get("value") if row.get("computed") else None
        if cid == "M3" and isinstance(value, list) and len(value) == 9:
            values.update({f"AR_pair_{i:02d}": v for i, v in enumerate(value, 1)})
        elif cid in V3_SCALARS:
            values[V3_SCALARS[cid]] = value
    return values

def trial_window_starts(trial: dict[str, Any], total_samples: int,
                        window_samples: int, step_samples: int) -> range:
    """Return complete nonoverlap windows contained inside one trial."""
    if window_samples <= 0 or step_samples <= 0:
        raise ValueError("window and step sample counts must be positive")
    left_bound = (int(trial["source_start_sample"]) + 3) // 4
    right_bound = int(trial["source_end_sample_exclusive"]) // 4
    first = max(0, left_bound)
    stop = min(right_bound - window_samples + 1, int(total_samples) - window_samples + 1)
    if stop <= first:
        return range(0)
    return range(first, stop, step_samples)

def compute_fast_core_window(surface_data: np.ndarray, surface_labels: list[str],
                             trial: dict[str, Any], subject: str, surface: str,
                             window_index: int, start_sample: int,
                             source_identity: str, input_branch: dict[str, Any],
                             sample_origin: int = 0,
                             ) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compute one trial-local fast-core window independently of the 20 s path."""
    local_start = int(start_sample)
    global_start = local_start + int(sample_origin)
    right = local_start + S4
    global_right = global_start + S4
    window = surface_data[:, local_start:right]
    if window.shape != (len(surface_labels), S4):
        raise ValueError("fast-core window support/sample shape mismatch")
    support_qc = {
        "source_is_continuous": True, "timestamps_uniform": True,
        "input_samples_finite": bool(np.isfinite(window).all()), "gap_free": True,
        "bad_interval_free": None,
        "within_recording_bounds": bool(0 <= start_sample < right <= surface_data.shape[1]),
        "effective_filter_support_valid": None,
        "effective_filter_support_status": "whole_recording_MNE_resample_notch_bandpass_context; exact composite edge-safe margin not separately audited",
    }
    result = compute_pipeline_window_measurements(
        window, surface_labels, sample_rate_hz=TARGET_SFREQ,
        window_start_sec=global_start / TARGET_SFREQ,
        window_end_sec=global_right / TARGET_SFREQ,
        segment_id=f"{subject}_task-memory_{trial['trial_id']}",
        source_identity=source_identity, input_branch=input_branch,
        support_qc=support_qc, sequence_complexity_reference_count=32,
        activity_block_sec=2.0,
    )
    values = v3_values(result)
    return ({
        "subject": subject, "surface": surface, "trial_id": trial["trial_id"],
        "condition": trial["condition"], "load": int(trial["load"]),
        "window_index": int(window_index),
        "window_start_sample_250hz": global_start,
        "window_end_sample_250hz_exclusive": global_right,
        "window_start_sec": global_start / TARGET_SFREQ,
        "window_end_sec": global_right / TARGET_SFREQ,
        "sample_count": int(window.shape[1]), "channel_count": len(surface_labels),
        "channel_order_sha256": label_hash(surface_labels),
        "channel_set_sha256": label_hash(surface_labels, ordered=False),
        **{name: values.get(name) for name in FAST_CORE_COMPONENTS},
    }, result)

def summarize(event_rows: list[dict[str, Any]], v3_rows: list[dict[str, Any]],
              fast_core_rows: list[dict[str, Any]],
              trials: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    arms = {
        "conventional_spectral": CONVENTIONAL,
        "raw_mnps_v2_inputs": RAW_INPUTS,
        "historical_mnps_v2": tuple(f"hist_v2_{n}" for n in mnps_9d_CANONICAL_ORDER),
    }
    long = []
    for row in event_rows:
        for arm, cols in arms.items():
            for col in cols:
                try:
                    value = float(row.get(col))
                except (TypeError, ValueError, OverflowError):
                    continue
                if math.isfinite(value):
                    long.append({
                        "subject": row["subject"], "surface": row["surface"], "load": int(row["load"]),
                        "condition": row["condition"], "trial_id": row["trial_id"], "arm": arm,
                        "feature": col.removeprefix("hist_v2_"), "value": value,
                        "window_id": int(row["epoch_id"]),
                    })
    for row in v3_rows:
        for arm, cols in (("full_mnps_v3_1", V3_FEATURES), (FAST_CORE_20S_SUBSET_ARM, FAST_CORE_COMPONENTS)):
            for col in cols:
                try:
                    value = float(row.get(col))
                except (TypeError, ValueError, OverflowError):
                    continue
                if math.isfinite(value):
                    long.append({
                        "subject": row["subject"], "surface": row["surface"], "load": int(row["load"]),
                        "condition": row["condition"], "trial_id": row["trial_id"], "arm": arm,
                        "feature": col, "value": value, "window_id": int(row["window_index"]),
                    })
    for row in fast_core_rows:
        for col in FAST_CORE_COMPONENTS:
            try:
                value = float(row.get(col))
            except (TypeError, ValueError, OverflowError):
                continue
            if math.isfinite(value):
                long.append({
                    "subject": row["subject"], "surface": row["surface"], "load": int(row["load"]),
                    "condition": row["condition"], "trial_id": row["trial_id"], "arm": FAST_CORE_ARM,
                    "feature": col, "value": value, "window_id": int(row["window_index"]),
                })
    long_df = pd.DataFrame(long)
    if long_df.empty:
        raise ValueError("no finite benchmark arm values")
    trial_medians = (
        long_df.groupby(["subject", "surface", "load", "condition", "trial_id", "arm", "feature"], as_index=False)
        .agg(trial_median=("value", "median"), finite_window_count=("value", "count"))
    )
    feature_sets = {
        "conventional_spectral": CONVENTIONAL,
        "raw_mnps_v2_inputs": RAW_INPUTS,
        "historical_mnps_v2": mnps_9d_CANONICAL_ORDER,
        "full_mnps_v3_1": V3_FEATURES,
        FAST_CORE_20S_SUBSET_ARM: FAST_CORE_COMPONENTS,
        FAST_CORE_ARM: FAST_CORE_COMPONENTS,
    }
    summaries = []
    for subject in PARTICIPANTS:
        for surface in ("native", "core19"):
            for load in (5, 9, 13):
                for condition in ("control", "memory"):
                    cell_trials = [t for t in trials if t["subject"] == subject and int(t["load"]) == load and t["condition"] == condition]
                    for arm, features in feature_sets.items():
                        for feature in features:
                            subset = trial_medians[
                                (trial_medians.subject == subject) & (trial_medians.surface == surface)
                                & (trial_medians.load == load) & (trial_medians.condition == condition)
                                & (trial_medians.arm == arm) & (trial_medians.feature == feature)
                            ]
                            summaries.append({
                                "subject": subject, "surface": surface, "load": load, "condition": condition,
                                "arm": arm, "feature": feature,
                                "cell_median_of_trial_medians": float(subset.trial_median.median()) if len(subset) else np.nan,
                                "supported_trial_count": int(subset.trial_id.nunique()) if len(subset) else 0,
                                "total_trial_count": len(cell_trials),
                                "finite_window_count": int(subset.finite_window_count.sum()) if len(subset) else 0,
                            })
    cell = pd.DataFrame(summaries)
    keys = ["subject", "surface", "load", "arm", "feature"]
    wide = cell.pivot(index=keys, columns="condition", values="cell_median_of_trial_medians")
    paired = []
    for key, row in wide.iterrows():
        if pd.notna(row.get("control")) and pd.notna(row.get("memory")):
            paired.append({**dict(zip(keys, key)), "control": float(row["control"]),
                           "memory": float(row["memory"]),
                           "memory_minus_control": float(row["memory"] - row["control"])})
    paired_df = pd.DataFrame(paired)
    if paired_df.empty:
        contrast = pd.DataFrame()
    else:
        contrast = (
            paired_df.groupby(["surface", "load", "arm", "feature"], as_index=False)
            .agg(participant_count=("subject", "nunique"),
                 mean_memory_minus_control=("memory_minus_control", "mean"),
                 median_memory_minus_control=("memory_minus_control", "median"),
                 min_participant_difference=("memory_minus_control", "min"),
                 max_participant_difference=("memory_minus_control", "max"))
        )
    return trial_medians, cell, paired_df, contrast

def main() -> None:
    started = time.perf_counter()
    if OUT.exists():
        raise FileExistsError(f"refusing to overwrite an existing BENCH-002 output: {OUT}")
    OUT.mkdir(parents=True, exist_ok=False)
    mne.set_log_level("ERROR")
    config_path = NMD_ROOT / "mndm" / "config" / "config_ingest_common_eeg.yaml"
    config = load_config()
    config_sha = sha256_file(config_path)
    dataset_meta = json.loads((DATA_ROOT / "dataset_description.json").read_text(encoding="utf-8"))
    if dataset_meta.get("DatasetDOI", "").removeprefix("doi:") != "10.18112/openneuro.ds003838.v1.0.6":
        raise ValueError("dataset_description does not match frozen DOI version")
    changes_top = (DATA_ROOT / "CHANGES").read_text(encoding="utf-8").splitlines()[0].strip()
    if not changes_top.startswith("1.0.6 "):
        raise ValueError(f"unexpected top CHANGES entry: {changes_top}")
    participants = pd.read_csv(DATA_ROOT / "participants.tsv", sep="\t", dtype=str).set_index("participant_id")
    implementation_files = [
        NMD_ROOT / "mndm/src/mndm/features/eeg.py", NMD_ROOT / "mndm/src/mndm/features/ecg.py",
        NMD_ROOT / "mndm/src/mndm/features/ppg.py", NMD_ROOT / "mndm/src/mndm/projection.py",
        NMD_ROOT / "mndm/src/mndm/preprocess.py",
        NMD_ROOT / "mndm/src/mndm/mnps/v3_1/pipeline_measurements.py",
        NMD_ROOT / "mndm/src/mndm/mnps/v3_1/realizations.py", Path(__file__),
    ]
    implementation_hashes = {str(p): sha256_file(p) for p in implementation_files}
    all_trials, event_rows, v3_rows, fast_core_rows = [], [], [], []
    support_rows, processing_rows = [], []
    support_idx: dict[tuple[str, str, str], int] = {}
    baselines, input_hashes = {}, {}
    proxy_sources: Counter[str] = Counter()
    v3_jsonl = OUT / "v3_measurements.jsonl"
    fast_core_jsonl = OUT / "fast_core_4s_measurements.jsonl"
    expected_labels = None

    for subject in PARTICIPANTS:
        if subject not in participants.index or str(participants.loc[subject, "EEG_excluded"]).casefold() != "no":
            raise ValueError(f"{subject} is not EEG eligible in local participants.tsv")
        eegdir, ecgdir = DATA_ROOT / subject / "eeg", DATA_ROOT / subject / "ecg"
        eeg_set = eegdir / f"{subject}_task-memory_eeg.set"
        eeg_ch = eegdir / f"{subject}_task-memory_channels.tsv"
        events = eegdir / f"{subject}_task-memory_events.tsv"
        ecg_set = ecgdir / f"{subject}_task-memory_ecg.set"
        ecg_ch = ecgdir / f"{subject}_task-memory_channels.tsv"
        if not all(p.is_file() for p in (eeg_set, eeg_ch, events, ecg_set, ecg_ch)):
            raise FileNotFoundError(f"missing task-matched EEG/event/ECG files for {subject}")
        log(f"{subject}: hashing five source files")
        for path in (eeg_set, eeg_ch, events, ecg_set, ecg_ch):
            input_hashes[str(path)] = sha256_file(path)
        labels, chframe = load_labels(eeg_ch)
        if len(labels) != 63 or not (chframe["type"].astype(str).str.upper() == "EEG").all():
            raise ValueError(f"expected 63 EEG channels in {subject}, got {len(labels)}")
        if expected_labels is None:
            expected_labels = labels
        elif labels != expected_labels:
            raise ValueError(f"ordered EEG channels differ from the selected cohort in {subject}")
        eeg_uv = read_set(eeg_set, labels, scale=1e-6)
        trials, malformed = parse_trials(events, subject, eeg_uv.shape[1])
        all_trials.extend(trials)
        log(f"{subject}: parsed {len(trials)} complete trials; preprocessing continuous EEG")
        filtered, prep = preprocess_eeg(eeg_uv, labels)
        if filtered.shape[1] != int(eeg_uv.shape[1] // 4):
            raise ValueError(f"resampled sample grid mismatch in {subject}")
        del eeg_uv

        ecg_labels, _ = load_labels(ecg_ch)
        ecg_data = read_set(ecg_set, ecg_labels, scale=1.0)
        if ecg_data.shape[1] != int(prep["source_samples"]):
            raise ValueError(f"EEG/ECG timebase mismatch in {subject}")
        ecg_i = next((i for i, x in enumerate(ecg_labels) if x.casefold() == "ecg"), None)
        ppg_i = next((i for i, x in enumerate(ecg_labels) if x.casefold() == "ppg"), None)
        if ecg_i is None:
            raise ValueError(f"ECG channel missing for {subject}")
        try:
            ecg_features = compute_ecg_features(
                {"signals": {"ecg": ecg_data[ecg_i]}, "sfreq": SOURCE_SFREQ, "dataset_id": "ds003838"}, config
            )
        except Exception as exc:
            log(f"{subject}: ECG extraction failed ({type(exc).__name__}); continuing with lower-priority proxy")
            ecg_features = pd.DataFrame()
        if ppg_i is not None:
            try:
                ppg_features = compute_ppg_features(
                    {"signals": {"ppg": ecg_data[ppg_i]}, "sfreq": SOURCE_SFREQ, "dataset_id": "ds003838"}, config
                )
            except Exception as exc:
                log(f"{subject}: PPG extraction failed ({type(exc).__name__}); continuing with EEG proxy")
                ppg_features = pd.DataFrame()
        else:
            ppg_features = pd.DataFrame()
        del ecg_data
        log(f"{subject}: ECG feature rows={len(ecg_features)}; PPG feature rows={len(ppg_features)}")

        indices = {name.casefold(): i for i, name in enumerate(labels)}
        surfaces: list[tuple[str, list[str], np.ndarray]] = [("native", labels, np.arange(len(labels), dtype=int))]
        missing_core = [name for name in CORE19_CHANNELS if name.casefold() not in indices]
        if missing_core:
            log(f"{subject}: Core19 unavailable; missing {missing_core}")
        else:
            surfaces.append(("core19", list(CORE19_CHANNELS),
                             np.asarray([indices[name.casefold()] for name in CORE19_CHANNELS], dtype=int)))
        for surface, surface_labels, channel_indices in surfaces:
            log(f"{subject}/{surface}: computing continuous 8s/4s features and normalization")
            surface_data = np.asarray(filtered[channel_indices], dtype=np.float64).copy()
            surface_data -= surface_data.mean(axis=0, keepdims=True)
            meta = {
                "eeg_amplitude_unit": "volts", "eeg_amplitude_unit_status": "verified_from_BIDS_microV_to_volts_conversion",
                "eeg_reference_mode": "average_over_surface", "eeg_reference_status": "verified",
                "reference_set_hash": label_hash(surface_labels, ordered=False),
                "channel_set_hash": label_hash(surface_labels, ordered=False),
                "eeg_channel_count": len(surface_labels),
            }
            frame = compute_eeg_features({
                "signals": {"eeg": surface_data}, "sfreq": TARGET_SFREQ,
                "dataset_id": "ds003838", "channels": {"eeg": surface_labels}, "meta": meta,
            }, config)
            if frame.empty:
                raise ValueError(f"empty feature frame {subject}/{surface}")
            if not ecg_features.empty:
                frame = frame.merge(ecg_features, on="epoch_id", how="left", suffixes=("", "_ecg"))
            if not ppg_features.empty:
                frame = frame.merge(ppg_features, on="epoch_id", how="left", suffixes=("", "_ppg"))
            frame = add_proxy(frame)
            proxy_sources.update(frame["embodied_arousal_proxy_source"].fillna("unavailable").astype(str).replace("", "unavailable").value_counts().to_dict())
            coords, coord_names, feature_baselines = project_v2(frame, config)
            baselines[f"{subject}/{surface}"] = {
                "normalization_scope": "all continuous task-memory 8s/4s windows before trial selection",
                "window_count": len(frame), "subcoordinate_order": coord_names,
                "feature_standardization": config["mnps_projection"]["feature_standardization"],
                "normalize_mode": config["mnps_projection"]["normalize"],
                "clip_threshold": config["mnps_projection"]["clip_threshold"],
                "feature_baselines": feature_baselines,
                "channel_labels": surface_labels, "channel_order_sha256": label_hash(surface_labels),
                "channel_set_sha256": label_hash(surface_labels, ordered=False),
            }
            selected, support_counts = attach_event_windows(frame, coords, coord_names, trials, subject, surface, surface_labels)
            event_rows.extend(selected)
            log(f"{subject}/{surface}: full-file windows={len(frame)}; trial-contained 8s windows={len(selected)}")

            for trial in trials:
                row = {
                    **trial, "surface": surface, "surface_channel_count": len(surface_labels),
                    "surface_channel_order_sha256": label_hash(surface_labels),
                    "surface_channel_set_sha256": label_hash(surface_labels, ordered=False),
                    "eight_second_four_second_window_count": int(support_counts[str(trial["trial_id"])]),
                    "fast_core_four_second_window_count": 0,
                    "twenty_second_window_count": 0,
                }
                support_idx[(subject, surface, str(trial["trial_id"]))] = len(support_rows)
                support_rows.append(row)

            branch = {
                "branch_id": "mnps_bench_002_mne_common_preprocessing_v1",
                "reference_mode": "average_over_surface",
                "reference_set_sha256": label_hash(surface_labels, ordered=False),
                "filter_band_hz": [1.0, 45.0], "amplitude_unit": "volts", "reference_status": "verified",
            }
            # Compute the four-second fast core on its own support grid. This
            # loop includes trials that cannot supply a full-v3 20-second row.
            start_fast_core = time.perf_counter()
            for trial in trials:
                starts = trial_window_starts(trial, surface_data.shape[1], S4, S4)
                for widx, left in enumerate(starts):
                    record, result = compute_fast_core_window(
                        surface_data, surface_labels, trial, subject, surface, widx, left,
                        input_hashes[str(eeg_set)], branch,
                    )
                    fast_core_rows.append(record)
                    with fast_core_jsonl.open("a", encoding="utf-8") as stream:
                        stream.write(json.dumps(clean_json({
                            "subject": subject, "surface": surface, "trial": trial,
                            "window_index": widx,
                            "window_start_sample_250hz": left,
                            "window_end_sample_250hz_exclusive": left + S4,
                            "result": result,
                        }), ensure_ascii=False, allow_nan=False) + "\n")
                    support_rows[support_idx[(subject, surface, str(trial["trial_id"]))]][
                        "fast_core_four_second_window_count"
                    ] += 1
            fast_core_elapsed = time.perf_counter() - start_fast_core
            start_v3 = time.perf_counter()
            count_v3 = 0
            for trial in trials:
                t0 = (int(trial["source_start_sample"]) + 3) // 4
                t1 = int(trial["source_end_sample_exclusive"]) // 4
                window_starts = range(t0, t1 - S20 + 1, S20)
                for widx, left in enumerate(window_starts):
                    right = left + S20
                    window = surface_data[:, left:right]
                    if window.shape != (len(surface_labels), S20):
                        raise ValueError("v3 window support/sample shape mismatch")
                    support_qc = {
                        "source_is_continuous": True, "timestamps_uniform": True,
                        "input_samples_finite": bool(np.isfinite(window).all()), "gap_free": True,
                        "bad_interval_free": None,
                        "within_recording_bounds": bool(0 <= left < right <= surface_data.shape[1]),
                        "effective_filter_support_valid": True,
                        "effective_filter_support_status": "whole_recording_MNE_resample_notch_bandpass_context",
                    }
                    times: dict[str, float] = {}
                    result = compute_pipeline_window_measurements(
                        window, surface_labels, sample_rate_hz=TARGET_SFREQ,
                        window_start_sec=left / TARGET_SFREQ, window_end_sec=right / TARGET_SFREQ,
                        segment_id=f"{subject}_task-memory_{trial['trial_id']}",
                        source_identity=input_hashes[str(eeg_set)], input_branch=branch,
                        support_qc=support_qc, sequence_complexity_reference_count=32,
                        activity_block_sec=2.0,
                        metric_timing_callback=lambda name, seconds: times.__setitem__(name, seconds),
                    )
                    values = v3_values(result)
                    record = {
                        "subject": subject, "surface": surface, "trial_id": trial["trial_id"],
                        "condition": trial["condition"], "load": int(trial["load"]),
                        "window_index": int(widx), "window_start_sample_250hz": int(left),
                        "window_end_sample_250hz_exclusive": int(right),
                        "window_start_sec": left / TARGET_SFREQ, "window_end_sec": right / TARGET_SFREQ,
                        "sample_count": int(window.shape[1]), "channel_count": len(surface_labels),
                        "channel_order_sha256": label_hash(surface_labels),
                        "channel_set_sha256": label_hash(surface_labels, ordered=False), **values,
                    }
                    v3_rows.append(record)
                    full = {
                        "subject": subject, "surface": surface, "trial": trial, "window_index": int(widx),
                        "window_start_sample_250hz": int(left), "window_end_sample_250hz_exclusive": int(right),
                        "metric_seconds": times, "result": result,
                    }
                    with v3_jsonl.open("a", encoding="utf-8") as stream:
                        stream.write(json.dumps(clean_json(full), ensure_ascii=False, allow_nan=False) + "\n")
                    support_rows[support_idx[(subject, surface, str(trial["trial_id"]))]]["twenty_second_window_count"] += 1
                    count_v3 += 1
                    if count_v3 and count_v3 % 12 == 0:
                        log(f"{subject}/{surface}: v3 windows={count_v3}, elapsed={time.perf_counter()-start_v3:.1f}s")
            processing_rows.append({
                "subject": subject, "surface": surface, "channel_labels": surface_labels,
                "channel_count": len(surface_labels), "channel_order_sha256": label_hash(surface_labels),
                "channel_set_sha256": label_hash(surface_labels, ordered=False),
                "reference_mode": "average_over_surface", "source_reference": "FCz",
                "full_recording_feature_window_count": len(frame),
                "event_contained_8s_window_count": len(selected), "event_contained_20s_v3_window_count": count_v3,
                "fast_core_4s_elapsed_seconds": fast_core_elapsed,
                "v3_elapsed_seconds": time.perf_counter() - start_v3, "preprocessing": prep,
                "malformed_event_sequence_count": malformed,
                "event_interval_rule": "[first_digit_sample,last_digit_sample+3000)",
            })
            del surface_data, frame, coords
        del filtered, ecg_features, ppg_features
        log(f"{subject}: finished")

    event_df = pd.DataFrame(event_rows)
    v3_df = pd.DataFrame(v3_rows)
    fast_core_df = pd.DataFrame(fast_core_rows)
    support_df = pd.DataFrame(support_rows)
    trial_df = pd.DataFrame(all_trials)
    event_df.to_csv(OUT / "event_window_features.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    v3_df.to_csv(OUT / "v3_window_values.csv", index=False)
    fast_core_df.to_csv(OUT / "fast_core_4s_window_values.csv", index=False)
    support_df.to_csv(OUT / "trial_support.csv", index=False)
    trial_df.to_csv(OUT / "trials.csv", index=False)
    (OUT / "normalization_baselines.json").write_text(
        json.dumps(clean_json(baselines), indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8"
    )
    trial_medians, cell, paired, contrast = summarize(event_rows, v3_rows, fast_core_rows, all_trials)
    trial_medians.to_csv(OUT / "trial_medians.csv", index=False)
    cell.to_csv(OUT / "cell_summaries.csv", index=False)
    paired.to_csv(OUT / "participant_paired_differences.csv", index=False)
    contrast.to_csv(OUT / "pilot_contrast_summary.csv", index=False)

    arms = ("conventional_spectral", "raw_mnps_v2_inputs", "historical_mnps_v2", "full_mnps_v3_1", FAST_CORE_20S_SUBSET_ARM, FAST_CORE_ARM)
    common = []
    for subject in PARTICIPANTS:
        for surface in ("native", "core19"):
            for load in (5, 9, 13):
                result = {"subject": subject, "surface": surface, "load": load}
                for arm in arms:
                    subset = cell[(cell.subject == subject) & (cell.surface == surface) & (cell.load == load) & (cell.arm == arm)]
                    counts = subset.groupby("condition")["supported_trial_count"].max().to_dict() if len(subset) else {}
                    result[f"{arm}_paired_cell_supported"] = all(int(counts.get(c, 0)) > 0 for c in ("control", "memory"))
                result["all_six_arms_paired_cell_supported"] = all(result[f"{a}_paired_cell_supported"] for a in arms)
                common.append(result)
    common_df = pd.DataFrame(common)
    common_df.to_csv(OUT / "six_arm_common_cell_support.csv", index=False)

    grouped = support_df.groupby(["surface", "load", "condition"], as_index=False).agg(
        trials=("trial_id", "nunique"), eight_sec_windows=("eight_second_four_second_window_count", "sum"),
        fast_core_four_sec_windows=("fast_core_four_second_window_count", "sum"),
        twenty_sec_windows=("twenty_second_window_count", "sum"))
    lines = [
        "# BENCH-002 six-participant fast-gate-fix pilot", "",
        "Dataset: OpenNeuro ds003838 v1.0.6. Six prespecified participants; native63 and Core19 are separate average-referenced surfaces. This is a bounded execution/support and descriptive paired pilot. No classifier was fit.",
        "",
        "Trial interval: [first digit sample, last digit sample + 3000) at 1 kHz. The independent fast-core arm uses each complete nonoverlap 4 s window inside a single trial, regardless of 20 s support. Full v3.1 retains complete trial-local 20 s windows; its support is expected only at load 13. The separately named 20 s fast-core subset is retained for parity with the previous pilot. Historical v2 fit anchors use the entire continuous task-memory feature grid before event selection.",
        "",
        f"- Complete trials: {len(trial_df)} ({len(PARTICIPANTS)} participants, 162 each).",
        f"- Event-contained 8 s feature windows across surfaces: {len(event_df)}.",
        f"- Independent fast-core 4 s windows across surfaces: {len(fast_core_df)}.",
        f"- Complete v3.1 20 s windows across surfaces: {len(v3_df)}.",
        f"- Six-arm paired participant/surface/load cells with support: {int(common_df['all_six_arms_paired_cell_supported'].sum())}/{len(common_df)}.",
        "- No cohort AUC or inferential interval is reported at n=6.",
        "",
        "## Trial-contained support",
        "",
        "| Surface | Load | Condition | Trials | 8 s/4 s windows | Fast-core 4 s windows | Full-v3 20 s windows |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for row in grouped.itertuples():
        lines.append(f"| {row.surface} | {row.load} | {row.condition} | {row.trials} | {row.eight_sec_windows} | {row.fast_core_four_sec_windows} | {row.twenty_sec_windows} |")
    lines += [
        "", "## Participant-paired descriptive differences", "",
        "Each participant × load × condition value is the median of trial medians. Differences are memory minus control. The summary reports descriptive participant means and medians only.",
        "", "| Surface | Load | Arm | Feature | N | Mean difference | Median difference |",
        "|---|---:|---|---|---:|---:|---:|",
    ]
    for row in contrast.itertuples():
        lines.append(f"| {row.surface} | {row.load} | {row.arm} | {row.feature} | {row.participant_count} | {row.mean_memory_minus_control:.6g} | {row.median_memory_minus_control:.6g} |")
    lines += [
        "", "## Limits", "",
        "The published paper reports prior condition findings and the task uses a fixed control-memory block order, so the contrast remains exploratory and confounded with order. Trial support differs by estimator. Finite outputs are not qualification. The source EEG event export lacks retention-end and recall markers; the endpoint follows the task script and paper. No MNJ was computed.",
        "",
        "The per-window embodied proxy source is saved in event_window_features.csv. The resolver order is ECG RMSSD, ECG HR, PPG rate/amplitude, pupil features if available, then EEG high-frequency power. Pupil data are not read in this bounded pilot; if ECG/PPG do not resolve a row, EEG high-frequency is used and the source is explicit.",
        "",
        "## Output files", "",
        "- bench_002_event_window_amendment_v1_20261008.md: pre-extraction sample and estimator contract.",
        "- event_window_features.csv: retained 8 s event windows and conventional/raw/historical v2 features.",
        "- v3_window_values.csv and v3_measurements.jsonl: full-v3 20 s values plus QC/provenance.",
        "- fast_core_4s_window_values.csv and fast_core_4s_measurements.jsonl: independent trial-local 4 s `[PCV, TP, OI, SC]` values plus QC/provenance.",
        "- trials.csv and trial_support.csv: parsed trial intervals and per-surface support.",
        "- normalization_baselines.json: recording-local v2 fit statistics.",
        "- trial_medians.csv, cell_summaries.csv, participant_paired_differences.csv, pilot_contrast_summary.csv: trial-balanced summaries.",
        "- six_arm_common_cell_support.csv and run_manifest.json: paired-support map and run provenance.", "",
    ]
    (OUT / "results.md").write_text("\n".join(lines), encoding="utf-8")
    source_paths = [p for p in OUT.iterdir() if p.is_file() and p.name != "run_manifest.json"]
    config_path = NMD_ROOT / "mndm/config/config_ingest_common_eeg.yaml"
    amendment = ARTICLE_ROOT / "bench_002_event_window_amendment_v1_20261008.md"
    manifest = {
        "schema": "mnps_bench_002_six_participant_pilot_run.v2",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "complete", "dataset": "OpenNeuro ds003838 v1.0.6",
        "dataset_doi": "10.18112/openneuro.ds003838.v1.0.6", "local_changes_top": changes_top,
        "participants": list(PARTICIPANTS), "full_cohort_run": False, "classifier_fit": False,
        "feature_outcomes_examined": True, "trial_count": len(trial_df),
        "surface_availability": {s: sorted(set(x["surface"] for x in processing_rows if x["subject"] == s)) for s in PARTICIPANTS},
        "event_window_count_8s": len(event_df), "v3_window_count_20s": len(v3_df),
        "fast_core_4s_window_count": len(fast_core_df),
        "six_arm_common_cell_count": int(common_df["all_six_arms_paired_cell_supported"].sum()),
        "six_arm_cell_total": len(common_df), "embodied_proxy_source_counts": dict(proxy_sources),
        "scope_amendment_path": str(amendment), "scope_amendment_sha256": sha256_file(amendment),
        "scope_freeze_sha256": sha256_file(ARTICLE_ROOT / "bench_002_scope_freeze_v1_20261008.json"),
        "config_path": str(config_path), "config_sha256": sha256_file(config_path),
        "implementation_sha256": implementation_hashes, "input_file_sha256": input_hashes,
        "processing_by_subject_surface": processing_rows,
        "outputs": {p.name: {"bytes": p.stat().st_size, "sha256": sha256_file(p)} for p in source_paths},
        "elapsed_seconds": time.perf_counter() - started,
        "claim_ceiling": "exploratory six-participant execution/support pilot; no confirmation or biological qualification",
    }
    (OUT / "run_manifest.json").write_text(json.dumps(clean_json(manifest), indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    log(f"DONE: output={OUT}; elapsed={time.perf_counter()-started:.1f}s; event8={len(event_df)}; fast_core_4s={len(fast_core_df)}; v3_20={len(v3_df)}")

if __name__ == "__main__":
    main()

