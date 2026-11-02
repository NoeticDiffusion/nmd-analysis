# 003 - 2026-09-11 - ingest response confirmed: fidelity gate works; two new bundles consumed

## Summary

Ingest responded to `ingest_jacobian_fidelity_handover.md` (Priority 1–3) with two new I-CARE 2.1 bundles, both built from an updated overlay:

- `neuralmanifolddynamics_physionet_icare_2_1_20260911_125829` ("part1_0_12h") — same 161-subject population as `20260904_225047`, re-ingested with the fix. Used here as `bundle_id=20260911_125829`, role **discovery/exploratory (corrected)**.
- `neuralmanifolddynamics_physionet_icare_2_1_20260911_123135` ("next_140") — **141 new subjects, zero overlap** with part1. Used here as `bundle_id=20260911_123135`, role **confirmatory**.

Both restrict ingest to filename hours 000–012 (`exclude_files` / `next_140_0_12h` naming), which independently resolves Priority-3 item 4 (WFDB HH≥24 clocks) for this scope: **0/1815 and 0/1838 runs** have `time_reference_status != ok` in the two new bundles (previously 156/3484 `missing_or_invalid_start_end`).

## Priority 1 — Jacobian fidelity gate: confirmed working exactly as requested

Verified directly in `/jacobian/derived_metrics/v1/provenance` on sampled files from both bundles:

```text
provenance/fit_fidelity_gate         = rel_mse_baseline_median
provenance/fit_fidelity_gate_version = provisional_icare_20260911
provenance/fit_fidelity_threshold    = 0.9
provenance/rel_mse_baseline_median   = 0.976  (example file)
provenance/operator_semantics        = continuous_time_generator
provenance/nominal_dt_sec            = 4.0
provenance/abscissa_units            = 1/second
summary/fit_identified               = False
```

This is exactly requested-items 1–4 from the prior handover. Effect on this dataset, sampled 120 files per bundle:

| bundle | `computed` | `insufficient_support` | dominant `failure_reason` |
|---|---:|---:|---|
| part1 (125829) | 2/120 (full-dataset: 22/1815) | 118/120 | `local_linear_fit_not_better_than_baseline` (116/118) |
| next_140 (123135) | 0/120 (full-dataset: 53/1838) | 120/120 | `local_linear_fit_not_better_than_baseline` (115/120) |

**Consequence, stated plainly: with an honest fidelity gate, Family B (α, ω, `F_reactive`) is not testable on I-CARE EEG MNPS-3D at this window (8 s windows, 4 s Δt).** Only 13/163 (part1) and 24/215 (part2) patient-timebins have any finite `alpha_mean`. Primary contrast n is 7 vs 6 (part1, below our own `min_testable_group_n=10`) and 11 vs 11 (part2, borderline). This **confirms** the concern in the prior handover: the earlier "opposite-direction `F_reactive`" result on `20260904_225047` was a fitting artifact of an ungated near-null local-linear fit, not a biological signal. This is not a rejection of the stable-reactive-window hypothesis; it is a statement that this estimator/chart cannot currently test it here. We are marking Family B `not_testable` in the manuscript rather than reporting the small-n contrast as a null result.

Stochastic reachability inherited the gate correctly: `computation_status=unavailable` is now the dominant status (previously `invalid` from `expm` overflow). Article-local reachability recompute from `coords_3d_subject_anchored` remains necessary and is what the manuscript uses.

## Priority 2/3 items: status

| item | status |
|---|---|
| ComBat harmonization (batch_key=hospital) | **Enabled and applied.** `normalization_report.json`: `status=applied`, `family_wise` eta² pre→post for `cpc`-unrelated batch variance drops from ~0.02–0.29 to <0.01 on both bundles. |
| Cohort-anchored coordinates | **Added** (`coords_3d_cohort_anchored`, `coords_9d_cohort_anchored`, `jacobian_*_cohort_anchored`). File-level `primary_coordinate_contract` now defaults to `cohort_anchored`; `dynamical_families.diffusion` still explicitly pins `coordinate_layer=coords_3d_subject_anchored` per our overlay setting, and our reachability recompute explicitly requests `subject_anchored` by name — confirmed this is not silently switched. |
| `conventional_eeg` pack | Overlay sets `conventional_eeg.enabled: true` (`packs: [tier1, complexity, coma]`), but **no `eeg_conventional_*` columns and no `/extensions/conventional_eeg` group are present** in either new bundle's `features_raw`. The overlay's own comment says this "requires a features re-extract and a summarize re-run" and was "not validated against real data ... (no local copy of that raw dump)". Read as: the pack needs a features-stage rerun in addition to `summarize`; this dump only reran `summarize`. Not blocking Family A/B; flagging so a future qEEG-comparator pass isn't silently skipped again. |
| WFDB HH≥24 elapsed-time parsing | Not directly tested (both bundles restrict to hours 000–012 by `exclude_files`, so the failure mode can't occur here). Still open for any future bundle that ingests hours ≥13. |
| Empty run dirs / `signal_support_provenance` | 7 (part1) and 11 (next_140) empty grouped dirs remain, no explicit error record. `/provenance/signal_support_provenance` is present on sampled files now (was absent before) — resolved. |
| 9D `e_m` fallback | Still `coordinates/e_m/source=fallback`, `semantic_equivalence=false` in `/support_signature/v1` on sampled files. Not used for any primary hypothesis in this pass. |

## What analysis did with this

- Built `config/icare_v2_part1_corrected_config.yaml` (bundle `20260911_125829`) and `config/icare_v2_part2_confirmatory_config.yaml` (bundle `20260911_123135`), reusing the existing `src/` pipeline unchanged except for a `family_testable` flag (≥10 patients/arm) added to `icare_v2_outcome_contrast_analysis.py` so a gated-to-near-zero family cannot produce a misleadingly precise-looking small-n p-value.
- Ran the full pipeline on both bundles independently (`results/part1_corrected/`, `results/part2_confirmatory/`) and built a joint replication table (`results/replication/replication_summary.{csv,md}`).
- Results below in `handover/icare_v2_pipeline_handover.md` (v2 section) and `manuscript.typ`.

## Superseded

`results/full/` and `results/smoke/` (bundle `20260904_225047`) are **superseded for Family B** by this fidelity-gate confirmation; Family A results from that bundle are consistent with the corrected part1 numbers (same population, same direction, similar effect sizes) and are kept as a historical record, not deleted.
