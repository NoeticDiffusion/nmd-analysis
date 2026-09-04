# Parkinson walking reachability wrappers

This article-local wrapper calls `ndt_analysis.reachability_cones.summarize_reachability_h5(...)` directly.

- Anchor mode: `cohort`
- Coordinate contract: `cohort_anchored`
- Reachability config: `k=25`, `horizon=4`, `super_window_size=3`, `persistence_mode=all`
- Run rows written: `1385`

## Top HC vs PD reachability rows

- `rest` / `global` / `global` / `tube_log_det_median`: HC median=-10.42, PD median=-12.26, d=-0.5223, p=0.001363, q=0.02347
- `rest` / `global` / `global` / `cone_log_det_h2_median`: HC median=-10.83, PD median=-12.73, d=-0.5178, p=0.001568, q=0.02347
- `rest` / `global` / `global` / `pred_err_h2`: HC median=2.03, PD median=1.759, d=-0.6344, p=0.001711, q=0.02347
- `rest` / `global` / `global` / `tube_log_det_split_half_a_median`: HC median=-10.58, PD median=-12.29, d=-0.6048, p=0.00214, q=0.02347
- `rest` / `global` / `global` / `tube_log_det_mean`: HC median=-10.56, PD median=-12.28, d=-0.5566, p=0.00214, q=0.02347
- `rest` / `global` / `global` / `cone_log_det_h3_median`: HC median=-10.06, PD median=-11.79, d=-0.5207, p=0.002176, q=0.02347
- `rest` / `global` / `global` / `tube_log_det_split_half_b_median`: HC median=-10.31, PD median=-12.31, d=-0.5103, p=0.002214, q=0.02347
- `rest` / `global` / `global` / `cone_log_det_h4_median`: HC median=-9.683, PD median=-11.45, d=-0.5266, p=0.00229, q=0.02347
- `rest` / `global` / `global` / `cone_log_det_h1_median`: HC median=-13.36, PD median=-14.79, d=-0.4852, p=0.003415, q=0.03111
- `rest` / `global` / `global` / `cone_q_ratio_h2_median`: HC median=0.5988, PD median=0.632, d=0.5454, p=0.009544, q=0.06971
- `rest` / `global` / `global` / `q_ratio_h2_median`: HC median=0.5988, PD median=0.632, d=0.5454, p=0.009544, q=0.06971
- `rest` / `global` / `global` / `persistence_hysteresis_d_eff_median`: HC median=0.8518, PD median=0.6429, d=-0.6296, p=0.01105, q=0.06971

## Top PD rho rows

- `rest` / `global` / `global` / `age` / `tube_log_eig_var_mean`: rho=-0.2831, p=0.002171, q=0.04125, n=115
- `rest` / `global` / `global` / `age` / `cone_log_eig_var_h3_median`: rho=-0.2814, p=0.002317, q=0.04125, n=115
- `rest` / `global` / `global` / `age` / `tube_log_eig_var_median`: rho=-0.2792, p=0.002518, q=0.04125, n=115
- `rest` / `global` / `global` / `age` / `cone_log_eig_var_h4_median`: rho=-0.2781, p=0.002621, q=0.04125, n=115
- `rest` / `global` / `global` / `age` / `cone_log_eig_var_h2_median`: rho=-0.2757, p=0.002864, q=0.04125, n=115
- `rest` / `global` / `global` / `age` / `pred_err_h3`: rho=-0.2729, p=0.003173, q=0.04125, n=115
- `rest` / `global` / `global` / `age` / `pred_err_h2`: rho=-0.2618, p=0.004711, q=0.0525, n=115
- `rest` / `global` / `global` / `age` / `pred_err_h1`: rho=-0.2391, p=0.01006, q=0.07445, n=115
- `rest` / `global` / `global` / `age` / `tube_a_operator_norm_mean`: rho=-0.2371, p=0.01074, q=0.07445, n=115
- `rest` / `global` / `global` / `age` / `cone_dir_entropy_h2_median`: rho=0.2332, p=0.01214, q=0.07445, n=115
- `rest` / `global` / `global` / `age` / `cone_dir_entropy_norm_h2_median`: rho=0.2332, p=0.01214, q=0.07445, n=115
- `rest` / `global` / `global` / `age` / `cone_log_eig_var_h1_median`: rho=-0.2313, p=0.01287, q=0.07445, n=115

