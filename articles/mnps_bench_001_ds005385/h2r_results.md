# MNPS-BENCH-001R H2 secondary replication

## Question and status

H2R asks whether adding the same four frozen local-Jacobian summaries (MNJ)
to the 4-second fast core improves participant-paired AUC for classifying
Eyes-Closed versus Eyes-Open recordings in the second selected ds005385 cohort.
The unit is the participant; both state recordings stay together in the
participant-grouped CV folds.

This is a post-H1R, same-dataset secondary replication, not a prospective
confirmatory success test. H1R had already used these participants' recording
state labels. The H2-specific 4-second measurements and contrast had not been
analyzed for this cohort before the H2R freeze. Selection ranks 101–200 were
outcome-blind in membership and disjoint from H2's first 100, but the prior
H1R label exposure means the cohort was not untouched.

## Results

| Cohort | Fast-core AUC | Fast core + MNJ AUC | Paired ΔAUC (MNJ − core) | Conditional participant-bootstrap 95% interval |
|---|---:|---:|---:|---:|
| H2, first 100 | 0.92 | 0.93 | +0.01 | [−0.02, +0.05] |
| H2R, second 100 | 0.90 | 0.88 | −0.02 | [−0.08, +0.03] |

Both cohorts had 100 complete participants. The paired interval is a 2,000-draw
participant bootstrap conditional on the fitted repeated-CV predictions. The
estimator uses 5 outer folds repeated 20 times, participant grouping in both
outer and inner splits, 4 inner folds, and the frozen C grid
`{0.01, 0.1, 1, 10, 100}`. These intervals do not include uncertainty from
refitting the full nested-CV procedure in each bootstrap draw.

Across these two participant-disjoint subsets, the point estimates show little
observed incremental recording-state classification gain from adding MNJ to
the fast core under this specific ds005385 analysis. Both intervals include
zero. H2R is compatible with modest harm or a small positive gain; no
equivalence margin was specified. The result does not establish equivalence,
and it is not evidence that MNJ is generally redundant or uninformative.

The recording order is fixed: Eyes Closed precedes Eyes Open. Therefore, the
classification target is the recorded EC-versus-EO state and is confounded
with order/time; this analysis does not isolate a causal eye-closure effect.

## Support and measurement status

H2R retained all 100 participants in both arms. The four core candidates M1,
M2, E1, and E2 were computed, valid, and finite in all 9,249 saved v3.1
four-second windows, but their qualification flags were false. The AUC result
is therefore a computational/experimental benchmark on explicitly
unqualified measurements, not a scientifically qualified or biological
finding.

Every H2R participant passed the frozen technical support criteria for each
core and MNJ feature in both states. The fast-core windows had a minimum of
180 seconds of support. MNJ summaries had at least 33 finite centers in Eyes
Closed and 36 in Eyes Open, above the 30-center minimum; all recording-level
MNJ support checks passed. Median MNJ support was 172 seconds. Unsupported
values were not imputed.

Summarization also logged repeated `mnps_3d.mode=from_v2` fallbacks because
`coords_9d` was unavailable. This was an additional 3D export path; the H2
analysis used the saved M1/M2/E1/E2 measurements and calculated MNJ from those
series. The exact warning count was not persisted.

The unchanged analysis script reports the generic status
`confirmatory_h2_complete` after its complete-case minimum is met. For H2R,
that is a software completion label; it does not override the protocol's
post-H1R secondary-replication designation.

## Reproducibility artifacts

- H2R protocol: `H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\bench_001\mnps_bench_001r_h2_protocol_v1_20261008.md`
- H2R pre-execution freeze: `H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\bench_001\h2r_pre_execution_freeze_v5.json`
- H2R extraction manifest: `H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\bench_001\h2r_execution_manifest.json`
- H2R post-extraction analysis freeze: `H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\bench_001\h2r_analysis_freeze_v1_20261008.json`
- H2R analysis outputs: `I:\AAA_PYTHON_REPOS_BACKUP\homepages\_mnps_bench_001r_h2r_analysis_v1`
- H2R input H5 run: `I:\AAA_PYTHON_REPOS_BACKUP\homepages\_mnps_bench_001r_h2r_fast4s_clean_v1\ds005385\neuralmanifolddynamics_ds005385_20261008_115951`
- Original H2 outputs: `K:\ExternalReceivedDatasets\mnps_bench_001_ds005385\analysis\h2`

The H2 and H2R freezes match on the analysis script and test hashes, H1 CV
dependencies, NMD kernel hashes, analysis contract, and software versions.
