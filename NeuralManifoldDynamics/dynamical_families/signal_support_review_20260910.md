# Independent review: analysis signal-support ingest

**Verdict: PARTIAL PASS, preinstall.** The staged reader, audit and CLI
preserve recorded provenance while keeping effective support and scientific
qualification unknown. The staged report is historical: it pins reader hash
`766684592a13ec767b38ffe3cafef51555523198b686200c812d0ca1f7d7d6a4`, while
the current reviewed reader after the final defensive patch hashes to
`803ef61c859def02048d704d1eafbe1c691539be7aedb96bb782cb9c7351873a`.
Acceptance therefore requires a fresh postinstall CLI report whose code pins
match the installed files.

Independent adversarial tests in
`staging/nmd-analysis/tests/test_signal_support_independent.py` passed 13/13.
They exercise real temporary H5 files and reject future schemas, nonfinite or
duplicate-key JSON, plain/`_json` alias collisions, dataset-instead-of-group,
empty recorded exports, shifted/duplicate rows, path/clock/bounds mismatches,
and unsupported finite support claims. They preserve `legacy_missing` for an
absent provenance group. Audit cases cover strict JSON, input mutation,
malformed statuses, no pooling, and forced
`claim_status=no_biological_claim`. The project environment whole staged suite
passed **260 tests, 6 skipped**; support reader/audit tests passed **21**.

Direct read of the final r3 H5 returned `recorded`, valid validation,
`source_hash_status=recorded_only`, `row_alignment_status=validated`,
`temporal_support.status=unknown`, and 30 rows. Its H5 SHA-256 is
`a98c30141097cf1a656c2f6b677b36827ad2e3752f6b5c1700c6526045e2fb7d`. Direct
read of the legacy H5 returned `legacy_missing`, zero rows, and unknown hash,
alignment, and support; its H5 SHA-256 is
`3657fd599bbcddb774aa8ae237cb017f0a566c3a21e0877f4b43634d0d98a427`.
The staged report has `status=audited`, no errors, no pooling, no biological
claim, and qualification not assessed. Its before/after H5 hashes agree.

`recorded_only` validates the producer's recorded source hash and internal
stability; the reader does not rehash the external EDF or events TSV. The
audit H5 hash is a separate immutability check. Effective filter support,
nonlocal adaptive feature dependencies, stage purity, and a feature-specific
dependency graph remain unknown. Source-quality and fit-population metadata
are retained rather than independently interpreted. The reader and audit are
read-only with respect to input H5 data.

After installation, rerun the CLI on the explicit r3 and legacy H5 paths into
a fresh directory, check installed reader/audit/CLI hashes and equal input
hashes before and after, then preserve the same statuses and unknown fields.
This review authorizes no biological or stage-specific support claim.
