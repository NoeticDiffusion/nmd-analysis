#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Context",
  short-title: "Trajectory Psychosis Clinical Context",
  subtitle: "Cautious clinician-facing interpretation of trajectory geometry results",
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

This supplement translates the manuscript's trajectory-geometry findings into cautious clinician-facing language. It is intended for reviewers or readers who wish to understand the clinical implications without engaging with the mathematical formalism. It is deliberately conservative about what has and has not been established.

= What the study measured

Each subject in this study has a five-minute resting EEG recording. NeuralManifoldDynamics 2.1 converts those recordings into a three-dimensional coordinate sequence that represents how the brain's collective neural state evolves over time. Rather than asking where the subject's brain tends to sit on average (the focus of the companion study), this study asks how the brain moves: how quickly, how predictably, how reversibly, and with what energetic cost.

The specific metrics are:

- *Entropy rate*: how unpredictably the brain's state transitions from one region to another during rest. Higher entropy rate means more random, less stereotyped transitions.
- *Temporal irreversibility*: whether the sequence of states looks different when played forward versus backward in time. A more irreversible trajectory is more directed and non-equilibrium.
- *Noetic action*: a summary of the total cost or effort of the state-space trajectory. It combines a measure of how fast the state moves, how abruptly it changes direction (jerk), and where it sits in the state space. Higher action means a more costly or more energetically demanding trajectory.

= What the study found

In the larger and better-powered cohort (`ds003944`):

- Unmedicated first-episode psychosis patients had higher noetic action than healthy controls ($d = 0.77$, $p = 0.006$). This means their resting brain trajectories require more effort or cost, in the metric's terms, than healthy controls.
- Medicated first-episode psychosis patients did not show this elevation. Their trajectories were not significantly different from healthy controls in any of the primary metrics.
- Medicated patients tended to have lower trajectory jerk and lower irreversibility than unmedicated patients, though these comparisons did not reach statistical significance.

In the smaller cohort (`ds003947`), medicated patients showed a trend toward lower entropy rate than unmedicated patients, consistent with the pattern above, but the unmedicated group was too small ($n = 8$) for reliable conclusions.

= What this may mean clinically

This is an exploratory result and should not be interpreted as a biomarker or a clinical test. However, the pattern is consistent with a specific mechanistic idea: antipsychotic drugs may normalise the moment-to-moment dynamics of neural state-space traversal while leaving a residual shift in the average neural state. The companion study found that medicated FEP patients have a displaced average neural state but normal trajectory dynamics. The present study shows the complementary result: unmedicated FEP patients have elevated trajectory dynamics but a less clearly displaced average state.

One interpretation, consistent with aberrant salience models of psychosis, is that unmedicated psychosis involves episodic, abrupt redirections of neural state — captured here as elevated trajectory action and jerk — which antipsychotic drugs specifically reduce. This interpretation is plausible but not established by the present data. It should be treated as a hypothesis for future targeted investigation.

= What this study cannot claim

This study *cannot* claim:

- that noetic action is a validated biomarker for psychosis, medication state, or treatment response,
- that the specific metric values are interpretable in biologically absolute terms,
- that higher noetic action in unmedicated FEP reflects a specific neural circuit or neurotransmitter mechanism,
- that the result would replicate in an independent cohort or clinical sample,
- or that the jerk component specifically (as opposed to the total action) is the relevant signal.

The primary result ($q = 0.052$) narrowly missed the BH-FDR threshold. The temporal shuffled-null test — which would verify that the result depends on real temporal ordering rather than on which states are visited — has not been carried out. These are mandatory steps before the result can be treated as established.

= Relationship to established EEG and clinical literature

The present trajectory approach is complementary to, not a replacement for, established electrophysiological markers in psychosis, such as mismatch negativity reduction, gamma-band dysfunction, auditory steady-state response abnormalities, and resting alpha-band changes @tada2019mmn @grent2018gamma @zouaoui2023assr @sponheim1994resting. Those markers are better validated, replicated across larger samples, and linked to specific cognitive and clinical outcomes. The present trajectory framework adds a new organisational layer — a low-dimensional picture of how neural state moves over time — but it does not supersede existing markers and has not been validated against clinical outcomes or symptom severity in the current analysis.

The observation that medicated FEP has normalised trajectory dynamics is consistent with prior literature showing that antipsychotics can normalise some resting EEG measures (e.g., alpha power, mismatch negativity) while not fully restoring all neurophysiological parameters to healthy levels @centorrino2002eeg @ozaki2021qEEG_antipsychotics. The trajectory framework translates this clinical observation into a low-dimensional geometric picture, but the mechanistic specificity of that picture remains limited.

= What an appropriate next step would look like

The most important next step is independent replication in a larger unmedicated FEP sample, ideally with:

- a pre-specified primary endpoint (total noetic action, subject-anchored 3D coordinates),
- a time-shuffled null test to validate temporal specificity,
- residualisation of `noetic_action_potential` against static MNPS coordinate means,
- and clinical outcome data to test whether trajectory action predicts treatment response or symptom severity over time.

Without these steps, the present result should be treated as a hypothesis-generating pilot, not as an established finding.

#bibliography("psychosis.bib", style: "apa")
