# Classical Comparator Summary

- primary time bin: `0_12h`
- comparison: `CPC 1` vs `CPC 5`

## Available comparator metrics


## Unavailable in this bundle

- `MNPS path length` (`mnps_path_length`): `unavailable`.
- `MNPS step norm` (`mnps_step_norm_median`): `unavailable`.
- `MNPS displacement` (`mnps_displacement`): `unavailable`.
- `9D global std mean` (`coords_9d_global_std_mean`): `unavailable`. 9D summaries were omitted from the locked export because the upstream ingest used a temporary stability override with `mnps_9d.enabled: false` after duplicated / degenerate 9D coordinate columns triggered a fail-fast validation stop. This was a data-integrity safeguard to avoid silently writing misleading 9D Jacobian / trajectory summaries, not evidence that 9D lacks value.
- `MNJ Frobenius norm` (`jacobian_fro_median`): `unavailable`.
- `MNJ spectral radius` (`jacobian_spectral_radius_median`): `unavailable`.
- `MNJ trace` (`jacobian_trace_median`): `unavailable`.
- `MNJ condition` (`jacobian_condition_median`): `unavailable`.
