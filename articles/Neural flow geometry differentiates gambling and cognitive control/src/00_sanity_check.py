"""
00_sanity_check.py — QC audit for ds004511 before article analyses.

Reports:
  A. Epoch coverage by subject × task
  B. RESP QC pass rate by task (and subject-level variability)
  C. ECG / HRV quality by task
  D. Cardioresp coupling quality
  E. EOG stability by task
  F. Bad-subject flag (subjects with any task resp_ok_rate < 0.50)
  G. Summary table written to results/

Run: python src/00_sanity_check.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "nmd-analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from ds004511_support import (
    RESULTS_DIR,
    TASK_DISPLAY,
    TASK_ORDER,
    load_features,
    make_results_subdir,
    spearman_r,
)

OUT = make_results_subdir("00_sanity_check")

# ──────────────────────────────────────────────────────────────────────────────
# A. Load features and tag subject/task
# ──────────────────────────────────────────────────────────────────────────────
print("Loading features.parquet ...")
feat = load_features()
print(f"  Total epochs: {len(feat):,}")
print(f"  Subjects:     {feat['subject_id'].nunique()}")
print(f"  Tasks:        {feat['task_label'].value_counts().to_dict()}")

# ──────────────────────────────────────────────────────────────────────────────
# B. Epoch coverage by subject × task
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- A. Epoch coverage ---")
coverage = (
    feat.groupby(["subject_id", "task_label"])
    .size()
    .unstack(fill_value=0)
    .reindex(columns=TASK_ORDER, fill_value=0)
)
print(coverage.describe().round(1))
missing = coverage[coverage.eq(0).any(axis=1)]
if len(missing):
    print(f"  Subjects with zero epochs in some task: {len(missing)}")
    print(missing[missing.eq(0).any(axis=1)])
else:
    print("  All subjects have epochs in all tasks.")
coverage.to_csv(OUT / "epoch_coverage.csv")

# ──────────────────────────────────────────────────────────────────────────────
# C. RESP QC
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- B. RESP QC by task ---")
resp_task = feat.groupby("task_label")["qc_ok_resp"].mean().reindex(TASK_ORDER)
print(resp_task.round(3))

resp_sub = (
    feat.groupby(["subject_id", "task_label"])["qc_ok_resp"]
    .mean()
    .unstack(fill_value=np.nan)
    .reindex(columns=TASK_ORDER)
)
resp_sub.columns.name = None
print("\nSubject-level RESP pass rate (describe):")
print(resp_sub.describe().round(3))

# Flag subjects with low resp in any task
low_resp = resp_sub[resp_sub.min(axis=1) < 0.50]
print(f"\nSubjects with min task resp_ok < 50%: {len(low_resp)}")
if len(low_resp):
    print(low_resp.round(3))

low_resp_gg = resp_sub[resp_sub.get("gambling", pd.Series(dtype=float)) < 0.50]
low_resp_cc = resp_sub[resp_sub.get("cognitive_control", pd.Series(dtype=float)) < 0.50]
print(f"  Low in GG (<50%): {len(low_resp_gg)}")
print(f"  Low in CC (<50%): {len(low_resp_cc)}")
resp_sub.to_csv(OUT / "resp_qc_by_subject_task.csv")

# ──────────────────────────────────────────────────────────────────────────────
# D. ECG / HRV quality
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- C. ECG / HRV quality by task ---")
ecg_task = feat.groupby("task_label")[["qc_ok_ecg", "qc_ok_ecg_hrv"]].mean().reindex(TASK_ORDER)
print(ecg_task.round(3))

hrv_fill = (
    feat.groupby("task_label")[["ecg_hrv_rmssd_ms", "ecg_hrv_sdnn_ms"]]
    .apply(lambda g: g.notna().mean())
    .reindex(TASK_ORDER)
)
print("\nHRV column fill fraction:")
print(hrv_fill.round(3))

# ──────────────────────────────────────────────────────────────────────────────
# E. Cardioresp coupling quality
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- D. Cardioresp coupling quality ---")
cr_task = feat.groupby("task_label")[["qc_ok_cardioresp", "cardioresp_coupling_index", "cardioresp_rsa_amplitude"]].mean().reindex(TASK_ORDER)
print(cr_task.round(3))

# ──────────────────────────────────────────────────────────────────────────────
# F. EOG stability
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- E. EOG stability by task ---")
eog_task = feat.groupby("task_label")[["eog_eye_stability_index", "eog_artifact_fraction", "eog_blink_rate"]].mean().reindex(TASK_ORDER)
print(eog_task.round(3))

# ──────────────────────────────────────────────────────────────────────────────
# G. Resp anchor index fill and distribution
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- F. Resp anchor index ---")
ai_task = (
    feat.groupby("task_label")["resp_anchor_index"]
    .agg(fill=lambda s: s.notna().mean(), median="median", std="std")
    .reindex(TASK_ORDER)
)
print(ai_task.round(3))

# ──────────────────────────────────────────────────────────────────────────────
# H. Subject-level median summary table
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- G. Subject-level median resp anchor by task ---")
key_cols = [
    "resp_anchor_index", "resp_regular_index", "resp_phase_consistency",
    "resp_rate_bpm", "resp_amplitude_median",
    "ecg_hrv_rmssd_ms", "cardioresp_rsa_amplitude", "cardioresp_coupling_index",
    "eog_eye_stability_index",
]
avail = [c for c in key_cols if c in feat.columns]
sub_task = (
    feat.groupby(["subject_id", "task_label"])[avail]
    .median()
    .reset_index()
)
sub_task.to_csv(OUT / "subject_task_physio_medians.csv", index=False)
print(f"Saved subject×task physio medians: {sub_task.shape}")

# ──────────────────────────────────────────────────────────────────────────────
# I. QC flag — subjects excluded from EAP analyses
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- H. QC flag summary ---")
# Primary analysis: GG + CC (task-ful conditions); require resp_ok >= 0.30
task_resp_ok = resp_sub.reindex(columns=["gambling", "cognitive_control"])
resp_ok_mask = task_resp_ok.min(axis=1) >= 0.30
n_ok = resp_ok_mask.sum()
print(f"Subjects with resp_ok >= 30% in both GG and CC: {n_ok} / {len(resp_ok_mask)}")
resp_ok_sub = resp_ok_mask[resp_ok_mask].index.tolist()

# Save flags
flag_df = pd.DataFrame({
    "subject_id": resp_sub.index,
    "resp_ok_gg": resp_sub.get("gambling", pd.Series(dtype=float)),
    "resp_ok_cc": resp_sub.get("cognitive_control", pd.Series(dtype=float)),
    "resp_ok_rest": resp_sub.get("rest", pd.Series(dtype=float)),
    "qc_ok_for_eap": resp_ok_mask.values,
})
flag_df.to_csv(OUT / "subject_qc_flags.csv", index=False)
print(f"QC flag table saved -> {OUT / 'subject_qc_flags.csv'}")

print("\n=== Sanity check complete ===")
print(f"All outputs in: {OUT}")
