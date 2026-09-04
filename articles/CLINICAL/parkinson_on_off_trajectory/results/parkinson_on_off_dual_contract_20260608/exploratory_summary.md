# Exploratory Parkinson ON/OFF summary

This rerun splits inference by coordinate contract: `cohort_anchored` is primary for disease-state contrasts (`Control vs Parkinson OFF`, plus disease-facing `Control vs Parkinson ON` context), while `subject_anchored` remains primary for the paired pharmacology contrast (`Parkinson OFF vs ON`).

Oddball segmentation now prefers H5 `event_windows/*` start/stop indices when present, with guarded fallback to the older nearest-time mapping.

## Standard ndt-analysis layer

### Parkinson_OFF_vs_ON (subject_anchored)

- `regional_mnps_jacobian_3d / temporal / anisotropy_abs_eig_mean`: d=-0.483, p=0.0004998, q=0.03798
- `tier2_jacobian / signed_divergence_balance_mean_neg`: d=-0.711, p=0.002999, q=0.06597
- `regional_mnps_jacobian_3d / frontal / trace_median`: d=0.6504, p=0.002999, q=0.1139
- `regional_mnps_jacobian_3d / temporal / frobenius_norm_mean`: d=-0.5715, p=0.007496, q=0.1443
- `regional_mnps_jacobian_3d / temporal / a_operator_norm_mean`: d=-0.5626, p=0.008496, q=0.1443
- `regional_mnps_jacobian_3d / temporal / spectral_radius_mean`: d=-0.5479, p=0.009495, q=0.1443

### Control_vs_Parkinson_OFF (cohort_anchored)

- `global_mnps_9d / d_n_std`: d=-1.194, p=0.0004998, q=0.01349
- `regional_9d / frontal / d_n_std`: d=-1.268, p=0.0004998, q=0.01799
- `regional_9d / parietal_occipital / d_n_std`: d=-1.215, p=0.0004998, q=0.01799
- `regional_9d / frontal / m_e_std`: d=-1.189, p=0.0004998, q=0.01799
- `regional_9d / central / d_n_std`: d=-0.9732, p=0.001999, q=0.04567
- `regional_9d / temporal / d_n_std`: d=-0.9278, p=0.002499, q=0.04567

### Control_vs_Parkinson_ON (cohort_anchored)

- `global_mnps_jacobian_9d / mdr_median`: d=1.167, p=0.0004998, q=0.009495
- `regional_mnps_jacobian_9d / block_anisotropy_mean`: d=-0.8461, p=0.001499, q=0.01349
- `global_mnps_3d / e_std`: d=-0.8291, p=0.001999, q=0.01799
- `global_mnps_9d / d_n_std`: d=-1.122, p=0.0009995, q=0.02024
- `global_mnps_9d / e_m_mean`: d=-0.9603, p=0.001499, q=0.02024
- `global_mnps_jacobian_9d_block_jacobian / block_anisotropy_mean`: d=-0.8461, p=0.002499, q=0.02249

## Event-locked trajectory layer

### Parkinson_OFF_vs_ON (subject_anchored)

- `regional_event_locked_trajectory_9d` / `eyes_open` / `central` / `noetic_action_jerk`: d=-0.6405, p=0.0008081, q=0.2263
- `regional_event_locked_trajectory_3d` / `eyes_open` / `central` / `noetic_action_jerk`: d=-0.3954, p=0.001296, q=0.363
- `regional_event_locked_trajectory_9d` / `eyes_open` / `central` / `path_length`: d=-0.7143, p=0.002785, q=0.3899
- `global_event_locked_trajectory_3d` / `eyes_closed` / `global` / `curvature_median`: d=-0.549, p=0.02027, q=0.8394
- `global_event_locked_trajectory_3d` / `novel_tone` / `global` / `noetic_action`: d=0.4238, p=0.03668, q=0.8394
- `global_event_locked_trajectory_3d` / `novel_tone` / `global` / `noetic_action_potential`: d=0.4265, p=0.04512, q=0.8394

### Control_vs_Parkinson_OFF (cohort_anchored)

- `global_event_locked_trajectory_3d` / `eyes_closed` / `global` / `speed_median`: d=-1.212, p=4.701e-05, q=0.002539
- `global_event_locked_trajectory_3d` / `eyes_closed` / `global` / `noetic_action_kinetic`: d=-0.9277, p=7.815e-05, q=0.002539
- `global_event_locked_trajectory_3d` / `eyes_closed` / `global` / `noetic_action_jerk`: d=-0.9167, p=0.0001088, q=0.002539
- `global_event_locked_trajectory_3d` / `eyes_closed` / `global` / `path_length`: d=-1.189, p=0.0002073, q=0.003627
- `global_event_locked_trajectory_9d` / `eyes_closed` / `global` / `noetic_action_kinetic`: d=-1.085, p=7.187e-05, q=0.005031
- `global_event_locked_trajectory_9d` / `eyes_closed` / `global` / `speed_median`: d=-1.084, p=0.0003307, q=0.01157

### Control_vs_Parkinson_ON (cohort_anchored)

- `global_event_locked_trajectory_3d` / `novel_tone` / `global` / `hysteresis_area_me`: d=-1.039, p=0.0003842, q=0.02689
- `global_event_locked_trajectory_3d` / `eyes_closed` / `global` / `speed_median`: d=-0.9159, p=0.001423, q=0.03648
- `global_event_locked_trajectory_3d` / `standard_tone` / `global` / `hysteresis_area_me`: d=-0.9899, p=0.001563, q=0.03648
- `global_event_locked_trajectory_3d` / `eyes_closed` / `global` / `noetic_action_kinetic`: d=-0.7559, p=0.00339, q=0.05393
- `global_event_locked_trajectory_3d` / `eyes_closed` / `global` / `noetic_action_jerk`: d=-0.7141, p=0.003852, q=0.05393
- `global_event_locked_trajectory_3d` / `eyes_open` / `global` / `path_length`: d=-0.8579, p=0.006223, q=0.05887

## Trajectory ESB

### Parkinson_OFF_vs_ON (subject_anchored)

- `novel_tone` / `frontal` / `trajectory_esb2`: d=-0.498, p=0.01874, q=0.6015
- `standard_tone` / `temporal` / `trajectory_esb2`: d=-0.3842, p=0.04512, q=0.6015
- `standard_tone` / `temporal` / `trajectory_esb3`: d=-0.3252, p=0.04826, q=0.6015
- `target_tone` / `frontal` / `z_recovery`: d=-0.3697, p=0.05875, q=0.6015

### Control_vs_Parkinson_OFF (cohort_anchored)

- `target_tone` / `global` / `z_recovery`: d=-0.5231, p=0.03282, q=0.3585
- `standard_tone` / `global` / `z_recovery`: d=-0.5138, p=0.04781, q=0.3585
- `target_tone` / `global` / `z_tortuosity`: d=0.2322, p=0.1456, q=0.5533
- `novel_tone` / `global` / `trajectory_esb2`: d=-0.3919, p=0.2216, q=0.5533

### Control_vs_Parkinson_ON (cohort_anchored)

- `standard_tone` / `frontal` / `z_tortuosity`: d=0.8348, p=0.004902, q=0.2941
- `target_tone` / `frontal` / `z_tortuosity`: d=0.6905, p=0.01449, q=0.4348
- `standard_tone` / `global` / `z_recovery`: d=-0.294, p=0.09519, q=0.5527
- `target_tone` / `global` / `z_recovery`: d=-0.2533, p=0.116, q=0.5527

## Caveats

- Oddball structure is still event-driven inside a run indexed as `task=rest`, so event-locking remains a processed-window approximation rather than raw-trial EEG reconstruction.
- Standard/MNJ/reachability outputs come from the repository `ndt-analysis` pipeline; trajectory hysteresis and ESB-style scores remain article-local exploratory layers.
- Control subjects have no medication pairing, so disease-state and pharmacology questions are intentionally answered with different optimal coordinate contracts.
