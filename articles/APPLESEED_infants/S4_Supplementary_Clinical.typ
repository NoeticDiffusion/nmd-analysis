#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S4 Developmental Interpretation",
  short-title: "APPLESEED developmental scope",
  subtitle: "A cautious reader-facing summary",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Scope
#netn-box(title: [Research reanalysis, not a clinical test])[
  This is a secondary analysis of a small public infant EEG example dataset. It tested no intervention, provides no diagnostic threshold, and makes no individual-level prediction. No causal developmental mechanism is established.
]

This supplement translates the analysis boundary rather than amplifying the findings. The participants are not a clinical cohort, and the NDT-derived summaries are research measurements without clinical validation.

= What was studied
Thirteen infants each had two recordings approximately one week apart at four months. Eleven returned at approximately eight and twelve months. The analysis asked whether session-level local-flow and reachability summaries were stable in the short interval and changed within the same children at later assessments.

= What the measures mean
The MNJ is a local mathematical summary of how the exported EEG feature chart changes close to a given chart location. Reachability summarizes the local variation predicted by a fitted short-horizon transition model. Neither quantity is a direct measure of consciousness, cognition, disease, maturity, or prognosis.

= Main findings
Test--retest agreement was endpoint-dependent and imprecise in this 13-child sample: some point estimates were moderate or high, but the bootstrap intervals were broad and often included zero. No primary 3D MNJ/reachability contrast at eight or twelve months survived its nine-endpoint false-discovery-rate sensitivity correction in the 11-child longitudinal panel. Separately, the cohort-anchored mobility coordinate decreased in all 11 children from the four-month mean to twelve months (raw p=0.00098; BH p=0.0029 within the three-coordinate family). This is a chart-level common-scale result with moderate coordinate reliability, not evidence for a latent neural or maturational mechanism.

= What was not found
The study found no corrected primary MNJ/reachability endpoint difference over time. It did not test diagnostic separation, treatment response, clinical outcome prediction, or a link between the features and behavior. The mobility result should not be read as a normative group trajectory: the global IQR anchor includes all study ages, and nominal age strata are not individually measured ages.

= Appropriate next step
A confirmatory developmental study should prespecify a small endpoint set, use a larger longitudinal cohort, retain repeated recordings per age, test anchor stability across visits, and relate any reliable measure to independent behavioral/developmental outcomes.
