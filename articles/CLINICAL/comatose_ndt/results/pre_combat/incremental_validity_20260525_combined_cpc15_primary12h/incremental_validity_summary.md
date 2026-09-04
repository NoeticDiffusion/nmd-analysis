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
| clinical_only | 14 | 0.600 +/- 0.067 [0.588, 0.613] | 0.597 +/- 0.070 [0.584, 0.611] | 0.249 +/- 0.019 [0.245, 0.252] | 0.591 | +0.006 | 0.649 | 0.505 | +0.017 |
| eeg_only | 12 | 0.566 +/- 0.067 [0.553, 0.579] | 0.556 +/- 0.060 [0.545, 0.568] | 0.259 +/- 0.014 [0.256, 0.262] | 0.212 | +0.011 | 0.576 | 0.522 | -0.017 |
| clinical_plus_eeg | 26 | 0.583 +/- 0.067 [0.570, 0.596] | 0.572 +/- 0.062 [0.560, 0.584] | 0.260 +/- 0.024 [0.255, 0.265] | 0.297 | +0.005 | 0.581 | 0.529 | +0.000 |
| clinical_plus_eeg_plus_geometry | 31 | 0.672 +/- 0.062 [0.659, 0.684] | 0.653 +/- 0.073 [0.639, 0.668] | 0.237 +/- 0.026 [0.232, 0.242] | 0.453 | +0.008 | 0.655 | 0.617 | +0.088 |

## Geometry delta versus clinical + EEG

- delta ROC AUC: `+0.088` (95% bootstrap CI `+0.079` to `+0.097`, paired t-test `p = 1.77e-34`)
- delta AUPRC: `+0.081` (95% bootstrap CI `+0.072` to `+0.090`, paired t-test `p = 4.39e-32`)
- delta Brier: `-0.023` (95% bootstrap CI `-0.026` to `-0.019`, paired t-test `p = 1.92e-23`)

## Leave-One-Site-Out

- `clinical_only`: roc_auc=0.599 +/- 0.081, auprc=0.630 +/- 0.041, brier=0.263 +/- 0.045, cal_slope=0.532, cal_intercept=+0.016
- `eeg_only`: roc_auc=0.616 +/- 0.087, auprc=0.585 +/- 0.140, brier=0.277 +/- 0.040, cal_slope=1.235, cal_intercept=-0.233
- `clinical_plus_eeg`: roc_auc=0.571 +/- 0.067, auprc=0.560 +/- 0.085, brier=0.296 +/- 0.017, cal_slope=0.047, cal_intercept=-0.170
- `clinical_plus_eeg_plus_geometry`: roc_auc=0.612 +/- 0.026, auprc=0.593 +/- 0.135, brier=0.286 +/- 0.017, cal_slope=0.115, cal_intercept=-0.138

Brier deltas follow the usual score orientation, so more negative values indicate improvement.
Sensitivity and specificity are reported at a fixed probability threshold of `0.5` as an internal operating-point summary rather than as a bedside decision threshold recommendation.

## Top geometry-augmented coefficients

| Feature | Mean abs coef | Mean signed coef |
|---|---:|---:|
| geom_tube_d_eff_median | 1.009 | +1.009 |
| geom_tube_capture_gate_median | 0.860 | -0.860 |
| eeg__rawfeat_eeg_hjorth_complexity_median | 0.644 | -0.644 |
| clinical__shockable_rhythm | 0.531 | +0.531 |
| eeg__rawfeat_eeg_beta_median | 0.518 | -0.381 |
| eeg__rawfeat_eeg_hjorth_mobility_median | 0.509 | -0.509 |
| eeg__rawfeat_eeg_alpha_median | 0.468 | +0.460 |
| eeg__rawfeat_eeg_theta_median | 0.290 | -0.196 |
| geom_tube_a_operator_norm_median | 0.264 | +0.261 |
| eeg__rawfeat_eeg_permutation_entropy_median | 0.252 | -0.252 |
| eeg__rawfeat_eeg_sample_entropy_median | 0.252 | -0.252 |
| cat__hospital_D | 0.220 | +0.220 |
