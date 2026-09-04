# Wave1 Residual Tests

- cohort part: `part1`
- wave1 subject metrics: `J:\repos\NoeticDiffusion\articles\CLINICAL\comatose_experimental\results\wave1_geometry_pilots_20260526_part1_cpc15\subject_wave1_metrics.csv`
- subjects in merged residual frame: `141` (`CPC1` = `71`, `CPC5` = `70`)
- wave1 metrics tested: `mnj_reactivity_median, mnj_non_normality_median, mnj_henrici_departure_median, mnj_reactivity_gap_median, largest_lyapunov_per_hour, lyapunov_positive_sum_per_hour`
- controls: `spectral_radius_median, anisotropy_abs_eig_median, frobenius_norm_median, rotational_power_mean, mdr_median`

## Best Joint Residual Metrics

| Metric | Residual AUROC | Raw AUROC | Delta | R^2 |
|---|---:|---:|---:|---:|
| lyapunov_positive_sum_per_hour | 0.601 | 0.698 | -0.097 | 0.849 |
| mnj_non_normality_median | 0.555 | 0.708 | -0.153 | 0.787 |
| mnj_reactivity_median | 0.530 | 0.710 | -0.180 | 0.884 |
| mnj_reactivity_gap_median | 0.525 | 0.700 | -0.175 | 0.834 |
| mnj_henrici_departure_median | 0.520 | 0.704 | -0.184 | 0.881 |
| largest_lyapunov_per_hour | 0.516 | 0.698 | -0.182 | 0.910 |

## Strongest Spearman Correlations

- `mnj_reactivity_median`:
  - vs `frobenius_norm_median`: rho `0.949` (n=`141`)
  - vs `spectral_radius_median`: rho `0.743` (n=`141`)
- `mnj_non_normality_median`:
  - vs `frobenius_norm_median`: rho `0.948` (n=`141`)
  - vs `spectral_radius_median`: rho `0.729` (n=`141`)
- `mnj_henrici_departure_median`:
  - vs `frobenius_norm_median`: rho `0.948` (n=`141`)
  - vs `spectral_radius_median`: rho `0.718` (n=`141`)
- `mnj_reactivity_gap_median`:
  - vs `frobenius_norm_median`: rho `0.946` (n=`141`)
  - vs `spectral_radius_median`: rho `0.675` (n=`141`)
- `largest_lyapunov_per_hour`:
  - vs `spectral_radius_median`: rho `0.882` (n=`141`)
  - vs `anisotropy_abs_eig_median`: rho `0.876` (n=`141`)
- `lyapunov_positive_sum_per_hour`:
  - vs `spectral_radius_median`: rho `0.834` (n=`141`)
  - vs `anisotropy_abs_eig_median`: rho `0.805` (n=`141`)

## Notes

- Residuals are computed by joint linear regression against the established revised 9D control panel with an intercept.
- Both wave1 targets and controls are winsorized before regression, using the configured quantile bounds.
- This is a stricter test of incremental structure than the raw wave1 contrasts alone.

