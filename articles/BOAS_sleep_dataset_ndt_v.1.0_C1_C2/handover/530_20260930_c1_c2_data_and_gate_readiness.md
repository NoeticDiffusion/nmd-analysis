# 530 — 2026-09-30 — ds005555 C1/C2 data and gate readiness

## Summary

The C1/C2 article branch is being prepared as a prospective, exploratory reanalysis. No dataset was copied or moved. C1 can use the existing fold-safe chart HDF5 files by path; C2 remains unqualified because the chart files do not contain a qualified accessibility/future-law predictor. No future target values, scores or effects were opened in this readiness check.

## Data inventory

- Canonical raw BIDS source: `K:\ExternalReceivedDatasets\openneuro\received\ds005555`. It contains 355 EDF files and 256 event TSV files (39,320,483,371 bytes in total). The prior replay validation binds this source and its current per-file hashes. It remains in place and may be read as an input; it is not copied into the repository.
- The existing `J:\repos\nmd-analysis\data\raw\neuralmanifolddynamics_ds005555_20260918_090500` is an MNDM export, not the raw BIDS catalog: 128 HDF5 files plus JSON/YAML metadata, 347,492,402 bytes total, and no EDF or event TSV files. It is not substituted for the fold-safe prediction surface.
- Existing fold-safe chart surface: `J:\repos\nmd-analysis\articles\BOAS_sleep_dataset_ndt._v.1.0\results\fold_safe_chart_qualification_20260930_v1\processed\ds005555`. Inventory: 660 HDF5 files, 100,506,401,893 bytes. These files are already fold-partitioned and include 3D and 9D chart coordinates, epoch/time identities and QC/support metadata. Read-only HDF5 schema inspection did not load coordinate values.
- The full raw BIDS catalog is 39.3 GB while J: had 9.3 GB free at inspection; even the canonical PSG EDF subset exceeds available space. No partial copy was attempted. This does not block using the already-present fold-safe HDF5 inputs.

The bounded v1.0 pilot replay audit at `K:\processed\ds005555_continuous_c123_prediction_safe_pilot_20260929_v1_0_replay\audit\pilot_validation.json` reports `PASS_BOUNDED_TECHNICAL_ONLY`, `outcomes_calculated=false`, and exact numeric replay (`maximum_absolute_numeric_difference=0.0`; 61 numeric and 15 nonnumeric columns). The original extraction audit remains `PENDING_REPLAY`; the replay audit is the completed result. This two-recording technical pass does not qualify full-cohort outcome scoring.

## Contract and protocol boundary

No measurement implementation, MNPS definition, preprocessing or result changed in this step. The existing protocol `articles/BOAS_sleep_dataset_ndt._v.1.0/preregistration_continuous_C123_20260929.md` freezes C1 as 3D h1 primary with fixed Ridge M0/M1 and participant-balanced held-out MSE reduction; h2/h4 and 9D are secondary. Its section 5 explicitly defers C2 until a specific accessibility/future-law feature is nominated and shown to use training-only or past-only information. Full-cohort C1 outcome scoring still requires the listed gates, independent review and a separately dated hash freeze/authorization.

The separate proposal `project/validate_c1_c2_c3/sl_001_ds005555.txt` suggests a distributional C1 score and new C2 accessibility comparisons. Those suggestions are not silently substituted for the frozen C1 estimator and do not qualify C2. If adopted for this article branch, they must be written as a dated amendment with fully specified estimators and leakage boundaries before any outcomes are inspected. Gate 8 remains **NOT OPEN**.

## Current analysis assets and gaps

- The shared analysis module `nmd-analysis/nmd_analysis/continuous_c123_estimators.py` already provides synthetic-tested C1 example construction, fixed Ridge fold evaluation and out-of-fold aggregation. No article-specific C1 data loader/runner has yet been added to this branch.
- The inspected fold-safe HDF5 example includes current chart arrays and an empty `jacobian` group; nearest-neighbour indices are present, but their presence is not an accessibility qualification. There is no qualified `a_hat`, effective-dimension, predictive-covariance, `kappa` or MNJ predictor in this surface. Do not treat the 660 HDF5 files as a ready C2 input.
- The article directory is currently an unfilled generic template; `results/` contains only `.gitkeep`. Existing generic contrast scripts/configs are retained unchanged and are not the C1/C2 analysis.

## Next steps

1. Freeze the C1/C2 branch specification. Resolve whether it retains the registered C1 Ridge/MSE estimand or prospectively amends it to a fully specified distributional forecast score. Record the amendment without editing the prior frozen protocol.
2. Build and synthetically validate an article-local reader/runner that binds the existing fold-safe HDF5 files to the source-support, gap/segment and split manifests. Keep execution in support/preflight mode until full-cohort outcome authorization is issued.
3. For C2, nominate one primary accessibility predictor (and baseline), implement or identify its past-only/fold-local estimator, then qualify validity, missingness, support and leakage behavior before defining any effect run.
4. Independently review the implementation and pilot/reference outputs. Do not compute C1/C2 outcome scores under this note; it records readiness only.
