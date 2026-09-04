#import "../depression/network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Event-First Reinforcement-Learning Geometry Across Depressive Symptom Burden",
  short-title: "Depression PST Event Geometry",
  subtitle: "A subject-anchored NeuralManifoldDynamics 2.1 event-wrapper report for ds003474, with ds003478 as secondary support",
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
    "reinforcement learning",
    "trajectory geometry",
    "event-locked EEG",
  ),
  article-type: "Research Article / Compact Empirical Report",
  abstract: [
    The first `ds003474` depression manuscript showed that depressive symptom burden was visible in task-state reachability and higher-dimensional local dynamics, but its event layer remained coarse because it collapsed broad PST families and largely emphasized speed-like summaries. We therefore rebuilt the article around a subject-anchored event-first wrapper modeled after the Parkinson auditory recall stack. Trial-local segments were reconstructed directly from `event_windows` in the existing H5 exports and summarized with trajectory-style metrics in `3D` and `9D`, including path length, peak displacement, hysteresis, recovery residual, repertoire entropy, and noetic-action terms. The primary within-subject PST contrast, `feedback_correct` versus `feedback_incorrect`, produced robust event-native effects across the cohort (`n = 122`), led by `3D` path length (`d_z = 0.323`, `q = 0.00187`), `9D` noetic-action kinetic cost (`d_z = 0.237`, `q = 0.00483`), and `3D` hysteresis area (`d_z = 0.298`, `q = 0.00591`). The co-primary certainty contrast, operationalized from available training-pair labels as high-certainty `AB/BA` versus low-certainty `EF/FE`, was not significant after FDR correction. A lower-priority phase contrast, `train` versus `test`, was very strong (`9D` transition sparsity `d_z = 0.479`, `q = 1.55e-6`; `3D` peak displacement `d_z = 0.469`, `q = 1.65e-5`) but is broader than the paper's main reinforcement-learning endpoint. Depressive symptom modulation of the event-derived contrast scores was weaker: no low-versus-high BDI or continuous BDI result survived correction, although the certainty contrast showed suggestive associations in `3D` hysteresis (`rho = 0.240`, `q = 0.0944`) and self-loop rate (`rho = 0.234`, `q = 0.0944`). The bounded conclusion is that the event-first wrapper successfully recovers strong PST-native trajectory geometry, so the earlier depression draft was not merely "measuring the wrong thing"; however, in this cohort the depressive symptom signal remains much clearer on broader task-state and resting-state geometry than on corrected event-derived reinforcement-learning contrast scores.
  ],
  data-availability: [
    Event-first manuscript outputs are stored under `articles/CLINICAL/depression_probalistic_selection/results/depression_probsel_event_first_20260609/`. Key tables include `within_subject_contrasts.csv`, `within_subject_diff_detail.csv`, `bdi_group_contrasts.csv`, `bdi_correlations.csv`, `event_first_summary.md`, and the corresponding `event_metrics/` bundle. Figures for this manuscript are stored under `articles/CLINICAL/depression_probalistic_selection/figures/` as `draft2_within_subject_contrasts.png`, `draft2_bdi_group_modulation.png`, and `draft2_bdi_correlation_modulation.png`. Secondary support for rest-state and coarse task-state summaries comes from the existing depression manuscripts and article-facing exports under `articles/CLINICAL/depression/` and `articles/CLINICAL/depression_probalistic_selection/results/`.
  ],
  competing-interests: [
    No competing interests are declared in this draft.
  ],
)

= Introduction

The first paired depression PST manuscript asked whether depressive symptom burden reorganized a broad task-versus-rest summary surface. That was a reasonable first pass, but it was not yet analogous to why the Parkinson auditory recall article became strong: the Parkinson wrapper starts from within-subject task-native event contrasts, then asks whether the clinical axis modulates those event-level effects.

This second manuscript therefore moves the center of gravity. The main question is not whether low and high BDI differ on coarse task averages, but whether the PST itself produces reliable event-native geometry and whether depressive symptom burden modulates those within-subject event-derived contrast scores.

The design is intentionally narrow. We ask four bounded questions:

1. Does a subject-anchored event wrapper recover strong within-subject PST geometry for key task contrasts?
2. Is the clearest effect the planned `feedback_correct` versus `feedback_incorrect` contrast?
3. Does depressive symptom burden modulate any of those event-derived contrast scores?
4. How should these event-first results be integrated with the already established rest-state and coarse task-state findings?

This remains a symptom-burden paper, not a diagnostic case-control claim. The point is to test whether the previous depression manuscript was mainly limited by its event measurement strategy or whether the underlying clinical modulation is itself modest.

= Methods

== Cohort

The event-first wrapper uses the same participant table as the previous depression articles under `articles/CLINICAL/depression_probalistic_selection/metadata/participants.tsv`. The PST event surface was available for all `122` subjects, and `121` had usable BDI values. The low/high clinical comparison therefore again corresponds to `BDI 0-13` (`n = 76`) versus `BDI 20-63` (`n = 30`), with the middle band retained for continuous analyses but not for the primary low/high modulation test.

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
  caption: [Table 1: Cohort summary shared across the depression PST manuscripts.]
) <tab-cohort>

As in the earlier reports, this is a young, age-compressed cohort with an imbalanced symptom distribution. That matters because even moderate event-derived clinical effects should be read as cohort-local rather than as settled depression thresholds.

== Subject-anchored PST event wrapper

The wrapper was built directly from the existing H5 exports under `data/raw/neuralmanifolddynamics_ds003474_20260609_044822/`. For each subject, the script reads `event_windows`, `event_id`, `event_start_window_index`, and `event_stop_window_index`, then reconstructs a local trajectory segment around each event in both subject-anchored `3D` and `9D` coordinates.

Each segment includes a short pre-event and post-event corridor, so the metric family can ask not only where the event sits, but how the local trajectory enters, bends through, and exits that event neighborhood. The article-local metric set includes:

1. path length
2. peak displacement
3. recovery residual
4. hysteresis area
5. entropy rate
6. irreversibility
7. transition sparsity
8. noetic-action terms
9. curvature, tortuosity, and speed

This event-first layer is therefore closer to the Parkinson wrapper than to the previous depression draft, which mostly aggregated broad event families and selected scalar summaries such as `speed_mean`.

== Event families and contrasts

The wrapper defines the following segment families from the PST labels:

1. `feedback_correct`
2. `feedback_incorrect`
3. `train_high_certainty` from `train stim: a b` and `train stim: b a`
4. `train_mid_certainty` from `train stim: c d` and `train stim: d c`
5. `train_low_certainty` from `train stim: e f` and `train stim: f e`
6. `train_any`
7. `test_any`
8. `left_response`
9. `right_response`

The primary contrast is `feedback_correct` versus `feedback_incorrect`. The planned co-primary expectancy contrast had to be operationalized from the actual event labels exposed in the H5 contract. Because the wrapper does not expose chosen stimulus identity in `A/C/E` versus `B/D/F` form, the closest auditable proxy is pair certainty: high-certainty training pairs `AB/BA` versus low-certainty training pairs `EF/FE`.

For each metric and coordinate space, within-subject contrasts were computed first. Let

$
Delta_i = y_i^R - y_i^L
$

for subject `i`. The article then tests:

1. whether `Delta_i` differs from zero across subjects using Wilcoxon signed-rank tests with BH-FDR within `(contrast_name, analysis_type)`
2. whether `Delta_i` differs between `BDI 0-13` and `BDI 20-63`
3. whether `Delta_i` correlates with continuous BDI across all valid participants

This ordering is deliberate: event geometry first, symptom modulation second.

== Secondary support layer

This manuscript does not replace the earlier depression findings. It treats them as support rather than as the main inferential target. The resting-state article showed that depressive symptom burden localized most clearly to reachability and `9D` local dynamics, especially reachability `tube_log_eig_var_mean` (`d = -0.678`, `q = 0.00296`) and `9D` MNJ `rotational_power_mean` (`d = 0.569`, `q = 0.00317`). The first PST article showed a parallel task-average ordering, led by task-state reachability (`d = -0.719`, `q = 0.0107`) and block-resolved `9D` Jacobian structure (`d = -0.778`, `q = 0.0109`). Those prior results matter here mainly as context for judging whether the new event-first layer sharpens or overturns the broader story.

= Results

== Strong event-native geometry is present

The event-first wrapper clearly recovers strong task-native structure. The primary `feedback_correct` versus `feedback_incorrect` contrast is robust across the cohort. The strongest corrected rows are:

1. `3D` path length: `d_z = 0.323`, `p = 9.86e-5`, `q = 0.00187`
2. `9D` noetic-action kinetic cost: `d_z = 0.237`, `p = 2.54e-4`, `q = 0.00483`
3. `3D` hysteresis area (`d-e` plane): `d_z = 0.298`, `p = 9.33e-4`, `q = 0.00591`
4. `9D` path length: `d_z = 0.252`, `p = 9.97e-4`, `q = 0.00947`
5. `9D` speed: `d_z = 0.300`, `p = 0.00183`, `q = 0.0116`

These effects are not huge in the Parkinson sense, but they are cleanly corrected and internally coherent. Incorrect feedback occupies a longer and slightly more kinetically costly local corridor than correct feedback, with additional support from hysteresis-like return geometry. That alone already answers one important methodological question: the previous depression draft was not failing because the PST lacked event-native geometry. The task does carry robust within-subject event structure once it is measured at the segment level.

#figure(
  image("figures/draft2_within_subject_contrasts.png", width: 100%),
  caption: [Figure 1: Top within-subject event-first PST contrasts. The planned feedback contrast is robust, while the lower-priority `train` versus `test` split is even larger but conceptually broader.]
) <fig-within>

== The planned certainty contrast is weaker than hoped

The co-primary certainty contrast, high-certainty `AB/BA` versus low-certainty `EF/FE`, did not produce corrected within-subject effects. Its best rows remained modest and non-significant after FDR correction, for example `9D` speed (`d_z = 0.183`, `q = 0.669`) and `9D` tortuosity (`d_z = 0.192`, `q = 0.669`).

This is an important negative result. The event-first redesign did not automatically make every planned reinforcement-learning endpoint strong. In the available label structure, the cleanest event-native PST signal sits more on feedback outcome and broad task-phase differences than on the high-versus-low training-pair certainty split.

== A lower-priority phase contrast is very strong

Although it was deprioritized conceptually, `train` versus `test` produced the largest event-native contrast in the wrapper. The strongest corrected rows were:

1. `9D` transition sparsity: `d_z = 0.479`, `p = 1.28e-7`, `q = 1.55e-6`
2. `9D` noetic-action potential: `d_z = -0.421`, `p = 1.64e-7`, `q = 1.55e-6`
3. `9D` peak displacement: `d_z = 0.479`, `p = 9.25e-7`, `q = 5.86e-6`
4. `3D` peak displacement: `d_z = 0.469`, `p = 8.67e-7`, `q = 1.65e-5`
5. `3D` recovery residual: `d_z = 0.458`, `p = 3.55e-5`, `q = 1.12e-4`

These large phase effects validate the wrapper technically, but they are broader than the paper's main clinical endpoint. They show that the PST strongly deforms local trajectory grammar between training and test phases; they do not by themselves imply that BDI organizes that deformation.

By contrast, `left_response` versus `right_response` was broadly null (`q` values near `0.96`), which justifies keeping response-side effects in the background.

== BDI modulation is suggestive rather than corrected

The key clinical result is more restrained. None of the event-derived BDI low-versus-high contrasts survived FDR correction, and none of the continuous BDI associations reached corrected significance either.

Still, the most suggestive clinical rows did not appear on the primary feedback contrast. They appeared on the certainty contrast:

1. low/high BDI on `train_high_certainty` versus `train_low_certainty`, `3D` noetic-action kinetic cost: `d = -0.602`, `p = 0.00845`, `q = 0.161`
2. low/high BDI on the same contrast, `3D` self-loop rate: `d = 0.500`, `p = 0.0253`, `q = 0.240`
3. continuous BDI on the same contrast, `3D` hysteresis area (`d-e` plane): `rho = 0.240`, `p = 0.00813`, `q = 0.0944`
4. continuous BDI on the same contrast, `3D` self-loop rate: `rho = 0.234`, `p = 0.00993`, `q = 0.0944`

The primary feedback contrast showed weaker symptom ordering. Its top clinical rows were `9D` hysteresis area (`d-e` plane) for the low/high split (`d = -0.443`, `q = 0.378`) and the same metric for continuous BDI (`rho = -0.235`, `q = 0.182`).

The safest interpretation is therefore not that BDI strongly reorganizes all task-native reinforcement-learning event geometry. It is that symptom-linked modulation may be present in certainty-sensitive return-path and recurrence metrics, but the evidence remains only suggestive on the current corrected surface.

#figure(
  image("figures/draft2_bdi_group_modulation.png", width: 100%),
  caption: [Figure 2: Top low-versus-high BDI modulation rows. No event-derived contrast survives FDR correction, but the certainty contrast shows the clearest raw clinical separation.]
) <fig-bdi-group>

#figure(
  image("figures/draft2_bdi_correlation_modulation.png", width: 100%),
  caption: [Figure 3: Top continuous-BDI modulation rows. The strongest suggestive associations again localize to the certainty contrast rather than to the primary feedback contrast.]
) <fig-bdi-corr>

== Relation to the broader depression story

Taken together with the earlier articles, the depression story becomes sharper rather than larger.

First, the event-first wrapper shows that the PST itself contains strong local event geometry. Second, the older task-average and resting-state articles still carry the clearest corrected symptom signal: rest-state reachability and `9D` MNJ remain strong, and the first PST draft already showed a matching task-average reachability / block-MNJ ordering. Third, the new wrapper does *not* show a large corrected BDI modulation of the event-derived contrast scores.

That pattern matters. If the earlier depression paper had simply been measuring the task in the wrong way, the event-first rewrite should have produced clearly corrected symptom effects on the core PST contrasts. It improved the task-native measurement substantially, but the symptom effect itself remained comparatively modest.

= Discussion

This second article changes what can be defended.

The good news is methodological. A subject-anchored event wrapper is the right language for the PST. It reveals robust within-subject feedback and phase geometry that the broader first draft necessarily blurred. In that sense, the event-first redesign was worth doing and should be preferred for future perturbational or trial-local depression analyses.

The clinical news is more limited. Even after giving the depression article a more Parkinson-like event wrapper, the BDI modulation of those event-derived contrasts remained mostly sub-threshold after correction. That means the weaker depression result cannot be blamed only on a coarse event summary. Part of the answer is likely biological or dataset-specific: depressive symptom burden in this young cohort seems more visible in broader reachability and higher-order state geometry than in large event-by-event reinforcement-learning contrast scores.

This does not make the event layer useless. The certainty contrast now points to a plausible follow-up hypothesis: symptom burden may modulate how trajectories return or recur after uncertain training events, especially in `3D` hysteresis and repertoire-style metrics. But that is still a plausible interpretation, not yet a corrected result.

= Limitations

This manuscript has several important limits.

1. The certainty endpoint had to be operationalized from pair labels `AB/CD/EF` because the event wrapper does not expose chosen stimulus identity in direct `A/C/E` versus `B/D/F` form.
2. The trajectory metric family is article-local and exploratory rather than part of the frozen standard paper-facing export contract.
3. The cohort is young, single-site, and symptom-weighted rather than diagnostically balanced.
4. The strongest event-native effect outside feedback was `train` versus `test`, which is real but broader than the paper's main reinforcement-learning interpretation.
5. No event-derived BDI modulation survived FDR correction, so any clinical reading beyond "suggestive" would overstate the evidence.

= Conclusion

The event-first rewrite answers the methodological question more clearly than the clinical one. `ds003474` does contain strong subject-anchored PST trajectory geometry, especially for `feedback_correct` versus `feedback_incorrect` and for the broader `train` versus `test` phase split. So the original depression PST paper was not simply measuring the wrong object. But once depressive symptom burden is layered onto those event-derived contrast scores, the corrected clinical effects remain weak. The strongest defended depression claim therefore stays with the broader rest-state and task-average geometry layers, while the event-first wrapper contributes a narrower, more cautious extension: symptom burden may modulate certainty-sensitive return-path geometry, but that hypothesis still needs stronger confirmation.

= Acknowledgements

This work emerged through structured correspondence among human and AI collaborators; large language models from OpenAI, Anthropic, and Google assisted in literature synthesis, drafting, peer review, and editorial refinement. We also gratefully acknowledge the original investigators, clinical teams, participants, and data stewards who created, curated, and shared the public datasets and metadata that made these analyses possible.

= Contact

Robin Langell - hello(at)noeticdiffusion.com
