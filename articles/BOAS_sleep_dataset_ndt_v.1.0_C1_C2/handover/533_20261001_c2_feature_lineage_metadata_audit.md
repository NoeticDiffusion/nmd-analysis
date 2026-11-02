# 533 — 2026-10-01 — C2 feature-lineage metadata audit

## Scope and status

This is a metadata-only lineage check for the selected fold-safe H5 feature rows. It did not read `/features_raw` values, chart coordinates, stage/outcome fields, future targets, predictions, or scores. It does not qualify the C2 baseline or open the scoring gate.

**Result: exact row identity/time linkage is confirmed across the selected surface. Feature-value equality and per-row causal/source-quality support remain unverified.**

## Findings

- Across the 500 selected fold-safe H5 files, 462,725 row instances map to 92,545 unique `(file, epoch_id)` keys. H5 window bounds matched the J and K feature tables exactly for the corresponding rows; the metadata join found no missing keys, time mismatches, or shape errors.
- The J summary root contains 92,545 rows across 100 files and 49 columns. The K feature-only root contains 119,670 rows across 128 files and 97 columns. Row identity/time alignment does not establish equality of their feature values or producer operations.
- A bounded check of `sub-101` linked 935 H5 rows (`epoch_id` 0–934) to 935 unique J and K identity/time rows. Its K QC sidecar source SHA-256 matches the fold-manifest source SHA-256. The sidecar reports the finite-causal extraction/schema, but its `effective_filter_support` remains unknown; this does not certify row-level filter contributors.
- The H5 run manifest points at the J summary root. The H5 exporter looks for `qc_artifacts` under that root, where the sidecars are absent. The K feature-only root contains 128 per-recording QC sidecars. This explains the `missing_qc_sidecar` status as a resolver-scope mismatch for the inspected path; it does not establish that all H5 rows inherit qualified support from K.
- Byte-level hashes for the complete J/K feature tables and a full 500-H5-to-sidecar lineage were not completed. No exact feature-value lineage is claimed.

## Limits and next action

The row key/time join is sufficient to identify the corresponding sidecar candidates without copying data, but it is not proof that the exported H5 feature/chart values were produced by the same qualified causal path. The current support metadata still lacks a certified per-row effective filter interval and a complete recorded source-quality map. The C1 H5 metadata audit also notes that the historical run manifest does not bind a clean executed source tree.

Next, resolve support lineage on one or two recordings in a fresh output root using an explicit sidecar root and a clean, hash-bound producer checkout. Verify raw source hash, exact feature-to-epoch alignment, effective causal support, source-quality intervals, and chart export metadata. Treat this as a technical producer pilot only; do not calculate C1/C2 outcomes or effects. If it passes, extend metadata/support binding across the selected surface before any protocol review or scoring authorization.

## Evidence boundary

The underlying bounded and full-surface joins used only H5 identities, epoch IDs, window times, table schemas, source hashes, run/config manifests, and sidecar metadata. No predictor or outcome values were opened. The pilot described above has not yet been run.
