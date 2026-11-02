# M3 / CHART bounded qualification study — 2026-09-06

Status: prospective scope, written before benchmark outcome inspection.
Owner: nmd-analysis. Coordinator: Astra; reused Luna agents implement, test,
and independently review. This is an analysis experiment, not an ingest change.

## Question and fixed boundary

How accurately does the existing crossfit_local_chart_b candidate recover a
known discrete chart conditional velocity, and which changes under alternative
coordinates arise from the estimator, the metric, or lost information?

Canonical MNPS [m,d,e], 9D, J_hat, ingest increment covariance, missingness,
validity gates and existing historical outputs remain unchanged. No Itô drift,
biological qualification, M4 dataset gate, M5 utility, C2 residualization,
committor, FAR or production W_Q change is authorized by this experiment.

## M3 experiment contract

- Truth: stable linear Gaussian discrete dynamics with explicit A, Q and dt;
  target b_dt(x)=(A-I)x/dt. Q is a simulation innovation covariance only.
- Compare oracle, existing cross-fit local mean and local affine candidates,
  deliberately contaminated same-sample local mean, shuffled and time-displaced
  controls. Unsafe comparators are explicitly benchmark-only, never an option
  that disables the production cross-fit contract.
- Keep the same observed evaluation increment covariance for all comparisons;
  preserve its hash and distinguish it from oracle conditional Q/dt.
- A_bD follows ingest: b.T a b / ((b.T b) trace(a) + epsilon), unavailable
  for zero b. It is a chart-space, scale-sensitive operational quantity.
- Report velocity recovery error, alignment bias, rank correlation, seed
  variability, support/refusal counts and sensitivity to dt and embargo.
  A bad negative control is a diagnostic result, not an implementation failure
  to be hidden or a reason to tune parameters.
- Train/evaluation indices and full temporal support are disjoint; explicit
  embargo is audited. Evaluation target increments never enter a cross-fit fit.
- Agents must serialize and freeze their numeric default specification before
  the coordinator's first primary outcome run. Small tests may check algebra
  and contract handling. No post-outcome retuning of the primary specification.
- There is no preregistered empirical scientific PASS cutoff. Report observed
  recovery and limitations; numerical identity tolerances only test identities.

## CHART experiment contract

- Orthogonal maps and isotropic scaling: check correctly transformed vectors
  and covariance, and equivariance of the existing estimators on non-tied data.
- Anisotropic scaling: oracle transform identities still apply; Euclidean
  neighbour choices, alignment and effective dimension need not be invariant.
- A 3D-to-2D projection is a separate information-loss experiment. Construct two
  full states with identical projected present and different projected expected
  future because of a hidden coordinate. Do not label this a coordinate failure.
- No alternate chart replaces the canonical production chart.

## Failure and reference checks

Tests cover gaps/irregular dt, nonfinite input, insufficient support/rank,
overlap including shared endpoints, explicit raw support and embargo, and
evaluation-target independence. Undefined statistics remain null with reason.

Read only the existing ds005555 sub-99 full-night HDF5 for a bounded empirical
support smoke check (1068 30-second epochs according to the existing audit).
Hash the source; carry validity/qualification metadata. This is not synthetic
truth, biological recovery, a sleep contrast or a whole-cohort analysis.
Use explicit 30-second epoch support and a temporally separated split. Report
refusals and unavailable outputs without replacing them with zeros. Do not use
the existing invalid full-night W_Q in any scientific comparison.

## Reproducibility and integration

J: had zero free bytes at task start. Work proceeds in an isolated H: copy of
the current analysis package/tests. Baseline drift.py is preserved. Final
integration must verify original-file hashes, preserve unrelated edits and
report any disk-space block honestly. Results/temp files remain on H:.

Record runtime versions, commands, seeds, numeric specification hash, code
hashes, source hash, independent review and coordinator verdict. Tests run
with -B and pytest cache disabled. No full ingest or cohort execution.
