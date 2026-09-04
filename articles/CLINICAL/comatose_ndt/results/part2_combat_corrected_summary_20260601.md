# Part2 corrected ComBat summary 20260601

## New corrected-ComBat outputs

Source processed root:

- `J:/repos/NoeticDiffusion/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260601_143502_part2_combat`

New outputs written under `articles/CLINICAL/comatose_ndt/results/`:

- `timeline_analysis_20260601_part2_combat_corrected_primary12h`
- `timeline_analysis_20260601_part2_combat_corrected_hourly12h`
- `mnps_summary_20260601_part2_combat_corrected_primary12h_cpc15`
- `outcome_contrasts_20260601_part2_combat_corrected_primary12h_cpc15`
- `mnps_summary_20260601_part2_combat_corrected_hourly12h_9djac_cpc15`
- `outcome_contrasts_20260601_part2_combat_corrected_hourly12h_9djac_cpc15`
- `outcome_contrasts_20260601_part2_precombat_9d_jacobian_reference`

## Sanity check

The corrected ComBat export no longer shows the earlier `e_m` collapse:

- sampled `coords_9d_subject_anchored` rows were fully finite
- `e_m` had finite fraction `1.0`
- `3D` rows were also fully finite

The new primary `mnps_summary` handoff now exposes all requested families:

- `global_mnps_3d`
- `global_mnps_9d`
- `global_mnps_jacobian_3d`
- `global_mnps_jacobian_9d`
- `reachability_cones`

## Primary `0_12h` headline rows

These are the strongest patient-level `0_12h` rows from the corrected-ComBat primary contrast table.

- `global_mnps_3d` / `m_std`: delta-median `-0.1083`, Cohen's `d = -0.501`, Mann-Whitney `p = 0.0138`
- `global_mnps_9d` / `m_e_std`: delta-median `-0.1669`, Cohen's `d = -0.548`, `p = 6.03e-4`
- `global_mnps_jacobian_3d` / `spectral_radius_median`: delta-median `-0.006225`, Cohen's `d = -0.712`, `p = 1.03e-5`
- `global_mnps_jacobian_9d` / `spectral_radius_median`: delta-median `-0.009566`, Cohen's `d = -0.736`, `p = 6.55e-6`

For reachability, the numerically smallest `p` row was `tube_kappa_mean`, but it is hard to interpret because the raw scale is unstable. More article-friendly corrected-ComBat reachability rows were:

- `tube_q_ratio_h4_median`: delta-median `0.03564`, Cohen's `d = 0.668`, `p = 6.83e-4`
- `cone_dir_entropy_h4_median`: delta-median `0.1294`, Cohen's `d = 0.576`, `p = 2.97e-3`
- `pred_err_h4`: delta-median `-0.2445`, Cohen's `d = -0.266`, `p = 2.92e-4`
- `persistence_log_eig_var_median`: delta-median `0.5103`, Cohen's `d = 0.168`, `p = 0.0123`

Primary extreme-outcome coverage in the corrected-ComBat contrast table:

- `70` CPC1 subjects
- `68` CPC5 subjects

## Comparison against preserved `pre_combat` references

Direct `part2` references available in `pre_combat` existed for:

- reachability
- `9D` Jacobian

No exact preserved `part2` pre-ComBat analogue was available for article-local `MNPS 3D`, `MNPS 9D`, or `3D` Jacobian in the current saved folder set, so those are reported here as new corrected-ComBat results only.

### Reachability

Some reachability rows weakened relative to `pre_combat`:

- `tube_a_operator_norm_median`: old `d = -0.713`, `p = 1.22e-5`; new `d = -0.228`, `p = 0.492`
- `tube_a_operator_norm_mean`: old `d = -0.557`, `p = 3.16e-5`; new `d = -0.320`, `p = 0.205`

Some reachability rows stayed directional but with a different balance:

- `cone_dir_entropy_h4_median`: old `d = 0.684`, `p = 3.93e-5`; new `d = 0.576`, `p = 2.97e-3`
- `cone_dir_entropy_norm_h4_median`: old `d = 0.684`, `p = 3.93e-5`; new `d = 0.576`, `p = 2.97e-3`
- `persistence_log_eig_var_median`: old `d = 0.169`, `p = 3.28e-5`; new `d = 0.168`, `p = 0.0123`

Some rows strengthened materially in the corrected-ComBat rerun:

- `tube_q_ratio_h4_median`: old `d = 0.183`, `p = 0.253`; new `d = 0.668`, `p = 6.83e-4`
- `pred_err_h4`: old `d = -0.471`, `p = 0.0182`; new `d = -0.266`, `p = 2.92e-4`

### `9D` Jacobian

Using hourly/all-time-bin references for the preserved old `part2` `9D` Jacobian bundle, the corrected-ComBat rerun was broadly directionally consistent and often stronger:

- `spectral_radius_mean`: old delta-median `-0.006809`, `d = -0.0749`, `p = 6.66e-21`; new delta-median `-0.01362`, `d = -0.0128`, `p = 5.34e-37`
- `spectral_radius_median`: old delta-median `-0.004381`, `d = -0.511`, `p = 3.91e-21`; new delta-median `-0.008647`, `d = -0.661`, `p = 2.06e-36`
- `anisotropy_abs_eig_mean`: old delta-median `-0.0001695`, `d = -0.0745`, `p = 1.75e-18`; new delta-median `-0.0004395`, `d = -0.0550`, `p = 3.37e-29`
- `a_operator_norm_median`: old delta-median `-0.03489`, `d = -0.299`, `p = 1.20e-12`; new delta-median `-0.03091`, `d = -0.372`, `p = 8.98e-16`

## Takeaway

The corrected-ComBat `part2` rerun now behaves like a real article-facing dataset again:

- `9D` metrics are numerically present
- Jacobian and reachability both export broad metric surfaces
- the strongest new corrected-ComBat primary signals sit in `MNPS 9D` dispersion and both `3D` and `9D` Jacobian spectral-radius rows

Relative to the saved pre-ComBat references, the clearest pattern is not a uniform strengthening of everything. Instead:

- `9D` Jacobian looks broadly preserved or stronger
- reachability appears partly redistributed, with some older operator-norm rows weakening while entropy / `q_ratio` / prediction-error style rows become more prominent
