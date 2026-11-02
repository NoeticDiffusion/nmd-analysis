# Temporal support contract for the sub-99 development pilot

This contract records what the verified source can establish about temporal support. It is an audit contract, not a biological qualification.

## Source grid

The inspected source is `H:\SourceRepo2\NeuralManifoldDynamics\project\v3\ds005555_float64_verified_20260906\ds005555\neuralmanifolddynamics_ds005555_20260906_064207\sub-99_Sleep_acq-psg\sub-99_Sleep_acq-psg.h5`. It contains 1068 aligned windows. `/time` is finite and strictly increasing from 15 to 32025 seconds with exact spacing 30 seconds. `/window_start` and `/window_end` contain 1068 finite 30-second intervals, from `[0,30]` through `[32010,32040]`. The stage codes are 0:275, 1:20, 2:642, 3:15, 4:107, and 8:9.

The recorded masks `/qc/windows/coverage_ok`, `/qc/windows/retained_after_qc`, `/qc/windows/geometry_valid`, and `/qc/windows/coords_9d_valid` each contain 1068 true values. These masks establish recorded row-level availability only. They do not establish filter support, neighborhood purity, or future outcome availability.

## Transition and family support

The primary transition series contains 1065 rows. `H:\SourceRepo2\NeuralManifoldDynamics\project\v3\ds005555_float64_verified_20260906\ds005555\neuralmanifolddynamics_ds005555_20260906_064207\sub-99_Sleep_acq-psg\sub-99_Sleep_acq-psg.h5:/transition_residuals/v1/primary/series/source_window_id` is exactly 0 through 1064, and the corresponding `target_window_id` is exactly 1 through 1065. A one-step Q or W_Q recording therefore has transition support between adjacent recorded windows. Its recording grain must remain explicit; a stage label on either endpoint does not turn it into a stage-conditional estimate.

The analysis reader is `J:\repos\nmd-analysis\nmd-analysis\nmd_analysis\dynamical_families\readers.py::read_family`; `J:\repos\nmd-analysis\nmd-analysis\nmd_analysis\dynamical_families\adapters.py::diffusion_window_rows` requires aligned IDs and timestamps. It does not require every family scalar to be finite; scalar NaNs remain status/data limitations, while state-tensor validity is checked separately. Diffusion neighborhoods are state-space neighborhoods. They are global geometry unless a separate, verified stage-conditioned construction is recorded. Stage labels cannot be used as a proxy for that construction.

## Feature and coordinate provenance

The source records the support signature for `e_m` as `source=fallback`, feature `ppg_rate_bpm`, with `semantic_equivalence=false`. The source has feature metadata and robust-z information, but no per-filter temporal-support mask that would prove effective support for every derived coordinate. Anchor state identifiers, anchor hash, and anchor source were not recovered as a verified, complete temporal-support contract. These omissions remain missingness, not evidence of purity.

## Allowed and disallowed conclusions

The pilot may report exact ID/time/bound alignment, finite and monotone time, interval gaps or overlaps, row-level QC masks, family status and validity, recording grain, and provenance or missingness. Unknown stage codes must remain unknown. Missing or unavailable family status must remain unavailable. `stage_purity_status` stays `not_assessed` unless a separate support audit proves it. `recording_wq_used_as_stage` is false.

The pilot must not bridge gaps, infer temporal purity from equal stage labels, promote recording-grain Q/W_Q to stage grain, treat a state-space neighborhood as stage-conditioned, or treat the `e_m` PPG fallback as equivalent to the intended coordinate. Future-epoch prediction remains a separate, unrun measurement step.
