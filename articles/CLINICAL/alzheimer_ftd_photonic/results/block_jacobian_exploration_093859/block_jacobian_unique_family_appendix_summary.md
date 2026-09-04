# Unique block-family appendix summary

- raw root: `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_ds006036_20260528_093859`
- Deduplication rule: mirrored off-diagonal pairs such as `m->d` and `d->m` are collapsed into an unordered family such as `m<->d`.
- Family-level values are formed by averaging available mirrored orientations within each subject before running statistics.
- unique-family subject-metric rows: `7919`
- corrected group rows: `41` raw pair rows -> `22` unique-family rows
- corrected MMSE rows: `1` raw pair rows -> `1` unique-family rows

## Group contrasts

- `AD_vs_Healthy` / `Regional m/d/e family block Jacobian`: 22 corrected unique families

- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / c_sym_mean / `parietal_occipital` / `m<->d`, d=-0.985, p=0.0001648, q=0.007112
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / block_frobenius_mean / `temporal` / `m<->d`, d=-0.959, p=0.000307, q=0.007112
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / c_rot_mean / `temporal` / `m<->d`, d=-0.968, p=0.0003573, q=0.007112
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / c_sym_mean / `frontal` / `m<->d`, d=-0.716, p=0.0003951, q=0.007112
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / block_frobenius_mean / `parietal_occipital` / `m->m`, d=-0.745, p=0.0005319, q=0.007474
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / c_sym_mean / `temporal` / `m<->d`, d=-0.832, p=0.0009927, q=0.007474
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / block_frobenius_mean / `frontal` / `m<->d`, d=-0.672, p=0.00104, q=0.007474
- `AD_vs_Healthy`: Regional m/d/e family block Jacobian / c_rot_mean / `parietal_occipital` / `m<->d`, d=-0.825, p=0.00109, q=0.007474

## MMSE correlations

- `FTD_only` / `Regional m/d/e family block Jacobian`: 1 corrected unique families

- `FTD_only`: Regional m/d/e family block Jacobian / block_frobenius_mean / `temporal` / `m->m`, rho=0.671, p=0.000457, q=0.03291

## Notes

- Diagonal families such as `m->m` are unchanged by this condensation step.
- Off-diagonal family labels use the unordered notation `m<->d`, `m<->e`, and `d<->e`.
- This appendix-oriented pass is easier to narrate than the raw oriented-pair surface and is the better candidate if block-Jacobian material is carried forward.
