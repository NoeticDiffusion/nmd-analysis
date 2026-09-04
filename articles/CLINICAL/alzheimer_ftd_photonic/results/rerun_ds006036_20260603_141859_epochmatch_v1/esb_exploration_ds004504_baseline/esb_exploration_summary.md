# Exploratory ESB summary with ds004504 baseline

This pass treats `ds004504` resting-state recordings as the subject-level baseline for the same participants found in the photic cohort.

Definitions used here:

1. `ESB-2 ds004504`: healthy-template deviation of `[photic - rest]` in capacity-guidance space.
2. `h_rest_raw`: post-photic residual distance from the same subject's ds004504 resting baseline.
3. `ESB-3 ds004504`: `ESB-2 ds004504` plus the normalized residual recovery term.

## Coverage

- Resting-state baseline coverage: `88` subjects.
- Subjects with at least 4 post-photic windows: `68` / `88`.
- Subjects with at least 2 eye-labeled post-photic windows: `67` / `88`.

## AD vs Healthy highlights

- Strongest `esb2_ds004504` row: `posterior_capacity_global_guidance` / `photo_5hz` with `d = 0.586`, `p = 0.01297`, `q = 0.02595`.
- Strongest `esb3_ds004504` row: `posterior_capacity_global_guidance` / `photo_5hz` with `d = 0.328`, `p = 0.09492`, `q = 0.126`.
- Strongest `h_rest_raw` row: `posterior_capacity_global_guidance` / `photo_5hz` with `d = 0.179`, `p = 0.5687`, `q = 0.5961`.

## Frequency pattern check

- `esb2_ds004504` best spec `posterior_capacity_global_guidance` across frequencies: `photo_5hz` d=0.586, `photo_10hz` d=0.401, `photo_15hz` d=0.603, `photo_20hz` d=0.207.
- `esb3_ds004504` best spec `posterior_capacity_global_guidance` across frequencies: `photo_5hz` d=0.328, `photo_10hz` d=0.289, `photo_15hz` d=0.373, `photo_20hz` d=0.171.

## Readout

- If ds004504 solves the baseline problem, `ESB-2 ds004504` should become finite for the full cohort and give a cleaner stage-resolved abnormal-response signal than the pre-photic proxy version.
- If the main lift still comes from `h_rest_raw`, the collapse story remains more recovery-led than evoked-deviation-led even under a real external baseline.