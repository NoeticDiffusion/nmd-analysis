# Apollo matched-state C3 (matched_state_c3_20260921)

First protocol sedation minus pre-drug baseline at greedy caliper-matched present MNPS locations. Matching is outcome-blind. Status: `exploratory_discovery_20260921_g4_not_locked`. Not consciousness. Not confirmatory amplitude. Not identified Itô drift/diffusion.

Subjects included: 19/20. Caliper = median baseline LOO nearest-neighbour distance. Minimum 20 matched pairs. Bootstrap 10000, seed 20260920.

## Support

| Subject | n later eligible | n baseline eligible | n pairs | match frac | caliper | median d | included |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| sub-002 | 103 | 95 | 38 | 0.369 | 0.274 | 0.177 | yes |
| sub-003 | 80 | 93 | 31 | 0.388 | 0.304 | 0.178 | yes |
| sub-005 | 98 | 98 | 40 | 0.408 | 0.261 | 0.193 | yes |
| sub-006 | 98 | 95 | 32 | 0.327 | 0.284 | 0.187 | yes |
| sub-007 | 73 | 65 | 27 | 0.37 | 0.33 | 0.235 | yes |
| sub-008 | 95 | 90 | 33 | 0.347 | 0.266 | 0.184 | yes |
| sub-009 | 103 | 100 | 37 | 0.359 | 0.268 | 0.17 | yes |
| sub-010 | 98 | 80 | 30 | 0.306 | 0.289 | 0.199 | yes |
| sub-013 | 105 | 95 | 33 | 0.314 | 0.253 | 0.176 | yes |
| sub-014 | 98 | 100 | 37 | 0.378 | 0.278 | 0.167 | yes |
| sub-018 | 100 | 100 | 46 | 0.46 | 0.258 | 0.155 | yes |
| sub-020 | 98 | 100 | 48 | 0.49 | 0.334 | 0.229 | yes |
| sub-022 | 100 | 88 | 39 | 0.39 | 0.284 | 0.184 | yes |
| sub-023 | 98 | 103 | 38 | 0.388 | 0.263 | 0.161 | yes |
| sub-024 | 90 | 60 | 13 | 0.144 | 0.291 | 0.2 | no |
| sub-025 | 95 | 90 | 30 | 0.316 | 0.302 | 0.209 | yes |
| sub-026 | 103 | 103 | 32 | 0.311 | 0.244 | 0.162 | yes |
| sub-027 | 100 | 93 | 24 | 0.24 | 0.253 | 0.187 | yes |
| sub-028 | 98 | 90 | 33 | 0.337 | 0.247 | 0.174 | yes |
| sub-029 | 73 | 103 | 35 | 0.479 | 0.304 | 0.197 | yes |

## Contrasts (Holm only on matched MNPS speed and spread)

| Family | Metric | n | later med | base med | Δ med | d_z | sign p | Wilcoxon p | Holm p |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| matched_mnps | `matched_speed` | 19 | 0.1963 | 0.2044 | -0.01003 | -0.164 | 0.3593 | 0.3525 | 0.3593 |
| matched_mnps | `matched_spread` | 19 | 0.05739 | 0.06869 | -0.007636 | -0.331 | 0.06357 | 0.1819 | 0.1271 |
| unmatched | `unmatched_speed` | 20 | 0.2083 | 0.2156 | -0.01311 | -0.427 | 0.01182 | 0.04405 | - |
| unmatched | `unmatched_spread` | 20 | 0.06469 | 0.08065 | -0.0166 | -0.687 | 0.01182 | 0.008308 | - |
| random_match | `random_speed` | 19 | 0.2083 | 0.2138 | -0.009075 | -0.44 | 0.3593 | 0.1042 | - |
| random_match | `random_spread` | 19 | 0.06807 | 0.08624 | -0.0102 | -0.507 | 0.1671 | 0.04456 | - |
| matched_mnps_spectral | `matched_speed` | 6 | 0.2214 | 0.1894 | 0.02538 | 0.448 | 0.2188 | 0.3125 | - |
| matched_mnps_spectral | `matched_spread` | 6 | 0.072 | 0.06406 | 0.008477 | 0.293 | 0.6875 | 0.4375 | - |

Random-match ignores present \(x\) but keeps the matched pair count. Unmatched uses all eligible sources. Spectral matching concatenates baseline-robust-z MNPS-used EEG features.

Local recording fits mean this is same-chart-coordinate matching, not a documented cross-phase physical anchor.
