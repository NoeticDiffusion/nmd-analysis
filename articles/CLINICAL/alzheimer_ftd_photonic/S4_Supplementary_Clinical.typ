#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Summary - Evoked Neural Geometry Under Photic Stress in Alzheimer Disease and Frontotemporal Dementia",
  short-title: "Photic Dementia Clinical Summary",
  subtitle: "A cautious clinician-facing interpretation of the exact block-native Alzheimer/FTD photic rerun",
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

The goal is not to make the findings sound more mature than they are. The goal is to translate the present result bundle into clinically understandable language while preserving the manuscript's caution:

1. this is a group-level exploratory EEG physiology study,
2. not a validated dementia biomarker,
3. not a disease-severity instrument ready for bedside use,
4. and not a substitute for syndromic assessment, standard EEG interpretation, neuropsychology, imaging, or longitudinal clinical follow-up.

= What was compared

The local photic cohort contains `88` participants: `29 Healthy`, `36 AD`, and `23 FTD`. The manuscript restricts its main inferential surface to exact block-native `PHOTO 5`, `10`, `15`, and `20 Hz` windows from the canonical ds006036 rerun.

The paper then asks two different clinical questions:

- Do Alzheimer disease or frontotemporal dementia show evoked physiological differences from Healthy controls during rhythmic visual driving?
- On the exact overlapping global Jacobian surface, is the strongest evoked Alzheimer-versus-Healthy difference also present at rest?

To answer the second question, the article uses a narrow ds004504 resting-state reference on the same global `3D` and `9D` `mdr_median` surface. Clinically, this means the manuscript is not only asking whether dementia groups differ during flicker. It is also asking whether the strongest observed difference is more visible under perturbation than during baseline rest.

= Clinician-facing headline

The clearest message is not that the dataset cleanly separates all dementia syndromes. The clearest message is that the stable corrected group signal is a narrow `AD vs Healthy` evoked difference that becomes much more visible under photic driving than on the matched resting reference.

In practical terms:

- the corrected group surface is asymmetric, not broad;
- `AD` shows the clearest repeatable evoked separation from `Healthy`;
- `FTD vs Healthy` and `AD vs FTD` do not survive the main corrected group threshold;
- and symptom-severity structure is broader than the disease-dissociation surface.

This makes the manuscript stronger as an evoked stress-test physiology report than as a categorical dementia classifier.

= Three clinically relevant takeaways

== 1. Alzheimer disease showed the clearest repeatable evoked difference from Healthy controls

All corrected group rows in the main paper localized to global `9D` MNJ `mdr_median` for `AD vs Healthy`, strongest at `PHOTO 20 Hz` and also retained at `PHOTO 10 Hz` and `PHOTO 15 Hz`.

The safest clinical translation is not that one specific flicker frequency diagnoses Alzheimer disease. It is that, on this exported surface, Alzheimer physiology showed less control-like local dynamical reconfiguration during photic driving than Healthy physiology, and that this pattern repeated across several adjacent stimulus frequencies rather than appearing as a single isolated row.

By contrast, the manuscript does *not* support a strong corrected claim that `FTD` is cleanly separated from `Healthy`, nor that `AD` and `FTD` are cleanly separated from each other on the main group surface.

== 2. The matched resting reference was much weaker than the photic effect

On the exact overlapping global `9D` `mdr_median` surface, the resting-state `AD vs Healthy` contrast was near null (`d = -0.080`, `q = 0.909`), whereas the photic contrast became large and corrected, peaking at `PHOTO 20 Hz` (`d = -0.984`, `q = 0.0034`).

Clinically, the restrained reading is that the strongest manuscript signal is not simply a baseline difference that happens to persist during stimulation. Rather, the perturbational setting appears to reveal or amplify physiological structure that is much less obvious on the same summary family at rest.

This does *not* prove that photic stimulation is generally superior to resting EEG for all dementia questions. It supports a narrower statement: on this specific shared Jacobian surface, the Alzheimer-versus-Healthy difference is much clearer during rhythmic driving than on the matched resting reference.

== 3. Symptom severity structure was broader than the group-separation surface

The MMSE layer retained eight corrected rows, led by pooled-dementia `PHOTO 20 Hz` global `9D` MNJ `rotational_power_median` (`rho = -0.470`, `q = 0.0020`). `AD_only` also retained corrected rows, while the strongest `FTD_only` row remained visually interesting but subthreshold after correction (`q = 0.097`).

For clinicians, this means the dataset contains more symptom-linked structure than diagnosis-linked structure. That is important, because it suggests the exported physiology may track cognitive burden in ways that are not identical to case-control separation.

At the same time, the evidence remains group-level and uneven. A broader MMSE surface does *not* mean that the method is already ready for individual severity staging, prognosis, or treatment monitoring.

= How to read the geometry terms clinically

The manuscript necessarily uses geometric language, but the safest clinical translation can stay simple.

- `MNPS` / state-space position: where the exported EEG physiology tends to sit on the fixed measurement surface.
- MNJ / Jacobian metrics: how the local rules of motion on that surface appear to change.
- `mdr_median`: how quickly the local Jacobian appears to reconfigure relative to its current magnitude.
- Reachability-style metrics: how broad or constrained nearby short-horizon movement appears to be.
- MMSE correlations: whether worse cognition aligns with more abnormal values on these exported summaries.

These are *descriptors* of physiology, not direct disease mechanisms. They can help organize complex EEG structure, but they are not yet established diagnostic entities.

= A restrained clinical interpretation of the current result set

If one wanted to summarize the paper in clinic-friendly language, the most defensible wording would be close to the following:

Under rhythmic photic driving, Alzheimer disease showed a repeatable abnormality relative to Healthy controls on a global high-dimensional Jacobian summary, and this abnormality was much weaker on the matched resting reference. Frontotemporal dementia did not yield an equally stable corrected group signal on the main surface. Symptom severity, especially lower MMSE, aligned with a broader set of high-frequency global Jacobian summaries than the group map itself.

That wording is deliberately narrower than:

- "photic EEG cleanly distinguishes all dementia syndromes,"
- "the method already separates Alzheimer disease from frontotemporal dementia,"
- "the strongest frequency is a clinically validated resonance marker,"
- or "the geometry is ready for individual patient stratification."

The present evidence does not justify those stronger claims.

= What clinicians should *not* conclude

This supplement is intended to make overinterpretation less likely. The current results should *not* be used to conclude that:

1. a single geometric metric can diagnose Alzheimer disease or frontotemporal dementia,
2. the absence of a corrected `FTD vs Healthy` row means that frontotemporal dementia has no evoked physiological abnormality,
3. photic stimulation has been shown to outperform resting EEG across dementia workups in general,
4. the observed `AD vs Healthy` effect isolates cortical disease alone rather than also reflecting retinal or early visual-pathway vulnerability,
5. or the retained MMSE rows are already ready for patient-level cognitive staging.

At present, the findings are best viewed as a carefully bounded evoked physiology map with a narrow corrected Alzheimer-versus-Healthy surface and a broader but still exploratory severity layer.

= What would increase clinical confidence

The clinically most useful next steps would be:

1. replication on an independent dementia cohort with similar photic labeling quality,
2. explicit comparison against classical EEG slowing, alpha, and complexity panels on the same participants,
3. better control of retinal and early visual-pathway confounding in the interpretation of the evoked difference,
4. linkage to diagnosis-relevant covariates such as disease duration, syndrome subtype, medication exposure, and imaging burden,
5. and eventual testing of whether any combination of geometric and conventional EEG summaries improves clinically meaningful discrimination or prediction.

Until those steps are done, the current manuscript should be read as a structured perturbational EEG study rather than as a translationally mature dementia biomarker report.

#bibliography("alzheimer_ftd_reference_list.bib")
