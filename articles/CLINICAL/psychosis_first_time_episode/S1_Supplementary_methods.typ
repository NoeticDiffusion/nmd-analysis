#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "Psychosis Supplementary Methods",
  subtitle: "Shared-reference contract, metric hierarchy, and reviewer-facing method detail",
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

This supplement expands the methods that were intentionally compressed in the main psychosis manuscript. It focuses on six items:

1. the processed-bundle and subgroup contract used for `ds003944` and `ds003947`,
2. the shared-reference coordinate definition used for the main between-subject contrasts,
3. the fixed `3D` / `9D` NeuralManifoldDynamics chart basis,
4. the analysis-family hierarchy used to keep claims bounded,
5. the reviewer-facing baseline-comparator panel,
6. and the exploratory clinical-phenotype splits.

The main paper's empirical target is narrow. It does *not* claim that one exact metric should replicate across all psychosis cohorts. It asks whether medication-stratified psychosis separation remains readable under one locked shared-reference analysis surface across two independent resting-state EEG cohorts.

= Processed bundle contract

The paper-facing rerun consumes two OpenNeuro-derived psychosis cohorts:

- `ds003944`
- `ds003947`

Both were processed through the same NeuralManifoldDynamics 2.1 export contract before the article-local summaries were built.@langell2026_mndm The article-local downstream stack then exports:

- global `3D` MNPS summaries,
- stratified `9D` MNPS summaries,
- global `3D` MNJ summaries,
- stratified `9D` MNJ summaries,
- `9 x 9` block-MNJ summaries,
- trajectory-level summaries,
- pooled `Healthy vs FEP` sensitivity passes,
- reviewer-facing baseline comparators,
- exploratory phenotype splits,
- and QC / leave-one-out summaries.

The subgroup contract used throughout the manuscript is:

- `Healthy`
- `FEP unmedicated`: `CPZ_at_scan = 0` or `n/a`
- `FEP medicated`: `CPZ_at_scan > 0`

This is an observational subgroup split, not a causal medication model. Medication status may remain entangled with illness severity, treatment selection, and cohort composition.

= Shared-reference coordinate contract

The primary between-subject contrasts in the psychosis paper use the cohort-anchored coordinate contract rather than subject-relative coordinates. In the NeuralManifoldDynamics export, the cohort-anchored layers are explicitly marked as the preferred layers for clinical group comparison, whereas the subject-anchored layers are intended for within-subject geometry.@langell2026_mndm

Operationally, the export stores a subject-balanced external anchor for each upstream feature under `/feature_anchors/per_feature`, including a center term $c_j$, a scale term $s_j$, the support counts, and the associated robust quantiles. The anchored feature transform can be written generically as

$
tilde(phi)_(t,j) = frac(phi_(t,j) - c_j, s_j + epsilon),
$

where $phi_(t,j)$ is the upstream feature for window $t$ and feature $j$. The anchored feature vector $tilde(phi)_t$ is then carried into the fixed downstream `3D` and `9D` projections. This is what makes the paper-facing coordinates interpretable as a common cross-subject reference frame rather than as subject-local reparameterizations.

The practical reason for using this contract in the psychosis article is simple: the main inferential question is between-subject group separation. Subject-anchored coordinates remain useful for within-subject geometry, but the article's primary comparisons are `Healthy` vs `FEP unmedicated`, `Healthy` vs `FEP medicated`, and `FEP unmedicated` vs `FEP medicated` in one shared-reference frame.

= NeuralManifoldDynamics chart basis

The coarse chart used throughout the article is

$
x_t = [m_t, d_t, e_t]^T,
$

and the stratified chart is

$
x_t^((9)) = [m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m]^T.
$

As in the main paper, these axes are treated as release-bound operational measurement families rather than as direct stand-ins for one neurotransmitter, one anatomical circuit, or one oscillatory band.@langell2025_6 @langell2025_stratified @langell2025_mnj @langell2026_mndm

The local dynamical layer is summarized through the Jacobian family. In compact form, local flow is written as

$
dot(x)(t) = f(x_t, t),
$

with local linear approximation

$
dot(x) approx A (x - bar(x)) + b,
$

where the estimated Jacobian is

$
hat(J) = A.
$

This is why the manuscript distinguishes:

- first-order position summaries (`MNPS`),
- trajectory summaries (how coordinates move over short horizons),
- and Jacobian / block-Jacobian summaries (how local flow expands, contracts, rotates, or redirects).

= Analysis-family hierarchy

The paper-facing hierarchy is fixed before interpretation:

#table(
  columns: (1.1fr, 1fr, 2.3fr),
  inset: 5pt,
  align: (left, center, left),
  table.header([*Layer*], [*Status*], [*Reason*]),
  [`3D MNPS`], [Primary], [highest interpretability and strongest QC pass profile],
  [Trajectory summaries], [Primary / secondary], [directly test whether psychosis separation appears in short-horizon movement],
  [`9D MNPS`], [Secondary], [mechanistic decomposition of the same shared-reference trajectory],
  [`3D` / `9D MNJ`], [Exploratory-secondary], [useful local-dynamical context, but estimator-sensitive relative to first-order coordinates],
  [Reachability], [Sensitivity], [reviewer-facing check on coherent reachable-neighborhood shifts],
  [Block-MNJ], [Exploratory], [reduced finite / testable fraction and no family-wise-confirmed headline effects],
)

Claim discipline follows from that table:

- primary claims concern corrected `3D` and trajectory-level medication-stratified separation,
- secondary claims concern stable `9D` localization and pooled-FEP robustness,
- and reachability, block-MNJ, and phenotype links remain supportive or exploratory unless explicitly stated otherwise.

BH-FDR is applied within each contrast and analysis family. The article therefore uses family-local multiplicity control rather than one manuscript-wide correction over the full metric universe.

= Pooled sensitivity contract

The reviewer-facing pooled sensitivity pass collapses all FEP participants into one `FEP` group and contrasts that pooled group against `Healthy`. It uses the same cleaned outputs and the same QC / statistical settings as the main three-group pass.

This pooled view is intentionally *not* the main inferential layer. Its purpose is to test whether the psychosis signal survives medication pooling or whether pooling partly averages away clinically meaningful heterogeneity. The answer differs by cohort, which is precisely why the main paper keeps medication stratification primary.

= Baseline comparator panel

The baseline panel is included as a calibration layer rather than as a winner-take-all benchmark. From each subject's `features_raw` H5 export, the article extracts compact conventional EEG summaries:

- spectral medians: `delta`, `theta`, `alpha`, `beta`, `alpha/theta`, `beta/alpha`
- complexity medians: Hjorth mobility, Hjorth complexity, permutation entropy, sample entropy
- simple trajectory baselines: speed, curvature, corner entropy, corner-transition entropy

These baselines are tested under the same subgroup contrasts, with Welch tests and BH-FDR within dataset, contrast, and baseline family. The intent is to answer a reviewer-facing question: do simpler EEG summaries already carry part of the separation, or does the shared-reference geometry expose something that simple baselines miss?

= Exploratory phenotype analyses

Two article-local FEP-only phenotype splits were added to connect the geometry to clinically recognizable symptom structure:

1. `SAPS_Q7`, using `Low hallucinations` (`<= 1`) versus `High hallucinations` (`>= 3`) and excluding the intermediate score `2`, based on SAPS hallucination severity.@andreasen1984scale
2. `BPRST19`, using a within-cohort FEP median split for total symptom burden based on BPRS total severity.@overall1962brief

These analyses remain exploratory. They are useful for asking whether symptom burden aligns more with first-order displacement, trajectory change, or block-coupling structure, but they are not part of the paper's primary replication target.

= Files

The main methods-facing and audit-facing files used by the psychosis article live under `articles/CLINICAL/psychosis_first_time_episode/results/`, especially:

- `demography_summary.csv`
- `psychosis_metric_family_summary.md`
- `psychosis_metric_family_detail.csv`
- `pooled_fep_reachability_summary.md`
- `psychosis_baseline_comparator_summary.csv`
- `clinical_phenotype_summary.csv`
- `clinical_phenotype_detail.csv`
- `qc_summary_article.csv`
- `baseline_comparator_manifest.json`

`S2` collects the data-heavy tables, `S3` summarizes QC / robustness, and `S4` translates the manuscript into cautious clinician-facing language.

#bibliography("psychosis.bib", style: "apa")
