# Dynamical families

This directory documents the main-repository **dynamical-family**
measurement contracts (`mndm.dynamical_families`). It is separate from
Jacobian-derived `mndm.dynamics` documented under `local_dynamics/`.

Canonical ingest write paths:

```text
/dynamical_families/diffusion/v1
/dynamical_families/destination/v1
/dynamical_families/resilience/v1
```

Legacy read-only: `/orthogonal_dynamics/`. Schema IDs unchanged.
Family YAML `spread` is `gate_closed`; opt-in discrete \(W_Q\) is
`/stochastic_reachability/v1` under local dynamics
(`input_semantics=discrete_transition_residual_covariance`, not
process noise).

This folder does **not** implement cohort statistics, cross-fit drift
estimators, or biological claims. See `analysis_handoff.md`.

Python readers now live in the separate `nmd_analysis.dynamical_families`
package. They are registered with `nmd-analysis run`; `nmd-analysis v3-audit`
adds a descriptive support/missingness report for the exact extraction.
See [v3 analysis setup](v3_analysis_setup.md). These readers do not qualify
the estimators biologically or implement the full M3 benchmark programme.

Capabilities ingest can already serialize (opt-in, fail-closed):

- `mndm.diffusion_geometry.v1`: increment-covariance `a_hat`. Ingest
  `drift=None`. Library C1 may consume a chart-space velocity supplied
  under an externally governed qualification without changing `a_hat`.
  Ingest records the certificate and checks structural compatibility;
  it does not adjudicate scientific independence. Analysis owns
  identification of `b` (DF-DRIFT-C1-M3).
- `mndm.committor.v1`: 1-D O2b adapter only; explicit RC + A/B.
- `mndm.finite_amplitude_resilience.v1`: perturbation-outcome summary;
  retrospective ingest is `not_testable`.

All family outputs inherit `primary_coordinate_contract`. Do not merge
subject- and cohort-anchored layers. `claim_status=no_biological_claim`
is not an NDT license.
