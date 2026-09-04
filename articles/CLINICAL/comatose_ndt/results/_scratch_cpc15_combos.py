"""Evaluate candidate combined NDT scores for CPC1 vs CPC5 separation.

Uses the per-subject 0-12h feature matrix produced by the search script.
All multivariate AUCs are out-of-fold via RepeatedStratifiedKFold to avoid
optimistic in-sample bias. Also evaluates a closed-form, fit-free contrast
score (no leakage possible).
"""
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score

RES = Path(r"articles/CLINICAL/comatose_ndt/results")
wide = pd.read_csv(RES / "_scratch_subject_feature_matrix.csv", index_col=0)
y = wide["y"].values
X = wide.drop(columns=["y"])

def oof_auc(cols, n_rep=20, seed=20260517):
    sub = X[cols].values
    clf = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                        LogisticRegression(solver="liblinear", class_weight="balanced", max_iter=1000))
    rkf = RepeatedStratifiedKFold(n_splits=5, n_repeats=n_rep, random_state=seed)
    aucs = []
    for tr, te in rkf.split(sub, y):
        clf.fit(sub[tr], y[tr])
        p = clf.predict_proba(sub[te])[:, 1]
        aucs.append(roc_auc_score(y[te], p))
    return np.mean(aucs), np.std(aucs)

def zfill(col):
    v = X[col].astype(float)
    return (v - v.median()) / (v.std() + 1e-9)

# Channel definitions
EXP = "global_mnps_jacobian_9d::spectral_radius_median"      # local expansion (high=poor)
EXP3 = "global_mnps_jacobian_3d::spectral_radius_median"
ANIS = "global_mnps_jacobian_9d::anisotropy_abs_eig_median"  # anisotropic deformation (high=poor)
BREADTH = "reachability_cones::tube_d_eff_median"            # reachable dimensionality (high=good)
DIRENT = "reachability_cones::tube_dir_entropy_norm_median"  # directional entropy (high=good)
ROT = "global_mnps_jacobian_3d::rotation_norm_median"

candidates = {
    "single: MNJ9D spectral_radius_mean": ["global_mnps_jacobian_9d::spectral_radius_mean"],
    "single: MNJ9D spectral_radius_median": [EXP],
    "single: tube_d_eff_median": [BREADTH],
    "2ch: expansion + breadth": [EXP, BREADTH],
    "3ch: expansion + anisotropy + breadth": [EXP, ANIS, BREADTH],
    "4ch: exp + anis + breadth + dir_entropy": [EXP, ANIS, BREADTH, DIRENT],
    "5ch CTIP-ish: +rotation": [EXP, ANIS, BREADTH, DIRENT, ROT],
    "3D-only NDI: exp3 + breadth + dirent": [EXP3, BREADTH, DIRENT],
}

print("=== Out-of-fold repeated-CV AUC (logistic) ===")
res = []
for name, cols in candidates.items():
    cols = [c for c in cols if c in X.columns]
    m, s = oof_auc(cols)
    res.append((name, len(cols), m, s))
    print(f"{m:.3f} +/- {s:.3f}   ({len(cols)} feat)  {name}")

# Closed-form, fit-free NDT contrast index (no CV needed; no fitted params)
# NDI = pathological-expansion channel  -  capacity-breadth channel
def contrast_auc(pos_cols, neg_cols):
    score = sum(zfill(c) for c in pos_cols) / len(pos_cols) - sum(zfill(c) for c in neg_cols) / len(neg_cols)
    s = score.values
    mask = ~np.isnan(s)
    return roc_auc_score(y[mask], s[mask]), mask.sum()

print("\n=== Closed-form fit-free contrast indices (direct AUC) ===")
auc1, n1 = contrast_auc([EXP, ANIS], [BREADTH, DIRENT])
print(f"{auc1:.3f}  (n={n1})  NDI = mean_z(expansion9D, anisotropy9D) - mean_z(tube_d_eff, dir_entropy)")
auc2, n2 = contrast_auc([EXP], [BREADTH])
print(f"{auc2:.3f}  (n={n2})  simple = z(spectral_radius9D) - z(tube_d_eff)")
auc3, n3 = contrast_auc([EXP3, ANIS], [BREADTH, DIRENT])
print(f"{auc3:.3f}  (n={n3})  NDI(3D-jac) = mean_z(spec3D, anis9D) - mean_z(tube_d_eff, dir_entropy)")

# correlation between the two channels
exp_c = (zfill(EXP) + zfill(ANIS)) / 2
br_c = (zfill(BREADTH) + zfill(DIRENT)) / 2
r = pd.concat([exp_c, br_c], axis=1).corr().iloc[0, 1]
print(f"\nchannel correlation (expansion vs breadth): r = {r:.3f}")
