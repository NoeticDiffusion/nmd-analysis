# Incremental Validity Summary

Primary endpoint cohort: `CPC1` vs `CPC5` in `0_12h`.

## Cohort

- n_subjects: 281
- CPC1: 141
- CPC5: 140

## Cross-validation procedure

- repeated CV splitter: `RepeatedStratifiedKFold(n_splits=5, n_repeats=20, random_state=20260517)`
- site sensitivity: `LeaveOneGroupOut()` with hospital as held-out group
- classifier: median imputation -> z-scoring -> `LogisticRegression(solver=liblinear, class_weight=balanced, max_iter=1000)`
- feature handling: fixed feature sets, with no additional fold-wise feature selection or univariate screening inside the CV loop
- selection boundary: the five geometry features were chosen before CV from the same locked cohort and should therefore be read as an internally validated post-selection exploratory layer rather than an externally frozen biomarker panel
- LOSO handling: `cat__hospital_*` dummy columns are excluded from evaluation to avoid out-of-support extrapolation in the held-out site

## Feature sets

- `clinical_only` (14): `cat__hospital_A`, `cat__hospital_B`, `cat__hospital_D`, `cat__hospital_E`, `cat__hospital_F`, `cat__sex_Female`, `cat__sex_Male`, `clinical__age`, `clinical__channel_count_median`, `clinical__channel_coverage_frac_median`, `clinical__ohca`, `clinical__rosc_minutes`, `clinical__shockable_rhythm`, `clinical__ttm_celsius`
- `eeg_only` (12): `eeg__rawfeat_eeg_alpha_median`, `eeg__rawfeat_eeg_alpha_theta_median`, `eeg__rawfeat_eeg_beta_alpha_median`, `eeg__rawfeat_eeg_beta_median`, `eeg__rawfeat_eeg_delta_median`, `eeg__rawfeat_eeg_gamma_median`, `eeg__rawfeat_eeg_highfreq_power_30_45_median`, `eeg__rawfeat_eeg_hjorth_complexity_median`, `eeg__rawfeat_eeg_hjorth_mobility_median`, `eeg__rawfeat_eeg_permutation_entropy_median`, `eeg__rawfeat_eeg_sample_entropy_median`, `eeg__rawfeat_eeg_theta_median`
- `clinical_plus_eeg` (26): fixed union of clinical and EEG features
- `clinical_plus_eeg_plus_geometry` (31): fixed union of clinical, EEG, and geometry features
- geometry features (5): `geom_persistence_kappa_median`, `geom_persistence_log_eig_var_median`, `geom_tube_a_operator_norm_median`, `geom_tube_capture_gate_median`, `geom_tube_d_eff_median`

## Repeated Stratified CV

| Model | Features | ROC AUC | AUPRC | Brier | Cal. slope | Cal. intercept | Sens. @0.5 | Spec. @0.5 | Delta AUC vs clinical+EEG |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| clinical_only | 14 | 0.596 +/- 0.065 [0.584, 0.609] | 0.583 +/- 0.065 [0.570, 0.595] | 0.248 +/- 0.018 [0.245, 0.252] | 0.595 | +0.011 | 0.643 | 0.502 | -0.003 |
| eeg_only | 12 | 0.521 +/- 0.066 [0.508, 0.534] | 0.527 +/- 0.056 [0.517, 0.538] | 0.260 +/- 0.015 [0.257, 0.263] | 0.219 | +0.012 | 0.570 | 0.477 | -0.079 |
| clinical_plus_eeg | 26 | 0.599 +/- 0.066 [0.587, 0.612] | 0.596 +/- 0.068 [0.583, 0.609] | 0.251 +/- 0.022 [0.246, 0.255] | 0.496 | +0.009 | 0.605 | 0.533 | +0.000 |
| clinical_plus_eeg_plus_geometry | 31 | 0.636 +/- 0.067 [0.622, 0.649] | 0.642 +/- 0.070 [0.628, 0.656] | 0.246 +/- 0.025 [0.241, 0.251] | 0.526 | +0.013 | 0.627 | 0.563 | +0.036 |

## Geometry delta versus clinical + EEG

- delta ROC AUC: `+0.036` (95% bootstrap CI `+0.028` to `+0.045`, paired t-test `p = 2.27e-13`)
- delta AUPRC: `+0.046` (95% bootstrap CI `+0.038` to `+0.054`, paired t-test `p = 5.55e-19`)
- delta Brier: `-0.005` (95% bootstrap CI `-0.008` to `-0.002`, paired t-test `p = 0.00262`)

## Leave-One-Site-Out

- `clinical_only`: roc_auc=0.600 +/- 0.072, auprc=0.612 +/- 0.055, brier=0.262 +/- 0.042, cal_slope=0.535, cal_intercept=+0.001
- `eeg_only`: roc_auc=0.614 +/- 0.112, auprc=0.591 +/- 0.105, brier=0.255 +/- 0.027, cal_slope=1.566, cal_intercept=-0.200
- `clinical_plus_eeg`: roc_auc=0.625 +/- 0.108, auprc=0.645 +/- 0.056, brier=0.272 +/- 0.054, cal_slope=0.575, cal_intercept=-0.128
- `clinical_plus_eeg_plus_geometry`: roc_auc=0.649 +/- 0.088, auprc=0.651 +/- 0.022, brier=0.271 +/- 0.045, cal_slope=0.514, cal_intercept=-0.157

Brier deltas follow the usual score orientation, so more negative values indicate improvement.
Sensitivity and specificity are reported at a fixed probability threshold of `0.5` as an internal operating-point summary rather than as a bedside decision threshold recommendation.

## Top geometry-augmented coefficients

| Feature | Mean abs coef | Mean signed coef |
|---|---:|---:|
| eeg__rawfeat_eeg_hjorth_mobility_median | 0.673 | -0.673 |
| eeg__rawfeat_eeg_hjorth_complexity_median | 0.650 | -0.650 |
| clinical__shockable_rhythm | 0.579 | +0.579 |
| geom_tube_d_eff_median | 0.497 | +0.497 |
| eeg__rawfeat_eeg_alpha_median | 0.449 | -0.449 |
| eeg__rawfeat_eeg_theta_median | 0.358 | -0.356 |
| eeg__rawfeat_eeg_beta_median | 0.344 | -0.339 |
| cat__hospital_D | 0.241 | +0.241 |
| cat__hospital_B | 0.221 | -0.218 |
| geom_tube_a_operator_norm_median | 0.212 | -0.199 |
| clinical__ohca | 0.209 | -0.209 |
| eeg__rawfeat_eeg_delta_median | 0.206 | +0.174 |
