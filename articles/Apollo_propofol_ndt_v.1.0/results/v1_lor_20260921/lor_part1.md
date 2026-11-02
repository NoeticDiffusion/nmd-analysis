# Apollo occupancy × LOR/ROR (occupancy_lor_20260921)

Behavioural labels from exact binomial 95% Clopper–Pearson intervals on `n_correct_responses` / 40 at later protocol sedation versus baseline. Occupancy is the frozen unmatched baseline-z scalar; it is joined, not recomputed. Status: `exploratory_discovery_20260921_g4_not_locked`. Not consciousness. Not protocol-3-as-LOR.

## Occupancy-blind label audit

LOR-impaired 7 / responsive 13 / missing 0 (Chennu 2016 reported 7 drowsy and 13 responsive).
Among LOR-impaired, ROR returned 7, not returned 0.

| Subject | k base | k first | k later | k recovery | LOR | ROR |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| sub-002 | 40 | 39 | 39 | 38 | responsive | not_applicable |
| sub-003 | 37 | 37 | 3 | 38 | lor_impaired | returned |
| sub-005 | 37 | 37 | 33 | 37 | responsive | not_applicable |
| sub-006 | 36 | 33 | 1 | 36 | lor_impaired | returned |
| sub-007 | 35 | 9 | 6 | 37 | lor_impaired | returned |
| sub-008 | 39 | 38 | 21 | 39 | lor_impaired | returned |
| sub-009 | 30 | 36 | 34 | 37 | responsive | not_applicable |
| sub-010 | 38 | 5 | 0 | 35 | lor_impaired | returned |
| sub-013 | 40 | 40 | 35 | 38 | responsive | not_applicable |
| sub-014 | 40 | 35 | 12 | 36 | lor_impaired | returned |
| sub-018 | 40 | 38 | 39 | 39 | responsive | not_applicable |
| sub-020 | 37 | 37 | 39 | 37 | responsive | not_applicable |
| sub-022 | 40 | 39 | 35 | 39 | responsive | not_applicable |
| sub-023 | 38 | 37 | 35 | 38 | responsive | not_applicable |
| sub-024 | 40 | 40 | 37 | 39 | responsive | not_applicable |
| sub-025 | 39 | 39 | 40 | 40 | responsive | not_applicable |
| sub-026 | 34 | 30 | 15 | 33 | lor_impaired | returned |
| sub-027 | 39 | 38 | 37 | 40 | responsive | not_applicable |
| sub-028 | 40 | 39 | 38 | 39 | responsive | not_applicable |
| sub-029 | 39 | 40 | 38 | 37 | responsive | not_applicable |

## Primary: occupancy Δ (later sedation − baseline) by LOR

| Status | n_LOR | n_resp | med LOR | med resp | Δ med | d | MW p | test |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| primary | 7 | 13 | 5.135 | 7.343 | -2.209 | 0.0258 | 0.7573 | NOT_TESTABLE |
| first_sedation_minus_baseline_lor_vs_responsive | 7 | 13 | 2.268 | 0.6664 | 1.601 | 0.678 | 0.2749 | NOT_TESTABLE |
| recovery_minus_baseline_lor_vs_responsive | 7 | 13 | 1.803 | 0.837 | 0.9663 | 0.681 | 0.4854 | NOT_TESTABLE |
| later_sedation_concentration_lor_vs_responsive | 7 | 13 | 1149 | 800 | 349 | 1.22 | 0.09559 | NOT_TESTABLE |

## Associations (later protocol sedation)

| Pair | n | Spearman ρ | p |
| --- | ---: | ---: | ---: |
| occupancy vs n_correct at later sedation | 20 | -0.0838 | 0.7255 |
| occupancy vs concentration at later sedation | 20 | 0.285 | 0.2239 |

Primary prediction: `lor_impaired occupancy Δ > responsive occupancy Δ`. Gate is ≥10 per arm. Protocol phase 3 remains a protocol label. Package `unresponsive` is not used.

Primary MW p = 0.7573, d = 0.0258, status `NOT_TESTABLE`.
