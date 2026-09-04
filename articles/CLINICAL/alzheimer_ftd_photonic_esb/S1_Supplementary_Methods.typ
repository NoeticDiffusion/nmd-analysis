#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods - Evoked Structural Brittleness Under Photic Stimulation in Alzheimer Disease and Frontotemporal Dementia",
  short-title: "ESB Supplementary Methods",
  subtitle: "Exact block-native photic contract, ds004504 anchoring, and ESB-2 construction",
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

This supplement records the extended methods for the ESB follow-up article. It focuses on:

1. the ds006036 plus ds004504 comparability contract,
2. the exact block-native photic selection inherited from the sibling paper,
3. the ESB-2 score definition,
4. the cross-fitted Healthy-template check,
5. the comparator and PRL side branches,
6. and the FDR / QC design used to keep the article review-stable.

= Datasets and comparability contract

The ESB rerun couples:

- `data/raw/neuralmanifolddynamics_ds006036_20260604_132747`
- `data/raw/neuralmanifolddynamics_ds004504_20260528_114734`

Subject-level ds004504 baselines were available for all `88` photic participants. The frozen primary ESB-2 surface further requires both posterior capacity and global guidance on both datasets, leaving a matched `86`-subject surface:

- `Healthy = 27`
- `AD = 36`
- `FTD = 23`

This remains a bounded comparison because ds004504 is resting and eyes-closed, whereas the ds006036 surface is eyes-open and stimulus-evoked. The rest branch is therefore used as a subject-aligned baseline anchor rather than as a full state-matched control.

= Noetic Diffusion and NeuralManifoldDynamics framing

The main paper uses two nested levels of description.

- Noetic Diffusion Theory is the broader dynamical framing.
- NeuralManifoldDynamics is the operational export layer that fixes auditable charts, Jacobian summaries, and reachability summaries.

In the present manuscript, the exported coordinate state is treated as a measurement contract rather than as proof that one unique latent ontology has been recovered. The paper tests group differences and MMSE structure on those exported observables only.

== NeuralManifoldDynamics chart basis

The coma manuscript does not define `m`, `d`, and `e` de novo inside the downstream article code. Instead, it consumes H5 exports produced under a fixed `NeuralManifoldDynamics` measurement contract, so the coordinate definitions are inherited from that release rather than re-estimated from the pooled cohort.@langell2026_mndm

The canonical `3D` chart is

$ x_t = [m_t, d_t, e_t] $

and the stratified chart is

$ x_t^((9)) = [m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m] $

where the `m`, `d`, and `e` labels should be read as fixed operational chart labels in the current release contract rather than as uniquely privileged latent biological variables.@langell2026_mndm

Under the active EEG contract used for the I-CARE article, the nine subcoordinates are built from fixed feature families before recomposition to `3D`:

#figure(
  kind: table,
  table(
    columns: (0.9fr, 1.05fr, 2.3fr),
    align: left,
    inset: 4pt,
    table.header([*Family*], [*Subcoordinate*], [*EEG operational mapping in active contract*]),
    [`m`], [`m_a`], [`-0.5 * eeg_delta - 0.5 * eeg_theta`],
    [`m`], [`m_e`], [`-1.0 * eeg_alpha`],
    [`m`], [`m_o`], [`eeg_beta_alpha`],
    [`d`], [`d_n`], [`eeg_gamma`],
    [`d`], [`d_l`], [`eeg_hjorth_mobility`],
    [`d`], [`d_s`], [`eeg_alpha_theta`],
    [`e`], [`e_e`], [`eeg_permutation_entropy`],
    [`e`], [`e_s`], [`eeg_hjorth_complexity`],
    [`e`], [`e_m`], [`embodied_arousal_proxy`],
  ),
  caption: [Fixed EEG-side `9D` chart used by the `NeuralManifoldDynamics` release inherited in this manuscript.@langell2026_mndm]
) <tab-s1-nmdm-9d>

The exported `mnps_3d` trajectory is then derived from a fixed weighted `9D -> 3D` projection:

$ m_t = 0.62 m_a + 0.55 m_e + 0.45 m_o $

$ d_t = 0.50 d_n + 0.82 d_l + 0.28 d_s $

$ e_t = 0.85 e_e + 0.62 e_s + 0.03 e_m $

Operationally, the upstream contract standardizes the contributing feature columns, applies coverage-aware renormalization when some subcoordinate support is missing, and records the resulting `3D` and `9D` trajectories as serialized measurement objects rather than as article-specific fitted axes.@langell2026_mndm The spread, Jacobian, and reachability summaries analyzed in this manuscript therefore inherit a versioned chart definition from `NeuralManifoldDynamics`.


= Exact block-native photic surface

The ESB manuscript inherits the exact block-native selection rule from the sibling photic export. Original windows are kept when their centers fall inside inferred H5 photic block intervals.

This yields the following stage inventory on the underlying ds006036 surface:

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
  caption: [Inherited photic selection inventory from the sibling `blocknative_selection_blocks.csv` export.]
) <tab-s1-esb-block-selection>

On the primary ESB-2 specification, analyzable stage counts are lower because the composite score requires matched ds004504 values and both axes on both datasets:

#figure(
  kind: table,
  table(
    columns: (1.8fr, 0.9fr, 0.9fr, 0.9fr, 0.9fr),
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
    [FTD], [22], [22], [22], [12],
  ),
  caption: [Primary ESB-2 stage coverage from `stage_coverage_summary.csv`.]
) <tab-s1-esb-stage-coverage>

= ESB-2 construction

For each subject and photic stage, the primary score uses:

- posterior capacity = parietal-occipital `tube_d_eff_median`,
- guidance = global `9D` `rotational_power_median`,
- baseline subtraction against the same subject's ds004504 summary.

Writing the rest-subtracted axes as `Delta C_i(f)` and `Delta R_i(f)`, the Healthy-template medians as `h_C(f)` and `h_R(f)`, and the robust Healthy scaling factors as `s_C(f)` and `s_R(f)`, the article-local score is:

$ "ESB-2"_i(f) = frac(1, sqrt(2)) sqrt((frac(Delta C_i(f) - h_C(f), s_C(f) + epsilon))^2 + (frac(Delta R_i(f) - h_R(f), s_R(f) + epsilon))^2) $

The score is therefore a two-axis distance from the Healthy median response after robust within-Healthy scaling. Higher ESB-2 means the subject deviates farther from the Healthy photic response template on this specific capacity-guidance plane.

= Cross-fitted Healthy-template check

The strongest template-circularity concern is that Healthy subjects contribute to the same template used to score them. The rerun therefore includes a cross-fitted Healthy variant:

1. each Healthy subject is rescored against a template that excludes that subject,
2. AD and FTD subjects remain scored against the full Healthy template,
3. the resulting contrast table is exported separately as `qc_cross_fitted_esb2_contrasts.csv`.

This does not create an external validation cohort, but it does bound in-sample shrinkage on the headline row.

= Secondary branches

The ESB follow-up keeps three secondary branches explicit.

1. Axis decomposition: `delta_capacity_rest` and `delta_guidance_rest` are analyzed separately to test whether the composite score is capacity-led or guidance-led.
2. PRL: a profile-based frequency-shape extension computed from the four-point ESB-2 profile.
3. Recovery / residual branches: retained for transparency, but kept outside the main claim boundary because the ds004504 resting anchor is not state matched to the post-photic residual state.

= Conventional comparator panel

To test whether ESB-2 merely re-labels familiar EEG change, the rerun adds a compact posterior comparator surface:

1. stage-matched posterior band-power proxy,
2. posterior alpha power,
3. posterior alpha/theta ratio,
4. posterior sample entropy.

All comparator values are summarized within the same exact block-native photic windows and then rest-subtracted against ds004504. Direct narrowband stimulation-frequency SSVEP amplitude was not available on the frozen contract, so the first branch is only a nearest-band posterior power proxy.

= Statistics and FDR families

Between-group contrasts are computed for:

1. `AD vs Healthy`,
2. `FTD vs Healthy`,
3. `AD vs FTD`.

The article uses:

- Mann-Whitney tests with Cohen's `d` for group contrasts,
- BH-FDR within explicitly defined score families,
- a separate frequency-only audit for the primary ESB-2 specification,
- leave-one-out template checks,
- permutation tests,
- recovery-subset stability checks,
- and comparator correlation tables.

The main FDR families are:

- ESB-2 / residual variants,
- axis decomposition,
- PRL,
- comparator contrasts,
- ESB-comparator correlations.

= Interpretation boundary

The review-stable interpretation rule is:

1. the exact block-native ds006036 surface defines the canonical photic branch,
2. the ds004504 branch is a subject-aligned baseline, not a state-matched recovery theorem,
3. ESB-2 is the headline score and PRL remains secondary,
4. the comparator panel is a broad posterior control rather than a definitive entrainment control,
5. negative `AD vs FTD` and PRL results remain explicit.

= Files

The main result bundle for this supplement is:

- `articles/CLINICAL/alzheimer_ftd_photonic_esb/results`

Especially:

- `esb_article_manifest.json`
- `esb_subject_scores.csv`
- `esb_contrasts.csv`
- `esb_axis_contrasts.csv`
- `qc_cross_fitted_esb2_scores.csv`
- `qc_cross_fitted_esb2_contrasts.csv`
- `prl_subject_scores.csv`
- `prl_contrasts.csv`
- `stage_coverage_summary.csv`
- `dataset_comparability_summary.csv`
- `qc_spec_sensitivity_summary.csv`
- `conventional_comparator_subject_stage.csv`
- `conventional_comparator_contrasts.csv`
- `conventional_comparator_esb2_correlations.csv`


#bibliography("alzheimer_ftd_reference_list.bib", title: [References])