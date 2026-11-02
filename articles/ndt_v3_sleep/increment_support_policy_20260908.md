# Increment-support audit policy — 2026-09-08

## Purpose and scope

This article-local audit inspects the structural support of already exported candidate diffusion increments and neighbor memberships. It does not recompute tensors, refit any estimator, retune thresholds, create stage contrasts, or upgrade a candidate historical-membership status.

The audit uses the accepted sub-99 HDF5, the pinned diffusion provenance, and the candidate neighbor-membership table from the accepted reconstruction artifact. Original global measurements remain unchanged.

## Frozen structural admissibility

For each candidate source-to-target increment, `admissible_structural` is true only when all of the following hold:

- source and target IDs are present and match the HDF5 epoch table exactly;
- source and target rows are finite and use the same raw-file identifier;
- target ID is the immediately consecutive epoch after source ID;
- target time is strictly later than source time;
- source/target window bounds are finite, ordered, and touching (`source.window_end == target.window_start`);
- the candidate dt equals the HDF5 time difference and is positive.
- the observed HDF5 increment dt matches the stored producer nominal dt and remains within the stored maximum relative-deviation contract (0.05 for this pilot).

No tolerance is introduced for IDs or bounds. The exported candidate distance and selection fields are retained as provenance, not used to change membership.

## Annotation and support states

Stage annotation is tracked separately from structural admissibility. The pool endpoint condition is true only when source and target both have known codes 0–4 and agree with one another; the query-conditioned condition additionally requires the query to be known and equal to both endpoints. These are separate denominators and are never conflated. Code 8 is retained as an explicit unknown/PSG-disconnection state and is never converted to zero or to a known stage.

Full feature/filter support is `not_assessed` unless the input artifacts contain explicit complete support evidence for the relevant estimator increment. Coordinate finiteness, producer masks, and timestamp adjacency do not prove full filter support. Neighborhood stage purity is also `not_assessed`; annotation flags are descriptive endpoint labels only.

## Query/pool summaries

The audit reports the all-adjacent HDF5 increment pool, rather than only the selected candidate rows, alongside candidate query counts, source/target pool counts, structural admissibility counts, code-8 counts, endpoint and query-conditioned stage flags, and missing/unknown structural fields. Unknown, unavailable, invalid, and empty groups remain visible with explicit status fields; no denominator is silently changed.

The audit does not treat a stage flag as a biological qualification or stage-conditioned diffusion result. It reports only whether candidate increment endpoints satisfy the frozen structural contract.

## Provenance and fail-closed rules

The runner requires exact input HDF5, candidate-membership, producer-provenance, policy, code, and output-path pins. It validates candidate query/source/target IDs, bounds, stage codes, and source/target metadata against the HDF5 before writing results. Hash mismatches, stale nonempty output directories, duplicate IDs, missing required columns, malformed bounds, or unexpected statuses stop the run before result tables are emitted.

The output records `claim_status=no_biological_claim`, `historical_membership_status=not_claimed`, `feature_filter_support_status=not_assessed`, and `neighborhood_stage_purity_status=not_assessed`. A passing structural check does not change any of these statuses.

## Frozen interpretation

The admissible-increment result is a window-native diffusion support audit over a recording-parent global candidate pool. It cannot establish historical neighbor identity, full estimator support, stage purity, stage-conditioned diffusion, or a biological claim. Any later stage-conditioned analysis would require a separately frozen experiment with explicit full-support evidence and participant-level governance.
