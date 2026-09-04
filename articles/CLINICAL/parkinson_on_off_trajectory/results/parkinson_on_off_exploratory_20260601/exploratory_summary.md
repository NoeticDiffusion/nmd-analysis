# Exploratory Parkinson ON/OFF summary

This run used `subject_anchored` coordinates throughout because the ds003490 MNDM bundle does not expose cohort-anchored coordinate layers.

## Standard ndt-analysis layer

### Parkinson_OFF_vs_ON

- `regional_3d / parietal_occipital / d_median`: d=0.7526, p=0.001499, q=0.05397
- `global_mnps_jacobian_9d / mdr_median`: d=0.5919, p=0.006497, q=0.1234
- `global_mnps_jacobian_9d / mdr_mean`: d=0.4527, p=0.02249, q=0.2136
- `regional_mnps_jacobian_9d / block_anisotropy_mean`: d=0.4473, p=0.02699, q=0.2429
- `global_mnps_jacobian_9d_block_jacobian / block_anisotropy_mean`: d=0.4473, p=0.02749, q=0.2474
- `tier2_jacobian / signed_divergence_balance_n`: d=0.4415, p=0.02499, q=0.2859

### Control_vs_Parkinson_OFF

- `regional_9d / central / m_o_std`: d=-1.163, p=0.0004998, q=0.05397
- `regional_9d / parietal_occipital / d_n_mean`: d=-1.019, p=0.0009995, q=0.05397
- `regional_9d / central / m_o_mean`: d=-0.911, p=0.001999, q=0.06747
- `regional_9d / temporal / m_o_mean`: d=-0.8504, p=0.002499, q=0.06747
- `regional_3d / parietal_occipital / d_median`: d=-0.9545, p=0.001999, q=0.07196
- `regional_3d / frontal / m_std`: d=-0.8334, p=0.004498, q=0.08096

### Control_vs_Parkinson_ON

- `global_mnps_jacobian_9d / mdr_mean`: d=1.258, p=0.0004998, q=0.004748
- `global_mnps_jacobian_9d / mdr_median`: d=1.162, p=0.0004998, q=0.004748
- `regional_3d / temporal / m_mean`: d=-0.9337, p=0.0009995, q=0.03598
- `regional_reachability_cones_3d / central / cone_q_ratio_h3_median`: d=0.9587, p=0.0004998, q=0.07696
- `regional_reachability_cones_3d / central / tube_q_ratio_h4_mean`: d=1.044, p=0.0009995, q=0.07696
- `regional_reachability_cones_3d / central / q_ratio_h3_median`: d=0.9587, p=0.0009995, q=0.07696

## Event-locked trajectory layer

- `regional_event_locked_trajectory_9d` / `eyes_open` / `central` / `noetic_action_jerk`: d=-0.6446, p=0.0009119, q=0.166
- `regional_event_locked_trajectory_9d` / `target_tone` / `temporal` / `irreversibility`: d=1.214, p=0.0009766, q=0.166
- `regional_event_locked_trajectory_9d` / `eyes_open` / `central` / `path_length`: d=-0.7143, p=0.002785, q=0.249
- `regional_event_locked_trajectory_9d` / `target_tone` / `temporal` / `entropy_production`: d=1.165, p=0.00293, q=0.249
- `global_event_locked_trajectory_9d` / `eyes_closed` / `global` / `entropy_rate`: d=0.6674, p=0.003781, q=0.3214
- `global_event_locked_trajectory_9d` / `eyes_closed` / `global` / `self_loop_rate`: d=-0.5617, p=0.01247, q=0.4496
- `global_event_locked_trajectory_9d` / `eyes_closed` / `global` / `transition_sparsity`: d=-0.5185, p=0.01587, q=0.4496
- `regional_event_locked_trajectory_9d` / `target_tone` / `parietal_occipital` / `hysteresis_area_mean`: d=-0.4756, p=0.007371, q=0.5012

## Trajectory ESB

### Parkinson_OFF_vs_ON

- `novel_tone` / `temporal` / `z_tortuosity`: d=0.5492, p=0.02365, q=0.8056
- `target_tone` / `temporal` / `z_tortuosity`: d=-0.4039, p=0.03934, q=0.8056
- `standard_tone` / `temporal` / `trajectory_esb3`: d=-0.3555, p=0.06465, q=0.8056
- `novel_tone` / `temporal` / `z_recovery`: d=-0.3406, p=0.09032, q=0.8056

### Control_vs_Parkinson_OFF

- `novel_tone` / `global` / `z_tortuosity`: d=0.3896, p=0.04781, q=0.5471
- `standard_tone` / `global` / `trajectory_esb2`: d=-0.2912, p=0.1073, q=0.5471
- `target_tone` / `global` / `z_hysteresis`: d=0.2591, p=0.1116, q=0.5471
- `novel_tone` / `global` / `z_hysteresis`: d=0.3791, p=0.1806, q=0.5471

### Control_vs_Parkinson_ON

- `target_tone` / `global` / `z_hysteresis`: d=0.4989, p=0.08419, q=0.7281
- `novel_tone` / `global` / `z_hysteresis`: d=0.4641, p=0.1456, q=0.7281
- `standard_tone` / `global` / `z_tortuosity`: d=-0.149, p=0.1456, q=0.7281
- `novel_tone` / `global` / `z_tortuosity`: d=0.1811, p=0.2003, q=0.7513

## Caveats

- Oddball structure is event-driven inside a run that is indexed as `task=rest`, so event-locking remains a windowed approximation rather than raw-trial EEG reconstruction.
- Standard/MNJ/reachability outputs come from the primary `ndt-analysis` pipeline; trajectory hysteresis and ESB-style scores are article-local exploratory layers.
- Control subjects have no ON/OFF medication contrast, so disease effects and pharmacology effects remain separated in the exports.
