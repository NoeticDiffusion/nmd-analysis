# Trajectory robustness summary

This summary focuses on the ideas1-selected trajectory candidates and checks whether their pooled signals survive basic temporal and QC stress tests.

## Selected metrics

- `trajectory_geometry_subject_anchored_3d` / `noetic_action`
- `trajectory_geometry_subject_anchored_3d` / `irreversibility`
- `trajectory_geometry_subject_anchored_9d` / `noetic_action_jerk`
- `trajectory_geometry_subject_anchored_9d` / `noetic_action`
- `trajectory_geometry_subject_anchored_9d` / `entropy_rate`

## Pooled effect summary by transform

### `trajectory_geometry_subject_anchored_3d` / `noetic_action`

- `observed`: medians `0.105437` vs `0.117722`, `d = -0.251`, `p = 0.0653`
- `reverse_time`: medians `0.105188` vs `0.119057`, `d = -0.254`, `p = 0.0568`, attenuation=1.011
- `time_shuffled`: medians `0.182306` vs `0.196591`, `d = -0.304`, `p = 0.0527`, attenuation=1.208

### `trajectory_geometry_subject_anchored_3d` / `irreversibility`

- `observed`: medians `0.0829588` vs `0.0847239`, `d = -0.156`, `p = 0.476`
- `reverse_time`: medians `0.0824564` vs `0.0847665`, `d = -0.156`, `p = 0.472`, attenuation=0.997
- `time_shuffled`: medians `0.108899` vs `0.103616`, `d = 0.180`, `p = 0.0699`, attenuation=1.149

### `trajectory_geometry_subject_anchored_9d` / `noetic_action_jerk`

- `observed`: medians `0.021703` vs `0.0218692`, `d = -0.342`, `p = 0.13`
- `reverse_time`: medians `0.021703` vs `0.0218692`, `d = -0.342`, `p = 0.131`, attenuation=1.000
- `time_shuffled`: medians `0.0891508` vs `0.0964551`, `d = -0.481`, `p = 0.00118`, attenuation=1.405

### `trajectory_geometry_subject_anchored_9d` / `noetic_action`

- `observed`: medians `0.257882` vs `0.276206`, `d = -0.338`, `p = 0.0328`
- `reverse_time`: medians `0.256742` vs `0.2721`, `d = -0.315`, `p = 0.0595`, attenuation=0.930
- `time_shuffled`: medians `0.486607` vs `0.514077`, `d = -0.449`, `p = 0.00842`, attenuation=1.329

### `trajectory_geometry_subject_anchored_9d` / `entropy_rate`

- `observed`: medians `1.83556` vs `1.74815`, `d = 0.158`, `p = 0.0403`
- `reverse_time`: medians `1.8363` vs `1.74774`, `d = 0.159`, `p = 0.0396`, attenuation=1.005
- `time_shuffled`: medians `2.21381` vs `2.16779`, `d = 0.222`, `p = 0.00396`, attenuation=1.400

## Observed vs transformed metric similarity

### `trajectory_geometry_subject_anchored_3d` / `noetic_action`

- `reverse_time`: rho=`0.992`, p=`0`, median abs delta=`0.00653905`
- `time_shuffled`: rho=`0.889`, p=`0`, median abs delta=`0.0722823`

### `trajectory_geometry_subject_anchored_3d` / `irreversibility`

- `reverse_time`: rho=`1.000`, p=`0`, median abs delta=`0.00025193`
- `time_shuffled`: rho=`0.632`, p=`0`, median abs delta=`0.0286036`

### `trajectory_geometry_subject_anchored_9d` / `noetic_action_jerk`

- `reverse_time`: rho=`1.000`, p=`0`, median abs delta=`0`
- `time_shuffled`: rho=`0.029`, p=`0.0924`, median abs delta=`0.0666612`

### `trajectory_geometry_subject_anchored_9d` / `noetic_action`

- `reverse_time`: rho=`0.987`, p=`0`, median abs delta=`0.0119584`
- `time_shuffled`: rho=`0.772`, p=`0`, median abs delta=`0.241026`

### `trajectory_geometry_subject_anchored_9d` / `entropy_rate`

- `reverse_time`: rho=`1.000`, p=`0`, median abs delta=`0.000715255`
- `time_shuffled`: rho=`0.695`, p=`0`, median abs delta=`0.368896`

## Strongest QC correlations

- `trajectory_geometry_subject_anchored_9d` / `irreversibility` vs `channel_coverage_frac_median`: rho=`-0.393`, p=`7.91e-12`, n=`281`
- `trajectory_geometry_subject_anchored_9d` / `irreversibility` vs `channel_count_median`: rho=`-0.393`, p=`7.91e-12`, n=`281`
- `trajectory_geometry_subject_anchored_3d` / `irreversibility` vs `channel_coverage_frac_median`: rho=`-0.364`, p=`2.99e-10`, n=`281`
- `trajectory_geometry_subject_anchored_3d` / `irreversibility` vs `channel_count_median`: rho=`-0.364`, p=`2.99e-10`, n=`281`
- `trajectory_geometry_subject_anchored_3d` / `entropy_production` vs `channel_count_median`: rho=`-0.321`, p=`3.7e-08`, n=`281`
- `trajectory_geometry_subject_anchored_3d` / `entropy_production` vs `channel_coverage_frac_median`: rho=`-0.321`, p=`3.7e-08`, n=`281`
- `trajectory_geometry_subject_anchored_9d` / `entropy_production` vs `channel_count_median`: rho=`-0.303`, p=`2.25e-07`, n=`281`
- `trajectory_geometry_subject_anchored_9d` / `entropy_production` vs `channel_coverage_frac_median`: rho=`-0.303`, p=`2.25e-07`, n=`281`
- `trajectory_geometry_subject_anchored_3d` / `entropy_rate` vs `channel_count_median`: rho=`-0.302`, p=`2.55e-07`, n=`281`
- `trajectory_geometry_subject_anchored_3d` / `entropy_rate` vs `channel_coverage_frac_median`: rho=`-0.302`, p=`2.55e-07`, n=`281`
- `trajectory_geometry_subject_anchored_9d` / `entropy_rate` vs `channel_count_median`: rho=`-0.267`, p=`5.64e-06`, n=`281`
- `trajectory_geometry_subject_anchored_9d` / `entropy_rate` vs `channel_coverage_frac_median`: rho=`-0.267`, p=`5.64e-06`, n=`281`
