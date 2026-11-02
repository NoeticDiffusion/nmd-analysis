#import "template_eLife.typ": *
#show: netn-template.with(title: "S3 Supplementary QC and Robustness", short-title: "S3 QC ds004511", subtitle: "Support boundaries and L4 certificate audit", authors: ((name: "Robin Langell", affil: 1),), affiliations: ("Langell Konsult AB, Vallentuna, Sweden",), corresponding-author: "Robin Langell, hello@noeticdiffusion.com", article-type: "Supplement")

= S3.1 Coverage

Chart-Jacobian alpha is finite on 134/134 recordings. Lag-1 one-step quantities are computed on 121/134 recordings; history-conditioned L2 is computed on 115/134. Lag-2 is absent. These are support facts, not successful imputation targets.

= S3.2 L4 certificate failures

#figure(kind: table, clean-table(columns: (1.7fr, 1.4fr, 1.1fr, 2.4fr), align: left, inset: 4pt,
table.header([*Subject*], [*Task*], [*Gate*], [*Failure*]),
[`sub-S200121`], [Rest], [F], [`post_dtype_psd_failure`],
[`sub-S200214`], [GG], [F], [`post_dtype_psd_failure`],
[`sub-S210203`], [CC], [F], [`post_dtype_psd_failure`],
), caption: [All missing finite `reach_a_q` certificates. One record falls in each task and each subject is distinct.])

= S3.3 Degenerate readout

Of 131 finite `reach_d_eff` values, 109 (83.2%) lie within $10^-6$ of 1; the median and minimum are 1 and the maximum is 1.31377. This rank-degenerate ellipsoid summary cannot support a capacity-dimension contrast. Apparent Wilcoxon significance on residual numerical variation is therefore method-limited and excluded from the article's substantive claims.

= S3.4 Next QC gate

The bounded audit is complete. The 13 recordings comprise 12 Rest and 1 CC (0 GG), all on a regular 4-s grid with 120--260 lag-1 pairs. Each fails the existing out-of-fold fidelity gate (`median(rel-MSE fold 1, fold 2) < 0.9`) with `one_step_fit_not_better_than_baseline`; reproduced fold scores agree within 1.338e-07. Diagnostic threshold sweeps (not production changes) identify 126/134 at 0.95, 128/134 at 1.0, and 131/134 at 1.5. This identifies a reproducible support boundary, not a reason to fill absent lags or reopen the estimator.

= S3.5 Fixed-duration chart-alpha sensitivity

All 134 recordings contain at least 100 exported chart-Jacobian alpha windows. Re-aggregation over the first 400 s preserves all three contrast directions: GG minus Rest, median difference 0.01450, $d_z=1.119$, $n=44$, $q=2.76 times 10^-8$; CC minus Rest, 0.00593, $d_z=0.394$, $n=45$, $q=0.0124$; and GG minus CC, 0.00995, $d_z=0.648$, $n=44$, $q=7.21 times 10^-5$. Here $q$ is BH over the three fixed-prefix alpha contrasts. This is a sampling-support sensitivity result, not a new measurement family or an assertion that early and full-recording dynamics are identical.

= S3.6 Duration boundary for L4

Recording durations are non-overlapping by task: Rest 480--596 s, CC 904--1324 s, and GG 2396--4652 s. The export contains no per-window L4 series, so a balanced-prefix L4 analysis is unavailable without recomputing the estimator. Audit-only within-task associations are positive in GG for `reach_a_q` (Spearman $rho=0.348$, $p=0.0224$) and `reach_v_norm` ($rho=0.353$, $p=0.0204$). These uncorrected correlations neither prove nor remove duration dependence. Large L4 task contrasts remain method-limited until L4 is recomputed under a predeclared balanced-window contract.

#figure(
  image("figures/results/ds004511_l4_certificate_qc_20260921.svg", width: 88%),
  caption: [Demoted L4 certificate QC. The three invalid `reach_a_q` certificates are evenly distributed across tasks; `reach_d_eff` is shown as a method limitation, not a dimension result. This figure is a QC summary, not reachability validation.]
) <fig-l4-qc>

#pagebreak()

= S3.7 Fixed-duration L1 sensitivity

All four frozen L1 series and exported validity masks support the same 100-window prefix in all 134 recordings. The 12 metric-by-contrast rows were corrected as one sensitivity family. Effects generally attenuated relative to the full recordings; 11/12 median-difference signs agreed. The sole sign change was the negligible and non-significant CC-minus-Rest `diffusion_effective_dimension` row (full $d_z=0.022$; fixed $d_z=-0.081$, fixed $q=0.732$).

#figure(kind: table, clean-table(
  columns: (1.45fr, 2.15fr, .75fr, .75fr, .85fr),
  align: (left, left, center, center, center), inset: 3.5pt,
  table.header([*Contrast*], [*L1 metric*], [*Full $d_z$*], [*400-s $d_z$*], [*400-s $q$*]),
  [GG -- Rest], [`diffusion_a_hat_frob`], [0.520], [0.445], [0.00836],
  [GG -- Rest], [`diffusion_total`], [0.551], [0.453], [0.00836],
  [GG -- Rest], [`diffusion_effective_dimension`], [0.146], [0.0667], [0.759],
  [GG -- Rest], [`chart_drift_b_hat_norm`], [1.82], [1.44], [2.02e-9],
  [CC -- Rest], [`diffusion_a_hat_frob`], [0.166], [0.272], [0.219],
  [CC -- Rest], [`diffusion_total`], [0.155], [0.266], [0.304],
  [CC -- Rest], [`diffusion_effective_dimension`], [0.0218], [-0.0811], [0.732],
  [CC -- Rest], [`chart_drift_b_hat_norm`], [0.505], [0.536], [0.00586],
  [GG -- CC], [`diffusion_a_hat_frob`], [0.332], [0.133], [0.489],
  [GG -- CC], [`diffusion_total`], [0.433], [0.162], [0.392],
  [GG -- CC], [`diffusion_effective_dimension`], [0.182], [0.193], [0.380],
  [GG -- CC], [`chart_drift_b_hat_norm`], [1.43], [0.947], [1.37e-6],
), caption: [Full-recording and deterministic 400-s-prefix L1 effect sizes. The displayed prefix $q$ is BH over the 12 L1 sensitivity rows; full-recording $q$ values belong to the separate 45-test task family and are not compared numerically here.]) <tab-l1-duration>

In the separate four-test fixed-prefix Friedman family, `chart_drift_b_hat_norm` remained informative ($chi^2=36.05$, $q=5.96 times 10^-8$). The diffusion-norm omnibus rows attenuated to $q=0.0564$ (`diffusion_a_hat_frob`) and $q=0.0649$ (`diffusion_total`); effective dimension remained uninformative ($q=0.761$). Thus the drift-norm pattern is robust to equalized sampling support, while the broader diffusion-family claim is weaker and contrast-specific.

The standardized chart-versus-L3 interaction uses 121 recordings with both production-supported estimators and complete subject contrasts of $n=32$, $n=32$, and $n=43$ for GG--Rest, CC--Rest, and GG--CC. Its positive GG--Rest and GG--CC rows survive the separate three-test exploratory BH family, but the estimand depends on the declared pooled median/MAD normalization. It is therefore a common-support robustness and estimator-difference analysis, not a raw-unit comparison or a duration test.

#netn-box(title: [QC verdict])[
  PARTIAL PASS. Chart-alpha and L1 drift-norm directions survive the deterministic 400-s sensitivity, while several diffusion results attenuate and L4 duration dependence remains unresolved. Lag-1 support is partial; lag-2 is unavailable; `reach_d_eff` is method-limited. No claim of a complete one-step, diffusion-invariant, reachability, or dimension analysis is licensed.
]
