# Parkinson walking clinical associations

This pass keeps the associations deliberately simple:

- Anchor mode: `subject`
- PD participants only
- Spearman correlations
- Separate `rest` and `walk` tables
- BH-FDR within each task x clinical-variable block

## rest

### updrs_part_iii

- `e_e_mean`: rho=0.1976, p=0.0359, q=0.5309, n=113
- `e_median`: rho=0.1857, p=0.0489, q=0.5309, n=113
- `jac9_frobenius_median`: rho=0.1814, p=0.05564, q=0.5309, n=112
- `jac9_rotation_norm_median`: rho=0.1778, p=0.06067, q=0.5309, n=112
- `d_n_mean`: rho=0.1554, p=0.1004, q=0.6448, n=113

### updrs_total

- `jac3_rotation_norm_median`: rho=0.1912, p=0.04246, q=0.732, n=113
- `jac3_frobenius_median`: rho=0.1821, p=0.05356, q=0.732, n=113
- `e_median`: rho=0.1693, p=0.07298, q=0.732, n=113
- `jac3_trace_median`: rho=-0.1491, p=0.1151, q=0.732, n=113
- `jac9_frobenius_median`: rho=0.147, p=0.1219, q=0.732, n=112

### moca

- `e_mean`: rho=-0.3115, p=0.0007842, q=0.02745, n=113
- `d_median`: rho=0.2602, p=0.005377, q=0.07992, n=113
- `m_mean`: rho=0.2473, p=0.008266, q=0.07992, n=113
- `e_s_mean`: rho=-0.2442, p=0.009134, q=0.07992, n=113
- `m_e_mean`: rho=0.2303, p=0.01414, q=0.09895, n=113

### disease_duration

- `d_n_mean`: rho=0.136, p=0.1454, q=0.9986, n=116
- `jac3_anisotropy_abs_eig_median`: rho=-0.1244, p=0.1834, q=0.9986, n=116
- `jac3_trace_median`: rho=-0.1164, p=0.2132, q=0.9986, n=116
- `d_s_median`: rho=-0.1125, p=0.2292, q=0.9986, n=116
- `m_a_mean`: rho=-0.1028, p=0.2722, q=0.9986, n=116

### ledd

- `d_s_median`: rho=-0.1733, p=0.064, q=0.9181, n=115
- `m_o_mean`: rho=0.144, p=0.1246, q=0.9181, n=115
- `e_e_median`: rho=-0.1352, p=0.1495, q=0.9181, n=115
- `m_e_median`: rho=0.134, p=0.1533, q=0.9181, n=115
- `d_l_median`: rho=0.1322, p=0.159, q=0.9181, n=115

### pigd_score

- `e_s_median`: rho=0.1929, p=0.04065, q=0.7652, n=113
- `jac3_frobenius_median`: rho=0.1781, p=0.05911, q=0.7652, n=113
- `jac3_rotation_norm_median`: rho=0.1738, p=0.06559, q=0.7652, n=113
- `jac9_frobenius_median`: rho=0.1298, p=0.1726, q=0.8297, n=112
- `m_o_median`: rho=-0.1258, p=0.1842, q=0.8297, n=113

### td_score

- `jac9_trace_median`: rho=-0.2352, p=0.01256, q=0.4397, n=112
- `m_median`: rho=0.1791, p=0.05771, q=0.9543, n=113
- `jac3_anisotropy_abs_eig_median`: rho=0.1417, p=0.1344, q=0.9543, n=113
- `d_n_mean`: rho=0.1313, p=0.1658, q=0.9543, n=113
- `m_a_median`: rho=0.1127, p=0.2347, q=0.9543, n=113

### ctt

- `e_mean`: rho=0.2869, p=0.002489, q=0.08268, n=109
- `m_a_mean`: rho=-0.2679, p=0.004864, q=0.08268, n=109
- `e_s_mean`: rho=0.2352, p=0.01383, q=0.1395, n=109
- `m_a_median`: rho=-0.2294, p=0.01641, q=0.1395, n=109
- `m_mean`: rho=-0.2101, p=0.02834, q=0.1927, n=109

### age

- `jac9_spectral_radius_median`: rho=-0.1546, p=0.09889, q=0.912, n=115
- `e_std`: rho=0.1339, p=0.1517, q=0.912, n=116
- `e_median`: rho=0.1333, p=0.1538, q=0.912, n=116
- `e_e_mean`: rho=0.1227, p=0.1895, q=0.912, n=116
- `m_a_mean`: rho=-0.1224, p=0.1904, q=0.912, n=116

## walk

### updrs_part_iii

- `jac9_spectral_radius_median`: rho=-0.1724, p=0.07444, q=0.979, n=108
- `m_e_mean`: rho=-0.127, p=0.1904, q=0.979, n=108
- `jac9_rotation_norm_median`: rho=-0.1257, p=0.1949, q=0.979, n=108
- `jac9_frobenius_median`: rho=-0.101, p=0.2984, q=0.979, n=108
- `m_mean`: rho=-0.09304, p=0.3382, q=0.979, n=108

### updrs_total

- `m_mean`: rho=-0.1476, p=0.1273, q=0.9747, n=108
- `jac9_rotation_norm_median`: rho=-0.1474, p=0.128, q=0.9747, n=108
- `m_e_mean`: rho=-0.1408, p=0.146, q=0.9747, n=108
- `jac9_frobenius_median`: rho=-0.1336, p=0.168, q=0.9747, n=108
- `m_a_mean`: rho=-0.1094, p=0.2596, q=0.9747, n=108

### moca

- `jac9_spectral_radius_median`: rho=0.1783, p=0.0648, q=0.9093, n=108
- `m_o_mean`: rho=-0.1659, p=0.08623, q=0.9093, n=108
- `m_a_median`: rho=-0.1357, p=0.1616, q=0.9093, n=108
- `jac3_frobenius_median`: rho=0.1333, p=0.1691, q=0.9093, n=108
- `jac9_rotation_norm_median`: rho=0.1292, p=0.1828, q=0.9093, n=108

### disease_duration

- `jac3_spectral_radius_median`: rho=0.1532, p=0.1101, q=0.9224, n=110
- `e_m_mean`: rho=-0.1487, p=0.1211, q=0.9224, n=110
- `e_mean`: rho=-0.1424, p=0.1378, q=0.9224, n=110
- `d_std`: rho=0.1231, p=0.2003, q=0.9224, n=110
- `jac9_trace_median`: rho=-0.1028, p=0.2852, q=0.9224, n=110

### ledd

- `m_median`: rho=0.1518, p=0.1135, q=0.9146, n=110
- `e_e_mean`: rho=-0.1366, p=0.1546, q=0.9146, n=110
- `d_std`: rho=0.1208, p=0.2088, q=0.9146, n=110
- `e_mean`: rho=-0.1102, p=0.2517, q=0.9146, n=110
- `jac3_anisotropy_abs_eig_median`: rho=-0.1081, p=0.2609, q=0.9146, n=110

### pigd_score

- `jac9_spectral_radius_median`: rho=-0.1749, p=0.07025, q=0.6989, n=108
- `jac3_anisotropy_abs_eig_median`: rho=-0.172, p=0.07504, q=0.6989, n=108
- `jac9_rotation_norm_median`: rho=-0.1537, p=0.1123, q=0.6989, n=108
- `m_a_median`: rho=-0.1358, p=0.1612, q=0.6989, n=108
- `d_std`: rho=-0.1351, p=0.1634, q=0.6989, n=108

### td_score

- `m_std`: rho=-0.1816, p=0.06, q=0.9775, n=108
- `m_o_mean`: rho=-0.1616, p=0.09484, q=0.9775, n=108
- `jac9_anisotropy_abs_eig_median`: rho=0.1494, p=0.1227, q=0.9775, n=108
- `jac3_anisotropy_abs_eig_median`: rho=0.1448, p=0.1348, q=0.9775, n=108
- `e_e_mean`: rho=0.1137, p=0.2412, q=0.9827, n=108

### ctt

- `jac9_spectral_radius_median`: rho=-0.231, p=0.01833, q=0.5316, n=104
- `jac3_frobenius_median`: rho=-0.1745, p=0.07647, q=0.5795, n=104
- `m_o_mean`: rho=0.1721, p=0.08074, q=0.5795, n=104
- `m_mean`: rho=0.1659, p=0.09244, q=0.5795, n=104
- `jac3_rotation_norm_median`: rho=-0.1559, p=0.1141, q=0.5795, n=104

### age

- `jac9_spectral_radius_median`: rho=-0.3289, p=0.000452, q=0.01311, n=110
- `e_m_mean`: rho=-0.2175, p=0.02248, q=0.3259, n=110
- `d_s_mean`: rho=-0.1675, p=0.08034, q=0.6637, n=110
- `d_median`: rho=-0.1401, p=0.1445, q=0.6637, n=110
- `d_mean`: rho=-0.1372, p=0.1531, q=0.6637, n=110

