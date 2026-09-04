# Jacobian Metrics v1

`mndm.jacobian_metrics.v1` interprets, but does not re-estimate, the existing
continuous-time local Jacobian field. Per valid window it writes
`spectral_abscissa`, `numerical_abscissa`, `symmetric_rate_min`,
`reactivity_gap`, `spectral_radius`, `frobenius_norm`, `trace`,
`rotation_norm`, and diagnostic `henrici_departure`.

`stable_reactive_flag` is one precisely defined condition:
`spectral_abscissa < -stability_zero_tolerance` and
`numerical_abscissa > reactivity_zero_tolerance`. Invalid windows retain NaN
metric values and `-1` for categorical fields; they are never zero-filled.
`stable_reactive_fraction` is calculated only over metric-valid windows and is
always accompanied by support counts.

Exports: `/jacobian/derived_metrics/v1/` and
`/jacobian_9D/derived_metrics/v1/`. Numerical abscissa uses the Euclidean
metric of the release-fixed exported coordinate chart.
