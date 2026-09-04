# 9D Jacobian Follow-Up Test Plan

This note lists the checks needed before `comatose_ndt_jacobian_9d.typ` should be treated as a manuscript rather than a draft.

## 1. Provenance and overlap

- Confirm that the article only uses the `9D`-enabled bundles:
  - `articles/CLINICAL/comatose_ndt/results/timeline_analysis_20260524_part1_primary12h_9d`
  - `articles/CLINICAL/comatose_ndt/results/mnps_summary_20260524_part1_primary12h_9d_targeted`
  - `articles/CLINICAL/comatose_ndt/results/timeline_analysis_20260523_part2_primary12h_9d`
  - `articles/CLINICAL/comatose_ndt/results/mnps_summary_20260523_part2_primary12h_9d`
- Verify `0` subject overlap and `0` run overlap before any pooled export.
- Write an explicit merge manifest for the `9D` article rather than relying on ad hoc concat tables.

## 2. Full outcome-contrast export

- Generate a dedicated manuscript-facing contrast bundle for:
  - `part1` `9D`
  - `part2` `9D`
  - pooled `9D`
- Export both:
  - `patient_timebin_outcome_contrasts.csv`
  - `run_level_outcome_contrasts.csv`
- Compute BH-FDR within the exact `global_mnps_jacobian_9d` metric family used in the article.

## 3. Candidate-family confirmation

- Recompute and rank all `global_mnps_jacobian_9d` metrics in `0_12 h`.
- Check whether these draft candidates remain article-facing after the formal rerun:
  - `spectral_radius_median`
  - `anisotropy_abs_eig_median`
  - `a_operator_norm_median`
  - `frobenius_norm_median`
  - `rotation_norm_median`
- Decide whether the article should freeze:
  - one lead metric,
  - a small predeclared family,
  - or a family-wise appendix plus one primary panel.

## 4. Robustness checks

- Site-stratified sensitivity.
- Shockable-only and non-shockable-only sensitivity.
- QC-only model using coverage and channel-count proxies.
- Correlation of article-facing `9D` Jacobian metrics with QC fields.
- Outlier sensitivity for each article-facing metric.
- LOSO or held-site sensitivity if any predictive model is added.

## 5. Relationship to the original coma article

- Quantify correlation between the chosen `9D` Jacobian metrics and:
  - `jacobian_fro_median`
  - `jacobian_spectral_radius_median`
  - `tube_d_eff_median`
  - `tube_a_operator_norm_median`
- Decide whether the follow-up article argues:
  - replication of the same biological signal in a different state space,
  - a cleaner local-linear surrogate,
  - or a genuinely distinct signal family.

## 6. Figures to add

- Main effect-size table or forest panel for the selected `9D` Jacobian family.
- Cohort/provenance overview for the `9D`-enabled bundles.
- Optional violin or ridge plots for the 2-3 strongest `9D` metrics.
- Optional correlation heatmap against the original reachability/Jacobian candidates.

## 7. Minimal manuscript checks

- `typst compile` succeeds.
- No missing citation keys in `cardiac_arrest_comatose_references.bib`.
- Every numeric claim in the manuscript maps to one explicit result file.
- Captions state whether each table is:
  - discovery-only,
  - verification-only,
  - or pooled.

## 8. Stretch goals

- Add a prediction section only if the `9D` feature family is frozen first.
- Compare `9D` Jacobian models against:
  - clinical + qEEG baseline,
  - original `3D` Jacobian comparator,
  - original reachability five-feature layer.
- If predictive sections are added, require nested or externally frozen feature selection rather than post hoc model expansion.
