# Parkinson walking regional analysis

- Anchor mode: `cohort`
- Reachability present in bundle: `False`
- Regional source spaces: 3D MNPS, 9D stratified coordinates, and regional 3D Jacobian summaries
- Group test: HC vs PD within task via Mann-Whitney U
- Clinical test: PD-only Spearman rho per task

## Top HC vs PD regional rows

- `rest` / `temporal` / `m_e_iqr`: HC median=0.6461, PD median=0.5223, d=-0.8418, p=0.0003418, q=0.03752
- `rest` / `temporal` / `m_std`: HC median=0.4146, PD median=0.3119, d=-0.839, p=0.0003763, q=0.03752
- `rest` / `parietal_occipital` / `e_s_median`: HC median=-0.341, PD median=-0.0317, d=0.5411, p=0.000473, q=0.03752
- `rest` / `parietal_occipital` / `e_median`: HC median=-3.521, PD median=-3.411, d=0.5059, p=0.0008559, q=0.03752
- `rest` / `parietal_occipital` / `m_mad`: HC median=0.3066, PD median=0.1666, d=-0.7243, p=0.001081, q=0.03752
- `rest` / `central` / `m_std`: HC median=0.4464, PD median=0.2986, d=-0.6923, p=0.001182, q=0.03752
- `rest` / `temporal` / `m_mad`: HC median=0.2567, PD median=0.1948, d=-0.6459, p=0.001182, q=0.03752
- `rest` / `parietal_occipital` / `m_iqr`: HC median=0.5958, PD median=0.3384, d=-0.705, p=0.001269, q=0.03752
- `rest` / `central` / `m_iqr`: HC median=0.5267, PD median=0.3767, d=-0.5324, p=0.001592, q=0.03752
- `rest` / `parietal_occipital` / `e_s_mean`: HC median=-0.2621, PD median=-0.0005995, d=0.4897, p=0.001706, q=0.03752
- `rest` / `temporal` / `m_iqr`: HC median=0.54, PD median=0.3873, d=-0.5586, p=0.001735, q=0.03752
- `rest` / `frontal` / `m_iqr`: HC median=0.529, PD median=0.3696, d=-0.6944, p=0.001765, q=0.03752

## Top rho rows

- `rest` / `age` / `frontal` / `d_s_mean`: rho=-0.4094, p=5.034e-06, q=0.001008, n=116
- `rest` / `age` / `frontal` / `d_s_median`: rho=-0.3956, p=1.103e-05, q=0.001008, n=116
- `rest` / `age` / `parietal_occipital` / `d_s_mean`: rho=-0.3948, p=1.154e-05, q=0.001008, n=116
- `rest` / `age` / `central` / `d_s_mean`: rho=-0.3732, p=3.685e-05, q=0.002414, n=116
- `rest` / `age` / `parietal_occipital` / `d_s_median`: rho=-0.3687, p=4.64e-05, q=0.002432, n=116
- `rest` / `age` / `central` / `d_s_median`: rho=-0.3574, p=8.203e-05, q=0.003124, n=116
- `rest` / `age` / `temporal` / `d_s_mean`: rho=-0.357, p=8.345e-05, q=0.003124, n=116
- `rest` / `age` / `temporal` / `d_s_median`: rho=-0.3512, p=0.000111, q=0.003635, n=116
- `rest` / `age` / `parietal_occipital` / `e_iqr`: rho=0.3076, p=0.0007815, q=0.02275, n=116
- `rest` / `age` / `parietal_occipital` / `e_s_mad`: rho=0.302, p=0.0009846, q=0.02509, n=116
- `rest` / `age` / `parietal_occipital` / `e_mad`: rho=0.3004, p=0.001053, q=0.02509, n=116
- `rest` / `age` / `parietal_occipital` / `e_s_iqr`: rho=0.2935, p=0.001387, q=0.03029, n=116

