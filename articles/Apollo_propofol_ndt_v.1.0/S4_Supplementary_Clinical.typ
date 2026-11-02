// S4 Supplementary Clinical Summary — Apollo propofol occupancy.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Summary",
  short-title: "S4 Clinical - Apollo propofol occupancy",
  subtitle: "A cautious clinician-facing interpretation of the occupancy result",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Scope and intent

#netn-box(title: [Important: healthy-volunteer sedation - not a monitoring study])[
  This is a secondary analysis of published EEG from 20 healthy adults sedated with propofol in
  a laboratory protocol. No clinical intervention was tested. No individual-level prediction is
  supported. Occupancy is not a depth-of-anaesthesia index, not a consciousness biomarker, and
  not a tool for titration.
]

This supplement is for clinically oriented readers. The goal is translation without
amplification. The sample is healthy volunteers, the design is within-subject observational
across protocol phases, and the main metric is a research occupancy scalar in a baseline-fixed
spectral chart. It was selected post hoc, so the reported contrasts are exploratory rather than
confirmatory.

= What is the framework, and why does it matter here?

Anaesthesia research often asks whether the brain has “less capacity” or is “less accessible”
under propofol. Those phrases mix three different facts: the measured state has moved, behaviour
has changed, and the local dynamical law may or may not have changed. This article keeps those
apart. Occupancy asks only whether the measured spectral pattern has left its awake
neighbourhood.

= What was studied

Twenty adults, four EEG sessions each: before drug, first protocol sedation, later protocol
sedation, and recovery, with blood propofol levels and a 40-trial auditory discrimination task
@chennu2016propofol. We did not collect new recordings.

= What occupancy means in plain language

Occupancy is how far a participant's current EEG spectral pattern sits from that same person's
pre-drug pattern, after a robust, within-person scaling. Larger occupancy means a larger
displacement in that chart, not “more unconscious.”

= The main findings, in order of clinical salience

== 1. Propofol moves the spectral pattern in an ordered way

Displacement increases from baseline to first sedation to later sedation, then only partly
returns during recovery. This is a protocol-phase trajectory, not a clinical depth scale.

== 2. Exploratory responsiveness analysis

The original 7 versus 13 drowsy/responsive split is recoverable from the task scores. The
exploratory data provide no evidence of a monotonic occupancy association with that split, but
the impaired arm is small and this does not establish that an association is absent. Some people
remain accurate despite very large displacement; some become impaired with similar or smaller
displacement.

== 3. We cannot yet say whether local dynamics change at a comparable state

Most participants have too little overlap between awake and sedated spectral patterns for a
fair “same state, different future?” test. That is a measurement boundary, not evidence that
dynamics are unchanged.

= What was not established

No monotonic occupancy association with behavioural responsiveness was detected in this
exploratory sample, but absence of association was not established. Protocol phase 3 is not
unresponsiveness. Local-chart reductions in drift/diffusion did not survive FDR and did not
survive a baseline-fixed reference. No consciousness claim is made. Feature-level contributions
and three bounded scaling/feature diagnostics were assessed in a post-hoc computational branch;
they supported stability of the reported scalar for those choices but are not clinical validation
or evidence that other feature sets, preprocessing, or cohorts would agree.

= What clinicians should not conclude

Do not use occupancy for titration, awareness monitoring, or prognosis. Do not treat a large
occupancy value as proof of unresponsiveness. Do not treat incomplete occupancy return at
recovery as residual anaesthesia without a behavioural or pharmacokinetic reading.

= What would increase clinical confidence

Prospective lock of the occupancy scalar, larger samples with a balanced impaired arm,
independent behavioural endpoints, replication of the sensitivity branch in an independent cohort,
and a chart in which matched-state dynamics can actually be tested.

= Summary for clinical readers

In this laboratory propofol dataset, the EEG spectral pattern reliably leaves the awake
neighbourhood and only partly returns. The exploratory data provide no evidence that this
displacement is a monotonic marker of behavioural responsiveness, but the analysis cannot rule
out an association. Occupancy is a research description of state relocation, not a clinical
marker.

#bibliography("references.bib", style: "apa")
