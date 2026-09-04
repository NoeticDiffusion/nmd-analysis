# Reinforcement learning Parkinson cognitive workload summary

This run analyzes `ds003506` with a mixed-contract policy: `cohort_anchored` is primary for disease-state contrasts against controls, while `subject_anchored` remains primary for the paired medication contrast.

## Standard ndt-analysis layer

### Parkinson_OFF_vs_ON (subject_anchored)

- `regional_3d / frontal / e_mean`: d=-0.5215, p=0.01049, q=0.2429
- `regional_3d / frontal / e_median`: d=-0.5108, p=0.01349, q=0.2429
- `eeg_classical_comparators / global / eeg_classical_peak_spectral_edge_95_delta_mean_median`: d=0.4574, p=0.02749, q=0.3309
- `eeg_classical_comparators / global / eeg_classical_relative_gamma_mad_sigma`: d=-0.4393, p=0.02749, q=0.3309
- `eeg_classical_comparators / global / eeg_classical_relative_delta_mad_sigma`: d=-0.4368, p=0.02949, q=0.3309
- `eeg_classical_comparators / global / eeg_classical_peak_spectral_edge_95_median`: d=-0.4384, p=0.03098, q=0.3309

### Control_vs_Parkinson_OFF (cohort_anchored)

- `eeg_classical_comparators / global / eeg_classical_relative_alpha_mean`: d=1.113, p=0.0004998, q=0.01599
- `eeg_classical_comparators / global / eeg_classical_relative_alpha_iqr`: d=0.9559, p=0.0004998, q=0.01599
- `eeg_classical_comparators / global / eeg_classical_relative_alpha_mad_sigma`: d=0.9384, p=0.0004998, q=0.01599
- `eeg_classical_comparators / global / eeg_classical_relative_alpha_median`: d=1.113, p=0.0009995, q=0.02399
- `regional_9d / frontal / d_s_mean`: d=1.064, p=0.0004998, q=0.02699
- `regional_9d / frontal / d_s_median`: d=0.9748, p=0.0004998, q=0.02699

### Control_vs_Parkinson_ON (cohort_anchored)

- `global_mnps_9d_block_jacobian / central / block_frobenius_mean`: d=-0.7136, p=0.003498, q=0.1259
- `adaptive_collapse / a_operator_norm`: d=0.5288, p=0.04348, q=0.1824
- `adaptive_collapse / capture_gate`: d=0.499, p=0.07296, q=0.1824
- `regional_9d / frontal / d_s_mean`: d=0.8218, p=0.002499, q=0.2159
- `regional_9d / frontal / d_s_median`: d=0.8141, p=0.006497, q=0.2159
- `regional_9d / central / e_m_mean`: d=-0.6424, p=0.01549, q=0.2159

## Event-locked trajectory layer

No merged wrapper event contrasts were produced.

## Caveats

- Wrapper metrics use task-specific `event_windows/*` segmentation and remain article-local summaries on top of the repository standard exports.
- Control subjects do not have medication pairing, so disease-state and pharmacology questions are answered with different optimal coordinate contracts.
