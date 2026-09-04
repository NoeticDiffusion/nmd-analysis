#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Summary - Walking-State Geometry in Parkinson Disease",
  short-title: "Walking Clinical Summary",
  subtitle: "A cautious clinician-facing interpretation of the mixed-anchor ds007526 analysis",
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

This supplement is written for clinicians and clinically oriented readers who want a plain-language interpretation of the Parkinson walking article without needing to work directly in the full Noetic Diffusion / NeuralManifoldDynamics vocabulary.

The goal is not to make the findings sound more mature than they are. The goal is to translate the current result set while preserving the manuscript's caution:

1. this is a group-level exploratory physiology study,
2. not a validated bedside biomarker,
3. not a treatment-response predictor,
4. and not a replacement for neurological examination, gait assessment, or standard EEG interpretation.

= What was compared

The dataset contributes `144` participants and `277` processed runs. The article asks two different clinical questions:

- Are Parkinson participants physiologically distinct from healthy controls *during walking*?
- How much does the same Parkinson participant change from *rest to walk*?

Those questions are not treated as the same statistical problem. The between-group walk comparison is handled in a cohort-shared frame. The within-subject Parkinson rest-to-walk comparison is handled in a subject-shared frame. In clinical language, the analysis tries to compare like with like instead of forcing disease-state and task-change into one mathematical comparison.

= Clinician-facing headline

The clearest message is not that walking simply normalizes Parkinson physiology, and it is not that one walk-vs-rest change metric is ready for clinical deployment. The clearest message is that Parkinson participants remain distinguishable from healthy controls during walking, and that this disease-state separation is stronger than the paired rest-to-walk reconfiguration seen within Parkinson participants.

In practical terms:

- the between-group walk branch retains four corrected global rows, all in the same `d` family;
- the paired Parkinson branch is real in the base standard family and becomes stronger in the revised article once the targeted `IQR`/`MAD` dispersion extension is included;
- the healthy-control paired branch is real, but secondary;
- and the richer clinical association structure appears mainly on the rest side rather than on the walk side.

= A short background on NDT and NMD

Clinicians do not need to buy the full theoretical language of Noetic Diffusion Theory in order to read this paper safely. The most practical way to read the method is as follows.

The raw EEG is first transformed into a fixed low-dimensional state description. In this article that exported state is summarized as a `3D` chart:

- `m`
- `d`
- `e`

with a more detailed `9D` expansion underneath it:

- `m_a`, `m_e`, `m_o`
- `d_n`, `d_l`, `d_s`
- `e_e`, `e_s`, `e_m`

The important point clinically is not the exact algebra. The important point is that the method does *not* claim to read out one hidden disease mechanism directly from EEG. It creates a stable, versioned coordinate system and then asks whether groups or conditions sit in different parts of that system, move differently inside it, or show different deformation and reachability patterns over time.

So when the paper refers to `MNPS`, Jacobian, or reachability, the safest translation is:

- `MNPS`: where the physiology tends to sit in the exported state map,
- Jacobian / `MNJ`: how local movement rules in that map appear to bend or reorganize,
- reachability: how broad or constrained nearby future movement appears to be,
- trajectory metrics: how the recorded path actually moves through the map.

= What `d` and `d_n` mean in clinical prose

Among the three top-level coordinates, `d` is the one most useful for the present walking paper.

The safest way to read `d` is as a *deviation / displacement family* inside the exported state chart. In other words, it summarizes one part of how far the current physiology sits from the reference operating pattern defined by the active NeuralManifoldDynamics contract. It is *not* a direct disease score, a dopamine score, or a validated severity axis.

The `d` coordinate is built from three lower-level subcoordinates:

- `d_n`
- `d_l`
- `d_s`

In this paper, `d_n` is especially important because several of the strongest walking rows are `d_n_mean` and `d_n_median`. The safest clinician-facing translation of `d_n` is:

- a *network-deviation-like* subcoordinate,
- indexing how strongly the exported physiology departs from its reference network regime,
- without implying that one specific anatomical network or one single symptom domain has been isolated.

So if `d_n_mean` is higher in Parkinson during walking, the restrained reading is not:

- "Parkinson patients have more of factor X,"
- or "this directly measures gait impairment,"
- or "this is a disease severity biomarker."

The restrained reading is:

- during walking, Parkinson physiology occupies a more shifted or more deviation-heavy region of the exported state space than healthy-control physiology.

That is a group-level physiological organization claim, not yet a bedside diagnostic claim.

= How to translate the main `d`-family findings clinically

The walking paper's strongest cohort rows are `d_n_mean`, `d_n_median`, `d_mean`, and `d_median`. A clinically understandable paraphrase would be:

- healthy controls and Parkinson participants do not simply differ by noise around the same walking EEG state;
- instead, the Parkinson group sits in a consistently shifted dynamical regime while walking;
- and that shift is concentrated in the deviation-related part of the exported state chart.

Clinically, one might describe this as:

"During walking, the Parkinson group appears to occupy a more displaced network-physiology regime than controls."

That wording is better than:

- "the brain is more disordered,"
- "the EEG is more abnormal in a general sense,"
- or "the metric measures Parkinson severity directly."

Similarly, when the paired branch shows rest-to-walk change in Parkinson, especially in `d`-family and `IQR`/`MAD` dispersion rows, the safest translation is:

- the Parkinson state does reconfigure when patients go from rest to walking,
- and part of that reconfiguration is not only a shift in average position, but a change in how variable or spread out the within-run state trajectory is.

That is closer to a statement about *state reorganization* than about direct treatment response or symptom improvement.

= Three clinically relevant takeaways

== 1. Walking exposes a coherent disease-state separation

The strongest walk disease-state rows are global `d_n_mean`, `d_n_median`, `d_mean`, and `d_median`, all higher in Parkinson than in healthy controls during walking. The clinically useful translation is not that one single scalar has been discovered. It is that the walking physiology of the Parkinson group occupies a reproducibly shifted region of the exported state space when compared in a shared cohort frame.

That makes the result more like a compact disease-state geometry than a broad feature scatter. The frontal regional replications support the idea that the walk effect is concentrated rather than random, but they do not justify an anatomical localization claim by themselves.

== 2. Parkinson participants do reconfigure from rest to walk, but the paired effect is still not the whole story

The paired Parkinson branch is now better read as a mixed location-and-dispersion result. In the revised article, the strongest paired rows include not only `d_n_mean` but also `m_a_iqr`, `d_iqr`, and `d_mad`. The safe clinical translation is that the Parkinson state does change when participants move from rest to walking, and that this change includes both a shift in where the physiology sits and a shift in how spread out or variable the within-run state expression is. Even so, the between-group disease-state separation during walking remains the stronger headline.

That matters because clinicians may be tempted to treat a paired rest-to-walk effect as more intuitive or more "real" than a between-group state-space shift. In this export, the paired branch is real but narrower.

== 3. Baseline physiology still carries the richer clinical-association signal

Although the article is walk-centered, the strongest clinical association surfaces appear mainly in rest. In the global layer, rest `d_s_mean` tracks age, executive function (`CTT`), and cognition (`MoCA`). In the regional layer, similar rest-side associations appear for central and frontal `d_s_mean`.

The clinician-facing implication is modest: baseline physiology may still be the richer disease-burden surface, even when the cleanest between-group separation appears during walking. That does *not* mean rest is a better diagnostic test. It means the current export distributes its useful information across two contexts: walk for the main disease-state contrast, rest for much of the clinical covariance structure.

= How to read the geometry terms clinically

The manuscript necessarily uses geometric language, but the safest clinical translation is simple.

- `MNPS` / state-space position: where the exported physiology tends to sit.
- Jacobian / deformation metrics: how the local rules of motion appear to change.
- Reachability metrics: how broad or constrained short-horizon future movement appears under the local model.
- Realized trajectory metrics: how the observed path moves through that space.

These are *descriptors* of physiology. They are not direct disease mechanisms, and they are not yet validated clinical entities.

= What clinicians should not conclude

This supplement is intended to make overinterpretation less likely. The current results should *not* be used to conclude that:

1. one geometry row can diagnose Parkinson disease,
2. the paired rest-to-walk branch is a ready-made treatment-response marker,
3. frontal regional support rows prove a localized cortical source,
4. the present method has been shown to outperform classical EEG,
5. or the retained rows already generalize beyond this processed bundle.

The fourth point is especially important because the current export does not expose the `conventional_eeg` extension. The article therefore cannot make a fair classical-comparator benchmark claim from this dataset version.

= What would increase clinical confidence

The clinically most useful next steps would be:

1. replication on an independent Parkinson walking cohort,
2. a bundle that includes valid classical EEG sidecars,
3. longitudinal or treatment-linked designs that connect geometry changes to clinically meaningful outcomes,
4. and external testing of whether the walk disease-state rows remain stable across preprocessing and site variation.

Until those steps are done, the present manuscript should be read as a careful signal-mapping study rather than as a translational claim of readiness.

#bibliography("parkinson_walking_geometry.bib")
