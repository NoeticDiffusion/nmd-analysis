# Parkinson walking task-delta contrasts

This pass compares `walk - rest` deltas between `HC` and `PD` for each run-level metric.

- Delta per participant: `walk value - rest value`
- Group test: Mann-Whitney U on delta distributions
- Effect size: Cohen's `d` on the delta distributions
- Correction: BH-FDR across the full delta metric table

- `m_a_mean`: HC delta median=0.1768, PD delta median=0.06441, d=-0.3672, p=0.04926, q=0.7933
- `d_l_mean`: HC delta median=0.2142, PD delta median=0.08092, d=-0.2879, p=0.08609, q=0.7933
- `m_mean`: HC delta median=0.0693, PD delta median=0.007485, d=-0.3605, p=0.08828, q=0.7933
- `m_e_mean`: HC delta median=0.007632, PD delta median=-0.04252, d=-0.3569, p=0.1346, q=0.7933
- `e_std`: HC delta median=-0.09664, PD delta median=0.00233, d=0.3846, p=0.1361, q=0.7933
- `jac9_trace_median`: HC delta median=0.05122, PD delta median=0.01389, d=-0.2777, p=0.1473, q=0.7933
- `e_s_mean`: HC delta median=-0.1825, PD delta median=-0.005203, d=0.2646, p=0.1977, q=0.7933
- `m_median`: HC delta median=0.03792, PD delta median=0.01115, d=-0.3175, p=0.2148, q=0.7933
- `d_s_mean`: HC delta median=0.1083, PD delta median=-0.01371, d=-0.1288, p=0.2283, q=0.7933
- `d_mean`: HC delta median=0.1383, PD delta median=0.08456, d=-0.2688, p=0.2306, q=0.7933
- `jac9_rotation_norm_median`: HC delta median=-0.04073, PD delta median=-0.01533, d=0.2517, p=0.2774, q=0.7933
- `m_a_median`: HC delta median=0.02734, PD delta median=-0.01844, d=-0.2617, p=0.2776, q=0.7933
