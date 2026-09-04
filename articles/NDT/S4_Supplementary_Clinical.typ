// S4 Supplementary: Related work and comparative theoretical positioning.
// Moved out of the NoeticDiffusionTheory.typ main-text Appendix to keep the
// main article focused on Tier-1 claims.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S4 Supplementary: Related Work",
  short-title: "S4 Related Work - NDT",
  subtitle: "NDT in relation to dynamical-systems/landscape accounts, predictive-processing/active-inference frameworks, and integrated-information/network-control approaches",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

#set par(leading: 0.8em, spacing: 0.6em)

#netn-box(title: [Relation to the main article])[
  This supplement expands the *Related work* appendix pointer from the main
  article (`NoeticDiffusionTheory.typ`, Appendix).
]

= S4.0 Related work

NDT is closest to dynamical-systems and landscape accounts of brain activity,
where cognition is modeled as movement through metastable state spaces
@deco2011emerging @kelso2012multistability. Its distinctive addition is a
rhythmic variance schedule: instead of treating noise as constant or exogenous,
NDT asks whether neural rhythms provide an observable control signal that gates
exploration and denoising over short time windows.

Predictive-processing and active-inference accounts provide an important
neighboring framework @friston2010free @clark2013whatever @seth2013interoceptive.
NDT is compatible with these accounts but shifts the emphasis from content-level
prediction to trajectory geometry, variance timing, and empirical state-space
readouts. Integrated-information and network-control approaches are also
complementary: they foreground information structure or transition energy,
whereas NDT focuses on event-locked flow, topology, recurrence, and reachability
in measured neural trajectories @tononi2016integrated @gu2015controllability.

The comparison should be read conservatively. NDT does not claim to replace
these frameworks, nor to solve the hard problem of consciousness. Its proposed
contribution is a narrower measurement hypothesis: if rhythmic variance control
is a real organizing principle, then event-locked entropy signatures and MNPS
geometry should survive preregistered null models better than smooth-precision
or rhythm-free alternatives.

= S4.1 Companion-evidence ledgers (clinical and rhythm-related)

Alongside the theoretical comparison above, four internal evidence-survey
ledgers catalog which companion manuscripts under `articles/CLINICAL/`,
`articles/RVC_SLEEP*`, `articles/RichSLeep_EAP_v2/`, and related folders can
serve as *bounded, dataset-level* empirical material for Signature Prediction
4 (clinical geometry contrasts) and the RVC/EAP rhythm claims. Each ledger
follows the project's five-way evidence discipline (established / internal
validated / plausible / speculative / rejected) and explicitly separates
positive findings from negative and null results.

- *Coma/cardiac-arrest geometry* — `articles/NDT/parts/007_20260809_clinical_coma_evidence_survey.md`.
  Pooled reachability/MNJ contrasts between good and poor neurological
  outcome are internal validated, dataset-bounded associations; they are
  *not* a test of the main article's Grand Mal boundary note and do not
  validate MNDM, RVC, or TRN mechanics.
- *Non-coma clinical disorders* (psychosis, depression, Parkinson,
  Alzheimer/FTD) — `articles/NDT/parts/008_20260809_clinical_disorder_evidence_survey.md`.
  Medication-stratified psychosis geometry and BDI-linked depression
  reachability support Signature Prediction 4's *existence* claim, but do
  not confirm the illustrative Mapper/DET or $d > 0.6$ volume-collapse
  operationalizations as literally written; several companions report
  informative null results.
- *Sleep rhythms and autonomic phase-locking* — `articles/NDT/parts/009_20260809_sleep_rhythm_evidence_survey.md`.
  Spindle-locked MNPS reconfiguration and carrier-specific autonomic
  phase-locking (SO trough $>$ spindle peak $>$ spindle onset $approx$
  REM-theta null) are internal validated; none of these companions
  validate the explicit $hat(r)(t)$ construction from the main article's
  RVC section or a TRN causal mechanism.
- *EAP, development, and task geometry* — `articles/NDT/parts/010_20260809_eap_developmental_task_evidence_survey.md`.
  Wake EAP co-modulation, encoding-pace task geometry, and developmental
  MNPS trajectories are internal validated at the condition level, with
  explicit nulls for direct within-subject anchor-to-performance coupling
  and for age-related MNJ/reachability change.

These ledgers are maintained as living documents; editors updating Signature
Prediction 4 or the RVC/EAP sections should consult them before adding or
strengthening any clinical or rhythm-linked citation.

#bibliography("references.bib", style: "apa")
