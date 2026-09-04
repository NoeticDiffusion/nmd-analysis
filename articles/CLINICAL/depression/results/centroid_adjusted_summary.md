# Centroid-adjusted depression summary

- Dataset: `ds003478`
- Primary comparison: `BDI 0-13` vs `BDI 20-63`
- Dynamic models are fit on subject-averaged values with centroid covariates from the matching coordinate family.

## Baseline centroid shifts

### 3D

- `e_median`: d=0.386, delta=0.220, p=0.07771, q=0.3864
- `e_mean`: d=0.297, delta=0.180, p=0.1751, q=0.3864
- `m_mean`: d=0.259, delta=0.220, p=0.1932, q=0.3864
- `m_median`: d=0.216, delta=0.196, p=0.2856, q=0.4284
- `d_median`: d=0.039, delta=0.027, p=0.8614, q=0.8857

### 9D

- `e_m_mean`: d=0.688, delta=0.427, p=0.001326, q=0.02387
- `e_m_median`: d=0.589, delta=0.396, p=0.006068, q=0.05461
- `m_o_median`: d=0.537, delta=0.536, p=0.0135, q=0.06371
- `m_o_mean`: d=0.523, delta=0.514, p=0.01416, q=0.06371
- `d_s_median`: d=-0.307, delta=-0.316, p=0.1319, q=0.4058

## Centroid-adjusted dynamics

- `Block MNJ m->m` / `block_frobenius_mean` (block=m->m): raw d=-0.517, adjusted beta=-0.024, residual d=-0.474, p=0.007267, q=0.05087, partial R2=0.073
- `Distribution summary` / `e_m_mad_sigma`: raw d=0.984, adjusted beta=0.179, residual d=0.577, p=0.02358, q=0.08252, partial R2=0.053
- `Block MNJ m->d` / `block_frobenius_mean` (block=m->d): raw d=-0.516, adjusted beta=-0.021, residual d=-0.330, p=0.0529, q=0.1234, partial R2=0.039
- `Global 9D MNJ` / `rotational_power_mean`: raw d=0.767, adjusted beta=0.002, residual d=0.375, p=0.108, q=0.1527, partial R2=0.027
- `Tier-2 EMMI` / `mv_median`: raw d=-0.453, adjusted beta=-0.165, residual d=-0.378, p=0.1091, q=0.1527, partial R2=0.025
- `Reachability cones` / `tube_log_eig_var_mean`: raw d=-0.816, adjusted beta=-1.176, residual d=-0.305, p=0.1673, q=0.1952, partial R2=0.020
- `Global 3D MNJ` / `spectral_radius_median`: raw d=0.022, adjusted beta=0.000, residual d=0.052, p=0.8579, q=0.8579, partial R2=0.000
