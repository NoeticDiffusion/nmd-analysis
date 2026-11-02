# V3-COVERAGE-001 — six-participant estimator support audit

**Status:** frozen before extracting any 4-, 8-, or 12-second candidate values.
This is a bounded computational-support audit, not an estimator-fidelity
study, benchmark contrast, or classifier run.

## Question

Determine whether the BENCH-002 extraction script incorrectly gates the
four-dimensional fast core behind the full-v3 20-second trial window. Measure
trial-level computational support for each existing pipeline candidate at
4, 8, 12, and 20 seconds using the six already selected OpenNeuro ds003838
participants. No estimator formula, reference count, channel set, or threshold
will change.

## Frozen input and preprocessing

- Dataset: local DOI-pinned `ds003838` v1.0.6,
  `10.18112/openneuro.ds003838.v1.0.6`.
- Participants: `sub-032`, `sub-033`, `sub-034`, `sub-035`, `sub-036`,
  `sub-038`; no expansion to the remaining cohort.
- Trials: reuse the frozen, complete digit-sequence intervals from
  `[first_digit_sample, last_digit_sample + 3000)` at 1 kHz.
- Resample to 250 Hz by inward mapping: `ceil(start/4)` through
  `floor(end/4)`, end exclusive.
- Common continuous preprocessing: BIDS microvolts to volts; MNE resample,
  50-Hz notch, 1–45-Hz zero-phase FIR filter; average-reference native63 and
  Core19 separately. Preserve both surfaces and their ordered labels/hashes.
- The BIDS `events.tsv` boundary markers are recording boundaries, not bad
  intervals. Since no bad-interval annotation is supplied, report
  `bad_interval_free` as unknown; do not infer a true value.

## Window and computation rule

- Durations are exactly 4, 8, 12, and 20 seconds. For each duration, use a
  duration-equal step, anchored at the inward-rounded trial start, so windows
  within that resolution do not overlap and every sample has unique time
  support within the trial.
- A trial is structurally eligible for a duration if it contains at least one
  complete aligned window with all requested surface samples finite and inside
  the recording. Count all possible complete non-overlap windows for support
  reporting.
- For each eligible trial, run the existing eight-candidate pipeline on its
  first complete window at each duration. This gives a deterministic
  per-trial computability check without repeatedly calculating additional
  windows from the same trial. The already saved 20-second measurements are
  reused as the frozen 20-second reference and checked against the same trial
  and surface keys.
- Keep the standard candidate definitions and identities: PCV, TP, AR, NIE,
  RD, OI, SC, ED. Keep SC at 32 exact-multiset references and AR blocks at
  2 seconds. A computed candidate requires a finite value, `computed=true`,
  `valid=true`, and no candidate reason. AR must return one value per adjacent
  two-second-block pair: 1, 3, 5, and 9 values at 4, 8, 12, and 20 seconds.
- Extract the fast core (PCV, TP, OI, SC) from each window independently of
  other candidate outcomes. Do not apply a 20-second eligibility check to the
  fast-core run.

## Support and interpretation

Report separately:

1. Structural trial and unique-window counts by duration, load, condition,
   participant, and surface.
2. Actual candidate computed/valid counts among the deterministic first-window
   checks by duration and load, plus candidate failure reasons.
3. Filter/support limitations. Upstream MNE filtering uses whole-recording
   context. PCV additionally applies its 8–13-Hz forward/backward IIR and FFT
   Hilbert transform within each supplied window; its edge fidelity remains
   unknown at every duration unless independently validated. Unknown bad
   intervals remain unknown for all candidates.

Finite candidate output establishes computability only. In particular, a
short-window ED or other spatial/covariance estimate is not thereby shown to
have adequate fidelity or interchangeable meaning with its 20-second value.
No condition contrast, optimization, cohort inference, or full-cohort run is
part of this audit. Any promising shorter realization proceeds to a separate
`V3-MULTISCALE-FIDELITY-001` study with an explicit scientific and numerical
fidelity contract.

## Outputs

Write the versioned protocol, runner, trial-support table, candidate-window
status table, summary, and hashes under
`outputs/v3_coverage_001_pilot_v1_20261008/`. Preserve BENCH-002 outputs and
all source data.
