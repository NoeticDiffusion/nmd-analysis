# Selected metric robustness

- subjects with residual `raw_nan_onset_sec`: `26`
- article-local event rows already exclude `raw_nan` events by construction
- group-level follow-up re-runs selected rows after subject exclusion or winsorization

## auditory_other_transition_sparsity_3d

- `all`: other_mean med=0.8767, auditory_all med=0.9514, d=3.376, p=1.034e-25
- `exclude_raw_nan`: other_mean med=0.8767, auditory_all med=0.9514, d=3.766, p=1.949e-21
- `control`: other_mean med=0.8733, auditory_all med=0.9514, d=3.651, p=7.105e-15
- `parkinson`: other_mean med=0.8767, auditory_all med=0.9514, d=3.254, p=8.284e-18

## auditory_other_entropy_rate_9d

- `all`: other_mean med=0.7881, auditory_all med=0.4332, d=-2.941, p=1.044e-25
- `exclude_raw_nan`: other_mean med=0.79, auditory_all med=0.4329, d=-3.121, p=1.972e-21
- `control`: other_mean med=0.7833, auditory_all med=0.4175, d=-2.858, p=7.105e-15
- `parkinson`: other_mean med=0.79, auditory_all med=0.4357, d=-2.969, p=8.33e-18

## auditory_other_peak_displacement_9d

- `all`: other_mean med=2.498, auditory_all med=1.512, d=-2.096, p=1.088e-25
- `exclude_raw_nan`: other_mean med=2.513, auditory_all med=1.512, d=-2.134, p=1.972e-21
- `control`: other_mean med=2.582, auditory_all med=1.473, d=-2.306, p=7.105e-15
- `parkinson`: other_mean med=2.468, auditory_all med=1.528, d=-1.998, p=8.861e-18

## arrowcue_entropy_rate_9d

- `all`: standard_arrowcue med=1.127, auditory_arrowcue med=0.432, d=-4.731, p=1.044e-25
- `exclude_raw_nan`: standard_arrowcue med=1.129, auditory_arrowcue med=0.4288, d=-5.054, p=1.972e-21
- `control`: standard_arrowcue med=1.122, auditory_arrowcue med=0.4131, d=-5.134, p=7.105e-15
- `parkinson`: standard_arrowcue med=1.14, auditory_arrowcue med=0.4369, d=-4.566, p=8.33e-18

## global_m_median_3d

- `all`: Control med=0.03467, Parkinson med=0.02008, d=-0.6018, p=0.004075
- `exclude_sub112`: Control med=0.03864, Parkinson med=0.02008, d=-0.6437, p=0.002179
- `winsorized_2p5_97p5`: Control med=0.03467, Parkinson med=0.02008, d=-0.589, p=0.004074

## tube_q_ratio_h4_mean

- `all`: Control med=0.2474, Parkinson med=0.2821, d=0.557, p=0.002509
- `exclude_sub112`: Control med=0.2473, Parkinson med=0.2821, d=0.5653, p=0.002241
- `winsorized_2p5_97p5`: Control med=0.2474, Parkinson med=0.2821, d=0.5592, p=0.002508

## jacobian9d_frobenius_norm_median

- `all`: Control med=0.633, Parkinson med=0.6295, d=0.01697, p=0.9751
- `exclude_sub112`: Control med=0.6321, Parkinson med=0.6295, d=0.1013, p=0.8146
- `winsorized_2p5_97p5`: Control med=0.633, Parkinson med=0.6295, d=0.01515, p=0.9734
