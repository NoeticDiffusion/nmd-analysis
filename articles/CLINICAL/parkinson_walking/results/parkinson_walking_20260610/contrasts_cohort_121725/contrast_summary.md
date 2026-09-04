# Parkinson walking contrasts

This pass keeps the design intentionally simple:

- Anchor mode: `cohort`
- `HC vs PD` within `rest`
- `HC vs PD` within `walk`
- `rest vs walk` within `HC` and within `PD` for participants with both runs

## Group contrasts

### HC_vs_PD_rest

- `d_std`: HC median=0.4513, PD median=0.3103, d=-0.4781, p=0.001956, q=0.07238
- `m_std`: HC median=0.5298, PD median=0.4455, d=-0.5328, p=0.0201, q=0.3718
- `e_std`: HC median=0.2837, PD median=0.2423, d=-0.5211, p=0.04589, q=0.5222
- `jac3_spectral_radius_median`: HC median=0.06326, PD median=0.05757, d=-0.3925, p=0.07355, q=0.5222
- `d_s_mean`: HC median=1.368, PD median=0.5836, d=-0.3269, p=0.08204, q=0.5222
- `d_s_median`: HC median=0.8185, PD median=0.518, d=-0.3213, p=0.08467, q=0.5222
- `m_a_mean`: HC median=1.15, PD median=0.8898, d=-0.2746, p=0.1495, q=0.7671
- `m_a_median`: HC median=1.167, PD median=0.8931, d=-0.2706, p=0.1659, q=0.7671

### HC_vs_PD_walk

- `d_n_mean`: HC median=0.1791, PD median=1.003, d=0.7658, p=0.001223, q=0.03018
- `d_n_median`: HC median=0.08343, PD median=0.9874, d=0.746, p=0.001631, q=0.03018
- `d_mean`: HC median=-0.8733, PD median=0.04965, d=0.7109, p=0.002961, q=0.03581
- `d_median`: HC median=-1.021, PD median=-0.008324, d=0.7185, p=0.003871, q=0.03581
- `d_s_median`: HC median=-1.32, PD median=-0.9887, d=0.4768, p=0.02471, q=0.1696
- `d_s_mean`: HC median=-1.154, PD median=-0.848, d=0.4648, p=0.0275, q=0.1696
- `m_e_mean`: HC median=0.2718, PD median=-0.1057, d=-0.4444, p=0.03545, q=0.1874
- `m_e_median`: HC median=0.2763, PD median=-0.06727, d=-0.4166, p=0.04593, q=0.2124

## Paired task contrasts

### HC_walk_vs_rest

- `d_s_mean`: rest median=1.774, walk median=-1.154, d=-1.432, p=4.768e-07, q=8.821e-06
- `d_s_median`: rest median=1.557, walk median=-1.32, d=-1.33, p=4.768e-07, q=8.821e-06
- `m_a_median`: rest median=1.12, walk median=-1.52, d=-1.523, p=2.384e-06, q=1.764e-05
- `m_a_mean`: rest median=1.059, walk median=-1.046, d=-1.489, p=2.384e-06, q=1.764e-05
- `e_s_mean`: rest median=-0.4264, walk median=1.413, d=1.188, p=2.384e-06, q=1.764e-05
- `e_s_median`: rest median=-0.4987, walk median=1.644, d=1.163, p=3.338e-06, q=2.058e-05
- `d_l_median`: rest median=0.6034, walk median=-1.312, d=-1.353, p=4.53e-06, q=2.394e-05
- `d_l_mean`: rest median=0.4206, walk median=-1.318, d=-1.297, p=1.025e-05, q=4.742e-05

### PD_walk_vs_rest

- `d_n_mean`: rest median=-0.7591, walk median=1.003, d=1.043, p=8.658e-18, q=2.302e-16
- `m_a_mean`: rest median=0.8898, walk median=-0.9255, d=-1.155, p=1.244e-17, q=2.302e-16
- `d_n_median`: rest median=-0.7531, walk median=0.9874, d=0.9974, p=2.69e-17, q=3.318e-16
- `m_a_median`: rest median=0.8931, walk median=-1.076, d=-1.118, p=8.012e-17, q=7.411e-16
- `d_s_mean`: rest median=0.5897, walk median=-0.848, d=-1.019, p=3.24e-16, q=2.397e-15
- `d_s_median`: rest median=0.5338, walk median=-0.9887, d=-0.9573, p=9.525e-16, q=5.874e-15
- `e_std`: rest median=0.2417, walk median=0.4153, d=0.7344, p=3.255e-15, q=1.72e-14
- `e_median`: rest median=-0.219, walk median=0.4976, d=0.7799, p=2.827e-12, q=1.308e-11

