# V3-TEMPORAL-FIDELITY-003 — controlled transient screen

**Status:** frozen before V003 outcomes are generated. This is a post-pilot
method amendment, not a prospective study: BENCH-002 outcomes and V002
stationary/continuous results have already been inspected.

## Question and scope

Can the frozen temporal-persistence estimator (TP/M2) recover a known temporary
change in lag-one dependence from short windows, while the full 20-second
window reports the expected diluted mixture? This is a controlled synthetic
screen. It does not establish that short EEG measurements capture meaningful
physiology or task events.

TP is the only transient coordinate included because its generator target is
specified directly by the AR(1) process. No transient truth will be assigned to
PCV, AR, OI, SC, or the other coordinates in this experiment.

## Stationary reference stage

Reuse the already completed V002 stationary TP screens without modification:
19 independent channels, 250 Hz, AR(1) rho 0.2 and 0.8, 100 independent seeds
per rho, and 4/8/12/20-second windows. Their frozen target is `1-rho`. The V002
summary CSV is copied into the V003 output as a small reference table and its
source hash is recorded. This stage is not recomputed or described as a new
V003 result.

## Controlled time-varying generator

- 200 independent seeds; 19 channels; 250 Hz; 20 seconds per signal.
- Regime A: `[0, 8)` and `[12, 20)` seconds, stationary unit-variance AR(1),
  rho 0.2, so the target TP is 0.8.
- Transient regime B: `[8, 12)` seconds, stationary unit-variance AR(1),
  rho 0.8, so the target TP is 0.2.
- The three regimes are independently initialized from their unit-variance
  stationary distributions. Adjacent samples across a regime boundary are
  independent, with expected lag product zero. This deliberately controlled
  reset represents an abrupt synthetic reconfiguration, not a physiological
  switching model.
- Use every 4-second-aligned window of duration 4, 8, 12, or 20 seconds that
  fits inside the signal. There are 13 windows per seed and 2,600 total
  measurements.
- Compute TP with the existing `compute_pipeline_m2_temporal_measurement`
  implementation. Do not change its formula or preprocessing.

For each window of `N` samples, define the independent generator target as

`TP_truth = 1 - sum_k((n_k - 1) * rho_k) / (N - 1)`,

where `n_k` is the number of samples from regime `k` inside that window, and
terms with `n_k < 2` contribute zero. Cross-regime adjacent pairs contribute
zero expected lag product. For mixed windows this is the generator's
uncentered population lag-product target; the production estimator centers
finite samples, so mixed-window bias is reported descriptively.

## Frozen engineering screens

The independent unit is the signal seed; windows are repeated observations.

- Median absolute bias across signal seeds for pure-regime 4-second background
  windows (A, truth 0.8): at most 0.10.
- Median absolute bias across signal seeds for the 4-second transient window
  (B, truth 0.2): at most 0.10.
- Median 4-second transient-minus-background TP difference across seeds: at
  most -0.40, in the expected negative direction.
- Median absolute bias across seeds for the 20-second mixed window (target from
  the formula above, approximately 0.680): at most 0.05.
- All other 8/12-second and mixed-window distributions are reported without a
  pass/fail threshold.

These are bounded engineering screens, not qualification or claims about
biological recordings. No task labels, classifiers, empirical condition
contrasts, formula tuning, or full-cohort data are used.

## Outputs and limits

Save the protocol and estimator hashes, V002 stationary reference hash,
generator seed and signal hashes, per-window truths and values, seed-level
screens, summary decisions, environment, and output hashes in the new
versioned V003 output directory. Measurements remain synthetic and
unqualified.
