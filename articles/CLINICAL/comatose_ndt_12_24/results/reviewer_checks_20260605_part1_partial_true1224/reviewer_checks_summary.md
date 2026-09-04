# Reviewer Checks Summary

- primary time bin: `12_24h`
- total subjects with analyzable `12_24h` summaries: `38`
- CPC breakdown in analyzable `12_24h` subset: `{1: 25, 5: 13}`
- exploratory reachability selection pool size (patient-level `reachability_cones` median summaries): `60`

## Selected metrics with BH-FDR

- `tube_a_operator_norm_median`: Cohen's `d = 0.353`, Mann-Whitney `p = 0.295`, BH-FDR `q = 0.771`
- `tube_d_eff_median`: Cohen's `d = 0.264`, Mann-Whitney `p = 0.479`, BH-FDR `q = 0.798`
- `persistence_log_eig_var_median`: Cohen's `d = 0.221`, Mann-Whitney `p = 0.712`, BH-FDR `q = 0.89`
- `persistence_kappa_median`: Cohen's `d = -0.228`, Mann-Whitney `p = 0.806`, BH-FDR `q = 0.922`
- `tube_capture_gate_median`: Cohen's `d = -0.016`, Mann-Whitney `p = 0.951`, BH-FDR `q = 1`

## Inter-metric correlations (Spearman rho)

- `tube_d_eff_median`: `persistence_kappa_median`=0.803, `persistence_log_eig_var_median`=0.889, `tube_a_operator_norm_median`=-0.005, `tube_capture_gate_median`=-0.720
- `persistence_kappa_median`: `tube_d_eff_median`=0.803, `persistence_log_eig_var_median`=0.897, `tube_a_operator_norm_median`=-0.215, `tube_capture_gate_median`=-0.712
- `persistence_log_eig_var_median`: `tube_d_eff_median`=0.889, `persistence_kappa_median`=0.897, `tube_a_operator_norm_median`=0.018, `tube_capture_gate_median`=-0.717
- `tube_a_operator_norm_median`: `tube_d_eff_median`=-0.005, `persistence_kappa_median`=-0.215, `persistence_log_eig_var_median`=0.018, `tube_capture_gate_median`=0.334
- `tube_capture_gate_median`: `tube_d_eff_median`=-0.720, `persistence_kappa_median`=-0.712, `persistence_log_eig_var_median`=-0.717, `tube_a_operator_norm_median`=0.334

## Shockable-only subgroup

- subgroup counts: `1` = 17, `5` = 4
- `tube_a_operator_norm_median`: medians `10.795` vs `9.930`, Cohen's `d = 0.594`, Mann-Whitney `p = 0.317`
- `tube_capture_gate_median`: medians `1.718` vs `1.825`, Cohen's `d = -0.050`, Mann-Whitney `p = 0.763`
- `tube_d_eff_median`: medians `2.733` vs `2.663`, Cohen's `d = -0.076`, Mann-Whitney `p = 0.829`
- `persistence_kappa_median`: medians `0.000` vs `0.001`, Cohen's `d = -0.410`, Mann-Whitney `p = 0.897`
- `persistence_log_eig_var_median`: medians `1.564` vs `1.535`, Cohen's `d = 0.103`, Mann-Whitney `p = 0.897`
