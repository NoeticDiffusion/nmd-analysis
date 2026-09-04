# Parkinson auditory recall summary

This run uses the fixed `ds004574` subject-anchored bundle and treats `raw_*` labels as the event surface while leaving `labels/stage` out of the inferential story.

## Standard ndt-analysis layer

- `global_mnps_3d` / `m_median`: d=-0.6018, p=0.001499, q=0.01349
- `adaptive_collapse` / `q_ratio_h4`: d=0.5182, p=0.003998, q=0.01999
- `reachability_cones` / `tube_q_ratio_h4_mean`: d=0.557, p=0.0009995, q=0.03078
- `reachability_cones` / `q_ratio_h2_median`: d=0.5523, p=0.001499, q=0.03078
- `reachability_cones` / `cone_q_ratio_h2_median`: d=0.5523, p=0.001999, q=0.03078
- `reachability_cones` / `cone_q_ratio_h3_median`: d=0.5388, p=0.001999, q=0.03078
- `reachability_cones` / `q_ratio_h4_median`: d=0.5182, p=0.001999, q=0.03078
- `reachability_cones` / `tube_q_ratio_h4_median`: d=0.5182, p=0.003998, q=0.04329
- `reachability_cones` / `median_min_eig_over_median_eig`: d=-0.4726, p=0.003998, q=0.04329
- `reachability_cones` / `q_ratio_h3_median`: d=0.5388, p=0.004498, q=0.04329

## Event-locked wrapper layer

### All_Auditory_vs_OtherMean

- `global_event_locked_trajectory_3d` / `other_mean__vs__auditory_all` / `transition_sparsity`: d=3.376, p=1.034e-25, q=4.051e-25
- `global_event_locked_trajectory_3d` / `other_mean__vs__auditory_all` / `path_length`: d=-1.893, p=1.044e-25, q=4.051e-25
- `global_event_locked_trajectory_3d` / `other_mean__vs__auditory_all` / `tortuosity`: d=-1.115, p=1.044e-25, q=4.051e-25
- `global_event_locked_trajectory_3d` / `other_mean__vs__auditory_all` / `entropy_rate`: d=-2.993, p=1.066e-25, q=4.051e-25
- `global_event_locked_trajectory_3d` / `other_mean__vs__auditory_all` / `peak_displacement`: d=-1.853, p=1.066e-25, q=4.051e-25
- `global_event_locked_trajectory_9d` / `other_mean__vs__auditory_all` / `transition_sparsity`: d=2.661, p=1.028e-25, q=4.136e-25
- `global_event_locked_trajectory_9d` / `other_mean__vs__auditory_all` / `entropy_rate`: d=-2.941, p=1.044e-25, q=4.136e-25
- `global_event_locked_trajectory_9d` / `other_mean__vs__auditory_all` / `path_length`: d=-1.895, p=1.044e-25, q=4.136e-25

### All_Auditory_vs_Standard

- `global_event_locked_trajectory_9d` / `standard_all__vs__auditory_all` / `transition_sparsity`: d=2.659, p=1.027e-25, q=3.969e-25
- `global_event_locked_trajectory_3d` / `standard_all__vs__auditory_all` / `transition_sparsity`: d=3.461, p=1.034e-25, q=3.969e-25
- `global_event_locked_trajectory_3d` / `standard_all__vs__auditory_all` / `entropy_rate`: d=-4.012, p=1.044e-25, q=3.969e-25
- `global_event_locked_trajectory_9d` / `standard_all__vs__auditory_all` / `entropy_rate`: d=-3.913, p=1.044e-25, q=3.969e-25
- `global_event_locked_trajectory_9d` / `standard_all__vs__auditory_all` / `peak_displacement`: d=-2.261, p=1.044e-25, q=3.969e-25
- `global_event_locked_trajectory_3d` / `standard_all__vs__auditory_all` / `peak_displacement`: d=-2.019, p=1.044e-25, q=3.969e-25
- `global_event_locked_trajectory_9d` / `standard_all__vs__auditory_all` / `path_length`: d=-1.901, p=1.044e-25, q=3.969e-25
- `global_event_locked_trajectory_3d` / `standard_all__vs__auditory_all` / `path_length`: d=-1.898, p=1.044e-25, q=3.969e-25

### Control_vs_Parkinson

- `global_event_locked_trajectory_9d` / `visual_response` / `tortuosity`: d=0.4726, p=0.00571, q=0.9007
- `global_event_locked_trajectory_9d` / `visual_all` / `tortuosity`: d=0.4651, p=0.00632, q=0.9007
- `global_event_locked_trajectory_9d` / `standard_precue` / `entropy_rate`: d=0.5024, p=0.01047, q=0.9694
- `global_event_locked_trajectory_9d` / `auditory_precue` / `hysteresis_area_md`: d=-0.4164, p=0.01374, q=0.9694
- `global_event_locked_trajectory_9d` / `standard_arrowcue` / `entropy_rate`: d=0.3947, p=0.02256, q=0.9694
- `global_event_locked_trajectory_9d` / `auditory_arrowcue` / `hysteresis_area_md`: d=-0.3975, p=0.02357, q=0.9694
- `global_event_locked_trajectory_9d` / `auditory_all` / `hysteresis_area_md`: d=-0.3712, p=0.02382, q=0.9694
- `global_event_locked_trajectory_9d` / `standard_all` / `entropy_rate`: d=0.3468, p=0.0402, q=0.9694

## Candidate article metrics

- `wrapper` / `All_Auditory_vs_Standard_arrowcue` / `global_event_locked_trajectory_9d` / `standard_arrowcue__vs__auditory_arrowcue` / `entropy_rate`: |d|=4.731, q=3.969e-25
- `wrapper` / `All_Auditory_vs_Standard_arrowcue` / `global_event_locked_trajectory_3d` / `standard_arrowcue__vs__auditory_arrowcue` / `transition_sparsity`: |d|=4.211, q=3.969e-25
- `wrapper` / `All_Auditory_vs_Standard_arrowcue` / `global_event_locked_trajectory_3d` / `standard_arrowcue__vs__auditory_arrowcue` / `entropy_rate`: |d|=4.074, q=3.969e-25
- `wrapper` / `All_Auditory_vs_Standard` / `global_event_locked_trajectory_3d` / `standard_all__vs__auditory_all` / `entropy_rate`: |d|=4.012, q=3.969e-25
- `wrapper` / `All_Auditory_vs_Standard_precue` / `global_event_locked_trajectory_3d` / `standard_precue__vs__auditory_precue` / `transition_sparsity`: |d|=3.962, q=3.969e-25
- `wrapper` / `All_Auditory_vs_Standard` / `global_event_locked_trajectory_9d` / `standard_all__vs__auditory_all` / `entropy_rate`: |d|=3.913, q=3.969e-25
- `wrapper` / `All_Auditory_vs_Standard_precue` / `global_event_locked_trajectory_3d` / `standard_precue__vs__auditory_precue` / `entropy_rate`: |d|=3.911, q=3.969e-25
- `wrapper` / `All_Auditory_vs_Standard` / `global_event_locked_trajectory_3d` / `standard_all__vs__auditory_all` / `transition_sparsity`: |d|=3.461, q=3.969e-25
- `wrapper` / `All_Auditory_vs_Standard_arrowcue` / `global_event_locked_trajectory_9d` / `standard_arrowcue__vs__auditory_arrowcue` / `transition_sparsity`: |d|=3.384, q=3.969e-25
- `wrapper` / `All_Auditory_vs_Standard_response` / `global_event_locked_trajectory_9d` / `standard_response__vs__auditory_response` / `entropy_rate`: |d|=3.263, q=3.969e-25
- `wrapper` / `All_Auditory_vs_Standard_response` / `global_event_locked_trajectory_3d` / `standard_response__vs__auditory_response` / `entropy_rate`: |d|=3.24, q=3.969e-25
- `wrapper` / `All_Auditory_vs_Standard_response` / `global_event_locked_trajectory_3d` / `standard_response__vs__auditory_response` / `transition_sparsity`: |d|=2.817, q=3.969e-25

## Caveats

- Event subtype labels come from behavior-enriched `raw_*` provenance rather than a stage-coded trial map.
- `raw_nan_onset_sec` is excluded from the article-local wrapper by construction and is not treated as a meaningful event.
- The bundle exposes no regional outputs, no cohort-anchor layer, and no ComBat normalization.
