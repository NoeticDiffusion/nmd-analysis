# Exploratory block-Jacobian check

- raw root: `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_ds006036_20260528_093859`
- subject-metric rows: `11879`
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
- `AD_vs_Healthy`: Global 9D block Jacobian / block_frobenius_mean / `global` / `d->m`, d=-0.966, p=0.0001134, q=0.001406
- `AD_vs_Healthy`: Global 9D block Jacobian / block_frobenius_mean / `global` / `m->e`, d=-0.737, p=0.0001563, q=0.001406
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / block_frobenius_mean / `parietal_occipital` / `m->d`, d=-0.971, p=0.0001482, q=0.005334
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / c_sym_mean / `parietal_occipital` / `d->m`, d=-0.985, p=0.0001648, q=0.005334
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / c_sym_mean / `parietal_occipital` / `m->d`, d=-0.985, p=0.0001648, q=0.005334
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / block_frobenius_mean / `frontal` / `m->d`, d=-0.661, p=0.0003573, q=0.005334
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / c_rot_mean / `temporal` / `d->m`, d=-0.968, p=0.0003573, q=0.005334

## MMSE correlations

- `FTD_only`: Regional m/d/e family block Jacobian / block_frobenius_mean / `temporal` / `m->m`, rho=0.671, p=0.000457, q=0.04936

## Notes

- This scan is run-level rather than frequency-stratified; the exported block-Jacobian contracts are whole-run summaries.
- BH-FDR is applied within `contrast x analysis_type` for group rows and within `cohort x analysis_type` for MMSE rows.
- Use this pass as a triage surface for article-vs-appendix decisions rather than as a finalized claim set.
