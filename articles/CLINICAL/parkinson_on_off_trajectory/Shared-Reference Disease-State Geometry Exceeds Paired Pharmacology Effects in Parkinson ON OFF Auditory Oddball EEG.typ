#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Shared-Reference Disease-State Geometry Exceeds Paired Pharmacology Effects in Parkinson ON/OFF Auditory Oddball EEG",
  short-title: "Parkinson Disease-State Geometry",
  subtitle: "A mixed-contract NeuralManifoldDynamics analysis of ds003490",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "Parkinson disease",
    "auditory oddball",
    "EEG",
    "trajectory geometry",
    "NeuralManifoldDynamics",
    "MNPS",
    "reachability",
  ),
  article-type: "Research Article",
  abstract: [
    Parkinson `ON/OFF` EEG here refers specifically to medication state: Parkinson participants were tested both `ON` dopaminergic medication and `OFF` dopaminergic medication. That design raises two different inference problems: disease-state structure is a between-subject comparison, whereas medication response is a paired within-subject comparison. We reran the NeuralManifoldDynamics `ds003490` bundle (`75` runs; `25` Parkinson `ON/OFF` pairs and `25` controls) with a mixed-contract design, using `cohort_anchored` coordinates for `Control vs Parkinson OFF` and `Control vs Parkinson ON`, and `subject_anchored` coordinates for `Parkinson OFF vs ON`. The article-local trajectory wrapper also replaced nearest-time oddball mapping with H5 `event_windows/*` start/stop indices when available. At the stricter main-text threshold of `BH-FDR q < 0.05`, `47` rows survived: `35` standard rows, `12` event-locked trajectory rows, and `0` trajectory ESB rows. Although the source dataset is auditory oddball EEG, the strongest retained effects were not primarily paired oddball medication-response effects; they were shared-reference disease-state and eyes-closed trajectory effects. `Control vs Parkinson OFF` was characterized by lower cohort-anchor `9D` dispersion and lower global eyes-closed trajectory speed and kinetic cost, including regional frontal `d_n_std` (`d = -1.268`, `q = 0.018`) and global eyes-closed `speed_median` (`d = -1.212`, `q = 0.0025`). `Control vs Parkinson ON` was led by global `9D` Jacobian `mdr_median` (`d = 1.167`, `q = 0.0095`) and by global tone-loop asymmetry, especially `novel_tone` `hysteresis_area_me` (`d = -1.039`, `q = 0.0269`). By contrast, the paired medication comparison retained only one subject-anchor row, `regional_mnps_jacobian_3d` temporal `anisotropy_abs_eig_mean` (`d_z = -0.483`, `q = 0.038`), and no event-locked or ESB row. Medication changes some aspects of the exported dynamics, but does not collapse the Parkinson state onto the control state. These results support a bounded conclusion: within this processed `ds003490` bundle, shared-reference disease-state geometry is internally stable under influence and trajectory-label sanity checks, whereas paired medication geometry remains narrow and hypothesis-generating.
  ],
  author-summary: [
    This rerun asks the Parkinson question in a way that is easier to defend under review. Disease-state contrasts against controls are evaluated in a cohort-shared coordinate frame, while the paired `OFF` versus `ON` medication contrast remains in a subject-shared frame. At `q < 0.05`, disease-state structure remains broad across both standard and event-locked layers, but the within-subject medication effect remains narrow. The strongest retained disease findings are shared-reference and eyes-closed effects for `Parkinson OFF`, while the strongest medicated disease-state finding is elevated global `9D` Jacobian `MDR` in `Parkinson ON`. Exact `event_windows/*` alignment improves the event contract and changes which tone rows survive, but it does not rescue the paired oddball pharmacology story. The resulting paper is therefore best read as a disease-state geometry paper with a narrow, hypothesis-generating pharmacology branch.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted in the submission version.],
  data-availability: [
    Data were analyzed from the publicly available OpenNeuro dataset `ds003490` (Cavanagh, 2021)@cavanagh2021ds003490, accessed via local NeuralManifoldDynamics export at `data/raw/neuralmanifolddynamics_ds003490_20260602_144145`. Mixed-contract result tables for this manuscript are stored under `articles/CLINICAL/parkinson_on_off_trajectory/results/parkinson_on_off_dual_contract_20260602`, including `primary_standard_contrasts.csv`, `primary_event_contrasts.csv`, `primary_trajectory_esb_contrasts.csv`, and `exploratory_summary.md`. Supplementary methods, data tables, and robustness notes are provided in `S1_Supplementary_methods.typ`, `S2_Supplementary_data.typ`, and `S3_Supplementary_QC_Robustness.typ`.
  ],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

= Introduction

The central problem in OpenNeuro `ds003490`@cavanagh2021ds003490 is not simply whether Parkinson EEG differs across states, but whether the disease-state question and the medication-response question should be asked in the same geometric frame. In this article, Parkinson `ON` and `OFF` refer to recording sessions acquired on versus off dopaminergic medication, not to disease stage. `Control vs Parkinson` is a between-subject reference problem and is therefore best posed in a cohort-shared coordinate system. `Parkinson OFF vs ON` is a paired within-subject problem and is therefore best posed in a subject-shared coordinate system. The previous manuscript effectively forced both questions into one contract. This rerun treats the contract split as a first-order design choice rather than as an appendix repair.

Parkinson EEG has been studied both as a resting-state marker of cortical slowing and network reorganization and as an event-related marker of altered attention, novelty processing, and cognitive control.@wang2020eegreview @oldedubbelink2013slowing @swann2015synchrony Prior work links Parkinson disease and Parkinson-related cognitive impairment to spectral slowing patterns involving theta/alpha shifts, as well as to altered ERP / P300 responses during auditory or visual oddball paradigms.@wang2020eegreview @seer2016erp @ferrazoli2022p300 @georgiev2015auditory @bertram2020novelty These findings motivate the use of both resting / eye-state and event-linked surfaces, but they also caution against reducing Parkinson EEG to a single medication-normalization axis.

That change matters especially for auditory oddball EEG. The processed bundle contains both continuous eye-state structure (`eyes_closed`, `eyes_open`) and event-driven structure (`Standard Tone`, `Novel Tone`, `Target Tone`) inside a run normalized as `task = rest`. This allows one standard NeuralManifoldDynamics layer (`MNPS`, Jacobian / MNJ-like, and reachability summaries) and one article-local event-locked trajectory layer built from path cost, curvature, hysteresis, and related geometry.@michel2018microstates, @vyas2020population, @mitchellheggs2023manifold

The new bundle also improves the event contract itself. The wrapper no longer needs to rely primarily on nearest-time onset mapping, because H5 `event_windows/*` now provides exact processed-window start and stop indices. That makes the event segmentation cleaner, even if it does not automatically produce more retained pharmacology rows.

#netn-box(title: [Primary design principle])[
  `cohort_anchored` is primary for disease-state inference (`Control vs Parkinson OFF`, `Control vs Parkinson ON`).

  `subject_anchored` is primary for paired pharmacology inference (`Parkinson OFF vs ON`).

  The main text is deliberately restricted to seven article-facing representative rows from the merged primary inventory, with extended methods and tables moved to `S1-S3`.
]

= Cohort and analysis design

The analyzed bundle contains `75` H5 runs from `50` unique subjects: `25` control runs, `25` Parkinson `OFF` runs, and `25` Parkinson `ON` runs. Each Parkinson subject contributes both medication states. Control subjects contribute a single `not_applicable` session. Age and sex are available for all `75` runs in `participant/clinical_json`, but several clinically useful disease-severity variables remain unavailable or incomplete, including measures such as `LEDD`, `UPDRS`, and disease duration.

Two linked layers were run:

1. a standard repository `ndt-analysis` path producing global and regional `MNPS 3D`, `MNPS 9D`, Jacobian / MNJ-like, and reachability outputs;
2. an article-local wrapper producing stage-locked and event-locked trajectory summaries in global and regional `3D` and `9D` spaces.

At `BH-FDR q < 0.05`, the merged primary inventories retain `35` standard rows, `12` event-locked trajectory rows, and `0` trajectory ESB rows (see @tab-threshold-inventory). The fuller `q < 0.1` inventory is preserved in `S2` as an audit surface rather than as the headline claim layer.

#figure(
  kind: table,
  table(
    columns: (1.1fr, 0.8fr, 0.8fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Threshold*], [*Standard*], [*Event*], [*ESB*], [*Total*]),
    [`q < 0.05`], [`35`], [`12`], [`0`], [`47`],
    [`q < 0.1`], [`69`], [`18`], [`0`], [`87`],
  ),
  caption: [Retained mixed-contract inventory by reporting threshold. The stricter `q < 0.05` layer defines the main-text claim surface, whereas the broader `q < 0.1` layer is retained only for transparency and follow-up analysis in `S2`. The `35` standard rows at `q < 0.05` include `12` regional replications of the global `e_m` coordinate; the deduplicated distinct count is `23`. This does not affect any focal-row claim in the main text. See `S2` and `S3` for details.]
) <tab-threshold-inventory>

= Methods

== Noetic Diffusion and NeuralManifoldDynamics framing

The main article treats Noetic Diffusion as the broader dynamical framing and NeuralManifoldDynamics as the operational measurement layer used to export analyzable coordinates and local summaries.@langell2025_6, @langell2026_mndm, @langell2026_compendium At the level used here, the exported `3D` chart is `x_t = [m_t, d_t, e_t]^T`, and the stratified `9D` chart is `x_t^(9) = [m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m]^T`. In this article, these coordinates are treated as fixed analysis objects rather than as proof of a unique latent biological mechanism.

Within that operational framing, NeuralManifoldDynamics contributes three linked summary layers. First, `MNPS` summarizes where the system sits in the exported chart. Second, the Meta-Noetic Jacobian / Jacobian layer summarizes local deformation of that chart through `J_t = partial f / partial x`. Third, reachability summaries approximate the short-horizon future-space geometry from local linearization. The article-local trajectory wrapper then adds realized-path summaries above the same exported coordinate contract.

== Standard and wrapper execution

The standard path used parallel subject-anchor and cohort-anchor configs under `ndt-analysis/config/`. The wrapper resolved both global and regional coordinate layers by requested contract and used contract-specific `regional_mnps/<network>/<coordinate_contract>/...` groups when available.

Oddball blocks were built from `event_windows/event_label`, `event_start_window_index`, and `event_stop_window_index` when those fields were present. The previous `/events/onset_sec` nearest-time logic was retained only as a guarded fallback. Eye-state blocks were derived from the H5 stage codebook and `labels/stage`.

== Focused metric definitions for the main rows

The wrapper reported speed, curvature, tortuosity, path length, peak displacement, recovery residual, hysteresis, entropy-rate, irreversibility, entropy production, self-loop rate, transition sparsity, and noetic-action terms (`total`, `kinetic`, `jerk`, `potential`). The main paper emphasizes the following operational definitions.

- `d_n_std`: the across-window standard deviation of the stratified `d_n` coordinate. In the compact NMD notation, `d_n = 1 - norm(avg_W(Tr(H(t_h,w)) / |V|))`, so `d_n_std` indexes variability of the network-deviation family across valid windows rather than a single static point estimate.
- `speed_median`: the median over valid steps of `|| z_(t+1) - z_t || / Delta t`.
- `noetic_action_kinetic`: the median kinetic component of the article-local action decomposition, `K_t = (1 / 2) || Delta z_t ||_M^2 / Delta t^2`, where `M` is the diagonal variance-stabilized metric.
- `mdr_median`: the median Jacobian-change ratio `D_t = || dot(J)_t ||_F / (|| J_t ||_F + epsilon)`, interpreted here as a size-normalized summary of how rapidly local Jacobian structure changes over time.
- `hysteresis_area_me`: the polygonal loop area between the forward and recovery paths in the projected `(m,e)` family plane. Larger values mean greater asymmetry between the outbound and return trajectory in that family projection.
- `anisotropy_abs_eig_mean`: the mean over valid windows of the variance of absolute Jacobian eigenvalues across eigenvalue dimensions. Larger values indicate more anisotropic local deformation, with eigenvalue magnitudes spread unequally across state-space directions. The retained paired row (`temporal / anisotropy_abs_eig_mean`, `d_z = -0.483`, `q = 0.038`) is interpreted directionally as a shift in Jacobian directional spread between `OFF` and `ON` states, rather than as a standalone mechanistic biomarker.

Trajectory ESB remained exploratory and yielded no retained row in the current primary inventory.

Standard and wrapper contrasts were corrected by BH-FDR within contrast and analysis-type families. The main-text threshold was tightened to `q < 0.05`, while the broader `q < 0.1` inventory is preserved in `S2`. Extended methods, metric definitions, and contract details are given in `S1`.

#netn-box(title: [Confirmatory status of the focal rows])[
  *Confirmatory status:* none. No primary endpoint was preregistered.

  *Internal-support status:* BH-FDR `q < 0.05` within contrast and analysis-type families; leave-one-subject-out sign stability; trajectory-label sanity null for event-locked rows; partial non-reducibility to classical EEG sidecars.

  *External-validation status:* absent. Results are bounded to this processed `ds003490` export surface.
]

= Results

== Seven focal effects at `q < 0.05`

The main article is intentionally restricted to seven rows (@tab-seven-effects) that together capture the primary disease-state and pharmacology story while avoiding redundancy.

#figure(
  kind: table,
  table(
    columns: (1.55fr, 1.0fr, 1.55fr, 1.4fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
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
  caption: [The seven focal rows emphasized in the main text. Medians follow the contrast order named in the first column. The `d` column reports Cohen's `d` for unpaired rows and Cohen's `d_z` (marked `z`) for the paired `OFF vs ON` row.]
) <tab-seven-effects>

These seven rows were chosen because they satisfy three criteria simultaneously: high effect magnitude, survival at the stricter `q < 0.05` threshold, and non-redundant coverage of the main inferential questions.

They should nonetheless be read as post hoc article-facing representatives from the corrected retained inventory rather than as preregistered primary endpoints. Their role is to summarize the dominant signal families in the processed bundle, not to define a frozen biomarker panel.

== Disease-state geometry in Parkinson OFF

`Control vs Parkinson OFF` is the clearest disease-state contrast in the rerun. The strongest standard rows are cohort-anchor `9D` dispersion summaries, especially frontal `d_n_std` (`d = -1.268`, `q = 0.018`) and global `d_n_std` (`d = -1.194`, `q = 0.013`). The strongest event-locked rows are global eyes-closed trajectory metrics, especially `speed_median` (`d = -1.212`, `q = 0.0025`) and `noetic_action_kinetic` in `9D` (`d = -1.085`, `q = 0.0050`).

This combination matters conceptually. The standard layer says that Parkinson `OFF` differs from controls in shared-reference stratified dispersion. The event-locked layer says that the same `OFF` state also traverses the eyes-closed geometry with altered speed and altered kinetic cost. The simplest defensible reading is therefore not one isolated biomarker, but convergence between a static `9D` disease-state separation and a dynamic eyes-closed trajectory abnormality.

Regional EEG findings are treated here as localization-supporting rather than as independent anatomical claims. The global `9D` `d_n_std` row is the safer disease-state representative; the frontal row is retained because it is the strongest regional instance but does not carry additional anatomical certainty beyond the global result. Subject-level distributions for these four focal rows are shown in @fig-control-off-violins.

#figure(
  image("figures/violin/control_vs_off_ndt.png", width: 92%),
  caption: [Subject-level violin plots for the four focal `Control vs Parkinson OFF` NDT/NMD rows (cohort-anchor contract). The panel combines the strongest cohort-anchor `9D` dispersion rows with the strongest eyes-closed trajectory rows, making visible that the `OFF` disease-state signal is expressed in both the standard and event-locked layers.]
) <fig-control-off-violins>

== Disease-state geometry in Parkinson ON

`Control vs Parkinson ON` is broader than a simple "medication normalizes the system" story would predict. The leading `Control vs Parkinson ON` standard row is `global_mnps_jacobian_9d / mdr_median` (`d = 1.167`, `q = 0.0095`). In parallel, the event-locked layer retains global tone hysteresis, especially `novel_tone` `hysteresis_area_me` (`d = -1.039`, `q = 0.0269`).

This pairing is central to the revised manuscript. The medicated Parkinson state is not merely drifting toward control. It remains globally non-control-like in a Jacobian / deformation sense, while also showing retained tone-loop asymmetry in the wrapper layer. Medication changes some aspects of the exported dynamics, but does not collapse the Parkinson state onto the control state. That is a stronger and more review-resistant claim than the earlier idea that the article was primarily an `ON/OFF` medication-success story. The subject-level distributions are shown in @fig-control-on-violins.

#figure(
  image("figures/violin/control_vs_on_ndt.png", width: 92%),
  caption: [Subject-level violin plots for focal `Control vs Parkinson ON` NDT/NMD rows (cohort-anchor contract). The panel shows that the medicated Parkinson state still departs from control on both the global `9D` Jacobian surface (`mdr_median`) and the tone-centered hysteresis surface, supporting a residual disease-state rather than a full normalization reading.]
) <fig-control-on-violins>

== Paired pharmacology remains narrow

The within-subject medication contrast remains limited. Only one subject-anchor row survives the primary threshold: `regional_mnps_jacobian_3d` temporal `anisotropy_abs_eig_mean` (`d_z = -0.483`, `q = 0.038`). The previously retained `tier2_jacobian` `signed_divergence_balance_mean_neg` (`d_z = -0.711`, `q = 0.066`) is now a near-miss after the mathematical sanity correction to persistence-based metrics. No event-locked row and no ESB row survive `q < 0.05`.

That outcome is scientifically useful even if it is not dramatic. The paired branch carries a minimal non-null signal — one abstract Jacobian adjunct without convergent event-layer or ESB support — and should not be read as a medication-response signature. The mixed-contract redesign therefore clarified that this dataset is much stronger for disease-state geometry than for paired medication geometry. The subject-level distribution for the single retained row is shown in @fig-off-on-violins.

That narrow paired result is consistent with a broader literature in which dopaminergic therapy can modulate EEG features, but not always as a simple global normalization. Acute L-dopa has been reported to increase alpha and beta power in centro-parietal regions, while other EEG biomarker work suggests medication-sensitive changes in synchronization and related electrophysiological state markers.@melgari2014ldopa @miller2019levodopa The present result is therefore compatible with medication sensitivity, but not with a broad medication-response signature in this processed bundle.

#figure(
  image("figures/violin/off_vs_on_ndt.png", width: 72%),
  caption: [Subject-level violin plot for the only retained paired `Parkinson OFF vs ON` NDT/NMD row, `tier2_jacobian / signed_divergence_balance_mean_neg` (subject-anchor contract). The figure makes explicit that the paired medication effect is a minimal non-null signal, present but narrow, with no parallel corrected event-locked panel to broaden the pharmacology claim.]
) <fig-off-on-violins>

== Event-window outcome

The shift to exact `event_windows/*` segmentation changed the tone-centered inventory in a way that becomes clearer under the stricter threshold. In the earlier one-contract run, no tone-centered row survived `q < 0.05`. In the current mixed-contract primary inventory, two tone rows survive `q < 0.05`, both in `Control vs Parkinson ON`: `novel_tone` and `standard_tone` `hysteresis_area_me`.

The event contract is therefore cleaner, but the paired oddball pharmacology question remains weak. Although the source data come from auditory oddball EEG, the strongest retained disease-state effects are not primarily paired oddball medication-response effects. This distinction matters because auditory oddball and novelty paradigms have repeatedly shown dopaminergic and cognitive effects in Parkinson disease, including altered distractor processing and novelty-related P3 responses.@georgiev2015auditory @bertram2020novelty The present wrapper results therefore do not argue against oddball sensitivity in Parkinson disease. Rather, they show that under the current processed-window geometry contract the corrected event-linked signal is disease-state-facing and limited, while the paired `OFF vs ON` oddball pharmacology branch remains weak. This is precisely the kind of negative-but-important result that improves the manuscript's defensibility.

= Discussion

The main qualitative improvement in this manuscript is inferential alignment. Disease-state claims now sit on the correct shared-reference cohort anchor, and paired pharmacology claims sit on the correct subject anchor. Once that alignment is enforced, the data tell a simpler story than before.

First, disease-state geometry is broad. `Parkinson OFF` differs from controls in both cohort-anchor `9D` dispersion and eyes-closed event-locked trajectory cost / speed. `Parkinson ON` remains globally non-control-like in `9D` Jacobian `MDR` and retains tone-hysteresis differences relative to controls. The medicated state is therefore altered, but not normalized.

Second, paired medication geometry is narrow. The rerun does not support a broad claim that dopamine state robustly reorganizes event-locked trajectory geometry across the main families. The one retained paired row (`temporal anisotropy_abs_eig_mean`, `d_z = -0.483`, `q = 0.038`) is real enough to report, but it is not sufficient to carry the article by itself. A previously prominent near-miss (`signed_divergence_balance_mean_neg`, `d_z = -0.711`, `q = 0.066`) narrowly falls outside the primary threshold following correction of a mathematical error in persistence-based Jacobian metrics.

Third, the wrapper remains valuable even though it does not dominate every layer. Its strongest retained disease-state rows are not generic and not redundant with the standard layer. They add a path-cost and loop-asymmetry view that the static and Jacobian layers do not provide directly.

Fourth, the conventional EEG sidecars improve interpretability but do not displace the main geometric story in this article-facing inventory. No classical comparator row survives `q < 0.1`, which supports incremental descriptive value of the NDT/NMD rows within this processed bundle, but not any general claim of benchmark superiority over standard EEG. The supplement-level focal-row sensitivity analysis against the classical panel also remains limited to partial alignment rather than simple reducibility, with the strongest group-adjusted associations concentrated around eyes-closed speed and tone hysteresis rather than the full focal set.

Fifth, several recent machine-learning and signal-decomposition studies have already reused Parkinson resting-state or oddball EEG datasets including `ds003490`, but that classification-oriented literature does not replace the present article's inferential focus on mixed-contract disease-state versus paired pharmacology geometry.@shabanpour2022subsecond @smrdel2025ica

= Limitations

1. The paper remains exploratory even though the main text is now restricted to `BH-FDR q < 0.05`, and the fuller `q < 0.1` inventory is kept only for auditability in `S2`.
2. `event_windows/*` improves processed-window alignment but does not convert the wrapper into a raw single-trial ERP reconstruction.
3. Important clinical severity covariates such as `LEDD`, `UPDRS`, and disease duration are still unavailable or incomplete. Without them, the present bundle cannot cleanly separate disease severity, medication exposure, chronic compensation, subtype, fatigue / attention, and related state effects.
4. The circular time-shift null discussed in `S3` is a low-resolution sanity null on exported trajectories rather than a full raw-signal permutation analysis.
5. Trajectory ESB remains negative in the current rerun and should not be framed as a validated disease score.
6. Classical EEG sidecars were included for comparison, and focal-row sensitivity checks suggest partial alignment rather than simple reducibility, but this is still an internal sidecar analysis rather than a formal incremental-validity benchmark.
7. The current paper is built from one processed bundle and is internally stable under influence and trajectory-label sanity checks, but does not yet include external replication.

= Conclusion

This mixed-contract analysis is a better article for review because it asks the correct geometric question in the correct coordinate frame. The strongest results are not a broad paired medication normalization story. They are a cohort-anchor disease-state story: within this processed `ds003490` export surface, Parkinson `OFF` differs from controls in stratified dispersion and eyes-closed trajectory cost, while Parkinson `ON` remains globally non-control-like in `9D` Jacobian `MDR` (`d = 1.167`) and retains tone-hysteresis differences relative to controls. Medication changes some aspects of the exported dynamics, but does not collapse the Parkinson state onto the control state. The paired `OFF` versus `ON` branch retains one subject-anchor row (`temporal anisotropy_abs_eig_mean`, `d_z = -0.483`, `q = 0.038`) and a strong near-miss (`signed_divergence_balance_mean_neg`, `d_z = -0.711`, `q = 0.066`), but is too narrow to support a medication-response claim beyond this exploratory report.


= Acknowledgements

This work emerged through structured correspondence among human and AI collaborators; large language models from OpenAI, Anthropic, and Google assisted in literature synthesis, drafting, peer review, and editorial refinement. We also gratefully acknowledge James F. Cavanagh, the original investigators, clinical teams, participants, and data stewards who created, curated, and shared the public datasets and metadata that made these analyses possible.

= Contact

Robin Langell - hello(at)noeticdiffusion.com

= Licensing

Licensing, stewardship, and any related trademark notes are summarized at `https://noeticdiffusion.com/license.html` and do not alter the scientific claims or reproducibility boundaries discussed here.

= Data and Code Availability

Reference implementations and analysis pipelines:
`https://github.com/NoeticDiffusion`

Datasets and related public bundles:
`https://github.com/NoeticDiffusion/NeuralManifoldDynamics-dataset`

#bibliography("parkinson_on_off_trajectory_geometry.bib")
