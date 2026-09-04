#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data - Evoked Neural Geometry Under Photic Stress in Alzheimer Disease and Frontotemporal Dementia",
  short-title: "Photic Supplementary Data",
  subtitle: "Canonical exact-block tables, rest-reference comparisons, and appendix inventories",
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

This supplement collects the data-heavy tables moved out of the main photic manuscript:

- the exact block-native stage inventory,
- the corrected group rows,
- the corrected MMSE rows,
- the rest-versus-photic reference table,
- and the run-level block-Jacobian appendix inventory.

`S2` is an audit bundle rather than the inferential headline. The main paper cites only the narrowest stable rows; the broader file-level inventories remain here for transparency.

= Exact block-native stage inventory

#figure(
  kind: table,
  table(
    columns: (1.7fr, 1.0fr, 1.0fr, 1.0fr),
    align: (left, center, center, center),
    inset: 5pt,
    table.header(
      [*Stage*],
      [*Subjects with blocks*],
      [*Block instances*],
      [*Selected windows*],
    ),
    [PHOTO 5 Hz], [85], [123], [515],
    [PHOTO 10 Hz], [83], [95], [450],
    [PHOTO 15 Hz], [84], [92], [435],
    [PHOTO 20 Hz], [86], [87], [357],
  ),
  caption: [Stage-wise exact block-native inventory from `blocknative_selection_blocks.csv`.]
) <tab-s2-stage-inventory>

= Corrected group rows

#figure(
  kind: table,
  table(
    columns: (1.45fr, 1.0fr, 1.3fr, 1.35fr, 0.9fr, 0.8fr, 0.8fr),
    align: (left, left, left, left, center, center, center),
    inset: 5pt,
    table.header(
      [*Contrast*],
      [*Frequency*],
      [*Layer*],
      [*Metric*],
      [*Network*],
      [*`d`*],
      [*`q`*],
    ),
    [AD vs Healthy], [PHOTO 20 Hz], [Global 9D MNJ], [`mdr_median`], [global], [-0.984], [0.0034],
    [AD vs Healthy], [PHOTO 10 Hz], [Global 9D MNJ], [`mdr_median`], [global], [-0.926], [0.0100],
    [AD vs Healthy], [PHOTO 15 Hz], [Global 9D MNJ], [`mdr_median`], [global], [-0.661], [0.0402],
  ),
  caption: [All corrected group rows from `group_frequency_contrasts.csv`. The canonical rerun retains only three corrected group rows, all on global `9D` `mdr_median`.]
) <tab-s2-group>

= Corrected MMSE rows

#figure(
  kind: table,
  table(
    columns: (1.35fr, 1.0fr, 1.3fr, 1.45fr, 0.9fr, 0.9fr, 0.8fr),
    align: (left, left, left, left, center, center, center),
    inset: 5pt,
    table.header(
      [*Cohort*],
      [*Frequency*],
      [*Layer*],
      [*Metric*],
      [*Network*],
      [*`rho`*],
      [*`q`*],
    ),
    [Dementia_all], [PHOTO 20 Hz], [Global 9D MNJ], [`rotational_power_median`], [global], [-0.470], [0.0020],
    [Dementia_all], [PHOTO 20 Hz], [Global 9D MNJ], [`spectral_radius_median`], [global], [-0.404], [0.0073],
    [Dementia_all], [PHOTO 20 Hz], [Global 9D MNJ], [`anisotropy_abs_eig_median`], [global], [-0.363], [0.0139],
    [AD_only], [PHOTO 5 Hz], [Global 3D MNJ], [`trace_median`], [global], [0.472], [0.0250],
    [AD_only], [PHOTO 20 Hz], [Global 9D MNJ], [`rotational_power_median`], [global], [-0.444], [0.0336],
    [AD_only], [PHOTO 20 Hz], [Global 9D MNJ], [`anisotropy_abs_eig_median`], [global], [-0.430], [0.0336],
    [Dementia_all], [PHOTO 20 Hz], [Global 9D MNJ], [`frobenius_norm_median`], [global], [-0.310], [0.0337],
    [AD_only], [PHOTO 20 Hz], [Global 9D MNJ], [`spectral_radius_median`], [global], [-0.390], [0.0452],
  ),
  caption: [All corrected MMSE rows from `mmse_correlations_summary.csv`.]
) <tab-s2-mmse>

= Resting-state reference

#figure(
  kind: table,
  table(
    columns: (1.35fr, 1.2fr, 1.0fr, 1.0fr, 0.8fr, 0.8fr),
    align: (left, left, left, center, center, center),
    inset: 5pt,
    table.header(
      [*Surface*],
      [*Condition*],
      [*Stage*],
      [*`d`*],
      [*`p`*],
      [*`q`*],
    ),
    [Global 9D MNJ], [Rest baseline], [Rest], [-0.080], [0.759], [0.909],
    [Global 9D MNJ], [Photic], [PHOTO 5 Hz], [-0.424], [0.228], [0.944],
    [Global 9D MNJ], [Photic], [PHOTO 10 Hz], [-0.926], [0.00167], [0.0100],
    [Global 9D MNJ], [Photic], [PHOTO 15 Hz], [-0.661], [0.00669], [0.0402],
    [Global 9D MNJ], [Photic], [PHOTO 20 Hz], [-0.984], [0.000564], [0.00338],
    [Global 3D MNJ], [Rest baseline], [Rest], [0.150], [0.549], [0.918],
    [Global 3D MNJ], [Photic], [PHOTO 15 Hz], [-0.611], [0.0152], [0.0912],
    [Global 3D MNJ], [Photic], [PHOTO 20 Hz], [-0.541], [0.0104], [0.0623],
  ),
  caption: [Rest-versus-photic `AD vs Healthy` reference table from `rest_vs_photic_reference/rest_vs_photic_reference.md` and the linked CSV bundle.]
) <tab-s2-rest-reference>

= Block-Jacobian appendix inventory

The run-level block-Jacobian appendix is intentionally separated from the main frequency-resolved photic surface.

#figure(
  kind: table,
  table(
    columns: (1.25fr, 1.5fr, 1.1fr, 1.0fr, 1.45fr, 1.0fr, 0.8fr),
    align: (left, left, left, left, left, center, center),
    inset: 5pt,
    table.header(
      [*Panel*],
      [*Contrast / cohort*],
      [*Network*],
      [*Family*],
      [*Metric*],
      [*Effect*],
      [*`q`*],
    ),
    [Group], [FTD vs Healthy], [parietal-occipital], [`m<->d`], [`c_sym_mean`], [`d = -1.066`], [0.0021],
    [Group], [FTD vs Healthy], [parietal-occipital], [`m<->d`], [`block_frobenius_mean`], [`d = -1.065`], [0.0021],
    [Group], [FTD vs Healthy], [parietal-occipital], [`d->d`], [`block_anisotropy_mean`], [`d = -0.646`], [0.00077],
    [Group], [AD vs Healthy], [frontal], [`m->m`], [`block_frobenius_mean`], [`d = -0.516`], [0.0041],
    [MMSE], [AD_only], [frontal], [`d->d`], [`block_frobenius_mean`], [`rho = -0.538`], [0.033],
  ),
  caption: [Representative rows from the unique-family block-Jacobian appendix surface. The condensation step reduced `55` raw corrected pair rows to `32` unique-family group rows and `5` raw MMSE rows to `4` unique-family MMSE rows.]
) <tab-s2-block-jacobian>

= Files

The tables in this supplement are backed mainly by:

- `articles/CLINICAL/alzheimer_ftd_photonic/results/blocknative_selection_blocks.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic/results/group_frequency_contrasts.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic/results/mmse_correlations_summary.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic/results/rest_vs_photic_reference/rest_vs_photic_reference.md`
- `articles/CLINICAL/alzheimer_ftd_photonic/results/block_jacobian_exploration_132747/block_jacobian_exploration_summary.md`
- `articles/CLINICAL/alzheimer_ftd_photonic/results/block_jacobian_exploration_132747/block_jacobian_unique_family_appendix_summary.md`


#bibliography("alzheimer_ftd_reference_list.bib", title: [References])