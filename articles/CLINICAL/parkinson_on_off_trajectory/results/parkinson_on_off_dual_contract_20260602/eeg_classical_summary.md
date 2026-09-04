# Classical EEG comparator summary

This article-facing wrapper re-runs only the `eeg_classical_comparators` block and then applies the same mixed-contract selection rule as the main manuscript.
For clinical readability, the article-facing `primary` table is restricted to median-valued comparator summaries, while the full contract-specific exports retain the wider metric inventory.

- `cohort_anchored` remains primary for `Control vs Parkinson OFF` and `Control vs Parkinson ON`.
- `subject_anchored` remains primary for `Parkinson OFF vs ON`.
- These rows are intended as clinically familiar comparator surfaces rather than replacement endpoints for the NDT/NMD layers.

## Parkinson_OFF_vs_ON (subject_anchored)

- `eeg_classical_relative_theta_median`: d=0.2855, p=0.1864, q=0.987
- `eeg_classical_relative_gamma_delta_mean_median`: d=0.2051, p=0.3318, q=0.987
- `eeg_classical_ratio_beta_alpha_median`: d=-0.1897, p=0.3418, q=0.987
- `eeg_classical_peak_alpha_frequency_delta_mean_median`: d=-0.1893, p=0.3633, q=0.987
- `eeg_classical_ratio_slowing_index_median`: d=-0.1828, p=0.3738, q=0.987
- `eeg_classical_ratio_delta_alpha_median`: d=-0.1842, p=0.4073, q=0.987
- `eeg_classical_ratio_slowing_index_delta_mean_median`: d=0.1803, p=0.4118, q=0.987
- `eeg_classical_ratio_delta_alpha_delta_mean_median`: d=-0.165, p=0.4208, q=0.987

## Control_vs_Parkinson_OFF (cohort_anchored)

- `eeg_classical_ratio_theta_alpha_median`: d=-0.4718, p=0.1009, q=0.4937
- `eeg_classical_complexity_permutation_entropy_median`: d=0.4491, p=0.1144, q=0.4937
- `eeg_classical_ratio_beta_alpha_delta_mean_median`: d=-0.4531, p=0.1194, q=0.4937
- `eeg_classical_complexity_hjorth_mobility_median`: d=0.4077, p=0.1569, q=0.4937
- `eeg_classical_relative_alpha_median`: d=0.3931, p=0.1719, q=0.4937
- `eeg_classical_relative_beta_median`: d=0.3754, p=0.1909, q=0.4937
- `eeg_classical_complexity_spectral_entropy_median`: d=0.3531, p=0.2059, q=0.4937
- `eeg_classical_complexity_hjorth_complexity_median`: d=-0.362, p=0.2094, q=0.4937

## Control_vs_Parkinson_ON (cohort_anchored)

- `eeg_classical_ratio_theta_alpha_median`: d=-0.6278, p=0.02799, q=0.2985
- `eeg_classical_ratio_slowing_index_median`: d=-0.6003, p=0.03548, q=0.3217
- `eeg_classical_relative_theta_delta_mean_median`: d=0.5694, p=0.05447, q=0.3217
- `eeg_classical_ratio_delta_alpha_median`: d=-0.5157, p=0.06047, q=0.3225
- `eeg_classical_complexity_hjorth_complexity_median`: d=-0.4101, p=0.1504, q=0.495
- `eeg_classical_ratio_beta_alpha_delta_mean_median`: d=-0.3927, p=0.1694, q=0.495
- `eeg_classical_relative_alpha_delta_mean_median`: d=0.3818, p=0.1794, q=0.495
- `eeg_classical_relative_alpha_median`: d=0.3741, p=0.1929, q=0.495

## Exported subject metrics (subject_anchored)

- rows: `7200`; metrics: `96`; subjects: `50`

## Exported subject metrics (cohort_anchored)

- rows: `7200`; metrics: `96`; subjects: `50`
