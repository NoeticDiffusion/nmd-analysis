# Pseudospectrum/Kreiss Pilot Summary

- processed roots: `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_physionet_icare_2_1_20260523_173059_part1_141sub, J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_physionet_icare_2_1_20260522_095945_part2_140sub`
- timeline dir: `J:\repos\NoeticDiffusion\articles\CLINICAL\comatose_ndt\results\timeline_analysis_20260525_combined_cpc15_primary12h`
- primary time bin: `0_12h`
- subjects: `4` (`CPC1` = `4`, `CPC5` = `0`)
- max Jacobian windows per subject: `400`
- real-axis probe points: `14`
- relative epsilons: `0.010`, `0.050`

## Top Metrics

| Metric | CPC1 median | CPC5 median | Cohen's d | Best-direction AUROC |
|---|---:|---:|---:|---:|

## Notes

- This pilot uses a coarse positive-real-axis resolvent scan, so Kreiss is reported as a lower-bound style proxy rather than an exact complex-plane supremum.
- The pseudospectral abscissa is likewise a coarse real-axis approximation using relative epsilon thresholds tied to Jacobian Frobenius scale.
- These outputs are exploratory pooled summaries rather than a full epsilon-pseudospectrum contour analysis.

