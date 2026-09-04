# Laguerre Surface B Pilot V2

This minimal v2 adds relative-trace SPD regularization and arcsinh-stabilized residualization.

## Batch

- cohort: `part2` / `0_12h`
- selected CPC1: 67
- selected CPC5: 70
- workers: `8`
- sigma_reg_eps: `1e-06`

## Asinh Scales

- `surface_b_logeuc_grad_median` scale: `2.08819`
- `surface_b_logeuc_grad_p95` scale: `6.65558`
- `surface_b_spectral_grad_median` scale: `1.62613`
- `surface_b_spectral_grad_p95` scale: `5.84174`

## Effect Sizes

| Metric | CPC1 median | CPC5 median | Cliff's delta | Cohen's d | Mann-Whitney p | Direct AUROC |
|---|---:|---:|---:|---:|---:|---:|
| Reachability A-operator norm median | 1.044 | 1.134 | -0.443 | -0.714 | 7.92e-06 | 0.721 |
| Surface B spectral deformation median (asinh) | 0.809 | 0.993 | -0.382 | -0.223 | 0.000117 | 0.691 |
| Surface B spectral deformation median | 1.463 | 1.895 | -0.382 | -0.037 | 0.000117 | 0.691 |
| Surface B spectral deformation p95 (asinh) | 0.635 | 1.070 | -0.379 | -0.265 | 0.000133 | 0.689 |
| Surface B spectral deformation p95 | 3.967 | 7.510 | -0.379 | -0.200 | 0.000133 | 0.689 |
| Reachability d_eff median | 2.026 | 1.821 | 0.374 | 0.701 | 0.000158 | 0.687 |
| Surface B log-Euclidean deformation p95 (asinh) | 0.665 | 1.090 | -0.360 | -0.257 | 0.000277 | 0.680 |
| Surface B log-Euclidean deformation p95 | 4.762 | 8.782 | -0.360 | -0.200 | 0.000277 | 0.680 |
| Surface B log-Euclidean deformation median (asinh) | 0.812 | 0.979 | -0.353 | -0.200 | 0.000373 | 0.676 |
| Surface B log-Euclidean deformation median | 1.889 | 2.386 | -0.353 | -0.028 | 0.000373 | 0.676 |
| Reachability capture gate median | 0.338 | 0.380 | -0.266 | -0.516 | 0.00726 | 0.633 |
| surface_b_logeuc_grad_p95_asinh residualized vs reachability | 0.099 | -0.534 | 0.215 | 0.036 | 0.0302 | 0.607 |
| surface_b_spectral_grad_p95_asinh residualized vs reachability | 0.095 | -0.518 | 0.214 | 0.038 | 0.0312 | 0.607 |
| surface_b_spectral_grad_median_asinh residualized vs reachability | 0.026 | -0.108 | 0.212 | 0.265 | 0.0325 | 0.606 |
| surface_b_logeuc_grad_median_asinh residualized vs reachability | 0.027 | -0.112 | 0.212 | 0.261 | 0.0325 | 0.606 |

- In this v2 table, Cliff's delta is the more trustworthy primary effect size because the raw Surface B distributions are heavy-tailed.
