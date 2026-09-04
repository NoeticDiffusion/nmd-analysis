#import "resuscitation_template.typ": *

#show: resuscitation-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "Coma Supplementary QC",
  authors: (),
  affiliations: (),
  corresponding-author: "",
  article-type: "Supplement",
  show-summary: false,
)

#align(center)[#text(size: 9pt)[Author information is withheld for blinded peer review.]]

= Scope

This supplement records the pooled quality-control, sensitivity, and temporal diagnostics that support the internal interpretation of the main analysis:

- shockable and non-shockable sensitivity,
- QC-only proxy prediction and QC correlations,
- leave-one-subject-out and leave-one-site-out stability,
- leave-one-subject-out prediction,
- patient-label permutation,
- train-fold-only cross-fitted reachability sensitivity,
- reachability horizon sensitivity,
- hourly time-shift nulls,
- early-versus-late distribution diagnostics,
- and caveats about what could not be tested from the locked export.

= Sensitivity by rhythm subgroup

The pooled cohort retains usable shockable-rhythm labels for `260` patients (`165` shockable). All five primary derived features were tested in both strata. These are sensitivity analyses, not separate confirmatory tests.

#figure(
  image("../figures/20260606_combined_invalidityfix/fig5_shockable_sensitivity.svg", width: 100%),
  caption: [Shockable-only sensitivity for the article-facing reachability metrics.]
) <fig-s3-shockable>

#figure(
  kind: table,
  clean-table(
    columns: (2.45fr, 0.95fr, 0.95fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Shockable-only metric*], [*`CPC 1` med*], [*`CPC 5` med*], [*Cohen's `d`*], [*M-W `p`*]),
    [`tube_d_eff_median`], [`2.963`], [`2.448`], [`+0.690`], [`0.00522`],
    [`persistence_log_det_median`], [`1.267`], [`0.808`], [`+0.689`], [`0.00473`],
    [`persistence_log_eig_var_median`], [`1.596`], [`1.118`], [`+0.482`], [`0.0424`],
    [`persistence_hysteresis_log_det_median`], [`2.632`], [`3.714`], [`-0.762`], [`0.00215`],
    [`tube_capture_gate_median`], [`1.773`], [`1.911`], [`-0.489`], [`0.108`],
  ),
  caption: [Shockable-only sensitivity for the updated five-metric family.]
) <tab-s3-shockable>

#figure(
  image("../figures/20260606_combined_invalidityfix/fig6_nonshockable_sensitivity.svg", width: 100%),
  caption: [Non-shockable-only sensitivity for the article-facing reachability metrics.]
) <fig-s3-nonshockable>

#figure(
  kind: table,
  clean-table(
    columns: (2.45fr, 0.95fr, 0.95fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Non-shockable metric*], [*`CPC 1` med*], [*`CPC 5` med*], [*Cohen's `d`*], [*M-W `p`*]),
    [`tube_d_eff_median`], [`3.087`], [`2.449`], [`+0.966`], [`0.00672`],
    [`persistence_log_det_median`], [`1.514`], [`0.866`], [`+1.152`], [`0.00851`],
    [`persistence_log_eig_var_median`], [`1.661`], [`0.897`], [`+1.001`], [`0.0107`],
    [`persistence_hysteresis_log_det_median`], [`2.204`], [`3.775`], [`-0.924`], [`0.00226`],
    [`tube_capture_gate_median`], [`1.961`], [`1.963`], [`-0.475`], [`0.200`],
  ),
  caption: [Non-shockable-only sensitivity for the updated five-metric family.]
) <tab-s3-nonshockable>

= QC-only proxy model and QC correlations

The export still does not preserve direct artifact burden for quantitative analysis. `artifact_detector_enabled_all` is constant false and `artifact_burden_mean` is missing, so the available QC package is limited to usable-window count, channel count, and channel coverage.

#figure(
  kind: table,
  clean-table(
    columns: (2.55fr, 1.15fr, 1.0fr, 1.0fr),
    align: left,
    inset: 4pt,
    table.header([*QC-only summary*], [*ROC AUC*], [*AUPRC*], [*Brier*]),
    [`Windows + channel count + coverage`], [`0.543 +/- 0.056`], [`0.530 +/- 0.035`], [`0.250 +/- 0.006`],
  ),
  caption: [QC-only proxy model summary. This analysis does not establish independence from artifact burden, which was unavailable.]
) <tab-s3-qc-model>

The QC correlations are selective rather than overwhelming. `tube_d_eff_median` shows only modest negative correlation with channel count and channel coverage (`rho = -0.154` for both), `persistence_log_eig_var_median` is somewhat more coverage-sensitive (`rho = -0.255`), and `tube_capture_gate_median` is near-null against the same proxies (`rho = 0.003`).

= Leave-one-out stability and prediction

The main pooled anchors were tested for directional stability under single-subject and whole-hospital omission, and the predictive geometry increment was tested under true subject-level leave-one-out prediction.

#figure(
  kind: table,
  clean-table(
    columns: (2.55fr, 0.85fr, 1.35fr, 1.35fr, 0.85fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Full `d`*], [*Leave-one-subject-out `d` range*], [*Leave-one-site-out `d` range*], [*Sign consistency*]),
    [`Reachability / tube_d_eff_median`], [`+0.838`], [`+0.814` to `+0.899`], [`+0.699` to `+0.980`], [`1.000`],
    [`Reachability / persistence_log_eig_var_median`], [`+0.736`], [`+0.713` to `+0.794`], [`+0.461` to `+0.911`], [`1.000`],
    [`Reachability / tube_capture_gate_median`], [`-0.558`], [`-0.608` to `-0.526`], [`-0.659` to `-0.356`], [`1.000`],
    [`MNJ 3D / spectral_radius_median`], [`-0.521`], [`-0.577` to `-0.506`], [`-0.602` to `-0.460`], [`1.000`],
    [`MNJ 9D / spectral_radius_median`], [`-0.603`], [`-0.721` to `-0.585`], [`-0.763` to `-0.263`], [`1.000`],
  ),
  caption: [Omission stability for the five main pooled anchors. Sign consistency is the fraction of leave-one-out reruns that preserved the direction of the full pooled effect.]
) <tab-s3-loo-stability>

The main point is direction stability rather than identical effect magnitude. `tube_d_eff_median`, `tube_capture_gate_median`, and both Jacobian anchors remain tightly stable under subject omission. The `MNJ 9D` and `persistence_log_eig_var_median` entries are more omission-sensitive in magnitude, but no single subject or site reverses their direction.

#figure(
  kind: table,
  clean-table(
    columns: (2.35fr, 0.9fr, 0.95fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Model*], [*Features*], [*AUROC*], [*AUPRC*], [*Brier*]),
    [`Clinical + qEEG`], [`26`], [`0.601`], [`0.578`], [`0.247`],
    [`Clinical + qEEG + geometry`], [`31`], [`0.668`], [`0.659`], [`0.235`],
  ),
  caption: [True subject-level leave-one-out prediction on the analyzable pooled extreme-outcome model cohort (`n = 281`).]
) <tab-s3-loo-prediction>

The increment remained directionally present in this one-subject-held-out analysis. It remains an internal validation result after fixed upstream preprocessing.

= Patient-label permutation

Permutation testing confirms all five metrics are well above the null. Observed effect sizes range from `|d| = 0.558` to `0.909`, all substantially exceeding the null p95 of approximately `0.35`.

#figure(
  kind: table,
  clean-table(
    columns: (2.65fr, 1.0fr, 1.0fr, 1.0fr, 1.0fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Observed `|d|`*], [*Null mean*], [*Null `p95`*], [*Empirical `p`*]),
    [`tube_d_eff_median`], [`0.838`], [`0.143`], [`0.348`], [`0.0005`],
    [`persistence_log_det_median`], [`0.896`], [`0.142`], [`0.345`], [`0.0005`],
    [`persistence_log_eig_var_median`], [`0.736`], [`0.143`], [`0.352`], [`0.0005`],
    [`persistence_hysteresis_log_det_median`], [`0.909`], [`0.144`], [`0.350`], [`0.0005`],
    [`tube_capture_gate_median`], [`0.558`], [`0.140`], [`0.349`], [`0.0015`],
    [`max abs effect across selected metrics`], [`0.909`], [`0.232`], [`0.430`], [`0.0005`],
  ),
  caption: [Label permutation for the five-metric family. All observed effect sizes substantially exceed the null p95 of approximately `0.35`.]
) <tab-s3-permutation>

Given the pooled |d| ≈ 0.90 for both new metrics — substantially larger than the null p95 of `0.35` — both clearly clear the permutation null. All five metrics now pass, rather than three-clear and two-borderline in the prior family.

= Cross-fitted repeated CV

The fixed five-feature article layer is a post-selection internal validation object, so a train-fold-only reselection control was also run. In each training fold, candidate reachability metrics were reranked using train-only Mann-Whitney tests and the top `5` rows were carried into the held-out fold. This asks whether the geometry gain collapses once feature choice is restricted to within-fold information.

#figure(
  kind: table,
  clean-table(
    columns: (2.55fr, 0.9fr, 1.15fr, 1.15fr, 1.15fr),
    align: left,
    inset: 4pt,
    table.header([*Model*], [*Features*], [*AUROC*], [*AUPRC*], [*Brier*]),
    [`Clinical + qEEG`], [`26`], [`0.602 +/- 0.109`], [`0.632 +/- 0.094`], [`0.269 +/- 0.052`],
    [`Fixed clinical + qEEG + geometry`], [`31`], [`0.722 +/- 0.095`], [`0.751 +/- 0.086`], [`0.227 +/- 0.052`],
    [`Cross-fitted clinical + qEEG + geometry`], [`31`], [`0.720 +/- 0.095`], [`0.751 +/- 0.088`], [`0.228 +/- 0.051`],
    [`Cross-fitted geometry only`], [`5`], [`0.747 +/- 0.089`], [`0.784 +/- 0.088`], [`0.212 +/- 0.033`],
  ),
  caption: [Train-fold-only cross-fitted repeated-CV control. Note: this analysis uses fewer CV repeats than the primary incremental validity run reported in the main article, resulting in higher variance and somewhat higher point estimates. The cross-fitted geometry layer is slightly stronger than the fixed article layer rather than collapsing.]
) <tab-s3-crossfit>

The train-only selector converges on a capacity-led and persistence-led neighborhood rather than on a completely different family. The most frequently selected rows were:

- `persistence_hysteresis_log_det_median` (`100` folds),
- `persistence_log_det_median` (`91` folds),
- `cone_d_eff_h1_median` (`62` folds),
- `tube_d_eff_split_half_a_median` (`40` folds),
- `cone_q_ratio_h2_median` (`39` folds).

The train-only selector repeatedly favored the two log-determinant persistence measures. This supports internal feature-selection stability but does not create an externally frozen biomarker panel.

= Horizon sensitivity

The horizon rerun confirms that the dimensionality result is not unique to one particular propagation depth. Effective dimensionality remains stable across `H = 1..4`, while the derived capture gate is directionally stable from `H = 2` onward. `H = 1` is structurally degenerate for the derived gate because `q^(1) = 1`.

#figure(
  kind: table,
  clean-table(
    columns: (2.15fr, 0.9fr, 0.9fr, 0.9fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*Horizon-resolved family*], [*`H = 1` `d`*], [*`H = 2` `d`*], [*`H = 3` `d`*], [*`H = 4` `d`*]),
    [`Effective dimensionality`], [`+0.887`], [`+0.842`], [`+0.805`], [`+0.789`],
    [`Anisotropy (`cone_kappa_h`)`], [`-0.231`], [`-0.280`], [`-0.287`], [`-0.294`],
    [`Log-eigenvalue spread (`cone_log_eig_var_h`)`], [`+0.176`], [`+0.136`], [`+0.088`], [`+0.036`],
    [`Derived capture gate`], [degenerate], [`-0.610`], [`-0.599`], [`-0.581`],
  ),
  caption: [Compact horizon-sensitivity grid for the pooled primary reachability family across `H = 1..4`.]
) <tab-s3-horizon>

= Hourly time-shift null

The main paper shows the hourly heatmap as useful descriptive context, but the added temporal QC asks a stricter question: are the observed hourly peak `|d|` values larger than what would be expected if each subject's hourly profile were circularly shifted before recomputing the group contrast? This subject-wise circular-shift null preserves each subject's overall hourly profile shape while disrupting shared peak alignment.

#figure(
  kind: table,
  clean-table(
    columns: (2.45fr, 0.95fr, 0.95fr, 1.05fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Peak bin*], [*Observed `d`*], [*Null mean max `|d|`*], [*Null `p95`*], [*Empirical `p`*]),
    [`MNJ 3D / spectral_radius_median`], [`3_4h`], [`-0.657`], [`0.638`], [`0.725`], [`0.312`],
    [`MNJ 9D / spectral_radius_median`], [`2_3h`], [`-0.849`], [`0.899`], [`1.010`], [`0.765`],
    [`Reachability / persistence_log_eig_var_median`], [`4_5h`], [`+0.954`], [`1.021`], [`1.178`], [`0.769`],
    [`Reachability / tube_capture_gate_median`], [`3_4h`], [`-0.711`], [`0.786`], [`0.933`], [`0.836`],
    [`Reachability / tube_d_eff_median`], [`2_3h`], [`+0.950`], [`1.061`], [`1.217`], [`0.947`],
  ),
  caption: [Subject-wise circular-shift null for hourly peak localization. The observed hourly maxima do not clearly exceed the shifted-anchor null maxima.]
) <tab-s3-time-shift>

This is the main cautionary result from the temporal QC pass. The hourly maps remain compatible with broad early structure and with a descriptive early-hour emphasis, but the null does not support a strong precise peak-timing claim.

= Early-versus-late window structure

The pooled hourly bundle shows subgroup-structured distributions when the `1-4 h` window is compared with the `8-12 h` window in paired subjects (`n = 240`). The strongest late-minus-early shifts are seen in `persistence_hysteresis_log_det_median` (median shift `−0.323`, `p = 1.6e-05`) and `persistence_log_det_median` (median shift `+0.171`, `p = 4.7e-06`), followed by `persistence_log_eig_var_median` and `tube_d_eff_median`.

#figure(
  kind: table,
  clean-table(
    columns: (2.35fr, 0.95fr, 0.95fr, 1.0fr, 1.0fr, 1.1fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Early BIC gain*], [*Late BIC gain*], [*Early high-mode frac*], [*Late high-mode frac*], [*Median late-minus-early*]),
    [`persistence_log_eig_var_median`], [`-9.753`], [`-8.948`], [`0.540`], [`0.600`], [`+0.171`],
    [`tube_d_eff_median`], [`-2.182`], [`9.849`], [`0.570`], [`0.670`], [`+0.140`],
    [`persistence_log_det_median`], [`-2.835`], [`-4.961`], [`0.440`], [`0.630`], [`+0.171`],
    [`persistence_hysteresis_log_det_median`], [`14.561`], [`55.034`], [`0.380`], [`0.240`], [`-0.323`],
    [`tube_capture_gate_median`], [`-7.073`], [`4.105`], [`0.210`], [`0.120`], [`-0.077`],
  ),
  caption: [Early-versus-late distribution summary using paired subjects with both windows available.]
) <tab-s3-early-late>

Available paired-shift Wilcoxon results:

- `persistence_log_eig_var_median`: median late-minus-early `+0.171`, Wilcoxon `p = 5.27e-05`
- `tube_d_eff_median`: median late-minus-early `+0.140`, Wilcoxon `p = 5.11e-05`
- `persistence_log_det_median`: median late-minus-early `+0.171`, Wilcoxon `p = 4.73e-06`
- `persistence_hysteresis_log_det_median`: median late-minus-early `-0.323`, Wilcoxon `p = 1.60e-05`
- `tube_capture_gate_median`: median late-minus-early `-0.077`, Wilcoxon `p = 0.000318`

= What remains unresolved

The pooled robustness package still leaves four unresolved boundaries.

1. WLST and time-of-death sensitivity cannot be tested from the manuscript-facing export.
2. Direct artifact burden is unavailable because the detector is off.
3. The current time-order control is limited to subject-wise circular shifts of already-derived hourly summaries; a stricter upstream re-estimation from reordered trajectories was not run.
4. The current supplement is an internal sensitivity package rather than external validation of a frozen bedside biomarker layer.

= Files

The tables in this supplement are backed by result bundles under `articles/CLINICAL/comatose_ndt/results/` with date tag `20260606_combined_invalidityfix`, specifically:

- `robustness_checks_20260606_combined_invalidityfix_newgeom`
- `horizon_sensitivity_20260606_combined_invalidityfix`
- `distribution_windows_20260606_combined_invalidityfix_newgeom`
- `additional_qc_20260606_combined_invalidityfix_newgeom`
- `figures/20260606_combined_invalidityfix/fig5_shockable_sensitivity.svg`

Release details for the frozen manuscript snapshot are withheld for blinded peer review.

= References

#bibliography("cardiac_arrest_comatose_references_blinded.bib", style: "resuscitation-vancouver.csl", title: none)
