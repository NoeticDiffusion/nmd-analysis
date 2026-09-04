#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Evoked Structural Brittleness Under Photic Stimulation in Alzheimer Disease and Frontotemporal Dementia",
  short-title: "Photic ESB",
  subtitle: "A ds004504-Anchored Photic EEG Study in Alzheimer Disease and Frontotemporal Dementia",
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
    "Evoked Structural Brittleness",
    "NeuralManifoldDynamics",
  ),
  article-type: "Research Article / Follow-up Working Paper",
  abstract: [
    In this exact-block/native-block follow-up analysis, we built a standalone article-local workflow around the canonical ds006036 photic EEG surface at `data/raw/neuralmanifolddynamics_ds006036_20260604_132747` together with subject-matched ds004504 resting baselines to test whether neurodegenerative groups show abnormal evoked deformation relative to a healthy response template. Using an exploratory-frozen ESB-2 specification, the primary score combined parietal-occipital `tube_d_eff_median` with global `rotational_power_median` after subject-level ds004504 baseline subtraction. The strongest disease-versus-Healthy separation localized to `PHOTO 15 Hz`: `AD vs Healthy` reached $d = 0.821$ and $q = 0.00626$, while `FTD vs Healthy` reached $d = 1.038$ and $q = 0.00269$. Cross-fitted Healthy rescoring preserved the same `PHOTO 15 Hz` effect, though with smaller magnitudes ($d = 0.676$ for `AD vs Healthy` and $d = 0.841$ for `FTD vs Healthy`). Axis decomposition showed that the deviation was mainly posterior-capacity-led, with corrected capacity rows at `PHOTO 5/10/15 Hz` for AD and no comparably stable guidance-only effect. A conventional comparator panel showed partial overlap with AD alpha-linked power change, but its direct association with ESB-2 remained weak and non-corrected. Leave-one-out, permutation, and recovery-subset QC supported the `PHOTO 15 Hz` ESB-2 result, whereas the secondary profile-based PRL test remained negative. The bounded conclusion is that ESB-2 is an internally stabilized disease-versus-Healthy perturbational deviation score on this cohort, not an externally validated biomarker or resonance-loss theorem.
  ],
  data-availability: [
    The article-local workflow is stored under `articles/CLINICAL/alzheimer_ftd_photonic_esb/src/`, with manuscript outputs under `articles/CLINICAL/alzheimer_ftd_photonic_esb/results/` and figure assets under `articles/CLINICAL/alzheimer_ftd_photonic_esb/figures/`.

    Core outputs include `esb_article_manifest.json`, `esb_subject_scores.csv`, `esb_contrasts.csv`, `esb_axis_contrasts.csv`, `qc_cross_fitted_esb2_scores.csv`, `qc_cross_fitted_esb2_contrasts.csv`, `qc_frequency_peak_audit.csv`, `qc_spec_sensitivity_summary.csv`, `dataset_comparability_summary.csv`, `negative_results_summary.csv`, `conventional_comparator_subject_stage.csv`, `conventional_comparator_contrasts.csv`, `conventional_comparator_esb2_correlations.csv`, `conventional_comparator_summary.md`, `qc_leave_one_out_esb2.csv`, `qc_permutation_tests.csv`, `qc_recovery_subset_stability.csv`, `esb_article_summary.md`, `esb_qc_summary.md`, `reproducibility_commands.md`, and `figure_manifest.json`.

    Extended score construction, full tables, robustness material, and clinician-facing interpretation are split into the standalone supplement files `S1_Supplementary_Methods.typ`, `S2_Supplementary_Data.typ`, `S3_Supplementary_QC_Robustness.typ`, and `S4_Supplementary_Clinical.typ`.
  ],
  competing-interests: [
    No competing interests are declared in this manuscript.
  ],
)

= Introduction

The earlier photic EEG article in this repository @langell2026_photic_stress established a narrow but corrected AD-versus-Healthy signal on a global Meta-Noetic Jacobian surface and showed that the overlapping resting-state reference was much weaker at baseline @mckhann2011 @rascovsky2011 @nardone2018. That result was intentionally compact and single-metric. The present follow-up asks a different question: can the same cohort support a perturbational deviation score defined relative to a healthy evoked response template rather than a single exported endpoint?

Rhythmic visual forcing is a natural test bed for that question. Human EEG responses to photic flicker can entrain ongoing oscillations and reveal frequency-specific response structure that is not obvious in passive baseline recordings @herrmann2001 @notbohm2016. This is clinically relevant because Alzheimer disease and behavioural-variant frontotemporal dementia do not primarily damage the same systems: AD more strongly emphasizes posterior and temporoparietal vulnerability, whereas bvFTD preferentially affects frontal-insular and salience-network organization @jagust2018 @seeley2009 @zhou2010.

This manuscript centers on one empirical score: Evoked Structural Brittleness, abbreviated ESB-2. ESB-2 measures how far a subject's rest-to-photic response vector deviates from the Healthy template in a two-axis space formed by posterior reachability capacity and global dynamical guidance. A secondary profile-based extension, Photic Resonance Loss, was also evaluated, but it is not treated as a co-equal headline finding because it did not stabilize as an article-level discriminator on the current four-frequency surface.

For readers outside the broader Noetic Diffusion framework, the analysis can be read operationally as follows: windowed EEG dynamics were summarized on a fixed low-dimensional measurement contract; subject-level photic-stage summaries were compared to subject-matched resting baselines; and group differences were tested on these exported measurements. The present claims concern only those exported measurements and their article-local audit trail, not the full theoretical scope of Noetic Diffusion Theory @langell2025_6 or the full NeuralManifoldDynamics interpretation @langell2026_mndm.

The paper is therefore bounded by three questions:

1. Does ds004504-anchored ESB-2 produce reproducible disease-versus-healthy separation on the frozen photic surface?
2. If so, is the deviation mainly capacity-led, guidance-led, or both?
3. Do secondary profile or recovery extensions add stable information beyond the core ESB-2 result?

Detailed score construction, full inventories, the full QC bundle, and clinician-facing interpretation are moved to standalone `S1`-`S4` supplements so that the main paper can stay focused on the review-stable article surface.

= Methods

== NeuralManifoldDynamics and Noetic Diffusion framing

NeuralManifoldDynamics is the manuscript's operational measurement layer rather than the full theory. In practice, preprocessed EEG is partitioned into short windows and exported into fixed low-dimensional charts under a versioned measurement contract, after which local geometric and dynamical summaries are computed on that charted surface @langell2026_mndm. In the present article, those exported summaries include reachability-derived capacity terms and Meta-Noetic Jacobian guidance terms, which are later aggregated by subject and photic stage.

More broadly, Noetic Diffusion Theory provides the organizing structure in which neural activity is modeled as motion on a constrained state space with both local geometry and local update structure @langell2025_6. At a minimal level, the framework separates a measurement layer that defines what is exported, a local-dynamics layer that characterizes how nearby states evolve, and a higher-level interpretive layer about diffusion, access, and control across the state surface. The present article uses only the bounded export and local-dynamics layers and tests group differences on those exported observables; it does not attempt to validate the full NDT interpretation.

== Datasets and comparability contract

The analysis couples the ds006036 eyes-open photic cohort @ds006036_1_0_6 with the ds004504 resting-state cohort @ds004504_1_0_9. Subject matching was performed by subject ID, and subject-level ds004504 baselines were available for all `88` photic participants. The frozen primary ESB-2 surface additionally requires both posterior capacity and global guidance on both datasets, leaving a matched `86`-subject surface with `27 Healthy`, `36 AD`, and `23 FTD` participants before stage-specific coverage filters are applied.

The comparison remains bounded because the datasets are not state-equivalent. Ds004504 is a resting, eyes-closed baseline dataset, whereas the ds006036 analysis surface is eyes-open and stimulus-evoked. For that reason, the resting anchor is used only as a subject-aligned baseline for the ESB score, not as a full state-matched non-photic control condition.

The ds006036 photic summaries are inherited from the sibling photic rerun, which now uses exact block-native selection from `data/raw/neuralmanifolddynamics_ds006036_20260604_132747`: original windows are kept when their centers fall inside inferred H5 photic block intervals. The frozen inferential surface remains restricted to `PHOTO 5`, `10`, `15`, and `20 Hz`. On the primary ESB-2 specification, stage-wise analyzable subject counts were:

#figure(
  kind: table,
  table(
    columns: (1.9fr, 0.9fr, 0.9fr, 0.9fr, 0.9fr),
    align: (left, center, center, center, center),
    inset: 5pt,
    table.header(
      [*Group*],
      [*PHOTO 5 Hz*],
      [*PHOTO 10 Hz*],
      [*PHOTO 15 Hz*],
      [*PHOTO 20 Hz*],
    ),
    [Healthy], [25], [27], [27], [18],
    [AD], [33], [34], [34], [23],
    [FTD], [23], [22], [22], [12],
  ),
  caption: [Primary ESB-2 stage coverage from `stage_coverage_summary.csv`. Coverage is stable through `15 Hz` and drops mainly at `20 Hz`, especially in `FTD` and the matched Healthy subset.]
) <tab-coverage>

== Primary score: ESB-2

For each subject and photic stage, we computed a two-component response vector relative to the same subject's ds004504 resting-state baseline. Delta C was the photic-stage capacity minus resting-state capacity, and Delta R was the photic-stage guidance minus resting-state guidance.

Capacity was defined as parietal-occipital tube_d_eff_median @langell2026_reachability, and guidance was defined as global 9D rotational_power_median from the MNJ layer @langell2025_mnj. At each frequency, the Healthy template was the median Healthy response vector with robust within-Healthy scaling. ESB-2 was then the scaled Euclidean distance from that Healthy template in the two-dimensional Delta C / Delta R plane.

Using HC to denote the Healthy set, the operational score can be written compactly as follows:

$ Delta C_i(f) = C_i(f) - C_i("rest") $

$ Delta R_i(f) = R_i(f) - R_i("rest") $

$ h_C(f) = "median"_(i in "HC")(Delta C_i(f)), quad h_R(f) = "median"_(i in "HC")(Delta R_i(f)) $

$ s_C(f) = "MAD"_(i in "HC")(Delta C_i(f)), quad s_R(f) = "MAD"_(i in "HC")(Delta R_i(f)) $

$ "ESB-2"_i(f) = frac(1, sqrt(2)) sqrt((frac(Delta C_i(f) - h_C(f), s_C(f) + epsilon))^2 + (frac(Delta R_i(f) - h_R(f), s_R(f) + epsilon))^2) $

Equivalently, the score first standardizes each axis separately, using $(Delta C_i(f) - h_C(f)) / (s_C(f) + epsilon)$ and $(Delta R_i(f) - h_R(f)) / (s_R(f) + epsilon)$, and then combines those two standardized axis values by Euclidean distance divided by $sqrt(2)$.

In other words, the numerical stabilizer $epsilon$ is added inside each denominator before squaring; it is not added after division.

The original article-local ESB surface used the full Healthy template for all groups. To test in-sample template bias directly, we also computed a cross-fitted Healthy variant in which each Healthy subject was rescored against a template that excluded that subject, while AD and FTD subjects remained scored against the full Healthy template.

The primary article specification combined posterior capacity with global guidance because this was the strongest exploratory candidate before the article build and remained the strongest realized surface after the article-local rerun. A second realized specification combined posterior capacity with frontal guidance. A third planned sensitivity specification, global capacity plus global guidance, could not be materialized on the frozen stage table because stage-wise global reachability rows were not present in the exported article-local metric surface.

== Specification status

The posterior-capacity plus global-guidance ESB-2 specification was selected from an exploratory pass before the article-local rerun. The present manuscript therefore treats this specification as internally stabilized but not externally validated. All p-values and q-values should be read as article-local inference for this frozen rerun rather than as confirmatory evidence from an independent cohort.

== Secondary profile and recovery extensions

As a secondary analysis, we also computed a simple profile-based Photic Resonance Loss score equal to one minus the correlation between a subject's four-point ESB-2 profile and the Healthy median profile on the same specification. This was included to test whether multifrequency shape adds stable information beyond the strongest single-stage ESB-2 rows.

We also retained an exploratory recovery quantity, h_rest_raw, defined as the Euclidean distance between post-photic residual geometry and the ds004504 resting baseline. Because ds004504 is not state matched to the post-photic eyes-open residual, recovery-weighted interpretations were treated as explicitly bounded and secondary.

== Conventional comparator panel

To test whether ESB-2 merely re-expresses ordinary photic EEG changes, we added a compact posterior comparator panel computed on the same subject-matched rest-to-photic surface. The four comparator readouts were:

1. a stage-matched posterior band-power proxy,
2. posterior alpha power,
3. posterior alpha/theta ratio,
4. posterior sample entropy.

All comparator values were summarized as subject-level medians within the exact block-native photic windows and then rest-subtracted against the corresponding ds004504 feature median. Direct stimulation-frequency SSVEP amplitude was not available on the frozen article feature surface, so the band-power proxy used the nearest posterior band exported in the contract: theta for `PHOTO 5 Hz`, alpha for `PHOTO 10 Hz`, and beta for `PHOTO 15` and `20 Hz`. The present comparator panel should therefore be read as a broad posterior EEG control rather than as a definitive entrainment control, and it cannot rule out all ordinary stimulation-frequency entrainment explanations.

== Statistics and QC

Between-group contrasts were computed for AD versus Healthy, FTD versus Healthy, and AD versus FTD using Mann-Whitney tests with Cohen's $d$. BH-FDR was applied within explicitly defined score families:

#figure(
  kind: table,
  table(
    columns: (1.55fr, 1.95fr, 1.2fr),
    align: (left, left, left),
    inset: 5pt,
    table.header(
      [*Family*],
      [*Tests included*],
      [*FDR scope*],
    ),
    [ESB-2 / recovery-weighted / residual contrasts], [contrast x frequency with specification varied inside each score family], [BH within family],
    [Axis decomposition], [contrast x frequency with specification varied inside each axis family], [BH within family],
    [PRL], [contrast with specification varied], [BH within family],
    [Comparator contrasts], [contrast x frequency with comparator varied], [BH within family],
    [ESB-comparator correlations], [cohort with comparator varied], [BH within family],
  ),
  caption: [FDR family definitions used in the article-local ESB workflow. The separate qc_frequency_peak_audit.csv file then adds a small post-hoc frequency-only audit for the primary ESB-2 specification.]
) <tab-fdr-families>

The article-local QC bundle included:

1. leave-one-out Healthy-template sensitivity on the primary ESB-2 and PRL surfaces,
2. 2000-draw permutation tests on the main PHOTO 15 Hz ESB-2 row and the primary PRL row,
3. specification sensitivity across the planned and realized ESB configurations,
4. stage coverage and recovery-coverage subset stability audits,
5. a conventional comparator panel with PHOTO 15 Hz group contrasts and Spearman association against ESB-2.

= Empirical Results

== ESB-2 showed its strongest disease-versus-Healthy separation at PHOTO 15 Hz

The article-local output bundle reproduced its strongest disease-versus-Healthy separation at `PHOTO 15 Hz` on the primary posterior-capacity plus global-guidance surface. `AD vs Healthy` reached $d = 0.821$, $p = 0.00313$, and $q = 0.00626$, while `FTD vs Healthy` reached $d = 1.038$, $p = 0.00135$, and $q = 0.00269$. On the full article surface, `FTD vs Healthy` also remained corrected at `PHOTO 5 Hz` and `PHOTO 10 Hz`, whereas `AD vs Healthy` was corrected only at `PHOTO 15 Hz`.

#figure(
  image("figures/figure_1_esb_prl_schematic.svg", width: 100%),
  caption: [Conceptual path of the article-local ESB workflow. Resting-state ds004504 recordings anchor the subject-specific baseline, ds006036 photic blocks provide the evoked response surface, and ESB-2 measures Healthy-template deviation in capacity-guidance space. Secondary profile and recovery extensions were evaluated only after the ESB-2 surface was established.]
) <fig-schematic>

#figure(
  image("figures/figure_2_esb2_group_trajectories.svg", width: 100%),
  caption: [Group trajectories for the primary ESB-2 specification. The strongest observed disease-versus-Healthy stage localizes to `PHOTO 15 Hz`, with `FTD` already elevated at `PHOTO 5/10 Hz` and `AD` rising most clearly at `PHOTO 15 Hz`.]
) <fig-esb-trajectory>

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
      [*d*],
      [*q*],
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
  caption: [Primary ESB-2 group contrasts from esb_contrasts.csv. Only rows central to the main empirical result are shown.]
) <tab-main-esb>

#figure(
  kind: table,
  table(
    columns: (1.55fr, 0.95fr, 0.95fr, 0.95fr, 0.95fr),
    align: (left, center, center, center, center),
    inset: 5pt,
    table.header(
      [*Metric version*],
      [*AD d*],
      [*AD q*],
      [*FTD d*],
      [*FTD q*],
    ),
    [Original ESB-2], [0.821], [0.0063], [1.038], [0.0027],
    [Cross-fitted Healthy ESB-2], [0.676], [0.0128], [0.841], [0.0073],
  ),
  caption: [PHOTO 15 Hz Healthy-template bias check. In the cross-fitted version, each Healthy subject is rescored against a Healthy template that excludes that subject, while AD and FTD remain scored against the full Healthy template. The main disease-versus-Healthy result weakens modestly but remains present.]
) <tab-crossfit>

This pattern differs from the earlier single-metric MNJ story @langell2026_photic_stress in an informative way. The strongest `mdr_median` row in the updated photic manuscript is an `AD vs Healthy` global `9D` effect at `PHOTO 20 Hz` with $d = -0.984$ and $q = 0.00338$, whereas the present composite score shows its strongest observed stage at `PHOTO 15 Hz` and separates both disease groups from Healthy. ESB-2 therefore does not replace the narrower `mdr_median` finding. It adds a broader disease-versus-Healthy deviation layer on top of it.

The cross-fitted Healthy analysis addresses the strongest template-circularity concern. At `PHOTO 15 Hz`, the main row weakened from $d = 0.821$ to $d = 0.676$ for `AD vs Healthy` and from $d = 1.038$ to $d = 0.841$ for `FTD vs Healthy`, but both remained statistically supported on the current article surface. This does not remove all development-stage bias concerns, but it does show that the result is not created solely by in-sample Healthy-template shrinkage.

All subsequent biological interpretation uses the original ESB-2 effect sizes as the article-local surface, while the cross-fitted estimates define the conservative robustness boundary.

== Specification sensitivity and capacity-led decomposition

The primary result remained strongest on the posterior-capacity plus global-guidance specification. The realized posterior-capacity plus frontal-guidance variant was weaker, especially for `FTD`, and the planned global-capacity plus global-guidance branch did not yield analyzable `PHOTO 15 Hz` contrasts on the frozen article export.

#figure(
  kind: table,
  table(
    columns: (1.9fr, 1.35fr, 1.05fr, 1.05fr, 1.45fr),
    align: (left, left, center, center, left),
    inset: 5pt,
    table.header(
      [*Specification*],
      [*Contrast*],
      [*d*],
      [*q*],
      [*Interpretation*],
    ),
    [Posterior capacity + global guidance], [AD vs Healthy], [0.821], [0.0063], [Primary and strongest realized surface],
    [Posterior capacity + global guidance], [FTD vs Healthy], [1.038], [0.0027], [Primary and strongest realized surface],
    [Posterior capacity + frontal guidance], [AD vs Healthy], [0.557], [0.0249], [Weaker guidance variant],
    [Posterior capacity + frontal guidance], [FTD vs Healthy], [0.138], [0.8328], [Does not stabilize FTD separation],
    [Global capacity + global guidance], [PHOTO 15 Hz], [n/a], [n/a], [Planned branch did not yield analyzable primary-stage contrasts],
  ),
  caption: [Specification sensitivity at PHOTO 15 Hz from qc_spec_sensitivity_summary.csv. The main result is not just a generic consequence of any ESB definition; it is strongest on the posterior-capacity plus global-guidance surface.]
) <tab-spec>

The axis decomposition indicates that the main ESB-2 lift was capacity-led. On the primary specification, `AD vs Healthy` capacity contrasts were negative at all frequencies and corrected at `PHOTO 5 Hz` ($d = -0.438$, $q = 0.0291$), `PHOTO 10 Hz` ($d = -0.652$, $q = 0.0071$), and `PHOTO 15 Hz` ($d = -0.631$, $q = 0.0118$), whereas guidance contrasts were smaller and did not yield comparably stable corrected rows. `FTD vs Healthy` showed the same broad signed direction, but with weaker capacity-only rows than the full composite score.

#figure(
  image("figures/figure_3_capacity_guidance_plane.svg", width: 92%),
  caption: [Capacity-guidance plane at PHOTO 15 Hz for the primary specification. Dashed lines mark the Healthy median template in Delta C and Delta R. Both disease groups drift away from the Healthy centroid, but the dominant signed shift is along the capacity axis.]
) <fig-plane>

The biological reading should therefore stay narrow: on this surface, disease-related evoked deviation looks more like a loss of response bandwidth than a pure failure of guidance alone. ESB-2 is best read here as a posterior-capacity-led deviation score whose second axis helps define the response plane rather than as evidence that capacity and guidance contribute equally.

== Negative and secondary findings

The corrected surface also defines what the article cannot claim. No corrected disease-versus-disease ESB-2 row survived on the article surface, and the current data therefore do not support a categorical AD-versus-FTD ESB dissociation. The signal is strongest as a disease-versus-Healthy perturbational deviation score.

The secondary PRL test was also negative at the article level. On the primary specification, the best AD-versus-Healthy PRL row remained weak (`d = -0.388`, `q = 0.270`), and the best FTD-versus-Healthy PRL row was similarly weak (`d = -0.372`, `q = 0.365`). No PRL contrast yielded a corrected row.

== Conventional posterior comparators overlapped only partially with ESB-2

The conventional comparator panel showed that some ordinary posterior EEG features do change on the same rest-subtracted surface, especially in AD. At PHOTO 15 Hz, both the stage-matched posterior band-power proxy and posterior alpha power separated AD from Healthy (`d = 0.619` and `d = 0.681`, both `q = 0.00155`). The FTD-versus-Healthy branch was weaker and did not survive correction; its largest conventional row was posterior alpha power (`d = 0.463`, `q = 0.136`).

#figure(
  kind: table,
  table(
    columns: (1.8fr, 0.9fr, 0.9fr, 0.9fr, 0.9fr, 0.9fr, 1.0fr),
    align: (left, center, center, center, center, center, center),
    inset: 5pt,
    table.header(
      [*Comparator*],
      [*AD d*],
      [*AD q*],
      [*FTD d*],
      [*FTD q*],
      [*rho all*],
      [*rho disease*],
    ),
    [Stage-matched posterior band-power proxy], [0.619], [0.0016], [0.161], [0.171], [0.098], [-0.067],
    [Posterior alpha power], [0.681], [0.0016], [0.463], [0.136], [0.182], [0.033],
    [Posterior alpha/theta ratio], [0.042], [0.129], [-0.180], [0.802], [0.169], [0.228],
    [Posterior sample entropy], [-0.399], [0.129], [-0.165], [0.802], [-0.148], [-0.023],
  ),
  caption: [PHOTO 15 Hz conventional comparator panel from conventional_comparator_contrasts.csv and conventional_comparator_esb2_correlations.csv. The correlation columns report Spearman rho against ESB-2 across all subjects and across the disease-only subset. Direct narrowband SSVEP amplitude was not available on the frozen feature surface, so the first row is a nearest-band posterior power proxy.]
) <tab-comparators>

However, the association between these conventional comparators and ESB-2 remained modest. Across all subjects at `PHOTO 15 Hz`, absolute Spearman correlations with ESB-2 were no larger than about `0.18`, and none survived correction. Once the Healthy group was removed, the correlations collapsed further, with absolute rho values no larger than `0.23` on the disease-only subset and mostly near zero.

#figure(
  image("figures/figure_4_conventional_comparator_correlations.svg", width: 100%),
  caption: [PHOTO 15 Hz scatter panel comparing ESB-2 against the four conventional posterior comparator deltas. Each x-axis is standardized within comparator for readability. All-subject and disease-only Spearman rho values are annotated in each panel. The conventional features show some overlap with the disease-versus-Healthy surface, but no single comparator tracks ESB-2 strongly within the disease-only subset.]
) <fig-comparators>

This is an important negative control. The current data do not show that ESB-2 is independent of all ordinary posterior EEG change, because alpha-linked power differences are present on the same surface. They do show, however, that ESB-2 is not well described as a simple re-labeled version of one conventional posterior feature, and that the available broad posterior power/entropy summaries do not capture the score well.

The primary specification should therefore be read as showing its strongest observed ESB-2 separation at PHOTO 15 Hz, not as proving a biological resonance peak. In the frequency-only audit, the PHOTO 15 Hz row survived four-frequency BH adjustment for both AD vs Healthy (`q = 0.0125`) and FTD vs Healthy (`q = 0.0054`), while the FTD branch also remained positive at PHOTO 5 Hz and PHOTO 10 Hz (`q = 0.0276` for both). The negative PRL result further cautions against reading the current data as a validated resonance-profile claim.

== QC supported the strongest observed PHOTO 15 Hz ESB-2 result

The main `PHOTO 15 Hz` ESB-2 result was stable under Healthy-template leave-one-out analysis. For `AD vs Healthy`, the effect-size range was narrow with median `0.818`, minimum `0.793`, and maximum `0.843`. `FTD vs Healthy` remained similarly stable with median `1.013`, minimum `0.925`, and maximum `1.091`. Permutation tests were concordant with the rank-based p-values: the empirical p-value was `0.0015` for `AD vs Healthy`, and the `FTD vs Healthy` row had no exceedance in `2000` draws.

#figure(
  kind: table,
  table(
    columns: (1.6fr, 1.25fr, 1.0fr, 1.0fr, 1.0fr),
    align: (left, left, center, center, center),
    inset: 5pt,
    table.header(
      [*Score*],
      [*Contrast*],
      [*Median d*],
      [*Min d*],
      [*Max d*],
    ),
    [ESB-2 leave-one-out], [AD vs Healthy], [0.818], [0.793], [0.843],
    [ESB-2 leave-one-out], [FTD vs Healthy], [1.013], [0.925], [1.091],
    [PRL leave-one-out], [AD vs Healthy], [-0.295], [-0.513], [0.028],
    [PRL leave-one-out], [FTD vs Healthy], [-0.435], [-0.568], [-0.170],
  ),
  caption: [Leave-one-out Healthy-template sensitivity from qc_leave_one_out_esb2.csv and qc_leave_one_out_prl.csv. ESB-2 remains stable; PRL does not.]
) <tab-loo>

Recovery-weighted variants were more difficult to interpret. On the primary PHOTO 15 Hz surface, the AD-versus-Healthy ESB-2 effect dropped from 0.821 on the full set to 0.561 on the subset with at least two recovery-eye windows, while the FTD-versus-Healthy effect dropped from 1.038 to 0.652. This does not invalidate ESB-2 itself, because the core score does not require recovery. It does, however, reinforce the decision to keep recovery-weighted interpretations outside the article's main claim boundary.

= Discussion

The most defensible conclusion is that ds004504-anchored ESB-2 is feasible, interpretable, and stronger than a null result, but not yet a universal perturbational biomarker.

First, the score is reproducible on its own terms on the exact-block/native-block surface. The main `PHOTO 15 Hz` row was prefigured by the exploratory pass, was recovered by the article-local build, remained stable under leave-one-out template perturbation, and retained low empirical permutation p-values. That is enough to claim that a rest-anchored capacity-guidance deviation score can be measured on this cohort.

Second, the score changes the disease story relative to the narrower MNJ paper @langell2026_photic_stress. The updated `mdr_median` line is strongest for `AD vs Healthy` at `PHOTO 20 Hz`, whereas the present ESB-2 line is strongest at `PHOTO 15 Hz` and separates both `AD` and `FTD` from Healthy. Composite deviation is therefore broader than the earlier single-metric signal, but also less diagnosis-specific. In practical terms, ESB-2 looks more like a disease-versus-Healthy perturbational score than an AD-only marker.

Third, the decomposition matters. The strongest signed movement is capacity-led: `AD` shows corrected negative posterior `Delta C` at `PHOTO 5/10/15 Hz`, and `FTD` shows the same broad signed direction even though its capacity-only rows are weaker than the full composite. Guidance contributes additional spread, but it is not independently convincing on this surface. That makes the current article more about abnormal response geometry than about a pure rotational-collapse narrative.

Fourth, the comparator panel makes the interpretation more credible. Some ordinary posterior measures, especially alpha-linked power change, do show disease-versus-Healthy separation on the same rest-subtracted surface. But their relationship to ESB-2 is weak and becomes near-null within the disease-only subset. That suggests that ESB-2 partly overlaps with familiar posterior photic response changes without collapsing to a single conventional measure. Because exact narrowband stimulation-frequency amplitude was not available on the frozen feature surface, this remains a broad posterior control rather than a definitive entrainment control.

Fifth, `PHOTO 15 Hz` should not be overread. It is the strongest observed frequency on the present four-frequency surface and survives a small frequency-only audit within the primary specification, but that does not make it a confirmed resonance peak. The additional corrected `FTD` rows at `PHOTO 5 Hz` and `PHOTO 10 Hz` argue more for a broader disease-sensitive frequency band than for a single sharp resonance point. The negative PRL result is especially important here because it argues against a stable frequency-profile claim.

Sixth, the negative PRL result is still useful. A four-point correlation-based profile score was simple and auditable, but it did not survive as an article-level discriminator. The current data therefore support a strong stage-local perturbational score more clearly than a resonance-loss theorem. A future PRL revision may still succeed, but it would likely require denser frequency support or a different profile summary.

= Limitations

Seven limitations define the present claim boundary.

1. The article's central comparison uses a resting, eyes-closed ds004504 anchor against an eyes-open, stimulus-evoked ds006036 surface. That is suitable for subject-aligned baseline subtraction, but not for a state-matched recovery theorem.
2. The primary ESB-2 specification was selected from exploratory work before the article-local rerun. The present manuscript therefore reports an internally stabilized development-stage metric rather than an externally validated one.
3. The frozen primary surface retains `86` matched subjects rather than all `88` photic participants, because the composite score requires both posterior capacity and global guidance on both datasets.
4. The planned global-capacity sensitivity branch did not yield analyzable primary-stage contrasts on the frozen export.
5. PRL was tested over only four frequencies and did not stabilize as a corrected group discriminator. It therefore remains secondary.
6. The comparator panel is limited to exported broad-band and entropy features. Exact narrowband stimulation-frequency SSVEP amplitude was not available on the frozen contract, so the nearest-band posterior power proxy should be read as an approximation rather than as a direct entrainment estimate.
7. Coverage drops at `PHOTO 20 Hz`, especially in `FTD` and the matched Healthy subset, and age- / sex-adjusted ESB-2 sensitivity was not included in the present build. Cross-frequency disease profiles should therefore not be interpreted as complete response curves.

Within those limits, the new paper still shows something concrete: disease groups deviate from the Healthy photic response template more strongly than Healthy controls do, and the cleanest departure localizes to a posterior-capacity-led composite rather than to a simple resting-state baseline deficit or a single conventional posterior comparator.

= Conclusion

This follow-up article supports a bounded perturbational-deviation claim. On the validated exact-block ds006036 plus ds004504 surface, ESB-2 is reproducibly elevated in both `AD` and `FTD` relative to Healthy, with the clearest shared peak at `PHOTO 15 Hz`. The signal is capacity-led, remains present under cross-fitted Healthy rescoring, and is only weakly tracked by the conventional posterior comparator panel. At the same time, the current data describe an internally stabilized development-stage metric rather than an externally validated biomarker, and they do not justify broader claims about resonance loss or recovery failure. Those remain natural next targets for more state-matched and frequency-dense datasets.

= Appendix

#figure(
  image("figures/appendix_figure_prl_profiles.svg", width: 100%),
  caption: [Secondary PRL profile panel. The left subpanel shows mean ESB-2 profiles across PHOTO 5, 10, 15, and 20 Hz on the primary specification. The right subpanel shows subject-level PRL distributions. This panel is retained for transparency but is not promoted to a main finding because PRL did not yield a corrected article-level group row.]
) <fig-prl>

#figure(
  image("figures/appendix_figure_recovery_residual.svg", width: 100%),
  caption: [State-mismatched post-photic residual relative to the ds004504 eyes-closed rest anchor. This panel is retained for transparency but is not promoted to a main claim because the resting anchor is not state matched to the post-photic residual state.]
) <fig-recovery>

#bibliography("alzheimer_ftd_reference_list.bib", title: [References])
