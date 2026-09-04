# Depression PST event-first summary

This wrapper treats subject-anchored PST event segments as the primary inferential layer, then asks whether BDI modulates the resulting within-subject contrast scores.

## Within-subject PST contrasts

### Feedback correct vs incorrect

- `global_event_locked_trajectory_9d` / `entropy_production`: d_z=-1.103, p=0.1797, q=0.95
- `global_event_locked_trajectory_9d` / `noetic_action_jerk`: d_z=-0.9504, p=0.1797, q=0.95
- `global_event_locked_trajectory_9d` / `irreversibility`: d_z=-0.5774, p=0.1797, q=0.95
- `global_event_locked_trajectory_9d` / `noetic_action_kinetic`: d_z=1.859, p=0.25, q=0.95
- `global_event_locked_trajectory_9d` / `curvature_median`: d_z=-1.815, p=0.25, q=0.95
- `global_event_locked_trajectory_9d` / `transition_sparsity`: d_z=-0.5774, p=0.3173, q=0.95
- `global_event_locked_trajectory_9d` / `hysteresis_area_md`: d_z=1.082, p=0.5, q=0.95
- `global_event_locked_trajectory_9d` / `entropy_rate`: d_z=0.6973, p=0.5, q=0.95

### Training high-certainty vs low-certainty pairs

- `global_event_locked_trajectory_9d` / `curvature_median`: d_z=3.522, p=0.25, q=0.7536
- `global_event_locked_trajectory_9d` / `path_length`: d_z=1.411, p=0.25, q=0.7536
- `global_event_locked_trajectory_9d` / `peak_displacement`: d_z=0.8327, p=0.25, q=0.7536
- `global_event_locked_trajectory_9d` / `irreversibility`: d_z=0.5774, p=0.3173, q=0.7536
- `global_event_locked_trajectory_9d` / `self_loop_rate`: d_z=0.5774, p=0.3173, q=0.7536
- `global_event_locked_trajectory_9d` / `transition_sparsity`: d_z=0.5774, p=0.3173, q=0.7536
- `global_event_locked_trajectory_9d` / `noetic_action_potential`: d_z=-0.5774, p=0.3173, q=0.7536
- `global_event_locked_trajectory_9d` / `entropy_production`: d_z=0.5774, p=0.3173, q=0.7536

### Training mid-certainty vs low-certainty pairs

- `global_event_locked_trajectory_9d` / `entropy_production`: d_z=1.087, p=0.1797, q=0.7917
- `global_event_locked_trajectory_9d` / `noetic_action_jerk`: d_z=-1.038, p=0.1797, q=0.7917
- `global_event_locked_trajectory_9d` / `irreversibility`: d_z=1.035, p=0.1797, q=0.7917
- `global_event_locked_trajectory_9d` / `tortuosity`: d_z=-6.172, p=0.25, q=0.7917
- `global_event_locked_trajectory_9d` / `curvature_median`: d_z=-1.592, p=0.25, q=0.7917
- `global_event_locked_trajectory_9d` / `path_length`: d_z=0.6297, p=0.25, q=0.7917
- `global_event_locked_trajectory_9d` / `self_loop_rate`: d_z=0.5774, p=0.3173, q=0.8613
- `global_event_locked_trajectory_3d` / `noetic_action_kinetic`: d_z=-0.9124, p=0.1797, q=0.8906

### Training vs test

- `global_event_locked_trajectory_3d` / `peak_displacement`: d_z=2.801, p=0.25, q=0.7917
- `global_event_locked_trajectory_3d` / `hysteresis_area_de`: d_z=2.092, p=0.25, q=0.7917
- `global_event_locked_trajectory_3d` / `noetic_action_jerk`: d_z=1.393, p=0.25, q=0.7917
- `global_event_locked_trajectory_3d` / `hysteresis_area_mean`: d_z=1.366, p=0.25, q=0.7917
- `global_event_locked_trajectory_3d` / `hysteresis_area_md`: d_z=1.184, p=0.25, q=0.7917
- `global_event_locked_trajectory_3d` / `path_length`: d_z=1.114, p=0.25, q=0.7917
- `global_event_locked_trajectory_9d` / `hysteresis_area_mean`: d_z=1.385, p=0.25, q=1
- `global_event_locked_trajectory_9d` / `hysteresis_area_de`: d_z=1.352, p=0.25, q=1

### Left vs right response

- `global_event_locked_trajectory_3d` / `curvature_median`: d_z=1.153, p=0.1797, q=0.6786
- `global_event_locked_trajectory_3d` / `noetic_action_potential`: d_z=1.15, p=0.1797, q=0.6786
- `global_event_locked_trajectory_3d` / `speed_median`: d_z=1.101, p=0.1797, q=0.6786
- `global_event_locked_trajectory_3d` / `recovery_residual`: d_z=-4.97, p=0.25, q=0.6786
- `global_event_locked_trajectory_3d` / `hysteresis_area_md`: d_z=-2.819, p=0.25, q=0.6786
- `global_event_locked_trajectory_3d` / `noetic_action`: d_z=0.9149, p=0.25, q=0.6786
- `global_event_locked_trajectory_3d` / `noetic_action_jerk`: d_z=0.7183, p=0.25, q=0.6786
- `global_event_locked_trajectory_9d` / `noetic_action_jerk`: d_z=1.101, p=0.1797, q=0.8636

## BDI low vs high modulation

No BDI low-vs-high modulation rows were produced.

## Continuous BDI modulation

No continuous BDI modulation rows were produced.
