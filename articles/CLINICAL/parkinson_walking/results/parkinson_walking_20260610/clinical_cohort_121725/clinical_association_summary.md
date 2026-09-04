# Parkinson walking clinical associations

This pass keeps the associations deliberately simple:

- Anchor mode: `cohort`
- PD participants only
- Spearman correlations
- Separate `rest` and `walk` tables
- BH-FDR within each task x clinical-variable block

## rest

### updrs_part_iii

- `d_s_median`: rho=-0.3444, p=0.0001879, q=0.006047, n=113
- `d_s_mean`: rho=-0.3321, p=0.0003269, q=0.006047, n=113
- `m_o_mean`: rho=0.2252, p=0.01645, q=0.2029, n=113
- `m_o_median`: rho=0.2114, p=0.02461, q=0.2277, n=113
- `d_n_mean`: rho=0.1832, p=0.05206, q=0.3852, n=113

### updrs_total

- `d_s_median`: rho=-0.2739, p=0.003327, q=0.06634, n=113
- `d_s_mean`: rho=-0.2718, p=0.003586, q=0.06634, n=113
- `d_n_mean`: rho=0.1982, p=0.03539, q=0.3342, n=113
- `m_o_mean`: rho=0.1974, p=0.03613, q=0.3342, n=113
- `m_o_median`: rho=0.1836, p=0.05156, q=0.3816, n=113

### moca

- `d_s_mean`: rho=0.3513, p=0.0001363, q=0.005042, n=113
- `d_s_median`: rho=0.3334, p=0.0003077, q=0.005693, n=113
- `m_o_mean`: rho=-0.321, p=0.0005276, q=0.006507, n=113
- `m_o_median`: rho=-0.3129, p=0.0007406, q=0.006851, n=113
- `jac3_rotation_norm_median`: rho=-0.225, p=0.01659, q=0.1227, n=113

### disease_duration

- `jac3_trace_median`: rho=-0.2241, p=0.01558, q=0.33, n=116
- `d_s_median`: rho=-0.2192, p=0.01805, q=0.33, n=116
- `d_s_mean`: rho=-0.2044, p=0.02774, q=0.33, n=116
- `e_mean`: rho=0.1855, p=0.04616, q=0.33, n=116
- `m_o_median`: rho=0.1797, p=0.05354, q=0.33, n=116

### ledd

- `jac3_trace_median`: rho=-0.223, p=0.01659, q=0.3495, n=115
- `e_mean`: rho=0.1853, p=0.04741, q=0.3495, n=115
- `e_e_mean`: rho=0.1841, p=0.04884, q=0.3495, n=115
- `e_e_median`: rho=0.1827, p=0.05061, q=0.3495, n=115
- `e_median`: rho=0.1798, p=0.05452, q=0.3495, n=115

### pigd_score

- `d_s_mean`: rho=-0.1531, p=0.1056, q=0.6762, n=113
- `d_s_median`: rho=-0.1505, p=0.1117, q=0.6762, n=113
- `d_n_mean`: rho=0.1491, p=0.1151, q=0.6762, n=113
- `e_median`: rho=-0.1368, p=0.1485, q=0.6762, n=113
- `d_n_median`: rho=0.1356, p=0.152, q=0.6762, n=113

### td_score

- `jac3_trace_median`: rho=-0.2245, p=0.01681, q=0.6219, n=113
- `d_n_mean`: rho=0.1551, p=0.1009, q=0.7128, n=113
- `jac9_rotation_norm_median`: rho=0.1473, p=0.1212, q=0.7128, n=112
- `jac9_frobenius_median`: rho=0.1468, p=0.1224, q=0.7128, n=112
- `jac9_trace_median`: rho=-0.1463, p=0.1237, q=0.7128, n=112

### ctt

- `d_s_mean`: rho=-0.4148, p=7.298e-06, q=0.00027, n=109
- `d_s_median`: rho=-0.3987, p=1.75e-05, q=0.0003238, n=109
- `m_o_median`: rho=0.3319, p=0.0004219, q=0.004424, n=109
- `m_o_mean`: rho=0.329, p=0.0004782, q=0.004424, n=109
- `d_mean`: rho=-0.2549, p=0.007487, q=0.04822, n=109

### age

- `d_s_mean`: rho=-0.4031, p=7.238e-06, q=0.0002678, n=116
- `d_s_median`: rho=-0.3789, p=2.733e-05, q=0.0005055, n=116
- `m_o_mean`: rho=0.2864, p=0.00183, q=0.02257, n=116
- `m_o_median`: rho=0.2749, p=0.002819, q=0.02607, n=116
- `jac9_frobenius_median`: rho=-0.2371, p=0.01072, q=0.06613, n=115

## walk

### updrs_part_iii

- `m_e_mean`: rho=-0.1776, p=0.06587, q=0.4709, n=108
- `d_n_median`: rho=0.1705, p=0.07767, q=0.4709, n=108
- `jac9_spectral_radius_median`: rho=-0.171, p=0.08114, q=0.4709, n=105
- `d_n_mean`: rho=0.1678, p=0.08253, q=0.4709, n=108
- `d_median`: rho=0.1643, p=0.08922, q=0.4709, n=108

### updrs_total

- `d_n_median`: rho=0.2181, p=0.02339, q=0.3619, n=108
- `d_n_mean`: rho=0.2094, p=0.02965, q=0.3619, n=108
- `d_median`: rho=0.2044, p=0.03382, q=0.3619, n=108
- `d_mean`: rho=0.1901, p=0.04871, q=0.3619, n=108
- `d_l_median`: rho=0.1766, p=0.06752, q=0.3619, n=108

### moca

- `m_a_mean`: rho=0.2674, p=0.005144, q=0.1367, n=108
- `m_a_median`: rho=0.2419, p=0.01165, q=0.1367, n=108
- `d_s_mean`: rho=0.2353, p=0.01424, q=0.1367, n=108
- `jac9_spectral_radius_median`: rho=0.2373, p=0.01477, q=0.1367, n=105
- `m_mean`: rho=0.2035, p=0.03462, q=0.2289, n=108

### disease_duration

- `e_std`: rho=-0.2984, p=0.001546, q=0.05721, n=110
- `d_n_median`: rho=0.1897, p=0.0471, q=0.6376, n=110
- `d_n_mean`: rho=0.186, p=0.05169, q=0.6376, n=110
- `e_m_median`: rho=0.162, p=0.09081, q=0.7689, n=110
- `jac3_anisotropy_abs_eig_median`: rho=0.1515, p=0.1142, q=0.7689, n=110

### ledd

- `d_n_median`: rho=0.1634, p=0.08804, q=0.9545, n=110
- `d_n_mean`: rho=0.1542, p=0.1077, q=0.9545, n=110
- `m_e_mean`: rho=-0.1283, p=0.1817, q=0.9545, n=110
- `m_e_median`: rho=-0.1193, p=0.2146, q=0.9545, n=110
- `jac3_rotation_norm_median`: rho=0.1128, p=0.2406, q=0.9545, n=110

### pigd_score

- `m_e_mean`: rho=-0.3147, p=0.0009095, q=0.01595, n=108
- `m_e_median`: rho=-0.3079, p=0.001189, q=0.01595, n=108
- `d_n_median`: rho=0.2992, p=0.00166, q=0.01595, n=108
- `d_n_mean`: rho=0.2981, p=0.001725, q=0.01595, n=108
- `m_mean`: rho=-0.2134, p=0.02661, q=0.1888, n=108

### td_score

- `jac3_anisotropy_abs_eig_median`: rho=0.234, p=0.01478, q=0.5469, n=108
- `d_s_mean`: rho=0.1869, p=0.05279, q=0.7253, n=108
- `d_s_median`: rho=0.1631, p=0.09171, q=0.7253, n=108
- `jac3_trace_median`: rho=0.149, p=0.1238, q=0.7253, n=108
- `jac9_anisotropy_abs_eig_median`: rho=0.1467, p=0.1352, q=0.7253, n=105

### ctt

- `m_median`: rho=-0.2874, p=0.003092, q=0.06506, n=104
- `m_mean`: rho=-0.2837, p=0.003517, q=0.06506, n=104
- `m_o_median`: rho=-0.2552, p=0.008922, q=0.08508, n=104
- `m_o_mean`: rho=-0.2543, p=0.009197, q=0.08508, n=104
- `m_e_median`: rho=-0.2459, p=0.01187, q=0.08782, n=104

### age

- `jac9_spectral_radius_median`: rho=-0.3182, p=0.0008381, q=0.03101, n=107
- `jac3_trace_median`: rho=0.2622, p=0.00565, q=0.1045, n=110
- `jac9_frobenius_median`: rho=-0.2419, p=0.01206, q=0.1195, n=107
- `jac9_rotation_norm_median`: rho=-0.2396, p=0.01291, q=0.1195, n=107
- `e_m_median`: rho=0.1901, p=0.04665, q=0.2721, n=110

