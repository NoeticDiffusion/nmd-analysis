#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Outcome-Linked Geometric Trajectory After Cardiac-Arrest Coma",
  short-title: "Geometric Trajectory in Coma",
  subtitle: "Exploratory subject-anchored 3D and 9D trajectory metrics in the first 12 hours after EEG-anchor",
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
    "trajectory geometry",
    "irreversibility",
    "entropy rate",
    "noetic action",
    "NeuralManifoldDynamics",
  ),
  article-type: "Research Article",
  abstract: [
    The reachability and `9D` Jacobian coma articles left open a third question: how the exported Meta-Noetic Phase Space (MNPS) is actually traversed over time. This exploratory sister draft therefore tests three article-facing trajectory summaries on subject-anchored `3D` and `9D` paths in the first `0-12 h` after EEG-anchor: irreversibility, repertoire entropy rate, and noetic action. The workflow has now been run on both the invalidity-corrected `part1` bundle (`141` extreme-outcome patients; `71 CPC 1`, `70 CPC 5`) and the non-overlapping `part2` bundle (`140` extreme-outcome patients; `70 CPC 1`, `70 CPC 5`), using the same `20260605` H5 roots as the companion reachability paper, followed by a pooled robustness pass with time-shuffle, reverse-time, and QC sensitivity checks. In `part1`, the strongest discovery-side shifts are `3D` noetic action (`d = -0.344`, Mann-Whitney `p = 0.055`, article-facing) and `9D` noetic action (`d = -0.455`, `p = 0.083`); no article-facing metric clears `q < 0.25` under BH-FDR. In `part2`, all signals attenuate to `|d| ≤ 0.225`. Pooled across both cohorts, `9D` noetic action is the clearest signal (`d = -0.329`, `p = 0.043`, `q = 0.187`), followed by `3D` noetic action (`d = -0.256`, `p = 0.058`) and `9D` entropy rate (`d = +0.158`, `p = 0.040`); no metric clears BH-FDR correction. The pooled robustness pass reveals that neither `3D` noetic action nor `9D` noetic action is a temporal-order signal: both strengthen under within-run time shuffle (`d = -0.304` and `-0.449` shuffled, versus `-0.251` and `-0.338` observed), indicating they measure trajectory roughness / friction rather than directional grammar. `3D` irreversibility, which in the earlier `20260601` run was the best temporal-order-sensitive candidate, collapses in the updated data: pooled observed `d = -0.156` (`p = 0.476`) with a sign flip under shuffle, and a substantial channel-coverage QC correlation (`rho = -0.364`). The bounded conclusion is that a reproducible article-local trajectory layer exists, the dominant pooled separator is broad action / friction structure, but the layer is materially weaker than the companion reachability family and no metric survives BH-FDR correction.
  ],
  author-summary: [
    The earlier coma papers asked what nearby futures remain reachable and how local flow deforms in a repaired `9D` space. This follow-up asks a simpler but complementary question: once the path exists, how does the system actually move through it over time? We therefore added an article-local trajectory layer for subject-anchored `3D` and `9D` exports and ran three initial metrics: irreversibility, entropy rate, and noetic action, using the same invalidity-corrected H5 exports as the companion reachability paper. After a full `part1` plus full `part2` rerun with the `20260605` processed roots, the clearest pooled signal is `9D` noetic action (`d = -0.329`, `p = 0.043`), but it strengthens under time shuffle — meaning it captures trajectory roughness, not temporal grammar. `3D` irreversibility, which had been the best temporal-order-sensitive candidate in the earlier `20260601` run, essentially collapses in the updated data (`d = -0.156`, `p = 0.476` pooled) and shows a substantial channel-coverage confounder. No metric survives BH-FDR correction. The manuscript therefore reads as exploratory: reproducible in direction but materially weaker than the companion reachability layer, and the "time-arrow" hypothesis is not currently supported.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted in the submission version.],
  data-availability: [The underlying I-CARE dataset is available through PhysioNet version `2.1` at https://doi.org/10.13026/m33r-bj81. The article-local trajectory outputs generated in this pass live under `articles/CLINICAL/comatose_geometric_trajectory/results/`, especially `trajectory_metrics_20260606_part1_primary12h/`, `trajectory_metrics_20260606_part2_primary12h/`, `outcome_contrasts_trajectory_20260606_cpc15_part1_primary12h/`, `outcome_contrasts_trajectory_20260606_cpc15_part2_primary12h/`, `outcome_contrasts_trajectory_20260606_pooled_cpc15_primary12h/`, `metric_result_ledger_20260606_part1/`, `metric_result_ledger_20260606_part2/`, and `robustness_20260606_trajectory/`. Timeline inputs are shared with the companion reachability paper at `articles/CLINICAL/comatose_ndt/results/timeline_analysis_20260606_part1_invalidityfix_primary12h/` and `timeline_analysis_20260606_part2_invalidityfix_primary12h/`.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

= Introduction

The current coma line already has two dynamical layers. The reachability paper asks whether later outcome is associated with broader or more persistent reachable local futures, while the `9D` Jacobian follow-up asks whether repaired local-linear deformation carries a distinct signal.@langell2026_reachability, @amorim2023icare, @PhysioNet-i-care-2.1 The remaining gap is temporal rather than purely local: once the trajectory has been exported, does the realized path grammar itself differ between later `CPC 1` and later `CPC 5` patients?

That gap matters because path traversal is not identical to either local reachability or local Jacobian structure. Two patients may have similarly bounded nearby futures yet differ in how directionally their state sequence unfolds, how richly it transitions across recurrent state regions, or how dynamically costly the resulting path appears. Those questions stay within the bounded NeuralManifoldDynamics export layer and do not require the manuscript to validate the full interpretive scope of Noetic Diffusion Theory.@langell2026_mndm, @langell2025_6

As in the other coma papers, the target is not a bedside-ready prognostic model or a direct measure of consciousness. The narrower aim is to determine whether a thin exploratory trajectory layer can be computed reproducibly on real I-CARE H5 bundles, whether any outcome direction survives a separate verification cohort, and whether the leading rows behave like genuine temporal-order signals rather than trivial support artifacts.

#netn-box(title: [Core question])[
  During the first `12 h` after EEG-anchor, do later `CPC 1` and later `CPC 5` patients differ in the realized temporal grammar of subject-anchored `3D` and `9D` MNPS traversal, as summarized here by irreversibility, repertoire entropy rate, and noetic action?
]

= Cohort and exploratory contract

This draft freezes the same coarse coma article contract as the sister papers while keeping the metric family deliberately narrow.

1. Primary time bin: `0_12h` after EEG-anchor.
2. Primary contrast: later `CPC 1` versus later `CPC 5`.@westhall2016standardized, @ruijter2019early, @hofmeijer2015early, @rajajee2023neuroprognostication
3. Primary coordinate contract: `subject_anchored`.
4. Primary path objects: both exported `3D` and `9D` trajectories.
5. Initial article-facing metrics: `irreversibility`, `entropy_rate`, `noetic_action`.

The first full result bundle reported here uses the part1 I-CARE export rooted at `neuralmanifolddynamics_physionet_icare_2_1_20260523_173059`, which yields `141` extreme-outcome patients (`71 CPC 1`, `70 CPC 5`) in the `0_12h` window. The same article-local code path has now also been promoted from smoke to a full verification-side rerun against `part2_140sub_9d`, yielding `140` additional extreme-outcome patients (`70 CPC 1`, `70 CPC 5`). The present draft still avoids a formal pooled article hierarchy, but it no longer depends on discovery-only execution.

#netn-box(title: [Selection And Validation Status])[
  *Current evidence layer:* separate `part1` discovery and `part2` verification contrasts are both available using the invalidity-corrected `20260605` H5 exports, along with a pooled robustness pass.

  *Verification readiness:* full `part2` outcome rerun completed; pooled article hierarchy available but no metric clears BH-FDR correction.

  *Article-facing family:* `irreversibility`, `entropy_rate`, `noetic_action` on subject-anchored `3D` and `9D` paths.

  *Current clearest pooled signal:* `9D noetic_action` (`d = -0.329`, `p = 0.043`) and `9D entropy_rate` (`d = +0.158`, `p = 0.040`); neither survives BH-FDR.

  *Temporal-order sensitivity status:* both noetic-action rows strengthen under time shuffle; `3D irreversibility` collapses under the updated data (`d = -0.156`, `p = 0.476`) and has a channel-coverage confounder.

  *Interpretive boundary:* no metric hierarchy is frozen as validated, and no pooled article claim is made in this version.
]

= Methods

== NeuralManifoldDynamics framing

NeuralManifoldDynamics provides the measurement layer used here.@langell2026_mndm Preprocessed EEG is partitioned into short windows and exported into fixed low-dimensional coordinate charts with versioned timing and provenance fields. This article requests the `subject_anchored` chart rather than the `cohort_anchored` alternative, because the present question concerns within-patient path organization rather than cross-subject geometric alignment.

The broader Noetic Diffusion Theory framing remains a background organizing language rather than the direct inferential target of this draft.@langell2025_6 The present manuscript stays at the bounded export and local-summary level: it reads article-local trajectories, computes exploratory path summaries, and compares those summaries by later outcome.

== Timeline and path extraction

Run-level timing is rebuilt article-locally with the existing coma timeline infrastructure, using `time_reference.v1` when available and WFDB-header fallback only when needed. Runs are assigned to bins by anchor-relative midpoint, matching the earlier coma export discipline. The current result bundle therefore contains:

1. `run_timing_metadata.csv`
2. `patient_timebin_summaries.csv`
3. run-level trajectory metrics
4. patient-timebin trajectory metrics
5. patient-level outcome contrasts

For the first pass, each continuous run is treated as its own path segment. Patient-level values in `0_12h` are then the median of run-level metric values for that patient and analysis type.

== Exploratory trajectory metrics

The first pass intentionally uses only three article-facing summaries.

1. *Irreversibility.* Each run is discretized into a fixed repertoire codebook on the requested chart (`12` states in `3D`, `24` in `9D`). If `pi_i` denotes empirical state occupancy and `P_ij` empirical transition probability, the reported transition-asymmetry score is `I = 0.5 * sum_(i,j) abs(pi_i P_ij - pi_j P_ji)`.
2. *Repertoire entropy rate.* On the same discretized transition matrix, the reported richness score is `H_rate = -sum_i pi_i sum_j P_ij log(P_ij + epsilon)`.
3. *Noetic action.* For variable-length runs, the article-local implementation reports the median local Lagrangian density rather than a raw path integral, so that run duration does not trivially dominate the contrast. The local density uses weighted kinetic, jerk, and potential terms of the subject-anchored coordinates, following the compact exploratory form `A_MNPS ~ 0.5 ||Delta z||_M^2 / Delta t^2 + eta ||Delta^2 z||_M^2 / Delta t^4 + lambda Phi(z)`, with diagonal metric weights estimated from the cohort fit sample and supportive component outputs retained for audit.

These choices are methodological compromises rather than canonical final definitions. In particular, the discretized transition scores should be read as bounded MNPS transition asymmetry / richness summaries, not as literal thermodynamic theorems, and the noetic-action decomposition is retained precisely because low-action suppression and high-action bursty instability may both align with poor outcome for different reasons.

== Temporal null and QC checks

Because the main conceptual tension is whether any row reflects true temporal grammar rather than merely path spread or support differences, the current article also includes a pooled robustness pass across `part1` and `part2`. For a selected set of `3D` and `9D` rows, each run is recomputed under three sequence conditions: the observed ordering, a within-run `time_shuffled` control that preserves the same coordinate cloud while breaking temporal order, and a `reverse_time` control. The current irreversibility definition uses absolute transition asymmetry, so full sign-flip reversal is not expected there; the practical question is instead whether the effect collapses once native order is destroyed.

At the patient level, the same robustness bundle also audits simple associations with run support, total windows, and channel support summaries. Those checks are not intended as full causal confound control, only as a first screen against the most obvious support-driven explanations.

= Results

The first full article-local pass has now been completed for both `part1` and `part2` using the invalidity-corrected `20260605` H5 exports, sharing timeline inputs with the companion reachability paper. The current result tree contains analyzable `0_12h` runs from `141` extreme-outcome patients in `part1` (`71 CPC 1`, `70 CPC 5`) and `140` extreme-outcome patients in `part2` (`70 CPC 1`, `70 CPC 5`).

Within the article-facing family, the discovery-side and validation-side stories show directional consistency but modest and attenuated effect sizes. In `part1`, the strongest article-facing shifts are `3D` noetic action (`d = -0.344`, Mann-Whitney `p = 0.055`) and `9D` noetic action (`d = -0.455`, `p = 0.083`); the dominant supportive row is `3D` entropy production (`d = -0.466`, `p = 0.037`). No article-facing metric clears `q < 0.25` under BH-FDR in `part1`. In `part2`, all signals attenuate substantially: the strongest article-facing directions are `9D` entropy rate (`d = +0.225`, `p = 0.058`) and `9D` noetic action (`d = -0.225`, `p = 0.274`). Pooled across both cohorts, `9D` noetic action is the clearest article-facing signal (`d = -0.329`, `p = 0.043`, `q = 0.187`), followed by `3D` noetic action (`d = -0.256`, `p = 0.058`, `q = 0.241`) and `9D` entropy rate (`d = +0.158`, `p = 0.040`, `q = 0.187`); none clears BH-FDR correction.

#figure(
  image("figures/20260601_geometric_trajectory/figure_1_trajectory_effect_sizes.svg", width: 100%),
  caption: [Part1 exploratory patient-level effect sizes for the three article-facing trajectory metrics in subject-anchored `3D` and `9D` charts (from `20260601` reference run; updated `20260606` figure pending regeneration).]
) <fig-traj-effects>

The supportive metrics reinforce the cautionary reading. `3D` entropy production (`d = -0.466`, `p = 0.037`) is the strongest discovery-side row across any metric, but it is a supportive rather than article-facing observable. In `part2`, all supportive signals attenuate similarly to the article-facing rows. In the pooled analysis, no metric — article-facing or supportive — clears BH-FDR correction.

The pooled robustness pass sharpens the interpretation significantly compared to the earlier `20260601` run. `9D` noetic action is the clearest pooled separator (observed `d = -0.338`, `p = 0.033`), but it strengthens substantially under time shuffle (`d = -0.449`, `p = 0.008`), indicating that it captures trajectory roughness or friction rather than temporal grammar. `3D` noetic action shows the same pattern: observed `d = -0.251` versus shuffled `d = -0.304`. Neither metric is therefore a temporal-order signal in its current form.

`3D` irreversibility, which in the earlier `20260601` run was the best temporal-order-sensitive candidate (`d = -0.280` observed versus `0.050` shuffled), essentially collapses in the updated `20260606` data: pooled observed `d = -0.156` (`p = 0.476`), shuffled `d = +0.180` (sign flip), and a substantial channel-coverage QC correlation (`rho = -0.364`, `p = 3.0e-10`). This suggests the earlier result was tied to data-specific properties of the `20260601` export roots rather than a generalizable temporal-asymmetry signal.

= Limitations and claim boundary

This draft is intentionally thin because the trajectory family is not yet frozen.

First, even though both `part1` and `part2` are available and a pooled robustness pass has been completed, no metric clears BH-FDR correction in the pooled analysis. The trajectory layer is therefore exploratory in both the statistical and conceptual sense. Second, `CPC 5` remains an outcome category shaped by systemic severity, care pathway, and potential treatment-limitation effects rather than a pure neural-death assay.@nolan2025postresuscitation, @sandroni2021european Third, the noetic-action implementation is operational rather than theoretically final: it measures median local Lagrangian density and is sensitive to coordinate roughness regardless of temporal order, as confirmed by the time-shuffle analysis. Fourth, `3D` irreversibility, which was the best temporal-order-sensitive candidate in the earlier `20260601` run, collapses substantially in the updated `20260606` data and has a strong channel-coverage confounder (`rho = -0.364`), making its earlier result non-reproducible under the corrected export. Fifth, the `irreversibility` score is an absolute transition-asymmetry quantity, not a signed reversal-sensitive observable, which limits its sensitivity to directed time-asymmetry.

The bounded conclusion is therefore simple. A reproducible article-local trajectory layer exists for subject-anchored coma paths and runs end-to-end on both the `part1` and `part2` raw roots. The clearest pooled separator is `9D` noetic action (`d = -0.329`, `p = 0.043`), but it is a friction / roughness observable rather than a temporal-grammar readout. `3D` irreversibility is no longer the best temporal-order-sensitive candidate after the updated data; the earlier result appears to have been data-root-specific. Everything stronger requires a stricter pooled hierarchy, a genuinely signed directionality metric, and ideally an explicit mechanism distinguishing roughness from order-sensitive asymmetry.

#bibliography("cardiac_arrest_comatose_references.bib")
