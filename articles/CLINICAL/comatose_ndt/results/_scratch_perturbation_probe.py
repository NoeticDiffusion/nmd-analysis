"""Probe: are coma MNPS trajectories bursty, and where are the perturbations?

The article uses run-level medians of geometry over ~52 min of mostly
quiescent EEG. NDT is most informative during *processing* (transients). Here
we (1) confirm burstiness of the trajectory speed, and (2) sketch an
endogenous-perturbation detector on the exported per-window geometry.
"""
import glob, json
import numpy as np
import h5py

DIRS = [
    r"data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260601_131927_part1_combat",
    r"data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260601_143502_part2_combat",
]

def subject_first_file(cpc_target, n_want):
    """Return list of (subject, file) for first run of subjects with given cpc."""
    out = {}
    for d in DIRS:
        for f in sorted(glob.glob(d + "/**/*.h5", recursive=True)):
            try:
                with h5py.File(f, "r") as h:
                    cpc = int(h.attrs.get("meta_cpc", -1))
                    subj = str(h.attrs.get("subject_id", ""))
            except Exception:
                continue
            if cpc == cpc_target and subj not in out:
                out[subj] = f
            if len(out) >= n_want:
                return out
    return out

def describe(f):
    with h5py.File(f, "r") as h:
        mnps = h["/mnps_3d"][:]            # (T,3)
        dot = h["/mnps_3d_dot"][:]         # (T,3)
        J = h["/jacobian/J_hat"][:]        # (W,3,3)
        subj = str(h.attrs["subject_id"]); cpc = int(h.attrs["meta_cpc"])
    speed = np.linalg.norm(dot, axis=1)
    # within-run robust threshold for "event"
    med = np.median(speed); mad = np.median(np.abs(speed - med)) * 1.4826 + 1e-9
    z = (speed - med) / mad
    events = z > 3.0
    # jacobian spectral radius per window
    eig = np.linalg.eigvals(J)
    spec = np.abs(eig).max(axis=1)
    return dict(subj=subj, cpc=cpc, T=len(speed),
                speed_cv=float(speed.std()/ (speed.mean()+1e-9)),
                speed_kurt=float(((speed-speed.mean())**4).mean()/(speed.std()**4+1e-9)),
                event_frac=float(events.mean()),
                spec_med=float(np.median(spec)),
                spec_p95=float(np.percentile(spec, 95)),
                speed=speed)

c1 = subject_first_file(1, 1)
c5 = subject_first_file(5, 1)
for tag, files in [("CPC1", c1), ("CPC5", c5)]:
    for subj, f in files.items():
        r = describe(f)
        sp = r.pop("speed")
        print(f"{tag} {r['subj']}: T={r['T']} speed CV={r['speed_cv']:.2f} kurt={r['speed_kurt']:.1f} "
              f"event_frac(z>3)={r['event_frac']:.3f} spec_med={r['spec_med']:.3f} spec_p95={r['spec_p95']:.3f}")
        # crude ascii burst profile (downsample to 60 bins, max speed per bin)
        bins = np.array_split(sp, 60)
        prof = np.array([b.max() for b in bins])
        prof = (prof - prof.min())/(np.ptp(prof)+1e-9)
        line = "".join(" .:-=+*#%@"[min(9,int(v*9))] for v in prof)
        print("   speed: |" + line + "|")
