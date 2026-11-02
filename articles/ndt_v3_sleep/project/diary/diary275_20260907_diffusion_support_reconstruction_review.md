# Diary 275 — independent diffusion-support reconstruction review

Date: 2026-09-07

Measurement question: can the stored sub-99 diffusion tensor, support count
and validity series be reproduced exactly from the pinned subject-anchored
3D state/time series and producer settings, so that candidate neighborhoods
can be exported with explicit stage endpoint flags?

Gate: candidate-only reconstruction. The exact tensor after stored dtype cast,
support, validity, computed producer status, source/config/input pins and
stored settings must pass before candidate rows are written. Unknown labels,
ties, adjacency, endpoint stages and temporal increments must remain visible.

The reviewed r9 source validates exactly seven producer file pins, rejects an
empty or partial producer set, requires `analysis_code` to resolve to the
runner itself, validates all seven settings without truncating fractional
integers, and compares the reconstruction settings to HDF5 stored
provenance. It checks source and input hashes before, during and after the
producer/helper usage. Candidate export remains fail-closed when any exact
gate fails.

Independent evidence: direct HDF5/output inspection found 1,068 queries and
21,360 rows, exactly 20 unique selections per query. Query/source/target stage
codes and window bounds match HDF5, source-to-target indices are adjacent,
all increments are positive, output hashes match, and the hash sidecar
matches. Nine queries have unknown stage code, no cutoff ties are ambiguous,
and code 8 appears in 68 source rows and 77 target rows. The independent
coordinator validation found 281/1,059 known queries with all twenty
same-known-stage endpoints, 33 known queries touching a disconnection
endpoint, and 88 endpoint rows touching code 8.

Validation commands and results:

- `H:\SourceRepo2\NeuralManifoldDynamics\.venv\Scripts\python.exe -B -m pytest -q articles\\ndt_v3_sleep\\tests\\test_diffusion_support_reconstruction_independent.py` — **6 passed**.
- Existing diffusion tests — **2 passed**.
- Complete article suite — **65 passed**.
- Independent direct HDF5/output checks and coordinator full-distance,
  argpartition, covariance and eigendecomposition validation — **PASS**.

Provenance: output
`results/diffusion_support_reconstruction_sub99_20260907_r9`; input hash
`3657fd599bbcddb774aa8ae237cb017f0a566c3a21e0877f4b43634d0d98a427`;
config hash
`9925b4c23e02914784ac4c56641fd25e1a2f76dbbd21377476093710923c549a`;
runner hash
`acc4c6be4470f60dc006cdf9b60cb541a3f3140af880a8e31ff452f9f1beed4b`.

Verdict: **PASS** for the bounded candidate reconstruction gate. The safe
claim is exact reproduction of the stored diffusion/support/valid series and
provenance-pinned candidate membership export. Full support, historical
membership and biological interpretation remain unestablished.

Canonical repository diary: project/diary/275_20260907_sleep_diffusion_support_review.md (repository root).
