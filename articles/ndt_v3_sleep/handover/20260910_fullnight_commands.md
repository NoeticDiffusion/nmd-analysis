# Full-night execution and reproduction

All outputs below must be fresh. The original raw files and H5 are read-only. Run analysis from J:/repos/nmd-analysis. Use the existing H repository Python environment.

```powershell
$env:PYTHONPATH='J:/repos/nmd-analysis/articles/ndt_v3_sleep/src;J:/repos/nmd-analysis/nmd-analysis'
$env:PYTHONDONTWRITEBYTECODE='1'
& H:/SourceRepo2/NeuralManifoldDynamics/.venv/Scripts/python.exe -B articles/ndt_v3_sleep/src/fullnight_stage_description.py --source-h5 "H:\SourceRepo2\NeuralManifoldDynamics\project\v3\fullnight_support_20260910\processed\ds005555\neuralmanifolddynamics_ds005555_20260910_112127\sub-99_Sleep_acq-psg\sub-99_Sleep_acq-psg.h5" --output H:/SourceRepo2/NeuralManifoldDynamics/project/v3/fullnight_support_20260910/reproduction_fresh --export-config articles/ndt_v3_sleep/config/epoch_sub99_fullnight_support_20260910.yaml --policy articles/ndt_v3_sleep/stage_dependency_policy_20260910.json
```

Ingest ran from H:/SourceRepo2/NeuralManifoldDynamics:

```powershell
$env:PYTHONPATH='H:/SourceRepo2/NeuralManifoldDynamics/mndm/src;H:/SourceRepo2/NeuralManifoldDynamics/core/src'
$env:PYTHONDONTWRITEBYTECODE='1'
& .venv/Scripts/python.exe -B -m mndm.cli all --config project/v3/fullnight_support_20260910/ingest/sub99_fullnight_support.yaml --dataset ds005555 --subject 99 --force-features --n-jobs 1 --mem-budget-gb 4
```

Do not rerun ingest into its existing output root: create a new overlay/output first. The first launch failed before processing because core/src was missing from PYTHONPATH; pipeline.log preserves that failure. Corrected pipeline_r1.log ended successfully. H project/diary/342 records ingest validation commands, including the final validation_r4 report; earlier validator reports are historical and superseded.

The accepted analysis ran from H staging using the same CLI with explicit --epoch-support and --descriptive-helper pointing to the installed J article src files, and output description_final. Installed helper defaults are adjacent files. Output JSON retains original H execution paths and hashes after its copies are installed in the article; raw H5 was not copied. The source SHA is 217991681011397acd4493cd97cc74e7a982d361a04e6e94d29b40c8261ef8a1.

Tests from the J root use PYTHONPATH including J:/repos/nmd-analysis/articles/ndt_v3_sleep and its src plus nmd-analysis, PYTHONDONTWRITEBYTECODE=1:

```powershell
& H:/SourceRepo2/NeuralManifoldDynamics/.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider articles/ndt_v3_sleep/tests
```

Pre-install: 90 existing tests and 7 new tests passed separately. Postinstall results and immutable install receipt are recorded under H:/SourceRepo2/NeuralManifoldDynamics/project/v3/fullnight_support_20260910.
