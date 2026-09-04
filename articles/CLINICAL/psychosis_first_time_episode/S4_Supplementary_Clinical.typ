#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Summary - First-Episode Psychosis Geometry Across Two Resting-State EEG Cohorts",
  short-title: "Psychosis Clinical Summary",
  subtitle: "A cautious clinician-facing interpretation of the medication-stratified psychosis study",
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

This supplement is written for clinicians and clinically oriented readers who want a plain-language reading of the psychosis manuscript without needing to work directly in the full NeuralManifoldDynamics terminology.

The aim is not to make the findings sound more mature than they are. The aim is to translate the current result set while preserving the manuscript's caution:

1. this is a group-level observational physiology study,
2. not a diagnostic test,
3. not a treatment-response biomarker,
4. and not a substitute for clinical assessment, medication review, or standard EEG interpretation.

= What was compared

The paper analyzes two resting-state first-episode psychosis cohorts:

- `ds003944`: `32` healthy, `19` unmedicated FEP, `31` medicated FEP
- `ds003947`: `30` healthy, `8` unmedicated FEP, `23` medicated FEP

The important clinical design choice is that the study does *not* collapse all FEP participants into one pool as the main analysis. Instead, it keeps medicated and unmedicated patients separate and asks whether the geometry that distinguishes psychosis from healthy controls changes with medication context.

In plain language, the question is:

- Do medicated and unmedicated first-episode patients look different from healthy controls?
- If so, does that difference appear in the same way across cohorts?
- And does pooling all FEP together hide clinically relevant structure?

= Clinician-facing headline

The cleanest message is not that one universal psychosis EEG marker was found. The cleanest message is that resting-state psychosis geometry is heterogeneous, and that medication stratification helps keep that heterogeneity visible.

More concretely:

- in `ds003944`, the strongest signal sits in a stable `m`-family displacement, especially for medicated FEP,
- in `ds003947`, the strongest corrected signal sits in unmedicated trajectory dynamics rather than in the same static first-order layer,
- and pooling all FEP together weakens the most interesting `ds003947` effect.

This means the study supports a methodological and physiological point: first-episode psychosis is not well summarized by one pooled geometry, and medication context appears important enough to change what looks most abnormal.

= Three clinically relevant takeaways

== 1. Medication heterogeneity is not a nuisance detail

The study repeatedly shows that medicated and unmedicated FEP should not automatically be treated as one physiologic group. In `ds003944`, the medicated subgroup carries the clearest corrected `m`-axis displacement. In `ds003947`, the unmedicated subgroup carries the strongest corrected trajectory abnormality.

In the manuscript, that first point is not just a general impression. In `ds003944`, the main corrected medicated-versus-healthy rows are:

1. `m_mean`
2. `m_median`
3. `m_std`
4. stratified `m_o_mean`
5. stratified `m_e_mean`

Here `m` refers to the metastability / mobility family. In plain language, it is the part of the exported state space intended to summarize how readily the resting EEG appears to move through organized neural-state configurations rather than remaining confined to one narrow regime. It should be read as a release-bound operational coordinate family, not as one direct biological variable.

Operationally, these metrics mean slightly different things:

1. `m_mean` is the average resting-state position on the coarse `m` axis. In plain language, it asks where the subject tends to sit on the metastability-family coordinate.
2. `m_median` is the median position on that same axis. In plain language, it asks whether that shift is typical across the recording rather than driven by a few extreme windows.
3. `m_std` is the spread of values on the `m` axis. In plain language, it asks whether the subject occupies a broader or narrower range of `m`-states.
4. `m_o_mean` and `m_e_mean` are higher-resolution `9D` subcoordinates inside the broader `m` family. In plain language, they ask *which part* of the `m`-family carries the displacement once the state space is decomposed more finely.

Clinically, this means the `ds003944` medicated signal looks more like a persistent shift in where resting-state physiology sits, and how broadly it occupies that `m`-related region, rather than one isolated transient effect.

Clinically, the safest translation is:

- medication exposure, illness severity, and treatment selection are probably entangled,
- the observable resting-state EEG geometry shifts with that context,
- and pooled case-control analyses may hide clinically relevant subgroup structure.

== 2. The paper supports a shared analysis surface, not a bedside biomarker

Some separation is visible in more familiar EEG baselines as well, such as `alpha`, `beta/alpha`, and Hjorth complexity. That matters clinically because it means the geometry is not obviously replacing conventional EEG interpretation.

Those comparator measures also have fairly direct clinical meanings:

1. `alpha` is the resting alpha-band power level.
2. `beta/alpha` is a spectral balance ratio, asking how much faster activity is present relative to alpha.
3. Hjorth complexity is a classical shape / irregularity descriptor of the EEG time series.

So the reviewer-facing point here is not that the geometric results float in total isolation from standard EEG. It is that some subgroup separation is already visible in familiar spectral and complexity summaries, while the NMD surface organizes those differences together with first-order coordinates, trajectories, and local dynamics in one common frame.

The value of the approach in the current paper is narrower:

- it organizes multiple first-order, trajectory, and local-dynamical summaries in one coherent reference frame,
- it makes the medication-sensitive subgroup structure easier to read,
- but it does not yet prove superiority over standard EEG features.

== 3. The strongest `ds003947` result is interesting but still fragile

The headline `ds003947` abnormality is a corrected trajectory effect in unmedicated FEP, but that subgroup contains only `8` patients. The leave-one-out check is reassuring, yet the sample remains small.

The specific headline metric there is `m_delta_mean_median`. Operationally, this is a trajectory summary rather than a static position summary:

1. `m_delta_mean_median` tracks the typical short-horizon change in the `m` coordinate across successive windows.
2. In plain language, it asks how strongly the resting-state trajectory keeps drifting or stepping along the `m` family over time.

In `ds003947`, the corrected finding is that unmedicated FEP shows *reduced* `m_delta_mean_median` relative to healthy participants. The clinician-facing translation is therefore not simply "the group sits somewhere else in state space." It is closer to "the moment-to-moment movement along this `m`-related axis looks more blunted or compressed."

The nearby exploratory support also fits that reading:

1. `mdr_mean` is a Jacobian-derived local deformation summary, asking how strongly the nearby flow field tends to deform.
2. `d_l_mean` / `d_l_median` are stratified `9D` position summaries inside one `d`-family subcoordinate, asking whether medicated FEP differs in a more specific higher-resolution location component.

That combination is why the manuscript describes `ds003947` as a trajectory-first and second-order signal rather than as a simple broad first-order displacement.

For clinicians, this means:

- the effect is worth following up,
- it should not be treated as a settled subgroup biomarker,
- and it should not be used for individual-level decision making.

= How to read the geometry clinically

The manuscript necessarily uses geometric language, but the safest clinical translation is simple.

- `MNPS` / state-space position: where the exported physiology tends to sit.
- Trajectory summaries: how that physiology tends to move over short horizons.
- Jacobian summaries: how local rules of motion appear to expand, contract, rotate, or redirect.
- Block-Jacobian summaries: which broad cross-family couplings may contribute to that local redirection.

These are descriptive layers for organizing physiology. They are not direct disease mechanisms, and they are not yet validated clinical entities.

= What clinicians should not conclude

This supplement is meant to reduce overinterpretation. The current article should *not* be used to conclude that:

1. one geometric metric diagnoses first-episode psychosis,
2. medicated FEP is always more abnormal than unmedicated FEP,
3. unmedicated trajectory abnormalities in `ds003947` are already externally established,
4. the method is ready for prognosis or treatment selection,
5. or the geometry has been shown to outperform standard EEG interpretation.

= A restrained clinical bottom line

If the paper were summarized in clinic-facing language, the most defensible wording would be close to this:

Resting-state EEG in first-episode psychosis shows medication-sensitive geometric heterogeneity. The subgroup carrying the clearest separation differs across cohorts, and pooling all psychosis cases together can hide part of that structure. The result is useful for study design and interpretation, but it is not yet a diagnostic or treatment-response tool.

= What would increase clinical confidence

The clinically most useful next steps would be:

1. replication on independent first-episode cohorts with larger unmedicated subgroups,
2. tighter linkage to symptom severity, treatment history, and illness-duration variables,
3. more explicit head-to-head comparison with conventional EEG features,
4. and eventual testing of whether any combined geometric-plus-classical panel improves clinically meaningful discrimination.

#bibliography("psychosis.bib", style: "apa")
