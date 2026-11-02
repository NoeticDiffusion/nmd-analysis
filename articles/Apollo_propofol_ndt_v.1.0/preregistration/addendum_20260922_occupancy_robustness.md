# Apollo occupancy robustness addendum — 2026-09-22

## Purpose and gate

This is a bounded, post-hoc robustness/reproducibility branch for the frozen
exploratory occupancy scalar in `results/v1_occupancy_20260921/`. It asks whether
the participant-level protocol-phase relocation is materially dependent on one
of the eight existing spectral features or on the particular baseline-only
scale. It does not reopen the measurement boundary, the canonical MNPS
definitions, matching, LOR labels, or any primary manuscript result.

This branch is a computational robustness lock only. It is not a G3 independent
code-review result and does not constitute a G4 confirmatory lock.

## Locked analysis version and input contract

- Analysis version: `apollo_occupancy_robustness_20260922_v1`.
- Unit: participant; each participant contributes at most one recording per
  protocol phase, using the same label/cohort join as the frozen occupancy run.
- Features: exactly the eight frozen `SPECTRAL_FEATURES`, in their existing
  order. No canonical MNPS feature or coordinate definition changes.
- Baseline frame: all baseline rows finite in all eight features; centre is the
  column median. The reference scale is the existing `1.4826 * MAD`, with
  non-finite or `<= 1e-8` scales invalid (`NaN`).
- Reference eligible rows: the original full eight-feature robust-z series and
  existing one-step mask (`finite z`, finite one-step increment, `valid == 1`,
  and observed `dt` in `[3.8, 4.2]`). Every sensitivity variant reuses this
  participant/phase mask. A variant never rescues a missing or ineligible row.
- Missingness: no imputation. A variant is `failure` if it has no finite value
  on the locked reference eligible rows; failures remain explicit and are not
  replaced with zero.
- Randomness: no random procedure is used. Existing bootstrap seed/constants
  are not reused to create new inferential claims.

## Pre-specified sensitivity analyses

1. **Feature decomposition (reference frame):** for each participant and phase,
   on the locked reference eligible rows, report each feature's squared-radius
   contribution `z_j^2`, its row-wise share `z_j^2 / sum_k z_k^2`, and the
   participant-level mean share and median squared contribution. Shares are
   undefined for zero-radius rows and are reported as missing. The eight mean
   shares sum to one up to floating-point tolerance when defined.
2. **Leave-one-feature-out:** for each frozen feature, recompute the median
   Euclidean radius after removing only that coordinate, using the same locked
   eligible rows. Report the participant-level value and the paired contrast
   versus baseline for each protocol phase. This is a decomposition/sensitivity
   diagnostic, not a new endpoint.
3. **Scale sensitivity:** retain the baseline median centre and use either
   (a) sample SD (`ddof=1`) or (b) IQR divided by the normal-consistency
   constant `1.3489795003921634`. Use the same finite/invalid-scale rule and
   the same locked reference eligible rows. Report paired contrasts for all
   protocol phases. These alternatives are descriptive checks of scale
   dependence and were not selected using their resulting contrasts.

## Reporting and failure criteria

For every variant, report participant count, paired support, positive/negative/
zero paired differences, median difference, paired `d_z`, exact sign-test and
Wilcoxon p-values, plus per-row support/failure counts. The branch is
`computationally locked` only when all input, source-code, configuration and
output hashes are written to its lock manifest and focused tests plus the
bounded reference run complete. Scientific robustness is **not established**
by a passing computation: interpretation remains limited by post-hoc selection,
small sample size, and the absence of an independent confirmatory cohort.

## Files and output isolation

The runner is `src/apollo_occupancy_robustness.py`; focused tests are in
`tests/test_apollo_occupancy_robustness.py`. All new outputs go to the fresh
root `results/v1_occupancy_robustness_20260922/`; the frozen
`v1_occupancy_20260921/` files are read-only inputs.
