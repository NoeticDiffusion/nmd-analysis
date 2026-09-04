#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Resting-State Neural Geometry Across Depressive Symptom Burden",
  short-title: "Depressive Symptom Geometry",
  subtitle: "A compact NeuralManifoldDynamics 2.1 report for ds003478",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "depression",
    "BDI",
    "EEG",
    "NeuralManifoldDynamics",
    "reachability cones",
    "MNJ",
  ),
  article-type: "Research Article / Compact Empirical Report",
  abstract: [
    We analyzed the resting-state openneuro EEG dataset ds003478 with a fixed NeuralManifoldDynamics 2.1 workflow, using Beck Depression Inventory (BDI) score as the primary clinical axis. The article-facing export included global 3D and 9D MNPS summaries, global 3D and 9D MNJ summaries, 9 x 9 block-MNJ, reachability cones, tier2_emmi, and distribution summaries. In the predefined low-versus-high symptom contrast (BDI 0-13 vs BDI 20-63), the strongest selected effects did not appear in 3D summaries. They concentrated in reachability (tube_log_eig_var_mean, d = -0.678, q = 0.00296; closely related tube_log_det_mean, d = 0.735, q = 0.00296), 9D MNJ (rotational_power_mean, d = 0.569, q = 0.00317), and a distribution summary (e_m_mad_sigma, d = 0.688, q = 0.0132). Continuous BDI analyses showed the same ordering across all valid participants: reachability (rho = -0.343, q = 0.00350), 9D MNJ (rho = 0.310, q = 0.00364), and distribution summary (rho = 0.358, q = 0.00226) outperformed 3D summaries. Clinical BDI bands sharpened the same pattern. BDI 0-13 vs 14-19 showed especially strong reachability (d = -0.831, q = 7.46e-6) and distribution (d = 1.727, q = 5.01e-4) effects, while BDI 14-19 vs 20-63 was comparatively weak. The bounded conclusion is that, in this dataset and export surface, depressive symptom burden is more visible in higher-dimensional local dynamics and reachability geometry than in coarse 3D summaries, and the dominant organization is a low-to-elevated symptom regime separation rather than a clean monotonic gradient within the high-BDI range.
  ],
  data-availability: [
    The manuscript-facing bundle is stored under `articles/CLINICAL/depression/results/` and `articles/CLINICAL/depression/figures/`. Key paper-facing tables and summaries include `demography_summary.csv`, `selected_metrics_summary.csv`, `bdi_correlations_summary.csv`, `clinical_bdi_bin_summary.csv`, `centroid_baseline_summary.csv`, `centroid_adjusted_dynamic_summary.csv`, and the corresponding manifest files. The participant metadata table used for cohort summaries is stored under `articles/CLINICAL/depression/metadata/participants.tsv`. The underlying ds003478 H5 exports and larger derived analysis tables can be distributed separately from this manuscript-facing bundle.
  ],
  competing-interests: [
    No competing interests are declared in this draft.
  ],
)

= Introduction

Depressive symptom burden need not manifest as a single scalar reduction in resting-state neural dynamics. If symptom load changes how local trajectories spread, rotate, or retain access to nearby state-space, the clearest signal may appear in higher-dimensional local summaries rather than in the coarsest global descriptors.

This compact report applies a fixed NeuralManifoldDynamics 2.1 workflow to the resting-state EEG dataset `ds003478` (`OpenNeuro DOI: 10.18112/openneuro.ds003478.v1.1.0`), using Beck Depression Inventory (BDI) score as the primary clinical axis. The aim is intentionally narrow. We ask three bounded questions:

1. Where does the clearest low-versus-high BDI separation appear on the current export surface?
2. Do continuous BDI associations reproduce the same ordering of signal across blocks?
3. Do clinically interpretable BDI bands (`0-13`, `14-19`, `20-63`) suggest a smooth severity gradient or a stronger regime contrast?

This is not presented as a diagnostic major depression biomarker paper. It is a paper-facing analysis of one auditable export surface in a young resting-state cohort with uneven clinical annotation beyond BDI.

= Methods

== Cohort

The manuscript uses participant metadata under `articles/CLINICAL/depression/metadata/participants.tsv` together with refreshed article-local NeuralManifoldDynamics outputs. The table below summarizes the `121` participants with usable BDI values. These bands reflect symptom-score strata rather than confirmed diagnostic groups.

#figure(
  kind: table,
  table(
    columns: (1.8fr, 0.8fr, 1.1fr, 1.1fr, 1.3fr, 1.1fr, 1.1fr),
    align: (left, center, center, center, center, center, center),
    inset: 5pt,
    table.header(
      [*BDI band*],
      [*N*],
      [*Age mean*],
      [*Age SD*],
      [*Female n (%)*],
      [*BDI mean*],
      [*BDI median*],
    ),
    [BDI 0-13], [76], [18.97], [1.21], [41 (53.9%)], [1.88], [1.0],
    [BDI 14-19], [15], [18.73], [1.58], [12 (80.0%)], [17.07], [18.0],
    [BDI 20-63], [30], [18.73], [0.91], [21 (70.0%)], [25.10], [25.0],
  ),
  caption: [Table 1: Cohort summary derived from `articles/CLINICAL/depression/results/demography_summary.csv`.]
) <tab-cohort>

Two features of the cohort matter for interpretation. First, the sample is young and age-compressed, so the report is about symptom-linked geometry in this specific population rather than across the broader clinical lifespan. Second, the BDI distribution is imbalanced toward the low-BDI range, with a relatively small middle band (`n = 15`). That asymmetry makes very large band effects noteworthy but still in need of cautious reading.

== Analysis surface

Each recording was processed through NeuralManifoldDynamics 2.1, which maps short EEG windows into a shared state-space together with local dynamical summaries. At the conceptual level, each window is treated as a point

$
x_t = [m_t, d_t, e_t]^T
$

with a local flow field and Jacobian

$
dot(x)(t) = f(x_t, t), quad J(x_t, t) = partial f(x_t, t) / partial x_t.
$

Unlike the more restricted Alzheimer-facing export, the current `ds003478` paper-facing surface spans first-order `3D` / `9D` MNPS, `3D` / `9D` Jacobian summaries, block-MNJ, reachability, and a smaller set of secondary trajectory and distribution summaries. This matters because it allows the present report to ask not only whether low and high BDI differ, but also whether the dominant signal lives in first-order amplitude structure, higher-dimensional local Jacobian structure, or reachability-related local capacity geometry.

== Statistical summary and claim discipline

The primary direct contrast is the predefined low-versus-high BDI comparison:

1. `BDI 0-13 vs BDI 20-63`

For each block, the manuscript reports the selected paper-facing metric from `articles/CLINICAL/depression/results/selected_metrics_summary.csv`, together with the exported effect size, p-value, and BH-FDR `q` value.

BDI was also examined in two exploratory ways:

1. continuous correlations across `All_valid`, `LowHigh_only`, and `High_BDI_only`
2. clinical BDI-bin contrasts for `BDI 0-13`, `BDI 14-19`, and `BDI 20-63`

These BDI analyses should be read as exploratory severity maps, not as frozen confirmatory endpoints. The clinical BDI-band pass is recomputed directly from article-local `subject_metrics`, so its nominal `p` / `q` values need not exactly match the primary selected low-versus-high export even when the split overlaps. Claims are emphasized only when they remain coherent across more than one block family.

= Results

== Low-versus-high BDI contrast

At the cohort-anchored coordinate level, the low-versus-high BDI separation is modest in `3D` rather than dramatic. The strongest `3D` shift still lies on the `e` axis: `e_median` differs by `+0.220` (`d = 0.386`, `q = 0.386`) and `e_mean` by `+0.180` (`d = 0.297`, `q = 0.386`). The `m` axis also shifts somewhat (`m_mean`, `+0.220`, `d = 0.259`, `q = 0.386`), whereas the `d` axis is nearly unchanged (`d_mean`, `+0.018`, `d = 0.032`; `d_median`, `+0.027`, `d = 0.039`). On this direct reading, low and high BDI are not strongly separated as `3D` centroids.

In `9D`, the coordinate shift is clearer, but not every visible feature remains family-corrected. The cleanest corrected low-versus-high centroid signal is `e_m_mean`, which differs by `+0.427` (`d = 0.688`, `q = 0.0239`). Parallel support remains visible in `e_m_median` (`+0.396`, `d = 0.589`, `q = 0.0546`), `m_o_mean` (`+0.514`, `d = 0.523`, `q = 0.0637`), and `m_o_median` (`+0.536`, `d = 0.537`, `q = 0.0637`), but those sit just above the family-wise threshold. This matters for interpretation. It suggests that the basic between-band displacement is weak in coarse `3D`, but more visible once the cohort-anchored stratified coordinate system is resolved in `9D`.

The clearest low-versus-high BDI effects do not appear in the selected `3D` summaries. The selected `3D` MNPS effect is negligible (`d_median`, `d = 0.042`, `q = 0.863`), and the selected `3D` MNJ effect is essentially null (`spectral_radius_median`, `d = 0.024`, `q = 1.0`).

By contrast, the strongest selected effects concentrate in higher-dimensional and reachability-linked summaries:

1. reachability `tube_log_eig_var_mean`: `d = -0.678`, `p = 0.000500`, `q = 0.00296`
2. `9D` MNJ `rotational_power_mean`: `d = 0.569`, `p = 0.000500`, `q = 0.00317`
3. distribution `e_m_mad_sigma`: `d = 0.688`, `p = 0.000500`, `q = 0.0132`

Within the same reachability family, `tube_log_det_mean` is also strong (`d = 0.735`, `p = 0.000500`, `q = 0.00296`), with a higher mean value in the high-BDI group (`-7.34` vs `-9.11`). That matters because it shows that the reachability result is not confined to one selected variance-like summary; a second tube-volume-like readout points in the same low-versus-high direction and suggests a different local reachable neighborhood rather than merely a coarse `3D` displacement. The selected `tier2_emmi` effect is smaller but still visible (`mv_median`, `d = -0.370`, `p = 0.0170`, `q = 0.0510`). The selected block-MNJ effect does not survive correction (`block_anisotropy_mean`, `m -> m`, `d = -0.203`, `q = 0.555`). A restrained reading fits these data better than a broad one: the present low-versus-high BDI separation is real on the current export surface, but it is carried mainly by reachability and `9D` local dynamics rather than by coarse `3D` summaries.

#figure(
  image("figures/depression_selected_effect_heatmap.png", width: 100%),
  caption: [Figure 1: Selected low-versus-high BDI effects across the current export surface. The strongest separation localizes to reachability and `9D` MNJ rather than to the selected `3D` summaries.]
) <fig-selected>

== Continuous BDI structure

Continuous BDI analyses reproduce the same ordering. Across all valid participants, the strongest selected associations are:

1. distribution `e_m_mad_sigma`: `rho = 0.358`, `p = 5.66e-5`, `q = 0.00226`
2. reachability `tube_log_eig_var_mean`: `rho = -0.343`, `p = 1.16e-4`, `q = 0.00350`
3. `9D` MNJ `rotational_power_mean`: `rho = 0.310`, `p = 5.46e-4`, `q = 0.00364`

Again, the selected `3D` layers are weak (`3D` MNPS `rho = -0.074`, `q = 0.551`; `3D` MNJ `rho = -0.087`, `q = 0.887`). The `LowHigh_only` cohort preserves the same direction with weaker magnitudes, especially for reachability (`rho = -0.287`, `q = 0.0288`) and `9D` MNJ (`rho = 0.280`, `q = 0.0246`).

The `High_BDI_only` subset looks different. None of the selected continuous associations survive correction there, although reachability remains suggestive (`rho = 0.349`, `p = 0.0590`, `q = 0.208`). This weakens any claim of a clean monotonic within-high-range severity gradient. The more defensible reading is that the strongest continuous organization separates low from elevated symptom regimes, with less stable ordering inside the high-BDI segment itself.

#figure(
  image("figures/depression_bdi_correlation_panel.png", width: 100%),
  caption: [Figure 2: Selected continuous BDI associations by cohort. Across both `All_valid` and `LowHigh_only`, the dominant structure is carried by reachability, `9D` MNJ, and distribution summaries.]
) <fig-bdi-corr>

== Clinical BDI bands

The clinical BDI-band analyses sharpen the same picture. `BDI 0-13` versus `14-19` already shows strong separation in reachability and distribution structure:

1. reachability `tube_log_eig_var_mean`: `d = -0.831`, `p = 6.79e-7`, `q = 7.46e-6`
2. distribution `e_m_mad_sigma`: `d = 1.727`, `p = 3.76e-5`, `q = 5.01e-4`

When the same low-versus-high split is rerun inside the exploratory clinical-bin analysis, it reinforces that ordering:

1. `9D` MNJ `rotational_power_mean`: `d = 0.569`, `p = 1.39e-4`, `q = 9.30e-4`
2. reachability `tube_log_eig_var_mean`: `d = -0.678`, `p = 2.48e-6`, `q = 2.67e-5`
3. distribution `e_m_mad_sigma`: `d = 0.688`, `p = 0.00120`, `q = 0.00957`

By comparison, `BDI 14-19` versus `20-63` is much weaker on the selected surface. Even where uncorrected signals appear, they do not organize into the same clean cross-block pattern. That asymmetry argues against a simple high-BDI dose response and in favor of a threshold-like or regime-like transition between low and elevated symptom strata.

#figure(
  image("figures/depression_bdi_bin_heatmap.png", width: 100%),
  caption: [Figure 3: Clinical BDI-band effects across the current export surface. The dominant separation is between low BDI and elevated BDI bands, while middle-versus-high contrasts remain comparatively weak.]
) <fig-bdi-bins>

= Discussion

This dataset does not support the claim that depressive symptom burden is best summarized by one coarse global neural scalar. A tighter reading fits the data better.

First, the strongest signal in the current export surface lies in reachability and `9D` local dynamics, not in the selected `3D` MNPS or `3D` MNJ summaries. Second, continuous BDI associations and banded contrasts point in the same direction, which increases confidence that the signal is not an artifact of one single thresholding choice. Third, the structure looks more like a low-to-elevated symptom regime separation than a smooth monotonic progression within the already elevated range.

That interpretation should still remain bounded. The current report does not prove that depression is fundamentally a reachability disorder or a `9D` Jacobian disorder. It shows only that, in this dataset and export surface, those layers carry the clearest BDI-linked organization, while the coarser `3D` summaries do not.

= Limitations

This manuscript has several important limits.

1. It is a single-dataset report in a young, age-compressed resting-state cohort.
2. The band sizes are imbalanced, especially for `BDI 14-19` (`n = 15`), which can inflate uncertainty and effect-size volatility.
3. The article is anchored primarily to BDI, not to a uniformly adjudicated diagnostic major depression label. Only part of the high-BDI subgroup has SCID and HamD annotation.
4. The strongest bin effects are internally coherent, but they remain cohort-local findings rather than settled clinical thresholds.
5. Several selected effects outside reachability, `9D` MNJ, and distribution summaries are weak or non-significant after correction.

= Conclusion

The current `ds003478` analysis supports a bounded conclusion: resting-state depressive symptom burden is detectable in a fixed NeuralManifoldDynamics 2.1 frame, but in this export it localizes more clearly to reachability geometry, `9D` local Jacobian dynamics, and related distribution summaries than to the selected `3D` summaries. The strongest organization is a separation between low and elevated BDI regimes, while within-high-BDI gradients remain less stable. The most defensible next step is therefore not to enlarge the claim, but to test whether this reachability-plus-`9D` pattern replicates in an independent depression cohort or under broader article-facing exports.

= Appendix: Axis And Layer Interpretation

This appendix gives a compact interpretation guide to the main axes and reporting layers used in the manuscript. The aim is not to turn the paper into a stand-alone theory paper, but to make the reported summaries easier to read in clinically recognizable terms.

== The coarse 3D state

The primary chart used throughout the manuscript is

$
x_t = [m_t, d_t, e_t]^T.
$

These three coordinates should be read as operational summary families rather than as direct measurements of one biological variable each.

*`m`: mobility / metastability family.* In plain terms, `m` tracks how readily the signal appears to move through organized state-space structure. In this depression report, `m` contributes some first-order displacement, but it is not the dominant `3D` separator.

*`d`: deviation / redistribution family.* `d` indexes how far the system sits from its more typical balance of integration and segregation under the fixed measurement contract. In the present cohort, `d` is the weakest of the three coarse low-versus-high BDI axes.

*`e`: entropy / irregularity family.* `e` summarizes complexity pressure, irregularity, and less compressible organization in the exported state representation. In this manuscript, the most visible `3D` centroid shift is `e`-weighted rather than `d`-weighted.

#netn-box(title: [Axis guardrail])[
  The `m`, `d`, and `e` axes are release-bound measurement families. They are not direct stand-ins for single symptom clusters, neurotransmitters, or one bedside depression score.
]

== The stratified 9D layer

The higher-resolution chart is

$
x_t^(9) = [m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m]^T.
$

This layer decomposes the same trajectory into subfamilies. The practical reason for reporting it is that a weak coarse `3D` effect can still hide a more specific higher-resolution displacement. In this depression cohort, the most visible first-order low-versus-high BDI shift localizes to `e_m` and `m_o`, rather than to a broad uniform displacement across all nine subcoordinates.

Clinically, the `9D` layer is best read as a localization device inside the state-space rather than as a set of nine independent biomarkers. It helps answer questions such as: is the visible shift broad, or is it concentrated in one specific mobility, deviation, or entropy subfamily?

== First-order geometry versus local dynamics

The manuscript reports several layers because they answer different questions:

- *3D / 9D MNPS:* where subjects tend to sit in state space.
- *MNJ:* how the local flow tends to expand, contract, rotate, or redirect.
- *Block-MNJ:* which broad cross-family couplings may contribute to that local redirection.
- *Reachability:* how locally accessible or constrained nearby dynamical space appears to be.

From a reader's perspective, the most important distinction is between *location* and *movement*. In this depression report, the first-order `3D` location shift is modest, the first-order `9D` location shift is clearer, and the local-dynamics layers ask whether anything remains once that location difference is taken seriously.

= Appendix: Cohort-Anchored Centroid Baseline

All primary between-subject comparisons in this manuscript are made in a cohort-anchored coordinate frame. This matters because centroid-like group differences are therefore directly interpretable as shared-reference displacement rather than as subject-local reparameterizations. The table below summarizes the baseline centroid shifts from `articles/CLINICAL/depression/results/centroid_baseline_summary.csv`.

#table(
  columns: (auto, auto, auto, auto, auto, auto),
  inset: 6pt,
  align: (left, left, center, center, center, left),
  table.header(
    [*Layer*],
    [*Metric*],
    [*Delta*],
    [*Cohen $d$*],
    [*$q$*],
    [*Interpretation*],
  ),
  [`3D`], [`e_median`], [`+0.220`], [0.386], [0.386], [largest coarse shift, but still modest],
  [`3D`], [`e_mean`], [`+0.180`], [0.297], [0.386], [`e`-weighted displacement remains moderate only],
  [`3D`], [`m_mean`], [`+0.220`], [0.259], [0.386], [`m` shifts somewhat but not strongly],
  [`3D`], [`d_mean` / `d_median`], [`+0.018` / `+0.027`], [0.032 / 0.039], [--], [`d` axis is nearly unchanged],
  [`9D`], [`e_m_mean`], [`+0.427`], [0.688], [0.0239], [clearest corrected centroid displacement],
  [`9D`], [`e_m_median`], [`+0.396`], [0.589], [0.0546], [`e_m` shift reproduces directionally but is correction-limited],
  [`9D`], [`m_o_mean`], [`+0.514`], [0.523], [0.0637], [higher-resolution `m` subfamily also shifts, but just above q-threshold],
  [`9D`], [`m_o_median`], [`+0.536`], [0.537], [0.0637], [`m_o` provides parallel `9D` support without surviving family-wise correction],
)

#v(4pt)
#text(size: 9pt, style: "italic")[
  The centroid baseline therefore supports a narrow but important claim: low-versus-high BDI is not strongly separated as a coarse `3D` centroid, but it is more clearly displaced in the cohort-anchored `9D` coordinate system, with `e_m_mean` providing the cleanest family-corrected centroid effect.
]

= Appendix: Centroid-Adjusted Dynamics

To test whether the main depression signal depends too strongly on simple centroid displacement, we ran a separate centroid-adjusted analysis in which selected dynamic summaries were modeled with the matching cohort-anchored centroid family as covariates. For `3D`-family measures we adjusted for `m_mean`, `d_mean`, and `e_mean`; for `9D`-family measures we adjusted for the nine `9D` coordinate means. The resulting summaries are stored in `articles/CLINICAL/depression/results/centroid_adjusted_dynamic_summary.csv`.

#table(
  columns: (auto, auto, auto, auto, auto, auto),
  inset: 6pt,
  align: (left, left, center, center, center, left),
  table.header(
    [*Block / feature*],
    [*Raw effect*],
    [*Adjusted $p$*],
    [*Adjusted $q$*],
    [*Residualized $d$*],
    [*Interpretation*],
  ),
  [`9D` MNJ `rotational_power_mean`], [`d = 0.767`], [0.108], [0.153], [0.375], [substantially weakens after `9D` centroid adjustment],
  [Reachability `tube_log_eig_var_mean`], [`d = -0.816`], [0.167], [0.195], [-0.305], [part of the raw separation tracks `9D` location],
  [Distribution `e_m_mad_sigma`], [`d = 0.984`], [0.0236], [0.0825], [0.577], [retains trend-level support after adjustment],
  [Block-MNJ `block_frobenius_mean`, `m -> m`], [`d = -0.517`], [0.0073], [0.0509], [-0.474], [strongest residual dynamic signal],
  [Block-MNJ `block_frobenius_mean`, `m -> d`], [`d = -0.516`], [0.0529], [0.123], [-0.330], [secondary block-level trend only],
)

#v(4pt)
#text(size: 9pt, style: "italic")[
  The adjusted view changes the emphasis of the paper. Some of the raw `9D` MNJ and reachability signal appears to ride on real `9D` centroid displacement, while the clearest residual dynamic difference after adjustment is block-resolved rather than global.
]

= Appendix: Cautious Clinical Interpretation

This manuscript is not a diagnostic or treatment-guidance paper. The safest clinical reading is narrower.

First, the paper suggests that depressive symptom burden in this cohort is not well summarized by one universal coarse scalar. A low-versus-high BDI separation is visible, but its first-order geometry is weak in `3D` and clearest in specific `9D` subfamilies, especially `e_m_mean`, with parallel but less correction-stable support in `e_m_median` and `m_o`.

Second, BDI should not be conflated with a uniformly adjudicated major depression diagnosis here. The present report is anchored primarily to symptom burden rather than to a frozen diagnostic case-control label, and only part of the high-BDI subgroup has SCID or HamD annotation.

Third, one clinically readable way to summarize the reachability result is that high-BDI recordings appear to occupy a different short-horizon dynamic regime. In this cohort, the strong reachability pattern, including the convergent `tube_log_det_mean` difference, should not be read as "better" or "healthier" capacity, but as evidence that the local neighborhood of reachable next states is configured differently in the elevated-symptom group.

Fourth, the centroid-adjusted appendix matters clinically because it narrows the strongest claim. It suggests that some of the apparent global `9D` / reachability difference reflects where high-BDI recordings sit in the shared state-space, while the strongest residual difference after adjustment is more localized in block-level coupling than in a broad global dynamic shift.

Fifth, none of the results here are ready for individual-level clinical use. The analysis is group-level, the middle BDI band is small, and the manuscript does not establish a bedside biomarker, prognostic score, or treatment-response rule.

#netn-box(title: [Clinical bottom line])[
  In cautious clinical terms, the paper's main result is that elevated depressive symptom burden is geometrically visible in resting EEG, including a reachability shift that suggests a different local dynamic neighborhood. But the dominant organization in this cohort is still best read as a modest coarse displacement, a clearer stratified `9D` displacement centered most cleanly on `e_m_mean`, and only more selective residual local-dynamical differences after centroid adjustment.
]

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
