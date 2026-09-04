# 9D Jacobian Incremental Validity Summary

- n_subjects: `281`
- CPC1: `141`
- CPC5: `140`

## Cross-validation procedure

- repeated CV splitter: `RepeatedStratifiedKFold(n_splits=5, n_repeats=20, random_state=20260525)`
- site sensitivity: `LeaveOneGroupOut()` with hospital as held-out group
- classifier: median imputation -> z-scoring -> `LogisticRegression(solver=liblinear, class_weight=balanced, max_iter=1000)`
- feature handling: fixed feature ladders with no in-fold feature selection or univariate screening
- LOSO handling: `cat__hospital_*` dummy columns are dropped in held-out-site evaluation

## Feature ladders

- `clinical_plus_eeg` (26): fixed union of clinical and EEG baseline features
- `jacobian9d_only` (5): `jac9d__spectral_radius_median`, `jac9d__anisotropy_abs_eig_median`, `jac9d__mdr_median`, `jac9d__rotational_power_mean`, `jac9d__rotational_power_median`
- `reachability_only` (5): `reach__tube_d_eff_median`, `reach__persistence_kappa_median`, `reach__persistence_log_eig_var_median`, `reach__tube_a_operator_norm_median`, `reach__tube_capture_gate_median`
- `jacobian3d_only` (3): `jac3d__jacobian_spectral_radius_median`, `jac3d__jacobian_fro_median`, `jac3d__jacobian_condition_median`
- `clinical_plus_eeg_plus_jacobian9d` (31): clinical + EEG + revised 9D
- `clinical_plus_eeg_plus_reachability` (31): clinical + EEG + reachability
- `clinical_plus_eeg_plus_reachability_plus_jacobian9d` (36): clinical + EEG + reachability + revised 9D

## Repeated CV

- `clinical_only`: AUROC `0.596 [0.583, 0.609]`, AUPRC `0.582 [0.570, 0.594]`, Brier `0.249 [0.246, 0.253]`; delta AUROC vs `clinical_plus_eeg` `+0.008 [+0.001, +0.015]`; delta AUROC vs `clinical_plus_eeg_plus_reachability` `-0.096 [-0.107, -0.085]`
- `eeg_only`: AUROC `0.564 [0.552, 0.576]`, AUPRC `0.552 [0.542, 0.563]`, Brier `0.259 [0.257, 0.262]`; delta AUROC vs `clinical_plus_eeg` `-0.024 [-0.037, -0.011]`; delta AUROC vs `clinical_plus_eeg_plus_reachability` `-0.128 [-0.142, -0.114]`
- `clinical_plus_eeg`: AUROC `0.588 [0.576, 0.601]`, AUPRC `0.569 [0.558, 0.580]`, Brier `0.259 [0.255, 0.264]`; delta AUROC vs `clinical_plus_eeg` `+0.000 [+0.000, +0.000]`; delta AUROC vs `clinical_plus_eeg_plus_reachability` `-0.104 [-0.113, -0.095]`
- `jacobian9d_only`: AUROC `0.676 [0.664, 0.687]`, AUPRC `0.618 [0.606, 0.631]`, Brier `0.222 [0.219, 0.225]`; delta AUROC vs `clinical_plus_eeg` `+0.087 [+0.070, +0.104]`; delta AUROC vs `clinical_plus_eeg_plus_reachability` `-0.017 [-0.030, -0.004]`
- `reachability_only`: AUROC `0.673 [0.661, 0.685]`, AUPRC `0.654 [0.642, 0.666]`, Brier `0.226 [0.222, 0.230]`; delta AUROC vs `clinical_plus_eeg` `+0.085 [+0.070, +0.099]`; delta AUROC vs `clinical_plus_eeg_plus_reachability` `-0.020 [-0.031, -0.008]`
- `jacobian3d_only`: AUROC `0.714 [0.701, 0.727]`, AUPRC `0.677 [0.662, 0.692]`, Brier `0.218 [0.215, 0.222]`; delta AUROC vs `clinical_plus_eeg` `+0.126 [+0.110, +0.142]`; delta AUROC vs `clinical_plus_eeg_plus_reachability` `+0.022 [+0.009, +0.034]`
- `coords9d_only`: AUROC `0.629 [0.616, 0.643]`, AUPRC `0.650 [0.636, 0.664]`, Brier `0.242 [0.240, 0.244]`; delta AUROC vs `clinical_plus_eeg` `+0.041 [+0.025, +0.057]`; delta AUROC vs `clinical_plus_eeg_plus_reachability` `-0.063 [-0.077, -0.049]`
- `clinical_plus_eeg_plus_jacobian9d`: AUROC `0.694 [0.682, 0.705]`, AUPRC `0.641 [0.629, 0.653]`, Brier `0.226 [0.221, 0.231]`; delta AUROC vs `clinical_plus_eeg` `+0.106 [+0.096, +0.115]`; delta AUROC vs `clinical_plus_eeg_plus_reachability` `+0.001 [-0.006, +0.009]`
- `clinical_plus_eeg_plus_reachability`: AUROC `0.692 [0.680, 0.705]`, AUPRC `0.660 [0.648, 0.674]`, Brier `0.231 [0.226, 0.237]`; delta AUROC vs `clinical_plus_eeg` `+0.104 [+0.095, +0.113]`; delta AUROC vs `clinical_plus_eeg_plus_reachability` `+0.000 [+0.000, +0.000]`
- `clinical_plus_eeg_plus_jacobian3d`: AUROC `0.697 [0.686, 0.709]`, AUPRC `0.639 [0.628, 0.650]`, Brier `0.226 [0.221, 0.231]`; delta AUROC vs `clinical_plus_eeg` `+0.109 [+0.100, +0.118]`; delta AUROC vs `clinical_plus_eeg_plus_reachability` `+0.005 [-0.003, +0.012]`
- `clinical_plus_eeg_plus_reachability_plus_jacobian9d`: AUROC `0.710 [0.698, 0.722]`, AUPRC `0.665 [0.652, 0.679]`, Brier `0.223 [0.217, 0.228]`; delta AUROC vs `clinical_plus_eeg` `+0.122 [+0.112, +0.132]`; delta AUROC vs `clinical_plus_eeg_plus_reachability` `+0.018 [+0.013, +0.023]`

## Leave-One-Site-Out

- `clinical_only`: AUROC `0.600 [0.548, 0.660]`, AUPRC `0.612 [0.570, 0.653]`, Brier `0.262 [0.226, 0.293]`
- `eeg_only`: AUROC `0.612 [0.560, 0.691]`, AUPRC `0.578 [0.478, 0.692]`, Brier `0.277 [0.248, 0.310]`
- `clinical_plus_eeg`: AUROC `0.577 [0.523, 0.630]`, AUPRC `0.545 [0.482, 0.585]`, Brier `0.296 [0.281, 0.310]`
- `jacobian9d_only`: AUROC `0.630 [0.583, 0.674]`, AUPRC `0.577 [0.479, 0.635]`, Brier `0.231 [0.218, 0.248]`
- `reachability_only`: AUROC `0.627 [0.546, 0.685]`, AUPRC `0.596 [0.484, 0.707]`, Brier `0.248 [0.226, 0.271]`
- `jacobian3d_only`: AUROC `0.663 [0.578, 0.728]`, AUPRC `0.613 [0.537, 0.690]`, Brier `0.239 [0.212, 0.283]`
- `coords9d_only`: AUROC `0.535 [0.422, 0.659]`, AUPRC `0.542 [0.381, 0.669]`, Brier `0.267 [0.241, 0.308]`
- `clinical_plus_eeg_plus_jacobian9d`: AUROC `0.643 [0.604, 0.685]`, AUPRC `0.569 [0.494, 0.620]`, Brier `0.273 [0.258, 0.286]`
- `clinical_plus_eeg_plus_reachability`: AUROC `0.641 [0.613, 0.669]`, AUPRC `0.608 [0.491, 0.689]`, Brier `0.275 [0.258, 0.287]`
- `clinical_plus_eeg_plus_jacobian3d`: AUROC `0.626 [0.522, 0.698]`, AUPRC `0.564 [0.484, 0.628]`, Brier `0.286 [0.248, 0.339]`
- `clinical_plus_eeg_plus_reachability_plus_jacobian9d`: AUROC `0.668 [0.633, 0.704]`, AUPRC `0.616 [0.521, 0.678]`, Brier `0.260 [0.245, 0.278]`

## Paired delta summary

- `clinical_plus_eeg_plus_jacobian9d` vs `clinical_plus_eeg`: delta AUROC `+0.106 [+0.096, +0.115]` (paired `p = 1.852e-38`), delta AUPRC `+0.073 [+0.063, +0.082]`, delta Brier `-0.033 [-0.037, -0.030]`
- `clinical_plus_eeg_plus_reachability` vs `clinical_plus_eeg`: delta AUROC `+0.104 [+0.095, +0.113]` (paired `p = 1.892e-40`), delta AUPRC `+0.092 [+0.082, +0.101]`, delta Brier `-0.028 [-0.032, -0.025]`
- `clinical_plus_eeg_plus_reachability_plus_jacobian9d` vs `clinical_plus_eeg_plus_reachability`: delta AUROC `+0.018 [+0.013, +0.023]` (paired `p = 1.431e-09`), delta AUPRC `+0.005 [-0.001, +0.011]`, delta Brier `-0.008 [-0.010, -0.006]`

## Top combined-model coefficients

- `eeg__rawfeat_eeg_hjorth_mobility_median`: mean abs coef `0.816`, mean signed coef `-0.816`
- `reach__tube_d_eff_median`: mean abs coef `0.813`, mean signed coef `0.813`
- `eeg__rawfeat_eeg_hjorth_complexity_median`: mean abs coef `0.762`, mean signed coef `-0.762`
- `reach__tube_capture_gate_median`: mean abs coef `0.697`, mean signed coef `0.697`
- `jac9d__anisotropy_abs_eig_median`: mean abs coef `0.649`, mean signed coef `-0.649`
- `clinical__shockable_rhythm`: mean abs coef `0.532`, mean signed coef `0.532`
- `eeg__rawfeat_eeg_beta_median`: mean abs coef `0.515`, mean signed coef `-0.372`
- `jac9d__rotational_power_mean`: mean abs coef `0.513`, mean signed coef `-0.513`
- `eeg__rawfeat_eeg_alpha_median`: mean abs coef `0.507`, mean signed coef `0.487`
- `jac9d__spectral_radius_median`: mean abs coef `0.493`, mean signed coef `-0.488`
