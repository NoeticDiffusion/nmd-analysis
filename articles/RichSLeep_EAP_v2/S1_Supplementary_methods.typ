// S1 Supplementary Methods — RichSleep_EAP_v2
// Companion to the manuscript.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "S1 Methods - RichSleep_EAP_v2",
  subtitle: "New data products, the cross-carrier phase-locking helper, the two new onset-hazard null constructions, and the intrinsic-strength interaction model",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S1.0 Dataset and relationship to the companion articles

This article analyzes RichSleep (@richsleep2026, 24 subjects, whole-night PSG) exclusively - the identical dataset and sleep-spindle catalog used in both companion articles' @langell2026rvcsleep @langell2026rvcsleeppeak analyses. NMD's 2026-07-12/13 delivery adds six new data products, validated end-to-end in `01_validate_v3_delivery.py` (`S1.1`). A bit-identity check on all 13 columns shared between `phase_resolved_v3` and the companion articles' `event_phase_v2` confirms geometry, onset/peak times, and phase values are byte-identical between deliveries - every geometry number reused from the companion articles in this article is therefore the companion articles' own frozen number, not a recomputation.

= S1.1 New and reused data products

#figure(
  kind: table,
  clean-table(
    columns: (1.3fr, 2.2fr),
    align: (left, left),
    inset: 4.5pt,
    table.header([*Product*], [*Description*]),
    [`phase_resolved_v3`], [24 subjects, 23,029 N2-spindle events (identical catalog to `event_phase_v2`), now 33 columns: adds `frequency_hz`, `amplitude`, `sigma_power`, `sigma_power_z_n2` (intrinsic strength) and `so_amplitude`, `so_spindle_coupling_score`, `so_spindle_latency_sec`, `so_partner_missing`, `so_coupling_qc_flag` (SO-spindle coupling).],
    [`slow_oscillation_v1`], [68,386 raw SO events (26,377 N2 + 42,009 N3), no phase columns - the source catalog for both the v3 SO-coupling columns and the N3-SO phase-resolved export below.],
    [`phase_continuous_v1`], [24 subjects, 8,834,120 rows total (~10.2 h/subject), continuous 10 Hz `phi_cardiac`/`phi_resp`/`phi_rem_theta`; `cardiac_phase_valid`/`resp_phase_valid`$approx$100%, `rem_theta_valid`$approx$8.2% (REM only). The genuine background/risk-set stream used by Test B (`S1.3`).],
    [`event_phase_n3_so_v1`], [42,009 N3-SO events, phase-resolved against cardiac and respiration at both SO trough and SO upstate (100% valid/QC-ok).],
    [`event_phase_rem_theta_v1`], [2,412 REM-theta 30 s epochs, phase-resolved against cardiac, respiration, and theta (100% valid; uneven per-subject $N$, 2-219).],
    [`non_event_risk_v1`], [66,827 N2-restricted, per-subject-matched, margin-excluded ($plus.minus 30$ s around every real spindle onset) non-event timepoints, each carrying its own `phi_cardiac`/`phi_resp` - NMD's purpose-built risk set for case-control hazard-style testing (Test A, `S1.3`).],
  ),
  caption: [All six data products, `01_validate_v3_delivery.py`. Geometry (`coords_9d`) exists only for the companion articles' N2-spindle-locked event/control/pre_far bins - see `S3.0` for the resulting sample-coverage implications.]
) <tab-products>

Only 2,708/23,029 spindles (11.8%) have a matched SO partner (`so_partner_missing`$=0$); of the companion articles' 190 geometry-valid events, only 25 (across 15 subjects) are SO-coupled - the power caveat behind R5's descriptive-only framing (`S1.5`, part 3).

= S1.2 Harmonic statistic and subject-rotation permutation null (unchanged from the companion articles)

For a set of phases $phi_1, ..., phi_n$ (radians), the first- and second-harmonic mean resultant lengths and the omnibus statistic used throughout the cross-carrier sweep and Test A/B:

$ R_1 = |chevron.l e^(i phi) chevron.r| = sqrt((1/n sum_k cos phi_k)^2 + (1/n sum_k sin phi_k)^2) $
$ R_2 = |chevron.l e^(2 i phi) chevron.r|, quad T_2 = R_1^2 + R_2^2 $ <eq:harmonic>

$T_2$ is an honestly-labelled analogue of Hermans-Rasson's robustness-to-multimodality motivation, not a re-implementation of that specific literature statistic (unchanged rationale from the companion article's `S1.2`) - every $p$-value here is a Monte Carlo permutation $p$-value, not an asymptotic one.

*Subject-rotation permutation test* (`rvc_sleep_support.subject_rotation_permutation_test`, unchanged from the companion article): for $n_"perm"=2000$ permutations, draw one i.i.d. $"Uniform"(0, 2pi)$ rotation per subject and add it to *all* of that subject's phases; recompute $R_1, T_2$ on the rotated pooled sample each time. This destroys any common population-level preferred phase while exactly preserving each subject's event count and within-subject clustering. Reported $p$-values: $p_(R_1) = (1 + \#{k: R_1^((k)) >= R_1^"obs"}) \/ (1 + n_"perm")$, and identically for $T_2$.

*Per-subject and second-order tests* (`rvc_sleep_support.run_phase_locking_family`, the generic helper shared across all five carrier/reference-point conditions in `S1.3`): a per-subject Rayleigh test (Zar 1999 large-sample approximation, valid for $n approx 10$ or more) for every subject with $>=1$ event, plus a second-order Rayleigh test on the subset of subjects with $>= 5$ events' circular mean directions (`min_events_per_subject=5`) - the per-subject table therefore always has $N$=24 (23 for REM-theta, one subject with $<5$ epochs), while the second-order test's $N$ can be smaller when a carrier has thinly-sampled subjects.

= S1.3 Cross-carrier phase-locking sweep and the two new onset-hazard tests

*Cross-carrier sweep* (`03_multistage_phase_locking.py`): `run_phase_locking_family` (S1.2) is applied to five carrier/reference-point conditions - N2-spindle onset (`phi_cardiac_onset`/`phi_resp_onset`), N2-spindle peak (`phi_cardiac_peak`/`phi_resp_peak`), N3-SO trough (`phi_cardiac_trough`/`phi_resp_trough`), N3-SO upstate (`phi_cardiac_upstate`/`phi_resp_upstate`), and REM-theta (`phi_cardiac`/`phi_resp`) - each at both channels, 10 tests total. The primary family for BH-FDR (@benjamini1995fdr, $alpha=0.05$) is these 10 pooled subject-rotation-permutation tests on $T_2$ (and, separately, on $R_1$); the second-order Rayleigh $p$-values are BH-FDR corrected separately within their own 10-test family. REM-theta's per-subject/second-order arm excludes the one subject with $<5$ epochs; the pooled/permutation arm retains all 2,412 events regardless.

*Test A - case-control logistic regression* (`04_spindle_onset_hazard_model.py`, `rvc_sleep_support.fit_logit_cluster`): real N2-spindle onsets ($n=23029$, `is_case`$=1$) are pooled with `non_event_risk_v1` rows ($n=66827$, `is_case`$=0$); `is_case ~ cos(phase) + sin(phase)`, logistic regression with cluster-robust SE by subject, joint Wald $chi^2(2)$ test on the $("cos", "sin")$ coefficient pair against the null that both are zero. The implied preferred phase is $hat(phi) = "atan2"(b_"sin", b_"cos")$. A significant result means real onsets occur at different phases than a matched, N2-restricted, subject-balanced sample of "could a spindle have started here" timepoints - a genuine hazard-ratio-style test using the real (non-uniform) N2 exposure distribution, not an assumed-uniform one.

*Test B - circular time-shift surrogate* (`rvc_sleep_support.circular_time_shift_surrogate_test`): for $n_"perm"=500$ permutations, each subject's own continuous phase stream (`phase_continuous_v1`) is shifted by an independent random lag (wrapping circularly at that subject's own recording duration, minimum shift 60 s) and phase is re-read at that subject's real onset clock-times under the shifted stream; $T_2$ (and $R_1$) are recomputed each time to build the null distribution. This preserves the exact non-sinusoidal waveform and autocorrelation structure of each subject's own physiological signal - a different null-construction principle from both Test A and the subject-rotation permutation (Null 0 in the main text and `S1.2`), sharing no free parameters or resampling unit with either.

An initial attempt at a third exposure model - a phase-binned Poisson-offset GLM using the per-subject geometry-run H5's `labels/stage` array as a continuous hypnogram - was abandoned when that array turned out to be populated only at 177 "jacobian-center" windows per subject (a sparse local-dynamics-fit subset), undercounting true N2 exposure by roughly two orders of magnitude; documented in `handover/handover_From_nmd_richsleep_eap_v2_delivery_received.md` S6. `non_event_risk_v1` (Test A) supersedes this abandoned approach.

= S1.4 Held-out population-preferred peak phase (self-contained recomputation)

Recomputed here, from this article's own `phase_resolved_v3` catalog, for self-containment (`05_qe_interaction_moderation.py`): using the (`subject_id`, `onset_sec`) key, anti-join the companion articles' 190 geometry-valid events out of the full 23,029-event catalog, leaving 22,839 held-out events. For each of the 24 subjects, compute their own circular mean direction of `phi_resp_peak` on the held-out set; $mu_("resp,peak")$ is the second-order circular mean (@eq:harmonic's $R_1$ construction applied to the 24 subject-mean angles) of those 24 held-out subject means. This reproduces the companion article's own held-out estimate exactly (both use the identical anti-join logic on bit-identical data).

= S1.5 Intrinsic-strength (qe) $times$ alignment interaction model (R4-R5)

1. *Alignment score.* $"resp_peak_alignment"_e = cos(phi_("resp,peak",e) - mu_("resp,peak"))$ for each of the companion articles' 190 geometry-valid events $e$ (S1.4).
2. *qe operationalizations.* Primary: $"qe" = log(1+"sigma_power_z_n2")$ (raw `sigma_power_z_n2` is heavily right-skewed, skew $approx 2.75$). Robustness: $"qe" = log(1+"amplitude")$ and untransformed `sigma_power_z_n2`.
3. *Primary/robustness family.* `delta ~ resp_peak_alignment * qe + covariates` via `fit_wls_cluster` (weights $1"/"n_"events,subject"$, cluster-robust SE by subject; all terms mean-centered before forming the product term, so the reported `_interaction` coefficient is a genuine interaction, not confounded with either main effect's scale). `delta` is `event_bin_value - matched_control_median` (`event_control` mode) or `event_bin_value - mean(pre_far bins, same event)` (`event_prefar` mode), for each of the 9 primary geometry endpoints (`m`, `d`, `e`, `d_n`, `d_l`, `d_s`, `e_e`, `e_s`, `e_m`, inherited unchanged from the companion articles' `coords_9d`). $9$ endpoints $times$ $2$ delta modes $times$ $3$ qe operationalizations - the *interaction* coefficient's BH-FDR correction is applied within each of the three 18-test families separately (one per qe operationalization), matching the companion article's Mål C family-size convention. Nuisance covariates: `event_duration_sec`, `window_center_sec`, `ocular_stability_index`, `sympathetic_index`, `vagal_index`, `eog_quality_quality`, `ecg_quality_quality`, `resp_quality_quality`, `cardioresp_quality_quality`, `anchor_support_fraction_quality` (`available_covariates()` requires $>=50%$ coverage).
4. *Secondary/exploratory SO-coupled check.* On the subset with `so_partner_missing`$=0$ (25 events/15 subjects before delta-mode-specific attrition; 21/14 in `event_control` mode, 19/13 in `event_prefar` mode, matching the same per-mode covariate-availability pattern as the primary family's 172/160), Pearson correlations of `delta` against `so_spindle_coupling_score` and `so_amplitude`, for each of the 9 endpoints $times$ 2 delta modes = 18 pairs. No interaction model, no FDR family - explicitly too few degrees of freedom for a confirmatory test (`S1.5` part 3's power caveat).

#bibliography("references.bib", style: "apa")
