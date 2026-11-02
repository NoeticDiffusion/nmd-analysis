# 538 — 2026-10-02 — Support sidecar binding pilot

## Scope

Bound the existing two-recording raw-EDF producer pilot to the QC-filtered candidate row identities, then audited the same MNDM support-export helper used by the H5 writer. The audit reads identity, time, sample-support, and QC metadata only. It does not read chart coordinate arrays or outcomes, or calculate scores/effects.

## Inputs and row binding

- The QC-filtered candidate table is `K:\processed\boas_sleep_c1c2_qc_filtered_fold_chart_replay_20261002_v2\processed\ds005555\features.parquet` (SHA-256 `139a9c5b685d2050107479d12ee8dc0070ae997ca4e1a31ecfb2af30226482c6`). The staging script reads only its identity columns to select rows.
- The pilot tables and QC sidecars were produced together from the two K: EDFs in `results/producer_support_pilot_20261001/`. The staging output copies no EDFs and copies the QC sidecars byte-for-byte.
- Fold 1 maps `sub-100` (`sub-067`) to training and `sub-105` (`sub-073`) to apply. The staged full input contains 996 training rows and 961 apply rows. The three sub-105 pilot rows absent from the candidate surface (epochs 722, 831, 845) are excluded by exact file/epoch/time identity.
- Staging script: `src/run_support_sidecar_export_pilot.py`. Full input manifest and config: `results/producer_support_sidecar_export_pilot_20261002_v1/control/`.

## Metadata-only export-helper result

`src/audit_support_sidecar_export_binding.py` passed the sub-105 / fold-1 apply audit through MNDM `build_signal_support_export` at revision `53bae391015a5bad51b8013c312745a8d90e52f5`. The result is `results/producer_support_sidecar_export_pilot_20261002_v1/control/sidecar_export_binding_audit.json`.

- The sidecar validates and its raw source SHA-256 matches the frozen fold manifest.
- All 961 apply rows have a validated nominal sample mapping, a finite-causal conservative contributor bound, and the matching source-file hash.
- The helper payload contains eight source annotation intervals. Its full validated execution record also retains the seven raw joint-EEG flatline intervals from the sidecar.
- No selected QC-filtered apply row overlaps those source annotation or raw flatline intervals. The reviewed epochs intersecting those intervals are absent from this row surface.
- H5-scoped helper payload support is `finite_causal_conservative_bound`. The run-level manifest collector separately reports temporal support as `unknown` by design; these scopes should not be conflated.

This verifies the helper payload and sidecar-to-row binding, but not H5 binary serialization: the payload audit sets `h5_binary_written_or_verified=false`.

## Bounded chart-export attempts

Two MNDM `summarize` attempts used separate output roots and were stopped at their stated time limits after producing no H5 or `run_manifest.json`:

| Input | Limit | Result |
|---|---:|---|
| Full two-recording input, 1,957 rows | 15 min | CPU-active; no chart output |
| Reduced input, 1 training + 128 apply rows | 5 min | CPU-active; no chart output |

Each attempt has a `chart_export_attempt_status.json` beside its staged inputs. Neither attempt copied or parsed raw EDFs. Fold source-hash verification may read the EDF bytes directly from K:. Both processes were stopped after the limits; no scores/effects were calculated.

The runtime of the actual chart serialization path remains unresolved. The metadata helper succeeds independently, so the current evidence isolates the remaining check to completing and inspecting a real H5 export, rather than validating the sidecar identity or row-support payload.

## Decision state and next action

C1’s score remains locked and unscored. C2’s variable remains an outcome-blind candidate; no coordinate values or scale were fitted, and C2 is not qualified. The separate protocol/analysis gate remains closed.

Next, profile one-recording `summarize` with verbose stage logging and complete a single H5 export with the same row-bound sidecar. Inspect only H5 provenance metadata and dataset shapes. Bind any C2 fold-local scale to fitting row IDs and code only after the producer support contract is established for the intended chart surface.
