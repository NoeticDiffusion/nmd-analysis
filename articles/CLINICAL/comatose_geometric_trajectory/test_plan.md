# Geometric Trajectory Follow-Up Test Plan

This note lists the checks needed before `Outcome-Linked Geometric Trajectory After Cardiac-Arrest Coma.typ` should be treated as a manuscript rather than an exploratory draft.

## 1. Provenance and overlap

- Confirm the exploratory run uses the intended I-CARE processed bundles and records them in an explicit manifest.
- Keep `part1` and `part2` separate until subject/run overlap is audited.
- State clearly whether each reported result is:
  - `part1` exploratory only,
  - `part2` exploratory only,
  - or a later pooled synthesis.

## 2. Coordinate contract

- Confirm that v1 uses `subject_anchored` trajectories as the primary path object.
- Keep `3D` and `9D` outputs separate in both filenames and tables.
- Do not mix `subject_anchored` and `cohort_anchored` trajectories inside one metric family.

## 3. Metric implementation checks

- Verify the exact v1 metrics:
  - `irreversibility`
  - `entropy_rate`
  - `noetic_action`
- Confirm the discretization rule used for transition metrics is frozen and recorded.
- Confirm the noetic-action metric, potential choice, and normalization matrix are all written to the run manifest.

## 4. Timeline and outcome checks

- Confirm the primary time bin is `0_12h` after EEG-anchor.
- Confirm the primary contrast is later `CPC 1` versus later `CPC 5`.
- Confirm the timing source comes from `time_reference.v1` when available, with any fallback counted in the manifest.

## 5. Result exports

- Export run-level trajectory metrics.
- Export patient-timebin trajectory metrics.
- Export patient-level `CPC 1` versus `CPC 5` contrasts for all article-facing metrics.
- Record support counts and missingness in the output manifest.

## 6. Interpretation boundary

- Treat the article as exploratory until the first outputs are reviewed.
- Do not claim a frozen biomarker hierarchy before metric behavior is inspected.
- Keep WLST / care-pathway caveats explicit for `CPC 5`.
- Do not overread irreversibility as a literal thermodynamic theorem.

## 7. Minimal manuscript checks

- `typst compile` succeeds.
- No missing citation keys.
- The Methods section matches the implemented trajectory metrics.
- The Results section clearly marks placeholder versus measured outputs.
