"""
09_conventional_eeg_baseline.py — Conventional-EEG baseline comparison for the
GG vs. CC MNJ Frobenius effect (peer_review/pr_01.md, finding #6).

A hard reviewer's obvious question: would a simple, well-known EEG summary
statistic (band power, band ratios, alpha peak frequency, spectral/permutation
entropy, Hjorth complexity) show a GG-vs-CC dissociation of comparable size to
the MNJ Frobenius-norm effect, without needing the Jacobian machinery at all?

This script answers that directly using the `eeg_conventional_*` feature
columns added to the NMD ingestion config (`conventional_eeg: {enabled: true,
packs: [tier1, complexity]}`) and computed in the same pipeline run as the
MNPS/MNJ geometry, so the comparison uses byte-identical epochs/subjects.

Method: for every `eeg_conventional_*` column, run the same paired Wilcoxon
signed-rank / Cohen's d_z contrast used for the primary MNJ metrics (Script 05),
on the same intersection sample, and report effect sizes side-by-side with the
MNJ Frobenius-norm and spectral-radius effects for direct comparison.

Outputs:
  results/09_conventional_eeg_baseline/
    conventional_eeg_wilcoxon.csv    — GG vs CC (+ GG vs Rest, CC vs Rest)
                                        contrasts for every conventional column
    conventional_vs_mnj_summary.csv  — side-by-side comparison table
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "nmd-analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from ds004511_support import (
    RESULTS_DIR,
    TASK_ORDER,
    bh_fdr,
    load_features,
    make_results_subdir,
    subject_task_medians,
    wilcoxon_paired,
)

OUT = make_results_subdir("09_conventional_eeg_baseline")

PRIMARY_PAIRS = [
    ("gambling", "cognitive_control"),
    ("gambling", "rest"),
    ("cognitive_control", "rest"),
]

# ──────────────────────────────────────────────────────────────────────────────
# Load features and discover conventional-EEG columns
# ──────────────────────────────────────────────────────────────────────────────
print("Loading epoch-level features ...")
feat = load_features()

conv_cols = sorted(c for c in feat.columns if c.startswith("eeg_conventional_"))
if not conv_cols:
    raise SystemExit(
        "No eeg_conventional_* columns found in features.parquet. "
        "Re-run the NMD pipeline with conventional_eeg.enabled=true "
        "(mndm/config/config_ingest_ds004511.yaml) before running this script."
    )
print(f"Found {len(conv_cols)} conventional-EEG columns: {conv_cols}")

# Restrict to the same intersection sample used throughout the article
# (subjects with valid epochs in all 3 tasks), for direct comparability.
prior_run_dir = RESULTS_DIR / "ds004511_20260701"
intersection_path = prior_run_dir / "05_mnj_confound_audit" / "intersection_sample.csv"
if intersection_path.exists():
    intersection_subs = sorted(pd.read_csv(intersection_path)["subject_id"].unique())
    feat = feat[feat["subject_id"].isin(intersection_subs)]
    print(f"Restricted to intersection sample: {len(intersection_subs)} subjects")
else:
    print("WARNING: intersection_sample.csv not found; using all available subjects.")

meds = subject_task_medians(feat, conv_cols)

# ──────────────────────────────────────────────────────────────────────────────
# Paired Wilcoxon contrasts for every conventional-EEG column
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- Conventional-EEG GG/CC/Rest contrasts ---")
rows = []
for col in conv_cols:
    pivot = meds.pivot_table(index="subject_id", columns="task_label", values=col)
    for t1, t2 in PRIMARY_PAIRS:
        if t1 not in pivot.columns or t2 not in pivot.columns:
            continue
        common = pivot[[t1, t2]].dropna().index
        a = pivot.loc[common, t1].values
        b = pivot.loc[common, t2].values
        stat, p, n, d = wilcoxon_paired(a, b)
        rows.append({
            "feature": col, "task1": t1, "task2": t2,
            "wilcoxon_stat": stat, "p": p, "cohen_dz": d, "n_pairs": n,
        })

res = pd.DataFrame(rows)
res["p_fdr"] = bh_fdr(res["p"].fillna(1).values)
res["sig_fdr05"] = res["p_fdr"] < 0.05
res.to_csv(OUT / "conventional_eeg_wilcoxon.csv", index=False)

print(f"Surviving FDR 5%: {res['sig_fdr05'].sum()} / {len(res)}")
gg_cc = res[(res["task1"] == "gambling") & (res["task2"] == "cognitive_control")].copy()
gg_cc = gg_cc.sort_values("cohen_dz", key=lambda s: s.abs(), ascending=False)
print("\nGG vs CC, sorted by |Cohen's d_z|:")
print(gg_cc[["feature", "cohen_dz", "p", "p_fdr", "sig_fdr05"]].to_string(index=False))

# ──────────────────────────────────────────────────────────────────────────────
# Side-by-side comparison with the primary MNJ effects
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- Comparison with primary MNJ GG vs CC effects ---")
mnj_gg_cc_path = prior_run_dir / "05_mnj_confound_audit" / "mnj_intersection_wilcoxon.csv"
comparison_rows = []
if mnj_gg_cc_path.exists():
    mnj_res = pd.read_csv(mnj_gg_cc_path)
    mnj_gg_cc = mnj_res[
        (mnj_res["task1"] == "gambling") & (mnj_res["task2"] == "cognitive_control")
    ]
    for _, r in mnj_gg_cc.iterrows():
        comparison_rows.append({
            "family": "MNJ", "metric": r["mnj_metric"],
            "cohen_dz": r["cohen_d"], "p": r["p"], "p_fdr": r["p_fdr"],
            "sig_fdr05": r["sig_fdr05"],
        })
else:
    print("WARNING: mnj_intersection_wilcoxon.csv not found; MNJ comparison rows omitted.")

for _, r in gg_cc.iterrows():
    comparison_rows.append({
        "family": "conventional_eeg", "metric": r["feature"],
        "cohen_dz": r["cohen_dz"], "p": r["p"], "p_fdr": r["p_fdr"],
        "sig_fdr05": r["sig_fdr05"],
    })

comp_df = pd.DataFrame(comparison_rows).sort_values(
    "cohen_dz", key=lambda s: s.abs(), ascending=False
)
comp_df.to_csv(OUT / "conventional_vs_mnj_summary.csv", index=False)
print(comp_df.to_string(index=False))

# ──────────────────────────────────────────────────────────────────────────────
# Interpretation summary
# ──────────────────────────────────────────────────────────────────────────────
print("\n=== Interpretation ===")
max_conv_d = gg_cc["cohen_dz"].abs().max() if len(gg_cc) else np.nan
mnj_frob_row = comp_df[(comp_df["family"] == "MNJ") & (comp_df["metric"] == "frobenius_norm")]
mnj_frob_d = float(mnj_frob_row["cohen_dz"].abs().iloc[0]) if len(mnj_frob_row) else np.nan
if np.isfinite(max_conv_d) and np.isfinite(mnj_frob_d):
    if max_conv_d < mnj_frob_d:
        print(f"Largest conventional-EEG |d_z| ({max_conv_d:.3f}) is smaller than the "
              f"MNJ Frobenius effect ({mnj_frob_d:.3f}): the MNJ dissociation is not "
              f"fully recoverable from simple band-power/complexity summaries alone.")
    else:
        print(f"WARNING: at least one conventional-EEG feature (|d_z|={max_conv_d:.3f}) "
              f"matches or exceeds the MNJ Frobenius effect ({mnj_frob_d:.3f}). "
              f"Re-examine whether MNJ is adding value beyond this simpler metric.")

print(f"\n=== Conventional-EEG baseline comparison complete ===")
print(f"Outputs: {OUT}")
