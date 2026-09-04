#import "../comatose_ndt/network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "Coma 12-24 h Data",
  subtitle: "Timing audit, fixed-family tables, and exploratory late-window context",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Scope

This supplement collects the data-heavy material supporting the `12_24h` coma pilot:

- the full-export timing audit,
- the analyzable late-window subject subset,
- the fixed reachability family and compact anchor rows,
- supportive `MNJ 9D` rows,
- broader exploratory reachability ranking context,
- and the repeated-run IQR/MAD outputs.

= Full-export timing audit

#figure(
  kind: table,
  table(
    columns: (2.65fr, 1.0fr, 1.55fr),
    align: left,
    inset: 4pt,
    table.header([*Audit item*], [*Count*], [*Note*]),
    [H5 runs in current export root], [1575], [all runs currently present on disk],
    [Subjects in current export root], [124], [current no-regional `part1` batch],
    [Runs assigned to `0_12h`], [1412], [majority of the mixed-bin root],
    [Runs assigned to `12_24h`], [143], [true inferential late-window slice],
    [Runs assigned to `24_48h`], [11], [late spillover],
    [Runs assigned to `72h_plus`], [9], [very late spillover],
    [Timing source: `time_reference`], [1561], [primary source in the full-root audit],
    [Timing source: `wfdb_header_subject_anchor`], [14], [fallback rows; not retained in filtered `12_24h` metrics],
    [Subjects with any `12_24h` coverage], [97], [late-window subject subset after audit],
  ),
  caption: [Run-level timing audit for the `20260608_part1_noregional_subjectanchor` late-window rerun.]
) <tab-s2-audit>

= Analyzable `12_24h` subject subset

#figure(
  kind: table,
  table(
    columns: (2.75fr, 1.1fr, 1.1fr, 1.5fr),
    align: left,
    inset: 4pt,
    table.header([*Subset item*], [*`CPC 1`*], [*`CPC 5`*], [*Note*]),
    [Subjects], [47], [50], [bounded pilot contrast],
    [Site `A`], [22], [17], [largest site in the late-window slice],
    [Site `B`], [7], [10], [moderate contribution],
    [Site `D`], [10], [7], [moderate contribution],
    [Site `E`], [1], [10], [late-window imbalance retained],
    [Site `F`], [7], [6], [small but present],
    [Recording start after anchor, mean / median `h`], [`12.116 / 12.000`], [same clock], [subject-level `12_24h` summaries],
    [Recording end after anchor, mean / median `h`], [`13.470 / 13.000`], [same clock], [subject-level `12_24h` summaries],
    [Channel coverage fraction, mean / median], [`0.942 / 0.952`], [same subset], [usable-channel proxy only],
  ),
  caption: [Analyzable `12_24h` subject subset used for the late-window `CPC 1` versus `CPC 5` pilot contrast.]
) <tab-s2-subset>

= Compact anchor table

#figure(
  kind: table,
  table(
    columns: (2.45fr, 1.0fr, 1.0fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Family / metric*], [*`CPC 1` med*], [*`CPC 5` med*], [*Cohen's `d`*], [*M-W `p`*]),
    [`MNPS 3D / m_std`], [`0.875`], [`0.831`], [`+0.345`], [`0.203`],
    [`MNPS 9D / m_e_std`], [`1.076`], [`1.077`], [`+0.277`], [`0.518`],
    [`Reachability / tube_d_eff_median`], [`3.000`], [`3.101`], [`-0.046`], [`0.642`],
    [`Reachability / persistence_log_eig_var_median`], [`1.704`], [`2.027`], [`-0.353`], [`0.0411`],
    [`Reachability / persistence_kappa_median`], [`0.000801`], [`0.001371`], [`-0.686`], [`0.00752`],
    [`Reachability / tube_a_operator_norm_median`], [`11.217`], [`9.803`], [`+0.571`], [`0.00868`],
    [`Reachability / tube_capture_gate_median`], [`1.706`], [`1.585`], [`+0.584`], [`0.00977`],
    [`MNJ 3D / spectral_radius_median`], [`0.0715`], [`0.0718`], [`-0.237`], [`0.798`],
    [`MNJ 3D / frobenius_norm_median`], [`0.1445`], [`0.1468`], [`-0.293`], [`0.321`],
    [`MNJ 9D / spectral_radius_median`], [`0.0959`], [`0.0972`], [`+0.155`], [`0.695`],
    [`MNJ 9D / frobenius_norm_median`], [`0.628`], [`0.576`], [`+0.240`], [`0.203`],
  ),
  caption: [Compact `12_24h` pilot anchors across the fixed reachability, `MNPS`, and `MNJ` families. Reachability and `MNJ 9D` rows use finite-value subsets (`42 CPC 1`, `48 CPC 5`) after metric availability filtering.]
) <tab-s2-anchors>

= Fixed reachability family

#figure(
  kind: table,
  table(
    columns: (2.45fr, 0.95fr, 0.95fr, 0.95fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*`CPC 1` med*], [*`CPC 5` med*], [*Cohen's `d`*], [*M-W `p`*], [*BH-FDR `q`*]),
    [`persistence_kappa_median`], [`0.000801`], [`0.001371`], [`-0.686`], [`0.00752`], [`0.0376`],
    [`tube_a_operator_norm_median`], [`11.217`], [`9.803`], [`+0.571`], [`0.00868`], [`0.0393`],
    [`tube_capture_gate_median`], [`1.706`], [`1.585`], [`+0.584`], [`0.00977`], [`0.0393`],
    [`persistence_log_eig_var_median`], [`1.704`], [`2.027`], [`-0.353`], [`0.0411`], [`0.137`],
    [`tube_d_eff_median`], [`3.000`], [`3.101`], [`-0.046`], [`0.642`], [`0.770`],
  ),
  caption: [Reviewer-style audit of the fixed five-metric reachability family in the analyzable `12_24h` subset. All rows are patient-level median summaries, and BH-FDR is applied only inside this five-row family.]
) <tab-s2-reachability>

The fixed family is therefore mixed-sign rather than uniformly weak. `persistence_kappa_median` is higher in `CPC 5`, whereas `tube_a_operator_norm_median` and `tube_capture_gate_median` are higher in `CPC 1`. `persistence_log_eig_var_median` remains nominal and `tube_d_eff_median` remains near-null in this late-window slice.

= Supportive `MNJ 9D` rows

#figure(
  kind: table,
  table(
    columns: (2.35fr, 1.0fr, 1.0fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*`CPC 1` med*], [*`CPC 5` med*], [*Cohen's `d`*], [*M-W `p`*]),
    [`spectral_radius_median`], [`0.0959`], [`0.0972`], [`+0.155`], [`0.695`],
    [`anisotropy_abs_eig_median`], [`0.000857`], [`0.000831`], [`+0.170`], [`0.194`],
    [`frobenius_norm_median`], [`0.628`], [`0.576`], [`+0.240`], [`0.203`],
    [`mdr_median`], [`0.150`], [`0.153`], [`-0.301`], [`0.147`],
  ),
  caption: [Supportive `MNJ 9D` rows in the `12_24h` pilot. These remain descriptive anchors rather than a second confirmatory family.]
) <tab-s2-mnj9d>

= Exploratory reachability rows outside the fixed family

#figure(
  kind: table,
  table(
    columns: (2.65fr, 0.95fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Exploratory reachability row*], [*Cohen's `d`*], [*M-W `p`*], [*BH-FDR `q`*]),
    [`cone_kappa_h2_median`], [`+0.428`], [`0.000874`], [`0.0112`],
    [`cone_kappa_h1_median`], [`+0.359`], [`0.000927`], [`0.0112`],
    [`cone_log_eig_var_h2_median`], [`+0.637`], [`0.000982`], [`0.0112`],
    [`tube_log_eig_var_median`], [`+0.653`], [`0.00134`], [`0.0112`],
    [`tube_kappa_median`], [`+0.487`], [`0.00138`], [`0.0112`],
    [`cone_log_eig_var_h1_median`], [`+0.596`], [`0.00154`], [`0.0112`],
    [`cone_kappa_h3_median`], [`+0.503`], [`0.00163`], [`0.0112`],
    [`cone_log_eig_var_h3_median`], [`+0.651`], [`0.00168`], [`0.0112`],
    [`cone_kappa_h4_median`], [`+0.450`], [`0.00168`], [`0.0112`],
    [`cone_log_eig_var_h4_median`], [`+0.651`], [`0.00337`], [`0.0202`],
  ),
  caption: [Top exploratory reachability rows outside the fixed five-metric family from the `12_24h` reviewer-style selection audit (`60` patient-level reachability median rows tested).]
) <tab-s2-exploratory-reachability>

This broader ranking explains why the main pilot text emphasizes a reweighted later-window geometry profile. The most strongly ranked late-window rows cluster in `cone/tube` `kappa` and log-eigenvalue branches rather than in `tube_d_eff_median`.

= Between-run temporal variability

The repeated-run bundle is coverage-limited in the true `12_24h` slice.

- At the strict `>=3`-run threshold, only `5` subjects per metric meet coverage and no contrast rows are testable.
- At the exploratory `>=2`-run threshold, `12` subjects per metric are analyzable (`8 CPC 1`, `4 CPC 5`).

#figure(
  kind: table,
  table(
    columns: (2.7fr, 1.0fr, 1.0fr, 0.9fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric (MAD, `>=2` runs)*], [*`CPC 1` med*], [*`CPC 5` med*], [*Cohen's `d`*], [*M-W `p`*]),
    [`persistence_kappa_median_mad`], [`0.000154`], [`0.000384`], [`-1.353`], [`0.0727`],
    [`persistence_log_eig_var_median_mad`], [`0.0760`], [`0.1815`], [`-1.274`], [`0.0283`],
    [`tube_d_eff_median_mad`], [`0.0916`], [`0.1932`], [`-1.046`], [`0.154`],
    [`tube_a_operator_norm_median_mad`], [`0.406`], [`0.183`], [`+0.778`], [`0.461`],
    [`tube_capture_gate_median_mad`], [`0.0629`], [`0.0530`], [`-0.003`], [`0.933`],
  ),
  caption: [Exploratory between-run MAD contrasts under the `>=2` repeated-run threshold. Negative `d` indicates larger instability in `CPC 5`.]
) <tab-s2-mad-min2>

#figure(
  kind: table,
  table(
    columns: (2.7fr, 1.0fr, 1.0fr, 0.9fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric (IQR, `>=2` runs)*], [*`CPC 1` med*], [*`CPC 5` med*], [*Cohen's `d`*], [*M-W `p`*]),
    [`persistence_kappa_median_iqr`], [`0.000176`], [`0.000433`], [`-1.316`], [`0.0727`],
    [`tube_a_operator_norm_median_iqr`], [`0.778`], [`0.240`], [`+0.745`], [`0.461`],
    [`tube_d_eff_median_iqr`], [`0.113`], [`0.256`], [`-0.713`], [`0.283`],
    [`persistence_log_eig_var_median_iqr`], [`0.176`], [`0.308`], [`-0.193`], [`0.214`],
    [`tube_capture_gate_median_iqr`], [`0.0768`], [`0.0643`], [`+0.146`], [`0.933`],
  ),
  caption: [Exploratory between-run IQR contrasts under the `>=2` repeated-run threshold. These rows remain small-sample context rather than confirmatory evidence.]
) <tab-s2-iqr-min2>

= Files

The stamped outputs backing this supplement are:

- `timeline_analysis_20260608_part1_noregional_subjectanchor_primary12h_allavailable`
- `mnps_summary_20260608_part1_noregional_subjectanchor_primary12h_true1224`
- `outcome_contrasts_20260608_part1_noregional_subjectanchor_primary12h_true1224_cpc15`
- `reviewer_checks_20260608_part1_noregional_subjectanchor_true1224`
- `between_run_iqr_mad_20260608_part1_noregional_subjectanchor_true1224_min3`
- `between_run_iqr_mad_20260608_part1_noregional_subjectanchor_true1224_min2`
- `pilot_manifest_20260608_part1_noregional_subjectanchor.json`
- `results/reproducibility_commands.md`
- `figures/20260608_part1_noregional_subjectanchor_true1224/`

The frozen article release corresponding to these tables is archived on Zenodo.@langell2026_coma_v011

#bibliography("../comatose_ndt/cardiac_arrest_comatose_references.bib")
