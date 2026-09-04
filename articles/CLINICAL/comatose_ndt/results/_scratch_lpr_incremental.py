"""Does the LPR reactivity profile add orthogonal value over the run-median?"""
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score

df = pd.read_csv(r"articles/CLINICAL/comatose_ndt/results/_scratch_lpr_features_fullcohort.csv")
y = (df["cpc"] == 5).astype(int).values
react = ["episode_rate_per_min", "median_amp", "median_recovery", "frac_recovered", "median_peak_spec"]

def oof(cols, nrep=40):
    X = df[cols].values
    clf = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                        LogisticRegression(solver="liblinear", class_weight="balanced", max_iter=1000))
    rkf = RepeatedStratifiedKFold(n_splits=5, n_repeats=nrep, random_state=7)
    a = []
    for tr, te in rkf.split(X, y):
        clf.fit(X[tr], y[tr]); a.append(roc_auc_score(y[te], clf.predict_proba(X[te])[:, 1]))
    return np.mean(a), np.std(a)

for name, cols in {
    "run_median_spec only": ["run_median_spec"],
    "LPR reactivity only": react,
    "median + LPR reactivity": ["run_median_spec"] + react,
}.items():
    m, s = oof(cols)
    print(f"{m:.3f} +/- {s:.3f}   {name}  ({len(cols)} feat)")

# correlation of reactivity composite with the median (orthogonality check)
from scipy.stats import rankdata
def z(c):
    v = df[c].values; v = np.where(np.isnan(v), np.nanmedian(v), v)
    r = rankdata(v); return (r - r.mean())/(r.std()+1e-9)
react_comp = sum(z(c) for c in react)/len(react)
print(f"\nrank corr(reactivity composite, run_median_spec) = {np.corrcoef(react_comp, z('run_median_spec'))[0,1]:+.3f}")
