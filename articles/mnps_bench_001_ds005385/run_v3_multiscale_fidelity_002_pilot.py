from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import signal

NMD_ROOT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics")
ARTICLE = Path(r"J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385")
PROTOCOL = ARTICLE / "v3_multiscale_fidelity_002_protocol_v1_20261009.md"
OUT = ARTICLE / "outputs" / "v3_multiscale_fidelity_002_pilot_v1_20261009"
sys.path.insert(0, str(NMD_ROOT / "mndm" / "src"))
from mndm.mnps.v3_1.pipeline_measurements import compute_pipeline_window_measurements
from mndm.mnps.v3_1.realizations import CORE19_CHANNELS

BASE_SEED = 20261009
SFREQ = 250.0
N_CH = 19
N_20 = 20 * int(SFREQ)
DURATIONS = (4, 8, 12, 20)
PANELS = (
    ("TP_rho_0.2", "TP", 0.2),
    ("TP_rho_0.8", "TP", 0.8),
    ("PCV_phase_order", "PCV", None),
    ("AR_block_activity", "AR", None),
    ("ED_covariance", "ED", None),
)
SHORT = {"M1": "PCV", "M2": "TP", "M3": "AR", "D1": "NIE",
         "D3": "RD", "E1": "OI", "E2": "SC", "E3": "ED"}
FAST_IDS = ("M1", "M2", "E1", "E2")
N_SURROGATE = 200
N_WINDOWS = 40
N_PERMUTATIONS = 999
ALPHA = 0.05


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def byte_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def enc(value: Any) -> str:
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


def init_out() -> None:
    if not PROTOCOL.is_file():
        raise FileNotFoundError(PROTOCOL)
    OUT.mkdir(parents=True, exist_ok=True)


def make_ar1(rng: np.random.Generator, rho: float, n: int) -> np.ndarray:
    eps = rng.normal(size=(N_CH, n))
    initial = rng.normal(size=(N_CH, 1))
    values, _ = signal.lfilter(
        [math.sqrt(1.0 - rho * rho)], [1.0, -rho], eps, axis=-1,
        zi=rho * initial,
    )
    return np.asarray(values, dtype=np.float64)


def make_pcv(rng: np.random.Generator) -> tuple[np.ndarray, dict[int, float], dict[str, Any]]:
    t = np.arange(N_20, dtype=np.float64) / SFREQ
    base = rng.uniform(-math.pi, math.pi, N_CH)
    shift = rng.uniform(-math.pi, math.pi, N_CH)
    phase = (2 * math.pi * 10 * t[None, :] + base[:, None]
             + 0.5 * np.sin(2 * math.pi * 0.25 * t[None, :] + shift[:, None]))
    z = np.exp(1j * phase)
    referenced_z = z - z.mean(axis=0, keepdims=True)
    order = np.abs(np.mean(
        referenced_z / np.maximum(np.abs(referenced_z), np.finfo(float).tiny), axis=0
    ))
    truth = {d: float(np.std(order[:d * int(SFREQ)], ddof=0)) for d in DURATIONS}
    return referenced_z.real.astype(np.float64), truth, {
        "carrier_hz": 10.0, "phase_modulation_amplitude_rad": 0.5,
        "phase_modulation_hz": 0.25, "equal_channel_amplitude": True,
        "reference": "instantaneous_average_over_19_channels",
        "truth": "phase order of the exact referenced complex generator",
    }


def make_ar(rng: np.random.Generator) -> tuple[np.ndarray, dict[int, list[float]], dict[str, Any]]:
    blocks = N_20 // int(2 * SFREQ)
    amp = np.exp(rng.normal(0.0, 0.45, size=(blocks, N_CH)))
    phase = rng.uniform(-math.pi, math.pi, N_CH)
    sample = np.arange(N_20)
    x = amp[sample // int(2 * SFREQ)].T * np.cos(
        2 * math.pi * 10 * sample[None, :] / SFREQ + phase[:, None]
    )
    truth: dict[int, list[float]] = {}
    block_samples = int(2 * SFREQ)
    for duration in DURATIONS:
        count = duration // 2
        activity = np.sqrt(np.mean(
            x[:, :duration * int(SFREQ)].reshape(N_CH, count, block_samples) ** 2, axis=2
        )).T
        changes = []
        for left, right in zip(activity[:-1], activity[1:], strict=True):
            l = left / np.max(np.abs(left))
            r = right / np.max(np.abs(right))
            l = l - np.mean(l)
            r = r - np.mean(r)
            changes.append(1.0 - float(np.dot(l, r) / (np.linalg.norm(l) * np.linalg.norm(r))))
        truth[duration] = changes
    return x.astype(np.float64), truth, {
        "carrier_hz": 10, "block_duration_sec": 2,
        "amplitudes": "lognormal by channel and block",
        "truth": "1 minus Pearson r of exact channel RMS block vectors",
    }


def make_ed(rng: np.random.Generator) -> tuple[np.ndarray, float, dict[str, Any]]:
    eigenvalues = np.geomspace(2.5, 0.35, N_CH)
    q, _ = np.linalg.qr(rng.normal(size=(N_CH, N_CH)))
    covariance = q @ np.diag(eigenvalues) @ q.T
    x = q @ np.diag(np.sqrt(eigenvalues)) @ rng.normal(size=(N_CH, N_20))
    target = float(np.sum(eigenvalues) ** 2 / np.sum(eigenvalues ** 2))
    return x.astype(np.float64), target, {
        "population_eigenvalues": eigenvalues.tolist(),
        "population_participation_ratio": target,
        "covariance_sha256": byte_hash(np.ascontiguousarray(covariance).tobytes()),
    }


def generate(panel_type: str, parameter: float | None,
             rng: np.random.Generator) -> tuple[np.ndarray, dict[int, Any], dict[str, Any]]:
    if panel_type == "TP":
        return make_ar1(rng, float(parameter), N_20), {
            d: 1.0 - float(parameter) for d in DURATIONS
        }, {"rho": float(parameter), "variance": 1.0, "independent_channels": True}
    if panel_type == "PCV":
        return make_pcv(rng)
    if panel_type == "AR":
        return make_ar(rng)
    if panel_type == "ED":
        x, target, params = make_ed(rng)
        return x, {d: target for d in DURATIONS}, params
    raise ValueError(panel_type)


def compute(x: np.ndarray, panel: str, replicate: int, duration: int,
            average_reference: bool) -> dict[str, dict[str, Any]]:
    n = duration * int(SFREQ)
    labels = tuple(CORE19_CHANNELS)
    branch = {
        "branch_id": "v3_multiscale_fidelity_002_synthetic_v1",
        "reference_mode": "average_over_surface" if average_reference else "none",
        "reference_set_sha256": (
            byte_hash("\n".join(sorted(s.casefold() for s in labels)).encode())
            if average_reference else None
        ),
        "filter_band_hz": None,
    }
    qc = {
        "source_is_continuous": True, "timestamps_uniform": True,
        "input_samples_finite": bool(np.isfinite(x[:, :n]).all()), "gap_free": True,
        "bad_interval_free": None, "within_recording_bounds": True,
        "effective_filter_support_valid": None,
        "effective_filter_support_status": "synthetic generator; no acquisition filter applied",
    }
    result = compute_pipeline_window_measurements(
        x[:, :n], labels, sample_rate_hz=SFREQ, window_start_sec=0.0,
        window_end_sec=float(duration),
        segment_id=f"{panel}_seed_{BASE_SEED + replicate}",
        source_identity="v3_multiscale_fidelity_002_synthetic",
        input_branch=branch, support_qc=qc,
        sequence_complexity_reference_count=32, activity_block_sec=2.0,
    )
    if result.get("status") != "computed":
        raise RuntimeError(f"not computed: {panel}/{replicate}/{duration}")
    return {str(r["candidate_id"]): r for r in result["measurements"]}


def pcv_full_context(x: np.ndarray, duration: int) -> float:
    sos = signal.butter(4, [8.0, 13.0], btype="bandpass", fs=SFREQ, output="sos")
    filtered = signal.sosfiltfilt(sos, x, axis=-1, padtype=None, padlen=0)
    analytic = signal.hilbert(filtered, axis=-1)[:, :duration * int(SFREQ)]
    amp = np.abs(analytic)
    if not np.isfinite(amp).all() or np.any(amp == 0):
        return math.nan
    order = np.abs(np.mean(analytic / amp, axis=0))
    return float(np.std(order, ddof=0))


def run_synthetic() -> None:
    init_out()
    destinations = [OUT / "synthetic_seed_measurements.csv",
                    OUT / "synthetic_seed_truth_and_input_hashes.jsonl",
                    OUT / "synthetic_screening_summary.csv"]
    if any(p.exists() for p in destinations):
        raise FileExistsError("synthetic output exists; refusing to overwrite")
    progress_csv = OUT / "synthetic_progress.csv"
    progress_jsonl = OUT / "synthetic_progress_seed_truth.jsonl"
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    seeds: list[str] = []
    completed_keys: set[tuple[str, int]] = set()
    if progress_csv.is_file():
        previous = pd.read_csv(progress_csv, keep_default_na=False)
        rows = previous.to_dict(orient="records")
        completed_keys = {
            (str(panel), int(replicate))
            for panel, replicate in previous[["panel", "replicate"]].drop_duplicates().itertuples(index=False, name=None)
        }
    if progress_jsonl.is_file():
        seeds = [line for line in progress_jsonl.read_text(encoding="utf-8").splitlines() if line]
    completed = len(completed_keys)
    for pidx, (panel, kind, parameter) in enumerate(PANELS):
        for replicate in range(100):
            if (panel, replicate) in completed_keys:
                continue
            seed = BASE_SEED + replicate
            rng = np.random.default_rng(np.random.SeedSequence([seed, pidx]))
            x, truth_by_duration, params = generate(kind, parameter, rng)
            digest = byte_hash(np.ascontiguousarray(x).tobytes())
            seeds.append(json.dumps({
                "panel": panel, "panel_type": kind, "replicate": replicate, "seed": seed,
                "panel_stream_index": pidx, "generator_parameters": params,
                "truth_by_duration": truth_by_duration, "signal_sha256": digest,
            }, ensure_ascii=False, separators=(",", ":"), allow_nan=False))
            average_reference = kind == "PCV"
            by_duration = {
                d: compute(x, panel, replicate, d, average_reference) for d in DURATIONS
            }
            full_context = {
                d: pcv_full_context(x, d) for d in DURATIONS
            } if kind == "PCV" else {}
            for duration in DURATIONS:
                truth = truth_by_duration[duration]
                for cid, result in by_duration[duration].items():
                    value = result.get("value") if result.get("computed") else None
                    is_target = (
                        (kind == "TP" and cid == "M2")
                        or (kind == "PCV" and cid == "M1")
                        or (kind == "AR" and cid == "M3")
                        or (kind == "ED" and cid == "E3")
                    )
                    target = truth if is_target else None
                    delta: Any = None
                    abs_delta: Any = None
                    rel_abs_delta = None
                    if target is not None and value is not None:
                        d = np.asarray(value, dtype=float) - np.asarray(target, dtype=float)
                        delta = float(d) if d.ndim == 0 else d.tolist()
                        a = np.abs(d)
                        abs_delta = float(a) if a.ndim == 0 else a.tolist()
                        if kind == "ED":
                            rel_abs_delta = float(abs(float(d)) / abs(float(target)))
                    ref20 = by_duration[20][cid].get("value")
                    if cid == "M3" and value is not None and ref20 is not None:
                        ref20 = np.asarray(ref20, dtype=np.float64)[:len(np.asarray(value).reshape(-1))].tolist()
                    diff20: Any = None
                    if value is not None and ref20 is not None:
                        d20 = np.asarray(value, dtype=float) - np.asarray(ref20, dtype=float)
                        diff20 = float(d20) if d20.ndim == 0 else d20.tolist()
                    rows.append({
                        "panel": panel, "panel_type": kind, "parameter": parameter,
                        "replicate": replicate, "seed": seed, "signal_sha256": digest,
                        "duration_sec": duration, "candidate_id": cid,
                        "candidate": SHORT[cid], "computed": bool(result.get("computed")),
                        "valid": bool(result.get("valid")), "qualified": bool(result.get("qualified")),
                        "value_json": enc(value) if value is not None else "",
                        "target_kind": "known_generator_truth" if target is not None
                                       else "long_20s_comparator_only",
                        "target_json": enc(target) if target is not None else "",
                        "signed_bias_json": enc(delta) if delta is not None else "",
                        "absolute_bias_json": enc(abs_delta) if abs_delta is not None else "",
                        "relative_absolute_bias": rel_abs_delta,
                        "comparator_20s_json": enc(ref20) if ref20 is not None else "",
                        "difference_from_20s_json": enc(diff20) if diff20 is not None else "",
                        "full_context_filtered_pcv": full_context.get(duration),
                        "local_minus_full_context_pcv": (
                            float(value) - full_context[duration]
                            if kind == "PCV" and cid == "M1" and value is not None else None
                        ),
                        "status": result.get("status"), "reason": result.get("reason"),
                    })
            completed += 1
            if completed % 10 == 0:
                atomic_csv(pd.DataFrame(rows), progress_csv)
                atomic_text("\n".join(seeds) + "\n", progress_jsonl)
                print(f"[synthetic] {completed}/500 seeds; elapsed={time.perf_counter()-started:.1f}s", flush=True)

    frame = pd.DataFrame(rows)
    atomic_csv(frame, destinations[0])
    atomic_text("\n".join(seeds) + "\n", destinations[1])
    summary: list[dict[str, Any]] = []
    known = frame.loc[frame["target_kind"].eq("known_generator_truth")]
    for (panel, candidate, duration), group in known.groupby(["panel", "candidate", "duration_sec"]):
        signed: list[float] = []
        absolute: list[float] = []
        relative: list[float] = []
        maximum = 0.0
        for _, item in group.iterrows():
            b = json.loads(item["signed_bias_json"])
            a = json.loads(item["absolute_bias_json"])
            if isinstance(b, list):
                signed.extend(map(float, b))
                absolute.extend(map(float, a))
                maximum = max(maximum, max(map(float, a), default=0.0))
            else:
                signed.append(float(b))
                absolute.append(float(a))
            if pd.notna(item["relative_absolute_bias"]):
                relative.append(float(item["relative_absolute_bias"]))
        median_bias = float(np.median(signed))
        median_abs = float(np.median(absolute))
        p95_abs = float(np.quantile(absolute, 0.95))
        threshold: float | str | None = None
        passed: bool | None = None
        if panel.startswith("TP_"):
            threshold = 0.10 if duration == 4 else 0.05
            passed = abs(median_bias) <= threshold
        elif panel == "PCV_phase_order":
            threshold = 0.05
            passed = abs(median_bias) <= threshold
        elif panel == "AR_block_activity":
            threshold = 1e-12
            passed = maximum <= threshold
        elif panel == "ED_covariance":
            threshold = 0.30 if duration == 4 else 0.20
            passed = float(np.median(relative)) <= threshold
        summary.append({
            "panel": panel, "candidate": candidate, "duration_sec": duration,
            "replicate_count": int(group["replicate"].nunique()),
            "median_signed_bias": median_bias, "median_absolute_bias": median_abs,
            "p95_absolute_bias": p95_abs, "maximum_absolute_component_error": maximum,
            "median_relative_absolute_bias": float(np.median(relative)) if relative else None,
            "screen_threshold": threshold,
            "screen_decision": ("pass_screen" if passed else "fail_screen")
                               if passed is not None else "descriptive_only",
        })
    pcv = frame.loc[frame["panel"].eq("PCV_phase_order") & frame["candidate"].eq("PCV")]
    for duration, group in pcv.groupby("duration_sec"):
        differences = pd.to_numeric(group["local_minus_full_context_pcv"], errors="coerce").dropna().to_numpy()
        med = float(np.median(np.abs(differences)))
        p95 = float(np.quantile(np.abs(differences), 0.95))
        summary.append({
            "panel": "PCV_local_vs_full_context", "candidate": "PCV",
            "duration_sec": int(duration), "replicate_count": len(differences),
            "median_signed_bias": float(np.median(differences)),
            "median_absolute_bias": med, "p95_absolute_bias": p95,
            "maximum_absolute_component_error": float(np.max(np.abs(differences))),
            "median_relative_absolute_bias": None,
            "screen_threshold": "median<=0.05,p95<=0.10",
            "screen_decision": "pass_screen" if med <= 0.05 and p95 <= 0.10 else "fail_screen",
        })
    atomic_csv(pd.DataFrame(summary), destinations[2])
    progress_csv.unlink(missing_ok=True)
    progress_jsonl.unlink(missing_ok=True)
    print(f"[synthetic] complete; rows={len(frame)}; elapsed={time.perf_counter()-started:.1f}s", flush=True)
    update_manifest("synthetic")


def holm(p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.argsort(p)
    adjusted = np.ones_like(p)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(p) - rank) * float(p[index])))
        adjusted[index] = running
    return adjusted, adjusted <= ALPHA


def run_surrogate() -> None:
    init_out()
    if not (OUT / "synthetic_seed_measurements.csv").is_file():
        raise FileNotFoundError("run the synthetic stage first")
    paths = [OUT / "stationary_surrogate_windows.csv",
             OUT / "stationary_surrogate_test_results.csv",
             OUT / "stationary_surrogate_summary.csv"]
    if any(path.exists() for path in paths):
        raise FileExistsError("surrogate output exists; refusing to overwrite")
    started = time.perf_counter()
    labels = tuple(CORE19_CHANNELS)
    branch = {"branch_id": "v3_multiscale_fidelity_002_surrogate_v1",
              "reference_mode": "none", "reference_set_sha256": None, "filter_band_hz": None}
    qc = {"source_is_continuous": True, "timestamps_uniform": True,
          "input_samples_finite": True, "gap_free": True, "bad_interval_free": None,
          "within_recording_bounds": True, "effective_filter_support_valid": None,
          "effective_filter_support_status": "generated stationary windows"}
    windows: list[dict[str, Any]] = []
    tests: list[dict[str, Any]] = []
    family_rejects = 0
    for dataset in range(N_SURROGATE):
        seed = BASE_SEED + dataset
        rng = np.random.default_rng(seed)
        vals = np.empty((N_WINDOWS, len(FAST_IDS)), dtype=float)
        for wi in range(N_WINDOWS):
            window_seed = int(rng.integers(0, 2**32, dtype=np.uint32))
            x = make_ar1(np.random.default_rng(window_seed), 0.50, 4 * int(SFREQ))
            digest = byte_hash(np.ascontiguousarray(x).tobytes())
            result = compute_pipeline_window_measurements(
                x, labels, sample_rate_hz=SFREQ, window_start_sec=0.0, window_end_sec=4.0,
                segment_id=f"surrogate_{dataset:03d}_{wi:02d}",
                source_identity="v3_multiscale_fidelity_002_stationary_surrogate",
                input_branch=branch, support_qc=qc, sequence_complexity_reference_count=32,
                activity_block_sec=2.0,
            )
            rows = {str(r["candidate_id"]): r for r in result["measurements"]}
            for ci, cid in enumerate(FAST_IDS):
                row = rows[cid]
                if not row.get("computed") or not math.isfinite(float(row["value"])):
                    raise RuntimeError(f"unsupported surrogate {dataset}/{wi}/{cid}")
                vals[wi, ci] = float(row["value"])
                windows.append({
                    "dataset_index": dataset, "dataset_seed": seed, "window_index": wi,
                    "window_seed": window_seed, "signal_sha256": digest, "candidate_id": cid,
                    "candidate": SHORT[cid], "value": float(row["value"]),
                    "computed": bool(row["computed"]), "valid": bool(row["valid"]),
                    "qualified": bool(row["qualified"]),
                })
        assignment = rng.permutation(np.repeat([0, 1], N_WINDOWS // 2))
        a, b = assignment == 0, assignment == 1
        observed = vals[a].mean(axis=0) - vals[b].mean(axis=0)
        prng = np.random.default_rng(np.random.SeedSequence([seed, 991]))
        perms = np.asarray([prng.permutation(N_WINDOWS) for _ in range(N_PERMUTATIONS)], dtype=np.int16)
        permstat = (
            vals[perms[:, :N_WINDOWS // 2]].mean(axis=1)
            - vals[perms[:, N_WINDOWS // 2:]].mean(axis=1)
        )
        p = (1 + np.sum(np.abs(permstat) >= np.abs(observed)[None, :], axis=0)) / (N_PERMUTATIONS + 1)
        adjusted, reject = holm(p)
        family_rejects += int(np.any(reject))
        for ci, cid in enumerate(FAST_IDS):
            tests.append({
                "dataset_index": dataset, "dataset_seed": seed, "candidate_id": cid,
                "candidate": SHORT[cid], "observed_difference": float(observed[ci]),
                "permutation_p_two_sided": float(p[ci]), "holm_adjusted_p": float(adjusted[ci]),
                "holm_reject_alpha_0_05": bool(reject[ci]), "permutation_count": N_PERMUTATIONS,
                "windows_per_label": N_WINDOWS // 2,
            })
        if (dataset + 1) % 10 == 0:
            print(f"[surrogate] {dataset+1}/{N_SURROGATE}; elapsed={time.perf_counter()-started:.1f}s", flush=True)
    win_df = pd.DataFrame(windows)
    test_df = pd.DataFrame(tests)
    summary = [{
        "candidate": name, "dataset_count": N_SURROGATE,
        "raw_rejection_rate": float((group["permutation_p_two_sided"] <= ALPHA).mean()),
        "holm_rejection_rate": float(group["holm_reject_alpha_0_05"].mean()),
        "raw_rejection_count": int((group["permutation_p_two_sided"] <= ALPHA).sum()),
        "holm_rejection_count": int(group["holm_reject_alpha_0_05"].sum()),
    } for name, group in test_df.groupby("candidate")]
    summary.append({
        "candidate": "familywise_any_of_four", "dataset_count": N_SURROGATE,
        "raw_rejection_rate": None, "holm_rejection_rate": family_rejects / N_SURROGATE,
        "raw_rejection_count": None, "holm_rejection_count": family_rejects,
    })
    atomic_csv(win_df, paths[0])
    atomic_csv(test_df, paths[1])
    atomic_csv(pd.DataFrame(summary), paths[2])
    print(f"[surrogate] complete; windows={len(win_df)}; familywise rate={family_rejects/N_SURROGATE:.3f}; elapsed={time.perf_counter()-started:.1f}s", flush=True)
    update_manifest("surrogate")


def update_manifest(stage: str) -> None:
    path = OUT / "run_manifest.json"
    previous = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    protocol_hash = file_hash(PROTOCOL)
    if previous and previous.get("protocol_sha256") != protocol_hash:
        raise ValueError("protocol hash differs from existing output manifest")
    pipeline = NMD_ROOT / "mndm/src/mndm/mnps/v3_1/pipeline_measurements.py"
    realizations = NMD_ROOT / "mndm/src/mndm/mnps/v3_1/realizations.py"
    script = Path(__file__).resolve()
    outputs = {
        p.name: {"bytes": p.stat().st_size, "sha256": file_hash(p)}
        for p in sorted(OUT.iterdir())
        if p.is_file() and p.name != "run_manifest.json" and not p.name.endswith(".tmp")
    }
    stages = dict(previous.get("stages", {}))
    stages[stage] = {"status": "complete", "completed_utc": datetime.now(timezone.utc).isoformat()}
    manifest = {
        "schema": "mndm.v3_multiscale_fidelity_002_pilot_manifest.v1",
        "status": "partial_protocol_stages_pending",
        "created_utc": previous.get("created_utc", datetime.now(timezone.utc).isoformat()),
        "dataset": "OpenNeuro ds003838 v1.0.6; six frozen V001 participants",
        "participants": ["sub-032", "sub-033", "sub-034", "sub-035", "sub-036", "sub-038"],
        "durations_sec": list(DURATIONS), "synthetic_seed_list": list(range(BASE_SEED, BASE_SEED + 100)),
        "synthetic_panels": [p[0] for p in PANELS],
        "surrogate_datasets": N_SURROGATE,
        "surrogate_windows_per_dataset": N_WINDOWS, "permutation_count": N_PERMUTATIONS,
        "continuous_empirical_stage": "not_run",
        "protocol_path": str(PROTOCOL), "protocol_sha256": protocol_hash,
        "runner_path": str(script), "runner_sha256": file_hash(script),
        "pipeline_path": str(pipeline), "pipeline_sha256": file_hash(pipeline),
        "realizations_path": str(realizations), "realizations_sha256": file_hash(realizations),
        "stages": stages, "claim_ceiling": "bounded method screening; no qualification, equivalence, task contrast, classifier, or full-cohort authorization",
        "outputs": outputs,
    }
    atomic_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("synthetic", "surrogate"), required=True)
    stage = parser.parse_args().stage
    run_synthetic() if stage == "synthetic" else run_surrogate()
