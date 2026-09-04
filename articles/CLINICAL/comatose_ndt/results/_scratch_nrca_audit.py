"""Independent audit of the colleague's NRCA proposal (diary 160).

NRCA = projection_to_recovery_ray / sqrt(1 + off_axis^2), where the oriented
4-vector is [z(d_eff), -z(capture), -z(spec3D), -z(frob3D)] and the ray is
[1,1,1,1]/2. The projection equals RDR_core (the linear sum) up to scale, so
the ONLY new ingredient is the off-axis coherence discount. We test:
  (1) Can we reproduce ~0.70 AUC?
  (2) Does the discount add anything over the plain projection?
  (3) Does NRCA beat the single MNJ9D spectral_radius ceiling (~0.715)?
  (4) Is it stable to robust-z vs rank-z scaling?
"""
import numpy as np, pandas as pd
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score

w = pd.read_csv(r"articles/CLINICAL/comatose_ndt/results/_scratch_subject_feature_matrix.csv", index_col=0)
y = w["y"].values  # 1 = CPC5 poor

def robust_z(col):
    v = pd.to_numeric(w[col], errors="coerce").astype(float).values
    med = np.nanmedian(v); mad = np.nanmedian(np.abs(v - med)) * 1.4826
    if not np.isfinite(mad) or mad <= 1e-12: mad = np.nanstd(v)
    v = np.where(np.isnan(v), med, v)
    return (v - med) / (mad + 1e-12)

def rank_z(col):
    v = pd.to_numeric(w[col], errors="coerce").astype(float).values
    v = np.where(np.isnan(v), np.nanmedian(v), v)
    r = rankdata(v); return (r - r.mean()) / (r.std() + 1e-9)

DE = "reachability_cones::tube_d_eff_median"
CAP = "reachability_cones::tube_capture_gate_median"
SP3 = "global_mnps_jacobian_3d::spectral_radius_median"
FR3 = "global_mnps_jacobian_3d::frobenius_norm_median"
SP9 = "global_mnps_jacobian_9d::spectral_radius_mean"

def nrca_family(zfun, spec_col=SP3, frob_col=FR3):
    v = np.column_stack([zfun(DE), -zfun(CAP), -zfun(spec_col), -zfun(frob_col)])
    ideal = np.ones(4) / 2.0
    proj = v @ ideal                       # == RDR_core / 2
    resid = v - np.outer(proj, ideal)
    off = np.linalg.norm(resid, axis=1)
    norm = np.linalg.norm(v, axis=1)
    cos = np.divide(proj, norm, out=np.zeros_like(proj), where=norm > 1e-12)
    nrca = proj / np.sqrt(1 + off**2)
    return proj, off, cos, nrca

def A(s):  # orientation-agnostic AUC, but report poor-high oriented
    a = roc_auc_score(y, s); return max(a, 1 - a)

print("=== robust-z (MAD) scaling, MNJ3D in cone (as in script) ===")
proj, off, cos, nrca = nrca_family(robust_z)
print(f"  projection (=RDR_core)  AUC {A(proj):.3f}")
print(f"  NRCA (proj/sqrt(1+off^2)) AUC {A(nrca):.3f}")
print(f"  cosine alignment         AUC {A(cos):.3f}")
print(f"  off_axis alone           AUC {A(off):.3f}")

print("\n=== rank-z scaling, MNJ3D in cone ===")
proj, off, cos, nrca = nrca_family(rank_z)
print(f"  projection (=RDR_core)  AUC {A(proj):.3f}")
print(f"  NRCA                     AUC {A(nrca):.3f}")
print(f"  cosine                   AUC {A(cos):.3f}")

print("\n=== rank-z, swap MNJ9D spectral_radius into cone ===")
proj9, off9, cos9, nrca9 = nrca_family(rank_z, spec_col=SP9)
print(f"  projection               AUC {A(proj9):.3f}")
print(f"  NRCA                     AUC {A(nrca9):.3f}")

print("\n=== ceilings for comparison ===")
print(f"  single MNJ9D spectral_radius_mean  AUC {A(robust_z(SP9)):.3f}")
print(f"  single MNJ3D spectral_radius       AUC {A(robust_z(SP3)):.3f}")

# Does the discount add anything? correlation of NRCA with plain projection,
# and paired bootstrap NRCA - projection.
rng = np.random.default_rng(0); i0 = np.where(y==0)[0]; i1 = np.where(y==1)[0]
proj, off, cos, nrca = nrca_family(robust_z)
r = np.corrcoef(rankdata(proj), rankdata(nrca))[0,1]
d = [A(nrca[b]) - A(proj[b]) for b in
     (np.concatenate([rng.choice(i0,len(i0)), rng.choice(i1,len(i1))]) for _ in range(2000))]
d = np.array(d)
print(f"\nNRCA vs projection: rank corr={r:.3f}  delta AUC={d.mean():+.3f}  CI[{np.percentile(d,2.5):+.3f},{np.percentile(d,97.5):+.3f}]")
