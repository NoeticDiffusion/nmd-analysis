#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "Psychosis Supplementary QC",
  subtitle: "QC pass rates, leave-one-out stability, and interpretation boundaries",
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

This supplement collects the reviewer-facing QC and robustness material that is now intentionally separated from the main psychosis manuscript:

- family-level QC pass rates,
- leave-one-out stability for the headline effects,
- the special caution attached to `ds003947` unmedicated `n = 8`,
- and the reason block-MNJ remains exploratory despite readable raw effects.

The key message is asymmetric rather than uniformly positive. The main `3D`, `9D`, trajectory, and `3D/9D MNJ` families are QC-clean enough for the paper's bounded claims, but the article does *not* support strong block-level or small-subgroup overinterpretation.

= QC pass profile

#figure(
  kind: table,
  table(
    columns: (1.0fr, 1.6fr, 0.9fr, 0.95fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Dataset*],
      [*Analysis family*],
      [*Rows*],
      [*Finite ok*],
      [*Validity limited*],
      [*QC pass*],
    ),
    [ds003944], [`global_mnps_3d`], [984], [1.00], [0.00], [1.00],
    [ds003944], [`global_mnps_9d`], [2952], [1.00], [0.00], [1.00],
    [ds003944], [`global_mnps_jacobian_3d`], [1640], [1.00], [0.00], [1.00],
    [ds003944], [`global_mnps_jacobian_9d`], [1640], [1.00], [0.00], [1.00],
    [ds003944], [`global_mnps_jacobian_9d_block_jacobian`], [3690], [0.333], [0.00], [0.333],
    [ds003944], [trajectory dynamics], [1640], [1.00], [0.00], [1.00],
    [ds003947], [`global_mnps_3d`], [732], [1.00], [0.00], [1.00],
    [ds003947], [`global_mnps_9d`], [2196], [1.00], [0.00], [1.00],
    [ds003947], [`global_mnps_jacobian_3d`], [1220], [1.00], [0.00], [1.00],
    [ds003947], [`global_mnps_jacobian_9d`], [1220], [1.00], [0.049], [0.951],
    [ds003947], [`global_mnps_jacobian_9d_block_jacobian`], [2745], [0.333], [0.00], [0.333],
    [ds003947], [trajectory dynamics], [1220], [1.00], [0.00], [1.00],
  ),
  caption: [Article-local QC summary derived from `qc_summary_article.csv`. The main first-order and trajectory families are effectively clean, whereas block-MNJ remains the obvious weak point.]
) <tab-s3-qc>

The primary implication is that the manuscript's hierarchy is data-driven rather than stylistic. `3D`, `9D`, and trajectory families can reasonably carry the main text, while block-MNJ should remain exploratory because only one third of its potential rows are finite and testable in both cohorts.

= Leave-one-out stability

#figure(
  kind: table,
  table(
    columns: (1.35fr, 1.65fr, 0.9fr, 1.15fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Check*],
      [*Feature*],
      [*Full `d`*],
      [*Leave-one-out range*],
      [*Sign consistency*],
    ),
    [ds003944 main], [`m_mean`, FEP medicated vs Healthy], [0.881], [`0.837` to `0.961`], [1.000],
    [ds003947 main], [`m_delta_mean_median`, FEP unmedicated vs Healthy], [-1.385], [`-1.569` to `-1.213`], [1.000],
    [ds003944 pooled], [`m_e_mean`, Healthy vs FEP], [0.720], [`0.663` to `0.806`], [1.000],
  ),
  caption: [Compact leave-one-out robustness summary for the three headline paper-facing effects. No single subject reversed the sign of any of these effects.]
) <tab-s3-loo>

#figure(
  image("figures/psychosis_qc_robustness.svg", width: 100%),
  caption: [QC and robustness summary for the psychosis article. The left panel shows family-level QC pass rates, and the right panel shows leave-one-out ranges for the headline effects.]
) <fig-s3-qc>

These omission checks do not turn the effects into universal biomarkers, but they do reduce the simplest concern that one anomalous participant is driving the headline findings.

= What the robustness pass supports

The QC / robustness package supports four bounded claims:

1. the main first-order and trajectory families are numerically stable enough for article-facing use,
2. the `ds003944` medicated-`m` displacement is not driven by one subject,
3. the `ds003947` trajectory effect is strong enough to survive single-subject omission despite the small subgroup,
4. and the pooled `ds003944` sensitivity signal is directionally stable.

It does *not* support stronger claims such as:

1. block-MNJ as a confirmatory layer,
2. `ds003947` unmedicated dynamics as a settled externally generalizable biomarker,
3. or full confound removal for medication, severity, and cohort-composition effects.

= Small-subgroup and block-layer cautions

Two reviewer-facing cautions should remain explicit.

== `ds003947` unmedicated subgroup

The `ds003947` headline dynamic effect is interesting precisely because it survives correction and leave-one-out omission despite a small unmedicated subgroup. But `n = 8` remains a real boundary. The effect should therefore be described as a strong cohort-local signal that motivates replication, not as a settled subgroup biomarker.

== Block-MNJ

Block-MNJ produces readable raw effects in both cohorts and even clinically suggestive `c_rot_mean` phenotype rows. However, the low finite / testable fraction means that this family is more fragile than the main `MNPS` and trajectory layers. The right role for block-MNJ in the current package is mechanistic context and hypothesis generation, not main-text confirmation.

= Files

The robustness material summarized here is backed primarily by:

- `qc_summary_article.csv`
- `figures/psychosis_qc_robustness.svg`

The leave-one-out ranges quoted here are the article-facing values carried into the manuscript and figure package.

#bibliography("psychosis.bib", style: "apa")

