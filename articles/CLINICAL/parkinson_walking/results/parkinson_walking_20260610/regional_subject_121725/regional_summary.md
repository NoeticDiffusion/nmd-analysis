# Parkinson walking regional analysis

- Anchor mode: `subject`
- Reachability present in bundle: `False`
- Regional source spaces: 3D MNPS, 9D stratified coordinates, and regional 3D Jacobian summaries
- Group test: HC vs PD within task via Mann-Whitney U
- Clinical test: PD-only Spearman rho per task

## Top HC vs PD regional rows

- `rest` / `central` / `e_s_mean`: HC median=0.1453, PD median=0.05619, d=-0.4589, p=0.00224, q=0.2098
- `rest` / `parietal_occipital` / `e_std`: HC median=0.9215, PD median=0.7818, d=-0.6327, p=0.003279, q=0.2098
- `rest` / `central` / `e_s_median`: HC median=0, PD median=0, d=0.2572, p=0.008747, q=0.3042
- `rest` / `parietal_occipital` / `e_s_mean`: HC median=0.2054, PD median=0.1082, d=-0.4295, p=0.01292, q=0.3042
- `rest` / `parietal_occipital` / `m_e_median`: HC median=0, PD median=0, d=-0.2468, p=0.01394, q=0.3042
- `rest` / `frontal` / `m_median`: HC median=0.03318, PD median=-0.00498, d=-0.4877, p=0.01426, q=0.3042
- `rest` / `parietal_occipital` / `m_median`: HC median=0.0581, PD median=0.006481, d=-0.4724, p=0.01708, q=0.3122
- `rest` / `temporal` / `m_std`: HC median=0.8202, PD median=0.7698, d=-0.4721, p=0.03093, q=0.3987
- `rest` / `frontal` / `e_median`: HC median=0.04664, PD median=0.003328, d=-0.4213, p=0.03093, q=0.3987
- `rest` / `central` / `jac3_rotation_norm_median`: HC median=0.4855, PD median=0.4419, d=-0.5214, p=0.03508, q=0.3987
- `rest` / `central` / `jac3_frobenius_median`: HC median=0.7436, PD median=0.6814, d=-0.4919, p=0.03687, q=0.3987
- `rest` / `parietal_occipital` / `m_a_mean`: HC median=-0.08859, PD median=-0.01672, d=0.4616, p=0.03779, q=0.3987

## Top rho rows

- `rest` / `ctt` / `parietal_occipital` / `d_l_mean`: rho=-0.3412, p=0.0002821, q=0.03245, n=109
- `rest` / `ctt` / `parietal_occipital` / `d_mean`: rho=-0.3193, p=0.0007148, q=0.0411, n=109
- `rest` / `ctt` / `frontal` / `e_e_mean`: rho=-0.2943, p=0.001892, q=0.07254, n=109
- `rest` / `moca` / `parietal_occipital` / `d_l_mean`: rho=0.3186, p=0.0005834, q=0.04994, n=113
- `rest` / `moca` / `frontal` / `d_mean`: rho=0.3089, p=0.0008706, q=0.04994, n=113
- `rest` / `moca` / `frontal` / `d_l_mean`: rho=0.2995, p=0.00127, q=0.04994, n=113
- `rest` / `moca` / `frontal` / `e_s_mean`: rho=-0.287, p=0.002058, q=0.06071, n=113
- `rest` / `pigd_score` / `temporal` / `e_std`: rho=-0.3276, p=0.0003968, q=0.04682, n=113
- `rest` / `pigd_score` / `frontal` / `m_e_mean`: rho=0.2931, p=0.001627, q=0.09597, n=113
- `rest` / `updrs_part_iii` / `temporal` / `e_std`: rho=-0.3746, p=4.361e-05, q=0.005146, n=113
- `rest` / `updrs_part_iii` / `frontal` / `e_e_mean`: rho=-0.3441, p=0.0001903, q=0.01123, n=113
- `rest` / `updrs_total` / `temporal` / `e_std`: rho=-0.3735, p=4.619e-05, q=0.005451, n=113

