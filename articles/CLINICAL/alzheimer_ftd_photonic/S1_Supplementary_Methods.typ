#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods - Evoked Neural Geometry Under Photic Stress in Alzheimer Disease and Frontotemporal Dementia",
  short-title: "Photic Supplementary Methods",
  subtitle: "Exact block-native selection, dual-anchor bundle contract, and resting-reference path",
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

This supplement records the extended methods for the canonical Alzheimer/FTD photic rerun. It focuses on:

1. the processed ds006036 bundle contract,
2. the exact block-native selection rule,
3. the dual-anchor measurement surface,
4. the ds004504 resting-reference path,
5. the metric and statistics boundary,
6. and the file-level contract used by the main paper.

= Processed bundle contract

The canonical rerun consumes:

- `data/raw/neuralmanifolddynamics_ds006036_20260604_132747`

This bundle is the article's primary ds006036 surface. It exposes:

- subject-anchored and cohort-anchored `3D` coordinates,
- subject-anchored and cohort-anchored `9D` coordinates,
- global `3D` and `9D` Jacobians,
- regional `3D` `MNPS`, regional `3D` Jacobians, and regional `3D` reachability outputs,
- `labels/stage` and stage codebooks,
- block-native metadata through `/blocks` and `/block_windows`,
- participant-level clinical fields including diagnosis and MMSE,
- and the usual provenance / QC groups.

The validated manuscript-facing stage surface remains restricted to:

- `PHOTO 5 Hz`
- `PHOTO 10 Hz`
- `PHOTO 15 Hz`
- `PHOTO 20 Hz`

Support above `20 Hz` remained too sparse for review-stable main-text inference.

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


= Exact block-native selection

The key methodological change in this rerun is that the photic surface is no longer built from a recovery-expanded stage overlay. Instead, the article uses the block metadata already present in the H5 contract.

Operationally:

1. read photic block intervals from `/blocks`,
2. identify the corresponding original exported windows,
3. keep an original window when its center falls inside the exact block interval,
4. aggregate only those retained original windows into the article-facing stage summaries.

This yields a leaner but cleaner surface than the earlier recovery-centric run:

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
  caption: [Exact block-native stage inventory from `blocknative_selection_blocks.csv`. Across all frequencies, the canonical rerun retains `1757` original windows across `397` block instances in `88` subjects.]
) <tab-s1-block-selection>

The selection summary written by the pipeline is:

- `selection_mode = blocks::center_within_exact_block_interval`
- `contract = cohort_anchored`
- `n_subjects_with_blocks = 88`
- `n_selected_block_instances = 397`
- `n_selected_original_windows = 1757`

= Dual-anchor bundle design

Although the main article keeps its inferential surface on the cohort-shared contract, the ds006036 bundle is dual-anchor:

- `subject_anchored` coordinates preserve subject-centered geometry,
- `cohort_anchored` coordinates define the shared between-subject comparison frame.

The present main paper uses the cohort-anchored surface for both group contrasts and MMSE summaries because the central questions are between-subject and diagnosis-facing. The subject-anchored layers remain useful for auditability and future within-subject extensions, but they are not part of the headline inferential surface here.

= Resting-state reference path

The internal baseline comparison uses:

- `data/raw/neuralmanifolddynamics_ds004504_20260528_114734`

This ds004504 branch is intentionally narrow. It reuses the same diagnostic contrasts, but only the overlapping global `3D` and `9D` MNJ `mdr_median` rows are promoted into the manuscript-facing rest-versus-photic reference bundle.

The reference therefore answers one bounded question: whether the main `AD vs Healthy` MNJ effect already exists at comparable strength on the shared resting surface.

= Metric families

The photic paper centers on two exported families.

1. Reachability summaries, especially `tube_d_eff_median` and `tube_capture_gate_median`.
2. MNJ summaries, especially `mdr_median`, with supporting `spectral_radius_median`, `rotational_power_median`, `frobenius_norm_median`, `trace_median`, and `anisotropy_abs_eig_median`.

The manuscript's main corrected group rows localize to `mdr_median`, but the broader MMSE layer retains supporting rows on the other MNJ summaries.

= Statistics boundary

Between-group contrasts are computed for:

1. `AD vs Healthy`,
2. `FTD vs Healthy`,
3. `AD vs FTD`.

The main paper uses:

- Mann-Whitney tests for group contrasts,
- Cohen's `d` as the effect-size summary,
- Spearman `rho` for MMSE association in `Dementia_all`, `AD_only`, and `FTD_only`,
- BH-FDR within each `contrast x stage x analysis_type` family for group rows,
- BH-FDR within each `cohort x stage x analysis_type` family for MMSE rows.

The exploratory run-level block-Jacobian appendix is handled separately because it is not frequency-stratified.

= Interpretation boundary

The review-stable interpretation rule is:

1. exact block-native window selection defines the canonical photic surface,
2. group claims are restricted to corrected rows on the cohort-shared main export,
3. the ds004504 branch is a narrow internal reference rather than a second full article surface,
4. the block-Jacobian family scan is appendix material rather than a co-equal headline layer,
5. and negative results are reported explicitly rather than hidden.

= Files

The main result bundle for this supplement is:

- `articles/CLINICAL/alzheimer_ftd_photonic/results`

Especially:

- `paper_exports_manifest.json`
- `blocknative_selection_blocks.csv`
- `blocknative_selection_summary.json`
- `subject_stage_region_metrics.csv`
- `group_frequency_contrasts.csv`
- `mmse_correlations_summary.csv`
- `selected_stage_metrics_summary.csv`
- `rest_vs_photic_reference/rest_vs_photic_reference.md`
- `block_jacobian_exploration_132747/block_jacobian_exploration_summary.md`
- `block_jacobian_exploration_132747/block_jacobian_unique_family_appendix_summary.md`


#bibliography("alzheimer_ftd_reference_list.bib", title: [References])