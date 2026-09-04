# Reviewer Checks Summary

- primary time bin: `12_24h`
- total subjects with analyzable `12_24h` summaries: `97`
- CPC breakdown in analyzable `12_24h` subset: `{1: 47, 5: 50}`
- exploratory reachability selection pool size (patient-level `reachability_cones` median summaries): `60`

## Selected metrics with BH-FDR

- `persistence_kappa_median`: Cohen's `d = -0.686`, Mann-Whitney `p = 0.00752`, BH-FDR `q = 0.0376`
- `tube_a_operator_norm_median`: Cohen's `d = 0.571`, Mann-Whitney `p = 0.00868`, BH-FDR `q = 0.0393`
- `tube_capture_gate_median`: Cohen's `d = 0.584`, Mann-Whitney `p = 0.00977`, BH-FDR `q = 0.0393`
- `persistence_log_eig_var_median`: Cohen's `d = -0.353`, Mann-Whitney `p = 0.0411`, BH-FDR `q = 0.137`
- `tube_d_eff_median`: Cohen's `d = -0.046`, Mann-Whitney `p = 0.642`, BH-FDR `q = 0.77`

## Inter-metric correlations (Spearman rho)

- `tube_d_eff_median`: `persistence_kappa_median`=0.715, `persistence_log_eig_var_median`=0.791, `tube_a_operator_norm_median`=-0.041, `tube_capture_gate_median`=-0.563
- `persistence_kappa_median`: `tube_d_eff_median`=0.715, `persistence_log_eig_var_median`=0.852, `tube_a_operator_norm_median`=-0.481, `tube_capture_gate_median`=-0.691
- `persistence_log_eig_var_median`: `tube_d_eff_median`=0.791, `persistence_kappa_median`=0.852, `tube_a_operator_norm_median`=-0.184, `tube_capture_gate_median`=-0.679
- `tube_a_operator_norm_median`: `tube_d_eff_median`=-0.041, `persistence_kappa_median`=-0.481, `persistence_log_eig_var_median`=-0.184, `tube_capture_gate_median`=0.478
- `tube_capture_gate_median`: `tube_d_eff_median`=-0.563, `persistence_kappa_median`=-0.691, `persistence_log_eig_var_median`=-0.679, `tube_a_operator_norm_median`=0.478

## Shockable-only subgroup

- subgroup counts: `1` = 33, `5` = 18
- `tube_a_operator_norm_median`: medians `11.693` vs `9.779`, Cohen's `d = 0.974`, Mann-Whitney `p = 0.00167`
- `persistence_kappa_median`: medians `0.001` vs `0.001`, Cohen's `d = -1.034`, Mann-Whitney `p = 0.00365`
- `persistence_log_eig_var_median`: medians `1.682` vs `2.054`, Cohen's `d = -0.537`, Mann-Whitney `p = 0.0625`
- `tube_capture_gate_median`: medians `1.702` vs `1.609`, Cohen's `d = 0.630`, Mann-Whitney `p = 0.0683`
- `tube_d_eff_median`: medians `3.001` vs `3.110`, Cohen's `d = -0.375`, Mann-Whitney `p = 0.283`
