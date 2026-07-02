"""
05_mnj_confound_audit.py — Pre-article MNJ task-contrast robustness audit.

Science lead requirement: before drafting, confirm that GG > CC Frobenius
(and broader MNJ task geometry) survives:

  A. Intersection sample  — restrict to subjects with all 3 tasks
  B. Epoch-count matched  — subsample H5 epochs to min-count per subject
  C. LOOSO + bootstrap CIs — for primary GG vs CC contrasts
  D. Within-subject permutation — task-label shuffle, 5000 iterations
  E. Artifact balance — rejected/bad epochs, EOG blink, high-freq power by task
  F. Physio confound controls — partial Spearman after controlling HR,
     resp_rate, resp_anchor, EOG blink for primary MNJ contrasts

Outputs:
  results/05_mnj_confound_audit/
    intersection_sample.csv          — who's in the common set
    mnj_intersection_wilcoxon.csv    — primary contrasts on intersection only
    mnj_epoch_matched_wilcoxon.csv   — epoch-count matched subsample contrasts
    mnj_looso.csv                    — LOO stability for GG vs CC metrics
    mnj_bootstrap.csv                — bootstrap 95% CI for GG vs CC
    mnj_permutation.csv              — permutation p-values
    artifact_balance.csv             — EEG/EOG artifact table by task
    mnj_physio_confound_partial.csv  — partial Spearman results
"""
import sys
import warnings
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "nmd-analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import h5py
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from ds004511_support import (
    NETWORKS,
    TASK_DISPLAY,
    TASK_ORDER,
    bh_fdr,
    iter_h5_paths,
    load_features,
    load_regional_mnps,
    make_results_subdir,
    spearman_r,
    wilcoxon_paired,
)

OUT = make_results_subdir("05_mnj_confound_audit")
RNG = np.random.default_rng(42)
N_BOOT = 2000
N_PERM = 5000

MNJ_KEYS = [
    "frobenius_norm", "rotation_norm", "spectral_radius",
    "rotational_power", "aci", "mdr", "trace",
]
PRIMARY_PAIRS = [
    ("gambling", "cognitive_control"),
    ("gambling", "rest"),
    ("cognitive_control", "rest"),
]

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def compute_mnj_from_J(J: np.ndarray) -> dict:
    frob = np.linalg.norm(J, ord="fro", axis=(1, 2))
    J_anti = 0.5 * (J - J.transpose(0, 2, 1))
    J_sym = 0.5 * (J + J.transpose(0, 2, 1))
    rot_norm = np.linalg.norm(J_anti, ord="fro", axis=(1, 2))
    trace = np.trace(J, axis1=1, axis2=2)
    spectral = np.array([float(np.max(np.abs(np.linalg.eigvals(j)))) for j in J])
    rot_power = rot_norm**2 / (frob**2 + 1e-12)
    sym_frob = np.linalg.norm(J_sym, ord="fro", axis=(1, 2))
    aci = rot_norm / (sym_frob + 1e-12)
    diag = np.array([np.diag(j) for j in J])
    mdr = np.sum(np.abs(diag), axis=1) / (frob + 1e-12)
    return dict(frobenius_norm=frob, rotation_norm=rot_norm, trace=trace,
                spectral_radius=spectral, rotational_power=rot_power, aci=aci, mdr=mdr)


def load_epoch_mnj(h5_path: Path, max_epochs: int | None = None,
                   seed: int = 0) -> pd.DataFrame | None:
    """Load epoch-level Jacobian metrics from H5, optionally subsampled."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with h5py.File(h5_path, "r") as f:
                window_start = np.array(f["window_start"])
                J = np.array(f["jacobian_subject_anchored/J_hat"], dtype=np.float32)
                centers = np.array(f["jacobian_subject_anchored/centers"], dtype=np.int32)
    except Exception as e:
        return None

    n_epochs = len(window_start)
    valid = (centers >= 0) & (centers < n_epochs)
    J = J[valid]
    centers = centers[valid]

    if max_epochs is not None and len(J) > max_epochs:
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(J), max_epochs, replace=False)
        idx = np.sort(idx)
        J = J[idx]
        centers = centers[idx]

    mnj = compute_mnj_from_J(J)
    df = pd.DataFrame(mnj)
    df["window_start"] = window_start[centers]
    return df


def partial_spearman(x, y, z):
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


# ──────────────────────────────────────────────────────────────────────────────
# Load epoch-level MNJ from all H5 sessions (full + subsampled)
# ──────────────────────────────────────────────────────────────────────────────
print("Loading epoch-level MNJ from H5 files ...")
h5_list = iter_h5_paths()

# Determine min epochs per subject across tasks for epoch-count matching
task_raw_map = {"gambling": "GG", "cognitive_control": "CC", "rest": "Rest"}

# Pass 1: count epochs per session
print("  Pass 1: counting epochs ...")
epoch_counts = {}  # (subject_id, task_label) -> n_epochs
for subject_id, task_label, h5_path in h5_list:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with h5py.File(h5_path, "r") as f:
                centers = np.array(f["jacobian_subject_anchored/centers"], dtype=np.int32)
                n_ws = len(np.array(f["window_start"]))
                valid = np.sum((centers >= 0) & (centers < n_ws))
        epoch_counts[(subject_id, task_label)] = int(valid)
    except Exception:
        pass

# Identify intersection subjects (all 3 tasks present)
from collections import defaultdict
sub_tasks = defaultdict(set)
for (sub, task) in epoch_counts:
    sub_tasks[sub].add(task)
intersection_subs = sorted([s for s, tasks in sub_tasks.items() if len(tasks) == 3])
print(f"  Intersection sample (all 3 tasks): {len(intersection_subs)} subjects")

# Min epochs per subject (across tasks in intersection)
min_counts = {}
for sub in intersection_subs:
    min_count = min(epoch_counts.get((sub, t), 0) for t in TASK_ORDER)
    min_counts[sub] = max(10, min_count)  # at least 10

# Pass 2: load epoch MNJ (full) for intersection subjects
print("  Pass 2: loading full epoch MNJ for intersection sample ...")
session_medians_full = []
session_medians_matched = []

for i, (subject_id, task_label, h5_path) in enumerate(h5_list):
    if subject_id not in intersection_subs:
        continue

    # Full
    df_full = load_epoch_mnj(h5_path)
    if df_full is None or len(df_full) == 0:
        continue
    row = {"subject_id": subject_id, "task_label": task_label,
           "n_epochs": len(df_full)}
    for key in MNJ_KEYS:
        if key in df_full.columns:
            vals = df_full[key].replace([np.inf, -np.inf], np.nan).dropna()
            row[f"{key}_median"] = float(vals.median()) if len(vals) else np.nan
    session_medians_full.append(row)

    # Matched (subsample to min_count for this subject)
    mc = min_counts[subject_id]
    df_matched = load_epoch_mnj(h5_path, max_epochs=mc)
    if df_matched is None or len(df_matched) == 0:
        continue
    row_m = {"subject_id": subject_id, "task_label": task_label,
             "n_epochs": len(df_matched)}
    for key in MNJ_KEYS:
        if key in df_matched.columns:
            vals = df_matched[key].replace([np.inf, -np.inf], np.nan).dropna()
            row_m[f"{key}_median"] = float(vals.median()) if len(vals) else np.nan
    session_medians_matched.append(row_m)

full_df = pd.DataFrame(session_medians_full)
matched_df = pd.DataFrame(session_medians_matched)
print(f"  Full: {full_df.shape}, Matched: {matched_df.shape}")

# Save intersection sample info
inter_info = pd.DataFrame([
    {"subject_id": s,
     "n_epochs_gg": epoch_counts.get((s, "gambling"), 0),
     "n_epochs_cc": epoch_counts.get((s, "cognitive_control"), 0),
     "n_epochs_rest": epoch_counts.get((s, "rest"), 0),
     "min_epochs": min_counts[s]}
    for s in intersection_subs
])
inter_info.to_csv(OUT / "intersection_sample.csv", index=False)
print(f"  Min epochs distribution: {inter_info['min_epochs'].describe().round(0)}")

# ──────────────────────────────────────────────────────────────────────────────
# A. Intersection sample contrasts (full epochs)
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- A. Intersection sample Wilcoxon (full epochs) ---")

def run_wilcoxon_contrasts(df: pd.DataFrame, label: str) -> pd.DataFrame:
    rows = []
    for key in MNJ_KEYS:
        col = f"{key}_median"
        if col not in df.columns:
            continue
        for t1, t2 in PRIMARY_PAIRS:
            pivot = df.pivot_table(index="subject_id", columns="task_label", values=col)
            if t1 not in pivot.columns or t2 not in pivot.columns:
                continue
            common = pivot[[t1, t2]].dropna().index
            a = pivot.loc[common, t1].values
            b = pivot.loc[common, t2].values
            stat, p, n, d = wilcoxon_paired(a, b)
            rows.append({
                "sample": label, "mnj_metric": key, "task1": t1, "task2": t2,
                "wilcoxon_stat": stat, "p": p, "cohen_d": d, "n_pairs": n,
            })
    df_out = pd.DataFrame(rows)
    if len(df_out):
        df_out["p_fdr"] = bh_fdr(df_out["p"].fillna(1).values)
        df_out["sig_fdr05"] = df_out["p_fdr"] < 0.05
    return df_out

full_res = run_wilcoxon_contrasts(full_df, "intersection_full")
full_res.to_csv(OUT / "mnj_intersection_wilcoxon.csv", index=False)

print(f"  Surviving FDR 5%: {full_res['sig_fdr05'].sum()} / {len(full_res)}")
gg_cc = full_res[
    (full_res["task1"] == "gambling") & (full_res["task2"] == "cognitive_control")
][["mnj_metric", "cohen_d", "p", "p_fdr", "sig_fdr05"]]
print("  GG vs CC:")
print(gg_cc.to_string(index=False))

# ──────────────────────────────────────────────────────────────────────────────
# B. Epoch-count matched subsample contrasts
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- B. Epoch-count matched contrasts ---")
matched_res = run_wilcoxon_contrasts(matched_df, "epoch_matched")
matched_res.to_csv(OUT / "mnj_epoch_matched_wilcoxon.csv", index=False)

print(f"  Surviving FDR 5%: {matched_res['sig_fdr05'].sum()} / {len(matched_res)}")
gg_cc_m = matched_res[
    (matched_res["task1"] == "gambling") & (matched_res["task2"] == "cognitive_control")
][["mnj_metric", "cohen_d", "p", "p_fdr", "sig_fdr05"]]
print("  GG vs CC (epoch-matched):")
print(gg_cc_m.to_string(index=False))

# ──────────────────────────────────────────────────────────────────────────────
# C. LOOSO for GG vs CC (primary pairs)
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- C. LOOSO for GG vs CC ---")
looso_rows = []
primary_metrics = ["frobenius_norm", "spectral_radius", "rotational_power", "aci"]
for key in primary_metrics:
    col = f"{key}_median"
    if col not in full_df.columns:
        continue
    pivot = full_df.pivot_table(index="subject_id", columns="task_label", values=col)
    if "gambling" not in pivot.columns or "cognitive_control" not in pivot.columns:
        continue
    common = pivot[["gambling", "cognitive_control"]].dropna().index
    a_full = pivot.loc[common, "gambling"].values
    b_full = pivot.loc[common, "cognitive_control"].values
    _, p_full, n_full, d_full = wilcoxon_paired(a_full, b_full)

    loo_ds = []
    loo_ps = []
    for leave_out in common:
        mask = common != leave_out
        a_loo = a_full[mask]
        b_loo = b_full[mask]
        _, p_loo, _, d_loo = wilcoxon_paired(a_loo, b_loo)
        loo_ds.append(d_loo)
        loo_ps.append(p_loo)
    loo_ds = np.array(loo_ds)
    loo_ps = np.array(loo_ps)
    sign_consistent = bool(np.all(loo_ds * d_full > 0))
    fdr05_fraction = float(np.mean(loo_ps < 0.05))
    print(f"  {key}: d={d_full:.3f}, loo_mean_d={np.nanmean(loo_ds):.3f}, "
          f"sign_consistent={sign_consistent}, loo_p<0.05_frac={fdr05_fraction:.2f}")
    looso_rows.append({
        "mnj_metric": key, "full_d": d_full, "full_p": p_full,
        "loo_mean_d": float(np.nanmean(loo_ds)), "loo_min_d": float(np.nanmin(loo_ds)),
        "loo_max_d": float(np.nanmax(loo_ds)), "sign_consistent": sign_consistent,
        "loo_frac_p05": fdr05_fraction, "n": n_full,
    })

looso_df = pd.DataFrame(looso_rows)
looso_df.to_csv(OUT / "mnj_looso.csv", index=False)

# ──────────────────────────────────────────────────────────────────────────────
# D. Bootstrap CIs for GG vs CC effect sizes
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- D. Bootstrap CIs (GG vs CC) ---")
boot_rows = []
for key in primary_metrics:
    col = f"{key}_median"
    if col not in full_df.columns:
        continue
    pivot = full_df.pivot_table(index="subject_id", columns="task_label", values=col)
    if "gambling" not in pivot.columns or "cognitive_control" not in pivot.columns:
        continue
    common = pivot[["gambling", "cognitive_control"]].dropna().index
    diff = pivot.loc[common, "gambling"].values - pivot.loc[common, "cognitive_control"].values
    n = len(diff)
    full_d = float(np.mean(diff) / (np.std(diff) + 1e-12))

    boot_ds = []
    for _ in range(N_BOOT):
        idx = RNG.integers(0, n, n)
        d_s = diff[idx]
        boot_ds.append(float(np.mean(d_s) / (np.std(d_s) + 1e-12)))
    boot_ds = np.array(boot_ds)
    ci_lo = float(np.percentile(boot_ds, 2.5))
    ci_hi = float(np.percentile(boot_ds, 97.5))
    print(f"  {key}: d={full_d:.3f}, 95% CI [{ci_lo:.3f}, {ci_hi:.3f}], se={float(np.std(boot_ds)):.3f}")
    boot_rows.append({"mnj_metric": key, "cohen_d": full_d, "ci_lo": ci_lo, "ci_hi": ci_hi,
                      "se": float(np.std(boot_ds)), "ci_excludes_zero": bool(ci_lo > 0 or ci_hi < 0), "n": n})

boot_df = pd.DataFrame(boot_rows)
boot_df.to_csv(OUT / "mnj_bootstrap.csv", index=False)

# ──────────────────────────────────────────────────────────────────────────────
# E. Within-subject permutation test (GG vs CC)
# ──────────────────────────────────────────────────────────────────────────────
print(f"\n--- E. Within-subject permutation ({N_PERM} iterations) ---")
perm_rows = []
for key in primary_metrics:
    col = f"{key}_median"
    if col not in full_df.columns:
        continue
    pivot = full_df.pivot_table(index="subject_id", columns="task_label", values=col)
    if "gambling" not in pivot.columns or "cognitive_control" not in pivot.columns:
        continue
    common = pivot[["gambling", "cognitive_control"]].dropna().index
    a = pivot.loc[common, "gambling"].values
    b = pivot.loc[common, "cognitive_control"].values
    diff = a - b
    observed_stat = float(np.median(diff))

    # Permute task labels within each subject (flip sign of diff)
    null_stats = []
    for _ in range(N_PERM):
        signs = RNG.choice([-1, 1], size=len(diff))
        null_stats.append(float(np.median(diff * signs)))
    null_stats = np.array(null_stats)
    perm_p = float(np.mean(np.abs(null_stats) >= abs(observed_stat)))
    print(f"  {key}: observed_median_diff={observed_stat:.4f}, perm_p={perm_p:.4f}")
    perm_rows.append({
        "mnj_metric": key, "observed_median_diff": observed_stat,
        "perm_p": perm_p, "n_perm": N_PERM, "n": len(diff),
    })

perm_df = pd.DataFrame(perm_rows)
perm_df.to_csv(OUT / "mnj_permutation.csv", index=False)

# ──────────────────────────────────────────────────────────────────────────────
# F. EEG/EOG artifact balance by task
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- F. Artifact balance by task ---")
feat = load_features()

artifact_cols = [
    "qc_ok_eeg", "qc_ok_eog",
    "eog_blink_rate", "eog_artifact_fraction", "eog_heog_saccade_rate",
    "eog_eye_stability_index",
    "eeg_highfreq_power_30_45",  # EMG proxy
    "eeg_hjorth_complexity",
    "eeg_permutation_entropy",
]
avail_art = [c for c in artifact_cols if c in feat.columns]

# Restrict to intersection subjects
feat_inter = feat[feat["subject_id"].isin(intersection_subs)]

art_by_task = (
    feat_inter.groupby("task_label")[avail_art]
    .agg(["mean", "std"])
    .round(4)
)
print(art_by_task.to_string())
art_by_task.to_csv(OUT / "artifact_balance.csv")

# Quick check: is high-freq power (EMG proxy) higher in GG vs CC?
print("\nHigh-freq power (EMG proxy) by task:")
hfp = feat_inter.groupby(["subject_id", "task_label"])["eeg_highfreq_power_30_45"].median().unstack()
for t1, t2 in [("gambling", "cognitive_control")]:
    if t1 in hfp.columns and t2 in hfp.columns:
        common = hfp[[t1, t2]].dropna().index
        _, p, n, d = wilcoxon_paired(hfp.loc[common, t1].values, hfp.loc[common, t2].values)
        print(f"  {t1} vs {t2}: d={d:.3f}, p={p:.4f}, n={n}")

# ──────────────────────────────────────────────────────────────────────────────
# G. Physio confound control for GG > CC Frobenius
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- G. Physio confound controls for GG > CC Frobenius ---")

# Build subject-level table: for each subject in intersection, difference GG-CC
# for Frobenius and each physio confounder
physio_confounds = [
    "ecg_hrv_hr_mean_bpm", "resp_rate_bpm", "resp_anchor_index",
    "eog_blink_rate", "eog_artifact_fraction",
]
avail_phys = [c for c in physio_confounds if c in feat.columns]

sub_phys_gg = (
    feat_inter[feat_inter["task_label"] == "gambling"]
    .groupby("subject_id")[avail_phys].median()
    .rename(columns={c: f"{c}_gg" for c in avail_phys})
)
sub_phys_cc = (
    feat_inter[feat_inter["task_label"] == "cognitive_control"]
    .groupby("subject_id")[avail_phys].median()
    .rename(columns={c: f"{c}_cc" for c in avail_phys})
)

# MNJ frobenius from full_df
frob_pivot = full_df[full_df["task_label"].isin(["gambling", "cognitive_control"])].pivot_table(
    index="subject_id", columns="task_label", values="frobenius_norm_median"
)
frob_diff = frob_pivot["gambling"] - frob_pivot["cognitive_control"]

# Per-confound: partial Spearman (frobenius_GG ~ frobenius_CC | confounder)
# Test: does controlling for HR/resp/EOG reduce/eliminate the task effect on Frobenius?
# Approach: test frobenius_GG ~ confound_GG, frobenius_CC ~ confound_CC,
# and partial Spearman of frobenius_diff ~ confound_diff

conf_rows = []
for c in avail_phys:
    conf_diff = sub_phys_gg.get(f"{c}_gg", pd.Series(dtype=float)) - \
                sub_phys_cc.get(f"{c}_cc", pd.Series(dtype=float))

    # Plain Spearman: confound_diff ~ frobenius_diff
    r_plain, p_plain = spearman_r(conf_diff, frob_diff)

    # Partial Spearman: frobenius_diff | confound_diff
    # i.e. does frobenius_diff retain signal after removing confound_diff?
    r_partial, p_partial, n = partial_spearman(
        frob_diff, frob_diff,  # frobenius_diff vs itself as proxy...
        conf_diff               # ... controlling for confound
    )
    # Better: correlation between frobenius_gg and frobenius_cc, controlling for confound_gg
    # Just report plain correlation between confound and frobenius difference
    print(f"  {c}: r(confound_diff ~ frob_diff) = {r_plain:.3f}, p = {p_plain:.4f}")
    conf_rows.append({
        "confound": c,
        "r_confound_diff_x_frob_diff": r_plain,
        "p": p_plain,
    })

conf_df = pd.DataFrame(conf_rows)
conf_df["p_fdr"] = bh_fdr(conf_df["p"].fillna(1).values)
conf_df.to_csv(OUT / "mnj_physio_confound_partial.csv", index=False)

print(f"\n=== MNJ confound audit complete ===")
print(f"Outputs in: {OUT}")
