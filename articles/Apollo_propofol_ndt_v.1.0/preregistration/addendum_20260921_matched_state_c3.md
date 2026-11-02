# Addendum 2026-09-21: matched-state C3 (first sedation vs baseline)

Status: dated exploratory addendum. Frozen after `sl_001.md` and before
`results/v1_c3_20260921/`. G3 independent review and G4 lock were not
completed. This is not a confirmatory H1/H2 run and does not reopen the
132-test Jacobian-α/L1–L3 panel.

The 132-test screen remains discovery. q = 0.24 is not reinterpreted as
confirmation. Protocol phase 3 is not unresponsiveness. Chart-Jacobian α
is not one-step L3.

## Question

Within subject, at approximately the same current MNPS location \(x_t\),
does first-protocol sedation change the subsequent one-step increment law
relative to pre-drug baseline?

This is an empirical approximation of NDT-C3,
\(K_h^{x|\gamma_1}(x,\cdot)\neq K_h^{x|\gamma_2}(x,\cdot)\) at matched \(x\),
on the exported chart. It is not a causal drug-effect claim.

## Match space (outcome-blind)

Primary: Euclidean distance on `coords_3d_subject_anchored`.
Matching uses present \(x_t\) only. Increments, \(b\), \(a\), and Jacobian
α are not used to choose pairs.

Limitation: G2 `feature_fit_scopes` is
`local_input_frame_rows_selected_by_original_finite_feature_mask` and
`common_phase_anchor_documented=false`. Matching is therefore
same-local-chart-coordinate, not a proven common physical state. A
baseline-derived re-anchor of raw features is a later sensitivity, not
this primary.

## Caliper and assignment

1. Eligible sources: finite \(x_t\) and finite one-step `dx_dt` with
   `observed_dt` in \([3.8, 4.2]\) s.
2. Caliper, from **baseline only**: median leave-one-out nearest-neighbour
   Euclidean distance among eligible baseline sources.
3. Assignment: greedy one-to-one, sedation → baseline, sorted by
   increasing distance, no replacement, keep if \(d\le\) caliper.
4. Subject included if \(\ge 20\) matched pairs.

## Primary endpoints (Holm of 2)

Later minus earlier on subject summaries of the matched sources.
Prediction: first sedation < baseline.

1. `matched_speed`: median \(\|dx/dt\|_2\)
2. `matched_spread`: \(\operatorname{Tr}(\mathrm{Cov}(dx/dt))\) with
   sample covariance over matched sources

These are realized one-step increment geometry, not identified Itô \(b\)
or \(a\), and not L2/L3 operators.

## Controls (not Holm)

- Unmatched: same two scalars on all eligible sources (occupancy-uncontrolled).
- Random match: same pair count, baseline partners shuffled among eligible
  baseline sources, seed 20260920 (ignores \(x\)).
- Spectral sensitivity: same algorithm after concatenating the eight
  MNPS-used `features_raw` columns (`eeg_delta`, `eeg_theta`, `eeg_alpha`,
  `eeg_beta`, `eeg_gamma`, `eeg_alpha_theta`, `eeg_beta_alpha`,
  `eeg_sample_entropy`), robust-z scored from baseline median/MAD only.

## Inference

Exact two-sided sign test and Wilcoxon on the 20 subject differences.
Holm across the two matched primaries only. Effect: paired Cohen \(d_z\)
and median difference with 10 000-subject percentile bootstrap, seed
20260920. Reporting gate: \(\ge 10\) subjects with a finite nonzero
difference. Exploratory; G4 not locked. Export remains `subject_anchored`.

## Not in this run

L2/L3 one-step operators; destination; resilience; iterated L4; expanding
the 132-test panel; LOR/ROR segmentation; confirmatory amplitude decrease;
consciousness.

## Prospective G3/G4 family (declared, not executed here)

If a later lock is requested: co-primary recording-level
`chart_drift_b_hat_norm` and `diffusion_total` on first sedation −
baseline, Holm of 2; recovery − first sedation as directional
reversibility; Jacobian α as a predefined dissociation endpoint.
`diffusion_a_hat_frob` is a diffusion-magnitude sensitivity, not a third
primary. That lock still requires G3 independent review.
