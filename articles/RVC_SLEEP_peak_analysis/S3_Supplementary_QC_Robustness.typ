// S3 Supplementary QC and Robustness — RVC_SLEEP_peak_analysis

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "S3 QC/Robustness - RVC_SLEEP_peak_analysis",
  subtitle: "Sample/phase-quality coverage, the full robustness-check audit, R6 sensitivity-check detail, and a reviewer-facing summary",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S3.0 Sample and phase-quality coverage

#figure(
  clean-table(
    columns: (1.5fr, 0.9fr, 1fr, 1.3fr),
    align: (left, center, center, center),
    inset: 4.5pt,
    table.header([*Sample*], [*$N$ subj.*], [*$N$ events*], [*Filter applied*]),
    [Full raw catalog], [24], [23,029], [None (all `event_phase_v2` rows)],
    [Quality-filtered], [24], [20,877 (90.6%)], [`cardiac_phase_quality`$>=0.7$ and `resp_phase_quality`$=1.0$],
    [Geometry-valid, N2-staged subsample], [24], [190 (0.8%)], [N2 stage, `coords_9d_finite`, exact-onset join against event-locked geometry (companion article's R6b population)],
    [Held-out (R6's $mu_("resp,peak")$ estimate)], [24], [22,839 (99.2%)], [Full catalog minus the 190 geometry-valid events (anti-join on (`subject_id`, `onset_sec`))],
  ),
  caption: [Sample definitions and coverage. Every subject contributes to every sample (no subject-level attrition at any filtering stage). Sources: `results/rvc_sleep_20260710/{11_richsleep_maalb_corrected,13_peak_phase_alignment_moderation}/`.]
) <tab-sample-coverage>

The 9.4% of events dropped by the quality filter and the 99.2% dropped by the geometry-valid filter are not random with respect to sleep depth or event duration in general, but the quality filter's effect on the headline result is small in either direction (compare full-catalog vs. quality-filtered rows, main text Tables 2-3): both samples agree in sign and significance pattern throughout R2-R3.

= S3.1 Robustness-check audit (full detail, companion to main text R4)

=== Phase-convention calibration

Pass: `inhale_at_onset`'s sign convention is internally consistent with `phi_resp_onset`'s documented sign in both directions (mean $phi_"resp,onset" = -1.587$ rad when `inhale_at_onset`$=1$, expected negative per the documented convention; $+1.588$ rad when $=0$, expected positive). This is a schema-drift sanity check, not a novel result; it passing means the peak-phase physiological labels reported throughout this article (e.g. "$32%$ of the way to full inhale-peak") can be trusted against RichSleep's own documented phase convention.

=== Onset-to-peak advance characterization

Median time-to-peak is 0.430 s, correlating strongly with event duration ($r=0.842$) - consistent with an amplitude-envelope-peak detector, where a longer event has more room for its peak to occur later relative to onset. The respiratory onset-to-peak phase advance (median 0.669 rad, IQR $[0.436, 0.986]$) implies a local respiratory period of $approx 4.04$ s ($approx 14.8$ breaths/min), a physiologically ordinary rate - a reassuring sanity check that the peak-phase channel is not some numerically degenerate transformation of the onset-phase channel, but a genuinely different (and, per the results, more strongly locked) quantity. The cardiac advance (median 1.340 rad, std 2.050) is far more dispersed, because `time_to_peak` frequently spans multiple RR intervals ($approx 0.8$-$0.9$ s each) - the mechanistic reason `phi_cardiac_peak` carries materially different information from `phi_cardiac_onset` rather than being a fixed rotation of it.

A logical note completes this check: convolving a uniform (null) onset-phase distribution with *any* rotation that is independent of the onset-phase value itself is still uniform in expectation, so a data-dependent onset-to-peak rotation cannot, by itself, mechanically manufacture the observed peak-phase $R_1$ out of a genuinely uniform onset distribution. The duration-tercile re-test (main text Table 3) checks this empirically regardless, and finds the respiratory effect stable across all three duration terciles - the strongest available evidence against a duration-tail-driven artifact.

=== Leave-one-subject-out and split-half

Both reported in full in the main text (R4) and S2.3/S2 respectively. Summary: respiratory peak-phase locking survives every one of 24 single-subject removals on both the second-order and pooled-permutation statistic, and replicates independently in both halves of a deterministic 12/12 subject split. Cardiac peak-phase locking loses pooled significance in 2/24 leave-one-out reruns and fails to replicate in one of the two split halves entirely (half A: $p=0.530$, null) - the single most decisive piece of evidence that the cardiac effect should not be treated on the same evidentiary footing as the respiratory one.

= S3.2 R6 (alignment-moderation) sensitivity-check detail

The full 18-test alignment-moderation table (S2.4) includes three sensitivity checks alongside the primary WLS-cluster coefficient: a one-sample $t$-test and a Wilcoxon signed-rank test on the 20 per-subject slopes (`min_events=3`, so 20/24 subjects contribute), and a within-subject sign-flip permutation test on the same slopes. For the two BH-FDR survivors:

#figure(
  clean-table(
    columns: (0.7fr, 1fr, 1fr, 1fr, 1.4fr),
    align: (left, center, center, center, left),
    inset: 4.5pt,
    table.header([*Endp.*], [*WLS-cluster $q$*], [*slope $t$-test $p$*], [*slope Wilcoxon $p$*], [*Reading*]),
    [`d`], [0.021], [0.077 (ns)], [0.044], [Wilcoxon agrees; $t$-test and sign-flip permutation ($p=0.068$) borderline/ns],
    [`d_l`], [0.005], [0.105 (ns)], [0.014], [Wilcoxon agrees; $t$-test and sign-flip permutation ($p=0.10$) ns],
  ),
  caption: [Neither survivor has unanimous agreement across all three companion sensitivity checks. This is a materially weaker robustness profile than, e.g., the respiratory peak-phase-locking result's unanimous 4-check agreement (S3.1) and is the primary reason R6 is reported as fragile/exploratory rather than as a second confirmed finding (main text R6, Discussion).]
) <tab-r6-sensitivity>

The pattern - WLS-cluster and Wilcoxon agree, parametric $t$-test and permutation test do not - is consistent with a right-skewed or outlier-influenced distribution of per-subject slopes (Wilcoxon and the sign-flip permutation test use different aspects of the same slope distribution; the fact that they disagree with each other, not just with the $t$-test, argues against a simple "one test is just less powerful" explanation and toward a more genuinely borderline effect). No further outlier-exclusion or alternative-estimator follow-up was run for this exploratory secondary analysis; this is listed as an open follow-up (main text Limitations), not resolved here.

= S3.3 Reviewer-facing robustness summary

#netn-box(title: [Robustness summary])[
  *Timing pathway (R2-R5, this article's primary claim).* Onset-phase locking is null at $approx 120 times$ the companion study's original sample size - not a power artifact, a genuine null for that specific reference point. Peak-phase locking is a different story: the respiratory channel is robust across every one of four independent checks (duration-tercile, LOSO, split-half, phase-convention calibration) and is treated as an established, internally-validated result of this article. The cardiac channel is directionally similar but fails two of the same checks (duration-dependence, one split-half failure) and is explicitly *not* built upon further (R6 tests respiration only). *Efficacy pathway (R6, secondary).* A small, exploratory 18-test family finds 2 BH-FDR survivors, with only partial (not unanimous) agreement across three companion sensitivity checks, and a fragile own robustness profile - reported honestly as a hint worth independent replication, not as a second confirmed finding riding on R2-R5's stronger evidentiary base. Open items not yet closed: R6's post-hoc/exploratory origin, the single-dataset limitation (no ANPHY/BOAS phase-resolved export exists), the absent endogenous-strength (SO-spindle-coupling/amplitude) covariate, and the 30 s/epoch geometry-resolution ceiling that caps how phase-resolved R6's *outcome* variable can ever be, independent of how precisely phase itself is measured (main text Limitations).
]

#bibliography("references.bib", style: "apa")
