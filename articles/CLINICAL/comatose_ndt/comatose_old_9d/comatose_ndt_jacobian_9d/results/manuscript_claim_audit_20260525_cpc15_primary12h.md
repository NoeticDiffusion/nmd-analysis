# 9D Jacobian Manuscript Claim Audit

This file freezes the source mapping for every manuscript-facing numeric statement in `comatose_ndt_jacobian_9d.typ`.

## Analysis Scopes

- `primary_result_export`
  File: `results/outcome_contrasts_9d_jacobian_20260525_cpc15_primary12h/`
  Use for: part1 / part2 / pooled `9D` Jacobian contrasts, ranks, `d`, `p`, `q`, medians, subject counts, provenance overlap checks.

- `result_ledger`
  File: `results/result_ledger_20260525_cpc15_primary12h/metric_result_ledger.csv`
  Use for: frozen article hierarchy, tier labels, pooled-promoted vs legacy-supportive classification.

- `robustness_internal`
  Files:
  `results/robustness_20260525_cpc15_primary12h/subset_metric_contrasts.csv`
  `results/robustness_20260525_cpc15_primary12h/qc_only_model_summary.csv`
  `results/robustness_20260525_cpc15_primary12h/metric_qc_correlations.csv`
  `results/robustness_20260525_cpc15_primary12h/label_permutation_summary.csv`
  `results/robustness_20260525_cpc15_primary12h/winsorization_sensitivity.csv`
  `results/robustness_20260525_cpc15_primary12h/leave_one_site_out_effects.csv`
  Use for: shockable/non-shockable sensitivity, QC-only model, QC correlations, permutation, winsorization, leave-one-site-out robustness.

- `prediction_internal_synthesis`
  Files:
  `results/incremental_validity_20260525_cpc15_primary12h/incremental_validity_summary.csv`
  `results/incremental_validity_20260525_cpc15_primary12h/incremental_validity_site_summary.csv`
  `results/incremental_validity_20260525_cpc15_primary12h/incremental_validity_feature_summary.csv`
  `results/incremental_validity_20260525_cpc15_primary12h/joint_signal_correlation_matrix.csv`
  Use for: repeated-CV metrics, LOSO metrics, combined-model coefficients, inter-layer correlation claims.

## Manuscript Claim Map

### Metadata and Abstract

- Provenance statement "0 subject overlap and 0 run overlap":
  Scope: `primary_result_export`
  File: `results/outcome_contrasts_9d_jacobian_20260525_cpc15_primary12h/manifest.json`

- `spectral_radius_median` part1 / part2 / pooled `d`, pooled `p`, pooled `q`:
  Scope: `result_ledger`
  File: `results/result_ledger_20260525_cpc15_primary12h/metric_result_ledger.csv`

- `anisotropy_abs_eig_median` part1 / part2 / pooled `d`:
  Scope: `result_ledger`
  File: `results/result_ledger_20260525_cpc15_primary12h/metric_result_ledger.csv`

- `mdr_median`, `rotational_power_mean`, `rotational_power_median` pooled `d` values in the abstract:
  Scope: `result_ledger`
  File: `results/result_ledger_20260525_cpc15_primary12h/metric_result_ledger.csv`

- Shockable-only and non-shockable-only values for `rotational_power_mean` and `mdr_median`:
  Scope: `robustness_internal`
  File: `results/robustness_20260525_cpc15_primary12h/subset_metric_contrasts.csv`

- QC-only `AUROC = 0.559`:
  Scope: `robustness_internal`
  File: `results/robustness_20260525_cpc15_primary12h/qc_only_model_summary.csv`

- Repeated-CV `AUROC` values for `jacobian9d_only`, `reachability_only`, `jacobian3d_only`, `clinical_plus_eeg`, `clinical_plus_eeg_plus_jacobian9d`, and `clinical_plus_eeg_plus_reachability_plus_jacobian9d`:
  Scope: `prediction_internal_synthesis`
  File: `results/incremental_validity_20260525_cpc15_primary12h/incremental_validity_summary.csv`

- LOSO `AUROC = 0.668` for the combined reachability+`9D` model:
  Scope: `prediction_internal_synthesis`
  File: `results/incremental_validity_20260525_cpc15_primary12h/incremental_validity_site_summary.csv`

### Scope Table

- Analyzable-subject counts `161`, `140`, `301` and extreme-outcome counts `141`, `140`, `281`:
  Scope: `primary_result_export`
  Files:
  `results/outcome_contrasts_9d_jacobian_20260525_cpc15_primary12h/manifest.json`
  `results/outcome_contrasts_9d_jacobian_20260525_cpc15_primary12h/part1/selection_audit_top5.csv`
  `results/outcome_contrasts_9d_jacobian_20260525_cpc15_primary12h/part2/selection_audit_top5.csv`
  `results/outcome_contrasts_9d_jacobian_20260525_cpc15_primary12h/pooled/article_candidate_ranking.csv`

### Methods

- Revised hierarchy ordering and legacy-supportive demotion:
  Scope: `result_ledger`
  File: `results/result_ledger_20260525_cpc15_primary12h/metric_result_ledger.csv`

### Results Main Text

- Lead and secondary replicated values in "The formal `20260525` export changes the pooled hierarchy":
  Scope: `result_ledger`
  File: `results/result_ledger_20260525_cpc15_primary12h/metric_result_ledger.csv`

- Pooled-promoted `mdr` / rotational-power values in the same section:
  Scope: `result_ledger`
  File: `results/result_ledger_20260525_cpc15_primary12h/metric_result_ledger.csv`

- Revised table `@tab-primary` medians, `d`, `p`, `q`:
  Scope: `primary_result_export`
  Files:
  `results/outcome_contrasts_9d_jacobian_20260525_cpc15_primary12h/part1/article_candidate_ranking.csv`
  `results/outcome_contrasts_9d_jacobian_20260525_cpc15_primary12h/part2/article_candidate_ranking.csv`
  `results/outcome_contrasts_9d_jacobian_20260525_cpc15_primary12h/pooled/article_candidate_ranking.csv`

- Full-cohort, shockable-only, and non-shockable-only effect sizes:
  Scope: `robustness_internal`
  File: `results/robustness_20260525_cpc15_primary12h/subset_metric_contrasts.csv`

- Permutation `empirical p` values:
  Scope: `robustness_internal`
  File: `results/robustness_20260525_cpc15_primary12h/label_permutation_summary.csv`

- QC-only model values and QC correlation examples:
  Scope: `robustness_internal`
  Files:
  `results/robustness_20260525_cpc15_primary12h/qc_only_model_summary.csv`
  `results/robustness_20260525_cpc15_primary12h/metric_qc_correlations.csv`

- Correlations versus reachability and older `3D` Jacobian layers:
  Scope: `prediction_internal_synthesis`
  File: `results/incremental_validity_20260525_cpc15_primary12h/joint_signal_correlation_matrix.csv`

- Repeated-CV and LOSO performance values in the prediction section:
  Scope: `prediction_internal_synthesis`
  Files:
  `results/incremental_validity_20260525_cpc15_primary12h/incremental_validity_summary.csv`
  `results/incremental_validity_20260525_cpc15_primary12h/incremental_validity_site_summary.csv`

- Statement that combined coefficients are led by `tube_d_eff_median`, qEEG mobility/complexity, and active `9D` features:
  Scope: `prediction_internal_synthesis`
  File: `results/incremental_validity_20260525_cpc15_primary12h/incremental_validity_feature_summary.csv`

### Figure and Table Caption Contract

- `@fig-9d-provenance`:
  Scope: `primary_result_export`
  File: `results/outcome_contrasts_9d_jacobian_20260525_cpc15_primary12h/manifest.json`

- `@fig-9d-revised-forest`:
  Scope: `result_ledger`
  Files:
  `results/result_ledger_20260525_cpc15_primary12h/metric_result_ledger.csv`
  `results/outcome_contrasts_9d_jacobian_20260525_cpc15_primary12h/*/article_candidate_ranking.csv`

- `@fig-9d-distributions`:
  Scope: `primary_result_export`
  Files:
  `../comatose_ndt/results/mnps_summary_20260524_part1_primary12h_9d_targeted/patient_timebin_signal_metrics.csv`
  `../comatose_ndt/results/mnps_summary_20260523_part2_primary12h_9d/patient_timebin_signal_metrics.csv`

- `@fig-9d-robustness`:
  Scope: `robustness_internal`
  Files:
  `results/robustness_20260525_cpc15_primary12h/subset_metric_contrasts.csv`
  `results/robustness_20260525_cpc15_primary12h/winsorization_sensitivity.csv`

- `@fig-9d-corr`:
  Scope: `prediction_internal_synthesis`
  File: `results/incremental_validity_20260525_cpc15_primary12h/joint_signal_correlation_matrix.csv`

- `@tab-predictive` and `@fig-9d-prediction`:
  Scope: `prediction_internal_synthesis`
  Files:
  `results/incremental_validity_20260525_cpc15_primary12h/incremental_validity_summary.csv`
  `results/incremental_validity_20260525_cpc15_primary12h/incremental_validity_site_summary.csv`

### Limitations and Discussion

- Shockable/non-shockable heterogeneity claim for `mdr_median` and `rotational_power_median`:
  Scope: `robustness_internal`
  File: `results/robustness_20260525_cpc15_primary12h/subset_metric_contrasts.csv`

- Statement that `3D` Jacobian remains competitive:
  Scope: `prediction_internal_synthesis`
  File: `results/incremental_validity_20260525_cpc15_primary12h/incremental_validity_summary.csv`

- Complementarity framing and modest combined-model gain:
  Scope: `prediction_internal_synthesis`
  Files:
  `results/incremental_validity_20260525_cpc15_primary12h/incremental_validity_summary.csv`
  `results/incremental_validity_20260525_cpc15_primary12h/incremental_validity_site_summary.csv`
