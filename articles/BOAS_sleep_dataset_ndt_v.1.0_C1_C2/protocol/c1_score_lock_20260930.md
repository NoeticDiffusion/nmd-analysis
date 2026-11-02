# C1 score lock — 2026-09-30

## Decision

**Confirmed: carry forward the C1 score already frozen in BOAS-C123-001 v1.0. This note does not amend that protocol and does not authorize outcome scoring.** In particular, the separate proposal for a distributional forecast score is not adopted here. The locked primary is the participant-balanced, held-out reduction in multi-output conditional-mean MSE for 3D `h1`.

## Locked estimand

- **Question and target:** whether two immediately preceding observed chart rows improve prediction of the future observed chart state beyond the current chart alone. At an eligible origin `t` (the end of a 30-second measurement window), the target is the chart vector `x[t+h]`, not displacement and not a future-state distribution.
- **Primary representation:** canonical 3D chart `[m,d,e]`, in its registered order, at row-lag `h1` (nominally 30 seconds). Report actual origin-to-target elapsed time. Do not pool dimensions. The fixed secondary cells are 3D `h2`/`h4` (nominally 60/120 seconds), plus 9D at `h1`/`h2`/`h4` as a separate sensitivity representation. The 9D results are not independent replications.
- **Models:** fixed multi-output Ridge conditional-mean models, separately fit within each outer fold. `M0: x[t] -> x[t+h]`. `M1: (x[t], x[t-1], x[t-2]) -> x[t+h]`, with input block order current, one-row lag, two-row lag. The history is past-only and contiguous with the origin. Both models use the same eligible origin-target rows.
- **Outer evaluation:** deterministic five-fold `GroupKFold` grouped by biological PID; every PID and its recordings stay wholly in one fold. Both models are fit using outer-training PIDs and evaluated on that fold's held-out PIDs. The five fold results are assembled once into participant-level out-of-fold reductions.
- **Locked score:** at each held-out row and representation, MSE is the mean squared error across chart coordinates. Average row losses within recording, recordings equally within PID, then average the PID-level reductions equally across PIDs. For each PID, reduction is `MSE(M0) - MSE(M1)`; the reported cohort score is the mean of those held-out PID reductions. A positive value means this fixed history-augmented Ridge model had lower held-out conditional-mean MSE. The score is in outer-training-IQR-scaled chart-coordinate units.

## Registered preprocessing and scaling

The frozen source protocol specifies the unchanged MNDM chart definition and producer settings below. They are upstream contract requirements for any chart surface used to claim this estimand; this lock does not assert that the selected H5 files have already been verified against them. These feature-level steps define the chart inputs and are distinct from the later fold-local C1 coordinate transform.

- The primary chart is 3D `[m,d,e]` from the inherited fixed `mnps_projection.v1_mapping`; 9D uses `mnps_9d.definition_version=2.0`. Default feature standardization is `[robust_z, clip]`. `eeg_delta`, `eeg_theta`, `eeg_alpha`, `eeg_beta`, and `eeg_gamma` use `[log10, robust_z, clip]`. `eeg_alpha_theta`, `eeg_beta_alpha`, `eeg_sample_entropy`, `eeg_permutation_entropy`, `eeg_spectral_entropy`, `eeg_hjorth_complexity`, and `eeg_hjorth_mobility` use `[robust_z, clip]`; all other mapped features use the declared default.
- The MNDM external feature anchor is fit on training PIDs only, with `scale_method=iqr`, `min_subjects=20`, `subject_anchored=false`, and `cohort_anchored=true`. No ComBat or other whole-recording/cohort transform is allowed. Bind each fold's resolved config, MNDM code, and anchor artifact by hash. If required anchors do not qualify, that fold is unavailable; do not refit on apply PIDs.
- In the primary population, each included recording must have `support_signature/v1/coordinates/e_m/source=fallback` and `fallback_feature=ppg_rate_bpm`. Exclude the EOG-blink-rate and EEG-high-frequency fallback strata from the pooled primary; report their availability separately. Apply identical recording/PID eligibility to 9D.
- The registered `ppg_rate_bpm` input is produced by `window_local_present_only_v1`: select exactly one source channel matching `ppg|pleth|pulse|photopleth`, record its channel name and post-typing MNE type, do not filter the current 30-second raw pulse window, subtract that window's median, detect peaks on the absolute centered signal with minimum distance 0.35 s and prominence `max(1e-6, 0.75 * (median(abs(centered_window)) + 1e-8))`, and calculate `60 / mean(interpeak_interval_seconds)` within that window. Mark it QC-valid only for a finite rate with at least two peaks; otherwise preserve missingness and provenance. The legacy stream-wide zero-phase filter/global threshold is prohibited.
- For the C1 estimator, fit one coordinate-wise transform per outer fold and representation using training data only. First take coordinate-wise medians across eligible chart rows within each training PID-recording, then coordinate-wise medians across recordings within PID. Define each coordinate's center as the median and scale as the IQR over those finite PID summaries. A zero or non-finite IQR makes that coordinate/fold unavailable. Apply the same `(x-center)/IQR` transform to every current/history predictor block and every future target coordinate; do not refit per model, lag block, or matrix column. Fit `Ridge(alpha=1.0, fit_intercept=true)` after this transform. Alpha, features, and model selection are not tuned against held-out data.

## Eligibility and exclusions

A candidate path is eligible only if the origin, all required history and intervening rows, and target are present, finite, coordinate-QC valid, and source-support eligible within the same PID, recording, and verified contiguous segment. The shared estimator consumes already-qualified chart surfaces; the caller must establish the registered support contract and pass its row-level eligibility instead of treating the estimator as a source-support validator. Epoch identities must be consecutive across the dependency path and timestamps strictly increase; retain and report actual horizon seconds. The source protocol additionally requires finite causal conservative raw-sample support and no rejected source-quality interval crossing any dependency bounds, including affected neighboring rows. Do not interpolate, bridge gaps, or replace unsupported/missing values with zero. Keep unavailable rows and their reasons. Exclude an origin if either model's required input or the target is unavailable; the model comparison uses their common eligible rows. Where a within-segment shifted-history diagnostic is reported, its shift is fixed before scoring at five or more rows; it is diagnostic only, not a score-selection or pass/fail rule.

A reporting cell with fewer than 20 independent scored PIDs is `INCONCLUSIVE`; 20 is a reporting/feasibility floor, not a power guarantee. Failed fold anchors or zero/non-finite coordinate scales make the affected fold/cell unavailable, not zero.

## Uncertainty and claim ceiling

The protocol specifies a descriptive participant-cluster percentile 95% interval from 10,000 resamples of the PID-level reductions, seed `20260929`. There is no registered epoch-level inferential sample size, confirmatory p-value, success threshold, or equivalence claim. The estimator's `DESCRIPTIVE_SCORE_AVAILABLE` status means only that a score can be summarized; it is not a scientific pass or evidence of prediction beyond this defined chart, history, model class, and horizons. The result cannot establish or refute a distributional, existential, or unmeasured-state C1 claim.

## Current gate status and compatibility limit

This score lock is a protocol decision only. No chart-coordinate values, future targets, predictions, scores, stage labels, or effects were read or calculated for this confirmation. The 2026-09-30 outcome-blind preflight established row identity/support-path linkage only. Its handover reports the H5 generic temporal-support status as `unknown` and H5 source-quality status as `not_recorded`; it checked coordinate dataset shapes but did not index coordinate values. The shared estimator documentation likewise states that it does not load data, create MNPS coordinates, or qualify source support; callers must establish those properties. Therefore the preflight does **not** establish that the existing H5 files' resolved producer config, MNDM code, feature-anchor hashes, modality provenance, or raw-support contracts satisfy every registered preprocessing/source requirement above, nor that nominal 30/60/120-second intervals hold for every eligible path.

Gate 8 remains **NOT OPEN**. Before outcome scoring, the article must complete the separate hash-bound input/config/code/anchor freeze, verify the H5 inputs against registered producer and source-support requirements (or resolve the gaps with a dated protocol amendment), complete independent review, and receive separate scoring authorization. The support counts from handover 531 are not outcome evidence. C2 is outside this lock and remains unqualified under handover 530/531.

## Source basis and validation

This is a textual cross-check; no tests or scoring runs were performed.

- Source registration: `articles/BOAS_sleep_dataset_ndt._v.1.0/preregistration_continuous_C123_20260929.md`, especially §§1–3 (folding/support and preprocessing at lines 16–22; C1 at lines 24–33; v1.0 status at line 4).
- Article readiness: `articles/BOAS_sleep_dataset_ndt_v.1.0_C1_C2/handover/530_20260930_c1_c2_data_and_gate_readiness.md`, especially lines 5, 11, 18–25, 28–33.
- Outcome-blind support preflight: `articles/BOAS_sleep_dataset_ndt_v.1.0_C1_C2/handover/531_20260930_c1_outcome_blind_chart_preflight.md`, especially lines 5–7, 11–25, 46–50.
- Shared implementation: `nmd-analysis/nmd_analysis/continuous_c123_estimators.py`; constants and IQR fit at lines 22–26 and 109–162; fold construction/eligibility at lines 348–454; PID-weighted loss and bootstrap at lines 457–481; Ridge fitting and row MSE at lines 523–619; complete-fold OOF aggregation and descriptive interval at lines 622–702.

Commands inspected in `J:\repos\nmd-analysis`:

- `git status --short` (to preserve pre-existing worktree changes).
- `rg --files articles/BOAS_sleep_dataset_ndt_v.1.0_C1_C2` and targeted `rg --files` to identify the article files and source preregistration.
- Targeted `rg -n` searches for C1, preprocessing, score, scaling, support, gates, and estimator functions across the source preregistration, handovers 530/531, and `continuous_c123_estimators.py`.
- PowerShell `Get-Content -LiteralPath ...` with line-numbered ranges for the source protocol §§1–3, handovers 530/531, and estimator lines 1–165, 348–481, 523–702.
- `Test-Path` confirmed that this new `protocol/` file and its containing directory did not already exist before creation.

Cross-check outcome: the source registration, both handovers, and the shared implementation agree on the primary 3D `h1` fixed Ridge/MSE-reduction estimand and its participant-balanced aggregation. The note carries that definition forward without changing it. Data-contract qualification and scoring authorization remain separate, unresolved gates.

