# ESB QC summary

## Leave-one-out healthy template sensitivity

### ESB-2

- `AD_vs_Healthy` effect-size range under leave-one-out: median=0.603, min=0.544, max=0.611
- `FTD_vs_Healthy` effect-size range under leave-one-out: median=0.824, min=0.709, max=0.911

### PRL

- `AD_vs_Healthy` effect-size range under leave-one-out: median=-0.566, min=-0.644, max=-0.407
- `FTD_vs_Healthy` effect-size range under leave-one-out: median=-0.918, min=-1.019, max=-0.744

## Permutation tests

- `esb2_ds004504` / `AD_vs_Healthy` / `photo_15hz`: observed d=0.603, empirical p=0.0195
- `esb2_ds004504` / `FTD_vs_Healthy` / `photo_15hz`: observed d=0.867, empirical p=0.0025
- `prl_score` / `AD_vs_Healthy` / `profile_all`: observed d=-0.592, empirical p=0.0265
- `prl_score` / `FTD_vs_Healthy` / `profile_all`: observed d=-0.961, empirical p=0.0025

## Recovery-coverage subset stability

- `all_subjects` / `AD_vs_Healthy`: d=0.603, p=0.05899, n=(35,27)
- `all_subjects` / `FTD_vs_Healthy`: d=0.867, p=0.00686, n=(22,27)
- `recovery_eye2_only` / `AD_vs_Healthy`: d=0.251, p=0.5029, n=(24,27)
- `recovery_eye2_only` / `FTD_vs_Healthy`: d=0.530, p=0.1856, n=(12,27)

## Cross-fitted healthy-template contrasts

- `AD_vs_FTD` / `photo_15hz`: d=-0.066, p=0.4657, q=0.4657, n=(35,22)
- `AD_vs_Healthy` / `photo_15hz`: d=0.494, p=0.1729, q=0.1729, n=(35,27)
- `FTD_vs_Healthy` / `photo_15hz`: d=0.709, p=0.02136, q=0.02136, n=(22,27)
