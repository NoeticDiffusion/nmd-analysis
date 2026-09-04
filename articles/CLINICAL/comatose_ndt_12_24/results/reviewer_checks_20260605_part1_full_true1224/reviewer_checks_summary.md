# Reviewer Checks Summary

- primary time bin: `12_24h`
- total subjects with analyzable `12_24h` summaries: `105`
- CPC breakdown in analyzable `12_24h` subset: `{1: 52, 5: 53}`
- exploratory reachability selection pool size (patient-level `reachability_cones` median summaries): `60`

## Selected metrics with BH-FDR

- `persistence_kappa_median`: Cohen's `d = -0.670`, Mann-Whitney `p = 0.00485`, BH-FDR `q = 0.0257`
- `persistence_log_eig_var_median`: Cohen's `d = -0.470`, Mann-Whitney `p = 0.00851`, BH-FDR `q = 0.0393`
- `tube_capture_gate_median`: Cohen's `d = 0.222`, Mann-Whitney `p = 0.0375`, BH-FDR `q = 0.127`
- `tube_a_operator_norm_median`: Cohen's `d = 0.241`, Mann-Whitney `p = 0.0976`, BH-FDR `q = 0.293`
- `tube_d_eff_median`: Cohen's `d = -0.201`, Mann-Whitney `p = 0.266`, BH-FDR `q = 0.389`

## Inter-metric correlations (Spearman rho)

- `tube_d_eff_median`: `persistence_kappa_median`=0.758, `persistence_log_eig_var_median`=0.828, `tube_a_operator_norm_median`=0.049, `tube_capture_gate_median`=-0.415
- `persistence_kappa_median`: `tube_d_eff_median`=0.758, `persistence_log_eig_var_median`=0.873, `tube_a_operator_norm_median`=-0.333, `tube_capture_gate_median`=-0.540
- `persistence_log_eig_var_median`: `tube_d_eff_median`=0.828, `persistence_kappa_median`=0.873, `tube_a_operator_norm_median`=-0.078, `tube_capture_gate_median`=-0.530
- `tube_a_operator_norm_median`: `tube_d_eff_median`=0.049, `persistence_kappa_median`=-0.333, `persistence_log_eig_var_median`=-0.078, `tube_capture_gate_median`=0.563
- `tube_capture_gate_median`: `tube_d_eff_median`=-0.415, `persistence_kappa_median`=-0.540, `persistence_log_eig_var_median`=-0.530, `tube_a_operator_norm_median`=0.563

## Shockable-only subgroup

- subgroup counts: `1` = 38, `5` = 20
- `tube_a_operator_norm_median`: medians `11.217` vs `9.779`, Cohen's `d = 0.650`, Mann-Whitney `p = 0.0158`
- `persistence_kappa_median`: medians `0.001` vs `0.001`, Cohen's `d = -0.783`, Mann-Whitney `p = 0.0245`
- `persistence_log_eig_var_median`: medians `1.663` vs `2.044`, Cohen's `d = -0.456`, Mann-Whitney `p = 0.0936`
- `tube_capture_gate_median`: medians `1.706` vs `1.609`, Cohen's `d = 0.400`, Mann-Whitney `p = 0.114`
- `tube_d_eff_median`: medians `2.795` vs `3.095`, Cohen's `d = -0.292`, Mann-Whitney `p = 0.322`
