#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "Trajectory Psychosis Supplementary Data",
  subtitle: "Full contrast tables, group compositions, and supportive metric summaries",
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

This supplement collects the data-heavy material moved out of the main manuscript:

- group compositions and data coverage,
- full 3D contrast tables for both datasets,
- full 9D contrast tables for both datasets,
- directional summary of jerk-related metrics,
- and cross-dataset pattern comparison.

= Group composition and data coverage

#figure(
  kind: table,
  table(
    columns: (1.1fr, 1.35fr, 0.65fr, 0.9fr, 0.9fr, 1.0fr, 0.9fr),
    align: left,
    inset: 5pt,
    table.header(
      [*Dataset*],
      [*Group*],
      [*N*],
      [*Age mean*],
      [*Age SD*],
      [*Female n (%)*],
      [*CPZ median*],
    ),
    [ds003944], [Healthy], [32], [21.61], [3.97], [12 (37.5%)], [--],
    [ds003944], [FEP unmedicated], [19], [22.33], [4.21], [5 (26.3%)], [`0 / n.a.`],
    [ds003944], [FEP medicated], [31], [22.34], [5.41], [11 (35.5%)], [`227.3`],
    [ds003947], [Healthy], [30], [24.20], [5.13], [14 (46.7%)], [--],
    [ds003947], [FEP unmedicated], [8], [25.01], [5.06], [2 (25.0%)], [`0 / n.a.`],
    [ds003947], [FEP medicated], [23], [22.82], [4.57], [7 (30.4%)], [`303.0`],
  ),
  caption: [Group composition. Identical to companion static-geometry study; medication groups use the same `CPZ_at_scan` split.]
) <tab-s2-groups>

Each subject has approximately 75 analysis windows at 4-second intervals, yielding approximately 74 interior windows for noetic action computation and approximately 74 transitions for repertoire metrics. All 82 `ds003944` subjects and 61 `ds003947` subjects passed the minimum-window filter ($geq 16$ valid windows) and contributed to the codebook fitting and metric computation.

= Full 3D contrast table: ds003944

#figure(
  kind: table,
  table(
    columns: (1.5fr, 1.5fr, 0.6fr, 0.6fr, 0.6fr, 0.45fr, 0.45fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Contrast*],
      [*Metric*],
      [*$d$*],
      [*$p$*],
      [*$q$*],
      [*$n_a$*],
      [*$n_b$*],
      [*AF*],
    ),
    [FEP unmedicated vs Healthy], [`noetic_action`], [+0.774], [0.0062], [0.0524], [19], [32], [yes],
    [FEP unmedicated vs Healthy], [`noetic_action_potential`], [+0.728], [0.0116], [0.0524], [19], [32], [no],
    [FEP unmedicated vs Healthy], [`irreversibility`], [+0.382], [0.3349], [0.7534], [19], [32], [yes],
    [FEP unmedicated vs Healthy], [`entropy_rate`], [+0.231], [--], [--], [19], [32], [yes],
    [FEP unmedicated vs Healthy], [`transition_sparsity`], [-0.350], [0.3279], [0.7534], [19], [32], [no],
    [FEP unmedicated vs Healthy], [`entropy_production`], [+0.275], [0.4416], [0.7597], [19], [32], [no],
    [FEP unmedicated vs Healthy], [`self_loop_rate`], [+0.268], [--], [--], [19], [32], [no],
    [FEP unmedicated vs Healthy], [`noetic_action_kinetic`], [-0.300], [--], [--], [19], [32], [no],
    [FEP unmedicated vs Healthy], [`noetic_action_jerk`], [+0.108], [--], [--], [19], [32], [no],
    [],[], [], [], [], [], [], [],
    [FEP medicated vs Healthy], [`noetic_action`], [+0.362], [0.1757], [0.5520], [31], [32], [yes],
    [FEP medicated vs Healthy], [`noetic_action_potential`], [+0.319], [0.1469], [0.5520], [31], [32], [no],
    [FEP medicated vs Healthy], [`self_loop_rate`], [--], [--], [--], [31], [32], [no],
    [FEP medicated vs Healthy], [`noetic_action_kinetic`], [-0.351], [0.1939], [0.5520], [31], [32], [no],
    [FEP medicated vs Healthy], [`irreversibility`], [-0.176], [--], [--], [31], [32], [yes],
    [FEP medicated vs Healthy], [`entropy_rate`], [-0.096], [--], [--], [31], [32], [yes],
    [],[], [], [], [], [], [], [],
    [FEP medicated vs FEP unmedicated], [`irreversibility`], [-0.499], [0.2504], [0.4508], [31], [19], [yes],
    [FEP medicated vs FEP unmedicated], [`transition_sparsity`], [+0.480], [0.1481], [0.4060], [31], [19], [no],
    [FEP medicated vs FEP unmedicated], [`self_loop_rate`], [+0.403], [0.1805], [0.4060], [31], [19], [no],
    [FEP medicated vs FEP unmedicated], [`noetic_action`], [-0.362], [0.1288], [0.4060], [31], [19], [yes],
    [FEP medicated vs FEP unmedicated], [`noetic_action_potential`], [-0.362], [0.0932], [0.4060], [31], [19], [no],
    [FEP medicated vs FEP unmedicated], [`noetic_action_jerk`], [-0.351], [0.3792], [0.5488], [31], [19], [no],
    [FEP medicated vs FEP unmedicated], [`noetic_action_kinetic`], [-0.320], [0.3684], [0.6632], [31], [19], [no],
  ),
  caption: [Full 3D trajectory contrast table for `ds003944`. AF = article-facing metric. All $q$ values apply BH-FDR within {contrast, analysis type}. Blank cells indicate that the specific value was not in the printed contrast output and should be read from `ds003944_trajectory_contrasts.csv`.]
) <tab-s2-44-3d>

= Full 9D contrast table: ds003944

#figure(
  kind: table,
  table(
    columns: (1.5fr, 1.5fr, 0.6fr, 0.6fr, 0.6fr, 0.45fr, 0.45fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Contrast*],
      [*Metric*],
      [*$d$*],
      [*$p$*],
      [*$q$*],
      [*$n_a$*],
      [*$n_b$*],
      [*AF*],
    ),
    [FEP unmedicated vs Healthy], [`noetic_action`], [+0.441], [0.0958], [0.6847], [19], [32], [yes],
    [FEP unmedicated vs Healthy], [`noetic_action_potential`], [+0.421], [0.1522], [0.6847], [19], [32], [no],
    [FEP unmedicated vs Healthy], [`irreversibility`], [+0.196], [--], [--], [19], [32], [yes],
    [FEP unmedicated vs Healthy], [`transition_sparsity`], [+0.304], [0.4280], [0.9767], [19], [32], [no],
    [FEP medicated vs Healthy], [`self_loop_rate`], [+0.381], [0.0976], [0.8620], [31], [32], [no],
    [FEP medicated vs Healthy], [`noetic_action_kinetic`], [-0.349], [0.4292], [0.8620], [31], [32], [no],
    [FEP medicated vs FEP unmedicated], [`noetic_action_kinetic`], [-0.320], [0.3684], [0.6632], [31], [19], [no],
    [FEP medicated vs FEP unmedicated], [`noetic_action_jerk`], [-0.273], [0.6457], [0.8302], [31], [19], [no],
  ),
  caption: [Selected 9D trajectory effects for `ds003944`. Directional consistency with 3D is preserved for the primary contrasts. Full table in `ds003944_trajectory_contrasts.csv`.]
) <tab-s2-44-9d>

= Full 3D contrast table: ds003947

#figure(
  kind: table,
  table(
    columns: (1.5fr, 1.5fr, 0.6fr, 0.6fr, 0.6fr, 0.45fr, 0.45fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Contrast*],
      [*Metric*],
      [*$d$*],
      [*$p$*],
      [*$q$*],
      [*$n_a$*],
      [*$n_b$*],
      [*AF*],
    ),
    [FEP medicated vs FEP unmedicated], [`entropy_rate`], [-0.769], [0.0822], [0.7106], [23], [8], [yes],
    [FEP medicated vs FEP unmedicated], [`transition_sparsity`], [+0.641], [0.2211], [0.7106], [23], [8], [no],
    [FEP medicated vs FEP unmedicated], [`self_loop_rate`], [+0.462], [0.2369], [0.7106], [23], [8], [no],
    [FEP medicated vs FEP unmedicated], [`irreversibility`], [-0.230], [0.4295], [0.8354], [23], [8], [yes],
    [],[], [], [], [], [], [], [],
    [FEP unmedicated vs Healthy], [`entropy_rate`], [+0.591], [0.3316], [0.5968], [8], [30], [yes],
    [FEP unmedicated vs Healthy], [`irreversibility`], [+0.292], [0.2808], [0.5968], [8], [30], [yes],
    [FEP unmedicated vs Healthy], [`entropy_production`], [+0.325], [0.2651], [0.5968], [8], [30], [no],
    [FEP unmedicated vs Healthy], [`transition_sparsity`], [-0.643], [0.1557], [0.5968], [8], [30], [no],
    [FEP unmedicated vs Healthy], [`noetic_action`], [-0.298], [0.5858], [0.7532], [8], [30], [yes],
    [],[], [], [], [], [], [], [],
    [FEP medicated vs Healthy], [`noetic_action_potential`], [-0.377], [0.1994], [0.9071], [23], [30], [no],
    [FEP medicated vs Healthy], [`noetic_action`], [-0.250], [0.4040], [0.9071], [23], [30], [yes],
    [FEP medicated vs Healthy], [`irreversibility`], [-0.218], [0.7196], [0.9214], [23], [30], [yes],
  ),
  caption: [Full 3D trajectory contrast table for `ds003947`. Power is limited by $n = 8$ unmedicated FEP subjects; no contrast reached BH-FDR correction. The entropy rate trend (medicated vs unmedicated) is the clearest directional signal.]
) <tab-s2-47-3d>

= Jerk-specific summary across datasets

The `noetic_action_jerk` component was predicted to be specifically sensitive to aberrant-salience-like abrupt state-space redirections. The table below summarises the directional pattern across all contrasts and both datasets.

#figure(
  kind: table,
  table(
    columns: (1.0fr, 1.5fr, 0.65fr, 0.65fr, 0.9fr),
    align: left,
    inset: 5pt,
    table.header(
      [*Dataset*],
      [*Contrast*],
      [*$d$ (3D)*],
      [*$p$ (3D)*],
      [*Direction*],
    ),
    [ds003944], [FEP unmedicated vs Healthy], [+0.108], [--], [unmedicated slightly higher],
    [ds003944], [FEP medicated vs Healthy], [-0.206], [0.606], [medicated slightly lower],
    [ds003944], [FEP medicated vs FEP unmedicated], [-0.351], [0.379], [medicated lower than unmedicated],
    [ds003947], [FEP unmedicated vs Healthy], [+0.231], [0.712], [unmedicated slightly higher],
    [ds003947], [FEP medicated vs Healthy], [+0.170], [0.713], [medicated slightly higher],
    [ds003947], [FEP medicated vs FEP unmedicated], [-0.192], [--], [medicated lower],
  ),
  caption: [Jerk component summary. The direction is consistently such that medicated FEP has lower `noetic_action_jerk` than unmedicated FEP in both datasets, but no comparison approaches significance. Unmedicated FEP is directionally higher than healthy in both datasets. These patterns are hypothesis-generating only.]
) <tab-s2-jerk>

= Cross-dataset directional comparison

#figure(
  kind: table,
  table(
    columns: (1.4fr, 1.0fr, 0.8fr, 0.8fr, 1.5fr),
    align: left,
    inset: 5pt,
    table.header(
      [*Metric*],
      [*ds003944 FEP-unmed vs HC*],
      [*ds003947 FEP-unmed vs HC*],
      [*Consistent?*],
      [*Comment*],
    ),
    [`noetic_action`], [$d = +0.774$], [$d = -0.298$], [No], [Strong ds003944 signal; ds003947 reversed, ns],
    [`entropy_rate`], [$d = +0.231$], [$d = +0.591$], [Yes], [Both positive; ds003947 slightly larger],
    [`irreversibility`], [$d = +0.382$], [$d = +0.292$], [Yes], [Both positive, both ns],
    [`noetic_action_jerk`], [$d = +0.108$], [$d = +0.231$], [Yes], [Both small positive, ns],
  ),
  caption: [Cross-dataset directional consistency for FEP unmedicated vs Healthy. The entropy rate and irreversibility metrics are consistent in direction; noetic action is not, potentially reflecting codebook differences, small sample in ds003947 ($n=8$), or genuine cohort differences. Cross-dataset replication of noetic action requires a future larger-sample analysis.]
) <tab-s2-cross>

= Files

The tables in this supplement are backed by the article-local outputs under `articles/CLINICAL/psychosis_first_time_geometric_trajectory/results/trajectory_geometry_20260607_full/`:

- `ds003944/ds003944_subject_trajectory_metrics.csv` — per-subject per-metric values
- `ds003944/ds003944_trajectory_contrasts.csv` — full contrast table
- `ds003947/ds003947_subject_trajectory_metrics.csv`
- `ds003947/ds003947_trajectory_contrasts.csv`
- `manifest.json` — run metadata and codebook summary

#bibliography("psychosis.bib", style: "apa")
