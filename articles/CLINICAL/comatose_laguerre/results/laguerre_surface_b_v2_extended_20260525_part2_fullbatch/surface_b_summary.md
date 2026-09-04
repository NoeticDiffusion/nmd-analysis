# Laguerre Surface B Pilot V2 Extended

This extended v2 triangulates Surface B across log-Euclidean, spectral, and Bures-Wasserstein geometries and separates spatial from temporal deformation.

## Batch

- cohort: `part2` / `0_12h`
- selected CPC1: 67
- selected CPC5: 70
- workers: `8`
- sigma_reg_eps: `1e-06`

## Asinh Scales

- `surface_b_logeuc_spatial_grad_median` scale: `2.08819`
- `surface_b_logeuc_spatial_grad_p95` scale: `6.65558`
- `surface_b_spectral_spatial_grad_median` scale: `1.62613`
- `surface_b_spectral_spatial_grad_p95` scale: `5.84174`
- `surface_b_bures_spatial_grad_median` scale: `0.956611`
- `surface_b_bures_spatial_grad_p95` scale: `4.05611`
- `surface_b_logeuc_temporal_grad_median` scale: `157.3`
- `surface_b_logeuc_temporal_grad_p95` scale: `630.739`
- `surface_b_spectral_temporal_grad_median` scale: `123.605`
- `surface_b_spectral_temporal_grad_p95` scale: `560.609`
- `surface_b_bures_temporal_grad_median` scale: `69.7197`
- `surface_b_bures_temporal_grad_p95` scale: `443.871`

## Effect Sizes

| Metric | CPC1 median | CPC5 median | Cliff's delta | Cohen's d | Mann-Whitney p | Direct AUROC |
|---|---:|---:|---:|---:|---:|---:|
| Reachability A-operator norm median | 1.044 | 1.134 | -0.443 | -0.714 | 7.92e-06 | 0.721 |
| Surface B bures spatial grad p95 (asinh) | 0.633 | 1.242 | -0.410 | -0.266 | 3.47e-05 | 0.705 |
| Surface B bures spatial grad p95 | 2.742 | 6.446 | -0.410 | -0.200 | 3.47e-05 | 0.705 |
| Surface B spectral spatial grad median (asinh) | 0.809 | 0.993 | -0.382 | -0.223 | 0.000117 | 0.691 |
| Surface B spectral spatial grad median | 1.463 | 1.895 | -0.382 | -0.037 | 0.000117 | 0.691 |
| Surface B spectral spatial grad p95 (asinh) | 0.635 | 1.070 | -0.379 | -0.265 | 0.000133 | 0.689 |
| Surface B spectral spatial grad p95 | 3.967 | 7.510 | -0.379 | -0.200 | 0.000133 | 0.689 |
| Reachability d_eff median | 2.026 | 1.821 | 0.374 | 0.701 | 0.000158 | 0.687 |
| Surface B bures temporal grad p95 (asinh) | 0.754 | 1.137 | -0.371 | -0.491 | 0.000178 | 0.686 |
| Surface B bures temporal grad p95 | 367.039 | 621.711 | -0.371 | -0.296 | 0.000178 | 0.686 |
| Surface B logeuc spatial grad p95 (asinh) | 0.665 | 1.090 | -0.360 | -0.257 | 0.000277 | 0.680 |
| Surface B logeuc spatial grad p95 | 4.762 | 8.782 | -0.360 | -0.200 | 0.000277 | 0.680 |
| Surface B bures spatial grad median (asinh) | 0.776 | 0.969 | -0.353 | -0.255 | 0.000373 | 0.676 |
| Surface B bures spatial grad median | 0.819 | 1.078 | -0.353 | 0.012 | 0.000373 | 0.676 |
| Surface B logeuc spatial grad median (asinh) | 0.812 | 0.979 | -0.353 | -0.200 | 0.000373 | 0.676 |
| Surface B logeuc spatial grad median | 1.889 | 2.386 | -0.353 | -0.028 | 0.000373 | 0.676 |
| Surface B spectral temporal grad p95 (asinh) | 0.797 | 0.977 | -0.309 | -0.412 | 0.00184 | 0.654 |
| Surface B spectral temporal grad p95 | 495.490 | 639.488 | -0.309 | -0.267 | 0.00184 | 0.654 |
| Surface B logeuc temporal grad p95 (asinh) | 0.795 | 1.003 | -0.279 | -0.363 | 0.00489 | 0.639 |
| Surface B logeuc temporal grad p95 | 556.167 | 744.053 | -0.279 | -0.231 | 0.00489 | 0.639 |
| Reachability capture gate median | 0.338 | 0.380 | -0.266 | -0.516 | 0.00726 | 0.633 |
| Surface B spectral temporal grad median (asinh) | 0.855 | 0.936 | -0.255 | -0.344 | 0.00996 | 0.628 |
| Surface B spectral temporal grad median | 118.971 | 133.323 | -0.255 | -0.309 | 0.00996 | 0.628 |
| Surface B bures temporal grad median (asinh) | 0.839 | 0.938 | -0.230 | -0.316 | 0.0202 | 0.615 |

- Cliff's delta is the primary ranking metric here because the Surface B distributions remain heavy-tailed even after stabilization.
