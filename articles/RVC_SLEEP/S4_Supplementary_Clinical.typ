// S4 Supplementary Clinical Summary — RVC_SLEEP

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Summary",
  short-title: "S4 Clinical Summary - RVC_SLEEP",
  subtitle: "A cautious clinician-facing interpretation of the sleep-spindle geometry replication study",
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

#netn-box(title: [Important: observational study - no intervention tested])[
  This study tested *no* clinical intervention. All three cohorts (ANPHY, BOAS, RichSleep) are healthy, unselected overnight-PSG samples; no sleep stage, physiology, or brain state was manipulated. All reported findings are *observational, cross-sectional, and group-level*. No individual-level sleep-quality prediction is supported. No causal inference beyond the tested statistical associations is warranted.
]

This supplement is written for clinicians, sleep technologists, and clinically oriented readers who want to know what this study does and does not show, without needing to parse the statistical machinery in the main text and S1-S3. The goal is translation, not amplification: every claim below is scoped exactly as tightly as the main-text Results support it, and the framing limitations - healthy (non-clinical) samples, a correlational design, and research-only (non-diagnostic, non-validated) geometric metrics - apply throughout.

= What is the framework, and why does it matter here?

The analysis uses a geometric summary of moment-to-moment EEG state, called MNPS (Meta-Noetic Phase Space), which reduces the high-dimensional EEG signal at every 30-second window into a handful of numbers describing how "integrated vs. segregated," "variable," and "disordered" the brain's activity looks at that moment. This is conceptually related to, but distinct from, standard sleep-EEG measures like spectral power or sleep-stage labels: it is a summary of network-level geometric structure, not of any single frequency band. The clinically relevant question this study asks is narrow and specific: *does a well-known, transient EEG event (the sleep spindle) produce a reproducible shift in this geometric summary, and does the person's heart-rate/breathing state just before the spindle change how big that shift is?*

= What was studied

Three separate groups of healthy adults had a full night of PSG (polysomnography - simultaneous EEG, eye-movement, chin-muscle, heart, and breathing recording) in a sleep lab: 27 people (ANPHY), 128 people (BOAS), and 24 people (RichSleep, the newest and most completely instrumented of the three, with simultaneous heart-rate and breathing signals covering essentially the whole night for every participant). Automated software (YASA) detected sleep spindles - the short bursts of 11-16 Hz brain activity that occur during stage-2 (N2) sleep - in each recording. The geometric summary was then compared between spindle moments and two kinds of "control" moments: other N2 sleep from the same night with no spindle nearby, and the same spindle's own few seconds *before* it started.

= What the coordinates mean in plain language

- `d` and its sub-parts (`d_n`, `d_l`, `d_s`) - roughly, how far the brain's networks are from a balanced middle ground between "everything acting together" and "everything acting separately." A rising `d`-family value during a spindle means the brain's network organization is moving further from that balance point, briefly.
- `m` and its sub-parts - how variable/mobile the brain's state is from moment to moment.
- `e` and its sub-parts (`e_e`, `e_s`, `e_m`) - how disordered/entropic the signal looks, and (for `e_m` specifically) a mixed EEG-shape measure that, in one experimental configuration only (never in the main analysis), can be partly built from heart-rate or breathing signal instead of EEG.

= The main findings, in order of clinical salience

== 1. A specific geometric shift (`d_n`) rises at the spindle relative to its own pre-event baseline in two of the three groups

This is the headline finding, and it is a *two-dataset* result: in ANPHY and BOAS, the `d_n` geometric measure goes up at the spindle compared with the same spindle's own moment just before. In RichSleep the same timing comparison was underpowered and inconclusive (160 usable paired events vs. about 1,000 and 575 in the other two groups). That is not hidden here, and it is not treated as a contradiction of the ANPHY/BOAS result. This adds a geometric signature to what is already known about spindles from spectral/detector-based sleep research; it does not, by itself, tell us anything new about memory, cognition, or health outcomes.

== 2. This shift is not simply "any difference vs. generic N2 sleep" - it is more specific and more subtle than that

A broader comparison (spindle moments vs. generic non-spindle N2 sleep) also showed differences on most of the geometric measures, but a closer look showed that for several of them, this broader difference is mostly explained by how each group's *baseline* N2 sleep (just before a spindle) already differs from its generic N2 sleep - not by the spindle itself. Only the narrower "before vs. during the spindle" comparison (finding 1) isolates a genuine spindle-timed effect.

== 3. Heart-rate and breathing state just before a spindle: no moderation detected

Using the most completely instrumented of the three groups (RichSleep), we tested whether a person's autonomic state right before a spindle predicts a bigger or smaller geometric shift under tonic composite anchors. We did not detect that it does, on the primary dual-arm index or on the phase-resolved tests reported here (the latter at substantially lower power). The same tonic-anchor null was found earlier in the other two groups using a single heart-rate-only or breathing-only measure; this third test removes the concern that those earlier nulls were simply due to incomplete heart/breathing data. It does not rule out embodied-anchor coupling in general.

= What was NOT found - equally important

- No detected moderation of sleep spindles' geometric signature by cardiac or respiratory state beforehand, under the tonic composite anchors and underpowered phase-resolved tests reported here.
- No evidence, in this study, connecting the geometric shift to any clinical outcome, memory-test performance, or sleep-quality rating - none of those measures were collected or analyzed here.
- The "before vs. during spindle" timing replication in the third group (RichSleep) did not reach statistical significance on its own, most likely because that comparison only had a much smaller number of usable spindle events available than the other two groups - this is read as an underpowered test, not as a contradiction of findings 1-2 above.
- One secondary geometric measure (`e_e`) moved in *opposite* directions between the newest group and the two earlier groups in the broader (not the timing) comparison - an open, unresolved discrepancy, not hidden here.

= How to read the technical terminology clinically

- *"State-space reconfiguration"* means a measurable change in the geometric summary described above - not a change in consciousness level, memory encoding, or any directly measurable cognitive or clinical state.
- *"Embodied Anchor Principle (EAP) moderation"* is the specific, narrow hypothesis that was tested and *not supported*: that pre-spindle heart/breathing state changes the size of the EEG geometric shift. A null result here says nothing about heart-brain coupling in general, which is a much broader and separately well-established area of research; it only speaks to this one specific, narrowly defined test.
- *"FDR-significant"* is a statistical multiple-comparison correction, not a clinical-effect-size statement; a small, FDR-significant effect is not necessarily clinically meaningful, and this study makes no claim that any effect size reported here is clinically actionable.

= What clinicians should not conclude

- This study does *not* establish that the geometric measures reported here can diagnose, predict, or monitor any sleep disorder, cognitive condition, or clinical state.
- This study does *not* establish that heart-rate or breathing monitoring devices (e.g. wearables) can be used to infer or predict brain-state changes during sleep spindles - the opposite (a null result) was found for the specific test performed.
- No individual-level inference is supported; all results are group-level, subject-weighted averages with substantial between-subject variability (visible in the wide confidence intervals reported in the main text).
- None of the three cohorts includes a clinical or patient population; nothing here should be generalized to sleep disorders, neurological disease, or psychiatric conditions without dedicated replication in those populations.

= What would increase clinical confidence

- Replication of the `d_n` timing effect in a clinical population (e.g. insomnia, sleep apnea, or a neurodegenerative-disease cohort) with matched controls.
- A larger-$N$, adequately powered version of the RichSleep timing (A2r) replication, to resolve whether its current null is a true power limitation or a genuine discrepancy.
- Direct comparison of the geometric measures against an established, validated clinical sleep-quality or memory-consolidation outcome, which was outside the scope of this study.
- Investigation of the open `e_e` sign discrepancy between RichSleep and the two earlier cohorts, to determine whether it reflects a genuine dataset-specific difference (e.g. sleep-architecture fragmentation) or a technical/staging-protocol artifact.

= Summary for clinical readers

Across three independent, healthy-adult overnight sleep studies, a specific EEG-derived geometric measure rose at sleep spindles relative to each spindle's own pre-event baseline in two groups (ANPHY, 27 people; BOAS, 110 people on that timing test) and was inconclusive in the third (RichSleep, 24 people, 160 paired events). A separate test found no evidence that a person's heart-rate or breathing state just before the spindle changes the size of this shift under the tonic composite anchors and underpowered phase-resolved tests reported here. Neither finding currently supports any diagnostic, monitoring, or intervention use; both are offered as basic-science evidence for a specific, narrowly defined pair of hypotheses.

#bibliography("references.bib", style: "apa")
