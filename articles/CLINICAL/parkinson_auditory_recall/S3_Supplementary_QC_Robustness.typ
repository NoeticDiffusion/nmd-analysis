#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "Parkinson Supplementary QC",
  subtitle: "Residual-label exclusion, subgroup stability, and outlier sensitivity for ds004574",
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

This supplement collects the robustness material that was intentionally separated from the main manuscript:

- residual `raw_nan_onset_sec` exclusion,
- control-only and Parkinson-only reruns of the selected auditory contrasts,
- selected `sub-112` exclusion and winsorized follow-up for the supportive global group rows,
- explicit confirmation that the flagged `9D` Jacobian outlier does not create a hidden article-facing Jacobian result,
- and caveats about the remaining validation boundary.

= Residual-label exclusion and subgroup stability

The article-local wrapper already excludes `raw_nan_onset_sec` events by construction. A separate robustness pass then asked whether the selected auditory anchors remained strong after excluding all subjects with positive residual-`nan` event labels and after rerunning the same auditory comparisons inside `Control` and `Parkinson` separately.

The local pass flagged `26` subjects with positive residual `raw_nan_onset_sec` windows in the final H5 bundle. Excluding those subjects did not weaken the selected auditory anchors. Nor did the direction depend on diagnostic group.

#figure(
  kind: table,
  table(
    columns: (2.35fr, 1.25fr, 1.25fr, 1.1fr, 1.1fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*All subjects*], [*Exclude raw `nan`*], [*Control only*], [*Parkinson only*]),
    [`3D transition_sparsity / other_mean vs auditory_all`], [`d = +3.376`, `p = 1.03e-25`], [`d = +3.766`, `p = 1.95e-21`], [`d = +3.651`, `p = 7.11e-15`], [`d = +3.254`, `p = 8.28e-18`],
    [`9D entropy_rate / other_mean vs auditory_all`], [`d = -2.941`, `p = 1.04e-25`], [`d = -3.121`, `p = 1.97e-21`], [`d = -2.858`, `p = 7.11e-15`], [`d = -2.969`, `p = 8.33e-18`],
    [`9D peak_displacement / other_mean vs auditory_all`], [`d = -2.096`, `p = 1.09e-25`], [`d = -2.134`, `p = 1.97e-21`], [`d = -2.306`, `p = 7.11e-15`], [`d = -1.998`, `p = 8.86e-18`],
    [`9D entropy_rate / standard_arrowcue vs auditory_arrowcue`], [`d = -4.731`, `p = 1.04e-25`], [`d = -5.054`, `p = 1.97e-21`], [`d = -5.134`, `p = 7.11e-15`], [`d = -4.566`, `p = 8.33e-18`],
  ),
  caption: [Selected auditory anchors remain large after residual-label exclusion and within diagnostic subgroups. The main auditory event effect is therefore not driven by the residual `raw_nan_onset_sec` subset.]
) <tab-s3-auditory-stability>

The main point is not exact numerical equality across subgroups, but directional and magnitude stability. The auditory event regime remains dramatically less entropic and more transition-sparse in both controls and Parkinson subjects.

= Supportive global rows under subject exclusion and winsorization

The supportive disease layer used in the main paper is smaller than the event-primary layer, so it is more important to ask whether a single extreme subject or a mild tail clip changes the story. The two article-facing group rows were therefore rerun after excluding `sub-112` and after pooled `2.5%/97.5%` winsorization.

#figure(
  kind: table,
  table(
    columns: (2.3fr, 1.2fr, 1.2fr, 1.2fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Full cohort*], [*Exclude `sub-112`*], [*Winsorized*]),
    [`global 3D m_median`], [`d = -0.602`, `p = 0.00407`], [`d = -0.644`, `p = 0.00218`], [`d = -0.589`, `p = 0.00407`],
    [`reachability tube_q_ratio_h4_mean`], [`d = +0.557`, `p = 0.00251`], [`d = +0.565`, `p = 0.00224`], [`d = +0.559`, `p = 0.00251`],
  ),
  caption: [The supportive global Parkinson-control anchors remain directionally stable after explicit outlier exclusion and mild winsorization.]
) <tab-s3-group-stability>

These rows are therefore not artifacts of one flagged subject. If anything, exclusion of `sub-112` slightly strengthens the selected global differences rather than weakening them.

= Explicit 9D Jacobian outlier check

The handover noted `sub-112` as the strongest `9D` Jacobian-amplitude outlier. A direct follow-up on `global_mnps_jacobian_9d / frobenius_norm_median` shows why the final paper does not depend on that family.

#figure(
  kind: table,
  table(
    columns: (2.45fr, 1.15fr, 1.15fr, 1.15fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Full cohort*], [*Exclude `sub-112`*], [*Winsorized*]),
    [`global 9D Jacobian frobenius_norm_median`], [`d = +0.0170`, `p = 0.975`], [`d = +0.101`, `p = 0.815`], [`d = +0.0151`, `p = 0.973`],
  ),
  caption: [The flagged `9D` Jacobian outlier does not convert the null global Jacobian family into a hidden article-facing result.]
) <tab-s3-jacobian-null>

This is why the main manuscript keeps the disease-support layer on global `m` and reachability rather than promoting a Jacobian claim that the data do not support.

= What remains unresolved

The current robustness package still leaves four boundaries unresolved.

1. The bundle has no regional outputs, so no regional localization robustness analysis can be performed.
2. `labels/stage` remains intentionally unusable as a semantic event surface in this dataset.
3. The current validation package is internal to one processed `ds004574` export and does not test external replication.
4. The dominant event result is primarily `auditory vs standard`; the current data do not support a comparably strong `auditory vs visual` dissociation.

= Files

The tables in this supplement are backed by:

- `results/parkinson_auditory_recall_20260602/selected_metric_robustness.csv`
- `results/parkinson_auditory_recall_20260602/selected_metric_robustness.md`
- `results/parkinson_auditory_recall_20260602/event_contrasts.csv`
- `results/parkinson_auditory_recall_20260602/standard_analysis/ds004574_subject_metrics_20260602_120537.parquet`
