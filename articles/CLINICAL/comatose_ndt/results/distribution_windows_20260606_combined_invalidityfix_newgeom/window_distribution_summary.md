# Early-versus-late distribution summary

This summary compares patient-level median summaries over two time windows built from the latest pooled hourly reachability bundle.

## Inputs

- input: `..\results\mnps_summary_20260606_combined_invalidityfix_hourly12h_cpc15\patient_timebin_signal_metrics.csv`
- early bins: `1_2h, 2_3h, 3_4h`
- late bins: `8_9h, 9_10h, 10_11h, 11_12h`
- metrics: `persistence_log_det_median, persistence_hysteresis_log_det_median, persistence_log_eig_var_median, tube_d_eff_median, tube_capture_gate_median`

## Reading guide

- `bic_gain_2_vs_1 > 0` means the two-component Gaussian mixture fit outperformed a one-component fit by BIC.
- `component_separation_sigma` is the distance between the two fitted component means in pooled-sigma units.
- Transition rows track whether paired subjects stay in the low/high mode or switch between windows.

## Metric notes

### `persistence_log_det_median`

- early BIC gain: `-2.835`; late BIC gain: `-4.961`
- early separation: `2.380` sigma; late separation: `2.716` sigma
- paired median late-minus-early shift: `0.170669` (Wilcoxon `p=4.73e-06`)
- transition counts: low->low `32`, low->high `24`, high->low `5`, high->high `39`
- high-mode fraction: early `0.440` -> late `0.630`

### `persistence_hysteresis_log_det_median`

- early BIC gain: `14.561`; late BIC gain: `55.034`
- early separation: `2.004` sigma; late separation: `1.538` sigma
- paired median late-minus-early shift: `-0.323255` (Wilcoxon `p=1.595e-05`)
- transition counts: low->low `57`, low->high `5`, high->low `19`, high->high `19`
- high-mode fraction: early `0.380` -> late `0.240`

### `persistence_log_eig_var_median`

- early BIC gain: `-9.753`; late BIC gain: `-8.948`
- early separation: `2.431` sigma; late separation: `2.488` sigma
- paired median late-minus-early shift: `0.171465` (Wilcoxon `p=5.267e-05`)
- transition counts: low->low `34`, low->high `12`, high->low `6`, high->high `48`
- high-mode fraction: early `0.540` -> late `0.600`

### `tube_d_eff_median`

- early BIC gain: `-2.182`; late BIC gain: `9.849`
- early separation: `2.647` sigma; late separation: `2.680` sigma
- paired median late-minus-early shift: `0.140404` (Wilcoxon `p=5.114e-05`)
- transition counts: low->low `25`, low->high `18`, high->low `8`, high->high `49`
- high-mode fraction: early `0.570` -> late `0.670`

### `tube_capture_gate_median`

- early BIC gain: `-7.073`; late BIC gain: `4.105`
- early separation: `0.898` sigma; late separation: `2.598` sigma
- paired median late-minus-early shift: `-0.0766154` (Wilcoxon `p=0.0003183`)
- transition counts: low->low `73`, low->high `6`, high->low `15`, high->high `6`
- high-mode fraction: early `0.210` -> late `0.120`

