#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "First-Episode Psychosis Geometry Across Two Resting-State EEG Cohorts",
  short-title: "Psychosis Geometry Across Two EEG Cohorts",
  subtitle: "NeuralManifoldDynamics 2.1 / Noetic Diffusion Theory analysis of ds003944 and ds003947",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "first-episode psychosis",
    "EEG",
    "NeuralManifoldDynamics",
    "MNPS",
    "MNJ",
    "medication stratification",
  ),
  article-type: "Research Article / Methods-Anchored Empirical Report",
  abstract: [
    We analysed two resting-state EEG cohorts of first-episode psychosis using NeuralManifoldDynamics 2.1 within a Noetic Diffusion Theory (NDT) framework to estimate low-dimensional neural-state trajectories and local dynamics for each subject in one shared cross-subject reference frame. The primary design compared `Healthy`, `FEP unmedicated`, and `FEP medicated`, with `CPZ_at_scan > 0` treated as medicated and `CPZ_at_scan = 0` or `n/a` treated as unmedicated. The intended replication target was not one universal feature-level biomarker, but whether medication-stratified psychosis separation remained visible across cohorts under the same shared-reference analysis surface. In OpenNeuro dataset `ds003944` (`32` healthy, `19` unmedicated, `31` medicated), the strongest corrected effects were stable first-order and stratified `m`-family shifts in `FEP medicated vs Healthy`, including global `m_mean` ($d = 0.881$, $q = 0.0157$), global `m_median` ($d = 0.865$, $q = 0.0090$), and stratified `m_o_mean` ($d = 0.814$, $q = 0.0270$). In OpenNeuro dataset `ds003947` (`30` healthy, `8` unmedicated, `23` medicated), the strongest corrected effect instead appeared in dynamics: `FEP unmedicated vs Healthy` showed reduced trajectory `m_delta_mean_median` ($d = -1.385$, $q = 0.0400$), while higher-order Jacobian support remained exploratory. A pooled `Healthy vs FEP` sensitivity test confirmed a stable psychosis signal in `ds003944` but weakened the `ds003947` dynamic effect, supporting medication stratification rather than premature pooling. Reviewer-facing baseline comparators showed that some subgroup separation was also visible in simple spectral and complexity summaries, so the present report should be read as demonstrating an interpretable shared state-space analysis surface rather than clear superiority over conventional EEG. Because the `ds003947` unmedicated subgroup was small (`n = 8`), that dynamic effect should be treated as a strong cohort-local signal requiring replication rather than as a settled subgroup biomarker. These results support a bounded conclusion: NeuralManifoldDynamics 2.1 exposes medication-sensitive psychosis geometry across two FEP EEG cohorts, but the feature carrying the signal is cohort-dependent, so the framework is best treated as a reproducible shared-reference analysis surface rather than a universal FEP biomarker.
  ],
  data-availability: [
    All paper-facing exports used in this draft were generated locally from the 2026-05-20 NeuralManifoldDynamics 2.1 runs and written under `articles/CLINICAL/psychosis_first_time_episode/results/`, with figures under `articles/CLINICAL/psychosis_first_time_episode/figures/`. The main article relies especially on `demography_summary.csv`, `psychosis_metric_family_summary.md`, `psychosis_metric_family_detail.csv`, `pooled_fep_reachability_summary.md`, `psychosis_baseline_comparator_summary.csv`, `clinical_phenotype_summary.csv`, `clinical_phenotype_detail.csv`, `qc_summary_article.csv`, and `baseline_comparator_manifest.json`. Extended methods, detailed tables, robustness notes, and clinician-facing interpretation are provided in `S1_Supplementary_methods.typ`, `S2_Supplementary_data.typ`, `S3_Supplementary_QC_Robustness.typ`, and `S4_Supplementary_Clinical.typ`.
  ],
  competing-interests: [
    No competing interests are declared in this manuscript draft.
  ],
)

= Introduction

First-episode psychosis is unlikely to be captured by a single geometric signature. Clinical state, medication exposure, and cohort composition can all redistribute the observable signal across first-order coordinates, higher-dimensional substructure, and Jacobian-derived dynamics. A useful analysis framework therefore has to do two things at once: preserve interpretable subject summaries and place recordings in a common reference frame for between-subject contrasts. More broadly, psychosis has long been framed as a disorder of disturbed functional integration and dysconnectivity rather than of isolated regional abnormality @stephan2009dysconnection @petterssonyeo2011dysconnectivity. Existing EEG and clinical psychosis literatures already point toward altered microstate dynamics, aberrant salience, alpha-band dysfunction, and abnormal complexity, but they do not yet provide one unified low-dimensional dynamical chart @rieger2016microstate @kapur2003psychosis @palaniyappan2012salience @takahashi2013complexity.

Resting EEG studies also suggest that relevant abnormalities are already visible near illness onset. Classical qEEG work found increased low-frequency activity and reduced alpha in first-episode schizophrenia, while later FEP studies linked resting spectral abnormalities to 1-year symptomatic and functional outcome @sponheim1994resting @renaldi2019fep_eeg.

Here we use NeuralManifoldDynamics 2.1, an NDT-aligned pipeline that converts each resting EEG recording into a trajectory in a low-dimensional neural state space together with local Jacobian estimates @langell2025_6 @langell2026_compendium @langell2026_mndm. In practice, this gives one reproducible set of 3D coordinates, one higher-resolution 9D decomposition, and one set of local dynamical summaries per subject @langell2025_stratified @langell2025_mnj. The present manuscript applies that workflow to two psychosis cohorts, `ds003944` and `ds003947`, and asks a focused question: when we split FEP into medicated and unmedicated groups, where do the reproducible cohort-level separations appear? The intended replication target is not one exact feature, but whether medication-stratified psychosis separation remains visible in a fixed shared-reference state space across cohorts. The aim is not to replace established EEG markers, but to test whether a fixed shared-reference state-space can organize them into interpretable first-order, trajectory-level, and local-dynamical summaries.

This is not a benchmark across multiple normalization schemes. Instead, it is a paper-facing demonstration of one reproducible NeuralManifoldDynamics 2.1 analysis pathway: three-group contrasts, common-effect summaries, and shared figures interpreted in one cross-subject state space.

= Methods

== Datasets and group definition

Both datasets were analysed from the 2026-05-20 NeuralManifoldDynamics 2.1 runs. The underlying resting-state first-episode psychosis EEG cohorts correspond to the OpenNeuro datasets `ds003944` (Resting Task 1) and `ds003947` (Resting Task 2) @ds003944_openneuro @ds003947_openneuro. Their shared alpha-network article context is provided by Phalen et al. @phalen2020alpha, and the same public EEG datasets have also been reused in recent classification work @gengecbenli2023cissa @redwan2024psd.

#table(
  columns: (1.1fr, 1.35fr, 0.7fr, 0.9fr, 0.9fr, 1.0fr, 0.95fr),
  inset: 6pt,
  align: (left, left, center, center, center, center, center),
  table.header(
    [*Dataset*],
    [*Group*],
    [*N*],
    [*Age mean*],
    [*Age SD*],
    [*Female n (%)*],
    [*CPZ median*],
  ),
  [ds003944], [Healthy], [32], [21.61], [3.97], [12 (37.5%)], [--],
  [ds003944], [FEP unmedicated], [19], [22.33], [4.21], [5 (26.3%)], [`0 / n.a.`],
  [ds003944], [FEP medicated], [31], [22.34], [5.41], [11 (35.5%)], [`227.3`],
  [ds003947], [Healthy], [30], [24.20], [5.13], [14 (46.7%)], [--],
  [ds003947], [FEP unmedicated], [8], [25.01], [5.06], [2 (25.0%)], [`0 / n.a.`],
  [ds003947], [FEP medicated], [23], [22.82], [4.57], [7 (30.4%)], [`303.0`],
)

#v(6pt)

Medication grouping used the participant metadata field `CPZ_at_scan`. We assigned `CPZ_at_scan > 0` to `FEP medicated`, and `CPZ_at_scan = 0` or `n/a` to `FEP unmedicated`. Healthy controls remained in a separate `Healthy` group. Missing CPZ values were rare: `2 / 50` FEP participants in `ds003944` and `0 / 31` in `ds003947`. Group counts above refer to unique participants; inferential `N` for each feature is reported directly in the exported contrast tables and can vary slightly by block after QC. We treated medication state as a primary stratification variable rather than as a nuisance-only covariate because antipsychotic exposure can alter resting neurophysiology and dynamic resting-state measures @ozaki2021qEEG_antipsychotics @zhong2024antipsychotic_fmri.

#table(
  columns: (auto, auto, auto, auto, auto),
  inset: 6pt,
  align: (left, center, center, center, center),
  table.header(
    [*Dataset / group*],
    [*N*],
    [*Age mean*],
    [*Age SD*],
    [*Female n (%)*],
  ),
  [ds003944 Healthy], [32], [21.61], [3.97], [12 (37.5%)],
  [ds003944 FEP], [50], [22.33], [4.94], [16 (32.0%)],
  [ds003947 Healthy], [30], [24.19], [5.13], [14 (46.7%)],
  [ds003947 FEP], [31], [23.38], [4.71], [9 (29.0%)],
)

#v(4pt)
#text(size: 9pt, style: "italic")[
  Demographic summary derived from `articles/CLINICAL/psychosis_first_time_episode/results/demography_summary.csv` together with cohort medication metadata. Within-dataset subgroup age and sex comparisons were not strongly imbalanced in the current metadata (`all age p > 0.30`, `all sex p > 0.36` in the article-local audit), but the paper should still be read as medication-stratified observational analysis rather than as a confound-free medication effect model.
]

== Shared-reference anchor definition

The main between-subject analyses use the cohort-anchored coordinate contract rather than subject-relative coordinates. Operationally, the upstream pipeline stores a subject-balanced external anchor for each exported feature under `/feature_anchors/per_feature`, including a center term $c_j$, a scale term $s_j$, and the associated robust quantiles and support counts. For each upstream feature $phi_(t,j)$, the anchored feature is

$
tilde(phi)_(t,j) = frac(phi_(t,j) - c_j, s_j + epsilon),
$

and the anchored feature vector $tilde(phi)_t$ is then carried into the fixed `3D` and `9D` projections. This is what makes the resulting coordinates interpretable as a common clinical group-comparison space rather than as subject/session-relative geometry. Subject-anchored coordinates remain useful for within-subject geometry, but the present manuscript's primary between-subject contrasts are intentionally carried out in the shared-reference contract.

== NeuralManifoldDynamics 2.1 workflow and core equations

Each resting EEG recording was converted by NeuralManifoldDynamics 2.1 into a sequence of short time windows. For each window $t$, the pipeline computes a feature vector $phi_t in RR^p$ from the EEG and projects it into a 3D Meta-Noetic Phase Space (MNPS) state @langell2025_6 @langell2026_compendium

$
x_t = P(phi_t) = [m_t, d_t, e_t]^T,
$

where $m$ denotes the metastability-family coordinate, $d$ the diffusivity / redistribution-family coordinate, and $e$ the entropy-family coordinate. The higher-resolution 9D state used in the manuscript decomposes the same trajectory into interpretable sub-coordinates @langell2025_stratified:

$
x_t^(9) = [m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m]^T.
$

Across windows ${x_t}_(t=1)^T$, each recording becomes a state-space trajectory. We summarize first-order geometry with subject-level means, medians, dispersion, and short-horizon trajectory descriptors such as speed, curvature, and delta statistics.

Local dynamics are represented by a short-horizon flow field

$
dot(x)(t) = f(x_t, t),
$

with local Jacobian

$
J(x_t, t) = partial f(x_t, t) / partial x_t.
$

Operationally, the manuscript uses local linear fits within NeuralManifoldDynamics 2.1 to estimate these Jacobians @langell2025_mnj @langell2026_mndm:

$
dot(x) approx A (x - bar(x)) + b, quad hat(J) = A.
$

We then report scalar summaries from the 3D Jacobian, the 9D Jacobian, and the corresponding block decompositions. In plain language, the 3D/9D coordinates capture where a subject tends to occupy state space, while the Jacobian-derived metrics capture how that state tends to locally expand, rotate, or redirect over time. Throughout the manuscript, the `m`, `d`, and `e` axes are treated as release-bound operational proxy families rather than as direct measurements of single biological variables.

== Analysis blocks

For each dataset we generated cleaned and contrast outputs for five paper-facing families:

1. global 3D MNPS, with trajectory dynamics exported alongside the same block;
2. stratified 9D MNPS;
3. global 3D MNJ;
4. stratified 9D MNJ; and
5. 9x9 block-MNJ summaries.

We also generated article-local `reachability_cones` summaries and a pooled reachability sensitivity export. Reachability is therefore part of the paper-facing export surface, but it is treated as a supplement-level sensitivity layer rather than as a primary endpoint, because that family was refreshed after the first pooled sensitivity pass and is used here mainly to test whether pooled or stratified psychosis contrasts show coherent reachable-neighborhood shifts.

Contrasts were run for `FEP unmedicated vs Healthy`, `FEP medicated vs Healthy`, and `FEP medicated vs FEP unmedicated`. Positive effect sizes indicate higher values in the first named group because each contrast was parameterized as right-minus-left in the exported analysis tables. BH-FDR was computed within each contrast and analysis family; results with `q <= 0.05` are treated as the strongest inferential layer, while `p < 0.05` and `p < 0.1` are reported as secondary uncorr-sig and trend signals. This is family-local multiplicity control, not manuscript-wide control across the full metric universe.

== Endpoint hierarchy and claim discipline

#table(
  columns: (auto, auto, auto),
  inset: 6pt,
  align: (left, center, left),
  table.header(
    [*Layer*],
    [*Status*],
    [*Reason*],
  ),
  [3D MNPS], [Primary], [highest interpretability and strongest QC pass profile],
  [Trajectory summaries], [Primary / secondary], [directly test whether psychosis separation appears in short-horizon dynamics],
  [9D MNPS], [Secondary], [mechanistic decomposition of the same state-space trajectory],
  [3D / 9D MNJ], [Exploratory-secondary], [useful local-dynamical summaries, but more estimator-sensitive than first-order coordinates],
  [Reachability cones], [Exploratory-sensitivity], [supplement-level shared-reference check on reachable-neighborhood / gate shifts rather than a primary inferential anchor],
  [Block-MNJ], [Exploratory], [reduced QC pass rate and no family-wise-FDR-surviving block effects in the main contrasts],
)

#v(4pt)
#text(size: 9pt, style: "italic")[
  Claim hierarchy used throughout the paper: primary claims concern corrected `3D` / trajectory-level separations and medication-stratification effects; secondary claims concern pooled-FEP robustness and stable `9D` decomposition; reachability, block-MNJ, and phenotype links are treated as sensitivity or exploratory unless stated otherwise. Detailed methods, tables, and reviewer-facing caveats are moved to `S1-S4`.
]

== Sensitivity analysis: pooled FEP

To test whether the main psychosis signal depends too strongly on medication stratification or on the treatment of rare missing CPZ values, we ran a separate sensitivity analysis in which all FEP cases were pooled into a single `FEP` group and contrasted against `Healthy`. This sensitivity analysis used the same cleaned NeuralManifoldDynamics outputs, the same QC/statistical settings as the main manuscript, and a single `Healthy vs FEP` comparison in place of the three-group design. Because `reachability_cones` was added after the first pooled sensitivity pass, pooled reachability was summarized separately from the refreshed article-local `reachability_cones` subject metrics. We treat the pooled analysis as a robustness check and supplement-level view rather than as the main inferential endpoint, because it intentionally collapses clinically meaningful medication-state heterogeneity.

== Reviewer-facing baseline comparators

Because this manuscript is not intended as a full benchmark across all possible EEG representations, we added a compact comparator panel against simpler baselines. From each subject's `features_raw` H5 export we extracted median spectral summaries (`delta`, `theta`, `alpha`, `beta`, `alpha/theta`, `beta/alpha`) and median complexity summaries (Hjorth mobility, Hjorth complexity, permutation entropy, sample entropy). From `subject_metrics` we also extracted simple trajectory baselines (`speed`, `curvature`, `corner_entropy`, `corner_transition_entropy`). These comparator families were tested with the same medication-stratified contrasts using Welch tests and BH-FDR within dataset, contrast, and baseline family. Their role is reviewer-facing calibration rather than a claim that simple features and NMD summaries should be judged by one global winner-take-all benchmark.

== Exploratory clinical phenotypes

To address the clinical-context concern more directly, we ran two additional FEP-only exploratory analyses from the article-local `subject_metrics` tables. The first used `SAPS_Q7` from the Scale for the Assessment of Positive Symptoms (SAPS) @andreasen1984scale to form `Low hallucinations` (`SAPS_Q7 <= 1`) and `High hallucinations` (`SAPS_Q7 >= 3`) groups, excluding the intermediate score of `2`. This yielded `20` vs `18` FEP participants in `ds003944` and `17` vs `10` in `ds003947`. The second used `BPRST19` from the Brief Psychiatric Rating Scale (BPRS) @overall1962brief as a total-symptom-burden measure and split each dataset at its within-cohort FEP median, yielding `25` vs `23` FEP participants in `ds003944` and `16` vs `15` in `ds003947`.

These phenotype analyses were treated as exploratory rather than primary endpoints. We joined phenotype tables to the article-local `subject_metrics` outputs, ran Welch tests for each metric within each analysis family, and applied BH-FDR within analysis family. Full results are reported in `S2` and in `articles/CLINICAL/psychosis_first_time_episode/results/clinical_phenotype_summary.csv`.

#figure(
  image("figures/psychosis_analysis_flow.svg", width: 100%),
  caption: [
    Analysis workflow used in the manuscript. The main three-group contrasts are complemented by a pooled `Healthy vs FEP` sensitivity check, a compact reviewer-facing baseline comparator panel, and exploratory FEP-only phenotype analyses (`SAPS_Q7`, `BPRST19`), all exported into article-local summary files.
  ],
)

= Results

== ds003944

The clearest `ds003944` finding was a medicated FEP displacement along the `m` geometry. In the global 3D block, `FEP medicated vs Healthy` showed q-significant increases in `m_mean` ($d = 0.881$, $p = 0.0035$, $q = 0.0157$), `m_median` ($d = 0.865$, $p = 0.0010$, $q = 0.0090$), and `m_std` ($d = 0.654$, $p = 0.0135$, $q = 0.040$). The same contrast remained readable in the 9D layer, where `m_o_mean` ($d = 0.814$, $p = 0.0020$, $q = 0.027$), `m_e_mean` ($d = 0.747$, $p = 0.0040$, $q = 0.030$), and `m_o_std` ($d = 0.715$, $p = 0.0075$, $q = 0.040$) all survived family-wise FDR within the stratified block.

Medication stratification mattered inside FEP as well. `FEP medicated vs FEP unmedicated` separated strongly on global `m_std` ($d = 0.972$, $p = 0.0020$, $q = 0.0180$), with additional exploratory higher-order support in stratified-MNJ and block-MNJ layers summarized separately below. By contrast, `FEP unmedicated vs Healthy` remained weaker and less stable after correction: the strongest signals were trajectory `m_delta_mean_median` ($d = -0.715$, $p = 0.0120$, $q = 0.240$), stratified `m_e_median` ($d = 0.701$, $p = 0.0220$, $q = 0.297$), and global `e_mean` ($d = 0.695$, $p = 0.0250$, $q = 0.164$), none of which survived BH-FDR.

#table(
  columns: (auto, auto, auto, auto, auto, auto),
  inset: 6pt,
  align: (left, left, center, center, center, left),
  table.header(
    [*Contrast*],
    [*Block / feature*],
    [*Cohen $d$*],
    [*$p$*],
    [*$q$*],
    [*Tier*],
  ),
  [FEP medicated vs Healthy], [3D MNPS `m_mean`], [0.881], [0.0035], [0.0157], [`q<=0.05`],
  [FEP medicated vs Healthy], [9D MNPS `m_o_mean`], [0.814], [0.0020], [0.0270], [`q<=0.05`],
  [FEP medicated vs FEP unmedicated], [3D MNPS `m_std`], [0.972], [0.0020], [0.0180], [`q<=0.05`],
  [FEP medicated vs Healthy], [9D MNPS `m_e_mean`], [0.747], [0.0040], [0.0304], [`q<=0.05`],
  [FEP unmedicated vs Healthy], [Trajectory `m_delta_mean_median`], [-0.715], [0.0120], [0.2399], [`p<0.05`],
)

#v(4pt)
#text(size: 9pt, style: "italic")[
  Interpretation: corrected first-order `m`-family displacement, strongest in medicated FEP. In this cohort, the clearest separation is carried by the medicated subgroup, which may reflect medication exposure, illness severity correlated with treatment, clinical selection, or their interaction rather than a pure medication-free psychosis signature.
]

== ds003947

The second cohort did not simply replicate the `ds003944` pattern at the same layer. Instead, its strongest robust separation appeared in dynamics. `FEP unmedicated vs Healthy` showed a q-significant decrease in trajectory `m_delta_mean_median` ($d = -1.385$, $p = 0.0020$, $q = 0.0400$), which was the single strongest corrected effect in the entire `ds003947` export surface. The same contrast also produced exploratory support in block-MNJ and stratified 9D MNJ, suggesting that the unmedicated subgroup carries a dynamic and second-order perturbation even when its static global mean shift is less stable.

Medicated FEP in `ds003947` was more mixed. The strongest raw 9D MNPS features (`d_l_median`: $d = 0.815$, $p = 0.0050$, $q = 0.074$; `d_l_mean`: $d = 0.792$, $p = 0.0055$, $q = 0.074$) sat just above the FDR threshold, while the stratified-MNJ layer showed a similar uncorr-sig increase in `mdr_mean` for `FEP medicated vs Healthy` ($d = 0.789$, $p = 0.0050$, $q = 0.095$). `FEP medicated vs FEP unmedicated` did not yield a comparably stable family-level separation, although block-MNJ again provided a readable trend (`block_trace_mean`: $d = 0.749$, $p = 0.0885$, $q = 0.532$).

#table(
  columns: (auto, auto, auto, auto, auto, auto),
  inset: 6pt,
  align: (left, left, center, center, center, left),
  table.header(
    [*Contrast*],
    [*Block / feature*],
    [*Cohen $d$*],
    [*$p$*],
    [*$q$*],
    [*Tier*],
  ),
  [FEP unmedicated vs Healthy], [Trajectory `m_delta_mean_median`], [-1.385], [0.0020], [0.0400], [`q<=0.05`],
  [FEP unmedicated vs Healthy], [9D MNJ `mdr_mean`], [0.790], [0.0545], [0.5175], [`p<0.1`],
  [FEP medicated vs Healthy], [9D MNPS `d_l_median`], [0.815], [0.0050], [0.0742], [`p<0.05`],
  [FEP medicated vs Healthy], [9D MNJ `mdr_mean`], [0.789], [0.0050], [0.0950], [`p<0.05`],
  [FEP medicated vs Healthy], [9D MNPS `d_l_mean`], [0.792], [0.0055], [0.0742], [`p<0.05`],
)

#v(4pt)
#text(size: 9pt, style: "italic")[
  Interpretation: corrected trajectory-level dynamic effect in unmedicated FEP; second-order support remains exploratory. Because the unmedicated subgroup is small (`n = 8`), this should be read as a strong cohort-local signal that needs replication rather than as a settled subgroup biomarker.
]

== Cross-dataset synthesis

The two cohorts converge on one high-level point: medication stratification changes the geometry that looks most informative, and the same shared-reference NeuralManifoldDynamics 2.1 workflow keeps those differences readable across subjects. They do not converge on a single universal feature. `ds003944` concentrates its strongest corrected signal in the global and stratified `m` axes for medicated FEP, whereas `ds003947` concentrates its strongest corrected signal in trajectory `m` dynamics for unmedicated FEP. Read conservatively, the replicated result is therefore not one exact feature but one repeated phenomenon: psychosis-related separation remains visible under one common state-space pipeline, yet the layer that carries the separation shifts with cohort composition and medication status.

What replicates, then, is the usefulness of a fixed shared-reference state-space for exposing medication-sensitive heterogeneity. What does *not* replicate is one universal feature-level biomarker or a clear winner over all conventional EEG summaries. This distinction is central to the paper's claim hierarchy and is why the present manuscript should be read as a methods-anchored empirical report rather than as a universal FEP biomarker study.

== Sensitivity analysis: pooled Healthy vs FEP

The pooled sensitivity analysis was informative precisely because it did *not* behave identically across cohorts. In `ds003944`, the main psychosis signal remained visible after pooling: `Healthy vs FEP` preserved BH-FDR-significant global `m_mean` ($d = 0.688$, $p = 0.0050$, $q = 0.022$), global `m_median` ($d = 0.701$, $p = 0.0025$, $q = 0.022$), and stratified `m_e_mean` / `m_e_median` ($d = 0.720$ / $0.705$, $p = 0.0020$ / $0.0035$, $q = 0.047$ for both). This indicates that the core psychosis geometry in `ds003944` is strong enough to survive medication pooling, even though its largest effects still localize more cleanly when medicated and unmedicated FEP are separated.

In `ds003947`, pooling diluted the clearest main-analysis effect. The strongest pooled findings shifted toward 9D MNJ (`mdr_mean`: $d = 0.771$, $p = 0.0045$, $q = 0.071$; `mdr_median`: $d = 0.737$, $p = 0.0075$, $q = 0.071$) and away from a corrected trajectory result, while the pooled trajectory `m_delta_mean_median` effect dropped to an uncorr-sig signal ($d = -0.629$, $p = 0.0125$, $q = 0.250$). That pattern argues that medication pooling is not a harmless simplification in `ds003947`: it partially averages away the abnormal-dynamics signature that becomes most visible in the unmedicated subgroup.

The refreshed pooled reachability pass adds a similar asymmetry. In `ds003944`, `Healthy vs FEP` produced a coherent reachability pattern with `tube_capture_gate_median` ($d = 0.685$, $p = 0.0021$, $q = 0.0606$) and `tube_q_ratio_h4_mean` ($d = -0.728$, $p = 0.0036$, $q = 0.0606$), both just above the family-wise threshold. In `ds003947`, pooled reachability remained weak and correction-limited; the strongest non-reliability pooled metric was only `cone_kappa_mean` ($d = 0.458$, $p = 0.0789$, $q = 0.981$). This pooled reachability contrast therefore reinforces the broader read of the manuscript: `ds003944` carries a wider psychosis-related shift that partly survives pooling, whereas `ds003947` remains more subgroup-specific and heterogeneity-sensitive.

#v(4pt)
#text(size: 9pt, style: "italic")[
  Interpretation: pooling confirms `ds003944` but weakens `ds003947`, supporting medication stratification rather than pooled-FEP analysis as the main inferential view.
]

== Reviewer-facing baseline comparators

A compact comparator panel against simpler EEG summaries showed a mixed but informative pattern. In `ds003944`, the strongest baseline effect was spectral rather than dynamical: `FEP medicated vs Healthy` separated on `beta/alpha` ($d = 0.768$, $p = 0.0036$, $q = 0.021$), while simple speed/curvature baselines remained weak. In `ds003947`, `FEP unmedicated vs Healthy` also showed a corrected spectral baseline effect in `alpha` power ($d = -0.817$, $p = 0.0042$, $q = 0.025$), and `FEP medicated vs Healthy` showed a corrected complexity effect in Hjorth complexity ($d = -0.765$, $p = 0.0062$, $q = 0.025$). However, generic speed/curvature baselines did not reproduce the strongest dynamic main-text result. The baseline panel therefore suggests that some cohort-local separation is visible in simpler EEG summaries, but it does not establish NMD as globally superior to conventional EEG. Its value here is organizational: one shared state-space makes the medication-sensitive geometry readable across first-order, trajectory, and local-dynamical summaries. Full baseline details are reported in `S2`.

== Exploratory block-MNJ structure

Block-MNJ is used here as a hypothesis-generating layer rather than as a primary inferential endpoint. In `ds003944`, `FEP medicated vs FEP unmedicated` showed readable but family-level-subthreshold block support (`block_trace_mean`: $d = 0.691$, $p = 0.0125$, $q = 0.058$). In `ds003947`, `FEP unmedicated vs Healthy` showed a larger raw block effect (`block_trace_mean`: $d = -0.926$, $p = 0.0260$, $q = 0.234$), but again without family-wise support. These patterns are worth retaining for future targeted follow-up, yet they remain exploratory here, especially given the reduced block-MNJ QC pass rate summarized in `S3`. The safest interpretation is altered local recirculation or coupling structure on the exported surface, not a direct claim about one anatomical circuit.

== Exploratory clinical phenotypes

These phenotype analyses are retained as hypothesis-generating only. Briefly, `ds003944` linked higher hallucination burden (`SAPS_Q7`) most clearly to an `e`-weighted displacement, whereas higher total burden (`BPRST19`) showed stronger first-order and block-coupling effects; `ds003947` provided weaker or more selective support. Full phenotype tables now sit in `S2`, and these analyses are not part of the paper's primary inferential claim set.

#figure(
  image("figures/psychosis_selected_effect_heatmap.svg", width: 100%),
  caption: [
    Selected paper-facing effects from the article-local exports. Each cell shows the preferred block summary for one dataset and contrast; colour encodes Cohen's $d$, and the cell label shows the exported metric. `q` marks `q <= 0.05`, `*` marks `p < 0.05`, and `~` marks `p < 0.1`.
  ],
)

#figure(
  image("figures/psychosis_m_axis_focus.svg", width: 100%),
  caption: [
    m-axis focused view of the main results. The figure emphasizes how `ds003944` concentrates separation in static and stratified `m` metrics for medicated FEP, whereas `ds003947` places its strongest corrected effect in trajectory `m_delta_mean_median` for unmedicated FEP.
  ],
)

= Discussion

This compressed study supports three cautious conclusions.

First, a fixed shared-reference NeuralManifoldDynamics 2.1 analysis can expose clinically meaningful heterogeneity that pooled FEP analysis partly hides. In practical terms, it makes three-group psychosis contrasts straightforward to compute and summarize within one common state-space definition across subjects. That is the paper's real replication target: not exact feature identity, but reproducible medication-sensitive separability under one locked analysis surface.

Second, medication stratification is not a cosmetic refinement. In `ds003944`, the medicated subgroup carries the strongest and cleanest `m`-axis displacement, although the pooled sensitivity test shows that a broader psychosis signal still survives in global and stratified `m` features, especially `m_e`. In `ds003947`, the unmedicated subgroup instead carries the only q-significant dynamic effect, and the pooled sensitivity test weakens that result, which argues directly against collapsing medication states too early. This medication-linked redistribution is at least qualitatively compatible with prior EEG and neurocognitive reports that antipsychotic exposure can stabilize some dimensions of pathological activity while introducing a different kind of rigidity @centorrino2002eeg @keefe2007neurocognitive. At the same time, the `ds003944` medicated-FEP separation should not be read as "the psychosis signal": it may reflect medication exposure, illness severity correlated with treatment, clinical selection, or a medication-by-illness interaction.

Third, the `m` axis remains important, but not always in the same form. In one cohort it appears as a stable global displacement (`m_mean`, `m_median`, `m_std`), while in the other it appears most clearly as an altered trajectory drift term (`m_delta_mean_median`). That pattern is consistent with a geometry-first view in which the same NDT-aligned state-space exposes a common family of psychosis-sensitive coordinates, but the exact feature expression remains cohort-dependent. The safest oscillatory interpretation is therefore not that `m` measures one single rhythm, but that it reflects altered rhythm-weighted coordination whose expression can shift between static occupancy and dynamic instability, broadly in line with early-psychosis gamma and ASSR abnormalities reported in MEG and electrophysiology meta-analyses @grent2018gamma @zouaoui2023assr. The reviewer-facing comparator panel reinforces the bounded version of that claim: simple spectral and complexity baselines capture part of the subgroup separation, so the present work should be read as an organizing analysis surface rather than as a definitive superiority benchmark.

The present EEG findings also fit naturally within a broader multimodal dysconnectivity literature. Resting-state fMRI studies in first-episode and early psychosis have reported altered default-mode, salience-network, and wider cortical-subcortical-cerebellar connectivity patterns, suggesting that the cohort-level EEG geometry reported here may be one modality-specific expression of a broader network disturbance @alonsosolis2012default @jensen2024neuromark @huang2022salience. At the same time, scalp EEG does not have the spatial resolution to claim direct network-specific mechanism from these coordinates alone; the most defensible wording is that the exported geometry is compatible with broader dysconnectivity models, not that it localizes them.

The main limitations are equally clear. `ds003947` has only eight unmedicated participants, so second-order and block-level effects there should be treated as supportive rather than definitive. We also did not benchmark alternative preprocessing or manifold-construction schemes exhaustively, so the current results should be read as evidence for one reproducible NeuralManifoldDynamics 2.1 workflow rather than as a universal proof that any single implementation choice is optimal. Relatedly, the reported q-values control within contrast-family blocks rather than across the full manuscript-wide metric universe. Block-MNJ remains exploratory in both cohorts: it adds readable structure, but the strongest block-level findings do not survive family-wise FDR here and should not be overread as specific circuit claims. The pooled sensitivity analysis helps on one reviewer-facing point, however: because only two FEP participants across both cohorts had missing CPZ values, the difference between pooled and stratified results is unlikely to be driven by missingness alone. The phenotype analyses add clinical texture but do not fully remove confounding by medication state, especially for the hallucination split, so they are best read as hypothesis-generating extensions rather than as replacement primary endpoints. More generally, early-psychosis electrophysiology is heterogeneous even for comparatively established markers such as mismatch negativity, where chronic schizophrenia findings are stronger and first-episode effects remain more debated @tada2019mmn @haigh2017mmn_fes. The present results should therefore be read as cohort- and medication-sensitive geometry rather than as a universal FEP biomarker.

= Supplement overview

Extended material has been moved out of the main manuscript to keep the claim hierarchy explicit:

1. `S1` gives the expanded methods, including the shared-reference anchor definition and endpoint contract.
2. `S2` collects the detailed data tables for pooled sensitivity, reachability, baseline comparators, and phenotype splits.
3. `S3` collects QC and robustness notes, including the reduced block-MNJ pass profile.
4. `S4` gives a cautious clinician-facing interpretation that avoids biomarker overreach.

#bibliography("psychosis.bib", style: "apa")
