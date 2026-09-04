#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data - Resting-State Neural Geometry Across Depressive Symptom Burden",
  short-title: "Depression Supplementary Data",
  subtitle: "Selected block inventories, centroid sidecars, and supplementary violin displays",
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

This supplement collects the data-heavy tables moved out of the compact main article:

1. selected low/high BDI rows,
2. selected continuous-BDI rows,
3. exploratory clinical-band rows,
4. centroid baseline rows,
5. centroid-adjusted dynamic rows,
6. broader metric-family sidecars,
7. and supplementary violin displays.

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
  caption: [Cohort summary from `results/demography_summary.csv`.]
) <tab-s2-cohort>

= Selected low-versus-high BDI rows

#figure(
  kind: table,
  table(
    columns: (1.4fr, 1.75fr, 1.45fr, 0.9fr, 0.9fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Block*], [*Analysis type*], [*Metric*], [*Low mean*], [*High mean*], [*`d`*], [*`q`*]),
    [`Global 3D MNPS`], [`global_mnps_3d`], [`d_median`], [`0.294`], [`0.326`], [`0.042`], [`0.860`],
    [`Global 9D MNPS`], [`global_mnps_9d`], [`d_s_mean`], [`1.305`], [`1.083`], [`-0.209`], [`0.377`],
    [`Global 3D MNJ`], [`global_mnps_jacobian_3d`], [`spectral_radius_median`], [`0.0617`], [`0.0620`], [`0.024`], [`1.00`],
    [`Global 9D MNJ`], [`global_mnps_jacobian_9d`], [`rotational_power_mean`], [`0.0360`], [`0.0398`], [`0.569`], [`0.00317`],
    [`9x9 block MNJ`], [`global_mnps_jacobian_9d_block_jacobian`], [`block_anisotropy_mean (m -> m)`], [`172.10`], [`94.48`], [`-0.203`], [`0.555`],
    [`Reachability cones`], [`reachability_cones`], [`tube_log_eig_var_mean`], [`11.95`], [`7.742`], [`-0.678`], [`0.00296`],
    [`Tier-2 EMMI`], [`tier2_emmi`], [`mv_median`], [`0.130`], [`-0.0906`], [`-0.370`], [`0.0510`],
    [`Distribution summary`], [`dist_summary`], [`e_m_mad_sigma`], [`0.170`], [`0.478`], [`0.688`], [`0.0132`],
  ),
  caption: [Selected low/high BDI block rows from `results/selected_metrics_summary.csv`.]
) <tab-s2-selected>

= Selected continuous-BDI rows

#figure(
  kind: table,
  table(
    columns: (1.4fr, 1.75fr, 1.45fr, 0.8fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Block*], [*Analysis type*], [*Metric*], [*N*], [*`rho`*], [*`q`*]),
    [`Global 3D MNPS`], [`global_mnps_3d`], [`d_median`], [`121`], [`-0.0735`], [`0.550`],
    [`Global 9D MNPS`], [`global_mnps_9d`], [`d_s_mean`], [`121`], [`-0.124`], [`0.394`],
    [`Global 3D MNJ`], [`global_mnps_jacobian_3d`], [`spectral_radius_median`], [`121`], [`-0.0871`], [`0.887`],
    [`Global 9D MNJ`], [`global_mnps_jacobian_9d`], [`rotational_power_mean`], [`121`], [`0.310`], [`0.00364`],
    [`9x9 block MNJ`], [`global_mnps_jacobian_9d_block_jacobian`], [`block_anisotropy_mean (d -> d)`], [`121`], [`0.00714`], [`0.938`],
    [`Reachability cones`], [`reachability_cones`], [`tube_log_eig_var_mean`], [`121`], [`-0.343`], [`0.00350`],
    [`Tier-2 EMMI`], [`tier2_emmi`], [`mv_median`], [`121`], [`-0.112`], [`0.518`],
    [`Distribution summary`], [`dist_summary`], [`e_m_mad_sigma`], [`121`], [`0.358`], [`0.00226`],
  ),
  caption: [Selected continuous-BDI rows (`All_valid`) from `results/bdi_correlations_summary.csv`.]
) <tab-s2-bdi-rho>

= Clinical BDI-band contrasts

#figure(
  kind: table,
  table(
    columns: (1.55fr, 1.4fr, 1.35fr, 0.85fr, 0.85fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Split*], [*Block*], [*Metric*], [*Left mean*], [*Right mean*], [*`d`*], [*`q`*]),
    [`0-13 vs 14-19`], [`Reachability cones`], [`tube_log_eig_var_mean`], [`11.95`], [`6.752`], [`-0.831`], [`7.46e-6`],
    [`0-13 vs 14-19`], [`Distribution summary`], [`e_m_mad_sigma`], [`0.170`], [`0.962`], [`1.727`], [`5.01e-4`],
    [`0-13 vs 20-63`], [`Global 9D MNJ`], [`rotational_power_mean`], [`0.0360`], [`0.0398`], [`0.569`], [`9.30e-4`],
    [`0-13 vs 20-63`], [`Reachability cones`], [`tube_log_eig_var_mean`], [`11.95`], [`7.742`], [`-0.678`], [`2.67e-5`],
    [`0-13 vs 20-63`], [`Distribution summary`], [`e_m_mad_sigma`], [`0.170`], [`0.478`], [`0.688`], [`0.00957`],
    [`14-19 vs 20-63`], [`Distribution summary`], [`e_m_mad_sigma`], [`0.962`], [`0.478`], [`-0.643`], [`0.236`],
    [`14-19 vs 20-63`], [`Reachability cones`], [`tube_log_eig_var_mean`], [`6.752`], [`7.742`], [`0.203`], [`0.765`],
  ),
  caption: [Selected clinical-band contrasts from `results/clinical_bdi_bin_summary.csv`.]
) <tab-s2-bins>

= Baseline centroid rows

#figure(
  kind: table,
  table(
    columns: (0.8fr, 1.35fr, 0.85fr, 0.85fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Layer*], [*Metric*], [*Low mean*], [*High mean*], [*`d`*], [*`q`*]),
    [`3D`], [`e_median`], [`0.159`], [`0.379`], [`0.386`], [`0.386`],
    [`3D`], [`e_mean`], [`0.0776`], [`0.258`], [`0.297`], [`0.386`],
    [`3D`], [`m_mean`], [`0.0665`], [`0.286`], [`0.259`], [`0.386`],
    [`9D`], [`e_m_mean`], [`-0.139`], [`0.288`], [`0.688`], [`0.0239`],
    [`9D`], [`e_m_median`], [`-0.179`], [`0.216`], [`0.589`], [`0.0546`],
    [`9D`], [`m_o_median`], [`0.0221`], [`0.558`], [`0.537`], [`0.0637`],
    [`9D`], [`m_o_mean`], [`0.280`], [`0.794`], [`0.523`], [`0.0637`],
  ),
  caption: [Top baseline centroid rows from `results/centroid_baseline_summary.csv`.]
) <tab-s2-centroids>

= Centroid-adjusted dynamic rows

#figure(
  kind: table,
  table(
    columns: (1.55fr, 1.3fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Block*], [*Metric*], [*Raw `d`*], [*Adj. beta*], [*Adj. `q`*], [*Residual `d`*]),
    [`Block MNJ m->m`], [`block_frobenius_mean`], [`-0.517`], [`-0.0243`], [`0.0509`], [`-0.474`],
    [`Distribution summary`], [`e_m_mad_sigma`], [`0.984`], [`0.179`], [`0.0825`], [`0.577`],
    [`Block MNJ m->d`], [`block_frobenius_mean`], [`-0.516`], [`-0.0212`], [`0.123`], [`-0.330`],
    [`Global 9D MNJ`], [`rotational_power_mean`], [`0.767`], [`0.00175`], [`0.153`], [`0.375`],
    [`Tier-2 EMMI`], [`mv_median`], [`-0.453`], [`-0.165`], [`0.153`], [`-0.378`],
    [`Reachability cones`], [`tube_log_eig_var_mean`], [`-0.816`], [`-1.176`], [`0.195`], [`-0.305`],
  ),
  caption: [Centroid-adjusted sensitivity rows from `results/centroid_adjusted_dynamic_summary.csv`.]
) <tab-s2-centroid-adjusted>

= Metric-family sidecars

The selected block tables above intentionally compress the larger export surface. The strongest metric-family rows across the wider low/high inventory are summarized below.

#figure(
  kind: table,
  table(
    columns: (1.55fr, 1.0fr, 1.55fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Analysis family*], [*Metric family*], [*Metric*], [*`d`*], [*`q`*]),
    [`Global 9D MNPS`], [`location`], [`e_m_mean`], [`0.566`], [`0.00900`],
    [`Global 9D MNPS`], [`spread`], [`m_o_std`], [`0.528`], [`0.00900`],
    [`Global 9D MNJ`], [`jacobian`], [`jacobian_near_singular_rate`], [`-0.686`], [`0.00317`],
    [`Reachability cones`], [`reachability`], [`tube_log_det_mean`], [`0.735`], [`0.00296`],
    [`Tier-2 EMMI`], [`trajectory`], [`mv_over_speed_median`], [`-0.403`], [`0.04498`],
    [`Distribution summary`], [`shape`], [`e_m_skewness`], [`-0.538`], [`0.0188`],
  ),
  caption: [Representative metric-family sidecars from `results/metric_family_summary.csv`.]
) <tab-s2-families>

= Supplementary violin displays

#figure(
  image("figures/supp_violin_selected_blocks.png", width: 100%),
  caption: [Supplementary violin plot for the eight selected resting-state blocks by BDI band.]
) <fig-s2-selected-violins>

#figure(
  image("figures/supp_violin_centroid_baseline.png", width: 100%),
  caption: [Supplementary violin plot for the strongest baseline centroid coordinates by BDI band.]
) <fig-s2-centroid-violins>

= Files

This supplement is backed mainly by:

- `results/selected_metrics_summary.csv`
- `results/bdi_correlations_summary.csv`
- `results/clinical_bdi_bin_summary.csv`
- `results/centroid_baseline_summary.csv`
- `results/centroid_adjusted_dynamic_summary.csv`
- `results/metric_family_summary.csv`
