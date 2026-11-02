# NORMALIZATION-CONTRACT-001 — robust-z invariants

**Status:** exploratory audit of a frozen transformation and existing saved
features. It does not change a measurement, aggregation, or classifier.

## Question and boundary

Verify the implementation-level consequences of recording-local robust-z
normalization described after LEGACY-LOSS-003:

1. An additive offset and a positive multiplicative scale applied uniformly to
   all samples in one recording are removed by local robust-z, within numeric
   precision.
2. One transform shared across two states in a recording can preserve their
   within-recording location difference.
3. The median of robust-z values on the same support is zero, up to numeric
   precision.
4. Normalization need not remove variance-shape or temporal-order information.
5. A fixed reference transform does not recenter each target recording, so
   deviations from that reference remain visible.
6. Count exact and near-zero values among the 2,000 saved LEGACY-LOSS-003 R-arm
   recording aggregates.

Use only
outputs/_mnps_legacy_loss_003/stage_feature_values.csv for the empirical
audit and the frozen mndm.projection._apply_column_pipeline helper for
synthetic transforms. Do not reopen EDF, HDF5, or source recordings. Do not
rerun EEG processing or classification. Do not modify LEGACY-LOSS-003,
canonical v3.1 values, or the historical v2 implementation.

## Prespecified computation

The empirical population is exactly the rows with arm R in the saved stage
feature table. Require 2,000 finite values, comprising 100 participants, two
states, and ten features. Report counts for exactly zero and absolute value
at most 1e-12, 1e-6, and 1e-5, globally and by feature; also report the maximum
absolute value and number of distinct saved values.

Synthetic signals use NumPy's default_rng(20261008). The robust-z arm calls
the frozen projection helper with the pipeline robust_z, which uses the
repository's float32 median and 1.4826 × MAD scale, with the historical
epsilon-floor compatibility policy. Record comparisons and tolerances in
machine-readable output. Verify local offset and positive-scale invariance
with absolute tolerance 1e-6. Verify the same-support median is within 1e-6
of zero. For a shared two-state transform, compare each state's normalized
median; as a control, transform each state locally and confirm its median
centers independently. For temporal structure, compare a deterministic
first-order autoregressive series with a permutation of the same samples:
median and variance should be unchanged while lag-1 autocorrelation changes.
For fixed-reference scaling, estimate median and 1.4826 × MAD once from a
separate reference vector, then apply them unchanged to a signal and its
constant-offset version.

## Interpretation

These are algebraic and implementation checks, not evidence that any
transformation is beneficial for a scientific task. The empirical counts
describe the saved legacy aggregation only. Local robust-z can be useful for
relative variation while removing recording-level location and positive
scale; a shared or fixed reference answers a different question. Window-level
values and temporal order are not replaced by their recording median.

## Outputs

Write results to a new
outputs/_mnps_normalization_contract_001/ directory: an empirical per-feature
CSV, synthetic invariant JSON, concise Markdown results, and a hash manifest.
Preserve the upstream source table and historical outputs.
