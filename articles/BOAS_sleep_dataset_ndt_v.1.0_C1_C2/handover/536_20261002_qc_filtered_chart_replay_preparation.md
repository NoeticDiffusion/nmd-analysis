# 536 — 2026-10-02 — QC-overlap filtering and chart replay preparation

## Scope

Continued the outcome-blind C1 support work. The original fold-safe chart surface remains unchanged. The source support audit identifies four apply-H5 epochs whose conservative causal contributor bounds intersect a recorded `raw_joint_eeg_flatline` interval. These rows were still marked primary-eligible and were present in the old apply H5s.

No existing H5 future-coordinate arrays were opened. The interrupted MNDM summarize process may have performed intermediate chart calculations in memory; no new H5 was written and those intermediates were not inspected. No stage/outcome values, predictions, scores, or effects were calculated. The four exclusions below are based only on source-time and QC-interval metadata.

## Prepared candidate

`src/prepare_qc_qualified_chart_surface.py` now creates an isolated candidate input and ten per-fold configs under `results/qc_qualified_fold_safe_chart_replay_20261002_v1/`:

- Source feature surface SHA-256 `3a1fca54625c372f7c43c37d3c19650fd2fce241350f366230bf4e5d9d9b68a2`, 92,545 rows / 100 recordings.
- Four rows are removed before anchor fitting, one for each recorded flatline overlap: `sub-85` epoch 478, `sub-125` epoch 27, `sub-105` epoch 831, and `sub-82` epoch 18.
- Candidate feature surface: 92,541 rows / 100 recordings, SHA-256 `fbd31e8828ae4288322f723f3d82ffaed0da22d13802e734f838eaff1c58829c`.
- The output carries a 100-recording file index and fold-specific training/apply configs. Each training config fits a new anchor from the filtered surface; its apply config points at that new anchor.

The input table copies predictor columns unchanged for retained rows. This is an engineering candidate pending chart regeneration and a fresh metadata-only support preflight; it is not a qualified C1/C2 surface.

## Chart-generation attempt

A fold-0 training summarize run was started and interrupted before it wrote any H5. The intended run directory is empty. For scale reference, the old fold-0 training run contains 80 H5 files totaling 12,132,991,189 bytes; the old manifest creation to final H5 timestamp span is about 7,189 seconds. This is a historical wall-clock span, not a controlled runtime estimate. A 500-file five-fold replay at the old median H5 size would be about 75.8 GB, before any extra metadata.

The interruption is recorded in `results/qc_qualified_fold_safe_chart_replay_20261002_v1/provenance/chart_replay_execution_status.json`. No raw EDF copy was made, and this preparation did not rerun raw EDF feature extraction.

## Current decision state

The existing article-local C1 v2 support audit remains `QUALITY_OVERLAPS_PRESENT_REQUIRE_SUPPORT_REVIEW`; it found four rows whose quality overlap affects otherwise eligible forecast paths. C1’s score is locked but remains unscored. C2 candidate v2 remains unqualified. The protocol and analysis gate stays closed.

To proceed with this candidate, generate each fold’s new training anchor and H5s, then its apply H5s, followed by the outcome-blind identity/time/support preflight. Do not interpret the candidate input filter itself as authorization to calculate scores or effects.
