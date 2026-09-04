# Unique block-family appendix summary

- raw root: `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_ds006036_20260603_141859`
- Deduplication rule: mirrored off-diagonal pairs such as `m->d` and `d->m` are collapsed into an unordered family such as `m<->d`.
- Family-level values are formed by averaging available mirrored orientations within each subject before running statistics.
- unique-family subject-metric rows: `7783`
- corrected group rows: `55` raw pair rows -> `32` unique-family rows
- corrected MMSE rows: `5` raw pair rows -> `5` unique-family rows

## Group contrasts

- `AD_vs_Healthy` / `Regional m/d/e family block Jacobian`: 14 corrected unique families
- `FTD_vs_Healthy` / `Regional m/d/e family block Jacobian`: 18 corrected unique families

- `FTD_vs_Healthy`: Regional m/d/e family block Jacobian / block_anisotropy_mean / `parietal_occipital` / `d->d`, d=-0.646, p=1.066e-05, q=0.0007673
- `FTD_vs_Healthy`: Regional m/d/e family block Jacobian / block_frobenius_mean / `frontal` / `d->d`, d=-0.251, p=4.31e-05, q=0.001533
- `FTD_vs_Healthy`: Regional m/d/e family block Jacobian / block_anisotropy_mean / `frontal` / `d->d`, d=-0.250, p=6.386e-05, q=0.001533
- `FTD_vs_Healthy`: Regional m/d/e family block Jacobian / c_sym_mean / `parietal_occipital` / `m<->d`, d=-1.066, p=0.000127, q=0.002051
- `FTD_vs_Healthy`: Regional m/d/e family block Jacobian / block_frobenius_mean / `parietal_occipital` / `m<->d`, d=-1.065, p=0.0001587, q=0.002051
- `FTD_vs_Healthy`: Regional m/d/e family block Jacobian / block_frobenius_mean / `frontal` / `m<->d`, d=-0.254, p=0.0001709, q=0.002051
- `FTD_vs_Healthy`: Regional m/d/e family block Jacobian / c_rot_mean / `parietal_occipital` / `m<->d`, d=-1.026, p=0.0002839, q=0.00292
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / block_frobenius_mean / `frontal` / `m->m`, d=-0.516, p=0.0001648, q=0.004077

## MMSE correlations

- `AD_only` / `Regional m/d/e family block Jacobian`: 5 corrected unique families

- `AD_only`: Regional m/d/e family block Jacobian / block_frobenius_mean / `frontal` / `d->d`, rho=-0.538, p=0.0007063, q=0.03345
- `AD_only`: Regional m/d/e family block Jacobian / block_frobenius_mean / `frontal` / `m<->d`, rho=-0.512, p=0.001423, q=0.03345
- `AD_only`: Regional m/d/e family block Jacobian / c_rot_mean / `frontal` / `m<->d`, rho=-0.505, p=0.001687, q=0.03345
- `AD_only`: Regional m/d/e family block Jacobian / c_sym_mean / `frontal` / `m<->d`, rho=-0.501, p=0.001858, q=0.03345
- `AD_only`: Regional m/d/e family block Jacobian / block_frobenius_mean / `temporal` / `m<->d`, rho=-0.475, p=0.003452, q=0.04971

## Notes

- Diagonal families such as `m->m` are unchanged by this condensation step.
- Off-diagonal family labels use the unordered notation `m<->d`, `m<->e`, and `d<->e`.
- This appendix-oriented pass is easier to narrate than the raw oriented-pair surface and is the better candidate if block-Jacobian material is carried forward.
