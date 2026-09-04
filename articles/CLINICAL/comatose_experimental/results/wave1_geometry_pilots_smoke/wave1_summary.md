# Wave 1 Geometry Pilots Summary

- processed root: `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_physionet_icare_2_1_20260523_173059_part1_141sub`
- timeline dir: `J:\repos\NoeticDiffusion\articles\CLINICAL\comatose_ndt\results\timeline_analysis_20260525_part1_primary12h`
- primary time bin: `0_12h`
- subjects: `2` (`CPC1` = `2`, `CPC5` = `0`)
- max chaos points per subject: `4000`
- max Lyapunov windows per subject: `2500`
- burst quantile: `0.90`

## Top Metrics

| Metric | CPC1 median | CPC5 median | Cohen's d | Best-direction AUROC |
|---|---:|---:|---:|---:|

## Notes

- The Lyapunov output is a pilot-style linearized discrete approximation built from `I + J_t * dt` rather than a fully re-estimated trajectory Jacobian flow.
- The non-normal block reports cheap transient proxies (`non_normality`, Henrici departure, numerical-abscissa-style reactivity) instead of a full epsilon-pseudospectrum sweep.
- These outputs are internal exploratory summaries on the `part1` cohort, not frozen validation results.

