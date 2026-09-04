// S4 Supplementary Clinical Summary — RVC_SLEEP_peak_analysis

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Summary",
  short-title: "S4 Clinical Summary - RVC_SLEEP_peak_analysis",
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
  This article reports a basic-science, mechanistic/methods-level result about the timing of a well-known EEG event (the sleep spindle) relative to breathing. It tested *no* clinical population, intervention, or outcome. The single dataset (RichSleep, 24 subjects) is healthy and unselected. Nothing here supports any diagnostic, monitoring, or intervention use.
]

= What was found, in plain language

Sleep spindles - brief bursts of brain activity during light-to-moderate sleep - tend to reach their *strongest* moment at a particular point in the breathing cycle (roughly a third of the way toward the top of an inhale), consistently across 24 healthy adults and several independent checks. This is a refinement of a companion study's earlier finding that the *start* of a spindle shows no such pattern - it turns out the timing signal is there, but only shows up when looking at the spindle's peak rather than its beginning. A weaker, less consistent version of the same idea was found for heartbeat timing. A separate, more tentative analysis found a hint - not yet a solid finding - that spindles occurring closer to this preferred breathing moment might also produce a slightly larger effect on the brain's own state-space geometry (the same geometric measure used in the companion study), but this needs independent confirmation before it should be trusted.

= Why this is not (yet) clinically actionable

- This is a *timing* finding about when, within a spindle, brain and breathing activity align - not a finding about memory, cognition, sleep quality, or any clinical outcome. None of those were measured or tested here.
- The single dataset is healthy, unselected, and observational; no sleep disorder, cognitive condition, or intervention was studied.
- The secondary, more clinically-adjacent question (does this timing predict anything about the spindle's own downstream effect?) returned only a fragile, partially-inconsistent hint (2 of 18 statistical tests, with mixed agreement across follow-up checks) - explicitly not strong enough to build on without independent replication.
- "Statistically significant" in this article, as elsewhere in this research program, is a multiple-comparison-corrected statistical statement, not a claim about clinical meaningfulness or effect size at the individual level.

= What would make this more clinically relevant

- Replicating the respiratory peak-phase timing effect in an independent, ideally larger and/or clinical (e.g. sleep-apnea, insomnia) PSG sample.
- A dedicated, pre-registered replication of the fragile secondary (alignment-moderation) result, ideally with a genuine endogenous spindle-strength covariate (e.g. slow-oscillation-spindle coupling), which is not available in the present data.
- Any demonstration that this timing relationship, or its downstream geometric consequence, differs between healthy and clinical populations - entirely untested here.

= Summary for clinical readers

This is a basic-science refinement of exactly *where within a sleep spindle* a breathing-related timing signal appears (its peak, not its onset), replicated across four independent robustness checks in one healthy 24-subject dataset. A secondary, much more tentative hint that this timing might also relate to the spindle's downstream brain-state effect is reported honestly as fragile and unconfirmed. Neither result currently supports any diagnostic, monitoring, or intervention use.

#bibliography("references.bib", style: "apa")
