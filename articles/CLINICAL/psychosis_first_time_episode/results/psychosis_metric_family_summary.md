# Psychosis metric family summary

- Analysis root: `J:\repos\NoeticDiffusion\data\analysis\psychosis_cohort_anchor_20260520`

## Available families

- `ds003944` / `FEP medicated vs FEP unmedicated` / `Adaptive collapse`: other
- `ds003944` / `FEP medicated vs FEP unmedicated` / `Global 3D MNPS`: location, spread
- `ds003944` / `FEP medicated vs FEP unmedicated` / `Stratified 9D MNPS`: location, spread
- `ds003944` / `FEP medicated vs FEP unmedicated` / `Global 3D MNJ`: jacobian
- `ds003944` / `FEP medicated vs FEP unmedicated` / `Stratified 9D MNJ`: jacobian
- `ds003944` / `FEP medicated vs FEP unmedicated` / `9x9 block MNJ`: block_jacobian
- `ds003944` / `FEP medicated vs FEP unmedicated` / `Reachability cones`: reachability
- `ds003944` / `FEP medicated vs FEP unmedicated` / `Trajectory dynamics`: other, shape, spread, timescale, trajectory
- `ds003944` / `FEP medicated vs Healthy` / `Adaptive collapse`: other
- `ds003944` / `FEP medicated vs Healthy` / `Global 3D MNPS`: location, spread
- `ds003944` / `FEP medicated vs Healthy` / `Stratified 9D MNPS`: location, spread
- `ds003944` / `FEP medicated vs Healthy` / `Global 3D MNJ`: jacobian
- `ds003944` / `FEP medicated vs Healthy` / `Stratified 9D MNJ`: jacobian
- `ds003944` / `FEP medicated vs Healthy` / `9x9 block MNJ`: block_jacobian
- `ds003944` / `FEP medicated vs Healthy` / `Reachability cones`: reachability
- `ds003944` / `FEP medicated vs Healthy` / `Trajectory dynamics`: other, shape, spread, timescale, trajectory
- `ds003944` / `FEP unmedicated vs Healthy` / `Adaptive collapse`: other
- `ds003944` / `FEP unmedicated vs Healthy` / `Global 3D MNPS`: location, spread
- `ds003944` / `FEP unmedicated vs Healthy` / `Stratified 9D MNPS`: location, spread
- `ds003944` / `FEP unmedicated vs Healthy` / `Global 3D MNJ`: jacobian
- `ds003944` / `FEP unmedicated vs Healthy` / `Stratified 9D MNJ`: jacobian
- `ds003944` / `FEP unmedicated vs Healthy` / `9x9 block MNJ`: block_jacobian
- `ds003944` / `FEP unmedicated vs Healthy` / `Reachability cones`: reachability
- `ds003944` / `FEP unmedicated vs Healthy` / `Trajectory dynamics`: other, shape, spread, timescale, trajectory
- `ds003947` / `FEP medicated vs FEP unmedicated` / `Adaptive collapse`: other
- `ds003947` / `FEP medicated vs FEP unmedicated` / `Global 3D MNPS`: location, spread
- `ds003947` / `FEP medicated vs FEP unmedicated` / `Stratified 9D MNPS`: location, spread
- `ds003947` / `FEP medicated vs FEP unmedicated` / `Global 3D MNJ`: jacobian
- `ds003947` / `FEP medicated vs FEP unmedicated` / `Stratified 9D MNJ`: jacobian
- `ds003947` / `FEP medicated vs FEP unmedicated` / `9x9 block MNJ`: block_jacobian
- `ds003947` / `FEP medicated vs FEP unmedicated` / `Reachability cones`: reachability
- `ds003947` / `FEP medicated vs FEP unmedicated` / `Trajectory dynamics`: other, shape, spread, timescale, trajectory
- `ds003947` / `FEP medicated vs Healthy` / `Adaptive collapse`: other
- `ds003947` / `FEP medicated vs Healthy` / `Global 3D MNPS`: location, spread
- `ds003947` / `FEP medicated vs Healthy` / `Stratified 9D MNPS`: location, spread
- `ds003947` / `FEP medicated vs Healthy` / `Global 3D MNJ`: jacobian
- `ds003947` / `FEP medicated vs Healthy` / `Stratified 9D MNJ`: jacobian
- `ds003947` / `FEP medicated vs Healthy` / `9x9 block MNJ`: block_jacobian
- `ds003947` / `FEP medicated vs Healthy` / `Reachability cones`: reachability
- `ds003947` / `FEP medicated vs Healthy` / `Trajectory dynamics`: other, shape, spread, timescale, trajectory
- `ds003947` / `FEP unmedicated vs Healthy` / `Adaptive collapse`: other
- `ds003947` / `FEP unmedicated vs Healthy` / `Global 3D MNPS`: location, spread
- `ds003947` / `FEP unmedicated vs Healthy` / `Stratified 9D MNPS`: location, spread
- `ds003947` / `FEP unmedicated vs Healthy` / `Global 3D MNJ`: jacobian
- `ds003947` / `FEP unmedicated vs Healthy` / `Stratified 9D MNJ`: jacobian
- `ds003947` / `FEP unmedicated vs Healthy` / `9x9 block MNJ`: block_jacobian
- `ds003947` / `FEP unmedicated vs Healthy` / `Reachability cones`: reachability
- `ds003947` / `FEP unmedicated vs Healthy` / `Trajectory dynamics`: other, shape, spread, timescale, trajectory

## Strongest metric by family

### ds003944

#### FEP medicated vs FEP unmedicated

- `Adaptive collapse` / `other`: `a_operator_norm`, d=0.3885, p=0.1864, q=0.5592
- `Global 3D MNPS` / `location`: `e_median`, d=-0.5144, p=0.08246, q=0.3223
- `Global 3D MNPS` / `spread`: `m_std`, d=0.9723, p=0.001999, q=0.01799
- `Stratified 9D MNPS` / `location`: `m_o_mean`, d=0.5514, p=0.06347, q=0.6927
- `Stratified 9D MNPS` / `spread`: `m_o_std`, d=0.9275, p=0.003498, q=0.09445
- `Global 3D MNJ` / `jacobian`: `rotation_norm_median`, d=0.6053, p=0.03648, q=0.305
- `Stratified 9D MNJ` / `jacobian`: `aci_mean`, d=0.7262, p=0.01699, q=0.07952
- `9x9 block MNJ` / `block_jacobian`: `block_trace_mean`, d=0.6913, p=0.01099, q=0.08096
- `Reachability cones` / `reachability`: `tube_log_det_split_half_rho`, d=-0.5060, p=0.08946, q=0.8984
- `Trajectory dynamics` / `spread`: `tier2_jacobian_condition_number_mad`, d=-0.0403, p=0.902, q=0.969
- `Trajectory dynamics` / `shape`: `e_delta_mean_median`, d=0.3239, p=0.2564, q=0.6217
- `Trajectory dynamics` / `trajectory`: `endpoint_dist`, d=0.5698, p=0.06047, q=0.4647
- `Trajectory dynamics` / `timescale`: `m_tau_sec`, d=0.5602, p=0.06447, q=0.4647
- `Trajectory dynamics` / `other`: `tier2_jacobian_rotation_coherence_mrl`, d=0.0722, p=0.7866, q=0.969

#### FEP medicated vs Healthy

- `Adaptive collapse` / `other`: `capture_gate`, d=0.7648, p=0.003498, q=0.009745
- `Global 3D MNPS` / `location`: `m_mean`, d=0.8812, p=0.0009995, q=0.004498
- `Global 3D MNPS` / `spread`: `m_std`, d=0.6537, p=0.01149, q=0.03448
- `Stratified 9D MNPS` / `location`: `m_o_mean`, d=0.8139, p=0.002999, q=0.02699
- `Stratified 9D MNPS` / `spread`: `m_o_std`, d=0.7154, p=0.008496, q=0.04588
- `Global 3D MNJ` / `jacobian`: `spectral_radius_mean`, d=0.4562, p=0.06947, q=0.8965
- `Stratified 9D MNJ` / `jacobian`: `mdr_mean`, d=0.3301, p=0.2184, q=0.9812
- `9x9 block MNJ` / `block_jacobian`: `block_trace_mean`, d=0.5617, p=0.01899, q=0.1709
- `Reachability cones` / `reachability`: `tube_capture_gate_median`, d=0.7648, p=0.003998, q=0.1154
- `Trajectory dynamics` / `spread`: `tier2_jacobian_condition_number_iqr`, d=0.0486, p=0.8956, q=0.9781
- `Trajectory dynamics` / `shape`: `e_delta_mean_median`, d=0.5299, p=0.03698, q=0.59
- `Trajectory dynamics` / `trajectory`: `endpoint_dist`, d=0.4396, p=0.08146, q=0.59
- `Trajectory dynamics` / `timescale`: `e_tau_sec`, d=-0.3507, p=0.2374, q=0.6437
- `Trajectory dynamics` / `other`: `tier2_jacobian_condition_number_median`, d=-0.1151, p=0.7941, q=0.9379

#### FEP unmedicated vs Healthy

- `Adaptive collapse` / `other`: `q_ratio_h4`, d=-0.6332, p=0.02999, q=0.06222
- `Global 3D MNPS` / `location`: `e_mean`, d=0.6950, p=0.02499, q=0.1642
- `Global 3D MNPS` / `spread`: `m_std`, d=-0.1181, p=0.6772, q=0.795
- `Stratified 9D MNPS` / `location`: `m_e_median`, d=0.7012, p=0.02199, q=0.2969
- `Stratified 9D MNPS` / `spread`: `e_s_std`, d=0.4427, p=0.1369, q=0.4134
- `Global 3D MNJ` / `jacobian`: `rotation_norm_median`, d=-0.3229, p=0.2924, q=0.921
- `Stratified 9D MNJ` / `jacobian`: `aci_median`, d=-0.6614, p=0.01899, q=0.1531
- `9x9 block MNJ` / `block_jacobian`: `block_frobenius_mean`, d=-0.5733, p=0.04648, q=0.4183
- `Reachability cones` / `reachability`: `tube_q_ratio_h4_mean`, d=-0.7407, p=0.01149, q=0.4714
- `Trajectory dynamics` / `spread`: `tier2_jacobian_condition_number_iqr`, d=0.0307, p=0.956, q=0.995
- `Trajectory dynamics` / `shape`: `m_delta_mean_median`, d=-0.7149, p=0.01349, q=0.3103
- `Trajectory dynamics` / `trajectory`: `speed_median`, d=-0.3219, p=0.2734, q=0.995
- `Trajectory dynamics` / `timescale`: `m_tau_sec`, d=-0.3670, p=0.2429, q=0.995
- `Trajectory dynamics` / `other`: `tier2_jacobian_rotation_coherence_mrl`, d=-0.0719, p=0.8176, q=0.995

### ds003947

#### FEP medicated vs FEP unmedicated

- `Adaptive collapse` / `other`: `capture_gate`, d=0.0526, p=0.8921, q=0.989
- `Global 3D MNPS` / `location`: `d_mean`, d=0.4964, p=0.2239, q=0.7416
- `Global 3D MNPS` / `spread`: `d_std`, d=0.2178, p=0.6082, q=0.7416
- `Stratified 9D MNPS` / `location`: `e_m_median`, d=-0.5878, p=0.1654, q=0.6176
- `Stratified 9D MNPS` / `spread`: `d_n_std`, d=-0.6894, p=0.1004, q=0.6176
- `Global 3D MNJ` / `jacobian`: `trace_median`, d=-0.7317, p=0.07496, q=1
- `Stratified 9D MNJ` / `jacobian`: `aci_mean`, d=-0.4878, p=0.2544, q=0.8564
- `9x9 block MNJ` / `block_jacobian`: `block_trace_mean`, d=0.7494, p=0.07846, q=0.5386
- `Reachability cones` / `reachability`: `persistence_tau_kappa_median`, d=1.1435, p=0.01149, q=0.8736
- `Trajectory dynamics` / `spread`: `tier2_jacobian_condition_number_mad`, d=0.1598, p=0.7166, q=0.954
- `Trajectory dynamics` / `shape`: `m_delta_mean_median`, d=0.5193, p=0.2054, q=0.954
- `Trajectory dynamics` / `trajectory`: `curvature_median`, d=-0.3765, p=0.3778, q=0.954
- `Trajectory dynamics` / `timescale`: `d_tau_sec`, d=0.5874, p=0.1934, q=0.954
- `Trajectory dynamics` / `other`: `tier2_jacobian_rotation_coherence_mrl`, d=-0.8962, p=0.03548, q=0.8161

#### FEP medicated vs Healthy

- `Adaptive collapse` / `other`: `capture_gate`, d=0.0918, p=0.7361, q=0.8721
- `Global 3D MNPS` / `location`: `d_median`, d=0.5637, p=0.04798, q=0.2676
- `Global 3D MNPS` / `spread`: `m_std`, d=0.3190, p=0.2554, q=0.4198
- `Stratified 9D MNPS` / `location`: `d_l_mean`, d=0.7925, p=0.006497, q=0.09445
- `Stratified 9D MNPS` / `spread`: `d_l_std`, d=0.4143, p=0.1494, q=0.5532
- `Global 3D MNJ` / `jacobian`: `mdr_median`, d=0.4557, p=0.1004, q=1
- `Stratified 9D MNJ` / `jacobian`: `mdr_mean`, d=0.7887, p=0.003498, q=0.06647
- `9x9 block MNJ` / `block_jacobian`: `block_frobenius_mean`, d=0.4916, p=0.09095, q=0.8186
- `Reachability cones` / `reachability`: `tube_d_eff_split_half_n`, d=0.5981, p=0.03448, q=1
- `Trajectory dynamics` / `spread`: `tier2_jacobian_condition_number_mad`, d=-0.2117, p=0.4553, q=0.7915
- `Trajectory dynamics` / `shape`: `m_delta_mean_median`, d=-0.4664, p=0.09595, q=0.6178
- `Trajectory dynamics` / `trajectory`: `path_length`, d=0.4600, p=0.09495, q=0.6178
- `Trajectory dynamics` / `timescale`: `d_tau_sec`, d=-0.3712, p=0.2139, q=0.6178
- `Trajectory dynamics` / `other`: `tier2_jacobian_rotation_coherence_mrl`, d=-0.3566, p=0.2149, q=0.6178

#### FEP unmedicated vs Healthy

- `Adaptive collapse` / `other`: `a_operator_norm`, d=-0.0546, p=0.8851, q=0.934
- `Global 3D MNPS` / `location`: `m_median`, d=0.7424, p=0.06597, q=0.3418
- `Global 3D MNPS` / `spread`: `m_std`, d=0.6366, p=0.1079, q=0.3418
- `Stratified 9D MNPS` / `location`: `e_s_mean`, d=-0.8737, p=0.02949, q=0.4193
- `Stratified 9D MNPS` / `spread`: `m_a_std`, d=0.6936, p=0.08096, q=0.4193
- `Global 3D MNJ` / `jacobian`: `mdr_median`, d=0.6062, p=0.1239, q=1
- `Stratified 9D MNJ` / `jacobian`: `mdr_median`, d=1.0219, p=0.009995, q=0.1899
- `9x9 block MNJ` / `block_jacobian`: `block_trace_mean`, d=-0.9260, p=0.02349, q=0.2114
- `Reachability cones` / `reachability`: `persistence_tau_d_eff_median`, d=-1.0919, p=0.01899, q=1
- `Trajectory dynamics` / `spread`: `tier2_jacobian_condition_number_mad`, d=-0.4466, p=0.2714, q=0.7621
- `Trajectory dynamics` / `shape`: `m_delta_mean_median`, d=-1.3854, p=0.0009995, q=0.02299
- `Trajectory dynamics` / `trajectory`: `curvature_mad`, d=-0.5804, p=0.1574, q=0.7621
- `Trajectory dynamics` / `timescale`: `d_tau_sec`, d=-0.5262, p=0.1949, q=0.7621
- `Trajectory dynamics` / `other`: `tier2_jacobian_condition_number_median`, d=-0.5565, p=0.1679, q=0.7621
