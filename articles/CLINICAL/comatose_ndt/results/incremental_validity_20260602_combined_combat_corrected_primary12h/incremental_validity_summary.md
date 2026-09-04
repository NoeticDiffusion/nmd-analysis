# Incremental Validity Summary

Primary endpoint cohort: `CPC1` vs `CPC5` in `0_12h`.

## Cohort

- n_subjects: 277
- CPC1: 140
- CPC5: 137

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
| clinical_only | 14 | 0.589 +/- 0.067 [0.576, 0.602] | 0.580 +/- 0.062 [0.569, 0.592] | 0.251 +/- 0.020 [0.247, 0.254] | 0.594 | +0.029 | 0.638 | 0.503 | -0.006 |
| eeg_only | 12 | 0.527 +/- 0.069 [0.514, 0.541] | 0.542 +/- 0.060 [0.530, 0.553] | 0.259 +/- 0.017 [0.256, 0.262] | 0.302 | +0.031 | 0.561 | 0.489 | -0.068 |
| clinical_plus_eeg | 26 | 0.595 +/- 0.073 [0.580, 0.609] | 0.594 +/- 0.066 [0.581, 0.607] | 0.254 +/- 0.026 [0.249, 0.259] | 0.494 | +0.034 | 0.611 | 0.535 | +0.000 |
| clinical_plus_eeg_plus_geometry | 31 | 0.687 +/- 0.073 [0.673, 0.701] | 0.680 +/- 0.073 [0.666, 0.694] | 0.231 +/- 0.033 [0.225, 0.238] | 0.632 | +0.030 | 0.675 | 0.608 | +0.092 |

## Geometry delta versus clinical + EEG

- delta ROC AUC: `+0.092` (95% bootstrap CI `+0.082` to `+0.102`, paired t-test `p = 7.75e-33`)
- delta AUPRC: `+0.086` (95% bootstrap CI `+0.076` to `+0.097`, paired t-test `p = 9.03e-29`)
- delta Brier: `-0.023` (95% bootstrap CI `-0.027` to `-0.019`, paired t-test `p = 5.75e-19`)

## Leave-One-Site-Out

- `clinical_only`: roc_auc=0.587 +/- 0.087, auprc=0.605 +/- 0.073, brier=0.264 +/- 0.043, cal_slope=0.520, cal_intercept=+0.025
- `eeg_only`: roc_auc=0.598 +/- 0.117, auprc=0.597 +/- 0.095, brier=0.254 +/- 0.028, cal_slope=1.436, cal_intercept=-0.307
- `clinical_plus_eeg`: roc_auc=0.603 +/- 0.118, auprc=0.606 +/- 0.053, brier=0.271 +/- 0.055, cal_slope=0.514, cal_intercept=-0.087
- `clinical_plus_eeg_plus_geometry`: roc_auc=0.667 +/- 0.129, auprc=0.651 +/- 0.078, brier=0.270 +/- 0.063, cal_slope=0.406, cal_intercept=+0.057

Brier deltas follow the usual score orientation, so more negative values indicate improvement.
Sensitivity and specificity are reported at a fixed probability threshold of `0.5` as an internal operating-point summary rather than as a bedside decision threshold recommendation.

## Top geometry-augmented coefficients

| Feature | Mean abs coef | Mean signed coef |
|---|---:|---:|
| geom_tube_d_eff_median | 0.812 | +0.812 |
| eeg__rawfeat_eeg_hjorth_complexity_median | 0.712 | -0.712 |
| clinical__shockable_rhythm | 0.583 | +0.583 |
| eeg__rawfeat_eeg_theta_median | 0.510 | -0.510 |
| eeg__rawfeat_eeg_hjorth_mobility_median | 0.482 | -0.482 |
| cat__hospital_D | 0.397 | +0.397 |
| eeg__rawfeat_eeg_alpha_median | 0.356 | -0.354 |
| eeg__rawfeat_eeg_beta_median | 0.270 | -0.267 |
| geom_persistence_log_eig_var_median | 0.257 | +0.254 |
| geom_persistence_kappa_median | 0.242 | +0.242 |
| cat__hospital_B | 0.224 | -0.224 |
| eeg__rawfeat_eeg_delta_median | 0.223 | +0.191 |
