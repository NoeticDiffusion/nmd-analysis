# Verified development pilot handover

Working directory: `J:/repos/nmd-analysis`. Accepted artifact:
`articles/ndt_v3_sleep/results/pilot_verified_final_20260906`.
Source and all configuration/code hashes are in its `pilot_manifest.json`.
The source SHA256 is
`3657fd599bbcddb774aa8ae237cb017f0a566c3a21e0877f4b43634d0d98a427`.

The independent reviewer executed the final run and inspected it before
the coordinator opened its results (review 01 and diary 261). Equivalent
reproduction command in PowerShell, using the recorded project environment:

```powershell
$env:PYTHONPATH='J:\repos\nmd-analysis\nmd-analysis'
$env:PYTHONDONTWRITEBYTECODE='1'
.venv/Scripts/python.exe -B articles/ndt_v3_sleep/src/sleep_pilot.py --config articles/ndt_v3_sleep/config/pilot_sub99_verified.yaml --output-root articles/ndt_v3_sleep/results/pilot_verified_final_20260906
```

Final run exit 0. That output now exists and is deliberately protected against
reuse: choose a fresh explicit `--output-root` for repetition. Intermediate
`pilot_20260906` and `pilot_verified_20260906` are superseded, preserved runs.

Coordinator regression command:

```powershell
$env:PYTHONPATH='J:\repos\nmd-analysis\nmd-analysis;J:\repos\nmd-analysis\articles\ndt_v3_sleep\src'
$env:PYTHONDONTWRITEBYTECODE='1'
.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider articles/ndt_v3_sleep/tests nmd-analysis/tests/test_v3_audit.py nmd-analysis/tests/test_v3_pipeline.py nmd-analysis/tests/test_dynamical_families.py nmd-analysis/tests/test_local_dynamics.py
```

Result: **25 passed in 3.27s**. Article-only independent reviewer: 10 passed.
Covered examples include source/config mismatch, nonempty output refusal,
unknown labels/statuses, malformed alignment and actual interval gaps.
The real-data test checks serialized array alignment; it is not a biological
or full estimator-support test.

After independent review the coordinator recomputed source, config and six
code hashes, read all 16 Parquet tables, verified native statuses/grains and
counted finite values per diffusion scalar. The saved check is
`20260906_coordinator_validation.json`, including output-table hashes,
stage counts and no-biological-claim status.

Manuscript build (from the article directory):

```powershell
typst compile 'Neural State Geometry and Dynamical Measurement Families Across Sleep.typ' 'Neural State Geometry and Dynamical Measurement Families Across Sleep.pdf'
```

Exit 0. Both PDF pages were rendered with bundled Poppler and visually
inspected. Supplement sources were adapted but not separately compiled in
this step. No raw data copied, no cohort or contrasts run, no publication.

Next gate and limitations: `../sciencelead/01_pilot_readiness.md`.
