# Diary 273 — independent bounded stage-support review

Date: 2026-09-07

Measurement question: do the accepted sub-99 epoch labels and temporal
bounds trace exactly to the pinned raw PSG `stage_hum` annotations, and what
same-label run support remains after the fixed two-sided rule?

Gate: bounded descriptive source-label and run-length audit. The contract
requires exact row alignment, explicit unknown labels and gaps/overlaps,
`max(bout_length - 2, 0)` retention for each contiguous known run, and
unknown support when recording duration is absent or invalid.

The earlier r6 review was partial because invalid recording durations could
produce numeric tails and the before-hash snapshot started after source reads.
The current r7 source resolves both. It validates finite nonnegative duration,
marks an epoch end beyond duration as a mismatch with no tail, snapshots all
pinned inputs before reads, and compares hashes after reads. It also keeps
code 8 as unknown, accepts a missing `stage_ai` column, validates integer IDs
and stage codes, checks sample-clock alignment, and records output hashes.

Independent evidence: direct reads found 1,068 matching rows; all stage,
onset, duration and 256 Hz inclusive sample-bound checks passed. Counts are
0:275, 1:20, 2:642, 3:15, 4:107 and code 8:9, split into 84 bouts. The
two-sided retained counts are Wake 249, N1 2, N2 581, N3 0 and REM 103. The
recording duration is 32,064 s, the final epoch bound is 32,040 s, and the
derived tail is 24 s. All four QC masks are true. The r7 manifest pins the
epoch table, raw TSV, code, config, epoch manifest and four provenance files;
the current code hash equals the manifest hash.

Validation commands and results:

- `H:\SourceRepo2\NeuralManifoldDynamics\.venv\Scripts\python.exe -B -m pytest -q articles\\ndt_v3_sleep\\tests` — **65 passed**.
- Independent pandas/NumPy checks of raw alignment, run lengths, source
  hashes, output hashes and manifest pins — **passed**.
- Synthetic failure checks for missing/invalid duration, shifted or
  mismatched rows, gaps/overlaps, noninteger IDs/codes and source mutation —
  **passed**.

Provenance: output
`results/stage_support_audit_20260907_r7`; epoch table SHA-256
`e18bd9cb9aff3e00ad959f8458390fd3d6a5baf0ce0ec89a07e3f2b710c5ae54`; raw
TSV SHA-256
`ff6fe9640f3188c12b7ee58dde085336cf22b12d7fff397f5f2012c25984cedd`; audit
code SHA-256
`1d895a51806592361d83b3851e675dc54f4759584e75fec49f2f81037cc8d119`.

Verdict: **PASS** for the bounded descriptive stage-support gate. The safe
claim is limited to source-label alignment, recording tail and exact
two-sided contiguous run support. Estimator support, diffusion-neighborhood
purity, stage-conditioned dynamics and biological interpretation remain
unestablished. The next gate is independent validation of the candidate-only
diffusion reconstruction.

Canonical repository diary: project/diary/273_20260907_sleep_stage_support_review.md (repository root).
