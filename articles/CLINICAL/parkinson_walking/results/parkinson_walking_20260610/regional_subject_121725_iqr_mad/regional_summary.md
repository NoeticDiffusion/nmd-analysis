# Parkinson walking regional analysis

- Anchor mode: `subject`
- Reachability present in bundle: `False`
- Regional source spaces: 3D MNPS, 9D stratified coordinates, and regional 3D Jacobian summaries
- Group test: HC vs PD within task via Mann-Whitney U
- Clinical test: PD-only Spearman rho per task

## Top HC vs PD regional rows

- `rest` / `parietal_occipital` / `e_mad`: HC median=0.6226, PD median=0.4778, d=-0.9556, p=2.065e-05, q=0.005451
- `rest` / `parietal_occipital` / `e_iqr`: HC median=1.228, PD median=0.9774, d=-0.8745, p=4.386e-05, q=0.005789
- `rest` / `central` / `e_s_mean`: HC median=0.1453, PD median=0.05619, d=-0.4589, p=0.00224, q=0.1529
- `rest` / `central` / `jac3_rotation_norm_mad`: HC median=0.1502, PD median=0.1216, d=-0.7548, p=0.002317, q=0.1529
- `rest` / `parietal_occipital` / `e_std`: HC median=0.9215, PD median=0.7818, d=-0.6327, p=0.003279, q=0.1575
- `rest` / `central` / `jac3_rotation_norm_iqr`: HC median=0.295, PD median=0.2494, d=-0.7362, p=0.004109, q=0.1575
- `rest` / `central` / `jac3_frobenius_mad`: HC median=0.1757, PD median=0.1509, d=-0.693, p=0.004175, q=0.1575
- `rest` / `central` / `jac3_frobenius_iqr`: HC median=0.3543, PD median=0.3013, d=-0.6499, p=0.006664, q=0.2199
- `rest` / `central` / `e_s_median`: HC median=0, PD median=0, d=0.2572, p=0.008747, q=0.2566
- `rest` / `central` / `e_mad`: HC median=0.5273, PD median=0.4712, d=-0.562, p=0.01169, q=0.2804
- `rest` / `parietal_occipital` / `e_s_mean`: HC median=0.2054, PD median=0.1082, d=-0.4295, p=0.01292, q=0.2804
- `rest` / `parietal_occipital` / `m_e_median`: HC median=0, PD median=0, d=-0.2468, p=0.01394, q=0.2804

## Top rho rows

- `rest` / `ctt` / `parietal_occipital` / `d_l_mean`: rho=-0.3412, p=0.0002821, q=0.06969, n=109
- `rest` / `ctt` / `parietal_occipital` / `d_mean`: rho=-0.3193, p=0.0007148, q=0.08827, n=109
- `rest` / `moca` / `parietal_occipital` / `d_l_mean`: rho=0.3186, p=0.0005834, q=0.0989, n=113
- `rest` / `moca` / `frontal` / `d_mean`: rho=0.3089, p=0.0008706, q=0.0989, n=113
- `rest` / `moca` / `frontal` / `d_l_mean`: rho=0.2995, p=0.00127, q=0.0989, n=113
- `rest` / `moca` / `frontal` / `e_e_mad`: rho=0.2939, p=0.001582, q=0.0989, n=113
- `rest` / `pigd_score` / `temporal` / `e_std`: rho=-0.3276, p=0.0003968, q=0.0992, n=113
- `rest` / `updrs_part_iii` / `temporal` / `e_std`: rho=-0.3746, p=4.361e-05, q=0.0109, n=113
- `rest` / `updrs_part_iii` / `frontal` / `e_e_mean`: rho=-0.3441, p=0.0001903, q=0.02378, n=113
- `rest` / `updrs_part_iii` / `temporal` / `e_iqr`: rho=-0.3235, p=0.0004749, q=0.03957, n=113
- `rest` / `updrs_part_iii` / `temporal` / `e_mad`: rho=-0.3143, p=0.0006976, q=0.0436, n=113
- `rest` / `updrs_total` / `temporal` / `e_std`: rho=-0.3735, p=4.619e-05, q=0.01155, n=113

