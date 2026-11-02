"""Exploratory held-out multiscale analysis of NMD window measurements.

Ingest estimators are imported unchanged. Sampling, AR reduction, controls and
prediction belong to this downstream experiment. Run --extract then --analyze.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
from scipy import signal

HERE = Path(__file__).resolve().parent
NMD = Path(r"H:\SourceRepo2\NeuralManifoldDynamics")
PROJECT = NMD / "project/new_mnps_v.3.1"
PROTOCOL = HERE / "vector_integration_001_protocol_v1_20261010.yaml"
OUT = HERE / "outputs/vector_integration_001_20261010"
DATA = Path(r"K:\ExternalReceivedDatasets\openneuro\received\ds005555")
PEOPLE = tuple(f"sub-{i}" for i in range(1, 21))
LABELS = ("PSG_F3", "PSG_F4", "PSG_C3", "PSG_C4", "PSG_O1", "PSG_O2")
FAST_IDS = ("M1", "M2", "E1", "E2")
CONTEXT_IDS = ("M3", "D1", "D3", "E3")
AXES = ("PCV", "TP", "OI", "SC")
EXTENDED = ("AR", "NIE", "RD", "ED")
HISTORY = 24
SEED = 3103201


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def csv_write(path, rows):
    if not rows:
        raise ValueError(f"empty_output:{path}")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def vector(result, ids):
    """Candidate-local unsupported values stay missing; AR is an explicit reduction."""
    by_id = {row["candidate_id"]: row for row in result["measurements"]}
    values = []
    for candidate in ids:
        row = by_id[candidate]
        if not row["computed"] or not row["valid"] or row["value"] is None:
            return None
        value = float(np.median(row["value"])) if candidate == "M3" else float(row["value"])
        if not np.isfinite(value):
            return None
        values.append(value)
    return values


def conventional(data):
    freq, psd = signal.welch(data, fs=256, nperseg=1024, axis=-1)
    total = psd[:, (freq >= 1) & (freq <= 45)].sum(axis=1)
    fractions = [np.median(psd[:, (freq >= lo) & (freq < hi)].sum(axis=1) / total)
                 for lo, hi in ((1, 4), (4, 8), (8, 13), (13, 30))]
    var0, var1, var2 = [np.var(np.diff(data, n=order, axis=-1), axis=-1) for order in (0, 1, 2)]
    mobility = np.sqrt(var1 / var0)
    complexity = np.sqrt(var2 / var1) / mobility
    values = np.asarray(fractions + [np.median(mobility), np.median(complexity)])
    return values.tolist() if np.isfinite(values).all() else None


def feature(extractor, module, filtered, start, end, person):
    return extractor.feature_window(module, filtered, start, end,
                                    source_identity=f"ds005555:{person}:task-Sleep:acq-psg")


def extract():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "extraction_manifest.json").exists():
        raise FileExistsError("extraction_already_saved_use_analyze_or_new_output_root")
    extractor = load("vector_causal_extractor", PROJECT / "run_causal_fast4_001.py")
    # Explicit sensor selection before reading: no silent dropping or Core19 claim.
    original_labels = extractor.LABELS
    prior = json.loads((PROJECT / "outputs/mnj_pred_002_20261010/run_manifest.json").read_text())
    sys.path.insert(0, str(NMD / "mndm/src"))
    from mndm.mnps.v3_1 import pipeline_measurements as module
    fir = signal.firwin(513, [1., 45.], pass_zero=False, fs=256, window="hamming")
    traces, qc, causality = {}, [], {}
    with (OUT / "measurements.jsonl").open("w", encoding="utf-8") as stream:
        for person in PEOPLE:
            edf = DATA / person / "eeg" / f"{person}_task-Sleep_acq-psg_eeg.edf"
            sidecar = edf.with_name(f"{person}_task-Sleep_acq-psg_channels.tsv")
            eeg_json = edf.with_name(f"{person}_task-Sleep_acq-psg_eeg.json")
            metadata = json.loads(eeg_json.read_text(encoding="utf-8"))
            if metadata.get("EEGReference") != "M1 (left mastoid)":
                raise ValueError(f"requested_reference_realization_not_present:{person}")
            extractor.CHANNELS_TSV = sidecar
            header = extractor.parse_edf_header(edf)
            extractor.validate_sidecar(header)
            raw = extractor.read_edf_prefix(edf, header)
            prior_prefix_hash = hashlib.sha256(raw.astype("<f8").tobytes()).hexdigest()
            if prior_prefix_hash != prior["source"]["participant_prefix_signal_hashes"][person]:
                raise ValueError(f"source_prefix_changed_from_prior_pilot:{person}")
            raw = raw[[original_labels.index(label) for label in LABELS]]
            if raw.shape != (6, 160 * 256) or not np.isfinite(raw).all():
                raise ValueError(f"invalid_raw_prefix:{person}")
            filtered = signal.lfilter(fir, [1.], raw, axis=-1)
            extractor.LABELS = LABELS
            fast, context = [], []
            for duration, ends, destination in ((4, range(8, 161, 4), fast),
                                                 (20, range(112, 157, 4), context)):
                for end in ends:
                    start = end - duration
                    result = feature(extractor, module, filtered, start, end, person)
                    result["analysis_realization_id"] = "VECTOR-INTEGRATION-001.SCALP6_CAUSAL_FIR.v1"
                    stream.write(json.dumps({"participant_id": person, "window_sec": duration,
                                             "result": result}, allow_nan=False) + "\n")
                    ids = FAST_IDS if duration == 4 else CONTEXT_IDS
                    destination.append({"start": start, "end": end,
                                        "value": vector(result, ids),
                                        "conventional": conventional(filtered[:, start*256:end*256])})
            traces[person] = {"fast": fast, "context": context}
            with edf.open("rb") as header_stream:
                header_hash = hashlib.sha256(header_stream.read(header["header_bytes"])).hexdigest()
            qc.append({"participant_id": person, "edf_path": str(edf), "edf_bytes": edf.stat().st_size,
                       "header_sha256": header_hash,
                       "prior_eight_signal_prefix_hash_verified": True,
                       "channels_sidecar_sha256": sha(sidecar),
                       "eeg_json_sha256": sha(eeg_json), "recorded_reference": metadata["EEGReference"],
                       "metadata_channel_count": metadata.get("EEGChannelCount"),
                       "raw_scalp6_prefix_sha256": hashlib.sha256(raw.astype("<f8").tobytes()).hexdigest(),
                       "fast_count": len(fast), "fast_complete": sum(r["value"] is not None for r in fast),
                       "context_count": len(context), "context_complete": sum(r["value"] is not None for r in context),
                       "bad_interval_free": "unknown"})
            if person == "sub-1":
                changed = raw.copy()
                rng = np.random.default_rng(SEED)
                changed[:, 120*256:] += rng.normal(0, 150, size=changed[:, 120*256:].shape)
                changed_filtered = signal.lfilter(fir, [1.], changed, axis=-1)
                comparisons = []
                for duration, end in ((4, 120), (20, 120), (20, 104), (4, 124)):
                    ids = FAST_IDS if duration == 4 else CONTEXT_IDS
                    a = vector(feature(extractor, module, filtered, end-duration, end, person), ids)
                    b = vector(feature(extractor, module, changed_filtered, end-duration, end, person), ids)
                    comparisons.append({"duration": duration, "end": end,
                                        "equal": a == b, "base": a, "perturbed": b})
                causality = {"origin_sec": 120,
                             "raw_prefix_equal": bool(np.array_equal(raw[:, :120*256], changed[:, :120*256])),
                             "filtered_prefix_equal": bool(np.array_equal(filtered[:, :120*256], changed_filtered[:, :120*256])),
                             "comparisons": comparisons,
                             "passed": all(r["equal"] for r in comparisons[:3]) and not comparisons[3]["equal"]}
                if not causality["passed"]:
                    raise AssertionError("future_perturbation_failed")
            print(f"extracted {person}: fast={len(fast)}, context={len(context)}", flush=True)
            extractor.LABELS = original_labels
    dump(OUT / "trajectories.json", traces)
    csv_write(OUT / "participant_input_qc.csv", qc)
    dump(OUT / "extraction_manifest.json", {
        "experiment_id": "VECTOR-INTEGRATION-001", "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(__file__),
        "measurement_sources": {str(p.relative_to(NMD)): sha(p) for p in
                                (NMD / "mndm/src/mndm/mnps/v3_1").glob("*.py")},
        "entropy_source_sha256": sha(NMD / "mndm/src/mndm/features/eeg_entropy.py"),
        "extractor_sha256": sha(PROJECT / "run_causal_fast4_001.py"),
        "labels": LABELS, "channel_count": 6,
        "channel_order_sha256": hashlib.sha256("\n".join(s.casefold() for s in LABELS).encode()).hexdigest(),
        "channel_set_sha256": hashlib.sha256("\n".join(sorted(s.casefold() for s in LABELS)).encode()).hexdigest(),
        "fir_sha256": hashlib.sha256(fir.astype("<f8").tobytes()).hexdigest(),
        "reference": "recorded_M1_left_mastoid_no_rereference; verified from all participant EEG JSON sidecars",
        "future_perturbation": causality, "input_qc": qc,
        "software": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "outputs": {name: sha(OUT / name) for name in ("measurements.jsonl", "trajectories.json", "participant_input_qc.csv")}})


def build_rows(traces):
    rows, excluded = [], []
    for person, trace in traces.items():
        fast = trace["fast"]
        context = {row["end"]: row for row in trace["context"]}
        for i, current in enumerate(fast):
            if current["end"] < 128:
                continue
            for horizon in (1, 2):
                if i + horizon >= len(fast):
                    continue
                hist = fast[i-HISTORY+1:i+1]
                correct = context.get(current["end"])
                wrong = context.get(current["end"]-16)
                target = fast[i+horizon]
                reason = None
                future = fast[i+1:i+horizon+1]
                if len(hist) != HISTORY or any(r["value"] is None for r in hist+future):
                    reason = "missing_fast_history_or_target"
                elif any(a["end"] != b["start"] for a,b in zip(hist+future, (hist+future)[1:])) or any(r["end"]-r["start"] != 4 for r in hist+future) or target["end"] != current["end"]+horizon*4:
                    reason = "noncontiguous_time_grid"
                elif not correct or not wrong or any(r["value"] is None for r in (correct, wrong)):
                    reason = "missing_context"
                elif any(r["conventional"] is None for r in hist+[correct]):
                    reason = "missing_conventional_descriptors"
                elif any(r["start"] < hist[0]["start"] or r["end"] > current["end"] or r["end"]-r["start"] != 20 for r in (correct,wrong)):
                    reason = "context_outside_common_history_support"
                if reason:
                    excluded.append({"participant_id": person, "origin_sec": current["end"], "horizon_sec": horizon*4, "reason": reason})
                    continue
                rows.append({"person": person, "origin": current["end"], "horizon": horizon,
                             "history": np.asarray([r["value"] for r in hist]),
                             "context": np.asarray(correct["value"]), "wrong": np.asarray(wrong["value"]),
                             "conventional": np.r_[np.asarray([r["conventional"] for r in hist]).ravel(), correct["conventional"]],
                             "current": np.asarray(current["value"]), "target": np.asarray(target["value"])})
    return rows, excluded


def ridge(x, y, test, alpha=100):
    mx, sx = x.mean(axis=0), x.std(axis=0)
    sx = np.where(sx > 1e-10, sx, 1.)
    my, sy = y.mean(axis=0), y.std(axis=0)
    sy = np.where(sy > 1e-10, sy, 1.)
    z = np.c_[(x-mx)/sx, np.ones(len(x))]
    zt = np.c_[(test-mx)/sx, np.ones(len(test))]
    penalty = np.eye(z.shape[1])*alpha
    penalty[-1,-1] = 0
    coefficient = np.linalg.solve(z.T@z+penalty, z.T@((y-my)/sy))
    return (zt@coefficient)*sy+my


def fit_models(train, test):
    h = np.stack([r["history"] for r in train])
    ht = np.stack([r["history"] for r in test])
    y, yt0 = np.stack([r["target"] for r in train]), np.stack([r["current"] for r in test])
    delta = y - np.stack([r["current"] for r in train])
    x, xt = h.reshape(len(h),-1), ht.reshape(len(ht),-1)
    c, ct = np.stack([r["context"] for r in train]), np.stack([r["context"] for r in test])
    w, wt = np.stack([r["wrong"] for r in train]), np.stack([r["wrong"] for r in test])
    pred = {"A0_persistence": yt0}
    for order in (1,2):
        pred[f"A{order}_AR{order}"] = np.column_stack([
            ridge(h[:,-order:,axis], y[:,axis:axis+1], ht[:,-order:,axis], alpha=1).ravel() for axis in range(4)])
    designs = {"B_fast": (x,xt), "C_fast_extended": (np.c_[x,c], np.c_[xt,ct]),
               "D_wrong_context": (np.c_[x,w],np.c_[xt,wt]),
               "E_conventional": (np.stack([r["conventional"] for r in train]), np.stack([r["conventional"] for r in test]))}
    for axis,name in enumerate(EXTENDED):
        keep = [a for a in range(4) if a != axis]
        designs[f"C_drop_{name}"] = (np.c_[x,c[:,keep]],np.c_[xt,ct[:,keep]])
    for axis,name in enumerate(AXES):
        keep = [a for a in range(4) if a != axis]
        designs[f"B_drop_{name}"] = (h[:,:,keep].reshape(len(h),-1),ht[:,:,keep].reshape(len(ht),-1))
    for name,(design,test_design) in designs.items():
        pred[name] = yt0 + ridge(design,delta,test_design)
    return pred


def rmse(error):
    return float(np.sqrt(np.mean(np.square(error))))


def analyze():
    manifest = json.loads((OUT / "extraction_manifest.json").read_text())
    if manifest["protocol_sha256"] != sha(PROTOCOL):
        raise ValueError("protocol_changed_since_extraction")
    for name,digest in manifest["outputs"].items():
        if sha(OUT/name) != digest:
            raise ValueError(f"input_hash_mismatch:{name}")
    traces = json.loads((OUT / "trajectories.json").read_text())
    rows,excluded = build_rows(traces)
    dump(OUT / "excluded_origins.json", excluded)
    scores, predictions, summaries, contrasts = [], [], [], []
    rng = np.random.default_rng(SEED)
    for horizon in (1,2):
        subset = [r for r in rows if r["horizon"] == horizon]
        people = sorted({r["person"] for r in subset})
        if len(people) < 10:
            raise ValueError("insufficient_participant_coverage")
        errors = {}
        for person in people:
            train = [r for r in subset if r["person"] != person]
            test = [r for r in subset if r["person"] == person]
            truth = np.stack([r["target"] for r in test])
            for model,pred in fit_models(train,test).items():
                error = pred-truth
                errors.setdefault(model,{})[person] = error
                for axis,axis_name in enumerate(AXES):
                    scores.append({"participant_id":person,"horizon_sec":horizon*4,"model":model,
                                   "axis":axis_name,"n_origins":len(test),"rmse":rmse(error[:,axis])})
                for r,t,p in zip(test,truth,pred,strict=True):
                    for axis,axis_name in enumerate(AXES):
                        predictions.append({"participant_id":person,"origin_sec":r["origin"],"horizon_sec":horizon*4,
                                            "model":model,"axis":axis_name,"truth":t[axis],"prediction":p[axis]})
        for model,by_person in errors.items():
            for axis,name in [(-1,"all_raw_units")]+list(enumerate(AXES)):
                selected = {p: e if axis == -1 else e[:,axis] for p,e in by_person.items()}
                summaries.append({"horizon_sec":horizon*4,"model":model,"axis":name,
                                  "n_participants":len(people),"n_origins":len(subset),
                                  "pooled_rmse":rmse(np.concatenate(list(selected.values()),axis=0)),
                                  "participant_macro_rmse":float(np.mean([rmse(e) for e in selected.values()]))})
        comparisons = [(base,"C_fast_extended") for base in
                       ("B_fast","D_wrong_context","A0_persistence","A1_AR1","A2_AR2","E_conventional")]
        comparisons += [(f"C_drop_{name}","C_fast_extended") for name in EXTENDED]
        comparisons += [(f"B_drop_{name}","B_fast") for name in AXES]
        for base,candidate in comparisons:
            for axis,name in [(-1,"all_raw_units")]+list(enumerate(AXES)):
                gains = np.asarray([rmse(errors[base][p] if axis == -1 else errors[base][p][:,axis])-
                                    rmse(errors[candidate][p] if axis == -1 else errors[candidate][p][:,axis]) for p in people])
                means = gains[rng.integers(0,len(gains),size=(5000,len(gains)))].mean(axis=1)
                contrasts.append({"horizon_sec":horizon*4,"baseline":base,"candidate":candidate,"axis":name,
                                  "mean_participant_rmse_gain":float(gains.mean()),"ci95_low":float(np.quantile(means,.025)),
                                  "ci95_high":float(np.quantile(means,.975)),"fraction_participants_improved":float(np.mean(gains>0))})
    csv_write(OUT/"prediction_rows.csv",predictions)
    csv_write(OUT/"participant_axis_rmse.csv",scores)
    csv_write(OUT/"prediction_summary.csv",summaries)
    csv_write(OUT/"paired_contrasts.csv",contrasts)
    main_models = ("A0_persistence","A1_AR1","A2_AR2","B_fast","C_fast_extended","D_wrong_context","E_conventional")
    lines = ["# VECTOR-INTEGRATION-001 results", "", "Exploratory scalp-six causal realization; 20 participants, first 160 s only.", "",
             "| Model | 4 s pooled RMSE | 8 s pooled RMSE |", "|---|---:|---:|"]
    for model in main_models:
        values = [next(r["pooled_rmse"] for r in summaries if r["model"]==model and r["axis"]=="all_raw_units" and r["horizon_sec"]==h) for h in (4,8)]
        lines.append(f"| {model} | {values[0]:.6g} | {values[1]:.6g} |")
    lines += ["", "Raw-unit fast coordinates are dimensionless but differently scaled. Per-axis results are primary for interpreting which measurements benefit; pooled RMSE is descriptive.", "",
              "| Horizon | Contrast (positive favors C) | Mean participant RMSE gain | Bootstrap 95% interval |", "|---|---|---:|---|"]
    for r in contrasts:
        if r["axis"]=="all_raw_units" and r["baseline"] in ("B_fast","D_wrong_context"):
            lines.append(f"| {r['horizon_sec']} s | {r['baseline']} minus C | {r['mean_participant_rmse_gain']:.6g} | [{r['ci95_low']:.6g}, {r['ci95_high']:.6g}] |")
    lines += ["", f"Eligible origins: {sum(r['horizon']==1 for r in rows)} at 4 s and {sum(r['horizon']==2 for r in rows)} at 8 s. Excluded: {len(excluded)}.",
              "", "All context windows and the displaced-context control lie inside the same 96 s span available to B. Scaling is fitted on training participants only. Wrong-time context is a single past displacement, not a shuffled-context test.",
              "", "No stage/event changes, test-retest, full cohort, independent dataset, or biological qualification was evaluated. The six scalp sensors differ from the previous eight-sensor EEG/EOG/EMG pilot. Bad intervals remain unknown; PCV edge fidelity is unqualified. AR is a named median reduction of all nine original changes. The context support is fixed at 20 s, not optimized.",
              "", "The 513-tap FIR adds 2 s left support and 1 s uncompensated group delay. Origin and immediate 4 s target share raw filter support; the 8 s target avoids that immediate overlap. Fast ablations drop that coordinate's history inputs while retaining the current-state persistence anchor for every target.",
              "", "See paired_contrasts.csv for all per-coordinate gains and ablations, and measurements.jsonl for full estimator, support, reference and sensor provenance."]
    (OUT/"results.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    dump(OUT/"analysis_manifest.json",{
        "experiment_id":"VECTOR-INTEGRATION-001","status":"completed_bounded_exploratory_pilot",
        "created_utc":datetime.now(timezone.utc).isoformat(),"runner_sha256":sha(__file__),"protocol_sha256":sha(PROTOCOL),
        "extraction_manifest_sha256":sha(OUT/"extraction_manifest.json"),"folds":"leave_one_participant_out",
        "ridge_alpha":100,"seed":SEED,"n_participants":len(traces),"n_origins":len(rows),"excluded":excluded,
        "outputs":{name:sha(OUT/name) for name in ("prediction_rows.csv","participant_axis_rmse.csv","prediction_summary.csv","paired_contrasts.csv","excluded_origins.json","results.md")}})
    print("\n".join(lines[:14]),flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract",action="store_true")
    parser.add_argument("--analyze",action="store_true")
    args = parser.parse_args()
    if not args.extract and not args.analyze:
        parser.error("choose --extract and/or --analyze")
    if args.extract:
        extract()
    if args.analyze:
        analyze()
