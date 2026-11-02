# Addendum 2026-09-21: Jacobian-α + L1/L2/L3 panel

Status: dated exploratory addendum. Written after the L0–L4 coverage inventory and before the 80-file within-subject contrasts in `results/v1_level_20260921/`. G3 independent review and G4 lock were not completed. Inference is therefore exploratory/post-hoc relative to the 2026-09-20 preregistration.

Chart-Jacobian α (`jacobian/derived_metrics/v1/series/spectral_abscissa`) is Family B chart linearization, not one-step L3.

## Grain

Valid epochs → recording median (tensor reductions: Frobenius on `a_hat`/`phi_hat`, L2 on `b_hat`/`affine_mean_rate`, trace on innovation covariance) → median over repeated recordings in the same subject/phase → paired later minus earlier. Complete-case pairs only. Broadcast one-step operators count as one recording.

## Contrasts

Same six protocol-phase pairs as `addendum_20260921_stage_contrasts.md`.

## Frozen metrics (n = 22; identities with finite values only)

- Jacobian α: `jacobian_alpha`
- L1: `diffusion_a_hat_frob`, `diffusion_total`, `diffusion_effective_dimension`, `diffusion_concentration`, `chart_drift_b_hat_norm`, `neighbor_gain_q90`, `neighbor_gain_rate_q90`, `neighbor_separation_rate`, `cloud_volume_change_rate`, `history_predictive_gain`
- L2 (lag-1): `one_step_phi_frob`, `one_step_affine_mean_rate_norm`, `one_step_innovation_trace`, `operator_max_gain_rate`, `operator_volume_gain_rate`, `operator_rotation_rate`, `history_conditioned_phi_frob`
- L3 (lag-1 generator proxy): `one_step_spectral_abscissa`, `one_step_numerical_abscissa`, `one_step_divergence`, `one_step_generator_rotation_norm`

Omitted because empty or not identified on this export: `A_bD`, `R_b_over_a`, lag-2 one-step, destination, resilience, iterated L4/FAR. Stochastic reachability `w_q` is not an identified L4 horizon and is omitted.

## Inference

Wilcoxon signed-rank p; BH-FDR across finite tests in this panel, plus BH within level and within contrast. Effect: paired Cohen d_z and median difference with 10 000-subject percentile bootstrap, seed 20260920. L2/L3 n is smaller because lag-1 identification is partial and phase-imbalanced. Scaling remains `subject_anchored` with ComBat disabled. Not consciousness. Not confirmatory amplitude.
