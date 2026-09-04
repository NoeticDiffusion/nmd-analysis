// Generic manuscript template.
// Usage: copy this folder to articles/<new article name>/, rename this file to
// the article title, and replace the placeholder metadata and section text.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "[Article title]",
  short-title: "[Short title <= 70 chars]",
  subtitle: "[Optional subtitle / one-line elaboration]",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "[keyword 1]",
    "[keyword 2]",
    "[keyword 3]",
    "[keyword 4]",
    "[keyword 5]",
    "[keyword 6]",
  ),
  article-type: "Research Article",
  abstract: [
    [Placeholder abstract. State the question, the dataset, the sample, the primary analysis, the main result with its effect size and p-value, the robustness/confound checks, and the interpretation. Keep to the journal's word limit (e.g. 200 words for Network Neuroscience).]
  ],
  author-summary: [
    [Placeholder author summary. One or two plain-language sentences on what was asked, what was found, and why it matters. Limited to 125 words for Research articles.]
  ],
  author-contributions: [RL: Conceptualization, Methodology, Data Curation, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted at submission.],
  data-availability: [Describe dataset sources (with DOIs), analysis scripts location, and pipeline availability.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

#set heading(numbering: "1.")
#set math.equation(numbering: "(1)")

= Introduction <sec:intro>

[Placeholder. Frame the scientific question, summarize the relevant prior work with citations, state what gap the present study addresses, and end with the core question in a `netn-box`.]

#netn-box(title: [Core question])[
  [State the single central question this article answers.]
]

= Theory <sec:theory>

== Theoretical framework and primary metric

[Placeholder. Introduce the theoretical framework and the primary metric(s) used. Define the core equation.]

$ d X_t = -nabla F(X_t, t) d t + sigma(t) d W_t $ <eq:core>

[Define each symbol and how the metric(s) are derived from it.]

== Embodied Anchoring Principle (if applicable)

[Placeholder. Include only if the article uses an EAP / secondary-physiology analysis. Otherwise delete this subsection.]

= Methods <sec:methods>

== Dataset

[Placeholder. Describe the dataset, sample size, conditions/tasks, recording modalities, sampling rates, and any dataset-version caveats. Cite the dataset with its DOI.]

== NMD pipeline

[Placeholder. Describe the NeuralManifoldDynamics run (run identifier, date), preprocessing (ICA, etc.), epoching window, and injected auxiliary channels.]

== Primary endpoints

[Placeholder. List the primary and secondary endpoints and how each is computed.]

== Statistical design

[Placeholder. Specify the unit of analysis, the contrast test (e.g. Wilcoxon signed-rank), the effect-size measure (e.g. Cohen's $d_z$), and the multiple-comparison correction (e.g. Benjamini-Hochberg FDR at $alpha = 0.05$).]

== Robustness protocol

[Placeholder. List the robustness checks: (1) intersection sample, (2) epoch-count matching, (3) leave-one-subject-out, (4) bootstrap CIs, (5) within-subject permutation, (6) artifact balance, (7) physiological confounds, (8) additional confound checks, (9) conventional-feature baseline, (10) event/response-rate sensitivity.]

== Secondary analysis

[Placeholder. Describe any secondary/exploratory analyses (e.g. EAP partial correlations). Mark them as pre-specified or exploratory.]

= Results <sec:results>

== R1: Data quality and coverage <sec:r1>

[Placeholder. Report epoch counts, subject counts per task, and QC pass rates. Use a `clean-table` for modality coverage.]

#figure(
  kind: table,
  clean-table(
    columns: (1.8fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center),
    inset: 5pt,
    table.header([*Modality*], [*Task A*], [*Task B*], [*Task C*]),
    [Modality 1], [%], [%], [%],
  ),
  caption: [Placeholder data-quality table. Report QC pass rates by task and modality.]
) <tab-qc>

== R2: Global coordinates <sec:r2>

[Placeholder. Report the global-coordinate task contrasts (often a null).]

== R3: Primary contrast <sec:r3>

[Placeholder. Report the primary-metric pairwise contrasts.]

#figure(
  kind: table,
  clean-table(
    columns: (1.8fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center),
    inset: 5pt,
    table.header([*Metric*], [*Task A vs B* $d$], [*p*], [*FDR*]),
    [`metric_1`], [0.00], [1.00], [-],
  ),
  caption: [Placeholder primary-contrast table. Cohen's $d$ as paired $d_z$. yes = survives FDR 5%.]
) <tab-primary>

== R4: Robustness and confound audit <sec:r4>

[Placeholder. Report the robustness-check results (intersection sample, epoch matching, LOOSO, bootstrap, permutation, artifact balance, confound partial correlations).]

== R5: Confound dissociation <sec:r5>

[Placeholder. Report the key confound check that dissociates the primary effect from a peripheral/alternative explanation.]

#netn-box(title: [Dissociation finding])[
  [State the dissociation in one sentence.]
]

== R6: Secondary analysis <sec:r6>

[Placeholder. Report secondary/exploratory analyses, with explicit FDR status.]

= Discussion <sec:discussion>

== Primary finding

[Placeholder. Interpret the primary result and what it shows that global coordinates did not.]

== Confound interpretation

[Placeholder. Discuss what the confound audit rules out and what it leaves open.]

== Secondary findings

[Placeholder. Interpret secondary results cautiously; label non-significant trends as such.]

== Limitations

[Placeholder. List the limitations: trial-level labels unavailable, sample size for secondary analyses, dataset-version discrepancies, untested alternatives, etc.]

== Conclusion

[Placeholder. Summarize what the article establishes, scoped to what the robustness checks support.]

= Acknowledgements

[Placeholder. Acknowledge dataset contributors, pipeline/toolbox authors, and funding.]

#bibliography("references.bib", style: "apa")
