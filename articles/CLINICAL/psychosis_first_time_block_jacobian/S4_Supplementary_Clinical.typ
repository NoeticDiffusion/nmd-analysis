#import "../psychosis_first_time_geometric_trajectory/network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Context",
  short-title: "Block-Jacobian Coupling Clinical Context",
  subtitle: "Cautious clinician-facing interpretation of block-Jacobian coupling findings",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Purpose

This supplement translates the manuscript's block-Jacobian findings into cautious clinician-facing language. It is intended for reviewers or readers who wish to understand the clinical implications without engaging with the mathematical formalism. It is deliberately conservative about what has and has not been established.

= What the study measured

Each subject in this study has a five-minute resting EEG recording. NeuralManifoldDynamics 2.1 converts those recordings into a nine-dimensional coordinate sequence, further organised into three functional groups: metastability ($m$), diffusivity ($d$), and entropy ($e$). The local dynamics of this nine-dimensional trajectory are summarised at each moment by a matrix — the Jacobian — that captures how each group influences every other group's rate of change.

This study asks: *how do these within-brain coupling relationships differ by medication state?* Rather than asking where the brain sits on average (the companion static study) or how it moves (the companion trajectory study), this analysis asks which brain sub-systems are driving which others, and how strongly.

The specific measurements are:

- *Self-coupling strength* (diagonal blocks, e.g. $e → e$): how strongly a sub-system's own state determines its own future. High self-coupling means the sub-system is self-governed; low self-coupling means it is driven mainly by external inputs.
- *Cross-coupling strength* (off-diagonal blocks, e.g. $m → e$): how strongly one sub-system influences another. High $m → e$ coupling means changes in the metastability sub-system rapidly propagate into the entropy sub-system.
- *Directed coupling asymmetry* ($c_{"rot"}$): whether the relationship between two sub-systems is balanced or directional. High rotational coupling between $d$ and $e$ means one of them consistently leads the other.

= What the study found

In the larger and better-powered cohort (`ds003944`):

- Unmedicated first-episode psychosis patients showed *lower* entropy self-coupling ($e → e$ Frobenius norm) than healthy controls ($d = -0.573$, $p = 0.026$). This means the entropy sub-system in unmedicated FEP is less autonomously self-governed — it behaves less as a self-contained dynamic unit.
- Medicated first-episode psychosis patients showed *higher* entropy self-coupling than both unmedicated patients ($d = +0.705$, $p = 0.020$) and healthy controls ($e → e$ trace: $d = +0.562$, $p = 0.048$). The ordering is: unmedicated FEP < healthy < medicated FEP.
- Medicated FEP also showed stronger metastability-to-entropy coupling ($m → e$) compared to healthy controls ($d = +0.631$, $p = 0.040$), and stronger directed coupling between diffusivity and entropy ($d ↔ e$ rotational coupling) compared to unmedicated FEP ($d = +0.637$, $p = 0.048$).

In the smaller cohort (`ds003947`, $n = 8$ unmedicated):

- Unmedicated FEP showed large and significant reduction in diffusivity self-coupling ($d → d$ trace: $d = -0.926$, $p = 0.041$). This is a different sub-system from `ds003944` ($e$ vs $d$), but the direction — weakened self-regulation in unmedicated FEP — is consistent.

= What this may mean clinically

These are exploratory results and should not be interpreted as biomarkers or clinical tests. However, the pattern is suggestive of two distinct pharmacological effects.

*In unmedicated FEP*, the entropy (and possibly diffusivity) sub-system appears less able to govern itself: its coupling strength is reduced, suggesting that its dynamics are dominated by external inputs rather than by self-organised activity. This is consistent with a state of entropic dysregulation in untreated psychosis — the brain's complexity sub-system is not self-sustaining but fluctuating reactively. Clinically, this resonates with the unpredictability and apparent randomness of thought and perception reported by unmedicated FEP patients.

*In medicated FEP*, the pattern reverses: entropy self-coupling is elevated above healthy levels. Antipsychotic medications do not simply restore the entropy sub-system to its pre-illness state; they appear to push it into a more constrained, more self-referential configuration than even healthy controls. This could be interpreted as pharmacological over-regulation — the drugs that reduce aberrant complexity do so by increasing the self-governing strength of the entropy sub-system beyond the healthy set-point. The simultaneous increase in cross-family coupling from both metastability and diffusivity into the entropy family suggests that more of the brain's dynamic activity is being channelled into entropy regulation.

One clinical correlate that is plausible, though not established here, is that this over-regulation corresponds to the blunted, constrained quality that many patients on antipsychotics describe: a sense of reduced spontaneity, flattened emotional range, and reduced drive. These symptoms are consistent with a neural state in which the entropy sub-system is more tightly self-coupled and more heavily driven by external sub-systems, reducing the natural variability of thought and experience. This interpretation is speculative and requires direct testing against symptom measures.

= What this study cannot claim

This study *cannot* claim:

- that block Jacobian coupling metrics are validated biomarkers for psychosis, medication state, or treatment response,
- that the specific coupling changes are caused by antipsychotic medication rather than by pre-existing group differences or illness severity,
- that the $e → e$ elevation in medicated FEP is a mechanism of antipsychotic action rather than a correlate of other between-group differences,
- that the findings would replicate in an independent cohort with different demographic or clinical characteristics,
- or that leave-one-subject-out stability has been verified for the primary $e → e$ gradient.

The analysis is cross-sectional and non-randomised. No dose-response relationship has been demonstrated within the medicated group. Several recommended QC steps (global coupling residualisation, leave-one-out, within-medicated dose-response) remain outstanding.

= Relationship to companion studies

This is the third study in a series analysing resting-state EEG geometry in first-episode psychosis:

1. *Static geometry* @langell2026_psychosis: medicated FEP has a displaced average position in the metastability coordinate. This is about *where* the brain tends to sit.
2. *Trajectory geometry* @langell2026_trajectory: unmedicated FEP has elevated path cost (noetic action) during resting state. This is about *how* the brain moves.
3. *Coupling architecture* (this study): unmedicated FEP has reduced self-coupling in the entropy (and diffusivity) sub-system; medicated FEP has elevated entropy self-coupling and increased cross-family coupling into the entropy sub-system. This is about *which sub-systems govern which*.

The three studies are complementary: they expose different facets of the same medication-stratified neural geometry, each facet invisible to the others. None individually is a complete description of the geometry; together they suggest a picture in which:

- untreated psychosis involves a self-regulating entropy sub-system that is weakened and reactive,
- antipsychotic treatment normalises the movement grammar (trajectory action) while over-regulating the entropy sub-system,
- and the average neural state shifts (static position) are most visible in the medicated group regardless of the dynamic and coupling picture.

Whether these three geometric signals are causally linked to each other or independently driven by medication remains an open question.

= What an appropriate next step would look like

The most important clinical next step is linking the block Jacobian coupling metrics to clinical outcome measures — symptom severity scores, treatment response trajectories, or functional outcome at follow-up. If $e → e$ self-coupling correlates with negative symptom severity, it would provide evidence that the coupling metric captures a clinically relevant dimension of illness state. If dose-response within the medicated group is demonstrated, it would strengthen the causal attribution to antipsychotic mechanisms.

An independent replication in a larger cohort, preferably with longitudinal design (pre-treatment and post-treatment scans for the same subjects), would provide much stronger evidence for the medication-stratified coupling hypothesis.

#bibliography("../psychosis_first_time_geometric_trajectory/psychosis.bib", style: "apa")
