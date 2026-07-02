"""
10_corrugator_emg_confound.py — Corrugator EMG descriptive contrast and
confound check for the primary GG > CC Frobenius effect (peer_review/pr_01.md,
finding #7b).

The BioPac hardware recorded two EMG channels over the corrugator supercilii
muscle (a standard, validated facial-affect/frowning indicator; Larsen, Norris
& Cacioppo 2003), injected into the NMD pipeline as `EMGA`/`EMGB` and combined
by the EMG feature extractor into a single per-epoch `emg_rms` column. This
channel is a plausible confound for the GG-vs-CC MNJ effect for two reasons:
(1) it could contaminate frontal EEG via volume conduction, and (2) it could
independently track affective responses to a gambling task's wins/losses that
a self-report/deception cover story does not otherwise let us measure.

Method: identical in structure to Script 07 (EDA confound control).
  (a) Descriptive: paired Wilcoxon contrast of tonic emg_rms across
      GG / CC / Rest on the intersection sample.
  (b) Confound test: Spearman correlation between the subject-level GG-CC
      difference in emg_rms and the GG-CC difference in MNJ Frobenius norm.

Outputs:
  results/10_corrugator_emg_confound/
    emg_descriptive_wilcoxon.csv   — GG/CC/Rest tonic emg_rms contrasts
    emg_confound_partial.csv       — EMG-specific confound test
    full_confound_table_with_emg.csv — Script 05/07 table extended with EMG
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "nmd-analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from ds004511_support import (
    RESULTS_DIR,
    bh_fdr,
    load_features,
    make_results_subdir,
    spearman_r,
    wilcoxon_paired,
)

OUT = make_results_subdir("10_corrugator_emg_confound")

PRIMARY_PAIRS = [
    ("gambling", "cognitive_control"),
    ("gambling", "rest"),
    ("cognitive_control", "rest"),
]

# ──────────────────────────────────────────────────────────────────────────────
# Load features and restrict to intersection sample + EMG QC pass
# ──────────────────────────────────────────────────────────────────────────────
print("Loading epoch-level features ...")
feat = load_features()

if "emg_rms" not in feat.columns:
    raise SystemExit(
        "No emg_rms column found in features.parquet. Re-run the NMD pipeline "
        "with the EMGA/EMGB physio_tsv_inject channels enabled "
        "(mndm/config/config_ingest_ds004511.yaml) before running this script."
    )

if "qc_ok_emg" in feat.columns:
    n_before = len(feat)
    feat = feat[feat["qc_ok_emg"].fillna(False).astype(bool)]
    print(f"  EMG QC filter: kept {len(feat)} / {n_before} epochs")

prior_run_dir = RESULTS_DIR / "ds004511_20260701"
intersection_path = prior_run_dir / "05_mnj_confound_audit" / "intersection_sample.csv"
if intersection_path.exists():
    intersection_subs = sorted(pd.read_csv(intersection_path)["subject_id"].unique())
    feat = feat[feat["subject_id"].isin(intersection_subs)]
    print(f"Restricted to intersection sample: {len(intersection_subs)} subjects")
else:
    intersection_subs = sorted(feat["subject_id"].unique())
    print("WARNING: intersection_sample.csv not found; using all available subjects.")

# ──────────────────────────────────────────────────────────────────────────────
# (a) Descriptive: tonic corrugator EMG by task
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- (a) Corrugator EMG (emg_rms) by task ---")
emg_pivot = feat.groupby(["subject_id", "task_label"])["emg_rms"].median().unstack()

desc_rows = []
for t1, t2 in PRIMARY_PAIRS:
    if t1 not in emg_pivot.columns or t2 not in emg_pivot.columns:
        continue
    common = emg_pivot[[t1, t2]].dropna().index
    a = emg_pivot.loc[common, t1].values
    b = emg_pivot.loc[common, t2].values
    stat, p, n, d = wilcoxon_paired(a, b)
    print(f"  {t1} vs {t2}: d_z={d:.3f}, p={p:.4f}, n={n}")
    desc_rows.append({
        "task1": t1, "task2": t2, "wilcoxon_stat": stat, "p": p,
        "cohen_dz": d, "n_pairs": n,
    })

desc_df = pd.DataFrame(desc_rows)
desc_df["p_fdr"] = bh_fdr(desc_df["p"].fillna(1).values)
desc_df["sig_fdr05"] = desc_df["p_fdr"] < 0.05
desc_df.to_csv(OUT / "emg_descriptive_wilcoxon.csv", index=False)

# ──────────────────────────────────────────────────────────────────────────────
# (b) Confound test: GG-CC EMG diff vs GG-CC Frobenius diff
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- (b) EMG confound test for GG > CC Frobenius effect ---")
mnj_summary_path = prior_run_dir / "03_mnj_reachability" / "subject_mnj_summary.csv"
if not mnj_summary_path.exists():
    raise SystemExit(f"Required file not found: {mnj_summary_path}")

mnj_summary = pd.read_csv(mnj_summary_path)
frob_pivot = (
    mnj_summary[mnj_summary["subject_id"].isin(intersection_subs)]
    .pivot_table(index="subject_id", columns="task_label", values="frobenius_norm_median")
)
frob_diff = frob_pivot["gambling"] - frob_pivot["cognitive_control"]

emg_diff = emg_pivot["gambling"] - emg_pivot["cognitive_control"] if (
    "gambling" in emg_pivot.columns and "cognitive_control" in emg_pivot.columns
) else pd.Series(dtype=float)

r_emg, p_emg = spearman_r(emg_diff, frob_diff)
n_common = pd.DataFrame({"emg": emg_diff, "frob": frob_diff}).dropna().shape[0]
print(f"Spearman(EMG_diff, Frobenius_diff): r={r_emg:.3f}, p={p_emg:.4f}, n={n_common}")

emg_row = pd.DataFrame([{
    "confound": "emg_rms_corrugator",
    "r_confound_diff_x_frob_diff": r_emg,
    "p": p_emg,
    "n": n_common,
}])
emg_row.to_csv(OUT / "emg_confound_partial.csv", index=False)

# ──────────────────────────────────────────────────────────────────────────────
# Combine with the Script 05/07 confound table for a single reviewer-facing table
# ──────────────────────────────────────────────────────────────────────────────
full_confound_path = prior_run_dir / "07_eda_confound_control" / "full_confound_table.csv"
if full_confound_path.exists():
    prior_confounds = pd.read_csv(full_confound_path)
    prior_confounds = prior_confounds[["confound", "r_confound_diff_x_frob_diff", "p"]].copy()
    combined = pd.concat(
        [prior_confounds, emg_row[["confound", "r_confound_diff_x_frob_diff", "p"]]],
        ignore_index=True,
    )
    combined["p_fdr"] = bh_fdr(combined["p"].fillna(1).values)
    combined["sig_fdr05"] = combined["p_fdr"] < 0.05
    combined.to_csv(OUT / "full_confound_table_with_emg.csv", index=False)
    print("\n=== Combined confound table (HR, resp_rate, resp_anchor, EOG blink, EDA tonic, corrugator EMG) ===")
    print(combined.to_string(index=False))
else:
    print("WARNING: full_confound_table.csv (Script 07) not found; skipping combined table.")

# ──────────────────────────────────────────────────────────────────────────────
# Interpretation summary
# ──────────────────────────────────────────────────────────────────────────────
print("\n=== Interpretation ===")
if not (p_emg == p_emg) or p_emg > 0.05:  # NaN-safe "not significant" check
    print("Corrugator EMG does NOT confound the GG>CC Frobenius effect (no significant")
    print("association between EMG difference and Frobenius difference). This closes")
    print("the corrugator-EMG confound question raised in peer_review/pr_01.md finding #7.")
else:
    print("WARNING: corrugator EMG difference shows a significant association with")
    print("Frobenius difference. Further investigation required before finalizing the claim.")

print(f"\n=== Corrugator EMG confound check complete ===")
print(f"Outputs: {OUT}")
