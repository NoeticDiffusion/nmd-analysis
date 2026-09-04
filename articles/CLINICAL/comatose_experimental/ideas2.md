Från implementatören:

`wave1`-piloten är byggd och körd mot part1-bunten.

Koden ligger i `articles/CLINICAL/comatose_experimental/src/run_wave1_geometry_pilots.py`, och huvudresultaten ligger i `articles/CLINICAL/comatose_experimental/results/wave1_geometry_pilots_20260526_part1_cpc15`. Jag skrev också en kort logg i `project/diary/103_20260526_coma_wave1_geometry_pilots.md`.

Körningen använde `141` subjekt (`71` `CPC1`, `70` `CPC5`) och `1668` runs från `0_12h`-kontraktet. Wrappern läser direkt från H5: `coords_9d_subject_anchored/values`, `jacobian_9D/J_hat`, `jacobian_9D/centers` och `time`, med run-/label-information från `comatose_ndt`-timelinen.

Det viktigaste utfallet är att den här första vågen inte främst pekar mot chaos eller burstiness, utan mot `non-normal / transient`-MNJ-signaler. Toppmetrikerna i part1 blev:

- `mnj_reactivity_median`: best-direction `AUROC 0.710`
- `mnj_non_normality_median`: `0.708`
- `mnj_henrici_departure_median`: `0.704`
- `mnj_reactivity_gap_median`: `0.700`
- `lyapunov_positive_sum_per_hour`: `0.698`
- `largest_lyapunov_per_hour`: `0.698`

`mnps_chaos_index_median` var svagare (`~0.594`), och burstiness-måtten låg ungefär runt `0.556-0.558`.

Viktiga filer att titta på är `wave1_summary.md`, `wave1_metric_contrasts.csv`, `subject_wave1_metrics.csv` och `wave1_manifest.json` i resultatmappen.

En viktig caveat är att detta fortfarande är en pilotimplementation: Lyapunov-delen är en linjäriserad diskret approximation, och pseudospektrumspåret är just nu implementerat som billiga `non-normal/transient`-proxies snarare än en full `epsilon`-pseudospektrum-svepning. Om du vill kan jag ta nästa steg och antingen:

Robin: tankar och ideer?