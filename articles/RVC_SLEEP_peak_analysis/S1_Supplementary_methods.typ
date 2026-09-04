// S1 Supplementary Methods — RVC_SLEEP_peak_analysis
// Companion to the manuscript.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "S1 Methods - RVC_SLEEP_peak_analysis",
  subtitle: "Dataset, phase-resolved export, corrected permutation-null construction, robustness-check protocol, and the alignment-moderation model",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S1.0 Dataset and relationship to the companion article

This article analyzes RichSleep (@richsleep2026, 24 subjects, whole-night PSG) exclusively - the identical dataset and identical NMD run (`neuralmanifolddynamics_RichSleep_20260709_100219`, config digest `0c8d751c52029306`) used in the companion RVC_SLEEP article's @langell2026rvcsleep R6/R6b. Sleep-spindle events were originally detected with YASA (@vallat2021yasa, C3-A2 channel, 200 Hz, sigma 12-15 Hz, N2 only); this article does not re-run detection, only re-analyzes the resulting phase-resolved export under a corrected statistical protocol. Geometry (`coords_9d`) is unaffected by the `resp_anchor_index` sign fix documented in the companion article (its `S1.0`/`S1.7`), so all geometry values used in R6 here are unchanged from the companion article's own frozen numbers.

= S1.1 Phase-resolved export and phase conventions

The `event_phase_v2` export (`RichSleep_resolved/phase_resolved_v2/`, one parquet per subject, concatenated to 23,029 rows across 24 subjects) provides, per detected spindle: `onset_sec`, `peak_sec` (time of maximum amplitude within the detected event), `duration_sec`, `phi_cardiac_onset`, `phi_cardiac_peak`, `phi_resp_onset`, `phi_resp_peak`, `cardiac_phase_quality`, `resp_phase_quality`, `rr_interval_ms_at_onset`, `inhale_at_onset`, and `hep_amplitude_pre_far`. Phase conventions (documented in `RichSleep_resolved/phase_resolved_v1/run_meta.json`, `phase_conventions`): $phi_"resp" in (-pi, pi)$ (Hilbert-transform phase of the 0.1-0.5 Hz bandpassed chest signal), $0 =$ full inhale, $(-pi, 0) =$ rising/inhale, $(0, pi) =$ falling/exhale, `inhale_at_onset`$=1$ iff $phi_"resp,onset" < 0$; $phi_"cardiac" in [0, 2pi)$, $0 =$ nearest R-peak, $pi =$ mid-cycle.

Two samples are used throughout R2-R3: the *full catalog* (all 23,029 rows, 24 subjects) and a *quality-filtered* subset (`cardiac_phase_quality`$>=0.7$ and `resp_phase_quality`$=1.0$, 20,877 rows). A third sample, the *geometry-valid subsample* (190 rows, the companion article's R6b population: N2-staged, `coords_9d_finite`, exact-onset-joined against the event-locked geometry table), is retained only for direct comparability with the companion article's own numbers (Table 1 in the main text) and as the input population for R6's alignment-moderation test.

= S1.2 Harmonic statistic and corrected permutation-null construction

For a set of phases $phi_1, ..., phi_n$ (radians), define the first- and second-harmonic mean resultant lengths and the omnibus statistic used throughout:

$ R_1 = |chevron.l e^(i phi) chevron.r| = sqrt((1/n sum_k cos phi_k)^2 + (1/n sum_k sin phi_k)^2) $
$ R_2 = |chevron.l e^(2 i phi) chevron.r|, quad T_2 = R_1^2 + R_2^2 $ <eq:harmonic>

$T_2$ is an honestly-labelled analogue of Hermans-Rasson's robustness-to-multimodality motivation (an omnibus statistic sensitive to axial/bimodal alternatives that $R_1$ alone can miss), not a re-implementation of that specific literature statistic - chosen to avoid risking a subtly wrong formula, since every $p$-value here is a Monte Carlo permutation $p$-value with no dependence on any statistic's asymptotic distribution.

*Subject-rotation permutation test* (the corrected primary-family test; replaces an earlier, retracted proposal to shuffle subject labels on the pooled angle set, which an external theoretical review correctly identified as leaving the pooled statistic invariant and therefore not constructing a valid null at all). For $n_"perm"=2000$ permutations: draw one i.i.d. $"Uniform"(0, 2pi)$ rotation per subject and add it to *all* of that subject's phases; recompute $R_1, T_2$ on the rotated pooled sample each time. This destroys any common population-level preferred phase / axial alignment while exactly preserving each subject's event count, within-subject clustering, and the observed unequal per-subject sampling. Reported $p$-values: $p_(R_1) = (1 + \#{k: R_1^((k)) >= R_1^"obs"}) \/ (1 + n_"perm")$, and identically for $T_2$.

*Subject-cluster bootstrap.* For $n_"boot"=2000$ resamples: resample subjects with replacement (keeping each selected subject's full event set), recompute pooled $R_1$; report the empirical 2.5/97.5 percentiles as a CI on $R_1$. This characterizes estimation stability, not a hypothesis test.

*Categorical cross-check.* For a binary flag (`inhale_at_onset`), aggregate to one subject-level proportion first (pseudo-replication-safe by construction), then one-sample $t$-test and Wilcoxon signed-rank against the 0.5 null.

= S1.3 Primary and secondary test families

*Primary family* (BH-FDR corrected jointly, @benjamini1995fdr, $alpha=0.05$): $2$ channels (`phi_cardiac_onset`, `phi_resp_onset`) $times$ $2$ samples (full catalog, quality-filtered) $= 4$ tests, both $R_1$- and $T_2$-based $p$-values BH-FDR corrected within their own statistic across the 4-test family.

*Secondary/exploratory family* (reported, not folded into the primary correction): the identical subject-rotation permutation machinery applied to `phi_cardiac_peak`/`phi_resp_peak` on the full catalog and quality-filtered samples, and to all four channels on the geometry-valid 190-event subsample; the `inhale_at_onset` categorical cross-check; and, retained for context (already pseudo-replication-safe by construction, unaffected by the permutation-null correction), per-subject Rayleigh tests (Zar 1999 large-sample approximation) plus a second-order Rayleigh test on the 24 subject-level mean-direction angles, both per channel and sample.

= S1.4 Robustness-check protocol for the peak-phase finding

Run only for `phi_resp_peak`/`phi_cardiac_peak`, after the secondary family (S1.3) identified a candidate effect:

1. *Phase-convention calibration.* Re-verify `inhale_at_onset`'s sign convention against `phi_resp_onset`'s documented sign; report preferred peak-phase angles in degrees with an explicit physiological label (respiratory: fraction of the way from exhale-trough to inhale-peak, or vice versa; cardiac: degrees after the nearest R-peak).
2. *Onset-to-peak advance and duration-tercile stratification.* Compute $"time_to_peak" = "peak_sec" - "onset_sec"$ and the wrapped phase advance $Delta phi = ("phi_peak" - "phi_onset" + pi) mod 2pi - pi$ per channel; split events into duration terciles (`pd.qcut`, 3 groups) and re-run the full subject-rotation permutation test (S1.2) within each tercile independently, with distinct fixed seeds per tercile (46/47/48) for reproducibility.
3. *Leave-one-subject-out (LOSO) jackknife.* For each of the 24 subjects, drop that subject and recompute (a) the second-order Rayleigh test on the remaining 23 subject-mean directions and (b) the pooled subject-rotation permutation test ($n_"perm"=500$, reduced from 2000 for the 24$times$-repeated loop; fixed seed 44), reporting the range of resulting $p$-values across all 24 reruns and identifying the single most influential subject (largest resulting $p$ on drop).
4. *Deterministic split-half replication.* Split the 24 subjects alphabetically into two fixed 12-subject halves (`sub-xn001`-`sub-xn012` vs. `sub-xn013`-`sub-xn024`); re-run both the pooled subject-rotation permutation test ($n_"perm"=2000$, fixed seed 45) and the second-order Rayleigh test independently within each half.

= S1.5 Peak-phase alignment-moderation model (new analysis, R6)

To test whether alignment to the population-preferred respiratory-peak phase moderates the companion article's spindle-locked geometry delta, without circularity:

1. *Held-out population phase estimate.* Using the (subject_id, onset_sec) key, anti-join the 190 geometry-valid events out of the full 23,029-event catalog, leaving 22,839 held-out events. For each of the 24 subjects, compute their own circular mean direction on the held-out set; $mu_("resp,peak")$ is the second-order circular mean (@eq:harmonic's $R_1$ construction, applied to the 24 subject-mean angles) of those 24 held-out subject means - i.e. a subject-balanced, non-circular estimate that never uses any of the 190 test events.
2. *Alignment score.* For each of the 190 geometry-valid events $e$: $"alignment"_e = cos(phi_("resp,peak",e) - mu_("resp,peak")) in [-1, 1]$.
3. *Moderation model.* Identical WLS-cluster machinery to the companion article's Mål C (its `S1.5`/`S1.6`): $"delta" ~ "alignment" + "centered nuisance covariates"$, weights $=1"/"n_"events,subject"$, cluster-robust SE by subject; `delta` is `event_bin_value - matched_control_median` (`event_control` mode) or `event_bin_value - mean(pre_far bins, same event)` (`event_prefar` mode), computed for each of the 9 primary geometry endpoints; nuisance covariates identical to the companion article's list (`event_duration_sec`, `window_center_sec`, `ocular_stability_index`, `sympathetic_index`, `vagal_index`, `eog_quality_quality`, `ecg_quality_quality`, `resp_quality_quality`, `cardioresp_quality_quality`, `anchor_support_fraction_quality`; `available_covariates()` requires $>=50%$ coverage). $9$ endpoints $times$ $2$ delta modes $= 18$ tests, BH-FDR corrected jointly - identical family size/design to the companion article's Mål C, for direct comparability. Only the respiratory-peak channel is tested; cardiac-peak is excluded a priori (already downgraded to fragile in R4-R5 before R6 was run).
4. *Companion sensitivity checks.* Per-subject OLS slopes of `delta` on `alignment` (`min_events=3`), then a one-sample $t$-test, Wilcoxon signed-rank, and a within-subject sign-flip permutation test ($n_"perm"=2000$) on those slopes - identical machinery to the companion article's own Mål C sensitivity protocol.
5. *Secondary circular-regression sensitivity check* (exploratory, not part of the 18-test family): $"delta" ~ cos(phi_("resp,peak")) + sin(phi_("resp,peak")) + "covariates"$ (identical WLS-cluster machinery), with the implied "geometry-optimal" phase direction $hat(phi) = "atan2"("sin_coef", "cos_coef")$ and a cluster-robust Wald test that both coefficients are jointly zero, compared against $mu_("resp,peak")$ via the wrapped angular distance $|"atan2"(sin(hat(phi) - mu), cos(hat(phi) - mu))|$.

#bibliography("references.bib", style: "apa")
