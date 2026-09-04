#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Depressive Symptom Geometry Across Rest and Probabilistic Selection",
  short-title: "Depression Rest-Task Geometry",
  subtitle: "A paired NeuralManifoldDynamics 2.1 report for ds003474 and ds003478",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "depression",
    "BDI",
    "probabilistic selection",
    "rest-task comparison",
    "reachability cones",
    "MNJ",
  ),
  article-type: "Research Article / Compact Empirical Report",
  abstract: [
    We analyzed the probabilistic-selection EEG dataset `ds003474` together with its resting-state companion `ds003478`, using Beck Depression Inventory (BDI) score as the primary clinical axis and preserving subject-level pairing through shared participant identifiers and `Original_ID`. The paired overlap was complete at the metadata level (`122/122` subjects; `121` with usable BDI), with `sub-038` excluded from inferential summaries because its task/rest metadata row is invalid. On the task-state surface alone, the strongest low-versus-high BDI effects did not appear in coarse `3D` summaries. They localized to reachability (`tube_log_eig_var_mean`, `d = -0.719`, `q = 0.0107`) and block-resolved `9D` Jacobian structure (`block_frobenius_mean`, `e -> d`, `d = -0.778`, `q = 0.0109`). Continuous task-state BDI analyses reproduced the same ordering, with reachability (`rho = -0.398`, `q = 0.00271`) and distribution summary (`e_m_mad_sigma`, `rho = 0.313`, `q = 0.0290`) providing the clearest stable associations. Event-locked analyses around feedback, stimulus, and response windows were dominated by speed-like summaries but did not survive FDR correction, although post-feedback and late-training speed showed suggestive positive BDI correlations. Crucially, paired `task-minus-rest` summaries were broadly null across the selected block surface. The bounded conclusion is therefore twofold: depressive symptom burden is visible in task-state local dynamics and reachability geometry, but the present paired analysis does not support a strong BDI-dependent rest-to-task reconfiguration claim on the selected delta surface.
  ],
  data-availability: [
    Manuscript-facing outputs for this paired article are stored under `articles/CLINICAL/depression_probalistic_selection/results/` and `articles/CLINICAL/depression_probalistic_selection/figures/`. Key tables include `paired_overlap_subjects.csv`, `demography_summary.csv`, `selected_metrics_summary.csv`, `bdi_correlations_summary.csv`, `clinical_bdi_bin_summary.csv`, `event_locked_summary.csv`, `event_locked_correlation_summary.csv`, `paired_delta_summary.csv`, and `paired_delta_correlation_summary.csv`. The paired participant table used by the article is stored under `articles/CLINICAL/depression_probalistic_selection/metadata/participants.tsv`.
  ],
  competing-interests: [
    No competing interests are declared in this draft.
  ],
)

= Introduction

The resting-state depression report for `ds003478` showed that depressive symptom burden was more visible in reachability and higher-dimensional local dynamics than in coarse `3D` summaries. The natural next question is not whether the same cohort also shows task-state signal, but whether symptom-linked geometry changes when the system is placed under reinforcement-learning demands.

This compact paired report therefore uses the probabilistic-selection task dataset `ds003474` together with the resting-state companion dataset `ds003478`. The design stays deliberately narrow and auditable. We ask four bounded questions:

1. Does the task-state surface show the same broad ordering as the resting-state article, namely stronger signal in reachability / higher-dimensional dynamics than in selected `3D` summaries?
2. Do continuous BDI analyses inside the task reproduce the same ordering as the low-versus-high contrast?
3. Do event-locked task windows add symptom-linked structure beyond subject-averaged task geometry?
4. Does the paired `task-minus-rest` surface reveal a robust BDI-dependent reconfiguration?

This is not presented as a diagnostic major depression biomarker paper. It is a paired rest-task analysis of one young cohort, one symptom axis, and one fixed NeuralManifoldDynamics export surface.

= Methods

== Paired cohort

The article uses the participant table under `articles/CLINICAL/depression_probalistic_selection/metadata/participants.tsv`, which reuses the richer depression metadata already validated for the resting-state report. The task-source metadata from `N:/received/ds003474/participants.tsv` matched it exactly for `Original_ID` in all `122` subjects and for `BDI` / `STAI` in all `121` valid rows. Both the task and rest analysis surfaces contained `122` subjects, producing a complete paired overlap with one invalid metadata row (`sub-038`).

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
  caption: [Table 1: Cohort summary derived from `articles/CLINICAL/depression_probalistic_selection/results/demography_summary.csv`.]
) <tab-cohort>

As in the resting-state article, the sample is young and age-compressed, the middle BDI band is relatively small (`n = 15`), and BDI should be read as a symptom burden axis rather than as a frozen diagnostic case-control label.

== Task-state and paired surfaces

The task recordings were processed from the already-generated subject H5 exports under `data/raw/neuralmanifolddynamics_ds003474_20260609_044822/`, then converted into article-local cleaned and analysis parquets. The main task-state article surface spans global `3D` and `9D` MNPS, global `3D` and `9D` MNJ, block-MNJ, reachability, `tier2_emmi`, and distribution summaries. The same subject-level surface from the prior `ds003478` report was reused for the resting-state arm.

For task-only summaries, BDI was evaluated in three complementary ways:

1. `BDI 0-13` versus `BDI 20-63`
2. continuous BDI correlations across `All_valid`, `LowHigh_only`, and `High_BDI_only`
3. clinical BDI-band contrasts for `0-13`, `14-19`, and `20-63`

The current `ds003474` `subject_metrics` export was fully populated, but the generated `contrast_results` parquet contained no contrast rows. To keep the task-state layer auditable and reproducible, the low-versus-high task summaries reported here were recomputed directly from `subject_metrics` using the same BDI-band definitions as the rest article.

For the paired surface, selected block-level metrics were extracted from both the task and rest `subject_metrics` tables and combined as `task - rest` for each participant. This means the paired analysis tests symptom-linked change in the selected metric surface itself rather than a broader multivariate joint model.

== Event-locked layer

The task H5 files contain additive `event_windows` tables aligned to the cohort-anchored `3D` / `9D` coordinates and `mnps_3d_dot`. We aggregated six event families:

1. `feedback_correct`
2. `feedback_incorrect`
3. `train_stim_any`
4. `test_stim_any`
5. `left_response`
6. `right_response`

For each family, we summarized `pre_near`, `event`, and `post_near` windows using the cohort-anchored `m`, `d`, `e`, `e_m`, `m_o`, and `speed` (`||dot(x)||`) summaries. These event-locked results should be read as exploratory because they were not pre-frozen in the resting-state article and because none of the selected event summaries survived FDR correction.

= Results

== Task-state low-versus-high BDI effects

The task-only `3D` and coarse `9D` summaries remained weak. The selected `3D` MNPS effect (`d_median`) was small (`d = -0.145`, `q = 0.612`), the selected `9D` MNPS effect (`d_s_mean`) was similarly small (`d = -0.099`, `q = 0.848`), and the selected global `3D` / `9D` MNJ metrics were not close to corrected significance (`q = 0.996` and `q = 0.404`, respectively).

The strongest selected low-versus-high BDI task effects instead concentrated in the same general neighborhood that mattered in rest: block-resolved `9D` dynamics and reachability. The clearest corrected signals were:

1. block-MNJ `block_frobenius_mean`, `e -> d`: `d = -0.778`, `p = 0.00143`, `q = 0.0109`
2. reachability `tube_log_eig_var_mean`: `d = -0.719`, `p = 0.00153`, `q = 0.0107`

The task distribution summary still shifted in the expected direction (`e_m_mad_sigma`, `d = 0.506`, `p = 0.0330`), but did not survive correction (`q = 0.665`). The practical reading is restrained but clear: depressive symptom burden is visible in the task-state export, yet the dominant separation is carried by local dynamic structure and reachable neighborhood geometry rather than by coarse state-space position alone.

#figure(
  image("figures/probsel_selected_effect_heatmap.png", width: 100%),
  caption: [Figure 1: Selected task-state low-versus-high BDI effects. The strongest corrected separation localizes to block-resolved `9D` dynamics and reachability rather than to the selected `3D` summaries.]
) <fig-selected>

== Continuous BDI ordering inside the task

Continuous task-state BDI analyses reproduced the same ranking. Across all valid participants, the clearest selected correlations were:

1. reachability `tube_log_eig_var_mean`: `rho = -0.398`, `q = 0.00271`
2. distribution `e_m_mad_sigma`: `rho = 0.313`, `q = 0.0290`
3. block-MNJ `block_frobenius_mean`, `e -> d`: `rho = -0.345`, `p = 0.00347`, `q = 0.0938`

Again, the selected `3D` layers remained weak (`3D` MNPS `rho = -0.041`, `q = 0.758`; `3D` MNJ `rho = 0.081`, `q = 0.547`). Restricting the analysis to the low-plus-high subset preserved the same ordering, especially for reachability (`rho = -0.409`, `q = 0.00765`), while the `High_BDI_only` subset was broadly null. This reproduces the main pattern from the resting-state article: the strongest organization looks more like a low-to-elevated regime separation than a smooth severity gradient within the already elevated range.

#figure(
  image("figures/probsel_bdi_correlation_panel.png", width: 100%),
  caption: [Figure 2: Selected continuous BDI associations inside the task-state surface. Reachability remains the most stable task-state signal, with additional support from distribution summaries and a weaker block-MNJ trend.]
) <fig-bdi-corr>

The exploratory clinical-bin pass pointed in the same qualitative direction without producing fresh corrected results. `BDI 0-13` versus `14-19` showed the strongest uncorrected reachability (`d = -0.492`, `p = 0.0317`) and distribution (`d = 1.093`, `p = 0.00683`) effects, while `BDI 14-19` versus `20-63` was broadly weak. This supports the same threshold-like interpretation as the continuous pass, but with limited additional inferential weight because the corrected `q` values remained above `0.05`.

== Event-locked task windows

The selected event-locked summaries were dominated by `speed_mean` rather than by direct `m`, `d`, or `e` displacement. Low-versus-high BDI event effects were small to moderate in raw magnitude, especially around feedback and response windows (`d` roughly `0.21` to `0.27`), but none survived correction.

The continuous event-locked analysis was somewhat more informative. The most suggestive positive BDI associations appeared in:

1. `feedback_incorrect`, `post_far` speed: `rho = 0.203`, `p = 0.0255`, `q = 0.0764`
2. `train_stim_any`, `post_far` speed: `rho = 0.196`, `p = 0.0310`, `q = 0.0931`
3. `feedback_correct`, `post_near` speed: `rho = 0.185`, `p = 0.0423`, `q = 0.127`

By contrast, the aggregated `test_stim_any` windows were near-null across all three bins. The safest reading is that symptom burden may be linked to modestly elevated peri-feedback and late-training task speed, but the current event-locked evidence is still exploratory rather than stable.

#figure(
  image("figures/probsel_event_locked_heatmap.png", width: 100%),
  caption: [Figure 3: Selected event-locked low-versus-high BDI effects across the task. The selected metric is consistently speed-like, but none of the event families survives FDR correction.]
) <fig-event>

== Paired task-minus-rest deltas

The paired rest-task layer is notable mainly for what it does *not* show. None of the selected `task - rest` summaries produced a robust low-versus-high BDI effect, and none produced a stable continuous BDI association. The largest raw low-versus-high delta effect was the `tier2_emmi` summary (`mv_median`, `d = 0.337`, `p = 0.101`), but it was not close to correction. Reachability, which was strong in both the rest article and the task-only analysis here, was essentially null on the paired delta surface (`d = -0.130`, `q = 0.804`; `rho = -0.061`, `q = 0.915`).

This matters for interpretation. The current paired evidence does not support the stronger story that higher BDI primarily reflects a large, easily detectable rest-to-task reconfiguration failure on the selected scalar block surface. The cleaner reading is weaker: symptom-linked geometry is visible in rest and in task, but the *difference* between those two surfaces does not currently emerge as a robust BDI-organized endpoint under this selected pairing strategy.

#figure(
  image("figures/probsel_paired_delta_panel.png", width: 100%),
  caption: [Figure 4: Selected paired `task-minus-rest` effects. The paired delta surface is broadly null, despite task-only and rest-only symptom-linked structure on several individual layers.]
) <fig-paired>

= Discussion

The paired design narrows the depression claim rather than enlarging it.

First, the task-state analysis independently supports the general emphasis from the resting-state article: depressive symptom burden is more visible in higher-order local geometry than in the selected coarse `3D` summaries. Second, the task surface adds a somewhat stronger block-resolved `9D` result than the original rest article, especially the `e -> d` block-MNJ separation. Third, the event-locked layer does not currently overturn the subject-averaged story; it provides suggestive peri-feedback and training-speed effects, but not corrected ones.

The most important negative result is the paired one. If high-BDI participants had shown a strong rest-to-task reconfiguration deficit on the selected delta surface, the paired analysis should have sharpened rather than erased the rest/task signal. It did not. That does not mean the rest-task idea is false in general. It means the present scalar paired readout, on this export surface, is not yet the strongest defended claim.

= Limitations

This manuscript has several important limits.

1. It is a single-cohort paired report in a young, age-compressed sample.
2. The task-state `9D` Jacobian and related block summaries have smaller usable denominators than the full cohort.
3. The low-versus-high task contrast had to be recomputed from `subject_metrics` because the generated `contrast_results` parquet for `ds003474` contained no contrast rows.
4. Event-locked summaries are exploratory and collapsed across large stimulus families rather than pre-specified trial-level hypotheses.
5. The paired `task-minus-rest` analysis uses selected scalar block summaries, so a null delta result does not rule out richer multivariate or trajectory-level reconfiguration differences.

= Conclusion

The paired `ds003474` plus `ds003478` report supports a bounded conclusion. Depressive symptom burden is visible in probabilistic-selection task geometry, especially in reachability and block-resolved `9D` dynamics, and the task-state ordering broadly echoes the prior resting-state article. But the current paired `task-minus-rest` surface is broadly null. The strongest present claim is therefore not that depression produces a large rest-to-task reconfiguration failure, but that symptom-linked structure is detectable in both states while the direct delta between them remains weak on the selected article-facing surface.

= Acknowledgements

This work emerged through structured correspondence among human and AI collaborators; large language models from OpenAI, Anthropic, and Google assisted in literature synthesis, drafting, peer review, and editorial refinement. We also gratefully acknowledge the original investigators, clinical teams, participants, and data stewards who created, curated, and shared the public datasets and metadata that made these analyses possible.

= Contact

Robin Langell - hello(at)noeticdiffusion.com
