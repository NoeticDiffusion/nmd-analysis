# Between-run IQR and MAD — 5 NDT article metrics

- cohort: `130` subjects (`70` CPC1, `60` CPC5)
- time bin: `0_12h`
- minimum runs for IQR/MAD: `3`
- metrics: `persistence_log_det_median`, `persistence_hysteresis_log_det_median`, `tube_d_eff_median`, `tube_capture_gate_median`, `persistence_log_eig_var_median`

## What is being measured

Between-run IQR and MAD capture **within-patient temporal variability** across the multiple
recording runs in the 0-12 h window. This is distinct from within-run spread (IQR/MAD of
Jacobian eigenvalues within a single recording computed by `reachability_cones.py`).

High between-run IQR/MAD = the geometry metric fluctuates substantially across the patient's
recordings — potentially reflecting attractor instability or non-stationarity.

## Reference: median contrasts (from primary analysis)

- `persistence_hysteresis_log_det_median`: CPC1 `2.351` vs CPC5 `3.631`, d = `-0.921`, p = `7.74e-08`
- `persistence_log_det_median`: CPC1 `1.364` vs CPC5 `0.8215`, d = `+0.897`, p = `2.21e-06`
- `tube_d_eff_median`: CPC1 `3.067` vs CPC5 `2.46`, d = `+0.858`, p = `5.7e-06`
- `persistence_log_eig_var_median`: CPC1 `1.674` vs CPC5 `0.9727`, d = `+0.739`, p = `4.43e-05`
- `tube_capture_gate_median`: CPC1 `1.796` vs CPC5 `1.885`, d = `-0.484`, p = `0.0424`

## Between-run IQR contrasts

- `tube_capture_gate_median_iqr`: CPC1 med `0.1806` vs CPC5 med `0.2906`, Cohen's d = `-0.991`, MW p = `3.69e-06`, AUROC = `0.247`, n = `64/50`
- `persistence_hysteresis_log_det_median_iqr`: CPC1 med `0.4605` vs CPC5 med `1.078`, Cohen's d = `-0.643`, MW p = `8.44e-05`, AUROC = `0.285`, n = `64/50`
- `persistence_log_det_median_iqr`: CPC1 med `0.3279` vs CPC5 med `0.2763`, Cohen's d = `+0.229`, MW p = `0.105`, AUROC = `0.589`, n = `64/50`
- `tube_d_eff_median_iqr`: CPC1 med `0.3089` vs CPC5 med `0.3728`, Cohen's d = `-0.213`, MW p = `0.229`, AUROC = `0.434`, n = `64/50`
- `persistence_log_eig_var_median_iqr`: CPC1 med `0.3525` vs CPC5 med `0.3323`, Cohen's d = `+0.072`, MW p = `0.403`, AUROC = `0.546`, n = `64/50`

## Between-run MAD contrasts

- `tube_capture_gate_median_mad`: CPC1 med `0.0896` vs CPC5 med `0.1535`, Cohen's d = `-1.033`, MW p = `3.79e-06`, AUROC = `0.247`, n = `64/50`
- `persistence_hysteresis_log_det_median_mad`: CPC1 med `0.2224` vs CPC5 med `0.4957`, Cohen's d = `-0.687`, MW p = `1.92e-05`, AUROC = `0.266`, n = `64/50`
- `tube_d_eff_median_mad`: CPC1 med `0.1538` vs CPC5 med `0.203`, Cohen's d = `-0.242`, MW p = `0.194`, AUROC = `0.429`, n = `64/50`
- `persistence_log_det_median_mad`: CPC1 med `0.1547` vs CPC5 med `0.1283`, Cohen's d = `+0.234`, MW p = `0.102`, AUROC = `0.590`, n = `64/50`
- `persistence_log_eig_var_median_mad`: CPC1 med `0.1805` vs CPC5 med `0.1629`, Cohen's d = `+0.030`, MW p = `0.368`, AUROC = `0.549`, n = `64/50`

## Notes

- Between-run IQR and MAD require at least `--min-runs` finite values per patient.
  Subjects with fewer qualifying runs contribute NaN.
- The within-run IQR/MAD computed by `reachability_cones.py` per EEG window is
  currently not exported to the signal-metric CSVs — only the within-run median is.
- Between-run variability is a different construct from the central-tendency median.
  A significant between-run IQR contrast would suggest CPC groups differ not just in
  typical geometry level but in how stably that geometry is maintained across recordings.