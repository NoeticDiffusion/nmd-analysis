# RichSLeep_EAP_v2

Second follow-up article to `articles/RVC_SLEEP/` and `articles/RVC_SLEEP_peak_analysis/`.
Manuscript: *Autonomic Phase-Locking Is Strongest at Slow-Oscillation Troughs,
Not Spindle Onsets, Across Human NREM and REM Sleep*.

## Relationship to the companion articles

`articles/RVC_SLEEP/` replicated a spindle-locked state-space reconfiguration
across three datasets and found spindle-*onset* phase-locking to be null.
`articles/RVC_SLEEP_peak_analysis/` showed that null was a reference-point
artifact: on RichSleep's full 23,029-event catalog, spindle-*peak* phase
robustly locks to respiration (and, more fragilely, to the cardiac cycle),
and found a small, exploratory hint that alignment to a preferred phase might
also moderate the spindle-locked geometry effect itself.

NMD's 2026-07-12/13 RichSleep delivery (`data/`) added six new data products
that make several questions raised by that prior work newly testable:
per-event intrinsic spindle strength and slow-oscillation(SO)-spindle
coupling, a continuous 10 Hz cardiac/respiratory/theta phase stream,
phase-resolved N3-SO ($N=42{,}009$) and REM-theta ($N=2{,}412$) catalogs, and
a purpose-built non-event risk set ($N=66{,}827$) for hazard-style testing.
This article uses them to:

1. Run one consistent phase-locking test across five carrier/reference-point
   conditions spanning three sleep stages (N2-spindle onset and peak, N3-SO
   trough and upstate, REM-theta) - the "state determines carrier" question
   from `articles/Rythmic_Variance_Control_in_Sleep_theory/plan/02_response.md`
   (S8).
2. Test the previously-ambiguous spindle-onset question with two further,
   independent null constructions grounded in real exposure data (a
   case-control test against the new non-event risk set, and a circular
   time-shift surrogate on the new continuous phase stream) - alongside the
   companion article's own subject-rotation permutation null (relabeled
   "Null 0" here for direct three-way comparison).
3. Sharpen the companion article's fragile timing-efficacy hint into a proper
   *interaction* test, using the new per-event intrinsic-strength covariate
   (sigma-power, amplitude) now available.

Only RichSleep is analyzed here (ANPHY/BOAS have no phase-resolved N3-SO or
REM-theta export); this article does not attempt a three-dataset replication.

## Contents

```
RichSLeep_EAP_v2/
  Autonomic Phase-Locking...typ                main manuscript
  S1_Supplementary_methods.typ                 new data products, phase-locking helper, both new onset-hazard nulls, the qe-interaction model
  S2_Supplementary_data.typ                    full result tables (all CSVs referenced by section)
  S3_Supplementary_QC_Robustness.typ           delivery-validation checks, sample coverage, R3 histogram check, reviewer-facing summary
  S4_Supplementary_Clinical.typ                brief clinician-facing note (not yet clinically translatable)
  S5_Glossary.typ                              article-specific + carried-over NDT/RVC/EAP/companion-article terms
  template_eLife.typ                           shared Typst engine (do not edit; identical to companion articles' copy)
  references.bib                               bibliography (RichSleep-only scope, same as RVC_SLEEP_peak_analysis)
  figures/                                     fig1-fig5 SVGs (cross-carrier bars, rose plots, hazard curve, qe distributions, efficacy interaction)
  data/                                        NMD's 2026-07-12/13 delivery: phase_resolved_v3, slow_oscillation_v1, phase_continuous_v1, event_phase_n3_so_v1, event_phase_rem_theta_v1, non_event_risk_v1 (24 subjects each)
  src/                                          analysis scripts (see below)
  results/rvc_sleep_v2_20260713/{01..06}_*/    frozen pipeline outputs underlying every number in the manuscript/supplements
  handover/                                     delivery-validation handover note (the NMD-improvements request this data answers lives in articles/Rythmic_Variance_Control_in_Sleep_theory/handover/)
  sciencelead/, peer_review/                    provenance folders (empty at authoring time)
```

## `src/` scripts

Numbering starts fresh at `01` (unlike `RVC_SLEEP_peak_analysis`, which
inherited and pruned the companion article's `09`-`14` numbering) since this
article's pipeline is a new, self-contained sequence over the new data
delivery.

- `01_validate_v3_delivery.py` - schema/row-count/QC checks across all six data folders; a `phase_resolved_v3`-vs-`event_phase_v2` bit-identity check on shared columns (proves geometry/phase numbers are unchanged from the companion articles); cross-checks the SO-coupling $N=25$/15-subject power caveat.
- `rvc_sleep_support.py` - shared constants/loaders/statistics, ported from `RVC_SLEEP_peak_analysis`'s copy: path constants for the six new data folders, `load_phase_v3`/`load_n3_so`/`load_rem_theta`/`load_phase_continuous`/`load_non_event_risk`, the generic `run_phase_locking_family` helper, `fit_logit_cluster` (cluster-robust logistic regression, for Test A).
- `02_build_merged_table.py` - merges the companion articles' 190-event geometry table with `phase_resolved_v3`, attaching the new `qe` (intrinsic-strength/SO-coupling) columns.
- `03_multistage_phase_locking.py` - the cross-carrier phase-locking sweep (5 carrier/reference-point conditions $times$ 2 channels = 10 tests); regression checks against the companion article's diary 241/242 raw permutation $p$-values.
- `04_spindle_onset_hazard_model.py` - Test A (case-control logit vs. `non_event_risk_v1`) and Test B (circular time-shift surrogate on `phase_continuous_v1`) for the spindle-onset question; cross-null summary against Null 0.
- `05_qe_interaction_moderation.py` - the intrinsic-strength $times$ alignment interaction test (primary + two robustness qe operationalizations, 3 $times$ 18 tests) and the SO-coupled descriptive-only exploratory check.
- `06_make_figures.py` - generates all 5 manuscript figures from the CSVs above.

Run order for a from-scratch reproduction: `01` -> `02` -> `03` -> `04` -> `05` -> `06`. All scripts are idempotent (each run creates a fresh dated subfolder under `results/`); the manuscript/supplements cite the specific `results/rvc_sleep_v2_20260713/` run frozen at authoring time.

## Building

```
typst compile "Autonomic Phase-Locking Is Strongest at Slow-Oscillation Troughs, Not Spindle Onsets, Across Human NREM and REM Sleep.typ"
typst compile S1_Supplementary_methods.typ
typst compile S2_Supplementary_data.typ
typst compile S3_Supplementary_QC_Robustness.typ
typst compile S4_Supplementary_Clinical.typ
typst compile S5_Glossary.typ
```
