#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "Coma Supplementary Data",
  subtitle: "Primary tables, exploratory hourly anchors, and invalidity-fix vs `pre_combat` comparison",
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

This supplement collects the data-heavy material moved out of the main article:

- pooled primary anchor tables,
- detailed reachability rows,
- supportive `MNJ 9D` tables,
- compact exploratory hourly-localization summaries,
- between-run IQR temporal variability results,
- exploratory late-window (`12_24h`) global-pool BH-FDR ranking,
- and the focused invalidity-fix-versus-`pre_combat` comparison note.

= Primary pooled anchors

#figure(
  kind: table,
  clean-table(
    columns: (2.35fr, 1.1fr, 1.1fr, 1.1fr, 1.0fr, 1.0fr),
    align: left,
    inset: 4pt,
    table.header([*Family / metric*], [*`part1` med*], [*`part2` med*], [*Pooled med*], [*Pooled `d`*], [*Pooled `p`*]),
    [`MNPS 3D / m_std`], [`0.850 / 0.932`], [`0.792 / 0.891`], [`0.824 / 0.915`], [`-0.279`], [`0.0296`],
    [`MNPS 9D / m_e_std`], [`1.091 / 1.238`], [`1.104 / 1.265`], [`1.103 / 1.265`], [`-0.302`], [`0.00153`],
    [`Reachability / tube_d_eff_median`], [`2.953 / 2.466`], [`3.087 / 2.339`], [`2.990 / 2.448`], [`+0.838`], [`9.24e-06`],
    [`Reachability / persistence_log_eig_var_median`], [`1.453 / 0.926`], [`2.001 / 1.102`], [`1.619 / 1.017`], [`+0.736`], [`5.30e-05`],
    [`Reachability / tube_capture_gate_median`], [`1.881 / 1.917`], [`1.519 / 2.005`], [`1.835 / 1.960`], [`-0.558`], [`0.00804`],
    [`MNJ 3D / spectral_radius_median`], [`0.0736 / 0.0783`], [`0.0703 / 0.0759`], [`0.0720 / 0.0775`], [`-0.521`], [`7.31e-08`],
    [`MNJ 3D / frobenius_norm_median`], [`0.151 / 0.173`], [`0.153 / 0.182`], [`0.153 / 0.176`], [`-0.499`], [`1.85e-07`],
    [`MNJ 9D / spectral_radius_median`], [`0.1022 / 0.1203`], [`0.1036 / 0.1222`], [`0.1025 / 0.1213`], [`-0.603`], [`4.90e-07`],
    [`MNJ 9D / anisotropy_abs_eig_median`], [`0.000972 / 0.00137`], [`0.00115 / 0.00148`], [`0.00106 / 0.00139`], [`-0.538`], [`1.13e-07`],
    [`MNJ 9D / frobenius_norm_median`], [`0.601 / 0.733`], [`0.555 / 0.642`], [`0.576 / 0.699`], [`-0.592`], [`1.72e-06`],
    [`MNJ 9D / mdr_median`], [`0.1523 / 0.1583`], [`0.1507 / 0.1548`], [`0.1516 / 0.1577`], [`-0.255`], [`5.68e-04`],
  ),
  caption: [Compact primary anchors across partwise and pooled cohorts. Median entries are shown as `CPC 1 / CPC 5`.]
) <tab-s2-primary-anchors>

= Detailed reachability family

#figure(
  kind: table,
  clean-table(
    columns: (2.45fr, 0.95fr, 0.95fr, 0.95fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*`CPC 1` med*], [*`CPC 5` med*], [*Cohen's `d`*], [*M-W `p`*], [*BH-FDR `q`*]),
    [`tube_d_eff_median`], [`2.990`], [`2.448`], [`+0.838`], [`9.24e-06`], [`1.54e-05`],
    [`persistence_log_det_median`], [`1.305`], [`0.832`], [`+0.896`], [`1.49e-06`], [`3.73e-06`],
    [`persistence_log_eig_var_median`], [`1.619`], [`1.017`], [`+0.736`], [`5.30e-05`], [`6.63e-05`],
    [`persistence_hysteresis_log_det_median`], [`2.558`], [`3.718`], [`-0.909`], [`1.14e-07`], [`5.70e-07`],
    [`tube_capture_gate_median`], [`1.835`], [`1.960`], [`-0.558`], [`8.04e-03`], [`8.04e-03`],
  ),
  caption: [Pooled article-facing reachability family from the reviewer-style selection audit. All five metrics clear BH-FDR correction at `q < 0.05`.]
) <tab-s2-reachability>

This table is the primary corrected family in the article's inferential contract: BH-FDR is applied inside these five reachability rows, whereas the remaining tables in this supplement function as secondary anchors, exploratory material, or audit context. `tube_d_eff_median` and `persistence_log_eig_var_median` are the two strongest effective-dimensionality separators; `persistence_log_det_median` and `persistence_hysteresis_log_det_median` are the two strongest persistence-log-determinant separators; and `tube_capture_gate_median` captures transport-dynamics complementarity. All five now clear BH-FDR correction.

= Supportive `MNJ 9D` table

#figure(
  kind: table,
  clean-table(
    columns: (2.35fr, 1.1fr, 0.95fr, 0.95fr, 1.1fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Metric*],
      [*`part1` med*], [*`part1` `d`*], [*`part1` `p`*],
      [*`part2` med*], [*`part2` `d`*], [*`part2` `p`*],
    ),
    [`spectral_radius_median`], [`0.1022 / 0.1203`], [`-0.777`], [`1.27e-05`], [`0.1036 / 0.1222`], [`-0.400`], [`0.0123`],
    [`anisotropy_abs_eig_median`], [`0.000972 / 0.00137`], [`-0.747`], [`9.10e-06`], [`0.00115 / 0.00148`], [`-0.352`], [`0.00488`],
    [`frobenius_norm_median`], [`0.601 / 0.733`], [`-0.886`], [`1.15e-05`], [`0.555 / 0.642`], [`-0.317`], [`0.0209`],
    [`mdr_median`], [`0.1523 / 0.1583`], [`-0.394`], [`1.72e-04`], [`0.1507 / 0.1548`], [`-0.214`], [`0.277`],
  ),
  caption: [Supportive `MNJ 9D` rows retained after the merge. Median entries are shown as `CPC 1 / CPC 5`.]
) <tab-s2-mnj9d>

The key point is cohort asymmetry, not absence of signal. `MNJ 9D` spectral radius and anisotropy are clearly present in both cohorts, with larger standardized effects in `part1` than `part2` for this run. The main paper therefore reports `MNJ 9D` as material but cohort-heterogeneous rather than as a one-cohort artifact.

= Exploratory hourly localization anchors

#figure(
  kind: table,
  clean-table(
    columns: (2.6fr, 1.15fr, 1.15fr, 1.15fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Hourly range of `d`*], [*Peak bin*], [*Peak `d`*]),
    [`Reachability / tube_d_eff_median`], [`+0.740` to `+0.950`], [`2_3h`], [`+0.950`],
    [`Reachability / tube_capture_gate_median`], [`-0.399` to `-0.711`], [`3_4h`], [`-0.711`],
    [`MNJ 3D / spectral_radius_median`], [`-0.657` to `-0.366`], [`3_4h`], [`-0.657`],
    [`MNJ 9D / spectral_radius_median`], [`-0.849` to `-0.429`], [`2_3h`], [`-0.849`],
  ),
  caption: [Compact hourly peak summary for the main pooled localization anchors across `0_1h` through `11_12h`.]
) <tab-s2-hourly>

These rows are descriptive rather than confirmatory. They summarize where the observed hourly effect-size peaks occur, but they should be read together with the circular-shift null in `S3`, which did not support a strong precise peak-timing claim for the observed early-hour peaks.

To make the hourly localization less abstract, the lead reachability result is expanded below with selected early-bin values. These rows show that `tube_d_eff_median` is already separated in `0_1h`, strengthens through `2_3h`, and remains near-peak at `3_4h`.

#figure(
  kind: table,
  clean-table(
    columns: (1.15fr, 1.2fr, 1fr, 1fr, 0.9fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Time bin*], [*`CPC 1 / CPC 5` `n`*], [*`CPC 1` med*], [*`CPC 5` med*], [*Cohen's `d`*], [*M-W `p`*]),
    [`0_1h`], [`59 / 48`], [`2.843`], [`2.291`], [`+0.786`], [`1.22e-04`],
    [`1_2h`], [`57 / 44`], [`2.960`], [`2.451`], [`+0.761`], [`4.37e-04`],
    [`2_3h`], [`57 / 50`], [`3.115`], [`2.555`], [`+0.950`], [`1.49e-05`],
    [`3_4h`], [`57 / 43`], [`3.118`], [`2.407`], [`+0.950`], [`5.72e-05`],
    [`4_5h`], [`56 / 44`], [`3.145`], [`2.448`], [`+0.831`], [`8.86e-05`],
    [`5_6h`], [`59 / 45`], [`3.178`], [`2.591`], [`+0.779`], [`2.04e-04`],
  ),
  caption: [Selected hourly-bin values for the lead pooled reachability metric, `tube_d_eff_median`. Median entries are shown separately for `CPC 1` and `CPC 5`.]
) <tab-s2-hourly-tube-deff>


= Between-run temporal variability — IQR

This section reports the between-run interquartile range (IQR, defined as `q75 − q25` of per-run values) for the five article-facing reachability metrics. The analysis uses the same recording-complete subset as the main-article MAD analysis: subjects with ≥`3` qualifying per-run values in the `0-12 h` time bin (`n = 130`, `70 CPC 1` / `60 CPC 5`). IQR measures the spread of middle-half per-run values, complementing the MAD analysis in the main text.

#figure(
  kind: table,
  clean-table(
    columns: (2.55fr, 1.0fr, 1.0fr, 0.9fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric (IQR)*], [*`CPC 1` med*], [*`CPC 5` med*], [*Cohen's `d`*], [*M-W `p`*]),
    [`tube_capture_gate_median` IQR], [`0.1680`], [`0.2882`], [`-0.991`], [`3.69e-06`],
    [`persistence_hysteresis_log_det_median` IQR], [`0.4173`], [`0.9143`], [`-0.643`], [`8.44e-05`],
    [`persistence_log_det_median` IQR], [`0.4698`], [`0.6219`], [`-0.271`], [`0.0759`],
    [`persistence_log_eig_var_median` IQR], [`0.5291`], [`0.7234`], [`-0.263`], [`0.0928`],
    [`tube_d_eff_median` IQR], [`0.7004`], [`0.7695`], [`-0.125`], [`0.334`],
  ),
  caption: [Between-run IQR contrasts in the recording-complete subset (`n = 130`, `70 CPC 1` / `60 CPC 5`). Negative Cohen's `d` indicates larger spread in `CPC 5` subjects. Between-run MAD results are reported in the main article; the IQR and MAD rankings are directionally identical for the two strongest metrics.]
) <tab-s2-between-run-iqr>

The IQR findings are directionally consistent with the MAD results in the main article. `tube_capture_gate_median` IQR (`d = -0.991`) and `persistence_hysteresis_log_det_median` IQR (`d = -0.643`) rank in the same order as their MAD counterparts. The remaining three metrics show weaker or non-significant IQR separation, matching the MAD pattern. The coverage selectivity of the recording-complete subset should be noted: patients with fewer qualifying recordings are excluded, and this may differ across sites or outcome groups.

= Exploratory late-window (`12_24h`) global-pool audit

To test whether additional `12_24h` rows outrank the fixed late-window five-metric family, we ran a full-pool BH-FDR audit on the rerun bundle `outcome_contrasts_20260608_part1_noregional_subjectanchor_primary12h_true1224_cpc15` (`patient_timebin`, `time_bin == 12_24h`). Global BH-FDR was applied across all `159` tested rows.

#figure(
  kind: table,
  clean-table(
    columns: (2.85fr, 0.95fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Global `12_24h` row (`q < 0.05`)*], [*Cohen's `d`*], [*M-W `p`*], [*Global BH `q`*]),
    [`global_mnps_jacobian_3d / trace_mean`], [`-0.664`], [`0.00482`], [`0.0459`],
    [`reachability_cones / tube_log_eig_var_median`], [`+0.653`], [`0.00134`], [`0.0222`],
    [`reachability_cones / cone_log_eig_var_h4_median`], [`+0.651`], [`0.00337`], [`0.0412`],
    [`reachability_cones / cone_log_eig_var_h3_median`], [`+0.651`], [`0.00168`], [`0.0222`],
    [`global_mnps_9d / e_s_mean`], [`+0.638`], [`0.000864`], [`0.0222`],
    [`reachability_cones / cone_log_eig_var_h2_median`], [`+0.637`], [`0.000982`], [`0.0222`],
    [`reachability_cones / median_min_eig_over_median_eig`], [`-0.626`], [`0.00507`], [`0.0459`],
    [`global_mnps_9d / e_s_std`], [`+0.600`], [`0.00155`], [`0.0222`],
    [`reachability_cones / cone_log_eig_var_h1_median`], [`+0.596`], [`0.00154`], [`0.0222`],
    [`reachability_cones / tube_a_operator_norm_mean`], [`+0.566`], [`0.00520`], [`0.0459`],
    [`reachability_cones / cone_kappa_h3_median`], [`+0.503`], [`0.00163`], [`0.0222`],
    [`reachability_cones / tube_kappa_median`], [`+0.487`], [`0.00138`], [`0.0222`],
    [`reachability_cones / median_cond`], [`+0.460`], [`0.00110`], [`0.0222`],
    [`reachability_cones / cone_kappa_h4_median`], [`+0.450`], [`0.00168`], [`0.0222`],
    [`reachability_cones / tube_log_eig_var_mean`], [`+0.438`], [`0.00384`], [`0.0428`],
    [`reachability_cones / cone_kappa_h2_median`], [`+0.428`], [`0.000874`], [`0.0222`],
    [`reachability_cones / cone_kappa_h1_median`], [`+0.359`], [`0.000927`], [`0.0222`],
    [`reachability_cones / persistence_hysteresis_kappa_median`], [`+0.328`], [`0.00404`], [`0.0428`],
  ),
  caption: [All globally BH-FDR-significant `12_24h` rows from the no-regional rerun (`159` tested rows at patient level).]
) <tab-s2-late1224-global-bh>

This global-pool audit changed the ranking relative to the prespecified five-row late-window family. Under global multiplicity, the five prespecified rows no longer remained corrected-positive (`persistence_kappa_median q = 0.0627`, `tube_a_operator_norm_median q = 0.0627`, `tube_capture_gate_median q = 0.0641`, `persistence_log_eig_var_median q = 0.168`, `tube_d_eff_median q = 0.756`). The top corrected rows instead concentrated in `cone/tube` log-eigenvalue and `kappa` branches, with additional `MNJ 3D trace` and `MNPS 9D e_s` anchors.

The full table is stored in `results/late1224_global_pool_bh_20260608.csv` with a compact note in `results/late1224_global_pool_bh_20260608.md`.

= Conclusion: difference versus the first `0_12h` window

Relative to the main `0_12h` pooled result, the late-window exploratory profile is not a direct replay.

- In `0_12h`, the prespecified five-metric article family is jointly corrected-positive and led by `tube_d_eff_median`, `persistence_log_det_median`, and `persistence_hysteresis_log_det_median` (Table @tab-s2-reachability).
- In `12_24h`, global correction across the full metric pool shifts the strongest corrected rows toward `cone/tube` log-eig-variance and `kappa` branches, with additional `MNJ 3D trace` and `MNPS 9D e_s` rows.
- The late-window prespecified five-row set remains informative as a bounded family analysis, but it is more multiplicity-sensitive than the early-window (`0_12h`) contract and should be interpreted as exploratory rather than confirmatory in this broad-pool setting.

= Files

The main tables in this supplement are backed by the pooled result bundles under `articles/CLINICAL/comatose_ndt/results/` with date tag `20260606_combined_invalidityfix`.

Additional late-window audit outputs are:

- `results/late1224_global_pool_bh_20260608.csv`
- `results/late1224_global_pool_bh_20260608.md`

The frozen article release corresponding to these tables is archived on Zenodo.@langell2026_coma_v011

= References

#bibliography("cardiac_arrest_comatose_references.bib")

