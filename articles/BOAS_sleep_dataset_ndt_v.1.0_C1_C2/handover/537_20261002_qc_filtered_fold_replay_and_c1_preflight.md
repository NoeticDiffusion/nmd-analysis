# 537 — 2026-10-02 — QC-filtered fold replay and C1 metadata preflight

## Scope

Completed the QC-filtered five-fold chart replay and the article-local, outcome-blind C1 support preflight. MNDM `summarize` consumed the candidate QC-filtered `features.parquet` and file index; the raw EDFs were neither copied nor read during this replay and remain on K:. The preflight reads H5 identity, time, and QC metadata plus coordinate dataset shapes only. It does not read coordinate arrays, stage values, future chart values, or scores.

## Replay surface

- Replay root: `K:\processed\boas_sleep_c1c2_qc_filtered_fold_chart_replay_20261002_v2`.
- All ten training/apply runs have completed manifests; the processed dataset root contains exactly 500 H5 files totaling 76,532,626,236 bytes.
- H5 counts by fold, training/apply: 0 = 80/20, 1 = 81/19, 2 = 80/20, 3 = 79/21, 4 = 80/20. All counts match the frozen split manifests.
- MNDM revision: `53bae391015a5bad51b8013c312745a8d90e52f5`.
- Candidate feature table: 92,541 rows / 100 recordings; SHA-256 `139a9c5b685d2050107479d12ee8dc0070ae997ca4e1a31ecfb2af30226482c6`.
- The four reviewed `raw_joint_eeg_flatline` overlap epochs are absent from their selected fold charts.
- The chart replay output contains no QC sidecar directory at its processed dataset root; run-level `signal_support_provenance` therefore remains unknown/empty. The external support ledger used for path accounting does not prove those records describe the executed feature producer.

The replay progress record is `K:\processed\boas_sleep_c1c2_qc_filtered_fold_chart_replay_20261002_v2\control\replay_status.json`. It records `outcome_scores_calculated=false` and `effects_calculated=false`.

## C1 metadata preflight

`src/c1_qc_filtered_outcome_blind_preflight.py` produced `results/c1_qc_filtered_outcome_blind_preflight_20261002_v2/` with verdict `PARTIAL_PASS_OUTCOME_BLIND_C1_SUPPORT_PREFLIGHT`.

- All 500 H5s in the replay root belong to the ten selected fold runs; all run manifests and fold assignments validate.
- The 462,705 H5 identity/time/QC rows (five folds × 92,541 candidate rows) bind to the source-support ledger and the frozen fold PID assignment.
- The four registry exclusions have zero matching rows in their selected fold charts.
- After removing those four keys from the source ledger, the full ledger contains 119,666 rows across 128 recordings. Its primary-surface subset contains 92,541 rows across 100 recordings and 78 PIDs, and its keys match the filtered candidate table exactly.
- Path-support counts are recorded by fold, role, dimension (3D/9D), and horizon (h1/h2/h4), using two history rows, 30-second windows, source-support/gap continuity, and chart QC flags. These are support counts only.
- Across the ten repeated fold-role surfaces, the primary 3D/h1 cell has 460,170 outcome-blind eligible paths; every eligible h1/h2/h4 path has the nominal 30/60/120-second horizon, with zero horizon mismatches. Fold-role totals are repeated CV support, not independent observations or scores.
- Validation SHA-256: `AAD7A1EEBCF08C62C8B67E427F40E8FA323D82211B58269C60B30A00CFB88F73`.

The first preflight attempt correctly stopped because the source ledger also includes 28 recordings outside the primary surface. Validation now checks exact row-key parity against the primary-surface subset while retaining the wider source ledger for provenance joins.

## Decision state and limits

C1’s score definition remains locked; this preflight does not amend or calculate it. No contrasts, effects, or outcome values were computed, and the separate protocol/analysis gate remains closed.

The C2 v2 protocol and estimator received a read-only review. The candidate is sufficiently specified as an outcome-blind proposal: 3D `[m,d,e]`, h1, one nearest training transition per PID, `k=32`, leave-one-PID-out support-radius calibration, local future-endpoint covariance log-determinant, and OOF exclusion from both transition and scale rosters. It is not qualified as a prognostically safe BOAS predictor. All ten new run manifests report `signal_support_provenance.status=unknown`, `temporal_support_status=unknown`, and zero support records; the replay root has no per-recording QC sidecars. The external row-support audit does not certify the exact chart producer or establish that query `x_t` excludes filter lookahead.

The C2 estimator also trusts the caller-supplied coordinate scale. Its hash and declared PID roster do not prove that the numeric scale was fitted from the declared fold/OOF rows. Before using H5 coordinate values for C2, bind a fold-local scale artifact to its fitting rows and code, after the producer's causal-support and quality-interval lineage is established. The synthetic target-invariance and failure-path checks listed in the candidate protocol also remain to be run. C2 scoring remains gated.

A fresh raw-EDF producer pilot with a correctly bound per-recording QC/support sidecar is still required before C1/C2 value-level qualification.

Follow-up support-sidecar binding audit and bounded H5 export attempts are recorded in [handover 538](538_20261002_sidecar_export_binding_pilot.md).
