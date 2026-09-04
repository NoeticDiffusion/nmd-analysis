#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Summary - Depressive Symptom Geometry Across Rest and Probabilistic Selection",
  short-title: "Depression Probabilistic Selection Clinical Summary",
  subtitle: "A cautious plain-language interpretation of the paired depression rest-task article",
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

This supplement is written for clinicians and clinically oriented readers who want a plain-language interpretation of the article without needing to work directly in the full Noetic Diffusion / NeuralManifoldDynamics terminology.

The goal is not to make the findings sound more mature than they are. The goal is to translate the current result set into clinically understandable language while preserving the manuscript's caution:

1. this is a group-level physiological analysis,
2. not a validated depression biomarker,
3. not a treatment-response predictor,
4. and not a substitute for clinical interview, rating scales, or standard EEG interpretation.

= What was compared

The article compares two linked surfaces from the same young depression-relevant cohort:

1. task EEG during probabilistic selection (`ds003474`),
2. resting-state EEG from the matched depression article (`ds003478`).

The symptom axis is Beck Depression Inventory (BDI), treated both continuously and through the article's fixed bands:

1. `BDI 0-13`
2. `BDI 14-19`
3. `BDI 20-63`

The analysis therefore asks three clinically intuitive questions:

1. Do low- and high-BDI participants differ during task-state geometry?
2. Do specific event periods in the task carry symptom-linked effects?
3. Does symptom burden organize the *difference* between task and rest?

= Clinician-facing headline

The clearest message is not that depression produced a large rest-to-task reconfiguration failure. The clearest message is that depressive symptom burden is more visible in the task-state and rest-state geometric surfaces themselves than in the paired `task - rest` delta.

In practical terms:

1. coarse `3D` summaries were weak,
2. the strongest task-state rows concentrated in reachability and block-resolved `9D` dynamics,
3. the direct paired delta layer was broadly null,
4. and the event-window layer stayed exploratory.

That is a narrower and more defensible clinical message than claiming one large task-evoked depression signature.

= Three clinically relevant takeaways

== 1. Symptom burden was more visible in higher-order local geometry than in coarse position

The task-state signal did not localize cleanly to the simplest `3D` descriptors. Instead, the strongest corrected low/high BDI rows were:

1. `Task 9x9 block MNJ / block_frobenius_mean (e -> d)`: `d = -0.778`, `q = 0.0109`
2. `Task reachability / tube_log_eig_var_mean`: `d = -0.719`, `q = 0.0107`

Clinically, the safest translation is:

- high-BDI participants were not mainly distinguished by one simple shift in average task-state position,
- they were better distinguished by how locally structured and how locally reachable the exported dynamics looked.

This should *not* be read as proof of one unique disease mechanism. It should be read as evidence that the more complex dynamic descriptors were more informative than the coarsest state coordinates in this cohort.

== 2. The task event layer did not become a strong depression biomarker

The event-window analysis was useful because it asked whether symptom burden concentrated specifically around feedback, training, testing, or response epochs. But the low/high event findings remained modest. None of the article-facing event rows survived FDR correction.

The strongest continuous event suggestions were still only near-miss findings:

1. `feedback_incorrect / post_far / speed_mean`: `rho = 0.203`, `q = 0.076`
2. `train_stim_any / post_far / speed_mean`: `rho = 0.196`, `q = 0.093`

For clinicians, the important interpretation is restraint:

- the task may contain symptom-sensitive peri-feedback and late-training effects,
- but the present article does not justify a claim of a robust event-locked depression marker on this coarse event surface.

== 3. The paired rest-task delta was weaker than the separate rest and task stories

This was the key negative result.

If higher BDI had primarily reflected a strong failure to reconfigure between rest and task, one would expect the paired `task - rest` layer to sharpen the signal. It did not. The paired rows were broadly null:

1. paired reachability: `d = -0.130`, `q = 0.804`; `rho = -0.061`, `q = 0.915`
2. paired `3D MNPS`: `d = -0.165`, `q = 0.804`
3. paired `9D MNJ`: `d = -0.147`, `q = 0.804`

Clinically, this means:

- the article supports symptom-linked state differences more strongly than symptom-linked state-*change* differences,
- so the present data do not support a strong "rest-to-task reconfiguration deficit" headline.

= How to read the geometric terms clinically

The safest plain-language translation is simple.

1. `MNPS` or state-space position: where the exported physiology tends to sit.
2. `MNJ` or Jacobian metrics: how the local rules of motion appear to deform.
3. reachability: how broad or constrained the short-horizon future state neighborhood appears to be.
4. paired delta: how much the same person's task value differs from their rest value.

These are descriptors of physiology, not validated diagnostic entities. Their value at this stage is that they may help organize complex EEG structure into interpretable group-level summaries that can later be tested against clinical variables and conventional EEG panels.

= What clinicians should *not* conclude

The current results should *not* be used to conclude that:

1. one NDT/NMD metric can diagnose depression,
2. a BDI threshold has been biologically validated,
3. the task event layer already provides a clinically useful depression biomarker,
4. the paired rest-task delta is a robust measure of maladaptive cognitive reconfiguration,
5. or these findings already generalize beyond this processed bundle.

At present, the findings are best viewed as structured exploratory physiology with internally coherent task-state and rest-state group patterns.

= What would increase clinical confidence

The clinically most useful next steps would be:

1. replication in an independent depression cohort,
2. richer event-specific annotations beyond the current broad task-family windows,
3. direct comparison against conventional EEG comparator panels,
4. linkage to broader clinical variables beyond BDI alone,
5. and testing whether combined geometric and classical EEG summaries improve clinically meaningful discrimination.

Until those steps are done, the current manuscript should be read as a careful signal-mapping study rather than as a translational claim of readiness.
