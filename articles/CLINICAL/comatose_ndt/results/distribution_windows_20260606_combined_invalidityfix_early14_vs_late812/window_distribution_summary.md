# Early-versus-late distribution summary

This summary compares patient-level median summaries over two time windows built from the latest pooled hourly reachability bundle.

## Inputs

- input: `J:\repos\NoeticDiffusion\articles\CLINICAL\comatose_ndt\results\mnps_summary_20260606_combined_invalidityfix_hourly12h_cpc15\patient_timebin_signal_metrics.csv`
- early bins: `1_2h, 2_3h, 3_4h`
- late bins: `8_9h, 9_10h, 10_11h, 11_12h`
- metrics: `persistence_log_eig_var_median, persistence_kappa_median, tube_d_eff_median, tube_a_operator_norm_median, tube_capture_gate_median`

## Reading guide

- `bic_gain_2_vs_1 > 0` means the two-component Gaussian mixture fit outperformed a one-component fit by BIC.
- `component_separation_sigma` is the distance between the two fitted component means in pooled-sigma units.
- Transition rows track whether paired subjects stay in the low/high mode or switch between windows.

## Metric notes

### `persistence_log_eig_var_median`

- early BIC gain: `-9.753`; late BIC gain: `-8.948`
- early separation: `2.431` sigma; late separation: `2.488` sigma
- paired median late-minus-early shift: `0.171465` (Wilcoxon `p=5.267e-05`)
- transition counts: low->low `34`, low->high `12`, high->low `6`, high->high `48`
- high-mode fraction: early `0.540` -> late `0.600`

### `persistence_kappa_median`

- early BIC gain: `-7.250`; late BIC gain: `43.445`
- early separation: `2.755` sigma; late separation: `7.480` sigma
- paired median late-minus-early shift: `4.37708e-07` (Wilcoxon `p=0.06946`)
- transition counts: low->low `99`, low->high `1`, high->low `0`, high->high `0`
- high-mode fraction: early `0.000` -> late `0.010`

### `tube_d_eff_median`

- early BIC gain: `-2.182`; late BIC gain: `9.849`
- early separation: `2.647` sigma; late separation: `2.680` sigma
- paired median late-minus-early shift: `0.140404` (Wilcoxon `p=5.114e-05`)
- transition counts: low->low `25`, low->high `18`, high->low `8`, high->high `49`
- high-mode fraction: early `0.570` -> late `0.670`

### `tube_a_operator_norm_median`

- early BIC gain: `2.795`; late BIC gain: `11.552`
- early separation: `2.342` sigma; late separation: `2.042` sigma
- paired median late-minus-early shift: `-0.579039` (Wilcoxon `p=0.06095`)
- transition counts: low->low `54`, low->high `7`, high->low `16`, high->high `23`
- high-mode fraction: early `0.390` -> late `0.300`

### `tube_capture_gate_median`

- early BIC gain: `-7.073`; late BIC gain: `4.105`
- early separation: `0.898` sigma; late separation: `2.598` sigma
- paired median late-minus-early shift: `-0.0766154` (Wilcoxon `p=0.0003183`)
- transition counts: low->low `73`, low->high `6`, high->low `15`, high->high `6`
- high-mode fraction: early `0.210` -> late `0.120`

