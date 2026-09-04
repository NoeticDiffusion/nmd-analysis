# Reinforcement learning Parkinson cognitive workload summary

This run analyzes `ds003506` with a mixed-contract policy: `cohort_anchored` is primary for disease-state contrasts against controls, while `subject_anchored` remains primary for the paired medication contrast.

## Standard ndt-analysis layer

### Parkinson_OFF_vs_ON (subject_anchored)

- `regional_3d / frontal / e_mean`: d=-0.5215, p=0.008996, q=0.2069
- `regional_3d / frontal / e_median`: d=-0.5108, p=0.01149, q=0.2069
- `eeg_classical_comparators / global / eeg_classical_peak_spectral_edge_95_delta_mean_median`: d=0.4574, p=0.02399, q=0.3253
- `eeg_classical_comparators / global / eeg_classical_relative_gamma_mad_sigma`: d=-0.4393, p=0.02399, q=0.3253
- `eeg_classical_comparators / global / eeg_classical_peak_spectral_edge_95_median`: d=-0.4384, p=0.02649, q=0.3253
- `eeg_classical_comparators / global / eeg_classical_relative_gamma_iqr`: d=-0.4275, p=0.02849, q=0.3253

### Control_vs_Parkinson_OFF (cohort_anchored)

- `eeg_classical_comparators / global / eeg_classical_relative_alpha_median`: d=1.113, p=0.0004998, q=0.02399
- `eeg_classical_comparators / global / eeg_classical_relative_alpha_iqr`: d=0.9559, p=0.0004998, q=0.02399
- `eeg_classical_comparators / global / eeg_classical_relative_alpha_mean`: d=1.113, p=0.0009995, q=0.02399
- `eeg_classical_comparators / global / eeg_classical_relative_alpha_mad_sigma`: d=0.9384, p=0.0009995, q=0.02399
- `global_mnps_jacobian_9d / mdr_mean`: d=0.8348, p=0.003498, q=0.03323
- `global_mnps_jacobian_9d / rotational_power_mean`: d=0.6577, p=0.003498, q=0.03323

### Control_vs_Parkinson_ON (cohort_anchored)

- `global_mnps_jacobian_9d / aci_mean`: d=0.8349, p=0.002499, q=0.04748
- `global_mnps_jacobian_9d / aci_median`: d=0.7441, p=0.007496, q=0.07121
- `global_mnps_9d_block_jacobian / central / block_frobenius_mean`: d=-0.7136, p=0.002499, q=0.08996
- `regional_9d / frontal / d_s_median`: d=0.8141, p=0.001499, q=0.1619
- `adaptive_collapse / a_operator_norm`: d=0.5098, p=0.06197, q=0.1627
- `adaptive_collapse / capture_gate`: d=0.4552, p=0.1084, q=0.1627

## Event-locked trajectory layer

### Parkinson_OFF_vs_ON (subject_anchored)

- `regional_event_locked_trajectory_3d` / `match_feedback_error` / `parietal_occipital` / `hysteresis_area_md`: d=-0.9402, p=0.0008545, q=0.7795
- `regional_event_locked_trajectory_3d` / `error_all` / `parietal_occipital` / `hysteresis_area_md`: d=-0.9237, p=0.001526, q=0.7795
- `regional_event_locked_trajectory_3d` / `match_feedback_reward` / `temporal` / `tortuosity`: d=-0.7033, p=0.001555, q=0.7795
- `global_event_locked_trajectory_9d` / `error_all` / `global` / `speed_median`: d=-0.7865, p=0.01245, q=0.9382
- `global_event_locked_trajectory_9d` / `match_feedback_reward` / `global` / `hysteresis_area_me`: d=-0.3949, p=0.0127, q=0.9382
- `global_event_locked_trajectory_9d` / `match_feedback_error` / `global` / `speed_median`: d=-0.7265, p=0.01508, q=0.9382

### Control_vs_Parkinson_OFF (cohort_anchored)

- `global_event_locked_trajectory_9d` / `match_feedback_punishment` / `global` / `hysteresis_area_de`: d=0.6042, p=0.008957, q=0.3993
- `global_event_locked_trajectory_9d` / `match_feedback_error` / `global` / `peak_displacement`: d=0.4034, p=0.01148, q=0.3993
- `global_event_locked_trajectory_9d` / `match_response_all` / `global` / `hysteresis_area_de`: d=0.5772, p=0.01565, q=0.3993
- `global_event_locked_trajectory_9d` / `error_all` / `global` / `peak_displacement`: d=0.3814, p=0.01731, q=0.3993
- `global_event_locked_trajectory_9d` / `punishment_all` / `global` / `recovery_residual`: d=0.5812, p=0.01789, q=0.3993
- `global_event_locked_trajectory_9d` / `choose_feedback_punishment` / `global` / `path_length`: d=0.617, p=0.0187, q=0.3993

### Control_vs_Parkinson_ON (cohort_anchored)

- `global_event_locked_trajectory_3d` / `choose_feedback_punishment` / `global` / `noetic_action_jerk`: d=0.49, p=0.01304, q=0.8611
- `global_event_locked_trajectory_3d` / `match_feedback_punishment` / `global` / `recovery_residual`: d=0.5555, p=0.02132, q=0.8611
- `global_event_locked_trajectory_3d` / `choose_feedback_punishment` / `global` / `path_length`: d=0.4135, p=0.02991, q=0.8611
- `global_event_locked_trajectory_3d` / `match_feedback_punishment` / `global` / `noetic_action_jerk`: d=0.2242, p=0.02991, q=0.8611
- `global_event_locked_trajectory_3d` / `choose_feedback_punishment` / `global` / `noetic_action_kinetic`: d=0.5563, p=0.04133, q=0.8611
- `global_event_locked_trajectory_3d` / `match_feedback_punishment` / `global` / `path_length`: d=0.3514, p=0.04471, q=0.8611

## Caveats

- Wrapper metrics use task-specific `event_windows/*` segmentation and remain article-local summaries on top of the repository standard exports.
- Control subjects do not have medication pairing, so disease-state and pharmacology questions are answered with different optimal coordinate contracts.
