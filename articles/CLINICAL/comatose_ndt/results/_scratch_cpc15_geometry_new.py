"""Outside-the-box geometric metrics from horizon dynamics + cross-channel ratios.

Theory: Sigma^(h+1) = A Sigma^(h) A^T + Q with A = exp(J dt). As the horizon
grows, the reachable set is increasingly dominated by the top eigenvector of A,
so the effective reachable dimension d_eff(h) collapses at a rate set by the
spectral gap of J. A canalized (CPC5) flow with one runaway unstable mode
collapses fast; a healthy flow keeps reachable dimension distributed.

We test NEW single quantities that no current metric captures:
  - horizon collapse rate / curvature of cone_d_eff, dir_entropy, kappa, q_ratio
  - cross-channel RATIOS / interactions (nonlinear, invisible to linear LR)
  - a 'Noetic Canalization Index' = expansion magnitude x dimensional collapse
"""
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score

RES = Path(r"articles/CLINICAL/comatose_ndt/results")
w = pd.read_csv(RES / "_scratch_subject_feature_matrix.csv", index_col=0)
y = w["y"].values

def auc(s):
    s = np.asarray(s, float)
    m = ~np.isnan(s)
    a = roc_auc_score(y[m], s[m])
    return max(a, 1 - a), a, m.sum()

def col(name):
    return w[f"reachability_cones::{name}"].astype(float).values if not name.startswith("global") else w[name].astype(float).values

H = np.array([1, 2, 3, 4], dtype=float)
def horizon_slope(prefix, suffix="_median"):
    M = np.column_stack([col(f"{prefix}_h{h}{suffix}") for h in [1, 2, 3, 4]])
    # per-subject OLS slope of value vs horizon
    Hc = H - H.mean()
    slopes = np.full(M.shape[0], np.nan)
    for i in range(M.shape[0]):
        v = M[i]
        mm = ~np.isnan(v)
        if mm.sum() >= 3:
            vv = v[mm] - v[mm].mean()
            slopes[i] = (Hc[mm] * vv).sum() / (Hc[mm] ** 2).sum()
    return slopes, M

print("=== NEW: horizon-dynamics single metrics (AUC) ===")
results = []
for pref in ["cone_d_eff", "cone_dir_entropy_norm", "cone_kappa", "cone_log_det", "cone_q_ratio", "cone_log_eig_var"]:
    sl, M = horizon_slope(pref)
    a, raw, n = auc(sl)
    results.append((a, f"{pref} horizon SLOPE", raw))
    # relative collapse (h1 -> h4)
    rel = (M[:, 0] - M[:, 3]) / (np.abs(M[:, 0]) + 1e-9)
    a2, raw2, _ = auc(rel)
    results.append((a2, f"{pref} relative collapse (h1->h4)", raw2))
for a, name, raw in sorted(results, reverse=True):
    print(f"  {a:.3f}  (raw {raw:.3f})  {name}")

# ---- cross-channel nonlinear ratios / interactions ----
def zr(name):
    v = col(name); med = np.nanmedian(v); v = np.where(np.isnan(v), med, v)
    r = rankdata(v); return (r - r.mean()) / (r.std() + 1e-9)

SPEC = "global_mnps_jacobian_9d::spectral_radius_mean"
SPEC3 = "global_mnps_jacobian_3d::spectral_radius_median"
COND = "global_mnps_jacobian_9d::jacobian_cond_median"
FROB = "global_mnps_jacobian_9d::frobenius_norm_median"
ANIS = "global_mnps_jacobian_9d::anisotropy_abs_eig_median"
TDE = "tube_d_eff_median"
PLD = "persistence_log_det_median"
DENT = "tube_dir_entropy_norm_median"

print("\n=== NEW: cross-channel ratios / interactions (AUC) ===")
deff_slope, Md = horizon_slope("cone_d_eff")
deff_long = Md[:, 3]
deff_h1 = Md[:, 0]
cands = {
    # canalization: high expansion that fails to produce sustained reachable dim
    "log(spectral_radius) - log(tube_d_eff)": np.log(np.clip(col(SPEC),1e-9,None)) - np.log(np.clip(col(TDE),1e-9,None)),
    "spectral_radius / tube_d_eff": col(SPEC)/np.clip(col(TDE),1e-9,None),
    "frobenius / tube_d_eff (deformation per dim)": col(FROB)/np.clip(col(TDE),1e-9,None),
    "Noetic Canalization Index NCI = z(spec)+z(cond) - z(deff_long)+z(-deff_slope)": zr(SPEC)+zr(COND) + (-(rankdata(np.nan_to_num(deff_long,nan=np.nanmedian(deff_long)))-len(y)/2)/ (np.std(rankdata(deff_long))+1e-9)),
    "spectral_radius * relative_deff_collapse": col(SPEC) * ((deff_h1-deff_long)/(np.abs(deff_h1)+1e-9)),
    "spectral_radius * (-cone_d_eff slope)": col(SPEC) * (-deff_slope),
    "jacobian_cond / persistence_log_det": col(COND)/np.clip(col(PLD)-np.nanmin(col(PLD))+1,1e-9,None),
}
crows = []
for name, s in cands.items():
    a, raw, n = auc(s)
    crows.append((a, name, raw))
for a, name, raw in sorted(crows, reverse=True):
    print(f"  {a:.3f}  (raw {raw:.3f})  {name}")

print(f"\nreference: single MNJ9D spectral_radius_mean = {auc(col(SPEC))[0]:.3f}")
