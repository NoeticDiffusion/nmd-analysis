# Pseudospectrum/Kreiss Pilot Summary

- processed roots: `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_physionet_icare_2_1_20260523_173059_part1_141sub, J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_physionet_icare_2_1_20260522_095945_part2_140sub`
- timeline dir: `J:\repos\NoeticDiffusion\articles\CLINICAL\comatose_ndt\results\timeline_analysis_20260525_combined_cpc15_primary12h`
- primary time bin: `0_12h`
- subjects: `281` (`CPC1` = `141`, `CPC5` = `140`)
- subjects with non-null 9D-derived pseudospectrum/Kreiss metrics: `141` (`CPC1` = `71`, `CPC5` = `70`); the local `part2` raw H5 root on this machine lacks `coords_9d` / `jacobian_9D`, so these pooled pilot metrics effectively reflect the subset with available 9D exports
- max Jacobian windows per subject: `400`
- real-axis probe points: `14`
- relative epsilons: `0.010`, `0.050`

## Top Metrics

| Metric | CPC1 median | CPC5 median | Cohen's d | Best-direction AUROC |
|---|---:|---:|---:|---:|
| pseudospec_abscissa_rel05_median | 0.1075 | 0.1075 | -0.686 | 0.660 |
| pseudospec_headroom_rel05_median | 0.0631 | 0.0690 | -0.579 | 0.660 |
| kreiss_realaxis_lower_median | 50.3988 | 53.0593 | -0.342 | 0.634 |
| kreiss_realaxis_lower_p95 | 654.0143 | 729.6891 | -0.335 | 0.604 |
| pseudospec_abscissa_rel01_median | 0.0599 | 0.0599 | -0.465 | 0.601 |
| resolvent_peak_realaxis_median | 3016.3809 | 3047.4842 | -0.214 | 0.534 |

## Notes

- This pilot uses a coarse positive-real-axis resolvent scan, so Kreiss is reported as a lower-bound style proxy rather than an exact complex-plane supremum.
- The pseudospectral abscissa is likewise a coarse real-axis approximation using relative epsilon thresholds tied to Jacobian Frobenius scale.
- These outputs are exploratory pooled summaries rather than a full epsilon-pseudospectrum contour analysis.

