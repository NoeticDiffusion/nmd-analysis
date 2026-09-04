# ESB QC summary

## Leave-one-out healthy template sensitivity

### ESB-2

- `AD_vs_Healthy` effect-size range under leave-one-out: median=0.818, min=0.793, max=0.843
- `FTD_vs_Healthy` effect-size range under leave-one-out: median=1.013, min=0.925, max=1.091

### PRL

- `AD_vs_Healthy` effect-size range under leave-one-out: median=-0.295, min=-0.513, max=0.028
- `FTD_vs_Healthy` effect-size range under leave-one-out: median=-0.435, min=-0.568, max=-0.170

## Permutation tests

- `esb2_ds004504` / `AD_vs_Healthy` / `photo_15hz`: observed d=0.821, empirical p=0.0015
- `esb2_ds004504` / `FTD_vs_Healthy` / `photo_15hz`: observed d=1.038, empirical p=0
- `prl_score` / `AD_vs_Healthy` / `profile_all`: observed d=-0.198, empirical p=0.4485
- `prl_score` / `FTD_vs_Healthy` / `profile_all`: observed d=-0.372, empirical p=0.201

## Recovery-coverage subset stability

- `all_subjects` / `AD_vs_Healthy`: d=0.821, p=0.003128, n=(34,27)
- `all_subjects` / `FTD_vs_Healthy`: d=1.038, p=0.001346, n=(22,27)
- `recovery_eye2_only` / `AD_vs_Healthy`: d=0.561, p=0.0765, n=(23,27)
- `recovery_eye2_only` / `FTD_vs_Healthy`: d=0.652, p=0.1101, n=(12,27)

## Cross-fitted healthy-template contrasts

- `AD_vs_FTD` / `photo_15hz`: d=-0.027, p=0.6688, q=0.6688, n=(34,22)
- `AD_vs_Healthy` / `photo_15hz`: d=0.676, p=0.01277, q=0.01277, n=(34,27)
- `FTD_vs_Healthy` / `photo_15hz`: d=0.841, p=0.007287, q=0.007287, n=(22,27)
