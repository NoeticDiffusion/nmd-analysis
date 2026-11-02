#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "S2 Data - BOAS registered reanalysis",
  subtitle: "Complete descriptive tables and family-level status ledgers",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S2.0 Data package and table conventions

The complete machine-readable tables are generated from the frozen v5 snapshot and retained under `results/article_tables_20260924_v5`. The tables preserve fallback strata, coordinate dimension, native grain, support counts, unavailable values, and status fields. They contain no inferential test results and no biological qualification.

= S2.1 Coverage table

`table_1_coverage.csv` and `table_1_coverage.md` report the 128 recording IDs, 100 biological `pid` values, 16,629 selected windows, 1,469 gaps, 2,318,850 omitted seconds, stage counts, and fallback inventory.

= S2.2 A1 primary contrast table

`table_2_a1_primary_contrasts.csv` and `.md` contain full and boundary-only PPG 3D summaries for spectral and numerical abscissa across N2-minus-Wake, N3-minus-Wake, and REM-minus-Wake. Columns include eligible people and recordings, median, quartiles, and the registered person-cluster percentile interval.

#figure(
  kind: table,
  clean-table(
    columns: (1.3fr, 1fr, 1.3fr, .7fr, 1.1fr, 1.7fr),
    align: (left, center, left, right, right, right),
    inset: 3pt,
    table.header([*Contrast*], [*Pass*], [*Endpoint*], [*$n$ people*], [*Median*], [*Bootstrap q025--q975*]),
    [N2 minus Wake], [Full], [Spectral abscissa], [76], [-0.000647], [-0.001518 -- -0.000114],
    [N2 minus Wake], [Full], [Numerical abscissa], [76], [-0.002557], [-0.004512 -- -0.001333],
    [N3 minus Wake], [Full], [Spectral abscissa], [33], [-0.001872], [-0.003083 -- -0.000462],
    [N3 minus Wake], [Full], [Numerical abscissa], [33], [-0.005922], [-0.007751 -- -0.003335],
    [REM minus Wake], [Full], [Spectral abscissa], [75], [0.000720], [0.000164 -- 0.001588],
    [REM minus Wake], [Full], [Numerical abscissa], [75], [0.000761], [-0.000967 -- 0.002236],
  ),
  caption: [Compact view of the full-pass primary table. The machine-readable table also contains the boundary-only pass.]
) <s2-primary>

= S2.3 A2 finite-time-response support table

`table_3_a2_ftr_support.csv` and `.md` report each fallback stratum, dimension, and registered horizon. They include eligible people and recordings, nominated summaries, actual horizon duration, zero-valid-sequence counts, and unusable-horizon counts. The exact 9D `sub-3` and `sub-4` rows remain unavailable at h1, h2, and h4.

= S2.4 A3 family status table

`table_4_a3_family_status.csv` and `.md` group the serialized family ledger by family, role, computation status, measurement validity, support status, and claim status. The diffusion parent and increment-covariance child are separate rows and must not be collapsed.

= S2.5 Reproducibility manifest

`article_outputs_manifest.json` records the frozen input analysis-manifest hash, freeze-marker hash, derived-output hashes, and the descriptive method-limited status. The frozen source tables remain under `results/registered_reanalysis_20260923_frozen_v5` and are not overwritten by the derived-output generation.
