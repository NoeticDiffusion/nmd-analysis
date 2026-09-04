# Part1 NeuroComBat-cleaned vs non-ComBat summary

## New NeuroComBat-cleaned outputs

The following result directories were generated against:

`J:/repos/NoeticDiffusion/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260527_101007_NeruroComBat_cleaned`

- `timeline_analysis_20260601_part1_neurocombat_cleaned_primary12h`
- `timeline_analysis_20260601_part1_neurocombat_cleaned_hourly12h`
- `mnps_summary_20260601_part1_neurocombat_cleaned_primary12h_cpc15_prefiltered`
- `mnps_summary_20260601_part1_neurocombat_cleaned_hourly12h_cpc15_prefiltered`
- `outcome_contrasts_20260601_part1_neurocombat_cleaned_primary12h_cpc15_prefiltered`
- `outcome_contrasts_20260601_part1_neurocombat_cleaned_hourly12h_cpc15_prefiltered`

These names intentionally include `neurocombat_cleaned` so they stay visually distinct from the existing non-ComBat `20260525` bundle.

## What was rerun

This pass reran the article-local reachability pipeline that is compatible with the NeuroComBat-cleaned export:

1. `icare_patient_timeline_analysis.py`
2. `icare_mnps_summary_analysis.py --analysis reachability_cones`
3. `icare_outcome_contrast_analysis.py`

The rerun was limited to reachability outputs because the current NeuroComBat-cleaned root was already known to have broader invalid-coordinate issues on other article lines, and the part1 article-facing reachability bundle was the closest like-for-like comparison available here.

## Main comparison against existing non-ComBat part1 outputs

- Primary `0_12h` extreme-outcome subject coverage fell from `141` subjects in the non-ComBat bundle to `139` subjects in the NeuroComBat-cleaned rerun.
- Hourly extreme-outcome subject coverage fell from `141` to `140`.
- `sub-0977` is absent already at the NeuroComBat-cleaned timeline level.
- `sub-0512` remains in the NeuroComBat-cleaned timeline table but drops out before the primary reachability handoff, so the primary MNPS summary ends at `139` subjects.

The much larger change is metric availability:

- Non-ComBat primary reachability handoff: `82` usable metrics.
- NeuroComBat-cleaned primary reachability handoff: `3` usable metrics.
- Non-ComBat hourly reachability handoff: `83` usable metrics.
- NeuroComBat-cleaned hourly reachability handoff: `3` usable metrics.

The only surviving NeuroComBat-cleaned reachability metrics were:

- `near_singular_rate`
- `tube_d_eff_split_half_n`
- `tube_log_det_split_half_n`

All of the article-facing reachability geometry metrics that drove the original part1 signal disappeared from the NeuroComBat-cleaned handoff because they no longer survived as usable numeric fields in the new export.

## Primary contrast change

In the original non-ComBat `part1` primary bundle, the strongest reachability contrasts included large shifts in:

- `persistence_hysteresis_log_det_median`
- `persistence_log_det_median`
- `persistence_log_eig_var_median`
- `cone_d_eff_h1_median`

In the NeuroComBat-cleaned rerun, those metrics were not available in the article-facing handoff at all.

For the three surviving metrics, the primary `0_12h` patient-level contrasts were effectively null:

- `near_singular_rate`: new delta-median `0.0`, Mann-Whitney `p = 1.0`
- `tube_d_eff_split_half_n`: new delta-median `0.0`, Mann-Whitney `p = 1.0`
- `tube_log_det_split_half_n`: new delta-median `0.0`, Mann-Whitney `p = 1.0`

For reference, these same three metrics were already weak in the original non-ComBat bundle, so the NeuroComBat-cleaned rerun does not reveal a cleaner alternative signal. Instead, it collapses the reachability result surface almost entirely.

## Interpretation

This looks less like a subtle contrast shift and more like a data-compatibility problem for the current reachability export path:

- the rerun completed without hard script failures,
- but the metric handoff contracted from `82-83` reachability metrics down to `3`,
- and the remaining contrasts were all null.

The practical takeaway is that the current NeuroComBat-cleaned `part1` root is not article-equivalent to the existing non-ComBat reachability bundle. It does not preserve enough usable reachability metrics to support a like-for-like refresh of the original `comatose_ndt` findings.

## Suggested next step

If we want a true ComBat comparison for this article line, the next debugging step should be upstream: inspect why the NeuroComBat-cleaned export leaves most reachability-cone summary fields unusable or all-NaN, rather than treating this as a meaningful biological reversal of the original article result.
