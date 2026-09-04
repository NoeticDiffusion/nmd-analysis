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

- `observed`: medians `0.0931062` vs `0.101212`, `d = -0.290`, `p = 0.0299`
- `reverse_time`: medians `0.0918758` vs `0.106749`, `d = -0.308`, `p = 0.0124`, attenuation=1.064
- `time_shuffled`: medians `0.176464` vs `0.198921`, `d = -0.362`, `p = 0.00354`, attenuation=1.250

### `trajectory_geometry_subject_anchored_3d` / `irreversibility`

- `observed`: medians `0.0742696` vs `0.0773098`, `d = -0.280`, `p = 0.102`
- `reverse_time`: medians `0.0739336` vs `0.0771456`, `d = -0.281`, `p = 0.102`, attenuation=1.004
- `time_shuffled`: medians `0.0980776` vs `0.0987249`, `d = 0.050`, `p = 0.922`, attenuation=0.178

### `trajectory_geometry_subject_anchored_9d` / `noetic_action_jerk`

- `observed`: medians `0.0232417` vs `0.0255664`, `d = -0.240`, `p = 0.0547`
- `reverse_time`: medians `0.0232417` vs `0.0255705`, `d = -0.240`, `p = 0.0547`, attenuation=1.000
- `time_shuffled`: medians `0.0934222` vs `0.103496`, `d = -0.388`, `p = 2.25e-06`, attenuation=1.619

### `trajectory_geometry_subject_anchored_9d` / `noetic_action`

- `observed`: medians `0.226352` vs `0.23789`, `d = -0.365`, `p = 0.0294`
- `reverse_time`: medians `0.226528` vs `0.22994`, `d = -0.328`, `p = 0.0865`, attenuation=0.901
- `time_shuffled`: medians `0.460092` vs `0.487868`, `d = -0.420`, `p = 0.015`, attenuation=1.151

### `trajectory_geometry_subject_anchored_9d` / `entropy_rate`

- `observed`: medians `2.01612` vs `1.94851`, `d = 0.158`, `p = 0.0388`
- `reverse_time`: medians `2.01691` vs `1.94884`, `d = 0.158`, `p = 0.038`, attenuation=0.999
- `time_shuffled`: medians `2.46259` vs `2.44182`, `d = 0.147`, `p = 0.00311`, attenuation=0.930

## Observed vs transformed metric similarity

### `trajectory_geometry_subject_anchored_3d` / `noetic_action`

- `reverse_time`: rho=`0.989`, p=`0`, median abs delta=`0.00727389`
- `time_shuffled`: rho=`0.824`, p=`0`, median abs delta=`0.0854529`

### `trajectory_geometry_subject_anchored_3d` / `irreversibility`

- `reverse_time`: rho=`1.000`, p=`0`, median abs delta=`0.000249166`
- `time_shuffled`: rho=`0.345`, p=`6.79e-94`, median abs delta=`0.0290791`

### `trajectory_geometry_subject_anchored_9d` / `noetic_action_jerk`

- `reverse_time`: rho=`1.000`, p=`0`, median abs delta=`0`
- `time_shuffled`: rho=`-0.166`, p=`4.39e-22`, median abs delta=`0.0709085`

### `trajectory_geometry_subject_anchored_9d` / `noetic_action`

- `reverse_time`: rho=`0.974`, p=`0`, median abs delta=`0.013623`
- `time_shuffled`: rho=`0.683`, p=`0`, median abs delta=`0.256518`

### `trajectory_geometry_subject_anchored_9d` / `entropy_rate`

- `reverse_time`: rho=`1.000`, p=`0`, median abs delta=`0.000656659`
- `time_shuffled`: rho=`0.656`, p=`0`, median abs delta=`0.398985`

## Strongest QC correlations

- `trajectory_geometry_subject_anchored_3d` / `irreversibility` vs `n_runs_support`: rho=`0.343`, p=`3.52e-09`, n=`281`
- `trajectory_geometry_subject_anchored_9d` / `irreversibility` vs `channel_coverage_frac_median`: rho=`-0.327`, p=`7.51e-05`, n=`141`
- `trajectory_geometry_subject_anchored_9d` / `irreversibility` vs `channel_count_median`: rho=`-0.327`, p=`7.51e-05`, n=`141`
- `trajectory_geometry_subject_anchored_9d` / `irreversibility` vs `n_runs_support`: rho=`0.281`, p=`1.72e-06`, n=`281`
- `trajectory_geometry_subject_anchored_3d` / `irreversibility` vs `channel_count_median`: rho=`-0.267`, p=`0.00137`, n=`141`
- `trajectory_geometry_subject_anchored_3d` / `irreversibility` vs `channel_coverage_frac_median`: rho=`-0.267`, p=`0.00137`, n=`141`
- `trajectory_geometry_subject_anchored_9d` / `entropy_production` vs `n_runs_support`: rho=`0.259`, p=`1.07e-05`, n=`281`
- `trajectory_geometry_subject_anchored_3d` / `entropy_rate` vs `n_runs_support`: rho=`0.233`, p=`7.86e-05`, n=`281`
- `trajectory_geometry_subject_anchored_9d` / `entropy_rate` vs `channel_coverage_frac_median`: rho=`-0.218`, p=`0.00938`, n=`141`
- `trajectory_geometry_subject_anchored_9d` / `entropy_rate` vs `channel_count_median`: rho=`-0.218`, p=`0.00938`, n=`141`
- `trajectory_geometry_subject_anchored_3d` / `entropy_rate` vs `channel_count_median`: rho=`-0.212`, p=`0.0115`, n=`141`
- `trajectory_geometry_subject_anchored_3d` / `entropy_rate` vs `channel_coverage_frac_median`: rho=`-0.212`, p=`0.0115`, n=`141`
