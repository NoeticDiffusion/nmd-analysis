"""Why does CPC1-vs-CPC5 AUC plateau at ~0.71-0.73?

Tests three hypotheses:
  H1 single-shared-axis: one latent severity dimension carries the signal
     -> AUC(PC1) ~ ceiling; metrics highly inter-correlated.
  H2 information saturation: even a kitchen-sink over ALL 166 metrics caps
     -> no feature engineering breaks it; ceiling is label/data-bound.
  H3 label-noise floor: implied if even an overfit-capacity model can't exceed it.
"""
import numpy as np, pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score

w = pd.read_csv(r"articles/CLINICAL/comatose_ndt/results/_scratch_subject_feature_matrix.csv", index_col=0)
y = w["y"].values
X = w.drop(columns=["y"])
keep = [c for c in X.columns if "mndm_version" not in c and X[c].notna().sum() > 0.8*len(X) and X[c].nunique() > 5]
X = X[keep]
print(f"{X.shape[1]} features, {len(y)} subjects ({(y==0).sum()} CPC1 / {(y==1).sum()} CPC5)")

imp = SimpleImputer(strategy="median"); sc = StandardScaler()
Xs = sc.fit_transform(imp.fit_transform(X))

def cv_auc(estimator, Xmat, nrep=20):
    rkf = RepeatedStratifiedKFold(n_splits=5, n_repeats=nrep, random_state=7)
    a = []
    for tr, te in rkf.split(Xmat, y):
        estimator.fit(Xmat[tr], y[tr])
        a.append(roc_auc_score(y[te], estimator.predict_proba(Xmat[te])[:, 1]))
    return np.mean(a), np.std(a)

# H2/H3: kitchen-sink upper bounds
lr = LogisticRegression(solver="liblinear", class_weight="balanced", max_iter=2000, C=0.1)
m, s = cv_auc(lr, Xs); print(f"\nkitchen-sink logistic (166 feat, L2 C=0.1): AUC {m:.3f} +/- {s:.3f}")
lr2 = LogisticRegression(solver="liblinear", penalty="l1", class_weight="balanced", max_iter=2000, C=0.2)
m, s = cv_auc(lr2, Xs); print(f"kitchen-sink logistic L1 (sparse):          AUC {m:.3f} +/- {s:.3f}")
gb = GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=0)
m, s = cv_auc(gb, Xs); print(f"gradient boosting (nonlinear, 166 feat):    AUC {m:.3f} +/- {s:.3f}")

# H1: single shared axis via PCA
pca = PCA(n_components=10).fit(Xs)
evr = pca.explained_variance_ratio_
print(f"\nPCA explained variance: PC1={evr[0]:.2f} PC2={evr[1]:.2f} PC3={evr[2]:.2f} "
      f"cum5={evr[:5].sum():.2f}")
scores = pca.transform(Xs)
for k in range(5):
    a = roc_auc_score(y, scores[:, k]); a = max(a, 1-a)
    print(f"  AUC(PC{k+1}) = {a:.3f}")

# how concentrated is the discriminative direction? logistic on PC1 only vs top-3 PCs
for npc in (1, 2, 3, 5):
    a = cv_auc(make_pipeline(LogisticRegression(max_iter=1000)), scores[:, :npc])[0]
    print(f"  CV AUC top-{npc} PCs = {a:.3f}")

# H1 redundancy: mean |rank corr| among the strongest metrics
top = ["global_mnps_jacobian_9d::spectral_radius_mean","global_mnps_jacobian_3d::spectral_radius_median",
       "reachability_cones::tube_d_eff_median","reachability_cones::persistence_log_det_median",
       "global_mnps_jacobian_9d::jacobian_cond_median","reachability_cones::tube_dir_entropy_norm_median"]
top = [t for t in top if t in X.columns]
R = X[top].rank().corr().abs()
iu = np.triu_indices_from(R, 1)
print(f"\nmean |Spearman| among 6 strongest metrics = {R.values[iu].mean():.2f}")
