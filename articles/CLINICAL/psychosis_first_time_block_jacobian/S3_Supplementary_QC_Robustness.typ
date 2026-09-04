#import "../psychosis_first_time_geometric_trajectory/network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "Block-Jacobian Coupling QC",
  subtitle: "Data coverage, artefact risks, confound checks, and outstanding validations",
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

This supplement documents:

1. data coverage in the block Jacobian pipeline,
2. artefact risks specific to block Jacobian coupling metrics,
3. known confounds and their expected direction of influence,
4. outstanding validation steps before main results can be treated as established,
5. and the relationship between the block Jacobian results and the companion study QC.

= Data coverage

The `stratified_block_jacobians_subjects_*.csv` files contain one row per subject per block pair. All 82 `ds003944` subjects and all 61 `ds003947` subjects contributed block Jacobian coupling metrics. No subjects were excluded.

#figure(
  kind: table,
  table(
    columns: (0.9fr, 0.9fr, 0.9fr, 1.2fr),
    align: left,
    inset: 5pt,
    table.header(
      [*Dataset*],
      [*Total subjects*],
      [*Subjects with block Jacobian data*],
      [*Block pairs per subject*],
    ),
    [ds003944], [82], [82], [9 (3×3 family pairs)],
    [ds003947], [61], [61], [9 (3×3 family pairs)],
  ),
  caption: [Data coverage. All subjects have complete block Jacobian data. Each subject contributes 9 block pair rows × up to 5 metrics per row = up to 45 scalar values.]
) <tab-s3-coverage>

= Artefact risks

== Between-group confounds in mean coupling level

The block Jacobian Frobenius norm is an absolute measure of coupling magnitude. If groups differ in global signal amplitude or in the overall scale of the Jacobian eigenspectrum, this would produce coupling differences across all block pairs simultaneously, rather than the selective $e → e$ and $m → e$ pattern observed. The specificity of the observed effects (significant primarily in the entropy-related blocks, not in $m → m$ or in most off-diagonal pairs) argues against a global amplitude confound, but does not rule it out.

_Recommended validation_: regress each subject's mean total Frobenius norm (sum across all 9 blocks) from each block's Frobenius norm and re-run contrasts on residuals. If the $e → e$ gradient survives residualisation, it is specific to the entropy block rather than a global scaling effect.

== Medication heterogeneity within the medicated group

The medicated FEP group in `ds003944` includes subjects on different antipsychotic agents (typical, atypical, depot preparations) at varying doses (median CPZ equivalent = 227.3, range not reported). The observed $e → e$ elevation in medicated FEP is an average over this heterogeneous group. If only a subset of antipsychotic agents produce the coupling elevation, the true effect in the relevant sub-group would be larger and the estimate for the remainder would be diluted toward zero.

_Recommended validation_: plot `e->e block_frobenius_mean` against CPZ equivalent dose within the medicated group. A positive dose-response correlation would provide within-group evidence for the antipsychotic-coupling hypothesis.

== Illness duration and prior episode history

The FEP cohorts are first-episode samples, but the exact time from first symptoms to scan varies. Longer illness duration or more severe prodromal symptoms at scan could account for coupling differences independently of medication. This information is not available in the current analysis.

== Age and sex

Groups are approximately age- and sex-matched (see S2 group composition table). Age and sex correlates with EEG power and could in principle affect the Jacobian coupling structure, but given the close matching across groups, this is an unlikely primary driver of the observed effects.

= Outstanding: leave-one-subject-out sensitivity for the primary $e → e$ gradient

The primary $e → e$ Frobenius gradient (unmedicated < healthy < medicated in `ds003944`) rests on $n = 19$ for the unmedicated group. A single outlier with unusually low `e->e block_frobenius_mean` in the unmedicated group, or unusually high in the medicated group, could exaggerate the gradient.

_Recommended check_: run Mann-Whitney U for the three $e → e$ contrasts after leaving out each subject in turn and record the range of $d$ values. If the gradient is present in all leave-one-out replicates, it is robust to individual subjects. If one subject's removal collapses the effect, that subject should be reported as a potential outlier.

= Outstanding: global coupling residualisation

As noted above, the block Frobenius results should be residualised against the mean total coupling level to verify that the $e → e$ and $m → e$ effects are family-specific rather than globally scaled.

= Outstanding: within-medicated dose-response

A correlation between CPZ equivalent dose and `e->e block_frobenius_mean` within the medicated group would be the strongest available within-group evidence for the antipsychotic-coupling interpretation. This has not been computed for the present draft.

= Outstanding: temporal stability of coupling structure

The current analysis uses per-window mean block coupling metrics, collapsing temporal variation within the recording. If the $e → e$ coupling is elevated only at specific moments in the recording (e.g., early windows when medication is less absorbed, or late windows when attention lapses), the mean would underestimate the effect during those periods and could produce artefactual group differences.

_Recommended check_: compute the standard deviation of per-window `block_frobenius` within each subject and test whether the SD itself differs between groups. Elevated within-subject coupling variance in unmedicated FEP would suggest intermittent rather than tonic coupling deficit.

= Relationship to companion study QC

The companion static-geometry study @langell2026_psychosis ran leave-one-subject-out, cross-fitted fold score, and between-site robustness checks on the cohort-anchored MNPS coordinates. Those checks do not transfer directly to the block Jacobian metrics, because the block Jacobian is a different output layer of the NMD pipeline with different statistical properties.

The block Jacobian metrics are pre-aggregated by NMD and are not expected to have the same sensitivity to outlier subjects or codebook choices as the trajectory metrics. However, the upstream NMD fitting is the same for both, so any artefacts introduced by the embedding or manifold estimation will propagate to the block Jacobian as well.

The most relevant upstream quality concern is the reliability of the 9×9 Jacobian estimation: if the local linearisation is unstable (e.g., due to noisy coordinate estimates or short recording length), the block Frobenius norms will reflect estimation noise rather than true coupling structure. The NMD 2.1 Jacobian estimator uses regularisation to mitigate this, but the regularisation parameters have not been swept for this dataset.

= Summary of QC status

#figure(
  kind: table,
  table(
    columns: (2.0fr, 1.0fr, 1.5fr),
    align: left,
    inset: 5pt,
    table.header(
      [*Validation*],
      [*Status*],
      [*Priority*],
    ),
    [Leave-one-subject-out on $e → e$ gradient], [Not done], [High],
    [Global coupling residualisation], [Not done], [High],
    [Within-medicated dose-response ($d$ vs CPZ)], [Not done], [Medium],
    [Within-subject coupling variance check], [Not done], [Medium],
    [Upstream Jacobian regularisation sweep], [Not done], [Low / exploratory],
  ),
  caption: [QC validation status. The two high-priority checks should be completed before the main $e → e$ gradient result is treated as established.]
) <tab-s3-qc>

#bibliography("../psychosis_first_time_geometric_trajectory/psychosis.bib", style: "apa")
