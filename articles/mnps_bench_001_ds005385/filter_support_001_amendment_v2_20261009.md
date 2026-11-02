# FILTER-SUPPORT-001 amendment v2 — separate boundary classes

Date: 2026-10-09. This amendment was written after the frozen v1 perturbation outputs and before the guarded-window measurement replay. It does not change the perturbation, filtering, or tolerance definitions.

## Why the support classes are separate

`sl_028` distinguishes (A) continuous-recording edges from (B) experimental trial boundaries. The v1 text's single phrase “operational guard” could be read as applying the worst physical-recording-edge margin to every internal trial. That is not appropriate: the physical edge is absent at an interior trial boundary. Report two guards and apply each only to its matching boundary class.

## Frozen results so far

- Trial-boundary perturbations: 96 complete-chain cases (six participants × control/memory load-13 boundary examples × start/end × four perturbations). The first tested grid margin passing all cases is **2 seconds**. At 1 second, the maximum peak ratio is `2.120343945584339e-4`, above the `1e-4` tolerance. At 2 seconds, the maximum peak ratio is `6.996166116488596e-5`; maximum RMS/stimulus-RMS ratio is `1.3124436597143726e-5`.
- Physical recording edges: 48 complete-chain cases (six participants × recording start/end × four perturbations). The first tested margin passing all cases is **4 seconds**. At 3 seconds, the maximum peak ratio is `1.466376499536378e-4`; at 4 seconds it is `3.6694779659436334e-5`.
- Use `g_trial = 2 s` for internal trial starts and ends. Use `g_recording = 4 s` only where a candidate window lies within four seconds of a physical recording edge. A window must satisfy both relevant boundaries independently.
- Pilot trial support begins at least 571.432 seconds after recording start and ends at least 12.318 seconds before recording end. Therefore the physical recording-edge margin does not further trim these six participants' trial windows.

These are tolerance-based operational margins, not exact finite support. The default frequency-domain resampler remains globally supported; observed influence is empirical for the tested lengths and perturbations.

## Exact guarded load-13 window check

The historic window is shifted inward by two seconds at trial start. The replay measures perturbation response over that exact new 20-second interval for start and scheduled-recall boundaries. Results are in `guarded_load13_window_leakage.csv`; the original unshifted-window comparison remains in `recall_window_leakage.csv`. Neither synthetic replay proves that speech occurred or contaminated source EEG.

## Output files

- `guard_summary.csv`, `guard_grid_all_cases.csv`: trial-boundary results.
- `recording_edge_guard_summary.csv`, `recording_edge_guard_grid.csv`: physical-edge results.
- `recall_window_leakage.csv`: influence over the historic 20-second load-13 window.
- `guarded_load13_window_leakage.csv`: influence over the exact shifted 20-second window.
- `run_manifest.json`, `recording_edge_manifest.json`: runtime, inputs, and frozen parameters.
