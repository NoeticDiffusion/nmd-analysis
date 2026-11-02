# Dynamical families — analysis handoff

Status: **RATIFIED** after Science Lead amendments (2026-09-03).

Source of truth (ingest):
`H:/SourceRepo2/NeuralManifoldDynamics/project/mnps_v3/df_drift_c1_analysis_handoff.md`

Authority: ingest `sl_mnps3_005.md` (overrides `sl_mnps3_004.md` next gate).
M1–M2 C1 consume-external-`b` is **PASS / RATIFIED** and **frozen in ingest**.
M3 is **not authorized in ingest**. This repo owns identification of `b`.
Next DF-DRIFT work is **M3 design here**. Do not ask ingest to change the
Type C primitive.

Dynamical families are **not** Jacobian-derived `mndm.dynamics`. Do not
extend `local_dynamics/readers.py` silently for `/dynamical_families/`.
Update 2026-09-05: analysis readers for `a_hat` / `A_bD` and a bounded
cross-fit chart-velocity candidate are now implemented in the separate
`nmd_analysis.dynamical_families` package. This handoff remains the scientific
baseline; M3 qualification, empirical M4 and utility M5 remain open.
See [v3 analysis setup](v3_analysis_setup.md) and [M3 design](m3_design.md).

```text
INGEST  frozen C1 consume-external-b + a_hat identity
ANALYSIS  M3 identification, later M4/M5, leftover science gates
FAR     parked BLOCKED_EXTERNAL_CUSTODY (ingest custody, not this repo)
```

---

## Boundary

Long-term repo-boundary rule (SL-005, preserve verbatim):

> If an operation requires choosing among scientifically plausible
> estimators, splitting data to establish independence, tuning a
> validation protocol, constructing null controls, or interpreting a
> condition contrast, it belongs outside ingest.

Complementary ingest-admissibility rule:

> An ingest primitive is admissible when the mathematical object and
> required inputs are already specified, and the operation deterministically
> transforms those inputs into a versioned measurement artifact without
> choosing the scientific interpretation.

```text
INGEST if:
specified inputs
+ deterministic transformation
+ versioned output
+ fail-closed validity checks

ANALYSIS if:
estimator choice
or identification
or data splitting
or comparator/null construction
or scientific model selection
or hypothesis inference
```

```text
INGEST
qualified inputs
      ↓
deterministic/versioned measurement primitive
      ↓
auditable artifact


ANALYSIS
data
 ↓
identification / estimator choice
 ↓
cross-fitting / controls / nulls
 ↓
scientific qualification
 ↓
possibly qualified input to ingest primitive
```

The main repository supplies per-recording, versioned measurements and
their provenance. This analysis repository owns estimator selection,
independence/cross-fit protocols, null controls, dataset feasibility,
cohort aggregation, and scientific claims.

Ingest can say: if you hand it a chart-space velocity field supplied
under an externally governed qualification, with compatible time
semantics, it can calculate C1 alignment without changing the
increment-covariance diffusion object. Ingest **records** that
certificate and validates structural compatibility. It does **not**
adjudicate scientific independence, estimator bias, or M3 PASS.

Ingest will **not** answer: how should that velocity field be constructed
from this dataset?

---

## Ingest contract (available today)

```text
Available:
- MNPS chart trajectory
- timestamps / dt
- increment-covariance a_hat at /dynamical_families/diffusion/v1
  a_semantics = raw_increment_covariance
- C1 alignment API
- provenance fields
- forbidden-source rules

Analysis must supply (if C1 is used empirically / at M3):
- b_hat array
- b_hat content hash
- exact trajectory/timebase alignment
- source MNPS artifact hash
- source NMD schema/version
- NMD code/package revision used for C1 evaluation
- estimator id/version
- estimator provenance
- qualification id/hash
- train/evaluation partition provenance
- train/evaluation index hashes
- embargo specification
- overlap audit

Analysis owns:
- crossfit estimator
- embargo
- oracle/comparator/null experiments
- M3 qualification decision

Ingest does not:
- fit b
- choose embargo
- cross-validate
- infer NDT drift
- adjudicate scientific qualification
```

The contamination certificate must not be a declarative flag alone.
M3 should prove and serialize something auditable, for example:

```text
train_increment_ids ∩ evaluation_increment_ids = ∅
embargo violations = 0
```

with hashes or counts supporting those statements.

Library API (do not request residualization):

```python
estimate_local_diffusion_geometry(
    ...,
    drift=external_field_or_none,
    residualize_increments=False,
)
```

Gate C1-A: truth-known chart-space \(b\) leaves `a_hat` / `D_total` /
`d_diff` / `c_diff` byte-equal to `drift=None`.

Production ingest files still have `A_bD` / `R_b_over_a`
`not_testable` / `independent_drift_not_supplied`. NaN is not zero
alignment. `ratio_semantics=chart_velocity_to_increment_spread` when C1
is computed; that is not an Itô drift-to-diffusion ratio.

**Refuse as `b`:** `mnps_xdot`, Jacobian intercept, same-sample increment
mean, Jacobian residual, committor potential gradient.

C2 `residualize_increments=True` is `invalid` /
`c2_residualize_increments_not_authorized`. Do not ask ingest to
residualize `a_hat`.

`crossfit_local_chart_b` may later be a **provenance token** on an
externally supplied field. The algorithm lives here, not in ingest.

ds004100 OD-EPI-001 is an `a_hat` translation overlay (D-M4 PASS,
serialization/QC). It is not a drift experiment and not an ictal
biology license.

```text
D-M4 PASS
    =
chart-space increment-covariance serialization feasibility

NOT
    ictal biology
    latent a(x)
    drift
    Type C
```

Overlay lifecycle: analysis does not donate estimator code back to ingest
just because a measurement becomes useful. The input can remain
externally produced. Science lead decides whether an object has earned
an external qualification; ingest may later serialize it under an
explicit overlay without owning the estimator.

---

## Immediate analysis programme: DF-DRIFT-C1-M3

Compare:

```text
truth-known b               ← positive control
cross-fit b                 ← candidate estimator
same-sample local mean b    ← contaminated comparator
shuffled/time-displaced b   ← negative control
```

Measure: alignment recovery, bias in \(A_{bD}\), rank recovery,
variance, embargo/`dt` sensitivity, insufficient-support failure,
`train/eval overlap = empty`, `embargo violations = 0`.

Later: M4 dataset-selection gate (not ds004100 ictal); M5 utility only
after M4.

---

## Other leftover gates from ingest `project/mnps_v3`

| Item | This repo owns | Do not |
|---|---|---|
| C2 residualized `a` | nothing until a new science-lead gate | request ingest residualization |
| ds004100 D-M4 | any later contrast is a **new** prereg | treat 319/319 `a_hat` as ictal biology |
| Gate F \(W_Q\) | whether the discrete chart-space predictive-spread object is useful | Gate E residual covariance as process noise, NDT reachability, I-CARE tubes, or consciousness |
| Committor RC / A–B | which RC, which A/B, new overlay prereg | 2-D/3-D/9D MNPS `q`; stage labels as truth |
| FAR \(R(\rho)\) / FAR-003+ | interpretability and empirical curve **after** E1+E2 XML unblocks ingest custody | infer FAR from Jacobian/FTR/\(W_Q\); live 002E while blocked |
| Grain | refuse \(N=\) window-count; keep recording/subject grain | pool 40k windows as independent \(N\) |
| Deferred families | do not invent \(I_{\mathrm{pred}}\) / TE / FDT / Fisher / \(M(\tau)\) as NMD exports | |
| Chart robustness | audit-only condition-sign stability | alternative MNPS charts |

Committor ingest primitive: MNPS chart trajectory + explicit 1-D RC +
explicit A/B + certificate. No production overlay without a new prereg.
BOAS G=17 failed local predictive criteria. ds004100 destination
NOT_TESTABLE.

FAR ingest primitive: perturbation/outcome table with an external
protocol certificate. Retrospective ingest is `not_testable` /
`no_perturbation_protocol`. FAR-EXT-002E is `BLOCKED_EXTERNAL_CUSTODY`
in ingest until complete E1+E2 XML.

### Gate F / \(W_Q\)

Frozen ingest primitive (`gate_f_admissible_q.md`, 2026-09-02): opt-in
`/stochastic_reachability/v1` may propagate a recording-level **discrete
transition-residual covariance** with a cross-fit transition operator to
form a chart-space predictive-spread object.

```text
input_semantics =
    discrete_transition_residual_covariance

NOT:
    process_noise_covariance
    continuous-time a(x)
    NDT SDE Q
    historical I-CARE reachability semantics
```

Family YAML `spread` stays `gate_closed`. Historical I-CARE
`tube_d_eff_median` is **not** this schema. Registry forbid
`gate_e_proxy_as_process_noise` stays.

---

## Claim ceilings

```text
Safe:     MNPS is a chart. MNJ is a chart Jacobian.
          C1 is alignment of an independent chart-space velocity
          with increment covariance. Ingest does not supply b
          and does not adjudicate scientific qualification of b.

Not:      Itô b(X) or a(x)
          x_dot or Jacobian intercept as SDE b
          empirical A_bD as NDT alignment
          R_b/a under C1 as an Itô ratio
          C2 residualized a
          licensed NDT α/ω/G_peak
          Gate E Q as process noise
          observational FAR / R(ρ)
          I-CARE tubes = stochastic_reachability.v1
          ingest metadata = M3 PASS
```

---

## Evidence ledger

```text
ESTABLISHED / INTERNAL VALIDATED
DF-DRIFT-C1 M1–M2: truth-known chart-space velocity for C1
without modifying frozen increment-covariance a_hat.

ARCHITECTURAL DECISION
Drift identification: owned by nmd-analysis, not ingest.

PLAUSIBLE / UNTESTED
crossfit_local_chart_b as a candidate independent velocity.

NOT ESTABLISHED
empirical chart drift; Itô drift; C2; empirical NDT alignment;
scientific utility of C1.
```
