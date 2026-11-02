# 532 — 2026-10-01 — C2 fold-safe spectral input readiness

## Status

**Candidate input identified; qualification is incomplete. Gate 8 remains closed.**
The existing fold-safe chart H5 files contain a raw, per-row feature surface
that can serve as the source for C2's prespecified EEG baseline after temporal,
quality, row-identity, and fold-locality checks pass. The inspected H5
provenance does not pass those checks, so no article-local reader or real-data
feature table was created. No feature-matrix values, chart-coordinate values,
stage/outcome values, or C1/C2 scores/effects were read or computed here.

## H5 feature surface

Metadata-only inspection of one fold-0 training H5 found:

- `/features_raw/values` is `float32[T,K]`, aligned per timepoint, with group
  attribute `export_transform=none`; `/features_raw/names` defines its column
  order. The sample has 18 columns.
- Candidate EEG columns are `eeg_delta`, `eeg_theta`, `eeg_alpha`,
  `eeg_beta`, `eeg_gamma`, `eeg_highfreq_power_30_45`, `eeg_alpha_theta`,
  `eeg_beta_alpha`, `eeg_hjorth_mobility`, `eeg_hjorth_complexity`, and
  `eeg_permutation_entropy`. `eeg_sample_entropy` is an alias of the same
  permutation-entropy calculation; keep one alias if this candidate set is
  adopted.
- `embodied_arousal_proxy`, `ppg_rate_bpm`, and the four
  `actual_source_sample_*` / `actual_source_time_*` columns also occur in the
  sample surface. They are outside the proposed EEG-only baseline. The source
  sample/time columns are provenance fields and must not be predictors.
- `/features_robust_z` and `/features_projection_z` carry transforms and fit
  metadata. Their transform and fit boundaries have not been qualified for
  this C2 surface. Use `/features_raw` as the candidate source; fit any model
  scaling on outer-training PIDs only.

These names identify available fields; they do not lock the final C2 feature
set or authorize scoring.

## Time and producer contract

The source protocol defines the forecast origin as the end of a 30-second
window. The inherited ds005555 config uses `length_s: 30.0` and `step_s: 30.0`.
In the EEG producer, band powers are derived from the current epoch's PSD;
ratios, Hjorth metrics, and permutation entropy are also computed from that
epoch's signal slice. This makes the listed raw features conceptually available
at `t_end` when the exact executed signal path is causal. A causal filter can
add earlier raw-sample contributors before `t_start`; its effective interval
must still end no later than `t_end` and avoid rejected source-quality spans.

The fold-safe config chain intends `temporal_support_mode: causal_finite`, an
identity sample grid at 256 Hz, a 1–45 Hz EEG bandpass, and
`eeg_bandpass_phase: minimum`. MNDM's preprocessor has an explicit minimum-phase
FIR path and records operation support. Config intent alone does not establish
that these operations ran for a particular exported row.

The inspected fold-0 training H5 reports `temporal_support_status=unknown`,
`source_quality_status=not_recorded`, and a reason that effective filter
support is not certified for every epoch. Its execution record is marked
`unknown` with `support_schema_mismatch` / `missing_qc_sidecar`; per-epoch
support is also `unknown`. In the inspected sample, some row metadata carries
nominal or conservative sample bounds, but the export's support status remains
unknown. Handover 531 also records the selected H5 surface's generic
temporal-support status as unknown. A source-audit join used for chart path
support is not, by itself, proof that each exported feature value has a
verified causal contributor interval.

## Promotion requirements

Before `/features_raw` can enter C2's baseline, a fold-specific audit must:

1. Join each H5 raw-feature row to its chart/support row by recording identity
   and exact integer `epoch_id`; verify row count, feature order hash, and exact
   `t_start`/`t_end` alignment. Bind the source file hash and fold role.
2. Verify the actual preprocessing execution record for every included source
   file. Require a finite causal dependency bound ending at or before the
   forecast origin, with a recorded source-quality interval map. Exclude rows
   with unknown, missing, or intersecting support; never fill them.
3. Read only the origin row's selected `/features_raw` EEG columns for both
   train and apply inputs. Do not estimate transforms from apply PIDs or from
   future rows in a recording. Any model scaling is fit on the outer-training
   PID roster, participant-balanced under the frozen protocol.
4. Preserve per-feature missingness and report supported coverage by fold,
   PID, and recording. Select a single permutation-entropy alias and freeze the
   final column list before outcome scoring.

The primary candidate column list is the 11-field EEG set above, with exactly
one entropy alias. It should be adopted only through the separate C2 protocol
review; the present handoff does not lock it.

## Bounded pilot path and blockers

The raw BIDS EDF source remains read-only at
`K:\ExternalReceivedDatasets\openneuro\received\ds005555`; MNDM's
prediction-safe feature config and the existing two-recording replay are
available on K:. Handover 530 reports a bounded technical replay pass with
exact numeric reproduction and no outcomes calculated. This establishes that
a small raw-EDF extraction/replay is technically feasible without copying the
raw catalog or running a cohort extraction. No new EDF processing was run for
this assessment.

The current blocker is the support sidecar contract: the selected H5 export
cannot currently prove row-level causal support or recorded source-quality
support. A bounded follow-up should use one or two recordings in a fresh output
root after the support-sidecar mismatch is resolved, then verify per-epoch
execution records, feature-to-origin alignment, and source hashes. That pilot
would check producer behavior only; it would not qualify the full fold surface
or open a scoring gate.

## Source files inspected

- Fold chart config: `articles/BOAS_sleep_dataset_ndt._v.1.0/results/fold_safe_chart_qualification_20260930_v1/configs/fold_0_training_label_free_v2.yaml`.
- Producer config:
  `H:/SourceRepo2/NeuralManifoldDynamics/mndm/config/sources/openneuro/config_ingest_ds005555_continuous_c123_fold_safe_chart_qualification.yaml`;
  it imports
  `config_ingest_ds005555_continuous_c123_prediction_safe_full_cohort_features_20260929.yaml`.
- Epoch config:
  `H:/SourceRepo2/NeuralManifoldDynamics/mndm/config/sources/openneuro/config_ingest_ds005555_continuous_c123.yaml`.
- Feature computation: `H:/SourceRepo2/NeuralManifoldDynamics/mndm/src/mndm/features/eeg.py` (epoch PSD and feature-row construction).
- Causal filter and support mapping:
  `H:/SourceRepo2/NeuralManifoldDynamics/mndm/src/mndm/preprocess.py` and
  `H:/SourceRepo2/NeuralManifoldDynamics/mndm/src/mndm/signal_support_provenance.py`.
- H5 feature/support export: `H:/SourceRepo2/NeuralManifoldDynamics/mndm/src/mndm/pipeline/summary.py`;
  contract reference: `H:/SourceRepo2/NeuralManifoldDynamics/mndm/Output_variables_guide.md`.
- Forecast-origin definition: `articles/BOAS_sleep_dataset_ndt._v.1.0/preregistration_continuous_C123_20260929.md`.

No producer code, C1 files, or unrelated outputs were changed. The only
protocol change corrects the description of the H5 feature surface and points
to this handoff.
