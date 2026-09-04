# Hypoglycemia robustness analyses

## Design

- Label-swap null: independently swap euglycemia/hypoglycemia labels within each paired participant.
- Sensitivity: exclude participants whose hypoglycemia H5 geometry contract is marked `adjusted`.
- This tests the stability of condition association; it does not create an euglycemia-only feature anchor or establish a glucose dose-response.

## Excluded in adjusted-geometry sensitivity

- `sub-004`
- `sub-017`
- `sub-021`

## Paired label-swap null

| analysis | metric | n | observed HYPO-EU | null p | null q |
|---|---|---:|---:|---:|---:|
| global_mnps_9d | d_l_median | 34 | -0.4404 | 0.03 | 0.04125 |
| global_mnps_9d | d_n_median | 34 | 1.014 | 0.0004 | 0.001467 |
| global_mnps_9d | e_e_median | 34 | -0.7084 | 0.0172 | 0.03153 |
| global_mnps_9d | e_m_median | 34 | 1.024 | 0.0018 | 0.00495 |
| global_mnps_9d | m_a_median | 34 | -1.096 | 9.999e-05 | 0.0011 |
| global_mnps_9d | m_e_median | 34 | -0.6848 | 0.0003 | 0.001467 |
| reachability_cones | tube_d_eff_median | 33 | 0.2512 | 0.0147 | 0.03153 |
| reachability_cones | tube_dir_entropy_median | 33 | 0.08805 | 0.0282 | 0.04125 |
| reachability_cones | tube_kappa_median | 33 | -2872 | 0.06369 | 0.07785 |
| reachability_cones | tube_log_det_median | 33 | 0.395 | 0.2409 | 0.265 |
| reachability_cones | tube_rotation_median | 33 | 0.004369 | 0.8354 | 0.8354 |

## Excluding adjusted-geometry participants

| analysis | metric | n full -> sensitivity | full delta | sensitivity delta | direction preserved |
|---|---|---:|---:|---:|---|
| global_mnps_9d | d_l_median | 34 -> 31 | -0.4404 | -0.5032 | True |
| global_mnps_9d | d_n_median | 34 -> 31 | 1.014 | 0.8624 | True |
| global_mnps_9d | e_e_median | 34 -> 31 | -0.7084 | -0.8124 | True |
| global_mnps_9d | e_m_median | 34 -> 31 | 1.024 | 0.7081 | True |
| global_mnps_9d | m_a_median | 34 -> 31 | -1.096 | -1.043 | True |
| global_mnps_9d | m_e_median | 34 -> 31 | -0.6848 | -0.6387 | True |
| reachability_cones | tube_d_eff_median | 33 -> 31 | 0.2512 | 0.2365 | True |
| reachability_cones | tube_dir_entropy_median | 33 -> 31 | 0.08805 | 0.0804 | True |
| reachability_cones | tube_kappa_median | 33 -> 31 | -2872 | -3011 | True |
| reachability_cones | tube_log_det_median | 33 -> 31 | 0.395 | 0.4497 | True |
| reachability_cones | tube_rotation_median | 33 -> 31 | 0.004369 | 0.001744 | True |
