#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Regional Recovery-Linked Neural Geometry After Cardiac-Arrest Coma",
  short-title: "Regional Recovery-Linked Geometry",
  subtitle: "Channel-group reachability in the first 12 hours after EEG anchor",
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
    "regional EEG",
    "reachability",
    "NeuralManifoldDynamics",
    "recovery prognosis",
  ),
  article-type: "Research Article",
  abstract: [
    Early electroencephalography (EEG) after cardiac arrest is clinically informative, but global summaries alone may miss whether recovery-linked geometry is spatially concentrated in specific channel groups or distributed across the scalp. This manuscript extends the prior I-CARE reachability article into a regional analysis that keeps the same outcome contract, time window, and primary metric families while shifting the unit of geometric summarization from whole-record exports to predefined channel-group bundles. The planned regional groups are frontal, central, parietal-occipital, temporal, midline, left hemisphere, and right hemisphere. The primary article-facing reachability summaries remain effective dimensionality (`tube_d_eff_median`), temporal persistence (`persistence_kappa_median`, `persistence_log_eig_var_median`), and capture-related summaries (`tube_a_operator_norm_median`, `tube_capture_gate_median`). The central question is whether later `CPC 1` and later `CPC 5` differ not only in global reachability, but in where on the scalp that divergence is most visible during the first `12 h` after EEG-anchor. This draft is intentionally written as a results-ready manuscript shell while the regional NeuralManifoldDynamics export is being finalized; the same framework can then be re-run when the pending cohort expansion of approximately `140` additional extreme-outcome patients becomes available.
  ],
  author-summary: [
    The earlier coma manuscript showed that better later outcome was associated with broader effective reachable dimensionality, more persistent reachability structure, and weaker local capture in the first monitored EEG hours. This regional follow-up asks where that geometry lives. Using the same I-CARE cohort logic and the same article-facing metrics, we compare predefined EEG channel groups to test whether recovery-linked divergence is strongest in frontal, central, posterior, temporal, midline, or hemispheric summaries. The present draft locks the manuscript structure and analytic contract before the regional export is fully populated, so effect sizes, tables, and predictive comparisons can be inserted directly once the data handoff is complete.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Analysis Plan, Writing, and Editing.],
  funding-info: [Funding information will be inserted in the submission version.],
  data-availability: [This regional manuscript is anchored to the same I-CARE coma cohort used in `articles/comatose_ndt/`, with the regional EEG export rooted in `E:/Science_Datasets/physionet/processed/physionet_icare_2_1/neuralmanifolddynamics_physionet_icare_2_1_20260525_141608`. The implemented article-facing pipeline writes the primary regional summaries to `articles/CLINICAL/comatose_ndt_regional/results/mnps_summary_20260526_regional_primary12h/`, hourly rebinned summaries to `articles/CLINICAL/comatose_ndt_regional/results/mnps_summary_20260526_regional_hourly12h/`, and manuscript-ready tables/heatmaps to `articles/CLINICAL/comatose_ndt_regional/results/article_exports_20260526_regional_cpc15/` plus `articles/CLINICAL/comatose_ndt_regional/figures/20260526_regional_cpc15/`.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

= Introduction

Cardiac-arrest coma remains a strong test case for geometry-centered electroencephalography (EEG) analysis because the clinically relevant question is not only whether the EEG appears globally slow, suppressed, or discontinuous, but whether early neural dynamics retain enough short-horizon flexibility to support later recovery. Continuous EEG already contributes to multimodal neuroprognostication after cardiac arrest, and clinically interpretable signal exists in standardized visual patterns, continuity structure, reactivity, and quantitative EEG summaries.@herman2015consensus, @sandroni2021european, @nolan2025postresuscitation, @westhall2016standardized, @hirsch2021acns, @hofmeijer2015early, @ruijter2019early, @benghanem2022eeg

The previous global I-CARE reachability article asked whether later `CPC 1` and later `CPC 5` patients differ in local short-horizon geometry during the first `12 h` after EEG-anchor and found the clearest signal in a correlated family spanning effective dimensionality, persistence, and capture-related summaries. The next question is spatial rather than merely global: is the recovery-linked signal broadly distributed across the scalp, or does it localize more strongly to particular channel groups?

That question matters for both physiology and translational use. If the geometry signal is spatially diffuse, the global result may already capture most of what is clinically useful. If it is spatially structured, then regional reachability may reveal a more informative organization of preserved versus collapsed dynamics. A regional result would still not be a source-localization claim, but it could show whether the most article-relevant divergence is preferentially frontal, central, posterior, temporal, midline, or lateralized.

NeuralManifoldDynamics provides a natural contract for this extension.@langell2026_mndm Rather than training outcome-specific embeddings separately for each endpoint, the pipeline exports standardized geometric summaries that can be recomputed within predefined channel bundles. The aim is still prognostic and dynamical rather than metaphysical. Nothing in this manuscript is treated as a direct measure of consciousness, and nothing here is intended as a bedside-ready prediction tool.

#netn-box(title: [Core questions])[
  1. During the first `12 h` after EEG-anchor, do later `CPC 1` and later `CPC 5` patients differ in regional short-horizon reachability?

  2. If such differences exist, are they distributed across most channel groups or concentrated in a smaller regional subset?

  3. Do regional summaries improve internal prediction beyond the clinical + qEEG baseline more than the previously reported global geometry layer alone?
]

= Cohort and regional analysis design

The regional manuscript is designed as a direct extension of the global I-CARE coma article.@amorim2023icare The primary outcome contrast remains later Cerebral Performance Category (CPC) `1` versus later `CPC 5`.@rittenberger2011cpc The primary time window remains the first `12 h` after EEG-anchor, and the primary unit of inference remains the patient rather than the individual window.

The current manuscript is written before the regional export has been fully materialized into article-facing result tables. Accordingly, this draft locks the scientific framing, section structure, channel-group contract, and primary inferential targets now, so that the finished export can be inserted without rewriting the paper. This is useful both for the present discovery cohort and for the planned rerun after the pending cohort expansion of approximately `140` additional extreme-outcome patients.

The regional groups are defined from the confirmed I-CARE channel headers currently available in the export contract.

#figure(
  kind: table,
  table(
    columns: (1.35fr, 2.65fr),
    align: left,
    inset: 5pt,
    table.header([*Group*], [*Channels*]),
    [`frontal`], [`Fp1`, `Fp2`, `Fpz`, `F3`, `F4`, `F7`, `F8`, `Fz`],
    [`central`], [`C3`, `C4`, `Cz`],
    [`parietal_occipital`], [`P3`, `P4`, `Pz`, `O1`, `O2`],
    [`temporal`], [`T3`, `T4`, `T5`, `T6`],
    [`midline`], [`Fpz`, `Fz`, `Cz`, `Pz`],
    [`left_hemisphere`], [`Fp1`, `F3`, `F7`, `C3`, `P3`, `O1`, `T3`, `T5`],
    [`right_hemisphere`], [`Fp2`, `F4`, `F8`, `C4`, `P4`, `O2`, `T4`, `T6`],
  ),
  caption: [Table 1: Predefined regional EEG channel groups for the regional coma manuscript. These are scalp-level channel bundles, not source-localized cortical parcels.]
) <tab-regions>

The group definitions intentionally mix anatomically adjacent summaries (`frontal`, `central`, `parietal_occipital`, `temporal`) with organizational summaries (`midline`, `left_hemisphere`, `right_hemisphere`). This allows the manuscript to ask three different regional questions at once: anterior versus posterior weighting, temporal versus non-temporal involvement, and lateralized versus midline organization.

= Reachability framework

The regional manuscript keeps the same measurement logic as the global article. Under the local stochastic reachability model,@langell2026_reachability each window has a short-horizon reachable cloud whose geometry can be summarized by size, effective dimensionality, persistence, and capture-related quantities. The main interpretive families therefore remain unchanged:

1. *Capacity / dimensionality:* how many effectively independent directions the reachable cloud spans.
2. *Persistence:* how stably reachable structure remains open across neighboring windows.
3. *Capture / contraction:* how strongly local dynamics appear contracted, canalized, or locally trapped.

That continuity with the earlier article is deliberate. The regional study is not meant to introduce a new metric family; it is meant to test where the existing reachability signal is strongest.

#figure(
  kind: table,
  table(
    columns: (1.4fr, 2.3fr, 2.5fr),
    align: left,
    inset: 4pt,
    table.header([*Family*], [*Primary article-facing metrics*], [*Interpretation*]),
    [Capacity / dimensionality], [`tube_d_eff_median`], [Broader reachable covariance spans more effective directions in the local future set.],
    [Persistence], [`persistence_kappa_median`, `persistence_log_eig_var_median`], [Reachability structure remains more stable across neighboring windows rather than fluctuating erratically.],
    [Capture / contraction], [`tube_a_operator_norm_median`, `tube_capture_gate_median`], [Local dynamics appear less versus more tightly contracted or capture-dominated.],
  ),
  caption: [Table 2: Primary regional article-facing metrics, inherited from the global coma manuscript.]
) <tab-metrics>

Secondary contextual metrics may again include `tube_log_det_median`, `q_ratio_h4_median`, and selected classical MNPS or Jacobian summaries where available, but the regional paper should remain anchored to the five article-facing metrics above unless the export clearly shows a different ranked family.

= Methods

== Time anchoring and outcome definition

The primary analysis remains anchored to EEG monitoring start because this is the most reliable timing anchor in the current I-CARE export. The primary inferential window is `0-12 h` after EEG-anchor, and the main contrast is later `CPC 1` versus later `CPC 5`. As in the global manuscript, this extreme-outcome design sharpens separation but must be interpreted conservatively because `CPC 5` intersects with death and therefore with real clinical pathways, including possible withdrawal-of-life-sustaining therapy effects.@rajajee2023neuroprognostication, @nolan2025postresuscitation

== Regional summarization contract

For each predefined channel group in @tab-regions, the regional export should compute the same family of reachability summaries already used in the global article. The intended manuscript logic is therefore:

1. compute group-specific geometric summaries within each channel bundle,
2. aggregate those summaries to patient level across the first `12 h`,
3. compare later `CPC 1` versus later `CPC 5` within each region,
4. inspect hourly `0-1 h` through `11-12 h` organization,
5. and finally test whether a regional geometry layer improves prediction beyond clinical + qEEG baselines.

This design keeps the measurement family fixed while changing only the spatial support of the summary.

The implemented regional wrapper now follows that contract directly. `src/icare_regional_mnps_summary_analysis.py` reuses the coma time-bin logic and remaps the established `part1` timing metadata onto the new regional EEG bundle, `src/run_regional_article_pipeline.py` orchestrates the primary `0-12 h` pass plus hourly rebinning, and `src/build_regional_article_exports.py` converts the patient/time-bin metric files into article-facing regional ranking, laterality, hourly, and MNJ tables. The small QC layer also records the locked group/feature contract in `regional_feature_inventory.csv` and `regional_contract_summary.json`.

For the regional MNJ layer, the main article hierarchy remains `spectral_radius_median`, `anisotropy_abs_eig_median`, `mdr_median`, `rotational_power_mean`, `rotational_power_median`, and `frobenius_norm_median`. The current regional export exposes the Jacobian tensor itself for every channel group but not a dedicated regional `jacobian_dot` surface; the pipeline therefore computes a centered finite-difference fallback for the regional Jacobian derivative when populating the MDR field, while keeping the exported metric name and interpretation aligned with the 9D Jacobian manuscript.

== Primary inferential targets

The manuscript has three primary inferential targets.

First, *within-region outcome separation*: for each regional group, do the five article-facing metrics show directional separation between later `CPC 1` and later `CPC 5`?

Second, *between-region ranking*: which regional groups show the largest and most coherent effect-size pattern across the five article-facing metrics?

Third, *temporal organization*: does the strongest regional separation emerge immediately, or does it cluster in the early-to-mid monitored interval as in the global article?

The regional paper should avoid overclaiming exact lobar localization. The operational claim is about channel-group summaries on the scalp, not about direct cortical source reconstruction.

== Statistical summary

The planned statistical reporting mirrors the global manuscript. For each metric within each region, the patient-level contrast table should report robust descriptive summaries, Mann-Whitney U tests, Welch tests, Cohen's `d`, and Cliff's delta. Where the candidate pool is large, BH-FDR `q` values should be reported within the regional feature pool used for article-facing ranking.

Because the same subjects contribute to multiple overlapping channel groups, multiplicity should be handled transparently but interpreted conservatively. The regional article is best read as a structured outcome-contrast study with multiple correlated views, not as seven independent localization experiments.

== Hourly analyses

As in the earlier manuscript, hourly `0-1 h` through `11-12 h` bins should be treated as exploratory temporal maps rather than as a fully corrected confirmatory endpoint family. The main purpose of the hourly analyses is localization in time: do regional geometry differences appear only transiently, or do they remain coherent across several monitored hours?

== Predictive comparison

The planned model comparison should again use four tiers:

1. clinical-only,
2. qEEG-only,
3. clinical + qEEG,
4. clinical + qEEG + regional geometry.

If the export supports it, a fifth comparison is also worthwhile:

5. clinical + qEEG + global geometry + regional geometry.

That fifth tier would test whether regional summaries add information on top of the already established global five-feature reachability layer rather than merely replicating it. Any such model comparison should still be labeled as internal post-selection evidence unless the regional panel is frozen before model evaluation or validated in the forthcoming expanded cohort.

== Planned cohort extension

One reason to lock this manuscript structure now is that the same regional pipeline can later be rerun in the planned cohort expansion of approximately `140` additional extreme-outcome patients. That next dataset will matter in two ways: it can stabilize regional ranking and it can test whether any region-specific signature survives beyond the current discovery-sized sample. The present manuscript should therefore distinguish clearly between:

1. current discovery-cohort regional effects,
2. later internal replication in the enlarged cohort,
3. and any eventual claim of externally frozen biomarker validity.

= Results

#netn-box(title: [Draft status])[
  The primary `0-12 h` regional summaries were recovered from the existing adapter outputs, rebinned hourly, and exported into `results/article_exports_20260526_regional_cpc15/` with companion figures in `figures/20260526_regional_cpc15/`. Tables 3-6 below are now populated from those frozen exports. Table 7 remains a downstream target because the repeated-CV predictive comparison has not yet been rerun for the regional feature panel.
]

== Regional ranking in the `0-12 h` window

The first results section should answer a simple question: which regional groups carry the clearest patient-level `CPC 1` versus `CPC 5` separation across the shared reachability family?

The most useful article-facing table will likely be a compact region-by-metric ranking that foregrounds medians and effect sizes rather than only p-values. A good final version of this section should emphasize whether the signal is:

1. broad across most channel groups,
2. concentrated in one or two regional families,
3. or split into distinct spatial sub-patterns for capacity, persistence, and capture.

#figure(
  kind: table,
  table(
    columns: (1.5fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Region*],
      [*`d_eff`*],
      [*Pers. kappa*],
      [*Pers. log eig var*],
      [*A-op norm*],
      [*Capture gate*],
    ),
    [`frontal`], [`+0.60 (q=0.002)`], [`+0.24 (q=1.84e-05)`], [`+0.24 (q=1.73e-05)`], [`-0.82 (q=9.98e-06)`], [`-0.61 (q=0.004)`],
    [`central`], [`+0.62 (q=0.002)`], [`+0.24 (q=8.64e-05)`], [`+0.24 (q=2.72e-05)`], [`-0.78 (q=2.09e-05)`], [`-0.66 (q=0.002)`],
    [`parietal_occipital`], [`+0.71 (q=3.13e-04)`], [`+0.17 (q=1.23e-05)`], [`+0.17 (q=6.64e-06)`], [`-0.83 (q=7.95e-06)`], [`-0.63 (q=0.003)`],
    [`temporal`], [`+0.61 (q=7.23e-04)`], [`+0.17 (q=1.66e-04)`], [`+0.17 (q=9.49e-05)`], [`-0.67 (q=4.74e-05)`], [`-0.52 (q=0.013)`],
    [`midline`], [`+0.66 (q=4.49e-04)`], [`+0.17 (q=2.88e-05)`], [`+0.17 (q=1.73e-05)`], [`-0.75 (q=8.16e-05)`], [`-0.59 (q=0.005)`],
    [`left_hemisphere`], [`+0.90 (q=2.63e-06)`], [`+0.24 (q=5.90e-07)`], [`+0.24 (q=5.68e-07)`], [`-0.86 (q=3.36e-07)`], [`-0.67 (q=8.61e-04)`],
    [`right_hemisphere`], [`+0.88 (q=6.64e-06)`], [`+0.17 (q=2.63e-06)`], [`+0.17 (q=1.61e-06)`], [`-0.78 (q=1.61e-06)`], [`-0.58 (q=0.003)`],
  ),
  caption: [Table 3: Compact regional ranking table for the five article-facing reachability metrics in the `0-12 h` patient-level CPC1-vs-CPC5 contrast. Populated directly from `regional_reachability_ranking_table.csv` using the article-cell strings exported by `build_regional_article_exports.py`.]
) <tab-regional-ranking>

The frozen primary export shows a coherent regionally distributed pattern rather than a sharply localized one. `left_hemisphere` and `right_hemisphere` carry the strongest pooled reachability separation, with `central`, `parietal_occipital`, and `frontal` close behind, while all seven regions preserve the same high-level directional structure: higher `tube_d_eff_median` and persistence in `CPC 1`, but lower `tube_a_operator_norm_median` and `tube_capture_gate_median`. `tube_d_eff_median` therefore remains the clearest positive capacity-like regional signal, but the largest absolute cross-region separation is actually the contraction/capture-like `A-op norm` family.

== Hemispheric and midline organization

The `left_hemisphere`, `right_hemisphere`, and `midline` groups support a second question that the global article could not address directly: is the geometry signal mainly bilateral and diffuse, or does it show a preferential organization along lateralized or midline summaries?

This section should not force a laterality claim if the data do not support one. A null or near-symmetric pattern would still be informative because it would argue that the recovery-linked signal is more global or bilaterally organized than hemisphere-specific. Conversely, a consistent asymmetry across persistence, dimensionality, and capture would be noteworthy, especially if it survives in the enlarged cohort.

#figure(
  kind: table,
  table(
    columns: (1.7fr, 1.0fr, 1.0fr, 1.0fr, 1.0fr),
    align: left,
    inset: 4pt,
    table.header([*Comparison*], [*`d_eff`*], [*Persistence*], [*Capture*], [*Interpretive note*]),
    [`Left vs right overall pattern`], [`L +0.90 / R +0.88`], [`L +0.24 / R +0.17`], [`L -0.77 / R -0.68`], [`largely bilateral pattern`],
    [`Midline vs bilateral pattern`], [`M +0.66 / Bil +0.89`], [`M +0.17 / Bil +0.20`], [`M -0.67 / Bil -0.72`], [`midline similar to bilateral`],
  ),
  caption: [Table 4: Hemispheric and midline summary table populated from `regional_lateralization_summary.csv`, which summarizes left-versus-right and midline-versus-bilateral effect patterns across the frozen reachability families.]
) <tab-lateralization>

The hemispheric summary supports a bilateral rather than lateralized interpretation. Left and right hemisphere effects are nearly matched on `d_eff` and persistence, and the midline summary remains broadly similar to the bilateral average rather than separating into its own dominant motif.

== Hourly organization of the regional signal

The hourly regional question is whether the reachability separation is confined to a single early spike or instead remains organized across the first monitored `12 h`, and whether the leading region changes across metric families as the window unfolds.

The core visualization is therefore a region-by-hour heatmap for one summary per metric family, together with compact article-facing tables that identify which regional groups lead each hour and which metric families persist latest.

#figure(
  kind: table,
  table(
    columns: (1.4fr, 1fr, 1fr, 1fr, 1fr),
    align: left,
    inset: 4pt,
    table.header([*Region*], [*Earliest coherent bin*], [*Peak interval*], [*Late persistence*], [*Notes*]),
    [`frontal`], [`1_2h`], [`1_2h`], [`11_12h`], [`Pers. kappa with same-direction support`],
    [`central`], [`1_2h`], [`3_4h`], [`11_12h`], [`Pers. kappa with same-direction support`],
    [`parietal_occipital`], [`0_1h`], [`3_4h`], [`11_12h`], [`A-op norm`],
    [`temporal`], [`0_1h`], [`1_2h`], [`11_12h`], [`A-op norm`],
    [`midline`], [`0_1h`], [`2_3h`], [`11_12h`], [`Pers. kappa with same-direction support`],
    [`left_hemisphere`], [`0_1h`], [`1_2h`], [`11_12h`], [`Pers. kappa with same-direction support`],
    [`right_hemisphere`], [`0_1h`], [`5_6h`], [`11_12h`], [`d_eff with same-direction support`],
  ),
  caption: [Table 5: Summary of hourly organization across regions populated from `regional_hourly_summary.csv`; the companion effect-size heatmaps live in `figures/20260526_regional_cpc15/regional_hourly_reachability_panels.svg`.]
) <tab-hourly-summary>

The hourly export also argues against a singular first-hour-only spike. Most regions first show coherent separation in `0-1 h` or `1-2 h`, peak between `1-2 h` and `5-6 h`, and retain late same-direction signal through `11-12 h`. That pattern is consistent with an early-to-mid divergence that remains observable across the monitored window rather than collapsing immediately after the first hour.

#figure(
  kind: table,
  table(
    columns: (0.9fr, 1.35fr, 1.5fr, 1.35fr, 1.35fr),
    align: left,
    inset: 4pt,
    table.header([*Hour*], [*`d_eff` lead*], [*Persistence lead*], [*A-op norm lead*], [*Capture gate lead*]),
    [`0_1h`], [`left_hemisphere +0.74 (q=1.93e-04)`], [`left_hemisphere +0.18 (q=1.93e-04)`], [`left_hemisphere -0.53 (q=1.93e-04)`], [`left_hemisphere -0.59 (q=0.0035)`],
    [`1_2h`], [`left_hemisphere +0.93 (q=1.77e-05)`], [`midline +0.87 (q=2.62e-05)`], [`central -0.58 (q=2.43e-05)`], [`central -0.72 (q=2.34e-04)`],
    [`2_3h`], [`right_hemisphere +0.95 (q=1.03e-05)`], [`left_hemisphere +0.99 (q=7.11e-06)`], [`left_hemisphere -0.86 (q=1.21e-05)`], [`left_hemisphere -0.72 (q=9.75e-04)`],
    [`3_4h`], [`right_hemisphere +0.86 (q=8.01e-05)`], [`left_hemisphere +1.00 (q=1.85e-05)`], [`right_hemisphere -0.83 (q=1.17e-04)`], [`right_hemisphere -0.64 (q=0.0032)`],
    [`4_5h`], [`right_hemisphere +0.84 (q=2.75e-04)`], [`left_hemisphere +0.80 (q=2.75e-04)`], [`frontal -0.72 (q=3.18e-04)`], [`frontal -0.58 (q=0.0076)`],
    [`5_6h`], [`right_hemisphere +0.96 (q=9.24e-06)`], [`left_hemisphere +0.88 (q=2.05e-05)`], [`right_hemisphere -0.77 (q=3.19e-05)`], [`parietal_occipital -0.57 (q=0.0118)`],
    [`6_7h`], [`right_hemisphere +0.80 (q=1.10e-04)`], [`right_hemisphere +0.93 (q=1.96e-05)`], [`left_hemisphere -0.72 (q=4.41e-05)`], [`central -0.58 (q=0.0052)`],
    [`7_8h`], [`left_hemisphere +0.79 (q=4.29e-04)`], [`right_hemisphere +0.91 (q=9.09e-05)`], [`parietal_occipital -0.73 (q=6.26e-04)`], [`central -0.54 (q=0.0287)`],
    [`8_9h`], [`left_hemisphere +0.81 (q=5.59e-04)`], [`left_hemisphere +0.81 (q=4.40e-04)`], [`parietal_occipital -0.79 (q=2.87e-04)`], [`central -0.57 (q=0.0155)`],
    [`9_10h`], [`right_hemisphere +0.75 (q=0.0013)`], [`left_hemisphere +0.80 (q=7.25e-04)`], [`parietal_occipital -0.73 (q=7.34e-04)`], [`left_hemisphere -0.46 (q=0.0478)`],
    [`10_11h`], [`left_hemisphere +0.61 (q=0.0231)`], [`left_hemisphere +0.57 (q=0.0231)`], [`parietal_occipital -0.64 (q=0.0264)`], [`right_hemisphere -0.43 (q=0.136)`],
    [`11_12h`], [`right_hemisphere +0.83 (q=8.32e-04)`], [`left_hemisphere +0.79 (q=8.32e-04)`], [`parietal_occipital -0.66 (q=0.0092)`], [`right_hemisphere -0.32 (q=0.282)`],
  ),
  caption: [Table 5a: Hour-by-hour regional leaders for the main reachability families. Each cell reports the strongest regional Cohen's `d` for that hour within the named family. Positive values indicate higher `CPC 1`; negative values indicate higher `CPC 5`.]
) <tab-hourly-leads>

Two features stand out in this hourly leader table. First, the early and mid-window positive separation is largely carried by `left_hemisphere` and `right_hemisphere`, with left-weighted peaks in the `1-4 h` persistence block and a right-weighted `d_eff` crest around `5_6h`. Second, the contraction/capture-like families shift posteriorly with time: `tube_a_operator_norm_median` is led by hemispheric or frontal groups earlier, but by `parietal_occipital` from `7_8h` through `11_12h`. `tube_capture_gate_median` also weakens late, becoming only borderline by `9_10h` and no longer clearly significant in the last two hours.

#figure(
  kind: table,
  table(
    columns: (1.45fr, 1.15fr, 1.15fr, 1.15fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*First significant hour*], [*Peak hour*], [*Latest significant hour*]),
    [`tube_d_eff_median`], [`0_1h left_hemisphere (+0.74)`], [`5_6h right_hemisphere (+0.96)`], [`11_12h parietal_occipital (+0.74)`],
    [`persistence_kappa_median`], [`0_1h central (+0.18)`], [`2_3h left_hemisphere (+0.98)`], [`11_12h midline (+0.58)`],
    [`persistence_log_eig_var_median`], [`0_1h central (+0.18)`], [`3_4h left_hemisphere (+1.00)`], [`11_12h midline (+0.54)`],
    [`tube_a_operator_norm_median`], [`0_1h central (-0.47)`], [`2_3h left_hemisphere (-0.86)`], [`11_12h left_hemisphere (-0.59)`],
    [`tube_capture_gate_median`], [`0_1h central (-0.54)`], [`2_3h left_hemisphere (-0.72)`], [`9_10h left_hemisphere (-0.46)`],
  ),
  caption: [Table 5b: First, strongest, and latest significant hourly regional findings for each article-facing reachability metric. These rows summarize the exploratory hourly contrast map while keeping the metric families separated.]
) <tab-hourly-metric-timeline>

Viewed metric-by-metric, the hourly pattern is not uniform. The `d_eff` family is already present in the first hour but peaks later at `5_6h` in `right_hemisphere`; the persistence pair peak slightly earlier, in the `2-4 h` interval, with especially strong `left_hemisphere` effects; `tube_a_operator_norm_median` is strongest at `2_3h` and remains significant through `11_12h`; and `tube_capture_gate_median` is the only main family that clearly drops out before the final two hourly bins.

== Regional MNJ hierarchy

The regional article should report its Jacobian results in a clearly separated layer rather than blending them into the reachability ranking table. This keeps the distinction between local reachable geometry and local linear dynamics explicit while preserving the revised 9D Jacobian hierarchy that motivated the regional follow-up.

#figure(
  kind: table,
  table(
    columns: (1.6fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Region*],
      [*Spectral radius*],
      [*Anisotropy*],
      [*MDR*],
      [*Rot. mean*],
      [*Rot. median*],
      [*Frobenius*],
    ),
    [`frontal`], [`-0.68 (q=2.36e-04)`], [`-0.74 (q=2.36e-04)`], [`-0.20 (q=0.004)`], [`-0.56 (q=3.03e-04)`], [`-0.01 (q=0.510)`], [`-0.78 (q=2.36e-04)`],
    [`central`], [`-0.66 (q=2.36e-04)`], [`-0.73 (q=2.36e-04)`], [`-0.24 (q=0.008)`], [`-0.53 (q=0.003)`], [`+0.11 (q=0.104)`], [`-0.36 (q=2.36e-04)`],
    [`parietal_occipital`], [`-0.68 (q=2.36e-04)`], [`-0.74 (q=2.36e-04)`], [`-0.26 (q=0.001)`], [`-0.67 (q=3.97e-04)`], [`-0.06 (q=0.829)`], [`-0.77 (q=3.11e-04)`],
    [`temporal`], [`-0.17 (q=2.85e-04)`], [`-0.17 (q=3.03e-04)`], [`-0.23 (q=0.001)`], [`-0.50 (q=0.004)`], [`+0.07 (q=0.600)`], [`-0.17 (q=2.85e-04)`],
    [`midline`], [`-0.65 (q=2.53e-04)`], [`-0.70 (q=2.36e-04)`], [`-0.26 (q=0.002)`], [`-0.51 (q=0.003)`], [`+0.02 (q=0.356)`], [`-0.73 (q=2.85e-04)`],
    [`left_hemisphere`], [`-0.69 (q=9.94e-04)`], [`-0.72 (q=4.81e-04)`], [`-0.20 (q=0.019)`], [`-0.42 (q=0.002)`], [`-0.09 (q=0.758)`], [`-0.77 (q=2.36e-04)`],
    [`right_hemisphere`], [`-0.62 (q=6.22e-04)`], [`-0.66 (q=0.001)`], [`-0.17 (q=0.033)`], [`-0.52 (q=0.001)`], [`-0.05 (q=0.678)`], [`-0.71 (q=2.36e-04)`],
  ),
  caption: [Table 6: Regional MNJ summary table for the revised Jacobian hierarchy, populated directly from `regional_mnj_primary_table.csv` using the exported article-cell strings for `spectral_radius_median`, `anisotropy_abs_eig_median`, `mdr_median`, `rotational_power_mean`, `rotational_power_median`, and `frobenius_norm_median`.]
) <tab-regional-mnj>

The regional MNJ hierarchy is related but not identical to the reachability ranking. `parietal_occipital` and `frontal` are the strongest pooled MNJ groups, followed by `left_hemisphere` and `midline`, with the dominant MNJ metrics coming from `spectral_radius_median`, `anisotropy_abs_eig_median`, and `frobenius_norm_median`. `rotational_power_median` is weak throughout and should not anchor the article's Jacobian interpretation.

== Incremental validity beyond clinical + qEEG baselines

The regional manuscript should retain the bounded complementarity claim used in the global paper. The relevant question is not whether regional geometry replaces standard clinical EEG reasoning, but whether it adds useful information beyond the existing clinical + qEEG baseline and, if tested, beyond the global geometry layer.

#figure(
  kind: table,
  table(
    columns: (2.0fr, 1.0fr, 1.0fr, 1.0fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*Model*], [*AUROC*], [*AUPRC*], [*Brier*], [*Delta AUC*]),
    [`Clinical`], [`TBD`], [`TBD`], [`TBD`], [`TBD`],
    [`qEEG`], [`TBD`], [`TBD`], [`TBD`], [`TBD`],
    [`Clinical + qEEG`], [`TBD`], [`TBD`], [`TBD`], [`TBD`],
    [`Clinical + qEEG + regional geometry`], [`TBD`], [`TBD`], [`TBD`], [`TBD`],
    [`Clinical + qEEG + global + regional geometry`], [`TBD`], [`TBD`], [`TBD`], [`TBD`],
  ),
  caption: [Table 7: Planned repeated-CV model comparison. This table remains a downstream pipeline target; once a frozen regional feature panel is selected, its source rows should live beside the other article exports under `results/article_exports_20260526_regional_cpc15/`.]
) <tab-prediction>

The final interpretation here should remain strict: if the regional layer improves internal performance, that is evidence of complementarity inside the analyzed cohort, not of a frozen deployable biomarker panel. The forthcoming enlarged cohort is the natural next test for any regional feature set selected here.

= Discussion

The regional manuscript is designed to answer a narrower and deeper follow-up question to the original global article. The prior work established that early reachability structure differs between later `CPC 1` and later `CPC 5` patients. The regional extension asks where that structure is most visible when the same geometric summaries are recomputed within predefined EEG channel groups.

Several outcomes would each be scientifically useful.

The exported tables favor the first of those outcomes. Most regional groups recapitulate the same directional reachability pattern, which points to a broadly distributed scalp-level recovery signal rather than a single sharply dominant locus. The strongest pooled reachability effects sit in the bilateral hemisphere summaries, but the frontal, central, and parietal-occipital groups remain close enough that a distributed interpretation is more defensible than a narrowly localized one.

The MNJ layer is also clearly non-null, but it tilts somewhat more toward `parietal_occipital` and `frontal` dominance than the reachability layer. That separation is useful because it suggests that local linear dynamics and short-horizon reachability are related yet not interchangeable regional summaries.

The predictive comparison remains the main unfinished downstream step. Until Table 7 is populated, the regional manuscript can support a spatial-organization claim and an internal reachability/MNJ ranking claim, but not yet a completed incremental-validity claim beyond the clinical + qEEG baseline.

= Limitations

This regional manuscript inherits all major limitations from the global coma article and adds several new ones.

1. The cohort is observational and clinically heterogeneous rather than a fully harmonized prospective benchmark.
2. The extreme-outcome endpoint sharpens separation but makes interpretation delicate because `CPC 5` intersects with death, systemic illness severity, treatment limitations, and possibly withdrawal-of-life-sustaining therapy effects.@rajajee2023neuroprognostication
3. The primary window remains the first `12 h` after EEG-anchor, not necessarily the first `12 h` after ROSC.
4. The regional groups are scalp-level channel bundles, not source-localized cortical parcels.
5. Several channel groups overlap by design, especially `midline` with anterior and posterior groups, so region-level effects are correlated rather than independent.
6. The same five article-facing metrics may not rank identically in every region; if the export reveals large between-region differences, the manuscript must distinguish a frozen cross-region metric family from exploratory within-region ranking.
7. Any regional predictive model selected and evaluated within the same cohort remains an internal post-selection analysis rather than external validation.
8. The reachability and MNJ export handoff is now complete, but the regional predictive comparison is still a downstream step. The manuscript therefore already supports a frozen descriptive interpretation, while any incremental-validity claim remains pending the repeated-CV model rerun.

= Conclusion

This draft defines a regional follow-up manuscript to the global I-CARE reachability article. It preserves the same outcome contrast, the same `0-12 h` time contract, and the same primary reachability metrics while shifting the main scientific question from "does early recovery-linked geometry exist?" to "where is that geometry most visible across the scalp?" Once the regional export is complete, this manuscript can be populated directly with patient-level regional contrasts, hourly organization maps, and predictive comparisons. The forthcoming cohort expansion of approximately `140` additional extreme-outcome patients then provides the natural next step for testing whether any regional signature is stable enough to survive beyond the current discovery setting.

= Appendix: Compact Metric Definitions

This appendix briefly restates the five primary reachability summaries carried over from the global coma article so that the regional manuscript remains readable as a stand-alone paper.

== Local reachability covariance

The local short-horizon model is written as

$ x_(t + 1) = A_t x_t + b_t + epsilon_t, quad epsilon_t ~ (0, Q_t) $

with propagated covariance

$ Sigma_t^((0)) = sigma_0^2 I, quad Sigma_t^((h + 1)) = A_t Sigma_t^((h)) A_t^top + Q_t $

where $A_t$ is the local linear dynamics operator and $Q_t$ is the innovation covariance. The summaries below are computed from the eigenstructure of $Sigma_t^((h))$ and then aggregated across windows to the patient level.

== `tube_d_eff_median`

Let $lambda_1, dots, lambda_d$ be the eigenvalues of a horizon-specific reachable covariance $Sigma_t^((h))$. The effective dimensionality is

$ d_("eff"),t^((h)) = frac((sum_i lambda_i)^2, sum_i lambda_i^2) $

Higher values indicate that the reachable cloud is spread across more effectively independent directions.

== `persistence_kappa_median`

The tube anisotropy summary is based on the eigenvalue condition number

$ kappa_t^((h)) = frac(lambda_(max)(Sigma_t^((h))), lambda_(min)(Sigma_t^((h))) + epsilon) $

The persistence transform measures local temporal stability of that summary over neighboring windows:

$ P(z_t) = frac(1, "std"(z_(t-w:t+w)) + epsilon) $

applied here to the tube-level $kappa$ series. Higher values indicate more stable local anisotropy structure over time.

== `persistence_log_eig_var_median`

For each horizon, the spread of log-eigenvalues is summarized as

$ V_t^((h)) = "var"(log(lambda_i + epsilon)) $

and converted into the same persistence transform

$ P(V_t) = frac(1, "std"(V_(t-w:t+w)) + epsilon) $

so that higher values indicate more stable retained eigenspectrum structure across neighboring windows.

== `tube_a_operator_norm_median`

The local dynamics matrix $A_t$ has operator norm

$ norm(A_t)_2 = max_(norm(v)_2 = 1) norm(A_t v)_2 $

which summarizes the strongest local amplification or contraction scale implied by the fitted linear map. In the coma manuscripts, this serves as a compact contraction / capture summary.

== `tube_capture_gate_median`

The innovation-versus-transport balance at horizon `h` is summarized by

$ q_t^((h)) = frac("tr"(Sigma_t^((h)) - A_t Sigma_t^((h - 1)) A_t^top), "tr"(Sigma_t^((h)))) $

and combined with the operator norm to form the capture gate

$ G_t = (1 - q_t^((4))) log(1 + norm(A_t)_2) $

Higher values indicate a stronger combination of transport-dominated evolution and locally strong linear dynamics, interpreted here as stronger short-horizon capture.

= Appendix: Exact Hourly Regional Effect Tables

The tables below report the exact hourly regional Cohen's `d` values for each article-facing reachability metric. Positive values indicate higher `CPC 1`; negative values indicate higher `CPC 5`. An asterisk denotes hourly BH-FDR `q < 0.05` within that metric.

#figure(
  kind: table,
  text(size: 6.4pt)[
    table(
      columns: (1.7fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.78fr),
      align: left,
      inset: 2.5pt,
      table.header([*Region*], [*0-1*], [*1-2*], [*2-3*], [*3-4*], [*4-5*], [*5-6*], [*6-7*], [*7-8*], [*8-9*], [*9-10*], [*10-11*], [*11-12*]),
      [`frontal`], [`+0.347`], [`+0.657*`], [`+0.538*`], [`+0.603*`], [`+0.572*`], [`+0.500*`], [`+0.377*`], [`+0.541*`], [`+0.652*`], [`+0.597*`], [`+0.481`], [`+0.588*`],
      [`central`], [`+0.362`], [`+0.699*`], [`+0.710*`], [`+0.740*`], [`+0.656*`], [`+0.627*`], [`+0.509*`], [`+0.607*`], [`+0.453`], [`+0.504*`], [`+0.201`], [`+0.525*`],
      [`parietal_occipital`], [`+0.439*`], [`+0.633*`], [`+0.654*`], [`+0.770*`], [`+0.668*`], [`+0.673*`], [`+0.528*`], [`+0.632*`], [`+0.729*`], [`+0.731*`], [`+0.476`], [`+0.742*`],
      [`temporal`], [`+0.443*`], [`+0.665*`], [`+0.655*`], [`+0.619*`], [`+0.612*`], [`+0.623*`], [`+0.467*`], [`+0.569*`], [`+0.570*`], [`+0.656*`], [`+0.333`], [`+0.615*`],
      [`midline`], [`+0.437*`], [`+0.677*`], [`+0.745*`], [`+0.709*`], [`+0.630*`], [`+0.590*`], [`+0.518*`], [`+0.560*`], [`+0.528*`], [`+0.660*`], [`+0.337`], [`+0.652*`],
      [`left_hemisphere`], [`+0.744*`], [`+0.934*`], [`+0.899*`], [`+0.809*`], [`+0.748*`], [`+0.898*`], [`+0.740*`], [`+0.794*`], [`+0.809*`], [`+0.750*`], [`+0.615*`], [`+0.801*`],
      [`right_hemisphere`], [`+0.614*`], [`+0.909*`], [`+0.946*`], [`+0.859*`], [`+0.839*`], [`+0.958*`], [`+0.802*`], [`+0.758*`], [`+0.772*`], [`+0.750*`], [`+0.453`], [`+0.833*`],
    )
  ],
  caption: [Appendix Table A1: Exact hourly regional effect sizes for `tube_d_eff_median`.]
) <tab-appendix-hourly-deff>

#figure(
  kind: table,
  text(size: 6.4pt)[
    table(
      columns: (1.7fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.78fr),
      align: left,
      inset: 2.5pt,
      table.header([*Region*], [*0-1*], [*1-2*], [*2-3*], [*3-4*], [*4-5*], [*5-6*], [*6-7*], [*7-8*], [*8-9*], [*9-10*], [*10-11*], [*11-12*]),
      [`frontal`], [`+0.181*`], [`+0.761*`], [`+0.534*`], [`+0.658*`], [`+0.556*`], [`+0.671*`], [`+0.604*`], [`+0.587*`], [`+0.704*`], [`+0.650*`], [`+0.449*`], [`+0.637*`],
      [`central`], [`+0.181*`], [`+0.819*`], [`+0.861*`], [`+0.726*`], [`+0.623*`], [`+0.792*`], [`+0.642*`], [`+0.726*`], [`+0.481*`], [`+0.521*`], [`+0.152`], [`+0.499*`],
      [`parietal_occipital`], [`+0.170*`], [`+0.737*`], [`+0.744*`], [`+0.685*`], [`+0.672*`], [`+0.646*`], [`+0.632*`], [`+0.708*`], [`+0.646*`], [`+0.680*`], [`+0.402`], [`+0.555*`],
      [`temporal`], [`+0.170*`], [`+0.660*`], [`+0.501*`], [`+0.642*`], [`+0.482*`], [`+0.593*`], [`+0.626*`], [`+0.587*`], [`+0.497*`], [`+0.599*`], [`+0.231`], [`+0.566*`],
      [`midline`], [`+0.170*`], [`+0.849*`], [`+0.864*`], [`+0.820*`], [`+0.653*`], [`+0.690*`], [`+0.597*`], [`+0.559*`], [`+0.457*`], [`+0.721*`], [`+0.340`], [`+0.580*`],
      [`left_hemisphere`], [`+0.181*`], [`+0.787*`], [`+0.981*`], [`+0.918*`], [`+0.766*`], [`+0.878*`], [`+0.802*`], [`+0.805*`], [`+0.735*`], [`+0.755*`], [`+0.563*`], [`+0.738*`],
      [`right_hemisphere`], [`+0.170*`], [`+0.854*`], [`+0.914*`], [`+0.864*`], [`+0.710*`], [`+0.851*`], [`+0.889*`], [`+0.872*`], [`+0.691*`], [`+0.658*`], [`+0.386`], [`+0.692*`],
    )
  ],
  caption: [Appendix Table A2: Exact hourly regional effect sizes for `persistence_kappa_median`.]
) <tab-appendix-hourly-pers-kappa>

#figure(
  kind: table,
  text(size: 6.4pt)[
    table(
      columns: (1.7fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.78fr),
      align: left,
      inset: 2.5pt,
      table.header([*Region*], [*0-1*], [*1-2*], [*2-3*], [*3-4*], [*4-5*], [*5-6*], [*6-7*], [*7-8*], [*8-9*], [*9-10*], [*10-11*], [*11-12*]),
      [`frontal`], [`+0.181*`], [`+0.806*`], [`+0.596*`], [`+0.677*`], [`+0.625*`], [`+0.705*`], [`+0.657*`], [`+0.684*`], [`+0.799*`], [`+0.701*`], [`+0.502*`], [`+0.688*`],
      [`central`], [`+0.181*`], [`+0.843*`], [`+0.867*`], [`+0.771*`], [`+0.681*`], [`+0.854*`], [`+0.670*`], [`+0.764*`], [`+0.628*`], [`+0.593*`], [`+0.251`], [`+0.542*`],
      [`parietal_occipital`], [`+0.170*`], [`+0.749*`], [`+0.847*`], [`+0.812*`], [`+0.739*`], [`+0.654*`], [`+0.655*`], [`+0.761*`], [`+0.738*`], [`+0.733*`], [`+0.441`], [`+0.504*`],
      [`temporal`], [`+0.170*`], [`+0.690*`], [`+0.516*`], [`+0.680*`], [`+0.531*`], [`+0.622*`], [`+0.646*`], [`+0.682*`], [`+0.530*`], [`+0.636*`], [`+0.330`], [`+0.559*`],
      [`midline`], [`+0.170*`], [`+0.874*`], [`+0.786*`], [`+0.852*`], [`+0.702*`], [`+0.725*`], [`+0.640*`], [`+0.693*`], [`+0.596*`], [`+0.781*`], [`+0.388`], [`+0.536*`],
      [`left_hemisphere`], [`+0.181*`], [`+0.778*`], [`+0.994*`], [`+0.998*`], [`+0.795*`], [`+0.870*`], [`+0.821*`], [`+0.845*`], [`+0.813*`], [`+0.798*`], [`+0.568*`], [`+0.791*`],
      [`right_hemisphere`], [`+0.170*`], [`+0.874*`], [`+0.947*`], [`+0.924*`], [`+0.718*`], [`+0.824*`], [`+0.935*`], [`+0.915*`], [`+0.768*`], [`+0.705*`], [`+0.420`], [`+0.644*`],
    )
  ],
  caption: [Appendix Table A3: Exact hourly regional effect sizes for `persistence_log_eig_var_median`.]
) <tab-appendix-hourly-pers-logeig>

#figure(
  kind: table,
  text(size: 6.4pt)[
    table(
      columns: (1.7fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.78fr),
      align: left,
      inset: 2.5pt,
      table.header([*Region*], [*0-1*], [*1-2*], [*2-3*], [*3-4*], [*4-5*], [*5-6*], [*6-7*], [*7-8*], [*8-9*], [*9-10*], [*10-11*], [*11-12*]),
      [`frontal`], [`-0.498*`], [`-0.538*`], [`-0.605*`], [`-0.697*`], [`-0.725*`], [`-0.662*`], [`-0.584*`], [`-0.715*`], [`-0.745*`], [`-0.700*`], [`-0.614`], [`-0.586*`],
      [`central`], [`-0.469*`], [`-0.579*`], [`-0.732*`], [`-0.742*`], [`-0.711*`], [`-0.736*`], [`-0.691*`], [`-0.700*`], [`-0.732*`], [`-0.677*`], [`-0.556`], [`-0.573*`],
      [`parietal_occipital`], [`-0.513*`], [`-0.441*`], [`-0.727*`], [`-0.768*`], [`-0.712*`], [`-0.763*`], [`-0.602*`], [`-0.734*`], [`-0.793*`], [`-0.729*`], [`-0.642*`], [`-0.659*`],
      [`temporal`], [`-0.487*`], [`-0.451*`], [`-0.614*`], [`-0.669*`], [`-0.652*`], [`-0.431*`], [`-0.529*`], [`-0.556*`], [`-0.723*`], [`-0.714*`], [`-0.529`], [`-0.525*`],
      [`midline`], [`-0.513*`], [`-0.541*`], [`-0.648*`], [`-0.749*`], [`-0.698*`], [`-0.596*`], [`-0.623*`], [`-0.669*`], [`-0.757*`], [`-0.684*`], [`-0.583`], [`-0.567*`],
      [`left_hemisphere`], [`-0.526*`], [`-0.507*`], [`-0.858*`], [`-0.779*`], [`-0.565*`], [`-0.750*`], [`-0.716*`], [`-0.669*`], [`-0.737*`], [`-0.676*`], [`-0.629*`], [`-0.590*`],
      [`right_hemisphere`], [`-0.414*`], [`-0.420*`], [`-0.776*`], [`-0.833*`], [`-0.641*`], [`-0.766*`], [`-0.697*`], [`-0.714*`], [`-0.711*`], [`-0.632*`], [`-0.617*`], [`-0.586*`],
    )
  ],
  caption: [Appendix Table A4: Exact hourly regional effect sizes for `tube_a_operator_norm_median`.]
) <tab-appendix-hourly-aop>

#figure(
  kind: table,
  text(size: 6.4pt)[
    table(
      columns: (1.7fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.72fr, 0.78fr),
      align: left,
      inset: 2.5pt,
      table.header([*Region*], [*0-1*], [*1-2*], [*2-3*], [*3-4*], [*4-5*], [*5-6*], [*6-7*], [*7-8*], [*8-9*], [*9-10*], [*10-11*], [*11-12*]),
      [`frontal`], [`-0.480*`], [`-0.508*`], [`-0.563*`], [`-0.555*`], [`-0.576*`], [`-0.567*`], [`-0.461*`], [`-0.455`], [`-0.535*`], [`-0.442`], [`-0.312`], [`-0.274`],
      [`central`], [`-0.539*`], [`-0.718*`], [`-0.688*`], [`-0.601*`], [`-0.544*`], [`-0.560*`], [`-0.584*`], [`-0.538*`], [`-0.570*`], [`-0.450`], [`-0.303`], [`-0.302`],
      [`parietal_occipital`], [`-0.525*`], [`-0.564*`], [`-0.698*`], [`-0.585*`], [`-0.519*`], [`-0.574*`], [`-0.431`], [`-0.500`], [`-0.563*`], [`-0.417`], [`-0.376`], [`-0.315`],
      [`temporal`], [`-0.492*`], [`-0.463*`], [`-0.536*`], [`-0.596*`], [`-0.562*`], [`-0.407`], [`-0.439*`], [`-0.371`], [`-0.535*`], [`-0.397`], [`-0.306`], [`-0.240`],
      [`midline`], [`-0.557*`], [`-0.602*`], [`-0.543*`], [`-0.628*`], [`-0.572*`], [`-0.503*`], [`-0.524*`], [`-0.436`], [`-0.537*`], [`-0.450`], [`-0.285`], [`-0.226`],
      [`left_hemisphere`], [`-0.586*`], [`-0.666*`], [`-0.724*`], [`-0.644*`], [`-0.452*`], [`-0.506*`], [`-0.501*`], [`-0.467`], [`-0.505*`], [`-0.459*`], [`-0.349`], [`-0.222`],
      [`right_hemisphere`], [`-0.435*`], [`-0.432*`], [`-0.690*`], [`-0.644*`], [`-0.424*`], [`-0.564*`], [`-0.468*`], [`-0.508`], [`-0.516*`], [`-0.406`], [`-0.431`], [`-0.322`],
    )
  ],
  caption: [Appendix Table A5: Exact hourly regional effect sizes for `tube_capture_gate_median`.]
) <tab-appendix-hourly-capture>

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

= References

#bibliography("../comatose_ndt/cardiac_arrest_comatose_references.bib")
