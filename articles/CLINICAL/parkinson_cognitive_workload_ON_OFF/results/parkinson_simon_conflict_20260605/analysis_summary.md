# Simon conflict Parkinson cognitive workload summary

This run analyzes `ds003509` with a mixed-contract policy: `cohort_anchored` is primary for disease-state contrasts against controls, while `subject_anchored` remains primary for the paired medication contrast.

## Standard ndt-analysis layer

### Parkinson_OFF_vs_ON (subject_anchored)

- `global_mnps_3d / m_median`: d=0.5154, p=0.007996, q=0.07196
- `adaptive_collapse / q_ratio_h4`: d=-0.3694, p=0.06097, q=0.08396
- `adaptive_collapse / a_operator_norm`: d=0.3345, p=0.07446, q=0.08396
- `adaptive_collapse / capture_gate`: d=0.3535, p=0.08396, q=0.08396
- `regional_mnps_jacobian_3d / temporal / mdr_mean`: d=0.4105, p=0.001999, q=0.1139
- `regional_mnps_jacobian_3d / temporal / mdr_median`: d=0.5505, p=0.003498, q=0.1139

### Control_vs_Parkinson_OFF (cohort_anchored)

- `regional_9d / parietal_occipital / d_s_mean`: d=1.166, p=0.0004998, q=0.01349
- `regional_9d / parietal_occipital / d_n_std`: d=-1.155, p=0.0004998, q=0.01349
- `regional_9d / parietal_occipital / d_s_median`: d=1.13, p=0.0004998, q=0.01349
- `regional_9d / central / d_n_std`: d=-1.129, p=0.0004998, q=0.01349
- `regional_9d / temporal / e_m_mean`: d=-0.8667, p=0.0009995, q=0.01963
- `regional_9d / temporal / d_s_mean`: d=0.8714, p=0.001499, q=0.01963

### Control_vs_Parkinson_ON (cohort_anchored)

- `regional_9d / frontal / e_m_mean`: d=-0.9908, p=0.0004998, q=0.01349
- `regional_9d / parietal_occipital / e_m_mean`: d=-0.9908, p=0.0004998, q=0.01349
- `regional_9d / temporal / e_m_mean`: d=-0.9908, p=0.0004998, q=0.01349
- `global_mnps_9d / e_m_median`: d=-0.9848, p=0.0004998, q=0.01349
- `regional_9d / parietal_occipital / d_s_mean`: d=0.9818, p=0.0004998, q=0.01349
- `global_mnps_9d / e_m_mean`: d=-0.9908, p=0.0009995, q=0.01349

## Event-locked trajectory layer

### Parkinson_OFF_vs_ON (subject_anchored)

- `regional_event_locked_trajectory_3d` / `feedback_reward_all` / `temporal` / `peak_displacement`: d=0.5621, p=0.001555, q=0.5198
- `regional_event_locked_trajectory_3d` / `test_stimulus_easy` / `temporal` / `curvature_median`: d=-0.6738, p=0.002043, q=0.5198
- `regional_event_locked_trajectory_3d` / `test_response_correct` / `temporal` / `hysteresis_area_de`: d=0.656, p=0.002902, q=0.5198
- `regional_event_locked_trajectory_3d` / `feedback_reward_all` / `central` / `curvature_median`: d=-0.4867, p=0.003161, q=0.5198
- `regional_event_locked_trajectory_3d` / `training_all` / `parietal_occipital` / `recovery_residual`: d=-0.4468, p=0.004061, q=0.5198
- `regional_event_locked_trajectory_3d` / `training_no_response` / `temporal` / `peak_displacement`: d=0.477, p=0.004232, q=0.5198

### Control_vs_Parkinson_OFF (cohort_anchored)

- `regional_event_locked_trajectory_9d` / `training_feedback_reward` / `central` / `tortuosity`: d=0.9212, p=0.001079, q=0.9575
- `regional_event_locked_trajectory_9d` / `training_response_correct` / `central` / `tortuosity`: d=0.7557, p=0.003444, q=0.9575
- `regional_event_locked_trajectory_9d` / `test_no_response` / `temporal` / `tortuosity`: d=0.9438, p=0.003506, q=0.9575
- `regional_event_locked_trajectory_9d` / `test_all` / `frontal` / `recovery_residual`: d=0.8446, p=0.004029, q=0.9575
- `regional_event_locked_trajectory_9d` / `test_stimulus_direct_conflict` / `central` / `tortuosity`: d=0.7534, p=0.005477, q=0.9575
- `regional_event_locked_trajectory_9d` / `test_response_all` / `frontal` / `hysteresis_area_de`: d=0.7903, p=0.007748, q=0.9575

### Control_vs_Parkinson_ON (cohort_anchored)

- `regional_event_locked_trajectory_9d` / `test_response_all` / `temporal` / `hysteresis_area_de`: d=1.002, p=0.0004677, q=0.4731
- `regional_event_locked_trajectory_9d` / `test_all` / `temporal` / `hysteresis_area_de`: d=0.9605, p=0.001079, q=0.4731
- `regional_event_locked_trajectory_9d` / `test_stimulus_all` / `temporal` / `hysteresis_area_de`: d=0.7976, p=0.004243, q=0.4731
- `regional_event_locked_trajectory_9d` / `test_stimulus_all` / `frontal` / `hysteresis_area_de`: d=0.8375, p=0.005477, q=0.4731
- `regional_event_locked_trajectory_9d` / `feedback_reward_all` / `temporal` / `hysteresis_area_de`: d=0.5466, p=0.009396, q=0.4731
- `regional_event_locked_trajectory_9d` / `training_stimulus_incongruent` / `temporal` / `hysteresis_area_de`: d=0.3969, p=0.009396, q=0.4731

## Caveats

- Wrapper metrics use task-specific `event_windows/*` segmentation and remain article-local summaries on top of the repository standard exports.
- Control subjects do not have medication pairing, so disease-state and pharmacology questions are answered with different optimal coordinate contracts.
