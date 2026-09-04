# First-episode psychosis turning-angle analysis

## Status

Pipeline-only. The manuscript and supplements remain templates; this folder
contains an exploratory reanalysis of the trajectories used by
`psychosis_first_time_episode`, not an amendment to that source article.

## Question and inherited design

The source article, `First-Episode Psychosis Geometry Across Two Resting-State
EEG Cohorts.typ`, reports medication-stratified geometry in ds003944 and
ds003947, but it does not treat the distribution of explicit three-point
turning angles as an endpoint. This pipeline tests the original exploratory
hypothesis: FEP may show less directionally persistent, more abruptly
redirecting MNPS trajectories than Healthy participants.

It preserves the source article's design:

- ds003944 and ds003947 are analyzed separately;
- the primary contrasts are unmedicated FEP vs Healthy, medicated FEP vs
  Healthy, and medicated vs unmedicated FEP;
- Healthy vs pooled FEP is sensitivity-only;
- cohort-anchored trajectories are primary because that is the source
  article's shared-reference between-subject contract; subject-anchored
  trajectories are a labelled contract sensitivity;
- ds003947 unmedicated FEP has n=8 and all contrasts involving that group
  carry an explicit small-group warning.

## Method

For each subject, the pipeline loads serialized native 3D and 9D MNPS
coordinates from the NMD 2.1 H5 export, and derives the `m3`, `d3`, and `e3`
9D-family subspaces. It computes turning metrics at lags 1, 2, and 4:
mean cosine, median/MAD/IQR/p90 angle, fractions beyond 90/120 degrees,
entropy, angle-step-length coupling, and a within-subject shuffled-increment
null Z-score. Triples with either adjacent step below the dataset-specific,
pooled 10th-percentile threshold are excluded. Time gaps split trajectories;
no angle crosses a discontinuity.

`src/01_compute_psychosis_turning_angles.py` produces subject tables;
`02_psychosis_angle_contrasts.py` runs the group statistics; and
`03_psychosis_angle_robustness.py` evaluates lag and coordinate-contract
sensitivity. Full output is under `results/psychosis_angles_20260719/`.

## Full-run result

The primary cohort-anchored analysis used the expected available samples:

| Dataset | Healthy | FEP unmedicated | FEP medicated |
|---|---:|---:|---:|
| ds003944 | 32 | 19 | 31 |
| ds003947 | 30 | 8 | 23 |

No primary medication-stratified contrast survived BH-FDR:

- **0/450** full-family cells were significant (150 metrics × 3 contrasts)
  in either dataset.
- **0/135** preselected tail/spread cells (`p90`, IQR, MAD) survived their
  targeted BH-FDR family in either dataset.
- Consequently, no tail/spread cell met the plan's dynamic-coherence
  requirement: targeted significance at two or more lags with consistent
  direction.

There are moderate-to-large *uncorrected* effects, but they are neither
FDR-supported nor cross-cohort replicated. Examples include ds003944
medicated FEP vs Healthy on native-3D lag-4 p90 (`d=+0.739`, `p=0.00662`,
full-family `q=0.958`) and ds003947 medicated FEP vs Healthy on `m3`, lag-1
p90 (`d=+0.632`, `p=0.00856`, full-family `q=0.477`). The headline
ds003947 unmedicated-vs-Healthy direction is especially non-interpretable:
its strongest raw cell is null-Z in `m3` at lag 1 (`d=-0.927`, `p=0.0282`),
but n=8 and full-family `q=1.0`.

The subject-anchored sensitivity was also run. It does not rescue a
cohort-anchored, lag-coherent targeted effect.

## Claim status

- **Established:** turning angles are valid Euclidean trajectory descriptors
  in 3D and 9D.
- **Internal result:** this implementation ran successfully on the source
  cohorts and produced the predeclared primary and sensitivity tables.
- **Falsified under this specification:** the proposed angle-distribution
  signature does not survive the source article's medication-stratified,
  per-dataset multiple-testing correction.
- **Not supported:** a cross-cohort FEP turning-angle biomarker, a
  medication-independent angle effect, or an excess-redirection claim based
  on the null-Z statistic.
- **Open:** a more focused, externally motivated endpoint or an
  out-of-sample design could be tested later, but selecting it from these raw
  p-values would be post hoc and should not be represented as confirmation.
