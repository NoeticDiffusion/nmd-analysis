# APPLESEED infants

Exploratory longitudinal reanalysis of infant EEG state-space geometry. The
canonical source export is `neuralmanifolddynamics_ds003710_20260804_153346`,
and the canonical result tree is `results/appleseed_cohort_20260805/`.

## Dataset and associated publications

The source data are the public **APPLESEED Example Dataset**, OpenNeuro
`ds003710`, version `1.0.2`. The official dataset DOI is
[10.18112/openneuro.ds003710.v1.0.2](https://doi.org/10.18112/openneuro.ds003710.v1.0.2);
the versioned landing page is
[OpenNeuro ds003710](https://openneuro.org/datasets/ds003710/versions/1.0.2).
The release contains 48 EEG recording sessions from 13 infants, with
approximately 4-month test/retest sessions and longitudinal sessions at
approximately 8 and 12 months. NEMAR provides a secondary catalogue entry at
[ds003710](https://nemar.org/dataexplorer/detail?dataset_id=ds003710).

The primary article associated with the release is:

- Puglia, M. H., Slobin, J. S., & Williams, C. L. (2022). *The automated
  preprocessing pipe-line for the estimation of scale-wise entropy from EEG
  data (APPLESEED): Development and validation for use in pediatric
  populations*. Developmental Cognitive Neuroscience, 58, 101163.
  [10.1016/j.dcn.2022.101163](https://doi.org/10.1016/j.dcn.2022.101163)

The bibliography also includes related methodological and developmental
literature on entropy, infant EEG reliability, longitudinal EEG, BIDS, and
multiscale signal analysis. Puglia et al. (2020) is listed as related work
from the broader infant social-EEG research program; it is not used as a
replacement for the official dataset citation.

## Package contents

- `Early Changes in Infant EEG State-Space Geometry.typ`: main manuscript.
- `S1_Supplementary_methods.typ` through `S6_Changelog.typ`: supplements.
- `references.bib`: cited literature and dataset record.
- `results/appleseed_cohort_20260805/`: canonical derived tables, manifests,
  and figures.
- `src/`: export, analysis, event-exploration, and figure-generation scripts.
- `handover/`, `peer_review/`, and `sciencelead/`: provenance and review records.

## Building

From this directory, compile the main article or a supplement with:

```text
typst compile "Early Changes in Infant EEG State-Space Geometry.typ"
typst compile "S1_Supplementary_methods.typ"
```

Each Typst file resolves its bibliography from the local `references.bib`.
The article's claims are tied to the canonical export and result tree above;
smoke-test and superseded result trees are historical only.
