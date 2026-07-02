"""
01_cross_task_mnps.py — Cross-task MNPS geometry contrast for ds004511.

Tests whether neural manifold geometry (m, d, e) differs across:
  Gambling (GG) vs. Cognitive Control (CC) vs. Rest

Statistics:
  - Friedman test (3-way repeated-measures) for each MNPS axis
  - Pairwise Wilcoxon signed-rank (post-hoc, BH-FDR corrected)
  - Effect size: matched-pairs Cohen's d
  - Network breakdown: repeat per network label

Outputs:
  results/01_cross_task_mnps/
    mnps_cross_task_global.csv   — subject × task MNPS medians (global)
    mnps_friedman.csv            — Friedman test results
    mnps_pairwise.csv            — pairwise Wilcoxon + FDR
    mnps_network_pairwise.csv    — network-stratified pairwise tests
    block_jacobian_friedman.csv  — Frobenius/rotation Friedman across tasks
"""
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "nmd-analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from ds004511_support import (
    MNPS_COLS,
    NETWORKS,
    TASK_DISPLAY,
    TASK_ORDER,
    bh_fdr,
    friedman_test,
    load_block_jacobians,
    load_regional_mnps,
    make_results_subdir,
    wilcoxon_paired,
)

OUT = make_results_subdir("01_cross_task_mnps")

# ──────────────────────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────────────────────
print("Loading regional MNPS ...")
reg = load_regional_mnps()
print(f"  Shape: {reg.shape}  tasks: {reg['task_label'].unique()}")

# ──────────────────────────────────────────────────────────────────────────────
# A. Global MNPS (aggregate across networks)
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- A. Global MNPS (network-averaged) ---")
mnps_cols = [c for c in MNPS_COLS if c in reg.columns]
global_mnps = (
    reg.groupby(["subject_id", "task_label"])[mnps_cols]
    .mean()
    .reset_index()
)
# Wide format: one row per subject
wide = global_mnps.pivot_table(
    index="subject_id", columns="task_label", values=mnps_cols
)
wide.columns = [f"{col}_{task}" for col, task in wide.columns]
wide.to_csv(OUT / "mnps_cross_task_global.csv")
print(f"  Global MNPS table: {wide.shape}")

# Descriptive stats
for col in mnps_cols:
    print(f"\n  {col}:")
    for task in TASK_ORDER:
        vals = global_mnps.loc[global_mnps["task_label"] == task, col].dropna()
        print(f"    {TASK_DISPLAY.get(task, task)}: median={vals.median():.4f}  IQR=[{vals.quantile(.25):.4f}, {vals.quantile(.75):.4f}]  n={len(vals)}")

# ──────────────────────────────────────────────────────────────────────────────
# B. Friedman test across 3 tasks
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- B. Friedman test (GG, CC, Rest) ---")
friedman_rows = []
for col in mnps_cols:
    # Need subjects present in all 3 tasks
    pivot = global_mnps.pivot_table(index="subject_id", columns="task_label", values=col)
    common_subs = pivot.dropna().index
    groups = [pivot.loc[common_subs, t].values for t in TASK_ORDER if t in pivot.columns]
    if len(groups) < 3:
        continue
    chi2, p = friedman_test(*groups)
    print(f"  {col}: chi2={chi2:.3f}  p={p:.4f}  n={len(common_subs)}")
    friedman_rows.append({"mnps_axis": col, "friedman_chi2": chi2, "p": p, "n_subjects": len(common_subs)})

friedman_df = pd.DataFrame(friedman_rows)
friedman_df["p_fdr"] = bh_fdr(friedman_df["p"].fillna(1).values)
friedman_df.to_csv(OUT / "mnps_friedman.csv", index=False)

# ──────────────────────────────────────────────────────────────────────────────
# C. Pairwise Wilcoxon signed-rank (post-hoc)
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- C. Pairwise Wilcoxon (post-hoc) ---")
pairs = list(combinations(TASK_ORDER, 2))
pair_rows = []
for col in mnps_cols:
    pivot = global_mnps.pivot_table(index="subject_id", columns="task_label", values=col)
    for t1, t2 in pairs:
        if t1 not in pivot.columns or t2 not in pivot.columns:
            continue
        common = pivot[[t1, t2]].dropna().index
        a = pivot.loc[common, t1].values
        b = pivot.loc[common, t2].values
        stat, p, n, d = wilcoxon_paired(a, b)
        print(f"  {col}: {t1} vs {t2}  stat={stat:.1f}  p={p:.4f}  d={d:.3f}  n={n}")
        pair_rows.append({
            "mnps_axis": col, "task1": t1, "task2": t2,
            "wilcoxon_stat": stat, "p": p, "cohen_d": d, "n_pairs": n,
        })

pair_df = pd.DataFrame(pair_rows)
pair_df["p_fdr"] = bh_fdr(pair_df["p"].fillna(1).values)
pair_df["sig_fdr05"] = pair_df["p_fdr"] < 0.05
pair_df.to_csv(OUT / "mnps_pairwise.csv", index=False)
print(f"\n  Pairs surviving FDR 5%: {pair_df['sig_fdr05'].sum()} / {len(pair_df)}")

# ──────────────────────────────────────────────────────────────────────────────
# D. Network-stratified pairwise tests
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- D. Network-stratified pairwise Wilcoxon ---")
net_pair_rows = []
for net in NETWORKS:
    net_data = reg[reg["network_label"] == net].copy()
    for col in mnps_cols:
        pivot = net_data.pivot_table(index="subject_id", columns="task_label", values=col)
        for t1, t2 in pairs:
            if t1 not in pivot.columns or t2 not in pivot.columns:
                continue
            common = pivot[[t1, t2]].dropna().index
            if len(common) < 5:
                continue
            a = pivot.loc[common, t1].values
            b = pivot.loc[common, t2].values
            stat, p, n, d = wilcoxon_paired(a, b)
            net_pair_rows.append({
                "network": net, "mnps_axis": col, "task1": t1, "task2": t2,
                "wilcoxon_stat": stat, "p": p, "cohen_d": d, "n_pairs": n,
            })

net_pair_df = pd.DataFrame(net_pair_rows)
if len(net_pair_df):
    net_pair_df["p_fdr"] = bh_fdr(net_pair_df["p"].fillna(1).values)
    net_pair_df["sig_fdr05"] = net_pair_df["p_fdr"] < 0.05
    net_pair_df.to_csv(OUT / "mnps_network_pairwise.csv", index=False)
    print(f"  Network tests: {len(net_pair_df)} total, {net_pair_df['sig_fdr05'].sum()} survive FDR 5%")
    sig_net = net_pair_df[net_pair_df["sig_fdr05"]].sort_values("p_fdr")
    if len(sig_net):
        print(sig_net[["network", "mnps_axis", "task1", "task2", "cohen_d", "p_fdr"]].to_string(index=False))

# ──────────────────────────────────────────────────────────────────────────────
# E. Block Jacobian cross-task
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- E. Block Jacobian cross-task contrast ---")
bjac = load_block_jacobians()
bjac_cols = ["block_frobenius_mean", "block_trace_mean", "block_anisotropy_mean", "c_rot_mean"]
avail_bj = [c for c in bjac_cols if c in bjac.columns]
print(f"  Block Jacobian columns: {avail_bj}")

bj_global = (
    bjac.groupby(["subject_id", "task_label"])[avail_bj]
    .mean()
    .reset_index()
)
bj_friedman_rows = []
for col in avail_bj:
    pivot = bj_global.pivot_table(index="subject_id", columns="task_label", values=col)
    common = pivot.dropna().index
    groups = [pivot.loc[common, t].values for t in TASK_ORDER if t in pivot.columns]
    if len(groups) < 3:
        continue
    chi2, p = friedman_test(*groups)
    print(f"  {col}: chi2={chi2:.3f}  p={p:.4f}  n={len(common)}")
    bj_friedman_rows.append({"metric": col, "friedman_chi2": chi2, "p": p, "n_subjects": len(common)})

bj_fried_df = pd.DataFrame(bj_friedman_rows)
if len(bj_fried_df):
    bj_fried_df["p_fdr"] = bh_fdr(bj_fried_df["p"].fillna(1).values)
    bj_fried_df.to_csv(OUT / "block_jacobian_friedman.csv", index=False)

# Pairwise Wilcoxon for Frobenius
print("\n  Pairwise Wilcoxon for block_frobenius_mean:")
bj_pair_rows = []
for col in avail_bj:
    pivot = bj_global.pivot_table(index="subject_id", columns="task_label", values=col)
    for t1, t2 in pairs:
        if t1 not in pivot.columns or t2 not in pivot.columns:
            continue
        common = pivot[[t1, t2]].dropna().index
        a = pivot.loc[common, t1].values
        b = pivot.loc[common, t2].values
        stat, p, n, d = wilcoxon_paired(a, b)
        print(f"    {col}: {t1} vs {t2}  p={p:.4f}  d={d:.3f}")
        bj_pair_rows.append({
            "metric": col, "task1": t1, "task2": t2,
            "wilcoxon_stat": stat, "p": p, "cohen_d": d, "n_pairs": n,
        })

if bj_pair_rows:
    bj_pair_df = pd.DataFrame(bj_pair_rows)
    bj_pair_df["p_fdr"] = bh_fdr(bj_pair_df["p"].fillna(1).values)
    bj_pair_df.to_csv(OUT / "block_jacobian_pairwise.csv", index=False)

print(f"\n=== Cross-task MNPS contrast complete ===")
print(f"Outputs in: {OUT}")
