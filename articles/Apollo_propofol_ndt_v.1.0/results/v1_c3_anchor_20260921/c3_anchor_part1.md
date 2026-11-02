# Apollo baseline-anchored matched-state C3 (matched_state_c3_baseline_anchor_20260921)

First protocol sedation minus pre-drug baseline in a baseline-only robust-z frame of the eight MNPS-used features_raw columns. Matching is outcome-blind. Status: `exploratory_discovery_20260921_g4_not_locked`. Not consciousness. Not confirmatory amplitude.

Subjects included: 7/20. Bootstrap 10000, seed 20260920.

## Support

| Subject | n later eligible | n baseline eligible | n pairs | match frac | caliper | median d | included |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| sub-002 | 103 | 95 | 28 | 0.272 | 1.39 | 1.08 | yes |
| sub-003 | 80 | 93 | 6 | 0.075 | 1.17 | 0.846 | no |
| sub-005 | 98 | 98 | 0 | 0 | 1.15 | nan | no |
| sub-006 | 98 | 95 | 0 | 0 | 1.24 | nan | no |
| sub-007 | 73 | 65 | 3 | 0.0411 | 1.36 | 0.885 | no |
| sub-008 | 95 | 90 | 4 | 0.0421 | 1.11 | 0.854 | no |
| sub-009 | 103 | 100 | 2 | 0.0194 | 1.02 | 0.888 | no |
| sub-010 | 98 | 80 | 10 | 0.102 | 1.08 | 0.917 | no |
| sub-013 | 105 | 95 | 25 | 0.238 | 1.29 | 1.09 | yes |
| sub-014 | 98 | 100 | 22 | 0.224 | 1.32 | 0.926 | yes |
| sub-018 | 100 | 100 | 6 | 0.06 | 1.23 | 1.05 | no |
| sub-020 | 98 | 100 | 1 | 0.0102 | 1.47 | 0.78 | no |
| sub-022 | 100 | 88 | 33 | 0.33 | 1.42 | 1.19 | yes |
| sub-023 | 98 | 103 | 25 | 0.255 | 1.26 | 0.973 | yes |
| sub-024 | 90 | 60 | 4 | 0.0444 | 1.56 | 1.25 | no |
| sub-025 | 95 | 90 | 19 | 0.2 | 1.38 | 0.936 | no |
| sub-026 | 103 | 103 | 9 | 0.0874 | 1.23 | 1.14 | no |
| sub-027 | 100 | 93 | 1 | 0.01 | 1.39 | 1.25 | no |
| sub-028 | 98 | 90 | 24 | 0.245 | 1.03 | 0.826 | yes |
| sub-029 | 73 | 103 | 20 | 0.274 | 1.43 | 1.05 | yes |

## Contrasts (Holm only on matched speed and spread)

| Family | Metric | n | later med | base med | Δ med | d_z | sign p | Wilcoxon p | Holm p |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| matched_anchor | `matched_speed` | 7 | 0.5802 | 0.5687 | 0.05066 | 0.0954 | 1 | 0.9375 | 1 |
| matched_anchor | `matched_spread` | 7 | 0.4784 | 0.3944 | 0.03062 | -0.139 | 1 | 0.8125 | 1 |
| unmatched_anchor | `unmatched_speed` | 20 | 0.6786 | 0.6197 | 0.07485 | 0.311 | 0.1153 | 0.1054 | - |
| unmatched_anchor | `unmatched_spread` | 20 | 0.7014 | 0.6459 | -0.02172 | -0.266 | 1 | 0.5217 | - |
| unmatched_anchor | `unmatched_occupancy` | 20 | 4.071 | 2.709 | 1.704 | 1.15 | 0.0004025 | 1.907e-05 | - |
| matched_anchor_qc | `matched_occupancy` | 7 | 2.11 | 2.163 | 0.1326 | 0.245 | 1 | 0.8125 | - |
| random_anchor | `random_speed` | 7 | 0.5944 | 0.6432 | -0.03212 | -0.374 | 0.4531 | 0.375 | - |
| random_anchor | `random_spread` | 7 | 0.4326 | 0.5457 | -0.08255 | -0.599 | 0.4531 | 0.2188 | - |
| unmatched_recovery | `unmatched_speed` | 20 | 0.6533 | 0.6197 | 0.05277 | 0.354 | 0.2632 | 0.03277 | - |
| unmatched_recovery | `unmatched_spread` | 20 | 0.7198 | 0.6459 | 0.1151 | 0.206 | 0.5034 | 0.1893 | - |
| unmatched_recovery | `unmatched_occupancy` | 20 | 3.949 | 2.709 | 1.341 | 0.445 | 4.005e-05 | 9.537e-06 | - |

Occupancy is median Euclidean radius in baseline-z. Unmatched occupancy asks whether sedation leaves the awake neighbourhood. Matched occupancy is a QC that the paired states are similarly far from origin.

Recovery unmatched is available for 20 subjects and is not Holm.
