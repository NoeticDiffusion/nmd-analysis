# Laguerre Surface B Pilot V2

This minimal v2 adds relative-trace SPD regularization and arcsinh-stabilized residualization.

## Batch

- cohort: `part2` / `0_12h`
- selected CPC1: 3
- selected CPC5: 3
- workers: `1`
- sigma_reg_eps: `1e-06`

## Asinh Scales

- `surface_b_logeuc_grad_median` scale: `2.11649`
- `surface_b_logeuc_grad_p95` scale: `7.07839`
- `surface_b_spectral_grad_median` scale: `1.72356`
- `surface_b_spectral_grad_p95` scale: `6.48905`

## Effect Sizes

| Metric | CPC1 median | CPC5 median | Cliff's delta | Cohen's d | Mann-Whitney p | Direct AUROC |
|---|---:|---:|---:|---:|---:|---:|
| surface_b_logeuc_grad_median_asinh residualized vs reachability | -0.017 | -0.074 | 1.000 | 1.249 | 0.1 | 1.000 |
| Reachability d_eff median | 2.214 | 1.472 | 0.778 | 2.021 | 0.2 | 0.889 |
| Reachability A-operator norm median | 0.933 | 1.419 | -0.778 | -1.342 | 0.2 | 0.889 |
| surface_b_spectral_grad_median_asinh residualized vs reachability | -0.013 | -0.070 | 0.778 | 1.244 | 0.2 | 0.889 |
| surface_b_spectral_grad_p95_asinh residualized vs reachability | 0.010 | -0.142 | 0.778 | 1.218 | 0.2 | 0.889 |
| surface_b_logeuc_grad_p95_asinh residualized vs reachability | -0.021 | -0.157 | 0.556 | 1.233 | 0.4 | 0.778 |
| Surface B spectral deformation p95 (asinh) | 0.497 | 1.078 | -0.556 | -0.578 | 0.4 | 0.778 |
| Surface B log-Euclidean deformation p95 (asinh) | 0.538 | 1.051 | -0.556 | -0.546 | 0.4 | 0.778 |
| Surface B spectral deformation p95 | 3.356 | 8.428 | -0.556 | -0.501 | 0.4 | 0.778 |
| Surface B log-Euclidean deformation p95 | 3.998 | 8.890 | -0.556 | -0.476 | 0.4 | 0.778 |
| Surface B spectral deformation median (asinh) | 0.670 | 0.993 | -0.333 | -0.411 | 0.7 | 0.667 |
| Surface B log-Euclidean deformation median (asinh) | 0.717 | 0.982 | -0.333 | -0.356 | 0.7 | 0.667 |
| Surface B spectral deformation median | 1.242 | 2.006 | -0.333 | -0.333 | 0.7 | 0.667 |
| Surface B log-Euclidean deformation median | 1.651 | 2.430 | -0.333 | -0.291 | 0.7 | 0.667 |
| Reachability capture gate median | 0.266 | 0.372 | -0.111 | -0.269 | 1 | 0.556 |

- In this v2 table, Cliff's delta is the more trustworthy primary effect size because the raw Surface B distributions are heavy-tailed.
