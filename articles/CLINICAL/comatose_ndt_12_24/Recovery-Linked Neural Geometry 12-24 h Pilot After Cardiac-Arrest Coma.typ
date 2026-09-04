#import "../comatose_ndt/network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Recovery-Linked Neural Geometry 12-24 h Pilot After Cardiac-Arrest Coma",
  short-title: "Coma 12-24 h Pilot",
  subtitle: "A late-window part1 continuation of the I-CARE geometry line",
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
    "reachability",
    "Jacobian",
    "NeuralManifoldDynamics",
    "pilot",
  ),
  article-type: "Research Article",
  abstract: [
    This pilot extends the existing I-CARE coma geometry line into the later `12-24 h` anchor-relative window using a no-regional subject-anchored export with updated invalidity control. The processed root contained `1575` H5 runs across `124` subjects, but only `143` runs from `97` subjects belonged to the true `12_24h` slice after timing reconstruction; the remaining runs were mostly still in `0_12h`. The downstream contract was held fixed to the established coma article and carried forward the same `MNPS`, `MNJ`, and reachability summaries. In the analyzable `12_24h` subset (`47 CPC 1`, `50 CPC 5`), the fixed reachability family was no longer weak but mixed-sign: `persistence_kappa_median` (`d = -0.686`, `q = 0.0376`), `tube_a_operator_norm_median` (`d = 0.571`, `q = 0.0393`), and `tube_capture_gate_median` (`d = 0.584`, `q = 0.0393`) survived BH-FDR inside the prespecified five-metric family, while `persistence_log_eig_var_median` remained nominal (`d = -0.353`, `q = 0.137`) and `tube_d_eff_median` did not (`d = -0.046`, `p = 0.642`). The Jacobian anchors were present but modest (`MNJ 3D spectral_radius_median d = -0.237`, `p = 0.798`; `frobenius_norm_median d = -0.293`, `p = 0.321`). Between-run MAD at the strict `>=3`-run threshold was not testable in this sparse late-window slice; under exploratory `>=2`-run coverage (`n = 12`), the largest MAD contrast appeared in `persistence_log_eig_var_median` (`d = -1.274`, `p = 0.0283`).
  ],
  author-summary: [
    The existing coma article stabilized an early `0-12 h` geometry contract. This continuation tests whether the same downstream stack can be carried into `12-24 h` under a no-regional subject-anchored export. It can. The timeline audit, fixed metric extraction, bounded `CPC 1` versus `CPC 5` contrast, reviewer checks, figures, and a late-window MAD/IQR pass all rebuild cleanly under the same contract. What changed relative to the earlier pass is the substantive pattern: the fixed five-metric reachability family is now led by a mixed-sign trio (`persistence_kappa_median`, `tube_a_operator_norm_median`, `tube_capture_gate_median`), while `tube_d_eff_median` and Jacobian anchors remain modest.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted in the submission version.],
  data-availability: [Pilot outputs for the current rerun live under `articles/CLINICAL/comatose_ndt_12_24/results/`, with reproducibility commands recorded in `results/reproducibility_commands.md`. The upstream processed root analyzed here is `J:/repos/NoeticDiffusion/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260607_151559_no_regional_12_24h_subject_anchor`, especially the stamped bundles `timeline_analysis_20260608_part1_noregional_subjectanchor_primary12h_allavailable`, `mnps_summary_20260608_part1_noregional_subjectanchor_primary12h_true1224`, `outcome_contrasts_20260608_part1_noregional_subjectanchor_primary12h_true1224_cpc15`, `reviewer_checks_20260608_part1_noregional_subjectanchor_true1224`, and `between_run_iqr_mad_20260608_part1_noregional_subjectanchor_true1224_min2`.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

= Introduction

This pilot continues the existing I-CARE coma geometry line into a later anchor-relative window without changing the downstream metric contract. The starting point is the established article under `articles/CLINICAL/comatose_ndt/`, which already fixed the main interpretive hierarchy: `MNPS` as descriptive spread, `MNJ` as local linear deformation, and reachability as the lead short-horizon geometry layer.@amorim2023icare, @langell2026_coma_v011

The present continuation is narrower than the main article in two ways. First, the currently available processed root is still part1-only. Second, despite the folder name, the root contains a mix of `0_12h`, `12_24h`, and later runs, so the manuscript must distinguish the full-export timing audit from the true `12_24h` subset rather than treating the directory name as ground truth.

#netn-box(title: [Pilot question])[
  Using a no-regional subject-anchored late-window export, can the established coma geometry contract be extended into a bounded `12_24h` pilot without changing the metric family or overstating the current completeness of the cohort?
]

= Cohort and pilot design

The pilot consumes the processed root `J:/repos/NoeticDiffusion/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260607_151559_no_regional_12_24h_subject_anchor` under the `subject_anchored` export contract. The analysis stack is kept parallel to the main coma manuscript: timeline reconstruction, filtered `mnps_summary` extraction, a bounded `CPC 1` versus `CPC 5` contrast, reviewer-style checks for the fixed reachability family, a between-run MAD/IQR pass, and a figure bundle focused on the true `12_24h` subset.

The critical design rule is that the pilot does *not* trust the folder name as a time-bin label. Instead it first reconstructs the full anchor-relative timing table and only then filters the geometry summary stack to `time_bin == "12_24h"`. The full-export audit and the inferential slice therefore answer different questions.

#figure(
  kind: table,
  table(
    columns: (2.5fr, 1.1fr, 1.4fr),
    align: left,
    inset: 4pt,
    table.header([*Bundle item*], [*Count*], [*Interpretation*]),
    [Full export H5 runs], [1575], [all runs currently present on disk],
    [Full export subjects], [124], [current no-regional batch],
    [Runs in `0_12h`], [1412], [majority of the current root],
    [Runs in `12_24h`], [143], [true pilot slice],
    [Runs in `24_48h`], [11], [late spillover],
    [Runs in `72h_plus`], [9], [very late spillover],
    [Subjects with `12_24h` coverage], [97], [analyzable later-window subset],
    [`CPC 1 / CPC 5` in `12_24h` subset], [`47 / 50`], [bounded pilot contrast],
  ),
  caption: [Full-export audit and the true `12_24h` inferential slice for the no-regional subject-anchored bundle.]
) <tab-bundle-audit>

#figure(
  image("figures/20260608_part1_noregional_subjectanchor_true1224/fig1_cohort_coverage_overview.svg", width: 100%),
  caption: [Site distribution plus timing and channel-coverage overview for the analyzable `12_24h` pilot subset.]
) <fig-cohort>

= Methods

The downstream scripts mirror the established line under `articles/CLINICAL/comatose_ndt/src/` and are staged locally under `articles/CLINICAL/comatose_ndt_12_24/src/`. The fixed article-facing metric families are:

- Reachability: `tube_d_eff_median`, `persistence_kappa_median`, `persistence_log_eig_var_median`, `tube_a_operator_norm_median`, `tube_capture_gate_median`
- `MNPS` anchors: `m_std`, `m_e_std`
- `MNJ` anchors: `spectral_radius_median`, `frobenius_norm_median` in `3D`, with supportive `9D` rows

As in the main article, the endpoint should be interpreted as a recovery-linked `CPC 1` versus `CPC 5` association contrast rather than as a pure neural-viability label.@sandroni2021european The pilot runner used here is `src/run_coma_12_24_pilot.py`, which writes a stamped timeline audit, a filtered `12_24h` `mnps_summary` bundle, an outcome-contrast bundle, reviewer checks, figures, and a manifest describing the exact output paths. Between-run variability is summarized by `src/compute_between_run_iqr_mad.py`.

= Results

== Full-export audit versus true `12_24h` subset

The current no-regional pilot root is still mixed-bin rather than window-pure. The timing reconstruction showed `1575` H5 runs across `124` subjects, with `1412` runs assigned to `0_12h`, `143` to `12_24h`, `11` to `24_48h`, and `9` to `72h_plus`. The true inferential slice therefore settled at `97` subjects, of whom `47` were later `CPC 1` and `50` later `CPC 5`. Mean/median recording start in the filtered subset were `13.290 / 12.0 h` after anchor, mean/median recording end were `14.187 / 13.0 h`, and mean/median channel coverage were `0.944 / 0.952`.

== Fixed anchor families

The updated later-window pilot changes the hierarchy relative to the earlier pass. Within the fixed reachability family, `persistence_kappa_median` remains the clearest corrected negative row (`d = -0.686`, `q = 0.0376`), while `tube_a_operator_norm_median` (`d = 0.571`, `q = 0.0393`) and `tube_capture_gate_median` (`d = 0.584`, `q = 0.0393`) now also survive BH-FDR with positive direction in `CPC 1`. `persistence_log_eig_var_median` remains nominal (`d = -0.353`, `q = 0.137`) and `tube_d_eff_median` remains near-null (`d = -0.046`, `p = 0.642`).

The classical anchors were present but secondary. `MNJ 3D` retained the direction of lower `CPC 1` local expansion, with modest rows (`spectral_radius_median d = -0.237`, `p = 0.798`; `frobenius_norm_median d = -0.293`, `p = 0.321`). `MNJ 9D` remained weak (`spectral_radius_median d = 0.155`, `p = 0.695`; `frobenius_norm_median d = 0.240`, `p = 0.203`), and the `MNPS` spread anchors stayed small. The current `12_24h` slice therefore looks less Jacobian-led than the early-window paper and more like a mixed-sign reachability variant.

#figure(
  kind: table,
  table(
    columns: (2.35fr, 1.1fr, 1.1fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Family / metric*], [*`CPC 1` med*], [*`CPC 5` med*], [*Cohen's `d`*], [*M-W `p`*]),
    [`MNPS 3D / m_std`], [`0.875`], [`0.831`], [`+0.345`], [`0.203`],
    [`MNPS 9D / m_e_std`], [`1.076`], [`1.077`], [`+0.277`], [`0.518`],
    [`Reachability / tube_d_eff_median`], [`3.000`], [`3.101`], [`-0.046`], [`0.642`],
    [`Reachability / persistence_log_eig_var_median`], [`1.704`], [`2.027`], [`-0.353`], [`0.0411`],
    [`Reachability / persistence_kappa_median`], [`0.000801`], [`0.001371`], [`-0.686`], [`0.00752`],
    [`Reachability / tube_a_operator_norm_median`], [`11.217`], [`9.803`], [`+0.571`], [`0.00868`],
    [`Reachability / tube_capture_gate_median`], [`1.706`], [`1.585`], [`+0.584`], [`0.00977`],
    [`MNJ 3D / spectral_radius_median`], [`0.0715`], [`0.0718`], [`-0.237`], [`0.798`],
    [`MNJ 3D / frobenius_norm_median`], [`0.1445`], [`0.1468`], [`-0.293`], [`0.321`],
    [`MNJ 9D / spectral_radius_median`], [`0.0959`], [`0.0972`], [`+0.155`], [`0.695`],
    [`MNJ 9D / frobenius_norm_median`], [`0.628`], [`0.576`], [`+0.240`], [`0.203`],
  ),
  caption: [Compact `12_24h` pilot anchors. Medians are shown separately for the analyzable `CPC 1` and `CPC 5` groups.]
) <tab-primary-anchors>

#figure(
  image("figures/20260608_part1_noregional_subjectanchor_true1224/fig2_primary_reachability_panel.svg", width: 100%),
  caption: [Fixed five-metric reachability family in the analyzable `12_24h` pilot subset.]
) <fig-reachability>

== Reviewer-style selection boundary

The reviewer-style audit no longer supports the partial-pass conclusion that the fixed five-metric reachability family is simply weak. In the current rerun, three prespecified rows survive BH-FDR: `persistence_kappa_median` (higher in `CPC 5`) plus `tube_a_operator_norm_median` and `tube_capture_gate_median` (both higher in `CPC 1`). Exploratory rows outside the frozen five-metric family remain led by condition/persistence variants such as `cone_kappa_h1_median` and `cone_kappa_h2_median`. What remains unproven is whether this mixed-sign pattern is a stable late-window biological signal, a downstream artifact/smoothness effect, or a mixture of both.

== Between-run temporal variability (MAD)

The pilot now includes a dedicated between-run IQR/MAD pass in `12_24h`. Under the strict threshold (subjects with at least `3` qualifying runs per metric), no contrast rows are testable because only `5` subjects meet coverage. This is expected in a sparse late-window slice dominated by single-run subjects.

Under an exploratory threshold of `>=2` runs, `12` subjects are analyzable (`8 CPC 1`, `4 CPC 5`). In that subset, the largest MAD separation appears in `persistence_log_eig_var_median_mad` (`0.076` versus `0.182`, `d = -1.274`, `p = 0.0283`), followed by `persistence_kappa_median_mad` (`d = -1.353`, `p = 0.0727`). These signals are directionally consistent with higher persistence-side instability in `CPC 5`, but the sample is too small for confirmatory interpretation.

= Discussion

The main value of the pilot is now both structural and substantive. The later-window continuation can be run under the same downstream contract, and the no-regional export is large enough to produce a clean timing audit, a filtered `12_24h` metric bundle, a bounded contrast table, manuscript-facing figures, and a bounded between-run variability pass.

Substantively, the current `12_24h` slice is not well described as a `MNJ 3D`-first continuation. The stronger evidence now sits inside the fixed reachability family itself, but not in the same row that led the early-window paper. `tube_d_eff_median` remains near-null, while the corrected rows are a mixed-sign set (`persistence_kappa_median` in `CPC 5`, `tube_a_operator_norm_median` and `tube_capture_gate_median` in `CPC 1`). That is a later-window geometry story, but not a simple replay of the early `0_12h` hierarchy.

#netn-box(title: [Claim hierarchy])[
  Internal validated result: the no-regional export supports a clean mixed-bin audit and a reproducible true `12_24h` bundle under the same metric contract as the main coma article, with BH-FDR support for `persistence_kappa_median`, `tube_a_operator_norm_median`, and `tube_capture_gate_median` inside the prespecified five-metric reachability family. Plausible interpretation: late-window reachability may follow a mixed-sign reweighting rather than a single persistence-only shift. Not yet validated: a pooled part1/part2 claim, a mechanistic explanation, or a deployment-style later-window biomarker.
]

= Limitations

The main limitation is still incompleteness. The current export is part1-only, mixed-bin, and not yet suitable for any pooled part1/part2 claim. The inferential slice represents `143` runs from `97` subjects and may therefore exaggerate or distort ranking among closely related reachability metrics. Between-run MAD/IQR is especially coverage-limited in this late window: only `5` subjects meet the strict `>=3` threshold (no testable contrasts), and only `12` meet exploratory `>=2` coverage. The pilot also inherits the same endpoint caveat as the main coma line: `CPC 1` versus `CPC 5` is recovery-linked rather than a pure neural-viability label, and the locked export does not allow the article to resolve WLST or related pathway effects.@sandroni2021european

= Conclusion

The `12_24h` coma pilot preserves the existing geometry contract and yields a bounded later-window continuation bundle under the no-regional export. In the current slice, the strongest fixed-family signal is not `tube_d_eff_median` or `MNJ 3D`, but a mixed-sign reachability trio (`persistence_kappa_median`, `tube_a_operator_norm_median`, `tube_capture_gate_median`) with persistence-log-eig variability remaining nominal. Between-run MAD is not confirmatory at strict coverage but shows exploratory persistence-side instability in the sparse `>=2` repeated-run subset. The manuscript should therefore be read as a bounded late-window `part1` result: internally coherent, still not pooled, and suggestive of a shifted later-window hierarchy rather than a direct replay of the early-window paper.

#bibliography("../comatose_ndt/cardiac_arrest_comatose_references.bib")
