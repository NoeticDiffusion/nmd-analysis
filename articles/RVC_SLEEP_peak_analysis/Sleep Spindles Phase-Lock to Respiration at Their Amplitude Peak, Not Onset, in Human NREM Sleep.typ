// RVC_SLEEP_peak_analysis manuscript — a corrected-permutation reanalysis of
// RichSleep's full spindle catalog that recovers population-level
// respiratory (and, more fragilely, cardiac) peak-phase coupling missed by
// the companion RVC_SLEEP article's onset-referenced test, plus a new,
// exploratory test of whether phase-alignment moderates the companion
// article's spindle-locked geometry effect. Content is drawn from
// results/rvc_sleep_20260710/{11,12,13}_*/ (diary 241/242/243).

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Sleep Spindles Phase-Lock to Respiration at Their Amplitude Peak, Not Onset, in Human NREM Sleep",
  short-title: "Spindle-peak, not onset, phase-locks to respiration",
  subtitle: "A corrected permutation reanalysis of a companion study's full spindle catalog recovers a robust respiratory coupling missed by an onset-referenced test, with a fragile cardiac counterpart and a weak secondary link to spindle-locked geometry",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "sleep spindles",
    "respiratory phase-locking",
    "cardiac phase-locking",
    "circular statistics",
    "embodied anchoring",
    "rhythmic variance control",
  ),
  article-type: "Research Article",
  abstract: [
    A companion three-dataset replication study (RVC_SLEEP) reported a null result for spindle-*onset* cardiac/respiratory phase-locking in human NREM sleep, using a two-stage hierarchical Rayleigh test on a 190-event, geometry-valid RichSleep subsample. An independent theoretical review of that result flagged the subsample as underpowered and recommended a pseudo-replication-safe permutation reanalysis on RichSleep's full raw spindle catalog rather than the geometry-filtered subsample. We reanalyzed all 23,029 detected RichSleep spindles (24 subjects) using a subject-specific random-phase-rotation permutation null and a first+second-harmonic omnibus statistic. Spindle-*onset* phase-locking remained null for both cardiac and respiratory channels at roughly 120$times$ the original sample size (all BH-FDR $q >= 0.48$). However, spindle-*peak* (amplitude-envelope-maximum) phase showed a robust, population-level respiratory coupling (pooled $R_1 = 0.045$, permutation $p = 0.0005$; second-order $R = 0.665$ across 24 subjects, $p = 7 times 10^(-6)$) and a weaker, less robust cardiac coupling (pooled $R_1 = 0.016$, $p = 0.02$; second-order $R = 0.462$, $p = 0.005$). Four independent robustness checks - duration-tercile stratification, leave-one-subject-out jackknife, deterministic split-half replication, and phase-convention calibration against the export's documented convention - confirmed the respiratory effect holds in every subsample tested, while the cardiac effect is duration-dependent and fails to replicate in one of two subject-split halves. We then asked whether alignment to this population-preferred respiratory phase (estimated on a held-out 99.2% of the catalog) moderates the size of the companion study's spindle-locked geometry change (the same 190 geometry-valid events): 2 of 18 pre-specified WLS-cluster tests survived BH-FDR (`d_l` endpoint, event-vs-pre-spindle-baseline mode, $q = 0.005$; `d` endpoint, same mode, $q = 0.021$), and a free circular-regression sensitivity check found the implied geometry-optimal phase within $11 degree$ of the independently-estimated timing-preferred phase for `d_l`. We conclude that respiratory phase locks to spindle peak, not onset, in human NREM sleep - resolving a design-driven false negative in the companion study - and report a fragile secondary signal that this coupling may also weakly moderate the spindle's own geometric consequence, framed here as an event-*timing* (not yet a confirmed event-*efficacy*) result for the sleep-EAP hypothesis, pending independent replication.
  ],
  author-summary: [
    A companion study found no evidence that sleep spindles occur at a preferred moment of the breathing or heartbeat cycle, using a small subsample of the available recordings. Re-running the same test with a corrected statistical method on the full 23,029-spindle catalog, we found that while the very *start* of a spindle indeed shows no preferred phase, the moment of its *strongest* activity does: spindles tend to peak roughly a third of the way toward full inhalation, consistently across 24 sleeping adults and several independent checks. A weaker, less consistent link to the heartbeat cycle was also found. We further found a fragile hint that how closely a spindle's peak matches this preferred breathing phase relates to the size of that spindle's effect on brain-state geometry, though this needs independent replication.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Data Curation, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted at submission.],
  data-availability: [RichSleep is described in @richsleep2026; formal access details will be added at submission (identical dataset to the companion RVC_SLEEP article's R6/R6b). NMD (NeuralManifoldDynamics) pipeline outputs and all analysis scripts are versioned in the analysis repository under `articles/RVC_SLEEP_peak_analysis/src/`, with per-script result tables under `articles/RVC_SLEEP_peak_analysis/results/`.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

#set heading(numbering: "1.")
#set math.equation(numbering: "(1)")

= Introduction <sec:intro>

A companion three-dataset study, *RVC_SLEEP* @langell2026rvcsleep, replicated a spindle-locked state-space reconfiguration (a rise in the `d_n` geometry endpoint) across three independent overnight-PSG datasets, then tested whether pre-event embodied-anchor (EAP) state moderates that effect. Its most mechanistically direct test (R6b, "Mål B") asked whether spindle *onset* preferentially occurs at a particular cardiac or respiratory phase, using RichSleep's phase-resolved export (`event_phase_v2`). That test was null at every level tested: 0/48 within-subject Rayleigh tests and 0/2 population-level second-order Rayleigh tests, on a 190-event, geometry-valid, N2-staged subsample.

An independent theoretical review of that result (internal document, `articles/Rythmic_Variance_Control_in_Sleep_theory/plan/02_response.md`) identified two problems with treating that null as conclusive. First, the 190-event subsample discards 99% of RichSleep's spindle catalog (23,029 raw detected events across the same 24 subjects) for reasons unrelated to the phase-locking question itself - the subsample requires N2-staging *and* geometry validity, neither of which the phase-locking hypothesis needs. Second, the review's own worked critique of an earlier *proposed* correction (shuffling subject labels on the pooled angle set) noted that such a shuffle leaves the pooled circular-uniformity statistic invariant and therefore does not construct a valid null at all; it instead recommended a subject-specific random-phase-rotation surrogate, among other pseudo-replication-safe alternatives. It further noted that two external, non-NDT PSG studies - Ghibaudo, Juventin, Buonviso et al. @ghibaudo2024spindle_resp and Schreiner, Petzka, Staudigl, Staresina @schreiner2023resp_memory - had already established population-level respiration-spindle phase-locking in independent human samples using a pooled, all-events design rather than the hierarchical per-subject-then-second-order design RVC_SLEEP used, raising the possibility that the RichSleep null was a design/power artifact rather than a genuine absence of coupling.

#netn-box(title: [Core question])[
  Does a corrected, pseudo-replication-safe permutation reanalysis of RichSleep's full spindle catalog recover population-level cardiac/respiratory phase-locking that the companion study's underpowered, two-stage design missed - and if so, at spindle onset, or at some other reference point in the event?
]

This article reports that reanalysis. It finds that onset-phase locking remains null even at full statistical power, but that spindle *peak* phase - the moment of maximal amplitude within the detected event, not its start - shows a robust population-level respiratory coupling and a more fragile cardiac one. Because a *timing* result (does phase predict *when* an event occurs, or here, what phase an event's peak lands at) is conceptually distinct from an *efficacy* result (does phase alignment change the *consequence* of an event that has already occurred), we additionally report a new, secondary analysis testing whether alignment to the population-preferred respiratory phase moderates the size of RVC_SLEEP's own spindle-locked geometry effect on the same 190 geometry-valid events used there.

= Theory <sec:theory>

== RVC/EAP tiering and the timing/efficacy distinction

Within Noetic Diffusion Theory (NDT), sleep spindles are treated as candidate *Rhythmic Variance Control* (RVC) events - endogenous, TRN-implemented, rhythm-defined windows of transient gating-precision change @langell2025ndt. The *Embodied Anchoring Principle* (EAP) is explicitly tiered as a secondary, Tier-2 extension of this core mechanism, proposing that peripheral bodily rhythms (cardiac, respiratory) can additionally condition the same latent landscape - "intended for a later wave of interoception-focused... studies," per the theory document's own framing, not a claim on equal evidentiary footing with the Tier-1 RVC core.

The reviewed reformulation (`02_response.md`) sharpens EAP's sleep-specific form into two separable, non-exclusive pathways, which this article adopts as its organizing distinction:

- *Event-timing pathway.* Does body phase help determine *when* an endogenous RVC event (here, a spindle, or a specific feature of it such as its amplitude peak) occurs, i.e. is event phase non-uniformly distributed relative to the cardiac/respiratory cycle?
- *Event-efficacy pathway.* Given that an event has occurred, does the body's phase at that moment change *how strongly* the event reconfigures state-space geometry - i.e. does phase-alignment moderate the event's own downstream consequence?

R2-R5 below test the timing pathway (replacing RVC_SLEEP's underpowered onset-referenced version with a corrected, full-catalog reanalysis); R6 tests the efficacy pathway directly, using RVC_SLEEP's own geometry-valid subsample.

== Corrected permutation-null construction

The statistic used throughout is the first-harmonic mean resultant length $R_1 = |chevron.l e^(i phi) chevron.r|$ (Rayleigh's classical concentration measure) plus a second-harmonic term $R_2 = |chevron.l e^(2 i phi) chevron.r|$, combined into an omnibus $T_2 = R_1^2 + R_2^2$ sensitive to axial/bimodal alternatives that $R_1$ alone can miss. Rather than an asymptotic Rayleigh $p$-value, every $p$-value here is a Monte Carlo permutation $p$-value against a *subject-specific random-phase-rotation* null: each permutation draws one i.i.d. $"Uniform"(0, 2 pi)$ rotation per subject and adds it to *all* of that subject's phases. This destroys any common population-level preferred phase while exactly preserving each subject's event count, within-subject clustering, and the unequal per-subject sampling that a naive pooled test would otherwise be vulnerable to - the pseudo-replication-safe alternative the theoretical review recommended in place of a subject-label shuffle. Full formulas are in `S1.1`.

= Methods <sec:methods>

== Dataset

RichSleep @richsleep2026 - the same 24-subject, whole-night PSG dataset used in RVC_SLEEP's R6/R6b - is the sole dataset analyzed here. No phase-resolved export exists for RVC_SLEEP's other two datasets (ANPHY, BOAS), so this article does not attempt a multi-dataset replication of the timing result; this is a stated limitation, not an oversight (Discussion).

== NMD pipeline and phase-resolved export

Analyses use RichSleep's `event_phase_v2` export (NMD run `neuralmanifolddynamics_RichSleep_20260709_100219`, identical to RVC_SLEEP's own RichSleep run; geometry is unaffected by the `resp_anchor_index` sign fix documented there, `S1.0`), which provides, per detected spindle, `onset_sec`, `peak_sec` (the amplitude-envelope maximum within the event), `duration_sec`, and cardiac/respiratory phase at both reference points (`phi_cardiac_onset`, `phi_cardiac_peak`, `phi_resp_onset`, `phi_resp_peak`). Phase conventions (documented in `phase_resolved_v1/run_meta.json`): $phi_"resp" in (-pi, pi)$, $0 =$ full inhale, $(-pi, 0) =$ rising/inhale, $(0, pi) =$ falling/exhale; $phi_"cardiac" in [0, 2pi)$, $0 =$ nearest R-peak, $pi =$ mid-cycle.

== Primary and secondary endpoint families

*Primary family* (well-powered, confirmatory): onset-phase, $times$ 2 channels (`phi_cardiac_onset`, `phi_resp_onset`) $times$ 2 samples (full catalog, $n=23029$; quality-filtered, `cardiac_phase_quality`$>=0.7$ and `resp_phase_quality`$=1.0$, $n=20877$) = 4 tests, BH-FDR corrected jointly (both $R_1$- and $T_2$-based $p$-values reported).

*Secondary/exploratory family* (not FDR-corrected against the primary family): the identical machinery applied to peak-phase channels (`phi_cardiac_peak`, `phi_resp_peak`) on the same two samples, plus all four channels re-applied to the original 190-event geometry-valid subsample for direct comparability with RVC_SLEEP's R6b numbers; a categorical cross-check (`inhale_at_onset` subject-level proportion vs. 0.5); and, retained for context, per-subject Rayleigh tests plus a second-order Rayleigh test on the 24 subject-level mean directions (both already pseudo-replication-safe by construction and unaffected by the permutation-null critique).

== Robustness protocol for the peak-phase finding

Four checks, run only once a candidate peak-phase effect was identified (R3), before it is treated as anything beyond exploratory:

1. *Phase-convention calibration* - re-verifying `inhale_at_onset`'s internal consistency against the documented convention, and reporting preferred peak-phase angles with an explicit physiological label.
2. *Onset-to-peak advance / duration-tercile stratification* - characterizing the onset-to-peak phase advance ($"peak_sec" - "onset_sec"$, converted to a phase rotation) and re-testing within three duration terciles (short/mid/long), to rule out a duration-tail-driven artifact.
3. *Leave-one-subject-out (LOSO) jackknife* - re-running both the second-order and pooled-permutation tests 24 times, once per dropped subject, to check for single-subject influence.
4. *Deterministic split-half replication* - re-running both tests on two independent 12-subject halves (alphabetically first vs. last), the strongest single check for whether an effect is population-general or driven by a subset of subjects.

== Secondary analysis: peak-phase alignment moderation of spindle-locked geometry

A new analysis (this article's only new statistical test, `13_peak_phase_alignment_moderation.py`) asks whether alignment to the population-preferred respiratory peak phase moderates RVC_SLEEP's own spindle-locked geometry effect. To avoid circularity, the population-preferred phase $mu_("resp,peak")$ is estimated as the subject-balanced second-order circular mean of `phi_resp_peak` on the *held-out* 22,839 events (the full catalog minus the 190 geometry-valid events used below - under 1% of the catalog, costing negligible power). For each of the 190 geometry-valid events, $"alignment"_e = cos(phi_("resp,peak",e) - mu_("resp,peak")) in [-1, 1]$ (high when that event's peak lands at the population-preferred phase). This is regressed against the geometry delta ($"endpoint" - "baseline"$, `event_control` or `event_prefar` mode, identical to RVC_SLEEP's Mål C machinery: WLS with weights $1"/"n_"events,subject"$, cluster-robust SE by subject, mean-centered nuisance covariates) across all 9 geometry endpoints $times$ 2 delta modes = 18 tests, BH-FDR corrected jointly - the identical family size/design as RVC_SLEEP's own Mål C, for direct comparability. Only the validated respiratory channel is tested (cardiac-peak is excluded a priori, having already been downgraded to fragile in this article's own R4-R5). A secondary, exploratory circular-regression check ($"delta" ~ cos(phi_("resp,peak")) + sin(phi_("resp,peak")) + "covariates"$, not folded into the 18-test family) additionally asks whether the data-implied "geometry-optimal" phase direction coincides with the independently-estimated timing-preferred phase $mu_("resp,peak")$.

= Results <sec:results>

== R1: Data coverage <sec:r1>

#figure(
  kind: table,
  clean-table(
    columns: (1.6fr, 1fr, 1fr),
    align: (left, center, center),
    inset: 5pt,
    table.header([*Sample*], [*$N$ subj.*], [*$N$ events*]),
    [Full raw catalog (`event_phase_v2`)], [24], [23,029],
    [Quality-filtered (`cardiac_phase_quality`$>=0.7$, `resp_phase_quality`$=1.0$)], [24], [20,877],
    [Geometry-valid, N2-staged subsample (RVC_SLEEP R6b's population)], [24], [190],
  ),
  caption: [Sample coverage. The geometry-valid subsample is the same 190-event population RVC_SLEEP's Mål B/C and this article's R6 alignment-moderation test use; the full and quality-filtered samples are new to this article's R2-R5.]
) <tab-coverage>

== R2: Onset-phase locking remains null at full power <sec:r2>

The primary, well-powered family confirms RVC_SLEEP's onset-phase null, now at up to 120$times$ the original sample size (Table @tab-onset-null): no channel/sample combination survives BH-FDR on either the $R_1$- or $T_2$-based permutation $p$-value (minimum $q = 0.483$ for $R_1$; minimum $q = 0.106$ for $T_2$).

#figure(
  kind: table,
  clean-table(
    columns: (0.9fr, 1fr, 0.7fr, 0.9fr, 0.9fr, 0.9fr, 0.9fr),
    align: (left, left, center, center, center, center, center),
    inset: 4.5pt,
    table.header([*Sample*], [*Channel*], [*$N$*], [*pooled $R_1$*], [*perm $p$ ($R_1$)*], [*FDR $q$*], [*FDR $q$ ($T_2$)*]),
    [Full catalog], [`phi_cardiac_onset`], [23,029], [0.0093], [0.353], [0.482], [0.109],
    [Full catalog], [`phi_resp_onset`], [23,029], [0.0189], [0.151], [0.482], [0.106],
    [Quality-filtered], [`phi_cardiac_onset`], [20,877], [0.0043], [0.827], [0.827], [0.116],
    [Quality-filtered], [`phi_resp_onset`], [20,877], [0.0153], [0.362], [0.482], [0.109],
  ),
  caption: [Primary family: corrected subject-rotation permutation test, spindle-onset phase. No BH-FDR survivor on either statistic. Source: `results/rvc_sleep_20260710/11_richsleep_maalb_corrected/molB_primary_corrected_permutation.csv`.]
) <tab-onset-null>

On the original 190-event geometry-valid subsample, onset-phase remains null too ($R_1 = 0.050$, $p = 0.692$ cardiac; $R_1 = 0.021$, $p = 0.929$ respiratory) - consistent with RVC_SLEEP's own R6b numbers on that subsample, confirming this reanalysis is not simply finding a different result because of a different statistical method applied to the same small sample; the change in conclusion (R3) comes specifically from the ~120-fold larger, non-geometry-filtered catalog.

== R3: Spindle-peak respiratory phase is robustly population-locked <sec:r3>

In contrast, the identical machinery applied to spindle-*peak* phase (secondary/exploratory family, not folded into R2's FDR correction) shows a clear, population-level respiratory effect and a weaker cardiac one (Table @tab-peak-primary):

#figure(
  kind: table,
  clean-table(
    columns: (0.9fr, 1fr, 0.7fr, 0.9fr, 0.9fr),
    align: (left, left, center, center, center),
    inset: 4.5pt,
    table.header([*Sample*], [*Channel*], [*$N$*], [*pooled $R_1$*], [*perm $p$ ($R_1$)*]),
    [Full catalog], [`phi_cardiac_peak`], [23,029], [0.0159], [0.0200],
    [Full catalog], [`phi_resp_peak`], [23,029], [0.0453], [0.0005],
    [Quality-filtered], [`phi_cardiac_peak`], [20,877], [0.0145], [0.0675],
    [Quality-filtered], [`phi_resp_peak`], [20,877], [0.0418], [0.0030],
  ),
  caption: [Secondary/exploratory family: corrected subject-rotation permutation test, spindle-*peak* phase. Reported descriptively (not BH-FDR-corrected against R2's primary family, per the pre-specified analysis plan). Source: `results/rvc_sleep_20260710/11_richsleep_maalb_corrected/molB_secondary_exploratory_permutation.csv`.]
) <tab-peak-primary>

The population-level, second-order Rayleigh test on the 24 subject-mean directions (already pseudo-replication-safe by construction, unaffected by the primary-family permutation-null critique) agrees, and additionally survives BH-FDR jointly with the onset-phase second-order tests (Table @tab-second-order):

#figure(
  kind: table,
  clean-table(
    columns: (1.3fr, 0.9fr, 0.9fr, 1fr),
    align: (left, center, center, center),
    inset: 4.5pt,
    table.header([*Channel*], [*$R$ (24 subj.)*], [*$p$*], [*FDR $q$*]),
    [`phi_cardiac_onset`], [0.273], [0.168], [0.336],
    [`phi_resp_onset`], [0.403], [0.019], [0.050],
    [`phi_cardiac_peak`], [0.462], [0.0049], [0.0197],
    [`phi_resp_peak`], [0.665], [$7 times 10^(-6)$], [$5.5 times 10^(-5)$],
  ),
  caption: [Second-order (population-level) Rayleigh test on the 24 subject-level mean-direction angles, full catalog. `phi_resp_peak` is the only channel/reference-point combination surviving BH-FDR at a conventional threshold by a wide margin. Source: `results/rvc_sleep_20260710/11_richsleep_maalb_corrected/molB_second_order_rayleigh.csv`.]
) <tab-second-order>

Per-subject, `phi_resp_peak` shows FDR-significant within-subject concentration in 8/24 subjects (median $R = 0.071$) and `phi_cardiac_peak` in 1/24 (median $R = 0.036$) - versus 7/24 and 0/24 for the corresponding onset-phase channels - consistent with a genuine, if individually modest, population-level effect rather than a few strongly-locked subjects driving the pooled statistic (Fig. @fig-rose, @fig-per-subject).

#figure(
  image("figures/fig1_resp_peak_rose_plot.svg", width: 62%),
  caption: [Pooled circular histogram of `phi_resp_peak` across all 23,029 events. Arrow: mean direction ($-122.6 degree$, i.e. rising/inhale, 32% of the way to full inhale-peak), scaled to $R_1 = 0.045$.]
) <fig-rose>

#figure(
  image("figures/fig2_per_subject_resp_vs_cardiac.svg", width: 90%),
  caption: [Per-subject mean peak-phase direction (24 points; radial position = within-subject $R$). Respiratory phase (left) shows tighter angular clustering across subjects than cardiac phase (right), visualizing the dissociation quantified in Tables @tab-second-order and @tab-split-half.]
) <fig-per-subject>

#netn-box(title: [R3 summary])[
  Spindle onset-phase locking is null at full statistical power (R2), but spindle *peak*-phase is population-level, subject-consistent, and second-order-significant for respiration ($R = 0.665$, $p = 7 times 10^(-6)$) and, more weakly, cardiac phase ($R = 0.462$, $p = 0.005$). This resolves the theoretical review's H1 (power/design-artifact hypothesis for the companion study's null): the effect exists, and the companion study's two-stage, onset-referenced, geometry-filtered design was underpowered *and* referenced the wrong point in the event to detect it.
]

== R4: Robustness audit <sec:r4>

*Phase-convention calibration.* `inhale_at_onset`'s internal consistency check passes (mean $phi_"resp,onset" = -1.587$ rad when `inhale_at_onset`$=1$, expected negative; $+1.588$ rad when $=0$, expected positive), confirming no schema drift from the documented convention. The preferred peak-phase angles: respiratory $-122.6 degree$ (inhale, rising, 32% of the way to full inhale-peak); cardiac $40.6 degree$ after the nearest R-peak.

*Onset-to-peak advance and duration-tercile stratification.* Median time-to-peak is 0.43 s (correlation with duration $r = 0.842$, confirming peak $approx$ event midpoint, as expected for an amplitude-envelope-peak detector). The respiratory onset-to-peak phase advance is tight and consistent with a physiologically plausible $approx 13$-$16$ breaths/min local respiratory rate (median advance 0.669 rad, implied period 4.04 s); the cardiac advance is far more dispersed (median 1.34 rad, std 2.05), because time-to-peak often spans multiple RR intervals. Critically, the respiratory peak-phase effect holds in *every* duration tercile (Table @tab-tercile, Fig. @fig-tercile), ruling out a duration-tail-driven artifact; the cardiac effect is significant only in the shortest-duration tercile.

#figure(
  kind: table,
  clean-table(
    columns: (1fr, 1fr, 0.7fr, 0.9fr, 0.9fr),
    align: (left, left, center, center, center),
    inset: 4.5pt,
    table.header([*Tercile*], [*Channel*], [*$N$*], [*$R_1$*], [*perm $p$*]),
    [Short (0.50-0.72 s)], [`phi_resp_peak`], [7,738], [0.0455], [0.0005],
    [Short (0.50-0.72 s)], [`phi_cardiac_peak`], [7,738], [0.0267], [0.0235],
    [Mid (0.72-1.03 s)], [`phi_resp_peak`], [7,654], [0.0505], [0.0010],
    [Mid (0.72-1.03 s)], [`phi_cardiac_peak`], [7,654], [0.0152], [0.2699],
    [Long (1.04-8.21 s)], [`phi_resp_peak`], [7,637], [0.0431], [0.0090],
    [Long (1.04-8.21 s)], [`phi_cardiac_peak`], [7,637], [0.0103], [0.3038],
  ),
  caption: [Duration-tercile-stratified re-test. Respiratory peak-phase locking survives in all three terciles; cardiac only in the shortest. Source: `results/rvc_sleep_20260710/12_richsleep_maalb_peak_phase_deepdive/check2_duration_tercile_stratified.csv`.]
) <tab-tercile>

#figure(
  image("figures/fig3_duration_tercile_robustness.svg", width: 68%),
  caption: [Pooled $R_1$ by duration tercile and channel (asterisk = perm $p<0.05$ within-tercile). Respiratory locking is stable across the full duration range; cardiac locking decays with duration.]
) <fig-tercile>

*Leave-one-subject-out jackknife.* For `phi_resp_peak`, the second-order test remains $p<0.05$ in all 24 leave-one-out reruns (range $p in [0.0000, 0.0000]$) and the pooled-permutation test remains $p<0.05$ in all 24 reruns (range $[0.0020, 0.0020]$); no single subject is disproportionately influential (dropping the most influential subject, `sub-xn017`, still gives $p = 0.0000$). For `phi_cardiac_peak`, the second-order test remains $p<0.05$ in 24/24 reruns (range $[0.0014, 0.0105]$), but the pooled-permutation test loses significance in 2/24 reruns (range $[0.0040, 0.0679]$) - a first sign of fragility.

*Deterministic split-half replication.* Splitting subjects alphabetically into two independent 12-subject halves gives the clearest dissociation (Table @tab-split-half, Fig. @fig-splithalf): respiratory peak-phase locking replicates in *both* halves independently (half A: $R_1 = 0.059$, $p = 0.004$; half B: $R_1 = 0.037$, $p = 0.012$); cardiac peak-phase locking replicates *only* in half B ($R_1 = 0.019$, $p = 0.032$) and is null in half A ($R_1 = 0.012$, $p = 0.530$).

#figure(
  kind: table,
  clean-table(
    columns: (1fr, 1fr, 0.8fr, 0.9fr, 0.9fr, 0.9fr),
    align: (left, left, center, center, center, center),
    inset: 4.5pt,
    table.header([*Half*], [*Channel*], [*$N$ events*], [*pooled $R_1$*], [*perm $p$*], [*2nd-order $R$ ($p$)*]),
    [A (sub-xn001-012)], [`phi_resp_peak`], [9,532], [0.0594], [0.0040], [0.714 (0.0011)],
    [A (sub-xn001-012)], [`phi_cardiac_peak`], [9,532], [0.0116], [0.5302], [0.292 (0.368)],
    [B (sub-xn013-024)], [`phi_resp_peak`], [13,497], [0.0371], [0.0120], [0.624 (0.0067)],
    [B (sub-xn013-024)], [`phi_cardiac_peak`], [13,497], [0.0193], [0.0320], [0.640 (0.0051)],
  ),
  caption: [Deterministic split-half self-replication. Source: `results/rvc_sleep_20260710/12_richsleep_maalb_peak_phase_deepdive/check4_split_half_replication.csv`.]
) <tab-split-half>

#figure(
  image("figures/fig4_split_half_replication.svg", width: 90%),
  caption: [Split-half comparison, both channels. Respiratory peak-phase locking is present in both independent halves; cardiac peak-phase locking is present only in half B.]
) <fig-splithalf>

== R5: Respiratory-vs-cardiac dissociation <sec:r5>

#netn-box(title: [R4-R5 summary])[
  Respiratory peak-phase locking is robust: it survives duration-tercile stratification (all three terciles), leave-one-subject-out (24/24 reruns), and deterministic split-half replication (both halves independently). Cardiac peak-phase locking is fragile: it is significant only in the shortest duration tercile, loses pooled significance in 2/24 leave-one-out reruns, and fails to replicate in one of the two split halves entirely. The two channels are read differently going forward: respiratory peak-phase locking is treated as an established, this-article internally-validated result; cardiac peak-phase locking is reported as exploratory and not built upon further (R6 tests only the respiratory channel).
]

== R6: Peak-phase alignment moderation of spindle-locked geometry <sec:r6>

Using the held-out (22,839-event) population-preferred phase $mu_("resp,peak") = -128.4 degree$ ($R = 0.666$, 24 subjects) - closely consistent with the full-catalog pooled estimate in R3 - as the reference direction, alignment to that phase was tested as a moderator of the 190-event geometry-valid subsample's spindle-locked delta, across 9 endpoints $times$ 2 delta modes (Table @tab-alignment). 2/18 tests survive BH-FDR, both in the `event_prefar` (within-spindle timing) delta mode:

#figure(
  kind: table,
  clean-table(
    columns: (1fr, 0.6fr, 0.7fr, 0.7fr, 0.8fr, 0.9fr),
    align: (left, center, center, center, center, center),
    inset: 4.5pt,
    table.header([*Delta mode*], [*Endp.*], [*$N$ events*], [*coef*], [*$p$*], [*FDR $q$*]),
    [`event_prefar`], [`d`], [160], [$+0.243$], [$0.0023$], [$0.021$],
    [`event_prefar`], [`d_l`], [160], [$+0.184$], [$0.0003$], [$0.005$],
    [`event_prefar`], [`e`], [160], [$+0.136$], [$0.035$], [$0.139$ (ns)],
    [`event_prefar`], [`d_n`], [160], [$+0.353$], [$0.036$], [$0.139$ (ns)],
    [`event_control`], [all 9 endpoints], [172], [-], [$0.06$-$0.73$], [$>=0.18$ (ns)],
  ),
  caption: [Strongest rows of the 18-test alignment-moderation family (full 18-row table in `S2.0`); WLS-cluster, weights $1"/"n_"events,subject"$, cluster-robust SE by subject. Positive coefficients: closer alignment to the population-preferred respiratory-peak phase predicts a *larger* within-spindle timing rise on `d` and `d_l`. Source: `results/rvc_sleep_20260710/13_peak_phase_alignment_moderation/resp_peak_alignment_moderation.csv`.]
) <tab-alignment>

The companion per-subject-slope sensitivity check is mixed: the Wilcoxon signed-rank test on subject-level slopes agrees for both survivors (`d`: $p = 0.044$; `d_l`: $p = 0.014$), but the one-sample $t$-test does not (`d`: $p = 0.077$; `d_l`: $p = 0.105$) and the companion sign-flip permutation test only agrees for `d` ($p=0.068$, borderline) and not `d_l` ($p=0.10$) - a genuinely mixed robustness picture, reported as such rather than smoothed over (`S3`).

The secondary, exploratory circular-regression check finds that the data-implied "geometry-optimal" phase direction for `d_l` ($-117.4 degree$) lies within $10.9 degree$ of the independently-estimated timing-preferred phase $mu_("resp,peak")$ ($-128.4 degree$) - i.e. the phase that makes a spindle's own within-spindle geometry rise largest is close to the same phase spindles already preferentially peak at (Fig. @fig-alignment). The corresponding `d` endpoint shows a looser but still same-quadrant correspondence ($-97.2 degree$, $31.1 degree$ from $mu_("resp,peak")$).

#figure(
  image("figures/fig5_alignment_moderation_scatter.svg", width: 68%),
  caption: [Alignment ($cos(phi_("resp,peak")-mu_("resp,peak"))$) vs. `d_l` timing delta (`event_prefar` mode), the strongest of the 18 alignment-moderation tests. Points colored by subject; dashed line is an unweighted display trend, not the inferential WLS-cluster fit reported in Table @tab-alignment.]
) <fig-alignment>

#netn-box(title: [R6 summary - fragile, secondary])[
  A small, exploratory secondary family (2/18 BH-FDR survivors, mixed agreement across three sensitivity checks, $N=190$ events) provides weak evidence that respiratory-peak alignment moderates the size of the companion study's within-spindle geometry rise, and that the phase which appears to maximize this effect is close to the population's own preferred spindle-peak phase. This is reported as a *timing*-pathway-adjacent hint at an *efficacy* effect, not as a confirmed event-efficacy result (Theory) - it requires independent replication before being treated as established.
]

= Discussion <sec:discussion>

== Primary finding: peak, not onset, is the right reference point

The companion RVC_SLEEP study's onset-referenced Mål B test was null, and this reanalysis confirms that null holds even at $approx 120 times$ the original sample size (R2) - the onset-phase null is not a power artifact. What *was* a power/design artifact, per the theoretical review's H1, was testing the wrong reference point at insufficient power: spindle *peak* phase, tested on the full catalog with a corrected permutation null, shows a robust, population-level respiratory coupling (R3-R5) that four independent robustness checks confirm holds outside the specific subsample and test design that produced the original null. This is best read as resolving a design-driven false negative, not as contradicting the companion study's own reported result on its own subsample and reference point - Table @tab-onset-null's geometry-valid-subsample row reproduces RVC_SLEEP's R6b numbers essentially exactly.

== Relation to external literature

Ghibaudo et al. @ghibaudo2024spindle_resp report population-level, non-uniform spindle-*occurrence* phase relative to the respiratory cycle in an independent 20-subject PSG sample, using a pooled, all-events design; Schreiner et al. @schreiner2023resp_memory report that SO-spindle-complex *timing* couples to respiratory phase (peaking near inspiration) and, further, that coupling strength predicts memory-reactivation fidelity. Both operationalize spindle *timing* as an onset- or occurrence-referenced quantity, and both report inspiration- or peri-inspiration-favoring preferred phases - broadly consistent in direction with this article's peak-phase preferred angle ($-122.6 degree$, i.e. the rising/inhale limb, 32% of the way to full inhale-peak), though not directly comparable in reference point (their onset/occurrence vs. this article's envelope peak) or in the exact phase convention used. This article's own onset-phase test remains null on the same dataset, which is itself informative: it is not that RichSleep lacks any respiratory-spindle coupling detectable by a corrected, well-powered test (as the two external studies would predict it should), but that the coupling in this dataset is specifically carried by the envelope peak rather than the onset - a genuine, reportable difference in *where within the event* the coupling is strongest, not a failure to replicate the general phenomenon. A separate line of work reports that respiration-brain coupling undergoes a *phase shift*, and becomes *more* consistent rather than simply weaker, moving from wakefulness into deeper sleep @progneurobio2025_resp_wake_sleep - a state-dependent-reorganization picture broadly compatible with finding a genuine, reference-point-specific coupling in NREM sleep rather than either a simple continuation or a simple absence of a wake-state pattern.

== Interpreting R6 via the timing/efficacy distinction

Per the timing/efficacy framing (Theory), R3-R5 establish an event-timing result: respiratory phase predicts a feature of *when* (or more precisely, at what phase) a spindle's peak occurs. R6 asks the logically separate event-efficacy question: does that phase additionally predict how strongly the spindle reconfigures geometry? The answer here is a fragile "maybe": 2/18 tests survive family-wise correction, one sensitivity check (Wilcoxon) agrees for both, two others (t-test, sign-flip permutation) do not fully agree, and the finding emerged from testing only *after* the timing result was already established (a secondary analysis motivated by, not independent of, R3-R5). Per the theoretical review's own outcome table, this pattern - "timing effect present, efficacy effect small/inconsistent" - is one of several a priori plausible readings, and is treated here as exactly that: a hint worth a dedicated, pre-registered, independently-replicated test, not a second confirmed finding riding on the first.

== Limitations

- *Post-hoc/exploratory origin.* The peak-phase finding (R3) emerged from a secondary sweep run specifically because the pre-specified onset-phase test was null; while the four robustness checks in R4 were run independently of that motivation, the initial discovery was not pre-registered.
- *Single-dataset.* RichSleep is the only one of RVC_SLEEP's three datasets with a phase-resolved export; ANPHY and BOAS cannot be used to test cross-dataset replication of the timing result.
- *No endogenous-strength covariate.* Neither R3-R5 nor R6 include an SO-spindle-coupling or spindle-amplitude covariate (not present in the current NMD export schema), so this article cannot yet distinguish "phase moderates a spindle's own strength, which independently moderates geometry" from a more direct phase-geometry link, per the theoretical review's own recommended measurement model (`02_response.md` S5).
- *Geometry-outcome resolution ceiling.* RVC_SLEEP's `coords_9d` geometry export is 1 value per 30 s epoch (`phase_resolved_v1/run_meta.json`); R6's alignment-moderation test inherits this ceiling, so it cannot itself be phase-resolved beyond the resolution of its 190-event, epoch-level geometry outcome, independent of how precisely phase itself is measured.
- *R6 is exploratory and fragile.* $N=190$ events is modest, only 2/18 tests survive FDR, and the companion sensitivity checks disagree on one of the two survivors (`S3`); this is stated plainly rather than downplayed.

== Conclusion

Sleep spindles' amplitude peak - not their onset - phase-locks to the respiratory cycle in human NREM sleep, a robust, population-level, subject-consistent effect recovered by a corrected, full-catalog permutation reanalysis of a companion study's original, underpowered null. A weaker, duration-dependent, and only partially-replicating cardiac counterpart is also present. A new, exploratory secondary analysis provides fragile evidence that alignment to this preferred phase may additionally moderate the size of the companion study's own spindle-locked geometry effect, framed here as an event-timing result with a tentative, not-yet-confirmed link to event efficacy - a distinction this article's theoretical framing treats as essential to avoid overclaiming a mechanistic role for phase beyond what the data currently support.

= Acknowledgements

The author thanks the RichSleep dataset contributors for the underlying recordings, and acknowledges the external theoretical review (`02_response.md`) whose specific, falsifiable recommendations directly motivated this reanalysis.

#bibliography("references.bib", style: "apa")
