# MNPS code-fix rerun assessment

Date: 2026-10-08

## Decision

No numerical rerun of the saved BENCH-001 analyses is indicated by these four
findings. The H2 cadence guard rejects malformed grids but the saved H2R set
already uses the declared 4-second cadence. The M1 correction changes
reference provenance metadata, not measurement values. The study-common channel
floor affects whether a requested realization can emit its estimator, but the
BENCH-002 pilot used native63 and Core19 surfaces. The microvolt PSD correction
does not affect the saved QC values because this preprocessing path supplies
volts; the separate candidate-grid `1e12` conversion receives volt-valued
signals and converts V²/Hz to µV²/Hz.

The H2R payload inventory currently under the relocated J: output contains
200 files, 9,249 v3.1 four-second windows, and 9,049 within-file adjacent start
pairs. Every adjacent pair is exactly four seconds apart and every interval is
four seconds, so the current guard accepts all saved windows and the numerical
MNJ results do not change. The guard now rejects previously accepted
off-cadence inputs. The copied analysis metadata still names the original I:
run directory; this audit read the corresponding HDF5 files from the J:
project output.

The M1 metadata export should be regenerated before a downstream consumer
relies on its flat reference fields. This is an export-provenance refresh, not
a numerical experiment rerun. No study-common realization below 19 channels
was requested in the six-person BENCH-002 execution, so its values and support
are unchanged by removing the inappropriate global floor.

## New bounded BENCH-002 execution

The authorized OpenNeuro ds003838 v1.0.6 pilot completed for the frozen six
participants. It is a new execution, not a before/after comparison against an
earlier ds003838 result. It retained 972 complete trials, 5,504 event-contained
8-second windows across the native63 and Core19 surfaces, and 648 complete
trial-local v3.1 20-second windows. The latter occur only at load 13. No
classifier or cohort-level inference was run.

All output hashes in the run manifest were checked. The result report records
that all 648 v3.1 windows have `support_audit_status=incomplete` because
`bad_interval_free` is null; computed values remain unqualified. The report
also states that raw EEG band powers are V², so tiny absolute differences
reflect the input unit scale and should not be read as equivalence.

## NORMALIZATION-CONTRACT-001

The previously generated audit is intact and its output/source/helper hashes
match its manifest. In the 2,000 saved LEGACY-LOSS-003 R-arm aggregates, 1,516
are exactly zero, 1,947 are within 1e-6 of zero, and all are within 1e-5; the
maximum absolute residual is 4.91e-6. The synthetic audit verifies the
same-support median-zero invariant, local offset and positive-scale removal,
retention of within-recording differences under one shared transform, and
preservation of temporal ordering information in the window values.

These findings support the specific aggregation explanation in
`sl_025.md`; they do not establish that robust-z is generally harmful or
recommend one normalization for every scientific use.
