"""
02_eap_physio_coupling.py — Embodied Anchoring Principle coupling test for ds004511.

Core EAP hypothesis: Interoceptive anchors (resp_anchor_index, HRV RMSSD,
RSA amplitude) correlate with neural flow geometry (Jacobian Frobenius,
MNPS m/d/e) within each task condition.

Analyses:
  A. Subject-level median physio × MNPS + Block-Jacobian (Spearman), FDR
  B. Within-task (GG vs CC vs Rest): does coupling strength differ?
  C. Specificity: is resp_anchor_index a stronger predictor than HRV/RSA alone?
     Partial Spearman (resp controlling for HRV, and vice versa)
  D. Network-specific coupling: resp_anchor × Frobenius per network
  E. Leave-one-subject-out (LOOSO) for top correlations
  F. Bootstrap 95% CI for top correlations

Outputs:
  results/02_eap_physio_coupling/
    coupling_global.csv       — full Spearman table, FDR corrected
    coupling_per_task.csv     — per-task Spearman
    coupling_partial.csv      — partial Spearman (resp|HRV, HRV|resp)
    coupling_per_network.csv  — network-specific resp×Frobenius
    coupling_looso.csv        — leave-one-out stability for top hits
    coupling_bootstrap.csv    — bootstrap CIs for top hits
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "nmd-analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from ds004511_support import (
    CARDIORESP_COLS,
    HRV_COLS,
    MNPS_COLS,
    NETWORKS,
    RESP_ANCHOR_COLS,
    TASK_DISPLAY,
    TASK_ORDER,
    bh_fdr,
    load_block_jacobians,
    load_features,
    load_regional_mnps,
    make_results_subdir,
    spearman_r,
    subject_task_medians,
)

OUT = make_results_subdir("02_eap_physio_coupling")
RNG = np.random.default_rng(42)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def partial_spearman(x, y, z):
    """Partial Spearman r of x~y controlling for z."""
    df = pd.DataFrame({"x": x, "y": y, "z": z}).dropna()
    if len(df) < 6:
        return np.nan, np.nan, len(df)
    rx = scipy_stats.rankdata(df["x"])
    ry = scipy_stats.rankdata(df["y"])
    rz = scipy_stats.rankdata(df["z"])
    r_xy = float(np.corrcoef(rx, ry)[0, 1])
    r_xz = float(np.corrcoef(rx, rz)[0, 1])
    r_yz = float(np.corrcoef(ry, rz)[0, 1])
    denom = np.sqrt(max(0, (1 - r_xz**2) * (1 - r_yz**2)))
    if denom < 1e-10:
        return np.nan, np.nan, len(df)
    r_p = (r_xy - r_xz * r_yz) / denom
    n = len(df)
    t = r_p * np.sqrt(max(0, (n - 3) / max(1e-10, 1 - r_p**2)))
    p = 2 * scipy_stats.t.sf(abs(t), df=max(1, n - 3))
    return float(r_p), float(p), n


def bootstrap_spearman(x, y, n_boot: int = 2000) -> tuple:
    """Bootstrap 95% CI for Spearman r."""
    df = pd.DataFrame({"x": x, "y": y}).dropna()
    n = len(df)
    if n < 5:
        return np.nan, np.nan, np.nan
    boots = []
    for _ in range(n_boot):
        idx = RNG.integers(0, n, n)
        r, _ = scipy_stats.spearmanr(df["x"].iloc[idx], df["y"].iloc[idx])
        boots.append(r)
    boots = np.array(boots)
    return float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5)), float(np.std(boots))


# ──────────────────────────────────────────────────────────────────────────────
# Load and prepare data
# ──────────────────────────────────────────────────────────────────────────────
print("Loading features ...")
feat = load_features()
print(f"  Epochs: {len(feat):,}  subjects: {feat['subject_id'].nunique()}")

print("Loading regional MNPS ...")
reg = load_regional_mnps()

print("Loading block Jacobians ...")
bjac = load_block_jacobians()

# Physio columns available
physio_cols = [
    "resp_anchor_index", "resp_regular_index", "resp_phase_consistency",
    "resp_rate_bpm", "ecg_hrv_rmssd_ms", "ecg_hrv_sdnn_ms",
    "cardioresp_rsa_amplitude", "cardioresp_coupling_index",
    "eog_eye_stability_index",
]
avail_physio = [c for c in physio_cols if c in feat.columns]

# Subject × task medians for physio (only resp-OK epochs for resp metrics)
print("\nComputing subject-task physio medians ...")
resp_phys = [c for c in avail_physio if c.startswith("resp_anchor") or c.startswith("resp_regular") or c.startswith("resp_phase") or c.startswith("resp_rate")]
non_resp_phys = [c for c in avail_physio if c not in resp_phys]

# Resp features: use QC-OK epochs only
feat_resp_ok = feat[feat["qc_ok_resp"] == 1]
sub_physio_resp = subject_task_medians(feat_resp_ok, resp_phys)

# Other physio features: use all epochs
sub_physio_other = subject_task_medians(feat, non_resp_phys)

sub_physio = sub_physio_resp.merge(sub_physio_other, on=["subject_id", "task_label"], how="outer")

# Neural geometry: network-averaged MNPS
mnps_cols = [c for c in MNPS_COLS if c in reg.columns]
sub_mnps = (
    reg.groupby(["subject_id", "task_label"])[mnps_cols]
    .mean()
    .reset_index()
)

# Block Jacobian global (network-averaged)
bjac_cols = ["block_frobenius_mean", "block_trace_mean", "c_rot_mean", "block_anisotropy_mean"]
avail_bj = [c for c in bjac_cols if c in bjac.columns]
sub_bjac = (
    bjac.groupby(["subject_id", "task_label"])[avail_bj]
    .mean()
    .reset_index()
)

# Merge all into one frame
sub = sub_physio.merge(sub_mnps, on=["subject_id", "task_label"], how="inner")
sub = sub.merge(sub_bjac, on=["subject_id", "task_label"], how="left")
print(f"  Combined subject-task table: {sub.shape}")

# ──────────────────────────────────────────────────────────────────────────────
# A. Global coupling: all physio × all geometry metrics (pooled across tasks)
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- A. Global coupling (pooled tasks, N=subject×task rows) ---")
geom_cols = mnps_cols + avail_bj
rows = []
for phys in avail_physio:
    for geom in geom_cols:
        if phys not in sub.columns or geom not in sub.columns:
            continue
        r, p = spearman_r(sub[phys], sub[geom])
        rows.append({"physio": phys, "geometry": geom, "spearman_r": r, "p": p,
                     "n": int(sub[[phys, geom]].dropna().shape[0])})

global_df = pd.DataFrame(rows)
global_df["p_fdr"] = bh_fdr(global_df["p"].fillna(1).values)
global_df["sig_fdr05"] = global_df["p_fdr"] < 0.05
global_df.to_csv(OUT / "coupling_global.csv", index=False)

sig_global = global_df[global_df["sig_fdr05"]].sort_values("p_fdr")
print(f"  {len(sig_global)} pairs survive FDR 5% (of {len(global_df)})")
if len(sig_global):
    print(sig_global[["physio", "geometry", "spearman_r", "p_fdr"]].to_string(index=False))

# ──────────────────────────────────────────────────────────────────────────────
# B. Per-task coupling
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- B. Per-task coupling ---")
task_rows = []
for task in TASK_ORDER:
    sub_t = sub[sub["task_label"] == task]
    for phys in ["resp_anchor_index", "ecg_hrv_rmssd_ms", "cardioresp_rsa_amplitude"]:
        for geom in ["block_frobenius_mean", "c_rot_mean", "m_median", "d_median", "e_median"]:
            if phys not in sub_t.columns or geom not in sub_t.columns:
                continue
            r, p = spearman_r(sub_t[phys], sub_t[geom])
            n = int(sub_t[[phys, geom]].dropna().shape[0])
            task_rows.append({"task": task, "physio": phys, "geometry": geom,
                              "spearman_r": r, "p": p, "n": n})

task_df = pd.DataFrame(task_rows)
task_df["p_fdr"] = bh_fdr(task_df["p"].fillna(1).values)
task_df["sig_fdr05"] = task_df["p_fdr"] < 0.05
task_df.to_csv(OUT / "coupling_per_task.csv", index=False)

print("  Key results:")
for task in TASK_ORDER:
    t_sub = task_df[task_df["task"] == task]
    sig = t_sub[t_sub["sig_fdr05"]]
    print(f"  {TASK_DISPLAY.get(task, task)}: {len(sig)} pairs survive FDR 5%")
    if len(sig):
        print(sig[["physio", "geometry", "spearman_r", "p_fdr"]].to_string(index=False))
    # Always print resp_anchor × frobenius regardless of significance
    row = t_sub[(t_sub["physio"] == "resp_anchor_index") & (t_sub["geometry"] == "block_frobenius_mean")]
    if len(row):
        r = row.iloc[0]
        print(f"    resp_anchor_index x block_frobenius_mean: r={r['spearman_r']:.3f}  p={r['p']:.4f}  p_fdr={r['p_fdr']:.4f}  n={r['n']}")

# ──────────────────────────────────────────────────────────────────────────────
# C. Partial Spearman: resp_anchor controlling for HRV, and HRV controlling for resp
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- C. Partial Spearman: resp_anchor x geometry | HRV ---")
part_rows = []
for task in TASK_ORDER:
    sub_t = sub[sub["task_label"] == task]
    for geom in ["block_frobenius_mean", "c_rot_mean", "m_median"]:
        if geom not in sub_t.columns:
            continue
        # resp | HRV
        r_resp_hrv, p_resp_hrv, n = partial_spearman(
            sub_t["resp_anchor_index"], sub_t[geom], sub_t["ecg_hrv_rmssd_ms"]
        )
        # HRV | resp
        r_hrv_resp, p_hrv_resp, n2 = partial_spearman(
            sub_t["ecg_hrv_rmssd_ms"], sub_t[geom], sub_t["resp_anchor_index"]
        )
        part_rows.append({
            "task": task, "geometry": geom,
            "r_resp_controlling_hrv": r_resp_hrv, "p_resp_controlling_hrv": p_resp_hrv,
            "r_hrv_controlling_resp": r_hrv_resp, "p_hrv_controlling_resp": p_hrv_resp,
            "n": n,
        })
        print(f"  {task}/{geom}: resp|HRV: r={r_resp_hrv:.3f} p={p_resp_hrv:.4f}  "
              f"HRV|resp: r={r_hrv_resp:.3f} p={p_hrv_resp:.4f}")

part_df = pd.DataFrame(part_rows)
part_df.to_csv(OUT / "coupling_partial.csv", index=False)

# ──────────────────────────────────────────────────────────────────────────────
# D. Network-specific resp_anchor × Frobenius
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- D. Network-specific resp_anchor x Frobenius ---")
net_rows = []
for net in NETWORKS:
    bjac_net = bjac[bjac["network_label"] == net].copy()
    sub_bjac_net = bjac_net.groupby(["subject_id", "task_label"])["block_frobenius_mean"].mean().reset_index()
    sub_net = sub_physio.merge(sub_bjac_net, on=["subject_id", "task_label"])
    for task in TASK_ORDER:
        sub_nt = sub_net[sub_net["task_label"] == task]
        r, p = spearman_r(sub_nt["resp_anchor_index"], sub_nt["block_frobenius_mean"])
        n = int(sub_nt[["resp_anchor_index", "block_frobenius_mean"]].dropna().shape[0])
        net_rows.append({"network": net, "task": task, "spearman_r": r, "p": p, "n": n})

net_df = pd.DataFrame(net_rows)
net_df["p_fdr"] = bh_fdr(net_df["p"].fillna(1).values)
net_df["sig_fdr05"] = net_df["p_fdr"] < 0.05
net_df.to_csv(OUT / "coupling_per_network.csv", index=False)
print(net_df[["network", "task", "spearman_r", "p", "p_fdr", "sig_fdr05"]].to_string(index=False))

# ──────────────────────────────────────────────────────────────────────────────
# E. Leave-one-subject-out (LOOSO) for top hits
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- E. LOOSO stability for top correlations ---")
top_hits = [
    ("resp_anchor_index", "block_frobenius_mean", "gambling"),
    ("resp_anchor_index", "block_frobenius_mean", "cognitive_control"),
    ("resp_anchor_index", "c_rot_mean", "gambling"),
    ("ecg_hrv_rmssd_ms", "block_frobenius_mean", "gambling"),
]
looso_rows = []
for phys, geom, task in top_hits:
    sub_t = sub[(sub["task_label"] == task) & sub[phys].notna() & sub[geom].notna()]
    subs = sub_t["subject_id"].unique()
    loo_rs = []
    for leave_out in subs:
        sub_loo = sub_t[sub_t["subject_id"] != leave_out]
        r, _ = spearman_r(sub_loo[phys], sub_loo[geom])
        loo_rs.append(r)
    loo_rs = np.array(loo_rs)
    full_r, full_p = spearman_r(sub_t[phys], sub_t[geom])
    print(f"  {task} / {phys} x {geom}: full_r={full_r:.3f}  loo_mean={np.nanmean(loo_rs):.3f}  loo_min={np.nanmin(loo_rs):.3f}  loo_max={np.nanmax(loo_rs):.3f}")
    looso_rows.append({
        "task": task, "physio": phys, "geometry": geom,
        "full_spearman_r": full_r, "full_p": full_p,
        "loo_mean_r": float(np.nanmean(loo_rs)),
        "loo_min_r": float(np.nanmin(loo_rs)),
        "loo_max_r": float(np.nanmax(loo_rs)),
        "loo_sign_consistent": bool(np.all(loo_rs * full_r > 0)),
        "n": len(subs),
    })

looso_df = pd.DataFrame(looso_rows)
looso_df.to_csv(OUT / "coupling_looso.csv", index=False)

# ──────────────────────────────────────────────────────────────────────────────
# F. Bootstrap CIs for top correlations
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- F. Bootstrap 95% CI for top correlations ---")
boot_rows = []
for phys, geom, task in top_hits:
    sub_t = sub[(sub["task_label"] == task)]
    r, p = spearman_r(sub_t[phys], sub_t[geom])
    ci_lo, ci_hi, se = bootstrap_spearman(sub_t[phys], sub_t[geom])
    print(f"  {task} / {phys} x {geom}: r={r:.3f}  95% CI [{ci_lo:.3f}, {ci_hi:.3f}]  SE={se:.3f}")
    boot_rows.append({"task": task, "physio": phys, "geometry": geom,
                      "spearman_r": r, "p": p, "ci_lo": ci_lo, "ci_hi": ci_hi, "se": se})

boot_df = pd.DataFrame(boot_rows)
boot_df.to_csv(OUT / "coupling_bootstrap.csv", index=False)

print(f"\n=== EAP coupling analysis complete ===")
print(f"Outputs in: {OUT}")
