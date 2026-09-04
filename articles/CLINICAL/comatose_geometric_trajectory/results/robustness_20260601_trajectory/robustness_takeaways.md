# Trajectory robustness takeaways

## Quick read

- `3D irreversibility` is the cleanest temporal-order-sensitive result in the current robustness pass. Its pooled patient-level contrast drops from `d = -0.280` in the observed sequence to `d = 0.050` after within-run `time_shuffled` control, while reverse-time leaves it essentially unchanged, as expected for an absolute flux-asymmetry score.
- `3D noetic_action` does **not** collapse under shuffle. The pooled contrast strengthens from `d = -0.290` to `d = -0.362` after `time_shuffled`, which argues against a narrow "native temporal grammar only" interpretation. Right now it looks more like a broader roughness / spread / friction marker.
- `9D noetic_action_jerk` behaves even more strongly like a roughness marker than a time-arrow marker. The observed pooled contrast is modest (`d = -0.240`), reverse-time is invariant, and `time_shuffled` amplifies the separation to `d = -0.388`.
- `9D entropy_rate` is also not strongly order-specific in the current implementation. Its pooled effect changes only modestly under shuffle (`d = 0.158` to `0.147`), suggesting that it is driven at least partly by occupancy / repertoire spread rather than by fine transition grammar.

## QC read

- The action-family metrics are the least coupled to basic support variables. `3D noetic_action` has weak associations with `n_runs_support`, `n_windows_total`, `channel_count_median`, and `channel_coverage_frac_median` in the pooled patient summary.
- `Irreversibility` and entropy-family metrics show more QC dependence, especially positive association with `n_runs_support` and negative association with channel count / coverage. That does not invalidate them, but it means any promotion of `irreversibility` should keep support/coverage sensitivity visible.

## Current interpretation

- If we want one metric that still looks like a genuine temporal-order signal, the best current candidate is `3D irreversibility`.
- If we want one metric that survives discovery, validation, and now pooled robustness as the empirically strongest separator, the best current candidate is still `3D noetic_action`, but it should be framed as a broader friction / roughness observable rather than a strict time-arrow metric.
- `9D jerk_action` remains interesting, but the null behavior says it should not be framed narrowly as burst-suppression or ordered-transport evidence yet.
