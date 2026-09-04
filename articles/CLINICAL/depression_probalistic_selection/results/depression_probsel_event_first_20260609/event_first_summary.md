# Depression PST event-first summary

This wrapper treats subject-anchored PST event segments as the primary inferential layer, then asks whether BDI modulates the resulting within-subject contrast scores.

## Within-subject PST contrasts

### Feedback correct vs incorrect

- `global_event_locked_trajectory_3d` / `path_length`: d_z=0.3228, p=9.855e-05, q=0.001872
- `global_event_locked_trajectory_9d` / `noetic_action_kinetic`: d_z=0.2371, p=0.0002541, q=0.004827
- `global_event_locked_trajectory_3d` / `noetic_action_jerk`: d_z=0.08758, p=0.0009319, q=0.005909
- `global_event_locked_trajectory_3d` / `hysteresis_area_de`: d_z=0.2979, p=0.000933, q=0.005909
- `global_event_locked_trajectory_9d` / `path_length`: d_z=0.2519, p=0.0009967, q=0.009469
- `global_event_locked_trajectory_9d` / `speed_median`: d_z=0.3003, p=0.00183, q=0.01159
- `global_event_locked_trajectory_9d` / `curvature_median`: d_z=-0.2613, p=0.003589, q=0.01705
- `global_event_locked_trajectory_3d` / `curvature_median`: d_z=-0.2187, p=0.005625, q=0.02432

### Training high-certainty vs low-certainty pairs

- `global_event_locked_trajectory_9d` / `speed_median`: d_z=0.1833, p=0.0755, q=0.6689
- `global_event_locked_trajectory_9d` / `curvature_median`: d_z=-0.03712, p=0.1132, q=0.6689
- `global_event_locked_trajectory_9d` / `tortuosity`: d_z=0.1919, p=0.1394, q=0.6689
- `global_event_locked_trajectory_9d` / `irreversibility`: d_z=-0.1291, p=0.1463, q=0.6689
- `global_event_locked_trajectory_9d` / `entropy_rate`: d_z=-0.09416, p=0.188, q=0.6689
- `global_event_locked_trajectory_9d` / `hysteresis_area_md`: d_z=0.1063, p=0.2266, q=0.6689
- `global_event_locked_trajectory_9d` / `noetic_action`: d_z=-0.07299, p=0.3103, q=0.6689
- `global_event_locked_trajectory_9d` / `path_length`: d_z=0.1112, p=0.3524, q=0.6689

### Training mid-certainty vs low-certainty pairs

- `global_event_locked_trajectory_9d` / `noetic_action_kinetic`: d_z=-0.18, p=0.01785, q=0.3391
- `global_event_locked_trajectory_3d` / `hysteresis_area_mean`: d_z=0.08261, p=0.136, q=0.8526
- `global_event_locked_trajectory_3d` / `entropy_rate`: d_z=-0.06798, p=0.2786, q=0.8526
- `global_event_locked_trajectory_3d` / `peak_displacement`: d_z=0.05483, p=0.3799, q=0.8526
- `global_event_locked_trajectory_3d` / `noetic_action_potential`: d_z=-0.1247, p=0.4598, q=0.8526
- `global_event_locked_trajectory_3d` / `irreversibility`: d_z=0.0632, p=0.5585, q=0.8526
- `global_event_locked_trajectory_3d` / `curvature_median`: d_z=0.001898, p=0.6313, q=0.8526
- `global_event_locked_trajectory_3d` / `noetic_action_jerk`: d_z=-0.06188, p=0.6875, q=0.8526

### Training vs test

- `global_event_locked_trajectory_9d` / `transition_sparsity`: d_z=0.4787, p=1.277e-07, q=1.555e-06
- `global_event_locked_trajectory_9d` / `noetic_action_potential`: d_z=-0.4208, p=1.637e-07, q=1.555e-06
- `global_event_locked_trajectory_9d` / `peak_displacement`: d_z=0.4793, p=9.254e-07, q=5.861e-06
- `global_event_locked_trajectory_3d` / `peak_displacement`: d_z=0.469, p=8.67e-07, q=1.647e-05
- `global_event_locked_trajectory_3d` / `hysteresis_area_md`: d_z=0.466, p=2.325e-06, q=2.209e-05
- `global_event_locked_trajectory_3d` / `noetic_action_potential`: d_z=-0.31, p=7.195e-06, q=3.726e-05
- `global_event_locked_trajectory_3d` / `transition_sparsity`: d_z=0.3877, p=8.996e-06, q=3.726e-05
- `global_event_locked_trajectory_3d` / `path_length`: d_z=0.4316, p=9.805e-06, q=3.726e-05

### Left vs right response

- `global_event_locked_trajectory_3d` / `hysteresis_area_me`: d_z=0.0578, p=0.3399, q=0.9588
- `global_event_locked_trajectory_3d` / `path_length`: d_z=-0.08706, p=0.3412, q=0.9588
- `global_event_locked_trajectory_3d` / `peak_displacement`: d_z=0.08991, p=0.4187, q=0.9588
- `global_event_locked_trajectory_3d` / `tortuosity`: d_z=-0.06111, p=0.491, q=0.9588
- `global_event_locked_trajectory_3d` / `hysteresis_area_de`: d_z=-0.06521, p=0.5211, q=0.9588
- `global_event_locked_trajectory_3d` / `self_loop_rate`: d_z=0.0558, p=0.5313, q=0.9588
- `global_event_locked_trajectory_3d` / `hysteresis_area_mean`: d_z=-0.09874, p=0.5995, q=0.9588
- `global_event_locked_trajectory_3d` / `noetic_action_potential`: d_z=-0.01391, p=0.6567, q=0.9588

## BDI low vs high modulation

### Feedback correct vs incorrect

- `global_event_locked_trajectory_9d` / `hysteresis_area_de`: d=-0.4434, p=0.02458, q=0.3784
- `global_event_locked_trajectory_9d` / `transition_sparsity`: d=-0.453, p=0.04977, q=0.3784
- `global_event_locked_trajectory_9d` / `irreversibility`: d=0.3844, p=0.05975, q=0.3784
- `global_event_locked_trajectory_9d` / `tortuosity`: d=0.2969, p=0.1131, q=0.5111
- `global_event_locked_trajectory_9d` / `hysteresis_area_me`: d=0.3174, p=0.1345, q=0.5111
- `global_event_locked_trajectory_9d` / `curvature_median`: d=0.2326, p=0.2121, q=0.5764

### Training high-certainty vs low-certainty pairs

- `global_event_locked_trajectory_3d` / `noetic_action_kinetic`: d=-0.6019, p=0.00845, q=0.1606
- `global_event_locked_trajectory_3d` / `self_loop_rate`: d=0.4998, p=0.02531, q=0.2405
- `global_event_locked_trajectory_9d` / `self_loop_rate`: d=0.4874, p=0.01651, q=0.3136
- `global_event_locked_trajectory_3d` / `tortuosity`: d=-0.3426, p=0.05311, q=0.3364
- `global_event_locked_trajectory_3d` / `transition_sparsity`: d=-0.2298, p=0.1386, q=0.5366
- `global_event_locked_trajectory_3d` / `hysteresis_area_de`: d=0.3408, p=0.153, q=0.5366

### Training mid-certainty vs low-certainty pairs

- `global_event_locked_trajectory_9d` / `self_loop_rate`: d=0.4359, p=0.03976, q=0.6194
- `global_event_locked_trajectory_9d` / `noetic_action`: d=0.4263, p=0.0718, q=0.6194
- `global_event_locked_trajectory_9d` / `hysteresis_area_me`: d=-0.3066, p=0.1288, q=0.6194
- `global_event_locked_trajectory_9d` / `transition_sparsity`: d=-0.2731, p=0.1361, q=0.6194
- `global_event_locked_trajectory_9d` / `noetic_action_potential`: d=0.3092, p=0.163, q=0.6194
- `global_event_locked_trajectory_3d` / `hysteresis_area_me`: d=-0.4468, p=0.03354, q=0.6373

### Training vs test

- `global_event_locked_trajectory_9d` / `self_loop_rate`: d=-0.4085, p=0.01697, q=0.3224
- `global_event_locked_trajectory_9d` / `transition_sparsity`: d=-0.3226, p=0.0695, q=0.6602
- `global_event_locked_trajectory_9d` / `tortuosity`: d=0.3241, p=0.1098, q=0.6954
- `global_event_locked_trajectory_9d` / `curvature_median`: d=0.2918, p=0.1803, q=0.7474
- `global_event_locked_trajectory_9d` / `irreversibility`: d=0.24, p=0.2085, q=0.7474
- `global_event_locked_trajectory_9d` / `entropy_production`: d=0.2204, p=0.236, q=0.7474

### Left vs right response

- `global_event_locked_trajectory_3d` / `hysteresis_area_me`: d=-0.3261, p=0.1416, q=0.8021
- `global_event_locked_trajectory_3d` / `noetic_action_kinetic`: d=-0.3634, p=0.175, q=0.8021
- `global_event_locked_trajectory_3d` / `entropy_production`: d=0.2859, p=0.2308, q=0.8021
- `global_event_locked_trajectory_3d` / `hysteresis_area_mean`: d=0.2395, p=0.3336, q=0.8021
- `global_event_locked_trajectory_3d` / `speed_median`: d=-0.228, p=0.3782, q=0.8021
- `global_event_locked_trajectory_3d` / `hysteresis_area_md`: d=0.1851, p=0.3826, q=0.8021

## Continuous BDI modulation

### Feedback correct vs incorrect

- `global_event_locked_trajectory_9d` / `hysteresis_area_de`: rho=-0.2347, p=0.009555, q=0.1815
- `global_event_locked_trajectory_9d` / `irreversibility`: rho=0.183, p=0.04453, q=0.4231
- `global_event_locked_trajectory_9d` / `transition_sparsity`: rho=-0.1397, p=0.1263, q=0.6692
- `global_event_locked_trajectory_9d` / `curvature_median`: rho=0.1346, p=0.1409, q=0.6692
- `global_event_locked_trajectory_9d` / `peak_displacement`: rho=0.1205, p=0.1881, q=0.7148
- `global_event_locked_trajectory_9d` / `tortuosity`: rho=0.09682, p=0.2907, q=0.7676

### Training high-certainty vs low-certainty pairs

- `global_event_locked_trajectory_3d` / `hysteresis_area_de`: rho=0.2396, p=0.008128, q=0.09435
- `global_event_locked_trajectory_3d` / `self_loop_rate`: rho=0.2336, p=0.009932, q=0.09435
- `global_event_locked_trajectory_3d` / `noetic_action_kinetic`: rho=-0.1712, p=0.06042, q=0.3826
- `global_event_locked_trajectory_3d` / `entropy_production`: rho=-0.1341, p=0.1426, q=0.5873
- `global_event_locked_trajectory_3d` / `hysteresis_area_mean`: rho=0.1302, p=0.1546, q=0.5873
- `global_event_locked_trajectory_3d` / `transition_sparsity`: rho=-0.1111, p=0.2251, q=0.6619

### Training mid-certainty vs low-certainty pairs

- `global_event_locked_trajectory_9d` / `self_loop_rate`: rho=0.2091, p=0.02137, q=0.406
- `global_event_locked_trajectory_9d` / `hysteresis_area_me`: rho=-0.1763, p=0.0531, q=0.5044
- `global_event_locked_trajectory_3d` / `hysteresis_area_me`: rho=-0.1902, p=0.0367, q=0.6973
- `global_event_locked_trajectory_9d` / `transition_sparsity`: rho=-0.1122, p=0.2206, q=0.8058
- `global_event_locked_trajectory_9d` / `hysteresis_area_mean`: rho=-0.1082, p=0.2377, q=0.8058
- `global_event_locked_trajectory_9d` / `speed_median`: rho=0.1074, p=0.2409, q=0.8058

### Training vs test

- `global_event_locked_trajectory_9d` / `curvature_median`: rho=0.1772, p=0.05184, q=0.3591
- `global_event_locked_trajectory_9d` / `self_loop_rate`: rho=-0.1663, p=0.0683, q=0.3591
- `global_event_locked_trajectory_9d` / `peak_displacement`: rho=-0.1573, p=0.08487, q=0.3591
- `global_event_locked_trajectory_9d` / `irreversibility`: rho=0.1531, p=0.09359, q=0.3591
- `global_event_locked_trajectory_9d` / `hysteresis_area_me`: rho=-0.1444, p=0.114, q=0.3591
- `global_event_locked_trajectory_9d` / `entropy_production`: rho=0.1426, p=0.1188, q=0.3591

### Left vs right response

- `global_event_locked_trajectory_3d` / `entropy_production`: rho=0.1512, p=0.09788, q=0.798
- `global_event_locked_trajectory_3d` / `hysteresis_area_mean`: rho=0.1496, p=0.1014, q=0.798
- `global_event_locked_trajectory_3d` / `noetic_action`: rho=0.1067, p=0.2442, q=0.798
- `global_event_locked_trajectory_3d` / `hysteresis_area_md`: rho=0.1051, p=0.2514, q=0.798
- `global_event_locked_trajectory_3d` / `self_loop_rate`: rho=-0.0892, p=0.3305, q=0.798
- `global_event_locked_trajectory_3d` / `recovery_residual`: rho=0.08019, p=0.3819, q=0.798
