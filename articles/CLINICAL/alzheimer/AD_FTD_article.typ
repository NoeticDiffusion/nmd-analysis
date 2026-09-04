#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Resting-State Neural Geometry in Alzheimer Disease and Frontotemporal Dementia",
  short-title: "AD and FTD Neural Geometry",
  subtitle: "A compact NeuralManifoldDynamics 2.1 report for ds004504",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "Alzheimer disease",
    "frontotemporal dementia",
    "EEG",
    "NeuralManifoldDynamics",
    "MNJ",
    "MMSE",
  ),
  article-type: "Research Article / Compact Empirical Report",
  abstract: [
    We analyzed the resting-state EEG dataset `ds004504` with a fixed NeuralManifoldDynamics 2.1 workflow to compare `Healthy`, `AD`, and `FTD` groups in a shared state-space and local-dynamics frame. The currently available paper-facing export for this dataset emphasized `tier2_emmi`, global `3D` MNJ, global `9D` MNJ, and `9 x 9` block-MNJ summaries rather than the broader first-order and reachability surface. In direct group contrasts, the clearest Healthy-versus-dementia effects localized to block-MNJ rather than to scalar global Jacobian summaries: selected `d -> d` block magnitude differed for both `AD vs Healthy` ($d = -0.526$, $p = 0.040$) and `FTD vs Healthy` ($d = -0.623$, $p = 0.031$), while `AD vs FTD` remained weak on the selected surface. Continuous MMSE analyses were modest in pooled dementia and weak in `AD` alone, but much stronger in `FTD`: `FTD_only` showed a strong `9D` MNJ association for `spectral_radius_median` ($rho = 0.754$, $q = 0.00046$) and a parallel block-MNJ `e -> e` association for `block_frobenius_mean` ($rho = 0.630$, $q = 0.0116$). Cohort-specific MMSE bins sharpened that pattern further. In `FTD_only`, the median split produced `9D` MNJ `spectral_radius_median` ($d = 1.236$, $q = 0.0229$) and block-MNJ `e -> e` magnitude ($d = 1.486$, $q = 0.0503$), while `AD_only` showed only trend-level bin effects. The bounded conclusion is that, in this dataset and export surface, dementia-related separation appears more clearly in higher-dimensional local dynamics than in coarse global summaries, and the strongest severity-linked signal is presently concentrated in the FTD subgroup rather than shared uniformly across both dementias.
  ],
  data-availability: [
    The manuscript-facing bundle is stored under `articles/CLINICAL/alzheimer/results/` and `articles/CLINICAL/alzheimer/figures/`. Key paper-facing tables and summaries include `demography_summary.csv`, `selected_metrics_summary.csv`, `mmse_correlations_summary.csv`, `cohort_mmse_bin_summary.csv`, and the corresponding manifest files. The underlying ds004504 H5 exports and larger derived analysis tables can be distributed separately from this manuscript-facing bundle.
  ],
  competing-interests: [
    No competing interests are declared in this draft.
  ],
)

= Introduction

Alzheimer disease (AD) and frontotemporal dementia (FTD) are both neurodegenerative syndromes, but they need not deform neural dynamics in the same way. A useful state-space analysis should therefore do more than ask whether dementia differs from health in one scalar direction. It should also ask where the signal concentrates: in coarse subject summaries, in higher-dimensional decomposition, or in local dynamical coupling.

This compact report applies a fixed NeuralManifoldDynamics 2.1 workflow to the resting-state EEG dataset `ds004504`, which contains `Healthy`, `AD`, and `FTD` groups together with Mini Mental State Examination (MMSE) scores. The aim is intentionally narrow. We ask two bounded questions:

1. Where does the clearest Healthy-versus-dementia separation appear on the currently available export surface?
2. Does within-diagnosis MMSE severity align more with `AD`, with `FTD`, or with neither?

This is not presented as a general dementia biomarker paper. It is a paper-facing analysis of one auditable export surface for one cohort.

= Methods

== Cohort

The manuscript uses the local `ds004504` export and participant metadata under `articles/alzheimer/metadata/ds004504_alzheimer_FTD_eeg/participants.tsv`. The cohort contains `88` participants: `29 Healthy`, `36 AD`, and `23 FTD`.

#figure(
  kind: table,
  table(
    columns: (2.1fr, 0.9fr, 1.2fr, 1.2fr, 1.3fr, 1.2fr),
    align: (left, center, center, center, center, center),
    inset: 5pt,
    table.header(
      [*Group*],
      [*N*],
      [*Age mean*],
      [*Age SD*],
      [*Female n (%)*],
      [*MMSE mean*],
    ),
    [Healthy], [29], [67.90], [5.40], [11 (37.9%)], [30.00],
    [AD], [36], [66.39], [7.89], [24 (66.7%)], [17.75],
    [FTD], [23], [63.65], [8.22], [9 (39.1%)], [22.17],
  ),
  caption: [Table 1: Cohort summary derived from `articles/alzheimer/results/demography_summary.csv`.]
) <tab-cohort>

The group means already show that this cohort is clinically heterogeneous in a useful way: `Healthy` sits at the MMSE ceiling, `AD` is lower on average, and `FTD` lies in between. The inferential question is whether those clinical differences appear more clearly in coarse dynamics or in higher-dimensional local geometry.

== Analysis surface

Each recording was processed through NeuralManifoldDynamics 2.1, which maps short EEG windows into a low-dimensional neural state and local Jacobian summaries. At the conceptual level, the workflow treats each window as a point

$
x_t = [m_t, d_t, e_t]^T
$

in a shared state-space together with a local flow field

$
dot(x)(t) = f(x_t, t), quad J(x_t, t) = partial f(x_t, t) / partial x_t.
$

The current `ds004504` paper-facing export did not expose the full first-order and reachability family in stable article form. The present manuscript is therefore restricted to four summary layers that were available and verified in the current export:

1. `tier2_emmi`
2. global `3D` MNJ
3. global `9D` MNJ
4. `9 x 9` block-MNJ

This limitation matters. The paper can speak directly about these layers, but it cannot claim that broader MNPS or reachability hypotheses were already fully tested in this cohort.

== Statistical summary and claim discipline

Between-group contrasts used the three predefined comparisons:

1. `AD vs Healthy`
2. `FTD vs Healthy`
3. `AD vs FTD`

For each block, we report the selected paper-facing metric from `articles/alzheimer/results/selected_metrics_summary.csv`, together with Cohen's `d`, p-values, and BH-FDR `q` values from the current export.

MMSE was examined in two exploratory ways:

1. continuous within-cohort correlations
2. cohort-specific MMSE bins for `Dementia_all`, `AD_only`, and `FTD_only`

These MMSE analyses should be read as exploratory severity maps rather than as externally frozen confirmatory endpoints. The strongest findings are emphasized only when they remain coherent across more than one summary layer.

= Results

== Healthy-versus-dementia contrasts

The clearest direct Healthy-versus-dementia effects did not appear in the selected scalar `3D` or `9D` global MNJ summaries. Instead, they localized to block-MNJ magnitude. In the selected export, both `AD vs Healthy` and `FTD vs Healthy` showed reduced `d -> d` block magnitude relative to health:

1. `AD vs Healthy`: `block_frobenius_mean`, `d -> d`, $d = -0.526$, $p = 0.040$, $q = 0.364$
2. `FTD vs Healthy`: `block_frobenius_mean`, `d -> d`, $d = -0.623$, $p = 0.031$, $q = 0.279$

`FTD vs Healthy` also showed a selected `tier2_emmi` speed effect (`speed_median`, $d = 0.590$, $p = 0.046$, $q = 0.138$), whereas `AD vs Healthy` did not show a comparably strong selected EMMI effect. The direct `AD vs FTD` comparison remained weak on the selected export surface. Taken together, the current data support a cautious reading: Healthy-versus-dementia separation is present, but in this export it is more visible in local higher-order coupling than in the coarsest selected global Jacobian summaries.

#figure(
  image("figures/ad_ftd_selected_effect_heatmap.png", width: 100%),
  caption: [Figure 1: Selected `AD`, `FTD`, and `Healthy` contrast effects across the available export layers. The strongest Healthy-versus-dementia signal in the current selected surface localizes to block-MNJ rather than to the selected scalar global MNJ summaries.]
) <fig-selected>

== Continuous MMSE structure

Continuous MMSE structure was not uniform across the cohort. In pooled dementia, the signal was modest: the strongest selected association was block-MNJ `e -> e` magnitude (`block_frobenius_mean`, $rho = 0.308$, $p = 0.0178$, $q = 0.240$), which is suggestive but not corrected-significant in that pooled frame.

`AD_only` was weaker. None of the selected continuous MMSE associations survived correction, and even the strongest selected AD-specific block-MNJ signal remained modest (`e -> e`, $rho = 0.272$, $p = 0.109$, $q = 0.559$).

`FTD_only` looked different. Here the strongest selected continuous MMSE signal appeared in `9D` MNJ and was accompanied by a parallel block-MNJ finding:

1. `9D` MNJ `spectral_radius_median`: $rho = 0.754$, $p = 3.29 times 10^(-5)$, $q = 0.00046$
2. block-MNJ `e -> e` `block_frobenius_mean`: $rho = 0.630$, $p = 0.00128$, $q = 0.0116$

This is the cleanest severity-linked pattern in the present report. On the current export surface, MMSE severity appears to track higher-dimensional local dynamics much more strongly in `FTD_only` than in `AD_only`.

#figure(
  image("figures/ad_ftd_mmse_correlation_panel.png", width: 100%),
  caption: [Figure 2: Selected continuous MMSE associations by cohort. The dominant continuous severity structure in the current dataset is concentrated in the FTD subgroup, especially in `9D` MNJ and block-MNJ.]
) <fig-mmse-corr>

== Cohort-specific MMSE bins

The cohort-specific MMSE-bin analyses reinforced the same asymmetry. The pooled `Dementia_all` bins were mostly trend-level. `AD_only` produced some moderate effect sizes, especially in block-MNJ `e -> e`, but none of the selected AD-only bin contrasts remained corrected-significant.

By contrast, `FTD_only` sharpened markedly under the same binning logic. The most notable selected effects were:

1. median split (`MMSE <= 22` vs `> 22`):
   - `9D` MNJ `spectral_radius_median`: $d = 1.236$, $p = 0.00820$, $q = 0.0229$
   - block-MNJ `e -> e` `block_frobenius_mean`: $d = 1.486$, $p = 0.00950$, $q = 0.0503$
2. lower-versus-upper FTD tertiles:
   - `9D` MNJ `spectral_radius_median`: $d = 2.714$, $p = 0.00797$, $q = 0.0558$
3. middle-versus-upper FTD tertiles:
   - block-MNJ `e -> m` `block_frobenius_mean`: $d = 1.662$, $p = 0.0220$

These subgroup bins are small, especially in the upper FTD tertile (`n = 4`), so the very large effect sizes should be treated as strong cohort-local signals rather than as settled severity biomarkers. Still, the direction is internally coherent: the FTD subgroup repeatedly concentrates MMSE-linked signal in higher-dimensional and block-resolved local dynamics.

#figure(
  image("figures/ad_ftd_mmse_bin_heatmap.png", width: 100%),
  caption: [Figure 3: Cohort-specific MMSE-bin effects across `Dementia_all`, `AD_only`, and `FTD_only`. The strongest severity-linked bin effects again localize to FTD-specific `9D` and block-MNJ summaries.]
) <fig-mmse-bins>

= Discussion

The present dataset does not support a broad claim that one single scalar neural summary separates all dementias from health or tracks severity equally across diagnoses. A tighter reading fits the data better.

First, Healthy-versus-dementia separation is visible, but on the currently exported surface it appears more clearly in block-resolved Jacobian structure than in the selected scalar global MNJ metrics. Second, the within-cohort severity signal is not shared evenly by `AD` and `FTD`. The strongest continuous and binned MMSE structure is concentrated in `FTD_only`, where both `9D` MNJ and block-MNJ repeatedly carry the signal. Third, the `AD` subgroup is not null, but in this compact analysis its severity structure is weaker and mostly trend-level.

That pattern can be read in a restrained way. The current export suggests that dementia-related organization in this cohort may be better captured as higher-dimensional local dynamical reconfiguration than as a simple global contraction index. It does not yet justify a claim that FTD is "more geometric" than AD in any general sense. It only shows that, in this dataset and export surface, FTD contributed the clearest MMSE-linked dynamic organization.

= Limitations

This manuscript has several important limits.

1. It is a single-dataset report with modest subgroup sizes, especially once MMSE tertiles are formed.
2. The article is constrained by the currently exported paper-facing surface. The present draft cannot test broader first-order MNPS or reachability hypotheses because those layers were not the stable article-facing outputs in this pass.
3. Many direct group contrasts were only uncorrected-significant or trend-level after BH-FDR.
4. MMSE is clinically useful but coarse, and these analyses are cross-sectional rather than longitudinal.
5. The strongest FTD bin effects come from small cells and therefore demand replication before being treated as robust subtype markers.

= Conclusion

The current `ds004504` analysis supports a bounded conclusion: resting-state dementia-related separation is detectable in a fixed NeuralManifoldDynamics 2.1 frame, but in this export it localizes more clearly to higher-dimensional and block-level local dynamics than to the selected scalar global Jacobian summaries. Within that surface, the strongest severity-linked organization is concentrated in `FTD_only`, while `AD_only` remains weaker and mostly trend-level. The most defensible next step is therefore not to enlarge the claim, but to test whether this FTD-heavy severity pattern replicates once a broader first-order and reachability export is brought into the article-facing workflow.

= Acknowledgements

This work emerged through structured correspondence among human and AI collaborators; large language models from OpenAI, Anthropic, and Google assisted in literature synthesis, drafting, peer review, and editorial refinement. We also gratefully acknowledge the original investigators, clinical teams, participants, and data stewards who created, curated, and shared the public datasets and metadata that made these analyses possible.

= Contact

Robin Langell - hello(at)noeticdiffusion.com

= Licensing

This manuscript provides only a brief licensing summary; full terms and conditions are available via the Mychainos multi-layer licensing framework (`https://noeticdiffusion.com/license.html`). In short, the conceptual content is released under CC BY-SA 4.0, software under GPLv3, and relevant hardware/biological artifacts under open hardware/biological licences (for example, CERN OHL v2 and OpenMTA). Unified ethical guardrails apply: no coercive, military, or surveillance applications; no patenting or black-boxing of core methods; and derived works should remain accessible, attributed, and shared with care.

= Data and Code Availability

Reference implementations and analysis pipelines:
`https://github.com/NoeticDiffusion`

Datasets and related public bundles:
`https://github.com/NoeticDiffusion/NeuralManifoldDynamics-dataset`

= Trademark Notice

Certain terms used in this manuscript (including Noetic Diffusion, Noetic Diffusion Theory, Noetic Diffusion Mapping, Noetic Diffusion Health Index, and Noetic Atlas) are used as project names and are the subject of ongoing trademark applications. A concise description of the stewardship rationale, current registration status, and how this interacts with open scientific use is available at `https://noeticdiffusion.com/license.html`. These trademark aspects do not affect the scientific content, reproducibility, or licensing of the methods described here.
