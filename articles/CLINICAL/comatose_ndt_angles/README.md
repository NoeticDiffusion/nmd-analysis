# Coma turning-angle geometry pipeline

## Status

Pipeline-only. No manuscript has been written yet - `manuscript.typ`, `S1`-`S6`
etc. are still the generic `aa_template` placeholders. This folder currently
holds `plan.md` (the original design note - not edited by this pipeline) plus
a working analysis pipeline in `src/` and its results in `results/`. See
`project/diary/` for the working session that produced it.

## Hypothesis

`plan.md` was written for the first-episode-psychosis resting-state EEG
cohorts (ds003944/ds003947), proposing that three-point MNPS turning angles -
the angle between the incoming and outgoing displacement vector at each
trajectory point, in 3D, 9D, and per-family 3D subspaces - might separate
groups by directional persistence vs. abrupt redirection, and that the upper
tail (large/frequent turns) might be more informative than the mean.

This pipeline asks the same geometric question on a different cohort and a
different outcome axis: does turning-angle magnitude, spread, diversity, or
null-normalized persistence during the first 12h post-arrest separate CPC1
(good outcome) from CPC5 (poor outcome) in the I-CARE cardiac-arrest coma
cohort?

## Reuse: no new H5 extraction

This pipeline does **not** re-extract H5 data. It reuses the per-epoch 9D +
composite (`m`,`d`,`e`) chart series already extracted, for the first 12h
post-arrest under the `subject_anchored` coordinate contract, by the sibling
`comatose_ndt_first12h_phase_shift` pipeline's `01_extract_epoch_series.py`
(`../comatose_ndt_first12h_phase_shift/results/epoch_series/epoch_series_first12h_part{1,2}.parquet`).

This is a valid substitution, not an approximation of convenience: the `m`,
`d`, `e` composite columns in that parquet use the *exact* fixed weights
documented as the native `mnps_3d` recomposition in
`articles/CLINICAL/comatose_ndt/S1_Supplementary_methods.typ`:

```
m_t = 0.62 m_a + 0.55 m_e + 0.45 m_o
d_t = 0.50 d_n + 0.82 d_l + 0.28 d_s
e_t = 0.85 e_e + 0.62 e_s + 0.03 e_m
```

So treating those three columns as the "native 3D chart" (plan.md's primary
analysis) is the same chart already used elsewhere in the `comatose_ndt`
article family, not a pipeline-specific stand-in.

## Scope of this implementation pass

Implemented, per plan.md's recommended analysis hierarchy:

1. Native 3D turning (`m`, `d`, `e`) - primary.
2. Native 9D turning (all nine chart axes) - secondary.
3. Family-specific 3D turning: `m_*=[m_a,m_e,m_o]`, `d_*=[d_n,d_l,d_s]`,
   `e_*=[e_e,e_s,e_m]`.
4. Lag sensitivity, ell in {1, 2, 4} epochs (~4s/8s/16s at the fixed 4s MNPS
   step).
5. Step-length filtering (pooled 10th-percentile exclusion).
6. Within-run displacement-permutation null -> per-run Z-score.
7. CPC1-vs-CPC5 contrast (replacing plan.md's medication-stratified
   contrast, since coma has no medication axis), with BH-FDR across the
   full predeclared (chart x lag x metric) cell family.

**Not implemented** in this pass: the metric-adjusted (shrinkage-covariance)
9D angle from plan.md section 3. plan.md itself labels that layer "robustness
only"; it remains a documented follow-up.

See `src/coma_angle_support.py` for the exact metric definitions and
`src/README.md` for how to run the three pipeline stages.

## Result summary (first full run)

CPC1 (n~134-141) vs CPC5 (n~136-140), 301 total patients with turning-angle
features, 150 predeclared (chart x lag x turning-feature) contrast cells:

- **36 of 150 cells FDR-significant (q<0.05)**, dominated by the upper-tail /
  spread metrics: `turn_angle_p90`, `turn_angle_iqr`, `turn_angle_mad`.
- The effect is **broadly replicated**: it appears across all five charts
  (native 3D, native 9D, and all three family subspaces `m3`/`d3`/`e3`) and
  across all three lags, satisfying plan.md's own replication bar
  ("A genuine group effect should ideally preserve its direction over at
  least two lags").
- **Direction**: CPC1 (good outcome) has *lower* p90/IQR/MAD turning angle
  than CPC5 (poor outcome) in every significant cell (all `cohens_d`,
  `cliffs_delta` negative under the good-minus-poor convention). I.e. poor-
  outcome trajectories redirect more abruptly / have a heavier tail of large
  turns in the first 12h - the same qualitative direction plan.md predicted
  for FEP-psychosis vs. healthy.
- Effect sizes are small-to-moderate: `|cohens_d|` up to ~0.56 (best cell:
  `e3__lag1__turn_angle_p90`), most FDR-significant cells in the 0.2-0.4
  range.
- **Important caveat - null-normalized persistence does *not* replicate**:
  none of the `null_z_median_angle` cells (the permutation-null Z-score from
  plan.md section 7, i.e. "is this trajectory more organized than its own
  displacement repertoire would produce under random re-ordering") reach
  significance (all uncorrected p>0.12). This means the raw turning-angle
  tail difference is not yet shown to reflect *excess* redirection beyond
  what the patient's own step-length/amplitude repertoire would produce -
  it could instead (or additionally) reflect a difference in the amplitude/
  step-length distribution itself. plan.md explicitly distinguishes these as
  the weak-form (`theta_FEP > theta_Healthy`) vs. strong-form
  (`Z_theta,FEP > Z_theta,Healthy`) hypotheses; only the weak form is
  supported so far.

Full outputs: `results/cpc_contrast/cpc1_vs_cpc5_turning_angle_contrasts.csv`
and `results/cpc_contrast/cpc1_vs_cpc5_turning_angle_summary.md`.

## Hour-resolved localization follow-up

The pooled analysis can hide a temporally localized outcome difference, so the
same tail/spread metrics were re-estimated independently within each hour
(`0_1h` through `11_12h`). Turning triples never cross an hourly boundary.
To retain comparability with the pooled analysis, the step-length exclusions
use the same globally pooled per-(chart, lag) 10th-percentile thresholds; they
are not re-estimated per hour.

This was a deliberately constrained follow-up: 45 predeclared cells
(5 charts x 3 lags x `turn_angle_p90`/`turn_angle_iqr`/`turn_angle_mad`),
each with 12 hourly tests. BH-FDR is applied *within each cell across its 12
hours*, not across all 540 hourly contrasts. Therefore it supports
localization of the already-established pooled effect; it does **not** create
a new discovery-wide significance claim.

- **29/45 cells** have at least one within-cell FDR-significant hour, and
  **42/45** have a strongest hourly `|d|` larger than their pooled-12h
  estimate.
- The largest localized effect is
  `e3__lag4__turn_angle_p90` at **3–4h**: `d=-0.555`, `p=1.62e-05`,
  within-cell `q=0.000194`, versus pooled `d=-0.382`.
- Other strong instances include `9d__lag2__turn_angle_mad` at 2–3h
  (`d=-0.512`) and native `3d__lag4__turn_angle_p90` at 3–4h
  (`d=-0.511`).
- This is **not a single sharp critical hour**: many cells remain
  significant in 7–12 of the 12 bins. The hourly split modestly strengthens
  several effects, but most signal is temporally broad rather than confined
  to one transient episode.

Hourly outputs: `results/turning_angles_hourly/`,
`results/patient_features_hourly/`, and
`results/cpc_contrast_hourly/cpc1_vs_cpc5_turning_angle_hourly_contrasts.csv`
plus its CSV/Markdown localization summaries.

## Research-discipline status of this branch

Per the repository's role/discipline conventions:

- **Established mathematical result**: three-point turning angles are
  well-defined in 3D and 9D (plan.md section 1).
- **Internal validated result**: 36/150 predeclared cells FDR-significant,
  replicated across chart and lag, for the turning-angle tail/spread metrics
  specifically - this is a real, reproducible pattern in this pipeline's
  output on the real I-CARE part1+part2 data. The constrained hourly
  follow-up further shows that this pattern is present across many individual
  hours and reaches `|d|≈0.56` in its strongest hour.
- **Plausible interpretation**: poor-outcome (CPC5) coma patients show a
  heavier tail of abrupt trajectory redirection in the first 12h than
  good-outcome (CPC1) patients; the difference is not confined to a unique
  early or late critical hour.
- **Speculative extension**: this may reflect reduced dynamical
  organization/stability of the underlying neural state, analogous to the
  disorganized-flow hypothesis plan.md proposed for psychosis - not yet
  supported by the null-normalized (strong-form) test.
- **Not (yet) supported / open**: that the effect reflects *excess*
  redirection beyond the patient's own displacement repertoire (the
  permutation-null Z-score contrast is null). Also open: the
  metric-adjusted 9D angle (deferred), a global correction across all hourly
  tests, and out-of-sample replication.
