#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Outcome-Linked 9D Jacobian Geometry After Cardiac-Arrest Coma",
  short-title: "9D Jacobian Geometry in Coma",
  subtitle: "Replicated spectral-radius effects and modest complementarity to reachability in early post-arrest EEG",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "cardiac-arrest coma",
    "I-CARE",
    "EEG",
    "MNPS 9D",
    "Jacobian",
    "NeuralManifoldDynamics",
  ),
  article-type: "Research Article",
  abstract: [
    Early electroencephalography (EEG) after cardiac arrest already supports neuroprognostication, but the main reachability paper left open whether repaired `9D` local-linear summaries carry a distinct outcome-linked signal. We analyzed non-overlapping I-CARE `part1` and `part2_140sub_9d` cohorts together with a pooled `0-12 h` `CPC 1` versus `CPC 5` synthesis after confirming `0` subject overlap and `0` run overlap. `spectral_radius_median` remained the clearest replicated lead (`d = -0.632` in `part1`, `-0.617` in `part2`, pooled `-0.620`; pooled `q = 3.41e-8`). `anisotropy_abs_eig_median` also replicated directionally but with marked cohort asymmetry (`d = -0.348` versus `-0.641`), while `frobenius_norm_median` remained a stable restored comparator across cohorts and hourly bins. `mdr_median` and `rotational_power_mean` were weaker pooled-promoted signals, and `rotational_power_median` was retained only as a supportive companion summary. In repeated cross-validation, revised `9D` metrics alone reached `AUROC = 0.676`, comparable to reachability (`0.673`) but below the older `3D` Jacobian comparator (`0.714`). Adding revised `9D` to `clinical+qEEG+reachability` yielded a small positive paired increment (`Delta AUROC = +0.018` [`+0.013`, `+0.023`]; `Delta` Brier `= -0.008` [`-0.010`, `-0.006`]), while `Delta` `AUPRC = +0.005` [`-0.001`, `+0.011`] was less stable. Because WLST and time-of-death annotations were unavailable in the manuscript-facing bundle, the `CPC 1` versus `CPC 5` contrast should be read as recovery-associated local-linear geometry rather than as a pure neural-viability assay. The bounded conclusion is that repaired `9D` Jacobian summaries add a credible follow-up layer to the coma geometry program, led by spectral radius and a restored Frobenius comparator, but they do not supersede either reachability or the older `3D` Jacobian view.
  ],
  author-summary: [
    This follow-up asks whether repaired `9D` Jacobian summaries add a useful local-linear view beyond the main reachability paper. The most durable signal is lower `spectral_radius_median` in better-outcome patients, with `frobenius_norm_median` remaining a stable restored comparator and `anisotropy_abs_eig_median` replicating directionally but with notable cohort asymmetry. The paper therefore argues for a graded and complementary `9D` story rather than a replacement claim: modest internal prediction gains, honest competition from older `3D` Jacobian summaries, and cautious interpretation because WLST and time-of-death annotations are unavailable in the manuscript-facing bundle.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted in the submission version.],
  data-availability: [The underlying I-CARE dataset is available through PhysioNet version `2.1` at https://doi.org/10.13026/m33r-bj81. This article is based on `9D`-enabled bundles under `articles/CLINICAL/comatose_ndt/results/`, especially `timeline_analysis_20260524_part1_primary12h_9d`, `mnps_summary_20260524_part1_primary12h_9d_targeted`, `timeline_analysis_20260523_part2_primary12h_9d`, and `mnps_summary_20260523_part2_primary12h_9d`. The formal part1 / part2 / pooled `9D` Jacobian contrasts are exported in `articles/CLINICAL/comatose_ndt_jacobian_9d/results/outcome_contrasts_9d_jacobian_20260525_cpc15_primary12h/`. The frozen revised metric hierarchy is stored under `results/result_ledger_20260525_cpc15_primary12h/`; robustness outputs under `results/robustness_20260525_cpc15_primary12h/`; predictive / joint-model outputs under `results/incremental_validity_20260525_cpc15_primary12h/`; the earlier best-available hourly proxy comparison under `results/hourly_20260525_best_available_metrics/`; and the exact hourly rerun under `results/hourly_20260525_exact_revised_9d/`. Figure assets for this refreshed manuscript live under `articles/CLINICAL/comatose_ndt_jacobian_9d/figures/20260525_jacobian_9d/`.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

= Introduction

The main coma article already established that early geometry in the first monitored EEG hours separates later `CPC 1` from later `CPC 5` patients in the I-CARE cohort and its PhysioNet dataset release.@langell2026_reachability, @amorim2023icare, @PhysioNet-i-care-2.1, @sandroni2021european, @nolan2025postresuscitation That article was intentionally conservative about scope: it focused on a frozen set of `3D` reachability summaries that could be traced cleanly through the locked discovery bundle, the explicit verification bundle, and the pooled synthesis.

The repaired `9D` coordinate layer raises a different question. Once stratified `9D` coordinates and their Jacobians are available in both dated cohorts, should the next article still treat `9D` as a peripheral comparator, or does the cleaner follow-up hypothesis live there instead?

This draft takes the second option. It does not try to widen the first paper. Instead, it sketches a follow-up manuscript centered on `global_mnps_jacobian_9d` summaries. The scientific rationale is simple: Jacobian summaries on the repaired `9D` state space are more natural local-dynamical measures than the coordinate-spread scalar `coords_9d_global_std_mean`, and they may offer a cleaner bridge between stratified state geometry and early neuroprognostic separation. Compact definitions of the main MNJ metrics used here are given in the appendix.

This follow-up is not primarily motivated by a claim that repaired `9D` should outperform every older comparator in standalone discrimination. In the current internal rerun, the older `3D` Jacobian comparator remains competitive. The value proposition of the present paper is instead that repaired `9D` scalar Jacobian summaries provide a distinct and auditable local-linear view that may still contribute information partly complementary to the main reachability family.

As in the main reachability article, the aim here is not to claim a bedside-ready neuroprognostic model, a direct measure of consciousness, or a pure neural-viability assay. The narrower goal is to test whether a repaired and auditable `9D` local-linear layer carries outcome-linked structure inside the same early EEG window, while keeping the clinical interpretation conservative.

#netn-box(title: [Core question])[
  In the first `12 h` after EEG-anchor, do later `CPC 1` and later `CPC 5` patients differ in repaired `9D` Jacobian geometry in a way that both replicates across the `part1` / `part2_140sub_9d` split and remains informative beyond the earlier reachability layer?
]

= Cohort and provenance scope

This draft uses only the bundles that actually support a symmetric `9D` Jacobian comparison.

1. `part1`: `timeline_analysis_20260524_part1_primary12h_9d` + `mnps_summary_20260524_part1_primary12h_9d_targeted`
2. `part2`: `timeline_analysis_20260523_part2_primary12h_9d` + `mnps_summary_20260523_part2_primary12h_9d`

That choice matters. The earlier verification run `neuralmanifolddynamics_physionet_icare_2_1_20260522_095945_part2_140sub` does *not* contain `9D` coordinates or `9D` Jacobians, so it is not the correct partner for a `9D` follow-up article. The later `part2_140sub_9d` rerun is the appropriate verification-side counterpart.

The pooled summaries below come from the dedicated manuscript-facing `20260525` `9D` Jacobian export, which concatenates the non-overlapping `9D`-enabled `part1` and `part2` patient-timebin tables only after verifying `0` subject overlap and `0` run overlap in the source manifests.

#figure(
  kind: table,
  table(
    columns: (2.35fr, 1.35fr, 1.35fr, 1.45fr),
    align: left,
    inset: 5pt,
    table.header([*Bundle item*], [*`part1` `9D`*], [*`part2` `9D`*], [*Pooled `9D` export*]),
    [Analyzable subjects in local `0-12 h` index], [161], [140], [301],
    [Extreme-outcome `CPC 1 / CPC 5` subset], [141 (`71 / 70`)], [140 (`70 / 70`)], [281 (`141 / 140`)],
    [`9D` coordinates present in source run manifest], [yes], [yes in later `part2_140sub_9d` rerun], [yes by construction],
    [`global_mnps_jacobian_9d` available], [yes], [yes], [yes],
    [Primary role in this article], [locked discovery / reference], [explicit verification], [manuscript-facing pooled synthesis],
  ),
  caption: [Scope of the `9D` Jacobian follow-up draft. This article intentionally uses the `9D`-enabled discovery and verification bundles rather than the earlier non-`9D` `part2` export.]
) <tab-scope>

= Why a separate article

The first coma article was already near the upper limit of reasonable scope. Adding a second, partially repaired metric family would have blurred the main message and weakened provenance discipline. A dedicated `9D` Jacobian article is cleaner for three reasons.

First, the measurement object is different. The reachability paper asks whether local short-horizon reachable structure differs by outcome. The present draft asks whether local-linear deformation in the repaired stratified `9D` state space differs by outcome.

Second, the article-facing candidates are different. The `3D` reachability story emphasized effective dimensionality, persistence, and capture. The formal `9D` Jacobian export now centers more clearly on spectral radius, anisotropy-like spread, `mdr`, and rotational-power structure than on the older operator / Frobenius / rotation-norm trio.

Third, the provenance chain is different. The `9D` comparison depends on the later repaired `part1` and `part2` bundles, so it is methodologically cleaner to write a follow-up manuscript than to splice those bundles into the original article's main evidence chain.

= Methods

== Primary analysis contract

As in the reachability manuscript, the primary time bin is the first `12 h` after EEG-anchor and the primary contrast is later `CPC 1` versus later `CPC 5`.@westhall2016standardized, @ruijter2019early, @hofmeijer2015early We again treat the patient as the unit of inference.

The candidate family in this article comes from `global_mnps_jacobian_9d`, not from the `3D` reachability or `3D` Jacobian exports. The main change from the earlier draft is that the manuscript hierarchy is now frozen against the *formal* pooled `20260525` export rather than against the older provisional Jacobian shortlist. The revised hierarchy is therefore:

1. `spectral_radius_median`
2. `anisotropy_abs_eig_median`
3. `mdr_median`
4. `rotational_power_mean`

The older operator-size trio (`a_operator_norm_median`, `frobenius_norm_median`, `rotation_norm_median`) is retained as replication-supportive legacy context because it still replicates directionally in both cohorts, but it is no longer treated as the primary pooled hierarchy. Within that legacy trio, `frobenius_norm_median` is restored here to the main reported set because it was removed from the previous article, remains directionally replicated, and can now be traced through both the formal `0-12 h` export and the exact hourly rerun. `rotational_power_median` is retained only as a supportive companion to `rotational_power_mean`, because its cohort-specific verification and hourly support are noticeably weaker than the main article-facing set. Compact mathematical definitions for `spectral_radius_median`, `anisotropy_abs_eig_median`, `frobenius_norm_median`, `mdr_median`, and the rotational-power summaries are given in the appendix.

== Outcome interpretation and selection status

The extreme-outcome `CPC 1` versus `CPC 5` contrast sharpens separation but must still be interpreted conservatively because `CPC 5` intersects with death, systemic illness severity, treatment limitation, and potentially withdrawal-of-life-sustaining therapy rather than representing a pure neural recovery assay.@rajajee2023neuroprognostication, @nolan2025postresuscitation The current manuscript-facing `9D` bundle does not preserve explicit WLST or time-of-death annotations, so this article cannot partition `CPC 5` into post-WLST versus other death pathways.

The selection boundary also differs from the main reachability paper. Here the article-facing hierarchy was *not* frozen from discovery-only ranking and then carried forward unchanged. Instead, the formal pooled `20260525` export was audited first, after which the manuscript hierarchy was frozen. That means the leading pair (`spectral_radius_median`, `anisotropy_abs_eig_median`) can be described as directionally replicated across the dated cohorts, whereas `mdr_median` and the rotational-power summaries should be described more carefully as pooled-promoted signals rather than as prospectively frozen verification targets.

#netn-box(title: [Selection And Validation Status])[
  *Primary analysis family:* `global_mnps_jacobian_9d` in the formal `0-12 h` `CPC 1` versus `CPC 5` export.

  *Primary replicated lead across dated cohorts:* `spectral_radius_median`.

  *Secondary replicated direction with magnitude asymmetry:* `anisotropy_abs_eig_median`.

  *Pooled-promoted signals:* `mdr_median`, `rotational_power_mean`.

  *Supportive companion summary:* `rotational_power_median`.

  *Restored main comparator:* `frobenius_norm_median` (retained in the main article-facing set despite pooled rank `7` because it directionally replicates and is available in the exact hourly rerun).

  *Verification status:* dated `part2_140sub_9d` provides directional replication, but the revised article-facing hierarchy itself was frozen only after auditing the pooled export.

  *Prediction / joint-model status:* internal synthesis analyses, not external validation of a prospectively frozen bedside measurement layer.
]

== Statistical summary

For each candidate we report group medians, Cohen's `d`, and Mann-Whitney `p` in the compact manuscript tables below. The formal `20260525` export also computes BH-FDR within the exact `global_mnps_jacobian_9d` primary-bin family; those `q` values are retained in the result ledger and candidate-ranking tables under `results/`.

== Predictive model specification

For internal predictive synthesis, every ladder used the same classifier pipeline: median imputation, z-scoring, and balanced `LogisticRegression` with `liblinear` solver. Repeated cross-validation used `RepeatedStratifiedKFold` with `5` splits and `20` repeats, while site sensitivity used `LeaveOneGroupOut()` with hospital as the held-out group. The held-out-site evaluation excludes `cat__hospital_*` dummy columns to avoid out-of-support extrapolation. Feature ladders were fixed before model fitting and no additional fold-wise feature selection or univariate screening was performed inside the cross-validation loop.

The main predictive ladders were baseline clinical+qEEG, revised `9D` alone, reachability alone, older `3D` Jacobian alone, clinical+qEEG+revised `9D`, clinical+qEEG+reachability, and clinical+qEEG+reachability+revised `9D`. Fold-averaged coefficients reported below come from the repeated-CV logistic models and should be read as internal ranking aids rather than as stable mechanistic weights.

== Robustness and joint-model protocol

Secondary analyses were deliberately built after freezing the revised hierarchy. The refreshed article-local robustness package includes shockable-only and non-shockable-only sensitivity analyses, a QC-only proxy model based on usable windows and coverage/channel-count fields, QC correlations, patient-label permutation, winsorized effect-size sensitivity, and leave-one-site-out effect summaries. Because the revised `9D` hierarchy was itself frozen only after inspecting the audited pooled export, all prediction and joint-model results below should be read as internal synthesis analyses rather than as external validation of a prospectively frozen bedside measurement layer.

== Hourly localization protocol

To localize the revised `9D` signals within the first `12 h`, we ran a dedicated hourly rerun of `global_mnps_jacobian_9d` against the repaired `hourly_12h` `part1` and `part2` timeline bundles. The upstream rerun was prefiltered to `CPC 1` and `CPC 5` only; the article-facing hourly summary then restricted the pooled patient-timebin handoff to the twelve bins `0_1h` through `11_12h`. This distinction matters because the upstream H5-run counts refer to all selected extreme-outcome runs in the hourly bundle, whereas the manuscript-facing hourly table and heatmap below use only the first-`12 h` patient-timebin rows. Within each metric, BH-FDR was applied across its twelve hourly contrasts.

#figure(
  kind: table,
  table(
    columns: (1.15fr, 0.9fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*Hourly bin*], [*`CPC 1` n*], [*`CPC 5` n*]),
    [`0_1h`], [`131`], [`131`],
    [`1_2h`], [`131`], [`130`],
    [`2_3h`], [`131`], [`133`],
    [`3_4h`], [`131`], [`124`],
    [`4_5h`], [`129`], [`126`],
    [`5_6h`], [`124`], [`128`],
    [`6_7h`], [`129`], [`130`],
    [`7_8h`], [`128`], [`131`],
    [`8_9h`], [`124`], [`129`],
    [`9_10h`], [`118`], [`130`],
    [`10_11h`], [`123`], [`127`],
    [`11_12h`], [`123`], [`124`],
  ),
  caption: [Hourly patient support for the exact revised `9D` rerun. Counts are identical across the reported exact-hourly metrics because the pooled patient-timebin handoff uses the same `CPC 1` / `CPC 5` subject filter in each bin.]
) <tab-hourly-support>

= Results

== Cohort-wise replication remains anchored by spectral radius before pooled reranking

The main article-facing story should still begin with what survives in both dated cohorts before any pooled reranking is discussed. The strongest result remains unchanged: better-outcome patients have lower `9D` Jacobian spectral radius in both `part1` (`d = -0.632`, `p = 9.76e-6`) and `part2` (`d = -0.617`, `p = 1.11e-4`), with pooled `d = -0.620` and pooled BH-FDR `q = 3.41e-8`. `anisotropy_abs_eig_median` also remains directionally replicated, but its magnitude is notably asymmetric (`d = -0.348` in `part1` versus `-0.641` in `part2`, pooled `-0.337`). It is therefore best treated as a secondary replicated direction rather than as a fully stabilized co-lead. Readers who want the compact mathematical definitions of these MNJ summaries can find them in the appendix.

After those two replicated directions, the pooled reranking becomes narrower and more conditional. In the audited pooled ranking, the next two article-facing signals are `mdr_median` (pooled `d = -0.287`, `p = 3.05e-4`) and `rotational_power_mean` (`d = -0.285`, `p = 4.49e-5`). `rotational_power_median` remains directionally consistent and pooled-significant (`d = -0.260`, `p = 0.00383`), but it is retained only as a supportive companion because its cohort-specific verification and hourly support are visibly weaker than the primary article-facing set.

At the same time, `frobenius_norm_median` deserves explicit recovery into the article's main reported set. It is not one of the pooled-promoted metrics, and its pooled rank remains lower (`7`), but it still replicates directionally in both dated cohorts (`d = -0.280` in `part1`, `-0.464` in `part2`) with pooled `d = -0.230`, pooled `p = 7.53e-7`, and pooled `q = 3.01e-6`. That combination makes it too stable and too Jacobian-relevant to leave buried only in the supporting tier.

#figure(
  image("figures/20260525_jacobian_9d/fig1_9d_provenance_overview.svg", width: 100%),
  caption: [Provenance overview for the refreshed `9D` Jacobian article bundle. The pooled synthesis is built only after verifying `0` subject overlap and `0` run overlap between the `part1` and `part2_140sub_9d` sources.]
) <fig-9d-provenance>

#figure(
  kind: table,
  table(
    columns: (2.15fr, 1.15fr, 0.95fr, 0.95fr, 1.15fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Metric*],
      [*`part1` med*], [*`part1` `d`*], [*`part1` `p`*],
      [*`part2` med*], [*`part2` `d`*], [*`part2` `p`*],
    ),
    [`spectral_radius_median`], [`0.097 / 0.106`], [`-0.632`], [`9.76e-6`], [`0.097 / 0.103`], [`-0.617`], [`1.11e-4`],
    [`anisotropy_abs_eig_median`], [`0.000861 / 0.001030`], [`-0.348`], [`7.46e-6`], [`0.000868 / 0.000977`], [`-0.641`], [`1.29e-4`],
    [`mdr_median`], [`0.151 / 0.153`], [`-0.223`], [`0.0124`], [`0.151 / 0.154`], [`-0.397`], [`0.00959`],
    [`rotational_power_mean`], [`0.0283 / 0.0295`], [`-0.300`], [`0.00259`], [`0.0280 / 0.0288`], [`-0.388`], [`0.00527`],
    [`frobenius_norm_median`], [`0.621 / 0.691`], [`-0.280`], [`4.04e-5`], [`0.618 / 0.673`], [`-0.464`], [`0.00422`],
  ),
  caption: [Cohort-specific `0-12 h` extreme-outcome contrasts for the main article-facing `9D` Jacobian set. Median entries are shown as `CPC 1 / CPC 5`.]
) <tab-primary-cohorts>

#figure(
  kind: table,
  table(
    columns: (2.2fr, 1.2fr, 1.0fr, 1.0fr, 1.0fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Metric*],
      [*Pooled med*], [*Pooled `d`*], [*Pooled `p`*], [*Pooled `q`*],
    ),
    [`spectral_radius_median`], [`0.097 / 0.105`], [`-0.620`], [`3.41e-9`], [`3.41e-8`],
    [`anisotropy_abs_eig_median`], [`0.000865 / 0.001011`], [`-0.337`], [`3.27e-9`], [`3.41e-8`],
    [`mdr_median`], [`0.151 / 0.153`], [`-0.287`], [`3.05e-4`], [`6.10e-4`],
    [`rotational_power_mean`], [`0.0280 / 0.0289`], [`-0.285`], [`4.49e-5`], [`9.97e-5`],
    [`frobenius_norm_median`], [`0.619 / 0.690`], [`-0.230`], [`7.53e-7`], [`3.01e-6`],
  ),
  caption: [Pooled `0-12 h` extreme-outcome synthesis for the main article-facing `9D` Jacobian set. Median entries are shown as `CPC 1 / CPC 5`. This pooled table follows the frozen result ledger built from the formal `20260525` export, while also restoring `frobenius_norm_median` as an explicit main reported comparator.]
) <tab-primary-pooled>

#figure(
  image("figures/20260525_jacobian_9d/fig2_9d_revised_forest.svg", width: 100%),
  caption: [Revised hierarchy forest plot across `part1`, `part2`, and pooled synthesis. The figure foregrounds the main article-facing metrics while the legacy operator / norm family remains supportive context.]
) <fig-9d-revised-forest>

== Distribution shape and robustness are not identical across the revised family

The revised hierarchy does not imply that all five main reported metrics deserve identical interpretive weight. `spectral_radius_median` remains strong in the full cohort and within both shockable-only (`d = -0.525`, `p = 2.07e-4`) and non-shockable-only (`d = -0.733`, `p = 1.52e-4`) subsets. `anisotropy_abs_eig_median` is directionally stable but more heterogeneous in magnitude across cohorts and rhythm strata (`d = -0.322` and `-0.669`), which is why it is treated here as a secondary replicated direction rather than as a fully stabilized co-lead.

The restored Frobenius comparator is more stable than its pooled rank alone suggests. `frobenius_norm_median` remains directionally separated in both rhythm strata (`d = -0.240`, `p = 2.87e-4`; `d = -0.471`, `p = 0.00933`), and its winsorized pooled separation deepens materially (`d = -0.525`). That makes it a useful main Jacobian-scale reference even though the audited pooled hierarchy still places it below the `mdr` / rotational tier.

The pooled-promoted layer is narrower. `rotational_power_mean` survives both rhythm strata (`d = -0.338`, `p = 0.00513`; `d = -0.352`, `p = 0.00256`) and remains above the permutation null (`empirical p = 0.0020`). `mdr_median` remains article-worthy as a pooled-promoted signal, but its current support is driven much more by the non-shockable subset (`d = -0.546`, `p = 0.00453`) than by the shockable subset (`d = -0.139`, `p = 0.0615`), so it should be read as a non-shockable-weighted signal rather than as a uniform cohort-wide lead. `rotational_power_median` behaves only as a weaker companion to `rotational_power_mean` and is therefore kept outside the primary hierarchy.

#figure(
  image("figures/20260525_jacobian_9d/fig3_9d_distribution_panel.svg", width: 100%),
  caption: [Display-only winsorized distribution view for the strongest replicated leads, the restored Frobenius comparator, and one pooled-promoted rotational metric. Each metric is clipped to the pooled `1st-99th` percentile range to reduce tail dominance, while all inferential statistics reported in the manuscript remain based on the original untrimmed values.]
) <fig-9d-distributions>

#figure(
  image("figures/20260525_jacobian_9d/fig3a_9d_revised_metric_violins.png", width: 100%),
  caption: [Pooled `0-12 h` violin-grid for the main article-facing `9D` Jacobian metrics together with the supportive `rotational_power_median` companion. The raw pooled values again show lower central tendency in `CPC 1` than in `CPC 5`, with the clearest visual separation in the leading spectral-radius, anisotropy, and Frobenius summaries.]
) <fig-9d-revised-violins>

#figure(
  image("figures/20260525_jacobian_9d/fig3b_9d_revised_metric_violins_winsorized.png", width: 100%),
  caption: [Display-only winsorized version of the pooled `0-12 h` `9D` violin-grid. Each metric is clipped to its pooled `1st-99th` percentile range to reduce tail dominance and make the core group separation easier to inspect; all inferential statistics in the manuscript remain based on the untrimmed values.]
) <fig-9d-revised-violins-winsorized>

#figure(
  image("figures/20260525_jacobian_9d/fig4_9d_robustness_heatmap.svg", width: 100%),
  caption: [Robustness map for the revised and legacy `9D` Jacobian metrics. The pooled-promoted layer is not uniformly stable: `rotational_power_mean` persists across rhythm strata more cleanly than `mdr_median`, while the supportive `rotational_power_median` remains visibly weaker.]
) <fig-9d-robustness>

The QC-only proxy model remains modest (`AUROC = 0.559`, `AUPRC = 0.558`), which argues against a trivial coverage-only explanation. QC correlations are present but not overwhelming. The strongest occur for the rotational-power summaries versus coverage/channel-count proxies (for example `rotational_power_median` rho `= -0.267` against both available coverage proxies), whereas the leading spectral-radius result is much less entangled with those same fields. That pattern is more consistent with partial QC sensitivity layered on top of genuine signal than with a purely QC-defined effect, but it does not fully falsify a QC contribution to the rotational-power family; those metrics should therefore be interpreted more cautiously than the spectral-radius and Frobenius lines.

== Exact hourly rerun localizes the revised `9D` family to an early-present, mid-window-stronger pattern

The exact hourly rerun does not support a single delayed onset hour. Per-bin support remains substantial throughout the window (`CPC 1` n `= 118-131`, `CPC 5` n `= 124-133`; @tab-hourly-support), which reduces the risk that the early bins are being driven by tiny edge subsets. `spectral_radius_median` and `anisotropy_abs_eig_median` are BH-FDR-significant in every hourly bin from `0_1h` through `11_12h`, with both peaking at `3_4h` (`d = -0.667` and `-0.658`). That pattern is more consistent with early presence plus stronger mid-window separation than with a one-bin threshold effect.

The restored Frobenius comparator belongs in this main hourly story as well. `frobenius_norm_median` is BH-FDR-significant in every hourly bin, first at `0_1h` and strongest at `2_3h` (`d = -0.595`), which places it closer to the leading replicated pair than to the weaker tail of the pooled-promoted tier in temporal stability.

The pooled-promoted layer is weaker but still informative. `mdr_median` is already significant at `0_1h` (`q = 0.0365`) and is strongest at `6_7h` (`d = -0.405`). `rotational_power_mean` is significant in nearly every hourly bin, strongest at `5_6h` (`d = -0.507`), while `rotational_power_median` remains only a supportive companion summary and reaches BH-FDR significance in a smaller subset of bins (`2_3h`, `5_6h`, `8_9h`, and `9_10h`). Across all exact hourly metrics, lower values remain associated with later `CPC 1`.

#figure(
  image("results/hourly_20260525_exact_revised_9d/hourly_exact_revised_9d_heatmap.png", width: 100%),
  caption: [Exact hourly rerun for the article-facing `9D` Jacobian set. The leading pair (`spectral_radius_median` and `anisotropy_abs_eig_median`) and the restored `frobenius_norm_median` are significant across the full `0-12 h` window, whereas `mdr` and the rotational-power summaries are weaker and more localized. Asterisks denote BH-FDR `< 0.05` within metric across the twelve hourly bins; hourly patient support is summarized in @tab-hourly-support.]
) <fig-9d-hourly>

== Earlier best-available hourly proxies pointed in the same direction

Before the exact `global_mnps_jacobian_9d` hourly rerun was rebuilt, the repaired hourly `9D` timeline exports exposed only a smaller proxy set: `jacobian_fro_median`, `jacobian_spectral_radius_median`, and `coords_9d_global_std_mean`. That earlier comparison should remain in the article because it provides an independent chronology of what the hourly repaired bundles already supported before the exact revised-family rerun existed.

The proxy pattern is broadly concordant with the exact rerun rather than contradictory to it. `jacobian_fro_median` is BH-FDR-significant from `0_1h` onward and is strongest at `5_6h` (`d = -0.664`); `jacobian_spectral_radius_median` is likewise significant from `0_1h` and peaks at `3_4h` (`d = -0.593`); and the earlier coordinate-spread comparator `coords_9d_global_std_mean` first reaches BH-FDR significance at `1_2h` and is strongest at `3_4h` (`d = -0.500`). These proxies should not be treated as substitutes for the exact revised `9D` Jacobian family, but they reinforce the narrower temporal claim that lower-geometry better-outcome separation is already present early and tends to strengthen through the early-to-mid window.

#figure(
  image("results/hourly_20260525_best_available_metrics/hourly_best_available_heatmap.png", width: 100%),
  caption: [Earlier best-available hourly proxy comparison from the repaired `9D` timeline exports. These rows are not the exact revised article-facing `global_mnps_jacobian_9d` metrics, but the same early-present and mid-window-stronger organization is already visible in `jacobian_fro_median`, `jacobian_spectral_radius_median`, and `coords_9d_global_std_mean`. Asterisks denote BH-FDR `< 0.05` within metric across the twelve hourly bins.]
) <fig-9d-hourly-proxy>

== Relationship to reachability and older Jacobian layers

The revised `9D` layer overlaps only partly with the main reachability story. `spectral_radius_median` correlates strongly with the older `3D` Jacobian summaries (`rho = 0.814` with `jacobian_spectral_radius_median`, `rho = 0.848` with `jacobian_fro_median`), which suggests that the dominant expansion-scale signal is not unique to the repaired `9D` state space. By contrast, `anisotropy_abs_eig_median` is more mixed: it is moderately negative with `tube_d_eff_median` (`rho = -0.574`) but positive with `tube_capture_gate_median` (`rho = 0.603`), indicating partial overlap rather than simple redundancy.

`mdr_median` is the most informative pooled-promoted bridge here. It correlates only weakly with the five-feature reachability layer (`rho = -0.056` to `0.139`) while remaining moderately to strongly aligned with older Jacobian comparators (`rho = 0.753` with `jacobian_spectral_radius_median`, `0.711` with `jacobian_fro_median`). That pattern supports a useful interpretive split: the revised `9D` follow-up is not merely re-reporting effective dimensionality under a different name, but neither does it completely supersede earlier Jacobian summaries.

#figure(
  image("figures/20260525_jacobian_9d/fig6_joint_signal_correlation_heatmap.svg", width: 100%),
  caption: [Joint signal correlation map across revised `9D` Jacobian leads, the main reachability family, older `3D` Jacobian comparators, and the earlier `coords_9d_global_std_mean` spread comparator. The repaired `9D` layer overlaps partly with both the Jacobian and reachability stories rather than collapsing onto either one.]
) <fig-9d-corr>

== Prediction and joint-model complementarity

The predictive results are informative but should be read conservatively. As a standalone feature family, revised `9D` metrics perform about as well as the five-feature reachability layer (`AUROC = 0.676` [`0.664`, `0.687`] versus `0.673` [`0.661`, `0.685`]) and clearly above the restricted structured clinical+qEEG baseline (`0.588` [`0.576`, `0.601`]). The older `3D` Jacobian comparator is still surprisingly competitive as a standalone family (`AUROC = 0.714` [`0.701`, `0.727`]), which means the refreshed `9D` paper should not claim that repaired `9D` metrics uniformly dominate earlier Jacobian views.

The more useful comparison is additive, but the additive story has two distinct scales. Relative to the restricted clinical+qEEG baseline, both reachability and revised `9D` produce large paired gains (`Delta AUROC = +0.104` [`+0.095`, `+0.113`] and `+0.106` [`+0.096`, `+0.115`], respectively). The narrower complementarity question is whether revised `9D` adds anything once reachability is already present. On that paired comparison, adding revised `9D` to `clinical+qEEG+reachability` yields a smaller but still positive `Delta AUROC = +0.018` [`+0.013`, `+0.023`] and `Delta` Brier `= -0.008` [`-0.010`, `-0.006`], while `Delta` `AUPRC = +0.005` [`-0.001`, `+0.011`] is less stable. The combined reachability+`9D` ladder nevertheless reaches the strongest repeated-CV `AUROC` among the tested structured models (`0.710` [`0.698`, `0.722`]) and the best leave-one-site-out `AUROC` (`0.668` [`0.633`, `0.704`]).

#figure(
  kind: table,
  table(
    columns: (2.05fr, 1.2fr, 1.2fr, 1.0fr, 1.05fr, 1.35fr),
    align: left,
    inset: 4pt,
    table.header([*Model*], [*Repeated-CV `AUROC`*], [*Repeated-CV `AUPRC`*], [*Brier*], [*LOSO `AUROC`*], [*Repeated-CV `Delta AUROC` vs `C+qEEG+Reach`*]),
    [`Clinical + qEEG`], [`0.588 [0.576, 0.601]`], [`0.569 [0.558, 0.580]`], [`0.259 [0.255, 0.264]`], [`0.577 [0.523, 0.630]`], [`-0.104 [-0.113, -0.095]`],
    [`Revised `9D` only`], [`0.676 [0.664, 0.687]`], [`0.618 [0.606, 0.631]`], [`0.222 [0.219, 0.225]`], [`0.630 [0.583, 0.674]`], [`-0.017 [-0.030, -0.004]`],
    [`Reachability only`], [`0.673 [0.661, 0.685]`], [`0.654 [0.642, 0.666]`], [`0.226 [0.222, 0.230]`], [`0.627 [0.546, 0.685]`], [`-0.020 [-0.031, -0.008]`],
    [`3D Jacobian only`], [`0.714 [0.701, 0.727]`], [`0.677 [0.662, 0.692]`], [`0.218 [0.215, 0.222]`], [`0.663 [0.578, 0.728]`], [`+0.022 [+0.009, +0.034]`],
    [`Clinical + qEEG + revised `9D``], [`0.694 [0.682, 0.705]`], [`0.641 [0.629, 0.653]`], [`0.226 [0.221, 0.231]`], [`0.643 [0.604, 0.685]`], [`+0.001 [-0.006, +0.009]`],
    [`Clinical + qEEG + reachability`], [`0.692 [0.680, 0.705]`], [`0.660 [0.648, 0.674]`], [`0.231 [0.226, 0.237]`], [`0.641 [0.613, 0.669]`], [`0.000 [0.000, 0.000]`],
    [`Clinical + qEEG + reachability + revised `9D``], [`0.710 [0.698, 0.722]`], [`0.665 [0.652, 0.679]`], [`0.223 [0.217, 0.228]`], [`0.668 [0.633, 0.704]`], [`+0.018 [+0.013, +0.023]`],
  ),
  caption: [Internal predictive comparison for the revised `9D` article. Repeated-CV intervals are bootstrap confidence intervals on mean fold performance, and the final column reports the paired repeated-CV `Delta AUROC` against `clinical + qEEG + reachability`. These values should be read as internal synthesis analyses, not as external validation of a prospectively frozen bedside model.]
) <tab-predictive>

#figure(
  image("figures/20260525_jacobian_9d/fig5_9d_prediction_panel.svg", width: 100%),
  caption: [Repeated-CV and leave-one-site-out `AUROC` for the main predictive ladders. The combined reachability+`9D` model is the strongest structured model tested here, but the gain over reachability alone is modest.]
) <fig-9d-prediction>

= Discussion

The repaired `9D` Jacobian layer still deserves its own article rather than a footnote in the reachability manuscript. The reason, however, is now more specific than in the older draft. The dedicated `20260525` export does not support a simple story in which one hand-picked five-metric Jacobian family cleanly carries the whole paper. Instead it supports a layered story: one dominant replicated expansion marker, one secondary but magnitude-asymmetric anisotropy signal, one restored Frobenius comparator that remains too stable to bury in the appendix tier, and a smaller pooled-promoted `mdr` / rotational layer.

That revised structure is scientifically more useful than the older shortlist because it makes the article less doctrinaire. The follow-up paper no longer has to argue that the repaired `9D` family replaces the reachability story or even the older `3D` Jacobian comparators. In the current rerun the `3D` Jacobian-only model is still very competitive, and the revised `9D` family is better interpreted as a sharper decomposition of local-linear structure than as a universal winner across every comparison. The joint-model results push in the same direction: in fold-averaged repeated-CV coefficients, `tube_d_eff_median`, Hjorth mobility / complexity, `anisotropy_abs_eig_median`, `rotational_power_mean`, and `spectral_radius_median` all remain active in the combined reachability+`9D` ladder, which supports partial complementarity rather than a wholesale `9D` takeover.

The practical implication is that the strongest framing for this paper is complementarity with graded confidence. The main paper remains the cleanest source for a frozen reachability-first narrative. The present follow-up paper then asks what happens when one looks directly at repaired local-linear deformation in the stratified `9D` space. The answer is that the `9D` layer is not empty and not redundant, but also not uniformly stronger than every comparator. It contributes a dominant spectral-radius effect, a secondary anisotropy signal that still needs cautious reading because of cohort asymmetry, a restored Frobenius comparator that remains visible in both the `0-12 h` and exact hourly analyses, and a smaller rotational / `mdr` tier that should be interpreted with less confidence than the leading trio. In prediction, the clearest additive steps occur from baseline clinical+qEEG to either reachability or revised `9D`; the narrower gain from adding revised `9D` on top of reachability is positive in paired `AUROC` and Brier summaries but smaller, and the paired `AUPRC` increment is less stable. The new exact hourly rerun sharpens the dynamical picture further: the leading pair and Frobenius are already present in the first hour and then strengthen in the early-to-mid window, rather than appearing only after a delayed transition. The earlier best-available hourly proxy map points in the same direction, which matters because it shows that the temporal organization was already visible before the exact revised-family rerun was rebuilt.

Across the main `9D` summaries, lower values in `CPC 1` point toward a more contractive and locally steadier regime in the better-outcome group: lower spectral radius means a smaller dominant local gain, lower Frobenius norm means weaker overall local deformation, lower `mdr` means slower Jacobian change relative to its current scale, and lower rotational-power means weaker complex-eigenvalue content. In NDT terms, that pattern is compatible with a more locally stable linear regime in the better-outcome group rather than with a stronger expansive or rapidly reconfiguring one. Read together with the reachability paper, the conservative interpretation is not lower dynamical capacity overall, but broader reachable capacity paired with less locally expansive linear deformation.

= Limitations

This article has eight main limitations.

1. The revised article-facing hierarchy was frozen after inspecting the formal pooled `20260525` export, not from a prospectively preregistered metric plan. The pooled-promoted `mdr` and rotational-power signals therefore require more caution than `spectral_radius_median`.
2. The extreme-outcome endpoint sharpens separation but also makes interpretation more delicate because `CPC 5` intersects with death, treatment limitations, and potentially withdrawal-of-life-sustaining therapy rather than representing a pure neural recovery assay.@rajajee2023neuroprognostication The current manuscript-facing `9D` bundle does not retain explicit WLST or time-of-death metadata, so this article cannot currently separate post-WLST deaths from other `CPC 5` pathways.
3. The joint-model and predictive sections are internal synthesis analyses rather than external validation. They include the same pooled cohort used to motivate the revised `9D` hierarchy, and the smallest additive step in the manuscript is the paired `reachability + revised 9D` increment rather than the much larger baseline-to-geometry jumps.
4. The reachability-versus-`9D` joint models merge aligned subject-level features from multiple audited bundle layers rather than from one single prospectively frozen multimodal handoff.
5. The QC proxy package addresses usable-window count and coarse channel-coverage structure, but direct artifact burden remains unavailable because the detector was off in the relevant export layer. This is especially relevant for the rotational-power family, where partial QC sensitivity cannot be fully excluded by the current proxy checks alone.
6. The rhythm-stratified results are heterogeneous: `mdr_median` is clearly weaker in the shockable subset than in the non-shockable subset, so its current support should be read as non-shockable-weighted rather than uniform. `rotational_power_median` is the least stable member of the revised pooled-promoted tier, and the restored `frobenius_norm_median` is more stable than those pooled-promoted signals but still not as strong as `spectral_radius_median`.
7. The older `3D` Jacobian comparator remains competitive in the current internal prediction rerun, so the present paper should not be read as evidence that repaired `9D` metrics uniformly dominate earlier Jacobian summaries.
8. The earlier best-available hourly proxy comparison is supportive but not exact: it uses the strongest Jacobian / `9D`-near fields present in the repaired hourly timeline exports rather than the full revised article-facing `global_mnps_jacobian_9d` family.

= Conclusion

The repaired `9D` follow-up path is viable, but the formal `20260525` export changes what the article should actually claim. The durable center is `spectral_radius_median`, with `anisotropy_abs_eig_median` as a secondary but magnitude-asymmetric replicated signal. `frobenius_norm_median` should also remain in the main article-facing set as a restored Jacobian comparator because it directionally replicates in both dated cohorts and remains significant across the full exact hourly window. The pooled hierarchy then promotes `mdr` and `rotational_power_mean` ahead of the older norm-based trio, but those promoted signals are not equally robust and should be reported with graded confidence, while `rotational_power_median` remains only a supportive companion summary. The exact hourly rerun adds an important localization constraint: the strongest `9D` separation is already present in the first monitored hour and tends to peak in the `2-7 h` window rather than emerging as a single late threshold event, with per-bin support remaining in the `118-131` (`CPC 1`) and `124-133` (`CPC 5`) range. In internal prediction, revised `9D` metrics are comparable to reachability as a standalone family, and adding revised `9D` on top of `clinical+qEEG+reachability` yields a small positive paired `AUROC` / Brier increment while the paired `AUPRC` gain is less stable. Older `3D` Jacobian summaries also remain competitive. The most defensible reading is therefore that repaired `9D` Jacobian geometry adds a useful complementary layer to the coma geometry program: strong enough for a dedicated follow-up article, but not strong enough to replace the main reachability paper, not a direct neural-viability assay in the current bundle, and not strong enough to justify a maximalist translational claim.

 = Appendix: MNJ Metric Definitions

This appendix gives compact mathematical definitions for the article-facing MNJ summaries emphasized in the main text. The aim is to make the Jacobian layer auditable without turning the manuscript into a stand-alone methods paper.

== Local `9D` Jacobian summary

For each analyzable local window on the repaired stratified `9D` state space, let $J_t in RR^(9 times 9)$ denote the estimated local Jacobian of the fitted dynamics map, and let $lambda_(1,t), dots, lambda_(9,t)$ be its eigenvalues. The article-facing MNJ metrics are formed window-wise from $J_t$ and then aggregated across windows at the patient level. Unless noted otherwise, the reported summary is the patient-level median across valid windows.

== `spectral_radius_median`

The local spectral radius is

$ rho_t = max_i |lambda_(i,t)| $

and

$ "spectral_radius_median" = "median"_t (rho_t) $

Higher values indicate that the fitted local Jacobian has a larger dominant eigenvalue magnitude inside the exported `9D` coordinate system, meaning a stronger dominant local linear gain scale in at least one direction. This should not be read as a generic stability-threshold claim such as whether the underlying system crosses `rho > 1` in an abstract rescaled dynamical system.

#figure(
  image("figures/spectral_radius_median.png", width: 92%),
  caption: [Intuitive visualization of `spectral_radius_median`.]
) <fig-appendix-spectral-radius>

== `anisotropy_abs_eig_median`

The local anisotropy summary used in this article is the variance of the absolute eigenvalue magnitudes:

$ A_t = "var"_i(|lambda_(i,t)|) $

and

$ "anisotropy_abs_eig_median" = "median"_t (A_t) $

Higher values mean that the eigenvalue magnitudes are more unevenly distributed across directions. In other words, this summary reflects dispersion in $|lambda|$, not a condition number or a signed real-part imbalance.

#figure(
  image("figures/anistropy_abs_eig_median.png", width: 92%),
  caption: [Intuitive visualization of `anisotropy_abs_eig_median`.]
) <fig-appendix-anisotropy>

== `frobenius_norm_median`

The local Frobenius norm is

$ F_t = norm(J_t)_F = sqrt("tr"(J_t^top J_t)) $

and

$ "frobenius_norm_median" = "median"_t (F_t) $

Higher values indicate a larger overall local Jacobian magnitude when all matrix entries are taken together. In this manuscript it functions as a compact main-scale comparator for overall local linear deformation strength.

== `mdr_median`

When the time derivative of the local Jacobian is available, let $dot(J)_t$ denote the window-wise Jacobian derivative and define the exported ratio

$ D_t = frac(norm(dot(J)_t)_F, norm(J_t)_F + epsilon) $

with a small numerical stabilizer $epsilon$.

The article-facing handoff then reports

$ "mdr_median" = "median"_t (D_t) $

By this implementation, higher values mean that the Jacobian changes faster relative to its current magnitude. The manuscript keeps the frozen export name `MDR` for consistency with the audited bundle, but the quantity itself behaves like a normalized meta-plasticity ratio rather than an inverted rigidity score.

#figure(
  image("figures/mdr_median.png", width: 92%),
  caption: [Intuitive visualization of `mdr_median`.]
) <fig-appendix-mdr>

== `rotational_power_mean`

The local rotational-power summary first measures the mean absolute imaginary-part magnitude of the Jacobian eigenvalues:

$ R_t = frac(1, 9) sum_i |Im(lambda_(i,t))| $

The mean-aggregated article-facing version is then

$ "rotational_power_mean" = "mean"_t (R_t) $

Higher values indicate stronger complex-eigenvalue content and therefore stronger oscillatory or rotational local-linear structure.

#figure(
  image("figures/rotational_power_mean.png", width: 92%),
  caption: [Intuitive visualization of `rotational_power_mean`.]
) <fig-appendix-rotational-mean>

== `rotational_power_median`

The companion median-aggregated version uses the same per-window quantity

$ R_t = frac(1, 9) sum_i |Im(lambda_(i,t))| $

but aggregates it as

$ "rotational_power_median" = "median"_t (R_t) $

This keeps the same interpretation as `rotational_power_mean` while reducing sensitivity to a smaller number of high-rotation windows.

#figure(
  image("figures/rotational_power_median.png", width: 92%),
  caption: [Intuitive visualization of `rotational_power_median`.]
) <fig-appendix-rotational-median>

== Exploratory pooled mixed-signal trio

As a short exploratory appendix check, we also evaluated a compact pooled-only three-feature model that combined `rotational_power_mean` with the reachability summaries `tube_d_eff_median` and `persistence_log_eig_var_median`, without adding clinical or qEEG covariates. In repeated stratified cross-validation on the pooled `part1 + part2` cohort (`n = 281`; `141` `CPC 1`, `140` `CPC 5`), this trio reached `AUROC = 0.707` [`0.575`, `0.811`], `AUPRC = 0.673` [`0.554`, `0.820`], and Brier `= 0.214` [`0.185`, `0.254`]. The width of the `AUROC` interval should be read as high uncertainty rather than as evidence of a stable `~0.71` model.

Because this three-feature combination was motivated by post hoc subset scanning rather than by the frozen article hierarchy, it should be read only as an exploratory appendix-side complement to the main predictive ladder.

#bibliography("cardiac_arrest_comatose_references.bib")
