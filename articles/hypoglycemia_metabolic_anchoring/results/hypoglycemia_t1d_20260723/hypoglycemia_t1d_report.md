# Hypoglycemia T1D: paired NDT analysis

## Design and evidence status

- 34 complete subject pairs; contrast direction is hypoglycemia minus euglycemia.
- This is an internal empirical analysis of discrete five-minute EEG excerpts.
- It contains no continuous clamp trajectory, recovery segment, participant-level glucose value, or awareness subgroup metadata.
- Cohort-anchored coordinates use a pooled eu+hy feature anchor; they are not euglycemia-anchored coordinates.
- Reachability outputs are exploratory and validity-limited under the frozen split-half criteria; they are not confirmatory endpoints.

## NDT contrast results

- Engine contrast rows: 157; the table below is the prespecified coordinate and audit subset.
- QC summary rows: 22.

| analysis | metric | n_pairs | effect (HYPO-EU) | p | q |
|---|---|---:|---:|---:|---:|
| global_mnps_3d | d_median | 34 | 0.02782 | 0.8592 | 0.964 |
| global_mnps_3d | e_median | 34 | -0.244 | 0.03319 | 0.07469 |
| global_mnps_3d | m_median | 34 | -0.7429 | 0.0002 | 0.0008998 |
| global_mnps_9d | d_l_median | 34 | -0.4404 | 0.03099 | 0.05977 |
| global_mnps_9d | d_n_median | 34 | 1.014 | 0.0007998 | 0.003085 |
| global_mnps_9d | d_s_median | 34 | -0.311 | 0.2022 | 0.2274 |
| global_mnps_9d | e_e_median | 34 | -0.7084 | 0.0176 | 0.03959 |
| global_mnps_9d | e_m_median | 34 | 1.024 | 0.0016 | 0.004799 |
| global_mnps_9d | e_s_median | 34 | 0.3226 | 0.1194 | 0.1612 |
| global_mnps_9d | m_a_median | 34 | -1.096 | 0.0002 | 0.0018 |
| global_mnps_9d | m_e_median | 34 | -0.6848 | 0.0003999 | 0.0018 |
| global_mnps_9d | m_o_median | 34 | -0.3578 | 0.09238 | 0.13298 |
| global_mnps_jacobian_3d | frobenius_norm_median | 34 | -0.009684 | 0.2452 | 0.6654 |
| global_mnps_jacobian_3d | rotation_norm_median | 34 | -0.005262 | 0.4277 | 0.6947 |
| global_mnps_jacobian_3d | trace_median | 34 | -0.009713 | 0.03779 | 0.6654 |
| global_mnps_jacobian_9d | a_operator_norm_median | 33 | -0.1283 | 0.004199 | 0.03419 |
| global_mnps_jacobian_9d | frobenius_norm_median | 33 | -0.1297 | 0.005399 | 0.03419 |
| global_mnps_jacobian_9d | rotation_norm_median | 33 | -0.09025 | 0.005199 | 0.03419 |
| reachability_cones | tube_d_eff_median | 33 | 0.2512 | 0.0124 | 0.1343 |
| reachability_cones | tube_dir_entropy_median | 33 | 0.08805 | 0.02979 | 0.1534 |
| reachability_cones | tube_kappa_median | 33 | -2872 | 0.06019 | 0.1698 |
| reachability_cones | tube_log_det_median | 33 | 0.395 | 0.2454 | 0.5367 |
| reachability_cones | tube_rotation_median | 33 | 0.004369 | 0.8324 | 0.9171 |

## Classical EEG sanity check

| feature | n_pairs | effect (HYPO-EU) | Cohen dz | p | q |
|---|---:|---:|---:|---:|---:|
| eeg_theta | 34 | 0.1297 | 0.709 | 2.205e-06 | 1.323e-05 |
| eeg_delta | 34 | 0.1025 | 0.752 | 2.866e-05 | 8.597e-05 |
| eeg_alpha | 34 | 0.1693 | 0.3855 | 0.004326 | 0.008652 |
| eeg_sample_entropy | 34 | -0.028 | -0.4393 | 0.03582 | 0.04298 |
| eeg_permutation_entropy | 34 | -0.028 | -0.4393 | 0.03582 | 0.04298 |
| eeg_hjorth_complexity | 34 | 0.08457 | 0.2776 | 0.1682 | 0.1682 |

## Interpretation boundary

Any paired NDT differences are condition-associated changes in this batch, not evidence that glucose directly measures consciousness or that a metabolic gate is causally identified.
