# Wave1 Lyapunov v2 Summary

- processed roots: `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_physionet_icare_2_1_20260523_173059_part1_141sub`
- timeline dir: `J:\repos\NoeticDiffusion\articles\CLINICAL\comatose_ndt\results\timeline_analysis_20260525_part1_primary12h`
- primary time bin: `0_12h`
- subjects: `141` (`CPC1` = `71`, `CPC5` = `70`)
- max Lyapunov windows per run: `128`
- max step seconds: `120.0`
- max expm argument: `50.0`
- mean observed Lyapunov horizon per subject (hours): `10.297`

## Lyapunov v2 Contrasts

| Metric | CPC1 median | CPC5 median | Cohen's d | Best-direction AUROC |
|---|---:|---:|---:|---:|
| lyapunov_positive_sum_v2_per_hour | 418.4787 | 470.7629 | -0.558 | 0.687 |
| largest_lyapunov_v2_per_hour | 193.9176 | 222.5550 | -0.605 | 0.686 |
| kaplan_yorke_dimension_v2 | 8.9901 | 8.9805 | 0.188 | 0.524 |

## V1 vs V2

| V1 metric | V2 metric | Spearman rho | V1 AUROC | V2 AUROC | Delta |
|---|---|---:|---:|---:|---:|
| largest_lyapunov_per_hour | largest_lyapunov_v2_per_hour | 0.894 | 0.698 | 0.686 | -0.011 |
| lyapunov_positive_sum_per_hour | lyapunov_positive_sum_v2_per_hour | 0.865 | 0.698 | 0.687 | -0.012 |
| kaplan_yorke_dimension | kaplan_yorke_dimension_v2 | 0.134 | 0.525 | 0.524 | -0.001 |

## Notes

- V2 estimates use per-run QR iteration over `exp(J dt)` rather than `I + J dt`.
- Cross-run temporal gaps are excluded by resetting the QR state at each run.
- Large within-run time gaps beyond the configured threshold are skipped.
