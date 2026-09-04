# Reviewer Checks Summary

- primary time bin: `0_12h`
- total subjects with analyzable `0_12h` summaries in local subject index: `301`
- CPC breakdown in local subject index: `{1: 141, 2: 10, 3: 7, 4: 3, 5: 140}`
- exploratory reachability selection pool size (patient-level `reachability_cones` median summaries): `60`

## Selected metrics with BH-FDR

- `tube_d_eff_median`: Cohen's `d = 0.838`, Mann-Whitney `p = 9.24e-06`, BH-FDR `q = 4.87e-05`
- `persistence_log_eig_var_median`: Cohen's `d = 0.736`, Mann-Whitney `p = 5.3e-05`, BH-FDR `q = 0.000114`
- `tube_capture_gate_median`: Cohen's `d = -0.558`, Mann-Whitney `p = 0.00804`, BH-FDR `q = 0.0142`
- `tube_a_operator_norm_median`: Cohen's `d = -0.124`, Mann-Whitney `p = 0.735`, BH-FDR `q = 0.886`
- `persistence_kappa_median`: Cohen's `d = 0.147`, Mann-Whitney `p = 0.806`, BH-FDR `q = 0.913`

## Inter-metric correlations (Spearman rho)

- `tube_d_eff_median`: `persistence_kappa_median`=0.209, `persistence_log_eig_var_median`=0.801, `tube_a_operator_norm_median`=0.198, `tube_capture_gate_median`=-0.385
- `persistence_kappa_median`: `tube_d_eff_median`=0.209, `persistence_log_eig_var_median`=0.354, `tube_a_operator_norm_median`=-0.236, `tube_capture_gate_median`=-0.212
- `persistence_log_eig_var_median`: `tube_d_eff_median`=0.801, `persistence_kappa_median`=0.354, `tube_a_operator_norm_median`=-0.033, `tube_capture_gate_median`=-0.521
- `tube_a_operator_norm_median`: `tube_d_eff_median`=0.198, `persistence_kappa_median`=-0.236, `persistence_log_eig_var_median`=-0.033, `tube_capture_gate_median`=0.705
- `tube_capture_gate_median`: `tube_d_eff_median`=-0.385, `persistence_kappa_median`=-0.212, `persistence_log_eig_var_median`=-0.521, `tube_a_operator_norm_median`=0.705

## Shockable-only subgroup

- subgroup counts: `1` = 52, `5` = 26
- `tube_d_eff_median`: medians `2.963` vs `2.448`, Cohen's `d = 0.690`, Mann-Whitney `p = 0.00522`
- `persistence_log_eig_var_median`: medians `1.596` vs `1.118`, Cohen's `d = 0.482`, Mann-Whitney `p = 0.0424`
- `tube_capture_gate_median`: medians `1.773` vs `1.911`, Cohen's `d = -0.489`, Mann-Whitney `p = 0.108`
- `persistence_kappa_median`: medians `0.000` vs `0.000`, Cohen's `d = 0.198`, Mann-Whitney `p = 0.699`
- `tube_a_operator_norm_median`: medians `15.543` vs `14.820`, Cohen's `d = -0.181`, Mann-Whitney `p = 0.787`
