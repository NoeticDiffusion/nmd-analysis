from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

NMD_ROOT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics")
ARTICLE_ROOT = Path(r"J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385")
PROTOCOL = ARTICLE_ROOT / "v3_temporal_fidelity_003_protocol_v1_20261009.md"
V002 = ARTICLE_ROOT / "outputs" / "v3_multiscale_fidelity_002_pilot_v1_20261009"
OUT = ARTICLE_ROOT / "outputs" / "v3_temporal_fidelity_003_pilot_v1_20261009"
N_CHANNELS = 19
SFREQ = 250.0
DURATION_SEC = 20
N_SAMPLES = int(SFREQ * DURATION_SEC)
SEGMENTS = ((0, 8, 0.2, "A"), (8, 12, 0.8, "B"), (12, 20, 0.2, "A"))
SEED_BASE = 20261030
REPLICATES = 200
WINDOW_DURATIONS = (4, 8, 12, 20)
SCREEN_THRESHOLDS = {
    "background_4s_median_absolute_bias_max": 0.10,
    "transient_4s_median_absolute_bias_max": 0.10,
    "transient_minus_background_median_max": -0.40,
    "mixed_20s_median_absolute_bias_max": 0.05,
}
LABELS = tuple(f"S{i:02d}" for i in range(1, N_CHANNELS + 1))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_array(values: np.ndarray) -> str:
    canonical = np.ascontiguousarray(np.asarray(values, dtype="<f8"))
    return hashlib.sha256(canonical.view(np.uint8)).hexdigest()


def generate_piecewise_ar1(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    result = np.empty((N_CHANNELS, N_SAMPLES), dtype=np.float64)
    for start_sec, end_sec, rho, _name in SEGMENTS:
        left = int(start_sec * SFREQ)
        right = int(end_sec * SFREQ)
        length = right - left
        result[:, left] = rng.normal(size=N_CHANNELS)
        innovation_scale = float(np.sqrt(1.0 - rho * rho))
        for sample in range(left + 1, right):
            result[:, sample] = rho * result[:, sample - 1] + innovation_scale * rng.normal(size=N_CHANNELS)
        if length < 2:
            raise ValueError("each regime must contain at least two samples")
    return result


def target_tp(start_sample: int, end_sample: int) -> float:
    pair_covariance = 0.0
    total_pairs = end_sample - start_sample - 1
    for start_sec, end_sec, rho, _name in SEGMENTS:
        left = max(start_sample, int(start_sec * SFREQ))
        right = min(end_sample, int(end_sec * SFREQ))
        segment_samples = max(0, right - left)
        if segment_samples >= 2:
            pair_covariance += (segment_samples - 1) * rho
    return 1.0 - pair_covariance / total_pairs


def window_regime(start_sample: int, end_sample: int) -> str:
    overlaps: list[str] = []
    for start_sec, end_sec, _rho, name in SEGMENTS:
        if min(end_sample, int(end_sec * SFREQ)) > max(start_sample, int(start_sec * SFREQ)):
            overlaps.append(name)
    if len(set(overlaps)) == 1:
        return overlaps[0]
    return "mixed"


def main() -> None:
    started = time.perf_counter()
    if OUT.exists():
        raise FileExistsError(f"refusing to overwrite V003 output: {OUT}")
    OUT.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(NMD_ROOT / "core" / "src"))
    sys.path.insert(0, str(NMD_ROOT / "mndm" / "src"))
    from mndm.mnps.v3_1.pipeline_measurements import compute_pipeline_m2_temporal_measurement

    v002_summary_path = V002 / "synthetic_screening_summary.csv"
    v002_summary = pd.read_csv(v002_summary_path)
    stationary = v002_summary.loc[v002_summary["candidate"].eq("TP")].copy()
    if len(stationary) != 8:
        raise ValueError(f"expected eight frozen V002 stationary TP rows; got {len(stationary)}")
    stationary.to_csv(OUT / "stationary_tp_screen_reuse.csv", index=False)

    signal_rows: list[dict[str, Any]] = []
    measurement_rows: list[dict[str, Any]] = []
    support_qc = {
        "source_is_continuous": True,
        "timestamps_uniform": True,
        "input_samples_finite": True,
        "gap_free": True,
        "bad_interval_free": True,
        "within_recording_bounds": True,
        "effective_filter_support_valid": True,
        "effective_filter_support_status": "known_synthetic_no_filter",
    }
    input_branch = {
        "branch_id": "v3_temporal_fidelity_003_synthetic_piecewise_ar1",
        "reference_mode": "synthetic_unreferenced_independent_channels",
        "reference_set_sha256": hashlib.sha256("\n".join(LABELS).encode()).hexdigest(),
        "filter_band_hz": None,
    }

    for replicate in range(REPLICATES):
        seed = SEED_BASE + replicate
        signal = generate_piecewise_ar1(seed)
        signal_hash = sha256_array(signal)
        signal_rows.append({"replicate": replicate, "seed": seed, "signal_sha256": signal_hash,
                            "shape": list(signal.shape), "dtype": "float64"})
        for duration_sec in WINDOW_DURATIONS:
            duration_samples = int(duration_sec * SFREQ)
            for start_sec in range(0, DURATION_SEC - duration_sec + 1, 4):
                start_sample = int(start_sec * SFREQ)
                end_sample = start_sample + duration_samples
                window = signal[:, start_sample:end_sample]
                truth = target_tp(start_sample, end_sample)
                segment_id = f"v3tf003_seed{seed}_{start_sec}s_{duration_sec}s"
                result = compute_pipeline_m2_temporal_measurement(
                    window,
                    LABELS,
                    sample_rate_hz=SFREQ,
                    window_start_sec=float(start_sec),
                    window_end_sec=float(start_sec + duration_sec),
                    segment_id=segment_id,
                    input_branch=input_branch,
                    support_qc=support_qc,
                )
                value = result.get("value") if result.get("computed") and result.get("valid") else None
                numeric = float(value) if value is not None else None
                measurement_rows.append({
                    "replicate": replicate,
                    "seed": seed,
                    "signal_sha256": signal_hash,
                    "duration_sec": duration_sec,
                    "start_sec": start_sec,
                    "end_sec": start_sec + duration_sec,
                    "sample_start": start_sample,
                    "sample_end_exclusive": end_sample,
                    "window_regime": window_regime(start_sample, end_sample),
                    "sample_count": duration_samples,
                    "channel_count": N_CHANNELS,
                    "candidate": "TP",
                    "truth_target": truth,
                    "value": numeric,
                    "signed_bias": numeric - truth if numeric is not None else None,
                    "absolute_bias": abs(numeric - truth) if numeric is not None else None,
                    "computed": bool(result.get("computed")),
                    "valid": bool(result.get("valid")),
                    "qualified": bool(result.get("qualified")),
                    "reason": result.get("reason"),
                    "window_sha256": sha256_array(window),
                })

    measurements = pd.DataFrame(measurement_rows)
    if len(measurements) != REPLICATES * 13:
        raise ValueError(f"expected {REPLICATES * 13} windows; got {len(measurements)}")
    if not measurements["computed"].all() or not measurements["valid"].all() or measurements["qualified"].any():
        raise ValueError("synthetic TP computation/support/qualification status violated the protocol")
    measurements.to_csv(OUT / "transient_window_measurements.csv", index=False)
    pd.DataFrame(signal_rows).to_json(OUT / "signal_seed_hashes.jsonl", orient="records", lines=True)

    seed_rows: list[dict[str, Any]] = []
    for replicate, seed in enumerate(range(SEED_BASE, SEED_BASE + REPLICATES)):
        current = measurements.loc[measurements["seed"].eq(seed)]
        background = current.loc[(current["duration_sec"].eq(4)) & (current["window_regime"].eq("A")), "value"]
        transient = current.loc[(current["duration_sec"].eq(4)) & (current["window_regime"].eq("B")), "value"]
        full = current.loc[current["duration_sec"].eq(20), "value"]
        if len(background) != 4 or len(transient) != 1 or len(full) != 1:
            raise ValueError(f"unexpected per-seed window support for {seed}")
        background_value = float(background.median())
        transient_value = float(transient.iloc[0])
        full_value = float(full.iloc[0])
        seed_rows.append({
            "replicate": replicate,
            "seed": seed,
            "background_4s_median": background_value,
            "background_truth": 0.8,
            "background_absolute_bias": abs(background_value - 0.8),
            "transient_4s_value": transient_value,
            "transient_truth": 0.2,
            "transient_absolute_bias": abs(transient_value - 0.2),
            "transient_minus_background": transient_value - background_value,
            "full_20s_value": full_value,
            "full_20s_truth": target_tp(0, N_SAMPLES),
            "full_20s_absolute_bias": abs(full_value - target_tp(0, N_SAMPLES)),
        })
    seed_summary = pd.DataFrame(seed_rows)
    seed_summary.to_csv(OUT / "seed_level_transient_summary.csv", index=False)

    screens = {
        "background_4s_median_absolute_bias": float(seed_summary["background_absolute_bias"].median()),
        "transient_4s_median_absolute_bias": float(seed_summary["transient_absolute_bias"].median()),
        "transient_minus_background_median": float(seed_summary["transient_minus_background"].median()),
        "mixed_20s_median_absolute_bias": float(seed_summary["full_20s_absolute_bias"].median()),
    }
    decisions = {
        "background_4s": screens["background_4s_median_absolute_bias"] <= SCREEN_THRESHOLDS["background_4s_median_absolute_bias_max"],
        "transient_4s": screens["transient_4s_median_absolute_bias"] <= SCREEN_THRESHOLDS["transient_4s_median_absolute_bias_max"],
        "transient_detection_direction_and_magnitude": screens["transient_minus_background_median"] <= SCREEN_THRESHOLDS["transient_minus_background_median_max"],
        "20s_mixture": screens["mixed_20s_median_absolute_bias"] <= SCREEN_THRESHOLDS["mixed_20s_median_absolute_bias_max"],
    }

    summary_rows = []
    for (duration, regime), group in measurements.groupby(["duration_sec", "window_regime"], sort=True):
        absolute = group["absolute_bias"].to_numpy(dtype=np.float64)
        signed = group["signed_bias"].to_numpy(dtype=np.float64)
        summary_rows.append({
            "duration_sec": int(duration),
            "window_regime": str(regime),
            "measurement_count": len(group),
            "independent_seed_count": group["seed"].nunique(),
            "median_truth": float(group["truth_target"].median()),
            "median_value": float(group["value"].median()),
            "median_signed_bias": float(np.median(signed)),
            "median_absolute_bias": float(np.median(absolute)),
            "p95_absolute_bias": float(np.quantile(absolute, 0.95)),
        })
    pd.DataFrame(summary_rows).to_csv(OUT / "duration_regime_summary.csv", index=False)

    stationary_path = OUT / "stationary_tp_screen_reuse.csv"
    protocol_hash = sha256_file(PROTOCOL)
    estimator_path = NMD_ROOT / "mndm/src/mndm/mnps/v3_1/pipeline_measurements.py"
    manifest: dict[str, Any] = {
        "schema": "v3_temporal_fidelity_003_run.v1",
        "status": "pass_screens" if all(decisions.values()) else "screens_not_all_passed",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "protocol_path": str(PROTOCOL),
        "protocol_sha256": protocol_hash,
        "estimator_path": str(estimator_path),
        "estimator_sha256": sha256_file(estimator_path),
        "v002_stationary_reference_path": str(V002 / "synthetic_screening_summary.csv"),
        "v002_stationary_reference_sha256": sha256_file(V002 / "synthetic_screening_summary.csv"),
        "stationary_tp_reference_rows": len(stationary),
        "generator": {
            "kind": "piecewise_independent_stationary_AR1_segments",
            "segments": [{"start_sec": a, "end_sec": b, "rho": rho, "regime": name} for a, b, rho, name in SEGMENTS],
            "channel_count": N_CHANNELS,
            "sample_rate_hz": SFREQ,
            "replicates": REPLICATES,
            "seed_base": SEED_BASE,
            "window_durations_sec": list(WINDOW_DURATIONS),
            "window_step_sec": 4,
        },
        "screens": screens,
        "screen_thresholds": SCREEN_THRESHOLDS,
        "screen_decisions": decisions,
        "independent_unit": "signal seed; windows are repeated observations",
        "all_measurements_unqualified": bool(not measurements["qualified"].any()),
        "task_labels_or_classifiers_used": False,
        "claim_ceiling": "bounded synthetic TP estimator screen; not evidence of physiological transient validity",
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": __import__("scipy").__version__,
        },
        "elapsed_seconds": time.perf_counter() - started,
        "outputs_sha256": {},
    }
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.name != "run_manifest.json":
            manifest["outputs_sha256"][path.name] = sha256_file(path)
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    lines = [
        "# V3-TEMPORAL-FIDELITY-003 transient screen results",
        "",
        f"Status: **{manifest['status']}**. Synthetic TP-only experiment; no task labels, classifiers, or biological qualification.",
        "",
        f"The run used {REPLICATES} independent 19-channel, 250 Hz, 20-second signals and {len(measurements)} windows. The frozen V002 stationary TP screen is reused from `{V002 / 'synthetic_screening_summary.csv'}`; it was not rerun.",
        "",
        "## Frozen transient screens",
        "",
        "| Screen | Observed | Threshold | Result |",
        "| --- | ---: | ---: | --- |",
        f"| 4 s background median absolute bias | {screens['background_4s_median_absolute_bias']:.6g} | ≤ {SCREEN_THRESHOLDS['background_4s_median_absolute_bias_max']:.3g} | {'PASS' if decisions['background_4s'] else 'FAIL'} |",
        f"| 4 s transient median absolute bias | {screens['transient_4s_median_absolute_bias']:.6g} | ≤ {SCREEN_THRESHOLDS['transient_4s_median_absolute_bias_max']:.3g} | {'PASS' if decisions['transient_4s'] else 'FAIL'} |",
        f"| 4 s transient minus background median TP | {screens['transient_minus_background_median']:.6g} | ≤ {SCREEN_THRESHOLDS['transient_minus_background_median_max']:.3g} | {'PASS' if decisions['transient_detection_direction_and_magnitude'] else 'FAIL'} |",
        f"| 20 s mixture median absolute bias | {screens['mixed_20s_median_absolute_bias']:.6g} | ≤ {SCREEN_THRESHOLDS['mixed_20s_median_absolute_bias_max']:.3g} | {'PASS' if decisions['20s_mixture'] else 'FAIL'} |",
        "",
        "The signal switches between independent stationary segments (rho 0.2, rho 0.8 transient, rho 0.2); the reset is an intentionally controlled generator, not a physiological model. Mixed 8/12-second results are descriptive. The 20-second value is compared with its generator-defined lag-product mixture, not treated as the truth for the 4-second transient.",
        "",
        "See `transient_window_measurements.csv`, `seed_level_transient_summary.csv`, `duration_regime_summary.csv`, `stationary_tp_screen_reuse.csv`, and `run_manifest.json` for full provenance and observations.",
    ]
    (OUT / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Add the report checksum after writing it, then rewrite the manifest.
    manifest["outputs_sha256"]["results.md"] = sha256_file(OUT / "results.md")
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "output": str(OUT), "screens": screens,
                      "decisions": decisions, "elapsed_seconds": manifest["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
