# MNPS v3.1 — sl_027 execution summary (2026-10-09)

## Scope

Executed the five experiments requested in `H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\science_lead\sl_027.md` on the frozen six-participant OpenNeuro ds003838 pilot. No 65-participant run or classifier was run. Estimator formulas and the SC reference count were not changed.

## Results by sequence

### 1. BENCH-002-PREPROCESS-PARITY-001 — pass

MNE 1.6.1 became importable after setting `NUMBA_CACHE_DIR` to a writable temporary directory before import. The parity replay used hash-identical raw EEG and channel metadata, fixed windows/sample indices, and the MNE path from the BENCH-002 runner. All 16 PCV/TP/OI/SC components matched saved measurements within `rtol=1e-7`, `atol=1e-10`; maximum absolute difference was `9.72e-17`.

The historical run did not retain filtered arrays, so byte identity of the prior postprocessed arrays cannot be checked. This establishes measurement parity on the frozen inputs, not bytewise intermediate-array identity.

Evidence: [parity manifest](<J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385\outputs\bench_002_preprocessing_parity_001_20261009_v2\run_manifest.json>) and [component comparison](<J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385\outputs\bench_002_preprocessing_parity_001_20261009_v2\component_parity.csv>).

### 2. BENCH-002-FAST-END2END-001 — pass

The corrected six-person run emitted 7,776 four-second fast-core windows across loads 5, 9, and 13, and 648 full-v3 20-second windows at load 13. All ten post-run checks passed, including finite values, trial-bound support, manifest/input hashes, and unchanged historical full-vector results. The 648 historical windows × 16 numeric components had exactly zero difference. No classifier or full-cohort run was executed.

Evidence: [pilot outputs](<J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385\outputs\bench_002_pilot_v2_fast_gate_fix_20261009\results.md>) and [post-run validation](<J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385\outputs\bench_002_pilot_v2_fast_gate_fix_validation_20261009\results.md>).

### 3. V3-TEMPORAL-FIDELITY-003 — frozen synthetic screens passed

The TP-only transient experiment used 200 seeded signals and 2,600 windows. All four frozen screens passed: 4-second background and transient median absolute bias were 0.00390 and 0.00424; transient-minus-background TP was -0.59843; 20-second mixture median absolute bias was 0.00337. The stationary screen was reused from V002. These results apply to the specified synthetic generator and do not establish physiological validity or validate other coordinates.

Evidence: [transient-screen results](<J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385\outputs\v3_temporal_fidelity_003_pilot_v1_20261009\results.md>) and [frozen protocol](<J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385\v3_temporal_fidelity_003_protocol_v1_20261009.md>).

### 4. V3-REFERENCE-SENSITIVITY-001 — completed, descriptive

The MNE-matched branch reprocessed the same 61 V002 continuous anchors using 4-, 8-, 12-, and 20-second windows; Core19 and native63; and average versus linked-mastoid reference. It emitted 7,808 measurement rows. All rows were computed and valid, but all remain unqualified. All 14 post-run validation checks passed, with zero pair-metadata or paired-value errors. The 4,514 paired component rows consist of seven scalar candidates at all durations plus the nine AR components at 20 seconds; shorter AR vectors are not treated as the canonical nine-component realization.

Reference sensitivity is visible in the primary Core19 surface. Values below are the median of six participant-level median absolute differences (each participant's anchors are repeated observations):

| Candidate | 4 s | 20 s | Native63 4 s | Native63 20 s |
| --- | ---: | ---: | ---: | ---: |
| PCV | 0.126 | 0.127 | 0.124 | 0.131 |
| RD | 0.553 | 0.320 | 0.686 | 0.412 |
| ED | 0.442 | 0.351 | 0.597 | 0.633 |

These are descriptive differences in the estimator's own units, not cross-metric comparable magnitudes. Core19 PCV and RD effects are consequential enough that reference must remain part of the named realization; they do not establish which reference is scientifically preferable. Native63's linked-mastoid output retains TP9/TP10, which therefore become zero. Each MNE recording has one fewer resampled terminal sample than the V002 polyphase branch; the fixed anchors still fit, and the branches were not pooled. Source bad-interval status and upstream composite filter-edge support remain unknown. The files were labelled `task-rest`, but were not assumed to represent physiological rest; no event labels or classifier were used.

Evidence: [reference results](<J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385\outputs\v3_reference_sensitivity_001_mne_pilot_v1_20261009\results.md>), [paired differences](<J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385\outputs\v3_reference_sensitivity_001_mne_pilot_v1_20261009\paired_anchor_differences.csv>), and [participant summaries](<J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385\outputs\v3_reference_sensitivity_001_mne_pilot_v1_20261009\reference_sensitivity_by_participant.csv>). The [14-check validation summary](<J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385\outputs\v3_reference_sensitivity_001_mne_pilot_v1_20261009\validation_summary.json>) records all checks; [validator script](<J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385\validate_v3_reference_sensitivity_001.py>) is rerunnable.

### 5. BENCH-002-GO-NOGO — HOLD for the 65-person run

The engineering parity and corrected six-person execution gates now pass. The full-cohort run remains on hold because the requested temporal-QC gate is not resolved: bad-interval-free status is unknown, and effective support at the edges of the full-recording MNE resample/notch/bandpass chain has not been quantified. This is a run-readiness decision; computable pilot values remain preserved with their QC and qualification state.

Reference sensitivity is a separate comparability issue, not a reason to select a reference by condition contrast. Retain Core19 average as the declared primary BENCH-002 realization and keep any alternative reference separately named. Also preserve the task's fixed control-memory block order as a design limitation in any later condition analysis.

## Required work before reconsidering the full cohort

1. Resolve and record source bad-interval/bad-channel annotations and their relationship to trial windows; do not silently treat unknown as clean.
2. Quantify or explicitly bound effective temporal/filter-edge support for the exact MNE pipeline and planned window placements. Keep unsupported and unqualified outputs explicit.
3. Freeze the planned Core19 average-reference realization and its metadata. Do not pool reference branches or choose one based on a desired contrast.
4. Re-run a bounded support/QC pilot if any preprocessing or support policy changes, then revisit the full-cohort gate.

No code formula, historical result, or cohort output was overwritten. Existing unrelated worktree changes were preserved.
