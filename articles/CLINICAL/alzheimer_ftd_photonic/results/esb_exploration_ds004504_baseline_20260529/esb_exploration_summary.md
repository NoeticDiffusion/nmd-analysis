# Exploratory ESB summary with ds004504 baseline

This pass treats `ds004504` resting-state recordings as the subject-level baseline for the same participants found in the photic cohort.

Definitions used here:

1. `ESB-2 ds004504`: healthy-template deviation of `[photic - rest]` in capacity-guidance space.
2. `h_rest_raw`: post-photic residual distance from the same subject's ds004504 resting baseline.
3. `ESB-3 ds004504`: `ESB-2 ds004504` plus the normalized residual recovery term.

## Coverage

- Resting-state baseline coverage: `86` subjects.
- Subjects with at least 4 post-photic windows: `68` / `88`.
- Subjects with at least 2 eye-labeled post-photic windows: `67` / `88`.

## AD vs Healthy highlights

- Strongest `esb2_ds004504` row: `posterior_capacity_global_guidance` / `photo_15hz` with `d = 0.821`, `p = 0.003128`, `q = 0.006256`.
- Strongest `esb3_ds004504` row: `posterior_capacity_global_guidance` / `photo_15hz` with `d = 0.624`, `p = 0.06832`, `q = 0.07504`.
- Strongest `h_rest_raw` row: `posterior_capacity_global_guidance` / `photo_20hz` with `d = 0.106`, `p = 0.7246`, `q = 0.7467`.

## Frequency pattern check

- `esb2_ds004504` best spec `posterior_capacity_global_guidance` across frequencies: `photo_5hz` d=0.472, `photo_10hz` d=0.493, `photo_15hz` d=0.821, `photo_20hz` d=0.069.
- `esb3_ds004504` best spec `posterior_capacity_global_guidance` across frequencies: `photo_5hz` d=0.161, `photo_10hz` d=0.353, `photo_15hz` d=0.624, `photo_20hz` d=0.167.

## Readout

- If ds004504 solves the baseline problem, `ESB-2 ds004504` should become finite for the full cohort and give a cleaner stage-resolved abnormal-response signal than the pre-photic proxy version.
- If the main lift still comes from `h_rest_raw`, the collapse story remains more recovery-led than evoked-deviation-led even under a real external baseline.