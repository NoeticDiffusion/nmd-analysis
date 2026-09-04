# Laguerre Surface B Pilot V2

This minimal v2 adds relative-trace SPD regularization and arcsinh-stabilized residualization.

## Batch

- cohort: `part2` / `0_12h`
- selected CPC1: 1
- selected CPC5: 1
- workers: `1`
- sigma_reg_eps: `1e-06`

## Asinh Scales

- `surface_b_logeuc_grad_median` scale: `1.12158`
- `surface_b_logeuc_grad_p95` scale: `7.20274`
- `surface_b_spectral_grad_median` scale: `0.923572`
- `surface_b_spectral_grad_p95` scale: `6.4961`

## Effect Sizes

| Metric | CPC1 median | CPC5 median | Cliff's delta | Cohen's d | Mann-Whitney p | Direct AUROC |
|---|---:|---:|---:|---:|---:|---:|
| Reachability d_eff median | 2.214 | 1.215 | 1.000 | nan | 1 | 1.000 |
| Reachability A-operator norm median | 0.933 | 1.913 | -1.000 | nan | 1 | 1.000 |
| Reachability capture gate median | 0.266 | 0.381 | -1.000 | nan | 1 | 1.000 |
| Surface B log-Euclidean deformation median | 0.748 | 1.495 | -1.000 | nan | 1 | 1.000 |
| Surface B log-Euclidean deformation p95 | 1.779 | 12.626 | -1.000 | nan | 1 | 1.000 |
| Surface B spectral deformation median | 0.582 | 1.265 | -1.000 | nan | 1 | 1.000 |
| Surface B spectral deformation p95 | 1.424 | 11.568 | -1.000 | nan | 1 | 1.000 |
| Surface B log-Euclidean deformation median (asinh) | 0.626 | 1.098 | -1.000 | nan | 1 | 1.000 |
| Surface B log-Euclidean deformation p95 (asinh) | 0.245 | 1.327 | -1.000 | nan | 1 | 1.000 |
| Surface B spectral deformation median (asinh) | 0.595 | 1.120 | -1.000 | nan | 1 | 1.000 |
| Surface B spectral deformation p95 (asinh) | 0.218 | 1.341 | -1.000 | nan | 1 | 1.000 |

- In this v2 table, Cliff's delta is the more trustworthy primary effect size because the raw Surface B distributions are heavy-tailed.
