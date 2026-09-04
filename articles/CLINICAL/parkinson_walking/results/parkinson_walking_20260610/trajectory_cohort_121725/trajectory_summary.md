# Parkinson walking trajectory geometry

This pass is explicitly exploratory and follows the compact-summary trajectory layer rather than the standard NMD contract.

- Anchor mode: `cohort`
- Implemented compact-summary endpoints: `H_rate`, `I`, `A_MNPS`, `kappa_median`, `T_path`
- Here these map to `entropy_rate`, `irreversibility`, `noetic_action`, `curvature_median`, and `tortuosity`

## Top HC vs PD trajectory rows

- `rest` / `3D` / `noetic_action_kinetic`: HC median=0.006168, PD median=0.004328, d=-0.6865, p=0.002356, q=0.01209
- `rest` / `3D` / `curvature_median`: HC median=3.299, PD median=4.135, d=0.5964, p=0.002924, q=0.01209
- `rest` / `3D` / `path_length`: HC median=32.4, PD median=27.8, d=-0.6714, p=0.003021, q=0.01209
- `rest` / `3D` / `noetic_action_jerk`: HC median=0.00142, PD median=0.00122, d=-0.5295, p=0.01072, q=0.03216
- `rest` / `3D` / `noetic_action`: HC median=-0.5073, PD median=-0.2607, d=0.2918, p=0.2508, q=0.5058
- `rest` / `3D` / `noetic_action_potential`: HC median=-0.523, PD median=-0.2735, d=0.2921, p=0.2529, q=0.5058
- `rest` / `3D` / `entropy_rate`: HC median=0.7937, PD median=0.7007, d=-0.05678, p=0.4892, q=0.7613
- `rest` / `3D` / `self_loop_rate`: HC median=0.647, PD median=0.6733, d=0.07698, p=0.5248, q=0.7613
- `rest` / `3D` / `transition_sparsity`: HC median=0.9201, PD median=0.9306, d=0.1165, p=0.571, q=0.7613
- `rest` / `3D` / `tortuosity`: HC median=32.2, PD median=28.57, d=-0.08961, p=0.6406, q=0.7687
- `rest` / `3D` / `entropy_production`: HC median=0.6243, PD median=0.803, d=0.01276, p=0.8007, q=0.8301
- `rest` / `3D` / `irreversibility`: HC median=0.0678, PD median=0.06825, d=-0.003096, p=0.8301, q=0.8301

## Top rho rows

- `rest` / `3D` / `ctt` / `noetic_action_potential`: rho=-0.2516, p=0.008321, q=0.05655, n=109
- `rest` / `3D` / `ctt` / `noetic_action`: rho=-0.2476, p=0.009424, q=0.05655, n=109
- `rest` / `3D` / `pigd_score` / `irreversibility`: rho=-0.2578, p=0.005839, q=0.03773, n=113
- `rest` / `3D` / `pigd_score` / `entropy_production`: rho=-0.2556, p=0.006288, q=0.03773, n=113
- `rest` / `3D` / `pigd_score` / `self_loop_rate`: rho=0.2234, p=0.01741, q=0.06963, n=113
- `rest` / `3D` / `pigd_score` / `entropy_rate`: rho=-0.2075, p=0.02744, q=0.08233, n=113
- `rest` / `9D` / `age` / `curvature_median`: rho=0.3068, p=0.0008076, q=0.009691, n=116
- `rest` / `9D` / `age` / `noetic_action`: rho=-0.2586, p=0.00507, q=0.02618, n=116
- `rest` / `9D` / `age` / `noetic_action_potential`: rho=-0.2511, p=0.006545, q=0.02618, n=116
- `rest` / `9D` / `age` / `path_length`: rho=-0.2178, p=0.01882, q=0.05646, n=116
- `rest` / `9D` / `age` / `noetic_action_jerk`: rho=-0.1932, p=0.03774, q=0.09059, n=116
- `rest` / `9D` / `ctt` / `noetic_action`: rho=-0.3254, p=0.0005547, q=0.004315, n=109

