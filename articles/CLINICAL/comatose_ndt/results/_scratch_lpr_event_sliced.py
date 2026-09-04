"""Event-Sliced NDT / Latent Perturbation Reactivity (LPR) - first real test.

Per the colleague's spec:
  1. event score E_t = robust(dMNPS) + robust(dlog raw_features) + eta*robust(dJ)
     (use log-raw features + MNPS + Jacobian, NOT features_robust_z)
  2. cluster supra-threshold windows into episodes (allow small gaps)
  3. per episode: baseline(pre) / peak / post -> amplitude, recovery_half_time,
     residual, hysteresis-ish
  4. aggregate per subject; compare CPC1 vs CPC5 AUC to the run-median baseline.

Robustness: require multi-region support (>=2 regional speeds elevated) to
reduce single-region artifact events.
"""
import glob
import numpy as np
import h5py
import pandas as pd
from sklearn.metrics import roc_auc_score

DIRS = [
    r"data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260601_131927_part1_combat",
    r"data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260601_143502_part2_combat",
]
N_PER_GROUP = 200
RUNS_PER_SUBJ = 60
ETA_J = 0.5
Z_THRESH = 3.0
GAP = 1            # merge episodes separated by <=1 window
PRE = 4            # baseline windows before episode
POST = 6           # post windows after episode for residual/recovery
REGIONS = ["frontal", "central", "parietal_occipital", "temporal"]

def robust_z(x):
    x = np.asarray(x, float)
    med = np.median(x); mad = np.median(np.abs(x - med)) * 1.4826 + 1e-9
    return (x - med) / mad

def spec_radius(J):
    return np.abs(np.linalg.eigvals(J)).max(axis=1)

def run_lpr(f):
    with h5py.File(f, "r") as h:
        mnps = h["/mnps_3d"][:]
        raw = h["/features_raw/values"][:]
        J = h["/jacobian/J_hat"][:]
        cpc = int(h.attrs.get("meta_cpc", -1))
        reg_speed = []
        for r in REGIONS:
            key = f"/regional_mnps/{r}/mnps_dot"
            if key in h:
                reg_speed.append(np.linalg.norm(h[key][:], axis=1))
    T = len(mnps)
    if T < 80:
        return None
    # change signals (length T-1, indexed at t for transition t-1->t)
    dM = np.linalg.norm(np.diff(mnps, axis=0), axis=1)
    rawpos = np.log(np.abs(raw) + 1e-6)
    dF = np.linalg.norm(np.diff(rawpos, axis=0), axis=1)
    spec = spec_radius(J)
    n = min(len(dM), len(dF), len(spec) - 0 if len(spec) else 0)
    spec_al = spec[:min(len(spec), T)]
    dJ = np.abs(np.diff(spec_al))
    L = min(len(dM), len(dF), len(dJ))
    dM, dF, dJ = dM[:L], dF[:L], dJ[:L]
    E = robust_z(dM) + robust_z(dF) + ETA_J * robust_z(dJ)
    # multi-region support
    if reg_speed:
        rs = np.column_stack([robust_z(np.diff(s))[:L] for s in reg_speed if len(s) > L])
        support = (rs > 1.5).sum(axis=1) if rs.size else np.full(L, 2)
    else:
        support = np.full(L, 2)
    is_ev = (E > Z_THRESH) & (support >= 2)
    # cluster into episodes (merge gaps <= GAP)
    episodes = []
    t = 0
    idx = np.where(is_ev)[0]
    if len(idx) == 0:
        return dict(cpc=cpc, n_episodes=0, episode_rate_per_min=0.0,
                    median_amp=np.nan, median_recovery=np.nan, median_residual=np.nan,
                    frac_recovered=np.nan, median_peak_spec=np.nan,
                    run_median_spec=float(np.median(spec_al)))
    start = idx[0]; prev = idx[0]
    for j in idx[1:]:
        if j - prev <= GAP + 1:
            prev = j
        else:
            episodes.append((start, prev)); start = j; prev = j
    episodes.append((start, prev))

    amps, recs, resids, recovered, peakspec = [], [], [], [], []
    for (s, e) in episodes:
        if s - PRE < 0 or e + POST >= T:
            continue
        base = np.median(mnps[s - PRE:s], axis=0)
        seg = mnps[s:e + 1]
        dev = np.linalg.norm(seg - base, axis=1)
        peak_i = s + int(np.argmax(dev))
        amp = float(dev.max())
        amps.append(amp)
        peakspec.append(float(spec_al[min(peak_i, len(spec_al) - 1)]))
        post = np.median(mnps[e + 1:e + 1 + POST], axis=0)
        resids.append(float(np.linalg.norm(post - base)))
        # recovery half-time: windows after peak to fall below half-amplitude
        half = base + 0.5 * (mnps[peak_i] - base)
        rt = np.nan
        for k in range(1, POST + 8):
            if peak_i + k >= T: break
            if np.linalg.norm(mnps[peak_i + k] - base) <= 0.5 * amp:
                rt = k; break
        recs.append(rt)
        recovered.append(1.0 if np.isfinite(rt) else 0.0)
    dur_min = T * 4 / 60.0
    return dict(
        cpc=cpc,
        n_episodes=len(amps),
        episode_rate_per_min=len(amps) / dur_min,
        median_amp=float(np.nanmedian(amps)) if amps else np.nan,
        median_recovery=float(np.nanmedian(recs)) if any(np.isfinite(recs)) else np.nan,
        median_residual=float(np.nanmedian(resids)) if resids else np.nan,
        frac_recovered=float(np.nanmean(recovered)) if recovered else np.nan,
        median_peak_spec=float(np.nanmedian(peakspec)) if peakspec else np.nan,
        run_median_spec=float(np.median(spec_al)),
    )

# collect subjects
by_subj = {}
for d in DIRS:
    for f in sorted(glob.glob(d + "/**/*.h5", recursive=True)):
        subj = f.split("sub-")[1][:4]
        by_subj.setdefault(subj, []).append(f)

rows = []; s1 = s5 = 0
for subj, files in by_subj.items():
    try:
        with h5py.File(files[0], "r") as h:
            cpc = int(h.attrs.get("meta_cpc", -1))
    except Exception:
        continue
    if cpc == 1 and s1 >= N_PER_GROUP: continue
    if cpc == 5 and s5 >= N_PER_GROUP: continue
    if cpc not in (1, 5): continue
    fr = [run_lpr(f) for f in files[:RUNS_PER_SUBJ]]
    fr = [x for x in fr if x is not None]
    if not fr: continue
    agg = {"subj": subj, "cpc": cpc}
    for k in fr[0]:
        if k == "cpc": continue
        vals = [x[k] for x in fr if x[k] is not None and np.isfinite(x[k])]
        agg[k] = float(np.median(vals)) if vals else np.nan
    rows.append(agg)
    s1 += cpc == 1; s5 += cpc == 5

df = pd.DataFrame(rows)
print(f"subjects: CPC1={(df.cpc==1).sum()} CPC5={(df.cpc==5).sum()}")
print(f"median episodes/subj: CPC1={df[df.cpc==1].n_episodes.median():.0f} CPC5={df[df.cpc==5].n_episodes.median():.0f}")
y = (df["cpc"] == 5).astype(int).values
print("\nmetric                     AUC    CPC1_med   CPC5_med   n_finite")
for c in ["run_median_spec", "episode_rate_per_min", "median_amp", "median_recovery",
          "median_residual", "frac_recovered", "median_peak_spec"]:
    v = df[c].values; m = np.isfinite(v)
    if m.sum() < 40:
        print(f"{c:24s}  insufficient ({m.sum()})"); continue
    a = roc_auc_score(y[m], v[m]); a = max(a, 1 - a)
    print(f"{c:24s} {a:.3f}   {np.nanmedian(df[df.cpc==1][c]):+.3f}   {np.nanmedian(df[df.cpc==5][c]):+.3f}   {m.sum()}")
df.to_csv(r"articles/CLINICAL/comatose_ndt/results/_scratch_lpr_features_fullcohort.csv", index=False)
print("\nsaved _scratch_lpr_features_fullcohort.csv")
