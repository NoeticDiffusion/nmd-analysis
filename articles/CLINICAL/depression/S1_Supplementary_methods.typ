#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods - Resting-State Neural Geometry Across Depressive Symptom Burden",
  short-title: "Depression Supplementary Methods",
  subtitle: "Resting-state export surface, BDI regime contrasts, and centroid-adjusted sensitivity analysis",
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

This supplement records the extended methods for the resting-state depression article. It focuses on:

1. the processed bundle and cohort bridge,
2. the article-facing NeuralManifoldDynamics measurement surface,
3. the selected paper-facing block logic,
4. the continuous and banded BDI analyses,
5. the centroid-adjusted sensitivity analysis,
6. and the supplementary QC / violin-plot support scripts.

= Processed bundle and cohort bridge

The resting-state manuscript uses the processed ds003478 bundle exposed through:

- `data/analysis/depression_ds003478_20260521/ds003478_subject_metrics_20260522_120333.parquet`
- `data/analysis/depression_ds003478_20260521/ds003478_contrast_results_20260522_120336.parquet`

The article-local metadata bridge is:

- `articles/CLINICAL/depression/metadata/participants.tsv`

The participant table contains `122` rows, of which `121` have usable BDI values. One row (`sub-038`) is flagged as invalid and excluded from the symptom-facing summaries.

#figure(
  kind: table,
  table(
    columns: (1.8fr, 0.8fr, 1.1fr, 1.1fr, 1.3fr, 1.1fr, 1.1fr),
    align: (left, center, center, center, center, center, center),
    inset: 5pt,
    table.header(
      [*BDI band*],
      [*N*],
      [*Age mean*],
      [*Age SD*],
      [*Female n (%)*],
      [*BDI mean*],
      [*BDI median*],
    ),
    [BDI 0-13], [76], [18.97], [1.21], [41 (53.9%)], [1.88], [1.0],
    [BDI 14-19], [15], [18.73], [1.58], [12 (80.0%)], [17.07], [18.0],
    [BDI 20-63], [30], [18.73], [0.91], [21 (70.0%)], [25.10], [25.0],
  ),
  caption: [Article-facing cohort summary from `results/demography_summary.csv`.]
) <tab-s1-cohort>

= NeuralManifoldDynamics measurement surface

The article treats the exported state as a fixed measurement contract rather than as an article-specific latent re-fit. The core chart is

$ x_t = [m_t, d_t, e_t] $

with higher-resolution stratified coordinates

$ x_t^((9)) = [m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m] $

and local Jacobian summaries defined operationally on the exported trajectory.

The article-facing surface spans:

1. global `MNPS 3D`
2. global `MNPS 9D`
3. global `MNJ 3D`
4. global `MNJ 9D`
5. global `9 x 9` block-Jacobian
6. reachability cones
7. `tier2_emmi`
8. distribution summaries
9. supplementary sidecar families such as `tau_summary`, `robust_summary`, `tier2_jacobian`, `features_raw`, and `features_robust_z`

The compact manuscript emphasizes only one selected paper-facing metric per major block family, but the broader inventory remains available in the metric-family sidecars.

= Selected article-facing blocks

The selected low-versus-high BDI surface follows the fixed block logic below.

#figure(
  kind: table,
  table(
    columns: (1.15fr, 1.55fr, 1.8fr, 1.45fr),
    align: left,
    inset: 4pt,
    table.header([*Block key*], [*Title*], [*Analysis type*], [*Selected metric*]),
    [`mnps_3d`], [`Global 3D MNPS`], [`global_mnps_3d`], [`d_median`],
    [`mnps_9d`], [`Global 9D MNPS`], [`global_mnps_9d`], [`d_s_mean`],
    [`mnj_3d`], [`Global 3D MNJ`], [`global_mnps_jacobian_3d`], [`spectral_radius_median`],
    [`mnj_9d`], [`Global 9D MNJ`], [`global_mnps_jacobian_9d`], [`rotational_power_mean`],
    [`block_mnj`], [`9x9 block MNJ`], [`global_mnps_jacobian_9d_block_jacobian`], [`block_anisotropy_mean`],
    [`reachability`], [`Reachability cones`], [`reachability_cones`], [`tube_log_eig_var_mean`],
    [`emmi`], [`Tier-2 EMMI`], [`tier2_emmi`], [`mv_median`],
    [`distribution`], [`Distribution summary`], [`dist_summary`], [`e_m_mad_sigma`],
  ),
  caption: [Selected article-facing blocks from `results/selected_metrics_summary.csv`.]
) <tab-s1-blocks>

The selected metric is not always the strongest metric in the full family. It is the predesignated paper-facing representative for that block family, chosen to keep the compact article review-stable and visually compact.

= Primary, continuous, and clinical-band BDI analyses

The manuscript uses three symptom-facing passes:

1. a primary low-versus-high contrast: `BDI 0-13` versus `BDI 20-63`
2. continuous BDI correlations across `All_valid`, `LowHigh_only`, and `High_BDI_only`
3. exploratory clinical-band contrasts: `0-13 vs 14-19`, `0-13 vs 20-63`, and `14-19 vs 20-63`

The main text gives priority to rows that remain coherent across more than one block family. This prevents one isolated family-specific hit from becoming the entire interpretation.

= Centroid baseline and centroid-adjusted sensitivity

The article includes a supplementary sensitivity pass that separates two questions:

1. *baseline centroid displacement*: do the low- and high-BDI groups differ in first-order `3D` or `9D` position?
2. *centroid-adjusted dynamics*: do selected dynamic blocks remain group-sensitive after covarying out the baseline coordinates of the matching family?

For baseline centroid differences, the main low/high comparison is run directly on selected `3D` and `9D` coordinate means and medians.

For the centroid-adjusted models, the target metric `y_i` is regressed on:

$ y_i = beta_0 + beta_1 g_i + gamma^T c_i + epsilon_i $

where `g_i` is the low/high BDI group indicator and `c_i` is either the `3D` centroid covariate set (`m_mean`, `d_mean`, `e_mean`) or the `9D` centroid covariate set (`d_l_mean`, `d_n_mean`, `d_s_mean`, `e_e_mean`, `e_m_mean`, `e_s_mean`, `m_a_mean`, `m_e_mean`, `m_o_mean`), depending on the target family.

HC3-robust standard errors are used for the adjusted group coefficient, and a residualized Cohen's `d` is also reported as a compact effect-size sidecar.

= Supplementary QC and violin support

In addition to the original article scripts:

- `src/build_depression_paper_exports.py`
- `src/run_depression_bdi_bins.py`
- `src/run_depression_centroid_adjusted_analysis.py`
- `src/build_depression_svg_and_qc.py`

this supplement adds:

1. `src/run_depression_additional_qc.py`
2. `src/build_depression_violin_plots.py`
3. `src/run_depression_supplement_pipeline.py`

These scripts generate:

- selected-block denominator summaries,
- leave-one-subject-out stability summaries,
- centroid-adjusted focus tables,
- and supplementary violin plots for both the selected article blocks and the strongest centroid-baseline coordinates.

= Files

The supplement bundle is anchored mainly to:

- `results/paper_exports_manifest.json`
- `results/selected_metrics_summary.csv`
- `results/bdi_correlations_summary.csv`
- `results/clinical_bdi_bin_summary.csv`
- `results/centroid_baseline_summary.csv`
- `results/centroid_adjusted_dynamic_summary.csv`
- `results/additional_qc_20260609/qc_selected_block_coverage.csv`
- `results/additional_qc_20260609/qc_leave_one_subject_out.csv`
- `results/additional_qc_20260609/qc_centroid_adjusted_focus.csv`
