# V3-MULTISCALE-FIDELITY-001 — six-participant paired-duration characterization

**Status:** frozen after the support audit completed and before inspecting any
candidate values. This is a descriptive, bounded pilot characterization. It
does not qualify a duration, establish equivalence, or authorize a full-cohort
run.

## Question

For the six ds003838 pilot participants, characterize how the existing v3.1
candidate values at 4, 8, and 12 seconds relate numerically to the existing
20-second realization on the same load-13 trial and channel surface. The
purpose is to identify gross duration sensitivity and whether a separate
multi-resolution study is worth pursuing. Estimator definitions and versions
remain unchanged.

## Frozen inputs

- Support audit: `outputs/v3_coverage_001_pilot_v1_20261008/`.
- Dataset/release and participants: exactly those recorded in that audit.
- Pairing key: subject, surface, trial ID, and candidate ID.
- Comparison population: load 13 only, because no 20-second support exists at
  loads 5 or 9.
- Compared windows start at the same inward-rounded trial start. Short windows
  are prefixes of the corresponding 20-second input; they are therefore
  nested, share samples, and are not independent replicates.
- No condition contrast, classifier, threshold search, or full-cohort run.

## Candidate comparisons

- Scalar candidates: PCV/M1, TP/M2, NIE/D1, RD/D3, OI/E1, SC/E2, and ED/E3.
- For each candidate and duration 4/8/12 seconds, pair its value with the
  same-trial 20-second value. Report per participant and surface: paired
  count, Spearman rank correlation, Lin concordance correlation coefficient,
  median signed difference (short minus 20 seconds), and median absolute
  difference. Also report the six-participant range of each participant-level
  statistic. No pooled inferential p-values or acceptance thresholds are used.
- AR/M3 is a duration-dependent vector with 1, 3, 5, or 9 adjacent two-second
  block comparisons. Do not collapse these vectors to a scalar. Compare the
  4/8/12-second vector with the matching prefix of the 20-second vector, record
  component counts and exact/near-exact agreement, and report any mismatch.
- For ED, report sample count/channel count at each duration and explicitly
  treat temporal autocorrelation and effective sample size as unresolved. A
  finite participation ratio is computability, not evidence against
  short-window covariance bias.

## Interpretation limits

- Twenty seconds is the frozen v3.1 comparator, not a validated ground truth.
- The paired windows overlap by construction, so agreement can be inflated by
  shared input. Six participants cannot establish general fidelity.
- PCV uses its window-local forward/backward alpha filter and FFT-Hilbert
  transform; edge fidelity is unassessed. Upstream filter edge safety and
  bad-interval-free provenance are unresolved for all durations.
- SC uses a duration-bound seed derived from the start/end times and 32 exact
  multiset shuffles per channel. Its cross-duration difference includes the
  declared stochastic-reference realization as well as duration.
- Duration-specific numerical agreement does not establish interchangeable
  measurement meaning. Any later recommendation for separate estimator IDs
  requires a separate scientific contract and independent validation.

## Decision use

Use the descriptive results only to decide whether to design a separately
versioned multi-resolution measurement study. Do not use this characterization
to claim scientific qualification, tune measurement definitions, compare
conditions, or launch the remaining 59 participants. Follow it with a written
BENCH-002 go/no-go recommendation that distinguishes the 4-second fast-core
coverage path from full-v3 coverage.
