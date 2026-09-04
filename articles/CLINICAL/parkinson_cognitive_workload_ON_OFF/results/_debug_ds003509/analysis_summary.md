# Simon conflict Parkinson cognitive workload summary

This run analyzes `ds003509` with a mixed-contract policy: `cohort_anchored` is primary for disease-state contrasts against controls, while `subject_anchored` remains primary for the paired medication contrast.

## Standard ndt-analysis layer

### Parkinson_OFF_vs_ON (subject_anchored)

- `global_mnps_3d / m_median`: d=0.5154, p=0.007996, q=0.07196
- `adaptive_collapse / q_ratio_h4`: d=-0.3694, p=0.06047, q=0.08396
- `adaptive_collapse / capture_gate`: d=0.3535, p=0.07396, q=0.08396
- `adaptive_collapse / a_operator_norm`: d=0.3345, p=0.08396, q=0.08396
- `regional_mnps_jacobian_3d / temporal / mdr_mean`: d=0.4105, p=0.002499, q=0.08862
- `regional_mnps_jacobian_3d / temporal / spectral_radius_median`: d=0.5935, p=0.002999, q=0.08862

### Control_vs_Parkinson_OFF (cohort_anchored)

- `regional_9d / parietal_occipital / d_s_mean`: d=1.166, p=0.0004998, q=0.01349
- `regional_9d / parietal_occipital / d_n_std`: d=-1.155, p=0.0004998, q=0.01349
- `regional_9d / parietal_occipital / d_s_median`: d=1.13, p=0.0004998, q=0.01349
- `regional_9d / central / d_n_std`: d=-1.129, p=0.0004998, q=0.01349
- `regional_9d / central / e_m_mean`: d=-0.8667, p=0.0009995, q=0.02076
- `regional_9d / temporal / d_s_mean`: d=0.8714, p=0.001499, q=0.02076

### Control_vs_Parkinson_ON (cohort_anchored)

- `regional_9d / frontal / e_m_mean`: d=-0.9908, p=0.0004998, q=0.01349
- `global_mnps_9d / e_m_median`: d=-0.9848, p=0.0004998, q=0.01349
- `regional_9d / parietal_occipital / e_m_median`: d=-0.9848, p=0.0004998, q=0.01349
- `regional_9d / temporal / e_m_median`: d=-0.9848, p=0.0004998, q=0.01349
- `regional_9d / parietal_occipital / d_s_mean`: d=0.9818, p=0.0004998, q=0.01349
- `regional_9d / temporal / e_m_mean`: d=-0.9908, p=0.0009995, q=0.01472

## Event-locked trajectory layer

No merged wrapper event contrasts were produced.

## Caveats

- Wrapper metrics use task-specific `event_windows/*` segmentation and remain article-local summaries on top of the repository standard exports.
- Control subjects do not have medication pairing, so disease-state and pharmacology questions are answered with different optimal coordinate contracts.
