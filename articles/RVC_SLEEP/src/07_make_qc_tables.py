"""
07_make_qc_tables.py — Final QC/robustness summary tables for the manuscript's
S3 Supplementary QC & Robustness section.

Consolidates:
  A. Gate #2 QC checklist (handover_From_nmd.md §4), cross-checked against
     this repo's own 00_sanity_check.py outputs where possible.
  B. BOAS Pass C respiratory-anchor restricted-sample size (from script 05).
  C. Known limitations to document (handover_From_nmd.md §6), carried
     forward verbatim as a structured table rather than prose, so it can be
     rendered directly into S3.

Run: python src/07_make_qc_tables.py
Requires: 00_sanity_check.py to have been run; 05_pass_c_eap_moderation.py
          is used opportunistically if already run (BOAS restricted N).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from rvc_sleep_support import RESULTS_DIR, make_results_subdir

OUT = make_results_subdir("07_make_qc_tables")


def find_latest(glob_pattern: str):
    candidates = sorted(RESULTS_DIR.glob(glob_pattern))
    return candidates[-1] if candidates else None


# ──────────────────────────────────────────────────────────────────────────────
# A. Gate #2 QC checklist (reproduced from handover_From_nmd.md §4)
# ──────────────────────────────────────────────────────────────────────────────
gate2_checklist = pd.DataFrame([
    {"check": "ANPHY ecg_hrv_rmssd_ms in event-locked rows", "nmd_status": "0% NaN, all bins",
     "analysis_repo_cross_check": "see anchor_nan_rates.csv (00_sanity_check)"},
    {"check": "BOAS resp_regular_index in event-locked rows",
     "nmd_status": "0% NaN in 54/128 subjects; 66/128 have no respiratory channel",
     "analysis_repo_cross_check": "see anchor_nan_rates.csv (00_sanity_check); restrict Pass C N accordingly"},
    {"check": "Primary geometry free of body signals", "nmd_status": "Clean",
     "analysis_repo_cross_check": "assumed from NMD contract; not independently re-derived here"},
    {"check": "Matched controls are N2, within-subject", "nmd_status": ">99.8% N2 purity",
     "analysis_repo_cross_check": "see pass_a_filter_coverage.csv (00_sanity_check)"},
    {"check": "All 5 spindle time bins populated", "nmd_status": "OK",
     "analysis_repo_cross_check": "see event_locked_coverage.csv (00_sanity_check)"},
    {"check": "Primary vs anchor-aug runs unambiguously identified", "nmd_status": "OK via config_hash",
     "analysis_repo_cross_check": "see run_manifest_check.csv (00_sanity_check)"},
    {"check": "Detector covariates (duration, frequency_hz)", "nmd_status": "usable",
     "analysis_repo_cross_check": "used as covariates in Pass A1/A2/C models"},
    {"check": "sigma_power", "nmd_status": "absent (YASA v1 CSV only)",
     "analysis_repo_cross_check": "not available; flagged as a post-Pass-A follow-up, not a blocker"},
])
gate2_checklist.to_csv(OUT / "gate2_qc_checklist.csv", index=False)
print("=== A. Gate #2 QC checklist ===")
print(gate2_checklist.to_string(index=False))

# ──────────────────────────────────────────────────────────────────────────────
# B. BOAS Pass C restricted-sample size (opportunistic, if script 05 has run)
# ──────────────────────────────────────────────────────────────────────────────
print("\n=== B. BOAS Pass C restricted sample ===")
pass_c_path = find_latest("rvc_sleep_*/05_pass_c_eap_moderation/pass_c_eap_moderation.csv")
if pass_c_path is not None:
    pass_c = pd.read_csv(pass_c_path)
    boas_primary = pass_c[(pass_c["dataset"] == "ds005555") & (pass_c["model"] == "primary")]
    print(boas_primary[["endpoint", "n_events", "n_subjects"]].to_string(index=False) if len(boas_primary) else "  (no rows)")
    boas_primary.to_csv(OUT / "boas_pass_c_restricted_n.csv", index=False)
else:
    print("  05_pass_c_eap_moderation.py has not been run yet; skipping.")

# ──────────────────────────────────────────────────────────────────────────────
# C. Known limitations table (handover_From_nmd.md §6)
# ──────────────────────────────────────────────────────────────────────────────
known_limitations = pd.DataFrame([
    {"id": 1, "limitation": "BOAS Pass C N reduction",
     "detail": "66/128 subjects have no respiratory signal; Pass C BOAS effective N ~= 54"},
    {"id": 2, "limitation": "Matched controls: single bin",
     "detail": "Controls contribute one window each, not a pre/event/post structure; "
               "the within-spindle temporal contrast (event vs pre_far) is computed within "
               "spindle_event rows only (Pass A2)"},
    {"id": 3, "limitation": "event_confidence all NaN",
     "detail": "YASA v0.7 does not export a per-spindle confidence score; use event_duration_sec "
               "and frequency_hz as detector proxy covariates"},
    {"id": 4, "limitation": "sigma_power absent",
     "detail": "Not in YASA v1 CSV; can be added by rerunning the spindle-detection script with "
               "sp.summary() full output, deferred until reviewers request it"},
    {"id": 5, "limitation": "9D falsification warnings (ANPHY)",
     "detail": "9D MNPS is effectively rank-3 for all ANPHY subjects (EEG-only); use "
               "coords_9d_finite filter and interpret 9D cautiously, treat 3D MNPS (m,d,e) as primary"},
])
known_limitations.to_csv(OUT / "known_limitations.csv", index=False)
print("\n=== C. Known limitations ===")
print(known_limitations.to_string(index=False))

print("\n=== QC table build complete ===")
print(f"All outputs in: {OUT}")
