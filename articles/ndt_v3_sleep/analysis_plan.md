# Prospective analysis plan

## Question and scope

The pilot asks whether sleep-stage state geometry and dynamical measurement
families can be extracted with auditable temporal support from the verified
ds005555 sub-99 recording. It is a methods and support study until the
planned extraction, missingness, and within-person development checks are
complete.
It does not authorize biological claims from recording-level proxies.

## Frozen order

1. Import the verified source read-only and record source, code, config, and
   runtime hashes.
2. Audit continuous time support, epoch/window support, stage labels,
   coordinate contracts, computation status, measurement validity, and
   missingness before any contrast.
3. Define the eligible state-stage join using explicit time intervals. A label
   is usable only when the requested measurement support is contained in the
   stage interval; gaps, overlaps, and unknown alignment remain unavailable.
4. Aggregate within participant and recording first. The participant is the
   unit for any later cohort inference; windows and transitions are repeated
   measurements, not independent participants.
5. Run the primary MNPS and diffusion endpoints that pass their support and
   validity contracts. Keep all preselected dynamical horizons in diagnostic
   tables; never choose a horizon after inspecting outcomes.
6. Run the planned within-person summaries and QC audit. Only then decide
   whether a separate cohort extension has sufficient participants and support.

## Endpoint policy

Primary candidates are MNPS state geometry and diffusion-family summaries when
their canonical source status is computed and their support is valid. Q/W_Q
is a recording-level one-step transition residual covariance proxy; it is not
relabelled as a sleep-stage or individual-level noise estimate. The current
9D `v_norm` sensitivity evidence is method-limited and remains descriptive
only. Destination and resilience outputs may be unavailable and must retain
their explicit failure status. DF-DRIFT-C1/M3 remains a candidate estimator,
not a qualified empirical endpoint.

## Missingness and exclusions

Do not replace unavailable, invalid, irregular-dt, insufficient-support, or
nonfinite measurements with zeros. Report counts and reasons by stage,
recording, coordinate contract, and endpoint. Stage strata are descriptive
until temporal containment and repeated-measure structure are verified.

## Statistical freeze

No biological contrast, multiple-comparison family, or effect-size claim is
preregistered by this development document. After the support audit fixes the
eligible participant set and endpoint table, any later cohort analysis must state its participant
inclusion rule, within-participant aggregation, contrast, effect size,
correction family, and robustness checks before reading results.

## Reproducibility

Each run receives a fresh output directory, source and code hashes, config
hash, runtime versions, manifest, audit, and a changelog entry. The article
directory contains no raw HDF5. Historical or invalid Gate F artifacts remain
provenance evidence and are not silently upgraded by a shorter-horizon run.

## 2026-09-07 development experiment: labelled global coordinates

This amendment is specified before inspecting the new descriptive outputs,
but after inspecting the source support audit and stage counts. It is not a
preregistration or a confirmation study. It does not relax the full-support
containment requirement for any future stage-conditioned endpoint.

The bounded experiment uses the already verified sub-99 epoch table. Its
question is how recorded global MNPS coordinates are distributed among the
aligned window labels, and how these descriptive distributions change when
immediate label boundaries are excluded. It does not estimate a separate
geometry, diffusion neighborhood, or dynamical model for each sleep stage.

Eligibility is evaluated separately for 3D and 9D: a known stage label, a
finite complete coordinate vector, explicitly true `coverage_ok` and
`retained_after_qc`, and the corresponding explicitly true producer mask
(`geometry_valid` for 3D, `coords_9d_valid` for 9D). Missing masks cannot pass.
All source rows remain in the coverage audit, including unknown labels and
failed or unknown masks. Joint exclusions and separate failure reasons must
not be confused: one row can fail more than one condition.

The fixed sensitivity subset additionally requires the immediately preceding
and following windows to have the same known stage label, consecutive IDs,
and touching window bounds. Recording endpoints, gaps and unknown labels
cannot satisfy this three-window condition. This is a label-boundary
diagnostic, not verified filter support or neighborhood stage purity.

Report counts and median/25th/75th percentiles for every coordinate and stage
under both policies, retaining empty groups as unavailable. Provide a temporal
trajectory with breaks at unsupported intervals and descriptive distribution
figures. Do not compute population tests, choose a favored coordinate after
inspection, infer clinical significance, or replicate recording-level Q/W_Q.
The `e_m` PPG fallback is not semantically equivalent to its intended signal;
its limitation accompanies any displayed coordinate summaries.

Full filter support, anchor provenance and diffusion-neighborhood purity
remain unresolved. Any observed separation is development evidence from one
recording and will inform a separately specified replication protocol.

## 2026-09-07 annotation and run-support audit

The bounded audit compares the accepted epoch table with the authoritative
human-scored `stage_hum` column in the original ds005555 sub-99 event TSV. It
checks row-to-epoch mapping, onset and duration, sample-clock alignment using the
pinned 256-Hz EEG metadata, stage-code/status mapping, gaps, and the recording
end. `stage_ai` is retained as available source metadata but is not used as a
replacement. Code 8 remains an explicitly unknown PSG-disconnection status and
does not bridge known-stage runs.

The audit contains 84 contiguous label/status bouts: 83 known-stage bouts and
one unknown/disconnection bout. Known-stage counts are Wake 17 bouts/275
windows, N1 16/20, N2 33/642, N3 15/15, and REM 2/107; every N3 bout is one
30-second window. These are support facts for the single recording, not a
relabeling judgment or evidence that N3 physiology is absent. The raw recording
duration is 32,064 seconds and the accepted epoch table ends at 32,040
seconds, so the 24-second tail is outside the audited epoch table.

This audit does not establish full filter containment, diffusion-neighborhood
purity, or stage purity for any estimator. Those gates remain
`not_assessed`; no stage-conditioned estimator or population inference is
authorized by this amendment. The cohort metadata also remains unresolved:
`participants.tsv` has 128 rows and 100 distinct participant IDs, whereas the
local dataset README reports 108 people. That discrepancy is recorded as a
future cohort-governance limitation and is not used to reinterpret this
single-recording pilot.

## Candidate support result and next gate

The frozen reconstruction protocol is in `support_audit_plan_20260907.md`.
Candidate run r9 exactly reproduces the stored global diffusion tensors and
independently verified selections. 281/1,059 known queries have all 20 increments
entirely in the query stage, while 33 known queries touch code-8 endpoints.
These diagnostics neither alter producer measurements nor establish historical
membership or full preprocessing support. Before a stage-conditioned experiment,
specify admissible increments, gap boundaries, full feature/filter containment,
and participant aggregation. Preserve the original estimates for comparison;
do not choose exclusions based on favorable stage contrasts.

## 2026-09-08 implemented support audit

The frozen structural/annotation policy is implemented in
`src/increment_support_audit.py`, with the accepted bounded result in
`results/increment_support_sub99_20260908_r2`. Full adjacent-pool support is
separate from selected candidate support. The inventory establishes nominal
30-second feature input and recording-global reference fitting, but lacks
sufficient executed filter/resampling provenance for full-support qualification.
No new stage-conditioned estimator was run. The next gate is the bounded ingest
provenance export in `handover/20260908_ingest_support_export_request.md`.
