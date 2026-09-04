# Laguerre Surface B Pilot V2 Extended

This extended v2 triangulates Surface B across log-Euclidean, spectral, and Bures-Wasserstein geometries and separates spatial from temporal deformation.

## Batch

- cohort: `part2` / `0_12h`
- selected CPC1: 1
- selected CPC5: 1
- workers: `1`
- sigma_reg_eps: `1e-06`

## Asinh Scales

- `surface_b_logeuc_spatial_grad_median` scale: `1.12158`
- `surface_b_logeuc_spatial_grad_p95` scale: `7.20274`
- `surface_b_spectral_spatial_grad_median` scale: `0.923572`
- `surface_b_spectral_spatial_grad_p95` scale: `6.4961`
- `surface_b_bures_spatial_grad_median` scale: `0.414401`
- `surface_b_bures_spatial_grad_p95` scale: `8.57137`
- `surface_b_logeuc_temporal_grad_median` scale: `51.6124`
- `surface_b_logeuc_temporal_grad_p95` scale: `282.685`
- `surface_b_spectral_temporal_grad_median` scale: `41.2022`
- `surface_b_spectral_temporal_grad_p95` scale: `254.226`
- `surface_b_bures_temporal_grad_median` scale: `20.9323`
- `surface_b_bures_temporal_grad_p95` scale: `384.515`

## Effect Sizes

| Metric | CPC1 median | CPC5 median | Cliff's delta | Cohen's d | Mann-Whitney p | Direct AUROC |
|---|---:|---:|---:|---:|---:|---:|
| Reachability d_eff median | 2.214 | 1.215 | 1.000 | nan | 1 | 1.000 |
| Reachability A-operator norm median | 0.933 | 1.913 | -1.000 | nan | 1 | 1.000 |
| Reachability capture gate median | 0.266 | 0.381 | -1.000 | nan | 1 | 1.000 |
| Surface B logeuc spatial grad median | 0.748 | 1.495 | -1.000 | nan | 1 | 1.000 |
| Surface B logeuc spatial grad p95 | 1.779 | 12.626 | -1.000 | nan | 1 | 1.000 |
| Surface B logeuc spatial grad median (asinh) | 0.626 | 1.098 | -1.000 | nan | 1 | 1.000 |
| Surface B logeuc spatial grad p95 (asinh) | 0.245 | 1.327 | -1.000 | nan | 1 | 1.000 |
| Surface B spectral spatial grad median | 0.582 | 1.265 | -1.000 | nan | 1 | 1.000 |
| Surface B spectral spatial grad p95 | 1.424 | 11.568 | -1.000 | nan | 1 | 1.000 |
| Surface B spectral spatial grad median (asinh) | 0.595 | 1.120 | -1.000 | nan | 1 | 1.000 |
| Surface B spectral spatial grad p95 (asinh) | 0.218 | 1.341 | -1.000 | nan | 1 | 1.000 |
| Surface B bures spatial grad median | 0.331 | 0.498 | -1.000 | nan | 1 | 1.000 |
| Surface B bures spatial grad p95 | 0.891 | 16.251 | -1.000 | nan | 1 | 1.000 |
| Surface B bures spatial grad median (asinh) | 0.732 | 1.016 | -1.000 | nan | 1 | 1.000 |
| Surface B bures spatial grad p95 (asinh) | 0.104 | 1.396 | -1.000 | nan | 1 | 1.000 |
| Surface B logeuc temporal grad median | 57.793 | 45.432 | 1.000 | nan | 1 | 1.000 |
| Surface B logeuc temporal grad p95 | 155.336 | 410.034 | -1.000 | nan | 1 | 1.000 |
| Surface B logeuc temporal grad median (asinh) | 0.964 | 0.794 | 1.000 | nan | 1 | 1.000 |
| Surface B logeuc temporal grad p95 (asinh) | 0.525 | 1.167 | -1.000 | nan | 1 | 1.000 |
| Surface B spectral temporal grad median | 44.789 | 37.615 | 1.000 | nan | 1 | 1.000 |
| Surface B spectral temporal grad p95 | 134.640 | 373.813 | -1.000 | nan | 1 | 1.000 |
| Surface B spectral temporal grad median (asinh) | 0.942 | 0.818 | 1.000 | nan | 1 | 1.000 |
| Surface B spectral temporal grad p95 (asinh) | 0.508 | 1.178 | -1.000 | nan | 1 | 1.000 |
| Surface B bures temporal grad median | 25.348 | 16.517 | 1.000 | nan | 1 | 1.000 |

- Cliff's delta is the primary ranking metric here because the Surface B distributions remain heavy-tailed even after stabilization.
