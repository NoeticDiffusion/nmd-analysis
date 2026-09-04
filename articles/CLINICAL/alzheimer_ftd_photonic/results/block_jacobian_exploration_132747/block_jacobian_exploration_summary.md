# Exploratory block-Jacobian check

- raw root: `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_ds006036_20260604_132747`
- subject-metric rows: `11716`
- surfaces: `Global 9D block Jacobian, Regional m/d/e family block Jacobian`

## Coverage

- `Global 9D block Jacobian` / `block_anisotropy_mean`: 88 subjects
- `Global 9D block Jacobian` / `block_frobenius_mean`: 88 subjects
- `Global 9D block Jacobian` / `block_trace_mean`: 88 subjects
- `Global 9D block Jacobian` / `c_rot_mean`: 88 subjects
- `Global 9D block Jacobian` / `c_sym_mean`: 88 subjects
- `Regional m/d/e family block Jacobian` / `block_anisotropy_mean`: 88 subjects
- `Regional m/d/e family block Jacobian` / `block_frobenius_mean`: 88 subjects
- `Regional m/d/e family block Jacobian` / `block_trace_mean`: 88 subjects
- `Regional m/d/e family block Jacobian` / `c_rot_mean`: 88 subjects
- `Regional m/d/e family block Jacobian` / `c_sym_mean`: 88 subjects

## Group contrasts

- `AD_vs_Healthy`: Global 9D block Jacobian / block_frobenius_mean / `global` / `d->e`, d=-1.171, p=1.72e-06, q=4.643e-05
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / block_frobenius_mean / `frontal` / `m->d`, d=-0.673, p=2.893e-06, q=0.0002447
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / block_frobenius_mean / `temporal` / `m->d`, d=-0.843, p=4.531e-06, q=0.0002447
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / block_frobenius_mean / `parietal_occipital` / `m->d`, d=-0.878, p=2.208e-05, q=0.0007948
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / block_frobenius_mean / `parietal_occipital` / `e->d`, d=-0.743, p=4.174e-05, q=0.001127
- `FTD_vs_Healthy`: Regional m/d/e family block Jacobian / block_anisotropy_mean / `parietal_occipital` / `d->d`, d=-0.646, p=1.066e-05, q=0.001151
- `AD_vs_Healthy`: Global 9D block Jacobian / block_frobenius_mean / `global` / `d->m`, d=-0.966, p=0.0001134, q=0.001406
- `AD_vs_Healthy`: Global 9D block Jacobian / block_frobenius_mean / `global` / `m->e`, d=-0.737, p=0.0001563, q=0.001406

## MMSE correlations

- `AD_only`: Regional m/d/e family block Jacobian / block_frobenius_mean / `frontal` / `d->d`, rho=-0.538, p=0.0007063, q=0.04014
- `AD_only`: Regional m/d/e family block Jacobian / c_rot_mean / `frontal` / `d->m`, rho=-0.505, p=0.001687, q=0.04014
- `AD_only`: Regional m/d/e family block Jacobian / c_rot_mean / `frontal` / `m->d`, rho=-0.505, p=0.001687, q=0.04014
- `AD_only`: Regional m/d/e family block Jacobian / c_sym_mean / `frontal` / `d->m`, rho=-0.501, p=0.001858, q=0.04014
- `AD_only`: Regional m/d/e family block Jacobian / c_sym_mean / `frontal` / `m->d`, rho=-0.501, p=0.001858, q=0.04014

## Notes

- This scan is run-level rather than frequency-stratified; the exported block-Jacobian contracts are whole-run summaries.
- BH-FDR is applied within `contrast x analysis_type` for group rows and within `cohort x analysis_type` for MMSE rows.
- Use this pass as a triage surface for article-vs-appendix decisions rather than as a finalized claim set.
