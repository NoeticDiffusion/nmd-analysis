# Bounded E3 sleep drift candidate follow-up

This is an article-local, read-only engineering candidate pilot. It freezes
the exact two E1/E2 H5 sources and their SHA-256 values before any prediction,
then reuses the installed `nmd_analysis.dynamical_families.drift` estimator.
The frozen split is train increments `0:600`, evaluation increments `700:800`,
60-second epoch-support embargo, 32 neighbours, minimum 12 training rows, and
the two existing estimators `local_mean` and `local_linear`. The explicit
coordinate datasets are `mnps_3d` and `coords_9d/values`; they are recorded as
candidate paths and are not asserted identical to the E1/E2 subject-anchored
family layers.

The accepted M3 reference smoke also requires
`provenance/geometry_contract/status` to be `ok`. The sub-1 source reports
`adjusted`, so its four candidate rows are intentionally serialized as
source-contract refusals with null predictions. This preserves negative
evidence; the runner does not relax the gate. The sub-99 source reports `ok`
and supplies the computed candidate rows. Any explicit-versus-subject-anchored
array equality observed in an H5 is retained as an H5-local observation only.

Run from `H:/SourceRepo2/NeuralManifoldDynamics` with the H virtualenv and the
installed analysis checkout on `PYTHONPATH`:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='J:/repos/nmd-analysis/articles/ndt_v3_sleep;J:/repos/nmd-analysis/articles/ndt_v3_sleep/src;J:/repos/nmd-analysis/nmd-analysis'
$python = 'H:/SourceRepo2/NeuralManifoldDynamics/.venv/Scripts/python.exe'
$config = 'J:/repos/nmd-analysis/articles/ndt_v3_sleep/config/sleep_drift_candidate_20260910.json'
$output = 'J:/repos/nmd-analysis/articles/ndt_v3_sleep/results/sleep_drift_candidate_20260910/run_r2'
& $python -B -m pytest -q -p no:cacheprovider J:/repos/nmd-analysis/articles/ndt_v3_sleep/tests/test_sleep_drift_candidate.py
& $python -B J:/repos/nmd-analysis/articles/ndt_v3_sleep/src/sleep_drift_candidate.py --config $config --output-root $output
```

These are the executed command paths. For reproduction, replace `$output`
with a fresh directory; the accepted `run_r2` is preserved and the runner
refuses to overwrite it.

The runner writes `candidate_report.json`, `candidate_predictions.json`, and
`output_hashes.json` under `run_r2` (the initial run is retained at the parent
directory). It retains actual train/evaluation indices and hashes,
endpoint overlap, per-increment epoch support, embargo distance, actual dt,
coordinate provenance, candidate predictions and held-out increments. It
refuses nonfinite coordinates/support and never imputes missing values.

The report is candidate diagnostics only. It does not run stage contrasts,
select outcomes, assess qualification, identify an Itô drift, or make a
biological claim. Epoch-window separation is recorded; full upstream signal
support remains unknown, while the source export records whole-record robust-z
fit populations that include evaluation rows and are therefore not held out.

Independent support review is recorded at
`peer_review/16_sleep_drift_candidate_support_audit.md`. Its verdict is
PARTIAL PASS for bounded candidate input support and METHOD-LIMITED for any
empirical interpretation.

The accepted corrected artifact is `results/sleep_drift_candidate_20260910/run_r2`.
The frozen spec hash is
`fb95a1b4a1fa3058e5fcb065d48978ef87e7b505044fcd57e14120e0978c7c77`. The
sub-99 and sub-1 source hashes are respectively
`217991681011397acd4493cd97cc74e7a982d361a04e6e94d29b40c8261ef8a1` and
`1eba1d7d9a470647992ab729f26a4ee5cea9249586e7e98cbad814759cff94db`.
The focused wrapper suite passed 15 tests. Independent direct-H5 numerical
verification passed with report SHA-256
`c96685946d50af882e2d9ce884f5ea68d4277f0daaea7b43ce88d11ac7479406`; all 400
sub-99 predictions matched direct reconstruction exactly, and all four sub-1
coordinate/estimator rows were strict geometry refusals with null predictions.

Coordinator final regression: 161 passed in 12.77 seconds. Exact combined
test and independent verification commands, reviewed code/config hashes and
resolved findings are recorded in `peer_review/17_sleep_drift_candidate_final_review.md`.
