# Parkinson oddball disease-first summary

This run keeps `ds004574` fixed and treats oddball trajectories as a disease-facing cost, recovery, and coupling problem.

## Disease-first wrapper rows

- `global_event_locked_trajectory_3d` / `auditory_arrowcue` / `coupling_dm_tau2`: d=0.4924, p=0.009394, q=0.6433
- `global_event_locked_trajectory_3d` / `standard_response` / `torsion_median`: d=0.3499, p=0.01035, q=0.6433
- `global_event_locked_trajectory_3d` / `standard_precue` / `asymmetry_md_tau1`: d=0.4676, p=0.01072, q=0.6433
- `global_event_locked_trajectory_3d` / `visual_all` / `tortuosity`: d=0.469, p=0.01098, q=0.6433
- `global_event_locked_trajectory_3d` / `all_arrowcue` / `coupling_em_tau1`: d=0.353, p=0.01098, q=0.6433
- `global_event_locked_trajectory_3d` / `all_precue` / `asymmetry_md_tau1`: d=0.491, p=0.01125, q=0.6433
- `global_event_locked_trajectory_3d` / `all_precue` / `coupling_dm_tau1`: d=-0.404, p=0.01439, q=0.6433
- `global_event_locked_trajectory_3d` / `visual_precue` / `tortuosity`: d=0.4711, p=0.0149, q=0.6433
- `global_event_locked_trajectory_3d` / `standard_arrowcue` / `coupling_em_tau1`: d=0.3541, p=0.01577, q=0.6433
- `global_event_locked_trajectory_3d` / `standard_all` / `torsion_median`: d=0.2836, p=0.01632, q=0.6433
- `global_event_locked_trajectory_3d` / `all_precue` / `torsion_median`: d=0.3309, p=0.01651, q=0.6433
- `global_event_locked_trajectory_3d` / `visual_all` / `asymmetry_me_tau1`: d=-0.3945, p=0.0167, q=0.6433
- `global_event_locked_trajectory_3d` / `standard_arrowcue` / `asymmetry_md_tau1`: d=0.4107, p=0.01807, q=0.6433
- `global_event_locked_trajectory_3d` / `standard_precue` / `torsion_median`: d=0.3202, p=0.01828, q=0.6433
- `global_event_locked_trajectory_3d` / `all_arrowcue` / `coupling_dm_tau1`: d=-0.3683, p=0.0189, q=0.6433

## Standard supportive rows

- `global_mnps_3d` / `m_median`: d=-0.6018, p=0.0009995, q=0.008996
- `adaptive_collapse` / `q_ratio_h4`: d=0.5182, p=0.003998, q=0.01999
- `reachability_cones` / `q_ratio_h2_median`: d=0.5523, p=0.0009995, q=0.03848
- `reachability_cones` / `cone_q_ratio_h2_median`: d=0.5523, p=0.001499, q=0.03848
- `reachability_cones` / `cone_q_ratio_h3_median`: d=0.5388, p=0.001499, q=0.03848
- `reachability_cones` / `tube_q_ratio_h4_mean`: d=0.557, p=0.001999, q=0.03848
- `reachability_cones` / `tube_q_ratio_h4_median`: d=0.5182, p=0.003998, q=0.05131
- `reachability_cones` / `median_min_eig_over_median_eig`: d=-0.4726, p=0.004998, q=0.05131
- `reachability_cones` / `q_ratio_h3_median`: d=0.5388, p=0.005497, q=0.05131
- `reachability_cones` / `q_ratio_h4_median`: d=0.5182, p=0.005497, q=0.05131

## Secondary subtype rows

- `global_event_locked_trajectory_9d` / `standard_all__vs__auditory_all` / `transition_sparsity`: d=2.659, p=1.027e-25, q=8.564e-25
- `global_event_locked_trajectory_3d` / `standard_arrowcue__vs__auditory_arrowcue` / `transition_sparsity`: d=4.211, p=1.03e-25, q=8.564e-25
- `global_event_locked_trajectory_9d` / `standard_arrowcue__vs__auditory_arrowcue` / `transition_sparsity`: d=3.384, p=1.031e-25, q=8.564e-25
- `global_event_locked_trajectory_3d` / `standard_all__vs__auditory_all` / `transition_sparsity`: d=3.461, p=1.034e-25, q=8.564e-25
- `global_event_locked_trajectory_3d` / `standard_precue__vs__auditory_precue` / `transition_sparsity`: d=3.962, p=1.034e-25, q=8.564e-25
- `global_event_locked_trajectory_9d` / `standard_response__vs__auditory_response` / `transition_sparsity`: d=2.323, p=1.035e-25, q=8.564e-25
- `global_event_locked_trajectory_3d` / `standard_response__vs__auditory_response` / `transition_sparsity`: d=2.817, p=1.035e-25, q=8.564e-25
- `global_event_locked_trajectory_9d` / `standard_arrowcue__vs__auditory_arrowcue` / `entropy_rate`: d=-4.731, p=1.044e-25, q=8.564e-25
- `global_event_locked_trajectory_3d` / `standard_arrowcue__vs__auditory_arrowcue` / `entropy_rate`: d=-4.074, p=1.044e-25, q=8.564e-25
- `global_event_locked_trajectory_3d` / `standard_all__vs__auditory_all` / `entropy_rate`: d=-4.012, p=1.044e-25, q=8.564e-25
- `global_event_locked_trajectory_9d` / `standard_all__vs__auditory_all` / `entropy_rate`: d=-3.913, p=1.044e-25, q=8.564e-25
- `global_event_locked_trajectory_3d` / `standard_precue__vs__auditory_precue` / `entropy_rate`: d=-3.911, p=1.044e-25, q=8.564e-25

## Selection queue

- priority `0` / `wrapper` / `Control_vs_Parkinson` / `auditory_arrowcue` / `coupling_dm_tau2`: |d|=0.4924, q=0.6433
- priority `0` / `wrapper` / `Control_vs_Parkinson` / `auditory_all` / `coupling_dm_tau2`: |d|=0.4733, q=0.6433
- priority `0` / `wrapper` / `Control_vs_Parkinson` / `auditory_response` / `asymmetry_me_tau2`: |d|=0.3747, q=0.6433
- priority `0` / `wrapper` / `Control_vs_Parkinson` / `auditory_all` / `coupling_me_tau1`: |d|=0.4117, q=0.7175
- priority `0` / `wrapper` / `Control_vs_Parkinson` / `auditory_arrowcue` / `hysteresis_area_md`: |d|=0.3975, q=0.7175
- priority `0` / `wrapper` / `Control_vs_Parkinson` / `auditory_all` / `hysteresis_area_md`: |d|=0.3712, q=0.7175
- priority `0` / `wrapper` / `Control_vs_Parkinson` / `auditory_all` / `coupling_dm_tau2`: |d|=0.3705, q=0.7175
- priority `0` / `wrapper` / `Control_vs_Parkinson` / `auditory_response` / `return_probability_tau2`: |d|=0.3606, q=0.7175
- priority `0` / `wrapper` / `Control_vs_Parkinson` / `auditory_all` / `return_probability_tau2`: |d|=0.3327, q=0.7175
- priority `0` / `wrapper` / `Control_vs_Parkinson` / `auditory_response` / `hysteresis_area_md`: |d|=0.2731, q=0.7175
- priority `0` / `wrapper` / `Control_vs_Parkinson` / `auditory_response` / `coupling_dm_tau2`: |d|=0.4099, q=0.7208
- priority `0` / `wrapper` / `Control_vs_Parkinson` / `auditory_response` / `entropy_rate`: |d|=0.3336, q=0.7268
- priority `0` / `wrapper` / `Control_vs_Parkinson` / `auditory_arrowcue` / `coupling_md_tau2`: |d|=0.2788, q=0.7268
- priority `0` / `wrapper` / `Control_vs_Parkinson` / `auditory_all` / `hysteresis_area_mean`: |d|=0.407, q=0.7419
- priority `0` / `wrapper` / `Control_vs_Parkinson` / `auditory_arrowcue` / `return_probability_tau2`: |d|=0.37, q=0.7419
