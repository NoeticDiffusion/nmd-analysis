"""Final confirmation: Noetic Regime-Brittleness Index (NRBI).

Two-axis CTIP-style composite:
  P-axis (pathological expansion / lock-in): rank-z mean of
      MNJ spectral_radius (9D mean) and Jacobian conditioning (cond number)
  C-axis (capacity collapse): negative rank-z mean of
      reachability tube_d_eff and persistence_log_det
  NRBI = sqrt( relu(P)^2 + relu(C_collapse)^2 )   [fit-free, 0 params]

Compares NRBI to the best single metric with stratified bootstrap AUC CIs.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score

RES = Path(r"articles/CLINICAL/comatose_ndt/results")
wide = pd.read_csv(RES / "_scratch_subject_feature_matrix.csv", index_col=0)
y = wide["y"].values
X = wide.drop(columns=["y"])

def zr(col):
    v = X[col].astype(float).values
    med = np.nanmedian(v)
    v = np.where(np.isnan(v), med, v)
    r = rankdata(v)
    return (r - r.mean()) / (r.std() + 1e-9)

SPEC = "global_mnps_jacobian_9d::spectral_radius_mean"
COND9 = "global_mnps_jacobian_9d::jacobian_cond_median"
COND3 = "global_mnps_jacobian_3d::jacobian_cond_median"
TDE = "reachability_cones::tube_d_eff_median"
PLD = "reachability_cones::persistence_log_det_median"

P = (zr(SPEC) + zr(COND9) + zr(COND3)) / 3.0          # high = pathological expansion (poor)
C_collapse = -(zr(TDE) + zr(PLD)) / 2.0               # high = capacity collapse (poor)

NRBI = np.sqrt(np.clip(P, 0, None) ** 2 + np.clip(C_collapse, 0, None) ** 2)
NRBI_signed = P + C_collapse  # additive variant

scores = {
    "single MNJ9D spectral_radius_mean (raw)": X[SPEC].fillna(X[SPEC].median()).values,
    "rank-z P-axis only (expansion+cond)": P,
    "additive P + C_collapse": NRBI_signed,
    "NRBI regime distance (fit-free)": NRBI,
}

def boot_ci(score, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    idx0 = np.where(y == 0)[0]; idx1 = np.where(y == 1)[0]
    aucs = []
    for _ in range(n):
        b = np.concatenate([rng.choice(idx0, len(idx0)), rng.choice(idx1, len(idx1))])
        aucs.append(roc_auc_score(y[b], score[b]))
    return np.percentile(aucs, [2.5, 97.5])

print("metric, AUC [95% bootstrap CI]")
for name, s in scores.items():
    a = roc_auc_score(y, s)
    lo, hi = boot_ci(np.asarray(s, float))
    print(f"  {a:.3f}  [{lo:.3f}, {hi:.3f}]   {name}")

# paired bootstrap: NRBI vs best single
rng = np.random.default_rng(1)
idx0 = np.where(y == 0)[0]; idx1 = np.where(y == 1)[0]
d = []
s_single = scores["single MNJ9D spectral_radius_mean (raw)"]
for _ in range(2000):
    b = np.concatenate([rng.choice(idx0, len(idx0)), rng.choice(idx1, len(idx1))])
    d.append(roc_auc_score(y[b], NRBI[b]) - roc_auc_score(y[b], s_single[b]))
d = np.array(d)
print(f"\nNRBI - single  delta AUC = {d.mean():+.3f}  [{np.percentile(d,2.5):+.3f}, {np.percentile(d,97.5):+.3f}]  P(>0)={np.mean(d>0):.3f}")

# direction sanity
print("\nmean NRBI  CPC1:", round(NRBI[y==0].mean(),3), " CPC5:", round(NRBI[y==1].mean(),3))
