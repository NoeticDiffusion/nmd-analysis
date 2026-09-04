# APPLESEED cohort-anchor run handover

- Input: `neuralmanifolddynamics_ds003710_20260804_153346`.
- Contract: 48 sessions, 13 children, 11 complete longitudinal cases; cohort anchor `ds003710_global_cohort_all_timepoints_iqr_v2_1` over 8,179 subject-balanced epochs.
- Primary layer: cohort-anchored 3D MNJ and reachability (48/48).
- QC: 38 `ok`, 10 `adjusted`; 9D Jacobian available in 46/48, in 10/11 balanced 4-to-8-month cases, and in 9/11 balanced 4-to-12-month cases.
- Exploratory 4m-mean to 8m result: lower reachability effective dimension ($d_z=-0.48$, raw p=0.102) and directional entropy ($d_z=-0.39$, raw p=0.102), neither FDR-supported.
- Cohort coordinates show descriptive mobility decrease ($d_z=-0.48$, p=0.206) and deviation increase ($d_z=0.44$, p=0.175).
- Exploratory 4m-mean to 12m result: no 3D dynamical endpoint had raw p<0.365. Cohort-coordinate mobility decreased substantially ($d_z=-1.51$, raw p=0.00098; within-coordinate-family FDR sensitivity p=0.0029); deviation and entropy-related coordinate shifts were not supported.

These are common-scale, exploratory results. The global anchor includes all ages, so it is not a held-out-age normalization and does not support predictive or normative claims.
