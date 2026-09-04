#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data - Depressive Symptom Geometry Across Rest and Probabilistic Selection",
  short-title: "Depression Probabilistic Selection Data",
  subtitle: "Selected block inventories, event summaries, and supplementary violin displays",
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

This supplement collects the data-heavy tables moved out of the main article:

1. selected task-state low/high BDI rows,
2. selected continuous-BDI task-state rows,
3. exploratory clinical-band rows,
4. event-window summaries,
5. paired task-minus-rest summaries,
6. and supplementary violin displays for the main task, event, and paired-delta surfaces.

= Cohort table

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
  caption: [Article-local task cohort summary from `results/demography_summary.csv`.]
) <tab-s2-cohort>

= Selected task-state low-versus-high BDI rows

#figure(
  kind: table,
  table(
    columns: (1.4fr, 1.7fr, 1.6fr, 0.9fr, 0.9fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Block*], [*Analysis type*], [*Metric*], [*Low mean*], [*High mean*], [*`d`*], [*`q`*]),
    [`Task 3D MNPS`], [`global_mnps_3d`], [`d_median`], [`0.198`], [`0.108`], [`-0.145`], [`0.612`],
    [`Task 9D MNPS`], [`global_mnps_9d`], [`d_s_mean`], [`0.456`], [`0.363`], [`-0.099`], [`0.848`],
    [`Task 3D MNJ`], [`global_mnps_jacobian_3d`], [`spectral_radius_median`], [`0.0633`], [`0.0640`], [`0.069`], [`0.996`],
    [`Task 9D MNJ`], [`global_mnps_jacobian_9d`], [`rotational_power_mean`], [`0.0335`], [`0.0346`], [`0.214`], [`0.404`],
    [`Task 9x9 block MNJ`], [`global_mnps_jacobian_9d_block_jacobian`], [`block_frobenius_mean (e -> d)`], [`0.650`], [`0.339`], [`-0.778`], [`0.0109`],
    [`Task reachability`], [`reachability_cones`], [`tube_log_eig_var_mean`], [`7.755`], [`5.537`], [`-0.719`], [`0.0107`],
    [`Task tier-2 EMMI`], [`tier2_emmi`], [`mv_median`], [`0.0239`], [`0.0222`], [`-0.004`], [`0.975`],
    [`Task distribution`], [`dist_summary`], [`e_m_mad_sigma`], [`0.179`], [`0.368`], [`0.506`], [`0.665`],
  ),
  caption: [Selected task-state low-versus-high BDI rows from `results/selected_metrics_summary.csv`. The strongest corrected rows remain block-MNJ and reachability.]
) <tab-s2-task-lowhigh>

= Selected task-state continuous BDI rows

#figure(
  kind: table,
  table(
    columns: (1.4fr, 1.7fr, 1.55fr, 0.8fr, 0.8fr, 0.7fr),
    align: left,
    inset: 4pt,
    table.header([*Block*], [*Analysis type*], [*Metric*], [*N*], [*`rho`*], [*`q`*]),
    [`Task 3D MNPS`], [`global_mnps_3d`], [`d_median`], [`121`], [`-0.041`], [`0.758`],
    [`Task 9D MNPS`], [`global_mnps_9d`], [`d_s_mean`], [`121`], [`-0.055`], [`0.903`],
    [`Task 3D MNJ`], [`global_mnps_jacobian_3d`], [`spectral_radius_median`], [`121`], [`0.081`], [`0.547`],
    [`Task 9D MNJ`], [`global_mnps_jacobian_9d`], [`rotational_power_mean`], [`70`], [`0.011`], [`0.949`],
    [`Task 9x9 block MNJ`], [`global_mnps_jacobian_9d_block_jacobian`], [`block_frobenius_mean (e -> d)`], [`70`], [`-0.345`], [`0.0938`],
    [`Task reachability`], [`reachability_cones`], [`tube_log_eig_var_mean`], [`69`], [`-0.398`], [`0.00271`],
    [`Task tier-2 EMMI`], [`tier2_emmi`], [`mv_median`], [`121`], [`-0.002`], [`0.981`],
    [`Task distribution`], [`dist_summary`], [`e_m_mad_sigma`], [`121`], [`0.313`], [`0.0290`],
  ),
  caption: [Selected continuous-BDI task rows from `results/bdi_correlations_summary.csv` (`All_valid` cohort).]
) <tab-s2-task-rho>

= Exploratory clinical-band rows

The table below highlights the clinically interpretable comparisons that were most helpful for contextualizing the main low/high result.

#figure(
  kind: table,
  table(
    columns: (1.55fr, 1.55fr, 1.6fr, 0.85fr, 0.85fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Split*], [*Block*], [*Metric*], [*Left mean*], [*Right mean*], [*`d`*], [*`q`*]),
    [`0-13 vs 14-19`], [`Task reachability`], [`tube_log_eig_var_mean`], [`7.755`], [`6.109`], [`-0.492`], [`0.139`],
    [`0-13 vs 14-19`], [`Task distribution`], [`e_m_mad_sigma`], [`0.179`], [`0.596`], [`1.093`], [`0.137`],
    [`0-13 vs 20-63`], [`Task 9x9 block MNJ`], [`block_frobenius_mean (e -> d)`], [`0.650`], [`0.339`], [`-0.778`], [`0.0109`],
    [`0-13 vs 20-63`], [`Task reachability`], [`tube_log_eig_var_mean`], [`7.755`], [`5.537`], [`-0.719`], [`0.0107`],
    [`14-19 vs 20-63`], [`Task reachability`], [`tube_log_eig_var_mean`], [`6.109`], [`5.537`], [`-0.474`], [`1.00`],
    [`14-19 vs 20-63`], [`Task distribution`], [`e_m_mad_sigma`], [`0.596`], [`0.368`], [`-0.516`], [`0.917`],
  ),
  caption: [Selected clinical-band comparisons from `results/clinical_bdi_bin_summary.csv`.]
) <tab-s2-bdi-bands>

= Event-window summaries

The task-window layer remained exploratory and was dominated by `speed_mean`. The event-bin low/high BDI rows are shown below.

#figure(
  kind: table,
  table(
    columns: (1.45fr, 0.9fr, 0.9fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Event family*], [*Metric*], [*`d`*], [*`p`*], [*`q`*]),
    [`feedback_correct`], [`speed_mean (event)`], [`0.249`], [`0.257`], [`0.309`],
    [`feedback_incorrect`], [`speed_mean (event)`], [`0.269`], [`0.215`], [`0.258`],
    [`train_stim_any`], [`speed_mean (event)`], [`0.249`], [`0.251`], [`0.301`],
    [`test_stim_any`], [`speed_mean (event)`], [`0.089`], [`0.685`], [`0.685`],
    [`left_response`], [`speed_mean (event)`], [`0.206`], [`0.340`], [`0.408`],
    [`right_response`], [`speed_mean (event)`], [`0.261`], [`0.255`], [`0.383`],
  ),
  caption: [Event-bin low/high BDI rows from `results/event_locked_summary.csv`. None survived FDR correction.]
) <tab-s2-event-lowhigh>

The strongest continuous event suggestions were:

1. `feedback_incorrect / post_far / speed_mean`: `rho = 0.203`, `q = 0.0764`
2. `train_stim_any / post_far / speed_mean`: `rho = 0.196`, `q = 0.0931`
3. `feedback_correct / post_far / speed_mean`: `rho = 0.189`, `q = 0.115`

= Paired task-minus-rest summaries

#figure(
  kind: table,
  table(
    columns: (1.45fr, 1.55fr, 0.85fr, 0.85fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Block*], [*Metric*], [*Low mean*], [*High mean*], [*`d`*], [*`q`*]),
    [`3D MNPS`], [`d_median`], [`-0.101`], [`-0.218`], [`-0.165`], [`0.804`],
    [`9D MNPS`], [`d_s_mean`], [`-0.858`], [`-0.720`], [`0.126`], [`0.804`],
    [`3D MNJ`], [`spectral_radius_median`], [`0.00151`], [`0.00195`], [`0.036`], [`0.869`],
    [`9D MNJ`], [`rotational_power_mean`], [`-0.00518`], [`-0.00606`], [`-0.147`], [`0.804`],
    [`Block MNJ m->m`], [`block_frobenius_mean`], [`0.114`], [`0.125`], [`0.085`], [`0.804`],
    [`Reachability`], [`tube_log_eig_var_mean`], [`-0.811`], [`-1.308`], [`-0.130`], [`0.804`],
    [`Tier-2 EMMI`], [`mv_median`], [`-0.105`], [`0.113`], [`0.337`], [`0.804`],
    [`Distribution summary`], [`e_m_mad_sigma`], [`0.00991`], [`-0.110`], [`-0.260`], [`0.804`],
  ),
  caption: [Selected low/high BDI paired `task - rest` rows from `results/paired_delta_summary.csv`.]
) <tab-s2-paired>

The paired continuous correlations were uniformly weak, with all `q` values equal to `0.915` in the selected paired block inventory.

= Supplementary violin displays

#figure(
  image("figures/supp_violin_task_blocks.png", width: 100%),
  caption: [Supplementary violin plot for the eight selected task-state blocks by BDI band.]
) <fig-s2-task-violins>

#figure(
  image("figures/supp_violin_event_speed.png", width: 100%),
  caption: [Supplementary event-window violin plot for `speed_mean` in the `event` bin across the six article-facing event families.]
) <fig-s2-event-violins>

#figure(
  image("figures/supp_violin_paired_delta.png", width: 100%),
  caption: [Supplementary violin plot for the eight selected paired `task - rest` blocks by BDI band.]
) <fig-s2-paired-violins>

= Files

This supplement is backed mainly by:

- `results/demography_summary.csv`
- `results/selected_metrics_summary.csv`
- `results/bdi_correlations_summary.csv`
- `results/clinical_bdi_bin_summary.csv`
- `results/event_locked_summary.csv`
- `results/event_locked_correlation_summary.csv`
- `results/paired_delta_summary.csv`
- `results/paired_delta_correlation_summary.csv`
