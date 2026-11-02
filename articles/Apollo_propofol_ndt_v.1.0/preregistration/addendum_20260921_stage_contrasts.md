# Addendum 2026-09-21: within-subject stage panel

Status: dated exploratory addendum. G3 independent review and G4 lock were not completed before this user-requested analysis. Secondary Wilcoxon/BH p-values are therefore exploratory/post-hoc relative to the 2026-09-20 preregistration, which reserved secondary inference for a list frozen before inspecting state effects. This file is that list. It was written before the 80-file dynamical stage contrasts were computed.

## Grain

Valid epochs → recording median → median over repeated recordings in the same subject/phase → paired subject difference (later minus earlier). Equal subject weight. Broadcast one-step operators count as one recording.

## Contrasts

1. first_protocol_sedation − pre_drug_baseline (primary)
2. later_protocol_sedation − pre_drug_baseline
3. recovery − pre_drug_baseline
4. later_protocol_sedation − first_protocol_sedation
5. recovery − first_protocol_sedation
6. recovery − later_protocol_sedation

## Frozen metrics (n = 15)

H1 `diffusion_total`; H2 `diffusion_effective_dimension`; S1 `R_b_over_a`, `A_bD`; S2 `neighbor_gain_q90`, `operator_max_gain_rate`; S3 `history_predictive_gain`; exploratory `diffusion_concentration`, `jacobian_spectral_abscissa`, `jacobian_trace`, `jacobian_rotation_norm`, `jacobian_reactivity_gap`, `turning_rate`, `ftr_g_max_h1`, `ftr_g_max_h2`.

Excluded: destination, resilience, stochastic reachability `w_q`, 9D.

## Inference

H1/H2: exact two-sided sign test; Holm across those two p-values on contrast 1 only. Discovery family: Wilcoxon signed-rank p, BH-FDR across all 15 × 6 tests. Effect: paired Cohen d_z and median difference with 10 000-subject percentile bootstrap, seed 20260920. Scaling remains `subject_anchored` with ComBat disabled, so H1/H2 amplitude claims stay exploratory local chart geometry.
