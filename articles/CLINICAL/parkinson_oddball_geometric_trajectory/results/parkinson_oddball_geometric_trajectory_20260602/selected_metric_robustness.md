# Parkinson oddball disease-first robustness

- subjects with residual `raw_nan_onset_sec`: `26`
- wrapper rows are rerun after residual-label exclusion, `sub-112` exclusion, and pooled winsorization
- coupling/asymmetry rows also receive a circular-shift family shuffle null

## auditory_arrowcue_coupling_dm_tau2_3d

- `all`: Control med=-0.03987, Parkinson med=0.08839, d=0.4924, p=0.009394
- `exclude_raw_nan`: Control med=-0.01236, Parkinson med=0.1086, d=0.4602, p=0.04063
- `exclude_sub112`: Control med=-0.04021, Parkinson med=0.08839, d=0.4979, p=0.008872
- `winsorized_2p5_97p5`: Control med=-0.03987, Parkinson med=0.08839, d=0.4826, p=0.009336
- `shuffle_null_exclude_raw_nan`: Control med=-0.01639, Parkinson med=0.01166, d=0.6377, p=0.01073

## auditory_response_asymmetry_me_tau2_3d

- `all`: Control med=-0.05923, Parkinson med=0.0183, d=0.3747, p=0.03242
- `exclude_raw_nan`: Control med=-0.09783, Parkinson med=0.0135, d=0.5764, p=0.008793
- `exclude_sub112`: Control med=-0.0665, Parkinson med=0.0183, d=0.3813, p=0.03007
- `winsorized_2p5_97p5`: Control med=-0.05923, Parkinson med=0.0183, d=0.3996, p=0.03192
- `shuffle_null_exclude_raw_nan`: Control med=0.00569, Parkinson med=-0.0007663, d=0.03905, p=0.8479

## auditory_all_coupling_me_tau1_9d

- `all`: Control med=0.09939, Parkinson med=0.1728, d=0.4117, p=0.01596
- `exclude_raw_nan`: Control med=0.1067, Parkinson med=0.1638, d=0.3307, p=0.08844
- `exclude_sub112`: Control med=0.09722, Parkinson med=0.1728, d=0.4765, p=0.008032
- `winsorized_2p5_97p5`: Control med=0.09939, Parkinson med=0.1728, d=0.4242, p=0.01595
- `shuffle_null_exclude_raw_nan`: Control med=0.01925, Parkinson med=-0.002083, d=-0.5308, p=0.0153

## auditory_arrowcue_hysteresis_area_md_9d

- `all`: Control med=0.4656, Parkinson med=0.386, d=-0.3975, p=0.02357
- `exclude_raw_nan`: Control med=0.4868, Parkinson med=0.3807, d=-0.6379, p=0.006581
- `exclude_sub112`: Control med=0.4587, Parkinson med=0.386, d=-0.3587, p=0.03596
- `winsorized_2p5_97p5`: Control med=0.4656, Parkinson med=0.386, d=-0.4205, p=0.02356

## auditory_all_return_probability_tau2_9d

- `all`: Control med=0.1429, Parkinson med=0.1215, d=-0.3327, p=0.02179
- `exclude_raw_nan`: Control med=0.1429, Parkinson med=0.1146, d=-0.2781, p=0.1254
- `exclude_sub112`: Control med=0.1429, Parkinson med=0.1215, d=-0.3275, p=0.02749
- `winsorized_2p5_97p5`: Control med=0.1429, Parkinson med=0.1215, d=-0.3404, p=0.02165

## auditory_arrowcue_noetic_action_jerk_9d

- `all`: Control med=0.03459, Parkinson med=0.03036, d=-0.343, p=0.07358
- `exclude_raw_nan`: Control med=0.03706, Parkinson med=0.02975, d=-0.5528, p=0.003275
- `exclude_sub112`: Control med=0.03421, Parkinson med=0.03036, d=-0.312, p=0.1071
- `winsorized_2p5_97p5`: Control med=0.03459, Parkinson med=0.03036, d=-0.3141, p=0.07527

## global_m_median_3d

- `all`: Control med=0.03467, Parkinson med=0.02008, d=-0.6018, p=0.004075
- `exclude_sub112`: Control med=0.03864, Parkinson med=0.02008, d=-0.6437, p=0.002179
- `winsorized_2p5_97p5`: Control med=0.03467, Parkinson med=0.02008, d=-0.589, p=0.004074

## reachability_tube_q_ratio_h4_mean

- `all`: Control med=0.2474, Parkinson med=0.2821, d=0.557, p=0.002509
- `exclude_sub112`: Control med=0.2473, Parkinson med=0.2821, d=0.5653, p=0.002241
- `winsorized_2p5_97p5`: Control med=0.2474, Parkinson med=0.2821, d=0.5592, p=0.002508
