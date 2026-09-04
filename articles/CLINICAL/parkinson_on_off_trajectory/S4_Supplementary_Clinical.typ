#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Summary - Disease-State and Paired Pharmacology Geometry in Parkinson ON/OFF Auditory Oddball EEG",
  short-title: "Parkinson Clinical Summary",
  subtitle: "A cautious clinician-facing interpretation of the mixed-contract ds003490 rerun",
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

This supplement is written for clinicians and clinically oriented readers who want a plain-language interpretation of the manuscript results without needing to work directly in the full Noetic Diffusion / NeuralManifoldDynamics terminology.

The goal is not to make the findings sound more mature than they are. The goal is to translate the current result set into a clinically understandable form while preserving the manuscript's caution:

1. this is a group-level exploratory physiology study,
2. not a validated bedside biomarker,
3. not a treatment-response predictor,
4. and not a substitute for neurological examination, medication review, or standard EEG interpretation.

= What was compared

The dataset contains `25` controls, `25` Parkinson `OFF` runs, and `25` Parkinson `ON` runs. Each Parkinson participant contributes both medication states. The rerun therefore asks two different clinical questions:

- How different is untreated or less-medicated Parkinson physiology from control physiology?
- How much does the same person's physiology shift between `OFF` and `ON`?

The manuscript treats those as different statistical problems. Control-versus-Parkinson is handled in a cohort-shared reference frame. `OFF` versus `ON` is handled in a subject-shared paired frame. In clinical language, this means the paper tries to compare like with like, instead of forcing disease-state and medication-response into the same mathematical comparison.

= Clinician-facing headline

The clearest message is not that medication erased the Parkinson signal. The clearest message is that disease-state structure was broader and easier to detect than paired medication change.

In practical terms:

- Parkinson `OFF` differed from controls on several convergent measures, including shared-reference dispersion in the `9D` state space and slower / more costly eyes-closed trajectories.
- Parkinson `ON` still did not look fully control-like. The leading `Control vs Parkinson ON` standard row is a global Jacobian reconfiguration measure (`mdr_median`, `d = 1.167`) in `Control vs Parkinson ON`.
- The paired `OFF` versus `ON` result was much narrower. Only one paired row survived the stricter main-text threshold.

This means the dataset supports a cautious disease-physiology story more strongly than a strong medication-normalization story.

= Three clinically relevant takeaways

== 1. Parkinson `OFF` was not only shifted, but dynamically less efficient

The strongest `Control vs Parkinson OFF` event-layer rows were not tone-specific oddball markers. They were eyes-closed trajectory measures:

- lower `speed_median`,
- lower `path_length`,
- and lower `noetic_action_kinetic`.

The clinically useful translation is not that the brain is "slower" in one simple scalar sense. It is that the exported state trajectory moves through its baseline eyes-closed space with lower velocity and lower weighted kinetic expression. In this manuscript that is interpreted as altered dynamical engagement or reduced physiological mobility, not as proof of a single mechanism such as bradykinesia or bradyphrenia in isolation.

== 2. Medication changed the physiology, but did not make it control-like

If the rerun had shown only `OFF vs ON` differences, one might be tempted to tell a simple dopamine-response story. That is *not* what the present dataset supports most strongly.

Instead, `Parkinson ON` still retained broad between-group differences from controls, including the `9D` Jacobian `mdr_median` row (`d = 1.167`) and corrected tone-loop hysteresis rows. Clinically, the restrained reading is:

- medication state matters,
- but the medicated Parkinson brain remains physiologically distinct from control on this exported surface,
- and the residual difference is visible both in global deformation summaries and in some event-linked loop-asymmetry measures.

This is closer to a "persistent altered state under treatment" interpretation than to a full normalization interpretation.

== 3. The paired medication signal was real but limited

The within-subject contrast is important because it is the clinically intuitive question: what changes when the same patient goes from `OFF` to `ON`?

The answer here is modest. Only one paired row survived the stricter threshold, `regional_mnps_jacobian_3d / temporal / anisotropy_abs_eig_mean` (`d_z = -0.483`, `q = 0.038`), reflecting a reduction in temporal Jacobian eigenvalue spread between `OFF` and `ON` states. A previously retained near-miss (`signed_divergence_balance_mean_neg`, `d_z = -0.711`, `q = 0.066`) no longer passes the primary threshold after correction to persistence-based metrics. Together these rows are enough to say the paired comparison is not completely null. They are *not* enough to claim a broad, reproducible medication-response signature across the main dynamic families.

For clinical readers, this means:

- do not read the paper as showing a strong per-patient physiological medication marker,
- do read it as showing that the dataset contains more stable disease-state than medication-state structure,
- and consider the paired result hypothesis-generating rather than decision-ready.

= How to read the geometry terms clinically

The manuscript necessarily uses geometric language, but the safest clinical translation is simple.

- `MNPS` / state-space position: where the exported physiology tends to sit.
- Jacobian / deformation metrics: how the local rules of motion appear to be changing.
- Reachability-style metrics: how broad or constrained short-horizon future movement appears to be.
- Realized trajectory metrics: how the observed path actually moves through that space during eyes-closed, eyes-open, or tone periods.

These are *descriptors* of physiology. They are not direct disease mechanisms, and they are not yet validated diagnostic entities. Their clinical value at this stage is that they may organize complex EEG structure into interpretable group-level summaries that can later be tested against classical EEG markers and outcomes.

= How classical EEG comparators should be used

The repository now also supports classical EEG comparator sidecars, such as:

- relative delta / theta / alpha / beta power,
- theta/alpha and delta/alpha ratios,
- peak alpha frequency,
- spectral edge frequency,
- spectral entropy,
- Hjorth mobility,
- and Hjorth complexity.

For clinicians, these comparators are important for two reasons.

First, they give familiar reference points. If a geometric result loosely tracks increased slowing, reduced alpha organization, or altered spectral complexity, that makes the newer result easier to contextualize.

Second, they provide an honesty check. If an NDT/NMD result appears clinically interesting but a broad classical EEG panel is entirely silent, that does not invalidate the geometric result, but it should make the interpretation more careful.

The intended use in this article is therefore adjunctive, not competitive:

- classical EEG comparators help anchor interpretation,
- NDT/NMD measures may still capture structure that the classical panel misses,
- but neither family should be oversold as definitive without external replication.

= A restrained clinical interpretation of the current result set

If one wanted to summarize the paper in clinic-friendly language, the most defensible wording would be close to the following:

Parkinson physiology in this auditory oddball resting export differs from control physiology in a broad state-dependent way, especially in the `OFF` condition. Medication changes some aspects of the exported dynamics, but does not collapse the Parkinson state onto the control state. The between-group disease signal is therefore stronger than the within-subject medication signal in this dataset.

That wording is deliberately narrower than:

- "the EEG normalizes on medication,"
- "the method detects treatment response robustly,"
- or "the geometry is ready for individual patient stratification."

The present evidence does not justify those stronger claims.

= What clinicians should *not* conclude

This supplement is intended to make overinterpretation less likely. The current results should *not* be used to conclude that:

1. a single NDT/NMD metric can diagnose Parkinson disease,
2. an `ON/OFF` physiological threshold is available for clinical use,
3. a patient with a weak paired effect is biologically non-responsive to medication,
4. these geometric measures outperform standard EEG interpretation,
5. or the retained rows already generalize beyond this processed bundle.

At present, the findings are best viewed as structured exploratory physiology with internally coherent group patterns.

= What would increase clinical confidence

The clinically most useful next steps would be:

1. replication on an independent Parkinson cohort,
2. explicit comparison against classical EEG comparator panels,
3. linkage to clinical severity variables such as `UPDRS`, `LEDD`, disease duration, and cognitive status,
4. testing whether the strongest disease-state rows remain stable under stricter preprocessing and site controls,
5. and eventually evaluating whether any combination of geometric and classical EEG measures improves clinically meaningful discrimination or prediction.

Until those steps are done, the current manuscript should be read as a careful signal-mapping study rather than a translational claim of readiness.

#bibliography("parkinson_on_off_trajectory_geometry.bib")