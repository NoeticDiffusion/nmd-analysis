# Reviewer Checks Summary

- primary time bin: `0_12h`
- total subjects with analyzable `0_12h` summaries in local subject index: `298`
- CPC breakdown in local subject index: `{1: 140, 2: 10, 3: 7, 4: 3, 5: 138}`
- exploratory reachability selection pool size (patient-level `reachability_cones` median summaries): `60`

## Selected metrics with BH-FDR

- `tube_d_eff_median`: Cohen's `d = 0.638`, Mann-Whitney `p = 1.02e-06`, BH-FDR `q = 1.23e-05`
- `persistence_log_eig_var_median`: Cohen's `d = 0.122`, Mann-Whitney `p = 2.39e-05`, BH-FDR `q = 5.3e-05`
- `persistence_kappa_median`: Cohen's `d = 0.127`, Mann-Whitney `p = 0.0145`, BH-FDR `q = 0.0249`
- `tube_capture_gate_median`: Cohen's `d = -0.348`, Mann-Whitney `p = 0.0183`, BH-FDR `q = 0.0305`
- `tube_a_operator_norm_median`: Cohen's `d = -0.129`, Mann-Whitney `p = 0.413`, BH-FDR `q = 0.486`

## Inter-metric correlations (Spearman rho)

- `tube_d_eff_median`: `persistence_kappa_median`=0.361, `persistence_log_eig_var_median`=0.737, `tube_a_operator_norm_median`=0.023, `tube_capture_gate_median`=-0.174
- `persistence_kappa_median`: `tube_d_eff_median`=0.361, `persistence_log_eig_var_median`=0.465, `tube_a_operator_norm_median`=0.283, `tube_capture_gate_median`=0.219
- `persistence_log_eig_var_median`: `tube_d_eff_median`=0.737, `persistence_kappa_median`=0.465, `tube_a_operator_norm_median`=-0.011, `tube_capture_gate_median`=-0.175
- `tube_a_operator_norm_median`: `tube_d_eff_median`=0.023, `persistence_kappa_median`=0.283, `persistence_log_eig_var_median`=-0.011, `tube_capture_gate_median`=0.933
- `tube_capture_gate_median`: `tube_d_eff_median`=-0.174, `persistence_kappa_median`=0.219, `persistence_log_eig_var_median`=-0.175, `tube_a_operator_norm_median`=0.933

## Shockable-only subgroup

- subgroup counts: `1` = 98, `5` = 67
- `tube_d_eff_median`: medians `2.912` vs `2.545`, Cohen's `d = 0.571`, Mann-Whitney `p = 0.00161`
- `persistence_kappa_median`: medians `0.000` vs `0.000`, Cohen's `d = 0.207`, Mann-Whitney `p = 0.0615`
- `persistence_log_eig_var_median`: medians `1.515` vs `1.190`, Cohen's `d = 0.269`, Mann-Whitney `p = 0.102`
- `tube_a_operator_norm_median`: medians `7.354` vs `7.529`, Cohen's `d = -0.029`, Mann-Whitney `p = 0.692`
- `tube_capture_gate_median`: medians `1.363` vs `1.376`, Cohen's `d = -0.113`, Mann-Whitney `p = 0.797`
