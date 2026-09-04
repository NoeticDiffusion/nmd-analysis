# Additional Parkinson walking QC / robustness summary

This supplement-facing QC pass adds three checks to the walking manuscript:

1. explicit classical-comparator availability status,
2. leave-one-subject-out stability for the revised focal rows,
3. and a time-reshuffle null for the leading exploratory trajectory rows.

## Classical comparator status

- `classical_eeg_sidecars`: status `unavailable` with `0` / `277` H5 files carrying the required extension. No direct benchmark claim against classical EEG is justified from this bundle because the conventional_eeg extension is absent.

## Leave-one-subject-out stability

- `Global walk d_n_mean`: full effect `0.7658`, full `q = 0.03018`, leave-one-out effect range `0.7098` to `0.8325`, median `0.7646`, sign consistency `1`, worst-case omission `sub-003`.
- `Global walk d_n_median`: full effect `0.746`, full `q = 0.03018`, leave-one-out effect range `0.6908` to `0.8124`, median `0.7445`, sign consistency `1`, worst-case omission `sub-015`.
- `Global walk d_mean`: full effect `0.7109`, full `q = 0.03581`, leave-one-out effect range `0.6404` to `0.8045`, median `0.7074`, sign consistency `1`, worst-case omission `sub-015`.
- `Global walk d_median`: full effect `0.7185`, full `q = 0.03581`, leave-one-out effect range `0.6497` to `0.8073`, median `0.7153`, sign consistency `1`, worst-case omission `sub-015`.
- `PD paired d_n_mean`: full effect `0.4089`, full `q = 0.001038`, leave-one-out effect range `0.3962` to `0.4501`, median `0.4069`, sign consistency `1`, worst-case omission `sub-067`.
- `PD paired m_a_iqr`: full effect `0.4717`, full `q = 0.0006546`, leave-one-out effect range `0.4599` to `0.5084`, median `0.47`, sign consistency `1`, worst-case omission `sub-051`.
- `PD paired d_iqr`: full effect `0.4025`, full `q = 0.0007283`, leave-one-out effect range `0.3899` to `0.445`, median `0.4`, sign consistency `1`, worst-case omission `sub-030`.
- `PD paired d_mad`: full effect `0.4125`, full `q = 0.0007283`, leave-one-out effect range `0.3995` to `0.4535`, median `0.4091`, sign consistency `1`, worst-case omission `sub-030`.
- `HC context m_a_mean`: full effect `0.8884`, full `q = 0.01758`, leave-one-out effect range `0.8439` to `1.156`, median `0.8675`, sign consistency `1`, worst-case omission `sub-022`.

## Time-reshuffle null for trajectory rows

- `Rest trajectory noetic_action_kinetic (3D)`: observed `d = -0.6865`, observed `q = 0.01209`, null mean `|d| = 0.4309`, null p95 `|d| = 0.6258`, empirical `p = 0.01493` across `200` reshuffles.
- `Rest trajectory curvature_median (3D)`: observed `d = 0.5964`, observed `q = 0.01209`, null mean `|d| = 0.5401`, null p95 `|d| = 0.709`, empirical `p = 0.3383` across `200` reshuffles.
- `Rest trajectory path_length (3D)`: observed `d = -0.6714`, observed `q = 0.01209`, null mean `|d| = 0.6065`, null p95 `|d| = 0.6809`, empirical `p = 0.08955` across `200` reshuffles.
- `Rest trajectory noetic_action_jerk (3D)`: observed `d = -0.5295`, observed `q = 0.03216`, null mean `|d| = 0.3976`, null p95 `|d| = 0.5566`, empirical `p = 0.1095` across `200` reshuffles.

## Boundaries

- The leave-one-out pass checks row stability, not external replication.
- The time-reshuffle null permutes exported window order within run. It therefore tests whether trajectory findings depend on temporal order, but it is not a raw-signal permutation analysis.
- Classical EEG remains an availability boundary rather than a comparator result in this bundle.
