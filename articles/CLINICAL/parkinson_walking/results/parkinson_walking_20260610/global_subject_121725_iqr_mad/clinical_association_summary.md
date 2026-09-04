# Parkinson walking clinical associations

This pass keeps the associations deliberately simple:

- Anchor mode: `subject`
- PD participants only
- Spearman correlations
- Separate `rest` and `walk` tables
- BH-FDR within each task x clinical-variable block

## rest

### updrs_part_iii

- `m_o_mad`: rho=-0.2525, p=0.006965, q=0.5433, n=113
- `e_e_mean`: rho=0.1976, p=0.0359, q=0.7887, n=113
- `e_e_iqr`: rho=0.1892, p=0.0447, q=0.7887, n=113
- `e_median`: rho=0.1857, p=0.0489, q=0.7887, n=113
- `jac9_frobenius_median`: rho=0.1814, p=0.05564, q=0.7887, n=112

### updrs_total

- `jac3_rotation_norm_median`: rho=0.1912, p=0.04246, q=0.8927, n=113
- `m_o_mad`: rho=-0.184, p=0.05104, q=0.8927, n=113
- `jac3_frobenius_median`: rho=0.1821, p=0.05356, q=0.8927, n=113
- `e_e_iqr`: rho=0.1787, p=0.05823, q=0.8927, n=113
- `e_median`: rho=0.1693, p=0.07298, q=0.8927, n=113

### moca

- `e_mean`: rho=-0.3115, p=0.0007842, q=0.06117, n=113
- `d_median`: rho=0.2602, p=0.005377, q=0.1781, n=113
- `m_mean`: rho=0.2473, p=0.008266, q=0.1781, n=113
- `e_s_mean`: rho=-0.2442, p=0.009134, q=0.1781, n=113
- `m_e_mean`: rho=0.2303, p=0.01414, q=0.1949, n=113

### disease_duration

- `d_mad`: rho=0.1574, p=0.09148, q=0.9986, n=116
- `m_e_iqr`: rho=0.1524, p=0.1023, q=0.9986, n=116
- `jac3_spectral_radius_iqr`: rho=-0.1396, p=0.135, q=0.9986, n=116
- `d_n_mean`: rho=0.136, p=0.1454, q=0.9986, n=116
- `m_mad`: rho=-0.1336, p=0.1529, q=0.9986, n=116

### ledd

- `e_s_mad`: rho=0.2103, p=0.02405, q=0.9003, n=115
- `d_s_median`: rho=-0.1733, p=0.064, q=0.9003, n=115
- `m_e_iqr`: rho=0.1551, p=0.09787, q=0.9003, n=115
- `e_e_mad`: rho=0.1528, p=0.103, q=0.9003, n=115
- `m_o_mean`: rho=0.144, p=0.1246, q=0.9003, n=115

### pigd_score

- `m_o_mad`: rho=-0.2148, p=0.02235, q=0.7493, n=113
- `e_s_median`: rho=0.1929, p=0.04065, q=0.7493, n=113
- `jac9_trace_iqr`: rho=-0.1855, p=0.05025, q=0.7493, n=112
- `jac3_frobenius_median`: rho=0.1781, p=0.05911, q=0.7493, n=113
- `jac3_rotation_norm_median`: rho=0.1738, p=0.06559, q=0.7493, n=113

### td_score

- `jac9_trace_median`: rho=-0.2352, p=0.01256, q=0.9545, n=112
- `m_median`: rho=0.1791, p=0.05771, q=0.9545, n=113
- `e_e_iqr`: rho=0.1641, p=0.08234, q=0.9545, n=113
- `d_s_mad`: rho=-0.1632, p=0.08408, q=0.9545, n=113
- `e_s_mad`: rho=-0.1568, p=0.09729, q=0.9545, n=113

### ctt

- `e_mean`: rho=0.2869, p=0.002489, q=0.1873, n=109
- `m_a_mean`: rho=-0.2679, p=0.004864, q=0.1873, n=109
- `e_s_mean`: rho=0.2352, p=0.01383, q=0.3159, n=109
- `m_a_median`: rho=-0.2294, p=0.01641, q=0.3159, n=109
- `m_mean`: rho=-0.2101, p=0.02834, q=0.4364, n=109

### age

- `jac9_spectral_radius_median`: rho=-0.1546, p=0.09889, q=0.9239, n=115
- `e_e_mad`: rho=-0.152, p=0.1033, q=0.9239, n=116
- `e_s_mad`: rho=0.1458, p=0.1184, q=0.9239, n=116
- `e_std`: rho=0.1339, p=0.1517, q=0.9239, n=116
- `d_l_iqr`: rho=-0.1333, p=0.1537, q=0.9239, n=116

## walk

### updrs_part_iii

- `m_e_iqr`: rho=0.1945, p=0.04369, q=0.993, n=108
- `d_l_mad`: rho=0.1842, p=0.05636, q=0.993, n=108
- `jac9_spectral_radius_median`: rho=-0.1724, p=0.07444, q=0.993, n=108
- `jac9_trace_mad`: rho=0.1575, p=0.1034, q=0.993, n=108
- `jac9_trace_iqr`: rho=0.1523, p=0.1155, q=0.993, n=108

### updrs_total

- `m_o_iqr`: rho=-0.1833, p=0.05756, q=0.9447, n=108
- `d_s_iqr`: rho=-0.1719, p=0.0753, q=0.9447, n=108
- `d_l_mad`: rho=0.1593, p=0.09954, q=0.9447, n=108
- `m_mean`: rho=-0.1476, p=0.1273, q=0.9447, n=108
- `jac9_rotation_norm_median`: rho=-0.1474, p=0.128, q=0.9447, n=108

### moca

- `jac9_spectral_radius_median`: rho=0.1783, p=0.0648, q=0.9069, n=108
- `m_o_mean`: rho=-0.1659, p=0.08623, q=0.9069, n=108
- `m_a_median`: rho=-0.1357, p=0.1616, q=0.9069, n=108
- `jac3_frobenius_median`: rho=0.1333, p=0.1691, q=0.9069, n=108
- `jac9_rotation_norm_median`: rho=0.1292, p=0.1828, q=0.9069, n=108

### disease_duration

- `d_s_iqr`: rho=-0.2389, p=0.01196, q=0.7543, n=110
- `m_e_mad`: rho=-0.2195, p=0.02125, q=0.7543, n=110
- `d_l_mad`: rho=0.1692, p=0.07715, q=0.8849, n=110
- `m_a_iqr`: rho=-0.1615, p=0.09192, q=0.8849, n=110
- `jac3_spectral_radius_median`: rho=0.1532, p=0.1101, q=0.8849, n=110

### ledd

- `d_s_iqr`: rho=-0.2406, p=0.01133, q=0.8045, n=110
- `m_e_iqr`: rho=0.1551, p=0.1056, q=0.9799, n=110
- `jac3_trace_iqr`: rho=-0.1544, p=0.1072, q=0.9799, n=110
- `m_median`: rho=0.1518, p=0.1135, q=0.9799, n=110
- `jac3_trace_mad`: rho=-0.1507, p=0.1162, q=0.9799, n=110

### pigd_score

- `jac3_spectral_radius_iqr`: rho=-0.184, p=0.05656, q=0.9337, n=108
- `jac9_spectral_radius_median`: rho=-0.1749, p=0.07025, q=0.9337, n=108
- `jac3_spectral_radius_mad`: rho=-0.1733, p=0.07289, q=0.9337, n=108
- `jac3_anisotropy_abs_eig_median`: rho=-0.172, p=0.07504, q=0.9337, n=108
- `d_s_iqr`: rho=-0.1587, p=0.1009, q=0.9337, n=108

### td_score

- `d_l_mad`: rho=0.2952, p=0.001923, q=0.1365, n=108
- `m_o_iqr`: rho=-0.2266, p=0.01835, q=0.6515, n=108
- `jac3_trace_mad`: rho=-0.1944, p=0.04381, q=0.852, n=108
- `jac3_trace_iqr`: rho=-0.1881, p=0.05122, q=0.852, n=108
- `m_std`: rho=-0.1816, p=0.06, q=0.852, n=108

### ctt

- `m_a_iqr`: rho=-0.2488, p=0.01086, q=0.4339, n=104
- `jac3_frobenius_mad`: rho=-0.2329, p=0.01734, q=0.4339, n=104
- `jac9_spectral_radius_median`: rho=-0.231, p=0.01833, q=0.4339, n=104
- `jac3_frobenius_median`: rho=-0.1745, p=0.07647, q=0.7652, n=104
- `m_o_mean`: rho=0.1721, p=0.08074, q=0.7652, n=104

### age

- `jac9_spectral_radius_median`: rho=-0.3289, p=0.000452, q=0.03209, n=110
- `e_m_mean`: rho=-0.2175, p=0.02248, q=0.798, n=110
- `d_s_mean`: rho=-0.1675, p=0.08034, q=0.935, n=110
- `d_l_mad`: rho=0.1528, p=0.111, q=0.935, n=110
- `d_median`: rho=-0.1401, p=0.1445, q=0.935, n=110

