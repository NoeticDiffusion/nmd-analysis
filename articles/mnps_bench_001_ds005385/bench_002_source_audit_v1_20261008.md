# BENCH-002-SOURCE-AUDIT

Date: 2026-10-08  
Status: metadata/design selection recorded before any ds003838 MNPS feature
outputs were computed. Source literature findings are already public and were
consulted; this is an exploratory external benchmark selection, not an
untouched confirmatory test.

## Decision

Select **OpenNeuro ds003838 v1.0.6** for the next bounded external
MNPS-BENCH-002 comparison. Primary contrast: within-participant **digit-span
serial-recall instruction vs passive listening**, matched within each of the
three digit loads (5, 9, 13). Both conditions use auditory digit sequences;
exact sequence identity is not assumed and remains to be verified from the
stimulus/trial metadata. Use event-anchored encoding and the common
post-sequence retention interval; omit the later spoken-recall interval from
the primary comparison so vocal motor activity is not part of the positive
condition window. The metadata preflight must verify the mapping from final
digit markers to the end of the audio and retention interval before freezing
sample boundaries. Keep block, trial, load and event boundaries in the saved
support. The unit is participant × load × condition; all model arms use the
same rows and participant-grouped folds.

The selected source is the version-pinned [OpenNeuro ds003838 v1.0.6 release](https://openneuro.org/datasets/ds003838/versions/1.0.6),
identified by DOI `10.18112/openneuro.ds003838.v1.0.6`. Its participant table
marks 65 as `EEG_excluded=no`. These 65 form the outcome-blind screening
roster in `bench_002_outcome_blind_inclusion_manifest.csv`. They remain
screening-eligible if paired task/event metadata and the requested channel
realization are available. **There is no global 60-second gate in this source
selection.** Freeze each estimator's own support/computability contract in the
benchmark protocol; preserve any other computable values if one realization
is unsupported. The paired classifier may use only rows computable for every
compared arm, with that analysis-specific intersection reported.

### Preliminary BIDS metadata check (one participant only)

The current GitHub mirror's `sub-032_task-memory_eeg.json` describes a
continuous 7,395.32-second mixed-condition recording at 1 kHz, with 63 EEG
channels, FCz as the recorded online reference and Fpz as ground. The separate
`sub-032_task-rest_eeg.json` reports 227.081 seconds (about 3 min 47 s). The
data descriptor describes a nominal four-minute eyes-closed resting recording
alongside the digit-span task; however, the current `task-rest` sidecar repeats
`TaskName: mixed` and the digit-span task description. Treat that as a metadata
inconsistency to resolve against the DOI-pinned release and recording/event
files, including the duration discrepancy, not as evidence that the rest file
contains passive listening. The paper describes a 64-channel acquisition
system with FCz reference, so the difference from 63 EEG channels
in the sample sidecars appears to be recorded EEG-channel count versus physical
system count; the actual ordered labels and consistency across the 65-person
roster remain unverified. The matching memory events dictionary has per-digit
markers for passive control (`x500…`) and memory (`x600…`) at each load; the
memory codes also mark recall correctness. These markers support
condition/load parsing but do not by themselves establish exact digit-sequence
identity. This is a sample-level check against the moving GitHub mirror, not
the version-pinned, population-wide metadata preflight. The 7,395-second
mixed-condition task file does not establish 120–180 seconds of uninterrupted
same-condition dynamics and does not change the primary MNJ exclusion.

Primary comparison arms: conventional spectral features, raw MNPS 2.0 inputs,
historical MNPS 2.0, full MNPS v3.1, and the frozen fast-four v3.1 realization.
Preserve Core19 and any native-channel realization as separately identified
outputs if both can be computed; do not substitute one for the other. Report
paired participant AUC differences, participant-level within-load changes,
support/QC, and a conventional reference. No model settings or measurements
are tuned to these results.

**Do not include MNJ in the primary BENCH-002 hypothesis.** The task consists
of short, event-defined trials with intervening events and condition blocks;
the metadata establishes ample cumulative task support but not 120–180
seconds of uninterrupted, same-condition dynamics. Do not join windows across
trial gaps to manufacture a continuous trajectory. If a separate trial-local
MNJ design is pursued, freeze it as a separate analysis after event-duration
and support preflight.

## Why ds003838 ranks first

The dataset README reports raw 64-channel EEG at 1 kHz, a comparatively useful EEG roster
(65 after the source EEG-exclusion flag), and an auditory control: participants
either memorize or passively hear digit sequences at the same three list
lengths. The [primary task paper](https://www.nature.com/articles/s41597-022-01414-2)
reports 54 passive-listening and 108 memory trials, with all three loads
represented. This gives a more focused active-task comparison and a
larger independent sample than the other metadata-audited active-task
candidates. The official participant table is the only basis for the 65-person
screening roster.

There are material limits. Each block presents three control trials, then 12
memory trials, then three more control trials; condition order is therefore
not counterbalanced. Memory trials also end in spoken serial recall. The
primary event-window rule excludes retrieval speech, but it cannot remove
order, fatigue, expectation or instruction differences. The published
dataset paper reports EEG condition findings, and that literature was read in
this source audit. Thus selection is blind to **our MNPS feature outputs** but
not blind to all published neural outcomes. Treat the benchmark as external
and exploratory; do not call it an independent confirmatory validation or a
prospective biological success.

## Ranked metadata audit

| Rank | Dataset | Suitability | Main limitation / disposition |
|---:|---|---|---|
| 1 | [**ds003838 v1.0.6**](https://openneuro.org/datasets/ds003838/versions/1.0.6) | 65 EEG-eligible participants; raw 64-channel, 1 kHz EEG; auditory digit-span task in passive and memory conditions; matched 5/9/13 loads. Best current sample/design balance for v3.1 vs v2 task-level measurement comparison. | Fixed control→memory→control sequence; retrieval speech in memory condition; cumulative event support is not a continuous MNJ series. Exact sequence identity still requires metadata verification. Selected with exploratory claim ceiling. |
| 2 | [**ds005048**](https://github.com/OpenNeuroDatasets/ds005048) | 35 participant directories; 19 monopolar 10–20 channels, 250 Hz; repeated 40 s 40-Hz stimulation bouts separated by 20 s silence. Potential repeated-block sensory perturbation benchmark. | Small cohort; elderly dementia-related population; alternation means no uninterrupted 120 s condition; short/long sessions use different online references before average rereferencing. Long-session count and exact per-participant support still need metadata preflight. |
| 3 | [**ds005403**](https://openneuro.org/datasets/ds005403/versions/1.0.1) | 32 participants; active delayed-auditory-feedback speech task; 62 EEG channels in [NEMAR's 10–10 metadata](https://www.nemar.org/dataset/on005403); events include per-trial delay. Scientifically meaningful perturbation and likely ample total duration. | 118.45 GB in OpenNeuro metadata / about 136 GB on NEMAR; 10 kHz recordings include EEG, EGG and audio; Core19 mapping, delay-level balance and uninterrupted condition support were not verified. High ingestion cost and vocal/multimodal contamination. Conditional candidate only. |
| 4 | [**ds004148**](https://github.com/OpenNeuroDatasets/ds004148) | 60 participants, 64 electrodes, 500 Hz, three sessions, rest plus subtraction/music/memory states; strong repeated-state and reliability design ([data descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC9470564/)). | Already used for NMD v3 measurement feasibility in this project; not an unused, outcome-blind benchmark. Retrospective challenge only. |
| 5 | [**ds005514 (HBN Release 9)**](https://openneuro.org/datasets/ds005514/versions/1.0.1) | 295 participants, multiple EEG tasks and rest; ample nominal sample size. | Task availability is uneven; ages span childhood/adolescence; no single stable within-person contrast is selected without task-specific coverage analysis. High screening and harmonization cost. |
| 6 | [**ds004010**](https://github.com/OpenNeuroDatasets/ds004010) | 24 healthy participants in a multisensory target-detection task; simultaneous audio-visual noise and attention conditions. | Too few independent participants for the preferred primary benchmark; event and duration support not preflighted. |
| 7 | [**ds004117**](https://github.com/OpenNeuroDatasets/ds004117) | 23 healthy participants; 71-channel, 250 Hz modified Sternberg task with multiple blocks and event annotations. | Low independent N; trial-level design; published prior task results. Keep as a methods pilot only. |

## Outcome-blind screening and inclusion rule

The attached manifest freezes the 65 source-table rows with `EEG_excluded=no`
as screening-eligible participants. This is **not yet the final technical
inclusion set**. Before any feature extraction, run a metadata-only BIDS
preflight to confirm paired task/event files, exact channel labels/reference,
and the three condition/load combinations. Freeze any exclusions from that
preflight in a versioned amendment before computing MNPS values. Do not impose
a global duration threshold: record support by estimator and realization,
emit each computable measurement, and use a named common-support intersection
only for the paired model comparison. The initial planned N is 65; final N may
be lower for predeclared metadata/support reasons only.

The intended event window is first stimulus onset through the end of the
common 3-second post-sequence retention interval; use the same load for memory
and control, and exclude spoken response and subsequent ITI. Freeze exact
sample boundaries only after the metadata-only preflight confirms trigger,
audio-offset and trial-boundary interpretation. Do not treat trials, windows,
or channels as independent participants. Split and bootstrap at participant
level. Report per-load results and a prespecified participant-level pooled
summary; do not pool the three loads as if they were exchangeable samples.

## Computational cost estimate

This source audit transferred no EEG data and ran no signal processing. The
[OpenNeuro/NEMAR record](https://nemar.org/dataset/on003838) reports a 253 GB
total dataset including peripheral signals;
the EEG-only byte total and per-task duration were not verified here. Budget
one metadata-only preflight with negligible signal compute, then a bounded
six-participant pilot (both conditions, all loads) to measure ingest, resampling,
channel realization and feature runtime. If runtime scales approximately
linearly, estimate the 65-person feature run as `pilot_runtime × 65/6`, then
add the five-arm nested-CV cost from the pilot's actual fit timing. Do not
download the full multimodal dataset or start a cohort run until this pilot
resolves size, event and support uncertainties. No whole-cohort EEG run is
authorized by this source-audit step.

## Sources

- [OpenNeuro ds003838 v1.0.6 release and pinned participant table](https://openneuro.org/datasets/ds003838/versions/1.0.6)
- [OpenNeuro ds003838 dataset README and file tree](https://github.com/OpenNeuroDatasets/ds003838)
- [Provisional sub-032 task-memory EEG sidecar](https://github.com/OpenNeuroDatasets/ds003838/blob/main/sub-032/eeg/sub-032_task-memory_eeg.json)
- [Provisional sub-032 task-rest EEG sidecar](https://github.com/OpenNeuroDatasets/ds003838/blob/main/sub-032/eeg/sub-032_task-rest_eeg.json)
- [Provisional sub-032 task-memory event-code dictionary](https://github.com/OpenNeuroDatasets/ds003838/blob/main/sub-032/eeg/sub-032_task-memory_events.json)
- [Primary ds003838 task/methods paper](https://www.nature.com/articles/s41597-022-01414-2)
- [OpenNeuro ds005048 dataset README](https://github.com/OpenNeuroDatasets/ds005048)
- [OpenNeuro ds005403 v1.0.1 metadata](https://openneuro.org/datasets/ds005403/versions/1.0.1)
- [NEMAR ds005403 metadata and data organization](https://www.nemar.org/dataset/on005403)
- [OpenNeuro ds004148 dataset README](https://github.com/OpenNeuroDatasets/ds004148)
- [ds004148 data descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC9470564/)
- [OpenNeuro ds005514 Release 9 metadata](https://openneuro.org/datasets/ds005514/versions/1.0.1)
- [OpenNeuro ds004010 dataset README](https://github.com/OpenNeuroDatasets/ds004010)
- [OpenNeuro ds004117 dataset README](https://github.com/OpenNeuroDatasets/ds004117)
