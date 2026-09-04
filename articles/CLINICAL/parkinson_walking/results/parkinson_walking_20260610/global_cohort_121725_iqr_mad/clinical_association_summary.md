# Parkinson walking clinical associations

This pass keeps the associations deliberately simple:

- Anchor mode: `cohort`
- PD participants only
- Spearman correlations
- Separate `rest` and `walk` tables
- BH-FDR within each task x clinical-variable block

## rest

### updrs_part_iii

- `d_s_median`: rho=-0.3444, p=0.0001879, q=0.01324, n=113
- `d_s_mean`: rho=-0.3321, p=0.0003269, q=0.01324, n=113
- `m_o_mean`: rho=0.2252, p=0.01645, q=0.3987, n=113
- `d_s_iqr`: rho=-0.2187, p=0.01998, q=0.3987, n=113
- `m_o_median`: rho=0.2114, p=0.02461, q=0.3987, n=113

### updrs_total

- `d_s_median`: rho=-0.2739, p=0.003327, q=0.1452, n=113
- `d_s_mean`: rho=-0.2718, p=0.003586, q=0.1452, n=113
- `d_n_mean`: rho=0.1982, p=0.03539, q=0.7317, n=113
- `m_o_mean`: rho=0.1974, p=0.03613, q=0.7317, n=113
- `m_o_median`: rho=0.1836, p=0.05156, q=0.8179, n=113

### moca

- `d_s_mean`: rho=0.3513, p=0.0001363, q=0.01104, n=113
- `d_s_median`: rho=0.3334, p=0.0003077, q=0.01246, n=113
- `m_o_mean`: rho=-0.321, p=0.0005276, q=0.01425, n=113
- `m_o_median`: rho=-0.3129, p=0.0007406, q=0.015, n=113
- `jac9_rotation_norm_mad`: rho=0.2352, p=0.01256, q=0.1679, n=112

### disease_duration

- `jac3_trace_median`: rho=-0.2241, p=0.01558, q=0.5991, n=116
- `d_s_median`: rho=-0.2192, p=0.01805, q=0.5991, n=116
- `d_s_mean`: rho=-0.2044, p=0.02774, q=0.5991, n=116
- `d_s_mad`: rho=-0.1949, p=0.03608, q=0.5991, n=116
- `e_mean`: rho=0.1855, p=0.04616, q=0.5991, n=116

### ledd

- `jac3_trace_median`: rho=-0.223, p=0.01659, q=0.7651, n=115
- `e_mean`: rho=0.1853, p=0.04741, q=0.7651, n=115
- `e_e_mean`: rho=0.1841, p=0.04884, q=0.7651, n=115
- `e_e_median`: rho=0.1827, p=0.05061, q=0.7651, n=115
- `e_median`: rho=0.1798, p=0.05452, q=0.7651, n=115

### pigd_score

- `d_s_mean`: rho=-0.1531, p=0.1056, q=0.9652, n=113
- `d_s_median`: rho=-0.1505, p=0.1117, q=0.9652, n=113
- `d_n_mean`: rho=0.1491, p=0.1151, q=0.9652, n=113
- `d_mad`: rho=-0.1438, p=0.1286, q=0.9652, n=113
- `d_iqr`: rho=-0.1437, p=0.1289, q=0.9652, n=113

### td_score

- `d_s_iqr`: rho=-0.2308, p=0.01392, q=0.6807, n=113
- `jac3_trace_median`: rho=-0.2245, p=0.01681, q=0.6807, n=113
- `d_s_mad`: rho=-0.1908, p=0.04294, q=0.7182, n=113
- `d_l_mad`: rho=-0.168, p=0.0753, q=0.7182, n=113
- `jac9_frobenius_iqr`: rho=0.1686, p=0.07563, q=0.7182, n=112

### ctt

- `d_s_mean`: rho=-0.4148, p=7.298e-06, q=0.0005911, n=109
- `d_s_median`: rho=-0.3987, p=1.75e-05, q=0.0007089, n=109
- `d_s_iqr`: rho=-0.3512, p=0.000181, q=0.004886, n=109
- `m_o_median`: rho=0.3319, p=0.0004219, q=0.007747, n=109
- `m_o_mean`: rho=0.329, p=0.0004782, q=0.007747, n=109

### age

- `d_s_mean`: rho=-0.4031, p=7.238e-06, q=0.0005863, n=116
- `d_s_median`: rho=-0.3789, p=2.733e-05, q=0.0008377, n=116
- `d_s_iqr`: rho=-0.3765, p=3.103e-05, q=0.0008377, n=116
- `d_s_mad`: rho=-0.3323, p=0.000268, q=0.005427, n=116
- `m_o_mean`: rho=0.2864, p=0.00183, q=0.02964, n=116

## walk

### updrs_part_iii

- `m_e_mean`: rho=-0.1776, p=0.06587, q=0.8553, n=108
- `d_n_median`: rho=0.1705, p=0.07767, q=0.8553, n=108
- `m_o_iqr`: rho=-0.17, p=0.07856, q=0.8553, n=108
- `jac9_spectral_radius_median`: rho=-0.171, p=0.08114, q=0.8553, n=105
- `d_n_mean`: rho=0.1678, p=0.08253, q=0.8553, n=108

### updrs_total

- `d_n_median`: rho=0.2181, p=0.02339, q=0.5402, n=108
- `d_n_mean`: rho=0.2094, p=0.02965, q=0.5402, n=108
- `m_e_mad`: rho=-0.2084, p=0.0304, q=0.5402, n=108
- `d_median`: rho=0.2044, p=0.03382, q=0.5402, n=108
- `d_mean`: rho=0.1901, p=0.04871, q=0.5402, n=108

### moca

- `d_s_iqr`: rho=0.2955, p=0.001904, q=0.1543, n=108
- `m_a_mean`: rho=0.2674, p=0.005144, q=0.1994, n=108
- `d_s_mad`: rho=0.254, p=0.00798, q=0.1994, n=108
- `m_a_median`: rho=0.2419, p=0.01165, q=0.1994, n=108
- `d_s_mean`: rho=0.2353, p=0.01424, q=0.1994, n=108

### disease_duration

- `e_std`: rho=-0.2984, p=0.001546, q=0.0635, n=110
- `e_iqr`: rho=-0.298, p=0.001568, q=0.0635, n=110
- `e_mad`: rho=-0.2404, p=0.01142, q=0.3083, n=110
- `e_m_mad`: rho=0.213, p=0.02547, q=0.5157, n=110
- `d_s_iqr`: rho=-0.1941, p=0.04214, q=0.5234, n=110

### ledd

- `jac9_rotation_norm_iqr`: rho=0.1687, p=0.08246, q=0.9858, n=107
- `d_n_median`: rho=0.1634, p=0.08804, q=0.9858, n=110
- `jac9_frobenius_iqr`: rho=0.1587, p=0.1025, q=0.9858, n=107
- `d_n_mean`: rho=0.1542, p=0.1077, q=0.9858, n=110
- `jac9_rotation_norm_mad`: rho=0.1535, p=0.1145, q=0.9858, n=107

### pigd_score

- `m_e_mean`: rho=-0.3147, p=0.0009095, q=0.03492, n=108
- `m_e_median`: rho=-0.3079, p=0.001189, q=0.03492, n=108
- `d_n_median`: rho=0.2992, p=0.00166, q=0.03492, n=108
- `d_n_mean`: rho=0.2981, p=0.001725, q=0.03492, n=108
- `m_mean`: rho=-0.2134, p=0.02661, q=0.4133, n=108

### td_score

- `jac3_anisotropy_abs_eig_median`: rho=0.234, p=0.01478, q=0.9054, n=108
- `m_e_mad`: rho=-0.1936, p=0.04466, q=0.9054, n=108
- `d_s_mean`: rho=0.1869, p=0.05279, q=0.9054, n=108
- `m_e_iqr`: rho=-0.1817, p=0.05984, q=0.9054, n=108
- `d_s_iqr`: rho=0.1747, p=0.07058, q=0.9054, n=108

### ctt

- `m_median`: rho=-0.2874, p=0.003092, q=0.1424, n=104
- `m_mean`: rho=-0.2837, p=0.003517, q=0.1424, n=104
- `d_s_iqr`: rho=-0.271, p=0.005398, q=0.1457, n=104
- `m_o_median`: rho=-0.2552, p=0.008922, q=0.149, n=104
- `m_o_mean`: rho=-0.2543, p=0.009197, q=0.149, n=104

### age

- `jac9_spectral_radius_median`: rho=-0.3182, p=0.0008381, q=0.06789, n=107
- `jac3_trace_median`: rho=0.2622, p=0.00565, q=0.2206, n=110
- `jac9_frobenius_median`: rho=-0.2419, p=0.01206, q=0.2206, n=107
- `jac9_rotation_norm_median`: rho=-0.2396, p=0.01291, q=0.2206, n=107
- `e_m_mad`: rho=0.2346, p=0.01362, q=0.2206, n=110

