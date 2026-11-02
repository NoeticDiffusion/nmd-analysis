// S3 Supplementary QC and Robustness — generic template.
// Rename and replace placeholders per article.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "S3 QC/Robustness - [short article tag]",
  subtitle: "Quality control, robustness/confound audit, and reviewer-facing robustness summary",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S3.0 Sample and epoch coverage overview

[Placeholder. Subject counts per task, epoch counts (mean/median/range), and the intersection-sample size used for the confound audit.]

#figure(
  clean-table(
    columns: (1.6fr, 1fr, 1fr, 1fr, 1fr),
    table.header([*Task*], [*$N$ subj. (valid)*], [*Mean ep./subj.*], [*Median ep./subj.*], [*Range*]),
    [Task A], [`[TBD]`], [`[TBD]`], [`[TBD]`], [`[TBD]`],
  ),
  caption: [Placeholder epoch-coverage table. Source: `[results path]`.]
) <tab-epoch-coverage>

= S3.1 Physiological QC pass rates

[Placeholder. QC pass rates by modality and task. Reference the QC figure.]

= S3.2 EEG/EOG artifact balance across tasks

[Placeholder. EOG QC, blink rate, and high-frequency-power (EMG proxy) balance by task.]

= S3.3 Robustness and confound audit (full results)

[Placeholder. Full results for each audit part listed in S1.6: intersection sample, epoch-count matching, LOOSO, bootstrap CIs, within-subject permutation, artifact balance, physiological confounds.]

=== Intersection sample and epoch matching

[Placeholder.]

=== Leave-one-subject-out and bootstrap

[Placeholder.]

=== Within-subject permutation

[Placeholder.]

=== Artifact balance

[Placeholder.]

=== Physiological confound controls

[Placeholder.]

= S3.4 Follow-ups

[Placeholder. Dedicated follow-up scripts, each reported in its own subsection.]

== S3.4a Auxiliary confound follow-up (Script A detail)

[Placeholder.]

== S3.4b Additional confound follow-up (Script B detail)

[Placeholder.]

== S3.4c Conventional-feature baseline comparison (Script C detail)

[Placeholder. A baseline effect-size comparison, not a test of incremental predictive validity.]

== S3.4d Event/response-rate sensitivity follow-up (Script D detail)

[Placeholder.]

= S3.5 Reviewer-facing robustness summary

#netn-box(title: [Robustness summary])[
  [Placeholder. One-paragraph summary of which checks the primary effect survived and which alternatives were narrowed or closed.]
]

#bibliography("references.bib", style: "apa")
