#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "S2 Data — ds004587 EAP",
  subtitle: "Result-table shells and provenance requirements for completed analyses",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S2.0 Reporting rule

Versioned audit and IG-only exploratory result files are available under `results/ds004587_20260712/` (original anchor-export refresh, `anchor_index` scale-integrity gate failed) and `results/ds004587_20260713/` (anchor-index-fix export, `anchor_index` passes the gate). All results reported in the main text use the `results/ds004587_20260713/` run against the `neuralmanifolddynamics_ds004587_20260712_111138` NMD export. The planned paired rest--illusion tables remain unavailable in both runs because the source release has no rest EEG. Each completed table cites its source CSV, analysis run identifier, code version, and inclusion rule.

= S2.1 Dataset coverage and eligibility

#figure(
  kind: table,
  clean-table(
    columns: (2fr, 1.2fr, 1.2fr, 2.2fr),
    align: (left, center, center, left),
    inset: 4pt,
    table.header([*Analysis surface*], [*Eligible $N$*], [*Excluded $N$*], [*Reason/source*]),
    [Primary rest--illusion neural], [0], [47], [No rest EEG / `00_sanity_check/inclusion_matrix.csv`],
    [IG-only respiratory/HRV screen], [45], [2], [Missing physiology / `02_anchor_validation/anchor_inference_gate.csv`],
    [Composite `anchor_index`], [45], [2], [Scale-integrity gate now passes (fixed export); missing-physiology exclusion only],
    [Behavior/strength], [0], [47], [No trial-to-EEG alignment contract],
  ),
  caption: [Eligibility by analysis surface. The dataset documents missing physiology for two participants and missing behavioral data for three participants; endpoint-specific eligibility must be derived from the audited release. @ds004587]
) <tab-eligibility>

= S2.2 Primary rest--illusion contrasts

The primary table will include every frozen endpoint. Condition summaries must use the same participant-level aggregation as the inferential test. Direction must state the subtraction order; paired $d_z$, confidence interval, exact $p$, and BH-FDR $q$ are required. @wilcoxon1945 @benjamini1995

#figure(
  kind: table,
  clean-table(
    columns: (1.8fr, 1fr, 1fr, 0.8fr, 1fr, 1fr, 0.8fr),
    align: (left, center, center, center, center, center, center),
    inset: 3.5pt,
    table.header([*Endpoint*], [*Rest*], [*Illusion*], [*$N$*], [*$d_z$ [CI]*], [*$p$*], [*$q$*]),
    [`TBD: frozen endpoint`], [`TBD`], [`TBD`], [`TBD`], [`TBD`], [`TBD`], [`TBD`],
  ),
  caption: [Complete pre-specified primary rest--illusion contrast family. Source: `TBD`.]
) <tab-primary>

= S2.3 Raw physiology and composite anchors

Raw ECG, PPG, and respiratory summaries will be reported separately from any composite anchor index. For every reported feature, the table must identify the calculation window, quality gate, and the number of valid participants. Composite indices must list their constituents and missing-data behavior. Their label does not establish a direct physiological mechanism.

= S2.4 Conditional anchor--geometry association family

The completed association screen is IG-only and participant-median; it is not time- or phase-resolved because the synchronization gate is indeterminate. `anchor_index` is included (it now passes the scale-integrity gate under the fixed export). It lists the complete corrected family in `04_eap_physio_coupling/direct_coupling.csv` and `hrv_controlled_coupling.csv`:

#figure(
  kind: table,
  clean-table(
    columns: (1.5fr, 1.5fr, 0.8fr, 0.8fr, 1fr, 0.8fr, 0.8fr),
    align: (left, left, center, center, center, center, center),
    inset: 3.5pt,
    table.header([*Anchor feature*], [*Neural endpoint*], [*Level*], [*$N$*], [*Effect [CI]*], [*$p$*], [*$q$*]),
    [`resp_anchor_index`], [`frobenius_norm`], [participant median], [45], [$r_s=-0.07$ [$-0.38$, $0.28$]], [$0.65$], [$0.85$],
    [`anchor_index`], [`trace`], [participant median], [45], [$r_s=-0.30$ [--]], [$0.046$], [$0.85$],
    [`ppg_quality_score`], [`m`], [participant median], [45], [$r_s=-0.34$ [--]], [$0.022$], [$0.85$],
  ),
  caption: [Predeclared directional respiratory association (`resp_anchor_index`) and the two smallest uncorrected $p$-values observed in the direct-coupling family, including the now-eligible composite `anchor_index`. No direct or HRV-adjusted association survives BH-FDR. Source: `results/ds004587_20260713/04_eap_physio_coupling/`. The `resp_anchor_index` point estimate differs from the value reported against the pre-fix export ($r_s=-0.26$) because the composite is a robust-z index recomputed cohort-wide by the scale fix; per-subject Frobenius-norm and raw physiological feature values are unchanged between exports (see S1.0).]
) <tab-eap>

= S2.5 Conditional illusion and behavioral analyses

Illusion family, objective strength, response time, accuracy, and event-locked results will be reported only after the BIDS event/behavior join is verified. Effects will be described as associations with dataset-defined labels. The table will state whether the model estimates within-person or between-person variation, all covariates, and the correction family.

= S2.6 Null and unavailable outcomes

This section will preserve: (1) pre-specified null effects, (2) failed quality gates, (3) unavailable export fields, and (4) analyses omitted because timing or label provenance was insufficient. These outcomes constrain interpretation and are not editorial omissions.

#bibliography("references.bib", style: "apa")
