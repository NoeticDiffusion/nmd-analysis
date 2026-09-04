# ESB article summary

## Main ESB-2 result

- Strongest `AD vs Healthy` ESB-2 row: `posterior_capacity_global_guidance` / `photo_5hz` with `d = 0.586`, `p = 0.01297`, `q = 0.02595`.
- Strongest `FTD vs Healthy` ESB-2 row: `posterior_capacity_global_guidance` / `photo_5hz` with `d = 0.784`, `p = 0.00329`, `q = 0.00658`.

## Cross-fitted healthy-template check

- `AD_vs_Healthy` / `photo_15hz` / `esb2_crossfit_hc`: d=0.494, p=0.1729, q=0.1729
- `FTD_vs_Healthy` / `photo_15hz` / `esb2_crossfit_hc`: d=0.709, p=0.02136, q=0.02136

## PRL

- Strongest `AD vs Healthy` PRL row: `posterior_capacity_global_guidance` with `d = -0.592`, `p = 0.01082`, `q = 0.02165`.

## Axis decomposition

- `delta_capacity_rest` / `photo_15hz`: d=-0.872, p=0.0007276, q=0.0007276
- `delta_capacity_rest` / `photo_10hz`: d=-0.870, p=0.0007754, q=0.0007754
- `delta_guidance_rest` / `photo_10hz`: d=0.482, p=0.1152, q=0.1152
- `delta_capacity_rest` / `photo_5hz`: d=-0.079, p=0.3067, q=0.3067

## Comparison to MNJ reference

- `ESB2` / `photo_5hz` / `esb2_ds004504`: d=0.586, p=0.01297, q=0.02595
- `MNJ_reference` / `photo_10hz` / `mdr_median`: d=-1.082, p=0.0008172, q=0.004903

## Specification sensitivity

- `AD_vs_Healthy` / `posterior_capacity_global_guidance` at `photo_15hz`: d=0.603, q=0.118
- `AD_vs_Healthy` / `posterior_capacity_frontal_guidance` at `photo_15hz`: d=0.316, q=0.3343
- `AD_vs_Healthy` / `global_capacity_global_guidance` at `photo_15hz`: d=nan, q=nan
- `FTD_vs_Healthy` / `posterior_capacity_global_guidance` at `photo_15hz`: d=0.867, q=0.01372
- `FTD_vs_Healthy` / `posterior_capacity_frontal_guidance` at `photo_15hz`: d=0.048, q=0.8802
- `FTD_vs_Healthy` / `global_capacity_global_guidance` at `photo_15hz`: d=nan, q=nan

## Dataset comparability

- Matched ds004504 baselines were available for `88` / `88` photic subjects.
- Group totals on the matched surface were `Healthy=29`, `AD=36`, `FTD=23`.
- Primary-stage analyzable counts were `Healthy=27`, `AD=35`, `FTD=22`.

## Negative findings

- `ESB2` / `AD_vs_FTD`: corrected rows=0, best scope=`photo_5hz`, best d=0.496, best q=0.1608
- `PRL` / `AD_vs_Healthy`: corrected rows=1, best scope=`profile_all`, best d=-0.592, best q=0.02165
- `PRL` / `FTD_vs_Healthy`: corrected rows=1, best scope=`profile_all`, best d=-0.961, best q=0.002744
- `PRL` / `AD_vs_FTD`: corrected rows=0, best scope=`profile_all`, best d=0.365, best q=0.7446

## Frequency audit for primary ESB-2 spec

- `AD_vs_Healthy` / `photo_5hz`: d=0.586, p=0.01297, frequency-wise q=0.05189
- `AD_vs_Healthy` / `photo_10hz`: d=0.401, p=0.1256, frequency-wise q=0.1674
- `AD_vs_Healthy` / `photo_15hz`: d=0.603, p=0.05899, frequency-wise q=0.118
- `AD_vs_Healthy` / `photo_20hz`: d=0.207, p=0.2326, frequency-wise q=0.2326
- `FTD_vs_Healthy` / `photo_5hz`: d=0.784, p=0.00329, frequency-wise q=0.01316
- `FTD_vs_Healthy` / `photo_10hz`: d=0.585, p=0.03964, frequency-wise q=0.05285
- `FTD_vs_Healthy` / `photo_15hz`: d=0.867, p=0.00686, frequency-wise q=0.01372
- `FTD_vs_Healthy` / `photo_20hz`: d=-0.116, p=0.6372, frequency-wise q=0.6372
