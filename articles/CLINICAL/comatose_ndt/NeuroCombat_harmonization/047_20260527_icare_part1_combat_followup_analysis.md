## Session: Follow-up analyses on ComBat part1 pilot

Date: 2026-05-27

### Question

Why did feature-level ComBat appear to reduce site signal but not improve the downstream CPC1-vs-CPC5 pilot?

### Scope

- Paired subjects in pilot: `159`
- CPC1/CPC5 subjects used for follow-up: `139`
- Input bundle:
  - `results/combat_pilot_20260527/combat_pilot_subject_level.csv`
  - `results/combat_pilot_20260527/combat_pilot_site_dependence_detail.csv`

### Analysis 1: hospital-outcome imbalance

If hospitals carry different CPC mixtures, then de-batching can remove nuisance structure and real predictive proxy structure at the same time.

- chi-square hospital x CPC: `chi2 = 11.840`, `p = 0.0186`
- Cramer's V: `0.292`
- Interpretation: the CPC mixture is not site-neutral in this paired cohort.

| hospital | cpc_1 | cpc_5 | n_total | cpc1_rate |
|---|---|---|---|---|
| A | 35 | 26 | 61 | 0.574 |
| B | 13 | 14 | 27 | 0.481 |
| D | 11 | 8 | 19 | 0.579 |
| E | 2 | 15 | 17 | 0.118 |
| F | 8 | 7 | 15 | 0.533 |

Notable point: hospital `E` is strongly poor-outcome enriched (`2` CPC1 vs `15` CPC5, CPC1 rate `0.118`).

### Analysis 2: feature-family de-batching

Family summaries below use the subject-level hospital effect sizes from the pilot (`eta^2` by hospital for each feature). More negative deltas mean ComBat reduced site dependence.

| family | median_eta2_baseline | median_eta2_combat | delta_median_eta2_combat_minus_baseline | q_lt_0_05_baseline | q_lt_0_05_combat |
|---|---|---|---|---|---|
| dynamics | 0.042 | 0.058 | 0.016 | 3 | 4 |
| delta | 0.049 | 0.027 | -0.022 | 0 | 8 |
| theta | 0.048 | 0.030 | -0.019 | 0 | 8 |
| alpha | 0.049 | 0.023 | -0.026 | 1 | 8 |
| beta | 0.053 | 0.148 | 0.095 | 7 | 8 |
| gamma | 0.032 | 0.034 | 0.002 | 6 | 8 |
| highfreq_power_30_45 | 0.032 | 0.034 | 0.002 | 6 | 8 |
| alpha_theta | 0.025 | 0.032 | 0.007 | 1 | 0 |
| beta_alpha | 0.045 | 0.040 | -0.005 | 2 | 4 |
| hjorth_mobility | 0.168 | 0.031 | -0.137 | 8 | 0 |
| hjorth_complexity | 0.200 | 0.025 | -0.175 | 8 | 0 |
| permutation_entropy | 0.166 | 0.021 | -0.146 | 8 | 0 |
| sample_entropy | 0.166 | 0.021 | -0.146 | 8 | 0 |
| embodied_arousal_proxy | 0.034 | nan | nan | 1 | nan |

Readout:
- strongest site reductions concentrated in Hjorth complexity and entropy-style families
- beta-family features remained relatively site-coupled, and several beta features became more site-linked after ComBat

### Analysis 3: within-site outcome signal after removing hospital means/scales

For each feature, values were z-scored within hospital and then CPC1-vs-CPC5 Cohen's d was computed on the pooled hospital-standardized values. This asks whether the feature still carries outcome structure after local site normalization.

| family | median_abs_d_baseline | median_abs_d_combat | delta_median_abs_d_combat_minus_baseline | n_abs_d_ge_0_5_baseline | n_abs_d_ge_0_5_combat |
|---|---|---|---|---|---|
| dynamics | 0.304 | 0.268 | -0.035 | 0 | 0 |
| delta | 0.206 | 0.063 | -0.143 | 0 | 0 |
| theta | 0.072 | 0.101 | 0.029 | 0 | 0 |
| alpha | 0.072 | 0.074 | 0.002 | 0 | 0 |
| beta | 0.079 | 0.173 | 0.094 | 0 | 0 |
| gamma | 0.123 | 0.094 | -0.028 | 0 | 0 |
| highfreq_power_30_45 | 0.123 | 0.094 | -0.028 | 0 | 0 |
| alpha_theta | 0.211 | 0.211 | -0.000 | 0 | 0 |
| beta_alpha | 0.130 | 0.064 | -0.066 | 0 | 0 |
| hjorth_mobility | 0.337 | 0.335 | -0.002 | 0 | 0 |
| hjorth_complexity | 0.129 | 0.130 | 0.000 | 0 | 0 |
| permutation_entropy | 0.523 | 0.517 | -0.006 | 5 | 5 |
| sample_entropy | 0.523 | 0.517 | -0.006 | 5 | 5 |
| embodied_arousal_proxy | 0.126 | nan | nan | 0 | 0 |

Readout:
- if the delta above is negative, ComBat weakened the within-site outcome separation for that family
- if the delta is positive, the family retained or improved signal after hospital standardization

### Analysis 4: how strongly each family was perturbed

Median absolute paired subject-level symmetric percent shifts quantify how hard ComBat moved each family relative to the old export. This measure is bounded to `[0, 200]` and is more stable for near-zero features.

| family | median_feature_shift_pct | p95_feature_shift_pct | max_feature_shift_pct |
|---|---|---|---|
| dynamics | 6.19 | 6.89 | 6.97 |
| delta | 192.93 | 198.29 | 199.43 |
| theta | 160.88 | 186.02 | 194.35 |
| alpha | 104.86 | 148.35 | 162.94 |
| beta | 146.36 | 188.16 | 197.12 |
| gamma | 139.31 | 175.56 | 181.29 |
| highfreq_power_30_45 | 139.31 | 175.56 | 181.29 |
| alpha_theta | 8.32 | 11.93 | 12.01 |
| beta_alpha | 64.37 | 142.92 | 157.78 |
| hjorth_mobility | 19.10 | 22.53 | 23.59 |
| hjorth_complexity | 11.77 | 14.08 | 14.09 |
| permutation_entropy | 4.34 | 6.38 | 7.16 |
| sample_entropy | 4.34 | 6.38 | 7.16 |
| embodied_arousal_proxy | nan | nan | nan |

### Feature spot-checks

Largest site-signal reductions:

| feature | family | eta2_baseline | eta2_combat | delta_eta2_combat_minus_baseline |
|---|---|---|---|---|
| raw__eeg_hjorth_complexity__g_frontal | hjorth_complexity | 0.259 | 0.031 | -0.228 |
| raw__eeg_permutation_entropy__g_midline | permutation_entropy | 0.245 | 0.028 | -0.217 |
| raw__eeg_sample_entropy__g_midline | sample_entropy | 0.245 | 0.028 | -0.217 |
| raw__eeg_hjorth_complexity | hjorth_complexity | 0.219 | 0.025 | -0.194 |
| raw__eeg_hjorth_complexity__g_right_hemisphere | hjorth_complexity | 0.215 | 0.024 | -0.191 |
| raw__eeg_sample_entropy__g_central | sample_entropy | 0.208 | 0.022 | -0.186 |
| raw__eeg_permutation_entropy__g_central | permutation_entropy | 0.208 | 0.022 | -0.186 |
| raw__eeg_hjorth_complexity__g_parietal_occipital | hjorth_complexity | 0.198 | 0.021 | -0.176 |

Largest within-site outcome losses:

| feature | family | abs_d_baseline | abs_d_combat | delta_abs_d_combat_minus_baseline |
|---|---|---|---|---|
| raw__eeg_delta__g_parietal_occipital | delta | 0.244 | 0.025 | -0.219 |
| raw__eeg_delta__g_frontal | delta | 0.214 | 0.003 | -0.211 |
| raw__eeg_delta__g_central | delta | 0.205 | 0.008 | -0.197 |
| raw__eeg_delta__g_midline | delta | 0.208 | 0.031 | -0.177 |
| raw__eeg_beta_alpha__g_midline | beta_alpha | 0.159 | 0.046 | -0.113 |
| raw__eeg_highfreq_power_30_45__g_midline | highfreq_power_30_45 | 0.114 | 0.012 | -0.103 |
| raw__eeg_gamma__g_midline | gamma | 0.114 | 0.012 | -0.103 |
| raw__eeg_beta_alpha__g_central | beta_alpha | 0.213 | 0.116 | -0.096 |

Largest within-site outcome gains:

| feature | family | abs_d_baseline | abs_d_combat | delta_abs_d_combat_minus_baseline |
|---|---|---|---|---|
| raw__eeg_beta__g_right_hemisphere | beta | 0.002 | 0.137 | 0.135 |
| raw__eeg_beta__g_left_hemisphere | beta | 0.087 | 0.206 | 0.119 |
| raw__eeg_theta | theta | 0.004 | 0.112 | 0.108 |
| raw__eeg_beta_alpha__g_right_hemisphere | beta_alpha | 0.006 | 0.110 | 0.104 |
| raw__eeg_beta | beta | 0.071 | 0.174 | 0.103 |
| dyn__mnps_rms | dynamics | 0.399 | 0.490 | 0.091 |
| raw__eeg_beta__g_temporal | beta | 0.013 | 0.084 | 0.071 |
| raw__eeg_theta__g_midline | theta | 0.007 | 0.077 | 0.070 |

### Interpretation

- The paired CPC cohort is hospital-imbalanced, so site is partly entangled with prognosis in the observed data.
- ComBat did de-batch several raw feature families, especially entropy/Hjorth-style families.
- But de-batching was not uniformly beneficial: some beta-related families stayed site-linked, and several feature families lost within-site CPC separation after ComBat.
- This makes the overall pilot result much less paradoxical: ComBat can remove real nuisance while also stripping away site-correlated proxy signal that the baseline classifier was using.
- In this cohort, the current ComBat setup looks more like a successful de-batching transform than a successful downstream prognostic enhancement.

### Takeaway

The most plausible explanation is not that harmonization failed, but that the present ComBat configuration removed site-linked structure faster than it preserved clinically useful within-site separation. That is compatible with lower hospital-predictability and lower CPC predictability at the same time.
