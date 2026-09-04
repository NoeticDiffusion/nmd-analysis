# Horizon sensitivity summary

- input_csv: `J:\repos\NoeticDiffusion\articles\CLINICAL\comatose_ndt\results\mnps_summary_20260602_combined_combat_corrected_primary12h_cpc15\patient_timebin_adapter_summaries.csv`
- time_bin: `0_12h`
- Good/Poor CPC filter: `1` vs `5`

## Key takeaways

- Effective dimensionality stays stable across `H=1..4`: Cohen's `d` ranges from `0.580` to `0.636`.
- The derived capture gate is directionally stable once it becomes informative: for `H=2..4`, Cohen's `d` ranges from `-0.431` to `-0.364`.
- `capture_gate @ H=1` is structurally degenerate in the current estimator because `q^(1) = 1`, so the gate becomes informative only from `H=2` onward.
- Raw horizon-resolved anisotropy (`cone_kappa_h`) remains directionally aligned but small in standardized magnitude (`d` roughly `-0.357` to `-0.123`).
- Raw horizon-resolved log-eigenvalue spread (`cone_log_eig_var_h`) shows strong median separation but near-zero standardized `d`, consistent with the manuscript's more cautious treatment of persistence-related summaries.

## Compact effect table

| family | h1_d | h1_p | h1_delta_median | h1_status | h2_d | h2_p | h2_delta_median | h2_status | h3_d | h3_p | h3_delta_median | h3_status | h4_d | h4_p | h4_delta_median | h4_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| effective_dimensionality | 0.58 | 2.3e-06 | 0.383 | ok | 0.636 | 1.02e-06 | 0.437 | ok | 0.634 | 1.38e-06 | 0.461 | ok | 0.625 | 2.3e-06 | 0.436 | ok |
| anisotropy | -0.357 | 0.0263 | -1.73e+05 | ok | -0.182 | 0.00739 | -4.8e+05 | ok | -0.131 | 0.00479 | -7.78e+05 | ok | -0.123 | 0.00474 | -1.32e+06 | ok |
| log_eig_var | 0.0446 | 0.877 | -0.429 | ok | 0.0183 | 0.757 | -0.41 | ok | -0.00669 | 0.69 | -0.451 | ok | -0.0344 | 0.591 | -0.461 | ok |
| capture_gate |  | 1 | 0 | degenerate_constant | -0.431 | 0.00763 | -0.169 | ok | -0.395 | 0.0111 | -0.227 | ok | -0.364 | 0.0149 | -0.241 | ok |

## Detailed rows

| family | horizon | metric | good_median | poor_median | delta_median_good_minus_poor | cohens_d | mannwhitney_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| effective_dimensionality | 1 | cone_d_eff_h1_median | 3.21 | 2.83 | 0.383 | 0.58 | 2.3e-06 | ok |
| effective_dimensionality | 2 | cone_d_eff_h2_median | 3.05 | 2.62 | 0.437 | 0.636 | 1.02e-06 | ok |
| effective_dimensionality | 3 | cone_d_eff_h3_median | 2.81 | 2.35 | 0.461 | 0.634 | 1.38e-06 | ok |
| effective_dimensionality | 4 | cone_d_eff_h4_median | 2.57 | 2.14 | 0.436 | 0.625 | 2.3e-06 | ok |
| anisotropy | 1 | cone_kappa_h1_median | 1.48e+06 | 1.65e+06 | -1.73e+05 | -0.357 | 0.0263 | ok |
| anisotropy | 2 | cone_kappa_h2_median | 2.49e+06 | 2.97e+06 | -4.8e+05 | -0.182 | 0.00739 | ok |
| anisotropy | 3 | cone_kappa_h3_median | 3.57e+06 | 4.35e+06 | -7.78e+05 | -0.131 | 0.00479 | ok |
| anisotropy | 4 | cone_kappa_h4_median | 4.77e+06 | 6.09e+06 | -1.32e+06 | -0.123 | 0.00474 | ok |
| log_eig_var | 1 | cone_log_eig_var_h1_median | 17.1 | 17.5 | -0.429 | 0.0446 | 0.877 | ok |
| log_eig_var | 2 | cone_log_eig_var_h2_median | 18.4 | 18.8 | -0.41 | 0.0183 | 0.757 | ok |
| log_eig_var | 3 | cone_log_eig_var_h3_median | 19 | 19.5 | -0.451 | -0.00669 | 0.69 | ok |
| log_eig_var | 4 | cone_log_eig_var_h4_median | 19.6 | 20.1 | -0.461 | -0.0344 | 0.591 | ok |
| capture_gate | 1 | capture_gate_h1_median | 0 | 0 | 0 |  | 1 | degenerate_constant |
| capture_gate | 2 | capture_gate_h2_median | 0.835 | 1 | -0.169 | -0.431 | 0.00763 | ok |
| capture_gate | 3 | capture_gate_h3_median | 1.17 | 1.39 | -0.227 | -0.395 | 0.0111 | ok |
| capture_gate | 4 | capture_gate_h4_median | 1.35 | 1.59 | -0.241 | -0.364 | 0.0149 | ok |

