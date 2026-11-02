# 534 — 2026-10-01 — Two-recording raw-EDF support pilot

## Scope and status

A bounded technical replay read two raw EDF recordings directly from `K:\ExternalReceivedDatasets\openneuro\received\ds005555`; no raw-data copy was made. Feature outputs were written to the article-local `results/producer_support_pilot_20261001/` root. The replay did not calculate C1 or C2 targets, predictions, scores, or effects.

The feature commands were invoked from the managed checkout at revision `53bae391015a5bad51b8013c312745a8d90e52f5`, based on `2b61d3eca37dfca4892dee488ad211e3f7ae037d`. Exact code/config SHA-256 values, sidecar hashes, source-file hashes, and metadata checks are recorded in `results/producer_support_pilot_20261001/validation.json`. The validator records checkout revision and cleanliness after extraction; the feature sidecars do not independently capture those values at execution time. The article-local audit implementation is `src/c1_c2_support_pilot_audit.py`.

**Result: incomplete for this two-recording support pilot.** Raw source hashes were stable and matched the source-support audit and apply-H5 manifest. Pilot row support bounds matched the source-support audit; matched H5 row identity, window bounds, and midpoint times agreed. H5 apply rows exactly matched the support audit's primary-surface-eligible row set, but the check found a quality-support conflict described below.

## Results

- `sub-100`: all 996 pilot rows were source-support eligible and matched the 996 apply-H5 rows. No selected source-quality intervals or sample gaps were observed.
- `sub-105`: the pilot emitted 964 feature rows; 962 rows were primary-surface eligible and matched the 962 apply-H5 rows. Rows 722 and 845 intersected configured `stage_hum` code-8 intervals and were ineligible and absent from apply H5. Raw flatline intervals also crossed contributor bounds for rows 722 and 831; row 831 remained primary-eligible and present in apply H5. No input sample gaps were observed.
- **Unresolved quality conflict:** the validated QC sidecar contains 8 `stage_hum` intervals and 7 raw joint-EEG flatline intervals; all 15 have finite, ordered bounds and match the configured selected-interval count. Flatline interval `[24922.0, 24927.7109375]` intersects `sub-105` epoch 831's actual causal contributor interval `[24926.703125, 24960.0]`. The source-support audit nevertheless marks epoch 831 eligible, and apply H5 contains it. This means the existing primary eligibility/H5 surface does not account for at least this raw-flatline overlap under the pilot's quality policy. It must be reconciled before the surface can pass the source-quality support contract.
- The imported config chain was parsed and hash-bound: it maps `PSG_disconnection` to code 8 and sets `read_sleep_stage_annotations: false` for feature export. Neither pilot feature table has stage-named columns. The audit did not read event TSV values, chart coordinates, future chart values, or scores; it did inspect the recorded quality-interval metadata, including the code-8 intervals.
- The sidecars report a verified continuous EDF grid and finite causal support. EEG used an 845-tap minimum-phase FIR; the filter and identity-grid coefficient hashes are recorded in the JSON validation report. This establishes the declared support path for these two recordings only.

## Expanded apply-surface QC metadata scan

The follow-up scan reused the previously validated outcome-blind apply-H5 identity/time map and read the 100 matching QC sidecars under `K:\processed\ds005555_continuous_c123_prediction_safe_full_cohort_features_20260929\ds005555\qc_artifacts`. It did not open H5 coordinate arrays or feature matrices. All 100 source hashes matched between sidecar, source-support audit, and fold manifest; all 100 QC sidecar EDF paths matched the expected raw EDF paths on `K:`; every recorded interval's clock was explicitly `original_raw_seconds`, and its raw-file provenance matched that EDF. All 92,545 apply-H5 row identities/windows joined to source support; all recorded source-quality and flatline interval collections were well-formed, and their counts matched the selected-interval counts.

The scan found **four apply-H5 rows in four recordings** whose conservative causal contributor bounds intersect a recorded `raw_joint_eeg_flatline` interval while the source-support audit still marks the row primary-eligible and the validated apply chart map contains it:

- fold 0, PID 52, `sub-85`, epoch 478;
- fold 0, PID 104, `sub-125`, epoch 27;
- fold 1, PID 73, `sub-105`, epoch 831;
- fold 4, PID 48, `sub-82`, epoch 18.

The overlap ledger records exact contributor-time bounds and row identities. This is an outcome-blind eligibility conflict, not evidence about a condition or effect. The full scan verdict is `QUALITY_OVERLAPS_PRESENT_REQUIRE_SUPPORT_REVIEW`; Gate 8 remains closed.

The initial v1 path reconstruction exactly reproduced the prior C1 preflight baseline. Independent review then found that its h2/h4 path rule did not check chart validity on every intervening row, and its interval scan silently ignored invalid contributor bounds. Treat those v1 path counts as preliminary; the protocol-complete replacement and results are in handover 535 and `results/full_surface_quality_overlap_audit_20261001_v2/`.

The QC sidecars have matching raw-source hashes, but they are external to the chart H5 run and do not prove that the H5 producer embedded or applied the same quality map. The overlap therefore requires conservative support review; it is not a measurement of numerical contamination or a biological result.

Audit implementation: `src/c1_full_surface_quality_overlap_audit.py`. Outputs: `results/full_surface_quality_overlap_audit_20261001_v1/validation.json`, `recording_quality_support_summary.csv`, `apply_h5_quality_overlap_rows.csv`, `quality_aware_path_support_summary.csv`, and `quality_affected_forecast_paths.csv`.

## Limits

This is a two-recording engineering pilot, not full-surface qualification. The audit compared identity, time, support, QC, and source-hash metadata. It did not compare feature values or chart-coordinate values, hash all 500 H5 files, independently certify the producer implementation, or establish C1/C2 scientific validity. Generated feature values remain uninspected. The raw-flatline mismatch is negative evidence; this pilot does not pass the C1/C2 support gate and does not permit outcome scoring.

The article's protocol/analysis gate remains closed. The C1 score and the prognostic safety/qualification of the C2 candidate still need their separate decisions before any effect analysis.

## Status update

The full selected-H5 row-key/time/source-support join remains documented in handover 531: 500 H5 files and 462,725 chart-row instances were bound to source support and fold manifests. The later 100-recording audit checks the apply surface against the full recorded QC interval map, reconstructs every dependency row under the frozen C1 path rule, validates contributor-bound finiteness/order, and is documented in handover 535. No C1 score or C2 effect was calculated.
