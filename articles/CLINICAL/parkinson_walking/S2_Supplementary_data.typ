#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data - Walking-State Geometry in Parkinson Disease",
  short-title: "Walking Supplementary Data",
  subtitle: "Focal rows, retained counts, and selected support tables for ds007526",
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

This supplement collects the data-heavy tables moved out of the main article:

- the eight focal rows used in the revised main text,
- retained counts by branch and threshold,
- the full compact headline tables for cohort walk and Parkinson paired contrasts,
- the targeted `IQR`/`MAD` paired extension rows,
- selected `IQR`/`MAD` regional support rows,
- the healthy-control paired context rows,
- selected regional and reachability support rows,
- selected global and regional clinical association rows,
- selected `IQR`/`MAD` rho rows,
- and the leading exploratory trajectory rows.

= Eight focal rows

#figure(
  kind: table,
  clean-table(
    columns: (1.45fr, 0.95fr, 1.3fr, 1.45fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Contract*], [*Layer*], [*Row*], [*Left med*], [*Right med*], [*`d`*], [*`q`*]),
    [`HC walk vs PD walk`], [`cohort`], [`global MNPS`], [`d_n_mean`], [`0.179`], [`1.003`], [`0.766`], [`0.030`],
    [`HC walk vs PD walk`], [`cohort`], [`global MNPS`], [`d_n_median`], [`0.0834`], [`0.987`], [`0.746`], [`0.030`],
    [`HC walk vs PD walk`], [`cohort`], [`global MNPS`], [`d_mean`], [`-0.873`], [`0.0496`], [`0.711`], [`0.036`],
    [`HC walk vs PD walk`], [`cohort`], [`global MNPS`], [`d_median`], [`-1.021`], [`-0.00832`], [`0.718`], [`0.036`],
    [`PD walk vs rest`], [`subject`], [`global MNPS`], [`d_n_mean`], [`0.00369`], [`0.110`], [`0.409`#super[z]], [`7.28e-4`],
    [`PD walk vs rest`], [`subject`], [`dispersion`], [`m_a_iqr`], [`1.161`], [`1.285`], [`0.472`#super[z]], [`6.55e-4`],
    [`PD walk vs rest`], [`subject`], [`dispersion`], [`d_iqr`], [`0.794`], [`0.928`], [`0.403`#super[z]], [`7.28e-4`],
    [`PD walk vs rest`], [`subject`], [`dispersion`], [`d_mad`], [`0.400`], [`0.455`], [`0.412`#super[z]], [`7.28e-4`],
  ),
  caption: [The eight focal rows used in the revised main article. The cohort rows come from the base standard family, while the paired Parkinson rows come from the targeted subject-anchor dispersion extension. The `d` column reports Cohen's `d` for the unpaired walk disease-state rows and Cohen's `d_z` (marked `z`) for the paired Parkinson rows.]
) <tab-s2-seven>

= Retained counts by branch

#figure(
  kind: table,
  clean-table(
    columns: (1.7fr, 0.95fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Branch*], [*Rows total*], [*`q < 0.05`*], [*`q < 0.1`*]),
    [`Cohort walk standard`], [`37`], [`4`], [`4`],
    [`PD paired standard`], [`37`], [`3`], [`4`],
    [`HC paired context`], [`37`], [`1`], [`3`],
    [`Cohort walk regional`], [`128`], [`2`], [`11`],
    [`Cohort rest reachability`], [`82`], [`9`], [`13`],
    [`Cohort rest trajectory`], [`24`], [`4`], [`7`],
    [`Cohort rest global rho`], [`333`], [`17`], [`24`],
    [`Subject-anchor global rho`], [`575`], [`2`], [`10`],
    [`Cohort rest regional rho`], [`1143`], [`113`], [`158`],
    [`Cohort rest trajectory rho`], [`216`], [`7`], [`23`],
  ),
  caption: [Retained counts taken directly from `article_exports_121725/retained_counts.csv`. These refer to the base standard article ledger. The targeted `IQR`/`MAD` extension is summarized separately below.]
) <tab-s2-counts>

= Cohort walk headline rows

#figure(
  kind: table,
  clean-table(
    columns: (1.35fr, 1.25fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Metric*], [*HC med*], [*PD med*], [*`d`*], [*`q`*]),
    [`HC vs PD walk`], [`d_n_mean`], [`0.179`], [`1.003`], [`0.766`], [`0.030`],
    [`HC vs PD walk`], [`d_n_median`], [`0.0834`], [`0.987`], [`0.746`], [`0.030`],
    [`HC vs PD walk`], [`d_mean`], [`-0.873`], [`0.0496`], [`0.711`], [`0.036`],
    [`HC vs PD walk`], [`d_median`], [`-1.021`], [`-0.00832`], [`0.718`], [`0.036`],
  ),
  caption: [All corrected `q < 0.05` cohort-walk standard rows. No additional cohort-walk standard row survives at `q < 0.1`.]
) <tab-s2-cohort-walk>

= Parkinson paired base-standard rows

#figure(
  kind: table,
  clean-table(
    columns: (1.35fr, 1.4fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Metric*], [*Rest med*], [*Walk med*], [*`d_z`*], [*`q`*]),
    [`PD walk vs rest`], [`d_n_mean`], [`0.00369`], [`0.110`], [`0.409`], [`0.0010`],
    [`PD walk vs rest`], [`d_mean`], [`-0.0168`], [`0.0723`], [`0.351`], [`0.0060`],
    [`PD walk vs rest`], [`jac9_anisotropy_abs_eig_median`], [`1.763`], [`1.823`], [`0.214`], [`0.032`],
    [`PD walk vs rest`], [`d_std`], [`0.705`], [`0.753`], [`0.292`], [`0.079`],
  ),
  caption: [The Parkinson paired base-standard branch. The first three rows survive `q < 0.05`; `d_std` is shown as the only additional `q < 0.1` near-headline row. These are the rows from the original central-tendency family before the targeted `IQR`/`MAD` extension.]
) <tab-s2-pd-paired>

= Parkinson paired `IQR`/`MAD` extension rows

#figure(
  kind: table,
  clean-table(
    columns: (1.35fr, 1.45fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Metric*], [*Rest med*], [*Walk med*], [*`d_z`*], [*`q`*]),
    [`PD walk vs rest`], [`m_a_iqr`], [`1.161`], [`1.285`], [`0.472`], [`6.55e-4`],
    [`PD walk vs rest`], [`d_iqr`], [`0.794`], [`0.928`], [`0.403`], [`7.28e-4`],
    [`PD walk vs rest`], [`d_mad`], [`0.400`], [`0.455`], [`0.412`], [`7.28e-4`],
    [`PD walk vs rest`], [`d_n_mean`], [`0.00369`], [`0.110`], [`0.409`], [`7.28e-4`],
    [`PD walk vs rest`], [`e_s_mad`], [`0.674`], [`0.674`], [`-0.0296`], [`0.0868`],
    [`PD walk vs rest`], [`jac9_anisotropy_abs_eig_mad`], [`0.152`], [`0.166`], [`0.219`], [`0.0969`],
  ),
  caption: [Targeted subject-anchor dispersion extension for the paired Parkinson branch. The first four rows define the revised paired headline in the main article; the final two rows are shown as the nearest `q < 0.1` context.]
) <tab-s2-pd-iqrmad>

= Healthy-control paired context

#figure(
  kind: table,
  clean-table(
    columns: (1.35fr, 1.1fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Metric*], [*Rest med*], [*Walk med*], [*`d_z`*], [*`q`*]),
    [`HC walk vs rest`], [`m_a_mean`], [`-0.146`], [`0.0736`], [`0.888`], [`0.0176`],
    [`HC walk vs rest`], [`m_mean`], [`-0.00722`], [`0.0908`], [`0.682`], [`0.0828`],
    [`HC walk vs rest`], [`d_l_mean`], [`-0.1328`], [`0.1536`], [`0.656`], [`0.0828`],
  ),
  caption: [Secondary-context healthy-control paired rows. Only `m_a_mean` survives `q < 0.05`.]
) <tab-s2-hc-context>

= Selected regional support rows

#figure(
  kind: table,
  clean-table(
    columns: (1.4fr, 0.95fr, 1.3fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Network*], [*Metric*], [*HC med*], [*PD med*], [*`d`*], [*`q`*]),
    [`HC vs PD walk`], [`frontal`], [`d_n_mean`], [`4.523`], [`5.476`], [`1.062`], [`0.0049`],
    [`HC vs PD walk`], [`frontal`], [`d_n_median`], [`4.465`], [`5.503`], [`1.051`], [`0.0049`],
    [`HC vs PD walk`], [`central`], [`d_n_mean`], [`2.959`], [`3.884`], [`0.656`], [`0.0647`],
    [`HC vs PD walk`], [`central`], [`d_n_median`], [`2.573`], [`3.848`], [`0.653`], [`0.0632`],
  ),
  caption: [Selected cohort-walk regional support rows. The two frontal rows survive `q < 0.05`; the central rows are included as the nearest `q < 0.1` context for the same family.]
) <tab-s2-regional>

= Selected `IQR`/`MAD` regional support rows

#figure(
  kind: table,
  clean-table(
    columns: (1.4fr, 1.0fr, 1.35fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Network*], [*Metric*], [*HC med*], [*PD med*], [*`d`*], [*`q`*]),
    [`HC vs PD rest`], [`temporal`], [`m_e_iqr`], [`0.646`], [`0.522`], [`-0.842`], [`0.0375`],
    [`HC vs PD rest`], [`parietal_occipital`], [`m_mad`], [`0.307`], [`0.167`], [`-0.724`], [`0.0375`],
    [`HC vs PD rest`], [`parietal_occipital`], [`m_iqr`], [`0.596`], [`0.338`], [`-0.705`], [`0.0375`],
    [`HC vs PD rest`], [`frontal`], [`m_iqr`], [`0.529`], [`0.370`], [`-0.694`], [`0.0375`],
    [`HC vs PD rest`], [`parietal_occipital`], [`e_mad`], [`0.623`], [`0.478`], [`-0.956`], [`0.00545`],
    [`HC vs PD walk`], [`temporal`], [`m_mad`], [`0.572`], [`0.486`], [`-0.946`], [`0.0203`],
  ),
  caption: [Selected regional `IQR`/`MAD` support rows from the cohort- and subject-anchor extension outputs. The strongest corrected rows are largely rest-side, but one walk-side temporal `m_mad` row also survives in the subject-anchor regional branch.]
) <tab-s2-regional-iqrmad>

= Selected reachability support rows

#figure(
  kind: table,
  clean-table(
    columns: (1.7fr, 1.2fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Metric*], [*HC med*], [*PD med*], [*`d`*], [*`q`*]),
    [`HC vs PD rest`], [`pred_err_h2`], [`2.030`], [`1.759`], [`-0.634`], [`0.023`],
    [`HC vs PD rest`], [`tube_log_det_mean`], [`-10.56`], [`-12.28`], [`-0.557`], [`0.023`],
    [`HC vs PD rest`], [`tube_log_det_median`], [`-10.42`], [`-12.26`], [`-0.522`], [`0.023`],
    [`HC vs PD rest`], [`cone_log_det_h2_median`], [`-10.83`], [`-12.73`], [`-0.518`], [`0.023`],
  ),
  caption: [Selected global rest reachability rows. The reachability branch is strong but rest-weighted, which is why it remains supplement-level support rather than a main walk headline.]
) <tab-s2-reach>

= Selected clinical association rows

#figure(
  kind: table,
  clean-table(
    columns: (1.2fr, 1.05fr, 1.35fr, 0.8fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Layer*], [*Task*], [*Row*], [*`rho`*], [*`q`*], [*`n`*]),
    [`global rho`], [`rest`], [`age vs d_s_mean`], [`-0.403`], [`2.68e-4`], [`116`],
    [`global rho`], [`rest`], [`CTT vs d_s_mean`], [`-0.415`], [`2.70e-4`], [`109`],
    [`global rho`], [`rest`], [`MoCA vs d_s_mean`], [`0.351`], [`0.0050`], [`113`],
    [`regional rho`], [`rest`], [`central d_s_mean vs CTT`], [`-0.432`], [`1.82e-4`], [`109`],
    [`regional rho`], [`rest`], [`frontal d_s_mean vs age`], [`-0.409`], [`4.88e-4`], [`116`],
    [`subject rho`], [`rest`], [`e_mean vs MoCA`], [`-0.311`], [`0.027`], [`113`],
    [`subject rho`], [`walk`], [`jac9 spectral radius vs age`], [`-0.329`], [`0.013`], [`110`],
  ),
  caption: [Selected clinical association rows from the article ledger. The dominant pattern is rest-side association structure in the `d_s_mean` family.]
) <tab-s2-rho>

= Selected `IQR`/`MAD` rho rows

#figure(
  kind: table,
  clean-table(
    columns: (1.05fr, 0.95fr, 1.55fr, 0.8fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Layer*], [*Task*], [*Row*], [*`rho`*], [*`q`*], [*`n`*]),
    [`global rho`], [`rest`], [`age vs d_s_iqr`], [`-0.377`], [`8.38e-4`], [`116`],
    [`global rho`], [`rest`], [`CTT vs d_s_iqr`], [`-0.351`], [`0.00489`], [`109`],
    [`global rho`], [`rest`], [`age vs d_s_mad`], [`-0.332`], [`0.00543`], [`116`],
    [`regional rho`], [`rest`], [`P/O e_iqr vs CTT`], [`0.439`], [`1.25e-4`], [`109`],
    [`regional rho`], [`rest`], [`P/O e_mad vs CTT`], [`0.435`], [`1.25e-4`], [`109`],
    [`regional rho`], [`rest`], [`central e_mad vs MoCA`], [`-0.389`], [`0.00211`], [`113`],
    [`subject regional rho`], [`rest`], [`temporal e_iqr vs UPDRS total`], [`-0.338`], [`0.0311`], [`113`],
    [`subject regional rho`], [`rest`], [`temporal e_iqr vs UPDRS III`], [`-0.323`], [`0.0396`], [`113`],
  ),
  caption: [Selected `IQR`/`MAD` rho rows from the dispersion extension. The dominant pattern is again rest-side, with corrected rows in both cohort-anchor and subject-anchor regional surfaces.]
) <tab-s2-iqrmad-rho>

#figure(
  image("figures/20260610_article/iqr_mad_rho_panels.svg", width: 98%),
  caption: [Scatter panels for the strongest `IQR`/`MAD` clinical associations. The figure combines global and regional examples so that the rest-side dispersion-association surface is visible at subject level rather than only as table entries.]
) <fig-s2-iqrmad-rho>

= Exploratory trajectory rows

#figure(
  kind: table,
  clean-table(
    columns: (1.25fr, 1.0fr, 1.35fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Dim*], [*Metric*], [*HC med*], [*PD med*], [*`d`*], [*`q`*]),
    [`HC vs PD rest`], [`3D`], [`noetic_action_kinetic`], [`0.00617`], [`0.00433`], [`-0.687`], [`0.012`],
    [`HC vs PD rest`], [`3D`], [`path_length`], [`32.4`], [`27.8`], [`-0.671`], [`0.012`],
    [`HC vs PD rest`], [`3D`], [`curvature_median`], [`3.299`], [`4.135`], [`0.596`], [`0.012`],
    [`HC vs PD rest`], [`3D`], [`noetic_action_jerk`], [`0.00142`], [`0.00122`], [`-0.530`], [`0.032`],
  ),
  caption: [The leading exploratory compact-summary trajectory rows. They are retained for transparency, but remain rest-dominant and exploratory in this manuscript.]
) <tab-s2-trajectory>

= Files

The tables in this supplement are backed mainly by:

- `results/parkinson_walking_20260610/article_exports_121725/focal_rows.csv`
- `results/parkinson_walking_20260610/article_exports_121725/context_rows.csv`
- `results/parkinson_walking_20260610/article_exports_121725/supportive_rows.csv`
- `results/parkinson_walking_20260610/article_exports_121725/exploratory_rows.csv`
- `results/parkinson_walking_20260610/article_exports_121725/retained_counts.csv`
- `results/parkinson_walking_20260610/article_exports_121725/evidence_ledger.csv`

#bibliography("parkinson_walking_geometry.bib")
