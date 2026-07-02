"""
11_event_density_sensitivity.py — Event/response-rate sensitivity analysis for the
primary GG > CC MNJ Frobenius effect (peer_review/pr_03.md, "Optional analysis if
feasible"; peer_review/pr_02.md, Limitations item 2).

Rationale: GG (self-paced, 144 dice-betting rounds) and CC (a fast, back-to-back
four-task battery) differ in overall task structure. Neither the conventional-EEG
baseline (Script 09) nor the corrugator-EMG confound check (Script 10) controls for
*when*, within a session, discrete task events/responses occur -- a purely temporal-
structure explanation for elevated GG Frobenius that is distinct from arousal,
EMG artifact, or broadband power. This script tests that alternative directly using
data that is *already available* without any NMD pipeline/ingest changes:

  - Epoch windows (window_start, 8 s length) come from the existing H5
    `jacobian_subject_anchored` tensors (same source as Scripts 03/05).
  - Event timing comes directly from the raw BIDS `events.tsv` "Sync(1)" trigger
    pulses (onset column), which are dataset-native and independent of NMD ingest.

No re-ingest is required: this is a downstream covariate analysis joining two
data sources that already exist on disk.

Method:
  A. Session-level descriptive: Sync(1) pulse rate (events/second) by task, to
     test the Limitations' assumption that GG is low-event-rate and CC is
     high-event-rate (this assumption is checked here, not asserted).
  B. Epoch-level event density: count Sync(1) onsets falling inside each epoch's
     [window_start, window_start + 8s) window, joined to the H5-derived
     per-epoch Frobenius norm (same H5 loading path as Script 05).
  C. Confound-partial test: Spearman(GG-CC session event-rate diff,
     GG-CC Frobenius diff), same pattern as Scripts 07/10, using the existing
     `subject_mnj_summary.csv` (Script 03) so it can be appended to the
     combined confound table.
  D. Epoch-level covariate check: within-task Spearman(epoch event count,
     epoch Frobenius), to test whether local event proximity predicts local
     deformation.
  E. Density-matched sensitivity: recompute the GG vs CC Frobenius contrast
     restricted to each subject's below-median-event-density epochs in both
     tasks (a within-subject, within-task median split, avoiding a fixed
     absolute threshold that could be vacuous in one task), to test whether
     the effect survives when the most event-dense epochs are excluded.

Outputs:
  results/11_event_density_sensitivity/
    session_event_rate.csv                    — per-session pulse rate + duration
    event_rate_wilcoxon_by_task.csv           — GG/CC/Rest pulse-rate contrasts
    event_rate_confound_partial.csv           — GG-CC event-rate vs Frobenius-diff
    epoch_density_frobenius_correlation.csv   — within-task epoch-level Spearman
    density_matched_wilcoxon.csv              — low-density-only GG vs CC contrast
    full_confound_table_with_event_rate.csv   — Script 05/07/10 table + event rate
"""
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "nmd-analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import h5py
import numpy as np
import pandas as pd

from ds004511_support import (
    RESULTS_DIR,
    TASK_LABEL_TO_RAW,
    bh_fdr,
    iter_h5_paths,
    load_events,
    make_results_subdir,
    spearman_r,
    wilcoxon_paired,
)

OUT = make_results_subdir("11_event_density_sensitivity")
WINDOW_LEN_S = 8.0  # matches the ds004511 8-second epoch window (S1.1)

PRIMARY_PAIRS = [
    ("gambling", "cognitive_control"),
    ("gambling", "rest"),
    ("cognitive_control", "rest"),
]

prior_run_dir = RESULTS_DIR / "ds004511_20260701"
intersection = pd.read_csv(prior_run_dir / "05_mnj_confound_audit" / "intersection_sample.csv")
intersection_subs = sorted(intersection["subject_id"].unique())
print(f"Intersection sample: {len(intersection_subs)} subjects")


def compute_frobenius_from_J(J: np.ndarray) -> np.ndarray:
    return np.linalg.norm(J, ord="fro", axis=(1, 2))


def load_epoch_frobenius(h5_path: Path) -> pd.DataFrame | None:
    """Load epoch-level Frobenius norm + window_start from H5 (full, no subsampling)."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with h5py.File(h5_path, "r") as f:
                window_start = np.array(f["window_start"])
                J = np.array(f["jacobian_subject_anchored/J_hat"], dtype=np.float32)
                centers = np.array(f["jacobian_subject_anchored/centers"], dtype=np.int32)
    except Exception:
        return None

    n_epochs = len(window_start)
    valid = (centers >= 0) & (centers < n_epochs)
    J = J[valid]
    centers = centers[valid]
    if len(J) == 0:
        return None

    frob = compute_frobenius_from_J(J)
    return pd.DataFrame({"window_start": window_start[centers], "frobenius_norm": frob})


# ──────────────────────────────────────────────────────────────────────────────
# A. Load Sync(1) event onsets for all three tasks (raw BIDS events.tsv)
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- A. Loading Sync(1) event onsets from raw events.tsv ---")

events_by_task = {}
for task_raw in ["GG", "CC", "Rest"]:
    ev = load_events(task_raw=task_raw)
    if len(ev) and "trial_type" in ev.columns:
        ev = ev[ev["trial_type"].astype(str).str.startswith("Sync")]
    events_by_task[task_raw] = ev
    print(f"  {task_raw}: {len(ev)} Sync pulses across {ev['subject_id'].nunique() if len(ev) else 0} subjects")

# ──────────────────────────────────────────────────────────────────────────────
# B. Session-level event rate + epoch-level event density
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- B. Session-level event rate and epoch-level event density ---")

h5_list = [x for x in iter_h5_paths() if x[0] in intersection_subs]
task_raw_map = {"gambling": "GG", "cognitive_control": "CC", "rest": "Rest"}

session_rows = []
epoch_rows = []

for subject_id, task_label, h5_path in h5_list:
    epoch_df = load_epoch_frobenius(h5_path)
    if epoch_df is None or len(epoch_df) == 0:
        continue

    task_raw = task_raw_map[task_label]
    ev = events_by_task.get(task_raw, pd.DataFrame())
    onsets = np.array([])
    if len(ev):
        sub_ev = ev[ev["subject_id"] == subject_id]
        if len(sub_ev):
            onsets = np.sort(sub_ev["onset"].values.astype(float))

    win_start = epoch_df["window_start"].values.astype(float)
    win_end = win_start + WINDOW_LEN_S

    # Vectorized per-epoch event count via searchsorted
    if len(onsets):
        lo = np.searchsorted(onsets, win_start, side="left")
        hi = np.searchsorted(onsets, win_end, side="left")
        counts = hi - lo
    else:
        counts = np.zeros(len(win_start), dtype=int)
    epoch_df["event_count"] = counts

    epoch_df["subject_id"] = subject_id
    epoch_df["task_label"] = task_label
    epoch_rows.append(epoch_df)

    session_start = float(win_start.min())
    session_end = float(win_end.max())
    duration_s = session_end - session_start
    n_in_window = int(np.sum((onsets >= session_start) & (onsets < session_end))) if len(onsets) else 0
    rate = n_in_window / duration_s if duration_s > 0 else np.nan
    session_rows.append({
        "subject_id": subject_id, "task_label": task_label,
        "n_epochs": len(epoch_df), "duration_s": duration_s,
        "n_events": n_in_window, "event_rate_hz": rate,
        "median_epoch_event_count": float(np.median(counts)),
        "mean_epoch_event_count": float(np.mean(counts)),
    })

session_df = pd.DataFrame(session_rows)
epoch_df_all = pd.concat(epoch_rows, ignore_index=True)
session_df.to_csv(OUT / "session_event_rate.csv", index=False)

print(session_df.groupby("task_label")[["event_rate_hz", "median_epoch_event_count"]].describe().round(3).to_string())

# ──────────────────────────────────────────────────────────────────────────────
# B2. Descriptive Wilcoxon: event rate by task pair (tests the Limitations'
#     assumption that GG is low-rate and CC is high-rate)
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- B2. Event-rate contrasts by task pair ---")
rate_pivot = session_df.pivot_table(index="subject_id", columns="task_label", values="event_rate_hz")

rate_rows = []
for t1, t2 in PRIMARY_PAIRS:
    if t1 not in rate_pivot.columns or t2 not in rate_pivot.columns:
        continue
    common = rate_pivot[[t1, t2]].dropna().index
    a, b = rate_pivot.loc[common, t1].values, rate_pivot.loc[common, t2].values
    stat, p, n, d = wilcoxon_paired(a, b)
    print(f"  {t1} vs {t2}: event_rate d_z={d:.3f}, p={p:.4f}, n={n}  "
          f"(median {t1}={np.median(a):.3f} Hz, median {t2}={np.median(b):.3f} Hz)")
    rate_rows.append({"task1": t1, "task2": t2, "cohen_dz": d, "p": p, "n_pairs": n,
                       "median_t1_hz": float(np.median(a)), "median_t2_hz": float(np.median(b))})

rate_res = pd.DataFrame(rate_rows)
rate_res["p_fdr"] = bh_fdr(rate_res["p"].fillna(1).values)
rate_res["sig_fdr05"] = rate_res["p_fdr"] < 0.05
rate_res.to_csv(OUT / "event_rate_wilcoxon_by_task.csv", index=False)

# ──────────────────────────────────────────────────────────────────────────────
# C. Confound-partial test: GG-CC event-rate diff vs GG-CC Frobenius diff
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- C. Event-rate confound test for GG > CC Frobenius effect ---")

mnj_summary = pd.read_csv(prior_run_dir / "03_mnj_reachability" / "subject_mnj_summary.csv")
frob_pivot = (
    mnj_summary[mnj_summary["subject_id"].isin(intersection_subs)]
    .pivot_table(index="subject_id", columns="task_label", values="frobenius_norm_median")
)
frob_diff = frob_pivot["gambling"] - frob_pivot["cognitive_control"]

rate_diff = rate_pivot["gambling"] - rate_pivot["cognitive_control"] if (
    "gambling" in rate_pivot.columns and "cognitive_control" in rate_pivot.columns
) else pd.Series(dtype=float)

r_rate, p_rate = spearman_r(rate_diff, frob_diff)
n_common = pd.DataFrame({"rate": rate_diff, "frob": frob_diff}).dropna().shape[0]
print(f"Spearman(event_rate_diff, Frobenius_diff): r={r_rate:.3f}, p={p_rate:.4f}, n={n_common}")

rate_row = pd.DataFrame([{
    "confound": "event_rate_hz",
    "r_confound_diff_x_frob_diff": r_rate,
    "p": p_rate,
    "n": n_common,
}])
rate_row.to_csv(OUT / "event_rate_confound_partial.csv", index=False)

# ──────────────────────────────────────────────────────────────────────────────
# D. Epoch-level covariate check: does local event density predict local
#    Frobenius, within each task?
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- D. Epoch-level event-density x Frobenius correlation (within task) ---")

epoch_corr_rows = []
for task_label in ["gambling", "cognitive_control", "rest"]:
    sub = epoch_df_all[epoch_df_all["task_label"] == task_label]
    if len(sub) < 20:
        continue
    r, p = spearman_r(sub["event_count"], sub["frobenius_norm"])
    print(f"  {task_label}: Spearman(event_count, frobenius_norm) r={r:.3f}, p={p:.2e}, n_epochs={len(sub):,}")
    epoch_corr_rows.append({"task_label": task_label, "r": r, "p": p, "n_epochs": len(sub)})

epoch_corr_df = pd.DataFrame(epoch_corr_rows)
epoch_corr_df.to_csv(OUT / "epoch_density_frobenius_correlation.csv", index=False)

# ──────────────────────────────────────────────────────────────────────────────
# E. Density-matched sensitivity: GG vs CC restricted to below-median-density
#    epochs within each subject x task (avoids a fixed absolute threshold,
#    which could be vacuous if one task has uniformly higher event density)
# ──────────────────────────────────────────────────────────────────────────────
print("\n--- E. Density-matched sensitivity (below-median-density epochs only) ---")

low_density_medians = []
for (subject_id, task_label), grp in epoch_df_all.groupby(["subject_id", "task_label"]):
    thresh = grp["event_count"].median()
    low = grp[grp["event_count"] <= thresh]
    if len(low) < 5:
        continue
    low_density_medians.append({
        "subject_id": subject_id, "task_label": task_label,
        "frobenius_norm_median_lowdensity": float(low["frobenius_norm"].median()),
        "n_epochs_lowdensity": len(low),
        "event_count_threshold": float(thresh),
    })
low_df = pd.DataFrame(low_density_medians)

low_pivot = low_df.pivot_table(index="subject_id", columns="task_label", values="frobenius_norm_median_lowdensity")
n_epochs_pivot = low_df.pivot_table(index="subject_id", columns="task_label", values="n_epochs_lowdensity")

density_rows = []
for t1, t2 in PRIMARY_PAIRS:
    if t1 not in low_pivot.columns or t2 not in low_pivot.columns:
        continue
    common = low_pivot[[t1, t2]].dropna().index
    a, b = low_pivot.loc[common, t1].values, low_pivot.loc[common, t2].values
    stat, p, n, d = wilcoxon_paired(a, b)
    n_ep_t1 = n_epochs_pivot.loc[common, t1].median() if t1 in n_epochs_pivot.columns else np.nan
    n_ep_t2 = n_epochs_pivot.loc[common, t2].median() if t2 in n_epochs_pivot.columns else np.nan
    print(f"  {t1} vs {t2} (low-density epochs only): d_z={d:.3f}, p={p:.4f}, n={n} "
          f"(median n_epochs/subject: {t1}={n_ep_t1:.0f}, {t2}={n_ep_t2:.0f})")
    density_rows.append({
        "task1": t1, "task2": t2, "cohen_dz": d, "p": p, "n_pairs": n,
        "median_n_epochs_t1": n_ep_t1, "median_n_epochs_t2": n_ep_t2,
    })

density_res = pd.DataFrame(density_rows)
density_res["p_fdr"] = bh_fdr(density_res["p"].fillna(1).values)
density_res["sig_fdr05"] = density_res["p_fdr"] < 0.05
density_res.to_csv(OUT / "density_matched_wilcoxon.csv", index=False)

# ──────────────────────────────────────────────────────────────────────────────
# Combine with the Script 05/07/10 confound table for a single reviewer table
# ──────────────────────────────────────────────────────────────────────────────
full_confound_path = prior_run_dir / "10_corrugator_emg_confound" / "full_confound_table_with_emg.csv"
if full_confound_path.exists():
    prior_confounds = pd.read_csv(full_confound_path)
    prior_confounds = prior_confounds[["confound", "r_confound_diff_x_frob_diff", "p"]].copy()
    combined = pd.concat(
        [prior_confounds, rate_row[["confound", "r_confound_diff_x_frob_diff", "p"]]],
        ignore_index=True,
    )
    combined["p_fdr"] = bh_fdr(combined["p"].fillna(1).values)
    combined["sig_fdr05"] = combined["p_fdr"] < 0.05
    combined.to_csv(OUT / "full_confound_table_with_event_rate.csv", index=False)
    print("\n=== Combined confound table (HR, resp_rate, resp_anchor, EOG blink, EDA tonic, EMG, event rate) ===")
    print(combined.to_string(index=False))
else:
    print(f"WARNING: {full_confound_path} not found; skipping combined table.")

# ──────────────────────────────────────────────────────────────────────────────
# Interpretation summary
# ──────────────────────────────────────────────────────────────────────────────
print("\n=== Interpretation ===")
gg_cc_rate = rate_res[(rate_res["task1"] == "gambling") & (rate_res["task2"] == "cognitive_control")]
if len(gg_cc_rate):
    row = gg_cc_rate.iloc[0]
    print(f"GG vs CC event rate: d={row['cohen_dz']:.3f}, p={row['p']:.4f} "
          f"(median GG={row['median_t1_hz']:.3f} Hz, median CC={row['median_t2_hz']:.3f} Hz)")

if not (p_rate == p_rate) or p_rate > 0.05:
    print("Event-rate difference does NOT correlate with the Frobenius difference")
    print("(no significant association). This is one sensitivity check, not a full")
    print("resolution of the event/response-rate confound; see density-matched")
    print("and epoch-level covariate results above for convergent/divergent evidence.")
else:
    print("WARNING: event-rate difference shows a significant association with")
    print("Frobenius difference. This strengthens rather than resolves the")
    print("event/response-rate concern raised in peer_review/pr_02.md and pr_03.md.")

gg_cc_density = density_res[(density_res["task1"] == "gambling") & (density_res["task2"] == "cognitive_control")]
if len(gg_cc_density):
    row = gg_cc_density.iloc[0]
    print(f"\nDensity-matched (low-density epochs only) GG vs CC Frobenius: "
          f"d={row['cohen_dz']:.3f}, p={row['p']:.4f}")
    print("If this remains large and significant, the primary effect is not simply")
    print("driven by event-dense epochs; if it shrinks substantially, event density")
    print("contributes to (but does not necessarily fully explain) the effect.")

print(f"\n=== Event-density sensitivity analysis complete ===")
print(f"Outputs: {OUT}")
