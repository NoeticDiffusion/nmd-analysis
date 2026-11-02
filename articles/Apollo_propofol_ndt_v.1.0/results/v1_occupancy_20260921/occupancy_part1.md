# Apollo occupancy / state relocation (occupancy_relocation_20260921)

Median Euclidean radius in the baseline-only robust-z frame of the eight MNPS-used features_raw columns. Exact scalar from the C3-anchor pipeline. Status: `exploratory_discovery_20260921_g4_not_locked`. Promoted after sl_003/sl_004. Not consciousness. Not NDT-C3. Not confirmatory local-chart b/a.

n subjects = 20. Bootstrap 10000, seed 20260920.

## Occupancy by protocol phase

| Subject | baseline | first sedation | later sedation | recovery |
| --- | ---: | ---: | ---: | ---: |
| sub-002 | 2.402 | 2.867 | 3.556 | 5.542 |
| sub-003 | 2.447 | 4.265 | 5.643 | 3.43 |
| sub-005 | 2.372 | 6.83 | 13.37 | 4.867 |
| sub-006 | 2.788 | 6.513 | 7.922 | 3.111 |
| sub-007 | 2.694 | 7.869 | 26.41 | 28.6 |
| sub-008 | 2.85 | 6.438 | 17.91 | 5.01 |
| sub-009 | 2.287 | 3.878 | 20.44 | 2.881 |
| sub-010 | 2.387 | 3.806 | 6.084 | 5.524 |
| sub-013 | 2.524 | 3.182 | 4.759 | 2.92 |
| sub-014 | 2.726 | 2.472 | 9.437 | 2.764 |
| sub-018 | 2.471 | 4.742 | 28.62 | 4.467 |
| sub-020 | 2.675 | 5.168 | 15.35 | 4.492 |
| sub-022 | 2.87 | 3.537 | 3.718 | 4.569 |
| sub-023 | 2.956 | 3.349 | 12.85 | 4.718 |
| sub-024 | 2.724 | 5.03 | 10.07 | 2.42 |
| sub-025 | 2.9 | 2.987 | 7.576 | 3.359 |
| sub-026 | 2.774 | 5.042 | 6.383 | 4.578 |
| sub-027 | 2.823 | 6.378 | 17.77 | 3.335 |
| sub-028 | 2.4 | 2.16 | 3.09 | 3.237 |
| sub-029 | 2.758 | 3.199 | 3.852 | 2.908 |

## Contrasts versus baseline

| Role | Contrast | n | later med | base med | Δ med | d_z | n+ | n− | sign p | Wilcoxon p |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| primary | `first_sedation_minus_baseline` | 20 | 4.071 | 2.709 | 1.704 | 1.15 | 18 | 2 | 0.0004025 | 1.907e-05 |
| secondary | `later_sedation_minus_baseline` | 20 | 8.679 | 2.709 | 5.923 | 1.12 | 20 | 0 | 1.907e-06 | 1.907e-06 |
| secondary | `recovery_minus_baseline` | 20 | 3.949 | 2.709 | 1.341 | 0.445 | 19 | 1 | 4.005e-05 | 9.537e-06 |

## Why C3 is NOT_TESTABLE (baseline-anchor match support)

Subjects with ≥20 caliper-matched pairs: 7/20. This table is copied from the frozen C3-anchor run; occupancy is not rematched.

| Subject | n pairs | match frac | included |
| --- | ---: | ---: | --- |
| sub-002 | 28 | 0.272 | yes |
| sub-003 | 6 | 0.075 | no |
| sub-005 | 0 | 0 | no |
| sub-006 | 0 | 0 | no |
| sub-007 | 3 | 0.0411 | no |
| sub-008 | 4 | 0.0421 | no |
| sub-009 | 2 | 0.0194 | no |
| sub-010 | 10 | 0.102 | no |
| sub-013 | 25 | 0.238 | yes |
| sub-014 | 22 | 0.224 | yes |
| sub-018 | 6 | 0.06 | no |
| sub-020 | 1 | 0.0102 | no |
| sub-022 | 33 | 0.33 | yes |
| sub-023 | 25 | 0.255 | yes |
| sub-024 | 4 | 0.0444 | no |
| sub-025 | 19 | 0.2 | no |
| sub-026 | 9 | 0.0874 | no |
| sub-027 | 1 | 0.01 | no |
| sub-028 | 24 | 0.245 | yes |
| sub-029 | 20 | 0.274 | yes |

Primary prediction is later > earlier (relocation away from the awake neighbourhood). Local-chart L1 b/a remains discovery. NDT-C3 remains OPEN.

Primary sign test: p = 0.0004025, d_z = 1.15, 18/20 increase.
