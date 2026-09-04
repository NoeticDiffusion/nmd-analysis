# Laguerre Surface B Pilot

This pilot estimates deformation of per-window reachability covariance objects rather than point-cloud patch curvature.

## Batch

- cohort: `part2` / `0_12h`
- selected CPC1: 67
- selected CPC5: 70
- workers: `8`
- max_points_per_run: `300`
- reachability_k: `25`
- reachability_horizon: `4`

## Effect Sizes

| Metric | CPC1 median | CPC5 median | Cohen's d | Cliff's delta | Mann-Whitney p | Direct AUROC |
|---|---:|---:|---:|---:|---:|---:|
| Reachability A-operator norm median | 1.044 | 1.134 | -0.714 | -0.443 | 7.92e-06 | 0.721 |
| Reachability d_eff median | 2.026 | 1.821 | 0.701 | 0.374 | 0.000158 | 0.687 |
| Reachability capture gate median | 0.338 | 0.380 | -0.516 | -0.266 | 0.00726 | 0.633 |
| surface_b_logeuc_grad_median residualized vs reachability | 0.043 | -1.869 | 0.242 | 0.263 | 0.00804 | 0.631 |
| surface_b_spectral_grad_median residualized vs reachability | -0.012 | -1.625 | 0.239 | 0.270 | 0.00654 | 0.635 |
| Surface B spectral deformation p95 | 3.967 | 7.510 | -0.203 | -0.380 | 0.000126 | 0.690 |
| Surface B log-Euclidean deformation p95 | 4.762 | 8.782 | -0.202 | -0.360 | 0.000281 | 0.680 |
| surface_b_spectral_grad_p95 residualized vs reachability | 643045.728 | -15573899.095 | -0.089 | 0.202 | 0.0419 | 0.601 |
| surface_b_logeuc_grad_p95 residualized vs reachability | 855960.063 | -20878002.725 | -0.088 | 0.202 | 0.0419 | 0.601 |
| Surface B spectral deformation median | 1.463 | 1.895 | -0.045 | -0.381 | 0.000119 | 0.691 |
| Surface B log-Euclidean deformation median | 1.889 | 2.386 | -0.036 | -0.353 | 0.000373 | 0.676 |
