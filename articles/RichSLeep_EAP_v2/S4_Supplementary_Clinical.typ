// S4 Supplementary Clinical Summary — RichSleep_EAP_v2

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Summary",
  short-title: "S4 Clinical Summary - RichSleep_EAP_v2",
  subtitle: "A brief, cautious clinician-facing note on this mechanistic/methods-level finding",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

#netn-box(title: [Important: not yet a clinical finding])[
  This article reports a basic-science, mechanistic/methods-level survey of how brain rhythms during sleep relate to breathing and heartbeat timing. It tested *no* clinical population, intervention, or outcome. The single dataset (RichSleep, 24 subjects) is healthy and unselected. Nothing here supports any diagnostic, monitoring, or intervention use.
]

= What was found, in plain language

Slow brain waves that occur during the deepest stage of sleep (slow oscillations) line up strongly and consistently with a particular point in the breathing and heartbeat cycle - more strongly than anything else measured in this research program so far, across 24 healthy adults. A memory-related rhythm that occurs during dream sleep (REM theta) showed no such link at all. For the sleep spindle - a shorter burst of brain activity in lighter sleep, studied in a companion article - three different, individually reasonable ways of testing whether its very *start* lines up with breathing/heartbeat gave three different answers; rather than picking the one we prefer, we report the disagreement itself as the finding. Finally, a separate check asked whether a spindle's own intrinsic strength changes how much a preferred-timing effect (found in the companion study) shows up in the brain's state-space geometry: it does not, at least not detectably with the data available.

= Why this is not (yet) clinically actionable

- This is a *timing* finding about when different sleep rhythms align with breathing/heartbeat - not a finding about memory, cognition, sleep quality, or any clinical outcome. None of those were measured or tested here.
- The single dataset is healthy, unselected, and observational; no sleep disorder, cognitive condition, or intervention was studied.
- The one question with the most attempted rigor - whether spindle onset timing predicts anything - produced three disagreeing answers rather than one, which is reported honestly as unresolved rather than as a clean result to build on.
- The strength-moderation check (does a stronger spindle show a bigger timing-related effect on brain-state geometry) was clean-null across three different ways of measuring "strength" - explicitly not evidence that intrinsic strength matters, nor that it doesn't; only that no such interaction was detected at current sample size.
- "Statistically significant" in this article, as elsewhere in this research program, is a multiple-comparison-corrected statistical statement, not a claim about clinical meaningfulness or effect size at the individual level.

= What would make this more clinically relevant

- Replicating the slow-oscillation timing result in an independent, ideally larger and/or clinical (e.g. sleep-apnea, insomnia, dementia-risk) PSG sample - this is the strongest and most replication-worthy result in this article.
- A substantially larger slow-oscillation-spindle-coupled event yield (this article's coupled subset, 25 events/15 subjects, was too small for a confirmatory test), to properly power a genuine strength-moderation test.
- Resolving, rather than merely reporting, the three-way disagreement on spindle-onset timing - e.g. with a purpose-built, pre-registered null construction chosen in advance of seeing any result.
- Any demonstration that carrier-specific autonomic phase-locking, or its downstream geometric consequence, differs between healthy and clinical populations - entirely untested here.

= Summary for clinical readers

This is a basic-science survey of *which* sleep rhythms show timing links to breathing/heartbeat (strongest for slow oscillations, essentially absent for REM theta, and unresolved for sleep-spindle onset), together with a clean-null check of whether spindle strength moderates a companion study's more tentative timing-geometry link. None of this currently supports any diagnostic, monitoring, or intervention use; the slow-oscillation result is the most clinically-promising thread for future replication work.

#bibliography("references.bib", style: "apa")
