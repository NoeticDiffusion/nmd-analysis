#import "../comatose_ndt/network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "Coma 12-24 h QC",
  subtitle: "Subgroup sensitivity, metric dependence, and coverage limits in the late-window pilot",
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

This supplement collects the bounded QC / robustness material available for the stamped `12_24h` pilot rerun. It is intentionally narrower than the early-window `comatose_ndt` robustness package because the late-window article has not been expanded into a full prediction, permutation, and hourly-null rerun for the current `20260608_part1_noregional_subjectanchor` stamp.

The current supplement therefore focuses on:

- rhythm-subgroup sensitivity,
- dependence structure inside the fixed five-metric family,
- repeated-run coverage limits,
- and an explicit note about what was *not* rerun for this pilot.

= Sensitivity by rhythm subgroup

In the analyzable `12_24h` subject subset, shockable-rhythm status is known for `94/97` subjects (`56` shockable, `38` non-shockable, `3` missing). The reviewer-style rerun persists the shockable-only subgroup directly; the non-shockable rows below were recomputed directly from the same stamped `patient_timebin_signal_metrics.csv` and timeline metadata under the identical five-metric family.

#figure(
  image("figures/20260608_part1_noregional_subjectanchor_true1224/fig5_shockable_sensitivity.svg", width: 100%),
  caption: [Shockable-only sensitivity for the fixed late-window reachability family.]
) <fig-s3-shockable>

#figure(
  kind: table,
  table(
    columns: (2.45fr, 0.95fr, 0.95fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Shockable-only metric*], [*`CPC 1` med*], [*`CPC 5` med*], [*Cohen's `d`*], [*M-W `p`*]),
    [`tube_a_operator_norm_median`], [`11.693`], [`9.779`], [`+0.974`], [`0.00167`],
    [`persistence_kappa_median`], [`0.001`], [`0.001`], [`-1.034`], [`0.00365`],
    [`persistence_log_eig_var_median`], [`1.682`], [`2.054`], [`-0.537`], [`0.0625`],
    [`tube_capture_gate_median`], [`1.702`], [`1.609`], [`+0.630`], [`0.0683`],
    [`tube_d_eff_median`], [`3.001`], [`3.110`], [`-0.375`], [`0.283`],
  ),
  caption: [Shockable-only subgroup sensitivity from the stamped reviewer-check bundle (`33 CPC 1`, `18 CPC 5` with analyzable fixed-family rows).]
) <tab-s3-shockable>

#figure(
  kind: table,
  table(
    columns: (2.45fr, 0.95fr, 0.95fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Non-shockable-only metric*], [*`CPC 1` med*], [*`CPC 5` med*], [*Cohen's `d`*], [*M-W `p`*]),
    [`tube_d_eff_median`], [`2.762`], [`3.074`], [`+0.187`], [`0.845`],
    [`persistence_kappa_median`], [`0.000934`], [`0.000778`], [`-0.247`], [`0.845`],
    [`persistence_log_eig_var_median`], [`1.577`], [`1.959`], [`-0.197`], [`0.345`],
    [`tube_a_operator_norm_median`], [`9.473`], [`9.700`], [`-0.059`], [`0.938`],
    [`tube_capture_gate_median`], [`1.742`], [`1.558`], [`+0.379`], [`0.325`],
  ),
  caption: [Directly recomputed non-shockable subgroup sensitivity from the same stamped `12_24h` metric bundle (`7 CPC 1`, `29 CPC 5` with analyzable fixed-family rows).]
) <tab-s3-nonshockable>

The practical reading is asymmetry rather than clean subgroup replication. The shockable subgroup retains the same late-window mixed-sign neighborhood seen in the full pilot, whereas the non-shockable subgroup is highly coverage-imbalanced and does not provide a stable competing hierarchy.

= Dependence inside the fixed five-metric family

The reviewer-style rerun also records pairwise Spearman correlations across the five fixed reachability metrics. These are useful because the late-window family is not orthogonal: the persistence-side rows move together, while `tube_a_operator_norm_median` and `tube_capture_gate_median` partly separate from the persistence-led block.

#figure(
  kind: table,
  table(
    columns: (2.25fr, 0.82fr, 0.82fr, 0.82fr, 0.82fr, 0.82fr),
    align: center + horizon,
    inset: 4pt,
    table.header(
      [*Metric*],
      [*`tube_d_eff`*],
      [*`persistence_kappa`*],
      [*`persistence_log_eig_var`*],
      [*`tube_a_operator_norm`*],
      [*`tube_capture_gate`*],
    ),
    [`tube_d_eff_median`], [`1.000`], [`0.715`], [`0.791`], [`-0.041`], [`-0.563`],
    [`persistence_kappa_median`], [`0.715`], [`1.000`], [`0.852`], [`-0.481`], [`-0.691`],
    [`persistence_log_eig_var_median`], [`0.791`], [`0.852`], [`1.000`], [`-0.184`], [`-0.679`],
    [`tube_a_operator_norm_median`], [`-0.041`], [`-0.481`], [`-0.184`], [`1.000`], [`0.478`],
    [`tube_capture_gate_median`], [`-0.563`], [`-0.691`], [`-0.679`], [`0.478`], [`1.000`],
  ),
  caption: [Spearman dependence structure inside the fixed five-metric late-window family.]
) <tab-s3-correlations>

The strongest dependence is between `persistence_kappa_median` and `persistence_log_eig_var_median` (`rho = 0.852`), followed by the links from those two rows to `tube_d_eff_median`. By contrast, `tube_a_operator_norm_median` is only weakly coupled to `tube_d_eff_median` (`rho = -0.041`) and only moderately aligned with `tube_capture_gate_median` (`rho = 0.478`), which helps explain why the late-window fixed family is mixed-sign rather than one-dimensional.

= Repeated-run coverage boundary

The between-run IQR/MAD pass is constrained mainly by sparse repeated recording in the true `12_24h` slice. Coverage is identical across the five fixed metrics:

#figure(
  kind: table,
  table(
    columns: (2.8fr, 1.3fr, 1.8fr),
    align: left,
    inset: 4pt,
    table.header([*Coverage threshold*], [*Subjects per metric*], [*Interpretation*]),
    [`>=2` finite runs], [12], [`8 CPC 1` / `4 CPC 5`; exploratory contrasts possible],
    [`>=3` finite runs], [5], [too sparse for testable strict-threshold contrasts],
    [Any subject with at least one late-window run], [90], [coverage base for the variability audit],
  ),
  caption: [Repeated-run coverage boundary for the late-window IQR/MAD analysis.]
) <tab-s3-coverage>

This is the main reason the repeated-run findings in the manuscript remain exploratory. The late-window slice is structurally dominated by single-run subjects, so the variability layer is informative but not yet stable enough for a confirmatory robustness package.

= What was not rerun

The current `12_24h` supplement should not be confused with the much broader early-window robustness package. For the latest `20260608_part1_noregional_subjectanchor` stamp, the following were *not* rerun into a manuscript-facing late-window supplement:

1. a dedicated QC-only proxy prediction model,
2. patient-label permutation for the fixed family,
3. leave-one-subject-out or leave-one-site-out stability tables,
4. train-fold-only cross-fitted reselection,
5. horizon-sensitivity summaries,
6. and subject-wise circular-shift nulls for peak timing.

This omission is deliberate rather than accidental: the current late-window article is framed as a bounded continuation bundle, not as a full pooled robustness package parallel to the early-window paper.

= Files

The tables and figure in this supplement are backed primarily by:

- `reviewer_checks_20260608_part1_noregional_subjectanchor_true1224`
- `between_run_iqr_mad_20260608_part1_noregional_subjectanchor_true1224_min2`
- `between_run_iqr_mad_20260608_part1_noregional_subjectanchor_true1224_min3`
- `figures/20260608_part1_noregional_subjectanchor_true1224/fig5_shockable_sensitivity.svg`

The frozen article release corresponding to this pilot line is archived on Zenodo.@langell2026_coma_v011

#bibliography("../comatose_ndt/cardiac_arrest_comatose_references.bib")
