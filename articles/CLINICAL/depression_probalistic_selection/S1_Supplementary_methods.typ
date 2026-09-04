#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods - Depressive Symptom Geometry Across Rest and Probabilistic Selection",
  short-title: "Depression Probabilistic Selection Methods",
  subtitle: "Paired rest-task design, task-state export surface, and event-window layer",
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

This supplement records the extended methods for the paired depression probabilistic-selection manuscript. It focuses on:

1. the paired cohort and metadata bridge,
2. the task-state and paired block surfaces,
3. the exploratory event-window layer,
4. the statistical reporting rules,
5. and the supplementary QC / violin-plot support scripts added for this article.

= Cohort and paired overlap

The task dataset is `ds003474`, processed from:

- `data/raw/neuralmanifolddynamics_ds003474_20260609_044822`

The resting comparison arm reuses the established depression resting-state article surface from `ds003478`, with subject matching based on shared `participant_id` (`sub-001` etc.) and validated `Original_ID`.

The article-local participant table is:

- `articles/CLINICAL/depression_probalistic_selection/metadata/participants.tsv`

The paired overlap audit found:

1. `122` task subjects in the processed task bundle,
2. `122` rest subjects in the re-used resting-state export,
3. `121` participants with usable BDI values,
4. one invalid metadata row (`sub-038`) excluded from inferential summaries.

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
  caption: [Task-cohort summary derived from `results/demography_summary.csv`.]
) <tab-s1-cohort>

= NeuralManifoldDynamics measurement stack

The task manuscript inherits a fixed NeuralManifoldDynamics export surface rather than re-estimating article-specific axes. The operational chart layers analyzed here are:

1. global `MNPS 3D`
2. global `MNPS 9D`
3. global `MNJ 3D`
4. global `MNJ 9D`
5. global `9D` block-Jacobian
6. reachability cones
7. `tier2_emmi`
8. distribution summaries

In compact notation, the exported first-order chart is

$ x_t = [m_t, d_t, e_t] $

and the stratified chart is

$ x_t^((9)) = [m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m] $

The manuscript treats these as auditable measurement contracts, not as proof that one unique latent biological ontology has been recovered.

= Task-state and paired block surfaces

The article-local task exports were built from:

- `data/analysis/depression_probsel_ds003474_20260609/ds003474_subject_metrics_20260609_090225.parquet`
- `data/analysis/depression_probsel_ds003474_20260609/ds003474_contrast_results_20260609_090228.parquet`

The resting comparison arm was read from:

- `data/analysis/depression_ds003478_20260521/ds003478_subject_metrics_20260522_120333.parquet`

The selected paper-facing block inventory used in the main article is:

#figure(
  kind: table,
  table(
    columns: (1.2fr, 1.45fr, 1.9fr, 1.4fr),
    align: left,
    inset: 4pt,
    table.header([*Block key*], [*Title*], [*Analysis type*], [*Selected metric*]),
    [`mnps_3d`], [`Task 3D MNPS`], [`global_mnps_3d`], [`d_median`],
    [`mnps_9d`], [`Task 9D MNPS`], [`global_mnps_9d`], [`d_s_mean`],
    [`mnj_3d`], [`Task 3D MNJ`], [`global_mnps_jacobian_3d`], [`spectral_radius_median`],
    [`mnj_9d`], [`Task 9D MNJ`], [`global_mnps_jacobian_9d`], [`rotational_power_mean`],
    [`block_mnj`], [`Task 9x9 block MNJ`], [`global_mnps_jacobian_9d_block_jacobian`], [`block_frobenius_mean`],
    [`reachability`], [`Task reachability`], [`reachability_cones`], [`tube_log_eig_var_mean`],
    [`emmi`], [`Task tier-2 EMMI`], [`tier2_emmi`], [`mv_median`],
    [`distribution`], [`Task distribution summary`], [`dist_summary`], [`e_m_mad_sigma`],
  ),
  caption: [Selected task-state blocks carried into the main paired rest-task manuscript.]
) <tab-s1-blocks>

For the paired surface, the same selected block metrics were combined as:

$ Delta_i^(T-R) = y_i^T - y_i^R $

for each participant `i`, then tested against BDI as both a low/high contrast and a continuous symptom axis.

= Event-window layer

The task H5 files expose:

1. `event_windows/event_id`
2. `event_windows/event_label_key`
3. `event_windows/event_start_window_index`
4. `event_windows/event_stop_window_index`
5. `event_windows/bin_label`

The main paired article uses a conservative event summary layer built from six event families:

1. `feedback_correct`
2. `feedback_incorrect`
3. `train_stim_any`
4. `test_stim_any`
5. `left_response`
6. `right_response`

Each family is summarized over:

1. `pre_far`
2. `pre_near`
3. `event`
4. `post_near`
5. `post_far`

using cohort-anchored `m`, `d`, `e`, `e_m`, `m_o`, and `speed_mean`.

This layer is intentionally weaker and more exploratory than the task-state block surface. It was designed to ask whether broad event families added clinically coherent information, not to build a full subject-anchored event wrapper. That more task-native event-first design is treated separately in the sister event-focused article.

= Statistical conventions

The paired rest-task article uses three complementary depression summaries:

1. low-versus-high BDI: `BDI 0-13` vs `BDI 20-63`
2. continuous BDI correlations across `All_valid`, `LowHigh_only`, and `High_BDI_only`
3. exploratory clinical BDI-band contrasts: `0-13`, `14-19`, `20-63`

The generated `ds003474 contrast_results` parquet contained no task-facing contrast rows for the primary low/high comparison. The article therefore recomputed those selected low-versus-high task summaries directly from `subject_metrics`, preserving the same BDI-band definitions as the resting-state article.

BH-FDR correction is applied within the relevant article-local family blocks. The main text is intentionally selective: it emphasizes the most coherent corrected rows rather than treating every exported metric as an equal headline candidate.

= Supplementary support scripts

In addition to the original article scripts:

- `src/run_depression_probsel_pipeline.py`
- `src/build_depression_probsel_exports.py`
- `src/build_depression_probsel_figures.py`

this supplement adds:

1. `src/run_depression_probsel_additional_qc.py`
2. `src/build_depression_probsel_violin_plots.py`
3. `src/run_depression_probsel_supplement_pipeline.py`

These scripts generate:

- denominator / coverage summaries,
- event-coverage summaries,
- leave-one-subject-out robustness checks for the selected block rows,
- and supplementary violin plots for task-state, event-window, and paired-delta values by BDI band.

= Files

The methods and supplement-facing bundle are anchored mainly to:

- `results/paper_exports_manifest.json`
- `results/selected_metrics_summary.csv`
- `results/bdi_correlations_summary.csv`
- `results/clinical_bdi_bin_summary.csv`
- `results/event_locked_summary.csv`
- `results/event_locked_correlation_summary.csv`
- `results/paired_delta_summary.csv`
- `results/paired_delta_correlation_summary.csv`
- `results/additional_qc_20260609/additional_qc_summary.md`
