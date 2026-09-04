// S5 Glossary — generic template.
// Shared terminology across articles. Living document: update to match the
// current MNDM pipeline version, and note version-specific changes in entries.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S5 - Glossary",
  short-title: "Glossary",
  subtitle: "Shared terminology across articles",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("glossary", "NDT", "MNDM", "MNPS", "embodied anchoring"),
  article-type: "Supplementary Material",
  abstract: [
    This document defines the core terminology used across articles in this repository. Entries cover the theoretical framework, the computational pipeline, embodied anchor metrics, the family of primary metric scalar summaries, trajectory geometry, robustness-audit methods, and statistical methods. Definitions reflect the current implementation as of the latest pipeline version; version-specific changes to metric computation are noted in the relevant entry.
  ],
)

#set heading(numbering: none)

_Note: This is a living document. Definitions are updated to match the current pipeline version. Version-specific changes to metric computation are noted in the relevant entry._

_*Reading guide for reviewers.* Where relevant, entries distinguish three layers: (1) *Implemented* - the exact computation in the pipeline; (2) *Interpretation* - the most defensible empirical reading; (3) *Speculative / Not established* - theoretical mappings not yet directly confirmed._

= A - D

*Attractor* - [Placeholder. A stable region in the neural state manifold to which trajectories tend to return after small perturbations. Geometrically, a local minimum in the potential landscape.]

*Coordinate (e.g. `m`, `d`, `e`)* - [Placeholder. State what each axis captures and the direction of interpretation.]

*[Term]* - [Placeholder definition following the format above.]

= E - L

*[Term]* - [Placeholder definition.]

*[Term]* - [Placeholder definition.]

= M - R

*Primary metric (e.g. Frobenius norm)* - [Placeholder. Implemented: formula. Interpretation: what it reflects. Not established: caveats.]

*[Term]* - [Placeholder definition.]

= S - Z

*Statistical method (e.g. BH-FDR)* - [Placeholder. The multiple-comparison correction used throughout. Threshold: $q < 0.05$ for primary analyses.]

*Robustness method (e.g. LOOSO, bootstrap, permutation)* - [Placeholder. Define each robustness check.]

*[Term]* - [Placeholder definition.]

#bibliography("references.bib", style: "apa")
