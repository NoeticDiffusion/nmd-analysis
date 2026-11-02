# Postinstall independent review: analysis signal-support ingest

**Date:** 2026-09-10  
**Verdict: PASS for the bounded ingest contract.** The reviewed files were
installed into `J:/repos/nmd-analysis` under the recorded receipt, and the
fresh CLI audit was run from that installed analysis checkout. The prior
preinstall hash mismatch is resolved.

The installed test log reports **32 passed**. The independent preinstall
review suite had already passed 13/13 adversarial tests and the full staged
project suite had passed 260 tests with 6 skips. The installation receipt
records 13 installed files and exact hashes for the reader, audit, CLI,
independent tests, and review diaries. `installed_validation.json` reports
`status=PASS`, `installed_files_verified=13`, and the installed reader path
under `J:/repos/nmd-analysis/nmd-analysis/nmd_analysis/signal_support.py`.

The fresh report at
`H:/SourceRepo2/NeuralManifoldDynamics/project/v3/analysis_support_20260910/installed_reference/signal_support_audit.json`
reports `status=audited`, `errors=[]`, `claim_status=no_biological_claim`,
`scientific_qualification=not_assessed`, and `subject_pooling=not_performed`.
The new r3 H5 is `recorded`, validation `valid`,
`source_hash_status=recorded_only`, `row_alignment_status=validated`,
`temporal_support.status=unknown`, with 30 rows and 9 operations. Its H5
SHA-256 is
`a98c30141097cf1a656c2f6b677b36827ad2e3752f6b5c1700c6526045e2fb7d`.
The legacy H5 is `legacy_missing`, with zero exported provenance rows (not an empty recording) and unknown hash,
alignment, and support. Its H5 SHA-256 is
`3657fd599bbcddb774aa8ae237cb017f0a566c3a21e0877f4b43634d0d98a427`.

The report's before and after H5 hash maps are identical. Its installed code
pins match the receipt and installed files:

- reader: `803ef61c859def02048d704d1eafbe1c691539be7aedb96bb782cb9c7351873a`;
- audit: `5ca1574b4cc6122bdcd6a0f34885735db23e72f97f214287d8d13e0553979948`;
- CLI: `06cef8872ca9601c7bb13fcb1cc3fb1e66eb9cb51c2e2c3cf1af74154f21b585`.

`external_raw_rehash_performed=false` is preserved. Thus the source EDF/TSV
hashes are producer-recorded evidence, while the audit H5 hashes establish
that the audited artifacts did not change. Effective filter support, nonlocal
adaptive feature dependencies, stage purity, and biological qualification
remain unknown or unassessed; the recording-level operation list is not a
feature-specific dependency graph. This PASS closes the ingest and provenance
installation gate only and authorizes no new scientific or stage-specific
claim.
