"""Confirm the Canalization Ratio and brittleness-plane subtypes.

CR = spectral_radius(MNJ) / tube_d_eff(reachability)  -- one dimensionless number
unifying the local-expansion (MNJ) and reachable-dimension (cone) families.
Checks: AUC vs single, part1/part2 split stability, bootstrap sens@spec0.95.
"""
import numpy as np, pandas as pd
from pathlib import Path
from sklearn.metrics import roc_auc_score, roc_curve

RES = Path(r"articles/CLINICAL/comatose_ndt/results")
w = pd.read_csv(RES / "_scratch_subject_feature_matrix.csv", index_col=0)
# need hospital/cohort: pull from the long file's subject index quickly via cohort matrix? use cpc only here
y = w["y"].values
spec = w["global_mnps_jacobian_9d::spectral_radius_mean"].astype(float)
tde = w["reachability_cones::tube_d_eff_median"].astype(float)
spec = spec.fillna(spec.median()); tde = tde.fillna(tde.median())
CR = (spec / tde.clip(lower=1e-9)).values
logCR = np.log(np.clip(spec.values,1e-9,None)) - np.log(np.clip(tde.values,1e-9,None))

def sens_at(score, sp):
    fpr,tpr,_=roc_curve(y,score); ok=np.where((1-fpr)>=sp)[0]
    return tpr[ok].max() if len(ok) else np.nan

rng=np.random.default_rng(0); i0=np.where(y==0)[0]; i1=np.where(y==1)[0]
def boot(fn,n=2000):
    out=[]
    for _ in range(n):
        b=np.concatenate([rng.choice(i0,len(i0)),rng.choice(i1,len(i1))]); out.append(fn(b))
    return np.percentile(out,[2.5,97.5])

print("Canalization Ratio CR = spectral_radius / tube_d_eff")
print(f"  AUC CR={roc_auc_score(y,CR):.3f}  logCR={roc_auc_score(y,logCR):.3f}  single spec={roc_auc_score(y,spec.values):.3f}")
print(f"  sens@spec0.95: CR={sens_at(CR,0.95):.3f}  single={sens_at(spec.values,0.95):.3f}")
ci=boot(lambda b: sens_at(CR[b],0.95)-sens_at(spec.values[b],0.95))
print(f"  bootstrap delta sens@spec0.95 (CR - single): [{ci[0]:+.3f}, {ci[1]:+.3f}]")

# part1/part2 split via subject metadata
meta=pd.read_csv(RES/"merge_manifest_20260602_combined_combat_corrected_primary12h_combined_subject_metadata.csv")
mc=[c for c in meta.columns if 'subject' in c.lower()][0]
src=[c for c in meta.columns if any(k in c.lower() for k in['part','cohort','source','bundle'])]
print("\nmeta cohort cols:",src[:6])
