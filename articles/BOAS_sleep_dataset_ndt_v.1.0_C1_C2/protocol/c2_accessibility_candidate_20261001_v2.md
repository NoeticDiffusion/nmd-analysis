# C2 accessibility candidate v2 — 2026-10-01

## Status

**Outcome-blind candidate specification only; not qualified and not an authorization to score outcomes.** This version tightens the training-row cross-fit boundary and fixes the scalar's coordinate units. It does not amend the source preregistration or lock the downstream C2 outcome score. The previous candidate note remains as history and is superseded on those two points.

## Candidate and inheritance

Keep the v1 candidate's primary 3D `[m,d,e]`, h1, nearest training transition per PID, `k=32`, training-only leave-one-PID-out support-radius calibration, and `log det` of the selected training future-endpoint covariance. Preserve its exact transition eligibility, missingness, support, and failure rules except for the amendments below. Use the fold's existing chart coordinates as inputs; no C1 or C2 scores, condition contrasts, or outcomes are part of this feature definition.

For an apply query, the transition library, radius calibration, and coordinate scale use only the complete outer-training PID roster. For a training OOF query, the queried PID must be excluded from **both** the transition library/radius calibration and the coordinate-scale fitting roster. This prevents the PID's own future chart states from entering its feature through either the selected endpoints or a globally fitted IQR scale. The query API must reject an OOF query whose PID appears in either roster.

The participant-balanced coordinate IQR is used for neighbor geometry and covariance calculation. If `D = diag(s)` contains the fitted coordinate scales and `Sigma_z` is the selected covariance in scaled units, report

`A_C2 = log det(Sigma_z) + 2 * sum(log(s))`.

This is the log-determinant in the fixed native units of the supplied fold-specific chart coordinates. Training-OOF rows use a scale fitted without their PID; apply rows use the full outer-training scale. Their neighbor geometry can therefore differ because the training row is cross-fitted, while the reported covariance unit stays the same. Equal-distance transitions use a stable identity order `(recording_id, segment_id, epoch_id)` as the tie-break, so file row order cannot change selected endpoints. The feature output records the transition-library and scale-training PID roster counts and SHA-256 digests plus the numeric-scale digest so these inputs can be audited.

## Qualification requirements

Before the feature is used in any C2 contrast, an outcome-blind qualification must establish:

- Exact chart-row identity, coordinate order, timestamps, source-file hashes, causal contributor bounds, and source-quality interval binding for every query and training transition. Unknown or intersecting support fails closed. The existing H5 producer/support contract remains unresolved, so no current H5 coordinate values have been admitted by this note.
- Outer-fold locality and OOF exclusion from both transition and scale rosters, using the emitted roster digests. Apply PIDs must be disjoint from both outer-training rosters.
- Bind the numeric scale digest to the hash of the actual scale-fitting input rows and the fold-local fitting code. The estimator currently trusts the caller to provide a scale fitted on the declared roster; a roster digest alone cannot prove how the numeric scale was produced.
- Target-invariance checks: changing apply targets, later rows, stage fields, or outcomes cannot change a current-origin feature; changing an OOF PID's own future transitions cannot change its feature or scale roster. The query schema continues to reject target, stage, and outcome fields.
- Explicit unavailable reasons and retained rows for invalid support/QC, gaps, too few distinct training PIDs, out-of-radius queries, and singular/non-finite covariance. No interpolation, imputation, or zero substitution.
- Outcome-blind per-PID/per-recording coverage and support summaries for all folds. The 11-column EEG spectral baseline described in handover 532 remains a separate unqualified input family until its own temporal/source-support and preprocessing contract passes.

Any later C2 score, effect, or claim requires its own frozen outcome-model/score protocol, independent review, and authorization. No such analysis was run for this candidate update.
