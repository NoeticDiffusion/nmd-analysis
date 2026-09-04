#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Evoked Neural Geometry Under Photic Stress in Alzheimer Disease and Frontotemporal Dementia",
  short-title: "Photic AD and FTD Geometry",
  subtitle: "A Frequency-Resolved EEG Study with Resting-State Reference",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "Alzheimer disease",
    "frontotemporal dementia",
    "photic stimulation",
    "EEG",
    "reachability",
    "MNJ",
    "MMSE",
  ),
  article-type: "Research Article / Compact Empirical Report",
  abstract: [
    We analyzed the ds006036 eyes-open photic-stimulation EEG cohort with the canonical exact-block/native-block rerun rooted at `data/raw/neuralmanifolddynamics_ds006036_20260604_132747`, pairing the same cohort with a matched ds004504 resting-state reference on the overlapping global MNJ `mdr_median` surface. The article now keeps the original exported windows whose centers fall inside inferred H5 photic blocks, yielding `1757` selected windows across `397` block instances on the frozen `5/10/15/20 Hz` surface. All corrected group rows localized to `AD vs Healthy` global `9D` MNJ `mdr_median`, strongest at `PHOTO 20 Hz` ($d = -0.984$, $q = 0.0034$), with additional corrected `PHOTO 10 Hz` and `PHOTO 15 Hz` rows; no corrected `FTD vs Healthy` or `AD vs FTD` group contrast survived FDR. On the matched ds004504 resting-state baseline, the same `AD vs Healthy` `9D` `mdr_median` contrast was near null ($d = -0.080$, $q = 0.909$), so the shared-surface separation remained specific to photic driving rather than baseline alone. MMSE structure was broader than the group surface but shifted relative to the older recovery-centric rerun: eight corrected severity rows survived, led by pooled-dementia `PHOTO 20 Hz` global `9D` MNJ `rotational_power_median` ($rho = -0.470$, $q = 0.0020$). The bounded conclusion is that the exact-block/native-block rerun preserves a narrow but stable AD-versus-Healthy evoked MNJ signal while leaving broader severity structure mainly on high-frequency global `9D` MNJ metrics rather than on a disease-dissociation surface.
  ],
  data-availability: [
    The manuscript-facing result bundle is stored under `articles/CLINICAL/alzheimer_ftd_photonic/results/`, with figure assets under `articles/CLINICAL/alzheimer_ftd_photonic/figures/`. Core outputs include `paper_exports_manifest.json`, `blocknative_selection_blocks.csv`, `blocknative_selection_summary.json`, `subject_stage_region_metrics.csv`, `group_frequency_contrasts.csv`, `mmse_correlations_summary.csv`, `results/rest_vs_photic_reference/`, `results/block_jacobian_exploration_132747/`, and `figure_manifest.json`. Extended methods, tables, robustness material, and clinician-facing interpretation are split into the standalone supplement files `S1_Supplementary_Methods.typ`, `S2_Supplementary_Data.typ`, `S3_Supplementary_QC_Robustness.typ`, and `S4_Supplementary_Clinical.typ`.
  ],
  competing-interests: [
    No competing interests are declared in this manuscript.
  ],
)

= Introduction

Clinically, Alzheimer disease and frontotemporal dementia are distinct but partially overlapping neurodegenerative syndromes, and EEG remains attractive as a comparatively inexpensive, non-invasive readout of functional change in both conditions @mckhann2011 @rascovsky2011 @nardone2018.

Intermittent photic stimulation offers a different perturbation frame from resting-state analysis. In human EEG, rhythmic visual flicker can elicit frequency-tagged responses across a broad range of stimulation rates and can entrain ongoing oscillations under appropriate conditions @herrmann2001 @notbohm2016. Instead of asking only how dementia reshapes spontaneous neural geometry, the photic dataset asks whether external rhythmic driving reveals frequency-specific changes in local capacity and local-linear dynamics that remain muted at baseline.

In this manuscript, "photic stress" is used in the dynamical-systems sense of a structured perturbation, not as a claim about subjective stress or systemic stress physiology.

That perturbational frame is also biologically interesting because AD and bvFTD do not emphasize identical large-scale systems: AD more strongly affects posterior default-mode and temporoparietal vulnerability patterns, whereas bvFTD disproportionately impacts frontal-insular and salience-network organization @jagust2018 @seeley2009 @zhou2010.

This standalone report applies an article-local NeuralManifoldDynamics 2.1 export workflow @langell2026_mndm within the broader Noetic Diffusion framing @langell2025_6 to the ds006036 photic EEG cohort (`Healthy`, `AD`, `FTD`) @ds006036_1_0_6 and pairs it with an article-local ds004504 resting-state reference @ds004504_1_0_9 on the overlapping global MNJ `mdr_median` surface. The canonical rerun now freezes exact block-native photic selection from the `20260604_132747` ds006036 bundle. The aim is intentionally narrow and bounded by the validated analysis contract:

1. Can exact-block/native-block `5/10/15/20 Hz` photic selection reveal any defensible group separation in reachability or MNJ metrics?
2. Do the same evoked metrics align with MMSE within the dementia cohort or within specific diagnoses?
3. On the exact overlapping MNJ surface, is the main `AD vs Healthy` effect weaker at rest than under photic driving?

This is not presented as a general photic biomarker paper. It is an auditable report on one photic export together with one explicit resting-state reference layer. Extended methods, inventories, QC, and clinician-facing interpretation are split into standalone `S1`-`S4` supplements so the main paper can stay focused on the review-stable claim surface.

For readers not already familiar with Noetic Diffusion Theory, the operational layer used here is narrower than the full theory. NeuralManifoldDynamics exports short-window EEG summaries into fixed `3D` and `9D` measurement charts, and the local Jacobian summarizes how the charted dynamics change around each windowed state. The manuscript tests group and MMSE structure on those exported chart-level summaries; it does not claim direct access to the full latent process proposed by the broader NDT framework.

= Methods

== Cohort

The local participant table contains `88` participants: `29 Healthy`, `36 AD`, and `23 FTD`.

#figure(
  kind: table,
  table(
    columns: (2.0fr, 0.8fr, 1.1fr, 1.1fr, 1.3fr, 1.1fr),
    align: (left, center, center, center, center, center),
    inset: 5pt,
    table.header(
      [*Group*],
      [*N*],
      [*Age mean*],
      [*Age SD*],
      [*Female n (%)*],
      [*MMSE mean*],
    ),
    [Healthy], [29], [67.90], [5.40], [11 (37.9%)], [30.00],
    [AD], [36], [66.39], [7.89], [24 (66.7%)], [17.75],
    [FTD], [23], [63.65], [8.22], [9 (39.1%)], [22.17],
  ),
  caption: [Cohort summary derived from `demography_summary.csv`.]
) <tab-cohort>

== Frozen analysis surface

The report uses the canonical ds006036 rerun @ds006036_1_0_6 at `data/raw/neuralmanifolddynamics_ds006036_20260604_132747`. The H5 contracts expose:

1. subject-anchored and cohort-anchored `3D` and `9D` coordinates,
2. global `3D` and `9D` Jacobians,
3. regional `3D` MNPS and regional `3D` Jacobians for four realized regions: `frontal`, `central`, `parietal_occipital`, and `temporal`,
4. block-native metadata (`/blocks`, `/block_windows`) used to define the article's exact photic surface.

Two advertised surfaces remain outside the manuscript claim boundary:

1. a manuscript-stable higher-frequency analysis surface beyond `20 Hz`, because raw `25/30 Hz` support remains sparse,
2. a seven-region idealized regional partition that is not part of the validated article surface.

The main article keeps between-group and MMSE inference on the cohort-anchored surface. The dual-anchor bundle is still important for auditability and future work, but the present inferential contract is the cohort-shared exact-block surface summarized in `S1`.

== Exact block-native selection rule

The canonical rerun no longer expands sparse stage labels by a recovery heuristic. Instead, it uses the H5 block contract directly:

1. infer photic block intervals from `/blocks`,
2. identify the corresponding original exported windows,
3. retain an original window when its center falls within the exact block interval.

This keeps the inferential surface tied to original windows rather than to a recovery-expanded overlay. Across the bundle, exact block-native selection retained `1757` original windows across `397` block instances from `88` subjects and kept the article restricted to `PHOTO 5/10/15/20 Hz`.

#figure(
  kind: table,
  table(
    columns: (1.7fr, 1.0fr, 1.0fr, 1.0fr),
    align: (left, center, center, center, center),
    inset: 5pt,
    table.header(
      [*Selected stage*],
      [*Subjects with blocks*],
      [*Block instances*],
      [*Selected windows*],
    ),
    [PHOTO 5 Hz], [85], [123], [515],
    [PHOTO 10 Hz], [83], [95], [450],
    [PHOTO 15 Hz], [84], [92], [435],
    [PHOTO 20 Hz], [86], [87], [357],
  ),
  caption: [Exact block-native photic surface from `blocknative_selection_blocks.csv`. Across all frequencies, the canonical rerun retains `1757` original windows across `397` block instances without recovery expansion.]
) <tab-qc>

== Resting-state reference path

To provide an internal resting-state baseline, we analyzed ds004504 @ds004504_1_0_9 from `data/raw/neuralmanifolddynamics_ds004504_20260528_114734` with article-local wrappers stored beside the photic manuscript. The resting reference is intentionally narrow: it reuses the same `AD/Healthy/FTD` contrast structure, but only the overlapping global `3D` and `9D` MNJ `mdr_median` rows were carried forward into the manuscript-facing comparison bundle.

This reference therefore functions as an internal baseline check, not as a second full manuscript surface. It answers a specific question: whether the main corrected photic `AD vs Healthy` MNJ effect is already present at rest on the same summary family.

#figure(
  image("figures/figure_1_paradigm_pipeline.svg", width: 100%),
  caption: [Figure 1: Schematic of the article-local analysis path. Panel A shows the resting baseline plus the frozen `PHOTO 5/10/15/20 Hz` stages used in the manuscript. Panel B shows the manuscript export path from EEG windows through the coordinate contract, local Jacobian and reachability summaries, and finally group/MMSE outputs.]
) <fig-pipeline>

== Metric layers and statistics

The report centers on two families.

First, the reachability layer summarizes short-horizon local capacity geometry on the cohort-anchored `3D` MNPS or regional `3D` MNPS paths @langell2026_reachability. The primary article-facing reachability endpoints are:

1. `tube_d_eff_median`,
2. `tube_capture_gate_median`.

The full export also retains supporting reachability size and conditioning rows such as `tube_log_det_median` and `tube_kappa_median`.

Second, the MNJ layer summarizes the local Jacobian tensor @langell2025_mnj. The primary group-reference MNJ endpoint is `mdr_median`, while the export also retains `spectral_radius_median`, `rotational_power_median`, `frobenius_norm_median`, `trace_median`, and `anisotropy_abs_eig_median`.

=== Operational definition of `mdr_median`

When the time derivative of the local Jacobian is available, let $dot(J)_t$ denote the window-wise Jacobian derivative and define the exported ratio

$ D_t = frac(norm(dot(J)_t)_F, norm(J_t)_F + epsilon) $

with a small numerical stabilizer $epsilon$.

The manuscript-facing handoff then reports

$ "mdr_median" = "median"_t (D_t) $

across valid windows within each photic stage. By this implementation, higher values mean that the local Jacobian changes faster relative to its current magnitude, whereas lower values mean more slowly varying local Jacobian structure. In the present manuscript, lower photic `mdr_median` in `AD` is interpreted narrowly as reduced relative local Jacobian reconfiguration on the exported MNJ surface under rhythmic driving. Because the numerator is divided by the current Jacobian Frobenius norm, the quantity is partly size-normalized, but it still remains an operational summary inside the frozen NeuralManifoldDynamics 2.1 chart rather than a normalization-free or direct biophysical measurement.

#figure(
  image("figures/mdr_median.png", width: 92%),
  caption: [Conceptual interpretation of `mdr_median`. Lower values indicate that local Jacobian structure changes relatively slowly over time, whereas higher values indicate more rapid local Jacobian reconfiguration relative to current magnitude.]
) <fig-mdr-concept>

Between-group contrasts were computed for:

1. `AD vs Healthy`,
2. `FTD vs Healthy`,
3. `AD vs FTD`.

P-values come from Mann-Whitney tests, effect sizes are Cohen's `d`, and BH-FDR `q` values were adjusted within each `contrast x stage x analysis_type` block. Mini-Mental State Examination (MMSE) correlations @folstein1975 were assessed with Spearman `rho` in `Dementia_all`, `AD_only`, and `FTD_only`, with BH-FDR applied within each `cohort x stage x analysis_type` block. The Figure 4 scatter is included specifically to visually audit the strongest corrected MMSE row on the canonical rerun so that the reported rank-based result can be judged against the raw point cloud rather than against summary statistics alone.

= Results

== Exact block-native selection defined a lean but still broad surface

The canonical rerun no longer depends on recovery-centric regularization. Instead, it reads the exact H5 block intervals and keeps original windows whose centers fall within those intervals. This yielded `397` selected block instances and `1757` original windows across `88` subjects, with stage totals of `515` (`5 Hz`), `450` (`10 Hz`), `435` (`15 Hz`), and `357` (`20 Hz`) windows. The resulting surface is slightly leaner than the older recovery-centric rerun, but it remains broad enough for the same four-frequency inferential frame while avoiding recovery-expanded windows.

== Resting-state reference was weaker than photic stress

On the exact overlapping global `9D` MNJ `mdr_median` surface, the ds004504 resting-state baseline was near null for `AD vs Healthy` ($d = -0.080$, $p = 0.775$, $q = 0.909$). The corresponding photic effect was larger in magnitude at every frequency, reaching $d = -0.424$ at `PHOTO 5 Hz`, $d = -0.926$ at `PHOTO 10 Hz`, $d = -0.661$ at `PHOTO 15 Hz`, and $d = -0.984$ at `PHOTO 20 Hz`; the `10/15/20 Hz` rows survived correction on the article surface. The overlapping global `3D` `mdr_median` reference shows the same directional pattern more weakly, with a near-null resting effect ($d = 0.150$, $q = 0.918$) and subthreshold photic rows at `PHOTO 15 Hz` ($d = -0.611$, $q = 0.091$) and `PHOTO 20 Hz` ($d = -0.541$, $q = 0.062$).

This does not prove that photic stimulation is universally superior to resting-state across all conceivable metrics. It does, however, answer the narrow comparison targeted here on the manuscript's main MNJ surface: the corrected `AD vs Healthy` `9D` `mdr_median` separation is weak at rest and much larger under evoked rhythmic driving.

#figure(
  image("figures/figure_2_rest_vs_photic_stress.svg", width: 100%),
  caption: [Figure 2: Resting-state reference versus photic stress on the overlapping global `9D` MNJ `mdr_median` surface. The top panel shows article-local group means and standard errors for `Healthy` and `AD`, from resting baseline through `PHOTO 5/10/15/20 Hz`. The lower panel shows the matching `AD vs Healthy` Cohen's `d` values, making explicit that the baseline reference is near null while the strongest evoked separation appears at `PHOTO 20 Hz` in the canonical rerun.]
) <fig-rest-vs-photic>

== Group contrasts were sparse and frequency-specific

Only three group-contrast rows survived correction across the full reachability/MNJ export, and all three belonged to `AD vs Healthy` global `9D` MNJ `mdr_median`.

#figure(
  kind: table,
  table(
    columns: (1.5fr, 1.1fr, 1.5fr, 1.4fr, 1.1fr, 0.8fr, 0.9fr),
    align: (left, left, left, left, center, center, center),
    inset: 5pt,
    table.header(
      [*Contrast*],
      [*Frequency*],
      [*Layer*],
      [*Metric*],
      [*Network*],
      [*d*],
      [*q*],
    ),
    [AD vs Healthy], [PHOTO 20 Hz], [Global 9D MNJ], [`mdr_median`], [global], [-0.984], [0.0034],
    [AD vs Healthy], [PHOTO 10 Hz], [Global 9D MNJ], [`mdr_median`], [global], [-0.926], [0.0100],
    [AD vs Healthy], [PHOTO 15 Hz], [Global 9D MNJ], [`mdr_median`], [global], [-0.661], [0.0402],
  ),
  caption: [All corrected group-contrast findings from `group_frequency_contrasts.csv`.]
) <tab-corrected-contrasts>

This corrected table supports a narrow reading. The stable group signal is a repeated `AD vs Healthy` reduction in global `9D` MNJ `mdr_median`, strongest at `PHOTO 20 Hz` but already present at `PHOTO 10 Hz` and `PHOTO 15 Hz`. The dataset does not yield any corrected `AD vs FTD` or `FTD vs Healthy` group row, and it no longer yields a corrected global `3D` row on the canonical rerun. The manuscript therefore does not claim a direct disease-to-disease dissociation in the corrected group statistics.

The regional map is presented as a descriptive localization aid rather than as a full inferential topography. Figure 3 uses the frozen four-region `PHOTO 10 Hz` regional MNJ summary (`mdr_median`) because the H5 contracts expose only `frontal`, `central`, `parietal_occipital`, and `temporal`, and because the corrected group findings themselves are global rather than regional. It should be read as a four-region effect summary, not as a seven-region scalp reconstruction or as an additional corrected finding set.

#figure(
  image("figures/figure_3_four_region_map.svg", width: 92%),
  caption: [Figure 3: Descriptive four-region `PHOTO 10 Hz` regional summary on the frozen contract. Colors show Cohen's `d` for `mdr_median` on the regional `3D` MNJ surface for `AD vs Healthy` and `FTD vs Healthy`. This panel is explicitly a four-region summary from the realized article contract, not a full scalp topoplot, and it does not alter the corrected group result table in which all surviving rows are global.]
) <fig-region-map>

== MMSE structure was broader than the group surface

The MMSE panel is broader than the group-contrast panel, but the canonical rerun concentrates it more tightly than before. Eight rows survive correction, and all eight sit on global MNJ surfaces in either pooled dementia or `AD_only`.

The strongest corrected severity row is pooled-dementia `PHOTO 20 Hz` global `9D` MNJ `rotational_power_median` ($rho = -0.470$, $p = 3.31 times 10^(-4)$, $q = 0.0020$). Figure 4 shows the corresponding point cloud. The regression overlay is only a visual guide, but the pooled-dementia trend is not driven by one obvious outlier and remains interpretable when `AD` and `FTD` subjects are shown separately against faint Healthy background points.

#figure(
  image("figures/figure_4_ftd_frontal_mmse_scatter.svg", width: 92%),
  caption: [Figure 4: Subject-level MMSE scatter for the strongest corrected severity association on the canonical rerun: pooled dementia, `PHOTO 20 Hz`, global `9D` MNJ `rotational_power_median`. The annotation reports the rank-based statistic used in the manuscript; the regression line and interval are visual guides. `AD` and `FTD` points are colored separately, while `Healthy` points are retained only as faint background context.]
) <fig-ftd-mmse>

Because the earlier recovery-centric rerun had suggested stronger `FTD`-specific MMSE structure, Figure 5 is retained as a descriptive subgroup audit on the strongest `FTD_only` row in the canonical rerun: `PHOTO 20 Hz`, frontal regional `3D` MNJ `rotational_power_median` ($rho = 0.613$, $p = 0.0041$, $q = 0.097$). This row is visually structured and still worth inspection, but it does not survive the main manuscript's corrected threshold.

#figure(
  image("figures/figure_5_ftd_only_mmse_scatter.svg", width: 92%),
  caption: [Figure 5: Subject-level MMSE scatter for the strongest `FTD_only` row on the canonical rerun: `PHOTO 20 Hz`, frontal regional `3D` MNJ `rotational_power_median`. The annotation reports the rank-based statistic used in the audit. This panel is included as a subgroup-oriented descriptive follow-up to Figure 4, not as an additional corrected main-text finding, because the row remains subthreshold after within-family correction (`q = 0.097`).]
) <fig-ftd-mmse-subgroup>

#figure(
  kind: table,
  table(
    columns: (1.4fr, 1.0fr, 1.35fr, 1.45fr, 1.0fr, 0.9fr, 0.9fr),
    align: (left, left, left, left, center, center, center),
    inset: 5pt,
    table.header(
      [*Cohort*],
      [*Frequency*],
      [*Layer*],
      [*Metric*],
      [*Network*],
      [*rho*],
      [*q*],
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
  caption: [All corrected MMSE associations from `mmse_correlations_summary.csv`.]
) <tab-mmse>

On this export, severity structure is therefore not confined to one single MNJ summary, but it is more concentrated than before. In pooled dementia, the densest corrected cluster appears at `PHOTO 20 Hz` global `9D` MNJ, where lower MMSE aligns with higher rotational power, spectral radius, anisotropy, and Frobenius energy. `AD_only` contributes a corrected `PHOTO 5 Hz` global `3D` trace row plus three `PHOTO 20 Hz` global `9D` rows. By contrast, the canonical rerun no longer yields a corrected `FTD_only` MMSE row.

This still makes the severity map broader than the corrected group map. The evidence tilts toward MNJ as the richer surface here, especially at high-frequency global `9D`, but it does not support the stronger claim that symptom-linked structure is distributed evenly across diagnoses or metric families.

= Discussion

The most defensible interpretation is narrower than a broader disease-dissociation hypothesis.

First, the canonical exact-block/native-block rerun does contain non-trivial dementia-related structure, but the stable between-group signal remains narrow and asymmetric. All corrected group rows come from `AD vs Healthy` global `9D` MNJ `mdr_median`, strongest at `PHOTO 20 Hz` and also present at `PHOTO 10 Hz` and `PHOTO 15 Hz`, while direct `AD vs FTD` and `FTD vs Healthy` contrasts do not survive correction.

Second, the resting-state comparison is included as an explicit article-local reference rather than as background motivation alone. On the overlapping global `9D` `mdr_median` surface, resting-state baseline was essentially null for `AD vs Healthy`, whereas the same contrast became large and corrected under photic driving. That supports a bounded stress-test reading: the MNJ effect is more visible under evoked rhythmic forcing than at baseline on this specific shared surface. It still does not justify the broader theorem that resting-state is generally inadequate for all dementia-related geometry questions.

Third, the severity map is broader than the group-contrast map but also more concentrated than in the older rerun. Global `9D` MNJ at `PHOTO 20 Hz` is now the clearest pooled-dementia surface, `AD_only` retains a lighter but corrected signature on the same family plus one `PHOTO 5 Hz` global `3D` row, and `FTD_only` no longer contributes a corrected MMSE row. That pattern does not prove a single unified mechanism, but it does show that symptom-linked structure is richer than the group-linked surface even after the surface is tightened to exact block-native windows.

Fourth, the block-Jacobian appendix remains complementary rather than primary. After mirrored-pair condensation, the run-level appendix still retains `32` corrected unique-family group rows and `4` corrected MMSE rows, spanning both `AD vs Healthy` and `FTD vs Healthy`, but it is not frequency-stratified and therefore remains outside the main article's inferential boundary. It is treated as supporting exploratory geometry rather than as part of the main argument.

= Limitations

Several limits must remain explicit.

1. The photic stage surface now comes from inferred H5 block intervals rather than from a recovery heuristic, but those intervals are still a dataset-derived contract rather than an independently audited stimulus log.
2. The article-level analysis supports only `PHOTO 5/10/15/20 Hz`. Raw `25/30 Hz` labels do exist, but cohort-level support remains too sparse for manuscript-grade claims.
3. The H5 contracts expose four realized regions (`frontal`, `central`, `parietal_occipital`, `temporal`) rather than a seven-region idealized partition, so Figure 3 is intentionally a four-region summary rather than a full scalp reconstruction.
4. Many stage-specific cells are modest in size, especially once the cohort is split by diagnosis and frequency.
5. The resting-state reference is intentionally narrow and was limited to the overlapping global `3D/9D` MNJ `mdr_median` surface, so it should not be read as an exhaustive rest-versus-photic comparison across all available metrics.
6. Corrected group contrasts are much sparser than corrected MMSE rows, so between-group conclusions should be read more narrowly than symptom-linked ones.
7. Because photic driving depends on peripheral sensory and early visual pathways, part of the observed `AD vs Healthy` evoked difference could reflect retinal or primary visual-system degradation rather than cortical manifold failure alone.

= Conclusion

The standalone ds006036 photic analysis now rests on the exact-block/native-block `20260604_132747` export, where original windows are selected directly from the inferred H5 photic blocks. The corrected between-group surface narrows to `AD vs Healthy` global `9D` MNJ `mdr_median` reductions at `PHOTO 10/15/20 Hz`. The ds004504 resting-state reference shows that the overlapping `AD vs Healthy` `9D` `mdr_median` contrast is near null at baseline, so the main manuscript signal is stronger under evoked photic stress on that shared surface. MMSE structure remains broader than the group map, but it is now concentrated mainly in pooled-dementia and `AD_only` high-frequency global `9D` MNJ rows, led by `PHOTO 20 Hz` rotational power. The most defensible next step is explicit replication on similarly well-labeled exports, especially to test whether this narrower exact-block signal and its high-frequency severity map remain stable once higher-frequency photic stages become dense enough for manuscript-grade `25/30 Hz` analysis.

= Appendix: Exploratory Block-Jacobian Families

An exploratory run-level block-Jacobian pass complements the main photic export. This surface is not frequency-stratified and therefore sits outside the manuscript's main inferential boundary. To reduce redundant directional bookkeeping, mirrored off-diagonal pairs such as `m->d` and `d->m` were collapsed into unordered unique families such as `m<->d`, with mirrored values averaged within subject before statistics were recomputed.

That condensation simplified the picture materially. Corrected block-Jacobian group rows fell from `55` raw pair rows to `32` unique-family rows, and corrected MMSE rows fell from `5` raw rows to `4` unique-family rows. The retained appendix surface is dominated by regional `m/d/e` families in `AD vs Healthy` and `FTD vs Healthy`, while the global `9D` block-Jacobian rows do not remain central after condensation. We therefore treat block Jacobians as appendix-only complementary geometry rather than as part of the main photic claim set.

#figure(
  kind: table,
  table(
    columns: (1.0fr, 1.25fr, 1.2fr, 1.0fr, 1.5fr, 1.2fr, 0.85fr),
    align: (left, left, left, left, left, center, center),
    inset: 5pt,
    table.header(
      [*Panel*],
      [*Contrast/cohort*],
      [*Network*],
      [*Family*],
      [*Metric*],
      [*Effect*],
      [*q*],
    ),
    [Group], [FTD vs Healthy], [parietal-occipital], [`m<->d`], [`c_sym_mean`], [`d = -1.066`], [0.0021],
    [Group], [FTD vs Healthy], [parietal-occipital], [`m<->d`], [`block_frobenius_mean`], [`d = -1.065`], [0.0021],
    [Group], [FTD vs Healthy], [parietal-occipital], [`d->d`], [`block_anisotropy_mean`], [`d = -0.646`], [0.00077],
    [Group], [AD vs Healthy], [frontal], [`m->m`], [`block_frobenius_mean`], [`d = -0.516`], [0.0041],
    [MMSE], [AD_only], [frontal], [`d->d`], [`block_frobenius_mean`], [`rho = -0.538`], [0.033],
  ),
  caption: [Representative findings from the deduplicated run-level block-Jacobian appendix surface, summarized from `block_jacobian_unique_family_appendix_summary.md`.]
) <tab-block-jacobian-appendix>

= Acknowledgements

This work emerged through structured correspondence among human and AI collaborators; large language models from OpenAI, Anthropic, and Google assisted in literature synthesis, drafting, and editorial refinement. We also gratefully acknowledge the original investigators, clinical teams, participants, and data stewards who created, curated, and shared the public datasets and metadata that made these analyses possible.

= Contact

Robin Langell - hello(at)noeticdiffusion.com

= Licensing

This manuscript provides only a brief licensing summary; full terms and conditions are available via the Mychainos multi-layer licensing framework (`https://noeticdiffusion.com/license.html`). In short, the conceptual content is released under CC BY-SA 4.0, software under GPLv3, and relevant hardware/biological artifacts under open hardware/biological licences (for example, CERN OHL v2 and OpenMTA). Unified ethical guardrails apply: no coercive, military, or surveillance applications; no patenting or black-boxing of core methods; and derived works should remain accessible, attributed, and shared with care.

= Data and Code Availability

Reference implementations and analysis pipelines:
`https://github.com/NoeticDiffusion`

Datasets and related public bundles:
`https://github.com/NoeticDiffusion/NeuralManifoldDynamics-dataset`

= Trademark Notice

Certain terms used in this manuscript (including Noetic Diffusion, Noetic Diffusion Theory, Noetic Diffusion Mapping, Noetic Diffusion Health Index, and Noetic Atlas) are used as project names and are the subject of ongoing trademark applications. A concise description of the stewardship rationale, current registration status, and how this interacts with open scientific use is available at `https://noeticdiffusion.com/license.html`. These trademark aspects do not affect the scientific content, reproducibility, or licensing of the methods described here.

#bibliography("alzheimer_ftd_reference_list.bib", title: [References])
