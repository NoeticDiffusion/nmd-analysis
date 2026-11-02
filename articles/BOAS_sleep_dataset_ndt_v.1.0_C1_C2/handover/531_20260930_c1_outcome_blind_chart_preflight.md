# 531 — 2026-09-30 — ds005555 outcome-blind C1 chart preflight

## Summary

**PARTIAL PASS — support/provenance preflight only.** The article-local runner binds the explicitly selected fold-safe H5 chart rows to the frozen participant folds, source-support audit, segment identifiers, chart windows, and h1/h2/h4 paths. It does not read chart-coordinate arrays or stage/outcome fields and does not calculate predictions, scores, contrasts, or effects.

No measurement implementation, numerical behavior, MNPS definition, preprocessing, or measurement semantics changed. The canonical 3D/9D chart definitions remain fixed. This step does not amend the previously registered C1 score or open the full-cohort scoring gate. C2 remains unqualified.

## Inputs and selection

- Read-only chart input: `articles/BOAS_sleep_dataset_ndt._v.1.0/results/fold_safe_chart_qualification_20260930_v1/processed/ds005555`.
- The directory contains 660 H5 files. The runner selects 500 files from the five explicit label-free fold run pairs: fold 0 v2 and folds 1–4 v1. The remaining 160 files are retained fold-0 training variants and are inventoried but not read into the C1 support surface.
- Frozen fold manifests are taken from the V4 source-support audit. All 78 primary-surface participant IDs occur in exactly one apply fold, and apply assignments cover all 100 primary-surface recordings.
- The source audit has 119,670 rows over 128 recordings and 100 PIDs; its primary surface contains 92,545 rows over 100 recordings and 78 PIDs. The runner reads only an explicit allow-list of identity, time, source-support, gap, segment, hash, and QC columns. Stage/outcome columns in the CSV are excluded.
- The raw EDFs were not copied or read in this preflight.

## Results

- All 462,725 selected chart-row instances (train and apply across folds) matched exactly one source-support row by `(file, epoch_id)`. H5 BIDS subject, numeric PID, fold grouping subject, start/end times, and frozen source hash were cross-checked.
- The five apply folds form a disjoint partition of the 78 primary-surface PIDs.
- The source audit reports zero rows with a nonzero input-sample gap count. Complete forecast paths also had no time-contiguity or segment-break failures. Missing intermediate/target row identities remain a separate exclusion.
- For the primary support cell, 3D h1 with two historical rows: 92,346 apply candidate origins; 92,038 outcome-blind eligible paths; 308 unqualified origins with a missing intermediate/target row. Eligible paths cover all 78 PIDs and all 100 PID-recording cells.
- Apply support counts are 91,876 eligible paths at h2 and 91,555 at h4. The 9D support counts match the 3D counts under the H5 QC metadata. Training paths are repeated across folds: 368,152 eligible 3D h1 paths from 369,384 candidate origins, so they are not an independent participant count.

The runner reads H5 participant identity, epoch/time/window vectors, and stored QC booleans. It checks coordinate dataset shapes only; it never indexes coordinate values. The result is a technical support map, not evidence that future chart values predict anything.

## Files and reproducibility

- Runner: `articles/BOAS_sleep_dataset_ndt_v.1.0_C1_C2/src/c1_outcome_blind_preflight.py`
- Output: `articles/BOAS_sleep_dataset_ndt_v.1.0_C1_C2/results/c1_outcome_blind_preflight_20260930_v1/`
  - `validation.json`
  - `c1_path_support_summary.csv`
  - `c1_path_support_by_fold_pid_recording.csv`
  - `selected_h5_inventory.csv`
  - `fold_inventory.csv`
  - `chart_run_inventory.csv`

Validation performed:

- `python -m py_compile articles/BOAS_sleep_dataset_ndt_v.1.0_C1_C2/src/c1_outcome_blind_preflight.py` — passed.
- `python articles/BOAS_sleep_dataset_ndt_v.1.0_C1_C2/src/c1_outcome_blind_preflight.py --output-root <fresh temporary directory>` — completed with `PARTIAL_PASS_OUTCOME_BLIND_C1_SUPPORT_PREFLIGHT`, 500 selected H5 files and 462,725 support-bound chart rows.
- The final rerun's five CSV artifacts matched the article output; the final validation records the 78-PID apply partition and the primary-surface counts. The projection digests bind the exact support columns and the H5 identity/time/QC metadata used.

Two preliminary guard failures exposed assumptions in the new preflight code, not input failures: the source audit includes side-stratum recordings outside the primary chart surface, and H5 BIDS subject IDs differ from the biological grouping PID. The runner now checks primary-surface coverage separately and verifies both identifiers against the source audit and fold manifest.

## Contract limits and next gate

The existing source protocol still specifies 3D h1 as primary, fixed Ridge M0/M1, and participant-balanced held-out MSE reduction; this preflight neither amends that score nor runs it. H5 generic temporal-support status remains `unknown`, and H5 source-quality status remains `not_recorded`; row support is retained as a separate hash-bound audit object. Gate 8 remains **NOT OPEN**.

Next, write a dated article-branch C1 score lock that explicitly carries forward or amends the existing registered score, and nominate one C2 accessibility predictor with a train-only/past-only leakage boundary and capacity-matched baseline. Only after those protocol decisions and their review should outcome scoring be considered.
