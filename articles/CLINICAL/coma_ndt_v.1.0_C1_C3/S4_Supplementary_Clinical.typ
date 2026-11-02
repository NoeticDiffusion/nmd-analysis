// S4 Supplementary Clinical Summary — generic template.
// Rename and replace placeholders per article. Keep the cautious tone.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Summary",
  short-title: "S4 Clinical Summary - [short article tag]",
  subtitle: "A cautious clinician-facing interpretation of the article",
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
  This study tested *no* clinical intervention. Participants performed ordinary laboratory conditions; no physiology or brain state was manipulated directly. All reported findings are *observational, cross-sectional, and group-level*. No individual-level predictions are supported. No causal inference beyond the tested associations is warranted.
]

[Placeholder. State that this supplement is written for clinicians and clinically oriented readers, that the goal is translation not amplification, and list the framing limitations: healthy vs. clinical sample, correlational design, non-validated research metrics.]

= What is the framework, and why does it matter here?

[Placeholder. Plain-language explanation of the theoretical framework and why a clinician should care.]

= What was studied

[Placeholder. Dataset, sample, conditions, and recording modalities in plain language.]

= What the coordinates mean in plain language

[Placeholder. Translate each coordinate / metric into a plain-language description.]

= The main findings, in order of clinical salience

== 1. [Primary finding in plain language]

[Placeholder.]

== 2. [Confound / dissociation finding]

[Placeholder.]

== 3. [Secondary finding, if any]

[Placeholder.]

= What was NOT found - equally important

[Placeholder. State the nulls and the non-significant trends explicitly.]

= How to read the technical terminology clinically

[Placeholder. Map the key technical terms to clinically meaningful concepts, with caution about over-interpretation.]

= What clinicians should not conclude

[Placeholder. List the inference errors a clinician should avoid (causal claims, individual-level prediction, diagnostic use).]

= What would increase clinical confidence

[Placeholder. Replication in patient samples, longitudinal designs, validated biomarker testing, intervention studies.]

= Summary for clinical readers

[Placeholder. One-paragraph balanced summary.]

#bibliography("references.bib", style: "apa")
