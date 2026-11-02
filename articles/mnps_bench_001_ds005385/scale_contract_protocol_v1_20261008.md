# SCALE-CONTRACT-001 — Derived analysis scales

**Status:** exploratory, post-hoc method analysis. Freeze this protocol, script,
source table, and runtime before calculating new scale comparisons.

## Question and measurement boundary

Keep the frozen v3.1 measurement realization unchanged. Use the existing
V3-STRUCTURE-001 recording-level medians for the eight candidate families:
PCV, TP, the ordered nine-value AR/M3 vector, NIE, RD, OI, SC, and ED. The
canonical table therefore has 16 numeric columns. No estimator, window,
support rule, median, coordinate order, or qualification flag is changed.
Transformations below create derived analysis representations only.

This analysis uses the already exposed, participant-disjoint ds005385 H1 and
H1R cohorts (100 participants each), each with one EC and one EO recording.
Values are the saved medians of supported v3.1 windows. Read only the
V3-STRUCTURE-001 recording_features.csv; do not reopen HDF5 or EDF files.
The upstream freeze and run manifest carry the source selection and HDF5
provenance.

## Prespecified scales

Compare three representations:

1. x_native: the saved 16-column recording-level measurement vector.
2. T_log1p: apply natural log(1+x) to each saved scalar or AR/M3 component
   **after** recording-level aggregation. The estimators define these observed
   quantities as nonnegative: PCV is a standard deviation, TP is 1-rho(1),
   AR/M3 is 1-r for adjacent-block vector correlations, NIE is graph
   efficiency, RD is a mean Euclidean distance, OI is normalized entropy, SC
   is an observed/reference phrase-count ratio, and ED is a covariance
   participation ratio. log1p is defined at zero and requires no epsilon.
   Before analysis, require all finite saved values to be nonnegative; stop if
   this domain gate fails. Do not clip, shift, impute, or silently omit values.
3. z_fixed_reference: in each model training fold, compute the mean and
   population standard deviation of each native feature using training
   participants and both their states only. Apply those parameters unchanged
to the held-out participants. Use scale 1 for a constant or numerically
near-constant feature, with the same float64 variance-error bound used by the
frozen runtime's StandardScaler. This is a fold-specific training-sample
reference, not a healthy normative reference.

All transformations act on the supported recording medians, not on EEG
samples or individual windows. In particular, log1p(median(windows)) is not
claimed to equal median(log1p(windows)).

## Evaluation

### Within-cohort prediction

For H1 and H1R separately, classify recorded EO versus EC using the complete
16-column vector, with participant as the grouped unit. Require at least 80
complete participant pairs; do not impute or zero-fill. Use 20 repeats of
5-fold stratified grouped outer CV, 4-fold grouped inner CV, and
C={0.01,0.1,1,10,100}. Generate one split schedule per cohort and reuse it
for all three scales. Use the existing H1 helper's split-seed rule and
participant-paired AUC. x_native and T_log1p use the existing
training-fold StandardScaler plus L2 logistic model. For z_fixed_reference,
fit the training-fold reference at each inner and outer fit and then fit the
same L2 logistic model without a second scaler. Record paired AUC, participant
bootstrap intervals conditional on repeated out-of-fold predictions, paired
contrasts versus x_native, chosen C values, predictions, and the maximum
absolute probability difference between x_native and z_fixed_reference.

Also run the same nested grouped CV separately for each of the 16 canonical
columns under x_native and T_log1p, reusing the cohort split schedule. Report
the paired participant AUC, bootstrap interval, and paired AUC contrast for
each feature and scale. This is a descriptive single-coordinate prediction
audit; it does not select or qualify coordinates. z_fixed_reference is not
run again for single-feature prediction because it is the same positive
training-fold affine standardization as the native model's StandardScaler.

Because the classifier's StandardScaler estimates the same training-fold
mean and standard deviation as z_fixed_reference, these two model arms are
expected to be affine-equivalent. Verify this numerically; the reference layer
is still useful as a named analysis representation, but should not be
described as improving prediction if the predictions are equivalent.

### H1-to-H1R transport check

Use H1 only to select C by 4-fold participant-grouped CV for each scale, with
seed 20261008 and the same participant-paired AUC. Fit each scale's final
model on all H1 participants and evaluate it once on the disjoint H1R
participants. Fit the fixed-reference parameters only on H1. Report paired
AUC and a participant bootstrap interval. This is a same-dataset
disjoint-cohort transport check, not independent external validation or a
identified nuisance-effect analysis.

### Scale behavior and unavailable criteria

For each feature, report observed domain; paired EO-minus-EC mean, SD, and
median absolute change on native and T_log1p scales; rank agreement of
participant-level changes; change-sign agreement; and between-participant SD
of each participant's EC/EO midpoint. These are descriptive summaries.
Report short-term test-retest reliability and nuisance robustness as
unavailable: the source has no repeated same-state session and this frozen
table has no identifiable nuisance strata. Do not substitute adjacent
windows, H1/H1R membership, or classifier performance for those quantities.

Do not select a transform based on a preferred p-value or a single AUC.
Report all three scales and all 16 coordinates. Do not run ComBat: batch
factors are not identified in this scope.

## Interpretation limits

This is exploratory post-hoc work on exposed outcomes. It cannot qualify a
measurement, establish a biological mechanism, identify nuisance effects,
demonstrate test-retest reliability, or support prospective performance. H1
and H1R are disjoint participant subsets of the same dataset and their
recorded EC/EO order is fixed. Any transform conclusion is conditional on
these saved v3.1 medians, complete cases, models, split schedule, and runtime.
All scale arms in this run share one newly frozen runtime and split schedule.
Do not compare its absolute AUC values directly with V3-STRUCTURE-001: that
upstream analysis recorded a different NumPy/scikit-learn runtime.

Keep all outputs in a new scale-contract directory. Preserve original v3.1
values, upstream artifacts, and prior results.
