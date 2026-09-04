# Results provenance

`appleseed_sftc_20260807/` is the first (and, as of this writing, only) test
run, produced by:

```
python src/01_compute_family_coupling.py
python src/02_family_coupling_age_contrast.py
```

against `data/raw/neuralmanifolddynamics_ds003710_20260804_153346` (same
export used by the parent `APPLESEED_infants` article's
`appleseed_cohort_20260805` run).

- `01_family_coupling/` - per-session Stratified Family Temporal Coupling
  (SFTC) endpoints: `family_coupling_long.csv` (long format, one row per
  session x receiver family x driver family x lag), `family_coupling_wide.csv`
  (one row per session, 27 endpoint columns), `family_coupling_qc.csv`,
  `export_manifest.json`.
- `02_age_contrast/` - reliability (4m test-retest ICC) and balanced paired
  age contrasts (4m-to-8m, 4m-to-12m) on the 27 SFTC endpoints, using the same
  statistical design as the parent article's `02_reliability_longitudinal.py`.

This is a first exploratory test run, not a manuscript result. See
`articles/aaa_ideas/ideas_trajectory_repertoire_status_and_infant_eeg.md`
section 4 for the full write-up and claim-discipline status (no BH-FDR
hits at n=11-13 subjects; a lag-1 autocorrelation confound caveat).
