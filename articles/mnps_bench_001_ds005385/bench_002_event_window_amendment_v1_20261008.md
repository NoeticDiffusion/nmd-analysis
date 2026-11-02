# BENCH-002 event-window amendment v1

Date: 2026-10-08  
Status: frozen before this pilot's MNPS feature extraction. This amendment resolves the sample-window rule and pilot implementation for the already-selected six participants. It does not change `bench_002_scope_freeze_v1_20261008.json` or authorize a full-cohort run.

## Dataset and participants

Use the local DOI-pinned OpenNeuro release `ds003838` v1.0.6 (`10.18112/openneuro.ds003838.v1.0.6`). Confirm the version from `dataset_description.json` and the top `CHANGES` entry. The bounded pilot uses the previously selected participants `sub-032`, `sub-033`, `sub-034`, `sub-035`, `sub-036`, and `sub-038`, with EEG exclusion flag `no`. Do not expand the roster in this run.

## Trial and source-sample boundaries

Parse `events.tsv` digit rows from the `trial_type` condition, position, and list-length fields; require a complete position sequence `1..load` and retain load 5, 9, and 13 for both control/listening and memory instructions. A trial's source interval is the half-open interval

`[first_digit_sample, last_digit_sample + 3000)`

at the 1,000-Hz source rate. The last digit trigger marks stimulus onset. The task script has a two-second digit cycle followed by a one-second explicit `retention_1s` routine; the task paper describes a three-second retention period. Thus the 3,000-sample endpoint is measured from the final digit-onset trigger. The EEG export does not retain the `retention_1s` or recall trigger itself, so this endpoint is supported by the script and published method, not by a retained end marker. Retrieval speech and ITI are outside the interval. Do not exclude trials based on recall correctness.

The 250-Hz grid maps the source interval inward: `ceil(start/4)` to `floor(end/4)`, end exclusive. This keeps every processed sample within the frozen source bounds; resampling-boundary rounding is at most 4 ms per edge.

## Common preprocessing and realizations

Read the continuous EEGLAB HDF5 payload directly after verifying its shape against BIDS `channels.tsv`; preserve the source ordered labels and FCz acquisition-reference provenance. Apply the common MNDM EEG preprocessing defaults: MNE resampling 1,000 to 250 Hz, 50-Hz notch, 1–45-Hz bandpass, then average reference. No channel is interpolated or dropped in this pilot. Emit two distinct surfaces when their labels are present: all native 63 channels, average-referenced over those 63; and the named Core19 subset, selected in its declared order and average-referenced over those 19. Keep each surface's ordered labels, set hash, channel count, source reference, and offline reference set in output metadata.

## Frozen feature windows and arms

- Conventional spectral, raw MNPS 2.0 inputs, and historical MNPS 2.0 use the configured 8-second windows with 4-second steps on the continuous recording grid. Keep only windows wholly contained in one trial interval. Do not join across trial gaps.
- Fit the historical v2 recording-local transform on all eligible 8-second/4-second windows from that participant's continuous task-memory EEG recording, then apply that fixed recording-local anchor to the event-contained windows. Use the configured v2.0 nine-subcoordinate map and transform sequence. Keep raw v2 inputs and transformed v2 coordinates as separate arms. Resolve `embodied_arousal_proxy` using the existing first-finite source priority from task-matched ECG/PPG and EEG features, and save the selected source for every window.
- Full v3.1 and fast-four v3.1 use the frozen 20-second window and 20-second step, anchored at each trial's first digit sample on the inward-rounded 250-Hz grid. Emit only complete windows within a trial. Use the default 32 exact-multiset references for SC. Fast-four is the subset PCV, TP, OI, and SC; full v3.1 retains all eight standard candidates. These trial durations are expected to support 20-second windows only at load 13; report unsupported support by load rather than shortening the estimator window.
- Keep candidate-specific values and QC. Do not include MNJ in this pilot comparison.

## Pilot summaries and claim ceiling

Save every computable window and its trial/support metadata. Aggregate descriptive medians by participant × load × condition, then report within-participant memory-minus-listening differences by load. Report the intersection of rows supported by all compared arms. With six participants, this is an execution and support pilot: do not fit or interpret cohort classifiers, do not treat trials as independent participants, and make no confirmatory or biological qualification claim.

## Output root

`J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385\outputs\bench_002_pilot_v1_20261008`

For cell summaries, first take each metric's median among supported windows within each trial, then take the median of those trial medians for participant × load × condition. This gives each trial equal weight despite the 18-control/36-memory design. Preserve both window counts and supported-trial counts; do not use an unsupported trial as zero.
