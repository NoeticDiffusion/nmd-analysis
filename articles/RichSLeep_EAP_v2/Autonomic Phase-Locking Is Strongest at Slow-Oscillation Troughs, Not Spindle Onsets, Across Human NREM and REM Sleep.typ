// RichSleep_EAP_v2 manuscript — a cross-carrier ("state determines carrier")
// extension of the RVC_SLEEP / RVC_SLEEP_peak_analysis companion articles,
// built on NMD's 2026-07-12/13 RichSleep delivery (per-event spindle
// strength + SO coupling, a continuous 10 Hz phase stream, phase-resolved
// N3-slow-oscillation and REM-theta catalogs, and a purpose-built non-event
// risk set). Content is drawn from
// results/rvc_sleep_v2_20260713/{01..05}_*/ (diary entry pending).

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Autonomic Phase-Locking Is Strongest at Slow-Oscillation Troughs, Not Spindle Onsets, Across Human NREM and REM Sleep",
  short-title: "SO troughs, not spindle onsets, drive autonomic phase-locking",
  subtitle: "A cross-carrier RichSleep survey with two independent onset-hazard nulls and a null test of whether intrinsic spindle strength moderates spindle-locked geometry",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "sleep spindles",
    "slow oscillations",
    "REM theta",
    "respiratory phase-locking",
    "cardiac phase-locking",
    "point-process hazard model",
    "embodied anchoring",
  ),
  article-type: "Research Article",
  abstract: [
    A companion study (RVC_SLEEP_peak_analysis) found that sleep-spindle *peak* - not onset - phase-locks to respiration in human NREM sleep, using a corrected permutation reanalysis of RichSleep's full spindle catalog. NMD's newest RichSleep delivery adds four further data products: per-event intrinsic spindle strength and slow-oscillation(SO)-spindle coupling, a continuous 10 Hz cardiac/respiratory/theta phase stream, phase-resolved N3-SO ($N=42,009$) and REM-theta ($N=2,412$) catalogs, and a purpose-built non-event risk set ($N=66,827$) for hazard-style testing. We used these to run one consistent phase-locking test (subject-rotation permutation, first+second-harmonic omnibus statistic) across five sleep "carriers" spanning three stages, to test two further, independent nulls for the previously-ambiguous spindle-onset question, and to test whether intrinsic spindle strength moderates the companion study's respiratory-alignment-to-geometry effect. Slow-oscillation phase-locking was the strongest effect in the dataset by a wide margin (pooled $R_1 = 0.050$-$0.064$; second-order $R = 0.65$-$0.75$ across 24 subjects; all $p < 10^(-5)$, both trough and upstate, both channels) - exceeding even the already-robust N2-spindle-peak respiratory result ($R_1 = 0.045$, second-order $R = 0.665$) that motivated this article. REM-theta phase-locking was null on both channels (all raw $p > 0.32$). For spindle onset, three independent null constructions disagreed: a subject-rotation permutation gave a borderline, family-dependent result (respiratory raw $p = 0.027$); a case-control test against the new non-event risk set found a highly significant but tiny respiratory effect ($p = 4 times 10^(-7)$) and no cardiac effect ($p = 0.38$); a circular time-shift surrogate found the reverse (cardiac $p = 0.004$, respiratory $p = 1.0$). We report this three-way disagreement as-is rather than resolving it by selecting a preferred null. Finally, whether intrinsic spindle strength (sigma-power, amplitude; three operationalizations) moderates the companion study's respiratory-alignment-to-geometry effect was tested across 18 pre-specified interaction tests: none survived BH-FDR, and a small SO-coupled exploratory subset ($N=25$ events/15 subjects) showed no descriptive signal either. We conclude that autonomic phase-locking in human sleep is carrier-specific and strongest for slow oscillations, that spindle-onset timing remains a fragile, null-construction-sensitive effect, and that intrinsic spindle strength does not detectably moderate the companion study's phase-alignment-geometry link at current power.
  ],
  author-summary: [
    A companion study found that the *peak*, not the start, of a sleep spindle lines up with a preferred point of the breathing cycle. New data let us test whether other sleep rhythms show the same pattern. Slow brain waves during deep sleep (slow oscillations) turned out to show an even stronger, near-universal link to both breathing and heartbeat, while a memory-related rhythm during dream sleep (REM theta) showed none. We also tried three different ways of testing whether spindles preferentially *start* at a particular breathing/heartbeat phase; the three methods disagreed with each other, so we report that disagreement honestly rather than picking the answer we like. Finally, we asked whether stronger spindles show a bigger version of the peak-phase effect on brain-state geometry: they do not, at least not detectably with the data available.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Data Curation, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted at submission.],
  data-availability: [RichSleep is described in @richsleep2026; formal access details will be added at submission (identical dataset to the companion RVC_SLEEP / RVC_SLEEP_peak_analysis articles). NMD (NeuralManifoldDynamics) pipeline outputs and all analysis scripts are versioned in the analysis repository under `articles/RichSLeep_EAP_v2/src/`, with per-script result tables under `articles/RichSLeep_EAP_v2/results/`.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

#set heading(numbering: "1.")
#set math.equation(numbering: "(1)")

= Introduction <sec:intro>

Two companion articles established a specific, carefully-qualified result in human NREM sleep. *RVC_SLEEP* @langell2026rvcsleep replicated a spindle-locked state-space reconfiguration across three independent overnight-PSG datasets and found a null result for whether spindle *onset* phase-locks to the cardiac or respiratory cycle, using a 190-event, geometry-valid RichSleep subsample. *RVC_SLEEP_peak_analysis* @langell2026rvcsleeppeak showed that this null was a design artifact of testing the wrong reference point at insufficient power: on RichSleep's full 23,029-event catalog, spindle *peak* (not onset) phase robustly locks to respiration (population-level second-order $R = 0.665$, $p = 7 times 10^(-6)$ across 24 subjects) and, more fragilely, to the cardiac cycle. A small, exploratory secondary analysis in that article further suggested (2/18 BH-FDR survivors, mixed sensitivity-check agreement) that alignment to this preferred phase might weakly moderate the size of the spindle-locked geometry effect itself.

NMD's most recent RichSleep delivery makes four questions raised, but not answerable, by that prior work newly testable. First: is autonomic phase-locking specific to spindles, or does it generalize across sleep's other major oscillatory "carriers" - N3 slow oscillations (SOs) and REM theta? An internal theoretical review (`articles/Rythmic_Variance_Control_in_Sleep_theory/plan/02_response.md`) had explicitly raised a "state determines carrier" framing: different sleep stages recruit different endogenous rhythmic events, and if body-phase entrainment is a general property of endogenous rhythm-defined events rather than a spindle-specific quirk, it should appear - to varying degrees - across carriers. Second: the spindle-*onset* phase-locking question, left ambiguous by RVC_SLEEP's underpowered null and RVC_SLEEP_peak_analysis's own borderline full-catalog re-test, can now be probed with two null constructions grounded directly in real exposure data (a purpose-built non-event risk set, and a continuous phase stream) rather than only a parametric uniform-circular assumption. Third: RVC_SLEEP_peak_analysis's fragile timing-efficacy hint can be sharpened into an actual interaction test now that per-event intrinsic spindle strength (sigma-power, amplitude) and SO-spindle coupling are available. Fourth, more speculatively: does the "state determines carrier" idea extend to a genuine hazard-style account of *when* a spindle starts, using continuous exposure data rather than only discrete event phases?

#netn-box(title: [Core question])[
  Does autonomic (cardiac/respiratory) phase-locking generalize across sleep's major endogenous rhythmic events beyond the sleep spindle - and does resolving the spindle-onset question with exposure-grounded nulls, or adding an intrinsic-strength covariate to the spindle-peak efficacy test, change either companion article's conclusions?
]

This article reports a single, consistent cross-carrier phase-locking sweep (N2-spindle onset and peak, N3-SO trough and upstate, REM-theta), two new onset-hazard tests, and a strength$times$alignment interaction test on the companion study's own 190-event geometry-valid subsample. It finds that slow-oscillation phase-locking is the strongest effect in the entire dataset, that REM-theta shows none, that the three onset-hazard nulls disagree with each other in a way worth reporting rather than resolving, and that intrinsic spindle strength does not detectably moderate the companion study's alignment-geometry link.

= Theory <sec:theory>

== RVC/EAP tiering and the "state determines carrier" framing

Within Noetic Diffusion Theory (NDT), rhythm-defined endogenous events - sleep spindles being the primary studied case - are treated as candidate *Rhythmic Variance Control* (RVC) events, and the *Embodied Anchoring Principle* (EAP) is a secondary, Tier-2 extension proposing that peripheral bodily rhythms can additionally condition the same latent landscape @langell2025ndt. Nothing in this tiering privileges the spindle as the *only* RVC-eligible event: N3 slow oscillations and REM theta bursts are both endogenous, rhythm-defined, and stage-specific in exactly the sense spindles are, differing mainly in which brain state recruits them. The "state determines carrier" framing (`02_response.md`) makes this explicit: if autonomic entrainment reflects a general property of the underlying gating/denoising mechanism rather than a spindle-specific coincidence, it should be detectable - with plausibly different strength - across all three carriers, using the identical statistical test.

== Timing vs. efficacy, revisited with an intrinsic-strength covariate

RVC_SLEEP_peak_analysis distinguished an *event-timing* pathway (does body phase predict *when*, or at what phase, an event occurs) from an *event-efficacy* pathway (does phase at the moment of an event change *how strongly* it reconfigures geometry), and found timing evidence for spindle peak-phase but only a fragile, secondary hint of efficacy. That analysis could not separate "phase moderates a spindle's own intrinsic strength, which independently moderates geometry" from a more direct phase-geometry link, for lack of a strength covariate - a limitation flagged explicitly there and in `02_response.md` (S5). The present article closes that specific gap: with per-event sigma-power, amplitude, and SO-spindle coupling now available, the efficacy question becomes a proper *interaction* test (does alignment's effect on geometry depend on how strong the spindle already is), not merely a main effect.

== Corrected permutation-null construction (unchanged from the companion article)

The statistic used throughout the cross-carrier sweep is unchanged from RVC_SLEEP_peak_analysis: the first-harmonic mean resultant length $R_1 = |chevron.l e^(i phi) chevron.r|$, a second-harmonic term $R_2 = |chevron.l e^(2 i phi) chevron.r|$, combined into an omnibus $T_2 = R_1^2 + R_2^2$, tested via Monte Carlo permutation against a *subject-specific random-phase-rotation* null (each permutation draws one i.i.d. $"Uniform"(0, 2 pi)$ rotation per subject, added to all of that subject's phases) rather than an asymptotic Rayleigh $p$-value. Two further null constructions, new to this article, are introduced in Methods for the onset-hazard question specifically.

= Methods <sec:methods>

== Dataset and new data products

RichSleep @richsleep2026 (24 subjects, whole-night PSG) is the sole dataset, as in both companion articles. NMD's 2026-07-12/13 delivery adds six data products, validated in `01_validate_v3_delivery.py` (all checks pass; `S1.1`):

- `phase_resolved_v3` - the same 23,029-event N2-spindle catalog as the companion article's `event_phase_v2` (confirmed by an exact bit-identity check on all 13 shared columns), extended with `sigma_power`, `sigma_power_z_n2`, `amplitude`, `frequency_hz`, and SO-spindle coupling columns.
- `slow_oscillation_v1` - 68,386 raw SO events (26,377 N2, 42,009 N3).
- `phase_continuous_v1` - 24 subjects, 8,834,120 rows total, continuous 10 Hz `phi_cardiac`/`phi_resp`/`phi_rem_theta`.
- `event_phase_n3_so_v1` - 42,009 N3-SO events, phase-resolved at both trough and upstate.
- `event_phase_rem_theta_v1` - 2,412 REM-theta 30 s epochs, phase-resolved.
- `non_event_risk_v1` - 66,827 N2-restricted, per-subject-matched, margin-excluded ($plus.minus 30$ s around every real spindle) non-event timepoints, purpose-built as a genuine risk set for hazard-style testing.

== Cross-carrier phase-locking sweep

One generic test (`run_phase_locking_family`, Theory) is applied to four carrier $times$ up to two reference-point combinations, five carrier/reference-point conditions in total: N2-spindle onset, N2-spindle peak (both regression checks against the companion article), N3-SO trough, N3-SO upstate, and REM-theta - each at both cardiac and respiratory channels, for 10 tests. The primary family for BH-FDR is these 10 pooled subject-rotation-permutation tests on the $T_2$ statistic. REM-theta's per-subject arm excludes the one subject with $<5$ epochs; the pooled/permutation arm retains all 2,412 events.

== Onset-hazard tests (two new null constructions)

*Test A - case-control logistic regression.* Real spindle onsets (cases, $n=23029$) are pooled with `non_event_risk_v1` rows (controls, $n=66827$); `"is_case" ~ cos(phi) + sin(phi)`, cluster-robust logistic regression by subject, joint Wald $chi^2(2)$ test on the $(cos, sin)$ coefficient pair. A significant result means real onsets occur at different phases than a matched sample of "could a spindle have started here" N2 timepoints - the case-control analogue of a hazard-ratio test, using the genuine (non-uniform-in-phase-value) exposure distribution rather than an assumed-uniform one.

*Test B - circular time-shift surrogate.* Each subject's own continuous phase stream (`phase_continuous_v1`) is shifted by an independent random lag (wrapping at that subject's recording duration) and phase is re-read at the same real onset clock-times; repeated 500 times to build a null distribution for $T_2$. This preserves the exact non-sinusoidal waveform and autocorrelation structure of each subject's own signal - a different null-construction principle from both Test A and the cross-carrier sweep's subject-rotation permutation (now relabeled Null 0 for this comparison).

An initial attempt at a third exposure model, a phase-binned Poisson-offset GLM using the geometry-run H5's `labels/stage` array as a continuous hypnogram, was abandoned: that array turned out to be populated only at the 177 "jacobian-center" windows per subject (a sparse local-dynamics-fit subset), not continuously, and undercounted true N2 exposure by roughly two orders of magnitude - documented in `handover/handover_From_nmd_richsleep_eap_v2_delivery_received.md` S6. `non_event_risk_v1` (Test A) was found on NMD's delivery share alongside the other five products but had not yet been copied into this article's data folder; it supersedes the abandoned approach.

== Intrinsic-strength $times$ alignment interaction test

Using the companion article's held-out, subject-balanced population-preferred peak phase $mu_("resp,peak")$ (recomputed here from this article's own `phase_resolved_v3` catalog for self-containment; reproduces the companion value exactly, see S1.4) and the resulting alignment score $"resp_peak_alignment" = cos(phi_("resp,peak") - mu_("resp,peak"))$, the primary family fits `delta ~ alignment * qe + covariates` (WLS-cluster, weights $1"/"n_"events,subject"$, cluster-robust SE by subject) on the companion article's 190-event geometry-valid subsample, testing the *interaction* coefficient across 9 geometry endpoints $times$ 2 delta modes = 18 tests, BH-FDR jointly. Primary $"qe" = log(1+"sigma_power_z_n2")$ (raw sigma-power is heavily right-skewed, skew $approx 2.75$); robustness repeats with $"qe" = log(1+"amplitude")$ and untransformed `sigma_power_z_n2`. A secondary, explicitly non-confirmatory, descriptive-only check (no interaction model, no FDR family - too few degrees of freedom) reports Pearson correlations between geometry delta and SO-spindle coupling score/SO amplitude on the true SO-coupled subset ($N=25$ events/15 subjects).

= Results <sec:results>

== R1: Data coverage <sec:r1>

#figure(
  kind: table,
  clean-table(
    columns: (1.9fr, 0.8fr, 1.1fr),
    align: (left, center, center),
    inset: 5pt,
    table.header([*Data product*], [*$N$ subj.*], [*$N$ events/rows*]),
    [`phase_resolved_v3` (N2-spindle)], [24], [23,029],
    [`slow_oscillation_v1` (raw SO, N2+N3)], [24], [68,386 (26,377 N2 + 42,009 N3)],
    [`phase_continuous_v1` (10 Hz stream)], [24], [8,834,120 rows (~10.22 h/subj.)],
    [`event_phase_n3_so_v1` (N3-SO, phase-resolved)], [24], [42,009],
    [`event_phase_rem_theta_v1` (REM-theta, phase-resolved)], [24], [2,412 (2-219/subj.)],
    [`non_event_risk_v1` (non-event risk set)], [24], [66,827 (492-7,698/subj.)],
    [Geometry-valid, N2-staged subsample (companion articles' population)], [24], [190],
  ),
  caption: [Data coverage across all six new/reused data products. All schema, row-count, and QC checks pass (`01_validate_v3_delivery.py`); the `phase_resolved_v3` vs. `event_phase_v2` bit-identity check confirms geometry is unchanged by the new delivery.]
) <tab-coverage>

Only 2,708/23,029 spindles (11.8%) have a matched SO partner, and of the 190 geometry-valid events, only 25 (across 15 subjects) are SO-coupled - the power caveat behind R5's descriptive-only framing.

== R2: Slow-oscillation phase-locking exceeds the spindle-peak effect; REM theta is null <sec:r2>

The cross-carrier sweep (Table @tab-crosscarrier, Fig. @fig-crosscarrier) shows a clear ordering: N3-SO phase-locking (both trough and upstate, both channels) is the strongest effect in the dataset by a wide margin, exceeding even the already-robust N2-spindle-peak respiratory result; N2-spindle-onset is weak/borderline; REM-theta is null on both channels.

#figure(
  kind: table,
  clean-table(
    columns: (1.1fr, 0.8fr, 0.7fr, 0.8fr, 0.9fr, 0.9fr, 0.9fr),
    align: (left, left, center, center, center, center, center),
    inset: 4.5pt,
    table.header([*Carrier*], [*Ch.*], [*$N$*], [*pooled $R_1$*], [*2nd-order $R$*], [*perm $p$ ($T_2$)*], [*FDR $q$*]),
    [N2-spindle onset], [cardiac], [23,029], [0.0093], [0.273], [0.0815], [0.102],
    [N2-spindle onset], [resp], [23,029], [0.0189], [0.403], [0.0265], [0.038],
    [N2-spindle peak], [cardiac], [23,029], [0.0159], [0.462], [0.0015], [0.0025],
    [N2-spindle peak], [resp], [23,029], [0.0453], [0.665], [0.0005], [0.0010],
    [N3-SO trough], [cardiac], [42,009], [0.0645], [0.654], [0.0005], [0.0010],
    [N3-SO trough], [resp], [42,009], [0.0535], [0.754], [0.0005], [0.0010],
    [N3-SO upstate], [cardiac], [42,009], [0.0626], [0.669], [0.0005], [0.0010],
    [N3-SO upstate], [resp], [42,009], [0.0504], [0.708], [0.0005], [0.0010],
    [REM-theta], [cardiac], [2,412], [0.0194], [0.369], [0.3233], [0.342],
    [REM-theta], [resp], [2,412], [0.0225], [0.241], [0.3423], [0.342],
  ),
  caption: [Cross-carrier phase-locking, 10-test primary family, BH-FDR jointly. Pooled $R_1$: subject-rotation permutation test on all events; 2nd-order $R$: Rayleigh test on the 24 (23 for REM-theta) subject-mean directions. Source: `03_multistage_phase_locking.py` outputs.]
) <tab-crosscarrier>

#figure(
  image("figures/fig1_cross_carrier_phase_locking.svg", width: 95%),
  caption: [Cross-carrier comparison: pooled $R_1$ (left) and BH-FDR-corrected significance (right, $-log_10$ scale, asterisk = $q<0.05$). N3-SO dominates both channels; REM-theta is flat.]
) <fig-crosscarrier>

#figure(
  image("figures/fig2_rose_plots_per_carrier.svg", width: 98%),
  caption: [Pooled circular histograms by carrier (columns) and channel (rows: cardiac, resp). Note the differing phase-origin convention per channel ($phi_"cardiac" in [0,2pi)$, $phi_"resp" in (-pi,pi]$) - both mathematically valid, just differently anchored; this does not affect any $cos$/$sin$-based statistic reported here.]
) <fig-rose>

Regression checks against the companion article (`S1.5`) confirm the onset-phase and peak-phase raw permutation $p$-values reproduce diary 241/242's values bit-for-bit (onset cardiac $p=0.0815$, onset resp $p=0.0265$, both exact matches). The onset-resp raw $p$ is unchanged from the companion article; what changes is its FDR status, because the declared family is different (10 tests here vs. 4 there) - discussed in R3 and Discussion, not treated as a discrepancy to be resolved in either direction.

== R3: Three independent onset-hazard nulls disagree <sec:r3>

Table @tab-hazard and Fig. @fig-hazard summarize the two new onset-hazard tests alongside the cross-carrier sweep's own subject-rotation result (relabeled Null 0 here for direct comparison):

#figure(
  kind: table,
  clean-table(
    columns: (1.5fr, 1fr, 1fr),
    align: (left, center, center),
    inset: 4.5pt,
    table.header([*Null construction*], [*Cardiac $p$*], [*Resp $p$*]),
    [Null 0: subject-rotation permutation (raw)], [0.0815], [0.0265],
    [Test A: case-control logit vs. `non_event_risk_v1` ($chi^2(2)$ Wald)], [0.379], [$3.96 times 10^(-7)$],
    [Test B: circular time-shift surrogate], [0.0040], [1.0000],
  ),
  caption: [Onset-phase-locking under three independent null constructions. Source: `03_multistage_phase_locking.py`, `04_spindle_onset_hazard_model.py`.]
) <tab-hazard>

#figure(
  image("figures/fig3_hazard_curve.svg", width: 95%),
  caption: [Test A's fitted intensity-ratio curve (dashed) vs. binned empirical case:control ratio (points), by channel, with both tests' $p$-values annotated.]
) <fig-hazard>

The three constructions do not converge, and disagree in different directions per channel. For cardiac: Test A (case-control) finds nothing ($p=0.379$); Test B (time-shift) finds a weak effect ($p=0.004$); Null 0 is borderline-null ($p=0.0815$). An ad hoc 12-bin case-vs-control histogram comparison shows no coherent shape difference for cardiac, so Test B's hit is not corroborated by either other test and is treated as more likely a false positive of that specific construction than a real effect. For respiration: Test A finds a small but very clearly non-zero effect ($p=4 times 10^(-7)$, surviving FDR at $q=7.9 times 10^(-7)$); the same histogram check confirms a coherent, monotonic first-harmonic-like density excess/deficit pattern (not noise), just a small one ($approx$5-10% per-bin deviation), detectable only because Test A's pooled $N$ (89,856 rows) gives it far more statistical power than Null 0 or Test B; Null 0's raw $p=0.0265$ is directionally consistent (same channel, same qualitative weak-positive-signal) but Test B ($p=1.0$) finds nothing.

#netn-box(title: [R3 summary - reported, not resolved])[
  Onset-phase-locking is at most a very weak, null-construction-sensitive effect for respiration, and is not corroborated by any two of the three tests simultaneously for cardiac - in sharp, deliberate contrast to the N2-peak and N3-SO results (R2), which are large and significant under every test tried. This three-way disagreement is reported as-is; it is not resolved by selecting whichever null gives a preferred answer, and is used in the Discussion as a methodological caution about single-null "onset locking is null" claims.
]

== R4: Intrinsic spindle strength does not moderate the alignment-geometry effect <sec:r4>

The primary family (`"delta" ~ "resp_peak_alignment" * log(1+"sigma_power_z_n2") + "covariates"`, 18 tests) finds *0/18* interaction terms BH-FDR-significant (minimum raw $p=0.135$, endpoint `m`, `event_control` mode; Table @tab-qeinteraction gives the full endpoint list, `S2.3`). Robustness repeats with $"qe"="amplitude"$ (log-transformed) and untransformed `sigma_power_z_n2` likewise find 0/18 significant, and no (delta_mode, endpoint) pair reaches significance under any of the three qe operationalizations.

#figure(
  kind: table,
  clean-table(
    columns: (1fr, 0.7fr, 0.7fr, 0.9fr, 0.9fr, 0.9fr),
    align: (left, left, center, center, center, center),
    inset: 4.5pt,
    table.header([*Delta mode*], [*Endp.*], [*$N$*], [*interaction coef*], [*$p$*], [*FDR $q$*]),
    [`event_control`], [`m`], [172], [$+0.081$], [0.135], [0.834 (ns)],
    [`event_prefar`], [`d`], [160], [$-0.147$], [0.279], [0.834 (ns)],
    [`event_prefar`], [`d_l`], [160], [$-0.049$], [0.516], [0.865 (ns)],
    [all other 15 rows], [-], [160-172], [-], [0.34-0.94], [$>=0.83$ (ns)],
  ),
  caption: [Primary family (qe = log1p(sigma_power_z_n2)); smallest-$p$ rows shown, full 18-row table in `S2.3`. No interaction term survives BH-FDR. `d` and `d_l` are shown for direct comparison with the companion article's main-effect finding on these same two endpoints (R6 there); the alignment *main effect* in this interaction model remains nominally consistent in direction and significance with that finding (`d`: $p=0.023$; `d_l`: $p=0.0030$, both `event_prefar` mode) but is not this family's FDR-corrected quantity. Source: `05_qe_interaction_moderation.py`.]
) <tab-qeinteraction>

#figure(
  image("figures/fig4_qe_coupling_distributions.svg", width: 98%),
  caption: [Intrinsic-strength distribution (raw and log1p-transformed sigma-power z-score) and SO-coupling coverage (25/190 events).]
) <fig-qedist>

#figure(
  image("figures/fig5_efficacy_interaction.svg", width: 68%),
  caption: [Illustration only (no FDR-significant interaction was found): delta vs. alignment, split by qe tertile, for the smallest-$p$ endpoint. Overlapping tertile trend lines with no consistent ordering are the expected appearance of a null interaction.]
) <fig-efficacy>

== R5: SO-coupled subset shows no descriptive signal (exploratory, N=25/15 subjects) <sec:r5>

On the true SO-coupled subset, all 18 delta-vs-coupling-score and delta-vs-SO-amplitude Pearson correlations are weak and inconsistent in sign across endpoints (range $-0.29$ to $+0.44$, `S2.4`), with no discernible pattern. This is reported descriptively only, per the plan's explicit power caveat (25 events/15 subjects - too few degrees of freedom for a confirmatory interaction model or an FDR family), and should not be read as evidence against a true SO-coupling effect, only as uninformative at this sample size.

#netn-box(title: [R4-R5 summary])[
  Adding an intrinsic-strength covariate - the specific gap RVC_SLEEP_peak_analysis's efficacy hint could not close - does not turn that hint into a confirmed interaction: 0/18 tests survive FDR under any of three qe operationalizations, and the small SO-coupled subset adds no descriptive signal either. The companion article's fragile 2/18 main-effect finding is neither strengthened nor contradicted by this null interaction result; the two questions (does alignment matter on average; does its effect scale with spindle strength) are logically separate, and only the second is addressed here.
]

= Discussion <sec:discussion>

== State determines carrier, and to what degree

The cross-carrier sweep (R2) supports the "state determines carrier" framing, but with a specific, unpredicted ordering: N3-SO phase-locking is not merely present but is the single strongest autonomic-coupling effect measured across either this or the companion articles, exceeding the already-robust N2-spindle-peak result by a wide margin on both channels (second-order $R approx 0.65$-$0.75$ vs. $0.46$-$0.67$). REM-theta shows no detectable coupling at all. This is not "autonomic entrainment is a general property of endogenous sleep events, present everywhere to similar degree" - it is carrier-specific in a strong sense, with slow oscillations - the largest-amplitude, most globally-synchronized cortical event of the three - showing the tightest coupling, and REM theta - a fast, more locally-generated rhythm during an autonomically volatile stage - showing none. This ordering (SO $>$ spindle-peak $>$ spindle-onset $approx$ REM-theta) is a genuine empirical result of this article, not an a priori prediction of the "state determines carrier" framing itself, which was agnostic on relative magnitude.

== Onset timing: a caution about single-null claims

R3's three-way disagreement is, itself, the most methodologically important result in this article. Had only Test A been run, the conclusion would be "respiratory onset-phase-locking is real, if tiny." Had only Test B been run, the conclusion would be "cardiac onset-phase-locking is real, respiratory is not." Had only Null 0 (the companion article's own method) been run, the conclusion would be "both are borderline-null." All three cannot be simultaneously true readings of the same phenomenon, and this article does not adjudicate between them - the honest summary is that spindle-onset autonomic coupling, unlike spindle-peak or SO coupling, is small enough that its statistical detectability depends on which (real, defensible) null construction and how much power that construction happens to bring to bear, rather than on a single unambiguous effect size. This stands in useful methodological contrast to R2's SO and spindle-peak results, which are large and significant under every test applied to them.

== Efficacy remains unconfirmed, now on stronger footing

RVC_SLEEP_peak_analysis's own limitations section named the missing intrinsic-strength covariate as the one gap preventing a real test of whether phase-alignment's effect on geometry might simply reflect spindle strength (a plausible confound/mediator RVC_SLEEP_peak_analysis could not rule out). This article closes that gap and finds no interaction (R4) - which sharpens, rather than resolves, the interpretation of the companion article's fragile main-effect hint: it is not obviously explained by an unmeasured strength confound (there is no detectable qe-dependence to explain it), but it also gains no additional support from this test. The efficacy question remains exactly where the companion article left it: a fragile, secondary, not-yet-independently-replicated hint, now with one more plausible confound tested and not found.

== Relation to companion articles and external literature

This article's N2-spindle onset and peak regression checks (R2) reproduce RVC_SLEEP_peak_analysis's diary 241/242 raw statistics exactly, confirming the new NMD delivery changes nothing about previously-reported geometry or phase-locking numbers (the `phase_resolved_v3` vs. `event_phase_v2` bit-identity check, R1, is the data-level guarantee behind this). The N3-SO and REM-theta results are new to the RichSleep/RVC_SLEEP line of work; to our knowledge no prior analysis in this repository has tested autonomic phase-locking for either carrier. Ghibaudo et al. @ghibaudo2024spindle_resp and Schreiner et al. @schreiner2023resp_memory, cited in the companion article for spindle-timing-respiration coupling, do not address SO or REM-theta phase-locking directly; a state-dependent-reorganization account of respiration-brain coupling across sleep depth @progneurobio2025_resp_wake_sleep is broadly compatible with - though does not specifically predict - the SO-dominant ordering found here.

== Limitations

- *Single-dataset.* RichSleep remains the only RVC_SLEEP-line dataset with a phase-resolved export; none of R2-R5's results have been tested for cross-dataset replication (ANPHY is ECG-only, BOAS mostly lacks respiration - ruled out on data-contract grounds, not merely unattempted).
- *REM-theta power and evenness.* 2,412 epochs is small relative to the N2/N3 carriers, and per-subject $N$ is uneven (2-219); the REM-theta null could reflect genuine absence of coupling or insufficient power to detect a smaller true effect - this article cannot distinguish the two.
- *No geometry outcome for N3-SO or REM-theta.* `coords_9d` geometry exists only for the N2-spindle-locked event/control/pre_far bins (per the companion article's `09_richsleep_verification.py`), so R2's SO and REM-theta results are timing-only; no efficacy test analogous to R4 is possible for either carrier with the current export.
- *Onset-hazard disagreement is unresolved by design.* R3 reports three answers rather than one; a reader wanting a single number for "does spindle onset phase-lock" will not find one here, deliberately.
- *qe operationalization.* All three qe transforms are monotonic functions of the same two underlying detector outputs (sigma-power, amplitude); a genuinely independent strength measure (e.g. an amplitude estimate from a different detector) was not available and could behave differently.
- *SO-coupling power.* R5's $N=25$/15-subject descriptive check is far too small to rule out a true SO-coupling effect; it is reported as uninformative, not as evidence of absence.

== Conclusion

Autonomic phase-locking in human sleep is carrier-specific, not a general property of endogenous rhythmic events applied uniformly: it is strongest at slow-oscillation trough/upstate, present but weaker at spindle peak, weak and null-construction-sensitive at spindle onset, and undetectable in REM theta. Spindle-onset timing's fragility is best characterized by the disagreement among three independent, individually-defensible null constructions rather than by any single one of them. Intrinsic spindle strength does not detectably moderate the companion article's phase-alignment-to-geometry effect, closing (without resolving) the one confound that article's own limitations section had flagged as open. Together with the companion articles, this establishes autonomic-carrier phase-locking as a real but heterogeneous phenomenon across human sleep's oscillatory repertoire, with its downstream functional consequence for state-space geometry remaining, for now, an open and only weakly-supported question.

= Acknowledgements <sec:ack>

The author thanks the RichSleep dataset contributors for the underlying recordings, and NMD (NeuralManifoldDynamics) for the newly-delivered phase-resolved, continuous-phase, and risk-set data products that made this article's cross-carrier and hazard-model analyses possible.

#bibliography("references.bib", style: "apa")
