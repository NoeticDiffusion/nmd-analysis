# Outcome contrast summary

## Inputs

- patient_timebin_rows: 17540
- run_level_rows: 150418
- patient_timebin_outcome_counts: {'CPC5': 9177, 'CPC1': 8363}
- run_level_outcome_counts: {'CPC5': 75782, 'CPC1': 74636}

## Status

- patient_timebin_contrast_status_counts: {'ok': 246, 'limited_n': 82}
- run_level_contrast_status_counts: {'ok': 328}

## Top Patient/Time-Bin Contrasts

- `reachability_cones` / `tube_rotation_mean` / `all_time_bins`: delta_median=-0.06049, mannwhitney_p=3.469e-07
- `reachability_cones` / `tube_rotation_median` / `all_time_bins`: delta_median=-0.07157, mannwhitney_p=6.471e-07
- `reachability_cones` / `cone_rotation_median` / `all_time_bins`: delta_median=-0.07157, mannwhitney_p=6.471e-07
- `reachability_cones` / `tube_a_operator_norm_median` / `0_12h`: delta_median=-0.08571, mannwhitney_p=1.221e-05
- `reachability_cones` / `persistence_hysteresis_log_det_median` / `0_12h`: delta_median=-0.2534, mannwhitney_p=2.032e-05
- `reachability_cones` / `persistence_hysteresis_log_eig_var_median` / `0_12h`: delta_median=-0.2895, mannwhitney_p=2.835e-05
- `reachability_cones` / `cone_dir_entropy_norm_h1_median` / `all_time_bins`: delta_median=0.07444, mannwhitney_p=2.904e-05
- `reachability_cones` / `cone_dir_entropy_h1_median` / `all_time_bins`: delta_median=0.08178, mannwhitney_p=2.904e-05
- `reachability_cones` / `tube_a_operator_norm_mean` / `0_12h`: delta_median=-0.1461, mannwhitney_p=3.164e-05
- `reachability_cones` / `persistence_log_eig_var_median` / `0_12h`: delta_median=1.186, mannwhitney_p=3.282e-05

## Top Run-Level Contrasts

- `reachability_cones` / `tube_a_operator_norm_median` / `all_time_bins`: delta_median=-0.07675, mannwhitney_p=4.005e-36
- `reachability_cones` / `persistence_kappa_median` / `all_time_bins`: delta_median=0.2052, mannwhitney_p=8.718e-36
- `reachability_cones` / `tube_a_operator_norm_median` / `0_12h`: delta_median=-0.07739, mannwhitney_p=1.438e-35
- `reachability_cones` / `persistence_hysteresis_kappa_median` / `all_time_bins`: delta_median=-3.925, mannwhitney_p=3.007e-35
- `reachability_cones` / `persistence_kappa_median` / `0_12h`: delta_median=0.2032, mannwhitney_p=8.514e-35
- `reachability_cones` / `tube_a_operator_norm_mean` / `all_time_bins`: delta_median=-0.09826, mannwhitney_p=1.657e-34
- `reachability_cones` / `persistence_log_eig_var_median` / `all_time_bins`: delta_median=1.397, mannwhitney_p=2.342e-34
- `reachability_cones` / `persistence_hysteresis_kappa_median` / `0_12h`: delta_median=-3.925, mannwhitney_p=5.217e-34
- `reachability_cones` / `persistence_hysteresis_log_eig_var_median` / `all_time_bins`: delta_median=-0.2475, mannwhitney_p=5.941e-34
- `reachability_cones` / `cone_dir_entropy_norm_h4_median` / `all_time_bins`: delta_median=0.08144, mannwhitney_p=7.91e-34

