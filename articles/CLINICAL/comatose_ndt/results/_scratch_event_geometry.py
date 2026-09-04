"""Endogenous-perturbation geometry vs run-level median (CPC1 vs CPC5).

Detect spontaneous transients in the MNPS speed trace (within-run robust z),
then compute geometry CONDITIONED on event vs quiescent windows, plus a
reactivity/recovery proxy. Compare per-subject AUC against the run-median.
"""
import glob
import numpy as np
import h5py
from sklearn.metrics import roc_auc_score

DIRS = [
    r"data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260601_131927_part1_combat",
    r"data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260601_143502_part2_combat",
]
N_PER_GROUP = 55
RUNS_PER_SUBJ = 4
Z_EVENT = 3.0

def collect():
    by_subj = {}  # subj -> dict(cpc, files[])
    for d in DIRS:
        for f in sorted(glob.glob(d + "/**/*.h5", recursive=True)):
            subj = f.split("sub-")[1][:4]
            by_subj.setdefault(subj, {"files": []})
            by_subj[subj]["files"].append(f)
    return by_subj

def run_features(f):
    with h5py.File(f, "r") as h:
        dot = h["/mnps_3d_dot"][:]
        J = h["/jacobian/J_hat"][:]
        cpc = int(h.attrs.get("meta_cpc", -1))
    speed = np.linalg.norm(dot, axis=1)
    if len(speed) < 60:
        return None
    spec = np.abs(np.linalg.eigvals(J)).max(axis=1)
    n = min(len(speed), len(spec))                         # align lengths
    speed = speed[:n]; spec = spec[:n]
    med = np.median(speed); mad = np.median(np.abs(speed - med)) * 1.4826 + 1e-9
    z = (speed - med) / mad
    ev = z > Z_EVENT
    quiet = ~ev
    feats = {
        "cpc": cpc,
        "median_speed": float(np.median(speed)),
        "median_spec": float(np.median(spec)),                       # run-level baseline metric
        "spec_p95": float(np.percentile(spec, 95)),                  # tail of local expansion
        "spec_p99": float(np.percentile(spec, 99)),
        "spec_iqr": float(np.subtract(*np.percentile(spec, [75, 25]))),
        "spec_range_ratio": float(np.percentile(spec, 95) / (np.median(spec) + 1e-9)),  # dynamic range
        "speed_p95": float(np.percentile(speed, 95)),
        "speed_iqr": float(np.subtract(*np.percentile(speed, [75, 25]))),
        "event_rate_per_min": float(ev.mean() * (60 / 4)),            # events per minute
        "event_amp": float(z[ev].mean()) if ev.any() else 0.0,        # mean transient amplitude
        "spec_during_event": float(np.median(spec[ev])) if ev.any() else np.nan,
        "spec_during_quiet": float(np.median(spec[quiet])) if quiet.any() else np.nan,
        "burst_kurtosis": float(((speed - speed.mean())**4).mean()/(speed.std()**4 + 1e-9)),
    }
    # reactivity/recovery: median windows for speed to fall back below baseline after an event
    rec = []
    idx = np.where(ev)[0]
    for i in idx:
        for k in range(1, 15):
            if i + k >= len(z): break
            if z[i + k] < 1.0:
                rec.append(k); break
    feats["recovery_windows"] = float(np.median(rec)) if rec else np.nan
    # explosive gain: how much more the Jacobian expands during events vs quiet
    if ev.any() and quiet.any():
        feats["event_explosive_gain"] = feats["spec_during_event"] - feats["spec_during_quiet"]
    else:
        feats["event_explosive_gain"] = np.nan
    return feats

by_subj = collect()
rows = []
seen1 = seen5 = 0
for subj, info in by_subj.items():
    # peek cpc from first file
    try:
        with h5py.File(info["files"][0], "r") as h:
            cpc = int(h.attrs.get("meta_cpc", -1))
    except Exception:
        continue
    if cpc == 1 and seen1 >= N_PER_GROUP: continue
    if cpc == 5 and seen5 >= N_PER_GROUP: continue
    if cpc not in (1, 5): continue
    fr = [run_features(f) for f in info["files"][:RUNS_PER_SUBJ]]
    fr = [x for x in fr if x is not None]
    if not fr: continue
    agg = {"subj": subj, "cpc": cpc}
    for k in fr[0]:
        if k == "cpc": continue
        vals = [x[k] for x in fr if np.isfinite(x[k])]
        agg[k] = float(np.median(vals)) if vals else np.nan
    rows.append(agg)
    if cpc == 1: seen1 += 1
    else: seen5 += 1

import pandas as pd
df = pd.DataFrame(rows)
print(f"subjects: CPC1={ (df.cpc==1).sum() }  CPC5={ (df.cpc==5).sum() }")
y = (df["cpc"] == 5).astype(int).values
print("\nmetric                     AUC   CPC1_med   CPC5_med")
for c in ["median_spec", "median_speed", "spec_p95", "spec_p99", "spec_iqr",
          "spec_range_ratio", "speed_p95", "speed_iqr",
          "event_rate_per_min", "event_amp",
          "spec_during_event", "spec_during_quiet", "event_explosive_gain",
          "recovery_windows", "burst_kurtosis"]:
    v = df[c].values
    m = np.isfinite(v)
    if m.sum() < 40: 
        print(f"{c:26s}  (insufficient finite: {m.sum()})"); continue
    a = roc_auc_score(y[m], v[m]); a = max(a, 1 - a)
    print(f"{c:26s} {a:.3f}   {np.nanmedian(df[df.cpc==1][c]):+.3f}   {np.nanmedian(df[df.cpc==5][c]):+.3f}")
df.to_csv(r"articles/CLINICAL/comatose_ndt/results/_scratch_event_features.csv", index=False)
