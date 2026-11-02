# V3-MULTISCALE-FIDELITY-002 — bounded estimator-fidelity protocol

**Status:** design frozen before any new V002 outcomes are computed. This is a
post-pilot method amendment, not a prospective preregistration: V001's
descriptive duration comparisons and several BENCH-002 outcomes have already
been inspected.

## Questions

1. Do candidate estimators recover controlled quantities on synthetic signals
   with known phase, autocorrelation, block activity, or covariance structure?
2. How sensitive are candidate values to finite duration, window-local filter
   edges, montage, and reference on continuous recordings, without using task
   labels or condition contrasts?
3. Do stationary surrogate signals produce excess apparent differences when
   random labels are assigned?

The experimental unit is the participant for continuous EEG summaries and the
independent generated signal seed for synthetic results. Windows within a
recording are repeated measurements, not independent participants.

## Frozen inputs and support

- Dataset: OpenNeuro ds003838 v1.0.6; the same six frozen V001 participants.
- Realizations: native63 and the fixed Core19 channel set, average referenced
  separately. They remain separate measurement outputs.
- Durations: 4, 8, 12, and 20 seconds; windows use the 250 Hz sample grid and
  never cross recording boundaries. Continuous windows are not selected by
  trial condition or digit load.
- V001 outputs are descriptive comparators only. Twenty seconds is not treated
  as truth, and no comparison to task labels, classifier, or full-cohort run is
  permitted in this protocol.
- The source still has no bad-interval-free evidence. Signal indicators are
  reported as QC; they do not silently reject or qualify a measurement.

## Synthetic truth panels

Use fixed seed list 20261009 plus replicate index, 100 independent seeds per
panel, 19 channels, and 250 Hz. Run all candidate durations. Preserve the
generating parameters and the per-seed observations.

1. **TP / AR(1):** independent unit-variance AR(1) channels at rho 0.2 and
   0.8. TP truth is 1-rho. This panel tests temporal-persistence bias.
2. **PCV / phase order:** 19 equal-amplitude 10 Hz channels with known,
   time-varying phase offsets. Apply the frozen average-reference operation to
   the synthetic channels. PCV truth is the temporal standard deviation of the
   population phase-order parameter from the known referenced generator, using
   its full-context analytic phase rather than a short-window filter.
3. **AR / block activity:** exact 10 Hz carriers with amplitudes fixed within
   contiguous two-second blocks. AR truth is 1-Pearson(rms_block_i,
   rms_block_i+1) computed from the known block amplitude vectors.
4. **ED / covariance:** Gaussian channels generated from a frozen covariance
   eigenspectrum. ED truth is the population participation ratio
   (sum(lambda))^2/sum(lambda^2).
5. **NIE, RD, OI, SC:** preserve each estimator's declared operational formula.
   Record generated-population references where analytically defined; where a
   finite-window target is not available, report bias against the long
   synthetic realization as a comparator and label it accordingly.

## Predeclared screening thresholds

These are engineering/method screening thresholds for this bounded study, not
universal qualification rules.

- TP absolute median bias against 1-rho: at most 0.10 at 4 s and 0.05 at
  8/12/20 s, for each rho panel.
- PCV absolute median bias against generator-phase truth: at most 0.05 at each
  duration; for the additional local-window versus full-context comparison,
  median absolute difference at most 0.05 and 95th percentile at most 0.10.
- AR block-change: maximum absolute component error at most 1e-12 for each
  supported pair; unsupported components remain missing.
- ED relative median bias against the population participation ratio: at most
  30% at 4 s and 20% at 8/12/20 s. Report replicate distributions and do not
  infer a passed finite-sample estimator from a finite output alone.
- Stationary surrogate false-positive fraction: generate 200 independent null
  datasets, each with 40 stationary windows (20 per randomly assigned label).
  Compute all four fast-core candidates, run a two-sided permutation test for
  each candidate in each dataset, and apply Holm within each four-test family.
  Report raw per-candidate and familywise rejection rates. A familywise rate
  above 0.10 fails the calibration screen.
- Empirical duration, montage, reference, and split-half results are reported
  with participant-level distributions. No empirical equivalence threshold is
  applied because the six participants and non-identical realizations cannot
  establish universal comparability.

## Continuous EEG comparisons

- Compare same-start nested durations at every eligible continuous position,
  then compare equal-duration windows at early, middle, and late recording
  positions. This separates duration changes from a single trial-start-only
  sample, but does not eliminate time-on-task physiology.
- For PCV only, compare the local-window alpha filter/Hilbert result with a
  full-recording-context alpha phase-order series evaluated on the identical
  sample interval. Preserve the recording-edge exclusion and report it.
- Report per-candidate duration distributions, split-half/repeat-window
  stability, native63/Core19 sensitivity, and the change under average versus
  linked-mastoid reference where the recorded labels permit it.
- Report signal-screening QC (flatness, peak-to-peak, robust amplitude, and
  high-frequency power) separately from source annotations and from filter
  support. Do not turn any one indicator into an unreviewed clean/not-clean
  gate.

## Multiplicity and interpretation

- No exposed task contrast or classifier is in scope.
- Holm correction is used only for the four fast-core synthetic surrogate
  candidate tests. Other comparisons are descriptive and reported at the
  participant or independent-seed level.
- Threshold failures identify unresolved estimator/duration combinations;
  they do not motivate tuning formulas or gates on these outcomes.
- Passing screens does not qualify a measurement for biological use or show
  that different durations, references, or channel sets are interchangeable.
- No full-cohort execution is authorized by this protocol.

## Required outputs

Save the frozen protocol hash, input hashes, code hashes, every generated seed
and truth value, per-window measurements, QC indicators, participant-level
summaries, surrogate test statistics, threshold decisions, and explicit
limitations in a new versioned output directory. Never overwrite V001.
