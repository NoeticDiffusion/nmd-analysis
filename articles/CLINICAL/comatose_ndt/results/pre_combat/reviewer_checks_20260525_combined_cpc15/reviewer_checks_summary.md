# Reviewer Checks Summary

- primary time bin: `0_12h`
- total subjects with analyzable `0_12h` summaries in local subject index: `301`
- CPC breakdown in local subject index: `{1: 141, 2: 10, 3: 7, 4: 3, 5: 140}`
- exploratory reachability selection pool size (patient-level `reachability_cones` median summaries): `60`

## Selected metrics with BH-FDR

- `tube_d_eff_median`: Cohen's `d = 0.513`, Mann-Whitney `p = 1.85e-05`, BH-FDR `q = 0.000139`
- `persistence_log_eig_var_median`: Cohen's `d = 0.123`, Mann-Whitney `p = 3.46e-05`, BH-FDR `q = 0.00016`
- `persistence_kappa_median`: Cohen's `d = 0.119`, Mann-Whitney `p = 0.0196`, BH-FDR `q = 0.0512`
- `tube_a_operator_norm_median`: Cohen's `d = -0.064`, Mann-Whitney `p = 0.0838`, BH-FDR `q = 0.132`
- `tube_capture_gate_median`: Cohen's `d = -0.142`, Mann-Whitney `p = 0.0862`, BH-FDR `q = 0.133`

## Inter-metric correlations (Spearman rho)

- `tube_d_eff_median`: `persistence_kappa_median`=-0.126, `persistence_log_eig_var_median`=0.065, `tube_a_operator_norm_median`=0.380, `tube_capture_gate_median`=0.371
- `persistence_kappa_median`: `tube_d_eff_median`=-0.126, `persistence_log_eig_var_median`=0.930, `tube_a_operator_norm_median`=-0.875, `tube_capture_gate_median`=-0.843
- `persistence_log_eig_var_median`: `tube_d_eff_median`=0.065, `persistence_kappa_median`=0.930, `tube_a_operator_norm_median`=-0.774, `tube_capture_gate_median`=-0.769
- `tube_a_operator_norm_median`: `tube_d_eff_median`=0.380, `persistence_kappa_median`=-0.875, `persistence_log_eig_var_median`=-0.774, `tube_capture_gate_median`=0.942
- `tube_capture_gate_median`: `tube_d_eff_median`=0.371, `persistence_kappa_median`=-0.843, `persistence_log_eig_var_median`=-0.769, `tube_a_operator_norm_median`=0.942

## Shockable-only subgroup

- subgroup counts: `1` = 99, `5` = 69
- `tube_d_eff_median`: medians `2.267` vs `1.980`, Cohen's `d = 0.754`, Mann-Whitney `p = 2.89e-06`
- `tube_capture_gate_median`: medians `1.359` vs `0.448`, Cohen's `d = 0.317`, Mann-Whitney `p = 0.235`
- `persistence_log_eig_var_median`: medians `2.104` vs `2.331`, Cohen's `d = 0.165`, Mann-Whitney `p = 0.258`
- `tube_a_operator_norm_median`: medians `6.906` vs `1.419`, Cohen's `d = 0.377`, Mann-Whitney `p = 0.307`
- `persistence_kappa_median`: medians `0.002` vs `0.142`, Cohen's `d = 0.126`, Mann-Whitney `p = 0.631`
