#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "S3 QC/Robustness — MNJ Task Geometry (ds004511)",
  subtitle: "Quality control, ten-part confound audit, and reviewer-facing robustness summary",
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

Of 45 subjects, 44 contributed valid GG data. One subject (`sub-S200203`) had zero valid GG epochs and was excluded from GG analyses only (no GG EEG acquisition exists for this subject; dataset README documents a recording-time technical error). This subject contributed valid CC and Rest data, so 45 subjects contributed CC data and 45 contributed Rest data. The intersection sample used for the confound audit (S3.3) requires valid Jacobian data in all three tasks and comprises $N = 44$ subjects.

#figure(
  clean-table(
    columns: (1.6fr, 1fr, 1fr, 1fr, 1fr),
    table.header([*Task*], [*$N$ subj. (valid)*], [*Mean ep./subj.*], [*Median ep./subj.*], [*Range*]),
    [Gambling], [44 / 45], [891], [910], [0–1164],
    [Cognitive control], [45 / 45], [262], [261], [227–332],
    [Rest], [45 / 45], [126], [124], [121–150],
  ),
  caption: [Epoch coverage by task ($N = 45$ subjects total). One gambling session (`sub-S200203`) has zero valid epochs, due to a genuinely missing GG EEG acquisition (see S1.0, S3.0), and is excluded from GG-specific analyses; its row is included in the mean/median/range above as 0 to reflect true coverage across all 45 subjects. Gambling's much longer task duration is the motivation for the epoch-count-matched sensitivity analysis (S3.3, part B). Source: `00_sanity_check/epoch_coverage.csv`.]
) <tab-epoch-coverage>

= S3.1 Physiological QC pass rates

#figure(
  image("figures/fig6_qc_coverage.svg", width: 62%),
  caption: [Respiration and EDA epoch-level QC pass rates by task (duplicated from the main text Fig. 6 for supplement completeness).]
) <fig-qc-s3>

#figure(
  clean-table(
    columns: (1.8fr, 1.2fr, 1.6fr),
    table.header([*Task*], [*Resp. QC pass rate*], [*EDA QC pass rate*]),
    [Gambling], [73.4%], [98.8%],
    [Cognitive control], [85.1%], [98.3%],
    [Rest], [57.7%], [99.7%],
  ),
  caption: [Mean epoch-level QC pass rate by task and modality, averaged across subjects. Respiration QC is substantially lower during Rest (57.7%), consistent with irregular/shallow breathing during eyes-closed passive rest; despite this, `qc_ok_for_eap` (the composite subject-level gate requiring adequate respiration data in at least one usable task pairing) is satisfied for 97.8% of subjects (44/45). EDA QC is uniformly high ($>$98%) across all three tasks because the session-level rejection gate (S1.3) removes the small number of fully bad sessions rather than sporadic epochs. Source: `00_sanity_check/resp_qc_by_subject_task.csv`, `subject_qc_flags.csv`, `06_eda_extraction/eda_qc_summary.csv`.]
) <tab-qc-pass-rates>

Five EDA sessions across three subjects were rejected outright at the session-quality gate (flat/saturated signal): `sub-S201222` Rest; `sub-S200303` Rest; and `sub-S201210` Rest, CC, and GG. Separately, one GG session (`sub-S200203`) produced zero valid epochs and was excluded from GG analyses across all modalities, not only EDA (see S3.0 for the per-subject reason).

= S3.2 EEG/EOG artifact balance across tasks

To rule out differential artifact contamination as an alternative explanation for the MNJ task effect (audit part F, S1.6), EEG/EOG quality flags and artifact-proxy features were tabulated by task across the intersection sample.

#figure(
  kind: table,
  clean-table(
    columns: (1.8fr, 1fr, 1fr, 1fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Gambling*], [*Cognitive control*], [*Rest*]),
    [`qc_ok_eeg` (mean)], [`1.000`], [`1.000`], [`1.000`],
    [`qc_ok_eog` (mean)], [`1.000`], [`1.000`], [`1.000`],
    [`eog_blink_rate` (mean ± SD)], [`0.42 ± 0.30`], [`0.44 ± 0.33`], [`0.19 ± 0.29`],
    [`eog_artifact_fraction` (mean ± SD)], [`0.0009 ± 0.013`], [`0.0012 ± 0.011`], [`0.0003 ± 0.004`],
    [`eeg_highfreq_power_30_45` (mean ± SD)], [`0.149 ± 0.647`], [`0.144 ± 0.341`], [`0.705 ± 3.919`],
    [`eeg_hjorth_complexity` (mean ± SD)], [`2.331 ± 0.827`], [`2.266 ± 0.785`], [`2.298 ± 0.562`],
    [`eeg_permutation_entropy` (mean ± SD)], [`0.905 ± 0.021`], [`0.908 ± 0.021`], [`0.873 ± 0.050`],
  ),
  caption: [EEG/EOG artifact-proxy features by task, intersection sample ($N = 44$). Both `qc_ok_eeg` and `qc_ok_eog` are at or near 1.0 for all tasks (no differential quality gate failure). Blink rate is markedly lower at Rest (eyes closed, fewer voluntary blinks) — the opposite direction from what would be needed to explain higher GG deformation via blink artifact. High-frequency (30–45 Hz, EMG-contamination proxy) power is *higher* at Rest, not GG, ruling out muscle-artifact contamination as an explanation for the GG-selective Frobenius effect. Hjorth complexity and permutation entropy are closely matched across all three tasks. Source: `05_mnj_confound_audit/artifact_balance.csv`.]
) <tab-artifact-balance>

= S3.3 Ten-part robustness and confound audit (full results)

This section reports the complete numerical results underlying the audit protocol described in S1.6, run in response to the science-lead review (`sciencelead/001.md`, `sciencelead/002.md`).

*(A) Intersection sample.* Restricting the primary MNJ contrasts to the $N = 44$ subjects with valid data in all three tasks:

#figure(
  kind: table,
  clean-table(
    columns: (1.5fr, 1.6fr, 1fr, 0.9fr, 0.7fr),
    align: left,
    inset: 3.5pt,
    table.header([*Metric*], [*Contrast*], [*$d$*], [*FDR $q$*], [*Sig.*]),
    [`frobenius_norm`], [GG vs CC], [`1.620`], [`5.6e-12`], [Yes],
    [`frobenius_norm`], [GG vs Rest], [`0.738`], [`2.8e-5`], [Yes],
    [`frobenius_norm`], [CC vs Rest], [`-0.263`], [`0.196`], [No],
    [`spectral_radius`], [GG vs CC], [`1.808`], [`5.6e-12`], [Yes],
    [`rotational_power`], [GG vs CC], [`-1.025`], [`1.1e-7`], [Yes],
    [`aci`], [GG vs CC], [`-1.015`], [`1.0e-7`], [Yes],
    [`mdr`], [GG vs CC], [`0.420`], [`0.006`], [Yes],
  ),
  caption: [Selected rows from the intersection-sample re-analysis (all 21 rows in `mnj_intersection_wilcoxon.csv`); the GG vs. CC Frobenius effect is numerically identical to the full-sample result because GG's own valid-subject set already coincides with $N = 44$. Only the CC vs. Rest contrast changes appreciably (full sample $N = 45$, $d = -0.229$, $p_"fdr" = 0.243$ vs. intersection $N = 44$, $d = -0.263$, $p_"fdr" = 0.196$) — a negligible, non-significant difference in both cases.]
) <tab-intersection>

*(B) Epoch-count matching.* Subsampling each subject to the minimum epoch count across their three tasks (median $approx$122 epochs) before recomputing medians:

#figure(
  kind: table,
  clean-table(
    columns: (1.5fr, 1.6fr, 1fr, 1fr, 0.7fr),
    align: left,
    inset: 3.5pt,
    table.header([*Metric*], [*Contrast*], [*Full-sample $d$*], [*Epoch-matched $d$*], [*Sig. (matched)*]),
    [`frobenius_norm`], [GG vs CC], [`1.620`], [`1.444`], [Yes],
    [`frobenius_norm`], [GG vs Rest], [`0.738`], [`0.690`], [Yes],
    [`spectral_radius`], [GG vs CC], [`1.808`], [`1.668`], [Yes],
    [`rotational_power`], [GG vs CC], [`-1.025`], [`-0.685`], [Yes],
    [`aci`], [GG vs CC], [`-1.015`], [`-0.687`], [Yes],
    [`mdr`], [GG vs CC], [`0.420`], [`0.461`], [Yes],
  ),
  caption: [Epoch-count-matched sensitivity analysis. All primary GG-involving contrasts remain significant after equalizing epoch counts across tasks; effect sizes shrink modestly (Frobenius: $-11%$; rotational power/ACI: $-33%$) but no contrast changes sign or significance direction. This confirms that GG's much larger epoch count (mean 891 vs. 262 for CC, 126 for Rest) is not the primary driver of the observed effects. Full 21-row table: `05_mnj_confound_audit/mnj_epoch_matched_wilcoxon.csv`.]
) <tab-epoch-matched>

*(C) Leave-one-subject-out (LOOSO).*

#figure(
  kind: table,
  clean-table(
    columns: (1.5fr, 1fr, 1fr, 1fr, 1.1fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Full $d$*], [*LOO min $d$*], [*LOO max $d$*], [*Sign-consistent*]),
    [`frobenius_norm`], [`1.620`], [`1.595`], [`1.711`], [`44/44`],
    [`spectral_radius`], [`1.808`], [`1.781`], [`1.943`], [`44/44`],
    [`rotational_power`], [`-1.025`], [`-1.112`], [`-1.003`], [`44/44`],
    [`aci`], [`-1.015`], [`-1.096`], [`-0.993`], [`44/44`],
  ),
  caption: [LOOSO robustness for the four primary GG vs. CC effects ($N = 44$ iterations each). All four metrics retain their sign in 100% of leave-one-out iterations, and all 44 LOO iterations remain significant at $p < 0.05$ (`loo_frac_p05 = 1.0` for all four metrics). No single subject drives the effect. Source: `05_mnj_confound_audit/mnj_looso.csv`.]
) <tab-looso>

*(D) Bootstrap confidence intervals* (2000 resamples, 95% CI on Cohen's $d$):

#figure(
  kind: table,
  clean-table(
    columns: (1.5fr, 1fr, 1fr, 1fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*$d$*], [*95% CI*], [*Excludes 0*]),
    [`frobenius_norm`], [`1.620`], [`[1.306, 2.128]`], [Yes],
    [`spectral_radius`], [`1.808`], [`[1.451, 2.441]`], [Yes],
    [`rotational_power`], [`-1.025`], [`[-1.415, -0.743]`], [Yes],
    [`aci`], [`-1.015`], [`[-1.384, -0.745]`], [Yes],
  ),
  caption: [Bootstrap 95% confidence intervals for the four primary metrics ($N = 44$, percentile method). All four intervals exclude zero by a wide margin. Source: `05_mnj_confound_audit/mnj_bootstrap.csv`.]
) <tab-bootstrap-full>

*(E) Within-subject permutation test* (5000 sign-flip permutations):

#figure(
  clean-table(
    columns: (1.5fr, 1.4fr, 1fr),
    table.header([*Metric*], [*Observed median $Delta$*], [*Permutation $p$*]),
    [`frobenius_norm`], [`+0.0277`], [`< 0.0002`],
    [`spectral_radius`], [`+0.0156`], [`< 0.0002`],
    [`rotational_power`], [`-0.0304`], [`< 0.0002`],
    [`aci`], [`-0.0513`], [`< 0.0002`],
  ),
  caption: [Within-subject sign-flip permutation test (5000 permutations). 0/5000 label-shuffled permutations produced a median difference as extreme as the observed one, for any of the four primary metrics; exact $p = 0$ is reported as $< 0.0002$. Source: `05_mnj_confound_audit/mnj_permutation.csv`.]
) <tab-permutation>

*(F) Artifact balance*: see S3.2.

*(G) Physiological confound partial correlations*: the initial physiological-confound set contained five candidates (HR, respiration rate, respiratory anchor index, EOG blink rate, tonic EDA); the combined seven-row table, extended with corrugator EMG (part H) and Sync-pulse event rate (part J), is reported in S2.6. None of the seven candidate confounds survives BH-FDR correction (all $q > 0.20$).

*(H) Corrugator-EMG confound*: see S3.4b. Corrugator EMG does not differ between GG and CC ($d = 0.08$, $p = 0.51$) and does not correlate with the GG−CC Frobenius difference ($r_s = -0.08$, $p = 0.60$).

*(I) Conventional-EEG baseline comparison*: see S3.4c. The largest of 16 conventional-EEG GG-vs-CC effect sizes (relative theta power, $d = 0.63$) is less than half the primary MNJ Frobenius effect ($d = 1.62$).

*(J) Event/response-rate sensitivity*: see S3.4d. Session-level Sync(1) pulse rate is higher in CC than GG (opposite of a naive event-density account), the GG−CC event-rate difference is uncorrelated with the GG−CC Frobenius difference ($r_s = -0.05$, $p = 0.77$), and the effect is undiminished ($d = 1.70$ vs. $d = 1.62$) when restricted to below-median-event-density epochs in both tasks.

= S3.4 EDA, corrugator-EMG, conventional-EEG, and event-rate follow-ups

== S3.4a EDA confound follow-up (Script 07 detail)

The EDA confound test was run as a dedicated follow-up (`07_eda_confound_control.py`) once the standalone EDA extraction (Script 06) was complete, extending the four-confound table from Script 05 to five confounds.

#figure(
  clean-table(
    columns: (2fr, 1fr, 1fr, 1fr),
    table.header([*Test*], [*$r_s$*], [*$p$*], [*$N$*]),
    [EDA tonic SCL diff. × Frobenius diff. (GG−CC)], [`-0.10`], [`0.51`], [`43`],
  ),
  caption: [EDA-specific confound test: Spearman correlation between the subject-level GG−CC difference in tonic EDA (SCL) and the GG−CC difference in MNJ Frobenius norm. The null result ($r_s = -0.10$, $p = 0.51$) is consistent with, and independently corroborates, the direct EDA GG-vs-CC comparison reported in the main text R5 ($d = -0.07$, $p = 0.55$): tonic sympathetic arousal is statistically indistinguishable between gambling and cognitive control both in absolute level and in its subject-level covariation with the neural flow-geometry effect. Source: `07_eda_confound_control/eda_confound_partial.csv`.]
) <tab-eda-confound-detail>

== S3.4b Corrugator-EMG confound follow-up (Script 10 detail)

Once the BioPac `EMGA`/`EMGB` corrugator-supercilii channels were added to the NMD ingestion config (`config_ingest_ds004511.yaml`, `physio_tsv_inject`) and the pipeline was re-run, `10_corrugator_emg_confound.py` computed the direct GG/CC/Rest contrast on tonic `emg_rms` and its confound-partial test against the Frobenius difference, extending the five-confound table to six.

#figure(
  clean-table(
    columns: (2.3fr, 1fr, 1fr, 1fr),
    table.header([*Test*], [*$d$ or $r_s$*], [*$p$*], [*$N$*]),
    [`emg_rms` GG vs CC (direct contrast)], [$d=0.08$], [`0.51`], [`44`],
    [`emg_rms` GG vs Rest (direct contrast)], [$d=0.54$], [`< 0.001`], [`44`],
    [`emg_rms` CC vs Rest (direct contrast)], [$d=0.57$], [`< 0.0001`], [`44`],
    [EMG diff. × Frobenius diff. (GG−CC)], [$r_s=-0.08$], [`0.60`], [`44`],
  ),
  caption: [Corrugator-EMG confound test. Tonic corrugator EMG is matched between GG and CC (like EDA) but, unlike EDA, is elevated in both active tasks relative to rest — plausibly reflecting general facial/postural muscle tone during eyes-open tasks versus eyes-closed rest, rather than a task-specific affective signal. The confound-partial test ($r_s = -0.08$, $p = 0.60$) shows no relationship between the subject-level GG−CC EMG difference and the GG−CC Frobenius difference, closing the corrugator-EMG confound question raised for the primary effect. Source: `10_corrugator_emg_confound/emg_descriptive_wilcoxon.csv`, `emg_confound_partial.csv`.]
) <tab-emg-confound-detail>

== S3.4c Conventional-EEG baseline comparison (Script 09 detail)

#figure(
  clean-table(
    columns: (2.6fr, 1fr, 1fr, 1fr),
    table.header([*Conventional-EEG feature (GG vs CC)*], [*$d_z$*], [*$p$*], [*FDR $q$*]),
    [Relative theta power], [`0.63`], [`1.7e-4`], [`3.5e-4`],
    [Alpha/theta ratio], [`-0.38`], [`0.024`], [`0.038`],
    [Spectral-edge frequency (95%)], [`-0.36`], [`0.008`], [`0.015`],
    [Theta/alpha ratio], [`0.31`], [`0.037`], [`0.056`],
    [Hjorth complexity], [`0.29`], [`0.030`], [`0.047`],
  ),
  caption: [Largest five (of 16) conventional-EEG GG-vs-CC effect sizes, $N = 44$ intersection sample. For comparison, the primary MNJ effects on the same sample are Frobenius norm $d = 1.62$ and spectral radius $d = 1.81$ — roughly $2.6$–$4.5 times$ larger than the strongest conventional-EEG metric. 31/48 conventional-EEG contrasts (all three task pairs) survive BH-FDR at 5%, confirming these are genuine, well-powered effects and not just power-law noise; they are simply much smaller than the MNJ geometric effect for the GG-vs-CC contrast specifically. Source: `09_conventional_eeg_baseline/conventional_eeg_wilcoxon.csv`, `conventional_vs_mnj_summary.csv`.]
) <tab-conventional-eeg-detail>

== S3.4d Event/response-rate sensitivity follow-up (Script 11 detail)

Raw BIDS `events.tsv` Sync(1) trigger-pulse onsets — dataset-native and independent of NMD ingest — were joined to the H5 epoch windows to test whether the two tasks' differing event/response-rate structure could explain the GG$>$CC Frobenius effect (`11_event_density_sensitivity.py`; see main-text §R5b and S1.6(J) for method).

#figure(
  clean-table(
    columns: (2.6fr, 1fr, 1fr, 1fr),
    table.header([*Test*], [*$d_z$ or $r_s$*], [*$p$*], [*$N$*]),
    [Session event rate: GG vs CC (direct contrast)], [$d_z = -4.00$], [`< 0.0001`], [`44`],
    [Session event rate: GG vs Rest (direct contrast)], [$d_z = 19.8$], [`< 0.0001`], [`44`],
    [Session event rate: CC vs Rest (direct contrast)], [$d_z = 16.3$], [`< 0.0001`], [`44`],
    [Event-rate diff. × Frobenius diff. (GG−CC)], [$r_s = -0.05$], [`0.77`], [`44`],
    [Epoch event count × Frobenius (within GG)], [$r_s = 0.03$], [`2.1e-9`], [`39,985 epochs`],
    [Epoch event count × Frobenius (within CC)], [$r_s = 0.03$], [`6.8e-4`], [`11,363 epochs`],
    [GG vs CC Frobenius, low-density epochs only], [$d_z = 1.70$], [`< 0.0001`], [`44`],
  ),
  caption: [Event/response-rate sensitivity results. Median session-level Sync(1) pulse rate: GG = 0.357 Hz, CC = 0.453 Hz, Rest = 0.002 Hz — CC's per-second rate is *higher* than GG's, the opposite of a naive "GG is event-dense" account (GG has far more total pulses per session, ~1,285 vs. ~470, but a proportionally much longer session, ~60 vs. ~17 min median). The subject-level GG−CC event-rate difference is uncorrelated with the GG−CC Frobenius difference. A small but statistically significant epoch-level coupling exists within both tasks ($r_s approx 0.03$, $r^2 approx 0.001$), but restricting the GG-vs-CC contrast to each subject's below-median-event-density epochs in both tasks (median 644 GG / 162 CC epochs retained per subject) leaves the effect materially unchanged ($d = 1.70$ vs. $d = 1.62$ full-sample). Source: `11_event_density_sensitivity/session_event_rate.csv`, `event_rate_wilcoxon_by_task.csv`, `event_rate_confound_partial.csv`, `epoch_density_frobenius_correlation.csv`, `density_matched_wilcoxon.csv`.]
) <tab-event-rate-detail>

This section narrows, but does not fully close, the event/response-rate question: the confound-partial and density-matched tests are consistent with a genuine task-geometry effect rather than an event-density artifact, but the small residual epoch-level coupling and the dataset's lack of stimulus/response pulse labeling mean this remains an open, if substantially narrowed, caveat (see main-text Limitations).

This completes the confound and baseline audit requested during science-lead review: all seven tested plausible peripheral-physiological/temporal-structure explanations for the GG$>$CC Frobenius effect (heart rate, respiration rate, respiratory anchoring, EOG blink rate, tonic EDA, corrugator EMG, event/response rate) have been tested; none accounts for the effect, and a matched conventional-EEG baseline comparison confirms the MNJ effect is not a simple restatement of band-power differences. The event/response-rate check narrows rather than fully eliminates this alternative (see main-text Limitations).

= S3.5 Reviewer-facing robustness summary

#figure(
  kind: table,
  clean-table(
    columns: (2.4fr, 1.4fr, 2.6fr),
    align: left,
    inset: 4pt,
    table.header([*Robustness check*], [*Result*], [*Interpretation*]),
    [Intersection sample ($N=44$)], [$d = 1.62$, unchanged], [Not driven by unequal task coverage],
    [Epoch-count matching], [$d = 1.44$ ($approx$11% shrink)], [Not driven by GG's larger epoch count],
    [LOOSO (44 iterations)], [44/44 sign-consistent], [Not driven by any single subject],
    [Bootstrap 95% CI], [`[1.31, 2.13]`], [Excludes zero with wide margin],
    [Permutation test (5000)], [$p < 0.0002$], [Exceeds all label-shuffled nulls],
    [Artifact balance], [No differential contamination], [Not an EEG/EOG artifact],
    [Heart rate confound], [$r_s = -0.06$, $q = 0.83$], [Not a cardiac-arousal confound],
    [Respiration rate confound], [$r_s = -0.29$, $q = 0.20$], [Largest uncorrected signal; does not survive FDR],
    [Respiratory anchor confound], [$r_s = +0.33$, $q = 0.20$], [Does not survive FDR],
    [EOG blink rate confound], [$r_s = -0.20$, $q = 0.44$], [Not an ocular-artifact confound],
    [Tonic EDA confound], [$r_s = -0.10$, $q = 0.83$], [Not a sympathetic-arousal confound],
    [Corrugator EMG confound], [$r_s = -0.08$, $q = 0.83$], [Not a facial-muscle/affect confound],
    [Conventional-EEG baseline], [Largest $d = 0.63$ vs. MNJ $d=1.62$], [Not recoverable from simple band power/complexity],
    [Event-rate confound], [$r_s = -0.05$, $q = 0.77$], [Not an event/response-density confound (narrowed, not fully closed)],
    [Density-matched sensitivity], [$d = 1.70$ (low-density epochs only)], [Undiminished when event-dense epochs excluded],
    [Block-level cross-check], [$d = 1.70$, independent pathway], [Replicates in independent aggregation],
  ),
  caption: [Reviewer-facing summary of the ten-part robustness and confound audit, with individual confound rows expanded, for the primary GG$>$CC MNJ Frobenius-norm effect (report row: Frobenius norm unless noted; more than ten rows appear here because parts 7 and 10 each expand into several individual confound rows). All checks are consistent with a genuine, robust task-geometry effect rather than a sampling, artifact, peripheral-physiological, conventional-EEG-power, or event/response-rate confound.]
) <tab-robustness-summary>

#bibliography("references.bib")
