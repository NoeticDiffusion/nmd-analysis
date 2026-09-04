#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness - Evoked Neural Geometry Under Photic Stress in Alzheimer Disease and Frontotemporal Dementia",
  short-title: "Photic Supplementary QC",
  subtitle: "Selection audit, resting-reference checks, and appendix boundary conditions",
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

This supplement collects the robustness and cautionary material intentionally compressed in the main photic paper:

- why the exact block-native surface is more defensible than the older recovery-centric surface,
- what the ds004504 resting-reference actually tests,
- how narrow the corrected group surface remains,
- how the run-level block-Jacobian appendix should be bounded,
- and what negative findings should remain explicit.

= Why the exact block-native surface is stronger

The central methodological change is inferential rather than cosmetic. The article now reads the block contract already present in the H5 bundle and keeps original windows whose centers fall within exact photic intervals.

This is stronger than the earlier recovery-centric surface because:

1. it removes recovery-expanded windows from the main inferential path,
2. it ties stage inclusion to explicit block intervals already stored in the processed bundle,
3. it keeps the manuscript surface auditable through `blocknative_selection_blocks.csv` and `blocknative_selection_summary.json`.

The practical cost is modest. The canonical rerun still retains `1757` selected windows across `397` block instances in `88` subjects, so the four-frequency surface remains broad enough for the same article questions.

= Resting-state reference as a negative control

The ds004504 branch is a deliberately narrow negative control rather than a second full article.

#figure(
  kind: table,
  table(
    columns: (1.3fr, 1.2fr, 1.0fr, 0.8fr, 0.8fr),
    align: (left, left, left, center, center),
    inset: 5pt,
    table.header(
      [*Surface*],
      [*Condition*],
      [*Stage*],
      [*`d`*],
      [*`q`*],
    ),
    [Global 9D MNJ], [Rest baseline], [Rest], [-0.080], [0.909],
    [Global 9D MNJ], [Photic], [PHOTO 10 Hz], [-0.926], [0.0100],
    [Global 9D MNJ], [Photic], [PHOTO 15 Hz], [-0.661], [0.0402],
    [Global 9D MNJ], [Photic], [PHOTO 20 Hz], [-0.984], [0.0034],
    [Global 3D MNJ], [Rest baseline], [Rest], [0.150], [0.918],
    [Global 3D MNJ], [Photic strongest], [PHOTO 15 Hz], [-0.611], [0.0912],
  ),
  caption: [The ds004504 reference stays near null on the shared `9D` `mdr_median` surface while the photic `10/15/20 Hz` rows remain materially larger. The same pattern is present, but weaker, on the overlapping `3D` surface.]
) <tab-s3-rest-negative-control>

This does not prove that photic forcing is universally superior to rest. It does show that the specific shared-surface `AD vs Healthy` `mdr_median` effect promoted in the main paper is much weaker at baseline.

= Negative group findings remain explicit

The corrected group surface is intentionally narrow:

1. corrected rows = `3`,
2. all corrected rows = `AD vs Healthy`,
3. all corrected rows = global `9D` MNJ `mdr_median`,
4. corrected `FTD vs Healthy` rows = `0`,
5. corrected `AD vs FTD` rows = `0`.

The strongest near-miss descriptive regional row in the main photic inventory is not promoted to a headline finding. This is important for review stability: the manuscript is not hiding a broader positive result surface.

= MMSE surface changed materially in the canonical rerun

The updated exact block-native rerun does *not* preserve the older FTD-heavy MMSE picture. Instead:

1. corrected MMSE rows = `8`,
2. pooled dementia contributes the strongest cluster at `PHOTO 20 Hz` global `9D` MNJ,
3. `AD_only` contributes one `PHOTO 5 Hz` global `3D` row and three `PHOTO 20 Hz` global `9D` rows,
4. corrected `FTD_only` rows = `0`.

This shift is why the main paper now audits a pooled-dementia `PHOTO 20 Hz` row in Figure 4 instead of the older FTD-specific scatter.

= Block-Jacobian appendix boundary

The run-level block-Jacobian scan remains useful, but it should stay in the appendix.

#figure(
  kind: table,
  table(
    columns: (1.5fr, 1.0fr, 1.0fr, 1.4fr),
    align: (left, center, center, left),
    inset: 5pt,
    table.header(
      [*Quantity*],
      [*Raw*],
      [*Unique-family*],
      [*Interpretation*],
    ),
    [Corrected group rows], [55], [32], [Mirrored off-diagonal pairs collapse materially but the appendix still retains non-trivial regional family structure.],
    [Corrected MMSE rows], [5], [4], [The MMSE appendix survives condensation but remains too small and too run-level for headline promotion.],
  ),
  caption: [Condensation summary from `block_jacobian_unique_family_appendix_summary.md`.]
) <tab-s3-block-family>

The appendix is kept supplementary for three reasons:

1. it is run-level rather than frequency-stratified,
2. it is dominated by regional family rows rather than the main manuscript's global frequency-specific surface,
3. and the global `9D` block-Jacobian branch does not remain central after mirrored-pair condensation.

= Review-facing caution points

1. The H5 block intervals are dataset-derived contracts rather than an independently audited raw stimulus log.
2. The main paper still supports only `PHOTO 5/10/15/20 Hz`; support above `20 Hz` remains too sparse.
3. The realized regional surface has only four regions (`frontal`, `central`, `parietal_occipital`, `temporal`).
4. Stage-wise cell sizes become modest once the cohort is split by diagnosis and frequency.
5. The ds004504 branch is intentionally narrow and should not be read as an exhaustive rest-versus-photic atlas.
6. Corrected group rows are much sparser than corrected MMSE rows, so between-group claims should remain narrower than symptom-linked claims.
7. Part of the evoked `AD vs Healthy` difference could reflect retinal or early visual degradation rather than cortical manifold failure alone.

= Files

The QC and robustness claims in this supplement are backed mainly by:

- `articles/CLINICAL/alzheimer_ftd_photonic/results/blocknative_selection_summary.json`
- `articles/CLINICAL/alzheimer_ftd_photonic/results/blocknative_selection_blocks.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic/results/rest_vs_photic_reference/rest_vs_photic_reference.md`
- `articles/CLINICAL/alzheimer_ftd_photonic/results/group_frequency_contrasts.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic/results/mmse_correlations_summary.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic/results/block_jacobian_exploration_132747/block_jacobian_exploration_summary.md`
- `articles/CLINICAL/alzheimer_ftd_photonic/results/block_jacobian_exploration_132747/block_jacobian_unique_family_appendix_summary.md`


#bibliography("alzheimer_ftd_reference_list.bib", title: [References])