# Coma Robustness Checks

- n_subjects: `277`
- selected geometry metrics: `geom_tube_d_eff_median, geom_persistence_kappa_median, geom_persistence_log_eig_var_median, geom_tube_a_operator_norm_median, geom_tube_capture_gate_median`
- shockable status available for: `260` subjects
- shockable subjects: `165`
- artifact detector status: unavailable for quantitative use in the locked export (`artifact_detector_enabled_all` is constant false and `artifact_burden_mean` is missing)
- WLST / time-of-death sensitivity: not available from the locked manuscript result bundle
- time-order disruption control: not run here because an honest test would require re-estimation from reordered trajectories rather than post hoc reshuffling of already-derived reachability summaries

## Shockable-only subset

- `geom_tube_d_eff_median`: medians `2.912` vs `2.545`, Cohen's `d = 0.571`, Mann-Whitney `p = 0.00161`
- `geom_persistence_kappa_median`: medians `0.000` vs `0.000`, Cohen's `d = 0.207`, Mann-Whitney `p = 0.0615`
- `geom_persistence_log_eig_var_median`: medians `1.515` vs `1.190`, Cohen's `d = 0.269`, Mann-Whitney `p = 0.102`
- `geom_tube_a_operator_norm_median`: medians `7.354` vs `7.529`, Cohen's `d = -0.029`, Mann-Whitney `p = 0.692`
- `geom_tube_capture_gate_median`: medians `1.363` vs `1.376`, Cohen's `d = -0.113`, Mann-Whitney `p = 0.797`

## Non-shockable-only subset

- `geom_tube_d_eff_median`: medians `2.899` vs `2.383`, Cohen's `d = 0.507`, Mann-Whitney `p = 0.0205`
- `geom_persistence_kappa_median`: medians `0.000` vs `0.000`, Cohen's `d = 0.318`, Mann-Whitney `p = 0.388`
- `geom_persistence_log_eig_var_median`: medians `1.045` vs `0.743`, Cohen's `d = 0.306`, Mann-Whitney `p = 0.00778`
- `geom_tube_a_operator_norm_median`: medians `5.487` vs `8.251`, Cohen's `d = -0.292`, Mann-Whitney `p = 0.0767`
- `geom_tube_capture_gate_median`: medians `1.228` vs `1.620`, Cohen's `d = -0.687`, Mann-Whitney `p = 0.00265`

## QC / coverage-only prediction model

- features: `qc__n_windows_total, clinical__channel_count_median, clinical__channel_coverage_frac_median`
- ROC AUC: `0.541 +/- 0.065`
- AUPRC: `0.534 +/- 0.039`
- Brier: `0.250 +/- 0.007`

## Geometry versus QC associations (Spearman)

- `geom_tube_d_eff_median` vs `qc__n_windows_total`: rho=`nan`, p=`nan` (n=`277`)
- `geom_tube_d_eff_median` vs `clinical__channel_count_median`: rho=`-0.154`, p=`0.0103` (n=`277`)
- `geom_tube_d_eff_median` vs `clinical__channel_coverage_frac_median`: rho=`-0.154`, p=`0.0103` (n=`277`)
- `geom_persistence_kappa_median` vs `qc__n_windows_total`: rho=`nan`, p=`nan` (n=`277`)
- `geom_persistence_kappa_median` vs `clinical__channel_count_median`: rho=`-0.227`, p=`0.000136` (n=`277`)
- `geom_persistence_kappa_median` vs `clinical__channel_coverage_frac_median`: rho=`-0.227`, p=`0.000136` (n=`277`)
- `geom_persistence_log_eig_var_median` vs `qc__n_windows_total`: rho=`nan`, p=`nan` (n=`277`)
- `geom_persistence_log_eig_var_median` vs `clinical__channel_count_median`: rho=`-0.255`, p=`1.73e-05` (n=`277`)
- `geom_persistence_log_eig_var_median` vs `clinical__channel_coverage_frac_median`: rho=`-0.255`, p=`1.73e-05` (n=`277`)
- `geom_tube_a_operator_norm_median` vs `qc__n_windows_total`: rho=`nan`, p=`nan` (n=`277`)
- `geom_tube_a_operator_norm_median` vs `clinical__channel_count_median`: rho=`0.025`, p=`0.673` (n=`277`)
- `geom_tube_a_operator_norm_median` vs `clinical__channel_coverage_frac_median`: rho=`0.025`, p=`0.673` (n=`277`)
- `geom_tube_capture_gate_median` vs `qc__n_windows_total`: rho=`nan`, p=`nan` (n=`277`)
- `geom_tube_capture_gate_median` vs `clinical__channel_count_median`: rho=`0.003`, p=`0.954` (n=`277`)
- `geom_tube_capture_gate_median` vs `clinical__channel_coverage_frac_median`: rho=`0.003`, p=`0.954` (n=`277`)

## Patient-label permutation

- `geom_tube_d_eff_median`: observed max/abs `d = 0.638`, null mean `0.093`, null p95 `0.229`, empirical `p = 0.0005`
- `geom_persistence_kappa_median`: observed max/abs `d = 0.127`, null mean `0.120`, null p95 `0.130`, empirical `p = 0.266`
- `geom_persistence_log_eig_var_median`: observed max/abs `d = 0.122`, null mean `0.120`, null p95 `0.125`, empirical `p = 0.245`
- `geom_tube_a_operator_norm_median`: observed max/abs `d = 0.129`, null mean `0.096`, null p95 `0.238`, empirical `p = 0.282`
- `geom_tube_capture_gate_median`: observed max/abs `d = 0.348`, null mean `0.096`, null p95 `0.239`, empirical `p = 0.0065`
- `max_abs_cohens_d_across_selected_metrics`: observed max/abs `d = 0.638`, null mean `0.165`, null p95 `0.287`, empirical `p = 0.0005`
