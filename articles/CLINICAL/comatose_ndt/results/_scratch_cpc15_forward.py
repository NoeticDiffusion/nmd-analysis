"""Greedy forward selection (out-of-fold AUC) + robust/regime composites.

Answers: starting from the best single NDT metric, which additions genuinely
improve CPC1-vs-CPC5 separation, and do rank-robust or 'either-axis' regime
composites beat a single Jacobian metric?
"""
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import rankdata
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
# drop spurious / sparse
good = [c for c in X.columns if "mndm_version" not in c and X[c].notna().sum() > 0.8*len(X) and X[c].nunique() > 5]
X = X[good]

rkf = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=20260517)
def oof_auc(cols):
    sub = X[cols].values
    clf = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                        LogisticRegression(solver="liblinear", class_weight="balanced", max_iter=1000))
    aucs = []
    for tr, te in rkf.split(sub, y):
        clf.fit(sub[tr], y[tr]); p = clf.predict_proba(sub[te])[:, 1]
        aucs.append(roc_auc_score(y[te], p))
    return float(np.mean(aucs))

start = "global_mnps_jacobian_9d::spectral_radius_mean"
selected = [start]
best = oof_auc(selected)
print(f"start {best:.3f}  {start}")
for step in range(4):
    cand_scores = []
    for c in X.columns:
        if c in selected:
            continue
        cand_scores.append((oof_auc(selected + [c]), c))
    cand_scores.sort(reverse=True)
    gain = cand_scores[0][0] - best
    print(f"\nstep {step+1}: best add -> {cand_scores[0][0]:.3f} (gain {gain:+.3f}) {cand_scores[0][1]}")
    for s, c in cand_scores[1:4]:
        print(f"          alt {s:.3f}  {c}")
    if gain < 0.003:
        print("  -> gain below 0.003, stop forward selection")
        break
    selected.append(cand_scores[0][1]); best = cand_scores[0][0]

print("\nfinal selected:", selected, "OOF AUC", round(best, 3))

# ---- robust rank-based single + regime 'either-axis' composites ----
def zr(col):  # robust rank z
    v = X[col].astype(float).values
    r = rankdata(v)
    return (r - r.mean()) / (r.std() + 1e-9)

EXP = "global_mnps_jacobian_9d::spectral_radius_mean"
ANIS = "global_mnps_jacobian_9d::anisotropy_abs_eig_median"
BREADTH = "reachability_cones::tube_d_eff_median"
DIRENT = "reachability_cones::tube_dir_entropy_norm_median"

print("\n=== rank-robust fit-free composites (direct AUC) ===")
expansion = (zr(EXP) + zr(ANIS)) / 2          # high = poor
breadth = (zr(BREADTH) + zr(DIRENT)) / 2      # high = good
for name, s in {
    "rank z expansion(9D spec+anis)": expansion,
    "contrast: expansion - breadth": expansion - breadth,
    "either-axis max(expansion, -breadth)": np.maximum(expansion, -breadth),
    "sum-of-squares regime dist": np.sqrt(np.clip(expansion,0,None)**2 + np.clip(-breadth,0,None)**2),
}.items():
    print(f"{roc_auc_score(y, s):.3f}  {name}")

# Do expansion and breadth misclassify the SAME subjects? (predictive redundancy check)
from sklearn.metrics import roc_curve
def youden_pred(score):
    fpr, tpr, thr = roc_curve(y, score)
    j = np.argmax(tpr - fpr)
    return (score >= thr[j]).astype(int)
pe = youden_pred(expansion); pb = youden_pred(-breadth)
agree = (pe == pb).mean()
print(f"\nexpansion vs breadth classification agreement: {agree:.3f}")
print(f"expansion correct: {(pe==y).mean():.3f} | breadth correct: {(pb==y).mean():.3f} | OR-correct (either right): {((pe==y)|(pb==y)).mean():.3f}")
