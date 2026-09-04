#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Summary - Resting-State Neural Geometry Across Depressive Symptom Burden",
  short-title: "Depression Clinical Summary",
  subtitle: "A cautious clinician-facing interpretation of the resting-state ds003478 report",
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

This supplement is written for clinicians and clinically oriented readers who want a plain-language interpretation of the resting-state depression article without needing to work directly in the full Noetic Diffusion / NeuralManifoldDynamics terminology.

The goal is not to make the findings sound more mature than they are. The goal is to translate the current result set into clinically understandable language while preserving the article's caution:

1. this is a group-level physiology study,
2. not a validated depression biomarker,
3. not a treatment-selection tool,
4. and not a substitute for clinical interview, rating scales, or standard EEG interpretation.

= What was compared

The article analyzes resting-state EEG from ds003478 using Beck Depression Inventory (BDI) score as the primary clinical axis.

The symptom summaries were intentionally simple:

1. a low-symptom group: `BDI 0-13`
2. a middle-symptom group: `BDI 14-19`
3. a high-symptom group: `BDI 20-63`

The main inferential contrast is low versus high. The middle band is used mainly to ask whether the signal looks like a smooth severity gradient or more like a shift from low to elevated symptom burden.

= Clinician-facing headline

The clearest message is not that depression is best captured by one coarse global EEG shift. The clearest message is that the strongest symptom-linked organization in this export surface appears in higher-order dynamic summaries rather than in the simplest `3D` state coordinates.

In practical terms:

1. coarse `3D` summaries were weak,
2. the strongest selected rows concentrated in reachability, `9D` Jacobian structure, and distribution summaries,
3. and the middle-to-high symptom comparison was much weaker than the low-to-elevated contrast.

That makes the article easier to summarize clinically:

- depressive symptom burden is visible in the resting-state export,
- but the signal is carried more by complex local geometry than by a single gross resting-state scalar.

= Three clinically relevant takeaways

== 1. The strongest signal was not in the coarsest state coordinates

The selected `3D` rows were weak:

1. `Global 3D MNPS / d_median`: `d = 0.042`, `q = 0.860`
2. `Global 3D MNJ / spectral_radius_median`: `d = 0.024`, `q = 1.00`

By contrast, the strongest selected low/high rows were:

1. `Reachability / tube_log_eig_var_mean`: `d = -0.678`, `q = 0.00296`
2. `Global 9D MNJ / rotational_power_mean`: `d = 0.569`, `q = 0.00317`
3. `Distribution / e_m_mad_sigma`: `d = 0.688`, `q = 0.0132`

Operationally, these metrics mean different things:

1. `d_median` is the median resting-state position along the exported coarse `d` axis. In plain language, it asks whether the cohort sits in a different average deviation-related region of the `3D` state space.
2. `spectral_radius_median` is the median size of the dominant local Jacobian eigenvalue. In plain language, it asks whether the local resting-state dynamics tend to be more strongly amplifying / damping overall.
3. `tube_log_eig_var_mean` is the mean log-variance of the reachability-tube eigenvalues. In plain language, it asks whether the locally reachable future neighborhood is more uneven or more compressed across directions.
4. `rotational_power_mean` is the mean strength of the rotational component in the local `9D` Jacobian field. In plain language, it asks whether the resting-state dynamics show more turning / circulation in the higher-dimensional local flow.
5. `e_m_mad_sigma` is a robust sigma-scaled median-absolute-deviation summary for the `e_m` coordinate. In plain language, it asks whether this higher-resolution entropy-related coordinate is more broadly spread across the recording.

Clinically, the safest translation is:

- the most visible symptom-linked resting-state difference is not simply "more" or "less" activity on one coarse axis,
- it is better described as a change in the local structure and local accessibility of the exported resting-state dynamics.

== 2. The signal looked more like a low-to-elevated regime shift than a smooth high-range gradient

The middle band matters because it tells us whether the results behave like a gradual severity ladder.

The clearest clinical-band split was:

1. `BDI 0-13 vs 14-19`: reachability `tube_log_eig_var_mean`, `d = -0.831`, `q = 7.46e-6`
2. `BDI 0-13 vs 14-19`: distribution `e_m_mad_sigma`, `d = 1.727`, `q = 5.01e-4`

But `BDI 14-19 vs 20-63` was much weaker on the same selected surface. That argues for restraint:

- the current article supports a low-versus-elevated symptom regime contrast more clearly than a clean within-high-range dose-response gradient.

== 3. Some dynamic differences overlap with baseline state-space position

The centroid-adjusted sensitivity pass is clinically useful because it asks whether the strongest dynamic rows remain when first-order resting-state position is taken into account.

The answer is mixed:

1. `Block MNJ m->m / block_frobenius_mean` remained the clearest adjusted row (`adjusted q = 0.0509`)
2. `Distribution / e_m_mad_sigma` remained suggestive (`adjusted q = 0.0825`)
3. reachability and `9D` MNJ weakened after centroid adjustment

Clinically, this means:

- the stronger rows are real on the export surface,
- but some of their separation likely overlaps with baseline state-space displacement rather than representing a completely independent dynamic layer.

= How to read the geometry terms clinically

The simplest plain-language translation is:

1. `MNPS` or state-space position: where the resting-state physiology tends to sit.
2. `MNJ` or Jacobian metrics: how the local rules of motion appear to deform.
3. reachability: how broad or constrained the locally accessible future state neighborhood appears to be.
4. distribution summaries: how the resting-state values are spread, skewed, or concentrated across the recording.

These are descriptors of physiology, not validated diagnostic entities. Their current value is organizational: they may help compress complex resting-state EEG structure into clinically interpretable group-level summaries that can later be compared against symptoms, diagnoses, and conventional EEG features.

= What clinicians should *not* conclude

The current results should *not* be used to conclude that:

1. one NDT/NMD metric can diagnose depression,
2. one BDI threshold has already been biologically validated,
3. the strongest retained rows are specific to major depressive disorder rather than broader symptom burden,
4. the geometry layer is ready for individual patient stratification,
5. or the findings already generalize outside this cohort.

At present, the safest interpretation is that the resting-state dataset contains a reproducible low-to-elevated symptom organization on this export surface, especially in higher-order local geometry.

= What would increase clinical confidence

The clinically most useful next steps would be:

1. replication in an independent depression cohort,
2. direct comparison against conventional EEG comparator panels,
3. stronger diagnostic annotation beyond BDI alone,
4. testing whether the strongest rows remain stable across preprocessing variations and recording sites,
5. and eventually evaluating whether any combined geometric-plus-classical EEG panel improves clinically meaningful discrimination.

Until those steps are done, the present report should be read as careful signal mapping rather than as a translational claim of readiness.
