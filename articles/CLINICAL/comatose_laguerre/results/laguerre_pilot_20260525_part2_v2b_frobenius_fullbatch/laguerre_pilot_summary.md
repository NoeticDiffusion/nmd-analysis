# Laguerre Pilot V2 Summary

Batch cohort: `part2` / `0_12h`.

## Design

- Geometry is computed from subject-anchored 3D MNPS coordinates read directly from the H5 files referenced by the coma wrappers.
- This v2 batch adds shape index, curvedness, an ambient-Frobenius state-space grad-II proxy, saddle fraction, direction coherence, curvature entropy, a Mann-Kendall trend, residualization against reachability, and a trajectory-curvature negative control.
- `subjects_per_group=0` (`0` means all eligible subjects)
- `workers=8`
- `max_points_per_run=60`
- `neighborhood_size=25`
- `gradient_neighbors=8`
- `s3_over_s2_max=0.75`
- `surface_fit_r2_min=0.02`

## Cohort Triage

- eligible CPC1 subjects: 67
- eligible CPC5 subjects: 70
- selected CPC1 subjects: 67
- selected CPC5 subjects: 70

## Selected Subjects

- CPC1: sub-0985, sub-0616, sub-0877, sub-0676, sub-0722, sub-0817, sub-0549, sub-0750, sub-0928, sub-0475, ... (67 total)
- CPC5: sub-0875, sub-0831, sub-0385, sub-0536, sub-0725, sub-0570, sub-0745, sub-0441, sub-0472, sub-0749, ... (70 total)

## Effect Sizes

| Metric | CPC1 median | CPC5 median | Cohen's d | Cliff's delta | Mann-Whitney p | Direct AUROC |
|---|---:|---:|---:|---:|---:|---:|
| Reachability A-operator norm median | 1.044 | 1.134 | -0.714 | -0.443 | 7.92e-06 | 0.721 |
| Reachability d_eff median | 2.026 | 1.821 | 0.701 | 0.374 | 0.000158 | 0.687 |
| Reachability capture gate median | 0.338 | 0.380 | -0.516 | -0.266 | 0.00726 | 0.633 |
| Reachability-weighted curvedness interaction | 1.496 | 1.308 | 0.464 | 0.357 | 0.000318 | 0.678 |
| Laguerre bending-direction coherence | 0.155 | 0.176 | -0.439 | -0.247 | 0.0127 | 0.623 |
| laguerre_legacy_change_norm_median residualized vs reachability | -0.003 | 0.082 | -0.363 | -0.280 | 0.00476 | 0.640 |
| Trajectory curvature median | 0.956 | 0.919 | 0.357 | 0.287 | 0.00384 | 0.643 |
| laguerre_shape_entropy residualized vs reachability | -0.006 | 0.045 | -0.343 | -0.313 | 0.00159 | 0.657 |
| laguerre_saddle_fraction residualized vs reachability | -0.007 | 0.034 | -0.316 | -0.302 | 0.00232 | 0.651 |
| laguerre_shape_change_norm_median residualized vs reachability | -0.003 | 0.057 | -0.312 | -0.255 | 0.00996 | 0.628 |
| Legacy change norm p95 | 3.026 | 3.164 | -0.284 | -0.207 | 0.0366 | 0.604 |
| Reachability-weighted grad-II interaction | 6.233 | 5.410 | 0.279 | 0.208 | 0.0356 | 0.604 |
| Shape-only change norm p95 | 1.885 | 1.933 | -0.259 | -0.173 | 0.0808 | 0.587 |
| Laguerre curvedness p95 | 1.829 | 1.887 | -0.240 | -0.155 | 0.119 | 0.577 |
| Laguerre shape index median | 0.002 | 0.000 | 0.206 | 0.102 | 0.304 | 0.551 |
| laguerre_shape_index_median residualized vs reachability | 0.009 | 0.001 | 0.196 | 0.102 | 0.304 | 0.551 |
| laguerre_legacy_change_norm_p95 residualized vs reachability | -0.156 | -0.081 | -0.185 | -0.073 | 0.46 | 0.537 |
| laguerre_curvedness_median residualized vs reachability | -0.006 | 0.009 | -0.180 | -0.108 | 0.275 | 0.554 |

## Quick Read

- strongest raw Laguerre metric: `laguerre_curvedness_scaled_median` with Cohen's d `0.464` and direct AUROC `0.678`.
- strongest reachability-residualized Laguerre metric: `laguerre_legacy_change_norm_median_resid_reachability` with Cohen's d `-0.363` and direct AUROC `0.640`.
- reachability reference (`tube_d_eff_median`) shows Cohen's d `0.701` and direct AUROC `0.687` in the same batch.
- Residual metrics are the stricter test of whether the Laguerre layer adds information beyond reachability severity.
- Reachability-weighted metrics are interaction terms by construction, not independent geometry-only measures.
