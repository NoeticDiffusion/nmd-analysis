# Analysis plan: new dynamical families (2026-09-10)

This is an analysis plan for the already inspected development artifacts. It is
not a preregistration and does not turn the current two-recording comparison
into a population study. MNPS remains the observation chart; family outputs
retain their native grain, support, validity, and claim ceilings.

## Contract inventory

The local-Jacobian implementation computes the Euclidean-coordinate metrics
`spectral_abscissa` (alpha), `numerical_abscissa` (omega),
`reactivity_gap`, regime flags, and related norms per window under
`mndm.jacobian_metrics.v1`. Finite-time response (`mndm.finite_time_response.v1`)
is an optional model-derived family. These are window-native measurements with
recording summaries; they do not license empirical NDT alpha/omega or
perturbational claims.

The diffusion family is `mndm.diffusion_geometry.v1`. It estimates local
chart-space raw increment covariance from state-space neighborhoods and reports
`a_hat`, `D_total`, `d_diff`, `c_diff`, support and validity. The inspected
contract uses raw increment covariance, approximately regular time steps, and a
recording parent. With no independent chart drift, `A_bD` and `R_b_over_a` are
`not_testable`, never zero. The neighborhood is global state geometry, not a
stage-conditioned object.

DF-DRIFT-C1 is an analysis-owned extension. Ingest may consume an externally
qualified chart-space velocity for alignment only; it does not estimate `b`.
The handoff permits a future `crossfit_local_chart_b` candidate, and reuses the existing M3 benchmark evidence. Any new candidate run preserves
disjoint train/evaluation increments, explicit support, embargo audit and controls. `mnps_xdot`, Jacobian intercepts, same-sample local
increment means, and residualized C2 covariance are excluded.

## Three questions and endpoints

### Q1 â€” What is the reproducible local-Jacobian dynamical profile?

Primary endpoints are per-window `spectral_abscissa`, `numerical_abscissa`,
`reactivity_gap`, validity and support counts. Finite-time-response peak values are
a secondary recording-level endpoint from its `recording_rows` contract, not a
window endpoint. Summaries are computed separately for 3D and 9D where those
rows exist, with window denominators and recording-level summaries. The unit for replication is the
recording/participant, never the window count. Contrasts are fixed before
reading directions: same-coordinate, same-family summaries between the two
recordings, with no observed-direction selection. These are descriptive
coordinate-metric quantities, not NDT stability or consciousness endpoints.
They may be summarized descriptively by the recorded center-window label under
the frozen recording-parent stage policy; this is label association, not a
stage-intrinsic estimator or refit. The abscissae are Euclidean-coordinate
metrics and are not invariant under arbitrary reparameterization, so 3D and 9D
values remain separate.

### Q2 â€” Does raw chart increment geometry reproduce across recordings?

Primary endpoints are diffusion `D_total`, `d_diff`, `c_diff`, valid-row and
support counts, and failure/status metadata for the canonical 3D artifact and
recording. The analysis keeps the producer neighborhood, metric, timestep rule,
PSD floor, and masks fixed. Existing query-row values may be summarized by
their center-window label as a descriptive recording-parent association under
the frozen stage policy; the neighbor covariance remains global and is not
relabelled as stage-intrinsic diffusion. `A_bD` and `R_b_over_a` remain
secondary and are unavailable when independent drift is absent. No diffusion
family is refit to stages or used for participant pooling. The current 3D and
9D artifacts can have different row grids; a missing 9D row is not silently
treated as missing data in the 3D analysis.

### Q3 â€” Is an independently estimated chart velocity feasible for C1?

The existing accepted M3 synthetic benchmarks and reference smoke establish
engineering readiness for the candidate workflow; they are not scientific
qualification. A scoped candidate experiment may reuse that workflow on the
selected H5 support contract, with truth-known/comparator controls retained.
Required measures are alignment recovery, `A_bD` bias, rank recovery, variance,
support refusal, dt sensitivity, train/evaluation disjointness, and embargo
violations. Any empirical C1 quantity remains an externally supplied alignment
field, not an identified Ito drift; no biological contrast is planned in this
step.

## Levels of analysis

**Primary runnable now:** Q1 and Q2 using existing serialized family outputs,
with exact provenance, native grain, finite/missing/status counts, and fixed
cross-recording summaries. A bounded two-recording report can answer
reproducibility questions without cohort inference.

The current selected H5 inventory supports this bounded work: the independent
recording has 915 epoch rows, 913 serialized 3D rows and 856 serialized 9D
rows; its diffusion series has 915 rows. The stored diffusion contract records
raw increment covariance with nominal 30-second dt and `drift_mode=not_supplied`;
`A_bD` and `R_b_over_a` are explicitly not testable. These are availability
facts for planning, not a stage contrast or a drift result. The missing 3D/9D
rows must remain missing and must not be length-coerced or replaced.

**Secondary candidate:** Q3 reuses the accepted M3 benchmark and
`m3_reference_smoke.py` as a bounded support/candidate check if its explicit
coordinate paths and 30-second support contract match the selected artifact.
This is candidate readiness, not an empirical drift result or qualification.

**Excluded or method-limited:** stage-intrinsic Jacobian/diffusion/drift refits or claims,
NDT SDE `b` or `a(x)`, C2 residualized covariance, Q/W_Q as process noise or
stage measures, committor/FAR contrasts, p-values, pooled participant effects,
and any consciousness or clinical interpretation. The `m/e` fallback and mixed
feature provenance are scoped limitations of feature interpretation, not a
reason to block a descriptive family inventory; they must remain visible.

## Bounded deliverables and controls

1. Produce one machine-readable family inventory per recording containing schema,
   source H5 hash, family status/validity/grain, coordinate layer, support,
   and code/config hashes.
2. Produce fixed-order tables for the specified E1 3D/9D and E2 3D endpoints only, with
   unavailable values preserved as null/NaN and no stage relabeling.
3. Reuse accepted M3/CHART evidence; run relevant regression only when implementation
   changes justify it. A new candidate overlay must serialize train/evaluation index hashes, actual indices, endpoint overlap,
   window-support embargo, dt policy, and estimator provenance.
4. Have an independent reviewer inspect code, masks, native grain, and fresh
   artifacts before interpreting any two-recording direction.

The safe outcome is a reproducible recording-level family comparison. It does
not establish a universal axis, stage mechanism, Ito drift, or population
effect.

For sleep-label reporting, each recording is summarized separately first under
the fixed parent reference, then the fixed N2-minus-Wake within-recording
descriptive contrast is reported with its denominators and support status.
Standardized coordinates are not assumed to have directly comparable absolute
magnitudes across participants; cross-participant interpretation is limited to
the prespecified descriptive direction/replication question.

## Frozen first execution scope

The operational specification is `analysis_plan_new_families_20260910.json`.
First execute E1/E2, using existing artifacts only. E1 has alpha, omega and the
derived gap, separately in3D/9D; E2 has D_total, d_diff and c_diff in3D only.
Report every known stage with n, median and quartiles, plus the fixed N2-minus-Wake
contrast for every endpoint. Aliases are not additional measures. Code8 and other
unknown labels remain separate. Qualification counts stay null.

J centers are explicit epoch-array positions, not an assumed common915/1068-row
grid. Map each through stored epoch IDs, time and labels and retain nonconsecutive
center gaps, especially in sub-1 9D. A center label does not identify every training
neighbor's stage. FTR is deferred from this first deliverable: its native
recording-horizon object and irregular-horizon support require their own display.

Deliver two figure groups (abscissa/reactivity and diffusion geometry), complete
endpoint tables and one reviewed manuscript result update. E3 is a separate
candidate experiment using existing benchmark/estimator code, not a prerequisite
for these figures. Do not restart ingest or the m/e investigation to execute
E1/E2. Source differences remain explicit limitations on interpretation.
