# Additional QC / robustness summary

- cohort subjects: `281`
- CPC1 subjects: `141`
- CPC5 subjects: `140`

## Leave-one-subject-out metric stability

- `reachability_tube_d_eff_median`: full `d = 0.838`, leave-one-subject-out range `0.814` to `0.899`, sign consistency `1.000`
- `reachability_persistence_log_eig_var_median`: full `d = 0.736`, leave-one-subject-out range `0.713` to `0.794`, sign consistency `1.000`
- `reachability_tube_capture_gate_median`: full `d = -0.558`, leave-one-subject-out range `-0.608` to `-0.526`, sign consistency `1.000`
- `mnj3d_spectral_radius_median`: full `d = -0.521`, leave-one-subject-out range `-0.577` to `-0.506`, sign consistency `1.000`
- `mnj9d_spectral_radius_median`: full `d = -0.603`, leave-one-subject-out range `-0.721` to `-0.585`, sign consistency `1.000`

## Leave-one-site-out metric stability

- `reachability_tube_d_eff_median`: full `d = 0.838`, leave-one-site-out range `0.699` to `0.980`, sign consistency `1.000`
- `reachability_persistence_log_eig_var_median`: full `d = 0.736`, leave-one-site-out range `0.461` to `0.911`, sign consistency `1.000`
- `reachability_tube_capture_gate_median`: full `d = -0.558`, leave-one-site-out range `-0.659` to `-0.356`, sign consistency `1.000`
- `mnj3d_spectral_radius_median`: full `d = -0.521`, leave-one-site-out range `-0.602` to `-0.460`, sign consistency `1.000`
- `mnj9d_spectral_radius_median`: full `d = -0.603`, leave-one-site-out range `-0.763` to `-0.263`, sign consistency `1.000`

## Leave-one-subject-out prediction

- `clinical_plus_eeg`: `AUROC = 0.601`, `AUPRC = 0.578`, `Brier = 0.247`
- `clinical_plus_eeg_plus_geometry`: `AUROC = 0.638`, `AUPRC = 0.626`, `Brier = 0.241`

## Cross-fitted repeated CV

- `clinical_plus_eeg`: `AUROC = 0.602 +/- 0.109`, `AUPRC = 0.632 +/- 0.094`, `Brier = 0.269 +/- 0.052`
- `fixed_clinical_plus_eeg_plus_geometry`: `AUROC = 0.708 +/- 0.098`, `AUPRC = 0.729 +/- 0.090`, `Brier = 0.234 +/- 0.052`
- `crossfit_clinical_plus_eeg_plus_geometry`: `AUROC = 0.720 +/- 0.095`, `AUPRC = 0.751 +/- 0.088`, `Brier = 0.228 +/- 0.051`
- `crossfit_geometry_only`: `AUROC = 0.747 +/- 0.089`, `AUPRC = 0.784 +/- 0.088`, `Brier = 0.212 +/- 0.033`

Top cross-fitted reachability metrics:

- `persistence_hysteresis_log_det_median` selected in `100` folds
- `persistence_log_det_median` selected in `91` folds
- `cone_d_eff_h1_median` selected in `62` folds
- `tube_d_eff_split_half_a_median` selected in `40` folds
- `cone_q_ratio_h2_median` selected in `39` folds
- `cone_q_ratio_h3_median` selected in `34` folds
- `persistence_hysteresis_log_eig_var_median` selected in `26` folds
- `q_ratio_h2_median` selected in `24` folds
- `cone_d_eff_h2_median` selected in `23` folds
- `q_ratio_h3_median` selected in `19` folds

## Hourly time-shift null

- `mnj3d_spectral_radius_median`: observed peak `3_4h` with `d = -0.657`, null mean max `|d| = 0.638`, null p95 `0.725`, empirical `p = 0.312`
- `mnj9d_spectral_radius_median`: observed peak `2_3h` with `d = -0.849`, null mean max `|d| = 0.899`, null p95 `1.010`, empirical `p = 0.765`
- `reachability_persistence_log_eig_var_median`: observed peak `4_5h` with `d = 0.954`, null mean max `|d| = 1.021`, null p95 `1.178`, empirical `p = 0.769`
- `reachability_tube_capture_gate_median`: observed peak `3_4h` with `d = -0.711`, null mean max `|d| = 0.786`, null p95 `0.933`, empirical `p = 0.836`
- `reachability_tube_d_eff_median`: observed peak `2_3h` with `d = 0.950`, null mean max `|d| = 1.061`, null p95 `1.217`, empirical `p = 0.947`
