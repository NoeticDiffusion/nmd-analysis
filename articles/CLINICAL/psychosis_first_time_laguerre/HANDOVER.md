# Psychosis First-Time Laguerre Handover

This folder is a handover landing zone for the next LLM after the repository is moved to a larger disk.

The immediate goal is **not** to rebuild the whole psychosis paper. The goal is to let the next LLM quickly resume the exploratory `Surface B` / `Laguerre-adjacent` psychosis pilot that was just tested on the article data.

## What was done

The latest exploratory script lives in:

- `articles/CLINICAL/psychosis_first_time_episode/src/run_psychosis_surface_b_testshot.py`

It runs a short `Surface B`-like pilot on the psychosis article data by:

1. loading article-local cleaned `global_mnps_3d` rows from `data/cleaned/psychosis_cohort_anchor_20260520/`,
2. using the linked raw H5 files to recover per-window 3D MNPS trajectories,
3. computing per-window reachability covariance objects with `compute_reachability_cones_from_mnps(...)`,
4. summarizing both spatial and temporal deformation of those covariance objects,
5. applying relative-trace SPD regularization,
6. applying `arcsinh` before residualization against:
   - `tube_d_eff_median`
   - `tube_a_operator_norm_median`
7. exporting pooled and medication-stratified contrasts for:
   - `Healthy vs FEP`
   - `Healthy vs FEP medicated`
   - `Healthy vs FEP unmedicated`
   - `FEP medicated vs FEP unmedicated`

## Main outputs already generated

Full result bundle:

- `articles/CLINICAL/psychosis_first_time_episode/results/psychosis_surface_b_testshot_20260526_full/`

Most useful files there:

- `psychosis_surface_b_summary.md`
- `psychosis_surface_b_effect_sizes.csv`
- `psychosis_surface_b_subject_metrics.csv`
- `psychosis_surface_b_residual_models.json`

Session note:

- `project/diary/094_20260526_psychosis_surface_b_testshot.md`

## Current read

### ds003944 looks promising enough for a bounded follow-up

The strongest non-baseline `Surface B`-style psychosis signal was in `ds003944`, mainly in the **temporal** channel.

Most important rows:

- `Healthy vs FEP`
  - top raw Surface B: `surface_b_logeuc_temporal_grad_p95`
    - Cliff's delta about `0.268`
    - AUROC about `0.634`
  - top residualized Surface B: `surface_b_logeuc_temporal_grad_p95_asinh_resid_reachability`
    - Cliff's delta about `0.274`
    - AUROC about `0.637`

- `Healthy vs FEP medicated`
  - top raw Surface B: `surface_b_logeuc_temporal_grad_p95`
    - Cliff's delta about `0.383`
    - AUROC about `0.692`
  - top residualized Surface B: `surface_b_logeuc_temporal_grad_p95_asinh_resid_reachability`
    - Cliff's delta about `0.387`
    - AUROC about `0.694`

Working interpretation:

- `ds003944` provides a modest but coherent temporal deformation signal.
- The raw and residualized directions stay aligned.
- This is more promising than the coma `Surface A` story, but it is still exploratory.

### ds003947 looks weak on this layer

`ds003947` did not show a comparably convincing `Surface B` result.

For pooled `Healthy vs FEP`:

- top raw Surface B: `surface_b_spectral_spatial_grad_p95`
  - Cliff's delta about `-0.120`
  - AUROC about `0.560`
- top residualized Surface B: `surface_b_spectral_spatial_grad_p95_asinh_resid_reachability`
  - Cliff's delta about `-0.125`
  - AUROC about `0.562`

Working interpretation:

- `ds003947` is not the right target for a larger follow-up right now.

### Important guardrail

The existing article-local reachability baseline in `ds003944` is still at least as strong as the new `Surface B` layer:

- `tube_capture_gate_median`
  - Cliff's delta about `0.39`
  - AUROC about `0.695`

So this new layer should be treated as an exploratory geometry extension, not as a replacement primary endpoint.

## Exact command that worked

From repo root:

```powershell
python "articles/CLINICAL/psychosis_first_time_episode/src/run_psychosis_surface_b_testshot.py" --workers 8 --output-dir "H:/SourceRepo2/NoeticDiffusion/articles/CLINICAL/psychosis_first_time_episode/results/psychosis_surface_b_testshot_20260526_full"
```

Smoke test command that also worked:

```powershell
python "articles/CLINICAL/psychosis_first_time_episode/src/run_psychosis_surface_b_testshot.py" --datasets ds003944 --workers 1 --max-points-per-run 120 --output-dir "H:/SourceRepo2/NoeticDiffusion/articles/CLINICAL/psychosis_first_time_episode/results/psychosis_surface_b_testshot_20260526_smoke2"
```

## Critical migration caveat

This is the most important thing for the next LLM to know after the disk move:

The cleaned psychosis parquet files contain absolute `source_h5_path` values pointing to the old repo location on `H:`.

That means:

- if the repository is moved to a different absolute path or a different drive letter,
- the script may fail even though the raw H5 files were copied correctly,
- because `run_psychosis_surface_b_testshot.py` currently trusts `source_h5_path` from the cleaned parquet.

### What to verify first after the move

Check these paths:

- new repo root
- `data/raw/neuralmanifolddynamics_ds003944_20260520_121126/`
- `data/raw/neuralmanifolddynamics_ds003947_20260520_114135/`
- `data/cleaned/psychosis_cohort_anchor_20260520/`

Then inspect one cleaned parquet row and one `source_h5_path`.

If `source_h5_path` still points to the old location, there are two reasonable fixes:

1. **Preferred quick fix**
   Update `run_psychosis_surface_b_testshot.py` so it reconstructs the H5 path relative to repo root instead of trusting the absolute parquet path.

2. **Heavier but cleaner fix**
   Regenerate the relevant cleaned psychosis outputs so the stored `source_h5_path` values match the new disk location.

## Best next step for the next LLM

Do **not** broaden this immediately across both psychosis datasets.

The most sensible next pass is tightly scoped to `ds003944` only:

1. make the script migration-safe after the disk move,
2. rerun the existing `ds003944` pilot once to confirm parity,
3. add `Bures-Wasserstein` beside log-Euclidean,
4. add a simple bootstrap or leave-one-out check for the temporal `p95` result,
5. only then decide whether to add an appendix paragraph or figure to the psychosis article.

## Suggested first prompt for the next LLM

Use something close to:

> Resume the psychosis `Surface B` exploratory pilot from `articles/CLINICAL/psychosis_first_time_laguerre/HANDOVER.md`. First make `articles/CLINICAL/psychosis_first_time_episode/src/run_psychosis_surface_b_testshot.py` robust to the new repo path after disk migration, then rerun the `ds003944` pilot and compare the results to the previously exported `psychosis_surface_b_testshot_20260526_full` bundle before making any further methodological changes.

## Related files

- `articles/CLINICAL/psychosis_first_time_episode/src/run_psychosis_surface_b_testshot.py`
- `articles/CLINICAL/psychosis_first_time_episode/results/psychosis_surface_b_testshot_20260526_full/psychosis_surface_b_summary.md`
- `articles/CLINICAL/psychosis_first_time_episode/results/psychosis_surface_b_testshot_20260526_full/psychosis_surface_b_effect_sizes.csv`
- `project/diary/094_20260526_psychosis_surface_b_testshot.md`

