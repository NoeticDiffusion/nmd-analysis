# Parkinson walking IQR/MAD extension

Date: 2026-06-11

## Scope

Add `IQR` and `MAD` summary statistics to the article-local `parkinson_walking`
run-level analysis stack and rerun the main contrast/clinical tables in separate
output folders so the current manuscript package is not overwritten.

## Important boundary

This dataset does **not** support a useful same-task *between-run* IQR/MAD
analysis:

- maximum runs per participant-task = `1`
- participants with more than one run in the same task = `0`

So the extension implemented here is:

- **within-run** `IQR` and `MAD` across valid windows/timepoints inside each
  run-level metric stream,
- for global and regional `MNPS` / Jacobian summaries,
- under both `cohort` and `subject` anchors.

## Output folders

Global:

- `global_cohort_121725_iqr_mad`
- `global_subject_121725_iqr_mad`

Regional:

- `regional_cohort_121725_iqr_mad`
- `regional_subject_121725_iqr_mad`

## Key findings

### Global cohort anchor

No global `IQR`/`MAD` group contrast survived:

- `0` rows at `q < 0.05`
- `0` rows at `q < 0.1`

The strongest near-miss rows were rest-side:

- `HC_vs_PD_rest / d_n_mad` (`d = -0.642`, `q = 0.180`)
- `HC_vs_PD_rest / d_n_iqr` (`d = -0.439`, `q = 0.180`)

Global cohort-anchor clinical `rho` did retain corrected rows, mainly in rest:

- `rest / age / d_s_iqr` (`rho = -0.377`, `q = 8.38e-4`)
- `rest / ctt / d_s_iqr` (`rho = -0.351`, `q = 0.00489`)
- `rest / age / d_s_mad` (`rho = -0.332`, `q = 0.00543`)
- `rest / ctt / d_s_mad` (`rho = -0.314`, `q = 0.0117`)

### Global subject anchor

The clearest new IQR/MAD signal is in the paired Parkinson branch:

- `PD_walk_vs_rest / m_a_iqr` (`d_z = 0.472`, `q = 6.55e-4`)
- `PD_walk_vs_rest / d_iqr` (`d_z = 0.403`, `q = 7.28e-4`)
- `PD_walk_vs_rest / d_mad` (`d_z = 0.412`, `q = 7.28e-4`)

Additional near-threshold rows:

- `PD_walk_vs_rest / e_s_mad` (`q = 0.0868`)
- `PD_walk_vs_rest / jac9_anisotropy_abs_eig_mad` (`q = 0.0969`)

The `HC_walk_vs_rest` branch had:

- `0` rows at `q < 0.05`
- `0` rows at `q < 0.1`

Global subject-anchor clinical `rho` produced:

- `0` corrected `IQR`/`MAD` rows at `q < 0.05`

### Regional cohort anchor

Regional cohort-anchor `IQR`/`MAD` group contrasts were stronger than the global
ones and were rest-dominant:

- `9` rows at `q < 0.05`
- `10` rows at `q < 0.1`

Leading rows:

- `HC_vs_PD_rest_regional / temporal / m_e_iqr` (`d = -0.842`, `q = 0.0375`)
- `HC_vs_PD_rest_regional / parietal_occipital / m_mad` (`d = -0.724`, `q = 0.0375`)
- `HC_vs_PD_rest_regional / temporal / m_mad` (`d = -0.646`, `q = 0.0375`)
- `HC_vs_PD_rest_regional / parietal_occipital / m_iqr` (`d = -0.705`, `q = 0.0375`)

Regional cohort-anchor clinical `rho` was especially rich:

- `63` rows at `q < 0.05`
- `106` rows at `q < 0.1`

Leading rows:

- `rest / ctt / parietal_occipital / e_iqr` (`rho = 0.439`, `q = 1.25e-4`)
- `rest / ctt / parietal_occipital / e_mad` (`rho = 0.435`, `q = 1.25e-4`)
- `rest / ctt / parietal_occipital / e_s_mad` (`rho = 0.435`, `q = 1.25e-4`)
- `rest / moca / central / e_mad` (`rho = -0.389`, `q = 0.00211`)

### Regional subject anchor

Regional subject-anchor group contrasts retained:

- `3` rows at `q < 0.05`
- `4` rows at `q < 0.1`

Leading rows:

- `HC_vs_PD_rest_regional / parietal_occipital / e_mad` (`d = -0.956`, `q = 0.00545`)
- `HC_vs_PD_rest_regional / parietal_occipital / e_iqr` (`d = -0.875`, `q = 0.00579`)
- `HC_vs_PD_walk_regional / temporal / m_mad` (`d = -0.946`, `q = 0.0203`)

Regional subject-anchor clinical `rho` retained:

- `3` rows at `q < 0.05`
- `5` rows at `q < 0.1`

Leading rows:

- `rest / updrs_total / temporal / e_iqr` (`rho = -0.338`, `q = 0.0311`)
- `rest / updrs_part_iii / temporal / e_iqr` (`rho = -0.323`, `q = 0.0396`)
- `rest / updrs_part_iii / temporal / e_mad` (`rho = -0.314`, `q = 0.0436`)

## Takeaway

The `IQR`/`MAD` extension does add real signal, but not in the same place as the
current manuscript headline:

- global cohort-anchor walk disease-state remains driven by central-tendency rows,
- paired Parkinson subject-anchor gains three strong new `IQR`/`MAD` rows,
- and the richest `IQR`/`MAD` structure appears in regional and rest-side
  analyses rather than the primary global walk headline.
