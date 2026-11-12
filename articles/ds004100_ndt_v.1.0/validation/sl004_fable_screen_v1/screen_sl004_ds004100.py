"""Run the frozen SL-004 FABLE screen on ds004100.

The runner computes candidate values on matched 8 s windows under two explicit
reference realizations. Ictal samples are isolated before resampling/filtering;
no processing segment spans ictal and non-ictal labels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import re
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

import mne
import numpy as np
import pandas as pd
from scipy import signal, stats
from threadpoolctl import threadpool_limits


HERE = Path(__file__).resolve().parent
DATA_ROOT = Path(r"K:\ExternalReceivedDatasets\openneuro\ds004100")
PREFLIGHT_ROOT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics\project\mnps2_audit\sl\outputs\SL004_DS004100_label_blind_20261111_validated_10s")
PROTOCOL_PATH = HERE / "SL004_DS004100_SCREEN_PROTOCOL_v1.md"
PREFLIGHT_SCRIPT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics\project\mnps2_audit\sl\preflight_sl004_ds004100.py")
FS = 250
WINDOW_SEC = 8
STEP_SEC = 8
EDGE_SEC = 10
EVENT_GUARD_SEC = 10
WINDOW_SAMPLES = FS * WINDOW_SEC
HILBERT_PAD_SAMPLES = FS * 10
CANDIDATES = ["burst_alpha", "sp_disp", "paf_cog"]
COMPARATORS = ["alpha_power_log10", "broadband_power_log10", "broad_spectral_centroid"]
METRICS = CANDIDATES + COMPARATORS
PRIMARY_REF = "recorded_reference_unknown"
REFERENCE_IDS = [PRIMARY_REF, "common_contact_average_reference"]
PILOT_PAIRS = [
    ("sub-HUP173", "seeg"),  # 256 Hz
    ("sub-HUP164", "seeg"),  # 1024 Hz
    ("sub-HUP107", "ecog"),  # 500 Hz
    ("sub-HUP074", "ecog"),  # 512 Hz
]
FILE_RE = re.compile(
    r"^(?P<subject>sub-[^_]+)_ses-(?P<session>[^_]+)_task-(?P<task>[^_]+)_acq-(?P<acq>[^_]+)_run-(?P<run>[^_]+)_ieeg\.edf$"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()


def truth(value: Any) -> bool:
    return value is True or str(value).strip().casefold() in {"true", "1", "yes"}


def sample_grid_windows(row: pd.Series) -> list[float]:
    duration = float(row["sidecar_duration_sec"])
    task = str(row["task"]).casefold()
    if task == "ictal":
        condition_start = float(row["ictal_onset_sec"])
        condition_end = float(row["ictal_offset_sec"])
        event_guard = EVENT_GUARD_SEC
    else:
        condition_start, condition_end = 0.0, duration
        event_guard = 0.0
    first_k = math.ceil((EDGE_SEC - 1e-9) / STEP_SEC)
    last_start = duration - EDGE_SEC - WINDOW_SEC
    starts: list[float] = []
    for k in range(first_k, int(math.floor(last_start / STEP_SEC)) + 1):
        start = float(k * STEP_SEC)
        end = start + WINDOW_SEC
        if start >= condition_start + event_guard - 1e-9 and end <= condition_end - event_guard + 1e-9:
            starts.append(start)
    return starts


def common_good_contacts(pair_records: pd.DataFrame, acq: str) -> tuple[list[str], str]:
    intersections: list[set[str]] = []
    ordered_first: list[str] | None = None
    for _, row in pair_records.sort_values("relative_path").iterrows():
        channels = pd.read_csv(row["channels_path"], sep="\t", keep_default_na=False, dtype=str)
        mask = (
            channels["status"].astype(str).str.strip().str.casefold().eq("good")
            & channels["type"].astype(str).str.strip().str.upper().eq(acq.upper())
        )
        ordered = channels.loc[mask, "name"].astype(str).tolist()
        intersections.append(set(ordered))
        if ordered_first is None:
            ordered_first = channels["name"].astype(str).tolist()
    common = set.intersection(*intersections) if intersections else set()
    ordered_common = [name for name in (ordered_first or []) if name in common]
    if not ordered_common:
        return [], stable_hash([])
    return ordered_common, stable_hash(ordered_common)


def load_resampled_segment(row: pd.Series, contact_names: list[str]) -> tuple[np.ndarray, int, dict[str, Any]]:
    """Read one labeled interval, resample it, and return its EDF-grid origin.

    For ictal recordings the raw event is isolated before resampling and only
    same-event reflection is used as context. The left extension is chosen so
    the output polyphase grid stays aligned to the EDF run start.
    """
    path = Path(str(row["edf_path"]))
    raw = mne.io.read_raw_edf(path, preload=False, verbose="ERROR")
    try:
        native_fs = float(raw.info["sfreq"])
        if abs(native_fs - float(row["header_sfreq"])) > 1e-9:
            raise ValueError("edf_sampling_rate_changed_after_preflight")
        if str(row["task"]).casefold() == "ictal":
            source_start = int(round(float(row["ictal_onset_sample"])))
            source_stop = int(round(float(row["ictal_offset_sample"])))
            if not (0 <= source_start < source_stop <= int(raw.n_times)):
                raise ValueError("ictal_sample_bounds_outside_edf")
        else:
            source_start, source_stop = 0, int(raw.n_times)
        values_uv = raw.get_data(picks=contact_names, start=source_start, stop=source_stop, verbose="ERROR") * 1e6
        n_times = int(raw.n_times)
    finally:
        raw.close()

    if values_uv.shape[0] != len(contact_names) or values_uv.shape[1] < 2:
        raise ValueError("unsupported_contact_or_sample_count")
    if not np.isfinite(values_uv).all():
        raise ValueError("nonfinite_source_samples_on_fixed_contact_set")

    native_rate = int(round(native_fs))
    ratio = Fraction(FS, native_rate)
    up, down = ratio.numerator, ratio.denominator
    if str(row["task"]).casefold() == "ictal":
        # At least 1 s of reflected event-only signal; align padded origin to
        # the output grid, whose phase is fixed by EDF time zero.
        minimum_pad = int(math.ceil(native_fs))
        pad_left = minimum_pad + ((source_start - minimum_pad) % down)
        pad_right = minimum_pad
        if pad_left >= values_uv.shape[1] or pad_right >= values_uv.shape[1]:
            raise ValueError("ictal_interval_too_short_for_reflected_resample_padding")
        values_uv = np.pad(values_uv, ((0, 0), (pad_left, pad_right)), mode="reflect")
        padded_source_start = source_start - pad_left
        if padded_source_start % down:
            raise RuntimeError("polyphase_origin_does_not_align_to_edf_grid")
        output_origin = (padded_source_start * up) // down
    else:
        output_origin = 0

    resampled = signal.resample_poly(values_uv, up, down, axis=-1)
    return np.ascontiguousarray(resampled, dtype=np.float64), int(output_origin), {
        "native_sampling_rate_hz": native_fs,
        "source_sample_count": int(source_stop - source_start),
        "edf_sample_count": n_times,
        "resample_up": up,
        "resample_down": down,
        "resampled_sample_count": int(resampled.shape[-1]),
        "resampled_origin_sample_on_edf_grid": int(output_origin),
        "ictal_event_wasolated_before_resampling": str(row["task"]).casefold() == "ictal",
    }


def compute_window_metrics(
    filtered: np.ndarray,
    envelope: np.ndarray,
    start_sample: int,
    n_contacts: int,
) -> tuple[dict[str, float], str]:
    end_sample = start_sample + WINDOW_SAMPLES
    x = filtered[:, start_sample:end_sample]
    env = envelope[:, start_sample:end_sample]
    result: dict[str, float] = {name: float("nan") for name in METRICS}
    invalid: list[str] = []

    env_mean = np.mean(env, axis=1)
    env_sd = np.std(env, axis=1, ddof=0)
    if np.all(np.isfinite(env_mean)) and np.all(env_mean > 0) and np.all(np.isfinite(env_sd)):
        result["burst_alpha"] = float(np.median(env_sd / env_mean))
    alpha_power = np.mean(env * env, axis=1)
    median_alpha_power = float(np.median(alpha_power))
    if np.all(np.isfinite(alpha_power)) and np.isfinite(median_alpha_power) and median_alpha_power > 0:
        result["alpha_power_log10"] = float(np.log10(median_alpha_power))

    channel_var = np.var(x, axis=1, ddof=0)
    if np.all(np.isfinite(channel_var)) and np.all(channel_var > 0):
        log_var = np.log10(channel_var)
        median_log_var = float(np.median(log_var))
        result["sp_disp"] = float(1.4826 * np.median(np.abs(log_var - median_log_var)))
        result["broadband_power_log10"] = median_log_var

    freqs, psd = signal.welch(
        x,
        fs=FS,
        window="hann",
        nperseg=4 * FS,
        noverlap=2 * FS,
        detrend="constant",
        scaling="density",
        axis=-1,
    )
    median_psd = np.median(psd, axis=0)
    if np.all(np.isfinite(median_psd)):
        paf = (freqs >= 7.0) & (freqs <= 13.0)
        broad = (freqs >= 1.0) & (freqs <= 45.0)
        paf_power = float(np.sum(median_psd[paf]))
        broad_power = float(np.sum(median_psd[broad]))
        if paf_power > 0:
            result["paf_cog"] = float(np.sum(freqs[paf] * median_psd[paf]) / paf_power)
        if broad_power > 0:
            result["broad_spectral_centroid"] = float(np.sum(freqs[broad] * median_psd[broad]) / broad_power)

    invalid = [name for name, value in result.items() if not np.isfinite(value)]
    return result, ";".join(invalid)


def process_recording(
    row: pd.Series,
    pair_contacts: list[str],
    channel_hash: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    starts = sample_grid_windows(row)
    relative_path = str(row["relative_path"])
    base = {
        "subject": str(row["subject"]),
        "acq": str(row["acq"]),
        "task": str(row["task"]),
        "run": str(row["run"]),
        "relative_path": relative_path,
        "n_common_good_contacts": len(pair_contacts),
        "ordered_contact_set_sha256": channel_hash,
        "n_guarded_windows": len(starts),
        "expected_guarded_windows": int(float(row["guarded_8s_window_count"])),
        "recording_duration_sec": float(row["sidecar_duration_sec"]),
        "event_onset_sec": float(row["ictal_onset_sec"]) if str(row["task"]).casefold() == "ictal" else np.nan,
        "event_offset_sec": float(row["ictal_offset_sec"]) if str(row["task"]).casefold() == "ictal" else np.nan,
    }
    if len(starts) != base["expected_guarded_windows"]:
        raise ValueError(f"preflight_window_count_mismatch:{relative_path}:{len(starts)}!={base['expected_guarded_windows']}")
    if not starts:
        return [], [{**base, "reference": ref, "status": "no_guarded_windows", "error": ""} for ref in REFERENCE_IDS]

    resampled, output_origin, resample_info = load_resampled_segment(row, pair_contacts)
    feature_rows: list[dict[str, Any]] = []
    support_rows: list[dict[str, Any]] = []
    sos = signal.butter(4, [8.0, 12.0], btype="bandpass", fs=FS, output="sos")

    for reference in REFERENCE_IDS:
        segment = resampled.copy()
        if reference == "common_contact_average_reference":
            segment -= np.mean(segment, axis=0, keepdims=True)
        try:
            mne.filter.notch_filter(segment, FS, freqs=[60.0], copy=False, verbose="ERROR")
            mne.filter.filter_data(segment, FS, l_freq=1.0, h_freq=45.0, copy=False, verbose="ERROR")
            if not np.isfinite(segment).all():
                raise ValueError("nonfinite_filtered_values")

            alpha_pad = np.pad(segment, ((0, 0), (HILBERT_PAD_SAMPLES, HILBERT_PAD_SAMPLES)), mode="reflect")
            alpha_filtered = signal.sosfiltfilt(sos, alpha_pad, axis=-1)
            analytic = signal.hilbert(alpha_filtered, axis=-1)
            envelope = np.abs(analytic[:, HILBERT_PAD_SAMPLES:-HILBERT_PAD_SAMPLES])
            del alpha_pad, alpha_filtered, analytic
            if not np.isfinite(envelope).all():
                raise ValueError("nonfinite_hilbert_envelope")

            for start_sec in starts:
                global_start = int(round(start_sec * FS))
                local_start = global_start - output_origin
                if local_start < 0 or local_start + WINDOW_SAMPLES > segment.shape[-1]:
                    raise ValueError(f"window_outside_resampled_segment:{start_sec}")
                metrics, invalid_metrics = compute_window_metrics(segment, envelope, local_start, len(pair_contacts))
                feature_rows.append({
                    **base,
                    **resample_info,
                    "reference": reference,
                    "window_start_sec": float(start_sec),
                    "window_end_sec": float(start_sec + WINDOW_SEC),
                    "n_contacts": len(pair_contacts),
                    "feature_qc_invalid_metrics": invalid_metrics,
                    **metrics,
                })
            support_rows.append({**base, **resample_info, "reference": reference, "status": "computed", "error": ""})
        except Exception as exc:  # noqa: BLE001 - keep run/reference QC and other computable results.
            support_rows.append({**base, **resample_info, "reference": reference, "status": "error", "error": f"{type(exc).__name__}:{exc}"})
        finally:
            del segment

    del resampled
    return feature_rows, support_rows


def holm_adjust(pvalues: list[float]) -> list[float]:
    if not pvalues:
        return []
    p = np.asarray(pvalues, dtype=float)
    order = np.argsort(p)
    adjusted = np.empty_like(p)
    running = 0.0
    n = len(p)
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (n - rank) * p[index]))
        adjusted[index] = running
    return adjusted.tolist()


def bootstrap_median(values: np.ndarray, rng: np.random.Generator, draws: int = 10_000) -> tuple[float, float]:
    n = len(values)
    if n == 0:
        return float("nan"), float("nan")
    indices = rng.integers(0, n, size=(draws, n))
    boot = np.median(values[indices], axis=1)
    return float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))


def make_run_summaries(features: pd.DataFrame) -> pd.DataFrame:
    keys = ["subject", "acq", "task", "run", "relative_path", "reference", "ordered_contact_set_sha256"]
    rows: list[dict[str, Any]] = []
    for key, group in features.groupby(keys, dropna=False):
        meta = dict(zip(keys, key))
        for metric in METRICS:
            values = pd.to_numeric(group[metric], errors="coerce").to_numpy(dtype=float)
            finite = values[np.isfinite(values)]
            if finite.size:
                rows.append({**meta, "metric": metric, "run_median": float(np.median(finite)), "n_valid_windows": int(finite.size), "n_windows": int(len(group))})
    return pd.DataFrame(rows)


def make_participant_contrasts(run_summaries: pd.DataFrame) -> pd.DataFrame:
    if run_summaries.empty:
        return pd.DataFrame()
    keys = ["subject", "acq", "reference", "metric"]
    task_rows: list[dict[str, Any]] = []
    for key, group in run_summaries.groupby(keys, dropna=False):
        meta = dict(zip(keys, key))
        for task in ("ictal", "interictal"):
            part = group[group.task == task]
            if len(part):
                task_rows.append({
                    **meta,
                    "task": task,
                    "participant_task_median": float(np.median(part.run_median.to_numpy(dtype=float))),
                    "n_runs": int(part.relative_path.nunique()),
                    "n_valid_windows": int(part.n_valid_windows.sum()),
                })
    task_frame = pd.DataFrame(task_rows)
    output: list[dict[str, Any]] = []
    for key, group in task_frame.groupby(keys, dropna=False):
        values = {row.task: row for row in group.itertuples(index=False)}
        if "ictal" not in values or "interictal" not in values:
            continue
        ictal, inter = values["ictal"], values["interictal"]
        meta = dict(zip(keys, key))
        output.append({
            **meta,
            "ictal_median": float(ictal.participant_task_median),
            "interictal_median": float(inter.participant_task_median),
            "participant_delta_ictal_minus_interictal": float(ictal.participant_task_median - inter.participant_task_median),
            "n_ictal_runs": int(ictal.n_runs),
            "n_interictal_runs": int(inter.n_runs),
            "n_ictal_windows": int(ictal.n_valid_windows),
            "n_interictal_windows": int(inter.n_valid_windows),
        })
    return pd.DataFrame(output)


def summarize_effects(contrasts: pd.DataFrame, seed: int = 20261111) -> pd.DataFrame:
    if contrasts.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for (acq, reference, metric), group in contrasts.groupby(["acq", "reference", "metric"]):
        values = group.participant_delta_ictal_minus_interictal.to_numpy(dtype=float)
        values = values[np.isfinite(values)]
        rng = np.random.default_rng(seed + (sum(ord(c) for c in f"{acq}:{reference}:{metric}") % 1_000_000))
        low, high = bootstrap_median(values, rng)
        positive = int(np.sum(values > 0))
        negative = int(np.sum(values < 0))
        zero = int(np.sum(values == 0))
        p_sign = (
            float(stats.binomtest(positive, positive + negative, 0.5, alternative="two-sided").pvalue)
            if positive + negative and metric in CANDIDATES and reference == PRIMARY_REF
            else float("nan")
        )
        rows.append({
            "acq": acq,
            "reference": reference,
            "metric": metric,
            "n_participants": int(values.size),
            "median_participant_delta": float(np.median(values)) if values.size else float("nan"),
            "mean_participant_delta": float(np.mean(values)) if values.size else float("nan"),
            "bootstrap_95_low_median": low,
            "bootstrap_95_high_median": high,
            "n_positive": positive,
            "n_negative": negative,
            "n_zero": zero,
            "positive_fraction_nonzero": float(positive / (positive + negative)) if positive + negative else float("nan"),
            "exact_two_sided_sign_test_p": p_sign,
            "holm_p_primary_family": float("nan"),
        })
    result = pd.DataFrame(rows)
    for acq in ("seeg", "ecog"):
        mask = (result.acq == acq) & (result.reference == PRIMARY_REF) & result.metric.isin(CANDIDATES)
        valid = result.loc[mask & np.isfinite(result.exact_two_sided_sign_test_p), :]
        adjusted = holm_adjust(valid.exact_two_sided_sign_test_p.tolist())
        result.loc[valid.index, "holm_p_primary_family"] = adjusted
    return result


def make_reference_comparison(contrasts: pd.DataFrame) -> pd.DataFrame:
    if contrasts.empty:
        return pd.DataFrame()
    output: list[dict[str, Any]] = []
    for (acq, metric), group in contrasts[contrasts.metric.isin(CANDIDATES)].groupby(["acq", "metric"]):
        wide = group.pivot(index="subject", columns="reference", values="participant_delta_ictal_minus_interictal")
        if PRIMARY_REF not in wide or "common_contact_average_reference" not in wide:
            continue
        matched = wide[[PRIMARY_REF, "common_contact_average_reference"]].dropna()
        if matched.empty:
            continue
        primary = matched[PRIMARY_REF].to_numpy(dtype=float)
        average = matched["common_contact_average_reference"].to_numpy(dtype=float)
        delta = average - primary
        rng = np.random.default_rng(20261111 + (sum(ord(c) for c in f"ref:{acq}:{metric}") % 1_000_000))
        low, high = bootstrap_median(delta, rng)
        nonzero = (primary != 0) & (average != 0)
        output.append({
            "acq": acq,
            "metric": metric,
            "n_matched_participants": int(len(matched)),
            "median_delta_recorded_reference_unknown": float(np.median(primary)),
            "median_delta_common_contact_average_reference": float(np.median(average)),
            "median_reference_effect_shift_average_minus_recorded": float(np.median(delta)),
            "bootstrap_95_low_reference_effect_shift": low,
            "bootstrap_95_high_reference_effect_shift": high,
            "direction_agreement_fraction_nonzero": float(np.mean(np.sign(primary[nonzero]) == np.sign(average[nonzero]))) if np.any(nonzero) else float("nan"),
            "n_direction_reversals": int(np.sum(np.sign(primary[nonzero]) != np.sign(average[nonzero]))) if np.any(nonzero) else 0,
        })
    return pd.DataFrame(output)


def make_comparator_correlations(contrasts: pd.DataFrame) -> pd.DataFrame:
    primary = contrasts[(contrasts.acq == "seeg") & (contrasts.reference == PRIMARY_REF)]
    if primary.empty:
        return pd.DataFrame()
    wide = primary.pivot(index="subject", columns="metric", values="participant_delta_ictal_minus_interictal")
    output: list[dict[str, Any]] = []
    for candidate in CANDIDATES:
        for comparator in COMPARATORS:
            if candidate not in wide or comparator not in wide:
                continue
            pair = wide[[candidate, comparator]].dropna().to_numpy(dtype=float)
            if len(pair) < 3 or np.std(pair[:, 0]) == 0 or np.std(pair[:, 1]) == 0:
                output.append({"candidate": candidate, "comparator": comparator, "n_participants": int(len(pair)), "spearman_rho": float("nan"), "bootstrap_95_low": float("nan"), "bootstrap_95_high": float("nan")})
                continue
            rho = float(stats.spearmanr(pair[:, 0], pair[:, 1]).statistic)
            rng = np.random.default_rng(20261111 + (sum(ord(c) for c in f"corr:{candidate}:{comparator}") % 1_000_000))
            draws: list[float] = []
            n = len(pair)
            for _ in range(10_000):
                sample = pair[rng.integers(0, n, size=n)]
                if np.std(sample[:, 0]) and np.std(sample[:, 1]):
                    value = stats.spearmanr(sample[:, 0], sample[:, 1]).statistic
                    if np.isfinite(value):
                        draws.append(float(value))
            low, high = (np.quantile(draws, [0.025, 0.975]).tolist() if draws else (float("nan"), float("nan")))
            output.append({"candidate": candidate, "comparator": comparator, "n_participants": int(n), "spearman_rho": rho, "bootstrap_95_low": float(low), "bootstrap_95_high": float(high)})
    return pd.DataFrame(output)


def parse_pair_list(values: list[str] | None, mode: str) -> list[tuple[str, str]] | None:
    if not values:
        return PILOT_PAIRS if mode == "pilot" else None
    pairs: list[tuple[str, str]] = []
    for value in values:
        for item in value.split(","):
            subject, acq = item.strip().split(":", maxsplit=1)
            pairs.append((subject.strip(), acq.strip().casefold()))
    return pairs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["pilot", "full"], default="full")
    parser.add_argument("--pairs", nargs="*", help="Optional patient:acq pairs, e.g. sub-HUP173:seeg,sub-HUP107:ecog")
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()
    start_time = time.perf_counter()
    mne.set_log_level("ERROR")
    threadpool_limits(limits=1)

    preflight_manifest_path = PREFLIGHT_ROOT / "manifest.json"
    preflight_manifest = json.loads(preflight_manifest_path.read_text(encoding="utf-8"))
    if preflight_manifest["filter_support_audit"]["combined_resample_notch_broadband_alpha_effective_half_support_sec"] >= EDGE_SEC:
        raise RuntimeError("edge_guard_does_not_exceed_measured_filter_support")
    inventory = pd.read_csv(PREFLIGHT_ROOT / "recording_inventory.csv")
    pair_support = pd.read_csv(PREFLIGHT_ROOT / "participant_pair_support.csv")
    eligible_pairs_frame = pair_support[
        pair_support.screen_eligible_with_common_good_channels_and_guarded_windows.map(truth)
    ].copy()
    eligible_pairs = set(zip(eligible_pairs_frame.subject.astype(str), eligible_pairs_frame.acq.astype(str)))
    requested_pairs = parse_pair_list(args.pairs, args.mode)
    if requested_pairs is None:
        selected_pairs = sorted(eligible_pairs)
    else:
        selected_pairs = sorted(set(requested_pairs))
        unsupported = [pair for pair in selected_pairs if pair not in eligible_pairs]
        if unsupported:
            raise ValueError(f"requested_pairs_not_screen_eligible:{unsupported}")
    selected_set = set(selected_pairs)
    selected_records = inventory[
        inventory.apply(lambda r: (str(r.subject), str(r.acq)) in selected_set and str(r.task) in {"ictal", "interictal"}, axis=1)
    ].copy()
    if selected_records.empty:
        raise RuntimeError("no_recordings_selected")

    out_dir = args.out_dir or (
        HERE / "outputs" / ("SL004_DS004100_pilot_v1_20261111" if args.mode == "pilot" else "SL004_DS004100_final_screen_v1_20261111")
    )
    if out_dir.exists():
        raise FileExistsError(out_dir)
    out_dir.mkdir(parents=True, exist_ok=False)

    contact_sets: dict[tuple[str, str], tuple[list[str], str]] = {}
    for pair in selected_pairs:
        rows = selected_records[(selected_records.subject == pair[0]) & (selected_records.acq == pair[1])]
        contacts, channel_hash = common_good_contacts(rows, pair[1])
        expected = int(eligible_pairs_frame.loc[(eligible_pairs_frame.subject == pair[0]) & (eligible_pairs_frame.acq == pair[1]), "common_good_ieeg_channels"].iloc[0])
        if len(contacts) != expected:
            raise RuntimeError(f"common_contact_count_changed:{pair}:{len(contacts)}!={expected}")
        contact_sets[pair] = (contacts, channel_hash)

    window_rows: list[dict[str, Any]] = []
    support_rows: list[dict[str, Any]] = []
    selected_records = selected_records.sort_values(["subject", "acq", "task", "run"]).reset_index(drop=True)
    for index, row in selected_records.iterrows():
        pair = (str(row.subject), str(row.acq))
        contacts, channel_hash = contact_sets[pair]
        try:
            rows, support = process_recording(row, contacts, channel_hash)
            window_rows.extend(rows)
            support_rows.extend(support)
        except Exception as exc:  # noqa: BLE001 - record the failed source, preserve other recordings.
            base = {
                "subject": pair[0], "acq": pair[1], "task": str(row.task), "run": str(row.run),
                "relative_path": str(row.relative_path), "n_common_good_contacts": len(contacts),
                "ordered_contact_set_sha256": channel_hash, "n_guarded_windows": len(sample_grid_windows(row)),
                "expected_guarded_windows": int(float(row.guarded_8s_window_count)),
            }
            support_rows.extend([{**base, "reference": ref, "status": "error", "error": f"{type(exc).__name__}:{exc}"} for ref in REFERENCE_IDS])
        if (index + 1) % 10 == 0 or index + 1 == len(selected_records):
            print(f"recordings processed {index + 1}/{len(selected_records)}; window rows {len(window_rows)}", flush=True)

    windows = pd.DataFrame(window_rows)
    run_support = pd.DataFrame(support_rows)
    if windows.empty:
        raise RuntimeError("no_candidate_windows_computed")
    windows.to_csv(out_dir / "window_features.csv", index=False)
    run_support.to_csv(out_dir / "run_support.csv", index=False)
    run_summaries = make_run_summaries(windows)
    run_summaries.to_csv(out_dir / "run_summaries.csv", index=False)

    contrasts = pd.DataFrame()
    effects = pd.DataFrame()
    ref_comparison = pd.DataFrame()
    correlations = pd.DataFrame()
    if args.mode == "full":
        contrasts = make_participant_contrasts(run_summaries)
        effects = summarize_effects(contrasts)
        ref_comparison = make_reference_comparison(contrasts)
        correlations = make_comparator_correlations(contrasts)
        contrasts.to_csv(out_dir / "participant_contrasts.csv", index=False)
        effects.to_csv(out_dir / "screen_statistics.csv", index=False)
        ref_comparison.to_csv(out_dir / "reference_sensitivity.csv", index=False)
        correlations.to_csv(out_dir / "comparator_change_correlations.csv", index=False)

    protocol_hash = sha256_file(PROTOCOL_PATH)
    script_hash = sha256_file(Path(__file__).resolve())
    preflight_script_hash = sha256_file(PREFLIGHT_SCRIPT)
    status_counts = run_support.groupby(["reference", "status"]).size().to_dict()
    manifest = {
        "protocol_id": "SL-004 ds004100 candidate screen v1",
        "realization_id": "FABLE_DS004100_BOUNDARY_SAFE_v1",
        "mode": args.mode,
        "created_local_date": "2026-11-11",
        "candidate_features_computed": True,
        "candidate_condition_contrasts_computed": bool(args.mode == "full"),
        "selected_patient_acquisition_pairs": [f"{s}:{a}" for s, a in selected_pairs],
        "selected_recordings": int(len(selected_records)),
        "window_feature_rows": int(len(windows)),
        "run_support_status_counts": {f"{k[0]}:{k[1]}": int(v) for k, v in status_counts.items()},
        "participant_contrast_rows": int(len(contrasts)),
        "metrics": METRICS,
        "reference_realizations": REFERENCE_IDS,
        "eligible_pairs_by_modality_from_preflight": preflight_manifest["screen_eligible_participants_by_modality"],
        "dataset_doi": preflight_manifest["dataset_doi"],
        "dataset_bids_spec_version": preflight_manifest["dataset_bids_version"],
        "datalad_dataset_uuid": preflight_manifest["datalad_dataset_uuid"],
        "local_git_commit_sha": preflight_manifest["local_git_commit_sha"],
        "edf_file_index_sha256_name_and_size_only": preflight_manifest["edf_file_index_sha256_name_and_size_only"],
        "preflight_manifest_sha256": sha256_file(preflight_manifest_path),
        "preflight_metadata_hash_manifest_sha256": sha256_file(PREFLIGHT_ROOT / "metadata_input_hashes.csv"),
        "protocol_sha256": protocol_hash,
        "screen_script_sha256": script_hash,
        "preflight_script_sha256": preflight_script_hash,
        "filter_support_audit": preflight_manifest["filter_support_audit"],
        "software": {"python": platform.python_version(), "mne": mne.__version__, "numpy": np.__version__, "pandas": pd.__version__},
        "elapsed_seconds": round(time.perf_counter() - start_time, 1),
        "outputs": [
            "window_features.csv", "run_support.csv", "run_summaries.csv",
            *(["participant_contrasts.csv", "screen_statistics.csv", "reference_sensitivity.csv", "comparator_change_correlations.csv"] if args.mode == "full" else []),
            "manifest.json", "readout.md",
        ],
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    if args.mode == "full":
        write_full_readout(out_dir, manifest, effects, ref_comparison, correlations, run_support)
    else:
        (out_dir / "readout.md").write_text(
            "# SL-004 technical pilot\n\n"
            "Candidate windows were computed only to check execution, support, reference symmetry, and finite-value handling. "
            "No participant contrasts, hypothesis tests, or condition effects were calculated or inspected.\n\n"
            f"- Selected pairs: {', '.join(manifest['selected_patient_acquisition_pairs'])}\n"
            f"- Recordings: {manifest['selected_recordings']}\n"
            f"- Window rows: {manifest['window_feature_rows']}\n"
            f"- Run support statuses: `{manifest['run_support_status_counts']}`\n",
            encoding="utf-8",
        )
    print(json.dumps({
        "output": str(out_dir),
        "mode": args.mode,
        "selected_pairs": len(selected_pairs),
        "recordings": len(selected_records),
        "window_rows": len(windows),
        "run_support_status_counts": manifest["run_support_status_counts"],
        "candidate_values_printed": False,
        "contrasts_computed": bool(args.mode == "full"),
        "elapsed_seconds": manifest["elapsed_seconds"],
    }, indent=2), flush=True)
    return 0


def write_full_readout(
    out_dir: Path,
    manifest: dict[str, Any],
    effects: pd.DataFrame,
    reference: pd.DataFrame,
    correlations: pd.DataFrame,
    run_support: pd.DataFrame,
) -> None:
    def table(frame: pd.DataFrame) -> str:
        if frame.empty:
            return "(no rows)"
        view = frame.copy()
        for col in view.columns:
            if pd.api.types.is_float_dtype(view[col]):
                view[col] = view[col].map(lambda x: "" if not np.isfinite(x) else f"{x:.4g}")
        headers = [str(c) for c in view.columns]
        rows = [["" if pd.isna(v) else str(v) for v in row] for row in view.itertuples(index=False, name=None)]
        lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
        lines.extend("| " + " | ".join(v.replace("|", "\\|") for v in row) + " |" for row in rows)
        return "\n".join(lines)

    primary = effects[(effects.acq == "seeg") & (effects.reference == PRIMARY_REF) & effects.metric.isin(CANDIDATES)]
    seeg_average = effects[(effects.acq == "seeg") & (effects.reference == "common_contact_average_reference") & effects.metric.isin(CANDIDATES)]
    ecog = effects[(effects.acq == "ecog") & effects.metric.isin(CANDIDATES)]
    errors = run_support[run_support.status == "error"]
    lines = [
        "# SL-004 final candidate screen — ds004100",
        "",
        "**Exploratory, unqualified measurement screen. MNPS v2 remains frozen.** Candidate values and paired contrasts were computed under the frozen experimental realization.",
        "",
        f"- Snapshot DOI: `{manifest['dataset_doi']}`; BIDS specification: `{manifest['dataset_bids_spec_version']}`; DataLad UUID: `{manifest['datalad_dataset_uuid']}`.",
        f"- Eligible pair support before signal QC: {manifest['eligible_pairs_by_modality_from_preflight']} (10 s margins; SEEG and ECoG kept separate).",
        f"- Screened recordings: {manifest['selected_recordings']}; candidate window rows across both reference realizations: {manifest['window_feature_rows']}; processing errors: {len(errors)}.",
        "- Primary tests are exact two-sided sign tests on participant-level SEEG contrasts under `recorded_reference_unknown`, Holm-adjusted across the three candidates. The sign test assesses direction consistency; effect magnitude is reported by the median contrast and participant-bootstrap interval.",
        "- ECoG is a separate sensitivity analysis, with its own Holm family. It is not pooled with SEEG.",
        "- Both reference realizations use identical contact sets and windows. Reference sensitivity is reported descriptively; it does not recover the physical hardware reference.",
        "- Comparator correlations are diagnostics only. No patient-held-out prediction test was run, so this screen cannot establish incremental predictive value or superiority over omitted MNPS coordinates.",
        "",
        "## SEEG primary: recorded reference unknown",
        "",
        table(primary),
        "",
        "## SEEG reference sensitivity: common-contact average reference",
        "",
        table(seeg_average),
        "",
        "## ECoG separate modality analysis",
        "",
        table(ecog),
        "",
        "## Reference effect shifts",
        "",
        table(reference),
        "",
        "## Candidate–comparator change correlations (SEEG, recorded reference unknown)",
        "",
        table(correlations),
        "",
        "## Limits and next decision",
        "",
        "`paf_cog` remains a 7–13 Hz band centroid unless a resolved peak diagnostic supports a peak interpretation. `sp_disp` is a spread across patient-specific implanted contacts. `burst_alpha` uses an event/run-local Hilbert transform; it is a state descriptor, not prospective forecasting. A consistent paired difference supports a regime descriptor, not unique information. If a candidate is considered for experimental MNPS 3.4, assess whether its participant changes overlap the simple spectral comparators and then require a separate patient-held-out predictive-value study. This screen has no aligned, comparable MNPS v2 baseline and cannot support a claim that candidates outperform coordinates proposed for removal.",
        "",
        "## Reproducibility artifacts",
        "",
        "See `manifest.json` for the frozen protocol/script hashes and software versions; `window_features.csv` and `run_support.csv` preserve window-level values and support; `participant_contrasts.csv` preserves one participant contrast per metric/reference/modality.",
    ]
    (out_dir / "readout.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
