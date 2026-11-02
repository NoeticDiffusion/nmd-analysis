# Stage-dependency policy for the sleep development pilot

**Policy version:** `ndt.sleep.stage_dependency_policy.v1`  
**Scope:** the already-seen sub-99 development recording and the current MNPS v3 evidence. This is a development policy, not a preregistration and not a population result.

## Decision

Recording-parent descriptive associations with the recorded sleep labels are
`allowed_description_with_limitations`. They must retain the canonical MNPS
3D/9D coordinates, the fixed recording-wide parent normalization, all
validity and missingness masks, denominators, and source-quality provenance.
The policy does not qualify a stage-intrinsic dynamical measurement:
`stage_purity_status = not_assessed` and `full_qualified_count = null`.

The descriptive object is a property of this recording and its parent
coordinate system. It may show how recorded labels coincide with measured
coordinates; it does not establish that a filter-pure, stage-specific process
generated those coordinates, nor that stages are biologically separable.

## Coordinate and reference policy

The recording-wide parent normalization is fitted once and held fixed across
all labels. Per-stage fitting, refitting, or stage-dependent calibration is
prohibited. A global robust-z/reference fit is a known nonlocal recording
dependency and must be reported as such; it is not, by itself, grounds for
rejecting a descriptive association. Across participants the coordinates are
relative standardized coordinates, not universal absolute units. Replication
and any inference therefore use independent participants as the unit.

Here the parent is the actual processed input artifact. A cropped engineering
reference is not a whole-night reference, and two artifacts from the same
participant are not independent replication. The declared normalization rule
must be distinguished from evidence that it was followed: missing legacy fit
provenance remains unknown. A descriptive contrast requires enough known-stage
observations and documented validity; permission to inspect labels alone is
not evidence that a usable contrast exists.

The current evidence does not provide a complete executed feature/filter
dependency graph. The v1 signal-support reader can validate structural
provenance and row alignment, but the effective temporal support remains
`unknown`. A nominal 30-second epoch extent is not a finite filter-support
certificate. Filter/resampling padding, the complete feature graph, and the
PPG fallback's semantic equivalence are not established. No arbitrary guard
margin, endpoint label, or neighboring label may be promoted to a purity
certificate.

## Stage-intrinsic gate

Stage-intrinsic dynamics remain `not_assessed` until the following are
available for the actual execution: per-row feature and filter support,
filter/resampling/padding provenance, source-quality overlap handling, the
complete estimator-neighborhood support, and an explicitly stage-conditioned
construction. This gate does not permit stage-specific diffusion, Jacobian,
FTR, Q, or W_Q claims. Recording-grain Q/W_Q remains at recording grain and
must never be assigned to an epoch or stage.

The current increment evidence is structural adjacency only. Known endpoint
labels can support descriptive summaries, but do not prove stage purity. Source
quality code `8` is preserved literally with its source interval provenance;
it is not relabeled into a biological stage, used as a mask, or removed by a
refit under this policy.

## Replication and reporting

This is a development policy for data already inspected, not a preregistered
analysis. Any replication claim requires independent participant recordings
under the same frozen policy. A future cohort analysis must report participant
counts, per-label denominators, missingness, validity, source-quality/code-8
coverage, and the fixed parent-normalization provenance before any contrast is
interpreted.

**Safe claim:** bounded, recording-parent descriptive label associations may be
reported with the stated limitations.  
**Not established:** stage-intrinsic filter-pure dynamics, biological stage
discrimination, population inference, or stage-conditioned Q/W_Q/diffusion
qualification.
