#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data - Evoked Structural Brittleness Under Photic Stimulation in Alzheimer Disease and Frontotemporal Dementia",
  short-title: "ESB Supplementary Data",
  subtitle: "Primary ESB tables, specification checks, and comparator inventories",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Scope

This supplement collects the data-heavy tables moved out of the main ESB manuscript:

- the primary ESB-2 group surface,
- the cross-fitted Healthy-template comparison,
- the specification sensitivity table,
- the axis-decomposition rows,
- the comparator panel,
- and the explicit negative-result inventory.

= Primary ESB-2 group surface

#figure(
  kind: table,
  table(
    columns: (1.45fr, 1.0fr, 0.95fr, 0.95fr, 0.85fr, 0.85fr),
    align: (left, left, center, center, center, center),
    inset: 5pt,
    table.header(
      [*Contrast*],
      [*Frequency*],
      [*Left n*],
      [*Right n*],
      [*`d`*],
      [*`q`*],
    ),
    [AD vs Healthy], [PHOTO 5 Hz], [33], [25], [0.472], [0.0923],
    [AD vs Healthy], [PHOTO 10 Hz], [34], [27], [0.493], [0.0886],
    [AD vs Healthy], [PHOTO 15 Hz], [34], [27], [0.821], [0.0063],
    [AD vs Healthy], [PHOTO 20 Hz], [23], [18], [0.069], [0.9059],
    [FTD vs Healthy], [PHOTO 5 Hz], [22], [25], [0.692], [0.0414],
    [FTD vs Healthy], [PHOTO 10 Hz], [22], [27], [0.760], [0.0276],
    [FTD vs Healthy], [PHOTO 15 Hz], [22], [27], [1.038], [0.0027],
    [FTD vs Healthy], [PHOTO 20 Hz], [12], [18], [-0.086], [0.8489],
  ),
  caption: [Primary ESB-2 group contrasts from `esb_contrasts.csv`.]
) <tab-s2-esb-main>

= Cross-fitted Healthy-template check

#figure(
  kind: table,
  table(
    columns: (1.55fr, 1.0fr, 0.95fr, 0.95fr, 0.95fr),
    align: (left, center, center, center, center),
    inset: 5pt,
    table.header(
      [*Metric version*],
      [*AD `d`*],
      [*AD `q`*],
      [*FTD `d`*],
      [*FTD `q`*],
    ),
    [Original ESB-2 at PHOTO 15 Hz], [0.821], [0.0063], [1.038], [0.0027],
    [Cross-fitted Healthy ESB-2 at PHOTO 15 Hz], [0.676], [0.0128], [0.841], [0.0073],
  ),
  caption: [PHOTO 15 Hz cross-fitted Healthy-template comparison from `qc_cross_fitted_esb2_contrasts.csv`.]
) <tab-s2-crossfit>

= Specification sensitivity

#figure(
  kind: table,
  table(
    columns: (1.9fr, 1.3fr, 1.0fr, 1.0fr, 1.4fr),
    align: (left, left, center, center, left),
    inset: 5pt,
    table.header(
      [*Specification*],
      [*Contrast*],
      [*`d`*],
      [*`q`*],
      [*Interpretation*],
    ),
    [Posterior capacity + global guidance], [AD vs Healthy], [0.821], [0.0063], [Primary and strongest realized surface],
    [Posterior capacity + global guidance], [FTD vs Healthy], [1.038], [0.0027], [Primary and strongest realized surface],
    [Posterior capacity + frontal guidance], [AD vs Healthy], [0.557], [0.0249], [Weaker guidance variant],
    [Posterior capacity + frontal guidance], [FTD vs Healthy], [0.138], [0.8328], [Does not stabilize FTD separation],
    [Global capacity + global guidance], [PHOTO 15 Hz], [n/a], [n/a], [Planned branch did not yield analyzable primary-stage contrasts],
  ),
  caption: [Specification sensitivity from `qc_spec_sensitivity_summary.csv`.]
) <tab-s2-spec>

= Axis decomposition

#figure(
  kind: table,
  table(
    columns: (1.55fr, 1.25fr, 1.0fr, 0.9fr, 0.9fr, 0.8fr, 0.8fr),
    align: (left, left, left, center, center, center, center),
    inset: 5pt,
    table.header(
      [*Axis*],
      [*Contrast*],
      [*Frequency*],
      [*Left n*],
      [*Right n*],
      [*`d`*],
      [*`q`*],
    ),
    [`delta_capacity_rest`], [AD vs Healthy], [PHOTO 5 Hz], [33], [25], [-0.438], [0.0291],
    [`delta_capacity_rest`], [AD vs Healthy], [PHOTO 10 Hz], [34], [27], [-0.652], [0.0071],
    [`delta_capacity_rest`], [AD vs Healthy], [PHOTO 15 Hz], [34], [27], [-0.631], [0.0118],
    [`delta_guidance_rest`], [AD vs Healthy], [PHOTO 15 Hz], [34], [27], [0.456], [0.4507],
    [`delta_capacity_rest`], [FTD vs Healthy], [PHOTO 15 Hz], [22], [27], [-0.392], [0.1624],
    [`delta_guidance_rest`], [FTD vs Healthy], [PHOTO 15 Hz], [22], [27], [0.113], [0.7861],
  ),
  caption: [Representative axis-decomposition rows from `esb_axis_contrasts.csv`. The corrected axis-only signal is concentrated on the AD capacity branch.]
) <tab-s2-axis>

= Conventional comparator panel

#figure(
  kind: table,
  table(
    columns: (1.8fr, 0.9fr, 0.9fr, 0.9fr, 0.9fr, 0.9fr, 0.9fr),
    align: (left, center, center, center, center, center, center),
    inset: 5pt,
    table.header(
      [*Comparator*],
      [*AD `d`*],
      [*AD `q`*],
      [*FTD `d`*],
      [*FTD `q`*],
      [*`rho` all*],
      [*`rho` disease*],
    ),
    [Stage-matched posterior band-power proxy], [0.619], [0.0016], [0.161], [0.171], [0.098], [-0.067],
    [Posterior alpha power], [0.681], [0.0016], [0.463], [0.136], [0.182], [0.033],
    [Posterior alpha/theta ratio], [0.042], [0.129], [-0.180], [0.802], [0.169], [0.228],
    [Posterior sample entropy], [-0.399], [0.129], [-0.165], [0.802], [-0.148], [-0.023],
  ),
  caption: [PHOTO 15 Hz comparator summary from `conventional_comparator_contrasts.csv` and `conventional_comparator_esb2_correlations.csv`.]
) <tab-s2-comparators>

= Explicit negative-result inventory

#figure(
  kind: table,
  table(
    columns: (1.1fr, 1.25fr, 1.2fr, 0.9fr, 0.8fr, 1.8fr),
    align: (left, left, left, center, center, left),
    inset: 5pt,
    table.header(
      [*Family*],
      [*Contrast*],
      [*Best scope*],
      [*Best `d`*],
      [*Best `q`*],
      [*Interpretation*],
    ),
    [ESB2], [AD vs FTD], [PHOTO 15 Hz], [0.356], [0.313], [No corrected disease-vs-disease ESB-2 row was retained.],
    [PRL], [AD vs Healthy], [profile_all], [-0.388], [0.270], [The first PRL implementation did not yield a corrected article-level group row.],
    [PRL], [FTD vs Healthy], [profile_all], [-0.372], [0.365], [The first PRL implementation did not yield a corrected article-level group row.],
    [PRL], [AD vs FTD], [profile_all], [0.193], [0.669], [The profile score did not support disease-vs-disease separation either.],
  ),
  caption: [Explicit negative-result inventory from `negative_results_summary.csv`.]
) <tab-s2-negative>

= Files

The tables in this supplement are backed mainly by:

- `articles/CLINICAL/alzheimer_ftd_photonic_esb/results/esb_contrasts.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic_esb/results/qc_cross_fitted_esb2_contrasts.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic_esb/results/qc_spec_sensitivity_summary.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic_esb/results/esb_axis_contrasts.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic_esb/results/conventional_comparator_contrasts.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic_esb/results/conventional_comparator_esb2_correlations.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic_esb/results/negative_results_summary.csv`


#bibliography("alzheimer_ftd_reference_list.bib", title: [References])