# Late 12-24h global pool BH-FDR audit (patient level)

- source contrasts: `articles/CLINICAL/comatose_ndt_12_24/results/outcome_contrasts_20260608_part1_noregional_subjectanchor_primary12h_true1224_cpc15/patient_timebin_outcome_contrasts.csv`
- scope: `summary_level == patient_timebin`, `time_bin == 12_24h`, `status == ok`
- multiplicity correction: Benjamini-Hochberg across the full `12_24h` patient-level metric pool (`n = 159` tested rows)

## Global-BH significant rows (`q < 0.05`)

18 rows survived global BH-FDR:

1. `global_mnps_jacobian_3d/trace_mean`: `d = -0.664`, `p = 0.00482`, `q = 0.0459`
2. `reachability_cones/tube_log_eig_var_median`: `d = +0.653`, `p = 0.00134`, `q = 0.0222`
3. `reachability_cones/cone_log_eig_var_h4_median`: `d = +0.651`, `p = 0.00337`, `q = 0.0412`
4. `reachability_cones/cone_log_eig_var_h3_median`: `d = +0.651`, `p = 0.00168`, `q = 0.0222`
5. `global_mnps_9d/e_s_mean`: `d = +0.638`, `p = 0.000864`, `q = 0.0222`
6. `reachability_cones/cone_log_eig_var_h2_median`: `d = +0.637`, `p = 0.000982`, `q = 0.0222`
7. `reachability_cones/median_min_eig_over_median_eig`: `d = -0.626`, `p = 0.00507`, `q = 0.0459`
8. `global_mnps_9d/e_s_std`: `d = +0.600`, `p = 0.00155`, `q = 0.0222`
9. `reachability_cones/cone_log_eig_var_h1_median`: `d = +0.596`, `p = 0.00154`, `q = 0.0222`
10. `reachability_cones/tube_a_operator_norm_mean`: `d = +0.566`, `p = 0.00520`, `q = 0.0459`
11. `reachability_cones/cone_kappa_h3_median`: `d = +0.503`, `p = 0.00163`, `q = 0.0222`
12. `reachability_cones/tube_kappa_median`: `d = +0.487`, `p = 0.00138`, `q = 0.0222`
13. `reachability_cones/median_cond`: `d = +0.460`, `p = 0.00110`, `q = 0.0222`
14. `reachability_cones/cone_kappa_h4_median`: `d = +0.450`, `p = 0.00168`, `q = 0.0222`
15. `reachability_cones/tube_log_eig_var_mean`: `d = +0.438`, `p = 0.00384`, `q = 0.0428`
16. `reachability_cones/cone_kappa_h2_median`: `d = +0.428`, `p = 0.000874`, `q = 0.0222`
17. `reachability_cones/cone_kappa_h1_median`: `d = +0.359`, `p = 0.000927`, `q = 0.0222`
18. `reachability_cones/persistence_hysteresis_kappa_median`: `d = +0.328`, `p = 0.00404`, `q = 0.0428`

## Prespecified five 12-24h rows under global BH-FDR

- `persistence_kappa_median`: `d = -0.686`, `p = 0.00752`, `q = 0.0627`
- `tube_a_operator_norm_median`: `d = +0.571`, `p = 0.00868`, `q = 0.0627`
- `tube_capture_gate_median`: `d = +0.584`, `p = 0.00977`, `q = 0.0641`
- `persistence_log_eig_var_median`: `d = -0.353`, `p = 0.0411`, `q = 0.168`
- `tube_d_eff_median`: `d = -0.046`, `p = 0.642`, `q = 0.756`

## Output table

The full sortable table with global-q values is:

- `articles/CLINICAL/comatose_ndt/results/late1224_global_pool_bh_20260608.csv`
