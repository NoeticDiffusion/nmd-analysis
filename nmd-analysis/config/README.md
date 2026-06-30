# Config files

This directory holds the YAML configs that drive the two-stage `nmd-analysis` pipeline.
There are **two distinct families** — they are not duplicates.

## 1. Dataset configs — `ndt-analysis-<dataset>.yaml`

Used by the **`run`** command (`nmd-analysis run --config ...`).

These describe how to turn raw HDF5 input into cleaned Parquet tables:

- `input.h5_root` — path to the raw H5 dataset directory.
- `analyses` — which cleaned analyses/exports to enable.
- `flags` — e.g. `sleep_data_contrast`, `stage_code_map`, `min_stage_timepoints`.
- `modality_rules` — modality-specific overrides.
- `coordinate_contract` — coordinate normalization contract.

Loaded by `nmd_analysis.config.load_dataset_config`.

`ndt-analysis-template.yaml` is the starter template.

## 2. Analysis configs — `analysis-<dataset>.yaml`

Used by the **`analyze`** command (`nmd-analysis analyze --config ...`).

These describe how to turn cleaned Parquet tables into analysis results
(statistics, contrasts, reachability, Jacobian summaries):

- `input.cleaned_root` — path to the cleaned Parquet directory.
- `blocks` — which analysis blocks to enable, with per-block `validity` gates.
- `contrasts` — paired / unpaired contrasts to evaluate.
- `statistics` — permutation/bootstrap counts, FDR grouping, min group sizes.
- `qc` — QC thresholds applied before analysis.

Loaded by `nmd_analysis.analysis_config.load_analysis_config`.

## Typical workflow

```powershell
# 1. raw H5  ->  cleaned parquet
nmd-analysis run --config nmd-analysis/config/ndt-analysis-ds003490.yaml

# 2. cleaned parquet  ->  analysis results
nmd-analysis analyze --config nmd-analysis/config/analysis-ds003490.yaml
```

See `docs/configuration.rst` for the full schema reference.
