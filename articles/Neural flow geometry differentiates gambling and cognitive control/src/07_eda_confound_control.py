"""
07_eda_confound_control.py — EDA confound control for the primary
GG > CC Frobenius norm effect.

Science lead requirement (sciencelead/002.md, "one remaining analysis before
final draft"): confirm that the GG > CC MNJ Frobenius effect survives control
for tonic EDA, extending the physio confound table from Script 05 (which
covered HR, respiration rate, resp_anchor_index, EOG blink rate) with the
EDA tonic SCL feature extracted in Script 06.

Method: identical to Script 05 Part G. For each intersection-sample subject
(N=42), compute GG-minus-CC differences in:
  - MNJ Frobenius norm (from subject_mnj_summary.csv, Script 03)
  - tonic EDA SCL (from eda_features.parquet, Script 06)
Then test the plain Spearman correlation between the two difference series,
and reproduce the full multi-confound partial-correlation table
(HR, resp_rate, resp_anchor, EOG blink, EDA tonic) for direct comparison
with the Script 05 table.

Outputs:
  results/07_eda_confound_control/
    eda_confound_partial.csv       — EDA-specific confound test
    full_confound_table.csv        — combined 5-confound table (05 + EDA)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "nmd-analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from ds004511_support import (
    RESULTS_DIR,
    bh_fdr,
    load_features,
    make_results_subdir,
    spearman_r,
)

OUT = make_results_subdir("07_eda_confound_control")

# ──────────────────────────────────────────────────────────────────────────────
# Load intersection sample + MNJ Frobenius (Script 03/05 outputs)
# ──────────────────────────────────────────────────────────────────────────────

prior_run_dir = RESULTS_DIR / "ds004511_20260701"
intersection = pd.read_csv(prior_run_dir / "05_mnj_confound_audit" / "intersection_sample.csv")
intersection_subs = sorted(intersection["subject_id"].unique())
print(f"Intersection sample: {len(intersection_subs)} subjects")

mnj_summary = pd.read_csv(prior_run_dir / "03_mnj_reachability" / "subject_mnj_summary.csv")
frob_pivot = (
    mnj_summary[mnj_summary["subject_id"].isin(intersection_subs)]
    .pivot_table(index="subject_id", columns="task_label", values="frobenius_norm_median")
)
frob_diff = frob_pivot["gambling"] - frob_pivot["cognitive_control"]
print(f"  Frobenius GG-CC diff: n={frob_diff.notna().sum()}, "
      f"mean={frob_diff.mean():.4f}, median={frob_diff.median():.4f}")

# ──────────────────────────────────────────────────────────────────────────────
# Load EDA features (Script 06 output) and compute GG-CC tonic SCL diff
# ──────────────────────────────────────────────────────────────────────────────

eda_path = prior_run_dir / "06_eda_extraction" / "eda_features.parquet"
eda = pd.read_parquet(eda_path)
eda_ok = eda[eda["qc_ok_eda"] == 1]

eda_pivot = (
    eda_ok[eda_ok["subject_id"].isin(intersection_subs)]
    .groupby(["subject_id", "task_label"])["eda_tonic_scl"]
    .median()
    .unstack()
)
eda_diff = eda_pivot["gambling"] - eda_pivot["cognitive_control"]
print(f"  EDA tonic SCL GG-CC diff: n={eda_diff.notna().sum()}, "
      f"mean={eda_diff.mean():.4f}, median={eda_diff.median():.4f}")

# ──────────────────────────────────────────────────────────────────────────────
# Test 1: plain Spearman, EDA diff vs Frobenius diff
# ──────────────────────────────────────────────────────────────────────────────

r_eda, p_eda = spearman_r(eda_diff, frob_diff)
n_common = pd.DataFrame({"eda": eda_diff, "frob": frob_diff}).dropna().shape[0]
print(f"\nSpearman(EDA_diff, Frobenius_diff): r={r_eda:.3f}, p={p_eda:.4f}, n={n_common}")

eda_row = pd.DataFrame([{
    "confound": "eda_tonic_scl",
    "r_confound_diff_x_frob_diff": r_eda,
    "p": p_eda,
    "n": n_common,
}])
eda_row.to_csv(OUT / "eda_confound_partial.csv", index=False)

# ──────────────────────────────────────────────────────────────────────────────
# Combine with Script 05's confound table for a single reviewer-facing table
# ──────────────────────────────────────────────────────────────────────────────

prior_confounds = pd.read_csv(prior_run_dir / "05_mnj_confound_audit" / "mnj_physio_confound_partial.csv")
prior_confounds = prior_confounds[["confound", "r_confound_diff_x_frob_diff", "p"]].copy()

combined = pd.concat([prior_confounds, eda_row[["confound", "r_confound_diff_x_frob_diff", "p"]]],
                      ignore_index=True)
combined["p_fdr"] = bh_fdr(combined["p"].fillna(1).values)
combined["sig_fdr05"] = combined["p_fdr"] < 0.05
combined.to_csv(OUT / "full_confound_table.csv", index=False)

print("\n=== Combined confound table (HR, resp_rate, resp_anchor, EOG blink, EDA tonic) ===")
print(combined.to_string(index=False))

# ──────────────────────────────────────────────────────────────────────────────
# Interpretation summary
# ──────────────────────────────────────────────────────────────────────────────

print("\n=== Interpretation ===")
if p_eda > 0.05 or (combined.loc[combined["confound"] == "eda_tonic_scl", "sig_fdr05"].values[0] == False):
    print("EDA does NOT confound the GG>CC Frobenius effect (no significant")
    print("association between EDA difference and Frobenius difference after FDR).")
    print("This is consistent with the direct EDA GG-vs-CC null (d=-0.08, p=0.51,")
    print("Script 06) and completes the science lead's required confound table.")
else:
    print("WARNING: EDA difference shows a significant association with Frobenius")
    print("difference. Further investigation required before finalizing the claim.")

print(f"\n=== EDA confound control complete ===")
print(f"Outputs: {OUT}")
