# E3 coordinate-support gate handover

This is a separate article-local gate for the frozen E3 sleep drift candidate.
It preserves the original strict `geometry_contract/status == ok` outcome in
each row and evaluates the frozen coordinate-support policy separately. The
policy allows an adjusted source only when both selected coordinate layers,
time grid, epoch support and recorded support metadata pass, the 3D Jacobian
is clean, and the 9D adjustment is a positive, internally consistent
condition-number-only filter. No status is rewritten in the source or in the
strict result. The scoped adjusted rows call the installed
`crossfit_local_chart_b` directly after eligibility passes.

## Frozen inputs

- Policy/config: `J:/repos/nmd-analysis/articles/ndt_v3_sleep/config/sleep_drift_coordinate_gate_20260912.json`
- Frozen policy-spec SHA-256:
  `5b60875f1a2b5957a223877104895747a09fefae237a35c1acceb9296b114910`
- Policy file SHA-256:
  `1998611daf17b006ba28e63eb8cab86f32b19ea53e082456759b785907d86574`
- Base E3 config:
  `J:/repos/nmd-analysis/articles/ndt_v3_sleep/config/sleep_drift_candidate_20260910.json`
- Base E3 config SHA-256:
  `89f40623b4c310c257f2baab3c6d1edcc8f75d16eb2a284371494d26454a965e`
- Source H5 SHA-256 values are unchanged before/after the run:
  - sub-99: `217991681011397acd4493cd97cc74e7a982d361a04e6e94d29b40c8261ef8a1`
  - sub-1: `1eba1d7d9a470647992ab729f26a4ee5cea9249586e7e98cbad814759cff94db`

The runner binds the policy to these exact source paths and hashes, explicit
`mnps_3d` and `coords_9d/values` paths, canonical axes, and the unchanged
train `0:600` / evaluation `700:800` split with `k=32`, minimum support 12,
embargo 60 seconds, and local mean/local linear estimators.

## Commands

From `H:/SourceRepo2/NeuralManifoldDynamics`:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='J:/repos/nmd-analysis/articles/ndt_v3_sleep/src;J:/repos/nmd-analysis/nmd-analysis'
& .venv/Scripts/python.exe -B -m sleep_drift_coordinate_gate `
  --policy J:/repos/nmd-analysis/articles/ndt_v3_sleep/config/sleep_drift_coordinate_gate_20260912.json `
  --output-root J:/repos/nmd-analysis/articles/ndt_v3_sleep/results/sleep_drift_coordinate_gate_20260912/run_r4
```

Focused synthetic policy and failure controls:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='J:/repos/nmd-analysis/articles/ndt_v3_sleep;J:/repos/nmd-analysis/articles/ndt_v3_sleep/src;J:/repos/nmd-analysis/nmd-analysis'
& .venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider `
  J:/repos/nmd-analysis/articles/ndt_v3_sleep/tests/test_sleep_drift_coordinate_gate.py
```

The focused suite passed **17 tests**. It covers policy acceptance, strict
versus scoped status, unknown/inconsistent/extra reason metadata, unsupported
adjustment reasons, gaps, deficient rank, hash mismatch, overwrite refusal,
fractional and boolean counters, missing stored 3D evidence, contradictory
3D evidence, and retained nonfinite rows. A requests dependency-version
warning is emitted by the environment and does not fail the tests.

## Frozen run evidence

The final bounded run is:
`J:/repos/nmd-analysis/articles/ndt_v3_sleep/results/sleep_drift_coordinate_gate_20260912/run_r4`

The first run is retained directly in the result parent directory; later
`run_r2` and `run_r3` directories are retained as
superseded history. Their numeric candidates were unchanged; `run_r3` was
not accepted as the frozen artifact because the source hash changed during
the final stored-3D provenance correction. The first post-correction test
attempt also exposed an assertion-message mismatch for a boolean finite-row
fraction; the gate already refused that input, the assertion was corrected,
and the final focused suite passes.

- 8 rows total.
- sub-99: all four strict rows and all four scoped rows computed, with 100
  predictions per row.
- sub-1: all four strict rows remain `refused` with `source_contract`; all
  four scoped rows are eligible and computed with 100 predictions per row.
- The scoped sub-1 rows preserve observed overall status `adjusted` and do
  not relabel it as `ok`.
- `candidate_predictions.json` SHA-256:
  `f7c16955b766b5c0caeaf5a1c06b1c4e894d0c580dfe1b858dacc04cd0f1ffd7`
- `candidate_report.json` SHA-256:
  `bf5857b52c434807562357dd134646ffe7f8018c2a5e549b11aed1409483a1bc`
- Runner SHA-256:
  `e8c97c19d308630e409879033a3fcf5b1d6d1837c5f3afbc6c1add0f2d3fc019`
- Unchanged legacy candidate runner SHA-256:
  `c9ca8ebef383e6d1db0b25dd431b088e2bca6047f74e5687d7c880dc2df86294`
- Unchanged drift estimator SHA-256:
  `28a783d9e3818b3f4d9c4ffafa99e66b5d367a0ac8bebae8ef4e8fd971cafde7`

The result remains an engineering candidate with
`candidate_not_qualified`, `no_biological_claim`, `not_assessed`, and
`stage_contrast=not_run`. Effective upstream signal support is still unknown;
whole-record robust-z fit populations and the PPG/EOG fallback distinction
remain in provenance. Existing exploratory sub-1 predictions were already
inspected and are not preregistered or unseen primary outcomes. No canonical
diffusion family field, new contrast, or stronger independence claim was
created.

The commands above identify the accepted executed run. For reproduction,
choose a fresh output directory; accepted outputs must not be overwritten.
Root final combined regression:178passed90.96s. Final direct-HDF5 verification
of run_r4 passed for all800vectors, both source hashes, policy/output hashes,
preserved strict outcomes and unchanged sub-99 values. Exact commands and
final review are in `peer_review/19_sleep_coordinate_gate_final_review.md`.
