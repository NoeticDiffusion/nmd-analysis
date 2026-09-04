# Parkinson walking contrasts

This pass keeps the design intentionally simple:

- Anchor mode: `auto`
- `HC vs PD` within `rest`
- `HC vs PD` within `walk`
- `rest vs walk` within `HC` and within `PD` for participants with both runs

## Group contrasts

### HC_vs_PD_rest

- `d_s_median`: HC median=0, PD median=0, d=0.4137, p=0.01211, q=0.2578
- `m_e_median`: HC median=0, PD median=0, d=-0.2366, p=0.01394, q=0.2578
- `d_n_median`: HC median=0, PD median=0, d=0.0716, p=0.04032, q=0.3887
- `e_median`: HC median=0.004101, PD median=0.05889, d=0.4074, p=0.04756, q=0.3887
- `m_a_mean`: HC median=-0.1361, PD median=-0.0462, d=0.2933, p=0.05541, q=0.3887
- `m_median`: HC median=-0.04671, PD median=0.01032, d=0.4008, p=0.06431, q=0.3887
- `m_mean`: HC median=-0.02066, PD median=0.02783, d=0.1992, p=0.07355, q=0.3887
- `m_a_median`: HC median=-0.0345, PD median=0.001494, d=0.2993, p=0.1182, q=0.5468

### HC_vs_PD_walk

- `m_e_mean`: HC median=0.05127, PD median=-0.02275, d=-0.3826, p=0.05353, q=0.5806
- `e_s_mean`: HC median=0.01815, PD median=0.1288, d=0.4014, p=0.05655, q=0.5806
- `m_mean`: HC median=0.09082, PD median=0.0268, d=-0.3863, p=0.07477, q=0.5806
- `e_std`: HC median=0.6271, PD median=0.7139, d=0.3561, p=0.09634, q=0.5806
- `d_s_mean`: HC median=0.2907, PD median=0.1913, d=-0.3603, p=0.09996, q=0.5806
- `e_mean`: HC median=0.005569, PD median=0.04273, d=0.3284, p=0.1102, q=0.5806
- `d_l_mean`: HC median=0.1536, PD median=0.02991, d=-0.3109, p=0.1361, q=0.5806
- `jac9_trace_median`: HC median=0.02986, PD median=0.005495, d=-0.2575, p=0.1569, q=0.5806

## Paired task contrasts

### HC_walk_vs_rest

- `m_a_mean`: rest median=-0.146, walk median=0.07362, d=0.8884, p=0.0004752, q=0.01758
- `m_mean`: rest median=-0.007218, walk median=0.09082, d=0.6822, p=0.006033, q=0.08276
- `d_l_mean`: rest median=-0.1328, walk median=0.1536, d=0.6563, p=0.006711, q=0.08276
- `d_mean`: rest median=-0.02498, walk median=0.1381, d=0.634, p=0.01353, q=0.1251
- `jac9_trace_median`: rest median=-0.006713, walk median=0.02986, d=0.4069, p=0.03838, q=0.284
- `e_mean`: rest median=0.09108, walk median=0.005569, d=-0.4409, p=0.06504, q=0.4011
- `m_median`: rest median=-0.04839, walk median=0.00776, d=0.4112, p=0.09175, q=0.4512
- `jac9_rotation_norm_median`: rest median=0.4852, walk median=0.4355, d=-0.3734, p=0.1114, q=0.4512

### PD_walk_vs_rest

- `d_n_mean`: rest median=0.003687, walk median=0.1101, d=0.4089, p=2.806e-05, q=0.001038
- `d_mean`: rest median=-0.01678, walk median=0.07233, d=0.3506, p=0.0003242, q=0.005997
- `jac9_anisotropy_abs_eig_median`: rest median=1.762, walk median=1.821, d=0.2675, p=0.003743, q=0.04616
- `d_std`: rest median=0.7055, walk median=0.7528, d=0.2918, p=0.008566, q=0.07924
- `d_l_mean`: rest median=-0.08952, walk median=0.02991, d=0.2441, p=0.01603, q=0.1186
- `m_a_mean`: rest median=-0.0462, walk median=0.003464, d=0.197, p=0.03095, q=0.1909
- `jac9_spectral_radius_median`: rest median=0.1085, walk median=0.1066, d=-0.1647, p=0.05868, q=0.2512
- `jac9_trace_median`: rest median=-0.004525, walk median=0.005292, d=0.2054, p=0.05912, q=0.2512

