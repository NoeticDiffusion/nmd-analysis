# LEGACY-LOSS-002 — window-level log-only extension, v3

Date: 2026-10-08  
Status: post-hoc exploratory correction; outcomes from the five-arm analysis
and the earlier log-after-aggregation extension are already known.

## Correction and question

The earlier extension applied `log10` to saved recording medians. It described
that as equivalent to window-level log followed by median aggregation. That
equivalence is false for an ordinary median with an even number of values,
because the median averages the two middle values. The v2 result therefore
answers a narrower question: log-after-aggregation. Preserve it under that
label, and use this new v3 extension for the frozen feature-transform question:

> What is the paired participant AUC difference when feature-specific log10
> is applied to each saved raw window before the exact support-preserving
> median aggregation, with no robust-z or clipping?

This correction was made after the v1/v2 log-only AUC results were observed;
the v3 analysis is explicitly post-hoc and cannot be considered confirmatory.

## Frozen arms and computation

Read the 200 frozen processed H1 HDF5 files listed in the primary
LEGACY-LOSS-002 freeze. Verify each source SHA256 before and after use. Read
only saved `features_raw` windows, `window_start`, and `window_end`; do not
read EDF or recompute EEG features.

Use the exact ten ordered historical raw-v2 features. `raw` is the median of
finite saved raw windows over the exact H1 unique-support rule. `L_window`
applies `log10` per finite window only for the four feature columns declared
log-configured in the primary frozen transform contract, preserving missing
positions; the remaining six columns are unchanged. Then use the same exact
support-preserving median helper. Require zero nonpositive finite windows for
the four log-configured features. Verify the recomputed raw medians match the
primary frozen raw summary values within absolute tolerance `1e-12`.

Use the same 100 complete participants, feature order, H1 participant order,
nested grouped-CV helper, shared split schedule, model grid, training-fold
standardization, state row order, and software runtime for both arms. Compare
`L_window - raw` paired participant AUC with a 2,000-draw participant
bootstrap (seed 20261015), conditional on repeated-CV predictions. Refit raw
within v3 and record the difference between its OOF probabilities and the
primary saved probabilities. The primary run used scikit-learn 1.7.2; v3 uses
1.8.0, so exact cross-version probabilities are not a stop condition.

## Provenance and limits

Freeze the v3 script, this amendment, the source H5 manifest and hashes, the
primary LEGACY-LOSS-002 artifacts, and the v2 run manifest before v3 fitting.
Write outputs to a new directory. Preserve v1/v2 files and outputs.

This estimates an operational post-hoc transform effect on the exposed
ds005385 cohort under the exact measurement aggregation, classifier, splits
and current runtime. It does not establish a biological mechanism or replace
historical MNPS 2.0. The earlier v2 contrast is not a substitute for the
window-level result.
