#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness - Resting-State Neural Geometry Across Depressive Symptom Burden",
  short-title: "Depression Supplementary QC",
  subtitle: "Denominator visibility, leave-one-subject-out stability, and centroid-adjusted caution",
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

This supplement collects the most practical review-facing robustness material for the resting-state depression article:

1. denominator visibility for the selected block surface,
2. leave-one-subject-out stability for the selected low/high and continuous-BDI rows,
3. centroid-adjusted sensitivity rows,
4. and the main caution points that remain even after those checks.

= Denominator visibility

At the subject level, the selected article blocks all start from the same processed cohort. Every selected block resolves for all `122` subjects, with `121` subjects carrying usable BDI values.

#figure(
  kind: table,
  table(
    columns: (1.45fr, 1.6fr, 0.85fr, 0.8fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Block*], [*Metric*], [*Total*], [*Low*], [*Mid*], [*High*]),
    [`Global 3D MNPS`], [`d_median`], [`122`], [`76`], [`15`], [`30`],
    [`Global 9D MNPS`], [`d_s_mean`], [`122`], [`76`], [`15`], [`30`],
    [`Global 3D MNJ`], [`spectral_radius_median`], [`122`], [`76`], [`15`], [`30`],
    [`Global 9D MNJ`], [`rotational_power_mean`], [`122`], [`76`], [`15`], [`30`],
    [`9x9 block MNJ`], [`block_anisotropy_mean`], [`122`], [`76`], [`15`], [`30`],
    [`Reachability cones`], [`tube_log_eig_var_mean`], [`122`], [`76`], [`15`], [`30`],
    [`Tier-2 EMMI`], [`mv_median`], [`122`], [`76`], [`15`], [`30`],
    [`Distribution summary`], [`e_m_mad_sigma`], [`122`], [`76`], [`15`], [`30`],
  ),
  caption: [Selected block coverage from `results/additional_qc_20260609/qc_selected_block_coverage.csv`.]
) <tab-s3-coverage>

This denominator clarity matters because the `contrast_results` tables themselves report row-level counts that can be confused with subject-level support. The article's inferential object is the subject-level resting-state summary, and at that level the selected surface is complete apart from the single invalid BDI row.

= Leave-one-subject-out stability

The strongest selected rows remain directionally stable under leave-one-subject-out omission.

#figure(
  kind: table,
  table(
    columns: (1.55fr, 1.45fr, 0.85fr, 1.25fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*Block*], [*Metric*], [*Full `d`*], [*Leave-one-out `d` range*], [*Sign consistency*]),
    [`Global 9D MNJ`], [`rotational_power_mean`], [`0.767`], [`0.716` to `0.851`], [`1.00`],
    [`Reachability cones`], [`tube_log_eig_var_mean`], [`-0.816`], [`-0.893` to `-0.791`], [`1.00`],
    [`Distribution summary`], [`e_m_mad_sigma`], [`0.984`], [`0.917` to `1.068`], [`1.00`],
    [`Tier-2 EMMI`], [`mv_median`], [`-0.453`], [`-0.514` to `-0.332`], [`1.00`],
    [`Global 3D MNPS`], [`d_median`], [`0.039`], [`-0.043` to `0.120`], [`0.967`],
    [`Global 3D MNJ`], [`spectral_radius_median`], [`0.022`], [`-0.204` to `0.095`], [`0.934`],
  ),
  caption: [Representative leave-one-subject-out rows from `results/additional_qc_20260609/qc_leave_one_subject_out.csv`.]
) <tab-s3-loo-d>

The same pattern appears for continuous BDI associations:

1. `Global 9D MNJ / rotational_power_mean`: full `rho = 0.310`, leave-one-out range `0.295` to `0.335`
2. `Reachability / tube_log_eig_var_mean`: full `rho = -0.343`, leave-one-out range `-0.372` to `-0.329`
3. `Distribution / e_m_mad_sigma`: full `rho = 0.358`, leave-one-out range `0.346` to `0.382`

The weak `3D` rows also remain weak under omission. This is useful because it argues against a simple one-subject explanation for the main ranking of effects.

= Centroid-adjusted sensitivity

The next reviewer-facing question is whether the strongest rows survive once baseline centroid position is taken into account.

#figure(
  kind: table,
  table(
    columns: (1.55fr, 1.2fr, 0.95fr, 0.85fr, 0.85fr),
    align: left,
    inset: 4pt,
    table.header([*Block*], [*Metric*], [*Adj. beta*], [*Adj. `q`*], [*Residual `d`*]),
    [`Block MNJ m->m`], [`block_frobenius_mean`], [`-0.0243`], [`0.0509`], [`-0.474`],
    [`Distribution summary`], [`e_m_mad_sigma`], [`0.179`], [`0.0825`], [`0.577`],
    [`Block MNJ m->d`], [`block_frobenius_mean`], [`-0.0212`], [`0.123`], [`-0.330`],
    [`Global 9D MNJ`], [`rotational_power_mean`], [`0.00175`], [`0.153`], [`0.375`],
    [`Tier-2 EMMI`], [`mv_median`], [`-0.165`], [`0.153`], [`-0.378`],
    [`Reachability cones`], [`tube_log_eig_var_mean`], [`-1.176`], [`0.195`], [`-0.305`],
  ),
  caption: [Centroid-adjusted focus rows from `results/additional_qc_20260609/qc_centroid_adjusted_focus.csv`.]
) <tab-s3-centroid-adjusted>

This sensitivity check changes the interpretation boundary, but not the main message:

1. the unadjusted ranking of strong rows is real,
2. some of that separation plausibly overlaps with baseline coordinate displacement,
3. and the cleanest centroid-adjusted survivor is the `block_frobenius_mean` `m -> m` row, with distribution close behind.

That means the paper is stronger as a claim about the *resting-state export surface as a whole* than as a proof that every reported dynamic row is fully independent of first-order position.

= Main robustness takeaways

The QC pass supports four practical conclusions:

1. the selected block surface is not denominator-fragile at the subject level,
2. the strongest unadjusted rows are not one-subject artifacts,
3. the weak `3D` rows stay weak under omission,
4. and centroid-adjustment attenuates the broader story rather than overturning it.

The most defensible interpretation therefore remains:

1. reachability, `9D` local dynamics, and distribution structure carry the clearest symptom-linked signal,
2. coarse `3D` summaries remain secondary,
3. and some of the stronger dynamic differences are partly entangled with higher-resolution baseline state-space position.

= Review-facing caution points

1. This is still a single-cohort study in a young, age-compressed resting-state sample.
2. The middle BDI band remains small (`n = 15`), which limits confidence in the `14-19 vs 20-63` comparison.
3. Leave-one-subject-out omission is useful, but it is not external replication.
4. The centroid-adjusted pass is a sensitivity analysis, not a replacement inferential framework for the main article.
5. The strongest block-level story is internally coherent, but it remains cohort-local until replicated elsewhere.

= Files

The robustness material in this supplement is backed mainly by:

- `results/additional_qc_20260609/qc_selected_block_coverage.csv`
- `results/additional_qc_20260609/qc_leave_one_subject_out.csv`
- `results/additional_qc_20260609/qc_centroid_adjusted_focus.csv`
- `results/additional_qc_20260609/additional_qc_summary.md`
- `results/centroid_adjusted_dynamic_summary.csv`
