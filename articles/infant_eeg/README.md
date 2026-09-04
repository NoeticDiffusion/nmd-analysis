# Cohort-Anchored Infant EEG State-Space Geometry

This folder contains the manuscript, six supplements, reproducible analysis wrappers, peer-review notes, and derived results for the artifact-masked Figshare infant EEG reanalysis.

## Canonical analysis contract

- Primary R1-R5 export: `results/figshare_infant_cohort_20260805_132612/`
- Primary source export: `data/raw/neuralmanifolddynamics_figshare_infant_eeg_20260805_132612/`
- R6 conventional-qEEG results: `06_conventional_eeg_age/` copied from the coverage-fixed re-extraction `neuralmanifolddynamics_figshare_infant_eeg_20260806_122539`; see `results/README.md`.
- Figures cited by Typst are the SVG files in the canonical `04_figures/` directory.

## Related public dataset

The source analysed in this article is the Figshare release
[`10.6084/m9.figshare.5598814.v1`](https://doi.org/10.6084/m9.figshare.5598814.v1),
not an OpenNeuro dataset. A related but distinct infant-EEG resource is
[OpenNeuro `ds004577`](https://openneuro.org/datasets/ds004577), DOI
[`10.18112/openneuro.ds004577.v1.0.1`](https://doi.org/10.18112/openneuro.ds004577.v1.0.1).
It contains 103 typically developing infants and 130 resting EEG recordings
from the first year of life, primarily during physiological sleep. Its
dataset article is Harmony et al., *Normative longitudinal EEG recordings
during sleep stage II in the first year of age* (Scientific Data, 2024),
[`10.1038/s41597-024-03606-4`](https://doi.org/10.1038/s41597-024-03606-4).
`ds004577` is documented as related context only and is not pooled with the
Figshare cohort or used to fit the MNPS anchor.

## Reproduction

Run R1-R5 against the canonical artifact-masked export:

```powershell
python src/run_infant_eeg_analysis.py `
  --data-root data/raw/neuralmanifolddynamics_figshare_infant_eeg_20260805_132612 `
  --output-root results/figshare_infant_cohort_20260805_132612
```

Run the conventional-qEEG comparator separately against the coverage-fixed export and a separate result tree:

```powershell
python src/run_infant_eeg_analysis.py `
  --data-root data/raw/neuralmanifolddynamics_figshare_infant_eeg_20260806_122539 `
  --output-root results/figshare_infant_cohort_20260806_122539 `
  --with-conventional-eeg
```

The runner refuses to use the default export for R6 and refuses to overwrite the canonical primary result tree. Before copying the resulting `06_conventional_eeg_age/` directory into the canonical tree, verify the shared MNPS/MNJ/reachability columns as documented in `results/README.md`.

## Building the manuscript

```powershell
typst compile "Cohort-Anchored Infant EEG State-Space Geometry Tracks Age in Early Infancy.typ"
typst compile S1_Supplementary_methods.typ
typst compile S2_Supplementary_data.typ
typst compile S3_Supplementary_QC_Robustness.typ
typst compile S4_Supplementary_Clinical.typ
typst compile S5_Glossary.typ
typst compile S6_Changelog.typ
```

The article is exploratory and descriptive. Coordinate positions are not treated as latent neural states, and local-dynamics nulls are not interpreted as evidence of developmental invariance.
