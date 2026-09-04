# Between-run IQR and MAD — 12-24h pilot

- cohort: `90` subjects (`42` CPC1, `48` CPC5)
- time bin: `12_24h`
- minimum runs for IQR/MAD: `2`
- metrics: `tube_d_eff_median`, `persistence_kappa_median`, `persistence_log_eig_var_median`, `tube_a_operator_norm_median`, `tube_capture_gate_median`

## Contrasts

### IQR
- `persistence_kappa_median_iqr`: CPC1 `0.0001757` vs CPC5 `0.0004329`, d=`-1.316`, p=`0.0727`, n=`8/4`
- `tube_a_operator_norm_median_iqr`: CPC1 `0.7782` vs CPC5 `0.2395`, d=`+0.745`, p=`0.461`, n=`8/4`
- `tube_d_eff_median_iqr`: CPC1 `0.1133` vs CPC5 `0.2556`, d=`-0.713`, p=`0.283`, n=`8/4`
- `persistence_log_eig_var_median_iqr`: CPC1 `0.1755` vs CPC5 `0.3081`, d=`-0.193`, p=`0.214`, n=`8/4`
- `tube_capture_gate_median_iqr`: CPC1 `0.07681` vs CPC5 `0.0643`, d=`+0.146`, p=`0.933`, n=`8/4`

### MAD
- `persistence_kappa_median_mad`: CPC1 `0.0001535` vs CPC5 `0.0003841`, d=`-1.353`, p=`0.0727`, n=`8/4`
- `persistence_log_eig_var_median_mad`: CPC1 `0.07596` vs CPC5 `0.1815`, d=`-1.274`, p=`0.0283`, n=`8/4`
- `tube_d_eff_median_mad`: CPC1 `0.09158` vs CPC5 `0.1932`, d=`-1.046`, p=`0.154`, n=`8/4`
- `tube_a_operator_norm_median_mad`: CPC1 `0.4062` vs CPC5 `0.1828`, d=`+0.778`, p=`0.461`, n=`8/4`
- `tube_capture_gate_median_mad`: CPC1 `0.06287` vs CPC5 `0.05295`, d=`-0.003`, p=`0.933`, n=`8/4`