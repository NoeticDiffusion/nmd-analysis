# TAC 6/8/10 — Between-run IQR and MAD

- cohort: `281` subjects (`141` CPC1, `140` CPC5)
- minimum runs for IQR/MAD: `3`

## Reference: median contrasts (from patient_level_metrics.csv)

- `tac10_9d_within_band_flux_median`: CPC1 `0.5281` vs CPC5 `0.6156`, d = `-0.633`, p = `4.61e-05`, n = `70/60`
- `tac10_9d_cross_band_flux_median`: CPC1 `1.064` vs CPC5 `1.248`, d = `-0.616`, p = `1.2e-05`, n = `70/60`
- `tac6_9d_sigma_velocity_median`: CPC1 `0.4208` vs CPC5 `0.4421`, d = `-0.318`, p = `0.00304`, n = `70/60`
- `tac8_3d_cone_twist_median`: CPC1 `0.09818` vs CPC5 `0.08673`, d = `+0.243`, p = `0.00726`, n = `141/140`
- `tac8_9d_cone_twist_median`: CPC1 `0.203` vs CPC5 `0.1984`, d = `+0.242`, p = `0.248`, n = `70/60`
- `tac10_9d_cross_band_ratio_median`: CPC1 `2.02` vs CPC5 `2.026`, d = `-0.097`, p = `0.344`, n = `70/60`
- `tac6_3d_sigma_velocity_median`: CPC1 `0.1394` vs CPC5 `0.1377`, d = `+0.063`, p = `0.61`, n = `141/140`

## Between-run IQR contrasts

- `tac10_9d_within_band_flux_median_iqr`: CPC1 med `0.04957` vs CPC5 med `0.1057`, d = `-0.850`, p = `6.1e-07`, AUROC = `0.227`, n = `64/50`
- `tac10_9d_cross_band_flux_median_iqr`: CPC1 med `0.09299` vs CPC5 med `0.204`, d = `-0.845`, p = `7.5e-07`, AUROC = `0.229`, n = `64/50`
- `tac6_9d_sigma_velocity_median_iqr`: CPC1 med `0.02194` vs CPC5 med `0.03789`, d = `-0.838`, p = `1.52e-05`, AUROC = `0.263`, n = `64/50`
- `tac8_9d_cone_twist_median_iqr`: CPC1 med `0.02364` vs CPC5 med `0.03272`, d = `-0.611`, p = `0.00127`, AUROC = `0.323`, n = `64/50`
- `tac6_3d_sigma_velocity_median_iqr`: CPC1 med `0.01301` vs CPC5 med `0.01462`, d = `-0.238`, p = `0.0148`, AUROC = `0.415`, n = `140/136`
- `tac10_9d_cross_band_ratio_median_iqr`: CPC1 med `0.05998` vs CPC5 med `0.06379`, d = `-0.091`, p = `0.173`, AUROC = `0.425`, n = `64/50`
- `tac8_3d_cone_twist_median_iqr`: CPC1 med `0.02269` vs CPC5 med `0.02417`, d = `-0.025`, p = `0.433`, AUROC = `0.473`, n = `140/136`

## Between-run MAD contrasts

- `tac10_9d_cross_band_flux_median_mad`: CPC1 med `0.04349` vs CPC5 med `0.09767`, d = `-0.852`, p = `1.26e-06`, AUROC = `0.235`, n = `64/50`
- `tac10_9d_within_band_flux_median_mad`: CPC1 med `0.02332` vs CPC5 med `0.04883`, d = `-0.815`, p = `2.11e-06`, AUROC = `0.240`, n = `64/50`
- `tac6_9d_sigma_velocity_median_mad`: CPC1 med `0.01231` vs CPC5 med `0.01824`, d = `-0.721`, p = `0.000378`, AUROC = `0.305`, n = `64/50`
- `tac8_9d_cone_twist_median_mad`: CPC1 med `0.01339` vs CPC5 med `0.01749`, d = `-0.520`, p = `0.00528`, AUROC = `0.347`, n = `64/50`
- `tac6_3d_sigma_velocity_median_mad`: CPC1 med `0.006279` vs CPC5 med `0.007801`, d = `-0.232`, p = `0.0112`, AUROC = `0.412`, n = `140/136`
- `tac10_9d_cross_band_ratio_median_mad`: CPC1 med `0.03182` vs CPC5 med `0.03419`, d = `+0.024`, p = `0.39`, AUROC = `0.453`, n = `64/50`
- `tac8_3d_cone_twist_median_mad`: CPC1 med `0.01186` vs CPC5 med `0.01198`, d = `-0.010`, p = `0.738`, AUROC = `0.488`, n = `140/136`