# Next Steps

## After moving the repo
1. Confirm the moved repo has enough free disk space.
2. Open `HANDOVER_20260526_regional_run_after_move.md`.
3. Prefer a clean rerun of the regional pipeline unless there is a strong reason to recover from partial outputs.

## Recommended execution order
1. Run:
   ```powershell
   python "articles/CLINICAL/comatose_ndt_regional/src/run_regional_article_pipeline.py"
   ```
2. Confirm these directories exist and contain fresh outputs:
   - `articles/CLINICAL/comatose_ndt_regional/results/mnps_summary_20260526_regional_primary12h/`
   - `articles/CLINICAL/comatose_ndt_regional/results/mnps_summary_20260526_regional_hourly12h/`
   - `articles/CLINICAL/comatose_ndt_regional/results/article_exports_20260526_regional_cpc15/`
   - `articles/CLINICAL/comatose_ndt_regional/figures/20260526_regional_cpc15/`

## Validate outputs
1. Check that these files exist and are non-empty:
   - `regional_reachability_ranking_table.csv`
   - `regional_lateralization_summary.csv`
   - `regional_hourly_summary.csv`
   - `regional_mnj_primary_table.csv`
   - `regional_primary_metric_contrasts.csv`
2. Check that the three SVG figure files were written.
3. Spot-check that all seven regions are present.

## Then update the manuscript
1. Open `articles/CLINICAL/comatose_ndt_regional/comatose_ndt_regional_draft.typ`.
2. Replace the `TBD` cells using the exported CSV files.
3. Update the results prose to reflect:
   - whether reachability is bilateral/distributed versus localized
   - which regions lead the MNJ hierarchy
   - whether `tube_d_eff_median` remains the clearest regional reachability signal
4. Keep MNJ and reachability interpretations clearly separated.

## If rerun is too expensive
1. Reuse the partial primary directory:
   - `results/mnps_summary_20260526_regional_primary12h/`
2. Rebuild the missing small derived files from the existing adapter outputs.
3. Then run hourly rebin and article exports only.

## Final closeout
1. Write a new diary entry in `project/diary/`.
2. Summarize:
   - what completed,
   - what the top regional findings were,
   - and whether any remaining blockers still exist.
