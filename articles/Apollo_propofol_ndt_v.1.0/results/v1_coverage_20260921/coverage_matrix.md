# Apollo dynamical-family coverage (L0–L4)

Export `neuralmanifolddynamics_Sedation-RestingState_20260918_075713`. Files read: 80/80.

A file **has a value** when the primary series contains at least one finite number.
`computed` is the group certificate. This is an inventory, not a propofol contrast,
not Itô identification, and not consciousness.

## Level rollup

| Level | Identities | Any finite on ≥1 file | Computed on all 80 | Median file coverage | Files with any identity finite |
| --- | ---: | ---: | ---: | ---: | ---: |
| L0 | 4 | 4 | 4 | 100.0% | 80/80 |
| L1 | 13 | 11 | 13 | 100.0% | 80/80 |
| L2 | 13 | 7 | 0 | 37.5% | 50/80 |
| L3 | 8 | 4 | 0 | 28.7% | 46/80 |
| L4 | 4 | 2 | 1 | 45.6% | 80/80 |

## Headline identities

| Metric | Level | >=1 finite | Computed/exported | Status mode |
| --- | --- | ---: | ---: | --- |
| `increment_covariance_level0` | L0 | 80/80 (100.0%) | 80/80 (100.0%) | `computed` |
| `realized_velocity_level0` | L0 | 80/80 (100.0%) | 80/80 (100.0%) | `computed` |
| `diffusion_a_hat` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | `computed` |
| `diffusion_A_bD` | L1 | 0/80 (0.0%) | 80/80 (100.0%) | `computed` |
| `chart_drift_b_hat_pooled` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | `computed` |
| `amplification_neighbor_gain_q90_level1` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | `computed` |
| `history_predictive_gain_level1` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | `computed` |
| `turning_angle_level0` | L0 | 80/80 (100.0%) | 80/80 (100.0%) | `computed` |
| `one_step_lag1_affine_one_step_map_level2` | L2 | 46/80 (57.5%) | 46/80 (57.5%) | `computed` |
| `history_conditioned_operator_level2` | L2 | 30/80 (37.5%) | 30/80 (37.5%) | `insufficient_support` |
| `one_step_lag1_spectral_abscissa_level3` | L3 | 46/80 (57.5%) | 46/80 (57.5%) | `computed` |
| `one_step_lag1_iterated_horizon_map_level4` | L4 | 0/80 (0.0%) | 0/80 (0.0%) | `insufficient_support` |
| `one_step_lag2_affine_one_step_map_level2` | L2 | 0/80 (0.0%) | 0/80 (0.0%) | `insufficient_support` |
| `destination` | adjacent | 0/80 (0.0%) | 0/80 (0.0%) | `not_testable` |
| `resilience` | L4 | 0/80 (0.0%) | 0/80 (0.0%) | `not_testable` |
| `reach_3d` | L4 | 80/80 (100.0%) | 80/80 (100.0%) | `computed` |

## One-step / L4 by protocol phase

| Phase | Metric | >=1 finite | Computed | Status mode |
| --- | --- | ---: | ---: | --- |
| `first_protocol_sedation` | `diffusion_a_hat` | 20/20 (100.0%) | 20/20 (100.0%) | `computed` |
| `first_protocol_sedation` | `one_step_lag1_affine_one_step_map_level2` | 9/20 (45.0%) | 9/20 (45.0%) | `insufficient_support` |
| `first_protocol_sedation` | `history_conditioned_operator_level2` | 2/20 (10.0%) | 2/20 (10.0%) | `insufficient_support` |
| `first_protocol_sedation` | `one_step_lag1_spectral_abscissa_level3` | 9/20 (45.0%) | 9/20 (45.0%) | `not_testable` |
| `first_protocol_sedation` | `one_step_lag1_iterated_horizon_map_level4` | 0/20 (0.0%) | 0/20 (0.0%) | `not_testable` |
| `first_protocol_sedation` | `one_step_lag2_affine_one_step_map_level2` | 0/20 (0.0%) | 0/20 (0.0%) | `insufficient_support` |
| `first_protocol_sedation` | `resilience` | 0/20 (0.0%) | 0/20 (0.0%) | `not_testable` |
| `first_protocol_sedation` | `reach_3d` | 20/20 (100.0%) | 20/20 (100.0%) | `computed` |
| `later_protocol_sedation` | `diffusion_a_hat` | 20/20 (100.0%) | 20/20 (100.0%) | `computed` |
| `later_protocol_sedation` | `one_step_lag1_affine_one_step_map_level2` | 13/20 (65.0%) | 13/20 (65.0%) | `computed` |
| `later_protocol_sedation` | `history_conditioned_operator_level2` | 10/20 (50.0%) | 10/20 (50.0%) | `insufficient_support` |
| `later_protocol_sedation` | `one_step_lag1_spectral_abscissa_level3` | 13/20 (65.0%) | 13/20 (65.0%) | `computed` |
| `later_protocol_sedation` | `one_step_lag1_iterated_horizon_map_level4` | 0/20 (0.0%) | 0/20 (0.0%) | `insufficient_support` |
| `later_protocol_sedation` | `one_step_lag2_affine_one_step_map_level2` | 0/20 (0.0%) | 0/20 (0.0%) | `insufficient_support` |
| `later_protocol_sedation` | `resilience` | 0/20 (0.0%) | 0/20 (0.0%) | `not_testable` |
| `later_protocol_sedation` | `reach_3d` | 20/20 (100.0%) | 20/20 (100.0%) | `computed` |
| `pre_drug_baseline` | `diffusion_a_hat` | 20/20 (100.0%) | 20/20 (100.0%) | `computed` |
| `pre_drug_baseline` | `one_step_lag1_affine_one_step_map_level2` | 10/20 (50.0%) | 10/20 (50.0%) | `computed` |
| `pre_drug_baseline` | `history_conditioned_operator_level2` | 7/20 (35.0%) | 7/20 (35.0%) | `insufficient_support` |
| `pre_drug_baseline` | `one_step_lag1_spectral_abscissa_level3` | 10/20 (50.0%) | 10/20 (50.0%) | `computed` |
| `pre_drug_baseline` | `one_step_lag1_iterated_horizon_map_level4` | 0/20 (0.0%) | 0/20 (0.0%) | `insufficient_support` |
| `pre_drug_baseline` | `one_step_lag2_affine_one_step_map_level2` | 0/20 (0.0%) | 0/20 (0.0%) | `insufficient_support` |
| `pre_drug_baseline` | `resilience` | 0/20 (0.0%) | 0/20 (0.0%) | `not_testable` |
| `pre_drug_baseline` | `reach_3d` | 20/20 (100.0%) | 20/20 (100.0%) | `computed` |
| `recovery` | `diffusion_a_hat` | 20/20 (100.0%) | 20/20 (100.0%) | `computed` |
| `recovery` | `one_step_lag1_affine_one_step_map_level2` | 14/20 (70.0%) | 14/20 (70.0%) | `computed` |
| `recovery` | `history_conditioned_operator_level2` | 11/20 (55.0%) | 11/20 (55.0%) | `computed` |
| `recovery` | `one_step_lag1_spectral_abscissa_level3` | 14/20 (70.0%) | 14/20 (70.0%) | `computed` |
| `recovery` | `one_step_lag1_iterated_horizon_map_level4` | 0/20 (0.0%) | 0/20 (0.0%) | `insufficient_support` |
| `recovery` | `one_step_lag2_affine_one_step_map_level2` | 0/20 (0.0%) | 0/20 (0.0%) | `insufficient_support` |
| `recovery` | `resilience` | 0/20 (0.0%) | 0/20 (0.0%) | `not_testable` |
| `recovery` | `reach_3d` | 20/20 (100.0%) | 20/20 (100.0%) | `computed` |
## chart

| Metric | Level | Present | Computed | >=1 finite | Series finite (mean) | Status | Qual / failure |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `coords_3d_subject_anchored` | adjacent | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 1.000 | `exported` | `-` |
| `coords_9d_subject_anchored` | adjacent | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 1.000 | `exported` | `-` |
| `mnps_3d_dot` | adjacent | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 1.000 | `exported` | `-` |

## diffusion

| Metric | Level | Present | Computed | >=1 finite | Series finite (mean) | Status | Qual / failure |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `diffusion_a_hat` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 1.000 | `computed` | `ito_not_qualified` |
| `diffusion_d_diff` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 1.000 | `computed` | `ito_not_qualified` |
| `diffusion_D_total` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 1.000 | `computed` | `ito_not_qualified` |
| `diffusion_A_bD` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | 0/80 (0.0%) | 0.000 | `computed` | `ito_not_qualified` |
| `diffusion_R_b_over_a` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | 0/80 (0.0%) | 0.000 | `computed` | `ito_not_qualified` |
| `increment_covariance_level0` | L0 | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 0.989 | `computed` | `unconditional_increment_covariance_not_a_hat` |

## chart_drift

| Metric | Level | Present | Computed | >=1 finite | Series finite (mean) | Status | Qual / failure |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `realized_velocity_level0` | L0 | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 0.989 | `computed` | `not_assessed` |
| `chart_drift_b_hat_pooled` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 0.965 | `computed` | `ito_not_qualified` |
| `chart_drift_b_hat_crossfit` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 0.882 | `computed` | `ito_not_qualified` |
| `chart_drift_lag_diagnostics` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 0.965 | `computed` | `ito_not_qualified` |

## one_step

| Metric | Level | Present | Computed | >=1 finite | Series finite (mean) | Status | Qual / failure |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `one_step_lag1_affine_one_step_map_level2` | L2 | 78/80 (97.5%) | 46/80 (57.5%) | 46/80 (57.5%) | 0.584 | `computed` | `one_step_identified` |
| `one_step_lag2_affine_one_step_map_level2` | L2 | 80/80 (100.0%) | 0/80 (0.0%) | 0/80 (0.0%) | 0.000 | `insufficient_support` | `one_step_not_identified` |
| `one_step_lag1_conditional_affine_mean_rate_level2` | L2 | 78/80 (97.5%) | 46/80 (57.5%) | 46/80 (57.5%) | 0.584 | `computed` | `one_step_identified` |
| `one_step_lag2_conditional_affine_mean_rate_level2` | L2 | 80/80 (100.0%) | 0/80 (0.0%) | 0/80 (0.0%) | 0.000 | `insufficient_support` | `one_step_not_identified` |
| `one_step_lag1_innovation_covariance_level2` | L2 | 78/80 (97.5%) | 46/80 (57.5%) | 46/80 (57.5%) | 0.584 | `computed` | `one_step_identified` |
| `one_step_lag2_innovation_covariance_level2` | L2 | 80/80 (100.0%) | 0/80 (0.0%) | 0/80 (0.0%) | 0.000 | `insufficient_support` | `one_step_not_identified` |
| `one_step_lag1_operator_max_gain_rate_level2` | L2 | 80/80 (100.0%) | 46/80 (57.5%) | 46/80 (57.5%) | 0.990 | `computed` | `one_step_functional_of_qualified_map_not_independent_oos` |
| `one_step_lag2_operator_max_gain_rate_level2` | L2 | 80/80 (100.0%) | 0/80 (0.0%) | 0/80 (0.0%) | n/a | `not_testable` | `one_step_functional_of_qualified_map_not_independent_oos` |
| `one_step_lag1_operator_volume_gain_rate_level2` | L2 | 80/80 (100.0%) | 46/80 (57.5%) | 46/80 (57.5%) | 0.990 | `computed` | `one_step_functional_of_qualified_map_not_independent_oos` |
| `one_step_lag2_operator_volume_gain_rate_level2` | L2 | 80/80 (100.0%) | 0/80 (0.0%) | 0/80 (0.0%) | n/a | `not_testable` | `one_step_functional_of_qualified_map_not_independent_oos` |
| `one_step_lag1_operator_rotation_rate_level2` | L2 | 80/80 (100.0%) | 46/80 (57.5%) | 46/80 (57.5%) | 0.990 | `computed` | `one_step_functional_of_qualified_map_not_independent_oos` |
| `one_step_lag2_operator_rotation_rate_level2` | L2 | 80/80 (100.0%) | 0/80 (0.0%) | 0/80 (0.0%) | n/a | `not_testable` | `one_step_functional_of_qualified_map_not_independent_oos` |
| `one_step_lag1_spectral_abscissa_level3` | L3 | 78/80 (97.5%) | 46/80 (57.5%) | 46/80 (57.5%) | 0.990 | `computed` | `generator_proxy_from_qualified_one_step_not_ito` |
| `one_step_lag2_spectral_abscissa_level3` | L3 | 80/80 (100.0%) | 0/80 (0.0%) | 0/80 (0.0%) | n/a | `not_testable` | `generator_proxy_from_qualified_one_step_not_ito` |
| `one_step_lag1_numerical_abscissa_level3` | L3 | 78/80 (97.5%) | 46/80 (57.5%) | 46/80 (57.5%) | 0.990 | `computed` | `generator_proxy_from_qualified_one_step_not_ito` |
| `one_step_lag2_numerical_abscissa_level3` | L3 | 80/80 (100.0%) | 0/80 (0.0%) | 0/80 (0.0%) | n/a | `not_testable` | `generator_proxy_from_qualified_one_step_not_ito` |
| `one_step_lag1_divergence_level3` | L3 | 78/80 (97.5%) | 46/80 (57.5%) | 46/80 (57.5%) | 0.990 | `computed` | `generator_proxy_from_qualified_one_step_not_ito` |
| `one_step_lag2_divergence_level3` | L3 | 80/80 (100.0%) | 0/80 (0.0%) | 0/80 (0.0%) | n/a | `not_testable` | `generator_proxy_from_qualified_one_step_not_ito` |
| `one_step_lag1_generator_rotation_norm_level3` | L3 | 78/80 (97.5%) | 46/80 (57.5%) | 46/80 (57.5%) | 0.990 | `computed` | `generator_proxy_from_qualified_one_step_not_ito` |
| `one_step_lag2_generator_rotation_norm_level3` | L3 | 80/80 (100.0%) | 0/80 (0.0%) | 0/80 (0.0%) | n/a | `not_testable` | `generator_proxy_from_qualified_one_step_not_ito` |
| `one_step_lag1_iterated_horizon_map_level4` | L4 | 80/80 (100.0%) | 0/80 (0.0%) | 0/80 (0.0%) | 0.000 | `insufficient_support` | `horizon_propagation_not_identified` |

## amplification

| Metric | Level | Present | Computed | >=1 finite | Series finite (mean) | Status | Qual / failure |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `amplification_neighbor_gain_q90_level1` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 0.989 | `computed` | `same_pair_observed_gain_not_operator_max_gain` |
| `amplification_neighbor_gain_rate_q90_level1` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 0.989 | `computed` | `same_pair_observed_gain_rate_not_operator_max_gain` |
| `amplification_neighbor_separation_rate_level1` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 0.989 | `computed` | `same_pair_observed_separation_not_spectral_abscissa` |
| `amplification_cloud_volume_change_rate_level1` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 0.989 | `computed` | `same_pair_cloud_volume_not_operator_volume` |

## history

| Metric | Level | Present | Computed | >=1 finite | Series finite (mean) | Status | Qual / failure |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `history_predictive_gain_level1` | L1 | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 0.883 | `computed` | `history_error_reduction_not_markov_restoration` |
| `history_conditioned_operator_level2` | L2 | 80/80 (100.0%) | 30/80 (37.5%) | 30/80 (37.5%) | 0.367 | `insufficient_support` | `history_conditioned_operator_not_identified` |

## turning

| Metric | Level | Present | Computed | >=1 finite | Series finite (mean) | Status | Qual / failure |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `turning_angle_level0` | L0 | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 0.979 | `computed` | `realized_turning_not_operator_rotation` |
| `turning_rate_level0` | L0 | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 0.979 | `computed` | `realized_turning_not_operator_rotation` |

## destination

| Metric | Level | Present | Computed | >=1 finite | Series finite (mean) | Status | Qual / failure |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `destination` | adjacent | 80/80 (100.0%) | 0/80 (0.0%) | 0/80 (0.0%) | n/a | `not_testable` | `not_generator_committor` |

## resilience

| Metric | Level | Present | Computed | >=1 finite | Series finite (mean) | Status | Qual / failure |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `resilience` | L4 | 80/80 (100.0%) | 0/80 (0.0%) | 0/80 (0.0%) | n/a | `not_testable` | `not_assessed` |

## jacobian

| Metric | Level | Present | Computed | >=1 finite | Series finite (mean) | Status | Qual / failure |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `jacobian_3d_jhat` | adjacent | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 1.000 | `exported` | `-` |
| `jacobian_3d_alpha` | adjacent | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 1.000 | `computed` | `-` |
| `jacobian_3d_omega` | adjacent | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 1.000 | `computed` | `-` |
| `jacobian_3d_rel_mse_oos` | adjacent | 80/80 (100.0%) | 0/80 (0.0%) | 80/80 (100.0%) | 1.000 | `not_recorded` | `-` |
| `jacobian_9d_alpha` | adjacent | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 1.000 | `computed` | `-` |
| `jacobian_9d_subject_anchored_jhat` | adjacent | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 1.000 | `exported` | `-` |

## ftr

| Metric | Level | Present | Computed | >=1 finite | Series finite (mean) | Status | Qual / failure |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `ftr_3d_g_peak` | adjacent | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 1.000 | `computed` | `-` |
| `ftr_9d_g_peak` | adjacent | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 1.000 | `computed` | `-` |

## reachability

| Metric | Level | Present | Computed | >=1 finite | Series finite (mean) | Status | Qual / failure |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `reach_3d` | L4 | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 1.000 | `computed` | `not_assessed` |
| `reach_9d` | L4 | 80/80 (100.0%) | 73/80 (91.2%) | 73/80 (91.2%) | 1.000 | `computed` | `not_assessed` |

## transition

| Metric | Level | Present | Computed | >=1 finite | Series finite (mean) | Status | Qual / failure |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `transition_residuals_3d` | adjacent | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 1.000 | `computed` | `-` |
| `qproxy_3d` | adjacent | 80/80 (100.0%) | 80/80 (100.0%) | 80/80 (100.0%) | 1.000 | `computed` | `-` |

## How to read this

- L0 = realized increment objects. L1 = local conditional / same-pair / history-gain.
- L2 = identified one-step map and its functionals, plus history-conditioned operator.
- L3 = generator proxy from a qualified one-step map. Not Family B Jacobian α.
- L4 = iterated horizon map, FAR, and stochastic reachability. Destination is unnumbered `not_testable`.
- `A_bD` / `R_b_over_a` can be `computed` with all-NaN series when drift_source is not supplied.
- Lag-2 one-step and L4 horizon maps are not substitutes for lag-1 coverage.
