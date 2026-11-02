# Independent participant reproduction

Protocol: independent_selection_protocol_20260910.json, frozen before sub-1 contrast inspection. This is a development protocol, not a registered confirmatory study.

From J:/repos/nmd-analysis, use the reviewed H Python environment and fresh output names:

```powershell
$env:PYTHONPATH='J:/repos/nmd-analysis/articles/ndt_v3_sleep/src;J:/repos/nmd-analysis/nmd-analysis'
$env:PYTHONDONTWRITEBYTECODE='1'
& H:/SourceRepo2/NeuralManifoldDynamics/.venv/Scripts/python.exe -B articles/ndt_v3_sleep/src/fullnight_stage_description.py --source-h5 "H:\SourceRepo2\NeuralManifoldDynamics\project\v3\independent_sleep_20260910\processed\ds005555\neuralmanifolddynamics_ds005555_20260910_114609\sub-1_Sleep_acq-psg\sub-1_Sleep_acq-psg.h5" --output H:/SourceRepo2/NeuralManifoldDynamics/project/v3/independent_sleep_20260910/reproduction_fresh --export-config articles/ndt_v3_sleep/config/epoch_sub1_independent_20260910.yaml --policy articles/ndt_v3_sleep/stage_dependency_policy_20260910.json
& H:/SourceRepo2/NeuralManifoldDynamics/.venv/Scripts/python.exe -B articles/ndt_v3_sleep/src/compare_parent_stage_direction.py --reference articles/ndt_v3_sleep/results/fullnight_support_sub99_20260910/fullnight_stage_summary.json --candidate H:/SourceRepo2/NeuralManifoldDynamics/project/v3/independent_sleep_20260910/reproduction_fresh/fullnight_stage_summary.json --protocol articles/ndt_v3_sleep/independent_selection_protocol_20260910.json --participants K:/ExternalReceivedDatasets/openneuro/ds005555/participants.tsv --output H:/SourceRepo2/NeuralManifoldDynamics/project/v3/independent_sleep_20260910/comparison_reproduction_fresh
```

The accepted H-stage description used the installed fullnight wrapper with explicit --epoch-support pointing to the new staged exporter, and explicit --descriptive-helper pointing to the installed article helper. Output description_final and comparison_r1 are retained as original evidence. Installed copies preserve original source paths/hashes; raw H5 is outside the article. The helper generalization preserves sub-99 default behavior (reference_backcompat exactly matched the old table and summaries).

Ingest command, from H:/SourceRepo2/NeuralManifoldDynamics:

```powershell
$env:PYTHONPATH='H:/SourceRepo2/NeuralManifoldDynamics/mndm/src;H:/SourceRepo2/NeuralManifoldDynamics/core/src'
$env:PYTHONDONTWRITEBYTECODE='1'
& .venv/Scripts/python.exe -B -m mndm.cli all --config project/v3/independent_sleep_20260910/ingest/sub1_independent_sleep.yaml --dataset ds005555 --subject 1 --force-features --n-jobs 1 --mem-budget-gb 4
```

Do not rerun into existing outputs: use a new output overlay. Ingest exited0; source/config pins and fresh validation are in ingest/. Diary344 records exact validation commands. No participant selection or parameter tuning followed contrast inspection.

For article tests add J:/repos/nmd-analysis/articles/ndt_v3_sleep to PYTHONPATH and run:

```powershell
& H:/SourceRepo2/NeuralManifoldDynamics/.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider articles/ndt_v3_sleep/tests
```

Some independent tests deliberately use these pinned local reference artifacts; they require the documented H/K data paths. Final installed test logs and receipt are in the H independent_sleep_20260910 workspace.
