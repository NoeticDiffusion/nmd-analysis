# MNJ-INFORMATION-001 protocol

**Status:** exploratory diagnostic protocol frozen before the new matrix-level
and static-predictability calculations. The ds005385 EC/EO outcomes have
already been inspected in H2/H2R; this experiment is not confirmatory.

## Question and scope

Diagnose whether the current four summaries of the local 4D Jacobian are
algebraically redundant, predictable from recording-level static PCV/TP/OI/SC,
or insensitive to matrix structure and temporal direction. Analyze the two
participant-disjoint H2/H2R ds005385 cohorts separately. Do not use EC/EO
classification outcomes to select or tune a new model.

Use only the existing H2/H2R processed HDF5 outputs, which preserve saved
4-second PCV, TP, OI, and SC windows. Re-estimate the local Jacobians from those
saved trajectories with the exact derivative, whitening/kNN, and local-Jacobian
kernels and parameters bound in the H2/H2R freezes. Do not reread EDFs or
recompute EEG measurements. Preserve the existing ordered four-coordinate
trajectory `[PCV, TP, OI, SC]`, 4-second step, gap/jump segmentation, and
Jacobian support QC.

## A. Algebraic dependence and recording-level relationships

For each finite center matrix, compute `S=(J+J.T)/2` and
`A=(J-J.T)/2`, then verify
`||J||_F^2 = ||S||_F^2 + ||A||_F^2`. Record absolute and relative numerical
residuals. Preserve all four existing summaries and their definitions,
including singular-value anisotropy. Calculate pairwise-complete Spearman
correlations and pair counts among the four recording-level summaries
separately by cohort and recorded state. Do not add significance tests.

Include a constructed exact counterexample showing that two different signed
Jacobian matrices can have identical four current scalar summaries. Label this
as an algebraic illustration, not an observed dataset result.

## B. Static predictability of the summaries

For each recording-level MNJ summary, predict it from recording-level PCV, TP,
OI, and SC. Use a fixed multi-output linear Ridge model with `alpha=1.0`, no
model selection, training-fold standardization of predictors and targets, and
participant-grouped outer CV using the H1 split generator (5 group folds, 20
repeats). Keep both states from each participant in the same fold. Use one
common participant-complete set per cohort across all eight inputs/targets;
require at least 80 participants or report coverage only.

Average each recording's predictions over the 20 held-out repeats. Report
out-of-fold R-squared separately for each target and participant-bootstrap 95%
intervals (2,000 draws, seed 20261008), conditional on the fitted repeated-CV
predictions. Report model complexity (four predictors per target, four
outputs; 20 linear coefficients/intercepts in total). These estimates measure
predictability under this fixed linear model only; low R-squared does not prove
independence and high R-squared does not prove mathematical redundancy.

## C. Matrix structure and state-space position

Retain every finite estimated 4x4 center Jacobian and its center time, saved
coordinate vector, source file, cohort, participant, recording state,
trajectory segment, support status, and underdetermined-neighborhood flag.
Export signed entries of J, S, and A; sorted singular values; complex
eigenvalues; numerical rank; condition number; trace; and the four existing
scalar summaries. Summarize center results at recording/participant level;
do not treat overlapping centers as independent participants.

For each recording, calculate within-recording Spearman associations between
each fast coordinate and each of the four existing local Jacobian summaries,
then summarize these recording-level associations by cohort. Preserve pair
counts and state separation. Describe marginal distributions of signed
entries and matrix spectra. No local-center significance claims are planned.

## D. Temporal-order control

Apply a time-reversal control to every saved trajectory segment in the H2/H2R
recordings. Reverse its sequence of four-dimensional coordinate rows, relabel
the reversed rows on the same increasing 4-second grid, and estimate Jacobians
with the same kernels and parameters. Pair reversed centers with their
original-coordinate rows. This preserves the points and neighborhood graph
within each segment while reversing temporal direction. Compare signed J and
the four scalar summaries center by center. Report numerical differences and
support counts; do not interpret the control as representing a biological
process. This is a time-direction control, not a general test of every form of
temporal-order dependence.

## Support, provenance, and interpretation

Use the existing 30-center, 50%-finite-center, and 60-second unique-support
requirements when summarizing a recording. Keep unsupported summaries missing.
Report finite, attempted, and underdetermined centers before any complete-case
restriction. Bind the exact H2/H2R analysis freezes, selections, execution
manifests, HDF5 inputs, H2 helper/test, NMD kernel hashes, this protocol,
analysis code, and software versions before calculations begin. Save results
under `I:\AAA_PYTHON_REPOS_BACKUP\homepages\_mnps_mnj_information_001`.

The result may provisionally classify the limitation as redundancy,
under-summary, support uncertainty, or a mixture. Matrix-level sensitivity to
sign/orientation alone does not establish useful task information. The report
must retain the exposed-cohort, fixed-order, and estimator-specific limitations
and must not claim equivalence or biological qualification.
