# Apollo within-subject stage contrasts (stage_within_subject_20260921)

Paired later-minus-earlier on subject/phase medians. Holm is only H1/H2 sign tests on first sedation minus baseline. BH-FDR is across the frozen 15-metric × 6-contrast Wilcoxon family. Status: `exploratory_discovery_20260921_g4_not_locked`. Not consciousness. Not confirmatory amplitude.

Subjects with both primary phases: see `n_pairs` in the primary block. Bootstrap 10000, seed 20260920.

## Missingness (recordings with a finite included median)

| Metric | n finite / 80 |
| --- | ---: |
| `diffusion_total` | 80/80 |
| `diffusion_effective_dimension` | 80/80 |
| `R_b_over_a` | 0/80 |
| `A_bD` | 0/80 |
| `diffusion_concentration` | 80/80 |
| `neighbor_gain_q90` | 80/80 |
| `operator_max_gain_rate` | 46/80 |
| `history_predictive_gain` | 80/80 |
| `jacobian_spectral_abscissa` | 80/80 |
| `jacobian_trace` | 80/80 |
| `jacobian_rotation_norm` | 80/80 |
| `jacobian_reactivity_gap` | 80/80 |
| `turning_rate` | 80/80 |
| `ftr_g_max_h1` | 80/80 |
| `ftr_g_max_h2` | 80/80 |

## Primary contrast: first protocol sedation − pre-drug baseline

| Role | Metric | n | later med | base med | Δ med | d_z | sign p | Holm p | BH q |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| H1 | `diffusion_total` | 20 | 0.2181 | 0.2412 | -0.03906 | -0.702 | 0.01182 | 0.02364 | 0.2845 |
| H2 | `diffusion_effective_dimension` | 20 | 2.163 | 2.062 | 0.036 | 0.113 | 0.8238 | 0.8238 | 0.9115 |
| S1 | `R_b_over_a` | 0 | nan | nan | nan | nan | nan | - | nan |
| S1 | `A_bD` | 0 | nan | nan | nan | nan | nan | - | nan |
| exploratory | `diffusion_concentration` | 20 | 0.6008 | 0.6157 | -0.006291 | -0.085 | 0.8238 | - | 0.9115 |
| S2 | `neighbor_gain_q90` | 20 | 3.194 | 3.188 | -0.05416 | -0.205 | 0.2632 | - | 0.8393 |
| S2 | `operator_max_gain_rate` | 4 | -0.08343 | -0.07324 | -0.003085 | 0.038 | 1 | - | 1 |
| S3 | `history_predictive_gain` | 20 | -0.07951 | -0.07844 | 0.01628 | -0.103 | 0.8238 | - | 0.9267 |
| exploratory | `jacobian_spectral_abscissa` | 20 | 0.02198 | 0.02597 | -0.005944 | -0.313 | 0.1153 | - | 0.7148 |
| exploratory | `jacobian_trace` | 20 | -0.005434 | 0.003531 | -0.009935 | -0.439 | 0.2632 | - | 0.5916 |
| exploratory | `jacobian_rotation_norm` | 20 | 0.0825 | 0.08859 | 0.0002067 | -0.251 | 0.8238 | - | 0.8393 |
| exploratory | `jacobian_reactivity_gap` | 20 | 0.02679 | 0.02857 | -0.0004134 | -0.221 | 1 | - | 0.8393 |
| exploratory | `turning_rate` | 20 | 0.3855 | 0.3882 | -0.001381 | 0.125 | 1 | - | 0.9216 |
| exploratory | `ftr_g_max_h1` | 20 | 1.228 | 1.261 | -0.03467 | -0.394 | 0.2632 | - | 0.7148 |
| exploratory | `ftr_g_max_h2` | 20 | 1.44 | 1.514 | -0.08628 | -0.462 | 0.1153 | - | 0.5916 |

## FDR-significant discovery rows (|d_z| order)

R_b_over_a and A_bD are all-NaN in this export (S1 not testable). operator_max_gain_rate is computed in 46/80 recordings.
No Wilcoxon BH q < 0.05 in the frozen family (78 finite tests). No within-contrast BH q < 0.05 either.

Do not read protocol phase 3 as unresponsiveness. Do not treat recovery as a guaranteed reversal.
H1/H2 remain exploratory local chart geometry because the export is `subject_anchored` with ComBat disabled.
