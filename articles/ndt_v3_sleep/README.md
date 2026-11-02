# Neural State Geometry and Dynamical Measurement Families Across Sleep

Current study: the complete locally available ds005555 PSG cohort, with 128
nights from 100 people and 120,091 continuous 30-second epochs. The main
manuscript now reports the cohort's nine fixed Jacobian/diffusion endpoints.
The previous manuscript is preserved as `Development history before full
cohort 20260912.typ`; the development sections below remain historical.

Current entry points:

- Results and limitations: [sciencelead/13_sleep_full_cohort_results.md](sciencelead/13_sleep_full_cohort_results.md).
- Tables and figure: `results/sleep_cohort_20260912`.
- Exact analysis command: [handover/20260912_sleep_cohort_analysis_commands.md](handover/20260912_sleep_cohort_analysis_commands.md).
- Reviewed H5 manifest: `H:/SourceRepo2/NeuralManifoldDynamics/project/v3/sleep_dataset_delivery_20260912/coordinator_reviewed_analysis_inputs.json`.
- Full reviews: `peer_review/20_sleep_cohort_delivery_review.md` and `peer_review/21_sleep_cohort_final_review.md`.

The current analysis uses the frozen config with an explicit `--source-manifest`
override. The canonical historical execution manifest is not its active input.
The reviewed input retains `source_hashes_stable=false` from operational source
edits during the ingest run; the basis and limits of accepting the pinned H5
artifacts are recorded in the coordinator review. Missing 9D outputs for sub-3
and sub-4 remain null. No biological or population-validation claim is made.

## Development history


Development article workspace for the ds005555 NMD v3 sleep pilot. This
directory is derived from `articles/aa_template`; the source template is
unchanged.

The study begins with a support and missingness audit of the verified sub-99
recording. Primary analyses use MNPS state coordinates and diffusion geometry
when their recorded support and validity metadata permit them. Recording-level
Q/W_Q summaries remain measurement proxies and are not stage-level
observations. The 9D `v_norm` endpoint is method-limited in the current
sensitivity diagnostic and is excluded from biological conclusions until an
independent numerical reference is complete. Destination and resilience
families may remain explicitly unavailable.

The staged analysis plan is in `analysis_plan.md`. No results, contrasts,
sample counts, or literature claims should be added until supported by
recorded run artifacts and cited sources. The cohort protocol is still a
working governance document; it is not presented as preregistered.

## Files

- `Neural State Geometry and Dynamical Measurement Families Across Sleep.typ` â€” main manuscript.
- `S1_Supplementary_methods.typ` â€” measurement contract and statistical plan.
- `S2_Supplementary_data.typ` â€” reserved for complete reported tables.
- `S3_Supplementary_QC_Robustness.typ` â€” support, missingness, and robustness audit.
- `S4_Supplementary_Clinical.typ` â€” scoped interpretation, written after results.
- `S5_Glossary.typ` â€” terms and endpoint definitions.
- `S6_Changelog.typ` â€” internal provenance and revision history.
- `analysis_plan.md` â€” staged analysis protocol.

Do not copy raw HDF5 files into this article directory. Store only manifests,
audits, tables, figures, and links or hashes for source artifacts.

## Run the bounded import pilot

From `J:/repos/nmd-analysis` in PowerShell:

```powershell
$env:PYTHONPATH='J:\repos\nmd-analysis\nmd-analysis'
$env:PYTHONDONTWRITEBYTECODE='1'
.venv/Scripts/python.exe -B articles/ndt_v3_sleep/src/sleep_pilot.py --config articles/ndt_v3_sleep/config/pilot_sub99_verified.yaml
```

The config pins one source H5 by path and SHA256. The runner uses the existing
analysis-package pipeline and writes its exact extraction/support audit plus
an article manifest and epoch-label audit. Recording MNPS, Jacobian, FTR and
Q/W_Q tables retain recording grain. No sleep contrast is enabled.

The default destination is `results/pilot_verified_20260906`. A nonempty output
directory is refused. For another run, supply `--output-root` with a new,
explicit directory; retain earlier runs. `results/pilot_20260906` is a
superseded development run and must not be used as the accepted pilot.

The **accepted reviewed run** is
[`results/pilot_verified_final_20260906`](results/pilot_verified_final_20260906).
The default destination above also contains a superseded intermediate run;
choose a new output directory for any repetition. The final run used the
additional argument
`--output-root articles/ndt_v3_sleep/results/pilot_verified_final_20260906`.

Read [the pilot readiness assessment](sciencelead/01_pilot_readiness.md) for
the actual available measures, limitations and next implementation step.

The per-row `stage_purity_status=not_assessed` is intentional: aligned labels
do not establish that each estimator's full support lies within one stage.
See `sciencelead/` and `peer_review/` for the actual run verdict and remaining
work before stage contrasts.

## Current result: reviewed descriptive pilot, 2026-09-07

The accepted run is
[`descriptive_epoch_sub99_20260907_r10`](results/descriptive_epoch_sub99_20260907_r10).
Earlier descriptive candidates r1-r9 are development history and are not the
article's accepted results. The historical epoch readiness report describes
the earlier disk-space blockage; integration is now complete.

The source contains 1,068 windows, including nine unknown labels. Primary
coordinate summaries use 1,059 windows; the fixed two-sided same-label rule
retains 935. N1 drops from 20 to 2 and N3 from 15 to 0. N3 boundary statistics
remain unavailable. This is descriptive evidence from one recording, not
population inference or qualification of stage-conditioned dynamics.

All 42 article tests pass. Independent review and coordinator recomputation
verify the 120 3D/9D coordinate summary rows and registered artifact hashes.
The integrated epoch exporter was also rerun on J: and produced an identical
Parquet file. Read the [current assessment](sciencelead/02_descriptive_pilot_readiness.md),
[independent review](peer_review/04_stage_descriptive_review.md), and
[coordinator validation](handover/20260907_descriptive_coordinator_validation.json).

Reproduce the descriptive analysis from the repository root, choosing a fresh
output directory (the accepted output must not be overwritten):

```powershell
$env:PYTHONPATH='J:/repos/nmd-analysis/nmd-analysis;J:/repos/nmd-analysis/articles/ndt_v3_sleep/src'
$env:PYTHONDONTWRITEBYTECODE='1'
& 'H:/SourceRepo2/NeuralManifoldDynamics/.venv/Scripts/python.exe' -B articles/ndt_v3_sleep/src/descriptive_epoch_analysis.py --table articles/ndt_v3_sleep/results/epoch_support_20260907/epoch_coordinates.parquet --output articles/ndt_v3_sleep/results/descriptive_epoch_sub99_replication --config articles/ndt_v3_sleep/config/descriptive_sub99.yaml
```

The CLI requires the pinned config. The explicit output argument controls the
destination; the config's output field records the accepted run location.
Input table, epoch manifest, runner code and fixed policy are validated before
output creation. Full feature/filter support, anchor provenance and diffusion
neighborhood purity remain unresolved. The PPG fallback is not semantically
equivalent to the intended e_m signal.

## Annotation and run-support audit

The bounded audit at
[`results/stage_support_audit_20260907_r7`](results/stage_support_audit_20260907_r7)
compares the epoch table with the authoritative human-scored `stage_hum`
annotation source. It found 84 contiguous label/status bouts: 83 known-stage
bouts and one unresolved code-8 PSG-disconnection bout. The 15 N3 bouts are
all single 30-second windows; this explains the loss of N3 under the fixed
two-sided boundary diagnostic, but does not imply an annotation error or
absence of N3 physiology. The audit retained code 8 as unknown and did not
substitute `stage_ai`.

The source alignment is supported by exact onset/duration and 256-Hz sample
clock checks. The raw recording duration is 32,064 seconds while the accepted
epoch bounds end at 32,040 seconds, leaving a 24-second tail outside the epoch
table. This is a bounded annotation and run-support audit; full estimator,
filter, and diffusion-neighborhood purity remain `not_assessed`, and the audit
is documented in the independent reviews. A future cohort limitation is an unresolved metadata
discrepancy: `participants.tsv` contains 128 rows and 100 distinct participant
IDs, while the local README reports 108 people.

## Candidate diffusion-support audit

Accepted candidate run: `results/diffusion_support_reconstruction_sub99_20260907_r9`.
All 1,068 stored tensors and 21,360 selections were independently reconstructed.
281/1,059 known queries have all 20 increments' endpoints in the query stage;
33 known queries touch a disconnection endpoint. Membership remains candidate-only,
with historical identity unclaimed and full feature/filter support unassessed.
The complete article suite now passes 65 tests. See
[support summary](sciencelead/04_source_and_neighborhood_audit.md) and
[direct verification](handover/20260907_support_coordinator_validation.json).

## 2026-09-08 feature/filter and increment-support audit

Accepted run: `results/increment_support_sub99_20260908_r2`. It retains the
whole adjacent HDF5 pool separately from the frozen candidate selections.
All 1,067 pairs are structurally admissible; 976 have matching known endpoints
(Wake 258, N1 4, N2 609, N3 0, REM 105). Ten pairs touch code 8.
Full-support-qualified counts are unavailable, not zero. No tensor was refitted.

The source audit distinguishes a recording-global robust-z fit from unknown
executed filter/resampling support. The effective epoch grid is 30/30 seconds;
generic 8/4 metadata is explicitly distinguished in the stored time-grid audit.
See [current summary](sciencelead/05_feature_filter_and_increment_support.md),
[source inventory](handover/20260908_feature_filter_support_audit.md),
[fixed policy](increment_support_policy_20260908.md), and
[next ingest implementation handoff](handover/20260908_ingest_support_export_request.md).
