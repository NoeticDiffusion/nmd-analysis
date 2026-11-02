# Reproduce E1/E2 sleep results

Accepted numerical output: results/new_family_sleep_20260910 (final runner run_r3). Accepted figures: its figures directory (final figures_r3). Original plan remains planned_not_executed as a historical frozen specification; the analysis manifest records executed status. This is development evidence, not preregistration or biological qualification.

From H:/SourceRepo2/NeuralManifoldDynamics, choose fresh output directories:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='J:/repos/nmd-analysis/articles/ndt_v3_sleep;J:/repos/nmd-analysis/articles/ndt_v3_sleep/src;J:/repos/nmd-analysis/nmd-analysis'
& .venv/Scripts/python.exe -B J:/repos/nmd-analysis/articles/ndt_v3_sleep/src/new_family_sleep_analysis.py --h5 H:/SourceRepo2/NeuralManifoldDynamics/project/v3/fullnight_support_20260910/processed/ds005555/neuralmanifolddynamics_ds005555_20260910_112127/sub-99_Sleep_acq-psg/sub-99_Sleep_acq-psg.h5 --h5 H:/SourceRepo2/NeuralManifoldDynamics/project/v3/independent_sleep_20260910/processed/ds005555/neuralmanifolddynamics_ds005555_20260910_114609/sub-1_Sleep_acq-psg/sub-1_Sleep_acq-psg.h5 --plan J:/repos/nmd-analysis/articles/ndt_v3_sleep/analysis_plan_new_families_20260910.json --inventory J:/repos/nmd-analysis/articles/ndt_v3_sleep/results/new_family_inventory_20260910/family_metric_inventory.json --output H:/SourceRepo2/NeuralManifoldDynamics/project/v3/family_sleep_results_20260910/installed_reproduction
& .venv/Scripts/python.exe -B J:/repos/nmd-analysis/articles/ndt_v3_sleep/src/plot_new_family_sleep.py --endpoint-rows H:/SourceRepo2/NeuralManifoldDynamics/project/v3/family_sleep_results_20260910/installed_reproduction/endpoint_rows.json --output-root H:/SourceRepo2/NeuralManifoldDynamics/project/v3/family_sleep_results_20260910/installed_figures_reproduction
& .venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider J:/repos/nmd-analysis/articles/ndt_v3_sleep/tests
```

Use the authoritative long JSON once. The same observations also have a convenience CSV export; reading both as different observations is incorrect. Figure support/PSD-floor diagnostics count each query once across three long metric rows. The final plotter rejects duplicate observations and preserves separate recordings and representations. Code8 is a distinct unresolved label, never merged with known-stage summaries.

The runner refuses existing output roots, duplicate input files and frozen input/plan mismatches. Producer computation status remains separate from numerical finiteness, support, scientific validity and qualification. All unknown qualifications remain null. No measurement estimator is retuned or refitted by label.

Original implementation run H:/run_r1 and independent reviewer run project/v3/family_sleep_results_20260910/run_r1 used different NumPy/h5py versions but produced byte-identical numeric tables. Run_r2 preserves producer availability status; final run_r3 additionally requires exact diffusion identifiers, retains null summaries for unavailable endpoints and names the finite-valid denominator explicitly. Endpoint values remain identical; summary metadata changes are intentional. Final plot source may name H:/run_r1, whose authoritative JSON hash equals the installed table; manifests preserve actual execution paths rather than rewriting provenance after copying. Earlier figure drafts are superseded by figures_r3 and are not installed.

Coordinator independently read HDF5 arrays without importing the runner/readers and reconstructed all90 known-stage summaries and18 contrasts. Float64 summary arithmetic matched at rtol1e-12/atol1e-14. An earlier direct check used float32 interpolation arithmetic and differed by about3e-11; it was corrected to match the specified float64 descriptive arithmetic, preserving the earlier artifact as history. Evidence/scripts: H project/v3/family_sleep_results_20260910/verify_direct_h5.py, compare_direct_results.py, coordinator_direct_h5_float64.json and run_r3/coordinator_table_verification.json.

The article includes all nine endpoint contrasts and six distribution panels; four actual-center timeline figures are accompanying artifacts. Full H5 sources are not copied into the article. Independent review and exact units evidence are in peer_review/15_new_family_sleep_results_review.md.
