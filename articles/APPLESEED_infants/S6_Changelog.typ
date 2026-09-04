#import "template_eLife.typ": *
#show: netn-template.with(
  title: "S6 Changelog",
  short-title: "APPLESEED changelog",
  subtitle: "Initial reproducible reliability reanalysis",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= 2026-08-05: Cohort-anchor analysis release
- Audited the 48-session H5 export: 13 children, 11 complete longitudinal cases, 38 `ok` and 10 `adjusted` geometry contracts.
- Added reusable H5-to-session wrappers, primary reliability/longitudinal analysis, optional child-aggregated event analysis, and figure generation.
- Frozen the cohort-anchored three-dimensional nine-endpoint primary family and reachability configuration ($k=12$, horizon 3), using export `neuralmanifolddynamics_ds003710_20260804_153346` and anchor `ds003710_global_cohort_all_timepoints_iqr_v2_1`.
- Added session-level ICC(A,1), cluster bootstrap, paired-change, named-FDR-family, coordinate/comparator reliability, and retest-mean sensitivity outputs.
- Wrote the manuscript and six supplements with explicit all-ages-anchor, 9D-complete-case, nominal-age, and chart-level interpretation limits.
