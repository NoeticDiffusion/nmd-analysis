# ESB article summary

## Main ESB-2 result

- Strongest `AD vs Healthy` ESB-2 row: `posterior_capacity_global_guidance` / `photo_15hz` with `d = 0.821`, `p = 0.003128`, `q = 0.006256`.
- Strongest `FTD vs Healthy` ESB-2 row: `posterior_capacity_global_guidance` / `photo_15hz` with `d = 1.038`, `p = 0.001346`, `q = 0.002691`.

## Cross-fitted healthy-template check

- `AD_vs_Healthy` / `photo_15hz` / `esb2_crossfit_hc`: d=0.676, p=0.01277, q=0.01277
- `FTD_vs_Healthy` / `photo_15hz` / `esb2_crossfit_hc`: d=0.841, p=0.007287, q=0.007287

## PRL

- Strongest `AD vs Healthy` PRL row: `posterior_capacity_frontal_guidance` with `d = -0.388`, `p = 0.1348`, `q = 0.2695`.

## Axis decomposition

- `delta_capacity_rest` / `photo_10hz`: d=-0.652, p=0.007071, q=0.007071
- `delta_capacity_rest` / `photo_15hz`: d=-0.631, p=0.01176, q=0.01176
- `delta_capacity_rest` / `photo_5hz`: d=-0.438, p=0.02907, q=0.02907
- `delta_guidance_rest` / `photo_15hz`: d=0.456, p=0.2253, q=0.4507

## Comparison to MNJ reference

- `ESB2` / `photo_15hz` / `esb2_ds004504`: d=0.821, p=0.003128, q=0.006256
- `MNJ_reference` / `photo_20hz` / `mdr_median`: d=-0.984, p=0.0005636, q=0.003382

## Specification sensitivity

- `AD_vs_Healthy` / `posterior_capacity_global_guidance` at `photo_15hz`: d=0.821, q=0.006256
- `AD_vs_Healthy` / `posterior_capacity_frontal_guidance` at `photo_15hz`: d=0.557, q=0.02487
- `AD_vs_Healthy` / `global_capacity_global_guidance` at `photo_15hz`: d=nan, q=nan
- `FTD_vs_Healthy` / `posterior_capacity_global_guidance` at `photo_15hz`: d=1.038, q=0.002691
- `FTD_vs_Healthy` / `posterior_capacity_frontal_guidance` at `photo_15hz`: d=0.138, q=0.8328
- `FTD_vs_Healthy` / `global_capacity_global_guidance` at `photo_15hz`: d=nan, q=nan

## Dataset comparability

- Matched ds004504 baselines were available for `86` / `86` photic subjects.
- Group totals on the matched surface were `Healthy=27`, `AD=36`, `FTD=23`.
- Primary-stage analyzable counts were `Healthy=27`, `AD=34`, `FTD=22`.

## Negative findings

- `ESB2` / `AD_vs_FTD`: corrected rows=0, best scope=`photo_15hz`, best d=0.356, best q=0.3126
- `PRL` / `AD_vs_Healthy`: corrected rows=0, best scope=`profile_all`, best d=-0.388, best q=0.2695
- `PRL` / `FTD_vs_Healthy`: corrected rows=0, best scope=`profile_all`, best d=-0.372, best q=0.3649
- `PRL` / `AD_vs_FTD`: corrected rows=0, best scope=`profile_all`, best d=0.193, best q=0.6694

## Frequency audit for primary ESB-2 spec

- `AD_vs_Healthy` / `photo_5hz`: d=0.472, p=0.04614, frequency-wise q=0.06153
- `AD_vs_Healthy` / `photo_10hz`: d=0.493, p=0.04432, frequency-wise q=0.06153
- `AD_vs_Healthy` / `photo_15hz`: d=0.821, p=0.003128, frequency-wise q=0.01251
- `AD_vs_Healthy` / `photo_20hz`: d=0.069, p=0.5722, frequency-wise q=0.5722
- `FTD_vs_Healthy` / `photo_5hz`: d=0.692, p=0.02071, frequency-wise q=0.02761
- `FTD_vs_Healthy` / `photo_10hz`: d=0.760, p=0.0138, frequency-wise q=0.02761
- `FTD_vs_Healthy` / `photo_15hz`: d=1.038, p=0.001346, frequency-wise q=0.005382
- `FTD_vs_Healthy` / `photo_20hz`: d=-0.086, p=0.8489, frequency-wise q=0.8489
