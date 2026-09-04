#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S6 Changelog",
  short-title: "S6 Hypoglycemia dynamics changelog",
  subtitle: "Analysis, claim-boundary, and supplement revisions",
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

This changelog records substantive revisions to the hypoglycemia EEG
reanalysis package. It distinguishes changes to the frozen analysis outputs
from changes in interpretation, reporting, and reviewer-facing documentation.

= Changelog

== 2026-07-23: Initial paired analysis release

- Reanalyzed 68 H5 files from 34 paired participants under the frozen
  `neuralmanifolddynamics_hypoglycemia_t1d_20260723_180515` export.
- Added paired 3D and 9D coordinate contrasts, 3D/9D Jacobian summaries,
  reachability audit outputs, raw EEG feature checks, and QC tables.
- Added a 10,000-draw paired label-swap null and a directional sensitivity
  analysis excluding the three hypoglycemia files marked `adjusted`.

== 2026-08-17: Peer-review revision round

- Corrected the abstract's q-value wording: $e_e$ has $q = 0.0396$, whereas
  $m_a$, $m_e$, $d_n$, and $e_m$ have engine-level $q <= 0.0048$.
- Reframed the title, Results, Discussion, Conclusion, S1, S3, S4, and S5 so
  reachability is explicitly validity-limited rather than a tested negative
  finding. The nominal direction is retained as an exploratory audit.
- Reported the previously omitted $d_l$ survivor in the restricted label-swap
  null and added the 9D Jacobian exploratory family to S2.
- Documented engine-wide FDR families, channel-identity uncertainty, the
  source-versus-reanalysis preprocessing differences, the pooled anchor, the
  standardized-feature clip, and the operational boundary of $e_m$.
- Corrected numerical discrepancies in the S2 $m_o$ and $d_s$ rows.
- Replaced the generic S4 and S5 templates with article-specific clinical
  interpretation and glossary text.
- Replaced the copied S4 template with this article-specific changelog.

== 2026-08-18: Literature and archive audit

- Added nine directly relevant research articles covering quantitative EEG,
  nonlinear complexity, EEG coherence, antecedent hypoglycemia, cognition,
  cerebral metabolism, and neuroimaging context.
- Added the Zenodo data-record citation
  `10.5281/zenodo.3465213` and separated it from the associated Entropy
  article citation.
- Documented that the public OpenNeuro catalogue search found no matching
  dataset or dataset-specific publication; Zenodo remains the source archive
  used for this reanalysis.
