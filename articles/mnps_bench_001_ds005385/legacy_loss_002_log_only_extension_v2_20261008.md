# LEGACY-LOSS-002 — log-only extension, v2

Date: 2026-10-08  
Status: exploratory post-run extension. Not confirmatory or outcome-blind.

## Amendment history

The primary five-arm outcomes were already known when the log-only extension
was proposed. In the first execution attempt, the two arms were fitted, and
the log-only mean participant AUC (`L`) was observed as 0.94. The attempt then
stopped because it required exact raw out-of-fold probability reproduction
against the saved primary run. The primary run used scikit-learn 1.7.2; the
current runtime is 1.8.0. Re-fitting identical inputs with a different
scikit-learn version does not reproduce probabilities exactly (observed
maximum absolute difference 0.1178191296). This is a runtime reproducibility
failure, not a transformation-contract mismatch.

This v2 protocol keeps the same single `L - raw` question and does not use the
observed log-only result to change features, model grid, or splits. It removes
the cross-version exact-probability gate. Instead, it records the discrepancy
as a limitation and computes both paired arms in the same current runtime,
with the same participant order and the same shared H1 nested grouped-CV split
schedule. The first partial attempt and v1 freeze remain preserved.

## Frozen contrast and implementation

Compare the saved raw arm with one `L` arm over the ten historical raw-v2
features. Apply feature-specific `log10` only to `eeg_delta`, `eeg_theta`,
`eeg_alpha`, and `eeg_gamma`; do not apply recording-level robust-z or
clipping. Leave the remaining six columns unchanged.

Use the validated 60-second support medians from the primary LEGACY-LOSS-002
run. Verify that every configured log-source window was positive. Since
`log10` is strictly increasing on positive inputs, it commutes with the saved
support-median aggregation, so applying it to the saved median is equivalent
to applying it per window and then aggregating.

Use the exact same 100 complete participants, ordered features, participant
order, H1 split-schedule helper, nested grouped-CV helper, model grid,
training-fold standardization, and state row order as the primary analysis.
Refit both `raw` and `L` in this runtime. Compare the new raw OOF probabilities
against the primary saved probabilities and record the maximum absolute
difference. Do not use that cross-version probability difference as a stop
condition. The paired contrast remains within-runtime `L - raw` participant
AUC with a 2,000-draw participant bootstrap (seed 20261014), conditional on
the repeated-CV predictions.

## Provenance and interpretation

Freeze this v2 protocol and script before the final v2 fit. Validate the
primary output hashes and bind this run to the primary freeze, H1 helper and
source freeze, saved raw feature table, and saved primary predictions. Read no
EDF and recompute no EEG features.

This is post-hoc and exploratory. It describes the operational effect of
log-only transformation under this representation, aggregation, classifier,
current software runtime, and exposed ds005385 cohort. It cannot establish a
biological mechanism or replace the historical MNPS 2.0 comparator. The
cross-version prediction mismatch remains an explicit reproducibility limit.
