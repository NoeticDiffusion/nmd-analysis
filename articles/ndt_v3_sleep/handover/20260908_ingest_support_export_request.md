# Next bounded ingest change: executed signal-support provenance

Status: implementation handoff, not an implemented or validated export.
Question: which raw samples and fitted references can contribute to each
exported feature row? Keep the canonical measurements and existing outputs fixed.

## Minimum information to persist

1. **Execution record per raw file and signal branch.** Raw identity/hash,
   input/output sampling frequencies and clock mapping; resolved resampling,
   notch, bandpass and PPG filter parameters; library/version; actual branch,
   fallback or failure; kernel/filter length where meaningful; phase, padding,
   crop and boundary handling. Record CSD/rereference as spatial operations,
   separate from temporal filters. A configured operation is not proof it ran.
2. **Per-feature input extent.** Raw-file identity, actual epoch sample bounds,
   nominal time bounds, upstream operation IDs and a support status/reason.
   Distinguish exact finite raw support, known noncompact/nonlocal support,
   and unknown support. Do not substitute epoch bounds for unknown filter
   support. Any effective finite support needs a named approximation and an
   independently tested error bound; no arbitrary number of neighboring epochs.
3. **Reference-fit dependence.** Feature/transform, fitted center/scale,
   included row IDs or a reproducible selection hash, recording/cohort/external
   scope and calibration identity. This is separate from raw temporal support.
   Do not fit separately by sleep stage to manufacture comparable coordinates.
4. **Source quality intervals.** Preserve recorded PSG disconnections/bad
   annotations with their source and clock mapping. Export overlap evidence
   and uncertainty; analysis owns the admissibility rule. Do not silently
   interpolate, bridge, relabel or change canonical masks to obtain a contrast.

The exact schema and migration must be reviewed in the ingest repository before
implementation. Old HDF5 files lacking these records remain unsupported for
this claim; presence of a new field alone cannot certify old executions.

## Bounded acceptance evidence

- Synthetic impulse/edge tests for the actually selected filter/resampling
  branches, including gaps and fallbacks; distinguish mathematical nonlocality
  from a stated approximation.
- Recording of failed or unknown support without invented zeros/bounds.
- Hash-linked source, resolved configuration, executed code and runtime.
- A short reference check into a fresh output root, with unchanged measurement
  definitions; no cohort run. Demonstrate source-clock mapping and disconnection
  handling without using stage differences to select parameters.
- Independent review before importing any support-qualified result into the
  article. Existing global-coordinate descriptive results remain available.

Scientific next gate: use that evidence to freeze an analysis-layer increment
policy and participant aggregation, then run a separately specified replication.
