# Apollo occupancy robustness (apollo_occupancy_robustness_20260922_v1)

Computational robustness branch for the frozen exploratory occupancy scalar. All variants reuse the original full-eight-feature reference eligibility mask and participant-level pairing. This is not a confirmatory lock.

Rows with successful participant-phase values: 880/880.
Feature contribution rows: 640; support-audit rows: 80.
Reference reproduction: PASS (80/80 cells; max absolute difference 3.55e-15; tolerance 1e-10).

## Paired contrasts

| Variant | Phase | n | median Δ | d_z | + | − | sign p | Wilcoxon p |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `full_mad` | first_protocol_sedation | 20 | 1.704 | 1.15 | 18 | 2 | 0.0004025 | 1.907e-05 |
| `full_mad` | later_protocol_sedation | 20 | 5.923 | 1.12 | 20 | 0 | 1.907e-06 | 1.907e-06 |
| `full_mad` | recovery | 20 | 1.341 | 0.445 | 19 | 1 | 4.005e-05 | 9.537e-06 |
| `loo_eeg_alpha` | first_protocol_sedation | 20 | 1.722 | 1.18 | 18 | 2 | 0.0004025 | 1.335e-05 |
| `loo_eeg_alpha` | later_protocol_sedation | 20 | 6.085 | 1.13 | 20 | 0 | 1.907e-06 | 1.907e-06 |
| `loo_eeg_alpha` | recovery | 20 | 1.166 | 0.549 | 19 | 1 | 4.005e-05 | 9.537e-06 |
| `loo_eeg_alpha_theta` | first_protocol_sedation | 20 | 1.6 | 1.05 | 16 | 4 | 0.01182 | 0.0001678 |
| `loo_eeg_alpha_theta` | later_protocol_sedation | 20 | 6.145 | 1.13 | 20 | 0 | 1.907e-06 | 1.907e-06 |
| `loo_eeg_alpha_theta` | recovery | 20 | 1.105 | 0.543 | 19 | 1 | 4.005e-05 | 5.722e-06 |
| `loo_eeg_beta` | first_protocol_sedation | 20 | 1.65 | 1.23 | 18 | 2 | 0.0004025 | 1.335e-05 |
| `loo_eeg_beta` | later_protocol_sedation | 20 | 5.385 | 1.09 | 20 | 0 | 1.907e-06 | 1.907e-06 |
| `loo_eeg_beta` | recovery | 20 | 1.247 | 0.429 | 19 | 1 | 4.005e-05 | 9.537e-06 |
| `loo_eeg_beta_alpha` | first_protocol_sedation | 20 | 1.387 | 1.13 | 18 | 2 | 0.0004025 | 1.907e-05 |
| `loo_eeg_beta_alpha` | later_protocol_sedation | 20 | 3.475 | 0.914 | 20 | 0 | 1.907e-06 | 1.907e-06 |
| `loo_eeg_beta_alpha` | recovery | 20 | 1.236 | 0.439 | 19 | 1 | 4.005e-05 | 1.335e-05 |
| `loo_eeg_delta` | first_protocol_sedation | 20 | 1.757 | 1.16 | 18 | 2 | 0.0004025 | 9.537e-06 |
| `loo_eeg_delta` | later_protocol_sedation | 20 | 5.604 | 1.1 | 20 | 0 | 1.907e-06 | 1.907e-06 |
| `loo_eeg_delta` | recovery | 20 | 1.192 | 0.44 | 19 | 1 | 4.005e-05 | 3.815e-06 |
| `loo_eeg_gamma` | first_protocol_sedation | 20 | 1.295 | 1.11 | 18 | 2 | 0.0004025 | 1.335e-05 |
| `loo_eeg_gamma` | later_protocol_sedation | 20 | 5.182 | 1.09 | 20 | 0 | 1.907e-06 | 1.907e-06 |
| `loo_eeg_gamma` | recovery | 20 | 1.086 | 0.412 | 18 | 2 | 0.0004025 | 3.624e-05 |
| `loo_eeg_sample_entropy` | first_protocol_sedation | 20 | 1.678 | 1.11 | 18 | 2 | 0.0004025 | 3.624e-05 |
| `loo_eeg_sample_entropy` | later_protocol_sedation | 20 | 6.074 | 1.11 | 20 | 0 | 1.907e-06 | 1.907e-06 |
| `loo_eeg_sample_entropy` | recovery | 20 | 1.038 | 0.423 | 18 | 2 | 0.0004025 | 4.768e-05 |
| `loo_eeg_theta` | first_protocol_sedation | 20 | 1.742 | 1.17 | 18 | 2 | 0.0004025 | 1.907e-05 |
| `loo_eeg_theta` | later_protocol_sedation | 20 | 5.504 | 1.12 | 20 | 0 | 1.907e-06 | 1.907e-06 |
| `loo_eeg_theta` | recovery | 20 | 1.186 | 0.432 | 19 | 1 | 4.005e-05 | 5.722e-06 |
| `scale_iqr` | first_protocol_sedation | 20 | 1.722 | 1.17 | 18 | 2 | 0.0004025 | 1.335e-05 |
| `scale_iqr` | later_protocol_sedation | 20 | 5.922 | 1.13 | 20 | 0 | 1.907e-06 | 1.907e-06 |
| `scale_iqr` | recovery | 20 | 1.298 | 0.451 | 19 | 1 | 4.005e-05 | 5.722e-06 |
| `scale_sd` | first_protocol_sedation | 20 | 1.427 | 1.17 | 18 | 2 | 0.0004025 | 1.907e-05 |
| `scale_sd` | later_protocol_sedation | 20 | 4.833 | 1.21 | 20 | 0 | 1.907e-06 | 1.907e-06 |
| `scale_sd` | recovery | 20 | 1.149 | 0.706 | 19 | 1 | 4.005e-05 | 9.537e-06 |

## Interpretation boundary

The branch quantifies feature and scaling dependence of the frozen scalar. It does not establish biological robustness, LOR specificity, consciousness, NDT-C3, or a confirmatory effect. Invalid variants and unsupported rows remain explicit in the CSV outputs.
