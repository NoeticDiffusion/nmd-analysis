# RVC_SLEEP_peak_analysis

Follow-up article to `articles/RVC_SLEEP/`. Manuscript: *Sleep Spindles
Phase-Lock to Respiration at Their Amplitude Peak, Not Onset, in Human NREM
Sleep*.

## Relationship to the companion article

The companion three-dataset study (`articles/RVC_SLEEP/`) replicated a
spindle-locked state-space reconfiguration across ANPHY, BOAS, and RichSleep,
then tested (its R6/"Mal B") whether spindle *onset* preferentially occurs at
a particular cardiac/respiratory phase, using RichSleep's phase-resolved
export on a 190-event, geometry-valid, N2-staged subsample. That test was
null throughout.

An external theoretical review (`articles/Rythmic_Variance_Control_in_Sleep_theory/plan/02_response.md`)
flagged two problems with that null: (1) the 190-event subsample discards
99% of RichSleep's raw spindle catalog for reasons unrelated to the
phase-locking question itself, and (2) an earlier *proposed* correction
(shuffling subject labels on the pooled angle set) does not construct a
valid null at all, since it leaves the pooled circular-uniformity statistic
invariant.

This article is the resulting corrected reanalysis. It:

1. Re-tests onset-phase locking on the full 23,029-event RichSleep catalog
   (not just the 190-event subsample) using a valid subject-specific
   random-phase-rotation permutation null (diary 241) - confirming the
   onset-phase null holds even at ~120x the original power.
2. Discovers, in the process, that spindle *peak* (amplitude-envelope
   maximum, not onset) phase is a robust, population-level, subject-
   consistent quantity for respiration (and, more fragilely, cardiac phase),
   and subjects that finding to four independent robustness checks (diary
   242): duration-tercile stratification, leave-one-subject-out jackknife,
   deterministic split-half replication, and phase-convention calibration.
3. Adds one new analysis (diary 243, this article's only new statistical
   test, not present in the companion article) asking whether *alignment*
   to the population-preferred respiratory-peak phase moderates the
   companion article's own spindle-locked geometry delta on the same
   190-event subsample - the event-*efficacy* question, as distinct from the
   event-*timing* question R2-R5 answer, per the theoretical review's
   timing/efficacy framing.

Only RichSleep is analyzed here (ANPHY and BOAS have no phase-resolved
export); this article does not attempt a three-dataset replication of the
timing result.

## Contents

```
RVC_SLEEP_peak_analysis/
  Sleep Spindles Phase-Lock to Respiration...typ   main manuscript
  S1_Supplementary_methods.typ                     phase conventions, permutation-null construction, robustness/alignment-model formulas
  S2_Supplementary_data.typ                         full result tables (all CSVs referenced by section)
  S3_Supplementary_QC_Robustness.typ                sample coverage, full robustness-check audit, R6 sensitivity detail
  S4_Supplementary_Clinical.typ                     brief clinician-facing note (not yet clinically translatable)
  S5_Glossary.typ                                   article-specific + carried-over NDT/RVC/EAP terms
  template_eLife.typ                                shared Typst engine (do not edit; identical to companion article's copy)
  references.bib                                    bibliography (RichSleep-only scope; ANPHY/BOAS dataset refs removed)
  figures/                                          fig1-fig5 SVGs (rose plot, per-subject scatter, duration-tercile, split-half, alignment scatter)
  src/                                               analysis scripts (see below)
  results/rvc_sleep_20260710/{09,10,11,12,13}_*/    frozen pipeline outputs underlying every number in the manuscript/supplements
  RichSleep_resolved/                               phase-resolved NMD export (event_phase_v1, event_phase_v2), inherited from the companion article's RichSleep run
  handover/, sciencelead/, peer_review/             provenance carried over from the companion article
```

## `src/` scripts

Numbering is inherited from the companion article and intentionally *not*
renumbered from zero; scripts `00`-`08` (ANPHY/BOAS-specific) and the
unrelated `11_richsleep_resp_anchor_followup.py` (a `resp_anchor_index`
sign-bug follow-up, diary 240) were pruned as out of scope for this
RichSleep-only article.

- `09_richsleep_verification.py` - RichSleep-specific NMD export sanity check (inherited, unmodified).
- `10_richsleep_phase_resolved_eap.py` - builds the 190-event geometry-valid, N2-staged merged table (`richsleep_event_phase_merged.parquet`) that both the companion article's Mal B/C and this article's R6 use (inherited, unmodified).
- `11_richsleep_maalb_corrected.py` - the corrected onset+peak-phase permutation reanalysis on the full 23,029-event catalog (diary 241; primary/secondary families, per-subject and second-order Rayleigh tests).
- `12_richsleep_maalb_peak_phase_deepdive.py` - the four robustness checks on the peak-phase finding (diary 242).
- `13_peak_phase_alignment_moderation.py` - **new**: the alignment-moderation test (R6, diary 243).
- `14_make_figures.py` - **new**: generates all 5 manuscript figures from the CSVs above.
- `rvc_sleep_support.py` - shared constants/loaders/statistics; `ARTICLE_DIR` fixed here to point at this folder (it was inherited from the companion article's copy and initially pointed at the wrong directory - see `src/rvc_sleep_support.py`'s docstring history).

Run order for a from-scratch reproduction: `09` -> `10` -> `11` -> `12` -> `13` -> `14`. All scripts are idempotent (each run creates a fresh timestamped subfolder under `results/`); the manuscript/supplements cite the specific `results/rvc_sleep_20260710/` run frozen at authoring time.

## Building

```
typst compile "Sleep Spindles Phase-Lock to Respiration at Their Amplitude Peak, Not Onset, in Human NREM Sleep.typ"
typst compile S1_Supplementary_methods.typ
typst compile S2_Supplementary_data.typ
typst compile S3_Supplementary_QC_Robustness.typ
typst compile S4_Supplementary_Clinical.typ
typst compile S5_Glossary.typ
```
