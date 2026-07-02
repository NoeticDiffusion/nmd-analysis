#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "S1 Methods — MNJ Task Geometry (ds004511)",
  subtitle: "NeuralManifoldDynamics measurement contract, Meta-Noetic Jacobian computation, standalone EDA extraction, and the robustness/confound audit protocol",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S1.0 Dataset and NMD measurement contract

`ds004511` @ds004511 ("Deception_data", Makowski, Pham & Lau; CC0; OpenNeuro DOI version `v1.0.2`) is a publicly available multimodal dataset collected at Nanyang Technological University. The dataset's own README and official participants table list `N = 44` healthy adults; the ingested data release used here contains 45 subject directories, the 45th (`sub-S200203`) present with valid CC/Rest data but not listed in the official demographics table and lacking any GG EEG acquisition (README: "does not have any EEG acquisition file pertaining to the Gambling Game task due to technical errors during the recording"). We report `N = 45` throughout, consistent with the ingested pipeline manifest, and flag this version-specific 44-vs-45 discrepancy explicitly rather than silently reconciling it. Three within-subject conditions were recorded in a single session: a gambling game (GG, raw task label `GG`) — officially the "Spontaneous Deception Task," in the tradition of gambling-based spontaneous-lying paradigms in the deception literature @yin2016 @chen2024deception: a solitary, self-paced task in which participants received an initial stake and completed 144 rounds of privately predicting a dice-roll outcome, placing a bet (10–80 cents) on that prediction, and self-reporting to the system whether the prediction was correct; participants were told this cover story specifically to create an unmonitored opportunity to misreport outcomes, but there is no computerized partner, no cooperate/defect choice, and no social-interaction component — a cognitive control task (CC, raw task label `CC`, a four-part response-inhibition/conflict-resolution battery: processing-speed, response-selection, response-inhibition, and conflict-resolution sub-tasks, 460 trials total), and eyes-closed resting state (Rest, raw task label `Rest`). EEG was recorded with a 128-channel TruScan system; BioPac AcqKnowledge hardware recorded ECG, respiration (RSP), two EMG channels placed over the corrugator supercilii muscle (a standard facial-affect/frowning indicator @larsen2003), and electrodermal activity (EDA), all at 4000 Hz, synchronized to the EEG clock via shared trigger pulses.

As in the sister `embodied_anchoring` articles, the present analyses should be read against the NeuralManifoldDynamics (NMD) measurement contract rather than as direct computations on raw tables. @langell2025ndt Ingest is version-bound: it standardizes modality-specific feature tables, applies fixed release-specific coordinate mappings, estimates local Jacobian structure where the geometry contract permits, and serializes auditable artifacts (H5 summaries, `features.parquet`, `run_manifest.json`) for downstream analysis. Ingest does not adapt coordinate definitions to the specific contrasts tested in this article.

The NMD run used throughout is `neuralmanifolddynamics_ds004511_20260701_193708` (short form: run `193708`), which also computed a conventional-EEG feature pack (band power, band ratios, alpha peak frequency, spectral/permutation entropy, Hjorth complexity) and the two BioPac corrugator-EMG channels (`EMGA`, `EMGB`) alongside the primary MNPS/MNJ geometry. An earlier run (`010029`) had incorrectly excluded two GG sessions (`sub-S200211`, `sub-S210317`) whose EDF files were, at that time, unresolved `git-annex` placeholder stubs (105 bytes) in the local dataset mirror rather than the actual recordings; both were re-fetched in full from the OpenNeuro S3 mirror, hash-verified against their `git-annex` keys, and successfully processed in run `193708`. Independent component analysis removed 1–2 cardiac/ocular components per session, using ECG-derived heartbeat events for component identification (`ECG=["ECG"]`). One GG session produced zero valid epochs and was excluded from GG analyses only: `sub-S200203` (no GG EEG file exists for this subject; documented dataset-level technical error). This subject contributed valid CC and Rest data; 134 of 135 possible sessions ($45 times 3 - 1$) contributed GG/CC/Rest data as applicable.

= S1.1 Epoch structure and MNPS/MNJ export

EEG was segmented into 8-second epochs on a sliding basis (session-specific step size stored in the H5 `/provenance/` group; typical overlap yields several hundred epochs per GG session and $approx 120$–$150$ per CC/Rest session, reflecting the much longer GG task duration). For each epoch, the NMD pipeline exports:

- `mnps_3d` (`m`, `d`, `e`) and its derivative `mnps_3d_dot` — canonical Meta-Noetic Phase Space coordinates
- `jacobian_subject_anchored/J_hat` — the per-epoch $3 times 3$ local Jacobian matrix, subject-anchored (estimated relative to that subject's own MNPS reference frame rather than a population-pooled reference)
- `jacobian_subject_anchored/centers` — the index into `/window_start` identifying which time point each Jacobian estimate corresponds to
- per-epoch ECG/HRV indices (RMSSD, pNN50), respiration metrics (`resp_anchor_index`, `resp_regular_index`, `resp_phase_consistency`, `resp_rate_bpm`, `resp_amplitude_median`), cardiorespiratory coupling (`cardioresp_rsa_amplitude`, `cardioresp_coupling_index`), and EOG stability (`eog_eye_stability_index`, `eog_blink_rate`, `eog_artifact_fraction`)
- regional (network-stratified) MNPS summaries for four cortical networks: frontal, central, parietal-occipital, and temporal
- regional and stratified block-level Jacobian summaries (`regional_block_jacobians_subjects_*.csv`, `stratified_block_jacobians_subjects_*.csv`), aggregated at the task-block level rather than per-epoch

Regional MNPS rows flagged `strat9_falsified = 1` (indicating a failed 9D stratification geometry check for that session) were excluded from network-level analyses, following the standard NMD loader convention (`load_regional_mnps(exclude_falsified=True)`).

= S1.2 Meta-Noetic Jacobian metrics

From each per-epoch $3 times 3$ Jacobian matrix $J$, six scalar summaries were computed directly from the raw `J_hat` tensor (function `compute_mnj_from_J` in `05_mnj_confound_audit.py`, replicating the NMD specification @langell2025ndt):

$ ||J||_F = sqrt(sum_(i,j) J_(i j)^2) quad "(Frobenius norm — total deformation)" $

$ J_"anti" = frac(1,2)(J - J^top), quad "rotation\_norm" = ||J_"anti"||_F $

$ "trace" = sum_i J_(i i) $

$ rho(J) = max_i |lambda_i (J)| quad "(spectral radius — largest-magnitude eigenvalue)" $

$ "rotational\_power" = frac(||J_"anti"||_F^2, ||J||_F^2 + epsilon) $

$ J_"sym" = frac(1,2)(J + J^top), quad "aci" = frac(||J_"anti"||_F, ||J_"sym"||_F + epsilon) quad "(anisotropic compression index)" $

$ "mdr" = frac(sum_i |J_(i i)|, ||J||_F + epsilon) quad "(manifold deformation rate)" $

with $epsilon = 10^{-12}$ throughout to guard against division by zero. `frobenius_norm` and `spectral_radius` were designated primary endpoints (absolute deformation magnitude); `rotation_norm`, `rotational_power`, `aci`, and `mdr` were designated secondary endpoints (directional/structural composition of the deformation). Epoch-level metrics were summarized to one value per subject × task by taking the median across all valid epochs (`frobenius_norm_median`, etc.), matching the convention used throughout the NDT article series.

*Intuition.* Both primary endpoints summarize the same local Jacobian $J$ but capture different geometric aspects of it. $||J||_F$ (Frobenius norm) aggregates deformation across *all* directions simultaneously: a low value means nearby trajectories through that point in state space stay close together and roughly parallel (weak local deformation), while a high value means nearby trajectories are pulled apart, twisted, or redirected substantially over a short distance (@fig-frobenius-intuition). $rho(J)$ (spectral radius) instead isolates the *single most amplified direction*: a low value means no one direction dominates and nearby movement changes only moderately regardless of orientation, while a high value means at least one local direction stretches trajectories rapidly, producing pronounced elongation along a dominant axis even if other directions remain comparatively flat (@fig-spectral-radius-intuition). A region of state space can therefore have high $||J||_F$ without a single dominant stretching direction (isotropic deformation, low `aci`), or a high $rho(J)$ driven by one strongly amplified axis while the aggregate deformation is more modest — this is why both are reported as separate primary endpoints rather than treated as redundant.

#figure(
  image("figures/conceptual/Jacobian_frobenius_norm.png", width: 92%),
  caption: [Conceptual visualization of the Frobenius norm $||J||_F$ as a measure of total local flow deformation. Left: low $||J||_F$ — nearby particle trajectories (blue) through the local vector field (grey arrows) remain smooth and close together. Right: high $||J||_F$ — trajectories through the same class of local vector field are strongly bent, twisted, and redirected, reflecting large aggregate deformation across all directions. Schematic illustration for methodological intuition only; not derived from `ds004511` data.]
) <fig-frobenius-intuition>

#figure(
  image("figures/conceptual/spectral_radius_median.png", width: 92%),
  caption: [Conceptual visualization of the spectral radius $rho(J) = max_i |lambda_i (J)|$ as a measure of dominant local gain. Left: low $rho(J)$ — no single local direction shows strong amplification, so nearby trajectories change only moderately regardless of starting orientation. Right: high $rho(J)$ — at least one local direction amplifies movement strongly, so nearby trajectories stretch rapidly along a dominant axis (shaded bands) while other directions may remain comparatively unamplified. Schematic illustration for methodological intuition only; not derived from `ds004511` data.]
) <fig-spectral-radius-intuition>

Block-level Jacobian summaries (`block_frobenius_mean`, `block_trace_mean`, `block_anisotropy_mean`, `c_rot_mean`) are computed independently by the NMD pipeline's block-aggregation step from task-segment-level (rather than epoch-level) Jacobian fits, and are reported in R3 as a cross-check using an entirely separate aggregation pathway.

= S1.3 EDA extraction (standalone script)

The NMD pipeline ingests the BioPac EDA channel as a miscellaneous channel but, as of run `193708`, does not decompose it into tonic/phasic components or extract epoch-level features. A standalone extraction script, `06_eda_extraction.py`, was written for this article; a full handover note (`handover/eda_extractor_handover.md`) documents the algorithm for future integration into the NMD pipeline proper.

*Input.* Raw `*_physio.tsv.gz` files (BioPac export, tab-separated, 4000 Hz), column index 5 ("EDA, Y, PPGED-R"). The physio column order is time · ECG · RSP · EMG-A · EMG-B · EDA · Digital. Each session's `*_physio.json` sidecar supplies a `StartTime` offset (seconds of physio recording preceding EEG onset) used to align physio sample indices to the `features.parquet` epoch grid (`t_start`, `t_end`).

*Fast I/O.* Because raw physio files range from 25 MB (Rest) to $>$ 200 MB (GG) and reside on a network drive, `pandas.read_csv` was prohibitively slow for a full-cohort run. The extractor instead streams the gzip file line-by-line using Python's built-in `gzip` module and `str.split("\t", col_idx + 1)`, which stops parsing after the needed column — approximately 5–10$times$ faster than a full-table `pandas` read for this file size and column count.

*Downsampling.* The 4000 Hz EDA signal was downsampled to 50 Hz using two cascaded `scipy.signal.decimate` calls with zero-phase filtering ($q = 8$ then $q = 10$, total factor 80). Cascading avoids the numerical instability of a single large-factor IIR decimation.

*Decomposition.* `neurokit2.eda_process` (method `"neurokit"`) @makowski2021neurokit2 was called once per full downsampled session (not per epoch), yielding continuous tonic (`EDA_Tonic`) and phasic (`EDA_Phasic`) component arrays plus SCR peak indices and amplitudes for the entire session. Session-level quality gating rejected sessions with tonic-component range $< 0.01$ µS or session mean outside $(0, 100)$ µS (flat, saturated, or disconnected electrode).

*Per-epoch features.* For each 8-second epoch in `features.parquet`, the corresponding index range in the downsampled tonic/phasic arrays was located and the following scalar features extracted: `eda_tonic_scl` (mean tonic level), `eda_tonic_slope` (linear regression slope of tonic component vs. time within the epoch), `eda_phasic_scr_rate` (SCR count normalized to events/min), `eda_phasic_scr_amp` (mean SCR peak amplitude within the epoch), `eda_phasic_scr_count`, `eda_phasic_auc` (mean absolute phasic signal), and `eda_arousal_index` (SCR rate plus absolute tonic slope, unnormalized composite). Epochs shorter than 2 s of valid downsampled samples were marked `qc_ok_eda = 0` and excluded.

*Run summary.* 55,903 epochs across 129 sessions were processed in 45.2 minutes (of 136 physio files found; the count exceeds $45 times 3$ because `sub-S200303` has a duplicated CC-session physio file in the ingested release, and one additional file could not be matched to an epoch table and was skipped). Five sessions across three subjects were rejected outright at the session-quality gate (`sub-S201222` Rest; `sub-S200303` Rest; `sub-S201210` Rest, CC, and GG — flat or saturated signal); the remaining sessions achieved 98.3–99.7% epoch-level QC pass rates (S3.1 gives the full per-task breakdown). This matches the reported $134 - 5 = 129$ processed sessions exactly ($134$ = $135$ possible subject$times$task combinations minus the one subject with no GG acquisition, `sub-S200203`).

= S1.4 Physiological confound and EAP feature definitions

`resp_anchor_index`, `resp_regular_index`, and `resp_phase_consistency` are NMD-native respiration–MNPS coherence proxies computed from the respiration belt signal; higher values indicate more regular, more strongly phase-locked breathing relative to the concurrent neural trajectory. `cardioresp_rsa_amplitude` and `cardioresp_coupling_index` quantify respiratory sinus arrhythmia amplitude and cardiorespiratory phase coupling from the joint ECG/RSP signal. `emg_rms` is the per-epoch root-mean-square amplitude of the combined `EMGA`/`EMGB` corrugator-supercilii channels, computed by the NMD pipeline's standard EMG feature extractor once these channels were added to `physio_tsv_inject` in `config_ingest_ds004511.yaml`. These features, together with ECG-derived HRV (RMSSD) and EOG-derived blink rate/artifact fraction, constitute the candidate confound set audited against the primary GG vs. CC Frobenius contrast (S1.6).

= S1.5 Statistical design

Session-level medians of epoch-level metrics were computed per subject per task (`subject_task_medians` helper, `ds004511_support.py`). Cross-task contrasts used the Wilcoxon signed-rank test with continuity correction on matched subject pairs (`scipy.stats.wilcoxon`, `zero_method="wilcox"`). Cohen's $d$ was computed as the signed mean paired difference divided by the standard deviation of the paired differences (not the rank-biserial approximation, despite similar magnitude in this dataset). Friedman's test (`scipy.stats.friedmanchisquare`) was used for the three-condition omnibus test on MNPS coordinates. Multiple-comparison correction used Benjamini–Hochberg FDR @benjamini1995 at $alpha = 0.05$, applied within each pre-specified test family (18 tests for the primary MNJ pairwise family: 6 metrics $times$ 3 task pairs; 9 tests for MNPS pairwise; 7 tests for the confound-correlation family in S1.6, after adding corrugator EMG and Sync-pulse event rate; 9 tests for the EAP partial-correlation family in R6; 48 tests for the conventional-EEG baseline family in R5a, 16 features $times$ 3 task pairs).

Spearman correlations (`scipy.stats.spearmanr`) were used throughout for physiological-coupling analyses, computed on session-level medians unless otherwise noted. Partial Spearman correlation (controlling for a third variable) was computed by rank-transforming all three variables, computing the pairwise Pearson correlations on ranks, and applying the standard partial-correlation formula with a Student's $t$ significance test on $n - 3$ degrees of freedom (function `partial_spearman`, `05_mnj_confound_audit.py`).

= S1.6 Robustness and confound audit protocol

Following the science-lead audit requirement (`sciencelead/001.md`, `sciencelead/002.md`), the primary GG vs. CC Frobenius-norm contrast was subjected to a ten-part audit, implemented in `05_mnj_confound_audit.py` (parts A–F), `07_eda_confound_control.py` (part G), `10_corrugator_emg_confound.py` (part H, added in a subsequent revision once the EMG channels were ingested), `09_conventional_eeg_baseline.py` (part I, a baseline comparison rather than a confound test in the strict sense), and `11_event_density_sensitivity.py` (part J, an event/response-rate sensitivity check added once the raw BIDS `events.tsv` timing was joined to the epoch-level Jacobian data):

*(A) Intersection sample.* All primary contrasts were re-computed restricting to the $N = 44$ subjects with valid epoch-level Jacobian data for all three tasks (identified from H5 `jacobian_subject_anchored/centers` availability), removing any imbalance from subjects contributing to only a subset of tasks.

*(B) Epoch-count matching.* For each intersection subject, the minimum epoch count across the three tasks was computed (floor of 10), and epoch-level Jacobian rows were randomly subsampled without replacement (fixed seed, `np.random.default_rng`) to that count before recomputing subject-task medians and contrasts. This controls for the possibility that GG sessions' much larger epoch counts (typically 850–1150 vs. 120–330 for CC/Rest) inflate apparent effect sizes through more stable median estimation.

*(C) Leave-one-subject-out (LOOSO).* For the four primary metrics (Frobenius norm, spectral radius, rotational power, ACI), the GG vs. CC contrast was recomputed 44 times, each time excluding one subject, recording the sign and magnitude of Cohen's $d$ and the $p$-value.

*(D) Bootstrap confidence intervals.* 2000 bootstrap resamples of the 44 paired differences were drawn with replacement (`N_BOOT = 2000` in `05_mnj_confound_audit.py`); Cohen's $d$ was recomputed on each resample to build an empirical 95% CI (2.5th/97.5th percentiles). This is a different, smaller resample count than the 5000-iteration permutation test in (E) below; earlier drafts of the main article and S3/S4 incorrectly stated "5000 resamples" for the bootstrap step by conflating the two counts, and have been corrected to 2000 throughout.

*(E) Within-subject permutation.* The sign of each subject's GG$-$CC difference was randomly flipped (Rademacher $plus.minus 1$) 5000 times, and the median of the permuted differences was compared to the observed median difference to obtain an exact permutation $p$-value.

*(F) Artifact balance.* EEG/EOG quality flags (`qc_ok_eeg`, `qc_ok_eog`), EOG blink rate, EOG artifact fraction, high-frequency EEG power (30–45 Hz, an EMG contamination proxy), Hjorth complexity, and permutation entropy were tabulated by task across the intersection sample to rule out differential artifact contamination as an explanation for the MNJ contrast.

*(G) Physiological confound partial correlations.* For each candidate confound $c$ (heart rate, respiration rate, respiratory anchor index, EOG blink rate, tonic EDA), the subject-level GG$-$CC difference in $c$ was correlated (Spearman) against the subject-level GG$-$CC difference in Frobenius norm. A significant positive association here — confound difference tracking Frobenius difference — would indicate that the primary contrast could be partly explained by that physiological covariate changing differentially between tasks. The EDA arm of this test (part G in `07_eda_confound_control.py`) reused the identical GG$-$CC intersection-sample construction and Spearman methodology, applied to `eda_tonic_scl` medians from the Script 06 output.

*(H) Corrugator-EMG confound.* Identical in structure to part G, but applied to the tonic (subject-median) `emg_rms` column derived from the injected `EMGA`/`EMGB` channels (`10_corrugator_emg_confound.py`). Both the direct GG-vs-CC contrast on `emg_rms` and the confound-difference-vs-Frobenius-difference Spearman correlation were computed.

*(I) Conventional-EEG baseline comparison.* Not a confound test but a scope check: the same paired-Wilcoxon protocol used for the primary MNJ contrasts (part A) was applied to the 16 `eeg_conventional_*` columns on the identical intersection sample, and the resulting GG-vs-CC effect sizes were compared directly against the primary MNJ Frobenius and spectral-radius effect sizes (`09_conventional_eeg_baseline.py`).

*(J) Event/response-rate sensitivity.* Raw BIDS `events.tsv` Sync(1) trigger-pulse onsets (dataset-native, independent of NMD ingest) were joined to the H5-derived epoch windows (`window_start`, 8 s length) by counting onsets falling in each epoch's time window (`np.searchsorted` on sorted onset arrays). Four checks were run: (i) session-level pulse rate (total in-window pulses / session duration) contrasted by task with the standard paired-Wilcoxon protocol; (ii) a confound-partial Spearman correlation between the subject-level GG$-$CC event-rate difference and the GG$-$CC Frobenius difference, identical in structure to parts G/H; (iii) within-task epoch-level Spearman correlation between per-epoch event count and per-epoch Frobenius norm; and (iv) a density-matched sensitivity contrast, in which each subject's epochs were split at their own within-subject-within-task median event count, and the GG-vs-CC Wilcoxon contrast was recomputed on the below-median-density subset only (`11_event_density_sensitivity.py`).

= S1.7 Secondary EAP analysis

Session-level Spearman correlations between `resp_anchor_index` and each MNPS/MNJ session median were computed separately within each task. Where the direct association was strongest (cognitive control, `resp_anchor_index` vs. `m`), a partial Spearman correlation controlling for `ecg_hrv_rmssd_ms` was computed to test whether the respiratory association was reducible to a shared cardiac-autonomic confound. Bootstrap 95% CIs (2000 resamples) and LOOSO sign-consistency (44 iterations, gambling condition) were computed for the exploratory `resp_anchor_index` × `frobenius_norm` association using the same procedures as S1.6(C)–(D).

#bibliography("references.bib")
