# 9D Jacobian Robustness Summary

- n_subjects: `281`
- CPC1: `141`
- CPC5: `140`
- shockable available: `264`

## Full-cohort contrasts

- `anisotropy_abs_eig_median`: medians `0.000864763` vs `0.00101093`, `d = -0.337`, `p = 3.27e-09`
- `spectral_radius_median`: medians `0.0968183` vs `0.105434`, `d = -0.620`, `p = 3.41e-09`
- `a_operator_norm_median`: medians `0.492284` vs `0.562036`, `d = -0.227`, `p = 4.85e-07`
- `frobenius_norm_median`: medians `0.619392` vs `0.690281`, `d = -0.230`, `p = 7.53e-07`
- `rotation_norm_median`: medians `0.436162` vs `0.485421`, `d = -0.232`, `p = 9.09e-07`
- `rotational_power_mean`: medians `0.028042` vs `0.0288894`, `d = -0.285`, `p = 4.49e-05`
- `mdr_median`: medians `0.151384` vs `0.153322`, `d = -0.287`, `p = 0.000305`
- `rotational_power_median`: medians `0.0273667` vs `0.0278741`, `d = -0.260`, `p = 0.00383`

## Shockable Only

- `spectral_radius_median`: medians `0.0968183` vs `0.101802`, `d = -0.525`, `p = 0.000207`
- `rotation_norm_median`: medians `0.435826` vs `0.472896`, `d = -0.241`, `p = 0.000266`
- `frobenius_norm_median`: medians `0.618895` vs `0.67315`, `d = -0.240`, `p = 0.000287`
- `a_operator_norm_median`: medians `0.493356` vs `0.553977`, `d = -0.239`, `p = 0.000321`
- `anisotropy_abs_eig_median`: medians `0.000864763` vs `0.000972982`, `d = -0.322`, `p = 0.000341`
- `rotational_power_mean`: medians `0.028042` vs `0.028819`, `d = -0.338`, `p = 0.00513`
- `rotational_power_median`: medians `0.0273868` vs `0.0276628`, `d = -0.227`, `p = 0.0295`
- `mdr_median`: medians `0.151556` vs `0.152442`, `d = -0.139`, `p = 0.0615`

## Nonshockable Only

- `spectral_radius_median`: medians `0.095697` vs `0.110076`, `d = -0.733`, `p = 0.000152`
- `anisotropy_abs_eig_median`: medians `0.000845698` vs `0.00108184`, `d = -0.669`, `p = 0.000157`
- `rotational_power_mean`: medians `0.0279489` vs `0.0297442`, `d = -0.352`, `p = 0.00256`
- `mdr_median`: medians `0.15089` vs `0.153306`, `d = -0.546`, `p = 0.00453`
- `a_operator_norm_median`: medians `0.491386` vs `0.57497`, `d = -0.463`, `p = 0.00632`
- `rotation_norm_median`: medians `0.433483` vs `0.498702`, `d = -0.467`, `p = 0.00892`
- `frobenius_norm_median`: medians `0.615377` vs `0.708331`, `d = -0.471`, `p = 0.00933`
- `rotational_power_median`: medians `0.0272303` vs `0.0280239`, `d = -0.464`, `p = 0.026`

## QC-only model

- ROC AUC: `0.559 +/- 0.068`
- AUPRC: `0.558 +/- 0.057`
- Brier: `0.252 +/- 0.008`

## Strongest QC correlations

- `rotational_power_median` vs `channel_count_median`: rho=`-0.267`, p=`5.54e-06`
- `rotational_power_median` vs `channel_coverage_frac_median`: rho=`-0.267`, p=`5.54e-06`
- `rotational_power_mean` vs `channel_count_median`: rho=`-0.230`, p=`9.65e-05`
- `rotational_power_mean` vs `channel_coverage_frac_median`: rho=`-0.230`, p=`9.65e-05`
- `rotation_norm_median` vs `n_windows_total`: rho=`0.178`, p=`0.00277`
- `frobenius_norm_median` vs `n_windows_total`: rho=`0.175`, p=`0.0033`
- `a_operator_norm_median` vs `n_windows_total`: rho=`0.174`, p=`0.00349`
- `anisotropy_abs_eig_median` vs `n_windows_total`: rho=`0.127`, p=`0.034`

## Label permutation

- `spectral_radius_median`: observed abs `d = 0.620`, null p95 `0.237`, empirical `p = 0.0005`
- `anisotropy_abs_eig_median`: observed abs `d = 0.337`, null p95 `0.187`, empirical `p = 0.0005`
- `mdr_median`: observed abs `d = 0.287`, null p95 `0.237`, empirical `p = 0.0180`
- `rotational_power_mean`: observed abs `d = 0.285`, null p95 `0.199`, empirical `p = 0.0020`
- `rotational_power_median`: observed abs `d = 0.260`, null p95 `0.233`, empirical `p = 0.0305`
- `a_operator_norm_median`: observed abs `d = 0.227`, null p95 `0.167`, empirical `p = 0.0005`
- `frobenius_norm_median`: observed abs `d = 0.230`, null p95 `0.168`, empirical `p = 0.0005`
- `rotation_norm_median`: observed abs `d = 0.232`, null p95 `0.170`, empirical `p = 0.0005`
- `max_abs_cohens_d_across_article_metrics`: observed abs `d = 0.620`, null p95 `0.280`, empirical `p = 0.0005`

## Winsorization sensitivity

- `anisotropy_abs_eig_median`: original `d = -0.337`, winsorized `d = -0.670`
- `a_operator_norm_median`: original `d = -0.227`, winsorized `d = -0.542`
- `frobenius_norm_median`: original `d = -0.230`, winsorized `d = -0.525`
- `rotation_norm_median`: original `d = -0.232`, winsorized `d = -0.519`
- `rotational_power_mean`: original `d = -0.285`, winsorized `d = -0.392`
- `spectral_radius_median`: original `d = -0.620`, winsorized `d = -0.632`
- `mdr_median`: original `d = -0.287`, winsorized `d = -0.276`
- `rotational_power_median`: original `d = -0.260`, winsorized `d = -0.259`
