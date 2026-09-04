# Coma Robustness Checks

- n_subjects: `281`
- selected geometry metrics: `geom_tube_d_eff_median, geom_persistence_kappa_median, geom_persistence_log_eig_var_median, geom_tube_a_operator_norm_median, geom_tube_capture_gate_median`
- shockable status available for: `264` subjects
- shockable subjects: `168`
- artifact detector status: unavailable for quantitative use in the locked export (`artifact_detector_enabled_all` is constant false and `artifact_burden_mean` is missing)
- WLST / time-of-death sensitivity: not available from the locked manuscript result bundle
- time-order disruption control: not run here because an honest test would require re-estimation from reordered trajectories rather than post hoc reshuffling of already-derived reachability summaries

## Shockable-only subset

- `geom_tube_d_eff_median`: medians `2.267` vs `1.980`, Cohen's `d = 0.754`, Mann-Whitney `p = 2.89e-06`
- `geom_persistence_kappa_median`: medians `0.002` vs `0.142`, Cohen's `d = 0.126`, Mann-Whitney `p = 0.631`
- `geom_persistence_log_eig_var_median`: medians `2.104` vs `2.331`, Cohen's `d = 0.165`, Mann-Whitney `p = 0.258`
- `geom_tube_a_operator_norm_median`: medians `6.906` vs `1.419`, Cohen's `d = 0.377`, Mann-Whitney `p = 0.307`
- `geom_tube_capture_gate_median`: medians `1.359` vs `0.448`, Cohen's `d = 0.317`, Mann-Whitney `p = 0.235`

## Non-shockable-only subset

- `geom_tube_d_eff_median`: medians `2.035` vs `2.134`, Cohen's `d = 0.027`, Mann-Whitney `p = 0.853`
- `geom_persistence_kappa_median`: medians `0.251` vs `0.001`, Cohen's `d = 0.298`, Mann-Whitney `p = 0.00276`
- `geom_persistence_log_eig_var_median`: medians `2.873` vs `1.428`, Cohen's `d = 0.308`, Mann-Whitney `p = 0.000549`
- `geom_tube_a_operator_norm_median`: medians `1.214` vs `8.968`, Cohen's `d = -0.672`, Mann-Whitney `p = 0.000728`
- `geom_tube_capture_gate_median`: medians `0.408` vs `1.544`, Cohen's `d = -0.775`, Mann-Whitney `p = 0.000564`

## QC / coverage-only prediction model

- features: `qc__n_windows_total, clinical__channel_count_median, clinical__channel_coverage_frac_median`
- ROC AUC: `0.556 +/- 0.086`
- AUPRC: `0.545 +/- 0.054`
- Brier: `0.250 +/- 0.012`

## Geometry versus QC associations (Spearman)

- `geom_tube_d_eff_median` vs `qc__n_windows_total`: rho=`nan`, p=`nan` (n=`281`)
- `geom_tube_d_eff_median` vs `clinical__channel_count_median`: rho=`-0.204`, p=`0.015` (n=`141`)
- `geom_tube_d_eff_median` vs `clinical__channel_coverage_frac_median`: rho=`-0.204`, p=`0.015` (n=`141`)
- `geom_persistence_kappa_median` vs `qc__n_windows_total`: rho=`nan`, p=`nan` (n=`281`)
- `geom_persistence_kappa_median` vs `clinical__channel_count_median`: rho=`-0.220`, p=`0.0088` (n=`141`)
- `geom_persistence_kappa_median` vs `clinical__channel_coverage_frac_median`: rho=`-0.220`, p=`0.0088` (n=`141`)
- `geom_persistence_log_eig_var_median` vs `qc__n_windows_total`: rho=`nan`, p=`nan` (n=`281`)
- `geom_persistence_log_eig_var_median` vs `clinical__channel_count_median`: rho=`-0.245`, p=`0.00346` (n=`141`)
- `geom_persistence_log_eig_var_median` vs `clinical__channel_coverage_frac_median`: rho=`-0.245`, p=`0.00346` (n=`141`)
- `geom_tube_a_operator_norm_median` vs `qc__n_windows_total`: rho=`nan`, p=`nan` (n=`281`)
- `geom_tube_a_operator_norm_median` vs `clinical__channel_count_median`: rho=`0.144`, p=`0.0889` (n=`141`)
- `geom_tube_a_operator_norm_median` vs `clinical__channel_coverage_frac_median`: rho=`0.144`, p=`0.0889` (n=`141`)
- `geom_tube_capture_gate_median` vs `qc__n_windows_total`: rho=`nan`, p=`nan` (n=`281`)
- `geom_tube_capture_gate_median` vs `clinical__channel_count_median`: rho=`0.045`, p=`0.6` (n=`141`)
- `geom_tube_capture_gate_median` vs `clinical__channel_coverage_frac_median`: rho=`0.045`, p=`0.6` (n=`141`)

## Patient-label permutation

- `geom_tube_d_eff_median`: observed max/abs `d = 0.513`, null mean `0.095`, null p95 `0.229`, empirical `p = 0.0005`
- `geom_persistence_kappa_median`: observed max/abs `d = 0.119`, null mean `0.119`, null p95 `0.120`, empirical `p = 0.481`
- `geom_persistence_log_eig_var_median`: observed max/abs `d = 0.123`, null mean `0.119`, null p95 `0.124`, empirical `p = 0.236`
- `geom_tube_a_operator_norm_median`: observed max/abs `d = 0.064`, null mean `0.094`, null p95 `0.234`, empirical `p = 0.581`
- `geom_tube_capture_gate_median`: observed max/abs `d = 0.142`, null mean `0.094`, null p95 `0.234`, empirical `p = 0.237`
- `max_abs_cohens_d_across_selected_metrics`: observed max/abs `d = 0.513`, null mean `0.157`, null p95 `0.266`, empirical `p = 0.0005`
