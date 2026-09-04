# Local dynamics extension

This directory documents the main-repository measurement contracts introduced
for local dynamics. It does not implement the retrospective audits, cohort
statistics, or biological claims described in the analysis-repository material.

Capabilities:

- `mndm.jacobian_metrics.v1`: semantic measurements derived from `J_hat`.
- `mndm.finite_time_response.v1`: opt-in, time-ordered finite-time response.
- `mndm.residual_covariance_proxy.v1`: residual covariance with explicit time semantics.
- `mndm.stochastic_reachability.v1`: transport of admissible residual covariance.

All metrics inherit `primary_coordinate_contract`; outputs must never merge
subject- and cohort-anchored coordinate layers.
