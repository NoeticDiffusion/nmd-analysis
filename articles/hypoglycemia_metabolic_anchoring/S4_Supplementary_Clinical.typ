#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Summary",
  short-title: "S4 Clinical Summary - hypoglycemia dynamics",
  subtitle: "A cautious clinician-facing interpretation of the paired EEG reanalysis",
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

#netn-box(title: [Important: controlled condition contrast, not a clinical test])[
  The source study used a hyperinsulinemic euglycemic--hypoglycemic clamp.
  This reanalysis compares two five-minute EEG excerpts per participant; it did
  not administer a new intervention or collect new clinical measurements. The
  comparison is paired and condition-associated, but the excerpts do not
  provide a glucose dose-response, recovery trajectory, awareness subgroup, or
  individual-level prediction. The research coordinates are not validated
  clinical biomarkers.
]

This supplement is written for clinicians and clinically oriented readers. Its
goal is translation, not amplification: it describes what the EEG contrast
shows, what the computational summaries mean operationally, and which clinical
inferences remain unsupported. The cohort contains people with type 1 diabetes,
but the analysis has no participant-level glucose, symptom, cognitive,
awareness, recovery, or demographic metadata.

= What is the framework, and why does it matter here?

The pipeline places each short EEG window on a fixed, multidimensional
feature chart. It then summarizes both the location of a recording on that
chart and the local pattern of change between windows. This separation matters
because increased slow-wave power can coexist with reduced entropy or altered
mobility; no single rhythm should be assumed to represent preserved neural
function. The chart is a research representation of processed EEG, not a
direct image of a brain state.

= What was studied

The dataset contains 34 people with type 1 diabetes and two separately
excerpted five-minute scalp-EEG recordings per person: euglycemia and
hypoglycemia. The frozen ingest staged 19 channels at 200 Hz, with seven
channel identities confirmed in the provenance and the remaining labels
mapped by best-effort convention. Filtering, epoching, and artifact handling
differed from the source paper, so this is a bounded reanalysis rather than a
direct reproduction of its entire preprocessing pipeline.

= What the coordinates mean in plain language

The 3D chart reports three operational families: mobility ($m$), deviation
($d$), and an entropy-related coordinate ($e$). The 9D chart splits these into
three subcomponents each. These names describe feature aggregates, not
established biological functions. In this EEG-only run, $e_e$ is the exported
permutation-entropy coordinate and $e_s$ is the contract's Hjorth-complexity
slot. The $e_m$ field is a bounded energy/arousal-related high-frequency EEG
proxy; it is not a peripheral embodied measure and is not itself an entropy
estimator.
The frozen contract clipped standardized features at 6.0, and three
hypoglycemia sessions reached that ceiling for $e_m$.

= The main findings, in order of clinical salience

== 1. A multicomponent EEG chart changed under hypoglycemia

Coarse mobility was lower under hypoglycemia ($Delta m = -0.743$,
$q = 0.00090$). The detailed chart showed lower $m_a$, $m_e$, and $e_e$ and
higher $d_n$ and $e_m$. This is a reproducible paired contrast on this frozen
measurement surface, not a diagnostic signature.

== 2. Slow power and chart coordinates should not be conflated

Raw EEG checks showed higher theta and delta power, together with lower
exported entropy measures. Some mobility-family coordinates may share
spectral inputs with those checks, so the pattern is not an independent
physiological dissociation. It does show why higher slow-wave power alone
cannot be interpreted as stronger coordination or preserved cognition.

== 3. Local dynamics and reachability remain bounded

The 3D Jacobian endpoints were not FDR-supported. The 9D Jacobian family
showed exploratory lower operator, Frobenius, and rotation medians. The
reachability export was available for 33 pairs but failed its frozen
split-half validity criteria in all participants. Its nominal effective
dimension and directional entropy were higher, not lower, and are not
confirmatory evidence.

= What was NOT found - equally important

No validated reachability collapse, glucose threshold, dose-response,
recovery trajectory, impaired-awareness subgroup, autonomic warning signal, or
metabolic adequacy gate was identified. The analysis did not measure
consciousness, cognition during the excerpts, interoception, cardiac or
respiratory signals, or regional brain physiology. The pooled feature anchor
also makes euglycemia a comparison condition, not an external physiological
zero.

= How to read the technical terminology clinically

*Paired contrast* means that each participant is compared with themself across
the two condition excerpts. *FDR q-value* is a multiplicity-adjusted result
within an engine analysis block; the reported engine q-values include all
exported summaries, not only the median rows shown in S2. *Jacobian* describes
the local derivative of the fitted feature-chart flow. *Reachability* is a
model-propagated short-horizon covariance summary, not observed behavior,
brain connectivity, or a clinical capacity measure. *Validity-limited* means
that the exported result did not meet its prespecified internal reliability
criteria.

= What clinicians should not conclude

Clinicians should not use these coordinates to diagnose hypoglycemia, predict
an individual's cognition or consciousness, infer impaired awareness, or
estimate glucose concentration. They should not interpret $m$, $e$, or
reachability as direct measures of neural capacity, and should not cite this
reanalysis as evidence for an embodied-anchoring mechanism or a causal
metabolic gate.

= What would increase clinical confidence

Confidence would require an independent sample with continuous glucose and
rate-of-change measurements, clamp timing, symptom and cognitive measures,
autonomic/interoceptive signals, and recovery recordings. A future analysis
should predefine an euglycemia-only anchor, validate the reachability contract
on longer recordings, disclose channel identity and feature mappings, and test
whether the research coordinates add information beyond conventional EEG
features and simpler condition models.

= Summary for clinical readers

In this paired reanalysis of 34 people with type 1 diabetes, hypoglycemia was
associated with a reproducible change in a fixed, multicomponent EEG feature
chart and with higher low-frequency power. The detailed coordinate pattern was
mixed rather than a uniform collapse, and the reachability export was
validity-limited. The findings support a bounded condition-associated EEG
signature under one computational contract; they do not support individual
clinical prediction, a glucose dose-response, a recovery claim, a metabolic
gate, or a conclusion about consciousness.

#bibliography("references.bib", style: "apa")
