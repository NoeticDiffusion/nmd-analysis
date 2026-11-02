# LEGACY-LOSS-001 — BENCH-001 representation-stage diagnostic

Date: 2026-10-07

## Question and status

This exploratory, post-H1 diagnostic traces participant-grouped EC/EO
discrimination across the frozen BENCH-001 input-to-output chain. It asks where
the H1 recording distinction becomes less visible in the legacy representation.
It is not a new confirmatory hypothesis or a causal test of the individual
transformations.

No EEG is reprocessed. The diagnostic reads only the 200 H1 processed HDF5
files frozen by h1_analysis_freeze_v3.json.

## Frozen stages

1. raw_v2_inputs: the same ten feature columns already used by H1, aggregated
   as the median of finite windows with at least 60 seconds of unique supported
   time.
2. projection_z_inputs: those same ten columns from the HDF5
   features_projection_z surface, with the local per-recording transform and
   feature-baseline metadata retained.
3. legacy_9d: the saved coords_9d coordinates, using
   qc/windows/coords_9d_valid and the same support aggregation.
4. legacy_3d_from_v2: saved mnps_3d values, using
   qc/windows/mnps_3d_valid. Every recording must report effective mode
   from_v2 and no fallback; unsupported 3D rows remain missing.

All stages use the intersection of participants with complete paired EC and EO
recordings and complete features at all four stages. The same 60-second support
rule and recording-level window medians apply. If fewer than 80 participants
remain, the runner stops instead of changing the frozen cohort floor.

## Statistical contract

The runner reuses BENCH-001 H1's exact participant-grouped nested CV helpers:
5 outer folds × 20 repeats, 4 inner folds, C={0.01, 0.1, 1, 10, 100},
standardized L2 logistic regression, and paired participant AUC. It builds one
split schedule and applies it unchanged to every stage. It reports each stage's
AUC and adjacent-stage participant-paired differences with the H1 conditional
2,000-draw bootstrap interval (seed 20261008). These intervals describe
resampling of the observed participant scores conditional on the fitted CV
predictions; they do not include retraining variability.

No multiplicity-adjusted or biological inference is planned. Stage differences
also change dimension and aggregation, so they localize an operational
representation change without isolating one causal mechanism. The dataset's
EC-before-EO ordering caveat remains.

## Provenance and outputs

The runner verifies the H1 frozen input hashes and H1 analysis-script hash
before analysis, then verifies the HDF5 hashes again after analysis. It records
the feature transform/anchor metadata for each input, the exact common
participant set, support rows, model choices, participant predictions, source
hashes, and output hashes in a new output directory separate from H1 and H2.
