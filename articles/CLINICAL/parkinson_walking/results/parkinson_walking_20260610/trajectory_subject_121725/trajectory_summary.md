# Parkinson walking trajectory geometry

This pass is explicitly exploratory and follows the compact-summary trajectory layer rather than the standard NMD contract.

- Anchor mode: `subject`
- Implemented compact-summary endpoints: `H_rate`, `I`, `A_MNPS`, `kappa_median`, `T_path`
- Here these map to `entropy_rate`, `irreversibility`, `noetic_action`, `curvature_median`, and `tortuosity`

## Top HC vs PD trajectory rows

- `rest` / `3D` / `noetic_action_jerk`: HC median=0.009317, PD median=0.01004, d=0.2776, p=0.1358, q=0.6587
- `rest` / `3D` / `entropy_rate`: HC median=1.279, PD median=1.323, d=0.2916, p=0.1786, q=0.6587
- `rest` / `3D` / `curvature_median`: HC median=1.897, PD median=1.979, d=0.1884, p=0.2286, q=0.6587
- `rest` / `3D` / `transition_sparsity`: HC median=0.7639, PD median=0.7569, d=-0.2195, p=0.2317, q=0.6587
- `rest` / `3D` / `noetic_action_kinetic`: HC median=0.03345, PD median=0.03813, d=0.2316, p=0.2745, q=0.6587
- `rest` / `3D` / `self_loop_rate`: HC median=0.3305, PD median=0.3275, d=-0.1915, p=0.5149, q=0.791
- `rest` / `3D` / `tortuosity`: HC median=34.02, PD median=29.95, d=-0.1727, p=0.5736, q=0.791
- `rest` / `3D` / `path_length`: HC median=58.61, PD median=59.4, d=0.08096, p=0.5839, q=0.791
- `rest` / `3D` / `noetic_action`: HC median=0.1272, PD median=0.1206, d=0.07707, p=0.7031, q=0.791
- `rest` / `3D` / `entropy_production`: HC median=6.241, PD median=6.157, d=-0.1456, p=0.7295, q=0.791
- `rest` / `3D` / `irreversibility`: HC median=0.3362, PD median=0.3453, d=-0.1067, p=0.7658, q=0.791
- `rest` / `3D` / `noetic_action_potential`: HC median=0.07191, PD median=0.06036, d=0.07095, p=0.791, q=0.791

## Top rho rows

- `rest` / `3D` / `ctt` / `noetic_action`: rho=0.2618, p=0.005964, q=0.03704, n=109
- `rest` / `3D` / `ctt` / `noetic_action_potential`: rho=0.2607, p=0.006173, q=0.03704, n=109
- `rest` / `3D` / `moca` / `tortuosity`: rho=-0.2525, p=0.006963, q=0.07761, n=113
- `rest` / `3D` / `moca` / `noetic_action`: rho=-0.2332, p=0.01293, q=0.07761, n=113
- `rest` / `3D` / `pigd_score` / `noetic_action`: rho=0.25, p=0.007584, q=0.09101, n=113
- `rest` / `3D` / `pigd_score` / `tortuosity`: rho=0.2232, p=0.01749, q=0.09371, n=113
- `rest` / `3D` / `pigd_score` / `noetic_action_potential`: rho=0.2131, p=0.02343, q=0.09371, n=113
- `rest` / `3D` / `updrs_part_iii` / `noetic_action`: rho=0.2798, p=0.002685, q=0.03222, n=113
- `rest` / `3D` / `updrs_part_iii` / `noetic_action_potential`: rho=0.236, p=0.01187, q=0.07121, n=113
- `rest` / `9D` / `moca` / `tortuosity`: rho=-0.3032, p=0.001095, q=0.01315, n=113
- `rest` / `9D` / `moca` / `irreversibility`: rho=-0.225, p=0.01659, q=0.07924, n=113
- `rest` / `9D` / `moca` / `noetic_action`: rho=-0.2167, p=0.02113, q=0.07924, n=113

