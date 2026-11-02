#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S6 Internal Changelog",
  short-title: "S6 Changelog - BOAS registered reanalysis",
  subtitle: "Internal provenance, review, freezing, and manuscript history",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Scope and intent

This internal supplement records the provenance and decision history of the exploratory registered BOAS reanalysis. It is not a biological interpretation and should not be separated from the measurement and qualification limits in the main manuscript.

= Analysis provenance

The source run is `neuralmanifolddynamics_ds005555_20260918_090500`, derived from OpenNeuro ds005555 v1.1.1. The registered analysis script is `src/run_registered_reanalysis.py`; its frozen SHA-256 is `934d85d99b3d003c8eefa08f377c48b6fa0ab4454f91360d64853e9dac983eb7`. The frozen output is `results/registered_reanalysis_20260923_frozen_v5`. Derived table and figure outputs are under `results/article_tables_20260924_v5` and `figures/registered_v5`.

= Changelog

== 2026-09-23: registered reanalysis

The source inventory, gaps, stage counts, fallback strata, A1 eligible centers, A2 finite-time-response horizons, and A3 family ledger were written to a fresh output root. No producer measurement or canonical coordinate definition was changed.

== 2026-09-23: A1 orientation correction

The initial v4 output used target/Wake pair ordering with a `b - a` reduction, which reversed the named A1 contrasts. The pair ordering was corrected to Wake/target, a synthetic regression test was added, and v5 was regenerated. A2/A3 tables, source identities, and hashes were unchanged. V4 is preserved as superseded; v5 is the only accepted A1 output.

== 2026-09-24: independent review and freeze

The independent reviewer reconstructed A1 arithmetic from serialized eligible centers, checked person and summary reductions, verified A2 usability and A3 status separation, and passed with `INDEPENDENT_V5_AUDIT=PASS`. V5 was copied to a separate frozen snapshot with a freeze marker. Article tables and figures were derived downstream without modifying that snapshot.

== Interpretation ceiling

The final verdict is PASS for reproducible descriptive measurement reporting and METHOD-LIMITED for biological interpretation. The package does not establish fit fidelity, continuous signal support, stage-intrinsic biology, independent confirmation, or C1/C2/C3. The planned continuous-support pilot remains a separate future gate.
