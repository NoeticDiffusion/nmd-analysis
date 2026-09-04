# Wave 1 Geometry Pilots Summary

- processed root: `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_physionet_icare_2_1_20260523_173059_part1_141sub`
- timeline dir: `J:\repos\NoeticDiffusion\articles\CLINICAL\comatose_ndt\results\timeline_analysis_20260525_part1_primary12h`
- primary time bin: `0_12h`
- subjects: `141` (`CPC1` = `71`, `CPC5` = `70`)
- max chaos points per subject: `4000`
- max Lyapunov windows per subject: `2500`
- burst quantile: `0.90`

## Top Metrics

| Metric | CPC1 median | CPC5 median | Cohen's d | Best-direction AUROC |
|---|---:|---:|---:|---:|
| mnj_reactivity_median | 0.2432 | 0.2846 | -0.604 | 0.710 |
| mnj_non_normality_median | 0.3337 | 0.4596 | -0.562 | 0.708 |
| mnj_henrici_departure_median | 0.5691 | 0.6440 | -0.588 | 0.704 |
| mnj_reactivity_gap_median | 0.1751 | 0.2047 | -0.603 | 0.700 |
| lyapunov_positive_sum_per_hour | 431.0199 | 482.5422 | -0.653 | 0.698 |
| largest_lyapunov_per_hour | 129.1356 | 144.9435 | -0.649 | 0.698 |

## Notes

- The Lyapunov output is a pilot-style linearized discrete approximation built from `I + J_t * dt` rather than a fully re-estimated trajectory Jacobian flow.
- The non-normal block reports cheap transient proxies (`non_normality`, Henrici departure, numerical-abscissa-style reactivity) instead of a full epsilon-pseudospectrum sweep.
- These outputs are internal exploratory summaries on the `part1` cohort, not frozen validation results.

