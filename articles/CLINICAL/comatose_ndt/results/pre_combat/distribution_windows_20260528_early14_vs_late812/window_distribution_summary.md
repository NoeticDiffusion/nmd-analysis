# Early-versus-late distribution summary

This summary compares patient-level median summaries over two time windows built from the latest pooled hourly reachability bundle.

## Inputs

- input: `J:\repos\NoeticDiffusion\articles\CLINICAL\comatose_ndt\results\mnps_summary_20260525_combined_cpc15_hourly12h\patient_timebin_signal_metrics.csv`
- early bins: `1_2h, 2_3h, 3_4h`
- late bins: `8_9h, 9_10h, 10_11h, 11_12h`
- metrics: `persistence_log_eig_var_median, persistence_kappa_median, tube_d_eff_median, tube_a_operator_norm_median, tube_capture_gate_median`

## Reading guide

- `bic_gain_2_vs_1 > 0` means the two-component Gaussian mixture fit outperformed a one-component fit by BIC.
- `component_separation_sigma` is the distance between the two fitted component means in pooled-sigma units.
- Transition rows track whether paired subjects stay in the low/high mode or switch between windows.

## Metric notes

### `persistence_log_eig_var_median`

- early BIC gain: `105.597`; late BIC gain: `99.755`
- early separation: `3.527` sigma; late separation: `4.065` sigma
- paired median late-minus-early shift: `0.118459` (Wilcoxon `p=4.422e-05`)
- transition counts: low->low `163`, low->high `22`, high->low `4`, high->high `74`
- high-mode fraction: early `0.297` -> late `0.365`

### `persistence_kappa_median`

- early BIC gain: `1241.653`; late BIC gain: `1196.645`
- early separation: `2.283` sigma; late separation: `2.999` sigma
- paired median late-minus-early shift: `0.000153851` (Wilcoxon `p=0.0003346`)
- transition counts: low->low `135`, low->high `6`, high->low `4`, high->high `118`
- high-mode fraction: early `0.464` -> late `0.471`

### `tube_d_eff_median`

- early BIC gain: `20.235`; late BIC gain: `33.638`
- early separation: `3.215` sigma; late separation: `3.532` sigma
- paired median late-minus-early shift: `0.0411168` (Wilcoxon `p=0.000228`)
- transition counts: low->low `172`, low->high `22`, high->low `8`, high->high `61`
- high-mode fraction: early `0.262` -> late `0.316`

### `tube_a_operator_norm_median`

- early BIC gain: `660.514`; late BIC gain: `688.223`
- early separation: `2.778` sigma; late separation: `2.970` sigma
- paired median late-minus-early shift: `-0.022575` (Wilcoxon `p=0.04732`)
- transition counts: low->low `111`, low->high `8`, high->low `12`, high->high `132`
- high-mode fraction: early `0.548` -> late `0.532`

### `tube_capture_gate_median`

- early BIC gain: `358.485`; late BIC gain: `357.553`
- early separation: `5.224` sigma; late separation: `5.075` sigma
- paired median late-minus-early shift: `-0.0235519` (Wilcoxon `p=0.0006842`)
- transition counts: low->low `128`, low->high `4`, high->low `3`, high->high `128`
- high-mode fraction: early `0.498` -> late `0.502`

