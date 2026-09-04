# Incremental Validity Summary

Primary endpoint cohort: `CPC1` vs `CPC5` in `0_12h`.

## Cohort

- n_subjects: 140
- CPC1: 70
- CPC5: 70

## Cross-validation procedure

- repeated CV splitter: `RepeatedStratifiedKFold(n_splits=5, n_repeats=20, random_state=20260517)`
- site sensitivity: `LeaveOneGroupOut()` with hospital as held-out group
- classifier: median imputation -> z-scoring -> `LogisticRegression(solver=liblinear, class_weight=balanced, max_iter=1000)`
- feature handling: fixed feature sets, with no additional fold-wise feature selection or univariate screening inside the CV loop
- selection boundary: the five geometry features were chosen before CV from the same locked cohort and should therefore be read as an internally validated post-selection exploratory layer rather than an externally frozen biomarker panel
- LOSO handling: `cat__hospital_*` dummy columns are excluded from evaluation to avoid out-of-support extrapolation in the held-out site

## Feature sets

- `clinical_only` (12): `cat__hospital_A`, `cat__hospital_B`, `cat__hospital_D`, `cat__hospital_E`, `cat__hospital_F`, `cat__sex_Female`, `cat__sex_Male`, `clinical__age`, `clinical__ohca`, `clinical__rosc_minutes`, `clinical__shockable_rhythm`, `clinical__ttm_celsius`
- `eeg_only` (12): `eeg__rawfeat_eeg_alpha_median`, `eeg__rawfeat_eeg_alpha_theta_median`, `eeg__rawfeat_eeg_beta_alpha_median`, `eeg__rawfeat_eeg_beta_median`, `eeg__rawfeat_eeg_delta_median`, `eeg__rawfeat_eeg_gamma_median`, `eeg__rawfeat_eeg_highfreq_power_30_45_median`, `eeg__rawfeat_eeg_hjorth_complexity_median`, `eeg__rawfeat_eeg_hjorth_mobility_median`, `eeg__rawfeat_eeg_permutation_entropy_median`, `eeg__rawfeat_eeg_sample_entropy_median`, `eeg__rawfeat_eeg_theta_median`
- `clinical_plus_eeg` (24): fixed union of clinical and EEG features
- `clinical_plus_eeg_plus_geometry` (29): fixed union of clinical, EEG, and geometry features
- geometry features (5): `geom_persistence_kappa_median`, `geom_persistence_log_eig_var_median`, `geom_tube_a_operator_norm_median`, `geom_tube_capture_gate_median`, `geom_tube_d_eff_median`

## Repeated Stratified CV

| Model | Features | ROC AUC | AUPRC | Brier | Cal. slope | Cal. intercept | Sens. @0.5 | Spec. @0.5 | Delta AUC vs clinical+EEG |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| clinical_only | 12 | 0.256 +/- 0.071 [0.242, 0.270] | 0.398 +/- 0.037 [0.392, 0.406] | 0.299 +/- 0.024 [0.294, 0.304] | -3.694 | -0.022 | 0.302 | 0.326 | -0.060 |
| eeg_only | 12 | 0.463 +/- 0.096 [0.443, 0.481] | 0.516 +/- 0.073 [0.502, 0.530] | 0.282 +/- 0.023 [0.277, 0.286] | -0.301 | +0.027 | 0.556 | 0.404 | +0.147 |
| clinical_plus_eeg | 24 | 0.316 +/- 0.086 [0.299, 0.332] | 0.422 +/- 0.046 [0.414, 0.431] | 0.331 +/- 0.034 [0.324, 0.337] | -1.096 | +0.076 | 0.404 | 0.341 | +0.000 |
| clinical_plus_eeg_plus_geometry | 29 | 0.561 +/- 0.097 [0.542, 0.579] | 0.556 +/- 0.079 [0.541, 0.571] | 0.289 +/- 0.044 [0.280, 0.297] | 0.132 | +0.033 | 0.594 | 0.495 | +0.245 |

## Geometry delta versus clinical + EEG

- delta ROC AUC: `+0.245` (95% bootstrap CI `+0.226` to `+0.263`, paired t-test `p = 1.77e-45`)
- delta AUPRC: `+0.134` (95% bootstrap CI `+0.120` to `+0.148`, paired t-test `p = 2.39e-34`)
- delta Brier: `-0.042` (95% bootstrap CI `-0.050` to `-0.034`, paired t-test `p = 2e-17`)

## Leave-One-Site-Out

- `clinical_only`: roc_auc=0.230 +/- 0.175, auprc=0.403 +/- 0.055, brier=0.314 +/- 0.031, cal_slope=-40.612, cal_intercept=+2.217
- `eeg_only`: roc_auc=0.522 +/- 0.101, auprc=0.551 +/- 0.080, brier=0.277 +/- 0.034, cal_slope=0.201, cal_intercept=+0.214
- `clinical_plus_eeg`: roc_auc=0.310 +/- 0.144, auprc=0.425 +/- 0.050, brier=0.332 +/- 0.015, cal_slope=-2.347, cal_intercept=+0.120
- `clinical_plus_eeg_plus_geometry`: roc_auc=0.464 +/- 0.163, auprc=0.520 +/- 0.086, brier=0.377 +/- 0.119, cal_slope=0.034, cal_intercept=+0.042

Brier deltas follow the usual score orientation, so more negative values indicate improvement.
Sensitivity and specificity are reported at a fixed probability threshold of `0.5` as an internal operating-point summary rather than as a bedside decision threshold recommendation.

## Top geometry-augmented coefficients

| Feature | Mean abs coef | Mean signed coef |
|---|---:|---:|
| geom_tube_a_operator_norm_median | 1.039 | -1.039 |
| eeg__rawfeat_eeg_hjorth_complexity_median | 0.627 | -0.627 |
| eeg__rawfeat_eeg_beta_median | 0.488 | -0.252 |
| geom_tube_d_eff_median | 0.427 | +0.414 |
| eeg__rawfeat_eeg_beta_alpha_median | 0.319 | -0.247 |
| eeg__rawfeat_eeg_hjorth_mobility_median | 0.317 | -0.307 |
| eeg__rawfeat_eeg_gamma_median | 0.303 | +0.252 |
| eeg__rawfeat_eeg_highfreq_power_30_45_median | 0.303 | +0.252 |
| eeg__rawfeat_eeg_permutation_entropy_median | 0.271 | -0.271 |
| eeg__rawfeat_eeg_sample_entropy_median | 0.271 | -0.271 |
| eeg__rawfeat_eeg_delta_median | 0.242 | -0.086 |
| eeg__rawfeat_eeg_theta_median | 0.239 | -0.169 |
