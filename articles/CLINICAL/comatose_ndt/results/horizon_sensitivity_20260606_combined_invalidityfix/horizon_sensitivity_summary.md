# Horizon sensitivity summary

- input_csv: `J:\repos\NoeticDiffusion\articles\CLINICAL\comatose_ndt\results\mnps_summary_20260606_combined_invalidityfix_primary12h_cpc15\patient_timebin_adapter_summaries.csv`
- time_bin: `0_12h`
- Good/Poor CPC filter: `1` vs `5`

## Key takeaways

- Effective dimensionality stays stable across `H=1..4`: Cohen's `d` ranges from `0.789` to `0.887`.
- The derived capture gate is directionally stable once it becomes informative: for `H=2..4`, Cohen's `d` ranges from `-0.610` to `-0.581`.
- `capture_gate @ H=1` is structurally degenerate in the current estimator because `q^(1) = 1`, so the gate becomes informative only from `H=2` onward.
- Raw horizon-resolved anisotropy (`cone_kappa_h`) remains directionally aligned but small in standardized magnitude (`d` roughly `-0.294` to `-0.231`).
- Raw horizon-resolved log-eigenvalue spread (`cone_log_eig_var_h`) shows strong median separation but near-zero standardized `d`, consistent with the manuscript's more cautious treatment of persistence-related summaries.

## Compact effect table

| family | h1_d | h1_p | h1_delta_median | h1_status | h2_d | h2_p | h2_delta_median | h2_status | h3_d | h3_p | h3_delta_median | h3_status | h4_d | h4_p | h4_delta_median | h4_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| effective_dimensionality | 0.887 | 4.37e-06 | 0.49 | ok | 0.842 | 8.84e-06 | 0.573 | ok | 0.805 | 1.65e-05 | 0.535 | ok | 0.789 | 1.87e-05 | 0.525 | ok |
| anisotropy | -0.231 | 0.629 | -6.13e+03 | ok | -0.28 | 0.799 | -1.86e+04 | ok | -0.287 | 0.983 | -3.77e+04 | ok | -0.294 | 0.799 | -5.88e+04 | ok |
| log_eig_var | 0.176 | 0.33 | -0.21 | ok | 0.136 | 0.527 | -0.693 | ok | 0.0877 | 0.738 | -1.07 | ok | 0.0357 | 0.916 | -1.21 | ok |
| capture_gate |  | 1 | 0 | degenerate_constant | -0.61 | 0.0022 | -0.137 | ok | -0.599 | 0.0037 | -0.148 | ok | -0.581 | 0.00519 | -0.168 | ok |

## Detailed rows

| family | horizon | metric | good_median | poor_median | delta_median_good_minus_poor | cohens_d | mannwhitney_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| effective_dimensionality | 1 | cone_d_eff_h1_median | 3.38 | 2.89 | 0.49 | 0.887 | 4.37e-06 | ok |
| effective_dimensionality | 2 | cone_d_eff_h2_median | 3.17 | 2.59 | 0.573 | 0.842 | 8.84e-06 | ok |
| effective_dimensionality | 3 | cone_d_eff_h3_median | 2.85 | 2.32 | 0.535 | 0.805 | 1.65e-05 | ok |
| effective_dimensionality | 4 | cone_d_eff_h4_median | 2.58 | 2.05 | 0.525 | 0.789 | 1.87e-05 | ok |
| anisotropy | 1 | cone_kappa_h1_median | 5e+03 | 1.11e+04 | -6.13e+03 | -0.231 | 0.629 | ok |
| anisotropy | 2 | cone_kappa_h2_median | 6.14e+03 | 2.48e+04 | -1.86e+04 | -0.28 | 0.799 | ok |
| anisotropy | 3 | cone_kappa_h3_median | 1.16e+04 | 4.93e+04 | -3.77e+04 | -0.287 | 0.983 | ok |
| anisotropy | 4 | cone_kappa_h4_median | 1.98e+04 | 7.86e+04 | -5.88e+04 | -0.294 | 0.799 | ok |
| log_eig_var | 1 | cone_log_eig_var_h1_median | 6.55 | 6.76 | -0.21 | 0.176 | 0.33 | ok |
| log_eig_var | 2 | cone_log_eig_var_h2_median | 6.9 | 7.59 | -0.693 | 0.136 | 0.527 | ok |
| log_eig_var | 3 | cone_log_eig_var_h3_median | 7.47 | 8.54 | -1.07 | 0.0877 | 0.738 | ok |
| log_eig_var | 4 | cone_log_eig_var_h4_median | 8.09 | 9.3 | -1.21 | 0.0357 | 0.916 | ok |
| capture_gate | 1 | capture_gate_h1_median | 0 | 0 | 0 |  | 1 | degenerate_constant |
| capture_gate | 2 | capture_gate_h2_median | 1.15 | 1.29 | -0.137 | -0.61 | 0.0022 | ok |
| capture_gate | 3 | capture_gate_h3_median | 1.62 | 1.77 | -0.148 | -0.599 | 0.0037 | ok |
| capture_gate | 4 | capture_gate_h4_median | 1.87 | 2.04 | -0.168 | -0.581 | 0.00519 | ok |

