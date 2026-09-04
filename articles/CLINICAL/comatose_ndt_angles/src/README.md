# `src/` - coma turning-angle pipeline

Six stages. Run from this directory (`articles/CLINICAL/comatose_ndt_angles/src`).

## 0. Prerequisite

Stage 1 reads the epoch-series parquet files already produced by the sibling
pipeline. If they don't exist yet, run that pipeline's stage 1 first:

```
cd ../../comatose_ndt_first12h_phase_shift/src
python 01_extract_epoch_series.py --cohort-tag part1 --workers <N>
python 01_extract_epoch_series.py --cohort-tag part2 --workers <N> --processed-root <part2 root>
```

## 1. `coma_angle_support.py`

Not a script - shared helpers (chart/lag definitions, turning-triple math,
step-length filtering, permutation null, entropy/coupling metrics). See its
module docstring for the full scope and the native-3D-equals-composite
equivalence this pipeline relies on.

## 2. `01_compute_turning_angles.py`

```
python 01_compute_turning_angles.py --workers 6
```

Loads and dedups (`prefer_part2`) both cohort parts' epoch series, computes a
pooled 10th-percentile step-length threshold per (chart, lag), then computes
filtered turning-angle summary statistics + a within-run permutation-null
Z-score for every (run, chart, lag) combination. `--limit-groups N` restricts
to the first N (subject, run, acq) groups for a smoke test. `--n-perms`
controls the permutation-null resolution (default 200; this is the dominant
per-group cost - see the timing note below). Output:
`../results/turning_angles/run_level_turning_features.csv`.

Timing note: on this machine (16 cores, shared with other concurrent
workloads), processing all ~3800 runs x 5 charts x 3 lags with 200
permutations each took ~19 minutes with `--workers 6`. Without the
permutation null this drops to roughly a tenth of that; the null is the
dominant cost per (run, chart, lag) cell, not the angle computation itself.

## 3. `02_aggregate_patient_features.py`

```
python 02_aggregate_patient_features.py --run-level-path ../results/turning_angles/run_level_turning_features.csv
```

Rolls run-level features to one row per (patient, chart, lag), weighted by
each run's valid-angle count. Output:
`../results/patient_features/patient_chart_lag_turning_features.csv`.

## 4. `03_cpc_contrast.py`

```
python 03_cpc_contrast.py --patient-features-path ../results/patient_features/patient_chart_lag_turning_features.csv
```

CPC1 vs CPC5 contrast (Mann-Whitney U, Welch's t, Cohen's d, Cliff's delta,
BH-FDR) across all (chart x lag x turning-feature) cells. Output:
`../results/cpc_contrast/cpc1_vs_cpc5_turning_angle_contrasts.csv` +
`..._summary.md`.

## 5. `04_compute_turning_angles_hourly.py`

```
python 04_compute_turning_angles_hourly.py --workers 6
```

Hour-resolved follow-up. Splits each run into 0–1h through 11–12h bins and
computes turning triples within, never across, those boundaries. Reuses the
same full-cohort step-length thresholds as stage 1, so hourly and pooled
metrics remain comparable. Output:
`../results/turning_angles_hourly/run_hour_level_turning_features.csv`.

## 6. `05_aggregate_patient_features_hourly.py`

```
python 05_aggregate_patient_features_hourly.py --run-level-path ../results/turning_angles_hourly/run_hour_level_turning_features.csv
```

Aggregates to `(patient, hour, chart, lag)`, weighted by valid angle count.
Output:
`../results/patient_features_hourly/patient_hour_chart_lag_turning_features.csv`.

## 7. `06_cpc_contrast_hourly.py`

```
python 06_cpc_contrast_hourly.py --patient-features-path ../results/patient_features_hourly/patient_hour_chart_lag_turning_features.csv
```

Tests the preselected `turn_angle_p90`, `turn_angle_iqr`, and
`turn_angle_mad` metrics separately in every hour. BH-FDR is corrected within
each `(chart, lag, feature)` cell over its 12 hours; it is a localization
follow-up, not a discovery-wide correction across all 540 hourly tests.
Outputs are under `../results/cpc_contrast_hourly/`.

## Metrics computed per (run, chart, lag)

See `coma_angle_support.compute_turning_triples` / the summary block in
`01_compute_turning_angles.py::process_run_group` for exact formulas:

- `turn_cos_mean` - mean cos(theta): directional persistence.
- `turn_angle_median`, `turn_angle_mad`, `turn_angle_iqr`, `turn_angle_p90` -
  typical redirection and its spread/tail.
- `turn_fraction_gt_90`, `turn_fraction_gt_120` - frequency of
  orthogonal-or-worse / near-reversal turns.
- `turn_entropy` - Shannon entropy (nats) of the angle histogram (12 bins,
  0-180deg): diversity of turning regimes.
- `turn_length_coupling` - Spearman correlation of angle vs. local step
  length.
- `null_z_median_angle` - Z-score of the observed median angle against a
  200-permutation within-run null that shuffles the temporal order of the
  run's own displacement vectors (plan.md section 7's strong-form test).
