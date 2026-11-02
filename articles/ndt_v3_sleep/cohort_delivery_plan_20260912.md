# Full ds005555 cohort delivery contract (2026-09-12)

This document freezes the downstream delivery contract for the current local
continuous full-night ds005555 H5 cohort. It is a descriptive development
analysis plan, not a preregistration and not a population-validation claim.
The source inventory and H5 identities must be supplied by the ingest handoff
that produced the continuous full-night cohort. The historical 2026-09-04
stage-sampled run is rejected for this delivery because its stage sampling
creates irregular increment support. It is retained as historical provenance
only.

## Measurement boundary and source selection

The article reads existing producer surfaces through the installed
`nmd_analysis` readers. It does not rerun ingest, refit a family by stage, tune
an endpoint, repair a source, or identify independent Itô drift. The selected
source manifest is an input to the run and must be frozen before any cohort
outcome is inspected.

The runner accepts exactly one current source manifest. The manifest must
identify the continuous full-night producer run, its configuration and source
hash, and an explicit producer output row for each expected recording. A
successful row has an H5 path plus SHA-256; a producer failure may have a null
H5 path but must carry an explicit failure reason. The runner requires unique
recording identities, checks every listed H5 before and after reading, and
emits an explicit outcome for every expected entry. Missing, unreadable,
hash-mismatched or malformed entries are failures; they are never silently
dropped. No directory glob is used to add or replace entries, and the
historical sampled run cannot satisfy the source contract.

The raw `participants.tsv` and `participants.json` are bound and SHA-256
hashed before execution. `participant_id` in that table is the recording ID;
`pid` is the unique person identifier shared across nights. The current local
inventory has 128 recordings and 100 unique PIDs. The two already inspected
2026-09-10 recordings retain their original `development2` labels: old H5
files are excluded, while fresh current H5s for recording IDs `sub-1` and
`sub-99` remain included and are flagged `prior_development2`. The cohort is
therefore not an unseen validation cohort.

## Descriptive endpoints fixed before cohort execution

The primary label-associated endpoints reuse the frozen E1/E2 family scope:

* local Jacobian `spectral_abscissa`, `numerical_abscissa` and
  `reactivity_gap`, separately for canonical 3D and 9D rows;
* canonical 3D diffusion `D_total`, `d_diff` and `c_diff`.

Rows are mapped using the producer's explicit Jacobian center positions and
canonical diffusion query identifiers. Nonconsecutive centers and time gaps
remain visible; rows are never joined, interpolated, padded or assigned a
stage through neighboring labels. The center/query label is a recording-parent
association. It does not establish stage purity over an estimator's temporal
support. The fixed coordinate reference is the recording-global,
subject-anchored reference already present in each H5. Full executed signal
and filter support remain `unknown` unless the producer records more specific
provenance; this unknown is reported and does not become a zero.

For every endpoint and recording, the runner preserves the producer
`computation_status`, `measurement_validity`, `claim_status`, coordinate
contract/layer, native grain, support fields, finite-value state and validity
state. A row is usable for a descriptive summary only when its endpoint value
is finite and the producer's finite/valid mask allows it. Qualification counts
are always `null`; no biological or stage-intrinsic qualification is inferred.

The following are inventory-only outcomes and remain outside stage-label
summaries unless a later protocol explicitly adds them: recording-horizon FTR
(model-derived recording grain), transition residual/Q proxies, stochastic
reachability, destination and resilience. Independent drift and `A_bD`/
`R_b_over_a` are unavailable when the producer does not supply an independent
chart velocity. The runner records these families' status/failure reason when
the source exposes them, preserving `not_testable`, `unavailable` and missing
states verbatim.

## Labels, missingness and aggregation

Each recording is summarized independently under the fixed parent reference.
The label catalog is `Wake` (0), `N1` (1), `N2` (2), `N3` (3), `REM` (4),
`Code8` (8) and `Unknown` (any other, missing or malformed source label).
Code 8 and other unknowns remain separate categories and are excluded from
the known-stage N2-minus-Wake contrast. Their counts and usable-row counts are
still reported.

For each recording, endpoint and label, the output includes stored/mapped
rows, finite rows, producer-valid rows, support-known and support-valid rows,
used rows, and `n`, median, q25 and q75 of used finite values. An absent or
unsupported endpoint receives the same fixed row with null statistics and an
explicit status/reason. Unknown, unavailable, invalid and failed values remain
visible; no imputation or zero substitution is allowed. These 128-recording
tables remain available even when a producer row fails.

The fixed within-recording contrast is `median(N2) - median(Wake)`. It is
defined only when both groups contain at least one used finite row; otherwise
the contrast and direction are null with its missingness reason. For each PID,
recording-level stage medians are then reduced to the PID median across that
person's nights; recording-level paired contrasts are reduced to the PID
median paired contrast. Cohort tables aggregate those PID-level values in
fixed order, reporting median, q25, q75 and the number of contributing PIDs.
Epochs are never pooled, repeated nights do not create extra participant
weight, recordings with missing endpoints are not replaced, and no p-values,
pooled effect estimates, or confirmatory population claim are produced.

## Output and claim ceiling

The fresh output root is `results/sleep_cohort_20260912/`. It contains the
source/outcome manifest, endpoint rows, 128-recording stage summaries and
contrasts, PID-level summaries and contrasts, cohort aggregation tables,
family availability/failure inventory and code/config provenance. Existing
article outputs are never overwritten.

The safe result is a reproducible, support-audited descriptive report of
existing recording-parent measurements across the locally available
continuous full-night cohort. It does not establish stage-intrinsic dynamics,
filter-pure stage effects, an independent drift, a universal coordinate, a
biomarker or a consciousness/clinical interpretation.

## Bounded readiness check and execution

Before cohort execution, run the article-local driver on a fresh synthetic
manifest containing two small H5 fixtures and one deliberate missing/invalid
entry. Verify exact manifest coverage, duplicate-recording refusal, hash
checks, explicit failure outcomes, unknown-label retention, and repeated-night
PID aggregation (rather than pooled rows). Then run the producer's pinned
pilot H5 into a fresh pilot directory. The full cohort run is permitted only
after the explicit full output manifest and bounded checks pass; no result
direction is used to change this contract.
