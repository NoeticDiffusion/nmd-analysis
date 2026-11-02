# Signal-support provenance in nmd-analysis

The analysis package can read `mndm.signal_support_export.v1` through
`nmd_analysis.read_signal_support(path_or_open_h5)` and the CLI command below.
This is a read-only provenance audit. It does not run a stage contrast, change
coordinates, select estimators, mask samples, or change producer qualification.

```powershell
# Run in J:/repos/nmd-analysis/nmd-analysis with the analysis environment active.
python -m nmd_analysis.cli signal-support-audit `
  --input-h5 "path/to/explicit-recording.h5" `
  --output-root "path/to/new-audit-directory"
```

Repeat `--input-h5` for explicit additional inputs. Directories are not silently
searched. Existing output directories are refused. The output is
`signal_support_audit.json`; inputs are opened read-only and hashed before and
after the audit. The reader, audit and CLI source files are also hash-linked.

| Reader status | Meaning | Audit CLI |
|---|---|---|
| `recorded` | Recorded source/operation/epoch identity checks passed | Success; temporal support stays unknown |
| `legacy_missing` | This H5 lacks the new provenance group | Success with explicit unavailable evidence |
| `unsupported` | The present schema is not supported | Nonzero exit and diagnostic report |
| `malformed` | Present metadata is malformed or disagrees with source rows | Nonzero exit and diagnostic report |

`source_hash_status=recorded_only` means that the exported raw-file hash has
valid structure and agrees with the producer's recorded before/after checks.
The analysis reader does **not** rehash external raw files. Its separate H5
before/after hashes verify that the audited artifact stayed unchanged during
the audit. These are different checks.

The report retains execution operations, per-epoch nominal extents and gaps,
source-quality intervals, normalization center/scale and fit-population
provenance. It checks epoch IDs, order, source identity, nominal bounds,
source clocks and operation references. A plain H5 key plus its `_json` alias
is rejected as ambiguous. Nonfinite JSON and inconsistent positive support
claims are rejected. Missing support is never filled with zeros.

Validation is scoped: fit-population hashes and source-quality interpretation
are retained from ingest, not independently recomputed by this reader. A
normalization population does not become an independent calibration set.
Recording-level operation IDs are not a complete feature-specific dependency
graph. Even a successful audit always states
`scientific_qualification=not_assessed` and `claim_status=no_biological_claim`.

The engineering references are sub-99 only: the new 900-second r3 crop and
the earlier float64 whole-recording artifact. They are separate artifacts,
not two independent participants or a replication. The new crop has 30
provenance rows, 9 operation records within one source record, 9 original
source-quality intervals and 12 recorded fit features. Legacy provenance
remains absent/unknown. No stage-specific support certificate is produced.

Next scientific gate: specify the filter/reference dependency policy and
connect it to the article's increment-support decisions before upgrading any
sleep-stage claim. The article's previous results and input manifests remain
unchanged by this integration.
