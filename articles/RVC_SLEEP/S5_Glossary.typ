// S5 Glossary — shared terminology, RVC_SLEEP edition.
// Living document: update to match the current MNDM pipeline version, and
// note version-specific changes in entries.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S5 - Glossary",
  short-title: "Glossary",
  subtitle: "Shared terminology across articles, with RVC/sleep-specific entries",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("glossary", "NDT", "MNDM", "MNPS", "embodied anchoring", "rhythmic variance control", "sleep spindles"),
  article-type: "Supplementary Material",
  abstract: [
    This document defines the core terminology used across articles in this repository, with additional entries specific to the RVC_SLEEP spindle-geometry study (two-dataset A2r timing result in ANPHY/BOAS; RichSleep same-estimand timing test inconclusive). Entries cover the theoretical framework, the computational pipeline, embodied anchor metrics, the family of primary metric scalar summaries, the subject-weighted statistical protocol, and the robustness-audit methods used in this article. Definitions reflect the current implementation as of the RVC_SLEEP analysis freeze (2026-07-03/04) and the 2026-08-30 claim-scope revision; version-specific changes to metric computation are noted in the relevant entry.
  ],
)

#set heading(numbering: none)

_Note: This is a living document. Definitions are updated to match the current pipeline version. Version-specific changes to metric computation are noted in the relevant entry._

_*Reading guide for reviewers.* Where relevant, entries distinguish three layers: (1) *Implemented* - the exact computation in the pipeline; (2) *Interpretation* - the most defensible empirical reading; (3) *Speculative / Not established* - theoretical mappings not yet directly confirmed._

= A - D

*A1r / A2r* - The two primary subject-weighted contrast estimands used in this article. *A1r*: event-vs-matched-control specificity (`event_bin - matched_control_median`, subject-weighted). *A2r*: event-vs-pre_far within-spindle timing (`event_bin - mean(pre_far bins, same event)`, subject-weighted). Adopted as the corrected primary estimand (over the earlier event-weighted A1/A2) because of BOAS's uneven per-subject spindle-event counts.

*Anchor-augmented surface* - An alternate MNPS coordinate-export configuration (ANPHY/BOAS only) in which the `e_m` sub-coordinate's EEG term is partially or fully replaced by the dataset's primary body-derived anchor signal. Used only for the Pass B surface-sensitivity construction-validity check; never used as the primary geometric claim (dual-surface contract).

*Attractor* - A stable region in the neural state manifold to which trajectories tend to return after small perturbations. Geometrically, a local minimum in the potential landscape. *Speculative / Not established* in the context of this article: no attractor-landscape reconstruction was performed; the term is used only in the general NDT background sense.

*Cardioresp_anchor_index* - RichSleep's primary Embodied Anchor Principle (EAP) composite index: a dual-arm anchor built from *simultaneous* ECG and respiratory channels with near-100% subject coverage. Used as the primary anchor in the RichSleep EAP-moderation test (R6), specifically because it removes the single-channel-missingness limitation of ANPHY's cardiac-only and BOAS's respiratory-only anchors.

*Coordinate (`m`, `d`, `e`)* - The canonical 3D MNPS chart. `m` (metastability/mobility): how variable/mobile the state trajectory is. `d` (deviation): distance from an optimal integration-segregation balance point. `e` (entropy/entropic energy): disorder/complexity of the underlying signal. *Interpretation*: higher `d` during a spindle event reflects the state moving further from that balance point; this article does not interpret this directionally as "better" or "worse."

*`d_n`, `d_l`, `d_s`* - Three stratified sub-coordinates recomposed into `d`. *Interpretation*: `d_n` as network-integration deviation (this article's most reproducible tested endpoint in ANPHY/BOAS A2r); `d_l` as local clustering-based segregation load; `d_s` as representational-geometry deviation. *Implemented*: the NMD `mnps_9d.subcoords` feature map in the hashed run configs, not a schematic heat-kernel formula (S1.2).

*Dual-surface contract* - The rule that the primary MNPS geometry export never contains body-signal-derived features (`primary_eeg_only`), and that any body-signal-augmented export (`anchor_aug`) is used strictly for a construction-validity check (Pass B), never for the primary specificity/timing claim. Central to interpreting Pass B correctly (S1.4, main text R5).

= E - L

*Embodied Anchor Principle (EAP)* - The NDT proposition that bodily/interoceptive rhythms (cardiac, respiratory, ocular) can condition the same latent landscape that governs cortical state-space dynamics. In this article, tested strictly as a *moderator* of the EEG-only spindle-locked geometry effect (Pass C / RichSleep R6), not as a component of the geometry itself. *Not supported* under the tonic composite anchors and underpowered phase-resolved tests reported here (main text R5–R6b); not a general rejection of body-brain coupling.

*`e_e`, `e_s`, `e_m`* - Three stratified sub-coordinates recomposed into `e`. *Implemented in this contract*: `e_s = 0.5 · eeg_alpha_theta + 0.5 · eeg_gamma`; primary-surface `e_m = 0.6 · eeg_hjorth_mobility + 0.4 · eeg_beta_alpha`. `e_s` is not permutation entropy here. `e_m` is the one endpoint whose feature composition differs on the anchor-augmented surface (Dual-surface contract). See S1.2.

*Event-locked table* - The per-(subject, window, condition, bin_label) analysis-ready table produced by the NMD pipeline, aligning each detected sleep spindle against five peri-event bins (`pre_far`, `pre_near`, `event`, `post_near`, `post_far`) and a matched-control pool of non-spindle N2 windows. Control *rows* are 30 s MNPS-grid expansions; analysis median-collapses them per `matched_event_id` (S1.1). Not 1–3 independent control rows per spindle.

= M - R

*Matched control* - A non-spindle N2 window from the same subject and recording session, drawn at least 30 s from any spindle/K-complex/arousal, used as the comparison condition for the A1r specificity contrast.

*Meta-Noetic Phase Space (MNPS)* - The low-dimensional geometric chart (3D: $m,d,e$; 9D stratified: $m_a,m_e,m_o,d_n,d_l,d_s,e_e,e_s,e_m$) that NDT uses to project raw electrophysiology into an auditable, release-fixed state-space representation. See S1.2.

*NeuralManifoldDynamics (NMD)* - The versioned processing pipeline that ingests raw EDF/PSG recordings and exports per-epoch MNPS coordinates, Jacobian tensors, anchor-state indices, and event-locked analysis tables. Every claim in this article is read against the NMD `summarize` output for the relevant run (config-hash-verified), not against raw signals directly.

*Pass A / A1 / A2 / A1r / A2r / decomposition* - The frozen analysis sequence for ANPHY/BOAS: Pass A (base N2/coverage filter); A1 (event-weighted, pre-amendment specificity); A2 (event-weighted, pre-amendment timing); A1r/A2r (corrected, subject-weighted versions of the same two contrasts); A1 decomposition (splitting the A1r delta into a timing component and a baseline-separation component, resolving the `d_n` cross-dataset sign conflict - main text R4).

*Pass B* - The surface-sensitivity check: does the anchor-augmented surface change the A1r/A2r subject-weighted deltas relative to the primary surface? A construction-validity check, *not* an EAP-moderation test (main text R5).

*Pass C* - The EAP-moderation test itself: `delta ~ anchor_pre_far + nuisance covariates`, weighted least squares with cluster-robust SE by subject, plus a per-subject-slope sign-flip permutation sensitivity check. Run on ANPHY (cardiac-only anchor) and BOAS (respiratory-only anchor) in the frozen analysis; re-run on RichSleep (dual-arm cardiorespiratory anchor) as an out-of-sample verification (main text R6).

*Primary metric (endpoint) family* - The frozen 9-endpoint set $m, d, e, d_n, d_l, d_s, e_e, e_s, e_m$ used for every specificity/timing/moderation test in this article. Reachability-cone and Meta-Noetic Jacobian (MNJ) endpoints were planned as secondary layers but were not run under the current analysis freeze.

*Rhythmic Variance Control (RVC)* - The NDT hypothesis under test: that rhythm-defined events (here, sleep spindles) act as transient "variance-control" or gating-precision events, producing a measurable, reproducible reconfiguration of local state-space geometry. *Internal validated result* for the ANPHY+BOAS `d_n` timing signature specifically (main text R3); RichSleep A2r of the same estimand is *inconclusive*. Treating that signature as a general RVC / gating-precision *mechanism* is a *speculative extension*.

= S - Z

*Sign-flip permutation test* - The primary hypothesis test used throughout this article: randomly flips the sign of each subject's mean delta $n=2000$ times and compares the observed grand mean against the resulting null distribution. Chosen over a parametric test because it directly tests the within-subject direction question without a distributional assumption; one-sample $t$-test and Wilcoxon signed-rank on the same subject means are reported as sensitivity checks, not as the primary $p$-value.

*Statistical method (BH-FDR)* - Benjamini-Hochberg false discovery rate correction (@benjamini1995fdr), applied fresh within each frozen test family in this article (18 tests for ANPHY+BOAS A1r/A2r; 9 tests for each RichSleep A1r/A2r family; 54 tests for Pass C; 126 fitted rows for the RichSleep EAP family). Threshold: $q < 0.05$ throughout. Composites $m,d,e$ are not independent of the stratified coordinates; FDR still treats them as separate tests.

*Subject-weighted estimand* - The correct unit of analysis for this article's uneven-event-count datasets: every event-level delta is first collapsed to one subject-mean delta before any test statistic is computed, so that subjects with many spindle events do not numerically dominate subjects with few.

*Thalamic Reticular Nucleus - Variance Gating (TRN-VG)* - A proxy interpretation, not a direct measurement: spindle/slow-oscillation events are treated as thalamocortical-gating *proxies* in this line of work, because none of the three PSG datasets can directly observe TRN activity. This article makes no claim beyond "TRN-VG-consistent," and does not claim TRN-VG is validated.

*YASA* - Yet Another Spindle Algorithm (@vallat2021yasa), the open-source automated sleep-staging and spindle-detection tool used to detect all spindle events in this article (C3-A2 channel, sigma 12-15 Hz, N2-only).

#bibliography("references.bib", style: "apa")
