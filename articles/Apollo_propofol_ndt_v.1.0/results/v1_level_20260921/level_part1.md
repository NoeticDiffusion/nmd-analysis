# Apollo Jacobian-α + L1/L2/L3 stage contrasts (level_jl123_within_subject_20260921)

Paired later-minus-earlier on subject/phase medians, complete-case only. BH-FDR is across finite Wilcoxon tests in this panel. Status: `exploratory_discovery_20260921_g4_not_locked`. Chart-Jacobian α is not one-step L3. Not consciousness. Not confirmatory amplitude.

Bootstrap 10000, seed 20260920. L2/L3 n is smaller because one-step identification is partial.

## Missingness (recordings with a finite included median)

| Level | Metric | n finite / 80 |
| --- | --- | ---: |
| jacobian_alpha | `jacobian_alpha` | 80/80 |
| L1 | `diffusion_a_hat_frob` | 80/80 |
| L1 | `diffusion_total` | 80/80 |
| L1 | `diffusion_effective_dimension` | 80/80 |
| L1 | `diffusion_concentration` | 80/80 |
| L1 | `chart_drift_b_hat_norm` | 80/80 |
| L1 | `neighbor_gain_q90` | 80/80 |
| L1 | `neighbor_gain_rate_q90` | 80/80 |
| L1 | `neighbor_separation_rate` | 80/80 |
| L1 | `cloud_volume_change_rate` | 80/80 |
| L1 | `history_predictive_gain` | 80/80 |
| L2 | `one_step_phi_frob` | 46/80 |
| L2 | `one_step_affine_mean_rate_norm` | 46/80 |
| L2 | `one_step_innovation_trace` | 46/80 |
| L2 | `operator_max_gain_rate` | 46/80 |
| L2 | `operator_volume_gain_rate` | 46/80 |
| L2 | `operator_rotation_rate` | 46/80 |
| L2 | `history_conditioned_phi_frob` | 30/80 |
| L3 | `one_step_spectral_abscissa` | 46/80 |
| L3 | `one_step_numerical_abscissa` | 46/80 |
| L3 | `one_step_divergence` | 46/80 |
| L3 | `one_step_generator_rotation_norm` | 46/80 |

## Primary contrast by jacobian_alpha: first sedation − baseline

| Metric | n | later med | base med | Δ med | d_z | Wilcoxon p | BH q | BH q within level |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `jacobian_alpha` | 20 | 0.02198 | 0.02597 | -0.005944 | -0.313 | 0.165 | 0.7024 | 0.4323 |

## Primary contrast by L1: first sedation − baseline

| Metric | n | later med | base med | Δ med | d_z | Wilcoxon p | BH q | BH q within level |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `diffusion_a_hat_frob` | 20 | 0.1476 | 0.1652 | -0.03467 | -0.659 | 0.01069 | 0.2822 | 0.1283 |
| `diffusion_total` | 20 | 0.2181 | 0.2412 | -0.03906 | -0.702 | 0.007296 | 0.2408 | 0.1094 |
| `diffusion_effective_dimension` | 20 | 2.163 | 2.062 | 0.036 | 0.113 | 0.7012 | 0.9846 | 0.8765 |
| `diffusion_concentration` | 20 | 0.6008 | 0.6157 | -0.006291 | -0.0847 | 0.7012 | 0.9846 | 0.8765 |
| `chart_drift_b_hat_norm` | 20 | 0.07679 | 0.08956 | -0.01748 | -0.858 | 0.002325 | 0.2408 | 0.1094 |
| `neighbor_gain_q90` | 20 | 3.194 | 3.188 | -0.05416 | -0.205 | 0.4091 | 0.9643 | 0.7219 |
| `neighbor_gain_rate_q90` | 20 | 0.2903 | 0.2898 | -0.00412 | -0.221 | 0.3884 | 0.9643 | 0.7219 |
| `neighbor_separation_rate` | 20 | 0.1358 | 0.1327 | 0.0002768 | 0.0791 | 0.5958 | 0.9846 | 0.8765 |
| `cloud_volume_change_rate` | 20 | 0.3412 | 0.3466 | -0.01103 | -0.0424 | 0.7285 | 1 | 0.892 |
| `history_predictive_gain` | 20 | -0.07951 | -0.07844 | 0.01628 | -0.103 | 0.7841 | 1 | 0.9225 |

## Primary contrast by L2: first sedation − baseline

| Metric | n | later med | base med | Δ med | d_z | Wilcoxon p | BH q | BH q within level |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `one_step_phi_frob` | 4 | 1.033 | 1.009 | 0.03728 | 0.321 | 0.625 | 0.9846 | 1 |
| `one_step_affine_mean_rate_norm` | 4 | 0.0964 | 0.1133 | -0.016 | -1.94 | 0.125 | 0.6875 | 0.8906 |
| `one_step_innovation_trace` | 4 | 0.1939 | 0.232 | -0.04075 | -0.842 | 0.125 | 0.6875 | 0.8906 |
| `operator_max_gain_rate` | 4 | -0.08343 | -0.07324 | -0.003085 | 0.0381 | 1 | 1 | 1 |
| `operator_volume_gain_rate` | 4 | -0.4042 | -0.465 | 0.03872 | 0.37 | 0.625 | 0.9846 | 1 |
| `operator_rotation_rate` | 4 | 0.06692 | 0.07567 | 0.0009764 | 0.124 | 0.875 | 1 | 1 |
| `history_conditioned_phi_frob` | 1 | 1.419 | 1.557 | 0.1888 | nan | 1 | 1 | 1 |

## Primary contrast by L3: first sedation − baseline

| Metric | n | later med | base med | Δ med | d_z | Wilcoxon p | BH q | BH q within level |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `one_step_spectral_abscissa` | 4 | -0.09703 | -0.1034 | 0.03143 | 0.44 | 0.625 | 0.9846 | 1 |
| `one_step_numerical_abscissa` | 4 | -0.08309 | -0.07286 | -0.00341 | 0.00924 | 1 | 1 | 1 |
| `one_step_divergence` | 4 | -0.4042 | -0.465 | 0.03872 | 0.37 | 0.625 | 0.9846 | 1 |
| `one_step_generator_rotation_norm` | 4 | 0.09587 | 0.1091 | 0.0008098 | 0.105 | 0.875 | 1 | 1 |

## FDR-significant rows (n≥10, |d_z| order)

No Wilcoxon BH q < 0.05 among complete-case tests with n≥10.

## Largest |d_z| with n≥10

| Level | Contrast | Metric | n | d_z | Wilcoxon p | BH q | BH q within level |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| L1 | `first_sedation_minus_baseline` | `chart_drift_b_hat_norm` | 20 | -0.858 | 0.002325 | 0.2408 | 0.1094 |
| L1 | `first_sedation_minus_baseline` | `diffusion_total` | 20 | -0.702 | 0.007296 | 0.2408 | 0.1094 |
| L1 | `first_sedation_minus_baseline` | `diffusion_a_hat_frob` | 20 | -0.659 | 0.01069 | 0.2822 | 0.1283 |
| L1 | `recovery_minus_later_sedation` | `cloud_volume_change_rate` | 20 | 0.648 | 0.007296 | 0.2408 | 0.1094 |
| L1 | `recovery_minus_first_sedation` | `chart_drift_b_hat_norm` | 20 | 0.593 | 0.005581 | 0.2408 | 0.1094 |
| L1 | `recovery_minus_later_sedation` | `neighbor_separation_rate` | 20 | 0.581 | 0.01923 | 0.3174 | 0.1443 |
| L1 | `recovery_minus_later_sedation` | `neighbor_gain_rate_q90` | 20 | 0.545 | 0.01531 | 0.2887 | 0.1312 |
| L1 | `recovery_minus_later_sedation` | `neighbor_gain_q90` | 20 | 0.507 | 0.01531 | 0.2887 | 0.1312 |
| L1 | `recovery_minus_first_sedation` | `diffusion_total` | 20 | 0.474 | 0.02664 | 0.3907 | 0.1776 |
| L1 | `later_sedation_minus_baseline` | `neighbor_separation_rate` | 20 | -0.452 | 0.1327 | 0.6994 | 0.4684 |
| L1 | `recovery_minus_first_sedation` | `diffusion_a_hat_frob` | 20 | 0.445 | 0.03999 | 0.5279 | 0.2399 |
| L1 | `recovery_minus_first_sedation` | `neighbor_gain_rate_q90` | 20 | 0.431 | 0.1536 | 0.6994 | 0.4852 |

One-step L2/L3 pairs exist only when the lag-1 map is identified in both phases.
Do not read protocol phase 3 as unresponsiveness. Export is `subject_anchored`.
