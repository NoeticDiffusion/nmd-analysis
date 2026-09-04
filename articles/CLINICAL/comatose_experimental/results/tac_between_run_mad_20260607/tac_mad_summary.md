# TAC 6/8/10 — Between-run IQR and MAD

- cohort: `281` subjects (`141` CPC1, `140` CPC5)
- minimum runs for IQR/MAD: `3`

## Reference: median contrasts (from patient_level_metrics.csv)

- `tac10_9d_within_band_flux_median`: CPC1 `0.5255` vs CPC5 `0.5978`, d = `-0.657`, p = `1.53e-05`, n = `95/91`
- `tac10_9d_cross_band_flux_median`: CPC1 `1.049` vs CPC5 `1.191`, d = `-0.642`, p = `1.96e-05`, n = `95/91`
- `tac6_9d_sigma_velocity_median`: CPC1 `0.3943` vs CPC5 `0.4037`, d = `-0.268`, p = `0.0374`, n = `141/140`
- `tac8_3d_cone_twist_median`: CPC1 `0.09818` vs CPC5 `0.08673`, d = `+0.243`, p = `0.00726`, n = `141/140`
- `tac8_9d_cone_twist_median`: CPC1 `0.2002` vs CPC5 `0.195`, d = `+0.104`, p = `0.187`, n = `141/140`
- `tac6_3d_sigma_velocity_median`: CPC1 `0.1394` vs CPC5 `0.1377`, d = `+0.063`, p = `0.61`, n = `141/140`
- `tac10_9d_cross_band_ratio_median`: CPC1 `2.018` vs CPC5 `2.023`, d = `-0.047`, p = `0.408`, n = `95/91`

## Between-run IQR contrasts

- `tac10_9d_cross_band_flux_median_iqr`: CPC1 med `0.1038` vs CPC5 med `0.2315`, d = `-0.795`, p = `9.32e-07`, AUROC = `0.265`, n = `76/71`
- `tac10_9d_within_band_flux_median_iqr`: CPC1 med `0.0544` vs CPC5 med `0.12`, d = `-0.733`, p = `1.88e-06`, AUROC = `0.272`, n = `76/71`
- `tac6_9d_sigma_velocity_median_iqr`: CPC1 med `0.0253` vs CPC5 med `0.03568`, d = `-0.301`, p = `0.000629`, AUROC = `0.381`, n = `140/136`
- `tac6_3d_sigma_velocity_median_iqr`: CPC1 med `0.01301` vs CPC5 med `0.01462`, d = `-0.238`, p = `0.0148`, AUROC = `0.415`, n = `140/136`
- `tac8_9d_cone_twist_median_iqr`: CPC1 med `0.02632` vs CPC5 med `0.03387`, d = `-0.141`, p = `0.00154`, AUROC = `0.390`, n = `140/136`
- `tac10_9d_cross_band_ratio_median_iqr`: CPC1 med `0.06231` vs CPC5 med `0.0868`, d = `-0.091`, p = `0.0461`, AUROC = `0.405`, n = `76/71`
- `tac8_3d_cone_twist_median_iqr`: CPC1 med `0.02269` vs CPC5 med `0.02417`, d = `-0.025`, p = `0.433`, AUROC = `0.473`, n = `140/136`

## Between-run MAD contrasts

- `tac10_9d_cross_band_flux_median_mad`: CPC1 med `0.0491` vs CPC5 med `0.1258`, d = `-0.805`, p = `5.66e-07`, AUROC = `0.261`, n = `76/71`
- `tac10_9d_within_band_flux_median_mad`: CPC1 med `0.02674` vs CPC5 med `0.06449`, d = `-0.642`, p = `3.39e-05`, AUROC = `0.302`, n = `76/71`
- `tac6_9d_sigma_velocity_median_mad`: CPC1 med `0.01341` vs CPC5 med `0.01621`, d = `-0.302`, p = `0.00357`, AUROC = `0.399`, n = `140/136`
- `tac6_3d_sigma_velocity_median_mad`: CPC1 med `0.006279` vs CPC5 med `0.007801`, d = `-0.232`, p = `0.0112`, AUROC = `0.412`, n = `140/136`
- `tac8_9d_cone_twist_median_mad`: CPC1 med `0.01451` vs CPC5 med `0.01696`, d = `-0.094`, p = `0.0366`, AUROC = `0.427`, n = `140/136`
- `tac10_9d_cross_band_ratio_median_mad`: CPC1 med `0.03494` vs CPC5 med `0.04459`, d = `-0.068`, p = `0.0492`, AUROC = `0.406`, n = `76/71`
- `tac8_3d_cone_twist_median_mad`: CPC1 med `0.01186` vs CPC5 med `0.01198`, d = `-0.010`, p = `0.738`, AUROC = `0.488`, n = `140/136`