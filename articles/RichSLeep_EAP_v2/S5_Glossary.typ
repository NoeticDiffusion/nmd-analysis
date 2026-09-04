// S5 Glossary — RichSleep_EAP_v2

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S5 Glossary",
  short-title: "S5 Glossary - RichSleep_EAP_v2",
  subtitle: "Terms specific to this article, plus carried-over NDT/RVC/EAP and companion-article terms used throughout",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S5.0 Terms new to this article

#figure(
  clean-table(
    columns: (1.3fr, 3fr),
    align: (left, left),
    inset: 5pt,
    table.header([*Term*], [*Definition*]),
    ["State determines carrier"], [The framing (`articles/Rythmic_Variance_Control_in_Sleep_theory/plan/02_response.md`, S8) that different sleep stages recruit different endogenous rhythmic events (N2 spindles, N3 slow oscillations, REM theta), and that autonomic phase-locking, if it reflects a general property of the underlying gating/denoising mechanism, should be testable - with possibly different strength - across all three, using one identical statistical test (R2).],
    [Carrier], [One of the three endogenous, stage-specific rhythmic events tested here for autonomic phase-locking: the N2 sleep spindle, the N3 slow oscillation (SO), and the REM-theta epoch. "Cross-carrier" = the same test applied to more than one carrier.],
    [SO trough / SO upstate], [Two reference points within a detected N3 slow oscillation at which cardiac/respiratory phase is measured: the trough (most negative deflection) and the upstate (rising transition following the trough) - analogous to spindle onset/peak's two reference points in the companion article.],
    [Non-event risk set (`non_event_risk_v1`)], [NMD's purpose-built sample of N2-stage timepoints, drawn per subject (stratified by time-of-night quartile, excluding a margin around every real spindle event), each carrying its own cardiac/respiratory phase - used as the "control" population in Test A's case-control hazard-style test (distinct from a parametric uniform-circular null).],
    [Case-control logistic regression (Test A)], [`is_case ~ cos(phase) + sin(phase)`, cluster-robust by subject, comparing real spindle onsets (cases) against the non-event risk set (controls); tests whether onset phase differs from the real, non-uniform N2 exposure distribution rather than an assumed-uniform one.],
    [Circular time-shift surrogate (Test B)], [A null construction that shifts each subject's own continuous phase stream by a random lag and re-reads phase at the same real event times, preserving the exact non-sinusoidal waveform/autocorrelation of that subject's own signal - a different null-construction principle from both Test A and the subject-rotation permutation (Null 0).],
    [Null 0 / Test A / Test B], [Article-specific labels for, respectively: the subject-rotation permutation test (unchanged from the companion article, relabeled here for direct comparison), the case-control logistic regression, and the circular time-shift surrogate - the three independent null constructions compared in R3.],
    [Intrinsic spindle strength ($"qe"$)], [A per-event measure of how strong/well-formed a detected spindle is, operationalized three ways: log1p-transformed sigma-power z-score (primary), log1p-transformed amplitude, and untransformed sigma-power z-score (robustness).],
    [SO-spindle coupling], [Whether a detected spindle has a temporally-matched slow-oscillation partner (`so_partner_missing`$=0$) and, if so, the strength of that coupling (`so_spindle_coupling_score`) and the SO's own amplitude (`so_amplitude`) - available for only 11.8% of all spindles and 25/190 (13.2%) of the geometry-valid subsample.],
    [Intrinsic-strength $times$ alignment interaction], [The regression term testing whether `resp_peak_alignment`'s effect on spindle-locked geometry delta depends on the spindle's own intrinsic strength ($"qe"$) - logically distinct from either variable's own main effect, and from the companion article's main-effect-only alignment-moderation test.],
    [SO-coupled descriptive check], [A small ($N=25$ events/15 subjects), explicitly non-confirmatory correlational check (no interaction model, no BH-FDR family) between geometry delta and SO-coupling measures, reported for completeness/future hypothesis generation, not as a test result.],
  ),
  caption: [Terms introduced or newly operationalized in this article.]
) <tab-glossary-new>

= S5.1 Carried-over NDT/RVC/EAP and companion-article terms

#figure(
  clean-table(
    columns: (1.3fr, 3fr),
    align: (left, left),
    inset: 5pt,
    table.header([*Term*], [*Definition*]),
    [Noetic Diffusion Theory (NDT)], [The parent geometric framework for neural state dynamics within which RVC and EAP are formulated (@langell2025ndt); not itself tested by this article.],
    [Rhythmic Variance Control (RVC)], [The Tier-1 NDT mechanism under which endogenous, rhythm-defined events (spindles, SOs, REM-theta bursts) are treated as candidate transient gating-precision-change windows.],
    [Embodied Anchoring Principle (EAP)], [The Tier-2 NDT extension proposing that peripheral bodily rhythms can additionally condition the same latent landscape RVC events act on; this article's cross-carrier sweep and qe-interaction test are both relevant to (but not individually dispositive of) this principle.],
    [Onset-phase vs. peak-phase], [Two distinct reference points within a detected spindle event (companion article, @langell2026rvcsleeppeak): `onset_sec` vs. `peak_sec` (time of maximum amplitude) - this article's N2-spindle rows in R2 test both, reproducing the companion article's own numbers exactly.],
    [Event-timing pathway], [The hypothesis that body phase helps determine *when* an endogenous RVC event (or a specific feature of it) occurs - operationalized here as non-uniformity of event phase relative to the cardiac/respiratory cycle, tested across all five carrier/reference-point conditions (R2-R3).],
    [Event-efficacy pathway], [The logically separate hypothesis that, given an event has occurred, the body's phase at that moment changes *how strongly* the event reconfigures state-space geometry - the companion article's alignment-moderation main-effect test, sharpened here into an interaction test with an intrinsic-strength covariate (R4).],
    [Subject-rotation permutation null], [A Monte Carlo null distribution (unchanged from the companion article) constructed by adding one i.i.d. $"Uniform"(0,2pi)$ rotation per subject to all of that subject's phases, repeated $n_"perm"$ times; destroys any common population-level preferred phase while exactly preserving each subject's event count and within-subject clustering.],
    [Harmonic statistic ($R_1$, $R_2$, $T_2$)], [$R_1$: first-harmonic mean resultant length (classical Rayleigh concentration). $R_2$: second-harmonic mean resultant length (sensitive to axial/bimodal structure). $T_2 = R_1^2+R_2^2$: an omnibus statistic combining both, used throughout this article's and the companion article's permutation tests.],
    [Held-out estimation], [Estimating a population parameter (here, $mu_("resp,peak")$, recomputed self-containedly in this article, `S1.4`) on a data subset that excludes the events subsequently used to test a hypothesis involving that parameter, to avoid circularity/data leakage.],
    [(Peak-phase) alignment], [$"resp_peak_alignment"_e = cos(phi_e - mu)$ for a given event $e$'s respiratory-peak phase $phi_e$ and the held-out population-preferred phase $mu$ - unchanged from the companion article, used here as one of two interacting terms rather than as a standalone main effect.],
    [WLS-cluster (`fit_wls_cluster`)], [Weighted least squares with weights $1"/"n_"events,subject"$ (equalizing each subject's total contribution regardless of event count) and cluster-robust standard errors by subject; the shared regression machinery for the qe-interaction model, inherited unchanged from both companion articles.],
    [`d`, `d_n`, `d_l`, `d_s`, `e`, `e_e`, `e_s`, `e_m`, `m`], [The 9 primary geometry endpoints inherited from the companion articles' `coords_9d` state-space representation; not redefined here.],
    [`event_control` vs. `event_prefar` delta mode], [Two ways of computing a geometry "delta" for a given event, inherited unchanged from the companion articles: `event_control` = event value minus a matched control-window median; `event_prefar` = event value minus the same event's own pre-spindle baseline ("far") window value.],
    [BH-FDR], [Benjamini-Hochberg false discovery rate correction (@benjamini1995fdr), applied within each pre-specified test family (10-test cross-carrier family, `S1.3`; 18-test qe-interaction family, applied separately per qe operationalization, `S1.5`) but not across families.],
  ),
  caption: [Terms inherited from the companion RVC_SLEEP/RVC_SLEEP_peak_analysis articles and the broader NDT framework, retained here without modification unless otherwise noted.]
) <tab-glossary-carried>

#bibliography("references.bib", style: "apa")
