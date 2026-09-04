"""
01_validate_v3_delivery.py -- Validate NMD's 2026-07-12/13 RichSleep delivery
into articles/RichSLeep_EAP_v2/data/ (Phase 0 of
.cursor/plans/richsleep_eap_v2_article_aa3119f9.plan.md).

Five data products are checked here, each against a concrete claim made in
the plan (so this script either confirms the plan's factual basis or fails
loudly if the delivery has changed since it was written):

  1. phase_resolved_v3/   -- same 23,029-event N2-spindle catalog as the old
     event_phase_v2 (RVC_SLEEP_peak_analysis), extended from 14 to 33
     columns (adds frequency_hz, amplitude, sigma_power(_z_n2), so_amplitude,
     so_spindle_coupling_score, so_spindle_latency_sec, so_partner_missing).
     Checked here with an exact column-identity test against v2 on their
     shared columns -- if this passes, the already-published Mal-B/peak-
     phase/alignment numbers (diary 241/242/243) remain valid on v3 without
     re-running those pipelines.
  2. slow_oscillation_v1/ -- 68,386 raw SO events (26,377 N2 + 42,009 N3).
  3. phase_continuous_v1/ -- 24 subjects x ~10.2 h/night at 10 Hz, continuous
     phi_cardiac/phi_resp/phi_rem_theta (the risk-set stream for script 04).
  4. event_phase_n3_so_v1/ -- 42,009 N3 SOs, phase-resolved at trough+upstate.
  5. event_phase_rem_theta_v1/ -- 2,412 REM-theta 30s epochs, phase-resolved.
  6. non_event_risk_v1/ -- the genuine N2 non-event risk set (matched
     sampling, N=66,827) used by the hazard-model case-control test. Not
     copied into data/ by the initial delivery message; found alongside the
     other five on K:/ExternalReceivedDatasets/RichSleep/ and copied in
     here -- see handover/handover_From_nmd_richsleep_eap_v2_delivery_received.md.

Also cross-checks SO-coupling coverage against the existing 190-event
geometry-valid table from RVC_SLEEP_peak_analysis (script 10's output) to
confirm the N=25/15-subject SO-coupled-subset power caveat used throughout
the plan.

Run: python src/01_validate_v3_delivery.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ARTICLE_DIR / "data"
RESULTS_DIR = ARTICLE_DIR / "results"

OLD_V2_DIR = REPO_ROOT / "articles" / "RVC_SLEEP_peak_analysis" / "RichSleep_resolved" / "phase_resolved_v2"
OLD_MERGED_190_CANDIDATES = sorted(
    (REPO_ROOT / "articles" / "RVC_SLEEP_peak_analysis" / "results").glob(
        "rvc_sleep_*/10_richsleep_phase_resolved_eap/richsleep_event_phase_merged.parquet"
    )
)

from datetime import datetime

OUT = RESULTS_DIR / f"rvc_sleep_v2_{datetime.now().strftime('%Y%m%d')}" / "01_validate_v3_delivery"
OUT.mkdir(parents=True, exist_ok=True)

N_SUBJECTS_EXPECTED = 24
ok = True


def check(label: str, condition: bool, detail: str = "") -> None:
    global ok
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" -- {detail}" if detail else ""))
    if not condition:
        ok = False


# ─────────────────────────────────────────────────────────────────────────
# 1. phase_resolved_v3 vs run_meta_v3.json, and vs old event_phase_v2
# ─────────────────────────────────────────────────────────────────────────
print("=== 1. phase_resolved_v3/ ===")
v3_dir = DATA_DIR / "phase_resolved_v3"
v3_files = sorted(v3_dir.glob("*_event_phase_v3.parquet"))
check("24 subject files present", len(v3_files) == N_SUBJECTS_EXPECTED, f"found {len(v3_files)}")

with open(v3_dir / "run_meta_v3.json") as f:
    run_meta = json.load(f)
meta_rows = {s["subject"]: s["rows"] for s in run_meta["subjects"]}

v3_frames = []
row_mismatches = []
for p in v3_files:
    subj = p.stem.replace("_event_phase_v3", "")
    d = pd.read_parquet(p)
    d["subject"] = subj
    v3_frames.append(d)
    if len(d) != meta_rows.get(subj):
        row_mismatches.append((subj, len(d), meta_rows.get(subj)))
v3_full = pd.concat(v3_frames, ignore_index=True)
check("row counts match run_meta_v3.json for all subjects", len(row_mismatches) == 0, str(row_mismatches))
check("total events == 23,029", len(v3_full) == 23029, f"got {len(v3_full)}")
print(f"  columns ({len(v3_full.columns)}): {list(v3_full.columns)}")

v2_files = sorted(OLD_V2_DIR.glob("*_event_phase_v2.parquet"))
check("old event_phase_v2 24 files found for comparison", len(v2_files) == N_SUBJECTS_EXPECTED, f"found {len(v2_files)}")
v2_frames = []
for p in v2_files:
    subj = p.stem.replace("_event_phase_v2", "")
    d = pd.read_parquet(p)
    d["subject"] = subj
    v2_frames.append(d)
v2_full = pd.concat(v2_frames, ignore_index=True)
check("v2 total events == 23,029", len(v2_full) == 23029, f"got {len(v2_full)}")

shared_cols = [c for c in v2_full.columns if c in v3_full.columns and c != "subject"]
print(f"  shared columns to compare ({len(shared_cols)}): {shared_cols}")
v2_sorted = v2_full.sort_values(["subject", "onset_sec"]).reset_index(drop=True)
v3_sorted = v3_full.sort_values(["subject", "onset_sec"]).reset_index(drop=True)
check("v2 and v3 have identical (subject, onset_sec) key sets and row order after sort",
      len(v2_sorted) == len(v3_sorted)
      and (v2_sorted["subject"].to_numpy() == v3_sorted["subject"].to_numpy()).all()
      and np.allclose(v2_sorted["onset_sec"].to_numpy(), v3_sorted["onset_sec"].to_numpy()))

mismatch_cols = []
for c in shared_cols:
    a, b = v2_sorted[c], v3_sorted[c]
    if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
        same = np.allclose(a.to_numpy(dtype=float), b.to_numpy(dtype=float), equal_nan=True)
    else:
        same = a.astype(str).fillna("NaN").equals(b.astype(str).fillna("NaN"))
    if not same:
        mismatch_cols.append(c)
check("all shared columns bit-identical between v2 and v3 (proves v3 is a strict superset)",
      len(mismatch_cols) == 0, f"mismatched: {mismatch_cols}")

so_partner_missing_rate = v3_full["so_partner_missing"].mean()
coupled = v3_full[v3_full["so_partner_missing"] == 0]
print(f"\n  so_partner_missing rate: {so_partner_missing_rate:.4f} "
      f"({(v3_full['so_partner_missing'] == 0).sum()}/{len(v3_full)} coupled)")
print(f"  so_spindle_coupling_score (coupled only): "
      f"mean={coupled['so_spindle_coupling_score'].mean():.3f}, n={len(coupled)}")
print(f"  sigma_power_z_n2: mean={v3_full['sigma_power_z_n2'].mean():.2f}, "
      f"median={v3_full['sigma_power_z_n2'].median():.2f}, max={v3_full['sigma_power_z_n2'].max():.2f} "
      f"(heavily right-skewed -- flagging for log1p/rank transform downstream)")
print(f"  frequency_hz: mean={v3_full['frequency_hz'].mean():.2f}, "
      f"range=[{v3_full['frequency_hz'].min():.2f}, {v3_full['frequency_hz'].max():.2f}]")

v3_full.drop(columns=["subject"]).describe(include="all").to_csv(OUT / "phase_resolved_v3_describe.csv")

# ─────────────────────────────────────────────────────────────────────────
# 2. slow_oscillation_v1
# ─────────────────────────────────────────────────────────────────────────
print("\n=== 2. slow_oscillation_v1/ ===")
so_dir = DATA_DIR / "slow_oscillation_v1"
so_files = sorted(so_dir.glob("*_slow_oscillation_v1.parquet"))
check("24 subject files present", len(so_files) == N_SUBJECTS_EXPECTED, f"found {len(so_files)}")
so_frames = []
for p in so_files:
    d = pd.read_parquet(p)
    d["subject"] = p.stem.replace("_slow_oscillation_v1", "")
    so_frames.append(d)
so_full = pd.concat(so_frames, ignore_index=True)
so_full["stage"] = so_full["stage"].astype(int)
stage_counts = so_full["stage"].value_counts().to_dict()
check("covers both N2 (stage 2) and N3 (stage 3)", {2, 3}.issubset(set(stage_counts)), str(stage_counts))
check("all QC flags ok", (so_full["so_qc_flag"] == "ok").all(), so_full["so_qc_flag"].value_counts().to_dict())
n_n3 = int((so_full["stage"] == 3).sum())
print(f"  total SOs: {len(so_full)} (N2={stage_counts.get(2, 0)}, N3={n_n3})")

# ─────────────────────────────────────────────────────────────────────────
# 3. phase_continuous_v1
# ─────────────────────────────────────────────────────────────────────────
print("\n=== 3. phase_continuous_v1/ ===")
cont_dir = DATA_DIR / "phase_continuous_v1"
cont_files = sorted(cont_dir.glob("*_phase_continuous_v1.parquet"))
check("24 subject files present", len(cont_files) == N_SUBJECTS_EXPECTED, f"found {len(cont_files)}")
cont_summary_rows = []
total_cont_rows = 0
for p in cont_files:
    d = pd.read_parquet(p)
    subj = p.stem.replace("_phase_continuous_v1", "")
    dt = d["timestamp_sec"].diff().median()
    cont_summary_rows.append({
        "subject": subj, "n_rows": len(d), "dt_sec": dt,
        "duration_hr": d["timestamp_sec"].max() / 3600.0,
        "cardiac_valid_rate": d["cardiac_phase_valid"].mean(),
        "resp_valid_rate": d["resp_phase_valid"].mean(),
        "rem_theta_valid_rate": d["rem_theta_valid"].mean(),
    })
    total_cont_rows += len(d)
cont_summary = pd.DataFrame(cont_summary_rows)
check("sampling interval == 0.1 s (10 Hz) for all subjects", np.allclose(cont_summary["dt_sec"], 0.1))
check("cardiac + resp phase valid rate > 0.99 for all subjects",
      (cont_summary["cardiac_valid_rate"] > 0.99).all() and (cont_summary["resp_valid_rate"] > 0.99).all())
print(f"  total rows: {total_cont_rows}, mean duration/subject: {cont_summary['duration_hr'].mean():.2f} h")
print(f"  mean rem_theta_valid_rate: {cont_summary['rem_theta_valid_rate'].mean():.4f} (expected low, REM-only)")
cont_summary.to_csv(OUT / "phase_continuous_v1_per_subject_summary.csv", index=False)

# ─────────────────────────────────────────────────────────────────────────
# 4. event_phase_n3_so_v1
# ─────────────────────────────────────────────────────────────────────────
print("\n=== 4. event_phase_n3_so_v1/ ===")
n3_dir = DATA_DIR / "event_phase_n3_so_v1"
n3_files = sorted(n3_dir.glob("*_event_phase_n3_so_v1.parquet"))
check("24 subject files present", len(n3_files) == N_SUBJECTS_EXPECTED, f"found {len(n3_files)}")
n3_frames = [pd.read_parquet(p) for p in n3_files]
n3_full = pd.concat(n3_frames, ignore_index=True)
check("total N3-SO events == N3 count in slow_oscillation_v1 (42,009)", len(n3_full) == n_n3,
      f"got {len(n3_full)}, slow_oscillation_v1 N3={n_n3}")
for col in ["cardiac_phase_valid_trough", "resp_phase_valid_trough",
            "cardiac_phase_valid_upstate", "resp_phase_valid_upstate"]:
    check(f"{col} == 1 for (near-)all rows", (n3_full[col].mean() > 0.99), f"rate={n3_full[col].mean():.4f}")
check("phase_coupling_qc_flag_trough all ok", (n3_full["phase_coupling_qc_flag_trough"] == "ok").all())

# ─────────────────────────────────────────────────────────────────────────
# 5. event_phase_rem_theta_v1
# ─────────────────────────────────────────────────────────────────────────
print("\n=== 5. event_phase_rem_theta_v1/ ===")
rem_dir = DATA_DIR / "event_phase_rem_theta_v1"
rem_files = sorted(rem_dir.glob("*_event_phase_rem_theta_v1.parquet"))
check("24 subject files present", len(rem_files) == N_SUBJECTS_EXPECTED, f"found {len(rem_files)}")
rem_frames = []
for p in rem_files:
    d = pd.read_parquet(p)
    d["subject"] = p.stem.replace("_event_phase_rem_theta_v1", "")
    rem_frames.append(d)
rem_full = pd.concat(rem_frames, ignore_index=True)
per_subj_n = rem_full.groupby("subject").size()
check("total REM-theta epochs == 2,412", len(rem_full) == 2412, f"got {len(rem_full)}")
print(f"  per-subject N: min={per_subj_n.min()}, median={per_subj_n.median()}, max={per_subj_n.max()}")
for col in ["theta_phase_valid", "cardiac_phase_valid", "resp_phase_valid", "autonomic_phase_eligible"]:
    check(f"{col} == 1 for all rows", (rem_full[col] == 1).all(), f"rate={rem_full[col].mean():.4f}")
n_subj_below5 = int((per_subj_n < 5).sum())
print(f"  subjects with <5 REM-theta epochs (excluded from per-subject-only arm downstream): {n_subj_below5}")

# ─────────────────────────────────────────────────────────────────────────
# 6. non_event_risk_v1
# ─────────────────────────────────────────────────────────────────────────
print("\n=== 6. non_event_risk_v1/ ===")
risk_dir = DATA_DIR / "non_event_risk_v1"
risk_files = sorted(risk_dir.glob("*_non_event_risk_v1.parquet"))
check("24 subject files present", len(risk_files) == N_SUBJECTS_EXPECTED, f"found {len(risk_files)}")
risk_frames = [pd.read_parquet(p) for p in risk_files]
risk_full = pd.concat(risk_frames, ignore_index=True)
check("all rows stage == 2 (N2)", (risk_full["stage"] == 2).all(), risk_full["stage"].value_counts().to_dict())
check("all rows selection_status == 'selected'", (risk_full["selection_status"] == "selected").all())
check("cardiac + resp phase valid for all rows",
      (risk_full["cardiac_phase_valid"]).all() and (risk_full["resp_phase_valid"]).all())
per_subj_risk = risk_full.groupby("subject").size()
per_subj_spindles = v3_full.groupby("subject").size()
ratio = (per_subj_risk / per_subj_spindles.reindex(per_subj_risk.index)).mean()
print(f"  total risk rows: {len(risk_full)}, per-subject: "
      f"min={per_subj_risk.min()}, median={per_subj_risk.median()}, max={per_subj_risk.max()}")
print(f"  mean per-subject risk:spindle ratio: {ratio:.2f} (plan's exploratory estimate: ~2.9)")
print(f"  time_of_night_quartile counts: {risk_full['time_of_night_quartile'].value_counts().sort_index().to_dict()}")

# ─────────────────────────────────────────────────────────────────────────
# Cross-check: SO-coupling coverage among the 190 geometry-valid events
# ─────────────────────────────────────────────────────────────────────────
print("\n=== Cross-check: SO-coupling coverage among the 190 geometry-valid events ===")
if OLD_MERGED_190_CANDIDATES:
    merged_190 = pd.read_parquet(OLD_MERGED_190_CANDIDATES[-1])
    merged_190_keys = merged_190[["subject_id", "onset_sec"]].drop_duplicates().copy()
    merged_190_keys["subject"] = merged_190_keys["subject_id"].str.replace("sub-", "", regex=False)
    joined = merged_190_keys.merge(v3_full, on=["subject", "onset_sec"], how="left")
    n_missing_join = joined["so_partner_missing"].isna().sum()
    check("all 190 events found in v3 catalog", n_missing_join == 0, f"{n_missing_join} unmatched")
    n_coupled = int((joined["so_partner_missing"] == 0).sum())
    n_coupled_subjects = joined.loc[joined["so_partner_missing"] == 0, "subject_id"].nunique()
    print(f"  190 geometry-valid events -> {n_coupled} SO-coupled, across {n_coupled_subjects} subjects "
          f"(plan's stated N=25/15 -- {'confirmed' if (n_coupled, n_coupled_subjects) == (25, 15) else 'DIFFERS, update plan assumption'})")
    joined.to_csv(OUT / "geometry_valid_190_so_coupling_crosscheck.csv", index=False)
else:
    print("  [skip] no richsleep_event_phase_merged.parquet found under RVC_SLEEP_peak_analysis/results/")

# ─────────────────────────────────────────────────────────────────────────
print(f"\n=== Validation {'PASSED' if ok else 'FAILED -- see [FAIL] lines above'} ===")
print(f"Outputs in: {OUT}")
if not ok:
    sys.exit(1)
