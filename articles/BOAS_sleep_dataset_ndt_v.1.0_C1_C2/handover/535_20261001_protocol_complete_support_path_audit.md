# 535 — 2026-10-01 — Protocol-complete support-path audit

## Scope

This is the reviewed replacement for the preliminary path summary in handover 534. The audit binds the 100 selected apply-H5 recordings to their source-support rows, fold manifest, raw-EDF QC sidecars, and the previously validated outcome-blind chart identity/time map. It reads row and QC metadata only: no chart-coordinate arrays, feature values, stage/outcome columns, predictions, or scores.

## Protocol checks

The path evaluator now requires every dependency row—both history rows, origin, every intervening row, and target—to have the relevant dimension-specific chart-valid flag. It also requires every dependency row to have finite, strictly ordered conservative raw-sample contributor bounds. Invalid bounds are reported and make the audit incomplete; they cannot be interpreted as non-overlap. Recorded rejected source-quality intervals are checked against each valid dependency bound.

Independent review found and documented two omissions in audit v1: h2/h4 did not check chart validity for all intervening rows, and invalid contributor bounds were silently skipped by the overlap scan. Audit v2 fixes both. It separately reconstructs the earlier preflight counts to show comparability; those matching baseline counts are not used as a substitute for the complete protocol checks.

## Result

Audit v2 completed with `QUALITY_OVERLAPS_PRESENT_REQUIRE_SUPPORT_REVIEW`:

- 100/100 apply recordings passed expected raw-EDF source-path, source-hash, identity/time, interval-map, and row-join checks.
- All 92,545 apply-H5 row instances had finite, ordered contributor bounds. There were no intervening chart-validity exclusions and no invalid-bound rows.
- All 30 fold/dimension/horizon preflight baseline counts were reconstructed exactly.
- Four apply-H5 rows in four recordings intersect recorded raw joint-EEG flatline intervals while remaining primary-eligible: fold 0/PID 52/`sub-85` epoch 478; fold 0/PID 104/`sub-125` epoch 27; fold 1/PID 73/`sub-105` epoch 831; and fold 4/PID 48/`sub-82` epoch 18.
- Each dimension/horizon cell has four protocol-eligible paths that depend on these overlaps. Primary 3D `h1` has 92,038 protocol-eligible paths before the quality exclusions and 92,034 after; 3D `h2` has 91,876 and 91,872; 3D `h4` has 91,555 and 91,551. The 9D support counts are identical.

These are support counts, not scores or evidence of predictive effect. Gate 8 remains closed. Handover 534's v1 h2/h4 path interpretation is superseded by this v2 result.

## Artifacts

- Audit implementation: `src/c1_full_surface_quality_overlap_audit.py`
- Validation: `results/full_surface_quality_overlap_audit_20261001_v2/validation.json`
- Path support by fold/cell: `results/full_surface_quality_overlap_audit_20261001_v2/quality_aware_path_support_summary.csv`
- Exact QC overlaps: `results/full_surface_quality_overlap_audit_20261001_v2/apply_h5_quality_overlap_rows.csv`
- Affected forecast paths: `results/full_surface_quality_overlap_audit_20261001_v2/quality_affected_forecast_paths.csv`
- Invalid bounds ledger (empty): `results/full_surface_quality_overlap_audit_20261001_v2/invalid_h5_contributor_bounds.csv`

The audit and C2 estimator modules pass `py_compile`, and the metadata audit completed successfully. Independent review found no remaining material issue in v2 path eligibility or reported counts. The existing OOF fixture was updated to omit its query PID from the scale roster; no formal tests or outcome analyses were run.

## Producer and C2 follow-up

Metadata-only inspection of the fold-0 apply run manifest found `extra.signal_support_provenance.status=unknown` with an empty `records` list. The chart processed root has no `qc_artifacts` directory; the K-side QC sidecars used for the overlap audit came from a separate feature run. Matching raw-file hashes do not prove those sidecars describe the chart H5's executed preprocessing, so they cannot silently repair the H5 producer contract.

The article-local C2 estimator is now candidate v2 (`c2_local_future_cov_logdet_h1_3d_v2`). Its training-OOF query PID must be absent from both transition and coordinate-scale rosters; its log-determinant is converted back to native chart-coordinate volume units; equal-distance transitions use a stable identity tie-break; and each output records roster counts/digests plus the numeric scale digest. Independent review confirmed the log-determinant conversion and the query-roster guards. The estimator still trusts the caller to fit the numeric scale from the declared roster, so qualification must bind that scale to the actual fitting rows and code. The amended candidate protocol is `protocol/c2_accessibility_candidate_20261001_v2.md`. This remains a static candidate change only: no H5 coordinate values, feature values, scores, or effects were read or computed for C2. Its feature/schema/leakage qualification has not run.

## Remaining work

The apply-H5 producer/support contract is still unqualified: selected H5 metadata reports temporal support as unknown and source quality as not recorded, and the run's support-provenance record is empty. Resolve that contract or create a newly qualified chart surface before using the current H5s for C1 scoring or C2 fitting. C1's locked score definition remains unscored. C2 v2 needs outcome-blind schema, leakage, failure-path, and coverage qualification plus a frozen score contract before effects are examined.
