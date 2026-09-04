#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "Parkinson Supplementary Data",
  subtitle: "Primary mixed-contract tables, focal effects, and retained inventories",
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

`S2` collects the article-facing retained inventories for the dual-dataset manuscript.

The full stamped inventories remain in the result directories:

- `articles/CLINICAL/parkinson_cognitive_workload_ON_OFF/results/parkinson_simon_conflict_20260608`
- `articles/CLINICAL/parkinson_cognitive_workload_ON_OFF/results/parkinson_reinforcement_learning_20260608`

This supplement provides the compact manuscript-facing subset. The cross-task logic is intentionally asymmetric: Simon conflict is included as the stronger positive assay, while reinforcement learning is included to show how recoverability narrows under a different task context.

= Retained counts

#figure(
  kind: table,
  table(
    columns: (1.35fr, 1.0fr, 0.9fr, 1.0fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*Dataset*], [*`q < 0.05` standard*], [*`q < 0.05` event*], [*`q < 0.1` standard*], [*`q < 0.1` event*]),
    [`ds003509`], [`56`], [`0`], [`108`], [`0`],
    [`ds003506`], [`11`], [`0`], [`31`], [`0`],
  ),
  caption: [Primary retained-row counts by dataset, threshold, and layer.]
) <tab-s2-counts>

== Simon conflict (`ds003509`)

The Simon conflict dataset retained broad disease-state structure in the standard layer and no corrected event-wrapper rows.

#figure(
  kind: table,
  table(
    columns: (1.2fr, 1.8fr, 1.15fr, 0.9fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Row*], [*Metric*], [*`d`*], [*`q`*]),
    [`Control vs Parkinson OFF`], [`regional_9d / parietal_occipital`], [`d_s_mean`], [`1.166`], [`0.018`],
    [`Control vs Parkinson OFF`], [`regional_9d / parietal_occipital`], [`d_n_std`], [`-1.155`], [`0.018`],
    [`Control vs Parkinson OFF`], [`regional_9d / central`], [`d_n_std`], [`-1.129`], [`0.018`],
    [`Control vs Parkinson ON`], [`global_mnps_9d`], [`e_m_median`], [`-0.985`], [`0.027`],
    [`Control vs Parkinson ON`], [`regional_9d / frontal`], [`e_m_mean`], [`-0.991`], [`0.013`],
    [`Control vs Parkinson ON`], [`regional_9d / parietal_occipital`], [`d_s_mean`], [`0.982`], [`0.013`],
    [`Parkinson OFF vs ON`], [`global_mnps_3d`], [`m_median`], [`0.515`], [`0.090`],
  ),
  caption: [Focal Simon conflict standard-layer rows. The paired medication row is shown because it enters at `q < 0.1`, even though no paired row survives `q < 0.05`.]
) <tab-s2-simon>

At the primary thresholds, `ds003509` retained:

- `32` standard rows for `Control vs Parkinson OFF` at `q < 0.05`,
- `24` standard rows for `Control vs Parkinson ON` at `q < 0.05`,
- `4` standard rows for `Parkinson OFF vs ON` at `q < 0.1`,
- and `0` event-wrapper rows at `q < 0.1`.

The Simon conflict standard layer also carried a nontrivial collapse/Jacobian and reachability branch, especially in `Control vs Parkinson ON`.

#figure(
  kind: table,
  table(
    columns: (1.55fr, 0.9fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*Simon family*], [*`q < 0.05`*], [*`q < 0.1`*]),
    [`Jacobian / block-Jacobian / collapse`], [`2`], [`6`],
    [`Reachability / cone persistence`], [`2`], [`32`],
  ),
  caption: [Retained Simon conflict Jacobian-like and reachability-like standard rows. Reachability was concentrated in the `Control vs Parkinson ON` branch.]
) <tab-s2-simon-family-counts>

#figure(
  kind: table,
  table(
    columns: (1.2fr, 1.65fr, 1.2fr, 0.9fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Row*], [*Metric*], [*`d`*], [*`q`*]),
    [`Control vs Parkinson ON`], [`adaptive_collapse`], [`q_ratio_h4`], [`-0.632`], [`0.034`],
    [`Control vs Parkinson ON`], [`adaptive_collapse`], [`capture_gate`], [`0.616`], [`0.034`],
    [`Control vs Parkinson ON`], [`global_mnps_9d_block_jacobian / central`], [`block_anisotropy_mean`], [`0.414`], [`0.072`],
    [`Parkinson OFF vs ON`], [`adaptive_collapse`], [`q_ratio_h4`], [`-0.369`], [`0.083`],
    [`Parkinson OFF vs ON`], [`adaptive_collapse`], [`capture_gate`], [`0.354`], [`0.083`],
    [`Parkinson OFF vs ON`], [`adaptive_collapse`], [`a_operator_norm`], [`0.335`], [`0.083`],
  ),
  caption: [Focal Simon conflict collapse and block-Jacobian rows. These rows extend the main standard-layer table and show that the Simon `ON` branch carries more than simple `9D` centroid separation, while the paired branch enters only at the broader `q < 0.1` layer.]
) <tab-s2-simon-jacobian>

#figure(
  kind: table,
  table(
    columns: (1.2fr, 1.55fr, 1.35fr, 0.9fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Family*], [*Metric*], [*`d`*], [*`q`*]),
    [`Control vs Parkinson ON`], [`reachability_cones`], [`persistence_log_eig_var_median`], [`-0.919`], [`0.040`],
    [`Control vs Parkinson ON`], [`reachability_cones`], [`persistence_kappa_median`], [`-0.888`], [`0.040`],
    [`Control vs Parkinson ON`], [`reachability_cones`], [`median_min_eig_over_median_eig`], [`0.800`], [`0.066`],
    [`Control vs Parkinson ON`], [`reachability_cones`], [`tube_dir_entropy_mean`], [`-0.789`], [`0.066`],
    [`Control vs Parkinson ON`], [`reachability_cones`], [`persistence_hysteresis_d_eff_median`], [`0.704`], [`0.066`],
    [`Control vs Parkinson ON`], [`reachability_cones`], [`tube_capture_gate_mean`], [`0.659`], [`0.066`],
  ),
  caption: [Representative Simon conflict reachability rows. Many additional reachability metrics cluster at the same q-level in the full CSV, so this table shows the most interpretable representatives rather than the complete list.]
) <tab-s2-simon-reachability>

== Reinforcement learning (`ds003506`)

The reinforcement-learning dataset retained a narrower standard-layer inventory and again no corrected event-wrapper rows. In the article logic, this dataset functions less as a second positive replication surface and more as the boundary condition showing where recoverable disease-state geometry becomes thinner and more classically shareable.

#figure(
  kind: table,
  table(
    columns: (1.2fr, 1.8fr, 1.15fr, 0.9fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Row*], [*Metric*], [*`d`*], [*`q`*]),
    [`Control vs Parkinson OFF`], [`classical_eeg / global`], [`relative_alpha_mean`], [`1.113`], [`0.024`],
    [`Control vs Parkinson OFF`], [`classical_eeg / global`], [`relative_alpha_iqr`], [`0.956`], [`0.024`],
    [`Control vs Parkinson OFF`], [`global_mnps_jacobian_9d / global`], [`mdr_mean`], [`0.835`], [`0.033`],
    [`Control vs Parkinson OFF`], [`global_mnps_jacobian_9d / global`], [`rotational_power_mean`], [`0.658`], [`0.033`],
    [`Control vs Parkinson ON`], [`global_mnps_jacobian_9d / global`], [`aci_mean`], [`0.835`], [`0.047`],
    [`Control vs Parkinson OFF`], [`regional_9d / frontal`], [`d_s_mean`], [`1.064`], [`0.054`],
  ),
  caption: [Focal reinforcement-learning standard-layer rows. No paired `Parkinson OFF vs ON` row survives `q < 0.1` in this dataset. Compared with the earlier result pass, the strongest RL `ON` row is now `global_mnps_jacobian_9d / aci_mean` rather than a lone block-Jacobian residual.]
) <tab-s2-rl>

At the primary thresholds, `ds003506` retained:

- `10` standard rows for `Control vs Parkinson OFF` at `q < 0.05`,
- `1` standard row for `Control vs Parkinson ON` at `q < 0.05`, and `3` such rows at `q < 0.1`,
- `0` standard rows for `Parkinson OFF vs ON` at `q < 0.1`,
- and `0` event-wrapper rows at `q < 0.1`.

The reinforcement-learning dataset carried a much thinner Jacobian branch and no retained reachability branch.

#figure(
  kind: table,
  table(
    columns: (1.55fr, 0.9fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*RL family*], [*`q < 0.05`*], [*`q < 0.1`*]),
    [`Jacobian / block-Jacobian / collapse`], [`3`], [`10`],
    [`Reachability / cone persistence`], [`0`], [`0`],
  ),
  caption: [Retained reinforcement-learning Jacobian-like and reachability-like standard rows.]
) <tab-s2-rl-family-counts>

#figure(
  kind: table,
  table(
    columns: (1.2fr, 1.65fr, 1.2fr, 0.9fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Row*], [*Metric*], [*`d`*], [*`q`*]),
    [`Control vs Parkinson OFF`], [`global_mnps_jacobian_9d / global`], [`mdr_mean`], [`0.835`], [`0.033`],
    [`Control vs Parkinson OFF`], [`global_mnps_jacobian_9d / global`], [`rotational_power_mean`], [`0.658`], [`0.033`],
    [`Control vs Parkinson ON`], [`global_mnps_jacobian_9d / global`], [`aci_mean`], [`0.835`], [`0.047`],
    [`Control vs Parkinson OFF`], [`tier2_jacobian`], [`rotation_coherence_mean_axis_2`], [`-0.853`], [`0.055`],
    [`Control vs Parkinson ON`], [`global_mnps_jacobian_9d / global`], [`aci_median`], [`0.744`], [`0.071`],
    [`Control vs Parkinson ON`], [`global_mnps_9d_block_jacobian / central`], [`block_frobenius_mean`], [`-0.714`], [`0.090`],
  ),
  caption: [Retained reinforcement-learning Jacobian rows at `q < 0.1`. Unlike Simon conflict, this task still does not produce a broad retained reachability inventory, but the Jacobian branch is broader than in the earlier result pass and now includes a small `Control vs Parkinson ON` remainder.]
) <tab-s2-rl-jacobian>

No reinforcement-learning reachability row survived `q < 0.1` in the primary standard inventory.

== Cross-task synthesis

The cross-task comparison is intentionally narrow and asks how much disease-state geometry remains recoverable in each task context under the same mixed-contract policy.

#figure(
  kind: table,
  table(
    columns: (1.35fr, 1.55fr, 2.0fr),
    align: left,
    inset: 4pt,
    table.header([*Comparison*], [*Simon conflict*], [*Reinforcement learning*]),
    [`Disease-state inventory`], [`Broad for `OFF` and `ON` versus controls in the standard layer`], [`Strong for `OFF`, small Jacobian remainder for `ON`, much thinner overall`],
    [`Paired medication`], [`Only enters at `q < 0.1` in the standard layer`], [`Absent at `q < 0.1``],
    [`Event wrapper`], [`No retained row at `q < 0.1``], [`No retained row at `q < 0.1``],
    [`Dominant signal family`], [`Regional/global `9D` geometry plus collapse/reachability tail`], [`Mixed classical alpha and Jacobian geometry`],
  ),
  caption: [Conservative recoverability synthesis restricted to families that remain interpretable in both tasks. Reinforcement learning is included to bound the generality of the Simon conflict result, not to force a symmetric dual-positive story.]
) <tab-s2-cross>
