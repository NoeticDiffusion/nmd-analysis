# BENCH-002-FAST-GATE-FIX — validation status

## Code and saved-support checks

- The runner now extracts trial-local nonoverlapping 4 s fast-core windows in
  its own loop, before and independently of the 20 s full-v3 loop.
- The existing 20 s full-v3 measurement call and formulas were not changed.
- The runner writes to a new versioned output root and refuses to overwrite it.
- Both modified Python files passed AST parsing.
- The frozen coverage table contains 7,776 four-second fast-core candidate
  rows. Every row is computed, valid, finite, and supported; all remain
  unqualified. Each of native63 and Core19 has 324 supported first-window
  probes per candidate at each load 5, 9, and 13.
- The structural support table has 324 eligible 4 s trials per load and
  surface. The 20 s full-v3 support remains 324 trials at load 13 and zero at
  loads 5 and 9.

## Numerical parity limitation

I started a bounded re-computation against the saved EEG windows. The production
measurement function evaluates all eight candidates, including SC's exact
shuffle reference, even when only the four fast-core values are needed. After
about 18 minutes of CPU time the re-computation had not finished, so I stopped
it. No new numerical parity result is claimed from that attempt.

The prior coverage outputs were produced by the same measurement function and
contain all supported values at the same frozen sample locations. This supports
the implementation/control-flow fix, but does not replace an independent exact
input-window re-computation. The corrected six-participant runner itself has
not been run end to end.

## Focused short-trial regression check

An AST-isolated execution of the runner's actual trial-window and fast-core
helper functions used a synthetic trial shorter than 20 s. It emitted two
nonoverlapping 4 s windows wholly inside the trial and no 20 s window. Calling
the fast-core helper twice on the same synthetic 4 s input reproduced PCV, TP,
OI, and SC exactly; the values remained unqualified. This verifies the
short-trial boundary behavior and deterministic repeatability on a controlled
input, but it is not parity against the previously saved task EEG values.

## Decision

The gate fix is implemented and structural coverage is confirmed. Treat exact
4 s and 20 s numeric parity as pending; do not interpret this validation as
short-window fidelity, measurement qualification, or authorization for a
full-cohort run.
