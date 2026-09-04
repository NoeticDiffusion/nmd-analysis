# Coma Robustness Checks

- n_subjects: `281`
- selected geometry metrics: `geom_tube_d_eff_median, geom_persistence_log_det_median, geom_persistence_log_eig_var_median, geom_persistence_hysteresis_log_det_median, geom_tube_capture_gate_median`
- shockable status available for: `264` subjects
- shockable subjects: `168`
- artifact detector status: unavailable for quantitative use in the locked export (`artifact_detector_enabled_all` is constant false and `artifact_burden_mean` is missing)
- WLST / time-of-death sensitivity: not available from the locked manuscript result bundle
- time-order disruption control: not run here because an honest test would require re-estimation from reordered trajectories rather than post hoc reshuffling of already-derived reachability summaries

## Shockable-only subset

- `geom_tube_d_eff_median`: medians `2.963` vs `2.448`, Cohen's `d = 0.690`, Mann-Whitney `p = 0.00522`
- `geom_persistence_log_det_median`: medians `1.267` vs `0.808`, Cohen's `d = 0.689`, Mann-Whitney `p = 0.00473`
- `geom_persistence_log_eig_var_median`: medians `1.596` vs `1.118`, Cohen's `d = 0.482`, Mann-Whitney `p = 0.0424`
- `geom_persistence_hysteresis_log_det_median`: medians `2.632` vs `3.714`, Cohen's `d = -0.762`, Mann-Whitney `p = 0.00215`
- `geom_tube_capture_gate_median`: medians `1.773` vs `1.911`, Cohen's `d = -0.489`, Mann-Whitney `p = 0.108`

## Non-shockable-only subset

- `geom_tube_d_eff_median`: medians `3.087` vs `2.449`, Cohen's `d = 0.966`, Mann-Whitney `p = 0.00672`
- `geom_persistence_log_det_median`: medians `1.514` vs `0.866`, Cohen's `d = 1.152`, Mann-Whitney `p = 0.00851`
- `geom_persistence_log_eig_var_median`: medians `1.661` vs `0.897`, Cohen's `d = 1.001`, Mann-Whitney `p = 0.0107`
- `geom_persistence_hysteresis_log_det_median`: medians `2.204` vs `3.775`, Cohen's `d = -0.924`, Mann-Whitney `p = 0.00226`
- `geom_tube_capture_gate_median`: medians `1.961` vs `1.963`, Cohen's `d = -0.475`, Mann-Whitney `p = 0.2`

## QC / coverage-only prediction model

- features: `qc__n_windows_total, clinical__channel_count_median, clinical__channel_coverage_frac_median`
- ROC AUC: `0.543 +/- 0.056`
- AUPRC: `0.530 +/- 0.035`
- Brier: `0.250 +/- 0.006`

## Geometry versus QC associations (Spearman)

- `geom_tube_d_eff_median` vs `qc__n_windows_total`: rho=`nan`, p=`nan` (n=`130`)
- `geom_tube_d_eff_median` vs `clinical__channel_count_median`: rho=`-0.027`, p=`0.759` (n=`130`)
- `geom_tube_d_eff_median` vs `clinical__channel_coverage_frac_median`: rho=`-0.027`, p=`0.759` (n=`130`)
- `geom_persistence_log_det_median` vs `qc__n_windows_total`: rho=`nan`, p=`nan` (n=`130`)
- `geom_persistence_log_det_median` vs `clinical__channel_count_median`: rho=`-0.056`, p=`0.523` (n=`130`)
- `geom_persistence_log_det_median` vs `clinical__channel_coverage_frac_median`: rho=`-0.056`, p=`0.523` (n=`130`)
- `geom_persistence_log_eig_var_median` vs `qc__n_windows_total`: rho=`nan`, p=`nan` (n=`130`)
- `geom_persistence_log_eig_var_median` vs `clinical__channel_count_median`: rho=`-0.221`, p=`0.0113` (n=`130`)
- `geom_persistence_log_eig_var_median` vs `clinical__channel_coverage_frac_median`: rho=`-0.221`, p=`0.0113` (n=`130`)
- `geom_persistence_hysteresis_log_det_median` vs `qc__n_windows_total`: rho=`nan`, p=`nan` (n=`130`)
- `geom_persistence_hysteresis_log_det_median` vs `clinical__channel_count_median`: rho=`0.055`, p=`0.535` (n=`130`)
- `geom_persistence_hysteresis_log_det_median` vs `clinical__channel_coverage_frac_median`: rho=`0.055`, p=`0.535` (n=`130`)
- `geom_tube_capture_gate_median` vs `qc__n_windows_total`: rho=`nan`, p=`nan` (n=`130`)
- `geom_tube_capture_gate_median` vs `clinical__channel_count_median`: rho=`0.345`, p=`5.91e-05` (n=`130`)
- `geom_tube_capture_gate_median` vs `clinical__channel_coverage_frac_median`: rho=`0.345`, p=`5.91e-05` (n=`130`)

## Patient-label permutation

- `geom_tube_d_eff_median`: observed max/abs `d = 0.838`, null mean `0.143`, null p95 `0.348`, empirical `p = 0.0005`
- `geom_persistence_log_det_median`: observed max/abs `d = 0.896`, null mean `0.142`, null p95 `0.345`, empirical `p = 0.0005`
- `geom_persistence_log_eig_var_median`: observed max/abs `d = 0.736`, null mean `0.143`, null p95 `0.352`, empirical `p = 0.0005`
- `geom_persistence_hysteresis_log_det_median`: observed max/abs `d = 0.909`, null mean `0.144`, null p95 `0.350`, empirical `p = 0.0005`
- `geom_tube_capture_gate_median`: observed max/abs `d = 0.558`, null mean `0.140`, null p95 `0.349`, empirical `p = 0.0015`
- `max_abs_cohens_d_across_selected_metrics`: observed max/abs `d = 0.909`, null mean `0.232`, null p95 `0.430`, empirical `p = 0.0005`
