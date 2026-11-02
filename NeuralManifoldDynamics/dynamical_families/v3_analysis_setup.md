# NMD v3 analysis integration

The analysis package can extract the NMD v3 measurement families independently
of the older Jacobian/FTR layer. This is compatibility and support-audit work;
no sleep contrast, biological qualification, or M3 PASS is produced.

## Run the sleep support audit

From the `J:/repos/nmd-analysis` repository root in PowerShell:

```powershell
$env:PYTHONPATH = 'J:/repos/nmd-analysis/nmd-analysis'
.venv/Scripts/python.exe -B -m nmd_analysis.cli v3-audit --config nmd-analysis/config/ndt-analysis-ds005555-v3.yaml --input-root K:/processed/ds005555_dynamical_families/ds005555/neuralmanifolddynamics_ds005555_20260904_194153 --output-root H:/SourceRepo2/NeuralManifoldDynamics/project/v3/ds005555_new_audit --workers 1
```

Choose a fresh output directory for each audit. HDF5 inputs are opened read-only.
The example uses H: because J: ran out of free space during integration on
2026-09-05. Output can return to the analysis repository when space is available.
The explicit config selects extraction tables; it does not fit new estimators.
The ordinary `run` command supports the same table names and `--analyses` filter.
The `v3-audit` command writes Parquet, `v3_extraction_manifest.json` and
`v3_support_audit.json`. The manifest records the config hash and extraction
errors. The report uses only that run's output paths, not a glob of historical
Parquet files. An empty or errored extraction exits nonzero.

## New tables

| Analysis name | Grain | Contents |
|---|---|---|
| `dynamical_families_availability` | recording | Presence and provenance of the family surfaces |
| `diffusion_geometry_recording` | recording | Diffusion summary and certificate |
| `diffusion_geometry_window` | window | Serialized tensor/scalars, validity and aligned time identifiers when available |
| `destination_recording` | recording | Serialized destination result or explicit unavailable status |
| `resilience_recording` | recording | Serialized perturbation-family result or explicit unavailable status |

Canonical `/dynamical_families/{diffusion,destination,resilience}/v1` takes
precedence over legacy `/orthogonal_dynamics/` groups. The legacy namespace is
read-only. Unknown schemas are refused. Missing metadata is `not_recorded`,
not inferred scientific validity. NaN alignment values remain NaN.

The config also extracts existing Jacobian summaries, FTR horizons, transition
covariance and stochastic predictive-spread summaries in 3D/9D. These remain
under `nmd_analysis.local_dynamics`. The v3 certificate, inferential grain and
support signature are retained. Gate F uses discrete one-step transition
residual covariance; historical I-CARE tubes are not this schema.

`table_grain` describes the analysis table; `grain_*` describes the serialized
measurement contract. A recording summary of a window-native measurement does
not change its biological unit. Never feed window rows into a between-person
test. Missing metrics and refusals stay visible in the recording audit even
when no window table can be emitted.

## What the audit establishes

The support report counts rows, identified subjects and recordings, with
separate strata for coordinate contracts, states when present and validity
statuses. Counts are descriptive and not additive across overlapping strata.
It does not call a computed-but-`not_assessed` measurement biologically valid.
File-level computation failures cannot establish stage-specific missingness
when no time-aligned family rows exist.

Use this first to decide whether the available timebase and sampling support
the proposed sleep analysis. Existing ingestion may sample separated epochs;
the presence of a sleep label does not establish continuous dynamics. Do not
relax timestep validity thresholds simply to obtain computed tensors.

## Drift groundwork and remaining science

`nmd_analysis.dynamical_families.drift.crossfit_local_chart_b` accepts explicit
train/evaluation increment indices and produces a candidate chart velocity.
It checks overlap/embargo and records actual indices, temporal support and
hashes. For windowed measurements, callers must provide the full source-window
support, including filtering/feature support. Endpoint-only defaults describe
point samples and cannot certify independence of overlapping EEG windows.

The function does not orchestrate a whole cross-validation experiment, fit
fold-specific MNPS anchors, provide a qualified ingest overlay, or residualize
`a_hat`. The complete truth-known recovery/bias/rank/null benchmark remains
[M3 work](m3_design.md). `candidate_not_qualified` is intentional.

Next: inspect support, define a temporally valid state/event join and freeze
the matched-state/predictive-comparator protocol. Biological contrasts and
estimator qualification are separate from this integration. There is no
automatic cohort-wide biological analysis configuration yet.
