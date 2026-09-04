# Resting-state depression supplementary QC / robustness summary

This QC pass focuses on three review-facing questions:

1. how many usable subjects support each selected article block,
2. whether the selected low/high and continuous-BDI rows are directionally stable under leave-one-subject-out omission,
3. and which centroid-adjusted rows remain most relevant after accounting for baseline coordinate position.

## Selected block coverage

- `Global 3D MNPS` / `d_median`: total `122`, low `76`, mid `15`, high `30`.
- `Global 9D MNPS` / `d_s_mean`: total `122`, low `76`, mid `15`, high `30`.
- `Global 3D MNJ` / `spectral_radius_median`: total `122`, low `76`, mid `15`, high `30`.
- `Global 9D MNJ` / `rotational_power_mean`: total `122`, low `76`, mid `15`, high `30`.
- `9x9 block MNJ` / `block_anisotropy_mean`: total `122`, low `76`, mid `15`, high `30`.
- `Reachability cones` / `tube_log_eig_var_mean`: total `122`, low `76`, mid `15`, high `30`.
- `Tier-2 EMMI` / `mv_median`: total `122`, low `76`, mid `15`, high `30`.
- `Distribution summary` / `e_m_mad_sigma`: total `122`, low `76`, mid `15`, high `30`.

## Leave-one-subject-out stability

- `Global 3D MNPS` / `d_median`: full `d = 0.03942`, leave-one-out `d` range `-0.04292` to `0.1197`, sign consistency `0.9672`; full `rho = -0.07352`, leave-one-out `rho` range `-0.09692` to `-0.05104`.
- `Global 9D MNPS` / `d_s_mean`: full `d = -0.2241`, leave-one-out `d` range `-0.291` to `-0.1705`, sign consistency `1`; full `rho = -0.124`, leave-one-out `rho` range `-0.1438` to `-0.1054`.
- `Global 3D MNJ` / `spectral_radius_median`: full `d = 0.02207`, leave-one-out `d` range `-0.2039` to `0.09473`, sign consistency `0.9344`; full `rho = -0.08706`, leave-one-out `rho` range `-0.1106` to `-0.06903`.
- `Global 9D MNJ` / `rotational_power_mean`: full `d = 0.7673`, leave-one-out `d` range `0.7163` to `0.8509`, sign consistency `1`; full `rho = 0.3097`, leave-one-out `rho` range `0.2954` to `0.3345`.
- `9x9 block MNJ` / `block_anisotropy_mean`: full `d = -0.2862`, leave-one-out `d` range `-0.3184` to `-0.2516`, sign consistency `1`; full `rho = 0.00714`, leave-one-out `rho` range `-0.009069` to `0.03099`.
- `Reachability cones` / `tube_log_eig_var_mean`: full `d = -0.816`, leave-one-out `d` range `-0.8932` to `-0.7905`, sign consistency `1`; full `rho = -0.3433`, leave-one-out `rho` range `-0.372` to `-0.3293`.
- `Tier-2 EMMI` / `mv_median`: full `d = -0.4531`, leave-one-out `d` range `-0.5141` to `-0.3316`, sign consistency `1`; full `rho = -0.112`, leave-one-out `rho` range `-0.1319` to `-0.09001`.
- `Distribution summary` / `e_m_mad_sigma`: full `d = 0.984`, leave-one-out `d` range `0.9173` to `1.068`, sign consistency `1`; full `rho = 0.3576`, leave-one-out `rho` range `0.346` to `0.3817`.

## Centroid-adjusted focus

- `Block MNJ m->m (m->m)` / `block_frobenius_mean`: adjusted beta `-0.02429`, adjusted q `0.05087`, residualized d `-0.4736`.
- `Distribution summary` / `e_m_mad_sigma`: adjusted beta `0.1793`, adjusted q `0.08252`, residualized d `0.5765`.
- `Block MNJ m->d (m->d)` / `block_frobenius_mean`: adjusted beta `-0.02121`, adjusted q `0.1234`, residualized d `-0.3299`.
- `Global 9D MNJ` / `rotational_power_mean`: adjusted beta `0.001752`, adjusted q `0.1527`, residualized d `0.3746`.
- `Tier-2 EMMI` / `mv_median`: adjusted beta `-0.1654`, adjusted q `0.1527`, residualized d `-0.3778`.
- `Reachability cones` / `tube_log_eig_var_mean`: adjusted beta `-1.176`, adjusted q `0.1952`, residualized d `-0.3048`.

## Notes

- The strongest unadjusted resting-state task surface remains reachability, 9D MNJ, and distribution; the centroid-adjusted pass is a sensitivity analysis rather than a replacement endpoint.
- Leave-one-subject-out omission is a directional stability check only and should not be over-read as external replication.
