# Horizon sensitivity summary

- input_csv: `H:\SourceRepo2\NoeticDiffusion\articles\CLINICAL\comatose_ndt\results\mnps_summary_20260525_combined_cpc15_primary12h\patient_timebin_adapter_summaries.csv`
- time_bin: `0_12h`
- Good/Poor CPC filter: `1` vs `5`

## Key takeaways

- Effective dimensionality stays stable across `H=1..4`: Cohen's `d` ranges from `0.455` to `0.571`.
- The derived capture gate is directionally stable once it becomes informative: for `H=2..4`, Cohen's `d` ranges from `-0.195` to `-0.150`.
- `capture_gate @ H=1` is structurally degenerate in the current estimator because `q^(1) = 1`, so the gate becomes informative only from `H=2` onward.
- Raw horizon-resolved anisotropy (`cone_kappa_h`) remains directionally aligned but small in standardized magnitude (`d` roughly `-0.019` to `0.020`).
- Raw horizon-resolved log-eigenvalue spread (`cone_log_eig_var_h`) shows strong median separation but near-zero standardized `d`, consistent with the manuscript's more cautious treatment of persistence-related summaries.

## Compact effect table

| family | h1_d | h1_p | h1_delta_median | h1_status | h2_d | h2_p | h2_delta_median | h2_status | h3_d | h3_p | h3_delta_median | h3_status | h4_d | h4_p | h4_delta_median | h4_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| effective_dimensionality | 0.455 | 0.000141 | 0.207 | ok | 0.493 | 3.73e-05 | 0.215 | ok | 0.531 | 1.18e-05 | 0.167 | ok | 0.571 | 3.06e-06 | 0.192 | ok |
| anisotropy | -0.0193 | 0.122 | 233 | ok | 0.0205 | 0.113 | 252 | ok | 0.00618 | 0.106 | 269 | ok | 0.00404 | 0.0805 | 243 | ok |
| log_eig_var | -0.00221 | 0.125 | 0.569 | ok | -0.0173 | 0.0833 | 0.4 | ok | -0.0325 | 0.0585 | 0.382 | ok | -0.0499 | 0.0436 | 0.322 | ok |
| capture_gate |  | 1 | 0 | degenerate_constant | -0.195 | 0.0666 | -0.197 | ok | -0.169 | 0.076 | -0.238 | ok | -0.15 | 0.0865 | -0.267 | ok |

## Detailed rows

| family | horizon | metric | good_median | poor_median | delta_median_good_minus_poor | cohens_d | mannwhitney_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| effective_dimensionality | 1 | cone_d_eff_h1_median | 2.32 | 2.11 | 0.207 | 0.455 | 0.000141 | ok |
| effective_dimensionality | 2 | cone_d_eff_h2_median | 2.26 | 2.05 | 0.215 | 0.493 | 3.73e-05 | ok |
| effective_dimensionality | 3 | cone_d_eff_h3_median | 2.16 | 2 | 0.167 | 0.531 | 1.18e-05 | ok |
| effective_dimensionality | 4 | cone_d_eff_h4_median | 2.08 | 1.89 | 0.192 | 0.571 | 3.06e-06 | ok |
| anisotropy | 1 | cone_kappa_h1_median | 608 | 375 | 233 | -0.0193 | 0.122 | ok |
| anisotropy | 2 | cone_kappa_h2_median | 847 | 595 | 252 | 0.0205 | 0.113 | ok |
| anisotropy | 3 | cone_kappa_h3_median | 1.23e+03 | 960 | 269 | 0.00618 | 0.106 | ok |
| anisotropy | 4 | cone_kappa_h4_median | 1.82e+03 | 1.58e+03 | 243 | 0.00404 | 0.0805 | ok |
| log_eig_var | 1 | cone_log_eig_var_h1_median | 4.18 | 3.61 | 0.569 | -0.00221 | 0.125 | ok |
| log_eig_var | 2 | cone_log_eig_var_h2_median | 4.47 | 4.07 | 0.4 | -0.0173 | 0.0833 | ok |
| log_eig_var | 3 | cone_log_eig_var_h3_median | 4.86 | 4.48 | 0.382 | -0.0325 | 0.0585 | ok |
| log_eig_var | 4 | cone_log_eig_var_h4_median | 5.19 | 4.86 | 0.322 | -0.0499 | 0.0436 | ok |
| capture_gate | 1 | capture_gate_h1_median | 0 | 0 | 0 |  | 1 | degenerate_constant |
| capture_gate | 2 | capture_gate_h2_median | 0.307 | 0.505 | -0.197 | -0.195 | 0.0666 | ok |
| capture_gate | 3 | capture_gate_h3_median | 0.426 | 0.664 | -0.238 | -0.169 | 0.076 | ok |
| capture_gate | 4 | capture_gate_h4_median | 0.493 | 0.76 | -0.267 | -0.15 | 0.0865 | ok |

