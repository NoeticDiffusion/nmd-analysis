#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S5 — Glossary",
  short-title: "Glossary — ds004587 EAP",
  subtitle: "Operational terms and evidence boundaries",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("glossary", "EAP", "MNDM", "MNPS", "visual illusion"),
  article-type: "Supplementary Material",
  abstract: [Definitions for the operational constructs used in the ds004587 EAP analysis scaffold. Definitions distinguish implemented measurements, permitted interpretations, and claims not established by this observational design.],
)

#set heading(numbering: none)

_Reading rule._ An *implemented* entry describes a versioned calculation. An *interpretation* states its narrow empirical reading. A *not established* entry identifies inferences the present study cannot support.

= A -- D

*Anchor feature* — A physiology-derived measured variable aligned to the neural analysis grid, such as an ECG, PPG, or respiratory summary. *Not established:* a direct measure of EAP strength, interoceptive awareness, or causal control of neural dynamics.

*Association* — A statistical relation between measured variables. In this study, an association can be within participant or between participant and must state its time scale and correction family. *Not established:* temporal precedence or causality.

*BH-FDR* — Benjamini--Hochberg false-discovery-rate correction, used within explicitly declared endpoint families. A threshold of $q < 0.05$ controls the expected false-discovery proportion under its assumptions. @benjamini1995

*BIDS provenance* — The traceable relationship between an analysis row and its source participant, session, run, event, behavioral record, and data-release version.

*Condition contrast* — A comparison between rest and illusion-perception summaries. It is not an illusion-specific neural mechanism because the conditions differ in visual input, eye state, engagement, and response demands.

= E -- L

*EAP (Embodied Anchoring Principle)* — A speculative NDT extension proposing that cardiac and respiratory state may constrain neural dynamics. *Implemented here:* only candidate measured physiological proxies and conditional association tests. *Not established:* cycle-level entrainment, causal gating, or a unique physiological-to-neural pathway.

*Epoch* — A defined time interval of a continuous recording. Its duration, overlap, and condition assignment must be frozen in the run manifest before inference.

*Geometry contract* — The run-level validity metadata that states whether a specified neural-geometry output, especially a Jacobian, meets the pipeline's operational requirements. A failed contract makes that endpoint unavailable, not null.

*HRV (heart-rate variability)* — Variation in NN intervals derived from ECG R peaks. Its interpretation depends on R-peak quality, artifact handling, integration window, and stationarity. @taskforce1996

*Illusion strength* — A dataset-defined stimulus parameter intended to manipulate the contextual bias of a visual illusion. An association with this label is not proof of subjective illusion sensitivity unless the behavioral mapping is verified.

= M -- R

*MNDM* — The versioned computational pipeline used to export operational neural-coordinate, local-flow, and optional physiological surfaces. Its output schema and configuration are part of the measurement definition. @langell2026nmd

*MNJ (Meta-Noetic Jacobian)* — The estimated local Jacobian of an operational neural flow field. A common magnitude summary is $||J||_F = sqrt(sum_(i,j) J_(i j)^2)$. *Interpretation:* a model-dependent local deformation summary. *Not established:* direct physical force, stability, or cognitive efficiency.

*MNPS coordinate* — One component of the exported three-coordinate neural chart, conventionally $(m, d, e)$. *Interpretation:* a versioned chart coordinate. *Not established:* a directly observed latent psychological dimension.

*Null result* — An estimated effect that does not meet a declared decision threshold. It does not demonstrate equality or absence of all plausible effects; precision and confidence intervals are required.

*PPG (photoplethysmography)* — An optical peripheral pulse signal. Quality, sensor placement, and its relation to ECG must be documented before it is used as an anchor feature.

*Respiratory phase* — Instantaneous position within a respiratory cycle. It requires an explicit extraction method and validated timing alignment; it cannot be inferred from a session-level respiration-rate summary.

= S -- Z

*Synchronization gate* — A prespecified decision requiring adequate evidence for EEG--physiology timing alignment before event-, phase-, lag-, or direction-sensitive analyses are run.

*Variance schedule* — In the EAP/NDT theoretical notation, $sigma(t)$ controls stochastic variability in a state-dynamics equation. *Not established here:* an observed or causally identified biological variance schedule.

*Wilcoxon signed-rank test* — A nonparametric paired test used for the planned participant-level rest--illusion contrast. It tests a paired distributional shift under its assumptions and is reported with an effect size and interval. @wilcoxon1945

#bibliography("references.bib", style: "apa")
