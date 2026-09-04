# Parkinson walking regional analysis

- Anchor mode: `cohort`
- Reachability present in bundle: `False`
- Regional source spaces: 3D MNPS, 9D stratified coordinates, and regional 3D Jacobian summaries
- Group test: HC vs PD within task via Mann-Whitney U
- Clinical test: PD-only Spearman rho per task

## Top HC vs PD regional rows

- `rest` / `temporal` / `m_std`: HC median=0.4146, PD median=0.3119, d=-0.839, p=0.0003763, q=0.03027
- `rest` / `parietal_occipital` / `e_s_median`: HC median=-0.341, PD median=-0.0317, d=0.5411, p=0.000473, q=0.03027
- `rest` / `parietal_occipital` / `e_median`: HC median=-3.521, PD median=-3.411, d=0.5059, p=0.0008559, q=0.03584
- `rest` / `central` / `m_std`: HC median=0.4464, PD median=0.2986, d=-0.6923, p=0.001182, q=0.03584
- `rest` / `parietal_occipital` / `e_s_mean`: HC median=-0.2621, PD median=-0.0005995, d=0.4897, p=0.001706, q=0.03584
- `rest` / `parietal_occipital` / `e_mean`: HC median=-3.499, PD median=-3.395, d=0.4801, p=0.001956, q=0.03584
- `rest` / `frontal` / `m_std`: HC median=0.4257, PD median=0.3003, d=-0.6997, p=0.00199, q=0.03584
- `rest` / `parietal_occipital` / `m_std`: HC median=0.4529, PD median=0.2724, d=-0.6856, p=0.00224, q=0.03584
- `rest` / `frontal` / `m_a_median`: HC median=-2.29, PD median=-2.871, d=-0.5068, p=0.008478, q=0.1206
- `rest` / `central` / `e_s_median`: HC median=-0.3278, PD median=-0.07769, d=0.5177, p=0.01169, q=0.138
- `rest` / `frontal` / `m_a_mean`: HC median=-2.389, PD median=-2.872, d=-0.5117, p=0.01186, q=0.138
- `rest` / `central` / `e_median`: HC median=-3.514, PD median=-3.427, d=0.5148, p=0.01731, q=0.18

## Top rho rows

- `rest` / `age` / `frontal` / `d_s_mean`: rho=-0.4094, p=5.034e-06, q=0.0004884, n=116
- `rest` / `age` / `frontal` / `d_s_median`: rho=-0.3956, p=1.103e-05, q=0.0004884, n=116
- `rest` / `age` / `parietal_occipital` / `d_s_mean`: rho=-0.3948, p=1.154e-05, q=0.0004884, n=116
- `rest` / `age` / `central` / `d_s_mean`: rho=-0.3732, p=3.685e-05, q=0.00117, n=116
- `rest` / `age` / `parietal_occipital` / `d_s_median`: rho=-0.3687, p=4.64e-05, q=0.001179, n=116
- `rest` / `age` / `central` / `d_s_median`: rho=-0.3574, p=8.203e-05, q=0.001514, n=116
- `rest` / `age` / `temporal` / `d_s_mean`: rho=-0.357, p=8.345e-05, q=0.001514, n=116
- `rest` / `age` / `temporal` / `d_s_median`: rho=-0.3512, p=0.000111, q=0.001762, n=116
- `rest` / `age` / `frontal` / `m_o_median`: rho=0.2857, p=0.001881, q=0.02654, n=116
- `rest` / `age` / `frontal` / `m_o_mean`: rho=0.2654, p=0.00398, q=0.05055, n=116
- `rest` / `ctt` / `central` / `d_s_mean`: rho=-0.4325, p=2.651e-06, q=0.0001815, n=109
- `rest` / `ctt` / `parietal_occipital` / `e_std`: rho=0.4312, p=2.859e-06, q=0.0001815, n=109

