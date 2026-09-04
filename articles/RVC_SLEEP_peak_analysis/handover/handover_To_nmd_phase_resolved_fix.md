# Handover back to NMD: RichSleep spindle-catalog bug — root cause identified, scope larger than the phase test

**Date:** 2026-07-08 (superseded/updated same day after `v2` delivery)
**From:** Analysis repo (RVC_SLEEP / EAP fairness-test work)
**To:** NMD
**Status:** RESOLVED in diagnosis, BLOCKED on delivery — `neuralmanifolddynamics_RichSleep_20260708_135627`
is not yet present in this repo's `data/raw/`.

---

## 1. Correction to this document's original version

The original version of this file (same day, earlier) asked NMD to make
`event_phase_v1`/`v2` match "the frozen RVC_SLEEP event-locked spindle
catalog," on the assumption that the frozen catalog was ground truth. **That
assumption was wrong.** Further verification (below) shows the frozen
catalog is itself the corrupted one. NMD's own diagnosis and fix (glob-scope
bug in `summary.py`'s fallback path; `n_events_input` was pulling `xn024`'s
223→1065-count CSV for `xn001`, per NMD's report) is consistent with this and
is the *correct* root cause — thank you for finding and fixing it
independently.

## 2. What was found on the analysis side (independent verification)

Checked whether **all** subjects in each frozen event-locked table have
distinct spindle-onset signatures (first 3 onset times per subject):

| Dataset | N subjects | Distinct onset signatures | Verdict |
|---|---|---|---|
| ANPHY | 27 | 27 | clean |
| BOAS (ds005555) | 125 | 122 | clean (3 subjects share, consistent with chance) |
| **RichSleep** (`..._20260704_063231`) | 24 | **1** | **all 24 subjects share one signature** (`801.085, 917.095, 1027.76 s`), counts artificially narrow (1,004-1,059) vs. the wide, YASA-typical 164-2,566 range in the independently-detected `event_phase_v1/v2` catalogs |

This means the **original** RichSleep NMD ingest run
(`neuralmanifolddynamics_RichSleep_20260704_063231`) — the one underlying
the manuscript's R6 section (A1r `d_n`/`e_s` replication, A2r, and the
`cardioresp_anchor_index` EAP-moderation null; diary 231, folded into the
manuscript per diary 232) — has the bug, not (only) the phase-resolved
export. `xn024` happens to be the subject whose real catalog got duplicated
across the other 23 (its `event_phase_v2` onsets match the frozen table
exactly, 1058/1058).

**Scope is therefore larger than the phase-resolved (Test 1 / Mål B/C)
work**: Pass A1r, A2r, and the EAP-moderation test for RichSleep (R6 in the
manuscript) all need to be re-run against the corrected ingest, not just the
new phase columns.

## 3. What is requested now

1. Confirm `neuralmanifolddynamics_RichSleep_20260708_135627` has 24 distinct
   per-subject spindle-onset signatures (the same check run here — trivial
   to re-run: `groupby(subject).first(3 onsets)`, expect 24 distinct tuples).
2. Deliver/copy `neuralmanifolddynamics_RichSleep_20260708_135627` into this
   repo's `data/raw/` (or the shared `K:/ExternalReceivedDatasets/...`
   location this repo's `rvc_sleep_support.py` expects), analogous to the
   four frozen ANPHY/BOAS run roots.
3. Confirm `event_phase_v2`'s onset catalog now matches
   `neuralmanifolddynamics_RichSleep_20260708_135627`'s event-locked onsets
   per subject (not the old `063231` run) — this is the join Test 1 will
   actually use going forward.

## 4. What is NOT requested

- No changes to ANPHY or BOAS — both independently verified clean (27/27,
  122/125 distinct signatures).
- No further work on `phase_state_v1` (per-epoch, spindle-detection
  independent) — unaffected either way.

## 5. Impact while blocked (analysis-repo side)

- `manuscript.typ` R6 section, abstract, and Conclusion have been flagged
  in-place with an explicit "DATA INTEGRITY NOTE — R6 UNDER REVISION" box and
  provisional-result caveats (2026-07-08), pending re-delivery per §3 above.
- `rvc_sleep_support.py`'s `RUN_ROOTS[(DATASET_RICHSLEEP, SURFACE_PRIMARY)]`
  still points at the old `063231` run; will be repointed to `135627` once
  it is present locally and verified.
- Test 1 (Mål B spindle-phase-locking, Mål C HEP moderation) remains paused
  until the corrected run is available and `09_richsleep_verification.py`
  can be re-run to regenerate A1r/A2r/EAP-moderation numbers for the
  manuscript.
