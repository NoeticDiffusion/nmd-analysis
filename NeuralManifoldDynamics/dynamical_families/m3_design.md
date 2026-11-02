# DF-DRIFT-C1-M3 analysis design and bounded benchmark

The analysis-owned `crossfit_local_chart_b` estimator remains a candidate,
marked `candidate_not_qualified` and `no_biological_claim`. It estimates chart
conditional velocity from disjoint training increments and does not identify
an Itô drift, residualize ingest `a_hat`, or grant a scientific M3 PASS.

## Candidate contract

Each increment is `x[i] -> x[i+1]`. Local mean and local affine regression
use only supplied training increments to predict at evaluation source states.
Timestamps must be regular and finite. Raw-window supports must cover the
increment endpoints. Training and evaluation intervals must have a gap
strictly greater than the requested embargo; touching endpoints are refused
even when embargo is zero. Insufficient support/rank and nonfinite inputs
are refused rather than dropped or converted to zeros.

The 2026-09-06 change also rejects arithmetic overflow/nonfinite time
differences, velocities, distances, reductions and fits. Previously, extreme
finite inputs could produce a NaN candidate. The underlying estimation
algorithm and ordinary outputs are unchanged. The full-night reference
comparison found four 100-prediction arrays bitwise identical before/after.

## Implemented M3 / CHART experiment

`m3_benchmark.py` runs the frozen 3D stable linear-Gaussian experiment with
oracle, cross-fit, contaminated same-sample, shuffled-training and circularly
time-displaced controls. The discrete target is `(A_k-I)x/dt`, where effective
transitions and innovation covariances follow exact subsampling of the same
seeded base path. Fixed evaluation-only local neighbourhoods supply raw
increment covariance/dt and local mean b for operational alignment. Oracle
innovation covariance remains distinct from the measured tensor.

The result reports normalized velocity error, alignment bias/rank, variability,
support/refusal information and dt/embargo sensitivity. This is a restricted
synthetic diagnostic, not full ingest PSD-floor/float32/serialization parity.
Reported between-scenario SD and within-evaluation prediction variance are
not estimator variance at a common held-out state. Three seeds generate the
27 correlated scenario cells; they are not 27 independent replications.

`chart_benchmark.py` checks mixed orthogonal and isotropic transformation
equivariance, independent covariance-transform identities, expected anisotropic
metric/neighbour sensitivity and a separate information-loss projection
counterexample. Its scalar alignment is explicitly unregularized diagnostic
geometry, not production epsilon-regularized C1 A_bD.

`m3_reference_smoke.py` reads the explicitly chosen ds005555 full-night file
with a frozen split and raw 30-second epoch support. It validates schema,
axis order, dimensions and time support, retains source statuses, hashes the
source before/after, and never converts a computed candidate into empirical
qualification. It uses explicit coordinate paths rather than silently
switching to the file's declared subject-anchored primary layer.

The prospective protocol is `m3_chart_protocol_20260906.md`. Results and the
coordinator report are at:

`H:/SourceRepo2/NeuralManifoldDynamics/project/astra/m3_chart_20260906/report.md`

## Reproduction

Run from `J:/repos/nmd-analysis/nmd-analysis` with the validated Python runtime:

```powershell
$m3Python = 'H:\SourceRepo2\NeuralManifoldDynamics\.venv\Scripts\python.exe'
$m3Output = 'H:\SourceRepo2\NeuralManifoldDynamics\project\astra\m3_chart_new_run'
& $m3Python -B -m nmd_analysis.dynamical_families.m3_benchmark --output "$m3Output\m3.json"
& $m3Python -B -m nmd_analysis.dynamical_families.chart_benchmark --output "$m3Output\chart.json"
& $m3Python -B -m pytest tests -q -p no:cacheprovider --basetemp "$m3Output\pytest"
```

Use a fresh output root to retain previous results. The reference smoke takes
an explicit positional HDF5 path and `--output`. Primary frozen specifications:

- M3: `0e7cec90da5e31fab52f38af3d6b5bce4aa321326e89a9d7704f727d76540be6`.
- CHART: `36adcfb98985f5c3b3a427824bf3d02251dcd2dc9f7166f16bf1aa3ff773016d`.

Custom benchmark parameters are labelled `custom_test_spec`. A shift must be
an integer strictly between zero and the evaluation set size. The initial
M3 run had an implementation-invalid time-shift control; it and its exact
source are retained alongside the corrected run. The correction preserved
the numeric specification and all 162 non-time-shift result rows.

## Current gate

Implementation and bounded affine CHART checks: PASS. M3 scientific
qualification: PARTIAL PASS. The candidates recover information in the
tested synthetic 3D process, with estimator-dependent bias/error tradeoffs.
The reference establishes support compatibility only. It is not a 9D recovery
experiment, empirical drift identification, biological validation or evidence
that the chart is a sufficient state representation.

Next: prospectively fixed nonlinear/partially observed/noisy truth systems,
held-out states/seeds, pointwise uncertainty and 9D recovery. M4 dataset
selection and M5 downstream utility remain separate scientific gates.
