# 539 — 2026-10-03 — Apply H5 support-binding pilot

## Scope

Completed the next bounded producer step from handover 538. MNDM `summarize` wrote one fold-1 apply H5 for `sub-105` / PID 73 from the staged 128-row surface. The audit read support, QC, row identity, and time metadata plus H5 dataset shapes. It did not read chart coordinate arrays or calculate scores/effects. Raw EDFs were not copied or parsed by chart export; MNDM verified their source hashes by reading bytes from K:.

## Runtime and staging findings

- The first verbose run spent about 10.5 minutes before its first log line. `faulthandler` traced the stall to Numba's cache-path write check during MNE import (`ensure_cache_path` → `tempfile._mkstemp_inner`). Setting `NUMBA_CACHE_DIR` to an article-local writable directory made the same MNE logging initialization finish in about 1.4 seconds.
- The first cache-fixed attempt refused the staged epoch 0 because MNDM's fold selector uses a falsey fallback that turns numeric zero into an empty epoch key. The staging script now writes `epoch_id` as the canonical support-ledger string, preserving epoch 0 as `"0"`.
- The `--resume-run` folder must exist before summarize starts; the successful run used a newly created empty folder.

These are environment and row-identity plumbing changes only. MNDM source code and measurement definitions were not changed.

## H5 support result

The successful H5 is `results/producer_support_sidecar_export_pilot_20261003_v2/processed/ds005555/fold_1_apply_support_cachefix/sub-105_Sleep_acq-psg/sub-105_Sleep_acq-psg.h5` (151,397,938 bytes). The H5 contains 128 rows with `/coords_3d_cohort_anchored/values` shape `[128,3]`, `/coords_9d_cohort_anchored/values` shape `[128,9]`, and 128-element time/window/epoch vectors. Shapes only were inspected.

The sidecar-to-H5 audit is `results/producer_support_sidecar_export_pilot_20261003_v2/control/sidecar_export_binding_audit.json`:

- All 128 support extents are `finite_causal_conservative_bound` and nominally mapped.
- H5 epoch IDs and nominal clocks exactly match the staged apply rows; source sample bounds pass the half-open-bound check.
- The sidecar source hash matches the frozen fold manifest and the H5 execution record validates.
- Eight source-quality intervals and seven raw joint-EEG flatline intervals are retained; none overlaps the 128 selected rows.
- H5-scoped support provenance is `finite_causal_conservative_bound`. The separate run-level collector still says `unknown`; keep these scopes distinct.

Attempt history and the compact run status are in `results/producer_support_sidecar_export_pilot_20261003_v2/control/chart_export_attempt_status.json`.

## Decision state and next action

This confirms the support-sidecar path through one actual apply H5. It does not qualify the full five-fold / 500-H5 surface, and it does not establish row-level producer support for every training transition. The historical replay H5s still carry run-level support `unknown` and cannot be used as if this one-file pilot repaired them.

C1's score remains locked and unscored. C2 candidate v2 remains unqualified; no numeric C2 scale was fitted. The protocol/analysis gate remains closed.

Next, establish the same per-row support and QC provenance across the complete chart surface required by C2, including its outer-training transitions. Then fit the fold-local coordinate scale from those admitted training rows and bind its numeric digest to the exact fitting-row hash and fitter-code hash. Do not run C1/C2 outcome scoring or effects as part of that qualification.
