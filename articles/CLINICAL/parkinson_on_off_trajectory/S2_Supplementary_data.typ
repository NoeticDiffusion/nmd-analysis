#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data - Disease-State and Paired Pharmacology Geometry in Parkinson ON/OFF Auditory Oddball EEG",
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

This supplement collects the data-heavy tables moved out of the main article:

- the seven focal rows used in the main text,
- the mixed-contract centroid differences,
- a compact focal `NMD` versus classical EEG sidecar sensitivity summary,
- retained row counts by contrast and layer,
- top disease-state standard rows,
- top disease-state event-locked rows,
- the best paired pharmacology / ESB rows,
- and three additional regional inventory tables: regional MNPS position / coordinate summaries, regional Jacobian (`MNJ`) summaries, and regional reachability cones.

`S2` is an audit inventory rather than the inferential headline. The broader `q < 0.1` rows are retained here for transparency and hypothesis generation, while the main-text claim surface is restricted to the stricter `q < 0.05` layer.

= Seven focal rows

#figure(
  kind: table,
  table(
    columns: (1.6fr, 1.0fr, 1.6fr, 1.45fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Contract*], [*Layer*], [*Row*], [*Left med*], [*Right med*], [*`d`*], [*`q`*]),
    [`Control vs OFF`], [`cohort`], [`regional 9D`], [`frontal d_n_std`], [`0.852`], [`0.530`], [`-1.268`], [`0.018`],
    [`Control vs OFF`], [`cohort`], [`global MNPS 9D`], [`global d_n_std`], [`0.912`], [`0.505`], [`-1.194`], [`0.013`],
    [`Control vs OFF`], [`cohort`], [`global event 3D`], [`eyes_closed speed_median`], [`0.105`], [`0.078`], [`-1.212`], [`0.0025`],
    [`Control vs OFF`], [`cohort`], [`global event 9D`], [`eyes_closed noetic_action_kinetic`], [`0.0328`], [`0.0164`], [`-1.085`], [`0.0050`],
    [`Control vs ON`], [`cohort`], [`global Jacobian 9D`], [`mdr_median`], [`0.115`], [`0.134`], [`1.167`], [`0.0095`],
    [`Control vs ON`], [`cohort`], [`global event 3D`], [`novel_tone hysteresis_area_me`], [`0.0890`], [`0.0484`], [`-1.039`], [`0.0269`],
    [`OFF vs ON`], [`subject`], [`regional Jacobian 3D`], [`temporal anisotropy_abs_eig_mean`], [`0.0311`], [`0.0232`], [-0.483#super[z]], [`0.038`],
  ),
  caption: [The seven focal rows emphasized in the main article. The `d` column reports Cohen's `d` for unpaired rows and Cohen's `d_z` (marked `z`) for the paired `OFF vs ON` row.]
) <tab-s2-seven>

= Mixed-contract centroid differences

To make the first-order location shifts explicit, the table below reports pairwise centroid distances using the same contract logic as the main article: `cohort_anchored` for the disease-state contrasts against controls and `subject_anchored` for the paired `OFF vs ON` contrast.

#figure(
  kind: table,
  table(
    columns: (1.8fr, 1.0fr, 1.0fr, 1.0fr, 1.0fr, 1.0fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Primary contract*], [*3D centroid distance*], [*9D centroid distance*], [*3D distance / dispersion*], [*9D distance / dispersion*]),
    [`Control vs Parkinson OFF`], [`cohort`], [`0.3755`], [`1.1933`], [`0.3836`], [`0.4894`],
    [`Control vs Parkinson ON`], [`cohort`], [`0.2226`], [`0.9872`], [`0.2136`], [`0.3876`],
    [`Parkinson OFF vs ON`], [`subject`], [`0.0769`], [`0.1751`], [`0.4957`], [`0.5734`],
  ),
  caption: [Pairwise centroid-distance summary under the mixed-contract reporting rule, together with the corresponding distance-to-dispersion ratios. The between-subject disease-state centroid separation is larger in raw distance under the cohort-anchor frame, whereas the paired subject-anchor pharmacology shift is smaller in absolute distance and should therefore not be over-read as a competing headline signal.]
) <tab-s2-centroids>

= Retained counts

#figure(
  kind: table,
  table(
    columns: (1.2fr, 0.95fr, 0.95fr, 0.95fr, 0.95fr),
    align: left,
    inset: 5pt,
    table.header([*Threshold*], [*Standard retained*], [*Event retained*], [*ESB retained*], [*Total retained*]),
    [`q < 0.05`], [`35`], [`12`], [`0`], [`47`],
    [`q < 0.1`], [`69`], [`18`], [`0`], [`87`],
  ),
  caption: [Merged primary retained counts at both reporting thresholds. The stricter `q < 0.05` layer defines the main-text claim surface, whereas the broader `q < 0.1` layer is retained in `S2` for transparency and follow-up work.]
) <tab-s2-counts>

= Focal `NMD` versus classical sidecars

The table below gives a compact reader-facing summary of the direct focal-row sensitivity analysis from `S3`. For the between-subject contrasts, the main quantity shown is the group-adjusted subject-level Spearman `rho` after simple within-stratum median-centering. For the paired `OFF vs ON` branch, the reported `rho` is the subject-level `ON - OFF` delta correlation.

#figure(
  kind: table,
  table(
    columns: (2.15fr, 1.75fr, 0.9fr, 1.55fr),
    align: left,
    inset: 4pt,
    table.header([*Focal `NMD` row*], [*Strongest classical sidecar*], [*`rho`*], [*Interpretation*]),
    [`frontal 9D d_n_std (Control vs OFF)`], [`permutation entropy median`], [`0.198`], [`contrast-aligned but not reducible in this check`],
    [`eyes_closed speed_median 3D (Control vs OFF)`], [`Hjorth complexity median`], [`0.408`], [`partial alignment, but not reducible in this check`],
    [`eyes_closed noetic_action_kinetic 9D (Control vs OFF)`], [`slowing-index ratio median`], [`0.220`], [`contrast-aligned but not reducible in this check`],
    [`global 9D mdr_median (Control vs ON)`], [`theta/alpha ratio median`], [`-0.334`], [`partial alignment, but not reducible in this check`],
    [`novel_tone hysteresis_area_me (Control vs ON)`], [`peak median frequency median`], [`-0.464`], [`partial alignment, but not reducible in this check`],
    [`standard_tone hysteresis_area_me (Control vs ON)`], [`peak median frequency median`], [`-0.461`], [`partial alignment, but not reducible in this check`],
    [`signed_divergence_balance_mean_neg (OFF vs ON)`], [`Hjorth mobility median`], [`0.295`], [`limited paired alignment`],
  ),
  caption: [Compact focal-row sensitivity summary against the classical EEG sidecars. The strongest associations are partial rather than near-one-to-one, which argues against reading the focal geometry rows as simple restatements of the classical panel in this processed bundle.]
) <tab-s2-focal-vs-classical>

= Top retained standard rows: Control vs Parkinson OFF

#figure(
  kind: table,
  table(
    columns: (1.55fr, 1.2fr, 1.5fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Analysis type*], [*Network*], [*Metric*], [*Control med*], [*PD OFF med*], [*`d`*], [*`q`*]),
    [`regional_9d`], [`frontal`], [`d_n_std`], [`0.852`], [`0.530`], [`-1.268`], [`0.013`],
    [`regional_9d`], [`parietal_occipital`], [`d_n_std`], [`0.597`], [`0.321`], [`-1.215`], [`0.013`],
    [`global_mnps_9d`], [`global`], [`d_n_std`], [`0.912`], [`0.505`], [`-1.194`], [`0.013`],
    [`regional_9d`], [`frontal`], [`m_e_std`], [`0.574`], [`0.376`], [`-1.189`], [`0.013`],
    [`regional_9d`], [`central`], [`d_n_std`], [`0.835`], [`0.484`], [`-0.973`], [`0.013`],
    [`regional_3d`], [`frontal`], [`m_std`], [`0.607`], [`0.395`], [`-1.090`], [`0.036`],
    [`global_mnps_9d`], [`global`], [`e_m_mean`†], [`0.277`], [`-0.368`], [`-0.865`], [`0.040`],
    [`global_mnps_9d`], [`global`], [`e_m_std`†], [`1.105`], [`0.881`], [`-0.826`], [`0.040`],
  ),
  caption: [Top retained cohort-anchor standard rows for `Control vs Parkinson OFF`. †Global coordinate; see note below.]
) <tab-s2-off-standard>

= Top retained standard rows: Control vs Parkinson ON

#figure(
  kind: table,
  table(
    columns: (1.55fr, 1.2fr, 1.5fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Analysis type*], [*Network*], [*Metric*], [*Control med*], [*PD ON med*], [*`d`*], [*`q`*]),
    [`global_mnps_jacobian_9d`], [`global`], [`mdr_median`], [`0.115`], [`0.134`], [`1.167`], [`0.0095`],
    [`regional_9d`], [`frontal`], [`m_e_std`], [`0.574`], [`0.449`], [`-1.132`], [`0.013`],
    [`global_mnps_9d`], [`global`], [`d_n_std`], [`0.912`], [`0.570`], [`-1.122`], [`0.013`],
    [`regional_9d`], [`frontal`], [`d_n_std`], [`0.852`], [`0.539`], [`-1.107`], [`0.013`],
    [`global_mnps_jacobian_9d`], [`global`], [`mdr_mean`], [`0.133`], [`0.154`], [`1.168`], [`0.014`],
    [`regional_9d`], [`parietal_occipital`], [`d_n_std`], [`0.597`], [`0.431`], [`-0.878`], [`0.018`],
    [`global_mnps_9d`], [`global`], [`e_m_mean`†], [`0.277`], [`-0.491`], [`-0.960`], [`0.022`],
    [`global_mnps_9d`], [`global`], [`e_e_std`], [`0.663`], [`0.432`], [`-0.873`], [`0.022`],
  ),
  caption: [Top retained cohort-anchor standard rows for `Control vs Parkinson ON`. †`e_m_mean` is a global coordinate: its value is identical across all regional networks by construction (see note below). The global `global_mnps_9d` row is the canonical representative; regional rows carrying the same value are not shown separately.]
) <tab-s2-on-standard>

== Note on `e_m`-family coordinates

The `e_m_mean`, `e_m_median`, and `e_m_std` metrics are computed from the global `e_m` subcoordinate of the stratified 9D chart. In the NeuralManifoldDynamics export used here, `e_m` is defined at the whole-brain level and is therefore identical for all regional network rows within the same run. As a result, frontal, temporal, central, and parietal-occipital regional rows for any `e_m`-family metric carry the same per-subject values and are not independent test units. In Tables @tab-s2-off-standard and @tab-s2-on-standard, only the global `global_mnps_9d` representative row is shown for each `e_m`-family metric. The full raw retained count of `35` standard rows at `q < 0.05` includes `12` regional `e_m`-family rows that are replications of `2` distinct global observations; the corresponding deduplicated distinct count is `23`.

= Top retained event rows: Control vs Parkinson OFF

#figure(
  kind: table,
  table(
    columns: (1.7fr, 1.05fr, 1.2fr, 1.55fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Analysis type*], [*Segment*], [*Network*], [*Metric*], [*Control med*], [*PD OFF med*], [*`d`*], [*`q`*]),
    [`global_event_locked_trajectory_3d`], [`eyes_closed`], [`global`], [`speed_median`], [`0.105`], [`0.078`], [`-1.212`], [`0.0025`],
    [`global_event_locked_trajectory_3d`], [`eyes_closed`], [`global`], [`noetic_action_kinetic`], [`0.00822`], [`0.00455`], [`-0.928`], [`0.0025`],
    [`global_event_locked_trajectory_3d`], [`eyes_closed`], [`global`], [`noetic_action_jerk`], [`0.00230`], [`0.00131`], [`-0.917`], [`0.0025`],
    [`global_event_locked_trajectory_3d`], [`eyes_closed`], [`global`], [`path_length`], [`8.232`], [`5.926`], [`-1.189`], [`0.0036`],
    [`global_event_locked_trajectory_9d`], [`eyes_closed`], [`global`], [`noetic_action_kinetic`], [`0.0328`], [`0.0164`], [`-1.085`], [`0.0050`],
    [`global_event_locked_trajectory_9d`], [`eyes_closed`], [`global`], [`speed_median`], [`0.342`], [`0.254`], [`-1.084`], [`0.0116`],
    [`global_event_locked_trajectory_9d`], [`eyes_closed`], [`global`], [`path_length`], [`25.155`], [`20.332`], [`-1.075`], [`0.0152`],
    [`regional_event_locked_trajectory_3d`], [`eyes_open`], [`frontal`], [`curvature_median`], [`2.700`], [`5.264`], [`1.012`], [`0.0370`],
  ),
  caption: [Top retained cohort-anchor event rows for `Control vs Parkinson OFF`. Note that the final row (`frontal / curvature_median / eyes_open`) has a positive direction (`d = 1.012`), opposite to all other focal disease-state rows. Its interpretation remains unresolved; see `S3` caution point 9.]
) <tab-s2-off-event>

= Top retained event rows: Control vs Parkinson ON

#figure(
  kind: table,
  table(
    columns: (1.7fr, 1.05fr, 1.2fr, 1.55fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Analysis type*], [*Segment*], [*Network*], [*Metric*], [*Control med*], [*PD ON med*], [*`d`*], [*`q`*]),
    [`global_event_locked_trajectory_3d`], [`novel_tone`], [`global`], [`hysteresis_area_me`], [`0.0890`], [`0.0484`], [`-1.039`], [`0.0269`],
    [`global_event_locked_trajectory_3d`], [`standard_tone`], [`global`], [`hysteresis_area_me`], [`0.0943`], [`0.0565`], [`-0.990`], [`0.0365`],
    [`global_event_locked_trajectory_3d`], [`eyes_closed`], [`global`], [`speed_median`], [`0.105`], [`0.0819`], [`-0.916`], [`0.0365`],
    [`global_event_locked_trajectory_3d`], [`eyes_closed`], [`global`], [`noetic_action_kinetic`], [`0.00822`], [`0.00530`], [`-0.756`], [`0.0539`],
    [`global_event_locked_trajectory_3d`], [`eyes_closed`], [`global`], [`noetic_action_jerk`], [`0.00230`], [`0.00132`], [`-0.714`], [`0.0539`],
    [`global_event_locked_trajectory_3d`], [`eyes_open`], [`global`], [`path_length`], [`8.351`], [`6.809`], [`-0.858`], [`0.0589`],
    [`global_event_locked_trajectory_3d`], [`target_tone`], [`global`], [`hysteresis_area_me`], [`0.0887`], [`0.0489`], [`-0.761`], [`0.0589`],
    [`global_event_locked_trajectory_3d`], [`eyes_closed`], [`global`], [`peak_displacement`], [`1.377`], [`1.076`], [`-0.815`], [`0.0939`],
  ),
  caption: [Top retained cohort-anchor event rows for `Control vs Parkinson ON`.]
) <tab-s2-on-event>

= Paired pharmacology and ESB

#figure(
  kind: table,
  table(
    columns: (1.65fr, 1.05fr, 1.15fr, 1.7fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Family*], [*Segment*], [*Network*], [*Metric*], [*OFF med*], [*ON med*], [*`d`*], [*`q`*]),
    [`standard retained`], [--], [`temporal`], [`anisotropy_abs_eig_mean`], [`0.0311`], [`0.0232`], [`-0.483`], [`0.038`],
    [`standard near-miss`], [--], [`global`], [`signed_divergence_balance_mean_neg`], [`-0.0440`], [`-0.0503`], [`-0.711`], [`0.066`],
    [`standard near-miss`], [--], [`frontal`], [`trace_median`], [`-0.0374`], [`0.0337`], [`0.650`], [`0.133`],
    [`event near-miss`], [`eyes_open`], [`central`], [`noetic_action_jerk (9D)`], [`0.0442`], [`0.0248`], [`-0.641`], [`0.226`],
    [`event near-miss`], [`eyes_open`], [`central`], [`path_length (9D)`], [`40.329`], [`33.455`], [`-0.714`], [`0.390`],
    [`ESB near-miss`], [`novel_tone`], [`frontal`], [`trajectory_esb2`], [`1.259`], [`0.782`], [`-0.498`], [`0.601`],
    [`ESB near-miss`], [`standard_tone`], [`temporal`], [`trajectory_esb2`], [`1.250`], [`0.931`], [`-0.384`], [`0.601`],
  ),
  caption: [The paired `OFF vs ON` story remains narrow. One standard row survives (`temporal anisotropy_abs_eig_mean`). The previously retained `signed_divergence_balance_mean_neg` is now a near-miss (`q = 0.066`) following correction of persistence-based metrics. Event and ESB rows remain non-retained.]
) <tab-s2-paired>

= Regional MNPS: position and coordinate summaries

The two regional position layers are `regional_mnps_3d` (run via `src/run_regional_mnps_contrasts.py` directly from the MNDM bundle CSV, no legacy adapter) and `regional_9d` (stratified `9D` subcoordinates from the NMD pipeline). The `regional_3d` layer (`m/d/e` mean/median/std only) is omitted here because all its retained rows appear in `regional_mnps_3d` with higher power. For `regional_9d`, `e_m`-family rows are not shown as independent entries; see the note in the top standard-row tables.

#figure(
  kind: table,
  table(
    columns: (1.5fr, 0.75fr, 1.1fr, 1.45fr, 0.85fr, 0.85fr, 0.7fr, 0.7fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Layer*], [*Network*], [*Metric*], [*Left med*], [*Right med*], [*`d`*], [*`q`*]),
    table.cell(colspan: 8, fill: rgb("#f0f0f0"))[_Control vs Parkinson OFF_],
    [`Control vs OFF`], [`mnps_3d`], [`frontal`], [`m_std`], [`0.607`], [`0.395`], [`-1.090`], [`0.020`],
    [`Control vs OFF`], [`9d`], [`frontal`], [`d_n_std`], [`0.852`], [`0.530`], [`-1.268`], [`0.018`],
    [`Control vs OFF`], [`9d`], [`parietal_occ`], [`d_n_std`], [`0.597`], [`0.321`], [`-1.215`], [`0.018`],
    [`Control vs OFF`], [`9d`], [`frontal`], [`m_e_std`], [`0.574`], [`0.376`], [`-1.189`], [`0.018`],
    [`Control vs OFF`], [`9d`], [`central`], [`d_n_std`], [`0.835`], [`0.484`], [`-0.973`], [`0.046`],
    [`Control vs OFF`], [`9d`], [`temporal`], [`d_n_std`], [`0.861`], [`0.517`], [`-0.928`], [`0.046`],
    table.cell(colspan: 8, fill: rgb("#f0f0f0"))[_Control vs Parkinson ON_],
    [`Control vs ON`], [`mnps_3d`], [`frontal`], [`strat9_condition_number`], [`19.34`], [`14.81`], [`-1.118`], [`0.012`],
    [`Control vs ON`], [`mnps_3d`], [`temporal`], [`trace_mean`], [`0.0733`], [`-0.0235`], [`-1.032`], [`0.012`],
    [`Control vs ON`], [`mnps_3d`], [`frontal`], [`m_std`], [`0.607`], [`0.385`], [`-0.950`], [`0.026`],
    [`Control vs ON`], [`9d`], [`frontal`], [`m_e_std`], [`0.574`], [`0.449`], [`-1.132`], [`0.027`],
    [`Control vs ON`], [`9d`], [`frontal`], [`d_n_std`], [`0.852`], [`0.539`], [`-1.107`], [`0.027`],
    [`Control vs ON`], [`9d`], [`parietal_occ`], [`d_n_std`], [`0.597`], [`0.431`], [`-0.878`], [`0.031`],
    table.cell(colspan: 8, fill: rgb("#f0f0f0"))[_Parkinson OFF vs ON_],
    table.cell(colspan: 8)[_No rows at `q < 0.1` in either position layer for the paired contrast._],
  ),
  caption: [Regional MNPS position and stratified coordinate summaries at `q < 0.05`. Left median = Control for disease-state contrasts; Left median = Parkinson OFF for the paired contrast. `strat9_condition_number` is the condition number of the stratified `9D` chart; `trace_mean` is the mean trace of the regional MNPS matrix. Additionally, `e_m_mean` (d ranging from −0.86 to −0.96) and `e_m_std` (d ≈ −0.83) survive at `q < 0.05` for all four networks in both disease-state contrasts; these are global coordinate replications and are not shown as independent rows (see `e_m` note above). `regional_mnps_3d` FDR was corrected across all 25 metrics × 4 networks × 3 contrasts jointly.]
) <tab-s2-regional-mnps>

= Regional Jacobian: `MNJ` summaries

The `regional_mnps_jacobian_3d` and `regional_mnps_jacobian_9d` layers compute Jacobian-derived metrics (trace, anisotropy, `MDR`, etc.) at the network level. This table shows all rows at `q < 0.1`; none reach `q < 0.05` except the `temporal / anisotropy_abs_eig_mean` row for the paired contrast, which is the focal paired row in the main article.

#figure(
  kind: table,
  table(
    columns: (1.5fr, 0.85fr, 1.1fr, 1.6fr, 0.85fr, 0.85fr, 0.7fr, 0.7fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Layer*], [*Network*], [*Metric*], [*Left med*], [*Right med*], [*`d`*], [*`q`*]),
    table.cell(colspan: 8, fill: rgb("#f0f0f0"))[_Control vs Parkinson OFF (near-miss, q < 0.1)_],
    [`Control vs OFF`], [`jac_3d`], [`frontal`], [`frobenius_norm_mean`], [`1.056`], [`0.900`], [`-0.887`], [`0.057`],
    [`Control vs OFF`], [`jac_3d`], [`frontal`], [`rotation_norm_mean`], [`0.659`], [`0.580`], [`-0.862`], [`0.057`],
    [`Control vs OFF`], [`jac_3d`], [`frontal`], [`a_operator_norm_mean`], [`0.996`], [`0.838`], [`-0.887`], [`0.076`],
    [`Control vs OFF`], [`jac_3d`], [`parietal_occ`], [`frobenius_norm_median`], [`1.098`], [`1.277`], [`0.753`], [`0.076`],
    table.cell(colspan: 8, fill: rgb("#f0f0f0"))[_Control vs Parkinson ON (near-miss, q < 0.1)_],
    [`Control vs ON`], [`jac_3d`], [`temporal`], [`trace_mean`], [`0.0733`], [`-0.0235`], [`-1.032`], [`0.025`],
    [`Control vs ON`], [`jac_3d`], [`central`], [`mdr_median`], [`0.581`], [`0.628`], [`0.908`], [`0.025`],
    [`Control vs ON`], [`jac_3d`], [`temporal`], [`trace_median`], [`0.0461`], [`-0.0067`], [`-0.954`], [`0.025`],
    [`Control vs ON`], [`jac_9d`], [---], [`block_anisotropy_mean`], [`185.5`], [`78.5`], [`-0.846`], [`0.013`],
    table.cell(colspan: 8, fill: rgb("#f0f0f0"))[_Parkinson OFF vs ON_],
    [`OFF vs ON`], [`jac_3d`], [`temporal`], [`anisotropy_abs_eig_mean`#super[\*]], [`0.0311`], [`0.0232`], [-0.483#super[z]], [`0.038`],
  ),
  caption: [Regional Jacobian rows at `q < 0.1`. `d_z` (marked #super[z]) is Cohen's `d_z` for the paired contrast; all other rows are unpaired Cohen's `d`. #super[\*]Focal paired row from the main article. `jac_9d block_anisotropy_mean` has no network column as it is a tier-2 global adjunct. Left median = Control for disease-state contrasts; Left median = Parkinson OFF for the paired contrast. The `Control vs ON` Jacobian near-miss rows (`temporal trace_mean/median`, `central mdr_median`) suggest a coordinated reduction in temporal network Jacobian magnitude under dopaminergic medication, consistent with the global `mdr_median` focal row.]
) <tab-s2-regional-jacobian>

= Regional reachability cones

The `regional_reachability_cones_3d` layer assesses how much of the manifold neighbourhood is geometrically accessible per network. All `q < 0.1` rows are concentrated in the `Control vs Parkinson ON` contrast, frontal network; no rows survive in the `Control vs Parkinson OFF` or `Parkinson OFF vs ON` contrasts.

#figure(
  kind: table,
  table(
    columns: (1.5fr, 1.1fr, 2.0fr, 0.85fr, 0.85fr, 0.7fr, 0.7fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Network*], [*Metric*], [*Control med*], [*PD ON med*], [*`d`*], [*`q`*]),
    [`Control vs ON`], [`frontal`], [`tube_capture_gate_mean`], [`0.472`], [`0.431`], [`-1.027`], [`0.053`],
    [`Control vs ON`], [`frontal`], [`tube_capture_gate_median`], [`0.443`], [`0.391`], [`-1.116`], [`0.053`],
    [`Control vs ON`], [`frontal`], [`tube_q_ratio_h4_mean`], [`0.409`], [`0.446`], [`1.008`], [`0.053`],
    [`Control vs ON`], [`frontal`], [`tube_q_ratio_h4_median`], [`0.402`], [`0.461`], [`0.943`], [`0.069`],
    [`Control vs ON`], [`frontal`], [`cone_q_ratio_h3_median`], [`0.483`], [`0.524`], [`0.931`], [`0.069`],
    [`Control vs ON`], [`frontal`], [`cone_q_ratio_h4_median`], [`0.402`], [`0.461`], [`0.943`], [`0.069`],
    [`Control vs ON`], [`frontal`], [`q_ratio_h3_median`], [`0.483`], [`0.524`], [`0.931`], [`0.069`],
    [`Control vs ON`], [`frontal`], [`q_ratio_h4_median`], [`0.402`], [`0.461`], [`0.943`], [`0.080`],
    [`Control vs ON`], [`frontal`], [`cone_q_ratio_h2_median`], [`0.630`], [`0.654`], [`0.932`], [`0.080`],
    [`Control vs ON`], [`frontal`], [`q_ratio_h2_median`], [`0.630`], [`0.654`], [`0.932`], [`0.080`],
  ),
  caption: [Regional reachability cone rows at `q < 0.1`. All retained rows are frontal network, `Control vs Parkinson ON`. `tube_capture_gate` measures the fraction of the neighbourhood captured by the reachability tube; `q_ratio` metrics summarize the quantile distribution of neighbourhood-size ratios at horizon `h`. The direction is mixed: capture gate and tube norm decrease in `Parkinson ON` (lower reachability), while `q_ratio_h3/h4` metrics increase (indicating heavier-tailed neighbourhood distribution). None of these rows reach `q < 0.05` after FDR correction over the full reachability metric inventory.]
) <tab-s2-regional-reachability>

= Files

The tables in this supplement are backed by:

- `results/parkinson_on_off_dual_contract_20260608/primary_standard_contrasts.csv`
- `results/parkinson_on_off_dual_contract_20260608/primary_event_contrasts.csv`
- `results/parkinson_on_off_dual_contract_20260608/primary_trajectory_esb_contrasts.csv`
- `results/parkinson_on_off_dual_contract_20260608/regional_mnps_contrasts.csv` (generated by `src/run_regional_mnps_contrasts.py`)
- `results/parkinson_on_off_cohort_anchor_standard_20260601_163214/cohort_anchor_centroid_summary.csv`
- `results/parkinson_on_off_dual_contract_20260608/additional_qc_20260603_classical_shuffle/qc_focal_nmd_vs_classical_summary.csv`
- `results/parkinson_on_off_dual_contract_20260608/exploratory_summary.md`

#bibliography("parkinson_on_off_trajectory_geometry.bib")