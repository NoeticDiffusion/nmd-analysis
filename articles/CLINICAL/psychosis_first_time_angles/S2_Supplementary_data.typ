// S2 Supplementary Data — generic template.
// Rename and replace placeholder tables per article.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "S2 Data - [short article tag]",
  subtitle: "Complete contrast tables for global coordinates, primary metrics, regional/block summaries, secondary coupling, and confounds",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S2.0 Complete global coordinate contrast table

[Placeholder. All pairwise contrasts for global coordinates, Wilcoxon signed-rank on session medians, BH-FDR applied across the family. None/few survive correction - the global null reported as R2 in the main text.]

#figure(
  kind: table,
  clean-table(
    columns: (0.8fr, 1.6fr, 1fr, 1fr, 1fr, 0.9fr, 0.9fr, 0.7fr),
    align: left,
    inset: 3.5pt,
    table.header(
      [*Coord.*], [*Contrast*], [*A med.*], [*B med.*], [*C med.*], [*$d$*], [*FDR $q$*], [*Sig.*]
    ),
    [`[coord]`], [Task A vs B], [`[TBD]`], [`[TBD]`], [-], [`[TBD]`], [`[TBD]`], [No],
  ),
  caption: [Placeholder global-coordinate contrast table. Source: `[results path]`.]
) <tab-global-full>

= S2.1 Complete primary-metric contrast table

[Placeholder. All pairwise contrasts for the primary metric family, Wilcoxon signed-rank on session medians, BH-FDR across the family.]

#figure(
  kind: table,
  clean-table(
    columns: (1.8fr, 1.1fr, 1fr, 1fr),
    align: (left, center, center, center),
    inset: 5pt,
    table.header([*Metric*], [*A vs B* $d$], [*p*], [*FDR*]),
    [`metric_1`], [`[TBD]`], [`[TBD]`], [-],
  ),
  caption: [Placeholder primary-metric contrast table. yes = survives FDR 5%.]
) <tab-primary-full>

= S2.2 Regional contrasts

[Placeholder. Regional / network-stratified contrasts.]

= S2.3 Block-level contrasts

[Placeholder. Block-level contrasts from an independent aggregation pathway.]

= S2.4 Secondary coupling (full table)

[Placeholder. Full secondary-coupling table (e.g. EAP partial correlations), sorted by uncorrected $p$, with FDR $q$.]

= S2.5 Secondary physio-coupling

[Placeholder. Secondary physiology-coordinate coupling, global and per-network.]

= S2.6 Physiological and temporal-structure confound partial-correlation table (combined)

[Placeholder. Combined confound partial-correlation table across all follow-up scripts.]

= S2.7 Descriptive summary by task

[Placeholder. Descriptive summaries (e.g. tonic SCL, EMG RMS) by task.]

#bibliography("references.bib", style: "apa")
