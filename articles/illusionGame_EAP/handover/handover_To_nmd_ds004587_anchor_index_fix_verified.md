# Handover to NMD — ds004587 `anchor_index` scale fix verified; contract gaps remain

**Date:** 2026-07-12
**From:** NoeticDiffusion analysis / `illusionGame_EAP`
**To:** NeuralManifoldDynamics
**Status:** confirmation of fix + residual data-contract gaps; follow-up to
`handover_To_nmd_ds004587_anchor_index_scale_failure.md`

## Summary

A new ds004587 export, `neuralmanifolddynamics_ds004587_20260712_111138`
(57 subject-run H5 files), was audited against the same checks that flagged
the `anchor_index` scale failure in
`neuralmanifolddynamics_ds004587_20260712_081757`. The robust-z degeneracy
bug is **fixed** in this run. The pre-existing data-contract gaps (no rest
condition, no trial/event labels, no time reference) are **unchanged**.

## 1. `anchor_index` scale bug — fixed

Across all 57 H5 files, zero windows exceed an absolute `anchor_index`
value of `1000` (previously 488 windows across 10 files, with a global
maximum of `875,000,000`). Full-cohort distribution for every `anchor_state`
component:

| feature | n_finite | median | IQR | min | max | max/IQR |
|---|---:|---:|---:|---:|---:|---:|
| sympathetic_index | 9721 | -0.0097 | 0.9222 | -8.0002 | 3.2586 | 8.68 |
| vagal_index | 9721 | 0.0267 | 0.9542 | -3.7301 | 5.2161 | 5.47 |
| vascular_index | 9721 | 0.0553 | 0.8953 | -3.8913 | 12.8395 | 14.34 |
| pupil_arousal_index | 0 | — | — | — | — | all-NaN |
| anchor_index | 9721 | 0.0261 | 0.3236 | -1.4232 | 3.9107 | 12.08 |
| resp_anchor_index | 8193 | -0.0622 | 0.9656 | -13.5141 | 3.8216 | 14.00 |
| ocular_stability_index | 10049 | 0.0000 | 1.0117 | -6.2390 | 5.3959 | 6.17 |
| cardioresp_anchor_index | 9720 | -0.0231 | 1.0564 | -4.9391 | 3.3172 | 4.68 |
| anchor_index_v02 | 10251 | -0.0033 | 0.3855 | -4.7214 | 5.3959 | 14.00 |

All max/IQR ratios are now well under the `1000` gross-scale gate used by
the article pipeline (previous worst case: `~2.30e9`). `pupil_arousal_index`
remains all-`NaN`, consistent with no pupillometry channel in the ds004587
source release (expected, not a defect).

This is a clean pass under the same audit method as the prior report; we
have not (yet) confirmed which specific guardrail from the prior handover
was applied, only that the observable symptom is gone.

## 2. Residual data-contract gaps — unchanged

From `run_manifest.json` for `..._111138`:

- `conditions.count = 0`, `conditions.unique = []`, `tasks.unique = ["illusion_game"]`
  — no rest condition is present in this export; every included run is
  `illusion_game`. Confirmed empirically: no H5 file carries a `rest` task
  attribute.
- `labels_stage: false`, and zero H5 files contain an `/events` or
  `/labels` group — trial-level and behavioral labels are still not
  attached to the EEG windows.
- `time_reference: false` — no run/window clock provenance is exported.
- `feature_anchors: false`, `anchor_coupling: false` — unrelated to the
  scale bug, but still disabled in this run's config.

These three gaps (no rest EEG, no trial labels, no time reference) are the
same ones documented in
`articles/illusionGame_EAP/peer_review/pr1_data_contract_audit.md` and
`sciencelead/001_data_contract_verdict.md`, and they are the reason the
original rest-vs-illusion EAP study remains a no-go independent of the
anchor-index fix.

## Net effect for `illusionGame_EAP`

- The `anchor_index` scale gate in `02_anchor_validation.py` /
  `ds004587_support.py::valid_anchor_columns` would now pass `anchor_index`
  for this export, so it could be reinstated in a re-run of the IG-only
  exploratory screen (`04_eap_physio_coupling.py`).
- The rest-vs-illusion geometry comparison, robustness/confound audit, and
  illusion-strength/behavior analyses remain gated exactly as before: they
  require rest EEG and/or trial labels that this export does not provide.

## Suggested next step (NMD side)

Confirm in the `mndm` changelog/config diff between the `_081757` and
`_111138` runs which of the four guardrails requested in
`handover_To_nmd_ds004587_anchor_index_scale_failure.md` (robust-z floor,
modality-aware eligibility, quality propagation, export-level validation)
was the actual fix, and add the minimal regression test described there so
the fix is protected against regression.
