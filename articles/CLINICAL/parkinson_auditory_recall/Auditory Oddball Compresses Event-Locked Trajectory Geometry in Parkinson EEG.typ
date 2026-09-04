#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Auditory Oddball Compresses Event-Locked Trajectory Geometry in Parkinson EEG",
  short-title: "Parkinson Auditory Recall",
  subtitle: "A NeuralManifoldDynamics analysis of ds004574 oddball subtype structure and supportive Parkinson-control geometry",
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
    "reachability",
  ),
  article-type: "Research Article",
  abstract: [
    We analyzed the NeuralManifoldDynamics `ds004574` oddball bundle (`146` subjects; `98` Parkinson, `48` controls) to ask whether subtype-aware auditory events occupy a distinct noetic geometry and whether that event structure aligns with Parkinson-control differences. Two linked layers were used. A standard `ndt-analysis` path quantified global `MNPS 3D`, `MNPS 9D`, Jacobian, and reachability summaries. An article-local wrapper then compared subject-level event-centered trajectory metrics across `standard`, `auditory oddball`, and `visual oddball` windows using subject-anchored `3D` and `9D` coordinates. The dominant result was event-locked rather than disease-locked. Relative to the pooled non-auditory mean, auditory windows showed sharply increased transition sparsity and reduced entropy rate, path length, and peak displacement (`3D transition_sparsity d = 3.376, q = 4.05e-25`; `9D entropy_rate d = -2.941, q = 4.14e-25`; `9D peak_displacement d = -2.096, q = 4.14e-25`). The strongest phase-localized row was `9D` arrowcue entropy rate for `standard vs auditory` (`d = -4.731, q = 3.97e-25`). These effects remained strong after excluding subjects with residual `raw_nan_onset_sec` provenance and within both diagnostic groups separately. By contrast, `auditory vs visual` produced no BH-FDR-positive rows, and no event-locked `Control vs Parkinson` row survived BH-FDR. The supportive disease layer instead appeared in the standard global exports, where Parkinson subjects showed lower `3D m_median` (`d = -0.602, q = 0.0135`) and higher reachability `tube_q_ratio_h4_mean` (`d = 0.557, q = 0.0308`). These findings support a bounded conclusion: in this bundle, oddball subtype structure dominates the event-locked geometry, while Parkinson-control differences remain present but smaller and more global.
  ],
  author-summary: [
    This manuscript asks a simple but important question: when we know which oddball subtype each EEG window belongs to, does the auditory oddball occupy a different state-space geometry from the rest of the run, and does Parkinson disease change that geometry further? The answer in `ds004574` is layered. The strongest and most reproducible effect is not a disease biomarker but an event-structure effect: auditory windows are shorter, less entropic, and more transition-sparse than standard windows, especially around the arrowcue phase. Those differences survive residual-label exclusion and are present in both controls and Parkinson patients. The disease signal is smaller and sits in the global layer instead, with lower `m` and higher reachability `q_ratio` in Parkinson. The most conservative interpretation is therefore that subtype-aware event provenance is essential for understanding this dataset, while Parkinson-control differences add a weaker but still BH-FDR-positive global geometry shift on top of that event structure.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted in the submission version.],
  data-availability: [
    Data were analyzed from the local NeuralManifoldDynamics export at `data/raw/neuralmanifolddynamics_ds004574_20260602_062756`. Manuscript-facing outputs are stored under `articles/CLINICAL/parkinson_auditory_recall/results/parkinson_auditory_recall_20260602`, including `standard_analysis/`, `event_metrics/`, `event_contrasts.csv`, `article_metric_ranking.csv`, `selected_metric_robustness.csv`, and the supplementary summary notes. Article-local code is stored under `articles/CLINICAL/parkinson_auditory_recall/src/`.
  ],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

= Introduction

Parkinson EEG is often summarized through spectral slowing, beta imbalance, or canonical event-related components. Those views remain useful, but they also compress the signal into relatively static descriptors. The more specific opportunity in `ds004574` is that the processed bundle preserves subtype-aware oddball provenance at the window level. That means the question is no longer only whether Parkinson subjects differ from controls, but whether the event geometry itself changes when the run moves from `standard` to `auditory oddball` or `visual oddball`.

This distinction matters because the dataset combines three properties that are analytically unusual in the current repository. First, it contains a moderate clinical cohort (`146` subjects) rather than a tiny proof-of-concept sample. Second, the bundle exports subject-anchored `3D`, `9D`, and Jacobian layers with numerically healthy coverage across the cohort. Third, the behavior-enriched staging promotes oddball subtype labels into the H5 contract, allowing event-centered trajectory geometry to be compared directly across `standard`, `auditory`, and `visual` windows.

The present manuscript is therefore event-first rather than diagnosis-first. The primary question is whether auditory oddball windows occupy a distinct trajectory regime relative to the rest of the run. Parkinson-control contrasts remain important, but here they function as a supportive global layer rather than as the only endpoint. This framing is deliberate because the event surface is the strongest new information in the bundle contract, whereas diagnosis is inherited from the participant table and has to compete with large within-run subtype structure.

#netn-box(title: [Core question])[
  In the subtype-aware `ds004574` oddball bundle, does the auditory oddball occupy a distinct event-locked trajectory geometry relative to standard and visual windows, and if so, does Parkinson disease add a smaller but interpretable global geometry shift on top of that event structure?
]

= Cohort and design

The analyzed bundle was `ds004574`, processed through NeuralManifoldDynamics into a local export containing `146` subject H5 files. The cohort structure is straightforward: `98` Parkinson subjects and `48` controls, all with `condition = not_applicable` and `task = oddball`. The bundle uses a behavior-enriched staging so that subtype-aware oddball labels are preserved in `labels/raw_*` arrays.

The key methodological consequence is that the article does not use `labels/stage` as a trial-state annotation. In this dataset the stage field is largely `-1` and was not promoted into a meaningful event surface. All event-related inference is therefore anchored to `raw_standard_*`, `raw_oddball_auditory_*`, and `raw_oddball_visual_*` labels, while `raw_nan_onset_sec` is treated as residual unmatched provenance and excluded from the event wrapper by construction.

#figure(
  kind: table,
  table(
    columns: (2.55fr, 1.15fr, 1.15fr, 1.6fr),
    align: left,
    inset: 5pt,
    table.header([*Design item*], [*Control*], [*Parkinson*], [*Bundle status*]),
    [Unique subjects], [48], [98], [`146` total H5 files],
    [Task label], [`oddball`], [`oddball`], [subtype-aware behavior-enriched staging],
    [Condition label], [`not_applicable`], [`not_applicable`], [single-condition clinical cohort],
    [Coordinate contract], [subject_anchored], [subject_anchored], [no cohort-anchor layer in bundle],
    [Main event surface], [`standard`, `auditory`, `visual`], [`standard`, `auditory`, `visual`], [`raw_*` labels used directly],
    [Regional outputs], [none], [none], [global layers only],
    [ComBat normalization], [none], [none], [disabled in run manifest],
  ),
  caption: [Cohort and bundle design summary for the `ds004574` Parkinson auditory oddball analysis.]
) <tab-design>

= Analysis framework

Two linked analysis layers were run.

1. *Standard global layer.* `ndt-analysis` exported global `MNPS 3D`, `MNPS 9D`, Jacobian, reachability, `trajectory_dynamics`, and `tier2_jacobian` summaries, followed by `Control vs Parkinson` contrasts with BH-FDR correction.
2. *Event-locked wrapper layer.* Article-local code used the same subject-anchored coordinates but replaced stage logic with subtype-aware `raw_*` event blocks. Each block was summarized in local windows with `2` pre-event and `3` post-event windows.

The wrapper quantified path length, tortuosity, peak displacement, entropy rate, irreversibility, entropy production, hysteresis, recovery residual, and noetic-action summaries in both `3D` and `9D`. Full metric definitions and provenance are reported in `S1`.

The inferential hierarchy was also split deliberately. The primary contrasts were within-subject auditory comparisons, especially `auditory` versus `standard` and `auditory` versus pooled non-auditory `other_mean`. Supportive contrasts were `Control vs Parkinson` comparisons in the standard global layer and, secondarily, in the event wrapper. Full tables are moved to `S2`, and robustness follow-up is reported in `S3`.

= Results

== Auditory oddball geometry dominates the event layer

The clearest result in the entire manuscript is a large within-subject event-structure effect. Auditory windows are markedly more compact and less entropic than the pooled non-auditory mean. The strongest pooled non-auditory anchors were:

- higher `3D transition_sparsity` in auditory windows,
- lower `9D entropy_rate`,
- lower `9D peak_displacement`.

These are all large effects with extremely small BH-FDR values. In practical terms, the auditory oddball occupies a shorter and more canalized event path than the rest of the run.

#figure(
  kind: table,
  table(
    columns: (2.05fr, 1.45fr, 1.0fr, 1.0fr, 0.85fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Comparison*], [*Left med*], [*Right med*], [*`d`*], [*BH-FDR `q`*]),
    [`3D transition_sparsity`], [`other_mean` vs `auditory_all`], [`0.8767`], [`0.9514`], [`+3.376`], [`4.05e-25`],
    [`9D entropy_rate`], [`other_mean` vs `auditory_all`], [`0.7881`], [`0.4332`], [`-2.941`], [`4.14e-25`],
    [`9D peak_displacement`], [`other_mean` vs `auditory_all`], [`2.498`], [`1.512`], [`-2.096`], [`4.14e-25`],
    [`9D entropy_rate`], [`standard_arrowcue` vs `auditory_arrowcue`], [`1.127`], [`0.432`], [`-4.731`], [`3.97e-25`],
  ),
  caption: [Primary event-facing article anchors. Positive `d` means the right-hand auditory quantity is larger; negative `d` means it is smaller.]
) <tab-primary-auditory>

The phase-localized result strengthens this reading. The strongest single row in the entire ranking was `9D` arrowcue entropy rate for `standard_arrowcue vs auditory_arrowcue` (`d = -4.731`, `q = 3.97e-25`), which implies that the entropy contraction is not only a subtype-collapsed average but is especially strong around the arrowcue epoch.

== The dominant auditory contrast is against standard, not visual

The event layer is not equally separated across all subtype pairs. `Auditory vs standard` and `auditory vs pooled other_mean` produced many large retained rows, but `auditory vs visual` produced no BH-FDR-positive rows. That matters because it bounds the interpretation. The main event geometry difference in this bundle is not a generic auditory-versus-everything effect; it is driven primarily by the gap between standard windows and the auditory oddball regime.

This asymmetry is also why the pooled `other_mean` contrast remains article-worthy despite the null `auditory vs visual` result: the standard arm contributes a large share of the non-auditory baseline, and the auditory-standard separation is both strong and phase-consistent.

== Parkinson-control effects remain present but are smaller and more global

No event-locked `Control vs Parkinson` row survived BH-FDR in the wrapper. The disease signal instead emerged in the standard global exports. Parkinson subjects showed lower global `3D m_median` and higher reachability `q_ratio` summaries, indicating a smaller but consistent global geometry shift layered on top of the much larger event-structure effect.

#figure(
  kind: table,
  table(
    columns: (2.15fr, 1.0fr, 1.0fr, 0.85fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Control med*], [*Parkinson med*], [*`d`*], [*BH-FDR `q`*]),
    [`global 3D m_median`], [`0.0347`], [`0.0201`], [`-0.602`], [`0.0135`],
    [`reachability tube_q_ratio_h4_mean`], [`0.2474`], [`0.2821`], [`+0.557`], [`0.0308`],
    [`reachability q_ratio_h2_median`], [`0.5177`], [`0.5469`], [`+0.552`], [`0.0308`],
    [`adaptive collapse q_ratio_h4`], [`0.2312`], [`0.2752`], [`+0.518`], [`0.0200`],
  ),
  caption: [Supportive `Control vs Parkinson` anchors from the standard global layer.]
) <tab-supportive-group>

The practical consequence is that diagnosis and event subtype live on different effect scales in this dataset. Event subtype dominates the event-locked geometry, while diagnosis is visible in the global summaries but does not produce a comparably strong event-specific wrapper signature at the current threshold.

= Discussion

This manuscript supports three main conclusions.

First, subtype-aware oddball provenance fundamentally changes how the dataset should be read. Once `raw_*` labels are used directly, auditory windows occupy a sharply more canalized trajectory regime than standard windows. The dominant features of that regime are lower entropy rate, shorter paths, smaller displacement, and higher transition sparsity.

Second, the strongest event result is not sufficient by itself to claim a Parkinson-specific auditory biomarker. The same auditory-versus-standard direction survives in both controls and Parkinson subjects, and `auditory vs visual` does not survive BH-FDR. The most responsible reading is therefore that the primary event effect reflects a strong subtype geometry built into the task, not a disease-only phenomenon.

Third, Parkinson-control structure is still present, but it is subtler and more global. Lower `m_median` and higher reachability `q_ratio` values in Parkinson suggest reduced global mobility together with a shifted short-horizon transport regime. Those effects are much smaller than the within-subject subtype contrasts, but they are BH-FDR-positive and robust to exclusion of `sub-112` and mild winsorization.

The resulting picture is layered rather than singular. The bundle is most informative when event structure and diagnosis are treated as different scales of geometry rather than as competing explanations for one dominant metric.

= Limitations

1. The bundle exposes only subject-anchored global layers, so there is no regional localization analysis in the current manuscript.
2. `labels/stage` is intentionally not used as an event surface in this dataset, so all event inference depends on the behavior-enriched `raw_*` labels.
3. `Auditory vs visual` did not yield BH-FDR-positive rows, which means the primary event story is mainly `auditory vs standard`.
4. The event wrapper is article-local code, not yet a frozen shared repository standard.
5. The bundle is not ComBat-normalized and provides no cohort-anchor layer or external validation cohort.

= Conclusion

The `ds004574` Parkinson oddball bundle is dominated by a strong event-structure effect: auditory windows are shorter, less entropic, and more transition-sparse than standard windows, especially at arrowcue. Parkinson-control differences remain visible, but they are smaller and appear in the global `m` and reachability layers rather than as BH-FDR-positive event-locked wrapper rows. The most conservative conclusion is therefore that subtype-aware event provenance is the main analytic advance in this dataset, while Parkinson-control geometry forms a secondary but reproducible global layer on top of that event structure.
