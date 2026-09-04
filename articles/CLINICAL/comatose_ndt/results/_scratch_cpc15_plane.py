"""The Noetic Brittleness Plane: a 2D geometric object, not a scalar.

Axes (rank-z, oriented so higher = more pathological):
  P (expansion/lock-in)  = mean rank-z of MNJ spectral_radius + jacobian_cond
  C (capacity collapse)  = -mean rank-z of tube_d_eff + persistence_log_det
Since corr(P,C) ~ 0 and they misclassify DIFFERENT patients, we test:
  1. Polar coords: radius rho = severity, angle theta = brittleness TYPE.
  2. Whether a conjunctive (both-axis) rule improves the high-specificity
     corner (clinically the relevant region for poor-outcome calls), even
     when global AUC is flat.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score, roc_curve

RES = Path(r"articles/CLINICAL/comatose_ndt/results")
w = pd.read_csv(RES / "_scratch_subject_feature_matrix.csv", index_col=0)
y = w["y"].values  # 1 = CPC5 (poor)

def zr(name):
    v = w[name].astype(float).values; med = np.nanmedian(v)
    v = np.where(np.isnan(v), med, v); r = rankdata(v)
    return (r - r.mean()) / (r.std() + 1e-9)

P = (zr("global_mnps_jacobian_9d::spectral_radius_mean") + zr("global_mnps_jacobian_9d::jacobian_cond_median")) / 2
C = -(zr("reachability_cones::tube_d_eff_median") + zr("reachability_cones::persistence_log_det_median")) / 2

rho = np.sqrt(P**2 + C**2)                 # severity (regime distance)
theta = np.degrees(np.arctan2(C, P))       # brittleness TYPE angle
# rectified regime distance: only pathological quadrant counts
rho_path = np.sqrt(np.clip(P,0,None)**2 + np.clip(C,0,None)**2)

print("corr(P,C):", round(np.corrcoef(P, C)[0,1], 3))
print("rho severity AUC:", round(roc_auc_score(y, rho), 3),
      "| rho_path AUC:", round(roc_auc_score(y, rho_path), 3),
      "| theta AUC:", round(max(roc_auc_score(y, theta), 1-roc_auc_score(y, theta)), 3))

# Operating-point comparison: sensitivity for POOR at fixed high specificity
def sens_at_spec(score, target_spec):
    fpr, tpr, thr = roc_curve(y, score)
    ok = np.where((1 - fpr) >= target_spec)[0]
    return tpr[ok].max() if len(ok) else np.nan

SPEC = w["global_mnps_jacobian_9d::spectral_radius_mean"].fillna(
       w["global_mnps_jacobian_9d::spectral_radius_mean"].median()).values
ratio = SPEC / np.clip(w["reachability_cones::tube_d_eff_median"].fillna(
        w["reachability_cones::tube_d_eff_median"].median()).values, 1e-9, None)

print("\n=== Sensitivity for poor outcome at fixed specificity ===")
print(f"{'score':40s}  spec0.90  spec0.95  spec0.99")
for name, s in {
    "single spectral_radius": SPEC,
    "ratio spec/tube_d_eff": ratio,
    "rho_path (plane severity)": rho_path,
    "P axis only": P,
    "C axis only": C,
}.items():
    print(f"{name:40s}  {sens_at_spec(s,0.90):.3f}     {sens_at_spec(s,0.95):.3f}     {sens_at_spec(s,0.99):.3f}")

# Conjunctive high-confidence rule: both axes pathological
# pick per-axis thresholds at 80th percentile of CPC1 (healthy) distribution
def thr_from_good(ax, q=80):
    return np.percentile(ax[y == 0], q)
both = (P > thr_from_good(P)) & (C > thr_from_good(C))
either = (P > thr_from_good(P)) | (C > thr_from_good(C))
for nm, rule in {"BOTH axes high (conjunctive)": both, "EITHER axis high (disjunctive)": either}.items():
    tp = (rule & (y==1)).sum(); fp = (rule & (y==0)).sum()
    sens = tp / (y==1).sum(); spec = 1 - fp/(y==0).sum(); ppv = tp/max(rule.sum(),1)
    print(f"\n{nm}: flags {rule.sum()} pts | sens(poor)={sens:.3f} spec={spec:.3f} PPV={ppv:.3f}")

# Brittleness-type stratification among poor patients
poor = y == 1
exp_dom = (P[poor] > C[poor]).mean()
print(f"\nAmong CPC5: expansion-dominant {exp_dom:.2f}, collapse-dominant {1-exp_dom:.2f}")
print("median theta CPC1:", round(np.median(theta[y==0]),1), " CPC5:", round(np.median(theta[y==1]),1))
