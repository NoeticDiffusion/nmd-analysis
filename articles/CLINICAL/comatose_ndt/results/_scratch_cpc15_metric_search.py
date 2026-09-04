"""Scratch exploration: search for an NDT metric / combination that best
separates CPC1 (good) from CPC5 (poor) in the pooled 0-12h coma cohort.

Reads the long-format patient_timebin_signal_metrics, pivots to a per-subject
0-12h feature matrix, ranks single metrics by AUC, then evaluates candidate
combined scores with repeated stratified CV (logistic regression).
"""
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RepeatedStratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score

ROOT = Path(r"articles/CLINICAL/comatose_ndt/results/mnps_summary_20260602_combined_combat_corrected_primary12h_cpc15")
LONG = ROOT / "patient_timebin_signal_metrics.csv"

df = pd.read_csv(LONG, low_memory=False)
df = df[df["time_bin"] == "0_12h"].copy()

# Keep only extreme outcomes CPC1 vs CPC5
df = df[df["cpc"].isin([1, 5])].copy()
df["y"] = (df["cpc"] == 5).astype(int)  # 1 = poor (CPC5)

# Build a unique feature key
df["feat"] = df["analysis_type"].astype(str) + "::" + df["metric"].astype(str)

# Pivot: one row per subject, columns = feat, value = value
wide = df.pivot_table(index="subject", columns="feat", values="value", aggfunc="median")
ymap = df.groupby("subject")["y"].first()
wide = wide.join(ymap)
y = wide["y"].values
X = wide.drop(columns=["y"])

print("subjects:", len(wide), "| CPC1:", (y == 0).sum(), "CPC5:", (y == 1).sum())
print("candidate features:", X.shape[1])

# Drop near-constant / all-nan, and the spurious mndm_version
keep = []
for c in X.columns:
    if "mndm_version" in c:
        continue
    col = X[c]
    if col.notna().sum() < 0.8 * len(col):
        continue
    if col.nunique(dropna=True) < 5:
        continue
    keep.append(c)
X = X[keep]
print("usable features after filtering:", X.shape[1])

# Single-metric AUC ranking (sign-agnostic)
rows = []
for c in X.columns:
    v = X[c].values
    mask = ~np.isnan(v)
    if mask.sum() < 50:
        continue
    auc = roc_auc_score(y[mask], v[mask])
    auc_use = max(auc, 1 - auc)
    rows.append((c, auc, auc_use))
rank = pd.DataFrame(rows, columns=["feat", "auc_poor", "auc_abs"]).sort_values("auc_abs", ascending=False)
pd.set_option("display.max_colwidth", 60)
print("\n=== TOP 30 SINGLE METRICS (univariate AUC) ===")
print(rank.head(30).to_string(index=False))

rank.to_csv(ROOT.parent / "_scratch_single_metric_auc.csv", index=False)
wide.to_csv(ROOT.parent / "_scratch_subject_feature_matrix.csv")
print("\nsaved single-metric ranking + subject matrix")
