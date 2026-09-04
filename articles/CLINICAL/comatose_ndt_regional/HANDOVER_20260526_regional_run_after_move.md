# Handover: Regional Coma Run After Project Move

## Purpose
This note is for the next LLM after the repository has been moved to a larger disk.

Goal:
- resume the regional EEG coma pipeline in `articles/CLINICAL/comatose_ndt_regional/`
- finish the dataset run cleanly
- produce article-facing CSVs/figures
- then populate the remaining `TBD` cells in `comatose_ndt_regional_draft.typ`

## Current status
- The regional pipeline code has already been implemented.
- The article draft has already been wired to concrete output files.
- The main blocker was disk space, not code logic.

The project ran out of space on `H:` during the regional export recovery step.
At the time of failure:
- `H:` effectively had `0` free space.
- The primary regional run had already written the large adapter outputs.
- The smaller derived files were not completed.

## Important implemented files
- `articles/CLINICAL/comatose_ndt_regional/src/icare_regional_mnps_summary_analysis.py`
- `articles/CLINICAL/comatose_ndt_regional/src/build_regional_article_exports.py`
- `articles/CLINICAL/comatose_ndt_regional/src/run_regional_article_pipeline.py`
- `articles/CLINICAL/comatose_ndt_regional/config/icare_ndt_analysis_regional.yaml`
- `articles/CLINICAL/comatose_ndt_regional/comatose_ndt_regional_draft.typ`
- `ndt-analysis/ndt_analysis/legacy_adapters.py`

Related diary entry:
- `project/diary/095_20260526_coma_regional_pipeline_wiring.md`

## Dataset and cohort contract
Primary processed bundle:
- `E:/Science_Datasets/physionet/processed/physionet_icare_2_1/neuralmanifolddynamics_physionet_icare_2_1_20260525_141608`

Regional EEG groups:
- `frontal`
- `central`
- `parietal_occipital`
- `temporal`
- `midline`
- `left_hemisphere`
- `right_hemisphere`

Primary cohort contract:
- reuse the coma part1 time metadata
- `CPC 1` vs `CPC 5`
- primary window `0_12h`

## What already exists
Partial primary output directory:
- `articles/CLINICAL/comatose_ndt_regional/results/mnps_summary_20260526_regional_primary12h/`

Files confirmed present there:
- `run_level_adapter_summaries.csv`
- `patient_timebin_adapter_summaries.csv`
- `run_level_signal_metrics.csv`

File present but incomplete/useless:
- `patient_timebin_signal_metrics.csv` is currently `0` bytes and should be treated as invalid.

The previous full primary run exited with a non-zero code, but not before writing the large primary CSVs above.

## What the next LLM should do

### Recommended path: clean rerun after move
After the project is moved to a larger disk, the simplest path is to rerun the regional pipeline cleanly from the repo root.

Run from the moved repo root:

```powershell
python "articles/CLINICAL/comatose_ndt_regional/src/run_regional_article_pipeline.py"
```

That script is intended to:
- run the primary `0_12h` regional summary
- rebin to hourly
- build article-facing exports

If you want to run the primary step only first:

```powershell
python "articles/CLINICAL/comatose_ndt_regional/src/icare_regional_mnps_summary_analysis.py" `
  --processed-root "E:/Science_Datasets/physionet/processed/physionet_icare_2_1/neuralmanifolddynamics_physionet_icare_2_1_20260525_141608" `
  --timeline-input-dir "articles/CLINICAL/comatose_ndt/results/timeline_analysis_20260525_part1_primary12h" `
  --output-dir "articles/CLINICAL/comatose_ndt_regional/results/mnps_summary_20260526_regional_primary12h" `
  --time-bin-scheme primary_12h `
  --analysis regional_mnps_jacobian_3d `
  --analysis regional_reachability_cones_3d `
  --prefilter-good-cpc 1 `
  --prefilter-poor-cpc 5 `
  --prefilter-time-bin 0_12h `
  --workers 20
```

Then:

```powershell
python "articles/CLINICAL/comatose_ndt/src/icare_rebin_mnps_summary.py" `
  --input-dir "articles/CLINICAL/comatose_ndt_regional/results/mnps_summary_20260526_regional_primary12h" `
  --output-dir "articles/CLINICAL/comatose_ndt_regional/results/mnps_summary_20260526_regional_hourly12h" `
  --time-bin-scheme hourly_12h
```

Then:

```powershell
python "articles/CLINICAL/comatose_ndt_regional/src/build_regional_article_exports.py" `
  --primary-summary-dir "articles/CLINICAL/comatose_ndt_regional/results/mnps_summary_20260526_regional_primary12h" `
  --hourly-summary-dir "articles/CLINICAL/comatose_ndt_regional/results/mnps_summary_20260526_regional_hourly12h" `
  --output-dir "articles/CLINICAL/comatose_ndt_regional/results/article_exports_20260526_regional_cpc15" `
  --figure-dir "articles/CLINICAL/comatose_ndt_regional/figures/20260526_regional_cpc15"
```

### Faster recovery path: reuse the already written primary CSVs
If disk space is available but you want to avoid recomputing the whole primary run, you can recover the missing small files from the already written adapter outputs in:
- `articles/CLINICAL/comatose_ndt_regional/results/mnps_summary_20260526_regional_primary12h/`

Minimum recovery tasks:
1. regenerate `patient_timebin_signal_metrics.csv` from `patient_timebin_adapter_summaries.csv`
2. regenerate `metric_handoff_manifest.json`
3. run hourly rebin
4. run article exports

The previous attempt failed only because writing those additional files exhausted disk space.

## Expected article-facing outputs
The draft is already wired to these outputs:
- `results/article_exports_20260526_regional_cpc15/regional_reachability_ranking_table.csv`
- `results/article_exports_20260526_regional_cpc15/regional_lateralization_summary.csv`
- `results/article_exports_20260526_regional_cpc15/regional_hourly_summary.csv`
- `results/article_exports_20260526_regional_cpc15/regional_mnj_primary_table.csv`
- `results/article_exports_20260526_regional_cpc15/regional_primary_metric_contrasts.csv`
- `figures/20260526_regional_cpc15/regional_primary_reachability_heatmap.svg`
- `figures/20260526_regional_cpc15/regional_primary_mnj_heatmap.svg`
- `figures/20260526_regional_cpc15/regional_hourly_reachability_panels.svg`

## Important implementation notes
- `regional_mnps_jacobian_3d` was patched to read the real `/regional_mnps/<group>/jacobian` tensors.
- Regional `mdr_median` currently uses a centered finite-difference fallback because the regional bundle exposes `jacobian` but not a dedicated regional `jacobian_dot`.
- The pipeline remaps the existing coma part1 timing metadata onto the new regional bundle by matching H5 path suffixes.

## Current primary findings already observed
These came from in-memory analysis of the successfully written `patient_timebin_adapter_summaries.csv`.

Reachability:
- strongest overall regions: `left_hemisphere`, `right_hemisphere`, then `central`, `parietal_occipital`, `frontal`
- pattern is largely bilateral rather than strongly lateralized
- `tube_d_eff_median` is strongly positive for `CPC1` vs `CPC5` in all regions
- persistence metrics are modestly positive
- `tube_a_operator_norm_median` and `tube_capture_gate_median` are negative, meaning lower capture/contraction-like signal in `CPC1`

MNJ:
- strongest regions: `parietal_occipital`, `frontal`, `left_hemisphere`, `midline`
- strongest MNJ metrics were `spectral_radius_median`, `anisotropy_abs_eig_median`, and `frobenius_norm_median`
- `rotational_power_median` was the weakest MNJ signal

Interpretation snapshot:
- regional reachability looks real and fairly distributed/bilateral
- regional MNJ also looks real, with somewhat stronger posterior/frontal emphasis depending on metric family

## After successful rerun
Once the outputs exist, the next LLM should:
1. inspect the generated regional CSVs/figures
2. replace the `TBD` entries in `comatose_ndt_regional_draft.typ`
3. update the discussion text to reflect the observed bilateral reachability pattern and the regional MNJ ranking
4. write a new diary entry summarizing the completed rerun and article fill-in

## Suggested first check after the move
Before rerunning anything:

```powershell
Get-PSDrive -PSProvider FileSystem | Select-Object Name,Free,Used
```

If the moved repo root has plenty of free space, prefer the clean rerun path above.
