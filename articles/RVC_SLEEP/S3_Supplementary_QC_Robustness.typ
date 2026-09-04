// S3 Supplementary QC and Robustness — RVC_SLEEP

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "S3 QC/Robustness - RVC_SLEEP",
  subtitle: "Sample/epoch coverage, anchor QC, the full robustness/confound audit, and a reviewer-facing summary",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S3.0 Sample and epoch coverage overview

#figure(
  clean-table(
    columns: (1.3fr, 0.9fr, 1.1fr, 1.1fr, 1.3fr),
    align: (left, center, center, center, center),
    inset: 4.5pt,
    table.header([*Dataset*], [*$N$ subj.*], [*Control rows*], [*Event rows*], [*Config hash (16-char)*]),
    [ANPHY (primary)], [27], [34,263], [1,076], [`b6d72c504414c540`],
    [ANPHY (anchor-aug)], [27], [34,263], [1,076], [`e52ce463339d642b`],
    [BOAS (primary)], [128], [192,312], [634], [`19e24fb3acea8f8e`],
    [BOAS (anchor-aug)], [128], [192,312], [634], [`1374fa95bc12d6d1`],
    [RichSleep (primary)], [24], [32,931 (control cond.)], [46,058 (raw, all bins), 3,900 (N2-filtered)], [`0c8d751c52029306`],
  ),
  caption: [`run_manifest.json` sanity check: config-hash match and subject-count match, all 5 runs `pass=True`. RichSleep figures are from the QA-corrected `neuralmanifolddynamics_RichSleep_20260709_100219` ingest (S1.0). Sources: `results/rvc_sleep_20260702/00_sanity_check/run_manifest_check.csv`; `results/rvc_sleep_20260709/09_richsleep_verification/sanity_check.csv`.]
) <tab-epoch-coverage>

#figure(
  clean-table(
    columns: (1.2fr, 1.2fr, 0.9fr, 1fr),
    align: (left, left, center, center),
    inset: 4.5pt,
    table.header([*Dataset*], [*bin_label*], [*Condition*], [*$N$ rows*]),
    [ANPHY], [control], [matched_control], [34,263],
    [ANPHY], [event], [spindle_event], [1,076],
    [ANPHY], [pre_far / pre_near], [spindle_event], [7,151 / 3,568],
    [ANPHY], [post_far / post_near], [spindle_event], [6,985 / 2,465],
    [BOAS], [control], [matched_control], [192,312],
    [BOAS], [event], [spindle_event], [634],
    [BOAS], [pre_far / pre_near], [spindle_event], [4,226 / 2,122],
    [BOAS], [post_far / post_near], [spindle_event], [4,114 / 1,477],
  ),
  caption: [Full condition $times$ bin_label row coverage (see the QC figure in the main text). Source: `results/rvc_sleep_20260702/00_sanity_check/event_locked_coverage.csv`.]
) <tab-bin-coverage>

= S3.1 Physiological (anchor) QC and coverage

#figure(
  clean-table(
    columns: (1fr, 1.7fr, 1fr, 1.3fr),
    align: (left, left, center, center),
    inset: 4.5pt,
    table.header([*Dataset*], [*Column*], [*NaN rate*], [*$N$ subj. valid (pre_far)*]),
    [ANPHY], [`ecg_hrv_rmssd_ms`], [$0.0%$], [27/27],
    [ANPHY], [`ecg_hrv_sdnn_ms`], [$0.0%$], [27/27],
    [ANPHY], [`ecg_hrv_pnn50`], [$0.0%$], [27/27],
    [BOAS], [`resp_regular_index`], [$64.71%$], [61/128],
    [BOAS], [`resp_depth_index`], [$64.71%$], [61/128],
    [BOAS], [`resp_rate_bpm`], [$64.71%$], [61/128],
    [BOAS], [`anchor_index_v02`], [$0.99%$], [122/128],
    [RichSleep], [`cardioresp_anchor_index`], [$0.0%$], [24/24 (base filter); 24/24 usable in R6 after event/subject dropna],
    [RichSleep], [`anchor_index`, `anchor_index_v02`, `sympathetic_index`, `vagal_index`, `resp_anchor_index`, `ocular_stability_index`], [$0.0%$ (all)], [24/24 (base filter)],
    [RichSleep], [`ecg_quality_quality`, `resp_quality_quality`, `eog_quality_quality`, `cardioresp_quality_quality`], [$0.0%$ (all, mean$=1.0$)], [24/24],
  ),
  caption: [Anchor and anchor-quality coverage. RichSleep is the only dataset with simultaneous near-complete cardiac + respiratory + ocular coverage; ANPHY has complete cardiac-only coverage; BOAS's single respiratory anchor is majority-missing (~66/128 subjects with no usable respiratory channel), the key limitation that motivated re-testing EAP moderation on RichSleep (manuscript R6). Sources: `results/rvc_sleep_20260702/00_sanity_check/anchor_nan_rates.csv`; `results/rvc_sleep_20260709/09_richsleep_verification/sanity_check.csv`.]
) <tab-anchor-qc>

= S3.2 EEG/EOG artifact balance across datasets

A dedicated cross-task EOG/EMG artifact-balance follow-up (as run in the sister gambling article) was not re-run for RVC_SLEEP; instead, per-row `eog_quality_quality`, `ecg_quality_quality`, `resp_quality_quality`, and `cardioresp_quality_quality` flags (0/1) are carried as covariates directly into the Pass C / RichSleep EAP-moderation models (S1.6, S2.6), so that any gross artifact-driven anchor unreliability is mean-centered out of the moderation coefficient rather than assessed as a separate balance check. All four quality flags show 100% coverage (mean $= 1.0$, i.e. no rows flagged unusable) in RichSleep's event-locked export (Table @tab-anchor-qc); this is an open follow-up to formally re-verify epoch-by-epoch, not merely at the aggregate level.

= S3.3 Robustness and confound audit (full results)

=== Subject-weighted vs. event-weighted estimand

The pre-amendment, event-weighted OLS-intercept estimator (`02_pass_a1_rvc_specificity.py`, A1-original) is retained only as a sensitivity table; it is not reported in the main text because BOAS's uneven per-subject event counts (median 5, range 1-18) let a small number of high-event-count subjects dominate the pooled estimate, and because its covariate set (including `window_center_sec`) was not mean-centered, making its fitted intercept an out-of-sample extrapolation rather than a directly interpretable population mean (a documented limitation, `results/frozen_evidence_summary_20260703.md` §3.6). The subject-weighted A1r/A2r estimator (S1.5) was adopted as the corrected primary specifically to fix this.

=== Leave-one-subject-out and bootstrap

Not run as a separate pass in the current freeze; the subject-level sign-flip permutation test (S1.5) and the one-sample $t$/Wilcoxon sensitivity pair serve the same robustness role (testing whether the grand-mean direction is driven by a small subset of subjects) without requiring a separate LOOSO re-fit. A dedicated LOOSO/bootstrap pass is a candidate follow-up if a reviewer requests it specifically (S3.4).

=== Within-subject permutation

This *is* the primary inferential test used throughout (S1.5): $n=2000$ subject-level sign-flip permutations per (endpoint, dataset) cell, seed 42, for A1r, A2r, and the RichSleep replication (R6); a companion per-subject-slope sign-flip permutation for Pass C / RichSleep EAP moderation (S2.4, S2.5).

=== Artifact balance

See S3.2; carried as mean-centered nuisance covariates in the moderation models rather than as a stand-alone contrast.

=== Physiological confound controls

Nuisance covariates (`event_duration_sec`, `window_center_sec`, and the anchor-quality/secondary-anchor indices, S2.6) are mean-centered and included in every Pass C / RichSleep moderation model specifically to control for detector-strength/time-of-night/anchor-reliability confounds before estimating the anchor coefficient of interest.

= S3.4 Follow-ups

== S3.4a Surface-sensitivity follow-up (Pass B detail)

Full 36-row table in S2.3. Reading: the anchor-augmented surface behaves exactly as a construction-validity check should - only `e_m` (directly modified) and, weakly, `e` (which recomposes from `e_m`) respond to anchor injection; the other 7 endpoints are byte-identical across surfaces in both datasets and both delta modes. 0/36 FDR-status flips. This confirms the dual-surface export is doing what it is supposed to do; it is explicitly *not* an EAP-moderation test (manuscript R5 guardrail).

== S3.4b RichSleep sensitivity-anchor follow-up (detail)

Several RichSleep sensitivity anchors (`anchor_index`, `sympathetic_index`, `ocular_stability_index`) show nominally FDR-significant coefficients on the order of $10^(-8)$-$10^(-9)$ per raw unit (S2.5) - three to four orders of magnitude smaller in absolute effect than the primary anchor's null-but-comparably-scaled coefficients. Given that these composite indices are raw, non-standardized scales with very large ranges, and that several of these rows are discordant with their own subject-level-slope sensitivity check ($p_"slope"$ not matching the pooled $p$), the most defensible reading is a scale/multicollinearity artifact of the pooled WLS fit rather than a genuine secondary-anchor moderation effect. This is flagged, not silently omitted, and is a candidate follow-up (standardizing all composite anchors to $z$-scores before the moderation fit) if pursued further.

== S3.4c A1/A2 decomposition (detail)

Full decomposition results in S2.2. This follow-up was essential rather than optional: without it, the `d_n` A1r sign conflict between ANPHY and BOAS (Table S2.0) would have been misread as a failure to replicate, when it is in fact fully explained by a dataset-specific difference in how each cohort's pre-spindle baseline compares to its own matched-control distribution, with the timing component ($A$) agreeing in sign in both datasets.

== S3.4d RichSleep A2r power follow-up (detail)

RichSleep's A2r within-spindle timing replication (S2.1) used 160 paired events across all 24 subjects on the corrected ingest (up from 78 events / 19 subjects on the earlier, buggy ingest), versus 1,037 (ANPHY) and 575 (BOAS) - still roughly 6-7$times$ fewer paired events than either frozen dataset. The two headline endpoints (`d_n`, `e_s`) still do not survive FDR ($q=0.72$, $q=0.71$), though two non-primary endpoints (`e_e`: $q=0.0045$; `e_m`: $q=0.036$) now do with the larger, corrected sample. Given the effect sizes observed in ANPHY/BOAS (subject-mean deltas $approx 0.04$-$0.17$ for `d_n`), the still-modest paired-event count is consistent with continued underpowering for the primary timing claim rather than a genuine null. An honest follow-up is an event-bin-restricted RichSleep A1r plus A/B/C decomposition, not pooling across peri-event bins (that would switch estimands).

== S3.4e RichSleep phase-resolved EAP mechanism follow-up (Aim B/C, manuscript R6b)

Full tables in S2.6. Both mechanism-level tests (spindle-onset cardiac/respiratory phase-locking; HEP-amplitude moderation of the geometry response) ran on a smaller population than R6's tonic mixed-bin rows - 190 of 2,253 raw `event`-bin spindle rows, 24 subjects, ~7-8 events/subject on average - because they require an exact-onset join against `event_phase_v2` and because only 190/2,253 `event`-bin rows have window-centre `stage==2`. That split is a stage-window mismatch (S1.1): YASA used N2 hypnogram epochs; the event-locked label is the 30 s MNPS window centre. It is not evidence that the detector fired outside N2. Given this smaller sample, both null results (0/48 within-subject + 0/2 second-order Rayleigh tests, including untestable $n=1$–$2$ cells; 0/18 HEP-moderation tests) should be read as *no effect detected at this power*, not as a stronger disconfirmation than R6's tonic null. Mixed-bin tonic $N$ (2,260–2,435) must not be compared with 190 as unique-spindle counts.

== S3.4f `resp_anchor_index` sensitivity-anchor follow-up: artifact checks and resolution

Full detail and tables in S2.5a. Three candidate artifact explanations for the `resp_anchor_index` sensitivity model's non-negligible, FDR-surviving `event_control`-mode coefficients originally observed were tested and ruled out: (1) *scale artifact* - `resp_anchor_index` sat on an ordinary $approx[-1,1]$ scale, unlike the $10^6$-$10^8$-scale raw composites that explain the other sensitivity anchors' negligible-magnitude coefficients; (2) *multicollinearity* - its maximum Spearman correlation with the primary `cardioresp_anchor_index` anchor or any nuisance covariate in the moderation model was $|r| = 0.196$; (3) *single-subject-outlier artifact* - the effect direction held in 18-20/24 subjects at every endpoint and got *more* significant, not less, after excluding the single most extreme subject at each endpoint. Bivariate (anchor-only) and full covariate-adjusted coefficients also agreed closely, ruling out a covariate-adjustment artifact.

None of that explained the finding - tracing `resp_anchor_index`'s exact construction surfaced a fourth, upstream artifact none of the three checks above were designed to catch: a sign bug in the anchor's construction (the already-inverted rate/slowing component was double-negated, so it rewarded fast rather than slow breathers), since corrected (S1.7). Re-running the moderation test against the corrected export: the original `event_control`-mode finding is now a clean null, matching the primary anchor exactly - fully resolved. A *different*, weaker pattern emerged in the `event_prefar` mode on the corrected data (`d`, `e`, `d_n`, `e_s` FDR-significant, `e_e` at the boundary); re-running the same three artifact checks on it finds the same ordinary scale and low multicollinearity. Two further, stricter checks: a joint BH-FDR correction pooling both delta modes' 108 sensitivity-anchor tests together (rather than the two separate 54-test families `09_richsleep_verification.py` corrects within) confirms `d`/`e`/`d_n`/`e_s` ($q<=0.021$) but drops `e_e` from boundary to non-significant ($q=0.073$); and excluding the subject with the single most extreme *raw* anchor value (a different check from excluding the most-extreme-*slope* subject) leaves every coefficient essentially unchanged. `d` is the one endpoint that loses significance specifically under the most-extreme-slope exclusion, and remains the weakest of the four survivors. Given that this anchor's signal has already flipped completely once, this new pattern is reported at low confidence as a hypothesis for a future independently-replicated test rather than a finding, despite surviving every artifact check attempted (S2.5a).

= S3.5 Reviewer-facing robustness summary

#netn-box(title: [Robustness summary])[
  The primary claim (within-spindle $d_n$ timing rise) survives sign-flip permutation and BH-FDR correction in two independent datasets (ANPHY, BOAS). RichSleep's same-estimand A2r test is inconclusive (160 paired events; `d_n` $q=0.72$) and is not rescued by mixed-bin A1r, which is a different estimand, was not event-bin restricted, and was not decomposed. The broader event-vs-control specificity claim is real on most endpoints in ANPHY/BOAS but is shown by explicit decomposition to be baseline-sensitive for `d_n`, `d_s`, and `m` - this is reported, not smoothed over. Anchor-augmented-surface sensitivity (Pass B) behaves exactly as a construction-validity check should and never changes an FDR conclusion. The EAP-moderation null (Pass C) is not attributable to single-channel anchor missingness, because it reproduces on RichSleep's near-fully-covered dual-arm cardiorespiratory anchor under a tonic operationalization, and holds up under two more direct phase-resolved tests as well (R6b, S3.4e), albeit at lower power. The `resp_anchor_index` sensitivity-anchor episode (S2.5a, S3.4f) is now fully resolved for its original form (an upstream construction bug, not a genuine effect) and has produced one new, low-confidence, unreplicated hypothesis in its place - neither version challenges the primary anchor's null. Open items not yet closed: the RichSleep `e_e` A1r sign discrepancy (R6), RichSleep's underpowered A2r replication, the interpretation of RichSleep's small-magnitude sensitivity-anchor coefficients (S3.4b), a sensitivity that uses onset-stage rather than window-stage N2 (S3.4e), event-bin re-fits of RichSleep A1r/tonic EAP, and the new `event_prefar` `resp_anchor_index` pattern (S2.5a, S3.4f) pending independent replication.
]

#bibliography("references.bib", style: "apa")
