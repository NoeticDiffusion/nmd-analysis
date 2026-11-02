#import "template_eLife.typ": *
#show: netn-template.with(title: "S2 Supplementary Data", short-title: "S2 Data ds004511", subtitle: "Result-table index and reproducibility record", authors: ((name: "Robin Langell", affil: 1),), affiliations: ("Langell Konsult AB, Vallentuna, Sweden",), corresponding-author: "Robin Langell, hello@noeticdiffusion.com", article-type: "Supplement")

= S2.1 Frozen artefacts

The corrected occupancy/MNJ/L1/L4 table is `results/v1_task_20260922_d_eff_qc_excluded/task_part1.md`; its substantive BH family contains 45 pairwise tests and excludes the degenerate `reach_d_eff` readout while preserving that readout in a separate QC section. The L2/L3 panel is `results/v1_level_20260921/level_part1.md`; the chart-alpha duration diagnostic is `results/v1_duration_robustness_20260922/duration_robustness.md`; the L1 duration diagnostic is `results/v1_l1_duration_robustness_20260922/l1_duration_robustness.md`; the estimator-interaction diagnostic is `results/v1_estimator_task_interaction_20260922/interaction_report.md`; and the L4 certificate audit is `results/v1_l4_qc_20260921/l4_qc.md`. Adjacent JSON manifests preserve executable provenance. The recording inventory is `results/ingest_20260921/recording_table.csv`.

= S2.2 Key complete-case contrasts

#figure(kind: table, clean-table(columns: (2.4fr, .8fr, 1fr, 1.1fr, 1.1fr), align: (left, center, center, center, center), inset: 4pt,
table.header([*GG minus Rest*], [*$n$*], [*$d_z$*], [*$p$*], [*BH $q$*]),
[Chart-Jacobian alpha], [44], [1.42], [1.558e-11], [5.607e-10],
[One-step spectral abscissa], [32], [-0.328], [0.1288], [0.1783],
[L2 rotation rate], [32], [-1.10], [6.906e-7], [8.044e-6],
[L3 generator rotation], [32], [-1.08], [6.906e-7], [8.044e-6],
), caption: [Rows transcribed from the separate L2/L3 family.])

= S2.3 Interpretation keys

The reported $n$ is endpoint- and contrast-specific. Chart-Jacobian alpha is finite on 134/134 recordings, lag-1 quantities on 121/134, and history-conditioned L2 on 115/134. On the chart-alpha eligible 32-person GG--Rest subset, $d_z=1.461$, median difference 0.01271, and $p=3.26e-9$. The raw rows are not a formal test of effect-size difference; the separate standardized interaction test below is the declared exploratory test on common estimator support. The L2/L3 pairwise $q$ column is global BH across 36 Wilcoxon tests.

= S2.3b Standardized estimator-by-task interaction

The interaction runner uses the 121 recordings with both production-supported chart and one-step L3 alpha. Each endpoint is centered and scaled separately by its common-support pooled recording median and $1.4826$ times MAD before subject-task medians and task contrasts are formed. The primary interaction is standardized chart contrast minus standardized L3 contrast. These three Wilcoxon tests have their own exploratory BH family; sign-flip and bootstrap columns are robustness summaries. This is normalization-dependent and does not compare raw endpoint units.

#figure(kind: table, clean-table(columns: (1.8fr, .55fr, .95fr, .95fr, .95fr, .95fr, .95fr), align: (left, center, center, center, center, center, center), inset: 3.5pt,
table.header([*Contrast*], [*$n$*], [*median interaction*], [*$d_z$*], [*Wilcoxon $p$*], [*BH $q$*], [*sign-flip $p$*]),
[GG -- Rest], [32], [1.888], [0.966], [6.79e-6], [2.04e-5], [1.00e-5],
[CC -- Rest], [32], [0.555], [0.327], [0.0837], [0.0837], [0.0755],
[GG -- CC], [43], [1.229], [0.771], [1.42e-5], [2.13e-5], [2.00e-5],
), caption: [Exploratory estimator-by-task interaction on common production support. Positive values mean a larger standardized chart-alpha task contrast than standardized L3-alpha contrast.]) <tab-alpha-interaction>

= S2.3c Common-support concordance

The concordance analysis uses the same complete subject pairs as the interaction output and introduces no new support or inferential family. Spearman $rho_s$ is a descriptive rank association between the standardized chart-alpha and L3-alpha task contrasts. Sign agreement excludes zero contrasts from its denominator; bootstrap intervals resample complete subject pairs within each contrast.

#figure(kind: table, clean-table(columns: (1.55fr, .55fr, .8fr, 1.1fr, .75fr, 1.1fr), align: (left, center, center, center, center, center), inset: 3.5pt,
table.header([*Contrast*], [*$n$*], [*$rho_s$*], [*95% CI*], [*$p$*], [*same sign*]),
[GG -- Rest], [32], [-0.383], [[-0.683, -0.001]], [0.0303], [12/32],
[CC -- Rest], [32], [-0.251], [[-0.570, 0.099]], [0.166], [13/32],
[GG -- CC], [43], [-0.284], [[-0.559, 0.041]], [0.0646], [11/43],
), caption: [Descriptive concordance of standardized estimator task contrasts. Bootstrap 95% CIs use 10,000 paired resamples. The axes are not raw endpoint units.]) <tab-estimator-concordance>

The source table, report and manifest are in `results/v1_estimator_concordance_20260922/`; the main-text scatter is `figures/results/ds004511_common_support_concordance_20260922.svg`.

#pagebreak()

= S2.4 Complete L1 local-law family

The four frozen L1 metrics are shown for all three within-subject contrasts rather than selected by significance. The corrected $q$ values use the 45-test substantive occupancy/MNJ/L1/L4-amplitude family; `reach_d_eff` is QC-only and is not part of that family. These are exploratory export-level summaries, not identified biological drift or diffusion.

#figure(kind: table, clean-table(
  columns: (1.55fr, 2.25fr, .55fr, .85fr, .7fr, .9fr, .9fr),
  align: (left, left, center, center, center, center, center), inset: 3.5pt,
  table.header([*Contrast*], [*L1 metric*], [*$n$*], [$Delta$ *med*], [*$d_z$*], [*$p$*], [*BH $q$*]),
  [GG -- Rest], [`diffusion_a_hat_frob`], [44], [0.03241], [0.520], [0.001358], [0.003217],
  [GG -- Rest], [`diffusion_total`], [44], [0.04987], [0.551], [0.001186], [0.003139],
  [GG -- Rest], [`diffusion_effective_dimension`], [44], [0.02645], [0.146], [0.3947], [0.4674],
  [GG -- Rest], [`chart_drift_b_hat_norm`], [44], [0.03436], [1.82], [2.16e-12], [1.62e-11],
  [CC -- Rest], [`diffusion_a_hat_frob`], [45], [0.008981], [0.166], [0.2715], [0.3818],
  [CC -- Rest], [`diffusion_total`], [45], [0.01813], [0.155], [0.3822], [0.4674],
  [CC -- Rest], [`diffusion_effective_dimension`], [45], [0.03825], [0.0218], [0.7122], [0.7630],
  [CC -- Rest], [`chart_drift_b_hat_norm`], [45], [0.005902], [0.505], [0.007377], [0.01509],
  [GG -- CC], [`diffusion_a_hat_frob`], [44], [0.02029], [0.332], [0.01170], [0.02290],
  [GG -- CC], [`diffusion_total`], [44], [0.02711], [0.433], [0.005605], [0.01201],
  [GG -- CC], [`diffusion_effective_dimension`], [44], [0.01941], [0.182], [0.3947], [0.4674],
  [GG -- CC], [`chart_drift_b_hat_norm`], [44], [0.02264], [1.43], [1.921e-11], [1.081e-10],
), caption: [Complete pairwise L1 family. Positive differences are later minus earlier as named in the contrast column. No row was selected by significance.]) <tab-l1-complete>

Complete-triplet Friedman tests likewise supported task variation in `diffusion_a_hat_frob` ($chi^2=8.909$, $n=44$, $q=0.01938$), `diffusion_total` ($chi^2=6.682$, $q=0.04828$), and `chart_drift_b_hat_norm` ($chi^2=49.95$, $q=7.10 times 10^-11$), but not `diffusion_effective_dimension` ($chi^2=2.227$, $q=0.3789$). These omnibus $q$ values use the separate 15-test substantive Friedman family.
