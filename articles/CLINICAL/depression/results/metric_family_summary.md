# Metric family summary

- Dataset: `ds003478`
- Contrast: `BDI_0_13_vs_BDI_20_63`

## Available analysis families

- `adaptive_collapse`: other
- `Distribution summary`: location, shape, spread
- `features_raw`: other
- `features_robust_z`: other
- `Global 3D MNPS`: location, spread
- `Global 9D MNPS`: location, spread
- `Global 3D MNJ`: jacobian
- `Global 9D MNJ`: jacobian
- `9x9 block MNJ`: block_jacobian
- `Reachability cones`: reachability
- `regional_3d`: other
- `regional_9d`: other
- `robust_summary`: other
- `Tau summary`: timescale
- `Tier-2 EMMI`: trajectory
- `Tier-2 Jacobian`: jacobian

## Strongest metric by family

### adaptive_collapse

- `other`: `a_operator_norm`, d=-0.1541, p=0.3288, q=0.7701

### Distribution summary

- `location`: `e_m_mean`, d=0.5657, p=0.0004998, q=0.01319
- `spread`: `e_m_iqr`, d=0.7315, p=0.0004998, q=0.01319
- `shape`: `e_m_skewness`, d=-0.5384, p=0.0009995, q=0.01885

### features_raw

- `other`: `feature_iqr`, d=0.8353, p=0.0004998, q=0.01223

### features_robust_z

- `other`: `feature_min`, d=-0.7938, p=0.0004998, q=0.03823

### Global 3D MNPS

- `location`: `e_median`, d=0.3547, p=0.02049, q=0.1844
- `spread`: `d_std`, d=-0.1332, p=0.3708, q=0.6675

### Global 9D MNPS

- `location`: `e_m_mean`, d=0.5657, p=0.0004998, q=0.008996
- `spread`: `m_o_std`, d=0.5276, p=0.0009995, q=0.008996

### Global 3D MNJ

- `jacobian`: `trace_median`, d=-0.1814, p=0.2374, q=1

### Global 9D MNJ

- `jacobian`: `jacobian_near_singular_rate`, d=-0.6861, p=0.0004998, q=0.003165

### 9x9 block MNJ

- `block_jacobian`: `block_frobenius_mean` (block=m->m), d=-0.3311, p=0.02699, q=0.2429

### Reachability cones

- `reachability`: `tube_log_det_mean`, d=0.7354, p=0.0004998, q=0.00296

### regional_3d

- `other`: `m_std`, d=-0.4379, p=0.003498, q=0.1124

### regional_9d

- `other`: `d_l_std`, d=-0.4234, p=0.003998, q=0.2399

### robust_summary

- `other`: `m_o_ci_high`, d=0.5286, p=0.0004998, q=0.01199

### Tau summary

- `timescale`: `d_n_tau_sec`, d=0.4975, p=0.002499, q=0.1499

### Tier-2 EMMI

- `trajectory`: `mv_over_speed_median`, d=-0.4034, p=0.007496, q=0.04498

### Tier-2 Jacobian

- `jacobian`: `rotation_coherence_mean_resultant_length`, d=0.2702, p=0.08346, q=0.8389
