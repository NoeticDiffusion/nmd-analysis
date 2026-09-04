# Handover to NMD — ds004587 `anchor_index` scale failure

**Date:** 2026-07-12  
**From:** NoeticDiffusion analysis / `illusionGame_EAP`  
**To:** NeuralManifoldDynamics  
**Status:** bug report and requested guardrail; no scientific inference depends on the affected composite

## Summary

The refreshed ds004587 export
`neuralmanifolddynamics_ds004587_20260712_081757` successfully includes
`/anchor_state`, but its legacy `anchor_index` is numerically invalid for
analysis. The global maximum is `875,000,000`, whereas its median is `0.043`
and IQR is `0.380` (maximum/IQR approximately `2.30e9`).

The largest outlier is fully localized and reproducible:

- H5: `sub-FFE111_ses-01_illusion_game_run-01/sub-FFE111_ses-01_illusion_game_run-01.h5`
- `anchor_state` row index: `2`
- affected fields:
  - `sympathetic_index = 875,000,000`
  - `anchor_index = 875,000,000`
- no other v0.1 component is present on that row.

This is not a one-row event: `488` windows exceed an absolute
`anchor_index` value of `1000`, across 10 run files. The reported maximum is
therefore a visible example of a wider robust-scaling failure, not an
otherwise valid composite with one bad sample.

## Source-level trace

The maximal example, `sub-FFE111`, has no ECG, respiration, or PPG physiology
files in the source release. At its offending row:

| Surface | `eog_blink_rate` | ECG/PPG/HRV candidates |
|---|---:|---|
| `/features_raw/values` | `0.875` | all `NaN` |
| `/features_robust_z/values` | `875,000,000` | all `NaN` |

The default `sympathetic_index` specification includes `eog_blink_rate` as a
positive fallback. For this example, with all physiological candidates
missing, the unbounded robust-z value becomes the full
`sympathetic_index`; the v0.1 nanmean composite then copies it unchanged to
`anchor_index`. The repeated multi-subject failures make robust-z
degeneracy, rather than only this missing-modality case, the primary defect
to correct.

The relevant implementation path is:

1. `pipeline/anchor_state.py`:
   `DEFAULT_ANCHOR_INDEX_SPECS["sympathetic_index"]` includes
   `eog_blink_rate`;
2. `_feature_series()` reads robust-z values;
3. `_combine_signed_series()` accepts the single finite fallback;
4. `_nanmean_composite()` writes the resulting value as `anchor_index`.

## Analysis action already taken

The article pipeline excludes `anchor_index` through a gross-scale gate
(`max(abs(value)) / IQR > 1000`). It is not used in the IG-only exploratory
association screen. The retained raw respiratory and HRV features remain
separately reported.

This protects the current analysis but should not be the durable pipeline
solution.

## Requested NMD guardrails

1. **Robust-z degeneracy:** prevent division by an effectively zero robust
   scale from producing finite values of this magnitude. Emit `NaN` (or an
   explicit invalid-status value) when the scale is below a documented floor.
2. **Modality-aware anchor eligibility:** do not allow EOG-only fallback to
   instantiate a physiological `sympathetic_index` when ECG/PPG inputs are
   wholly absent. Mark the component and composite unavailable instead.
3. **Composite quality propagation:** if an anchor component is unavailable or
   numerically invalid, expose that in `/anchor_quality` and prevent it from
   entering the composite nanmean.
4. **Export-level validation:** add a post-export scale/finite check for every
   anchor component and composite, with a clear summary/manifest warning.

## Minimal regression test

Create an input with all ECG/PPG/HRV features `NaN`, finite
`eog_blink_rate = 0.875`, and a degenerate robust-z scale. Expected behavior:

- `sympathetic_index`: `NaN` / unavailable;
- `anchor_index`: `NaN` / unavailable;
- quality/status: explicitly fails physiology-support eligibility;
- no finite sentinel-scale value is exported.
