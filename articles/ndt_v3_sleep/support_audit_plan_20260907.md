# Development support audit: annotations and diffusion neighborhoods

This is a development protocol specified after the sub-99 descriptive pilot,
not a preregistration. Canonical measurements, labels, masks and the accepted
r10 results remain unchanged. No cohort run or inferential test is authorized
by this document.

## Annotation provenance and contiguous support

Trace the accepted epoch table to the selected raw PSG `stage_hum` annotations,
with pinned TSV, events JSON, EEG JSON, README and dataset-description inputs.
Check labels, onsets, durations and the one-based inclusive sample clock.
Compare every row, not only counts. Detect invalid numeric inputs, alignment
shifts and missing source metadata explicitly. The AI scoring is not an
alternative target for this audit.

Report known-stage bouts split at label changes, unknown intervals, nonconsecutive
IDs, gaps or overlaps. Unknown/disconnection intervals may be grouped separately;
they cannot bridge known-stage bouts. Keep all known stages, including absent
ones. Counts and summed durations of absent groups are zero; extrema are
unavailable. Derive the exact two-sided label-boundary count from the bout
structure, retaining the already frozen rule. Full filter support remains
unassessed.

Derive any recording tail from the pinned source duration and represented
window end; missing duration cannot become a hardcoded value. Preserve the
distinction between source code 8 (documented PSG disconnection) and the
analysis layer's existing unknown-stage representation.

## Candidate diffusion-support reconstruction

Before examining reconstructed memberships, freeze these conditions:

- One accepted HDF5, exact stored subject-anchored 3D states, time, epoch IDs,
  source-file segmentation and producer settings; no tuning or new exclusions.
- Snapshot/hash the inspected producer and numerical helpers actually used.
  Record the numerical environment and original input hashes. Matching source
  blobs do not prove the full historical executed tree.
- Recompute using the producer's unchanged k=20 neighborhood rule and stored
  settings. Require exact equality of support counts and validity, and exact
  diffusion-tensor equality after casting to the stored tensor dtype (including
  matching NaN positions). Do not relax this gate after seeing results.
- If reproduction fails, preserve diagnostics and export no qualified candidate
  membership. If it passes, verify that the exported candidate selections also
  reproduce the matched tensor calculation.
- Export candidate query/source/target IDs, distances, dt, endpoint labels,
  disconnection flags and kth-boundary tie diagnostics. Report whether both
  increment endpoints share the query's known label and whether either endpoint
  is code 8. Unknown queries cannot be counted as stage-pure.
- Even a matching tensor is not proof of unique historical membership. Retain
  `candidate_reconstruction` status and explicitly flag equal-distance cutoff
  ties. Do not substitute Jacobian `/nn/indices` for diffusion neighbors.

Diffusion stays window-native with a recording parent. These diagnostics
describe the support of a global estimate, not separately estimated
stage-conditioned diffusion. Historical exactness, full preprocessing support
and biological qualification remain outside this gate.

## Review and reporting

Use fresh outputs with config/code/input/output hashes and before/after source
checks. Independent tests must assert known expected behavior for gaps, unknowns,
empty groups, altered sample clocks, mismatches, reconstruction refusal and ties.
An independent code/run review precedes coordinator interpretation. Preserve
negative evidence and keep earlier article results traceable.

The local participant metadata also requires reconciliation before cohort
inference: 128 table rows contain 100 distinct `pid` values, whereas the README
states 108 individuals. This discrepancy is not resolved by counting IDs alone.
