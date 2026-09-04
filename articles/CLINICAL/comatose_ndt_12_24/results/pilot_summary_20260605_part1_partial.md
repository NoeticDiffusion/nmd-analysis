# Coma 12-24 h pilot summary

This stamped pilot extends the existing `comatose_ndt` article contract into the
later `12_24h` anchor-relative window using the currently available H5 files in:

`J:/repos/NoeticDiffusion/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260605_060324_12_24h_part1`

## Audit

- full export: `647` H5 runs across `51` subjects
- run midpoint bins:
  - `0_12h`: `586` runs
  - `12_24h`: `56` runs
  - `24_48h`: `5` runs
- true `12_24h` subset: `38` subjects
  - `25 CPC 1`
  - `13 CPC 5`

## Fixed anchor readout

- `tube_d_eff_median`: `2.789` vs `2.477`, `d = +0.264`, `p = 0.479`
- `tube_a_operator_norm_median`: `10.795` vs `9.700`, `d = +0.353`, `p = 0.295`
- `tube_capture_gate_median`: `1.718` vs `1.734`, `d = -0.016`, `p = 0.951`
- `MNJ 3D / spectral_radius_median`: `0.0748` vs `0.0775`, `d = -0.741`, `p = 0.117`
- `MNJ 3D / frobenius_norm_median`: `0.1479` vs `0.1597`, `d = -0.597`, `p = 0.140`

## Interpretation

- The late-window continuation pipeline now works end-to-end under the same metric
  contract as `articles/CLINICAL/comatose_ndt`.
- The current `12_24h` slice is too small for a strong reachability-led claim.
- `MNJ 3D` is the clearest later-window candidate to follow when more H5 files
  arrive.
- The fixed reachability family is presently weak and partly direction-mixed; in
  particular, `tube_a_operator_norm_median` flips sign relative to the main
  early-window article.

## Growth hooks

- The pilot runner `src/run_coma_12_24_pilot.py` already supports a custom
  `--processed-root`, `--stamp`, `--workers`, and figure/QC toggles.
- Later part2 or refreshed part1 exports can be added by rerunning the same entry
  point with a new stamp and then merging at the article layer rather than
  changing the folder structure.
- The current stamped outputs are:
  - `timeline_analysis_20260605_part1_partial_primary12h_allavailable`
  - `mnps_summary_20260605_part1_partial_primary12h_true1224`
  - `outcome_contrasts_20260605_part1_partial_primary12h_true1224_cpc15`
  - `reviewer_checks_20260605_part1_partial_true1224`
  - `pilot_manifest_20260605_part1_partial.json`
