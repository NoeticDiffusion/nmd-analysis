# V3-STRUCTURE-001 exploratory analysis protocol

**Status:** exploratory plan frozen before the new structure calculations; not
a prospective or confirmatory analysis. The ds005385 outcomes have already
been inspected in H1/H1R and H2/H2R.

## Question and inputs

Describe overlap among the frozen v3.1 measurement families, their
within-participant EC-to-EO recording-state differences, and their individual
and family-level contribution to recording-state classification. Analyze the
two participant-disjoint ds005385 cohorts separately.

Use only the existing full H1 and H1R processed HDF5 outputs. Both contain the
full v3.1 20-second measurement realization. Do not reprocess EDFs. The 4-second
H2/H2R exports are excluded because their M3 payload is not the frozen
nine-component AR/M3 vector; they are not substitutes for the full H1/H1R
realization.

## Measurement definition and support

Preserve the eight frozen v3.1 measurement families:

| Family | Candidate | Numeric columns |
|---|---|---|
| PCV | M1 | PCV |
| TP | M2 | TP |
| AR/M3 | M3 | AR_pair_01 through AR_pair_09, in canonical order |
| NIE | D1 | NIE |
| RD | D3 | RD |
| OI | E1 | OI |
| SC | E2 | SC |
| ED | E3 | ED |

This is seven scalar families plus the nine-dimensional AR/M3 family: 16
numeric columns grouped into eight families. Do not collapse AR/M3 to a scalar.
For every recording, use the median of finite, computed, valid v3.1 windows
whose unique `[start, end)` interval union reaches the existing 60-second
support minimum. Keep unsupported values missing and report coverage before
complete-case restriction. Qualification remains separate from computability.

## Descriptive structure

For each cohort separately:

1. Calculate pairwise-complete Spearman correlations among the 16 columns for
   Eyes Closed, Eyes Open, and the participant-level difference
   `EyesOpen - EyesClosed`. Report the pair count for every correlation; do
   not add unadjusted significance claims.
2. For those three scopes, calculate covariance spectra after standardizing
   each column across participants within that cohort and scope. Report the
   eigenvalues, explained-variance fractions, cumulative fractions,
   participation-ratio effective rank `(sum(lambda))^2 / sum(lambda^2)`,
   sample size, and zero-variance columns. The standardized spectrum is used
   because the measurement columns have different units and scales.
3. Report participant-level means, standard deviations, medians, and IQRs for
   each column in EC, EO, and paired `EO - EC` differences.

## Exploratory out-of-fold classification

The target is the recorded EC-versus-EO state, not a causal eye-closure effect;
EC always precedes EO in this dataset. The inference unit is the participant,
and both state recordings remain in the same fold.

Within each cohort, use one common participant-complete set across all 16
columns and both states, with a minimum of 80 participants. Reuse the H1
analysis split generator: 5 stratified group outer folds, 20 repeats, 4 grouped
inner folds, and the existing C grid `{0.01, 0.1, 1, 10, 100}`. Reuse the same
schedule for every feature set within a cohort. Standardize only within each
training fold using the existing `StandardScaler` plus logistic-regression
pipeline; select C using the inner-fold participant-paired AUC.

Evaluate 17 fixed feature sets: all 16 columns; one set for each of the eight
families; and eight leave-one-family-out sets. AR/M3 enters or leaves as its
complete ordered nine-column block. Report participant-paired AUC and
participant-bootstrap 95% intervals conditional on the fitted repeated-CV
predictions (2,000 draws; seed 20261008), as well as paired differences from
the full set. These are descriptive, unadjusted comparisons; do not select a
new feature set or claim prospective success from these exposed cohorts.

If fewer than 80 participants are complete across all 16 columns and both
states, publish support coverage only and skip this CV analysis. No imputation
or zero-filling is allowed.

## Interpretation limits

This analysis is descriptive and exploratory. Correlation does not establish
measurement redundancy; family-level ablation does not establish construct
validity. State differences combine state with fixed recording order. All
candidate measurements remain subject to their exported qualification flags.

The analysis script must bind both existing H1/H1R selection and execution
freezes, their exact HDF5 input hashes, this protocol, the H1 helper code and
test hash, and the software versions before calculations begin. Results and
outputs are written to a separate directory under
`I:\AAA_PYTHON_REPOS_BACKUP\homepages\_mnps_v3_structure_001`.
