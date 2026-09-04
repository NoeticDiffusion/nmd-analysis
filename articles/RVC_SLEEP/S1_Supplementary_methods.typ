// S1 Supplementary Methods — RVC_SLEEP
// Companion to manuscript.typ.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "S1 Methods - RVC_SLEEP",
  subtitle: "Measurement contract, primary metric computation, auxiliary extraction, and the robustness/confound audit protocol",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S1.0 Dataset and measurement contract

Three independent overnight PSG datasets were used, all observational (no experimental manipulation):

- *ANPHY-Sleep* (@wei2024_anphy_sleep, @anphy_sleep_osf) - 27 healthy adults, high-density scalp EEG (Biosemi, 93 channels). NMD run roots: `neuralmanifolddynamics_ANPHY_20260702_082429` (primary) / `..._084940` (anchor-augmented). Config digests (`run_manifest.json -> config.digest_sha256`, first 16 chars): `b6d72c504414c540` (primary), `e52ce463339d642b` (anchor-aug).
- *BOAS / ds005555* (@ds005555_1_1_1) - 128 subjects, PSG, OpenNeuro. Run roots: `neuralmanifolddynamics_ds005555_20260702_080821` (primary) / `..._084946` (anchor-augmented). Config digests: `19e24fb3acea8f8e` (primary), `1374fa95bc12d6d1` (anchor-aug).
- *RichSleep* (@richsleep2026) - 24 subjects, whole-night PSG: six EEG channels (F3-A2, F4-A1, C3-A2, C4-A1, O1-A2, O2-A1), two EOG channels (EOG-L, EOG-R), chin EMG, ECG, respiratory, snoring, leg-movement, blood-oxygen and carbon-dioxide, chest/abdominal movement, and breath-interval-duration channels; 200 Hz sampling; impedance kept below 10 $Omega$ throughout acquisition; hypnogram labels W/N1/N2/N3/R (30 s epochs). Run root: `neuralmanifolddynamics_RichSleep_20260709_100219` (primary-only; no anchor-augmented counterpart was ingested for this dataset). Config digest: `0c8d751c52029306`. Added as an out-of-sample verification dataset; the ingest underwent standard QA before use, which identified and corrected a subject-scoping bug in event-locked source resolution and, separately, a sign bug in the `resp_anchor_index` sensitivity anchor (S1.7).

All analyses were run against the NMD (NeuralManifoldDynamics) `summarize` pipeline output, not against raw EDF/BIDS tables directly; every claim in this article should be read against the measurement contract below, not as a direct computation on raw signals. RichSleep's event-locked schema uses a numeric `stage` codebook (Wake=0, N1=1, N2=2, N3=3, REM=4; $-1$=unscored) instead of the `n2`/`n3`/`rem`/`wake` indicator columns present in the ANPHY/BOAS export; an `n2` indicator is derived from `stage == 2` before applying the shared Pass A filter (`rvc_sleep_support.py::ensure_n2_column`).

= S1.1 Epoch structure and feature export

Each subject's continuous recording is epoched into 30 s windows and exported per-window with: the 3D primary MNPS coordinates (`mnps_3d`) and their first derivative; the 9D stratified coordinates (`coords_9d`) and derivative; the local Jacobian tensor (`jacobian`, `jacobian_9D`) and its derivative; the `anchor_state` composite indices and `anchor_quality` flags (0/1 per-channel usability); raw (`features_raw`) and robust-$z$ (`features_robust_z`) per-epoch feature matrices; and the AASM sleep-stage label. Spindle events (detected by YASA, @vallat2021yasa, on C3-A2 at 200 Hz, sigma 12-15 Hz, N2-only *hypnogram epochs*, no resampling) are then aligned against this window grid into an *event-locked* export: one row per (subject, window, condition, bin_label), with `condition in {spindle_event, matched_control}` and, for spindle events, `bin_label in {pre_far, pre_near, event, post_near, post_far}` (single `bin_label = control` for matched controls). Matched controls are drawn from the same subject's N2 windows outside a 30 s exclusion margin of any spindle/K-complex/arousal. Those matched epochs are expanded onto the 30 s MNPS grid, so control *row* counts (ANPHY 34,263; BOAS 192,312) are much larger than unique spindles. Analysis median-collapses the control pool per `matched_event_id` before computing deltas (`rvc_sleep_support.py::aggregate_controls_per_event`); the estimand is one control median per spindle, not one independent row per control window. "N2-only" on the detector is the hypnogram-epoch restriction. Event-locked windows carry the stage of the *window centre*; a 0.5–2 s spindle near a stage boundary can sit in a 30 s window whose centre is not N2. ANPHY/BOAS retained rows are already ~100% N2 (`frac_n2` $0.9995$ / $0.9999$). RichSleep's numeric `stage` codebook labels the MNPS window; Pass A then keeps `stage==2`, which is why A2r/R6b collapse to 160/190 event-bin rows of 2,253 (manuscript R6b).

= S1.2 Primary metric definitions

The canonical 3D MNPS chart is $x_t = [m_t, d_t, e_t]^T$, recomposed from the 9D stratified chart $x_t^((9)) = [m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m]^T$ via a release-fixed projection $x_t = P_"fixed" x_t^((9))$. The *tested* family in this article is the frozen 9-name set `GEOMETRY_COLS` $= [m, d, e, d_n, d_l, d_s, e_e, e_s, e_m]$. Chart coordinates $m_a, m_e, m_o$ are exported and were *not* tested. The active 9D-to-3D recomposition used across all three datasets (identical `mnps_projection.v1_mapping` in every run config; columns L2-normalized at runtime with coverage-aware renormalization):

$ m = 0.62 dot m_a + 0.55 dot m_e + 0.45 dot m_o $
$ d = 0.50 dot d_n + 0.82 dot d_l + 0.28 dot d_s $
$ e = 0.85 dot e_e + 0.62 dot e_s + 0.03 dot e_m $ <eq:chart-map>

Interpretive MNPS labels (not the ingest computation): $d_n$ as network-integration deviation, $d_l$ as local segregation load, $d_s$ as representational-geometry deviation, $e_e$ as an entropy family, $e_s$ as an entropy-shape / complexity family, $e_m$ as a mixed EEG-shape slot. Those labels are *plausible interpretations*. The computation is the NMD feature map in the frozen run configs (`config.digest_sha256` prefixes in S1.0).

Operational EEG feature composition for this article's `rvc_v1_eeg_only_e_m` contract, after per-feature `robust_z` + clip (with `log10` pre-transform for band-power features):

- Primary-surface $e_m$ (all three datasets, identical): $0.6 dot "eeg_hjorth_mobility" + 0.4 dot "eeg_beta_alpha"$.
- ANPHY anchor-augmented $e_m$: $0.8 dot "ecg_hrv_rmssd_ms" + 0.2 dot "eeg_hjorth_mobility"$.
- BOAS anchor-augmented $e_m$: $0.7 dot "resp_regular_index" + 0.3 dot "eeg_beta_alpha"$.
- $e_s$ (all datasets, this contract): $0.5 dot "eeg_alpha_theta" + 0.5 dot "eeg_gamma"$. This is the sole $e_s$ definition used here; it is *not* permutation entropy.

The remaining tested stratified coordinates ($d_n$, $d_l$, $d_s$, $e_e$) follow the frozen NMD `mnps_9d.subcoords` map in each hashed run config, not a schematic heat-kernel formula. A reviewer can reimplement them from that config plus the NMD measurement-contract paper; they cannot be reimplemented from an interpretive Laplacian cartoon. Default NMD EEG reference mappings (not necessarily this contract) include $d_n <- "eeg_gamma"$, $d_l <- "eeg_hjorth_mobility"$, $d_s <- "eeg_alpha_theta"$, $e_e <- "eeg_permutation_entropy"$ (@langell2025ndt; NMD contract table). Confirm against the hashed run YAML before treating those defaults as this article's ingest.

= S1.3 Auxiliary feature extraction

Sleep spindles were detected using YASA v0.7 (@vallat2021yasa) as a standalone step prior to NMD ingestion (`project/scripts/16_yasa_spindle_detection.py`), producing per-subject CSVs with `onset_sec`, `duration_sec`, `peak_sec`, and `frequency_hz` per detected spindle (channel C3-A2, sigma band 12-15 Hz, N2-only). RichSleep's numeric sleep-stage annotations were converted from the dataset's native `<sub>_stages.txt` format (label + onset + duration, 30 s epochs) via `project/scripts/17_richsleep_ann_to_stages.py`, using the stage map Wake=0/N1=1/N2=2/N3=3/REM=4. `event_confidence` (a per-spindle detector confidence score) and `sigma_power` (spindle-band power) are *not* exported by this YASA version's CSV output and are not present anywhere downstream; `event_duration_sec` and `frequency_hz` are used as detector-strength proxy covariates instead (S1.6).

= S1.4 Physiological confound and secondary feature definitions (dual-surface contract)

Two surfaces are exported per dataset (ANPHY, BOAS only; RichSleep has a primary surface only):

- *Primary (`primary_eeg_only`)* - used for the primary specificity/timing claims (R2-R4, R6) and for the EAP-moderation test itself (R5-R6). `coords_9d` contains no cardiac, respiratory, or other body-derived features; body signals appear only in the `anchor_state`/`anchor_quality` sidecar group and in event-locked row columns, never inside the primary geometry.
- *Anchor-augmented (`anchor_aug`, ANPHY/BOAS only)* - used only for the Pass B surface-sensitivity check (R5), never for the primary claim; `e_m`'s EEG term is partially or fully replaced by the dataset's primary body anchor (weights in S1.2).

Per-dataset anchor (EAP) feature groups, all aligned to the canonical MNPS window grid:

- *ANPHY*: `ecg_hrv_rmssd_ms` (primary Pass C anchor, 0% NaN, 27/27 subjects), `ecg_hrv_sdnn_ms`, `ecg_hrv_pnn50`.
- *BOAS*: `resp_regular_index` (primary Pass C anchor; NaN in ~66/128 subjects with no respiratory channel), `resp_depth_index`, `resp_rate_bpm`, `anchor_index_v02` (composite sensitivity anchor, ~0.99% NaN, ~127/128 subjects).
- *RichSleep*: `cardioresp_anchor_index` (primary anchor for R6 - a dual-arm composite built from simultaneous ECG + respiratory channels, 0% NaN, 24/24 subjects), plus sensitivity anchors `anchor_index`, `anchor_index_v02`, `sympathetic_index`, `vagal_index`, `resp_anchor_index`, `ocular_stability_index` (all 0% NaN). RichSleep's `anchor_contract` is `rvc_v1_anchor_v02_dual_arm_cardioresp`; unlike ANPHY/BOAS, its underlying per-epoch features (`features_raw`) additionally include EOG-derived blink/saccade metrics, chin-EMG RMS, and explicit cardiorespiratory-coupling features (`cardioresp_rsa_amplitude`, `cardioresp_coherence`, `cardioresp_rpeak_resp_plv`, `cardioresp_coupling_index`) that are not exposed in the event-locked schema and were not used as Pass-C-style anchors in this article (left as a follow-up, S3.4).

= S1.5 Statistical design

The biological unit of analysis is the *subject*. For each (endpoint, dataset) cell of the frozen 9-endpoint family ($m, d, e, d_n, d_l, d_s, e_e, e_s, e_m$):

1. Compute an event-level delta: `event_control_delta = event_bin_value - median(matched_control_values for that event)` (A1r) or `event_prefar_delta = event_bin_value - mean(the same event's own pre_far bin values)` (A2r).
2. Collapse to one subject-mean delta (`groupby(subject_id).mean()`).
3. *Primary $p$-value*: subject-level sign-flip permutation test on the grand mean of subject-mean deltas ($n=2000$ permutations, seed 42).
4. *Sensitivity*: one-sample $t$-test and Wilcoxon signed-rank on the same subject means (reported, not primary).
5. Mean subject delta $plus.minus$ analytic $t$-based 95% CI.
6. Benjamini-Hochberg FDR (@benjamini1995fdr) applied fresh within each frozen test family: 18 tests (9 endpoints $times$ 2 datasets) for A1r/A2r on ANPHY+BOAS; 9 tests for each RichSleep A1r and A2r family (R6); 54 tests (2 delta modes $times$ 3 anchor models spanning both datasets $times$ 9 endpoints: ANPHY primary + BOAS primary + BOAS `anchor_index_v02`) for Pass C; 126 fitted rows (7 anchors $times$ 9 endpoints $times$ 2 delta modes) for the RichSleep EAP family, of which the primary `cardioresp_anchor_index` 18 tests are the confirmatory tonic-anchor family. $alpha = 0.05$ throughout. RichSleep A1r, as coded in `09_richsleep_verification.py`, does *not* restrict to `bin_label=="event"` (mixed-bin peri-spindle windows); ANPHY/BOAS A1r does. Do not treat those as the same sample definition.

= S1.6 Robustness and confound audit protocol

1. *Subject-weighted vs. event-weighted estimand.* A1-original (event-weighted, cluster-robust-SE OLS intercept) is retained as a pre-amendment sensitivity table; A1r/A2r (subject-weighted, sign-flip permutation) is the corrected primary, adopted because BOAS's uneven per-subject event counts (median 5, range 1-18) let high-event-count subjects dominate an event-weighted estimate.
2. *A1/A2 decomposition* (R4) - `event - control = (event - pre_far) + (pre_far - control)`, testing whether an event-vs-control effect is a timing effect, a baseline-separation effect, or both.
3. *Surface sensitivity (Pass B, R5)* - identical subject-weighted estimand computed on both the primary and anchor-augmented surface, reporting `surface_delta`, correlation, sign-agreement fraction, and any FDR-status flips (ANPHY/BOAS only).
4. *EAP moderation (Pass C/R5-R6)* - `delta ~ anchor_pre_far + <mean-centered nuisance covariates>` (covariates: `event_duration_sec`, `window_center_sec` as a time-of-night proxy, `ocular_stability_index`, `sympathetic_index`, `vagal_index`, `eog_quality_quality`, `ecg_quality_quality`, `resp_quality_quality` [RichSleep only], `cardioresp_quality_quality` [RichSleep only], `anchor_support_fraction_quality`; `frequency_hz` is requested defensively but is not present in the current NMD event-locked schema and is always dropped), weighted by $1 \/ n_"events, subject"$, cluster-robust SE by subject; companion per-subject-slope sign-flip permutation test, immune to event-count imbalance by construction. `available_covariates()` additionally requires $>=50%$ non-NaN coverage per covariate before inclusion, to avoid a covariate's missingness silently zeroing out the usable sample.
5. *Cross-dataset replication (RichSleep, R6)* - the identical A1r/A2r/Pass-C machinery re-run on RichSleep, with `stage`-derived `n2` filtering (S1.0) and explicit sign-agreement reporting against the frozen ANPHY/BOAS A1r/A2r tables.

= S1.7 Secondary analysis

The RichSleep EAP-moderation test (R6, exploratory, not specified ahead of RichSleep's ingestion) additionally reports six sensitivity anchors beyond the primary dual-arm composite `cardioresp_anchor_index`: `anchor_index`, `anchor_index_v02`, `sympathetic_index`, `vagal_index`, `resp_anchor_index`, `ocular_stability_index`. These are reported to check whether the mechanistically-motivated primary anchor's null result generalizes to other available composite indices, not as an independent hypothesis family; several show numerically negligible coefficients ($approx 10^(-8)$-$10^(-9)$ per raw unit) despite nominal FDR significance and are flagged as likely scale/multicollinearity artifacts (S2.5, S3.4b). `resp_anchor_index` originally did not fit that pattern (non-negligible, FDR-surviving `event_control`-mode coefficients); a dedicated follow-up (`11_richsleep_resp_anchor_followup.py`, S2.5a, S3.4f) ruled out scale, multicollinearity, and single-subject-outlier explanations, but tracing its exact construction surfaced a genuine upstream sign bug in its rate/slowing component. This was corrected and a re-export delivered; re-verified against it, the original finding is now a clean null (fully resolved), and a new, weaker, unreplicated `event_prefar`-mode pattern emerged in its place (S2.5, S2.5a, manuscript R6).

= S1.8 RichSleep phase-resolved EAP mechanism test protocol (Aim B/C, manuscript R6b)

Exploratory follow-up, run only after independently re-verifying (24/24 subjects, exact onset match) that the phase-resolved RichSleep export (`event_phase_v2`) joins correctly against the corrected event-locked catalog (`neuralmanifolddynamics_RichSleep_20260709_100219`, S1.0 - geometry unaffected by the `resp_anchor_index` sign fix, so Aim B/C results below are unchanged). Two tests, both restricted to the same N2-*window*, geometry-valid spindle population (`pass_a_filter`, S1.6). The 190/2,253 event-bin split is a stage-window mismatch: YASA used N2 hypnogram epochs; the event-locked `stage` label is the 30 s MNPS window centre (S1.1).

- *Aim B (spindle-onset phase-locking).* Rayleigh test (Zar 1999 large-sample approximation) for non-uniformity of `phi_cardiac_onset` and `phi_resp_onset` (event_phase_v2's phase conventions: cardiac phase 0 at the nearest R-peak; respiratory phase 0 at full inhale via a Hilbert-transform convention, S1.0/`run_meta.json`), run per subject (within-subject entrainment) and again on the 24 subject-level mean-direction angles (second-order, population-level common preferred phase). No permutation-based null was used; the Rayleigh approximation is treated as approximate/descriptive given the modest per-subject $N$ (median $approx 8$ events/subject after the N2 + geometry-valid filter). Subjects with $n=1$–$2$ events are not Rayleigh-testable; "0/24 FDR-significant" includes those untestable cells.
- *Aim C (HEP-amplitude moderation).* Identical WLS-cluster (weights $=1"/"n_"events,subject"$, cluster-robust SE by subject) + centered-nuisance-covariate + subject-level-slope sign-flip permutation machinery as R6/Pass C (S1.5/S1.6), with `hep_amplitude_pre_far` as the sole anchor, both delta modes (`event_control`, `event_prefar`), all 9 geometry endpoints (18 tests, BH-FDR corrected per delta-mode family of 9).

Aim A (phase-resolved manifold variance, i.e. testing whether the *magnitude* of spindle-locked geometry change itself varies with phase at sub-epoch resolution) is infeasible on this export: `coords_9d` resolution is 1 value / 30 s feature epoch (`epoching.step_s == epoching.length_s == 30 s`), so no phase-resolved variance signal exists to test (confirmed in `phase_resolved_v1/run_meta.json`). Aim D (an ANPHY/BOAS partial replication of Aim B/C) was not attempted - no phase-resolved export exists for those two datasets.

#bibliography("references.bib", style: "apa")
