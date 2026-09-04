# Resting-state vs photic reference

- Resting-state baseline comes from `ds004504` with the same diagnostic contrasts (`AD`, `FTD`, `Healthy`).
- The photic stages come from the exact block-native ds006036 export, using original windows whose centers fall inside inferred photic blocks.

## global_mnj_9d

- Resting baseline `AD vs Healthy` `mdr_median`: d=-0.080, p=0.7591, q=0.9086.
- Strongest photic stage: `PHOTO 20 Hz` with d=-0.984, p=0.0005636, q=0.003382.

## global_mnj_3d

- Resting baseline `AD vs Healthy` `mdr_median`: d=0.150, p=0.5487, q=0.9183.
- Strongest photic stage: `PHOTO 15 Hz` with d=-0.611, p=0.01519, q=0.09116.

## Figure-2 note

- The frequency-stress figure uses subject-level `global_mnj_9d` `mdr_median` means with `AD` and `Healthy` traced from resting baseline through `PHOTO 5/10/15/20 Hz`.
