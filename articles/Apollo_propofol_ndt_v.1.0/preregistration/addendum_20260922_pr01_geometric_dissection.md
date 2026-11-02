# PR-01 geometric dissection and covariance-aware sensitivity

## Status and scope

This is a dated, **post-hoc exploratory** analysis addendum written before its
execution.  It responds to peer-review item PR-01 and does not alter the
frozen `v1_occupancy_20260921` outputs, their feature contract, their
baseline-only robust-z frame, or their one-step eligibility masks.

## Questions

1. Does the observed radial displacement contain a shift of the eligible
   phase-cloud centre, increased within-phase dispersion, or both?
2. Does the ordered phase trajectory remain visible in one covariance-aware
   baseline frame?
3. How does C3 match support change when the frozen subject-specific caliper
   is multiplied by 0.5, 1.0, 1.5, and 2.0?  This is a support diagnostic, not
   a replacement primary gate.
4. What deterministic bootstrap uncertainty intervals accompany the existing
   later-sedation and recovery paired effects, and the exploratory Spearman
   association with behavioural hit count?

## Fixed contract

- Participants and protocol labels: the frozen G1/G2 tables.
- State features: delta, theta, alpha, beta, gamma, alpha/theta, beta/alpha,
  and sample entropy, exactly as in the frozen occupancy analysis.
- Reference frame and per-phase source eligibility: baseline robust median and
  MAD scale plus the existing finite/observed-dt [3.8, 4.2] s mask.
- Participant is the sole inferential unit.  All results are descriptive and
  exploratory; no G3/G4 claim is created.
- Centre displacement is the Euclidean norm of the coordinatewise median of
  eligible phase points.  Dispersion is the median Euclidean distance from
  those same points to their phase median.
- The covariance-aware sensitivity uses the covariance of *eligible baseline*
  robust-z points, shrunk deterministically by 10% toward its mean-variance
  diagonal before symmetric inverse-square-root whitening.  It reuses each
  phase's original eligibility mask.
- Bootstrap intervals use 10,000 participant resamples and seed `20260922`.
  The Spearman interval resamples paired participant rows.

## Outputs and interpretation boundary

Outputs will be written only to
`results/v1_pr01_geometric_20260922_final2/`, with a manifest hashing inputs, plan,
code, and generated tables.  A centre result may support the narrowly worded
description “phase-cloud centre displacement in this measured chart”; it does
not establish latent-state relocation, consciousness, a clinical biomarker,
or a changed conditional transition law.  The caliper curve cannot recover a
failed common-support gate by choosing a wider caliper.
