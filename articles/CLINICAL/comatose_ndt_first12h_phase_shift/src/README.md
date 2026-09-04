# src/ pipeline: coma first-12h phase-shift detection

Four stages, run in order. Each stage is a standalone script (matching the
numbered-script convention used in `articles/CLINICAL/comatose_ndt/src` and
`articles/RVC_SLEEP/src`) so intermediate outputs can be inspected between
steps. All scripts reuse H5-loading, cohort/QC, dedup, and outcome-contrast
logic from `comatose_ndt/src` and `ndt-analysis` rather than re-deriving it;
see the module docstrings for exactly what is reused from where.

Read `coma_phase_shift_support.py`'s module docstring first - it documents
the `d_n` naming caveat (I-CARE `d_n` = `eeg_gamma`, not the RVC_SLEEP
heat-kernel network-diffusivity `d_n`) that this whole pipeline is built
around.

## Dependencies

`pip install ruptures` (PELT changepoint detection; not otherwise used
anywhere in this repository). Everything else (`h5py`, `pandas`, `numpy`,
`scipy`) is already required by `comatose_ndt/src`.

## Stage 1: extract per-epoch chart series

```
python 01_extract_epoch_series.py --processed-root <part1 H5 root> --cohort-tag part1 --max-hours 12
python 01_extract_epoch_series.py --processed-root <part2 H5 root> --cohort-tag part2 --max-hours 12
```

Writes `results/epoch_series/epoch_series_first12h_<cohort_tag>.parquet`: one
row per (subject, run, epoch) with all nine 9D-chart coordinates plus the
`m`/`d`/`e` composites, clipped to `[0, max_hours)` anchor-relative hours.
Also writes an extraction QC CSV (per-run epoch counts, timing source used).

`--processed-root` defaults to the same auto-discovery
(`resolve_default_processed_root()`) used by `icare_patient_timeline_analysis.py`,
so pointing this at the same part1/part2 roots used for the published
article's `mnps_summary` step is the intended usage.

## Stage 2: detect shifts

```
python 02_detect_shifts.py --epoch-series-path results/epoch_series/epoch_series_first12h_part1.parquet --cohort-tag part1
python 02_detect_shifts.py --epoch-series-path results/epoch_series/epoch_series_first12h_part2.parquet --cohort-tag part2
```

For every (run, coordinate) series: robust-z-score -> PELT (`ruptures`,
default `model=rbf`) -> per-changepoint magnitude (normalized level jump)
and quality (Welch-style, data-support-weighted jump strength; **not** a
native ruptures cost value or a p-value - see
`coma_phase_shift_support.welch_like_quality`) -> run-level summary
(`n_shifts`, `shift_rate_per_hour`, magnitude/quality means and medians,
median segment length).

Writes `results/shift_detection/run_level_shift_features_<cohort_tag>.csv`.

Tunable via `--pelt-model`, `--pelt-penalty-scale`, `--min-epochs`
(defaults documented in `coma_phase_shift_support.py`); penalty choice
materially changes shift counts and is a natural robustness-check axis.

## Stage 3: aggregate to patient level

```
python 03_aggregate_patient_features.py \
  --run-level-path results/shift_detection/run_level_shift_features_part1.csv \
  --run-level-path results/shift_detection/run_level_shift_features_part2.csv \
  --dedup-policy prefer_part2
```

Dedups overlapping (subject, run, acq, coordinate) rows across cohorts using
the same `prefer_part2` convention as
`comatose_ndt/src/merge_coma_cohort_results.py`, then rolls run-level shift
features up to one row per (patient, coordinate), weighting by each run's
analyzed epoch count.

Writes `results/patient_features/patient_coordinate_shift_features.csv`.

## Stage 4: CPC1 vs CPC5 contrast

```
python 04_cpc_contrast.py --patient-features-path results/patient_features/patient_coordinate_shift_features.csv
```

For every (coordinate x shift-feature) cell: Mann-Whitney U + Welch's t-test,
Cohen's d + Cliff's delta (reusing `icare_outcome_contrast_analysis.py`), then
BH-FDR (reusing `classical_comparator_summary.bh_fdr`) across the full
predeclared family - the same statistical convention as the published
`comatose_ndt` article's outcome contrasts.

Writes `results/cpc_contrast/cpc1_vs_cpc5_phase_shift_contrasts.csv` and a
`.md` summary listing any FDR-significant (q < 0.05) cells.

## Known limitations / next robustness checks (not yet implemented)

- PELT penalty selection is a fixed documented constant, not BIC/elbow-tuned;
  sensitivity to this choice has not been checked.
- No figures or hourly-resolved shift-rate maps yet (would mirror
  `comatose_ndt/src/jacobian_hourly_summary.py`).
- Has not yet been run against the real I-CARE part1/part2 H5 exports (only
  smoke-tested against synthetic data during development).
