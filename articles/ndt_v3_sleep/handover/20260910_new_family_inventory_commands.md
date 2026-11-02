# Reproduce the family inventory and verify this planning step

The analysis plan is not a report of new sleep-stage results. The accepted inventory
is results/new_family_inventory_20260910/family_metric_inventory.json. Older H
inventory variants are superseded; scientific qualification remains null.

From J:/repos/nmd-analysis:

```powershell
$env:PYTHONPATH='J:/repos/nmd-analysis/nmd-analysis'
$env:PYTHONDONTWRITEBYTECODE='1'
& H:/SourceRepo2/NeuralManifoldDynamics/.venv/Scripts/python.exe -B articles/ndt_v3_sleep/src/inventory_new_families.py --h5 H:/SourceRepo2/NeuralManifoldDynamics/project/v3/fullnight_support_20260910/processed/ds005555/neuralmanifolddynamics_ds005555_20260910_112127/sub-99_Sleep_acq-psg/sub-99_Sleep_acq-psg.h5 --h5 H:/SourceRepo2/NeuralManifoldDynamics/project/v3/independent_sleep_20260910/processed/ds005555/neuralmanifolddynamics_ds005555_20260910_114609/sub-1_Sleep_acq-psg/sub-1_Sleep_acq-psg.h5 --out H:/SourceRepo2/NeuralManifoldDynamics/project/v3/family_article_plan_20260910/inventory_reproduction_fresh.json
```

Output must not exist. This calls installed canonical readers and adapters,
records reader/code hashes and H5 before/after hashes, and performs no refit.

Coordinator formula check from H:/SourceRepo2/NeuralManifoldDynamics:

```powershell
& .venv/Scripts/python.exe -B project/v3/family_article_plan_20260910/verify_metric_definitions.py
```

This independently reconstructs alpha/omega/gap from stored J, verifies center
indices, diffusion trace and alias identities, and confirms missing drift fields
remain NaN. It does not certify estimator accuracy or biological validity.

The forthcoming E1/E2 runner must follow analysis_plan_new_families_20260910.json:
fixed existing inputs, exact center/query label mapping, all specified endpoints,
separate 3D/9D grids, median/quartiles/denominators and N2-minus-Wake, no pooling.
FTR and empirical drift are not prerequisites. No new ingest is required.
