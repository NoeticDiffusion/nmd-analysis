# Additional QC / robustness summary

- cohort subjects: `277`
- CPC1 subjects: `140`
- CPC5 subjects: `137`

## Leave-one-subject-out metric stability

- `reachability_tube_d_eff_median`: full `d = 0.638`, leave-one-subject-out range `0.626` to `0.668`, sign consistency `1.000`
- `reachability_persistence_log_eig_var_median`: full `d = 0.122`, leave-one-subject-out range `0.120` to `0.123`, sign consistency `1.000`
- `reachability_tube_capture_gate_median`: full `d = -0.348`, leave-one-subject-out range `-0.366` to `-0.332`, sign consistency `1.000`
- `mnj3d_spectral_radius_median`: full `d = -0.536`, leave-one-subject-out range `-0.583` to `-0.521`, sign consistency `1.000`
- `mnj9d_spectral_radius_median`: full `d = -0.138`, leave-one-subject-out range `-0.653` to `-0.137`, sign consistency `1.000`

## Leave-one-site-out metric stability

- `reachability_tube_d_eff_median`: full `d = 0.638`, leave-one-site-out range `0.374` to `0.751`, sign consistency `1.000`
- `reachability_persistence_log_eig_var_median`: full `d = 0.122`, leave-one-site-out range `0.124` to `0.182`, sign consistency `1.000`
- `reachability_tube_capture_gate_median`: full `d = -0.348`, leave-one-site-out range `-0.510` to `-0.208`, sign consistency `1.000`
- `mnj3d_spectral_radius_median`: full `d = -0.536`, leave-one-site-out range `-0.596` to `-0.505`, sign consistency `1.000`
- `mnj9d_spectral_radius_median`: full `d = -0.138`, leave-one-site-out range `-0.706` to `-0.146`, sign consistency `1.000`

## Leave-one-subject-out prediction

- `clinical_plus_eeg`: `AUROC = 0.601`, `AUPRC = 0.567`, `Brier = 0.247`
- `clinical_plus_eeg_plus_geometry`: `AUROC = 0.694`, `AUPRC = 0.662`, `Brier = 0.225`

## Cross-fitted repeated CV

- `clinical_plus_eeg`: `AUROC = 0.605 +/- 0.064`, `AUPRC = 0.606 +/- 0.065`, `Brier = 0.249 +/- 0.021`
- `fixed_clinical_plus_eeg_plus_geometry`: `AUROC = 0.694 +/- 0.063`, `AUPRC = 0.682 +/- 0.073`, `Brier = 0.227 +/- 0.026`
- `crossfit_clinical_plus_eeg_plus_geometry`: `AUROC = 0.686 +/- 0.064`, `AUPRC = 0.673 +/- 0.073`, `Brier = 0.231 +/- 0.026`
- `crossfit_geometry_only`: `AUROC = 0.655 +/- 0.066`, `AUPRC = 0.645 +/- 0.067`, `Brier = 0.232 +/- 0.018`

Top cross-fitted reachability metrics:

- `tube_d_eff_split_half_b_median` selected in `85` folds
- `cone_d_eff_h2_median` selected in `75` folds
- `tube_d_eff_median` selected in `70` folds
- `persistence_log_det_median` selected in `68` folds
- `persistence_hysteresis_log_det_median` selected in `54` folds
- `cone_d_eff_h3_median` selected in `30` folds
- `tube_d_eff_split_half_a_median` selected in `30` folds
- `cone_d_eff_h1_median` selected in `20` folds
- `cone_q_ratio_h2_median` selected in `19` folds
- `cone_q_ratio_h3_median` selected in `16` folds

## Hourly time-shift null

- `mnj3d_spectral_radius_median`: observed peak `3_4h` with `d = -0.654`, null mean max `|d| = 0.661`, null p95 `0.741`, empirical `p = 0.514`
- `mnj9d_spectral_radius_median`: observed peak `3_4h` with `d = -0.728`, null mean max `|d| = 0.689`, null p95 `0.757`, empirical `p = 0.169`
- `reachability_persistence_log_eig_var_median`: observed peak `4_5h` with `d = 0.529`, null mean max `|d| = 0.583`, null p95 `0.668`, empirical `p = 0.902`
- `reachability_tube_capture_gate_median`: observed peak `3_4h` with `d = -0.389`, null mean max `|d| = 0.396`, null p95 `0.465`, empirical `p = 0.527`
- `reachability_tube_d_eff_median`: observed peak `3_4h` with `d = 0.687`, null mean max `|d| = 0.704`, null p95 `0.794`, empirical `p = 0.606`
