#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Task Context Determines How Much Parkinson Disease-State Geometry Is Recoverable",
  short-title: "Task-Dependent Parkinson Geometry",
  subtitle: "A mixed-contract NeuralManifoldDynamics analysis of ds003509 and ds003506",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "Parkinson disease",
    "task context",
    "Simon conflict",
    "reinforcement learning",
    "EEG",
    "NeuralManifoldDynamics",
    "trajectory geometry",
  ),
  article-type: "Research Article",
  abstract: [
    We asked a narrower question than a generic Parkinson cognitive-workload study: under one fixed mixed-contract NeuralManifoldDynamics policy, how much disease-state geometry is recoverable in different task contexts? We analyzed two Parkinson EEG bundles with parallel repeated-session cohort structures (`28` controls, `28` Parkinson `OFF`, `28` Parkinson `ON` per dataset): `ds003509` (Simon conflict) and `ds003506` (reinforcement learning). Disease-state contrasts against controls were treated as primary in `cohort_anchored` space, while the paired `OFF vs ON` medication contrast remained primary in `subject_anchored` space. Recoverability differed sharply by task. In `ds003509`, the standard layer retained `56` primary rows at `BH-FDR q < 0.05` and `108` at `q < 0.1`, led by regional `9D` disease-state rows such as parietal-occipital `d_s_mean` (`d = 1.166`, `q = 0.018`) and central `d_n_std` (`d = -1.129`, `q = 0.018`) for `Control vs Parkinson OFF`, together with broad `e_m` and `d_s` separation for `Control vs Parkinson ON`. Simon conflict also carried a secondary dynamical branch, with `6` Jacobian/collapse-like rows and `32` reachability-like rows at `q < 0.1`, especially `q_ratio_h4` (`d = -0.632`, `q = 0.034`) and `persistence_log_eig_var_median` (`d = -0.919`, `q = 0.040`) in the `Control vs Parkinson ON` contrast. In `ds003506`, the standard layer retained `11` rows at `q < 0.05` and `31` at `q < 0.1`, led mainly by classical relative alpha (`d = 1.113`, `q = 0.024`) together with a smaller Jacobian branch including `mdr_mean` (`d = 0.835`, `q = 0.033`) for `Control vs Parkinson OFF` and `aci_mean` (`d = 0.835`, `q = 0.047`) for `Control vs Parkinson ON`. Reinforcement learning retained a modest Jacobian-like branch (`10` rows at `q < 0.1`) and no reachability row at that threshold, indicating a narrower and partly classical-EEG-facing signal rather than a broad geometry-specific win. The paired medication branch was weak in both datasets, and no event-locked wrapper row survived `q < 0.1` in either task. These results support a bounded conclusion: task context determines how much Parkinson disease-state geometry is recoverable, with Simon conflict preserving a broad cohort-level geometric signal and reinforcement learning preserving a thinner, partly classical signal under the same analysis contract.
  ],
  author-summary: [
    This manuscript asks a contrast question: when the same mixed-contract analysis policy is applied to two Parkinson task contexts, how much disease-state geometry remains recoverable? The answer is task dependent. The Simon conflict dataset shows broad disease-state structure against controls in the standard geometric layer and retains a secondary Jacobian/reachability branch, while the reinforcement-learning dataset shows a much thinner OFF-state inventory that overlaps more strongly with classical alpha-sensitive EEG summaries. In both datasets the paired medication branch is weak, and the event-locked wrapper fails to produce any retained row at `q < 0.1`. The safest reading is therefore not that Parkinson has one generic cognitive-workload geometry, but that different tasks preserve different amounts of recoverable disease-state structure under the same analysis contract.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted in the submission version.],
  data-availability: [
    Data are analyzed from the local NeuralManifoldDynamics exports `data/raw/neuralmanifolddynamics_ds003509_20260608_151832` and `data/raw/neuralmanifolddynamics_ds003506_20260608_163629`. Manuscript-facing outputs are written under `articles/CLINICAL/parkinson_cognitive_workload_ON_OFF/results/parkinson_simon_conflict_20260608` and `articles/CLINICAL/parkinson_cognitive_workload_ON_OFF/results/parkinson_reinforcement_learning_20260608`, including `analysis_summary.md`, `primary_standard_contrasts.csv`, `primary_event_contrasts.csv`, wrapper summaries, stamped parquets, and pipeline manifests. Article-facing violin panels are stored under `articles/CLINICAL/parkinson_cognitive_workload_ON_OFF/figures/violin/`.
  ],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

= Introduction

This article does not ask whether Parkinson disease has one generic cognitive-workload geometry. It asks a narrower question: under one fixed mixed-contract NeuralManifoldDynamics policy, how much disease-state geometry is recoverable in different task contexts? The key opportunity is that two Parkinson task datasets share the same repeated-session cohort structure while differing in cognitive demand: `ds003509` probes conflict control through the Simon paradigm, whereas `ds003506` probes adaptive control and outcome learning through a reinforcement-learning task. Because both bundles expose explicit `subject_anchored` and `cohort_anchored` coordinate layers, the manuscript can ask the same disease-state and paired medication questions on two different task surfaces.

That framing is motivated by the broader Parkinson EEG literature. Group differences in Parkinson disease have been reported in resting-state slowing, altered alpha/beta structure, event-related attention and novelty processing, and changes in dynamic coordination rather than one single task-invariant electrophysiological signature.@wang2020eegreview @seer2016erp @oldedubbelink2013slowing @melgari2014ldopa @sorrentino2021flexible Simon conflict and reinforcement-learning paradigms therefore should not be treated as interchangeable assays. They both tax cognitive control, but they emphasize partially different mixtures of conflict monitoring, action selection, outcome evaluation, and medication-sensitive oscillatory structure.

The main comparison is therefore informative even if one task becomes the stronger positive case and the other mainly bounds the generality of that result. In this article, Simon conflict is allowed to function as the geometry-rich assay if that is where the disease-state signal survives, while reinforcement learning is allowed to function as the narrower contrast case if its strongest rows prove thinner, more OFF-dominant, or more classically shareable. Population-dynamics and manifold-style summaries motivate asking this question at the level of recovered low-dimensional state structure rather than only at the level of isolated spectral features.@vyas2020population @mitchellheggs2023manifold

#netn-box(title: [Primary design principle])[
  `cohort_anchored` is primary for `Control vs Parkinson OFF` and `Control vs Parkinson ON`.

  `subject_anchored` is primary for `Parkinson OFF vs ON`.

  Cross-task synthesis is secondary and will be bounded to how much disease-state geometry remains recoverable inside each task-specific surface.
]

= Cohort and design

Both processed bundles use the same cohort layout:

- `28` controls with `condition = not_applicable`,
- `28` Parkinson `OFF` runs,
- `28` Parkinson `ON` runs.

That yields `84` H5 runs in each dataset and `56` unique subjects per task. The tasks differ, however, in what an event means.

- `ds003509` (`simon_conflict`) contains training and test phases with congruent/incongruent stimuli, conflict variants, response correctness, and reward / punishment feedback.
- `ds003506` (`reinforcement_learning`) contains choose/match phases with instruction, stimulus, response, and reward / punishment / timeout / error feedback families.

The manuscript therefore treats the tasks as parallel but not interchangeable. They share cohort logic, coordinate contracts, and summary metrics, but each task keeps its own event-family contrasts.

#figure(
  kind: table,
  table(
    columns: (1.35fr, 1.0fr, 1.0fr, 2.1fr),
    align: left,
    inset: 5pt,
    table.header([*Dataset*], [*Runs*], [*Subjects*], [*Primary event surface*]),
    [`ds003509`], [`84`], [`56`], [`training_*`, `test_*`, conflict / response / feedback families],
    [`ds003506`], [`84`], [`56`], [`choose_*`, `match_*`, response / feedback families],
  ),
  caption: [Shared cohort scale and task-specific event surfaces for the two Parkinson cognitive workload bundles.]
) <tab-design>

= Analysis framework

Two linked layers will be reported for each dataset.

1. *Standard `ndt-analysis` layer.* Global and regional `MNPS 3D`, `MNPS 9D`, Jacobian, and reachability summaries will be exported and contrasted under both coordinate contracts.
2. *Article-local event wrapper.* Task-specific `event_windows/*` segments will be summarized with path, curvature, hysteresis, entropy-rate, and noetic-action metrics in both `3D` and `9D`.

The contrast hierarchy is fixed in advance:

- `Parkinson OFF vs ON`: paired, primary in `subject_anchored`.
- `Control vs Parkinson OFF`: unpaired, primary in `cohort_anchored`.
- `Control vs Parkinson ON`: unpaired, primary in `cohort_anchored`.

This split matters because disease-state and medication-response are not the same inferential problem. The mixed-contract policy avoids flattening both questions into one coordinate frame just because the cohort is shared.

#figure(
  kind: table,
  table(
    columns: (1.5fr, 0.9fr, 0.9fr, 0.9fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*Dataset*], [*`q < 0.05` standard*], [*`q < 0.05` event*], [*`q < 0.1` standard*], [*`q < 0.1` event*]),
    [`ds003509`], [`56`], [`0`], [`108`], [`0`],
    [`ds003506`], [`11`], [`0`], [`31`], [`0`],
  ),
  caption: [Retained primary rows by dataset, threshold, and layer. Both tasks were dominated by the standard layer; no event-locked wrapper row survived `q < 0.1`.]
) <tab-retained>

#figure(
  kind: table,
  table(
    columns: (1.35fr, 1.0fr, 1.0fr, 1.0fr, 1.0fr),
    align: left,
    inset: 4pt,
    table.header([*Dataset*], [*Jacobian / collapse `q < 0.05`*], [*Jacobian / collapse `q < 0.1`*], [*Reachability `q < 0.05`*], [*Reachability `q < 0.1`*]),
    [`ds003509`], [`2`], [`6`], [`2`], [`32`],
    [`ds003506`], [`3`], [`10`], [`0`], [`0`],
  ),
  caption: [Retained Jacobian/collapse-like and reachability-like standard rows. The Simon conflict dataset carries the only substantial reachability branch.]
) <tab-dynamical-families>

= Results

== Simon conflict recovers broad cohort-level disease-state geometry

`ds003509` produced the broadest disease-state signal in the entire manuscript. At `q < 0.05`, the primary standard inventory retained `56` rows, split across `32` rows for `Control vs Parkinson OFF` and `24` rows for `Control vs Parkinson ON`. At `q < 0.1`, the standard inventory expanded to `108` rows, including `4` paired `Parkinson OFF vs ON` rows. By contrast, the event-locked wrapper remained fully negative, with `0` rows at both `q < 0.05` and `q < 0.1`.

The strongest `Control vs Parkinson OFF` rows were regional `9D` disease-state measures centered on the `d` family, especially parietal-occipital `d_s_mean` (`d = 1.166`, `q = 0.018`), parietal-occipital `d_n_std` (`d = -1.155`, `q = 0.018`), and central `d_n_std` (`d = -1.129`, `q = 0.018`). The strongest `Control vs Parkinson ON` rows also sat in the standard `9D` layer, especially global and regional `e_m` separation together with persistent parietal-occipital `d_s` differences. This means the Simon dataset did not support a medication-normalization reading. Both Parkinson states remained non-control-like in the cohort-anchor frame, but in slightly different standard-layer coordinates.

Importantly, the Simon `ON` branch was not limited to centroid-like `9D` separation. It also carried a secondary dynamical inventory. At `q < 0.1`, the dataset retained `6` Jacobian/collapse-like rows and `32` reachability-like rows. The clearest non-centroid rows were adaptive-collapse `q_ratio_h4` (`d = -0.632`, `q = 0.034`) and `capture_gate` (`d = 0.616`, `q = 0.034`), followed by reachability rows such as `persistence_log_eig_var_median` (`d = -0.919`, `q = 0.040`), `persistence_kappa_median` (`d = -0.888`, `q = 0.040`), and `tube_dir_entropy_mean` (`d = -0.789`, `q = 0.066`). That broader dynamical spread strengthens the claim that Simon conflict is not merely a static disease-state separator, but also the only task here with a sizable corrected reachability inventory.

The new violin panels make the subject-level distributions explicit across classical, `MNPS 9D`, and Jacobian / reachability families. The QC pass supported the standard-layer Simon interpretation rather than softening it. Focal retained rows showed leave-one-subject-out sign consistency of `1.0`, standard permutation nulls remained supportive for `global e_m_median` (`empirical p = 0.0078`), `q_ratio_h4` (`empirical p = 0.0155`), and `persistence_log_eig_var_median` (`empirical p = 0.0155`), while the best event row `test_response_all / hysteresis_area_de` failed the circular time-shift null (`empirical p = 0.2`). Geometry also remained at least modestly stronger than the best classical sidecars, with `|d|` gaps of `0.242` for `Control vs Parkinson OFF` and `0.068` for `Control vs Parkinson ON`.

The paired Simon branch was much weaker. No `OFF vs ON` row survived `q < 0.05`, and only four standard rows entered at `q < 0.1`. The clearest paired geometric row remained global `3D m_median` (`d = 0.515`, `q = 0.090`), accompanied by adaptive-collapse `q_ratio_h4`, `capture_gate`, and `a_operator_norm` rows at the same broader threshold (`q = 0.083`). That is enough to justify a bounded paired medication discussion, but not enough to shift the article headline away from recoverable disease-state structure.

== Reinforcement learning recovers a narrower and partly classical OFF-state signal

`ds003506` was materially narrower than `ds003509`. At `q < 0.05`, the primary standard inventory retained `11` rows, split across `10` rows for `Control vs Parkinson OFF` and `1` row for `Control vs Parkinson ON`. At `q < 0.1`, the standard inventory reached `31` rows, with `3` `Control vs Parkinson ON` rows and no paired `OFF vs ON` row surviving. As in Simon conflict, the event-locked wrapper remained fully negative at `q < 0.1`.

The most important difference from Simon conflict is not only smaller counts, but also the composition of the retained rows. The strongest `Control vs Parkinson OFF` rows were partly classical EEG comparator rows, especially relative alpha summaries (`relative_alpha_mean d = 1.113, q = 0.024`) together with a smaller Jacobian branch including `global_mnps_jacobian_9d / mdr_mean` (`d = 0.835`, `q = 0.033`) and `rotational_power_mean` (`d = 0.658`, `q = 0.033`). Broader-layer geometry rows such as frontal `9D d_s_mean` (`d = 1.064`, `q = 0.054`) remained present, but no longer sat in the leading `q < 0.05` set. This means the OFF-state reinforcement-learning signal remained real, but was less purely geometry-led than the Simon conflict signal.

The dynamical branch was also much thinner than Simon conflict, but it was broader than in the previous result pass. Reinforcement learning retained `10` Jacobian-like rows at `q < 0.1` and no reachability row at all. The clearest corrected Jacobian rows were `global_mnps_jacobian_9d / mdr_mean` for `Control vs Parkinson OFF` (`d = 0.835`, `q = 0.033`) and `global_mnps_jacobian_9d / aci_mean` for `Control vs Parkinson ON` (`d = 0.835`, `q = 0.047`), while `tier2_jacobian rotation_coherence_mean_axis_2` dropped to a broader-layer near-miss (`d = -0.853`, `q = 0.055`) and central `block_frobenius_mean` remained secondary (`d = -0.714`, `q = 0.090`). The paired medication branch was fully negative at `q < 0.1`. The safest interpretation is therefore that the reinforcement-learning dataset supports a narrower OFF-state disease signal, with a small Jacobian-only ON-state remainder and no corrected paired medication or reachability story.

The reinforcement-learning violin panels sharpen the same point. The strongest OFF-state distributions are visibly classical-alpha-heavy, and the QC summaries agree. Leave-one-subject-out sign consistency was `1.0` for focal alpha, global `d_s`, and exploratory reachability-like rows. Standard permutation nulls supported the retained alpha and global `d_s` rows (`empirical p = 0.0078`) and even the exploratory `persistence_tau_log_det_median` row (`empirical p = 0.0155`). But the geometry-versus-classical comparison showed that the best OFF-state classical alpha row slightly exceeded the best geometry row (`|d|` gap = `-0.049`), and the best event row `match_feedback_punishment / hysteresis_area_de` again failed the circular time-shift null (`empirical p = 0.2`). That pattern reinforces a bounded reading: the RL task contains a real OFF-state signal, but it is not a geometry-only win and therefore functions here mainly as a boundary condition on recoverability.

== Paired medication and event-wrapper branches do not generalize across tasks

The two tasks agree on the most important negative result: the event-locked wrapper did not yield a retained row at `q < 0.1` in either dataset. They also agree that the paired medication branch is weak. Simon conflict retains only a small `OFF vs ON` remainder at `q < 0.1`, and reinforcement learning retains none. That means neither task supports a robust corrected medication-normalization story, and neither task supports promotion of the article-local wrapper into a positive task-dynamic endpoint.

== Task context determines recoverability under a fixed analysis contract

Simon conflict is the stronger disease-state dataset. It retains broad standard-layer separation for both `Parkinson OFF` and `Parkinson ON`, and those rows are not limited to `9D` geometry. Simon also retains a modest collapse/Jacobian branch and the only substantial corrected reachability branch in the study. Reinforcement learning is narrower and more heterogeneous. Its strongest OFF-state rows mix standard geometry with classical alpha comparators, and its ON-state branch expands to a small Jacobian-only remainder, with no retained reachability inventory. The QC pass sharpens that asymmetry rather than weakening it: Simon geometry modestly exceeds its best classical competitors, whereas the RL OFF-state branch is at least partly classical-facing and can be matched or slightly exceeded by alpha-sensitive sidecars. The cross-task synthesis is therefore not one unified Parkinson workload geometry, but a task-dependent recoverability hierarchy in which Simon conflict is both more cohort-separating and more dynamically structured than reinforcement learning.

= Discussion

This manuscript is best read as a task-dependent recoverability paper rather than as a generic Parkinson cognitive-workload paper. Under one fixed mixed-contract analysis policy, Simon conflict preserves a broad recoverable disease-state geometry, whereas reinforcement learning preserves a thinner and partly classical-facing OFF-state signal. The contribution is therefore not that all Parkinson workload tasks expose the same state axis, but that task context determines how much disease-state geometry remains recoverable.

Three conclusions follow.

First, the disease-state branch is broader than the paired medication branch in both tasks. In Simon conflict this is very clear: broad `Control vs Parkinson OFF` and `Control vs Parkinson ON` inventories survive in `cohort_anchored` space, while the paired branch enters only at `q < 0.1`. Simon also extends into corrected collapse and reachability families, especially for `Control vs Parkinson ON`. In reinforcement learning the same hierarchy remains, but in a thinner form: OFF-state separation survives, a small ON-state Jacobian branch also survives, the paired branch is absent, and no reachability row is retained.

Second, task context matters. Simon conflict behaves like a geometry-rich disease-state amplifier with an added collapse/reachability tail. Reinforcement learning behaves like a narrower and partly classical-EEG-facing disease-state surface with a small Jacobian-only dynamical remainder and no corrected reachability extension. That difference is scientifically useful because it argues against a simplistic idea that any Parkinson cognitive-workload task will expose the same corrected state geometry once exported into the same coordinate family. It also bounds any claim that the reinforcement-learning branch demonstrates a geometry-specific advantage over conventional EEG summaries.

Third, the negative event result is itself informative. The wrapper layer was intentionally designed to test whether task-family windows added a stronger dynamic story on top of the standard exports. In these two datasets, they did not survive correction, and the focal event rows also failed the circular time-shift null in both datasets (`empirical p = 0.2` in each case). The article should therefore be written as a standard-layer disease-state paper with a negative event-wrapper appendix branch, not as an event-locked Parkinson biomarker claim.

= Limitations

1. The manuscript remains exploratory, and the main corrected surfaces are post hoc article-facing summaries rather than preregistered endpoints.
2. The event wrapper is article-local code layered on top of repository-standard exports, and it remained negative after correction in both tasks.
3. Reinforcement learning showed a meaningful OFF-state signal, but several of its strongest rows were classical alpha comparators rather than purely geometric rows, which bounds any claim of geometry-specific advantage in that task.
4. Cross-task synthesis risks over-compression if Simon conflict and reinforcement-learning event families are treated as more interchangeable than they really are.
5. Clinical severity covariates remain limited in the current bundle-facing metadata.
6. The two tasks share cohort structure but should not be read as interchangeable assays or as proof that one task-general Parkinson workload signature exists.

= Conclusion

The combined analysis does not support one generic task-level Parkinson workload signature. It supports a narrower and more defensible conclusion: task context determines how much Parkinson disease-state geometry is recoverable under a fixed mixed-contract analysis policy. Simon conflict yields broad cohort-level disease-state geometry in the standard layer with an added collapse/reachability tail, reinforcement learning yields a narrower and partly classical-EEG-dominant signal with a small Jacobian-only remainder, and neither task yields a corrected event-locked wrapper inventory. The paired medication branch is weak in both tasks and should remain secondary.

#bibliography("parkinson_on_off_cognitive_workload_references.bib")
