#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Auditory Oddball Occupies a Compressed Event-Locked Trajectory Regime in a Behavior-Enriched EEG Cohort",
  short-title: "Auditory Oddball Geometry",
  subtitle: "A NeuralManifoldDynamics re-framing of `ds004574` with Parkinson stratification as a secondary layer",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "auditory oddball",
    "EEG",
    "trajectory geometry",
    "event-locked dynamics",
    "NeuralManifoldDynamics",
    "Parkinson disease",
  ),
  article-type: "Research Article",
  abstract: [
    We analyzed the behavior-enriched NeuralManifoldDynamics `ds004574` oddball bundle (`146` subjects; `98` Parkinson, `48` controls) to ask a narrower question than the current disease-first framing allows: do subtype-aware auditory events occupy a distinct event-locked trajectory regime, regardless of diagnosis? The primary analysis therefore used article-local event wrappers on subject-anchored `3D` and `9D` coordinates, with `auditory vs standard` as the main contrast and Parkinson-control structure treated as a secondary layer. The dominant result was a large auditory contraction rather than a disease-specific event effect. Relative to `standard`, auditory windows showed markedly lower entropy rate, shorter path length, smaller peak displacement, and higher transition sparsity, with the strongest row at `9D standard_arrowcue vs auditory_arrowcue entropy_rate` (`d = -4.731, q = 3.97e-25`). Auditory versus visual yielded no BH-FDR-positive rows, and no event-locked `Control vs Parkinson` row survived BH-FDR. A smaller diagnosis-related signal remained visible only in the standard global exports, where Parkinson subjects showed lower `3D m_median` (`d = -0.602, q = 0.0135`) and higher reachability `tube_q_ratio_h4_mean` (`d = 0.557, q = 0.0308`). The most conservative conclusion is therefore event-first: in this bundle, behavior-enriched oddball provenance reveals a sharply compressed auditory trajectory regime that dominates the event surface, while Parkinson contributes a secondary global geometry shift rather than the main event-locked story.
  ],
  author-summary: [
    This draft takes the strongest result in the bundle seriously and lets it drive the paper. The key finding is not that Parkinson patients show a uniquely large auditory oddball signature. Instead, the key finding is that once subtype-aware `raw_*` labels are used directly, auditory oddball windows occupy a shorter, less entropic, and more transition-sparse trajectory regime than standard windows across the cohort. The strongest separation localizes to the arrowcue epoch. Parkinson-control differences are still present, but they are smaller and appear in the global layer rather than as BH-FDR-positive event-locked contrasts. That makes the better-focused paper a manuscript about event geometry unlocked by behavior-enriched provenance, with diagnosis treated as an important but secondary stratification.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted in the submission version.],
  data-availability: [
    Data were analyzed from the local NeuralManifoldDynamics export at `data/raw/neuralmanifolddynamics_ds004574_20260602_062756`. Manuscript-facing outputs are stored under `articles/CLINICAL/parkinson_auditory_recall/results/parkinson_auditory_recall_20260602`, including `standard_analysis/`, `event_metrics/`, `event_contrasts.csv`, `article_metric_ranking.csv`, `selected_metric_robustness.csv`, and the supplementary summary notes. Article-local code is stored under `articles/CLINICAL/parkinson_auditory_recall/src/`.
  ],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

= Introduction

The `ds004574` bundle is unusually valuable not because it is a Parkinson cohort alone, but because it preserves subtype-aware oddball provenance at the event level. That behavior-enriched contract changes the scientific question. Instead of asking only whether Parkinson subjects differ from controls, the more defensible first question is whether the run itself contains a distinct auditory event geometry once `standard`, `auditory oddball`, and `visual oddball` windows are separated directly.

That distinction matters because the event-facing signal is much larger than the disease-facing signal in the current results. The strongest retained rows are all within-subject subtype contrasts, especially `auditory vs standard`, while the event-locked `Control vs Parkinson` layer remains null after BH-FDR correction. A disease-first article therefore risks overselling the weaker part of the dataset and understating the strongest analytic advance, namely that behavior-enriched provenance exposes a sharply compressed auditory trajectory regime.

This draft is written around that narrower and stronger claim. Parkinson disease remains relevant, but mainly as context, stratification, and a secondary global comparison. The paper's main contribution is that subtype-aware event provenance reorganizes how the dataset should be interpreted.

#netn-box(title: [Core question])[
  In the behavior-enriched `ds004574` oddball bundle, do auditory oddball windows occupy a distinct event-locked trajectory geometry relative to standard and visual windows, and does diagnosis remain secondary once that event structure is modeled directly?
]

= Cohort and bundle rationale

The analyzed bundle contains `146` subject H5 files (`98` Parkinson, `48` controls), all from an oddball task processed into subject-anchored `3D`, `9D`, Jacobian, and reachability layers. The defining feature for the present draft is not the cohort label alone, but the fact that behavior-enriched staging preserved subtype-aware `raw_*` labels in the exported H5 contract.

This has one immediate methodological consequence: `labels/stage` is not the event surface of interest here. In this dataset, stage is largely non-informative for trial semantics, whereas `raw_standard_*`, `raw_oddball_auditory_*`, and `raw_oddball_visual_*` encode the meaningful event classes. Residual `raw_nan_onset_sec` labels are therefore treated as unmatched provenance and excluded from the article-local event wrapper.

#figure(
  kind: table,
  table(
    columns: (2.55fr, 1.15fr, 1.15fr, 1.6fr),
    align: left,
    inset: 5pt,
    table.header([*Design item*], [*Control*], [*Parkinson*], [*Bundle status*]),
    [Unique subjects], [48], [98], [`146` total H5 files],
    [Task label], [`oddball`], [`oddball`], [behavior-enriched subtype-aware staging],
    [Condition label], [`not_applicable`], [`not_applicable`], [single-condition clinical cohort],
    [Coordinate contract], [subject_anchored], [subject_anchored], [global `3D` and `9D` exports available],
    [Primary event surface], [`standard`, `auditory`, `visual`], [`standard`, `auditory`, `visual`], [`raw_*` labels used directly],
    [Residual caveat], [possible], [possible], [`raw_nan_onset_sec` excluded from wrapper],
    [Regional outputs], [none], [none], [global layers only],
  ),
  caption: [Cohort and bundle design summary for the refocused `ds004574` auditory oddball manuscript.]
) <tab-design>

= Analysis framework

The analysis was deliberately split into a primary and a secondary layer.

1. *Primary event layer.* Article-local event wrappers quantified trajectory geometry in subject-anchored `3D` and `9D` coordinates using subtype-aware `raw_*` labels with `2` pre-event and `3` post-event windows. The prespecified manuscript anchors were `auditory vs standard`, followed by `auditory vs visual` as a specificity bound.
2. *Secondary diagnosis layer.* Standard global `ndt-analysis` exports were retained to ask whether Parkinson-control differences persisted after the event story had already been established.

The wrapper summarized path length, tortuosity, peak displacement, entropy rate, irreversibility, entropy production, hysteresis, recovery residual, and noetic-action summaries. Full definitions and provenance can remain in `S1`, while complete tables and QC notes can remain in `S2` and `S3`.

= Results

== Auditory oddball windows occupy a compact low-entropy regime

The main result is a large within-subject separation between auditory and standard windows. Across both `3D` and `9D`, auditory windows are shorter, less entropic, less displaced, and more transition-sparse than standard windows. This is the strongest signal in the dataset and should form the backbone of the paper.

#figure(
  kind: table,
  table(
    columns: (2.1fr, 1.45fr, 1.0fr, 1.0fr, 0.85fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Comparison*], [*Left med*], [*Right med*], [*`d`*], [*BH-FDR `q`*]),
    [`3D entropy_rate`], [`standard_all` vs `auditory_all`], [--], [--], [`-4.012`], [`3.97e-25`],
    [`9D entropy_rate`], [`standard_all` vs `auditory_all`], [--], [--], [`-3.913`], [`3.97e-25`],
    [`3D transition_sparsity`], [`standard_all` vs `auditory_all`], [--], [--], [`+3.461`], [`3.97e-25`],
    [`9D peak_displacement`], [`standard_all` vs `auditory_all`], [--], [--], [`-2.261`], [`3.97e-25`],
    [`3D path_length`], [`standard_all` vs `auditory_all`], [--], [--], [`-1.898`], [`3.97e-25`],
  ),
  caption: [Primary manuscript anchors for the refocused paper. Positive `d` means the right-hand auditory quantity is larger; negative `d` means it is smaller.]
) <tab-auditory-standard>

In practical terms, the auditory oddball does not merely perturb the run. It pushes the subject-anchored trajectory into a more canalized regime with fewer effective transitions and a lower local repertoire entropy. Those features are clearer and more reproducible than any event-locked diagnosis effect in the same dataset.

== The strongest separation localizes to the arrowcue epoch

The subtype effect is not only a pooled average. It becomes strongest around the arrowcue phase, where auditory windows show the largest retained contraction in entropy rate and a parallel increase in transition sparsity. That localization gives the manuscript a sharper mechanistic center than a simple global subtype average.

#figure(
  kind: table,
  table(
    columns: (2.15fr, 1.55fr, 0.9fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Comparison*], [*`d`*], [*BH-FDR `q`*]),
    [`9D entropy_rate`], [`standard_arrowcue` vs `auditory_arrowcue`], [`-4.731`], [`3.97e-25`],
    [`3D transition_sparsity`], [`standard_arrowcue` vs `auditory_arrowcue`], [`+4.211`], [`3.97e-25`],
    [`3D entropy_rate`], [`standard_arrowcue` vs `auditory_arrowcue`], [`-4.074`], [`3.97e-25`],
    [`9D path_length`], [`standard_arrowcue` vs `auditory_arrowcue`], [`-2.461`], [`3.97e-25`],
  ),
  caption: [Arrowcue-localized anchors. The strongest retained row in the entire ranking is the `9D` arrowcue entropy contraction.]
) <tab-arrowcue>

This arrowcue concentration is useful rhetorically and analytically. It shows that the auditory contraction is not a vague task-average phenomenon but a phase-localized event geometry effect that survives very stringent multiple-testing correction.

== Visual oddball bounds the claim

The manuscript should also be explicit about what the data do *not* support. `Auditory vs visual` produced no BH-FDR-positive rows. That null result narrows the interpretation in a productive way. The auditory regime is clearly separated from `standard`, but it is not cleanly separated from every non-auditory event class in the bundle.

That bound improves the article rather than weakening it. It turns the claim from "auditory events are globally unique" into the more precise statement that the primary event geometry shift in this bundle is the `standard -> auditory` transition, with visual windows lying closer to auditory than standard on the wrapper metrics that dominate the ranking.

== Diagnosis is secondary and largely global

Once the event layer is modeled directly, Parkinson-control differences remain smaller and move into the global summaries. No event-locked wrapper row survives BH-FDR for `Control vs Parkinson`, but the standard exports still show lower `m` and higher reachability `q_ratio` in Parkinson. These effects are worth reporting, yet they no longer need to carry the manuscript.

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
  ),
  caption: [Secondary diagnosis-facing anchors from the standard global layer.]
) <tab-global-diagnosis>

The more disciplined framing is therefore layered: event subtype dominates the event-locked geometry, while diagnosis contributes a smaller and more global deformation of the subject-level state space.

= Discussion

This refocused manuscript makes a stronger promise and asks the data to defend only what they clearly support. The strongest and cleanest result in `ds004574` is that subtype-aware event provenance exposes a compressed auditory oddball regime. That regime is expressed as lower entropy rate, shorter path length, smaller displacement, and higher transition sparsity, with the sharpest separation at arrowcue.

That framing is preferable to a disease-first title for three reasons. First, it aligns the manuscript with the largest observed effects rather than with the weaker secondary layer. Second, it highlights the actual analytic advance in the bundle, namely that behavior-enriched `raw_*` provenance becomes a meaningful event surface for NeuralManifoldDynamics. Third, it avoids overstating a Parkinson-specific auditory biomarker when the event-locked diagnosis contrasts are null after BH-FDR correction.

Parkinson disease still belongs in the paper, but in a different role. It can serve as a secondary stratification, a global comparison, and a motivation for why subtype-aware event analysis matters in a clinical cohort. What it should not do in this draft is define the paper's primary causal or inferential identity.

The broader methodological lesson is that bundle semantics matter. When enriched event provenance is present, the most informative question may shift from cross-subject disease classification to within-run event geometry. In `ds004574`, that shift produces a paper that is both more conservative and more convincing.

= Limitations

1. The bundle exposes subject-anchored global layers only, so the present draft cannot localize the auditory effect to specific regions or source-space networks.
2. Event inference depends on behavior-enriched `raw_*` labels rather than a canonical stage-coded trial surface.
3. Residual `raw_nan_onset_sec` provenance remains in a subset of subjects and must continue to be excluded or bounded in sensitivity analyses.
4. `Auditory vs visual` does not survive BH-FDR, so the event claim is best stated as `standard vs auditory` rather than as a universal auditory specificity result.
5. The event wrapper remains article-local code rather than a frozen shared repository standard.

= Conclusion

The better-focused article in this folder is not primarily a Parkinson biomarker paper. It is a paper about how subtype-aware oddball provenance reveals a sharply compressed auditory event geometry in `ds004574`. Auditory windows are shorter, less entropic, and more transition-sparse than standard windows, especially at arrowcue, while Parkinson-control differences remain smaller and largely global. That event-first framing fits the observed effect structure better and gives the manuscript a cleaner, more defensible center.
