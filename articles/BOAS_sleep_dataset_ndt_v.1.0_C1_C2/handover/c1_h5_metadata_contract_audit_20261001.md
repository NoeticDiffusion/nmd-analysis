# C1/C2 handover — fold-safe H5 metadata contract audit

**Date:** 2026-10-01  
**Status:** Partial metadata binding confirmed; the complete producer/source-support contract is **not proven**. Gate 8 remains closed.

## Scope and result

This audit asks whether the selected fold-safe chart H5 surface can be tied, from manifests, configs, H5 metadata and already-recorded preflight evidence, to the frozen chart producer, fold-anchor and source-support contract. It does not authorize C1 or C2 outcome scoring.

The existing preflight selects 500 of 660 H5 files: training and apply runs for folds 0–4, with fold 0 v2 and folds 1–4 v1. Its validation records 462,725 chart-row instances bound to source-support rows; five apply folds disjointly cover the 78-PID primary surface. The exact validation artifact is SHA-256 `6fc15bfbeb84fa6ac5f11a3d6def0e03adf94352b2661cbb4dee56fca200038a`. Its metadata projection digests are:

- Outcome-blind source-support columns: `f98837e6e27cadc1c51e6aff0a534c172fe35712a4a27e8e3b965870528ba5b1`.
- H5 identity, time and QC metadata: `cf1a477ac9c98ee33bc2be40fd03e7c24ba1098e9ec6d60909ca518f930e4832`.

The source-support validation is `PARTIAL_PASS_SOURCE_SUPPORT_ONLY` (SHA-256 `068e77b2b470e44257ccf2d3184c0aecdbc2ecd142af900f73bf67d9a513def2`); the all-fold chart-map validation is SHA-256 `4175558bebf72f990b81f2b899d9116f43d8bc706d75de8033152fe00f08676a`, with map parquet SHA-256 `9b6ffb767f4e30b6f9a2f729f79c9e2b5342088d96e7266f34164b69aace8902`.

The per-run validation entries record hashes for all 10 manifests, provided configs and resolved configs. The captured cross-check found all 10 run-manifest/config/resolved-digest links consistent; runs are marked completed with zero run errors, and training/apply roles match their fold overlays. H5 `provenance/contract/config_digest_sha256` values match the associated resolved manifest digests. The inventory's `manifest_source_sha256` binds source EDFs; it is not an H5-byte digest. The recorded metadata projection digest is also not a digest of complete H5 payloads, so these records do not establish byte-for-byte H5 integrity.

## Contract fields that agree

The captured metadata scan covered the 500 selected H5 files without indexing chart arrays. All report MNDM `3.1.0`, schema `mnps_tensor_spec_v2_4`, the primary 3D layer `coords_3d_cohort_anchored`, primary coordinate contract `cohort_anchored`, axis order `[m,d,e]`, and 9D definition version `2.0`. The 3D mapping source is `mnps_projection.v1_mapping`; normalization metadata reports `robust_z`.

All five training/apply fold pairs report matching training-derived anchor identity and hash. Anchor settings agree with the overlays: IQR scaling, minimum 20 subjects, subject-balanced cohort anchoring, source `mndm.fold_split.training_ranges_only`; the H5-reported training subject count agrees with the run manifest. The captured inner anchor hashes are:

| Fold | H5 anchor ID | H5/anchor parameter hash | Anchor artifact byte SHA-256 |
|---|---|---|---|
| 0 | `ds005555_continuous_c123_fold_0_chart_label_free_v2` | `6d53ee0bed64ac41a1398a1243696491feb699472d9ce966f1dcbbf7df34d590` | `4de494ab07257adba37005fb622b87fa67b346907b410a4310146e78e6d040d3` |
| 1 | `ds005555_continuous_c123_fold_1_chart_label_free_v1` | `395582ad6f754574324aec0e6b91f6ba378603d712968e54aa6950c3dc394156` | `e50b7d55919a4fa65864231f2b47e25f1b708404409107b4bdeb0c1b663cbe03` |
| 2 | `ds005555_continuous_c123_fold_2_chart_label_free_v1` | `a11eb58c5127d2246a0aaba0509de6656bdb5e24678c1e58109065fc6ae30b33` | `7c82ceb64af66d7c8141d091fe6962d67ae1e7b9a4521e9d4f7d9abdc56456dc` |
| 3 | `ds005555_continuous_c123_fold_3_chart_label_free_v1` | `b0b6db727bb8ca57b8b42c0f1eb23158f52114f199db8b5390f351bfc709cb41` | `124453a4b37eed0d6860e5ea39f1e6614e83bfd9591bd5f416a179667150e837` |
| 4 | `ds005555_continuous_c123_fold_4_chart_label_free_v1` | `a76bff0b2c31e993f4ea9eed829010e313584e571bb47f186b0cf656a23f4bf7` | `48be0f0d8b722396b93f4c16575761ad1fd618005b50a8f396d61d02fa5effe2` |

These checks support fold/config/anchor **metadata consistency**. They do not prove that every producer operation ran as declared for every exported row.

## Contracts still unproven

- H5 signal-support metadata reports `status=recorded`, but `temporal_support_status=unknown` and `source_quality_status=not_recorded`; its reason says effective filter support is not certified for every epoch row. The run manifests likewise report support as unknown. The separate row-support join is useful identity/gap evidence, but does not certify the exported feature/coordinate dependency interval or source-quality interval for each row.
- Run manifests record git revision `2b61d3eca37dfca4892dee488ad211e3f7ae037d`, matching the captured producer checkout revision, but do not bind a clean source tree or a complete executed-code-tree hash. The producer checkout was modified at audit time. A revision string plus config digest cannot prove which modified source files executed.
- The imported config chain expresses intended causal preprocessing, but config intent does not establish per-row execution. In particular, source/filter-support certification remains absent. Handover 532 independently describes the H5 support-sidecar mismatch and missing quality sidecar.
- The preflight binds identity/time/QC projections and source hashes, not full H5 bytes. Thus payload integrity is not established by the quoted projection hashes.

**Conclusion:** metadata supports the selected run, fold, config-digest and anchor associations. It does not establish the full frozen producer/config/anchor/**source-support** contract for scoring. Keep C1 and C2 scoring gated until the row-level causal support/source-quality contract and executed producer identity are resolved and separately reviewed.

## Evidence inspected

- Frozen source protocol: `articles/BOAS_sleep_dataset_ndt._v.1.0/preregistration_continuous_C123_20260929.md`.
- Article handovers: `530_20260930_c1_c2_data_and_gate_readiness.md`, `531_20260930_c1_outcome_blind_chart_preflight.md`, and `532_20261001_c2_fold_safe_spectral_input_readiness.md`.
- Preflight metadata: `articles/BOAS_sleep_dataset_ndt_v.1.0_C1_C2/results/c1_outcome_blind_preflight_20260930_v1/validation.json` and `selected_h5_inventory.csv`.
- Fold-safe qualification manifests, provided configs, resolved config digests, H5 metadata/provenance, and five fold anchor artifacts under `articles/BOAS_sleep_dataset_ndt._v.1.0/results/fold_safe_chart_qualification_20260930_v1/`.
- Source-support and all-fold chart-map validation records named above.

Checks used were read-only: repository status and file inventory; parsing the preflight JSON/CSV; checking recorded run/config/fold/anchor digests; and reading HDF5 metadata, group names and dataset shapes. No chart-coordinate array was indexed; no stage label or outcome field/value, future target, forecast, or score was read or calculated.

## Process deviations

The process was not perfectly metadata-only, and that limitation is recorded explicitly:

1. A preliminary preview of the minified `signal_support_ledger.json` emitted stage-source interval records. The preview was stopped and its content was not used in this audit. No stage label/outcome value or C1/C2 result was inspected from it.
2. A later H5 layout probe printed all root attributes, including a serialized feature-anchor attribute containing per-feature training-median summaries. This was not chart-coordinate data, a future target, a stage label/outcome, prediction or score. The output was stopped; no further H5 content was queried.

These deviations reduce the strength of the process-isolation claim. The substantive audit conclusion above is limited to captured validation, manifest/config and metadata evidence; neither deviation is treated as evidence that the full source-support contract passes.
