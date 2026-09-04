# Early-versus-late distribution summary

This summary compares patient-level median summaries over two time windows built from the latest pooled hourly reachability bundle.

## Inputs

- input: `J:\repos\NoeticDiffusion\articles\CLINICAL\comatose_ndt\results\mnps_summary_20260602_combined_combat_corrected_hourly12h_cpc15\patient_timebin_signal_metrics.csv`
- early bins: `1_2h, 2_3h, 3_4h`
- late bins: `8_9h, 9_10h, 10_11h, 11_12h`
- metrics: `persistence_log_eig_var_median, persistence_kappa_median, tube_d_eff_median, tube_a_operator_norm_median, tube_capture_gate_median`

## Reading guide

- `bic_gain_2_vs_1 > 0` means the two-component Gaussian mixture fit outperformed a one-component fit by BIC.
- `component_separation_sigma` is the distance between the two fitted component means in pooled-sigma units.
- Transition rows track whether paired subjects stay in the low/high mode or switch between windows.

## Metric notes

### `persistence_log_eig_var_median`

- early BIC gain: `12.921`; late BIC gain: `3.484`
- early separation: `2.431` sigma; late separation: `2.493` sigma
- paired median late-minus-early shift: `0.127631` (Wilcoxon `p=8.758e-08`)
- transition counts: low->low `77`, low->high `43`, high->low `18`, high->high `102`
- high-mode fraction: early `0.500` -> late `0.604`

### `persistence_kappa_median`

- early BIC gain: `43.376`; late BIC gain: `407.929`
- early separation: `3.251` sigma; late separation: `28.277` sigma
- paired median late-minus-early shift: `7.43398e-08` (Wilcoxon `p=0.002064`)
- transition counts: low->low `239`, low->high `1`, high->low `0`, high->high `0`
- high-mode fraction: early `0.000` -> late `0.004`

### `tube_d_eff_median`

- early BIC gain: `10.126`; late BIC gain: `24.571`
- early separation: `2.604` sigma; late separation: `2.302` sigma
- paired median late-minus-early shift: `0.119212` (Wilcoxon `p=5.29e-07`)
- transition counts: low->low `60`, low->high `44`, high->low `22`, high->high `114`
- high-mode fraction: early `0.567` -> late `0.658`

### `tube_a_operator_norm_median`

- early BIC gain: `161.862`; late BIC gain: `136.402`
- early separation: `2.152` sigma; late separation: `1.960` sigma
- paired median late-minus-early shift: `-0.205933` (Wilcoxon `p=0.2541`)
- transition counts: low->low `119`, low->high `13`, high->low `15`, high->high `93`
- high-mode fraction: early `0.450` -> late `0.442`

### `tube_capture_gate_median`

- early BIC gain: `-4.547`; late BIC gain: `-7.182`
- early separation: `2.215` sigma; late separation: `1.880` sigma
- paired median late-minus-early shift: `-0.0547576` (Wilcoxon `p=0.005076`)
- transition counts: low->low `95`, low->high `19`, high->low `23`, high->high `103`
- high-mode fraction: early `0.525` -> late `0.508`

