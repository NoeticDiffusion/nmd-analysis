"""
03_mnj_reachability.py — Epoch-level MNJ and Reachability extraction for ds004511.

For each H5 session:
  1. Load epoch Jacobians from jacobian_subject_anchored (3D, cohort-normalized)
  2. Compute per-epoch MNJ metrics: frobenius_norm, rotation_norm, trace,
     spectral_radius, rotational_power, aci, mdr
  3. Attempt reachability extraction via summarize_reachability_h5 or manual k-NN
  4. Merge with physio features from features.parquet by window_start
  5. Subject-session level: median per task
  6. Within-session: epoch-level resp_anchor_index × MNJ coupling

Outputs:
  results/03_mnj_reachability/
    subject_mnj_summary.csv       — subject × task MNJ medians
    mnj_cross_task_wilcoxon.csv   — pairwise MNJ Wilcoxon across tasks
    mnj_resp_coupling.csv         — Spearman (session-level medians)
    mnj_resp_coupling_within.csv  — per-epoch Spearman per session, aggregated
    mnj_resp_looso.csv            — LOOSO for top correlations
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "nmd-analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import warnings
import h5py
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from ds004511_support import (
    NETWORKS,
    TASK_DISPLAY,
    TASK_ORDER,
    bh_fdr,
    load_features,
    make_results_subdir,
    iter_h5_paths,
    spearman_r,
    wilcoxon_paired,
)
from itertools import combinations

OUT = make_results_subdir("03_mnj_reachability")

# ──────────────────────────────────────────────────────────────────────────────
# MNJ computation helpers
# ──────────────────────────────────────────────────────────────────────────────

def compute_mnj_metrics_from_jacobians(J: np.ndarray) -> dict:
    """Compute MNJ metrics from a batch of (N, d, d) Jacobians.
    Returns dict of 1D arrays of length N.
    """
    N, d, _ = J.shape
    frob = np.linalg.norm(J, ord="fro", axis=(1, 2))

    J_sym = 0.5 * (J + J.transpose(0, 2, 1))
    J_anti = 0.5 * (J - J.transpose(0, 2, 1))
    rot_norm = np.linalg.norm(J_anti, ord="fro", axis=(1, 2))

    trace = np.trace(J, axis1=1, axis2=2)
    spectral_radius = np.array([
        float(np.max(np.abs(np.linalg.eigvals(j)))) for j in J
    ])
    rot_power = rot_norm**2 / (frob**2 + 1e-12)

    # ACI: asymmetry to contraction index
    sym_frob = np.linalg.norm(J_sym, ord="fro", axis=(1, 2))
    aci = rot_norm / (sym_frob + 1e-12)

    # MDR: mean diagonal ratio
    diag = np.array([np.diag(j) for j in J])
    off_diag_frob = np.sqrt(np.maximum(0, frob**2 - np.sum(diag**2, axis=1)))
    mdr = np.sum(np.abs(diag), axis=1) / (frob + 1e-12)

    return {
        "frobenius_norm": frob,
        "rotation_norm": rot_norm,
        "trace": trace,
        "spectral_radius": spectral_radius,
        "rotational_power": rot_power,
        "aci": aci,
        "mdr": mdr,
    }


def load_session_epoch_data(h5_path: Path, feat: pd.DataFrame, file_stem: str) -> pd.DataFrame | None:
    """Load epoch-level Jacobians and physio from H5 + features.parquet.

    Returns merged DataFrame with columns:
      window_start, {mnj_metrics}, resp_anchor_index, ecg_hrv_rmssd_ms, ...
    """
    try:
        with h5py.File(h5_path, "r") as f:
            # Time grid
            window_start = np.array(f["window_start"], dtype=np.float64)

            # Subject-anchored Jacobians
            J = np.array(f["jacobian_subject_anchored/J_hat"], dtype=np.float32)
            centers = np.array(f["jacobian_subject_anchored/centers"], dtype=np.int32)
    except Exception as e:
        warnings.warn(f"Failed to read {h5_path}: {e}")
        return None

    # MNJ metrics
    mnj = compute_mnj_metrics_from_jacobians(J)
    jac_df = pd.DataFrame(mnj)
    jac_df["epoch_idx"] = centers.astype(int)

    # Map epoch_idx → window_start (centers index into the full time grid)
    n_epochs = len(window_start)
    valid = (centers >= 0) & (centers < n_epochs)
    jac_df = jac_df[valid].copy()
    jac_df["window_start"] = window_start[jac_df["epoch_idx"].values]

    # Physio features for this session
    sess_feat = feat[feat["file"] == file_stem].copy()
    if len(sess_feat) == 0:
        return jac_df  # no physio merge

    # Merge on window_start ≈ t_start (float tolerance)
    sess_feat = sess_feat.rename(columns={"t_start": "window_start"})
    merged = pd.merge_asof(
        jac_df.sort_values("window_start"),
        sess_feat.sort_values("window_start")[[
            "window_start", "resp_anchor_index", "resp_regular_index",
            "resp_rate_bpm", "resp_phase_consistency",
            "ecg_hrv_rmssd_ms", "cardioresp_rsa_amplitude",
            "cardioresp_coupling_index", "qc_ok_resp",
        ]],
        on="window_start",
        tolerance=2.0,
        direction="nearest",
    )
    return merged


# ──────────────────────────────────────────────────────────────────────────────
# Main: iterate all H5 files
# ──────────────────────────────────────────────────────────────────────────────
print("Loading features.parquet for epoch alignment ...")
feat = load_features()
# Build lookup from file basename (without dir) to full filename
feat["file_stem"] = feat["file"]  # already basename

h5_list = iter_h5_paths()
print(f"Processing {len(h5_list)} H5 sessions ...")

all_session_rows = []
all_epoch_rows = []

MNJ_KEYS = [
    "frobenius_norm", "rotation_norm", "trace",
    "spectral_radius", "rotational_power", "aci", "mdr",
]
PHYSIO_MERGE_COLS = [
    "resp_anchor_index", "resp_regular_index", "resp_rate_bpm",
    "resp_phase_consistency", "ecg_hrv_rmssd_ms",
    "cardioresp_rsa_amplitude", "cardioresp_coupling_index", "qc_ok_resp",
]

for i, (subject_id, task_label, h5_path) in enumerate(h5_list):
    if (i + 1) % 20 == 0:
        print(f"  {i+1}/{len(h5_list)} ...")

    # Reconstruct EDF filename pattern for this session
    # H5 session dir: sub-S200116_ses-01_cognitive_control_run-01
    # EDF file:       sub-S200116_ses-01_task-CC_run-01_eeg.edf
    task_raw_map = {"gambling": "GG", "cognitive_control": "CC", "rest": "Rest"}
    task_raw = task_raw_map.get(task_label, task_label)
    sub_id_short = subject_id.replace("sub-", "")
    file_stem = f"{subject_id}_ses-01_task-{task_raw}_run-01_eeg.edf"

    epoch_df = load_session_epoch_data(h5_path, feat, file_stem)
    if epoch_df is None or len(epoch_df) == 0:
        continue

    # Session-level medians
    row = {"subject_id": subject_id, "task_label": task_label, "n_epochs": len(epoch_df)}
    for key in MNJ_KEYS:
        if key in epoch_df.columns:
            vals = epoch_df[key].replace([np.inf, -np.inf], np.nan).dropna()
            row[f"{key}_median"] = float(vals.median()) if len(vals) else np.nan
            row[f"{key}_iqr"] = float(vals.quantile(0.75) - vals.quantile(0.25)) if len(vals) else np.nan
    for col in PHYSIO_MERGE_COLS:
        if col in epoch_df.columns:
            resp_ok = epoch_df["qc_ok_resp"] == 1 if "qc_ok_resp" in epoch_df.columns else pd.Series([True] * len(epoch_df))
            if col.startswith("resp"):
                vals = epoch_df.loc[resp_ok, col].dropna()
            else:
                vals = epoch_df[col].dropna()
            row[f"{col}_median"] = float(vals.median()) if len(vals) else np.nan
    all_session_rows.append(row)

    # Within-session: Spearman per epoch (resp_anchor × frobenius)
    if "resp_anchor_index" in epoch_df.columns and "frobenius_norm" in epoch_df.columns:
        resp_ok_mask = (epoch_df["qc_ok_resp"] == 1) if "qc_ok_resp" in epoch_df.columns else pd.Series([True] * len(epoch_df), index=epoch_df.index)
        sub_ep = epoch_df[resp_ok_mask & epoch_df["resp_anchor_index"].notna() & epoch_df["frobenius_norm"].notna()]
        if len(sub_ep) >= 10:
            r_rf, p_rf = spearman_r(sub_ep["resp_anchor_index"], sub_ep["frobenius_norm"])
            r_rc, p_rc = spearman_r(sub_ep["resp_anchor_index"], sub_ep.get("rotation_norm", pd.Series(dtype=float)))
            all_epoch_rows.append({
                "subject_id": subject_id, "task_label": task_label,
                "r_resp_frobenius": r_rf, "p_resp_frobenius": p_rf,
                "r_resp_rotation": r_rc, "p_resp_rotation": p_rc,
                "n_epochs_resp_ok": len(sub_ep),
            })

print(f"  Done. {len(all_session_rows)} sessions processed, {len(all_epoch_rows)} within-session correlations.")

session_df = pd.DataFrame(all_session_rows)
session_df.to_csv(OUT / "subject_mnj_summary.csv", index=False)

epoch_corr_df = pd.DataFrame(all_epoch_rows)
epoch_corr_df.to_csv(OUT / "within_session_mnj_resp_spearman.csv", index=False)

# ──────────────────────────────────────────────────────────────────────────────
# Cross-task Wilcoxon for MNJ metrics
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- Cross-task Wilcoxon for MNJ metrics ---")
pairs = list(combinations(TASK_ORDER, 2))
pair_rows = []
for key in MNJ_KEYS:
    col = f"{key}_median"
    if col not in session_df.columns:
        continue
    pivot = session_df.pivot_table(index="subject_id", columns="task_label", values=col)
    for t1, t2 in pairs:
        if t1 not in pivot.columns or t2 not in pivot.columns:
            continue
        common = pivot[[t1, t2]].dropna().index
        a = pivot.loc[common, t1].values
        b = pivot.loc[common, t2].values
        stat, p, n, d = wilcoxon_paired(a, b)
        print(f"  {key}: {t1} vs {t2}  p={p:.4f}  d={d:.3f}  n={n}")
        pair_rows.append({"mnj_metric": key, "task1": t1, "task2": t2,
                          "wilcoxon_stat": stat, "p": p, "cohen_d": d, "n_pairs": n})

if pair_rows:
    pair_df = pd.DataFrame(pair_rows)
    pair_df["p_fdr"] = bh_fdr(pair_df["p"].fillna(1).values)
    pair_df["sig_fdr05"] = pair_df["p_fdr"] < 0.05
    pair_df.to_csv(OUT / "mnj_cross_task_wilcoxon.csv", index=False)
    print(f"  Surviving FDR 5%: {pair_df['sig_fdr05'].sum()} / {len(pair_df)}")
    sig = pair_df[pair_df["sig_fdr05"]].sort_values("p_fdr")
    if len(sig):
        print(sig[["mnj_metric", "task1", "task2", "cohen_d", "p_fdr"]].to_string(index=False))

# ──────────────────────────────────────────────────────────────────────────────
# Session-level resp_anchor × MNJ coupling
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- Session-level resp_anchor x MNJ Spearman ---")
coup_rows = []
for task in TASK_ORDER:
    sub_t = session_df[session_df["task_label"] == task]
    for mnj_key in MNJ_KEYS:
        mnj_col = f"{mnj_key}_median"
        if mnj_col not in sub_t.columns:
            continue
        r_rsp, p_rsp = spearman_r(sub_t["resp_anchor_index_median"], sub_t[mnj_col])
        r_hrv, p_hrv = spearman_r(sub_t["ecg_hrv_rmssd_ms_median"], sub_t[mnj_col])
        r_rsa, p_rsa = spearman_r(sub_t.get("cardioresp_rsa_amplitude_median", pd.Series(dtype=float)), sub_t[mnj_col])
        n = int(sub_t[["resp_anchor_index_median", mnj_col]].dropna().shape[0])
        coup_rows.append({
            "task": task, "mnj_metric": mnj_key,
            "r_resp_anchor": r_rsp, "p_resp_anchor": p_rsp,
            "r_hrv_rmssd": r_hrv, "p_hrv_rmssd": p_hrv,
            "r_rsa": r_rsa, "p_rsa": p_rsa, "n": n,
        })

coup_df = pd.DataFrame(coup_rows)
coup_df["p_fdr_resp"] = bh_fdr(coup_df["p_resp_anchor"].fillna(1).values)
coup_df["sig_fdr05_resp"] = coup_df["p_fdr_resp"] < 0.05
coup_df.to_csv(OUT / "mnj_resp_coupling.csv", index=False)

print("Top correlations (resp_anchor × MNJ, |r| > 0.2):")
notable = coup_df[coup_df["r_resp_anchor"].abs() > 0.2].sort_values("p_resp_anchor")
if len(notable):
    print(notable[["task", "mnj_metric", "r_resp_anchor", "p_resp_anchor", "p_fdr_resp", "sig_fdr05_resp"]].to_string(index=False))
else:
    print("  None with |r| > 0.2")

# Print all frobenius correlations
frob_rows = coup_df[coup_df["mnj_metric"] == "frobenius_norm"]
print("\nresp_anchor × frobenius by task:")
print(frob_rows[["task", "r_resp_anchor", "p_resp_anchor", "r_hrv_rmssd", "r_rsa", "n"]].to_string(index=False))

# ──────────────────────────────────────────────────────────────────────────────
# Within-session epoch-level correlation summary
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- Within-session epoch-level resp_anchor x frobenius ---")
if len(epoch_corr_df):
    print(epoch_corr_df.groupby("task_label")[["r_resp_frobenius", "r_resp_rotation"]].describe().round(3))
    # Sign consistency
    for task in TASK_ORDER:
        sub_t = epoch_corr_df[epoch_corr_df["task_label"] == task]
        if len(sub_t) == 0:
            continue
        rs = sub_t["r_resp_frobenius"].dropna()
        n_neg = (rs < 0).sum()
        n_pos = (rs > 0).sum()
        from scipy.stats import wilcoxon
        if len(rs) >= 5:
            try:
                stat, p = wilcoxon(rs, zero_method="wilcox")
            except ValueError:
                p = np.nan
        else:
            p = np.nan
        median_r = rs.median()
        print(f"  {task}: n_sessions={len(rs)}, median_r={median_r:.3f}, n_neg={n_neg}, n_pos={n_pos}, Wilcoxon_p={p:.4f}")

# ──────────────────────────────────────────────────────────────────────────────
# LOOSO for session-level top correlations
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- LOOSO for session-level top correlations ---")
top_hits = [
    ("resp_anchor_index_median", "frobenius_norm_median", "gambling"),
    ("resp_anchor_index_median", "frobenius_norm_median", "cognitive_control"),
    ("resp_anchor_index_median", "rotation_norm_median", "gambling"),
    ("ecg_hrv_rmssd_ms_median", "frobenius_norm_median", "gambling"),
]
looso_rows = []
for phys, geom, task in top_hits:
    sub_t = session_df[(session_df["task_label"] == task) &
                        session_df.get(phys, pd.Series(dtype=float)).notna() if phys in session_df.columns else False]
    if phys not in session_df.columns or geom not in session_df.columns:
        continue
    sub_t = session_df[(session_df["task_label"] == task)]
    sub_t = sub_t[[phys, geom, "subject_id"]].dropna()
    if len(sub_t) < 6:
        continue
    full_r, full_p = spearman_r(sub_t[phys], sub_t[geom])
    loo_rs = []
    for sub_loo in sub_t["subject_id"].unique():
        sub_loo_df = sub_t[sub_t["subject_id"] != sub_loo]
        r, _ = spearman_r(sub_loo_df[phys], sub_loo_df[geom])
        loo_rs.append(r)
    loo_rs = np.array(loo_rs)
    print(f"  {task}/{phys} x {geom}: full_r={full_r:.3f}  p={full_p:.4f}  loo_mean={np.nanmean(loo_rs):.3f}  loo_min={np.nanmin(loo_rs):.3f}")
    looso_rows.append({
        "task": task, "physio": phys, "geometry": geom,
        "full_r": full_r, "full_p": full_p,
        "loo_mean": float(np.nanmean(loo_rs)),
        "loo_min": float(np.nanmin(loo_rs)),
        "loo_max": float(np.nanmax(loo_rs)),
        "sign_consistent": bool(np.all(loo_rs * full_r > 0)),
    })

if looso_rows:
    looso_df = pd.DataFrame(looso_rows)
    looso_df.to_csv(OUT / "mnj_resp_looso.csv", index=False)

print(f"\n=== MNJ extraction complete ===")
print(f"Outputs in: {OUT}")
